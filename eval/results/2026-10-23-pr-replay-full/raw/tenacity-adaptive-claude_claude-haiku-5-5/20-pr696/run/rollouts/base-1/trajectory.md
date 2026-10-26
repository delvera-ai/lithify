# trajectory base-1

final message:
Fixed: `@tenacity.retry` now works after `tenacity.tornado = None`. The existing suite passes, and a new regression test covers the case.

**Cause:** `tenacity/__init__.py` computed `_HAS_TORNADO` once at import time, and the decorator checked that snapshot. Setting the global to `None` later left the snapshot `True`, so the code went on to call `tornado.gen` on `None`.

**Change** (`tenacity/__init__.py`, in `retry()`'s `wrap`):
- The decorator now reads the live global: `has_tornado = tornado is not None`, then uses `has_tornado` in the tornado branch.
- I kept it in a local `bool`, not inline in the `and` chain. With tornado installed, mypy under `strict` flags `tornado is not None` as a redundant left operand. The original code avoided that for the same reason.
- `_HAS_TORNADO` stays for the import-time `from tenacity.tornadoweb import TornadoRetrying` gate, where a snapshot is correct.

**Test** (`tests/test_tenacity.py`, in `TestRetryTyping`): `test_retry_decorates_when_tornado_global_is_none` patches `tenacity.tornado` to `None` with `mock.patch.object`, decorates a function, and checks it runs. It fails on the unfixed code with the same `AttributeError` and passes with the fix.

**Verification:**
- Project tests: 179 passed, 1 skipped (baseline was 178 passed, 1 skipped; the difference is the new test).
- mypy: I ran it in a separate venv with tornado, pytest and trio installed. Its output matches HEAD exactly, so the change adds no type errors.
- ruff: one `ICN001` in `tests/test_tenacity.py:17` (`import datetime`). That line is not part of my change, so I left it alone.

I haven't committed anything; the changes are in the working tree for you to review.

## events
[tool_use Bash] {"command": "grep -n \"tornado\" tenacity/__init__.py | head -50", "description": "Find tornado references in tenacity/__init__.py"}
[tool_result] 88:    import tornado
90:    tornado = None  # type: ignore[assignment]
92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
95:_HAS_TORNADO = tornado is not None
790:            and hasattr(tornado.gen, "is_coroutine_function")
791:            and tornado.gen.is_coroutine_function(f)
805:    from tenacity.tornadoweb import TornadoRetrying
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "offset": 80, "limit": 20}
[tool_result] 80	    wait_incrementing,
81	    wait_none,
82	    wait_random,
83	    wait_random_exponential,
84	)
85	from .wait import wait_random_exponential as wait_full_jitter
86	
87	try:
88	    import tornado
89	except ImportError:
90	    tornado = None  # type: ignore[assignment]
91	
92	# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
93	# so testing the module object for truthiness reads as an always-true check.
94	# Keep the availability answer in a plain bool instead.
95	_HAS_TORNADO = tornado is not None
96	
97	if t.TYPE_CHECKING:
98	    if sys.version_info >= (3, 11):
99	        from typing import Self
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "offset": 775, "limit": 45}
[tool_result] 775	    def wrap(f: t.Callable[P, R]) -> _RetryDecorated[P, R]:
776	        if isinstance(f, retry_base):
777	            warnings.warn(
778	                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
779	                f"this will probably hang indefinitely (did you mean retry={f.__class__.__name__}(...)?)",
780	                stacklevel=2,
781	            )
782	        r: BaseRetrying
783	        sleep = dkw.get("sleep")
784	        if _utils.is_coroutine_calla
…[434 chars elided]…
*dargs, **dkw)
796	
797	        return r.wraps(f)
798	
799	    return wrap
800	
801	
802	from tenacity.asyncio import AsyncRetrying  # noqa: E402
803	
804	if _HAS_TORNADO:
805	    from tenacity.tornadoweb import TornadoRetrying
806	
807	
808	__all__ = [
809	    "NO_RESULT",
810	    "AsyncRetrying",
811	    "AttemptManager",
812	    "BaseAction",
813	    "BaseRetrying",
814	    "DoAttempt",
815	    "DoSleep",
816	    "Future",
817	    "RetryAction",
818	    "RetryCallState",
819	    "RetryError",
[assistant] The cause is visible: `_HAS_TORNADO` is computed once at import, so the decorator never sees the later `tornado = None`. Before changing it, I'll check how the tests use the global and what the mypy config says about the `is not None` check.
[tool_use Bash] {"command": "grep -rn \"_HAS_TORNADO\\|tornado = None\\|tornado\\.\\(gen\\|__\\)\" --include=*.py . | grep -v \"^./.git/\" ; grep -n -A12 \"\\[tool.mypy\\]\" pyproject.toml setup.cfg mypy.ini 2>/dev/null; ls <work>/env-tenacity/bin/python 2>&1", "description": "Search for tornado flag uses and mypy config"}
[tool_result] (eval):1: no matches found: --include=*.py
115:[tool.mypy]
116-strict = true
117-# Match `requires-python`, so results do not depend on which interpreter
118-# happens to run mypy. Without this it defaults to the running version and
119-# silently skips checking that the code is valid on the oldest one we support.
120-python_version = "3.10"
121-files = ["tenacity", "tests"]
122-show_error_codes = true
123-exclude = ["tenacity/_version\\.py"]
124-# `strict` is not "everything" -- these are checks it leaves off.
125-warn_unreachable = true
126-disallow_any_unimported = true
127-extra_checks = true
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "grep -rn \"_HAS_TORNADO\\|tornado = None\\|tornado\\.gen\" tenacity tests | head -30", "description": "Search tenacity and tests for tornado usages"}
[tool_result] tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:789:            _HAS_TORNADO
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:804:if _HAS_TORNADO:
[assistant] Tests don't touch the flag today, so the fix belongs in the decorator. I'll run the baseline test suite first, then make the change.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run baseline test suite"}
[tool_result] ................s................................................................................................................ [ 72%]
..................................................                       [100%]
178 passed, 1 skipped, 15 subtests passed in 1.88s
[assistant] Baseline is green (178 passed, 1 skipped). Next, a reproduction of the bug.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint(f())\n\" 2>&1 | tail -3", "description": "Reproduce the AttributeError"}
[tool_result]     and hasattr(tornado.gen, "is_coroutine_function")
                ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'gen'
[assistant] Reproduced. The fix is to read the live `tornado` global at decoration time instead of the import-time `_HAS_TORNADO` snapshot. I'll keep `_HAS_TORNADO` only for the import-time gate at line 804, where a snapshot is correct.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "old_string": "        elif (\n            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "        elif (\n            tornado is not None\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py has been updated successfully.
[assistant] The `_HAS_TORNADO` comment now describes the wrong thing, so I'll check what mypy says about the new `is not None` check before rewriting it.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m mypy --version 2>&1; $PY -m mypy 2>&1 | tail -15; $PY -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint(f(), type(f).__name__)\nasync def g(): return 1\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Run mypy, repro again, and test suite"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named mypy
1 function
..................................................                       [100%]
178 passed, 1 skipped, 15 subtests passed in 1.84s
[assistant] The fix works: the repro now decorates and runs, and the suite still passes. mypy isn't in the project env, so I'll install it in a separate throwaway venv to check the strict config. I'll also look for the existing tornado tests so a regression test can sit beside them.
[tool_use Bash] {"command": "(python3 -m venv /tmp/mypy-venv-tenacity && /tmp/mypy-venv-tenacity/bin/pip install -q mypy 2>&1 | tail -2; /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | tail -8) ; grep -rln \"tornado\" tests | head; git stash list --format='%H %gs' | head -3", "description": "Install mypy in temp venv and run it; find tornado tests"}
[tool_result] [notice] A new release of pip is available: 25.0.1 -> 26.2.2
[notice] To update, run: python3.12 -m pip install --upgrade pip
tests/test_tornado.py:34: error: Untyped decorator makes function "_retryable_coroutine_with_2_attempts" untyped  [untyped-decorator]
tests/test_tornado.py:42: error: Class cannot subclass "AsyncTestCase" (has type "Any")  [misc]
tests/test_tornado.py:42: error: Base type AsyncTestCase becomes "Any" due to an unfollowed import  [no-any-unimported]
tests/test_tornado.py:43
…[21 chars elided]…
rator makes function "test_retry" untyped  [untyped-decorator]
tests/test_tornado.py:50: error: Untyped decorator makes function "test_stop_after_attempt" untyped  [untyped-decorator]
tests/test_asyncio.py:24: error: Cannot find implementation or library stub for module named "trio"  [import-not-found]
tests/test_asyncio.py:30: error: Cannot find implementation or library stub for module named "pytest"  [import-not-found]
Found 23 errors in 6 files (checked 19 source files)
tests/test_tornado.py
[assistant] The bare venv lacks tornado, pytest and trio, so those errors are environmental. To see whether my edit adds anything, I'll compare mypy output against a clean export of HEAD.
[tool_use Bash] {"command": "rm -rf /tmp/base-tenacity-head && mkdir /tmp/base-tenacity-head && git archive HEAD | tar -x -C /tmp/base-tenacity-head && (cd /tmp/base-tenacity-head && /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-base.txt); /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-new.txt; diff /tmp/mypy-base.txt /tmp/mypy-new.txt && echo \"IDENTICAL mypy output (modulo line numbers)\"; grep \"tenacity/__init__\" /tmp/mypy-new.txt", "description": "Diff mypy output against HEAD export"}
[tool_result] IDENTICAL mypy output (modulo line numbers)
tenacity/__init__.py: error: Cannot find implementation or library stub for module named "tornado"  [import-not-found]
tenacity/__init__.py: error: Unused "type: ignore" comment  [unused-ignore]
tenacity/__init__.py: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
[assistant] Those three tenacity lines come from tornado not being installed in that venv, and they appear identically in HEAD. With tornado unresolved mypy sees `Any`, which hides the question that matters: whether `tornado is not None` trips strict-equality once the real module type is visible. I'll install tornado and re-check.
[tool_use Bash] {"command": "/tmp/mypy-venv-tenacity/bin/pip install -q tornado pytest trio 2>&1 | grep -v notice | tail -2; (cd /tmp/base-tenacity-head && /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-base.txt); /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-new.txt; diff /tmp/mypy-base.txt /tmp/mypy-new.txt && echo \"IDENTICAL\"; echo \"--- new-file tenacity errors:\"; grep \"tenacity/__init__\" /tmp/mypy-new.txt; /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | tail -1", "description": "Install tornado deps and diff mypy output again"}
[tool_result] 1c1,2
< Success: no issues found in 19 source files
---
> Found 1 error in 1 file (checked 19 source files)
> tenacity/__init__.py: error: Left operand of "and" is always true  [redundant-expr]
--- new-file tenacity errors:
tenacity/__init__.py: error: Left operand of "and" is always true  [redundant-expr]
Found 1 error in 1 file (checked 19 source files)
[assistant] With tornado visible, mypy flags `tornado is not None` as a redundant left operand of `and`. That's why the original code kept a bool. I'll keep the live read but store it in a local `bool` first, which avoids the redundant-expression check without a type-ignore.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "old_string": "        sleep = dkw.get(\"sleep\")\n        if _utils.is_coroutine_callable(f) or (\n            sleep is not None and _utils.is_coroutine_callable(sleep)\n        ):\n            r = AsyncRetrying(*dargs, **dkw)\n  
…[256 chars elided]…
 `tenacity.tornado = None` at runtime is honoured by later decorations.\n        has_tornado = tornado is not None\n        if _utils.is_coroutine_callable(f) or (\n            sleep is not None and _utils.is_coroutine_callable(sleep)\n        ):\n            r = AsyncRetrying(*dargs, **dkw)\n        elif (\n            has_tornado\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "/tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-new.txt; diff /tmp/mypy-base.txt /tmp/mypy-new.txt && echo \"mypy: IDENTICAL to HEAD\"; PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint('decorated ok:', f())\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Re-run mypy diff, repro, and test suite"}
[tool_result] mypy: IDENTICAL to HEAD
decorated ok: 1
178 passed, 1 skipped, 15 subtests passed in 1.88s
[assistant] Mypy output matches HEAD, the repro passes, and the suite is green. Now a regression test. I'll check the existing test layout first so it matches.
[tool_use Bash] {"command": "ls tests; grep -n \"^import\\|^from\\|monkeypatch\" tests/test_tenacity.py | head -30; grep -n \"def test_retry_decorator\\|def test_.*decor\" tests/*.py | head", "description": "Inspect test file layout and decorator tests"}
[tool_result] __init__.py
__pycache__
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
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
29:import tenacity
30:from tenacity import RetryCallState, RetryError, Retrying, retry
31:from tenacity._utils import override
32:from tenacity.retry import retry
…[227 chars elided]…
 None:
tests/test_tenacity.py:1623:    def test_statistics_visible_through_outer_decorator(self) -> None:
tests/test_tenacity.py:2252:    def test_retry_decorated_method_keeps_bound_signature(self) -> None:
tests/test_tenacity.py:2302:    def test_decorated(self, mock_sleep: typing.Any) -> None:
tests/test_tenacity.py:2307:    def test_decorated_retry_with(self, mock_sleep: typing.Any) -> None:
tests/test_asyncio.py:126:    async def test_statistics_visible_through_outer_decorator(self) -> None:
[tool_use Bash] {"command": "sed -n 2248,2300p tests/test_tenacity.py", "description": "Read decorator test section for style"}
[tool_result]         self.assertEqual(with_raw_result, "1")
        self.assertEqual(with_constructor_result, "1")

    def test_retry_decorated_method_keeps_bound_signature(self) -> None:
        """A decorated instance method must type-check like a bound method.

        Without a descriptor (``__get__``) on ``_RetryDecorated``, static type
        checkers treat ``instance.method`` the same as the unbound
        ``Class.method``, so a normal call with only the non-``self`` keyword
        arguments looks
…[851 chars elided]…
, untyped-decorator]
    def _decorated_fail(self) -> None:
        self._fail()

    @pytest.fixture()
    def mock_sleep(
        self, monkeypatch: typing.Any
    ) -> typing.Generator[typing.Any, None, None]:
        class MockSleep:
            call_count = 0

            def __call__(self, seconds: float) -> None:
                self.call_count += 1

        sleep = MockSleep()
        monkeypatch.setattr(tenacity.nap.time, "sleep", sleep)  # type: ignore[attr-defined]
        yield sleep
[assistant] I'll add the test to the same class, right after the existing decorator test, using `mock.patch.object` to set the global to `None` and restore it afterwards.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tests/test_tenacity.py", "old_string": "        doubler = Doubler()\n        result: int = doubler.double(value=21)\n        self.assertEqual(result, 42)\n", "new_string": "        doubler = Doubler()\n        result: int = doubler.double(value=21)\n    
…[224 chars elided]…
rnado path by setting\n        ``tenacity.tornado = None`` instead of uninstalling tornado. Decorating\n        after that must not touch ``tornado.gen``.\n        \"\"\"\n        with mock.patch.object(tenacity, \"tornado\", None):\n\n            @retry(stop=tenacity.stop_after_attempt(2))\n            def succeeds() -> int:\n                return 7\n\n        self.assertEqual(succeeds(), 7)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163312-bug-setting-the-module-global-te/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next I'll confirm the new test fails against the unfixed code, using the HEAD export with only the new test file copied in. Then I'll run the full suite and mypy on the test file.
[tool_use Bash] {"command": "cp tests/test_tenacity.py /tmp/base-tenacity-head/tests/test_tenacity.py && (cd /tmp/base-tenacity-head && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k tornado_global 2>&1 | tail -3); echo \"--- with fix:\";
…[71 chars elided]…
hify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; /tmp/mypy-venv-tenacity/bin/mypy 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/mypy-new.txt; diff /tmp/mypy-base.txt /tmp/mypy-new.txt && echo \"mypy: IDENTICAL to HEAD (incl. tests/)\"", "description": "Verify test fails on HEAD, passes with fix, mypy clean"}
[tool_result] =========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestRetryTyping::test_retry_decorates_when_tornado_global_is_none
1 failed, 139 deselected in 0.07s
--- with fix:
179 passed, 1 skipped, 15 subtests passed in 1.87s
mypy: IDENTICAL to HEAD (incl. tests/)
[assistant] The new test fails on the unfixed code and passes with the fix, and mypy output is unchanged from HEAD. Last, lint and the final diff.
[tool_use Bash] {"command": "(which ruff >/dev/null 2>&1 && ruff check tenacity tests && ruff format --check tenacity tests) ; /tmp/mypy-venv-tenacity/bin/pip install -q ruff 2>&1 | grep -v notice; /tmp/mypy-venv-tenacity/bin/ruff check tenacity tests 2>&1 | tail -2; /tmp/mypy-venv-tenacity/bin/ruff format --check tenacity tests 2>&1 | tail -2; rm -rf /tmp/base-tenacity-head; git status --short; git diff", "description": "Run ruff checks and show final diff"}
[tool_result] Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
19 files already formatted
 M tenacity/__init__.py
 M tests/test_tenacity.py
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 51925ef..65d7485 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -781,12 +781,15 @@ def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
             )
         r: BaseRetrying
         sleep = dkw.get("sleep")
+        # Read the live module global rather than `_HAS_TORNADO`, so 
…[940 chars elided]…
tornado`` global.
+
+        Test suites exercise the non-tornado path by setting
+        ``tenacity.tornado = None`` instead of uninstalling tornado. Decorating
+        after that must not touch ``tornado.gen``.
+        """
+        with mock.patch.object(tenacity, "tornado", None):
+
+            @retry(stop=tenacity.stop_after_attempt(2))
+            def succeeds() -> int:
+                return 7
+
+        self.assertEqual(succeeds(), 7)
+
 
 class TestMockingSleep:
     RETRY_ARGS = {
[assistant] Ruff reports one error. I need to see whether it comes from my change or already exists.
[tool_use Bash] {"command": "/tmp/mypy-venv-tenacity/bin/ruff check tenacity tests --output-format concise 2>&1 | head -3; git stash list >/dev/null; git show HEAD:tenacity/__init__.py > /tmp/head_init.py; git show HEAD:tests/test_tenacity.py > /tmp/head_test.py; mkdir -p /tmp/ruffcheck/tenacity /tmp/ruffcheck/tests && cp /tmp/head_init.py /tmp/ruffcheck/tenacity/__init__.py && cp /tmp/head_test.py /tmp/ruffcheck/tests/test_tenacity.py && (cd /tmp/ruffcheck && /tmp/mypy-venv-tenacity/bin/ruff check tenacity tests --output-format concise 2>&1 | head -3); rm -rf /tmp/ruffcheck /tmp/head_init.py /tmp/head_test.py", "description": "Identify ruff error and check whether HEAD has it"}
[tool_result] tests/test_tenacity.py:17:8: ICN001 `datetime` should be imported as `dt`
Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
tenacity/__init__.py:98:8: UP036 Version block is outdated for minimum Python version
tenacity/__init__.py:101:9: UP035 [*] Import from `typing` instead: `Self`
tenacity/__init__.py:251:29: B008 Do not perform function call `wait_none` in argument defaults; instead, perform the call within the function, or read the default from a module-level singleton variable
[assistant] Fixed: `@tenacity.retry` now works after `tenacity.tornado = None`. The existing suite passes, and a new regression test covers the case.

**Cause:** `tenacity/__init__.py` computed `_HAS_TORNADO` once at import time, and the decorator checked that snapshot. Setting the global to `None` later left the snapshot `True`, so the code went on to call `tornado.gen` on `None`.

**Change** (`tenacity/__init__.py`, in `retry()`'s `wrap`):
- The decorator now reads the live global: `has_tornado = tornado is not None`, then uses `has_tornado` in the tornado branch.
- I kept it in a local `bool`, not inli
…[492 chars elided]…
nction, and checks it runs. It fails on the unfixed code with the same `AttributeError` and passes with the fix.

**Verification:**
- Project tests: 179 passed, 1 skipped (baseline was 178 passed, 1 skipped; the difference is the new test).
- mypy: I ran it in a separate venv with tornado, pytest and trio installed. Its output matches HEAD exactly, so the change adds no type errors.
- ruff: one `ICN001` in `tests/test_tenacity.py:17` (`import datetime`). That line is not part of my change, so I left it alone.

I haven't committed anything; the changes are in the working tree for you to review.
