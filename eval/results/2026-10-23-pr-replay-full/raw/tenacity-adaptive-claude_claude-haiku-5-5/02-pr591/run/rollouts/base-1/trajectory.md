# trajectory base-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes: 127 passed, 1 skipped.

**Cause:** `log_it` in `tenacity/after.py` applied `sec_format % retry_state.seconds_since_start` unconditionally. That property returns `None` until an outcome timestamp is set, so the `%` formatting raised `TypeError`.

**Fix:** `tenacity/after.py` now checks for `None` first and uses `"?"`. Otherwise it formats the value with `sec_format` as before. The message text is unchanged apart from that placeholder.

**Test:** I added `test_03_seconds_since_start_unset` to `tests/test_after.py`. It builds a retry state with no outcome timestamp, asserts `seconds_since_start is None`, and checks that the logged message reads `after ?(s), ...`. I did not run the new test against the unfixed code to confirm it fails there. The `TypeError` path is clear from the code, but that check is still outstanding.

I did not commit anything.

## events
[tool_use Bash] {"command": "cat tenacity/after.py && grep -n \"seconds_since_start\" -r tenacity | head -30", "description": "Read after_log source and find seconds_since_start usages"}
[tool_result] # Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[1585 chars elided]…
et")
tenacity/stop.py:128:            retry_state.seconds_since_start + retry_state.upcoming_sleep
tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
tenacity/asyncio/__init__.py:146:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "grep -rn \"after_log\" tests | head -20; ls tests", "description": "Find existing after_log tests"}
[tool_result] tests/test_after.py:7:    after_log,
tests/test_after.py:37:        fun = after_log(
tests/test_after.py:64:        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py"}
[tool_result] 1	import logging
2	import random
3	import unittest.mock
4	
5	from tenacity import (
6	    _utils,
7	    after_log,
8	)
9	
10	from . import test_tenacity
11	
12	
13	class TestAfterLogFormat(unittest.TestCase):
14	    def setUp(self) -> None:
15	        self.log_level = random.choice(
16	            (
17	                logging.DEBUG,
18	                logging.INFO,
19	                logging.WARNING,
20	                logging.ERROR,
21	                logging.CRITICAL,
22	            )
23	     
…[1718 chars elided]…
5	        fun(retry_state)
66	        fn_name = (
67	            "<unknown>"
68	            if retry_state.fn is None
69	            else _utils.get_callback_name(retry_state.fn)
70	        )
71	        log.assert_called_once_with(
72	            self.log_level,
73	            f"Finished call to '{fn_name}' "
74	            f"after {sec_format % retry_state.seconds_since_start}(s), "
75	            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
76	        )
77	
[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A 25 tests/test_tenacity.py; sed -n 540,556p tenacity/__init__.py", "description": "Inspect make_retry_state and seconds_since_start"}
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
…[617 chars elided]…
ion: RetryAction | None = None
        #: Next sleep time as decided by the retry manager.
        self.upcoming_sleep: float = 0.0

    @property
    def seconds_since_start(self) -> float | None:
        if self.outcome_timestamp is None:
            return None
        return self.outcome_timestamp - self.start_time

    def prepare_for_next_attempt(self) -> None:
        self.outcome = None
        self.outcome_timestamp = None
        self.attempt_number += 1
        self.next_action = None
[assistant] Root cause is clear: `log_it` formats `seconds_since_start` with `%` unconditionally, and that property returns `None` until an outcome timestamp is set. I'll fix that in `after.py` and add a regression test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        if retry_state.seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)\n        fun(retry_state)\n        fn_name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            els
…[1561 chars elided]…
me = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] The suite passes. One style nit: the new `make_retry_state(...)` call fits on one line under the formatter's 88-column limit, so I'll collapse it to match what `ruff format` would produce.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        retry_state = test_tenacity.make_retry_state(\n            self.previous_attempt_number, 0.1\n        )\n        retry_state.outcome_timestamp = None", "new_string": "        retry_state = test_tenacity.make_retry_state(self.previous_attempt_number, 0.1)\n        retry_state.outcome_timestamp = None"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160033-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Rerun test suite after formatting tweak"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes: 127 passed, 1 skipped.

**Cause:** `log_it` in `tenacity/after.py` applied `sec_format % retry_state.seconds_since_start` unconditionally. That property returns `None` until an outcome timestamp is set, so the `%` formatting raised `TypeError`.

**Fix:** `tenacity/after.py` now checks for `None` first and uses `"?"`. Otherwise it formats the value with `sec_format` as before. The message text is unchanged apart from that placeholder.

**Test:** I added `test_03_seconds_since_start_unset` to `tests/test_after.py`. It builds a retry state with no outcome timestamp, asserts `seconds_since_start is None`, and checks that the logged message reads `after ?(s), ...`. I did not run the new test against the unfixed code to confirm it fails there. The `TypeError` path is clear from the code, but that check is still outstanding.

I did not commit anything.
