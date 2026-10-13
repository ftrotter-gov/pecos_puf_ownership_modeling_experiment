# PECOS Ownership Experiments

A place for the NPD team to experiment and learn about how PECOS models ownership.

## Data Sources

This project is built on two monthly public-use files published by CMS under
**Provider Characteristics → Hospitals & Other Facilities**. Both are updated
**monthly**, and CMS retains every prior monthly snapshot on the landing page.

| Dataset | Landing page | Local file (current snapshot) | Rows | Role |
| :------ | :----------- | :---------------------------- | ---: | :--- |
| Hospital Enrollments | <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-enrollments> | `data/Hospital_Enrollments_2026.07.31.csv` | 9,161 | Hospital attributes: CCN, associate ID, organization name, organization type structure, proprietary/nonprofit flag |
| Hospital All Owners | <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-all-owners> | `data/Hospital_All_Owners_2026.07.31_update.csv` | 146,859 | One row per hospital-owner relationship: owner associate ID, owner type, role code, title, percentage ownership |

The two files join on **`ENROLLMENT ID`**.

Two auxiliary files from the same landing page are also present locally but are **not**
used by the previous implementation:

| Local file | Rows |
| :--------- | ---: |
| `data/Hospital_Additional_Addresses_2026.07.31.csv` | 30,375 |
| `data/Hospital_Additional_NPIs_2026.07.31.csv` | 2,729 |

### Working with the data

- **`data/` is gitignored.** The CSVs are public and re-downloadable, so they are not
  tracked here. Download them by hand from the landing pages above; nothing in this
  repository fetches data automatically. See [`data/README.md`](data/README.md).
- **Current vintage is `2026.07.31`.** The All Owners file is an `_update` revision
  (CMS re-published that extract on 2026-09-29).
- **Encoding is Windows-1252, not UTF-8**, and both files use CRLF line endings.
- **Official CMS data dictionaries and guidance** are committed under
  [`data_documentation/`](data_documentation/):
  `Hospital_Enrollments_Data_Dictionary.pdf`,
  `Hospital_All_Owners_Data_Dictionary.pdf`, and `Hospital_Data_Guidance.pdf`.

## About CCNs

The **CCN** (CMS Certification Number) identifies a certified facility and is the key
the ownership hierarchy is built on. Two properties of it drive most of the data
handling in this repo.

### Valid lengths are 6, 10, and 13 characters

Anything else is malformed. On the current snapshot **1.05%** of eligible hospital
CCNs (63 of 6,028) fall outside that set:

| Length | Count | Share | Status |
| -----: | ----: | ----: | :----- |
| 6 | 5,965 | 98.9549% | valid |
| 7 | 31 | 0.5143% | malformed — 6-char CCN plus a letter (`140010A`) |
| 8 | 28 | 0.4645% | malformed — 6-char CCN plus 2 digits (`22007401`) |
| 9 | 4 | 0.0664% | malformed — 6-char CCN plus 3 digits (`330027001`) |

This snapshot happens to contain no 10- or 13-character CCNs, but both are treated as
valid so a future snapshot using those forms is not flagged.

The malformed values are not random: each looks like a valid 6-character CCN with a
suffix appended. **Whether to truncate or reject them is still an open decision** — the
pipeline currently passes them through untouched, inheriting the original R script's
behavior. `inlaw_tests/test_ccn_length_is_valid.py` guards the rate rather than
asserting zero.

Separately, CMS sometimes emits a **5-character CCN** that has lost a leading zero;
the pipeline left-pads 934 such rows back to 6 characters.

### Character 3 encodes a special-unit type

Position 3 of the CCN marks psychiatric, rehabilitation, and swing-bed units. These are
**excluded** from the hierarchy — they are units within a hospital rather than hospitals
in their own right — and captured in the `ccn_exclusions` table for review:

| Char 3 | Special unit | Distinct CCNs |
| :----- | :----------- | ------------: |
| `M`, `S` | Psychiatric | 766 |
| `R`, `T` | Rehabilitation | 758 |
| `U`, `W`, `Y`, `Z` | Swing Bed | 1,609 |

That is the whole funnel: **9,161** distinct source CCNs → **3,133** excluded as special
units → **6,028** eligible hospitals classified into the five ownership categories.

Note the exclusion reads position 3 of whatever value is present, including the
malformed over-long CCNs above — another reason the truncation question matters.

## Configuration

**You must create a `.env` before running the checks.** It is never committed —
the database you point at is a local choice, and may carry credentials.
[`example.env`](example.env) is the committed template documenting every supported
variable:

```bash
cp example.env .env
```

The defaults work as-is, so no editing is needed unless you want to change the
database. `inlaw` auto-discovers `.env` when run from the repository root.

**DuckDB is the default, not a requirement.** The repo assumes it because it needs no
server and keeps the pipeline reproducible from a single file. Nothing is locked to it:
the pipeline writes through pandas and the checks query through SQLAlchemy, so any
SQLAlchemy-supported database works — change `INLAW_URL` and the `write_to_duckdb()`
function in `build_hierarchy.py`. InLaw imposes no database at all; a check can
validate a pandas DataFrame in-process and ignore the connection entirely.

## Running the pipeline and tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # Python 3.10-3.13
cp example.env .env

python build_hierarchy.py           # writes data/pecos.duckdb
python build_ownership_graph.py     # resolves ultimate ownership
inlaw inlaw_tests                   # runs the validation checks

python run_inlaw_test.py inlaw_tests/test_ccn_length_is_valid.py   # just one
python save_inlaw_results.py        # run all + save a dated markdown report
```

Or `make all`, which runs the whole chain through to a built report site.

`build_hierarchy.py` is the Python/pandas reimplementation of
`previous_implementation/hirearchy_R.R`. It classifies every eligible hospital CCN
into one of five ownership categories and persists each pipeline stage to DuckDB.

## Ultimate ownership

`build_ownership_graph.py` answers "who ultimately owns this hospital" by
walking upward from each enrolled organization through every intermediate
holding company until it reaches an entity nothing else owns. It adds three
tables to `data/pecos.duckdb`: `ownership_edges`, `ultimate_owner_by_org`, and
`ultimate_owner_summary`.

On the 2026.07.31 snapshot: **5,276** provider organizations resolve to
**2,246** ultimate owners, and **1,623** organizations are joint ventures —
owned by more than one ultimate owner, and so counted under each.

**The resolution uses [igraph](https://python.igraph.org/).** Edges point
org → owner, so walking *out* walks upward, an ultimate owner is a vertex with
out-degree 0, and everything above a hospital is one `subcomponent()` call.
`decompose()` splits the graph into **563** independent ownership families,
the largest covering 2,903 organizations.

**The filtered ownership graph is acyclic** — igraph's strongly connected
component decomposition finds no component larger than a single vertex, and
`is_dag()` returns true. This is worth stating because the *raw* file is not
acyclic: it holds **1,106** self-ownership rows and **1,108** reciprocal
edge-ends (A owns B, B owns A). All of them vanish once the edges are
restricted to organizational ownership roles 34/35 with self-loops removed —
the cycles live in the officer and managing-employee rows, which are not
ownership. The deepest real chain is only 2 hops.

The code does not *assume* acyclicity: `is_dag()` is checked on every build and
a warning is printed if a future snapshot introduces a real cycle. The
traversal terminates either way, because `subcomponent()` visits each vertex
once instead of walking paths.

Only organization-to-organization ownership (`TYPE - OWNER = 'O'`, role codes
34 and 35) forms the chain. Individuals — physician owners, board members,
managing employees — are excluded from the hierarchy.

Organizations with no organizational owner at all (government bodies,
nonprofits, individually held hospitals) are their own ultimate owner at depth
0, so every provider organization appears rather than silently dropping out.

> **Scope limit:** this is the Hospital public-use file only. Hospices, SNFs,
> and home health agencies are published separately by CMS and are **not**
> counted, so the figures describe an owner's hospital footprint, not its
> total healthcare footprint.

### Owner de-duplication: the data patch

CMS identifies an owner by *enrollment ID*, not by company, and one real
company holds many. Left alone, a corporate family is reported as several
separate "ultimate owners" — HCA appeared five times, and 89 hospitals listed
all five at once.

This is fixed **in the data, before the ETL**, by
[`patched_data/owner_name_patch.yaml`](patched_data/owner_name_patch.yaml).
That directory is the single place where data-content problems get corrected,
and **both the patch rules and the corrected CSVs they produce are version
controlled** — so the effect of any rule change is visible in a diff without
downloading the 26 MB CMS source files. The raw downloads in `data/` stay
gitignored. See [`patched_data/README.md`](patched_data/README.md).

**Measured effect on the 2026.07.31 snapshot:**

| | Before | After |
| :--- | ---: | ---: |
| Distinct ultimate owners | 4,610 | **4,523** |
| Published owners (excl. self-owned) | 2,246 | **2,167** |
| Joint ventures | 1,623 | **1,544** |
| Owner/org pairs | 11,812 | **10,267** |
| Ownership edges | 10,566 | **8,894** |
| Exact-duplicate name rate | 3.45% | **2.28%** |

HCA's five fragments became one row — **117 orgs / 218 hospitals**, matching
the union computed independently. 116 duplicate owner IDs were merged across
3,864 rows; hospital classification was untouched, exactly as intended.

**What the patch deliberately does *not* do:**

- **It does not merge by corporate form.** `TRIAD HEALTHCARE CORPORATION` and
  `TRIAD HEALTHCARE LLC` stay separate — Inc and LLC are distinct legal
  entities, and merging them would assert a fact not in evidence. This is most
  of the residual 2.28%.
- **It does not cluster automatically.** Co-ownership clustering was built,
  measured, and rejected: at a 2-hospital threshold it fused **Tenet,
  LifePoint, CommonSpirit, CHI and Texas Health Resources** into one
  113-member "company" by chaining through genuine joint ventures. Families
  are listed by hand with evidence instead.
- **It does not delete passive investors.** Vanguard and BlackRock still rank
  near the top on 5–10% *indirect* stakes. They are flagged, not removed —
  deleting disclosed ownership would falsify the data.

**`is_JV` is still approximate.** It means "more than one ultimate owner", so
any remaining fragmentation still manufactures false joint ventures.

Full analysis: [`AI_Instructions/EntityResolutionProblem.md`](AI_Instructions/EntityResolutionProblem.md).

### A note on ownership depth

Maximum depth is 2, which understates real corporate structure. PECOS records
direct (34) and indirect (35) parties as a **flat list** per hospital rather
than as a parent-of-parent chain, so five levels of one hierarchy arrive as
five siblings at depth 1. Depth here measures *how CMS recorded the structure*,
not how deep it actually goes.

## Reports

The [`reports/`](reports/) directory holds an [Evidence](https://evidence.dev)
site that publishes the ultimate-owner report to GitHub Pages. It builds
**locally** — there is no CI — and is pushed with `make publish`.

```bash
make install    # once
make all        # data -> graph -> test -> sources -> site
make serve      # preview at localhost:3000
make publish    # push to GitHub Pages
```

See [`reports/README.md`](reports/README.md), which documents the two
configuration details that silently break a Pages deploy if missed
(`.nojekyll` and `deployment.basePath`).

The validation checks live in [`inlaw_tests/`](inlaw_tests/), **one
[InLaw](https://pypi.org/project/inlaw/) / Great Expectations class per file** so that
individual checks are easy to run.

Where a data problem is known and expected, the check is a **regression guard against a
documented baseline** rather than an assertion of perfection — a check that fails every
run just teaches people to ignore the suite. Two such baselines are in place on the
current snapshot:

- Role-34 over-ownership affects **2.18%** of enrollments → fails above **3.18%**
- Malformed CCN lengths affect **1.05%** of hospitals → fails above **2.05%**
  (see [About CCNs](#about-ccns))

**All nineteen currently pass**, so a failure means something actually changed. See
[`inlaw_tests/README.md`](inlaw_tests/README.md).

### Recording results over time

`save_inlaw_results.py` runs the suite and writes a dated markdown report to
[`inlaw_tests_results_by_day/`](inlaw_tests_results_by_day/), one file per day. By
default it saves **only when every check passes**, keeping that directory a record of
known-good states; `--force_save` records a failing run too, clearly marked. The exit
code reflects the checks, not whether a report was written, so it is CI-safe.

## Prior work

The original analysis scripts live in [`previous_implementation/`](previous_implementation/).
They are summarized — and specified for reimplementation in Python — in
[`AI_Instructions/PreviousImplementationSummary.md`](AI_Instructions/PreviousImplementationSummary.md).

## Public domain

This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/) as indicated in [LICENSE](LICENSE).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request or issue, you are agreeing to comply with this waiver of copyright interest.
