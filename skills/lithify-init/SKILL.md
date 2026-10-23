---
name: lithify-init
description: Set up lithify in the current git repository (creates .lithify/, a starter harness, and renders it into CLAUDE.md, AGENTS.md and skills folders). Use when the user says /lithify-init or asks to set up, install or enable lithify for this project.
---

# Initialise lithify in this repository

1. Confirm this is a git repository (`git rev-parse --show-toplevel`). lithify needs git.
2. Check lithify is installed: `lithify --version`. If missing, offer
   `uv tool install lithify` or `pipx install lithify` and stop until it is installed.
3. Find the project's check command. Look at CI config, `package.json` scripts, `Makefile`,
   `pyproject.toml`, `Cargo.toml` or `go.mod`. Prefer the fastest command that runs the unit
   tests; mention a lint or typecheck command if there is an obvious one. Confirm it with the
   user in one line if there is any doubt.
4. Run `lithify init --test-cmd "<command>"` (add `--executor claude|codex|agy` if the user
   prefers a specific CLI for probes).
5. Open `.lithify/config.toml` and set `lint_cmd` / `typecheck_cmd` if the project has them.
   Explain `auto_adopt` in one sentence: off by default, so harness changes wait for review.
6. Run `lithify doctor` and `lithify status` and summarise the result.
7. Tell the user what to commit: `.lithify/` (config, harness, library, state), and the
   rendered `CLAUDE.md`, `AGENTS.md`, `.claude/skills/`, `.agents/skills/`. Probe evidence in
   `.lithify/runs/` is git-ignored.

Existing CLAUDE.md / AGENTS.md content is preserved: lithify only manages the block between
its `lithify:begin` and `lithify:end` markers, and never overwrites a skill it did not create.
