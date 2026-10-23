# Evaluation spend ledger

Caps: pilot (3B) $25; total $150. Cost is the sum of `usage.cost` from every `outcome.json` produced, plus any role costs logged by the eval scripts. Codex and Antigravity may not report dollars: their token counts are recorded and the cost estimated (marked `est`).

| date | phase | runs | cost USD | cumulative USD | notes |
|---|---|---|---|---|---|
| 2026-10-23 | 3A sim sweep | 90 simulated | 0.00 | 0.00 | mock agent, no credentials |
| 2026-10-23 | 3B raw CLI captures | 3 (claude, codex, agy) | 0.0027 | 0.0027 | codex: 54,232 in (48,768 cached) / 126 out tokens, $ not reported; agy: quota error, 0 tokens |
| 2026-10-23 | 3B conformance claude | 1 task, k=1 | 1.8548 | 1.8575 | executions $0.033, editor roles ≈ $1.82 |
| 2026-10-23 | 3B conformance codex | 1 task, k=1 | 0.00 (est) | 1.8575 | 133,905 in / 995,584 cached / 9,937 out tokens; Codex reports no $ (ChatGPT plan) |
| 2026-10-23 | 3B pilot sequence (adaptive, claude) | 8 tasks | 4.8639 | 6.7214 | task 1 = $4.21 |
| 2026-10-23 | 3B install/hook checks | 1 claude + 4 codex sessions | 0.0029 | 6.7243 | codex sessions: small prompts, tokens not recorded |
| 2026-10-23 | 3C dev set (humanize #142, #206 × 3 strategies) | 6 tasks | 9.0344 | 15.7587 | harness debugging; found test-edit gate blocks PRs that change pinned behaviour |
| 2026-10-23 | 3C pilot humanize (10 eval PRs × 3 strategies) | 30 tasks | 22.2600 | 38.0187 | baseline 0.09, static 21.90, adaptive 0.27 |

**Pilot cap:** $25.00 — spent $6.72 (27%). **Total cap:** $150.00 — spent $38.02.
