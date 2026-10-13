"""Resolve ultimate ownership for every enrolled provider organization.

Spec: AI_Instructions/UltimateOwnerReport.md.

Runs AFTER build_hierarchy.py, reading the tables it wrote to data/pecos.duckdb
and adding the tables the Evidence report in reports/ queries.

WHY THE GRAPH IS RESOLVED HERE AND NOT IN THE REPORT
----------------------------------------------------
Evidence ships parquet to the browser and queries it with DuckDB-WASM.
Resolving reachability over a graph client-side would be slow and fragile.
Doing it once here means the report only ever runs flat SELECT/GROUP BY.

THE RESOLUTION USES igraph
--------------------------
The ownership structure is a graph, so it is handled with a graph library
rather than a hand-rolled recursive CTE. igraph does the two things needed
here directly, in C:

    decompose(mode='weak')     split into independent ownership families
    subcomponent(v, mode='out') everything reachable upward from one org

Edges point ORG -> OWNER, so walking "out" walks upward toward owners, and an
ultimate owner is simply a vertex with out-degree 0.

WHAT THE GRAPH ACTUALLY LOOKS LIKE
----------------------------------
Measured on the 2026.07.31 snapshot, after filtering:

    org -> org edges (TYPE='O', ROLE 34/35)      10,566
    vertices                                      5,506
    weakly connected components                     563
    largest component                             2,903 vertices
    terminal owners (out-degree 0)                2,388
    is_dag                                         True

The filtered ownership graph IS ACYCLIC -- igraph's strongly connected
component decomposition finds no component larger than one vertex.

This is worth stating plainly because the RAW file is not acyclic: it contains
1,106 self-ownership rows and 1,108 reciprocal edge-ends (A owns B, B owns A).
Every one of those disappears once the edge set is restricted to
organizational ownership roles 34/35 with self-loops removed. The cycles live
in the officer/director/managing-employee rows, which are not ownership and
are excluded.

The code does NOT assume acyclicity, because a future snapshot could
introduce a real cycle. is_dag() is checked at build time and reported; the
reachability approach used here terminates correctly either way, since
subcomponent() visits each vertex once rather than walking paths.

An "ultimate owner" is a node with no organizational owner above it. Orgs that
have no organizational owner at all (government bodies, nonprofits, and
individually held hospitals) are their own ultimate owner at depth 0, so every
provider organization appears in the report rather than dropping out.

Usage:
    python build_ownership_graph.py [allowners_file]
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import igraph as ig
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

# Patched copies of the CMS files, produced by apply_data_patch.py. Version
# controlled, unlike data/ -- see patched_data/README.md.
PATCHED_DATA_DIR = Path(__file__).resolve().parent / "patched_data"

DUCKDB_PATH = DATA_DIR / "pecos.duckdb"

# The PATCHED owners file, matching build_hierarchy.py. See
# patched_data/README.md; regenerate with `make patch`.
DEFAULT_ALLOWNERS_FILE = "Hospital_All_Owners_2026.07.31_update.patched.csv"

# CMS ships these files Windows-1252 encoded, not UTF-8. Matches
# build_hierarchy.py SOURCE_ENCODING.
SOURCE_ENCODING = "cp1252"

# Owner name and classification flags. build_hierarchy.py does not load these
# columns, so the owner dimension is read from the source CSV directly rather
# than inventing names from the ID.
OWNER_DIM_COLUMNS = [
    "ASSOCIATE ID - OWNER",
    "TYPE - OWNER",
    "ORGANIZATION NAME - OWNER",
    "DOING BUSINESS AS NAME - OWNER",
    "STATE - OWNER",
    "PRIVATE EQUITY COMPANY - OWNER",
    "REIT - OWNER",
    "HOLDING COMPANY - OWNER",
    "CHAIN HOME OFFICE - OWNER",
    "NON PROFIT - OWNER",
    "FOR PROFIT - OWNER",
]

# 34 = direct owner, 35 = indirect owner. Only these two role codes describe
# ownership; the rest (25, 36-44) are officers, directors, and managing
# employees, which must not create ownership edges.
OWNERSHIP_ROLE_CODES = ("34", "35")

# No recursion depth ceiling is needed. igraph's subcomponent() visits each
# vertex at most once, so traversal terminates on its own -- the hand-rolled
# recursive CTE this replaced needed an explicit depth cap and path guard.


def resolve_input(filename: str) -> Path:
    """Find a source file in patched_data/ or data/.

    Mirrors resolve_input() in build_hierarchy.py. The two scripts cannot
    share it: InLaw loads check files standalone and the pipeline scripts are
    run independently, so each stays self-contained.
    """
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate

    for directory in (PATCHED_DATA_DIR, DATA_DIR):
        path = directory / filename
        if path.exists():
            return path

    hint = PATCHED_DATA_DIR if ".patched." in filename else DATA_DIR
    raise FileNotFoundError(
        f"{filename} not found in {PATCHED_DATA_DIR.name}/ or {DATA_DIR.name}/. "
        f"Expected it at {hint / filename}. "
        f"If it is a patched file, run 'make patch' first."
    )


def load_owner_dimension(allowners_file: str) -> pd.DataFrame:
    """Read owner names and classification flags from the source CSV.

    One row per organizational owner. Verified on the 2026.07.31 snapshot:
    4,086 owner associate IDs, zero blank organization names, and zero IDs
    carrying more than one distinct name -- so first() is a safe collapse.
    """
    owners = pd.read_csv(
        resolve_input(allowners_file),
        usecols=OWNER_DIM_COLUMNS,
        dtype=str,
        encoding=SOURCE_ENCODING,
        keep_default_na=False,
        na_values=[],
    )

    owners = owners[owners["TYPE - OWNER"].str.strip().str.upper() == "O"].copy()

    owner_dim = (
        owners.groupby("ASSOCIATE ID - OWNER", as_index=False)
        .first()
        .rename(
            columns={
                "ASSOCIATE ID - OWNER": "owner_id",
                "ORGANIZATION NAME - OWNER": "owner_name",
                "DOING BUSINESS AS NAME - OWNER": "owner_dba_name",
                "STATE - OWNER": "owner_state",
                "PRIVATE EQUITY COMPANY - OWNER": "is_private_equity",
                "REIT - OWNER": "is_reit",
                "HOLDING COMPANY - OWNER": "is_holding_company",
                "CHAIN HOME OFFICE - OWNER": "is_chain_home_office",
                "NON PROFIT - OWNER": "is_non_profit",
                "FOR PROFIT - OWNER": "is_for_profit",
            }
        )
        .drop(columns=["TYPE - OWNER"])
    )

    return owner_dim


# Organization-to-organization ownership edges, cleaned.
#
# Three filters, each load-bearing:
#   TYPE - OWNER = 'O'     individuals are not part of the corporate chain
#   ROLE CODE in (34, 35)  ownership roles only, not officers/directors
#   owner <> owned         drops the 1,106 self-loops that would otherwise
#                          make every affected org its own ultimate owner
EDGES_SQL = f"""
CREATE OR REPLACE TABLE ownership_edges AS
SELECT DISTINCT
    "ASSOCIATE ID - OWNER" AS owner_id,
    "ASSOCIATE ID"         AS org_id,
    MAX(CASE WHEN "ROLE CODE - OWNER" = '34' THEN 1 ELSE 0 END)
        OVER (PARTITION BY "ASSOCIATE ID - OWNER", "ASSOCIATE ID") AS is_direct
FROM hospital_allowners
WHERE TRIM(UPPER("TYPE - OWNER")) = 'O'
  AND TRIM("ROLE CODE - OWNER") IN {OWNERSHIP_ROLE_CODES}
  AND TRIM("ASSOCIATE ID - OWNER") <> TRIM("ASSOCIATE ID")
  AND TRIM(COALESCE("ASSOCIATE ID - OWNER", '')) <> ''
  AND TRIM(COALESCE("ASSOCIATE ID", '')) <> ''
"""

def build_ownership_digraph(edges: pd.DataFrame) -> ig.Graph:
    """Build the directed ownership graph, with edges pointing ORG -> OWNER.

    That direction is the whole trick: walking OUT from a hospital walks
    UPWARD through its owners, so an ultimate owner is just a vertex with
    out-degree 0, and everything above a hospital is one subcomponent call.
    """
    return ig.Graph.TupleList(
        edges[["org_id", "owner_id"]].itertuples(index=False, name=None),
        directed=True,
    )


def describe_graph(graph: ig.Graph) -> dict:
    """Summarize the graph's shape, including whether it is acyclic.

    is_dag() is reported rather than assumed. On the 2026.07.31 snapshot the
    filtered graph is acyclic, but a future snapshot could introduce a real
    ownership cycle and that should be visible in the build output rather than
    silently changing the results.

    decompose(mode='weak') splits the graph into independent ownership
    families -- subgraphs with no ownership link between them. Nothing in the
    resolution needs them, but the count and the largest size say more about
    the shape of US hospital ownership than any single number here.
    """
    components = graph.decompose(mode="weak")
    sizes = sorted((component.vcount() for component in components), reverse=True)

    return {
        "vertices": graph.vcount(),
        "edges": graph.ecount(),
        "is_dag": graph.is_dag(),
        "components": len(components),
        "largest_component": sizes[0] if sizes else 0,
        "terminal_owners": sum(1 for v in graph.vs if v.outdegree() == 0),
    }


def resolve_ultimate_owners(
    graph: ig.Graph, enrolled_org_ids: set[str]
) -> pd.DataFrame:
    """Map every enrolled provider organization to its ultimate owner(s).

    For each enrolled org, subcomponent(mode='out') returns every vertex
    reachable upward through ownership. The ultimate owners are those reachable
    vertices with out-degree 0 -- nothing owns them in turn.

    subcomponent() visits each vertex at most once, so this terminates even if
    a future snapshot introduces a cycle. The old recursive CTE needed an
    explicit path guard to get the same safety.

    Orgs with no ownership edges at all (government bodies, nonprofits,
    individually held hospitals) are not in the graph. They are their own
    ultimate owner, and are added here so no provider organization is dropped.

    Only ENROLLED orgs become rows. Intermediate holding companies are vertices
    in the graph but are not providers, and counting them as such previously
    inflated the provider total by 312.
    """
    names = graph.vs["name"]
    is_terminal = [vertex.outdegree() == 0 for vertex in graph.vs]
    in_graph = {name: index for index, name in enumerate(names)}

    # Depth is the shortest number of ownership hops from org to owner. Taken
    # from igraph's BFS distances so it stays consistent with reachability.
    records: list[tuple[str, str, int]] = []

    for org_id in sorted(enrolled_org_ids):
        vertex = in_graph.get(org_id)

        if vertex is None:
            # No organizational owner anywhere: its own ultimate owner.
            records.append((org_id, org_id, 0))
            continue

        reachable = graph.subcomponent(vertex, mode="out")
        terminals = [index for index in reachable if is_terminal[index]]

        if not terminals:
            # Only possible if org sits in a cycle with no exit. Not present in
            # the current snapshot (the graph is a DAG), but handled so a future
            # one degrades to "owns itself" instead of vanishing.
            records.append((org_id, org_id, 0))
            continue

        distances = graph.distances(source=vertex, target=terminals, mode="out")[0]
        for terminal, distance in zip(terminals, distances):
            depth = int(distance) if distance != float("inf") else 0
            records.append((org_id, names[terminal], depth))

    return pd.DataFrame(
        records, columns=["org_id", "ultimate_owner_id", "depth"]
    ).drop_duplicates()


# Enrich the resolved (org, ultimate owner) pairs with names and attributes.
#
# The pairs themselves come from igraph via resolve_ultimate_owners(), which is
# registered as `ultimate_pairs`. This SQL only joins and labels -- all graph
# traversal happens in igraph.
PATHS_SQL = """
CREATE OR REPLACE TABLE ultimate_owner_by_org AS
WITH org_dim AS (
    SELECT
        "ASSOCIATE ID" AS org_id,
        ANY_VALUE("ORGANIZATION NAME")           AS org_name,
        ANY_VALUE("ORGANIZATION TYPE STRUCTURE") AS org_type_structure,
        ANY_VALUE("PROPRIETARY NONPROFIT")       AS proprietary_nonprofit,
        COUNT(DISTINCT CCN) FILTER (WHERE TRIM(COALESCE(CCN, '')) <> '') AS n_ccns
    FROM hospital_enrollments
    GROUP BY 1
)
SELECT
    c.org_id,
    d.org_name,
    d.org_type_structure,
    d.proprietary_nonprofit,
    COALESCE(d.n_ccns, 0)::BIGINT AS n_ccns,
    c.ultimate_owner_id,
    -- Self-owned orgs carry their own enrollment name; everyone else takes
    -- the owner name from the All Owners file.
    COALESCE(o.owner_name, d.org_name) AS ultimate_owner_name,
    o.owner_state,
    o.is_private_equity,
    o.is_reit,
    o.is_holding_company,
    o.is_chain_home_office,
    c.depth AS ownership_depth,
    COUNT(*) OVER (PARTITION BY c.org_id) AS n_ultimate_owners,
    CASE WHEN COUNT(*) OVER (PARTITION BY c.org_id) > 1
         THEN 'Yes' ELSE 'No' END AS is_JV
FROM ultimate_pairs c
LEFT JOIN org_dim   d ON d.org_id   = c.org_id
LEFT JOIN owner_dim o ON o.owner_id = c.ultimate_owner_id
"""

# One row per ultimate owner: the spine of the report, ordered so the largest
# owners land at the top.
SUMMARY_SQL = """
CREATE OR REPLACE TABLE ultimate_owner_summary AS
SELECT
    ultimate_owner_id,
    ANY_VALUE(ultimate_owner_name) AS ultimate_owner_name,
    ANY_VALUE(owner_state)         AS owner_state,
    COUNT(DISTINCT org_id)         AS n_provider_orgs,
    SUM(n_ccns)::BIGINT            AS n_hospitals,
    COUNT(DISTINCT org_id) FILTER (WHERE is_JV = 'Yes') AS n_joint_ventures,
    COUNT(DISTINCT org_id) FILTER (WHERE org_type_structure = 'CORPORATION') AS n_corporation,
    COUNT(DISTINCT org_id) FILTER (WHERE org_type_structure = 'LLC')         AS n_llc,
    COUNT(DISTINCT org_id) FILTER (WHERE org_type_structure = 'GOVERNMENT')  AS n_government,
    COUNT(DISTINCT org_id) FILTER (WHERE org_type_structure = 'PARTNERSHIP') AS n_partnership,
    COUNT(DISTINCT org_id) FILTER (WHERE proprietary_nonprofit = 'N')        AS n_nonprofit,
    MAX(ownership_depth)           AS max_ownership_depth,
    ANY_VALUE(is_private_equity)   AS is_private_equity,
    ANY_VALUE(is_reit)             AS is_reit,
    ANY_VALUE(is_holding_company)  AS is_holding_company,
    ANY_VALUE(is_chain_home_office) AS is_chain_home_office,
    -- Self-owned single orgs are not really "owners"; flagging them lets the
    -- report separate real corporate parents from standalone hospitals.
    CASE WHEN MAX(ownership_depth) = 0 AND COUNT(DISTINCT org_id) = 1
         THEN 'Yes' ELSE 'No' END AS is_self_owned
FROM ultimate_owner_by_org
GROUP BY ultimate_owner_id
ORDER BY n_provider_orgs DESC, n_hospitals DESC
"""


def build_tables(connection: duckdb.DuckDBPyConnection) -> dict:
    """Create the three ownership tables, in dependency order.

    SQL cleans the edges and labels the results; igraph does the traversal in
    between. Returns the graph summary so main() can report it.
    """
    connection.execute(EDGES_SQL)

    edges = connection.execute(
        "SELECT org_id, owner_id FROM ownership_edges"
    ).df()
    enrolled_org_ids = set(
        connection.execute(
            'SELECT DISTINCT "ASSOCIATE ID" AS org_id FROM hospital_enrollments '
            "WHERE TRIM(COALESCE(\"ASSOCIATE ID\", '')) <> ''"
        ).df()["org_id"]
    )

    graph = build_ownership_digraph(edges)
    summary = describe_graph(graph)
    ultimate_pairs = resolve_ultimate_owners(graph, enrolled_org_ids)

    connection.register("ultimate_pairs", ultimate_pairs)
    connection.execute(PATHS_SQL)
    connection.unregister("ultimate_pairs")

    connection.execute(SUMMARY_SQL)
    return summary


def report_counts(connection: duckdb.DuckDBPyConnection) -> None:
    """Print the numbers a reviewer needs to sanity-check the resolution."""
    scalar = lambda sql: connection.execute(sql).fetchone()[0]  # noqa: E731

    print(f"Ownership edges: {scalar('SELECT COUNT(*) FROM ownership_edges')}")
    print(
        "  distinct owners: "
        f"{scalar('SELECT COUNT(DISTINCT owner_id) FROM ownership_edges')}"
    )
    print(
        "  distinct owned orgs: "
        f"{scalar('SELECT COUNT(DISTINCT org_id) FROM ownership_edges')}"
    )

    print(
        f"\nProvider org / ultimate owner pairs: "
        f"{scalar('SELECT COUNT(*) FROM ultimate_owner_by_org')}"
    )
    print(
        "  provider orgs covered: "
        f"{scalar('SELECT COUNT(DISTINCT org_id) FROM ultimate_owner_by_org')}"
    )
    print(
        "  distinct ultimate owners: "
        f"{scalar('SELECT COUNT(*) FROM ultimate_owner_summary')}"
    )
    joint_ventures = scalar(
        "SELECT COUNT(DISTINCT org_id) FROM ultimate_owner_by_org "
        "WHERE is_JV = 'Yes'"
    )
    print(f"  joint ventures (orgs with >1 ultimate owner): {joint_ventures}")
    print(
        "  max ownership depth: "
        f"{scalar('SELECT MAX(ownership_depth) FROM ultimate_owner_by_org')}"
    )

    print("\nTop 10 ultimate owners by provider organization count:")
    top = connection.execute(
        """
        SELECT ultimate_owner_name, n_provider_orgs, n_hospitals
        FROM ultimate_owner_summary
        WHERE is_self_owned = 'No'
        ORDER BY n_provider_orgs DESC, n_hospitals DESC
        LIMIT 10
        """
    ).df()
    print(top.to_string(index=False))


def main(argv: list[str]) -> int:
    allowners_file = argv[1] if len(argv) >= 2 else DEFAULT_ALLOWNERS_FILE

    if not DUCKDB_PATH.exists():
        print(
            f"{DUCKDB_PATH} not found. Run build_hierarchy.py first.",
            file=sys.stderr,
        )
        return 1

    owner_dim = load_owner_dimension(allowners_file)
    print(f"Organizational owners in the dimension: {len(owner_dim)}")

    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        # Registered rather than written as a table: it is an input to the
        # SQL below, not a published output.
        connection.register("owner_dim", owner_dim)
        graph_summary = build_tables(connection)
        connection.unregister("owner_dim")

        print("\nOwnership graph (igraph):")
        print(f"  vertices: {graph_summary['vertices']}")
        print(f"  edges: {graph_summary['edges']}")
        print(f"  weakly connected components: {graph_summary['components']}")
        print(f"  largest component: {graph_summary['largest_component']}")
        print(f"  terminal owners (out-degree 0): {graph_summary['terminal_owners']}")
        print(f"  acyclic (is_dag): {graph_summary['is_dag']}")
        if not graph_summary["is_dag"]:
            print(
                "  WARNING: the filtered ownership graph now contains a cycle. "
                "It was acyclic on the 2026.07.31 snapshot; investigate before "
                "trusting the depths below."
            )

        print()
        report_counts(connection)
    finally:
        connection.close()

    print(f"\nWrote 3 tables to {DUCKDB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
