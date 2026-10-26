"""Draft redacted task texts from PR sources; every draft is then reviewed and edited by hand.

    python eval/draft_tasks.py sqlglot     # writes eval/prs/sqlglot/drafts/<n>.md

Drafting keeps what a user-facing issue would say: the title as a request, the linked issue's
text and the example SQL in it. It drops what gives the implementation away: sections such as
Changes / Fix / Root cause / Implementation / Validation / Test plan, lines naming source or test
files, images, tool trailers. Expected outputs are not added. The hand review (tasks/) removes
anything left that the hidden tests alone would reveal, and states the dialect and API involved.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parent
DROP_SECTION = re.compile(
    r"^#+\s*(changes( done| proposed)?|summary of changes|fix|the fix|root cause|cause|implementation|"
    r"validation|tests?|test plan|testing|checklist|notes? for reviewers?|screenshots?|description of changes)\b",
    re.I,
)
DROP_LINE = re.compile(
    r"(sqlglot/[\w/]+\.py|tests?/[\w/.]+|`[\w/]+\.py`|pytest|<img|!\[|Co-Authored-By|Generated with \[Claude|"
    r"^\s*[-*]\s*\[[ x]\]|\bDOCS\b|^\s*\*\*DOCS\*\*)",
    re.I,
)
TITLE = re.compile(r"^(feat|fix|chore|refactor|perf)(\(([^)]*)\))?!?:\s*", re.I)


INLINE_LABEL = re.compile(r"^\s*\*\*(root cause|cause|fix|the fix|changes|implementation|validation)\b", re.I)


def clean(md: str) -> str:
    """Drop implementation sections (until the next heading) and inline-labelled implementation
    paragraphs (until the next blank line), plus lines naming files, images and tool trailers."""
    out: list[str] = []
    in_section = in_para = False
    for line in md.splitlines():
        if re.match(r"^#+\s", line):
            in_section, in_para = bool(DROP_SECTION.match(line)), False
            if in_section:
                continue
        elif INLINE_LABEL.match(line):
            in_para = True
        elif in_para and not line.strip():
            in_para = False
            continue
        if in_section or in_para or DROP_LINE.search(line):
            continue
        out.append(line)
    text = re.sub(r"<!--.*?-->", "", "\n".join(out), flags=re.S)
    text = re.sub(r"https://github\.com/\S+/(pull|issues)/\d+", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def draft(src: str) -> str:
    head, _, rest = src.partition("\n")
    m = re.match(r"# PR #\d+: (.*)", head)
    title = m.group(1).strip() if m else head
    tm = TITLE.match(title)
    scope = (tm.group(3) or "").strip() if tm else ""
    request = TITLE.sub("", title).replace("[CLAUDE]", "").strip()
    pr_body, _, issues = rest.partition("\n## Issue #")
    body = clean(pr_body.split("## PR body", 1)[-1])
    issue = clean("## Issue #" + issues) if issues else ""
    lines = [f"In sqlglot{f' ({scope} dialect)' if scope else ''}: {request[0].upper() + request[1:]}."]
    if issue:
        lines += ["", issue]
    if body and body != "(empty)":
        lines += ["", body]
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str]) -> int:
    repo = argv[0]
    src_dir = EVAL / "prs" / repo / "source"
    out = EVAL / "prs" / repo / "drafts"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(src_dir.glob("*.md")):
        (out / f.name).write_text(draft(f.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"{len(list(out.glob('*.md')))} drafts in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
