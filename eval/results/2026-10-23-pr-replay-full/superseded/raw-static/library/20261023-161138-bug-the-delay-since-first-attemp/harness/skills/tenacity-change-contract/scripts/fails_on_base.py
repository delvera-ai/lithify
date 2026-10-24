#!/usr/bin/env python3
"""Check that new/changed tests FAIL on the unmodified code (HEAD), read-only.

Usage (from the repo root, with the project interpreter so pytest is importable):
    <project-python> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \
        tests/test_x.py::TestY::test_z [more pytest node ids or args ...]

What it does: exports HEAD with `git archive` into a temp dir, copies the
working-tree `tests/` directory over it (so your new tests run against the OLD
package code), confirms `import tenacity` resolves inside the temp dir, and runs
pytest there with the arguments you gave. The working tree, index and stash are
never touched.

Exit codes:
    0  GOOD  - the tests fail (or fail to import) on HEAD: they catch the bug.
    1  BAD   - the tests pass on HEAD: they do not reproduce the bug.
    2  ERROR - the check could not run; report the fail-on-base check as NOT verified.
"""

import os
import shutil
import subprocess
import sys
import tempfile


def main(argv: list[str]) -> int:
    if not argv:
        print("ERROR: pass the pytest node ids of the new tests", file=sys.stderr)
        return 2
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: not inside a git repository: {exc}", file=sys.stderr)
        return 2
    tests_dir = os.path.join(root, "tests")
    if not os.path.isdir(tests_dir):
        print(f"ERROR: no tests/ directory under {root}", file=sys.stderr)
        return 2

    tmp = tempfile.mkdtemp(prefix="fails_on_base_")
    try:
        archive = subprocess.run(
            ["git", "-C", root, "archive", "--format=tar", "HEAD"],
            capture_output=True, check=False,
        )
        if archive.returncode != 0:
            print("ERROR: git archive HEAD failed:", archive.stderr.decode(), file=sys.stderr)
            return 2
        untar = subprocess.run(
            ["tar", "-x", "-C", tmp], input=archive.stdout, capture_output=True, check=False
        )
        if untar.returncode != 0:
            print("ERROR: extracting HEAD failed:", untar.stderr.decode(), file=sys.stderr)
            return 2
        shutil.rmtree(os.path.join(tmp, "tests"), ignore_errors=True)
        shutil.copytree(
            tests_dir, os.path.join(tmp, "tests"),
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

        probe = subprocess.run(
            [sys.executable, "-c", "import tenacity, os; print(os.path.realpath(tenacity.__file__))"],
            cwd=tmp, capture_output=True, text=True, check=False,
        )
        resolved = probe.stdout.strip()
        if probe.returncode != 0 or not resolved.startswith(os.path.realpath(tmp)):
            print(
                "ERROR: `import tenacity` does not resolve to the HEAD copy "
                f"(got {resolved or probe.stderr.strip()!r}); check not valid.",
                file=sys.stderr,
            )
            return 2

        run = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no", *argv],
            cwd=tmp, capture_output=True, text=True, check=False,
        )
        out = (run.stdout + run.stderr).splitlines()
        print("\n".join(out[-40:]))
        print("-" * 60)
        if run.returncode == 1:
            print("GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.")
            return 0
        if run.returncode == 2:
            print("GOOD (collection error): tests cannot even import on HEAD. "
                  "Confirm above that the error is the missing/changed name your fix adds.")
            return 0
        if run.returncode == 0:
            print("BAD: tests PASS on HEAD - they do not reproduce the bug. Rework the test.")
            return 1
        print(f"ERROR: pytest exit {run.returncode} (5 = no tests matched the ids). Not verified.")
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
