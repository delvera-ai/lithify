# Owner-requested A2 recovery — 2026-10-28

The owner requested continuation after the interruption report. Resume A2 at task 22, retaining positions 1–21. The historical cause and actual second-request bill remain unresolved; the original audit is preserved unchanged.

The known $0.0039429 interruption estimate plus a $0.10 conservative hold are included in A2 run_cost and round-only phase accounting. The hold is encumbered budget, not observed spend. RECOVERY.json records the bound: second request max output 128,000; previous prompt 32,206 tokens plus 16,431 overcounted UTF-8 bytes of new transcript events, below 100k. Pricing all prompt tokens as 1h cache writes plus maximum output gives $0.0737274; the $0.10 hold covers that request. Keep the hold until actual billing is established; replace it rather than adding it twice. All original caps and strict tripwires remain unchanged.

A complete local tar archive preserves the original clone, checkpoint, carried state and task-22 probe before reset; its hash is recorded. The original checkpoint is separately retained. Product sources byte-match the 89020d7 manifest, and all frozen PR/task hashes match. The recovery changes evaluation supervision only.

Launch with the pinned env-r2-replicates Python and the existing original --work/--out/--python/--product-commit arguments plus --resume-a2, through eval/round2/supervise_a_replicates.py. The supervisor is detached with no terminal/stdin or inherited tool pipes, holds an exclusive local lock, records SUPERVISOR.json, redirects console output locally, and never restarts a failed launcher. The launcher records CHILD_EXITS.jsonl. Existing CLI-limit-only resumes retain their maximum three/run/UTC-day allowance. Crash, budget and tripwire stops require review.

A2 completes before A3–A5 run sequentially with independent clone/state. The launcher stops after A5; B requires its original affordability assessment. No Phase-1 work is authorized here.

Validation: ruff check, format check, mypy, pytest, diff whitespace check, gzip-aware evidence leak scan. Zero-token supervisor simulation persisted exit 76 and refused duplicate launch without changing its prior exit record. Main checkout remains unchanged.
