---
title: Ultimate Owners of Medicare-Enrolled Hospitals
---

Who ultimately owns America's hospitals? This report walks the ownership chain
in the CMS PECOS public-use files — from each enrolled hospital, up through
every intermediate holding company, to the entity that nothing else owns.

**Click any owner to see the hospitals they control.**

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

## Search and filter

```sql states
select distinct owner_state as state
from pecos.ultimate_owners
where owner_state is not null and trim(owner_state) <> ''
order by state
```

<Dropdown
  data={states}
  name=selected_state
  value=state
  title="Owner state"
  defaultValue="%"
>
  <DropdownOption value="%" valueLabel="All states" />
</Dropdown>

<Slider
  name=min_orgs
  title="Minimum provider organizations"
  defaultValue=1
  min=1
  max=50
  step=1
/>

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
    max_ownership_depth,
    '/owners/' || ultimate_owner_id as owner_link
from pecos.ultimate_owners
where coalesce(owner_state, '') like '${inputs.selected_state.value}'
  and n_provider_orgs >= ${inputs.min_orgs}
order by n_provider_orgs desc, n_hospitals desc
```

<DataTable data={ultimate_owners} search=true rows=20 link=owner_link>
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

**Orgs vs. Hospitals.** `Orgs` counts provider organizations (distinct Medicare
enrollments); `Hospitals` counts the CCN-identified facilities beneath them.
Hospitals exceeds orgs for most chains, because one organization often operates
several certified facilities.

**Joint ventures.** A provider organization with more than one ultimate owner.
It is counted under *each* owner, so the `Orgs` column sums to more than the
total number of hospitals.

**Depth.** How many ownership hops PECOS recorded between the hospital and this
owner.

**Individuals are excluded.** Only organization-to-organization ownership forms
the chain. Physician owners and board members appear in the source data but are
not part of the corporate hierarchy.

> ⚠️ **These counts have real limitations.** Owners are only partly
> de-duplicated, index funds rank near the top, and the joint-venture flag is
> approximate. **[Read the caveats](/caveats)** before quoting any number here.
