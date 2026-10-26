# trajectory base-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the full test suite passes (127 passed, 1 skipped).

**Cause:** `after_log` formatted `retry_state.seconds_since_start` directly with `sec_format % ...`. That property returns `None` when `outcome_timestamp` is unset, so `%` raised a `TypeError`.

**Changes:**
- `tenacity/after.py`: compute `elapsed` as `"?"` when the value is `None`, otherwise `sec_format % seconds`, and use it in the message. The normal output is unchanged.
- `tests/test_after.py`: added `test_03_seconds_since_start_unset`, which sets `outcome_timestamp = None` and checks for `after ?(s), `. I did not touch the existing tests.

Changes are uncommitted in the worktree. I didn't commit or push.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\" --include=*.py . | grep -v \"^./.git/\" ; echo ---; grep -n \"def after_log\" -A 40 tenacity/after.py", "description": "Locate seconds_since_start usages and after_log"}
[tool_result] (eval):1: no matches found: --include=*.py
---
29:def after_log(
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
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\" tenacity tests docs 2>/dev/null; echo ---; grep -n \"seconds_since_start\" -B3 -A8 tenacity/__init__.py | head -40; echo ---; grep -n \"after_log\" -A30 tests/test_tenacity.py | head -80; echo; ls tests", "description": "Find seconds_since_start definition and after_log tests"}
[tool_result] tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.seconds_since_start is None:
tenacity/stop.py:126:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:128:            retry_state.seconds
…[1542 chars elided]…
t = 0.0
544-
545-    @property
546:    def seconds_since_start(self) -> float | None:
547-        if self.outcome_timestamp is None:
548-            return None
549-        return self.outcome_timestamp - self.start_time
550-
551-    def prepare_for_next_attempt(self) -> None:
552-        self.outcome = None
553-        self.outcome_timestamp = None
554-        self.attempt_number += 1
---

__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "cat tests/test_after.py; echo ---; git status --short; ls <work>/env-tenacity/bin/python 2>&1", "description": "Read existing after_log tests and check env"}
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
…[1654 chars elided]…
lse _utils.get_callback_name(retry_state.fn)
        )
        log.assert_called_once_with(
            self.log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )
---
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 35,60p tests/test_tenacity.py", "description": "Read make_retry_state helper"}
[tool_result] _unset = object()


def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
    missing = []
    for k, v in kwargs.items():
        if v is _unset:
            missing.append(k)
    missing_str = ", ".join(repr(s) for s in missing)
    return TypeError(func_name + " func missing parameters: " + missing_str)


def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
    # Ensure outcome_timestamp - start_time is *exactly* equal to the delay to
    # avoid complexity in test code.
    retry_state.start_time = Fraction(retry_state.start_time)  # type: ignore[assignment]
    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
    assert retry_state.seconds_since_start == delay


def make_retry_state(
    previous_attempt_number: typing.Any,
    delay_since_first_attempt: typing.Any,
    last_result: typing.Any = None,
    upcoming_sleep: typing.Any = 0,
) -> RetryCallState:
[assistant] Root cause: `after_log` formats `seconds_since_start` directly with `%`, and that property returns `None` when `outcome_timestamp` is unset. I'll fix `after.py` to fall back to `"?"`, and add a test for that case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        seconds = retry_state.seconds_since_start\n        elapsed = \"?\" if seconds is None else sec_format % seconds\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)\n        fun(retry_state)\n        fn_name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            els
…[1474 chars elided]…
ame = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            \"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155039-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.80s
[tool_use Bash] {"command": "git diff --stat && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_after.py -k unset 2>&1 | tail -2", "description": "Show diff stats and rerun the new test"}
[tool_result]  tenacity/after.py   |  4 +++-
 tests/test_after.py | 21 +++++++++++++++++++++
 2 files changed, 24 insertions(+), 1 deletion(-)
.                                                                        [100%]
1 passed, 2 deselected in 0.01s
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the full test suite passes (127 passed, 1 skipped).

**Cause:** `after_log` formatted `retry_state.seconds_since_start` directly with `sec_format % ...`. That property returns `None` when `outcome_timestamp` is unset, so `%` raised a `TypeError`.

**Changes:**
- `tenacity/after.py`: compute `elapsed` as `"?"` when the value is `None`, otherwise `sec_format % seconds`, and use it in the message. The normal output is unchanged.
- `tests/test_after.py`: added `test_03_seconds_since_start_unset`, which sets `outcome_timestamp = None` and checks for `after ?(s), `. I did not touch the existing tests.

Changes are uncommitted in the worktree. I didn't commit or push.
