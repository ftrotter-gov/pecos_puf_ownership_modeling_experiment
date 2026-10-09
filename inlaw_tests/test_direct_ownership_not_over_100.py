"""Role-34 over-ownership stays near its known baseline rate.

Spec: AI_Instructions/PreviousImplementationSummary.md section 5.

Role code 34 is *direct* ownership, so the shares for one enrollment should
never sum above 100%. The Stata error-checking script used this as its headline
quality metric and attributed the excess to duplicated owner rows across the
multiple enrollment records a hospital accumulates over time.

THIS PROBLEM IS EXPECTED IN THE DATA. On the 2026.07.31 snapshot it occurs in
2.18% of enrollments that have any role-34 rows (121 of 5,547), with sums
reaching 300%. A check asserting zero would fail permanently and teach the team
to ignore it.

So this check is a REGRESSION GUARD, not a purity assertion. It fails only when
the rate climbs more than 1 percentage point above the documented baseline,
i.e. above 3.18%. That tolerates normal month-to-month drift while catching a
real deterioration in CMS data quality, or a pipeline change that starts
double-counting owners.

If this fails, compare the reported rate against BASELINE_RATE_PERCENT below.
If the new rate is genuinely the new normal, update the baseline deliberately
and say why in the commit message -- do not simply widen the tolerance.
"""

from inlaw import DBTable, InLaw

# Floating point guard, so 100.00000001 does not count as over-ownership.
TOLERANCE = 0.0001

# Measured on the 2026.07.31 snapshot: 121 of 5,547 enrollments carrying any
# role-34 row summed above 100%.
BASELINE_RATE_PERCENT = 2.18

# Fail only if the rate rises more than this much above the baseline.
ALLOWED_INCREASE_PERCENTAGE_POINTS = 1.0

CEILING_RATE_PERCENT = BASELINE_RATE_PERCENT + ALLOWED_INCREASE_PERCENTAGE_POINTS


class TestDirectOwnershipNotOver100(InLaw):
    title = (
        f"Role 34 over-ownership rate stays at or below "
        f"{CEILING_RATE_PERCENT:.2f}% (baseline {BASELINE_RATE_PERCENT:.2f}%)"
    )

    @staticmethod
    def run(engine, settings=None):
        hospital_allowners = DBTable(schema="main", table="hospital_allowners")

        sql = f"""
            WITH enrollment_totals AS (
                SELECT "ENROLLMENT ID" AS enrollment_id,
                       SUM(TRY_CAST("PERCENTAGE OWNERSHIP" AS DOUBLE)) AS share_total
                FROM {hospital_allowners}
                WHERE "ROLE CODE - OWNER" = '34'
                GROUP BY "ENROLLMENT ID"
            )
            SELECT
                100.0
                * COUNT(*) FILTER (WHERE share_total > {100 + TOLERANCE})
                / NULLIF(COUNT(*), 0) AS over_100_rate_percent
            FROM enrollment_totals
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="over_100_rate_percent",
            min_value=0.0,
            max_value=CEILING_RATE_PERCENT,
        )

        if result.success:
            return True

        # The adapter reports the offending value in partial_unexpected_list;
        # this expectation validates a single-row result, so take the first.
        unexpected_values = result.result.get("partial_unexpected_list") or []
        observed = f"{unexpected_values[0]:.2f}" if unexpected_values else "unknown"

        return (
            f"Role-34 over-ownership is {observed}% of enrollments, above the "
            f"{CEILING_RATE_PERCENT:.2f}% ceiling "
            f"(baseline {BASELINE_RATE_PERCENT:.2f}% + "
            f"{ALLOWED_INCREASE_PERCENTAGE_POINTS:.2f} point tolerance). "
            f"Either CMS data quality degraded or the pipeline is "
            f"double-counting owner rows."
        )
