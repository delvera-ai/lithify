# trajectory comp-1

final message:
`func.statistics` now stays visible through a `functools.wraps` wrapper, for both sync and async `@retry` functions. The outer wrapper's `statistics` is the same object as the inner one's, and it updates as the call runs.

**Cause:** `functools.wraps` copies the inner function's attributes once, at decoration time. Each call then rebound `wrapped_f.statistics` to a fresh dict, so the outer wrapper kept the original empty `{}`.

**Fix:**
- `tenacity/__init__.py` (`BaseRetrying.wraps`) and `tenacity/asyncio/__init__.py` (`AsyncRetrying.wraps`) create one dict per decorated function and never rebind it.
- Each call still runs on its own statistics dict, so recursive or concurrent calls don't clear each other's values. A new `_StatisticsMirror` dict copies every write into the shared dict. The shared dict is also `fn.retry.statistics`, so `fn.retry.statistics is fn.statistics` still holds.
- My first attempt refreshed the shared dict only when a call finished. That broke the existing `test_delay_since_first_attempt_available_on_first_attempt`, which reads `fn.statistics` from inside the function body. I replaced it with the mirror, which keeps that test passing.

**Tests:**
- Added `test_statistics_visible_through_functools_wraps` to `TestDecoratorWrapper` in `tests/test_tenacity.py` and `tests/test_asyncio.py`. Both failed on the unfixed code because the outer `statistics` was `{}`, and pass now.
- Full suite (`run_tests.py`): exit 0, 167 passed, 1 skipped.
- `check_changed.py`: PASS, 0 problems. ruff and mypy were not run, since they aren't available here.
- No existing test was edited.

**Behaviour to know about:**
- `fn.statistics` is a plain dict that is now shared across calls on the same function. Concurrent calls overwrite each other's values, so the last writer wins. Before this change the last call to start won, so the practical difference is small. Per-thread reads still go through `fn.retry.statistics`.
- I added `reno` note `releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml` (a `fixes:` entry).

I didn't update the docs in `doc/source/index.rst`, since this fix changes no documented usage.

## events
[assistant] I'll start by reading the relevant code and the change-contract skill the project harness points to for this kind of change.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; grep -n \"statistics\\|wraps\\|def wraps\\|def retry\\b\" tenacity/__init__.py | head -80", "description": "Read change-contract skill and locate statistics code"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, th
…[27956 chars elided]…
istics["idle_for"] = 0
391:        self.statistics["delay_since_first_attempt"] = 0
408:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
467:            self.statistics["idle_for"] += sleep
468:            self.statistics["attempt_number"] += 1
656:    statistics: dict[str, t.Any]
683:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
687:def retry(
705:def retry(
722:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
754:        return r.wraps(f)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", "offset": 355, "limit": 35}
[tool_result] 355	        return self._local.iter_state  # type: ignore[no-any-return]
356	
357	    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
358	        """Wrap a function for retrying.
359	
360	        :param f: A function to wrap for retrying.
361	        """
362	
363	        @functools.wraps(
364	            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
365	        )
366	        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:
367	            if not self.en
…[591 chars elided]…

378	
379	        # Preserve attributes
380	        wrapped_f.retry = self  # type: ignore[attr-defined]
381	        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
382	        wrapped_f.statistics = {}  # type: ignore[attr-defined]
383	
384	        return t.cast("_RetryDecorated[P, R]", wrapped_f)
385	
386	    def begin(self) -> None:
387	        self.statistics.clear()
388	        self.statistics["start_time"] = time.monotonic()
389	        self.statistics["attempt_number"] = 1
[tool_use Bash] {"command": "grep -n \"statistics\\|def wraps\\|async_wrapped\\|copy = self.copy\\|wraps(\" tenacity/asyncio/__init__.py; grep -n \"statistics\" tests/test_tenacity.py | head -30; grep -n \"class TestDecoratorWrapper\" -A30 tests/test_tenacity.py | head -60", "description": "Inspect async wraps and existing statistics tests"}
[tool_result] 153:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
200:    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
201:        wrapped = super().wraps(fn)
204:        @functools.wraps(
207:        async def async_wrapped(*args: t.Any, **kwargs: t.Any) -> t.Any:
212:            copy = self.copy()
213:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
214:            self._local.statistics = copy.statistics
218:     
…[3418 chars elided]…
:
1269-            _retryable_test_with_stop(NoIOErrorAfterCount(5))
1270-            self.fail("Expected IOError")
1271-        except OSError as re:
1272-            self.assertTrue(isinstance(re, IOError))
1273-            print(re)
1274-
1275-    def test_retry_if_exception_of_type(self) -> None:
1276-        self.assertTrue(_retryable_test_with_exception_type_io(NoIOErrorAfterCount(5)))
1277-
1278-        try:
1279-            _retryable_test_with_exception_type_io(NoNameErrorAfterCount(5))
[tool_use Bash] {"command": "sed -n 1440,1540p tests/test_tenacity.py; echo ----; sed -n 1855,1895p tests/test_tenacity.py; echo ----; sed -n 195,225p tenacity/asyncio/__init__.py; echo ----; git log --oneline -3 -- tenacity/__init__.py; ls releasenotes/notes | tail -3", "description": "Read existing statistics tests and async wraps"}
[tool_result]         class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
        )
        h = retrying.wraps(Hello())
        self.assertEqual(h(), "Hello")

    def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.

        - statistics contains the value for the latest function run
        - re
…[5809 chars elided]…
istics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
----
868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The root cause is clear: `functools.wraps` copies the inner `__dict__` once at decoration, but the inner wrapper rebinds `statistics` on every call, so the outer wrapper keeps the original `{}`. Before changing anything, I'll write the regression tests and confirm they fail on the current code. First I need the test file layout and the project Python.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_tenacity.py | grep -n \"import\"; echo ----; grep -n \"class TestDecoratorWrapper\" -A3 tests/test_asyncio.py; grep -n \"^from\\|^import\" tests/test_asyncio.py; echo ----; ls <work>/env-tenacity/bin/python && echo PY_OK; ls releasenotes/notes | wc -l; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Inspect test imports and python env"}
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
----
496:class TestDecoratorWrapper(unittest.TestCase):
497-    @asynctest
498-    async def test_retry_fun
…[327 chars elided]…
test
32:import tenacity
33:from tenacity import (
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
----
<work>/env-tenacity/bin/python
PY_OK
      49
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Bash] {"command": "sed -n 496,530p tests/test_asyncio.py; echo ----; grep -n \"^class TestDecoratorWrapper\\|^class TestStatistics\" tests/test_tenacity.py; sed -n 1249,1252p tests/test_tenacity.py; grep -n \"asynctest\" tests/test_asyncio.py | head -3", "description": "Read async decorator test shape"}
[tool_result] class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.

        - statistics contains the value for the latest function run
        - retry object can be modified to change its behaviour (useful to patch in tests)
        - retry object statistics are synced with function statistics
        """

        self.assertTrue(
            await _retryable_coro
…[601 chars elided]…
    "stop",
            tenacity.stop_after_attempt(1),
        ):
            try:
----
1249:class TestDecoratorWrapper(unittest.TestCase):
1493:class TestStatisticsKeys:
1857:class TestStatistics(unittest.TestCase):
class TestDecoratorWrapper(unittest.TestCase):
    def test_with_wait(self) -> None:
        start = current_time_ms()
        result = _retryable_test_with_wait(NoneReturnUntilAfterCount(5))
54:def asynctest(callable_: _F) -> Callable[..., Any]:
80:    @asynctest
86:    @asynctest
[assistant] I'll add the sync regression test next to the existing decorator tests, and the async one in the matching class. Both check that an outer `functools.wraps` wrapper exposes the same dict object and the real attempt count.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_tenacity.py", "old_string": "class TestDecoratorWrapper(unittest.TestCase):\n    def test_with_wait(self) -> None:", "new_string": "class TestDecoratorWrapper(unittest.TestCase):\n    def test_statistics_visible_through_functools_wraps(self) -
…[519 chars elided]…
         nonlocal attempts\n            attempts += 1\n            if attempts < 3:\n                raise ValueError(\"fail\")\n            return attempts\n\n        outer = timing(_foobar)\n        self.assertEqual(3, outer())\n        self.assertIs(_foobar.statistics, outer.statistics)\n        self.assertEqual(3, outer.statistics[\"attempt_number\"])\n\n    def test_with_wait(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_tenacity.py", "old_string": "import contextlib\nimport datetime\nimport logging", "new_string": "import contextlib\nimport datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from tenacity import\\|^    retry,\\|_retryable_coroutine_with_2_attempts(\" -A0 tests/test_asyncio.py | head; sed -n 33,42p tests/test_asyncio.py; grep -n \"^async def _retryable_coroutine_with_2_attempts\\|^@retry\" -A1 tests/test_asyncio.py | head -8", "description": "Check async test helper imports"}
[tool_result] 33:from tenacity import (
37:    retry,
42:from tenacity import asyncio as tasyncio
74:async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
102:            await _retryable_coroutine_with_2_attempts(thing)
507:            await _retryable_coroutine_with_2_attempts(NoIOErrorAfterCount(1))
532:                    await _retryable_coroutine_with_2_attempts(NoIOErrorAfterCount(2))
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
67:@retry
68-async def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Any:
--
73:@retry(stop=stop_after_attempt(2))
74:async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
75-    await asyncio.sleep(0.00001)
--
560:@retry(sleep=my_async_sleep)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_asyncio.py", "old_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n    async def test_retry_function_attributes(self) -> None:", "new_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n    async 
…[572 chars elided]…
mpts += 1\n            if attempts < 3:\n                raise ValueError(\"fail\")\n            return attempts\n\n        outer = timing(_foobar)\n        self.assertEqual(3, await outer())\n        self.assertIs(_foobar.statistics, outer.statistics)\n        self.assertEqual(3, outer.statistics[\"attempt_number\"])\n\n    @asynctest\n    async def test_retry_function_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now I'll run the two new tests alone against the unfixed code, as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
tests/test_tenacity.py:1275: AssertionError
_____ TestDecoratorWrapper.test_statistics_visible_through_functools_wraps _____

self = <tests.test_asyncio.TestDecoratorWrapper testMethod=test_statistics_visible_through_functools_wraps>

    @asynctest
    async def test_statistics_visible_through_functools_wraps(self) -> None:
        """An outer functools.wraps decorator must expose the real statistics."""
    
        def timing(
            f: Callable[..., Any],
        ) -> Callable[..
…[691 chars elided]…
t_attempt': 5.875001079402864e-05} is not {}

tests/test_asyncio.py:522: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps
============================== 2 failed in 0.07s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail for the reported reason: the outer wrapper's `statistics` is the stale decoration-time `{}`. Now the fix. Each decorated function gets one dict object created at decoration. Each call still works on its own copy, and the shared dict is refreshed in place when the call finishes, so `functools.wraps` copies keep seeing the results.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", "old_string": "        @functools.wraps(\n            f, functools.WRAPPER_ASSIGNMENTS + (\"__defaults__\", \"__kwdefaults__\")\n        )\n        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:\n            if not self.enabled
…[930 chars elided]…
te a copy to prevent overwriting the local contexts when\n            # calling the same wrapped functions multiple times in the same stack\n            copy = self.copy()\n            self._local.statistics = copy.statistics\n            try:\n                return copy(f, *args, **kw)\n            finally:\n                statistics.clear()\n                statistics.update(copy.statistics)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", "old_string": "        wrapped_f.statistics = {}  # type: ignore[attr-defined]", "new_string": "        wrapped_f.statistics = statistics  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py", "old_string": "        @functools.wraps(\n            fn, functools.WRAPPER_ASSIGNMENTS + (\"__defaults__\", \"__kwdefaults__\")\n        )\n        async def async_wrapped(*args: t.Any, **kwargs: t.Any) -> t.Any:\n        
…[1626 chars elided]…
)  # type: ignore[type-var]\n            finally:\n                statistics.clear()\n                statistics.update(copy.statistics)\n\n        # Preserve attributes\n        async_wrapped.retry = self  # type: ignore[attr-defined]\n        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]\n        async_wrapped.statistics = statistics  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next, the release note (the change-contract skill requires one for user-visible fixes), then the two new tests green, then the full suite.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml", "content": "---\nfixes:\n  - |\n    ``func.statistics`` is now visible through another decorator that uses\n    ``functools.wraps`` on a ``@retry``-decorated function, for both sync and\n    async functions. Previously the outer wrapper kept the empty dict it copied\n    at decoration time. ``func.statistics`` is now one dict per decorated\n    function, refreshed when each call finishes, so it is updated after a call\n    rather than live during the call. Use ``func.retry.statistics`` to read\n    statistics while the call is still running.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/green.txt", "description": "Write release note and run new tests green"}
[tool_result] exit=0
tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps PASSED [100%]

============================== 2 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|exit=|FAILED|timed out|hung\" /tmp/full.txt | tail -15; echo ----; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_exit=$?\"; tail -25 /tmp/check.txt", "description": "Run full test suite and changed-file checker"}
[tool_result] exit=1
FAILED tests/test_tenacity.py::TestStatisticsKeys::test_delay_since_first_attempt_available_on_first_attempt
========= 1 failed, 166 passed, 1 skipped, 12 subtests passed in 1.91s =========
exit=1 (pytest); full log: /tmp/run_tests.log
----
check_exit=0
changed: releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite has one failure, and it is a real constraint. `test_delay_since_first_attempt_available_on_first_attempt` reads `fn.statistics` from inside the function body during the first attempt, so `fn.statistics` must be live during a call. I can't edit that test, so my snapshot-at-end approach is wrong. I'll look at where the statistics get written so the shared dict can be kept live.
[tool_use Bash] {"command": "grep -n \"statistics\\[\" tenacity/__init__.py tenacity/asyncio/__init__.py tenacity/tornadoweb.py; echo ----; grep -n \"def _begin_iter\\|def begin\\|def _run_stop\\|def next_action\\|def _post_stop_check_actions\\|def _post_retry_check_actions\\|def __init__\\|def copy\" tenacity/__init__.py tenacity/asyncio/__init__.py; echo; sed -n 384,392p tenacity/__init__.py", "description": "Locate statistics write sites and hooks"}
[tool_result] tenacity/asyncio/__init__.py:153:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:395:        self.statistics["start_time"] = time.monotonic()
tenacity/__init__.py:396:        self.statistics["attempt_number"] = 1
tenacity/__init__.py:397:        self.statistics["idle_for"] = 0
tenacity/__init__.py:398:        self.statistics["delay_since_first_attempt"] = 0
tenacity/__init__.py:415:        self.statistics["delay_since_first_attempt"] = 
…[1184 chars elided]…
75:    def __init__(
tenacity/asyncio/__init__.py:152:    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]

            return self.copy(*args, **kwargs).wraps(f)

        # Preserve attributes
        wrapped_f.retry = self  # type: ignore[attr-defined]
        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
        wrapped_f.statistics = statistics  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)
[assistant] Hooking every write site would mean touching shared methods and the async copies, so I'll mirror at the dict instead. The per-call dict keeps its isolation, and it publishes its full contents into the shared decoration-time dict on every write. Every write path (`begin`, `_run_stop`, `next_action`, async copies) goes through `__setitem__` or `clear`, so none of them need edits. First I'll check where the class should live and how the async module imports from the package.
[tool_use Bash] {"command": "grep -n \"^class \\|^from \\|^import \" tenacity/__init__.py | head -40; echo ----; grep -n \"^from \\|^import \\|^    [A-Za-z_]*,$\" tenacity/asyncio/__init__.py | head -30", "description": "Check class order and asyncio imports"}
[tool_result] 18:import dataclasses
19:import functools
20:import sys
21:import threading
22:import time
23:import typing as t
24:import warnings
25:from abc import ABC, abstractmethod
26:from concurrent import futures
28:from . import _utils
31:from .after import after_log, after_nothing
34:from .before import before_log, before_nothing
37:from .before_sleep import before_sleep_log, before_sleep_nothing
40:from .nap import sleep, sleep_using_event
43:from .retry import (
61:from .stop import (
72:from .wait 
…[508 chars elided]…
766:from tenacity.asyncio import AsyncRetrying  # noqa: E402
----
18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
24:    AttemptManager,
25:    BaseRetrying,
26:    DoAttempt,
27:    DoSleep,
28:    RetryCallState,
29:    RetryError,
30:    _RetryDecorated,
31:    _utils,
32:    after_nothing,
33:    before_nothing,
37:from .retry import (
38:    RetryBaseT,
39:    retry_all,
40:    retry_any,
41:    retry_if_exception,
42:    retry_if_result,
[assistant] Next I'll swap the snapshot code for the mirror in both wrappers. The class goes just above `BaseRetrying`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", "old_string": "        # One dict per decorated function, updated in place: functools.wraps copies\n        # the attribute at decoration time, so an outer wrapper keeps this object.\n        statistics: dict[str, t.Any] = {}\n\n  
…[1125 chars elided]…
ed:\n                return f(*args, **kw)\n            # Always create a copy to prevent overwriting the local contexts when\n            # calling the same wrapped functions multiple times in the same stack\n            copy = self.copy()\n            copy._local.statistics = _StatisticsMirror(statistics)\n            self._local.statistics = statistics\n            return copy(f, *args, **kw)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", "old_string": "class BaseRetrying(ABC):", "new_string": "class _StatisticsMirror(dict[str, t.Any]):\n    \"\"\"Per-call statistics that also refresh a shared dict on every write.\n\n    Each call keeps its own dict, so concurrent o
…[194 chars elided]…
n        super().__init__()\n        self._shared = shared\n\n    def __setitem__(self, key: str, value: t.Any) -> None:\n        super().__setitem__(key, value)\n        self._publish()\n\n    def clear(self) -> None:\n        super().clear()\n        self._publish()\n\n    def _publish(self) -> None:\n        self._shared.clear()\n        self._shared.update(self)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            self._local.statistics = copy.statistics\n            try:\n                return await copy(fn, *args, **kwargs)  # type: ignore[type-var]\n            finally:\n                statistics.clear()\n                statistics.update(copy.statistics)", "new_string": "            copy = self.copy()\n            copy._local.statistics = _StatisticsMirror(statistics)\n            self._local.statistics = statistics\n            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py", "old_string": "    _RetryDecorated,\n    _utils,", "new_string": "    _RetryDecorated,\n    _StatisticsMirror,\n    _utils,"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] The release note is now wrong: it says the dict refreshes when a call finishes, but it now refreshes on every write. I'll correct it and then run the tests.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml", "content": "---\nfixes:\n  - |\n    ``func.statistics`` is now visible through another decorator that uses\n    ``functools.wraps`` on a ``@retry``-decorated function, for both sync and\n    async functions. Previously the outer wrapper kept the empty dict it copied\n    at decoration time. The outer wrapper's ``statistics`` is now the same\n    object as the inner function's, and it is updated as each call runs.\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_fu
…[26 chars elided]…
.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|FAILED|hung|timed out\" /tmp/full.txt | tail -8; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_exit=$?\"; tail -4 /tmp/check.txt", "description": "Fix release note, run new tests, full suite, and checker"}
[tool_result] exit=0
============================== 2 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
============== 167 passed, 1 skipped, 12 subtests passed in 1.81s ==============
check_exit=0
changed: releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (167 passed, 1 skipped, exit 0) and the checker reports 0 problems. Before reporting, I'll spot-check the invariants the change touches: `fn.retry.statistics is fn.statistics`, per-call isolation for recursive and concurrent calls, and the `enabled=False` path.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/check_inv.py <<'EOF'\nimport asyncio, functools\nfrom tenacity import retry, stop_after_attempt\nfrom tenacity.asyncio import AsyncRetrying\n\n@retry(stop=stop_after_attempt(3))\ndef f(n):\n    if n > 0:\n        f(n 
…[380 chars elided]…
 *a, **k: g(*a, **k))\n    res = await asyncio.gather(g(0), g(1))\n    print(\"async results:\", res, \"identity:\", g.retry.statistics is g.statistics)\n\nasyncio.run(main())\n\n@retry(enabled=False)\ndef h():\n    return 1\nh()\nprint(\"disabled stats:\", h.statistics)\nEOF\n$PY -I /tmp/check_inv.py; rm -f /tmp/check_inv.py", "description": "Spot-check statistics invariants in a scratch script"}
[tool_result] Traceback (most recent call last):
  File "/tmp/check_inv.py", line 2, in <module>
    from tenacity import retry, stop_after_attempt
ModuleNotFoundError: No module named 'tenacity'
[assistant] The `-I` flag also drops `PYTHONPATH`, so the package wasn't importable. I'll rerun with the working tree on the path.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; mkdir -p /tmp/inv-check && cat > /tmp/inv-check/check_inv.py <<'EOF'\nimport asyncio\nfrom tenacity import retry, stop_after_attempt\n\n@retry(stop=stop_after_attempt(3))\ndef f(n):\n    if n > 0:\n        f(n - 1)  # recursion:
…[322 chars elided]…
ain():\n    res = await asyncio.gather(g(0), g(1))\n    print(\"async results:\", res, \"identity:\", g.retry.statistics is g.statistics)\n\nasyncio.run(main())\n\n@retry(enabled=False)\ndef h():\n    return 1\nh()\nprint(\"disabled stats:\", h.statistics)\nEOF\nPYTHONPATH=\"$PWD\" $PY /tmp/inv-check/check_inv.py; rm -rf /tmp/inv-check", "description": "Run invariant spot-check with repo on path"}
[tool_result] sync identity: True 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/asyncio/__init__.py", line 124, in __call__
    result = await fn(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/inv-check/check_inv.py", line 17, in g
    raise ValueError
ValueError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  Fil
…[1661 chars elided]…
onovan/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/_utils.py", line 107, in inner
    return call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/comp-1/tenacity/__init__.py", line 486, in exc_check
    raise retry_exc from fut.exception()
tenacity.RetryError: RetryError[<Future at 0x105617770 state=finished raised ValueError>]
[assistant] That traceback is from my scratch script, not the library: `g(0)` always raises, so it correctly exhausts its 2 attempts. I'll let `gather` collect the exception and check the rest.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; mkdir -p /tmp/inv-check && cat > /tmp/inv-check/check_inv.py <<'EOF'\nimport asyncio\nfrom tenacity import retry, stop_after_attempt\n\n@retry(stop=stop_after_attempt(2))\nasync def g(i):\n    await asyncio.sleep(0.01 * i)\n    
…[195 chars elided]…
nstance(r, Exception) else r for r in res])\n    print(\"async identity:\", g.retry.statistics is g.statistics, g.statistics[\"attempt_number\"])\n\nasyncio.run(main())\n\n@retry(enabled=False)\ndef h():\n    return 1\nh()\nprint(\"disabled stats:\", h.statistics)\nEOF\nPYTHONPATH=\"$PWD\" $PY /tmp/inv-check/check_inv.py; rm -rf /tmp/inv-check", "description": "Rerun async concurrency spot-check"}
[tool_result] async results: ['RetryError', 1]
async identity: True 2
disabled stats: {}
[assistant] The spot-checks pass. Last, I'll confirm the diff contains only the intended changes.
[tool_use Bash] {"command": "git status --short; git diff --stat", "description": "Show changed files and diff stat"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml
 tenacity/__init__.py         | 34 +++++++++++++++++++++++++++++++---
 tenacity/asyncio/__init__.py | 11 ++++++++---
 tests/test_asyncio.py        | 28 ++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 28 ++++++++++++++++++++++++++++
 4 files changed, 95 insertions(+), 6 deletions(-)
[assistant] `func.statistics` now stays visible through a `functools.wraps` wrapper, for both sync and async `@retry` functions. The outer wrapper's `statistics` is the same object as the inner one's, and it updates as the call runs.

**Cause:** `functools.wraps` copies the inner function's attributes once, at decoration time. Each call then rebound `wrapped_f.statistics` to a fresh dict, so the outer wrapper kept the original empty `{}`.

**Fix:**
- `tenacity/__init__.py` (`BaseRetrying.wraps`) and `tenacity/asyncio/__init__.py` (`AsyncRetrying.wraps`) create one dict per decorated function and never reb
…[953 chars elided]…
they aren't available here.
- No existing test was edited.

**Behaviour to know about:**
- `fn.statistics` is a plain dict that is now shared across calls on the same function. Concurrent calls overwrite each other's values, so the last writer wins. Before this change the last call to start won, so the practical difference is small. Per-thread reads still go through `fn.retry.statistics`.
- I added `reno` note `releasenotes/notes/functools-wraps-statistics-3f9c1a7e5b2d8046.yaml` (a `fixes:` entry).

I didn't update the docs in `doc/source/index.rst`, since this fix changes no documented usage.
