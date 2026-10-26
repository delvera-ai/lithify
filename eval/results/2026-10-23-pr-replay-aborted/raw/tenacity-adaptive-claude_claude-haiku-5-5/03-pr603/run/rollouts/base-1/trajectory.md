# trajectory base-1

final message:
The `delay_since_first_attempt` key is now present from the start of every run, with value `0` until the first stop check, so reading it on the first attempt no longer raises `KeyError`.

**Change:** one line in `begin()` in `tenacity/__init__.py`, which already resets the statistics at the start of each run:

```python
self.statistics["delay_since_first_attempt"] = 0
```

The async path (`tenacity/asyncio/__init__.py`) calls the same `begin()` from `__aiter__`, so it gets the fix too.

**Verification:**
- Repro against the patched repo: during the first attempt the key reads `0`. After the retries the final statistics contain the real elapsed value.
- Project test suite (`env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`): 135 passed, 1 skipped, 12 subtests passed.

I didn't add a regression test, to keep the change minimal. If you want one, a small test in `tests/test_tenacity.py` that reads the key inside the first attempt would lock this in. I also didn't commit anything. The diff is a single added line in the worktree.

## events
[tool_use Bash] {"command": "rtk grep -rn \"delay_since_first_attempt\\|statistics\" tenacity/ | head -50", "description": "Find statistics and delay_since_first_attempt usages"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\\|statistics\" tenacity/ | head -50", "description": "Find statistics and delay_since_first_attempt usages"}
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
[tool_use Bash] {"command": "sed -n 345,440p tenacity/__init__.py && echo ---- && sed -n 130,170p tenacity/asyncio/__init__.py && echo ---- && grep -rn \"delay_since_first\\|statistics\" tests/ docs/ README* | head -30", "description": "Read retry state and statistics code"}
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
…[7143 chars elided]…
ry.statistics, {})
tests/test_tenacity.py:1346:                    "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:1350:                self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
tests/test_tenacity.py:1352:                self.assertEqual(_retryable_test_with_stop.retry.statistics, {})
tests/test_tenacity.py:1623:        self.assertEqual({}, _foobar.statistics)
tests/test_tenacity.py:1625:        self.assertEqual(1, _foobar.statistics["attempt_number"])
[assistant] The fix belongs in `begin()`, which resets statistics at the start of each run. The asyncio retrying class inherits it through `__aiter__`. I'll check the docstring and the stats-related tests, then make the change.
[tool_use Bash] {"command": "sed -n 292,320p tenacity/__init__.py && grep -n \"def begin\\|self.begin()\" tenacity/*.py tenacity/asyncio/*.py && ls <work>/env-tenacity/bin/python 2>&1", "description": "Check docstring, begin() callers, and test env"}
[tool_result]         )

    @property
    def statistics(self) -> dict[str, t.Any]:
        """Return a dictionary of runtime statistics.

        This dictionary will be empty when the controller has never been
        ran. When it is running or has ran previously it should have (but
        may not) have useful and/or informational keys and values when
        running is underway and/or completed.

        .. warning:: The keys in this dictionary **should** be somewhat
                     stable (not chan
…[850 chars elided]…
# type: ignore[no-any-return]

    @property
tenacity/__init__.py:352:    def begin(self) -> None:
tenacity/__init__.py:443:        self.begin()
tenacity/__init__.py:475:        self.begin()
tenacity/tornadoweb.py:46:        self.begin()
tenacity/asyncio/__init__.py:112:        self.begin()
tenacity/asyncio/__init__.py:167:        self.begin()
<work>/env-tenacity/bin/python
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-155121-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-155121-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll run a quick reproduction and the project's test suite with the project's interpreter.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I -c \"\nimport tenacity\n@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(0))\ndef f():\n    print('stats during attempt:', f.statistics.get('delay_since_first_attempt', 'MISSING'))\n    if f.statistics['attempt_number'] < 3: raise ValueError\nf()\nprint('final:', f.statistics)\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Reproduce fix and run project test suite"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
...........s................................................ [ 44%]
........................................................................ [ 97%]
....                                                                     [100%]
135 passed, 1 skipped, 12 subtests passed in 1.84s
[assistant] The test suite passes. My repro failed only because `-I` ignores the working directory, so I'll rerun it with the repo on `PYTHONPATH`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY -I -c \"\nimport tenacity\n@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(0))\ndef f():\n    print('stats during attempt:', f.statistics.get('delay_since_first_attempt', 'MISSING'))\n    if f.statistics['attempt_number'] < 3: raise ValueError\nf()\nprint('final:', f.statistics)\n\"; git stash list >/dev/null; git diff --stat", "description": "Rerun repro with repo on path; show diff stat"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'
 tenacity/__init__.py | 1 +
 1 file changed, 1 insertion(+)
[assistant] `-I` also ignores `PYTHONPATH`, so I'll drop it for this inline snippet. The snippet is not reading any downloaded files.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport tenacity\n@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(0))\ndef f():\n    print('stats during attempt:', f.statistics.get('delay_since_first_attempt', 'MISSING'))\n    if f.statistics['attempt_number'] < 3: raise ValueError\nf()\nprint('final:', f.statistics)\n\"", "description": "Run repro snippet against the patched repo"}
[tool_result] stats during attempt: 0
stats during attempt: 9.541981853544712e-06
stats during attempt: 3.937497967854142e-05
final: {'start_time': 225979.422864125, 'attempt_number': 3, 'idle_for': 0.0, 'delay_since_first_attempt': 3.937497967854142e-05}
[assistant] The `delay_since_first_attempt` key is now present from the start of every run, with value `0` until the first stop check, so reading it on the first attempt no longer raises `KeyError`.

**Change:** one line in `begin()` in `tenacity/__init__.py`, which already resets the statistics at the start of each run:

```python
self.statistics["delay_since_first_attempt"] = 0
```

The async path (`tenacity/asyncio/__init__.py`) calls the same `begin()` from `__aiter__`, so it gets the fix too.

**Verification:**
- Repro against the patched repo: during the first attempt the key reads `0`. After the retries the final statistics contain the real elapsed value.
- Project test suite (`env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`): 135 passed, 1 skipped, 12 subtests passed.

I didn't add a regression test, to keep the change minimal. If you want one, a small test in `tests/test_tenacity.py` that reads the key inside the first attempt would lock this in. I also didn't commit anything. The diff is a single added line in the worktree.
