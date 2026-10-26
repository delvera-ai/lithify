# trajectory base-1

final message:
`TryAgain` raised from an `except` block now re-raises the original exception when `reraise=True`, for both `Retrying` and `AsyncRetrying`. The full suite passes (159 passed, 1 skipped), and the two new regression tests fail without the fix.

**Cause:** when attempts run out, `RetryError.reraise()` re-raised the last attempt's exception, which was the `TryAgain` sentinel. The real error survives only as that sentinel's `__context__`. Sync and async share this code path, so one change covers both.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): if the last exception is a `TryAgain` with a `__context__`, raise that context instead. A bare `raise tenacity.TryAgain` with no originating error still raises `TryAgain`, which keeps the existing `test_retry_try_again_forever_reraise` behaviour.

**Tests added:**
- `tests/test_tenacity.py`: sync case, `assertRaisesRegex(ValueError, ...)`.
- `tests/test_asyncio.py`: async case, placed in `TestContextManager` with `@asynctest`. My first placement lacked the decorator and passed without running, so I moved it and re-checked.

**Not changed:** the `reraise=False` path still raises `RetryError` with `TryAgain` as its cause. That matches the report, which asked only about `reraise=True`.

Nothing is committed. The changes are in the working tree: `tenacity/__init__.py`, `tests/test_tenacity.py`, `tests/test_asyncio.py`.

## events
[tool_use Bash] {"command": "grep -rn \"TryAgain\\|reraise\\|_post_retry\\|retry_error_cls\\|fut.exception\\|def iter\\|def __call__\" tenacity/*.py | head -80", "description": "Find TryAgain and reraise handling in tenacity"}
[tool_result] tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:239:        reraise: bool = False,
tenacity/__init__.py:240:        retry_error_cls: type[RetryError] = RetryError,
tenacity/__init__.py:252:        self.reraise = reraise
tenacity/__init__.py:254:        self.retry_error_cls = retry_error_cls
tenacity/__init__.py:268:        reraise: bool | object = _unset,
tenacity/__init__.py:269:        retry_error_cls: type[
…[3652 chars elided]…
te") -> bool:
tenacity/stop.py:67:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/stop.py:80:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/stop.py:90:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/stop.py:107:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/stop.py:124:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/tornadoweb.py:40:    def __call__(  # type: ignore[override]
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "offset": 120, "limit": 340}
[tool_result] 120	    def reset(self) -> None:
121	        self.actions = []
122	        self.retry_run_result = False
123	        self.stop_run_result = False
124	        self.is_explicit_retry = False
125	
126	
127	class TryAgain(Exception):
128	    """Always retry the executed function when raised."""
129	
130	
131	NO_RESULT = object()
132	
133	
134	class DoAttempt:
135	    pass
136	
137	
138	class DoSleep(float):
139	    pass
140	
141	
142	class BaseAction:
143	    """Base class for representing actions t
…[12619 chars elided]…
retry_exc = self.retry_error_cls(fut)
448	                if self.reraise:
449	                    retry_exc.reraise()
450	                raise retry_exc from fut.exception()
451	
452	            self._add_action_func(exc_check)
453	            return
454	
455	        def next_action(rs: "RetryCallState") -> None:
456	            sleep = rs.upcoming_sleep
457	            rs.next_action = RetryAction(sleep)
458	            rs.idle_for += sleep
459	            self.statistics["idle_for"] += sleep
[tool_use Bash] {"command": "grep -rn \"TryAgain\" tests/ docs/ README* 2>/dev/null | head -30; git status --short; git log --oneline -1", "description": "Find TryAgain usages in tests and docs"}
[tool_result] tests/test_tenacity.py:843:            raise tenacity.TryAgain
tests/test_tenacity.py:854:            raise tenacity.TryAgain
tests/test_tenacity.py:862:            raise tenacity.TryAgain
tests/test_tenacity.py:869:        self.assertRaises(tenacity.TryAgain, r, _r)
README.rst:278:It's also possible to retry explicitly at any time by raising the `TryAgain`
README.rst:287:          raise TryAgain
94569d2 lithify: probe base
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "offset": 830, "limit": 50}
[tool_result] 830	    def test_retry_and_coalesces(self) -> None:
831	        """Multiple & operations flatten into a single retry_all."""
832	        a = tenacity.retry_if_result(lambda x: x == 1)
833	        b = tenacity.retry_if_result(lambda x: x > 0)
834	        c = tenacity.retry_if_result(lambda x: x < 10)
835	
836	        combined = a & b & c
837	        self.assertIsInstance(combined, retry_all)
838	        self.assertEqual(len(combined.retries), 3)
839	
840	    def _raise_try_again(self) -> None:
84
…[1069 chars elided]…
city.TryAgain, r, _r)
870	        self.assertEqual(5, r.statistics["attempt_number"])
871	
872	    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
873	        with self.assertRaises(TypeError):
874	            tenacity.retry_if_exception_message()
875	
876	    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
877	        with self.assertRaises(TypeError):
878	            tenacity.retry_if_exception_message(message="negative", match="negative")
879	
[tool_use Bash] {"command": "grep -n \"class Future\" -A 40 tenacity/__init__.py | grep -n \"def \\|raise\\|return\" ; grep -n \"reraise\" tenacity/asyncio/*.py tenacity/*.py | grep -v \"__init__.py:2[3-9]\\|__init__.py:6\\|__init__.py:7\" ", "description": "Inspect Future class and other reraise uses"}
[tool_result] 4:524-    def __init__(self, attempt_number: int) -> None:
9:529-    def failed(self) -> bool:
11:531-        return self.exception() is not None
14:534-    def construct(
23:543-        return fut
29:549-    def __init__(
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:448:                if self.reraise:
tenacity/__init__.py:449:                    retry_exc.reraise()
tenacity/asyncio/__init__.py:89:        reraise: bool = False,
tenacity/asyncio/__init__.py:104:            reraise=reraise,
[assistant] Both sync and async share `BaseRetrying._post_stop_check_actions` → `RetryError.reraise()`, so one fix covers both. Let me reproduce first.
[tool_use Bash] {"command": "cat > /tmp/repro_tryagain.py <<'EOF'\nimport asyncio\nimport tenacity\nfrom tenacity import Retrying, AsyncRetrying, stop_after_attempt, retry_never\n\ndef call():\n    try:\n        raise ValueError(\"the real error\")\n    except ValueError:\n        raise tenacity.TryAgain\n\nasync def acall():\n    try:\n        raise ValueError(\"the real error\")\n    except ValueError:\n       
…[248 chars elided]…
never, reraise=True)(acall)))]:\n    try:\n        fn()\n    except BaseException as e:\n        print(label, type(e).__name__, e)\nEOF\nPYTHONPATH=. <work>/env-tenacity/bin/python -I /tmp/repro_tryagain.py", "description": "Reproduce TryAgain reraise bug for sync and async"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/repro_tryagain.py", line 2, in <module>
    import tenacity
ModuleNotFoundError: No module named 'tenacity'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/repro_tryagain.py", "description": "Reproduce TryAgain reraise bug for sync and async"}
[tool_result] sync TryAgain 
async TryAgain
[assistant] Reproduced for both sync and async. The `ValueError` is preserved as the `__context__` of the `TryAgain`, so `RetryError.reraise()` should unwrap it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py", "old_string": "    def reraise(self) -> t.NoReturn:\n        if self.last_attempt.failed:\n            raise self.last_attempt.result()\n        raise self", "new_string": "    def reraise(self) -> t.NoReturn:\n        if self.last
…[19 chars elided]…
           exc = self.last_attempt.exception()\n            # A TryAgain raised from an except block only exists to trigger a retry;\n            # the error that caused it is its context, which is what should surface.\n            if isinstance(exc, TryAgain) and exc.__context__ is not None:\n                raise exc.__context__\n            raise self.last_attempt.result()\n        raise self"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing TryAgain tests, covering sync and async, then run the suite.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "offset": 1, "limit": 60}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITHOUT W
…[1178 chars elided]…
art_time = Fraction(retry_state.start_time)  # type: ignore[assignment]
50	    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
51	    assert retry_state.seconds_since_start == delay
52	
53	
54	def make_retry_state(
55	    previous_attempt_number: typing.Any,
56	    delay_since_first_attempt: typing.Any,
57	    last_result: typing.Any = None,
58	    upcoming_sleep: typing.Any = 0,
59	) -> RetryCallState:
60	    """Construct RetryCallState for given attempt number & delay.
[tool_use Bash] {"command": "grep -n \"asyncio\\|async def test\" tests/test_tenacity.py | head -15; ls tests/", "description": "Check existing async test conventions"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "sed -n 1,60p tests/test_asyncio.py; grep -n \"TryAgain\\|def test_\" tests/test_asyncio.py | tail -5", "description": "Read asyncio test conventions"}
[tool_result] # Copyright 2016 Étienne Bersac
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the spe
…[807 chars elided]…
(callable_: _F) -> Callable[..., Any]:
    @wraps(callable_)
    def wrapper(*a: Any, **kw: Any) -> Any:
        return asyncio.run(callable_(*a, **kw))

    return wrapper

390:    async def test_retry_with_async_result_and(self) -> None:
413:    async def test_retry_with_async_result_rand(self) -> None:
436:    async def test_async_retying_iterator(self) -> None:
446:    async def test_retry_function_attributes(self) -> None:
515:    async def test_sync_function_with_async_sleep(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py", "old_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(5, r.statistics[\"attempt_number\"])\n\n", "new_string": "        self.assertRaises(tenacity.TryAgain, r, _r)\n        self.assertEqual(
…[194 chars elided]…
e real error\")\n            except ValueError:\n                raise tenacity.TryAgain\n\n        r = Retrying(\n            stop=tenacity.stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "    async def test_retry_function_attributes(self) -> None:", "new_string": "    async def test_retry_try_again_from_except_reraises_cause(self) -> None:\n        async def _r() -> None:\n            try:\n         
…[89 chars elided]…
    raise tenacity.TryAgain\n\n        r = AsyncRetrying(\n            stop=stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            await r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n    async def test_retry_function_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25; PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/repro_tryagain.py", "description": "Run project test suite and repro script"}
[tool_result] ............s....................................................................................................................... [ 82%]
............................                                             [100%]
=============================== warnings summary ===============================
tests/test_asyncio.py::TestDecoratorWrapper::test_retry_function_attributes
  ~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/unittest/case.py:589: RuntimeWarn
…[455 chars elided]…
unittest/case.py:690: DeprecationWarning: It is deprecated to return a value that is not None from a test case (<bound method TestDecoratorWrapper.test_retry_function_attributes of <tests.test_asyncio.TestDecoratorWrapper testMethod=test_retry_function_attributes>>)
    return self.run(*args, **kwds)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
159 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.86s
sync ValueError the real error
async ValueError the real error
[assistant] All 159 pass. The `never awaited` warning is on `test_retry_function_attributes`, which I didn't touch, but I want to confirm my new async test is actually executed and not silently skipped by the same mechanism.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P -m pytest -p no:cacheprovider --color=no -v -k \"try_again\" 2>&1 | grep -i \"try_again\\|passed\\|failed\"; git stash list | head -0; git diff --stat", "description": "Run TryAgain tests verbosely and show diff stats"}
[tool_result] tests/test_asyncio.py::TestDecoratorWrapper::test_retry_try_again_from_except_reraises_cause PASSED [ 20%]
tests/test_tenacity.py::TestRetryConditions::test_retry_try_again PASSED [ 40%]
tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_forever PASSED [ 60%]
tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_forever_reraise PASSED [ 80%]
tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_from_except_reraises_cause PASSED [100%]
====================== 5 passed, 155 deselected in 0.04s =======================
head: illegal line count -- 0
 tenacity/__init__.py   |  5 +++++
 tests/test_asyncio.py  | 16 ++++++++++++++++
 tests/test_tenacity.py | 16 ++++++++++++++++
 3 files changed, 37 insertions(+)
[assistant] The async test reports PASSED, but it's an `async def` inside a `unittest.TestCase` class, which means the coroutine may never be awaited and the pass is vacuous. Let me check how neighboring async tests are declared.
[tool_use Bash] {"command": "sed -n 385,392p tests/test_asyncio.py; sed -n 436,450p tests/test_asyncio.py", "description": "Inspect decorators on neighboring async tests"}
[tool_result]         result = await test()

        self.assertEqual(4, result)

    @asynctest
    async def test_retry_with_async_result_and(self) -> None:
        async def test() -> int:
            attempts = 0
    async def test_async_retying_iterator(self) -> None:
        thing = NoIOErrorAfterCount(5)
        with pytest.raises(TypeError):
            for attempts in AsyncRetrying():
                with attempts:
                    await _async_function(thing)


class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_try_again_from_except_reraises_cause(self) -> None:
        async def _r() -> None:
            try:
                raise ValueError("the real error")
            except ValueError:
[assistant] My insertion landed in `TestDecoratorWrapper` without the `@asynctest` decorator, so it passes without running. I'll move it into the class that holds the other async-retry tests and decorate it.
[tool_use Bash] {"command": "grep -n \"^class \\|@asynctest\" tests/test_asyncio.py | head -40", "description": "List test classes and asynctest decorators"}
[tool_result] 79:class TestAsyncio(unittest.TestCase):
80:    @asynctest
86:    @asynctest
91:    @asynctest
98:    @asynctest
135:    @asynctest
163:class TestAsyncEnabled(unittest.TestCase):
164:    @asynctest
181:class TestTrio(unittest.TestCase):
195:class TestContextManager(unittest.TestCase):
196:    @asynctest
210:    @asynctest
225:    @asynctest
241:    @asynctest
255:    @asynctest
274:    @asynctest
298:    @asynctest
327:    @asynctest
358:    @asynctest
389:    @asynctest
412:    @asynctest
435:    @asynctest
444:class TestDecoratorWrapper(unittest.TestCase):
445:    @asynctest
529:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
530:    @asynctest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "    async def test_retry_try_again_from_except_reraises_cause(self) -> None:\n        async def _r() -> None:\n            try:\n                raise ValueError(\"the real error\")\n            except ValueError:\n
…[89 chars elided]…
top_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            await r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n    async def test_retry_function_attributes(self) -> None:", "new_string": "    async def test_retry_function_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py", "old_string": "                    await _async_function(thing)\n\n\nclass TestDecoratorWrapper(unittest.TestCase):", "new_string": "                    await _async_function(thing)\n\n    @asynctest\n    async def test_retry_try_
…[187 chars elided]…
               raise tenacity.TryAgain\n\n        r = AsyncRetrying(\n            stop=stop_after_attempt(2),\n            retry=tenacity.retry_never,\n            reraise=True,\n        )\n        with self.assertRaisesRegex(ValueError, \"the real error\"):\n            await r(_r)\n        self.assertEqual(2, r.statistics[\"attempt_number\"])\n\n\nclass TestDecoratorWrapper(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191528-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now I'll confirm the async test actually fails without the fix. I'll revert only the library file temporarily via a patch file (not stash), run the tests, then restore it.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; git diff -- tenacity/__init__.py > /tmp/tryagain_fix.patch && git checkout -- tenacity/__init__.py && echo \"== without fix ==\" && $P -m pytest -q -p no:cacheprovider --color=no -k try_again 2>&1 | tail -3; git apply /tmp/tryagain_fix.patch && echo \"== with fix ==\" && $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git diff --stat", "description": "Verify new tests fail without fix and pass with it"}
[tool_result] == without fix ==
FAILED tests/test_asyncio.py::TestContextManager::test_retry_try_again_from_except_reraises_cause
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_from_except_reraises_cause
2 failed, 3 passed, 155 deselected in 0.11s
== with fix ==
............................                                             [100%]
159 passed, 1 skipped, 12 subtests passed in 1.80s
 tenacity/__init__.py   |  5 +++++
 tests/test_asyncio.py  | 17 +++++++++++++++++
 tests/test_tenacity.py | 16 ++++++++++++++++
 3 files changed, 38 insertions(+)
[assistant] `TryAgain` raised from an `except` block now re-raises the original exception when `reraise=True`, for both `Retrying` and `AsyncRetrying`. The full suite passes (159 passed, 1 skipped), and the two new regression tests fail without the fix.

**Cause:** when attempts run out, `RetryError.reraise()` re-raised the last attempt's exception, which was the `TryAgain` sentinel. The real error survives only as that sentinel's `__context__`. Sync and async share this code path, so one change covers both.

**Fix** (`tenacity/__init__.py`, `RetryError.reraise`): if the last exception is a `TryAgain` wit
…[185 chars elided]…
_reraise` behaviour.

**Tests added:**
- `tests/test_tenacity.py`: sync case, `assertRaisesRegex(ValueError, ...)`.
- `tests/test_asyncio.py`: async case, placed in `TestContextManager` with `@asynctest`. My first placement lacked the decorator and passed without running, so I moved it and re-checked.

**Not changed:** the `reraise=False` path still raises `RetryError` with `TryAgain` as its cause. That matches the report, which asked only about `reraise=True`.

Nothing is committed. The changes are in the working tree: `tenacity/__init__.py`, `tests/test_tenacity.py`, `tests/test_asyncio.py`.
