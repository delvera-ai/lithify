# trajectory base-1

final message:
The outer wrapper's `statistics` is now the same object as the inner one's, for both sync and async functions. The full suite passes (167 passed, 1 skipped), and the change checker passes.

**Cause:** `functools.wraps` copies the inner function's `__dict__` into the outer wrapper once, at decoration time. The outer wrapper kept the initial `{}`, and each call only rebound the inner wrapper's `statistics`.

**Fix** (`tenacity/__init__.py` and `tenacity/asyncio/__init__.py`): each decorated function now keeps one stable statistics dict, and every call writes into that dict instead of replacing it.

**Tests:**
- `tests/test_tenacity.py::TestStatistics::test_statistics_visible_through_functools_wraps` and `tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps` both failed first with the outer `statistics` as `{}`, then passed after the fix.
- I added a reno note, `releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml`. PyYAML is unavailable here, so the note's YAML was not parsed.

**Tradeoff to decide on:** `func.statistics` is now shared across threads. Before, each concurrent call had its own dict, and the docs say statistics are per-thread. Calls running at the same time on one decorated function now write into the same dict. The retry logic doesn't read these values, so control flow is unaffected, but the reported numbers can interleave. Keeping per-call dicts and still matching the outer wrapper is not possible with `functools.wraps`, since it copies a snapshot. If per-thread values matter to you, the alternative is to give up the identity requirement, so I left the choice to you. The existing tests don't cover concurrent calls, so nothing failed on this.

**Not run:** ruff and mypy (the checker reports them as unavailable here). I did not commit.

## events
[tool_use Bash] {"command": "rtk git status --short | head; rtk grep -n \"statistics\" tenacity/__init__.py tenacity/asyncio/__init__.py | head -60; ls .lithify/harness/scripts/", "description": "Check status and locate statistics code"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
check_changed.py
run_tests.py
[tool_use Bash] {"command": "git status --short | head; grep -n \"statistics\\|wraps\" tenacity/__init__.py tenacity/asyncio/__init__.py; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Check status and locate statistics code"}
[tool_result] tenacity/asyncio/__init__.py:153:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:200:    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
tenacity/asyncio/__init__.py:201:        wrapped = super().wraps(fn)
tenacity/asyncio/__init__.py:204:        @functools.wraps(
tenacity/asyncio/__init__.py:213:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:214:
…[1797 chars elided]…
e_start
tenacity/__init__.py:467:            self.statistics["idle_for"] += sleep
tenacity/__init__.py:468:            self.statistics["attempt_number"] += 1
tenacity/__init__.py:656:    statistics: dict[str, t.Any]
tenacity/__init__.py:754:        return r.wraps(f)
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "sed -n 355,385p tenacity/__init__.py; echo ----; sed -n 198,225p tenacity/asyncio/__init__.py", "description": "Read sync and async wraps implementations"}
[tool_result]         return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.
        """

        @functools.wraps(
            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:
            if not self.enabled:
                return f(*args, **kw)
       
…[1534 chars elided]…
copy.statistics  # type: ignore[attr-defined]
            self._local.statistics = copy.statistics
            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]

        # Preserve attributes
        async_wrapped.retry = self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
        async_wrapped.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
[tool_use Bash] {"command": "sed -n 300,330p tenacity/__init__.py; sed -n 380,400p tenacity/__init__.py; grep -rn \"statistics\" tests/ | head -40; cat .lithify/harness/memory.md | head -5; ls tests | head -50", "description": "Read copy, statistics property, and related tests"}
[tool_result]         )

    def __getstate__(self) -> dict[str, t.Any]:
        # Exclude threading.local which cannot be pickled
        return {k: v for k, v in self.__dict__.items() if k != "_local"}

    def __setstate__(self, state: dict[str, t.Any]) -> None:
        self.__dict__.update(state)
        self._local = threading.local()

    def __str__(self) -> str:
        return self._name if self._name is not None else "<unknown>"

    def __repr__(self) -> str:
        return (
            f"<{self.__
…[5147 chars elided]…
at func.retry.statistics is accessible during execution."""
tests/test_tenacity.py:1900:            attempts.append(_foobar.retry.statistics["attempt_number"])
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "sed -n 326,349p tenacity/__init__.py; grep -n \"def copy\" -A30 tenacity/__init__.py | grep -n \"local\\|copy(\" ; sed -n 1890,1915p tests/test_tenacity.py; sed -n 1520,1540p tests/test_tenacity.py", "description": "Read docs and copy implementation"}
[tool_result]     def statistics(self) -> dict[str, t.Any]:
        """Return a dictionary of runtime statistics.

        This dictionary will be empty when the controller has never been
        ran. When it is running or has ran previously it should have (but
        may not) have useful and/or informational keys and values when
        running is underway and/or completed.

        .. warning:: The keys in this dictionary **should** be somewhat
                     stable (not changing), but their existenc
…[1934 chars elided]…
enabled=False, .retry, .retry_with, .statistics are still available."""

        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
        def my_func() -> str:
            return "ok"

        assert hasattr(my_func, "retry")
        assert hasattr(my_func, "retry_with")
        assert hasattr(my_func, "statistics")
        assert my_func() == "ok"

    def test_enabled_false_via_retry_with(self) -> None:
        """retry_with(enabled=False) disables retrying."""
        call_count = 0
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; ls doc/source/ 2>/dev/null | head; ls releasenotes/notes 2>/dev/null | tail -3", "description": "Read the tenacity change contract skill"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, the `enabled` switch, which exception escapes on give-up (`TryAgain`, `reraise=True`, `RetryError.reraise()`, `retry_error_cls`/`retry_error_ca
…[23525 chars elided]…
`<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
  annotated (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
api.rst
changelog.rst
conf.py
index.rst
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 1,30p tests/test_tenacity.py | grep -n \"import\"; sed -n 1850,1862p tests/test_tenacity.py; echo ----; grep -n \"^import\\|^from\\|asynctest\\|^class \" tests/test_asyncio.py | head -30; sed -n 495,530p tests/test_asyncio.py; echo ----; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Read test conventions and an existing reno note"}
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
        def _mock_fn() -> None:
            calls.append("x")

        self.assertRaises(tenacity.RetryError, _mock_fn)
        self.assertEqual(2, len(calls))


class TestStatistics(unittest.TestCase):
    def test_stats(self
…[1770 chars elided]…
pected_stats,
        )
        self.assertEqual(
            _retryable_coroutine_with_2_attempts.retry.statistics,
            expected_stats,
        )

        with mock.patch.object(
            _retryable_coroutine_with_2_attempts.retry,
            "stop",
            tenacity.stop_after_attempt(1),
        ):
            try:
----
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[assistant] Root cause: `functools.wraps` copies the outer function's `__dict__` at decoration time, so the outer wrapper keeps the initial `{}` object. Each call later rebinds only the inner wrapper's `statistics`. I'll write the regression tests first and run them red.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "class TestStatistics(unittest.TestCase):\n    def test_stats(self) -> None:", "new_string": "class TestStatistics(unittest.TestCase):\n    def test_statistics_visible_through_functools_wraps(self) -> None:\n       
…[312 chars elided]…
ueError(\"retry\")\n            return 42\n\n        @functools.wraps(_inner)\n        def _timed(*args: typing.Any, **kwargs: typing.Any) -> int:\n            return _inner(*args, **kwargs)\n\n        self.assertEqual(42, _timed())\n        self.assertIs(_inner.statistics, _timed.statistics)\n        self.assertEqual(2, _timed.statistics[\"attempt_number\"])\n\n    def test_stats(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "import contextlib\nimport datetime\nimport logging", "new_string": "import contextlib\nimport datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n    async def test_retry_function_attributes(self) -> None:", "new_string": "class TestDecoratorWrapper(unittest.TestCase):\n    @asynctest\n    async 
…[438 chars elided]…
rn 42\n\n        @wraps(_inner)\n        async def _timed(*args: Any, **kwargs: Any) -> int:\n            return await _inner(*args, **kwargs)\n\n        self.assertEqual(42, await _timed())\n        self.assertIs(_inner.statistics, _timed.statistics)\n        self.assertEqual(2, _timed.statistics[\"attempt_number\"])\n\n    @asynctest\n    async def test_retry_function_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,80p .lithify/harness/scripts/run_tests.py | grep -n \"argparse\\|add_argument\\|python\\|usage\" | head; <work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestStatistics::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red1.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] 1:#!/usr/bin/env python3
9:Usage (from the repo root, with the project python from memory.md):
10:    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
43:            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
exit=1
    
        self.assertEqual(42, _timed())
>       self.assertIs(_inner.statistics, _timed.statistics)
E       AssertionError: {'start_time': 245492.90931775, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt
…[1085 chars elided]…
_first_attempt': 1.1416006600484252e-05} is not {}

tests/test_asyncio.py:517: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatistics::test_statistics_visible_through_functools_wraps
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps
============================== 2 failed in 0.14s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail for the reported reason: the outer wrapper's `statistics` is the stale `{}`. Now the fix: the decorated function keeps one stable statistics dict, and each call's copy writes into it instead of rebinding the attribute.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "            copy = self.copy()\n            wrapped_f.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return copy(f, *args, **kw)", "new_s
…[16 chars elided]…
     # Reuse the same dict on every call, never rebind it: functools.wraps\n            # copies the attribute into outer wrappers at decoration time.\n            statistics = wrapped_f.statistics  # type: ignore[attr-defined]\n            copy = self.copy()\n            copy._local.statistics = statistics\n            self._local.statistics = statistics\n            return copy(f, *args, **kw)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return await copy(fn, *a
…[106 chars elided]…
 never rebind it: functools.wraps\n            # copies the attribute into outer wrappers at decoration time.\n            statistics = async_wrapped.statistics  # type: ignore[attr-defined]\n            copy = self.copy()\n            copy._local.statistics = statistics\n            self._local.statistics = statistics\n            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now the targeted tests, then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestStatistics::test_statistics_visible_through_functools_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_visible_through_functools_wraps > /tmp/green1.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green1.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/full.txt", "description": "Run new tests green, then full suite"}
[tool_result] exit=0

============================== 2 passed in 0.03s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
tests/test_tenacity.py::TestMockingSleep::test_decorated_retry_with PASSED [ 94%]
tests/test_tenacity.py::TestPickle::test_retry_strategies_picklable PASSED [ 94%]
tests/test_tenacity.py::TestPickle::test_retrying_picklable PASSED       [ 95%]
tests/test_tenacity.py::TestPickle::test_retrying_picklable_after_run PASSED [ 95%]
tests/test_tenacity.py::Te
…[173 chars elided]…
ado::test_repr PASSED                     [ 97%]
tests/test_tornado.py::TestTornado::test_retry PASSED                    [ 98%]
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 167 passed, 1 skipped, 12 subtests passed in 2.15s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Targeted tests are green and the full suite passes (167 passed, 1 skipped). The tenacity contract also requires a reno note for a user-visible fix, so I'll add one and then run the change checker.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml", "content": "---\nfixes:\n  - |\n    ``statistics`` is now visible through decorators that wrap a ``@retry``-decorated\n    function with ``functools.wraps``. Previously the outer wrapper's ``statistics``\n    stayed an empty ``{}``. It is now the same dict as the inner function's\n    ``statistics``, for both sync and async functions.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt; git status --short", "description": "Run change checker and list modified files"}
[tool_result] exit=1
changed: releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL tests/test_asyncio.py:506: nested async def needs a blank line before it
FAIL tests/test_tenacity.py:1867: nested def needs a blank line before it
FAIL: 2 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml
[assistant] The checker flags two nested defs that need a blank line before them. Let me look at those lines.
[tool_use Bash] {"command": "sed -n 1863,1868p tests/test_tenacity.py; echo ----; sed -n 502,507p tests/test_asyncio.py", "description": "View flagged lines around nested defs"}
[tool_result]             stop=tenacity.stop_after_attempt(2),
            retry=tenacity.retry_if_exception_type(ValueError),
            reraise=True,
        )
        def _inner() -> int:
            calls.append(1)
----
            stop=tenacity.stop_after_attempt(2),
            retry=tenacity.retry_if_exception_type(ValueError),
            reraise=True,
        )
        async def _inner() -> int:
            calls.append(1)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "            reraise=True,\n        )\n        def _inner() -> int:\n            calls.append(1)\n            if len(calls) < 2:\n                raise ValueError(\"retry\")\n            return 42\n\n        @functools.wraps(_inner)", "new_string": "            reraise=True,\n        )\n\n        def _inner() -> int:\n            calls.append(1)\n            if len(calls) < 2:\n                raise ValueError(\"retry\")\n            return 42\n\n        @functools.wraps(_inner)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "            reraise=True,\n        )\n        async def _inner() -> int:", "new_string": "            reraise=True,\n        )\n\n        async def _inner() -> int:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-211551-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/check2.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full2.txt", "description": "Re-run change checker and full suite"}
[tool_result] exit=0
changed: releasenotes/notes/functools-wraps-statistics-3b9e2d7a41c08f16.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
exit=0
============== 167 passed, 1 skipped, 12 subtests passed in 1.88s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The outer wrapper's `statistics` is now the same object as the inner one's, for both sync and async functions. The full suite passes (167 passed, 1 skipped), and the change checker passes.

**Cause:** `functools.wraps` copies the inner function's `__dict__` into the outer wrapper once, at decoration time. The outer wrapper kept the initial `{}`, and each call only rebound the inner wrapper's `statistics`.

**Fix** (`tenacity/__init__.py` and `tenacity/asyncio/__init__.py`): each decorated function now keeps one stable statistics dict, and every call writes into that dict instead of replacing i
…[632 chars elided]…
 same time on one decorated function now write into the same dict. The retry logic doesn't read these values, so control flow is unaffected, but the reported numbers can interleave. Keeping per-call dicts and still matching the outer wrapper is not possible with `functools.wraps`, since it copies a snapshot. If per-thread values matter to you, the alternative is to give up the identity requirement, so I left the choice to you. The existing tests don't cover concurrent calls, so nothing failed on this.

**Not run:** ruff and mypy (the checker reports them as unavailable here). I did not commit.
