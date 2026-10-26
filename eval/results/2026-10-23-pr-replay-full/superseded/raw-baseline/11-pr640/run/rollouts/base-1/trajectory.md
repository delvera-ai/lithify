# trajectory base-1

final message:
With `reraise=True`, a `TryAgain` raised inside an `except` block now re-raises the original exception once attempts are exhausted. This works for both sync and async retrying. The full suite passes (159 passed, 1 skipped), and the new tests fail without the fix.

**The change** is in `RetryError.reraise` in `tenacity/__init__.py`. Both sync and async paths go through it. If the last attempt failed with `TryAgain` and that `TryAgain` has a `__context__` (the exception it was raised from), it raises that context. A bare `TryAgain` with no surrounding `except` still raises `TryAgain`, which keeps the existing `test_retry_try_again_forever_reraise` passing.

**Tests added:**
- `tests/test_tenacity.py`: `test_retry_try_again_forever_reraise_cause` covers the sync case from the report.
- `tests/test_asyncio.py`: `test_reraise_try_again_cause` covers the async case. I also added the `retry_never` import it needs.

**Release note:** `releasenotes/notes/fix-try-again-reraise-cause-5c2e9d1a7b3f4e60.yaml`, a `fixes` entry in the repo's reno format.

I did not commit anything. I also did not change `RetryError.reraise`'s behaviour for `TryAgain` raised with no cause, so a manual `reraise()` call in that case still raises `TryAgain`.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"TryAgain\\|reraise\\|def iter\\|def __call__\\|def _post_retry_check_actions\\|def iter_state\\|raise_retry\\|retry_exc_state\\|fut.exception\\|def exc_check\" tenacity/*.py | head -100", "description": "Check repo state and find TryAgain/reraise usages"}
[tool_result] tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:239:        reraise: bool = False,
tenacity/__init__.py:252:        self.reraise = reraise
tenacity/__init__.py:268:        reraise: bool | object = _unset,
tenacity/__init__.py:285:            reraise=_first_set(reraise, self.reraise),
tenacity/__init__.py:344:    def iter_state(self) -> IterState:
tenacity/__init__.py:403:    def iter(self, retry_state: "RetryC
…[3074 chars elided]…
loat:
tenacity/wait.py:144:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:171:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:201:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:236:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:281:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/tornadoweb.py:40:    def __call__(  # type: ignore[override]
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "offset": 120, "limit": 340}
[tool_result] 120	    def reset(self) -> None:
121	        self.actions = []
122	        self.retry_run_result = False
123	        self.stop_run_result = False
124	        self.is_explicit_retry = False
125	
126	
127	class TryAgain(Exception):
128	    """Always retry the executed function when raised."""
129	
130	
131	NO_RESULT = object()
132	
133	
134	class DoAttempt:
135	    pass
136	
137	
138	class DoSleep(float):
139	    pass
140	
141	
142	class BaseAction:
143	    """Base class for representing actions t
…[12619 chars elided]…
retry_exc = self.retry_error_cls(fut)
448	                if self.reraise:
449	                    retry_exc.reraise()
450	                raise retry_exc from fut.exception()
451	
452	            self._add_action_func(exc_check)
453	            return
454	
455	        def next_action(rs: "RetryCallState") -> None:
456	            sleep = rs.upcoming_sleep
457	            rs.next_action = RetryAction(sleep)
458	            rs.idle_for += sleep
459	            self.statistics["idle_for"] += sleep
[tool_use Bash] {"command": "grep -rn \"reraise()\\|\\.result()\\|TryAgain\" tenacity/ tests/ docs/ README* 2>/dev/null | grep -v \"\\.pyc\"; ls; git log --oneline -3 -- tenacity/__init__.py", "description": "Find reraise call sites, TryAgain usages, and tests"}
[tool_result] tenacity/retry.py:199:            return self.predicate(retry_state.outcome.result())
tenacity/retry.py:214:            return not self.predicate(retry_state.outcome.result())
tenacity/before_sleep.py:49:            verb, value = "returned", retry_state.outcome.result()
tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:188:            raise self.last_attempt.result()
tenacity/__init__.py:421:            fut.exception(), TryAgain
tenacity/__init__.py:429:            self._a
…[901 chars elided]…
ise()
README.rst:278:It's also possible to retry explicitly at any time by raising the `TryAgain`
README.rst:287:          raise TryAgain
README.rst:402:        return retry_state.outcome.result()
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
6a2a08b fix: add missing space in type annotation (#617)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
4c1b7bc fix: sync func.retry.statistics with copy's statistics (#614)
[tool_use Bash] {"command": "sed -n 830,875p tests/test_tenacity.py; echo ----; sed -n 1730,1775p tests/test_tenacity.py; echo ----; cat AGENTS.md | head -60; ls releasenotes/notes | tail -5", "description": "View existing TryAgain and reraise tests and project notes"}
[tool_result]     def test_retry_and_coalesces(self) -> None:
        """Multiple & operations flatten into a single retry_all."""
        a = tenacity.retry_if_result(lambda x: x == 1)
        b = tenacity.retry_if_result(lambda x: x > 0)
        c = tenacity.retry_if_result(lambda x: x < 10)

        combined = a & b & c
        self.assertIsInstance(combined, retry_all)
        self.assertEqual(len(combined.retries), 3)

    def _raise_try_again(self) -> None:
        self._attempts += 1
        if self._a
…[3111 chars elided]…
memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The existing test `test_retry_try_again_forever_reraise` raises `TryAgain` with no surrounding `except`, so it has no underlying cause. The fix should only swap in the cause when there is one. I'll make that change in `RetryError.reraise`, which both sync and async paths use through `exc_check`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "old_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            raise self.last_attempt.result()\n        raise self", "new_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            exc = self.last_attempt.exception()\n            # A TryAgain raised inside an ``except`` block is only a retry signal;\n            # re-raise the exception that caused it instead.\n            if isinstance(exc, TryAgain) and exc.__context__ is not None:\n                raise exc.__context__\n            raise self.last_attempt.result()\n        raise self"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll add regression tests for sync and async, and check how the async tests are written.
[tool_use Bash] {"command": "grep -n \"TryAgain\\|reraise\\|^class \\|^import\\|^from\" tests/test_asyncio.py | head -40; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml", "description": "Inspect async tests and release note format"}
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
181:class TestTrio(unittest.TestC
…[5 chars elided]…

195:class TestContextManager(unittest.TestCase):
226:    async def test_reraise(self) -> None:
232:                stop=stop_after_attempt(1), reraise=True
444:class TestDecoratorWrapper(unittest.TestCase):
513:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
---
features:
  - |
    Add ``min`` parameter to ``wait_exponential_jitter`` to set a minimum wait
    time floor, consistent with ``wait_exponential``. Also accept ``timedelta``
    for ``max``, ``jitter``, and ``min`` parameters.
[tool_use Bash] {"command": "sed -n 79,100p tests/test_asyncio.py; echo ...; sed -n 195,245p tests/test_asyncio.py", "description": "Read async test patterns"}
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
      
…[1252 chars elided]…
 CustomError(Exception):
            pass

        try:
            async for attempt in tasyncio.AsyncRetrying(
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
        start = current_time_ms()
        try:
            async for attempt in tasyncio.AsyncRetrying(
[assistant] Adding the sync test next to the existing `TryAgain` tests, and an async test beside the async reraise tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "old_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5, r.statistics[\"attempt_number\"])\n\n", "new_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(
…[189 chars elided]…
e real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n\n        r = Retrying(\n            stop=tenacity.stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "        except CustomError:\n            pass\n        else:\n            raise Exception\n\n    @asynctest\n    async def test_sleeps(self) -> None:", "new_string": "        except CustomError:\n            pass\n 
…[190 chars elided]…
se ValueError(\"the real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n\n        retrying = tasyncio.AsyncRetrying(\n            stop=stop_after_attempt(2), retry=retry_never, reraise=True\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            await retrying(_r)\n\n    @asynctest\n    async def test_sleeps(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 33,42p tests/test_asyncio.py; grep -n \"retry_never\" tests/test_asyncio.py | head -3; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check imports and run the project test suite"}
[tool_result] from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
250:            stop=stop_after_attempt(2), retry=retry_never, reraise=True
            try:
                raise ValueError("the real error")
            except ValueError:
                raise tenacity.TryAgain
    
        retrying = tasyncio.AsyncRetrying(
>           stop=stop_after_attempt(2), retry=retry_never, reraise=True
                                              ^^^^^^^^^^^
        )
E       NameError: name 'retry_never' is not defined

tests/test_asyncio.py:250: NameError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_reraise_try_again_cause
1 failed, 158 passed, 1 skipped, 12 subtests passed in 1.87s
[assistant] The async test needs `retry_never` imported. Adding it to the existing import list and rerunning.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "    retry_if_result,\n    stop_after_attempt,\n)\nfrom tenacity import asyncio as tasyncio", "new_string": "    retry_if_result,\n    retry_never,\n    stop_after_attempt,\n)\nfrom tenacity import asyncio as tasyncio"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git stash list >/dev/null; cp tenacity/__init__.py /tmp/fixed_init.py && git show HEAD:tenacity/__init__.py > tenacity/__init__.py && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no -k try_again 2>&1 | tail -4; cp /tmp/fixed_init.py tenacity/__init__.py && git diff --stat", "description": "Run full suite, then confirm new tests fail without the fix"}
[tool_result] ............s....................................................................................................................... [ 82%]
............................                                             [100%]
159 passed, 1 skipped, 12 subtests passed in 1.82s
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_reraise_try_again_cause
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_forever_reraise_cause
2 failed, 3 passed, 155 deselected in 0.09s
 tenacity/__init__.py   |  5 +++++
 tests/test_asyncio.py  | 15 +++++++++++++++
 tests/test_tenacity.py | 16 ++++++++++++++++
 3 files changed, 36 insertions(+)
[assistant] Full suite passes (159 passed), and both new tests fail without the fix. Adding a release note, since the repo uses reno.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/releasenotes/notes/fix-try-again-reraise-cause-5c2e9d1a7b3f4e60.yaml", "content": "---\nfixes:\n  - |\n    With ``reraise=True``, a ``TryAgain`` raised inside an ``except`` block now\n    re-raises the underlying exception after the attempts are exhausted, instead\n    of the opaque ``TryAgain`` sentinel. This applies to both sync and async\n    retrying.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164105-bug-when-tryagain-is-raised-from/base-1/releasenotes/notes/fix-try-again-reraise-cause-5c2e9d1a7b3f4e60.yaml (file state is current in your context — no need to Read it back)
[assistant] With `reraise=True`, a `TryAgain` raised inside an `except` block now re-raises the original exception once attempts are exhausted. This works for both sync and async retrying. The full suite passes (159 passed, 1 skipped), and the new tests fail without the fix.

**The change** is in `RetryError.reraise` in `tenacity/__init__.py`. Both sync and async paths go through it. If the last attempt failed with `TryAgain` and that `TryAgain` has a `__context__` (the exception it was raised from), it raises that context. A bare `TryAgain` with no surrounding `except` still raises `TryAgain`, which keep
…[41 chars elided]…
ver_reraise` passing.

**Tests added:**
- `tests/test_tenacity.py`: `test_retry_try_again_forever_reraise_cause` covers the sync case from the report.
- `tests/test_asyncio.py`: `test_reraise_try_again_cause` covers the async case. I also added the `retry_never` import it needs.

**Release note:** `releasenotes/notes/fix-try-again-reraise-cause-5c2e9d1a7b3f4e60.yaml`, a `fixes` entry in the repo's reno format.

I did not commit anything. I also did not change `RetryError.reraise`'s behaviour for `TryAgain` raised with no cause, so a manual `reraise()` call in that case still raises `TryAgain`.
