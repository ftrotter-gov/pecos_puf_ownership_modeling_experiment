Entity Resolution — the problem under the ultimate owner report
===============================================================

**Status: PARTLY FIXED by `patched_data/owner_name_patch.yaml`.** The analysis
below describes the problem as originally found; see "What the patch fixed" at
the end for the measured result and what remains.

The ultimate owner resolution in `build_ownership_graph.py` treats
`ASSOCIATE ID - OWNER` as an entity identifier. It is not one. It identifies a
*PECOS enrollment record*, and a single real-world company holds many of them.
Nothing in the pipeline currently detects that two IDs are the same company, so
one corporate group is reported as several separate "ultimate owners".

This inflates the owner count, splits hospital counts across duplicate rows, and
corrupts the `is_JV` flag.

## Evidence

### 1. The same company under several legal names

Measured on the 2026.07.31 snapshot: **89 hospitals have five different "HCA"
entities each recorded as an ultimate owner.**

| Reported "ultimate owner" | Provider orgs | Hospitals |
| :--- | ---: | ---: |
| HCA INC | 115 | 214 |
| HCA HEALTHCARE INC | 112 | 212 |
| HEALTHTRUST INC - THE HOSPITAL COMPANY | 111 | 209 |
| HERCULES HOLDING II | 104 | 198 |
| FRISCO HOLDING II | 103 | 200 |

These are not five companies. They are one corporate family, and the union of
hospitals they touch is **225**, not the 1,033 you get by summing the column.

Pairwise overlap confirms it — these pairs own near-identical hospital sets:

| A | B | Shared | % of smaller |
| :--- | :--- | ---: | ---: |
| HCA HEALTHCARE INC | HERCULES HOLDING II | 104 | 100.0% |
| DSB ACQUISITION LLC | LIFEPOINT HEALTH INC | 108 | 100.0% |
| HCA INC | HCA HEALTHCARE INC | 110 | 98.2% |
| ENCOMPASS HEALTH CORPORATION | ENCOMPASS HEALTH OWNED HOSPITALS LLC | 74 | 100.0% |

Two entities that are each an "ultimate owner" of the same 100+ hospitals are
one group, not a joint venture.

### 2. Pure spelling variants

Some duplicates are nothing more than punctuation:

- `AMITE COUNTY BOARD OF SUPERVISORS` vs `AMITE COUNTY, BOARD OF SUPERVISORS`
- `COMMUNITY FOUNDATION OF NORTHWEST INDIANA INC` vs
  `COMMUNITY FOUNDATION OF NORTHWEST INDIANA, INC`

Normalizing case, punctuation, and corporate suffixes (INC/LLC/CORP/THE/…)
collapses the distinct ultimate owner count from **4,610 to 4,451** — about
**3.4%** of owners are exact duplicates under a trivial normalization. Names
with multiple associate IDs include MERCY HEALTH (4 IDs), TRINITY HEALTH (3),
CHARLOTTE MECKLENBURG HOSPITAL AUTHORITY (3).

This is the *easy* part of the problem and the smaller one.

### 3. Passive institutional investors are ranked as owners

`VANGUARD GROUP INC` (144 orgs) and `BLACKROCK INC` (115 orgs) currently rank
**#2 and #5** in the published report. Their rows are role code **35**
(indirect) at **5–10%** — index-fund positions, properly disclosed to CMS, but
not control. BlackRock co-occurs with Encompass Health on **100%** of
Encompass's hospitals, because it holds a small slice of the public parent.

Presenting them beside HCA as "ultimate owners" misleads the reader about who
controls a hospital. 64 organizational owners hold a stake under 5%.

## Impact on published numbers

| Figure | Reported | Reality |
| :--- | :--- | :--- |
| Distinct ultimate owners (4,610) | Overstated | ≥159 are exact-name duplicates; many more are corporate-family splits |
| `n_provider_orgs` per owner | Fragmented | HCA's true footprint is 225, split across 5 rows |
| Joint ventures (1,623) | Overstated | Only 6 are false under exact-name matching, but each HCA-style split creates spurious multi-owner rows |
| Top-10 ranking | Misleading | Contains duplicate HCA entities *and* two index funds |

Note the `is_JV` flag is the most damaged output: it is defined as "more than
one ultimate owner", and unresolved duplicates manufacture exactly that.

## Why the ownership graph looked "surprisingly" shallow

Max ownership depth is 2 and the filtered graph is a DAG. That is partly real
and partly an artifact: PECOS records a hospital's owners as a **flat list** of
direct (34) and indirect (35) parties, rather than as a parent-of-parent chain.
A five-level corporate structure arrives as five sibling rows on one hospital,
all terminal. So the "ultimate owners" of an HCA hospital are really five
*levels* of one hierarchy presented side by side — which is why they co-occur
at ~100%.

**Depth in this report measures how PECOS reported the structure, not how deep
the real corporate structure goes.**

## What a fix requires

Ordered by cost, and none of it is currently implemented:

1. **Normalize names.** Upper-case, strip punctuation and corporate suffixes,
   squeeze whitespace. Cheap; fixes the ~3.4% exact-duplicate layer only.
2. **Cluster by co-ownership.** Two owners sharing ≥95% of a large hospital set
   are one group. This is a graph problem igraph already handles —
   build a similarity graph over owners and take connected components.
   This is what collapses the HCA family.
3. **Classify by control, not presence.** Separate controlling owners from
   passive investors using role code and percentage, so index funds stop
   outranking operators. Needs a documented threshold decision.
4. **Resolve against an external authority.** SEC EDGAR CIK for public
   companies, IRS EIN / ProPublica for nonprofits. The only way to be *right*
   rather than merely self-consistent.

Steps 1–3 are mechanical and testable against this snapshot. Step 4 is a
project.

## What the patch fixed

`patched_data/owner_name_patch.yaml` implements steps 1-3 above, declaratively,
with a stated reason on every rule. `apply_data_patch.py` rewrites the CMS CSV
into a `.patched.csv` that the ETL now consumes by default.

Measured on the 2026.07.31 snapshot:

| | Before | After |
| :--- | ---: | ---: |
| Distinct ultimate owners | 4,610 | **4,523** |
| Published owners (excl. self-owned) | 2,246 | **2,167** |
| Joint ventures | 1,623 | **1,544** |
| Owner/org pairs | 11,812 | **10,267** |
| Ownership edges | 10,566 | **8,894** |
| Exact-duplicate name rate | 3.45% | **2.28%** |

116 duplicate owner IDs merged across 3,864 rows. The HCA family collapsed
from five rows into one — **117 provider orgs / 218 hospitals**, matching the
union computed independently before the patch was written. Hospital
classification was unchanged (the five-category hierarchy is byte-identical),
confirming the patch altered owner identity only.

### Step 2 was implemented, measured, and REJECTED

Automatic co-ownership clustering does not work on this data, and the evidence
is worth keeping:

| Threshold | Result |
| :--- | :--- |
| ≥2 shared hospitals, ≥95% overlap | One **113-member** cluster fusing Tenet, LifePoint, CommonSpirit, CHI Nebraska, Texas Health Resources and St. Luke's |
| ≥10 shared hospitals, ≥95% overlap | Cleaner, but still merges **Vanguard, BlackRock and Invesco** into Encompass Health, and **Morgan Stanley** into Tenet |

The cause is transitive chaining through genuine joint ventures: if A and B
co-own one hospital and B and C co-own another, connected components merge A
with C. Joint ventures are common here, so the failure is systematic rather
than incidental.

Corporate families are therefore listed **by hand** in the patch, each with
its overlap evidence, pruned of institutional investors.

## What remains

- **Corporate-form variants are intentionally unmerged.** `TRIAD HEALTHCARE
  CORPORATION` vs `TRIAD HEALTHCARE LLC` are different legal entities. This is
  most of the residual 2.28%.
- **Only five families are curated.** Smaller chains are still fragmented.
- **Passive investors still rank high.** Flagged in the patch, but not merged
  or deleted, because removing disclosed ownership would falsify the data. The
  report labels them instead.
- **`is_JV` remains approximate**, since any residual fragmentation still
  manufactures false joint ventures.
- **Step 4 — external authority (SEC CIK, IRS EIN) — is not implemented.** It
  is the only way to be *right* rather than merely self-consistent.

Owner-level counts are materially better than before, but should still not be
quoted as authoritative market-concentration figures.
