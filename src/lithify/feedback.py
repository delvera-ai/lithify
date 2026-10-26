"""Post-delivery feedback: harden the harness from a failure found after a task was delivered.

    lithify feedback <task-id> --log ci-output.txt

A task can pass every gate and still be wrong: a CI job, a reviewer or a test written later finds
what the gates did not check. That failure is the most valuable evidence the harness can get, and
without it a passing gate is never questioned. This command feeds it back:

1. The delivered rollout's evidence is copied, and its gate report is replaced by the
   post-delivery failure ("GATES: FAIL — after delivery"), so the existing role prompts read it
   exactly as they read any failed gate.
2. One domain and one invariant proposer edit a copy of the live harness against that evidence,
   with a repo snapshot that includes the delivered (applied) patch; a composer merges them.
3. The result becomes a reviewable proposal (`lithify adopt <task-id>-feedback`). Nothing is
   probed — the original task is history — so it is never auto-promoted.
4. The task's state record stops counting as a first-pass success, so stability drops and the
   schedule explores again on the next tasks.

The feedback never changes the task it is about: that work is already delivered.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import worktree
from .config import LITHIFY_DIR, load_config
from .harness import copy_harness, diff, harness_dir
from .library import Reflection
from .pipeline import Pipeline
from .state import mark_feedback_failed

GATE_HEADER = "GATES: FAIL — a check failed after this work was delivered (post-delivery feedback)"


@dataclass
class _Evidence:
    label: str
    evidence: Path


def feedback(start: Path, task_id: str, log_text: str, log=print) -> dict[str, Any]:
    root = worktree.repo_root(start)
    cfg = load_config(root)
    rdir = root / LITHIFY_DIR / "runs" / task_id
    outcome_file = rdir / "outcome.json"
    if not outcome_file.exists():
        raise RuntimeError(f"no outcome for task {task_id!r} under {rdir}")
    outcome = json.loads(outcome_file.read_text(encoding="utf-8"))
    selected = outcome.get("selected") or ""
    src = rdir / "rollouts" / selected
    if not selected or not src.is_dir():
        raise RuntimeError(f"task {task_id} delivered nothing; feedback applies to delivered work")

    pipe = Pipeline(root, cfg, log=log)
    pipe.task = outcome.get("task", "")
    pipe.task_id = f"{task_id}-feedback"
    pipe.runs_dir = rdir / "feedback"
    pipe.work = worktree.work_base(root) / pipe.task_id
    pipe.dirty = worktree.dirty_patch(root)  # the delivered patch, if it is still applied
    shutil.rmtree(pipe.runs_dir, ignore_errors=True)
    pipe.work.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"task_id": task_id, "proposal": None, "components": []}
    try:
        base_h = copy_harness(harness_dir(root), pipe.work / "harness-start")
        ev = pipe.runs_dir / "rollouts" / "delivered"
        shutil.copytree(src, ev)
        at_delivery = (ev / "gates.md").read_text(encoding="utf-8") if (ev / "gates.md").exists() else ""
        (ev / "gates.md").write_text(
            f"{GATE_HEADER}\n\n## post-delivery check output\n{log_text.strip()[-6000:]}\n\n"
            f"## gates at delivery (they passed, but did not cover this)\n{at_delivery}\n",
            encoding="utf-8",
        )
        # Only `.label` and `.evidence` are read from probes when copying rollouts into role contexts.
        evidence: list[Any] = [_Evidence("delivered", ev)]
        pipe.snapshot = pipe._new_wt("snapshot")
        log(f"lithify ▸ feedback on {task_id} (delivered by {selected})")
        cands = [pipe.propose("dom", 1, 1, base_h, evidence), pipe.propose("inv", 1, 1, base_h, evidence)]
        valid = [c for c in cands if c.valid and diff(base_h, c.harness)[1] > 0]
        chosen = valid[0] if valid else None
        if len(valid) > 1:
            comp = pipe.compose(1, 1, base_h, evidence, valid, {})
            if comp.valid and diff(base_h, comp.harness)[1] > 0:
                chosen = comp
        if chosen is not None:
            hdiff, _, changed = diff(base_h, chosen.harness)
            refl = Reflection()
            pdir = pipe._write_proposal(chosen.harness, hdiff, changed, refl)
            (pdir / "FEEDBACK.md").write_text(
                f"Post-delivery feedback on {task_id}.\n\n## check output\n{log_text.strip()[-6000:]}\n",
                encoding="utf-8",
            )
            result.update(proposal=str(pdir), components=sorted(changed))
            log(f"  ⧗ proposal for review: {pdir.relative_to(root)} ({', '.join(sorted(changed))})")
        else:
            log("  · no harness change proposed")
    finally:
        for wt in pipe._wts:
            worktree.remove(root, wt)
        shutil.rmtree(pipe.work, ignore_errors=True)
    result["marked"] = mark_feedback_failed(root, task_id, cfg.schedule)
    result["usage"] = pipe.usage
    pipe.runs_dir.mkdir(parents=True, exist_ok=True)
    (pipe.runs_dir / "feedback.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
