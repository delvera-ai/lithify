# Environment parity before calibration

Reference: eval/ENVIRONMENT.md (2026-10-23).

| Component | Round 1 record | Invalid A2 launch | Corrected setup |
|---|---|---|---|
| OS | Darwin 25.6.0 arm64 | same | same |
| uv | 0.11.7 | same | same |
| Claude Code | 2.1.309 | 2.1.191 from Homebrew | isolated npm install pinned 2.1.309; verified --version |
| Evaluation runner Python | project venv 3.14.4 | scratch 3.12.13 | use 3.14.4 from project venv to create non-editable calibration environment |
| Repository test Python | absolute scratch venv path in raw gate reports; repos.py creates 3.12 | absolute scratch venv 3.12.13 | absolute scratch venv 3.12.13 (repos.py policy) |
| bare python for subprocesses | available in original launch environment | missing | prepend repository venv bin to PATH |

The invalid A2 gate and holdout commands already used the absolute venv Python.
The failure was an internal subprocess in sqlglot's test_lazy_load, not the
top-level test command. Fix PATH as well as keeping absolute gate/holdout commands.
No global CLI installation or user settings were changed. Pin is run-local:
`<scratch>/claude-2.1.309/node_modules/.bin/claude`.

A matching CLI version and requested model label do not by themselves establish
matching billed model versions or accounting. Compare calibration modelUsage
with the original session evidence before deciding comparability.

Spend for this step: $0. Round-2 cumulative: $3.6267. No paid runs started.

## Session evidence correction

The subsequent all-rollout session audit found A actually ran Claude Code
2.1.310, and B/C 2.1.310–2.1.311. The 2.1.309 environment record was stale.
The owner-requested 2.1.309 pin is available, but it does not reproduce A's
actual CLI version. Treat the calibration as a setup/cost measurement, not a
valid replicate of A1. Ask before changing the noise plan.

## Remaining tool versions

Verified git 2.54.0, gh 2.90.0, and Codex 0.163.0 match the record.
Antigravity is now 1.4.6 vs 1.4.3 (unused by the Claude calibration).
The launch shell has Node 22.23.2 / npm 10.9.8 vs recorded Node 24.15.0 /
npm 11.12.1; install a run-local Node/npm pin before calibration so npm-based
Claude runs under the recorded runtime. Global tools remain unchanged.

## Calibration runtime decision

Owner approved 2.1.310 for actual A parity (rather than the stale 2.1.309
record). Both isolated pins are installed. Node 24.15.0 and npm 11.12.1 are
also installed run-locally. Final calibration uses 2.1.310 with that runtime,
Python 3.14.4 for the non-editable runner, and absolute repo-venv Python for
both gates and holdouts, with repo-venv bin on PATH for test subprocesses.
