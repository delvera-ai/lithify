# trajectory base-1

final message:
`AttemptManager` now supports `async with`, so `async with attempt:` works inside `async for` loops and behaves the same as `with attempt:`. The full test suite passes (142 passed, 1 skipped).

**Changes**
- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the sync and async paths share one implementation and cannot drift apart.
- **`tests/test_asyncio.py`**: added four tests in `TestContextManager`. They cover max-attempts retrying, a successful attempt recording a non-failed outcome, exception swallowing with a retry, and `reraise`. All four fail on the original code and pass with the change.
- **`releasenotes/notes/async-attempt-manager-context-3f9c1e2a7b4d5e60.yaml`**: new feature note, in the same format as the existing notes.

**Not run:** mypy and ruff are not installed in the project's test environment, so I did not run them. I also did not commit anything.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -n \"class AttemptManager\" -A60 tenacity/__init__.py | head -120", "description": "Inspect repo and AttemptManager class"}
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
195:class AttemptManager:
196-    """Manage attempt context."""
197-
198-    def __init__(self, retry_state: "RetryCallState"):
199-        self.retry_state = retry_state
200-
201-    def __enter__(self) -> None:
202-        pass
203-
204-    def __exit__(
205-        self,
206-        exc_type: type[BaseException] | None,
207-        exc_value: BaseException | None,
208-        traceback: t.Optional[
…[1617 chars elided]…
: t.Callable[[int | float], None] | object = _unset,
249-        stop: t.Union["StopBaseT", object] = _unset,
250-        wait: t.Union["WaitBaseT", object] = _unset,
251-        retry: retry_base | object = _unset,
252-        before: t.Callable[["RetryCallState"], None] | object = _unset,
253-        after: t.Callable[["RetryCallState"], None] | object = _unset,
254-        before_sleep: t.Callable[["RetryCallState"], None] | None | object = _unset,
255-        reraise: bool | object = _unset,
[tool_use Bash] {"command": "grep -rn \"AttemptManager\\|__aenter__\\|__enter__\\|__aexit__\" --include=*.py --include=*.rst --include=*.md . | grep -v \"^./.git/\"", "description": "Find AttemptManager references and context hooks"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "cat AGENTS.md | head -80; grep -rn \"AttemptManager\\|__aenter__\\|__aexit__\\|__enter__\" tenacity tests doc releasenotes README.rst; ls releasenotes/notes | tail -5", "description": "Search for AttemptManager usages and guidance docs"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[744 chars elided]…
/__init__.py:163:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:171:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:177:                return AttemptManager(retry_state=self._retry_state)
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml; grep -rln \"for attempt in\\|async for attempt\\|with attempt\" tests tenacity doc README.rst; grep -n \"async for attempt\" -B3 -A12 tests/test_asyncio.py | head -60; grep -n \"def test\" tests/test_asyncio.py | tail -5", "description": "Check release note format and existing async tests"}
[tool_result] ---
features:
  - |
    If you're using `Trio <https://trio.readthedocs.io>`__, then
    ``@retry`` now works automatically. It's no longer necessary to
    pass ``sleep=trio.sleep``.
tests/test_asyncio.py
tests/test_tenacity.py
doc/source/index.rst
README.rst
181-        attempts = 0
182-        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
183-        try:
184:            async for attempt in retrying:
185-                with attempt:
186-                    attempts += 1
187-
…[1442 chars elided]…
1
235-                attempt.retry_state.set_result(attempts)
236-            return attempts
237-
238-        result = await test()
239-
240-        self.assertEqual(3, result)
241-
242-    @asynctest
381:    async def test_retry_with_async_result_rand(self) -> None:
382:        async def test() -> int:
404:    async def test_async_retying_iterator(self) -> None:
414:    async def test_retry_function_attributes(self) -> None:
483:    async def test_sync_function_with_async_sleep(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "old_string": "    def __enter__(self) -> None:\n        pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.Trace
…[852 chars elided]…
ry_state.set_result(None)\n        return None\n\n    async def __aenter__(self) -> None:\n        return self.__enter__()\n\n    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.TracebackType\"],\n    ) -> bool | None:\n        return self.__exit__(exc_type, exc_value, traceback)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll add tests next to the existing async tests and a release note, following the existing style.
[tool_use Bash] {"command": "sed -n 170,195p tests/test_asyncio.py && sed -n 400,415p tests/test_asyncio.py && sed -n 1,30p tests/test_asyncio.py | grep -n import", "description": "Read test context for insertion point"}
[tool_result]             await trio.sleep(0.00001)
            return thing.go()

        trio.run(trio_function)

        assert thing.counter == thing.count


class TestContextManager(unittest.TestCase):
    @asynctest
    async def test_do_max_attempts(self) -> None:
        attempts = 0
        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
        try:
            async for attempt in retrying:
                with attempt:
                    attempts += 1
                    raise Excep
…[426 chars elided]…
th attempts:
                    await _async_function(thing)


class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:\n        class CustomError(Exception):\n            pass\n\n        try:\n            async for attempt in tasyncio.AsyncRetr
…[1988 chars elided]…
 test_reraise(self) -> None:\n        class CustomError(Exception):\n            pass\n\n        try:\n            async for attempt in tasyncio.AsyncRetrying(\n                stop=stop_after_attempt(1), reraise=True\n            ):\n                with attempt:\n                    raise CustomError()\n        except CustomError:\n            pass\n        else:\n            raise Exception\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] I left a tautological assertion in `test_async_with_success_sets_result`. Fixing it so the test checks the outcome inside the loop instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "    async def test_async_with_success_sets_result(self) -> None:\n        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))\n        async for attempt in retrying:\n            async with attempt:\n     
…[131 chars elided]…
 None\n        assert not attempt.retry_state.outcome.failed", "new_string": "    async def test_async_with_success_sets_result(self) -> None:\n        async for attempt in tasyncio.AsyncRetrying(stop=stop_after_attempt(3)):\n            async with attempt:\n                pass\n            assert attempt.retry_state.outcome is not None\n            assert not attempt.retry_state.outcome.failed"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/async-attempt-manager-context-3f9c1e2a7b4d5e60.yaml <<'EOF'\n---\nfeatures:\n  - |\n    The object yielded by ``AsyncRetrying`` iteration now supports the async\n    context manager protocol, so ``async with attempt:`` can be used inside\n    ``async for attempt in AsyncRetrying(...)`` loops. It behaves exactly like\n    ``with attempt:``.\nEOF\nls /private/tm
…[29 chars elided]…
oding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Add release note and run the project test suite"}
[tool_result] <work>/env-tenacity/bin/python
...........s........................................................................................................................ [ 92%]
...........                                                              [100%]
142 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] The full suite passes. I'll confirm the new tests ran and check that they fail without the change.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_asyncio.py -k async_with -v 2>&1 | tail -8; git stash list >/dev/null; cp tenacity/__init__.py /tmp/init_new.py && git show HEAD:tenacity/__init__.py > tenacity/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_asyncio.py -k async_with 2>&1 | tail -3; cp /tmp/init_new.py tenacity/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; rm -f /tmp/init_new.py; git status --short", "description": "Run new tests verbose, check they fail on old code, restore"}
[tool_result] rootdir: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163124-feature-attemptmanager-the-objec/base-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collected 26 items / 22 deselected / 4 selected

tests/test_asyncio.py ....                                               [100%]

======================= 4 passed, 22 deselected in 0.02s =======================
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_swallows_exception_and_retries
FAILED tests/test_asyncio.py::TestContextManager::test_do_max_attempts_async_with
4 failed, 22 deselected in 0.03s
142 passed, 1 skipped, 12 subtests passed in 1.83s
 M tenacity/__init__.py
 M tests/test_asyncio.py
?? releasenotes/notes/async-attempt-manager-context-3f9c1e2a7b4d5e60.yaml
[assistant] The four new tests fail on the old code and pass with the change. I'll run the linters the project configures.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ($PY -m mypy tenacity 2>&1 | tail -3) ; ($PY -m ruff check tenacity tests 2>&1 | tail -3); ($PY -m ruff format --check tenacity tests 2>&1 | tail -2)", "description": "Run mypy and ruff if available"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[assistant] `AttemptManager` now supports `async with`, so `async with attempt:` works inside `async for` loops and behaves the same as `with attempt:`. The full test suite passes (142 passed, 1 skipped).

**Changes**
- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the sync and async paths share one implementation and cannot drift apart.
- **`tests/test_asyncio.py`**: added four tests in `TestContextManager`. They cover max-attempts retrying, a successful attempt recording a non-failed outcome, exception swallowing with a retry, and `reraise`. All four fail on the original code and pass with the change.
- **`releasenotes/notes/async-attempt-manager-context-3f9c1e2a7b4d5e60.yaml`**: new feature note, in the same format as the existing notes.

**Not run:** mypy and ruff are not installed in the project's test environment, so I did not run them. I also did not commit anything.
