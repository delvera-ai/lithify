# trajectory base-1

final message:
The first-attempt read now returns `0` for both sync and async. The fix is in `tenacity/__init__.py`, plus a regression test. I haven't committed anything.

**Cause:** `delay_since_first_attempt` was only written in `_run_stop`, which runs after the first attempt's outcome is known. `begin()` resets `statistics` at the start of every run but never set this key, so a read during the first attempt raised `KeyError`.

**Fix:** `begin()` now sets `self.statistics["delay_since_first_attempt"] = 0`, so the key exists from the start of each run. Both the sync and async retry paths call `begin()`, so one change covers both.

**Tests:** the suite passes, 136 passed and 1 skipped, up from 135 passed before the new test. The new test is `test_stats_delay_since_first_attempt_present_on_first_attempt` in `tests/test_tenacity.py`. It reads the key inside the first attempt and expects `0`. The async path I checked with a one-off script, not a committed test. It printed `[0, 2.2e-05]`, so the first attempt reads `0` and the second reads the elapsed time.

The existing statistics tests already expected this key with `mock.ANY`, so I didn't change any of them.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\\|statistics\" tenacity/ | head -50", "description": "Find statistics and delay_since_first_attempt references"}
[tool_result] tenacity/__init__.py:295:    def statistics(self) -> dict[str, t.Any]:
tenacity/__init__.py:296:        """Return a dictionary of runtime statistics.
tenacity/__init__.py:305:                     change between major releases as new statistics are
tenacity/__init__.py:312:                  their own view of statistics they have collected (in the
tenacity/__init__.py:314:                  statistics from each thread).
tenacity/__init__.py:316:        if not hasattr(self._local, "statistics"):
ten
…[812 chars elided]…
istics["idle_for"] += sleep
tenacity/__init__.py:433:            self.statistics["attempt_number"] += 1
tenacity/__init__.py:614:    statistics: dict[str, t.Any]
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:195:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:201:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "offset": 340, "limit": 110}
[tool_result] 340	            return copy(f, *args, **kw)
341	
342	        def retry_with(*args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]":
343	            return self.copy(*args, **kwargs).wraps(f)
344	
345	        # Preserve attributes
346	        wrapped_f.retry = self  # type: ignore[attr-defined]
347	        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
348	        wrapped_f.statistics = {}  # type: ignore[attr-defined]
349	
350	        return t.cast("_RetryDecorated[P, R]", wr
…[3566 chars elided]…
        self._add_action_func(self.before_sleep)
439	
440	        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))
441	
442	    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
443	        self.begin()
444	
445	        retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
446	        while True:
447	            do = self.iter(retry_state=retry_state)
448	            if isinstance(do, DoAttempt):
449	                yield AttemptManager(retry_state=retry_state)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tenacity/asyncio/__init__.py", "offset": 120, "limit": 90}
[tool_result] 120	                    if is_async:
121	                        result = await fn(*args, **kwargs)
122	                    else:
123	                        result = fn(*args, **kwargs)
124	                except BaseException:
125	                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
126	                else:
127	                    retry_state.set_result(result)
128	            elif isinstance(do, DoSleep):
129	                retry_state.prepare_for_next_att
…[3092 chars elided]…
    return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
197	
198	        # Preserve attributes
199	        async_wrapped.retry = self  # type: ignore[attr-defined]
200	        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
201	        async_wrapped.statistics = {}  # type: ignore[attr-defined]
202	
203	        return t.cast("_RetryDecorated[P, R]", async_wrapped)
204	
205	
206	__all__ = [
207	    "AsyncRetrying",
208	    "WrappedFn",
209	    "retry_all",
[assistant] The sync and async paths both call `begin()` before each run, so initializing the key there covers both. Checking the other callers and the tests that assert on `statistics` before editing.
[tool_use Bash] {"command": "grep -rn \"begin()\\|def begin\" tenacity/ ; grep -rn \"statistics\" tests/ | head -40", "description": "Check begin() callers and statistics in tests"}
[tool_result] tenacity/__init__.py:352:    def begin(self) -> None:
tenacity/__init__.py:443:        self.begin()
tenacity/__init__.py:475:        self.begin()
tenacity/tornadoweb.py:46:        self.begin()
tenacity/asyncio/__init__.py:112:        self.begin()
tenacity/asyncio/__init__.py:167:        self.begin()
tests/test_asyncio.py:417:        - statistics contains the value for the latest function run
tests/test_asyncio.py:419:        - retry object statistics do not contain valid information
tests/test_a
…[1622 chars elided]…
ryable_test_with_stop.statistics, expected_stats)
tests/test_tenacity.py:1352:                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})
tests/test_tenacity.py:1623:        self.assertEqual({}, _foobar.statistics)
tests/test_tenacity.py:1625:        self.assertEqual(1, _foobar.statistics["attempt_number"])
tests/test_tenacity.py:1632:        self.assertEqual({}, _foobar.statistics)
tests/test_tenacity.py:1635:        self.assertEqual(2, _foobar.statistics["attempt_number"])
[assistant] Some tests compare the full `statistics` dict, so I need to see what they expect. Running the baseline suite first.
[tool_use Bash] {"command": "ls <work>/env-tenacity/bin/python 2>&1; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run baseline test suite"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "offset": 1310, "limit": 45}
[tool_result] <work>/env-tenacity/bin/python
...........s................................................ [ 44%]
........................................................................ [ 97%]
....                                                                     [100%]
135 passed, 1 skipped, 12 subtests passed in 1.87s
[tool_result] 1310	
1311	        retrying = Retrying(
1312	            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
1313	        )
1314	        h = retrying.wraps(Hello())
1315	        self.assertEqual(h(), "Hello")
1316	
1317	    def test_retry_function_attributes(self) -> None:
1318	        """Test that the wrapped function attributes are exposed as intended.
1319	
1320	        - statistics contains the value for the latest function run
1321	        - retry object can be modified to c
…[1087 chars elided]…
t_attempt": mock.ANY,
1347	                    "idle_for": mock.ANY,
1348	                    "start_time": mock.ANY,
1349	                }
1350	                self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
1351	                self.assertEqual(exc.last_attempt.attempt_number, 1)
1352	                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})
1353	            else:
1354	                self.fail("RetryError should have been raised after 1 attempt")
[assistant] Baseline is green (135 passed, 1 skipped). The existing tests already expect the key, just with `mock.ANY`, so the fix is to set it in `begin()`. I'll make that change and add a regression test next to the existing `statistics` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"attempt_number\"] = 1\n        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"attempt_number\"] = 1\n        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "offset": 1600, "limit": 45}
[tool_result] 1600	
1601	    def test_reraise_no_exception(self) -> None:
1602	        calls = []
1603	
1604	        @retry(
1605	            wait=tenacity.wait_fixed(0.1),
1606	            stop=tenacity.stop_after_attempt(2),
1607	            retry=lambda retry_state: True,
1608	            reraise=True,
1609	        )
1610	        def _mock_fn() -> None:
1611	            calls.append("x")
1612	
1613	        self.assertRaises(tenacity.RetryError, _mock_fn)
1614	        self.assertEqual(2, len(calls))
1615	
1
…[519 chars elided]…
632	        self.assertEqual({}, _foobar.statistics)
1633	        with contextlib.suppress(Exception):
1634	            _foobar()
1635	        self.assertEqual(2, _foobar.statistics["attempt_number"])
1636	
1637	
1638	class TestRetryErrorCallback(unittest.TestCase):
1639	    def setUp(self) -> None:
1640	        self._attempt_number = 0
1641	        self._callback_called = False
1642	
1643	    def _callback(self, fut: tenacity.Future) -> tenacity.Future:
1644	        self._callback_called = True
[assistant] I'll add a regression test that reads the key from inside the first attempt, which is the reported failure mode.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\nclass TestRetryErrorCallback", "new_string": "        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n    def test_stats_delay
…[61 chars elided]…
n        seen = []\n\n        @retry(stop=tenacity.stop_after_attempt(2))\n        def _foobar() -> None:\n            seen.append(_foobar.statistics[\"delay_since_first_attempt\"])\n            raise ValueError(42)\n\n        with contextlib.suppress(Exception):\n            _foobar()\n        self.assertEqual(0, seen[0])\n        self.assertEqual(2, len(seen))\n\n\nclass TestRetryErrorCallback"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next I'll run the suite and a quick async check, since the async path also goes through `begin()`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -I -c '\nimport asyncio, tenacity\nfrom tenacity import AsyncRetrying, retry\nseen = []\n@tenacity.retry(stop=tenacity.stop_after_attempt(2))\nasync def f():\n    seen.append(f.statistics[\"delay_since_first_attempt\"])\n    raise ValueError\nasync def main():\n    try:\n        await f()\n    except Exception:\n        pass\n    print(\"async first-attempt values:\", seen)\nasyncio.run(main())\n'; git stash list >/dev/null; git diff --stat", "description": "Run tests and async first-attempt check"}
[tool_result] ...........s................................................ [ 43%]
........................................................................ [ 96%]
.....                                                                    [100%]
136 passed, 1 skipped, 12 subtests passed in 1.82s
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
 tenacity/__init__.py   |  1 +
 tests/test_tenacity.py | 13 +++++++++++++
 2 files changed, 14 insertions(+)
[assistant] The `-I` flag blocked the repo import, so I'll rerun the check with the repo on `PYTHONPATH` from a script outside the repo.
[tool_use Bash] {"command": "mkdir -p /tmp/tenacity-check && cat > /tmp/tenacity-check/async_check.py <<'EOF'\nimport asyncio\nimport tenacity\n\nseen = []\n\n@tenacity.retry(stop=tenacity.stop_after_attempt(2))\nasync def f():\n    seen.append(f.statistics[\"delay_since_first_attempt\"])\n    raise ValueError\n\nasync def main():\n    try:\n        await f()\n    except Exception:\n        pass\n    print(\"asyn
…[72 chars elided]…
user/.cache/lithify/work/repo-b561bbaa0f70/20261023-155058-bug-the-delay-since-first-attemp/base-1 && PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/tenacity-check/async_check.py; rm -rf /tmp/tenacity-check", "description": "Verify async first-attempt statistics key"}
[tool_result] async first-attempt values: [0, 2.19999928958714e-05]
[assistant] The first-attempt read now returns `0` for both sync and async. The fix is in `tenacity/__init__.py`, plus a regression test. I haven't committed anything.

**Cause:** `delay_since_first_attempt` was only written in `_run_stop`, which runs after the first attempt's outcome is known. `begin()` resets `statistics` at the start of every run but never set this key, so a read during the first attempt raised `KeyError`.

**Fix:** `begin()` now sets `self.statistics["delay_since_first_attempt"] = 0`, so the key exists from the start of each run. Both the sync and async retry paths call `begin()`, so one change covers both.

**Tests:** the suite passes, 136 passed and 1 skipped, up from 135 passed before the new test. The new test is `test_stats_delay_since_first_attempt_present_on_first_attempt` in `tests/test_tenacity.py`. It reads the key inside the first attempt and expects `0`. The async path I checked with a one-off script, not a committed test. It printed `[0, 2.2e-05]`, so the first attempt reads `0` and the second reads the elapsed time.

The existing statistics tests already expected this key with `mock.ANY`, so I didn't change any of them.
