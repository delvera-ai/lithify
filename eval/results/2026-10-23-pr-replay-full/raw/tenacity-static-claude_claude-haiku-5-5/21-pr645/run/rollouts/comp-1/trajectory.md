# trajectory comp-1

final message:
`Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged, matching the decorator and iterator paths. The full suite passes (184 passed, 1 skipped), and `check_changed.py` reports 0 problems.

**What changed**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` before `begin()` when `enabled` is false.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting `fn` only when it is a coroutine function, as the retry loop below it does.
- `releasenotes/notes/fix-enabled-false-direct-call-b4c1c2fe94a8aef2.yaml`: a `fixes:` note, as the project requires for behaviour changes.
- Five new tests: three in `tests/test_tenacity.py` and `tests/test_asyncio.py` cover the raise and call-count path, and two cover the return value. No existing test lines were changed.

**Red/green**
- Against the unfixed code, the three "raises original exception" tests failed with `RetryError` wrapping the `ValueError`. That is the reported bug.
- The two "returns result" tests already passed before the fix, because the function succeeds on the first attempt. They guard the return path rather than the bug.
- After the fix, all five pass.

**Checks**
- Ruff and mypy were not run; they are unavailable in this environment, so the type-checking verdict is unverified.
- `tenacity/asyncio/__init__.py:122` has a new `# type: ignore[no-any-return]`. I reused the code the file already uses on the analogous `return do` line, but mypy did not confirm it. Please check it under mypy strict.

**Not done / left open**
- `TornadoRetrying.__call__` in `tenacity/tornadoweb.py` still ignores `enabled=False`. It was not in the task, so I left it. It would need the same guard in its generator form.
- I did not widen the "Disabling Retries" sentence in `doc/source/index.rst`. The contract marks it optional for a bug fix.

## events
[assistant] I'll start by reading the contract skill headings and the code paths involved.
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; grep -n 'enabled' tenacity/*.py | head -50", "description": "List contract headings and enabled references"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[750 chars elided]…
the change surface minimal
---
tenacity/__init__.py:263:        enabled: bool = True,
tenacity/__init__.py:277:        self.enabled = enabled
tenacity/__init__.py:294:        enabled: bool | object = _unset,
tenacity/__init__.py:311:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:382:            if not self.enabled:
tenacity/__init__.py:501:        if not self.enabled:
tenacity/__init__.py:746:    enabled: bool = ...,
tenacity/__init__.py:764:    enabled: bool = True,
[assistant] The `enabled` switch has its own contract section (1c1), so I'll read that plus §2–3 and the relevant code.
[tool_use Bash] {"command": "sed -n '341,381p;432,500p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n '370,400p;490,530p' tenacity/__init__.py", "description": "Read enabled contract and relevant code sections"}
[tool_result] ## 1c1. The `enabled` switch (`enabled=False`) — which entry points honour it
Verified at the current base (`grep -n "self.enabled" tenacity/*.py tenacity/asyncio/__init__.py`;
re-run it, the list grows as fixes land). Read this for ANY `enabled` bug, not only a new keyword.
- Honoured today, each before `begin()`: `wraps` (sync `wrapped_f`, async `async_wrapped`:
  `if not self.enabled: return f(...)` before `self.copy()`); `BaseRetrying.__iter__` (#643:
  yields one `AttemptManager` on a fresh
…[8746 chars elided]…
  do = self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                yield AttemptManager(retry_state=retry_state)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                break

    @abstractmethod
    def __call__(
        self,
        fn: t.Callable[..., WrappedFnReturnT],
        *args: t.Any,
        **kwargs: t.Any,
    ) -> WrappedFnReturnT:
        pass
[tool_use Bash] {"command": "grep -n 'def __call__' -A 40 tenacity/__init__.py | sed -n '1,60p'; echo ----; grep -n 'def __call__' -A 45 tenacity/asyncio/__init__.py; echo ----; grep -n 'def __call__' -A 30 tenacity/tornadoweb.py; echo ----; grep -n 'class TestEnabled' -A 30 tests/test_tenacity.py | head -50", "description": "Read __call__ implementations and existing enabled tests"}
[tool_result] 522:    def __call__(
523-        self,
524-        fn: t.Callable[..., WrappedFnReturnT],
525-        *args: t.Any,
526-        **kwargs: t.Any,
527-    ) -> WrappedFnReturnT:
528-        pass
529-
530-
531-class Retrying(BaseRetrying):
532-    """Retrying controller."""
533-
534-    @override
535:    def __call__(
536-        self,
537-        fn: t.Callable[..., WrappedFnReturnT],
538-        *args: t.Any,
539-        **kwargs: t.Any,
540-    ) -> WrappedFnReturnT:
541-        self.begin()
54
…[5525 chars elided]…

1670-
1671-        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
1672-        def my_func() -> str:
1673-            return "ok"
1674-
1675-        assert hasattr(my_func, "retry")
1676-        assert hasattr(my_func, "retry_with")
1677-        assert hasattr(my_func, "statistics")
1678-        assert my_func() == "ok"
1679-
1680-    def test_enabled_false_via_retry_with(self) -> None:
1681-        """retry_with(enabled=False) disables retrying."""
1682-        call_count = 0
1683-
[assistant] The fix is a guard at the top of `Retrying.__call__` and `AsyncRetrying.__call__`, matching the `wraps` path. Before editing, I'll look at the existing async enabled tests so the new regression tests match them.
[tool_use Bash] {"command": "grep -n 'class TestAsyncEnabled' -A 25 tests/test_asyncio.py; echo ----; grep -n '^from\\|^import\\|asynctest' tests/test_asyncio.py | head -20; echo ----; grep -n 'def test_enabled_false' tests/test_tenacity.py | tail -3; grep -n 'def test_enabled_false_via_retry_with' -A 14 tests/test_tenacity.py", "description": "Inspect async enabled tests and imports"}
[tool_result] 201:class TestAsyncEnabled(unittest.TestCase):
202-    @asynctest
203-    async def test_enabled_false_skips_retry(self) -> None:
204-        """When enabled=False, async function is called directly without retrying."""
205-        call_count = 0
206-
207-        @retry(enabled=False, stop=stop_after_attempt(3))
208-        async def always_fails() -> None:
209-            nonlocal call_count
210-            call_count += 1
211-            raise ValueError("fail")
212-
213-        with pytest.ra
…[1418 chars elided]…
        """retry_with(enabled=False) disables retrying."""
1682-        call_count = 0
1683-
1684-        @retry(stop=tenacity.stop_after_attempt(3))
1685-        def always_fails() -> None:
1686-            nonlocal call_count
1687-            call_count += 1
1688-            raise ValueError("fail")
1689-
1690-        disabled = always_fails.retry_with(enabled=False)
1691-        with pytest.raises(ValueError, match="fail"):
1692-            disabled()
1693-        assert call_count == 1
1694-
[assistant] The contract's red-test requirements are: assert the original exception type and a call count of 1 with a `stop=` that would otherwise retry, and cover a sync `fn` for the async path. I'll check the imports, then write the tests first.
[tool_use Bash] {"command": "sed -n '1,60p' tests/test_tenacity.py | grep -n 'import\\|Retrying' ; grep -n 'Retrying' tests/test_asyncio.py | head -5; sed -n '225,240p' tests/test_asyncio.py", "description": "Check test imports and async enabled test tail"}
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
29:import tenacity
30:from tenacity import RetryCallState, RetryError, Retrying, retry
31:from tenacity._utils import override
32:from tenacity.retry import retry_all, retry_any
34:    AsyncRetrying,
88:        # Mirrors the sync test: falsy `wait` values reach AsyncRetrying from

…[184 chars elided]…
):
            async for attempt in retrying:
                with attempt:
                    call_count += 1
                    raise ValueError("fail")
        assert call_count == 1

    @asynctest
    async def test_enabled_false_aiter_succeeds_on_first_attempt(self) -> None:
        """When enabled=False, the async iterator runs the body once and stops."""
        call_count = 0
        retrying = AsyncRetrying(
            enabled=False,
            stop=stop_after_attempt(5),
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tests/test_tenacity.py", "old_string": "    def test_enabled_false_iter_raises_original_exception(self) -> None:", "new_string": "    def test_enabled_false_direct_call_raises_original_exception(self) -> None:\n        \"\"\"Retrying(enabled=False)(fn) c
…[636 chars elided]…
gle call.\"\"\"\n        call_count = 0\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        retrying = Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        assert retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n    def test_enabled_false_iter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async regression tests, covering both a coroutine `fn` and a sync `fn` (the `is_coroutine_callable` branch).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:", "new_string": "    @asynctest\n    async def test_enabled_false_direct_call_raises_original_exception(self) -> None:\
…[1396 chars elided]…
call_count = 0\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        assert await retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tests/test_asyncio.py has been updated successfully.
[assistant] Writing the tests is not evidence yet. Next I'll run them alone against the unfixed code through the harness script, which the project requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_returns_res
…[29 chars elided]…
stAsyncEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_returns_result > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
        call_count = 0
    
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")
    
        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))
        with pytest.raises(ValueError, match="fail"):
>           await retrying(always_fails)

tests/test_asyncio.py:248: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/asyncio/__init__.py:121: in __call__

…[907 chars elided]…
ort test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raises_original_exception
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_raises_original_exception
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_raises_original_exception
========================= 3 failed, 2 passed in 0.10s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The three failures are the right gap: `RetryError` wraps the original `ValueError` instead of it propagating. The two `returns_result` tests already pass on the unfixed code, which is expected because the function succeeds on its first attempt. I'll note that in the final message. Now the fix, following the `wraps` path and §1c1's shape for the async branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tenacity/asyncio/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        is_async = _utils.is_coroutine_callable(fn)\n        while
…[73 chars elided]…
tils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                result = await fn(*args, **kwargs)\n            else:\n                result = fn(*args, **kwargs)\n            return result  # type: ignore[no-any-return]\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/comp-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next is the reno note (§2, required for a bug fix), then the green run. I'll generate the 16-hex suffix with a command rather than inventing it.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8); F=releasenotes/notes/fix-enabled-false-direct-call-$H.yaml; printf -- '---\\nfixes:\\n  - |\\n    Calling a ``Retrying`` or ``AsyncRetrying`` object directly with ``enabled=False``\\n    (``Retrying(enabled=False)(fn)``) now calls ``fn`` once and re-raises its exception\\n    unchanged, instead of running the full retry loop and raising ``RetryError``. This\\n    matches the ``@retry`` decorator and iterator paths.\\n' > \"$F\"; echo \"$F\"; cat \"$F\"; ls releasenotes/notes | head -3", "description": "Create reno release note for the fix"}
[tool_result] releasenotes/notes/fix-enabled-false-direct-call-b4c1c2fe94a8aef2.yaml
---
fixes:
  - |
    Calling a ``Retrying`` or ``AsyncRetrying`` object directly with ``enabled=False``
    (``Retrying(enabled=False)(fn)``) now calls ``fn`` once and re-raises its exception
    unchanged, instead of running the full retry loop and raising ``RetryError``. This
    matches the ``@retry`` decorator and iterator paths.
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yaml
add-async-actions-b249c527d99723bb.yaml
[assistant] Now the five regression tests should go green. Then the full suite and the stdlib checker.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_returns_res
…[30 chars elided]…
tAsyncEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_returns_result > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/green.txt", "description": "Run new regression tests against fixed code"}
[tool_result] exit=0
tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_returns_result PASSED [100%]

============================== 5 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/full.txt; echo ----; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] exit=0

============== 184 passed, 1 skipped, 15 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
----
exit=0
changed: releasenotes/notes/fix-enabled-false-direct-call-b4c1c2fe94a8aef2.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
UNVERIFIED tenacity/asyncio/__init__.py:122: added type: ignore[no-any-return] (codes already in file: arg-type, attr-defined, misc, no-any-return, override, truthy-bool, type-var)
HINT: mypy strict rejects an unneeded or wrong-code ignore. Prefer a shape that needs none; else take the code from an existing ignore on an analogous line, and name each UNVERIFIED line in the final message
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Everything is green: 184 passed, 1 skipped, and `check_changed.py` reports 0 problems. I'll confirm that no existing test lines were altered.
[tool_use Bash] {"command": "git diff --stat; git diff -U0 tests/ | grep '^-' | grep -v '^---' | wc -l", "description": "Confirm diff stat and no removed test lines"}
[tool_result]  tenacity/__init__.py         |  3 +++
 tenacity/asyncio/__init__.py |  9 ++++++++-
 tests/test_asyncio.py        | 48 ++++++++++++++++++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 28 ++++++++++++++++++++++++++
 4 files changed, 87 insertions(+), 1 deletion(-)
       0
[assistant] `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged, matching the decorator and iterator paths. The full suite passes (184 passed, 1 skipped), and `check_changed.py` reports 0 problems.

**What changed**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` before `begin()` when `enabled` is false.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting `fn` only when it is a coroutine function, as the retry loop below it does.
- `releasenotes/notes/fix-enabled-false-direc
…[716 chars elided]…
ironment, so the type-checking verdict is unverified.
- `tenacity/asyncio/__init__.py:122` has a new `# type: ignore[no-any-return]`. I reused the code the file already uses on the analogous `return do` line, but mypy did not confirm it. Please check it under mypy strict.

**Not done / left open**
- `TornadoRetrying.__call__` in `tenacity/tornadoweb.py` still ignores `enabled=False`. It was not in the task, so I left it. It would need the same guard in its generator form.
- I did not widen the "Disabling Retries" sentence in `doc/source/index.rst`. The contract marks it optional for a bug fix.
