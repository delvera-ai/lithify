"""Disposable git worktrees for probes.

Worktrees live OUTSIDE the repository (default ~/.cache/lithify/work/<repo-hash>/).
Claude Code reads every CLAUDE.md from the working directory up to the filesystem
root, so a worktree nested inside the repo would inherit the parent's harness and
contaminate the behavioral contrast between candidates.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from .harness import RENDERED_PATHS

GIT_ID = ["-c", "user.name=lithify", "-c", "user.email=lithify@localhost", "-c", "commit.gpgsign=false"]


class GitError(RuntimeError):
    pass


def git(cwd: Path, *args: str, check: bool = True, input: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input,
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed in {cwd}: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def repo_root(start: Path) -> Path:
    try:
        return Path(git(start, "rev-parse", "--show-toplevel").strip())
    except GitError as e:
        raise GitError(f"{start} is not inside a git repository (lithify needs git for worktrees)") from e


def work_base(root: Path) -> Path:
    env = os.environ.get("LITHIFY_WORK_DIR")
    base = Path(env) if env else Path.home() / ".cache" / "lithify" / "work"
    h = hashlib.sha1(str(root.resolve()).encode()).hexdigest()[:12]
    return base / f"{root.name}-{h}"


# Build artefacts that should never be part of a deliverable, even when a repo tracks them.
JUNK_GLOBS = (
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/node_modules/**",
    "**/.DS_Store",
)


def _exclude_args() -> list[str]:
    return [f":(exclude){p}" for p in RENDERED_PATHS] + [f":(exclude,glob){g}" for g in JUNK_GLOBS]


def dirty_patch(root: Path) -> str:
    """Tracked, uncommitted changes in the main tree (excluding lithify-managed paths)."""
    return git(root, "diff", "HEAD", "--binary", "--", ".", *_exclude_args())


def untracked(root: Path) -> list[str]:
    out = git(root, "ls-files", "--others", "--exclude-standard", "--", ".", *_exclude_args())
    return [ln for ln in out.splitlines() if ln.strip()]


def create(root: Path, name: str, base_patch: str = "") -> Path:
    wt = work_base(root) / name
    if wt.exists():
        remove(root, wt)
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(root, "worktree", "add", "--detach", str(wt), "HEAD")
    if base_patch.strip():
        git(wt, "apply", "--whitespace=nowarn", "-", input=base_patch)
    return wt


def seal_base(wt: Path) -> None:
    """Commit everything currently in the worktree so the deliverable diff is the agent's work only."""
    git(wt, "add", "-A")
    git(wt, *GIT_ID, "commit", "-q", "--allow-empty", "--no-verify", "-m", "lithify: probe base")


def deliverable(wt: Path) -> str:
    """Everything the agent changed since seal_base(), excluding rendered harness paths."""
    git(wt, "add", "-A", "--", ".", *_exclude_args())
    return git(wt, "diff", "--cached", "--binary", "HEAD", "--", ".", *_exclude_args())


def changed_files(wt: Path) -> list[tuple[str, str]]:
    """(status, path) for staged changes vs HEAD, after deliverable()."""
    out = git(wt, "diff", "--cached", "--name-status", "HEAD", "--", ".", *_exclude_args())
    rows = []
    for ln in out.splitlines():
        parts = ln.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0][:1], parts[-1]))
    return rows


_IGNORABLE_REMOVAL = ("import ", "from ", "#", "//", "use ", "require(", "const ", "package ")


def weakened_tests(wt: Path, paths: list[str]) -> list[str]:
    """Pre-existing test files where the agent removed or rewrote lines.

    Appending new tests or extending an import line is normal; deleting or changing existing
    assertions is how an agent makes its own oracle pass. Removed import/comment/blank lines
    are ignored so `from x import a` -> `from x import a, b` does not count.
    """
    out = []
    for p in paths:
        d = git(wt, "diff", "--cached", "-U0", "HEAD", "--", p, check=False)
        removed = [ln[1:].strip() for ln in d.splitlines() if ln.startswith("-") and not ln.startswith("---")]
        meaningful = [r for r in removed if r and not r.startswith(_IGNORABLE_REMOVAL)]
        if meaningful:
            out.append(f"{p} ({len(meaningful)} existing line(s) removed or changed)")
    return out


def apply_patch(root: Path, patch: str) -> tuple[bool, str]:
    if not patch.strip():
        return True, "empty patch"
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=root,
        input=patch,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, (proc.stderr or proc.stdout).strip()


def remove(root: Path, wt: Path) -> None:
    git(root, "worktree", "remove", "--force", str(wt), check=False)
    if wt.exists():
        shutil.rmtree(wt, ignore_errors=True)
    git(root, "worktree", "prune", check=False)
