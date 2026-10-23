---
name: lithify-compact
description: Shrink this repository's always-on agent instructions — deduplicate rules, move situational rules into on-demand skills, and list rules that a linter or test could enforce instead. Use when lithify reports the harness is over budget, or the user says /lithify-compact.
---

# Compact the harness

Self-improving harnesses accumulate rules; every always-on line is paid for on every run.

1. `lithify status` — note the always-on token estimate and budget.
2. `lithify compact` — runs a janitor session on a copy of the harness and writes the result
   as a proposal (nothing changes yet). It can take a few minutes.
3. Read the new proposal's `PROPOSAL.md` and `harness.diff` and summarise: tokens before/after,
   which rules were merged, which moved into skills, and the "candidates for mechanical
   enforcement" list in the proposed `README.md`.
4. Adopt only with the user's approval: `lithify adopt <id>`.
5. For each mechanical-enforcement candidate the user likes, offer to add the lint rule,
   test or pre-commit hook — then the text rule can be deleted in a later compaction.
