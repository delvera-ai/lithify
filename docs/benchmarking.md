# Benchmarking and validation

lithify makes two claims worth testing before you trust it with a repository:

1. **Quality:** tasks run through lithify pass hidden acceptance checks more often than the same
   agent with a static harness.
2. **Cost:** after a warm-up, lithify's tokens per task approach a plain single run, unlike a
   fixed-k harness optimiser that pays for proposals on every task.

## Level 0 — simulation (free, CI)

`lithify demo` runs the same 14-task sequence under `baseline`, `static` (Harness² step every
task) and `adaptive` (lithify) with a scripted agent. It checks the plumbing and the shape of the
schedule, not model behaviour.

## Level 1 — smoke test with real CLIs (cents)

Use a small repository with tests and a holdout script outside it:

```bash
lithify init --executor claude@<small-model> --test-cmd "python -m pytest -q"
# .lithify/config.toml:  holdout_cmd = "python /abs/path/holdout.py"   max_k = 1
lithify run --keep "<a task whose hidden checks need a convention the code documents but the task doesn't mention>"
lithify logs
```

What to look for in `.lithify/runs/<id>/`: the base rollout fails the holdout; at least one
candidate harness makes the executor pass it; `outcome.json` shows which; the library entry
attributes the edit with a cited trajectory moment.

## Level 2 — PR replay (the real evaluation)

Hidden acceptance checks come for free from history: a merged pull request's own tests are a
holdout the agent never saw.

For each of 10–30 merged PRs in a repository you know, in merge order:

1. `base` = the PR's merge-base; `task` = the issue or PR description (strip anything that gives
   away the implementation); `holdout` = the test files the PR added or changed, taken from the
   merge commit with `git show <merge>:<path>` into a directory outside the repo.
2. Reset a scratch clone to `base`, and run the task under each strategy on its own clone:
   * `baseline`: `lithify run --k 0 --no-escalate` (plain agent, starter harness)
   * `static`: `lithify run --k 1` with `skip_when_base_passes = false`
   * `adaptive`: `lithify run` (the schedule decides)
3. Strategies keep their own `.lithify/` across tasks: that is the point of the comparison.
4. Record from `outcome.json` and `state.json`: holdout pass on the delivered patch, first-pass,
   executions, role sessions, tokens, `cost_usd`, wall time, always-on harness size, S.

Report pass rate with a 95% interval (with 20 tasks per strategy, differences under ~15 points
are not meaningful), the cumulative-cost curve, and the S curve. Repeat with shuffled task order
at least twice — the paper reports three shuffled streams per configuration — because the
library makes results order-dependent.

## Fairness rules

- Same executor model, same timeout, same gates for every strategy.
- Holdout files must never be present in the worktree or reachable by the agents.
- Do not tune role prompts on the evaluation tasks; keep a separate development set.
- Report failures as well as wins: the paper's own failure analysis (blind selection preferring
  a weaker candidate, an incorrect premise propagating across candidates) applies here too.

## The protocol used for 0.1.0

The 0.1.0 evaluation (`eval/`, results under `eval/results/`) implements Level 2 as follows.

- **PR selection (`eval/pr_select.py`, no LLM calls).** Merged, human-authored PRs that change both
  source and test files, in merge order. A PR is kept only if, in a clean checkout: the existing
  suite passes at base; the PR's test files fail at base and pass at the merge commit; and the
  tests that existed at base still pass against the merged source. The last check excludes PRs that
  change behaviour an existing test pins: lithify's default gate rejects any edit to existing test
  lines, so those tasks are undeliverable for every strategy (#15). The oldest ~20% of kept PRs is
  the development set; only it is used to debug the harness.
- **Task text.** Written by hand from the PR title, body and linked issues (originals kept under
  `eval/prs/<repo>/source/`): behaviour and the public API the tests use, no implementation hints.
  Every expected output quoted in a task was checked against the merge commit. Requirements only the
  tests reveal are stated explicitly and marked "(stated requirement)".
- **Holdout: post-hoc only.** The PR's test files are copied in after delivery, run against the
  applied patch, and removed. They are never a gate, so no strategy can use them to select or
  escalate. Gates are the repository's existing suite.
- **Environment.** A scratch venv with the repository's dependencies but not the package itself,
  so tests import the checkout they run in; generated, gitignored version modules are stubbed and
  committed at every base (probe worktrees do not receive ignored files). lithify runs from a
  separate scratch venv so nothing in the agents' environment points at the evaluation repository.
- **Strategies.** Each has its own clone; the code is reset to each PR's base and the strategy's
  `.lithify/` is carried forward. `baseline` = `--k 0 --no-escalate`; `static` = `--k 1`,
  `skip_when_base_passes = false`; `adaptive` = schedule, `max_k = 2`. Adoption: `auto_adopt =
  false` and every proposal adopted after the task (a maintainer who accepts everything).
- **Executors.** `claude@claude-haiku-5-5` with editor roles on Claude Code's default model; Codex
  (default model, all roles) as a second configuration.

### Pitfalls the 0.1.0 evaluation hit

- **Subscription limits silently invalidate tasks.** A Claude session-limit notice looked like an
  empty failure and was recorded as the harness's fault. `eval/pr_replay.py` now discards a task on
  any limit signature and stops; `--resume` continues from that task with the strategy's state as it
  was before it. lithify itself now stops a task on a limit notice (#20).
- **Never touch the evaluation checkout while runs are live** (no branch switches, no moving
  results). Runs read task texts from it.
- **Ceiling effects.** On humanize and tenacity a plain Haiku agent already passed 10 of 10 and 21 of 22
  hidden-test sets respectively, leaving little room for any harness to improve quality. Choose repositories or
  tasks where the baseline fails a meaningful share, or the comparison can only measure cost.
