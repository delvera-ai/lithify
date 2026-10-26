# trajectory base-1

final message:
Fixed: `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The full suite passes (181 passed, 1 skipped, up from 179 because I added two tests).

**Cause:** `wraps()`, `__iter__` and `__aiter__` already checked `self.enabled`, but the two `__call__` methods ran the full retry loop regardless. That is why the direct call retried 3 times and raised `RetryError`.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` when disabled, matching the early return in `wraps()`.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` awaits `fn` when it is a coroutine function, and calls it directly otherwise. I moved the `is_async` check above the guard so both branches can use it.
- `tests/test_tenacity.py` and `tests/test_asyncio.py`: added one regression test each for the direct-call path. I did not modify any existing tests.

**Verification:** Before the fix, a quick script showed the sync call invoking the function 3 times and raising `RetryError`. After the fix, both paths raise the original `ValueError` after a single call. I used the project interpreter from the task instructions and ran the same pytest command.

I did not commit, and I did not add a release note under `releasenotes/`. Say if you want either.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -n \"enabled\" -r tenacity/*.py | head -50", "description": "Inspect repo layout and enabled references"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 250, "limit": 300}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 490, "limit": 40}
[tool_result] 490	            self.statistics["idle_for"] += sleep
491	            self.statistics["attempt_number"] += 1
492	
493	        self._add_action_func(next_action)
494	
495	        if self.before_sleep is not None:
496	            self._add_action_func(self.before_sleep)
497	
498	        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))
499	
500	    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
501	        if not self.enabled:
502	            retry_state = RetryCallState(
…[501 chars elided]…
ce(do, DoAttempt):
514	                yield AttemptManager(retry_state=retry_state)
515	            elif isinstance(do, DoSleep):
516	                retry_state.prepare_for_next_attempt()
517	                self.sleep(do)
518	            else:
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "offset": 531, "limit": 160}
[tool_result] 531	class Retrying(BaseRetrying):
532	    """Retrying controller."""
533	
534	    @override
535	    def __call__(
536	        self,
537	        fn: t.Callable[..., WrappedFnReturnT],
538	        *args: t.Any,
539	        **kwargs: t.Any,
540	    ) -> WrappedFnReturnT:
541	        self.begin()
542	
543	        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
544	        while True:
545	            do = self.iter(retry_state=retry_state)
546	            if isinstanc
…[5179 chars elided]…
he retry wrapper. Declared so that the
683	    # statistics stay accessible in a type-safe way even when the decorated
684	    # function is further wrapped by another functools.wraps-based decorator
685	    # (which copies these attributes onto the outer wrapper). See issue #519.
686	    __wrapped__: "_RetryDecorated[P, R]"
687	
688	    def retry_with(self, *args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]": ...
689	
690	    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
[tool_use Bash] {"command": "grep -n \"enabled\" tests/*.py | head -40; grep -n \"class AsyncRetrying\" -A3 tenacity/asyncio/__init__.py", "description": "Find enabled tests and async class"}
[tool_result] tests/test_asyncio.py:203:    async def test_enabled_false_skips_retry(self) -> None:
tests/test_asyncio.py:204:        """When enabled=False, async function is called directly without retrying."""
tests/test_asyncio.py:207:        @retry(enabled=False, stop=stop_after_attempt(3))
tests/test_asyncio.py:218:    async def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests
…[1598 chars elided]…
n enabled=False, the iterator protocol raises the original exception,
tests/test_tenacity.py:1715:            enabled=False,
tests/test_tenacity.py:1726:    def test_enabled_false_iter_succeeds_on_first_attempt(self) -> None:
tests/test_tenacity.py:1727:        """When enabled=False, the iterator protocol runs the body once and stops."""
tests/test_tenacity.py:1730:            enabled=False,
75:class AsyncRetrying(BaseRetrying):
76-    def __init__(
77-        self,
78-        sleep: t.Callable[
[tool_use Bash] {"command": "sed -n 75,200p tenacity/asyncio/__init__.py", "description": "Read AsyncRetrying class body"}
[tool_result] class AsyncRetrying(BaseRetrying):
    def __init__(
        self,
        sleep: t.Callable[
            [int | float], t.Awaitable[None] | None
        ] = _portable_async_sleep,
        stop: "StopBaseT" = tenacity.stop.stop_never,
        wait: "WaitBaseT" = tenacity.wait.wait_none(),
        retry: "SyncRetryBaseT | RetryBaseT" = tenacity.retry_if_exception_type(),
        before: t.Callable[
            ["RetryCallState"], t.Awaitable[None] | None
        ] = before_nothing,
        after:
…[4051 chars elided]…
 not self.enabled:
            if self._disabled_iter_done:
                outcome = self._retry_state.outcome
                if outcome is not None and outcome.failed:
                    raise outcome.exception()  # type: ignore[misc]
                raise StopAsyncIteration
            self._disabled_iter_done = True
            return AttemptManager(retry_state=self._retry_state)

        while True:
            do = await self.iter(retry_state=self._retry_state)
            if do is None:
[assistant] The bug is clear from the code: `wraps()` and `__iter__`/`__aiter__` check `self.enabled`, but `Retrying.__call__` and `AsyncRetrying.__call__` don't. I'll reproduce it first, then fix it.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -I -c \"\nimport tenacity, asyncio\nfrom tenacity.asyncio import AsyncRetrying\ndef f(): raise ValueError('boom')\ntry: tenacity.Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))(f)\nexcept Exception as e: print('sync:', type(e).__name__, e)\nasync def g(): raise ValueError('boom')\ntry: asyncio.run(AsyncRetrying(enabled=False, stop=tenacity.stop_after_attempt(3))(g))\nexcept Exception as e: print('async:', type(e).__name__, e)\n\" 2>&1 | tail -5", "description": "Reproduce bug with project interpreter"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport tenacity, asyncio\nfrom tenacity.asyncio import AsyncRetrying\ncalls=[]\ndef f(): calls.append(1); raise ValueError('boom')\ntry: tenacity.Retrying(enabled=False, stop=tenacity.stop_after_attemp
…[62 chars elided]…
__, e, 'calls', len(calls))\nasync def g(): calls.append(1); raise ValueError('boom')\ntry: asyncio.run(AsyncRetrying(enabled=False, stop=tenacity.stop_after_attempt(3))(g))\nexcept Exception as e: print('async:', type(e).__name__, e, 'calls', len(calls))\n\" 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Reproduce bug and run baseline test suite"}
[tool_result] sync: RetryError RetryError[<Future at 0x1037ac530 state=finished raised ValueError>] calls 3
async: RetryError RetryError[<Future at 0x1039b3950 state=finished raised ValueError>] calls 6
................s................................................................................................................ [ 71%]
...................................................                      [100%]
179 passed, 1 skipped, 15 subtests passed in 1.82s
[assistant] Reproduced: both paths retry 3 times and raise `RetryError`. Baseline suite is green (179 passed, 1 skipped). Applying the fix in both `__call__` methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n
…[134 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py", "old_string": "        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n      
…[108 chars elided]…
dFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        is_async = _utils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                return await fn(*args, **kwargs)\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `enabled=False` tests, without touching the existing ones.
[tool_use Bash] {"command": "sed -n 1650,1668p tests/test_tenacity.py; echo ----; sed -n 196,234p tests/test_asyncio.py", "description": "View existing enabled=False tests"}
[tool_result]         assert my_call.statistics is my_call.__wrapped__.statistics


class TestEnabled:
    def test_enabled_false_skips_retry(self) -> None:
        """When enabled=False, the function is called directly without retrying."""
        call_count = 0

        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fa
…[1029 chars elided]…
 body executes exactly once."""
        call_count = 0
        retrying = AsyncRetrying(
            enabled=False,
            stop=stop_after_attempt(5),
        )
        with pytest.raises(ValueError, match="fail"):
            async for attempt in retrying:
                with attempt:
                    call_count += 1
                    raise ValueError("fail")
        assert call_count == 1

    @asynctest
    async def test_enabled_false_aiter_succeeds_on_first_attempt(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            always_fails()\n        assert call_count == 1\n\n    def test_enabled_false_preserves_attributes(self) -> None:", "new_string": "        with py
…[388 chars elided]…
ls() -> None:\n            nonlocal call_count\n            call_count += 1\n            raise ValueError(\"fail\")\n\n        retrying = tenacity.Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            retrying(always_fails)\n        assert call_count == 1\n\n    def test_enabled_false_preserves_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> 
…[493 chars elided]…
 nonlocal call_count\n            call_count += 1\n            raise ValueError(\"fail\")\n\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            await retrying(always_fails)\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193157-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no -k \"call_on_retrying_object\" 2>&1 | tail -2; git stash list >/dev/null; PYTHONPATH=$PWD $PY -c \"\nimport tenacity
…[100 chars elided]…
ity.Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))(f)\nexcept Exception as e: print('sync:', type(e).__name__, e)\nasync def g(): raise ValueError('boom')\ntry: asyncio.run(AsyncRetrying(enabled=False, stop=tenacity.stop_after_attempt(3))(g))\nexcept Exception as e: print('async:', type(e).__name__, e)\n\"; git diff --stat", "description": "Run full suite, new tests, and verify fix"}
[tool_result] ................................................................. [ 70%]
.....................................................                    [100%]
181 passed, 1 skipped, 15 subtests passed in 1.78s
..                                                                       [100%]
2 passed, 180 deselected in 0.03s
sync: ValueError boom
async: ValueError boom
 tenacity/__init__.py         |  3 +++
 tenacity/asyncio/__init__.py |  7 ++++++-
 tests/test_asyncio.py        | 16 ++++++++++++++++
 tests/test_tenacity.py       | 15 +++++++++++++++
 4 files changed, 40 insertions(+), 1 deletion(-)
[assistant] Fixed: `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The full suite passes (181 passed, 1 skipped, up from 179 because I added two tests).

**Cause:** `wraps()`, `__iter__` and `__aiter__` already checked `self.enabled`, but the two `__call__` methods ran the full retry loop regardless. That is why the direct call retried 3 times and raised `RetryError`.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` when disabled, matching the early return in `wraps()`.
- `tenacity/async
…[139 chars elided]…
nc` check above the guard so both branches can use it.
- `tests/test_tenacity.py` and `tests/test_asyncio.py`: added one regression test each for the direct-call path. I did not modify any existing tests.

**Verification:** Before the fix, a quick script showed the sync call invoking the function 3 times and raising `RetryError`. After the fix, both paths raise the original `ValueError` after a single call. I used the project interpreter from the task instructions and ran the same pytest command.

I did not commit, and I did not add a release note under `releasenotes/`. Say if you want either.
