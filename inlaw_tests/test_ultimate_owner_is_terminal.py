"""Every ultimate owner is terminal: nothing owns it in turn.

Spec: AI_Instructions/UltimateOwnerReport.md.

This is the definition of "ultimate owner", asserted directly. If an entity
in ultimate_owner_by_org.ultimate_owner_id also appears as an OWNED node in
ownership_edges, the upward walk stopped early and the real parent above it
was never reached.

Resolution is igraph's subcomponent(mode='out'): everything reachable upward
from an org, keeping those with out-degree 0. A regression would most likely
come from reversing the edge direction (org -> owner) or changing the terminal
test, either of which silently returns the wrong entity as "ultimate" while
still producing a plausible-looking row count.
"""

from inlaw import DBTable, InLaw


class TestUltimateOwnerIsTerminal(InLaw):
    title = "No ultimate owner appears as an owned organization in ownership_edges"

    @staticmethod
    def run(engine, settings=None):
        ultimate_owner_by_org = DBTable(schema="main", table="ultimate_owner_by_org")
        ownership_edges = DBTable(schema="main", table="ownership_edges")

        sql = f"""
            SELECT COUNT(DISTINCT ultimate_owner_id) AS non_terminal_count
            FROM {ultimate_owner_by_org}
            WHERE ultimate_owner_id IN (SELECT org_id FROM {ownership_edges})
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="non_terminal_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = unexpected_values[0] if unexpected_values else "unknown"

        return (
            f"{observed} entities are reported as ultimate owners even though "
            f"ownership_edges shows something owning them. The upward walk in "
            f"resolve_ultimate_owners() (build_ownership_graph.py) is stopping "
            f"too early -- check the edge direction and the out-degree test."
        )
