"""Each single owner ROW's ownership percentage sits between 0 and 100.

Spec: AI_Instructions/PreviousImplementationSummary.md section 5.

Weaker than the per-enrollment sum check, and independent of it: this catches
a single malformed row (negative, or above 100) rather than an aggregation
problem. Rows with a blank or non-numeric percentage are ignored here.
"""

from inlaw import DBTable, InLaw


class TestOwnershipPercentageInRange(InLaw):
    title = (
        "Single-row check: PERCENTAGE OWNERSHIP on one owner row is between "
        "0 and 100 (this does NOT sum rows per enrollment)"
    )

    @staticmethod
    def run(engine, settings=None):
        hospital_allowners = DBTable(schema="main", table="hospital_allowners")

        sql = f"""
            SELECT TRY_CAST("PERCENTAGE OWNERSHIP" AS DOUBLE) AS ownership_percentage
            FROM {hospital_allowners}
            WHERE TRY_CAST("PERCENTAGE OWNERSHIP" AS DOUBLE) IS NOT NULL
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="ownership_percentage", min_value=0.0, max_value=100.0
        )

        if result.success:
            return True

        return (
            "At least one individual owner ROW has a PERCENTAGE OWNERSHIP that is "
            "negative or above 100. This is a per-row check: a single ownership "
            "stake on its own cannot exceed 100%. It is NOT the per-enrollment sum "
            "check (see test_direct_ownership_not_over_100.py for that), so this "
            "failure means the raw value in that one row is malformed."
        )
