# trajectory inv-1

final message:
`enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`, with `enabled=False` calling the function once and letting its exception propagate. The full suite passes: 145 passed, 1 skipped, no failures. I didn't commit anything; the changes are in the working tree.

**What changed**
- `tenacity/__init__.py`: `BaseRetrying` takes `enabled: bool = True` and stores it. `copy()` carries it, so `retry_with(enabled=False)` works. `Retrying.__call__` returns `fn(*args, **kwargs)` straight away when disabled. The `@retry` overloads gained the parameter.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying` accepts and forwards `enabled`. Its `__call__` awaits the function when it is a coroutine function, then returns the result.
- `tenacity/tornadoweb.py`: `TornadoRetrying.__call__` has the same check. Without it, `@retry(enabled=False)` on a Tornado coroutine would have been silently ignored, since its `**kwargs` passes the flag through.
- Tests: `TestEnabled` in `tests/test_tenacity.py` and `tests/test_asyncio.py`, plus `test_enabled_false_calls_once` in `tests/test_tornado.py`. Each runs the same failing scenario with the default and with `enabled=False`, so a fix that ignored the parameter would fail.
- Release note: `releasenotes/notes/enabled-parameter-33599495e6f54b15.yaml` (a `features:` entry).

**Verification**
- Fail-on-base (`fails_on_base.py`) exited 0: all six new tests fail on HEAD with `unexpected keyword argument 'enabled'`. That only shows the name is new; the default-vs-disabled comparison inside each test is what pins the behaviour.
- mypy and ruff are not installed in the project interpreter, so I did not run them. I checked the annotations by hand.

**Choices I made that you may want to change**
- Only the call path is affected. `for attempt in Retrying(enabled=False)` and `async with`-style iteration still retry. Making iteration single-shot would mean swallowing exceptions inside `with attempt:`, which conflicts with the propagation requirement, so I left it alone.
- A disabled call skips `begin()`, so `statistics` stays empty for that call.
- I included Tornado, which you didn't name, because the flag would otherwise do nothing there silently.

## events
[assistant] I'll start by loading the change-contract skill the project requires, then read the retry code.
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex 
…[7252 chars elided]…
rror: ... unexpected keyword argument` /
   `ImportError` on HEAD is expected, but it only shows the name is new. It does not show the
   behaviour is right. So each behaviour test must also prove it can tell the cases apart: in
   the same test, run the scenario with the parameter's default value and assert the result
   differs (e.g. it retries). Then a fix that ignored the new parameter would fail the test.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "pwd && git status --short && git log --oneline -1 && ls releasenotes/notes | tail -5 && ls tests && grep -n \"def retry\\|class Retrying\\|class AsyncRetrying\\|class BaseRetrying\\|def __init__\\|def wraps\\|def call\\|def __call__\\|def iter\\|def __iter__\\|def __aiter__\\|def copy\\|def __init__\" tenacity/__init__.py tenacity/asyncio/__init__.py", "description": "Check worktree state, notes, tests, and key defs"}
[tool_result] ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1
a4e9108 lithify: probe base
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
tenacity/asyncio/__init_
…[1787 chars elided]…

tenacity/__init__.py:630:    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
tenacity/__init__.py:635:    def __call__(
tenacity/__init__.py:639:    def __call__(
tenacity/__init__.py:643:    def __call__(
tenacity/__init__.py:647:    def __call__(
tenacity/__init__.py:653:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
tenacity/__init__.py:657:def retry(
tenacity/__init__.py:674:def retry(
tenacity/__init__.py:690:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
[assistant] The skill is loaded. Its checklist needs `fails_on_base.py` and the project interpreter from the CLAUDE.md. Next I'll read the core call paths.
[tool_use Bash] {"command": "sed -n 225,340p tenacity/__init__.py; echo ----; sed -n 380,700p tenacity/__init__.py", "description": "Read BaseRetrying init, copy, wraps and call paths"}
[tool_result]     ) -> bool | None:
        return self.__exit__(exc_type, exc_value, traceback)


class BaseRetrying(ABC):
    def __init__(
        self,
        sleep: t.Callable[[int | float], None] = sleep,
        stop: "StopBaseT" = stop_never,
        wait: "WaitBaseT" = wait_none(),
        retry: "RetryBaseT" = retry_if_exception_type(),
        before: t.Callable[["RetryCallState"], None] = before_nothing,
        after: t.Callable[["RetryCallState"], None] = after_nothing,
        before_sleep: t.
…[15067 chars elided]…
 -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...


def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
    """Wrap a function with a new `Retrying` object.

    :param dargs: positional arguments passed to Retrying object
    :param dkw: keyword arguments passed to the Retrying object
    """
    # support both @retry and @retry() as valid syntax
    if len(dargs) == 1 and callable(dargs[0]):
        return retry()(dargs[0])

    def wrap(f: t.Callable[P, R]) -> _RetryDecorated[P, R]:
[tool_use Bash] {"command": "sed -n 1,200p tenacity/asyncio/__init__.py", "description": "Read AsyncRetrying class"}
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
…[6478 chars elided]…
o prevent overwriting the local contexts when
            # calling the same wrapped functions multiple times in the same stack
            copy = self.copy()
            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]

        # Preserve attributes
        async_wrapped.retry = self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
[assistant] Next I need the decorator wiring (`wraps`, `retry_with`, `retry()`'s `wrap`) and the tail of the asyncio `wraps`, since `enabled` has to flow through `copy()` too.
[tool_use Bash] {"command": "sed -n 337,380p tenacity/__init__.py; echo ----; sed -n 700,720p tenacity/__init__.py; echo ----; sed -n 200,240p tenacity/asyncio/__init__.py; echo ----; grep -n \"_unset\\|_first_set\" tenacity/__init__.py | head; echo ----; ls releasenotes/notes | head -3; cat releasenotes/notes/$(ls releasenotes/notes | grep -v yaml$ | head -1) 2>/dev/null; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ----; ls .lithify/harness/skills/tenacity-change-contract/scripts/ 2>&1; ls <work>/env-tenacity/bin/python && echo PYOK", "description": "Read decorator wiring, reno note example, and skill script"}
[tool_result]     def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.
        """

        @functools.wraps(
            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:
            # Always create a copy to prevent overwriting the local contexts when
            # calling the same wrapped functions multiple times in
…[3022 chars elided]…
5:        before_sleep: t.Callable[["RetryCallState"], None] | None | object = _unset,
----
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
----
fails_on_base.py
<work>/env-tenacity/bin/python
PYOK
[assistant] The decorator path goes through `copy()`, so `enabled` has to be threaded through `copy()` as well. Before designing, I'll check `TornadoRetrying`, because if it overrides `__init__`, `copy()` would break on the new kwarg. I also need the existing test style.
[tool_use Bash] {"command": "grep -n \"class TornadoRetrying\" -A 30 tenacity/tornadoweb.py | head -50; echo ----; grep -n \"class Test\\|^def test_\" tests/test_tenacity.py | head -60; echo ----; grep -n \"def test_retry_function_attributes\" -A 25 tests/test_tenacity.py | head -40; echo ----; grep -n \"class TestRetryConditions\\|class TestContextManager\\|class TestDecorator\" tests/*.py; sed -n 1,30p tests/test_asyncio.py | grep -n import", "description": "Check Tornado subclass, test style, and attribute tests"}
[tool_result] 28:class TornadoRetrying(BaseRetrying):
29-    sleep: typing.Callable[..., "Future[None]"]
30-
31-    def __init__(
32-        self,
33-        sleep: "typing.Callable[[float], Future[None]]" = gen.sleep,
34-        **kwargs: typing.Any,
35-    ) -> None:
36-        super().__init__(**kwargs)
37-        self.sleep = sleep
38-
39-    @gen.coroutine
40-    def __call__(  # type: ignore[override]
41-        self,
42-        fn: "typing.Callable[..., typing.Generator[typing.Any, typing.Any, _RetValT
…[2794 chars elided]…
class TestDecoratorWrapper(unittest.TestCase):
tests/test_tenacity.py:1722:class TestContextManager(unittest.TestCase):
tests/test_asyncio.py:178:class TestContextManager(unittest.TestCase):
tests/test_asyncio.py:427:class TestDecoratorWrapper(unittest.TestCase):
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
[assistant] `TornadoRetrying` takes `**kwargs`, so `enabled` would reach `BaseRetrying` and be silently ignored there unless its `__call__` checks it too. I'll cover it so the flag doesn't quietly do nothing on that path. Now I'll make the core edits.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "        name: str | None = None,\n    ):\n        self.sleep = sleep", "new_string": "        name: str | None = None,\n        enabled: bool = True,\n    ):\n        self.sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "        self._name = name\n\n    def copy(", "new_string": "        self._name = name\n        self.enabled = enabled\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":", "new_string": "        name: str | None | object = _unset,\n        enabled: bool | object = _unset,\n    ) -> \"Self\":"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "            name=_first_set(name, self._name),\n        )", "new_string": "            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n 
…[133 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/__init__.py has been updated successfully.
[assistant] Sync core is done. Now the asyncio class, which has its own `__init__`, `__call__`, and `wraps`, plus the Tornado `__call__`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # type
…[1123 chars elided]…
,\n            enabled=enabled,\n        )\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            value: t.Any = fn(*args, **kwargs)\n            if _utils.is_coroutine_callable(fn):\n                value = await value\n            return value\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            return result\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Core code is in place. Before writing tests I'll check the imports and style used by the existing decorator tests in both files.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_tenacity.py | grep -n \"import\\|from\"; echo ----; sed -n 427,450p tests/test_asyncio.py; echo ----; sed -n 1,40p tests/test_asyncio.py | grep -n \"import\\|from\\|asyncio_\\|sleep\"; echo ----; tail -5 tests/test_asyncio.py; echo; tail -5 tests/test_tenacity.py; echo ----; grep -n \"def test_\" tests/test_tornado.py | head -3; sed -n 1,30p tests/test_tornado.py | grep -n \"import\"", "description": "Inspect test imports and existing async test style"}
[tool_result] 16:import contextlib
17:import datetime
18:import logging
19:import re
20:import time
21:import typing
22:import unittest
23:import warnings
24:from contextlib import contextmanager
25:from copy import copy
26:from fractions import Fraction
27:from unittest import mock
29:import pytest
30:from typeguard import check_type
----
class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attribut
…[1089 chars elided]…
  assert mock_sleep.call_count == 1


if __name__ == "__main__":
    unittest.main()
----
44:    def test_retry(self) -> Generator[Any, Any, None]:
51:    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
59:    def test_repr(self) -> None:
15:import unittest
16:from collections.abc import Generator
17:from typing import Any
19:from tornado import gen, testing
21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
23:from .test_tenacity import NoIOErrorAfterCount
[assistant] I have the test style. Tornado's disabled branch also needs coverage, so I'll look at how `test_tornado.py` writes its generator tests before adding one.
[tool_use Bash] {"command": "sed -n 25,60p tests/test_tornado.py", "description": "Read tornado test style"}
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
…[69 chars elided]…
t(5)
        yield _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @testing.gen_test
    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
        assert gen.is_coroutine_function(_retryable_coroutine)
        thing = NoIOErrorAfterCount(2)
        try:
            yield _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tornadoweb.TornadoRetrying())
[assistant] I have what I need for the tests. Each behaviour test runs the same scenario with the default and with `enabled=False`, so a fix that ignored the new parameter would fail.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py", "old_string": "        assert mock_sleep.call_count == 1\n\n\nif __name__ == \"__main__\":\n    unittest.main()", "new_string": "        assert mock_sleep.call_count == 1\n\n\nclass TestEnabled(unittest.TestCase):\n    def test_di
…[1718 chars elided]…
elf) -> None:\n        calls: list[int] = []\n\n        @tenacity.retry(stop=tenacity.stop_after_attempt(3))\n        def fail() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError, match=\"boom\"):\n            fail.retry_with(enabled=False)()\n        assert len(calls) == 1\n\n\nif __name__ == \"__main__\":\n    unittest.main()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_asyncio.py", "old_string": "        assert mock_sleep.await_count == 2\n\n\nif __name__ == \"__main__\":\n    unittest.main()", "new_string": "        assert mock_sleep.await_count == 2\n\n\nclass TestEnabled(unittest.TestCase):\n    @asynctest
…[1449 chars elided]…
"boom\"):\n            await tenacity.asyncio.AsyncRetrying(\n                enabled=False, stop=tenacity.stop_after_attempt(2)\n            )(succeed_after_failure)\n        assert len(calls) == 1\n\n        async def ok() -> str:\n            return \"ok\"\n\n        assert await tenacity.asyncio.AsyncRetrying(enabled=False)(ok) == \"ok\"\n\n\nif __name__ == \"__main__\":\n    unittest.main()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tornado.py", "old_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())", "new_string": "    @testing.gen_test\n    def test_enabled_false_calls_once(self) -> Generator[Any, Any, None]:\n        calls: list[int]
…[510 chars elided]…
efault still retries, so the disabled case below is a real difference.\n        with self.assertRaises(RetryError):\n            yield fail_default()\n        assert len(calls) == 3\n\n        calls.clear()\n        with self.assertRaises(ValueError):\n            yield fail_disabled()\n        assert len(calls) == 1\n\n    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tornado.py has been updated successfully.
[assistant] One cleanup before running: the `noqa: E731` on a lambda passed as an argument is unnecessary, and the assert wrapping is awkward. I'll simplify it and then run the new tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py", "old_string": "        assert (\n            tenacity.Retrying(enabled=False)(lambda: \"ok\") == \"ok\"  # noqa: E731\n        )", "new_string": "        assert tenacity.Retrying(enabled=False)(lambda: \"ok\") == \"ok\""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled tests/test_tornado.py::TestTornado::test_enabled_false_calls_once 2>&1 | tail -30; echo \"exit=$?\"", "description": "Run the new enabled tests"}
[tool_result]             return "ok"
    
>       with pytest.raises(tenacity.RetryError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RetryError

tests/test_tenacity.py:1966: Failed
_______ TestEnabled.test_disabled_async_retrying_returns_result_directly _______

self = <tests.test_asyncio.TestEnabled testMethod=test_disabled_async_retrying_returns_result_directly>

    @asynctest
    async def test_disabled_async_retrying_returns_result_directly(self) -> None:
        call
…[177 chars elided]…
        return "ok"
    
>       with pytest.raises(tenacity.RetryError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RetryError

tests/test_asyncio.py:552: Failed
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_disabled_retrying_returns_result_directly
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_async_retrying_returns_result_directly
2 failed, 4 passed in 0.07s
exit=0
[assistant] Both failures are my test's logic, not the code: the helper succeeds on its second call, so the default run with two attempts returns `"ok"` instead of raising. The default case should assert that it returns `"ok"` after two calls, and the disabled case should assert the first `ValueError` propagates after one call. I'll fix both tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py", "old_string": "        with pytest.raises(tenacity.RetryError):\n            tenacity.Retrying(stop=tenacity.stop_after_attempt(2))(\n                succeed_after_failure\n            )\n        assert len(calls) == 2", "new_string": "        # The default retries past the first failure and returns the later result.\n        assert (\n            tenacity.Retrying(stop=tenacity.stop_after_attempt(2))(\n                succeed_after_failure\n            )\n            == \"ok\"\n        )\n        assert len(calls) == 2"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(tenacity.RetryError):\n            await tenacity.asyncio.AsyncRetrying(\n                stop=tenacity.stop_after_attempt(2)\n            )(succeed_after_failure)\n        assert len(calls) == 2", "new_string": "        # The default retries past the first failure and returns the later result.\n        assert (\n            await tenacity.asyncio.AsyncRetrying(stop=tenacity.stop_after_attempt(2))(\n                succeed_after_failure\n            )\n            == \"ok\"\n        )\n        assert len(calls) == 2"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled tests/test_tornado.py::TestTornado::test_enabled_false_calls_once 2>&1 | tail -5; echo \"exit=${PIPESTATUS[0]}\"; ls .lithify/harness/skills/tenacity-change-contract/scripts/ && sed -n 1,30p .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py", "description": "Rerun new tests and inspect fails-on-base script"}
[tool_result] ......                                                                   [100%]
6 passed in 0.05s
exit=
fails_on_base.py
#!/usr/bin/env python3
"""Check that new/changed tests FAIL on the unmodified code (HEAD), read-only.

Usage (from the repo root, with the project interpreter so pytest is importable):
    <project-python> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \
        tests/test_x.py::TestY::test_z [more pytest node ids or args ...]

What it does: exports 
…[282 chars elided]…
stash are
never touched.

Exit codes:
    0  GOOD  - the tests fail (or fail to import) on HEAD: they catch the bug.
    1  BAD   - the tests pass on HEAD: they do not reproduce the bug.
    2  ERROR - the check could not run; report the fail-on-base check as NOT verified.
"""

import os
import shutil
import subprocess
import sys
import tempfile


def main(argv: list[str]) -> int:
    if not argv:
        print("ERROR: pass the pytest node ids of the new tests", file=sys.stderr)
        return 2
[assistant] All six new tests pass. Next I'll run the project's fail-on-base check on the new tests and create the release note in the same turn, since neither depends on the other.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled tests/test_tornado.py::TestTornado::test_enabled_false_calls_once; echo \"exit=$?\"", "description": "Verify new tests fail on HEAD"}
[tool_use Bash] {"command": "python3 -c \"import secrets;print(secrets.token_hex(8))\"", "description": "Generate suffix for release note filename"}
[tool_result]         calls: list[int] = []
    
        @retry(stop=stop_after_attempt(3))
        @gen.coroutine
        def fail_default() -> Generator[Any, Any, None]:
            calls.append(1)
            yield gen.sleep(0.00001)
            raise ValueError("boom")
    
>       @retry(enabled=False, stop=stop_after_attempt(3))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_tornado.py:70: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/_
…[1047 chars elided]…
city.py::TestEnabled::test_retry_with_can_disable_retrying
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_async_retrying_returns_result_directly
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_calls_once_and_propagates
FAILED tests/test_tornado.py::TestTornado::test_enabled_false_calls_once - Ty...
6 failed in 0.10s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
exit=0
[tool_result] 33599495e6f54b15
[assistant] Fail-on-base exits 0: all six fail on HEAD with `unexpected keyword argument 'enabled'`. As the checklist warns, that only shows the name is new. The behaviour is pinned by the same-test default-vs-disabled comparisons. Now the release note.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/releasenotes/notes/enabled-parameter-33599495e6f54b15.yaml", "content": "---\nfeatures:\n  - |\n    Added an ``enabled`` parameter (default ``True``) to ``Retrying``,\n    ``AsyncRetrying`` and the ``@retry`` decorator. With ``enabled=False`` the\n    decorated function is called directly, exactly once, with no retry logic,\n    and any exception it raises propagates unchanged. This is useful during\n    development and testing.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/inv-1/releasenotes/notes/enabled-parameter-33599495e6f54b15.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit=${PIPESTATUS[0]}\"; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ...........s........................................................................................................................ [ 90%]
..............                                                           [100%]
145 passed, 1 skipped, 12 subtests passed in 1.79s
exit=
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 M tests/test_tornado.py
?? releasenotes/notes/enabled-parameter-33599495e6f54b15.yaml
[assistant] `enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`, with `enabled=False` calling the function once and letting its exception propagate. The full suite passes: 145 passed, 1 skipped, no failures. I didn't commit anything; the changes are in the working tree.

**What changed**
- `tenacity/__init__.py`: `BaseRetrying` takes `enabled: bool = True` and stores it. `copy()` carries it, so `retry_with(enabled=False)` works. `Retrying.__call__` returns `fn(*args, **kwargs)` straight away when disabled. The `@retry` overloads gained the parameter.
- `tenacity/asyncio/__init__.py`: `Async
…[1002 chars elided]…
talled in the project interpreter, so I did not run them. I checked the annotations by hand.

**Choices I made that you may want to change**
- Only the call path is affected. `for attempt in Retrying(enabled=False)` and `async with`-style iteration still retry. Making iteration single-shot would mean swallowing exceptions inside `with attempt:`, which conflicts with the propagation requirement, so I left it alone.
- A disabled call skips `begin()`, so `statistics` stays empty for that call.
- I included Tornado, which you didn't name, because the flag would otherwise do nothing there silently.
