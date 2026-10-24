# trajectory comp-1

final message:
`Retrying` objects and the built-in retry strategies can now be pickled, and a used `Retrying` restores to a working object. A `Pool(spawn).map` over a `Retrying` that has already run returned `[7, 7]`. The changes are uncommitted in the worktree.

**The change**
- **`tenacity/retry.py`:** the built-in strategies stored lambdas and nested functions as their predicates. They are now module-level helpers bound with `functools.partial`. This covers `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` (both `message=` and `match=`), and `retry_if_not_exception_message`.
- **`tenacity/__init__.py`:** `BaseRetrying` gets `__getstate__`/`__setstate__`. The `threading.local` can't be pickled, so it is dropped on save and recreated on restore. Per-run `statistics` also start fresh on the restored object.
- **Tests:** a new `TestPickling` class in `tests/test_tenacity.py` covers a fresh `Retrying`, a used one, a `@retry` function's `.retry`, the message/type strategies (checked by behaviour, not just round-trip), and stop/wait strategies.
- **Release note:** `releasenotes/notes/pickle-retrying-objects-3c516c9dd191ba3a.yaml`, a `fixes:` entry.

**Verification**
- Red: before the fix, 10 of the 12 new subtests/tests failed with the reported errors (for example `Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'`). The two that passed are the stop/wait round-trips, which already worked; they guard against regressions.
- Green: `TestPickling` passes (5 tests, 16 subtests).
- Full suite via `run_tests.py`: `exit=0`, 151 passed, 1 skipped.
- `check_changed.py`: exit 0, 0 problems. It first flagged one 91-column line in my test; I shortened it.
- `ruff` and `mypy` were not run, since the harness says they can't run here.

**Choices and side effects to review**
- A restored `Retrying` starts with empty `statistics`. I treated per-run statistics as runtime state, consistent with `copy()`. If you want them to survive a round-trip, that's a small change.
- `copy.copy(retrying)` now goes through the new hooks, so the copy gets its own thread-local state instead of sharing the original's. The existing tests pass with this.
- Still not picklable, and deliberately left alone because they hold user or OS objects: the closures from `before_log`/`after_log`/`before_sleep_log`, `stop_when_event_set` and `sleep_using_event` (they hold a `threading.Event`), and user callables such as `retry_if_result`/`retry_if_exception` predicates or `wait_exception`. A `Retrying` that uses any of these still won't pickle.
- I did not add a docs change to `doc/source/index.rst`, since this is a bug fix that changes no documented usage.

## events
[assistant] I'll start by reading the change-contract skill the project requires for pickling changes, then the relevant code.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls tenacity; echo ---; cat .lithify/harness/scripts/run_tests.py | head -60; echo ---; cat <work>/env-tenacity/bin/python --version 2>&1 | head -1", "description": "Read change-contract skill and list tenacity package"}
[tool_result] <persisted-output>
Output too large (65.6KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261023-202610-bug-retrying-objects-and-the-bui-comp-1/fdc0c78d-0eb6-4329-a73f-2ba2cfd8803a/tool-results/b5grt689r.txt

Preview (first 2KB):
---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`,
…[1263 chars elided]…
wns the loop once: `begin()` (start of every run), `_begin_iter`,
  `_post_retry_check_actions`, `_post_stop_check_actions` are shared by sync, async and
  tornado (`tenacity/tornadoweb.py`); `AsyncRetrying` and `TornadoRetrying` call
  `self.begin()` and do not override it. A fix in one of these shared methods needs no async
  copy — say so rather than editing `tenacity/asyncio/`.
- `AsyncRetrying` (`tenacity/asyncio/__init__.py`) re-implements `_run_retry`, `_run_wait`,
...
</persisted-output>
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/.lithify/harness/skills/tenacity-change-contract/SKILL.md"}
[tool_result] 1	---
2	name: tenacity-change-contract
3	description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, addi
…[14750 chars elided]…

192	- ruff (`line-length = 88`, `target-version = "py310"`) checks and format-checks the whole repo,
193	  tests included (`tox -e pep8`).
194	- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
195	  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
196	  annotated (ruff/mypy can't run here).
197	
198	## 4. Keep the change surface minimal
199	Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
200	
[tool_use Bash] {"command": "ls tenacity; wc -l tenacity/*.py; grep -n \"pickl\\|__getstate__\\|__setstate__\\|__reduce\\|copy\" -r tenacity | head -40; cat /tmp/claude-501/*/scratchpad/pr-work/env-tenacity/bin/python 2>/dev/null | head -0; ls .lithify/harness/; cat .lithify/memory.md 2>/dev/null | head -20", "description": "List tenacity package and find pickling-related code"}
[tool_result] __init__.py
_utils.py
_version.py
after.py
asyncio
before.py
before_sleep.py
nap.py
py.typed
retry.py
stop.py
tornadoweb.py
wait.py
     797 tenacity/__init__.py
     111 tenacity/_utils.py
       2 tenacity/_version.py
      46 tenacity/after.py
      42 tenacity/before.py
      67 tenacity/before_sleep.py
      43 tenacity/nap.py
     297 tenacity/retry.py
     130 tenacity/stop.py
      62 tenacity/tornadoweb.py
     271 tenacity/wait.py
    1868 total
tenacity/before.py:7:# You may obtain a 
…[1280 chars elided]…
n await copy(fn, *args, **kwargs)  # type: ignore[type-var]
tenacity/asyncio/retry.py:7:# You may obtain a copy of the License at
tenacity/stop.py:7:# You may obtain a copy of the License at
tenacity/after.py:7:# You may obtain a copy of the License at
tenacity/_utils.py:7:# You may obtain a copy of the License at
head: illegal line count -- 0
(eval):1: no matches found: /tmp/claude-501/*/scratchpad/pr-work/env-tenacity/bin/python
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The skill's section 1b2 maps the work: `Retrying` state, strategy classes with lambdas, and the callables that stay out of scope. Next I'll read the core files and the project's Python path.
[tool_use Bash] {"command": "cat .lithify/memory.md; echo ---; grep -nE \"lambda|^ {8,}def \" tenacity/retry.py tenacity/stop.py tenacity/wait.py tenacity/asyncio/retry.py; echo ---; sed -n 150,300p tenacity/__init__.py", "description": "Read memory file, grep lambdas, view Retrying init"}
[tool_result] cat: .lithify/memory.md: No such file or directory
---
tenacity/retry.py:111:        super().__init__(lambda e: isinstance(e, exception_types))
tenacity/retry.py:123:        super().__init__(lambda e: not isinstance(e, exception_types))
tenacity/retry.py:135:        super().__init__(lambda e: not isinstance(e, exception_types))
tenacity/retry.py:225:            def message_fnc(exception: BaseException) -> bool:
tenacity/retry.py:232:            def match_fnc(exception: BaseException) -> bool:
te
…[4938 chars elided]…
_error_cls),
            retry_error_callback=_first_set(
                retry_error_callback, self.retry_error_callback
            ),
            name=_first_set(name, self._name),
            enabled=_first_set(enabled, self.enabled),
        )

    def __str__(self) -> str:
        return self._name if self._name is not None else "<unknown>"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} object at 0x{id(self):x} ("
            f"stop={self.stop}, "
[tool_use Bash] {"command": "sed -n 300,330p tenacity/__init__.py; echo ...; grep -n \"_local\\|def statistics\\|def iter_state\\|def begin\\|class \\|__copy__\\|__getstate__\" tenacity/__init__.py; echo ---; sed -n 1,140p tenacity/retry.py", "description": "Read Retrying repr, locals and retry.py head"}
[tool_result]             f"stop={self.stop}, "
            f"wait={self.wait}, "
            f"sleep={self.sleep}, "
            f"retry={self.retry}, "
            f"before={self.before}, "
            f"after={self.after}, "
            f"name={self._name!r})>"
        )

    @property
    def statistics(self) -> dict[str, t.Any]:
        """Return a dictionary of runtime statistics.

        This dictionary will be empty when the controller has never been
        ran. When it is running or has ran previou
…[6200 chars elided]…
s until an exception is raised of one or more types."""

    def __init__(
        self,
        exception_types: type[BaseException]
        | tuple[type[BaseException], ...] = Exception,
    ) -> None:
        self.exception_types = exception_types
        super().__init__(lambda e: not isinstance(e, exception_types))

    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")
[tool_use Bash] {"command": "sed -n 140,297p tenacity/retry.py", "description": "Read rest of retry.py"}
[tool_result]         # always retry if no exception was raised
        if not retry_state.outcome.failed:
            return True

        exception = retry_state.outcome.exception()
        if exception is None:
            raise RuntimeError("outcome failed but the exception is None")
        return self.predicate(exception)


class retry_if_exception_cause_type(retry_base):
    """Retries if any of the causes of the raised exception is of one or more types.

    The check on the type of the cause of the e
…[4244 chars elided]…
s retry_all(retry_base):
    """Retries if all the retries condition are valid."""

    def __init__(self, *retries: "RetryBaseT") -> None:
        self.retries = retries

    def __call__(self, retry_state: "RetryCallState") -> bool:
        return all(r(retry_state) for r in self.retries)

    def __rand__(self, other: "RetryBaseT") -> "retry_all":
        if isinstance(other, retry_all):
            return retry_all(*other.retries, *self.retries)
        return retry_all(other, *self.retries)
[assistant] The lambdas and nested `def`s in `retry.py` are the blockers for the strategy classes. `BaseRetrying` also holds a `threading.local`, which can't be pickled. Next I'll check the test layout, the existing pickle test, the reno note format, and whether the project Python runs.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY; $PY --version; grep -n \"pickle\" tests/*.py | head; ls releasenotes/notes | tail -3; grep -n \"class Test\" tests/test_tenacity.py | head -50; grep -n \"^import\\|^from\" tests/test_tenacity.py; sed -n 1,30p .lithify/harness/scripts/run_tests.py | grep -n \"argv\\|usage\\|def \\|--\" ", "description": "Check project python, pickle tests, and test layout"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Python 3.12.13
tests/test_tenacity.py:1927:    def test_retry_error_is_pickleable(self) -> None:
tests/test_tenacity.py:1928:        import pickle
tests/test_tenacity.py:1931:        pickled = pickle.dumps(expec
…[1205 chars elided]…
m fractions import Fraction
27:from unittest import mock
29:import pytest
30:from typeguard import check_type
32:import tenacity
33:from tenacity import RetryCallState, RetryError, Retrying, retry
34:from tenacity.retry import retry_all, retry_any
10:    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
12:          ... run_tests.py --timeout 60 tests/test_x.py::Cls::test_name
21:          --timeout 60; if it is a test you wrote, make its retry loop bounded
[tool_use Bash] {"command": "sed -n 1926,1936p tests/test_tenacity.py; echo ...; sed -n 1747,1768p tests/test_tenacity.py; echo ...; tail -5 tests/test_tenacity.py; echo ---; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml", "description": "Read test class examples and reno note format"}
[tool_result] class TestRetryException(unittest.TestCase):
    def test_retry_error_is_pickleable(self) -> None:
        import pickle

        expected = RetryError(last_attempt=123)  # type: ignore[arg-type]
        pickled = pickle.dumps(expected)
        actual = pickle.loads(pickled)
        self.assertEqual(expected.last_attempt, actual.last_attempt)


class TestRetryTyping(unittest.TestCase):
...
class TestStatistics(unittest.TestCase):
    def test_stats(self) -> None:
        @retry()
        def _fo
…[346 chars elided]…
sertEqual({}, _foobar.statistics)
        with contextlib.suppress(Exception):
            _foobar()
        self.assertEqual(2, _foobar.statistics["attempt_number"])


class TestRetryErrorCallback(unittest.TestCase):
...
        assert mock_sleep.call_count == 1


if __name__ == "__main__":
    unittest.main()
---
---
features:
  - |
    If you're using `Trio <https://trio.readthedocs.io>`__, then
    ``@retry`` now works automatically. It's no longer necessary to
    pass ``sleep=trio.sleep``.
[assistant] The project Python is 3.12 and the existing pickle test is in `TestRetryException`. Before writing tests I need to confirm the exact names of the stop/wait strategies and how `wraps` attaches `.retry`.
[tool_use Bash] {"command": "grep -n \"^class \\|^[a-z_]* = \" tenacity/stop.py tenacity/wait.py | head -60; grep -n \"wrapped_f.retry\\|\\.retry = \" tenacity/__init__.py; grep -n \"stop_after_attempt\\|max_attempt_number\" tenacity/stop.py | head -3", "description": "List strategy class and instance names"}
[tool_result] tenacity/stop.py:27:class stop_base(abc.ABC):
tenacity/stop.py:44:class stop_any(stop_base):
tenacity/stop.py:54:class stop_all(stop_base):
tenacity/stop.py:64:class _stop_never(stop_base):
tenacity/stop.py:71:stop_never = _stop_never()
tenacity/stop.py:74:class stop_when_event_set(stop_base):
tenacity/stop.py:84:class stop_after_attempt(stop_base):
tenacity/stop.py:94:class stop_after_delay(stop_base):
tenacity/stop.py:113:class stop_before_delay(stop_base):
tenacity/wait.py:27:class wait_base(
…[385 chars elided]…
:175:class wait_exponential(wait_base):
tenacity/wait.py:209:class wait_random_exponential(wait_exponential):
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
248:        self.retry = retry
363:        wrapped_f.retry = self  # type: ignore[attr-defined]
364:        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]
84:class stop_after_attempt(stop_base):
87:    def __init__(self, max_attempt_number: int) -> None:
88:        self.max_attempt_number = max_attempt_number
[assistant] Names confirmed. Writing the regression tests first, before any code change, so I can see them fail on the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py", "old_string": "class TestRetryTyping(unittest.TestCase):", "new_string": "class TestPickling(unittest.TestCase):\n    def _count_attempts(self, strategy: typing.Any, exc: BaseException) -> int:\n        attempts = 0\n\n        de
…[3941 chars elided]…
           tenacity.wait_random(0, 1),\n            tenacity.wait_incrementing(1),\n            tenacity.wait_exponential(),\n        ]\n        for strategy in strategies:\n            with self.subTest(strategy=strategy):\n                restored = pickle.loads(pickle.dumps(strategy))\n                self.assertIs(type(strategy), type(restored))\n\n\nclass TestRetryTyping(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py has been updated successfully.
[assistant] The tests use `pickle`, so I'll add the top-level import, then run the first new test alone against the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py", "old_string": "import logging\nimport re\nimport time", "new_string": "import logging\nimport pickle\nimport re\nimport time"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": ".lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red1.txt", "description": "Run first pickling regression test on unfixed code"}
[tool_result] exit=126
(eval):1: permission denied: .lithify/harness/scripts/run_tests.py
[assistant] The script isn't executable, so I'll run it through the project Python as the harness specifies.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -25 /tmp/red1.txt", "description": "Run first regression test via project python"}
[tool_result] exit=1
tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable FAILED [100%]

=================================== FAILURES ===================================
___________________ TestPickling.test_retrying_is_pickleable ___________________

self = <tests.test_tenacity.TestPickling testMethod=test_retrying_is_pickleable>

    def test_retrying_is_pickleable(self) -> None:
        retrying = Retrying(
            stop=tenacity.stop_after_attempt(2),
            wait=tenacity.wait_fixed(0
…[177 chars elided]…
rying))
                                ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'

tests/test_tenacity.py:1962: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] That failure is the reported one: the lambda in `retry_if_exception_type.__init__`. Now I'll run the whole new class on unfixed code to confirm the other tests fail for their reasons too.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/red2.txt 2>&1; echo \"exit=$?\"; grep -E \"^E  |FAILED|passed|failed\" /tmp/red2.txt | head -40", "description": "Run full TestPickling class on unfixed code"}
[tool_result] exit=1
E       AttributeError: Can't get local object 'retry_if_exception_type.__init__.<locals>.<lambda>'
SUBFAILED(strategy=<tenacity.retry.retry_if_exception_type object at 0x109b49e80>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
SUBFAILED(strategy=<tenacity.retry.retry_if_not_exception_type object at 0x109b49f10>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
SUBFAILED(strategy=<tenacity.retry.retry_unless_exception
…[625 chars elided]…
UBFAILED(strategy=<tenacity.retry.retry_if_not_exception_message object at 0x109b49c70>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_decorated_function_retry_is_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_retrying_is_pickleable - At...
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_is_pickleable
=============== 10 failed, 2 passed, 9 subtests passed in 0.12s ================
[assistant] Ten of the twelve new tests fail for the reported reasons. The two that pass are the stop/wait round-trip, which already works; they're guards against regressions. Now the fix, starting with the strategy predicates in `retry.py`: replace the lambdas and nested functions with module-level helpers bound by `functools.partial`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState", "new_string": "import abc\nimport functools\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "class retry_if_exception(retry_base):\n    \"\"\"Retry strategy that retries if an exception verifies a predicate.\"\"\"", "new_string": "# Predicate helpers are module-level so that functools.partial objects built from
…[582 chars elided]…
sage_matches(prog: re.Pattern[str], exception: BaseException) -> bool:\n    return bool(prog.match(str(exception)))\n\n\ndef _negate(\n    predicate: typing.Callable[..., bool], *args: typing.Any, **kwargs: typing.Any\n) -> bool:\n    return not predicate(*args, **kwargs)\n\n\nclass retry_if_exception(retry_base):\n    \"\"\"Retry strategy that retries if an exception verifies a predicate.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "        self.exception_types = exception_types\n        super().__init__(lambda e: isinstance(e, exception_types))", "new_string": "        self.exception_types = exception_types\n        super().__init__(functools.partial(_is_instance, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "        self.exception_types = exception_types\n        super().__init__(lambda e: not isinstance(e, exception_types))\n\n\nclass retry_unless_exception_type(retry_if_exception):\n    \"\"\"Retries until an exception is
…[473 chars elided]…
less_exception_type(retry_if_exception):\n    \"\"\"Retries until an exception is raised of one or more types.\"\"\"\n\n    def __init__(\n        self,\n        exception_types: type[BaseException]\n        | tuple[type[BaseException], ...] = Exception,\n    ) -> None:\n        self.exception_types = exception_types\n        super().__init__(functools.partial(_is_not_instance, exception_types))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "        if message:\n\n            def message_fnc(exception: BaseException) -> bool:\n                return message == str(exception)\n\n            predicate = message_fnc\n        elif match:\n            prog = re.
…[36 chars elided]…
tch_fnc(exception: BaseException) -> bool:\n                return bool(prog.match(str(exception)))\n\n            predicate = match_fnc\n        else:", "new_string": "        if message:\n            predicate = functools.partial(_message_equals, message)\n        elif match:\n            prog = re.compile(match)\n            predicate = functools.partial(_message_matches, prog)\n        else:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py", "old_string": "        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)", "new_string": "        self.predicate = functools.partial(_negate, if_predicate)"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/retry.py has been updated successfully.
[assistant] Next, `BaseRetrying` in `tenacity/__init__.py`: drop the per-thread `_local` when pickling and recreate it on restore.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/__init__.py", "old_string": "    def __str__(self) -> str:\n        return self._name if self._name is not None else \"<unknown>\"", "new_string": "    def __getstate__(self) -> dict[str, t.Any]:\n        # threading.local cannot be pickled. Sta
…[62 chars elided]…
he configuration is kept and a restored object starts fresh.\n        state = self.__dict__.copy()\n        del state[\"_local\"]\n        return state\n\n    def __setstate__(self, state: dict[str, t.Any]) -> None:\n        self.__dict__.update(state)\n        self._local = threading.local()\n\n    def __str__(self) -> str:\n        return self._name if self._name is not None else \"<unknown>\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/green1.txt 2>&1; echo \"exit=$?\"; grep -E \"^E  |FAILED|passed|failed\" /tmp/green1.txt | head -30", "description": "Run TestPickling class after fix"}
[tool_result] exit=1
E       ValueError: boom
E       AssertionError: 2 != 1
SUBFAILED(strategy=<tenacity.retry.retry_if_not_exception_type object at 0x1096d5f70>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
SUBFAILED(strategy=<tenacity.retry.retry_unless_exception_type object at 0x1096d6150>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
SUBFAILED(strategy=<tenacity.retry.retry_if_not_exception_message object at 0x1096d6210>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
SUBFAILED(strategy=<tenacity.retry.retry_if_not_exception_message object at 0x1096d61b0>) tests/test_tenacity.py::TestPickling::test_builtin_retry_strategies_are_pickleable
FAILED tests/test_tenacity.py::TestPickling::test_used_retrying_is_pickleable
=============== 5 failed, 4 passed, 12 subtests passed in 0.54s ================
[assistant] Five failures remain, and they look like mistakes in my tests rather than the fix. A non-retried `ValueError` propagates out of the helper, which only suppresses `RetryError`. And in `test_used_retrying`, the restored call succeeds on its first attempt, so `attempt_number` is 1, not 2. I'll confirm with the detailed output before changing the tests.
[tool_use Bash] {"command": "grep -n -B12 \"AssertionError: 2 != 1\" /tmp/green1.txt | head -40", "description": "Inspect assertion failure context"}
[tool_result] 19-            if calls < 2:
20-                raise ValueError("not yet")
21-            return "done"
22-    
23-        self.assertEqual("done", retrying(flaky))
24-        self.assertEqual(2, retrying.statistics["attempt_number"])
25-    
26-        restored = pickle.loads(pickle.dumps(retrying))
27-        # Runtime statistics are per-run state, so the restored object starts fresh.
28-        self.assertEqual({}, restored.statistics)
29-        self.assertEqual("done", restored(flaky))
30->       self.assertEqual(2, restored.statistics["attempt_number"])
31:E       AssertionError: 2 != 1
[assistant] Both are test-side errors. I'll fix them: the helper suppresses only `RetryError` plus the exception type under test, which avoids the broad `suppress(Exception)` the contract warns against, and the restored-run expectation becomes 1.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py", "old_string": "        with contextlib.suppress(RetryError):\n            Retrying(\n                retry=strategy,\n                stop=tenacity.stop_after_attempt(3),\n                wait=tenacity.wait_none(),\n            )(fn)\n        return attempts", "new_string": "        # A non-retried exception propagates raw, so it is suppressed by its own type.\n        with contextlib.suppress(RetryError, type(exc)):\n            Retrying(\n                retry=strategy,\n                stop=tenacity.stop_after_attempt(3),\n                wait=tenacity.wait_none(),\n            )(fn)\n        return attempts"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(\"done\", restored(flaky))\n        self.assertEqual(2, restored.statistics[\"attempt_number\"])", "new_string": "        self.assertEqual(\"done\", restored(flaky))\n        # flaky already succeeds on its second call, so the restored run needs one attempt.\n        self.assertEqual(1, restored.statistics[\"attempt_number\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestPickling > /tmp/green2.txt 2>&1; echo \"exit=$?\"; grep -E \"^E  |FAILED|passed|failed\" /tmp/green2.txt | head -30", "description": "Re-run TestPickling after test corrections"}
[tool_result] exit=0
==================== 5 passed, 16 subtests passed in 0.04s =====================
[assistant] All five new `TestPickling` tests pass. Next I'll add the reno release note (the contract requires one for behaviour changes), then run the full suite.
[tool_use Bash] {"command": "SUF=$(openssl rand -hex 8); F=releasenotes/notes/pickle-retrying-objects-$SUF.yaml; printf -- '---\\nfixes:\\n  - |\\n    ``Retrying`` objects, including ones that have already run, and the built-in\\n    retry strategies (``retry_if_exception_type``, ``retry_if_exception_message``,\\n    and their variants) can now be pickled. This makes ``@retry``-decorated\\n    functions usable wi
…[178 chars elided]…
ding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python; $PY -c \"import yaml\" 2>/dev/null; $PY -c \"\nimport sys; sys.path.insert(0,'.')\nimport re\ns=open('$F').read()\nprint('ends-with-newline', s.endswith('\\n'), 'hex suffix ok', bool(re.search(r'-[0-9a-f]{16}\\.yaml$', '$F')))\"", "description": "Create reno release note for the fix"}
[tool_result] ---
fixes:
  - |
    ``Retrying`` objects, including ones that have already run, and the built-in
    retry strategies (``retry_if_exception_type``, ``retry_if_exception_message``,
    and their variants) can now be pickled. This makes ``@retry``-decorated
    functions usable with ``multiprocessing``. A restored ``Retrying`` keeps its
    configuration and starts with empty ``statistics``.
ends-with-newline True hex suffix ok True
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|exit=|FAILED\" /tmp/full.txt | tail -15", "description": "Run the full test suite via harness script"}
[tool_result] exit=0
============== 151 passed, 1 skipped, 28 subtests passed in 1.77s ==============
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Full suite: `exit=0`, 151 passed, 1 skipped. Now the stdlib check script and the skill's lambda grep.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc.txt 2>&1; echo \"exit=$?\"; cat /tmp/cc.txt | tail -30; echo ---; grep -nE \"lambda|^ {8,}def \" tenacity/retry.py tenacity/stop.py tenacity/wait.py tenacity/asyncio/retry.py; echo ---; git status --short", "description": "Run check_changed script and lambda grep"}
[tool_result] exit=1
changed: releasenotes/notes/pickle-retrying-objects-3c516c9dd191ba3a.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:2000: line is 91 columns (max 88)
FAIL: 1 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---
tenacity/wait.py:100:        def wait_chained():
tenacity/wait.py:122:        def http_error(exception: BaseException) -> float:
tenacity/wait.py:135:        def http_get_request(url: str) -> None:
tenacity/retry.py:86:# them pickle; lambdas and nested functions cannot be pickled.
---
 M tenacity/__init__.py
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/pickle-retrying-objects-3c516c9dd191ba3a.yaml
[assistant] `check_changed.py` flags one line over 88 columns, a comment I added in the test. I'll shorten it and re-run.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py", "old_string": "        # flaky already succeeds on its second call, so the restored run needs one attempt.", "new_string": "        # flaky succeeds from its second call on, so the restored run needs one attempt."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-202610-bug-retrying-objects-and-the-bui/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/cc2.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/cc2.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; echo \"exit=$?\"; grep -E \"passed|failed|exit=\" /tmp/full2.txt | tail -3", "description": "Shorten comment, re-run check script and full suite"}
[tool_result] exit=0
changed: releasenotes/notes/pickle-retrying-objects-3c516c9dd191ba3a.yaml, tenacity/__init__.py, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
exit=0
============== 151 passed, 1 skipped, 28 subtests passed in 1.76s ==============
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Both checks pass: `check_changed.py` exit 0 with 0 problems, and the full suite is green after the final edit. The original report is about `Pool.map`, so I'll also run a quick end-to-end probe that sends a used `Retrying` through a real process pool, bounded with a subprocess timeout as the harness guidance requires.
[tool_use Bash] {"command": "mkdir -p /tmp/probe_pickle && cat > /tmp/probe_pickle/probe.py <<'EOF'\nimport multiprocessing as mp\nimport tenacity\nfrom tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed\n\ndef work(retrying: Retrying) -> int:\n    return retrying(lambda: 7)\n\nif __name__ == \"__main__\":\n    r = Retrying(stop=stop_after_attempt(2), wait=wait_fixed(0), retry=retry
…[201 chars elided]…
))\nEOF\nPY=<work>/env-tenacity/bin/python; PYTHONPATH=\"$PWD\" $PY -c 'import subprocess,sys;sys.exit(subprocess.run(sys.argv[1:],timeout=60).returncode)' $PY /tmp/probe_pickle/probe.py; echo \"exit=$?\"", "description": "Probe Retrying through a spawn multiprocessing pool"}
[tool_result] pool.map result: [7, 7]
exit=0
[assistant] `Retrying` objects and the built-in retry strategies can now be pickled, and a used `Retrying` restores to a working object. A `Pool(spawn).map` over a `Retrying` that has already run returned `[7, 7]`. The changes are uncommitted in the worktree.

**The change**
- **`tenacity/retry.py`:** the built-in strategies stored lambdas and nested functions as their predicates. They are now module-level helpers bound with `functools.partial`. This covers `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`, `retry_if_exception_message` (both `message=` and `match=`), 
…[1527 chars elided]…
ets its own thread-local state instead of sharing the original's. The existing tests pass with this.
- Still not picklable, and deliberately left alone because they hold user or OS objects: the closures from `before_log`/`after_log`/`before_sleep_log`, `stop_when_event_set` and `sleep_using_event` (they hold a `threading.Event`), and user callables such as `retry_if_result`/`retry_if_exception` predicates or `wait_exception`. A `Retrying` that uses any of these still won't pickle.
- I did not add a docs change to `doc/source/index.rst`, since this is a bug fix that changes no documented usage.
