#!/usr/bin/env python3
"""Run pytest in the foreground with a hard time limit; name the test that hangs.

A retry loop with no `stop=` (tenacity's default is never stop, no wait) spins
forever when the predicate under test is wrong, so a single bad test can hang
the whole suite with no output. This script bounds every run and, on timeout,
prints the node id of the test that was running.

Usage (from the repo root, with the project python from memory.md):
    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
    e.g.  ... run_tests.py                                  # full suite, 300 s
          ... run_tests.py --timeout 60 tests/test_x.py::Cls::test_name

Output: the last 40 lines of pytest -v output (full log in /tmp/run_tests.log),
then one verdict line.

Exit codes:
    0..5  pytest's own exit code (0 = all passed, 1 = failures, ...)
    124   TIMEOUT: process group killed; `HUNG IN: <node id>` names the test.
          Do not re-run the suite unchanged. Run that node id alone with
          --timeout 60; if it is a test you wrote, make its retry loop bounded
          (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
    if args[:1] == ["--timeout"]:
        if len(args) < 2:
            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
            return 2
        timeout = float(args[1])
        args = args[2:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "-rfE",
        "-p",
        "no:cacheprovider",
        "--color=no",
        *args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
    chunks: list[bytes] = []

    def pump() -> None:
        assert proc.stdout is not None
        fd = proc.stdout.fileno()
        while True:
            data = os.read(fd, 4096)
            if not data:
                break
            chunks.append(data)

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    timed_out = False
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        code = proc.wait()
    reader.join(timeout=5)

    text = b"".join(chunks).decode("utf-8", "replace")
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write(text)
    lines = text.splitlines()
    print("\n".join(lines[-40:]))
    print("---")
    if timed_out:
        hung = "(unknown: no test had started)"
        for line in reversed(lines):
            word = line.split(" ", 1)[0]
            if "::" in word:
                hung = word
                break
        print(f"TIMEOUT after {timeout:.0f}s; process group killed")
        print(f"HUNG IN: {hung}")
        print("exit=124 (see this script's docstring for the next step)")
        return 124
    print(f"exit={code} (pytest); full log: {LOG}")
    return code


if __name__ == "__main__":
    sys.exit(main())
