# trajectory base-1

final message:
`enabled=False` now makes `Retrying`, `AsyncRetrying`, and `@retry` call the function once, with no retry logic, and let its exception propagate unchanged. The full suite passes (148 passed, 1 skipped; I did not check what the skip is). Nothing is committed.

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` on `BaseRetrying.__init__`, carried through `copy()` so `retry_with(...)` and the decorator's per-call copies keep it. `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `retry()` overloads accept `enabled`.
- `tenacity/asyncio/__init__.py`: same for `AsyncRetrying`. It awaits coroutine functions and calls sync ones directly.
- `tenacity/tornadoweb.py`: the same short-circuit. The flag would otherwise be silently ignored by `TornadoRetrying`, which `@retry` picks for tornado coroutines.
- Tests: `TestEnabled` in `tests/test_tenacity.py` and `tests/test_asyncio.py`, and `test_disabled_calls_once` in `tests/test_tornado.py`. They cover the decorator, the call path, the iterator path, `retry_with(enabled=True)`, and the default.
- Release note: `releasenotes/notes/add-enabled-parameter-36b4ab7e813af358.yaml`.

**Choices I made that you may want to change**
- With `enabled=False`, the `for attempt in Retrying(enabled=False):` form runs one attempt and re-raises a failure. The `before` hook still runs once on that path. The call path skips all hooks and statistics.
- `enabled` is appended as the last parameter everywhere.

**Verification**
- New tests: 9 pass on the current code.
- Fail-on-base: all 9 fail on HEAD, reporting `unexpected keyword argument 'enabled'`. That shows the tests target the new parameter. It does not show the old behaviour being wrong, since the old code has no such parameter.
- mypy and ruff were not run; the project interpreter does not have them installed.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[6662 chars elided]…
n> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls && ls releasenotes/notes | tail -5 && cat memory.md 2>/dev/null | head -20; ls <work>/env-tenacity/bin/python 2>&1", "description": "Check repo state, notes, and project interpreter"}
[tool_result] 594b04d lithify: probe base
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
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
<work>/env-tenacity/bin/python
[assistant] The skill is loaded. Next I'll read the retry entry points, the async variant, and the fail-on-base script it references.
[tool_use Bash] {"command": "grep -n \"def retry\\|class BaseRetrying\\|class Retrying\\|def __init__\\|def wraps\\|def __call__\\|def wrapped_f\\|def wrap\\|def begin\\|def iter\\|def __iter__\\|sleep\\|retry_error_callback\\|wrapped_f\\|def copy\" tenacity/__init__.py | head -120; echo ---; cat tenacity/asyncio/__init__.py | grep -n \"class \\|def \\|wrapped_f\\|retry_with\\|copy\\|_wrap\" | head -80; echo ---; ls -la .lithify/harness/skills/tenacity-change-contract/scripts/ 2>&1; ls .claude/skills/tenacity-change-contract/ 2>&1", "description": "Locate retry entry points and check fail-on-base script"}
[tool_result] 36:# Import all built-in before sleep strategies for easier usage.
37:from .before_sleep import before_sleep_log, before_sleep_nothing
40:from .nap import sleep, sleep_using_event
165:    REPR_FIELDS = ("sleep",)
168:    def __init__(self, sleep: t.SupportsFloat) -> None:
169:        self.sleep = float(sleep)
182:    def __init__(self, last_attempt: "Future") -> None:
198:    def __init__(self, retry_state: "RetryCallState"):
229:class BaseRetrying(ABC):
230:    def __init__(
232:        sleep: 
…[5112 chars elided]…
type-var]
199:        async_wrapped.retry = self  # type: ignore[attr-defined]
200:        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
201:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
203:        return t.cast("_RetryDecorated[P, R]", async_wrapped)
---
total 16
drwxr-xr-x@ 3 user  staff    96 Oct 23 16:17 .
drwxr-xr-x@ 4 user  staff   128 Oct 23 16:17 ..
-rw-r--r--@ 1 user  staff  4214 Oct 23 16:15 fails_on_base.py
SKILL.md
scripts
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 225, "limit": 300}
[tool_result] 225	    ) -> bool | None:
226	        return self.__exit__(exc_type, exc_value, traceback)
227	
228	
229	class BaseRetrying(ABC):
230	    def __init__(
231	        self,
232	        sleep: t.Callable[[int | float], None] = sleep,
233	        stop: "StopBaseT" = stop_never,
234	        wait: "WaitBaseT" = wait_none(),
235	        retry: "RetryBaseT" = retry_if_exception_type(),
236	        before: t.Callable[["RetryCallState"], None] = before_nothing,
237	        after: t.Callable[["RetryCallStat
…[11673 chars elided]…
__init__()
511	        self.attempt_number = attempt_number
512	
513	    @property
514	    def failed(self) -> bool:
515	        """Return whether a exception is being held in this future."""
516	        return self.exception() is not None
517	
518	    @classmethod
519	    def construct(
520	        cls, attempt_number: int, value: t.Any, has_exception: bool
521	    ) -> "Future":
522	        """Construct a new Future object."""
523	        fut = cls(attempt_number)
524	        if has_exception:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "offset": 74, "limit": 135}
[tool_result] 74	class AsyncRetrying(BaseRetrying):
75	    def __init__(
76	        self,
77	        sleep: t.Callable[
78	            [int | float], None | t.Awaitable[None]
79	        ] = _portable_async_sleep,
80	        stop: "StopBaseT" = tenacity.stop.stop_never,
81	        wait: "WaitBaseT" = tenacity.wait.wait_none(),
82	        retry: "SyncRetryBaseT | RetryBaseT" = tenacity.retry_if_exception_type(),
83	        before: t.Callable[
84	            ["RetryCallState"], None | t.Awaitable[None]
85	      
…[5101 chars elided]…
defined]
196	            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
197	
198	        # Preserve attributes
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "offset": 525, "limit": 190}
[tool_result] 525	            fut.set_exception(value)
526	        else:
527	            fut.set_result(value)
528	        return fut
529	
530	
531	class RetryCallState:
532	    """State related to a single call wrapped with Retrying."""
533	
534	    def __init__(
535	        self,
536	        retry_object: BaseRetrying,
537	        fn: WrappedFn | None,
538	        args: t.Any,
539	        kwargs: t.Any,
540	    ) -> None:
541	        #: Retry call start timestamp
542	        self.start_time = time.monotonic
…[6503 chars elided]…
ss__.__name__}) as callable argument, "
704	                f"this will probably hang indefinitely (did you mean retry={f.__class__.__name__}(...)?)",
705	                stacklevel=2,
706	            )
707	        r: BaseRetrying
708	        sleep = dkw.get("sleep")
709	        if _utils.is_coroutine_callable(f) or (
710	            sleep is not None and _utils.is_coroutine_callable(sleep)
711	        ):
712	            r = AsyncRetrying(*dargs, **dkw)
713	        elif (
714	            tornado
[assistant] The sync and async `__call__` paths and `copy()` are clear. Now the rest of the `retry()` decorator and the places that construct retry objects.
[tool_use Bash] {"command": "sed -n 712,730p tenacity/__init__.py; echo ---; grep -rn \"Retrying(\\|\\.copy(\" tenacity/ | grep -v \"^tenacity/__init__.py:2[5-9][0-9]:\" ; echo ---; grep -rn \"reraise\" doc/source/*.rst | head; echo ---; grep -n \"class Test\\|def test_retry_function_attributes\\|def test_retry_as_decorator\\|def test_copy\" tests/test_tenacity.py | head -60; echo ---; cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml; cat tests/test_utils.py | head -5", "description": "Read decorator tail, find constructors, and style refs"}
[tool_result]             r = AsyncRetrying(*dargs, **dkw)
        elif (
            tornado
            and hasattr(tornado.gen, "is_coroutine_function")
            and tornado.gen.is_coroutine_function(f)
        ):
            r = TornadoRetrying(*dargs, **dkw)
        else:
            r = Retrying(*dargs, **dkw)

        return r.wraps(f)

    return wrap


from tenacity.asyncio import AsyncRetrying  # noqa: E402

if tornado:
    from tenacity.tornadoweb import TornadoRetrying
---
tenacity/__init__.py:
…[1366 chars elided]…
tions(unittest.TestCase):
1668:class TestStatistics(unittest.TestCase):
1689:class TestRetryErrorCallback(unittest.TestCase):
1722:class TestContextManager(unittest.TestCase):
1777:class TestInvokeAsCallable:
1847:class TestRetryException(unittest.TestCase):
1857:class TestRetryTyping(unittest.TestCase):
1892:class TestMockingSleep:
---
---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
import functools

from tenacity import _utils
[tool_use Bash] {"command": "cat tenacity/tornadoweb.py | sed -n 20,80p; echo ---; sed -n 1,60p .claude/skills/tenacity-change-contract/scripts/fails_on_base.py; echo ---; sed -n 1722,1776p tests/test_tenacity.py; echo; grep -n \"^class \\|^def \\|^import\\|^from\" tests/test_asyncio.py | head -30", "description": "Read tornado retrying, fail-on-base usage, and test style"}
[tool_result] from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState

if typing.TYPE_CHECKING:
    from tornado.concurrent import Future

_RetValT = typing.TypeVar("_RetValT")


class TornadoRetrying(BaseRetrying):
    sleep: typing.Callable[..., "Future[None]"]

    def __init__(
        self,
        sleep: "typing.Callable[[float], Future[None]]" = gen.sleep,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep

    @gen.coroutine
    def
…[5075 chars elided]…
:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
54:def asynctest(callable_: _F) -> Callable[..., Any]:
79:class TestAsyncio(unittest.TestCase):
164:class TestTrio(unittest.TestCase):
178:class TestContextManager(unittest.TestCase):
427:class TestDecoratorWrapper(unittest.TestCase):
496:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
[assistant] I have what I need. Plan:

- Add `enabled: bool = True` to `BaseRetrying.__init__` and `copy()`, so `retry_with` and the decorator's per-call copies carry it.
- `Retrying.__call__` and `AsyncRetrying.__call__` short-circuit to a single direct call when disabled.
- The iterator path (`for attempt in Retrying(enabled=False)`) runs one attempt and re-raises on failure, so it does not retry either.
- Add the parameter to the `retry()` overloads.
- Also short-circuit `TornadoRetrying.__call__`, so the flag is not silently ignored there.

Starting with the base class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        
…[409 chars elided]…
elf.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":", "new_string": "        name: str | None | object = _unset,\n        enabled: bool | object = _unset,\n    ) -> \"Self\":"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "            name=_first_set(name, self._name),\n        )", "new_string": "            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    def _begin_iter(self, retry_state: \"RetryCallState\") -> None:\n        self.iter_state.reset()\n\n        fut = retry_state.outcome\n        if fut is None:\n            if self.before is not None:\n           
…[279 chars elided]…
      if fut is None:\n            if self.before is not None:\n                self._add_action_func(self.before)\n            self._add_action_func(lambda rs: DoAttempt())\n            return\n\n        if not self.enabled:\n            # Disabled: a single attempt, so surface its outcome without retrying.\n            self._add_action_func(lambda rs: rs.outcome.result())\n            return\n"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        self, fn: t.Callable[..., WrappedFnReturnT],\n        *args: t.Any,\n        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn
…[268 chars elided]…
WrappedFnReturnT],\n        *args: t.Any,\n        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] The last edit was a no-op I attempted by mistake, so nothing changed there. Now the sync `Retrying.__call__` short-circuit, plus the `retry()` overloads.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[956 chars elided]…
     except BaseException:\n                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]\n                else:\n                    retry_state.set_result(result)\n            elif isinstance(do, DoSleep):\n                retry_state.prepare_for_next_attempt()\n                self.sleep(do)\n            else:\n                return do  # type: ignore[no-any-return]"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async side: the `AsyncRetrying` constructor and its `__call__` short-circuit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1103 chars elided]…
            name=name,\n            enabled=enabled,\n        )\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            if _utils.is_coroutine_callable(fn):\n                return await fn(*args, **kwargs)\n            return fn(*args, **kwargs)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next, the Tornado `__call__` and whether `tornado` is installed in the project interpreter, so I know whether I can test it.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"import tornado; print(tornado.version)\" 2>&1 | tail -1; $PY -c \"import trio\" 2>&1 | tail -1; sed -n 1,20p tenacity/tornadoweb.py | grep -n \"import\"", "description": "Check whether tornado is installed in project interpreter"}
[tool_result] 6.6
ModuleNotFoundError: No module named 'trio'
15:import sys
16:import typing
18:from tornado import gen
20:from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState
[assistant] Tornado 6.6 is installed, so the Tornado path can be tested too. Adding the same short-circuit there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            raise gen.Return((yield fn(*args, **kwargs)))\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Now the tests. I'll check the existing async test conventions and find the Tornado test module.
[tool_use Bash] {"command": "ls tests; sed -n 54,78p tests/test_asyncio.py; sed -n 427,445p tests/test_asyncio.py; grep -n \"tornado\" tests/*.py | head -5", "description": "Read async test helpers and tornado test location"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
def asynctest(callable_: _F) -> Callable[..., Any]:
    @wraps(callable_)
    def wrapper(*a: Any, **kw: Any) -> Any:
        return asyncio.run(callable_(*a, **kw))

    return wrapper


async def _async_function(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry
async def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Any:
    await as
…[833 chars elided]…

            "delay_since_first_attempt": mock.ANY,
            "idle_for": mock.ANY,
            "start_time": mock.ANY,
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
[assistant] I have the conventions. Checking the end of `tests/test_tenacity.py` and the Tornado test structure so I can append new classes in place.
[tool_use Bash] {"command": "tail -n 12 tests/test_tenacity.py | cat -A | cut -c1-100 | tail -n 12; echo ---; sed -n 19,60p tests/test_tornado.py; echo ---; tail -n 8 tests/test_tornado.py; echo ---; tail -n 6 tests/test_asyncio.py", "description": "Inspect test file endings and tornado test structure"}
[tool_result] cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
---
from tornado import gen, testing

from tenacity import RetryError, retry, stop_after_attempt, tornadoweb

from .test_tenacity import NoIOErrorAfterCount


@retry
@gen.coroutine
def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()


@retry(stop=stop_after_attempt(2))
@gen.coroutine
def _retryable_coroutine_with_2_attempts(
    thing: NoIOErrorAfterCount,
) -> Ge
…[554 chars elided]…
rorAfterCount(2)
        try:
            yield _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tornadoweb.TornadoRetrying())
---
                pass

        finally:
            gen.is_coroutine_function = old_attr


if __name__ == "__main__":
    unittest.main()
---
        assert result is True
        assert mock_sleep.await_count == 2


if __name__ == "__main__":
    unittest.main()
[tool_use Bash] {"command": "grep -n '__main__' tests/test_tenacity.py tests/test_asyncio.py tests/test_tornado.py; sed -n 1,30p tests/test_tenacity.py | grep -n import", "description": "Find main guards and imports in test modules"}
[tool_result] tests/test_asyncio.py:517:if __name__ == "__main__":
tests/test_tornado.py:77:if __name__ == "__main__":
tests/test_tenacity.py:1933:if __name__ == "__main__":
16:import contextlib
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py", "old_string": "if __name__ == \"__main__\":", "new_string": "class TestEnabled(unittest.TestCase):\n    def test_enabled_defaults_to_true(self) -> None:\n        self.assertTrue(tenacity.Retrying().enabled)\n\n    def test_disabl
…[1214 chars elided]…
       def flaky() -> int:\n            calls.append(1)\n            if len(calls) < 3:\n                raise ValueError(\"retry me\")\n            return len(calls)\n\n        reenabled = flaky.retry_with(\n            enabled=True, stop=tenacity.stop_after_attempt(3)\n        )\n        self.assertEqual(reenabled(), 3)\n        self.assertEqual(len(calls), 3)\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async tests, appended before the `test_asyncio.py` main guard.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "if __name__ == \"__main__\":", "new_string": "class TestEnabled(unittest.TestCase):\n    @asynctest\n    async def test_disabled_decorator_awaits_once_and_propagates(self) -> None:\n        calls: list[int] = []\n  
…[936 chars elided]…
syncRetrying(enabled=False, stop=stop_after_attempt(5))\n\n        async def run() -> None:\n            async for attempt in retrying:\n                with attempt:\n                    calls.append(1)\n                    raise ValueError(\"boom\")\n\n        with self.assertRaises(ValueError):\n            await run()\n        self.assertEqual(len(calls), 1)\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] One mistake to fix: `tasyncio` has no `retry` decorator. The module-level `retry` already dispatches async functions to `AsyncRetrying`, so I'll use it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py", "old_string": "        @tasyncio.retry(enabled=False, stop=stop_after_attempt(5))", "new_string": "        @retry(enabled=False, stop=stop_after_attempt(5))"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Last, a Tornado test, so the Tornado short-circuit is covered too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())", "new_string": "    @testing.gen_test\n    def test_disabled_calls_once(self) -> Generator[Any, Any, None]:\n        calls: list[int] = [
…[93 chars elided]…
lls.append(1)\n            yield gen.sleep(0.00001)\n            raise ValueError(\"boom\")\n\n        retrying = tornadoweb.TornadoRetrying(\n            enabled=False, stop=stop_after_attempt(5)\n        )\n        with self.assertRaises(ValueError):\n            yield retrying(fail)\n        assert len(calls) == 1\n\n    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[assistant] Before running anything, I'll write the release note the project contract requires. The filename needs 16 random hex characters, so I'll generate them.
[tool_use Bash] {"command": "openssl rand -hex 8", "description": "Generate random suffix for release note filename"}
[tool_result] 36b4ab7e813af358
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/releasenotes/notes/add-enabled-parameter-36b4ab7e813af358.yaml", "content": "---\nfeatures:\n  - |\n    Add an ``enabled`` parameter (default ``True``) to ``Retrying``,\n    ``AsyncRetrying`` and the ``@retry`` decorator. With ``enabled=False`` the\n    decorated function is called directly, exactly once, with no retry logic,\n    and any exception it raises propagates unchanged. This is useful during\n    development and testing.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-164433-feature-add-an-enabled-parameter/base-1/releasenotes/notes/add-enabled-parameter-36b4ab7e813af358.yaml (file state is current in your context — no need to Read it back)
[assistant] Release note is in place. Now the new tests against the new code.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled tests/test_tornado.py::TestTornado::test_disabled_calls_once 2>&1 | tail -n 30", "description": "Run the new enabled-parameter tests"}
[tool_result] .........                                                                [100%]
9 passed in 0.06s
[assistant] All 9 new tests pass. Next is the fail-on-base check the contract requires, run against HEAD.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .claude/skills/tenacity-change-contract/scripts/fails_on_base.py tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestEnabled tests/test_tornado.py::TestTornado::test_disabled_calls_once 2>&1 | tail -n 40; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run fail-on-base check for new tests against HEAD"}
[tool_result]         @gen.coroutine
        def fail() -> Generator[Any, Any, None]:
            calls.append(1)
            yield gen.sleep(0.00001)
            raise ValueError("boom")
    
>       retrying = tornadoweb.TornadoRetrying(
            enabled=False, stop=stop_after_attempt(5)
        )

tests/test_tornado.py:69: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <[AttributeError("'TornadoRetrying' object has no attribute 'stop'") raised in repr()] Tornad
…[997 chars elided]…
test_asyncio.py::TestEnabled::test_disabled_async_for_runs_once
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_call_with_sync_function_runs_once
FAILED tests/test_asyncio.py::TestEnabled::test_disabled_decorator_awaits_once_and_propagates
FAILED tests/test_tornado.py::TestTornado::test_disabled_calls_once - TypeErr...
9 failed in 0.12s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
exit=
[assistant] The check reports GOOD: all 9 fail on HEAD. They fail with `TypeError: ... unexpected keyword argument 'enabled'`, because the parameter does not exist there yet. That proves the tests exercise the new parameter, not the behaviour on the old code specifically. Now the full suite, run once after the final edit.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 15; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ...........s........................................................................................................................ [ 88%]
.................                                                        [100%]
148 passed, 1 skipped, 12 subtests passed in 1.81s
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 M tests/test_tornado.py
?? releasenotes/notes/add-enabled-parameter-36b4ab7e813af358.yaml
[assistant] `enabled=False` now makes `Retrying`, `AsyncRetrying`, and `@retry` call the function once, with no retry logic, and let its exception propagate unchanged. The full suite passes (148 passed, 1 skipped; I did not check what the skip is). Nothing is committed.

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` on `BaseRetrying.__init__`, carried through `copy()` so `retry_with(...)` and the decorator's per-call copies keep it. `Retrying.__call__` returns `fn(*args, **kwargs)` directly when disabled. The `retry()` overloads accept `enabled`.
- `tenacity/asyncio/__init__.py`: same 
…[654 chars elided]…
tempt in Retrying(enabled=False):` form runs one attempt and re-raises a failure. The `before` hook still runs once on that path. The call path skips all hooks and statistics.
- `enabled` is appended as the last parameter everywhere.

**Verification**
- New tests: 9 pass on the current code.
- Fail-on-base: all 9 fail on HEAD, reporting `unexpected keyword argument 'enabled'`. That shows the tests target the new parameter. It does not show the old behaviour being wrong, since the old code has no such parameter.
- mypy and ruff were not run; the project interpreter does not have them installed.
