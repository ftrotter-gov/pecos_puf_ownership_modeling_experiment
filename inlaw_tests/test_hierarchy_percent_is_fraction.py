"""Percent is a 0-1 fraction and the category percentages sum to 1.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.4.

The R script writes Percent as count / total, not a value out of 100. This
check guards against a future rewrite silently switching to percentage points.
"""

from inlaw import DBTable, InLaw


class TestHierarchyPercentIsFraction(InLaw):
    title = "Hierarchy Percent values are 0-1 fractions summing to 1"

    @staticmethod
    def run(engine, settings=None):
        heirarchy_table = DBTable(schema="main", table="heirarchy_table")

        range_sql = f'SELECT "Percent" AS percent_value FROM {heirarchy_table}'
        range_df = InLaw.sql_to_gx_df(sql=range_sql, engine=engine)
        range_result = range_df.expect_column_values_to_be_between(
            column="percent_value", min_value=0.0, max_value=1.0
        )
        if not range_result.success:
            return (
                "A Percent value falls outside 0-1; it may have been written as "
                "percentage points instead of a fraction."
            )

        sum_sql = f"""
            SELECT SUM("Percent") AS percent_total
            FROM {heirarchy_table}
            WHERE "Category" <> 'Hospitals, total'
        """
        sum_df = InLaw.sql_to_gx_df(sql=sum_sql, engine=engine)
        sum_result = sum_df.expect_column_values_to_be_between(
            column="percent_total", min_value=0.9999, max_value=1.0001
        )
        if not sum_result.success:
            return "The five category percentages do not sum to 1."

        return True
