"""Claude Code: `claude -p --output-format stream-json --verbose`.

stream-json gives the full trajectory (tool calls and results), which is the evidence
the proposers read; the final `result` event carries usage and total_cost_usd.

Format verified against Claude Code 2.1.309 (tests/fixtures/claude_2.1.309.jsonl).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from .base import Adapter, RunResult, clip, jsonl


class ClaudeAdapter(Adapter):
    name = "claude"
    binary = "claude"
    # Probes run in disposable worktrees outside the repo; override in config to tighten.
    default_args: ClassVar[list[str]] = ["--dangerously-skip-permissions"]

    def build_cmd(self, prompt: str, cwd: Path) -> list[str]:
        return [self.binary, "-p", prompt, "--output-format", "stream-json", "--verbose", *self.args]

    def parse(self, stdout: str, stderr: str, rc: int) -> RunResult:
        events = jsonl(stdout)
        lines: list[str] = []
        final: dict = {}
        for ev in events:
            t = ev.get("type")
            if t == "result":
                final = ev
            elif t in ("assistant", "user"):
                for block in (ev.get("message") or {}).get("content") or []:
                    if not isinstance(block, dict):
                        continue
                    bt = block.get("type")
                    if bt == "text" and block.get("text", "").strip():
                        lines.append(f"[{t}] {clip(block['text'], 1200)}")
                    elif bt == "tool_use":
                        lines.append(f"[tool_use {block.get('name')}] {clip(json.dumps(block.get('input')), 800)}")
                    elif bt == "tool_result":
                        content = block.get("content")
                        if isinstance(content, list):
                            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                        err = " ERROR" if block.get("is_error") else ""
                        lines.append(f"[tool_result{err}] {clip(content or '', 1000)}")
        usage = final.get("usage") or {}
        return RunResult(
            ok=bool(final) and not final.get("is_error", False),
            text=str(final.get("result", "")),
            transcript="\n".join(lines),
            tokens_in=int(usage.get("input_tokens", 0)) + int(usage.get("cache_creation_input_tokens", 0)),
            tokens_cached=int(usage.get("cache_read_input_tokens", 0)),
            tokens_out=int(usage.get("output_tokens", 0)),
            cost_usd=float(final.get("total_cost_usd", 0.0) or 0.0),
            error="" if final else clip(stderr or stdout, 2000),
            meta={"num_turns": final.get("num_turns"), "session_id": final.get("session_id")},
        )
