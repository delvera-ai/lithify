"""Task-level recursion (Propose -> Probe -> Compose -> Select) wrapped in the dynamic-k
schedule, followed by harnessing-level recursion (Reflect -> library -> promotion).

    k = 0  cruise     one execution with the current harness; gates pass -> apply, done
                      (zero improvement overhead). Gates fail -> escalate to k = 1 on the
                      same task, reusing that execution as the base rollout.
    k >= 1 parallel   k base rollouts, k INV + k DOM candidate harnesses, k compositions;
                      every harness is probed on the same task in its own worktree.
    k >= 1 sequential k chained contrastive steps, each starting from the last composition.

Deliverables that pass every deterministic gate go to a blind selector (skipped when only
one distinct deliverable passes). The selected deliverable is applied to the working tree;
its harness is the adopted harness H*. The reflector attributes each harness edit, writes
at most one lesson to the library, and — with auto_adopt — only components it marks
`helped` are promoted into the live harness. Everything else becomes a reviewable proposal.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import re
import shutil
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from . import prompts, worktree
from .adapters import get_adapter, split_spec
from .adapters.base import LimitReached, RunResult, hit_limit
from .config import CONFIG_FILE, LITHIFY_DIR, Config
from .gates import GateResult, is_test_path, run_gates
from .harness import always_on_text, copy_harness, diff, estimate_tokens, harness_dir, promote, render
from .library import Reflection, ensure_library, library_dir, parse_reflection, write_entry
from .state import TaskRecord, choose_k, load_state, record_task
from .validate import errors, validate

ROLE_PROMPT = "Read MISSION.md in the current directory and carry it out exactly. Work only inside the current directory."


@dataclass
class Probe:
    label: str
    harness: Path
    run: RunResult
    patch: str
    gates: GateResult
    evidence: Path
    verified: bool

    @property
    def passed(self) -> bool:
        return self.gates.passed and bool(self.patch.strip()) and self.run.ok


@dataclass
class Candidate:
    label: str
    scope: str  # inv | dom | comp
    harness: Path
    notes: str
    run: RunResult
    valid: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    task_id: str
    k: int
    reason: str
    delivered: bool
    applied: bool
    first_pass: bool
    selected: str = ""
    executions: int = 0
    role_sessions: int = 0
    proposal: Path | None = None
    promoted: list[str] = field(default_factory=list)
    message: str = ""
    record: TaskRecord | None = None


def slugify(text: str, n: int = 32) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n].strip("-") or "task"


def new_task_id(task: str) -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + slugify(task)


def _notes(text: str) -> str:
    m = re.search(r"<notes>(.*?)</notes>", text, re.S)
    return (m.group(1) if m else text[-3000:]).strip()


def _choice(text: str, ids: list[str]) -> str | None:
    m = re.search(r"```choice\s*\n?\s*([A-Za-z0-9_-]+)\s*\n?```", text)
    if m and m.group(1) in ids:
        return m.group(1)
    found = [i for i in ids if re.search(rf"\b{re.escape(i)}\b", text[-400:])]
    return found[-1] if len(found) >= 1 else None


class Pipeline:
    def __init__(
        self,
        root: Path,
        cfg: Config,
        log: Callable[[str], None] = print,
        keep_worktrees: bool = False,
        seed: int | None = None,
        escalate: bool = True,
    ):
        self.root = root
        self.escalate = escalate
        self.cfg = cfg
        self._log_lock = threading.Lock()
        self._sink = log
        self.keep = keep_worktrees
        self.rng = random.Random(seed)
        self._git_lock = threading.Lock()
        self._usage_lock = threading.Lock()
        self.usage: dict[str, float] = {"in": 0, "cached": 0, "out": 0, "cost": 0.0, "exec": 0, "roles": 0}
        self.dirty = ""
        self.task_id = ""
        self.task = ""
        self.runs_dir = Path()
        self.work = Path()
        self.snapshot: Path | None = None
        self.needs_review = ""
        self._wts: list[Path] = []

    # ------------------------------------------------------------------ plumbing

    def log(self, msg: str) -> None:
        with self._log_lock:
            self._sink(msg)

    def _account(self, r: RunResult, role: bool) -> None:
        with self._usage_lock:
            if r.raw_stream:
                sessions = self.runs_dir / "sessions"
                sessions.mkdir(parents=True, exist_ok=True)
                number = int(self.usage["exec"] + self.usage["roles"]) + 1
                prefix = sessions / f"{number:03d}-{'role' if role else 'execute'}"
                with gzip.open(prefix.with_suffix(".jsonl.gz"), "wt", encoding="utf-8") as stream:
                    stream.write(r.raw_stream)
                prefix.with_suffix(".json").write_text(json.dumps(r.meta, indent=2), encoding="utf-8")
            self.usage["in"] += r.tokens_in
            self.usage["cached"] += r.tokens_cached
            self.usage["out"] += r.tokens_out
            self.usage["cost"] += r.cost_usd
            self.usage["roles" if role else "exec"] += 1

    def _stop_on_limit(self, res: RunResult, what: str) -> None:
        """A limit notice means every later session would fail too: stop the task instead of burning
        through proposers and probes that record empty failures."""
        if hit_limit(res):
            raise LimitReached(f"{what} stopped by an agent CLI limit: {(res.error or res.text)[:300]}")

    def _adapter(self, spec: str):
        return get_adapter(spec, self.cfg.adapter_args.get(split_spec(spec)[0]))

    def _new_wt(self, name: str) -> Path:
        with self._git_lock:
            wt = worktree.create(self.root, f"{self.task_id}/{name}", self.dirty)
            self._wts.append(wt)
        # The config names the gate commands, including holdout_cmd: agents must not see it.
        (wt / LITHIFY_DIR / CONFIG_FILE).unlink(missing_ok=True)
        return wt

    def _pmap(self, fn, items):
        items = list(items)
        if not items:
            return []
        with ThreadPoolExecutor(max_workers=max(1, self.cfg.concurrency)) as ex:
            return list(ex.map(fn, items))

    # ------------------------------------------------------------------ probes

    def probe(self, label: str, hdir: Path) -> Probe:
        wt = self._new_wt(label)
        copy_harness(hdir, wt / LITHIFY_DIR / "harness")
        render(wt, wt / LITHIFY_DIR / "harness")
        with self._git_lock:
            worktree.seal_base(wt)
        self.log(f"  ▸ probe {label}: executing with {self.cfg.executor}")
        res = self._adapter(self.cfg.executor).run(self.task, wt, self.cfg.timeout_s, role="execute")
        self._account(res, role=False)
        self._stop_on_limit(res, f"probe {label}")
        patch = worktree.deliverable(wt)
        changed = worktree.changed_files(wt)
        cmds = self.cfg.gate_commands()
        modified_tests = [p for st, p in changed if st == "M" and is_test_path(p)]
        gates = run_gates(
            wt,
            cmds,
            changed,
            timeout_s=self.cfg.timeout_s,
            allow_test_edits=self.cfg.allow_test_edits,
            weakened=worktree.weakened_tests(wt, modified_tests),
        )
        if not cmds:
            gates.note = "no gates configured: deliverable is unverified"
        ev = self.runs_dir / "rollouts" / label
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "trajectory.md").write_text(
            f"# trajectory {label}\n\nfinal message:\n{res.text}\n\n## events\n{res.transcript}\n"
            + (f"\n## executor error\n{res.error}\n" if res.error else ""),
            encoding="utf-8",
        )
        (ev / "deliverable.patch").write_text(patch or "(no changes)\n", encoding="utf-8")
        (ev / "gates.md").write_text(gates.report() + "\n", encoding="utf-8")
        (ev / "run.json").write_text(
            json.dumps(
                {
                    "label": label,
                    "ok": res.ok,
                    "tokens_in": res.tokens_in,
                    "tokens_cached": res.tokens_cached,
                    "tokens_out": res.tokens_out,
                    "cost_usd": res.cost_usd,
                    "seconds": round(res.seconds, 1),
                    "gates_passed": gates.passed,
                    "patch_lines": patch.count("\n"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        p = Probe(label, hdir, res, patch, gates, ev, verified=bool(cmds))
        mark = "✓" if p.passed else "✗"
        self.log(f"  {mark} probe {label}: {gates.summary()}" + ("" if res.ok else f" [executor: {res.error[:120]}]"))
        return p

    # ------------------------------------------------------------------ role contexts

    def _ctx(self, name: str) -> Path:
        ctx = self.work / f"ctx-{name}"
        if ctx.exists():
            shutil.rmtree(ctx)
        (ctx / "context").mkdir(parents=True)
        (ctx / "context" / "task.md").write_text(self.task + "\n", encoding="utf-8")
        lib = library_dir(self.root)
        if lib.exists():
            shutil.copytree(
                lib, ctx / "context" / "library", ignore=shutil.ignore_patterns("harness")
            )  # index + lessons; harness on demand
            # executable harnesses are worth copying too, but keep contexts small: link them
            for d in lib.iterdir():
                if (d / "harness").is_dir():
                    tgt = ctx / "context" / "library" / d.name / "harness"
                    if not tgt.exists():
                        tgt.symlink_to(d / "harness", target_is_directory=True)
        if self.snapshot is not None:
            (ctx / "context" / "repo").symlink_to(self.snapshot, target_is_directory=True)
        return ctx

    def _copy_rollouts(self, ctx: Path, probes: list[Probe]) -> None:
        for p in probes:
            shutil.copytree(p.evidence, ctx / "context" / "rollouts" / p.label, dirs_exist_ok=True)

    def _role(self, role: str, ctx: Path, mission: str) -> RunResult:
        (ctx / "MISSION.md").write_text(mission, encoding="utf-8")
        cli = self.cfg.role_cli(role)
        res = self._adapter(cli).run(ROLE_PROMPT, ctx, self.cfg.timeout_s, role=role)
        self._account(res, role=True)
        self._stop_on_limit(res, f"role {role}")
        (ctx / "RESPONSE.md").write_text(res.text or res.error, encoding="utf-8")
        return res

    def _edit_session(self, role: str, ctx: Path, mission: str, label: str, scope: str) -> Candidate:
        res = self._role(role, ctx, mission)
        h = ctx / "context" / "harness"
        issues = validate(h, self.cfg.budget.always_on_tokens)
        errs = errors(issues)
        if errs and res.ok:
            self.log(f"  ↻ {label}: {len(errs)} validation error(s), one retry")
            retry = (
                mission
                + "\n\n# YOUR PREVIOUS EDIT FAILED VALIDATION\n\nFix exactly these and nothing else:\n"
                + "\n".join(f"- {e}" for e in errs)
                + "\n"
            )
            res2 = self._role(role, ctx, retry)
            res = res2 if res2.ok else res
            issues = validate(h, self.cfg.budget.always_on_tokens)
            errs = errors(issues)
        valid = res.ok and not errs
        if not valid:
            self.log(f"  ✗ {label}: discarded ({'; '.join(map(str, errs[:2])) or res.error[:120]})")
        else:
            self.log(f"  ✓ {label}: candidate harness ready")
        return Candidate(label, scope, h, _notes(res.text), res, valid, [str(i) for i in issues])

    def propose(self, scope: str, i: int, k: int, base_h: Path, evidence: list[Probe]) -> Candidate:
        label = f"{scope}-{i}"
        ctx = self._ctx(label)
        copy_harness(base_h, ctx / "context" / "harness")
        self._copy_rollouts(ctx, evidence)
        mission = prompts.render(f"propose_{scope}", I=i, K=k)
        self.log(f"  ▸ propose {label} ({self.cfg.role_cli('propose_' + scope)})")
        return self._edit_session(f"propose_{scope}", ctx, mission, label, scope)

    def compose(
        self, j: int, k: int, base_h: Path, base_probes: list[Probe], cands: list[Candidate], cand_probes: dict[str, Probe]
    ) -> Candidate:
        label = f"comp-{j}"
        ctx = self._ctx(label)
        copy_harness(base_h, ctx / "context" / "base_harness")
        copy_harness(base_h, ctx / "context" / "harness")
        self._copy_rollouts(ctx, base_probes + list(cand_probes.values()))
        for c in cands:
            cd = ctx / "context" / "candidates" / c.label
            copy_harness(c.harness, cd / "harness")
            (cd / "harness.diff").write_text(diff(base_h, c.harness)[0] or "(no change)\n", encoding="utf-8")
            (cd / "notes.md").write_text(c.notes + "\n", encoding="utf-8")
        mission = prompts.render("compose", K=k)
        self.log(f"  ▸ compose {label} ({self.cfg.role_cli('compose')})")
        return self._edit_session("compose", ctx, mission, label, "comp")

    def select(self, pool: list[Probe]) -> tuple[Probe, str]:
        # Distinct deliverables only: identical patches are one choice.
        # Ties on an identical deliverable: prefer the base harness (no change was needed),
        # then a composition (the merged successor), then single-scope candidates.
        def rank(p: Probe) -> int:
            name = p.label.split("-", 1)[-1] if p.label.startswith("r") and "-" in p.label else p.label
            return 0 if name.startswith(("base", "cruise")) else 1 if name.startswith("comp") else 2

        uniq: dict[str, Probe] = {}
        for p in sorted(pool, key=rank):
            uniq.setdefault(hashlib.sha1(p.patch.encode()).hexdigest(), p)
        distinct = list(uniq.values())
        if len(distinct) == 1:
            return distinct[0], "only one distinct deliverable passed the gates (no LLM judge needed)"
        ctx = self._ctx("select")
        ids = [f"c{n}" for n in range(1, len(distinct) + 1)]
        self.rng.shuffle(distinct)
        mapping = dict(zip(ids, distinct, strict=True))
        cdir = ctx / "context" / "candidates"
        cdir.mkdir(parents=True)
        for cid, p in mapping.items():
            (cdir / f"{cid}.patch").write_text(p.patch, encoding="utf-8")
            (cdir / f"{cid}.gates.md").write_text(p.gates.report(), encoding="utf-8")
        self.log(f"  ▸ blind select among {len(ids)} gate-passing deliverables ({self.cfg.role_cli('select')})")
        res = self._role("select", ctx, prompts.render("select", N=len(ids)))
        pick_id = _choice(res.text, ids)
        if pick_id is None:
            smallest = min(mapping.items(), key=lambda kv: len(kv[1].patch))
            return smallest[1], f"selector output unparseable; fell back to smallest passing patch ({smallest[0]})"
        why = re.search(r"<why>(.*?)</why>", res.text, re.S)
        return mapping[pick_id], (why.group(1).strip() if why else f"selector chose {pick_id}")

    def reflect(self, base_h: Path, probes: list[Probe], cands: list[Candidate], selected: Probe | None, why: str) -> Reflection:
        ctx = self._ctx("reflect")
        copy_harness(base_h, ctx / "context" / "base_harness")
        self._copy_rollouts(ctx, probes)
        for c in cands:
            cd = ctx / "context" / "candidates" / c.label
            copy_harness(c.harness, cd / "harness")
            (cd / "harness.diff").write_text(diff(base_h, c.harness)[0] or "(no change)\n", encoding="utf-8")
            (cd / "notes.md").write_text(c.notes + "\n", encoding="utf-8")
        passed = [p.label for p in probes if p.passed]
        (ctx / "context" / "selection.md").write_text(
            f"applied deliverable: {selected.label if selected else 'NONE (no rollout passed the gates)'}\n"
            f"reason: {why}\nrollouts that passed gates: {', '.join(passed) or 'none'}\n"
            f"rollouts that failed gates: {', '.join(p.label for p in probes if not p.passed) or 'none'}\n",
            encoding="utf-8",
        )
        self.log(f"  ▸ reflect ({self.cfg.role_cli('reflect')})")
        res = self._role("reflect", ctx, prompts.render("reflect"))
        return parse_reflection(res.text if res.ok else "")

    # ------------------------------------------------------------------ one contrastive step

    def step(self, k: int, base_h: Path, seed_probes: list[Probe], tag: str = "") -> tuple[list[Probe], list[Candidate]]:
        """One parallel Propose-Probe-Compose step of width k. Returns (all probes, all candidates)."""
        need = max(0, k - len(seed_probes))
        base = seed_probes + self._pmap(
            lambda i: self.probe(f"{tag}base-{i}", base_h), range(len(seed_probes) + 1, len(seed_probes) + need + 1)
        )
        if self.cfg.skip_when_base_passes and base and all(p.passed and p.verified for p in base):
            self.log("  ✓ every base rollout passed its gates — nothing to contrast, skipping proposals")
            return base, []
        jobs = [("inv", i) for i in range(1, k + 1)] + [("dom", i) for i in range(1, k + 1)]
        cands = self._pmap(lambda sj: self.propose(sj[0], sj[1], k, base_h, base), jobs)
        for c in cands:
            c.label = f"{tag}{c.label}"
        valid = self._dedupe([c for c in cands if c.valid and diff(base_h, c.harness)[1] > 0])
        cprobes = {p.label: p for p in self._pmap(lambda c: self.probe(c.label, c.harness), valid)}
        comps = self._pmap(lambda j: self.compose(j, k, base_h, base, valid, cprobes), range(1, k + 1))
        for c in comps:
            c.label = f"{tag}{c.label}"
        comps = self._dedupe(comps)
        # A composition identical to an already-probed harness needs no new execution.
        probed = {self._hkey(base_h): None, **{self._hkey(c.harness): c.label for c in valid}}
        to_probe = []
        for c in comps:
            if c.valid and self._hkey(c.harness) not in probed:
                probed[self._hkey(c.harness)] = c.label
                to_probe.append(c)
        compp = self._pmap(lambda c: self.probe(c.label, c.harness), to_probe)
        for c in comps:
            if c.valid and c not in to_probe:
                c.notes += f"\n(identical to already-probed harness {probed.get(self._hkey(c.harness)) or 'base'})"
        kept = [c for c in cands if c.valid and c in valid] + [c for c in cands if not c.valid]
        return base + list(cprobes.values()) + compp, kept + [c for c in comps if c in to_probe]

    def _dedupe(self, cands: list[Candidate]) -> list[Candidate]:
        """Identical candidate harnesses are one candidate: probe once, record the agreement."""
        seen: dict[str, Candidate] = {}
        out = []
        for c in cands:
            if not c.valid:
                out.append(c)
                continue
            key = self._hkey(c.harness)
            if key in seen:
                seen[key].notes += f"\n(independently proposed again, identically, by {c.label})"
                self.log(f"  = {c.label} is identical to {seen[key].label}; probing once")
                continue
            seen[key] = c
            out.append(c)
        return out

    @staticmethod
    def _hkey(h: Path) -> str:
        acc = hashlib.sha1()
        for f in sorted(p for p in h.rglob("*") if p.is_file()):
            acc.update(f.relative_to(h).as_posix().encode())
            acc.update(f.read_bytes())
        return acc.hexdigest()

    # ------------------------------------------------------------------ the task

    def run_task(
        self, task: str, k_override: int | None = None, mode: str | None = None, dry_run: bool = False, task_id: str | None = None
    ) -> Outcome:
        cfg = self.cfg
        st = load_state(self.root)
        k, reason = choose_k(st, cfg.schedule, cfg.max_k)
        if k_override is not None:
            k, reason = k_override, f"override k={k_override}"
        mode = mode or cfg.mode
        self.task = task.strip()
        self.task_id = task_id or new_task_id(task)
        if dry_run:
            per = (
                "1 execution, 0 role sessions (escalates to k=1 if the gates fail)"
                if k == 0
                else f"up to {4 * k} executions and {3 * k + 2} role sessions"
            )
            return Outcome(
                self.task_id, k, reason, False, False, False, message=f"would run k={k} ({reason}), mode={mode}: {per}"
            )

        cur_h = harness_dir(self.root)
        if not cur_h.is_dir():
            raise RuntimeError("no harness found — run `lithify init` first")
        hard = errors(validate(cur_h))
        if hard:
            raise RuntimeError("current harness fails validation:\n" + "\n".join(map(str, hard)))
        self.runs_dir = self.root / LITHIFY_DIR / "runs" / self.task_id
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.work = worktree.work_base(self.root) / self.task_id
        self.work.mkdir(parents=True, exist_ok=True)
        self.dirty = worktree.dirty_patch(self.root)
        if worktree.untracked(self.root):
            self.log("  ! untracked files are not copied into probe worktrees; commit or stage them if the task needs them")
        ensure_library(self.root)
        start_h = self.work / "harness-start"
        copy_harness(cur_h, start_h)  # freeze: the live harness may be promoted mid-way
        t0 = time.time()
        self.log(f"lithify ▸ {self.task_id}  k={k} ({reason}) mode={mode} executor={cfg.executor}")
        try:
            return self._run(k, reason, mode, start_h, st, t0)
        finally:
            if not self.keep:
                for wt in self._wts:
                    worktree.remove(self.root, wt)
                shutil.rmtree(self.work, ignore_errors=True)

    def _run(self, k: int, reason: str, mode: str, start_h: Path, st, t0: float) -> Outcome:
        probes: list[Probe] = []
        cands: list[Candidate] = []
        first_pass = False
        escalated_from_cruise = False

        if k == 0:
            # Labelled base-1 so that, if it escalates, it is read as the base rollout downstream.
            p = self.probe("base-1", start_h)
            probes.append(p)
            first_pass = p.passed and p.verified
            if p.passed:
                return self._finish(
                    k, reason, start_h, probes, cands, p, "cruise: gates passed on first execution", first_pass, t0, reflect=False
                )
            if not self.escalate:
                why = "cruise failed; escalation disabled" + self._save_for_review(probes)
                return self._finish(0, reason, start_h, probes, cands, None, why, first_pass, t0, reflect=False)
            self.log("  ! cruise execution failed its gates — escalating to k=1 on this task")
            k, reason, escalated_from_cruise = 1, reason + " → escalated", True

        # snapshot of the repo for role sessions that verify facts against source
        self.snapshot = self._new_wt("snapshot")

        seed = [probes[0]] if escalated_from_cruise else []
        if mode == "sequential" and k > 1:
            cur = start_h
            for r in range(1, k + 1):
                self.log(f"  — sequential round {r}/{k}")
                ps, cs = self.step(1, cur, seed if r == 1 else [], tag=f"r{r}-")
                probes += [p for p in ps if p not in probes]
                cands += cs
                comp = next((c for c in cs if c.scope == "comp" and c.valid), None)
                if comp is not None:
                    cur = comp.harness
        else:
            ps, cs = self.step(k, start_h, seed)
            probes += [p for p in ps if p not in probes]
            cands += cs

        base_label = probes[0].label
        if not escalated_from_cruise:
            first_pass = probes[0].passed and probes[0].verified
        self.log(f"  base rollout {base_label}: {'passed' if probes[0].passed else 'failed'} on first execution")

        passing = [p for p in probes if p.passed]
        if not passing:
            why = "no rollout passed the gates" + self._save_for_review(probes)
            return self._finish(k, reason, start_h, probes, cands, None, why, first_pass, t0, reflect=bool(cands))
        selected, why = self.select(passing)
        return self._finish(k, reason, start_h, probes, cands, selected, why, first_pass, t0, reflect=True)

    def _save_for_review(self, probes: list[Probe]) -> str:
        """A task whose correct fix changes behaviour an existing test pins can only pass by editing that
        test, which the gate forbids. Keep the work instead of discarding it: never applied, but saved
        for a human to review (or rerun with allow_test_edits = true)."""
        blocked = [p for p in probes if p.run.ok and p.patch.strip() and p.gates.blocked_only_by_test_edits]
        if not blocked:
            return ""
        best = min(blocked, key=lambda p: len(p.patch))
        path = self.runs_dir / "needs-review.patch"
        path.write_text(best.patch, encoding="utf-8")
        self.needs_review = str(path)
        return (
            f"; {len(blocked)} rollout(s) passed every command gate but changed existing tests "
            f"(allow_test_edits = false). The smallest, from {best.label}, is saved for review: {path}"
        )

    def _finish(
        self,
        k: int,
        reason: str,
        start_h: Path,
        probes: list[Probe],
        cands: list[Candidate],
        selected: Probe | None,
        why: str,
        first_pass: bool,
        t0: float,
        reflect: bool,
    ) -> Outcome:
        cfg = self.cfg
        out = Outcome(
            self.task_id,
            k,
            reason,
            delivered=selected is not None,
            applied=False,
            first_pass=first_pass,
            selected=selected.label if selected else "",
        )
        if selected is not None:
            ok, msg = worktree.apply_patch(self.root, selected.patch)
            out.applied = ok
            (self.runs_dir / "selected.patch").write_text(selected.patch, encoding="utf-8")
            self.log(
                f"  {'✓ applied' if ok else '✗ could not apply'} deliverable from {selected.label}: {why[:200]}"
                + ("" if ok else f" — patch saved to {self.runs_dir / 'selected.patch'} ({msg})")
            )
        adopted_h = selected.harness if selected is not None else start_h
        hdiff, churn, changed = diff(start_h, adopted_h)
        reflection = Reflection()
        if reflect and cands:
            reflection = self.reflect(start_h, probes, cands, selected, why)
            write_entry(self.root, self.task_id, self.task, reflection, adopted_h if changed else None, hdiff)
            self.log(
                f"  ✎ library: {'lesson recorded' if reflection.has_entry else 'NO_ENTRY'}; {len(reflection.rows)} edit row(s)"
            )

        live = harness_dir(self.root)
        if changed:
            to_promote = (changed & reflection.helped()) if cfg.auto_adopt else set()
            if to_promote:
                tmp = self.work / "promoted"
                promote(live, adopted_h, to_promote, tmp)
                if not errors(validate(tmp)):
                    copy_harness(tmp, live)
                    render(self.root)
                    out.promoted = sorted(to_promote)
                    self.log(f"  ⬆ promoted (evidence: helped): {', '.join(out.promoted)}")
            rest = changed - set(out.promoted)
            if rest:
                out.proposal = self._write_proposal(adopted_h, hdiff, rest, reflection)
                self.log(
                    f"  ⧗ proposal for review: {out.proposal.relative_to(self.root)} "
                    f"({', '.join(sorted(rest))}) — `lithify adopt {self.task_id}`"
                )

        always_on = estimate_tokens(always_on_text(live))
        rec = TaskRecord(
            task_id=self.task_id,
            k=k,
            first_pass=first_pass,
            delivered=out.delivered,
            churn_lines=churn,
            executions=int(self.usage["exec"]),
            tokens_in=int(self.usage["in"]),
            tokens_cached=int(self.usage["cached"]),
            tokens_out=int(self.usage["out"]),
            cost_usd=round(self.usage["cost"], 4),
            wall_s=round(time.time() - t0, 1),
            always_on_tokens=always_on,
        )
        st = record_task(self.root, load_state(self.root), rec, cfg.schedule)
        rec.stability_after = st.history[-1]["stability_after"]
        out.record = rec
        out.executions = int(self.usage["exec"])
        out.role_sessions = int(self.usage["roles"])
        out.message = why
        (self.runs_dir / "outcome.json").write_text(
            json.dumps(
                {
                    "task": self.task,
                    "k": k,
                    "reason": reason,
                    "selected": out.selected,
                    "why": why,
                    "applied": out.applied,
                    "first_pass": first_pass,
                    "promoted": out.promoted,
                    "needs_review": self.needs_review or None,
                    "proposal": str(out.proposal) if out.proposal else None,
                    "usage": self.usage,
                    "stability_after": rec.stability_after,
                    "probes": {p.label: {"passed": p.passed, "gates": p.gates.summary()} for p in probes},
                    "candidates": {c.label: {"valid": c.valid, "issues": c.issues[:5]} for c in cands},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.log(
            f"lithify ◂ delivered={out.delivered} first_pass={first_pass} "
            f"S={rec.stability_after:.2f} executions={out.executions} role_sessions={out.role_sessions} "
            f"tokens(in/cached/out)={self.usage['in']}/{self.usage['cached']}/{self.usage['out']}"
            + (f" cost=${self.usage['cost']:.2f}" if self.usage["cost"] else "")
        )
        return out

    def _write_proposal(self, adopted_h: Path, hdiff: str, keys: set[str], refl: Reflection) -> Path:
        pdir = self.root / LITHIFY_DIR / "proposals" / self.task_id
        copy_harness(adopted_h, pdir / "harness")
        (pdir / "harness.diff").write_text(hdiff, encoding="utf-8")
        rows = "\n".join(f"- `{r.component}`: **{r.verdict}** — {r.observed}" for r in refl.rows) or "- (no reflection)"
        (pdir / "PROPOSAL.md").write_text(
            f"# Harness proposal from {self.task_id}\n\nTask: {self.task[:300]}\n\n"
            f"Components changed: {', '.join(sorted(keys))}\n\n## Reflector verdicts\n\n{rows}\n\n"
            f"Review `harness.diff`, then `lithify adopt {self.task_id}` (all) or "
            f"`lithify adopt {self.task_id} --only <component>`; `lithify adopt --reject {self.task_id}` to drop.\n",
            encoding="utf-8",
        )
        (pdir / "keys.json").write_text(json.dumps(sorted(keys)), encoding="utf-8")
        return pdir
