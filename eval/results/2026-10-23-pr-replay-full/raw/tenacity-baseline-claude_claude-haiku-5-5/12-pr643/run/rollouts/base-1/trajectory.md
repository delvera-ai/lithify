# trajectory base-1

final message:
Fixed: `enabled=False` now works with the iterator pattern. The body runs once and exceptions propagate unchanged, for both `Retrying` and `AsyncRetrying`.

**Cause:** The decorator path checks `self.enabled` and calls the function directly. The iterator path (`BaseRetrying.__iter__` and `AsyncRetrying.__aiter__`/`__anext__`) never checked it, so it ran the full retry loop and then raised `RetryError`.

**Changes:**
- `tenacity/__init__.py`: added `_DisabledAttemptManager`, an `AttemptManager` whose `__exit__` returns `None`, so exceptions are not swallowed. `BaseRetrying.__iter__` yields one of these and returns when disabled.
- `tenacity/asyncio/__init__.py`: same behaviour in `__aiter__`/`__anext__`, using a one-shot flag.
- `tests/test_tenacity.py` and `tests/test_asyncio.py`: new tests for a single run with a propagated exception, and for a single run on success.
- `releasenotes/notes/enabled-false-iterator-3f9a1c2d7e4b8a60.yaml`: a `fixes` note.

**Verification:**
- Before the fix, a repro script showed 3 calls and `RetryError` in both the sync and async paths. After the fix it shows 1 call and `ValueError`.
- Full suite with the project's pytest command: 165 passed, 1 skipped.
- I did not confirm the new tests fail on the unfixed code. The repro covers that.
- `ruff` and `mypy` are not installed in the project's environment, so I did not run lint or type checks. The new code follows the existing annotation style.

Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"enabled\" --include=*.py . | grep -v test | head -50", "description": "Inspect repo layout and find enabled references"}
[tool_result] AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"enabled\" tenacity | head -50; ls tenacity tests", "description": "Find enabled references in tenacity package"}
[tool_result] tenacity/__init__.py:251:        enabled: bool = True,
tenacity/__init__.py:265:        self.enabled = enabled
tenacity/__init__.py:282:        enabled: bool | object = _unset,
tenacity/__init__.py:299:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:367:            if not self.enabled:
tenacity/__init__.py:693:    enabled: bool = ...,
tenacity/__init__.py:711:    enabled: bool = True,
tenacity/asyncio/__init__.py:94:        enabled: bool = True,
tenacity/asyncio/__init__.py:108:            enabled=enabled,
tenacity/asyncio/__init__.py:194:            if not self.enabled:
tenacity:
__init__.py
_utils.py
_version.py
after.py
asyncio
before.py
before_sleep.py
nap.py
py.typed
retry.py
stop.py
tornadoweb.py
wait.py

tests:
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "offset": 240, "limit": 420}
[tool_result] 240	        sleep: t.Callable[[int | float], None] = sleep,
241	        stop: "StopBaseT" = stop_never,
242	        wait: "WaitBaseT" = wait_none(),
243	        retry: "RetryBaseT" = retry_if_exception_type(),
244	        before: t.Callable[["RetryCallState"], None] = before_nothing,
245	        after: t.Callable[["RetryCallState"], None] = after_nothing,
246	        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
247	        reraise: bool = False,
248	        retry_error_cls: 
…[16365 chars elided]…
rovides the original callable signature plus retry control attributes.
646	    """
647	
648	    retry: "BaseRetrying"
649	    statistics: dict[str, t.Any]
650	
651	    def retry_with(self, *args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]": ...
652	
653	    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
654	
655	
656	class _AsyncRetryDecorator(t.Protocol):
657	    @t.overload
658	    def __call__(
659	        self, fn: "t.Callable[P, types.CoroutineType[t.Any, t.Any, R]]"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "offset": 80, "limit": 180}
[tool_result] 80	        stop: "StopBaseT" = tenacity.stop.stop_never,
81	        wait: "WaitBaseT" = tenacity.wait.wait_none(),
82	        retry: "SyncRetryBaseT | RetryBaseT" = tenacity.retry_if_exception_type(),
83	        before: t.Callable[
84	            ["RetryCallState"], None | t.Awaitable[None]
85	        ] = before_nothing,
86	        after: t.Callable[["RetryCallState"], None | t.Awaitable[None]] = after_nothing,
87	        before_sleep: t.Callable[["RetryCallState"], None | t.Awaitable[None]]
88	
…[5248 chars elided]…
reserve attributes
204	        async_wrapped.retry = self  # type: ignore[attr-defined]
205	        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
206	        async_wrapped.statistics = {}  # type: ignore[attr-defined]
207	
208	        return t.cast("_RetryDecorated[P, R]", async_wrapped)
209	
210	
211	__all__ = [
212	    "AsyncRetrying",
213	    "WrappedFn",
214	    "retry_all",
215	    "retry_any",
216	    "retry_if_exception",
217	    "retry_if_result",
218	]
219	
[tool_use Bash] {"command": "grep -n \"class AttemptManager\" -A 25 tenacity/__init__.py; grep -n \"enabled\" -B3 -A20 tests/test_tenacity.py | head -120; grep -n \"enabled\" tests/test_asyncio.py; ls releasenotes/notes | tail -5; git log --oneline -3 -- tenacity/__init__.py", "description": "Read AttemptManager and existing enabled tests"}
[tool_result] 203:class AttemptManager:
204-    """Manage attempt context."""
205-
206-    def __init__(self, retry_state: "RetryCallState"):
207-        self.retry_state = retry_state
208-
209-    def __enter__(self) -> None:
210-        pass
211-
212-    def __exit__(
213-        self,
214-        exc_type: type[BaseException] | None,
215-        exc_value: BaseException | None,
216-        traceback: "types.TracebackType | None",
217-    ) -> bool | None:
218-        if exc_type is not None and exc_value i
…[3125 chars elided]…
etry(enabled=False, stop=stop_after_attempt(3))
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
[tool_use Bash] {"command": "sed -n 225,240p tenacity/__init__.py; sed -n 160,185p tests/test_asyncio.py; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml; grep -n \"^import\\|^from\" tests/test_tenacity.py tests/test_asyncio.py; grep -n \"class Test\" tests/test_asyncio.py | head; grep -n \"for attempt in\\|__iter__\\|async for\" tests/test_tenacity.py | head -5", "description": "Read async AttemptManager exit, test imports, and note format"}
[tool_result]     async def __aenter__(self) -> None:
        pass

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: "types.TracebackType | None",
    ) -> bool | None:
        return self.__exit__(exc_type, exc_value, traceback)


class BaseRetrying(ABC):
    def __init__(
        self,
        sleep: t.Callable[[int | float], None] = sleep,
        assert list(attempt_nos2) == [1, 2, 3]


class TestAsyncEnabled(u
…[2277 chars elided]…
all, retry_any
79:class TestAsyncio(unittest.TestCase):
163:class TestAsyncEnabled(unittest.TestCase):
181:class TestTrio(unittest.TestCase):
195:class TestContextManager(unittest.TestCase):
467:class TestDecoratorWrapper(unittest.TestCase):
536:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
168:            for attempt in Retrying(
1916:        for attempt in Retrying():
1931:            for attempt in retry:
1943:            for attempt in retry:
1958:            for attempt in retry:
[assistant] Before editing, I'll confirm the bug reproduces and check the baseline test run.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; cat > /tmp/repro_enabled.py <<'EOF'\nimport asyncio\nfrom tenacity import Retrying, AsyncRetrying\ncalls = 0\ntry:\n    for attempt in Retrying(enabled=False, stop=__import__(\"tenacity\").stop_after_attempt(3))
…[315 chars elided]…
y\").stop_after_attempt(3)):\n            with attempt:\n                calls += 1\n                raise ValueError(\"boom\")\n    except Exception as e:\n        print(\"async:\", type(e).__name__, \"calls\", calls)\nasyncio.run(main())\nEOF\n$PY -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/repro_enabled.py').read())\"", "description": "Check env and reproduce the iterator bug"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
sync: RetryError calls 3
async: RetryError calls 3
[assistant] Reproduced: both paths run 3 attempts and raise `RetryError`. Now the fix: when disabled, the iterators yield one attempt context whose `__exit__` does not swallow the exception.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: \"types.TracebackType | None\",\n    ) -> bool | None:\n        ret
…[422 chars elided]…
\"\"Attempt context used when retrying is disabled.\n\n    Exceptions propagate unchanged, matching the decorator path with ``enabled=False``.\n    \"\"\"\n\n    def __exit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: \"types.TracebackType | None\",\n    ) -> None:\n        return None\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "    def __iter__(self) -> t.Generator[AttemptManager, None, None]:\n        self.begin()\n\n        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        while True:", "new_string": "    def __iter__(self) -> t.Generator[AttemptManager, None, None]:\n        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        if not self.enabled:\n            yield _DisabledAttemptManager(retry_state=retry_state)\n            return\n\n        self.begin()\n\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "old_string": "    def __aiter__(self) -> \"AsyncRetrying\":\n        self.begin()\n        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        return self\n\n    async def __anext__(self) -> Atte
…[222 chars elided]…
elf.enabled\n        if self.enabled:\n            self.begin()\n        return self\n\n    async def __anext__(self) -> AttemptManager:\n        if self._disabled_attempt_pending:\n            self._disabled_attempt_pending = False\n            return _DisabledAttemptManager(retry_state=self._retry_state)\n        if not self.enabled:\n            raise StopAsyncIteration\n\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"AttemptManager\\|^from tenacity import\" -A0 tenacity/asyncio/__init__.py | head; sed -n 30,45p tests/test_asyncio.py", "description": "Check AttemptManager imports in asyncio module"}
[tool_result] 23:from tenacity import (
24:    AttemptManager,
165:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
175:    async def __anext__(self) -> AttemptManager:
178:            return _DisabledAttemptManager(retry_state=self._retry_state)
187:                return AttemptManager(retry_state=self._retry_state)
import pytest

import tenacity
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (
[tool_use Bash] {"command": "sed -n 20,35p tenacity/asyncio/__init__.py", "description": "View asyncio module imports"}
[tool_result] import typing as t

import tenacity
from tenacity import (
    AttemptManager,
    BaseRetrying,
    DoAttempt,
    DoSleep,
    RetryCallState,
    RetryError,
    _RetryDecorated,
    _utils,
    after_nothing,
    before_nothing,
)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "old_string": "    RetryError,\n    _RetryDecorated,\n    _utils,", "new_string": "    RetryError,\n    _DisabledAttemptManager,\n    _RetryDecorated,\n    _utils,"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now tests for both iterator paths, next to the existing `enabled` tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py", "old_string": "        assert fails_twice() is True\n        assert call_count == 3\n\n\nclass TestRetryWith:", "new_string": "        assert fails_twice() is True\n        assert call_count == 3\n\n    def test_enabled_false_ite
…[825 chars elided]…
"fail\")\n        assert call_count == 1\n\n    def test_enabled_false_iterator_success(self) -> None:\n        \"\"\"When enabled=False, a successful body under the iterator pattern is a single run.\"\"\"\n        call_count = 0\n\n        for attempt in Retrying(enabled=False):\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n\nclass TestRetryWith:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")", "new_string": "        with py
…[670 chars elided]…
\n    async def test_enabled_false_iterator_success(self) -> None:\n        \"\"\"When enabled=False, a successful async iterator body runs exactly once.\"\"\"\n        call_count = 0\n\n        async for attempt in AsyncRetrying(enabled=False):\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] The first sync test never asserts its count; fixing that, then running the full suite with the project's checks command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py", "old_string": "        for attempt in Retrying(enabled=False, stop=tenacity.stop_after_attempt(3)):\n            with attempt:\n                call_count += 1\n                raise ValueError(\"fail\")\n\n    def test_enabled_false_iterator_propagates_exception", "new_string": "        with contextlib.suppress(ValueError):\n            for attempt in Retrying(enabled=False, stop=tenacity.stop_after_attempt(3)):\n                with attempt:\n                    call_count += 1\n                    raise ValueError(\"fail\")\n        assert call_count == 1\n\n    def test_enabled_false_iterator_propagates_exception"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191641-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/repro_enabled.py').read())\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Re-run repro and full pytest suite"}
[tool_result] sync: ValueError calls 1
async: ValueError calls 1
..............s............................................... [ 37%]
...................................................................... [ 79%]
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.85s
[assistant] Suite passes (165 passed, 1 skipped) and the repro now shows one call with `ValueError` propagating. Checking the project's lint/type setup and adding a release note.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; grep -n \"ruff\\|mypy\" pyproject.toml | head; ($PY -m ruff --version && $PY -m ruff check tenacity tests && $PY -m ruff format --check tenacity tests) 2>&1 | tail -8; ($PY -m mypy tenacity 2>&1 | tail -3) ; ls releasenotes/notes | grep -i \"enabled\"; grep -rl \"enabled\" releasenotes/notes | head -3", "description": "Run ruff and mypy if available; check release notes"}
[tool_result] 58:    "ruff",
59:    "mypy",
71:mypy = "mypy"
76:    { cmd = "ruff check --fix ." },
77:    { cmd = "ruff format ." },
82:    { cmd = "ruff check ." },
83:    { cmd = "ruff format --check ." },
89:    { ref = "mypy" },
98:[tool.ruff]
104:[tool.ruff.lint]
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
[tool_use Bash] {"command": "(command -v ruff && ruff check tenacity tests && ruff format --check tenacity tests) 2>&1 | tail -6; (command -v mypy && mypy tenacity) 2>&1 | tail -3; cat > releasenotes/notes/enabled-false-iterator-3f9a1c2d7e4b8a60.yaml <<'EOF'\n---\nfixes:\n  - |\n    ``Retrying(enabled=False)`` and ``AsyncRetrying(enabled=False)`` now run\n    the body exactly once when used with the iterator pattern\n    (``for attempt in retrying: with attempt: ...``). Exceptions propagate\n    unchanged instead of being wrapped in ``RetryError``, matching the\n    ``@retry(enabled=False)`` decorator behaviour.\nEOF\ngit status --short", "description": "Run ruff/mypy if installed, add release note"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/enabled-false-iterator-3f9a1c2d7e4b8a60.yaml
[assistant] Fixed: `enabled=False` now works with the iterator pattern. The body runs once and exceptions propagate unchanged, for both `Retrying` and `AsyncRetrying`.

**Cause:** The decorator path checks `self.enabled` and calls the function directly. The iterator path (`BaseRetrying.__iter__` and `AsyncRetrying.__aiter__`/`__anext__`) never checked it, so it ran the full retry loop and then raised `RetryError`.

**Changes:**
- `tenacity/__init__.py`: added `_DisabledAttemptManager`, an `AttemptManager` whose `__exit__` returns `None`, so exceptions are not swallowed. `BaseRetrying.__iter__` yields one 
…[266 chars elided]…
un on success.
- `releasenotes/notes/enabled-false-iterator-3f9a1c2d7e4b8a60.yaml`: a `fixes` note.

**Verification:**
- Before the fix, a repro script showed 3 calls and `RetryError` in both the sync and async paths. After the fix it shows 1 call and `ValueError`.
- Full suite with the project's pytest command: 165 passed, 1 skipped.
- I did not confirm the new tests fail on the unfixed code. The repro covers that.
- `ruff` and `mypy` are not installed in the project's environment, so I did not run lint or type checks. The new code follows the existing annotation style.

Nothing is committed.
