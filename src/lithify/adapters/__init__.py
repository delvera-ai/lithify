from __future__ import annotations

from .agy import AgyAdapter
from .base import Adapter, RunResult
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .mock import MockAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    "claude": ClaudeAdapter,
    "codex": CodexAdapter,
    "agy": AgyAdapter,
    "mock": MockAdapter,
}


def split_spec(spec: str) -> tuple[str, str]:
    """'claude@claude-haiku-5-5' -> ('claude', 'claude-haiku-5-5'); 'codex' -> ('codex', '')."""
    cli, _, model = spec.partition("@")
    return cli.strip(), model.strip()


def get_adapter(spec: str, extra_args: list[str] | None = None) -> Adapter:
    """Build an adapter from 'cli' or 'cli@model'."""
    name, model = split_spec(spec)
    try:
        ad = ADAPTERS[name](extra_args)
    except KeyError:
        raise ValueError(f"unknown CLI {name!r}; choose one of {', '.join(ADAPTERS)}") from None
    if model and ad.model_flag:
        ad.args += [ad.model_flag, model]
    return ad


__all__ = ["ADAPTERS", "Adapter", "RunResult", "get_adapter", "split_spec"]
