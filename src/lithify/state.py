"""Stability score and the dynamic-k ("annealing") schedule.

S in [0, 1] = first_pass_rate * (w + (1 - w) * (1 - normalized_harness_churn)),
over a rolling window of recent tasks, scaled down until the window has enough tasks.
Churn only modulates stability once the harness is passing: a harness that never passes
is unstable no matter how little it changes.

    S <  explore_below  -> k = max_k   (genesis: wide parallel exploration)
    S <  cruise_at      -> k = 1       (one Propose-Probe-Compose step)
    S >= cruise_at      -> k = 0       (cruise: execute once, observe, escalate on failure)

Anomaly spikes override the phase: one failure at k = 0 forces k = 1 on the next task,
two consecutive failures force k = max_k.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import LITHIFY_DIR, Schedule

STATE_FILE = "state.json"


@dataclass
class TaskRecord:
    task_id: str
    k: int
    first_pass: bool
    delivered: bool
    churn_lines: int
    executions: int
    tokens_in: int = 0
    tokens_cached: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    wall_s: float = 0.0
    always_on_tokens: int = 0
    stability_after: float = 0.0
    # Set by `lithify feedback`: the delivered work later failed a check (CI, review, a hidden test).
    feedback_failed: bool = False


@dataclass
class State:
    consecutive_failures: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    def records(self) -> list[TaskRecord]:
        return [TaskRecord(**h) for h in self.history]


def state_path(root: Path) -> Path:
    return root / LITHIFY_DIR / STATE_FILE


def load_state(root: Path) -> State:
    p = state_path(root)
    if not p.exists():
        return State()
    data = json.loads(p.read_text(encoding="utf-8"))
    return State(
        consecutive_failures=int(data.get("consecutive_failures", 0)),
        history=list(data.get("history", [])),
    )


def save_state(root: Path, st: State) -> None:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(st), indent=2) + "\n", encoding="utf-8")


def stability(history: list[dict[str, Any]], sched: Schedule) -> float:
    recent = history[-sched.window :] if sched.window > 0 else history
    if not recent:
        return 0.0
    fpr = sum(1 for h in recent if h.get("first_pass")) / len(recent)
    mean_churn = sum(int(h.get("churn_lines", 0)) for h in recent) / len(recent)
    churn_norm = min(1.0, mean_churn / max(1, sched.churn_scale_lines))
    w = sched.first_pass_weight
    # Fewer than `window` tasks means we have not observed enough to trust a high score.
    confidence = min(1.0, len(recent) / max(1, min(sched.window, 5)))
    return round(confidence * fpr * (w + (1 - w) * (1 - churn_norm)), 4)


def phase_for(s: float, sched: Schedule) -> str:
    if s < sched.explore_below:
        return "genesis"
    if s < sched.cruise_at:
        return "build"
    return "cruise"


def choose_k(st: State, sched: Schedule, max_k: int) -> tuple[int, str]:
    """Return (k, reason)."""
    if st.consecutive_failures >= 2:
        return max_k, f"anomaly spike: {st.consecutive_failures} consecutive failures"
    s = stability(st.history, sched)
    phase = phase_for(s, sched)
    if st.consecutive_failures == 1 and phase == "cruise":
        return 1, "anomaly: last task failed in cruise"
    if phase == "genesis":
        return max_k, f"genesis (S={s:.2f})"
    if phase == "build":
        return 1, f"build (S={s:.2f})"
    return 0, f"cruise (S={s:.2f})"


def mark_feedback_failed(root: Path, task_id: str, sched: Schedule) -> bool:
    """A delivered task failed after delivery: it no longer counts as a first-pass success, so
    stability drops and the schedule explores again. Returns False if the task is not in history."""
    st = load_state(root)
    for i, h in enumerate(st.history):
        if h.get("task_id") == task_id:
            was_pass = bool(h.get("first_pass"))
            h["first_pass"] = False
            h["feedback_failed"] = True
            if was_pass and i == len(st.history) - 1:
                st.consecutive_failures += 1
            st.history[-1]["stability_after"] = stability(st.history, sched)
            save_state(root, st)
            return True
    return False


def record_task(root: Path, st: State, rec: TaskRecord, sched: Schedule) -> State:
    st.history.append(asdict(rec))
    # "Failure" means the current harness did not pass the gates on its first execution,
    # even if escalation later recovered the task: the harness still needed help.
    st.consecutive_failures = 0 if rec.first_pass else st.consecutive_failures + 1
    st.history[-1]["stability_after"] = stability(st.history, sched)
    save_state(root, st)
    return st
