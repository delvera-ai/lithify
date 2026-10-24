# trajectory inv-1

final message:
`statistics["delay_since_first_attempt"]` is now present from the start of each run, with value `0` until a delay has happened. The full suite passes (136 passed, 1 skipped).

**Cause:** `begin()` in `tenacity/__init__.py` reset `statistics` but didn't set this key. The key was only written in `_run_stop`, after the first failed attempt. The async `AsyncRetrying` inherits `begin()`, so the one-line fix covers both.

**Changes:**
- `tenacity/__init__.py`: `begin()` now sets `self.statistics["delay_since_first_attempt"] = 0`.
- `tests/test_tenacity.py`: new `TestStatistics.test_delay_since_first_attempt_present_from_first_attempt`. A `before` hook reads the key on the first attempt. It fails on HEAD with `KeyError: 'delay_since_first_attempt'`, as the fails-on-base check confirmed.
- `releasenotes/notes/fix-delay-since-first-attempt-statistics-5c1e9a0d3b7f2e48.yaml`: a `fixes:` note describing the behaviour.

**Choices I made:**
- The regression test is sync only. The async path shares `begin()`, but I didn't add a separate async test.
- I didn't run mypy or ruff. They aren't installed in the project interpreter, so the new code is annotated by hand to the strict-mypy and ruff conventions.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" --include='*.py' --include='*.rst' --include='*.yaml' . ; ls releasenotes/notes | tail -3; cat memory.md 2>/dev/null | head -20", "description": "Locate delay_since_first_attempt references"}
[tool_result] tests/test_tenacity.py:57:    delay_since_first_attempt: typing.Any,
tests/test_tenacity.py:66:        previous_attempt_number is _unset or delay_since_first_attempt is _unset
tests/test_tenacity.py:72:            delay_since_first_attempt=delay_since_first_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay_since_first_attempt)
tests/test_tenacity.py:1329:            "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:1346:                    "delay_since_
…[364 chars elided]…
:        delay_since_first_attempt = 0.1
tests/test_after.py:75:            self.previous_attempt_number, delay_since_first_attempt
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 340,400p tenacity/__init__.py; echo ----; sed -n 130,170p tenacity/asyncio/__init__.py; echo ----; grep -n \"statistics\" tenacity/__init__.py | head -30", "description": "Show statistics code in sync and async retry"}
[tool_result]             return copy(f, *args, **kw)

        def retry_with(*args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]":
            return self.copy(*args, **kwargs).wraps(f)

        # Preserve attributes
        wrapped_f.retry = self  # type: ignore[attr-defined]
        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
        wrapped_f.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
     
…[4028 chars elided]…
ined]
348:        wrapped_f.statistics = {}  # type: ignore[attr-defined]
353:        self.statistics.clear()
354:        self.statistics["start_time"] = time.monotonic()
355:        self.statistics["attempt_number"] = 1
356:        self.statistics["idle_for"] = 0
373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
432:            self.statistics["idle_for"] += sleep
433:            self.statistics["attempt_number"] += 1
614:    statistics: dict[str, t.Any]
[tool_use Bash] {"command": "grep -n \"def begin\" -A8 tenacity/asyncio/__init__.py tenacity/__init__.py; sed -n 1,30p tests/test_tenacity.py | head -5; grep -n \"statistics\" tests/test_tenacity.py | head; ls releasenotes/notes | head -3; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Inspect begin methods, tests, and release note format"}
[tool_result] tenacity/__init__.py:352:    def begin(self) -> None:
tenacity/__init__.py-353-        self.statistics.clear()
tenacity/__init__.py-354-        self.statistics["start_time"] = time.monotonic()
tenacity/__init__.py-355-        self.statistics["attempt_number"] = 1
tenacity/__init__.py-356-        self.statistics["idle_for"] = 0
tenacity/__init__.py-357-
tenacity/__init__.py-358-    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
tenacity/__init__.py-359-        self.iter_state.act
…[776 chars elided]…
t_exception_message_message.statistics
1320:        - statistics contains the value for the latest function run
1322:        - retry object statistics do not contain valid information
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex 
…[3093 chars elided]…
n> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "ls .lithify/harness/skills/tenacity-change-contract/scripts/ 2>&1; ls <work>/env-tenacity/bin/python 2>&1; cat memory.md 2>&1 | head; grep -n \"retry_state.seconds_since_start\\|def seconds_since_start\" -A3 tenacity/__init__.py | head -20; sed -n 1300,1360p tests/test_tenacity.py", "description": "Check harness scripts, interpreter, and existing tests"}
[tool_result] fails_on_base.py
<work>/env-tenacity/bin/python
cat: memory.md: No such file or directory
374:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
375-        self.iter_state.stop_run_result = self.stop(retry_state)
376-
377-    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
--
566:    def seconds_since_start(
…[2092 chars elided]…
f.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
                self.assertEqual(exc.last_attempt.attempt_number, 1)
                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})
            else:
                self.fail("RetryError should have been raised after 1 attempt")


class TestRetryWith:
    def test_redefine_wait(self) -> None:
        start = current_time_ms()
        result = _retryable_test_with_wait.retry_with(wait=tenacity.wait_fixed(0.1))(
[tool_use Bash] {"command": "grep -n \"retry_object\" tenacity/__init__.py | head -5; sed -n 17,50p tests/test_tenacity.py; grep -n \"^class \\|^def test_\" tests/test_tenacity.py | head -60", "description": "Check retry_object and test file structure"}
[tool_result] 478:        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
525:        retry_object: BaseRetrying,
533:        self.retry_object = retry_object
563:        return str(self.retry_object)
import datetime
import logging
import re
import time
import typing
import unittest
import warnings
from contextlib import contextmanager
from copy import copy
from fractions import Fraction
from unittest import mock

import pytest
from typeguard import check_type

import tenacity
…[1267 chars elided]…
ler):
1115:class TestDecoratorWrapper(unittest.TestCase):
1357:class TestRetryWith:
1395:class TestBeforeAfterAttempts(unittest.TestCase):
1548:class TestReraiseExceptions(unittest.TestCase):
1617:class TestStatistics(unittest.TestCase):
1638:class TestRetryErrorCallback(unittest.TestCase):
1671:class TestContextManager(unittest.TestCase):
1726:class TestInvokeAsCallable:
1796:class TestRetryException(unittest.TestCase):
1806:class TestRetryTyping(unittest.TestCase):
1841:class TestMockingSleep:
[tool_use Bash] {"command": "sed -n 1617,1638p tests/test_tenacity.py", "description": "View existing statistics test class"}
[tool_result] class TestStatistics(unittest.TestCase):
    def test_stats(self) -> None:
        @retry()
        def _foobar() -> int:
            return 42

        self.assertEqual({}, _foobar.statistics)
        _foobar()
        self.assertEqual(1, _foobar.statistics["attempt_number"])

    def test_stats_failing(self) -> None:
        @retry(stop=tenacity.stop_after_attempt(2))
        def _foobar() -> None:
            raise ValueError(42)

        self.assertEqual({}, _foobar.statistics)
        with contextlib.suppress(Exception):
            _foobar()
        self.assertEqual(2, _foobar.statistics["attempt_number"])


class TestRetryErrorCallback(unittest.TestCase):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):", "new_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n    d
…[385 chars elided]…
      calls += 1\n            if calls == 1:\n                raise ValueError(\"first attempt fails\")\n\n        Retrying(\n            stop=tenacity.stop_after_attempt(2),\n            wait=tenacity.wait_fixed(0),\n            before=before,\n        )(fail_once)\n        self.assertEqual(2, len(seen))\n        self.assertEqual(0, seen[0])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the release note, then the checks. The skill's fail-on-base script needs the new test IDs.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/releasenotes/notes/fix-delay-since-first-attempt-statistics-5c1e9a0d3b7f2e48.yaml", "content": "---\nfixes:\n  - |\n    The ``delay_since_first_attempt`` key is now present in ``statistics`` from\n    the start of each run, with value ``0`` until a delay has occurred. Previously\n    the key was only added after the first retry, so reading\n    ``statistics[\"delay_since_first_attempt\"]`` during the first attempt raised\n    ``KeyError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/inv-1/releasenotes/notes/fix-delay-since-first-attempt-statistics-5c1e9a0d3b7f2e48.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_tenacity.py::TestStatistics::test_delay_since_first_attempt_present_from_first_attempt\" 2>&1 | tail -30; echo \"exit=$?\"", "description": "Write release note and check new test fails on base"}
[tool_result] >       Retrying(
            stop=tenacity.stop_after_attempt(2),
            wait=tenacity.wait_fixed(0),
            before=before,
        )(fail_once)

tests/test_tenacity.py:1652: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/__init__.py:479: in __call__
    do = self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/__init__.py:380: in iter
    result = action(retry_state)
             ^^^^^^^^^^^^^^^^^^^
_ _ _ 
…[327 chars elided]…
])
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'delay_since_first_attempt'

tests/test_tenacity.py:1642: KeyError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatistics::test_delay_since_first_attempt_present_from_first_attempt
1 failed in 0.06s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
exit=0
[assistant] The new test fails on HEAD with the reported `KeyError`. Now the full suite, after the final edit.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ...........s................................................ [ 43%]
........................................................................ [ 96%]
.....                                                                    [100%]
136 passed, 1 skipped, 12 subtests passed in 1.80s
 M tenacity/__init__.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-delay-since-first-attempt-statistics-5c1e9a0d3b7f2e48.yaml
[assistant] `statistics["delay_since_first_attempt"]` is now present from the start of each run, with value `0` until a delay has happened. The full suite passes (136 passed, 1 skipped).

**Cause:** `begin()` in `tenacity/__init__.py` reset `statistics` but didn't set this key. The key was only written in `_run_stop`, after the first failed attempt. The async `AsyncRetrying` inherits `begin()`, so the one-line fix covers both.

**Changes:**
- `tenacity/__init__.py`: `begin()` now sets `self.statistics["delay_since_first_attempt"] = 0`.
- `tests/test_tenacity.py`: new `TestStatistics.test_delay_since_first
…[29 chars elided]…
ttempt`. A `before` hook reads the key on the first attempt. It fails on HEAD with `KeyError: 'delay_since_first_attempt'`, as the fails-on-base check confirmed.
- `releasenotes/notes/fix-delay-since-first-attempt-statistics-5c1e9a0d3b7f2e48.yaml`: a `fixes:` note describing the behaviour.

**Choices I made:**
- The regression test is sync only. The async path shares `begin()`, but I didn't add a separate async test.
- I didn't run mypy or ruff. They aren't installed in the project interpreter, so the new code is annotated by hand to the strict-mypy and ruff conventions.

Nothing is committed.
