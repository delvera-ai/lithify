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
