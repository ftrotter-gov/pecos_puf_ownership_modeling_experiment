"""ownership_edges contains no organization that owns itself.

Spec: AI_Instructions/UltimateOwnerReport.md.

The All Owners file lists 1,106 rows where ASSOCIATE ID - OWNER equals
ASSOCIATE ID -- an organization recorded as its own owner. Left in place,
each one becomes a terminal node in the upward walk, so the affected hospital
resolves to itself as its own "ultimate owner" and disappears from the chain
it actually belongs to.

build_ownership_graph.py drops them in EDGES_SQL. This check asserts the drop
actually happened, because a regression here is silent: the report would still
build, still look reasonable, and simply understate large owners.
"""

from inlaw import DBTable, InLaw


class TestOwnershipEdgesNoSelfLoops(InLaw):
    title = "ownership_edges contains no self-owning organizations"

    @staticmethod
    def run(engine, settings=None):
        ownership_edges = DBTable(schema="main", table="ownership_edges")

        sql = f"""
            SELECT COUNT(*) AS self_loop_count
            FROM {ownership_edges}
            WHERE owner_id = org_id
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="self_loop_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = unexpected_values[0] if unexpected_values else "unknown"

        return (
            f"ownership_edges contains {observed} self-owning rows. The "
            f"`TRIM(\"ASSOCIATE ID - OWNER\") <> TRIM(\"ASSOCIATE ID\")` filter in "
            f"EDGES_SQL (build_ownership_graph.py) is not doing its job; "
            f"affected hospitals will resolve to themselves as ultimate owner."
        )
