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
inlaw inlaw_tests                   # runs the validation checks

python run_inlaw_test.py inlaw_tests/test_ccn_length_is_valid.py   # just one
python save_inlaw_results.py        # run all + save a dated markdown report
```

`build_hierarchy.py` is the Python/pandas reimplementation of
`previous_implementation/hirearchy_R.R`. It classifies every eligible hospital CCN
into one of five ownership categories and persists each pipeline stage to DuckDB.

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

**All twelve currently pass**, so a failure means something actually changed. See
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
