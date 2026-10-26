# trajectory base-1

final message:
A falsy callable wait strategy is now called in both the sync and async retry loops. Only `None` and numeric zero (which covers `sum([])`) still mean no wait. The full suite passes: 185 passed, 1 skipped.

**Change:**
- `tenacity/__init__.py` (`BaseRetrying._run_wait`) and `tenacity/asyncio/__init__.py` (`AsyncRetrying._run_wait`) replace `if not self.wait` with `if self.wait is None or (isinstance(self.wait, (int, float)) and not self.wait)`.

**Tests added (existing tests untouched):**
- `tests/test_tenacity.py::test_falsy_callable_wait_is_called` covers a class with `__bool__` returning False and one with `__len__` returning 0. It asserts each is called once.
- `tests/test_asyncio.py::test_falsy_callable_wait_is_called` covers the async path with a `__bool__`-False strategy and asserts it is called once per retry.

I did not run the new tests against the original code to confirm they fail there. By inspection, the old `not self.wait` check skips those objects, so their call counters would stay at zero.

## events
[tool_use Bash] {"command": "grep -rn \"wait\" --include=*.py -l . | grep -v test | head -30; ls", "description": "Find files referencing wait in the repo"}
[tool_result] (eval):1: no matches found: --include=*.py
AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
[tool_use Bash] {"command": "grep -rn \"wait\" tenacity/*.py | grep -n \"if \\|not \\|self.wait\\|_wait\" | head -60", "description": "Search for wait conditionals in tenacity package"}
[tool_result] 16:tenacity/__init__.py:267:        self.wait = wait
18:tenacity/__init__.py:300:            wait=_first_set(wait, self.wait),
19:tenacity/__init__.py:332:            f"wait={self.wait}, "
20:tenacity/__init__.py:420:    def _run_wait(self, retry_state: "RetryCallState") -> None:
23:tenacity/__init__.py:425:        if not self.wait:  # type: ignore[truthy-bool]
24:tenacity/__init__.py:428:            retry_state.upcoming_sleep = self.wait(retry_state)
25:tenacity/__init__.py:466:        self._ad
…[326 chars elided]…
ds(min)
77:tenacity/wait.py:86:        self.wait_random_max = _utils.to_seconds(max)
78:tenacity/wait.py:90:        return self.wait_random_min + (
79:tenacity/wait.py:91:            random.random() * (self.wait_random_max - self.wait_random_min)
82:tenacity/wait.py:99:        self.wait_funcs = strategies
83:tenacity/wait.py:103:        # Positional, like `BaseRetrying._run_wait`: a `WaitBaseT` callable is
84:tenacity/wait.py:107:        return float(sum(x(retry_state) for x in self.wait_funcs))
[tool_use Bash] {"command": "sed -n 410,440p tenacity/__init__.py; echo ----; grep -n \"_run_wait\\|wait\" tenacity/asyncio/__init__.py | head -30; echo ----; sed -n 90,112p tenacity/wait.py; echo ----; grep -rn \"wait\" tenacity/*.py | grep -i \"async\\|__bool__\" ; grep -rn \"__bool__\\|__len__\" tenacity/ ", "description": "Inspect sync wait logic, async retry, and wait sum class"}
[tool_result]         self.statistics["attempt_number"] = 1
        self.statistics["idle_for"] = 0
        self.statistics["delay_since_first_attempt"] = 0

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)

    def _run_retry(self, retry_state: "RetryCallState") -> None:
        self.iter_state.retry_run_result = self.retry(retry_state)

    def _run_wait(self, retry_state: "RetryCallState") -> None:
        # `wait` is annotated as always set, so
…[2953 chars elided]…
ait_funcs = strategies

    @override
    def __call__(self, retry_state: "RetryCallState") -> float:
        # Positional, like `BaseRetrying._run_wait`: a `WaitBaseT` callable is
        # only guaranteed to take the state positionally, so passing it by
        # keyword crashed on any callable whose parameter is not named
        # `retry_state`.
        return float(sum(x(retry_state) for x in self.wait_funcs))


class wait_chain(wait_base):
    """Chain two or more waiting strategies.

----
[assistant] The bug is the `if not self.wait` guard in both loops. I'll check the async version and the existing tests before changing it.
[tool_use Bash] {"command": "sed -n 150,165p tenacity/asyncio/__init__.py; echo ----; grep -rn \"wait=0\\|wait=None\\|sum(\\[\\])\\|wait_none\\|falsy\\|__bool__\" tests | head -20", "description": "View async wait logic and related existing tests"}
[tool_result]             retry_state
        )

    @override
    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        # See BaseRetrying._run_wait: falsy `wait` values mean "no wait" and
        # reach us from untyped callers.
        if not self.wait:  # type: ignore[truthy-bool]
            retry_state.upcoming_sleep = 0.0
        else:
            retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
                retry_state
          
…[403 chars elided]…
y:509:    def test_wait_falsy_values_mean_no_wait(self) -> None:
tests/test_tenacity.py:510:        # Untyped callers pass None or 0 to mean "no wait", and `sum([])`
tests/test_tenacity.py:524:        for wait in (None, 0, sum([])):
tests/test_tenacity.py:1717:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1732:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1752:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1771:            wait=tenacity.wait_none(),
[tool_use Bash] {"command": "sed -n 505,540p tests/test_tenacity.py; echo ----; sed -n 84,105p tests/test_asyncio.py", "description": "Read existing falsy-wait tests in sync and async suites"}
[tool_result]             w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

    def test_wait_falsy_values_mean_no_wait(self) -> None:
        # Untyped callers pass None or 0 to mean "no wait", and `sum([])`
        # over an empty list of strategies yields the int 0. All must reach
        # the retry path without blowing up inside iter().
        def make_flaky() -> typing.Callable[[], str]:
            attempts = []

            def flaky() -> 
…[1242 chars elided]…
2)
            retrying = AsyncRetrying(
                wait=wait,  # type: ignore[arg-type]
                stop=stop_after_attempt(5),
            )
            await retrying(_async_function, thing)
            assert thing.counter == thing.count

    @asynctest
    async def test_iscoroutinefunction(self) -> None:
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
        thing = NoIOErrorAfterCount(5)
[assistant] The root cause is clear: `if not self.wait` treats any falsy object as "no wait". I'll narrow the no-wait check to `None` and numeric zero in both loops, then add regression tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tenacity/__init__.py", "old_string": "        # `wait` is annotated as always set, so a type checker sees this guard\n        # as always true -- but untyped callers legitimately pass `None` or `0`\n        # to mean \"no wait\", and `sum([])` over an em
…[316 chars elided]…
lers legitimately pass `None` or `0`\n        # to mean \"no wait\", and `sum([])` over an empty list of strategies\n        # yields the int 0. Keep honouring those, but only those: any other\n        # value (including a callable that is falsy) must be called.\n        if self.wait is None or (isinstance(self.wait, (int, float)) and not self.wait):\n            retry_state.upcoming_sleep = 0.0"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tenacity/asyncio/__init__.py", "old_string": "        # See BaseRetrying._run_wait: falsy `wait` values mean \"no wait\" and\n        # reach us from untyped callers.\n        if not self.wait:  # type: ignore[truthy-bool]\n            retry_state.upcoming_sleep = 0.0", "new_string": "        # See BaseRetrying._run_wait: only `None` and numeric zero mean \"no\n        # wait\"; any other `wait` value, even a falsy callable, must be called.\n        if self.wait is None or (isinstance(self.wait, (int, float)) and not self.wait):\n            retry_state.upcoming_sleep = 0.0"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py", "old_string": "    def test_wait_radd_plain_callable(self) -> None:", "new_string": "    def test_falsy_callable_wait_is_called(self) -> None:\n        # A falsy wait strategy (empty container, or __bool__ -> False) is\n        #
…[805 chars elided]…
                self.assertEqual(wait.calls, 1)\n\n    @staticmethod\n    def _make_flaky_twice() -> typing.Callable[[], str]:\n        attempts = []\n\n        def flaky() -> str:\n            attempts.append(1)\n            if len(attempts) < 2:\n                raise ValueError(\"boom\")\n            return \"ok\"\n\n        return flaky\n\n    def test_wait_radd_plain_callable(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_iscoroutinefunction(self) -> None:", "new_string": "    @asynctest\n    async def test_falsy_callable_wait_is_called(self) -> None:\n        # A falsy wait strategy must be called,
…[247 chars elided]…
retry_state.attempt_number)\n                return 0.0\n\n        thing = NoIOErrorAfterCount(2)\n        retrying = AsyncRetrying(wait=FalsyWait(), stop=stop_after_attempt(5))  # type: ignore[arg-type]\n        await retrying(_async_function, thing)\n        assert thing.counter == thing.count\n        assert calls == [1]\n\n    @asynctest\n    async def test_iscoroutinefunction(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Running the suite with the project's required interpreter. I'll also verify the async test's expected call count against the helper class.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; grep -n \"^import typing\\|^import\\|class NoIOErrorAfterCount\" -A6 tests/test_asyncio.py | head -30", "description": "Run the project test suite and check async test helpers"}
[tool_result] ....F..............s........................................................................................................... [ 68%]
...........................................................              [100%]
=================================== FAILURES ===================================
________________ TestAsyncio.test_falsy_callable_wait_is_called ________________

self = <tests.test_asyncio.TestAsyncio testMethod=test_falsy_callable_wait_is_called>

    @asynctest
    async def test_f
…[701 chars elided]…
.py::TestAsyncio::test_falsy_callable_wait_is_called
1 failed, 184 passed, 1 skipped, 17 subtests passed in 1.87s
15:import asyncio
16:import inspect
17:import unittest
18-from collections.abc import Callable, Coroutine
19-from functools import wraps
20-from typing import Any, TypeVar
21-from unittest import mock
22-
23-try:
--
30:import pytest
31-
32:import tenacity
33-from tenacity import (
34-    AsyncRetrying,
35-    RetryCallState,
36-    RetryError,
37-    retry,
38-    retry_if_exception,
[assistant] The async test file imports `Any`, not `typing`. I'll fix that import and check the expected call count against the helper class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py", "old_string": "            def __call__(self, retry_state: typing.Any) -> float:\n                calls.append(retry_state.attempt_number)\n                return 0.0\n\n        thing = NoIOErrorAfterCount(2)\n        retrying = A
…[279 chars elided]…
ate) -> float:\n                calls.append(retry_state.attempt_number)\n                return 0.0\n\n        thing = NoIOErrorAfterCount(2)\n        retrying = AsyncRetrying(wait=FalsyWait(), stop=stop_after_attempt(5))  # type: ignore[arg-type]\n        await retrying(_async_function, thing)\n        assert thing.counter == thing.count\n        assert calls == list(range(1, thing.count + 1))"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git stash list >/dev/null; git diff --stat", "description": "Rerun test suite and show diff stats"}
[tool_result] ...................s........................................................................................................... [ 68%]
...........................................................              [100%]
185 passed, 1 skipped, 17 subtests passed in 1.86s
 tenacity/__init__.py         |  5 +++--
 tenacity/asyncio/__init__.py |  6 +++---
 tests/test_asyncio.py        | 19 +++++++++++++++++++
 tests/test_tenacity.py       | 37 +++++++++++++++++++++++++++++++++++++
 4 files changed, 62 insertions(+), 5 deletions(-)
[assistant] All 185 tests pass. I'll check line lengths, since two of the new lines are long.
[tool_use Bash] {"command": "git diff -U0 | grep '^+' | awk 'length($0) > 89 {print length($0)\": \"$0}'; grep -n \"line-length\" pyproject.toml", "description": "Check added lines against configured line length"}
[tool_result] 105: +        retrying = AsyncRetrying(wait=FalsyWait(), stop=stop_after_attempt(5))  # type: ignore[arg-type]
103: +                r = Retrying(wait=wait, stop=tenacity.stop_after_attempt(3))  # type: ignore[arg-type]
97:line-length = 88
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py", "old_string": "        retrying = AsyncRetrying(wait=FalsyWait(), stop=stop_after_attempt(5))  # type: ignore[arg-type]", "new_string": "        retrying = AsyncRetrying(\n            wait=FalsyWait(),  # type: ignore[arg-type]\n            stop=stop_after_attempt(5),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py", "old_string": "                r = Retrying(wait=wait, stop=tenacity.stop_after_attempt(3))  # type: ignore[arg-type]", "new_string": "                r = Retrying(\n                    wait=wait,  # type: ignore[arg-type]\n                    stop=tenacity.stop_after_attempt(3),\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163607-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Rerun test suite after formatting fixes"}
[tool_result] ...........................................................              [100%]
185 passed, 1 skipped, 17 subtests passed in 2.05s
[assistant] A falsy callable wait strategy is now called in both the sync and async retry loops. Only `None` and numeric zero (which covers `sum([])`) still mean no wait. The full suite passes: 185 passed, 1 skipped.

**Change:**
- `tenacity/__init__.py` (`BaseRetrying._run_wait`) and `tenacity/asyncio/__init__.py` (`AsyncRetrying._run_wait`) replace `if not self.wait` with `if self.wait is None or (isinstance(self.wait, (int, float)) and not self.wait)`.

**Tests added (existing tests untouched):**
- `tests/test_tenacity.py::test_falsy_callable_wait_is_called` covers a class with `__bool__` returning False and one with `__len__` returning 0. It asserts each is called once.
- `tests/test_asyncio.py::test_falsy_callable_wait_is_called` covers the async path with a `__bool__`-False strategy and asserts it is called once per retry.

I did not run the new tests against the original code to confirm they fail there. By inspection, the old `not self.wait` check skips those objects, so their call counters would stay at zero.
