# trajectory base-1

final message:
When `TryAgain` is raised from an `except` block with `reraise=True`, the original exception is now re-raised, for both sync and async retrying. The full test suite passes (159 passed, 1 skipped, same skip as before).

**Cause:** `RetryError.reraise()` in `tenacity/__init__.py` re-raised the last attempt's exception, which for a manual retry is the `TryAgain` sentinel. Python records the exception being handled as `TryAgain.__context__`, and that was never used.

**Fix:** `RetryError.reraise()` now checks whether the last exception is a `TryAgain` with a context. If so, it raises that context. Otherwise it behaves as before. The async path goes through the same method, so one change covers both. A bare `TryAgain` with no context still propagates unchanged, which keeps the existing `test_retry_try_again_forever_reraise` passing.

**Tests added (no existing tests edited):**
- `tests/test_tenacity.py`: `test_retry_try_again_reraises_cause`, the issue's repro with `stop_after_attempt(2)`, asserting `ValueError` and two attempts.
- `tests/test_asyncio.py`: the same scenario with `AsyncRetrying`.

I didn't confirm that the new tests fail on the original code. `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"TryAgain\\|reraise\\|def iter\\|_post_stop_check_actions\\|def __call__\\|retry_error_cls\\|RetryError\" tenacity/__init__.py tenacity/asyncio/__init__.py | head -80", "description": "Locate TryAgain and reraise handling"}
[tool_result] tenacity/asyncio/__init__.py:29:    RetryError,
tenacity/asyncio/__init__.py:89:        reraise: bool = False,
tenacity/asyncio/__init__.py:90:        retry_error_cls: type["RetryError"] = RetryError,
tenacity/asyncio/__init__.py:104:            reraise=reraise,
tenacity/asyncio/__init__.py:105:            retry_error_cls=retry_error_cls,
tenacity/asyncio/__init__.py:111:    async def __call__(  # type: ignore[override]
tenacity/asyncio/__init__.py:158:    async def iter(self, retry_state: "Retr
…[1627 chars elided]…
/__init__.py:650:    def __call__(
tenacity/__init__.py:654:    def __call__(
tenacity/__init__.py:658:    def __call__(
tenacity/__init__.py:662:    def __call__(
tenacity/__init__.py:681:    reraise: bool = ...,
tenacity/__init__.py:682:    retry_error_cls: type["RetryError"] = ...,
tenacity/__init__.py:699:    reraise: bool = False,
tenacity/__init__.py:700:    retry_error_cls: type["RetryError"] = RetryError,
tenacity/__init__.py:761:    "RetryError",
tenacity/__init__.py:763:    "TryAgain",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "offset": 340, "limit": 170}
[tool_result] 340	            self._local.statistics = t.cast("dict[str, t.Any]", {})
341	        return self._local.statistics  # type: ignore[no-any-return]
342	
343	    @property
344	    def iter_state(self) -> IterState:
345	        if not hasattr(self._local, "iter_state"):
346	            self._local.iter_state = IterState()
347	        return self._local.iter_state  # type: ignore[no-any-return]
348	
349	    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
350	        """Wrap a function
…[5843 chars elided]…
	    def __call__(
497	        self,
498	        fn: t.Callable[..., WrappedFnReturnT],
499	        *args: t.Any,
500	        **kwargs: t.Any,
501	    ) -> WrappedFnReturnT:
502	        self.begin()
503	
504	        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
505	        while True:
506	            do = self.iter(retry_state=retry_state)
507	            if isinstance(do, DoAttempt):
508	                try:
509	                    result = fn(*args, **kwargs)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tenacity/asyncio/__init__.py", "offset": 150, "limit": 60}
[tool_result] 150	        retry_state.upcoming_sleep = sleep
151	
152	    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
153	        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
154	        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
155	            retry_state
156	        )
157	
158	    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
159	        self._begin_iter
…[1867 chars elided]…
nore[attr-defined]
200	            self._local.statistics = copy.statistics
201	            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
202	
203	        # Preserve attributes
204	        async_wrapped.retry = self  # type: ignore[attr-defined]
205	        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
206	        async_wrapped.statistics = {}  # type: ignore[attr-defined]
207	
208	        return t.cast("_RetryDecorated[P, R]", async_wrapped)
209	
[tool_use Bash] {"command": "sed -n 120,200p tenacity/__init__.py && sed -n 509,530p tenacity/__init__.py && grep -n \"class AttemptManager\" -A 25 tenacity/__init__.py && sed -n 111,150p tenacity/asyncio/__init__.py && git log --oneline -3 -- tenacity/__init__.py && ls tests && grep -rn \"TryAgain\" tests | head -20", "description": "Read TryAgain, RetryError, and call paths"}
[tool_result]     def reset(self) -> None:
        self.actions = []
        self.retry_run_result = False
        self.stop_run_result = False
        self.is_explicit_retry = False


class TryAgain(Exception):
    """Always retry the executed function when raised."""


NO_RESULT = object()


class DoAttempt:
    pass


class DoSleep(float):
    pass


class BaseAction:
    """Base class for representing actions to take by retry object.

    Concrete implementations must define:
    - __init__: to initialize
…[4880 chars elided]…
 deprecated typing constructs with modern syntax (#616)
4c1b7bc fix: sync func.retry.statistics with copy's statistics (#614)
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
tests/test_tenacity.py:843:            raise tenacity.TryAgain
tests/test_tenacity.py:854:            raise tenacity.TryAgain
tests/test_tenacity.py:862:            raise tenacity.TryAgain
tests/test_tenacity.py:869:        self.assertRaises(tenacity.TryAgain, r, _r)
[tool_use Bash] {"command": "sed -n 835,875p tests/test_tenacity.py && grep -n \"reraise\" tests/test_tenacity.py | head -20 && ls <work>/env-tenacity/bin/python 2>&1", "description": "Inspect existing TryAgain tests and env python"}
[tool_result]         combined = a & b & c
        self.assertIsInstance(combined, retry_all)
        self.assertEqual(len(combined.retries), 3)

    def _raise_try_again(self) -> None:
        self._attempts += 1
        if self._attempts < 3:
            raise tenacity.TryAgain

    def test_retry_try_again(self) -> None:
        self._attempts = 0
        Retrying(stop=tenacity.stop_after_attempt(5), retry=tenacity.retry_never)(
            self._raise_try_again
        )
        self.assertEqual(3, self._
…[1593 chars elided]…
 retry_err.reraise()
1769:        self.assertRaises(tenacity.RetryError, _reraised_mock_fn)
1772:    def test_reraise_no_exception(self) -> None:
1779:            reraise=True,
1828:            reraise=True,
1912:    def test_context_manager_reraise(self) -> None:
1918:        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
<work>/env-tenacity/bin/python
[assistant] The root cause is in `RetryError.reraise()`: it re-raises the last attempt's exception, which for a manual retry is the `TryAgain` sentinel. Python keeps the original error as `TryAgain.__context__` when `TryAgain` is raised inside an `except` block, so `reraise()` can surface that instead. The async path goes through the same `_post_stop_check_actions` → `RetryError.reraise()`, so one fix covers both. The existing `test_retry_try_again_forever_reraise` raises `TryAgain` with no context and expects `TryAgain`, so that case must keep working.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "old_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            raise self.last_attempt.result()\n        raise self", "new_string": "    def reraise(self) -> t.NoReturn:\n        if self.last
…[12 chars elided]…
led:\n            exc = self.last_attempt.exception()\n            # A TryAgain raised inside an `except` block is a manual retry; the\n            # exception that triggered it is its context, so surface that instead.\n            if isinstance(exc, TryAgain) and exc.__context__ is not None:\n                raise exc.__context__\n            raise self.last_attempt.result()\n        raise self"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `TryAgain` test, for sync and async.
[tool_use Bash] {"command": "grep -n \"try_again\\|TryAgain\\|^class \\|^import\\|^from\" tests/test_asyncio.py | head -30", "description": "Find async test file structure"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
79:class TestAsyncio(unittest.TestCase):
163:class TestAsyncEnabled(unittest.TestCase):
181:class TestTrio(unittest.TestCase):
195:class TestContextManager(unittest.TestCase):
444:class TestDecoratorWrapper(unittest.TestCase):
513:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
[tool_use Bash] {"command": "sed -n 79,100p tests/test_asyncio.py && sed -n 40,60p tests/test_asyncio.py", "description": "Read async test class header"}
[tool_result] class TestAsyncio(unittest.TestCase):
    @asynctest
    async def test_retry(self) -> None:
        thing = NoIOErrorAfterCount(5)
        await _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @asynctest
    async def test_iscoroutinefunction(self) -> None:
        assert asyncio.iscoroutinefunction(_retryable_coroutine)
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
      
…[234 chars elided]…
  thing = NoIOErrorAfterCount(2)
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)

_F = TypeVar("_F", bound=Callable[..., Coroutine[Any, Any, Any]])


def asynctest(callable_: _F) -> Callable[..., Any]:
    @wraps(callable_)
    def wrapper(*a: Any, **kw: Any) -> Any:
        return asyncio.run(callable_(*a, **kw))

    return wrapper
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "old_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5, r.statistics[\"attempt_number\"])\n\n    def test_retry_if_exception_message_negative_no_inputs(self) -> None:", "new_string": "     
…[328 chars elided]…
nacity.TryAgain\n\n        r = Retrying(\n            stop=tenacity.stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n    def test_retry_if_exception_message_negative_no_inputs(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_iscoroutinefunction(self) -> None:", "new_string": "    @asynctest\n    async def test_retry_try_again_reraises_cause(self) -> None:\n        async def _r() -> None:\n            t
…[125 chars elided]…
Again\n\n        retrying = AsyncRetrying(\n            stop=stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            await retrying(_r)\n        assert retrying.statistics[\"attempt_number\"] == 2\n\n    @asynctest\n    async def test_iscoroutinefunction(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161607-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run the project test suite"}
[tool_result] .............s...................................................................................................................... [ 82%]
............................                                             [100%]
159 passed, 1 skipped, 12 subtests passed in 1.90s
[assistant] All 159 pass, with 1 skipped as before. I'll run the linters the project uses, if they're installed.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin; ($P/python -m ruff check tenacity tests && $P/python -m ruff format --check tenacity tests) 2>&1 | tail -5; ($P/python -m mypy tenacity 2>&1 | tail -3) ; git status --short", "description": "Run ruff and mypy on changed code"}
[tool_result] <work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
[assistant] When `TryAgain` is raised from an `except` block with `reraise=True`, the original exception is now re-raised, for both sync and async retrying. The full test suite passes (159 passed, 1 skipped, same skip as before).

**Cause:** `RetryError.reraise()` in `tenacity/__init__.py` re-raised the last attempt's exception, which for a manual retry is the `TryAgain` sentinel. Python records the exception being handled as `TryAgain.__context__`, and that was never used.

**Fix:** `RetryError.reraise()` now checks whether the last exception is a `TryAgain` with a context. If so, it raises that context.
…[85 chars elided]…
change covers both. A bare `TryAgain` with no context still propagates unchanged, which keeps the existing `test_retry_try_again_forever_reraise` passing.

**Tests added (no existing tests edited):**
- `tests/test_tenacity.py`: `test_retry_try_again_reraises_cause`, the issue's repro with `stop_after_attempt(2)`, asserting `ValueError` and two attempts.
- `tests/test_asyncio.py`: the same scenario with `AsyncRetrying`.

I didn't confirm that the new tests fail on the original code. `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. Nothing is committed.
