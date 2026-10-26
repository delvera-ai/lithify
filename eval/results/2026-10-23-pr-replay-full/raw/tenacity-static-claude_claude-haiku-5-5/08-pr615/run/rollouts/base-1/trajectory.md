# trajectory base-1

final message:
`Retrying` objects and the built-in retry strategies now pickle, including a `Retrying` that has already run and holds statistics. The unpickled object works and keeps its statistics. The full suite passes and the stdlib checks are clean. I did not commit.

**What was blocking pickle**
- `Retrying` held a `threading.local`, which cannot be pickled. `__getstate__`/`__setstate__` on `BaseRetrying` now save the calling thread's statistics, drop the thread-local storage and per-run state, and rebuild them on load.
- `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type` and `retry_if_not_exception_message` stored lambdas as predicates. `retry_if_exception_message` stored closures. These are now module-level functions bound with `functools.partial`, with the same behaviour.

**Verification**
- Regression tests (`TestPickling` in `tests/test_tenacity.py`) failed on the unfixed code with `Can't get local object ... <lambda>` and `... message_fnc`, and pass now (33/33 in the class).
- Full suite via `run_tests.py`: `exit=0`, 179 passed, 1 skipped. The skip is `test_trio_basic` because trio isn't installed.
- `check_changed.py`: exit 0, 0 problems. ruff and mypy were not run; the harness has no way to run them here.
- A `multiprocessing.Pool(2).map` over a `@retry`-decorated module-level function returns `[2, 4, 6]`, and `pickle.loads(pickle.dumps(fn.retry))` round-trips.

**Files changed**
- `tenacity/__init__.py`: pickle hooks on `BaseRetrying`.
- `tenacity/retry.py`: module-level predicates.
- `tests/test_tenacity.py`: `TestPickling`.
- `releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml`: a `fixes:` reno note, as the change contract requires.

I did not edit `doc/source/index.rst`, because the contract only asks for docs when a documented usage changes.

**Things to know**
- `Pool.map(decorated_fn, ...)` already worked before this change, because the decorated function pickles by reference. The fix matters when a `Retrying` or strategy itself crosses the process boundary.
- Side effect: `copy.copy(retrying)` now gives the copy its own thread-local storage. Before, the copy shared it. Nothing in the suite depends on the old sharing.
- User-supplied lambdas or closures (for example `retry_if_result(lambda ...)`, `wait_exception(lambda ...)`) still won't pickle. So does `stop_when_event_set`, because a `threading.Event` can't be pickled. Those are the caller's callables, so I left them alone.

## events
[assistant] I'll start by reading the change-contract skill and the relevant tenacity code.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls; echo ---; ls tenacity tests releasenotes/notes 2>/dev/null | head -80; echo ---; cat .lithify/harness/memory.md 2>/dev/null | head -30", "description": "Read change-contract skill and list repo layout"}
[tool_use Bash] {"command": "wc -l tenacity/*.py; sed -n 1,400p tenacity/__init__.py", "description": "Show repo files and core Retrying code"}
[tool_result]      797 tenacity/__init__.py
     111 tenacity/_utils.py
       2 tenacity/_version.py
      46 tenacity/after.py
      42 tenacity/before.py
      67 tenacity/before_sleep.py
      43 tenacity/nap.py
     297 tenacity/retry.py
     130 tenacity/stop.py
      62 tenacity/tornadoweb.py
     271 tenacity/wait.py
    1868 total
# Copyright 2016-2018 Julien Danjou
# Copyright 2017 Elisey Zanko
# Copyright 2016 Étienne Bersac
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licens
…[12453 chars elided]…
y_state.upcoming_sleep = sleep

    def _run_stop(self, retry_state: "RetryCallState") -> None:
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = self.stop(retry_state)

    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = action(retry_state)
        return result
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version) — i.e. any edit under tenacity/ that a user of the library could notice. Lists the files such a change mus
…[13041 chars elided]…
yaml

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
---
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "sed -n 400,797p tenacity/__init__.py", "description": "Read rest of core tenacity module"}
[tool_result]     def _begin_iter(self, retry_state: "RetryCallState") -> None:
        self.iter_state.reset()

        fut = retry_state.outcome
        if fut is None:
            if self.before is not None:
                self._add_action_func(self.before)
            self._add_action_func(lambda rs: DoAttempt())
            return

        self.iter_state.is_explicit_retry = fut.failed and isinstance(
            fut.exception(), TryAgain
        )
        if not self.iter_state.is_explicit_retry:
     
…[11847 chars elided]…
ult",
    "retry_never",
    "retry_unless_exception_type",
    "sleep",
    "sleep_using_event",
    "stop_after_attempt",
    "stop_after_delay",
    "stop_all",
    "stop_any",
    "stop_before_delay",
    "stop_never",
    "stop_when_event_set",
    "wait_chain",
    "wait_combine",
    "wait_exception",
    "wait_exponential",
    "wait_exponential_jitter",
    "wait_fixed",
    "wait_full_jitter",
    "wait_incrementing",
    "wait_none",
    "wait_random",
    "wait_random_exponential",
]
[tool_use Bash] {"command": "cat tenacity/retry.py | sed -n 1,140p; echo ----; grep -n \"class \\|def __init__\\|self\\.\\w* = \" tenacity/stop.py tenacity/wait.py", "description": "Read retry strategies and stop/wait class layout"}
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
…[7179 chars elided]…
econds(min)
tenacity/wait.py:197:        self.max = _utils.to_seconds(max)
tenacity/wait.py:198:        self.exp_base = exp_base
tenacity/wait.py:209:class wait_random_exponential(wait_exponential):
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
tenacity/wait.py:252:    def __init__(
tenacity/wait.py:259:        self.initial = initial
tenacity/wait.py:260:        self.max = max
tenacity/wait.py:261:        self.exp_base = exp_base
tenacity/wait.py:262:        self.jitter = jitter
[assistant] The core pickling blockers look like `threading.local` on `Retrying` and lambda predicates in the strategies. Next I'll check for lambdas and existing pickle references, and how the test suite is organised.
[tool_use Bash] {"command": "grep -n \"lambda\\|threading\\|pickle\" tenacity/*.py tenacity/asyncio/*.py; echo ---; grep -n \"class \\|^import\\|^from\" tests/test_tenacity.py | head -80; echo ---; grep -n \"class \\|sleep\" tenacity/asyncio/__init__.py | head -40; echo ---; sed -n 140,297p tenacity/retry.py | grep -n \"def __init__\\|self\\.\\w* =\\|class \" ", "description": "Find lambdas, pickle refs, test layout"}
[tool_result] tenacity/__init__.py:21:import threading
tenacity/__init__.py:253:        self._local = threading.local()
tenacity/__init__.py:408:            self._add_action_func(lambda rs: DoAttempt())
tenacity/__init__.py:420:            self._add_action_func(lambda rs: rs.outcome.result())
tenacity/__init__.py:458:        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))
tenacity/retry.py:111:        super().__init__(lambda e: isinstance(e, exception_types))
tenacity/retry.py:123:        super()
…[3639 chars elided]…
f_exception_message(retry_if_exception):
73:    def __init__(
105:class retry_if_not_exception_message(retry_if_exception_message):
108:    def __init__(
116:        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
131:class retry_any(retry_base):
134:    def __init__(self, *retries: "RetryBaseT") -> None:
135:        self.retries = retries
146:class retry_all(retry_base):
149:    def __init__(self, *retries: "RetryBaseT") -> None:
150:        self.retries = retries
[assistant] Three things block pickling of the default strategies: `threading.local` on `Retrying`, lambda predicates in `retry_if_exception_type` and friends, and a lambda in `retry_if_not_exception_message`. I'll look at the message-matching strategies and the existing test style before writing the regression test.
[tool_use Bash] {"command": "sed -n 205,297p tenacity/retry.py; echo ---; sed -n 1412,1430p tests/test_tenacity.py; echo ---; sed -n 1747,1768p tests/test_tenacity.py; echo ---; sed -n 1,20p releasenotes/notes/fix-local-context-overwrite-94190ba06a481631.yaml; ls .lithify/harness/scripts/", "description": "Read message strategies and existing test patterns"}
[tool_result]             return not self.predicate(retry_state.outcome.result())
        return False


class retry_if_exception_message(retry_if_exception):
    """Retries if an exception message equals or matches."""

    def __init__(
        self,
        message: str | None = None,
        match: None | str | re.Pattern[str] = None,
    ) -> None:
        if message and match:
            raise TypeError(
                f"{self.__class__.__name__}() takes either 'message' or 'match', not both"
        
…[3565 chars elided]…
tats_failing(self) -> None:
        @retry(stop=tenacity.stop_after_attempt(2))
        def _foobar() -> None:
            raise ValueError(42)

        self.assertEqual({}, _foobar.statistics)
        with contextlib.suppress(Exception):
            _foobar()
        self.assertEqual(2, _foobar.statistics["attempt_number"])


class TestRetryErrorCallback(unittest.TestCase):
---
---
fixes:
  - |
    Avoid overwriting local contexts when applying the retry decorator.
check_changed.py
run_tests.py
[assistant] The fix has three parts: give `Retrying` a pickle-safe state, replace the lambda predicates with module-level callables (or `functools.partial` over them), and cover the message strategies' closures the same way. Before changing anything, I'll confirm the current failures and check the project python exists.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY; $PY -I -c \"\nimport pickle, tenacity\nfrom tenacity import Retrying, retry_if_exception_type, retry_if_exception_message, stop_after_attempt\nfor o in [Retrying(), retry_if_exception_type(), retry_if_not_exception_m
…[28 chars elided]…
f_exception_message(message='x'), stop_after_attempt(2)]:\n    try:\n        pickle.dumps(o); print('ok', type(o).__name__)\n    except Exception as e: print('FAIL', type(o).__name__, type(e).__name__, e)\n\"; echo ---; tail -30 tests/test_tenacity.py; echo ---; sed -n 1,60p .lithify/harness/scripts/run_tests.py | head -60", "description": "Confirm pickling failures and read test tail and runner"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
---
    @pytest.fixture()
    def mock_sleep(
        self, monkeypatch: typing.Any
    )
…[2371 chars elided]…
meout = 300.0
    if args[:1] == ["--timeout"]:
        if len(args) < 2:
            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
            return 2
        timeout = float(args[1])
        args = args[2:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "-rfE",
        "-p",
        "no:cacheprovider",
        "--color=no",
        *args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
[assistant] The project python is a symlink, and `-I` hid the repo from the import path. I'll rerun the probe without `-I`, which is fine because this is the repo's own code.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport pickle, tenacity\nfrom tenacity import Retrying, retry_if_exception_type, retry_if_exception_message, stop_after_attempt\nfor o in [Retrying(), retry_if_exception_type(), retry_if_exception_message(message='x'), stop_after_attempt(2)]:\n    try:\n        pickle.dumps(o); print('ok', type(o).__name__)\n    except Exception as e: print('FAIL', type(o).__name__, type(e).__name__, e)\n\"", "description": "Confirm pickling failures on current code"}
[tool_result] FAIL Retrying AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL retry_if_exception_type AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL retry_if_exception_message AttributeError Can't get local object 'retry_if_exception_message.__init__.<locals>.message_fnc'
ok stop_after_attempt
[assistant] The current failures are as expected: `Retrying()`, `retry_if_exception_type()` and `retry_if_exception_message(...)` all fail to pickle. Next I'll add the regression tests, run them against the unfixed code, and check that they fail for the pickling reason.
[tool_use Bash] {"command": "grep -n 'if __name__ == \"__main__\"' tests/test_tenacity.py; grep -n \"def __init__\" -A3 tenacity/retry.py | sed -n 1,20p | grep -A3 cause; grep -n \"^import logging\" tests/test_tenacity.py", "description": "Check anchors for test insertion"}
[tool_result] 2012:if __name__ == "__main__":
18:import logging
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "import logging\nimport re", "new_string": "import logging\nimport pickle\nimport re"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "\n\nif __name__ == \"__main__\":\n    unittest.main()", "new_string": "\n\ndef _is_none(value: typing.Any) -> bool:\n    return value is None\n\n\n@tenacity.retry(\n    stop=tenacity.stop_after_attempt(2),\n    ret
…[3678 chars elided]…
            restored(fail)\n        assert restored.statistics[\"attempt_number\"] == 2\n\n    def test_decorated_function_retry_round_trip(self) -> None:\n        restored: typing.Any = pickle.loads(pickle.dumps(_pickle_double.retry))\n        assert isinstance(restored, Retrying)\n        assert restored(_pickle_double.__wrapped__, 3) == 6\n\n\nif __name__ == \"__main__\":\n    unittest.main()"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the new tests alone against the unfixed code. They should fail on pickling errors, not on import or typo errors.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/out_red.txt 2>&1; echo \"exit=$?\"; tail -45 /tmp/out_red.txt", "description": "Run new pickling tests against unfixed code"}
[tool_result] exit=1
    
        r = Retrying(
            stop=tenacity.stop_after_attempt(2),
            retry=tenacity.retry_if_exception_type(ValueError),
        )
        with contextlib.suppress(RetryError):
            r(fail)
        assert r.statistics["attempt_number"] == 2
    
>       restored = pickle.loads(pickle.dumps(r))
                                ^^^^^^^^^^^^^^^
E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'

tests/test_tenacity.py:
…[1409 chars elided]…
nd_trip[strategy13]
FAILED tests/test_tenacity.py::TestPickling::test_message_strategy_round_trip_keeps_behaviour
FAILED tests/test_tenacity.py::TestPickling::test_default_retrying_round_trip
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_round_trip_keeps_statistics
FAILED tests/test_tenacity.py::TestPickling::test_decorated_function_retry_round_trip
======================== 14 failed, 19 passed in 0.20s =========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The new tests fail for the expected reason (`Can't get local object ... <lambda>` and the message closure), and the non-pickling tests pass. Now the fix: module-level predicates instead of closures in `retry.py`, and `__getstate__`/`__setstate__` on `BaseRetrying`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n", "new_string": "import abc\nimport functools\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from t
…[561 chars elided]…
xception_types)\n\n\ndef _negate(predicate: typing.Callable[[BaseException], bool], exception: BaseException) -> bool:\n    return not predicate(exception)\n\n\ndef _message_equals(message: str, exception: BaseException) -> bool:\n    return message == str(exception)\n\n\ndef _message_matches(prog: re.Pattern[str], exception: BaseException) -> bool:\n    return bool(prog.match(str(exception)))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        self.exception_types = exception_types\n        super().__init__(lambda e: isinstance(e, exception_types))\n\n\nclass retry_if_not_exception_type(retry_if_exception):\n    \"\"\"Retries except an exception has b
…[1316 chars elided]…
s_exception_type(retry_if_exception):\n    \"\"\"Retries until an exception is raised of one or more types.\"\"\"\n\n    def __init__(\n        self,\n        exception_types: type[BaseException]\n        | tuple[type[BaseException], ...] = Exception,\n    ) -> None:\n        self.exception_types = exception_types\n        super().__init__(functools.partial(_is_not_instance_of, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        if message:\n\n            def message_fnc(exception: BaseException) -> bool:\n                return message == str(exception)\n\n            predicate = message_fnc\n        elif match:\n            prog = re.
…[36 chars elided]…
tch_fnc(exception: BaseException) -> bool:\n                return bool(prog.match(str(exception)))\n\n            predicate = match_fnc\n        else:", "new_string": "        if message:\n            predicate = functools.partial(_message_equals, message)\n        elif match:\n            prog = re.compile(match)\n            predicate = functools.partial(_message_matches, prog)\n        else:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)", "new_string": "        self.predicate = functools.partial(_negate, if_predicate)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[assistant] The `_negate` signature is over the 88-column limit, so I'll wrap it. Then I'll add the `BaseRetrying` pickle hooks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "def _negate(predicate: typing.Callable[[BaseException], bool], exception: BaseException) -> bool:", "new_string": "def _negate(\n    predicate: typing.Callable[[BaseException], bool], exception: BaseException\n) -> bool:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "            f\"name={self._name!r})>\"\n        )\n", "new_string": "            f\"name={self._name!r})>\"\n        )\n\n    def __getstate__(self) -> dict[str, t.Any]:\n        state = self.__dict__.copy()\n       
…[104 chars elided]…
rage in __setstate__. Per-run iter_state is dropped.\n        del state[\"_local\"]\n        state[\"_statistics\"] = dict(self.statistics)\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self.statistics.update(statistics)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the targeted test run against the fixed code, then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/out_green.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/out_green.txt; echo ======; $PY .lithify/harness/scripts/run_tests.py > /tmp/out_full.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/out_full.txt", "description": "Run pickling tests then full suite"}
[tool_result ERROR] Exit code 1
exit=0
tests/test_tenacity.py::TestPickling::test_message_strategy_round_trip_keeps_behaviour PASSED [ 90%]
tests/test_tenacity.py::TestPickling::test_default_retrying_round_trip PASSED [ 93%]
tests/test_tenacity.py::TestPickling::test_used_retrying_round_trip_keeps_statistics PASSED [ 96%]
tests/test_tenacity.py::TestPickling::test_decorated_function_retry_round_trip PASSED [100%]

============================== 33 passed in 0.03s ==============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
(eval):1: ===== not found
[assistant] The targeted tests pass (33/33). My `echo ======` hit the zsh issue the harness warns about, so the full suite did not run. I'll rerun it with a safe separator.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/out_full.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/out_full.txt", "description": "Run full test suite via harness runner"}
[tool_result] exit=0
tests/test_tornado.py::TestTornado::test_retry PASSED                    [ 98%]
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 179 passed, 1 skipped, 12 subtests passed in 1.78s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The full suite passes: `exit=0`, 179 passed, 1 skipped. Next: the reno release note the change contract requires, a real `multiprocessing.Pool` check (the reported scenario, which the unit tests don't exercise), and the harness's `check_changed.py`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; mkdir -p /tmp/pool_check && cat > /tmp/pool_check/pool_check.py <<'EOF'\nimport multiprocessing\nimport pickle\n\nimport tenacity\n\n\n@tenacity.retry(\n    stop=tenacity.stop_after_attempt(3),\n    retry=tenacity.retry_if_excep
…[110 chars elided]…
 with multiprocessing.Pool(2) as pool:\n        print(\"pool.map:\", pool.map(double, [1, 2, 3]))\n    print(\"retry round trip:\", pickle.loads(pickle.dumps(double.retry)))\nEOF\nPYTHONPATH=\"$PWD\" timeout 60 $PY /tmp/pool_check/pool_check.py; echo \"exit=$?\"; python3 -c \"import secrets;print(secrets.token_hex(8))\"", "description": "Check Pool.map with decorated function in a scratch script"}
[tool_result] (eval):21: command not found: timeout
exit=127
ef863ea0075170bd
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=\"$PWD\" $PY /tmp/pool_check/pool_check.py; echo \"exit=$?\"", "description": "Run Pool.map check without timeout utility"}
[tool_result] pool.map: [2, 4, 6]
retry round trip: <unknown>
exit=0
[assistant] `Pool.map` over a decorated module-level function works. That path pickles the function by reference, so it did not depend on the fix. The fix matters when a `Retrying` or strategy crosses the process boundary, which the round-trip tests cover. Now the release note, using the contract's file-name shape.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml", "content": "---\nfixes:\n  - |\n    ``Retrying`` objects, including ones that have already run and hold\n    statistics, and the built-in retry strategies can now be pickled, so\n    ``@retry``-decorated functions can be used with ``multiprocessing``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/out_check.txt 2>&1; echo \"exit=$?\"; cat /tmp/out_check.txt | tail -30; git status --short", "description": "Run stdlib change checks and show git status"}
[tool_result] exit=1
changed: releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:2026: line is 89 columns (max 88)
FAIL tests/test_tenacity.py:2066: nested def needs a blank line before it
FAIL: 2 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml
[tool_use Bash] {"command": "sed -n 2024,2027p tests/test_tenacity.py; echo ---; sed -n 2062,2068p tests/test_tenacity.py", "description": "View flagged test lines"}
[tool_result] class TestPickling:
    """Retrying objects and strategies must survive pickle (e.g. for multiprocessing)."""

---
            tenacity.wait_chain(tenacity.wait_fixed(1)),
            tenacity.wait_combine(tenacity.wait_fixed(1), tenacity.wait_none()),
        ],
    )
    def test_strategy_round_trip(self, strategy: typing.Any) -> None:
        restored = pickle.loads(pickle.dumps(strategy))
        assert type(restored) is type(strategy)
[assistant] Two flags: a docstring over 88 columns, and a "nested def" flag on the parametrized method. I'll check exactly what the checker's nested-def rule expects before changing the decorator layout.
[tool_use Bash] {"command": "grep -n \"nested def\" -B25 .lithify/harness/scripts/check_changed.py | head -60", "description": "Read checker's nested-def rule"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n -i \"blank line\\|nested\" .lithify/harness/scripts/check_changed.py | head; ", "description": "Locate nested-def check in script"}
[tool_result] 12:      * a nested `def`/`class` is preceded by a blank line (ruff format)
99:                    f"{path}:{no}: nested {m.group(2)} needs a blank line before it"
[tool_use Bash] {"command": "sed -n 80,100p .lithify/harness/scripts/check_changed.py", "description": "Read nested-def check logic"}
[tool_result]     errs += check_annotations(path, src, changed)
    lines = src.splitlines()
    for no in sorted(changed):
        if no > len(lines):
            continue
        line = lines[no - 1]
        if len(line) > MAX_LEN:
            errs.append(f"{path}:{no}: line is {len(line)} columns (max {MAX_LEN})")
        if "\t" in line:
            errs.append(f"{path}:{no}: tab character")
        if line != line.rstrip():
            errs.append(f"{path}:{no}: trailing whitespace")
        m = DEF_RE.match(line)
        if m and no >= 2:
            prev = lines[no - 2]
            prev_s = prev.strip()
            opener = prev_s.endswith(":") or prev_s.startswith(("@", "#"))
            if prev_s and not opener:
                errs.append(
                    f"{path}:{no}: nested {m.group(2)} needs a blank line before it"
                )
[assistant] The rule accepts a `def` only after a blank line, a line ending in `:`, or a decorator/comment line. A multi-line decorator's closing `)` fails that, so I'll move the strategy list to a module-level constant and fix the long docstring.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "class TestPickling:\n    \"\"\"Retrying objects and strategies must survive pickle (e.g. for multiprocessing).\"\"\"\n\n    @pytest.mark.parametrize(\n        \"strategy\",\n        [\n            tenacity.retry_if
…[3118 chars elided]…
t_random(0, 1),\n    tenacity.wait_chain(tenacity.wait_fixed(1)),\n    tenacity.wait_combine(tenacity.wait_fixed(1), tenacity.wait_none()),\n]\n\n\nclass TestPickling:\n    \"\"\"Retrying objects and strategies must survive pickle (for multiprocessing).\"\"\"\n\n    @pytest.mark.parametrize(\"strategy\", PICKLABLE_STRATEGIES)\n    def test_strategy_round_trip(self, strategy: typing.Any) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] I'll rerun the full suite and `check_changed.py` after this test-file edit.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/out_full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/out_full.txt; grep -i \"skip\" /tmp/out_full.txt | head -3; $PY .lithify/harness/scripts/check_changed.py > /tmp/out_check.txt 2>&1; echo \"check_exit=$?\"; tail -5 /tmp/out_check.txt", "description": "Rerun full suite and change checks"}
[tool_result] exit=0

============== 179 passed, 1 skipped, 12 subtests passed in 1.82s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
============== 179 passed, 1 skipped, 12 subtests passed in 1.82s ==============
check_exit=0
changed: releasenotes/notes/fix-retrying-pickle-ef863ea0075170bd.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Suite and change checks are green. Last, I'll identify the skipped test to confirm it isn't related, and review the final diff.
[tool_use Bash] {"command": "grep -n \"SKIPPED\" /tmp/run_tests.log | head -3; git diff --stat; git diff tenacity/", "description": "Identify skipped test and review source diff"}
[tool_result] 20:tests/test_asyncio.py::TestTrio::test_trio_basic SKIPPED (trio not i...) [  7%]
 tenacity/__init__.py   |  14 +++++++
 tenacity/retry.py      |  51 ++++++++++++++++++-------
 tests/test_tenacity.py | 101 +++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 152 insertions(+), 14 deletions(-)
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 591f970..b0db658 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -306,6 +306,20 @@ class BaseRetrying(ABC):
   
…[4101 chars elided]…
g 1 required argument 'message' or 'match'"
@@ -252,7 +275,7 @@ class retry_if_not_exception_message(retry_if_exception_message):
         super().__init__(message, match)
         # invert predicate
         if_predicate = self.predicate
-        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
+        self.predicate = functools.partial(_negate, if_predicate)
 
     def __call__(self, retry_state: "RetryCallState") -> bool:
         if retry_state.outcome is None:
[assistant] `Retrying` objects and the built-in retry strategies now pickle, including a `Retrying` that has already run and holds statistics. The unpickled object works and keeps its statistics. The full suite passes and the stdlib checks are clean. I did not commit.

**What was blocking pickle**
- `Retrying` held a `threading.local`, which cannot be pickled. `__getstate__`/`__setstate__` on `BaseRetrying` now save the calling thread's statistics, drop the thread-local storage and per-run state, and rebuild them on load.
- `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_
…[1270 chars elided]…
.)` already worked before this change, because the decorated function pickles by reference. The fix matters when a `Retrying` or strategy itself crosses the process boundary.
- Side effect: `copy.copy(retrying)` now gives the copy its own thread-local storage. Before, the copy shared it. Nothing in the suite depends on the old sharing.
- User-supplied lambdas or closures (for example `retry_if_result(lambda ...)`, `wait_exception(lambda ...)`) still won't pickle. So does `stop_when_event_set`, because a `threading.Event` can't be pickled. Those are the caller's callables, so I left them alone.
