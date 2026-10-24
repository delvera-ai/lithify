# trajectory dom-1

final message:
The cyclic-cause hang is fixed. `retry_if_exception_cause_type` now stops walking when it revisits an exception, so `raise e from e` and two exceptions pointing at each other both terminate. A matching type is still found in a non-cyclic chain, and a match inside a cycle is also found.

The change is in `tenacity/retry.py`: the cause walk keeps a set of visited exception ids and stops at the first repeat. The matching rule is unchanged, so it still checks each link's `__cause__`, never the raised exception itself.

**Tests** (`tests/test_tenacity.py`, class `TestDecoratorWrapper`):
- `test_retry_if_exception_cause_type_cycle_returns_direct` calls the strategy directly in a daemon thread. Against the unfixed code it fails with `AssertionError: True is not false` in 9.67 s, exit 1, not a hang. This is the red run I trust most.
- Two end-to-end `Retrying` tests cover the self-cycle and mutual-cycle cases, plus a match inside a cycle. These hang on unfixed code, so I did not get a clean red for them. The self-cycle one did hang under the harness (`exit=124`). The harness stopped at that first hang, so the mutual-cycle and match-inside-cycle tests never ran against the unfixed code.
- Full suite after the fix: 175 passed, 1 skipped, exit 0.

**Other steps:**
- Added `releasenotes/notes/fix-retry-if-exception-cause-type-cycle-2c9d4e1a7b6f3085.yaml` as a `fixes:` note. The hex suffix is a made-up value; any unique hex is fine.
- `check_changed.py`: PASS, 0 problems.

**Not run:** ruff, mypy and PyYAML are unavailable in this environment, so the reno note was not parsed as YAML. I did not change `doc/source/index.rst`, since this is a bug fix and not a new API.

**Scope:** the only chain walk in the package is this one. The async module has no cause-type class, so there is no async copy to fix.

I have not committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"__cause__\" tenacity/ tests/ | head -50; ls .lithify/harness/scripts/", "description": "Locate __cause__ usages and harness scripts"}
[tool_result] tenacity/__init__.py:193:                cause = exc.__cause__ or exc.__context__
tenacity/retry.py:164:    an exception in the chain that has no `__cause__`)
tenacity/retry.py:181:                if isinstance(exc.__cause__, self.exception_cause_types):
tenacity/retry.py:183:                exc = exc.__cause__
check_changed.py
run_tests.py
[tool_use Bash] {"command": "sed -n 150,200p tenacity/retry.py; echo ---; sed -n 180,200p tenacity/__init__.py; echo ---; grep -rln \"exception_cause_type\" tests/ doc/ releasenotes/ 2>/dev/null", "description": "Read cause-walk code and find related tests"}
[tool_result]         # always retry if no exception was raised
        if not retry_state.outcome.failed:
            return True

        exception = retry_state.outcome.exception()
        if exception is None:
            raise RuntimeError("outcome failed but the exception is None")
        return self.predicate(exception)


class retry_if_exception_cause_type(retry_base):
    """Retries if any of the causes of the raised exception is of one or more types.

    The check on the type of the cause of the e
…[1900 chars elided]…
       cause = exc.__cause__ or exc.__context__
                if cause is not None:
                    raise cause.with_traceback(cause.__traceback__) from None
            raise self.last_attempt.result()
        raise self

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.last_attempt}]"
---
tests/test_tenacity.py
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml
[tool_use Bash] {"command": "grep -n \"cause_type\\|def test_retry_if_exception_cause\\|^import\\|^from\" tests/test_tenacity.py | head -40; echo ---; sed -n 1,40p .lithify/harness/scripts/run_tests.py | head -60; echo ---; cat releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml", "description": "Inspect existing cause-type tests and harness script"}
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
1170:@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
1171:def _retryable_test_with_exceptio
…[1506 chars elided]…
also hangs without your change (`git stash`, run, `git
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
---
---
features:
  - |
    Add a new `retry_base` class called `retry_if_exception_cause_type` that
    checks, recursively, if any of the causes of the raised exception is of a certain type.
[tool_use Bash] {"command": "sed -n 1160,1180p tests/test_tenacity.py; echo ---; sed -n 1425,1445p tests/test_tenacity.py; echo ---; grep -n \"class NoNameErrorCauseAfterCount\" -A 12 tests/test_tenacity.py; echo ---; cat memory.md 2>/dev/null; ls ~/.claude/projects/-private-tmp-claude-501--Users-user-Coding-delvera-foundational-lithify-19d43989-6c6b-4090-9032-1fdbf9e87d20-scratchpad-pr-work-replay-pr-replay-full-tenacity-static-claude-claude-haiku-5-5-repo/memory/ 2>/dev/null", "description": "Read existing cause-type test and helpers"}
[tool_result] @retry(
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_result(lambda result: result is None),
)
def _retryable_test_with_stop(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
def _retryable_test_with_exception_cause_type(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(retry=tenacity.retry_if_exception_type(IOError))
def _retryable_test_with_exception_type_io(thing: typing.Any) -> typin
…[906 chars elided]…
---
1013:class NoNameErrorCauseAfterCount:
1014-    """Holds counter state for invoking a method several times in a row."""
1015-
1016-    def __init__(self, count: int) -> None:
1017-        self.counter = 0
1018-        self.count = count
1019-
1020-    def go2(self) -> typing.Any:
1021-        raise NameError("Hi there, I'm a NameError")
1022-
1023-    def go(self) -> typing.Any:
1024-        """Raise an IOError with a NameError as cause until after count threshold has been crossed.
1025-
---
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[assistant] Picking up at the regression test. The cause walk in `tenacity/retry.py` has no visited set, so I'll add a cyclic-cause test next to the existing cause-type test and confirm it hangs before fixing anything.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py", "old_string": "    def test_retry_preserves_argument_defaults(self) -> None:", "new_string": "    def test_retry_if_exception_cause_type_self_cause_terminates(self) -> None:\n        # `raise e from e` leaves e.__cause__ pointing 
…[1467 chars elided]…
   raise a\n\n        retrying = Retrying(\n            stop=tenacity.stop_after_attempt(3),\n            retry=tenacity.retry_if_exception_cause_type(IOError),\n            reraise=True,\n        )\n        with self.assertRaises(ValueError):\n            retrying(raise_cycle_with_match)\n        self.assertEqual(len(attempts), 3)\n\n    def test_retry_preserves_argument_defaults(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestTenacity::test_retry_if_exception_cause_type_self_cause_terminates tests/test_tenacity.py::TestTenacity::test_retry_if_exception_cause_type_mutual_cause_terminates tests/test_tenacity.py::TestTenacity::test_retry_if_exception_cause_type_match_inside_cycle > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -n 30 /tmp/red.txt", "description": "Run new cyclic-cause tests against unfixed code"}
[tool_result] exit=4
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collecte
…[453 chars elided]…
-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py::TestTenacity::test_retry_if_exception_cause_type_mutual_cause_terminates
(no match in any of [<Module test_tenacity.py>])

ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py::TestTenacity::test_retry_if_exception_cause_type_match_inside_cycle
(no match in any of [<Module test_tenacity.py>])

---
exit=4 (pytest); full log: /tmp/run_tests.log
[assistant] The node IDs were wrong: the class name isn't `TestTenacity`. Looking up the actual class that holds the existing cause-type test.
[tool_use Bash] {"command": "awk 'NR<=1440 && /^class /{c=$0} END{}; NR==1440{print c}' tests/test_tenacity.py", "description": "Find class containing the new tests"}
[tool_result] class TestDecoratorWrapper(unittest.TestCase):
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cause_terminates tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cause_terminates tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_match_inside_cycle > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -n 30 /tmp/red.txt", "description": "Run new cyclic-cause tests against unfixed code"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bavxt08j5). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bavxt08j5.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The run exceeded the foreground tool limit and moved to the background. Checking its output file for the verdict.
[tool_use Read] {"file_path": "<tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bavxt08j5.output"}
[tool_result] <system-reminder>Warning: the file exists but the contents are empty.</system-reminder>
[tool_use ToolSearch] {"query": "select:Monitor", "max_results": 1}
[tool_result] 
[assistant] Monitor is loaded. Using it to wait on the background red run until its `exit=` verdict line appears.
[tool_use Monitor] {"command": "f=<tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bavxt08j5.output; for i in $(seq 1 300); do if grep -q \"exit=\" \"$f\" 2>/dev/null; then grep -E \"exit=|HUNG|passed|failed|Error|FAILED\" \"$f\" | tail -n 20; break; fi; sleep 1; done", "description": "Wait for red-test run verdict and report it", "timeout_ms": 600000}
[tool_result] Monitor started (task b16ddvmsb, expires in 10m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[assistant] The red run for the three new cyclic-cause tests is still going: the harness bounds each test at 60 s, so this takes a few minutes. I'm waiting for its verdict before touching `tenacity/retry.py`. The fix is a visited-set guard in the `retry_if_exception_cause_type` cause walk, and I'll apply it only after the tests show red for the hang.
[assistant] The background run reports exit code 0, which is unexpected for unfixed code that should hang. Reading the output before concluding anything.
[tool_use Read] {"file_path": "<tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bavxt08j5.output"}
[tool_result] 1	exit=124
2	============================= test session starts ==============================
3	platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
4	rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1
5	configfile: pyproject.toml
6	plugins: typeguard-4.6.0
7	collecting ... collected 3 items
8	
9	tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cause_terminates 
10	---
11	TIMEOUT after 60s; process group killed
12	HUNG IN: tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cause_terminates
13	exit=124 (see this script's docstring for the next step)
14	
15	[exited with code 0]
16	
[assistant] The red run confirms the hang: the self-cause test hit the 60 s bound with `exit=124` and `HUNG IN: ...self_cause_terminates`. The harness stopped at the first hang, so the mutual-cause and match-inside-cycle tests never ran against the unfixed code. Applying the fix now: a visited-set guard in the cause walk.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tenacity/retry.py", "old_string": "            exc = retry_state.outcome.exception()\n            while exc is not None:\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc
…[35 chars elided]…
     exc = retry_state.outcome.exception()\n            # Track visited exceptions so a cyclic __cause__ chain terminates.\n            seen: set[int] = set()\n            while exc is not None and id(exc) not in seen:\n                seen.add(id(exc))\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc.__cause__"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tenacity/retry.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cause_terminates tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cause_terminates tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_match_inside_cycle tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -n 25 /tmp/green.txt", "description": "Run new and existing cause-type tests after fix"}
[tool_result] exit=0
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collecte
…[87 chars elided]…
type_self_cause_terminates PASSED [ 25%]
tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cause_terminates PASSED [ 50%]
tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_match_inside_cycle PASSED [ 75%]
tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type PASSED [100%]

============================== 4 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All four cause-type tests pass. Next, the full suite, with the tool timeout raised so it stays in the foreground.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -n 15 /tmp/full.txt", "description": "Run full test suite via harness script", "timeout": 600000}
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

============== 174 passed, 1 skipped, 12 subtests passed in 1.99s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt | tail -n 30", "description": "Run stdlib lint substitute on changed files"}
[tool_result] exit=0
changed: tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (174 passed, 1 skipped, exit 0) and the stdlib check is clean. This is a user-visible tenacity fix, so the change-contract skill applies. Checking which files it requires beyond the code.
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; grep -n -i 'reno\\|releasenote\\|index.rst' .lithify/harness/skills/tenacity-change-contract/SKILL.md | head -30; echo ---; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | grep -i 'fix' | tail -1)", "description": "Read contract skill checklist and sample reno note"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1a3. A strategy call that never returns (hang, 100% CPU, cyclic `__cause__`)
140:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
180:## 1b2. Object state, pickling
…[3430 chars elided]…
ith `grep -n "<existing usage, e.g. 'with attempt:'>" doc/source/index.rst`,
408:  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
---
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
fixes:
  - "Fix issue #288 : __name__ and other attributes for async functions"
[tool_use Bash] {"command": "sed -n 110,139p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; sed -n 361,382p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml", "description": "Read hang-fix checklist and reno note format"}
[tool_result] ## 1a3. A strategy call that never returns (hang, 100% CPU, cyclic `__cause__`)
Use this when a task says a `retry=`/`wait=`/`stop=` strategy hangs or loops forever.
- Loop order (`tenacity/__init__.py`): `_begin_iter` queues `_run_retry` (calls
  `self.retry(retry_state)`), then `_post_retry_check_actions` queues `_run_wait` and only
  then `_run_stop`. A `retry` (or `wait`) callable that never returns is never interrupted
  by `stop=`, so `stop_after_attempt(n)` in a test does NOT bound it. On
…[3009 chars elided]…
nal structure) use `other:` (11 notes in the
  repo use it). House style:
  ```yaml
  ---
  fixes:
    - |
      One or two sentences describing the user-visible fix.
  ```
- Rendered by `doc/source/changelog.rst` (`.. release-notes::`), so it must be valid YAML.

---
---
features:
  - |
    Add ``min`` parameter to ``wait_exponential_jitter`` to set a minimum wait
    time floor, consistent with ``wait_exponential``. Also accept ``timedelta``
    for ``max``, ``jitter``, and ``min`` parameters.
[assistant] The skill's hang guidance matters here. My end-to-end `Retrying` tests hang the process on unfixed code, so the red run can't terminate by itself. The skill asks for a direct call in a daemon thread with a join timeout, which fails instead of hanging. Checking the `make_retry_state` helper before adding that test.
[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A 12 tests/test_tenacity.py; grep -n \"^import threading\" tests/test_tenacity.py; grep -n \"make_retry_state(\" tests/test_tenacity.py | head -3", "description": "Inspect make_retry_state helper and threading import"}
[tool_result] 54:def make_retry_state(
55-    previous_attempt_number: typing.Any,
56-    delay_since_first_attempt: typing.Any,
57-    last_result: typing.Any = None,
58-    upcoming_sleep: typing.Any = 0,
59-) -> RetryCallState:
60-    """Construct RetryCallState for given attempt number & delay.
61-
62-    Only used in testing and thus is extra careful about timestamp arithmetics.
63-    """
64-    required_parameter_unset = (
65-        previous_attempt_number is _unset or delay_since_first_attempt is _unset
66-    )
54:def make_retry_state(
101:        rs = make_retry_state(2, 5)
105:        rs = make_retry_state(
[assistant] Adding a direct-call regression test that runs the predicate in a daemon thread. A hang then becomes a clean assertion failure.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_cause_type_self_cause_terminates(self) -> None:\n        # `raise e from e` leaves e.__cause__ pointing at e itself.", "new_string": "    def test_retry_if_exception_cause_type_cycle_
…[423 chars elided]…
ad = threading.Thread(\n            target=lambda: result.append(strategy(rs)), daemon=True\n        )\n        thread.start()\n        thread.join(timeout=5)\n        self.assertFalse(thread.is_alive())\n        self.assertEqual(result, [False])\n\n    def test_retry_if_exception_cause_type_self_cause_terminates(self) -> None:\n        # `raise e from e` leaves e.__cause__ pointing at e itself."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py", "old_string": "import re\nimport time\nimport typing", "new_string": "import re\nimport threading\nimport time\nimport typing"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/dom-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the red check for the new direct test. I'm temporarily restoring the unfixed `retry.py` from HEAD, keeping a copy of the fix to restore afterwards.
[tool_use Bash] {"command": "cp tenacity/retry.py /tmp/retry_fixed.py && git show HEAD:tenacity/retry.py > tenacity/retry.py && <work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_cycle_returns_direct > /tmp/red2.txt 2>&1; echo \"exit=$?\"; tail -n 12 /tmp/red2.txt; cp /tmp/retry_fixed.py tenacity/retry.py && git diff --stat", "description": "Red-check direct test on unfixed retry.py, then restore fix", "timeout": 200000}
[tool_result] Command did not complete within its 200s timeout and was moved to the background (ID: bsr3o39ie). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bsr3o39ie.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The red check went to the background, and the file-changed notice reflects my own temporary revert. The restore step is chained after the run, so it still executes. Waiting for the result before I touch anything else.
[tool_use Monitor] {"command": "f=<tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bsr3o39ie.output; for i in $(seq 1 540); do if grep -q \"exit=\" \"$f\" 2>/dev/null; then grep -E \"exit=|HUNG|passed|failed|Error|FAILED|assert\" \"$f\" | tail -n 20; break; fi; sleep 1; done", "description": "Wait for direct red-test verdict", "timeout_ms": 600000}
[tool_result] Monitor started (task big3gldkn, expires in 10m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[tool_use Bash] {"command": "tail -n 12 <tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-dom-1/dc44b5db-be3b-4236-b02d-0ed43d934952/tasks/bsr3o39ie.output; echo ---; diff /tmp/retry_fixed.py tenacity/retry.py && echo \"fix restored\"; grep -n \"seen\" tenacity/retry.py", "description": "Show red-check output and confirm fix restored"}
[tool_result] tests/test_tenacity.py:1459: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_cycle_returns_direct
============================== 1 failed in 9.67s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
 tenacity/retry.py      |  5 +++-
 tests/test_tenacity.py | 71 ++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 75 insertions(+), 1 deletion(-)

[exited with code 0]
---
fix restored
181:            seen: set[int] = set()
182:            while exc is not None and id(exc) not in seen:
183:                seen.add(id(exc))
[assistant] The direct test is red for the right reason on unfixed code: the thread is still alive after the join, `AssertionError: True is not false`, exit 1 rather than a hang. The fix is restored. Next, the reno note the skill requires.
[tool_use Bash] {"command": "python3 -c \"import secrets;print(secrets.token_hex(8))\" && cat > releasenotes/notes/fix-retry-if-exception-cause-type-cycle-2c9d4e1a7b6f3085.yaml <<'EOF'\n---\nfixes:\n  - |\n    Fix ``retry_if_exception_cause_type`` hanging forever (100% CPU) when the\n    exception's ``__cause__`` chain is cyclic, for example ``raise e from e`` or\n    two exceptions whose causes point at each oth
…[154 chars elided]…
private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python -c \"import yaml\" 2>/dev/null || echo \"(no PyYAML in env; reno note shape checked by eye)\"; cat releasenotes/notes/fix-retry-if-exception-cause-type-cycle-2c9d4e1a7b6f3085.yaml | head -3", "description": "Create reno release note for the fix"}
[tool_result] 6819278f45e98cc2
(no PyYAML in env; reno note shape checked by eye)
---
fixes:
  - |
[assistant] Re-running the full suite and the stdlib check with the new test and note in place.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; echo \"exit=$?\"; tail -n 4 /tmp/full2.txt; <work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"check_exit=$?\"; tail -n 6 /tmp/check2.txt", "description": "Run full suite and stdlib check after all edits", "timeout": 600000}
[tool_result] exit=0

============== 175 passed, 1 skipped, 12 subtests passed in 2.52s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
check_exit=0
changed: releasenotes/notes/fix-retry-if-exception-cause-type-cycle-2c9d4e1a7b6f3085.yaml, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The cyclic-cause hang is fixed. `retry_if_exception_cause_type` now stops walking when it revisits an exception, so `raise e from e` and two exceptions pointing at each other both terminate. A matching type is still found in a non-cyclic chain, and a match inside a cycle is also found.

The change is in `tenacity/retry.py`: the cause walk keeps a set of visited exception ids and stops at the first repeat. The matching rule is unchanged, so it still checks each link's `__cause__`, never the raised exception itself.

**Tests** (`tests/test_tenacity.py`, class `TestDecoratorWrapper`):
- `test_ret
…[649 chars elided]…
xit 0.

**Other steps:**
- Added `releasenotes/notes/fix-retry-if-exception-cause-type-cycle-2c9d4e1a7b6f3085.yaml` as a `fixes:` note. The hex suffix is a made-up value; any unique hex is fine.
- `check_changed.py`: PASS, 0 problems.

**Not run:** ruff, mypy and PyYAML are unavailable in this environment, so the reno note was not parsed as YAML. I did not change `doc/source/index.rst`, since this is a bug fix and not a new API.

**Scope:** the only chain walk in the package is this one. The async module has no cause-type class, so there is no async copy to fix.

I have not committed anything.
