# trajectory base-1

final message:
`delay_since_first_attempt` is now set to `0` at the start of every run, so reading it during the first attempt no longer raises `KeyError`. The full suite passes (137 passed, 1 skipped).

- **Fix:** `BaseRetrying.begin()` in `tenacity/__init__.py` now initialises the key alongside `start_time`, `attempt_number` and `idle_for`. `AsyncRetrying` inherits `begin()`, so the asyncio path is covered by the same line.
- **Regression tests:** one sync test in `tests/test_tenacity.py` (`TestStatistics`) and one async test in `tests/test_asyncio.py` (`TestContextManager`). Each reads the key inside the first attempt and asserts it is `0`. I added `import contextlib` to `test_asyncio.py` for this. With the fix line removed, both tests fail. They fail with an `AssertionError` rather than the `KeyError` itself, because the attempt context manager catches the `KeyError` and treats it as a retryable failure.
- **Release note:** `releasenotes/notes/fix-delay-since-first-attempt-b041f55c58c9d01b.yaml`, a `fixes:` entry describing the old and new behaviour.

mypy and ruff are not installed in the project's check interpreter, so I didn't run them. I annotated the new test code by inspection and wrapped long lines to match the formatter. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" --include='*.py' --include='*.rst' --include='*.yaml' . | head -50; cat memory.md 2>/dev/null | head -20", "description": "Find delay_since_first_attempt references"}
[tool_result] tests/test_asyncio.py:428:            "delay_since_first_attempt": mock.ANY,
tests/test_asyncio.py:453:                    "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:57:    delay_since_first_attempt: typing.Any,
tests/test_tenacity.py:66:        previous_attempt_number is _unset or delay_since_first_attempt is _unset
tests/test_tenacity.py:72:            delay_since_first_attempt=delay_since_first_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay
…[227 chars elided]…
nce_first_attempt = 0.1
tests/test_after.py:35:            self.previous_attempt_number, delay_since_first_attempt
tests/test_after.py:72:        delay_since_first_attempt = 0.1
tests/test_after.py:75:            self.previous_attempt_number, delay_since_first_attempt
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "offset": 300, "limit": 120}
[tool_result] 300	        may not) have useful and/or informational keys and values when
301	        running is underway and/or completed.
302	
303	        .. warning:: The keys in this dictionary **should** be somewhat
304	                     stable (not changing), but their existence **may**
305	                     change between major releases as new statistics are
306	                     gathered or removed so before accessing keys ensure that
307	                     they actually exist and handle whe
…[4497 chars elided]…
elf._add_action_func(self._run_stop)
410	        self._add_action_func(self._post_stop_check_actions)
411	
412	    def _post_stop_check_actions(self, retry_state: "RetryCallState") -> None:
413	        if self.iter_state.stop_run_result:
414	            if self.retry_error_callback:
415	                self._add_action_func(self.retry_error_callback)
416	                return
417	
418	            def exc_check(rs: "RetryCallState") -> None:
419	                fut = t.cast("Future", rs.outcome)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/asyncio/__init__.py", "offset": 120, "limit": 50}
[tool_result] 120	                    if is_async:
121	                        result = await fn(*args, **kwargs)
122	                    else:
123	                        result = fn(*args, **kwargs)
124	                except BaseException:
125	                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
126	                else:
127	                    retry_state.set_result(result)
128	            elif isinstance(do, DoSleep):
129	                retry_state.prepare_for_next_att
…[1301 chars elided]…
_iter(retry_state)
158	        result = None
159	        for action in self.iter_state.actions:
160	            result = await action(retry_state)
161	        return result
162	
163	    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
164	        raise TypeError("AsyncRetrying object is not iterable")
165	
166	    def __aiter__(self) -> "AsyncRetrying":
167	        self.begin()
168	        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
169	        return self
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[2197 chars elided]…
m; write
  code that satisfies the rules above by inspection, and say in the final message that
  they were not run.
- **Shared helpers in `tenacity/_utils.py` feed user-visible text.** `to_ordinal` /
  `find_ordinal` build the "Nth time calling it" messages in `tenacity/before.py` and
  `tenacity/after.py`, and `tests/test_after.py` computes its expected strings through
  `_utils.to_ordinal`. Fix such helpers in `_utils.py` itself (not at call sites), and test the
  helper directly in `tests/test_utils.py` — the logging tests will not catch a wrong helper
  because they call the same helper.

[tool_use Bash] {"command": "grep -rn \"def begin\\|statistics\" tenacity/ | head -30; ls releasenotes/notes | tail -5; git status --short", "description": "Check begin() overrides and release notes"}
[tool_result] tenacity/__init__.py:295:    def statistics(self) -> dict[str, t.Any]:
tenacity/__init__.py:296:        """Return a dictionary of runtime statistics.
tenacity/__init__.py:305:                     change between major releases as new statistics are
tenacity/__init__.py:312:                  their own view of statistics they have collected (in the
tenacity/__init__.py:314:                  statistics from each thread).
tenacity/__init__.py:316:        if not hasattr(self._local, "statistics"):
ten
…[1099 chars elided]…
irst_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:195:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:201:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The skill's contract is clear: a behaviour fix needs the code change, a reno note, and a regression test. Next I'll read the existing statistics tests and a recent release note so the new ones match their style.
[tool_use Bash] {"command": "sed -n 1300,1360p tests/test_tenacity.py; echo ----; sed -n 410,460p tests/test_asyncio.py; echo ----; cat releasenotes/notes/fix-local-context-overwrite-*.yaml 2>/dev/null; ls releasenotes/notes | grep -i fix | tail -3; echo ----; cat \"releasenotes/notes/$(ls releasenotes/notes | grep -i '^fix' | tail -1)\"", "description": "Read stats tests and sample release notes"}
[tool_result]     def test_retry_function_object(self) -> None:
        """Test that functools.wraps doesn't cause problems with callable objects.

        It raises an error upon trying to wrap it in Py2, because __name__
        attribute is missing. It's fixed in Py3 but was never backported.
        """

        class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
   
…[3480 chars elided]…
     "start_time": mock.ANY,
                }
                self.assertEqual(
                    _retryable_coroutine_with_2_attempts.statistics,
                    expected_stats,
                )
----
---
fixes:
  - |
    Avoid overwriting local contexts when applying the retry decorator.
fix-setuptools-config-3af71aa3592b6948.yaml
fix-wait-typing-b26eecdb6cc0a1de.yaml
fix_async-52b6594c8e75c4bc.yaml
----
---
fixes:
  - "Fix issue #288 : __name__ and other attributes for async functions"
[assistant] The bug is in `BaseRetrying.begin()`, which sets the other per-run statistics but not `delay_since_first_attempt`. `AsyncRetrying` doesn't override `begin`, so the one fix covers both. Before editing, I'll check how the existing tests drive `Retrying` directly so the regression test matches them.
[tool_use Bash] {"command": "grep -n \"^class \\|^from\\|^import\" tests/test_tenacity.py | head -40; grep -n \"for attempt in\\|async for attempt in\" tests/test_tenacity.py tests/test_asyncio.py | head -5; grep -n \"^class \\|^from\\|^import\" tests/test_asyncio.py | head -20", "description": "Inspect test file structure and imports"}
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
88:class TestBase(unittest.TestCase):
114:class TestRetryingName(unittest.TestCase):
181:c
…[1460 chars elided]…
ools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
79:class TestAsyncio(unittest.TestCase):
164:class TestTrio(unittest.TestCase):
178:class TestContextManager(unittest.TestCase):
412:class TestDecoratorWrapper(unittest.TestCase):
481:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
[tool_use Bash] {"command": "sed -n 1617,1637p tests/test_tenacity.py; echo ----; sed -n 178,200p tests/test_asyncio.py", "description": "Read TestStatistics and asyncio context manager test"}
[tool_result] class TestStatistics(unittest.TestCase):
    def test_stats(self) -> None:
        @retry()
        def _foobar() -> int:
            return 42

        self.assertEqual({}, _foobar.statistics)
        _foobar()
        self.assertEqual(1, _foobar.statistics["attempt_number"])

    def test_stats_failing(self) -> None:
        @retry(stop=tenacity.stop_after_attempt(2))
        def _foobar() -> None:
            raise ValueError(42)

        self.assertEqual({}, _foobar.statistics)
        with 
…[298 chars elided]…
g(stop=stop_after_attempt(3))
        try:
            async for attempt in retrying:
                with attempt:
                    attempts += 1
                    raise Exception
        except RetryError:
            pass

        assert attempts == 3

    @asynctest
    async def test_reraise(self) -> None:
        class CustomError(Exception):
            pass

        try:
            async for attempt in tasyncio.AsyncRetrying(
                stop=stop_after_attempt(1), reraise=True
[assistant] Now the fix: initialise the key in `begin()` alongside the other per-run statistics.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, the regression tests: one sync in `TestStatistics`, one async in asyncio's `TestContextManager`. Both read the key during the first attempt, which is where the `KeyError` happened.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n", "new_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n    def test_delay_since_first_attempt_present_before_
…[60 chars elided]…
=tenacity.stop_after_attempt(2), reraise=True)\n        seen_delays = []\n        with contextlib.suppress(ValueError):\n            for attempt in retrying:\n                with attempt:\n                    seen_delays.append(retrying.statistics[\"delay_since_first_attempt\"])\n                    raise ValueError\n\n        assert seen_delays[0] == 0\n        assert len(seen_delays) == 2\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py", "old_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:", "new_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_delay_since_first_attempt_present_before_
…[128 chars elided]…
lays = []\n        with contextlib.suppress(ValueError):\n            async for attempt in retrying:\n                with attempt:\n                    seen_delays.append(retrying.statistics[\"delay_since_first_attempt\"])\n                    raise ValueError\n\n        assert seen_delays[0] == 0\n        assert len(seen_delays) == 2\n\n    @asynctest\n    async def test_reraise(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Three things to fix in those tests: `test_asyncio.py` doesn't import `contextlib`; `seen_delays = []` needs a type annotation under mypy strict; and the `append` line runs past 88 columns, so the formatter would rewrap it. I'll correct all three.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py", "old_string": "import asyncio\nimport inspect", "new_string": "import asyncio\nimport contextlib\nimport inspect"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py", "old_string": "        seen_delays = []\n        with contextlib.suppress(ValueError):\n            async for attempt in retrying:\n                with attempt:\n                    seen_delays.append(retrying.statistics[\"delay_
…[18 chars elided]…
t\"])\n                    raise ValueError", "new_string": "        seen_delays: list[float] = []\n        with contextlib.suppress(ValueError):\n            async for attempt in retrying:\n                with attempt:\n                    seen_delays.append(\n                        retrying.statistics[\"delay_since_first_attempt\"]\n                    )\n                    raise ValueError"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "        seen_delays = []\n        with contextlib.suppress(ValueError):\n            for attempt in retrying:\n                with attempt:\n                    seen_delays.append(retrying.statistics[\"delay_since
…[7 chars elided]…
attempt\"])\n                    raise ValueError", "new_string": "        seen_delays: list[float] = []\n        with contextlib.suppress(ValueError):\n            for attempt in retrying:\n                with attempt:\n                    seen_delays.append(\n                        retrying.statistics[\"delay_since_first_attempt\"]\n                    )\n                    raise ValueError"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the release note. The contract requires a `<slug>-<16 hex>.yaml` name, so I'll generate the suffix and write the note.
[tool_use Bash] {"command": "f=\"releasenotes/notes/fix-delay-since-first-attempt-$(openssl rand -hex 8).yaml\" && printf -- '---\\nfixes:\\n  - |\\n    The ``delay_since_first_attempt`` key is now present in ``statistics`` from the\\n    start of each run, with a value of ``0`` until the first delay has occurred.\\n    Previously it was missing until after the first retry, so reading it during the\\n    first attempt raised ``KeyError``.\\n' > \"$f\" && echo \"$f\" && cat \"$f\" && \"<work>/env-tenacity/bin/python\" -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Write release note and run test suite"}
[tool_result] releasenotes/notes/fix-delay-since-first-attempt-b041f55c58c9d01b.yaml
---
fixes:
  - |
    The ``delay_since_first_attempt`` key is now present in ``statistics`` from the
    start of each run, with a value of ``0`` until the first delay has occurred.
    Previously it was missing until after the first retry, so reading it during the
    first attempt raised ``KeyError``.
...........s................................................ [ 43%]
........................................................................ [ 95%]
......                                                                   [100%]
137 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] The full suite passes (137 passed, 1 skipped). Next I'll confirm the new tests actually catch the bug: I'll remove the new line from `begin()` temporarily and check that they fail.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"delay_since_first_attempt\"] = 0\n\n", "new_string": "\n"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "\"<work>/env-tenacity/bin/python\" -m pytest -q -p no:cacheprovider --color=no -k delay_since_first_attempt_present 2>&1 | tail -6", "description": "Run new tests against reverted fix"}
[tool_result] tests/test_tenacity.py:1648: AssertionError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_delay_since_first_attempt_present_before_first_retry
FAILED tests/test_tenacity.py::TestStatistics::test_delay_since_first_attempt_present_before_first_retry
2 failed, 136 deselected in 0.08s
[assistant] Both new tests fail without the fix, as they should. The failure shows as an `AssertionError` rather than a `KeyError` because the attempt context manager catches the `KeyError` and treats it as a retryable failure. Now I'll restore the fix.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "\"<work>/env-tenacity/bin/python\" -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short; git diff --stat", "description": "Restore fix, run full suite, show changes"}
[tool_result] ......                                                                   [100%]
137 passed, 1 skipped, 12 subtests passed in 1.81s
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-delay-since-first-attempt-b041f55c58c9d01b.yaml
 tenacity/__init__.py   |  1 +
 tests/test_asyncio.py  | 16 ++++++++++++++++
 tests/test_tenacity.py | 14 ++++++++++++++
 3 files changed, 31 insertions(+)
[assistant] `delay_since_first_attempt` is now set to `0` at the start of every run, so reading it during the first attempt no longer raises `KeyError`. The full suite passes (137 passed, 1 skipped).

- **Fix:** `BaseRetrying.begin()` in `tenacity/__init__.py` now initialises the key alongside `start_time`, `attempt_number` and `idle_for`. `AsyncRetrying` inherits `begin()`, so the asyncio path is covered by the same line.
- **Regression tests:** one sync test in `tests/test_tenacity.py` (`TestStatistics`) and one async test in `tests/test_asyncio.py` (`TestContextManager`). Each reads the key inside the 
…[59 chars elided]…
tlib` to `test_asyncio.py` for this. With the fix line removed, both tests fail. They fail with an `AssertionError` rather than the `KeyError` itself, because the attempt context manager catches the `KeyError` and treats it as a retryable failure.
- **Release note:** `releasenotes/notes/fix-delay-since-first-attempt-b041f55c58c9d01b.yaml`, a `fixes:` entry describing the old and new behaviour.

mypy and ruff are not installed in the project's check interpreter, so I didn't run them. I annotated the new test code by inspection and wrapped long lines to match the formatter. Nothing is committed.
