# trajectory base-2

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the project suite passes (127 passed, 1 skipped).

The cause was in `tenacity/after.py`: the log message applied `%` formatting to `seconds_since_start` unconditionally, and `None % "%.3g"` raises `TypeError`. The fix formats the elapsed time only when it is set and uses `"?"` otherwise. Normal output is unchanged.

I also added `test_03_seconds_since_start_none` to `tests/test_after.py`. It sets `outcome_timestamp` to `None`, then checks that the log call contains `after ?(s)`. I did not run it against the unfixed code to confirm it fails there.

I have not committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\" --include=*.py . | head -30 && grep -n \"after_log\" -A30 tenacity/after.py | head -60", "description": "Locate after_log and seconds_since_start usages"}
[tool_result] (eval):1: no matches found: --include=*.py
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
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\" tenacity/ tests/ | head; grep -n \"after_log\" -B3 -A25 tests/test_tenacity.py | head -80; ls tests", "description": "Find seconds_since_start and after_log tests"}
[tool_result] tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.seconds_since_start is None:
tenacity/stop.py:126:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:128:            retry_state.seconds
…[50 chars elided]…
/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/asyncio/__init__.py:146:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "cat tests/test_after.py; cat tenacity/after.py | head -28; git status --short", "description": "Read after tests and module header"}
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
…[2351 chars elided]…
w or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import typing

from tenacity import _utils

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


def after_nothing(retry_state: "RetryCallState") -> None:
    """After call strategy that does nothing."""
[tool_use Bash] {"command": "sed -n 540,556p tenacity/__init__.py; grep -n \"def make_retry_state\" -A22 tests/test_tenacity.py", "description": "Inspect seconds_since_start and test helper"}
[tool_result]         #: Next action as decided by the retry manager
        self.next_action: RetryAction | None = None
        #: Next sleep time as decided by the retry manager.
        self.upcoming_sleep: float = 0.0

    @property
    def seconds_since_start(self) -> float | None:
        if self.outcome_timestamp is None:
            return None
        return self.outcome_timestamp - self.start_time

    def prepare_for_next_attempt(self) -> None:
        self.outcome = None
        self.outcome_times
…[520 chars elided]…
tempt_number is _unset or delay_since_first_attempt is _unset
67-    )
68-    if required_parameter_unset:
69-        raise _make_unset_exception(
70-            "wait/stop",
71-            previous_attempt_number=previous_attempt_number,
72-            delay_since_first_attempt=delay_since_first_attempt,
73-        )
74-
75-    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
76-    retry_state.attempt_number = previous_attempt_number
77-    if last_result is not None:
[assistant] I have the cause: `after_log` formats `seconds_since_start` with `%` unconditionally, so a `None` value raises `TypeError`. I'll fix that and add a regression test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-2/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        if retry_state.seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-2/tenacity/after.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-2/tests/test_after.py", "old_string": "        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)\n        fun(retry_state)\n        fn_name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            els
…[1528 chars elided]…
me = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-2/tests/test_after.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the project suite passes (127 passed, 1 skipped).

The cause was in `tenacity/after.py`: the log message applied `%` formatting to `seconds_since_start` unconditionally, and `None % "%.3g"` raises `TypeError`. The fix formats the elapsed time only when it is set and uses `"?"` otherwise. Normal output is unchanged.

I also added `test_03_seconds_since_start_none` to `tests/test_after.py`. It sets `outcome_timestamp` to `None`, then checks that the log call contains `after ?(s)`. I did not run it against the unfixed code to confirm it fails there.

I have not committed anything.
