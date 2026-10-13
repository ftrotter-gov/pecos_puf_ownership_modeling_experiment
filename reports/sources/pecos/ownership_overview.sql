-- Headline counts for the top of the report.
--
-- Computed here rather than in the browser so the page renders its summary
-- numbers from a single six-row table instead of aggregating the full
-- ownership table client-side.
SELECT
    (SELECT COUNT(DISTINCT org_id) FROM ultimate_owner_by_org)
        AS n_provider_orgs,
    (SELECT COUNT(*) FROM ultimate_owner_summary WHERE is_self_owned = 'No')
        AS n_ultimate_owners,
    (SELECT COUNT(DISTINCT org_id) FROM ultimate_owner_by_org WHERE is_JV = 'Yes')
        AS n_joint_ventures,
    (SELECT COUNT(*) FROM ultimate_owner_summary WHERE is_self_owned = 'Yes')
        AS n_self_owned,
    (SELECT COUNT(*) FROM ownership_edges)
        AS n_ownership_edges,
    (SELECT MAX(ownership_depth) FROM ultimate_owner_by_org)
        AS max_ownership_depth
