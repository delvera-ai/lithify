"""OpenAI Codex CLI: `codex exec --json` (JSONL events; usage on turn.completed).

Format verified against codex-cli 0.163.0 (tests/fixtures/codex_0.163.0.jsonl).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from .base import Adapter, RunResult, clip, jsonl


class CodexAdapter(Adapter):
    name = "codex"
    binary = "codex"
    # workspace-write sandbox; `codex exec` never prompts for approval. Worktrees are disposable.
    # codex-cli 0.163.0 removed `--full-auto`; `--sandbox workspace-write` is its equivalent.
    default_args: ClassVar[list[str]] = ["--sandbox", "workspace-write"]

    def build_cmd(self, prompt: str, cwd: Path) -> list[str]:
        return [self.binary, "exec", "--json", "--skip-git-repo-check", "-C", str(cwd), *self.args, prompt]

    def parse(self, stdout: str, stderr: str, rc: int) -> RunResult:
        lines: list[str] = []
        text = ""
        tin = tcache = tout = 0
        failed = ""
        for ev in jsonl(stdout):
            t = ev.get("type")
            if t == "turn.completed":
                u = ev.get("usage") or {}
                tin += int(u.get("input_tokens", 0))
                tcache += int(u.get("cached_input_tokens", 0))
                tout += int(u.get("output_tokens", 0))
            elif t in ("turn.failed", "error"):
                failed = str((ev.get("error") or {}).get("message") or ev.get("message") or "turn failed")
            elif t == "item.completed":
                item = ev.get("item") or {}
                it = item.get("type")
                if it == "agent_message":
                    text = item.get("text", "")
                    lines.append(f"[assistant] {clip(text, 1200)}")
                elif it == "command_execution":
                    lines.append(
                        f"[command exit={item.get('exit_code')}] {clip(item.get('command', ''), 400)}\n"
                        f"{clip(item.get('aggregated_output', ''), 1000)}"
                    )
                elif it == "file_change":
                    changes = item.get("changes") or []
                    lines.append("[file_change] " + ", ".join(f"{c.get('kind')} {c.get('path')}" for c in changes))
                elif it == "error":
                    lines.append(f"[error] {clip(item.get('message', ''), 800)}")
        return RunResult(
            ok=rc == 0 and not failed,
            text=text,
            transcript="\n".join(lines),
            tokens_in=max(0, tin - tcache),
            tokens_cached=tcache,
            tokens_out=tout,
            error=failed or ("" if rc == 0 else clip(stderr, 2000)),
        )
