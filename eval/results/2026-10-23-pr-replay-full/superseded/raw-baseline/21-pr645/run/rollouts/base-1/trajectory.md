# trajectory base-1

final message:
`Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The project suite passes: 181 passed, 1 skipped.

**The cause:** `__call__` on both classes had no `enabled` check. The decorator (`wraps`) and iterator (`__iter__` / `__aiter__`) paths already had one, so only direct calls ran the retry loop.

**The fix:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` early when disabled.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting `fn` when it is a coroutine function. This follows the existing `is_async` check in that method.

**Tests added:** `test_enabled_false_call_raises_original_exception` in `tests/test_tenacity.py` and `tests/test_asyncio.py`. Both assert one call and the original `ValueError`. I did not run them against the unpatched code to confirm they fail there. A standalone repro showed one call and the original `ValueError` after the fix.

Nothing is committed. The changes are in the working tree of this worktree.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"enabled\" tenacity/*.py | head -60", "description": "Check status and find enabled references"}
[tool_result] tenacity/__init__.py:263:        enabled: bool = True,
tenacity/__init__.py:277:        self.enabled = enabled
tenacity/__init__.py:294:        enabled: bool | object = _unset,
tenacity/__init__.py:311:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:382:            if not self.enabled:
tenacity/__init__.py:501:        if not self.enabled:
tenacity/__init__.py:746:    enabled: bool = ...,
tenacity/__init__.py:764:    enabled: bool = True,
[tool_use Bash] {"command": "sed -n 370,400p tenacity/__init__.py && echo ---- && sed -n 490,530p tenacity/__init__.py && echo ---- && grep -n \"def __call__\\|def wraps\\|class \\|def __iter__\\|def __aiter__\" tenacity/__init__.py tenacity/asyncio/__init__.py", "description": "Read enabled checks and call paths"}
[tool_result]         return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.
        """

        @functools.wraps(
            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:
            if not self.enabled:
                return f(*args, **kw)
       
…[3760 chars elided]…
it__.py:719:    def __call__(
tenacity/__init__.py:723:    def __call__(
tenacity/asyncio/__init__.py:75:class AsyncRetrying(BaseRetrying):
tenacity/asyncio/__init__.py:113:    async def __call__(  # type: ignore[override]
tenacity/asyncio/__init__.py:175:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:178:    def __aiter__(self) -> "AsyncRetrying":
tenacity/asyncio/__init__.py:211:    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
[tool_use Bash] {"command": "sed -n 531,560p tenacity/__init__.py && echo ---- && sed -n 1,20p tenacity/asyncio/__init__.py | grep -n import; sed -n 105,260p tenacity/asyncio/__init__.py", "description": "Read Retrying.__call__ and asyncio module"}
[tool_result] class Retrying(BaseRetrying):
    """Retrying controller."""

    @override
    def __call__(
        self,
        fn: t.Callable[..., WrappedFnReturnT],
        *args: t.Any,
        **kwargs: t.Any,
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        while True:
            do = self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                try:
                    resul
…[5870 chars elided]…
 copy(fn, *args, **kwargs)  # type: ignore[type-var]

        # Preserve attributes
        async_wrapped.retry = self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
        async_wrapped.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
    "AsyncRetrying",
    "WrappedFn",
    "retry_all",
    "retry_any",
    "retry_if_exception",
    "retry_if_result",
]
[assistant] The bug is clear: `Retrying.__call__` and `AsyncRetrying.__call__` have no `enabled` check, while `wraps()` and `__iter__` do. I'll add the same early return to both `__call__` methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)", "new_string": "    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py", "old_string": "    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        is_async = _utils.is_coroutine_callable(fn)", "new_string": "    ) -> WrappedFnReturnT:\n        is_async = _utils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                return await fn(*args, **kwargs)  # type: ignore[misc]\n            return fn(*args, **kwargs)  # type: ignore[no-any-return]\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Both edits are in. Next I'll confirm the bug reproduces on the original code, then run the project's check command against the change.
[tool_use Bash] {"command": "cat > /tmp/repro_enabled.py <<'EOF'\nimport asyncio\nfrom tenacity import Retrying, RetryError\nfrom tenacity.asyncio import AsyncRetrying\ncalls = []\ndef f():\n    calls.append(1); raise ValueError(\"boom\")\nasync def g():\n    calls.append(1); raise ValueError(\"boom\")\nfor name, fn, r in [(\"sync\", f, Retrying(enabled=False, stop=lambda s: False)), (\"async\", g, AsyncRetrying(
…[344 chars elided]…
ity/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_enabled.py').read())\"; echo \"--- tests\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Reproduce fix and run project test suite"}
[tool_result] sync ValueError calls= 1
async ValueError calls= 1
--- tests
................s................................................................................................................ [ 71%]
...................................................                      [100%]
179 passed, 1 skipped, 15 subtests passed in 1.89s
[assistant] The repro now shows one call and the original `ValueError`, and the suite passes (179 passed, 1 skipped). I'll add regression tests so this doesn't come back.
[tool_use Bash] {"command": "grep -rn \"enabled\" tests/ | head -30", "description": "Find existing enabled tests"}
[tool_result] tests/test_tenacity.py:1654:    def test_enabled_false_skips_retry(self) -> None:
tests/test_tenacity.py:1655:        """When enabled=False, the function is called directly without retrying."""
tests/test_tenacity.py:1658:        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))
tests/test_tenacity.py:1668:    def test_enabled_false_preserves_attributes(self) -> None:
tests/test_tenacity.py:1669:        """When enabled=False, .retry, .retry_with, .statistics are still available."""
test
…[1492 chars elided]…
nc def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests/test_asyncio.py:223:            enabled=False,
tests/test_asyncio.py:234:    async def test_enabled_false_aiter_succeeds_on_first_attempt(self) -> None:
tests/test_asyncio.py:235:        """When enabled=False, the async iterator runs the body once and stops."""
tests/test_asyncio.py:238:            enabled=False,
[tool_use Bash] {"command": "sed -n 1680,1745p tests/test_tenacity.py && echo ---- && sed -n 200,250p tests/test_asyncio.py", "description": "Read existing enabled test style"}
[tool_result]     def test_enabled_false_via_retry_with(self) -> None:
        """retry_with(enabled=False) disables retrying."""
        call_count = 0

        @retry(stop=tenacity.stop_after_attempt(3))
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        disabled = always_fails.retry_with(enabled=False)
        with pytest.raises(ValueError, match="fail"):
            disabled()
        assert call_count == 1

    def
…[3085 chars elided]…
en enabled=False, the async iterator runs the body once and stops."""
        call_count = 0
        retrying = AsyncRetrying(
            enabled=False,
            stop=stop_after_attempt(5),
        )
        async for attempt in retrying:
            with attempt:
                call_count += 1
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
class TestTrio(unittest.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py", "old_string": "        disabled = always_fails.retry_with(enabled=False)\n        with pytest.raises(ValueError, match=\"fail\"):\n            disabled()\n        assert call_count == 1\n\n", "new_string": "        disabled = alw
…[352 chars elided]…
t a RetryError.\"\"\"\n        call_count = 0\n\n        def always_fails() -> None:\n            nonlocal call_count\n            call_count += 1\n            raise ValueError(\"fail\")\n\n        retrying = Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            retrying(always_fails)\n        assert call_count == 1\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py", "old_string": "        with pytest.raises(ValueError, match=\"fail\"):\n            await always_fails()\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> 
…[480 chars elided]…
 nonlocal call_count\n            call_count += 1\n            raise ValueError(\"fail\")\n\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            await retrying(always_fails)\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165658-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git diff --stat", "description": "Run full test suite and show diff stat"}
[tool_result] .................s.............................................. [ 35%]
................................................................. [ 70%]
.....................................................                    [100%]
181 passed, 1 skipped, 15 subtests passed in 1.93s
 tenacity/__init__.py         |  3 +++
 tenacity/asyncio/__init__.py |  7 ++++++-
 tests/test_asyncio.py        | 16 ++++++++++++++++
 tests/test_tenacity.py       | 15 +++++++++++++++
 4 files changed, 40 insertions(+), 1 deletion(-)
[assistant] `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The project suite passes: 181 passed, 1 skipped.

**The cause:** `__call__` on both classes had no `enabled` check. The decorator (`wraps`) and iterator (`__iter__` / `__aiter__`) paths already had one, so only direct calls ran the retry loop.

**The fix:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` early when disabled.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting `fn` when it is a coroutine function. This follows the existing `is_async` check in that method.

**Tests added:** `test_enabled_false_call_raises_original_exception` in `tests/test_tenacity.py` and `tests/test_asyncio.py`. Both assert one call and the original `ValueError`. I did not run them against the unpatched code to confirm they fail there. A standalone repro showed one call and the original `ValueError` after the fix.

Nothing is committed. The changes are in the working tree of this worktree.
