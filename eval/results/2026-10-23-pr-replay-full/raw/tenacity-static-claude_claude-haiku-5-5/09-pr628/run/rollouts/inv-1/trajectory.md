# trajectory inv-1

final message:
`wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full suite passes (156 passed, 1 skipped, exit 0), and the four new tests fail before the fix and pass after.

**Changes**
- **`tenacity/wait.py`**: new `min` parameter (default 0), added last so existing positional calls still work. `max`, `jitter` and `min` go through `_utils.to_seconds`, as `wait_exponential` does. The result is clamped with `max(max(0, self.min), ...)`, mirroring `wait_exponential`. The docstring is updated.
- **`tests/test_tenacity.py`**: four tests in `TestWaitConditions`, one for `min` and one each for timedelta `max`, `jitter` and `min`. I ran them against the unfixed code first:
  - `min`: `unexpected keyword argument 'min'`
  - timedelta `max`: `'<' not supported between 'timedelta' and 'float'`
  - timedelta `jitter`: `unsupported operand ... 'timedelta' and 'int'`
  - timedelta `min`: fails on the missing `min` keyword first, because the test uses both gaps.
- **`doc/source/index.rst`**: a short paragraph and a `testcode` example using `min` and `max` as timedeltas.
- **`releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9a1c7e5b2d8046.yaml`**: a `features:` note.

**Choices I made**
- `min` is applied after the `max` cap, so if `min > max` the wait is `min`. This matches `wait_exponential`.
- `initial` still takes only numbers, since the request named `max`, `jitter` and `min`. Say if you want it to accept timedeltas too.

**Not run**
- ruff and mypy: not available in this environment. `check_changed.py` passed (0 problems) and reports them as not run.
- Sphinx doctest for the new docs example: not run. I checked the imports by reading only.
- YAML validity of the reno note: PyYAML is unavailable here, so it is checked by shape only.

## events
[assistant] I'll start by reading the wait strategy code and the change-contract skill this task triggers.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md && cat .lithify/memory.md 2>/dev/null; echo ---; grep -n \"\" tenacity/wait.py | sed -n '1,400p' | grep -n \"class \\|def \\|timedelta\\|import\" ", "description": "Read change-contract skill and wait module outline"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or 
…[16076 chars elided]…
 __init__(
170:170:    def __call__(self, retry_state: "RetryCallState") -> float:
175:175:class wait_exponential(wait_base):
188:188:    def __init__(
200:200:    def __call__(self, retry_state: "RetryCallState") -> float:
209:209:class wait_random_exponential(wait_exponential):
235:235:    def __call__(self, retry_state: "RetryCallState") -> float:
240:240:class wait_exponential_jitter(wait_base):
252:252:    def __init__(
264:264:    def __call__(self, retry_state: "RetryCallState") -> float:
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py; echo ...; sed -n 175,290p tenacity/wait.py; echo ---; cat tenacity/_utils.py | head -60; echo ---; grep -n \"time_unit_type\\|timedelta\" -r tenacity/ | head -40", "description": "Read wait strategies and utils"}
[tool_result] # Copyright 2016–2021 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS O
…[6081 chars elided]…
y/wait.py:164:        max: _utils.time_unit_type = _utils.MAX_WAIT,
tenacity/wait.py:191:        max: _utils.time_unit_type = _utils.MAX_WAIT,
tenacity/wait.py:193:        min: _utils.time_unit_type = 0,
tenacity/_utils.py:21:from datetime import timedelta
tenacity/_utils.py:81:time_unit_type = int | float | timedelta
tenacity/_utils.py:84:def to_seconds(time_unit: time_unit_type) -> float:
tenacity/_utils.py:86:        time_unit.total_seconds() if isinstance(time_unit, timedelta) else time_unit
[assistant] The current `wait_exponential_jitter` takes plain numbers only and has no floor. Next I'll check the existing tests, docs, and release-note conventions, and confirm the project Python exists.
[tool_use Bash] {"command": "grep -n \"exponential_jitter\\|class TestWaitExponentialJitter\\|timedelta\" tests/*.py | head -40; echo ---; grep -n \"exponential_jitter\\|wait_exponential\" doc/source/index.rst; echo ---; ls releasenotes/notes | tail -5; echo ---; ls -la <work>/env-tenacity/bin/python; echo ---; cat .lithify/harness/scripts/run_tests.py | head -40", "description": "Find existing tests, docs, notes, and venv"}
[tool_result] tests/test_tenacity.py:248:        for delay in (1, datetime.timedelta(seconds=1)):
tests/test_tenacity.py:256:        for delay in (1, datetime.timedelta(seconds=1)):
tests/test_tenacity.py:290:        for wait in (1, datetime.timedelta(seconds=1)):
tests/test_tenacity.py:298:            (datetime.timedelta(seconds=500), datetime.timedelta(seconds=100)),
tests/test_tenacity.py:311:            (datetime.timedelta(seconds=1), datetime.timedelta(seconds=20)),
tests/test_tenacity.py:401:           
…[2082 chars elided]…
 node id alone with
          --timeout 60; if it is a test you wrote, make its retry loop bounded
          (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
[tool_use Bash] {"command": "sed -n 590,625p tests/test_tenacity.py; echo ---; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; echo ---; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ---; sed -n 190,215p doc/source/index.rst; echo ---; grep -n \"^import\\|^from\" tests/test_tenacity.py", "description": "Read existing jitter test, notes, and docs example"}
[tool_result]         self._assert_inclusive_epsilon(mean(attempt[3]), 1, 0.08)
        self._assert_inclusive_epsilon(mean(attempt[4]), 2, 0.16)
        self._assert_inclusive_epsilon(mean(attempt[5]), 4, 0.32)
        self._assert_inclusive_epsilon(mean(attempt[6]), 8, 0.64)
        self._assert_inclusive_epsilon(mean(attempt[7]), 16, 1.28)
        self._assert_inclusive_epsilon(mean(attempt[8]), 30, 2.56)
        self._assert_inclusive_epsilon(mean(attempt[9]), 30, 2.56)

    def test_wait_exponential_jitt
…[2353 chars elided]…
 for the next 2 attempts and 9s for all attempts thereafter")
        raise Exception

Whether to retry
---
16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
24:from fractions import Fraction
25:from unittest import mock
27:import pytest
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
[assistant] Plan: I'll write the regression tests first and confirm they fail against the current code, then implement. The change touches a public strategy, so the change-contract skill applies: a reno note, a docs example, and tests. I'll read the test file region I need to edit.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tests/test_tenacity.py", "offset": 614, "limit": 12}
[tool_result] 614	            self.assertEqual(fn(make_retry_state(1, 0)), 5)
615	
616	        # Default arguments exist
617	        fn = tenacity.wait_exponential_jitter()
618	        fn(make_retry_state(0, 0))
619	
620	    def test_wait_retry_state_attributes(self) -> None:
621	        class ExtractCallState(Exception):
622	            pass
623	
624	        # retry_state is mutable, so return it as an exception to extract the
625	        # exact values it has when wait is called and bypass any other logic.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n\n    def test_wait_retry_state_attributes(self) -> None:", "new_string": "        # Default arg
…[1023 chars elided]…
e_retry_state(1, 0)), 1, 6)\n\n    def test_wait_exponential_jitter_timedelta_min(self) -> None:\n        fn = tenacity.wait_exponential_jitter(\n            initial=1, min=datetime.timedelta(seconds=5), jitter=0\n        )\n\n        self.assertEqual(fn(make_retry_state(1, 0)), 5)\n        self.assertEqual(fn(make_retry_state(4, 0)), 8)\n\n    def test_wait_retry_state_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] Tests are written. Now I'll run them alone against the unfixed code, through the harness runner, and read the failure reasons.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; \"$PY\" .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestRetry::test_wait_exponential_jitter_min tests/test_tenacity.py::TestRetry::test_wait_exponential_jitter_timedelta_max tests/test_tenacity.py::TestRetry::test_wait_exponential_jitter_timedelta_jitter tests/test_tenacity.py::TestRetry::test_wait_exponential_jitter_timedelta_min > /tmp/red.txt 2>&1; echo \"exit=$?\"; grep -E \"Error|FAILED|PASSED|passed|failed\" /tmp/red.txt | tail -30", "description": "Run new tests against unfixed code"}
[tool_result] exit=4
[tool_use Bash] {"command": "tail -15 /tmp/red.txt; grep -n \"class .*Test\" tests/test_tenacity.py | head -20", "description": "Show run output and test class names"}
[tool_result] ============================ no tests ran in 0.04s =============================
ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tests/test_tenacity.py::TestRetry::test_wait_exponential_jitter_min
(no match in any of [<Module test_tenacity.py>])

ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tests/test_tenacity.py::TestRetry::test_wait_expone
…[960 chars elided]…
ss TestEnabled:
1516:class TestRetryWith:
1554:class TestBeforeAfterAttempts(unittest.TestCase):
1707:class TestReraiseExceptions(unittest.TestCase):
1776:class TestStatistics(unittest.TestCase):
1828:class TestRetryErrorCallback(unittest.TestCase):
1861:class TestContextManager(unittest.TestCase):
1916:class TestInvokeAsCallable:
1986:class TestRetryException(unittest.TestCase):
1996:class TestRetryTyping(unittest.TestCase):
2019:class TestMockingSleep:
2060:class TestPickle(unittest.TestCase):
[assistant] The class is `TestWaitConditions`, not `TestRetry`, so my node IDs were wrong. Rerunning with the correct class.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; C=tests/test_tenacity.py::TestWaitConditions; \"$PY\" .lithify/harness/scripts/run_tests.py --timeout 60 $C::test_wait_exponential_jitter_min $C::test_wait_exponential_jitter_timedelta_max $C::test_wait_exponential_jitter_timedelta_jitter $C::test_wait_exponential_jitter_timedelta_min > /tmp/red.txt 2>&1; echo \"exit=$?\"; grep -E \"^E  |Error|FAILED|passed|failed\" /tmp/red.txt | head -30", "description": "Rerun new tests with correct class name"}
[tool_result] exit=1
E       TypeError: unsupported operand type(s) for -: 'datetime.timedelta' and 'int'
~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/random.py:503: TypeError
E       TypeError: wait_exponential_jitter.__init__() got an unexpected keyword argument 'min'
tests/test_tenacity.py:642: TypeError
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta_max
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta_jitter
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta_min
============================== 4 failed in 0.07s ===============================
[assistant] Four red tests. Two of the failure messages are clearly the intended gaps (`min` unknown, timedelta arithmetic). The `timedelta_max` failure isn't shown in that grep, so I'll check its actual reason before implementing.
[tool_use Bash] {"command": "grep -n \"test_wait_exponential_jitter_timedelta_max\" -A60 /tmp/run_tests.log | grep -E \"Error|tenacity/wait.py|test_tenacity.py:6\" | head -12", "description": "Inspect timedelta_max failure reason"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -nE \"^E |wait.py:[0-9]+|test_tenacity.py:[0-9]+:|_{5,} \" /tmp/run_tests.log | head -40", "description": "Extract failure lines from pytest log"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; \"$PY\" -I -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta_max 2>&1 | grep -E \"^E |wait.py:[0-9]+|test_tenacity.py:[0-9]+\" | head -12", "description": "Get timedelta_max failure traceback directly"}
[tool_result] tests/test_tenacity.py:632: 
E       TypeError: '<' not supported between instances of 'datetime.timedelta' and 'float'
tenacity/wait.py:271: TypeError
[assistant] All four fail for the intended reasons: `min` is an unknown keyword, and `timedelta` compares/subtracts against numbers. (`timedelta_min` also uses `min=`, so it fails on the missing parameter first, as expected for a test that uses both gaps.) Now the implementation, mirroring `wait_exponential`'s `min` handling.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is min(initial * 2**n
…[1637 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/tenacity/wait.py has been updated successfully.
[assistant] Implementation is in. Next, the docs example and reno note the change contract requires. I'll read the docs region before editing it.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/doc/source/index.rst", "offset": 194, "limit": 12}
[tool_result] 194	increasing jitter helps minimise collisions.
195	
196	.. testcode::
197	
198	    @retry(wait=wait_random_exponential(multiplier=1, max=60))
199	    def wait_exponential_jitter():
200	        print("Randomly wait up to 2^x * 1 seconds between each retry until the range reaches 60 seconds, then randomly up to 60 seconds afterwards")
201	        raise Exception
202	
203	
204	Sometimes it's necessary to build a chain of backoffs.
205	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/doc/source/index.rst", "old_string": "        print(\"Randomly wait up to 2^x * 1 seconds between each retry until the range reaches 60 seconds, then randomly up to 60 seconds afterwards\")\n        raise Exception\n\n\nSometimes it's necessary to build a 
…[364 chars elided]…
or on the wait.\n\n.. testcode::\n\n    @retry(wait=wait_exponential_jitter(min=datetime.timedelta(seconds=2),\n                                        max=datetime.timedelta(minutes=1)))\n    def wait_exponential_jitter_bounded():\n        print(\"Wait between 2 and 60 seconds between each retry, with jitter\")\n        raise Exception\n\n\nSometimes it's necessary to build a chain of backoffs."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/doc/source/index.rst has been updated successfully.
[assistant] The docs example uses `datetime`, so I need to confirm the doctest setup imports it.
[tool_use Bash] {"command": "grep -n \"import\\|testsetup\" doc/source/index.rst | head -30", "description": "Check imports in docs doctest blocks"}
[tool_result] 31:    import random
32:    from tenacity import retry
85:.. testsetup::
87:    import logging
89:    # Note the following import is used for demonstration convenience only.
90:    # Production code should always explicitly import the names it needs.
92:    from tenacity import *
330:    import logging
331:    import sys
345:    import logging
346:    import sys
362:    import logging
363:    import sys
442:    import logging
499:    import logging
556:    from tenacity import Retrying
617:    from unittest import mock
641:    import os
673:   from tenacity import Retrying, RetryError, stop_after_attempt
689:   from tenacity import AsyncRetrying, RetryError, stop_after_attempt
705:    from tenacity import AsyncRetrying, retry_if_result
[assistant] The setup block doesn't import `datetime`, so I'll add the import inside the example, as other examples in this file do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/doc/source/index.rst", "old_string": ".. testcode::\n\n    @retry(wait=wait_exponential_jitter(min=datetime.timedelta(seconds=2),", "new_string": ".. testcode::\n\n    import datetime\n\n    @retry(wait=wait_exponential_jitter(min=datetime.timedelta(seconds=2),"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/doc/source/index.rst has been updated successfully.
[assistant] Now the reno release note, using the repo's `features:` shape and a unique suffix.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9a1c7e5b2d8046.yaml", "content": "---\nfeatures:\n  - |\n    ``wait.wait_exponential_jitter`` accepts a new ``min`` argument that sets a\n    floor on the wait, matching ``wait_exponential``. Its ``max``, ``jitter`` and\n    ``min`` arguments also accept ``datetime.timedelta`` values as well as\n    numbers of seconds.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/inv-1/releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9a1c7e5b2d8046.yaml (file state is current in your context — no need to Read it back)
[assistant] Docs and note are in. Now I'll rerun the four new tests, which should go green.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; C=tests/test_tenacity.py::TestWaitConditions; \"$PY\" .lithify/harness/scripts/run_tests.py --timeout 60 $C::test_wait_exponential_jitter_min $C::test_wait_exponential_jitter_timedelta_max $C::test_wait_exponential_jitter_timedelta_jitter $C::test_wait_exponential_jitter_timedelta_min > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green.txt", "description": "Run new regression tests against fixed code"}
[tool_result] exit=0
============================== 4 passed in 0.03s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All four pass. Next, the full suite through the runner, and the stdlib lint check.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; \"$PY\" .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"run_exit=$?\"; tail -4 /tmp/full.txt; echo ===CHECK; \"$PY\" .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_exit=$?\"; tail -15 /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result ERROR] Exit code 1
run_exit=0

============== 156 passed, 1 skipped, 12 subtests passed in 1.86s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
(eval):1: ==CHECK not found
[assistant] The full suite passed (156 passed, 1 skipped). My `echo ===CHECK` hit the zsh `=`-word issue the harness warns about, so the check step didn't run. Rerunning it properly.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; \"$PY\" .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_exit=$?\"; tail -15 /tmp/check.txt", "description": "Run stdlib lint substitute on changed files"}
[tool_result] check_exit=0
changed: doc/source/index.rst, releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9a1c7e5b2d8046.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Lint substitute passes. I'll do a final review of the diff and confirm no stray files were left in the worktree.
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff -- tenacity/wait.py", "description": "Review final diff and working tree status"}
[tool_result]  M doc/source/index.rst
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9a1c7e5b2d8046.yaml
 doc/source/index.rst   | 13 +++++++++++++
 tenacity/wait.py       | 20 ++++++++++++--------
 tests/test_tenacity.py | 29 +++++++++++++++++++++++++++++
 3 files changed, 54 insertions(+), 8 deletions(-)
diff --git a/tenacity/wait.py b/tenacity/wait.py
index b28b788..c02a419 100644
--- a/tenacity/wait.py
+++ b/tenacity/wait.py
@@ -240,26 +240,30 @
…[1265 chars elided]…
er = jitter
+        self.jitter = _utils.to_seconds(jitter)
+        self.min = _utils.to_seconds(min)
 
     def __call__(self, retry_state: "RetryCallState") -> float:
         jitter = random.uniform(0, self.jitter)
@@ -268,4 +272,4 @@ class wait_exponential_jitter(wait_base):
             result = self.initial * exp + jitter
         except OverflowError:
             result = self.max
-        return max(0, min(result, self.max))
+        return max(max(0, self.min), min(result, self.max))
[assistant] `wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full suite passes (156 passed, 1 skipped, exit 0), and the four new tests fail before the fix and pass after.

**Changes**
- **`tenacity/wait.py`**: new `min` parameter (default 0), added last so existing positional calls still work. `max`, `jitter` and `min` go through `_utils.to_seconds`, as `wait_exponential` does. The result is clamped with `max(max(0, self.min), ...)`, mirroring `wait_exponential`. The docstring is updated.
- **`tests/test_tenacity.py`**: fou
…[631 chars elided]…
 `features:` note.

**Choices I made**
- `min` is applied after the `max` cap, so if `min > max` the wait is `min`. This matches `wait_exponential`.
- `initial` still takes only numbers, since the request named `max`, `jitter` and `min`. Say if you want it to accept timedeltas too.

**Not run**
- ruff and mypy: not available in this environment. `check_changed.py` passed (0 problems) and reports them as not run.
- Sphinx doctest for the new docs example: not run. I checked the imports by reading only.
- YAML validity of the reno note: PyYAML is unavailable here, so it is checked by shape only.
