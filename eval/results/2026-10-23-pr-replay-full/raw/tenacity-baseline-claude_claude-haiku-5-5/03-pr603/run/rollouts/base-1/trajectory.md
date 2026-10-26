# trajectory base-1

final message:
The `delay_since_first_attempt` key is now present from the start of each run, with value `0` until a delay has occurred. The full test suite passes (135 passed, 1 skipped).

The fix is one line in `begin()` in `tenacity/__init__.py`:

```python
self.statistics["delay_since_first_attempt"] = 0
```

The key was previously only written in `_run_stop`, so it didn't exist until the first stop check ran. The async retrier inherits `begin()` and has no override, so it gets the same fix.

I checked it with a small script. Both `Retrying` and `AsyncRetrying` read `statistics["delay_since_first_attempt"]` inside the first attempt and get `0` without a `KeyError`. On the second attempt the value is a small positive number, as before.

I did not add a regression test for this, since the task was the bug fix and the existing tests didn't cover the first-attempt case. I can add one if you want it in this change.

## events
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" --include=*.py . | head -50", "description": "Find delay_since_first_attempt references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"delay_since_first_attempt\" . --exclude-dir=.git | head -50", "description": "Search repo for delay_since_first_attempt"}
[tool_result] tests/test_asyncio.py:428:            "delay_since_first_attempt": mock.ANY,
tests/test_asyncio.py:453:                    "delay_since_first_attempt": mock.ANY,
tests/test_tenacity.py:57:    delay_since_first_attempt: typing.Any,
tests/test_tenacity.py:66:        previous_attempt_number is _unset or delay_since_first_attempt is _unset
tests/test_tenacity.py:72:            delay_since_first_attempt=delay_since_first_attempt,
tests/test_tenacity.py:84:    _set_delay_since_start(retry_state, delay
…[227 chars elided]…
nce_first_attempt = 0.1
tests/test_after.py:35:            self.previous_attempt_number, delay_since_first_attempt
tests/test_after.py:72:        delay_since_first_attempt = 0.1
tests/test_after.py:75:            self.previous_attempt_number, delay_since_first_attempt
tenacity/__init__.py:373:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/asyncio/__init__.py:151:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "grep -n \"statistics\" tenacity/__init__.py tenacity/asyncio/__init__.py; sed -n 330,390p tenacity/__init__.py; echo ----; sed -n 120,165p tenacity/asyncio/__init__.py", "description": "Show statistics handling in tenacity sources"}
[tool_result] tenacity/__init__.py:295:    def statistics(self) -> dict[str, t.Any]:
tenacity/__init__.py:296:        """Return a dictionary of runtime statistics.
tenacity/__init__.py:305:                     change between major releases as new statistics are
tenacity/__init__.py:312:                  their own view of statistics they have collected (in the
tenacity/__init__.py:314:                  statistics from each thread).
tenacity/__init__.py:316:        if not hasattr(self._local, "statistics"):
ten
…[5125 chars elided]…
r_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
            retry_state
        )

    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = await action(retry_state)
        return result

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        raise TypeError("AsyncRetrying object is not iterable")
[assistant] The key is only written in `_run_stop`, and `begin()` clears statistics without setting it. I'll initialise it to `0` in `begin()`, which the async class inherits (no `begin` override in `tenacity/asyncio/__init__.py`).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-185721-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py", "old_string": "        self.statistics[\"idle_for\"] = 0\n\n    def _add_action_func", "new_string": "        self.statistics[\"idle_for\"] = 0\n        self.statistics[\"delay_since_first_attempt\"] = 0\n\n    def _add_action_func"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-185721-bug-the-delay-since-first-attemp/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Run project test suite"}
[tool_result] ...........s................................................ [ 44%]
........................................................................ [ 97%]
....                                                                     [100%]
135 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] Next I'll confirm the key is present on the first attempt for both the sync and async retriers.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -I -c \"\nimport asyncio\nfrom tenacity import Retrying, AsyncRetrying, stop_after_attempt\nseen = []\ndef f():\n    seen.append(dict(Retrying.__dict__ and {})) \nr = Retrying(stop=stop_after_attempt(2), wait=lambda rs: 0)\nfor atte
…[174 chars elided]…
rror\nar = AsyncRetrying(stop=stop_after_attempt(2), wait=lambda rs: 0)\nasync def g():\n    async for attempt in ar:\n        with attempt:\n            print('async first attempt:', ar.statistics['delay_since_first_attempt'])\n            if attempt.retry_state.attempt_number < 2: raise ValueError\nasyncio.run(g())\n\" 2>&1", "description": "Check key present on first attempt in sync and async"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 3, in <module>
ModuleNotFoundError: No module named 'tenacity'
[assistant] `-I` also drops the working directory from `sys.path`, so the repo's `tenacity` package wasn't importable. This is the project's own code, so I'll run without `-I`.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nimport asyncio\nfrom tenacity import Retrying, AsyncRetrying, stop_after_attempt\nr = Retrying(stop=stop_after_attempt(2), wait=lambda rs: 0)\nfor attempt in r:\n    with attempt:\n        print('sync first attempt:', r.stati
…[116 chars elided]…
Retrying(stop=stop_after_attempt(2), wait=lambda rs: 0)\nasync def g():\n    async for attempt in ar:\n        with attempt:\n            print('async first attempt:', ar.statistics['delay_since_first_attempt'])\n            if attempt.retry_state.attempt_number < 2: raise ValueError\nasyncio.run(g())\n\" 2>&1; git -C . diff --stat", "description": "Verify key on first attempt for sync and async"}
[tool_result] sync first attempt: 0
sync first attempt: 8.542003342881799e-06
async first attempt: 0
async first attempt: 1.5708006685599685e-05
 tenacity/__init__.py | 1 +
 1 file changed, 1 insertion(+)
[assistant] The `delay_since_first_attempt` key is now present from the start of each run, with value `0` until a delay has occurred. The full test suite passes (135 passed, 1 skipped).

The fix is one line in `begin()` in `tenacity/__init__.py`:

```python
self.statistics["delay_since_first_attempt"] = 0
```

The key was previously only written in `_run_stop`, so it didn't exist until the first stop check ran. The async retrier inherits `begin()` and has no override, so it gets the same fix.

I checked it with a small script. Both `Retrying` and `AsyncRetrying` read `statistics["delay_since_first_attempt"]` inside the first attempt and get `0` without a `KeyError`. On the second attempt the value is a small positive number, as before.

I did not add a regression test for this, since the task was the bug fix and the existing tests didn't cover the first-attempt case. I can add one if you want it in this change.
