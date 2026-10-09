"""Run one InLaw check file, or a few, by path.

The `inlaw` CLI takes a *directory* and runs everything in it. This runner is
the companion for the one-class-per-file convention: it runs just the files you
name, which is what you want while iterating on a single check.

Usage:
    python run_inlaw_test.py inlaw_tests/test_ccn_length_is_valid.py
    python run_inlaw_test.py inlaw_tests/test_a.py inlaw_tests/test_b.py

Exit code is 0 only if every named check passed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import sqlalchemy
from dotenv import load_dotenv
from dynaconf import Dynaconf
from inlaw import InLaw, InlawError

REPO_ROOT = Path(__file__).resolve().parent


def read_only_args(connection_url: str) -> dict:
    """Open DuckDB read-only so concurrent check runs do not fight for the lock.

    DuckDB allows a single writer. The checks only read, so requesting
    read-only access lets several run at once and avoids clashing with a
    build_hierarchy.py run holding the write lock.
    """
    if connection_url.startswith("duckdb:") and ":memory:" not in connection_url:
        return {"read_only": True}
    return {}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    load_dotenv(REPO_ROOT / ".env")

    connection_url = os.environ.get("INLAW_URL")
    if not connection_url:
        print(
            "INLAW_URL is not set. Copy the template first:\n"
            "    cp example.env .env",
            file=sys.stderr,
        )
        return 2

    missing = [path for path in argv[1:] if not Path(path).exists()]
    if missing:
        print(f"No such check file(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    engine = sqlalchemy.create_engine(connection_url, connect_args=read_only_args(connection_url))
    settings = Dynaconf(environments=False, load_dotenv=True)

    try:
        results = InLaw.run_all(
            engine=engine, inlaw_files=argv[1:], settings=settings
        )
    except InlawError:
        # run_all already printed the per-check failure detail.
        return 1

    return 0 if results["failed"] == 0 and results["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
