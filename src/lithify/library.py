"""Harnessing-level recursion: the improvement library.

    .lithify/library/
      INDEX.md                         one line per entry (cue -> lesson), newest first
      <task-id>/EXPERIENCE.md          edit attribution rows + at most one transferable lesson
      <task-id>/harness/               the adopted harness snapshot (executable, not summarised)
      <task-id>/harness.diff           its diff against the harness the task started from

Lessons are retained only when supported by execution contrasts; NO_ENTRY is recorded
as such, and the index skips it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import LITHIFY_DIR
from .harness import copy_harness

LIBRARY_DIR = "library"
VERDICTS = ("helped", "hurt", "no observed effect", "confounded")


@dataclass
class EditRow:
    component: str
    candidates: str = ""
    change: str = ""
    observed: str = ""
    verdict: str = "confounded"


@dataclass
class Reflection:
    rows: list[EditRow] = field(default_factory=list)
    cue: str = ""
    lesson: str = ""
    evidence: str = ""
    confidence: str = ""
    raw: str = ""

    @property
    def has_entry(self) -> bool:
        return bool(self.lesson.strip())

    def helped(self) -> set[str]:
        return {r.component for r in self.rows if r.verdict == "helped"}


def library_dir(root: Path) -> Path:
    return root / LITHIFY_DIR / LIBRARY_DIR


def _block(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.S)
    return m.group(1).strip() if m else ""


def parse_reflection(text: str) -> Reflection:
    ref = Reflection(raw=text)
    edits = _block(text, "edits")
    cur: dict[str, str] = {}

    def flush() -> None:
        if cur.get("component"):
            v = cur.get("verdict", "confounded").lower().strip()
            v = next((x for x in VERDICTS if v.startswith(x)), "confounded")
            ref.rows.append(
                EditRow(
                    component=cur["component"].strip("` "),
                    candidates=cur.get("candidates", ""),
                    change=cur.get("change", ""),
                    observed=cur.get("observed", ""),
                    verdict=v,
                )
            )
        cur.clear()

    for line in edits.splitlines():
        line = line.strip()
        if not line:
            flush()
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip().lower()
            if k == "component" and cur.get("component"):
                flush()  # next row without a blank separator
            cur[k] = v.strip()
    flush()
    exp = _block(text, "experience")
    if exp and "NO_ENTRY" not in exp:
        fields: dict[str, str] = {}
        key = None
        for line in exp.splitlines():
            m = re.match(r"\s*(cue|lesson|evidence|confidence)\s*:\s*(.*)", line, re.I)
            if m:
                key = m.group(1).lower()
                fields[key] = m.group(2).strip()
            elif key and line.strip():
                fields[key] += " " + line.strip()
        ref.cue = fields.get("cue", "")
        ref.lesson = fields.get("lesson", "")
        ref.evidence = fields.get("evidence", "")
        ref.confidence = fields.get("confidence", "")
    return ref


def write_entry(
    root: Path, task_id: str, task: str, reflection: Reflection, adopted_harness: Path | None, harness_diff: str
) -> Path:
    lib = library_dir(root)
    entry = lib / task_id
    entry.mkdir(parents=True, exist_ok=True)
    if adopted_harness is not None and adopted_harness.exists():
        copy_harness(adopted_harness, entry / "harness")
    (entry / "harness.diff").write_text(harness_diff or "(no harness change)\n", encoding="utf-8")
    rows = (
        "\n".join(f"| `{r.component}` | {r.verdict} | {r.change} | {r.observed} |" for r in reflection.rows)
        or "| — | — | no harness edits were proposed | — |"
    )
    lesson = (
        f"- **cue:** {reflection.cue}\n- **lesson:** {reflection.lesson}\n"
        f"- **evidence:** {reflection.evidence}\n- **confidence:** {reflection.confidence}\n"
        if reflection.has_entry
        else "NO_ENTRY — the record showed no reusable execution contrast.\n"
    )
    (entry / "EXPERIENCE.md").write_text(
        f"# {task_id}\n\n**Task:** {task.strip()[:500]}\n\n## Transferable lesson\n\n{lesson}\n"
        f"## Edit attribution\n\n| component | verdict | change | observed |\n|---|---|---|---|\n{rows}\n",
        encoding="utf-8",
    )
    _update_index(lib)
    return entry


def _update_index(lib: Path) -> None:
    lines = [
        "# lithify improvement library",
        "",
        "Each entry: what situation a lesson applies to, and the harness operation that helped.",
        "Read an entry's EXPERIENCE.md and harness/ before reusing a component.",
        "",
    ]
    entries = sorted((d for d in lib.iterdir() if (d / "EXPERIENCE.md").exists()), reverse=True)
    for d in entries:
        text = (d / "EXPERIENCE.md").read_text(encoding="utf-8")
        cue = re.search(r"\*\*cue:\*\* (.*)", text)
        lesson = re.search(r"\*\*lesson:\*\* (.*)", text)
        if cue and lesson:
            lines.append(
                f"- [{d.name}]({d.name}/EXPERIENCE.md) — **when** {cue.group(1).strip()} **then** {lesson.group(1).strip()}"
            )
    (lib / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_library(root: Path) -> Path:
    lib = library_dir(root)
    lib.mkdir(parents=True, exist_ok=True)
    if not (lib / "INDEX.md").exists():
        _update_index(lib)
    return lib
