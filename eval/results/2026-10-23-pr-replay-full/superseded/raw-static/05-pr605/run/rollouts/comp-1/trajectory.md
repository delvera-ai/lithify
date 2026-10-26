# trajectory comp-1

final message:
`async with attempt:` now works inside `async for attempt in AsyncRetrying(...)` loops and behaves like `with attempt:`. The full suite passes (141 passed, 1 skipped).

**Before the change:** on HEAD, `async with attempt:` raised `TypeError: 'AttemptManager' object does not support the asynchronous context manager protocol`. `with attempt:` worked in both the sync and async loops.

**Changes:**
- `tenacity/__init__.py`: `AttemptManager` gains `__aenter__` and `__aexit__`. They delegate to the existing `__enter__` and `__exit__`, so the logic is not duplicated.
- `tests/test_asyncio.py`: three tests in `TestContextManager` mirror the existing `with` tests, using `async with`: `test_async_with_do_max_attempts`, `test_async_with_reraise`, and `test_async_with_retry_with_result`.
- `releasenotes/notes/attempt-manager-async-context-manager-248b14e6b437457d.yaml`: a `features:` note.
- `doc/source/index.rst`: a short `async with attempt:` example after the first `AsyncRetrying` example.

**Checks:**
- Fail-on-base: all three new tests fail on HEAD with the `TypeError` above, so they catch the bug.
- Mypy and ruff were not run; they are not installed in the project interpreter. I annotated the new methods by inspection.

I took the "exactly like `with`" reading to mean the three scenarios in the contract. I did not add a sync-only test for `Retrying`, because `AttemptManager` is shared and the sync path is unchanged.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[8611 chars elided]…
city-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (the `-m pytest` command in the always-on memory notes).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.

[tool_use Bash] {"command": "grep -n \"class AttemptManager\" -A 40 tenacity/__init__.py; grep -n \"__enter__\\|__exit__\\|__aenter__\\|__aexit__\" tenacity/*.py", "description": "Locate AttemptManager and context manager methods"}
[tool_result] 195:class AttemptManager:
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
210-        if exc_type is not None and exc_va
…[702 chars elided]…
g,
227-        before_sleep: t.Callable[["RetryCallState"], None] | None = None,
228-        reraise: bool = False,
229-        retry_error_cls: type[RetryError] = RetryError,
230-        retry_error_callback: t.Callable[["RetryCallState"], t.Any] | None = None,
231-        name: str | None = None,
232-    ):
233-        self.sleep = sleep
234-        self.stop = stop
235-        self.wait = wait
tenacity/__init__.py:201:    def __enter__(self) -> None:
tenacity/__init__.py:204:    def __exit__(
[assistant] Loaded the contract. Next I'll check the current `AttemptManager` usage, the existing async context-manager tests, and the release-note and doc conventions.
[tool_use Bash] {"command": "grep -n \"class TestContextManager\" -A 60 tests/test_asyncio.py | head -90; echo ---; ls releasenotes/notes | tail -5; echo ---; grep -n \"async with\\|AsyncRetrying\" doc/source/index.rst | head -20; echo ---; ls .lithify/harness/skills/tenacity-change-contract/scripts/ 2>&1; echo ---; grep -n \"AttemptManager\" -r tenacity tests doc/source | head", "description": "Inspect tests, release notes, docs, and helper script"}
[tool_result] 178:class TestContextManager(unittest.TestCase):
179-    @asynctest
180-    async def test_do_max_attempts(self) -> None:
181-        attempts = 0
182-        retrying = tasyncio.AsyncRetrying(stop=stop_after_attempt(3))
183-        try:
184-            async for attempt in retrying:
185-                with attempt:
186-                    attempts += 1
187-                    raise Exception
188-        except RetryError:
189-            pass
190-
191-        assert attempts == 3
192-
193-    
…[2245 chars elided]…
r[AttemptManager, None, None]:
tenacity/__init__.py:450:                yield AttemptManager(retry_state=retry_state)
tenacity/__init__.py:725:    "AttemptManager",
tenacity/asyncio/__init__.py:24:    AttemptManager,
tenacity/asyncio/__init__.py:163:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:171:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:177:                return AttemptManager(retry_state=self._retry_state)
[tool_use Bash] {"command": "sed -n 238,250p tests/test_asyncio.py; echo ---; sed -n 636,680p doc/source/index.rst; echo ---; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml; echo ---; cat .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py | head -60; echo ---; git status --short", "description": "Read remaining test, doc section, note format, and helper script"}
[tool_result]         result = await test()

        self.assertEqual(3, result)

    @asynctest
    async def test_retry_with_async_result(self) -> None:
        async def test() -> int:
            attempts = 0

            async def lt_3(x: float) -> bool:
                return x < 3

            async for attempt in tasyncio.AsyncRetrying(
---
   except RetryError:
       pass

You can configure every details of retry policy by configuring the Retrying
object.

With async code you can use AsyncRetrying.

…[3201 chars elided]…
 0:
            print("ERROR: git archive HEAD failed:", archive.stderr.decode(), file=sys.stderr)
            return 2
        untar = subprocess.run(
            ["tar", "-x", "-C", tmp], input=archive.stdout, capture_output=True, check=False
        )
        if untar.returncode != 0:
            print("ERROR: extracting HEAD failed:", untar.stderr.decode(), file=sys.stderr)
            return 2
        shutil.rmtree(os.path.join(tmp, "tests"), ignore_errors=True)
        shutil.copytree(
---
[assistant] Before editing, I'll probe the unmodified code with each variant the task names: `with attempt:` and `async with attempt:`, in both the sync and async loops.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/probe_attempt.py <<'EOF'\nimport asyncio\nfrom tenacity import Retrying, AsyncRetrying, stop_after_attempt\n\nasync def async_with_in_async_for():\n    async for attempt in AsyncRetrying(stop=stop_after_attempt(2)):\n
…[714 chars elided]…
int(name, \"-> raises\", type(e).__name__, e)\n    try:\n        async_with_in_sync_for()\n        print(\"async with in for -> n/a\")\n    except Exception as e:\n        print(\"with in sync for -> raises\", type(e).__name__, e)\n\nasyncio.run(main())\nEOF\n$PY -c \"import sys; print(sys.version)\" && $PY /tmp/probe_attempt.py", "description": "Probe async with/with variants on unmodified code"}
[tool_result ERROR] Exit code 1
3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
Traceback (most recent call last):
  File "/tmp/probe_attempt.py", line 2, in <module>
    from tenacity import Retrying, AsyncRetrying, stop_after_attempt
ModuleNotFoundError: No module named 'tenacity'
[assistant] The probe script sits in `/tmp`, so Python doesn't put the repo root on the import path. I'll rerun with `PYTHONPATH` set to the repo.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY /tmp/probe_attempt.py", "description": "Rerun probe with repo on PYTHONPATH"}
[tool_result] async with in async for -> raises TypeError 'AttemptManager' object does not support the asynchronous context manager protocol
with in async for -> raises RetryError RetryError[<Future at 0x103e38d70 state=finished raised ValueError>]
with in sync for -> raises RetryError RetryError[<Future at 0x103fe82c0 state=finished raised ValueError>]
[assistant] The baseline confirms the gap: `async with attempt:` raises `TypeError` on HEAD, while `with attempt:` works in both loops. Now I'll add the async protocol methods, delegating to the existing sync ones.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/tenacity/__init__.py", "old_string": "        # We don't have the result, actually.\n        self.retry_state.set_result(None)\n        return None\n\n\nclass BaseRetrying(ABC):", "new_string": "        # We don't have the result, actually.\n        self
…[32 chars elided]…
       return None\n\n    async def __aenter__(self) -> None:\n        return self.__enter__()\n\n    async def __aexit__(\n        self,\n        exc_type: type[BaseException] | None,\n        exc_value: BaseException | None,\n        traceback: t.Optional[\"types.TracebackType\"],\n    ) -> bool | None:\n        return self.__exit__(exc_type, exc_value, traceback)\n\n\nclass BaseRetrying(ABC):"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/tenacity/__init__.py has been updated successfully.
[assistant] Next, regression tests mirroring the three `TestContextManager` scenarios named in the contract, using `async with` in place of `with`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_sleeps(self) -> None:", "new_string": "    @asynctest\n    async def test_async_with_do_max_attempts(self) -> None:\n        attempts = 0\n        retrying = tasyncio.AsyncRetrying
…[970 chars elided]…
      return x < 3\n\n            async for attempt in tasyncio.AsyncRetrying(retry=retry_if_result(lt_3)):\n                async with attempt:\n                    attempts += 1\n                attempt.retry_state.set_result(attempts)\n            return attempts\n\n        result = await test()\n\n        self.assertEqual(3, result)\n\n    @asynctest\n    async def test_sleeps(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now the release note and a user-doc example. The note name needs 16 hex characters, so I'll generate them.
[tool_use Bash] {"command": "openssl rand -hex 8", "description": "Generate random suffix for release note name"}
[tool_result] 248b14e6b437457d
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/releasenotes/notes/attempt-manager-async-context-manager-248b14e6b437457d.yaml", "content": "---\nfeatures:\n  - |\n    The attempt object yielded by ``AsyncRetrying`` now supports the async\n    context-manager protocol, so ``async with attempt:`` works inside an\n    ``async for attempt in AsyncRetrying(...)`` loop. It behaves exactly like\n    ``with attempt:``: exceptions are recorded as the attempt's outcome and\n    retried, ``reraise=True`` re-raises the last exception, and\n    ``attempt.retry_state.set_result(...)`` still works. Previously it raised\n    ``TypeError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/releasenotes/notes/attempt-manager-async-context-manager-248b14e6b437457d.yaml (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/doc/source/index.rst", "old_string": "      except RetryError:\n          pass\n\nIn both cases, you may want to set the result", "new_string": "      except RetryError:\n          pass\n\nInside an ``async for`` loop, the attempt also works as an async 
…[75 chars elided]…
tempt:``:\n\n.. testcode::\n\n   from tenacity import AsyncRetrying, RetryError, stop_after_attempt\n\n   async def function():\n      try:\n          async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):\n              async with attempt:\n                  raise Exception('My code is failing!')\n      except RetryError:\n          pass\n\nIn both cases, you may want to set the result"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-163902-feature-attemptmanager-the-objec/comp-1/doc/source/index.rst has been updated successfully.
[assistant] Now the DONE checks, starting with the fail-on-base check on the three new tests.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py \"tests/test_asyncio.py::TestContextManager::test_async_with_do_max_attempts\" \"tests/test_asyncio.py::TestContextManager::test_async_with_reraise\" \"tests/test_asyncio.py::TestContextManager::test_async_with_retry_with_result\" 2>&1 | tail -60; echo \"EXIT=${PIPESTATUS[0]}\"", "description": "Run fails-on-base check for new tests"}
[tool_result]     @asynctest
    async def test_async_with_retry_with_result(self) -> None:
        async def test() -> int:
            attempts = 0
    
            # mypy doesn't have great lambda support
            def lt_3(x: float) -> bool:
                return x < 3
    
            async for attempt in tasyncio.AsyncRetrying(retry=retry_if_result(lt_3)):
                async with attempt:
                    attempts += 1
                attempt.retry_state.set_result(attempts)
            return 
…[642 chars elided]…
r
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_do_max_attempts
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_reraise - T...
FAILED tests/test_asyncio.py::TestContextManager::test_async_with_retry_with_result
3 failed in 0.05s
------------------------------------------------------------
GOOD: tests FAIL on HEAD. Check the failure above is the bug, not an unrelated error.
EXIT=
[assistant] All three new tests fail on HEAD with the `TypeError` above, which is the bug. Next, the full suite once after the final edit.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ...........s........................................................................................................................ [ 92%]
..........                                                               [100%]
141 passed, 1 skipped, 12 subtests passed in 1.85s
[tool_use Bash] {"command": "git status --short && rm -f /tmp/probe_attempt.py", "description": "Check git status and remove probe script"}
[tool_result]  M doc/source/index.rst
 M tenacity/__init__.py
 M tests/test_asyncio.py
?? releasenotes/notes/attempt-manager-async-context-manager-248b14e6b437457d.yaml
[assistant] `async with attempt:` now works inside `async for attempt in AsyncRetrying(...)` loops and behaves like `with attempt:`. The full suite passes (141 passed, 1 skipped).

**Before the change:** on HEAD, `async with attempt:` raised `TypeError: 'AttemptManager' object does not support the asynchronous context manager protocol`. `with attempt:` worked in both the sync and async loops.

**Changes:**
- `tenacity/__init__.py`: `AttemptManager` gains `__aenter__` and `__aexit__`. They delegate to the existing `__enter__` and `__exit__`, so the logic is not duplicated.
- `tests/test_asyncio.py`: three 
…[233 chars elided]…
ntext-manager-248b14e6b437457d.yaml`: a `features:` note.
- `doc/source/index.rst`: a short `async with attempt:` example after the first `AsyncRetrying` example.

**Checks:**
- Fail-on-base: all three new tests fail on HEAD with the `TypeError` above, so they catch the bug.
- Mypy and ruff were not run; they are not installed in the project interpreter. I annotated the new methods by inspection.

I took the "exactly like `with`" reading to mean the three scenarios in the contract. I did not add a sync-only test for `Retrying`, because `AttemptManager` is shared and the sync path is unchanged.
