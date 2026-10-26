#!/usr/bin/env python3
"""Lint/type/YAML checks for the files changed in the working tree.

The project venv (the one that runs pytest) has no pip, ruff, mypy or PyYAML,
and `uv`/`uvx` are absent. This script makes ONE throwaway venv in /tmp with
those tools, then checks only the changed files:

  - changed *.py            -> ruff check, ruff format --check, mypy (strict,
                               from pyproject, resolving imports against the
                               project interpreter)
  - releasenotes/notes/*.yaml -> must parse as a YAML mapping of reno sections

Usage (from the repo root):
    <project python> .lithify/harness/scripts/check_changed.py

Exit codes:
    0  every check ran and passed
    1  a check ran and failed -- fix the reported lines, then re-run once
    2  tooling unavailable (venv/pip install failed) -- do NOT retry; report
       lint/type/YAML as "not run" with the printed reason
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv

VENV = "/tmp/tenacity-check-venv"
TOOLS = ["ruff", "mypy", "pyyaml"]
RENO_SECTIONS = {
    "prelude",
    "features",
    "issues",
    "upgrade",
    "deprecations",
    "critical",
    "security",
    "fixes",
    "other",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def changed_files() -> list[str]:
    tracked = run(["git", "diff", "--name-only", "HEAD"])
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    if tracked.returncode != 0:
        print("UNAVAILABLE: git diff failed:", tracked.stderr.strip())
        sys.exit(2)
    names = set(tracked.stdout.split()) | set(untracked.stdout.split())
    return sorted(n for n in names if os.path.exists(n))


def ensure_venv() -> str:
    py = os.path.join(VENV, "bin", "python")
    if os.path.exists(py) and run([py, "-c", "import ruff, mypy, yaml"]).returncode == 0:
        return py
    try:
        venv.EnvBuilder(with_pip=True, clear=True).create(VENV)
    except Exception as exc:  # ensurepip missing, disk, permissions
        print(f"UNAVAILABLE: could not create {VENV}: {exc}")
        sys.exit(2)
    res = run([py, "-m", "pip", "install", "-q", *TOOLS])
    if res.returncode != 0:
        print("UNAVAILABLE: pip install failed (offline?):")
        print(res.stderr.strip()[-2000:])
        sys.exit(2)
    return py


def main() -> int:
    files = changed_files()
    py_files = [f for f in files if f.endswith(".py") and not f.startswith(".lithify/")]
    notes = [
        f
        for f in files
        if f.startswith("releasenotes/notes/") and f.endswith((".yaml", ".yml"))
    ]
    print("changed:", ", ".join(files) or "(none)")
    if not py_files and not notes:
        print("nothing to check")
        return 0

    tool_py = ensure_venv()
    failed = False

    if py_files:
        checks = [
            ("ruff check", [tool_py, "-m", "ruff", "check", *py_files]),
            ("ruff format --check", [tool_py, "-m", "ruff", "format", "--check", *py_files]),
            (
                "mypy",
                [tool_py, "-m", "mypy", "--python-executable", sys.executable, *py_files],
            ),
        ]
        for label, cmd in checks:
            res = run(cmd)
            status = "PASS" if res.returncode == 0 else "FAIL"
            failed |= res.returncode != 0
            print(f"[{status}] {label}")
            if res.returncode != 0:
                print((res.stdout + res.stderr).strip()[-4000:])

    for note in notes:
        code = (
            "import sys, yaml\n"
            "d = yaml.safe_load(open(sys.argv[1]))\n"
            "assert isinstance(d, dict) and d, 'not a non-empty mapping'\n"
            "bad = set(d) - set(sys.argv[2].split(','))\n"
            "assert not bad, f'unknown reno sections: {sorted(bad)}'\n"
            "for k, v in d.items():\n"
            "    if k == 'prelude':\n"
            "        assert isinstance(v, str), 'prelude: must be a string'\n"
            "        continue\n"
            "    assert isinstance(v, list) and all(isinstance(e, str) for e in v),"
            " f'{k}: must be a list of strings'\n"
        )
        res = run([tool_py, "-c", code, note, ",".join(sorted(RENO_SECTIONS))])
        status = "PASS" if res.returncode == 0 else "FAIL"
        failed |= res.returncode != 0
        print(f"[{status}] reno yaml {note}")
        if res.returncode != 0:
            print(res.stderr.strip().splitlines()[-1])

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
