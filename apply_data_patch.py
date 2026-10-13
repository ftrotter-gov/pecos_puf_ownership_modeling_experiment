"""Apply patched_data/owner_name_patch.yaml to the CMS All Owners CSV.

Spec: AI_Instructions/EntityResolutionProblem.md
Rules: patched_data/owner_name_patch.yaml

THIS IS THE SINGLE ENTRY POINT FOR DATA-CONTENT CORRECTIONS.

CMS publishes PECOS as-reported, with no entity resolution: one company
appears under several spellings and several enrollment IDs. That is a property
of the source data, not a pipeline bug, so it is corrected HERE -- before the
ETL -- rather than inside build_ownership_graph.py where the decisions would
be invisible and untestable.

    data/Hospital_All_Owners_...csv                      original, gitignored
        |  apply_data_patch.py + owner_name_patch.yaml
        v
    patched_data/Hospital_All_Owners_....patched.csv     generated, COMMITTED

Inputs live in data/ (gitignored, re-downloadable from CMS). Both the patch
rules and the patched output live in patched_data/ and are version
controlled, so the corrections and their effect are reviewable in a diff
without downloading anything.

GUARANTEES

  * The original file is opened read-only and never written.
  * Only the two columns named in the patch meta block are rewritten. Every
    other field, and every row, is passed through byte-for-byte -- the patch
    can rename and merge owners, but can never alter an ownership fact,
    drop a row, or change a percentage.
  * Row count out always equals row count in; --verify asserts it.
  * Encoding and line endings are preserved (cp1252 / CRLF), so the patched
    file is a drop-in replacement for the original.

Usage:
    python apply_data_patch.py              # write the patched CSV
    python apply_data_patch.py --report     # write it, then explain changes
    python apply_data_patch.py --verify     # check an existing patched file
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent

# Raw CMS downloads. Gitignored: large, and re-downloadable.
DATA_DIR = REPO_ROOT / "data"

# Patch rules AND their output. Both version controlled, so a reviewer can
# read the corrections and their effect without fetching the source data.
PATCHED_DATA_DIR = REPO_ROOT / "patched_data"
PATCH_PATH = PATCHED_DATA_DIR / "owner_name_patch.yaml"

# CMS ships these files Windows-1252 encoded with CRLF line endings. Matches
# SOURCE_ENCODING in build_hierarchy.py.
SOURCE_ENCODING = "cp1252"


class PatchError(Exception):
    """The patch cannot be applied as written."""


def load_patch(path: Path = PATCH_PATH) -> dict:
    """Read and lightly validate the rules file."""
    if not path.exists():
        raise PatchError(f"Patch file not found: {path}")

    patch = yaml.safe_load(path.read_text(encoding="utf-8"))

    for section in ("meta", "canonical_names", "identical_name_merges"):
        if section not in patch:
            raise PatchError(f"Patch file is missing the '{section}' section.")

    # Every rule must justify itself. This is enforced rather than merely
    # documented, so an unexplained merge cannot reach the data.
    for section in (
        "canonical_names",
        "identical_name_merges",
        "corporate_families",
        "passive_investors",
    ):
        for index, rule in enumerate(patch.get(section) or []):
            if not str(rule.get("reason", "")).strip():
                raise PatchError(
                    f"{section}[{index}] has no 'reason'. Every rule must "
                    f"state why it is correct -- see patched_data/README.md."
                )

    return patch


def build_lookups(patch: dict) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Flatten the rules into three lookup tables.

    Returns (name_to_canonical, id_to_canonical_id, id_to_canonical_name).

    Applied in order of increasing assertiveness: spelling variants first,
    then same-name ID merges, then the hand-curated corporate families. Later
    rules win, which matters when a family merge targets an ID that an
    identical-name rule also touched.
    """
    name_map: dict[str, str] = {}
    for rule in patch.get("canonical_names") or []:
        canonical = rule["canonical"]
        for variant in rule.get("variants") or []:
            name_map[variant.strip().upper()] = canonical

    id_map: dict[str, str] = {}
    id_name_map: dict[str, str] = {}

    for rule in patch.get("identical_name_merges") or []:
        keep = str(rule["keep"])
        for merged in rule.get("merge") or []:
            id_map[str(merged)] = keep
            if rule.get("name"):
                id_name_map[str(merged)] = rule["name"]
        # Pin the kept ID's name too, so every row for that ID agrees.
        if rule.get("name"):
            id_name_map.setdefault(keep, rule["name"])

    for rule in patch.get("corporate_families") or []:
        keep = str(rule["keep"])
        keep_name = rule.get("keep_name")
        for merged in rule.get("merge") or []:
            id_map[str(merged)] = keep
            if keep_name:
                id_name_map[str(merged)] = keep_name
        # The kept ID itself is renamed to the family's canonical name, so the
        # surviving record reads consistently. This OVERWRITES any name an
        # identical_name_merges rule set for the same ID -- families are the
        # more assertive, hand-reviewed rule and must win.
        if keep_name:
            id_name_map[keep] = keep_name

    # Collapse any chains (A -> B -> C becomes A -> C) so the result does not
    # depend on dictionary ordering.
    for source in list(id_map):
        seen = {source}
        target = id_map[source]
        while target in id_map and target not in seen:
            seen.add(target)
            target = id_map[target]
        id_map[source] = target

    return name_map, id_map, id_name_map


def patched_path(patch: dict) -> tuple[Path, Path]:
    """Resolve (source, destination) from the patch meta block.

    Source is read from data/; the patched copy is written to patched_data/
    alongside the rules that produced it.
    """
    meta = patch["meta"]
    source = DATA_DIR / meta["target_file"]
    suffix = meta.get("output_suffix", ".patched")
    destination = PATCHED_DATA_DIR / f"{source.stem}{suffix}{source.suffix}"
    return source, destination


def apply_patch(patch: dict, source: Path, destination: Path) -> dict:
    """Rewrite the CSV with corrections applied. Returns a change summary.

    Streams row by row rather than loading the frame, so memory stays flat and
    -- more importantly -- every untouched field is copied verbatim instead of
    being re-inferred by a parser.
    """
    meta = patch["meta"]
    id_column = meta["owner_id_column"]
    name_column = meta["owner_name_column"]
    name_map, id_map, id_name_map = build_lookups(patch)

    counts = Counter()
    renamed_examples: dict[str, str] = {}
    merged_ids: set[str] = set()

    with source.open("r", encoding=SOURCE_ENCODING, newline="") as source_file:
        reader = csv.DictReader(source_file)
        fieldnames = reader.fieldnames

        if fieldnames is None:
            raise PatchError(f"{source} has no header row.")
        for required in (id_column, name_column):
            if required not in fieldnames:
                raise PatchError(
                    f"{source} has no column named {required!r}. The patch "
                    f"meta block does not match this file."
                )

        destination.parent.mkdir(parents=True, exist_ok=True)

        # newline='' plus lineterminator preserves the CRLF endings CMS ships.
        with destination.open(
            "w", encoding=SOURCE_ENCODING, newline="", errors="replace"
        ) as destination_file:
            writer = csv.DictWriter(
                destination_file, fieldnames=fieldnames, lineterminator="\r\n"
            )
            writer.writeheader()

            for row in reader:
                counts["rows_in"] += 1

                original_id = (row.get(id_column) or "").strip()
                original_name = (row.get(name_column) or "").strip()

                # 1. Merge the owner ID, if a rule names it.
                new_id = id_map.get(original_id, original_id)
                if new_id != original_id:
                    row[id_column] = new_id
                    counts["owner_ids_merged"] += 1
                    merged_ids.add(original_id)

                # 2. Name follows the owner ID where a rule supplies one.
                #    Keyed on the POST-merge ID so the surviving record reads
                #    consistently: the kept ID's own rows are renamed too,
                #    otherwise one ID would still carry several names.
                new_name = id_name_map.get(new_id)
                if new_name is None:
                    new_name = id_name_map.get(original_id)
                if new_name is None:
                    new_name = name_map.get(original_name.upper(), original_name)

                if new_name != original_name:
                    row[name_column] = new_name
                    counts["owner_names_rewritten"] += 1
                    if len(renamed_examples) < 2000:
                        renamed_examples[original_name] = new_name

                writer.writerow(row)
                counts["rows_out"] += 1

    if counts["rows_in"] != counts["rows_out"]:
        raise PatchError(
            f"Row count changed: {counts['rows_in']} in, {counts['rows_out']} "
            f"out. The patch must never add or drop rows."
        )

    return {
        "counts": counts,
        "renamed_examples": renamed_examples,
        "merged_ids": merged_ids,
    }


def verify(patch: dict, source: Path, destination: Path) -> list[str]:
    """Check the patched file against the source and the rules.

    Returns a list of problems; empty means the file is consistent.
    """
    problems: list[str] = []

    if not destination.exists():
        return [f"{destination.name} does not exist. Run 'make patch' first."]

    meta = patch["meta"]
    id_column = meta["owner_id_column"]
    name_column = meta["owner_name_column"]
    _, id_map, _ = build_lookups(patch)

    def read_rows(path: Path):
        with path.open("r", encoding=SOURCE_ENCODING, newline="") as handle:
            yield from csv.DictReader(handle)

    source_rows = sum(1 for _ in read_rows(source))
    patched_rows = sum(1 for _ in read_rows(destination))
    if source_rows != patched_rows:
        problems.append(
            f"Row count differs: source {source_rows}, patched {patched_rows}."
        )

    # No ID that a rule merges away may survive in the output.
    surviving = set()
    names_per_id: dict[str, set[str]] = {}
    for row in read_rows(destination):
        owner_id = (row.get(id_column) or "").strip()
        if owner_id in id_map:
            surviving.add(owner_id)
        names_per_id.setdefault(owner_id, set()).add(
            (row.get(name_column) or "").strip()
        )

    if surviving:
        sample = ", ".join(sorted(surviving)[:5])
        problems.append(
            f"{len(surviving)} merged-away owner IDs still present: {sample}"
        )

    # After patching, one ID should carry exactly one name.
    inconsistent = {i: n for i, n in names_per_id.items() if len(n) > 1}
    if inconsistent:
        sample_id = sorted(inconsistent)[0]
        problems.append(
            f"{len(inconsistent)} owner IDs carry multiple names, e.g. "
            f"{sample_id}: {sorted(inconsistent[sample_id])[:3]}"
        )

    return problems


def print_report(patch: dict, result: dict, source: Path, destination: Path) -> None:
    """Explain what the patch changed, and why."""
    counts = result["counts"]

    print("\n" + "=" * 68)
    print("DATA PATCH REPORT")
    print("=" * 68)
    print(f"  source:  {source.name}")
    print(f"  output:  {destination.name}")
    print(f"  rows:    {counts['rows_in']:,} in / {counts['rows_out']:,} out")
    print()
    print("Rules applied:")
    print(f"  canonical_names ........ {len(patch.get('canonical_names') or [])}")
    print(
        f"  identical_name_merges .. {len(patch.get('identical_name_merges') or [])}"
    )
    print(
        f"  corporate_families ..... {len(patch.get('corporate_families') or [])}"
    )
    print(
        f"  passive_investors ...... {len(patch.get('passive_investors') or [])}"
        "  (flagged, not merged)"
    )
    print()
    print("Effect on the data:")
    print(f"  owner ID values merged ..... {counts['owner_ids_merged']:,} rows")
    print(f"  owner names rewritten ...... {counts['owner_names_rewritten']:,} rows")
    print(f"  distinct IDs merged away ... {len(result['merged_ids'])}")

    examples = result["renamed_examples"]
    if examples:
        print("\nSample renames:")
        for before, after in sorted(examples.items())[:12]:
            print(f"  {before!r}")
            print(f"    -> {after!r}")

    families = patch.get("corporate_families") or []
    if families:
        print("\nCorporate families merged:")
        for family in families:
            print(
                f"  {family['family']}: {len(family['merge'])} IDs -> "
                f"{family.get('keep_name', family['keep'])}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply the owner-name data patch to the CMS All Owners CSV."
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a detailed summary of what changed and why.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Check an existing patched file instead of regenerating it.",
    )
    arguments = parser.parse_args(argv)

    try:
        patch = load_patch()
        source, destination = patched_path(patch)

        if not source.exists():
            raise PatchError(
                f"Source file not found: {source}\n"
                f"The CMS CSVs are not committed; see data/README.md."
            )

        if arguments.verify:
            problems = verify(patch, source, destination)
            if problems:
                print("Patch verification FAILED:", file=sys.stderr)
                for problem in problems:
                    print(f"  - {problem}", file=sys.stderr)
                return 1
            print(f"Patch verified: {destination.name} matches the rules.")
            return 0

        result = apply_patch(patch, source, destination)

        if arguments.report:
            print_report(patch, result, source, destination)
        else:
            counts = result["counts"]
            print(
                f"Patched {counts['rows_in']:,} rows -> {destination.name} "
                f"({counts['owner_ids_merged']:,} owner IDs merged, "
                f"{counts['owner_names_rewritten']:,} names rewritten)"
            )

        problems = verify(patch, source, destination)
        if problems:
            print("\nWARNING: output did not verify:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1

        return 0

    except PatchError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
