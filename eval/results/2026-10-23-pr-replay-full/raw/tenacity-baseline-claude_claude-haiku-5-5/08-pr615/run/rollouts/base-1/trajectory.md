# trajectory base-1

final message:
`Retrying` objects and the built-in retry strategies now pickle with the standard `pickle` module, so `@retry`-decorated functions work with `multiprocessing` (`Pool.map` returned `[2, 4, 6]` in a check). The test suite passes: 151 passed, 1 skipped. Nothing is committed.

**What was broken**
- `BaseRetrying` held a `threading.local`, which can't be pickled.
- Several predicate strategies stored lambdas or closures: `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message`, `retry_if_not_exception_message`. The ones that wrap `retry_if_exception_type` (including `retry_any`/`retry_all` built on it) failed too.

**What changed**
- `tenacity/retry.py`: the lambdas and closures are replaced by small module-level helpers bound with `functools.partial`. Behaviour is unchanged.
- `tenacity/__init__.py`: `BaseRetrying.__getstate__`/`__setstate__` drop the `threading.local`, carry the calling thread's statistics across, and recreate the local storage on load. Because `AsyncRetrying` inherits from `BaseRetrying`, it gets the same behaviour.
- `tests/test_tenacity.py`: a new `TestPickle` class. Five of its tests fail on the original code and pass now.
- `releasenotes/notes/make-retrying-picklable-c45faf1f3d7c2a29.yaml`: a `fixes:` note in the repo's reno format.

**Decisions to check**
- Statistics are kept per the calling thread, matching how they're stored today. The per-call `iter_state` is reset on load, since it holds transient lambdas.
- As a side effect, `copy.deepcopy(retrying)` now works where it used to raise.

**Not covered**
- Hooks built with closures still don't pickle: `before_log`, `after_log`, `before_sleep_log`. A `Retrying` that uses them will still fail. I left these out because they are hooks rather than strategies, and fixing them means converting them to classes.
- User-supplied callables (such as a `wait_exception` lambda) and `threading.Event` objects (`stop_when_event_set`, `sleep_using_event`) still can't be pickled. That is up to the caller.

Ruff and mypy are configured in the project but aren't installed in the test environment, so I didn't run them. I checked that the added lines stay within the 88-column limit.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls -R | grep -v pyc | head -50 && wc -l $(git ls-files | grep -E '\\.py$')", "description": "Inspect repo layout and Python sources"}
[tool_result] 854b410 lithify: probe base
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

./doc:
source

./doc/source:
api.rst
changelog.rst
conf.py
index.rst

./releasenotes:
notes

./releasenotes/notes:
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
add-re-pattern-to-match-types-6a4c1d9e64e2a5e1.yaml
add-reno-d1ab5710f272650a.yaml
add-retry_except_exc
…[1098 chars elided]…
py
     217 tenacity/asyncio/__init__.py
     136 tenacity/asyncio/retry.py
      42 tenacity/before.py
      67 tenacity/before_sleep.py
      43 tenacity/nap.py
     297 tenacity/retry.py
     130 tenacity/stop.py
      62 tenacity/tornadoweb.py
     271 tenacity/wait.py
       0 tests/__init__.py
      84 tests/test_after.py
     535 tests/test_asyncio.py
     116 tests/test_issue_478.py
    2013 tests/test_tenacity.py
      78 tests/test_tornado.py
      57 tests/test_utils.py
    5133 total
[tool_use Bash] {"command": "cat AGENTS.md | head -80; grep -n \"class \\|def __init__\\|self\\.\\w* = \\|__slots__\\|__getstate__\\|__setstate__\\|__reduce__\" tenacity/__init__.py tenacity/retry.py tenacity/stop.py tenacity/wait.py tenacity/asyncio/*.py | head -150", "description": "Read agent notes and find classes and state attrs"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[9074 chars elided]…
 = exp_base
tenacity/wait.py:209:class wait_random_exponential(wait_exponential):
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
tenacity/wait.py:252:    def __init__(
tenacity/wait.py:259:        self.initial = initial
tenacity/wait.py:260:        self.max = max
tenacity/wait.py:261:        self.exp_base = exp_base
tenacity/wait.py:262:        self.jitter = jitter
tenacity/asyncio/__init__.py:74:class AsyncRetrying(BaseRetrying):
tenacity/asyncio/__init__.py:75:    def __init__(
[tool_use Bash] {"command": "sed -n 225,520p tenacity/__init__.py", "description": "Read BaseRetrying and Retrying"}
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
…[10357 chars elided]…
(result)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                return do  # type: ignore[no-any-return]


class Future(futures.Future[t.Any]):
    """Encapsulates a (future or past) attempted call to a target function."""

    def __init__(self, attempt_number: int) -> None:
        super().__init__()
        self.attempt_number = attempt_number

    @property
    def failed(self) -> bool:
[tool_use Bash] {"command": "sed -n 60,297p tenacity/retry.py; echo ----; sed -n 1,130p tenacity/stop.py | grep -v '^\\s*$' | tail -90", "description": "Read retry and stop strategy classes"}
[tool_result] RetryBaseT = retry_base | typing.Callable[["RetryCallState"], bool]


class _retry_never(retry_base):
    """Retry strategy that never rejects any result."""

    def __call__(self, retry_state: "RetryCallState") -> bool:
        return False


retry_never = _retry_never()


class _retry_always(retry_base):
    """Retry strategy that always rejects any result."""

    def __call__(self, retry_state: "RetryCallState") -> bool:
        return True


retry_always = _retry_always()


class retry_if_
…[10835 chars elided]…
sure that the max_delay is not exceeded.
    """
    def __init__(self, max_delay: _utils.time_unit_type) -> None:
        self.max_delay = _utils.to_seconds(max_delay)
    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.seconds_since_start is None:
            raise RuntimeError("__call__() called but seconds_since_start is not set")
        return (
            retry_state.seconds_since_start + retry_state.upcoming_sleep
            >= self.max_delay
        )
[tool_use Bash] {"command": "grep -n \"lambda\\|def .*(\\|pickle\" tenacity/wait.py tenacity/asyncio/retry.py tenacity/before.py tenacity/after.py tenacity/before_sleep.py tenacity/nap.py tenacity/_utils.py | head -60; echo ---; sed -n 1,40p tenacity/asyncio/retry.py | grep -n \"import\\|class\"; grep -rn \"pickle\" tests tenacity | head; sed -n 25,46p tenacity/wait.py; sed -n 1,40p tenacity/__init__.py | grep -n \"import\"", "description": "Search for lambdas, pickle references and imports"}
[tool_result] tenacity/after.py:25:def after_nothing(retry_state: "RetryCallState") -> None:
tenacity/after.py:29:def after_log(
tenacity/after.py:36:    def log_it(retry_state: "RetryCallState") -> None:
tenacity/wait.py:31:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:34:    def __add__(self, other: "wait_base") -> "wait_combine":
tenacity/wait.py:37:    def __radd__(self, other: "wait_base") -> typing.Union["wait_combine", "wait_base"]:
tenacity/wait.py:50:    def __init_
…[5112 chars elided]…
ait_base | typing.Callable[["RetryCallState"], float | int]


18:import dataclasses
19:import functools
20:import sys
21:import threading
22:import time
23:import typing as t
24:import warnings
25:from abc import ABC, abstractmethod
26:from concurrent import futures
28:from . import _utils
31:from .after import after_log, after_nothing
34:from .before import before_log, before_nothing
37:from .before_sleep import before_sleep_log, before_sleep_nothing
40:from .nap import sleep, sleep_using_event
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY; cat > /tmp/repro_pickle.py <<'EOF'\nimport pickle, tenacity\nfrom tenacity import retry, Retrying, stop_after_attempt, retry_if_exception_type, retry_if_exception_message, retry_if_not_exception_message, retry_if_res
…[1872 chars elided]…
ementing(),\n \"wait_jitter\": wait_exponential_jitter(), \"wait_exc\": wait_exception(lambda e: 1),\n}\nfor name, obj in cases.items():\n    try:\n        pickle.loads(pickle.dumps(obj)); print(\"ok  \", name)\n    except Exception as e:\n        print(\"FAIL\", name, type(e).__name__, str(e)[:90])\nEOF\n$PY -I /tmp/repro_pickle.py", "description": "Reproduce pickling failures across strategies"}
[tool_result ERROR] Exit code 1
lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "/tmp/repro_pickle.py", line 1, in <module>
    import pickle, tenacity
ModuleNotFoundError: No module named 'tenacity'
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_pickle.py", "description": "Run pickling reproduction with repo on path"}
[tool_result] FAIL Retrying AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL exc_type AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL not_exc_type AttributeError Can't get local object 'retry_if_not_exception_type.__init__.<locals>.<lambda>'
FAIL unless_exc_type AttributeError Can't get local object 'retry_unless_exception_type.__init__.<locals>.<lambda>'
FAIL exc_msg AttributeError Can't get local object 'retry_if_
…[490 chars elided]…
_type.__init__.<locals>.<lambda>'
FAIL all AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
ok   never
ok   always
ok   stop_after_delay
ok   stop_before
ok   stop_any
ok   stop_all
ok   stop_never
ok   wait_fixed
ok   wait_none
ok   wait_random
ok   wait_combine
ok   wait_chain
ok   wait_exp
ok   wait_rexp
ok   wait_inc
ok   wait_jitter
FAIL wait_exc PicklingError Can't pickle <function <lambda> at 0x1017682c0>: attribute lookup <lambda> on __main__ fai
[tool_use Bash] {"command": "sed -n 14,24p tenacity/retry.py; sed -n 1915,1940p tests/test_tenacity.py; grep -rn \"is retry_never\\|is retry_always\\|is stop_never\\|\\.predicate\" tenacity tests | head; ls releasenotes/notes | grep -i pickl; cat releasenotes/notes/add-stop-before-delay-a775f88ac872c923.yaml; grep -n \"^import\\|^from\" tests/test_tenacity.py", "description": "Check imports, existing pickle test and release note style"}
[tool_result] # See the License for the specific language governing permissions and
# limitations under the License.

import abc
import re
import typing

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


            f.calls.append(len(f.calls) + 1)  # type: ignore[attr-defined]
            raise CustomError("Retry it!")

        f.calls = []  # type: ignore[attr-defined]

        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
        with pytest.raises(CustomError):
     
…[1618 chars elided]…
rable than returning after that timeout.16:import contextlib
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
[assistant] Reproduced: the built-in predicate strategies store lambdas/closures, and `BaseRetrying` holds a `threading.local`. I'll replace the closures with module-level helpers bound via `functools.partial`, and add `__getstate__`/`__setstate__` to the base class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing\n", "new_string": "import abc\nimport functools\nimport re\nimport typing\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "retry_always = _retry_always()\n\n\nclass retry_if_exception(retry_base):\n    \"\"\"Retry strategy that retries if an exception verifies a predicate.\"\"\"\n\n    def __init__(self, predicate: typing.Callable[[BaseExce
…[4361 chars elided]…
s_exception_type(retry_if_exception):\n    \"\"\"Retries until an exception is raised of one or more types.\"\"\"\n\n    def __init__(\n        self,\n        exception_types: type[BaseException]\n        | tuple[type[BaseException], ...] = Exception,\n    ) -> None:\n        self.exception_types = exception_types\n        super().__init__(functools.partial(_is_not_instance_of, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        # set predicate\n        if message:\n\n            def message_fnc(exception: BaseException) -> bool:\n                return message == str(exception)\n\n            predicate = message_fnc\n        elif match
…[89 chars elided]…
tion) -> bool:\n                return bool(prog.match(str(exception)))\n\n            predicate = match_fnc\n        else:", "new_string": "        # set predicate\n        if message:\n            predicate = functools.partial(_is_message_equal, message)\n        elif match:\n            prog = re.compile(match)\n            predicate = functools.partial(_is_message_match, prog)\n        else:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py", "old_string": "        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)", "new_string": "        self.predicate = functools.partial(_negate, if_predicate)"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/retry.py has been updated successfully.
[assistant] Now the base class: drop the unpicklable `threading.local` on save, carry the calling thread's statistics across, and rebuild the local storage on load.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "        self._name = name\n        self.enabled = enabled\n\n    def copy(", "new_string": "        self._name = name\n        self.enabled = enabled\n\n    def __getstate__(self) -> dict[str, t.Any]:\n        state 
…[139 chars elided]…
 the thread-local storage when unpickling.\n        del state[\"_local\"]\n        state[\"_statistics\"] = self.statistics\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self._local.statistics = statistics\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_pickle.py; cat > /tmp/mp_check.py <<'EOF'\nimport pickle, logging\nfrom multiprocessing import Pool\nfrom tenacity import retry, Retrying, stop_after_attempt, wait_none, retry_if_exception_message\
…[366 chars elided]…
umps(r))\n    print(\"stats kept:\", clone.statistics == r.statistics, clone.statistics)\n    print(\"works:\", clone(lambda: 42))\n    print(\"stop/wait kept:\", type(clone.stop).__name__, type(clone.wait).__name__)\n    import copy as c\n    print(\"deepcopy:\", c.deepcopy(r)(lambda: 7))\nEOF\nPYTHONPATH=$PWD $PY /tmp/mp_check.py", "description": "Rerun pickling repro and multiprocessing check"}
[tool_result] ok   Retrying
ok   exc_type
ok   not_exc_type
ok   unless_exc_type
ok   exc_msg
ok   exc_match
ok   not_exc_msg
ok   not_exc_match
ok   cause
ok   res
ok   not_res
ok   any
ok   all
ok   never
ok   always
ok   stop_after_delay
ok   stop_before
ok   stop_any
ok   stop_all
ok   stop_never
ok   wait_fixed
ok   wait_none
ok   wait_random
ok   wait_combine
ok   wait_chain
ok   wait_exp
ok   wait_rexp
ok   wait_inc
ok   wait_jitter
FAIL wait_exc PicklingError Can't pickle <function <lambda> at 0x1048f8040>: attribute lookup <lambda> on __main__ fai
pool.map: [2, 4, 6]
stats kept: True {'start_time': 238005.3592915, 'attempt_number': 1, 'idle_for': 0, 'delay_since_first_attempt': 0}
works: 42
stop/wait kept: stop_after_attempt wait_none
deepcopy: 7
[assistant] Pool, stats preservation, and deepcopy all work. The one remaining failure is `wait_exception` given a user-supplied lambda, which is the caller's own choice. Next, regression tests and a release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(expected.last_attempt, actual.last_attempt)\n\n\nclass TestRetryTyping(unittest.TestCase):", "new_string": "        self.assertEqual(expected.last_attempt, actual.last_attempt)\n\n\nclass T
…[3680 chars elided]…
      strategy = tenacity.retry_any(\n            tenacity.retry_if_exception_type(ValueError),\n            tenacity.retry_all(tenacity.retry_if_result(bool), tenacity.retry_never),\n        )\n        actual = pickle.loads(pickle.dumps(strategy))\n        assert isinstance(actual, retry_any)\n        assert isinstance(actual.retries[1], retry_all)\n\n\nclass TestRetryTyping(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] The strategy-roundtrip test got convoluted in the cause branch. I'll rewrite it with explicit states.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_strategies_are_pickleable(self) -> None:\n        import pickle\n\n        strategies: list[tuple[typing.Any, typing.Any]] = [\n            (tenacity.retry_if_exception_type(ValueError), TypeErro
…[3445 chars elided]…
_if_result(lambda r: r > 1), succeeded(2)),\n            (tenacity.retry_if_not_result(lambda r: r > 1), succeeded(2)),\n        ]\n        for strategy, state in cases:\n            actual = pickle.loads(pickle.dumps(strategy))\n            assert type(actual) is type(strategy)\n            assert actual(state) == strategy(state)\n\n    def test_composed_strategies_are_pickleable(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] I just used a lambda in the `retry_if_result` cases, which can't be pickled. Switching those to `bool`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "            (tenacity.retry_if_result(lambda r: r > 1), succeeded(2)),\n            (tenacity.retry_if_not_result(lambda r: r > 1), succeeded(2)),", "new_string": "            (tenacity.retry_if_result(bool), succeeded(0)),\n            (tenacity.retry_if_not_result(bool), succeeded(0)),"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with project checks command"}
[tool_result] ............s............................................... [ 39%]
........................................................................ [ 86%]
....................                                                     [100%]
151 passed, 1 skipped, 12 subtests passed in 1.87s
[assistant] Full suite passes (151 passed). Next I'll confirm the new tests fail on the original code, and run the repo's linters.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; rm -rf /tmp/orig_tn && mkdir /tmp/orig_tn && git archive HEAD | tar -x -C /tmp/orig_tn && cp tests/test_tenacity.py /tmp/orig_tn/tests/ && (cd /tmp/orig_tn && $PY -m pytest -q -p no:cacheprovider --color=no -k \"Pickle\" 2>&1 | tail -8); echo ---; grep -n \"ruff\\|black\\|mypy\\|line-length\\|line_length\" pyproject.toml .pre-commit-config.yaml 2>/dev/null | head; for t in ruff black mypy; do $PY -m $t --version 2>/dev/null; done; $PY -m pytest -q -p no:cacheprovider --color=no -k Pickle --co 2>&1 | tail -3", "description": "Verify new tests fail on original code and check linter config"}
[tool_result] tests/test_tenacity.py:1963: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickle::test_composed_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickle::test_decorated_function_retry_is_pickleable
FAILED tests/test_tenacity.py::TestPickle::test_retry_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickle::test_retrying_is_pickleable - Attr...
FAILED tests/test_tenacity.py::TestPickle::test_used_retrying_keeps_statistics
5 failed, 1 passed, 146 deselected in 0.13s
---
59:    "ruff",
60:    "mypy",
72:mypy = "mypy"
77:    { cmd = "ruff check --fix ." },
78:    { cmd = "ruff format ." },
83:    { cmd = "ruff check ." },
84:    { cmd = "ruff format --check ." },
90:    { ref = "mypy" },
99:[tool.ruff]
100:line-length = 88
tests/test_tenacity.py::TestPickle::test_used_retrying_keeps_statistics

6/152 tests collected (146 deselected) in 0.03s
[assistant] Five new tests fail on the original code and pass with the fix (the sixth match is the existing `RetryError` pickle test). The linters didn't print versions, so I'll check whether they're on PATH.
[tool_use Bash] {"command": "which ruff mypy black uv 2>/dev/null; sed -n 55,100p pyproject.toml | grep -n \"\" | head -5; ruff --version 2>/dev/null && ruff format --check tenacity tests && ruff check tenacity tests; mypy --version 2>/dev/null && mypy tenacity 2>&1 | tail -3", "description": "Check for ruff and mypy availability and run them"}
[tool_result ERROR] Exit code 127
ruff not found
mypy not found
black not found
uv not found
1:    "poethepoet",
2:    "pytest",
3:    "tornado>=6.0",
4:    "typeguard",
5:    "ruff",
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m ruff --version 2>&1 | head -1; $PY -m mypy --version 2>&1 | head -1; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/retry.py tenacity/__init__.py tests/test_tenacity.py | head", "description": "Check ruff/mypy in project env and long lines"}
[tool_result] <work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
tenacity/retry.py: 185: 90
tenacity/retry.py: 250: 90
tenacity/retry.py: 261: 95
tenacity/__init__.py: 636: 114
tenacity/__init__.py: 725: 90
tenacity/__init__.py: 726: 106
tests/test_tenacity.py: 51: 89
tests/test_tenacity.py: 135: 89
tests/test_tenacity.py: 423: 105
tests/test_tenacity.py: 907: 99
[tool_use Bash] {"command": "sed -n 250p tenacity/retry.py; sed -n 261p tenacity/retry.py; git diff -U0 | grep '^+' | awk 'length > 89' ", "description": "Check whether any added lines exceed 88 columns"}
[tool_result]                 f"{self.__class__.__name__}() takes either 'message' or 'match', not both"
                f"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'"
[assistant] Added lines are all within 88 columns (the long ones are pre-existing). Last, a release note in the repo's reno format.
[tool_use Bash] {"command": "python3 -c \"import secrets;print(secrets.token_hex(8))\" && ls releasenotes/notes | grep -c yaml && grep -l \"^fixes:\" releasenotes/notes/*.yaml | head -2 | xargs -I{} sh -c 'echo == {}; cat {}'", "description": "Generate release note id and view a fixes note example"}
[tool_result] c45faf1f3d7c2a29
45
== releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
---
fixes:
  - "Fixes test failures with typeguard 3.x"
== releasenotes/notes/add-re-pattern-to-match-types-6a4c1d9e64e2a5e1.yaml
---
fixes:
  - |
    Added `re.Pattern` to allowed match types.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/releasenotes/notes/make-retrying-picklable-c45faf1f3d7c2a29.yaml", "content": "---\nfixes:\n  - |\n    ``Retrying`` objects, including ones that have already been used, and the\n    built-in retry strategies (``retry_if_exception_type``,\n    ``retry_if_exception_message``, ``retry_if_not_result``, ...) can now be\n    pickled. This makes functions decorated with ``@retry`` usable with\n    ``multiprocessing``, e.g. ``Pool.map``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-38fec5e48183/20261023-191104-bug-retrying-objects-and-the-bui/base-1/releasenotes/notes/make-retrying-picklable-c45faf1f3d7c2a29.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "rm -rf /tmp/orig_tn /tmp/repro_pickle.py /tmp/mp_check.py; PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git status --short; git diff --stat", "description": "Final test run, cleanup temp files, and show diff stats"}
[tool_result] 151 passed, 1 skipped, 12 subtests passed in 1.80s
 M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/make-retrying-picklable-c45faf1f3d7c2a29.yaml
 tenacity/__init__.py   |  14 +++++++
 tenacity/retry.py      |  51 ++++++++++++++++++-------
 tests/test_tenacity.py | 101 +++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 152 insertions(+), 14 deletions(-)
[assistant] `Retrying` objects and the built-in retry strategies now pickle with the standard `pickle` module, so `@retry`-decorated functions work with `multiprocessing` (`Pool.map` returned `[2, 4, 6]` in a check). The test suite passes: 151 passed, 1 skipped. Nothing is committed.

**What was broken**
- `BaseRetrying` held a `threading.local`, which can't be pickled.
- Several predicate strategies stored lambdas or closures: `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message`, `retry_if_not_exception_message`. The ones that wrap `retry_i
…[1030 chars elided]…
h closures still don't pickle: `before_log`, `after_log`, `before_sleep_log`. A `Retrying` that uses them will still fail. I left these out because they are hooks rather than strategies, and fixing them means converting them to classes.
- User-supplied callables (such as a `wait_exception` lambda) and `threading.Event` objects (`stop_when_event_set`, `sleep_using_event`) still can't be pickled. That is up to the caller.

Ruff and mypy are configured in the project but aren't installed in the test environment, so I didn't run them. I checked that the added lines stay within the 88-column limit.
