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

python run_inlaw_test.py inlaw_tests/test_ccn_is_six_characters.py   # just one
```

`build_hierarchy.py` is the Python/pandas reimplementation of
`previous_implementation/hirearchy_R.R`. It classifies every eligible hospital CCN
into one of five ownership categories and persists each pipeline stage to DuckDB.

The validation checks live in [`inlaw_tests/`](inlaw_tests/), **one
[InLaw](https://pypi.org/project/inlaw/) / Great Expectations class per file** so that
individual checks are easy to run.

Where a data problem is known and expected, the check is a **regression guard against a
documented baseline** rather than an assertion of perfection — a check that fails every
run just teaches people to ignore the suite. Role-34 over-ownership, for example,
affects 2.18% of enrollments on the current snapshot, so that check fails only above
3.18%. **One of the twelve fails by design**, flagging an unresolved design decision.
See [`inlaw_tests/README.md`](inlaw_tests/README.md).

## Prior work

The original analysis scripts live in [`previous_implementation/`](previous_implementation/).
They are summarized — and specified for reimplementation in Python — in
[`AI_Instructions/PreviousImplementationSummary.md`](AI_Instructions/PreviousImplementationSummary.md).

## Public domain

This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/) as indicated in [LICENSE](LICENSE).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request or issue, you are agreeing to comply with this waiver of copyright interest.
