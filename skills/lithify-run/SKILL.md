---
name: lithify-run
description: Run a coding task through lithify so the project's agent harness (CLAUDE.md/AGENTS.md rules, skills, scripts) improves from evidence. Use when the user says /lithify-run, asks to "lithify" a task, or asks to run a task with harness probing or self-improvement.
---

# Run a task through lithify

lithify runs the task in disposable git worktrees with one or more candidate harnesses,
checks every result with the project's own tests/lint first, picks the best deliverable,
applies it to the working tree, and records what it learned about the harness. How much it
explores (k) is decided by the project's stability score; you do not choose it unless the
user asks.

## Steps

1. Check lithify is available: `lithify --version`. If the command is missing, tell the user
   and offer `uv tool install lithify` (or `pipx install lithify`). Do not proceed without it.
2. Check the repository is initialised: `lithify status`. If it says "not initialised", stop
   and suggest the `lithify-init` skill instead.
3. Show the plan and cost before spending tokens:
   `lithify run --dry-run "<the task, verbatim>"`
   Tell the user the k it chose and the execution count in one line. If k is 2 or more,
   ask for confirmation before continuing — wide exploration runs many agent sessions.
4. Start the run detached (probes can outlast your shell's command timeout):
   `lithify run --detach "<the task, verbatim>"`
   It prints a JSON line with `task_id`.
5. Poll until it finishes: `lithify logs <task_id> --tail 25`, waiting between polls
   (e.g. `sleep 60` first). Keep polling while it reports `running`; give the user a short
   progress line at most every few polls, not after every one.
6. When it reports `finished`, report in a few lines:
   - whether a deliverable was applied, and from which probe (`base-*` means the current
     harness already did it; `inv-*`, `dom-*`, `comp-*` mean an improved harness did);
   - `git diff --stat` of the applied change — do not commit it; the user reviews and commits;
   - any components promoted into the harness, or a pending proposal
     (`lithify adopt --list`), and the new stability score.
7. If nothing passed the gates, say so plainly, point to `.lithify/runs/<task_id>/rollouts/`
   for the evidence, and offer to work on the task directly.

## Rules

- Pass the user's task text verbatim; do not rewrite or expand it.
- Never edit `.lithify/harness/` by hand during a run, and never run `lithify adopt` without
  the user asking — adoption changes how every future session in this repo behaves.
- Never commit, push or open a PR as part of this skill.
