"""Owner-name duplication stays at its documented baseline.

Spec: AI_Instructions/EntityResolutionProblem.md.

THIS PROBLEM IS PARTLY FIXED AND PARTLY INHERENT. CMS identifies owners by
enrollment ID, and one real company holds several, so a corporate family can
be reported as multiple distinct "ultimate owners".

patched_data/owner_name_patch.yaml corrects the cases that are demonstrably
the same entity. Measured on the 2026.07.31 snapshot, against the PATCHED
input the pipeline now consumes by default:

    before the patch   4,610 owner IDs -> 4,451 normalized names   3.45%
    after the patch    4,523 owner IDs -> 4,420 normalized names   2.28%

The baseline below is the POST-PATCH rate, so the gain is locked in: if the
patch stops being applied, or a rule is dropped, the rate climbs back toward
3.45% and this check fails.

The residue is real. It is names that differ by corporate form ("TRIAD
HEALTHCARE CORPORATION" vs "TRIAD HEALTHCARE LLC"), which the patch
deliberately does NOT merge because Inc and LLC are distinct legal entities.
Merging them would assert a corporate fact not in evidence.

Note this measures string duplication only. Corporate-family splits with
unrelated names (HEALTHTRUST / HERCULES HOLDING II) are invisible here; those
are handled by the hand-curated corporate_families rules in the patch.

Like the other known-defect checks in this suite, this is a REGRESSION GUARD
rather than an assertion of correctness: it fails only if the duplicate rate
climbs more than 1 percentage point above baseline, which would mean CMS
changed how owner names are recorded or the dimension load regressed.

A FALLING rate is not necessarily good news either -- if entity resolution is
implemented later, this baseline must be deliberately re-measured, not
quietly widened.
"""

from inlaw import DBTable, InLaw

# Measured on 2026.07.31 POST-PATCH: 4,523 owner IDs -> 4,420 normalized names.
# Tightened from the pre-patch 3.45% so the correction cannot silently regress.
BASELINE_RATE_PERCENT = 2.28

ALLOWED_INCREASE_PERCENTAGE_POINTS = 1.0

CEILING_RATE_PERCENT = BASELINE_RATE_PERCENT + ALLOWED_INCREASE_PERCENTAGE_POINTS


class TestOwnerDuplicateRate(InLaw):
    title = (
        f"Exact-duplicate owner-name rate stays at or below "
        f"{CEILING_RATE_PERCENT:.2f}% (baseline {BASELINE_RATE_PERCENT:.2f}%)"
    )

    @staticmethod
    def run(engine, settings=None):
        ultimate_owner_summary = DBTable(
            schema="main", table="ultimate_owner_summary"
        )

        # Normalization mirrors the one in EntityResolutionProblem.md: strip
        # punctuation to spaces, drop common corporate suffixes, squeeze
        # whitespace. Deliberately conservative -- it merges only names that
        # are unambiguously the same string.
        normalized = r"""
            TRIM(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(UPPER(ultimate_owner_name), '[^A-Z0-9 ]', ' ', 'g'),
                    '\b(INC|INCORPORATED|LLC|LP|LLP|CORP|CORPORATION|CO|COMPANY|LTD|THE|PLLC|PC)\b',
                    '', 'g'),
                '\s+', ' ', 'g'))
        """

        sql = f"""
            SELECT
                100.0
                * (COUNT(DISTINCT ultimate_owner_id)
                   - COUNT(DISTINCT {normalized}))
                / NULLIF(COUNT(DISTINCT ultimate_owner_id), 0)
                AS duplicate_rate_percent
            FROM {ultimate_owner_summary}
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="duplicate_rate_percent",
            min_value=0.0,
            max_value=CEILING_RATE_PERCENT,
        )

        if result.success:
            return True

        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = f"{unexpected_values[0]:.2f}" if unexpected_values else "unknown"

        return (
            f"Exact-duplicate owner names rose to {observed}% of owner IDs, "
            f"above the {CEILING_RATE_PERCENT:.2f}% ceiling (baseline "
            f"{BASELINE_RATE_PERCENT:.2f}%). Owner counts in the report are "
            f"already fragmented; this says they got worse. See "
            f"AI_Instructions/EntityResolutionProblem.md."
        )
