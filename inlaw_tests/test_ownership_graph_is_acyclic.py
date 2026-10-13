"""The filtered ownership graph contains no cycles.

Spec: AI_Instructions/UltimateOwnerReport.md.

Established with igraph on the 2026.07.31 snapshot: once edges are restricted
to organizational ownership (TYPE - OWNER = 'O', role codes 34/35) with
self-loops removed, strongly connected component decomposition finds no
component larger than a single vertex, and is_dag() returns true.

This is NOT true of the raw file, which carries 1,106 self-ownership rows and
1,108 reciprocal edge-ends (A owns B, B owns A). Those live in the officer,
director, and managing-employee rows -- not ownership -- and the role filter
removes every one of them.

The property is worth pinning because the pipeline reports an ownership DEPTH.
Depth is only meaningful on an acyclic graph; if a future snapshot introduces
a real ownership cycle, the depths become arbitrary and that should surface
here rather than as quietly wrong numbers in the published report.

The check is a 2-cycle probe rather than a full SCC decomposition, because
InLaw expectations run in SQL: it looks for any pair of organizations that
each own the other. That catches the reciprocal case the raw data actually
exhibits. build_ownership_graph.py additionally runs igraph's full is_dag()
on every build and prints a warning for longer cycles.
"""

from inlaw import DBTable, InLaw


class TestOwnershipGraphIsAcyclic(InLaw):
    title = "No two organizations in ownership_edges own each other"

    @staticmethod
    def run(engine, settings=None):
        ownership_edges = DBTable(schema="main", table="ownership_edges")

        sql = f"""
            SELECT COUNT(*) AS reciprocal_pair_count
            FROM {ownership_edges} a
            JOIN {ownership_edges} b
              ON a.owner_id = b.org_id
             AND a.org_id   = b.owner_id
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="reciprocal_pair_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = unexpected_values[0] if unexpected_values else "unknown"

        return (
            f"Found {observed} reciprocal ownership edges: organizations that "
            f"own each other. The ownership graph was acyclic on the "
            f"2026.07.31 snapshot, and ownership_depth is only meaningful "
            f"while it stays that way. Check whether the role-code filter in "
            f"EDGES_SQL (build_ownership_graph.py) still excludes officer and "
            f"managing-employee rows, which is where cycles come from."
        )
