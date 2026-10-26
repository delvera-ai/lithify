# trajectory base-1

final message:
`after_log` no longer crashes when `retry_state.seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the rest of the message is unchanged. The full test suite passes (127 passed, 1 skipped).

**Changes**
- `tenacity/after.py`: the formatter now checks for `None` first and uses `"?"` in place of the elapsed seconds. Otherwise it applies `sec_format` as before. The crash came from `"%.3g" % None` raising `TypeError`.
- `tests/test_after.py`: added `test_03_unset_outcome_timestamp`. It builds a retry state with `outcome_timestamp = None` and checks that the log line reads `after ?(s), ...`. I didn't run it against the unfixed code, but `%` formatting of `None` raises `TypeError`, so it would fail there.

I didn't change any existing tests. Nothing has been committed.

## events
[tool_use Bash] {"command": "grep -rn \"seconds_since_start\\|def after_log\" tenacity/ | head -30; grep -rn \"after_log\" tests/ | head", "description": "Find after_log and seconds_since_start usages"}
[tool_result] tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:110:        return retry_state.seconds_since_start >= self.max_delay
tenacity/stop.py:125:        if retry_state.seconds_since_start is None:
tenacity/stop.py:126:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/stop.py:128:            retry_state.seconds
…[175 chars elided]…
546:    def seconds_since_start(self) -> float | None:
tenacity/after.py:29:def after_log(
tenacity/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
tenacity/asyncio/__init__.py:146:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tests/test_after.py:7:    after_log,
tests/test_after.py:37:        fun = after_log(
tests/test_after.py:64:        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py"}
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
[assistant] The crash is at `after.py:45`: `sec_format % None` raises `TypeError`. I'll substitute `"?"` when the value is `None`, and add a regression test next to the existing ones.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py", "old_string": "        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "        if retry_state.seconds_since_start is None:\n            seconds = \"?\"\n        else:\n            seconds = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {seconds}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_tenacity.py", "limit": 60}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013 Ray Holder
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
…[1126 chars elided]…
elay to
49	    # avoid complexity in test code.
50	    retry_state.start_time = Fraction(retry_state.start_time)  # type: ignore[assignment]
51	    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
52	    assert retry_state.seconds_since_start == delay
53	
54	
55	def make_retry_state(
56	    previous_attempt_number: typing.Any,
57	    delay_since_first_attempt: typing.Any,
58	    last_result: typing.Any = None,
59	    upcoming_sleep: typing.Any = 0,
60	) -> RetryCallState:
[assistant] Now I'll add a regression test for the `None` case, using a fresh `RetryCallState` whose outcome timestamp is unset.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "    def test_02_custom_sec_format(self) -> None:", "new_string": "    def test_01_unset_outcome_timestamp(self) -> None:\n        \"\"\"Test log formatting when seconds_since_start is None.\"\"\"\n        log = unitte
…[498 chars elided]…
retry_state.fn is None\n            else _utils.get_callback_name(retry_state.fn)\n        )\n        log.assert_called_once_with(\n            self.log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after ?(s), \"\n            f\"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.\",\n        )\n\n    def test_02_custom_sec_format(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "    def test_01_unset_outcome_timestamp(self) -> None:", "new_string": "    def test_03_unset_outcome_timestamp(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll run the project's checks using the command from CLAUDE.md.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Run project test suite"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.88s
[assistant] Tests pass. Black would collapse one call I wrote onto a single line, so I'll match that to keep the formatting clean.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py", "old_string": "        retry_state = test_tenacity.make_retry_state(\n            self.previous_attempt_number, 0.1\n        )\n        retry_state.outcome_timestamp = None", "new_string": "        retry_state = test_tenacity.make_retry_state(self.previous_attempt_number, 0.1)\n        retry_state.outcome_timestamp = None"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git -C ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155025-bug-tenacity-after-log-crashes-w/base-1 diff --stat", "description": "Re-run tests and show diff stat"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.76s
 tenacity/after.py   |  6 +++++-
 tests/test_after.py | 23 +++++++++++++++++++++++
 2 files changed, 28 insertions(+), 1 deletion(-)
[assistant] `after_log` no longer crashes when `retry_state.seconds_since_start` is `None`. It logs `after ?(s)` in that case, and the rest of the message is unchanged. The full test suite passes (127 passed, 1 skipped).

**Changes**
- `tenacity/after.py`: the formatter now checks for `None` first and uses `"?"` in place of the elapsed seconds. Otherwise it applies `sec_format` as before. The crash came from `"%.3g" % None` raising `TypeError`.
- `tests/test_after.py`: added `test_03_unset_outcome_timestamp`. It builds a retry state with `outcome_timestamp = None` and checks that the log line reads `after ?(s), ...`. I didn't run it against the unfixed code, but `%` formatting of `None` raises `TypeError`, so it would fail there.

I didn't change any existing tests. Nothing has been committed.
