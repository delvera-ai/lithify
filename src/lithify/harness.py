"""The execution harness: eight file-backed components, one canonical directory.

    .lithify/harness/
      system.md              C1 system prompt        always on
      guardrails.md          C2 guardrails           always on
      memory.md              C3 durable memory       always on
      tool_guidance.md       C4 tool guidance        always on
      subagents/<n>/AGENT.md C5 subagents            delegated context
      skills/<n>/SKILL.md    C6 skills               on demand
      scripts/<file>         C7 scripts              run via shell
      hooks/                 C8 middleware (experimental, not rendered in v0)

`render()` projects the canonical harness into each CLI's native discovery paths:
CLAUDE.md + AGENTS.md (managed block), .claude/skills, .agents/skills, .claude/agents.
Copies, not symlinks: Claude Code writes internal files into its skills directory.
"""

from __future__ import annotations

import difflib
import hashlib
import re
import shutil
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from .config import LITHIFY_DIR

HARNESS_DIR = "harness"
ALWAYS_ON = ("system.md", "guardrails.md", "memory.md", "tool_guidance.md")
ALWAYS_ON_TITLES = {
    "system.md": "Role and procedure",
    "guardrails.md": "Guardrails",
    "memory.md": "Durable project memory",
    "tool_guidance.md": "Tool guidance",
}
BEGIN = "<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->"
END = "<!-- lithify:end -->"
MANAGED_MARKER = ".lithify-managed"
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")
SKILL_TARGETS = (".claude/skills", ".agents/skills")
CLAUDE_AGENTS = ".claude/agents"
# Paths the harness renders into a repo. Excluded from task deliverable diffs. Only the rendered
# subpaths: other files under .claude/ or .agents/ (settings, plugin manifests) are real sources.
RENDERED_PATHS = ("CLAUDE.md", "AGENTS.md", *SKILL_TARGETS, CLAUDE_AGENTS, LITHIFY_DIR)

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def harness_dir(root: Path) -> Path:
    return root / LITHIFY_DIR / HARNESS_DIR


def harness_hash(hdir: Path) -> str:
    """SHA-256 over the harness files: sorted relative paths, each followed by its bytes.

    Stable across machines for the same content. __pycache__ is skipped, as validate() skips it.
    """
    digest = hashlib.sha256()
    for f in sorted(p for p in hdir.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(f.relative_to(hdir).as_posix().encode("utf-8") + b"\0")
        digest.update(f.read_bytes() + b"\0")
    return digest.hexdigest()


def parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER.sub("", text, count=1)


@dataclass
class Skill:
    name: str
    description: str
    path: Path


def list_skills(hdir: Path) -> list[Skill]:
    out: list[Skill] = []
    sdir = hdir / "skills"
    if not sdir.is_dir():
        return out
    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if f.exists():
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            out.append(Skill(fm.get("name", ""), fm.get("description", ""), d))
    return out


def list_subagents(hdir: Path) -> list[Skill]:
    out: list[Skill] = []
    sdir = hdir / "subagents"
    if not sdir.is_dir():
        return out
    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        f = d / "AGENT.md"
        if f.exists():
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            out.append(Skill(fm.get("name", d.name), fm.get("description", ""), d))
    return out


def always_on_text(hdir: Path) -> str:
    parts: list[str] = ["## Project harness (lithify)"]
    for fname in ALWAYS_ON:
        f = hdir / fname
        if f.exists():
            body = f.read_text(encoding="utf-8").strip()
            if body:
                parts.append(f"### {ALWAYS_ON_TITLES[fname]}\n\n{body}")
    skills = list_skills(hdir)
    if skills:
        lines = [f"- `{s.name}` — {s.description}" for s in skills]
        parts.append("### Skills (load on demand)\n\n" + "\n".join(lines))
    subs = list_subagents(hdir)
    if subs:
        lines = [f"- `{s.name}` — {s.description} (brief: `.lithify/harness/subagents/{s.path.name}/AGENT.md`)" for s in subs]
        parts.append("### Subagents\n\n" + "\n".join(lines))
    sc = hdir / "scripts"
    if sc.is_dir():
        files = sorted(p.name for p in sc.iterdir() if p.is_file())
        if files:
            lines = [f"- `.lithify/harness/scripts/{n}`" for n in files]
            parts.append("### Helper scripts\n\n" + "\n".join(lines))
    return "\n\n".join(parts) + "\n"


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def _write_managed_block(path: Path, block: str) -> None:
    managed = f"{BEGIN}\n{block.rstrip()}\n{END}\n"
    if path.exists():
        cur = path.read_text(encoding="utf-8")
        if BEGIN in cur and END in cur:
            pre, rest = cur.split(BEGIN, 1)
            _, post = rest.split(END, 1)
            new = pre + managed + post.lstrip("\n")
        else:
            new = cur.rstrip() + "\n\n" + managed
    else:
        new = managed
    path.write_text(new, encoding="utf-8")


_MD_MARKER = f"<!-- {MANAGED_MARKER} -->"


def _is_managed(p: Path) -> bool:
    if p.is_dir():
        return (p / MANAGED_MARKER).exists()
    if p.suffix == ".md":
        head = p.read_text(encoding="utf-8")[:4000]
        return _MD_MARKER in head
    return False


def _sync_dirs(src_items: dict[str, Path], target: Path, file_name: str | None = None) -> None:
    """Mirror src_items into target, only touching entries lithify manages.

    file_name=None copies whole directories (skills); otherwise each item's `file_name`
    is written as `<name>.md` (Claude Code subagents).
    """
    target.mkdir(parents=True, exist_ok=True)
    for existing in list(target.iterdir()):
        if _is_managed(existing) and existing.name.removesuffix(".md") not in src_items:
            if existing.is_dir():
                shutil.rmtree(existing)
            else:
                existing.unlink()
    for name, src in src_items.items():
        if file_name is None:
            dst = target / name
            if dst.exists() and not _is_managed(dst):
                continue  # user-owned entry with the same name: never overwrite
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            (dst / MANAGED_MARKER).write_text("managed by lithify sync\n", encoding="utf-8")
        else:
            dst = target / f"{name}.md"
            if dst.exists() and not _is_managed(dst):
                continue
            body = (src / file_name).read_text(encoding="utf-8")
            m = _FRONTMATTER.match(body)  # frontmatter must stay first; marker goes after it
            cut = m.end() if m else 0
            dst.write_text(body[:cut] + _MD_MARKER + "\n" + body[cut:], encoding="utf-8")


def _bullet_id(fname: str, line: str) -> str:
    return f"{fname}#{hashlib.sha256(line.strip().encode('utf-8')).hexdigest()[:8]}"


def always_on_rules(hdir: Path) -> dict[str, str]:
    """Stable ids for the always-on bullets: `<file>#<hash of the bullet>` -> bullet text.

    An id changes only when its bullet's text changes, so a rollout can name the rules it had.
    """
    rules: dict[str, str] = {}
    for fname in ALWAYS_ON:
        f = hdir / fname
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.lstrip().startswith("- "):
                    rules[_bullet_id(fname, line)] = line.strip()
    return rules


def drop_component(hdir: Path, component: str) -> str:
    """Remove one component from `hdir` in place. `rule:<id>` drops an always-on bullet, `skill:<name>` a skill.

    Returns a description of what was removed.
    """
    kind, _, key = component.partition(":")
    if kind == "rule":
        for fname in ALWAYS_ON:
            f = hdir / fname
            if not f.exists():
                continue
            lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [ln for ln in lines if not (ln.lstrip().startswith("- ") and _bullet_id(fname, ln) == key)]
            if len(kept) != len(lines):
                f.write_text("".join(kept), encoding="utf-8")
                return f"rule {key} ({fname})"
        raise ValueError(f"no always-on rule {key!r} in {hdir}")
    if kind == "skill":
        d = hdir / "skills" / key
        if not d.is_dir():
            raise ValueError(f"no skill {key!r} in {hdir}")
        shutil.rmtree(d)
        return f"skill {key}"
    raise ValueError(f"component must be rule:<id> or skill:<name>, got {component!r}")


def classify_read(target: str, wt: Path) -> str:
    """Name what a rollout opened: `skill:<name>`, `instructions:<file>`, `subagent:<name>`, `lithify:<path>`
    or `file:<path>`. `target` is a Read file path (absolute, inside the probe worktree) or a `skill:<name>`."""
    if target.startswith("skill:"):
        return target
    rel = target
    with suppress(ValueError):  # outside the worktree: keep the absolute path
        rel = Path(target).resolve().relative_to(wt.resolve()).as_posix()
    if rel in INSTRUCTION_FILES:
        return f"instructions:{rel}"
    for prefix, kind in ((".claude/skills/", "skill"), (".agents/skills/", "skill"), (".claude/agents/", "subagent")):
        if rel.startswith(prefix):
            return f"{kind}:{rel[len(prefix) :].split('/', 1)[0]}"
    if rel.startswith(f"{LITHIFY_DIR}/"):
        return f"lithify:{rel}"
    return f"file:{rel}"


def render(root: Path, hdir: Path | None = None) -> dict[str, int]:
    """Project the harness into CLI discovery paths under `root`. Returns stats."""
    hdir = hdir or harness_dir(root)
    block = always_on_text(hdir)
    for fname in INSTRUCTION_FILES:
        _write_managed_block(root / fname, block)
    skills = {s.path.name: s.path for s in list_skills(hdir)}
    for t in SKILL_TARGETS:
        _sync_dirs(skills, root / t)
    subs = {s.path.name: s.path for s in list_subagents(hdir)}
    if subs or (root / CLAUDE_AGENTS).exists():
        _sync_dirs(subs, root / CLAUDE_AGENTS, file_name="AGENT.md")
    return {"always_on_tokens": estimate_tokens(block), "skills": len(skills), "subagents": len(subs)}


# ---------------------------------------------------------------- components & diffs


def component_key(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] in ("skills", "subagents") and len(parts) > 1:
        return f"{parts[0]}/{parts[1]}"
    if parts[0] == "scripts" and len(parts) > 1:
        return f"scripts/{parts[1]}"
    if parts[0] == "hooks":
        return "hooks"
    return rel


def _files(d: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not d.is_dir():
        return out
    for p in sorted(d.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.name != MANAGED_MARKER:
            try:
                out[p.relative_to(d).as_posix()] = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                out[p.relative_to(d).as_posix()] = f"<binary {p.stat().st_size} bytes>"
    return out


def diff(a: Path, b: Path) -> tuple[str, int, set[str]]:
    """Unified diff a->b, changed line count, and changed component keys."""
    fa, fb = _files(a), _files(b)
    chunks: list[str] = []
    churn = 0
    changed: set[str] = set()
    for rel in sorted(set(fa) | set(fb)):
        x, y = fa.get(rel, ""), fb.get(rel, "")
        if x == y:
            continue
        changed.add(component_key(rel))
        lines = list(
            difflib.unified_diff(
                x.splitlines(keepends=True),
                y.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
        churn += sum(1 for ln in lines if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
        chunks.append("".join(lines))
    return "\n".join(chunks), churn, changed


def copy_harness(src: Path, dst: Path) -> Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", MANAGED_MARKER))
    return dst


def promote(current: Path, adopted: Path, keys: set[str], out: Path) -> Path:
    """Build `out` = current harness with the given component keys taken from `adopted`."""
    copy_harness(current, out)
    fa = _files(adopted)
    fc = _files(current)
    for rel in set(fa) | set(fc):
        if component_key(rel) not in keys:
            continue
        target = out / rel
        if rel in fa:
            target.parent.mkdir(parents=True, exist_ok=True)
            src = adopted / rel
            shutil.copy2(src, target)
        elif target.exists():
            target.unlink()
    # prune empty dirs left by deletions
    for d in sorted((p for p in out.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    return out
