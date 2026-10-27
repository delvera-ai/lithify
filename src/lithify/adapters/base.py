"""Adapter contract: run one headless agent session and report what happened."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

# Notices CLIs return when a subscription or API limit stops a session before it does any work.
LIMIT_NOTICE = re.compile(r"(session|usage|rate) limit|hit your limit|quota (reached|exceeded)|RESOURCE_EXHAUSTED", re.I)


class LimitReached(RuntimeError):
    """The agent CLI refused to work because of a usage, session or rate limit."""


def hit_limit(res: RunResult) -> bool:
    return not res.ok and bool(LIMIT_NOTICE.search(f"{res.error}\n{res.text[:2000]}"))


@dataclass
class RunResult:
    ok: bool
    text: str = ""
    transcript: str = ""
    tokens_in: int = 0
    tokens_cached: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0
    returncode: int = 0
    error: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    raw_stream: str = ""


class Adapter:
    """One headless coding-agent CLI. Subclasses implement build_cmd() and parse()."""

    name = "base"
    binary = ""
    model_flag = "--model"
    default_args: ClassVar[list[str]] = []

    def __init__(self, extra_args: list[str] | None = None):
        # If the user supplies adapter_args for this CLI they replace the default
        # permission flags, so a stricter policy is always possible.
        self.args = list(extra_args) if extra_args is not None else list(self.default_args)

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def version(self) -> str:
        try:
            out = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=20)
            return (out.stdout or out.stderr).strip().splitlines()[0]
        except Exception as e:
            return f"unavailable ({e.__class__.__name__})"

    def build_cmd(self, prompt: str, cwd: Path) -> list[str]:
        raise NotImplementedError

    def parse(self, stdout: str, stderr: str, rc: int) -> RunResult:
        raise NotImplementedError

    def run(self, prompt: str, cwd: Path, timeout_s: int = 1800, role: str = "execute") -> RunResult:
        cmd = self.build_cmd(prompt, cwd)
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return RunResult(ok=False, error=f"{self.binary} not found on PATH", returncode=127)
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            res = self.parse(out, f"timeout after {timeout_s}s", 124)
            res.ok = False
            res.error = f"timeout after {timeout_s}s"
            res.returncode = 124
            res.meta["role"] = role
            res.seconds = time.time() - t0
            return res
        res = self.parse(proc.stdout or "", proc.stderr or "", proc.returncode)
        res.seconds = time.time() - t0
        res.returncode = proc.returncode
        if proc.returncode != 0 and not res.error:
            res.error = (proc.stderr or "").strip()[-2000:]
        res.meta["role"] = role
        return res


def jsonl(text: str) -> list[dict[str, Any]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def clip(text: str, limit: int = 1500) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + f"\n…[{len(text) - limit} chars elided]…\n" + text[-half:]


def pick(d: dict[str, Any], *keys: str, default: int = 0) -> int:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return int(v)
    return default
