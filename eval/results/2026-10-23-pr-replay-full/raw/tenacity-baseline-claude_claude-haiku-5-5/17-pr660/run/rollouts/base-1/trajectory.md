# trajectory base-1

final message:
`retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains and still finds a matching type anywhere in a non-cyclic chain. The full suite passes: 173 passed, 1 skipped.

**The cause:** the loop in `tenacity/retry.py` followed `__cause__` with no record of which exceptions it had already visited. With `raise e from e`, or two exceptions pointing at each other, it cycled forever and never returned.

**The fix:** the loop now keeps a set of visited exception ids and stops when it sees one again. The change is 3 lines in `tenacity/retry.py`.

**Tests added** in `tests/test_tenacity.py`, next to the existing cause-type test:
- A self-cause (`e.__cause__ = e`) with a non-matching type returns without retrying and re-raises.
- A mutual cause loop with a non-matching type behaves the same way.
- A cycle that also contains a `NameError` still matches and retries until the stop condition.

I did not run the new hang tests against the unfixed code, since they would hang there. The fix was checked by reading the loop, not by reproducing the old behaviour.

I did not add a release note under `releasenotes/notes/`, since you didn't ask for one. Say if you want one.

## events
[tool_use Bash] {"command": "grep -rn \"cause\" --include=*.py . | grep -v \"/\\.git/\" | head -50", "description": "Search for cause-chain code in Python sources"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"cause\" . --exclude-dir=.git | grep -v \"because\" | head -60", "description": "Search repo for cause references"}
[tool_result] LICENSE:19:      "control" means (i) the power, direct or indirect, to cause the
LICENSE:98:      (b) You must cause any modified files to carry prominent notices
tests/test_asyncio.py:297:    async def test_reraise_try_again_with_cause(self) -> None:
tests/test_tenacity.py:875:    def test_retry_try_again_with_cause_reraise(self) -> None:
tests/test_tenacity.py:896:    def test_retry_try_again_from_cause_reraise(self) -> None:
tests/test_tenacity.py:1024:        """Raise an IOError with a NameE
…[2118 chars elided]…
se_type` that
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml:5:    checks, recursively, if any of the causes of the raised exception is of a certain type.
releasenotes/notes/add-stop-before-delay-a775f88ac872c923.yaml:5:    if the next sleep time would cause overall delay to exceed the specified delay. 
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "offset": 150, "limit": 50}
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

…[967 chars elided]…
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "offset": 1010, "limit": 60}
[tool_result] 1010	        return True
1011	
1012	
1013	class NoNameErrorCauseAfterCount:
1014	    """Holds counter state for invoking a method several times in a row."""
1015	
1016	    def __init__(self, count: int) -> None:
1017	        self.counter = 0
1018	        self.count = count
1019	
1020	    def go2(self) -> typing.Any:
1021	        raise NameError("Hi there, I'm a NameError")
1022	
1023	    def go(self) -> typing.Any:
1024	        """Raise an IOError with a NameError as cause until after count thre
…[886 chars elided]…
 self.counter < self.count:
1054	            self.counter += 1
1055	            try:
1056	                self.go2()
1057	            except OSError as e:
1058	                raise NameError from e
1059	
1060	        return True
1061	
1062	
1063	class NameErrorUntilCount:
1064	    """Holds counter state for invoking a method several times in a row."""
1065	
1066	    derived_message = "Hi there, I'm a NameError"
1067	
1068	    def __init__(self, count: int) -> None:
1069	        self.counter = 0
[assistant] The bug is in `retry_if_exception_cause_type.__call__`: the `while` loop follows `__cause__` with no visited check, so a cycle never exits. I'll add cycle detection and a regression test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py", "old_string": "            exc = retry_state.outcome.exception()\n            while exc is not None:\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = ex
…[35 chars elided]…
      exc = retry_state.outcome.exception()\n            # Track visited exceptions so that cyclic cause chains terminate.\n            seen: set[int] = set()\n            while exc is not None and id(exc) not in seen:\n                seen.add(id(exc))\n                if isinstance(exc.__cause__, self.exception_cause_types):\n                    return True\n                exc = exc.__cause__"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "offset": 1420, "limit": 30}
[tool_result] 1420	            self.fail("CustomError should've been retried from errormessage")
1421	
1422	    def test_retry_if_not_exception_message_match(self) -> None:
1423	        try:
1424	            self.assertTrue(
1425	                _retryable_test_if_not_exception_message_message(
1426	                    NoCustomErrorAfterCount(2)
1427	                )
1428	            )
1429	        except CustomError:
1430	            s = _retryable_test_if_not_exception_message_message.statistics
1431	     
…[249 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"RetryCallState\\|^from\\|^import\" tests/test_tenacity.py | head -30", "description": "Check test imports and RetryCallState usage"}
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
46:def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
59:) -> RetryCallSta
…[348 chars elided]…
tryCallState(r, None, (), {})
274:        def stop_func(retry_state: RetryCallState) -> bool:
432:        def wait_func(retry_state: RetryCallState) -> typing.Any:
682:        def waitfunc(retry_state: RetryCallState) -> float:
804:        def my_retry(retry_state: tenacity.RetryCallState) -> bool:
821:        def my_retry(retry_state: tenacity.RetryCallState) -> bool:
1691:        def return_text(retry_state: RetryCallState) -> str:
1708:        def _before(retry_state: RetryCallState) -> None:
[tool_use Bash] {"command": "sed -n 140,165p tests/test_tenacity.py", "description": "Read existing retry_state test construction"}
[tool_result]         def my_func() -> None:
            raise ValueError

        with contextlib.suppress(Exception):
            my_func()
        assert captured
        assert "my_func" in captured[0].get_fn_name()

    def test_get_fn_name_context_manager_no_name(self) -> None:
        """get_fn_name() returns '<unknown>' in context manager mode without a name."""
        r = Retrying(stop=tenacity.stop_after_attempt(1))
        rs = RetryCallState(r, None, (), {})
        assert rs.get_fn_name() == "<u
…[64 chars elided]…
f) -> None:
        """get_fn_name() returns the given name in context manager mode."""
        r = Retrying(name="ws_listener", stop=tenacity.stop_after_attempt(1))
        rs = RetryCallState(r, None, (), {})
        assert rs.get_fn_name() == "ws_listener"

    def test_logging_uses_name(self) -> None:
        """before_log uses the name parameter in context manager mode."""
        import unittest.mock

        log = unittest.mock.MagicMock()
        logger = unittest.mock.MagicMock(log=log)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py", "old_string": "        except NameError:\n            pass\n\n    def test_retry_preserves_argument_defaults(self) -> None:", "new_string": "        except NameError:\n            pass\n\n    def test_retry_if_exception_cause_typ
…[1380 chars elided]…
eError(\"match\")\n            os_error = OSError(\"cycle\")\n            os_error.__cause__ = name_error\n            name_error.__cause__ = os_error\n            raise os_error\n\n        with pytest.raises(tenacity.RetryError):\n            cyclic_with_match()\n        assert cyclic_with_match.statistics[\"attempt_number\"] == 2\n\n    def test_retry_preserves_argument_defaults(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192500-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the project's checks using the command from the project instructions.
[tool_use Bash] {"command": "timeout 300 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Run project test suite"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Run project test suite"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.86s
[tool_use Bash] {"command": "git diff --stat && git diff tenacity/retry.py", "description": "Show diff stat and retry.py change"}
[tool_result]  tenacity/retry.py      |  5 ++++-
 tests/test_tenacity.py | 49 +++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 53 insertions(+), 1 deletion(-)
diff --git a/tenacity/retry.py b/tenacity/retry.py
index e59f4c0..00336d0 100644
--- a/tenacity/retry.py
+++ b/tenacity/retry.py
@@ -177,7 +177,10 @@ class retry_if_exception_cause_type(retry_base):
 
         if retry_state.outcome.failed:
             exc = retry_state.outcome.exception()
-            while exc is not None:
+            # Track visited exceptions so that cyclic cause chains terminate.
+            seen: set[int] = set()
+            while exc is not None and id(exc) not in seen:
+                seen.add(id(exc))
                 if isinstance(exc.__cause__, self.exception_cause_types):
                     return True
                 exc = exc.__cause__
[assistant] `retry_if_exception_cause_type` now terminates on cyclic `__cause__` chains and still finds a matching type anywhere in a non-cyclic chain. The full suite passes: 173 passed, 1 skipped.

**The cause:** the loop in `tenacity/retry.py` followed `__cause__` with no record of which exceptions it had already visited. With `raise e from e`, or two exceptions pointing at each other, it cycled forever and never returned.

**The fix:** the loop now keeps a set of visited exception ids and stops when it sees one again. The change is 3 lines in `tenacity/retry.py`.

**Tests added** in `tests/test_tenacity.py`, next to the existing cause-type test:
- A self-cause (`e.__cause__ = e`) with a non-matching type returns without retrying and re-raises.
- A mutual cause loop with a non-matching type behaves the same way.
- A cycle that also contains a `NameError` still matches and retries until the stop condition.

I did not run the new hang tests against the unfixed code, since they would hang there. The fix was checked by reading the loop, not by reproducing the old behaviour.

I did not add a release note under `releasenotes/notes/`, since you didn't ask for one. Say if you want one.
