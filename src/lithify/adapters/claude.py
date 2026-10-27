"""Claude Code: `claude -p --output-format stream-json --verbose`.

stream-json gives the full trajectory (tool calls and results), which is the evidence
the proposers read; each `result` event carries usage and total_cost_usd. Background completion
turns can emit additional results; accounting must retain every result. Usage is
per-turn; total_cost_usd and modelUsage are cumulative within each session:
https://code.claude.com/docs/en/agent-sdk/cost-tracking#track-costs-in-streaming-input-mode

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
        results: list[dict] = []
        calls: dict[str, dict] = {}
        models: dict[str, dict] = {}
        totals = dict.fromkeys(("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"), 0)
        sessions: dict[str, dict] = {}
        turns = 0
        for ev in events:
            t = ev.get("type")
            if t == "result":
                final = ev
                usage = ev.get("usage") or {}
                for key in totals:
                    totals[key] += int(usage.get(key, 0) or 0)
                session = sessions.setdefault(ev.get("session_id", ""), {"cost": 0.0, "models": {}})
                # Later results are cumulative, not additional spend. A crash can zero them.
                session["cost"] = max(session["cost"], float(ev.get("total_cost_usd", 0.0) or 0.0))
                turns += int(ev.get("num_turns", 0) or 0)
                billed = ev.get("modelUsage") or {}
                results.append(
                    {
                        "session_id": ev.get("session_id", ""),
                        "usage": usage,
                        "modelUsage": billed,
                        "total_cost_usd": ev.get("total_cost_usd", 0.0),
                        "num_turns": ev.get("num_turns", 0),
                        "is_error": ev.get("is_error", False),
                    }
                )
                for model, values in billed.items():
                    aggregate = session["models"].setdefault(model, {})
                    for key, value in values.items():
                        if key in (
                            "inputTokens",
                            "outputTokens",
                            "cacheReadInputTokens",
                            "cacheCreationInputTokens",
                            "thinkingTokens",
                            "costUSD",
                            "webSearchRequests",
                        ):
                            aggregate[key] = max(aggregate.get(key, 0), value or 0)
                        else:
                            aggregate[key] = value
            elif t in ("assistant", "user"):
                message = ev.get("message") or {}
                if t == "assistant" and message.get("usage"):
                    usage = message["usage"]
                    # A streamed message can appear in several blocks with the same id.
                    key = message.get("id") or f"event-{len(calls)}"
                    calls[key] = {
                        "model": message.get("model", ""),
                        "usage": usage,
                        "context_tokens": sum(
                            int(usage.get(k, 0) or 0)
                            for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
                        ),
                    }
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
        additive = {
            "inputTokens",
            "outputTokens",
            "cacheReadInputTokens",
            "cacheCreationInputTokens",
            "thinkingTokens",
            "costUSD",
            "webSearchRequests",
        }
        for session in sessions.values():
            for model, values in session["models"].items():
                aggregate = models.setdefault(model, {})
                for key, value in values.items():
                    aggregate[key] = aggregate.get(key, 0) + value if key in additive else value
        return RunResult(
            ok=bool(final) and not final.get("is_error", False),
            text=str(final.get("result", "")),
            transcript="\n".join(lines),
            tokens_in=totals["input_tokens"] + totals["cache_creation_input_tokens"],
            tokens_cached=totals["cache_read_input_tokens"],
            tokens_out=totals["output_tokens"],
            cost_usd=sum(session["cost"] for session in sessions.values()),
            # An error result (e.g. a usage-limit notice) carries its message in `result`.
            error=clip(str(final.get("result", "")), 2000)
            if final.get("is_error")
            else ("" if final else clip(stderr or stdout, 2000)),
            meta={
                "num_turns": turns,
                "session_id": final.get("session_id"),
                "result_count": len(results),
                "model_usage": models,
                "results": results,
                "calls": list(calls.values()),
            },
            raw_stream=stdout,
        )
