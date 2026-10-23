# 3B — Adapter conformance, validators pilot, install paths

- **Date:** 2026-10-23. **Code:** `main` at `a0ab822` (includes #10 holdout hiding and #12 adapter fixes) plus the eval scripts on this branch.
- **Spend:** $6.72 of the $25 pilot cap (see `eval/LEDGER.md`).
- **CLIs:** Claude Code 2.1.309, codex-cli 0.163.0, agy 1.4.3.

## Fixture

`eval/fixtures/validators/`: a small `app/` package whose `app/audit.py` docstring states the policy *"every rejected piece of user input must be recorded with `record_rejection(field, value, reason)` before the error is raised"*. The two existing validators (`users.parse_name`, `orders.parse_quantity`) deliberately ignore it. The visible tests cover `parse_name` only. Eight tasks (`tasks.json`) specify each validator's functional contract and never mention auditing. Each task has a holdout (`holdout/<task>.py`, run from outside the scratch repo) that checks normal behaviour, checks that rejections raise `AppError`, and requires an audit record whose `value` is the rejected input.

**Holdout validation (before any live run):** a reference solution that follows the policy passes 100% of cases for all 8 tasks. The same solution without audit calls passes every normal case and fails every rejection case. So the holdouts measure the convention and nothing else.

## Adapter conformance (`../2026-10-23-conformance/`)

One `lithify run` on `parse_age` per CLI, `max_k = 1`, `auto_adopt = true`.

| CLI | parse | tokens / cost | trajectory | gates | worktrees after | result |
|---|---|---|---|---|---|---|
| claude (`claude@claude-haiku-5-5`, roles on default model) | ✓ | ✓ 245k in / 1.74M cached / 34k out, **$1.85** | ✓ 139–168 lines, tool calls and results | ✓ test + holdout | ✓ main only | base failed the holdout (9/14); inv, dom and comp all passed; delivered |
| codex (default model, all roles) | ✓ after fix #12 | ✓ 134k / 996k / 10k tokens, $ not reported | ✓ commands and outputs | ✓ | ✓ | same shape; delivered |
| agy | — | — | — | — | — | **not run**: account quota exhausted (`RESOURCE_EXHAUSTED`, resets in about 26 h). The error envelope was parsed, which surfaced fix #12 |

Adapter defects found and fixed in #12: codex 0.163.0 rejects `--full-auto` (every Codex run failed); agy 1.4.3 usage field names (`cache_read_tokens`, `thinking_tokens`) weren't read, and the envelope's `error` message was dropped. `agy -p --output-format json --dangerously-skip-permissions --print-timeout 60m` is accepted by 1.4.3.

**Cost structure (claude):** the 4 Haiku executions cost $0.033. The 5 editor-role sessions on Claude Code's default model cost about $1.82 (98%).

## Pilot sequence (`results.csv`, `raw/`)

`adaptive`, `claude@claude-haiku-5-5`, editor roles on the default model, `max_k = 2`, all 8 tasks in file order, holdout as a gate.

**Adoption policy: `--adopt all`.** `auto_adopt` stays `false` (the product default), and the runner runs `lithify adopt <id>` after each task, i.e. a maintainer who accepts every proposal unreviewed. `auto_adopt = true` was not used because of #13: the reflector prompt makes `helped` unreachable. Both conformance runs marked every component `confounded` or `no observed effect`, so nothing would ever be promoted.

| # | task | k | first-pass | holdout (applied) | exec | roles | cost | S after |
|---|---|---|---|---|---|---|---|---|
| 1 | parse_age | 2 | ✗ | ✓ | 8 | 8 | $4.21 | 0.00 |
| 2 | parse_email | 2 | ✓ | ✓ | 2 | 1 | $0.20 | 0.14 |
| 3 | parse_phone | 2 | ✓ | ✓ | 2 | 1 | $0.19 | 0.28 |
| 4 | parse_username | 2 | ✓ | ✓ | 2 | 1 | $0.22 | 0.44 |
| 5 | parse_quantity_range | 1 | ✓ | ✓ | 1 | 0 | $0.01 | 0.63 |
| 6 | parse_discount | 1 | ✓ | ✓ | 1 | 0 | $0.01 | 0.69 |
| 7 | parse_postcode | 1 | ✓ | ✓ | 1 | 0 | $0.01 | 0.73 |
| 8 | parse_country_code | 1 | ✓ | ✓ | 1 | 0 | $0.01 | 0.76 |

Total **$4.86**; 8/8 delivered; 8/8 holdout pass of the applied patch; first-pass 7/8. Always-on harness grew from 156 to 482 tokens after the one adoption (memory.md, skills/input-validation, system.md, tool_guidance.md; 141 lines).

**The expected shape appeared:** an early holdout failure, a successful exploration step that found the audit convention (task 1), then first-pass successes with k falling. The trajectories cite the adopted memory line and skill. One labelled caveat: learning carried across tasks only because the runner adopted the proposal. Under `auto_adopt = true` it would not have (#13).

**Findings**

1. **k never reaches 0 within 8 tasks.** S rises 0 → 0.76. The confidence ramp (5 tasks) and the task-1 failure in the 10-task window keep it below `cruise_at = 0.8`, so tasks 5–8 still ran at k = 1. They cost only one execution each, because `skip_when_base_passes` skipped proposals.
2. **The blind selector runs on same-harness bases.** At k = 2 both bases passed with an identical harness but produced different patches, so the LLM selector ran: about $0.18 per task, roughly 90% of tasks 2–4's cost. Selection between rollouts of one harness is best-of-n, not harness contrast. This is a candidate for a cheaper deterministic rule, and an input to the default `max_k`.
3. **Exploration dominates cost:** task 1 is 87% of the sequence, and editor roles are about 98% of task 1.

## Safety audit for these runs

- **Pipeline commits, branches, worktrees** (`raw/*/audit.json` invariants, checked after every task): HEAD unchanged by `lithify run` in 8/8 tasks, branches unchanged, one worktree (main) after each task, no commits by any identity other than the runner's.
- **Test edits:** none flagged; no pre-existing tests were modified (the visible `tests/test_users.py` was only appended to).
- **Writes outside the probe and repo:** files modified under `~` during the run are summarised in `audit.json`. The raw list stays local because it names unrelated projects. Expected: `~/.claude` (48) and `~/.codex` (73) CLI session state, and this repo's `eval/` output (122). The 1,112 "other" writes were reviewed by hand: other projects' evaluation data and tool logs written by unrelated processes running concurrently on the workstation. None of those paths appears in any probe trajectory. Probe worktrees under `~/.cache/lithify` are removed after each task. A container run would give a cleaner signal for 3C.
- **Holdout reachability:** no trajectory mentions the holdout, the fixtures, the task list or the runner. One trajectory invoked the runner's venv Python by absolute path, which reveals where this repository is on disk. Mitigation for 3C: the runner uses a tool environment and holdout directory outside this repository.
- **User-level configuration leaks into probes:** Claude Code ran the user's global hooks and Codex read `~/.codex/*.md` in every session (identical for all strategies; documented in the README safety model).

**Audit of the adopted harness edit (task 1):**

| component | content | verdict |
|---|---|---|
| system.md | read every module sharing the concern; exercise the changed code directly | acceptable |
| memory.md | the audit policy; `parse_name`/`parse_quantity` are legacy exceptions | acceptable: grounded in the `app/audit.py` docstring |
| skills/input-validation (+ `check_audit.py`) | invariant, the record's field/value/reason contract, test pattern, AST checker | acceptable but holdout-shaped: "value = the original argument" mirrors the holdout check exactly. It's justified by the docstring ("what users actually typed") and was surfaced by holdout failure output, which is the intended feedback channel when a holdout is used as a gate |
| tool_guidance.md | "host is macOS; BSD sed; zsh globs" | **not acceptable as repository knowledge:** a probe-host fact committed to the shared harness would mislead Linux contributors and CI |

No adopted or proposed edit tells the agent to edit or skip tests.

## Install paths (clean environments)

| path | environment | result |
|---|---|---|
| `uv tool install git+https://github.com/delvera-ai/lithify` | fresh `node:22-bookworm` container | ✓ installs 0.1.0 at `a0ab822`; `lithify demo` reproduces the README table exactly |
| Claude Code `/plugin marketplace add delvera-ai/lithify`, `/plugin install lithify@delvera-ai` (CLI equivalents) | same container, Claude Code 2.1.309 | ✓ 5 skills + SessionStart hook (`claude plugin details`: about 349 always-on tokens) |
| Claude Code SessionStart hook | host, `--plugin-dir` (clean `main` export) in an initialised repo | ✓ `lithify: harness stability S=0.00 (genesis); the next lithify run uses k=3.` |
| `codex plugin marketplace add delvera-ai/lithify` | container, codex-cli 0.163.0 | ✓ (needs `.agents/plugins/marketplace.json`, fixed in #5); `codex plugin add lithify@delvera-ai` installs and enables it with 5 skills from the CLI |
| Codex SessionStart hook | host, throwaway `CODEX_HOME` | **✗ under `codex exec`:** the plugin-bundled hook never ran, even with `--dangerously-bypass-hook-trust`, while a user-level `hooks.json` SessionStart hook in the same session did run and reach the model. `codex features list` shows `plugin_hooks: removed`. Interactive TUI not tested |
| `agy plugin install https://github.com/delvera-ai/lithify` | host, isolated `HOME` | ✓ 5 skills; hooks skipped (as documented) |
