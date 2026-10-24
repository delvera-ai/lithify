#!/usr/bin/env python3
"""Stdlib-only style/shape checks for the files changed in the working tree.

ruff, mypy and PyYAML cannot run here: the project venv has no pip, and
building a /tmp venv dies in ensurepip (SIGABRT). So this script installs
nothing. It mechanically checks what the tools would most often catch:

  - changed *.py (added lines only; whole file if untracked)
      * compiles (syntax)
      * line length <= 88 (ruff line-length; do NOT eyeball this)
      * no tabs / trailing whitespace
      * a nested `def`/`class` is preceded by a blank line (ruff format);
        a decorated one sits directly under its decorator, even after `)`
      * every added `def` annotates all parameters and its return (mypy
        strict covers tenacity/ AND tests/; `self`/`cls` exempt)
  - releasenotes/notes/*.yaml
      * starts with `---`, top-level keys are reno sections, each section
        holds `- ` list entries, no tabs

Usage (from the repo root):
    <project python> .lithify/harness/scripts/check_changed.py

Exit codes:
    0  all checks above passed (ruff/mypy themselves still NOT run -- say so)
    1  a check failed -- fix the reported file:line, then re-run once
    2  could not determine changed files (git failed) -- report as not run
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys

MAX_LEN = 88
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
DEF_RE = re.compile(r"^(\s+)(async\s+def|def|class)\s")


def git(*args: str) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"UNAVAILABLE: git {' '.join(args)} failed: {res.stderr.strip()}")
        sys.exit(2)
    return res.stdout


def added_lines(path: str, untracked: bool) -> set[int]:
    """1-based line numbers added/changed in the working tree."""
    if untracked:
        with open(path, encoding="utf-8") as fh:
            return set(range(1, sum(1 for _ in fh) + 1))
    out = git("diff", "-U0", "HEAD", "--", path)
    lines: set[int] = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", out, re.M):
        start, count = int(m.group(1)), int(m.group(2) or "1")
        lines.update(range(start, start + count))
    return lines


def check_py(path: str, changed: set[int]) -> list[str]:
    errs: list[str] = []
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    try:
        compile(src, path, "exec")
    except SyntaxError as exc:
        errs.append(f"{path}:{exc.lineno}: syntax error: {exc.msg}")
    errs += check_annotations(path, src, changed)
    decorated = decorated_def_lines(src)
    lines = src.splitlines()
    for no in sorted(changed):
        if no > len(lines):
            continue
        line = lines[no - 1]
        if len(line) > MAX_LEN:
            errs.append(f"{path}:{no}: line is {len(line)} columns (max {MAX_LEN})")
        if "\t" in line:
            errs.append(f"{path}:{no}: tab character")
        if line != line.rstrip():
            errs.append(f"{path}:{no}: trailing whitespace")
        m = DEF_RE.match(line)
        # A decorated def follows its decorator directly (ruff puts no blank
        # line there), even when a multi-line decorator ends with `)`.
        if m and no >= 2 and no not in decorated:
            prev = lines[no - 2]
            prev_s = prev.strip()
            opener = prev_s.endswith(":") or prev_s.startswith(("@", "#"))
            if prev_s and not opener:
                errs.append(
                    f"{path}:{no}: nested {m.group(2)} needs a blank line before it"
                )
    return errs


def decorated_def_lines(src: str) -> set[int]:
    """Line numbers of `def`/`class` statements that carry decorators."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    return {
        n.lineno for n in ast.walk(tree) if isinstance(n, kinds) and n.decorator_list
    }


def check_annotations(path: str, src: str, changed: set[int]) -> list[str]:
    """mypy-strict proxy: an added def must annotate every param and return."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    errs: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.lineno not in changed:
            continue
        a = node.args
        params = [*a.posonlyargs, *a.args]
        if params and params[0].arg in ("self", "cls"):
            params = params[1:]
        params += a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]
        missing = [x.arg for x in params if x.annotation is None]
        if missing:
            errs.append(
                f"{path}:{node.lineno}: def {node.name}: unannotated "
                f"param(s) {', '.join(missing)} (mypy strict)"
            )
        if node.returns is None:
            errs.append(
                f"{path}:{node.lineno}: def {node.name}: missing return "
                "annotation (mypy strict; use -> None)"
            )
    return errs


def check_reno(path: str) -> list[str]:
    errs: list[str] = []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        errs.append(f"{path}:1: must start with '---'")
    section = None
    has_entry: dict[str, bool] = {}
    for no, line in enumerate(lines, 1):
        if "\t" in line:
            errs.append(f"{path}:{no}: tab character")
        if not line.strip() or line.strip() == "---":
            continue
        if not line.startswith(" "):
            key = line.split(":", 1)[0].strip()
            if not line.rstrip().endswith(":") and key != "prelude":
                errs.append(f"{path}:{no}: top-level line must be '<section>:'")
            if key not in RENO_SECTIONS:
                errs.append(f"{path}:{no}: unknown reno section {key!r}")
            section = key
            has_entry.setdefault(key, False)
        elif section and line.lstrip().startswith("- "):
            has_entry[section] = True
    if not has_entry:
        errs.append(f"{path}: no reno section found")
    for key, ok in has_entry.items():
        if not ok and key != "prelude":
            errs.append(f"{path}: section {key!r} has no '- ' entry")
    return errs


def main() -> int:
    tracked = set(git("diff", "--name-only", "HEAD").split())
    untracked = set(git("ls-files", "--others", "--exclude-standard").split())
    files = sorted(
        f
        for f in tracked | untracked
        if os.path.exists(f) and not f.startswith(".lithify/")
    )
    print("changed:", ", ".join(files) or "(none)")
    errs: list[str] = []
    for f in files:
        if f.endswith(".py"):
            errs += check_py(f, added_lines(f, f in untracked))
        elif f.startswith("releasenotes/notes/") and f.endswith((".yaml", ".yml")):
            errs += check_reno(f)
    for e in errs:
        print("FAIL", e)
    print(f"{'FAIL' if errs else 'PASS'}: {len(errs)} problem(s)")
    if errs:
        print(
            "HINT: this is a heuristic. If a FAIL contradicts a rule in"
            " skills/tenacity-change-contract, keep the code as the skill says and"
            " report the FAIL as a checker false positive; don't reshape the code"
        )
    print("NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
