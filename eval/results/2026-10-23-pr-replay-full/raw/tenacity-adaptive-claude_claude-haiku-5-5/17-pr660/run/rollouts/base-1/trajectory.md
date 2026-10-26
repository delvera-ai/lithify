# trajectory base-1

final message:
`retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains and still finds a matching cause anywhere in a non-cyclic chain. The full suite passes: 173 passed, 1 skipped.

**The fix** (`tenacity/retry.py`): the cause walk now records each exception's `id()` and stops when it reaches one it has already visited. `raise e from e` and mutually-pointing causes both end the walk. Matching behaviour is unchanged for acyclic chains.

**Tests** (`tests/test_tenacity.py`, added after the existing cause-type test; no existing test was touched):
- `test_retry_if_exception_cause_type_self_cause_terminates`: an exception whose cause is itself, with no matching type, returns "don't retry" and re-raises.
- `test_retry_if_exception_cause_type_cycle_with_match`: a cycle that still contains a matching `NameError` retries.

I confirmed the self-cause test hangs on the original code (a faulthandler dump showed the loop), so it guards the bug. I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"exception_cause\\|__cause__\" ~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1 --include=*.py | grep -v \"/\\.git/\"", "description": "Locate cause-chain code in repo"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"__cause__\" --include='*.py' . | grep -v \"/\\.git/\"", "description": "Find __cause__ usages in Python sources"}
[tool_result] tenacity/__init__.py:193:                cause = exc.__cause__ or exc.__context__
tenacity/retry.py:164:    an exception in the chain that has no `__cause__`)
tenacity/retry.py:181:                if isinstance(exc.__cause__, self.exception_cause_types):
tenacity/retry.py:183:                exc = exc.__cause__
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "offset": 140, "limit": 60}
[tool_result] 140	        self.exception_types = exception_types
141	        super().__init__(self._check)
142	
143	    def _check(self, e: BaseException) -> bool:
144	        return not isinstance(e, self.exception_types)
145	
146	    def __call__(self, retry_state: "RetryCallState") -> bool:
147	        if retry_state.outcome is None:
148	            raise RuntimeError("__call__() called before outcome was set")
149	
150	        # always retry if no exception was raised
151	        if not retry_state.outcom
…[1376 chars elided]…
189	    """Retries if the result verifies a predicate."""
190	
191	    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
192	        self.predicate = predicate
193	
194	    def __call__(self, retry_state: "RetryCallState") -> bool:
195	        if retry_state.outcome is None:
196	            raise RuntimeError("__call__() called before outcome was set")
197	
198	        if not retry_state.outcome.failed:
199	            return self.predicate(retry_state.outcome.result())
[assistant] The loop at `tenacity/retry.py:180-183` follows `__cause__` with no visited check, so a cycle never ends. I'll look at the existing tests before changing it.
[tool_use Bash] {"command": "grep -rn \"cause\" tests/ | head -30; grep -n \"^from\\|^import\" tests/test_tenacity.py | head -20", "description": "Find existing cause-related tests"}
[tool_result] tests/test_asyncio.py:297:    async def test_reraise_try_again_with_cause(self) -> None:
tests/test_tenacity.py:875:    def test_retry_try_again_with_cause_reraise(self) -> None:
tests/test_tenacity.py:896:    def test_retry_try_again_from_cause_reraise(self) -> None:
tests/test_tenacity.py:1024:        """Raise an IOError with a NameError as cause until after count threshold has been crossed.
tests/test_tenacity.py:1049:        """Raise a NameError with an IOError as cause until after count thr
…[740 chars elided]…
cts.
tests/test_tenacity.py:1475:        It raises an error upon trying to wrap it in Py2, because __name__
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "offset": 1425, "limit": 20}
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
1435	            _retryable_test_with_exception_cause_type(NoNameErrorCauseAfterCount(5))
1436	        )
1437	
1438	        try:
1439	            _retryable_test_with_exception_cause_type(NoIOErrorCauseAfterCount(5))
1440	            self.fail("Expected exception without NameError as cause")
1441	        except NameError:
1442	            pass
1443	
1444	    def test_retry_preserves_argument_defaults(self) -> None:
[assistant] Now I'll apply the fix: track visited exceptions by identity and stop when the chain revisits one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "old_string": "            exc = retry_state.outcome.exception()\n            while exc is not None:\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = ex
…[60 chars elided]…
utcome.exception()\n            # Track visited exceptions so a cyclic __cause__ chain (e.g. `raise e from e`) terminates.\n            seen: set[int] = set()\n            while exc is not None and id(exc) not in seen:\n                seen.add(id(exc))\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc.__cause__"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py has been updated successfully.
[assistant] Next, regression tests next to the existing cause-type test. They cover a self-cycle with no match (the hang case), a cycle that still finds a match, and a non-cyclic chain.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "old_string": "        except NameError:\n            pass\n\n    def test_retry_preserves_argument_defaults(self) -> None:", "new_string": "        except NameError:\n            pass\n\n    def test_retry_if_exception_cause_typ
…[736 chars elided]…
_cause__ = mid  # cycle back into the chain\n\n        def fail() -> None:\n            raise top\n\n        retrying = Retrying(\n            retry=tenacity.retry_if_exception_cause_type(NameError),\n            stop=tenacity.stop_after_attempt(2),\n        )\n        with self.assertRaises(RetryError):\n            retrying(fail)\n\n    def test_retry_preserves_argument_defaults(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "timeout 120 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k cause 2>&1 | tail -15; echo \"exit: $?\"", "description": "Run cause-related tests with timeout"}
[tool_result] (eval):1: command not found: timeout
exit: 0
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k cause 2>&1 | tail -15", "description": "Run cause-related tests"}
[tool_result] .....                                                                    [100%]
5 passed, 130 deselected in 0.05s
[assistant] The targeted tests pass. Next I'll confirm the new tests actually catch the hang on the original code, then run the full suite.
[tool_use Bash] {"command": "git show HEAD:tenacity/retry.py > /tmp/retry_orig.py && cp tenacity/retry.py /tmp/retry_fixed.py && cp /tmp/retry_orig.py tenacity/retry.py && <work>/env-tenacity/bin/python -c \"\nimport faulthandler,sys; faulthandler.dump_traceback_later(5, exit=True)\nimport tenacity\nfrom tenacity import Retrying\ne=ValueError('x'); e.__cause__=e\ndef f(): raise e\nRetrying(retry=tenacity.retry_if_exception_cause_type(NameError), stop=tenacity.stop_after_attempt(1))(f)\n\" 2>&1 | tail -3; cp /tmp/retry_fixed.py tenacity/retry.py && git diff --stat", "description": "Confirm original code hangs on self-cause"}
[tool_result]   File "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tenacity/__init__.py", line 421 in iter
  File "~/.cache/lithify/work/repo-fd67065479be/20261023-162745-bug-retry-if-exception-cause-typ/base-1/tenacity/__init__.py", line 527 in __call__
  File "<string>", line 7 in <module>
 tenacity/retry.py      |  5 ++++-
 tests/test_tenacity.py | 33 +++++++++++++++++++++++++++++++++
 2 files changed, 37 insertions(+), 1 deletion(-)
[assistant] The original code hangs on the self-cause case, as the bug report says, and the fix is restored. Running the full suite now:
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run full project test suite"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.88s
[assistant] `retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains and still finds a matching cause anywhere in a non-cyclic chain. The full suite passes: 173 passed, 1 skipped.

**The fix** (`tenacity/retry.py`): the cause walk now records each exception's `id()` and stops when it reaches one it has already visited. `raise e from e` and mutually-pointing causes both end the walk. Matching behaviour is unchanged for acyclic chains.

**Tests** (`tests/test_tenacity.py`, added after the existing cause-type test; no existing test was touched):
- `test_retry_if_exception_cause_type_self_cause_terminates`: an exception whose cause is itself, with no matching type, returns "don't retry" and re-raises.
- `test_retry_if_exception_cause_type_cycle_with_match`: a cycle that still contains a matching `NameError` retries.

I confirmed the self-cause test hangs on the original code (a faulthandler dump showed the loop), so it guards the bug. I haven't committed anything.
