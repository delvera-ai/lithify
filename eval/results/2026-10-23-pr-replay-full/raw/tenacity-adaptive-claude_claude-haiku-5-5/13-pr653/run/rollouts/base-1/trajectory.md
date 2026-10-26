# trajectory base-1

final message:
`func.statistics` now stays live through outer wrappers built with `functools.wraps`, for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's. The project suite passes: 167 passed, 1 skipped.

**Cause:** `functools.wraps` copies the inner wrapper's attributes once, when the outer wrapper is created. At that moment `statistics` was `{}`, so the outer wrapper kept that empty dict. The inner wrapper replaces its own `statistics` on every call, so the copy never updated.

**Fix:**
- `tenacity/__init__.py`: added a small `_StatisticsView` class, a read-only `Mapping` that reads the retry object's current statistics for the calling thread. Both wrappers now get one view at creation, and `functools.wraps` passes that same object to the outer wrapper. The per-call reassignment is gone; the thread-local `_local.statistics` assignment is kept.
- `tenacity/asyncio/__init__.py`: the same change for the async wrapper.

**Behaviour change to be aware of:** `func.statistics` is now a live read-only view rather than a plain `dict`. Reads, `==` against a dict, `dict(...)`, `in`, and `repr` all behave as before. Code that mutates `func.statistics` directly, or checks `type(...) is dict`, will notice the difference.

**Tests added:**
- `tests/test_tenacity.py`: a sync test with a `functools.wraps` wrapper around a failing retry-decorated function.
- `tests/test_asyncio.py`: the async equivalent, in a new `TestAsyncStatisticsWrapper` class.

Both check `assertIs` between the inner and outer statistics and the attempt count. I did not run them against the unfixed code, but the pre-fix behaviour (outer stays `{}`) makes the identity assertion fail. A manual script confirmed the fixed sync and async outputs.

I did not run mypy because it isn't installed in the project's test environment, and `ruff` isn't on the PATH here, so the style check was not run either.

Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"statistics\" --include=*.py . | grep -v \"/\\.git/\" | head -60", "description": "Locate statistics references in the repo"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short && grep -rn \"statistics\" . --exclude-dir=.git | head -60", "description": "Search repo for statistics references"}
[tool_result] tests/test_asyncio.py:291:        self.assertEqual(2, retrying.statistics["attempt_number"])
tests/test_asyncio.py:501:        - statistics contains the value for the latest function run
tests/test_asyncio.py:503:        - retry object statistics are synced with function statistics
tests/test_asyncio.py:517:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:521:            _retryable_coroutine_with_2_attempts.retry.statistics,
tests/test_asyncio.py:542:           
…[4516 chars elided]…
}  # type: ignore[attr-defined]
tenacity/__init__.py:387:        self.statistics.clear()
tenacity/__init__.py:388:        self.statistics["start_time"] = time.monotonic()
tenacity/__init__.py:389:        self.statistics["attempt_number"] = 1
tenacity/__init__.py:390:        self.statistics["idle_for"] = 0
tenacity/__init__.py:391:        self.statistics["delay_since_first_attempt"] = 0
tenacity/__init__.py:408:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "sed -n 300,400p tenacity/__init__.py && echo ---- && grep -n \"statistics\\|wraps\\|def wraps\\|_wrapped\\|copy\" tenacity/asyncio/__init__.py | head -40 && echo ---- && cat tenacity/__init__.py | grep -n \"wraps\" ", "description": "Read retry wrapper statistics code"}
[tool_result]         )

    def __getstate__(self) -> dict[str, t.Any]:
        # Exclude threading.local which cannot be pickled
        return {k: v for k, v in self.__dict__.items() if k != "_local"}

    def __setstate__(self, state: dict[str, t.Any]) -> None:
        self.__dict__.update(state)
        self._local = threading.local()

    def __str__(self) -> str:
        return self._name if self._name is not None else "<unknown>"

    def __repr__(self) -> str:
        return (
            f"<{self.__
…[4410 chars elided]…
ype-var]
218:        async_wrapped.retry = self  # type: ignore[attr-defined]
219:        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
220:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
222:        return t.cast("_RetryDecorated[P, R]", async_wrapped)
----
357:    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
363:        @functools.wraps(
377:            return self.copy(*args, **kwargs).wraps(f)
754:        return r.wraps(f)
[tool_use Bash] {"command": "sed -n 195,225p tenacity/asyncio/__init__.py && echo ---- && sed -n 1,30p tenacity/__init__.py | grep -n import && echo ---- && sed -n 1855,1905p tests/test_tenacity.py && echo ---- && sed -n 1520,1540p tests/test_tenacity.py && git log --oneline -3 -- tenacity/__init__.py", "description": "Read async wrapper, imports, and existing tests"}
[tool_result]                 self._retry_state.prepare_for_next_attempt()
                await self.sleep(do)  # type: ignore[misc]
            else:
                raise StopAsyncIteration

    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        wrapped = super().wraps(fn)
        # Ensure wrapper is recognized as a coroutine function.

        @functools.wraps(
            fn, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        async def async_wrapped(
…[3131 chars elided]…
unc, "retry")
        assert hasattr(my_func, "retry_with")
        assert hasattr(my_func, "statistics")
        assert my_func() == "ok"

    def test_enabled_false_via_retry_with(self) -> None:
        """retry_with(enabled=False) disables retrying."""
        call_count = 0

868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
[tool_use Bash] {"command": "sed -n 26,40p tenacity/__init__.py && echo ---- && sed -n 1,30p tenacity/asyncio/__init__.py | grep -n \"import\" && grep -n \"^class \\|^def \" tenacity/__init__.py | head -20 && ls <work>/env-tenacity/bin/python", "description": "Check imports and class layout for the edit"}
[tool_result] from concurrent import futures

from . import _utils

# Import all built-in after strategies for easier usage.
from .after import after_log, after_nothing

# Import all built-in before strategies for easier usage.
from .before import before_log, before_nothing

# Import all built-in before sleep strategies for easier usage.
from .before_sleep import before_sleep_log, before_sleep_nothing

# Import all nap strategies for easier usage.
from .nap import sleep, sleep_using_event
----
18:import funct
…[392 chars elided]…
BC):
508:class Retrying(BaseRetrying):
536:class Future(futures.Future[t.Any]):
561:class RetryCallState:
649:class _RetryDecorated(t.Protocol[P, R]):
663:class _AsyncRetryDecorator(t.Protocol):
683:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
687:def retry(
705:def retry(
722:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
<work>/env-tenacity/bin/python
[assistant] Root cause: `functools.wraps` copies the inner wrapper's `__dict__` once, at decoration time, so the outer wrapper keeps the `{}` that existed then. The inner wrapper replaces its own `statistics` attribute on every call, so the outer copy never updates. The fix is a live, shared view object that both wrappers reference and that reads the retry object's current statistics.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "from abc import ABC, abstractmethod\nfrom concurrent import futures", "new_string": "from abc import ABC, abstractmethod\nfrom collections.abc import Mapping\nfrom concurrent import futures"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "offset": 234, "limit": 6}
[tool_result] 234	    ) -> bool | None:
235	        return self.__exit__(exc_type, exc_value, traceback)
236	
237	
238	class BaseRetrying(ABC):
239	    def __init__(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "        return self.__exit__(exc_type, exc_value, traceback)\n\n\nclass BaseRetrying(ABC):", "new_string": "        return self.__exit__(exc_type, exc_value, traceback)\n\n\nclass _StatisticsView(Mapping[str, t.Any])
…[356 chars elided]…
n        self._retry = retry\n\n    def __getitem__(self, key: str) -> t.Any:\n        return self._retry.statistics[key]\n\n    def __iter__(self) -> t.Iterator[str]:\n        return iter(self._retry.statistics)\n\n    def __len__(self) -> int:\n        return len(self._retry.statistics)\n\n    def __repr__(self) -> str:\n        return repr(self._retry.statistics)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            wrapped_f.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)", "new_string": "            copy = self.copy()\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "        wrapped_f.statistics = {}  # type: ignore[attr-defined]", "new_string": "        wrapped_f.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics", "new_string": "            copy = self.copy()\n            self._local.statistics = copy.statistics"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "        async_wrapped.statistics = {}  # type: ignore[attr-defined]", "new_string": "        async_wrapped.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now the asyncio module needs the import. Let me check its import block and then run the checks.
[tool_use Bash] {"command": "sed -n 18,35p tenacity/asyncio/__init__.py", "description": "Show asyncio module import block"}
[tool_result] import functools
import sys
import typing as t

import tenacity
from tenacity import (
    AttemptManager,
    BaseRetrying,
    DoAttempt,
    DoSleep,
    RetryCallState,
    RetryError,
    _RetryDecorated,
    _utils,
    after_nothing,
    before_nothing,
)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "    _RetryDecorated,\n    _utils,\n    after_nothing,", "new_string": "    _RetryDecorated,\n    _StatisticsView,\n    _utils,\n    after_nothing,"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/claude-501-check-stats.py <<'EOF'\nimport asyncio, functools, tenacity\nfrom tenacity import retry, stop_after_attempt\n\ndef timed(f):\n    @functools.wraps(f)\n    def w(*a, **k):\n        return f(*a, **k)\n    return w\n\ndef atimed(f):\n    @functools.wraps(f)\n    async def w(*a, **k):\n        return await f(*a, **k)\n    return w\n\n@retry(stop=stop_after_attempt(3)
…[627 chars elided]…
 aouter.statistics is async_f.statistics)\nEOF\n<work>/env-tenacity/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/claude-501-check-stats.py').read())\"; rm -f /tmp/claude-501-check-stats.py", "description": "Run a manual repro of wrapped statistics"}
[tool_result] before {}
sync outer 2 True True
async outer 2 True
[assistant] The repro now shows the outer wrapper reporting the real statistics for both sync and async. Next, the project's test command.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run project test suite"}
[tool_result] ..............s............................................... [ 37%]
...................................................................... [ 79%]
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] All 165 pass. I'll add regression tests for the sync and async cases so this doesn't come back.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_asyncio.py | grep -n \"import\\|^class\" ; sed -n 1900,1912p tests/test_tenacity.py; grep -n \"^class \\|^import functools\" tests/test_asyncio.py tests/test_tenacity.py | head; sed -n 495,500p tests/test_asyncio.py", "description": "Inspect test file structure for insertion points"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
            attempts.append(_foobar.retry.statistics["attempt_number"])
            if len(attempts) < 3:
                raise ValueError("retry")
            return 42

        _foobar()
        self.assertEqual(attempts, [1, 2, 3])


class TestRetryErrorCallba
…[518 chars elided]…
leep(unittest.TestCase):
tests/test_tenacity.py:87:class TestBase(unittest.TestCase):
tests/test_tenacity.py:113:class TestRetryingName(unittest.TestCase):
tests/test_tenacity.py:180:class TestStopConditions(unittest.TestCase):
tests/test_tenacity.py:284:class TestWaitConditions(unittest.TestCase):

class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "        _foobar()\n        self.assertEqual(attempts, [1, 2, 3])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):", "new_string": "        _foobar()\n        self.assertEqual(attempts, [1, 2, 3])\n\n    def te
…[458 chars elided]…
)\n        def _foobar() -> None:\n            raise ValueError(42)\n\n        outer = timed(_foobar)\n        self.assertEqual({}, outer.statistics)\n        with contextlib.suppress(Exception):\n            outer()\n        self.assertIs(_foobar.statistics, outer.statistics)\n        self.assertEqual(2, outer.statistics[\"attempt_number\"])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\" tests/test_tenacity.py | head -20 && sed -n 565,575p tests/test_asyncio.py", "description": "Check test imports and async test insertion point"}
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
class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
    @asynctest
    async def test_sync_function_with_async_sleep(self) -> None:
        """A sync function with an async sleep callable uses AsyncRetrying."""
        mock_sleep = mock.AsyncMock()

        thing = NoneReturnUntilAfterCount(2)

        @retry(
            sleep=mock_sleep,
            wait=wait_fixed(1),
[assistant] The test file imports `typing` (not `t`) and has no `functools`, so I'll adjust my test to match.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "        def timed(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:\n            @functools.wraps(f)\n            def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:\n                return f(*args, **kwargs)", "new_string": "        def timed(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:\n            @functools.wraps(f)\n            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:\n                return f(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "import datetime\nimport logging", "new_string": "import datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "class TestSyncFunctionWithAsyncSleep(unittest.TestCase):\n    @asynctest", "new_string": "class TestAsyncStatisticsWrapper(unittest.TestCase):\n    @asynctest\n    async def test_stats_visible_through_functools_wrap
…[482 chars elided]…
ne:\n            raise ValueError(42)\n\n        outer = timed(_foobar)\n        self.assertEqual({}, outer.statistics)\n        with contextlib.suppress(Exception):\n            await outer()\n        self.assertIs(_foobar.statistics, outer.statistics)\n        self.assertEqual(2, outer.statistics[\"attempt_number\"])\n\n\nclass TestSyncFunctionWithAsyncSleep(unittest.TestCase):\n    @asynctest"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^import contextlib\\|stop_after_attempt,\\|    retry,\\|import retry\\|stop_after_attempt\" tests/test_asyncio.py | head -5; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; (command -v ruff && ruff format --check tenacity tests; ruff check tenacity tests) 2>&1 | tail -15", "description": "Run tests and lint checks"}
[tool_result] 37:    retry,
40:    stop_after_attempt,
73:@retry(stop=stop_after_attempt(2))
99:    async def test_stop_after_attempt(self) -> None:
121:            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
=================================== FAILURES ===================================
_ TestAsyncStatisticsWrapper.test_stats_visible_through_functools_wraps_wrapper _

self = <tests.test_asyncio.TestAsyncStatisticsWrapper testMethod=test_stats_visible_through_functools_wraps_wrapper>

…[650 chars elided]…
outer.statistics)
>       with contextlib.suppress(Exception):
             ^^^^^^^^^^
E       NameError: name 'contextlib' is not defined. Did you forget to import 'contextlib'

tests/test_asyncio.py:583: NameError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestAsyncStatisticsWrapper::test_stats_visible_through_functools_wraps_wrapper
1 failed, 166 passed, 1 skipped, 12 subtests passed in 1.82s
(eval):1: command not found: ruff
[assistant] The async test needs `contextlib`, which that file doesn't import. I'll use a try/except instead and wrap the long signature.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "        def timed(f: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:\n            @wraps(f)\n            async def wrapper(*args: Any, **kwargs: Any) -> Any:\n                ret
…[643 chars elided]…
    return await f(*args, **kwargs)\n\n            return wrapper\n\n        @retry(stop=stop_after_attempt(2))\n        async def _foobar() -> None:\n            raise ValueError(42)\n\n        outer = timed(_foobar)\n        self.assertEqual({}, outer.statistics)\n        with self.assertRaises(RetryError):\n            await outer()\n        self.assertIs(_foobar.statistics, outer.statistics)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161746-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    RetryError,\" tests/test_asyncio.py | head -2; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Fix test and rerun project test suite"}
[tool_result] 36:    RetryError,
..............s............................................... [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] All 167 pass, including the two new tests. One last check: a type check, since the package is typed.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m mypy tenacity 2>&1 | tail -5; git status --short; git diff --stat", "description": "Run mypy and show changed files"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 tenacity/__init__.py         | 28 ++++++++++++++++++++++++++--
 tenacity/asyncio/__init__.py |  4 ++--
 tests/test_asyncio.py        | 26 ++++++++++++++++++++++++++
 tests/test_tenacity.py       | 22 ++++++++++++++++++++++
 4 files changed, 76 insertions(+), 4 deletions(-)
[assistant] `func.statistics` now stays live through outer wrappers built with `functools.wraps`, for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's. The project suite passes: 167 passed, 1 skipped.

**Cause:** `functools.wraps` copies the inner wrapper's attributes once, when the outer wrapper is created. At that moment `statistics` was `{}`, so the outer wrapper kept that empty dict. The inner wrapper replaces its own `statistics` on every call, so the copy never updated.

**Fix:**
- `tenacity/__init__.py`: added a small `_StatisticsView` class, a r
…[743 chars elided]…
wraps` wrapper around a failing retry-decorated function.
- `tests/test_asyncio.py`: the async equivalent, in a new `TestAsyncStatisticsWrapper` class.

Both check `assertIs` between the inner and outer statistics and the attempt count. I did not run them against the unfixed code, but the pre-fix behaviour (outer stays `{}`) makes the identity assertion fail. A manual script confirmed the fixed sync and async outputs.

I did not run mypy because it isn't installed in the project's test environment, and `ruff` isn't on the PATH here, so the style check was not run either.

Nothing is committed.
