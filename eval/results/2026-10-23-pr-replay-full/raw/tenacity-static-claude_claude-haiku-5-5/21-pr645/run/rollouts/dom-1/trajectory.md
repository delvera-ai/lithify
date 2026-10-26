# trajectory dom-1

final message:
`Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged, with no `RetryError`. The full suite passes (183 passed, 1 skipped). I left the changes uncommitted.

**The fix**
- `tenacity/__init__.py`, `Retrying.__call__`: returns `fn(*args, **kwargs)` before `begin()`, the same shape as the existing `wraps` path.
- `tenacity/asyncio/__init__.py`, `AsyncRetrying.__call__`: when disabled, awaits `fn` if it is a coroutine function and calls it directly otherwise, so sync functions still work. It returns before `begin()`. The `# type: ignore[no-any-return]` follows the existing pattern in that file, but mypy has not verified it.

**Tests (new methods only, no existing lines changed)**
- `tests/test_tenacity.py::TestEnabled`: a direct call that raises gives `ValueError` with one call; a direct call that succeeds returns its result.
- `tests/test_asyncio.py::TestAsyncEnabled`: the same for an async function, plus a sync function passed to `AsyncRetrying(enabled=False)`.
- Before the fix, both failure tests failed with `RetryError` wrapping the `ValueError`, which is the reported bug. The two success-path tests passed before the fix too, as expected, since they guard the return value.

**Release note:** `releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml`, a `fixes:` entry.

**Checks**
- `run_tests.py` on the four new tests: green after the fix.
- `run_tests.py` full suite: exit 0, 183 passed, 1 skipped.
- `check_changed.py`: first run flagged one of my docstrings at 92 columns; I shortened it, and the re-run reports 0 problems.
- Not run: ruff and mypy (the script says they are unavailable here), so the new `type: ignore` is unverified. PyYAML was also not available, so the release note was not parsed as YAML.

**Not changed**
- `TornadoRetrying.__call__` in `tenacity/tornadoweb.py` still ignores `enabled=False`. The task named only `Retrying` and `AsyncRetrying`, so I left it alone; it is a one-line guard if you want it.
- I did not widen the "Disabling Retries" sentence in `doc/source/index.rst`. The contract marks that as optional for a bug fix.

## events
[assistant] I'll start by reading the contract skill headings and the code paths involved.
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n 'enabled' tenacity/*.py | head -60", "description": "List contract headings and enabled references"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[746 chars elided]…
eep the change surface minimal
tenacity/__init__.py:263:        enabled: bool = True,
tenacity/__init__.py:277:        self.enabled = enabled
tenacity/__init__.py:294:        enabled: bool | object = _unset,
tenacity/__init__.py:311:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:382:            if not self.enabled:
tenacity/__init__.py:501:        if not self.enabled:
tenacity/__init__.py:746:    enabled: bool = ...,
tenacity/__init__.py:764:    enabled: bool = True,
[tool_use Bash] {"command": "sed -n '1,18p;341,380p;77,109p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n '255,330p;370,400p;495,520p' tenacity/__init__.py", "description": "Read enabled contract section and Retrying code"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, th
…[13125 chars elided]…
.outcome.exception()  # type: ignore[misc]
            return

        self.begin()

        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
        while True:
            do = self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                yield AttemptManager(retry_state=retry_state)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                break
[tool_use Bash] {"command": "grep -n '__call__' -A22 tenacity/__init__.py | sed -n '1,40p'; echo ----; grep -n '__call__' -B3 -A40 tenacity/asyncio/__init__.py | head -70; echo ----; grep -n 'class TestEnabled' -A60 tests/test_tenacity.py | head -90", "description": "Read __call__ implementations and existing enabled tests"}
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
…[4839 chars elided]…
t
1702-            call_count += 1
1703-            if call_count < 3:
1704-                raise ValueError("fail")
1705-            return True
1706-
1707-        assert fails_twice() is True
1708-        assert call_count == 3
1709-
1710-    def test_enabled_false_iter_raises_original_exception(self) -> None:
1711-        """When enabled=False, the iterator protocol raises the original exception,
1712-        not a RetryError, and the body executes exactly once."""
1713-        call_count = 0
[assistant] The disabled-path contract is clear. Next I'll look at the async enabled tests and the test file layout so the new tests match.
[tool_use Bash] {"command": "sed -n '1713,1800p' tests/test_tenacity.py; echo ----; grep -n 'class TestAsyncEnabled' -A50 tests/test_asyncio.py | head -80; sed -n '1,20p' tests/test_asyncio.py | grep -n import", "description": "Read remaining enabled tests and async test file"}
[tool_result]         call_count = 0
        retrying = Retrying(
            enabled=False,
            stop=tenacity.stop_after_attempt(5),
            wait=tenacity.wait_none(),
        )
        with pytest.raises(ValueError, match="fail"):
            for attempt in retrying:
                with attempt:
                    call_count += 1
                    raise ValueError("fail")
        assert call_count == 1

    def test_enabled_false_iter_succeeds_on_first_attempt(self) -> None:
        """When 
…[4358 chars elided]…
sync for attempt in retrying:
242-            with attempt:
243-                call_count += 1
244-        assert call_count == 1
245-
246-
247-@unittest.skipIf(not have_trio, "trio not installed")
248-class TestTrio(unittest.TestCase):
249-    def test_trio_basic(self) -> None:
250-        thing = NoIOErrorAfterCount(5)
251-
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
[assistant] I'll write the regression tests first, before touching the library code. Sync tests go in `TestEnabled`, async ones in `TestAsyncEnabled`, and both are new methods only.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_tenacity.py", "old_string": "        for attempt in retrying:\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n\nclass TestRetryWith:", "new_string": "        for attempt in retrying:\n            w
…[808 chars elided]…
 calling the Retrying object returns the function's result.\"\"\"\n        call_count = 0\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        retrying = Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        assert retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n\nclass TestRetryWith:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n '^from\\|^import\\|    AsyncRetrying\\|stop_after_attempt,' tests/test_asyncio.py | head -30", "description": "Check imports in async test file"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
34:    AsyncRetrying,
40:    stop_after_attempt,
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_asyncio.py", "old_string": "        async for attempt in retrying:\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")", "new_string": "       
…[995 chars elided]…
nd returns its result.\"\"\"\n        call_count = 0\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        assert await retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now I'll run the new tests alone against the unfixed code, through the harness runner as the project requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -l $PY; sed -n '1,40p' .lithify/harness/scripts/run_tests.py | grep -n 'usage\\|argv\\|python' ; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raise
…[23 chars elided]…
sts/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_returns_result tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_returns_result > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
1:#!/usr/bin/env python3
9:Usage (from the repo root, with the project python from memory.md):
10:    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
39:    args = sys.ar
…[1380 chars elided]…
10908a150 state=finished raised ValueError>]

tenacity/__init__.py:481: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raises_original_exception
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_raises_original_exception
========================= 2 failed, 2 passed in 0.09s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The two failures are the reported bug: `RetryError` wrapping the original `ValueError`. The two success-path tests pass on the unfixed code, which is expected because the bug only shows on failure; they guard the return value. Now the fix, in both `__call__` methods, placed before `begin()` as the contract requires.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n 
…[133 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tenacity/asyncio/__init__.py", "old_string": "        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        self.begin()\n", "new_string": "        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            if _utils.is_coroutine_callable(fn):\n                result = await fn(*args, **kwargs)\n            else:\n                result = fn(*args, **kwargs)\n            return result  # type: ignore[no-any-return]\n\n        self.begin()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Both fixes are in. Next is the release note, which the contract's §2 requires, so I'll check its requirements and the existing note format.
[tool_use Bash] {"command": "sed -n '432,453p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; ls releasenotes/notes | tail -5; f=$(ls releasenotes/notes/*.yaml | tail -1); cat \"$f\"", "description": "Read reno contract section and sample note"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[730 chars elided]…
ible fix.
  ```
- Rendered by `doc/source/changelog.rst` (`.. release-notes::`), so it must be valid YAML.

trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml", "content": "---\nfixes:\n  - |\n    Calling a ``Retrying`` or ``AsyncRetrying`` object directly with a function\n    now honours ``enabled=False``: the function is called exactly once and its\n    exception propagates unchanged, instead of being retried and wrapped in\n    ``RetryError``. This matches the ``@retry`` decorator and the iterator\n    interface.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml (file state is current in your context — no need to Read it back)
[assistant] Now I'll re-run the four targeted tests green, then the full suite through the harness.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call_returns_result tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_raises_original_exception tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call_sync_fn_returns_result > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt", "description": "Run new regression tests against fixed code"}
[tool_result] exit=0

============================== 4 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt", "description": "Run full test suite via harness"}
[tool_result] exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 183 passed, 1 skipped, 15 subtests passed in 1.79s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt | tail -30; git status --short", "description": "Run stdlib lint/typing stand-in and show status"}
[tool_result] exit=1
changed: releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:1755: line is 92 columns (max 88)
FAIL: 1 problem(s)
HINT: this is a heuristic. If a FAIL contradicts a rule in skills/tenacity-change-contract, keep the code as the skill says and report the FAIL as a checker false positive; don't reshape the code
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml
[assistant] The line-length check flags one of my new docstrings. I'll shorten it and re-run the check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_tenacity.py", "old_string": "        \"\"\"When enabled=False, calling the Retrying object returns the function's result.\"\"\"", "new_string": "        \"\"\"When enabled=False, calling the Retrying object returns the result.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/check.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full.txt", "description": "Re-run line check and full suite after docstring fix"}
[tool_result] exit=0
changed: releasenotes/notes/enabled-false-direct-call-3e7b9a1c5d2f8046.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
exit=0
============== 183 passed, 1 skipped, 15 subtests passed in 1.82s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged, with no `RetryError`. The full suite passes (183 passed, 1 skipped). I left the changes uncommitted.

**The fix**
- `tenacity/__init__.py`, `Retrying.__call__`: returns `fn(*args, **kwargs)` before `begin()`, the same shape as the existing `wraps` path.
- `tenacity/asyncio/__init__.py`, `AsyncRetrying.__call__`: when disabled, awaits `fn` if it is a coroutine function and calls it directly otherwise, so sync functions still work. It returns before `begin()`. The `# typ
…[960 chars elided]…
ngs at 92 columns; I shortened it, and the re-run reports 0 problems.
- Not run: ruff and mypy (the script says they are unavailable here), so the new `type: ignore` is unverified. PyYAML was also not available, so the release note was not parsed as YAML.

**Not changed**
- `TornadoRetrying.__call__` in `tenacity/tornadoweb.py` still ignores `enabled=False`. The task named only `Retrying` and `AsyncRetrying`, so I left it alone; it is a one-line guard if you want it.
- I did not widen the "Disabling Retries" sentence in `doc/source/index.rst`. The contract marks that as optional for a bug fix.
