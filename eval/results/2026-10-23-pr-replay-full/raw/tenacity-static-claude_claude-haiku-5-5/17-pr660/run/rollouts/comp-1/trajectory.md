# trajectory comp-1

final message:
`retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains. Self-cycles (`raise e from e`) and mutual cycles both return promptly, and a matching cause type is still found in a non-cyclic chain.

**The fix** (`tenacity/retry.py`): the walk records each exception's `id()` and stops when it reaches one it has already seen. Each link's cause is still checked before the stop, so a match on the last unseen link is still found. I traced the mutual-cycle case by hand to confirm this.

**Tests** (`tests/test_tenacity.py`, in `TestDecoratorWrapper` next to the existing cause-type test):
- `test_retry_if_exception_cause_type_self_cycle`
- `test_retry_if_exception_cause_type_mutual_cycle`

Both were red against the unfixed code: each hung at 100% CPU, and `run_tests.py` reported `exit=124` with `HUNG IN:` naming the test. Both are green now, and the existing `test_retry_if_exception_cause_type` still passes.

**Other changes:**
- Reno note `releasenotes/notes/retry-if-exception-cause-type-cycle-21a7c9c3ea330386.yaml` as a `fixes:` entry. The tenacity contract requires one for any user-visible fix. I could not parse it, because PyYAML isn't in the project venv.
- No docs change, since this adds no new API.

**Verification:**
- Full suite: `exit=0`, 173 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: `exit=0`, 0 problems.

**Not run:** ruff and mypy (the harness says they can't run here), and the YAML parse of the reno note.

One note on the first red run: the mutual-cycle test took 783 s wall time but only 16 s CPU, so the host was descheduled. The script's timeout still fired and named the test correctly.

I have not committed anything. The changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"cause\" tenacity/*.py | head -50 && ls .lithify/harness/scripts/ && cat .lithify/harness/scripts/run_tests.py | head -60", "description": "Locate cause-walking code and harness scripts"}
[tool_result] tenacity/__init__.py:49:    retry_if_exception_cause_type,
tenacity/__init__.py:190:            # an "except" block), surface the underlying exception that caused
tenacity/__init__.py:193:                cause = exc.__cause__ or exc.__context__
tenacity/__init__.py:194:                if cause is not None:
tenacity/__init__.py:195:                    raise cause.with_traceback(cause.__traceback__) from None
tenacity/__init__.py:803:    "retry_if_exception_cause_type",
tenacity/retry.py:160:class
…[2624 chars elided]…
s slower and unbounded.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time

try:
    import resource
except ImportError:  # pragma: no cover - non-POSIX
    resource = None  # type: ignore[assignment]

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
    if args[:1] == ["--timeout"]:
        if len(args) < 2:
            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
[tool_use Bash] {"command": "sed -n 150,200p tenacity/retry.py && grep -n \"cause\" tests/*.py | head -40 && ls <work>/env-tenacity/bin/python && ls releasenotes/notes 2>/dev/null | tail -3", "description": "Read cause-type retry code and related tests"}
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
…[2447 chars elided]…
473:        """Test that functools.wraps doesn't cause problems with callable objects.
tests/test_tenacity.py:1475:        It raises an error upon trying to wrap it in Py2, because __name__
<work>/env-tenacity/bin/python
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 1165,1180p tests/test_tenacity.py && sed -n 1425,1450p tests/test_tenacity.py && grep -n \"^class \\|^import\\|^from\" tests/test_tenacity.py | head -40", "description": "Read existing cause-type tests and imports"}
[tool_result] )
def _retryable_test_with_stop(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
def _retryable_test_with_exception_cause_type(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(retry=tenacity.retry_if_exception_type(IOError))
def _retryable_test_with_exception_type_io(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(retry=tenacity.retry_if_not_exception_type(IOError))
                _retryabl
…[1795 chars elided]…
class NoCustomErrorAfterCount:
1139:class CapturingHandler(logging.Handler):
1287:class TestDecoratorWrapper(unittest.TestCase):
1531:class TestStatisticsKeys:
1577:class TestEnabled:
1664:class TestRetryWith:
1702:class TestBeforeAfterAttempts(unittest.TestCase):
1855:class TestReraiseExceptions(unittest.TestCase):
1924:class TestStatistics(unittest.TestCase):
1976:class TestRetryErrorCallback(unittest.TestCase):
2009:class TestContextManager(unittest.TestCase):
2064:class TestInvokeAsCallable:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tests/test_tenacity.py", "old_string": "        except NameError:\n            pass\n\n    def test_retry_preserves_argument_defaults(self) -> None:", "new_string": "        except NameError:\n            pass\n\n    def test_retry_if_exception_cause_typ
…[681 chars elided]…
__ = second\n        second.__cause__ = first\n\n        def fn() -> None:\n            raise first\n\n        retrying = Retrying(\n            retry=tenacity.retry_if_exception_cause_type(NameError),\n            stop=tenacity.stop_after_attempt(3),\n        )\n        with self.assertRaises(ValueError):\n            retrying(fn)\n\n    def test_retry_preserves_argument_defaults(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 20 \"tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_cause_type_self_cycle\" \"tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_cause_type_mutual_cycle\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/red.txt", "description": "Run new cycle regression tests against unfixed code", "timeout": 60000}
[tool_result] exit=4
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collect
…[218 chars elided]…
1/tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_cause_type_self_cycle
(no match in any of [<UnitTestCase TestRetryConditions>])

ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_cause_type_mutual_cycle
(no match in any of [<UnitTestCase TestRetryConditions>])

---
wall 0.3s, cpu 0.2s
exit=4 (pytest); full log: /tmp/run_tests.log
[assistant] The new tests live in `TestDecoratorWrapper`, not `TestRetryConditions`. Rerunning with the correct class.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 20 \"tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cycle\" > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/red1.txt; /private/tmp/claude-50
…[40 chars elided]…
onal-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 20 \"tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cycle\" > /tmp/red2.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/red2.txt", "description": "Run each cycle regression test alone against unfixed code", "timeout": 120000}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bjusg6hqy). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261024-152742-bug-retry-if-exception-cause-typ-comp-1/6704d763-91f2-4d0a-ba8a-336033ade08f/tasks/bjusg6hqy.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The run is still going past the shell timeout. Per the harness, I'll wait for its completion notice rather than kill it.
[tool_use Bash] {"command": "sleep 5; tail -5 /tmp/red1.txt 2>/dev/null; echo ---; tail -3 /tmp/run_tests.log 2>/dev/null", "description": "Check interim output of the first red run"}
[tool_result] tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cycle 
---
TIMEOUT (limit 20s; wall 20s, cpu 19s); process group killed
HUNG IN: tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cycle
exit=124 (see this script's docstring for the next step)
---
collecting ... collected 1 item

tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cycle
[tool_use Bash] {"command": "tail -4 /tmp/red1.txt; echo ---; tail -4 /tmp/red2.txt; echo ---; <work>/env-tenacity/bin/python -c \"import tenacity,sys; print(tenacity.__file__)\"", "description": "Read verdict lines of both red runs"}
[tool_result] ---
TIMEOUT (limit 20s; wall 20s, cpu 19s); process group killed
HUNG IN: tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cycle
exit=124 (see this script's docstring for the next step)
---
---
TIMEOUT (limit 20s; wall 783s, cpu 16s); process group killed
HUNG IN: tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cycle
exit=124 (see this script's docstring for the next step)
---
~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tenacity/__init__.py
[assistant] Both regression tests are red for the reported reason: each hangs at 100% CPU and `run_tests.py` names the test (`exit=124`, `HUNG IN:`). The mutual-cycle run took 783 s wall but only 16 s CPU, so the host was descheduled, not the script misbehaving. Now the fix: stop the walk when it revisits an exception.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tenacity/retry.py", "old_string": "        if retry_state.outcome.failed:\n            exc = retry_state.outcome.exception()\n            while exc is not None:\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                 
…[116 chars elided]…
     exc = retry_state.outcome.exception()\n            # Track visited exceptions so a cyclic __cause__ chain terminates.\n            seen: set[int] = set()\n            while exc is not None and id(exc) not in seen:\n                seen.add(id(exc))\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc.__cause__"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-152742-bug-retry-if-exception-cause-typ/comp-1/tenacity/retry.py has been updated successfully.
[assistant] Now the targeted tests, plus the skill's required-files list, since this is a user-visible tenacity change.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_self_cycle\" \"tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type_mutual_cycle\" \"tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/green.txt; grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Run targeted cycle tests green and list contract skill sections", "timeout": 120000}
[tool_result] exit=0
tests/test_tenacity.py::TestDecoratorWrapper::test_retry_if_exception_cause_type PASSED [100%]

============================== 3 passed in 0.05s ===============================
---
wall 0.5s, cpu 0.4s
exit=0 (pytest); full log: /tmp/run_tests.log
10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give
…[314 chars elided]…
of a wait/stop strategy; renaming or deprecating one
258:## 1b4. Exponential wait arithmetic (`tenacity/wait.py`)
291:## 1c. CONTRACT: a new keyword on `Retrying`/`AsyncRetrying`/`@retry`
331:## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
360:## 2. A release note in `releasenotes/notes/` (reno)
382:## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
396:## 3. A regression test in the matching test file
410:## 4. Keep the change surface minimal
[tool_use Bash] {"command": "sed -n 110,138p .lithify/harness/skills/tenacity-change-contract/SKILL.md; sed -n 360,382p .lithify/harness/skills/tenacity-change-contract/SKILL.md; ls releasenotes/notes | head -3; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml", "description": "Read hang-fix and release note sections of contract skill"}
[tool_result] ## 1a3. A strategy call that never returns (hang, 100% CPU, cyclic `__cause__`)
Use this when a task says a `retry=`/`wait=`/`stop=` strategy hangs or loops forever.
- Loop order (`tenacity/__init__.py`): `_begin_iter` queues `_run_retry` (calls
  `self.retry(retry_state)`), then `_post_retry_check_actions` queues `_run_wait` and only
  then `_run_stop`. A `retry` (or `wait`) callable that never returns is never interrupted
  by `stop=`, so `stop_after_attempt(n)` in a test does NOT bound it. On
…[3009 chars elided]…
e style:
  ```yaml
  ---
  fixes:
    - |
      One or two sentences describing the user-visible fix.
  ```
- Rendered by `doc/source/changelog.rst` (`.. release-notes::`), so it must be valid YAML.

## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
[assistant] The contract skill calls for a reno note on any user-visible fix and confirms the guard must still check the cause of the last unseen link, which my trace confirms. Adding the note, then running the full suite.
[tool_use Bash] {"command": "suffix=$(openssl rand -hex 8) && f=\"releasenotes/notes/retry-if-exception-cause-type-cycle-${suffix}.yaml\" && printf '%s\\n' '---' 'fixes:' '  - |' '    ``retry_if_exception_cause_type`` no longer hangs when an exception'\"'\"'s' '    ``__cause__`` chain is cyclic (e.g. ``raise e from e``). The chain walk now stops at'  '    an exception it has already visited, and still matches a c
…[67 chars elided]…
cat \"$f\" && python3 -c \"import yaml\" 2>/dev/null; echo \"yaml-check-skipped-if-no-pyyaml\"; <work>/env-tenacity/bin/python -c \"import yaml,sys; print(yaml.safe_load(open(sys.argv[1])))\" \"$f\" 2>&1 | tail -2", "description": "Create reno release note for the cycle fix"}
[tool_result] ---
fixes:
  - |
    ``retry_if_exception_cause_type`` no longer hangs when an exception's
    ``__cause__`` chain is cyclic (e.g. ``raise e from e``). The chain walk now stops at
    an exception it has already visited, and still matches a cause type found anywhere
    earlier in the chain.
yaml-check-skipped-if-no-pyyaml
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'yaml'
[assistant] PyYAML isn't in the project venv, so I can't parse the note; its shape matches the house style exactly. Running the full suite now, foreground, with the harness's 400000 ms ceiling.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -12 /tmp/full.txt", "description": "Run full test suite via harness script", "timeout": 400000}
[tool_result] exit=0
tests/test_tenacity.py::TestPickle::test_retrying_pickle_round_trip_works PASSED [ 96%]
tests/test_tornado.py::TestTornado::test_old_tornado PASSED              [ 97%]
tests/test_tornado.py::TestTornado::test_repr PASSED                     [ 97%]
tests/test_tornado.py::TestTornado::test_retry PASSED                    [ 98%]
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 173 passed, 1 skipped, 12 subtests passed in 2.37s ==============
---
wall 2.7s, cpu 1.1s
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt; git status --short", "description": "Run stdlib lint stand-in and show changed files", "timeout": 120000}
[tool_result] exit=0
changed: releasenotes/notes/retry-if-exception-cause-type-cycle-21a7c9c3ea330386.yaml, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/retry-if-exception-cause-type-cycle-21a7c9c3ea330386.yaml
[assistant] `retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains. Self-cycles (`raise e from e`) and mutual cycles both return promptly, and a matching cause type is still found in a non-cyclic chain.

**The fix** (`tenacity/retry.py`): the walk records each exception's `id()` and stops when it reaches one it has already seen. Each link's cause is still checked before the stop, so a match on the last unseen link is still found. I traced the mutual-cycle case by hand to confirm this.

**Tests** (`tests/test_tenacity.py`, in `TestDecoratorWrapper` next to the existing cause-type test)
…[520 chars elided]…
 I could not parse it, because PyYAML isn't in the project venv.
- No docs change, since this adds no new API.

**Verification:**
- Full suite: `exit=0`, 173 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: `exit=0`, 0 problems.

**Not run:** ruff and mypy (the harness says they can't run here), and the YAML parse of the reno note.

One note on the first red run: the mutual-cycle test took 783 s wall time but only 16 s CPU, so the host was descheduled. The script's timeout still fired and named the test correctly.

I have not committed anything. The changes are in the working tree.
