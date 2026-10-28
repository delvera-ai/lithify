# A2 interruption audit — 2026-10-28

Status: interrupted; no paid calls or restart during this audit. A3–A5 and B remain unstarted. Source HEAD e0e63f3; product build 89020d7. Main checkout unchanged.

21/60 outcomes remain valid: 14 hidden-test passes, 0 recorded timeouts, $0.7704 completed-task spend, mean $0.0366857/task, median wall 225.0 s. No statistical conclusion is drawn. Neither completed-task tripwire fired.

## Evidence and remaining uncertainty

The log and task-22 run directory start at 2026-10-27 22:36:40 UTC (00:36:40 local Oct 28). The run directory is empty; exported task-22 evidence contains only task.md. Claude session 5d9f8933-cf74-4073-832c-d9ec65414113 records an API request at 22:36:41.711Z, a model response at 22:36:43.705Z/44.330Z, a tool result, and a second API request at 22:36:44.945Z. It ends without a response to that second request, result event, cost-state or exit reason. Original session SHA-256 and redacted compressed transcript are preserved in interruptions/r1-A-rep2/22-crash-audit/.

No wrapper, replay runner or evaluation Claude process remains. Historical unified-exec session 31910 is unavailable; the daemon log confirms Unknown process id at 2026-10-28T06:17:24.681520Z. The historical launch used a foreground unified-exec session and pipes through the wrapper. There is no persisted child exit code, signal, traceback, A_PROGRESS or A_SUMMARY from that launch. This is an unexplained process disappearance, not an established CLI-limit, budget or timeout stop. Parent/session teardown is a plausible failure mode, not a proven cause. The wrapper only writes its final summary after the child exits and has no interruption handler; loss of the wrapper can leave its ledger status stale.

Scratch sqlglot PIDs 8737 and 8944–8953 have PPID 1, PGID 8720; cwd identifies A2 task 14 (#7550), started 17:35:49/54 local Oct 27. They predate task 22 and are orphaned earlier-task workers. No workers or unrelated Tenacity/Claude sessions were touched. Their existence does not establish why task 22 stopped or explain the earlier long inactive gaps.

## Partial accounting

Two assistant blocks share one message ID and identical usage: count once. Observed usage: 2 input, 18,264 one-hour cache-write, 13,940 cache-read, 301 output tokens (thinking included). Pinned CLI 2.1.310's local haiku_55 price table yields **$0.00394290** for that one response. This is a reconstructed local CLI estimate, not an invoice or complete task cost. Context is 32,206, below its 100k long-context boundary. There are no cumulative billing snapshots to sum. The second API request has unknown billed usage; the known amount is a lower bound.

Separate results-interrupted.csv charges that amount once to budget accounting, without adding a fake task outcome. Known A2 total >= $0.77434290; round-2 total >= **$4.44244290**, including invalid runs and calibration. Paid work remains blocked on unknown second-request usage; $4.4385 was only the previously recorded total.

## Resume verification and proposed recovery

Read-only checks confirm progress next_pos=22, 21 audit entries, CSV positions exactly 1–21 and matching run_cost=$0.7704. pr_replay.py --resume reads this checkpoint, skips positions <22, appends retained CSV rows, and restores carried state with save=False. It reuses the clone, but resets/cleans its working tree; it does not continue the interrupted Claude session. Both scratch clone and task-22 probe currently have clean tracked working trees. The carried state and interruption checkpoint are archived here before any reset. The A-replicate wrapper itself intentionally refuses an existing run directory and cannot simply be rerun.

Before recovery: reconcile second-request billing or establish a conservative owner-approved reservation; preserve the current scratch/probe snapshot before any reset; include the interrupted charge in A2's own run_cost (current checkpoint excludes it) and the phase cap. Then prepare an explicit single-A2 --resume invocation with the exact original environment, 89020d7 build, all original flags/caps/tripwires, and a durable supervisor that persists exit status. Review this recovery before any paid launch. Do not rewrite prior outcomes or the original checkpoint silently. A3–A5 follow only after A2 finishes and review permits continuation.
