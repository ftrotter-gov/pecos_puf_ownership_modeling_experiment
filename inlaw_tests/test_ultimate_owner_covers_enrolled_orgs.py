"""ultimate_owner_by_org covers every enrolled org, and nothing else.

Spec: AI_Instructions/UltimateOwnerReport.md.

Two failure modes, one in each direction, both caught here.

UNDER-COVERAGE: an enrolled provider organization with no row at all. Orgs
with no organizational owner (government bodies, nonprofits, individually
held hospitals) must still appear, as their own ultimate owner at depth 0. If
they are dropped, the report silently omits roughly 2,100 hospitals.

OVER-COVERAGE: a row for something that is not an enrolled provider. This
happened during development -- 312 intermediate holding companies appear as
OWNED nodes in ownership_edges, and without an enrolled-only filter they were
counted as provider organizations, inflating "provider orgs covered" to 5,588
against an actual enrollment count of 5,276. The report would have counted
holding companies as if they were hospitals.

Both sides must be exactly zero; there is no tolerated baseline here, because
this is pipeline logic rather than a defect inherited from CMS data.
"""

from inlaw import DBTable, InLaw


class TestUltimateOwnerCoversEnrolledOrgs(InLaw):
    title = "ultimate_owner_by_org covers exactly the enrolled provider organizations"

    @staticmethod
    def run(engine, settings=None):
        ultimate_owner_by_org = DBTable(schema="main", table="ultimate_owner_by_org")
        hospital_enrollments = DBTable(schema="main", table="hospital_enrollments")

        sql = f"""
            WITH enrolled AS (
                SELECT DISTINCT "ASSOCIATE ID" AS org_id
                FROM {hospital_enrollments}
                WHERE TRIM(COALESCE("ASSOCIATE ID", '')) <> ''
            ),
            reported AS (
                SELECT DISTINCT org_id FROM {ultimate_owner_by_org}
            )
            SELECT
                (SELECT COUNT(*) FROM enrolled
                 WHERE org_id NOT IN (SELECT org_id FROM reported)) AS missing_count,
                (SELECT COUNT(*) FROM reported
                 WHERE org_id NOT IN (SELECT org_id FROM enrolled)) AS extra_count
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)

        missing_result = gx_df.expect_column_values_to_be_between(
            column="missing_count", min_value=0, max_value=0
        )
        if not missing_result.success:
            unexpected_values = missing_result.result.get("partial_unexpected_list") or []
            observed = unexpected_values[0] if unexpected_values else "unknown"
            return (
                f"{observed} enrolled provider organizations have no ultimate "
                f"owner row. Orgs with no organizational owner must still "
                f"appear as their own ultimate owner at depth 0 -- check the "
                f"'vertex is None' branch of resolve_ultimate_owners() "
                f"(build_ownership_graph.py)."
            )

        extra_result = gx_df.expect_column_values_to_be_between(
            column="extra_count", min_value=0, max_value=0
        )
        if not extra_result.success:
            unexpected_values = extra_result.result.get("partial_unexpected_list") or []
            observed = unexpected_values[0] if unexpected_values else "unknown"
            return (
                f"{observed} rows describe organizations that are not enrolled "
                f"providers -- most likely intermediate holding companies "
                f"leaking in from ownership_edges. resolve_ultimate_owners() "
                f"(build_ownership_graph.py) must iterate enrolled orgs only."
            )

        return True
