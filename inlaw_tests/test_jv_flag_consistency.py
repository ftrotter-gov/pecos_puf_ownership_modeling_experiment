"""is_JV says Yes exactly when an organization has more than one ultimate owner.

Spec: AI_Instructions/UltimateOwnerReport.md.

The report requirement is that a provider organization with multiple ultimate
owners is a Joint Venture, shown as one row per ultimate owner, each carrying
is_JV = 'Yes'. Both columns are computed from the same window function in
PATHS_SQL, so this check pins them to each other and to the actual row count.

Three assertions, since each can break independently:

  1. n_ultimate_owners equals the real number of rows for that org.
  2. is_JV = 'Yes' whenever n_ultimate_owners > 1.
  3. is_JV = 'No'  whenever n_ultimate_owners = 1.

On the 2026.07.31 snapshot 1,623 provider organizations are joint ventures.
"""

from inlaw import DBTable, InLaw


class TestJvFlagConsistency(InLaw):
    title = "is_JV is Yes exactly when an org has more than one ultimate owner"

    @staticmethod
    def run(engine, settings=None):
        ultimate_owner_by_org = DBTable(schema="main", table="ultimate_owner_by_org")

        sql = f"""
            WITH actual AS (
                SELECT
                    org_id,
                    COUNT(*)                        AS actual_owner_count,
                    ANY_VALUE(n_ultimate_owners)    AS reported_owner_count,
                    MAX(CASE WHEN is_JV = 'Yes' THEN 1 ELSE 0 END) AS any_jv_yes,
                    MIN(CASE WHEN is_JV = 'Yes' THEN 1 ELSE 0 END) AS all_jv_yes
                FROM {ultimate_owner_by_org}
                GROUP BY org_id
            )
            SELECT
                COUNT(*) FILTER (
                    WHERE actual_owner_count <> reported_owner_count
                ) AS miscounted,
                COUNT(*) FILTER (
                    WHERE actual_owner_count > 1 AND all_jv_yes = 0
                ) AS jv_not_flagged,
                COUNT(*) FILTER (
                    WHERE actual_owner_count = 1 AND any_jv_yes = 1
                ) AS single_owner_flagged_jv
            FROM actual
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)

        checks = (
            (
                "miscounted",
                "organizations where n_ultimate_owners disagrees with the "
                "actual number of ultimate owner rows",
            ),
            (
                "jv_not_flagged",
                "joint ventures (more than one ultimate owner) that are not "
                "flagged is_JV = 'Yes' on every row",
            ),
            (
                "single_owner_flagged_jv",
                "organizations with a single ultimate owner incorrectly "
                "flagged is_JV = 'Yes'",
            ),
        )

        for column, description in checks:
            result = gx_df.expect_column_values_to_be_between(
                column=column, min_value=0, max_value=0
            )
            if not result.success:
                unexpected_values = result.result.get("partial_unexpected_list") or []
                observed = unexpected_values[0] if unexpected_values else "unknown"
                return (
                    f"Found {observed} {description}. The is_JV and "
                    f"n_ultimate_owners columns are both derived from the same "
                    f"window function in PATHS_SQL (build_ownership_graph.py); "
                    f"they have drifted apart."
                )

        return True
