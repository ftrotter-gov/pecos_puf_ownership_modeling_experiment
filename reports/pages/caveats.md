---
title: Caveats and Known Limitations
---

**Read this before quoting any number from this report.** The data is useful
for finding and exploring ownership records. It is **not** an authoritative
measure of market concentration, and several of its headline counts are known
to be wrong in specific, documented ways.

## 1. Owners are only partly de-duplicated

CMS identifies an owner by *enrollment ID*, not by company, and one real
company holds many. Left uncorrected, a corporate family appears as several
separate "ultimate owners".

A [data patch](https://github.com/ftrotter-gov/pecos_puf_ownership_modeling_experiment/blob/main/patched_data/owner_name_patch.yaml)
fixes the cases that are demonstrably the same entity — 116 duplicate owner
IDs merged, each with a stated reason. HCA was the worst case:

| Before the patch | Orgs | | After |
| :--- | ---: | :-- | :--- |
| HCA INC | 115 | | |
| HCA HEALTHCARE INC | 112 | | |
| HEALTHTRUST INC - THE HOSPITAL COMPANY | 111 | → | **HCA HEALTHCARE INC** — 117 orgs, 218 hospitals |
| HERCULES HOLDING II | 104 | | |
| FRISCO HOLDING II | 103 | | |

**89 hospitals had listed all five at once.**

### What is still wrong

Only families with clear evidence were merged, so **smaller chains remain
fragmented**. Two deliberate exclusions:

- **Corporate form is never merged.** `TRIAD HEALTHCARE CORPORATION` and
  `TRIAD HEALTHCARE LLC` stay separate — Inc and LLC are distinct legal
  entities, and merging them would assert a fact not in evidence.
- **Automatic clustering was rejected.** Grouping owners that share ≥95% of
  their hospitals chains unrelated companies together through genuine joint
  ventures: at a 2-hospital threshold it fused **Tenet, LifePoint,
  CommonSpirit, CHI and Texas Health Resources** into one 113-member
  "company". Even at ≥10 shared hospitals it pulled Vanguard, BlackRock and
  Invesco into Encompass Health.

Roughly **2.3%** of owner names remain exact duplicates under normalization,
down from 3.45% before the patch.

## 2. Index funds rank as owners

**Vanguard and BlackRock appear near the top of the table.** They hold 5–10%
*indirect* (role 35) stakes in publicly traded hospital chains — index-fund
positions, correctly disclosed to CMS, but a shareholding rather than control.

They are flagged in the patch as passive investors and deliberately **not**
merged or deleted: removing disclosed ownership would falsify the data.

Note also that "VANGUARD GROUP INC" (the index fund) and "VANGUARD HEALTH
SYSTEMS" (a Tenet subsidiary) are **different companies** with similar names.

## 3. The joint-venture flag is approximate

`is_JV` means "this organization has more than one ultimate owner". Because
owner de-duplication is incomplete, **a wholly owned hospital can be flagged
as a joint venture** purely because its owner still appears more than once.

Treat it as *"multiple ownership records"*, not *"multiple owners"*.

## 4. Depth measures reporting, not corporate structure

Maximum ownership depth is **2**, which understates real corporate hierarchies.

PECOS records a hospital's direct (role 34) and indirect (role 35) parties as
a **flat list**, not as a parent-of-parent chain. Five levels of one corporate
hierarchy arrive as five siblings at depth 1. So depth describes *how CMS
recorded the structure*, not how deep it actually goes.

## 5. Hospitals only

This is built from the CMS **Hospital** Enrollments public-use file. Hospices,
skilled nursing facilities, and home health agencies are published separately
and are **not** included.

The counts therefore describe an owner's **hospital footprint, not its total
healthcare footprint**. An owner with 300 nursing homes and 2 hospitals shows
as 2.

## 6. Source data quality carries through

- **1,106 organizations are listed as their own owner**, and 1,108 pairs each
  appear to own the other. Both are artifacts of officer and
  managing-employee rows rather than real ownership, and both disappear once
  the data is restricted to organizational ownership roles. The resulting
  ownership graph is acyclic.
- **Direct-ownership percentages sum above 100%** for about 2% of enrollments
  in the source itself.
- **About 1% of hospital CCNs are malformed** (a valid 6-character CCN with a
  suffix appended). They are passed through untouched.
- **Ownership is as-reported.** PECOS reflects what providers filed, with no
  independent verification, and the snapshot is a point in time.

## 7. What would make this authoritative

Not implemented, and each is a project:

1. **External entity resolution** — SEC EDGAR CIK for public companies, IRS
   EIN / ProPublica for nonprofits. The only way to be *right* rather than
   merely self-consistent.
2. **Control vs. passive classification** with a defensible ownership-share
   threshold, so index funds stop outranking operators.
3. **The other provider-type files**, for a complete healthcare footprint.

<Details title="Where this data comes from">

Built from two CMS monthly public-use files, **Hospital Enrollments** and
**Hospital All Owners**, published under
[Provider Characteristics → Hospitals & Other Facilities](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities).
Current snapshot: **2026.07.31**.

The pipeline is Python and DuckDB, with the ownership graph resolved using
[igraph](https://python.igraph.org/); this site is
[Evidence](https://evidence.dev). Everything builds locally — there is no CI —
and validation runs as 19 [InLaw](https://pypi.org/project/inlaw/) / Great
Expectations checks.

Full analysis of the entity-resolution problem is in
[`AI_Instructions/EntityResolutionProblem.md`](https://github.com/ftrotter-gov/pecos_puf_ownership_modeling_experiment/blob/main/AI_Instructions/EntityResolutionProblem.md).

</Details>

---

[← Back to the report](/)
