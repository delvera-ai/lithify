# trajectory base-1

final message:
`enabled` is now on `Retrying`, `AsyncRetrying`, `@retry`, and `TornadoRetrying`, which `@retry` uses for Tornado coroutines. With `enabled=False` the function runs once and its exception propagates unchanged, with no sleep. The project's test command passes: 152 passed, 1 skipped (baseline was 139 passed, 1 skipped). I haven't committed anything.

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` on `BaseRetrying.__init__`, forwarded through `copy()` so `retry_with(enabled=...)` works, and added to both `retry()` overloads. `Retrying.__call__` returns `fn(*args, **kwargs)` straight away when disabled.
- `tenacity/asyncio/__init__.py`: same parameter on `AsyncRetrying`. Its `__call__` awaits the function when it is a coroutine.
- `tenacity/tornadoweb.py`: the disabled path yields the function's result once and returns it.
- Tests: 13 new ones across `test_tenacity.py`, `test_asyncio.py` and `test_tornado.py`, covering disabled exception identity, return values, args, no sleep, `retry_with` re-enabling, and the Tornado path.
- `releasenotes/notes/add-enabled-parameter-b31bf138e22b9cc6.yaml`: a reno note, following the repo's convention.

**Choices I made**
- The bypass sits in `__call__`, not in `wraps()`. Every decorated call already goes through `copy()(...)`, so one check covers the decorator.
- Iterator and `async with` usage (`for attempt in Retrying(...)`) is unchanged by `enabled`. The request only covered the decorated function, so I left it alone. Say if you want it to bypass too.
- With `enabled=False`, `wrapped.statistics` is not updated, since no retry bookkeeping runs.

**Not verified:** ruff and mypy are not installed in the project's test environment, so I couldn't run the lint or strict type checks. I wrote the `type: ignore` comments by reading the code, so mypy is the first thing to run.

## events
[assistant] I'll start by reading the retry core and the decorator wiring.
[tool_use Bash] {"command": "git status --short && ls && wc -l tenacity/*.py && grep -n \"def retry\\|class Retrying\\|class AsyncRetrying\\|def __init__\\|def wraps\\|def __call__\\|def copy\\|def __iter__\\|def __aiter__\\|def iter\\|def call\\|def __getstate__\\|retry_base\\|def _wrapped\" tenacity/__init__.py tenacity/asyncio/__init__.py | head -80", "description": "Inspect repo layout and retry entry points"}
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
     789 tenacity/__init__.py
     111 tenacity/_utils.py
       2 tenacity/_version.py
      46 tenacity/after.py
      42 tenacity/before.py
      67 tenacity/before_sleep.py
      43 tenacity/nap.py
     275 tenacity/retry.py
     130 tenacity/stop.py
      62 tenacity/tornadoweb.py
     271 tenacity/wait.py
    1838 total
tenacity/asyncio/__init__.py:74:class AsyncRetrying(BaseRetrying):
tenacity/
…[2017 chars elided]…

tenacity/__init__.py:647:    def __call__(
tenacity/__init__.py:653:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
tenacity/__init__.py:657:def retry(
tenacity/__init__.py:674:def retry(
tenacity/__init__.py:690:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
tenacity/__init__.py:701:        if isinstance(f, retry_base):
tenacity/__init__.py:703:                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
tenacity/__init__.py:758:    "retry_base",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 200, "limit": 600}
[tool_result] 200	
201	    def __enter__(self) -> None:
202	        pass
203	
204	    def __exit__(
205	        self,
206	        exc_type: type[BaseException] | None,
207	        exc_value: BaseException | None,
208	        traceback: t.Optional["types.TracebackType"],
209	    ) -> bool | None:
210	        if exc_type is not None and exc_value is not None:
211	            self.retry_state.set_exception((exc_type, exc_value, traceback))
212	            return True  # Swallow exception.
213	        # We don't 
…[21972 chars elided]…
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py"}
[tool_result] 1	# Copyright 2016 Étienne Bersac
2	# Copyright 2016 Julien Danjou
3	# Copyright 2016 Joshua Harlow
4	# Copyright 2013-2014 Ray Holder
5	#
6	# Licensed under the Apache License, Version 2.0 (the "License");
7	# you may not use this file except in compliance with the License.
8	# You may obtain a copy of the License at
9	#
10	# http://www.apache.org/licenses/LICENSE-2.0
11	#
12	# Unless required by applicable law or agreed to in writing, software
13	# distributed under the License is distributed 
…[7495 chars elided]…
reserve attributes
199	        async_wrapped.retry = self  # type: ignore[attr-defined]
200	        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
201	        async_wrapped.statistics = {}  # type: ignore[attr-defined]
202	
203	        return t.cast("_RetryDecorated[P, R]", async_wrapped)
204	
205	
206	__all__ = [
207	    "AsyncRetrying",
208	    "WrappedFn",
209	    "retry_all",
210	    "retry_any",
211	    "retry_if_exception",
212	    "retry_if_result",
213	]
214	
[assistant] The retry core is clear. Next I'll check the Tornado subclass, the project's own instructions (AGENTS.md and CLAUDE.md), the release-note convention, and whether the test environment exists.
[tool_use Bash] {"command": "cat AGENTS.md; echo ----; cat CLAUDE.md; echo ----; cat tenacity/tornadoweb.py | sed -n 1,62p; echo ----; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | tail -1); echo ----; ls <work>/env-tenacity/bin/python 2>&1; ls tests; grep -rn \"enabled\" doc/ README.rst | head", "description": "Read project guidance, Tornado subclass, release notes, env"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[3455 chars elided]…
l-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
----
<work>/env-tenacity/bin/python
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[assistant] The project's test environment exists, so I can run the real checks. Before editing I want to see whether the docs list retry parameters and how the tests exercise `@retry` and `copy()`.
[tool_use Bash] {"command": "grep -rn \"reraise\" doc README.rst | head; echo ----; grep -n \"def test_copy\\|retry_with\\|def test_retry_function_attributes\\|def test_.*decorator\" tests/*.py | head -20; echo ----; grep -n \"copy(\" tests/test_tenacity.py | head -5; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Check docs, test patterns, and baseline test run"}
[tool_result] doc/source/index.rst:297:is most visible), you can set `reraise=True`.
doc/source/index.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
doc/source/index.rst:592:        retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
README.rst:297:is most visible), you can set `reraise=True`.
README.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
README.rst:592:        retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
----
tests/test_asynci
…[1649 chars elided]…
lf._decorated_fail.retry_with(
----
123:    def test_str_preserved_by_copy(self) -> None:
124:        """copy() preserves the name."""
126:        assert str(r.copy()) == "my_block"
128:    def test_str_overridden_by_copy(self) -> None:
129:        """copy() allows overriding the name."""
........................................................................ [ 94%]
........                                                                 [100%]
139 passed, 1 skipped, 12 subtests passed in 1.84s
[assistant] Baseline is 139 passed, 1 skipped. I'll add the parameter to `BaseRetrying` and `copy()`, then add the bypass to each `__call__` (sync, async, Tornado). Putting it in `__call__` covers the decorator too, because `wraps()` routes every call through `copy()(...)`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any] | None = None,\n        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        
…[547 chars elided]…
= stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":\n        \"\"\"Copy this object with some parameters changed if needed.\"\"\"\n        return self.__class__(\n            sleep=_first_set(sleep, self.
…[1228 chars elided]…
 self.before_sleep),\n            reraise=_first_set(reraise, self.reraise),\n            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),\n            retry_error_callback=_first_set(\n                retry_error_callback, self.retry_error_callback\n            ),\n            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(re
…[182 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:         kwargs: t.Any,
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        while True:
            do = self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                try:
                    result = fn(*args, **kwargs)</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] The `Retrying.__call__` match failed because its signature is `**kwargs`, not `kwargs`. I'll anchor on the unique return-annotation line instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async and Tornado `__call__` methods, plus the `enabled` pass-through in `AsyncRetrying.__init__`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1165 chars elided]…
)\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            if _utils.is_coroutine_callable(fn):\n                return await fn(*args, **kwargs)  # type: ignore[no-any-return]\n            return fn(*args, **kwargs)  # type: ignore[no-any-return]\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            raise gen.Return(result)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] The code changes are in. Next I'll add tests, so I need the existing class layout and style in each test file.
[tool_use Bash] {"command": "grep -n \"^class \\|^import\\|^from\\|^def _retryable\\|^    def test_str_overridden\" tests/test_tenacity.py tests/test_asyncio.py tests/test_tornado.py | head -60; sed -n 1,40p tests/test_tornado.py | grep -n \"import\\|class\\|def \" ; sed -n 120,140p tests/test_tenacity.py", "description": "List test classes, imports, and a sample test"}
[tool_result] tests/test_tornado.py:15:import unittest
tests/test_tornado.py:16:from collections.abc import Generator
tests/test_tornado.py:17:from typing import Any
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:23:from .test_tenacity import NoIOErrorAfterCount
tests/test_tornado.py:28:def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
tests/test_tor
…[3699 chars elided]…
erridden_by_copy(self) -> None:
        """copy() allows overriding the name."""
        r = Retrying(name="original")
        assert str(r.copy(name="overridden")) == "overridden"

    def test_get_fn_name_decorator(self) -> None:
        """get_fn_name() returns the function's qualified name when used as decorator."""
        captured: list[RetryCallState] = []

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(1),
            after=lambda rs: captured.append(rs),
        )
[assistant] I'll put the sync tests in a new class next to `TestRetryingName`, and the async tests in a new class in `test_asyncio.py`. First I'll check how the Tornado test class is structured.
[tool_use Bash] {"command": "sed -n 24,75p tests/test_tornado.py; echo ----; sed -n 178,200p tests/test_asyncio.py; echo ----; tail -5 tests/test_asyncio.py", "description": "Read Tornado and asyncio test style samples"}
[tool_result] @retry
@gen.coroutine
def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()


@retry(stop=stop_after_attempt(2))
@gen.coroutine
def _retryable_coroutine_with_2_attempts(
    thing: NoIOErrorAfterCount,
) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()


class TestTornado(testing.AsyncTestCase):
    @testing.gen_test
    def test_retry(self) -> Generator[Any, Any, None]:
        assert gen.is_corout
…[1391 chars elided]…
   except RetryError:
            pass

        assert attempts == 3

    @asynctest
    async def test_async_with_attempt_manager(self) -> None:
        """AttemptManager supports async with for use inside async for."""
        attempts = 0
        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
        try:
            async for attempt in retrying:
                async with attempt:
----
        assert mock_sleep.await_count == 2


if __name__ == "__main__":
    unittest.main()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "class TestStopConditions(unittest.TestCase):", "new_string": "class TestEnabled(unittest.TestCase):\n    def test_enabled_defaults_to_true(self) -> None:\n        assert Retrying().enabled is True\n        assert t
…[1969 chars elided]…
ssert len(calls) == 1\n\n        calls.clear()\n        with pytest.raises(RetryError):\n            fn.retry_with(enabled=True)()\n        assert len(calls) == 3\n\n    def test_copy_overrides_enabled(self) -> None:\n        r = Retrying(enabled=False)\n        assert r.copy().enabled is False\n        assert r.copy(enabled=True).enabled is True\n\n\nclass TestStopConditions(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async tests. `asynctest`, `RetryError`, and `stop_after_attempt` are already imported in that file, so I can append a class before the `__main__` guard.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        assert mock_sleep.await_count == 2\n\n\nif __name__ == \"__main__\":", "new_string": "        assert mock_sleep.await_count == 2\n\n\nclass TestEnabled(unittest.TestCase):\n    @asynctest\n    async def test
…[1861 chars elided]…
fter_attempt(3))\n        async def fn() -> None:\n            calls.append(1)\n            raise CustomError\n\n        with self.assertRaises(CustomError):\n            await fn()\n        assert len(calls) == 1\n\n        calls.clear()\n        with self.assertRaises(RetryError):\n            await fn.retry_with(enabled=True)()\n        assert len(calls) == 3\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Two of the sleep assertions are weak. The default `sleep` argument is bound at definition time, so patching `time.sleep` or `asyncio.sleep` proves nothing. I'll pass an explicit mock as `sleep=` instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        with mock.patch(\"asyncio.sleep\") as mock_sleep:\n            with self.assertRaises(ValueError) as cm:\n                await tasyncio.AsyncRetrying(\n                    enabled=False, stop=stop_after_att
…[102 chars elided]…
\n        mock_sleep.assert_not_called()", "new_string": "        mock_sleep = mock.AsyncMock()\n        with self.assertRaises(ValueError) as cm:\n            await tasyncio.AsyncRetrying(\n                enabled=False, sleep=mock_sleep, stop=stop_after_attempt(5)\n            )(fn)\n\n        assert cm.exception is error\n        assert len(calls) == 1\n        mock_sleep.assert_not_awaited()"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        calls = []\n        error = ValueError(\"boom\")\n\n        def fn() -> None:\n            calls.append(1)\n            raise error\n\n        with mock.patch(\"time.sleep\") as mock_sleep:\n            wit
…[337 chars elided]…
fn() -> None:\n            calls.append(1)\n            raise error\n\n        mock_sleep = mock.Mock()\n        with pytest.raises(ValueError) as exc_info:\n            Retrying(enabled=False, sleep=mock_sleep, stop=tenacity.stop_after_attempt(5))(\n                fn\n            )\n\n        assert exc_info.value is error\n        assert len(calls) == 1\n        mock_sleep.assert_not_called()"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next the Tornado case. `@retry` routes Tornado coroutines to `TornadoRetrying`, so that path needs its own test. I'll check what `NoIOErrorAfterCount.go` raises before I write it.
[tool_use Bash] {"command": "sed -n 839,856p tests/test_tenacity.py", "description": "Check NoIOErrorAfterCount behavior"}
[tool_result]         # plain_callable | retry_base (exercises __ror__ via reflection)
        retry2 = my_retry | tenacity.retry_if_exception_type(Exception)
        self.assertTrue(retry2(retry_state))

    def test_retry_and_with_plain_function(self) -> None:
        """Plain callables can be composed with retry_base via &."""

        def my_retry(retry_state: tenacity.RetryCallState) -> bool:
            return True

        # retry_base & plain_callable (exercises __and__ fallback)
        retry = tenacity.retry_if_result(lambda x: x == 1) & my_retry
        retry_state = make_retry_state(
            1, 1.0, last_result=tenacity.Future.construct(1, 1, False)
        )
        self.assertTrue(retry(retry_state))
[tool_use Bash] {"command": "grep -n -A12 \"^class NoIOErrorAfterCount\" tests/test_tenacity.py", "description": "Show NoIOErrorAfterCount definition"}
[tool_result] 920:class NoIOErrorAfterCount:
921-    """Holds counter state for invoking a method several times in a row."""
922-
923-    def __init__(self, count: int) -> None:
924-        self.counter = 0
925-        self.count = count
926-
927-    def go(self) -> typing.Any:
928-        """Raise an IOError until after count threshold has been crossed.
929-
930-        Then return True.
931-        """
932-        if self.counter < self.count:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "    @testing.gen_test\n    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:", "new_string": "    @testing.gen_test\n    def test_disabled_calls_once(self) -> Generator[Any, Any, None]:\n        @retry
…[47 chars elided]…
      @gen.coroutine\n        def fn(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:\n            yield gen.sleep(0.00001)\n            thing.go()\n\n        thing = NoIOErrorAfterCount(5)\n        with self.assertRaises(IOError):\n            yield fn(thing)\n        assert thing.counter == 1\n\n    @testing.gen_test\n    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with the project command"}
[tool_result]         def fn() -> None:
            calls.append(1)
            raise CustomError
    
        with pytest.raises(CustomError):
>           fn()

tests/test_tenacity.py:248: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/__init__.py:355: in wrapped_f
    return copy(f, *args, **kw)
           ^^^^^^^^^^^^^^^^^^^^
tenacity/__init__.py:492: in __call__
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
…[291 chars elided]…
nacity.py:245: TypeError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_calls_once
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_retry_with_reenables
FAILED tests/test_tenacity.py::TestEnabled::test_disabled_decorator_calls_once
FAILED tests/test_tenacity.py::TestEnabled::test_disabled_decorator_retry_with_reenables
4 failed, 148 passed, 1 skipped, 12 subtests passed in 1.88s
[assistant] The failures are in my test code: `CustomError` takes a required `value` argument. Before changing anything I'll count the occurrences so I only touch my new tests.
[tool_use Bash] {"command": "grep -n \"CustomError\" tests/test_tenacity.py tests/test_asyncio.py | head -30; grep -n -A3 \"^class CustomError\" tests/test_tenacity.py", "description": "Locate CustomError usages in test files"}
[tool_result] tests/test_tenacity.py:233:            raise CustomError
tests/test_tenacity.py:235:        with pytest.raises(CustomError):
tests/test_tenacity.py:245:            raise CustomError
tests/test_tenacity.py:247:        with pytest.raises(CustomError):
tests/test_tenacity.py:1044:class CustomError(Exception):
tests/test_tenacity.py:1062:class NoCustomErrorAfterCount:
tests/test_tenacity.py:1072:        """Raise a CustomError until after count threshold has been crossed.
tests/test_tenacity.py:1078:
…[1600 chars elided]…
nt(5)))
tests/test_tenacity.py:1413:        self.assertTrue(_retryable_default_f(NoCustomErrorAfterCount(5)))
tests/test_tenacity.py:1818:        class CustomError(Exception):
tests/test_tenacity.py:1826:                    raise CustomError("Don't retry!")
tests/test_tenacity.py:1828:        self.assertRaises(CustomError, test)
1044:class CustomError(Exception):
1045-    """This is a custom exception class.
1046-
1047-    Note that For Python 2.x, we don't strictly need to extend BaseException,
[assistant] Lines 233–247 in `test_tenacity.py` are the only `CustomError` uses I added. The asyncio file may not import it at all. I'll switch my decorator tests to a builtin `ValueError` in both files, which avoids the constructor issue entirely.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        @tenacity.retry(enabled=False, stop=tenacity.stop_after_attempt(5))\n        def fn() -> None:\n            calls.append(1)\n            raise CustomError\n\n        with pytest.raises(CustomError):", "new_string": "        @tenacity.retry(enabled=False, stop=tenacity.stop_after_attempt(5))\n        def fn() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        @tenacity.retry(enabled=False, stop=tenacity.stop_after_attempt(3))\n        def fn() -> None:\n            calls.append(1)\n            raise CustomError\n\n        with pytest.raises(CustomError):\n      
…[58 chars elided]…
s.clear()\n        with pytest.raises(RetryError):", "new_string": "        @tenacity.retry(enabled=False, stop=tenacity.stop_after_attempt(3))\n        def fn() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError):\n            fn()\n        assert len(calls) == 1\n\n        calls.clear()\n        with pytest.raises(RetryError):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        @tenacity.retry(enabled=False, stop=stop_after_attempt(5))\n        async def fn() -> None:\n            calls.append(1)\n            raise CustomError\n\n        with self.assertRaises(CustomError):", "new_string": "        @tenacity.retry(enabled=False, stop=stop_after_attempt(5))\n        async def fn() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with self.assertRaises(ValueError):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        @tenacity.retry(enabled=False, stop=stop_after_attempt(3))\n        async def fn() -> None:\n            calls.append(1)\n            raise CustomError\n\n        with self.assertRaises(CustomError):", "new_string": "        @tenacity.retry(enabled=False, stop=stop_after_attempt(3))\n        async def fn() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with self.assertRaises(ValueError):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; for t in ruff mypy; do $PY -m $t --version >/dev/null 2>&1 && echo \"have $t\" || echo \"no $t\"; done; grep -n \"mypy\\|ruff\" pyproject.toml .pre-commit-config.yaml 2>/dev/null | head", "description": "Run tests and check for available linters"}
[tool_result] ...........s...................................................... [ 43%]
.................................................................. [ 86%]
.....................                                                    [100%]
152 passed, 1 skipped, 12 subtests passed in 1.85s
no ruff
no mypy
59:    "ruff",
60:    "mypy",
72:mypy = "mypy"
77:    { cmd = "ruff check --fix ." },
78:    { cmd = "ruff format ." },
83:    { cmd = "ruff check ." },
84:    { cmd = "ruff format --check ." },
90:    { ref = "mypy" },
99:[tool.ruff]
105:[tool.ruff.lint]
[assistant] All 152 pass (139 before, plus 13 new). The project's lint and type-check tools aren't in the test venv, so I'll check whether they're on the PATH and run them if so.
[tool_use Bash] {"command": "(which ruff mypy uv 2>/dev/null; echo \"--\"); (ruff --version && ruff format --check . && ruff check .) 2>&1 | tail -15; (mypy --version && mypy tenacity tests) 2>&1 | tail -15", "description": "Run ruff and mypy if installed on PATH"}
[tool_result] ruff not found
mypy not found
uv not found
--
(eval):1: command not found: ruff
(eval):1: command not found: mypy
[assistant] Neither ruff nor mypy is installed here, so I can't run the project's lint and type checks. I'll check the mypy config to judge whether my `type: ignore` comments are well-formed, and fix the awkward wrapped call in the sync test by hand.
[tool_use Bash] {"command": "sed -n '/\\[tool.mypy\\]/,/^\\[tool.[a-z]*\\]$/p' pyproject.toml | head -30; grep -n \"line-length\" pyproject.toml", "description": "Read mypy and ruff config from pyproject"}
[tool_result] [tool.mypy]
strict = true
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]

[[tool.mypy.overrides]]
module = "tornado.*"
ignore_missing_imports = true

100:line-length = 88
[assistant] Strict mode is on, so a wrong `type: ignore` code would itself be an error. In the async sync-function branch, `fn` is typed as returning an `Awaitable`, so mypy would report `return-value`, not `no-any-return`. I'll correct that code and reformat the long test call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "            return fn(*args, **kwargs)  # type: ignore[no-any-return]", "new_string": "            return fn(*args, **kwargs)  # type: ignore[return-value]"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        with pytest.raises(ValueError) as exc_info:\n            Retrying(enabled=False, sleep=mock_sleep, stop=tenacity.stop_after_attempt(5))(\n                fn\n            )", "new_string": "        with pytest.raises(ValueError) as exc_info:\n            Retrying(\n                enabled=False, sleep=mock_sleep, stop=tenacity.stop_after_attempt(5)\n            )(fn)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163210-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next I'll add a reno release note, following the existing `releasenotes/notes` convention, and re-run the suite.
[tool_use Bash] {"command": "H=$(<work>/env-tenacity/bin/python -c \"import secrets;print(secrets.token_hex(8))\") && cat > releasenotes/notes/add-enabled-parameter-$H.yaml <<'EOF'\n---\nfeatures:\n  - |\n    Add an ``enabled`` parameter (default ``True``) to ``Retrying``,\n    ``AsyncRetryi
…[230 chars elided]…
ment and testing.\nEOF\ncat releasenotes/notes/add-enabled-parameter-$H.yaml; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short; git diff --stat", "description": "Add release note and rerun the project test command"}
[tool_result] ---
features:
  - |
    Add an ``enabled`` parameter (default ``True``) to ``Retrying``,
    ``AsyncRetrying`` and the ``@retry`` decorator. When set to ``False``, the
    decorated function is called directly, exactly once, with no retry logic,
    and any exception it raises propagates unchanged. This is useful during
    development and testing.
.....................                                                    [100%]
152 passed, 1 skipped, 12 subtests passed in 1.82s
 M tenacity/__init
…[63 chars elided]…

 M tests/test_asyncio.py
 M tests/test_tenacity.py
 M tests/test_tornado.py
?? releasenotes/notes/add-enabled-parameter-b31bf138e22b9cc6.yaml
 tenacity/__init__.py         |  9 +++++
 tenacity/asyncio/__init__.py |  7 ++++
 tenacity/tornadoweb.py       |  4 +++
 tests/test_asyncio.py        | 80 +++++++++++++++++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 81 ++++++++++++++++++++++++++++++++++++++++++++
 tests/test_tornado.py        | 13 +++++++
 6 files changed, 194 insertions(+)
[assistant] `enabled` is now on `Retrying`, `AsyncRetrying`, `@retry`, and `TornadoRetrying`, which `@retry` uses for Tornado coroutines. With `enabled=False` the function runs once and its exception propagates unchanged, with no sleep. The project's test command passes: 152 passed, 1 skipped (baseline was 139 passed, 1 skipped). I haven't committed anything.

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` on `BaseRetrying.__init__`, forwarded through `copy()` so `retry_with(enabled=...)` works, and added to both `retry()` overloads. `Retrying.__call__` returns `fn(*args, **kwargs)` str
…[651 chars elided]…
rated call already goes through `copy()(...)`, so one check covers the decorator.
- Iterator and `async with` usage (`for attempt in Retrying(...)`) is unchanged by `enabled`. The request only covered the decorated function, so I left it alone. Say if you want it to bypass too.
- With `enabled=False`, `wrapped.statistics` is not updated, since no retry bookkeeping runs.

**Not verified:** ruff and mypy are not installed in the project's test environment, so I couldn't run the lint or strict type checks. I wrote the `type: ignore` comments by reading the code, so mypy is the first thing to run.
