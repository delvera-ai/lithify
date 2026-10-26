# trajectory base-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full test suite passes: 127 passed, 1 skipped.

**The fix** (`tenacity/after.py`): the elapsed value is computed first. It is `"?"` when `seconds_since_start` is `None`, and `sec_format % seconds` otherwise. The log message format is unchanged in every other case.

**The test** (`tests/test_after.py`, `test_03_seconds_since_start_unset`): it builds a retry state with `outcome_timestamp = None`, then checks that the logger is called once with `after ?(s), ...`. The test passes with the fix. I did not run it against the original code to confirm it fails there.

The changes are uncommitted in the worktree. I did not commit them, since you only asked for the fix.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\\|def after_log\" tenacity/ | head -30; sed -n '1,40p' tenacity/after.py", "description": "Locate after_log and seconds_since_start usages"}
[tool_result] tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.s
…[1274 chars elided]…
e") -> None:
    """After call strategy that does nothing."""


def after_log(
    logger: _utils.LoggerProtocol,
    log_level: int,
    sec_format: str = "%.3g",
) -> typing.Callable[["RetryCallState"], None]:
    """After call strategy that logs to some logger the finished attempt."""

    def log_it(retry_state: "RetryCallState") -> None:
        if retry_state.fn is None:
            # NOTE(sileht): can't really happen, but we must please mypy
            fn_name = "<unknown>"
        else:
[tool_use Bash] {"command": "sed -n '40,60p' tenacity/after.py; sed -n '535,560p' tenacity/__init__.py; ls tests | head -50; grep -n \"after_log\" -A3 tests/*.py | head -60", "description": "View after_log body, seconds_since_start, and existing tests"}
[tool_result]         else:
            fn_name = _utils.get_callback_name(retry_state.fn)
        logger.log(
            log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )

    return log_it
        self.outcome: Future | None = None
        #: Timestamp of the last outcome
        self.outcome_timestamp: float | None = None
   
…[1024 chars elided]…
t test_tenacity
--
tests/test_after.py:37:        fun = after_log(
tests/test_after.py-38-            logger=logger, log_level=self.log_level
tests/test_after.py-39-        )  # use default sec_format
tests/test_after.py-40-        fun(retry_state)
--
tests/test_after.py:64:        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)
tests/test_after.py-65-        fun(retry_state)
tests/test_after.py-66-        fn_name = (
tests/test_after.py-67-            "<unknown>"
[tool_use Bash] {"command": "cat tests/test_after.py", "description": "Read existing after_log tests"}
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
…[1495 chars elided]…
self.log_level, sec_format=sec_format)
        fun(retry_state)
        fn_name = (
            "<unknown>"
            if retry_state.fn is None
            else _utils.get_callback_name(retry_state.fn)
        )
        log.assert_called_once_with(
            self.log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )
[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A25 tests/test_tenacity.py", "description": "Inspect make_retry_state test helper"}
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
…[40 chars elided]…
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
[assistant] Now the fix in `after_log`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-185653-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        if retry_state.seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-185653-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully.
[assistant] Next, a regression test covering the `None` case, following the existing test style:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-185653-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)\n        fun(retry_state)\n        fn_name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            els
…[1553 chars elided]…
name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-185653-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll run the project's test command, using the interpreter the CLAUDE.md specifies. I'll also confirm the new test fails without the fix.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -q -p no:cacheprovider --color=no tests/test_after.py 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run after-log tests and full suite with project interpreter"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Unknown option: -p
usage: <work>/env-tenacity/bin/python [option] ... [-c cmd | -m mod | file | -] [arg] ...
Try `python -h' for more information.
...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] The full suite passes (127 passed, 1 skipped). My first command was a typo (`python -q` instead of `python -m pytest -q`), so I'll rerun the new test in isolation and check the diff.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_after.py -k \"test_03\" 2>&1 | tail -3; git diff --stat", "description": "Run new test in isolation and show diff stats"}
[tool_result] .                                                                        [100%]
1 passed, 2 deselected in 0.01s
 tenacity/after.py   |  6 +++++-
 tests/test_after.py | 25 +++++++++++++++++++++++++
 2 files changed, 30 insertions(+), 1 deletion(-)
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full test suite passes: 127 passed, 1 skipped.

**The fix** (`tenacity/after.py`): the elapsed value is computed first. It is `"?"` when `seconds_since_start` is `None`, and `sec_format % seconds` otherwise. The log message format is unchanged in every other case.

**The test** (`tests/test_after.py`, `test_03_seconds_since_start_unset`): it builds a retry state with `outcome_timestamp = None`, then checks that the logger is called once with `after ?(s), ...`. The test passes with the fix. I did not run it against the original code to confirm it fails there.

The changes are uncommitted in the worktree. I did not commit them, since you only asked for the fix.
