# trajectory base-1

final message:
Calling `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now runs `fn` once and propagates its exception unchanged. The full suite passes (183 passed, 1 skipped).

**Cause:** `enabled` was checked in the decorator path (`wraps`) and the iterator path (`__iter__` / `__aiter__`), but not in `__call__`. So `__call__` ran the whole retry loop and wrapped the failure in `RetryError`.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` straight away when disabled. Before `begin()`, so statistics stay untouched, as on the decorator path.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same. It awaits `fn` when `fn` is a coroutine function, and calls it directly otherwise. The async-or-sync check moved above the disabled branch so both cases are handled.
- Tests: two regression tests per class in `tests/test_tenacity.py` and `tests/test_asyncio.py`. They cover the exception case and the success case. On the original code, the two exception tests fail with `RetryError`. The success tests already passed before the fix and are there to guard the return value.
- Release note: `releasenotes/notes/retrying-call-enabled-false-3f9c2a7d1e8b4c60.yaml`, a `fixes` entry.

**Mishap:** while checking the failing tests against the original code, I restored the files with a `cp` whose two backups had the same filename. That overwrote `tenacity/__init__.py` with the asyncio module. I restored that file from HEAD with `git checkout` and re-applied the 3-line edit. The asyncio module was never affected. The final diff is `tenacity/__init__.py` (+3), `tenacity/asyncio/__init__.py` (+6/−1), the two test files, and the release note. I did not run a linter or type checker.

Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -n \"enabled\" tenacity/*.py | head -60", "description": "Check repo state and find enabled references"}
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
tenacity/__init__.py:263:        enabled: bool = True,
tenacity/__init__.py:277:        self.enabled = enabled
tenacity/__init__.py:294:        enabled: bool | object = _unset,
tenacity/__init__.py:311:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:382:            if not self.enabled:
tenacity/__init__.py:501:        if not self.enabled:
tenacity/__init__.py:746:    enabled: bool = ...,
tenacity/__init__.py:764:    enabled: bool = True,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 250, "limit": 300}
[tool_result] 250	    def __init__(
251	        self,
252	        sleep: t.Callable[[int | float], None] = sleep,
253	        stop: "StopBaseT" = stop_never,
254	        wait: "WaitBaseT" = wait_none(),
255	        retry: "RetryBaseT" = retry_if_exception_type(),
256	        before: t.Callable[["RetryCallState"], None] = before_nothing,
257	        after: t.Callable[["RetryCallState"], None] = after_nothing,
258	        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
259	        reraise: boo
…[12309 chars elided]…
       fn: t.Callable[..., WrappedFnReturnT],
538	        *args: t.Any,
539	        **kwargs: t.Any,
540	    ) -> WrappedFnReturnT:
541	        self.begin()
542	
543	        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
544	        while True:
545	            do = self.iter(retry_state=retry_state)
546	            if isinstance(do, DoAttempt):
547	                try:
548	                    result = fn(*args, **kwargs)
549	                except BaseException:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 480, "limit": 60}
[tool_result] 480	                    retry_exc.reraise()
481	                raise retry_exc from fut.exception()
482	
483	            self._add_action_func(exc_check)
484	            return
485	
486	        def next_action(rs: "RetryCallState") -> None:
487	            sleep = rs.upcoming_sleep
488	            rs.next_action = RetryAction(sleep)
489	            rs.idle_for += sleep
490	            self.statistics["idle_for"] += sleep
491	            self.statistics["attempt_number"] += 1
492	
493	        se
…[1117 chars elided]…
se:
519	                break
520	
521	    @abstractmethod
522	    def __call__(
523	        self,
524	        fn: t.Callable[..., WrappedFnReturnT],
525	        *args: t.Any,
526	        **kwargs: t.Any,
527	    ) -> WrappedFnReturnT:
528	        pass
529	
530	
531	class Retrying(BaseRetrying):
532	    """Retrying controller."""
533	
534	    @override
535	    def __call__(
536	        self,
537	        fn: t.Callable[..., WrappedFnReturnT],
538	        *args: t.Any,
539	        **kwargs: t.Any,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 540, "limit": 150}
[tool_result] 540	    ) -> WrappedFnReturnT:
541	        self.begin()
542	
543	        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
544	        while True:
545	            do = self.iter(retry_state=retry_state)
546	            if isinstance(do, DoAttempt):
547	                try:
548	                    result = fn(*args, **kwargs)
549	                except BaseException:
550	                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
551	    
…[4869 chars elided]…
1	    statistics: dict[str, t.Any]
682	    # Set by functools.wraps on the retry wrapper. Declared so that the
683	    # statistics stay accessible in a type-safe way even when the decorated
684	    # function is further wrapped by another functools.wraps-based decorator
685	    # (which copies these attributes onto the outer wrapper). See issue #519.
686	    __wrapped__: "_RetryDecorated[P, R]"
687	
688	    def retry_with(self, *args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]": ...
689	
[tool_use Bash] {"command": "grep -n \"enabled\" tests/*.py | head -40; ls releasenotes/notes | tail -5", "description": "Find enabled tests and recent release notes"}
[tool_result] tests/test_asyncio.py:203:    async def test_enabled_false_skips_retry(self) -> None:
tests/test_asyncio.py:204:        """When enabled=False, async function is called directly without retrying."""
tests/test_asyncio.py:207:        @retry(enabled=False, stop=stop_after_attempt(3))
tests/test_asyncio.py:218:    async def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests
…[1725 chars elided]…
sts/test_tenacity.py:1726:    def test_enabled_false_iter_succeeds_on_first_attempt(self) -> None:
tests/test_tenacity.py:1727:        """When enabled=False, the iterator protocol runs the body once and stops."""
tests/test_tenacity.py:1730:            enabled=False,
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "grep -n \"def __call__\" -A40 tenacity/asyncio/__init__.py | head -80; grep -n \"enabled\" tenacity/asyncio/__init__.py; sed -n 1,30p tenacity/asyncio/__init__.py | grep -n import", "description": "Inspect AsyncRetrying.__call__ implementation"}
[tool_result] 113:    async def __call__(  # type: ignore[override]
114-        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any
115-    ) -> WrappedFnReturnT:
116-        self.begin()
117-
118-        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
119-        is_async = _utils.is_coroutine_callable(fn)
120-        while True:
121-            do = await self.iter(retry_state=retry_state)
122-            if isinstance(do, DoAttempt):
123-                try:
124-            
…[1190 chars elided]…
-        # See BaseRetrying._run_wait: falsy `wait` values mean "no wait" and
151-        # reach us from untyped callers.
152-        if not self.wait:  # type: ignore[truthy-bool]
153-            retry_state.upcoming_sleep = 0.0
95:        enabled: bool = True,
109:            enabled=enabled,
179:        if not self.enabled:
189:        if not self.enabled:
219:            if not self.enabled:
18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
[tool_use Bash] {"command": "sed -n 170,240p tenacity/asyncio/__init__.py; sed -n 200,250p tests/test_asyncio.py; sed -n 1650,1668p tests/test_tenacity.py", "description": "Read async wrapper and existing enabled tests"}
[tool_result]         for action in self.iter_state.actions:
            result = await action(retry_state)
        return result

    @override
    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        raise TypeError("AsyncRetrying object is not iterable")

    def __aiter__(self) -> "AsyncRetrying":
        if not self.enabled:
            self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
            self._disabled_iter_done = False
            return self

        self
…[4521 chars elided]…
(self) -> None:
        """When enabled=False, the function is called directly without retrying."""
        call_count = 0

        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            always_fails()
        assert call_count == 1

    def test_enabled_false_preserves_attributes(self) -> None:
[tool_use Bash] {"command": "cat AGENTS.md | head -60; cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml; git log -3 --stat --format='%h %s' | head -40", "description": "Read agent guidance and release note convention"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[1317 chars elided]…
|  18 +++
 CLAUDE.md                         |  18 +++
 tenacity/_version.py              |   2 +
 11 files changed, 400 insertions(+)
949dcfa fix: read the tornado global live instead of an import-time snapshot (#696)

 .../notes/fix-tornado-global-desync-8c2d40fa71b9e35a.yaml |  7 +++++++
 tenacity/__init__.py                                      | 15 +++++++++------
 tests/test_tornado.py                                     | 13 +++++++++++++
 3 files changed, 29 insertions(+), 6 deletions(-)
[assistant] Now the fix. The decorator and iterator paths already check `enabled`; `__call__` on both classes does not.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        is_async = _utils.is_coroutine_callable(fn)\n        while True:", "new_string": "    ) -> WrappedFnReturnT:\n        is_async = _utils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                return await fn(*args, **kwargs)\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now regression tests next to the existing `enabled=False` tests, one for each class.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            always_fails()\n        assert call_count == 1\n\n    def test_enabled_false_preserves_attributes(self) -> None:", "new_string": "        with py
…[946 chars elided]…
  call_count = 0\n        retrying = tenacity.Retrying(\n            enabled=False, stop=tenacity.stop_after_attempt(3)\n        )\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        assert retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n    def test_enabled_false_preserves_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> 
…[1023 chars elided]…
call_count = 0\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        assert await retrying(succeeds) == \"ok\"\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/retrying-call-enabled-false-3f9c2a7d1e8b4c60.yaml <<'EOF'\n---\nfixes:\n  - |\n    Calling a ``Retrying`` or ``AsyncRetrying`` object directly with a function\n    (``retrying(fn)``) now honours ``enabled=False``. The function is called\n    exactly once and its exception propagates unchanged instead of being\n    wrapped in ``RetryError`` after the full retry loop, matching the decorator\n    and iterator paths.\nEOF\nPY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Add release note and run the project test suite"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
..................s.............................................................................................................. [ 70%]
.......................................................                  [100%]
183 passed, 1 skipped, 15 subtests passed in 2.04s
[assistant] All 183 pass. To confirm the new tests actually catch the bug, I'll run them against the original source files, then restore my fix.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; mkdir -p /tmp/retry-fix-backup && cp tenacity/__init__.py tenacity/asyncio/__init__.py /tmp/retry-fix-backup/ && git show HEAD:tenacity/__init__.py > tenacity/__init__.py && git show HEAD:tenacity/asyncio/__init__.py > tenacity/
…[43 chars elided]…
no:cacheprovider --color=no -k \"call_raises_original or call_returns_result or call_sync_fn\" 2>&1 | tail -6; cp /tmp/retry-fix-backup/__init__.py tenacity/__init__.py && cp /tmp/retry-fix-backup/__init__.py tenacity/asyncio/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Verify new tests fail on original code, then restore fix"}
[tool_result] tenacity/__init__.py:481: RetryError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_call_raises_original_exception
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_call_raises_original_exception
2 failed, 2 passed, 180 deselected in 0.16s
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
6 errors in 0.15s
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/retrying-call-enabled-false-3f9c2a7d1e8b4c60.yaml
[assistant] The restore step went wrong: both backup files had the same basename, so the copy overwrote one with the other. Checking the actual state before doing anything else.
[tool_use Bash] {"command": "git diff --stat; git diff tenacity/asyncio/__init__.py | head -30; ls -la /tmp/retry-fix-backup/", "description": "Inspect working tree state after faulty restore"}
[tool_result]  tenacity/__init__.py         | 941 ++++++++-----------------------------------
 tenacity/asyncio/__init__.py |   7 +-
 tests/test_asyncio.py        |  31 ++
 tests/test_tenacity.py       |  33 ++
 4 files changed, 234 insertions(+), 778 deletions(-)
diff --git a/tenacity/asyncio/__init__.py b/tenacity/asyncio/__init__.py
index aa4a756..97179ed 100644
--- a/tenacity/asyncio/__init__.py
+++ b/tenacity/asyncio/__init__.py
@@ -113,10 +113,15 @@ class AsyncRetrying(BaseRetrying):
     async def __ca
…[286 chars elided]…
      return fn(*args, **kwargs)
+
         self.begin()
 
         retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
-        is_async = _utils.is_coroutine_callable(fn)
         while True:
             do = await self.iter(retry_state=retry_state)
             if isinstance(do, DoAttempt):
total 24
drwxr-xr-x@   3 user  wheel    96 Oct 23 16:35 .
drwxrwxrwt  163 root     wheel  5216 Oct 23 16:35 ..
-rw-r--r--@   1 user  wheel  9417 Oct 23 16:35 __init__.py
[assistant] The asyncio module is intact. `tenacity/__init__.py` was overwritten with the wrong file, so I'll restore it from HEAD and re-apply the one edit.
[tool_use Bash] {"command": "git checkout -- tenacity/__init__.py && git status --short", "description": "Restore core module from HEAD before re-applying fix"}
[tool_result]  M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/retrying-call-enabled-false-3f9c2a7d1e8b4c60.yaml
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 534, "limit": 10}
[tool_result] 534	    @override
535	    def __call__(
536	        self,
537	        fn: t.Callable[..., WrappedFnReturnT],
538	        *args: t.Any,
539	        **kwargs: t.Any,
540	    ) -> WrappedFnReturnT:
541	        self.begin()
542	
543	        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163501-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "rm -rf /tmp/retry-fix-backup && git diff --stat && PY=<work>/env-tenacity/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Confirm diff stat and rerun full test suite"}
[tool_result]  tenacity/__init__.py         |  3 +++
 tenacity/asyncio/__init__.py |  7 ++++++-
 tests/test_asyncio.py        | 31 +++++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 33 +++++++++++++++++++++++++++++++++
 4 files changed, 73 insertions(+), 1 deletion(-)
.......................................................                  [100%]
183 passed, 1 skipped, 15 subtests passed in 1.86s
[assistant] Calling `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now runs `fn` once and propagates its exception unchanged. The full suite passes (183 passed, 1 skipped).

**Cause:** `enabled` was checked in the decorator path (`wraps`) and the iterator path (`__iter__` / `__aiter__`), but not in `__call__`. So `__call__` ran the whole retry loop and wrapped the failure in `RetryError`.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` straight away when disabled. Before `begin()`, so statistics stay untouched, as on the decorator path.
- `te
…[571 chars elided]…
s/notes/retrying-call-enabled-false-3f9c2a7d1e8b4c60.yaml`, a `fixes` entry.

**Mishap:** while checking the failing tests against the original code, I restored the files with a `cp` whose two backups had the same filename. That overwrote `tenacity/__init__.py` with the asyncio module. I restored that file from HEAD with `git checkout` and re-applied the 3-line edit. The asyncio module was never affected. The final diff is `tenacity/__init__.py` (+3), `tenacity/asyncio/__init__.py` (+6/−1), the two test files, and the release note. I did not run a linter or type checker.

Nothing is committed.
