# Previous Implementation — Summary and Reimplementation Spec

## Purpose of this document

The `previous_implementation/` directory holds two analysis scripts written by the
prior team. This document explains what they do and specifies precisely enough
behavior for an AI agent to rebuild the work in Python.

**Scope decision:**

| Script | Language | Status |
| :----- | :------- | :----- |
| `hirearchy_R.R` | base R | **Reimplementation target.** Rebuild this in Python. |
| `deduping_using_latest_enrollment.do` | Stata | **Error-checking only. Do not reimplement.** Mined for data-quality ideas (§5). |

**Target stack for the rewrite:**

- **pandas** for the data manipulation
- **DuckDB** (file under `data/`) to persist inputs and outputs
- **Great Expectations**, driven by **[InLaw](https://pypi.org/project/inlaw/)**, for
  data validation tests

## 1. Data sources

Both scripts consume monthly CMS public-use files. See the root
[`README.md`](../README.md) and [`data/README.md`](../data/README.md) for the full
provenance table; in brief:

| Dataset | Landing page | Local file |
| :------ | :----------- | :--------- |
| Hospital Enrollments | <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-enrollments> | `data/Hospital_Enrollments_2026.07.31.csv` (9,161 rows) |
| Hospital All Owners | <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-all-owners> | `data/Hospital_All_Owners_2026.07.31_update.csv` (146,859 rows) |

Official CMS data dictionaries live in [`data_documentation/`](../data_documentation/).

Properties that matter for the rewrite:

- Files are **Windows-1252** encoded with **CRLF** line endings.
- The All Owners file is fully quoted; Enrollments is not.
- The two files join on **`ENROLLMENT ID`**.
- `data/` is gitignored; files are downloaded manually.

### 1.1 Column-name trap

`read.csv()` in R mangles column names, converting spaces and hyphens to dots. The R
script therefore refers to names that **do not exist in the CSV**. pandas reads headers
verbatim, so a direct transliteration of the R column names will fail.

| Real CSV header | R script name | Suggested pandas name |
| :-------------- | :------------ | :-------------------- |
| `ENROLLMENT ID` | `ENROLLMENT.ID` | `enrollment_id` |
| `ASSOCIATE ID` | `ASSOCIATE.ID` | `associate_id` |
| `ORGANIZATION NAME` | `ORGANIZATION.NAME` | `organization_name` |
| `CCN` | `CCN` | `ccn` |
| `ORGANIZATION TYPE STRUCTURE` | `ORGANIZATION.TYPE.STRUCTURE` | `structure` |
| `ORGANIZATION OTHER TYPE TEXT` | `ORGANIZATION.OTHER.TYPE.TEXT` | `other_text` |
| `PROPRIETARY NONPROFIT` | `PROPRIETARY.NONPROFIT` | `nonprofit` |
| `ASSOCIATE ID - OWNER` | `ASSOCIATE.ID...OWNER` | `owner_associate_id` |
| `TYPE - OWNER` | `TYPE...OWNER` | `owner_type` |
| `ROLE CODE - OWNER` | `ROLE.CODE...OWNER` | `owner_role` |
| `TITLE - OWNER` | `TITLE...OWNER` | `owner_title` |

(The triple dot comes from ` - ` — space, hyphen, space — becoming three dots.)

## 2. Domain concepts

- **`ENROLLMENT ID`** — identifies one Medicare enrollment record. The join key. A
  hospital can hold several over time.
- **`ASSOCIATE ID`** — identifies the enrolled hospital organization.
- **`ASSOCIATE ID - OWNER`** — identifies the owning party.
- **`ROLE CODE - OWNER`** — **`34` = direct owner**, **`35` = indirect owner**.
- **`TYPE - OWNER`** — **`I` = individual**, organization otherwise.
- **`PROPRIETARY NONPROFIT`** — **`N` = nonprofit**.
- **CCN** — 6-character facility identifier. **Character 3** encodes special-unit type
  (see §3.2); CMS sometimes emits a 5-character CCN that needs a leading zero.
- **Ownership-percentage axiom** — direct-owner (role 34) shares for one hospital
  should never sum above 100%. Used as a quality metric in §5.

### 2.1 Observed values in the 2026.07.31 snapshot

Verified directly against the files in `data/`. Use these as test fixtures and as a
reality check on the rules in §3.3.

`ORGANIZATION TYPE STRUCTURE` (enrollments, 9,161 rows):

| Value | Rows |
| :---- | ---: |
| `CORPORATION` | 5,202 |
| `LLC` | 1,750 |
| `OTHER` | 1,434 |
| `GOVERNMENT` | 602 |
| `PARTNERSHIP` | 167 |
| `NOT SELECTED` | 5 |
| `SOLE PROPRIETOR` | 1 |

This confirms the three literals the R rules test for — `PARTNERSHIP`, `GOVERNMENT`,
`OTHER` — all exist and are spelled as expected. Note `LLC` and `CORPORATION` are the
bulk of the file and match **no** structure rule, so those hospitals fall through to
rule 1 or 4, or land in "Not categorized".

`PROPRIETARY NONPROFIT`: `N` = 6,693, `P` = 2,356, **`D` = 112**. The third value `D`
is undocumented in the script and is treated as not-nonprofit by rule 4.

`ROLE CODE - OWNER` (owners, 146,859 rows) — twelve codes are present, not just 34/35:

| Code | Rows | | Code | Rows |
| :--- | ---: | :-- | :--- | ---: |
| `41` | 61,288 | | `38` | 1,208 |
| `40` | 33,099 | | `44` | 2,691 |
| `42` | 16,769 | | `39` | 542 |
| `43` | 11,371 | | `37` | 331 |
| `35` | 11,094 | | `36` | 81 |
| `34` | **6,774** | | `25` | 1,611 |

Only **`34`** drives rule 1. The other ~140k rows are non-ownership roles (officers,
directors, managing employees, etc.) and are irrelevant to rule 1 — but they still
reach rule 4, which only requires `TYPE - OWNER == "I"` plus board-like title text.

`TYPE - OWNER`: `I` (individual) = 124,522, `O` (organization) = 22,337.

**CCN length distribution — the R script under-handles this:**

| Length | Rows |
| -----: | ---: |
| 6 | 8,150 |
| **5** | 934 |
| **7** | 39 |
| **8** | 31 |
| **9** | 7 |

The script only pads length-5 CCNs. The 77 rows **longer than 6 characters** are passed
through untouched, and `substr(CCN, 3, 3)` still reads position 3 of an over-long
value. Decide explicitly how the Python version handles these rather than inheriting
the behavior by accident.

Observed character-3 values include all the special-unit codes the script screens for
(`Z`=1,334, `T`=752, `S`=719, `U`=273, `M`=47, `R`=6, `Y`=1, `W`=1) plus digits and a
stray `A`.

## 3. Reimplementation target — `hirearchy_R.R`

**What it produces:** a table that classifies every eligible hospital CCN into exactly
one of five ownership categories, with counts and percentages.

342 lines, **base R only** — no external packages (`read.csv`, `merge`, `aggregate`,
`grepl`, `table`). It is runnable as written.

### 3.0 Inputs and arguments

The R script reads from `data_dir = "/intake"` and defaults to August 2026 filenames,
with optional positional command-line overrides:

```r
script_args = commandArgs(trailingOnly = TRUE)
script_args = script_args[script_args != "--args"]
enrollment_file = ifelse(length(script_args) >= 1, script_args[1], "Hospital_Enrollments_aug2026.csv")
allowners_file  = ifelse(length(script_args) >= 2, script_args[2], "Hospital_All_Owners_aug2026.csv")
```

**In the Python rewrite:** the data directory is `data/`, not `/intake`, and the
defaults should be the filenames actually present (see §1). Keep the same contract —
two optional positional arguments overriding enrollment and owners filenames.

### 3.1 Step 1 — load and link

1. Read both CSVs with **every column as string** (`colClasses = "character"` →
   `dtype=str`). Do not let the reader infer types; IDs have significant leading zeros.
2. Transcode text from Windows-1252 to UTF-8. The R code is
   `iconv(x, from = "windows-1252", to = "UTF-8", sub = "")`. The script comments that
   `sub = ""` **drops invalid bytes only — it never drops rows.** In pandas, read with
   `encoding="cp1252"`; row counts must be unchanged by this step.
3. Subset to the needed columns:
   - Enrollments (7): `ENROLLMENT ID`, `ASSOCIATE ID`, `ORGANIZATION NAME`, `CCN`,
     `ORGANIZATION TYPE STRUCTURE`, `ORGANIZATION OTHER TYPE TEXT`,
     `PROPRIETARY NONPROFIT`
   - All Owners (7): `ENROLLMENT ID`, `ASSOCIATE ID`, `ORGANIZATION NAME`,
     `ASSOCIATE ID - OWNER`, `TYPE - OWNER`, `ROLE CODE - OWNER`, `TITLE - OWNER`
4. **Left join** enrollments to owners on `ENROLLMENT ID`
   (`merge(..., all.x = TRUE, sort = FALSE)` → `how="left"`). Enrollments is the left
   side, so every hospital survives even with no owner rows.
5. **Two integrity assertions** (R uses `stopifnot`, both must be exactly zero):
   - `ASSOCIATE ID` agrees across both files, after `trimws()` and stripping leading
     zeros with `sub("^0+", "", ...)`. The script notes some monthly files add a
     leading zero; originals are preserved and normalization is for comparison only.
   - `ORGANIZATION NAME` agrees across both files, compared `toupper(trimws(...))`.
   - Both checks **ignore rows where the owners-side value is `NA`** (unmatched left
     join rows). Reproduce that exclusion or the assertions will fire spuriously.
   - These two checks are prime candidates for InLaw/GX expectations (§6).
6. Where the two sides disagree in provenance, **the enrollment file wins**:
   `ASSOCIATE.ID.x` and `ORGANIZATION.NAME.x` become the canonical values.
7. Print five diagnostics: enrollment rows, all-owner rows, linked rows, and the two
   input filenames.

### 3.2 Step 2 — prepare the CCN file

1. `trimws()` the CCN.
2. **Left-pad to 6 characters:** if `nchar(CCN) == 5`, prepend `"0"`.
3. Read **character 3** (`substr(CCN, 3, 3)`) and classify special units:

   | Char 3 | Special unit |
   | :----- | :----------- |
   | `M`, `S` | Psychiatric |
   | `R`, `T` | Rehabilitation |
   | `U`, `W`, `Y`, `Z` | Swing Bed |
   | anything else | `""` (not a special unit) |

4. Save the excluded rows (`CCN`, char-3, special-unit label, organization name) as a
   **deduplicated** `ccn_exclusions` table for review.
5. Keep only rows where **CCN is non-empty AND special unit is `""`**. These are the
   eligible hospitals.
6. Print three diagnostics: source CCNs, excluded CCNs, eligible hospital CCNs (all as
   distinct counts).

### 3.3 Step 3 — the four hierarchy rules

First, normalize six text fields with `toupper(trimws(...))`, mapping `NA` to `""`:
`structure`, `other.text`, `nonprofit`, `owner.type`, `owner.role`, `owner.title`.

**Reproduce these three regexes verbatim.** They contain *deliberate misspellings*
observed in real CMS free-text; do not "fix" them. R string literals escape the
backslash, so `"\\b"` in R is `\b` in the actual pattern — use Python raw strings.

```python
partnership_terms = r"\b(PARTNERSHIP|LIMITED\s+PARTNER|GENERAL\s+PARTNER|LP|LLP)\b|\bL\.P\.\b"

government_terms = (
    r"\b(FEDERAL|COUNTY|CITY|MUNICIPAL|MUNICIPALITY|TOWNSHIP|PARISH|GOVERNMENT|"
    r"GOVERNMENTAL|GOVT|GOVERMENT|GOVERMENTAL|GOVENMENTAL|GOVERNEMNT|PUBLIC|STATE|"
    r"DISTRICT|AUTHORITY|TRIBAL|TRIBE|IHS|INDIAN\s+HEALTH\s+SERVICE|COMMONWEALTH|"
    r"INSTRUMENTALITY|DEPARTMENT\s+OF\s+DEFENSE)\b|POLITICAL\s*SUB[ -]?"
    r"(DIVISION|DIV|DIVISON)|POLITICALSUB"
)

board_terms = r"\bBOARD\b|\bTRUSTEES?\b|\bBOD\b|\bBOT\b|\bGOVERNING\s+(BOARD|BODY)\b"
```

Misspellings intentionally covered: `GOVERMENT`, `GOVERMENTAL`, `GOVENMENTAL`,
`GOVERNEMNT`, `DIVISON`.

R's `grepl(pattern, x, perl = TRUE)` becomes
`series.str.contains(pattern, regex=True, na=False)`. Matching is case-sensitive
against already-uppercased text.

All three patterns have been **verified to compile and match correctly under Python's
`re` module** as transcribed above, including the misspelling cases
(`COUNTY GOVERMENT`, `POLITICAL SUBDIVISON`) and `LLP` / `TRUSTEES`.

Row-level flags:

| Flag | Definition |
| :--- | :--------- |
| `rule1.has.owners` | `owner.role == "34"` (any direct owner) |
| `rule2.partnership` | `structure == "PARTNERSHIP"` **or** (`structure == "OTHER"` and `other.text` matches `partnership_terms`) |
| `rule3.government` | `structure == "GOVERNMENT"` **or** (`structure == "OTHER"` and `other.text` matches `government_terms`) |
| `nonprofit.N` | `nonprofit == "N"` |
| `board.title` | `owner.type == "I"` **and** `owner.title` matches `board_terms` |

Then **roll up to one row per CCN** taking the **maximum** of each flag — i.e. a
hospital gets the flag if *any* of its rows has it:

```r
aggregate(cbind(rule1.has.owners, rule2.partnership, rule3.government,
                nonprofit.N, board.title) ~ CCN, data = hospital_data, FUN = max)
```

> **R gotcha:** formula-interface `aggregate()` silently drops rows with `NA` in any
> referenced column. Because the five flags are built with `ifelse` over
> `NA`-to-`""`-normalized inputs they should be complete, but a pandas
> `groupby("ccn")[flags].max()` must produce the same CCN set — assert this.

Separately, roll up hospital names per CCN, sorted-unique and pipe-joined:
`paste(sort(unique(x)), collapse = " | ")`. Merge onto the flags.

**Apply the rules in order — first match wins:**

1. `rule1.has.owners == 1` → **"Has owners"**
2. else `rule2.partnership == 1` → **"Partnerships"**
3. else `rule3.government == 1` → **"Government"**
4. else `nonprofit.N == 1` **AND** `board.title == 1` → **"Non-profit"**
5. else → **"Not categorized"**

Note rule 4 is the only conjunction, and the ordering means a hospital with any role-34
owner is "Has owners" regardless of its other attributes.

### 3.4 Step 4 — the hierarchy table

Build counts over a **fixed category order**, preserving zero-count categories (R uses
`table(factor(..., levels = category_order))`; pandas needs
`pd.Categorical(..., categories=category_order)` or a reindex):

```
Has owners, Partnerships, Government, Non-profit, Not categorized
```

Output a data frame with a leading **"Hospitals, total"** row:

| Column | Value |
| :----- | :---- |
| `Category` | `"Hospitals, total"` then the five categories |
| `Count` | total CCN count, then each category count |
| `Percent` | `1`, then `count / total` |

`Percent` is a **0–1 fraction, not a percentage out of 100**. The script `print`s the
table and writes no file; the Python version should persist it to DuckDB (§6).

## 4. Not a reimplementation target — `deduping_using_latest_enrollment.do`

**Do not port this script.** It was written as **error checking**, not as production
logic. It is retained for the data-quality insight it documents (§5).

225 lines of Stata. It is an analyst's lab notebook rather than a runnable program:

- A bare `stop` on line 2.
- Prose, notes, and pasted result tables interleaved with code.
- A hard-coded Windows share path (`G:\HP\Divisions\HFP\...`) on line 111.
- Abandoned/alternative `collapse` variants left in place (lines 84–91).
- It reads an internal Stata extract (`owner_2roles_h26`, 18,046 obs × 88 vars), **not**
  the public CSVs. Fields it relies on — `own_pct`, `dt_max_h`, `effect_dt_oh`,
  `assoc_id_owner`, `owned_by_another` — are an internal derivation, so the script is
  not reproducible from `data/` as-is.

What it actually investigated: hospitals accumulate multiple enrollment IDs over time,
and naively summing ownership percentages across all of them massively overstates
ownership. It kept only the highest `enr_id` per hospital, de-duplicated, and confirmed
the inflation disappeared. Its row-count trail was 18,046 → 11,926 → 11,513 → 3,210
hospitals.

## 5. Data-quality ideas inherited from the Stata script

These are the useful residue of §4 — candidate validations for the Python pipeline,
not pipeline logic:

| Idea | Rationale / observed evidence |
| :--- | :---------------------------- |
| **Role-34 shares should never sum above 100% per hospital** | The script's headline quality metric. Role 34 is *direct* ownership, so >100% signals duplication. |
| **Duplicate enrollment IDs inflate ownership sums** | Three hospitals summed to 600%, 300%, and 200% before de-duplication and exactly 100% after: MCHS Hospitals Inc (`5698071173`), Saint Mary of Nazareth Hospital Chicago LLC (`6103348479`), Bowling Green-Warren County Community Hospital Corp (`7719899947`). |
| **The same owner can appear as both role 34 and role 35** | 46 such pairs were found. The analyst's resolution was to **retain the 35 (indirect) row**. |
| **Distribution of summed ownership share** | Bucketed as `<=50%`, `51-90%`, `91-100%`, `101-150%`, `151-250%`, `>250%`. 93 hospitals were at ≥200% before de-duplication. A useful drift monitor. |
| **Enrollment effective dates span many years** | Spread between earliest and latest effective date per hospital: **median 6 years, 90th percentile 24 years**. Confirms stale enrollment records are normal, not anomalous. |

Note these metrics need an ownership-percentage column. The public All Owners file does
carry `PERCENTAGE OWNERSHIP`, so the role-34 sum check is reproducible even though the
original script is not.

## 6. Testing architecture

### Layout

```
data/
  Hospital_Enrollments_2026.07.31.csv          # input (gitignored)
  Hospital_All_Owners_2026.07.31_update.csv    # input (gitignored)
  pecos.duckdb                                 # pipeline output (gitignored)
```

### Tables to persist

DuckDB is a **design choice, not an InLaw requirement** (see below). The pandas
pipeline should write each stage to `data/pecos.duckdb` so stages are inspectable and
the checks can query them by name:

| Table | Contents |
| :---- | :------- |
| `hospital_enrollments` | raw enrollments, as read |
| `hospital_allowners` | raw owners, as read |
| `owners_enrollments` | the linked table after §3.1 |
| `ccn_exclusions` | special-unit CCNs removed in §3.2 |
| `hospital_flags` | one row per eligible CCN with the five flags and `final_category` |
| `heirarchy_table` | the final five-category count/percent table from §3.4 |

### InLaw

[InLaw](https://pypi.org/project/inlaw/) is **a packaging convention, not a database
requirement.** Its job is to keep the query and the expectation logic for one Great
Expectations check together in a single class in a single file, and to give you a CLI
that discovers and runs them.

```bash
pip install 'inlaw[duckdb]'
```

Requires **Python 3.10–3.13** (3.14 is excluded due to a Great Expectations/Pydantic
incompatibility).

A check is a subclass of `InLaw` with a `title` and a static `run()` that returns
`True` for pass or a descriptive **string** for failure:

```python
class TestSomething(InLaw):
    title = "Human-readable description"

    @staticmethod
    def run(engine, settings=None):
        ...
        return True  # or "why it failed"
```

The CLI reports results per `title` and exits `0` only if every check passed.

#### SQL is convenient, but not mandatory

`InLaw.sql_to_gx_df(sql=..., engine=...)` runs SQL and hands back a validator. Note
what it does internally — it executes `pd.read_sql_query(...)` and feeds the result to
GX's `pandas_default` data source. **The validation always happens over a pandas
DataFrame.** SQL is just the retrieval mechanism.

So a check can skip the database entirely and validate a DataFrame it built itself:

```python
import great_expectations as gx
from inlaw import GXValidatorAdapter

def gx_df_from_dataframe(df):
    """Wrap an in-memory DataFrame in the same adapter sql_to_gx_df returns."""
    context = gx.get_context(mode="ephemeral")
    batch = context.data_sources.pandas_default.read_dataframe(df)
    return GXValidatorAdapter(batch)
```

The `engine` argument is passed positionally to every `run()` by the runner, but a
check is free to ignore it.

#### Why DuckDB is still the right call here

Not because InLaw needs it, but because:

- the intermediate tables are worth inspecting interactively between runs;
- expressing checks as SQL over named tables is clearer than reconstructing the same
  slice in pandas inside each test;
- the tests stay decoupled from the pipeline's in-process state, so they can run
  against output produced earlier or elsewhere.

A reasonable split: use SQL via `sql_to_gx_df` for anything that queries a persisted
table, and the DataFrame path above for checks on a transient intermediate that is not
worth persisting.

Configure with a `.env` file. The repository commits
[`example.env`](../example.env) as the documented template — copy it and edit:

```bash
cp example.env .env
```

```
INLAW_URL=duckdb:///data/pecos.duckdb
```

`.env` itself is gitignored, so local paths and any credentials stay private;
`example.env` is the thing that gets committed and kept up to date. Alternatively,
pass `inlaw --db-config-file <path>` to point at a different config file.

InLaw accepts either a single `INLAW_URL` **or** individual components
(`INLAW_DIALECT`, `INLAW_DRIVER`, `INLAW_USER`, `INLAW_PASSWORD`, `INLAW_HOST`,
`INLAW_PORT`, `INLAW_DATABASE`). For a file-based DuckDB only the dialect and
database path are meaningful. See `example.env` for the full annotated list.

Each test is a class with a `title` and a static `run`, returning `True` on success or
a failure-message string. A worked example using the SQL path:

```python
from inlaw import InLaw, DBTable

class TestDirectOwnershipNotOverHundred(InLaw):
    title = "Role 34 ownership shares do not sum above 100% per hospital"

    @staticmethod
    def run(engine, settings=None):
        owners = DBTable(table='hospital_allowners')
        sql = f"""
            SELECT SUM(CAST("PERCENTAGE OWNERSHIP" AS DOUBLE)) AS pct_total
            FROM {owners}
            WHERE "ROLE CODE - OWNER" = '34'
            GROUP BY "ENROLLMENT ID"
        """
        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column='pct_total', min_value=0, max_value=100
        )
        if result.success:
            return True
        return "Found hospitals whose role-34 ownership exceeds 100%"
```

Run with `inlaw <test_dir>` (optionally `--db-config-file <path>`).

#### Available expectations

InLaw's adapter maps only **nine** GX expectations; anything else raises
`AttributeError` listing what is available. Design checks within this set:

```
expect_column_values_to_be_between     expect_column_values_to_be_in_set
expect_column_sum_to_be_between        expect_column_values_to_match_regex
expect_column_values_to_be_unique      expect_table_row_count_to_equal
expect_column_values_to_not_be_null    expect_table_row_count_to_be_between
expect_column_values_to_be_null
```

In practice this is rarely limiting: push the real logic into the SQL (or the
DataFrame construction) so the expectation itself stays simple — typically asserting
that a count of offending rows is zero, or that a computed column sits in range.

### Tests worth writing

**Convention: one `InLaw` class per file**, in `inlaw_tests/`, named to match the file.
Pair two classes only when they are so tightly coupled that reading one without the
other is confusing. This keeps individual checks easy to run and makes a failure
message point straight at a file.

Because the `inlaw` CLI takes a directory rather than a file, `run_inlaw_test.py` in
the repository root runs one or more named check files via `InLaw.run_all(inlaw_files=...)`.

1. The two §3.1 integrity assertions (associate ID and organization name agree across
   files), as expectations rather than hard `stopifnot` crashes.
2. Row counts unchanged by the encoding transcode (§3.1 step 2).
3. Every CCN in `hospital_flags` is exactly 6 characters.
4. No CCN in `hospital_flags` has a special-unit character in position 3.
5. `final_category` only ever takes the five known values.
6. `heirarchy_table` counts sum to the "Hospitals, total" row, and `Percent` sums to 1.
7. The role-34 ≤ 100% check and the other §5 metrics.

## 7. Open questions and known gaps

- **`\bL\.P\.\b` is dead code.** Confirmed empirically: the trailing `\b` after an
  escaped `.` requires a word character immediately after it, so `ACME L.P.` never
  matches this alternative. The behavior is inherited verbatim and pinned by
  `inlaw_tests/test_regex_terms_match_known_cases.py`. Decide whether to repair it.
- **121 enrollments exceed 100% role-34 ownership** on the 2026.07.31 snapshot
  (maximum 300%), which is the §5 metric firing exactly as the Stata script predicted.
  This is **2.18%** of the 5,547 enrollments carrying any role-34 row. Because the
  problem is inherent to the data rather than to the pipeline,
  `inlaw_tests/test_direct_ownership_not_over_100.py` is written as a regression guard:
  it measures the rate and fails only above **3.18%** (baseline + 1 percentage point).
  Whether to de-duplicate owner rows the way the Stata script did remains open.

- **Data dictionaries not yet parsed.** The PDFs in `data_documentation/` have not been
  machine-read. Observed values are catalogued in §2.1, but the *meaning* of the
  non-34/35 role codes (`25`, `36`–`44`) and of `PROPRIETARY NONPROFIT = "D"` should be
  confirmed against the official dictionaries.
- **Over-long CCNs are unhandled.** Valid CCN lengths are **6, 10, and 13** characters.
  77 source rows (63 eligible hospitals, **1.05%**) fall outside that set at lengths 7,
  8, and 9, and the R script neither pads nor rejects them. Each looks like a valid
  6-character CCN with a suffix appended (`140010A`, `22007401`, `330027001`), so
  truncation to 6 is plausible — but it must be a deliberate decision, and note the
  special-unit exclusion reads position 3 of whatever value is present.
  `inlaw_tests/test_ccn_length_is_valid.py` guards the rate at **2.05%**
  (baseline + 1 percentage point) rather than asserting zero.
- **Path change.** The R script's `/intake` becomes `data/` in the rewrite.
- **No Python project scaffolding yet** — there is no `pyproject.toml` or
  `requirements.txt` in the repository.
- **Snapshot drift.** The R script defaults to `*_aug2026.csv` filenames; the data on
  disk is the `2026.07.31` vintage, and the All Owners file is an `_update` revision.
- **`AI_Instructions/GoodTestingApproach.md` is currently empty** and should be filled
  in to complement §6.

