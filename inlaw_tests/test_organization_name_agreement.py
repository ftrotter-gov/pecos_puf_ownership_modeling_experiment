"""ORGANIZATION NAME agrees between the enrollment and all-owners files.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.1, assertion 2.

Compared case-insensitively and whitespace-trimmed, skipping unmatched
left-join rows. The R script used stopifnot(); this reports instead of crashing.
"""

from inlaw import DBTable, InLaw


class TestOrganizationNameAgreement(InLaw):
    title = "ORGANIZATION NAME agrees between enrollment and all-owners files"

    @staticmethod
    def run(engine, settings=None):
        owners_enrollments = DBTable(schema="main", table="owners_enrollments")

        sql = f"""
            SELECT COUNT(*) AS mismatch_count
            FROM {owners_enrollments}
            WHERE organization_name_mismatch = 1
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="mismatch_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "ORGANIZATION NAME disagrees between the two source files on at least "
            "one row after trimming and case folding."
        )
