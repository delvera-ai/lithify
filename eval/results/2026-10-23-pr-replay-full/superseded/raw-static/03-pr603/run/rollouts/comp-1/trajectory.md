# trajectory comp-1

final message:
The key is now present from the start of every run, with value `0`, so `statistics["delay_since_first_attempt"]` no longer raises `KeyError` during the first attempt. The full suite passes: 137 passed, 1 skipped.

**The fix:** `begin()` in `tenacity/__init__.py` already initialises the other per-run keys, so I added `delay_since_first_attempt = 0` there. `AsyncRetrying` calls the same `begin()`, so the async path is covered without a second edit. The later write in `_run_stop` still overwrites the key once a delay has occurred.

**Other changes:**
- **Regression tests:** `test_stats_delay_since_first_attempt_before_first_delay` in `tests/test_tenacity.py` (`TestStatistics`) and in `tests/test_asyncio.py` (`TestContextManager`). Each reads the key on the first attempt, outside `with attempt:`, so a `KeyError` isn't swallowed.
- **Release note:** `releasenotes/notes/fix-delay-since-first-attempt-dde3541c0ff8744b.yaml`, a `fixes:` entry.

**Verification:**
- **Fail on HEAD:** both new tests fail on the unmodified code with `KeyError: 'delay_since_first_attempt'`, so they catch the bug.
- **Not run:** mypy and ruff are not installed in the project interpreter, so the strict typing and lint checks were not run. I wrote the new tests to the annotation conventions by inspection.
- **Stray files:** `git status` shows only the three modified files and the new release note.

I didn't commit anything.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[4801 chars elided]…
n> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" --include='*.py' --include='*.rst' --include='*.yaml' --include='*.md' . ; ls releasenotes/notes | tail -5", "description": "Find references to delay_since_first_attempt"}
[tool_result] tests/test_tenacity.py:57:    delay_since_first_attempt: typing.Any,
tests/test_tenacity.py:66:        previous_attempt_number is _unset or delay_since_first_attempt is _unset
tests/test_tenacity.py:72:            delay_since_first_attempt=delay_since_first_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay_since_first_attempt)
tests/test_tenacity.py:1329:            "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:1346:                    "delay_since_
…[1288 chars elided]…
lls/tenacity-change-contract/SKILL.md:64:  Later updates happen in `_run_stop` (`delay_since_first_attempt`) and the `next_action`
.lithify/harness/skills/tenacity-change-contract/SKILL.md:68:  `delay_since_first_attempt` is written in both `tenacity/__init__.py` and
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The skill's checklist is clear: fix in `begin()`, mirror in async where needed, add a reno note and a regression test, then verify. Next I'll read the relevant code.
[tool_use Bash] {"command": "grep -n \"def begin\\|statistics\\|def _run_stop\\|seconds_since_start\" tenacity/__init__.py tenacity/asyncio/__init__.py; sed -n 1,40p .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness/skills/tenacity-change-contract/scripts/ 2>/dev/null", "description": "Locate statistics code and harness files"}
[tool_result] tenacity/asyncio/__init__.py:150:    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:195:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:201:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
tenacity/__init__.py:295:    def
…[1602 chars elided]…

tenacity/__init__.py:614:    statistics: dict[str, t.Any]
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Behaviour-changing code changes here ship with a reno note in `releasenotes/notes/` and a regression test in `tests/`; load skill `tenacity-change-contract` before finishing such a change.
fails_on_base.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tenacity/__init__.py", "offset": 350, "limit": 30}
[tool_result] 350	        return t.cast("_RetryDecorated[P, R]", wrapped_f)
351	
352	    def begin(self) -> None:
353	        self.statistics.clear()
354	        self.statistics["start_time"] = time.monotonic()
355	        self.statistics["attempt_number"] = 1
356	        self.statistics["idle_for"] = 0
357	
358	    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
359	        self.iter_state.actions.append(fn)
360	
361	    def _run_retry(self, retry_state: "RetryCallState") -> None:
362	       
…[246 chars elided]…
= 0.0
369	
370	        retry_state.upcoming_sleep = sleep
371	
372	    def _run_stop(self, retry_state: "RetryCallState") -> None:
373	        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
374	        self.iter_state.stop_run_result = self.stop(retry_state)
375	
376	    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
377	        self._begin_iter(retry_state)
378	        result = None
379	        for action in self.iter_state.actions:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tenacity/asyncio/__init__.py", "offset": 140, "limit": 25}
[tool_result] 140	        )
141	
142	    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
143	        if self.wait:
144	            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)
145	        else:
146	            sleep = 0.0
147	
148	        retry_state.upcoming_sleep = sleep
149	
150	    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
151	        self.statistics["delay_since_first_attempt"] = retry_state.s
…[87 chars elided]…
sync_func(self.stop)(
153	            retry_state
154	        )
155	
156	    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
157	        self._begin_iter(retry_state)
158	        result = None
159	        for action in self.iter_state.actions:
160	            result = await action(retry_state)
161	        return result
162	
163	    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
164	        raise TypeError("AsyncRetrying object is not iterable")
[assistant] The cause is in `begin()`: it initialises `start_time`, `attempt_number` and `idle_for`, but not `delay_since_first_attempt`, which is only written in `_run_stop`. Since `begin()` is shared by sync and async, one edit covers both. I'll add the key there with value `0`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, the regression test. I'll look at the existing `TestStatistics` class and the fail-on-base script.
[tool_use Bash] {"command": "grep -n \"class TestStatistics\" -A30 tests/test_tenacity.py; grep -n \"class TestContextManager\" tests/test_asyncio.py; sed -n 1,60p .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py; ls releasenotes/notes | head -3; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml", "description": "Inspect statistics tests, async test class, and reno format"}
[tool_result] 1617:class TestStatistics(unittest.TestCase):
1618-    def test_stats(self) -> None:
1619-        @retry()
1620-        def _foobar() -> int:
1621-            return 42
1622-
1623-        self.assertEqual({}, _foobar.statistics)
1624-        _foobar()
1625-        self.assertEqual(1, _foobar.statistics["attempt_number"])
1626-
1627-    def test_stats_failing(self) -> None:
1628-        @retry(stop=tenacity.stop_after_attempt(2))
1629-        def _foobar() -> None:
1630-            raise ValueErr
…[2900 chars elided]…
:", untar.stderr.decode(), file=sys.stderr)
            return 2
        shutil.rmtree(os.path.join(tmp, "tests"), ignore_errors=True)
        shutil.copytree(
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
features:
  - |
    If you're using `Trio <https://trio.readthedocs.io>`__, then
    ``@retry`` now works automatically. It's no longer necessary to
    pass ``sleep=trio.sleep``.
[assistant] The fix is in place. Next I'll add a regression test in sync and async form, so I'm checking the async test module's conventions first.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_asyncio.py; sed -n 178,200p tests/test_asyncio.py; grep -n \"^import\\|^from\" tests/test_tenacity.py | head -30", "description": "Check async test imports and class layout"}
[tool_result] # Copyright 2016 Étienne Bersac
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the spe
…[942 chars elided]…
ttempt in tasyncio.AsyncRetrying(
                stop=stop_after_attempt(1), reraise=True
16:import contextlib
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
[assistant] I'll add a sync test in `TestStatistics` and an async one in `TestContextManager`. Both read the key at the start of the first attempt, outside any `with attempt:` block, so a `KeyError` surfaces directly rather than being swallowed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\nclass TestRetryErrorCallback", "new_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n    def test_stats_delay
…[85 chars elided]…
top=tenacity.stop_after_attempt(2))\n        delays: list[float] = []\n        for attempt in retrying:\n            # Read outside `with attempt:`, which would swallow a KeyError.\n            delays.append(retrying.statistics[\"delay_since_first_attempt\"])\n            with attempt:\n                raise ValueError(42)\n        self.assertEqual(0, delays[0])\n\n\nclass TestRetryErrorCallback"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_asyncio.py", "old_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:", "new_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_stats_delay_since_first_attempt_before_fi
…[161 chars elided]…
c for attempt in retrying:\n                # Read outside `with attempt:`, which would swallow a KeyError.\n                delays.append(retrying.statistics[\"delay_since_first_attempt\"])\n                with attempt:\n                    raise Exception\n        except RetryError:\n            pass\n\n        assert delays[0] == 0\n\n    @asynctest\n    async def test_reraise(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now the release note, with a random 16-hex suffix per the naming convention in the skill.
[tool_use Bash] {"command": "suffix=$(openssl rand -hex 8) && f=\"releasenotes/notes/fix-delay-since-first-attempt-$suffix.yaml\" && printf '%s\\n' '---' 'fixes:' '  - |' '    The ``delay_since_first_attempt`` key of a retrying object'\"'\"'s ``statistics``' '    is now present from the start of each run, with the value ``0`` until a' '    delay has occurred. Previously it was missing until after the first retry,' '    so reading ``statistics[\"delay_since_first_attempt\"]`` during the first' '    attempt raised ``KeyError``.' > \"$f\" && cat \"$f\"", "description": "Write reno release note for the fix"}
[tool_result] ---
fixes:
  - |
    The ``delay_since_first_attempt`` key of a retrying object's ``statistics``
    is now present from the start of each run, with the value ``0`` until a
    delay has occurred. Previously it was missing until after the first retry,
    so reading ``statistics["delay_since_first_attempt"]`` during the first
    attempt raised ``KeyError``.
[assistant] Next, the fail-on-base check against the new tests, using the project interpreter from `memory.md`.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_tenacity.py::TestStatistics::test_stats_delay_since_first_attempt_before_first_delay\" \"tests/test_asyncio.py::TestContextManager::test_stats_delay_since_first_attempt_before_first_delay\" 2>&1 | tail -40; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run new tests against HEAD to confirm they fail"}
[tool_result] FF                                                                       [100%]
=================================== FAILURES ===================================
____ TestStatistics.test_stats_delay_since_first_attempt_before_first_delay ____

self = <tests.test_tenacity.TestStatistics testMethod=test_stats_delay_since_first_attempt_before_first_delay>

    def test_stats_delay_since_first_attempt_before_first_delay(self) -> None:
        retrying = Retrying(stop=tenacity.stop_after_attempt(2))
 
…[1127 chars elided]…
t'

tests/test_asyncio.py:200: KeyError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatistics::test_stats_delay_since_first_attempt_before_first_delay
FAILED tests/test_asyncio.py::TestContextManager::test_stats_delay_since_first_attempt_before_first_delay
2 failed in 0.06s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
exit=
[assistant] Both new tests fail on HEAD with the reported `KeyError`, so they catch the bug. Now the full suite, run once after the final edit.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and check git status"}
[tool_result] rs = <RetryCallState 4449979808: attempt #2; slept for 0.0; last result: failed (ValueError 42)>

    def exc_check(rs: "RetryCallState") -> None:
        fut = t.cast("Future", rs.outcome)
        retry_exc = self.retry_error_cls(fut)
        if self.reraise:
            retry_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x1093d6360 state=finished raised ValueError>]

tenacity/__init__.py:424: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatistics::test_stats_delay_since_first_attempt_before_first_delay
1 failed, 136 passed, 1 skipped, 12 subtests passed in 1.90s
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-delay-since-first-attempt-dde3541c0ff8744b.yaml
[assistant] The sync test fails on my side, not the fix: the `for` loop raises `RetryError` when attempts run out, and I didn't catch it. The async test already handles this. I'll add the same handling.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_tenacity.py", "old_string": "        delays: list[float] = []\n        for attempt in retrying:\n            # Read outside `with attempt:`, which would swallow a KeyError.\n            delays.append(retrying.statistics[\"delay_since_first_att
…[127 chars elided]…
": "        delays: list[float] = []\n        with contextlib.suppress(RetryError):\n            for attempt in retrying:\n                # Read outside `with attempt:`, which would swallow a KeyError.\n                delays.append(retrying.statistics[\"delay_since_first_attempt\"])\n                with attempt:\n                    raise ValueError(42)\n        self.assertEqual(0, delays[0])"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_tenacity.py::TestStatistics::test_stats_delay_since_first_attempt_before_first_delay\" \"tests/test_asyncio.py::TestContextManager::test_stats_delay_since_first_attempt_before_first_delay\" > /tmp/fob.txt 2>&1; echo \"fails_on_base exit=$?\"; grep -E \"KeyError|GOOD|BAD\" /tmp/fob.txt | head -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short", "description": "Re-verify fail-on-base, full suite, and git status"}
[tool_result] fails_on_base exit=0
                # Read outside `with attempt:`, which would swallow a KeyError.
E               KeyError: 'delay_since_first_attempt'
tests/test_tenacity.py:1643: KeyError
                # Read outside `with attempt:`, which would swallow a KeyError.
E               KeyError: 'delay_since_first_attempt'
........................................................................ [ 95%]
......                                                                   [100%]
137 passed, 1 skipped, 12 subtests passed in 1.89s
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-delay-since-first-attempt-dde3541c0ff8744b.yaml
[assistant] The key is now present from the start of every run, with value `0`, so `statistics["delay_since_first_attempt"]` no longer raises `KeyError` during the first attempt. The full suite passes: 137 passed, 1 skipped.

**The fix:** `begin()` in `tenacity/__init__.py` already initialises the other per-run keys, so I added `delay_since_first_attempt = 0` there. `AsyncRetrying` calls the same `begin()`, so the async path is covered without a second edit. The later write in `_run_stop` still overwrites the key once a delay has occurred.

**Other changes:**
- **Regression tests:** `test_stats_delay_sinc
…[213 chars elided]…
Error` isn't swallowed.
- **Release note:** `releasenotes/notes/fix-delay-since-first-attempt-dde3541c0ff8744b.yaml`, a `fixes:` entry.

**Verification:**
- **Fail on HEAD:** both new tests fail on the unmodified code with `KeyError: 'delay_since_first_attempt'`, so they catch the bug.
- **Not run:** mypy and ruff are not installed in the project interpreter, so the strict typing and lint checks were not run. I wrote the new tests to the annotation conventions by inspection.
- **Stray files:** `git status` shows only the three modified files and the new release note.

I didn't commit anything.
