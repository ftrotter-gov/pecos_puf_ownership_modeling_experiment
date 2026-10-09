"""ASSOCIATE ID agrees between the enrollment and all-owners files.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.1, assertion 1.

The R script enforced this with stopifnot(), which crashes the pipeline. Here it
is a check, so a mismatch is reported rather than fatal. Comparison ignores
leading zeros (some monthly files add one) and unmatched left-join rows.
"""

from inlaw import DBTable, InLaw


class TestAssociateIdAgreement(InLaw):
    title = "ASSOCIATE ID agrees between enrollment and all-owners files"

    @staticmethod
    def run(engine, settings=None):
        owners_enrollments = DBTable(schema="main", table="owners_enrollments")

        sql = f"""
            SELECT COUNT(*) AS mismatch_count
            FROM {owners_enrollments}
            WHERE associate_id_mismatch = 1
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="mismatch_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "ASSOCIATE ID disagrees between the two source files on at least one "
            "row; the enrollment file value is treated as canonical."
        )
