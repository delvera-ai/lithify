# trajectory base-1

final message:
`Retrying` objects and the built-in retry strategies now pickle and restore to working objects, including after they have been used and carry statistics. The suite passes: 165 tests, 1 skipped, up from 146 with 19 new pickling tests. Changes are uncommitted in the worktree.

**Root causes**
- **Strategies:** `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_not_exception_message`, and `retry_if_exception_message` stored lambdas or closures as their predicates. I replaced them with module-level helpers wrapped in `functools.partial`, so behaviour is unchanged.
- **`Retrying`:** it held a `threading.local()`, which pickle can't serialise. I added `__getstate__`/`__setstate__` in `tenacity/__init__.py`. They drop the thread-local, carry the pickling thread's statistics across, and recreate the thread-local on load.

**Decision for you:** statistics are thread-local, so restored statistics are seeded lazily into whichever thread first reads them. I did this because `multiprocessing.Pool` unpickles returned objects in its result-handler thread, and statistics restored into that thread were invisible to the main thread. Per-attempt iteration state is not preserved; it's transient and recreated on load.

**Side effects:** `copy.deepcopy` of a `Retrying` also works now, since it goes through the same hooks.

**Verified:** `Pool.map` over a `@retry`-decorated function under `spawn` returns the right results. Retry objects with statistics round-trip across processes.

**Not covered:** the callbacks built by `before_log`, `before_sleep_log`, and `after_log` are closures, so they still can't be pickled. Neither can user-supplied lambdas (e.g. `wait_exception(lambda ...)`). Those are outside the strategy classes this bug names, so I left them alone. Say if you want them handled too.

**Lint:** ruff format and check pass on the changed files, with the 15 RUF036 warnings all pre-existing. mypy reports 6 errors, all on untouched lines. I installed ruff and mypy into a scratch venv outside the repo.

## events
[tool_use Bash] {"command": "git status --short && ls && wc -l tenacity/*.py && grep -n \"class \\|def __init__\\|__slots__\\|self\\.\\w* = \" tenacity/__init__.py | head -80", "description": "Inspect repo layout and core classes"}
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
     797 tenacity/__init__.py
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
112:class IterState:
121:        self.actions = []
122:        self.retry_ru
…[1517 chars elided]…
t__(
548:        self.start_time = time.monotonic()
550:        self.retry_object = retry_object
552:        self.fn = fn
554:        self.args = args
556:        self.kwargs = kwargs
589:        self.outcome = None
590:        self.outcome_timestamp = None
592:        self.next_action = None
598:        self.outcome, self.outcome_timestamp = fut, ts
609:        self.outcome, self.outcome_timestamp = fut, ts
625:class _RetryDecorated(t.Protocol[P, R]):
639:class _AsyncRetryDecorator(t.Protocol):
[tool_use Bash] {"command": "cat CLAUDE.md AGENTS.md | head -80; sed -n 100,125p tenacity/__init__.py; sed -n 225,262p tenacity/__init__.py; sed -n 480,512p tenacity/__init__.py; sed -n 535,625p tenacity/__init__.py", "description": "Read project docs and core retry code"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[6912 chars elided]…
   result = "none yet"
        elif self.outcome.failed:
            exception = self.outcome.exception()
            result = f"failed ({exception.__class__.__name__} {exception})"
        else:
            result = f"returned {self.outcome.result()}"

        slept = float(round(self.idle_for, 2))
        clsname = self.__class__.__name__
        return f"<{clsname} {id(self)}: attempt #{self.attempt_number}; slept for {slept}; last result: {result}>"


class _RetryDecorated(t.Protocol[P, R]):
[tool_use Bash] {"command": "sed -n 262,300p tenacity/__init__.py; grep -n \"statistics\\|_local\\|threading\\|def begin\\|def wraps\\|def copy\\|def __iter__\\|def __call__\\|def __init__\\|def __getstate__\\|def __setstate__\" tenacity/__init__.py; sed -n 1,40p tenacity/__init__.py | grep -n import; grep -n \"^class \\|def __init__\\|self\\.\\w* = \\|def __call__\\|self\\.\\w*: \" tenacity/stop.py tenacity/wait.py tenacity/retry.py tenacity/_utils.py tenacity/after.py tenacity/before.py tenacity/before_sleep.py tenacity/nap.py", "description": "Find statistics, copy, and strategy class definitions"}
[tool_result]         stop: t.Union["StopBaseT", object] = _unset,
        wait: t.Union["WaitBaseT", object] = _unset,
        retry: retry_base | object = _unset,
        before: t.Callable[["RetryCallState"], None] | object = _unset,
        after: t.Callable[["RetryCallState"], None] | object = _unset,
        before_sleep: t.Callable[["RetryCallState"], None] | None | object = _unset,
        reraise: bool | object = _unset,
        retry_error_cls: type[RetryError] | object = _unset,
        retry_error
…[11733 chars elided]…
_any(retry_base):
tenacity/retry.py:273:    def __init__(self, *retries: "RetryBaseT") -> None:
tenacity/retry.py:274:        self.retries = retries
tenacity/retry.py:276:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/retry.py:285:class retry_all(retry_base):
tenacity/retry.py:288:    def __init__(self, *retries: "RetryBaseT") -> None:
tenacity/retry.py:289:        self.retries = retries
tenacity/retry.py:291:    def __call__(self, retry_state: "RetryCallState") -> bool:
[tool_use Bash] {"command": "sed -n 300,372p tenacity/__init__.py; grep -n \"stop_never\\|retry_never\\|wait_none()\\|_unset\\b\" tenacity/*.py | head -30; sed -n 100,112p tenacity/retry.py; sed -n 60,72p tenacity/stop.py; ls tests; git log --oneline -3 -- tenacity/__init__.py", "description": "Read wraps/statistics and check sentinels"}
[tool_result]             f"stop={self.stop}, "
            f"wait={self.wait}, "
            f"sleep={self.sleep}, "
            f"retry={self.retry}, "
            f"before={self.before}, "
            f"after={self.after}, "
            f"name={self._name!r})>"
        )

    @property
    def statistics(self) -> dict[str, t.Any]:
        """Return a dictionary of runtime statistics.

        This dictionary will be empty when the controller has never been
        ran. When it is running or has ran previou
…[4880 chars elided]…
stops)


class _stop_never(stop_base):
    """Never stop."""

    def __call__(self, retry_state: "RetryCallState") -> bool:
        return False


stop_never = _stop_never()

__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
39eb157 feat: add enabled parameter to disable retrying (#604)
124e3a6 feat: add async context manager support to AttemptManager (#605)
42b70f9 fix: initialize delay_since_first_attempt in statistics on begin() (#603)
[tool_use Bash] {"command": "grep -n \"lambda\\|def \\w*(.*):$\\|nonlocal\" tenacity/*.py | grep -v \"def __\" ; sed -n 84,100p tenacity/retry.py; sed -n 206,270p tenacity/retry.py; sed -n 1,30p tenacity/wait.py | grep -n import; sed -n 40,50p tenacity/nap.py", "description": "Find lambdas and closures in strategy code"}
[tool_result] tenacity/__init__.py:408:            self._add_action_func(lambda rs: DoAttempt())
tenacity/__init__.py:420:            self._add_action_func(lambda rs: rs.outcome.result())
tenacity/__init__.py:458:        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))
tenacity/retry.py:111:        super().__init__(lambda e: isinstance(e, exception_types))
tenacity/retry.py:123:        super().__init__(lambda e: not isinstance(e, exception_types))
tenacity/retry.py:135:        super().__init__(lam
…[2713 chars elided]…
            raise RuntimeError("outcome failed but the exception is None")
        return self.predicate(exception)


class retry_any(retry_base):
17:import abc
18:import random
19:import typing
21:from tenacity import _utils
24:    from tenacity import RetryCallState
    def __call__(self, timeout: float | None) -> None:
        # NOTE(harlowja): this may *not* actually wait for timeout
        # seconds if the event is set (ie this may eject out early).
        self.event.wait(timeout=timeout)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; sed -n 376,400p tenacity/__init__.py; sed -n 440,460p tenacity/__init__.py", "description": "Run baseline test suite and read stats code"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
........................................................................ [ 89%]
...............                                                          [100%]
146 passed, 1 skipped, 12 subtests passed in 1.78s

…[1137 chars elided]…
ne:
            sleep = rs.upcoming_sleep
            rs.next_action = RetryAction(sleep)
            rs.idle_for += sleep
            self.statistics["idle_for"] += sleep
            self.statistics["attempt_number"] += 1

        self._add_action_func(next_action)

        if self.before_sleep is not None:
            self._add_action_func(self.before_sleep)

        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
[tool_use Bash] {"command": "mkdir -p /tmp/repro_retry && cat > /tmp/repro_retry/probe.py <<'EOF'\nimport pickle, re, sys, traceback\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1\")\nimport tenacity\nfrom tenacity import *\nfrom tenacity import retry, retry_if_exception_type, Retrying\nimport tenacity.retry as R, tenacity.stop as
…[2059 chars elided]…
g(stop=stop_after_attempt(2)); r(lambda: 1)\ntry: pickle.loads(pickle.dumps(r)); print(\"ok used\")\nexcept Exception as e: print(\"FAIL used\", e)\nEOF\n<work>/env-tenacity/bin/python -I /tmp/repro_retry/probe.py", "description": "Reproduce pickling failures across objects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/repro_retry/probe.py", line 12, in <module>
    "retry_if_not_exception_type": R.retry_if_not_exception_type(),
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'function' object has no attribute 'retry_if_not_exception_type'
[tool_use Bash] {"command": "cd /tmp/repro_retry && sed -i 's/^import tenacity.retry as R, tenacity.stop as S, tenacity.wait as W/import importlib; R = importlib.import_module(\"tenacity.retry\"); S = importlib.import_module(\"tenacity.stop\"); W = importlib.import_module(\"tenacity.wait\")/' probe.py && <work>/env-tenacity/bin/python -I probe.py", "description": "Rerun pickling probe with module imports fixed"}
[tool_result ERROR] Exit code 1
sed: 1: "probe.py
": extra characters at the end of p command
[tool_use Edit] {"replace_all": false, "file_path": "/tmp/repro_retry/probe.py", "old_string": "import tenacity.retry as R, tenacity.stop as S, tenacity.wait as W", "new_string": "import importlib\nR = importlib.import_module(\"tenacity.retry\")\nS = importlib.import_module(\"tenacity.stop\")\nW = importlib.import_module(\"tenacity.wait\")"}
[tool_result] The file /tmp/repro_retry/probe.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/repro_retry && <work>/env-tenacity/bin/python -I probe.py", "description": "Run pickling probe script"}
[tool_result] FAIL Retrying() AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL Retrying(stop,wait,retry) AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL retry_if_exception_type AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL retry_if_not_exception_type AttributeError Can't get local object 'retry_if_not_exception_type.__init__.<locals>.<lambda>'
FAIL retry_unless_excep
…[930 chars elided]…
   wait_random
ok   wait_combine
ok   wait_chain
FAIL wait_exception PicklingError Can't pickle <function <lambda> at 0x1038e3ec0>: attribute lookup <lambda> on __
ok   wait_incrementing
ok   wait_exponential
ok   wait_random_exponential
ok   wait_exponential_jitter
decorated fn: 3
FAIL used Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[tool_use Bash] {"command": "sed -n 1,62p tenacity/retry.py; sed -n 112,150p tenacity/retry.py", "description": "Read retry.py header and exception strategies"}
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
…[2434 chars elided]…
es))

    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        # always retry if no exception was raised
        if not retry_state.outcome.failed:
            return True

        exception = retry_state.outcome.exception()
        if exception is None:
            raise RuntimeError("outcome failed but the exception is None")
        return self.predicate(exception)
[assistant] Baseline is 146 passing. The failures come from lambdas and closures stored as predicates in the retry strategies, plus `threading.local()` on `BaseRetrying`. I'll make the predicates picklable first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n\n\nclass retry_base(abc.ABC):", "new_string": "import abc\nimport functools\nimport re\nimport typing\n\nif typ
…[498 chars elided]…
pes)\n\n\ndef _negate(predicate: typing.Callable[..., bool], *args: typing.Any) -> bool:\n    return not predicate(*args)\n\n\ndef _message_equals(message: str, exception: BaseException) -> bool:\n    return message == str(exception)\n\n\ndef _message_matches(prog: \"re.Pattern[str]\", exception: BaseException) -> bool:\n    return bool(prog.match(str(exception)))\n\n\nclass retry_base(abc.ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"lambda\\|message_fnc\\|match_fnc\\|predicate = \" tenacity/retry.py", "description": "Locate remaining closures in retry.py"}
[tool_result] 27:# (rather than lambdas or closures) so that retry strategies stay picklable.
113:        self.predicate = predicate
136:        super().__init__(lambda e: isinstance(e, exception_types))
148:        super().__init__(lambda e: not isinstance(e, exception_types))
160:        super().__init__(lambda e: not isinstance(e, exception_types))
208:        self.predicate = predicate
223:        self.predicate = predicate
250:            def message_fnc(exception: BaseException) -> bool:
253:            predicate = message_fnc
257:            def match_fnc(exception: BaseException) -> bool:
260:            predicate = match_fnc
279:        if_predicate = self.predicate
280:        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
[tool_use Bash] {"command": "f=tenacity/retry.py && \\\npython3 - \"$f\" <<'EOF'\nimport sys, pathlib\np = pathlib.Path(sys.argv[1])\ns = p.read_text()\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (s.count(old), old)\n    s = s.replace(old, new)\nrep('''def _negate(predicate: typing.Callable[..., bool], *args: typing.Any) -> bool:\n    return not predicate(*args)''', '''def _negat
…[895 chars elided]…
'''            prog = re.compile(match)\n            predicate = functools.partial(_message_matches, prog)''')\nrep('''self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)''',\n    '''self.predicate = functools.partial(_negate, if_predicate)''')\np.write_text(s)\nEOF\ngit diff --stat; sed -n 245,262p $f", "description": "Replace lambdas and closures with partial helpers"}
[tool_result]  tenacity/retry.py | 44 +++++++++++++++++++++++++++++++-------------
 1 file changed, 31 insertions(+), 13 deletions(-)
            )

        # set predicate
        if message:

            predicate = functools.partial(_message_equals, message)
        elif match:
            prog = re.compile(match)
            predicate = functools.partial(_message_matches, prog)
        else:
            raise TypeError(
                f"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'"
            )

        super().__init__(predicate)


class retry_if_not_exception_message(retry_if_exception_message):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        if message:\n\n            predicate = functools.partial(_message_equals, message)", "new_string": "        if message:\n            predicate = functools.partial(_message_equals, message)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[assistant] Now the thread-local state on `BaseRetrying`. I'll drop `_local` when pickling, carry the calling thread's statistics across, and recreate the thread-local on unpickle.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "        self._name = name\n        self.enabled = enabled\n\n    def copy(", "new_string": "        self._name = name\n        self.enabled = enabled\n\n    def __getstate__(self) -> dict[str, t.Any]:\n        state 
…[197 chars elided]…
sient and is recreated on unpickling.\n        del state[\"_local\"]\n        state[\"_statistics\"] = dict(self.statistics)\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self.statistics.update(statistics)\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/repro_retry && cat > check.py <<'EOF'\nimport copy, pickle, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1\")\nfrom tenacity import Retrying, retry, stop_after_attempt, wait_fixed, retry_if_exception_type, retry_if_exception_message, retry_if_not_exception_message, retry_any, retry_all, ret
…[2482 chars elided]…
\n<work>/env-tenacity/bin/python -I check.py && <work>/env-tenacity/bin/python -I probe.py", "description": "Verify pickling round trips and behaviour"}
[tool_result ERROR] Exit code 1
call: ok stats attempt: 3
Traceback (most recent call last):
  File "/private/tmp/repro_retry/check.py", line 17, in <module>
    r2 = pickle.loads(pickle.dumps(r))
                      ^^^^^^^^^^^^^^^
_pickle.PicklingError: Can't pickle <function <lambda> at 0x101149440>: attribute lookup <lambda> on __main__ failed
[assistant] That failure is from my test script: the `sleep=lambda` is a user-supplied lambda, which pickle can't handle. I'll switch it to a module-level function.
[tool_use Bash] {"command": "cd /tmp/repro_retry && sed -i 's/sleep=lambda s: None/sleep=nosleep/; s/^calls = {\"n\": 0}/calls = {\"n\": 0}\\ndef nosleep(s): pass/' check.py && PY=<work>/env-tenacity/bin/python && $PY -I check.py && $PY -I probe.py", "description": "Rerun pickling checks with module-level sleep"}
[tool_result ERROR] Exit code 1
sed: 1: "check.py
": command c expects \ followed by text
[tool_use Edit] {"replace_all": false, "file_path": "/tmp/repro_retry/check.py", "old_string": "calls = {\"n\": 0}\ndef flaky():", "new_string": "calls = {\"n\": 0}\ndef nosleep(s):\n    pass\ndef flaky():"}
[tool_result] The file /tmp/repro_retry/check.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/repro_retry && PY=<work>/env-tenacity/bin/python && $PY -I check.py && $PY -I probe.py", "description": "Run pickling checks and probe again"}
[tool_result ERROR] Exit code 1
call: ok stats attempt: 3
Traceback (most recent call last):
  File "/private/tmp/repro_retry/check.py", line 19, in <module>
    r2 = pickle.loads(pickle.dumps(r))
                      ^^^^^^^^^^^^^^^
_pickle.PicklingError: Can't pickle <function <lambda> at 0x101499260>: attribute lookup <lambda> on __main__ failed
[tool_use Bash] {"command": "cd /tmp/repro_retry && grep -n \"lambda\" check.py", "description": "Find leftover lambda in check script"}
[tool_result] 17:r = Retrying(stop=stop_after_attempt(5), wait=wait_fixed(0), retry=retry_if_exception_type(ValueError), sleep=lambda s: None, reraise=True)
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[tool_use Edit] {"replace_all": false, "file_path": "/tmp/repro_retry/check.py", "old_string": "sleep=lambda s: None, reraise=True)", "new_string": "sleep=nosleep, reraise=True)"}
[tool_result] The file /tmp/repro_retry/check.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/repro_retry && PY=<work>/env-tenacity/bin/python && $PY -I check.py && $PY -I probe.py", "description": "Run pickling checks and probe again"}
[tool_result] call: ok stats attempt: 3
restored stats: True {'start_time': 227179.025648541, 'attempt_number': 3, 'idle_for': 0.0, 'delay_since_first_attempt': 2.7959002181887627e-05}
restored call: ok 3
retry_if_exception_message retry_if_exception_message
retry_if_exception_message retry_if_exception_message
retry_if_not_exception_message retry_if_not_exception_message
retry_if_not_exception_type retry_if_not_exception_type
retry_unless_exception_type retry_unless_exception_type
retry_if_exception_cause_ty
…[848 chars elided]…

ok   stop_any
ok   stop_all
ok   stop_never
ok   wait_fixed
ok   wait_none
ok   wait_random
ok   wait_combine
ok   wait_chain
FAIL wait_exception PicklingError Can't pickle <function <lambda> at 0x1037cd3a0>: attribute lookup <lambda> on __
ok   wait_incrementing
ok   wait_exponential
ok   wait_random_exponential
ok   wait_exponential_jitter
decorated fn: 3
ok used
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[assistant] Round trips now work for all built-in strategies and `Retrying` objects with statistics. The only remaining failure is `wait_exception` given a lambda, which is user-supplied, so that's expected. Next I'll check the real `Pool.map` use case with spawn, then add tests.
[tool_use Bash] {"command": "cd /tmp/repro_retry && cat > pool_mod.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1\")\nfrom tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed\n\n@retry(stop=stop_after_attempt(3), wait=wait_fixed(0), retry=retry_if_exception_type(ValueError))\ndef w
…[520 chars elided]…
: 1)\n    with multiprocessing.Pool(1) as p:\n        print(\"pool with retry obj:\", p.apply(pickle.loads, (pickle.dumps(r),)).statistics)\nEOF\n<work>/env-tenacity/bin/python -I pool_main.py 2>&1 | tail -5", "description": "Test multiprocessing Pool with retried functions"}
[tool_result] pool: [2, 3, 4]
pool with retry obj: {}
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[assistant] The `Pool.map` case works. The retry-object round trip through a pool printed empty statistics, though, which needs checking.
[tool_use Bash] {"command": "cd /tmp/repro_retry && cat > dbg.py <<'EOF'\nimport pickle, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1\")\nfrom tenacity import Retrying, stop_after_attempt\nr = Retrying(stop=stop_after_attempt(2)); r(lambda: 1)\nprint(\"before:\", r.statistics)\nr2 = pickle.loads(pickle.dumps(r))\nprint(\"after:\", r2.statistics)\nr3 = pickle.loads(pickle.dumps(r2))\nprint(\"after2:\", r3.statistics)\nEOF\n<work>/env-tenacity/bin/python -I dbg.py", "description": "Debug statistics survival across pickling"}
[tool_result] before: {'start_time': 227190.567707166, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
after: {'start_time': 227190.567707166, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
after2: {'start_time': 227190.567707166, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[assistant] Plain pickling keeps statistics, so the empty result is specific to the pool path. I'll check what the worker sees.
[tool_use Bash] {"command": "cd /tmp/repro_retry && cat > pool_dbg.py <<'EOF'\nimport multiprocessing, sys, pickle\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1\")\nfrom tenacity import Retrying, stop_after_attempt\ndef worker_side(data):\n    obj = pickle.loads(data)\n    print(\"worker sees:\", obj.statistics, flush=True)\n    
…[122 chars elided]…
ore:\", r.statistics)\n    with multiprocessing.Pool(1) as p:\n        back = p.apply(worker_side, (pickle.dumps(r),))\n    print(\"main after:\", back.statistics)\nEOF\n<work>/env-tenacity/bin/python -I pool_dbg.py", "description": "Debug statistics inside a worker process"}
[tool_result] main before: {'start_time': 227196.925798583, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
worker sees: {'start_time': 227196.925798583, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
main after: {}
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[assistant] The worker sees the statistics, but they vanish on the way back. Pool's result-handler thread unpickles the returned object, and statistics are thread-local, so they land in that thread instead of the main thread. I'll make restored statistics seed lazily into whichever thread first reads them, which makes the restored object behave the same no matter where it is unpickled.
[tool_use Bash] {"command": "grep -n \"_local\\|def statistics\" tenacity/__init__.py", "description": "Locate thread-local usages in __init__.py"}
[tool_result] 253:        self._local = threading.local()
264:        del state["_local"]
271:        self._local = threading.local()
325:    def statistics(self) -> dict[str, t.Any]:
346:        if not hasattr(self._local, "statistics"):
347:            self._local.statistics = t.cast("dict[str, t.Any]", {})
348:        return self._local.statistics  # type: ignore[no-any-return]
352:        if not hasattr(self._local, "iter_state"):
353:            self._local.iter_state = IterState()
354:        return self._local.iter_state  # type: ignore[no-any-return]
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls", "new_string": "        self._local = threading.local()\n        # Statistics restored by unpickling, seeded into each thread on first use\n        self._restored_statistics: dict[str, t.Any] = {}\n        self.retry_error_cls = retry_error_cls"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "    def __getstate__(self) -> dict[str, t.Any]:\n        state = self.__dict__.copy()\n        # threading.local cannot be pickled, so drop it and carry over the\n        # statistics of the current thread instead. P
…[735 chars elided]…
ling.\n        del state[\"_local\"]\n        del state[\"_restored_statistics\"]\n        state[\"_statistics\"] = dict(self.statistics)\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self._restored_statistics = statistics"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "        if not hasattr(self._local, \"statistics\"):\n            self._local.statistics = t.cast(\"dict[str, t.Any]\", {})", "new_string": "        if not hasattr(self._local, \"statistics\"):\n            self._local.statistics = t.cast(\n                \"dict[str, t.Any]\", dict(self._restored_statistics)\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/repro_retry && PY=<work>/env-tenacity/bin/python && $PY -I pool_dbg.py && $PY -I pool_main.py && $PY -I check.py | head -4 && cd ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1 && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Rerun pool checks and full test suite"}
[tool_result] main before: {'start_time': 227222.164003416, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
worker sees: {'start_time': 227222.164003416, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
main after: {'start_time': 227222.164003416, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
pool: [2, 3, 4]
pool with retry obj: {'start_time': 227222.292229916, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
call: ok stats attempt: 3
restored stats: True {'start_time': 227222.37583, 'attempt_number': 3, 'idle_for': 0.0, 'delay_since_first_attempt': 3.079199814237654e-05}
restored call: ok 3
retry_if_exception_message retry_if_exception_message
........................................................................ [ 89%]
...............                                                          [100%]
146 passed, 1 skipped, 12 subtests passed in 1.82s
[assistant] All 146 existing tests still pass, and the pool and statistics paths now work. Next I'll add regression tests in the project's style.
[tool_use Bash] {"command": "sed -n 1,60p tests/test_tenacity.py | grep -n \"import\\|^def \\|^class \" ; grep -n \"^def test_.*copy\\|^def test_.*enabled\\|^def test_.*statistic\" tests/test_tenacity.py | head; tail -20 tests/test_tenacity.py", "description": "Inspect test file imports and style"}
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
32:import tenacity
33:from tenacity import RetryCallState, RetryError, Retrying, retry
34:from tenacity.retry import retry_all, retry_any
39:def _make_unset_exception(func_name:
…[319 chars elided]…
self, mock_sleep: typing.Any) -> None:
        with pytest.raises(RetryError):
            self._decorated_fail()
        assert mock_sleep.call_count == 4

    def test_decorated_retry_with(self, mock_sleep: typing.Any) -> None:
        fail_faster = self._decorated_fail.retry_with(
            stop=tenacity.stop_after_attempt(2),
        )
        with pytest.raises(RetryError):
            fail_faster()
        assert mock_sleep.call_count == 1


if __name__ == "__main__":
    unittest.main()
[tool_use Bash] {"command": "grep -n \"^class \\|^@pytest\" tests/test_tenacity.py | tail -12 && sed -n 36,38p tests/test_tenacity.py && grep -n \"^import\\|^from\" tests/test_tenacity.py | head -3", "description": "Find class layout near end of tests"}
[tool_result] 1412:class TestStatisticsKeys:
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
_unset = object()


16:import contextlib
17:import datetime
18:import logging
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\ndef rep(old, new):\n    global s\n    assert s.count(old) == 1, old\n    s = s.replace(old, new)\nrep(\"import logging\\nimport re\\nimport time\\n\", \"import logging\\nimport pickle\\nimport re\\nimport threading\\nimport time\\n\")\nrep('''import tenacity\nfrom tenacity import RetryC
…[3650 chars elided]…
(ValueError(\"other\")) is True\n\n\nif __name__ == \"__main__\":\n    unittest.main()''')\np.write_text(s)\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add pickling regression tests and run suite"}
[tool_result] <work>/env-tenacity/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/test_tenacity.py:2028: in <module>
    class TestPickle:
tests/test_tenacity.py:2079: in TestPickle
    tenacity.retry.retry_if_not_exception_type(ValueError),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'function' obje
…[53 chars elided]…
======================== short test summary info ============================
ERROR tests/test_after.py - AttributeError: 'function' object has no attribut...
ERROR tests/test_asyncio.py - AttributeError: 'function' object has no attrib...
ERROR tests/test_tenacity.py - AttributeError: 'function' object has no attri...
ERROR tests/test_tornado.py - AttributeError: 'function' object has no attrib...
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
4 errors in 0.26s
[assistant] The same `tenacity.retry` name shadowing from the probe applies here, since `retry` the decorator shadows the submodule. I'll import the strategies from `tenacity.retry` directly.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (s.count(old), old)\n    s = s.replace(old, new)\nrep('''from tenacity import (\n    RetryCallState,\n    RetryError,\n    Retrying,\n    retry,\n    retry_if_exception_message,\n    retry_if_exception_type,\n 
…[631 chars elided]…
city.retry.retry_unless_exception_type(ValueError)\", \"retry_unless_exception_type(ValueError)\")\np.write_text(s)\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Fix test imports and run full suite"}
[tool_result]         def fn() -> None:
            pass
    
        restored = pickle.loads(pickle.dumps(fn.retry))
>       assert restored.stop == fn.retry.stop
E       assert <tenacity.stop.stop_after_attempt object at 0x109088920> == <tenacity.stop.stop_after_attempt object at 0x108ff9760>
E        +  where <tenacity.stop.stop_after_attempt object at 0x109088920> = <Retrying object at 0x1093c9490 (stop=<tenacity.stop.stop_after_attempt object at 0x109088920>, wait=<tenacity.wait.wa...109088350>, before=<
…[655 chars elided]…
hing at 0x108e51b20>, name=None)> = <function TestPickle.test_decorated_function_retry_object_round_trip.<locals>.fn at 0x10949e020>.retry

tests/test_tenacity.py:2078: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickle::test_retrying_with_statistics_round_trip
FAILED tests/test_tenacity.py::TestPickle::test_decorated_function_retry_object_round_trip
2 failed, 163 passed, 1 skipped, 12 subtests passed in 1.84s
[assistant] Both failures are my test's fault: stop objects don't define `__eq__`, so they compare by identity. I'll assert on the attribute value instead.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\ndef rep(old, new):\n    global s\n    assert s.count(old) == 1, old\n    s = s.replace(old, new)\nrep('''        assert restored.statistics[\"attempt_number\"] == 1\n        assert restored.stop == r.stop\n''', '''        assert restored.statistics[\"attempt_number\"] == 1\n        asse
…[365 chars elided]…
undational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; ls <work>/env-tenacity/bin/ | grep -E \"ruff|mypy\"", "description": "Fix assertions and rerun full test suite"}
[tool_result] ........................................................................ [ 79%]
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] All 165 pass (146 existing plus 19 new). Next I'll check formatting and lint, if the project's tools are available.
[tool_use Bash] {"command": "grep -n \"ruff\\|mypy\\|pre-commit\" pyproject.toml | head; ls -a | grep -i pre-commit; which ruff mypy uv 2>/dev/null; PY=<work>/env-tenacity/bin/python; $PY -m ruff --version 2>&1 | head -1; $PY -m mypy --version 2>&1|head -1", "description": "Check for lint and type tooling"}
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
ruff not found
mypy not found
uv not found
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
[assistant] Ruff and mypy aren't in the env. I'll try installing them into a separate scratch venv, and fix the obviously long lines by hand in the meantime.
[tool_use Bash] {"command": "cd /tmp && python3 -m venv /tmp/lint-venv >/dev/null 2>&1 && /tmp/lint-venv/bin/pip install -q ruff mypy 2>&1 | tail -2; /tmp/lint-venv/bin/ruff --version; cd ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1 && /tmp/lint-venv/bin/ruff format --check tenacity tests; /tmp/lint-venv/bin/ruff check tenacity tests | tail -3", "description": "Install ruff in scratch venv and check files"}
[tool_result] [notice] A new release of pip is available: 25.0.1 -> 26.2.2
[notice] To update, run: python3.12 -m pip install --upgrade pip
ruff 0.17.2
unformatted: File would be reformatted
  --> tenacity/retry.py:38:13
   |
37 |
   - def _negate(predicate: typing.Callable[..., bool], *args: typing.Any, **kwargs: typing.Any) -> bool:
38 + def _negate(
39 +     predicate: typing.Callable[..., bool], *args: typing.Any, **kwargs: typing.Any
40 + ) -> bool:
41 |     return not predicate(*args, **kwargs)
   |

un
…[49 chars elided]…
s/test_tenacity.py:2067:35
     |
2066 |         results: list[dict[str, typing.Any]] = []
     -         thread = threading.Thread(target=lambda: results.append(pickle.loads(data).statistics))
2067 +         thread = threading.Thread(
2068 +             target=lambda: results.append(pickle.loads(data).statistics)
2069 +         )
2070 |         thread.start()
     |

2 files would be reformatted, 17 files already formatted

Found 15 errors.
15 unsafe fixes available with `--fix --unsafe-fixes`.
[tool_use Bash] {"command": "/tmp/lint-venv/bin/ruff format tenacity/retry.py tests/test_tenacity.py && /tmp/lint-venv/bin/ruff check tenacity tests --output-format concise | head -20; git diff --stat; git stash list | head -0; git show HEAD:tenacity/retry.py > /tmp/repro_retry/base_retry.py; git show HEAD:tests/test_tenacity.py > /tmp/repro_retry/base_test.py; cd /tmp/repro_retry && /tmp/lint-venv/bin/ruff check --output-format concise base_retry.py base_test.py | tail -2", "description": "Format changed files and compare lint with base"}
[tool_result] 2 files reformatted
tenacity/__init__.py:285:23: RUF036 `None` not at the end of the type union.
tenacity/__init__.py:288:31: RUF036 `None` not at the end of the type union.
tenacity/__init__.py:291:15: RUF036 `None` not at the end of the type union.
tenacity/__init__.py:689:44: RUF036 `None` not at the end of the type union.
tenacity/__init__.py:690:43: RUF036 `None` not at the end of the type union.
tenacity/__init__.py:691:50: RUF036 `None` not at the end of the type union.
tenacity/__init__.
…[803 chars elided]…
++++++-
 tenacity/retry.py      |  47 +++++++++++++++-------
 tests/test_tenacity.py | 105 ++++++++++++++++++++++++++++++++++++++++++++++++-
 3 files changed, 157 insertions(+), 17 deletions(-)
head: illegal line count -- 0
Found 12 errors.
[*] 1 fixable with `--fix`.
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1
[This command modified 1 file you've previously read: tenacity/retry.py. Call Read before editing.]
[assistant] The file was modified by my formatter run, so I'll re-read it before any further edits. First I need to see whether the RUF036 warnings are pre-existing or mine.
[tool_use Bash] {"command": "cd /tmp/repro_retry && /tmp/lint-venv/bin/ruff check --output-format concise --select RUF036 base_retry.py | tail -1; cd ~/.cache/lithify/work/repo-fd67065479be/20261023-161020-bug-retrying-objects-and-the-bui/base-1 && /tmp/lint-venv/bin/ruff check --output-format concise --select RUF036 tenacity/retry.py | tail -3; git show HEAD:tenacity/__init__.py > /tmp/repro_retry/base_init.py; /tmp/lint-venv/bin/ruff check --output-format concise --select RUF036 /tmp/repro_retry/base_init.py | tail -1; git diff -U0 tenacity/retry.py | grep \"^+\" | grep \"None\" ", "description": "Compare RUF036 warnings against base"}
[tool_result] 2 unsafe fixes available with `--fix --unsafe-fixes`.
tenacity/retry.py:269:16: RUF036 `None` not at the end of the type union.
Found 2 errors.
2 unsafe fixes available with `--fix --unsafe-fixes`.
9 unsafe fixes available with `--fix --unsafe-fixes`.
[assistant] No new RUF036 warnings: the 15 are all pre-existing, the same as on HEAD. Next I'll run mypy and the tests after the formatting pass.
[tool_use Bash] {"command": "/tmp/lint-venv/bin/pip install -q -e . 2>/dev/null; /tmp/lint-venv/bin/mypy tenacity 2>&1 | tail -8; echo ---; PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Run mypy on package and test suite again"}
[tool_result] tenacity/tornadoweb.py:39: error: Untyped decorator makes function "__call__" untyped  [untyped-decorator]
tenacity/tornadoweb.py:40: error: Unused "type: ignore" comment  [unused-ignore]
tenacity/asyncio/__init__.py:62: error: Cannot find implementation or library stub for module named "sniffio"  [import-not-found]
tenacity/asyncio/__init__.py:62: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
tenacity/asyncio/__init__.py:63: error: Cannot find implementation or library stub for module named "trio"  [import-not-found]
tenacity/asyncio/__init__.py:66: error: Returning Any from function declared to return "Awaitable[None]"  [no-any-return]
tenacity/__init__.py:89: error: Unused "type: ignore" comment  [unused-ignore]
Found 6 errors in 3 files (checked 12 source files)
---
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.77s
[assistant] mypy reports 6 errors, all in untouched lines (tornado, asyncio, and an unused ignore at `__init__.py:89`), and the suite is green. The editable install may have left build artifacts in the repo, so I'll check that and review the full diff.
[tool_use Bash] {"command": "git status --short && git diff -- tenacity/", "description": "Check working tree status and source diff"}
[tool_result]  M tenacity/__init__.py
 M tenacity/_version.py
 M tenacity/retry.py
 M tests/test_tenacity.py
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 591f970..b39664a 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -251,11 +251,29 @@ class BaseRetrying(ABC):
         self.before_sleep = before_sleep
         self.reraise = reraise
         self._local = threading.local()
+        # Statistics restored by unpickling, seeded into each thread on first use
+        self._rest
…[5531 chars elided]…
g 1 required argument 'message' or 'match'"
@@ -252,7 +271,7 @@ class retry_if_not_exception_message(retry_if_exception_message):
         super().__init__(message, match)
         # invert predicate
         if_predicate = self.predicate
-        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
+        self.predicate = functools.partial(_negate, if_predicate)
 
     def __call__(self, retry_state: "RetryCallState") -> bool:
         if retry_state.outcome is None:
[assistant] The `pip install -e` step overwrote the generated `tenacity/_version.py`, which I didn't intend to change. I'll restore that file to HEAD and re-run the tests.
[tool_use Bash] {"command": "git checkout -- tenacity/_version.py && git status --short && PY=<work>/env-tenacity/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2 && git diff -- tests/ | head -150", "description": "Restore generated version file and rerun tests"}
[tool_result]  M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.80s
diff --git a/tests/test_tenacity.py b/tests/test_tenacity.py
index 80060a3..012abd5 100644
--- a/tests/test_tenacity.py
+++ b/tests/test_tenacity.py
@@ -16,7 +16,9 @@
 import contextlib
 import datetime
 import logging
+import pickle
 import re
+import threading
 import time
 import typing
 import
…[3439 chars elided]…
y: typing.Any) -> None:
+        restored = pickle.loads(pickle.dumps(strategy))
+        assert type(restored) is type(strategy)
+
+    def test_predicate_behaviour_survives_round_trip(self) -> None:
+        strategy = pickle.loads(
+            pickle.dumps(retry_if_not_exception_message(message="boom"))
+        )
+        assert strategy.predicate(ValueError("boom")) is False
+        assert strategy.predicate(ValueError("other")) is True
+
+
 if __name__ == "__main__":
     unittest.main()
[assistant] The diff looks right. I'll tidy one inconsistency in the test (mixing `tenacity.stop_after_attempt` with the direct import), and check whether this project adds reno release notes for fixes.
[tool_use Bash] {"command": "git show --stat 39eb157 | tail -8; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | tail -1)", "description": "Check release note convention in recent commits"}
[tool_result]     Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

 doc/source/index.rst         | 32 ++++++++++++++++++++++++
 tenacity/__init__.py         |  8 ++++++
 tenacity/asyncio/__init__.py |  4 +++
 tests/test_asyncio.py        | 17 +++++++++++++
 tests/test_tenacity.py       | 58 ++++++++++++++++++++++++++++++++++++++++++++
 5 files changed, 119 insertions(+)
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\nfor old, new in [(\"            tenacity.stop_after_attempt(2),\\n\", \"            stop_after_attempt(2),\\n\"),\n                 (\"            tenacity.wait_combine(wait_fixed(1), tenacity.wait_none()),\\n\", \"            tenacity.wait_combine(wait_fixed(1), wait_none()),\\n\")]:\n
…[285 chars elided]…
 && /tmp/lint-venv/bin/ruff check --output-format concise tests/test_tenacity.py | tail -1; PY=<work>/env-tenacity/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Tidy test imports, lint, and run final suite"}
[tool_result] 13 files already formatted
All checks passed!
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.80s
 M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
[tool_use Bash] {"command": "grep -n \"def log_it\\|def \\w*(.*) -> .*:$\\|return log_it\\|return \" tenacity/before_sleep.py tenacity/before.py tenacity/after.py | head", "description": "Verify logging callbacks return closures"}
[tool_result] tenacity/before_sleep.py:25:def before_sleep_nothing(retry_state: "RetryCallState") -> None:
tenacity/before_sleep.py:37:    def log_it(retry_state: "RetryCallState") -> None:
tenacity/before_sleep.py:67:    return log_it
tenacity/after.py:25:def after_nothing(retry_state: "RetryCallState") -> None:
tenacity/after.py:36:    def log_it(retry_state: "RetryCallState") -> None:
tenacity/after.py:46:    return log_it
tenacity/before.py:25:def before_nothing(retry_state: "RetryCallState") -> None:
tenacity/before.py:34:    def log_it(retry_state: "RetryCallState") -> None:
tenacity/before.py:42:    return log_it
[assistant] `Retrying` objects and the built-in retry strategies now pickle and restore to working objects, including after they have been used and carry statistics. The suite passes: 165 tests, 1 skipped, up from 146 with 19 new pickling tests. Changes are uncommitted in the worktree.

**Root causes**
- **Strategies:** `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_not_exception_message`, and `retry_if_exception_message` stored lambdas or closures as their predicates. I replaced them with module-level helpers wrapped in `functools.partial`, so behaviour
…[866 chars elided]…
ults. Retry objects with statistics round-trip across processes.

**Not covered:** the callbacks built by `before_log`, `before_sleep_log`, and `after_log` are closures, so they still can't be pickled. Neither can user-supplied lambdas (e.g. `wait_exception(lambda ...)`). Those are outside the strategy classes this bug names, so I left them alone. Say if you want them handled too.

**Lint:** ruff format and check pass on the changed files, with the 15 RUF036 warnings all pre-existing. mypy reports 6 errors, all on untouched lines. I installed ruff and mypy into a scratch venv outside the repo.
