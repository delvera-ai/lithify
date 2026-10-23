# Contributing to lithify

Thanks for helping. lithify is small on purpose: the CLI uses only the Python standard library,
and the deterministic parts (state, worktrees, gates, validation, rendering) are where most bugs
and most value live.

## Development setup

```bash
uv venv && . .venv/bin/activate
uv pip install -e . pytest pytest-cov ruff mypy
pytest                # unit + integration tests (simulated agent; no credentials)
ruff check . && ruff format --check . && mypy
lithify demo          # end-to-end simulation
claude plugin validate .   # if you have Claude Code installed
```

## Ground rules

- **No runtime dependencies.** Anything that needs one should be optional.
- **Tests before tokens.** Behaviour of the pipeline must be testable with the mock adapter. If you
  change a role prompt, explain the failure mode it addresses in the PR and, ideally, attach a
  before/after from a live run (`.lithify/runs/<id>/outcome.json`).
- **Adapters are thin.** CLI flags and output formats change often; keep parsing tolerant, add a
  fixture-based test for each format you support, and note the CLI version you tested against.
- **Safety defaults stay conservative.** `auto_adopt = false`, test-edit gating on, no commits.

## Pull requests

Keep PRs focused, describe the user-visible change, update `CHANGELOG.md`, and make sure CI is
green. By contributing you agree your work is licensed under Apache-2.0.

## Agent instructions

lithify is dogfooded on this repository. Project rules for coding agents live in
`.lithify/harness/` and are rendered into `CLAUDE.md`, `AGENTS.md`, `.claude/skills/` and
`.agents/skills/`; change the harness and run `lithify sync`, never the rendered copies. See
[docs/maintainers.md](docs/maintainers.md) for repository settings.
