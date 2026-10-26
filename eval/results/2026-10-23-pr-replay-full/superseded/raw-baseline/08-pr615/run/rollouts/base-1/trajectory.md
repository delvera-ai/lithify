# trajectory base-1

final message:
`Retrying` objects (fresh or already used) and the built-in retry strategies now pickle and unpickle into working equivalents. The full suite passes: 151 passed, 1 skipped, with the 5 new tests failing on the original code.

**Root causes**
- `BaseRetrying` stores its per-thread state (including `statistics`) in a `threading.local`, which can't be pickled.
- `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` and `retry_if_not_exception_message` stored lambdas or closures as their predicate.
- Decorated functions themselves already pickled by reference, so `Pool.map(decorated_fn, ...)` worked. The failure only appeared when a `Retrying` object was pickled, for example one passed as an argument or reached through `fn.retry`.

**Changes**
- `tenacity/__init__.py`: `BaseRetrying.__getstate__` / `__setstate__` drop the `threading.local`, carry the calling thread's statistics across, and rebuild the local on load. This also covers `AsyncRetrying` and `TornadoRetrying`, which inherit from it.
- `tenacity/retry.py`: the lambdas and closures are replaced by `functools.partial` over module-level helpers. Predicate behaviour is unchanged.
- `tests/test_tenacity.py`: a new `TestPickling` class covering a fresh `Retrying`, a used one with statistics (restored, and still retries correctly), `fn.retry`, each built-in strategy's behaviour after a round trip, and a composed `retry_any`.
- `releasenotes/notes/picklable-retrying-3f1c9a7e2b5d8048.yaml`: a reno fix note.

**Verification**
- A `Pool(2).map` run with a decorated function, and one with a `Retrying` object as an argument, both return the expected results.
- Ruff and mypy report the same counts as `HEAD`. Their findings are on lines I didn't touch, and I ran them from a scratch venv because the project's check venv has no pip. A `ruff format` fix was applied to `retry.py`.
- Nothing is committed.

**Things to know**
- Statistics carry over as-is, so `start_time` is a `time.monotonic()` value from the original process. It's only meaningful within the same clock, so treat it as informational after a round trip.
- Pickling still fails for user-supplied values that aren't picklable, such as a lambda `sleep` or `before` callback. That's expected, but worth knowing.
- Out of scope, and worth a follow-up: `RetryError` carries a `concurrent.futures.Future` that holds a lock. If every attempt fails inside a `Pool` worker, the error can't be sent back to the parent and `multiprocessing` raises `MaybeEncodingError`. The fix would be to make `RetryError` picklable as well. I didn't change that because it alters exception semantics, so tell me if you want it included.

## events
[tool_use Bash] {"command": "git status --short && ls && cat tenacity/__init__.py | head -150 && ls tenacity tests && wc -l tenacity/*.py", "description": "Inspect repo layout and core retry module"}
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
# Copyright 2016-2018 Julien Danjou
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
# Unless require
…[3503 chars elided]…
py
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
[tool_use Bash] {"command": "sed -n 150,797p tenacity/__init__.py", "description": "Read the Retrying class in tenacity/__init__.py"}
[tool_result]     REPR_FIELDS: t.Sequence[str] = ()
    NAME: str | None = None

    def __repr__(self) -> str:
        state_str = ", ".join(
            f"{field}={getattr(self, field)!r}" for field in self.REPR_FIELDS
        )
        return f"{self.__class__.__name__}({state_str})"

    def __str__(self) -> str:
        return repr(self)


class RetryAction(BaseAction):
    REPR_FIELDS = ("sleep",)
    NAME = "retry"

    def __init__(self, sleep: t.SupportsFloat) -> None:
        self.sleep = float(slee
…[21151 chars elided]…
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
[tool_use Bash] {"command": "cat tenacity/retry.py && cat tenacity/stop.py && cat tenacity/wait.py", "description": "Read retry, stop and wait strategy modules"}
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
…[22264 chars elided]…
   jitter: float = 1,
    ) -> None:
        self.initial = initial
        self.max = max
        self.exp_base = exp_base
        self.jitter = jitter

    def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.initial * exp + jitter
        except OverflowError:
            result = self.max
        return max(0, min(result, self.max))
[tool_use Bash] {"command": "cat tenacity/nap.py | sed -n 15,50p; grep -n \"def \\|lambda\\|_local\\|threading\" tenacity/before.py tenacity/after.py tenacity/before_sleep.py tenacity/asyncio/__init__.py tenacity/asyncio/retry.py tenacity/tornadoweb.py | head -80; ls <work>/env-tenacity/bin/python 2>&1; python3 --version; ls releasenotes/notes | tail -5; cat AGENTS.md | head -60", "description": "Check remaining modules, env python, and repo guidance"}
[tool_result] # See the License for the specific language governing permissions and
# limitations under the License.

import time
import typing

if typing.TYPE_CHECKING:
    import threading


def sleep(seconds: float) -> None:
    """
    Sleep strategy that delays execution for a given number of seconds.

    This is the default strategy, and may be mocked out for unit testing.
    """
    time.sleep(seconds)


class sleep_using_event:
    """Sleep strategy that waits on an event to be set."""

    def __in
…[4461 chars elided]…
it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[assistant] Let me reproduce the failures before changing anything.
[tool_use Bash] {"command": "mkdir -p /tmp/pickle-repro && cat > /tmp/pickle-repro/repro.py <<'EOF'\nimport pickle, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1\")\nimport tenacity\nfrom tenacity import Retrying, retry, stop_after_attempt, retry_if_exception_type, retry_if_exception_message, retry_if_not_exception_message, r
…[1586 chars elided]…
__ == \"__main__\":\n    from multiprocessing import Pool\n    with Pool(2) as p:\n        print(\"Pool.map:\", p.map(f, [1, 2]))\nEOF\n<work>/env-tenacity/bin/python -I /tmp/pickle-repro/repro.py 2>&1 | tail -40", "description": "Reproduce pickling failures on current code"}
[tool_result] OK   retry_if_result(pred module fn)
OK   stop_after_attempt
OK   stop_never
OK   wait_none
FAIL retry_any(...) AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
OK   retry_never
decorated f: 6
FAIL Retrying() AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL Retrying(stop=..., wait=...) AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
FAIL retry_if_exception_type() At
…[2049 chars elided]…
e(match=) AttributeError Can't get local object 'retry_if_exception_message.__init__.<locals>.match_fnc'
FAIL retry_if_not_exception_message(message=) AttributeError Can't get local object 'retry_if_not_exception_message.__init__.<locals>.<lambda>'
OK   retry_if_result(pred module fn)
OK   stop_after_attempt
OK   stop_never
OK   wait_none
FAIL retry_any(...) AttributeError Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
OK   retry_never
decorated f: 6
Pool.map: [2, 4]
[assistant] The failure is confirmed: a decorated function pickles fine by reference, but any `Retrying` object (and its default `retry_if_exception_type()`) does not. Two causes: `BaseRetrying` holds a `threading.local`, and the retry strategies store lambdas/closures as predicates. I'll fix the predicates first, using module-level functions bound with `functools.partial` so the state stays picklable.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\" tenacity/retry.py && grep -n \"class AsyncRetrying\\|class TornadoRetrying\\|class BaseRetrying\" -r tenacity && sed -n 60,110p tenacity/asyncio/__init__.py && grep -n \"pickle\\|class Test\\|^def test_\" tests/test_tenacity.py | head -20 && ls releasenotes/notes | head -3 && cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml", "description": "Check imports, async classes, test and release-note conventions"}
[tool_result] 17:import abc
18:import re
19:import typing
tenacity/tornadoweb.py:28:class TornadoRetrying(BaseRetrying):
tenacity/__init__.py:229:class BaseRetrying(ABC):
tenacity/asyncio/__init__.py:74:class AsyncRetrying(BaseRetrying):
    if "trio" in sys.modules:
        # If trio is available, then sniffio is too
        import sniffio
        import trio

        if sniffio.current_async_library() == "trio":
            return trio.sleep(seconds)
    # Otherwise, assume asyncio
    # Lazy import asyncio
…[2226 chars elided]…
est.TestCase):
1856:class TestInvokeAsCallable:
1926:class TestRetryException(unittest.TestCase):
1927:    def test_retry_error_is_pickleable(self) -> None:
1928:        import pickle
1931:        pickled = pickle.dumps(expected)
1932:        actual = pickle.loads(pickled)
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
[assistant] Now the predicate changes in `retry.py`.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tenacity/retry.py\")\ns = p.read_text()\n\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (s.count(old), old)\n    s = s.replace(old, new)\n\nrep(\"import a
…[1910 chars elided]…
 prog = re.compile(match)\n            predicate = functools.partial(_message_matches, prog)\n''')\n\nrep('''        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)''',\n    '''        self.predicate = functools.partial(_negate, if_predicate)''')\n\np.write_text(s)\nEOF\ngit diff --stat", "description": "Replace lambda and closure predicates with picklable partials"}
[tool_result]  tenacity/retry.py | 48 +++++++++++++++++++++++++++++++++++-------------
 1 file changed, 35 insertions(+), 13 deletions(-)
[assistant] The notice is expected, since my own script wrote `retry.py`. I'll re-read the affected region before editing `__init__.py`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "offset": 255, "limit": 15}
[tool_result] 255	        self.retry_error_callback = retry_error_callback
256	        self._name = name
257	        self.enabled = enabled
258	
259	    def copy(
260	        self,
261	        sleep: t.Callable[[int | float], None] | object = _unset,
262	        stop: t.Union["StopBaseT", object] = _unset,
263	        wait: t.Union["WaitBaseT", object] = _unset,
264	        retry: retry_base | object = _unset,
265	        before: t.Callable[["RetryCallState"], None] | object = _unset,
266	        after: t.Callable[["RetryCallState"], None] | object = _unset,
267	        before_sleep: t.Callable[["RetryCallState"], None] | None | object = _unset,
268	        reraise: bool | object = _unset,
269	        retry_error_cls: type[RetryError] | object = _unset,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py", "old_string": "        self._name = name\n        self.enabled = enabled\n\n    def copy(", "new_string": "        self._name = name\n        self.enabled = enabled\n\n    def __getstate__(self) -> dict[str, t.Any]:\n        # thre
…[136 chars elided]…
te__.\n        state = self.__dict__.copy()\n        del state[\"_local\"]\n        state[\"_statistics\"] = self.statistics\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        statistics = state.pop(\"_statistics\")\n        self.__dict__.update(state)\n        self._local = threading.local()\n        self.statistics.update(statistics)\n\n    def copy("}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll re-run the reproduction and the existing test suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I /tmp/pickle-repro/repro.py 2>&1 | sort | uniq -c | head -40; echo ---; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Re-run pickle repro and full test suite"}
[tool_result]    3 OK   Retrying()
   3 OK   Retrying(stop=..., wait=...)
   3 OK   retry_any(...)
   3 OK   retry_if_exception_message(match=)
   3 OK   retry_if_exception_message(message=)
   3 OK   retry_if_exception_type()
   3 OK   retry_if_exception_type(ValueError)
   3 OK   retry_if_not_exception_message(message=)
   3 OK   retry_if_not_exception_type()
   3 OK   retry_if_result(pred module fn)
   3 OK   retry_never
   3 OK   retry_unless_exception_type()
   3 OK   stop_after_attempt
   3 OK   stop_never
   3 OK   wait_none
   1 Pool.map: [2, 4]
   3 decorated f: 6
---
............s............................................... [ 40%]
........................................................................ [ 89%]
...............                                                          [100%]
146 passed, 1 skipped, 12 subtests passed in 1.83s
[assistant] Everything passes now. Next I'll add regression tests next to the existing pickle test, following its style.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_tenacity.py | grep -n \"import\" ; sed -n 1920,1945p tests/test_tenacity.py; wc -l tests/test_tenacity.py", "description": "Look at existing pickle test and imports"}
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
        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
        with pytest.raises(CustomError):
            self.invoke(retry, f)
        assert f.calls == 
…[267 chars elided]…
xpected)
        actual = pickle.loads(pickled)
        self.assertEqual(expected.last_attempt, actual.last_attempt)


class TestRetryTyping(unittest.TestCase):
    def test_retry_type_annotations(self) -> None:
        """The decorator should maintain types of decorated functions."""

        def num_to_str(number):
            # type: (int) -> str
            return str(number)

        # equivalent to a raw @retry decoration
        with_raw = retry(num_to_str)
    2013 tests/test_tenacity.py
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(expected.last_attempt, actual.last_attempt)\n\n\nclass TestRetryTyping(unittest.TestCase):", "new_string": "        self.assertEqual(expected.last_attempt, actual.last_attempt)\n\n\nclass T
…[2733 chars elided]…
  assert actual(state) is expected, strategy\n\n    def test_composed_retry_strategies_are_pickleable(self) -> None:\n        strategy = tenacity.retry_if_exception_type(\n            ValueError\n        ) | tenacity.retry_if_result(lambda r: r is None)\n        actual = self.roundtrip(strategy)\n        assert isinstance(actual, tenacity.retry_any)\n\n\nclass TestRetryTyping(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] I left a placeholder assertion and a lambda that can't be pickled in that block. Fixing both before running anything.
[tool_use Bash] {"command": "grep -n \"class NoneReturnUntilAfterCount\\|^from tenacity\\|RetryCallState\" tests/test_tenacity.py | head; sed -n 30,50p tests/test_tenacity.py", "description": "Check test helper names and tenacity imports"}
[tool_result] 33:from tenacity import RetryCallState, RetryError, Retrying, retry
34:from tenacity.retry import retry_all, retry_any
48:def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
61:) -> RetryCallState:
62:    """Construct RetryCallState for given attempt number & delay.
76:    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
100:        rs = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
136:        captured: list[RetryCallState
…[302 chars elided]…
et_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
    missing = []
    for k, v in kwargs.items():
        if v is _unset:
            missing.append(k)
    missing_str = ", ".join(repr(s) for s in missing)
    return TypeError(func_name + " func missing parameters: " + missing_str)


def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
    # Ensure outcome_timestamp - start_time is *exactly* equal to the delay to
    # avoid complexity in test code.
[assistant] `NoneReturnUntilAfterCount` doesn't exist in this file, so I'll replace it with a small local helper and rewrite the block cleanly.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\n\ndef rep(old, new):\n    global s\n    assert s.count(old) == 1, old\n    s = s.replace(old, new)\n\nrep('''class TestPickling(unittest.Tes
…[3673 chars elided]…
)\n        assert isinstance(actual, tenacity.retry_any)\n''')\np.write_text(s)\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k Pickling 2>&1 | tail -30", "description": "Fix test helper usage and run pickling tests"}
[tool_result]     def test_used_retrying_keeps_statistics_and_still_works(self) -> None:
        retry = Retrying(
            sleep=lambda _: None,
            stop=tenacity.stop_after_attempt(3),
            retry=tenacity.retry_if_exception_type(ValueError),
        )
        assert retry(_FailTimes(1)) is None
        expected_stats = dict(retry.statistics)
        assert expected_stats["attempt_number"] == 2
    
>       actual = self.roundtrip(retry)
                 ^^^^^^^^^^^^^^^^^^^^^

tests/test_te
…[526 chars elided]…
kle
    
>       return pickle.loads(pickle.dumps(obj))
                            ^^^^^^^^^^^^^^^^^
E       AttributeError: Can't get local object 'TestPickling.test_used_retrying_keeps_statistics_and_still_works.<locals>.<lambda>'

tests/test_tenacity.py:1953: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_keeps_statistics_and_still_works
1 failed, 4 passed, 112 deselected in 0.06s
[assistant] That failure is in my test, not the library: `sleep=lambda` is a user-supplied, unpicklable value. I'll switch it to a module-level function.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_tenacity.py\")\ns = p.read_text()\nold = '''class _FailTimes:'''\nassert s.count(old) == 1\ns = s.replace(old, '''def _no_sleep(seconds: float) -> None:\n    pass\n\n\nclass _
…[310 chars elided]…
text(s)\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k Pickling 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Use module-level sleep in test and run suites"}
[tool_result] .....                                                                    [100%]
5 passed, 112 deselected in 0.04s
........................................................................ [ 86%]
....................                                                     [100%]
151 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] All 151 pass. To confirm the new tests actually guard the fix, I'll run them against the original `HEAD` library code. I'll also run the project's linters.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; rm -rf /tmp/verify-head && mkdir /tmp/verify-head && git archive HEAD | tar -x -C /tmp/verify-head && cp tests/test_tenacity.py /tmp/verify-head/tests/ && cd /tmp/verify-head && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k Pickling 2>&1 | tail -8; cd ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1 && grep -n \"ruff\\|mypy\" pyproject.toml | head; for t in ruff mypy; do $PY -m $t --version 2>/dev/null || echo \"no $t\"; done", "description": "Confirm new tests fail on HEAD and check lint tools"}
[tool_result] tests/test_tenacity.py:1957: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_composed_retry_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_decorated_function_retry_object_is_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_keeps_statistics_and_still_works
5 failed, 112 deselected in 0.12s
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
no ruff
no mypy
[assistant] All five new tests fail on `HEAD` and pass with the fix. The project's ruff and mypy aren't in the test venv, so I'll check for them elsewhere.
[tool_use Bash] {"command": "(which ruff mypy || echo none-on-path); PY=<work>/env-tenacity/bin/python; $PY -m pip install -q ruff mypy 2>&1 | tail -2; $PY -m ruff check . && $PY -m ruff format --check . ; $PY -m mypy tenacity 2>&1 | tail -5", "description": "Install ruff and mypy into test env and run them"}
[tool_result] ruff not found
mypy not found
none-on-path
<work>/env-tenacity/bin/python: No module named pip
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
[assistant] The check venv has no pip, and I don't want to modify it. I'll put the linters in a separate scratch venv instead.
[tool_use Bash] {"command": "python3 -m venv /tmp/lint-venv && /tmp/lint-venv/bin/pip install -q ruff mypy 2>&1 | tail -2; /tmp/lint-venv/bin/ruff check tenacity tests && /tmp/lint-venv/bin/ruff format --check tenacity tests; /tmp/lint-venv/bin/mypy tenacity 2>&1 | tail -8", "description": "Run ruff and mypy from a scratch venv"}
[tool_result] [notice] A new release of pip is available: 25.0.1 -> 26.2.2
[notice] To update, run: python3.12 -m pip install --upgrade pip
RUF036 `None` not at the end of the type union.
   --> tenacity/__init__.py:281:23
    |
279 |         before: t.Callable[["RetryCallState"], None] | object = _unset,
280 |         after: t.Callable[["RetryCallState"], None] | object = _unset,
281 |         before_sleep: t.Callable[["RetryCallState"], None] | None | object = _unset,
    |                       ^^^^^^^^^^^
…[12858 chars elided]…
ound]
tenacity/asyncio/__init__.py:62: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
tenacity/asyncio/__init__.py:63: error: Cannot find implementation or library stub for module named "trio"  [import-not-found]
tenacity/asyncio/__init__.py:66: error: Returning Any from function declared to return "Awaitable[None]"  [no-any-return]
tenacity/__init__.py:89: error: Unused "type: ignore" comment  [unused-ignore]
Found 6 errors in 3 files (checked 12 source files)
[assistant] Those ruff RUF036 and mypy errors are on lines I didn't touch, and they look like newer-tool-version noise. To be sure I added nothing, I'll compare against the `HEAD` copy and check formatting on the changed files.
[tool_use Bash] {"command": "L=/tmp/lint-venv/bin; echo \"HEAD ruff: $(cd /tmp/verify-head && $L/ruff check tenacity tests 2>&1 | tail -1)\"; echo \"HEAD mypy: $(cd /tmp/verify-head && $L/mypy tenacity 2>&1 | tail -1)\"; echo \"NOW  ruff: $($L/ruff check tenacity tests 2>&1 | tail -1)\"; echo \"NOW  mypy: $($L/mypy tenacity 2>&1 | tail -1)\"; $L/ruff check --select F,E,I,UP tenacity tests 2>&1 | tail -2; $L/ruff format --check tenacity tests", "description": "Compare lint results against HEAD and check formatting"}
[tool_result ERROR] Exit code 1
HEAD ruff: 15 unsafe fixes available with `--fix --unsafe-fixes`.
HEAD mypy: Found 6 errors in 3 files (checked 12 source files)
NOW  ruff: 15 unsafe fixes available with `--fix --unsafe-fixes`.
NOW  mypy: Found 6 errors in 3 files (checked 12 source files)

Found 23 errors.
unformatted: File would be reformatted
   --> tenacity/retry.py:253:1
    |
252 |         if message:
    -
253 |             predicate = functools.partial(_message_equals, message)
    |

1 file would be reformatted, 18 files already formatted
[assistant] Lint and mypy counts match `HEAD` exactly. The one real issue is a formatting nit in `retry.py`, which I'll fix. I'll also check that the wider-rule run has no new findings.
[tool_use Bash] {"command": "L=/tmp/lint-venv/bin; $L/ruff format tenacity/retry.py && $L/ruff format --check tenacity tests && echo \"HEAD extended: $(cd /tmp/verify-head && $L/ruff check --select F,E,I,UP tenacity tests 2>&1 | grep -c '^[A-Z]*[0-9]* ')\"; echo \"NOW extended: $($L/ruff check --select F,E,I,UP tenacity tests 2>&1 | grep -c '^[A-Z]*[0-9]* ')\"; git diff --stat; sed -n 240,262p tenacity/retry.py", "description": "Fix formatting and compare extended lint counts"}
[tool_result] 1 file reformatted
19 files already formatted
HEAD extended: 212
NOW extended: 212
 tenacity/__init__.py   | 14 ++++++++
 tenacity/retry.py      | 49 +++++++++++++++++++--------
 tests/test_tenacity.py | 92 ++++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 141 insertions(+), 14 deletions(-)

    def __init__(
        self,
        message: str | None = None,
        match: None | str | re.Pattern[str] = None,
    ) -> None:
        if message and match:
            raise TypeE
…[136 chars elided]…
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
[This command modified 1 file you've previously read: tenacity/retry.py. Call Read before editing.]
[assistant] Formatting is clean and the extended lint count is unchanged from `HEAD`. Next I'll add a reno release note, matching the repo's convention, and do an end-to-end `Pool.map` check with a `Retrying` object passed to the workers.
[tool_use Bash] {"command": "cat > releasenotes/notes/picklable-retrying-3f1c9a7e2b5d8048.yaml <<'EOF'\n---\nfixes:\n  - |\n    `Retrying` objects, including ones that have already been used, and the\n    built-in retry strategies can now be pickled, so `@retry`-decorated\n    functions and their retry objects work with `multiprocessing`.\nEOF\nPY=<tmp>/-Users-user-Coding-delvera-foundational
…[718 chars elided]…
n        print(\"retrying passed to pool:\", p.map(work, [(r, 1), (r, 2)]))\n    print(\"decorated:\", tenacity.retry(stop=tenacity.stop_after_attempt(2))(lambda_free).__name__)\nEOF\n$PY -I /tmp/pickle-repro/pool_check.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Add release note, run Pool end-to-end check and full suite"}
[tool_result]   File "~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/multiprocessing/pool.py", line 774, in get
    raise self._value
multiprocessing.pool.MaybeEncodingError: Error sending result: '<multiprocessing.pool.ExceptionWithTraceback object at 0x10197a0f0>'. Reason: 'TypeError("cannot pickle '_thread.RLock' object")'
....................                                                     [100%]
151 passed, 1 skipped, 12 subtests passed in 1.83s
 M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/picklable-retrying-3f1c9a7e2b5d8048.yaml
[assistant] The `Pool` check failed, but for a reason in my script rather than the fix: `lambda_free(1)` always raises, so the retries exhaust and `RetryError` is raised in the worker. That exception carries a `concurrent.futures.Future`, which holds a lock and can't be sent back. I'll make the failure transient so the success path gets exercised, and note the `RetryError` issue separately.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/pickle-repro/pool_check2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b58808c83cd1/20261023-163641-bug-retrying-objects-and-the-bui/base-1\")\nfrom multiprocessing import Pool\n
…[476 chars elided]…
t(3), retry=tenacity.retry_if_exception_type(ValueError), wait=tenacity.wait_none())\n    with Pool(2) as p:\n        print(\"Pool.map decorated:\", p.map(flaky, [2, 4]))\n        print(\"Pool.map retrying object arg:\", p.map(work, [(r, 2), (r, 4)]))\nEOF\n$PY -I /tmp/pickle-repro/pool_check2.py 2>&1 | grep \"Pool.map\"", "description": "Run positive multiprocessing check with transient failure"}
[tool_result] Pool.map decorated: [20, 40]
Pool.map retrying object arg: [20, 40]
[assistant] Both multiprocessing paths work. A final review of the library diff:
[tool_use Bash] {"command": "git diff -- tenacity/", "description": "Review the library diff"}
[tool_result] diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 591f970..7fd49ea 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -256,6 +256,20 @@ class BaseRetrying(ABC):
         self._name = name
         self.enabled = enabled
 
+    def __getstate__(self) -> dict[str, t.Any]:
+        # threading.local cannot be pickled, so carry the statistics of the
+        # calling thread across instead and rebuild the local in __setstate__.
+        state = self.__dict__.copy()
+       
…[3616 chars elided]…
g 1 required argument 'message' or 'match'"
@@ -252,7 +273,7 @@ class retry_if_not_exception_message(retry_if_exception_message):
         super().__init__(message, match)
         # invert predicate
         if_predicate = self.predicate
-        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
+        self.predicate = functools.partial(_negate, if_predicate)
 
     def __call__(self, retry_state: "RetryCallState") -> bool:
         if retry_state.outcome is None:
[assistant] `Retrying` objects (fresh or already used) and the built-in retry strategies now pickle and unpickle into working equivalents. The full suite passes: 151 passed, 1 skipped, with the 5 new tests failing on the original code.

**Root causes**
- `BaseRetrying` stores its per-thread state (including `statistics`) in a `threading.local`, which can't be pickled.
- `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` and `retry_if_not_exception_message` stored lambdas or closures as their predicate.
- Decorated functions themselves alre
…[1510 chars elided]…
eat it as informational after a round trip.
- Pickling still fails for user-supplied values that aren't picklable, such as a lambda `sleep` or `before` callback. That's expected, but worth knowing.
- Out of scope, and worth a follow-up: `RetryError` carries a `concurrent.futures.Future` that holds a lock. If every attempt fails inside a `Pool` worker, the error can't be sent back to the parent and `multiprocessing` raises `MaybeEncodingError`. The fix would be to make `RetryError` picklable as well. I didn't change that because it alters exception semantics, so tell me if you want it included.
