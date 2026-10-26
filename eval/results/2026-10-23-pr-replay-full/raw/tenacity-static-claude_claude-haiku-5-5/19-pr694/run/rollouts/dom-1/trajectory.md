# trajectory dom-1

final message:
All three regressions are fixed. The new tests fail on the unfixed code for the reported reasons and pass after the fix. The full suite passes and the stdlib checker reports 0 problems. Nothing is committed.

**What changed**

- **`wait=None`, `wait=0`, `wait=sum([])`** (`tenacity/__init__.py`, `tenacity/asyncio/__init__.py`): `_run_wait` now calls the wait only if it is callable, and otherwise uses `0.0`. `WaitBaseT` now also includes `int` and `None`, so these values type-check for users too.
- **`my_callable + wait_fixed(1)`** (`tenacity/wait.py`): `__radd__` returns `wait_combine(other, self)` when the left operand is callable. Non-zero numbers still return `NotImplemented`.
- **Positional state in `wait_combine`** (`tenacity/wait.py`): it calls `x(retry_state)`, and its arguments are typed as callables.
- **Tests**: four in `tests/test_tenacity.py::TestWaitConditions` and one async in `tests/test_asyncio.py::TestNoWaitValues`. I also removed the `# type: ignore[arg-type]` on the `sum([...])` wait in `test_wait_arbitrary_sum`, since the widened type now accepts it.
- **Reno note**: `releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml`.

**Decisions to check**

- A non-zero int such as `wait=5` now means "no wait" silently, where it used to raise `TypeError`. The fix needed `int` in the type for `sum([])`, and I chose the callable check over keeping the TypeError. If you want `wait=5` to keep raising, that's a small follow-up in the `else` branch of both `_run_wait` methods.

**Not fixed, as the task didn't name them**

- `wait_chain` (`tenacity/wait.py:128`) still calls `wait_func(retry_state=retry_state)`, so a plain callable with a parameter name other than `retry_state` fails there too.
- `sum([my_callable, wait_fixed(1)])` still fails, because `0 + my_callable` has no `__radd__` to fall back on. The `callable + wait` form works.

**Checks**

- Each new test was run alone against the unfixed code. The `wait=None` failure was `'NoneType' object is not callable`, and `wait=0`/`sum([])` failed with `'int' object is not callable`. The `+` test failed with `unsupported operand type(s) for +`, and the positional test with `unexpected keyword argument 'retry_state'`.
- Full suite via `run_tests.py`: exit 0, 177 passed, 1 skipped. I did not identify the skipped test.
- `check_changed.py`: PASS, 0 problems.
- **Not run**: ruff and mypy, which the environment doesn't have. The mypy-dependent parts are the widened `WaitBaseT`, the `callable` narrowing, and removing the `type: ignore` in `test_wait_arbitrary_sum`. Those are unverified.
- `run_tests.py` isn't executable here, so I ran it with the project Python. No other harness steps were skipped.

## events
[assistant] I'll start by reading the relevant code and the change-contract skill the project asks for.
[tool_use Bash] {"command": "pwd && git status --short | head && ls .lithify/harness/scripts/ && grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n 'wait' tenacity/wait.py | head -80", "description": "Check repo state, harness scripts, and wait module"}
[tool_use Bash] {"command": "cat tenacity/wait.py; echo ---; grep -n 'wait' tenacity/__init__.py | head -60", "description": "Read wait strategies module and __init__ wait handling"}
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
…[11744 chars elided]…
waitable[None] | None] = after_nothing,
748:    before_sleep: t.Callable[["RetryCallState"], t.Awaitable[None] | None]
752:    retry_error_callback: t.Callable[["RetryCallState"], t.Any | t.Awaitable[t.Any]]
846:    "wait_chain",
847:    "wait_combine",
848:    "wait_exception",
849:    "wait_exponential",
850:    "wait_exponential_jitter",
851:    "wait_fixed",
852:    "wait_full_jitter",
853:    "wait_incrementing",
854:    "wait_none",
855:    "wait_random",
856:    "wait_random_exponential",
[tool_result] ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1
check_changed.py
list_overrides.py
run_tests.py
10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composi
…[3243 chars elided]…
 wait with exponentially widening window.
251:        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
254:    When waiting for an unavailable resource to become available again, as
256:    wait_exponential strategy (which uses a fixed interval) may be preferable.
266:class wait_exponential_jitter(wait_base):
269:    It allows for a customized multiplier, maximum wait, jitter and minimum.
274:    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))
[assistant] The docs tools that just appeared aren't relevant to this task. Next I'll read the contract sections that cover wait composition and `wait=` values, plus the current `Retrying` wait handling.
[tool_use Bash] {"command": "sed -n '262,306p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n '1,20p;412,440p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n '240,300p;410,420p' tenacity/__init__.py; echo ----; grep -n 'wait' tenacity/asyncio/__init__.py | head -30", "description": "Read contract sections and wait handling in Retrying"}
[tool_result] ## 1b5. Wait composition (`+`, `sum()`, `wait_combine`, `wait_chain`) and the `wait=` value
Verified in `tenacity/wait.py`, `tenacity/__init__.py`, `tenacity/asyncio/__init__.py`, git log.
- `WaitBaseT = wait_base | Callable[[RetryCallState], float | int]` (`wait.py`): a plain
  function is a first-class wait strategy. INVARIANT: every site that invokes a wait strategy
  passes the retry state POSITIONALLY, as the loop does (`self.wait(retry_state)`), because a
  user callable may name its param
…[10960 chars elided]…
retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
157:        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
166:            result = await action(retry_state)
194:            do = await self.iter(retry_state=self._retry_state)
201:                await self.sleep(do)  # type: ignore[misc]
215:                return await fn(*args, **kwargs)  # type: ignore[misc]
227:            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
[tool_use Bash] {"command": "git log --oneline -n 15 -- tenacity/wait.py tenacity/__init__.py; git log -p -S'wait is None' --oneline -- tenacity/ | head -150", "description": "Read git history for wait None handling"}
[tool_result] a099996 refactor: mark overridden methods with @override (#682)
d6690dc refactor: declare BaseAction's REPR_FIELDS and NAME as ClassVar (#680)
e6ef84a refactor: drop always-true truthiness checks and enable truthy-bool (#679)
7c3c45c fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
a2af454 Fix static typing of @retry decorated instance methods (fixes #532) (#668)
6fec225 Improve inline type annotations (#664)
ac30991 chore: pin ruff to 0.16.1 (#670)
c650fb4 Fix exponenti
…[120 chars elided]…
 visible when @retry is further wrapped (fixes #519) (#653)
4ee186c wait_chain: reject empty strategy list with ValueError instead of IndexError (#646)
868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
1106b9a feat: deprecate `initial` in favor of `multiplier` in `wait_exponential_jitter` (#629)
3233040 feat: add `min` param and `timedelta` support to `wait_exponential_jitter` (#628)
[assistant] The contract points at commit `e6ef84a` as the one that removed the falsy-`wait` guard. I'll read that diff and the `__radd__` commit to see what each one removed.
[tool_use Bash] {"command": "git show e6ef84a -- tenacity/ | head -200; echo ====; git show 7c3c45c --stat; git show 7c3c45c -- tenacity/wait.py | head -80", "description": "Show commits that removed wait guard and changed __radd__"}
[tool_result ERROR] Exit code 1
commit e6ef84a1cebc01963106b1aecd598393054e0277
Author: Julien Danjou <julien@danjou.info>
Date:   Wed Aug 5 17:48:25 2026 +0200

    refactor: drop always-true truthiness checks and enable truthy-bool (#679)
    
    `truthy-bool` reports objects tested for truthiness that implement neither
    `__bool__` nor `__len__`, and so can only ever be true. Three sites:
    
    `BaseRetrying._run_wait` and `AsyncRetrying._run_wait` both guarded the
    wait call with `if self.wait:`. `wait
…[2740 chars elided]…
lf.wait:
-            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)
-        else:
-            sleep = 0.0
-
-        retry_state.upcoming_sleep = sleep
+        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
+            retry_state
+        )
 
     async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
         self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
(eval):1: === not found
[assistant] The `e6ef84a` commit removed `if self.wait:` from both `_run_wait` methods, and `7c3c45c` made `__radd__` reject non-zero numbers but not callables. Next I'll check the existing wait tests, every place `WaitBaseT` and `retry_state=` are used, and the `tornadoweb` wait path.
[tool_use Bash] {"command": "grep -n 'def test_wait_combine\\|def test_wait_arbitrary_sum\\|def test_wait_chain\\|class TestWaitConditions\\|def test_wait_none\\|wait=None\\|sum(\\[' tests/test_tenacity.py | head -30; echo ---; grep -n 'wait' tests/test_asyncio.py | head -30; echo ---; grep -rn 'WaitBaseT\\|retry_state=retry_state\\|_run_wait' tenacity/ | grep -v '^tenacity/wait.py:.*def __call__'; echo ---; grep -n 'wait' tenacity/tornadoweb.py | head; echo ---; ls releasenotes/notes | tail -5", "description": "Locate wait tests and call sites"}
[tool_result] 285:class TestWaitConditions(unittest.TestCase):
442:    def test_wait_combine(self) -> None:
492:    def test_wait_arbitrary_sum(self) -> None:
523:    def test_wait_chain(self) -> None:
541:    def test_wait_chain_multiple_invocations(self) -> None:
558:    def test_wait_chain_requires_at_least_one_strategy(self) -> None:
---
43:from tenacity.wait import wait_fixed
63:    await asyncio.sleep(0.00001)
69:    await asyncio.sleep(0.00001)
75:    await asyncio.sleep(0.00001)
83:        await _retr
…[2567 chars elided]…
init__.py:535:            do = self.iter(retry_state=retry_state)
tenacity/__init__.py:727:    wait: "WaitBaseT" = ...,
tenacity/__init__.py:744:    wait: "WaitBaseT" = wait_none(),
tenacity/tornadoweb.py:52:            do = self.iter(retry_state=retry_state)
---
---
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n '1,40p' tests/test_tenacity.py | grep -n 'import' ; sed -n '442,540p' tests/test_tenacity.py; echo ---; sed -n '590,620p' tests/test_asyncio.py; echo ---; sed -n '1,60p' tests/test_asyncio.py | grep -n 'import\\|^from'; echo ---; cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml", "description": "Read existing wait tests and reno note"}
[tool_result] 16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
24:from fractions import Fraction
25:from unittest import mock
27:import pytest
29:import tenacity
30:from tenacity import RetryCallState, RetryError, Retrying, retry
31:from tenacity._utils import override
32:from tenacity.retry import retry_all, retry_any
    def test_wait_combine(self) -> None:
        r = Retrying(
            wait=tenacity.wait_combine(

…[4368 chars elided]…
2:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
---
---
fixes:
  - |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
[assistant] Before writing tests I need the async test helpers and the `make_retry_state` signature, plus the mypy and ruff settings, since the test-only `# type: ignore` comments would interact with the widened type.
[tool_use Bash] {"command": "sed -n '30,60p' tests/test_asyncio.py; echo ---; grep -n 'def make_retry_state' -A12 tests/test_tenacity.py; echo ---; grep -n 'def asynctest' -A3 tests/test_asyncio.py; grep -n 'class Test' tests/test_asyncio.py; echo ---; grep -n 'mypy' -A12 pyproject.toml | head -40; echo ---; tail -5 tests/test_tenacity.py", "description": "Read async test imports, helpers, and mypy config"}
[tool_result] import pytest

import tenacity
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)

_F = TypeVar("_F", bound=Callable[..., Coroutine[Any, Any, Any]])


def asynctest(callable_: _F) -> Callable[..., Any]:
 
…[1550 chars elided]…
 check --fix ." },
75-    { cmd = "ruff format ." },
76-]
77-
78-[tool.poe.tasks.lint]
79-sequence = [
80-    { cmd = "ruff check ." },
81-    { cmd = "ruff format --check ." },
--
87:    { ref = "mypy" },
88-    { ref = "check" },
89-]
90-
91-[tool.pytest.ini_options]
92-filterwarnings = [
93-    "once::DeprecationWarning",
94-]
95-
96-[tool.ruff]
97-line-length = 88
98-indent-width = 4
99-target-version = "py310"
--
---
        assert calls == 3


if __name__ == "__main__":
    unittest.main()
[assistant] I have what I need. Following the harness order, I'll write the regression tests first, run them against the unfixed code, and only then change the source. The tests annotate `wait=` values with `list[typing.Any]` so they don't need a `# type: ignore` that would become unused once the type is widened.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_tenacity.py", "old_string": "    def _assert_range(self, wait: float, min_: float, max_: float) -> None:", "new_string": "    def test_wait_none_values_mean_no_wait(self) -> None:\n        # None, 0 and sum([]) (the int 0) all mean \"no wait\".
…[949 chars elided]…
:\n        # The parameter is not named `retry_state`, so the state must be\n        # passed positionally.\n        def extra(state: RetryCallState) -> float:\n            return 2\n\n        combined = tenacity.wait_combine(extra, tenacity.wait_fixed(1))\n        self.assertEqual(combined(make_retry_state(1, 0)), 3)\n\n    def _assert_range(self, wait: float, min_: float, max_: float) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_asyncio.py", "old_string": "        result = await sync_function()\n        assert result is True\n        assert mock_sleep.await_count == 2\n\n\nif __name__ == \"__main__\":", "new_string": "        result = await sync_function()\n        ass
…[450 chars elided]…
ts: list[int] = []\n\n            async def fail_once() -> None:\n                attempts.append(1)\n                if len(attempts) < 2:\n                    raise ValueError\n\n            await AsyncRetrying(\n                sleep=mock_sleep, wait=wait, stop=stop_after_attempt(2)\n            )(fail_once)\n            mock_sleep.assert_awaited_once_with(0)\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] Next, the harness wants each new test run alone against the unfixed code, through `run_tests.py`, to confirm each fails for its own reported reason.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_none_values_mean_no_wait > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red1.txt", "description": "Run wait-None regression test against unfixed code"}
[tool_result] exit=1
                    raise ValueError
    
>           Retrying(
                sleep=mock_sleep, wait=wait, stop=tenacity.stop_after_attempt(2)
            )(fail_once)

tests/test_tenacity.py:522: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/__init__.py:535: in __call__
    do = self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/__init__.py:428: in iter
    result = action(retry_state)
             ^^^^^^
…[520 chars elided]…
 retry_state.upcoming_sleep = self.wait(retry_state)
                                     ^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: 'NoneType' object is not callable

tenacity/__init__.py:418: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_none_values_mean_no_wait
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestNoWaitValues::test_wait_none_values_mean_no_wait > /tmp/red2.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red2.txt", "description": "Run async wait-None regression test against unfixed code"}
[tool_result] exit=1
>           await AsyncRetrying(
                sleep=mock_sleep, wait=wait, stop=stop_after_attempt(2)
            )(fail_once)

tests/test_asyncio.py:626: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/asyncio/__init__.py:121: in __call__
    do = await self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/asyncio/__init__.py:166: in iter
    result = await action(retry_state)
             ^^^^^^^^^^^^^
…[364 chars elided]…
g.Any, **kwargs: typing.Any) -> typing.Any:
>       return call(*args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^
E       TypeError: 'NoneType' object is not callable

tenacity/_utils.py:130: TypeError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestNoWaitValues::test_wait_none_values_mean_no_wait
============================== 1 failed in 0.03s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_callable_plus_wait_is_wait_combine > /tmp/red3.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red3.txt", "description": "Run callable-plus-wait regression test against unfixed code"}
[tool_result] exit=1
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collecte
…[541 chars elided]…
a + tenacity.wait_fixed(1)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: unsupported operand type(s) for +: 'function' and 'wait_fixed'

tests/test_tenacity.py:531: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_callable_plus_wait_is_wait_combine
============================== 1 failed in 0.03s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_combine_calls_callables_positionally > /tmp/red4.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red4.txt", "description": "Run positional wait_combine regression test against unfixed code"}
[tool_result] exit=1

    def test_wait_combine_calls_callables_positionally(self) -> None:
        # The parameter is not named `retry_state`, so the state must be
        # passed positionally.
        def extra(state: RetryCallState) -> float:
            return 2
    
        combined = tenacity.wait_combine(extra, tenacity.wait_fixed(1))
>       self.assertEqual(combined(make_retry_state(1, 0)), 3)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_tenacity.py:542: 
_ _ _ _ _ _ _ _ _ _
…[456 chars elided]…
^^^^^^^^^^^
E   TypeError: TestWaitConditions.test_wait_combine_calls_callables_positionally.<locals>.extra() got an unexpected keyword argument 'retry_state'

tenacity/wait.py:94: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_combine_calls_callables_positionally
============================== 1 failed in 0.03s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All four new tests fail for their own reported reasons: `'NoneType' object is not callable`, `unsupported operand type(s) for +: 'function' and 'wait_fixed'`, and `unexpected keyword argument 'retry_state'`. The `wait=None` loop stops at its first value, though, so I haven't yet seen `0` and `sum([])` fail. I'll check those two directly against the unfixed code before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport sys; sys.path.insert(0, '.')\nfrom unittest import mock\nimport tenacity\nfor w in (0, sum([])):\n    n = []\n    def f():\n        n.append(1)\n        if len(n) < 2: raise ValueError\n    try:\n        tenaci
…[19 chars elided]…
ock.Mock(), wait=w, stop=tenacity.stop_after_attempt(2))(f)\n        print(repr(w), 'OK')\n    except Exception as e:\n        print(repr(w), type(e).__name__, e)\n\" > /tmp/red_zero.txt 2>&1; echo \"exit=$?\"; cat /tmp/red_zero.txt; grep -n 'warn_unused\\|strict' pyproject.toml; grep -n 'type: ignore' tests/*.py | grep -i wait", "description": "Check wait=0 and wait=sum([]) fail on unfixed code"}
[tool_result] exit=0
0 TypeError 'int' object is not callable
0 TypeError 'int' object is not callable
106:    "B905",  # zip() without strict= (not needed in existing code)
116:strict = true
124:# `strict` is not "everything" -- these are checks it leaves off.
tests/test_tenacity.py:431:        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]
tests/test_tenacity.py:494:            wait=sum(  # type: ignore[arg-type]
[assistant] Both `0` and `sum([])` fail with `'int' object is not callable`, so every value in the regression set is confirmed red. Now the fix, starting with `wait.py`: widen the alias to the falsy values, accept callables in `__radd__` and `wait_combine`, and pass the state positionally.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py", "old_string": "    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, so tolerate that to\n        # make summing waits work. Any other left operand is a `wait_base`,\n        # who
…[488 chars elided]…
y other non-callable\n        # left operand is a number, which is not a wait.\n        if callable(other):\n            return wait_combine(other, self)\n        if other != 0:\n            return NotImplemented\n        return self\n\n\n# None and the int 0 (including `sum([])`) mean \"no wait\".\nWaitBaseT = (\n    wait_base | typing.Callable[[\"RetryCallState\"], float | int] | int | None\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py", "old_string": "    def __init__(self, *strategies: wait_base) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state=retry_state) for x in self.wait_funcs)", "new_string": "    def __init__(\n        self, *strategies: typing.Callable[[\"RetryCallState\"], float | int]\n    ) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state) for x in self.wait_funcs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py has been updated successfully.
[assistant] The `WaitBaseT` line fits in 88 columns on one line, so I'll collapse it to match ruff's formatting. Then the `__init__.py` and `asyncio` `_run_wait` methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py", "old_string": "WaitBaseT = (\n    wait_base | typing.Callable[[\"RetryCallState\"], float | int] | int | None\n)", "new_string": "WaitBaseT = wait_base | typing.Callable[[\"RetryCallState\"], float | int] | int | None"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/__init__.py", "old_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        retry_state.upcoming_sleep = self.wait(retry_state)", "new_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        if callable(self.wait):\n            sleep = self.wait(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/asyncio/__init__.py", "old_string": "        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(\n            retry_state\n        )", "new_string": "        if callable(self.wait):\n            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Widening `WaitBaseT` to include `int` should make the `# type: ignore[arg-type]` on the `sum([...])` wait in `test_wait_arbitrary_sum` unused, which `strict` mypy flags. I'll remove that one comment, since the type it suppressed now accepts that value. Then I'll add the reno note the contract requires.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_tenacity.py", "old_string": "            wait=sum(  # type: ignore[arg-type]", "new_string": "            wait=sum("}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; echo ---; openssl rand -hex 8", "description": "Read an existing reno note format and generate a note suffix"}
[tool_result] ---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
---
a15c2a97f24bc2f0
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml", "content": "fixes:\n  - |\n    ``wait=None``, ``wait=0`` and ``wait=sum([])`` mean \"no wait\" again. They\n    raised ``TypeError: 'NoneType' object is not callable`` once a retry ran,\n    for both ``Retrying`` and ``AsyncRetrying``.\n  - |\n    A plain callable can be added to a wait strategy again:\n    ``my_callable + wait_fixed(1)`` returns a ``wait_combine`` that sums both.\n  - |\n    ``wait_combine`` passes the retry state to its strategies positionally, so\n    plain callables may name their parameter anything.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml (file state is current in your context — no need to Read it back)
[assistant] The fix is in. Now I'll re-run the same four targeted tests plus the async one, each alone, to confirm they go green.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_none_values_mean_no_wait > /tmp/green1.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green1.txt", "description": "Re-run sync wait-None test after fix"}
[tool_result] exit=0
============================== 1 passed in 0.03s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestNoWaitValues::test_wait_none_values_mean_no_wait > /tmp/green2.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green2.txt", "description": "Re-run async wait-None test after fix"}
[tool_result] exit=0
============================== 1 passed in 0.01s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_callable_plus_wait_is_wait_combine > /tmp/green3.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green3.txt", "description": "Re-run callable-plus-wait test after fix"}
[tool_result] exit=0
============================== 1 passed in 0.01s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_combine_calls_callables_positionally > /tmp/green4.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green4.txt", "description": "Re-run positional wait_combine test after fix"}
[tool_result] exit=0
============================== 1 passed in 0.01s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All four are green. Next is the full suite through the harness script, then the stdlib checker.
[tool_use Bash] {"command": ".lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/full.txt", "description": "Run full test suite via harness script"}
[tool_result] exit=126
(eval):1: permission denied: .lithify/harness/scripts/run_tests.py
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/check.txt", "description": "Run stdlib lint substitute on changed files"}
[tool_result] exit=1
changed: releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/wait.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml:1: must start with '---'
FAIL: 1 problem(s)
HINT: this is a heuristic. If a FAIL contradicts a rule in skills/tenacity-change-contract, keep the code as the skill says and report the FAIL as a checker false positive; don't reshape the code
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Two things to fix. `run_tests.py` isn't executable, so I'll call it through the project Python as the harness instructs. The checker flags my reno note because it doesn't start with `---`, which is the format the existing `wait_exponential_jitter` note uses. I'll add the header and re-run both.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml", "old_string": "fixes:\n  - |\n    ``wait=None``", "new_string": "---\nfixes:\n  - |\n    ``wait=None``"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/dom-1/releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/full.txt", "description": "Run full test suite via harness script with project python"}
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/check.txt", "description": "Re-run stdlib lint substitute on changed files"}
[tool_result] exit=0
tests/test_tenacity.py::TestMockingSleep::test_decorated_retry_with PASSED [ 94%]
tests/test_tenacity.py::TestPickle::test_retry_strategies_picklable PASSED [ 94%]
tests/test_tenacity.py::TestPickle::test_retrying_picklable PASSED       [ 95%]
tests/test_tenacity.py::TestPickle::test_retrying_picklable_after_run PASSED [ 96%]
tests/test_tenacity.py::TestPickle::test_retrying_pickle_round_trip_works PASSED [ 96%]
tests/test_tornado.py::TestTornado::test_old_tornado PASSED              [ 97
…[34 chars elided]…
ado::test_repr PASSED                     [ 97%]
tests/test_tornado.py::TestTornado::test_retry PASSED                    [ 98%]
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 177 passed, 1 skipped, 12 subtests passed in 1.84s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_result] exit=0
changed: releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/wait.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite exits 0 with 177 passed and 1 skipped, and `check_changed.py` reports 0 problems. I'll confirm the remaining keyword call sites, the reason for the skip, and the final diff.
[tool_use Bash] {"command": "grep -n 'retry_state=retry_state' tenacity/wait.py; grep -n 'SKIP' /tmp/full.txt | head -3; git diff --stat; git status --short", "description": "Check remaining keyword call sites, skip reason, and diff stat"}
[tool_result] 128:        return wait_func(retry_state=retry_state)
268:        high = super().__call__(retry_state=retry_state)
 tenacity/__init__.py         |  7 ++++++-
 tenacity/asyncio/__init__.py |  9 ++++++---
 tenacity/wait.py             | 20 +++++++++++++-------
 tests/test_asyncio.py        | 21 +++++++++++++++++++++
 tests/test_tenacity.py       | 37 ++++++++++++++++++++++++++++++++++++-
 5 files changed, 82 insertions(+), 12 deletions(-)
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/wait.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-no-wait-values-callable-sum-a15c2a97f24bc2f0.yaml
[tool_use Bash] {"command": "grep -in 'skip' /tmp/full.txt | head -5", "description": "Find the skipped test in the full run output"}
[tool_result] 40:============== 177 passed, 1 skipped, 12 subtests passed in 1.84s ==============
[assistant] All three regressions are fixed. The new tests fail on the unfixed code for the reported reasons and pass after the fix. The full suite passes and the stdlib checker reports 0 problems. Nothing is committed.

**What changed**

- **`wait=None`, `wait=0`, `wait=sum([])`** (`tenacity/__init__.py`, `tenacity/asyncio/__init__.py`): `_run_wait` now calls the wait only if it is callable, and otherwise uses `0.0`. `WaitBaseT` now also includes `int` and `None`, so these values type-check for users too.
- **`my_callable + wait_fixed(1)`** (`tenacity/wait.py`): `__radd__` returns `wait_combine(other, se
…[1512 chars elided]…
with `unsupported operand type(s) for +`, and the positional test with `unexpected keyword argument 'retry_state'`.
- Full suite via `run_tests.py`: exit 0, 177 passed, 1 skipped. I did not identify the skipped test.
- `check_changed.py`: PASS, 0 problems.
- **Not run**: ruff and mypy, which the environment doesn't have. The mypy-dependent parts are the widened `WaitBaseT`, the `callable` narrowing, and removing the `type: ignore` in `test_wait_arbitrary_sum`. Those are unverified.
- `run_tests.py` isn't executable here, so I ran it with the project Python. No other harness steps were skipped.
