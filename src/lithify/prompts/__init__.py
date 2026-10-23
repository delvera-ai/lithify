"""Role prompts. Structure follows the Harness² stage prompts (Xu et al., 2026, App. H),
rewritten for software repositories where deterministic gates exist."""

from __future__ import annotations

from importlib import resources

ROLE_FILES = {
    "propose_inv": "propose_inv.md",
    "propose_dom": "propose_dom.md",
    "compose": "compose.md",
    "select": "select.md",
    "reflect": "reflect.md",
    "compact": "compact.md",
}


def _read(name: str) -> str:
    return resources.files(__package__).joinpath(name).read_text(encoding="utf-8")


def render(role: str, **values: object) -> str:
    text = _read(ROLE_FILES[role])
    shared = _read("_editor_shared.md")
    guard = _read("_guard.md")
    if role in ("propose_inv", "propose_dom"):
        cand = (
            f"You are candidate {values.get('I', 1)} of {values.get('K', 1)} on this dimension, drawn "
            "independently from the same evidence. Commit to the single most defensible version of your "
            "dimension; a later stage compares and merges."
        )
    else:
        cand = ""
    text = text.replace("@@SHARED@@", shared).replace("@@CANDIDATE_LINE@@", cand).replace("@@GUARD@@", guard)
    for key, val in values.items():
        text = text.replace(f"@@{key}@@", str(val))
    return text
