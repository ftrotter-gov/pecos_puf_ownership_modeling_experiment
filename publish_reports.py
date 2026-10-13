"""Publish the built Evidence site to GitHub Pages.

Spec: AI_Instructions/UltimateOwnerReport.md.

Copies reports/build/ onto the `gh_reports_branch` branch and pushes it.
There is no CI: the site is built locally and pushed from here deliberately,
so what you tested is byte-for-byte what ships.

HOW IT WORKS

The branch is built in a git worktree at .gh_reports/ rather than switching
branches in place. Your working copy stays on whatever branch you are on, with
no risk of build output being committed to main.

THE BRANCH KEEPS NO HISTORY, DELIBERATELY.

Each publish creates a single ORPHAN commit and force-pushes it, so the branch
is always exactly one commit holding exactly the current site.

This matters because the build is ~86 MB, almost all of it the DuckDB
WebAssembly engine that Evidence ships to run queries in the browser. An
ordinary append-only history would add that much to the repository on every
publish -- roughly a gigabyte after a dozen deploys -- for artifacts nobody
will ever read back. The branch is a publishing target, not a record; the
source history on main is what is worth keeping.

The force-push is therefore expected and safe. Never commit source to this
branch: it is discarded on the next publish.

ONE-TIME SETUP, IN THE GITHUB WEB UI

    Settings -> Pages -> Build and deployment
      Source: Deploy from a branch
      Branch: gh_reports_branch   /  (root)

This cannot be done from the command line and only needs doing once.

Usage:
    python publish_reports.py              # build must already exist
    python publish_reports.py --dry-run    # stage everything, do not push
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BUILD_DIR = REPO_ROOT / "reports" / "build"
WORKTREE_DIR = REPO_ROOT / ".gh_reports"
BRANCH = "gh_reports_branch"
REMOTE = "origin"

# A .gitignore committed ONTO the published branch.
#
# The branch holds only the built site, but checking it out does not remove
# the untracked source tree sitting in the working directory -- reports/,
# node_modules/, data/, .venv/ and the rest all stay on disk. With no
# .gitignore on this branch, git stops ignoring them, so the branch LOOKS
# full of source even though it tracks 131 build files.
#
# Worse, `git add -A` on that checkout sweeps in reports/node_modules/ (732 MB,
# including a 105 MB libduckdb.dylib) and produces a commit that can never be
# pushed, because GitHub rejects files over 100 MB.
#
# This file makes the branch report itself as clean. It is the only
# hand-written file on the branch; everything else is build output.
BRANCH_GITIGNORE = """\
# This branch holds ONLY the built Evidence site. publish_reports.py rebuilds
# it as a single orphan commit on every publish, so anything committed here
# by hand is discarded on the next run. Work on main instead.
#
# These rules exist because checking out this branch leaves the untracked
# source tree on disk. Without them `git add -A` pulls in node_modules --
# 732 MB, including a 105 MB libduckdb.dylib that exceeds GitHub's file size
# limit -- and the push fails.

# Evidence project source and its dependencies
reports/
node_modules/

# Pipeline inputs.
#
# NOTE: data/ itself is NOT ignored. The built site keeps its parquet files in
# data/, and without them every query on the published site returns nothing.
# Only the raw CMS source formats are excluded, so a leftover data/*.csv from
# the source checkout cannot be published while data/**/*.parquet still is.
data/*.csv
patched_data/
*.duckdb

# Python
.venv/
__pycache__/
*.py[cod]
*.py
inlaw_tests/
inlaw_tests_results_by_day/

# Repository source, present only as checkout leftovers
AI_Instructions/
data_documentation/
previous_implementation/
.github/
Makefile
*.md
.env
example.env
LICENSE
COMMUNITY.md
repolinter.json

# Publish worktree
.gh_reports/

# OS
.DS_Store
"""


class PublishError(Exception):
    """A step failed in a way the operator needs to read and act on."""


def git(
    *arguments: str,
    cwd: Path = REPO_ROOT,
    check: bool = True,
    quiet: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a git command and capture its output.

    Output is captured rather than inherited so that routine chatter ("Preparing
    worktree", "Switched to a new branch") stays out of the way, and so failures
    can be reported with the exact stderr git produced. Set quiet=False on a
    command whose output is the point.

    The shell version relied on `set -e` to stop on the first failure. Here a
    non-zero exit raises PublishError carrying git's own stderr, which main()
    prints -- except where check=False marks a command whose failure is
    expected and handled by the caller.
    """
    completed = subprocess.run(
        ["git", *arguments],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )

    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise PublishError(f"git {' '.join(arguments)} failed:\n{detail}")

    if not quiet and completed.stdout:
        print(completed.stdout, end="")

    return completed


def git_output(*arguments: str, cwd: Path = REPO_ROOT) -> str:
    """Run a git command and return its stdout, stripped."""
    return git(*arguments, cwd=cwd, quiet=True).stdout.strip()


def check_build_exists() -> None:
    """Refuse to publish without a complete build to publish."""
    if not BUILD_DIR.is_dir():
        raise PublishError(
            f"{BUILD_DIR} does not exist.\n"
            "Run 'make site' (or 'cd reports && npm run build') first."
        )

    if not (BUILD_DIR / "index.html").is_file():
        raise PublishError(
            f"{BUILD_DIR / 'index.html'} is missing; the build looks incomplete."
        )


def cleanup() -> None:
    """Remove the scratch worktree and local branch.

    Both are scratch state. Leaving either behind makes the next run fail
    ("branch already exists" / "already registered"), so this runs before
    starting and again on the way out.

    Every step tolerates failure: this is called when things are already in an
    unknown state, including from the finally block of a failed run.
    """
    worktrees = git("worktree", "list", "--porcelain", check=False, quiet=True)
    if f"worktree {WORKTREE_DIR}" in worktrees.stdout:
        git("worktree", "remove", "--force", str(WORKTREE_DIR),
            check=False, quiet=True)

    shutil.rmtree(WORKTREE_DIR, ignore_errors=True)
    git("worktree", "prune", check=False, quiet=True)
    # Only ever deletes the local scratch branch; origin is untouched.
    git("branch", "-D", BRANCH, check=False, quiet=True)


def prepare_empty_worktree() -> None:
    """Create a worktree holding an orphan branch with no files.

    --orphan starts a branch with no parent commit and no history, so the
    branch is rebuilt from nothing every time. The branch currently holds a
    copy of main; this is what hollows it out.
    """
    print(f"==> Preparing an empty {BRANCH} worktree")
    git("worktree", "add", "--detach", str(WORKTREE_DIR), quiet=True)
    git("checkout", "--orphan", BRANCH, cwd=WORKTREE_DIR, quiet=True)

    # --orphan carries the index over from the detached checkout; reset drops
    # it so nothing from main is staged into the publish commit.
    git("reset", "--hard", cwd=WORKTREE_DIR, check=False, quiet=True)

    for path in WORKTREE_DIR.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def copy_site() -> None:
    """Copy the built site in, then add the file that makes Pages serve it."""
    print("==> Copying reports/build/")
    shutil.copytree(BUILD_DIR, WORKTREE_DIR, dirs_exist_ok=True)

    # CRITICAL. GitHub Pages runs Jekyll by default, and Jekyll refuses to
    # serve any directory whose name starts with an underscore. Evidence puts
    # its JavaScript bundles in _app/, so without this file the site loads its
    # HTML and then hangs forever with no styling and no data, reporting no
    # error anywhere a reader would look.
    print("==> Writing .nojekyll")
    (WORKTREE_DIR / ".nojekyll").touch()

    # Makes the branch report itself as clean when checked out, and stops
    # `git add -A` from sweeping in node_modules. See BRANCH_GITIGNORE.
    print("==> Writing .gitignore")
    (WORKTREE_DIR / ".gitignore").write_text(BRANCH_GITIGNORE, encoding="utf-8")


def verify_staged_tree() -> None:
    """Refuse to publish source files or anything GitHub will reject.

    The branch must contain the built site and nothing else. Two specific
    failures have happened and are checked for explicitly:

      * node_modules / reports/ sweeping in from the untracked source tree
      * a file over GitHub's 100 MB limit, which makes the push fail after
        the commit already exists
    """
    staged = git_output("diff", "--cached", "--name-only", cwd=WORKTREE_DIR)
    paths = [line for line in staged.splitlines() if line.strip()]

    # data/ is deliberately absent from this list: the built site stores its
    # parquet files there and they must be published.
    forbidden = [
        path
        for path in paths
        if path.startswith(("reports/", "patched_data/", "inlaw_tests/"))
        or "node_modules/" in path
        or path.endswith((".py", ".duckdb", ".csv"))
    ]
    if forbidden:
        raise PublishError(
            f"{len(forbidden)} source file(s) staged for the published branch, "
            f"e.g. {forbidden[:3]}. Only the built site belongs here -- check "
            f"BRANCH_GITIGNORE and that reports/build/ is what you think."
        )

    # The site is useless without its data. An over-broad ignore rule once
    # excluded data/**/*.parquet, producing a site that loaded and then showed
    # empty tables -- a failure with no error message anywhere.
    required = {
        "index.html": any(path == "index.html" for path in paths),
        ".nojekyll": any(path == ".nojekyll" for path in paths),
        "parquet data": any(path.endswith(".parquet") for path in paths),
        "data manifest": any(path.endswith("manifest.json") for path in paths),
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        raise PublishError(
            f"The staged site is missing: {', '.join(missing)}. Publishing it "
            f"would produce a site that loads but shows no data. Check "
            f"BRANCH_GITIGNORE is not excluding build output, and that "
            f"'make sources && make site' ran."
        )

    # GitHub hard-rejects blobs over 100 MB. Catch it before the push.
    limit_bytes = 100 * 1024 * 1024
    oversized = [
        (path, (WORKTREE_DIR / path).stat().st_size)
        for path in paths
        if (WORKTREE_DIR / path).is_file()
        and (WORKTREE_DIR / path).stat().st_size > limit_bytes
    ]
    if oversized:
        listing = ", ".join(
            f"{path} ({size / 1048576:.0f} MB)" for path, size in oversized
        )
        raise PublishError(
            f"File(s) over GitHub's 100 MB limit staged: {listing}. "
            f"The push would be rejected."
        )


def commit_site() -> str:
    """Stage and commit everything. Returns the commit message."""
    git("add", "--all", cwd=WORKTREE_DIR, quiet=True)
    verify_staged_tree()

    source_commit = git_output("rev-parse", "--short", "HEAD")
    source_branch = git_output("rev-parse", "--abbrev-ref", "HEAD")
    message = f"Publish reports from {source_branch}@{source_commit}"

    git("commit", "-q", "-m", message, cwd=WORKTREE_DIR, quiet=True)
    print(f"==> Committed: {message}")
    return message


def print_dry_run_summary() -> None:
    """Report what would have been pushed."""
    print()
    print("==> --dry-run: built and committed, NOT pushed. Summary:")

    summary = git_output("show", "--stat", "--oneline", "HEAD", cwd=WORKTREE_DIR)
    for line in summary.splitlines()[:5]:
        print(line)

    tracked = git_output("ls-files", cwd=WORKTREE_DIR).splitlines()
    has_nojekyll = ".nojekyll" in tracked

    print()
    print(f"    Tracked files: {len(tracked)}")
    print(f"    .nojekyll present: {'yes' if has_nojekyll else 'NO -- the site will not work'}")
    print()
    print(f"    Nothing was sent to {REMOTE}. The scratch worktree and local")
    print("    branch are being removed now; rerun without --dry-run to publish.")


def pages_url() -> str | None:
    """Derive the GitHub Pages URL from the origin remote.

    Handles both remote forms, with or without a trailing .git:

        git@github.com:owner/repo.git
        https://github.com/owner/repo

    Returns None rather than guessing if origin is not a GitHub remote, since
    the URL is a convenience message and must not fail an otherwise good push.
    """
    remote_url = git_output("config", "--get", "remote.origin.url")
    match = re.search(
        r"(?:git@github\.com:|https://github\.com/)([^/]+)/(.+?)(?:\.git)?$",
        remote_url,
    )
    if not match:
        return None

    owner, repository = match.groups()
    return f"https://{owner}.github.io/{repository}/"


def push() -> None:
    """Force-push the orphan commit to the publishing branch."""
    # Force, because each publish is a fresh orphan commit with no ancestry in
    # common with what is already on the branch. See the module docstring.
    print(f"==> Force-pushing to {REMOTE}/{BRANCH}")
    git("push", "--force", REMOTE, BRANCH, cwd=WORKTREE_DIR, quiet=True)

    url = pages_url()
    print()
    if url:
        print("Published. The site will be live shortly at:")
        print(f"    {url}")
    else:
        print(f"Published to {REMOTE}/{BRANCH}.")
    print()
    print("If this is the first publish, set Settings -> Pages -> Source to")
    print(f"'Deploy from a branch', branch '{BRANCH}', folder '/ (root)'.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish the built Evidence site to GitHub Pages."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the publish commit locally but do not push it.",
    )
    arguments = parser.parse_args(argv)

    try:
        check_build_exists()
    except PublishError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        cleanup()
        prepare_empty_worktree()
        copy_site()
        commit_site()

        if arguments.dry_run:
            print_dry_run_summary()
            return 0

        push()
        return 0
    except PublishError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        # Always runs, including after a failure, so a broken publish never
        # leaves a half-built worktree to confuse the next one.
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
