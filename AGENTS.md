<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository, including test fixtures and captured CLI output (redact them).
- No runtime dependencies: `src/lithify/` uses the Python standard library only. Dev tools go in `[dependency-groups] dev`.
- Never weaken a safety default without an explicit issue that asks for it: `auto_adopt = false`, test-edit gating (`allow_test_edits = false`), and no commits, pushes or PRs from the pipeline (`worktree.py` only commits inside probe worktrees).
- Every change under `src/lithify/adapters/` needs a fixture-based parse test built from captured real CLI output (see the `adapter-change` skill).
- Every change under `src/lithify/prompts/` must name the failure mode it addresses (see the `prompt-change` skill).
- Do not hand-edit the lithify managed block in `CLAUDE.md`/`AGENTS.md` or anything under `.claude/skills/`, `.agents/skills/`, `.claude/agents/`; edit `.lithify/harness/` and run `lithify sync`.

### Durable project memory

- The project's checks run with `pytest -q`.
- Full pre-commit check: `ruff check . && ruff format --check . && mypy && pytest -q`; `lithify demo` is the credential-free end-to-end simulation (CI runs it).
- Module map (`src/lithify/`): `state.py` stability score and k schedule; `pipeline.py` the Propose→Probe→Compose→Select→Reflect loop; `worktree.py` probe isolation and deliverable diffs; `gates.py` deterministic gates and test-edit detection; `validate.py` zero-token harness validation; `harness.py` canonical harness and rendering into CLI paths; `library.py` improvement library and reflection parsing; `adapters/` one thin module per CLI (`mock.py` is the simulated agent); `prompts/` role prompts; `ops.py` init/sync/status/adopt/compact/report; `cli.py` argparse entry point.
- The version string lives in four places that must match (the release workflow checks): `pyproject.toml`, `plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`.
- `.agents/plugins/marketplace.json` and `.claude-plugin/` are real plugin sources, not rendered output.
- Tests use the mock adapter and `LITHIFY_WORK_DIR` (set by `tests/conftest.py`); no test may need credentials or a real agent CLI.

### Skills (load on demand)

- `adapter-change` — Use when a task touches src/lithify/adapters/ (Claude Code, Codex, Antigravity or mock adapters, CLI flags or output parsing).
- `prompt-change` — Use when a task touches src/lithify/prompts/ (proposer, composer, selector, reflector or compact role prompts).
<!-- lithify:end -->
