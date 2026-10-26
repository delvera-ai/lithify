# trajectory inv-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the rest of the message is unchanged.

**Changes**
- **`tenacity/after.py`**: the elapsed-seconds value is `"?"` when `seconds_since_start` is `None`, and `sec_format % ...` otherwise.
- **`tests/test_after.py`**: new `TestAfterLogUnsetTimestamp` test that builds a `RetryCallState` with no outcome timestamp and checks the logged message. I also added the `RetryCallState` import it needs.
- **`releasenotes/notes/fix-after-log-unset-timestamp-31263354d941f325.yaml`**: new `fixes:` note.

**Verification**
- The new test fails on the base code with `TypeError: must be real number, not NoneType`, which is the reported bug.
- Full suite: 127 passed, 1 skipped, 12 subtests passed.
- Line-length check passes for added lines.
- I did not run mypy or ruff. They are not installed in the project interpreter, so the annotations were checked by reading only.

The worktree is uncommitted. `git status` shows the two modified files and the new release note.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\" --include='*.py' tenacity tests | head -50; cat tenacity/after.py; ls releasenotes/notes | tail -5", "description": "Locate seconds_since_start usages and after.py"}
[tool_result] tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.s
…[2311 chars elided]…
og(
            log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )

    return log_it
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "cat ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/inv-1/.claude/skills/tenacity-change-contract/SKILL.md 2>/dev/null || find . -path ./.git -prune -o -name '*.md' -print | grep -i skill; cat memory.md 2>/dev/null | head -20", "description": "Read change contract skill and find memory file"}
[tool_result] ---
name: tenacity-change-contract
description: Load before finishing any change that alters tenacity's runtime behaviour or public API (bug fix, new feature, changed default, changed log/error text) — lists the files such a change must touch in this repo (release note, regression test), the conventions they follow, and the commands that prove the change is done.
---

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check 
…[3701 chars elided]…
ntil exit 0.
3. The full suite command from `memory.md`, **last**, after every edit (a wrap or rename after
   the last run invalidates it). Quote its pass/fail counts in the final message.
4. `git status --short` — expect exactly the code file(s), the test file, and one new
   `releasenotes/notes/*.yaml` (untracked, so `git diff --stat` will not list it); no stray
   stash entries or scratch files.

Final message: what changed per file, the results of steps 1–3, and that mypy/ruff were not run.
[tool_use Bash] {"command": "cat tests/test_after.py; ls -a; ls -a .lithify 2>/dev/null; find / -name memory.md -path '*lithify*' 2>/dev/null | head -3; ls releasenotes/notes | head -3; cat releasenotes/notes/fix-local-context-overwrite-*.yaml 2>/dev/null", "description": "Read existing after_log tests and locate memory file"}
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
…[2352 chars elided]…
9d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/clean2/.lithify/harness/memory.md
<tmp>/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/plumb/raw/adaptive-mock-s0/final-harness/memory.md
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
fixes:
  - |
    Avoid overwriting local contexts when applying the retry decorator.
[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null | head -30; ls <work>/env-tenacity/bin/python; grep -n \"def make_retry_state\" -A 25 tests/test_tenacity.py", "description": "Check harness memory, project interpreter, and make_retry_state helper"}
[tool_result] - The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Behaviour-changing code changes here ship with a reno note in `releasenotes/notes/` and a regression test in `tests/`; load skill `tenacity-change-contract` before finishing such a change.
<tmp>/-Users-user-Coding-delvera-foundational-lithify/
…[620 chars elided]…
r_unset:
69-        raise _make_unset_exception(
70-            "wait/stop",
71-            previous_attempt_number=previous_attempt_number,
72-            delay_since_first_attempt=delay_since_first_attempt,
73-        )
74-
75-    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
76-    retry_state.attempt_number = previous_attempt_number
77-    if last_result is not None:
78-        retry_state.outcome = last_result
79-    else:
80-        retry_state.set_result(None)
[tool_use Bash] {"command": "sed -n 535,560p tenacity/__init__.py; grep -n \"_utils\\|^import\\|^from\" tenacity/before.py | head; grep -n \"def to_ordinal\" -B2 -A3 tenacity/_utils.py", "description": "Inspect seconds_since_start property and sibling log helpers"}
[tool_result]         self.outcome: Future | None = None
        #: Timestamp of the last outcome
        self.outcome_timestamp: float | None = None
        #: Time spent sleeping in retries
        self.idle_for: float = 0.0
        #: Next action as decided by the retry manager
        self.next_action: RetryAction | None = None
        #: Next sleep time as decided by the retry manager.
        self.upcoming_sleep: float = 0.0

    @property
    def seconds_since_start(self) -> float | None:
        if se
…[305 chars elided]…
sult(self, val: t.Any) -> None:
        ts = time.monotonic()
        fut = Future(self.attempt_number)
        fut.set_result(val)
17:import typing
19:from tenacity import _utils
30:    logger: _utils.LoggerProtocol, log_level: int
39:            fn_name = _utils.get_callback_name(retry_state.fn)
43:            f"this is the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
57-
58-
59:def to_ordinal(pos_num: int) -> str:
60-    return f"{pos_num}{find_ordinal(pos_num)}"
61-
62-
[assistant] Root cause: `after_log` formats `seconds_since_start` with `%`, and that property returns `None` when `outcome_timestamp` is unset. I'll add a `"?"` fallback in `after.py`, then a regression test and a release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/inv-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        if retry_state.seconds_since_start is None:\n            seconds = \"?\"\n        else:\n            seconds = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {seconds}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/inv-1/tenacity/after.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_after.py <<'EOF'\n\n\nclass TestAfterLogUnsetTimestamp(unittest.TestCase):\n    def test_seconds_since_start_none_logs_question_mark(self) -> None:\n        \"\"\"Test log formatting when the outcome timestamp has not been set.\"\"\"\n        log = unittest.mock.MagicMock(spec=\"logging.Logger.log\")\n        logger = unittest.mock.MagicMock(spec=\"logging.Logger\", 
…[508 chars elided]…
OF'\nimport re\np='tests/test_after.py'\ns=open(p).read()\ns=s.replace(\"from tenacity import (\\n    _utils,\\n    after_log,\\n)\",\"from tenacity import (\\n    RetryCallState,\\n    _utils,\\n    after_log,\\n)\",1)\nopen(p,'w').write(s)\nEOF\nhead -8 tests/test_after.py; grep -n \"RetryCallState\" tenacity/__init__.py | head -2", "description": "Add regression test and import RetryCallState"}
[tool_result] import logging
import random
import unittest.mock

from tenacity import (
    RetryCallState,
    _utils,
    after_log,
113:    actions: list[t.Callable[["RetryCallState"], t.Any]] = dataclasses.field(
198:    def __init__(self, retry_state: "RetryCallState"):
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python\nID=$(python3 -c \"import secrets; print(secrets.token_hex(8))\")\ncat > releasenotes/notes/fix-after-log-unset-timestamp-$ID.yaml <<'EOF'\n---\nfixes:\n  - |\n    ``after_log`` no longer raises ``TypeError`` when the retry state 
…[416 chars elided]…
-3; python3 -c \"\nimport re,subprocess\nfor l in subprocess.run(['git','diff','-U0'],capture_output=True,text=True).stdout.splitlines():\n    pass\" ; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/after.py tests/test_after.py releasenotes/notes/fix-after-log-unset-timestamp-*.yaml; git status --short", "description": "Add release note, run tests, check line lengths and status"}
[tool_result] check_line_length.py
fails_on_base.py
...                                                                      [100%]
3 passed in 0.04s
...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.78s
tenacity/after.py: 50: 93
tests/test_after.py: 51: 93
tests/test_after.py: 76: 93
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/fix-after-log-unset-timestamp-31263354d941f325.yaml
[assistant] Tests pass. The three long lines flagged are pre-existing, not from my edits. Next I'll run the contract's regression check against the base code.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python\nS=.lithify/harness/skills/tenacity-change-contract/scripts\n$P $S/fails_on_base.py tests/test_after.py::TestAfterLogUnsetTimestamp::test_seconds_since_start_none_logs_question_mark; echo \"exit $?\"; python3 $S/check_line_length.py; echo \"exit $?\"; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git status --short", "description": "Verify test fails on base and run final checks"}
[tool_result] _ TestAfterLogUnsetTimestamp.test_seconds_since_start_none_logs_question_mark __

self = <tests.test_after.TestAfterLogUnsetTimestamp testMethod=test_seconds_since_start_none_logs_question_mark>

    def test_seconds_since_start_none_logs_question_mark(self) -> None:
        """Test log formatting when the outcome timestamp has not been set."""
        log = unittest.mock.MagicMock(spec="logging.Logger.log")
        logger = unittest.mock.MagicMock(spec="logging.Logger", log=log)
    
        re
…[1138 chars elided]…
45: TypeError
=========================== short test summary info ============================
FAILED tests/test_after.py::TestAfterLogUnsetTimestamp::test_seconds_since_start_none_logs_question_mark
1 failed in 0.06s
---
GOOD: tests FAIL on HEAD. Confirm the failure reason above.
exit 0
OK: no added .py line over 88 chars
exit 0
127 passed, 1 skipped, 12 subtests passed in 2.26s
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/fix-after-log-unset-timestamp-31263354d941f325.yaml
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the rest of the message is unchanged.

**Changes**
- **`tenacity/after.py`**: the elapsed-seconds value is `"?"` when `seconds_since_start` is `None`, and `sec_format % ...` otherwise.
- **`tests/test_after.py`**: new `TestAfterLogUnsetTimestamp` test that builds a `RetryCallState` with no outcome timestamp and checks the logged message. I also added the `RetryCallState` import it needs.
- **`releasenotes/notes/fix-after-log-unset-timestamp-31263354d941f325.yaml`**: new `fixes:` note.

**Verification**
- The new test fails on the base code with `TypeError: must be real number, not NoneType`, which is the reported bug.
- Full suite: 127 passed, 1 skipped, 12 subtests passed.
- Line-length check passes for added lines.
- I did not run mypy or ruff. They are not installed in the project interpreter, so the annotations were checked by reading only.

The worktree is uncommitted. `git status` shows the two modified files and the new release note.
