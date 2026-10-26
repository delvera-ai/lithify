# trajectory base-1

final message:
`enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`, and the full suite passes: 149 passed, 1 skipped (the baseline was 139 passed, 1 skipped, plus 10 new tests). I didn't commit anything.

With `enabled=False`, the wrapped function runs once and any exception propagates unchanged, with no sleep and no `RetryError`. The default stays `True`, so existing callers are unaffected.

**What changed**
- `tenacity/__init__.py`: `BaseRetrying` takes `enabled` as its last parameter, and `Retrying.__call__` returns `fn(*args, **kwargs)` directly when it is off. `copy()` carries the flag, so `wraps()` and `retry_with()` keep it. The `retry()` overloads accept it.
- `tenacity/asyncio/__init__.py`: same behaviour in `AsyncRetrying.__call__`, awaiting the function when it is a coroutine function.
- `tenacity/tornadoweb.py`: `TornadoRetrying` already inherited the parameter, but it would have ignored the flag, so I gave it the same early path. You didn't ask for this; drop it if you'd rather keep tornado out of scope.
- Tests in `tests/test_tenacity.py`, `tests/test_asyncio.py` and `tests/test_tornado.py` cover the disabled path, the default, `retry_with` keeping the flag, and re-enabling.
- A release note in `releasenotes/notes/enabled-parameter-3f1c9a7e2b5d8064.yaml`.

**Decisions to check**
- The iterator API (`for attempt in Retrying(...)` / `async for`) does not honour `enabled`. The spec only covers the called-function path, and making it honour the flag would mean changing how `AttemptManager` swallows exceptions. Say if you want that covered too.
- I didn't add docs to `doc/source/index.rst` or `README.rst`; the release note is the only user-facing text.

**Not verified:** ruff and mypy are not installed in the project's test environment, so I couldn't run the strict mypy config or the formatter. I checked line lengths by hand and corrected one type-ignore code by reasoning. Please run the project's lint and type checks before merging.

## events
[assistant] I'll start by reading the retry code and its tests.
[tool_use Bash] {"command": "git status --short && ls && ls tenacity tests && wc -l tenacity/*.py && grep -n \"def retry\\|class Retrying\\|class AsyncRetrying\\|def __init__\\|def wraps\\|def __call__\\|def iter\\|def __iter__\\|def __aiter__\\|def call\\|def __aenter__\\|def __enter__\" tenacity/*.py", "description": "Inspect repo layout and retry entry points"}
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
tenacity:
__init__.py
_utils.py
_version.py
after.py
asyncio
before.py
before_sleep.py
nap.py
py.typed
retry.py
stop.py
tornadoweb.py
wait.py

tests:
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
     789 tenacity/__init__.py
     111 tenacity/_utils.py
       2 tenacity/_version.py
      46 tenacity/after.py
      42 tenacity/before.py
    
…[5855 chars elided]…
f, retry_state: "RetryCallState") -> float:
tenacity/wait.py:160:    def __init__(
tenacity/wait.py:170:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:188:    def __init__(
tenacity/wait.py:200:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:235:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:252:    def __init__(
tenacity/wait.py:264:    def __call__(self, retry_state: "RetryCallState") -> float:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 220, "limit": 580}
[tool_result] 220	    async def __aexit__(
221	        self,
222	        exc_type: type[BaseException] | None,
223	        exc_value: BaseException | None,
224	        traceback: t.Optional["types.TracebackType"],
225	    ) -> bool | None:
226	        return self.__exit__(exc_type, exc_value, traceback)
227	
228	
229	class BaseRetrying(ABC):
230	    def __init__(
231	        self,
232	        sleep: t.Callable[[int | float], None] = sleep,
233	        stop: "StopBaseT" = stop_never,
234	        wait: "WaitBas
…[21304 chars elided]…
ep_using_event",
771	    "stop_after_attempt",
772	    "stop_after_delay",
773	    "stop_all",
774	    "stop_any",
775	    "stop_before_delay",
776	    "stop_never",
777	    "stop_when_event_set",
778	    "wait_chain",
779	    "wait_combine",
780	    "wait_exception",
781	    "wait_exponential",
782	    "wait_exponential_jitter",
783	    "wait_fixed",
784	    "wait_full_jitter",
785	    "wait_incrementing",
786	    "wait_none",
787	    "wait_random",
788	    "wait_random_exponential",
789	]
790	
[tool_use Bash] {"command": "cat AGENTS.md && ls releasenotes/notes | tail -5 && grep -rn \"enabled\" tenacity tests doc README.rst | head -20", "description": "Read project guidance and search for existing enabled references"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[77 chars elided]…
ject memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The core logic is in `BaseRetrying`, `Retrying.__call__`, and `retry()`. Next I'll read the async and tornado subclasses, plus a sample release note.
[tool_use Bash] {"command": "ls tenacity/asyncio && cat tenacity/asyncio/__init__.py && cat tenacity/tornadoweb.py && cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml && git log -3 --format=%H%n%s -- releasenotes | head", "description": "Read async and tornado retry subclasses"}
[tool_result] __init__.py
retry.py
# Copyright 2016 Étienne Bersac
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS
…[9242 chars elided]…
epare_for_next_attempt()
                yield self.sleep(do)
            else:
                raise gen.Return(do)
---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
d4e868d6b8368c00b5a1fad54de36c2c8c3a0fb3
Fix `retry()` annotations with async `sleep=` function (#555)
24415ebbca6ecafdf870af06441656dd96149d1d
support async sleep for sync fn (#551)
3bf33b44096077a0608855f6a380fd8a25fa6f26
chore: drop Python 3.9 support (EOL) (#552)
[assistant] I have the full picture of the call paths. Before editing, I'll check the docs that list retry parameters, whether the project's test interpreter exists, and how the tests are written.
[tool_use Bash] {"command": "grep -rn \"reraise\" doc README.rst | head; ls <work>/env-tenacity/bin/python && grep -n \"^def test_\\|^async def test_\" tests/test_tenacity.py | head -5 && grep -n \"reraise\" tests/test_tenacity.py | head -5 && grep -n \"tornado\" tests/test_tornado.py | head -3; sed -n 1,30p tests/test_asyncio.py | grep -n import", "description": "Find docs, check test interpreter, and sample test style"}
[tool_result] doc/source/index.rst:297:is most visible), you can set `reraise=True`.
doc/source/index.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
doc/source/index.rst:592:        retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
README.rst:297:is most visible), you can set `reraise=True`.
README.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
README.rst:592:        retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
/private/tmp/claude-50
…[251 chars elided]…
e_by_default(self) -> None:
1606:            reraise=True,
1608:        def _reraised_by_default() -> None:
19:from tornado import gen, testing
21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
60:        repr(tornadoweb.TornadoRetrying())
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
[assistant] The project's interpreter is present. I'll record the baseline test result before changing anything.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run baseline test suite"}
[tool_result] ...........s................................................ [ 42%]
........................................................................ [ 94%]
........                                                                 [100%]
139 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] Baseline is green: 139 passed, 1 skipped. Now the edits. I'm adding `enabled` to `BaseRetrying` as the last parameter so existing positional callers are unaffected. `copy()` has to carry it too, because `wraps()` builds the per-call copy through `copy()`, and without that the decorator would silently reset it to `True`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        
…[375 chars elided]…
= stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":\n        \"\"\"Copy this object with some parameters changed if needed.\"\"\"\n        return self.__class__(\n            sleep=_first_set(sleep, self.
…[1228 chars elided]…
 self.before_sleep),\n            reraise=_first_set(reraise, self.reraise),\n            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),\n            retry_error_callback=_first_set(\n                retry_error_callback, self.retry_error_callback\n            ),\n            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    def __call__(\n        self,\n        fn: t.Callable[..., WrappedFnReturnT],\n        *args: t.Any,\n        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallSt
…[396 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    sleep: t.Callable[[int | float], None] = sleep,\n    stop: \"StopBaseT\" = stop_never,\n    wait: \"WaitBaseT\" = wait_none(),\n    retry: \"RetryBaseT | tasyncio.retry.RetryBaseT\" = retry_if_exception_type(),\n
…[927 chars elided]…
 after_nothing,\n    before_sleep: t.Callable[[\"RetryCallState\"], None | t.Awaitable[None]]\n    | None = None,\n    reraise: bool = False,\n    retry_error_cls: type[\"RetryError\"] = RetryError,\n    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, `AsyncRetrying` (constructor plus `__call__`) and `TornadoRetrying`. The tornado class inherits the new argument through `**kwargs`, but its `__call__` would otherwise ignore the flag, so it needs the same early path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1134 chars elided]…
     enabled=enabled,\n        )\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            if _utils.is_coroutine_callable(fn):\n                return await fn(*args, **kwargs)\n            return fn(*args, **kwargs)  # type: ignore[no-any-return]\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "        **kwargs: typing.Any,\n    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "        **kwargs: typing.Any,\n    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            raise gen.Return(result)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Now the release note and tests. I'll check the existing test style first so the new tests match it.
[tool_use Bash] {"command": "sed -n 1595,1625p tests/test_tenacity.py && tail -30 tests/test_tenacity.py && grep -n \"^class \\|^import\\|^from\" tests/test_tenacity.py | head -30 && grep -n \"class \\|async def test\\|@pytest\\|asyncio.run\\|def test_\" tests/test_asyncio.py | head -20 && grep -n \"^class \\|def test_\" tests/test_tornado.py | head", "description": "Inspect test file style and structure"}
[tool_result]     def test_before_sleep_log_returns_with_exc_info(self) -> None:
        self.test_before_sleep_log_returns(exc_info=True)


class TestReraiseExceptions(unittest.TestCase):
    def test_reraise_by_default(self) -> None:
        calls = []

        @retry(
            wait=tenacity.wait_fixed(0.1),
            stop=tenacity.stop_after_attempt(2),
            reraise=True,
        )
        def _reraised_by_default() -> None:
            calls.append("x")
            raise KeyError("Bad key")

 
…[3131 chars elided]…
anager(self) -> None:
209:    async def test_reraise(self) -> None:
210:        class CustomError(Exception):
225:    async def test_sleeps(self) -> None:
239:    async def test_retry_with_result(self) -> None:
240:        async def test() -> int:
42:class TestTornado(testing.AsyncTestCase):
44:    def test_retry(self) -> Generator[Any, Any, None]:
51:    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
59:    def test_repr(self) -> None:
62:    def test_old_tornado(self) -> None:
[assistant] I'll add sync tests to `test_tenacity.py`, and async and tornado tests beside the existing ones. Reading the async and tornado test blocks first so the insertion points match.
[tool_use Bash] {"command": "sed -n 40,70p tests/test_tornado.py && sed -n 79,112p tests/test_asyncio.py", "description": "Read async and tornado test blocks"}
[tool_result] class TestTornado(testing.AsyncTestCase):
    @testing.gen_test
    def test_retry(self) -> Generator[Any, Any, None]:
        assert gen.is_coroutine_function(_retryable_coroutine)
        thing = NoIOErrorAfterCount(5)
        yield _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @testing.gen_test
    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
        assert gen.is_coroutine_function(_retryable_coroutine)
        thing = NoIOErrorAfterCount(2)

…[1220 chars elided]…
unter == thing.count

    @asynctest
    async def test_stop_after_attempt(self) -> None:
        thing = NoIOErrorAfterCount(2)
        try:
            await _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tasyncio.AsyncRetrying())

    def test_retry_attributes(self) -> None:
        assert hasattr(_retryable_coroutine, "retry")
        assert hasattr(_retryable_coroutine, "retry_with")
[assistant] I have what I need for the test placement. I'm adding one class of sync tests, plus async and tornado cases next to their existing neighbours.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_asyncio.py | grep -n \"import\\|tasyncio\" && sed -n 1,20p tests/test_tornado.py | grep -n \"import\"", "description": "Check test module import names"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
32:import tenacity
33:from tenacity import (
15:import unittest
16:from collections.abc import Generator
17:from typing import Any
19:from tornado import gen, testing
[tool_use Bash] {"command": "sed -n 32,50p tests/test_asyncio.py", "description": "Read asyncio test imports block"}
[tool_result] import tenacity
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        assert mock_sleep.call_count == 1\n\n\nif __name__ == \"__main__\":", "new_string": "        assert mock_sleep.call_count == 1\n\n\nclass TestEnabled(unittest.TestCase):\n    def test_retrying_disabled_call
…[1784 chars elided]…
alls = []\n\n        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))\n        def _fail() -> None:\n            calls.append(\"x\")\n            raise KeyError(\"Bad key\")\n\n        reenabled = _fail.retry_with(enabled=True, wait=tenacity.wait_fixed(0))\n        with pytest.raises(RetryError):\n            reenabled()\n        assert len(calls) == 3\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the asyncio test, placed after the existing `test_repr` in `TestAsyncio`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "    def test_repr(self) -> None:\n        repr(tasyncio.AsyncRetrying())\n\n    def test_retry_attributes(self) -> None:", "new_string": "    def test_repr(self) -> None:\n        repr(tasyncio.AsyncRetrying())\n\n 
…[249 chars elided]…
ise KeyError(\"Bad key\")\n\n        with pytest.raises(KeyError):\n            await _fail()\n        assert len(calls) == 1\n\n    @asynctest\n    async def test_disabled_async_retrying_with_sync_fn(self) -> None:\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(5))\n        assert await retrying(lambda x: x * 2, 21) == 42\n\n    def test_retry_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())", "new_string": "    @testing.gen_test\n    def test_disabled_calls_once_and_propagates(self) -> Generator[Any, Any, None]:\n        calls
…[94 chars elided]…
  calls.append(\"x\")\n            yield gen.moment\n            raise KeyError(\"Bad key\")\n\n        retrying = tornadoweb.TornadoRetrying(\n            enabled=False, stop=stop_after_attempt(5)\n        )\n        with self.assertRaises(KeyError):\n            yield retrying(_fail)\n        assert len(calls) == 1\n\n    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[assistant] Next, the release note, using the reno naming pattern the existing notes follow.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/releasenotes/notes/enabled-parameter-3f1c9a7e2b5d8064.yaml", "content": "---\nfeatures:\n  - |\n    Add an ``enabled`` parameter (default ``True``) to ``Retrying``,\n    ``AsyncRetrying`` and the ``@retry`` decorator. When set to ``False`` the\n    wrapped function is called directly, exactly once, with no retry logic, and\n    any exception it raises propagates unchanged. This is useful during\n    development and testing.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/releasenotes/notes/enabled-parameter-3f1c9a7e2b5d8064.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with changes"}
[tool_result] .............s...................................................................................................................... [ 88%]
..................                                                       [100%]
149 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] All 149 pass: the 139 baseline plus 10 new tests, with the same skip. The project may also run linters and type checks, so I'll check its config and run whichever tools the environment has.
[tool_use Bash] {"command": "grep -n \"ruff\\|mypy\\|pre-commit\" pyproject.toml | head; ls -a | grep -i pre-commit; PY=<work>/env-tenacity/bin; ls $PY | grep -i \"ruff\\|mypy\"; $PY/ruff format --check tenacity tests 2>&1 | tail -3; $PY/ruff check tenacity tests 2>&1 | tail -3; $PY/mypy tenacity 2>&1 | tail -3", "description": "Run linters and type checker if available"}
[tool_result] 59:    "ruff",
60:    "mypy",
72:mypy = "mypy"
77:    { cmd = "ruff check --fix ." },
78:    { cmd = "ruff format ." },
83:    { cmd = "ruff check ." },
84:    { cmd = "ruff format --check ." },
90:    { ref = "mypy" },
99:[tool.ruff]
105:[tool.ruff.lint]
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
[assistant] Ruff and mypy aren't installed in the project's test environment. I'll check whether the interpreter can run them as modules before deciding how to verify.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m ruff --version 2>&1 | tail -1; $PY -m mypy --version 2>&1 | tail -1; which ruff mypy uvx 2>/dev/null", "description": "Check whether ruff or mypy are runnable"}
[tool_result ERROR] Exit code 1
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
ruff not found
mypy not found
uvx not found
[assistant] Neither tool is installed, and I won't add packages to the shared test environment just for a lint pass. Instead I'll check the diff by hand for the one thing ruff would most likely flag here, lines over the 88-column default, and review the final diff.
[tool_use Bash] {"command": "git diff -U0 | grep '^+' | awk 'length($0) > 89 {print length($0)\": \"$0}'; git status --short; git diff --stat", "description": "Check added lines for length and review diff stat"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 M tests/test_tornado.py
?? releasenotes/notes/enabled-parameter-3f1c9a7e2b5d8064.yaml
 tenacity/__init__.py         |  9 ++++++
 tenacity/asyncio/__init__.py |  7 +++++
 tenacity/tornadoweb.py       |  4 +++
 tests/test_asyncio.py        | 18 ++++++++++++
 tests/test_tenacity.py       | 68 ++++++++++++++++++++++++++++++++++++++++++++
 tests/test_tornado.py        | 17 +++++++++++
 6 files changed, 123 insertions(+)
[assistant] No lines exceed the limit. Reviewing the diff, one line needs a second look: the sync fallback in `AsyncRetrying.__call__` returns `fn(...)` typed as an awaitable, so the `no-any-return` ignore I wrote is the wrong code. Mypy would report that as `return-value`. I'll correct it and check the mypy settings to see whether unused-ignore warnings are on.
[tool_use Bash] {"command": "grep -n -A12 \"tool.mypy\" pyproject.toml | head -30", "description": "Read mypy configuration"}
[tool_result] 117:[tool.mypy]
118-strict = true
119-files = ["tenacity", "tests"]
120-show_error_codes = true
121-exclude = ["tenacity/_version\\.py"]
122-
123:[[tool.mypy.overrides]]
124-module = "tornado.*"
125-ignore_missing_imports = true
126-
[assistant] The config is `strict = true`, which turns on unused-ignore warnings, so a wrong code is a failure either way. The error for returning an awaitable where `WrappedFnReturnT` is expected is `return-value`, so I'll use that code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "            return fn(*args, **kwargs)  # type: ignore[no-any-return]", "new_string": "            return fn(*args, **kwargs)  # type: ignore[return-value]"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155426-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Rerun full test suite after type-ignore fix"}
[tool_result] ..................                                                       [100%]
149 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] `enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`, and the full suite passes: 149 passed, 1 skipped (the baseline was 139 passed, 1 skipped, plus 10 new tests). I didn't commit anything.

With `enabled=False`, the wrapped function runs once and any exception propagates unchanged, with no sleep and no `RetryError`. The default stays `True`, so existing callers are unaffected.

**What changed**
- `tenacity/__init__.py`: `BaseRetrying` takes `enabled` as its last parameter, and `Retrying.__call__` returns `fn(*args, **kwargs)` directly when it is off. `copy()` carries the flag, s
…[776 chars elided]…
r`) does not honour `enabled`. The spec only covers the called-function path, and making it honour the flag would mean changing how `AttemptManager` swallows exceptions. Say if you want that covered too.
- I didn't add docs to `doc/source/index.rst` or `README.rst`; the release note is the only user-facing text.

**Not verified:** ruff and mypy are not installed in the project's test environment, so I couldn't run the strict mypy config or the formatter. I checked line lengths by hand and corrected one type-ignore code by reasoning. Please run the project's lint and type checks before merging.
