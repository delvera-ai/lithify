# trajectory base-1

final message:
`TryAgain` raised from an `except` block with `reraise=True` now re-raises the original error, for both `Retrying` and `AsyncRetrying`. The full suite passes.

**Cause:** `RetryError.reraise()` re-raised the last attempt's exception. For an explicit `TryAgain` that exception is the sentinel itself, so the sentinel escaped. The real error is on its `__context__`.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): when the last attempt failed with `TryAgain` and it has a `__context__`, re-raise that instead. Other cases are unchanged, including a `TryAgain` raised outside any `except` block. Both sync and async loops reach this through the shared `exc_check`, so no async copy was needed.

**Tests:**
- `tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_original_error`
- `tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraise_original_error`

Both failed against the unfixed code with `TryAgain` escaping, and pass now.

**Results:**
- Full suite via `run_tests.py`: 159 passed, 1 skipped, exit 0.
- `check_changed.py`: 0 problems.
- ruff and mypy were not run; they are unavailable in this environment.

**Also added:** a reno note, `releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml`, under `fixes:`. I did not validate its YAML because PyYAML is unavailable here.

**Not covered:** `raise TryAgain from err` outside an `except` block. The fix relies on `__context__`, which is set automatically when `TryAgain` is raised inside an `except` block.

## events
[assistant] I'll start by reading the retry loop and the existing `TryAgain` handling.
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"TryAgain\\|reraise\" tenacity/ | head -60 && cat .lithify/harness/skills/tenacity-change-contract/SKILL.md 2>/dev/null | head -80 && cat ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/.lithify/harness/scripts/run_tests.py | head -5 >/dev/null; ls .lithify/harness/scripts"}
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
tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:239:        reraise: bool = False,
tenacity/__init__.py:252:        self.reraise = reraise
tenacity/__init__.py:268:        reraise: bool | object = _unset,
tenacity/__init__.py:285:            reraise=_first_set(reraise, self.reraise),
tenacity/__init__.py:421:       
…[6398 chars elided]…
` class. Async composition tests are in `tests/test_asyncio.py::TestContextManager`.
- `stop.py` (`stop_any`/`stop_all` via `|`/`&`) and `wait.py` (`wait_combine` via `+`) have
  their own combinators. A task about retry composition does not cover them; leave them alone
  unless the task names them.
- Type aliases: sync `RetryBaseT` (`tenacity/retry.py`) and async `RetryBaseT`
  (`tenacity/asyncio/retry.py`). Inside `tenacity/asyncio/` the sync one is imported under
check_changed.py
run_tests.py
[assistant] The skill file is long; I'll read the retry-loop code directly, plus the async copy.
[tool_use Bash] {"command": "sed -n 120,135p tenacity/__init__.py && echo ---RETRYSTATE && sed -n 180,200p tenacity/__init__.py && echo ---ITER && sed -n 405,470p tenacity/__init__.py && echo ---ASYNC && grep -n \"TryAgain\\|reraise\\|_post_retry_check\\|def _run_retry\\|def iter\" tenacity/asyncio/__init__.py", "description": "Read TryAgain handling in sync and async loops"}
[tool_result]     def reset(self) -> None:
        self.actions = []
        self.retry_run_result = False
        self.stop_run_result = False
        self.is_explicit_retry = False


class TryAgain(Exception):
    """Always retry the executed function when raised."""


NO_RESULT = object()


class DoAttempt:
    pass
---RETRYSTATE
    """Encapsulates the last attempt instance right before giving up."""

    def __init__(self, last_attempt: "Future") -> None:
        self.last_attempt = last_attempt
        
…[2609 chars elided]…
_sleep is not None:
            self._add_action_func(self.before_sleep)

        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        self.begin()
---ASYNC
89:        reraise: bool = False,
104:            reraise=reraise,
139:    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
158:    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
[assistant] The cause is visible: `RetryError.reraise()` re-raises the last attempt's exception, and for an explicit `TryAgain` that is the sentinel itself. The real error is on `__context__`. Before editing, I'll read the rest of the contract skill and locate the project Python.
[tool_use Bash] {"command": "sed -n 80,200p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; sed -n 1,60p .lithify/harness/scripts/run_tests.py; echo ---; ls releasenotes/notes | tail -5; ls <work>/env-tenacity/bin/python 2>&1", "description": "Read rest of contract skill and runner usage"}
[tool_result]   (`tenacity/asyncio/retry.py`). Inside `tenacity/asyncio/` the sync one is imported under
  `TYPE_CHECKING` as `SyncRetryBaseT` (see `tenacity/asyncio/__init__.py`). They are defined
  after `retry_base`, so annotations that use them in the class body are quoted strings.

## 1b2. Object state, pickling and copying (`Retrying`, strategies)
Verified in `tenacity/__init__.py`, `retry.py`, `before*.py`, `after.py`, `stop.py`, `nap.py`.
- `BaseRetrying.__init__` stores `self._local = threading.local
…[11041 chars elided]…
*args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
---
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
<work>/env-tenacity/bin/python
[assistant] The project Python exists. Next I'll find the existing `TryAgain` tests and the reno note format so the new test sits beside them.
[tool_use Bash] {"command": "grep -n \"TryAgain\" tests/*.py | head -30; echo ---; grep -n \"^class \\|def test_retry_error_is_pickleable\" tests/test_asyncio.py | head -40; echo ---; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml; echo ---; grep -n \"^class \\|reraise\" tests/test_tenacity.py | head -60", "description": "Locate TryAgain and reraise tests and a sample reno note"}
[tool_result] tests/test_tenacity.py:843:            raise tenacity.TryAgain
tests/test_tenacity.py:854:            raise tenacity.TryAgain
tests/test_tenacity.py:862:            raise tenacity.TryAgain
tests/test_tenacity.py:869:        self.assertRaises(tenacity.TryAgain, r, _r)
---
79:class TestAsyncio(unittest.TestCase):
163:class TestAsyncEnabled(unittest.TestCase):
181:class TestTrio(unittest.TestCase):
195:class TestContextManager(unittest.TestCase):
444:class TestDecoratorWrapper(unittest.TestCase):
5
…[2143 chars elided]…
stCase):
1912:    def test_context_manager_reraise(self) -> None:
1918:        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
1928:class TestInvokeAsCallable:
1982:    def test_reraise(self) -> None:
1992:        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
1998:class TestRetryException(unittest.TestCase):
2008:class TestRetryTyping(unittest.TestCase):
2031:class TestMockingSleep:
2072:class TestPickle(unittest.TestCase):
2110:            reraise=True,
[tool_use Bash] {"command": "sed -n 836,872p tests/test_tenacity.py; echo ---; sed -n 1719,1787p tests/test_tenacity.py; echo ---; sed -n 1,20p tests/test_asyncio.py | grep -n import; grep -n \"asynctest\\|def test_retry_with_async_result_or\" tests/test_asyncio.py | head -5; sed -n 1982,1997p tests/test_tenacity.py", "description": "Read existing try-again and reraise tests"}
[tool_result]         combined = a & b & c
        self.assertIsInstance(combined, retry_all)
        self.assertEqual(len(combined.retries), 3)

    def _raise_try_again(self) -> None:
        self._attempts += 1
        if self._attempts < 3:
            raise tenacity.TryAgain

    def test_retry_try_again(self) -> None:
        self._attempts = 0
        Retrying(stop=tenacity.stop_after_attempt(5), retry=tenacity.retry_never)(
            self._raise_try_again
        )
        self.assertEqual(3, self._
…[3124 chars elided]…
 test_reraise(self) -> None:
        class CustomError(Exception):
            pass

        def f() -> typing.Any:
            f.calls.append(len(f.calls) + 1)  # type: ignore[attr-defined]
            raise CustomError("Retry it!")

        f.calls = []  # type: ignore[attr-defined]

        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
        with pytest.raises(CustomError):
            self.invoke(retry, f)
        assert f.calls == [1, 2]  # type: ignore[attr-defined]
[assistant] I'll add a sync regression test next to the existing `TryAgain` reraise test, and an async one in `test_asyncio.py`. First I'll check the async test style.
[tool_use Bash] {"command": "sed -n 79,112p tests/test_asyncio.py; grep -n \"reraise\" tests/test_asyncio.py | head", "description": "Read async test style and existing reraise tests"}
[tool_result] class TestAsyncio(unittest.TestCase):
    @asynctest
    async def test_retry(self) -> None:
        thing = NoIOErrorAfterCount(5)
        await _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @asynctest
    async def test_iscoroutinefunction(self) -> None:
        assert asyncio.iscoroutinefunction(_retryable_coroutine)
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
      
…[246 chars elided]…
IOErrorAfterCount(2)
        try:
            await _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tasyncio.AsyncRetrying())

    def test_retry_attributes(self) -> None:
        assert hasattr(_retryable_coroutine, "retry")
        assert hasattr(_retryable_coroutine, "retry_with")

226:    async def test_reraise(self) -> None:
232:                stop=stop_after_attempt(1), reraise=True
[assistant] I have the patterns I need. Adding the sync test first, then checking the async test file's imports before adding that one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "old_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5, r.statistics[\"attempt_number\"])\n\n", "new_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(
…[172 chars elided]…
se ValueError(\"the real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n\n        r = Retrying(\n            stop=tenacity.stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        self.assertRaisesRegex(ValueError, \"the real error\", r, _r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 20,52p tests/test_asyncio.py | grep -n \"import\\|^)\" ", "description": "Show test_asyncio import block"}
[tool_result] 1:from typing import Any, TypeVar
2:from unittest import mock
5:    import trio
11:import pytest
13:import tenacity
14:from tenacity import (
22:)
23:from tenacity import asyncio as tasyncio
24:from tenacity.wait import wait_fixed
26:from .test_tenacity import (
30:)
[tool_use Bash] {"command": "sed -n 33,42p tests/test_asyncio.py", "description": "Show full import list in test_asyncio"}
[tool_result] from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
[assistant] The async file already imports `tenacity`, so I'll reference `tenacity.TryAgain` and `tenacity.retry_never` through that module. Adding the async test to `TestAsyncio`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "    def test_repr(self) -> None:\n        repr(tasyncio.AsyncRetrying())", "new_string": "    @asynctest\n    async def test_retry_try_again_reraise_original_error(self) -> None:\n        async def _r() -> None:\n  
…[136 chars elided]…
Again\n\n        retrying = AsyncRetrying(\n            stop=stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with pytest.raises(ValueError, match=\"the real error\"):\n            await retrying(_r)\n        assert retrying.statistics[\"attempt_number\"] == 2\n\n    def test_repr(self) -> None:\n        repr(tasyncio.AsyncRetrying())"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Both regression tests are written. Per the harness, I'll run them against the unfixed code first and confirm they fail for the reported reason.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_original_error\" \"tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraise_original_error\" > /tmp/red_out.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red_out.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
tests/test_asyncio.py:120: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/asyncio/__init__.py:119: in __call__
    do = await self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/asyncio/__init__.py:162: in iter
    result = await action(retry_state)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/_utils.py:107: in inner
    return call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
tenacity/__init__.p
…[829 chars elided]…
r:
>           raise tenacity.TryAgain
E           tenacity.TryAgain

tests/test_asyncio.py:112: TryAgain
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_original_error
FAILED tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraise_original_error
============================== 2 failed in 0.12s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail for the reported reason: `TryAgain` escapes instead of `ValueError`. The fix goes in `RetryError.reraise()`, which both the sync and async loops reach through `exc_check`. For an explicit `TryAgain` it will re-raise the exception being handled when it was raised, which is `__context__`. Otherwise it keeps the current behaviour.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "old_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            raise self.last_attempt.result()\n        raise self", "new_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            exc = self.last_attempt.exception()\n            # TryAgain is only a retry signal: re-raise the error it was raised for.\n            if isinstance(exc, TryAgain) and exc.__context__ is not None:\n                raise exc.__context__\n            raise self.last_attempt.result()\n        raise self"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the two regression tests should go green, then the full suite and the style check.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_original_error\" \"tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraise_original_error\" > /tmp/green_out.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/green_out.txt", "description": "Run regression tests after the fix"}
[tool_result] exit=0
tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraise_original_error PASSED [ 50%]
tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraise_original_error PASSED [100%]

============================== 2 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full_out.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|exit=|HUNG|TIMEOUT\" /tmp/full_out.txt | tail -5; $PY .lithify/harness/scripts/check_changed.py > /tmp/check_out.txt 2>&1; echo \"check_exit=$?\"; tail -15 /tmp/check_out.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] exit=0
============== 159 passed, 1 skipped, 12 subtests passed in 2.00s ==============
exit=0 (pytest); full log: /tmp/run_tests.log
check_exit=0
changed: tenacity/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (159 passed, 1 skipped, exit 0) and `check_changed.py` reports 0 problems. This is a user-visible fix under `tenacity/`, so the contract calls for a reno note in `fixes:` form. I'll add it.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8); echo $H; ls releasenotes/notes | grep -i tryagain; echo \"$H\"", "description": "Generate a random suffix for the reno note name"}
[tool_result] 9eba46a4cd214e26
9eba46a4cd214e26
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml", "content": "---\nfixes:\n  - |\n    When ``TryAgain`` was raised from inside an ``except`` block to drive a\n    manual retry, and ``reraise=True`` was set, the error raised after the\n    attempts were exhausted was ``TryAgain`` itself. It now re-raises the\n    underlying exception that ``TryAgain`` was raised for. This applies to\n    both ``Retrying`` and ``AsyncRetrying``, and to ``RetryError.reraise()``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-205644-bug-when-tryagain-is-raised-from/base-1/releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml (file state is current in your context — no need to Read it back)
[assistant] The reno note is a new file, so I'll re-run the style check and confirm the YAML parses.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check_out2.txt 2>&1; echo \"check_exit=$?\"; tail -4 /tmp/check_out2.txt; $PY -c \"import sys; print('ok')\"; git status --short", "description": "Re-run style check and show changed files"}
[tool_result] check_exit=0
changed: releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml, tenacity/__init__.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
ok
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml
[assistant] `TryAgain` raised from an `except` block with `reraise=True` now re-raises the original error, for both `Retrying` and `AsyncRetrying`. The full suite passes.

**Cause:** `RetryError.reraise()` re-raised the last attempt's exception. For an explicit `TryAgain` that exception is the sentinel itself, so the sentinel escaped. The real error is on its `__context__`.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): when the last attempt failed with `TryAgain` and it has a `__context__`, re-raise that instead. Other cases are unchanged, including a `TryAgain` raised outside any `except` bloc
…[321 chars elided]…
d code with `TryAgain` escaping, and pass now.

**Results:**
- Full suite via `run_tests.py`: 159 passed, 1 skipped, exit 0.
- `check_changed.py`: 0 problems.
- ruff and mypy were not run; they are unavailable in this environment.

**Also added:** a reno note, `releasenotes/notes/reraise-try-again-original-error-9eba46a4cd214e26.yaml`, under `fixes:`. I did not validate its YAML because PyYAML is unavailable here.

**Not covered:** `raise TryAgain from err` outside an `except` block. The fix relies on `__context__`, which is set automatically when `TryAgain` is raised inside an `except` block.
