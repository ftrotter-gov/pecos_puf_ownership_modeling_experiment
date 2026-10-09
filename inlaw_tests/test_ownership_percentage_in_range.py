"""Any individual ownership percentage sits between 0 and 100.

Spec: AI_Instructions/PreviousImplementationSummary.md section 5.

Weaker than the per-enrollment sum check, and independent of it: this catches
a single malformed row (negative, or above 100) rather than an aggregation
problem. Rows with a blank or non-numeric percentage are ignored here.
"""

from inlaw import DBTable, InLaw


class TestOwnershipPercentageInRange(InLaw):
    title = "Each PERCENTAGE OWNERSHIP value is between 0 and 100"

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
            "At least one PERCENTAGE OWNERSHIP value is negative or above 100, "
            "which is impossible for a single ownership stake."
        )
