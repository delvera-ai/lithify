You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Before the first
edit under `tenacity/`, load `tenacity-change-contract` (headings, then the sections for the area
you touch plus §2–3), not after the checks. If a comment beside the code you change says why it
is written that way, your fix must still satisfy that reason, or the final message says why not.

Done means, in this order, each with its output read. Run every pytest through
`<project python> .lithify/harness/scripts/run_tests.py [--timeout S] [node ids]`, in the
foreground (it bounds the run and names a hung test; never background pytest or watch it with
a monitor):
1. Write the regression test first and run it alone (`--timeout 60 <node id>`) against the
   unfixed code; it must fail for the reported reason (the error or wrong output the task
   describes, not an import or typo error). A task that asks for several things (a new param
   AND a new accepted type) needs one test per thing, each red for its own gap; a test that
   also uses another new part fails on that part first and proves nothing about its own.
   Then fix and re-run them green.
2. Run the full suite (`run_tests.py`, no args); read the `exit=` line and the summary line.
   `exit=124` means a test hung: follow the script's printed next step; never just re-run.
3. Run `<project python> .lithify/harness/scripts/check_changed.py` (stdlib stand-in for
   ruff/mypy). Exit 1: fix each printed file:line and re-run. Never state a line length,
   format or typing verdict from reading; quote this script. Report ruff/mypy as not run.
Do not end your turn while a check is still running; a check you have not seen finish is not
run. A successful edit or file write is not evidence. In the final message, list every step
skipped.
