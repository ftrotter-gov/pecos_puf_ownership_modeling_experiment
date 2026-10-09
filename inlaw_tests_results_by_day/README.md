# `inlaw_tests_results_by_day/`

Dated markdown reports from the InLaw validation suite, written by
[`../save_inlaw_results.py`](../save_inlaw_results.py).

```bash
python save_inlaw_results.py                # saves only if every check passes
python save_inlaw_results.py --force_save   # saves even when checks fail
```

One file per day, named `inlaw-results-YYYY-MM-DD.md`. Re-running on the same
day replaces that day's file, so each date holds the latest run.

## Why the default is "save only on success"

These reports are meant to be a record of **known-good** states — a date-stamped
answer to "when did this last fully pass, and with which baselines?" Saving
every run regardless would dilute that.

Use `--force_save` when you deliberately want to capture a failure: recording a
regression before investigating it, or snapshotting the state of a new data
vintage before the baselines are updated. Forced reports are clearly marked —
the Outcome line says the run did not pass, and a **Not passing** section lists
the offending checks with their full diagnostic messages.

Exit code is `0` only when every check passed, independent of whether a report
was written, so this is safe to use in CI.

## Reading a report

- The **Summary** line matches what `inlaw inlaw_tests` prints.
- Each check appears with its title, which embeds the current baseline and
  threshold for the rate-guard checks.
- Failures carry an indented message explaining what moved and where to look.

A shifting baseline in these titles over time is itself useful history: it
shows when a threshold was revised, which should always be a deliberate act.
See [`../inlaw_tests/README.md`](../inlaw_tests/README.md) for what the
baselines mean.
