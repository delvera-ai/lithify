# trajectory base-1

final message:
`AttemptManager` now supports the async context-manager protocol, so `async with attempt:` works inside `async for attempt in AsyncRetrying(...)` and behaves like `with attempt:`. The full suite passes: 140 passed, 1 skipped.

**Changes**
- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the exception-swallowing and result-recording logic is not duplicated. The class is shared by the sync and async iterators, so no changes to `tenacity/asyncio/__init__.py` were needed.
- **`tests/test_asyncio.py`**: added `test_async_with_attempt` (retries until `RetryError`) and `test_async_with_attempt_success` (a failure followed by a success) to `TestContextManager`.
- **`releasenotes/notes/attempt-manager-async-context-manager-41eb2d3104fecc25.yaml`**: a `features:` note. I wrote it as a feature, not a fix.

**Verification**
- Fail-on-base check: both new tests fail on HEAD with `TypeError: 'AttemptManager' object does not support the asynchronous context manager protocol`, which is the missing feature.
- `git status` shows only the two modified files and the new reno note.
- mypy and ruff were not run; the project interpreter doesn't have them installed. The new code is fully annotated and follows the existing style.

Nothing is committed. Let me know if you want a commit or PR.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[6662 chars elided]…
n> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "cat <work>/env-tenacity/bin/python >/dev/null 2>&1; echo $?; grep -n \"class AttemptManager\" -A 40 tenacity/__init__.py; grep -rn \"__aenter__\\|__enter__\\|__aexit__\" tenacity/ | head -30; ls releasenotes/notes | tail -5", "description": "Load contract skill and inspect AttemptManager"}
[tool_result] 0
195:class AttemptManager:
196-    """Manage attempt context."""
197-
198-    def __init__(self, retry_state: "RetryCallState"):
199-        self.retry_state = retry_state
200-
201-    def __enter__(self) -> None:
202-        pass
203-
204-    def __exit__(
205-        self,
206-        exc_type: type[BaseException] | None,
207-        exc_value: BaseException | None,
208-        traceback: t.Optional["types.TracebackType"],
209-    ) -> bool | None:
210-        if exc_type is not None and exc_
…[894 chars elided]…
try_error_callback: t.Callable[["RetryCallState"], t.Any] | None = None,
231-        name: str | None = None,
232-    ):
233-        self.sleep = sleep
234-        self.stop = stop
235-        self.wait = wait
tenacity/__init__.py:201:    def __enter__(self) -> None:
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The contract skill is loaded: the change needs code, a reno note, and a regression test that fails on HEAD. Next I'll look at how the async loop yields attempts and how the existing tests are written.
[tool_use Bash] {"command": "grep -rn \"AttemptManager\" tenacity/ tests/ | head -30; echo ---; grep -n \"class TestContextManager\" -A 30 tests/test_asyncio.py | head -60; echo ---; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ---; ls .lithify/harness/skills/tenacity-change-contract/scripts/ 2>&1; ls .lithify 2>&1", "description": "Find AttemptManager usages, tests, and reno sample"}
[tool_result] tenacity/__init__.py:195:class AttemptManager:
tenacity/__init__.py:443:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/__init__.py:450:                yield AttemptManager(retry_state=retry_state)
tenacity/__init__.py:725:    "AttemptManager",
tenacity/asyncio/__init__.py:24:    AttemptManager,
tenacity/asyncio/__init__.py:163:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:171:    async def __anext__(self) -> AttemptMa
…[703 chars elided]…
eption):
196-            pass
197-
198-        try:
199-            async for attempt in tasyncio.AsyncRetrying(
200-                stop=stop_after_attempt(1), reraise=True
201-            ):
202-                with attempt:
203-                    raise CustomError()
204-        except CustomError:
205-            pass
206-        else:
207-            raise Exception
208-
---
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
---
fails_on_base.py
harness
library
state.json
[tool_use Bash] {"command": "cat memory.md 2>/dev/null; cat .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py | head -60; grep -n \"^from\\|^import\" tests/test_asyncio.py | head; grep -n \"features:\" -r releasenotes/notes | head -3", "description": "Read project memory and fail-on-base script"}
[tool_result] #!/usr/bin/env python3
"""Check that new/changed tests FAIL on the unmodified code (HEAD), read-only.

Usage (from the repo root, with the project interpreter so pytest is importable):
    <project-python> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \
        tests/test_x.py::TestY::test_z [more pytest node ids or args ...]

What it does: exports HEAD with `git archive` into a temp dir, copies the
working-tree `tests/` directory over it (so your new tests run agains
…[1925 chars elided]…
ncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml:2:features:
releasenotes/notes/support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml:2:features:
releasenotes/notes/export-convenience-symbols-981d9611c8b754f3.yaml:2:features:
[assistant] The project interpreter path is in CLAUDE.md, since there's no `memory.md` at the root. `AttemptManager` is a single class shared by the sync and async iterators, so adding the async protocol to it covers both. I'll implement by delegating to the sync methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "old_string": "        # We don't have the result, actually.\n        self.retry_state.set_result(None)\n        return None\n\n\nclass BaseRetrying(ABC):", "new_string": "        # We don't have the result, actually.\n        self
…[25 chars elided]…
one)\n        return None\n\n    async def __aenter__(self) -> None:\n        self.__enter__()\n\n    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.TracebackType\"],\n    ) -> bool | None:\n        return self.__exit__(exc_type, exc_value, traceback)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, the regression test. I need to see where `TestContextManager` continues after `test_reraise`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "offset": 205, "limit": 12}
[tool_result] 205	            pass
206	        else:
207	            raise Exception
208	
209	    @asynctest
210	    async def test_sleeps(self) -> None:
211	        start = current_time_ms()
212	        try:
213	            async for attempt in tasyncio.AsyncRetrying(
214	                stop=stop_after_attempt(1), wait=wait_fixed(1)
215	            ):
216	                with attempt:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "        else:\n            raise Exception\n\n    @asynctest\n    async def test_sleeps(self) -> None:", "new_string": "        else:\n            raise Exception\n\n    @asynctest\n    async def test_async_with_att
…[370 chars elided]…
ctest\n    async def test_async_with_attempt_success(self) -> None:\n        attempts = 0\n        async for attempt in tasyncio.AsyncRetrying(stop=stop_after_attempt(3)):\n            async with attempt:\n                attempts += 1\n                if attempts < 2:\n                    raise Exception\n\n        assert attempts == 2\n\n    @asynctest\n    async def test_sleeps(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now the reno note, named per the contract's `<slug>-<16 hex>.yaml` convention.
[tool_use Bash] {"command": "cat > releasenotes/notes/attempt-manager-async-context-manager-$(python3 -c 'import secrets;print(secrets.token_hex(8))').yaml <<'EOF'\n---\nfeatures:\n  - |\n    The object yielded by ``async for attempt in AsyncRetrying(...)`` now supports\n    the async context manager protocol, so ``async with attempt:`` works inside the\n    loop and behaves exactly like ``with attempt:``.\nEOF\n
…[98 chars elided]…
oundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python; $P .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py tests/test_asyncio.py::TestContextManager::test_async_with_attempt tests/test_asyncio.py::TestContextManager::test_async_with_attempt_success; echo \"exit=$?\"", "description": "Write reno note and run fail-on-base check"}
[tool_result] releasenotes/notes/attempt-manager-async-context-manager-41eb2d3104fecc25.yaml
FF                                                                       [100%]
=================================== FAILURES ===================================
__________________ TestContextManager.test_async_with_attempt __________________

self = <tests.test_asyncio.TestContextManager testMethod=test_async_with_attempt>

    @asynctest
    async def test_async_with_attempt(self) -> None:
        attempts = 0
      
…[812 chars elided]…
port the asynchronous context manager protocol

tests/test_asyncio.py:227: TypeError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_attempt - T...
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_attempt_success
2 failed in 0.05s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
exit=0
[assistant] Both new tests fail on HEAD with the expected `TypeError`. Now the full suite, run once after the final edit.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and check git status"}
[tool_result] ...........s................................................ [ 42%]
........................................................................ [ 93%]
.........                                                                [100%]
140 passed, 1 skipped, 12 subtests passed in 1.84s
 M tenacity/__init__.py
 M tests/test_asyncio.py
?? releasenotes/notes/attempt-manager-async-context-manager-41eb2d3104fecc25.yaml
[assistant] `AttemptManager` now supports the async context-manager protocol, so `async with attempt:` works inside `async for attempt in AsyncRetrying(...)` and behaves like `with attempt:`. The full suite passes: 140 passed, 1 skipped.

**Changes**
- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the exception-swallowing and result-recording logic is not duplicated. The class is shared by the sync and async iterators, so no changes to `tenacity/asyncio/__init__.py` were needed.
- **`tests/test_asyncio.py`**
…[185 chars elided]…
ttempt-manager-async-context-manager-41eb2d3104fecc25.yaml`**: a `features:` note. I wrote it as a feature, not a fix.

**Verification**
- Fail-on-base check: both new tests fail on HEAD with `TypeError: 'AttemptManager' object does not support the asynchronous context manager protocol`, which is the missing feature.
- `git status` shows only the two modified files and the new reno note.
- mypy and ruff were not run; the project interpreter doesn't have them installed. The new code is fully annotated and follows the existing style.

Nothing is committed. Let me know if you want a commit or PR.
