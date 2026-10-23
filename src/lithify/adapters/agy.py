"""Google Antigravity CLI: `agy -p --output-format json`.

The JSON envelope carries conversation_id, status, response and usage. agy 1.0.x had
a bug where print mode wrote nothing to stdout when piped; lithify reports that as an
error with an upgrade hint rather than guessing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from .base import Adapter, RunResult, clip, pick


class AgyAdapter(Adapter):
    name = "agy"
    binary = "agy"
    default_args: ClassVar[list[str]] = ["--dangerously-skip-permissions", "--print-timeout", "60m"]

    def build_cmd(self, prompt: str, cwd: Path) -> list[str]:
        return [self.binary, "-p", prompt, "--output-format", "json", *self.args]

    def parse(self, stdout: str, stderr: str, rc: int) -> RunResult:
        raw = stdout.strip()
        if not raw:
            return RunResult(
                ok=False,
                error="agy produced no stdout (agy 1.0.x print-mode bug?) — run `agy update`. " + clip(stderr, 1000),
            )
        try:
            env = json.loads(raw[raw.find("{") :])
        except json.JSONDecodeError:
            return RunResult(ok=bool(rc == 0), text=raw, transcript=clip(raw, 20000))
        usage = env.get("usage") or {}
        status = str(env.get("status", "")).upper()
        text = str(env.get("response", ""))
        return RunResult(
            ok=rc == 0 and status in ("", "SUCCESS", "OK", "COMPLETED"),
            text=text,
            # agy's envelope has no tool trajectory; keep the response as the transcript.
            transcript=f"[assistant] {clip(text, 20000)}",
            tokens_in=pick(usage, "input_tokens", "inputTokens", "prompt_tokens", "promptTokenCount"),
            tokens_cached=pick(usage, "cached_input_tokens", "cachedInputTokens", "cachedContentTokenCount"),
            tokens_out=pick(usage, "output_tokens", "outputTokens", "candidates_tokens", "candidatesTokenCount"),
            error="" if status in ("", "SUCCESS", "OK", "COMPLETED") else f"agy status {status}",
            meta={"conversation_id": env.get("conversation_id")},
        )
