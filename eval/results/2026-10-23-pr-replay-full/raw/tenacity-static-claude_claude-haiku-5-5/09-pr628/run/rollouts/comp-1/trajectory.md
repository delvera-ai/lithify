# trajectory comp-1

final message:
`wait_exponential_jitter` now takes `min`, and `max`, `jitter` and `min` accept either seconds or a `datetime.timedelta`. The full suite passes (156 passed, 1 skipped) and `check_changed.py` reports PASS. I haven't committed anything.

**What changed**
- **`tenacity/wait.py`**: `min` is a new last parameter, defaulting to 0. `max`, `jitter` and `min` are converted once in `__init__` with `_utils.to_seconds`. The result is clamped with the same expression `wait_exponential` uses, `max(max(0, self.min), min(result, self.max))`. With the default `min=0` the output is unchanged. `initial` and `exp_base` stay as they were; the task didn't name them.
- **`tests/test_tenacity.py`**: four new tests, one per gap: `max` as a timedelta, `jitter` as a timedelta (number and timedelta subtests), `min` as a number, and `min` as a timedelta. The red run against the unfixed code failed on the right things: `max` failed comparing a timedelta with a float at `wait.py:271`, and `jitter` failed inside `random.uniform`. Both `min` tests failed with "unexpected keyword argument 'min'". The `min`-timedelta test depends on `min` existing, so its red reason is that same missing keyword; I didn't separately prove the timedelta conversion.
- **`releasenotes/notes/wait-exponential-jitter-min-timedelta-09d78566c62edd25.yaml`**: a `features:` note.
- **`doc/source/index.rst`**: an example with a `min`/`max`/`jitter` timedelta set, placed above the existing `wait_exponential_jitter` doc block. That block redefines the name `wait_exponential_jitter` in the doctest namespace, so an example placed after it would break. The example's function name is distinct.

**Choices you may want to change**
- `min` is applied as a floor on the final result, so `min > max` returns `min`, the same as `wait_exponential`.
- I left `initial` as a plain float, since it is a scale factor and you didn't ask for it to change.

**Not run**
- ruff and mypy (unavailable in this environment).
- The Sphinx doctest build. I ran the doc example's logic directly instead; it produces floored and capped waits as expected.
- A YAML parse of the reno note; PyYAML isn't installed here. The file follows the shape of the existing notes.

## events
[assistant] I'll start by reading the wait strategy code and the change-contract skill the project asks for.
[tool_use Bash] {"command": "git status --short && ls && cat .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n \"jitter\\|class wait_exponential\\|timedelta\" tenacity/wait.py", "description": "Check status, read contract skill, grep wait.py"}
[tool_result] AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/c
…[17593 chars elided]…
azon.com/blogs/architecture/exponential-backoff-and-jitter/
240:class wait_exponential_jitter(wait_base):
241:    """Wait strategy that applies exponential backoff and jitter.
243:    It allows for a customized initial wait, maximum wait and jitter.
248:    The wait time is min(initial * 2**n + random.uniform(0, jitter), maximum)
257:        jitter: float = 1,
262:        self.jitter = jitter
265:        jitter = random.uniform(0, self.jitter)
268:            result = self.initial * exp + jitter
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tenacity/wait.py", "offset": 1, "limit": 300}
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
[tool_use Bash] {"command": "grep -n \"jitter\" tests/test_tenacity.py doc/source/index.rst; grep -n \"time_unit_type\\|def to_seconds\" -A6 tenacity/_utils.py | head -40; ls releasenotes/notes | tail -5; cat .lithify/harness/memory.md 2>/dev/null | head -20; ls .lithify/harness/scripts", "description": "Find jitter references in tests, docs, utils"}
[tool_result] doc/source/index.rst:182:Then again, it's also hard to beat combining fixed waits and jitter (to
doc/source/index.rst:189:    def wait_fixed_jitter():
doc/source/index.rst:194:increasing jitter helps minimise collisions.
doc/source/index.rst:199:    def wait_exponential_jitter():
tests/test_tenacity.py:598:    def test_wait_exponential_jitter(self) -> None:
tests/test_tenacity.py:599:        fn = tenacity.wait_exponential_jitter(max=60)
tests/test_tenacity.py:612:        fn = tenacity.wait_expon
…[403 chars elided]…
ol:
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
check_changed.py
run_tests.py
[assistant] Now the existing tests, the docs example, and the existing reno note for this wait.
[tool_use Bash] {"command": "sed -n 560,625p tests/test_tenacity.py; echo ----; sed -n 160,205p doc/source/index.rst; echo ----; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; echo ----; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ----; ls <work>/env-tenacity/bin/python; sed -n 1,60p .lithify/harness/scripts/run_tests.py | head -60", "description": "Read existing tests, docs, reno note, and runner"}
[tool_result]             self._assert_inclusive_range(fn(make_retry_state(8, 0)), 0, 60.0)
            self._assert_inclusive_range(fn(make_retry_state(9, 0)), 0, 60.0)

        # max wait
        max_wait = 5
        fn = tenacity.wait_random_exponential(10, max_wait)
        for _ in range(1000):
            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 0.00, max_wait)

        # min wait
        min_wait = 5
        fn = tenacity.wait_random_exponential(min=min_wait)
        for _ in range(1000
…[5852 chars elided]…
meout = 300.0
    if args[:1] == ["--timeout"]:
        if len(args) < 2:
            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
            return 2
        timeout = float(args[1])
        args = args[2:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "-rfE",
        "-p",
        "no:cacheprovider",
        "--color=no",
        *args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
[assistant] The contract skill applies here: this changes a wait strategy's arguments, so the change touches the code, a test, a reno note, and the docs. Next I'll check the test file's timedelta pattern and confirm the project interpreter runs.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|timedelta\" tests/test_tenacity.py | head -40; echo ----; grep -n \"def test_fixed_sleep\" -A12 tests/test_tenacity.py; echo ----; grep -n \"def _assert_inclusive_range\" -A4 tests/test_tenacity.py; echo ----; PY=<work>/env-tenacity/bin/python; $PY -c \"import sys;print(sys.version)\"; sed -n 60,120p .lithify/harness/scripts/run_tests.py | grep -n \"exit=\\|HUNG\" ", "description": "Inspect test imports, timedelta pattern, and interpreter"}
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
248:        for delay in (1, datetime.timedelta(seconds=1)):
256:        for delay in (1, datetime.timedelt
…[859 chars elided]…
bTest():
301-                r = Retrying(
----
499:    def _assert_inclusive_range(self, wait: float, low: float, high: float) -> None:
500-        self.assertLessEqual(wait, high)
501-        self.assertGreaterEqual(wait, low)
502-
503-    def _assert_inclusive_epsilon(
----
3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
46:        print(f"HUNG IN: {hung}")
47:        print("exit=124 (see this script's docstring for the next step)")
49:    print(f"exit={code} (pytest); full log: {LOG}")
[assistant] The tests go in first, following the file's `subTest` pattern for number and timedelta twins. Each new test exercises only its own gap, so the red run fails for the reason named in the task.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n", "new_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jit
…[1111 chars elided]…
lf.assertEqual(fn(make_retry_state(3, 0)), 5)\n            self._assert_inclusive_range(fn(make_retry_state(4, 0)), 8, 9)\n\n    def test_wait_exponential_jitter_min_timedelta(self) -> None:\n        fn = tenacity.wait_exponential_jitter(\n            max=60, min=datetime.timedelta(seconds=5)\n        )\n        for _ in range(1000):\n            self.assertEqual(fn(make_retry_state(1, 0)), 5)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tests/test_tenacity.py has been updated successfully.
[assistant] Step 1 of the procedure: run the new tests alone against the unfixed code and read why each one fails.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_max_timedelta tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_jitter_timedelta tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min_timedelta > /tmp/red.txt 2>&1; echo \"rc=$?\"; grep -E \"Error|FAILED|PASSED|exit=|passed|failed\" /tmp/red.txt | head -30", "description": "Run new wait tests against unfixed code"}
[tool_result] rc=1
E       TypeError: unsupported operand type(s) for -: 'datetime.timedelta' and 'int'
~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/random.py:503: TypeError
E       TypeError: wait_exponential_jitter.__init__() got an unexpected keyword argument 'min'
tests/test_tenacity.py:635: TypeError
E       TypeError: wait_exponential_jitter.__init__() got an unexpected keyword argument 'min'
tests/test_tenacity.py:643: TypeError
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_max_timedelta
SUBFAILED(<subtest>) tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_jitter_timedelta
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min_timedelta
================ 4 failed, 1 passed, 1 subtests passed in 0.12s ================
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Three of the four fail for their own gap. The `max` timedelta failure message is ambiguous, so I'll check its traceback before going on.
[tool_use Bash] {"command": "grep -n \"_ TestWaitConditions.test_wait_exponential_jitter_max_timedelta\\|test_wait_exponential_jitter_max_timedelta\" -A3 /tmp/red.txt | head; awk '/test_wait_exponential_jitter_max_timedelta ___/,/test_wait_exponential_jitter_jitter/' /tmp/red.txt | grep -E \"^E |tenacity/wait.py|test_tenacity.py:\" | head", "description": "Confirm traceback for max-timedelta test"}
[tool_result] 36:FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_max_timedelta
37-SUBFAILED(<subtest>) tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_jitter_timedelta
38-FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
39-FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min_timedelta
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no \"tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_max_timedelta\" 2>&1 | grep -E \"^E |wait.py:|test_tenacity.py:[0-9]+:\" | head", "description": "Show error for max-timedelta test alone"}
[tool_result] tests/test_tenacity.py:623: 
E       TypeError: '<' not supported between instances of 'datetime.timedelta' and 'float'
tenacity/wait.py:271: TypeError
[assistant] Confirmed: the `max` test fails at `wait.py:271` on the timedelta comparison, and the `jitter` subtest fails inside `random.uniform`. Both are their own gaps. Now the fix, using the house pattern from `wait_exponential`: convert once in `__init__`, clamp in `__call__`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tenacity/wait.py", "old_string": "    \"\"\"Wait strategy that applies exponential backoff and jitter.\n\n    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.c
…[1756 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tenacity/wait.py has been updated successfully.
[assistant] The formula line in the docstring is over 88 characters. I'll reflow it before the checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tenacity/wait.py", "old_string": "    The wait time is max(minimum, min(initial * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count.", "new_string": "    The wait time is\n    max(minimum, min(initial * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/tenacity/wait.py has been updated successfully.
[assistant] Next, the four new tests and the existing `wait_exponential_jitter` test, run green through the harness runner.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py -k \"wait_exponential_jitter\" > /tmp/green.txt 2>&1; echo \"rc=$?\"; tail -4 /tmp/green.txt", "description": "Run wait_exponential_jitter tests after fix"}
[tool_result] rc=0

============= 5 passed, 117 deselected, 2 subtests passed in 0.09s =============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The unit tests pass. Next are the user docs and the reno note, which the contract requires for a user-visible change. Before writing the docs example I need to check for a name clash: an existing doctest block defines a function called `wait_exponential_jitter`.
[tool_use Bash] {"command": "grep -n \"wait_exponential_jitter\\|__all__\" tenacity/__init__.py | head; sed -n 80,95p doc/source/index.rst; grep -n \"testsetup\\|testcode\\|import datetime\" doc/source/index.rst | head -5", "description": "Check exports and doc testsetup block"}
[tool_result] 77:    wait_exponential_jitter,
750:__all__ = [
799:    "wait_exponential_jitter",
----------

Basic Retry
~~~~~~~~~~~

.. testsetup::

    import logging
    #
    # Note the following import is used for demonstration convenience only.
    # Production code should always explicitly import the names it needs.
    #
    from tenacity import *

    class MyException(Exception):
        pass
29:.. testcode::
85:.. testsetup::
100:.. testcode::
113:.. testcode::
123:.. testcode::
[assistant] The name is exported, and the later doctest block's `def wait_exponential_jitter()` would shadow it for any example that follows. So the new example goes above that block, and I'll give its function a distinct name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/doc/source/index.rst", "old_string": "When multiple processes are in contention for a shared resource, exponentially\nincreasing jitter helps minimise collisions.\n", "new_string": "Exponential backoff with jitter can also take a floor and a cap, and acce
…[301 chars elided]…
),\n        max=datetime.timedelta(seconds=60),\n        jitter=datetime.timedelta(seconds=1),\n    ))\n    def wait_exponential_jitter_2_to_60_s():\n        print(\"Wait 2 to 60 seconds, growing exponentially, with up to 1 second of jitter\")\n        raise Exception\n\nWhen multiple processes are in contention for a shared resource, exponentially\nincreasing jitter helps minimise collisions.\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/doc/source/index.rst has been updated successfully.
[assistant] That sentence about doctest ordering is internal detail and doesn't belong in user-facing prose. I'll remove it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/doc/source/index.rst", "old_string": "`datetime.timedelta` values as well as seconds. This example must come before\nthe ``wait_exponential_jitter`` block below, which redefines that name.\n", "new_string": "`datetime.timedelta` values as well as seconds.\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/comp-1/doc/source/index.rst has been updated successfully.
[assistant] Now the reno note. I'll generate the 16-hex suffix the contract requires and write a `features:` entry.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8) && echo \"$H\" && printf -- '---\\nfeatures:\\n  - |\\n    `wait_exponential_jitter` now accepts a `min` argument that sets a floor on\\n    the wait, and accepts `datetime.timedelta` values for `max`, `jitter` and\\n    `min` as well as numbers of seconds, matching `wait_exponential`.\\n' > releasenotes/notes/wait-exponential-jitter-min-timedelta-$H.yaml && c
…[139 chars elided]…
l-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python && $PY -c \"import yaml\" 2>/dev/null; $PY -c \"\nimport sys\ntry:\n    import yaml; print('yaml ok', yaml.safe_load(open(sys.argv[1])))\nexcept ImportError: print('no yaml module')\n\" releasenotes/notes/wait-exponential-jitter-min-timedelta-$H.yaml", "description": "Create reno release note and check YAML"}
[tool_result] 09d78566c62edd25
---
features:
  - |
    `wait_exponential_jitter` now accepts a `min` argument that sets a floor on
    the wait, and accepts `datetime.timedelta` values for `max`, `jitter` and
    `min` as well as numbers of seconds, matching `wait_exponential`.
no yaml module
[assistant] PyYAML isn't installed here, so I can't parse the note; its shape matches the existing `features:` notes. Next: the full suite via the runner, the stdlib lint substitute, and a quick run of the doc example's code, all in one step.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"run_tests rc=$?\"; tail -3 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_changed rc=$?\"; cat /tmp/check.t
…[313 chars elided]…
y import Retrying\nr = Retrying(wait=wait_exponential_jitter(initial=1, min=datetime.timedelta(seconds=2), max=datetime.timedelta(seconds=60), jitter=datetime.timedelta(seconds=1)), stop=stop_after_attempt(3))\nprint([round(r.wait(type('S',(),{'attempt_number':n,'outcome':None})()),3) for n in (1,2,3,4)])\n\" 2>&1 | tail -3", "description": "Run full suite, lint substitute, and doc example check"}
[tool_result] run_tests rc=0
============== 156 passed, 1 skipped, 14 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
check_changed rc=0
changed: doc/source/index.rst, releasenotes/notes/wait-exponential-jitter-min-timedelta-09d78566c62edd25.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
[assistant] Full suite is green (156 passed, 1 skipped) and `check_changed.py` passes. The doc-snippet check failed only because `-I` drops the working directory from the import path, so I'll rerun it with the repo on the path.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport datetime\nfrom types import SimpleNamespace as NS\nfrom tenacity import wait_exponential_jitter, wait_exponential\nw = wait_exponential_jitter(initial=1, min=datetime.timedelta(seconds=2), max=datetime.timedelta(seconds=60), jitter=datetime.timedelta(seconds=1))\nprint('doc example waits (2..60 floor/cap, 1s jitter):', [round(w(NS(attempt_number=n)),3) for n in (1,2,3,4,5,6,7,8)])\nprint('wait_exponential min/max numbers unchanged:', wait_exponential(min=4,max=10)(NS(attempt_number=1)))\n\"; git diff --stat", "description": "Check doc example waits and diff stats"}
[tool_result] doc example waits (2..60 floor/cap, 1s jitter): [2.0, 2.027, 4.858, 8.819, 16.432, 32.491, 60.0, 60.0]
wait_exponential min/max numbers unchanged: 4.0
 doc/source/index.rst   | 17 +++++++++++++++++
 tenacity/wait.py       | 19 ++++++++++++-------
 tests/test_tenacity.py | 29 +++++++++++++++++++++++++++++
 3 files changed, 58 insertions(+), 7 deletions(-)
[assistant] `wait_exponential_jitter` now takes `min`, and `max`, `jitter` and `min` accept either seconds or a `datetime.timedelta`. The full suite passes (156 passed, 1 skipped) and `check_changed.py` reports PASS. I haven't committed anything.

**What changed**
- **`tenacity/wait.py`**: `min` is a new last parameter, defaulting to 0. `max`, `jitter` and `min` are converted once in `__init__` with `_utils.to_seconds`. The result is clamped with the same expression `wait_exponential` uses, `max(max(0, self.min), min(result, self.max))`. With the default `min=0` the output is unchanged. `initial` and `exp
…[1004 chars elided]…
 break. The example's function name is distinct.

**Choices you may want to change**
- `min` is applied as a floor on the final result, so `min > max` returns `min`, the same as `wait_exponential`.
- I left `initial` as a plain float, since it is a scale factor and you didn't ask for it to change.

**Not run**
- ruff and mypy (unavailable in this environment).
- The Sphinx doctest build. I ran the doc example's logic directly instead; it produces floored and capped waits as expected.
- A YAML parse of the reno note; PyYAML isn't installed here. The file follows the shape of the existing notes.
