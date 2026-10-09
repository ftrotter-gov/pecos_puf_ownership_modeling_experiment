"""No special-unit CCN survives into the eligible hospital set.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.2.

Character 3 of the CCN encodes a special-unit type. Psychiatric (M, S),
Rehabilitation (R, T), and Swing Bed (U, W, Y, Z) units are excluded from the
hierarchy and captured in ccn_exclusions instead.
"""

from inlaw import DBTable, InLaw


class TestNoSpecialUnitCcnsRemain(InLaw):
    title = "No special-unit CCN remains in hospital_flags"

    @staticmethod
    def run(engine, settings=None):
        hospital_flags = DBTable(schema="main", table="hospital_flags")

        sql = f"""
            SELECT COUNT(*) AS special_unit_count
            FROM {hospital_flags}
            WHERE substr(CCN, 3, 1) IN ('M', 'S', 'R', 'T', 'U', 'W', 'Y', 'Z')
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="special_unit_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "A psychiatric, rehabilitation, or swing-bed unit leaked into the "
            "eligible hospital set; the section 3.2 exclusion did not apply."
        )
