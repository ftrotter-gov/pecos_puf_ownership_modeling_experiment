# `inlaw_tests/` — data validation checks

One [InLaw](https://pypi.org/project/inlaw/) check per file, one class per check,
as specified in
[`../AI_Instructions/PreviousImplementationSummary.md`](../AI_Instructions/PreviousImplementationSummary.md) §6.

## Convention: one class per file

**Each file contains exactly one `InLaw` subclass**, named to match the file. This is
what makes individual checks easy to run and easy to find from a failure message.

Only pair two classes in one file if they are so tightly coupled that reading one
without the other is confusing — and prefer splitting even then.

Current state: **12 files, 12 classes.**

## Running them

```bash
cp example.env .env           # required once; .env is never committed
python build_hierarchy.py     # populates the database

inlaw inlaw_tests             # every check in the folder
python run_inlaw_test.py inlaw_tests/test_ccn_length_is_valid.py   # just one
```

DuckDB at `data/pecos.duckdb` is the default target, not a requirement — see
[`../example.env`](../example.env) for switching databases.

The `inlaw` CLI takes a **directory**, so pointing it at a single `.py` fails with
`Directory not found`. `run_inlaw_test.py` in the repository root is the companion for
the one-class-per-file convention: it accepts one or more file paths and exits `0` only
if all named checks pass. It opens DuckDB read-only, so several runs can proceed at
once without tripping DuckDB's single-writer lock.

`inlaw` auto-discovers `.env` in the repository root; copy `example.env` first.

> **Discovery caveat:** InLaw loads each `*.py` here as a standalone module by
> path, so **checks cannot import from each other**. Every file must be
> self-contained, which is why the regex constants are duplicated rather than
> imported from `build_hierarchy.py`.

## The checks

| File | Asserts | Spec |
| :--- | :------ | :--- |
| `test_associate_id_agreement.py` | `ASSOCIATE ID` agrees across both source files (leading zeros ignored) | §3.1 |
| `test_organization_name_agreement.py` | `ORGANIZATION NAME` agrees across both source files | §3.1 |
| `test_link_preserves_owner_rows.py` | The left join neither duplicates nor drops owner rows | §3.1 |
| `test_ccn_length_is_valid.py` | Malformed CCN length rate stays within 1 point of its 1.05% baseline | §2.1, §3.2 |
| `test_no_special_unit_ccns_remain.py` | No psychiatric/rehab/swing-bed unit survives into the hierarchy | §3.2 |
| `test_hospital_flags_one_row_per_ccn.py` | The flag rollup is unique on CCN with no nulls | §3.3 |
| `test_final_category_in_known_set.py` | `final.category` only takes the five documented values | §3.3 |
| `test_hierarchy_counts_sum_to_total.py` | Category counts reconcile with the total row and `hospital_flags` | §3.4 |
| `test_hierarchy_percent_is_fraction.py` | `Percent` is a 0–1 fraction summing to 1, not percentage points | §3.4 |
| `test_direct_ownership_not_over_100.py` | Role-34 over-ownership rate stays within 1 point of its 2.18% baseline | §5 |
| `test_ownership_percentage_in_range.py` | Each individual ownership percentage is within 0–100 | §5 |
| `test_regex_terms_match_known_cases.py` | The three classification regexes still match their documented cases | §3.3 |

## Known data problems and how they are handled

Some defects are inherent to the CMS data, not to the pipeline. A check that
asserts perfection against them fails every run and trains people to ignore the
suite. Where a problem is expected, the check is written as a **regression
guard** against a documented baseline instead.

**Role-34 over-ownership — tolerated at a baseline rate.**
Direct-ownership shares should never sum above 100% for one enrollment, but on
the 2026.07.31 snapshot they do for **2.18% of enrollments** (121 of 5,547),
reaching 300%. `test_direct_ownership_not_over_100.py` therefore measures the
*rate* and fails only if it exceeds **3.18%** — the baseline plus a 1 percentage
point tolerance. That absorbs normal month-to-month drift while still catching a
genuine deterioration, or a pipeline change that starts double-counting owners.

If it fails, check the reported rate against `BASELINE_RATE_PERCENT` in the
file. If the higher rate is the new normal, update the baseline deliberately and
explain why in the commit message — do not just widen the tolerance.

**Malformed CCN lengths — tolerated at a baseline rate.**
Valid CCN lengths are **6, 10, and 13** characters. On the 2026.07.31 snapshot
**1.05%** of eligible hospital CCNs (63 of 6,028) fall outside that set, so
`test_ccn_length_is_valid.py` fails only above **2.05%**.

| Length | Count | Share | |
| -----: | ----: | ----: | :--- |
| 6 | 5,965 | 98.9549% | valid |
| 7 | 31 | 0.5143% | malformed — 6-char CCN plus a letter (`140010A`) |
| 8 | 28 | 0.4645% | malformed — 6-char CCN plus 2 digits (`22007401`) |
| 9 | 4 | 0.0664% | malformed — 6-char CCN plus 3 digits (`330027001`) |

This snapshot contains no 10- or 13-character CCNs, but both are accepted so a
future snapshot using those forms does not trip the check. The malformed values
are not random — each looks like a valid 6-character CCN with a suffix appended.
Whether to truncate or reject them is the open decision in §7; the pipeline
currently passes them through untouched, which means `substr(CCN, 3, 1)` still
reads position 3 for the special-unit exclusion.

**The whole suite currently passes** (12 of 12), including the regex check that
pins the deliberate CMS misspellings (`GOVERMENT`, `GOVENMENTAL`, `GOVERNEMNT`,
`DIVISON`). A failure now means something actually changed.

## A note on `L.P.`

While building the regex check, the `\bL\.P\.\b` alternative in
`partnership_terms` turned out to be **dead code in the original R script**: a
trailing `\b` after an escaped `.` requires a word character immediately after,
so `ACME L.P.` never matches. The behavior is pinned in `MUST_NOT_MATCH` so that
any future correction has to be a deliberate, visible change.
