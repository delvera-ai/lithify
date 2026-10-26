# trajectory dom-1

final message:
`Retrying` objects (including ones that have already run) and the built-in retry strategies now pickle and restore to working objects. A `Retrying` passed through a spawn-context `Pool` runs in the worker. Changes are left uncommitted in the working tree.

**What changed**
- **`tenacity/retry.py`**: `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` and `retry_if_not_exception_message` used lambdas and nested functions as predicates, which can't be pickled. They now bind module-level functions with `functools.partial`. Behaviour is unchanged.
- **`tenacity/__init__.py`**: `BaseRetrying` gets `__getstate__`/`__setstate__`. The `threading.local` is dropped and rebuilt on restore. The calling thread's statistics are carried over, and per-run `iter_state` is not.
- **`tests/test_tenacity.py`**: new `TestPickling` class with four tests. Three failed on the unfixed code with `Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'`, the reported error. The fourth is a guard for stop/wait strategies, which were already picklable.
- **`releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml`**: a `fixes:` note. No `index.rst` change, since this is a bug fix that adds no documented usage.

**Verification**
- Full suite via `run_tests.py`: `exit=0`, 150 passed, 1 skipped. The skip is in the existing suite; I did not check its reason.
- `check_changed.py`: exit 0, 0 problems. It flagged one over-long line in my test, which I fixed.
- Not run: ruff and mypy, since they are unavailable here.
- Manual check: a `@retry` function and a used `Retrying` both work through `Pool.map` with the spawn context. `AsyncRetrying` also round-trips.

**Decisions for you to review**
- **Behaviour change in `copy.copy(retrying)`**: the copy used to share the original's thread-local statistics. Now it gets its own statistics dict, initialised from the original's. I think that is the correct copy semantics, but it is observable.
- **Statistics survive pickling**: a restored object reports the statistics of the thread that pickled it. If you'd rather restore a clean object, drop the `_statistics` entry from `__getstate__`.
- **Left unpicklable on purpose**: the logging callbacks from `before_log`/`after_log`/`before_sleep_log`, `stop_when_event_set`, `sleep_using_event`, and user callables passed to `retry_if_result`, `retry_if_exception` and similar. Those hold user or OS objects, so making them picklable would need a design decision.

## events
[assistant] I'll start by reading the project's change-contract skill, since pickling support on `Retrying` is listed as a trigger for it.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; cat .lithify/harness/scripts/run_tests.py | head -40; echo ---; ls tenacity; echo ---; cat tenacity/__init__.py | head -150", "description": "Read change-contract skill and package layout"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or 
…[19478 chars elided]…
yAgain(Exception):
    """Always retry the executed function when raised."""


NO_RESULT = object()


class DoAttempt:
    pass


class DoSleep(float):
    pass


class BaseAction:
    """Base class for representing actions to take by retry object.

    Concrete implementations must define:
    - __init__: to initialize all necessary fields
    - REPR_FIELDS: class variable specifying attributes to include in repr(self)
    - NAME: for identification in retry object methods and callbacks
    """
[assistant] The skill says strategy classes must keep constructor args as plain attributes, and that `Retrying` needs `__getstate__`/`__setstate__` with a fresh `_local`. Next I'll read the core `BaseRetrying` code and the strategy classes that build lambdas in `__init__`.
[tool_use Bash] {"command": "grep -n \"_local\\|class \\|def __init__\\|def copy\\|def statistics\\|def iter_state\\|def __getstate__\\|def __setstate__\\|def __copy__\" tenacity/__init__.py | head -80; echo ---; grep -nE \"lambda|^ {8,}def \" tenacity/retry.py tenacity/stop.py tenacity/wait.py tenacity/asyncio/retry.py; echo ---; grep -n \"_local\\|__init__\\|self.sleep\" tenacity/asyncio/__init__.py tenacity/tornadoweb.py | head -30", "description": "Locate relevant code in tenacity package"}
[tool_result] 112:class IterState:
127:class TryAgain(Exception):
134:class DoAttempt:
138:class DoSleep(float):
142:class BaseAction:
143:    """Base class for representing actions to take by retry object.
147:    - REPR_FIELDS: class variable specifying attributes to include in repr(self)
164:class RetryAction(BaseAction):
168:    def __init__(self, sleep: t.SupportsFloat) -> None:
179:class RetryError(Exception):
182:    def __init__(self, last_attempt: "Future") -> None:
195:class AttemptManager:
198:    
…[1677 chars elided]…
nadoweb.py:31:    def __init__(
tenacity/tornadoweb.py:36:        super().__init__(**kwargs)
tenacity/tornadoweb.py:37:        self.sleep = sleep
tenacity/tornadoweb.py:60:                yield self.sleep(do)
tenacity/asyncio/__init__.py:75:    def __init__(
tenacity/asyncio/__init__.py:96:        super().__init__(
tenacity/asyncio/__init__.py:132:                await self.sleep(do)  # type: ignore[misc]
tenacity/asyncio/__init__.py:182:                await self.sleep(do)  # type: ignore[misc]
[tool_use Bash] {"command": "sed -n 229,345p tenacity/__init__.py; echo ---; sed -n 484,512p tenacity/__init__.py", "description": "Read BaseRetrying init, copy, statistics"}
[tool_result] class BaseRetrying(ABC):
    def __init__(
        self,
        sleep: t.Callable[[int | float], None] = sleep,
        stop: "StopBaseT" = stop_never,
        wait: "WaitBaseT" = wait_none(),
        retry: "RetryBaseT" = retry_if_exception_type(),
        before: t.Callable[["RetryCallState"], None] = before_nothing,
        after: t.Callable[["RetryCallState"], None] = after_nothing,
        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
        reraise: bool = False,
    
…[4960 chars elided]…
      try:
                    result = fn(*args, **kwargs)
                except BaseException:
                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
                else:
                    retry_state.set_result(result)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                return do  # type: ignore[no-any-return]


class Future(futures.Future[t.Any]):
[tool_use Bash] {"command": "sed -n 1,140p tenacity/retry.py; echo ...; sed -n 200,270p tenacity/retry.py", "description": "Read retry strategy classes"}
[tool_result] # Copyright 2016–2021 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS O
…[5873 chars elided]…
cate(*args_, **kwargs_)

    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        if not retry_state.outcome.failed:
            return True

        exception = retry_state.outcome.exception()
        if exception is None:
            raise RuntimeError("outcome failed but the exception is None")
        return self.predicate(exception)


class retry_any(retry_base):
[assistant] The lambdas in `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type` and `retry_if_not_exception_message`, plus the nested `message_fnc`/`match_fnc` closures, are the unpicklable parts. Before writing anything I'll check the project python location, the existing pickle test, and the default callables that `BaseRetrying` stores.
[tool_use Bash] {"command": "ls -a .lithify; cat .lithify/memory.md 2>/dev/null | head -30; echo ---; grep -n \"pickle\" -A12 tests/test_tenacity.py | head -40; echo ---; grep -n \"^def \\|^async def \" tenacity/nap.py tenacity/before.py tenacity/after.py tenacity/before_sleep.py; echo ---; sed -n 60,100p tenacity/asyncio/__init__.py; ls releasenotes/notes | tail -3", "description": "Check project python, pickle tests and default callables"}
[tool_result] .
..
harness
library
state.json
---
1927:    def test_retry_error_is_pickleable(self) -> None:
1928:        import pickle
1929-
1930-        expected = RetryError(last_attempt=123)  # type: ignore[arg-type]
1931:        pickled = pickle.dumps(expected)
1932:        actual = pickle.loads(pickled)
1933-        self.assertEqual(expected.last_attempt, actual.last_attempt)
1934-
1935-
1936-class TestRetryTyping(unittest.TestCase):
1937-    def test_retry_type_annotations(self) -> None:
1938-        "
…[1848 chars elided]…
        retry_error_callback: t.Callable[["RetryCallState"], t.Any | t.Awaitable[t.Any]]
        | None = None,
        name: str | None = None,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            sleep=sleep,  # type: ignore[arg-type]
            stop=stop,
            wait=wait,
            retry=retry,  # type: ignore[arg-type]
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The project python is named in CLAUDE.md. I'll confirm it exists, then write the regression tests first so I can see them fail on the unfixed code.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -l $PY && $PY -c \"import sys;print(sys.version)\"; $PY -c \"import tenacity;print(tenacity.__file__)\"; grep -n \"class TestStatistics\" -A5 tests/test_tenacity.py | head; grep -n \"^class \" tests/test_tenacity.py | head -60", "description": "Verify project python and list test classes"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/__init__.py
1412:class TestStatisticsKey
…[998 chars elided]…
):
1412:class TestStatisticsKeys:
1429:class TestEnabled:
1487:class TestRetryWith:
1525:class TestBeforeAfterAttempts(unittest.TestCase):
1678:class TestReraiseExceptions(unittest.TestCase):
1747:class TestStatistics(unittest.TestCase):
1768:class TestRetryErrorCallback(unittest.TestCase):
1801:class TestContextManager(unittest.TestCase):
1856:class TestInvokeAsCallable:
1926:class TestRetryException(unittest.TestCase):
1936:class TestRetryTyping(unittest.TestCase):
1971:class TestMockingSleep:
[assistant] Python 3.12 is available and the tests import the working-tree `tenacity`. Next I'll check how existing tests build a `RetryCallState` so the new tests can drive strategies directly.
[tool_use Bash] {"command": "grep -n \"RetryCallState(\" tests/*.py | head -5; grep -n \"def set_exception\\|def set_result\" -A4 tenacity/__init__.py; grep -n \"^from\\|^import\" tests/test_tenacity.py; sed -n 1,30p tenacity/stop.py | grep -n import; grep -n \"class stop_when_event_set\\|class wait_exception\\|class retry_if_result\\|class wait_chain\\|class wait_combine\\|class retry_if_not_result\" tenacity/*.py", "description": "Check RetryCallState usage in tests"}
[tool_result] tests/test_tenacity.py:76:    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
tests/test_tenacity.py:100:        rs = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
tests/test_tenacity.py:153:        rs = RetryCallState(r, None, (), {})
tests/test_tenacity.py:159:        rs = RetryCallState(r, None, (), {})
594:    def set_result(self, val: t.Any) -> None:
595-        ts = time.monotonic()
596-        fut = Future(self.attempt_number)
597-        fut.set_
…[662 chars elided]…
enacity.retry import retry_all, retry_any
16:import abc
17:import typing
19:from tenacity import _utils
22:    import threading
24:    from tenacity import RetryCallState
tenacity/stop.py:74:class stop_when_event_set(stop_base):
tenacity/retry.py:179:class retry_if_result(retry_base):
tenacity/retry.py:194:class retry_if_not_result(retry_base):
tenacity/wait.py:79:class wait_combine(wait_base):
tenacity/wait.py:89:class wait_chain(wait_base):
tenacity/wait.py:114:class wait_exception(wait_base):
[assistant] I have what I need. Next I'll read the insertion point in the test file, then add a `TestPickling` class before `TestRetryTyping`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "offset": 1924, "limit": 14}
[tool_result] 1924	
1925	
1926	class TestRetryException(unittest.TestCase):
1927	    def test_retry_error_is_pickleable(self) -> None:
1928	        import pickle
1929	
1930	        expected = RetryError(last_attempt=123)  # type: ignore[arg-type]
1931	        pickled = pickle.dumps(expected)
1932	        actual = pickle.loads(pickled)
1933	        self.assertEqual(expected.last_attempt, actual.last_attempt)
1934	
1935	
1936	class TestRetryTyping(unittest.TestCase):
1937	    def test_retry_type_annotations(self) -> None:
[assistant] Before writing the assertions I need two attribute names: the stop strategy's attempt limit, and what `set_exception` expects. I'll check both.
[tool_use Bash] {"command": "grep -n \"max_attempt_number =\\|self.max_delay =\" tenacity/stop.py; sed -n 600,615p tenacity/__init__.py; sed -n 70,80p tests/test_tenacity.py", "description": "Check stop attribute names and set_exception"}
[tool_result] 88:        self.max_attempt_number = max_attempt_number
105:        self.max_delay = _utils.to_seconds(max_delay)
122:        self.max_delay = _utils.to_seconds(max_delay)
    def set_exception(
        self,
        exc_info: tuple[
            type[BaseException], BaseException, "types.TracebackType| None"
        ],
    ) -> None:
        ts = time.monotonic()
        fut = Future(self.attempt_number)
        fut.set_exception(exc_info[1])
        self.outcome, self.outcome_timestamp = fut, t
…[100 chars elided]…
       elif self.outcome.failed:
            exception = self.outcome.exception()
        raise _make_unset_exception(
            "wait/stop",
            previous_attempt_number=previous_attempt_number,
            delay_since_first_attempt=delay_since_first_attempt,
        )

    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
    retry_state.attempt_number = previous_attempt_number
    if last_result is not None:
        retry_state.outcome = last_result
    else:
[assistant] Both names check out. Now I'll add the regression tests: a round-trip for a bare `Retrying`, a used one with statistics, and behaviour-equivalence checks for the retry, stop and wait strategies.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "class TestRetryTyping(unittest.TestCase):\n    def test_retry_type_annotations(self) -> None:", "new_string": "def _is_value_error(exc: BaseException) -> bool:\n    return isinstance(exc, ValueError)\n\n\ndef _faile
…[4563 chars elided]…
= RetryCallState(None, None, (), {})  # type: ignore[arg-type]\n\n        for strategy in strategies:\n            restored = pickle.loads(pickle.dumps(strategy))\n            with self.subTest(strategy=repr(strategy)):\n                self.assertEqual(restored(retry_state), strategy(retry_state))\n\n\nclass TestRetryTyping(unittest.TestCase):\n    def test_retry_type_annotations(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] One thing to fix before running: `tenacity.retry` is the decorator function, not the submodule, so `tenacity.retry.retry_base` would fail. `retry_base` is exported from the package, so I'll use that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        strategies: list[tenacity.retry.retry_base] = [", "new_string": "        strategies: list[tenacity.retry_base] = ["}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the new class alone against the unfixed code, through the project's harness script as CLAUDE.md requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling 2>&1 | tail -60", "description": "Run new pickling tests against unfixed code"}
[tool_result]         if retry_state.seconds_since_start is None:
>           raise RuntimeError("__call__() called but seconds_since_start is not set")
E           RuntimeError: __call__() called but seconds_since_start is not set

tenacity/stop.py:109: RuntimeError
_______ TestPickling.test_used_retrying_keeps_statistics_and_still_runs ________

self = <tests.test_tenacity.TestPickling testMethod=test_used_retrying_keeps_statistics_and_still_runs>

    def test_used_retrying_keeps_statistics_and_still_runs(
…[1225 chars elided]…
0x10b366d20>') tests/test_tenacity.py::TestPickling::test_stop_and_wait_strategies_pickle_and_behave_the_same
SUBFAILED(strategy='<tenacity.stop.stop_any object at 0x10b366ab0>') tests/test_tenacity.py::TestPickling::test_stop_and_wait_strategies_pickle_and_behave_the_same
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_keeps_statistics_and_still_runs
================ 6 failed, 1 passed, 8 subtests passed in 0.11s ================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Some of these failures are mistakes in my tests, not the bug. Stop strategies need `seconds_since_start` set on the state, and I guessed at the statistics keys. I'll look at the real pickling errors and the statistics keys before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; grep -n \"PicklingError\\|AttributeError: Can\\|Can't pickle\\|Can't get\" /tmp/run_tests.log | head -8; $PY -c \"\nimport tenacity\ncalls=[]\n@tenacity.retry(stop=tenacity.stop_after_attempt(5), wait=tenacity.wait_fixed(0))\ndef f():\n    calls.append(1)\n    if len(calls)<2: raise ValueError\n    return 'ok'\nf()\nprint(f.retry.statistics)\n\"", "description": "Inspect pickling errors and statistics keys"}
[tool_result] 45:E           AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
64:E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
{}
[assistant] The reported error reproduces exactly: `Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'`. The statistics read was my mistake: the decorated wrapper exposes the running copy's stats as `fn.statistics`, not `fn.retry.statistics`, as the skill notes. I'll switch that test to call a `Retrying` directly and set `seconds_since_start` in the stop test.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport tenacity\ncalls=[]\nr=tenacity.Retrying(stop=tenacity.stop_after_attempt(5), wait=tenacity.wait_fixed(0))\ndef f():\n    calls.append(1)\n    if len(calls)<2: raise ValueError\n    return 'ok'\nprint(r(f)); print(r.statistics)\n\"", "description": "Check statistics keys after a direct Retrying run"}
[tool_result] ok
{'start_time': 242766.167993833, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt': 6.832997314631939e-06}
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        @retry(\n            stop=tenacity.stop_after_attempt(5),\n            wait=tenacity.wait_fixed(0),\n            retry=tenacity.retry_if_exception_type(ValueError),\n        )\n        def fails_once() -> st
…[1077 chars elided]…
ok\")\n        self.assertEqual(retrying.statistics[\"attempt_number\"], 2)\n\n        actual = pickle.loads(pickle.dumps(retrying))\n\n        self.assertEqual(actual.statistics, retrying.statistics)\n        self.assertIsNot(actual.statistics, retrying.statistics)\n        self.assertEqual(actual(lambda: \"again\"), \"again\")\n        self.assertEqual(actual.statistics[\"attempt_number\"], 1)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the stop/wait test: it needs `seconds_since_start` set on the state.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]\n\n        for strategy in strategies:\n            restored = pickle.loads(pickle.dumps(strategy))\n            with self.subTest(strategy=repr(strategy)):", "new_string": "        retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]\n        retry_state.seconds_since_start = 0.0\n\n        for strategy in strategies:\n            restored = pickle.loads(pickle.dumps(strategy))\n            with self.subTest(strategy=repr(strategy)):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Re-running the class on the unfixed code. The retry-strategy and `Retrying` tests should now fail on the pickling error, and the stop/wait tests should pass.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/pk1.txt 2>&1; tail -12 /tmp/pk1.txt; grep -n \"^E  \" /tmp/run_tests.log | sort | uniq -c | head", "description": "Re-run pickling tests against unfixed code"}
[tool_result]                               ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'

tests/test_tenacity.py:1998: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickling::test_retry_strategies_pickle_and_behave_the_same
FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
FAILED tests/test_tenacity.py::TestPickling::t
…[215 chars elided]…
=================
---
exit=1 (pytest); full log: /tmp/run_tests.log
   1 117:E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
   1 44:E           AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
   1 63:E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
   1 89:E       AttributeError: property 'seconds_since_start' of 'RetryCallState' object has no setter
[assistant] `seconds_since_start` is a read-only property derived from `start_time`, so I'll set `start_time` instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        retry_state.seconds_since_start = 0.0", "new_string": "        retry_state.start_time = time.monotonic()"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/pk1.txt 2>&1; tail -8 /tmp/pk1.txt; grep \"^E  \" /tmp/run_tests.log | sort | uniq -c", "description": "Re-run pickling tests against unfixed code"}
[tool_result] FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
SUBFAILED(strategy='<tenacity.stop.stop_after_delay object at 0x10b7a6d50>') tests/test_tenacity.py::TestPickling::test_stop_and_wait_strategies_pickle_and_behave_the_same
SUBFAILED(strategy='<tenacity.stop.stop_before_delay object at 0x10b7a6d80>') tests/test_tenacity.py::TestPickling::test_stop_and_wait_strategies_pickle_and_behave_the_same
SUBFAILED(strategy='<tenacity.stop.stop_any object at 0x10b7a6d20>') tests
…[114 chars elided]…
ty.py::TestPickling::test_used_retrying_keeps_statistics_and_still_runs
================ 6 failed, 1 passed, 8 subtests passed in 0.11s ================
---
exit=1 (pytest); full log: /tmp/run_tests.log
   1 E           AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
   3 E           RuntimeError: __call__() called but seconds_since_start is not set
   2 E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
[assistant] Still failing with `seconds_since_start is not set`, so I'll read the property to see what it actually depends on.
[tool_use Bash] {"command": "grep -n \"def seconds_since_start\" -A8 tenacity/__init__.py; grep -n \"self.start_time\\|self.seconds_since_start\\|_seconds\" tenacity/__init__.py | head", "description": "Read seconds_since_start property"}
[tool_result] 583:    def seconds_since_start(self) -> float | None:
584-        if self.outcome_timestamp is None:
585-            return None
586-        return self.outcome_timestamp - self.start_time
587-
588-    def prepare_for_next_attempt(self) -> None:
589-        self.outcome = None
590-        self.outcome_timestamp = None
591-        self.attempt_number += 1
548:        self.start_time = time.monotonic()
586:        return self.outcome_timestamp - self.start_time
[assistant] The property needs an outcome timestamp, so the stop tests should use a state that has an outcome. I'll use the existing `_failed_state` helper and drop the `start_time` line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]\n        retry_state.start_time = time.monotonic()\n\n        for strategy in strategies:", "new_string": "        retry_state = _failed_state(ValueError(\"boom\"))\n\n        for strategy in strategies:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/pk1.txt 2>&1; tail -8 /tmp/pk1.txt; grep \"^E  \" /tmp/run_tests.log | sort | uniq -c", "description": "Re-run pickling tests against unfixed code"}
[tool_result] tests/test_tenacity.py:1998: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickling::test_retry_strategies_pickle_and_behave_the_same
FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_keeps_statistics_and_still_runs
=============== 3 failed, 1 passed, 11 subtests passed in 0.07s ================
---
exit=1 (pytest); full log: /tmp/run_tests.log
   1 E           AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
   2 E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
[assistant] All three failures now show the reported error, `Can't get local object '...retry_if_exception_type.__init__.<locals>.<lambda>'`. The stop/wait guard test passes on the unfixed code, which is expected: those strategies are already picklable and the test is there to keep them that way.

Now the fix. For the strategy classes I'll replace the lambdas and nested closures with module-level functions bound with `functools.partial`, as the skill prescribes. I'll read the exact lines first.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "offset": 14, "limit": 6}
[tool_result] 14	# See the License for the specific language governing permissions and
15	# limitations under the License.
16	
17	import abc
18	import re
19	import typing
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "offset": 100, "limit": 170}
[tool_result] 100	
101	
102	class retry_if_exception_type(retry_if_exception):
103	    """Retries if an exception has been raised of one or more types."""
104	
105	    def __init__(
106	        self,
107	        exception_types: type[BaseException]
108	        | tuple[type[BaseException], ...] = Exception,
109	    ) -> None:
110	        self.exception_types = exception_types
111	        super().__init__(lambda e: isinstance(e, exception_types))
112	
113	
114	class retry_if_not_exception_type(retry_if_exceptio
…[5269 chars elided]…
	
257	    def __call__(self, retry_state: "RetryCallState") -> bool:
258	        if retry_state.outcome is None:
259	            raise RuntimeError("__call__() called before outcome was set")
260	
261	        if not retry_state.outcome.failed:
262	            return True
263	
264	        exception = retry_state.outcome.exception()
265	        if exception is None:
266	            raise RuntimeError("outcome failed but the exception is None")
267	        return self.predicate(exception)
268	
269	
[assistant] I have the exact text. Making the edits now: first the `functools` import, then the module-level helpers, then each constructor.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing", "new_string": "import abc\nimport functools\nimport re\nimport typing"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "class retry_if_exception(retry_base):\n    \"\"\"Retry strategy that retries if an exception verifies a predicate.\"\"\"", "new_string": "# Predicates below are module-level so that strategies built from them can be\n# p
…[442 chars elided]…
n)\n\n\ndef _message_matches(prog: re.Pattern[str], exception: BaseException) -> bool:\n    return bool(prog.match(str(exception)))\n\n\ndef _negated(predicate: typing.Callable[[BaseException], bool], exception: BaseException) -> bool:\n    return not predicate(exception)\n\n\nclass retry_if_exception(retry_base):\n    \"\"\"Retry strategy that retries if an exception verifies a predicate.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "        self.exception_types = exception_types\n        super().__init__(lambda e: isinstance(e, exception_types))", "new_string": "        self.exception_types = exception_types\n        super().__init__(functools.partial(_is_instance_of, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "        super().__init__(lambda e: not isinstance(e, exception_types))", "new_string": "        super().__init__(functools.partial(_is_not_instance_of, exception_types))"}
[tool_result ERROR] <tool_use_error>Found 2 matches of the string to replace, but replace_all is false. To replace all occurrences, set replace_all to true. To replace only one occurrence, please provide more context to uniquely identify the instance.
String:         super().__init__(lambda e: not isinstance(e, exception_types))</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "        # set predicate\n        if message:\n\n            def message_fnc(exception: BaseException) -> bool:\n                return message == str(exception)\n\n            predicate = message_fnc\n        elif match:
…[85 chars elided]…
ception) -> bool:\n                return bool(prog.match(str(exception)))\n\n            predicate = match_fnc\n        else:", "new_string": "        # set predicate\n        if message:\n            predicate = functools.partial(_message_equals, message)\n        elif match:\n            prog = re.compile(match)\n            predicate = functools.partial(_message_matches, prog)\n        else:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "        # invert predicate\n        if_predicate = self.predicate\n        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)", "new_string": "        # invert predicate\n        self.predicate = functools.partial(_negated, self.predicate)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[assistant] The two `not isinstance` constructors share an identical line, so I'll replace both at once. I'll also wrap the `_negated` signature, which is over the 88-column limit.
[tool_use Edit] {"replace_all": true, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "        super().__init__(lambda e: not isinstance(e, exception_types))", "new_string": "        super().__init__(functools.partial(_is_not_instance_of, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated. All occurrences were successfully replaced.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py", "old_string": "def _negated(predicate: typing.Callable[[BaseException], bool], exception: BaseException) -> bool:\n    return not predicate(exception)", "new_string": "def _negated(\n    predicate: typing.Callable[[BaseException], bool], exception: BaseException\n) -> bool:\n    return not predicate(exception)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/retry.py has been updated successfully.
[assistant] Strategy classes are done. Next is `BaseRetrying`: it needs state hooks that drop the unpicklable `threading.local` and carry the current thread's statistics across. I'll read the insertion point in `tenacity/__init__.py`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/__init__.py", "offset": 282, "limit": 6}
[tool_result] 282	            before=_first_set(before, self.before),
283	            after=_first_set(after, self.after),
284	            before_sleep=_first_set(before_sleep, self.before_sleep),
285	            reraise=_first_set(reraise, self.reraise),
286	            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),
287	            retry_error_callback=_first_set(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/__init__.py", "old_string": "    def __str__(self) -> str:\n        return self._name if self._name is not None else \"<unknown>\"", "new_string": "    def __getstate__(self) -> dict[str, t.Any]:\n        state = self.__dict__.copy()\n        # t
…[195 chars elided]…
atistics\"] = dict(self.statistics)\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self._local.statistics = statistics\n\n    def __str__(self) -> str:\n        return self._name if self._name is not None else \"<unknown>\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tenacity/__init__.py has been updated successfully.
[assistant] Running the pickling class again on the fixed code.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/pk2.txt 2>&1; tail -5 /tmp/pk2.txt", "description": "Run pickling tests against fixed code"}
[tool_result] tests/test_tenacity.py::TestPickling::test_used_retrying_keeps_statistics_and_still_runs PASSED [100%]

==================== 4 passed, 63 subtests passed in 0.03s =====================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All four pickling tests pass on the fixed code. The bug report is about `multiprocessing`, so I'll also check the real scenario directly: a decorated function and a used `Retrying` sent through a spawn-context `Pool`. The check script lives in `/tmp`, outside the repo.
[tool_use Write] {"file_path": "/tmp/mp_check/mp_check.py", "content": "import multiprocessing as mp\nimport sys\n\nsys.path.insert(0, \"~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1\")\n\nimport tenacity  # noqa: E402\n\n\n@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(0))\ndef flaky_double(x: int) -> int:\n    return x *
…[188 chars elided]…
(\"spawn\")\n    with ctx.Pool(2) as pool:\n        print(\"Pool.map decorated:\", pool.map(flaky_double, [1, 2, 3]))\n\n    used = tenacity.Retrying(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(0))\n    used(lambda: 1)\n    print(\"used stats before:\", used.statistics)\n    with ctx.Pool(2) as pool:\n        print(\"Pool.map Retrying:\", pool.map(run_retrying, [used, used]))\n"}
[tool_result] File created successfully at: /tmp/mp_check/mp_check.py (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; timeout 60 $PY -I /tmp/mp_check/mp_check.py 2>&1 | tail -15; echo \"exit=$?\"", "description": "Check multiprocessing Pool with Retrying objects"}
[tool_result] (eval):1: command not found: timeout
exit=0
[assistant] This macOS shell has no `timeout` command, so I'll run the script directly.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I /tmp/mp_check/mp_check.py > /tmp/mp_check/out.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/mp_check/out.txt", "description": "Run multiprocessing check script"}
[tool_result] exit=0
Pool.map decorated: [2, 4, 6]
used stats before: {'start_time': 242839.483661375, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
Pool.map Retrying: [21, 21]
[assistant] The scenario works: a `@retry` function and a used `Retrying` both run through a spawn-context `Pool`. Since this is a user-visible bug fix, the project's change contract requires a reno release note, so I'll generate a filename with a 16-hex suffix and write it.
[tool_use Bash] {"command": "python3 -c \"import secrets;print(secrets.token_hex(8))\"", "description": "Generate hex suffix for reno note filename"}
[tool_result] c78ae4f2f53e5e80
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml", "content": "---\nfixes:\n  - |\n    ``Retrying`` objects, including ones that have already run, and the built-in\n    retry strategies can now be pickled, so ``@retry``-decorated functions can be used\n    with ``multiprocessing`` (e.g. ``Pool.map``). A restored ``Retrying`` keeps the\n    statistics of the thread that pickled it.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml (file state is current in your context — no need to Read it back)
[assistant] The fix, tests and release note are in place. Now the full suite through the harness script, read in the foreground.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full1.txt 2>&1; tail -6 /tmp/full1.txt", "description": "Run full test suite via harness script"}
[tool_result] tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 150 passed, 1 skipped, 75 subtests passed in 1.79s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The full suite passes: 150 passed, 1 skipped, exit 0. Next, the stdlib check script the project requires for line length, spacing, syntax, annotations and the reno note shape.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc1.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/cc1.txt; grep -n \"skip\" /tmp/run_tests.log | head -3", "description": "Run project change checks script"}
[tool_result] exit=1
changed: releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:1967: line is 89 columns (max 88)
FAIL: 1 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
19:tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_skips_retry PASSED [  7%]
121:tests/test_tenacity.py::TestEnabled::test_enabled_false_skips_retry PASSED [ 71%]
168:============== 150 passed, 1 skipped, 75 subtests passed in 1.79s ==============
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "offset": 1965, "limit": 4}
[tool_result] 1965	        self.assertEqual(str(actual), "pickled")
1966	        self.assertTrue(actual.reraise)
1967	        self.assertEqual(actual.stop.max_attempt_number, 3)  # type: ignore[attr-defined]
1968	
[assistant] The one line over the limit is my assertion. I'll wrap it so the `type: ignore` stays on the attribute line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(actual.stop.max_attempt_number, 3)  # type: ignore[attr-defined]", "new_string": "        self.assertEqual(\n            actual.stop.max_attempt_number,  # type: ignore[attr-defined]\n            3,\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc2.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/cc2.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; tail -3 /tmp/full2.txt", "description": "Re-run change checks and full suite"}
[tool_result] exit=0
changed: releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
============== 150 passed, 1 skipped, 75 subtests passed in 1.79s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All checks pass: `check_changed.py` exits 0 with 0 problems, and the suite is still green. Two things I haven't verified yet: `AsyncRetrying` inherits the new hooks, and `copy.copy` now goes through them, which changes its behaviour. I'll check both directly.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cd /tmp/mp_check && $PY -I -c \"\nimport sys, pickle, copy, asyncio\nsys.path.insert(0,'~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/dom-1')\nimport tenacity\na = tenacity
…[187 chars elided]…
ef f():\n        n[0]+=1\n        if n[0]<2: raise ValueError\n        return 'ok'\n    return await b(f)\nprint('async:', asyncio.run(go()))\nr = tenacity.Retrying(); r(lambda: 1)\nc = copy.copy(r)\nprint('copy shares stats object:', c.statistics is r.statistics, '| copy has stats:', bool(c.statistics))\n\" ; cd - >/dev/null", "description": "Check AsyncRetrying pickling and copy.copy behaviour"}
[tool_result] async: ok
copy shares stats object: False | copy has stats: True
[assistant] Both hold. `AsyncRetrying` round-trips and runs after unpickling. `copy.copy` now gives the copy its own statistics dict, initialised from the original's; before, the copy shared the thread-local store. I'll flag that in the summary. Last, confirming the working-tree changes.
[tool_use Bash] {"command": "git status --short; git diff --stat", "description": "Show changed files and diff stats"}
[tool_result]  M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/pickle-retrying-objects-c78ae4f2f53e5e80.yaml
 tenacity/__init__.py   |  14 ++++++
 tenacity/retry.py      |  46 ++++++++++++------
 tests/test_tenacity.py | 125 +++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 170 insertions(+), 15 deletions(-)
[assistant] `Retrying` objects (including ones that have already run) and the built-in retry strategies now pickle and restore to working objects. A `Retrying` passed through a spawn-context `Pool` runs in the worker. Changes are left uncommitted in the working tree.

**What changed**
- **`tenacity/retry.py`**: `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` and `retry_if_not_exception_message` used lambdas and nested functions as predicates, which can't be pickled. They now bind module-level functions with `functools.partial`. Behaviou
…[1341 chars elided]…
om the original's. I think that is the correct copy semantics, but it is observable.
- **Statistics survive pickling**: a restored object reports the statistics of the thread that pickled it. If you'd rather restore a clean object, drop the `_statistics` entry from `__getstate__`.
- **Left unpicklable on purpose**: the logging callbacks from `before_log`/`after_log`/`before_sleep_log`, `stop_when_event_set`, `sleep_using_event`, and user callables passed to `retry_if_result`, `retry_if_exception` and similar. Those hold user or OS objects, so making them picklable would need a design decision.
