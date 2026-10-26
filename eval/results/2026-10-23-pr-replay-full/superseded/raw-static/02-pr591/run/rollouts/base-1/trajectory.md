# trajectory base-1

final message:
`after_log` no longer crashes when `retry_state.seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/after.py`**: the elapsed-seconds value is formatted only when it is set. Otherwise it is `?`.
- **`tests/test_after.py`**: new `TestAfterLogUnsetTimestamp` test. It sets `outcome_timestamp` to `None`, checks that the log line reads `after ?(s)`, and fails on the old code (verified by temporarily stashing the fix).
- **`releasenotes/notes/fix-after-log-unset-timestamp-3c1f9a7e2b5d8e41.yaml`**: a `fixes:` note describing the change.

I did not run mypy or ruff. The project interpreter doesn't have them installed. I checked by hand that the new code is annotated and within 88 columns.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\\|def after_log\" --include='*.py' tenacity tests | head -50; cat tenacity/after.py", "description": "Locate after_log and seconds_since_start usages"}
[tool_result] tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.seconds_since_start is None:
tenacity/stop.py:126:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:128:            retry_state.seconds
…[2114 chars elided]…
      if retry_state.fn is None:
            # NOTE(sileht): can't really happen, but we must please mypy
            fn_name = "<unknown>"
        else:
            fn_name = _utils.get_callback_name(retry_state.fn)
        logger.log(
            log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )

    return log_it
[tool_use Bash] {"command": "cat tests/test_after.py; sed -n 1,60p tests/test_after.py >/dev/null; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | grep -v placeholder | tail -1); git log --oneline -3 -- releasenotes/notes | cat", "description": "Read existing after_log tests and release note examples"}
[tool_result] import logging
import random
import unittest.mock

from tenacity import (
    _utils,
    after_log,
)

from . import test_tenacity


class TestAfterLogFormat(unittest.TestCase):
    def setUp(self) -> None:
        self.log_level = random.choice(
            (
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            )
        )
        self.previous_attempt_number = random.randint(1
…[2057 chars elided]…
lta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
d4e868d Fix `retry()` annotations with async `sleep=` function (#555)
24415eb support async sleep for sync fn (#551)
3bf33b4 chore: drop Python 3.9 support (EOL) (#552)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/tenacity/__init__.py", "offset": 530, "limit": 30}
[tool_result] 530	        self.kwargs = kwargs
531	
532	        #: The number of the current attempt
533	        self.attempt_number: int = 1
534	        #: Last outcome (result or exception) produced by the function
535	        self.outcome: Future | None = None
536	        #: Timestamp of the last outcome
537	        self.outcome_timestamp: float | None = None
538	        #: Time spent sleeping in retries
539	        self.idle_for: float = 0.0
540	        #: Next action as decided by the retry manager
541	 
…[211 chars elided]…
art(self) -> float | None:
547	        if self.outcome_timestamp is None:
548	            return None
549	        return self.outcome_timestamp - self.start_time
550	
551	    def prepare_for_next_attempt(self) -> None:
552	        self.outcome = None
553	        self.outcome_timestamp = None
554	        self.attempt_number += 1
555	        self.next_action = None
556	
557	    def set_result(self, val: t.Any) -> None:
558	        ts = time.monotonic()
559	        fut = Future(self.attempt_number)
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[1826 chars elided]…
m; write
  code that satisfies the rules above by inspection, and say in the final message that
  they were not run.
- **Shared helpers in `tenacity/_utils.py` feed user-visible text.** `to_ordinal` /
  `find_ordinal` build the "Nth time calling it" messages in `tenacity/before.py` and
  `tenacity/after.py`, and `tests/test_after.py` computes its expected strings through
  `_utils.to_ordinal`. Fix such helpers in `_utils.py` itself (not at call sites), and test the
  helper directly in `tests/test_utils.py` — the logging tests will not catch a wrong helper
  because they call the same helper.

[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A 25 tests/test_tenacity.py; ls releasenotes/notes | grep -i fix | head -3; cat releasenotes/notes/$(ls releasenotes/notes | grep -i '^fix' | head -1)", "description": "Inspect test helper and an existing fix release note"}
[tool_result] 55:def make_retry_state(
56-    previous_attempt_number: typing.Any,
57-    delay_since_first_attempt: typing.Any,
58-    last_result: typing.Any = None,
59-    upcoming_sleep: typing.Any = 0,
60-) -> RetryCallState:
61-    """Construct RetryCallState for given attempt number & delay.
62-
63-    Only used in testing and thus is extra careful about timestamp arithmetics.
64-    """
65-    required_parameter_unset = (
66-        previous_attempt_number is _unset or delay_since_first_attempt is _un
…[246 chars elided]…
t,
73-        )
74-
75-    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
76-    retry_state.attempt_number = previous_attempt_number
77-    if last_result is not None:
78-        retry_state.outcome = last_result
79-    else:
80-        retry_state.set_result(None)
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
fix-async-loop-with-result-f68e913ccb425aca.yaml
fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
---
fixes:
  - "Fixes test failures with typeguard 3.x"
[assistant] Now the fix, the regression tests, and the release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "        seconds_since_start = retry_state.seconds_since_start\n        seconds = \"?\" if seconds_since_start is None else sec_format % seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {seconds}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_after.py <<'EOF'\n\n\nclass TestAfterLogUnsetTimestamp(unittest.TestCase):\n    def test_seconds_since_start_none_logs_question_mark(self) -> None:\n        \"\"\"Log a '?' elapsed time instead of crashing when the timestamp is unset.\"\"\"\n        log = unittest.mock.MagicMock(spec=\"logging.Logger.log\")\n        logger = unittest.mock.MagicMock(spec=\"logging.Log
…[977 chars elided]…
`` in place of the elapsed seconds.\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_after.py 2>&1 | tail -5; git stash list | head -0; git diff --stat", "description": "Append regression test, add release note, run after_log tests"}
[tool_result] ...                                                                      [100%]
3 passed in 0.04s
head: illegal line count -- 0
 tenacity/after.py   |  4 +++-
 tests/test_after.py | 26 ++++++++++++++++++++++++++
 2 files changed, 29 insertions(+), 1 deletion(-)
[assistant] Targeted tests pass. Next I'll confirm the new test fails on the old code, check line lengths, and run the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; git stash push -q -m \"after-log-check\" -- tenacity/after.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_after.py 2>&1 | tail -2; git stash list --format='%H %gs' | grep after-log-check | cut -d' ' -f1 | xargs -I{} git stash apply -q {}; git stash list --format='%H %gs' | grep after-log-check | cut -d' ' -f1 | xargs -I{} git stash drop -q {}; git diff --stat | tail -1; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/after.py; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Verify test fails on old code, restore fix, run full suite"}
[tool_result] FAILED tests/test_after.py::TestAfterLogUnsetTimestamp::test_seconds_since_start_none_logs_question_mark
1 failed, 2 passed in 0.02s
error: '10f9f0be2a9c9dfbe8134389493fbcae995b711f' is not a stash reference
 2 files changed, 29 insertions(+), 1 deletion(-)
tenacity/after.py: 43: 90
tenacity/after.py: 48: 93
...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] The stash round-trip printed an error, so I need to check the working tree and stash list directly before trusting the result.
[tool_use Bash] {"command": "git stash list --format='%H %gs' | head; echo ---; git status --short; echo ---; grep -n \"seconds_since_start is None\" tenacity/after.py; echo; git diff tenacity/after.py", "description": "Check stash list, status, and after.py fix state"}
[tool_result] 10f9f0be2a9c9dfbe8134389493fbcae995b711f On (no branch): after-log-check
---
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/fix-after-log-unset-timestamp-3c1f9a7e2b5d8e41.yaml
---
43:        seconds = "?" if seconds_since_start is None else sec_format % seconds_since_start

diff --git a/tenacity/after.py b/tenacity/after.py
index a4b8922..10cbeb9 100644
--- a/tenacity/after.py
+++ b/tenacity/after.py
@@ -39,10 +39,12 @@ def after_log(
             fn_name = "<unknown>"
       
…[34 chars elided]…
ils.get_callback_name(retry_state.fn)
+        seconds_since_start = retry_state.seconds_since_start
+        seconds = "?" if seconds_since_start is None else sec_format % seconds_since_start
         logger.log(
             log_level,
             f"Finished call to '{fn_name}' "
-            f"after {sec_format % retry_state.seconds_since_start}(s), "
+            f"after {seconds}(s), "
             f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
         )
[assistant] The fix is in the working tree and the stash entry is still there. I'll compare the stash's copy against the working tree before dropping it.
[tool_use Bash] {"command": "SHA=10f9f0be2a9c9dfbe8134389493fbcae995b711f; git diff --quiet $SHA -- tenacity/after.py && echo \"stash after.py == working tree\"; git show $SHA --stat | tail -3", "description": "Compare stashed after.py with working tree"}
[tool_result] stash after.py == working tree

 tenacity/after.py | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "REF=$(git stash list --format='%gd %H' | grep 10f9f0be | cut -d' ' -f1); echo \"$REF\"; git stash drop -q \"$REF\" && git stash list | wc -l; git status --short", "description": "Drop the temporary stash entry by its ref"}
[tool_result] stash@{0}
       0
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/fix-after-log-unset-timestamp-3c1f9a7e2b5d8e41.yaml
[assistant] My new line 43 is 90 characters, over the 88 limit. I'll wrap it and rerun the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "        seconds = \"?\" if seconds_since_start is None else sec_format % seconds_since_start", "new_string": "        if seconds_since_start is None:\n            seconds = \"?\"\n        else:\n            seconds = sec_format % seconds_since_start"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Wrap long line and run full test suite"}
[tool_result] ....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] `after_log` no longer crashes when `retry_state.seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/after.py`**: the elapsed-seconds value is formatted only when it is set. Otherwise it is `?`.
- **`tests/test_after.py`**: new `TestAfterLogUnsetTimestamp` test. It sets `outcome_timestamp` to `None`, checks that the log line reads `after ?(s)`, and fails on the old code (verified by temporarily stashing the fix).
- **`releasenotes/notes/fix-after-log-unset-timestamp-3c1f9a7e2b5d8e41.yaml`**: a `fixes:` note describing the change.

I did not run mypy or ruff. The project interpreter doesn't have them installed. I checked by hand that the new code is annotated and within 88 columns.
