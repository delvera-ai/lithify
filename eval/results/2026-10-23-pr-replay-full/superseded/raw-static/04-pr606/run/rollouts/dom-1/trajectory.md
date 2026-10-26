# trajectory dom-1

final message:
Fixed: `retry_if_exception_type(IOError) | my_predicate` now returns a `retry_any` instead of raising, and the same holds for `&` and for the reverse order, in both sync and async code. The full suite passes (138 passed, 1 skipped). I did not run mypy or ruff, since neither is installed in the project's check interpreter.

**Cause:** `retry_base.__or__` and `__and__` always delegated to `other.__ror__` / `other.__rand__`. A plain function has neither, so the call raised `AttributeError: 'function' object has no attribute '__ror__'`. The reverse order worked because Python falls back to the right operand's reflected method.

**Changes:**
- `tenacity/retry.py`: `__or__` / `__and__` delegate only when `other` is a `retry_base`, and otherwise build `retry_any` / `retry_all` directly. Operator and `retry_any` / `retry_all` constructor annotations now use the existing `RetryBaseT` alias, so plain callables are accepted.
- `tenacity/asyncio/retry.py`: the four async operators and the async `retry_any` / `retry_all` constructors accept `SyncRetryBaseT | RetryBaseT`, which includes plain callables. The async operators already built the async classes directly, so their logic is unchanged.
- `tests/test_tenacity.py`: `test_retry_or_and_and_with_plain_callable` covers `|` and `&` in both orders, plus a decorator that uses `retry_if_exception_type(IOError) & plain` through the sync loop.
- `tests/test_asyncio.py`: `test_retry_with_plain_callable_composition` drives an `AsyncRetrying` loop with a sync `retry_base` on either side of a plain callable.
- `releasenotes/notes/fix-retry-composition-plain-callable-1d09c70e6f5b4277.yaml`: the reno note.

**Fail-on-base check:** both new tests fail on HEAD with the `AttributeError` above and pass on the fix. My first async test passed on HEAD because it only used async strategies, which never reach the broken sync operator. I rewrote it to put a sync `retry_base` on the left.

**Choices you may want to review:**
- The async tests cover sync `retry_base` on the left only, because async-only composition was never broken.
- Stop and wait strategies are unchanged. They already build their combinators directly and the report only concerned retry strategies.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex 
…[6661 chars elided]…
n> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "cat memory.md 2>/dev/null; ls; git log --oneline -1; grep -rn \"__or__\\|__and__\\|__ror__\\|__rand__\\|retry_any\\|retry_all\" tenacity/*.py | head -60", "description": "Inspect repo layout and composition code"}
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
571da37 lithify: probe base
tenacity/__init__.py:44:    retry_all,
tenacity/__init__.py:46:    retry_any,
tenacity/__init__.py:744:    "retry_all",
tenacity/__init__.py:746:    "retry_any",
tenacity/stop.py:34:    def __and__(self, other: "stop_base") -> "stop_all":
tenacity/stop.py:37:    def __or__(self, other: "stop_base") -> "stop_any":
tenacity/retry.py:32:    def __and__(self, other: "retry_base
…[91 chars elided]…
py:35:    def __rand__(self, other: "retry_base") -> "retry_all":
tenacity/retry.py:36:        return retry_all(other, self)
tenacity/retry.py:38:    def __or__(self, other: "retry_base") -> "retry_any":
tenacity/retry.py:39:        return other.__ror__(self)
tenacity/retry.py:41:    def __ror__(self, other: "retry_base") -> "retry_any":
tenacity/retry.py:42:        return retry_any(other, self)
tenacity/retry.py:254:class retry_any(retry_base):
tenacity/retry.py:264:class retry_all(retry_base):
[tool_use Bash] {"command": "sed -n 1,60p tenacity/retry.py; echo ----; sed -n 245,280p tenacity/retry.py; echo ----; grep -n \"class\\|__and__\\|__or__\\|__rand__\\|__ror__\\|RetryBaseT\\|wrap_to_async\" tenacity/asyncio/retry.py; echo ----; grep -n \"RetryBaseT\" -r tenacity | head -30; echo ----; ls -a .lithify/harness/skills/tenacity-change-contract/scripts 2>&1; ls <work>/env-tenacity/bin/python 2>&1", "description": "Read retry composition code and check helper paths"}
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
…[3104 chars elided]…
f_exception_type(),
tenacity/asyncio/__init__.py:38:    RetryBaseT,
tenacity/asyncio/__init__.py:46:    from tenacity.retry import RetryBaseT as SyncRetryBaseT
tenacity/asyncio/__init__.py:82:        retry: "SyncRetryBaseT | RetryBaseT" = tenacity.retry_if_exception_type(),
tenacity/asyncio/retry.py:53:RetryBaseT = (
----
.
..
fails_on_base.py
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 20,58p tenacity/asyncio/retry.py; echo ----; cat tenacity/_utils.py | grep -n \"def \\|wrap\" ; echo ----; PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport tenacity\nfrom tenacity import retry_if_exception_type\ndef p(s): return False\nfor expr in ['re
…[5 chars elided]…
f_exception_type(IOError) | p', 'p | retry_if_exception_type(IOError)', 'retry_if_exception_type(IOError) & p', 'p & retry_if_exception_type(IOError)']:\n    try:\n        print(expr, '->', type(eval(expr)).__name__)\n    except Exception as e: print(expr, 'EXC', type(e).__name__, e)\n\"; git log --oneline -8 -- tenacity/retry.py", "description": "Read async retry operators and reproduce the bug"}
[tool_result] if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


class async_retry_base(retry_base):
    """Abstract base class for async retry strategies."""

    @abc.abstractmethod
    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
        pass

    def __and__(  # type: ignore[override]
        self, other: "retry_base | async_retry_base"
    ) -> "retry_all":
        return retry_all(self, other)

    def __rand__(  # type: ignore[misc,override]
…[1226 chars elided]…
as no attribute '__rand__'
p & retry_if_exception_type(IOError) -> retry_all
fea6430 refactor: replace deprecated typing.Pattern with re.Pattern (#589)
9686ed7 refactor: enable additional ruff rules and fix violations (#584)
c4bada4 chore: enable ruff I, UP, B rules and auto-fix codebase (#571)
a44271f fix: Add re.Pattern to allowed match types (#497)
21137e7 Add async strategies (#451)
0b76e7c ci: replace black and flake8 by ruff
d9438b3 fix(mypy): add missing typing (#384)
c0fc691 ci: add mypy
[assistant] Reproduced: `retry_if_exception_type(IOError) | p` raises `AttributeError` because `retry_base.__or__` delegates to `p.__ror__`, which a plain function lacks. The reverse order works. Next I'll check the async composition classes and their constructors before choosing the fix.
[tool_use Bash] {"command": "sed -n 1,19p tenacity/asyncio/retry.py | grep -n import; sed -n 92,125p tenacity/asyncio/retry.py; echo ----; sed -n 25,45p tenacity/stop.py; echo ----; grep -n \"retry_base\\|RetryBaseT\" tenacity/asyncio/retry.py | head; echo ----; grep -n \"def test_retry_or\\|def test_retry_and\\|class TestRetryConditions\\|class TestContextManager\\|retry_if_result(.*) |\\|tasyncio.retry_if_exception(.*)|\" tests/test_tenacity.py tests/test_asyncio.py | head -20; cat .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py | head -60", "description": "Read async retry classes, tests, and check script"}
[tool_result] 16:import abc
17:import typing
19:from tenacity import _utils, retry_base
        return False


class retry_any(async_retry_base):
    """Retries if any of the retries condition is valid."""

    def __init__(self, *retries: retry_base | async_retry_base) -> None:
        self.retries = retries

    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
        result = False
        for r in self.retries:
            result = result or await _utils.wrap_to_a
…[4116 chars elided]…
e != 0:
            print("ERROR: git archive HEAD failed:", archive.stderr.decode(), file=sys.stderr)
            return 2
        untar = subprocess.run(
            ["tar", "-x", "-C", tmp], input=archive.stdout, capture_output=True, check=False
        )
        if untar.returncode != 0:
            print("ERROR: extracting HEAD failed:", untar.stderr.decode(), file=sys.stderr)
            return 2
        shutil.rmtree(os.path.join(tmp, "tests"), ignore_errors=True)
        shutil.copytree(
[assistant] The root cause is `retry_base.__or__`/`__and__`, which always delegate to `other.__ror__`/`__rand__`. A plain callable has neither, so it raises. The fix is to delegate only when `other` is a `retry_base` and build `retry_any`/`retry_all` directly otherwise. The annotations and the async operators need the same widening. Now I'll look at the existing tests to match their style.
[tool_use Bash] {"command": "sed -n 715,750p tests/test_tenacity.py; echo ----; sed -n 295,360p tests/test_asyncio.py; echo ----; sed -n 36,50p tenacity/asyncio/__init__.py; echo ----; ls releasenotes/notes | tail -4; cat \"releasenotes/notes/$(ls releasenotes/notes | grep fix | tail -1)\"", "description": "Read existing composition tests and release note format"}
[tool_result]         self.assertFalse(r(tenacity.Future.construct(1, 3, False)))
        self.assertFalse(r(tenacity.Future.construct(1, 1, True)))

    def test_retry_and(self) -> None:
        retry = tenacity.retry_if_result(lambda x: x == 1) & tenacity.retry_if_result(
            lambda x: isinstance(x, int)
        )

        def r(fut: tenacity.Future) -> bool:
            retry_state = make_retry_state(1, 1.0, last_result=fut)
            return retry(retry_state)

        self.assertTrue(r(tenacity.
…[3259 chars elided]…
    retry_if_result,
)

if t.TYPE_CHECKING:
    from tenacity.retry import RetryBaseT as SyncRetryBaseT
    from tenacity.stop import StopBaseT
    from tenacity.wait import WaitBaseT

WrappedFnReturnT = t.TypeVar("WrappedFnReturnT")
----
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
fixes:
  - "Fix issue #288 : __name__ and other attributes for async functions"
[assistant] Now the sync fix in `tenacity/retry.py`: delegate only for `retry_base` operands, and widen the operator and constructor annotations to the existing `RetryBaseT` alias.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/retry.py", "old_string": "    def __and__(self, other: \"retry_base\") -> \"retry_all\":\n        return other.__rand__(self)\n\n    def __rand__(self, other: \"retry_base\") -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __o
…[394 chars elided]…
\n\n    def __rand__(self, other: \"RetryBaseT\") -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __or__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        if isinstance(other, retry_base):\n            return other.__ror__(self)\n        return retry_any(self, other)\n\n    def __ror__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        return retry_any(other, self)"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/retry.py", "old_string": "    def __init__(self, *retries: retry_base) -> None:\n        self.retries = retries\n\n    def __call__(self, retry_state: \"RetryCallState\") -> bool:\n        return any(r(retry_state) for r in self.retries)\n\n\ncla
…[142 chars elided]…
None:", "new_string": "    def __init__(self, *retries: \"RetryBaseT\") -> None:\n        self.retries = retries\n\n    def __call__(self, retry_state: \"RetryCallState\") -> bool:\n        return any(r(retry_state) for r in self.retries)\n\n\nclass retry_all(retry_base):\n    \"\"\"Retries if all the retries condition are valid.\"\"\"\n\n    def __init__(self, *retries: \"RetryBaseT\") -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/retry.py has been updated successfully.
[assistant] Now the async side in `tenacity/asyncio/retry.py`. Its operators already build the async classes directly, so they only need the wider annotation. The `retry_any`/`retry_all` constructors also need to accept plain callables, since `wrap_to_async_func` already handles them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/asyncio/retry.py", "old_string": "if typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n\n\nclass async_retry_base(retry_base):\n    \"\"\"Abstract base class for async retry strategies.\"\"\"\n\n    @abc.abstractmethod\n    async de
…[1351 chars elided]…
f, other: \"SyncRetryBaseT | RetryBaseT\"\n    ) -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __or__(  # type: ignore[override]\n        self, other: \"SyncRetryBaseT | RetryBaseT\"\n    ) -> \"retry_any\":\n        return retry_any(self, other)\n\n    def __ror__(  # type: ignore[misc,override]\n        self, other: \"SyncRetryBaseT | RetryBaseT\"\n    ) -> \"retry_any\":"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/asyncio/retry.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/    def __init__(self, \\*retries: retry_base | async_retry_base) -> None:/    def __init__(self, *retries: \"SyncRetryBaseT | RetryBaseT\") -> None:/' tenacity/asyncio/retry.py && grep -n \"__init__\\|SyncRetryBaseT\" tenacity/asyncio/retry.py", "description": "Widen async retry_any/retry_all constructor annotations"}
[tool_result] sed: 2: "tenacity/asyncio/retry.py
": undefined label 'enacity/asyncio/retry.py'
[assistant] The sed invocation mangled its arguments, so I'll make that change with the Edit tool instead. The constructor line appears twice, so I'll use `replace_all`.
[tool_use Edit] {"replace_all": true, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/asyncio/retry.py", "old_string": "    def __init__(self, *retries: retry_base | async_retry_base) -> None:", "new_string": "    def __init__(self, *retries: \"SyncRetryBaseT | RetryBaseT\") -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tenacity/asyncio/retry.py has been updated. All occurrences were successfully replaced.
[assistant] Source edits are in. Next I'll add regression tests: a sync pair in `tests/test_tenacity.py` (both operand orders for `|` and `&`) and an async one in `tests/test_asyncio.py`. First I need the import headers and the `make_retry_state` helper.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_asyncio.py | grep -n \"import\"; grep -n \"^def make_retry_state\" -A6 tests/test_tenacity.py; grep -n \"^class TestContextManager\" -A3 tests/test_asyncio.py; grep -n \"def test_retry_with_async_result_and\" -A30 tests/test_asyncio.py | grep -n \"return attempts\\|self.assertEqual\" | head -3", "description": "Check test imports and helper signatures"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
32:import tenacity
33:from tenacity import (
55:def make_retry_state(
56-    previous_attempt_number: typing.Any,
57-    delay_since_first_attempt: typing.Any,
58-    last_result: typing.Any = None,
59-    upcoming_sleep: typing.Any = 0,
60-) -> RetryCallState:
61-    """Construct RetryCallState for given attempt number & delay.
178:class TestContextManager(unittest.TestCase):
179-    @asynctest
180-    async def test_do_max_attempts(self) -> None:
181-        attempts = 0
17:374-            return attempts
21:378-        self.assertEqual(3, result)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py", "old_string": "        self.assertTrue(r(tenacity.Future.construct(1, \"foo\", False)))\n        self.assertFalse(r(tenacity.Future.construct(1, \"foobar\", False)))\n        self.assertFalse(r(tenacity.Future.construct(1, 2.2, Fa
…[2324 chars elided]…
   return retry_state.attempt_number >= 3\n\n        @tenacity.retry(retry=tenacity.retry_if_exception_type(IOError) | is_third_attempt)\n        def flaky() -> int:\n            nonlocal attempts\n            attempts += 1\n            if attempts < 3:\n                raise OSError()\n            return attempts\n\n        self.assertEqual(3, flaky())\n\n    def _raise_try_again(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] I made two mistakes in that test: `is_int` is unused, and the decorator case is wrong. With `retry_if_exception_type(IOError) | is_third_attempt`, the third successful attempt would still retry because `attempt_number >= 3` is true, so the expected value would be 4, not 3. I'll switch it to an `&` with a plain "before the third attempt" predicate and wrap the long line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py", "old_string": "        def is_int(fut: tenacity.Future) -> bool:\n            return isinstance(fut.result(), int)\n\n        def r(", "new_string": "        def r("}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py", "old_string": "        # plain callable on the right of a retry_base, through the sync Retrying loop\n        attempts = 0\n\n        def is_third_attempt(retry_state: tenacity.RetryCallState) -> bool:\n            return retry_st
…[536 chars elided]…
bool:\n            return retry_state.attempt_number < 3\n\n        @tenacity.retry(\n            retry=tenacity.retry_if_exception_type(IOError) & before_third_attempt\n        )\n        def flaky() -> int:\n            nonlocal attempts\n            attempts += 1\n            if attempts < 3:\n                raise OSError()\n            return attempts\n\n        self.assertEqual(3, flaky())"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async regression test. It goes just before `test_retry_with_async_result_or`, and it covers a plain callable on each side of an async strategy.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_retry_with_async_result_or(self) -> None:", "new_string": "    @asynctest\n    async def test_retry_with_plain_callable_composition(self) -> None:\n        class CustomException(Exc
…[1231 chars elided]…
before_third_attempt | tasyncio.retry_if_exception(is_exc))\n        )\n        self.assertEqual(\n            3, await run(tasyncio.retry_if_exception(is_exc) & before_third_attempt)\n        )\n        self.assertEqual(\n            3, await run(before_third_attempt & tasyncio.retry_if_exception(is_exc))\n        )\n\n    @asynctest\n    async def test_retry_with_async_result_or(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] I just spotted a bug in the test I wrote. `retry_if_exception` takes a predicate over the exception, not over `RetryCallState`. I'll fix `is_exc` to take the exception.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py", "old_string": "        def is_exc(retry_state: tenacity.RetryCallState) -> bool:\n            assert retry_state.outcome  # help mypy\n            return retry_state.outcome.failed and isinstance(\n                retry_state.outcome.exception(), CustomException\n            )\n\n        def before_third_attempt", "new_string": "        def is_exc(e: BaseException) -> bool:\n            return isinstance(e, CustomException)\n\n        def before_third_attempt"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now the release note, named with 16 random hex characters per the repo convention. Then I'll run the fail-on-base check against the new tests.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8); F=releasenotes/notes/fix-retry-composition-plain-callable-$H.yaml; printf '%s\\n' '---' 'fixes:' '  - |' '    Fix composing a retry strategy with a plain callable using ``|`` or ``&``, in either order, which raised ``AttributeError`` since 8.4.2 instead of producing ``retry_any`` / ``retry_all``. Sync and async retry strategies work again, and the type annota
…[164 chars elided]…
0/scratchpad/pr-work/env-tenacity/bin/python; $PY .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable\" \"tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition\" 2>&1 | tail -60; echo EXIT=$?", "description": "Write release note and run fail-on-base check"}
[tool_result] ---
fixes:
  - |
    Fix composing a retry strategy with a plain callable using ``|`` or ``&``, in either order, which raised ``AttributeError`` since 8.4.2 instead of producing ``retry_any`` / ``retry_all``. Sync and async retry strategies work again, and the type annotations accept plain callables.

               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )

tests/test_asyncio.py:322: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
…[1550 chars elided]…
 'await' expression

tenacity/asyncio/retry.py:74: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable
FAILED tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition
2 failed in 0.06s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
EXIT=0
[assistant] Fail-on-base reports both new tests failing on HEAD, which is the expected direction. But the async failure is my test's bug, not the composition bug: `retry_if_exception` needs an async predicate. I'll make `is_exc` async and run the new tests against the working tree.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py", "old_string": "        def is_exc(e: BaseException) -> bool:\n            return isinstance(e, CustomException)", "new_string": "        async def is_exc(e: BaseException) -> bool:\n            return isinstance(e, CustomException)"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no \"tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable\" \"tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition\"
…[38 chars elided]…
arness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable\" \"tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition\" 2>&1 | grep -E \"^E  |FAILED|GOOD|BAD|passed|failed\" | head -20; echo EXIT=${PIPESTATUS[0]}", "description": "Run new tests and fail-on-base check again"}
[tool_result] ..                                                                       [100%]
2 passed in 0.04s

            return not retry_state.outcome.failed and (
E       AttributeError: 'function' object has no attribute '__ror__'. Did you mean: '__dir__'?
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable
1 failed, 1 passed in 0.05s
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
EXIT=
[assistant] Two results. The sync test fails on HEAD with exactly the reported `AttributeError`. The async test passes on HEAD, which means it doesn't reach the bug path. The skill notes warned about this: an async-only strategy on the left goes through `async_retry_base.__or__`, which was never broken. The regression needs a sync `retry_base` instance on the left, so I'll rewrite the async test around `tenacity.retry_if_exception_type`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py", "old_string": "        class CustomException(Exception):\n            pass\n\n        async def is_exc(e: BaseException) -> bool:\n            return isinstance(e, CustomException)\n\n        def before_third_attempt(retry_state: t
…[58 chars elided]…
_state.attempt_number < 3\n\n        async def run(retry_strategy: tasyncio.RetryBaseT) -> int:", "new_string": "        class CustomException(Exception):\n            pass\n\n        def before_third_attempt(retry_state: tenacity.RetryCallState) -> bool:\n            return retry_state.attempt_number < 3\n\n        async def run(retry_strategy: tenacity.retry_base | tasyncio.RetryBaseT) -> int:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py", "old_string": "        # plain callable on either side of an async strategy, with | and &\n        self.assertEqual(\n            3, await run(tasyncio.retry_if_exception(is_exc) | before_third_attempt)\n        )\n        self.ass
…[527 chars elided]…
 already worked)\n        retry_on_exc = tenacity.retry_if_exception_type(CustomException)\n        self.assertEqual(3, await run(retry_on_exc | before_third_attempt))\n        self.assertEqual(3, await run(before_third_attempt | retry_on_exc))\n        self.assertEqual(3, await run(retry_on_exc & before_third_attempt))\n        self.assertEqual(3, await run(before_third_attempt & retry_on_exc))"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161759-regression-since-8-4-2-composing/dom-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no \"tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable\" \"tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition\"
…[205 chars elided]…
o.py::TestContextManager::test_retry_with_plain_callable_composition\" > /tmp/fob.txt 2>&1; echo EXIT=$?; grep -E \"^E  |^FAILED|passed|failed|GOOD|BAD\" /tmp/fob.txt | head; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tests/test_asyncio.py tests/test_tenacity.py tenacity/retry.py tenacity/asyncio/retry.py | head", "description": "Rerun new tests, fail-on-base check, and line lengths"}
[tool_result] ..                                                                       [100%]
2 passed in 0.02s
EXIT=0
                if not attempt.retry_state.outcome.failed:
E       AttributeError: 'function' object has no attribute '__ror__'. Did you mean: '__dir__'?
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_and_with_plain_callable
FAILED tests/test_asyncio.py::TestContextManager::test_retry_with_plain_callable_composition
2 failed in 0.06s
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
tests/test_asyncio.py: 448: 89
tests/test_tenacity.py: 50: 89
tests/test_tenacity.py: 134: 89
tests/test_tenacity.py: 422: 105
tests/test_tenacity.py: 901: 99
tests/test_tenacity.py: 926: 99
tests/test_tenacity.py: 1370: 89
tests/test_tenacity.py: 1440: 106
tests/test_tenacity.py: 1451: 148
tests/test_tenacity.py: 1503: 92
[assistant] Both new tests now pass on the fix and fail on HEAD with the reported `AttributeError`. One of the over-long lines is mine (`test_asyncio.py:448`), so I'll wrap it, then run the full suite.
[tool_use Bash] {"command": "sed -n 448p tests/test_asyncio.py", "description": "Show the long line in test_asyncio"}
[tool_result]         - retry object can be modified to change its behaviour (useful to patch in tests)
[assistant] That line predates my change, so I'll leave it. Running the full suite now.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ...........s................................................ [ 43%]
........................................................................ [ 94%]
.......                                                                  [100%]
138 passed, 1 skipped, 12 subtests passed in 1.86s
 M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-retry-composition-plain-callable-1d09c70e6f5b4277.yaml
[assistant] Fixed: `retry_if_exception_type(IOError) | my_predicate` now returns a `retry_any` instead of raising, and the same holds for `&` and for the reverse order, in both sync and async code. The full suite passes (138 passed, 1 skipped). I did not run mypy or ruff, since neither is installed in the project's check interpreter.

**Cause:** `retry_base.__or__` and `__and__` always delegated to `other.__ror__` / `other.__rand__`. A plain function has neither, so the call raised `AttributeError: 'function' object has no attribute '__ror__'`. The reverse order worked because Python falls back to the rig
…[1018 chars elided]…
le-1d09c70e6f5b4277.yaml`: the reno note.

**Fail-on-base check:** both new tests fail on HEAD with the `AttributeError` above and pass on the fix. My first async test passed on HEAD because it only used async strategies, which never reach the broken sync operator. I rewrote it to put a sync `retry_base` on the left.

**Choices you may want to review:**
- The async tests cover sync `retry_base` on the left only, because async-only composition was never broken.
- Stop and wait strategies are unchanged. They already build their combinators directly and the report only concerned retry strategies.
