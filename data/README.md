# `data/` — local data files (not committed)

Everything in this directory except this README is ignored by git (see `.gitignore`:
`data/*` plus a `!data/README.md` exception). The CSVs are public CMS downloads, but
they are large and re-downloadable, so they are not tracked in the repository.

## Where these files come from

All files are monthly public-use files published by CMS under
**Provider Characteristics → Hospitals & Other Facilities**:

| Landing page | Dataset |
| :----------- | :------ |
| <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-enrollments> | Hospital Enrollments |
| <https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/hospital-all-owners> | Hospital All Owners |

Both datasets are updated **monthly**, and CMS keeps every prior monthly snapshot
available on the landing page. Pick a vintage and download the CSV by hand; nothing
in this repository downloads data automatically.

## Current snapshot: 2026.07.31

| File | Rows (excl. header) | Size | Used by the pipeline? |
| :--- | ------------------: | ---: | :-------------------- |
| `Hospital_Enrollments_2026.07.31.csv` | 9,161 | 2.5 MB | **Yes** — hospital attributes |
| `Hospital_All_Owners_2026.07.31_update.csv` | 146,859 | 25.9 MB | **Yes** — ownership rows |
| `Hospital_Additional_Addresses_2026.07.31.csv` | 30,375 | 2.1 MB | No |
| `Hospital_Additional_NPIs_2026.07.31.csv` | 2,729 | 76 KB | No |

Notes on this vintage:

- The All Owners file is an **`_update` revision** (CMS re-published the 2026.07.31
  extract on 2026-09-29). Keep the `_update` suffix in the filename so the revision is
  obvious.
- The two `Additional_*` files ship alongside the enrollment data on the same landing
  page. The previous implementation does not read them; they are kept for reference.
- Both primary files use **CRLF** line endings. The All Owners file is fully quoted;
  the Enrollments file is not.
- Text is **Windows-1252 encoded**, not UTF-8. Read it accordingly (the original R
  script ran `iconv(from = "windows-1252", to = "UTF-8")`).

## Official documentation

The CMS data dictionaries and guidance PDFs are committed under
[`../data_documentation/`](../data_documentation/):

- `Hospital_Enrollments_Data_Dictionary.pdf`
- `Hospital_All_Owners_Data_Dictionary.pdf`
- `Hospital_Data_Guidance.pdf`

## Derived artifacts

Pipeline output (for example a DuckDB database used by the
[InLaw](https://pypi.org/project/inlaw/) / Great Expectations tests) also belongs in
this directory and is likewise ignored by git.
