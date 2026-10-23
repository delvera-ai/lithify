"""A deterministic stand-in for an LLM coding agent, for tests and `lithify demo`.

The simulated world (see demo.py for the fixture repository):

* The executor implements `feature <name>` by writing features/<name>.py with a
  `# uses:` line listing every convention it knows. It knows a convention when the
  convention's backticked token appears in its always-on instructions (CLAUDE.md) or in a
  skill whose description mentions the task's area. It cannot read the hidden checks.
* If the always-on text tells it to run the project's test command, it does so once and
  fixes the FIRST missing convention the checks report (bounded self-correction).
* The DOM proposer turns failing-check messages into maintainer rules — area-specific
  ones into an on-demand skill, global ones into guardrails.md. The INV proposer adds a
  verify-before-finishing procedure. The composer merges candidates whose probes improved
  on the base; the selector prefers the smallest passing patch; the reflector marks an
  edit `helped` only when the improved rollout's trajectory shows that component in use.

Everything except the "model" is real: worktrees, rendering, gates, validation, diffs,
library, promotion and the k schedule all run exactly as they do with real CLIs.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
import time
from pathlib import Path
from typing import ClassVar

from .base import Adapter, RunResult

TOKEN = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")
MISSING = re.compile(r"missing `([A-Za-z_][A-Za-z0-9_.]*)` — (.+)")
SECTION_FILE = {
    "Role and procedure": "system.md",
    "Guardrails": "guardrails.md",
    "Durable project memory": "memory.md",
    "Tool guidance": "tool_guidance.md",
}
VERIFY_RULE = (
    "Before finishing, run the project's test command (`python3 tests/check.py`), read every "
    "failure, and fix the code; a written file is not evidence that the change works."
)
AREAS = {"api": "API", "db": "database", "reports": "report", "billing": "billing"}


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


class MockAdapter(Adapter):
    name = "mock"
    binary = "mock"
    default_args: ClassVar[list[str]] = []

    def available(self) -> bool:
        return True

    def version(self) -> str:
        return "mock (simulated agent)"

    def run(self, prompt: str, cwd: Path, timeout_s: int = 1800, role: str = "execute") -> RunResult:
        t0 = time.time()
        fn = getattr(self, f"_{role}", None)
        if fn is None:
            return RunResult(ok=False, error=f"mock has no role {role}")
        res: RunResult = fn(prompt, cwd)
        res.seconds = time.time() - t0
        res.meta["role"] = role
        return res

    # ------------------------------------------------------------------ executor

    def _execute(self, prompt: str, cwd: Path) -> RunResult:
        m = re.search(r"feature `([a-z_]+)`", prompt)
        if not m:
            return RunResult(ok=True, text="nothing to do", transcript="[assistant] no feature named")
        feat = m.group(1)
        am = re.search(r"\[area: (\w+)\]", prompt)
        area = am.group(1) if am else ""
        claude_md = _read(cwd / "CLAUDE.md")
        events: list[str] = ["[tool_use Read] CLAUDE.md"]
        known: dict[str, str] = {}
        section = ""
        for line in claude_md.splitlines():
            if line.startswith("### "):
                section = SECTION_FILE.get(line[4:].strip(), "")
                continue
            if section in ("guardrails.md", "memory.md", "system.md", "tool_guidance.md"):
                for tok in TOKEN.findall(line):
                    if tok.startswith("python3"):
                        continue
                    known.setdefault(tok, section)
        sdir = cwd / ".claude" / "skills"
        if sdir.is_dir() and area:
            for skill in sorted(sdir.iterdir()):
                text = _read(skill / "SKILL.md")
                desc = re.search(r"description:\s*(.*)", text)
                if desc and area in desc.group(1):
                    events.append(f"[tool_use Skill] loaded skill {skill.name}")
                    for tok in TOKEN.findall(text.split("---", 2)[-1]):
                        known.setdefault(tok, f"skills/{skill.name}")
        noise = float(os.environ.get("LITHIFY_MOCK_NOISE", "0") or 0)
        if noise and known:
            rng = random.Random(f"{cwd.name}:{feat}")
            if rng.random() < noise:
                dropped = rng.choice(sorted(known))
                known.pop(dropped)
                events.append(f"[assistant] (overlooked `{dropped}`)")
        turns = 4

        def write() -> None:
            (cwd / "features").mkdir(exist_ok=True)
            uses = ", ".join(sorted(known))
            (cwd / "features" / f"{feat}.py").write_text(
                f"# feature: {feat}\n# uses: {uses}\n\n\ndef {feat}():\n    raise NotImplementedError\n", encoding="utf-8"
            )

        write()
        events.append(f"[tool_use Write] features/{feat}.py")
        for tok, src in sorted(known.items()):
            events.append(f"[assistant] applied `{tok}` from {src}")
        if "run the project's test command" in claude_md and (cwd / "tests" / "check.py").exists():
            turns += 3
            out = subprocess.run(["python3", "tests/check.py"], cwd=cwd, capture_output=True, text=True)
            events.append(f"[tool_use Bash] python3 tests/check.py -> exit {out.returncode}")
            mine = "\n".join(ln for ln in out.stdout.splitlines() if ln.startswith(f"FAIL {feat}:"))
            miss = MISSING.findall(mine)
            if miss:
                tok = miss[0][0]
                known[tok] = "self-check (tool_guidance via system.md procedure)"
                events.append(f"[assistant] test output says `{tok}` is missing; fixing (procedure from system.md)")
                write()
        size = len(claude_md) // 4
        return RunResult(
            ok=True,
            text=f"Implemented feature {feat}.",
            transcript="\n".join(events),
            tokens_in=turns * (3000 + size),
            tokens_cached=0,
            tokens_out=turns * 150,
        )

    # ------------------------------------------------------------------ editors

    def _rollout_failures(self, ctx: Path) -> list[tuple[str, str, str]]:
        out = []
        for g in sorted((ctx / "context" / "rollouts").glob("*/gates.md")):
            for tok, msg in MISSING.findall(_read(g)):
                out.append((g.parent.name, tok, msg.strip()))
        return out

    def _area(self, ctx: Path) -> str:
        m = re.search(r"\[area: (\w+)\]", _read(ctx / "context" / "task.md"))
        return m.group(1) if m else ""

    def _propose_inv(self, prompt: str, ctx: Path) -> RunResult:
        h = ctx / "context" / "harness"
        sysmd = h / "system.md"
        cur = _read(sysmd)
        fails = self._rollout_failures(ctx)
        if not fails or "run the project's test command" in cur:
            return RunResult(
                ok=True, text="<notes>KEEP_BASE — no procedural divergence observed</notes>", tokens_in=7000, tokens_out=400
            )
        sysmd.write_text(cur.rstrip() + "\n\n" + VERIFY_RULE + "\n", encoding="utf-8")
        rl = fails[0][0]
        return RunResult(
            ok=True,
            text=f"<notes>system.md: verify-before-finishing — rollout {rl} wrote "
            "the file and stopped without running the tests</notes>",
            tokens_in=9000,
            tokens_out=900,
        )

    def _propose_dom(self, prompt: str, ctx: Path) -> RunResult:
        h = ctx / "context" / "harness"
        area = self._area(ctx)
        fails = self._rollout_failures(ctx)
        if not fails:
            return RunResult(ok=True, text="<notes>KEEP_BASE</notes>", tokens_in=7000, tokens_out=300)
        notes = []
        seen: set[str] = set()
        for label, tok, msg in fails:
            if tok in seen:
                continue
            seen.add(tok)
            rule = f"- {msg} (`{tok}`)"
            area_word = AREAS.get(area, "~")
            if area and area_word.lower() in msg.lower():
                sk = h / "skills" / f"{area}-conventions"
                sk.mkdir(parents=True, exist_ok=True)
                f = sk / "SKILL.md"
                body = _read(f) or (
                    f"---\nname: {area}-conventions\ndescription: Use when a task touches the {area} area; "
                    f"conventions every {area} change in this repository must follow.\n---\n\n"
                    f"# {area} conventions\n\n"
                )
                if rule not in body:
                    f.write_text(body.rstrip() + "\n" + rule + "\n", encoding="utf-8")
                notes.append(f"skills/{area}-conventions: {tok} — missing in {label}")
            else:
                g = h / "guardrails.md"
                cur = _read(g)
                if rule not in cur:
                    g.write_text(cur.rstrip() + ("\n" if cur.strip() else "") + rule + "\n", encoding="utf-8")
                notes.append(f"guardrails.md: {tok} — missing in {label}")
        return RunResult(ok=True, text="<notes>\n" + "\n".join(notes) + "\n</notes>", tokens_in=11000, tokens_out=1200)

    def _compose(self, prompt: str, ctx: Path) -> RunResult:
        c = ctx / "context"
        base_missing = min((len(MISSING.findall(_read(g))) for g in (c / "rollouts").glob("*base-*/gates.md")), default=0)
        notes = []
        for cand in sorted((c / "candidates").glob("*")):
            g = c / "rollouts" / cand.name / "gates.md"
            missing = len(MISSING.findall(_read(g)))
            if not g.exists() or (missing >= base_missing and "GATES: PASS" not in _read(g)):
                notes.append(f"dropped -> {cand.name} -> rollout did not improve on base ({missing} vs {base_missing})")
                continue
            for f in sorted((cand / "harness").rglob("*")):
                if not f.is_file():
                    continue
                rel = f.relative_to(cand / "harness")
                tgt = c / "harness" / rel
                tgt.parent.mkdir(parents=True, exist_ok=True)
                cur = _read(tgt)
                lines = cur.splitlines()
                new = [ln for ln in _read(f).splitlines() if ln.strip() and ln not in lines]
                if not cur:
                    tgt.write_text(_read(f), encoding="utf-8")
                elif new:
                    tgt.write_text(cur.rstrip() + "\n" + "\n".join(new) + "\n", encoding="utf-8")
            notes.append(f"kept -> {cand.name} -> rollout missing {missing} vs base {base_missing}")
        return RunResult(ok=True, text="<notes>\n" + "\n".join(notes) + "\n</notes>", tokens_in=14000, tokens_out=1500)

    def _compact(self, prompt: str, ctx: Path) -> RunResult:
        h = ctx / "context" / "harness"
        for name in ("system.md", "guardrails.md", "memory.md", "tool_guidance.md"):
            f = h / name
            if f.exists():
                seen, out = set(), []
                for ln in _read(f).splitlines():
                    if ln.strip() and ln in seen:
                        continue
                    seen.add(ln)
                    out.append(ln)
                f.write_text("\n".join(out) + "\n", encoding="utf-8")
        return RunResult(ok=True, text="<notes>deduplicated always-on rules</notes>", tokens_in=8000, tokens_out=600)

    # ------------------------------------------------------------------ judges

    def _select(self, prompt: str, ctx: Path) -> RunResult:
        pats = sorted((ctx / "context" / "candidates").glob("*.patch"))
        best = min(pats, key=lambda p: (len(_read(p)), p.name))
        cid = best.stem
        return RunResult(
            ok=True,
            text=f"<why>\nSCOPE: smallest change that does exactly what was asked.\n</why>\n```choice\n{cid}\n```",
            tokens_in=9000,
            tokens_out=300,
        )

    def _reflect(self, prompt: str, ctx: Path) -> RunResult:
        c = ctx / "context"
        base_missing = min((len(MISSING.findall(_read(g))) for g in (c / "rollouts").glob("*base-*/gates.md")), default=0)
        rows = []
        helped_any = []
        for cand in sorted((c / "candidates").glob("*")):
            dtext = _read(cand / "harness.diff")
            comps = sorted({_ckey(m) for m in re.findall(r"^\+\+\+ b/(\S+)", dtext, re.M)})
            if not comps:
                continue
            traj = _read(c / "rollouts" / cand.name / "trajectory.md")
            g = _read(c / "rollouts" / cand.name / "gates.md")
            missing = len(MISSING.findall(g))
            improved = bool(g) and (missing < base_missing or ("GATES: PASS" in g and base_missing > 0))
            for comp in comps:
                if not g:
                    verdict, obs = "confounded", "candidate was not probed"
                elif not improved:
                    verdict, obs = (
                        "hurt" if missing > base_missing else "no observed effect",
                        f"{cand.name} missing {missing} vs base {base_missing}",
                    )
                elif comp in traj or (comp == "system.md" and "procedure from system.md" in traj):
                    verdict, obs = "helped", f"{cand.name} trajectory applies {comp}; missing {missing} vs base {base_missing}"
                    helped_any.append(comp)
                else:
                    verdict, obs = "confounded", f"{cand.name} improved but trajectory does not show {comp} in use"
                rows.append(
                    f"component: {comp}\ncandidates: {cand.name}\nchange: edited {comp}\nobserved: {obs}\nverdict: {verdict}\n"
                )
        area = self._area(ctx)
        if helped_any:
            skill = next((h for h in helped_any if h.startswith("skills/")), None)
            exp = (
                f"<experience>\ncue: a task in this repository touches the {area or 'shared'} area and the "
                f"agent misses a project convention\nlesson: encode area-specific conventions in "
                f"{skill or 'guardrails.md'} as backticked, checkable rules, and keep a verify-before-finishing "
                f"step in system.md\nevidence: rows marked helped ({', '.join(sorted(set(helped_any)))})\n"
                f"confidence: medium — single rollout per candidate\n</experience>"
            )
        else:
            exp = "NO_ENTRY"
        return RunResult(ok=True, text="<edits>\n" + "\n".join(rows) + "</edits>\n" + exp, tokens_in=12000, tokens_out=1400)


def _ckey(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] in ("skills", "subagents", "scripts") and len(parts) > 1:
        return f"{parts[0]}/{parts[1]}"
    return rel
