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


def commit_site() -> str:
    """Stage and commit everything. Returns the commit message."""
    git("add", "--all", cwd=WORKTREE_DIR, quiet=True)

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
