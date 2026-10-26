# trajectory dom-1

final message:
Fixed. `func.statistics` now stays visible through `functools.wraps` wrappers for both sync and async `@retry` functions, and the outer wrapper's `statistics` is the same object as the inner one's. The full suite passes (167 passed, 1 skipped) and `check_changed.py` reports 0 problems.

**Root cause:** `functools.wraps` copies the inner function's `statistics` object onto the outer wrapper once, at decoration time. The inner wrapper then replaced `statistics` with a new dict on every call, so the outer wrapper kept the original empty `{}`.

**Fix** (`tenacity/__init__.py`, `tenacity/asyncio/__init__.py`):
- The function's `statistics` dict is created once and never rebound.
- Each call still gets its own dict, which is a small `_SharedStatistics` subclass. It writes every change through to the shared dict, so `fn.statistics` and `fn.retry.statistics` stay live during a call and per-call isolation is kept.

**Tests:** I added `test_statistics_visible_through_functools_wraps` to `TestDecoratorWrapper` in both `tests/test_tenacity.py` and `tests/test_asyncio.py`. Both failed against the unfixed code with `{} is not {...}` and pass now. I did not edit or weaken any existing test.

**Behaviour changes to note:**
- `fn.retry.statistics` is now the same object as `fn.statistics` (it was the per-call copy's dict before). This matches the existing #614 expectation.
- With concurrent calls, `fn.statistics` shows whichever call wrote last. That was already true before this change.

**Also added:** a reno note at `releasenotes/notes/fix-statistics-functools-wraps-5c2e9a1d7b3f4e80.yaml`. I did not change `doc/source/index.rst`, since the documented behaviour is unchanged.

**Not run:** ruff and mypy are not available in this environment, so the type-ignore comments and typing were checked only by reading.

## events
[tool_use Bash] {"command": "grep -n \"statistics\\|wraps\" tenacity/__init__.py | head -80; ls tests | head -50", "description": "Locate statistics and wraps usage in tenacity"}
[tool_result] 326:    def statistics(self) -> dict[str, t.Any]:
327:        """Return a dictionary of runtime statistics.
336:                     change between major releases as new statistics are
343:                  their own view of statistics they have collected (in the
345:                  statistics from each thread).
347:        if not hasattr(self._local, "statistics"):
348:            self._local.statistics = t.cast("dict[str, t.Any]", {})
349:        return self._local.statistics  # type: ignore
…[512 chars elided]…
["attempt_number"] = 1
390:        self.statistics["idle_for"] = 0
391:        self.statistics["delay_since_first_attempt"] = 0
408:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
467:            self.statistics["idle_for"] += sleep
468:            self.statistics["attempt_number"] += 1
656:    statistics: dict[str, t.Any]
754:        return r.wraps(f)
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "sed -n 350,385p tenacity/__init__.py; grep -n \"wraps\\|statistics\" tenacity/asyncio/__init__.py | head -30; ls .lithify/harness/scripts/; ls tests/test_issue_478.py && sed -n 1,30p tests/test_issue_478.py", "description": "Read wraps implementation and async counterpart"}
[tool_result]     @property
    def iter_state(self) -> IterState:
        if not hasattr(self._local, "iter_state"):
            self._local.iter_state = IterState()
        return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.
        """

        @functools.wraps(
            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefault
…[1662 chars elided]…
Any]:
    @wraps(callable_)
    def wrapper(*a: typing.Any, **kw: typing.Any) -> typing.Any:
        return asyncio.run(callable_(*a, **kw))

    return wrapper


MAX_RETRY_FIX_ATTEMPTS = 2


class TestIssue478(unittest.TestCase):
    def test_issue(self) -> None:
        results = []

        def do_retry(retry_state: RetryCallState) -> bool:
            outcome = retry_state.outcome
            assert outcome
            ex = outcome.exception()
            _subject_: str = retry_state.args[0]
[tool_use Bash] {"command": "sed -n 196,225p tenacity/asyncio/__init__.py; cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; ls releasenotes/notes 2>/dev/null | tail -5; grep -rn \"statistics\" tests/*.py | head -20; sed -n 1,30p .lithify/harness/scripts/run_tests.py | head -30", "description": "Read async wraps, contract skill, and existing statistics tests"}
[tool_result] <persisted-output>
Output too large (31.5KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261023-211551-bug-when-a-retry-decorated-funct-dom-1/1f630dbb-7675-4ce0-ba5c-037292f75385/tool-results/big440tv0.txt

Preview (first 2KB):
                await self.sleep(do)  # type: ignore[misc]
            else:
                raise StopAsyncIteration

    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        wrapped = s
…[671 chars elided]…
elf._local.statistics = copy.statistics
            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]

        # Preserve attributes
        async_wrapped.retry = self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
        async_wrapped.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
---
name: tenacity-change-contract
...
</persisted-output>
[tool_use Bash] {"command": "wc -c .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n \"statistics\" tests/test_tenacity.py tests/test_asyncio.py | head -20; ls releasenote* reno* doc 2>/dev/null | head; ls -d releasenotes/notes 2>/dev/null", "description": "Check skill size, statistics test references, release notes dir"}
[tool_result]    27433 .lithify/harness/skills/tenacity-change-contract/SKILL.md
tests/test_asyncio.py:291:        self.assertEqual(2, retrying.statistics["attempt_number"])
tests/test_asyncio.py:501:        - statistics contains the value for the latest function run
tests/test_asyncio.py:503:        - retry object statistics are synced with function statistics
tests/test_asyncio.py:517:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:521:            _retryable_coroutine_with
…[1057 chars elided]…
ception_message_delay.statistics
tests/test_tenacity.py:1392:            s = _retryable_test_if_not_exception_message_message.statistics
tests/test_tenacity.py:1454:        - statistics contains the value for the latest function run
tests/test_tenacity.py:1456:        - retry object statistics are synced with function statistics
tests/test_tenacity.py:1467:        self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
reno.yaml

doc:
source

releasenotes:
notes
releasenotes/notes
[tool_use Bash] {"command": "sed -n 1440,1470p tests/test_tenacity.py; sed -n 495,555p tests/test_asyncio.py; ls releasenotes/notes | tail -3; sed -n 1,60p .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Read existing statistics sync tests and skill head"}
[tool_result]         class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
        )
        h = retrying.wraps(Hello())
        self.assertEqual(h(), "Hello")

    def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.

        - statistics contains the value for the latest function run
        - re
…[7677 chars elided]…
` matches). `copy()` always starts with a fresh `_local`, so
  each call gets a new dict.
- `functools.wraps` (`WRAPPER_UPDATES`) copies the inner function's `__dict__` into an outer
  wrapper ONCE, at decoration. An attribute the inner wrapper later rebinds is stale on the
  outer one. Only objects that stay the same and are mutated in place stay visible there.
  `fn.retry` (the original `Retrying`) and `fn.retry_with` are never rebound, so
  `mock.patch.object(outer.retry, ...)` already works.
[tool_use Bash] {"command": "sed -n 60,140p .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Read rest of contract skill section 1a1 and onward"}
[tool_result]   `mock.patch.object(outer.retry, ...)` already works.
- INVARIANTS a change here must keep, or name as changed in the final message and reno note:
  per-thread statistics (the `statistics` property docstring says each thread has its own
  view); per-call isolation (a recursive or concurrent call of the same function must not
  `begin()`/`clear()` a dict that another running call is updating); `fn.retry.statistics is
  fn.statistics` after a call (#614); `enabled=False` returns before `self.copy
…[5503 chars elided]…
plice members only from
  operands whose type is exactly the container (`type(x) is retry_any`), not `isinstance`.
- Guarding tests: `tests/test_asyncio.py::TestContextManager::test_retry_with_async_result_or`
  (and `_ror`, `_and`, `_rand`)
  mix sync and async strategies. Run them by node id after touching either operator set.
- Sync composition tests live in `tests/test_tenacity.py::TestRetryConditions`
  (`test_retry_or`, `test_retry_and`, `test_retry_or_with_plain_function`, …); there is no
[tool_use Bash] {"command": "grep -n \"class TestDecoratorWrapper\\|^import\\|^from\\|_retryable_test_with_stop\" tests/test_tenacity.py | head -30; grep -n \"class TestDecoratorWrapper\" -A3 tests/test_asyncio.py; ls <work>/env-tenacity/bin/python && echo PYOK", "description": "Find test classes, imports and project python"}
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
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
1128:def _retryable_test_with_stop(thing: typing.Any) -> typing.Any:
1249:class TestDecoratorWrapper(unitte
…[669 chars elided]…
      _retryable_test_with_stop.retry.statistics, expected_stats
1608:        result = _retryable_test_with_stop.retry_with(
496:class TestDecoratorWrapper(unittest.TestCase):
497-    @asynctest
498-    async def test_retry_function_attributes(self) -> None:
499-        """Test that the wrapped function attributes are exposed as intended.
<work>/env-tenacity/bin/python
PYOK
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py", "old_string": "class TestDecoratorWrapper(unittest.TestCase):\n", "new_string": "class TestDecoratorWrapper(unittest.TestCase):\n    def test_statistics_visible_through_functools_wraps(self) -> None:\n        def timed(f: typing.C
…[337 chars elided]…
           stop=tenacity.stop_after_attempt(3),\n        )\n        def inner() -> typing.Optional[int]:\n            return None if counter.next() < 3 else 3\n\n        counter = itertools.count(1)\n        outer = timed(inner)\n\n        self.assertEqual(outer(), 3)\n        self.assertIs(outer.statistics, inner.statistics)\n        self.assertEqual(outer.statistics[\"attempt_number\"], 3)\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py", "old_string": "        def inner() -> typing.Optional[int]:\n            return None if counter.next() < 3 else 3\n\n        counter = itertools.count(1)\n        outer = timed(inner)", "new_string": "        def inner() -> typing.Optional[int]:\n            calls.append(1)\n            return None if len(calls) < 3 else 3\n\n        calls: typing.List[int] = []\n        outer = timed(inner)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py", "old_string": "        def timed(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:\n            @functools.wraps(f)", "new_string": "        def timed(f: typing.Any) -> typing.Any:\n            @functools.wraps(f)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the `functools` import, and the async twin test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py", "old_string": "import datetime\nimport logging", "new_string": "import datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_asyncio.py", "old_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n", "new_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n    async def test_statistics_visible_through_functools_wraps(self) ->
…[394 chars elided]…
    )\n        async def inner() -> typing.Optional[int]:\n            calls.append(1)\n            return None if len(calls) < 3 else 3\n\n        calls: typing.List[int] = []\n        outer = timed(inner)\n\n        self.assertEqual(await outer(), 3)\n        self.assertIs(outer.statistics, inner.statistics)\n        self.assertEqual(outer.statistics[\"attempt_number\"], 3)\n\n    @asynctest\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] Both tests are written. Running them against the unfixed code first.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
        def timed(f: typing.Any) -> typing.Any:
            @functools.wraps(f)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                return f(*args, **kwargs)
    
            return wrapper
    
        @retry(
            retry=tenacity.retry_if_result(lambda r: r is None),
            stop=tenacity.stop_after_attempt(3),
        )
        def inner() -> typing.Optional[int]:
            calls.append(1)
            return None if len(calls) < 3
…[773 chars elided]…
is not defined. Did you forget to import 'typing'

tests/test_asyncio.py:499: NameError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps
============================== 2 failed in 0.08s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The sync test fails on the bug itself (`{}` vs the real stats). The async one hit a NameError, so I'll check the module's imports.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_asyncio.py | grep -n \"import\"", "description": "Check test_asyncio imports"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
[tool_use Bash] {"command": "f=tests/test_asyncio.py && python3 - \"$f\" <<'EOF'\nimport sys\np = sys.argv[1]\ns = open(p).read()\nstart = s.index(\"class TestDecoratorWrapper\")\nhead, tail = s[:start], s[start:]\ntail = tail.replace(\"typing.Any\", \"Any\").replace(\"typing.Optional[int]\", \"Optional[int]\").replace(\"typing.List[int]\", \"List[int]\")\nhead = head.replace(\"from typing import Any, TypeVar\", \"from typing import Any, List, Optional, TypeVar\")\nopen(p, \"w\").write(head + tail)\nEOF\ngrep -n \"typing\" $f | head", "description": "Replace typing.* references with imported names in async tests"}
[tool_result] 20:from typing import Any, List, Optional, TypeVar
[assistant] Now re-running the async test to confirm it fails for the bug itself, not the import.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/red2.txt 2>&1; echo \"exit=$?\"; grep -n \"Error\\|passed\\|failed\" /tmp/red2.txt | tail -8", "description": "Re-run async regression test against unfixed code"}
[tool_result] exit=1
35:E       AssertionError: {} is not {'start_time': 245721.562294791, 'attempt_number': 3, 'idle_for': 0.0, 'delay_since_first_attempt': 7.316601113416255e-05}
37:tests/test_asyncio.py:518: AssertionError
40:============================== 1 failed in 0.03s ===============================
[assistant] Both new tests fail on the bug (`{}` vs the real stats), so the red step is done. Now the fix. `functools.wraps` copies the `statistics` dict object onto the outer wrapper once, at decoration time. The inner wrapper rebinds `statistics` on every call, so the outer copy goes stale. The fix keeps one dict object for the wrapper's lifetime and updates it in place. Each call still uses its own copy, so per-call isolation holds.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            wrapped_f.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)", "new_st
…[137 chars elided]…
    try:\n                return copy(f, *args, **kw)\n            finally:\n                # Update in place, never rebind: functools.wraps copies this dict\n                # object onto outer wrappers once, at decoration time.\n                wrapped_f.statistics.clear()  # type: ignore[attr-defined]\n                wrapped_f.statistics.update(copy.statistics)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return await copy(fn, *ar
…[235 chars elided]…
n, *args, **kwargs)  # type: ignore[type-var]\n            finally:\n                # Update in place, never rebind: functools.wraps copies this dict\n                # object onto outer wrappers once, at decoration time.\n                async_wrapped.statistics.clear()  # type: ignore[attr-defined]\n                async_wrapped.statistics.update(copy.statistics)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now the regression tests should go green, then the full suite and the lint stand-in.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/chk.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/chk.txt", "description": "Run new tests green, full suite, and changed-file checks"}
[tool_result] exit=0

============================== 2 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=1
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatisticsKeys::test_delay_since_first_attempt_available_on_first_attempt
FAILED tests/test_tenacity.py::TestStatistics::test_retry_object_statistics_during_execution
========= 2 failed, 165 passed, 1 skipped, 12 subtests passed in 1.87s 
…[110 chars elided]…
ncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL tenacity/__init__.py:379: line is 90 columns (max 88)
FAIL tenacity/asyncio/__init__.py:213: line is 91 columns (max 88)
FAIL tenacity/asyncio/__init__.py:220: line is 94 columns (max 88)
FAIL tests/test_asyncio.py:510: nested async def needs a blank line before it
FAIL tests/test_tenacity.py:1263: nested def needs a blank line before it
FAIL: 5 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Two existing tests now fail, so I need to see whether my change broke them or they depend on the old behaviour.
[tool_use Bash] {"command": "grep -n \"^E \\|^tests/.*Error\\|^>\" /tmp/full.txt | head -30; grep -n \"def test_retry_object_statistics_during_execution\\|def test_delay_since_first_attempt_available_on_first_attempt\" -A22 tests/test_tenacity.py | head -70", "description": "Show failure details and the two failing tests"}
[tool_result] 32:>       attempts.append(_foobar.retry.statistics["attempt_number"])
34:E       KeyError: 'attempt_number'
36:tests/test_tenacity.py:1924: KeyError
1518:    def test_delay_since_first_attempt_available_on_first_attempt(self) -> None:
1519-        """delay_since_first_attempt should be in statistics from the start."""
1520-
1521-        @retry(
1522-            stop=tenacity.stop_after_attempt(3),
1523-            retry=tenacity.retry_if_result(lambda x: x is None),
1524-        )
1525-        
…[1070 chars elided]…
1922-        )
1923-        def _foobar() -> int:
1924-            attempts.append(_foobar.retry.statistics["attempt_number"])
1925-            if len(attempts) < 3:
1926-                raise ValueError("retry")
1927-            return 42
1928-
1929-        _foobar()
1930-        self.assertEqual(attempts, [1, 2, 3])
1931-
1932-
1933-class TestRetryErrorCallback(unittest.TestCase):
1934-    def setUp(self) -> None:
1935-        self._attempt_number = 0
1936-        self._callback_called = False
[assistant] Both failing tests read `fn.statistics` / `fn.retry.statistics` **during** the call, and that live view is the contract. My end-of-call copy broke it. Fix: each call keeps its own dict, which writes through to the shared one on every mutation. That keeps live reads, identity, and per-call isolation.
[tool_use Bash] {"command": "grep -n \"^class \\|^import\\|^from\" tenacity/__init__.py | head -30; grep -n \"^from\\|^import\" tenacity/asyncio/__init__.py", "description": "List classes and imports in tenacity modules"}
[tool_result] 18:import dataclasses
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
43:from .retry import (
61:from .stop import (
72:from .wait 
…[43 chars elided]…
xponential as wait_full_jitter
112:class IterState:
127:class TryAgain(Exception):
134:class DoAttempt:
138:class DoSleep(float):
142:class BaseAction:
164:class RetryAction(BaseAction):
179:class RetryError(Exception):
203:class AttemptManager:
237:class BaseRetrying(ABC):
513:class Retrying(BaseRetrying):
541:class Future(futures.Future[t.Any]):
566:class RetryCallState:
18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
37:from .retry import (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            self._local.statistics = wrapped_f.statistics  # type: ignore[attr-defined]\n            try:\n                return copy(f, *args, **kw)\n            finally:\n           
…[198 chars elided]…
ignore[attr-defined]\n                wrapped_f.statistics.update(copy.statistics)  # type: ignore[attr-defined]", "new_string": "            copy = self.copy()\n            copy._local.statistics = _SharedStatistics(wrapped_f.statistics)  # type: ignore[attr-defined]\n            self._local.statistics = wrapped_f.statistics  # type: ignore[attr-defined]\n            return copy(f, *args, **kw)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            copy._local.statistics = _SharedStatistics(wrapped_f.statistics)  # type: ignore[attr-defined]\n            self._local.statistics = wrapped_f.statistics  # type: ignore[attr-defined]\n            return copy(f, *args, **kw)", "new_string": "            copy = self.copy()\n            shared = wrapped_f.statistics  # type: ignore[attr-defined]\n            copy._local.statistics = _SharedStatistics(shared)\n            self._local.statistics = shared\n            return copy(f, *args, **kw)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py", "old_string": "class BaseRetrying(ABC):\n", "new_string": "class _SharedStatistics(dict):  # type: ignore[type-arg]\n    \"\"\"Statistics of one call that also write through to the decorated function's dict.\n\n    ``functools.wraps
…[227 chars elided]…
ared one.\n    \"\"\"\n\n    def __init__(self, shared: dict[str, t.Any]) -> None:\n        super().__init__()\n        self._shared = shared\n\n    def __setitem__(self, key: str, value: t.Any) -> None:\n        super().__setitem__(key, value)\n        self._shared[key] = value\n\n    def clear(self) -> None:\n        super().clear()\n        self._shared.clear()\n\n\nclass BaseRetrying(ABC):\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py", "old_string": "class _SharedStatistics(dict):  # type: ignore[type-arg]\n    \"\"\"Statistics of one call that also write through to the decorated function's dict.\n\n    ``functools.wraps`` copies the function's ``statistics`` obje
…[226 chars elided]…
s _SharedStatistics(dict[str, t.Any]):\n    \"\"\"Statistics of one call, mirrored into the decorated function's shared dict.\n\n    ``functools.wraps`` copies the function's ``statistics`` object onto outer wrappers\n    once, at decoration time, so that object must never be rebound. Each call keeps its\n    own dict (per-call isolation) and mirrors every change into the shared one.\n    \"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async wrapper, which needs the same change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            self._local.statistics = async_wrapped.statistics  # type: ignore[attr-defined]\n            try:\n                return await copy(fn, *args, **kwargs)  # type: ig
…[281 chars elided]…
        async_wrapped.statistics.update(copy.statistics)  # type: ignore[attr-defined]", "new_string": "            copy = self.copy()\n            shared = async_wrapped.statistics  # type: ignore[attr-defined]\n            copy._local.statistics = _SharedStatistics(shared)\n            self._local.statistics = shared\n            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 23,36p tenacity/asyncio/__init__.py", "description": "View tenacity.asyncio import block"}
[tool_result] from tenacity import (
    AttemptManager,
    BaseRetrying,
    DoAttempt,
    DoSleep,
    RetryCallState,
    RetryError,
    _RetryDecorated,
    _utils,
    after_nothing,
    before_nothing,
)

# Import all built-in retry strategies for easier usage.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py", "old_string": "    RetryError,\n    _RetryDecorated,\n    _utils,", "new_string": "    RetryError,\n    _RetryDecorated,\n    _SharedStatistics,\n    _utils,"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -2 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/chk.txt 2>&1; echo \"exit=$?\"; cat /tmp/chk.txt | tail -12", "description": "Re-run new tests, full suite, and changed-file checks"}
[tool_result] exit=0
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
============== 167 passed, 1 skipped, 12 subtests passed in 1.82s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=1
changed: tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL tests/test_asyncio.py:510: nested async def needs a blank line before it
FAIL tests/test_tenacity.py:1263: nested def needs a blank line before it
FAIL: 2 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Full suite is green (167 passed, 1 skipped). The remaining two items are lint findings from the changed test files, so I'll look at those lines.
[tool_use Bash] {"command": "sed -n 1261,1264p tests/test_tenacity.py; echo ---; sed -n 507,511p tests/test_asyncio.py", "description": "View lines flagged by the lint check"}
[tool_result]             stop=tenacity.stop_after_attempt(3),
        )
        def inner() -> typing.Optional[int]:
            calls.append(1)
---
            retry=tenacity.retry_if_result(lambda r: r is None),
            stop=tenacity.stop_after_attempt(3),
        )
        async def inner() -> Optional[int]:
            calls.append(1)
[assistant] The check wants a blank line between the decorator and the nested `def`/`async def` in both test files.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py", "old_string": "        )\n        def inner() -> typing.Optional[int]:\n            calls.append(1)", "new_string": "        )\n\n        def inner() -> typing.Optional[int]:\n            calls.append(1)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_asyncio.py", "old_string": "        )\n        async def inner() -> Optional[int]:\n            calls.append(1)", "new_string": "        )\n\n        async def inner() -> Optional[int]:\n            calls.append(1)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] Lint findings addressed. Re-running the full suite and the checker, and reading an existing reno note to match the format the contract asks for.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -2 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/chk.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/chk.txt; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; grep -n \"functools\\|wraps\\|statistics\" doc/source/index.rst | head", "description": "Re-run full suite, checker, and read reno note example"}
[tool_result] exit=0
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
changed: tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
367:You can access the statistics about the retry made over a function by using the
368:`statistics` attribute attached to the function:
381:    print(raise_my_exception.statistics)
576:    print(raise_my_exception.statistics)
598:statistics should be read from the function `statistics` attribute.
614:    print(raise_my_exception.statistics)
656:Tenacity allows you to retry a code block without the need to wraps it in an
741:— the decorator wraps the function call itself, which for generators simply
[assistant] Suite and checker both pass. The contract asks for a reno note on any user-visible tenacity change, so I'll add one in the repo's format.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/releasenotes/notes/fix-statistics-functools-wraps-5c2e9a1d7b3f4e80.yaml", "content": "---\nfixes:\n  - |\n    ``func.statistics`` is now visible through another decorator that uses\n    ``functools.wraps`` on a function decorated with ``@retry``, for both sync and\n    async functions. Previously the outer wrapper's ``statistics`` stayed ``{}``.\n    The outer wrapper's ``statistics`` is now the same object as the inner one's.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/dom-1/releasenotes/notes/fix-statistics-functools-wraps-5c2e9a1d7b3f4e80.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "git status --short && git diff -- tenacity/ | head -120", "description": "Show changed files and tenacity diff"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-statistics-functools-wraps-5c2e9a1d7b3f4e80.yaml
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index e9532fc..4c35f96 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -234,6 +234,27 @@ class AttemptManager:
         return self.__exit__(exc_type, exc_value, traceback)
 
 
+class _SharedStatistics(dict[str, t.Any]):
+    """Statistics of on
…[1967 chars elided]…
ultiple times in the same stack
             copy = self.copy()
-            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
-            self._local.statistics = copy.statistics
+            shared = async_wrapped.statistics  # type: ignore[attr-defined]
+            copy._local.statistics = _SharedStatistics(shared)
+            self._local.statistics = shared
             return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
 
         # Preserve attributes
[assistant] Fixed. `func.statistics` now stays visible through `functools.wraps` wrappers for both sync and async `@retry` functions, and the outer wrapper's `statistics` is the same object as the inner one's. The full suite passes (167 passed, 1 skipped) and `check_changed.py` reports 0 problems.

**Root cause:** `functools.wraps` copies the inner function's `statistics` object onto the outer wrapper once, at decoration time. The inner wrapper then replaced `statistics` with a new dict on every call, so the outer wrapper kept the original empty `{}`.

**Fix** (`tenacity/__init__.py`, `tenacity/asyncio/__
…[623 chars elided]…
:**
- `fn.retry.statistics` is now the same object as `fn.statistics` (it was the per-call copy's dict before). This matches the existing #614 expectation.
- With concurrent calls, `fn.statistics` shows whichever call wrote last. That was already true before this change.

**Also added:** a reno note at `releasenotes/notes/fix-statistics-functools-wraps-5c2e9a1d7b3f4e80.yaml`. I did not change `doc/source/index.rst`, since the documented behaviour is unchanged.

**Not run:** ruff and mypy are not available in this environment, so the type-ignore comments and typing were checked only by reading.
