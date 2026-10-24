# trajectory base-1

final message:
A retrying object's `statistics` now includes `delay_since_first_attempt` from the start of each run, set to `0`. Before, the key only appeared after the first retry, so reading it during the first attempt raised `KeyError`.

The fix is one line in `begin()` in `tenacity/__init__.py`, which already resets `statistics` at the start of every run. The async retrier inherits that method, so it gets the fix too.

I added a regression test, `test_delay_since_first_attempt_present_before_first_retry`, to `tests/test_tenacity.py`. It reads the key from a `before` hook on the first attempt, expects `0`, and expects a positive value on the second attempt. It fails with `KeyError` without the fix and passes with it.

The project's test command passes: 136 passed, 1 skipped. I didn't add an async variant of the test; the async path shares `begin()`, but a dedicated async test would confirm it directly.

I didn't commit anything. The changes are in the working tree: `tenacity/__init__.py` and `tests/test_tenacity.py`.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" --include=*.py --include=*.md . | head -50", "description": "Find references to delay_since_first_attempt"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" . --exclude-dir=.git | head -50", "description": "Search repo for delay_since_first_attempt references"}
[tool_result] tests/test_asyncio.py:428:            "delay_since_first_attempt": mock.ANY,
tests/test_asyncio.py:453:                    "delay_since_first_attempt": mock.ANY,
tests/test_after.py:32:        delay_since_first_attempt = 0.1
tests/test_after.py:35:            self.previous_attempt_number, delay_since_first_attempt
tests/test_after.py:72:        delay_since_first_attempt = 0.1
tests/test_after.py:75:            self.previous_attempt_number, delay_since_first_attempt
tests/test_tenacity.py:57:    
…[227 chars elided]…
_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay_since_first_attempt)
tests/test_tenacity.py:1329:            "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:1346:                    "delay_since_first_attempt": mock.ANY,
tenacity/__init__.py:373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "sed -n 340,390p tenacity/__init__.py; echo ----; sed -n 130,160p tenacity/asyncio/__init__.py; echo ----; grep -n \"statistics\" tenacity/__init__.py tenacity/asyncio/__init__.py", "description": "Read retry statistics code in both modules"}
[tool_result]             return copy(f, *args, **kw)

        def retry_with(*args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]":
            return self.copy(*args, **kwargs).wraps(f)

        # Preserve attributes
        wrapped_f.retry = self  # type: ignore[attr-defined]
        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
        wrapped_f.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
     
…[4043 chars elided]…
.statistics["start_time"] = time.monotonic()
tenacity/__init__.py:355:        self.statistics["attempt_number"] = 1
tenacity/__init__.py:356:        self.statistics["idle_for"] = 0
tenacity/__init__.py:373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:432:            self.statistics["idle_for"] += sleep
tenacity/__init__.py:433:            self.statistics["attempt_number"] += 1
tenacity/__init__.py:614:    statistics: dict[str, t.Any]
[assistant] The fix belongs in `begin()`, which resets `statistics` at the start of each run. The async retrier inherits it, so one change covers both. I'll make the edit, then check the tests that assert on this dict.
[tool_use Edit] {"replace_all": false, "file_path": "<work>/env-tenacity/bin/python", "old_string": "x", "new_string": "y"}
[tool_result ERROR] <tool_use_error>File has NUL bytes in its first 8 KB: binary data, UTF-16/UTF-32 without a byte-order mark, or text with embedded NULs. These tools write UTF-8 (or UTF-16LE behind its byte-order mark) and never convert a file's encoding on their own, so nothing was written. If the file is text, make the change with a shell command that reads and writes it in its own encoding (iconv, or PowerShell Get-Content/Set-Content -Encoding), or ask the user whether to convert it to UTF-8 first. To replace the whole file with new UTF-8 text anyway, delete it first, then Write it.</tool_use_error>
[assistant] That edit was aimed at the wrong path (the Python binary) and was rejected, so nothing changed. I'll read the actual file and edit it.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "offset": 350, "limit": 10}
[tool_result] 350	        return t.cast("_RetryDecorated[P, R]", wrapped_f)
351	
352	    def begin(self) -> None:
353	        self.statistics.clear()
354	        self.statistics["start_time"] = time.monotonic()
355	        self.statistics["attempt_number"] = 1
356	        self.statistics["idle_for"] = 0
357	
358	    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
359	        self.iter_state.actions.append(fn)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll look at the existing statistics tests so the regression test matches their style.
[tool_use Bash] {"command": "sed -n 1300,1360p tests/test_tenacity.py; echo ----; sed -n 410,460p tests/test_asyncio.py", "description": "Read existing statistics tests in sync and async suites"}
[tool_result]     def test_retry_function_object(self) -> None:
        """Test that functools.wraps doesn't cause problems with callable objects.

        It raises an error upon trying to wrap it in Py2, because __name__
        attribute is missing. It's fixed in Py3 but was never backported.
        """

        class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
   
…[3183 chars elided]…
oroutine_with_2_attempts(NoIOErrorAfterCount(2))
                )
            except RetryError as exc:
                expected_stats = {
                    "attempt_number": 1,
                    "delay_since_first_attempt": mock.ANY,
                    "idle_for": mock.ANY,
                    "start_time": mock.ANY,
                }
                self.assertEqual(
                    _retryable_coroutine_with_2_attempts.statistics,
                    expected_stats,
                )
[assistant] I'll add a sync regression test right after the existing attributes test. It reads the key from inside the first attempt's `before` hook, which runs after `begin()`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})\n            else:\n                self.fail(\"RetryError should have been raised after 1 attempt\")\n\n\nclass TestRetryWith:", "ne
…[459 chars elided]…
istics[\"delay_since_first_attempt\"]\n            )\n\n        retrying = Retrying(\n            wait=tenacity.wait_fixed(0.01),\n            stop=tenacity.stop_after_attempt(2),\n            before=record_statistics,\n        )\n        self.assertTrue(retrying(NoneReturnUntilAfterCount(1)))\n        self.assertEqual(seen[0], 0)\n        self.assertGreater(seen[1], 0)\n\n\nclass TestRetryWith:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next I'll confirm the test file has the names I used and run the suite with the project's check command.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|NoneReturnUntilAfterCount\" tests/test_tenacity.py | head -30; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Check test imports and run the full test suite"}
[tool_result] 16:import contextlib
17:import datetime
18:import logging
19:import re
20:import time
21:import typing
22:import unittest
23:import warnings
24:from contextlib import contextmanager
25:from copy import copy
26:from fractions import Fraction
27:from unittest import mock
29:import pytest
30:from typeguard import check_type
32:import tenacity
33:from tenacity import RetryCallState, RetryError, Retrying, retry
787:class NoneReturnUntilAfterCount:
1118:        result = _retryable_test_with_wait(NoneR
…[1405 chars elided]…
r_cls(fut)
        if self.reraise:
            retry_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x1096c7fe0 state=finished raised TypeError>]

tenacity/__init__.py:424: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_delay_since_first_attempt_present_before_first_retry
1 failed, 135 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] The test failed because I passed a non-callable instance straight to `Retrying(...)`. The helper is meant to be an argument to a retried function, so I'll use `Retrying.call` instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "        self.assertTrue(retrying(NoneReturnUntilAfterCount(1)))\n        self.assertEqual(seen[0], 0)", "new_string": "        self.assertTrue(retrying.call(NoneReturnUntilAfterCount(1)))\n        self.assertEqual(seen[0], 0)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo ---; git stash list >/dev/null; git diff --stat; echo ---; git -c core.hooksPath=/dev/null status --short", "description": "Run full suite and show diff stat"}
[tool_result] tests/test_tenacity.py:1369: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_delay_since_first_attempt_present_before_first_retry
1 failed, 135 passed, 1 skipped, 12 subtests passed in 1.82s
---
 tenacity/__init__.py   |  1 +
 tests/test_tenacity.py | 17 +++++++++++++++++
 2 files changed, 18 insertions(+)
---
 M tenacity/__init__.py
 M tests/test_tenacity.py
[assistant] `Retrying` has no `call` method, so I'll check how `NoneReturnUntilAfterCount` is meant to be used and call it correctly.
[tool_use Bash] {"command": "sed -n 787,800p tests/test_tenacity.py; grep -n \"def __call__\" tenacity/__init__.py | head -3", "description": "Inspect test helper class and Retrying call signature"}
[tool_result] class NoneReturnUntilAfterCount:
    """Holds counter state for invoking a method several times in a row."""

    def __init__(self, count: int) -> None:
        self.counter = 0
        self.count = count

    def go(self) -> typing.Any:
        """Return None until after count threshold has been crossed.

        Then return True.
        """
        if self.counter < self.count:
            self.counter += 1
458:    def __call__(
470:    def __call__(
619:    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "        self.assertTrue(retrying.call(NoneReturnUntilAfterCount(1)))", "new_string": "        self.assertTrue(retrying(lambda c: c.go(), NoneReturnUntilAfterCount(1)))"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"--- without fix:\"; git stash push -q -m \"verify-regression\" -- tenacity/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k delay_since 2>&1 | tail -3; ref=$(git stash list --format='%H %gs' | grep verify-regression | cut -d' ' -f1); git stash apply -q \"$ref\" && git stash list --format='%H %gs' | grep -q \"$ref\" && s=$(git stash list --format='%gd %H %gs' | grep \"$ref\" | cut -d' ' -f1) && git stash drop -q \"$s\"; git diff --stat", "description": "Run suite, confirm test fails without fix, restore fix"}
[tool_result] tests/test_tenacity.py:1369: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_delay_since_first_attempt_present_before_first_retry
1 failed, 135 passed, 1 skipped, 12 subtests passed in 1.84s
--- without fix:
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_delay_since_first_attempt_present_before_first_retry
1 failed, 103 deselected in 0.04s
 tenacity/__init__.py   |  1 +
 tests/test_tenacity.py | 17 +++++++++++++++++
 2 files changed, 18 insertions(+)
[assistant] The test now runs but fails its own assertion. The default retry condition only retries on exceptions, so the `None` return never triggers a retry. I'll add `retry_if_result` so it retries until the helper returns `True`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "            stop=tenacity.stop_after_attempt(2),\n            before=record_statistics,", "new_string": "            stop=tenacity.stop_after_attempt(2),\n            retry=tenacity.retry_if_result(lambda result: result is None),\n            before=record_statistics,"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160131-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"--- without fix:\"; git stash push -q -m \"verify-regression-2\" -- tenacity/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenaci
…[67 chars elided]…
-3; ref=$(git stash list --format='%H %gs' | grep verify-regression-2 | cut -d' ' -f1); git stash apply -q \"$ref\"; s=$(git stash list --format='%gd %H %gs' | grep \"$ref\" | cut -d' ' -f1); [ -n \"$s\" ] && git stash drop -q \"$s\"; echo \"--- restored:\"; git diff --stat; git stash list | grep -c verify-regression || true", "description": "Run suite, verify test fails without fix, restore fix"}
[tool_result] ........................................................................ [ 96%]
.....                                                                    [100%]
136 passed, 1 skipped, 12 subtests passed in 1.96s
--- without fix:
E       KeyError: 'delay_since_first_attempt'
tests/test_tenacity.py:1361: KeyError
1 failed, 103 deselected in 0.05s
--- restored:
 tenacity/__init__.py   |  1 +
 tests/test_tenacity.py | 18 ++++++++++++++++++
 2 files changed, 19 insertions(+)
0
[assistant] A retrying object's `statistics` now includes `delay_since_first_attempt` from the start of each run, set to `0`. Before, the key only appeared after the first retry, so reading it during the first attempt raised `KeyError`.

The fix is one line in `begin()` in `tenacity/__init__.py`, which already resets `statistics` at the start of every run. The async retrier inherits that method, so it gets the fix too.

I added a regression test, `test_delay_since_first_attempt_present_before_first_retry`, to `tests/test_tenacity.py`. It reads the key from a `before` hook on the first attempt, expects `0`, and expects a positive value on the second attempt. It fails with `KeyError` without the fix and passes with it.

The project's test command passes: 136 passed, 1 skipped. I didn't add an async variant of the test; the async path shares `begin()`, but a dedicated async test would confirm it directly.

I didn't commit anything. The changes are in the working tree: `tenacity/__init__.py` and `tests/test_tenacity.py`.
