"""hospital_flags holds exactly one row per CCN, with no missing values.

Spec: AI_Instructions/PreviousImplementationSummary.md section 3.3.

The flag rollup groups by CCN and takes the maximum of each flag, so the result
must be unique on CCN. The spec also warns that R's formula-interface
aggregate() silently drops rows containing NA; this check guards the pandas
equivalent against quietly losing hospitals the same way.
"""

from inlaw import DBTable, InLaw


class TestHospitalFlagsOneRowPerCcn(InLaw):
    title = "hospital_flags has one row per CCN and no null CCNs"

    @staticmethod
    def run(engine, settings=None):
        hospital_flags = DBTable(schema="main", table="hospital_flags")

        sql = f"SELECT CCN FROM {hospital_flags}"
        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)

        unique_result = gx_df.expect_column_values_to_be_unique(column="CCN")
        if not unique_result.success:
            return "hospital_flags contains duplicate CCNs; the rollup did not collapse to one row per hospital."

        not_null_result = gx_df.expect_column_values_to_not_be_null(column="CCN")
        if not not_null_result.success:
            return "hospital_flags contains a null CCN."

        return True
