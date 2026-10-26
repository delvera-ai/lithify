# trajectory base-1

final message:
`enabled=False` is now respected by the iterator pattern. The body runs once and exceptions propagate unchanged, matching the decorator path. The full suite passes: 163 passed, 1 skipped (trio not installed).

**Cause:** `enabled` was only checked in the decorator path (`wraps()`). `BaseRetrying.__iter__` and `AsyncRetrying.__anext__` ran the normal retry loop regardless, and `AttemptManager.__exit__` swallowed each exception for retry.

**Changes:**
- `tenacity/__init__.py`: `AttemptManager` takes a `propagate` flag. When set, `__exit__` returns without capturing the exception, so it propagates. `BaseRetrying.__iter__` yields one such attempt and returns when `enabled` is false.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__anext__` does the same, yielding one propagating attempt and then stopping. `__aiter__` resets the flag.
- Tests added: `test_enabled_false_iterator_propagates_exception` in `tests/test_tenacity.py` and its async counterpart in `tests/test_asyncio.py`. I did not edit or remove any existing test.
- Release note: `releasenotes/notes/enabled-false-iterator-3c9e1a7b5d2f4e60.yaml`.

I didn't confirm that the new tests fail on the unmodified code. I expect them to, since the old loop would raise `RetryError` instead of `ValueError`. I also haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"enabled\" --include=*.py . | grep -v test | head -50", "description": "Check repo status and find enabled references"}
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
[tool_use Bash] {"command": "grep -rn \"enabled\" tenacity | head -50; echo ---; ls tenacity; echo ---; cat AGENTS.md | head -60", "description": "Search tenacity package for enabled references"}
[tool_result] tenacity/__init__.py:251:        enabled: bool = True,
tenacity/__init__.py:265:        self.enabled = enabled
tenacity/__init__.py:282:        enabled: bool | object = _unset,
tenacity/__init__.py:299:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:367:            if not self.enabled:
tenacity/__init__.py:693:    enabled: bool = ...,
tenacity/__init__.py:711:    enabled: bool = True,
tenacity/asyncio/__init__.py:94:        enabled: bool = True,
tenacity/asyncio/__ini
…[590 chars elided]…
it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "offset": 240, "limit": 480}
[tool_result] 240	        sleep: t.Callable[[int | float], None] = sleep,
241	        stop: "StopBaseT" = stop_never,
242	        wait: "WaitBaseT" = wait_none(),
243	        retry: "RetryBaseT" = retry_if_exception_type(),
244	        before: t.Callable[["RetryCallState"], None] = before_nothing,
245	        after: t.Callable[["RetryCallState"], None] = after_nothing,
246	        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
247	        reraise: bool = False,
248	        retry_error_cls: 
…[18853 chars elided]…
["RetryError"] = RetryError,
709	    retry_error_callback: t.Callable[["RetryCallState"], t.Any | t.Awaitable[t.Any]]
710	    | None = None,
711	    enabled: bool = True,
712	) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...
713	
714	
715	def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
716	    """Wrap a function with a new `Retrying` object.
717	
718	    :param dargs: positional arguments passed to Retrying object
719	    :param dkw: keyword arguments passed to the Retrying object
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "offset": 80, "limit": 150}
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
[assistant] The decorator path checks `self.enabled`, but the iterator paths (`BaseRetrying.__iter__` and `AsyncRetrying.__anext__`) don't. Next I'll look at `AttemptManager` to see how exceptions are handled inside a `with attempt:` block.
[tool_use Bash] {"command": "grep -n \"class AttemptManager\" -A 25 tenacity/__init__.py; grep -rln \"enabled\" tests; grep -rn \"enabled\" tests | head -30; ls releasenotes/notes | tail -5", "description": "Inspect AttemptManager and existing enabled tests"}
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
…[1566 chars elided]…
:    def test_enabled_true_retries_normally(self) -> None:
tests/test_tenacity.py:1550:        """When enabled=True (default), retrying works as usual."""
tests/test_tenacity.py:1553:        @retry(enabled=True, stop=tenacity.stop_after_attempt(3), reraise=True)
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The disabled path has to skip the retry machinery entirely. `AttemptManager.__exit__` swallows exceptions and records them for retry, so the disabled path needs an attempt that lets exceptions through. Let me check `__aexit__` and the existing tests before I edit.
[tool_use Bash] {"command": "sed -n 225,245p tenacity/__init__.py; sed -n 1505,1570p tests/test_tenacity.py; sed -n 160,190p tests/test_asyncio.py; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; ls .lithify 2>/dev/null; ls <work>/env-tenacity/bin/python", "description": "Read __aexit__, existing tests, release note format"}
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
        stop: "StopBaseT" = stop_never,
        wait: "WaitBaseT" = wait_
…[3034 chars elided]…
.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)

        @retry
        async def trio_function() -> Any:
            await trio.sleep(0.00001)
            return thing.go()

        trio.run(trio_function)
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
harness
library
state.json
<work>/env-tenacity/bin/python
[assistant] The fix has three parts: `AttemptManager` gets a `propagate` mode that lets exceptions through, and both iterator entry points return a single attempt when `enabled` is false. I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "    def __init__(self, retry_state: \"RetryCallState\"):\n        self.retry_state = retry_state\n\n    def __enter__(self) -> None:\n        pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseExcep
…[411 chars elided]…
n        self.propagate = propagate\n\n    def __enter__(self) -> None:\n        pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: \"types.TracebackType | None\",\n    ) -> bool | None:\n        if self.propagate:\n            return None\n        if exc_type is not None and exc_value is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py", "old_string": "    def __iter__(self) -> t.Generator[AttemptManager, None, None]:\n        self.begin()\n\n        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        while True:", "new_string": "    def __iter__(self) -> t.Generator[AttemptManager, None, None]:\n        self.begin()\n\n        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        if not self.enabled:\n            # Run the body exactly once; exceptions propagate unchanged.\n            yield AttemptManager(retry_state=retry_state, propagate=True)\n            return\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py", "old_string": "        self.begin()\n        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})\n        return self\n\n    async def __anext__(self) -> AttemptManager:\n        while True:", "new_string"
…[173 chars elided]…
\n    async def __anext__(self) -> AttemptManager:\n        if not self.enabled:\n            # Run the body exactly once; exceptions propagate unchanged.\n            if self._disabled_attempt_yielded:\n                raise StopAsyncIteration\n            self._disabled_attempt_yielded = True\n            return AttemptManager(retry_state=self._retry_state, propagate=True)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now I'll add regression tests for the iterator paths next to the existing `enabled=False` tests, plus a release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py", "old_string": "    def test_enabled_false_preserves_attributes(self) -> None:", "new_string": "    def test_enabled_false_iterator_runs_once(self) -> None:\n        \"\"\"When enabled=False, the iterator pattern runs the body exa
…[1025 chars elided]…
\n        \"\"\"When enabled=False, a successful iterator body also runs exactly once.\"\"\"\n        call_count = 0\n        retrying = tenacity.Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        for attempt in retrying:\n            with attempt:\n                call_count += 1\n        assert call_count == 1\n\n    def test_enabled_false_preserves_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")", "new_string": "        with py
…[316 chars elided]…
t = 0\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            async for attempt in retrying:\n                async with attempt:\n                    call_count += 1\n                    raise ValueError(\"fail\")\n        assert call_count == 1\n\n\n@unittest.skipIf(not have_trio, \"trio not installed\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/enabled-false-iterator-3c9e1a7b5d2f4e60.yaml <<'EOF'\n---\nfixes:\n  - |\n    ``enabled=False`` is now respected by the iterator pattern (``for attempt in\n    Retrying(...)`` and ``async for attempt in AsyncRetrying(...)``). The body runs\n    exactly once and exceptions propagate unchanged, matching the decorator path.\nEOF\ngrep -n \"AsyncRetrying\" tests/test_asyncio.py | head -3; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Add release note, check imports, run test suite"}
[tool_result] 34:    AsyncRetrying,
94:        retrying = AsyncRetrying()
107:        repr(tasyncio.AsyncRetrying())
.............s.......................................................................................................F.............. [ 80%]
.................................                                        [100%]
=================================== FAILURES ===================================
______________ TestEnabled.test_enabled_false_iterator_runs_once _______________

self = <tests.
…[231 chars elided]…
enabled=False, stop=tenacity.stop_after_attempt(3))
        attempts = 0
        for attempt in retrying:
            with attempt:
                attempts += 1
>               raise ValueError("fail")
E               ValueError: fail

tests/test_tenacity.py:1529: ValueError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_iterator_runs_once
1 failed, 163 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] One test I wrote is wrong: `test_enabled_false_iterator_runs_once` lets the `ValueError` escape without a `pytest.raises`, and it duplicates the propagate test. I'll delete it and keep the other two.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py", "old_string": "    def test_enabled_false_iterator_runs_once(self) -> None:\n        \"\"\"When enabled=False, the iterator pattern runs the body exactly once.\"\"\"\n        retrying = tenacity.Retrying(enabled=False, stop=tenac
…[111 chars elided]…
                attempts += 1\n                raise ValueError(\"fail\")\n        # Unreachable: the ValueError above propagates out of the loop.\n        raise AssertionError(\"expected ValueError to propagate\")  # pragma: no cover\n\n    def test_enabled_false_iterator_propagates_exception(self) -> None:", "new_string": "    def test_enabled_false_iterator_propagates_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161652-bug-retrying-enabled-false-is-ig/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git diff --stat", "description": "Rerun test suite and show diff stats"}
[tool_result] .............s...................................................................................................................... [ 80%]
................................                                         [100%]
163 passed, 1 skipped, 12 subtests passed in 1.82s
 tenacity/__init__.py         | 10 +++++++++-
 tenacity/asyncio/__init__.py |  7 +++++++
 tests/test_asyncio.py        | 12 ++++++++++++
 tests/test_tenacity.py       | 20 ++++++++++++++++++++
 4 files changed, 48 insertions(+), 1 deletion(-)
[assistant] `enabled=False` is now respected by the iterator pattern. The body runs once and exceptions propagate unchanged, matching the decorator path. The full suite passes: 163 passed, 1 skipped (trio not installed).

**Cause:** `enabled` was only checked in the decorator path (`wraps()`). `BaseRetrying.__iter__` and `AsyncRetrying.__anext__` ran the normal retry loop regardless, and `AttemptManager.__exit__` swallowed each exception for retry.

**Changes:**
- `tenacity/__init__.py`: `AttemptManager` takes a `propagate` flag. When set, `__exit__` returns without capturing the exception, so it propagat
…[107 chars elided]…
o/__init__.py`: `AsyncRetrying.__anext__` does the same, yielding one propagating attempt and then stopping. `__aiter__` resets the flag.
- Tests added: `test_enabled_false_iterator_propagates_exception` in `tests/test_tenacity.py` and its async counterpart in `tests/test_asyncio.py`. I did not edit or remove any existing test.
- Release note: `releasenotes/notes/enabled-false-iterator-3c9e1a7b5d2f4e60.yaml`.

I didn't confirm that the new tests fail on the unmodified code. I expect them to, since the old loop would raise `RetryError` instead of `ValueError`. I also haven't committed anything.
