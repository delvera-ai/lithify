# trajectory base-1

final message:
Composing a `retry_base` with a plain callable works again for `|` and `&`, in both operand orders, for sync and async strategies. The full suite passes: 138 passed, 1 skipped.

**Cause:** In `tenacity/retry.py`, the sync `retry_base.__or__` and `__and__` delegate to `other.__ror__` / `other.__rand__`. A plain function has neither, so `retry_if_exception_type(IOError) | my_predicate` raised `AttributeError`. The reflected forms (`my_predicate | retry_...`) already worked, and the async classes build `retry_any`/`retry_all` directly, so they were never affected.

**Changes (uncommitted):**
- `tenacity/retry.py`: `__and__` and `__or__` dispatch to the reflected method only when `other` is a `retry_base`. Otherwise they build `retry_all(self, other)` / `retry_any(self, other)` directly.
- `tenacity/retry.py` and `tenacity/asyncio/retry.py`: the operator annotations now accept plain callables (`RetryBaseT`) as well as strategy objects.
- `tests/test_tenacity.py`: `test_retry_or_and_with_plain_callable` checks both orders of `|` and `&` with a plain predicate and asserts the result type and truth values.
- `tests/test_asyncio.py`: `test_retry_with_plain_callable_composition` covers the async path.

**Verification:**
- Against the original `retry.py`, the new sync test fails with the reported `AttributeError`.
- Against the fix, all eight combinations (sync and async, both orders, `|` and `&`) return `retry_any` / `retry_all`.
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. The annotations are unchecked by a type checker.

I haven't committed. Say if you want a commit on a branch.

## events
[assistant] I'll start by finding the `|` and `&` composition code in the retry base.
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn \"__or__\\|__and__\\|retry_any\\|retry_all\\|class retry_base\" tenacity/ | head -50", "description": "Locate composition operators and retry_base in tenacity"}
[tool_result] 34d80e4 lithify: probe base
44afaca eval setup at 42b70f90790e
42b70f9 fix: initialize delay_since_first_attempt in statistics on begin() (#603)
tenacity/stop.py:34:    def __and__(self, other: "stop_base") -> "stop_all":
tenacity/stop.py:37:    def __or__(self, other: "stop_base") -> "stop_any":
tenacity/retry.py:25:class retry_base(abc.ABC):
tenacity/retry.py:32:    def __and__(self, other: "retry_base") -> "retry_all":
tenacity/retry.py:35:    def __rand__(self, other: "retry_base") -> "retry
…[985 chars elided]…
nacity/asyncio/retry.py:40:        return retry_all(other, self)
tenacity/asyncio/retry.py:42:    def __or__(  # type: ignore[override]
tenacity/asyncio/retry.py:44:    ) -> "retry_any":
tenacity/asyncio/retry.py:45:        return retry_any(self, other)
tenacity/asyncio/retry.py:49:    ) -> "retry_any":
tenacity/asyncio/retry.py:50:        return retry_any(other, self)
tenacity/asyncio/retry.py:95:class retry_any(async_retry_base):
tenacity/asyncio/retry.py:110:class retry_all(async_retry_base):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/retry.py"}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITH
…[8649 chars elided]…
    self.retries = retries
259	
260	    def __call__(self, retry_state: "RetryCallState") -> bool:
261	        return any(r(retry_state) for r in self.retries)
262	
263	
264	class retry_all(retry_base):
265	    """Retries if all the retries condition are valid."""
266	
267	    def __init__(self, *retries: retry_base) -> None:
268	        self.retries = retries
269	
270	    def __call__(self, retry_state: "RetryCallState") -> bool:
271	        return all(r(retry_state) for r in self.retries)
272	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/asyncio/retry.py"}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITH
…[3481 chars elided]…
ies if all the retries condition are valid."""
112	
113	    def __init__(self, *retries: retry_base | async_retry_base) -> None:
114	        self.retries = retries
115	
116	    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
117	        result = True
118	        for r in self.retries:
119	            result = result and await _utils.wrap_to_async_func(r)(retry_state)
120	            if not result:
121	                break
122	        return result
123	
[assistant] The sync `retry_base.__or__`/`__and__` delegate to `other.__ror__`/`other.__rand__`, which a plain function doesn't have. The async class overrides these and builds `retry_any`/`retry_all` directly. I'll check how this changed across releases and how `RetryBaseT` is used before editing.
[tool_use Bash] {"command": "git log --oneline -8 -- tenacity/retry.py && git tag | tail -5; git log -L32,42:tenacity/retry.py --oneline | head -80; grep -rn \"RetryBaseT\" tenacity/ | head; ls tests/ | head -30", "description": "Inspect retry.py history and RetryBaseT usage"}
[tool_result] fea6430 refactor: replace deprecated typing.Pattern with re.Pattern (#589)
9686ed7 refactor: enable additional ruff rules and fix violations (#584)
c4bada4 chore: enable ruff I, UP, B rules and auto-fix codebase (#571)
a44271f fix: Add re.Pattern to allowed match types (#497)
21137e7 Add async strategies (#451)
0b76e7c ci: replace black and flake8 by ruff
d9438b3 fix(mypy): add missing typing (#384)
c0fc691 ci: add mypy
v1.2.3
v1.3.0
v1.3.1
v1.3.2
v1.3.3
21137e7 Add async strategies (#451)

diff
…[1856 chars elided]…
_exception_type(),
tenacity/__init__.py:100:    from .retry import RetryBaseT
tenacity/__init__.py:224:        retry: "RetryBaseT" = retry_if_exception_type(),
tenacity/__init__.py:651:    retry: "RetryBaseT | tasyncio.retry.RetryBaseT" = ...,
tenacity/__init__.py:667:    retry: "RetryBaseT | tasyncio.retry.RetryBaseT" = retry_if_exception_type(),
tenacity/asyncio/retry.py:53:RetryBaseT = (
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[assistant] The `other.__ror__` dispatch was added in the 8.4.x line, which matches the regression window. Next I'll reproduce the bug with the project's test interpreter from CLAUDE.md.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; cat > /tmp/repro_compose.py <<'EOF'\nimport asyncio\nfrom tenacity import retry_if_exception_type, retry_any, retry_all, retry_never\nfrom tenacity.asyncio import retry_if_exception_type as aret\ndef pred(state)
…[434 chars elided]…
 | aret(IOError)),\n    (\"async base&fn\", lambda: aret(IOError) & pred),\n    (\"async fn&base\", lambda: pred & aret(IOError)),\n]:\n    try:\n        r = expr()\n        print(name, \"->\", type(r).__name__)\n    except Exception as e:\n        print(name, \"RAISED\", type(e).__name__, e)\nEOF\n$PY -I /tmp/repro_compose.py", "description": "Reproduce composition failures with plain callables"}
[tool_result ERROR] Exit code 1
lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "/tmp/repro_compose.py", line 2, in <module>
    from tenacity import retry_if_exception_type, retry_any, retry_all, retry_never
ModuleNotFoundError: No module named 'tenacity'
[assistant] The venv doesn't have tenacity installed, and `-I` ignores `PYTHONPATH`. I'll point `PYTHONPATH` at the worktree (the repo is trusted here, not a downloaded archive) and run without `-I`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_compose.py; echo ---; $PY -c \"import tenacity,sys;print(tenacity.__file__, sys.version)\"; PYTHONPATH=$PWD $PY -m pytest --version 2>&1 | tail -1", "description": "Run repro with worktree on PYTHONPATH"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_compose.py", line 3, in <module>
    from tenacity.asyncio import retry_if_exception_type as aret
ImportError: cannot import name 'retry_if_exception_type' from 'tenacity.asyncio' (~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/asyncio/__init__.py). Did you mean: 'retry_if_exception'?
---
~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/__init__.py 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
pytest 9.1.1
[assistant] The async module doesn't export `retry_if_exception_type`, so I'll use the async `retry_if_exception` directly in the repro.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/repro_compose.py <<'EOF'\nfrom tenacity import retry_if_exception_type, retry_base\nfrom tenacity.asyncio import retry_if_exception\ndef pred(state):\n    return False\nasync def apred(exc):\n    return False\ndef are
…[546 chars elided]…
ror)),\n    (\"async base&fn\", lambda: aret(IOError) & pred),\n    (\"async fn&base\", lambda: pred & aret(IOError)),\n]\nfor name, expr in cases:\n    try:\n        print(name, \"->\", type(expr()).__name__)\n    except Exception as e:\n        print(name, \"RAISED\", type(e).__name__, e)\nEOF\nPYTHONPATH=$PWD $PY /tmp/repro_compose.py", "description": "Rerun repro with corrected async imports"}
[tool_result] sync  base|fn RAISED AttributeError 'function' object has no attribute '__ror__'
sync  fn|base -> retry_any
sync  base&fn RAISED AttributeError 'function' object has no attribute '__rand__'
sync  fn&base -> retry_all
async base|fn -> retry_any
async fn|base -> retry_any
async base&fn -> retry_all
async fn&base -> retry_all
[assistant] Reproduced. Sync `retry_base | fn` and `retry_base & fn` raise `AttributeError` because they delegate to `other.__ror__`/`__rand__`, which a plain function lacks. The reflected forms and all async forms already work. Fix: in the sync base, dispatch only when `other` is a `retry_base`, and otherwise build the combinator directly. I'll also widen the annotations.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/retry.py", "old_string": "    def __and__(self, other: \"retry_base\") -> \"retry_all\":\n        return other.__rand__(self)\n\n    def __rand__(self, other: \"retry_base\") -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __
…[395 chars elided]…
\n\n    def __rand__(self, other: \"RetryBaseT\") -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __or__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        if isinstance(other, retry_base):\n            return other.__ror__(self)\n        return retry_any(self, other)\n\n    def __ror__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        return retry_any(other, self)"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/retry.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/asyncio/retry.py", "old_string": "    def __and__(  # type: ignore[override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_all\":\n        return retry_all(self, other)\n\n    def __rand__(  # type: ignore[misc,overri
…[647 chars elided]…
n        self, other: \"retry_base | RetryBaseT\"\n    ) -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __or__(  # type: ignore[override]\n        self, other: \"retry_base | RetryBaseT\"\n    ) -> \"retry_any\":\n        return retry_any(self, other)\n\n    def __ror__(  # type: ignore[misc,override]\n        self, other: \"retry_base | RetryBaseT\"\n    ) -> \"retry_any\":"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tenacity/asyncio/retry.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Both edits are in. Next I'll rerun the repro, then the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_compose.py; echo ---; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Rerun repro and full project test suite"}
[tool_result] sync  base|fn -> retry_any
sync  fn|base -> retry_any
sync  base&fn -> retry_all
sync  fn&base -> retry_all
async base|fn -> retry_any
async fn|base -> retry_any
async base&fn -> retry_all
async fn&base -> retry_all
---
...........s................................................ [ 43%]
........................................................................ [ 96%]
.....                                                                    [100%]
136 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] All eight combinations now return the right type, and the suite passes. Next I'll look at the existing operator tests so the new regression tests follow their style.
[tool_use Bash] {"command": "grep -n \"retry_any\\|retry_all\\| | \\| & \" tests/test_tenacity.py tests/test_asyncio.py | head -40", "description": "Find existing retry composition tests"}
[tool_result] tests/test_asyncio.py:309:            retry_strategy = tasyncio.retry_if_result(lt_3) | retry_if_exception(is_exc)
tests/test_asyncio.py:340:            retry_strategy = retry_if_result(lt_3) | tasyncio.retry_if_exception(is_exc)
tests/test_asyncio.py:368:            retry_strategy = tasyncio.retry_if_result(lt_3) & retry_if_result(gt_0)
tests/test_asyncio.py:391:            retry_strategy = retry_if_result(gt_0) & tasyncio.retry_if_result(lt_3)
tests/test_tenacity.py:61:    """Construct RetryCa
…[313 chars elided]…
result(lambda result: result == 123)
tests/test_tenacity.py:688:    def test_retry_any(self) -> None:
tests/test_tenacity.py:689:        retry = tenacity.retry_any(
tests/test_tenacity.py:703:    def test_retry_all(self) -> None:
tests/test_tenacity.py:704:        retry = tenacity.retry_all(
tests/test_tenacity.py:719:        retry = tenacity.retry_if_result(lambda x: x == 1) & tenacity.retry_if_result(
tests/test_tenacity.py:735:        ) | tenacity.retry_if_result(lambda x: isinstance(x, int))
[tool_use Bash] {"command": "sed -n 685,760p tests/test_tenacity.py; echo ----; sed -n 355,410p tests/test_asyncio.py", "description": "Read existing operator composition tests"}
[tool_result]         self.assertTrue(r(tenacity.Future.construct(1, 2, False)))
        self.assertFalse(r(tenacity.Future.construct(1, 1, False)))

    def test_retry_any(self) -> None:
        retry = tenacity.retry_any(
            tenacity.retry_if_result(lambda x: x == 1),
            tenacity.retry_if_result(lambda x: x == 2),
        )

        def r(fut: tenacity.Future) -> bool:
            retry_state = make_retry_state(1, 1.0, last_result=fut)
            return retry(retry_state)

        self.as
…[3742 chars elided]…
tegy):
                with attempt:
                    attempts += 1
                attempt.retry_state.set_result(attempts)

            return attempts

        result = await test()

        self.assertEqual(3, result)

    @asynctest
    async def test_async_retying_iterator(self) -> None:
        thing = NoIOErrorAfterCount(5)
        with pytest.raises(TypeError):
            for attempts in AsyncRetrying():
                with attempts:
                    await _async_function(thing)
[assistant] I'll add sync regression tests next to `test_retry_or`, covering both operand orders for `|` and `&`. Then I'll add one async test for a plain callable.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py", "old_string": "        self.assertTrue(r(tenacity.Future.construct(1, \"foo\", False)))\n        self.assertFalse(r(tenacity.Future.construct(1, \"foobar\", False)))\n        self.assertFalse(r(tenacity.Future.construct(1, 2.2, F
…[1333 chars elided]…
, is_one & base]\n        for retry in all_strategies:\n            self.assertIsInstance(retry, tenacity.retry_all)\n            self.assertFalse(r(retry, tenacity.Future.construct(1, 1, False)))\n            self.assertTrue(r(retry, tenacity.Future.construct(1, 2, False)))\n            self.assertFalse(r(retry, tenacity.Future.construct(1, 3, False)))\n\n    def _raise_try_again(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Before running it, I re-checked my expected values and they're wrong. With `base = (result == 2)` and `is_one`, `base & is_one` can never be true, so the `all` assertions don't test anything. I'll switch to an `is_even` predicate with values 1 to 4, which gives distinct `any` and `all` outcomes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_or_and_with_plain_callable(self) -> None:\n        def is_one(retry_state: tenacity.RetryCallState) -> bool:\n            return retry_state.outcome is not None and retry_state.outcome.result() =
…[1590 chars elided]…
is_even, is_even | base]:\n            self.assertIsInstance(retry, tenacity.retry_any)\n            self.assertEqual([False, True, False, True], [r(retry, v) for v in (1, 2, 3, 4)])\n\n        for retry in [base & is_even, is_even & base]:\n            self.assertIsInstance(retry, tenacity.retry_all)\n            self.assertEqual([False, True, False, False], [r(retry, v) for v in (1, 2, 3, 4)])"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async side. I'll check the imports in `test_asyncio.py` so the new test uses the names it already has.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_asyncio.py | grep -n \"import\\|^from\"", "description": "Check async test imports"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
32:import tenacity
33:from tenacity import (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_asyncio.py", "old_string": "            retry_strategy = retry_if_result(gt_0) & tasyncio.retry_if_result(lt_3)\n            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):\n                with attempt:\n                   
…[960 chars elided]…
utcome.result() > 0\n\n            retry_strategy = tasyncio.retry_if_result(lt_3) & gt_0\n            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):\n                with attempt:\n                    attempts += 1\n                attempt.retry_state.set_result(attempts)\n\n            return attempts\n\n        result = await test()\n\n        self.assertEqual(3, result)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Next I'll run the suite with the new tests, and check whether ruff and mypy are available in the env to lint the changes.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; for t in ruff mypy; do $PY -m $t --version 2>&1 | head -1; done", "description": "Run test suite and check for linters"}
[tool_result] ...........s................................................ [ 43%]
........................................................................ [ 94%]
.......                                                                  [100%]
138 passed, 1 skipped, 12 subtests passed in 1.81s
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
[assistant] All 138 pass (136 before, plus the 2 new tests). To confirm the new tests actually catch the bug, I'll run them against the original `retry.py` in a scratch copy.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; rm -rf /tmp/verify-revert && mkdir /tmp/verify-revert && cp -R tenacity tests pyproject.toml /tmp/verify-revert/ 2>/dev/null; git show HEAD:tenacity/retry.py > /tmp/verify-revert/tenacity/retry.py; cd /tmp/verify-revert && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestRetry tests/test_asyncio.py -k \"plain_callable\" 2>&1 | tail -8; cd - >/dev/null; rm -rf /tmp/verify-revert", "description": "Confirm new tests fail on the original retry.py"}
[tool_result] ERROR: not found: /private/tmp/verify-revert/tests/test_tenacity.py::TestRetry
(no match in any of [<Module test_tenacity.py>])


no tests ran in 0.04s
[assistant] The class name in my node ID was wrong. I'll rerun with a `-k` filter across both files.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; D=$(mktemp -d /tmp/verify-revert.XXXX); cp -R tenacity tests pyproject.toml $D/; git show HEAD:tenacity/retry.py > $D/tenacity/retry.py; cd $D && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py tests/test_asyncio.py -k \"plain_callable\" 2>&1 | grep -E \"passed|failed|Error|FAILED\" | head -10; cd - >/dev/null; rm -rf $D", "description": "Run new tests against original retry.py in scratch copy"}
[tool_result] E       AttributeError: 'function' object has no attribute '__ror__'. Did you mean: '__dir__'?
tenacity/retry.py:39: AttributeError
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_or_and_with_plain_callable
1 failed, 1 passed, 126 deselected in 0.08s
[assistant] On the original code the sync test fails with the exact reported `AttributeError`. The async test passes there too, which fits the report that async composition already worked. Last, I'll review the full diff.
[tool_use Bash] {"command": "git status --short && git diff -- tenacity/ && rm -f /tmp/repro_compose.py", "description": "Show status and source diff"}
[tool_result]  M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
diff --git a/tenacity/asyncio/retry.py b/tenacity/asyncio/retry.py
index cbb332e..7df1aee 100644
--- a/tenacity/asyncio/retry.py
+++ b/tenacity/asyncio/retry.py
@@ -30,22 +30,22 @@ class async_retry_base(retry_base):
         pass
 
     def __and__(  # type: ignore[override]
-        self, other: "retry_base | async_retry_base"
+        self, other: "retry_base | RetryBaseT"
     ) -> "retry_all
…[1321 chars elided]…
aseT") -> "retry_all":
         return retry_all(other, self)
 
-    def __or__(self, other: "retry_base") -> "retry_any":
-        return other.__ror__(self)
+    def __or__(self, other: "RetryBaseT") -> "retry_any":
+        if isinstance(other, retry_base):
+            return other.__ror__(self)
+        return retry_any(self, other)
 
-    def __ror__(self, other: "retry_base") -> "retry_any":
+    def __ror__(self, other: "RetryBaseT") -> "retry_any":
         return retry_any(other, self)
[assistant] Two of the new test lines are over the 88-column limit that ruff-format uses here. I'll wrap them to match the repo style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py", "old_string": "        def is_even(retry_state: tenacity.RetryCallState) -> bool:\n            return retry_state.outcome is not None and retry_state.outcome.result() % 2 == 0\n\n        def r(retry: tenacity.retry_base, value: i
…[226 chars elided]…
llState) -> bool:\n            return (\n                retry_state.outcome is not None\n                and retry_state.outcome.result() % 2 == 0\n            )\n\n        def r(retry: tenacity.retry_base, value: int) -> bool:\n            fut = tenacity.Future.construct(1, value, False)\n            retry_state = make_retry_state(1, 1.0, last_result=fut)\n            return retry(retry_state)"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_asyncio.py", "old_string": "            def gt_0(retry_state: tenacity.RetryCallState) -> bool:\n                return retry_state.outcome is not None and retry_state.outcome.result() > 0", "new_string": "            def gt_0(retry_state: tenacity.RetryCallState) -> bool:\n                return (\n                    retry_state.outcome is not None\n                    and retry_state.outcome.result() > 0\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155157-regression-since-8-4-2-composing/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Rerun full test suite after formatting edits"}
[tool_result] .......                                                                  [100%]
138 passed, 1 skipped, 12 subtests passed in 1.82s
[assistant] Composing a `retry_base` with a plain callable works again for `|` and `&`, in both operand orders, for sync and async strategies. The full suite passes: 138 passed, 1 skipped.

**Cause:** In `tenacity/retry.py`, the sync `retry_base.__or__` and `__and__` delegate to `other.__ror__` / `other.__rand__`. A plain function has neither, so `retry_if_exception_type(IOError) | my_predicate` raised `AttributeError`. The reflected forms (`my_predicate | retry_...`) already worked, and the async classes build `retry_any`/`retry_all` directly, so they were never affected.

**Changes (uncommitted):**
- `t
…[447 chars elided]…
 with a plain predicate and asserts the result type and truth values.
- `tests/test_asyncio.py`: `test_retry_with_plain_callable_composition` covers the async path.

**Verification:**
- Against the original `retry.py`, the new sync test fails with the reported `AttributeError`.
- Against the fix, all eight combinations (sync and async, both orders, `|` and `&`) return `retry_any` / `retry_all`.
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run them. The annotations are unchecked by a type checker.

I haven't committed. Say if you want a commit on a branch.
