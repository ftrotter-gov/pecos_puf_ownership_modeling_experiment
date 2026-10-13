# `patched_data/` — correcting the source CSVs

**This is the single place where data-content problems get fixed.**

CMS publishes the PECOS public-use files as-reported, with no normalization.
The same company appears under several names and several enrollment IDs, names
carry stray punctuation, and corporate families fragment across records. None
of that is a pipeline bug, so none of it belongs in pipeline code.

Instead it is fixed **here**, before the ETL runs, by a declarative patch:

```
data/Hospital_All_Owners_2026.07.31_update.csv              raw CMS download
        │                                                   (gitignored)
        │  apply_data_patch.py  +  owner_name_patch.yaml
        ▼
patched_data/Hospital_All_Owners_...update.patched.csv      VERSION CONTROLLED
        │
        ▼
build_hierarchy.py → build_ownership_graph.py → reports/
```

## Everything here is version controlled

| File | Role |
| :--- | :--- |
| `owner_name_patch.yaml` | The corrections, with a reason on every rule |
| `*.patched.csv` | The corrected data those rules produce |
| `README.md` | This file |

Both the rules **and their output** are committed, deliberately. The raw CMS
files in `data/` are gitignored — they are large and re-downloadable — but the
patched copies are the artifact people actually need to review. Committing
them means:

- a reviewer can `git diff` the effect of a rule change without downloading
  26 MB of CMS data or running anything;
- the exact data behind any published report is recoverable from history;
- a patched file that drifts from its rules is visible as an uncommitted diff.

The ETL reads from `patched_data/` first and falls back to `data/`, so both
raw and patched filenames resolve.

## Why a patch file and not code

**The rules are data, so they are reviewable as data.** Every correction is a
line in [`owner_name_patch.yaml`](owner_name_patch.yaml) with a reason
attached. A reviewer who knows the hospital industry but not Python can read
it, challenge a specific merge, and send a one-line change. Burying the same
decisions in `build_ownership_graph.py` would make them invisible.

It also keeps the chain auditable: the original CSV is never modified, the
patched CSV is regenerated from it deterministically, and
`apply_data_patch.py --report` prints exactly what changed and why.

## Design rules

1. **Never edit the original.** It is the CMS artifact of record.
2. **Every rule carries a `reason`.** A merge without a stated justification
   is not reviewable, and will be rejected.
3. **Merges must be evidence-backed**, not guesses about who owns whom.
4. **Patched output is committed**, so a reader can diff it without running
   anything.
5. **Conservative beats clever.** A wrong merge invents a corporate
   relationship that does not exist — worse than leaving two records split.
   When in doubt, do not merge.

## The rule types

### `canonical_names` — spelling variants
Collapses punctuation and suffix variants of the *same* name onto one spelling.

```yaml
- canonical: COMMUNITY FOUNDATION OF NORTHWEST INDIANA INC
  variants:
    - COMMUNITY FOUNDATION OF NORTHWEST INDIANA, INC
  reason: Identical entity; differs only by a comma.
```

### `identical_name_merges` — one name, many IDs
Where several `ASSOCIATE ID - OWNER` values carry a byte-identical name, they
are the same enrolled party and are merged onto the lowest ID. This is the
safest rule in the file: it asserts nothing beyond what CMS already states.

### `corporate_families` — the hard case
Different *legal* names for one group (HCA INC / HEALTHTRUST / HERCULES
HOLDING II). These are **not** detectable by string matching and are listed
explicitly, each with the overlap evidence that justifies it.

See [`../AI_Instructions/EntityResolutionProblem.md`](../AI_Instructions/EntityResolutionProblem.md)
for the full analysis.

## ⚠️ Why corporate families are listed by hand

Automatic co-ownership clustering was tried and **rejected**. Clustering
owners who share ≥95% of their hospitals, then taking connected components,
over-merges catastrophically: at a 2-hospital threshold it produced a single
113-member cluster fusing **Tenet, LifePoint, CommonSpirit, CHI Nebraska,
Texas Health Resources, and St. Luke's** into one "company".

The cause is transitive chaining through genuine joint ventures. If A and B
co-own one hospital, and B and C co-own another, connected components merge
A with C — even though A and C share nothing. Real JVs are exactly the
structures that make this unsafe, and they are common here.

Raising the threshold to 10 shared hospitals yields a clean, all-HCA cluster,
but that only works for the largest chains and silently misses smaller ones.
So the automatic merge is not used. The families below are listed explicitly,
with evidence, and a human decides.

## Running it

```bash
make patch                              # regenerate the patched CSV
python apply_data_patch.py --report     # what changed, and why
python apply_data_patch.py --verify     # confirm output matches the rules
```

`make all` runs the patch first, so the ETL always consumes patched data.

## Adding a correction

1. Add a rule to `owner_name_patch.yaml` with a `reason`.
2. Run `make patch` and read the report.
3. Run `make graph && make test` to see the effect on the outputs.
4. Commit the rule, the regenerated CSV, and the measured effect.
