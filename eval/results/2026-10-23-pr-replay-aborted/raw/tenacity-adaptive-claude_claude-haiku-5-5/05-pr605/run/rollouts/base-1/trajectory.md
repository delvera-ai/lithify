# trajectory base-1

final message:
`AttemptManager` now supports `async with`, so `async with attempt:` inside `async for` works and behaves like `with attempt:`.

**Changes**

- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the sync and async paths share one implementation: exceptions are recorded on the retry state and swallowed for retry, and success sets the result to `None`.
- **`tests/test_asyncio.py`**: added two tests next to the existing `test_do_max_attempts`:
  - `test_do_max_attempts_async_with` runs the max-attempts loop using `async with`.
  - `test_async_with_success_sets_result` checks that a successful `async with` block records a non-failed outcome with result `None`.

**Verification**

- The full suite passes: 140 passed, 1 skipped, 12 subtests passed.
- `ruff` and `mypy` are not installed in the project's test environment, so I did not run them. I did not install them.

I haven't committed anything. I also haven't checked the new tests against the original code to confirm they fail there. Without the new methods, `async with` raises `TypeError`, so they would fail.

## events
[tool_use Bash] {"command": "grep -rn \"AttemptManager\" --include=*.py --include=*.md . | head -50", "description": "Locate AttemptManager references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"AttemptManager\" . --exclude-dir=.git | head -50", "description": "Locate AttemptManager references"}
[tool_result] tenacity/__init__.py:195:class AttemptManager:
tenacity/__init__.py:443:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/__init__.py:450:                yield AttemptManager(retry_state=retry_state)
tenacity/__init__.py:725:    "AttemptManager",
tenacity/asyncio/__init__.py:24:    AttemptManager,
tenacity/asyncio/__init__.py:163:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:171:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:177:                return AttemptManager(retry_state=self._retry_state)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "offset": 190, "limit": 30}
[tool_result] 190	
191	    def __str__(self) -> str:
192	        return f"{self.__class__.__name__}[{self.last_attempt}]"
193	
194	
195	class AttemptManager:
196	    """Manage attempt context."""
197	
198	    def __init__(self, retry_state: "RetryCallState"):
199	        self.retry_state = retry_state
200	
201	    def __enter__(self) -> None:
202	        pass
203	
204	    def __exit__(
205	        self,
206	        exc_type: type[BaseException] | None,
207	        exc_value: BaseException | None,
208	        traceback: t.Optional["types.TracebackType"],
209	    ) -> bool | None:
210	        if exc_type is not None and exc_value is not None:
211	            self.retry_state.set_exception((exc_type, exc_value, traceback))
212	            return True  # Swallow exception.
213	        # We don't have the result, actually.
214	        self.retry_state.set_result(None)
215	        return None
216	
217	
218	class BaseRetrying(ABC):
219	    def __init__(
[tool_use Bash] {"command": "ls tests && grep -rn \"with attempt\\|async with\\|for attempt in\" tests docs README* 2>/dev/null | head -30", "description": "Find existing attempt-context usage in tests and docs"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
tests/test_asyncio.py:184:            async for attempt in retrying:
tests/test_asyncio.py:185:                with attempt:
tests/test_asyncio.py:199:            async for attempt in tasyncio.AsyncRetrying(
tests/test_asyncio.py:202:                with attempt:
tests/test_asyncio.py:213:            async for attempt in tasyncio.AsyncRetrying(
tests/test_asyncio.py:216:                with
…[1196 chars elided]…
for attempt in Retrying(
tests/test_tenacity.py:174:                with attempt:
tests/test_tenacity.py:1728:        for attempt in Retrying():
tests/test_tenacity.py:1729:            with attempt:
tests/test_tenacity.py:1743:            for attempt in retry:
tests/test_tenacity.py:1744:                with attempt:
tests/test_tenacity.py:1755:            for attempt in retry:
tests/test_tenacity.py:1756:                with attempt:
tests/test_tenacity.py:1770:            for attempt in retry:
[assistant] Now I'll add the async protocol methods, delegating to the existing sync logic so behavior stays identical.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "old_string": "        # We don't have the result, actually.\n        self.retry_state.set_result(None)\n        return None\n\n\nclass BaseRetrying(ABC):", "new_string": "        # We don't have the result, actually.\n        self
…[32 chars elided]…
       return None\n\n    async def __aenter__(self) -> None:\n        return self.__enter__()\n\n    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.TracebackType\"],\n    ) -> bool | None:\n        return self.__exit__(exc_type, exc_value, traceback)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, tests. I'll look at the existing async test style first.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "offset": 170, "limit": 50}
[tool_result] 170	            await trio.sleep(0.00001)
171	            return thing.go()
172	
173	        trio.run(trio_function)
174	
175	        assert thing.counter == thing.count
176	
177	
178	class TestContextManager(unittest.TestCase):
179	    @asynctest
180	    async def test_do_max_attempts(self) -> None:
181	        attempts = 0
182	        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
183	        try:
184	            async for attempt in retrying:
185	                with attempt:
1
…[542 chars elided]…
04	        except CustomError:
205	            pass
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
217	                    raise Exception()
218	        except RetryError:
219	            pass
[tool_use Bash] {"command": "sed -n 220,240p tests/test_asyncio.py", "description": "Read the following test block for insertion point"}
[tool_result]         t = current_time_ms() - start
        self.assertLess(t, 1.1)

    @asynctest
    async def test_retry_with_result(self) -> None:
        async def test() -> int:
            attempts = 0

            # mypy doesn't have great lambda support
            def lt_3(x: float) -> bool:
                return x < 3

            async for attempt in tasyncio.AsyncRetrying(retry=retry_if_result(lt_3)):
                with attempt:
                    attempts += 1
                attempt.retry_state.set_result(attempts)
            return attempts

        result = await test()

        self.assertEqual(3, result)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "        except RetryError:\n            pass\n\n        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:", "new_string": "        except RetryError:\n            pass\n\n        asse
…[521 chars elided]…
       retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))\n        async for attempt in retrying:\n            async with attempt:\n                pass\n\n        assert retrying.iter_state.actions  # sanity: loop ran\n        self.assertEqual(\n            retrying.statistics[\"attempt_number\"],\n            1,\n        )\n\n    @asynctest\n    async def test_reraise(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] That second test uses attributes I haven't verified. I'll rewrite it to check the retry state directly, the way the sync `with` path does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_async_with_success_sets_result(self) -> None:\n        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))\n        async for attempt in retrying:\n            async with
…[177 chars elided]…
,\n            1,\n        )", "new_string": "    @asynctest\n    async def test_async_with_success_sets_result(self) -> None:\n        async for attempt in tasyncio.AsyncRetrying(stop=stop_after_attempt(3)):\n            async with attempt:\n                pass\n            self.assertFalse(attempt.retry_state.outcome.failed)\n            self.assertIsNone(attempt.retry_state.outcome.result())"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155347-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "( <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 || true ) | tail -30", "description": "Run the project test suite"}
[tool_result] ...........s................................................ [ 42%]
........................................................................ [ 93%]
.........                                                                [100%]
140 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] All 140 pass. I'll run the project's linters too, if configured.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin; for t in ruff mypy; do if [ -x $P/$t ]; then echo \"== $t\"; $P/$t $( [ $t = ruff ] && echo \"check tenacity tests\" || echo \"tenacity\" ) 2>&1 | tail -5; else echo \"$t not installed\"; fi; done; git status --short", "description": "Run ruff and mypy if available, show status"}
[tool_result] ruff not installed
mypy not installed
 M tenacity/__init__.py
 M tests/test_asyncio.py
[assistant] `AttemptManager` now supports `async with`, so `async with attempt:` inside `async for` works and behaves like `with attempt:`.

**Changes**

- **`tenacity/__init__.py`**: added `__aenter__` and `__aexit__` to `AttemptManager`. They delegate to the existing `__enter__` and `__exit__`, so the sync and async paths share one implementation: exceptions are recorded on the retry state and swallowed for retry, and success sets the result to `None`.
- **`tests/test_asyncio.py`**: added two tests next to the existing `test_do_max_attempts`:
  - `test_do_max_attempts_async_with` runs the max-attempts loop using `async with`.
  - `test_async_with_success_sets_result` checks that a successful `async with` block records a non-failed outcome with result `None`.

**Verification**

- The full suite passes: 140 passed, 1 skipped, 12 subtests passed.
- `ruff` and `mypy` are not installed in the project's test environment, so I did not run them. I did not install them.

I haven't committed anything. I also haven't checked the new tests against the original code to confirm they fail there. Without the new methods, `async with` raises `TypeError`, so they would fail.
