---
title: Ultimate Owners of Medicare-Enrolled Hospitals
---

Who ultimately owns America's hospitals? This report resolves the full
ownership chain in the CMS PECOS public-use files, walking upward from each
enrolled hospital through every intermediate holding company until it reaches
an entity that nothing else owns.

```sql overview
select * from pecos.ownership_overview
```

<Grid cols=3>
  <BigValue
    data={overview}
    value=n_provider_orgs
    title="Provider organizations"
    fmt="#,##0"
  />
  <BigValue
    data={overview}
    value=n_ultimate_owners
    title="Ultimate owners"
    fmt="#,##0"
  />
  <BigValue
    data={overview}
    value=n_joint_ventures
    title="Joint ventures"
    fmt="#,##0"
  />
</Grid>

## ⚠️ Read this before using the counts

**Owners are partly de-duplicated.** CMS identifies each owner by an enrollment
ID, and one real company holds many of them, so a corporate family can appear
as several separate "ultimate owners".

A [data patch](https://github.com/ftrotter-gov/pecos_puf_ownership_modeling_experiment/blob/main/patched_data/owner_name_patch.yaml)
corrects the cases that are demonstrably the same entity — 116 duplicate owner
IDs merged, with a stated reason for each. The HCA family was the worst case,
and is now resolved:

| Before the patch | Orgs | | After |
| :--- | ---: | :-- | :--- |
| HCA INC | 115 | | |
| HCA HEALTHCARE INC | 112 | | |
| HEALTHTRUST INC - THE HOSPITAL COMPANY | 111 | → | **HCA HEALTHCARE INC** — 117 orgs, 218 hospitals |
| HERCULES HOLDING II | 104 | | |
| FRISCO HOLDING II | 103 | | |

**What is still wrong.** Only families with clear evidence were merged, so
smaller chains remain fragmented. Automatic clustering was tried and rejected
— it merged Tenet, LifePoint and CommonSpirit into a single "company" by
chaining through joint ventures.

**Index funds still rank near the top.** Vanguard and BlackRock appear because
they hold 5–10% *indirect* stakes in publicly traded chains. That is a correct
disclosure to CMS, but it is a shareholding, not control. They are flagged in
the patch as passive investors and deliberately **not** merged or deleted,
since removing disclosed ownership would falsify the data.

So: **this is a directory of reported ownership records, improved but not
authoritative.** Sorting and searching are reliable; summing a column still
is not.

## The owners

Search by owner name, or sort any column. The table opens ordered by the
number of provider organizations controlled, so the largest owners appear
first.

**`Orgs`** counts provider organizations (distinct Medicare enrollments);
**`Hospitals`** counts the CCN-identified facilities beneath them. Hospitals
exceeds orgs for most chains, because one organization frequently operates
several certified facilities.

```sql ultimate_owners
select
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_nonprofit,
    max_ownership_depth
from pecos.ultimate_owners
```

<DataTable data={ultimate_owners} search=true rows=20>
  <Column id=ultimate_owner_name title="Ultimate owner" wrap=true />
  <Column id=owner_state title="State" align=center />
  <Column id=n_provider_orgs title="Orgs" fmt="#,##0" contentType=colorscale />
  <Column id=n_hospitals title="Hospitals" fmt="#,##0" />
  <Column id=n_joint_ventures title="JVs" fmt="#,##0" />
  <Column id=n_corporation title="Corp" fmt="#,##0" />
  <Column id=n_llc title="LLC" fmt="#,##0" />
  <Column id=n_government title="Govt" fmt="#,##0" />
  <Column id=n_nonprofit title="Nonprofit" fmt="#,##0" />
  <Column id=max_ownership_depth title="Depth" align=center />
</DataTable>

## How to read this

**Ultimate owner.** An entity with no organizational owner above it in PECOS.
The resolver walks upward from each hospital through intermediate holding
companies until it runs out of parents.

**Joint ventures.** A provider organization with more than one ultimate owner
is flagged as a joint venture, and counted under *each* owner — so the `Orgs`
column sums to more than the number of hospitals. **This flag is unreliable
in exactly the way described above:** because one corporate family can appear
as several owners, a wholly owned HCA hospital is flagged `Yes` even though no
joint venture exists. Read it as "multiple ownership records", not "multiple
owners".

**Depth.** How many ownership hops PECOS reported between the hospital and
this owner. It measures *how CMS recorded the structure*, not how deep the
real corporate hierarchy is: PECOS lists direct (34) and indirect (35) parties
as a flat set, so several levels of one group arrive as siblings at depth 1
rather than as a chain. That is why the maximum depth here is only 2.

**Individuals are excluded.** Only organization-to-organization ownership
(`TYPE - OWNER = 'O'`) forms the chain. Physician owners and board members
appear in the source data but are not part of the corporate hierarchy.

## Limitations

**This is hospitals only.** The underlying file is the CMS *Hospital* Enrollments
public-use file. Hospices, skilled nursing facilities, and home health agencies
are published by CMS as separate files and are **not** included here, so the
counts describe an owner's hospital footprint, not its total healthcare
footprint. An owner with 300 nursing homes and 2 hospitals shows as 2.

**Standalone hospitals are set aside.** Hospitals that own themselves — those
with no organizational owner, typically government and nonprofit facilities —
are excluded from the table above so they do not bury the real corporate
parents. They remain in the underlying data.

**CMS data quality carries through.** The source lists 1,106 organizations as
their own owner, and 1,108 pairs that each appear to own the other. Both are
artifacts of officer and managing-employee rows rather than real ownership,
and both disappear once the data is restricted to organizational ownership —
the resulting ownership graph is acyclic. Direct-ownership percentages still
sum above 100% for about 2% of enrollments in the source itself.

**Ownership is as-reported.** PECOS reflects what providers filed, with no
independent verification, and the snapshot is a point in time.

<Details title="Where this data comes from">

Built from two CMS monthly public-use files, **Hospital Enrollments** and
**Hospital All Owners**, published under
[Provider Characteristics → Hospitals & Other Facilities](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities).
Current snapshot: **2026.07.31**.

The pipeline is Python and DuckDB; this site is
[Evidence](https://evidence.dev). Everything builds locally — there is no CI —
and validation runs as [InLaw](https://pypi.org/project/inlaw/) / Great
Expectations checks in `inlaw_tests/`.

</Details>
