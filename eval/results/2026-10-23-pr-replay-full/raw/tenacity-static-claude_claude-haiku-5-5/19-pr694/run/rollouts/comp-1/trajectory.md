# trajectory comp-1

final message:
All three regressions are fixed. Each has a regression test that failed against the unfixed code for its reported reason, and the full suite passes: `exit=0`, 177 passed, 1 skipped. The changes are uncommitted in this worktree.

**What changed**

1. **`wait=None`, `wait=0`, `wait=sum([])`** (`tenacity/__init__.py`, `tenacity/asyncio/__init__.py`): restored the `if self.wait:` guard in both `_run_wait` methods, which commit e6ef84a had removed on the premise that `wait` is never falsy. The `wait` annotations in `BaseRetrying.__init__`, `AsyncRetrying.__init__` and both `retry()` overloads now read `WaitBaseT | None | int`.
2. **`my_callable + wait_fixed(1)`** (`tenacity/wait.py`): `__radd__` now returns `wait_combine(other, self)` for a callable. It still returns `NotImplemented` for a non-zero number, so `5 + wait_fixed(1)` fails at the addition as before. `__add__` and `wait_combine` accept the wider `WaitBaseT` type.
3. **Positional retry state** (`tenacity/wait.py`): `wait_combine` calls each strategy as `x(retry_state)`.

**Tests added** (new methods only, no existing lines edited): `TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry`, `test_plain_callable_plus_wait_builds_combine`, `test_wait_combine_passes_retry_state_positionally` in `tests/test_tenacity.py`, and `TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry` in `tests/test_asyncio.py`. Each failed red, then passed green.

**Release notes:** two reno files in `releasenotes/notes/`, one for the `None`/`0` fix and one for the `+` and positional fixes.

**Checks**
- `check_changed.py`: `PASS: 0 problem(s)`.
- **Not run:** ruff and mypy. The harness says they cannot run here.

**Decisions and risks**
- **mypy is unverified.** After the widening, `self.wait(retry_state)` sits behind a truthiness guard that does not narrow out `int`, so mypy may report "int not callable" in `_run_wait`. I kept the guard rather than add `# type: ignore`, because the repo's contract asks for widening, not ignores. Someone should run mypy before merging.
- **Nonzero ints still raise.** `wait=5` still raises `TypeError` at call time, as before. I did not switch to a `callable()` guard, because that would silently turn `wait=5` into no wait.
- **`wait_chain` has the same keyword bug** at `tenacity/wait.py:125` (`wait_func(retry_state=retry_state)`). I left it alone because you scoped the fix to `wait_combine`; it is a one-line change if you want it. `wait_random_exponential`'s `super().__call__(retry_state=...)` is a method call and is harmless.
- **Possibly unused ignore:** the widening may make the existing `# type: ignore[arg-type]` on `wait=sum(` in `test_wait_arbitrary_sum` unused. I did not touch it, per the guardrails.
- **Skip:** the one skipped test is unidentified; I did not check which test it is.

## events
[assistant] I'll start by reading the wait strategy code and the existing tests, then write the regression tests before changing anything.
[tool_use Bash] {"command": "pwd && git status --short && ls .lithify/harness/scripts/ && ls tenacity/ tests/ && grep -n \"wait\" tenacity/wait.py | head -150", "description": "Show repo state, harness scripts, and wait module"}
[tool_result] ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1
check_changed.py
list_overrides.py
run_tests.py
tenacity/:
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

tests/:
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
30:class wait_base(abc.ABC):
31:    """Abstract base class for wait strategies."""
3
…[2386 chars elided]…
 wait with exponentially widening window.
251:        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
254:    When waiting for an unavailable resource to become available again, as
256:    wait_exponential strategy (which uses a fixed interval) may be preferable.
266:class wait_exponential_jitter(wait_base):
269:    It allows for a customized multiplier, maximum wait, jitter and minimum.
274:    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))
[tool_use Bash] {"command": "ls <work>/env-tenacity/bin/python 2>&1; cat .lithify/harness/memory.md 2>/dev/null | head -30; ls .lithify/harness/", "description": "Check project python and harness memory"}
[tool_result] <work>/env-tenacity/bin/python
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The Docs tools that just appeared aren't needed for this task. Next I'll read the wait module, the retry wait handling, and the existing wait tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/wait.py", "limit": 125}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITH
…[3286 chars elided]…
 -> None:
114	        if not strategies:
115	            raise ValueError("wait_chain() requires at least one strategy")
116	        self.strategies = strategies
117	
118	    @override
119	    def __call__(self, retry_state: "RetryCallState") -> float:
120	        wait_func_no = min(max(retry_state.attempt_number, 1), len(self.strategies))
121	        wait_func = self.strategies[wait_func_no - 1]
122	        return wait_func(retry_state=retry_state)
123	
124	
125	class wait_exception(wait_base):
[tool_use Bash] {"command": "grep -n \"wait\" tenacity/retry.py tenacity/asyncio/__init__.py tenacity/__init__.py | head -80; grep -n \"def test.*\\(combine\\|sum\\|none\\|zero\\|callable\\|wait_add\\|plus\\)\" tests/*.py | head -40", "description": "Find wait handling in retry code and related tests"}
[tool_result] tenacity/asyncio/__init__.py:49:    from tenacity.wait import WaitBaseT
tenacity/asyncio/__init__.py:52:WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Awaitable[t.Any]])
tenacity/asyncio/__init__.py:57:def _portable_async_sleep(seconds: float) -> t.Awaitable[None]:
tenacity/asyncio/__init__.py:79:            [int | float], t.Awaitable[None] | None
tenacity/asyncio/__init__.py:82:        wait: "WaitBaseT" = tenacity.wait.wait_none(),
tenacity/asyncio/__init__.py:85:            ["Retry
…[4691 chars elided]…
   "wait_random",
tenacity/__init__.py:856:    "wait_random_exponential",
tests/test_after.py:50:    def test_02_none_seconds_since_start(self) -> None:
tests/test_utils.py:6:def test_is_coroutine_callable() -> None:
tests/test_tenacity.py:442:    def test_wait_combine(self) -> None:
tests/test_tenacity.py:472:    def test_wait_double_sum(self) -> None:
tests/test_tenacity.py:480:    def test_wait_triple_sum(self) -> None:
tests/test_tenacity.py:492:    def test_wait_arbitrary_sum(self) -> None:
[assistant] The wait strategy is called as `self.wait(retry_state)` in `Retrying`, and `wait_combine` passes `retry_state=` by keyword. Next I'll check the `Retrying` constructor and the existing combine tests.
[tool_use Bash] {"command": "sed -n 240,300p tenacity/__init__.py; echo ----; sed -n 410,420p tenacity/__init__.py; echo ----; sed -n 140,160p tenacity/asyncio/__init__.py; echo ----; sed -n 436,510p tests/test_tenacity.py", "description": "Read Retrying init, run_wait, and existing wait tests"}
[tool_result]         exc_value: BaseException | None,
        traceback: "types.TracebackType | None",
    ) -> bool | None:
        return self.__exit__(exc_type, exc_value, traceback)


class BaseRetrying(ABC):
    def __init__(
        self,
        sleep: t.Callable[[int | float], None] = sleep,
        stop: "StopBaseT" = stop_never,
        wait: "WaitBaseT" = wait_none(),
        retry: "RetryBaseT" = retry_if_exception_type(),
        before: t.Callable[["RetryCallState"], None] = before_nothing,
   
…[5504 chars elided]…
t_fixed(1),
                    tenacity.wait_random(0, 3),
                    tenacity.wait_fixed(5),
                    tenacity.wait_none(),
                ]
            )
        )
        # Test it a few time since it's random
        for _ in range(1000):
            w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

    def _assert_range(self, wait: float, min_: float, max_: float) -> None:
        self.assertLess(wait, max_)
[assistant] Before choosing where to fix the `None`/`0` case, I'll check git history for the code that handled it before, and read the tenacity-change-contract sections that apply here.
[tool_use Bash] {"command": "git log --oneline -S \"wait is None\" -- tenacity | head; git log --oneline -S \"__radd__\" -- tenacity | head -5; echo ----; grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Search git history and list contract skill sections"}
[tool_result] 9a1b4b7 Implement '+' operator for wait strategies
----
10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, st
…[172 chars elided]…
on (`+`, `sum()`, `wait_combine`, `wait_chain`) and the `wait=` value
310:## 1c. CONTRACT: a new keyword on `Retrying`/`AsyncRetrying`/`@retry`, or a new accepted type for an existing one
350:## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
379:## 2. A release note in `releasenotes/notes/` (reno)
401:## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
415:## 3. A regression test in the matching test file
429:## 4. Keep the change surface minimal
[tool_use Bash] {"command": "sed -n 262,350p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n 379,440p .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Read wait composition and release note sections of contract"}
[tool_result] ## 1b5. Wait composition (`+`, `sum()`, `wait_combine`, `wait_chain`) and the `wait=` value
Verified in `tenacity/wait.py`, `tenacity/__init__.py`, `tenacity/asyncio/__init__.py`, git log.
- `WaitBaseT = wait_base | Callable[[RetryCallState], float | int]` (`wait.py`): a plain
  function is a first-class wait strategy. INVARIANT: every site that invokes a wait strategy
  passes the retry state POSITIONALLY, as the loop does (`self.wait(retry_state)`), because a
  user callable may name its param
…[9813 chars elided]…
 a multi-line `@retry(...)` call whose last line is `)`. Separate a nested
  decorated def from the code above it with a blank line before the `@`, never after the `)`.
- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
  annotated (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
[tool_use Bash] {"command": "git show 9a1b4b7 --stat | head -20; git show 9a1b4b7 -- tenacity/__init__.py | head -60", "description": "Inspect commit that introduced wait addition"}
[tool_result] commit 9a1b4b7459f9862249ab7f47bed7b104c35e6adc
Author: Gevorg Davoian <gdavoian@mirantis.com>
Date:   Sat Oct 22 16:51:17 2016 +0300

    Implement '+' operator for wait strategies

 tenacity/tests/test_tenacity.py | 26 ++++++++++++++++++++++++++
 tenacity/wait.py                | 35 ++++++++++++++++++++++++++++-------
 2 files changed, 54 insertions(+), 7 deletions(-)
[assistant] The contract skill flags the `None`/`0` guard as removed in commit e6ef84a, and it points at the `__radd__` branch and typing. I'll read those two commits and the reno notes they added so the restored behaviour matches the original intent.
[tool_use Bash] {"command": "git show e6ef84a --stat | head -20; git show e6ef84a -- tenacity | head -120; echo ======; git show 7c3c45c --stat | head -20; git show 7c3c45c -- tenacity | head -120; echo =====; ls releasenotes/notes | tail -15", "description": "Show commits that removed wait guard and changed radd"}
[tool_result ERROR] Exit code 1
commit e6ef84a1cebc01963106b1aecd598393054e0277
Author: Julien Danjou <julien@danjou.info>
Date:   Wed Aug 5 17:48:25 2026 +0200

    refactor: drop always-true truthiness checks and enable truthy-bool (#679)
    
    `truthy-bool` reports objects tested for truthiness that implement neither
    `__bool__` nor `__len__`, and so can only ever be true. Three sites:
    
    `BaseRetrying._run_wait` and `AsyncRetrying._run_wait` both guarded the
    wait call with `if self.wait:`. `wait
…[3831 chars elided]…
.wait:
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
(eval):1: ===== not found
[assistant] The guard was removed on the premise that `wait` is never falsy, which is false: users can pass `None` or `0`. The `echo =====` line broke the command, as the harness notes warn, so I'll rerun the rest with plain separators.
[tool_use Bash] {"command": "git show 7c3c45c --stat | head -12; git show 7c3c45c -- tenacity | head -90; echo ---; ls releasenotes/notes | grep -i \"wait\" ; echo ---; grep -rn \"WaitBaseT\" tenacity tests | grep -v \"^tenacity/__init__.py:.*wait: \" ", "description": "Show radd commit, related reno notes and WaitBaseT uses"}
[tool_result] commit 7c3c45cf57a3f10f6ee1334b137d607ead4974c1
Author: Julien Danjou <julien@danjou.info>
Date:   Wed Aug 5 17:42:32 2026 +0200

    fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
    
    * ci: run on pull requests targeting any base branch
    
    `on.pull_request.branches` filters on the *base* branch, not the head. With
    it pinned to `main`, only a pull request merging directly into `main` ran
    CI -- every stacked pull request, whose base is the branch belo
…[2975 chars elided]…
-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
tenacity/wait.py:49:WaitBaseT = wait_base | typing.Callable[["RetryCallState"], float | int]
tenacity/__init__.py:108:    from .wait import WaitBaseT
tenacity/asyncio/__init__.py:49:    from tenacity.wait import WaitBaseT
tenacity/asyncio/__init__.py:82:        wait: "WaitBaseT" = tenacity.wait.wait_none(),
[assistant] The reno note for `__radd__` and the typing commit both bear on the design, so I'll read them next. I also need the test file conventions: imports, `make_retry_state`, and the async test pattern.
[tool_use Bash] {"command": "cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml; echo ---; sed -n 1,40p tests/test_tenacity.py; echo ---; grep -n \"^class \\|def make_retry_state\" tests/test_tenacity.py | head -30; echo ---; sed -n 1,30p tests/test_asyncio.py; grep -n \"^class \\|asynctest\" tests/test_asyncio.py | head -30; echo ---; grep -n \"_run_wait\\|self.wait\" tenacity/tornadoweb.py tenacity/__init__.py", "description": "Read reno note, test file conventions, and wait call sites"}
[tool_result] ---
fixes:
  - |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
---
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013 Ray Holder
#
# Licensed under 
…[3828 chars elided]…
@asynctest
590:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
---
tenacity/__init__.py:264:        self.wait = wait
tenacity/__init__.py:297:            wait=_first_set(wait, self.wait),
tenacity/__init__.py:329:            f"wait={self.wait}, "
tenacity/__init__.py:417:    def _run_wait(self, retry_state: "RetryCallState") -> None:
tenacity/__init__.py:418:        retry_state.upcoming_sleep = self.wait(retry_state)
tenacity/__init__.py:456:        self._add_action_func(self._run_wait)
[assistant] I have the conventions. Next I'll read the helper signatures and one example of each test style so the new tests match.
[tool_use Bash] {"command": "sed -n 54,70p tests/test_tenacity.py; echo ---; sed -n 285,300p tests/test_tenacity.py; echo ---; sed -n 249,280p tests/test_asyncio.py; echo ---; sed -n 54,78p tests/test_asyncio.py", "description": "Read test helpers and style examples"}
[tool_result] def make_retry_state(
    previous_attempt_number: typing.Any,
    delay_since_first_attempt: typing.Any,
    last_result: typing.Any = None,
    upcoming_sleep: typing.Any = 0,
) -> RetryCallState:
    """Construct RetryCallState for given attempt number & delay.

    Only used in testing and thus is extra careful about timestamp arithmetics.
    """
    required_parameter_unset = (
        previous_attempt_number is _unset or delay_since_first_attempt is _unset
    )
    if required_parameter_
…[1849 chars elided]…
-> Any:
        return asyncio.run(callable_(*a, **kw))

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
[assistant] I have what I need to write the tests. Before editing, I'll confirm the `tasyncio` alias and how `run_tests.py` is invoked.
[tool_use Bash] {"command": "grep -n \"tasyncio\\|^from\\|^import\" tests/test_asyncio.py | head -30; echo ---; sed -n 1,30p .lithify/harness/scripts/run_tests.py | grep -n \"usage\\|--timeout\\|argv\\|argparse\\|add_argument\" ; grep -n \"add_argument\" .lithify/harness/scripts/run_tests.py", "description": "Check async test imports and runner options"}
[tool_result] 15:import asyncio
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
106:        repr(tasyncio.AsyncRetrying())
253:        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
268:
…[849 chars elided]…
      async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
477:            retry_strategy = tasyncio.retry_if_result(lt_3) & retry_if_result(gt_0)
478:            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
---
10:    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
12:          ... run_tests.py --timeout 60 tests/test_x.py::Cls::test_name
21:          --timeout 60; if it is a test you wrote, make its retry loop bounded
[assistant] Now I'll add the three sync regression tests just before the `_assert_range` helper in `TestWaitConditions`. These are new methods, so no existing test lines change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tests/test_tenacity.py", "old_string": "    def _assert_range(self, wait: float, min_: float, max_: float) -> None:", "new_string": "    def test_no_wait_values_mean_no_sleep_on_retry(self) -> None:\n        # None, 0 and sum([]) (which is the int 0) all
…[1042 chars elided]…
not `retry_state`.\n        def attempt_seconds(current: RetryCallState) -> float:\n            return current.attempt_number\n\n        state = make_retry_state(3, 5)\n        combined = tenacity.wait_combine(attempt_seconds, tenacity.wait_fixed(1))\n        self.assertEqual(combined(state), state.attempt_number + 1)\n\n    def _assert_range(self, wait: float, min_: float, max_: float) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tests/test_asyncio.py", "old_string": "class TestAsyncEnabled(unittest.TestCase):", "new_string": "class TestAsyncNoWaitValues(unittest.TestCase):\n    @asynctest\n    async def test_no_wait_values_mean_no_sleep_on_retry(self) -> None:\n        # None, 0
…[413 chars elided]…
                    attempts += 1\n                    if attempts == 1:\n                        raise ValueError\n                    return \"ok\"\n\n                retrying = tasyncio.AsyncRetrying(sleep=record_sleep, wait=wait)\n                self.assertEqual(await retrying(fails_once), \"ok\")\n                self.assertEqual(sleeps, [0])\n\n\nclass TestAsyncEnabled(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tests/test_asyncio.py has been updated successfully.
[assistant] Next I'll run each new test alone against the unfixed code. They need to fail for the reported reasons, not for import or typo errors.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red1.txt", "description": "Run no-wait regression test against unfixed code"}
[tool_result] exit=1
                sleeps: list[float] = []
                attempts = 0
    
                def fails_once() -> str:
                    nonlocal attempts
                    attempts += 1
                    if attempts == 1:
                        raise ValueError
                    return "ok"
    
                r = Retrying(sleep=sleeps.append, wait=wait)
>               self.assertEqual(r(fails_once), "ok")
                                 ^^^^^^^^^^^^^

tests/test_tenacity.py:524
…[1043 chars elided]…
hort test summary info ============================
SUBFAILED(wait=None) tests/test_tenacity.py::TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry
SUBFAILED(wait=0) tests/test_tenacity.py::TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry
SUBFAILED(wait=0) tests/test_tenacity.py::TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry
========================= 3 failed, 1 passed in 0.10s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry > /tmp/red2.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red2.txt", "description": "Run async no-wait regression test against unfixed code"}
[tool_result] exit=1
    
                async def fails_once() -> str:
                    nonlocal attempts
                    attempts += 1
                    if attempts == 1:
                        raise ValueError
                    return "ok"
    
                retrying = tasyncio.AsyncRetrying(sleep=record_sleep, wait=wait)
>               self.assertEqual(await retrying(fails_once), "ok")
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_asyncio.py:208: 
_ _ _ _ _ _ _ _ 
…[918 chars elided]…
est summary info ============================
SUBFAILED(wait=None) tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry
SUBFAILED(wait=0) tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry
SUBFAILED(wait=0) tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry
========================= 3 failed, 1 passed in 0.04s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_builds_combine > /tmp/red3.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red3.txt", "description": "Run plain-callable addition regression test against unfixed code"}
[tool_result] exit=1
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collect
…[580 chars elided]…
y.wait_fixed(1)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: unsupported operand type(s) for +: 'function' and 'wait_fixed'

tests/test_tenacity.py:531: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_builds_combine
============================== 1 failed in 0.03s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally > /tmp/red4.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red4.txt", "description": "Run positional retry-state regression test against unfixed code"}
[tool_result] exit=1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collected 1 item

tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally FAILED [100%]

=================================== FAILURES ===================================
_____ TestWaitConditions.test_wait_combine_passes_retry_state_positionally _____

self = <tests.test_tenacity.TestWaitConditions testMethod=test_wait_combine_passes_retry_state_positionally>

    def test_wait_combine_
…[972 chars elided]…
TypeError: TestWaitConditions.test_wait_combine_passes_retry_state_positionally.<locals>.attempt_seconds() got an unexpected keyword argument 'retry_state'

tenacity/wait.py:94: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally
============================== 1 failed in 0.03s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All four new tests fail against the unfixed code, each for its reported reason. The `wait=None`/`0` failures show `'int' object is not callable` (the `None` case is also reached through the same call path), and the `+` and keyword failures match the description.

Now the fix. The retry-state-positional invariant and the `__radd__` branch follow the repo's contract notes. I'll edit `wait.py` first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/wait.py", "old_string": "    def __add__(self, other: \"wait_base\") -> \"wait_combine\":\n        return wait_combine(self, other)\n\n    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, 
…[416 chars elided]…
\":\n        # `sum()` seeds its accumulator with the int 0, which adds nothing.\n        if other == 0:\n            return self\n        # A plain callable has no `__add__`, so Python falls back to us for it.\n        # Any other non-zero left operand (a number) is not a wait strategy.\n        if not callable(other):\n            return NotImplemented\n        return wait_combine(other, self)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/wait.py", "old_string": "    def __init__(self, *strategies: wait_base) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state=retry_state) for x in self.wait_funcs)", "new_string": "    def __init__(self, *strategies: WaitBaseT) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        # Positional: a plain callable may name its parameter anything.\n        return sum(x(retry_state) for x in self.wait_funcs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/wait.py has been updated successfully.
[assistant] Next is the `Retrying` side. The edit tool needs a real `Read` of these files first, so I'll read the relevant ranges.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "offset": 715, "limit": 50}
[tool_result] 715	    ) -> "_RetryDecorated[P, t.Awaitable[R]]": ...
716	
717	
718	@t.overload
719	def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
720	
721	
722	@t.overload
723	def retry(
724	    *,
725	    sleep: t.Callable[[int | float], t.Awaitable[None]],
726	    stop: "StopBaseT" = ...,
727	    wait: "WaitBaseT" = ...,
728	    retry: "RetryBaseT | tasyncio.retry.RetryBaseT" = ...,
729	    before: t.Callable[["RetryCallState"], t.Awaitable[None] | None] = ...,
730	    after: t.Callable[["R
…[1074 chars elided]…
"RetryCallState"], t.Any | t.Awaitable[t.Any]]
753	    | None = None,
754	    enabled: bool = True,
755	) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...
756	
757	
758	def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
759	    """Wrap a function with a new `Retrying` object.
760	
761	    :param dargs: positional arguments passed to Retrying object
762	    :param dkw: keyword arguments passed to the Retrying object
763	    """
764	    # support both @retry and @retry() as valid syntax
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py", "offset": 76, "limit": 12}
[tool_result] 76	    def __init__(
77	        self,
78	        sleep: t.Callable[
79	            [int | float], t.Awaitable[None] | None
80	        ] = _portable_async_sleep,
81	        stop: "StopBaseT" = tenacity.stop.stop_never,
82	        wait: "WaitBaseT" = tenacity.wait.wait_none(),
83	        retry: "SyncRetryBaseT | RetryBaseT" = tenacity.retry_if_exception_type(),
84	        before: t.Callable[
85	            ["RetryCallState"], t.Awaitable[None] | None
86	        ] = before_nothing,
87	        after: t.Callable[["RetryCallState"], t.Awaitable[None] | None] = after_nothing,
[assistant] I'll also read the `BaseRetrying` constructor and `_run_wait` ranges with the Read tool so the edits can go through.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "offset": 248, "limit": 6}
[tool_result] 248	        self,
249	        sleep: t.Callable[[int | float], None] = sleep,
250	        stop: "StopBaseT" = stop_never,
251	        wait: "WaitBaseT" = wait_none(),
252	        retry: "RetryBaseT" = retry_if_exception_type(),
253	        before: t.Callable[["RetryCallState"], None] = before_nothing,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "offset": 415, "limit": 5}
[tool_result] 415	        self.iter_state.retry_run_result = self.retry(retry_state)
416	
417	    def _run_wait(self, retry_state: "RetryCallState") -> None:
418	        retry_state.upcoming_sleep = self.wait(retry_state)
419	
[assistant] Here is my decision on the `None`/`0` design. The contract notes say to restore the original `if self.wait:` guard in both `_run_wait` methods and widen the annotations, not add `# type: ignore`. I'll follow that. I'll widen `wait` to `WaitBaseT | None | int` at the four annotation sites, restore the guard, and say plainly in the final message that mypy did not run.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "old_string": "        stop: \"StopBaseT\" = stop_never,\n        wait: \"WaitBaseT\" = wait_none(),\n        retry: \"RetryBaseT\" = retry_if_exception_type(),", "new_string": "        stop: \"StopBaseT\" = stop_never,\n        wait: \"WaitBaseT | None | int\" = wait_none(),\n        retry: \"RetryBaseT\" = retry_if_exception_type(),"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "old_string": "    stop: \"StopBaseT\" = ...,\n    wait: \"WaitBaseT\" = ...,", "new_string": "    stop: \"StopBaseT\" = ...,\n    wait: \"WaitBaseT | None | int\" = ...,"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "old_string": "    wait: \"WaitBaseT\" = wait_none(),\n    retry: \"RetryBaseT | tasyncio.retry.RetryBaseT\" = retry_if_exception_type(),", "new_string": "    wait: \"WaitBaseT | None | int\" = wait_none(),\n    retry: \"RetryBaseT | tasyncio.retry.RetryBaseT\" = retry_if_exception_type(),"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py", "old_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        retry_state.upcoming_sleep = self.wait(retry_state)", "new_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        if self.wait:\n            sleep = self.wait(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py", "old_string": "        wait: \"WaitBaseT\" = tenacity.wait.wait_none(),", "new_string": "        wait: \"WaitBaseT | None | int\" = tenacity.wait.wait_none(),"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py", "offset": 148, "limit": 6}
[tool_result] 148	    @override
149	    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
150	        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
151	            retry_state
152	        )
153	
[assistant] The async `_run_wait` needs the same guard restored. I'll make that edit now, keeping its existing `# type: ignore[override]` line unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py", "old_string": "        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(\n            retry_state\n        )\n\n    @override\n    async def _run_stop(", "new_string": "        if self.wait:\n            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep\n\n    @override\n    async def _run_stop("}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] With the fix in place, I'll run the four regression tests green in one invocation.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_no_wait_values_mean_no_sleep_on_retry tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_builds_combine tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/green.txt", "description": "Run the four regression tests against the fix"}
[tool_result] exit=0
tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_builds_combine PASSED [ 50%]
tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally PASSED [ 75%]
tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry 
tests/test_asyncio.py::TestAsyncNoWaitValues::test_no_wait_values_mean_no_sleep_on_retry PASSED [100%]

===================== 4 passed, 6 subtests passed in 0.02s =====================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All four pass. The contract also requires a reno release note for behaviour changes, so I'll add those next, then run the full suite and the stdlib checker.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/releasenotes/notes/fix-wait-none-zero-3e7a9d1c5b20f684.yaml", "content": "---\nfixes:\n  - |\n    ``Retrying(wait=None)``, ``wait=0`` and ``wait=sum([])`` mean \"no wait\"\n    again. Retrying after a failure raised ``TypeError: 'NoneType' object is\n    not callable`` (or ``'int' object is not callable``) instead of retrying\n    without a delay. This applies to both ``Retrying`` and ``AsyncRetrying``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/releasenotes/notes/fix-wait-none-zero-3e7a9d1c5b20f684.yaml (file state is current in your context — no need to Read it back)
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/releasenotes/notes/fix-wait-plain-callable-8c4f2e6a1d9b0537.yaml", "content": "---\nfixes:\n  - |\n    A plain callable can again be added to a wait strategy with ``+``:\n    ``my_callable + wait_fixed(1)`` builds a ``wait_combine`` that sums both.\n    ``wait_combine`` now passes the retry state to each strategy positionally,\n    so plain callables may name their parameter anything.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/comp-1/releasenotes/notes/fix-wait-plain-callable-8c4f2e6a1d9b0537.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/full.txt", "description": "Run the full test suite via the harness runner"}
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/check.txt", "description": "Run stdlib style and annotation checker on changed files"}
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

============== 177 passed, 1 skipped, 18 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_result] exit=0
changed: releasenotes/notes/fix-wait-none-zero-3e7a9d1c5b20f684.yaml, releasenotes/notes/fix-wait-plain-callable-8c4f2e6a1d9b0537.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/wait.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (177 passed, 1 skipped) and `check_changed.py` reports 0 problems. I'll do a final review: the remaining keyword call sites from the contract, the diff, and the reason for the one skip.
[tool_use Bash] {"command": "grep -n \"(retry_state=retry_state)\" tenacity/wait.py; grep -n \"skip\" /tmp/full.txt | head -3; git diff --stat; git diff -- tenacity/", "description": "Review keyword call sites, skip reason, and diff of source"}
[tool_result] 125:        return wait_func(retry_state=retry_state)
265:        high = super().__call__(retry_state=retry_state)
40:============== 177 passed, 1 skipped, 18 subtests passed in 1.81s ==============
 tenacity/__init__.py         | 13 +++++++++----
 tenacity/asyncio/__init__.py | 11 +++++++----
 tenacity/wait.py             | 21 ++++++++++++---------
 tests/test_asyncio.py        | 24 ++++++++++++++++++++++++
 tests/test_tenacity.py       | 35 +++++++++++++++++++++++++++++++++++
 5 files changed,
…[4688 chars elided]…
 waiting strategies."""
 
-    def __init__(self, *strategies: wait_base) -> None:
+    def __init__(self, *strategies: WaitBaseT) -> None:
         self.wait_funcs = strategies
 
     @override
     def __call__(self, retry_state: "RetryCallState") -> float:
-        return sum(x(retry_state=retry_state) for x in self.wait_funcs)
+        # Positional: a plain callable may name its parameter anything.
+        return sum(x(retry_state) for x in self.wait_funcs)
 
 
 class wait_chain(wait_base):
[assistant] All three regressions are fixed. Each has a regression test that failed against the unfixed code for its reported reason, and the full suite passes: `exit=0`, 177 passed, 1 skipped. The changes are uncommitted in this worktree.

**What changed**

1. **`wait=None`, `wait=0`, `wait=sum([])`** (`tenacity/__init__.py`, `tenacity/asyncio/__init__.py`): restored the `if self.wait:` guard in both `_run_wait` methods, which commit e6ef84a had removed on the premise that `wait` is never falsy. The `wait` annotations in `BaseRetrying.__init__`, `AsyncRetrying.__init__` and both `retry()` overloads now r
…[1620 chars elided]…
`wait=5` into no wait.
- **`wait_chain` has the same keyword bug** at `tenacity/wait.py:125` (`wait_func(retry_state=retry_state)`). I left it alone because you scoped the fix to `wait_combine`; it is a one-line change if you want it. `wait_random_exponential`'s `super().__call__(retry_state=...)` is a method call and is harmless.
- **Possibly unused ignore:** the widening may make the existing `# type: ignore[arg-type]` on `wait=sum(` in `test_wait_arbitrary_sum` unused. I did not touch it, per the guardrails.
- **Skip:** the one skipped test is unidentified; I did not check which test it is.
