# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] — unreleased

### Added
- `lithify` CLI (standard library only): `init`, `sync`, `validate`, `status`, `run`, `logs`,
  `adopt`, `compact`, `report`, `demo`, `doctor`, `hook`.
- Task-level recursion: scoped INV/DOM proposers, parallel and sequential modes, composition,
  probes in git worktrees outside the repository, deterministic gates, blind selection.
- Harnessing-level recursion: reflector edit attribution, improvement library with
  `EXPERIENCE.md` entries, evidence-gated promotion (`auto_adopt`) and reviewable proposals.
- Dynamic k schedule from a stability score, with cruise mode and anomaly spikes.
- Adapters for Claude Code, Codex and Antigravity; `cli@model` specs; a deterministic simulated
  agent for tests and `lithify demo`.
- Claude Code, Codex and Antigravity plugin manifests, five skills, and a fail-open
  `SessionStart` hook.
- `eval/sim_sweep.py`: simulation robustness sweep across task orders and mock noise levels
  (CI job `sim-sweep`); `LITHIFY_MOCK_SEED` varies mock noise draws between replicates.
- `eval/`: validators fixture with out-of-repo holdouts, `run_sequence.py` live runner,
  adapter conformance and pilot results (phase 3B).
- `eval/pr_select.py`, `eval/pr_replay.py`, `eval/repos.py`: PR-replay evaluation (post-hoc
  holdouts, per-strategy clones carrying `.lithify/`), humanize and tenacity PR lists, the
  development-set debug run and the humanize pilot (phase 3C).
- `eval/audit.py`: automated safety audit across every live run (pipeline invariants, test-edit
  flags, adopted harness edits, git writes, installs and paths outside the probe in trajectories).
- In-process CLI tests (`tests/test_cli.py`): `cli.py` coverage 0% → 83%.
- `needs-review.patch`: when every command gate passes but a rollout edited pre-existing tests, the
  smallest such patch is saved for review and named in `outcome.json` (`needs_review`) instead of
  being discarded (#15).
- `eval/RELEASE_READINESS.md` and an Evaluation section in the README with the 0.1.0 PR-replay
  results; `docs/benchmarking.md` documents the protocol actually used.

### Changed
- Default `max_k` is 2 (was 3), set from the evaluation data.
- README safety model: isolation covers the repository, not the machine — Claude Code probes with
  `--dangerously-skip-permissions` can write outside their worktree; Codex's sandbox prevented this.

### Fixed
- Reflector prompt: `helped` is defined operationally and one rollout is enough evidence. The old
  rule ("prefer `confounded` when a single rollout stands behind the difference") made `helped`
  unreachable, so `auto_adopt` never promoted anything (#13).
- Codex adapter: `codex-cli` 0.163.0 rejects `--full-auto`; default flags are now
  `--sandbox workspace-write`.
- Antigravity adapter: read `cache_read_tokens` and `thinking_tokens` (agy 1.4.3), and keep the
  envelope's `error` message instead of reporting only the status.
- `holdout_cmd` no longer reaches agents: probe and snapshot worktrees drop `.lithify/config.toml`,
  and gate reports show the holdout's result but not its command (#9).
- Codex marketplace manifest lives at `.agents/plugins/marketplace.json` (was misplaced at
  `plugins/marketplace.json`).
- Deliverable diffs and the main-tree dirty patch excluded all of `.claude/` and `.agents/`, so
  edits to real sources there (e.g. `.agents/plugins/marketplace.json`, `.claude/settings.json`)
  were silently dropped from task deliverables and never reached probe worktrees. Only the
  rendered subpaths (`.claude/skills`, `.agents/skills`, `.claude/agents`) are excluded now.
- CI installs into the `setup-uv` virtual environment instead of the system interpreter, and
  `claude plugin validate . --profile directory --strict` now fails the build instead of warning.
- Agent-CLI usage, session and rate limits: the Claude adapter now reports the CLI's error text
  instead of an empty error, and a limit notice stops the task (`LimitReached`) instead of
  launching further sessions that fail empty and get recorded as harness failures.
