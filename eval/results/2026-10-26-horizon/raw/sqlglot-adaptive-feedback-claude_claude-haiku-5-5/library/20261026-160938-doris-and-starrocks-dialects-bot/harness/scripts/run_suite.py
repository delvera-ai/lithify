#!/usr/bin/env python3
"""Run the project's pytest suite exactly once, to a log file, and print a short verdict.

Usage (from the repository root, with the project's python from memory.md):
    <python> .lithify/harness/scripts/run_suite.py                 # full suite
    <python> .lithify/harness/scripts/run_suite.py tests/dialects/test_doris.py
    <python> .lithify/harness/scripts/run_suite.py --timeout 540 -- -k "not tpcds"

Why: in this repo, launching a second full run while one was still going (auto-backgrounded
runs, "retry" runs) left several pytest processes competing for CPU; a ~80 s suite then took
over 10 minutes per run and every run was killed. This script refuses to start a second run
from the same checkout, enforces its own time limit, and always tells you where it stopped.

Output: elapsed time, a warning if other pytest processes are running on the machine,
every FAILED/ERROR line, and pytest's final summary line. The full verbose log path is printed.
Exit codes: pytest's own exit code (0 = all passed, 1 = failures, ...);
3 = a run from this checkout is already in progress (nothing started);
124 = time limit hit (process group killed; the test it was on is printed).
"""
import argparse
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _other_pytests() -> list[str]:
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,etime,command"], capture_output=True, text=True, check=False
        ).stdout
    except OSError:
        return []
    me = str(os.getpid())
    rows = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        exe = parts[2].split(None, 1)[0] if len(parts) == 3 else ""
        if "python" in os.path.basename(exe) and "-m pytest" in parts[2] and parts[0] != me:
            rows.append(line[:160])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--timeout", type=int, default=540, help="seconds before the run is killed")
    ap.add_argument("pytest_args", nargs="*", help="test paths / extra pytest args (after --)")
    args = ap.parse_args()

    root = os.getcwd()
    key = hashlib.sha1(root.encode()).hexdigest()[:10]
    tmp = tempfile.gettempdir()
    lock = os.path.join(tmp, f"lithify-suite-{key}.lock")
    log = os.path.join(tmp, f"lithify-suite-{key}.log")

    if os.path.exists(lock):
        try:
            pid = int(open(lock).read().strip() or 0)
        except (OSError, ValueError):
            pid = 0
        if pid and _alive(pid):
            print(f"BUSY: a run from this checkout is already in progress (pid {pid}).")
            print(f"Do not start another. Its log is {log}; wait for it to finish.")
            return 3
        os.remove(lock)

    others = _other_pytests()
    if others:
        print(f"WARNING: {len(others)} other pytest process(es) running; expect slower runs:")
        for row in others:
            print("  " + row)

    cmd = [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider", "--color=no"]
    cmd += args.pytest_args
    print("RUN: " + " ".join(cmd))
    print(f"LOG: {log}")
    sys.stdout.flush()

    start = time.time()
    with open(log, "w") as fh:
        proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        with open(lock, "w") as lf:
            lf.write(str(proc.pid))
        try:
            code = proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = 124
        finally:
            if os.path.exists(lock):
                os.remove(lock)
    elapsed = time.time() - start

    lines = open(log, errors="replace").read().splitlines()
    print(f"ELAPSED: {elapsed:.0f}s")
    if code == 124:
        print(f"TIMEOUT after {args.timeout}s. Last lines (the test in progress is last):")
        for line in lines[-3:]:
            print("  " + line[:200])
        print("Check the WARNING above for competing runs before suspecting a hang.")
        return 124

    bad = [ln for ln in lines if ln.startswith(("FAILED", "ERROR", "SUBFAILED"))]
    for ln in bad[:40]:
        print(ln[:240])
    if len(bad) > 40:
        print(f"... {len(bad) - 40} more; see {log}")
    summary = next((ln for ln in reversed(lines) if ln.strip()), "(empty log)")
    print(f"SUMMARY: {summary.strip('= ')}")
    print(f"EXIT: {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
