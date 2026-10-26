# trajectory base-1

final message:
All three regressions are fixed. The full suite passes (177 passed, 1 skipped), and `check_changed.py` reports 0 problems. Ruff and mypy were not run because they aren't installed in this environment, so the lint and typing status is unverified.

**Root causes**
1. Commit `e6ef84a` removed the `if self.wait:` guard in both `_run_wait` methods, on the claim that `wait` is never falsy. `None`, `0` and `sum([])` are falsy, so they reached the unguarded call.
2. `wait_base.__radd__` returned `NotImplemented` for any non-zero left operand, so `callable + wait_fixed(1)` raised `TypeError`.
3. `wait_combine` called its strategies with `retry_state=` as a keyword, which fails for a plain callable whose parameter has another name.

**Changes**
- `tenacity/__init__.py` and `tenacity/asyncio/__init__.py`: `_run_wait` calls `self.wait` only when `callable(self.wait)`, otherwise it sets the sleep to `0.0`. I used `callable()` rather than a truthiness check, because the project enables `truthy-bool` and `warn_unreachable`.
- The `wait` parameter of `BaseRetrying.__init__` and `AsyncRetrying.__init__` is now annotated `WaitBaseT | int | None`, so the runtime behaviour matches the declared type.
- `tenacity/wait.py`: `__radd__` returns `self` for the int seed and `wait_combine(other, self)` for a callable. `wait_combine` takes `WaitBaseT` strategies and calls them positionally. `__add__` takes `WaitBaseT` as well, for symmetry.
- Tests: `test_falsy_wait_means_no_wait` (sync and async, over `None`, `0`, `sum([])`), `test_plain_callable_plus_wait_is_combined`, and `test_wait_combine_passes_retry_state_positionally`. Each failed against the unfixed code for its own reason before the fix.
- Reno note: `releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml`, as a `fixes:` entry.

**Left alone**
- `wait_chain.__call__` still calls its strategies with `retry_state=` as a keyword, so it has the same bug as regression 3. It isn't in the three items you listed, so I didn't change it. It's a one-line fix if you want it in this change.
- One test in the suite is skipped. I didn't check why.

The changes are uncommitted.

## events
[assistant] I'll start by reading the wait strategy code and the existing tests before writing any regression test.
[tool_use Bash] {"command": "git status --short && ls && cat tenacity/wait.py && grep -n \"wait\" tenacity/__init__.py | head -60", "description": "Inspect repo state and wait strategy source"}
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
# Copyright 2016–2021 Julien Danjou
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
# distri
…[11836 chars elided]…
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
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md; cat .lithify/harness/scripts/run_tests.py | head -40; ls tests; cat .lithify/memory.md 2>/dev/null | head -20", "description": "Check harness skill sections, run script, tests dir"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[1605 chars elided]…
  (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[assistant] The Docs tools aren't relevant here, so I'll stay on the repo. Next I'll read the contract sections that apply and the retry-loop code that calls `self.wait`.
[tool_use Bash] {"command": "F=.lithify/harness/skills/tenacity-change-contract/SKILL.md && sed -n '110,150p;192,229p;331,400p' $F", "description": "Read relevant contract skill sections"}
[tool_result] ## 1b. Strategy composition (`|`, `&`) and sync/async mixing
- Sync combinators (`tenacity/retry.py` `retry_any`/`retry_all`) call members directly. Async
  ones (`tenacity/asyncio/retry.py`) await each member through `_utils.wrap_to_async_func`,
  so they accept sync and async members alike. A sync combinator must never hold an async
  member: the call returns a coroutine, which is truthy. Retry then never stops, and the
  suite hangs instead of failing.
- `retry_base.__or__`/`__and__` call `ot
…[8894 chars elided]…
 a multi-line `@retry(...)` call whose last line is `)`. Separate a nested
  decorated def from the code above it with a blank line before the `@`, never after the `)`.
- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
  annotated (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
[tool_use Bash] {"command": "sed -n '240,300p;320,335p;410,425p' tenacity/__init__.py && git log --oneline -3 -- tenacity/wait.py && git log -p -S'__radd__' --oneline -- tenacity/wait.py | head -80", "description": "Read Retrying init, wait call site, and git history"}
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
   
…[5137 chars elided]…
t):
+class wait_combine(wait_base):
     """Combine several waiting strategies."""
 
     def __init__(self, *strategies):
@@ -71,7 +92,7 @@ class wait_combine(object):
             self.wait_funcs))
 
 
-class wait_chain(object):
+class wait_chain(wait_base):
     """Chain two or more waiting strategies.
 
     If all strategies are exhausted, the very last strategy is used
@@ -97,7 +118,7 @@ class wait_chain(object):
         return wait_func(previous_attempt_number, delay_since_first_attempt)
[assistant] The `_run_wait` call has no guard for falsy values, which matches regression 1. I'll check the async path and whether an older guard existed in history before writing the test.
[tool_use Bash] {"command": "grep -rn \"_run_wait\\|self.wait\\b\\|_first_set\" tenacity/ | grep -v \"^tenacity/wait.py\" ; grep -n -A8 \"def _first_set\" tenacity/__init__.py; git log --oneline -S\"sleep = 0.0\" -- tenacity/ | head; git log --oneline -S\"if self.wait\" -- tenacity/ | head -3; echo ---; grep -n \"wait_combine\\|wait_fixed(1)\\|radd\\|+ wait\\|wait=None\\|wait=0\" tests/*.py | head -30", "description": "Locate wait call sites, history of wait guard, and existing tests"}
[tool_result] tenacity/__init__.py:183:def _first_set(first: t.Any | object, second: t.Any) -> t.Any:
tenacity/__init__.py:264:        self.wait = wait
tenacity/__init__.py:295:            sleep=_first_set(sleep, self.sleep),
tenacity/__init__.py:296:            stop=_first_set(stop, self.stop),
tenacity/__init__.py:297:            wait=_first_set(wait, self.wait),
tenacity/__init__.py:298:            retry=_first_set(retry, self.retry),
tenacity/__init__.py:299:            before=_first_set(before, self.befo
…[1892 chars elided]…
wait_fixed(1)
tests/test_asyncio.py:600:            wait=wait_fixed(1),
tests/test_tenacity.py:442:    def test_wait_combine(self) -> None:
tests/test_tenacity.py:444:            wait=tenacity.wait_combine(
tests/test_tenacity.py:482:            wait=tenacity.wait_fixed(1)
tests/test_tenacity.py:496:                    tenacity.wait_fixed(1),
tests/test_tenacity.py:526:                *[tenacity.wait_fixed(1) for i in range(2)]
tests/test_tenacity.py:1739:            wait=tenacity.wait_fixed(1),
[assistant] Commit `e6ef84a` touched the guard, so I'll read its diff for the wait code and the async `_run_wait`.
[tool_use Bash] {"command": "git show e6ef84a -- tenacity/ | grep -n -B6 -A6 \"wait\\|__radd__\\|wait_combine\" | head -150; echo ---; sed -n 140,160p tenacity/asyncio/__init__.py; echo ---; sed -n 440,470p tests/test_tenacity.py", "description": "Show truthiness-removal diff and existing wait tests"}
[tool_result] 4-
5-    refactor: drop always-true truthiness checks and enable truthy-bool (#679)
6-    
7-    `truthy-bool` reports objects tested for truthiness that implement neither
8-    `__bool__` nor `__len__`, and so can only ever be true. Three sites:
9-    
10:    `BaseRetrying._run_wait` and `AsyncRetrying._run_wait` both guarded the
11:    wait call with `if self.wait:`. `wait` is typed `WaitBaseT` and defaults to
12:    a `wait_none()` instance, so it is never falsy and the `sleep = 0.0` branch
1
…[3679 chars elided]…
rying(wait=tenacity.wait_exception(predicate))

        fut1 = tenacity.Future.construct(1, ValueError(), True)
        self.assertEqual(r.wait(make_retry_state(1, 0, last_result=fut1)), 3.5)

        fut2 = tenacity.Future.construct(1, KeyError(), True)
        self.assertEqual(r.wait(make_retry_state(1, 0, last_result=fut2)), 10.0)

        fut3 = tenacity.Future.construct(1, None, False)
        with self.assertRaises(RuntimeError):
            r.wait(make_retry_state(1, 0, last_result=fut3))
[assistant] The guard was removed in `e6ef84a` on the assumption that `wait` is never falsy. That's wrong for `None`, `0` and `sum([])`. Before writing tests I'll look at the existing test helpers and the async test file layout.
[tool_use Bash] {"command": "grep -n \"^class \\|^def \\|^from\\|^import\" tests/test_tenacity.py | head -60; grep -n \"^class \\|^from\\|^import\\|def make_retry_state\" tests/test_asyncio.py tests/__init__.py | head -40; grep -n \"class TestWaitConditions\" -A12 tests/test_tenacity.py; grep -n \"sleep=\" tests/test_tenacity.py | head -5; grep -n \"sleep=\" tests/test_asyncio.py | head -5", "description": "Survey test file structure and helpers"}
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
37:def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
46:def _set_delay_sinc
…[4106 chars elided]…
61:                    r.stop(make_retry_state(2, 0.999, upcoming_sleep=0.0001))
263:                self.assertTrue(r.stop(make_retry_state(2, 1, upcoming_sleep=0.001)))
264:                self.assertTrue(r.stop(make_retry_state(2, 1, upcoming_sleep=1)))
267:                self.assertFalse(r.stop(make_retry_state(2, 0.999, upcoming_sleep=0)))
268:                self.assertTrue(r.stop(make_retry_state(2, 1, upcoming_sleep=0)))
585:@retry(sleep=my_async_sleep)
599:            sleep=mock_sleep,
[assistant] I have the layout. Next I'll read one async context-manager test to copy its shape, plus `make_retry_state`.
[tool_use Bash] {"command": "sed -n 54,86p tests/test_tenacity.py; sed -n 249,275p tests/test_asyncio.py; sed -n 316,335p tests/test_asyncio.py; sed -n 515,520p tests/test_asyncio.py", "description": "Read helper and async test patterns"}
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
…[1760 chars elided]…
t=wait_fixed(1)
            ):
                with attempt:
                    raise Exception
        except RetryError:
            pass
        t = current_time_ms() - start
        self.assertLess(t, 1.1)

    @asynctest
    async def test_retry_with_result(self) -> None:
        async def test() -> int:
            attempts = 0
        with pytest.raises(TypeError):
            for attempts in AsyncRetrying():
                with attempts:
                    await _async_function(thing)
[assistant] I have what I need. The plan, following the harness order:

1. Add three tests (one per regression) and run them against the unfixed code to confirm each fails for its own reason.
2. Fix `_run_wait` (sync and async), `wait_base.__radd__`/`__add__`, and the `wait_combine` call.
3. Re-run the tests, then the full suite and `check_changed.py`.

I'll add the sync tests first. Each one uses a `typing.Any` value or a plain callable so mypy strictness doesn't block the test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tests/test_tenacity.py", "old_string": "            self.assertGreaterEqual(w, 5)\n\n    def test_wait_exception(self) -> None:", "new_string": "            self.assertGreaterEqual(w, 5)\n\n    def test_falsy_wait_means_no_wait(self) -> None:\n        wa
…[1002 chars elided]…
sertEqual(3, combined(make_retry_state(1, 0)))\n\n    def test_wait_combine_passes_retry_state_positionally(self) -> None:\n        def any_param_name(state: RetryCallState) -> float:\n            return 2\n\n        combined = tenacity.wait_combine(any_param_name, tenacity.wait_fixed(1))\n        self.assertEqual(3, combined(make_retry_state(1, 0)))\n\n    def test_wait_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async counterpart, next to the existing `test_sleeps` in `TestContextManager`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tests/test_asyncio.py", "old_string": "        t = current_time_ms() - start\n        self.assertLess(t, 1.1)\n\n    @asynctest\n    async def test_retry_with_result(self) -> None:", "new_string": "        t = current_time_ms() - start\n        self.asse
…[529 chars elided]…
eep\n                )\n                async for attempt in retrying:\n                    with attempt:\n                        attempts += 1\n                        if attempts == 1:\n                            raise ValueError\n                self.assertEqual(2, attempts)\n                self.assertEqual([0], sleeps)\n\n    @asynctest\n    async def test_retry_with_result(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Next I'll run the three new sync tests and the async one alone against the unfixed code, using the project's `run_tests.py` as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; for t in tests/test_tenacity.py::TestWaitConditions::test_falsy_wait_means_no_wait tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_is_combined tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait; do echo \"=== $t\"; $PY .lithify/harness/scripts/run_tests.py --timeout 60 $t > /tmp/red_out.txt 2>&1; echo \"exit=$?\"; grep -E \"Error|assert|FAILED|passed|failed\" /tmp/red_out.txt | head -8; done", "description": "Run each new regression test against unfixed code"}
[tool_result] === tests/test_tenacity.py::TestWaitConditions::test_falsy_wait_means_no_wait
exit=1
                        raise ValueError
>               self.assertEqual(2, r(fails_once))
retry_state = <RetryCallState 4455268720: attempt #1; slept for 0.0; last result: failed (ValueError )>
E       TypeError: 'int' object is not callable
tenacity/__init__.py:418: TypeError
SUBFAILED(wait=None) tests/test_tenacity.py::TestWaitConditions::test_falsy_wait_means_no_wait
SUBFAILED(wait=0) tests/test_tenacity.py
…[1404 chars elided]…
tempt #1; slept for 0.0; last result: failed (ValueError )>,)
E       TypeError: 'int' object is not callable
tenacity/_utils.py:130: TypeError
SUBFAILED(wait=None) tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait
SUBFAILED(wait=0) tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait
SUBFAILED(wait=0) tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait
========================= 3 failed, 1 passed in 0.04s ==========================
[assistant] All four tests fail, each for its own reason:

- `wait=None`, `0` and `sum([])` raise on the unguarded `self.wait(...)` call.
- `callable + wait_fixed(1)` hits `TypeError: unsupported operand`, because `__radd__` returns `NotImplemented`.
- `wait_combine` calls the callable with `retry_state=`, which fails on a differently named parameter.

Before choosing the falsy-check form, I'll check the lint and mypy settings, since the commit that removed the guard turned on `truthy-bool`.
[tool_use Bash] {"command": "sed -n '/\\[tool.mypy\\]/,/^\\[tool.[a-ln-z]/p' pyproject.toml | head -40; grep -n \"truthy\\|select\\|PL\\|ruff\" pyproject.toml | head -20", "description": "Check mypy and ruff settings in pyproject"}
[tool_result] [tool.mypy]
strict = true
# Match `requires-python`, so results do not depend on which interpreter
# happens to run mypy. Without this it defaults to the running version and
# silently skips checking that the code is valid on the oldest one we support.
python_version = "3.10"
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]
# `strict` is not "everything" -- these are checks it leaves off.
warn_unreachable = true
disallow_any_unimported = true
extra_check
…[224 chars elided]…
thy-iterable",
    "unused-awaitable",
]

56:    "ruff==0.16.1",
74:    { cmd = "ruff check --fix ." },
75:    { cmd = "ruff format ." },
80:    { cmd = "ruff check ." },
81:    { cmd = "ruff format --check ." },
96:[tool.ruff]
102:[tool.ruff.lint]
103:select = ["ASYNC", "B", "C4", "DTZ", "E", "EXE", "F", "FLY", "FURB", "I", "ICN", "ISC", "LOG", "PERF", "PGH", "PIE", "PTH", "PYI", "RET", "RSE", "RUF", "SIM", "SLF", "SLOT", "T10", "TC", "UP", "W"]
136:    "truthy-bool",
137:    "truthy-iterable",
[assistant] `truthy-bool`, `redundant-expr` and `warn_unreachable` are all on, and `wait` is declared as `WaitBaseT`, which excludes `None` and `int`. So an `is None` or `if self.wait:` check would be flagged, and so would a `callable()` negative branch. The honest fix is to widen the declared type of `wait` to admit `int | None` (which is what the user says must work) and branch on `callable()`. Before editing I'll confirm `callable` isn't shadowed and see how `AsyncRetrying` declares `wait`.
[tool_use Bash] {"command": "grep -rn \"callable\\b\" tenacity/ | grep -v \"Callable\" | head; grep -n \"wait\" tenacity/asyncio/__init__.py | head -20; grep -n \"def wrap_to_async_func\" -A4 tenacity/_utils.py", "description": "Check callable shadowing and async wait typing"}
[tool_result] tenacity/__init__.py:667:    Provides the original callable signature plus retry control attributes.
tenacity/__init__.py:683:    # plain callable attribute rather than a descriptor, so accessing a
tenacity/__init__.py:765:    if len(dargs) == 1 and callable(dargs[0]):
tenacity/__init__.py:771:                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
tenacity/__init__.py:777:        if _utils.is_coroutine_callable(f) or (
tenacity/__init__.py:778:            slee
…[1463 chars elided]…
p_to_async_func(self.wait)(
157:        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
166:            result = await action(retry_state)
194:            do = await self.iter(retry_state=self._retry_state)
201:                await self.sleep(do)  # type: ignore[misc]
123:def wrap_to_async_func(
124-    call: typing.Callable[..., typing.Any],
125-) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
126-    if is_coroutine_callable(call):
127-        return call
[assistant] `AsyncRetrying.__init__` declares `wait` the same way, so it needs the same widening. Here are the edits, starting with the sync side: the widened `__init__` annotation and the `_run_wait` guard.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/__init__.py", "old_string": "        wait: \"WaitBaseT\" = wait_none(),\n        retry: \"RetryBaseT\" = retry_if_exception_type(),\n        before: t.Callable[[\"RetryCallState\"], None] = before_nothing,", "new_string": "        wait: \"WaitBaseT | int | None\" = wait_none(),\n        retry: \"RetryBaseT\" = retry_if_exception_type(),\n        before: t.Callable[[\"RetryCallState\"], None] = before_nothing,"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/__init__.py", "old_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        retry_state.upcoming_sleep = self.wait(retry_state)", "new_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        # `wait=None`, `wait=0` and `wait=sum([])` all mean \"no wait\".\n        if callable(self.wait):\n            retry_state.upcoming_sleep = self.wait(retry_state)\n        else:\n            retry_state.upcoming_sleep = 0.0"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py", "old_string": "        wait: \"WaitBaseT\" = tenacity.wait.wait_none(),", "new_string": "        wait: \"WaitBaseT | int | None\" = tenacity.wait.wait_none(),"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py", "old_string": "        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(\n            retry_state\n        )", "new_string": "        # `wait=None`, `wait=0` and `wait=sum([])` all mean \"no wait\".\n        if callable(self.wait):\n            retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(\n                retry_state\n            )\n        else:\n            retry_state.upcoming_sleep = 0.0"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next, `wait.py`: `__add__` and `__radd__` accept plain callables, `wait_combine` accepts them as strategies, and it calls them positionally.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __add__(self, other: \"wait_base\") -> \"wait_combine\":\n        return wait_combine(self, other)\n\n    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, 
…[472 chars elided]…
t 0, so tolerate that to\n        # make summing waits work. Any other non-int left operand is a plain\n        # callable (a `wait_base` left operand's `__add__` never defers to us),\n        # so combine it with this strategy.\n        if isinstance(other, int):\n            if other != 0:\n                return NotImplemented\n            return self\n        return wait_combine(other, self)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __init__(self, *strategies: wait_base) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state=retry_state) for x in self.wait_funcs)", "new_string": "    def __init__(self, *strategies: WaitBaseT) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        # Positional, so plain callables may name their parameter anything.\n        return sum(x(retry_state) for x in self.wait_funcs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[assistant] The fix is in. I'll re-run the four new tests, then the full suite and `check_changed.py`, all in the foreground through the harness scripts.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_falsy_wait_means_no_wait tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_is_combined tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait > /tmp/green_targeted.txt 2>&1; echo \"targeted exit=$?\"; tail -8 /tmp/green_targeted.txt", "description": "Run the four regression tests against the fix"}
[tool_result] targeted exit=0
tests/test_tenacity.py::TestWaitConditions::test_plain_callable_plus_wait_is_combined PASSED [ 50%]
tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally PASSED [ 75%]
tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait 
tests/test_asyncio.py::TestContextManager::test_falsy_wait_means_no_wait PASSED [100%]

===================== 4 passed, 6 subtests passed in 0.02s =====================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full_suite.txt 2>&1; echo \"full exit=$?\"; tail -6 /tmp/full_suite.txt; echo ---; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check exit=$?\"; tail -15 /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] full exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 177 passed, 1 skipped, 18 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---
check exit=0
changed: tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/wait.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (177 passed, 1 skipped), and `check_changed.py` reports 0 problems. The contract for `tenacity/` changes requires a reno note for user-visible fixes, so I'll add one. Then I'll re-run the checker to validate it.
[tool_use Bash] {"command": "ls releasenotes/notes | tail -3 && openssl rand -hex 8", "description": "List existing reno notes and generate a hex suffix"}
[tool_result] wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
bed32484f72a9eb6
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml", "content": "---\nfixes:\n  - |\n    ``wait=None``, ``wait=0`` and ``wait=sum([])`` mean \"no wait\" again, for\n    both ``Retrying`` and ``AsyncRetrying``. Previously they raised ``TypeError``\n    as soon as a retry happened.\n  - |\n    A plain callable can be added to a wait strategy with ``+``, for example\n    ``my_callable + wait_fixed(1)``. The result is a ``wait_combine`` that sums\n    both. Previously this raised ``TypeError``.\n  - |\n    ``wait_combine`` passes the retry state to its strategies positionally, so\n    plain callables may name their parameter anything.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-214815-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"check exit=$?\"; tail -6 /tmp/check2.txt; git status --short; git diff --stat", "description": "Re-run changed-file checks and show diff summary"}
[tool_result] check exit=0
changed: releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tenacity/wait.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/wait.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml
 tenacity/__init__.py         |  8 ++++++--
 tenacity/asyncio/__init__.py | 12 ++++++++----
 tenacity/wait.py             | 22 +++++++++++++---------
 tests/test_asyncio.py        | 22 ++++++++++++++++++++++
 tests/test_tenacity.py       | 37 +++++++++++++++++++++++++++++++++++++
 5 files changed, 86 insertions(+), 15 deletions(-)
[assistant] All three regressions are fixed. The full suite passes (177 passed, 1 skipped), and `check_changed.py` reports 0 problems. Ruff and mypy were not run because they aren't installed in this environment, so the lint and typing status is unverified.

**Root causes**
1. Commit `e6ef84a` removed the `if self.wait:` guard in both `_run_wait` methods, on the claim that `wait` is never falsy. `None`, `0` and `sum([])` are falsy, so they reached the unguarded call.
2. `wait_base.__radd__` returned `NotImplemented` for any non-zero left operand, so `callable + wait_fixed(1)` raised `TypeError`.
3. `wait_
…[950 chars elided]…
wait_is_combined`, and `test_wait_combine_passes_retry_state_positionally`. Each failed against the unfixed code for its own reason before the fix.
- Reno note: `releasenotes/notes/wait-no-wait-and-callable-combine-bed32484f72a9eb6.yaml`, as a `fixes:` entry.

**Left alone**
- `wait_chain.__call__` still calls its strategies with `retry_state=` as a keyword, so it has the same bug as regression 3. It isn't in the three items you listed, so I didn't change it. It's a one-line fix if you want it in this change.
- One test in the suite is skipped. I didn't check why.

The changes are uncommitted.
