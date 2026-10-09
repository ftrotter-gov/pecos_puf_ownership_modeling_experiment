"""The five category counts add up to the "Hospitals, total" row.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.4.

Every eligible hospital lands in exactly one category, so the five category
counts must reconcile with the total row and with hospital_flags.
"""

from inlaw import DBTable, InLaw


class TestHierarchyCountsSumToTotal(InLaw):
    title = "Hierarchy category counts sum to the Hospitals, total row"

    @staticmethod
    def run(engine, settings=None):
        heirarchy_table = DBTable(schema="main", table="heirarchy_table")
        hospital_flags = DBTable(schema="main", table="hospital_flags")

        sql = f"""
            SELECT
                (
                    SELECT COALESCE(SUM("Count"), 0)
                    FROM {heirarchy_table}
                    WHERE "Category" <> 'Hospitals, total'
                )
                - (
                    SELECT "Count"
                    FROM {heirarchy_table}
                    WHERE "Category" = 'Hospitals, total'
                ) AS total_delta,
                (
                    SELECT "Count"
                    FROM {heirarchy_table}
                    WHERE "Category" = 'Hospitals, total'
                )
                - (SELECT COUNT(*) FROM {hospital_flags}) AS flags_delta
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)

        total_result = gx_df.expect_column_values_to_be_between(
            column="total_delta", min_value=0, max_value=0
        )
        if not total_result.success:
            return (
                "The five category counts do not sum to the Hospitals, total "
                "row: a hospital was double-counted or dropped."
            )

        flags_result = gx_df.expect_column_values_to_be_between(
            column="flags_delta", min_value=0, max_value=0
        )
        if not flags_result.success:
            return (
                "The Hospitals, total row does not match the hospital_flags row "
                "count."
            )

        return True
