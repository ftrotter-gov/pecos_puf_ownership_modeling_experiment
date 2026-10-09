"""Every eligible hospital CCN is exactly six characters.

Spec: AI_Instructions/PreviousImplementationSummary.md sections 2.1 and 3.2.

A CCN is a six-character facility identifier. The pipeline left-pads
five-character values, but the source also contains CCNs *longer* than six
characters, which the original R script passed through untouched. This check
exists to keep that visible: section 7 lists it as an open decision.
"""

from inlaw import DBTable, InLaw


class TestCcnIsSixCharacters(InLaw):
    title = "Every CCN in hospital_flags is exactly 6 characters"

    @staticmethod
    def run(engine, settings=None):
        hospital_flags = DBTable(schema="main", table="hospital_flags")

        sql = f"""
            SELECT COUNT(*) AS wrong_length_count
            FROM {hospital_flags}
            WHERE length(CCN) <> 6
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="wrong_length_count", min_value=0, max_value=0
        )

        if result.success:
            return True

        return (
            "Found CCNs that are not 6 characters long. Over-long CCNs are a "
            "known unresolved case inherited from the R script - see section 7."
        )
