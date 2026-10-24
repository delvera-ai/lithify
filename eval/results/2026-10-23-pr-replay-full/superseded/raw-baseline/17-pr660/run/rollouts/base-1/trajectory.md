# trajectory base-1

final message:
`retry_if_exception_cause_type` now terminates on cyclic cause chains, and a matching cause is still found in a non-cyclic chain. The full suite passes (172 passed, 1 skipped).

**Cause:** the loop in `tenacity/retry.py` followed `exc.__cause__` with no visited check. For `raise e from e`, `e.__cause__` is `e`, so the loop never ends.

**Fix:** the loop now records each exception's `id()` in a set and stops when it sees one again. I used `id()` rather than the exception objects themselves, so it doesn't depend on exceptions being hashable.

**Tests:** I added `test_retry_if_exception_cause_type_cyclic_cause` to `tests/test_tenacity.py`. It covers a self-cause, a two-exception cycle, and a matching cause deeper in a normal chain. It calls the predicate directly rather than going through the retry decorator, so a regression fails instead of hanging the test run. I confirmed the old loop hangs on the self-cause case.

I haven't committed anything; the changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"__cause__\\|cause\" tenacity/*.py | head -50", "description": "Find cause-chain handling in tenacity source"}
[tool_result] tenacity/__init__.py:49:    retry_if_exception_cause_type,
tenacity/__init__.py:190:            # an "except" block), surface the underlying exception that caused
tenacity/__init__.py:193:                cause = exc.__cause__ or exc.__context__
tenacity/__init__.py:194:                if cause is not None:
tenacity/__init__.py:195:                    raise cause.with_traceback(cause.__traceback__) from None
tenacity/__init__.py:803:    "retry_if_exception_cause_type",
tenacity/retry.py:160:class
…[69 chars elided]…
 """Retries if any of the causes of the raised exception is of one or more types.
tenacity/retry.py:163:    The check on the type of the cause of the exception is done recursively (until finding
tenacity/retry.py:164:    an exception in the chain that has no `__cause__`)
tenacity/retry.py:172:        self.exception_cause_types = exception_types
tenacity/retry.py:181:                if isinstance(exc.__cause__, self.exception_cause_types):
tenacity/retry.py:183:                exc = exc.__cause__
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "offset": 150, "limit": 45}
[tool_result] 150	        # always retry if no exception was raised
151	        if not retry_state.outcome.failed:
152	            return True
153	
154	        exception = retry_state.outcome.exception()
155	        if exception is None:
156	            raise RuntimeError("outcome failed but the exception is None")
157	        return self.predicate(exception)
158	
159	
160	class retry_if_exception_cause_type(retry_base):
161	    """Retries if any of the causes of the raised exception is of one or more types.

…[724 chars elided]…
not None:
181	                if isinstance(exc.__cause__, self.exception_cause_types):
182	                    return True
183	                exc = exc.__cause__
184	
185	        return False
186	
187	
188	class retry_if_result(retry_base):
189	    """Retries if the result verifies a predicate."""
190	
191	    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
192	        self.predicate = predicate
193	
194	    def __call__(self, retry_state: "RetryCallState") -> bool:
[assistant] The loop has no cycle guard: with `raise e from e`, `exc.__cause__` is `exc` forever. I'll add a visited set keyed by `id()`, which doesn't depend on exception hashability.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "old_string": "            exc = retry_state.outcome.exception()\n            while exc is not None:\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = ex
…[96 chars elided]…
ack visited exceptions so cyclic cause chains (e.g. `raise e from e`)\n            # terminate instead of looping forever.\n            seen: set[int] = set()\n            while exc is not None and id(exc) not in seen:\n                seen.add(id(exc))\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc.__cause__"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py has been updated successfully.
[assistant] Next I'll add regression tests next to the existing cause-type tests, then run the project's checks.
[tool_use Bash] {"command": "grep -rn \"cause_type\" tests/ | head; ls <work>/env-tenacity/bin/python 2>&1", "description": "Locate existing cause-type tests and check venv exists"}
[tool_result] tests/test_tenacity.py:1170:@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
tests/test_tenacity.py:1171:def _retryable_test_with_exception_cause_type(thing: typing.Any) -> typing.Any:
tests/test_tenacity.py:1433:    def test_retry_if_exception_cause_type(self) -> None:
tests/test_tenacity.py:1435:            _retryable_test_with_exception_cause_type(NoNameErrorCauseAfterCount(5))
tests/test_tenacity.py:1439:            _retryable_test_with_exception_cause_type(NoIOErrorCauseAfterCount(5))
<work>/env-tenacity/bin/python
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "offset": 1425, "limit": 25}
[tool_result] 1425	                _retryable_test_if_not_exception_message_message(
1426	                    NoCustomErrorAfterCount(2)
1427	                )
1428	            )
1429	        except CustomError:
1430	            s = _retryable_test_if_not_exception_message_message.statistics
1431	            self.assertTrue(s["attempt_number"] == 1)
1432	
1433	    def test_retry_if_exception_cause_type(self) -> None:
1434	        self.assertTrue(
1435	            _retryable_test_with_exception_cause_type(NoNa
…[38 chars elided]…
  )
1437	
1438	        try:
1439	            _retryable_test_with_exception_cause_type(NoIOErrorCauseAfterCount(5))
1440	            self.fail("Expected exception without NameError as cause")
1441	        except NameError:
1442	            pass
1443	
1444	    def test_retry_preserves_argument_defaults(self) -> None:
1445	        def function_with_defaults(a: int = 1) -> int:
1446	            return a
1447	
1448	        def function_with_kwdefaults(*, a: int = 1) -> int:
1449	            return a
[assistant] The existing tests go through the decorator. A regression test for a hang should not hang on failure, so I'll call the predicate directly. First I'll check how `RetryCallState` records an outcome.
[tool_use Bash] {"command": "grep -n \"def set_result\\|def set_exception\\|class RetryCallState\\|def __init__\" tenacity/__init__.py | head; grep -n \"^from\\|^import\" tests/test_tenacity.py | head -30", "description": "Inspect RetryCallState API and test imports"}
[tool_result] 168:    def __init__(self, sleep: t.SupportsFloat) -> None:
182:    def __init__(self, last_attempt: "Future") -> None:
206:    def __init__(self, retry_state: "RetryCallState"):
238:    def __init__(
545:    def __init__(self, attempt_number: int) -> None:
567:class RetryCallState:
570:    def __init__(
624:    def set_result(self, val: t.Any) -> None:
630:    def set_exception(
16:import contextlib
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
[tool_use Bash] {"command": "sed -n 624,645p tenacity/__init__.py", "description": "Read RetryCallState set_exception signature"}
[tool_result]     def set_result(self, val: t.Any) -> None:
        ts = time.monotonic()
        fut = Future(self.attempt_number)
        fut.set_result(val)
        self.outcome, self.outcome_timestamp = fut, ts

    def set_exception(
        self,
        exc_info: tuple[
            type[BaseException], BaseException, "types.TracebackType | None"
        ],
    ) -> None:
        ts = time.monotonic()
        fut = Future(self.attempt_number)
        fut.set_exception(exc_info[1])
        self.outcome, self.outcome_timestamp = fut, ts

    def __repr__(self) -> str:
        if self.outcome is None:
            result = "none yet"
        elif self.outcome.failed:
            exception = self.outcome.exception()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "old_string": "        except NameError:\n            pass\n\n    def test_retry_preserves_argument_defaults(self) -> None:", "new_string": "        except NameError:\n            pass\n\n    def test_retry_if_exception_cause_typ
…[1110 chars elided]…
r(\"matching\")\n        cycle_a = ValueError(\"a\")\n        cycle_b = KeyError(\"b\")\n        cycle_a.__cause__ = cycle_b\n        cycle_b.__cause__ = cycle_a\n        outer = RuntimeError(\"outer\")\n        outer.__cause__ = matching\n        matching.__cause__ = None\n        self.assertTrue(predicate(retry_state_for(outer)))\n\n    def test_retry_preserves_argument_defaults(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] The last block in that test is muddled: it builds a cycle it never uses. I'll replace it with a plain deep chain that checks the match is still found.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "old_string": "        # A matching cause is still found after a cycle is detected elsewhere in the chain.\n        matching = NameError(\"matching\")\n        cycle_a = ValueError(\"a\")\n        cycle_b = KeyError(\"b\")\n     
…[187 chars elided]…
  self.assertTrue(predicate(retry_state_for(outer)))", "new_string": "        # A matching cause deeper in a non-cyclic chain is still found.\n        deep_match = NameError(\"deep\")\n        middle = ValueError(\"middle\")\n        outer = RuntimeError(\"outer\")\n        outer.__cause__ = middle\n        middle.__cause__ = deep_match\n        self.assertTrue(predicate(retry_state_for(outer)))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165009-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "timeout 120 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit=$?\"", "description": "Run project test suite with venv python"}
[tool_result] (eval):1: command not found: timeout
exit=0
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite with venv python"}
[tool_result] ...............s.................................................................................................................... [ 76%]
.........................................                                [100%]
172 passed, 1 skipped, 12 subtests passed in 1.88s
[assistant] The suite passes: 172 passed, 1 skipped. Next I'll confirm the new test actually catches the bug by running the old loop under a timeout.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nimport signal\ndef alarm(*a): raise SystemExit('HUNG: old loop did not terminate')\nsignal.signal(signal.SIGALRM, alarm); signal.alarm(3)\ne = ValueError('x'); e.__cause__ = e\nexc = e\nwhile exc is not None:\n    if isinstance(exc.__cause__, NameError): break\n    exc = exc.__cause__\nprint('old loop finished')\n\" ; echo \"exit=$?\"; git diff --stat", "description": "Confirm old loop hangs on self-cause, show diff stat"}
[tool_result] HUNG: old loop did not terminate
exit=1
 tenacity/retry.py      |  6 +++++-
 tests/test_tenacity.py | 31 +++++++++++++++++++++++++++++++
 2 files changed, 36 insertions(+), 1 deletion(-)
[assistant] `retry_if_exception_cause_type` now terminates on cyclic cause chains, and a matching cause is still found in a non-cyclic chain. The full suite passes (172 passed, 1 skipped).

**Cause:** the loop in `tenacity/retry.py` followed `exc.__cause__` with no visited check. For `raise e from e`, `e.__cause__` is `e`, so the loop never ends.

**Fix:** the loop now records each exception's `id()` in a set and stops when it sees one again. I used `id()` rather than the exception objects themselves, so it doesn't depend on exceptions being hashable.

**Tests:** I added `test_retry_if_exception_cause_type_cyclic_cause` to `tests/test_tenacity.py`. It covers a self-cause, a two-exception cycle, and a matching cause deeper in a normal chain. It calls the predicate directly rather than going through the retry decorator, so a regression fails instead of hanging the test run. I confirmed the old loop hangs on the self-cause case.

I haven't committed anything; the changes are in the working tree.
