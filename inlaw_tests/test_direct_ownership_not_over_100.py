"""Role-34 ownership shares do not sum above 100% for one enrollment.

Spec: AI_Instructions/PreviousImplementationSummary.md section 5.

This is the headline quality metric from the Stata error-checking script. Role
code 34 is *direct* ownership, so a hospital summing above 100% indicates
duplicated owner rows rather than genuine over-ownership.

NOTE: this check is EXPECTED TO FAIL on the raw 2026.07.31 snapshot. The Stata
analyst found the same thing and attributed it to multiple enrollment records
per hospital. Grouping by ENROLLMENT ID (rather than by hospital) narrows but
does not eliminate it. Treat a failure here as a finding to investigate, which
is exactly what the original script was built to surface.
"""

from inlaw import DBTable, InLaw

TOLERANCE = 0.0001


class TestDirectOwnershipNotOver100(InLaw):
    title = "Role 34 ownership shares do not sum above 100% per enrollment"

    @staticmethod
    def run(engine, settings=None):
        hospital_allowners = DBTable(schema="main", table="hospital_allowners")

        sql = f"""
            SELECT COUNT(*) AS over_100_count
            FROM (
                SELECT "ENROLLMENT ID",
                       SUM(TRY_CAST("PERCENTAGE OWNERSHIP" AS DOUBLE)) AS share_total
                FROM {hospital_allowners}
                WHERE "ROLE CODE - OWNER" = '34'
                GROUP BY "ENROLLMENT ID"
            )
            WHERE share_total > {100 + TOLERANCE}
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="over_100_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "At least one enrollment has role-34 ownership summing above 100%. "
            "Known issue on the current snapshot - see section 5; likely "
            "duplicated owner rows across enrollment records."
        )
