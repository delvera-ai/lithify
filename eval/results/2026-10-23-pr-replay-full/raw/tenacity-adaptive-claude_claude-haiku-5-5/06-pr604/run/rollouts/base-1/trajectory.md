# trajectory base-1

final message:
`enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`. With `enabled=False` the function runs once, returns its result, and any exception propagates unchanged. The test suite passes: 149 passed, 1 skipped (baseline was 139 passed, 1 skipped).

**Changes**
- **`tenacity/__init__.py`**: `enabled: bool = True` on `BaseRetrying`, carried through `copy()` so `retry_with()` keeps it. `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `@retry` overloads gained the parameter; it reaches the constructor through `**dkw`.
- **`tenacity/asyncio/__init__.py`**: `AsyncRetrying` takes `enabled` and short-circuits in `__call__`, awaiting the function if it is a coroutine and calling it otherwise.
- **`tenacity/tornadoweb.py`**: `TornadoRetrying` also short-circuits. It accepts `enabled` through `**kwargs`, so without this the flag would be silently ignored there.
- **Tests**: 9 new tests across `test_tenacity.py`, `test_asyncio.py` and `test_tornado.py`. They cover call-once behaviour, exception identity, `copy()`/`retry_with()` preservation, and that the default still retries.
- **Release note**: `releasenotes/notes/add-enabled-parameter-3f8c1a2d9e7b5c60.yaml`.

**Choices I made**
- The bypass sits in `__call__` and skips `begin()`, so `statistics` stays empty when disabled.
- The `for attempt in Retrying(...)` / `async for` iteration form is not changed. The request talked about decorated functions, and making iteration yield exactly one attempt while still propagating exceptions would need more machinery. Say if you want it covered.
- I didn't add a section to `doc/source/index.rst` or `README.rst`; the release note is the only documentation.

**Not verified**
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. I checked line lengths by hand.
- I haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short && ls && wc -l tenacity/*.py && grep -n \"def retry\\b\\|class Retrying\\|class AsyncRetrying\\|def wrapped_f\\|def __call__\\|def call\\|def wraps\\|def iter\\b\\|def __init__\" tenacity/__init__.py tenacity/asyncio/__init__.py tenacity/*.py | head -60", "description": "Inspect repo layout and key definitions"}
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
tenacity/__init__.py:168:    def __init__(self, sleep: t.SupportsFloat) -> N
…[3466 chars elided]…
DoSleep | t.Any:
tenacity/__init__.py:469:    def __call__(
tenacity/__init__.py:478:class Retrying(BaseRetrying):
tenacity/__init__.py:481:    def __call__(
tenacity/__init__.py:509:    def __init__(self, attempt_number: int) -> None:
tenacity/__init__.py:534:    def __init__(
tenacity/__init__.py:630:    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
tenacity/__init__.py:635:    def __call__(
tenacity/__init__.py:639:    def __call__(
tenacity/__init__.py:643:    def __call__(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 215, "limit": 300}
[tool_result] 215	        return None
216	
217	    async def __aenter__(self) -> None:
218	        pass
219	
220	    async def __aexit__(
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
232	        sleep: t.Callable[[int 
…[11584 chars elided]…
           retry_state.prepare_for_next_attempt()
501	                self.sleep(do)
502	            else:
503	                return do  # type: ignore[no-any-return]
504	
505	
506	class Future(futures.Future[t.Any]):
507	    """Encapsulates a (future or past) attempted call to a target function."""
508	
509	    def __init__(self, attempt_number: int) -> None:
510	        super().__init__()
511	        self.attempt_number = attempt_number
512	
513	    @property
514	    def failed(self) -> bool:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 460, "limit": 330}
[tool_result] 460	            if isinstance(do, DoAttempt):
461	                yield AttemptManager(retry_state=retry_state)
462	            elif isinstance(do, DoSleep):
463	                retry_state.prepare_for_next_attempt()
464	                self.sleep(do)
465	            else:
466	                break
467	
468	    @abstractmethod
469	    def __call__(
470	        self,
471	        fn: t.Callable[..., WrappedFnReturnT],
472	        *args: t.Any,
473	        **kwargs: t.Any,
474	    ) -> WrappedFnRet
…[10691 chars elided]…
 "sleep_using_event",
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
[tool_use Bash] {"command": "cat AGENTS.md | head -80; echo ----; cat tenacity/asyncio/__init__.py; echo ----; sed -n 1,62p tenacity/tornadoweb.py; echo ----; ls releasenotes/notes | tail -5; ls tests; grep -rn \"enabled\" tenacity doc README.rst | head", "description": "Read async, tornado modules and project docs"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[10037 chars elided]…
oSleep):
                retry_state.prepare_for_next_attempt()
                yield self.sleep(do)
            else:
                raise gen.Return(do)
----
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
[tool_use Bash] {"command": "cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml; echo ----; ls <work>/env-tenacity/bin/python && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; grep -n \"copy(\" tests/test_tenacity.py | head -5; grep -n \"tornado\" tests/test_tornado.py | head -3", "description": "Check release note format and run baseline tests"}
[tool_result] ---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
----
<work>/env-tenacity/bin/python
...........s................................................ [ 42%]
........................................................................ [ 94%]
........                                                                 [100%]
139 passed, 1 skipped, 12 subtests passed in 2.26s
123:    def test_str_preserved_by_copy(self) -> None:
124:        """copy() preserves the name."""
126:        assert str(r.copy()) == "my_block"
128:    def test_str_overridden_by_copy(self) -> None:
129:        """copy() allows overriding the name."""
19:from tornado import gen, testing
21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
60:        repr(tornadoweb.TornadoRetrying())
[assistant] Baseline is green (139 passed, 1 skipped). Now the core change: a `enabled` flag on `BaseRetrying`, carried through `copy()`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        
…[375 chars elided]…
= stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":\n        \"\"\"Copy this object with some parameters changed if needed.\"\"\"\n        return self.__class__(\n            sleep=_first_set(sleep, self.
…[1228 chars elided]…
 self.before_sleep),\n            reraise=_first_set(reraise, self.reraise),\n            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),\n            retry_error_callback=_first_set(\n                retry_error_callback, self.retry_error_callback\n            ),\n            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, the sync bypass in `Retrying.__call__`, the `retry` decorator overloads, and the async class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async side: the constructor, and the bypass in `AsyncRetrying.__call__`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1369 chars elided]…
     self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        is_async = _utils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                return await fn(*args, **kwargs)\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] The tornado variant takes `enabled` through `**kwargs` into `BaseRetrying`, so without a bypass there it would be silently ignored. Adding the same short-circuit there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            raise gen.Return(result)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Now tests. Checking the existing test style first so the new ones match.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_asyncio.py; echo ----; sed -n 100,135p tests/test_tenacity.py; echo ----; grep -n \"^class \\|^def test_\\|asyncio.run\\|pytest.mark\" tests/test_asyncio.py | head -30; echo ----; sed -n 40,70p tests/test_tornado.py", "description": "Look at existing test conventions"}
[tool_result] # Copyright 2016 Étienne Bersac
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the spe
…[2849 chars elided]…
  except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tornadoweb.TornadoRetrying())

    def test_old_tornado(self) -> None:
        old_attr = gen.is_coroutine_function
        try:
            del gen.is_coroutine_function

            # is_coroutine_function was introduced in tornado 4.5;
            # verify that we don't *completely* fall over on old versions
            @retry
            def retryable(thing: NoIOErrorAfterCount) -> None:
[tool_use Bash] {"command": "sed -n 15,60p tests/test_tenacity.py | grep -n \"import\\|^)\" ; tail -5 tests/test_tenacity.py; echo ----; tail -5 tests/test_asyncio.py; grep -n \"^from\\|^import\" tests/test_asyncio.py", "description": "Check test module imports and file endings"}
[tool_result] 2:import contextlib
3:import datetime
4:import logging
5:import re
6:import time
7:import typing
8:import unittest
9:import warnings
10:from contextlib import contextmanager
11:from copy import copy
12:from fractions import Fraction
13:from unittest import mock
15:import pytest
16:from typeguard import check_type
18:import tenacity
19:from tenacity import RetryCallState, RetryError, Retrying, retry
46:) -> RetryCallState:
        assert mock_sleep.call_count == 1


if __name__ == "__main__":
    unittest.main()
----
        assert mock_sleep.await_count == 2


if __name__ == "__main__":
    unittest.main()
15:import asyncio
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        assert mock_sleep.call_count == 1\n\n\nif __name__ == \"__main__\":", "new_string": "        assert mock_sleep.call_count == 1\n\n\nclass TestEnabled(unittest.TestCase):\n    def test_disabled_calls_once_an
…[1872 chars elided]…
etry_with(self) -> None:\n        \"\"\"retry_with() keeps enabled unless it is passed explicitly.\"\"\"\n\n        @retry(enabled=False)\n        def fails() -> None:\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError):\n            fails.retry_with(stop=tenacity.stop_after_attempt(3))()\n        assert fails.retry.enabled is False\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Two of those tests are weaker than they look: the `retry_with` one asserts on the wrong object, and the `mock.patch` target doesn't affect the default `sleep` bound at definition time. Tightening both.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        fn = mock.Mock(side_effect=exc)\n        with mock.patch(\"tenacity.nap.time.sleep\") as mock_sleep:\n            with pytest.raises(ValueError) as info:\n                Retrying(enabled=False, stop=tenaci
…[108 chars elided]…
assert mock_sleep.call_count == 0", "new_string": "        fn = mock.Mock(side_effect=exc)\n        sleep = mock.Mock()\n        with pytest.raises(ValueError) as info:\n            Retrying(enabled=False, sleep=sleep, stop=tenacity.stop_after_attempt(5))(\n                fn\n            )\n        assert info.value is exc\n        assert fn.call_count == 1\n        assert sleep.call_count == 0"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "        @retry(enabled=False)\n        def fails() -> None:\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError):\n            fails.retry_with(stop=tenacity.stop_after_attempt(3))()\n        assert fails.retry.enabled is False", "new_string": "        calls = []\n\n        @retry(enabled=False)\n        def fails() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError):\n            fails.retry_with(stop=tenacity.stop_after_attempt(3))()\n        assert len(calls) == 1"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now async coverage in `test_asyncio.py`, covering both coroutine and sync callables through `AsyncRetrying`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        assert mock_sleep.await_count == 2\n\n\nif __name__ == \"__main__\":", "new_string": "        assert mock_sleep.await_count == 2\n\n\nclass TestAsyncEnabled(unittest.TestCase):\n    def test_disabled_calls_c
…[974 chars elided]…
d=False) on a coroutine function calls it once.\"\"\"\n        calls = []\n\n        @retry(enabled=False, stop=stop_after_attempt(5))\n        async def fails() -> None:\n            calls.append(1)\n            raise ValueError(\"boom\")\n\n        with pytest.raises(ValueError, match=\"boom\"):\n            asyncio.run(fails())\n        assert len(calls) == 1\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"stop_after_attempt\" tests/test_asyncio.py | head -2; PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; $PY -c \"import tornado\" 2>&1 | tail -1", "description": "Run full test suite with the new tests"}
[tool_result] 40:    stop_after_attempt,
73:@retry(stop=stop_after_attempt(2))
...........s........................................................................................................................ [ 88%]
.................                                                        [100%]
148 passed, 1 skipped, 12 subtests passed in 2.00s
[assistant] All 148 pass (139 existing + 9 new). Tornado imports cleanly here, so I'll add a tornado test for the bypass I added there too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())\n", "new_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())\n\n    @testing.gen_test\n    def test_disabled_calls_once(self) -> Generator[Any, Any, None]:\n        thing = NoIOErrorAfterCount(5)\n        disabled = retry(enabled=False)(_retryable_coroutine)\n        with self.assertRaises(IOError):\n            yield disabled(thing)\n        assert thing.counter == 1\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "grep -n -A8 \"class NoIOErrorAfterCount\\|def _retryable_coroutine(\" tests/test_tornado.py | head -40", "description": "Inspect tornado test helpers"}
[tool_result] 28:def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
29-    yield gen.sleep(0.00001)
30-    thing.go()
31-
32-
33-@retry(stop=stop_after_attempt(2))
34-@gen.coroutine
35-def _retryable_coroutine_with_2_attempts(
36-    thing: NoIOErrorAfterCount,
[assistant] `retry(enabled=False)` on a generator-style coroutine may not dispatch to `TornadoRetrying`, so I'll call `TornadoRetrying` directly to exercise the path I actually changed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "        thing = NoIOErrorAfterCount(5)\n        disabled = retry(enabled=False)(_retryable_coroutine)\n        with self.assertRaises(IOError):\n            yield disabled(thing)\n        assert thing.counter == 1", "new_string": "        thing = NoIOErrorAfterCount(5)\n        with self.assertRaises(IOError):\n            yield tornadoweb.TornadoRetrying(enabled=False)(_retryable_coroutine, thing)\n        assert thing.counter == 1"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; $PY -m mypy tenacity 2>&1 | tail -3; $PY -m ruff check tenacity tests 2>&1 | tail -3; $PY -m ruff format --check tenacity tests 2>&1 | tail -3", "description": "Run full tests plus type and lint checks"}
[tool_result] ...........s........................................................................................................................ [ 88%]
...........F......                                                       [100%]
=================================== FAILURES ===================================
_____________________ TestTornado.test_disabled_calls_once _____________________

self = <tests.test_tornado.TestTornado testMethod=test_disabled_calls_once>

    @testing.gen_test
    def test_disab
…[509 chars elided]…
-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[assistant] The tornado test fails: the disabled call didn't raise. Checking the helper's semantics before deciding whether the test or the code is wrong.
[tool_use Bash] {"command": "grep -rn -A12 \"class NoIOErrorAfterCount\" tests/ | head -20", "description": "Inspect NoIOErrorAfterCount helper"}
[tool_result] tests/test_tenacity.py:839:class NoIOErrorAfterCount:
tests/test_tenacity.py-840-    """Holds counter state for invoking a method several times in a row."""
tests/test_tenacity.py-841-
tests/test_tenacity.py-842-    def __init__(self, count: int) -> None:
tests/test_tenacity.py-843-        self.counter = 0
tests/test_tenacity.py-844-        self.count = count
tests/test_tenacity.py-845-
tests/test_tenacity.py-846-    def go(self) -> typing.Any:
tests/test_tenacity.py-847-        """Raise an IOError until after count threshold has been crossed.
tests/test_tenacity.py-848-
tests/test_tenacity.py-849-        Then return True.
tests/test_tenacity.py-850-        """
tests/test_tenacity.py-851-        if self.counter < self.count:
[tool_use Bash] {"command": "sed -n 22,30p tests/test_tornado.py; sed -n 851,856p tests/test_tenacity.py", "description": "Check tornado helper decorator and go() body"}
[tool_result] from .test_tenacity import NoIOErrorAfterCount


@retry
@gen.coroutine
def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()
        if self.counter < self.count:
            self.counter += 1
            raise OSError("Hi there, I'm an IOError")
        return True
[assistant] The helper is wrapped in `@retry` itself, so my test was calling a retrying function and the disabled path never ran. The test should use a plain coroutine.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "        thing = NoIOErrorAfterCount(5)\n        with self.assertRaises(IOError):\n            yield tornadoweb.TornadoRetrying(enabled=False)(_retryable_coroutine, thing)\n        assert thing.counter == 1", "new_string": "        @gen.coroutine\n        def plain(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:\n            yield gen.sleep(0.00001)\n            thing.go()\n\n        thing = NoIOErrorAfterCount(5)\n        with self.assertRaises(OSError):\n            yield tornadoweb.TornadoRetrying(enabled=False)(plain, thing)\n        assert thing.counter == 1"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tornado.py -k disabled 2>&1 | tail -2; $PY -m pyflakes --version >/dev/null 2>&1 && echo pyflakes; ls $(dirname $PY) | grep -i \"ruff\\|mypy\\|flake\\|black\" ; git diff --stat", "description": "Rerun full suite and show diff stats"}
[tool_result] ...........s........................................................................................................................ [ 88%]
..................                                                       [100%]
149 passed, 1 skipped, 12 subtests passed in 1.83s
.                                                                        [100%]
1 passed, 4 deselected in 0.02s
 tenacity/__init__.py         |  9 +++++++
 tenacity/asyncio/__init__.py |  9 ++++++-
 tenacity/tornadoweb.py       |  4 +++
 tests/test_asyncio.py        | 40 +++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 61 ++++++++++++++++++++++++++++++++++++++++++++
 tests/test_tornado.py        | 12 +++++++++
 6 files changed, 134 insertions(+), 1 deletion(-)
[assistant] All 149 pass. Ruff and mypy aren't installed in this env, so I'll check line lengths by hand, and look for a parameter reference in the docs and the release-notes convention.
[tool_use Bash] {"command": "git diff -U0 | grep \"^+\" | awk 'length($0) > 89 {print length($0)\": \"$0}'; grep -rn \"reraise\" doc README.rst | head -5; ls releasenotes/notes | head -3; grep -n \"line-length\\|E501\" pyproject.toml", "description": "Check long lines and docs references for params"}
[tool_result] 97: +        """With enabled=False a sync function is called exactly once and its result returned."""
doc/source/index.rst:297:is most visible), you can set `reraise=True`.
doc/source/index.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
doc/source/index.rst:592:        retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
README.rst:297:is most visible), you can set `reraise=True`.
README.rst:301:    @retry(reraise=True, stop=stop_after_attempt(3))
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
100:line-length = 88
110:    "E501",  # line too long (formatter handles what it can)
[assistant] Fixing the one over-long docstring and adding a reno release note, which is this repo's convention for features.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        \"\"\"With enabled=False a sync function is called exactly once and its result returned.\"\"\"", "new_string": "        \"\"\"With enabled=False a sync function is called once and its result returned.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat releasenotes/notes/add-async-actions-b249c527d99723bb.yaml", "description": "Read an existing release note for format"}
[tool_result] ---
features:
  - |
    Added the ability to use async functions for retries. This way, you can now use
    asyncio coroutines for retry strategy predicates.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/releasenotes/notes/add-enabled-parameter-3f8c1a2d9e7b5c60.yaml", "content": "---\nfeatures:\n  - |\n    Added an ``enabled`` parameter (default ``True``) to ``Retrying``,\n    ``AsyncRetrying`` and the ``@retry`` decorator. With ``enabled=False`` the\n    decorated function is called directly, exactly once, with no retry logic,\n    and any exception it raises propagates unchanged. This is useful during\n    development and testing.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-fd67065479be/20261023-160639-feature-add-an-enabled-parameter/base-1/releasenotes/notes/add-enabled-parameter-3f8c1a2d9e7b5c60.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Final test run and status check"}
[tool_result] ..................                                                       [100%]
149 passed, 1 skipped, 12 subtests passed in 1.76s
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 M tests/test_tornado.py
?? releasenotes/notes/add-enabled-parameter-3f8c1a2d9e7b5c60.yaml
[assistant] `enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`. With `enabled=False` the function runs once, returns its result, and any exception propagates unchanged. The test suite passes: 149 passed, 1 skipped (baseline was 139 passed, 1 skipped).

**Changes**
- **`tenacity/__init__.py`**: `enabled: bool = True` on `BaseRetrying`, carried through `copy()` so `retry_with()` keeps it. `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `@retry` overloads gained the parameter; it reaches the constructor through `**dkw`.
- **`tenacity/asyncio/__init__.py`**: `Asyn
…[673 chars elided]…
()`, so `statistics` stays empty when disabled.
- The `for attempt in Retrying(...)` / `async for` iteration form is not changed. The request talked about decorated functions, and making iteration yield exactly one attempt while still propagating exceptions would need more machinery. Say if you want it covered.
- I didn't add a section to `doc/source/index.rst` or `README.rst`; the release note is the only documentation.

**Not verified**
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. I checked line lengths by hand.
- I haven't committed anything.
