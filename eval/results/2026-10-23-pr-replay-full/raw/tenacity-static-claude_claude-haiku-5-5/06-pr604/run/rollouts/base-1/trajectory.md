# trajectory base-1

final message:
I added `enabled` (default `True`) to `BaseRetrying`, so it works on `Retrying`, `AsyncRetrying` and `@retry`. With `enabled=False` the function is called once, with no retry logic, and its exception propagates unchanged. The full suite passes: 147 passed, 1 skipped, exit 0. I did not commit anything.

**Changes**
- `tenacity/__init__.py`: `enabled` is stored on `BaseRetrying`, carried through `copy()` (so `retry_with(enabled=False)` works), and `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `retry()` typed overloads gained the parameter.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying` accepts and passes `enabled`. Its `__call__` awaits `fn` once when disabled, handling sync or async `fn`.
- `tenacity/tornadoweb.py`: `TornadoRetrying` got the same bypass. I did this because the parameter now lives on the base class, and without it `enabled=False` would be silently ignored there. This goes slightly beyond the three classes you named.
- Tests: `TestEnabled` in `tests/test_tenacity.py` (sync, including `retry_with`, plus a guard that the default still retries) and `TestEnabled` in `tests/test_asyncio.py` (async).
- Docs: a "Disabling retries" section in `doc/source/index.rst`. I ran its example and it works.
- Reno note: `releasenotes/notes/enabled-parameter-d829b79fb5fefe6f.yaml`, a `features:` entry.

**Verification**
- Red: before the fix, the new tests ran alone and seven failed with `TypeError: ... unexpected keyword argument 'enabled'`. That is the missing feature, not an import or typo error. The default-behaviour guard passed, as intended.
- Green: the new tests pass alone (8 passed).
- Full suite: `run_tests.py` exit 0, 147 passed, 1 skipped. I did not check which test is skipped.
- `check_changed.py`: exit 0, PASS with 0 problems.
- ruff and mypy were not run (unavailable in this environment).

**Decisions and gaps**
- Iteration (`for attempt in Retrying(enabled=False)` and `async for`) still retries. The request only covered the decorated call, so I left it alone. Say if you want it to yield a single attempt.
- With `enabled=False` the decorated function's `statistics` stay empty, because `begin()` is skipped.

## events
[assistant] I'll start by reading the change-contract skill, the harness scripts, and the core retry code.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; cat .lithify/harness/scripts/run_tests.py | head -80; echo ---; cat .lithify/harness/scripts/check_changed.py | head -60; echo ---; ls tenacity reno 2>/dev/null; ls releasenotes/notes 2>/dev/null | tail -5; git status --short | head", "description": "Read skill, harness scripts, and repo layout"}
[tool_use Bash] {"command": "cat tenacity/__init__.py | head -400", "description": "Read the core tenacity module"}
[tool_result] # Copyright 2016-2018 Julien Danjou
# Copyright 2017 Elisey Zanko
# Copyright 2016 Étienne Bersac
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
# distributed under the License is distrib
…[12095 chars elided]…
er_state.stop_run_result = self.stop(retry_state)

    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = action(retry_state)
        return result

    def _begin_iter(self, retry_state: "RetryCallState") -> None:
        self.iter_state.reset()

        fut = retry_state.outcome
        if fut is None:
            if self.before is not None:
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version) — i.e. any edit under tenacity/ that a user of the library could notice. Lists the files such a change must touch besides the code (reno note, test, user docs in doc/s
…[11102 chars elided]…
ef added_lines(path: str, untracked: bool) -> set[int]:
    """1-based line numbers added/changed in the working tree."""
---
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
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "cat tenacity/asyncio/__init__.py | head -150; echo ---; cat .lithify/harness/memory.md 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -20", "description": "Read async retry module and memory notes"}
[tool_result] # Copyright 2016 Étienne Bersac
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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT
…[4517 chars elided]…
f.wait:
            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)
        else:
            sleep = 0.0

        retry_state.upcoming_sleep = sleep

    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
---
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[assistant] The core loop and decorator are the parts that matter. Next I'll read the sync `__call__`, the `retry()` decorator, and the async `wraps`/`__call__` surfaces.
[tool_use Bash] {"command": "grep -n \"def \\|class \\|enabled\" tenacity/__init__.py | sed -n '1,200p'; echo ---; sed -n 400,520p tenacity/__init__.py", "description": "Locate functions and read the sync call path"}
[tool_result] 112:class IterState:
120:    def reset(self) -> None:
127:class TryAgain(Exception):
134:class DoAttempt:
138:class DoSleep(float):
142:class BaseAction:
143:    """Base class for representing actions to take by retry object.
147:    - REPR_FIELDS: class variable specifying attributes to include in repr(self)
154:    def __repr__(self) -> str:
160:    def __str__(self) -> str:
164:class RetryAction(BaseAction):
168:    def __init__(self, sleep: t.SupportsFloat) -> None:
175:def _first_set(first:
…[6451 chars elided]…
Future(futures.Future[t.Any]):
    """Encapsulates a (future or past) attempted call to a target function."""

    def __init__(self, attempt_number: int) -> None:
        super().__init__()
        self.attempt_number = attempt_number

    @property
    def failed(self) -> bool:
        """Return whether a exception is being held in this future."""
        return self.exception() is not None

    @classmethod
    def construct(
        cls, attempt_number: int, value: t.Any, has_exception: bool
[tool_use Bash] {"command": "sed -n 150,260p tenacity/asyncio/__init__.py; echo ---; grep -n \"def \\|class \" tenacity/tornadoweb.py | head -30", "description": "Read async call path and tornado overrides"}
[tool_result]     async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
            retry_state
        )

    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
 
…[1674 chars elided]…
= self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
        async_wrapped.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
    "AsyncRetrying",
    "WrappedFn",
    "retry_all",
    "retry_any",
    "retry_if_exception",
    "retry_if_result",
]
---
28:class TornadoRetrying(BaseRetrying):
31:    def __init__(
40:    def __call__(  # type: ignore[override]
[tool_use Bash] {"command": "sed -n 640,720p tenacity/__init__.py; echo ---; sed -n 20,70p tenacity/tornadoweb.py; echo ---; sed -n 1,40p tests/test_tenacity.py | grep -n \"import\" ; grep -n \"^class \\|^from\\|^import\" tests/test_asyncio.py | head -20; echo ---; grep -n \"retry_with\\|def test_retry_with\\|\\\"copy\\\"\\|copy(\" tests/test_tenacity.py | head", "description": "Read retry() decorator, tornado, and test layout"}
[tool_result]         self, fn: t.Callable[P, t.Coroutine[t.Any, t.Any, R]]
    ) -> "_RetryDecorated[P, t.Coroutine[t.Any, t.Any, R]]": ...
    @t.overload
    def __call__(
        self, fn: t.Callable[P, t.Awaitable[R]]
    ) -> "_RetryDecorated[P, t.Awaitable[R]]": ...
    @t.overload
    def __call__(
        self, fn: t.Callable[P, R]
    ) -> "_RetryDecorated[P, t.Awaitable[R]]": ...


@t.overload
def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...


@t.overload
def retry(
    *,
    sleep:
…[5234 chars elided]…
 == "my_block"
128:    def test_str_overridden_by_copy(self) -> None:
129:        """copy() allows overriding the name."""
131:        assert str(r.copy(name="overridden")) == "overridden"
1411:        result = _retryable_test_with_wait.retry_with(wait=tenacity.wait_fixed(0.1))(
1419:        result = _retryable_test_with_stop.retry_with(
1430:            _retryable.retry_with(stop=tenacity.stop_after_attempt(2))()
1442:        result = _retryable.retry_with(stop=tenacity.stop_after_attempt(5))()
[assistant] I have the call paths. Before writing code, I need the test-file layout, the docs section for usage examples, and the project Python path from memory.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; ls -l $P; grep -n \"^class \" tests/test_tenacity.py | tail -12; echo ---; sed -n 427,445p tests/test_asyncio.py; echo ---; grep -n \"^Retry\\|^[A-Z].*\\n\\|^----\\|^====\\|^\\~\\~\\~\\|^\\^\\^\\^\" doc/source/index.rst | head -80; echo ---; grep -n \"with attempt:\\|retry_with\\|@retry\" doc/source/index.rst | head -20", "description": "Check project python and find test/doc locations"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
1149:class TestDecoratorWrapper(unittest.TestCase):
1391:class TestStatisticsKeys:
1408:class TestRetryWith:
1446:class TestBeforeAfterAttempts(unittest.TestCase):
1599:class TestReraiseExceptions(unittest.TestC
…[5220 chars elided]…
 in range(3)] +
226:    @retry(retry=retry_if_exception_type(IOError))
231:    @retry(retry=retry_if_not_exception_type(ClientError))
244:    @retry(retry=retry_if_result(is_none_p))
271:    @retry(retry=(retry_if_result(is_none_p) | retry_if_exception_type()))
283:   @retry
301:    @retry(reraise=True, stop=stop_after_attempt(3))
326:    @retry(stop=stop_after_attempt(3), before=before_log(logger, logging.DEBUG))
341:    @retry(stop=stop_after_attempt(3), after=after_log(logger, logging.DEBUG))
[assistant] Plan: `enabled` lives on `BaseRetrying` so `copy()`/`retry_with` carry it, and each call path short-circuits before `begin()`. I'll write the regression tests first, then confirm they fail on the unfixed code.
[tool_use Bash] {"command": "sed -n 1391,1446p tests/test_tenacity.py; echo ---; sed -n 40,80p tests/test_asyncio.py", "description": "Read existing test style for statistics and retry_with"}
[tool_result] class TestStatisticsKeys:
    def test_delay_since_first_attempt_available_on_first_attempt(self) -> None:
        """delay_since_first_attempt should be in statistics from the start."""

        @retry(
            stop=tenacity.stop_after_attempt(3),
            retry=tenacity.retry_if_result(lambda x: x is None),
        )
        def succeeds_first_try() -> bool:
            assert "delay_since_first_attempt" in succeeds_first_try.statistics
            assert succeeds_first_try.statistics["
…[2306 chars elided]…


    return wrapper


async def _async_function(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry
async def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry(stop=stop_after_attempt(2))
async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


class TestAsyncio(unittest.TestCase):
    @asynctest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "class TestBeforeAfterAttempts(unittest.TestCase):", "new_string": "class TestEnabled:\n    def test_disabled_calls_once_and_propagates_exception(self) -> None:\n        calls: list[int] = []\n\n        def _fails()
…[1388 chars elided]…
    def test_enabled_by_default_still_retries(self) -> None:\n        calls: list[int] = []\n\n        @retry(stop=tenacity.stop_after_attempt(3))\n        def _fails() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(RetryError):\n            _fails()\n        assert len(calls) == 3\n\n\nclass TestBeforeAfterAttempts(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^class TestSyncFunctionWithAsyncSleep\" tests/test_asyncio.py", "description": "Locate async test insertion point"}
[tool_result] 496:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "class TestSyncFunctionWithAsyncSleep(unittest.TestCase):", "new_string": "class TestEnabled(unittest.TestCase):\n    @asynctest\n    async def test_disabled_calls_once_and_propagates_exception(self) -> None:\n      
…[774 chars elided]…
tion(self) -> None:\n        calls: list[int] = []\n\n        @retry(enabled=False, stop=stop_after_attempt(5))\n        async def _fails() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError, match=\"boom\"):\n            await _fails()\n        assert len(calls) == 1\n\n\nclass TestSyncFunctionWithAsyncSleep(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Both test classes are written. Now I'll run only the new tests against the unfixed code, as the harness requires, to confirm they fail for the feature's absence.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new tests alone against unfixed code"}
[tool_result] exit=1
    @asynctest
    async def test_disabled_decorator_does_not_retry_on_exception(self) -> None:
        calls: list[int] = []
    
>       @retry(enabled=False, stop=stop_after_attempt(5))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_asyncio.py:526: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

f = <function TestEnabled.test_disabled_decorator_does_not_retry_on_exception.<locals>._fails at 0x10960c2c0>

    def wrap(f: t.Callab
…[1112 chars elided]…
tion
FAILED tests/test_tenacity.py::TestEnabled::test_retry_with_can_disable - Typ...
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_calls_once_and_propagates_exception
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_calls_once_and_returns_value
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_does_not_retry_on_exception
========================= 7 failed, 1 passed in 0.12s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The seven failures are all `TypeError: ... unexpected keyword argument 'enabled'`, which is the missing feature, not an import or typo. The one passing test is the default-behaviour guard, as intended. Before implementing, I need to check how the async bypass should call a sync or async `fn`.
[tool_use Bash] {"command": "grep -n -A12 \"def wrap_to_async_func\" tenacity/_utils.py; grep -n -A4 \"def is_coroutine_callable\" tenacity/_utils.py", "description": "Read async wrapping helper"}
[tool_result] 102:def wrap_to_async_func(
103-    call: typing.Callable[..., typing.Any],
104-) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
105-    if is_coroutine_callable(call):
106-        return call
107-
108-    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
109-        return call(*args, **kwargs)
110-
111-    return inner
92:def is_coroutine_callable(call: typing.Callable[..., typing.Any]) -> bool:
93-    if inspect.isclass(call):
94-        return False
95-    if inspect.iscoroutinefunction(call):
96-        return True
[assistant] `wrap_to_async_func` handles both sync and async `fn`, so the async bypass is one line. Now the implementation, starting with the core `BaseRetrying`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any] | None = None,\n        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        
…[581 chars elided]…
elf.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":\n        \"\"\"Copy this object with some parameters changed if needed.\"\"\"\n        return self.__class__(\n            sleep=_first_set(sleep, self.
…[1228 chars elided]…
 self.before_sleep),\n            reraise=_first_set(reraise, self.reraise),\n            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),\n            retry_error_callback=_first_set(\n                retry_error_callback, self.retry_error_callback\n            ),\n            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "class Retrying(BaseRetrying):\n    \"\"\"Retrying controller.\"\"\"\n\n    def __call__(\n        self,\n        fn: t.Callable[..., WrappedFnReturnT],\n        *args: t.Any,\n        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()", "new_string": "class Retrying(BaseRetrying):\n    \"\"\"Retrying controller.\"\"\"\n\n    def __call__(\n        self,\n        fn: t.Callable[..., WrappedFnReturnT],\n        *args: t.Any,\n        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Core and decorator overloads are done. Next, the async class: its explicit `__init__` signature and its `__call__` bypass.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1036 chars elided]…
rror_cls,\n            retry_error_callback=retry_error_callback,\n            name=name,\n            enabled=enabled,\n        )\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return await _utils.wrap_to_async_func(fn)(*args, **kwargs)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            raise gen.Return(result)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Implementation is in place across all call paths. I'll re-run the same targeted tests to see them go green.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/green.txt", "description": "Run new tests after the fix"}
[tool_result] exit=0
tests/test_asyncio.py::TestEnabled::test_disabled_decorator_calls_once_and_returns_value PASSED [ 87%]
tests/test_asyncio.py::TestEnabled::test_disabled_decorator_does_not_retry_on_exception PASSED [100%]

============================== 8 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The new tests pass. Per the change contract, a feature needs a reno note and a user-docs example. I'll look at the docs style and the existing reno note format.
[tool_use Bash] {"command": "sed -n 289,312p doc/source/index.rst; echo ---; cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml; echo ---; grep -n \"testcode\" doc/source/index.rst | head -3; sed -n 296,300p doc/source/index.rst", "description": "Read docs section style and reno note format"}
[tool_result] Error Handling
~~~~~~~~~~~~~~

Normally when your function fails its final time (and will not be retried again based on your settings),
a `RetryError` is raised. The exception your code encountered will be shown somewhere in the *middle*
of the stack trace.

If you would rather see the exception your code encountered at the *end* of the stack trace (where it
is most visible), you can set `reraise=True`.

.. testcode::

    @retry(reraise=True, stop=stop_after_attempt(3))
    def raise_my_excepti
…[57 chars elided]…
 raise_my_exception()
    except MyException:
        # timed out retrying
        pass

Before and After Retry, and Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
---
---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
---
29:.. testcode::
100:.. testcode::
113:.. testcode::
If you would rather see the exception your code encountered at the *end* of the stack trace (where it
is most visible), you can set `reraise=True`.

.. testcode::
[assistant] I'll add a short "Disabling retries" section next to the error-handling example, and a reno note with a generated hex suffix.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/doc/source/index.rst", "old_string": "    try:\n        raise_my_exception()\n    except MyException:\n        # timed out retrying\n        pass\n\nBefore and After Retry, and Logging", "new_string": "    try:\n        raise_my_exception()\n    except M
…[206 chars elided]…
 called exactly once, with no retry logic. Any exception it raises\npropagates unchanged, not as a `RetryError`.\n\n.. testcode::\n\n    @retry(enabled=False, stop=stop_after_attempt(3))\n    def fails_once():\n        raise ValueError(\"no retries\")\n\n    try:\n        fails_once()\n    except ValueError:\n        # called once, not retried\n        pass\n\nBefore and After Retry, and Logging"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-200259-feature-add-an-enabled-parameter/base-1/doc/source/index.rst has been updated successfully.
[tool_use Bash] {"command": "N=$(openssl rand -hex 8); F=releasenotes/notes/enabled-parameter-$N.yaml; printf -- '---\\nfeatures:\\n  - |\\n    Add an ``enabled`` parameter (default ``True``) to ``Retrying``, ``AsyncRetrying``\\n    and the ``@retry`` decorator. With ``enabled=False`` the decorated function is\\n    called directly, exactly once, with no retry logic, and any exception it raises\\n    propagates unchanged. This is useful during development and testing.\\n' > $F; cat $F; echo \"$F\"", "description": "Write reno release note with random suffix"}
[tool_result] ---
features:
  - |
    Add an ``enabled`` parameter (default ``True``) to ``Retrying``, ``AsyncRetrying``
    and the ``@retry`` decorator. With ``enabled=False`` the decorated function is
    called directly, exactly once, with no retry logic, and any exception it raises
    propagates unchanged. This is useful during development and testing.
releasenotes/notes/enabled-parameter-d829b79fb5fefe6f.yaml
[assistant] Docs and reno note are written. Now the full suite and the stdlib style check, run in the foreground as the harness requires.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt; echo ---CHECK---; $P .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt | tail -30", "description": "Run full test suite and style checks"}
[tool_result] exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 147 passed, 1 skipped, 12 subtests passed in 1.80s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---CHECK---
exit=0
changed: doc/source/index.rst, releasenotes/notes/enabled-parameter-d829b79fb5fefe6f.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/tornadoweb.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (147 passed, 1 skipped, exit 0), and the style check passes. Two last checks: that the docs example actually runs, and that the docs `testsetup` imports the names it uses.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; grep -n -A6 \"testsetup\" doc/source/index.rst | head -12; cat > /tmp/doccheck.py <<'EOF'\nfrom tenacity import retry, stop_after_attempt\n\n@retry(enabled=False, stop=stop_after_attempt(3))\ndef fails_once():\n    raise ValueError(\"no retries\")\n\ncalls = []\ntry:\n    fails_once()\nexcept ValueError:\n    pass\nprint(\"doc example ok\")\nEOF\n$P -I /tmp/doccheck.py; echo \"exit=$?\"; grep -c \"\" /tmp/full.txt; grep -i \"skip\" /tmp/full.txt | head -3", "description": "Run docs example and locate the skipped test"}
[tool_result] 85:.. testsetup::
86-
87-    import logging
88-    #
89-    # Note the following import is used for demonstration convenience only.
90-    # Production code should always explicitly import the names it needs.
91-    #
Traceback (most recent call last):
  File "/tmp/doccheck.py", line 1, in <module>
    from tenacity import retry, stop_after_attempt
ModuleNotFoundError: No module named 'tenacity'
exit=1
42
============== 147 passed, 1 skipped, 12 subtests passed in 1.80s ==============
[assistant] The `-I` flag ignored my PYTHONPATH, so the import failed for the harness, not the example. I'll re-run with the repo on the path, and confirm the testsetup imports.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; PYTHONPATH=. $P /tmp/doccheck.py; echo \"exit=$?\"; sed -n 92,100p doc/source/index.rst", "description": "Re-run docs example with repo on path"}
[tool_result] doc example ok
exit=0
    from tenacity import *

    class MyException(Exception):
        pass

As you saw above, the default behavior is to retry forever without waiting when
an exception is raised.

.. testcode::
[assistant] The docs example runs and its testsetup uses `from tenacity import *`. Last, I'll confirm the working-tree changes are exactly what I intended.
[tool_use Bash] {"command": "git status --short; git diff --stat", "description": "Show changed files and diff stats"}
[tool_result]  M doc/source/index.rst
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/enabled-parameter-d829b79fb5fefe6f.yaml
 doc/source/index.rst         | 19 ++++++++++++++
 tenacity/__init__.py         |  9 +++++++
 tenacity/asyncio/__init__.py |  5 ++++
 tenacity/tornadoweb.py       |  4 +++
 tests/test_asyncio.py        | 40 +++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 61 ++++++++++++++++++++++++++++++++++++++++++++
 6 files changed, 138 insertions(+)
[assistant] I added `enabled` (default `True`) to `BaseRetrying`, so it works on `Retrying`, `AsyncRetrying` and `@retry`. With `enabled=False` the function is called once, with no retry logic, and its exception propagates unchanged. The full suite passes: 147 passed, 1 skipped, exit 0. I did not commit anything.

**Changes**
- `tenacity/__init__.py`: `enabled` is stored on `BaseRetrying`, carried through `copy()` (so `retry_with(enabled=False)` works), and `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `retry()` typed overloads gained the parameter.
- `tenacity/asyncio/__in
…[988 chars elided]…
d, as intended.
- Green: the new tests pass alone (8 passed).
- Full suite: `run_tests.py` exit 0, 147 passed, 1 skipped. I did not check which test is skipped.
- `check_changed.py`: exit 0, PASS with 0 problems.
- ruff and mypy were not run (unavailable in this environment).

**Decisions and gaps**
- Iteration (`for attempt in Retrying(enabled=False)` and `async for`) still retries. The request only covered the decorated call, so I left it alone. Say if you want it to yield a single attempt.
- With `enabled=False` the decorated function's `statistics` stay empty, because `begin()` is skipped.
