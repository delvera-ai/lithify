# Round-2 environment and cost calibration

All requested zero-token checks and one completed calibration are recorded.
No replicates were started. Round-2 ledger total: **$3.6681**, including
$3.6267 from the earlier environment-invalid replicate; **$26.3319** remains
under the $30 Phase-0 cap. Dollar figures are CLI estimates, not invoice data.

## Environment and oracle checks

The baseline's surviving session logs identify Claude Code **2.1.310**, rather
than the stale 2.1.309 in eval/ENVIRONMENT.md. The owner approved matching
2.1.310. It is pinned run-locally, with recorded Node 24.15.0/npm 11.12.1;
runner Python is 3.14.4 from the project venv. Repository tests use the absolute
Python 3.12.13 venv created under eval/repos.py's existing policy. Its bin is
also on PATH, fixing test_lazy_load's internal bare-python subprocess.
See ../../round2/ENVIRONMENT_PARITY.md and run-environment.json.

**60/60 original tasks** fail their hidden tests at base, pass at merge, and
pass the full repository suite at merge. No fixes/exclusions. Evidence:
../2026-10-27-r2-preflight/oracle.csv and its REPORT.md/logs. All checks cost $0.

## Single calibration: sqlglot#7492

Installed non-editable product **38bae7919ebc290dd8da5a2e0ad601a40e7630d1**,
with the fixed adapter from PR #31. Task text is unchanged. Baseline k=0,
no escalation, one execution. Gates and hidden tests pass; safety invariants
are clean (SAFETY.json). CLI version and reported model identifier match A1.
An identical backend model snapshot is not established by a matching identifier.

| measure | round-1 A task 1 | calibration |
|---|---:|---:|
| CLI version | 2.1.310 | 2.1.310 |
| reported model | claude-haiku-5-5 | claude-haiku-5-5 |
| estimated USD, unrounded evidence | 0.02944021 | 0.04137888 |
| unique assistant API calls | 22 | 40 |
| input tokens (without cache) | 44 | 82 |
| cache-write tokens | 52,106 | 57,105 |
| cache-read tokens | 1,083,661 | 2,197,168 |
| output tokens | 16,356 | 15,956 |
| context min / median / max | 32,289 / 53,195.5 / 63,442 | 34,352 / 56,877.5 / 68,441 |
| recorded wall seconds | 175.5 | 2,705.6 |

The ratio to the owner's **recorded $0.0294** reference is **1.40744×**,
below the 3× ($0.0882) stopping threshold. The original unrounded cost and
model accounting were recovered from its cost-state record, without changing
the original CSV. Calibration modelUsage attributes all $0.04137888 to
claude-haiku-5-5 (canonical model same, firstParty provider, list cost basis);
no other model is reported. This is reported client-side model accounting,
not independent verification of an invoice or immutable backend model build.

Calibration has **40 reported turns**, split **32 + 3 + 3 + 2** across four
result events. The original result-level turn count was not archived; its
22 unique assistant API calls are reconstructed from the local session log.
Every call's context and reported usage are in **per-call-context.csv**;
comparison.json contains the original and calibration evidence. Streaming
per-call output counts may be placeholders; aggregate outputs above come from
result usage and are corroborated by modelUsage.

Recorded wall time is 45.1 minutes versus 2.9 minutes originally. The raw
stream shows repeated background suite execution/notifications and long gaps;
the final cumulative API duration is 134.645 seconds. The reason for the
full timing gap is not established. Do not extrapolate one run into a reliable
mean time or budget. The final deterministic gate itself took 47.6 seconds.

## What the adapter evidence establishes

Four result events have per-turn usage but cumulative cost/modelUsage. Their
cumulative USD values are .03391860, .03661357, .03957841, .04137888.
Adding them would falsely report **$0.15148946**. Correct cost is the final
cumulative total, while per-turn token usage is summed. The old adapter's
last-result-only usage would report just 1,446 input/cache-write, 135,117
cache-read, and 321 output tokens; its dollar total would still be correct
for this successful session. The fix also retains earlier costs after zeroed
crash results and archives executor/role stream-json as gzip.

This follows [Anthropic's documented accounting scopes](https://code.claude.com/docs/en/agent-sdk/cost-tracking#track-costs-in-streaming-input-mode).
Raw redacted gzip plus per-session metadata are under
raw/calibration-A1/01-pr7492/run/sessions/. Original raw streams remain in the
scratch run. The actual four-result capture is now a regression fixture in
PR #31, alongside the original 2.1.309 and real 2.1.310 limit fixtures.

## Round-1 notification audit

199/199 archived rollouts matched local session logs. Final turns responding
to task notifications: **A 2/60, B 3/65, C 0/74**. Treat historical costs as
conservative lower bounds, but notification endings do not prove missing
money: every archived rollout cost matches its final cumulative cost-state
within rounding. Editor-role costs and invoices were not checked. Details:
../../round2/ROUND1_SESSION_AUDIT.json; updated eval/REVIEW_SUMMARY.md.

## Deviations, limits and next decision

The initial calibration launch was refused at a CLI limit: zero tokens and $0.
The runner misclassified it as a failure. That row/stream are preserved under
invalid-limit-1 and excluded. The notice detector and dropped CLI-budget
serialization were fixed with regression tests before a single permitted
resume. AUTO_RESUMES.json records one resume on 2026-10-27 UTC; no completed
task was repeated. The completed run had explicit runner cap $2, serialized
CLI cap $1.50, aggregate cap $30, and budget glob *-r2-*. See DEVIATIONS.md.

The requested version/model-identifier mismatch condition is not observed
for the completed baseline calibration. Cost is below 3×, but one task is
not a noise estimate or an estimate of B/E/editor-role costs. No task subset,
pre-registration decision, phase budget, or main-run design was changed.
No further run is launched. Phase 0 noise replication/reanalysis remains
unfinished and requires the owner's next instruction after this report.
