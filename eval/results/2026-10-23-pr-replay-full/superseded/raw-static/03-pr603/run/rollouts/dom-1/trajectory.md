# trajectory dom-1

final message:
The `delay_since_first_attempt` key is now present from the start of every run, with value `0` until a delay has happened. The full suite passes: 137 passed, 1 skipped (baseline was 135 passed, 1 skipped; the two new tests account for the difference).

**Cause:** the key was only written in `_run_stop`, which runs after the first attempt's outcome is known. Code reading it during attempt 1 got a `KeyError`.

**Changes:**
- `tenacity/__init__.py`: `begin()` now initialises `statistics["delay_since_first_attempt"] = 0` alongside the other per-run keys. The sync, async and tornado entry points all go through `begin()`, so one line covers all three. `_run_stop` still overwrites it after each attempt, as before.
- `tests/test_tenacity.py`: `TestStatistics.test_delay_since_first_attempt_present_from_first_attempt` reads the key inside the first attempt of a `Retrying` loop and asserts it is `0`.
- `tests/test_asyncio.py`: the same check for `AsyncRetrying`. Both tests failed before the fix and pass after it.
- `releasenotes/notes/delay-since-first-attempt-initial-value-3f1c9a7b2e5d8064.yaml`: a `fixes:` note describing the behaviour change.

**Not run:** mypy and ruff aren't installed in the project's check interpreter, so the strict typing and lint rules were checked by reading only. I didn't add a tornado-specific test; the shared `begin()` path covers it, but there is no direct test for that entry point.

Nothing is committed. The changes are in the working tree for you to review.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"delay_since_first_attempt\" --include='*.py' --include='*.rst' . | head -50", "description": "Check status and find delay_since_first_attempt references"}
[tool_result] tests/test_tenacity.py:57:    delay_since_first_attempt: typing.Any,
tests/test_tenacity.py:66:        previous_attempt_number is _unset or delay_since_first_attempt is _unset
tests/test_tenacity.py:72:            delay_since_first_attempt=delay_since_first_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay_since_first_attempt)
tests/test_tenacity.py:1329:            "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:1346:                    "delay_since_
…[227 chars elided]…
syncio.py:453:                    "delay_since_first_attempt": mock.ANY,
tests/test_after.py:32:        delay_since_first_attempt = 0.1
tests/test_after.py:35:            self.previous_attempt_number, delay_since_first_attempt
tests/test_after.py:72:        delay_since_first_attempt = 0.1
tests/test_after.py:75:            self.previous_attempt_number, delay_since_first_attempt
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "sed -n 340,400p tenacity/__init__.py && echo ---- && grep -n \"statistics\\|def __init__\\|self.start_time\\|seconds_since_start\" tenacity/__init__.py | head -60 && echo ---- && sed -n 120,170p tenacity/asyncio/__init__.py", "description": "Read retry state statistics code in sync and async modules"}
[tool_result]             return copy(f, *args, **kw)

        def retry_with(*args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]":
            return self.copy(*args, **kwargs).wraps(f)

        # Preserve attributes
        wrapped_f.retry = self  # type: ignore[attr-defined]
        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
        wrapped_f.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
     
…[4936 chars elided]…
DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = await action(retry_state)
        return result

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        raise TypeError("AsyncRetrying object is not iterable")

    def __aiter__(self) -> "AsyncRetrying":
        self.begin()
        self._retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
        return self
[assistant] The fix belongs in `begin()`, which resets statistics at the start of each run. Before editing, I'll load the project's required change-contract skill and check the existing statistics tests.
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex 
…[4272 chars elided]…
est_retry_function_attributes` in both
  `tests/test_tenacity.py` and `tests/test_asyncio.py` assert the *exact* key set of
  `statistics`, so adding or removing a key is a visible change those tests pin down.
- **`with attempt:` swallows exceptions** (`AttemptManager.__exit__` stores the exception as
  the attempt's outcome and returns `True`). Code that raises inside the block — including a
  `KeyError` from reading `statistics` — becomes a failed, retried attempt, not an error that
  reaches the test. In a regression test, record values inside the block and assert on them
  after the loop.

[tool_use Bash] {"command": "sed -n 1315,1360p tests/test_tenacity.py && echo ---- && grep -n \"statistics\" tests/*.py | head -40 && echo ---- && ls releasenotes/notes | tail -5", "description": "Show existing statistics tests and release notes"}
[tool_result]         self.assertEqual(h(), "Hello")

    def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.

        - statistics contains the value for the latest function run
        - retry object can be modified to change its behaviour (useful to patch in tests)
        - retry object statistics do not contain valid information
        """

        self.assertTrue(_retryable_test_with_stop(NoneReturnUntilAfterCount(2)))

       
…[3456 chars elided]…
sts/test_tenacity.py:1625:        self.assertEqual(1, _foobar.statistics["attempt_number"])
tests/test_tenacity.py:1632:        self.assertEqual({}, _foobar.statistics)
tests/test_tenacity.py:1635:        self.assertEqual(2, _foobar.statistics["attempt_number"])
----
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] The skill confirms the fix location: initialise the key in `begin()`, which covers sync, async and tornado. Next I'll check the existing statistics test classes and the release-note format.
[tool_use Bash] {"command": "grep -n \"^class \\|^def _retryable\" tests/test_tenacity.py | head -80 && echo ---- && grep -n \"^class \\|^async def test\\|^def test\" tests/test_asyncio.py | head -60 && echo ---- && cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml && echo ---- && sed -n 1,30p tests/test_asyncio.py && echo ---- && sed -n 410,470p tests/test_asyncio.py", "description": "Inspect test structure and a sample release note"}
[tool_result] 88:class TestBase(unittest.TestCase):
114:class TestRetryingName(unittest.TestCase):
181:class TestStopConditions(unittest.TestCase):
285:class TestWaitConditions(unittest.TestCase):
667:class TestRetryConditions(unittest.TestCase):
787:class NoneReturnUntilAfterCount:
805:class NoIOErrorAfterCount:
823:class NoNameErrorAfterCount:
841:class NoNameErrorCauseAfterCount:
866:class NoIOErrorCauseAfterCount:
891:class NameErrorUntilCount:
911:class IOErrorUntilCount:
929:class CustomError(Exception)
…[4875 chars elided]…

                    _retryable_coroutine_with_2_attempts.statistics,
                    expected_stats,
                )
                self.assertEqual(exc.last_attempt.attempt_number, 1)
                self.assertEqual(
                    _retryable_coroutine_with_2_attempts.retry.statistics,
                    {},
                )
            else:
                self.fail("RetryError should have been raised after 1 attempt")


# make sure mypy accepts passing an async sleep function
[tool_use Bash] {"command": "sed -n 1617,1640p tests/test_tenacity.py && echo ---- && sed -n 178,200p tests/test_asyncio.py && echo ---- && grep -n \"statistics\\|class .*Test\\|async def test_.*stat\" tests/test_asyncio.py | head; echo ----; grep -n \"class TestBase\\|def _retryable_coroutine_with_2\\|NoIOErrorAfterCount(\" tests/test_asyncio.py | head -5; echo ----; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Read TestStatistics, asyncio test patterns, and baseline test run"}
[tool_result] class TestStatistics(unittest.TestCase):
    def test_stats(self) -> None:
        @retry()
        def _foobar() -> int:
            return 42

        self.assertEqual({}, _foobar.statistics)
        _foobar()
        self.assertEqual(1, _foobar.statistics["attempt_number"])

    def test_stats_failing(self) -> None:
        @retry(stop=tenacity.stop_after_attempt(2))
        def _foobar() -> None:
            raise ValueError(42)

        self.assertEqual({}, _foobar.statistics)
        with 
…[1503 chars elided]…
mpts.retry.statistics,
----
74:async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
82:        thing = NoIOErrorAfterCount(5)
93:        thing = NoIOErrorAfterCount(5)
100:        thing = NoIOErrorAfterCount(2)
142:        thing1 = NoIOErrorAfterCount(3)
----
........................................................................ [ 97%]
....                                                                     [100%]
135 passed, 1 skipped, 12 subtests passed in 1.87s
[assistant] Baseline is 135 passed, 1 skipped. I'll write the regression tests first so I can watch them fail before fixing. The tests read `statistics` from inside the first attempt, since that is the reported failure mode.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tests/test_tenacity.py", "old_string": "        self.assertEqual({}, _foobar.statistics)\n        with contextlib.suppress(Exception):\n            _foobar()\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n", "new_string": "        s
…[293 chars elided]…
trying(stop=tenacity.stop_after_attempt(2))\n        seen: list[float] = []\n        with contextlib.suppress(RetryError):\n            for attempt in retrying:\n                with attempt:\n                    seen.append(retrying.statistics[\"delay_since_first_attempt\"])\n                    raise ValueError(42)\n        self.assertEqual(2, len(seen))\n        self.assertEqual(0, seen[0])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tests/test_asyncio.py", "old_string": "        except RetryError:\n            pass\n\n        assert attempts == 3\n\n    @asynctest\n    async def test_reraise(self) -> None:", "new_string": "        except RetryError:\n            pass\n\n        asser
…[206 chars elided]…
: list[float] = []\n        try:\n            async for attempt in retrying:\n                with attempt:\n                    seen.append(retrying.statistics[\"delay_since_first_attempt\"])\n                    raise Exception\n        except RetryError:\n            pass\n\n        assert len(seen) == 2\n        assert seen[0] == 0\n\n    @asynctest\n    async def test_reraise(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no -k delay_since_first_attempt_present 2>&1 | tail -15", "description": "Run new regression tests expecting failure before fix"}
[tool_result]         retrying = tenacity.Retrying(stop=tenacity.stop_after_attempt(2))
        seen: list[float] = []
        with contextlib.suppress(RetryError):
            for attempt in retrying:
                with attempt:
                    seen.append(retrying.statistics["delay_since_first_attempt"])
                    raise ValueError(42)
>       self.assertEqual(2, len(seen))
E       AssertionError: 2 != 1

tests/test_tenacity.py:1645: AssertionError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestContextManager::test_delay_since_first_attempt_present_from_first_attempt
FAILED tests/test_tenacity.py::TestStatistics::test_delay_since_first_attempt_present_from_first_attempt
2 failed, 136 deselected in 0.07s
[assistant] Both tests fail on the current code, as expected. Now the fix: initialise the key in `begin()`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/tenacity/__init__.py has been updated successfully.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/releasenotes/notes/delay-since-first-attempt-initial-value-3f1c9a7b2e5d8064.yaml", "content": "---\nfixes:\n  - |\n    The ``delay_since_first_attempt`` key of ``statistics`` is now present from\n    the start of each run, with the value ``0`` until a retry delay has occurred.\n    Previously the key was only added after the first attempt's stop check, so\n    code reading ``statistics[\"delay_since_first_attempt\"]`` during the first\n    attempt raised ``KeyError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-161138-bug-the-delay-since-first-attemp/dom-1/releasenotes/notes/delay-since-first-attempt-initial-value-3f1c9a7b2e5d8064.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ........................................................................ [ 95%]
......                                                                   [100%]
137 passed, 1 skipped, 12 subtests passed in 1.77s
 M tenacity/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/delay-since-first-attempt-initial-value-3f1c9a7b2e5d8064.yaml
[assistant] The `delay_since_first_attempt` key is now present from the start of every run, with value `0` until a delay has happened. The full suite passes: 137 passed, 1 skipped (baseline was 135 passed, 1 skipped; the two new tests account for the difference).

**Cause:** the key was only written in `_run_stop`, which runs after the first attempt's outcome is known. Code reading it during attempt 1 got a `KeyError`.

**Changes:**
- `tenacity/__init__.py`: `begin()` now initialises `statistics["delay_since_first_attempt"] = 0` alongside the other per-run keys. The sync, async and tornado entry points al
…[302 chars elided]…

- `tests/test_asyncio.py`: the same check for `AsyncRetrying`. Both tests failed before the fix and pass after it.
- `releasenotes/notes/delay-since-first-attempt-initial-value-3f1c9a7b2e5d8064.yaml`: a `fixes:` note describing the behaviour change.

**Not run:** mypy and ruff aren't installed in the project's check interpreter, so the strict typing and lint rules were checked by reading only. I didn't add a tornado-specific test; the shared `begin()` path covers it, but there is no direct test for that entry point.

Nothing is committed. The changes are in the working tree for you to review.
