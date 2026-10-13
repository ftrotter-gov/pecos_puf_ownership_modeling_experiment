---
title: Ultimate Owner
breadcrumb: "select ultimate_owner_name as breadcrumb from pecos.ultimate_owners where ultimate_owner_id = '${params.ultimate_owner_id}'"
---

```sql owner
select
    ultimate_owner_id,
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_partnership,
    n_nonprofit,
    max_ownership_depth,
    is_private_equity,
    is_reit,
    is_holding_company,
    is_chain_home_office
from pecos.ultimate_owners
where ultimate_owner_id = '${params.ultimate_owner_id}'
```

# {owner[0].ultimate_owner_name}

<Grid cols=3>
  <BigValue data={owner} value=n_provider_orgs title="Provider organizations" fmt="#,##0" />
  <BigValue data={owner} value=n_hospitals title="Hospitals" fmt="#,##0" />
  <BigValue data={owner} value=n_joint_ventures title="Joint ventures" fmt="#,##0" />
</Grid>

Registered in **{owner[0].owner_state ?? 'an unreported state'}**.

## Organizations owned

Every provider organization that resolves up to this owner. A joint venture
appears here *and* under its other owners.

```sql organizations
select
    org_name,
    org_type_structure,
    case proprietary_nonprofit
        when 'N' then 'Nonprofit'
        when 'P' then 'Proprietary'
        else proprietary_nonprofit
    end as profit_status,
    n_ccns,
    ownership_depth,
    is_JV,
    n_ultimate_owners
from pecos.owner_organizations
where ultimate_owner_id = '${params.ultimate_owner_id}'
order by n_ccns desc, org_name
```

<DataTable data={organizations} search=true rows=25>
  <Column id=org_name title="Provider organization" wrap=true />
  <Column id=org_type_structure title="Structure" />
  <Column id=profit_status title="Status" />
  <Column id=n_ccns title="Hospitals" fmt="#,##0" />
  <Column id=ownership_depth title="Depth" align=center />
  <Column id=is_JV title="JV?" align=center />
  <Column id=n_ultimate_owners title="Owners" align=center />
</DataTable>

## Organization mix

How this owner's provider organizations break down by legal structure, as
recorded in PECOS. "OTHER" is CMS's own catch-all value.

```sql mix
select
    org_type_structure as structure,
    count(*) as organizations,
    sum(n_ccns) as hospitals
from pecos.owner_organizations
where ultimate_owner_id = '${params.ultimate_owner_id}'
group by org_type_structure
order by organizations desc
```

<DataTable data={mix} rows=10>
  <Column id=structure title="Structure" />
  <Column id=organizations title="Organizations" fmt="#,##0" />
  <Column id=hospitals title="Hospitals" fmt="#,##0" />
</DataTable>

## Owner classification

As flagged by CMS in the All Owners file.

| Flag | Value |
| :--- | :--- |
| Private equity | {owner[0].is_private_equity ?? '—'} |
| REIT | {owner[0].is_reit ?? '—'} |
| Holding company | {owner[0].is_holding_company ?? '—'} |
| Chain home office | {owner[0].is_chain_home_office ?? '—'} |

PECOS owner ID `{owner[0].ultimate_owner_id}`.

---

[← All owners](/) · [Caveats](/caveats)

> ⚠️ Owner records are only partly de-duplicated, so a corporate family may
> still appear more than once. See **[caveats](/caveats)**.
