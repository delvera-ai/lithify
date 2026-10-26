# trajectory inv-1

final message:
`func.statistics` now stays live through a `functools.wraps` wrapper, for both sync and async functions. The full suite passes (167 passed, 1 skipped) and the stdlib style check passes.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` into the outer one when the outer decorator is applied. At that moment the inner `statistics` is the initial `{}`. Each call later rebinds the inner's `statistics` to a new per-call dict, but the outer keeps the copied reference to the `{}`.

**Fix:** each wrapper's `statistics` is now a single `_StatisticsView` object that reads the calling thread's current run, so the outer wrapper sees the same object and live values. The change is in `tenacity/__init__.py` (new view class, sync `wraps`) and `tenacity/asyncio/__init__.py` (async `wraps` now reuses the sync wrapper's view).

**Tests:** I added one regression test each in `tests/test_tenacity.py` (`TestStatistics`) and `tests/test_asyncio.py` (new `TestStatisticsThroughWrapper`). Both failed on the unfixed code with the outer `statistics` still `{}`, and both pass now.

**Behaviour change to know about:** `func.statistics` is no longer a plain `dict`. It compares equal to a dict and supports the mapping operations, but `isinstance(func.statistics, dict)` is now `False`. Reading it from a thread that has never called the function returns `{}`, where it previously returned the most recent call's dict from any thread. Both follow from the per-thread design. I noted both in the reno note.

**Harness steps:**
- Regression tests run alone against the unfixed code, then green after the fix.
- Full suite: `exit=0`, 167 passed, 1 skipped.
- `check_changed.py`: flagged one line over 88 columns in my test; I wrapped it and it now reports PASS.
- Added the reno note `releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml`.
- Not run: ruff and mypy, which the environment can't run.
- Skipped: I did not add a `doc/source/index.rst` change. The existing statistics docs still describe the function attribute accurately.

I did not commit anything.

## events
[assistant] I'll start by reading how `statistics` is attached to the decorated wrapper in tenacity.
[tool_use Bash] {"command": "git status --short && ls && grep -n \"statistics\\|wraps\\|def wraps\" tenacity/__init__.py | head -80", "description": "Check status and locate statistics handling"}
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
326:    def statistics(self) -> dict[str, t.Any]:
327:        """Return a dictionary of runtime statistics.
336:                     change between major releases as new statistics are
343:                  their own view of statistics they have collected (in the
345:                  statistics from each thread).
347:        if not hasattr(self._local, "statistics"):
348:            self._local.stati
…[501 chars elided]…
statistics.clear()
388:        self.statistics["start_time"] = time.monotonic()
389:        self.statistics["attempt_number"] = 1
390:        self.statistics["idle_for"] = 0
391:        self.statistics["delay_since_first_attempt"] = 0
408:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
467:            self.statistics["idle_for"] += sleep
468:            self.statistics["attempt_number"] += 1
656:    statistics: dict[str, t.Any]
754:        return r.wraps(f)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py", "offset": 350, "limit": 50}
[tool_result] 350	
351	    @property
352	    def iter_state(self) -> IterState:
353	        if not hasattr(self._local, "iter_state"):
354	            self._local.iter_state = IterState()
355	        return self._local.iter_state  # type: ignore[no-any-return]
356	
357	    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
358	        """Wrap a function for retrying.
359	
360	        :param f: A function to wrap for retrying.
361	        """
362	
363	        @functools.wraps(
364	            f, 
…[1212 chars elided]…
c()
389	        self.statistics["attempt_number"] = 1
390	        self.statistics["idle_for"] = 0
391	        self.statistics["delay_since_first_attempt"] = 0
392	
393	    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
394	        self.iter_state.actions.append(fn)
395	
396	    def _run_retry(self, retry_state: "RetryCallState") -> None:
397	        self.iter_state.retry_run_result = self.retry(retry_state)
398	
399	    def _run_wait(self, retry_state: "RetryCallState") -> None:
[tool_use Bash] {"command": "grep -n \"AsyncRetrying\\|def wraps\\|statistics\" tenacity/asyncio/__init__.py | head -40; cat .lithify/harness/skills/tenacity-change-contract/SKILL.md 2>/dev/null | head -80", "description": "Inspect async wraps and the change-contract skill"}
[tool_result] 74:class AsyncRetrying(BaseRetrying):
153:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
166:        raise TypeError("AsyncRetrying object is not iterable")
168:    def __aiter__(self) -> "AsyncRetrying":
200:    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
213:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
214:            self._local.statistics = copy.statistics
220:        async_wrapped.statistics 
…[6130 chars elided]…
 (`test_retry_try_again*`), and the `reraise` tests in `TestReraiseExceptions`. Async
  `reraise` is in `tests/test_asyncio.py::TestContextManager::test_reraise`.

## 1b. Strategy composition (`|`, `&`) and sync/async mixing
- Sync combinators (`tenacity/retry.py` `retry_any`/`retry_all`) call members directly. Async
  ones (`tenacity/asyncio/retry.py`) await each member through `_utils.wrap_to_async_func`,
  so they accept sync and async members alike. A sync combinator must never hold an async
[assistant] The cause is clear: `functools.wraps` copies the inner wrapper's `__dict__` into the outer one at decoration time, so the outer keeps the initial `{}` while the inner later rebinds `statistics` to a new dict. Next I'll check `copy()`, the docs, and how tests read `.statistics`.
[tool_use Bash] {"command": "sed -n 320,349p tenacity/__init__.py; grep -n \"def copy\" -A30 tenacity/__init__.py | head -45; sed -n 196,222p tenacity/asyncio/__init__.py; grep -rn \"\\.statistics\" tests/ | grep -v \"retry_object\\|self.statistics\" | head -30; ls tests releasenotes/notes | tail -5; cat .lithify/harness/scripts/run_tests.py | head -5; ls <work>/env-tenacity/bin/python", "description": "Inspect copy(), docs, and existing statistics tests"}
[tool_result]             f"before={self.before}, "
            f"after={self.after}, "
            f"name={self._name!r})>"
        )

    @property
    def statistics(self) -> dict[str, t.Any]:
        """Return a dictionary of runtime statistics.

        This dictionary will be empty when the controller has never been
        ran. When it is running or has ran previously it should have (but
        may not) have useful and/or informational keys and values when
        running is underway and/or completed.
…[6841 chars elided]…
,
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
#!/usr/bin/env python3
"""Run pytest in the foreground with a hard time limit; name the test that hangs.

A retry loop with no `stop=` (tenacity's default is never stop, no wait) spins
forever when the predicate under test is wrong, so a single bad test can hang
<work>/env-tenacity/bin/python
[assistant] Tests compare `.statistics` against plain dicts (`assertEqual({}, ...)`, `assertEqual(expected_stats, fn.statistics)`), so whatever I return has to compare equal to a dict. I'll read the rest of the change-contract skill for the required files, then look at the existing statistics tests.
[tool_use Bash] {"command": "sed -n 80,200p .lithify/harness/skills/tenacity-change-contract/SKILL.md; sed -n 1855,1900p tests/test_tenacity.py; ls releasenotes/notes | tail -3; grep -n \"statistics\" doc/source/index.rst | head", "description": "Read rest of contract skill and existing tests"}
[tool_result]   so they accept sync and async members alike. A sync combinator must never hold an async
  member: the call returns a coroutine, which is truthy. Retry then never stops, and the
  suite hangs instead of failing.
- `retry_base.__or__`/`__and__` call `other.__ror__(self)`/`other.__rand__(self)` on purpose.
  For `sync_strategy | async_strategy` the right operand is not a subclass of the left one, so
  Python calls the left `__or__`. Delegating is the only way `async_retry_base.__ror__` builds
  t
…[10826 chars elided]…

wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
367:You can access the statistics about the retry made over a function by using the
368:`statistics` attribute attached to the function:
381:    print(raise_my_exception.statistics)
576:    print(raise_my_exception.statistics)
598:statistics should be read from the function `statistics` attribute.
614:    print(raise_my_exception.statistics)
[assistant] The fix I'm considering is to make `statistics` on each wrapper a stable view that reads the current run's dict, so the outer wrapper's copied reference stays live. Before I write that, I need the regression tests, which must fail on the current code. I'll check the test imports first.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_tenacity.py | grep -n \"import\"; sed -n 1,25p tests/test_asyncio.py | grep -n \"import\"; grep -n \"^class \\|def test_stat\\|statistics\" tests/test_asyncio.py | head -30; sed -n 505,530p tests/test_asyncio.py", "description": "Check test imports and async statistics tests"}
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
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
79:cla
…[1030 chars elided]…
e_for": mock.ANY,
            "start_time": mock.ANY,
        }
        self.assertEqual(
            _retryable_coroutine_with_2_attempts.statistics,
            expected_stats,
        )
        self.assertEqual(
            _retryable_coroutine_with_2_attempts.retry.statistics,
            expected_stats,
        )

        with mock.patch.object(
            _retryable_coroutine_with_2_attempts.retry,
            "stop",
            tenacity.stop_after_attempt(1),
        ):
            try:
[assistant] I'll add a sync regression test to `TestStatistics` and an async one to `TestDecoratorWrapper`. Both wrap a `@retry` function in a `functools.wraps` decorator and check that the outer `statistics` is the inner one's object and holds the real values.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py", "old_string": "    def test_retry_object_statistics_during_execution(self) -> None:", "new_string": "    def test_stats_visible_through_wrapping_decorator(self) -> None:\n        \"\"\"A decorator using functools.wraps must expose
…[378 chars elided]…
:\n            raise ValueError(42)\n\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n        with contextlib.suppress(RetryError):\n            _foobar()\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n    def test_retry_object_statistics_during_execution(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_asyncio.py", "old_string": "class TestSyncFunctionWithAsyncSleep(unittest.TestCase):", "new_string": "class TestStatisticsThroughWrapper(unittest.IsolatedAsyncioTestCase):\n    async def test_stats_visible_through_wrapping_decorator(self) -> No
…[444 chars elided]…
          raise ValueError(42)\n\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n        with contextlib.suppress(tenacity.RetryError):\n            await _foobar()\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\nclass TestSyncFunctionWithAsyncSleep(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_asyncio.py has been updated successfully.
[assistant] The new tests use names the files may not import (`functools`, `t`, `contextlib`, `RetryError`). I'll check what each file already imports and align the tests with it.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|^    import\\|as t$\" tests/test_tenacity.py tests/test_asyncio.py | head -30; grep -c \"typing\\.Callable\\|t\\.Any\" tests/test_tenacity.py", "description": "Check imports in both test files"}
[tool_result] tests/test_asyncio.py:15:import asyncio
tests/test_asyncio.py:16:import inspect
tests/test_asyncio.py:17:import unittest
tests/test_asyncio.py:18:from collections.abc import Callable, Coroutine
tests/test_asyncio.py:19:from functools import wraps
tests/test_asyncio.py:20:from typing import Any, TypeVar
tests/test_asyncio.py:21:from unittest import mock
tests/test_asyncio.py:24:    import trio
tests/test_asyncio.py:30:import pytest
tests/test_asyncio.py:32:import tenacity
tests/test_asyncio.py:33
…[445 chars elided]…
e
tests/test_tenacity.py:22:import typing
tests/test_tenacity.py:23:import unittest
tests/test_tenacity.py:24:from fractions import Fraction
tests/test_tenacity.py:25:from unittest import mock
tests/test_tenacity.py:27:import pytest
tests/test_tenacity.py:28:from typeguard import check_type
tests/test_tenacity.py:30:import tenacity
tests/test_tenacity.py:31:from tenacity import RetryCallState, RetryError, Retrying, retry
tests/test_tenacity.py:32:from tenacity.retry import retry_all, retry_any
6
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py", "old_string": "        def timing(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:\n            @functools.wraps(f)\n            def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:\n                return f(*args, **kwargs)\
…[452 chars elided]…
wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:\n                return f(*args, **kwargs)\n\n            return wrapper\n\n        @timing\n        @retry(stop=tenacity.stop_after_attempt(2))\n        def _foobar() -> None:\n            raise ValueError(42)\n\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n        with contextlib.suppress(RetryError):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py", "old_string": "import contextlib\nimport datetime\nimport logging", "new_string": "import contextlib\nimport datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_asyncio.py", "old_string": "import asyncio\nimport inspect\nimport unittest", "new_string": "import asyncio\nimport contextlib\nimport inspect\nimport unittest"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_asyncio.py has been updated successfully.
[assistant] Both test files now have their imports. Next I'll run each regression test alone against the unfixed code, per the harness procedure, and confirm each fails for the reported reason.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestStatistics::test_stats_visible_through_wrapping_decorator > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -25 /tmp/red1.txt; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestStatisticsThroughWrapper::test_stats_visible_through_wrapping_decorator > /tmp/red2.txt 2>&1; echo \"exit=$?\"; tail -25 /tmp/red2.txt", "description": "Run both new regression tests against unfixed code"}
[tool_result] exit=1
    
        def timing(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:
            @functools.wraps(f)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                return f(*args, **kwargs)
    
            return wrapper
    
        @timing
        @retry(stop=tenacity.stop_after_attempt(2))
        def _foobar() -> None:
            raise ValueError(42)
    
        self.assertIs(_foobar.__wrapped__.statistics, _foobar.stati
…[1297 chars elided]…
Error: {'start_time': 245704.797954875, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt': 0.0002386250125709921} is not {}

tests/test_asyncio.py:585: AssertionError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestStatisticsThroughWrapper::test_stats_visible_through_wrapping_decorator
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail for the reported reason: the outer `statistics` is still the initial `{}` after the call. Next I'll make the fix. I need the module's imports and the start of `BaseRetrying` to place a small view class.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|^class \\|^if t\\|^    from\" tenacity/__init__.py | head -40; grep -n \"^from\\|^import\\|BaseRetrying\" tenacity/asyncio/__init__.py | head -20; grep -n \"requires-python\" pyproject.toml", "description": "Inspect module imports and class layout"}
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
…[528 chars elided]…
6:class Future(futures.Future[t.Any]):
561:class RetryCallState:
649:class _RetryDecorated(t.Protocol[P, R]):
663:class _AsyncRetryDecorator(t.Protocol):
759:from tenacity.asyncio import AsyncRetrying  # noqa: E402
761:if tornado:
762:    from tenacity.tornadoweb import TornadoRetrying
18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
25:    BaseRetrying,
37:from .retry import (
74:class AsyncRetrying(BaseRetrying):
17:requires-python = ">=3.10"
[assistant] I'll add the view class ahead of `BaseRetrying` and have both `wraps` implementations use one stable view per wrapper. The per-call `wrapped_f.statistics = copy.statistics` assignments go, but `self._local.statistics = copy.statistics` stays, because that is what the view reads.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py", "old_string": "import dataclasses\nimport functools\nimport sys", "new_string": "import collections.abc\nimport dataclasses\nimport functools\nimport sys"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py", "old_string": "class BaseRetrying(ABC):", "new_string": "class _StatisticsView(collections.abc.MutableMapping[str, t.Any]):\n    \"\"\"Live view of the statistics of the calling thread's most recent run.\n\n    ``functools.wraps`` c
…[496 chars elided]…
f._retry.statistics[key] = value\n\n    def __delitem__(self, key: str) -> None:\n        del self._retry.statistics[key]\n\n    def __iter__(self) -> t.Iterator[str]:\n        return iter(self._retry.statistics)\n\n    def __len__(self) -> int:\n        return len(self._retry.statistics)\n\n    def __repr__(self) -> str:\n        return repr(self._retry.statistics)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            wrapped_f.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)\n\n      
…[506 chars elided]…
kw)\n\n        def retry_with(*args: t.Any, **kwargs: t.Any) -> \"_RetryDecorated[P, R]\":\n            return self.copy(*args, **kwargs).wraps(f)\n\n        # Preserve attributes\n        wrapped_f.retry = self  # type: ignore[attr-defined]\n        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]\n        wrapped_f.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return await copy(fn, *ar
…[343 chars elided]…
           self._local.statistics = copy.statistics\n            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]\n\n        # Preserve attributes\n        async_wrapped.retry = self  # type: ignore[attr-defined]\n        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]\n        async_wrapped.statistics = wrapped.statistics  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now I'll re-run the two regression tests, expecting them to pass.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestStatistics::test_stats_visible_through_wrapping_decorator > /tmp/green1.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green1.txt; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestStatisticsThroughWrapper::test_stats_visible_through_wrapping_decorator > /tmp/green2.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green2.txt", "description": "Run both regression tests after the fix"}
[tool_result] exit=0

============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0

============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Both pass. Next is the full suite, which the harness requires, read through the `exit=` line and the summary.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|FAILED|ERROR\" /tmp/full.txt | tail -20", "description": "Run full test suite via harness script"}
[tool_result] exit=0
============== 167 passed, 1 skipped, 12 subtests passed in 1.79s ==============
[assistant] The full suite passes: 167 passed, 1 skipped. Next is the stdlib style check.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt | tail -30", "description": "Run stdlib style checker on changed files"}
[tool_result] exit=1
changed: tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:1894: line is 92 columns (max 88)
FAIL: 1 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The checker flags one line over 88 columns: the `timing` signature in my sync test. I'll wrap it the way ruff format would.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py", "old_string": "        def timing(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:", "new_string": "        def timing(\n            f: typing.Callable[..., typing.Any],\n        ) -> typing.Callable[..., typing.Any]:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] After that wrap I'll re-run the style checker and the full suite. Then I'll write the reno note, which the change-contract skill requires for user-visible behaviour.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check exit=$?\"; tail -4 /tmp/check.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"full exit=$?\"; grep -E \"passed|failed\" /tmp/full.txt | tail -3; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; ls releasenotes/notes | grep -i \"stat\\|fix\" | head", "description": "Re-run style check, suite, and read an existing reno note"}
[tool_result] check exit=0
changed: tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
full exit=0
============== 167 passed, 1 skipped, 12 subtests passed in 1.83s ==============
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
fix-async-loop-with-result-f68e913ccb425aca.yaml
fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
fix-local-context-overwrite-94190ba06a481631.yaml
fix-reraise-tryagain-underlying-exc-e21a26ee95bad0b3.yaml
fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml
fix-setuptools-config-3af71aa3592b6948.yaml
fix-wait-chain-empty-strategies-d3a8f7c2b1e4f569.yaml
fix-wait-typing-b26eecdb6cc0a1de.yaml
fix_async-52b6594c8e75c4bc.yaml
[assistant] Style check passes and the suite is still green. I'll match the style of an existing fix note for the reno entry.
[tool_use Bash] {"command": "cat releasenotes/notes/fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml", "description": "Read an existing fix release note"}
[tool_result] ---
fixes:
  - |
    Restore the value of the `retry` attribute for wrapped functions. Also,
    clarify that those attributes are write-only and statistics should be
    read from the function attribute directly.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml", "content": "---\nfixes:\n  - |\n    ``func.statistics`` is now kept up to date when a ``@retry``-decorated\n    function is wrapped by another decorator that uses ``functools.wraps``.\n    Previously the
…[67 chars elided]…
 outer and inner wrappers now share the same ``statistics`` object,\n    for both sync and async functions. Note that ``func.statistics`` is now a\n    live read-only-by-convention view of the calling thread's statistics\n    rather than a plain ``dict``: it compares equal to a dict and supports\n    the usual mapping operations, but ``isinstance(func.statistics, dict)``\n    is now ``False``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml (file state is current in your context — no need to Read it back)
[assistant] The note's "read-only-by-convention" wording is inaccurate, since the view supports writes. I'll correct it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml", "old_string": "    live read-only-by-convention view of the calling thread's statistics\n    rather than a plain ``dict``: it compares equal to a dict and supports\n    the usual mapping operations, but ``isinstance(func.statistics, dict)``\n    is now ``False``.", "new_string": "    live view of the calling thread's statistics rather than a plain\n    ``dict``: it compares equal to a dict and supports the usual mapping\n    operations, but ``isinstance(func.statistics, dict)`` is now ``False``."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/inv-1/releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] The reno note is in place. Last, I'll confirm the working tree holds only the intended files.
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Confirm changed files in the working tree"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml
 tenacity/__init__.py         | 34 ++++++++++++++++++++++++++++++++--
 tenacity/asyncio/__init__.py |  3 +--
 tests/test_asyncio.py        | 24 ++++++++++++++++++++++++
 tests/test_tenacity.py       | 24 ++++++++++++++++++++++++
 4 files changed, 81 insertions(+), 4 deletions(-)
[assistant] `func.statistics` now stays live through a `functools.wraps` wrapper, for both sync and async functions. The full suite passes (167 passed, 1 skipped) and the stdlib style check passes.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` into the outer one when the outer decorator is applied. At that moment the inner `statistics` is the initial `{}`. Each call later rebinds the inner's `statistics` to a new per-call dict, but the outer keeps the copied reference to the `{}`.

**Fix:** each wrapper's `statistics` is now a single `_StatisticsView` object that reads the calling th
…[883 chars elided]…
ted both in the reno note.

**Harness steps:**
- Regression tests run alone against the unfixed code, then green after the fix.
- Full suite: `exit=0`, 167 passed, 1 skipped.
- `check_changed.py`: flagged one line over 88 columns in my test; I wrapped it and it now reports PASS.
- Added the reno note `releasenotes/notes/fix-statistics-through-wrapper-3b9f1d6a2c7e4480.yaml`.
- Not run: ruff and mypy, which the environment can't run.
- Skipped: I did not add a `doc/source/index.rst` change. The existing statistics docs still describe the function attribute accurately.

I did not commit anything.
