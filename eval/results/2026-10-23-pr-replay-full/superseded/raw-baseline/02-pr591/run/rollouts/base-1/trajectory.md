# trajectory base-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the project's test suite passes (127 passed, 1 skipped).

- **Fix (`tenacity/after.py`):** the log message substitutes `"?"` for the elapsed seconds when the value is `None`. Otherwise it formats the value with `sec_format` as before.
- **Test (`tests/test_after.py`):** `test_03_seconds_since_start_none` sets `outcome_timestamp` to `None`, confirms `seconds_since_start` is `None`, and checks the emitted message contains `after ?(s)`.

I haven't run the new test against the unfixed code to confirm it fails there. The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"seconds_since_start\" -r tenacity tests | head -50; grep -n \"def after_log\" -A 40 tenacity/after.py", "description": "Locate after_log and seconds_since_start usages"}
[tool_result] tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.seconds_since_start is None:
tenacity/stop.py:126:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:128:            retry_state.seconds
…[1283 chars elided]…
            # NOTE(sileht): can't really happen, but we must please mypy
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py"}
[tool_result] 1	# Copyright 2016 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITHOUT W
…[783 chars elided]…
        # NOTE(sileht): can't really happen, but we must please mypy
39	            fn_name = "<unknown>"
40	        else:
41	            fn_name = _utils.get_callback_name(retry_state.fn)
42	        logger.log(
43	            log_level,
44	            f"Finished call to '{fn_name}' "
45	            f"after {sec_format % retry_state.seconds_since_start}(s), "
46	            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
47	        )
48	
49	    return log_it
50	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py"}
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
[assistant] The crash is at `after.py:45`: `sec_format % None` raises `TypeError`. I'll substitute `"?"` when the value is `None`, then add a test for that case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "        if retry_state.seconds_since_start is None:\n            seconds = \"?\"\n        else:\n            seconds = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {seconds}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)\n        fun(retry_state)\n        fn_name = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            els
…[1528 chars elided]…
me = (\n            \"<unknown>\"\n            if retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-160027-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Before running the suite, I need to confirm that setting `outcome_timestamp` to `None` actually makes `seconds_since_start` return `None`.
[tool_use Bash] {"command": "sed -n 540,556p tenacity/__init__.py; grep -n \"def make_retry_state\" -A 12 tests/test_tenacity.py; ls <work>/env-tenacity/bin/python 2>&1", "description": "Check seconds_since_start property and test helper"}
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
…[245 chars elided]…
ng_sleep: typing.Any = 0,
60-) -> RetryCallState:
61-    """Construct RetryCallState for given attempt number & delay.
62-
63-    Only used in testing and thus is extra careful about timestamp arithmetics.
64-    """
65-    required_parameter_unset = (
66-        previous_attempt_number is _unset or delay_since_first_attempt is _unset
67-    )
<work>/env-tenacity/bin/python
[assistant] The property returns `None` when `outcome_timestamp` is `None`, so the test setup is valid. Now I'll run the project's check command.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_use Bash] {"command": "git stash list >/dev/null; git -c core.pager=cat diff --stat; git -c core.pager=cat log -1 --format=%H", "description": "Show diff stats and current HEAD"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.81s
[tool_result]  tenacity/after.py   |  6 +++++-
 tests/test_after.py | 23 +++++++++++++++++++++++
 2 files changed, 28 insertions(+), 1 deletion(-)
4a7d4031814f871a37e2c232ca91f67bb07045e8
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the project's test suite passes (127 passed, 1 skipped).

- **Fix (`tenacity/after.py`):** the log message substitutes `"?"` for the elapsed seconds when the value is `None`. Otherwise it formats the value with `sec_format` as before.
- **Test (`tests/test_after.py`):** `test_03_seconds_since_start_none` sets `outcome_timestamp` to `None`, confirms `seconds_since_start` is `None`, and checks the emitted message contains `after ?(s)`.

I haven't run the new test against the unfixed code to confirm it fails there. The changes are uncommitted in the worktree.
