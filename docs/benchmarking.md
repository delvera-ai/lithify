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
