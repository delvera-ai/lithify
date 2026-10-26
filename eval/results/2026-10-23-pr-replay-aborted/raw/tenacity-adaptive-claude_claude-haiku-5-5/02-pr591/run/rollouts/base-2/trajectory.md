# trajectory base-2

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` instead, and the full test suite passes (127 passed, 1 skipped).

- **Fix** (`tenacity/after.py`): the elapsed value is computed first. If `seconds_since_start` is `None`, it becomes `"?"`; otherwise it goes through `sec_format` as before. Custom `sec_format` values still apply to the normal case.
- **Regression test** (`tests/test_after.py`, `test_03_unset_outcome_timestamp`): sets `outcome_timestamp` to `None` and checks the logged message contains `after ?(s)`.

I didn't run the new test against the unfixed code to confirm it fails there. The original crash is a `TypeError` from `"%.3g" % None`, so it should, but that's from reading the code rather than a run.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"after_log\" -A30 tenacity/after.py | head -60; ls tests | head -50", "description": "Read after_log implementation and list tests"}
[tool_result] 29:def after_log(
30-    logger: _utils.LoggerProtocol,
31-    log_level: int,
32-    sec_format: str = "%.3g",
33-) -> typing.Callable[["RetryCallState"], None]:
34-    """After call strategy that logs to some logger the finished attempt."""
35-
36-    def log_it(retry_state: "RetryCallState") -> None:
37-        if retry_state.fn is None:
38-            # NOTE(sileht): can't really happen, but we must please mypy
39-            fn_name = "<unknown>"
40-        else:
41-            fn_name = _utils.get_callback_name(retry_state.fn)
42-        logger.log(
43-            log_level,
44-            f"Finished call to '{fn_name}' "
45-            f"after {sec_format % retry_state.seconds_since_start}(s), "
46-            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
47-        )
48-
49-    return log_it
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "cat tests/test_after.py; grep -n \"seconds_since_start\" -B3 -A3 tenacity/__init__.py", "description": "Read existing after tests and seconds_since_start usage"}
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
…[2127 chars elided]…
 self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
366-        self.iter_state.stop_run_result = self.stop(retry_state)
367-
368-    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
--
543-        self.upcoming_sleep: float = 0.0
544-
545-    @property
546:    def seconds_since_start(self) -> float | None:
547-        if self.outcome_timestamp is None:
548-            return None
549-        return self.outcome_timestamp - self.start_time
[assistant] Now the fix: render "?" when the elapsed time is unknown.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-2/tenacity/after.py", "old_string": "        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "        if retry_state.seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-2/tenacity/after.py has been updated successfully.
[assistant] Next I'll add a regression test covering the `None` case, then run the project's test command.
[tool_use Bash] {"command": "cat >> tests/test_after.py <<'EOF'\n\n    def test_03_unset_outcome_timestamp(self) -> None:\n        \"\"\"Test log formatting when seconds_since_start is None.\"\"\"\n        log = unittest.mock.MagicMock(spec=\"logging.Logger.log\")\n        logger = unittest.mock.MagicMock(spec=\"logging.Logger\", log=log)\n\n        retry_state = test_tenacity.make_retry_state(self.previous_attem
…[512 chars elided]…
, \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add regression test and run project test suite"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` instead, and the full test suite passes (127 passed, 1 skipped).

- **Fix** (`tenacity/after.py`): the elapsed value is computed first. If `seconds_since_start` is `None`, it becomes `"?"`; otherwise it goes through `sec_format` as before. Custom `sec_format` values still apply to the normal case.
- **Regression test** (`tests/test_after.py`, `test_03_unset_outcome_timestamp`): sets `outcome_timestamp` to `None` and checks the logged message contains `after ?(s)`.

I didn't run the new test against the unfixed code to confirm it fails there. The original crash is a `TypeError` from `"%.3g" % None`, so it should, but that's from reading the code rather than a run.

I haven't committed anything.
