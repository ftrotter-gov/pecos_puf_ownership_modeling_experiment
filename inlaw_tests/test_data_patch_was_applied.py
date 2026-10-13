"""The data patch was applied: no merged-away owner ID survives in the DB.

Spec: patched_data/README.md, AI_Instructions/EntityResolutionProblem.md.

patched_data/owner_name_patch.yaml merges duplicate owner records onto a
single kept ID. If the ETL is ever pointed back at the RAW CSV -- by editing
DEFAULT_ALLOWNERS_FILE, or by passing the unpatched filename -- the pipeline
still runs and the report still builds, but every corrected duplicate
silently returns. The HCA family splits back into five "owners" and the
joint-venture count inflates by roughly 80 organizations.

That is the failure this check exists to catch: a regression that produces
plausible-looking output rather than an error.

It asserts that none of the merged-away IDs appear in the OWNER position of
ownership_edges. The patch rewrites them onto their kept ID, so a single
survivor there means the database was built from unpatched input.

Only the owner position is checked, deliberately. The patch rewrites the two
owner columns and nothing else, so a merged-away ID can still legitimately
appear as an OWNED organization: 22 of these IDs are themselves enrolled
hospitals, and 20 such rows exist on the current snapshot. Flagging those
would be a false alarm -- an earlier version of this check did exactly that.

The check reads the YAML directly rather than hard-coding IDs, so adding a
merge rule automatically extends the coverage. It is skipped with a clear
message if PyYAML or the patch file is unavailable, since InLaw loads each
check file standalone.
"""

from pathlib import Path

from inlaw import DBTable, InLaw

PATCH_PATH = (
    Path(__file__).resolve().parent.parent / "patched_data" / "owner_name_patch.yaml"
)


def merged_away_ids() -> list[str]:
    """Every owner ID the patch rewrites onto a different kept ID."""
    import yaml

    patch = yaml.safe_load(PATCH_PATH.read_text(encoding="utf-8"))

    merged: list[str] = []
    for section in ("identical_name_merges", "corporate_families"):
        for rule in patch.get(section) or []:
            merged.extend(str(value) for value in (rule.get("merge") or []))
    return merged


class TestDataPatchWasApplied(InLaw):
    title = "No owner ID merged away by the data patch survives in ownership_edges"

    @staticmethod
    def run(engine, settings=None):
        if not PATCH_PATH.exists():
            return f"Patch file not found at {PATCH_PATH}; cannot verify."

        try:
            merged = merged_away_ids()
        except ImportError:
            return (
                "PyYAML is not installed, so the patch rules cannot be read. "
                "Install requirements.txt."
            )

        if not merged:
            return "The patch defines no merges; expected at least one."

        ownership_edges = DBTable(schema="main", table="ownership_edges")
        id_list = ", ".join(f"'{owner_id}'" for owner_id in merged)

        sql = f"""
            SELECT COUNT(*) AS unpatched_id_count
            FROM {ownership_edges}
            WHERE owner_id IN ({id_list})
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="unpatched_id_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = unexpected_values[0] if unexpected_values else "unknown"

        return (
            f"{observed} rows reference owner IDs that the data patch merges "
            f"away, so the database was built from UNPATCHED data. Run "
            f"'make patch' then 'make data && make graph'. Check that "
            f"DEFAULT_ALLOWNERS_FILE in build_hierarchy.py still points at the "
            f".patched.csv file."
        )
