"""CCN lengths stay within the valid set, at a known malformed rate.

Spec: AI_Instructions/PreviousImplementationSummary.md sections 2.1 and 3.2.

Valid CCN lengths are 6, 10, and 13 characters. Anything else is malformed.

THIS PROBLEM IS EXPECTED IN THE DATA. On the 2026.07.31 snapshot, 1.05% of
eligible hospital CCNs (63 of 6,028) have an invalid length. A check asserting
zero would fail permanently and teach the team to ignore the suite, so this is
a REGRESSION GUARD: it fails only when the malformed rate climbs more than
1 percentage point above the documented baseline, i.e. above 2.05%.

Observed length distribution in hospital_flags:

    len  6   5,965   98.9549%   valid
    len  7      31    0.5143%   malformed - 6-char CCN plus a letter (140010A)
    len  8      28    0.4645%   malformed - 6-char CCN plus 2 digits (22007401)
    len  9       4    0.0664%   malformed - 6-char CCN plus 3 digits (330027001)

Note the snapshot contains no 10- or 13-character CCNs at all. They are
accepted as valid so that a future snapshot using those forms does not trip
this check.

The malformed values are not random: each appears to be a valid 6-character
CCN with a suffix appended. Whether to truncate them to 6, or reject them, is
the open decision tracked in section 7. The pipeline currently passes them
through untouched, which also means substr(CCN, 3, 1) still reads position 3
for the special-unit exclusion.

If this fails, compare the reported rate against BASELINE_RATE_PERCENT below.
If the new rate is genuinely the new normal, update the baseline deliberately
and say why in the commit message -- do not simply widen the tolerance.
"""

from inlaw import DBTable, InLaw

# A CCN is valid at these lengths; anything else is malformed.
VALID_CCN_LENGTHS = (6, 10, 13)

# Measured on the 2026.07.31 snapshot: 63 of 6,028 eligible CCNs are malformed.
BASELINE_RATE_PERCENT = 1.05

# Fail only if the rate rises more than this much above the baseline.
ALLOWED_INCREASE_PERCENTAGE_POINTS = 1.0

CEILING_RATE_PERCENT = BASELINE_RATE_PERCENT + ALLOWED_INCREASE_PERCENTAGE_POINTS


class TestCcnLengthIsValid(InLaw):
    title = (
        f"Malformed CCN length rate stays at or below "
        f"{CEILING_RATE_PERCENT:.2f}% (baseline {BASELINE_RATE_PERCENT:.2f}%, "
        f"valid lengths {'/'.join(str(n) for n in VALID_CCN_LENGTHS)})"
    )

    @staticmethod
    def run(engine, settings=None):
        hospital_flags = DBTable(schema="main", table="hospital_flags")
        valid_lengths = ", ".join(str(n) for n in VALID_CCN_LENGTHS)

        sql = f"""
            SELECT
                100.0
                * COUNT(*) FILTER (WHERE length(CCN) NOT IN ({valid_lengths}))
                / NULLIF(COUNT(*), 0) AS malformed_rate_percent
            FROM {hospital_flags}
        """

        gx_df = InLaw.sql_to_gx_df(sql=sql, engine=engine)
        result = gx_df.expect_column_values_to_be_between(
            column="malformed_rate_percent",
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
            f"Malformed CCN lengths rose to {observed}% of eligible hospitals, "
            f"above the {CEILING_RATE_PERCENT:.2f}% ceiling "
            f"(baseline {BASELINE_RATE_PERCENT:.2f}% + "
            f"{ALLOWED_INCREASE_PERCENTAGE_POINTS:.2f} point tolerance). "
            f"Valid lengths are {valid_lengths}; check whether CMS changed the "
            f"CCN format or the padding step in build_hierarchy.py regressed."
        )
