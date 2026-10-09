"""The three classification regexes still match their known cases.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.3.

The patterns are transcribed verbatim from hirearchy_R.R and deliberately
include misspellings seen in CMS free text (GOVERMENT, GOVENMENTAL,
GOVERNEMNT, DIVISON). This check pins that behavior so a well-meaning cleanup
cannot silently drop them.

It also demonstrates the non-SQL path: InLaw validates a pandas DataFrame
built in-process, ignoring the database engine entirely.
"""

import great_expectations as gx
import pandas as pd
from inlaw import GXValidatorAdapter, InLaw

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

# (text, pattern) pairs that must match. The misspellings are intentional.
MUST_MATCH = [
    ("A GENERAL PARTNERSHIP", PARTNERSHIP_TERMS),
    ("SMITH AND JONES LLP", PARTNERSHIP_TERMS),
    ("ACME LP", PARTNERSHIP_TERMS),
    ("COUNTY GOVERNMENT", GOVERNMENT_TERMS),
    ("COUNTY GOVERMENT", GOVERNMENT_TERMS),
    ("GOVENMENTAL ENTITY", GOVERNMENT_TERMS),
    ("GOVERNEMNT OWNED", GOVERNMENT_TERMS),
    ("POLITICAL SUBDIVISION", GOVERNMENT_TERMS),
    ("POLITICAL SUBDIVISON", GOVERNMENT_TERMS),
    ("INDIAN HEALTH SERVICE", GOVERNMENT_TERMS),
    ("CHAIRMAN OF THE BOARD", BOARD_TERMS),
    ("BOARD OF TRUSTEES", BOARD_TERMS),
    ("TRUSTEE", BOARD_TERMS),
    ("GOVERNING BODY MEMBER", BOARD_TERMS),
]

# Text that must NOT match, guarding against over-broad patterns.
MUST_NOT_MATCH = [
    ("LIMITED LIABILITY COMPANY", PARTNERSHIP_TERMS),
    ("FLAGSHIP MEDICAL CENTER", PARTNERSHIP_TERMS),
    ("PRIVATE EQUITY HOLDINGS", GOVERNMENT_TERMS),
    ("BOARDWALK SURGERY CENTER", BOARD_TERMS),
    # Documents a defect inherited verbatim from hirearchy_R.R: the alternative
    # \bL\.P\.\b can never fire. A trailing \b after an escaped '.' requires a
    # word character immediately after, so "ACME L.P." at end of string, or
    # followed by a space, does not match. The term is effectively dead code.
    # Pinned here deliberately - if a future rewrite "fixes" the pattern this
    # check fails and forces the change to be a conscious decision.
    ("ACME L.P.", PARTNERSHIP_TERMS),
    ("ACME L.P. HOLDINGS", PARTNERSHIP_TERMS),
]


class TestRegexTermsMatchKnownCases(InLaw):
    title = "Classification regexes match their documented cases, misspellings included"

    @staticmethod
    def run(engine, settings=None):
        rows = [
            {"label": text, "matched": bool(pd.Series([text]).str.contains(pattern, regex=True).iloc[0]), "expected": True}
            for text, pattern in MUST_MATCH
        ] + [
            {"label": text, "matched": bool(pd.Series([text]).str.contains(pattern, regex=True).iloc[0]), "expected": False}
            for text, pattern in MUST_NOT_MATCH
        ]

        frame = pd.DataFrame(rows)
        frame["is_correct"] = frame["matched"] == frame["expected"]

        # Validate an in-memory DataFrame: no database involved.
        context = gx.get_context(mode="ephemeral")
        batch = context.data_sources.pandas_default.read_dataframe(frame)
        gx_df = GXValidatorAdapter(batch)

        result = gx_df.expect_column_values_to_be_in_set(
            column="is_correct", value_set=[True]
        )

        if result.success:
            return True

        wrong = frame.loc[~frame["is_correct"], "label"].tolist()
        return f"Regex behavior changed for: {wrong}"
