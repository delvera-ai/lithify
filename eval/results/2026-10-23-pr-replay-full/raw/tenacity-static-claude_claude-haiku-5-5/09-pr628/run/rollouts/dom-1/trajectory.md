# trajectory dom-1

final message:
`wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full suite passes (154 passed, 1 skipped) and the harness checker reports PASS. Changes are uncommitted.

**What changed**
- **`tenacity/wait.py`**: new `min` parameter, added last so existing positional calls like `wait_exponential_jitter(10, 5)` still work. `max`, `jitter` and `min` are converted to seconds once in `__init__`, and the result is clamped with `max(max(0, self.min), min(result, self.max))`, the same pattern `wait_exponential` uses. The class docstring formula is updated.
- **`tests/test_tenacity.py`**: `test_wait_exponential_jitter_min` and `test_wait_exponential_jitter_timedelta`. The timedelta test compares a timedelta-configured strategy against its numeric twin, following the house pattern.
- **`doc/source/index.rst`**: a short `wait_exponential_jitter` example with `min` and `timedelta` values, in the existing doctest style.
- **`releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9c2a7e1b5d8046.yaml`**: a `features:` note.

**Choices I made**
- `initial` stays a plain float. It is a scale factor, not a duration, and the request didn't name it. Say if you want it to accept timedeltas too.
- Attribute `self.max` is now stored in seconds, so it is a float rather than whatever value was passed in.

**Harness steps**
- Red run: both new tests failed against the unfixed code. The first version failed on the unknown `min` keyword, so I split the timedelta test so the `max`/`jitter` timedelta case fails first with the real `TypeError` in `random.uniform`.
- Green run: the new tests and the existing jitter test pass.
- Full suite: `exit=0`, 154 passed, 1 skipped.
- `check_changed.py`: `exit=0`, PASS, 0 problems.

**Skipped or not run**
- ruff and mypy were not run; they are unavailable in this environment.
- The Sphinx doctest for `index.rst` was not run. I only confirmed the example's strategy constructs and reads back the expected values.

## events
[assistant] I'll start by reading the project's change contract skill and the current `wait_exponential_jitter` code.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; grep -n \"wait_exponential\" -r tenacity/ doc/ releasenotes/ tests/ | head -50; echo ---; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Read change contract skill and locate wait code"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or 
…[18527 chars elided]…
l-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml:4:    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
---
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py; echo ...; sed -n 170,300p tenacity/wait.py; echo ---; grep -n \"time_unit_type\\|to_seconds\" -A8 tenacity/_utils.py | head -40; echo ---; sed -n 590,630p tests/test_tenacity.py; echo ---; sed -n 190,215p doc/source/index.rst; echo ---; ls releasenotes/notes | grep -i \"timedelta\\|wait-random-exp\\|jitter\"", "description": "Read wait strategies, utils, tests, docs"}
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
…[7100 chars elided]…
 for i in range(3)] +
                           [wait_fixed(7) for i in range(2)] +
                           [wait_fixed(9)]))
    def wait_fixed_chained():
        print("Wait 3s for 3 attempts, 7s for the next 2 attempts and 9s for all attempts thereafter")
        raise Exception

Whether to retry
---
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The change touches a strategy's constructor arguments, so the contract requires a reno note, a test, and a docs check. Before writing code I'll confirm the project Python exists and check the test file's imports.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -l $PY; grep -n \"^import\\|^from\" tests/test_tenacity.py | head -30; grep -n \"def _assert_inclusive_range\" -A4 tests/test_tenacity.py; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml", "description": "Check project python, test imports, reno precedent"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
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
499:    def _assert_inclusive_range(self, wait: float, low: float, high: float) -> None:
500-        self.assertLessEqual(wait, high)
501-        self.assertGreaterEqual(wait, low)
502-
503-    def _assert_inclusive_epsilon(
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
[assistant] The project Python is present. Following the harness order, I'll write the regression tests first, before touching the implementation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n\n", "new_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_ji
…[1044 chars elided]…
self.subTest(attempt=attempt):\n                self.assertEqual(\n                    fn(make_retry_state(attempt, 0)),\n                    expected(make_retry_state(attempt, 0)),\n                )\n\n        fn = tenacity.wait_exponential_jitter(jitter=datetime.timedelta(seconds=2))\n        for _ in range(1000):\n            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 1, 3)\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new tests against unfixed code (expect failure)"}
[tool_result] exit=1
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collected
…[1225 chars elided]…
wait_exponential_jitter.__init__() got an unexpected keyword argument 'min'

tests/test_tenacity.py:633: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta
============================== 2 failed in 0.08s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail, but on the unknown `min` keyword, which would hide whether the timedelta path itself is broken. I'll split the timedelta test so the `max`/`jitter` timedelta cases run before any `min` usage, so the red run shows the real timedelta failure.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tests/test_tenacity.py", "old_string": "    def test_wait_exponential_jitter_timedelta(self) -> None:\n        expected = tenacity.wait_exponential_jitter(max=60, jitter=0, min=5)\n        fn = tenacity.wait_exponential_jitter(\n            max=datetime.ti
…[1239 chars elided]…
     for _ in range(1000):\n            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 1, 3)\n\n        fn = tenacity.wait_exponential_jitter(\n            max=datetime.timedelta(seconds=60),\n            jitter=0,\n            min=datetime.timedelta(seconds=5),\n        )\n        self.assertEqual(fn(make_retry_state(1, 0)), 5)\n        self.assertEqual(fn(make_retry_state(8, 0)), 60)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta > /tmp/red2.txt 2>&1; echo \"exit=$?\"; grep -n \"Error\\|^E \" /tmp/red2.txt | head -10; tail -3 /tmp/red2.txt", "description": "Re-run timedelta test against unfixed code"}
[tool_result] exit=1
16:E       TypeError: unsupported operand type(s) for -: 'datetime.timedelta' and 'int'
18:~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/random.py:503: TypeError
============================== 10 failed in 0.19s ==============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The red run now fails on the real problem: `random.uniform` receives a `timedelta` jitter. Next I'll make the implementation change: accept `time_unit_type` for `max`, `jitter` and the new `min`, convert once in `__init__`, and clamp with the house floor/cap pattern from `wait_exponential`. `initial` stays a float because it's a scale factor, not a duration.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is min(initial * 2**n
…[1524 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/tenacity/wait.py has been updated successfully.
[assistant] Now the targeted tests should go green.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/green.txt", "description": "Run new and existing jitter tests after fix"}
[tool_result] exit=0
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter PASSED [100%]

===================== 3 passed, 9 subtests passed in 0.05s =====================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The targeted tests pass. Next is the contract's required docs and release-note items, so I'll check how `index.rst` imports names in its doctest blocks.
[tool_use Bash] {"command": "grep -n \"testsetup\\|^    from tenacity\\|import\" doc/source/index.rst | head -20; grep -n \"wait_random_exponential\\|^Sometimes it\" doc/source/index.rst | head; sed -n 1,20p releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml", "description": "Check doc doctest imports and reno precedent"}
[tool_result] 31:    import random
32:    from tenacity import retry
85:.. testsetup::
87:    import logging
89:    # Note the following import is used for demonstration convenience only.
90:    # Production code should always explicitly import the names it needs.
92:    from tenacity import *
319:    import logging
320:    import sys
334:    import logging
335:    import sys
351:    import logging
352:    import sys
431:    import logging
488:    import logging
545:    from tenacity import Retrying
606:    from unittest import mock
630:    import os
662:   from tenacity import Retrying, RetryError, stop_after_attempt
678:   from tenacity import AsyncRetrying, RetryError, stop_after_attempt
198:    @retry(wait=wait_random_exponential(multiplier=1, max=60))
204:Sometimes it's necessary to build a chain of backoffs.
---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
[assistant] The doctest setup does `from tenacity import *`, so the new strategy is in scope. I'll add a short example after the jitter section and the reno note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/doc/source/index.rst", "old_string": "        print(\"Randomly wait up to 2^x * 1 seconds between each retry until the range reaches 60 seconds, then randomly up to 60 seconds afterwards\")\n        raise Exception\n\n\nSometimes it's necessary", "new_stri
…[503 chars elided]…
       min=datetime.timedelta(seconds=2),\n                                        max=60,\n                                        jitter=datetime.timedelta(seconds=1)))\n    def wait_exponential_jitter_min():\n        print(\"Wait at least 2 seconds, then an exponentially growing delay plus up to 1 second of jitter, capped at 60 seconds\")\n        raise Exception\n\n\nSometimes it's necessary"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/doc/source/index.rst has been updated successfully.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9c2a7e1b5d8046.yaml", "content": "---\nfeatures:\n  - |\n    ``wait_exponential_jitter`` gains a ``min`` argument that sets a floor on the\n    wait, matching ``wait_exponential``. Its ``max``, ``jitter`` and ``min``\n    arguments accept ``datetime.timedelta`` values as well as numbers of seconds.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-203956-feature-wait-exponential-jitter/dom-1/releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9c2a7e1b5d8046.yaml (file state is current in your context — no need to Read it back)
[assistant] Now the full suite and the stdlib checker, both run in the foreground as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|exit=\" /tmp/full.txt | tail -3; echo ---; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt", "description": "Run full test suite and check_changed script"}
[tool_result] exit=0
============== 154 passed, 1 skipped, 21 subtests passed in 1.82s ==============
exit=0 (pytest); full log: /tmp/run_tests.log
---
exit=0
changed: doc/source/index.rst, releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9c2a7e1b5d8046.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The suite passes (154 passed, 1 skipped) and the checker reports PASS. As a last check I'll confirm the new docs example constructs and that the `min` floor holds with real timing.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport datetime\nfrom tenacity import *\n@retry(wait=wait_exponential_jitter(initial=1, min=datetime.timedelta(seconds=2), max=60, jitter=datetime.timedelta(seconds=1)))\ndef f(): raise Exception\nw = wait_exponential_jitter(initial=1, min=datetime.timedelta(seconds=2), max=60, jitter=datetime.timedelta(seconds=1))\nprint(w.min, w.max, w.jitter)\n\" ; git status --short", "description": "Smoke-test doc example and list changed files"}
[tool_result] 2.0 60.0 1.0
 M doc/source/index.rst
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-jitter-min-timedelta-3f9c2a7e1b5d8046.yaml
[assistant] `wait_exponential_jitter` now takes a `min` floor, and `max`, `jitter` and `min` accept either seconds or `datetime.timedelta`. The full suite passes (154 passed, 1 skipped) and the harness checker reports PASS. Changes are uncommitted.

**What changed**
- **`tenacity/wait.py`**: new `min` parameter, added last so existing positional calls like `wait_exponential_jitter(10, 5)` still work. `max`, `jitter` and `min` are converted to seconds once in `__init__`, and the result is clamped with `max(max(0, self.min), min(result, self.max))`, the same pattern `wait_exponential` uses. The class docstr
…[824 chars elided]…
d against the unfixed code. The first version failed on the unknown `min` keyword, so I split the timedelta test so the `max`/`jitter` timedelta case fails first with the real `TypeError` in `random.uniform`.
- Green run: the new tests and the existing jitter test pass.
- Full suite: `exit=0`, 154 passed, 1 skipped.
- `check_changed.py`: `exit=0`, PASS, 0 problems.

**Skipped or not run**
- ruff and mypy were not run; they are unavailable in this environment.
- The Sphinx doctest for `index.rst` was not run. I only confirmed the example's strategy constructs and reads back the expected values.
