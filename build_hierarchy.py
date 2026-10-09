"""Build the hospital ownership hierarchy table.

Python/pandas reimplementation of previous_implementation/hirearchy_R.R.
See AI_Instructions/PreviousImplementationSummary.md for the full spec.

Reads the two CMS public-use CSVs from data/, writes every pipeline stage to
a DuckDB database so the InLaw checks in inlaw_tests/ can validate them.

Usage:
    python build_hierarchy.py [enrollment_file] [allowners_file]
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import duckdb
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
DUCKDB_PATH = DATA_DIR / "pecos.duckdb"

DEFAULT_ENROLLMENT_FILE = "Hospital_Enrollments_2026.07.31.csv"
DEFAULT_ALLOWNERS_FILE = "Hospital_All_Owners_2026.07.31_update.csv"

# CMS ships these files Windows-1252 encoded, not UTF-8.
SOURCE_ENCODING = "cp1252"

ENROLLMENT_COLUMNS = [
    "ENROLLMENT ID",
    "ASSOCIATE ID",
    "ORGANIZATION NAME",
    "CCN",
    "ORGANIZATION TYPE STRUCTURE",
    "ORGANIZATION OTHER TYPE TEXT",
    "PROPRIETARY NONPROFIT",
]

ALLOWNERS_COLUMNS = [
    "ENROLLMENT ID",
    "ASSOCIATE ID",
    "ORGANIZATION NAME",
    "ASSOCIATE ID - OWNER",
    "TYPE - OWNER",
    "ROLE CODE - OWNER",
    "TITLE - OWNER",
    "PERCENTAGE OWNERSHIP",
]

# Special-unit types encoded in character 3 of the CCN.
SPECIAL_UNIT_BY_CCN_CHAR3 = {
    "M": "Psychiatric",
    "S": "Psychiatric",
    "R": "Rehabilitation",
    "T": "Rehabilitation",
    "U": "Swing Bed",
    "W": "Swing Bed",
    "Y": "Swing Bed",
    "Z": "Swing Bed",
}

# Transcribed verbatim from hirearchy_R.R. The misspellings (GOVERMENT,
# GOVENMENTAL, GOVERNEMNT, DIVISON) are deliberate: they occur in CMS
# free-text. Do not "correct" them.
PARTNERSHIP_TERMS = (
    r"\b(PARTNERSHIP|LIMITED\s+PARTNER|GENERAL\s+PARTNER|LP|LLP)\b|\bL\.P\.\b"
)

GOVERNMENT_TERMS = (
    r"\b(FEDERAL|COUNTY|CITY|MUNICIPAL|MUNICIPALITY|TOWNSHIP|PARISH|GOVERNMENT|"
    r"GOVERNMENTAL|GOVT|GOVERMENT|GOVERMENTAL|GOVENMENTAL|GOVERNEMNT|PUBLIC|STATE|"
    r"DISTRICT|AUTHORITY|TRIBAL|TRIBE|IHS|INDIAN\s+HEALTH\s+SERVICE|COMMONWEALTH|"
    r"INSTRUMENTALITY|DEPARTMENT\s+OF\s+DEFENSE)\b|POLITICAL\s*SUB[ -]?"
    r"(DIVISION|DIV|DIVISON)|POLITICALSUB"
)

BOARD_TERMS = r"\bBOARD\b|\bTRUSTEES?\b|\bBOD\b|\bBOT\b|\bGOVERNING\s+(BOARD|BODY)\b"

CATEGORY_ORDER = [
    "Has owners",
    "Partnerships",
    "Government",
    "Non-profit",
    "Not categorized",
]


def matches(series: pd.Series, pattern: str) -> pd.Series:
    """Regex search, suppressing pandas' match-group warning.

    The patterns are transcribed verbatim from the R script and use capturing
    groups. pandas warns about that because str.contains ignores the groups,
    which is exactly the behavior wanted here. Rewriting them as non-capturing
    would silence the warning but make the transcription less obviously faithful
    to the original, so the warning is suppressed instead.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return series.str.contains(pattern, regex=True, na=False)


def normalize_text(series: pd.Series) -> pd.Series:
    """Uppercase and trim, mapping missing values to the empty string."""
    return series.fillna("").astype(str).str.strip().str.upper()


def strip_leading_zeros(series: pd.Series) -> pd.Series:
    """Drop leading zeros for comparison only; source values are preserved."""
    return series.fillna("").astype(str).str.strip().str.replace(
        r"^0+", "", regex=True
    )


def load_source_files(
    enrollment_file: str, allowners_file: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read both CSVs as all-string data, preserving significant leading zeros."""
    read_options = {
        "dtype": str,
        "encoding": SOURCE_ENCODING,
        "keep_default_na": False,
        "na_values": [],
    }

    hospital_enrollments = pd.read_csv(
        DATA_DIR / enrollment_file, usecols=ENROLLMENT_COLUMNS, **read_options
    )
    hospital_allowners = pd.read_csv(
        DATA_DIR / allowners_file, usecols=ALLOWNERS_COLUMNS, **read_options
    )

    return hospital_enrollments, hospital_allowners


def link_files(
    hospital_enrollments: pd.DataFrame, hospital_allowners: pd.DataFrame
) -> pd.DataFrame:
    """Left join enrollments to owners on ENROLLMENT ID.

    Enrollments is the left side, so hospitals with no owner rows survive.
    """
    owners_enrollments = hospital_enrollments.merge(
        hospital_allowners,
        on="ENROLLMENT ID",
        how="left",
        suffixes=("", " - ALLOWNERS"),
    )

    # The R script asserts these agree across both files. Here they are
    # recorded as columns so the InLaw checks can report on them instead of
    # crashing the pipeline.
    associate_id_enrollment = strip_leading_zeros(owners_enrollments["ASSOCIATE ID"])
    associate_id_allowners = strip_leading_zeros(
        owners_enrollments["ASSOCIATE ID - ALLOWNERS"]
    )
    matched = owners_enrollments["ASSOCIATE ID - ALLOWNERS"].fillna("") != ""

    owners_enrollments["associate_id_mismatch"] = (
        (associate_id_enrollment != associate_id_allowners) & matched
    ).astype(int)

    owners_enrollments["organization_name_mismatch"] = (
        (
            normalize_text(owners_enrollments["ORGANIZATION NAME"])
            != normalize_text(owners_enrollments["ORGANIZATION NAME - ALLOWNERS"])
        )
        & matched
    ).astype(int)

    return owners_enrollments


def prepare_ccns(owners_enrollments: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize CCNs and split off the special-unit rows.

    Returns (eligible hospital rows, deduplicated exclusions).
    """
    ccn = owners_enrollments["CCN"].fillna("").astype(str).str.strip()

    # Pad 5-character CCNs to 6. Note the source also contains CCNs longer
    # than 6 characters, which the original R script passes through untouched.
    owners_enrollments["CCN"] = ccn.where(ccn.str.len() != 5, "0" + ccn)

    owners_enrollments["CCN.position.3"] = owners_enrollments["CCN"].str[2:3]
    owners_enrollments["special.unit"] = (
        owners_enrollments["CCN.position.3"].map(SPECIAL_UNIT_BY_CCN_CHAR3).fillna("")
    )

    ccn_exclusions = owners_enrollments.loc[
        owners_enrollments["special.unit"] != "",
        ["CCN", "CCN.position.3", "special.unit", "ORGANIZATION NAME"],
    ].drop_duplicates()

    hospital_data = owners_enrollments[
        (owners_enrollments["CCN"] != "") & (owners_enrollments["special.unit"] == "")
    ].copy()

    return hospital_data, ccn_exclusions


def apply_rules(hospital_data: pd.DataFrame) -> pd.DataFrame:
    """Flag each row, roll up to one row per CCN, and categorize."""
    structure = normalize_text(hospital_data["ORGANIZATION TYPE STRUCTURE"])
    other_text = normalize_text(hospital_data["ORGANIZATION OTHER TYPE TEXT"])
    nonprofit = normalize_text(hospital_data["PROPRIETARY NONPROFIT"])
    owner_type = normalize_text(hospital_data["TYPE - OWNER"])
    owner_role = normalize_text(hospital_data["ROLE CODE - OWNER"])
    owner_title = normalize_text(hospital_data["TITLE - OWNER"])

    is_other = structure == "OTHER"

    hospital_data["rule1.has.owners"] = (owner_role == "34").astype(int)

    hospital_data["rule2.partnership"] = (
        (structure == "PARTNERSHIP")
        | (is_other & matches(other_text, PARTNERSHIP_TERMS))
    ).astype(int)

    hospital_data["rule3.government"] = (
        (structure == "GOVERNMENT")
        | (is_other & matches(other_text, GOVERNMENT_TERMS))
    ).astype(int)

    hospital_data["nonprofit.N"] = (nonprofit == "N").astype(int)

    hospital_data["board.title"] = (
        (owner_type == "I") & matches(owner_title, BOARD_TERMS)
    ).astype(int)

    flag_columns = [
        "rule1.has.owners",
        "rule2.partnership",
        "rule3.government",
        "nonprofit.N",
        "board.title",
    ]

    # A hospital carries a flag if any of its rows does.
    hospital_flags = hospital_data.groupby("CCN", as_index=False)[flag_columns].max()

    hospital_names = hospital_data.groupby("CCN", as_index=False)[
        "ORGANIZATION NAME"
    ].agg(lambda names: " | ".join(sorted(set(names))))

    hospital_flags = hospital_names.merge(hospital_flags, on="CCN", how="left")

    # First match wins, in rule order: assign in reverse so earlier rules win.
    hospital_flags["final.category"] = "Not categorized"
    hospital_flags.loc[
        (hospital_flags["nonprofit.N"] == 1) & (hospital_flags["board.title"] == 1),
        "final.category",
    ] = "Non-profit"
    hospital_flags.loc[
        hospital_flags["rule3.government"] == 1, "final.category"
    ] = "Government"
    hospital_flags.loc[
        hospital_flags["rule2.partnership"] == 1, "final.category"
    ] = "Partnerships"
    hospital_flags.loc[
        hospital_flags["rule1.has.owners"] == 1, "final.category"
    ] = "Has owners"

    return hospital_flags


def build_hierarchy_table(hospital_flags: pd.DataFrame) -> pd.DataFrame:
    """Count hospitals per category, preserving zero-count categories."""
    total = len(hospital_flags)
    counts = (
        pd.Categorical(hospital_flags["final.category"], categories=CATEGORY_ORDER)
        .value_counts()
        .reindex(CATEGORY_ORDER)
    )

    return pd.DataFrame(
        {
            "Category": ["Hospitals, total"] + CATEGORY_ORDER,
            "Count": [total] + counts.tolist(),
            # A 0-1 fraction, matching the R script.
            "Percent": [1.0] + [count / total for count in counts],
        }
    )


def write_to_duckdb(tables: dict[str, pd.DataFrame]) -> None:
    """Persist each pipeline stage as a DuckDB table."""
    DATA_DIR.mkdir(exist_ok=True)
    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        for table_name, frame in tables.items():
            connection.register("frame_to_write", frame)
            connection.execute(
                f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM frame_to_write"
            )
            connection.unregister("frame_to_write")
    finally:
        connection.close()


def main(argv: list[str]) -> int:
    enrollment_file = argv[1] if len(argv) >= 2 else DEFAULT_ENROLLMENT_FILE
    allowners_file = argv[2] if len(argv) >= 3 else DEFAULT_ALLOWNERS_FILE

    hospital_enrollments, hospital_allowners = load_source_files(
        enrollment_file, allowners_file
    )
    print(f"Enrollment rows: {len(hospital_enrollments)}")
    print(f"All owner rows: {len(hospital_allowners)}")

    owners_enrollments = link_files(hospital_enrollments, hospital_allowners)
    print(f"Linked rows: {len(owners_enrollments)}")
    print(f"Enrollment file: {enrollment_file}")
    print(f"All owners file: {allowners_file}")

    hospital_data, ccn_exclusions = prepare_ccns(owners_enrollments)
    print(f"Source CCNs: {owners_enrollments['CCN'].nunique()}")
    print(f"Excluded CCNs: {ccn_exclusions['CCN'].nunique()}")
    print(f"Eligible hospital CCNs: {hospital_data['CCN'].nunique()}")

    hospital_flags = apply_rules(hospital_data)
    heirarchy_table = build_hierarchy_table(hospital_flags)

    print()
    print(heirarchy_table.to_string(index=False))

    write_to_duckdb(
        {
            "hospital_enrollments": hospital_enrollments,
            "hospital_allowners": hospital_allowners,
            "owners_enrollments": owners_enrollments,
            "ccn_exclusions": ccn_exclusions,
            "hospital_flags": hospital_flags,
            "heirarchy_table": heirarchy_table,
        }
    )
    print(f"\nWrote 6 tables to {DUCKDB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
