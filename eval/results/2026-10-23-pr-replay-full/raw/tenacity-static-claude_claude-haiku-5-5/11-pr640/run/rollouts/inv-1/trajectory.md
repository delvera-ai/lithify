# trajectory inv-1

final message:
`TryAgain` raised from an `except` block with `reraise=True` now re-raises the underlying exception once retries are exhausted. Sync and async both work.

**Cause:** when retries run out, `exc_check` calls `RetryError.reraise()`, which re-raised the last attempt's exception. That exception was the `TryAgain` sentinel, so the real error was lost, even though it was still reachable as `TryAgain.__context__`.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): if the last attempt failed with a `TryAgain` that has a `__context__`, raise that context. A bare `raise TryAgain` with no context still raises `TryAgain`, as before. Sync and async share this path, so no `asyncio/` change was needed.

**Tests** (all five were red against the unfixed code, each raising `TryAgain` where `ValueError` was expected):
- `tests/test_tenacity.py`: `Retrying.__call__` with `reraise=True`; `for attempt in Retrying(...)`; direct `RetryError(fut).reraise()`.
- `tests/test_asyncio.py`: `AsyncRetrying.__call__`; `async for attempt in AsyncRetrying(...)`.

I did not add a test for `@retry`-decorated functions or `retry_with`. Both go through `__call__`, so they should behave the same, but I did not test them separately.

**Reno note:** `releasenotes/notes/tryagain-reraise-underlying-error-3c9e1f0a7b2d4e68.yaml`, a `fixes:` entry.

**Verification:**
- New tests: 5 passed (after the fix).
- Full suite: `exit=0`, 162 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: exit 0, 0 problems.
- ruff and mypy were not run; they are unavailable in this environment.

**Not changed:** without `reraise=True`, the `RetryError` still chains `TryAgain` as its cause (`raise retry_exc from fut.exception()`). The issue only asked about `reraise=True`, so I left that path alone.

## events
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; cat .lithify/harness/scripts/run_tests.py | head -60; grep -n \"TryAgain\\|reraise\" tenacity/*.py | head -80; ls releasenotes/notes | tail -5", "description": "Read tenacity change skill, test runner, and find TryAgain handling"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, adding, renaming or deprecating an argument of a wait/stop strategy (e.g. `wait_exponential_jitter`), emitting a `DeprecationWarning`, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing cha
…[20062 chars elided]…
acity/__init__.py:448:                if self.reraise:
tenacity/__init__.py:449:                    retry_exc.reraise()
tenacity/__init__.py:681:    reraise: bool = ...,
tenacity/__init__.py:699:    reraise: bool = False,
tenacity/__init__.py:763:    "TryAgain",
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 120,200p tenacity/__init__.py; echo ----; sed -n 400,470p tenacity/__init__.py; echo ----; grep -n \"TryAgain\\|reraise\\|def _run_retry\\|def __call__\\|def __aiter__\\|def __anext__\\|def iter\" tenacity/asyncio/__init__.py tenacity/tornadoweb.py", "description": "Read TryAgain, RetryError, and retry-loop code"}
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
…[4330 chars elided]…
pe: ignore[override]
tenacity/asyncio/__init__.py:139:    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
tenacity/asyncio/__init__.py:158:    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
tenacity/asyncio/__init__.py:168:    def __aiter__(self) -> "AsyncRetrying":
tenacity/asyncio/__init__.py:173:    async def __anext__(self) -> AttemptManager:
tenacity/tornadoweb.py:40:    def __call__(  # type: ignore[override]
[tool_use Bash] {"command": "grep -n \"class Future\" -A40 tenacity/__init__.py | head -60; grep -n \"TryAgain\" -B3 -A25 tests/test_tenacity.py | head -120; grep -n \"TryAgain\" tests/test_asyncio.py; grep -rn \"exc_check\\|reraise()\" tenacity/ ; git log --oneline -3 -- tenacity/__init__.py", "description": "Inspect Future class, existing TryAgain tests"}
[tool_result] 521:class Future(futures.Future[t.Any]):
522-    """Encapsulates a (future or past) attempted call to a target function."""
523-
524-    def __init__(self, attempt_number: int) -> None:
525-        super().__init__()
526-        self.attempt_number = attempt_number
527-
528-    @property
529-    def failed(self) -> bool:
530-        """Return whether a exception is being held in this future."""
531-        return self.exception() is not None
532-
533-    @classmethod
534-    def construct(
535- 
…[2883 chars elided]…
893-        if self.counter < self.count:
894-            self.counter += 1
tenacity/__init__.py:445:            def exc_check(rs: "RetryCallState") -> None:
tenacity/__init__.py:449:                    retry_exc.reraise()
tenacity/__init__.py:452:            self._add_action_func(exc_check)
6a2a08b fix: add missing space in type annotation (#617)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
4c1b7bc fix: sync func.retry.statistics with copy's statistics (#614)
[tool_use Bash] {"command": "grep -n \"reraise\\|^class \\|^from\\|^import\\|asynctest\" tests/test_asyncio.py | head -60; grep -n \"class TestRetryException\\|class TestRetryWithStatistics\\|class TestRetryIter\\|for attempt in\" tests/test_tenacity.py | head; grep -n \"^def \\|^class \" tests/test_tenacity.py | head -40; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Survey test file structure and style"}
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
54:def asynctest(callable_: _F) -> Callable[..., Any]:
79:class TestAsyncio(unittest.TestCase):
80:    @asynctest
86:    
…[2932 chars elided]…
) -> typing.Any:
1190:def _retryable_default_f(thing: typing.Any) -> typing.Any:
1195:def _retryable_test_with_exception_type_custom(thing: typing.Any) -> typing.Any:
1203:def _retryable_test_with_exception_type_custom_attempt_limit(
1209:class TestDecoratorWrapper(unittest.TestCase):
1453:class TestStatisticsKeys:
1470:class TestEnabled:
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Bash] {"command": "sed -n 1998,2030p tests/test_tenacity.py; echo ----; sed -n 220,242p tests/test_asyncio.py; echo ----; sed -n 1,20p releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; ls <work>/env-tenacity/bin/python && grep -n \"python\" .lithify/memory.md 2>/dev/null | head -3", "description": "View exception test class and async reraise test"}
[tool_result] class TestRetryException(unittest.TestCase):
    def test_retry_error_is_pickleable(self) -> None:
        import pickle

        expected = RetryError(last_attempt=123)  # type: ignore[arg-type]
        pickled = pickle.dumps(expected)
        actual = pickle.loads(pickled)
        self.assertEqual(expected.last_attempt, actual.last_attempt)


class TestRetryTyping(unittest.TestCase):
    def test_retry_type_annotations(self) -> None:
        """The decorator should maintain types of decorated 
…[927 chars elided]…
   stop=stop_after_attempt(1), reraise=True
            ):
                with attempt:
                    raise CustomError
        except CustomError:
            pass
        else:
            raise Exception

    @asynctest
    async def test_sleeps(self) -> None:
----
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 30,53p tests/test_asyncio.py; sed -n 79,100p tests/test_asyncio.py; grep -n \"retry_never\" tenacity/__init__.py | head -3", "description": "Check async test imports and style"}
[tool_result] import pytest

import tenacity
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
from tenacity.wait import wait_fixed

from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)

_F = TypeVar("_F", bound=Callable[..., Coroutine[Any, Any, Any]])


class TestAsyncio(unittest.TestCase):
    @asynctest

…[256 chars elided]…
o.iscoroutinefunction(_retryable_coroutine)
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
        thing = NoIOErrorAfterCount(5)
        retrying = AsyncRetrying()
        await retrying(_async_function, thing)
        assert thing.counter == thing.count

    @asynctest
    async def test_stop_after_attempt(self) -> None:
        thing = NoIOErrorAfterCount(2)
56:    retry_never,
784:    "retry_never",
[assistant] Writing the regression tests first, sync and async, across each entry point.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_tenacity.py", "old_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5, r.statistics[\"attempt_number\"])\n\n", "new_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5
…[1061 chars elided]…
try_again(self) -> None:\n        try:\n            try:\n                raise ValueError(\"the real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n        except tenacity.TryAgain as exc:\n            fut = tenacity.Future(1)\n            fut.set_exception(exc)\n\n        with self.assertRaises(ValueError):\n            tenacity.RetryError(fut).reraise()\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_asyncio.py", "old_string": "        except CustomError:\n            pass\n        else:\n            raise Exception\n\n    @asynctest\n    async def test_sleeps(self) -> None:", "new_string": "        except CustomError:\n            pass\n  
…[297 chars elided]…
.TryAgain\n\n        try:\n            async for attempt in tasyncio.AsyncRetrying(\n                stop=stop_after_attempt(2), retry=tenacity.retry_never, reraise=True\n            ):\n                with attempt:\n                    await _r()\n        except ValueError:\n            pass\n        else:\n            raise Exception\n\n    @asynctest\n    async def test_sleeps(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now an async `__call__` test in `TestAsyncio`, alongside the existing call-style tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_iscoroutinefunction(self) -> None:", "new_string": "    @asynctest\n    async def test_reraise_try_again_underlying_error_call(self) -> None:\n        async def _r() -> None:\n     
…[16 chars elided]…
             raise ValueError(\"the real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n\n        retrying = AsyncRetrying(\n            stop=stop_after_attempt(2), retry=tenacity.retry_never, reraise=True\n        )\n        with pytest.raises(ValueError):\n            await retrying(_r)\n\n    @asynctest\n    async def test_iscoroutinefunction(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestRetryingName 2>&1 | tail -3; $PY .lithify/harness/scripts/run_tests.py --timeout 60 -k \"try_again_reraise or reraise_unwraps or reraise_try_again\" tests/test_tenacity.py tests/test_asyncio.py 2>&1 | tail -30", "description": "Run new regression tests against unfixed code"}
[tool_result] ============================== 8 passed in 0.04s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
    retry_exc.reraise()
tenacity/__init__.py:188: in reraise
    raise self.last_attempt.result()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
~/.local/share/uv/python/cpy
…[692 chars elided]…
sts/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_underlying_error
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_underlying_error_iter
FAILED tests/test_asyncio.py::TestAsyncio::test_reraise_try_again_underlying_error_call
FAILED tests/test_asyncio.py::TestContextManager::test_reraise_try_again_underlying_error
====================== 5 failed, 147 deselected in 0.16s =======================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All five new tests are red, each raising `TryAgain` where the `ValueError` is expected. Now the fix: `RetryError.reraise()` is the one place the sync and async paths both re-raise the last attempt, so I'll unwrap the sentinel there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tenacity/__init__.py", "old_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            raise self.last_attempt.result()\n        raise self", "new_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            exc = self.last_attempt.exception()\n            # A TryAgain raised while handling an error is only a retry signal:\n            # re-raise the error that caused it.\n            if isinstance(exc, TryAgain) and exc.__context__ is not None:\n                raise exc.__context__\n            raise self.last_attempt.result()\n        raise self"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/inv-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, the reno note (this is a user-visible fix, so the contract requires one), then the green runs.
[tool_use Bash] {"command": "cat > releasenotes/notes/tryagain-reraise-underlying-error-3c9e1f0a7b2d4e68.yaml <<'EOF'\n---\nfixes:\n  - |\n    With ``reraise=True``, a ``TryAgain`` raised while handling an exception now\n    re-raises that underlying exception once the retries are exhausted, instead\n    of the ``TryAgain`` sentinel. This applies to sync and async retrying.\nEOF\nPY=<tmp>/-Users
…[195 chars elided]…
_reraise or reraise_unwraps or reraise_try_again\" tests/test_tenacity.py tests/test_asyncio.py 2>&1 | tail -4; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"run=$?\"; tail -4 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc.txt 2>&1; echo \"check=$?\"; cat /tmp/cc.txt | tail -20", "description": "Add reno note, run new tests, full suite, and checks"}
[tool_result] ====================== 5 passed, 147 deselected in 0.02s =======================
---
exit=0 (pytest); full log: /tmp/run_tests.log
run=0

============== 162 passed, 1 skipped, 12 subtests passed in 1.82s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
check=0
changed: releasenotes/notes/tryagain-reraise-underlying-error-3c9e1f0a7b2d4e68.yaml, tenacity/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] `TryAgain` raised from an `except` block with `reraise=True` now re-raises the underlying exception once retries are exhausted. Sync and async both work.

**Cause:** when retries run out, `exc_check` calls `RetryError.reraise()`, which re-raised the last attempt's exception. That exception was the `TryAgain` sentinel, so the real error was lost, even though it was still reachable as `TryAgain.__context__`.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): if the last attempt failed with a `TryAgain` that has a `__context__`, raise that context. A bare `raise TryAgain` with no context st
…[575 chars elided]…
same, but I did not test them separately.

**Reno note:** `releasenotes/notes/tryagain-reraise-underlying-error-3c9e1f0a7b2d4e68.yaml`, a `fixes:` entry.

**Verification:**
- New tests: 5 passed (after the fix).
- Full suite: `exit=0`, 162 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: exit 0, 0 problems.
- ruff and mypy were not run; they are unavailable in this environment.

**Not changed:** without `reraise=True`, the `RetryError` still chains `TryAgain` as its cause (`raise retry_exc from fut.exception()`). The issue only asked about `reraise=True`, so I left that path alone.
