# trajectory base-1

final message:
`func.statistics` now stays visible through a `functools.wraps` wrapper, for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's. The full suite passes (167 passed, 1 skipped), and the two new regression tests fail on the original code.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` onto the outer one when the decorator is applied. At that moment `statistics` was still the initial `{}`. The retry wrapper later rebinds its own `statistics` on each call, but the outer wrapper keeps the stale copy.

**Fix:**
- `tenacity/__init__.py`: added a small `_StatisticsView` class, a read-only `Mapping` that reads the retry object's current per-thread statistics. `wraps()` assigns one stable view instead of a plain dict, and the per-call rebinding of `statistics` is removed.
- `tenacity/asyncio/__init__.py`: the async wrapper gets the same treatment.
- Tests: added `test_stats_through_functools_wraps_decorator` to `TestStatistics` in `tests/test_tenacity.py` and to `TestDecoratorWrapper` in `tests/test_asyncio.py`. Both wrap the retried function in a timing decorator and check the statistics and the identity with `__wrapped__`. No existing tests were changed.

**Behaviour change to be aware of:** `func.statistics` is now a live read-only view rather than a plain `dict`. Equality, item access, `len`, and iteration behave as before, but `isinstance(func.statistics, dict)` is now `False`, and code that mutates it will fail. I found no code in the repo that does either.

I could not run ruff or mypy because neither is installed in the project's test environment.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"statistics\" --include=*.py . | grep -v \"^./.git/\" | head -50", "description": "Check status and find statistics references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"statistics\" . --exclude-dir=.git | head -50", "description": "Check status and find statistics references"}
[tool_result] tests/test_asyncio.py:291:        self.assertEqual(2, retrying.statistics["attempt_number"])
tests/test_asyncio.py:501:        - statistics contains the value for the latest function run
tests/test_asyncio.py:503:        - retry object statistics are synced with function statistics
tests/test_asyncio.py:517:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:521:            _retryable_coroutine_with_2_attempts.retry.statistics,
tests/test_asyncio.py:542:           
…[3680 chars elided]…
py:327:        """Return a dictionary of runtime statistics.
tenacity/__init__.py:336:                     change between major releases as new statistics are
tenacity/__init__.py:343:                  their own view of statistics they have collected (in the
tenacity/__init__.py:345:                  statistics from each thread).
tenacity/__init__.py:347:        if not hasattr(self._local, "statistics"):
tenacity/__init__.py:348:            self._local.statistics = t.cast("dict[str, t.Any]", {})
[tool_use Bash] {"command": "sed -n 300,420p tenacity/__init__.py; echo ----; cat tenacity/__init__.py | grep -n \"wraps\\|def wrapped_f\\|wrapped_f\\.\\|def __call__\\|retry_with\\|def copy\\|_local\\|def __getattr__\" ; echo ----; ls tenacity; grep -n \"wraps\\|statistics\\|retry_with\\|wrapped_f\" tenacity/asyncio/__init__.py tenacity/_utils.py 2>/dev/null | head -40", "description": "Read statistics property and wrapper code"}
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
…[6371 chars elided]…
= super().wraps(fn)
tenacity/asyncio/__init__.py:204:        @functools.wraps(
tenacity/asyncio/__init__.py:213:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:214:            self._local.statistics = copy.statistics
tenacity/asyncio/__init__.py:219:        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:220:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
[tool_use Bash] {"command": "sed -n 1,40p tenacity/__init__.py | grep -n \"import\"; echo ----; sed -n 1,30p tenacity/asyncio/__init__.py | grep -n import; sed -n 195,230p tenacity/asyncio/__init__.py; echo ----; sed -n 1855,1905p tests/test_tenacity.py; git log --oneline -3 -- tenacity/__init__.py", "description": "Read imports, async wrapper, and related tests"}
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
----
18:import functools
19:import sys
20:import typing as t

…[2840 chars elided]…
eption_type(ValueError),
            reraise=True,
        )
        def _foobar() -> int:
            attempts.append(_foobar.retry.statistics["attempt_number"])
            if len(attempts) < 3:
                raise ValueError("retry")
            return 42

        _foobar()
868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
[tool_use Bash] {"command": "grep -n \"^class \\|^def \\|^[A-Z_]* = \" tenacity/__init__.py | head -40; sed -n 28,70p tenacity/__init__.py | grep -n \"import\\|from\" ", "description": "List top-level definitions in tenacity package"}
[tool_result] 107:P = t.ParamSpec("P")
108:R = t.TypeVar("R")
112:class IterState:
127:class TryAgain(Exception):
131:NO_RESULT = object()
134:class DoAttempt:
138:class DoSleep(float):
142:class BaseAction:
164:class RetryAction(BaseAction):
175:def _first_set(first: t.Any | object, second: t.Any) -> t.Any:
179:class RetryError(Exception):
203:class AttemptManager:
237:class BaseRetrying(ABC):
508:class Retrying(BaseRetrying):
536:class Future(futures.Future[t.Any]):
561:class RetryCallState:
649:class _Retr
…[2 chars elided]…
ecorated(t.Protocol[P, R]):
663:class _AsyncRetryDecorator(t.Protocol):
683:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
687:def retry(
705:def retry(
722:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
1:from . import _utils
4:from .after import after_log, after_nothing
7:from .before import before_log, before_nothing
10:from .before_sleep import before_sleep_log, before_sleep_nothing
13:from .nap import sleep, sleep_using_event
16:from .retry import (
34:from .stop import (
[assistant] I've found the cause: `functools.wraps` copies the inner wrapper's `__dict__` onto the outer one at decoration time, so the outer keeps the original `{}`. The inner wrapper then rebinds its own `statistics` on each call, which the outer never sees. I'll make `statistics` a stable view that reads the live per-thread statistics of the retry object, so every wrapper layer shares the same object.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "class BaseRetrying(ABC):", "new_string": "class _StatisticsView(collections.abc.Mapping[str, t.Any]):\n    \"\"\"Live, read-only view of a retry object's statistics.\n\n    Decorators built on ``functools.wraps`` cop
…[343 chars elided]…
n        self._retry = retry\n\n    def __getitem__(self, key: str) -> t.Any:\n        return self._retry.statistics[key]\n\n    def __iter__(self) -> t.Iterator[str]:\n        return iter(self._retry.statistics)\n\n    def __len__(self) -> int:\n        return len(self._retry.statistics)\n\n    def __repr__(self) -> str:\n        return repr(self._retry.statistics)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            wrapped_f.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)\n\n     
…[507 chars elided]…
kw)\n\n        def retry_with(*args: t.Any, **kwargs: t.Any) -> \"_RetryDecorated[P, R]\":\n            return self.copy(*args, **kwargs).wraps(f)\n\n        # Preserve attributes\n        wrapped_f.retry = self  # type: ignore[attr-defined]\n        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]\n        wrapped_f.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the imports, and the async wrapper.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "import dataclasses\nimport functools\nimport sys", "new_string": "import collections.abc\nimport dataclasses\nimport functools\nimport sys"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,30p tenacity/asyncio/__init__.py | grep -n \"from\\|import\" ; sed -n 23,40p tenacity/asyncio/__init__.py", "description": "Read asyncio module imports"}
[tool_result] 18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
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

# Import all built-in retry strategies for easier usage.
from .retry import (
    RetryBaseT,
    retry_all,
    retry_any,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "    RetryError,\n    _RetryDecorated,\n    _utils,", "new_string": "    RetryError,\n    _RetryDecorated,\n    _StatisticsView,\n    _utils,"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics", "new_string": "            copy = self.copy()\n            self._local.statistics = copy.statistics"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "        async_wrapped.statistics = {}  # type: ignore[attr-defined]", "new_string": "        async_wrapped.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now a regression test for sync and async, wrapped by a `functools.wraps` timing decorator. I'm adding new tests only and leaving existing ones alone.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|class .*Test.*async\\|IsolatedAsyncio\\|asyncio.run\" tests/test_tenacity.py tests/test_asyncio.py | head -30; grep -n \"def test_stats_failing\" -A 12 tests/test_tenacity.py | tail -2", "description": "Inspect test file imports and structure"}
[tool_result] tests/test_tenacity.py:16:import contextlib
tests/test_tenacity.py:17:import datetime
tests/test_tenacity.py:18:import logging
tests/test_tenacity.py:19:import pickle
tests/test_tenacity.py:20:import re
tests/test_tenacity.py:21:import time
tests/test_tenacity.py:22:import typing
tests/test_tenacity.py:23:import unittest
tests/test_tenacity.py:24:from fractions import Fraction
tests/test_tenacity.py:25:from unittest import mock
tests/test_tenacity.py:27:import pytest
tests/test_tenacity.py:28:fr
…[564 chars elided]…
21:from unittest import mock
tests/test_asyncio.py:30:import pytest
tests/test_asyncio.py:32:import tenacity
tests/test_asyncio.py:33:from tenacity import (
tests/test_asyncio.py:42:from tenacity import asyncio as tasyncio
tests/test_asyncio.py:43:from tenacity.wait import wait_fixed
tests/test_asyncio.py:45:from .test_tenacity import (
tests/test_asyncio.py:57:        return asyncio.run(callable_(*a, **kw))
1878-        """Test that func.retry.statistics is synced with func.statistics."""
1879-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_object_statistics_synced(self) -> None:\n        \"\"\"Test that func.retry.statistics is synced with func.statistics.\"\"\"\n", "new_string": "    def test_stats_through_functools_wraps_decorato
…[531 chars elided]…
.assertEqual({}, _foobar.statistics)\n        with contextlib.suppress(Exception):\n            _foobar()\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n\n    def test_retry_object_statistics_synced(self) -> None:\n        \"\"\"Test that func.retry.statistics is synced with func.statistics.\"\"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "import contextlib\nimport datetime\nimport logging", "new_string": "import contextlib\nimport datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async counterpart in `test_asyncio.py`, next to the existing statistics tests.
[tool_use Bash] {"command": "sed -n 495,560p tests/test_asyncio.py", "description": "Read existing async statistics tests"}
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
…[1291 chars elided]…
xc.last_attempt.attempt_number, 1)
                self.assertEqual(
                    _retryable_coroutine_with_2_attempts.retry.statistics,
                    expected_stats,
                )
            else:
                self.fail("RetryError should have been raised after 1 attempt")


# make sure mypy accepts passing an async sleep function
# https://github.com/jd/tenacity/issues/399
async def my_async_sleep(x: float) -> None:
    await asyncio.sleep(x)


@retry(sleep=my_async_sleep)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "            else:\n                self.fail(\"RetryError should have been raised after 1 attempt\")\n\n\n# make sure mypy accepts passing an async sleep function", "new_string": "            else:\n                
…[550 chars elided]…
    async def _foobar() -> None:\n            raise ValueError(42)\n\n        self.assertEqual({}, _foobar.statistics)\n        with self.assertRaises(RetryError):\n            await _foobar()\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n        self.assertIs(_foobar.__wrapped__.statistics, _foobar.statistics)\n\n\n# make sure mypy accepts passing an async sleep function"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Running the full suite with the project's test command.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run project test suite"}
[tool_result] ..............s............................................... [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.87s
[assistant] All 167 pass. Next I'll confirm the new tests actually fail on the original code, so they guard the bug.
[tool_use Bash] {"command": "D=$(mktemp -d) && git archive HEAD | tar -x -C \"$D\" && cp tests/test_tenacity.py tests/test_asyncio.py \"$D/tests/\" && cd \"$D\" && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no -k \"functools_wraps\" 2>&1 | tail -8; rm -rf \"$D\"", "description": "Confirm new tests fail on original code"}
[tool_result]                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'attempt_number'

tests/test_tenacity.py:1896: KeyError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_stats_through_functools_wraps_decorator
FAILED tests/test_tenacity.py::TestStatistics::test_stats_through_functools_wraps_decorator
2 failed, 166 deselected in 0.09s
Shell cwd was reset to ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1
[assistant] Both new tests fail on the original code and pass with the fix. Now a lint and type check on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; ls $PY | grep -E \"ruff|mypy\"; for t in ruff mypy; do command -v $t >/dev/null 2>&1 && echo \"$t on PATH\"; done; ($PY/ruff check tenacity tests 2>&1; $PY/ruff format --check tenacity tests 2>&1; $PY/mypy tenacity 2>&1) | tail -20", "description": "Run ruff and mypy if available"}
[tool_result] (eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
[assistant] Neither ruff nor mypy is installed in the project env, so I can't run them. I'll fix one over-long line in the sync test by hand.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "        def timing(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:\n            @functools.wraps(f)", "new_string": "        def timing(\n            f: typing.Callable[..., typing.Any],\n        ) -> typing.Callable[..., typing.Any]:\n            @functools.wraps(f)"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191747-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat; git status --short", "description": "Rerun suite and show diff summary"}
[tool_result] ...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.80s
 tenacity/__init__.py         | 29 +++++++++++++++++++++++++++--
 tenacity/asyncio/__init__.py |  4 ++--
 tests/test_asyncio.py        | 22 ++++++++++++++++++++++
 tests/test_tenacity.py       | 24 ++++++++++++++++++++++++
 4 files changed, 75 insertions(+), 4 deletions(-)
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
[assistant] `func.statistics` now stays visible through a `functools.wraps` wrapper, for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's. The full suite passes (167 passed, 1 skipped), and the two new regression tests fail on the original code.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` onto the outer one when the decorator is applied. At that moment `statistics` was still the initial `{}`. The retry wrapper later rebinds its own `statistics` on each call, but the outer wrapper keeps the stale copy.

**Fix:**
- `tenacity/__init
…[442 chars elided]…
tDecoratorWrapper` in `tests/test_asyncio.py`. Both wrap the retried function in a timing decorator and check the statistics and the identity with `__wrapped__`. No existing tests were changed.

**Behaviour change to be aware of:** `func.statistics` is now a live read-only view rather than a plain `dict`. Equality, item access, `len`, and iteration behave as before, but `isinstance(func.statistics, dict)` is now `False`, and code that mutates it will fail. I found no code in the repo that does either.

I could not run ruff or mypy because neither is installed in the project's test environment.
