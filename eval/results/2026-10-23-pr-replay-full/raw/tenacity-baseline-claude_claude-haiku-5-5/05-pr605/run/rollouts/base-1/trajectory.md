# trajectory base-1

final message:
`AttemptManager` now supports `async with`, so `async with attempt:` works inside `async for attempt in AsyncRetrying(...)` and behaves like `with attempt:`. The full test suite passes: 141 passed, 1 skipped.

The change is in `tenacity/__init__.py`. `__aenter__` and `__aexit__` delegate to the existing `__enter__` and `__exit__`, so the success, exception-swallowing and retry-state logic is shared rather than duplicated.

I added three tests to `tests/test_asyncio.py`:
- the max-attempts case with `async with`, which raises `RetryError` after three attempts;
- a case where the first attempt fails and the second succeeds, which stops retrying;
- a `reraise=True` case that re-raises the original exception.

I also added a feature release note at `releasenotes/notes/attempt-manager-async-context-manager-3f9c1e2a7b8d4c60.yaml`.

Ruff and mypy are not installed in this environment, so I did not run lint or type checks. Nothing is committed yet; the changes are in the working tree.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"AttemptManager\" --include=*.py . | head -50", "description": "Locate AttemptManager definitions and usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; git grep -n \"AttemptManager\" | head -60; ls", "description": "Locate AttemptManager definitions and list repo root"}
[tool_result] tenacity/__init__.py:195:class AttemptManager:
tenacity/__init__.py:443:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/__init__.py:450:                yield AttemptManager(retry_state=retry_state)
tenacity/__init__.py:725:    "AttemptManager",
tenacity/asyncio/__init__.py:24:    AttemptManager,
tenacity/asyncio/__init__.py:163:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:171:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:177:                return AttemptManager(retry_state=self._retry_state)
AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "offset": 190, "limit": 40}
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
208	        
…[495 chars elided]…
[int | float], None] = sleep,
222	        stop: "StopBaseT" = stop_never,
223	        wait: "WaitBaseT" = wait_none(),
224	        retry: "RetryBaseT" = retry_if_exception_type(),
225	        before: t.Callable[["RetryCallState"], None] = before_nothing,
226	        after: t.Callable[["RetryCallState"], None] = after_nothing,
227	        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
228	        reraise: bool = False,
229	        retry_error_cls: type[RetryError] = RetryError,
[tool_use Bash] {"command": "cat CLAUDE.md AGENTS.md | head -80; ls releasenotes/notes | tail -5; ls doc", "description": "Read project instructions and release notes layout"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[929 chars elided]…
mory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
source
[tool_use Bash] {"command": "cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml; grep -rn \"with attempt\\|AttemptManager\\|attempt:\" tests | head -20; ls tests; sed -n 1,40p tests/test_asyncio.py | head -40; grep -n \"async for\\|async with\" tests/test_asyncio.py | head", "description": "Inspect release note format and existing attempt tests"}
[tool_result] ---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
tests/test_asyncio.py:185:                with attempt:
tests/test_asyncio.py:202:                with attempt:
tests/test_asyncio.py:216:                with attempt:
tests/test_asyncio.py:233:                with attempt:
tests/test_asyncio.py:253:                with attempt:
tests/test_asyncio.py:280:                with attempt:
tests/test_asyncio.py:311:                with a
…[1942 chars elided]…
io.AsyncRetrying(retry=retry_if_result(lt_3)):
250:            async for attempt in tasyncio.AsyncRetrying(
277:            async for attempt in tasyncio.AsyncRetrying(
310:            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
341:            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
369:            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
392:            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):
[assistant] Let me look at an existing async test to match the style, then make the change.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "offset": 175, "limit": 45}
[tool_result] 175	        assert thing.counter == thing.count
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
186	                    attempts += 1
187	                    raise Exception
188	        except RetryError:
189	          
…[420 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py", "old_string": "    def __enter__(self) -> None:\n        pass\n\n    def __exit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.Trace
…[852 chars elided]…
ry_state.set_result(None)\n        return None\n\n    async def __aenter__(self) -> None:\n        return self.__enter__()\n\n    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.TracebackType\"],\n    ) -> bool | None:\n        return self.__exit__(exc_type, exc_value, traceback)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now tests covering `async with` in `async for` (success, failure-then-retry, and exhaustion), plus a release note.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py", "old_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:", "new_string": "        assert attempts == 3\n\n    @asynctest\n    async def test_do_max_attempts_async_with(self) -> None:
…[805 chars elided]…
):\n            pass\n\n        try:\n            async for attempt in tasyncio.AsyncRetrying(\n                stop=stop_after_attempt(1), reraise=True\n            ):\n                async with attempt:\n                    raise CustomError()\n        except CustomError:\n            pass\n        else:\n            raise Exception\n\n    @asynctest\n    async def test_reraise(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190636-feature-attemptmanager-the-objec/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/attempt-manager-async-context-manager-3f9c1e2a7b8d4c60.yaml <<'EOF'\n---\nfeatures:\n  - |\n    - ``AttemptManager`` now supports the async context manager protocol, so ``async with attempt:`` works inside ``async for attempt in AsyncRetrying(...)`` loops, behaving the same as ``with attempt:``\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add release note and run the project test suite"}
[tool_result] ...........s........................................................................................................................ [ 92%]
..........                                                               [100%]
141 passed, 1 skipped, 12 subtests passed in 1.83s
[tool_use Bash] {"command": "git status --short && (ruff check tenacity tests 2>&1 | tail -3; ruff format --check tenacity tests 2>&1 | tail -3; mypy tenacity 2>&1 | tail -2) ", "description": "Show changed files and run lint and type checks"}
[tool_result]  M tenacity/__init__.py
 M tests/test_asyncio.py
?? releasenotes/notes/attempt-manager-async-context-manager-3f9c1e2a7b8d4c60.yaml
(eval):1: command not found: ruff
(eval):1: command not found: ruff
(eval):1: command not found: mypy
[assistant] `AttemptManager` now supports `async with`, so `async with attempt:` works inside `async for attempt in AsyncRetrying(...)` and behaves like `with attempt:`. The full test suite passes: 141 passed, 1 skipped.

The change is in `tenacity/__init__.py`. `__aenter__` and `__aexit__` delegate to the existing `__enter__` and `__exit__`, so the success, exception-swallowing and retry-state logic is shared rather than duplicated.

I added three tests to `tests/test_asyncio.py`:
- the max-attempts case with `async with`, which raises `RetryError` after three attempts;
- a case where the first attempt fails and the second succeeds, which stops retrying;
- a `reraise=True` case that re-raises the original exception.

I also added a feature release note at `releasenotes/notes/attempt-manager-async-context-manager-3f9c1e2a7b8d4c60.yaml`.

Ruff and mypy are not installed in this environment, so I did not run lint or type checks. Nothing is committed yet; the changes are in the working tree.
