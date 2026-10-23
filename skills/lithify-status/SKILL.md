---
name: lithify-status
description: Report the state of this repository's self-improving harness — stability score, phase, next exploration width k, cost history, library lessons and pending harness proposals. Use when the user asks how lithify or the harness is doing, or says /lithify-status.
---

# Report lithify status

1. Run `lithify status` and `lithify report`.
2. Summarise in a few lines:
   - stability S and phase (genesis = still exploring widely, build = one contrastive step per
     task, cruise = single execution, escalating only on a gate failure);
   - the k the next task will use and why (including any anomaly spike);
   - the cost trend from the report (tokens per task should fall as S rises);
   - always-on harness size versus budget — suggest the `lithify-compact` skill if over;
   - pending proposals, if any, and that `lithify adopt --list` shows them.
3. If the user wants detail on what the harness has learned, read `.lithify/library/INDEX.md`
   and the relevant `EXPERIENCE.md` entries, and summarise the lessons with their verdicts.
