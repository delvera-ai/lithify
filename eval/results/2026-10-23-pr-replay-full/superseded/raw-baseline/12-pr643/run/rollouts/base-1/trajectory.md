# trajectory base-1

final message:
`Retrying(enabled=False)` and `AsyncRetrying(enabled=False)` now run the body exactly once under the iterator pattern, and the original exception propagates unchanged. The full test suite passes (163 passed, 1 skipped).

**Cause:** `enabled` was checked in `wraps()` and `__call__`, but not in the iterator paths (`BaseRetrying.__iter__` and `AsyncRetrying.__anext__`). Those kept retrying, so the body ran 3 times and then raised `RetryError`.

**Fix:**
- `tenacity/__init__.py`: when disabled, `__iter__` yields a single `AttemptManager` and returns. `AttemptManager` takes an `enabled` flag, and when it is false `__exit__` returns `None` so the exception is not swallowed.
- `tenacity/asyncio/__init__.py`: when disabled, `__anext__` returns one `AttemptManager` and then raises `StopAsyncIteration`, using a one-shot flag reset in `__aiter__`.

**Tests:** I added two sync tests (failing body runs once and propagates `ValueError`; passing body runs once) and one async test. These are new tests only; no existing test was edited. I reproduced the bug before the change (3 calls, `RetryError`) and confirmed the fix (1 call, `ValueError`).

Ruff is not installed in the project's test environment, so I did not run the formatter or linter. I wrapped the one long line by hand. mypy was not run either.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"enabled\" tenacity/*.py | head -60", "description": "Check status and find enabled references"}
[tool_result] tenacity/__init__.py:251:        enabled: bool = True,
tenacity/__init__.py:265:        self.enabled = enabled
tenacity/__init__.py:282:        enabled: bool | object = _unset,
tenacity/__init__.py:299:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:367:            if not self.enabled:
tenacity/__init__.py:693:    enabled: bool = ...,
tenacity/__init__.py:711:    enabled: bool = True,
[tool_use Bash] {"command": "sed -n 340,420p tenacity/__init__.py && echo ---- && grep -n \"def __iter__\\|def __aiter__\\|def __anext__\\|def __next__\\|class AttemptManager\\|class RetryCallState\\|def iter\\|def wraps\\|def __call__\\|def _run_retry\\|def iter_state\\|AsyncRetrying\" tenacity/__init__.py tenacity/asyncio/__init__.py", "description": "Read Retrying.__call__/iter and locate iterator code"}
[tool_result]         .. note:: The values in this dictionary are local to the thread
                  running call (so if multiple threads share the same retrying
                  object - either directly or indirectly) they will each have
                  their own view of statistics they have collected (in the
                  future we may provide a way to aggregate the various
                  statistics from each thread).
        """
        if not hasattr(self._local, "statistics"):
            se
…[4359 chars elided]…
__init__.py:554:class RetryCallState:
tenacity/__init__.py:653:    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
tenacity/__init__.py:658:    def __call__(
tenacity/__init__.py:662:    def __call__(
tenacity/__init__.py:666:    def __call__(
tenacity/__init__.py:670:    def __call__(
tenacity/__init__.py:737:            r = AsyncRetrying(*dargs, **dkw)
tenacity/__init__.py:752:from tenacity.asyncio import AsyncRetrying  # noqa: E402
tenacity/__init__.py:760:    "AsyncRetrying",
[tool_use Bash] {"command": "sed -n 420,552p tenacity/__init__.py && echo ---- && sed -n 105,185p tenacity/asyncio/__init__.py", "description": "Read iterator and call logic in sync and async"}
[tool_result]         fut = retry_state.outcome
        if fut is None:
            if self.before is not None:
                self._add_action_func(self.before)
            self._add_action_func(lambda rs: DoAttempt())
            return

        self.iter_state.is_explicit_retry = fut.failed and isinstance(
            fut.exception(), TryAgain
        )
        if not self.iter_state.is_explicit_retry:
            self._add_action_func(self._run_retry)
        self._add_action_func(self._post_retry_check_
…[6678 chars elided]…
-> AttemptManager:
        while True:
            do = await self.iter(retry_state=self._retry_state)
            if do is None:
                raise StopAsyncIteration
            if isinstance(do, DoAttempt):
                return AttemptManager(retry_state=self._retry_state)
            if isinstance(do, DoSleep):
                self._retry_state.prepare_for_next_attempt()
                await self.sleep(do)  # type: ignore[misc]
            else:
                raise StopAsyncIteration
[tool_use Bash] {"command": "sed -n 200,235p tenacity/__init__.py && echo ---- && sed -n 60,100p tenacity/asyncio/__init__.py && echo ---- && grep -rn \"enabled\" tests/ docs/ README* 2>/dev/null | head -30 && git log --oneline -3 -- tenacity/__init__.py", "description": "Read AttemptManager, async init, and existing enabled tests/docs"}
[tool_result]         return f"{self.__class__.__name__}[{self.last_attempt}]"


class AttemptManager:
    """Manage attempt context."""

    def __init__(self, retry_state: "RetryCallState"):
        self.retry_state = retry_state

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: "types.TracebackType | None",
    ) -> bool | None:
        if exc_type is not None and exc_valu
…[3477 chars elided]…
nabled=True, stop=tenacity.stop_after_attempt(3), reraise=True)
README.rst:624:You can disable retrying entirely by passing ``enabled=False``. When disabled,
README.rst:633:        enabled=os.getenv("ENABLE_RETRIES", "1") != "0",
README.rst:651:    call_api.retry_with(enabled=False)()
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
[assistant] The iterator paths (`BaseRetrying.__iter__` and `AsyncRetrying.__anext__`) never check `self.enabled`, unlike `wraps()` and `__call__`. I'll reproduce the bug first, then fix it.
[tool_use Bash] {"command": "cat > /tmp/repro_enabled.py <<'EOF'\nimport asyncio\nimport tenacity\nfrom tenacity import Retrying, AsyncRetrying, stop_after_attempt\n\ncalls = 0\ntry:\n    for attempt in Retrying(enabled=False, stop=stop_after_attempt(3)):\n        with attempt:\n            calls += 1\n            raise ValueError(\"boom\")\nexcept Exception as e:\n    print(\"sync:\", type(e).__name__, \"calls=\
…[281 chars elided]…
 e:\n        print(\"async:\", type(e).__name__, \"calls=\", calls)\nasyncio.run(main())\nEOF\n<work>/env-tenacity/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/repro_enabled.py').read())\"", "description": "Reproduce the enabled=False iterator bug"}
[tool_result] sync: RetryError calls= 3
async: RetryError calls= 3
[assistant] Reproduced: both paths make 3 calls and raise `RetryError`. Now the fix. `AttemptManager` swallows exceptions, so disabled mode also needs to let them propagate.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "    def __init__(self, retry_state: \"RetryCallState\"):\n        self.retry_state = retry_state\n\n    def __enter__(self) -> None:\n        pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseExcep
…[401 chars elided]…
   pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: \"types.TracebackType | None\",\n    ) -> bool | None:\n        if not self.enabled:\n            # Retrying is disabled: let any exception propagate unchanged.\n            return None\n        if exc_type is not None and exc_value is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                yield Atte
…[90 chars elided]…
self, fn=None, args=(), kwargs={})\n        if not self.enabled:\n            # Run the body exactly once, without retrying.\n            yield AttemptManager(retry_state=retry_state, enabled=False)\n            return\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                yield AttemptManager(retry_state=retry_state)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async iterator. `__aiter__` resets a one-shot flag and `__anext__` uses it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "old_string": "    def __aiter__(self) -> \"AsyncRetrying\":\n        self.begin()\n        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        return self\n\n    async def __anext__(self) -> Atte
…[252 chars elided]…
  return self\n\n    async def __anext__(self) -> AttemptManager:\n        if not self.enabled:\n            # Run the body exactly once, without retrying.\n            if self._disabled_attempt_yielded:\n                raise StopAsyncIteration\n            self._disabled_attempt_yielded = True\n            return AttemptManager(retry_state=self._retry_state, enabled=False)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next I'll add regression tests next to the existing `enabled=False` tests. I'm only adding new tests and leaving the existing ones untouched.
[tool_use Bash] {"command": "sed -n 1505,1522p tests/test_tenacity.py && echo ---- && sed -n 1549,1570p tests/test_tenacity.py && echo ---- && sed -n 160,185p tests/test_asyncio.py", "description": "Read existing enabled=False test style"}
[tool_result] class TestEnabled:
    def test_enabled_false_skips_retry(self) -> None:
        """When enabled=False, the function is called directly without retrying."""
        call_count = 0

        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            always_fails()
        assert call_count == 1

    d
…[1071 chars elided]…
        @retry(enabled=False, stop=stop_after_attempt(3))
        async def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            await always_fails()
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
class TestTrio(unittest.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)

        @retry
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py", "old_string": "        assert fails_twice() is True\n        assert call_count == 3\n\n\nclass TestRetryWith:", "new_string": "        assert fails_twice() is True\n        assert call_count == 3\n\n    def test_enabled_false_ite
…[448 chars elided]…
n        assert call_count == 1\n\n    def test_enabled_false_iterator_success(self) -> None:\n        \"\"\"When enabled=False, a successful body under the iterator pattern is not repeated.\"\"\"\n        call_count = 0\n\n        for attempt in tenacity.Retrying(enabled=False):\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n\nclass TestRetryWith:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")", "new_string": "        with py
…[274 chars elided]…
ly once.\"\"\"\n        call_count = 0\n\n        with pytest.raises(ValueError, match=\"fail\"):\n            async for attempt in AsyncRetrying(enabled=False, stop=stop_after_attempt(3)):\n                with attempt:\n                    call_count += 1\n                    raise ValueError(\"fail\")\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"AsyncRetrying\\|^from\\|^import\" tests/test_asyncio.py | head -20; <work>/env-tenacity/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/repro_enabled.py').read())\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Rerun repro and full test suite"}
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
34:    AsyncRetrying,
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
94:        retrying = AsyncRetrying()
107:        repr(tasyncio.AsyncRetrying())
120:        retryi
…[86 chars elided]…
stop=stop_after_attempt(3)):
211:        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
226:        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
sync: ValueError calls= 1
async: ValueError calls= 1
.............s...................................................................................................................... [ 80%]
................................                                         [100%]
163 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] The repro now shows one call and the original `ValueError`, and the full suite passes (163 passed, 1 skipped). I'll check formatting and lint on the touched files, since one new test line is long.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; ($PY/ruff --version && $PY/ruff format --check tenacity tests; $PY/ruff check tenacity tests) 2>&1 | tail -20; ($PY/mypy --version >/dev/null 2>&1 && $PY/mypy tenacity 2>&1 | tail -3) ; rm -f /tmp/repro_enabled.py; git status --short", "description": "Run ruff format/check and mypy on changed code"}
[tool_result] (eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
[assistant] Ruff isn't installed in the project env, so I'll wrap the one long line by hand to match the 88-column style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py", "old_string": "            async for attempt in AsyncRetrying(enabled=False, stop=stop_after_attempt(3)):", "new_string": "            retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n            async for attempt in retrying:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164154-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Rerun test suite and show diff stats"}
[tool_result] .............s...................................................................................................................... [ 80%]
................................                                         [100%]
163 passed, 1 skipped, 12 subtests passed in 1.85s
 tenacity/__init__.py         | 10 +++++++++-
 tenacity/asyncio/__init__.py |  7 +++++++
 tests/test_asyncio.py        | 13 +++++++++++++
 tests/test_tenacity.py       | 21 +++++++++++++++++++++
 4 files changed, 50 insertions(+), 1 deletion(-)
[assistant] `Retrying(enabled=False)` and `AsyncRetrying(enabled=False)` now run the body exactly once under the iterator pattern, and the original exception propagates unchanged. The full test suite passes (163 passed, 1 skipped).

**Cause:** `enabled` was checked in `wraps()` and `__call__`, but not in the iterator paths (`BaseRetrying.__iter__` and `AsyncRetrying.__anext__`). Those kept retrying, so the body ran 3 times and then raised `RetryError`.

**Fix:**
- `tenacity/__init__.py`: when disabled, `__iter__` yields a single `AttemptManager` and returns. `AttemptManager` takes an `enabled` flag, and w
…[152 chars elided]…
ttemptManager` and then raises `StopAsyncIteration`, using a one-shot flag reset in `__aiter__`.

**Tests:** I added two sync tests (failing body runs once and propagates `ValueError`; passing body runs once) and one async test. These are new tests only; no existing test was edited. I reproduced the bug before the change (3 calls, `RetryError`) and confirmed the fix (1 call, `ValueError`).

Ruff is not installed in the project's test environment, so I did not run the formatter or linter. I wrapped the one long line by hand. mypy was not run either.

The changes are uncommitted in the worktree.
