# Evaluation environment

Recorded 2026-10-23 on the owner's workstation.

| component | version |
|---|---|
| OS | macOS (Darwin 25.6.0, arm64) |
| Python | 3.14.4 in the project venv (uv default; all eval runs and the 3A sweep), 3.13.7 as system `python3` |
| uv | 0.11.7 |
| git | 2.54.0 |
| gh | 2.90.0 |
| Claude Code (`claude`) | 2.1.309 |
| Codex CLI (`codex`) | 0.163.0 |
| Antigravity CLI (`agy`) | 1.4.3 |
| Node / npx | v24.15.0 / 11.12.1 |

GitHub CLI scopes: `gist, read:org, repo, workflow` (no `admin:org`; repository-level settings only).

Executors: primary `claude@claude-haiku-5-5` (editor roles on Claude Code's default model); secondary `codex`.
