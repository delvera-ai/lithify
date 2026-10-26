# trajectory base-1

final message:
`Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The full suite passes: 182 passed, 1 skipped, `exit=0`.

**Cause:** `wraps` (the decorator) and the iterator paths already checked `enabled`, but `Retrying.__call__` and `AsyncRetrying.__call__` did not.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` early when disabled, before `begin()`.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting coroutine functions. I moved the `is_async` computation above the check so both branches can use it.
- `tests/test_tenacity.py`: added `test_enabled_false_call_raises_original_exception` and `test_enabled_false_call_returns_result`.
- `tests/test_asyncio.py`: added `test_enabled_false_call_raises_original_exception`.
- `releasenotes/notes/retrying-enabled-false-call-11c98e3f8453b860.yaml`: a `fixes:` note, as the project's change contract requires for bug fixes.

**Verification:**
- Red first: the two raise tests failed against the unfixed code with `RetryError` wrapping the `ValueError`, which is the reported bug. The return-value test passed before the fix, because a first-attempt success already calls once; it's a guard, not a red test.
- Green after the fix: the targeted `TestEnabled` and `TestAsyncEnabled` classes pass (12 tests).
- `check_changed.py`: `PASS: 0 problem(s)`.

**Not run:** ruff and mypy are not installed in this environment, so I could not run them. The change includes two `type: ignore` comments in the async `__call__` (`no-any-return` and `return-value`). I chose those codes from the signatures, not from a mypy run, and the strict config flags unused ignores. If CI's mypy disagrees, those two lines are the place to look.

**Not changed:** I didn't update `doc/source/index.rst`. The "Disabling Retries" section only documents the decorator and `retry_with` forms, and this is a bug fix, not a new usage form.

I haven't committed anything.

## events
[assistant] I'll start by reading the change-contract headings, as the project requires before any edit under `tenacity/`, then locate the `enabled` handling.
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n 'enabled' tenacity/*.py | head -60", "description": "List contract headings and find enabled usages"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[664 chars elided]…
eep the change surface minimal
tenacity/__init__.py:263:        enabled: bool = True,
tenacity/__init__.py:277:        self.enabled = enabled
tenacity/__init__.py:294:        enabled: bool | object = _unset,
tenacity/__init__.py:311:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:382:            if not self.enabled:
tenacity/__init__.py:501:        if not self.enabled:
tenacity/__init__.py:746:    enabled: bool = ...,
tenacity/__init__.py:764:    enabled: bool = True,
[tool_use Bash] {"command": "sed -n '1,20p;350,378p;451,470p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n 255,320p tenacity/__init__.py; echo ----; sed -n 370,400p tenacity/__init__.py; echo ----; sed -n 490,520p tenacity/__init__.py", "description": "Read contract sections and relevant code"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, th
…[9670 chars elided]…
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
[assistant] The `enabled` short-circuit exists in `wraps` and `__iter__`, but not in `__call__`. Next I'll check the sync and async `__call__` paths and the async `__iter__`/`__anext__`.
[tool_use Bash] {"command": "grep -n 'def __call__\\|def __aiter__\\|def __anext__\\|def __iter__\\|def iter\\|def begin\\|class .*Retrying\\|def _begin_iter' tenacity/__init__.py tenacity/asyncio/__init__.py; echo ----; sed -n 1,40p tenacity/asyncio/__init__.py | head -5; grep -n 'enabled' tenacity/asyncio/__init__.py; echo ----; sed -n 520,560p tenacity/__init__.py", "description": "Locate call and iterator methods"}
[tool_result] tenacity/asyncio/__init__.py:75:class AsyncRetrying(BaseRetrying):
tenacity/asyncio/__init__.py:113:    async def __call__(  # type: ignore[override]
tenacity/asyncio/__init__.py:167:    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
tenacity/asyncio/__init__.py:175:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:178:    def __aiter__(self) -> "AsyncRetrying":
tenacity/asyncio/__init__.py:188:    async def __ane
…[1855 chars elided]…
      try:
                    result = fn(*args, **kwargs)
                except BaseException:
                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
                else:
                    retry_state.set_result(result)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                return do  # type: ignore[no-any-return]


class Future(futures.Future[t.Any]):
[tool_use Bash] {"command": "sed -n 110,240p tenacity/asyncio/__init__.py; echo ----; grep -n 'Disabling Retries' -A25 doc/source/index.rst; ls tests | head -50; grep -rn 'enabled' tests/*.py | head -30", "description": "Read async call path, docs, and existing tests"}
[tool_result]         )

    @override
    async def __call__(  # type: ignore[override]
        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        is_async = _utils.is_coroutine_callable(fn)
        while True:
            do = await self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                try:
                    if is_async:
  
…[7870 chars elided]…
nc def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests/test_asyncio.py:223:            enabled=False,
tests/test_asyncio.py:234:    async def test_enabled_false_aiter_succeeds_on_first_attempt(self) -> None:
tests/test_asyncio.py:235:        """When enabled=False, the async iterator runs the body once and stops."""
tests/test_asyncio.py:238:            enabled=False,
[assistant] The bug is clear: `Retrying.__call__` and `AsyncRetrying.__call__` have no `enabled` short-circuit, while `wraps` and the iterator paths do. Before writing tests, I'll read the release-note and docs sections of the contract and the existing test style.
[tool_use Bash] {"command": "sed -n 401,450p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n 1640,1750p tests/test_tenacity.py; echo ----; sed -n 195,250p tests/test_asyncio.py; ls releasenotes/notes | tail -5", "description": "Read contract \u00a72-3 and existing enabled tests"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[8324 chars elided]…
retrying:
            with attempt:
                call_count += 1
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
class TestTrio(unittest.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The contract asks for a red regression test before the fix. I'll add one new test to each test class (sync and async) that calls the retrying object directly with `enabled=False`, asserting one call and the original exception.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py", "old_string": "    def test_enabled_false_iter_succeeds_on_first_attempt(self) -> None:\n        \"\"\"When enabled=False, the iterator protocol runs the body once and stops.\"\"\"\n        call_count = 0\n        retrying = Retr
…[1469 chars elided]…
ling the Retrying object returns the function's\n        result from a single call.\"\"\"\n        call_count = 0\n\n        def succeeds() -> str:\n            nonlocal call_count\n            call_count += 1\n            return \"ok\"\n\n        retrying = Retrying(enabled=False, stop=tenacity.stop_after_attempt(3))\n        assert retrying(succeeds) == \"ok\"\n        assert call_count == 1\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py", "old_string": "    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:", "new_string": "    @asynctest\n    async def test_enabled_false_call_raises_original_exception(self) -> None:\n      
…[234 chars elided]…
 nonlocal call_count\n            call_count += 1\n            raise ValueError(\"fail\")\n\n        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))\n        with pytest.raises(ValueError, match=\"fail\"):\n            await retrying(always_fails)\n        assert call_count == 1\n\n    @asynctest\n    async def test_enabled_false_aiter_raises_original_exception(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now I'll run the new tests alone against the unfixed code, through the harness runner.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled::test_enabled_false_call_raises_original_exception tests/test_tenacity.py::TestEnabled::test_enabled_false_call_returns_result tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_call_raises_original_exception > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
        function awaits it once and raises its exception unchanged."""
        call_count = 0
    
        async def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")
    
        retrying = AsyncRetrying(enabled=False, stop=stop_after_attempt(3))
        with pytest.raises(ValueError, match="fail"):
>           await retrying(always_fails)

tests/test_asyncio.py:230: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
…[857 chars elided]…
[<Future at 0x108c7a2a0 state=finished raised ValueError>]

tenacity/__init__.py:481: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_call_raises_original_exception
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_call_raises_original_exception
========================= 2 failed, 1 passed in 0.09s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both new failing tests are red for the reported reason: `RetryError` wrapping the `ValueError`, after 3 attempts. The return-value test passes on the unfixed code because a first-attempt success already calls once; it's a guard, not a red test, and I'll say so in the summary.

Now the fix, applied in both `__call__` methods before `begin()`, mirroring the existing `wraps` and iterator short-circuits.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py", "old_string": "        **kwargs: t.Any,\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(
…[186 chars elided]…
 ) -> WrappedFnReturnT:\n        if not self.enabled:\n            return fn(*args, **kwargs)\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do, DoAttempt):\n                try:\n                    result = fn(*args, **kwargs)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py", "old_string": "        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n      
…[161 chars elided]…
nReturnT:\n        is_async = _utils.is_coroutine_callable(fn)\n        if not self.enabled:\n            if is_async:\n                return await fn(*args, **kwargs)  # type: ignore[misc]\n            return fn(*args, **kwargs)  # type: ignore[no-any-return]\n\n        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] I added two `type: ignore` comments without verifying they're needed, and I can't run mypy here. I'll check the `WrappedFn` type and the mypy config before deciding whether they stay, and run the tests first.
[tool_use Bash] {"command": "grep -n 'WrappedFn\\b\\|WrappedFn =' tenacity/asyncio/__init__.py tenacity/__init__.py | head; grep -n -A12 '\\[tool.mypy\\]' pyproject.toml; PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestAsyncEnabled > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/green.txt", "description": "Check types config and run enabled tests"}
[tool_result] tenacity/__init__.py:115:WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Any])
tenacity/__init__.py:594:        fn: WrappedFn | None,
tenacity/__init__.py:828:    "WrappedFn",
tenacity/asyncio/__init__.py:52:WrappedFn = t.TypeVar("WrappedFn", bound=t.Callable[..., t.Awaitable[t.Any]])
tenacity/asyncio/__init__.py:114:        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any
tenacity/asyncio/__init__.py:249:    "WrappedFn",
115:[tool.mypy]
116-strict = true
117-# Match `requires-pytho
…[224 chars elided]…
ersion = "3.10"
121-files = ["tenacity", "tests"]
122-show_error_codes = true
123-exclude = ["tenacity/_version\\.py"]
124-# `strict` is not "everything" -- these are checks it leaves off.
125-warn_unreachable = true
126-disallow_any_unimported = true
127-extra_checks = true
exit=0
tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_skips_retry PASSED [100%]

============================== 12 passed in 0.02s ==============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All 12 enabled tests pass. Next, the type-ignore question. I'll check whether mypy is available anywhere so I can verify rather than guess.
[tool_use Bash] {"command": "(which mypy ruff; python3 -c 'import mypy' ; /usr/bin/env python3 -m mypy --version) 2>&1 | head; grep -n 'warn_unused_ignores\\|disallow_any' pyproject.toml", "description": "Check whether mypy is installed"}
[tool_result] mypy not found
ruff not found
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'mypy'
<work>/env-tenacity/bin/python3: No module named mypy
126:disallow_any_unimported = true
[assistant] mypy isn't installed, and the harness says not to build a venv for it. The strict config includes `warn_unused_ignores`, so each ignore has to match a real error. I'll confirm `WrappedFnReturnT` is a bare TypeVar, then pick the ignore codes from that.
[tool_use Bash] {"command": "grep -n 'WrappedFnReturnT = ' tenacity/__init__.py tenacity/asyncio/__init__.py; grep -n 'no-any-return\\|return-value' tenacity/asyncio/__init__.py | head", "description": "Confirm return TypeVar definition"}
[tool_result] tenacity/asyncio/__init__.py:51:WrappedFnReturnT = t.TypeVar("WrappedFnReturnT")
tenacity/__init__.py:114:WrappedFnReturnT = t.TypeVar("WrappedFnReturnT")
120:            return fn(*args, **kwargs)  # type: ignore[no-any-return]
141:                return do  # type: ignore[no-any-return]
[assistant] My reasoning from the signatures: `fn` is bound to an awaitable-returning callable, so the sync branch returns `Awaitable[Any]`, which is a `return-value` error, not `no-any-return`. The awaited branch returns `Any`, which is `no-any-return`. I'll correct the ignore codes to match.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py", "old_string": "            if is_async:\n                return await fn(*args, **kwargs)  # type: ignore[misc]\n            return fn(*args, **kwargs)  # type: ignore[no-any-return]", "new_string": "            if is_async:\n                return await fn(*args, **kwargs)  # type: ignore[no-any-return]\n            return fn(*args, **kwargs)  # type: ignore[return-value]"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Next, the release note the contract requires for a bug fix (§2). I'll also check whether the docs describe the direct-call form, which decides whether §2a applies.
[tool_use Bash] {"command": "grep -n 'enabled' doc/source/index.rst; N=$(python3 -c 'import secrets;print(secrets.token_hex(8))'); echo $N; cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml", "description": "Check docs mentions and sample reno note"}
[tool_result] 624:You can disable retrying entirely by passing ``enabled=False``. When disabled,
633:        enabled=os.getenv("ENABLE_RETRIES", "1") != "0",
651:    call_api.retry_with(enabled=False)()
11c98e3f8453b860
---
fixes:
  - |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
[assistant] The docs only describe the decorator and `retry_with` forms, and this is a bug fix, so §2a doesn't require a docs change. I'll write the release note.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/releasenotes/notes/retrying-enabled-false-call-11c98e3f8453b860.yaml", "content": "---\nfixes:\n  - |\n    Calling a `Retrying` or `AsyncRetrying` object with a function, as in\n    `Retrying(enabled=False)(fn)`, now honours `enabled=False`. The function\n    is called once and its exception propagates unchanged instead of being\n    retried and wrapped in `RetryError`, matching the decorator and iterator\n    forms.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220928-bug-retrying-enabled-false-fn-an/base-1/releasenotes/notes/retrying-enabled-false-call-11c98e3f8453b860.yaml (file state is current in your context — no need to Read it back)
[assistant] Now the required sequence: the targeted tests green, then the full suite, then `check_changed.py`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestEnabled tests/test_asyncio.py::TestAsyncEnabled > /tmp/t1.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/t1.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/full.txt", "description": "Run targeted then full test suite"}
[tool_result] exit=0
============================== 12 passed in 0.02s ==============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0

============== 182 passed, 1 skipped, 15 subtests passed in 1.87s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc.txt 2>&1; echo \"exit=$?\"; cat /tmp/cc.txt | tail -30", "description": "Run stdlib lint stand-in on changed files"}
[tool_result] exit=0
changed: releasenotes/notes/retrying-enabled-false-call-11c98e3f8453b860.yaml, tenacity/__init__.py, tenacity/asyncio/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] All checks pass. I'll read the final source diff once before reporting.
[tool_use Bash] {"command": "git diff -- tenacity/", "description": "Show source diff"}
[tool_result] diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 530b63a..e466003 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -538,6 +538,9 @@ class Retrying(BaseRetrying):
         *args: t.Any,
         **kwargs: t.Any,
     ) -> WrappedFnReturnT:
+        if not self.enabled:
+            return fn(*args, **kwargs)
+
         self.begin()
 
         retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
diff --git a/tenacity/asyncio/__init__.py b/te
…[374 chars elided]…
)
+        if not self.enabled:
+            if is_async:
+                return await fn(*args, **kwargs)  # type: ignore[no-any-return]
+            return fn(*args, **kwargs)  # type: ignore[return-value]
+
         self.begin()
 
         retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
-        is_async = _utils.is_coroutine_callable(fn)
         while True:
             do = await self.iter(retry_state=retry_state)
             if isinstance(do, DoAttempt):
[assistant] `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` now call `fn` once and propagate its exception unchanged. The full suite passes: 182 passed, 1 skipped, `exit=0`.

**Cause:** `wraps` (the decorator) and the iterator paths already checked `enabled`, but `Retrying.__call__` and `AsyncRetrying.__call__` did not.

**Changes:**
- `tenacity/__init__.py`: `Retrying.__call__` returns `fn(*args, **kwargs)` early when disabled, before `begin()`.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying.__call__` does the same, awaiting coroutine functions. I moved the `is_async` computation a
…[824 chars elided]…
oblem(s)`.

**Not run:** ruff and mypy are not installed in this environment, so I could not run them. The change includes two `type: ignore` comments in the async `__call__` (`no-any-return` and `return-value`). I chose those codes from the signatures, not from a mypy run, and the strict config flags unused ignores. If CI's mypy disagrees, those two lines are the place to look.

**Not changed:** I didn't update `doc/source/index.rst`. The "Disabling Retries" section only documents the decorator and `retry_with` forms, and this is a bug fix, not a new usage form.

I haven't committed anything.
