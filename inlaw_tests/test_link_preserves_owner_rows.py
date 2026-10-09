"""The link step neither invents nor drops owner rows.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.1.

Two properties at once:
  * Reading the Windows-1252 source must not change row counts. The R script
    used iconv(sub = ""), which strips invalid bytes but never whole rows.
  * The enrollments-to-owners left join must not duplicate owner rows. Every
    owner row carries exactly one ENROLLMENT ID, so the linked table should
    have the same row count as the owners table.
"""

from inlaw import DBTable, InLaw


class TestLinkPreservesOwnerRows(InLaw):
    title = "Linked table row count matches the all-owners source row count"

    @staticmethod
    def run(engine, settings=None):
        owners_enrollments = DBTable(schema="main", table="owners_enrollments")
        hospital_allowners = DBTable(schema="main", table="hospital_allowners")

        sql = f"""
            SELECT
                (SELECT COUNT(*) FROM {owners_enrollments})
                - (SELECT COUNT(*) FROM {hospital_allowners}) AS row_count_delta
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="row_count_delta", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "Linked row count differs from the all-owners row count: the join "
            "duplicated or dropped rows, or the source read lost rows."
        )
