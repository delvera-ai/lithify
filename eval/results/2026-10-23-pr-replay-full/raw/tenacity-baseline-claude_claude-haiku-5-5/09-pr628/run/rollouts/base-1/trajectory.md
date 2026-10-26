# trajectory base-1

final message:
`wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full test suite passes: 154 passed, 1 skipped.

The change is in `tenacity/wait.py`:
- **`min`**: new last parameter, default `0`, so existing positional calls keep working. The result is clamped to `[min, max]`, using the same pattern as `wait_exponential`.
- **Timedelta support**: `max`, `jitter` and `min` go through `_utils.to_seconds()` in `__init__`, the same as the other wait classes.

I added two tests to `tests/test_tenacity.py` (`test_wait_exponential_jitter_min` and `test_wait_exponential_jitter_timedelta`) and left the existing test unchanged. I also added a release note at `releasenotes/notes/wait-exponential-jitter-min-timedelta-3c1f9e2a7b8d4f60.yaml`.

Choices to check:
- **`initial` is still a plain float.** You listed only `max`, `jitter` and `min`, so I didn't convert it. Say if you want it to accept timedeltas too.
- **Changes are uncommitted.** I haven't committed or pushed.
- **Lint and type checks didn't run.** `ruff` and `mypy` aren't installed in the project's test environment, so only pytest ran.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"wait_exponential_jitter\\|class wait_exponential\\b\\|class wait_exponential(\" --include=*.py --include=*.rst --include=*.md . | head -50", "description": "Locate wait_exponential_jitter and wait_exponential"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"wait_exponential_jitter\" . --exclude-dir=.git | head -50; echo ---; grep -rn \"class wait_exponential\" . --exclude-dir=.git", "description": "Locate wait_exponential_jitter references"}
[tool_result] tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
tests/test_tenacity.py:598:    def test_wait_exponential_jitter(self) -> None:
tests/test_tenacity.py:599:        fn = tenacity.wait_exponential_jitter(max=60)
tests/test_tenacity.py:612:        fn = tenacity.wait_exponential_jitter(10, 5)
tests/test_tenacity.py:617:        fn = tenacity.wait_exponential_jitter()
tenacity/__init__.py:77:    wait_exponential_jitter,
tenacity/__init__.py:799:    "wait_exponential_jitter",
doc/source/index.rst:199:    def wait_exponential_jitter():
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml:4:    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
---
tenacity/wait.py:175:class wait_exponential(wait_base):
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tenacity/wait.py"}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
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
13	# WITH
…[9266 chars elided]…
tial = initial
260	        self.max = max
261	        self.exp_base = exp_base
262	        self.jitter = jitter
263	
264	    def __call__(self, retry_state: "RetryCallState") -> float:
265	        jitter = random.uniform(0, self.jitter)
266	        try:
267	            exp = self.exp_base ** (retry_state.attempt_number - 1)
268	            result = self.initial * exp + jitter
269	        except OverflowError:
270	            result = self.max
271	        return max(0, min(result, self.max))
272	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py", "offset": 560, "limit": 80}
[tool_result] 560	            self._assert_inclusive_range(fn(make_retry_state(8, 0)), 0, 60.0)
561	            self._assert_inclusive_range(fn(make_retry_state(9, 0)), 0, 60.0)
562	
563	        # max wait
564	        max_wait = 5
565	        fn = tenacity.wait_random_exponential(10, max_wait)
566	        for _ in range(1000):
567	            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 0.00, max_wait)
568	
569	        # min wait
570	        min_wait = 5
571	        fn = tenacity.wait_random_expon
…[2670 chars elided]…
t has when wait is called and bypass any other logic.
626	        def waitfunc(retry_state: RetryCallState) -> float:
627	            raise ExtractCallState(retry_state)
628	
629	        retrying = Retrying(
630	            wait=waitfunc,
631	            retry=(
632	                tenacity.retry_if_exception_type()
633	                | tenacity.retry_if_result(lambda result: result == 123)
634	            ),
635	        )
636	
637	        def returnval() -> int:
638	            return 123
639	
[tool_use Bash] {"command": "cat tenacity/_utils.py | head -80; echo ---; sed -n 180,230p doc/source/index.rst; echo ---; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; ls releasenotes/notes | tail -5; echo ---; grep -rn \"timedelta\\|time_unit_type\" tenacity/*.py | head -30", "description": "Inspect utils, docs, release notes"}
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
…[4275 chars elided]…
:162:        start: _utils.time_unit_type = 0,
tenacity/wait.py:163:        increment: _utils.time_unit_type = 100,
tenacity/wait.py:164:        max: _utils.time_unit_type = _utils.MAX_WAIT,
tenacity/wait.py:191:        max: _utils.time_unit_type = _utils.MAX_WAIT,
tenacity/wait.py:193:        min: _utils.time_unit_type = 0,
tenacity/stop.py:104:    def __init__(self, max_delay: _utils.time_unit_type) -> None:
tenacity/stop.py:121:    def __init__(self, max_delay: _utils.time_unit_type) -> None:
[tool_use Bash] {"command": "cat releasenotes/notes/support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; grep -n \"wait_exponential_jitter\\|timedelta\" tenacity/__init__.py README* doc/source/*.rst | head; git log --oneline -3 -- tenacity/wait.py", "description": "Read release-note conventions and recent history"}
[tool_result] ---
features:
  - Add ``datetime.timedelta`` as accepted wait unit type.
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
tenacity/__init__.py:77:    wait_exponential_jitter,
tenacity/__init__.py:799:    "wait_exponential_jitter",
README.rst:199:    def wait_exponential_jitter():
doc/source/index.rst:199:    def wait_exponential_jitter():
ae2d75e refactor: enable PGH, PYI ruff rules and rename TCH to TC (#619)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
9686ed7 refactor: enable additional ruff rules and fix violations (#584)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is min(initial * 2**
…[1626 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tenacity/wait.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll add new tests alongside the existing one (leaving the existing test untouched), plus a release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n", "new_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jit
…[827 chars elided]…
lusive_range(fn(make_retry_state(1, 0)), 2, 2)\n            self._assert_inclusive_range(fn(make_retry_state(4, 0)), 8, 9)\n            self.assertEqual(fn(make_retry_state(9, 0)), 60)\n\n        fn = tenacity.wait_exponential_jitter(\n            initial=10, max=datetime.timedelta(seconds=5)\n        )\n        for _ in range(1000):\n            self.assertEqual(fn(make_retry_state(1, 0)), 5)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191317-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_tenacity.py | grep -n \"import\"; grep -n \"def _assert_inclusive_range\" -A3 tests/test_tenacity.py", "description": "Check test imports and helper signature"}
[tool_result] 16:import contextlib
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
499:    def _assert_inclusive_range(self, wait: float, low: float, high: float) -> None:
500-        self.assertLessEqual(wait, high)
501-        self.assertGreaterEqual(wait, low)
502-
[assistant] Imports are already in place. Adding the release note, then running the project's test command.
[tool_use Bash] {"command": "cat > releasenotes/notes/wait-exponential-jitter-min-timedelta-3c1f9e2a7b8d4f60.yaml <<'EOF'\n---\nfeatures:\n  - |\n    Add a ``min`` argument to ``wait_exponential_jitter``, matching\n    ``wait_exponential``, to set a floor on the wait time.\n  - |\n    ``wait_exponential_jitter`` now accepts ``datetime.timedelta`` values for\n    ``max``, ``jitter`` and ``min``, as well as numbers of seconds.\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add release note and run the project test suite"}
[tool_result] ............s............................................... [ 38%]
........................................................................ [ 85%]
.......................                                                  [100%]
154 passed, 1 skipped, 12 subtests passed in 1.90s
[assistant] The suite passes. I'll also run the linters and type checker the repo configures, if they're available in that environment.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; for t in ruff mypy; do if [ -x $PY/$t ]; then echo \"== $t\"; $PY/$t $( [ $t = ruff ] && echo \"check tenacity tests\" || echo \"tenacity\" ) 2>&1 | tail -5; else echo \"$t not installed\"; fi; done; $PY/ruff format --check tenacity tests 2>&1 | tail -3", "description": "Run ruff and mypy if installed"}
[tool_result] ruff not installed
mypy not installed
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
[assistant] `wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full test suite passes: 154 passed, 1 skipped.

The change is in `tenacity/wait.py`:
- **`min`**: new last parameter, default `0`, so existing positional calls keep working. The result is clamped to `[min, max]`, using the same pattern as `wait_exponential`.
- **Timedelta support**: `max`, `jitter` and `min` go through `_utils.to_seconds()` in `__init__`, the same as the other wait classes.

I added two tests to `tests/test_tenacity.py` (`test_wait_exponential_jitter_min` and `test_wait_exponential_jitter_timedelta`) and left the existing test unchanged. I also added a release note at `releasenotes/notes/wait-exponential-jitter-min-timedelta-3c1f9e2a7b8d4f60.yaml`.

Choices to check:
- **`initial` is still a plain float.** You listed only `max`, `jitter` and `min`, so I didn't convert it. Say if you want it to accept timedeltas too.
- **Changes are uncommitted.** I haven't committed or pushed.
- **Lint and type checks didn't run.** `ruff` and `mypy` aren't installed in the project's test environment, so only pytest ran.
