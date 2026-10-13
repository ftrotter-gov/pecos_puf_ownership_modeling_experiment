-- One row per (ultimate owner, provider organization): the drill-down detail.
--
-- Powers the per-owner pages at /owners/[ultimate_owner_id]. Every provider
-- organization appears once per ultimate owner, so a joint venture shows up
-- under each of its owners -- which is the behaviour the report describes.
--
-- Self-owned standalone hospitals are kept here even though the index page
-- hides them, so that a direct link to such an owner still resolves instead
-- of rendering an empty page.
SELECT
    ultimate_owner_id,
    ultimate_owner_name,
    org_id,
    org_name,
    org_type_structure,
    proprietary_nonprofit,
    n_ccns,
    ownership_depth,
    n_ultimate_owners,
    is_JV
FROM ultimate_owner_by_org
ORDER BY ultimate_owner_id, n_ccns DESC, org_name
