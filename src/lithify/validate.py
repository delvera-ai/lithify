"""Zero-token structural validation of a harness.

Errors discard a candidate before it is ever probed (a probe is a full agent run, so
catching a broken skill here is the cheapest saving in the whole loop). Rules follow the
Harness² editor contract — skills need a trigger, named scripts must ship, scripts must
compile — plus checks that matter for a public tool: secrets, budget, evaluator leakage.
"""

from __future__ import annotations

import py_compile
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .harness import ALWAYS_ON, always_on_text, estimate_tokens, parse_frontmatter

KNOWN_TOP = set(ALWAYS_ON) | {"skills", "scripts", "subagents", "hooks", "README.md"}
SCRIPT_REF = re.compile(r"(?<![\w/])((?:[\w.-]+/)*scripts/[\w.-]+\.(?:py|sh|js|mjs|ts))")
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
LEAK = re.compile(r"\b(the grader (expects|wants)|rubric says|answer key)\b", re.I)
SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


@dataclass
class Issue:
    level: str  # "error" | "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.path}: {self.message}"


def _resolve_script(ref: str, base: Path, hdir: Path) -> bool:
    ref = ref.removeprefix("./")
    candidates = [base / ref, hdir / ref]
    if ref.startswith(".lithify/harness/"):
        candidates.append(hdir / ref.removeprefix(".lithify/harness/"))
    return any(c.is_file() for c in candidates)


def validate(hdir: Path, budget_tokens: int | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if not hdir.is_dir():
        return [Issue("error", str(hdir), "harness directory does not exist")]

    for p in hdir.iterdir():
        if p.name.startswith(".") or p.name in KNOWN_TOP:
            continue
        issues.append(Issue("warning", p.name, "unknown top-level entry; it will not be rendered"))

    # text scans across every file
    for f in sorted(hdir.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(hdir).as_posix()
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append(Issue("warning", rel, "binary file in harness"))
            continue
        if SECRET.search(text):
            issues.append(Issue("error", rel, "looks like it contains a credential; never store secrets in the harness"))
        if LEAK.search(text):
            issues.append(Issue("warning", rel, "references a grader/rubric; the harness must describe work, not scoring"))
        if f.suffix == ".py":
            with tempfile.TemporaryDirectory() as td:
                try:
                    py_compile.compile(str(f), cfile=str(Path(td) / "x.pyc"), doraise=True)
                except py_compile.PyCompileError as e:
                    issues.append(Issue("error", rel, f"script does not compile: {e.msg.strip().splitlines()[-1]}"))

    # skills: frontmatter, trigger description, shipped helpers
    sdir = hdir / "skills"
    if sdir.is_dir():
        for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
            rel = f"skills/{d.name}"
            f = d / "SKILL.md"
            if not f.exists():
                issues.append(Issue("error", rel, "skill directory without SKILL.md"))
                continue
            text = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            if fm.get("name") != d.name:
                issues.append(Issue("error", rel, f"frontmatter name {fm.get('name')!r} must equal directory name {d.name!r}"))
            if not SKILL_NAME.match(d.name):
                issues.append(Issue("error", rel, "skill name must be lowercase letters, digits and hyphens"))
            desc = fm.get("description", "")
            if len(desc) < 20:
                issues.append(Issue("error", rel, "description is the skill's trigger: say WHEN to load it (>= 20 chars)"))
            for ref in SCRIPT_REF.findall(text):
                if not _resolve_script(ref, d, hdir):
                    issues.append(Issue("error", rel, f"invokes {ref} but that file does not ship with the harness"))

    # subagents
    adir = hdir / "subagents"
    if adir.is_dir():
        for d in sorted(p for p in adir.iterdir() if p.is_dir()):
            f = d / "AGENT.md"
            if not f.exists():
                issues.append(Issue("error", f"subagents/{d.name}", "subagent directory without AGENT.md"))
                continue
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            if not fm.get("description"):
                issues.append(Issue("error", f"subagents/{d.name}", "AGENT.md needs a `description:` in frontmatter"))
            if fm.get("name") and fm["name"] != d.name:
                issues.append(Issue("error", f"subagents/{d.name}", "frontmatter name must equal directory name"))

    # scripts referenced from always-on text
    for fname in ALWAYS_ON:
        f = hdir / fname
        if f.exists():
            for ref in SCRIPT_REF.findall(f.read_text(encoding="utf-8")):
                if not _resolve_script(ref, hdir, hdir):
                    issues.append(Issue("error", fname, f"references {ref} but that file does not ship with the harness"))

    if (hdir / "hooks").exists():
        issues.append(Issue("warning", "hooks", "C8 middleware is stored but not rendered into CLIs in v0"))

    if budget_tokens:
        tokens = estimate_tokens(always_on_text(hdir))
        if tokens > budget_tokens:
            issues.append(
                Issue(
                    "warning",
                    "always-on",
                    f"~{tokens} always-on tokens exceeds budget {budget_tokens}; run `lithify compact`",
                )
            )
    return issues


def errors(issues: list[Issue]) -> list[Issue]:
    return [i for i in issues if i.level == "error"]
