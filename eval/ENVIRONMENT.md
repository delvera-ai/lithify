# Evaluation environment

Recorded 2026-10-23 on the owner's workstation.

| component | version |
|---|---|
| OS | macOS (Darwin 25.6.0, arm64) |
| Python | 3.14.4 in the project venv (uv default; all eval runs and the 3A sweep), 3.13.7 as system `python3` |
| uv | 0.11.7 |
| git | 2.54.0 |
| gh | 2.90.0 |
| Claude Code (`claude`) | 2.1.310 for round-1 horizon arm A; B/C include 2.1.311 after CLI updates (2.1.309 was the earlier conformance capture) |
| Codex CLI (`codex`) | 0.163.0 |
| Antigravity CLI (`agy`) | 1.4.3 |
| Node / npx | v24.15.0 / 11.12.1 |

GitHub CLI scopes: `gist, read:org, repo, workflow` (no `admin:org`; repository-level settings only).

Executors: primary `claude@claude-haiku-5-5` (editor roles on Claude Code's default model); secondary `codex`.


Correction (round-2 session audit): the 2026-10-23 static inventory above did
not describe the later horizon CLI versions. All 60 A sessions record 2.1.310;
B/C record 2.1.310–2.1.311. Evidence:
`eval/round2/ROUND1_SESSION_AUDIT.json`. The original horizon launch commands
used a non-editable scratch tools venv created with Python 3.12, despite the
inventory's general statement about project-venv Python 3.14.4. The accepted
round-2 calibration used project-venv Python 3.14.4 for the runner and the
repository's absolute Python 3.12.13 for tests. Record this distinction rather
than treating the static inventory as proof of every launch environment.

The horizon launch commands omitted timeout/concurrency overrides; the frozen
runner f964993 defaults were `--timeout 900 --concurrency 4`. Round-2
replicates pass these values explicitly. A uses k=0 with no escalation, so
only one probe/suite runs at a time. A replicates run sequentially.
