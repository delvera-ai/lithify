"""Read-only audit of archived rollouts and surviving local Claude session metadata."""

from __future__ import annotations

import collections
import json
from pathlib import Path


def content_text(content) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    raw = root / "eval/results/2026-10-26-horizon/raw"
    projects = list((Path.home() / ".claude/projects").iterdir())
    rows = []
    for arm in sorted(d for d in raw.iterdir() if d.is_dir()):
        for trajectory in sorted(arm.rglob("trajectory.md")):
            task = trajectory.parents[3]
            state = json.loads((task / "state.json").read_text())
            tid = state["history"][-1]["task_id"]
            final = trajectory.read_text().split("final message:\n", 1)[1].split("\n## events", 1)[0].strip()
            candidates = []
            for directory in projects:
                if not directory.name.endswith(f"-{tid}-{trajectory.parent.name}"):
                    continue
                for session in directory.glob("*.jsonl"):
                    versions, models, calls = set(), set(), {}
                    last_user, last_assistant, matching_user = "", "", None
                    for line in session.open():
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if event.get("version"):
                            versions.add(event["version"])
                        message = event.get("message") or {}
                        if event.get("type") == "user":
                            last_user = content_text(message.get("content"))
                        elif event.get("type") == "assistant":
                            last_assistant = content_text(message.get("content")).strip()
                            if last_assistant == final:
                                matching_user = last_user
                            model = message.get("model", "")
                            if model:
                                models.add(model)
                            if message.get("usage"):
                                usage = message["usage"]
                                calls[message.get("id") or str(len(calls))] = {
                                    "model": model,
                                    "usage": usage,
                                    "context_tokens": sum(
                                        int(usage.get(k, 0) or 0)
                                        for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
                                    ),
                                }
                    if matching_user is not None:
                        candidates.append(
                            {
                                "versions": sorted(versions),
                                "models": sorted(models),
                                "terminal_notification": matching_user.lstrip().startswith("<task-notification>"),
                                "matched_at_session_end": last_assistant == final,
                                "calls": list(calls.values()),
                            }
                        )
            row = {
                "arm": arm.name,
                "trajectory": str(trajectory.relative_to(root)),
                "matched_sessions": len(candidates),
                "evidence": candidates,
            }
            rows.append(row)
    output = root / "eval/round2/ROUND1_SESSION_AUDIT.json"
    output.write_text(json.dumps(rows, indent=2) + "\n")
    for arm in sorted({r["arm"] for r in rows}):
        subset = [r for r in rows if r["arm"] == arm]
        counts = collections.Counter()
        versions = set()
        for row in subset:
            evidence = row["evidence"]
            counts["matched" if evidence else "unmatched"] += 1
            if any(e["terminal_notification"] for e in evidence):
                counts["notification_endings"] += 1
                print("notification:", row["trajectory"])
            versions.update(v for e in evidence for v in e["versions"])
        print(arm, len(subset), dict(counts), sorted(versions))


if __name__ == "__main__":
    main()
