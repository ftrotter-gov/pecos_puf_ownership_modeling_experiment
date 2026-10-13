-- One row per ultimate owner: the searchable index that is the report.
--
-- Standalone hospitals that own themselves (is_self_owned = 'Yes') are
-- excluded. They are their own ultimate owner by definition, so including
-- them would bury the ~2,400 real corporate parents under thousands of
-- single-hospital rows and make the "largest owners first" ordering useless.
-- The index page reports how many were set aside.
SELECT
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
FROM ultimate_owner_summary
WHERE is_self_owned = 'No'
ORDER BY n_provider_orgs DESC, n_hospitals DESC
