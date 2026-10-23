"""Deterministic gates: zero-token quality checks run inside each probe worktree.

Only candidates that pass every gate reach the (token-costing) blind selector. Edits to
tests that existed before the probe are treated as a gate failure by default: the tests
are the oracle, and an agent that rewrites its own oracle is the failure mode the
Harness² paper documents ("a checker written by the editor cannot catch the editor's
assumption").
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]+\.py$|_test\.(py|go)$|\.(test|spec)\.[jt]sx?$")


@dataclass
class GateRun:
    name: str
    cmd: str
    returncode: int
    seconds: float
    tail: str


@dataclass
class GateResult:
    passed: bool
    runs: list[GateRun] = field(default_factory=list)
    protected_test_edits: list[str] = field(default_factory=list)
    note: str = ""

    def summary(self) -> str:
        if not self.runs and not self.protected_test_edits:
            return "no gates configured" + (f"; {self.note}" if self.note else "")
        parts = [f"{r.name}={'pass' if r.returncode == 0 else f'FAIL({r.returncode})'}" for r in self.runs]
        if self.protected_test_edits:
            parts.append(f"edited-existing-tests={len(self.protected_test_edits)}")
        return ", ".join(parts)

    def report(self) -> str:
        lines = [f"GATES: {'PASS' if self.passed else 'FAIL'} — {self.summary()}"]
        for r in self.runs:
            lines.append(f"\n## {r.name}: `{r.cmd}` -> exit {r.returncode} ({r.seconds:.1f}s)\n{r.tail}")
        if self.protected_test_edits:
            lines.append("\n## edited pre-existing tests\n" + "\n".join(self.protected_test_edits))
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def run_gates(
    wt: Path,
    commands: list[tuple[str, str]],
    changed: list[tuple[str, str]],
    timeout_s: int = 900,
    allow_test_edits: bool = False,
    tail_chars: int = 2500,
    weakened: list[str] | None = None,
) -> GateResult:
    """`weakened` (from worktree.weakened_tests) refines which modified test files count; when it is
    None every modified or deleted pre-existing test file counts."""
    runs: list[GateRun] = []
    for name, cmd in commands:
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=wt,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            rc, out = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired as e:
            rc = 124
            out = f"TIMEOUT after {timeout_s}s\n" + str(e.stdout or "")[-1000:]
        runs.append(GateRun(name, cmd, rc, time.time() - t0, out[-tail_chars:]))
    deleted = [f"D {p}" for st, p in changed if st in ("D", "R") and is_test_path(p)]
    if weakened is None:
        protected = [f"{st} {p}" for st, p in changed if st == "M" and is_test_path(p)] + deleted
    else:
        protected = [f"M {w}" for w in weakened] + deleted
    passed = all(r.returncode == 0 for r in runs) and (allow_test_edits or not protected)
    return GateResult(passed=passed, runs=runs, protected_test_edits=protected)
