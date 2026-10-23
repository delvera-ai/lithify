#!/usr/bin/env python
"""Compare what Python expressions return on a git revision (default HEAD) vs the working tree.

Use it to show a bug on the unmodified code and to confirm that each new test input changes
output, without touching the working tree.

Usage (run from anywhere inside the repository, with the project's interpreter, WITHOUT -I):
    <python> compare_outputs.py 'naturalsize(999999)' 'naturalsize(1024**2 - 1, binary=True)'
    <python> compare_outputs.py --file exprs.txt          # one expression per line, '#' comments ok
    <python> compare_outputs.py --rev HEAD~1 --package humanize --src src 'intword(10**6)'

Each expression is evaluated with `import <package>` and `from <package> import *` already done.
A raised exception is reported as `!ExcType: message`, so error-path changes are compared too.

How it works: `git archive <rev> <src>` is extracted into a temp dir. Each side runs in its own
subprocess with PYTHONPATH=<side>/<src> and an empty cwd, and must import the package from that
side (checked via `<package>.__file__`), so the two versions can never share `sys.modules`.

Output: one block per expression (`same` or `CHANGED`, then `old:` / `new:`), then a final line
`N expressions, C changed, S same`.
Exit status: 0 = comparison ran (whatever the count); 2 = setup failure (not a git repo, bad
revision, import from the wrong place, no expressions). Nothing is written outside a temp dir.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RUNNER = r"""
import json, os, sys
pkg, expected_root = sys.argv[1], os.path.realpath(sys.argv[2])
mod = __import__(pkg)
where = os.path.realpath(getattr(mod, "__file__", "") or "")
if not where.startswith(expected_root + os.sep):
    print(json.dumps({"setup_error": f"{pkg} imported from {where}, expected under {expected_root}"}))
    sys.exit(0)
ns = {pkg: mod}
exec(f"from {pkg} import *", ns)
out = []
for expr in json.load(sys.stdin):
    try:
        out.append(repr(eval(expr, ns)))
    except BaseException as e:  # report, don't crash: error paths are behaviour too
        out.append(f"!{type(e).__name__}: {e}")
print(json.dumps({"results": out, "file": where}))
"""


def fail(msg: str) -> None:
    print(f"compare_outputs: SETUP FAILURE: {msg}", file=sys.stderr)
    sys.exit(2)


def run_side(python: str, src_dir: Path, package: str, exprs: list[str]) -> tuple[list[str], str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(src_dir)
    env.pop("PYTHONHOME", None)
    with tempfile.TemporaryDirectory() as empty_cwd:
        proc = subprocess.run(
            [python, "-c", RUNNER, package, str(src_dir)],
            input=json.dumps(exprs),
            capture_output=True,
            text=True,
            cwd=empty_cwd,
            env=env,
            check=False,
        )
    if proc.returncode != 0:
        fail(f"subprocess for {src_dir} exited {proc.returncode}:\n{proc.stderr.strip()}")
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        fail(f"unreadable output from {src_dir}:\n{proc.stdout}\n{proc.stderr}")
    if "setup_error" in data:
        fail(data["setup_error"])
    return data["results"], data["file"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exprs", nargs="*", help="Python expressions to evaluate on both sides")
    ap.add_argument("--file", help="file with one expression per line")
    ap.add_argument("--rev", default="HEAD", help="git revision for the 'old' side (default HEAD)")
    ap.add_argument("--package", default="humanize", help="package to import (default humanize)")
    ap.add_argument("--src", default="src", help="source dir relative to repo root (default src)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for both sides")
    args = ap.parse_args()

    exprs = list(args.exprs)
    if args.file:
        try:
            lines = Path(args.file).read_text().splitlines()
        except OSError as e:
            fail(str(e))
        exprs += [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    if not exprs:
        fail("no expressions given")

    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if top.returncode != 0:
        fail("not inside a git repository")
    root = Path(top.stdout.strip())
    new_src = root / args.src
    if not new_src.is_dir():
        fail(f"{new_src} is not a directory")

    with tempfile.TemporaryDirectory() as tmp:
        tar_path = Path(tmp) / "old.tar"
        arch = subprocess.run(
            ["git", "-C", str(root), "archive", "--format=tar", "-o", str(tar_path), args.rev, args.src],
            capture_output=True,
            text=True,
            check=False,
        )
        if arch.returncode != 0:
            fail(f"git archive {args.rev} {args.src} failed: {arch.stderr.strip()}")
        old_root = Path(tmp) / "old"
        with tarfile.open(tar_path) as tf:
            # archive comes from this repo's own git objects
            if hasattr(tarfile, "data_filter"):
                tf.extractall(old_root, filter="data")
            else:
                tf.extractall(old_root)  # noqa: S202
        old, old_file = run_side(args.python, old_root / args.src, args.package, exprs)
        new, new_file = run_side(args.python, new_src, args.package, exprs)

    print(f"old = {args.rev} ({old_file})")
    print(f"new = working tree ({new_file})")
    changed = 0
    for expr, o, n in zip(exprs, old, new):
        tag = "same   " if o == n else "CHANGED"
        changed += o != n
        print(f"{tag} {expr}\n    old: {o}\n    new: {n}")
    print(f"{len(exprs)} expressions, {changed} changed, {len(exprs) - changed} same")


if __name__ == "__main__":
    main()
