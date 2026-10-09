"""final.category only ever takes one of the five documented values.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.3.

The rule ladder is first-match-wins over rules 1-4 with an explicit
"Not categorized" fallback, so no other value should ever appear.
"""

from inlaw import DBTable, InLaw

KNOWN_CATEGORIES = [
    "Has owners",
    "Partnerships",
    "Government",
    "Non-profit",
    "Not categorized",
]


class TestFinalCategoryInKnownSet(InLaw):
    title = "final.category only contains the five known categories"

    @staticmethod
    def run(engine, settings=None):
        hospital_flags = DBTable(schema="main", table="hospital_flags")

        sql = f"""
            SELECT DISTINCT "final.category" AS final_category
            FROM {hospital_flags}
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_in_set(
            column="final_category", value_set=KNOWN_CATEGORIES
        )

        if result.success:
            return True

        return (
            f"hospital_flags contains a category outside the known set "
            f"{KNOWN_CATEGORIES}."
        )
