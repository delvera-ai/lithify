# trajectory base-1

final message:
The key is now present from the start of each run, so reading `statistics["delay_since_first_attempt"]` during the first attempt no longer raises `KeyError`.

**The change:** in `tenacity/__init__.py`, `Retrying.begin()` now initialises `self.statistics["delay_since_first_attempt"] = 0` alongside `start_time`, `attempt_number` and `idle_for`. The key was previously only written in `_run_stop`, which runs after a failed attempt. The asyncio retrier inherits `begin()`, so it gets the same fix with no separate edit.

**Verification:**
- The project test suite passes with the command from `CLAUDE.md`: 135 passed, 1 skipped, 12 subtests passed.
- A quick script with a function that fails once and then succeeds read `[0, 6.6e-06]` across its two attempts. The first read is `0`, and the second reflects the value written at the stop check after the first failure.

I did not add a regression test, since the request was for the bug fix and the existing tests already cover the statistics shape. I also did not commit. The change is only in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\\|statistics\" --include=*.py . | grep -v \"^./tests/\" | head -50", "description": "Find statistics and delay_since_first_attempt usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\\|statistics\" --include='*.py' --include='*.pyi' --include='*.md' . | head -60", "description": "Search for statistics and delay_since_first_attempt references"}
[tool_result] tests/test_asyncio.py:417:        - statistics contains the value for the latest function run
tests/test_asyncio.py:419:        - retry object statistics do not contain valid information
tests/test_asyncio.py:428:            "delay_since_first_attempt": mock.ANY,
tests/test_asyncio.py:433:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:437:            _retryable_coroutine_with_2_attempts.retry.statistics,
tests/test_asyncio.py:453:                    "delay_sin
…[4130 chars elided]…
istics["idle_for"] += sleep
tenacity/__init__.py:433:            self.statistics["attempt_number"] += 1
tenacity/__init__.py:614:    statistics: dict[str, t.Any]
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:195:            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]
tenacity/asyncio/__init__.py:201:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
[tool_use Bash] {"command": "sed -n 345,440p tenacity/__init__.py && echo ---- && sed -n 130,160p tenacity/asyncio/__init__.py && echo ---- && sed -n 1315,1355p tests/test_tenacity.py", "description": "Read retry statistics code and related tests"}
[tool_result]         # Preserve attributes
        wrapped_f.retry = self  # type: ignore[attr-defined]
        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
        wrapped_f.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
        self.statistics.clear()
        self.statistics["start_time"] = time.monotonic()
        self.statistics["attempt_number"] = 1
        self.statistics["idle_for"] = 0

    def 
…[5643 chars elided]…
1,
                    "delay_since_first_attempt": mock.ANY,
                    "idle_for": mock.ANY,
                    "start_time": mock.ANY,
                }
                self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
                self.assertEqual(exc.last_attempt.attempt_number, 1)
                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})
            else:
                self.fail("RetryError should have been raised after 1 attempt")
[tool_use Bash] {"command": "grep -n \"def begin\\|self.statistics\\[\\\"idle_for\\\"\\] = \\|start_time\" tenacity/asyncio/__init__.py tenacity/__init__.py; git status --short; ls CHANGES* docs 2>/dev/null | head", "description": "Check begin overrides and changelog"}
[tool_result] tenacity/__init__.py:352:    def begin(self) -> None:
tenacity/__init__.py:354:        self.statistics["start_time"] = time.monotonic()
tenacity/__init__.py:356:        self.statistics["idle_for"] = 0
tenacity/__init__.py:530:        self.start_time = time.monotonic()
tenacity/__init__.py:568:        return self.outcome_timestamp - self.start_time
(eval):1: no matches found: CHANGES*
[assistant] The asyncio retrier inherits `begin()`, so one fix covers both paths. Setting the key in `begin()` where the other keys are initialised:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-160052-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-160052-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite"}
[tool_result] ...........s................................................ [ 44%]
........................................................................ [ 97%]
....                                                                     [100%]
135 passed, 1 skipped, 12 subtests passed in 1.83s
[assistant] The suite passes. Next I'll confirm the actual scenario: reading the key during the first attempt.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c '\nimport tenacity\nseen = []\n@tenacity.retry(stop=tenacity.stop_after_attempt(2))\ndef f():\n    seen.append(f.statistics[\"delay_since_first_attempt\"])\n    if len(seen) < 2:\n        raise ValueError\nf()\nprint(\"values read per attempt:\", seen)\n'", "description": "Check key is readable during first attempt"}
[tool_result] values read per attempt: [0, 6.624992238357663e-06]
[assistant] The key is now present from the start of each run, so reading `statistics["delay_since_first_attempt"]` during the first attempt no longer raises `KeyError`.

**The change:** in `tenacity/__init__.py`, `Retrying.begin()` now initialises `self.statistics["delay_since_first_attempt"] = 0` alongside `start_time`, `attempt_number` and `idle_for`. The key was previously only written in `_run_stop`, which runs after a failed attempt. The asyncio retrier inherits `begin()`, so it gets the same fix with no separate edit.

**Verification:**
- The project test suite passes with the command from `CLAUDE.md`: 135 passed, 1 skipped, 12 subtests passed.
- A quick script with a function that fails once and then succeeds read `[0, 6.6e-06]` across its two attempts. The first read is `0`, and the second reflects the value written at the stop check after the first failure.

I did not add a regression test, since the request was for the bug fix and the existing tests already cover the statistics shape. I also did not commit. The change is only in the working tree.
