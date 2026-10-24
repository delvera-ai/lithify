# trajectory base-1

final message:
All three regressions are fixed in the worktree, with regression tests added. The suite passes (177 passed, 1 skipped). I did not commit.

**1. `wait=None`, `wait=0`, `wait=sum([])` raised `TypeError`** (sync and async)
- Cause: commit `e6ef84a` removed the `if self.wait:` guard in `_run_wait`, on the reasoning that `wait` is never falsy. That's wrong once callers pass `None`/`0`/`sum([])`.
- Fix: restored the guard in `tenacity/__init__.py` and `tenacity/asyncio/__init__.py`. Falsy waits sleep `0.0`.
- Mypy's `truthy-bool` rule (enabled in this repo) flags that guard because `WaitBaseT` doesn't admit `None`/`0`. I added a targeted `# type: ignore[truthy-bool]` with a comment explaining why, rather than widening the public type.

**2. `my_callable + wait_fixed(1)` raised `TypeError`**
- Cause: a plain function has no `__add__`, and `wait_base.__radd__` only accepted the int `0` that `sum()` seeds with.
- Fix: `__radd__` in `tenacity/wait.py` now returns `wait_combine(callable, self)` for callables. The `0` seed behaviour is unchanged. `__add__` and `wait_combine` accept plain callables in their type hints.

**3. `wait_combine` passed `retry_state=` as a keyword**
- Fix: it now passes the state positionally, so callables with any parameter name work.

**Tests:** I added four tests: falsy waits (sync and async), callable-plus-wait, and positional passing. All four fail on the unmodified base code and pass with the fix.

**Checks:** mypy reports the same error set as the base commit. The remaining ruff finding (`ICN001` in `tests/test_tenacity.py`) also exists on base. Some mypy errors come from `tornado`/`trio`/`sniffio` not being installed in my lint venv; they appear on base too.

**Not changed, but worth a look:** `wait_chain.__call__` has the same keyword-argument call (`wait_func(retry_state=retry_state)`), so it will break for plain callables with non-`retry_state` parameter names. I left it alone because it wasn't in your list, and the fix is the same one-line change.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -n \"wait\" tenacity/__init__.py | head -80 && cat tenacity/wait.py", "description": "Inspect repo layout and wait module"}
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
72:# Import all built-in wait strategies for easier usage.
73:from .wait import (
74:    wait_chain,
75:    wait_combine,
76:    wait_exception,
77:    wait_exponential,
78:    wait_exponential_jitter,
79:    wait_fixed,
80:    wait_incrementing,
81:    wait_none,
82:    wait_random,
83:    wait_random_exponential,
85:from .wait import wait_random_exponential as wait_full_jitter
108:    from .wait imp
…[11836 chars elided]…
      self.exp_base = exp_base
        self.jitter = _utils.to_seconds(jitter)
        self.min = _utils.to_seconds(min)

    @override
    def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.multiplier * exp + jitter
        except OverflowError:
            result = self.max
        return max(max(0, self.min), min(result, self.max))
[tool_use Bash] {"command": "sed -n 240,300p tenacity/__init__.py && sed -n 405,425p tenacity/__init__.py && grep -n \"wait\" tenacity/asyncio/__init__.py | head -30 && cat AGENTS.md | head -60 && git log --oneline -3 -- tenacity/wait.py && ls tests && grep -rn \"__radd__\\|wait_combine\\|wait=None\\|wait=0\" tests | head -30", "description": "Inspect retry init, async wait usage, tests"}
[tool_result]         exc_value: BaseException | None,
        traceback: "types.TracebackType | None",
    ) -> bool | None:
        return self.__exit__(exc_type, exc_value, traceback)


class BaseRetrying(ABC):
    def __init__(
        self,
        sleep: t.Callable[[int | float], None] = sleep,
        stop: "StopBaseT" = stop_never,
        wait: "WaitBaseT" = wait_none(),
        retry: "RetryBaseT" = retry_if_exception_type(),
        before: t.Callable[["RetryCallState"], None] = before_nothing,
   
…[5264 chars elided]…
-q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
a099996 refactor: mark overridden methods with @override (#682)
7c3c45c fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
c650fb4 Fix exponential wait threshold underflow (#656)
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
tests/test_tenacity.py:442:    def test_wait_combine(self) -> None:
tests/test_tenacity.py:444:            wait=tenacity.wait_combine(
[tool_use Bash] {"command": "git log --oneline -8 -- tenacity/ && git show 7c3c45c -- tenacity/wait.py | head -80 && git log -S\"_wait_func\" --oneline | head; grep -n \"callable\\|_utils.wrap\\|def wrap\" tenacity/_utils.py tenacity/__init__.py | head -30", "description": "Check git history for wait changes"}
[tool_result] 82b2a98 eval setup at a09999688c8d
a099996 refactor: mark overridden methods with @override (#682)
d6690dc refactor: declare BaseAction's REPR_FIELDS and NAME as ClassVar (#680)
e6ef84a refactor: drop always-true truthiness checks and enable truthy-bool (#679)
7c3c45c fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
a2af454 Fix static typing of @retry decorated instance methods (fixes #532) (#668)
6fec225 Improve inline type annotations (#664)
ac30991 chore: pin ruff to 
…[3680 chars elided]…
callable attribute rather than a descriptor, so accessing a
tenacity/__init__.py:765:    if len(dargs) == 1 and callable(dargs[0]):
tenacity/__init__.py:768:    def wrap(f: t.Callable[P, R]) -> _RetryDecorated[P, R]:
tenacity/__init__.py:771:                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
tenacity/__init__.py:777:        if _utils.is_coroutine_callable(f) or (
tenacity/__init__.py:778:            sleep is not None and _utils.is_coroutine_callable(sleep)
[tool_use Bash] {"command": "git show e6ef84a --stat && git show e6ef84a -- tenacity/ | head -300", "description": "Show truthiness-check refactor diff"}
[tool_result] commit e6ef84a1cebc01963106b1aecd598393054e0277
Author: Julien Danjou <julien@danjou.info>
Date:   Wed Aug 5 17:48:25 2026 +0200

    refactor: drop always-true truthiness checks and enable truthy-bool (#679)
    
    `truthy-bool` reports objects tested for truthiness that implement neither
    `__bool__` nor `__len__`, and so can only ever be true. Three sites:
    
    `BaseRetrying._run_wait` and `AsyncRetrying._run_wait` both guarded the
    wait call with `if self.wait:`. `wait` is typed `
…[4098 chars elided]…
override]
-        if self.wait:
-            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)
-        else:
-            sleep = 0.0
-
-        retry_state.upcoming_sleep = sleep
+        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
+            retry_state
+        )
 
     async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
         self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
[tool_use Bash] {"command": "sed -n 120,135p tenacity/_utils.py && sed -n 145,155p tenacity/asyncio/__init__.py && grep -n -A3 \"truthy\\|\\[tool.mypy\\]\\|\\[tool.pyright\\]\" pyproject.toml && sed -n 436,470p tests/test_tenacity.py && grep -n \"wait_arbitrary_sum\" -A25 tests/test_tenacity.py | head -40", "description": "Check async wrapper, lint config, related tests"}
[tool_result]     return inspect.iscoroutinefunction(dunder_call)


def wrap_to_async_func(
    call: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
    if is_coroutine_callable(call):
        return call

    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return call(*args, **kwargs)

    return inner
            retry_state
        )

    @override
    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignor
…[2371 chars elided]…
_state(1, 5))
506-            self.assertLess(w, 9)
507-            self.assertGreaterEqual(w, 6)
508-
509-    def _assert_range(self, wait: float, min_: float, max_: float) -> None:
510-        self.assertLess(wait, max_)
511-        self.assertGreaterEqual(wait, min_)
512-
513-    def _assert_inclusive_range(self, wait: float, low: float, high: float) -> None:
514-        self.assertLessEqual(wait, high)
515-        self.assertGreaterEqual(wait, low)
516-
517-    def _assert_inclusive_epsilon(
[tool_use Bash] {"command": "sed -n 112,140p pyproject.toml; ls <work>/env-tenacity/bin/ 2>&1 | head -30", "description": "Read lint config and check test env exists"}
[tool_result]     "SIM108",  # ternary instead of if-else (less readable in context)
]

[tool.mypy]
strict = true
# Match `requires-python`, so results do not depend on which interpreter
# happens to run mypy. Without this it defaults to the running version and
# silently skips checking that the code is valid on the oldest one we support.
python_version = "3.10"
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]
# `strict` is not "everything" -- these are checks it leav
…[7 chars elided]…

warn_unreachable = true
disallow_any_unimported = true
extra_checks = true
enable_error_code = [
    "deprecated",
    "exhaustive-match",
    "explicit-override",
    "ignore-without-code",
    "mutable-override",
    "possibly-undefined",
    "redundant-expr",
    "truthy-bool",
    "truthy-iterable",
    "unused-awaitable",
]

activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
py.test
pydoc.bat
pygmentize
pytest
python
python3
python3.12
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run test suite baseline"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.85s
[tool_use Bash] {"command": "mkdir -p /tmp/repro-tenacity && cat > /tmp/repro-tenacity/repro.py <<'EOF'\nimport asyncio\nimport tenacity\nfrom tenacity import Retrying, AsyncRetrying, wait_fixed, wait_combine\n\ndef fail_n(n):\n    calls = {\"i\": 0}\n    def f():\n        calls[\"i\"] += 1\n        if calls[\"i\"] <= n:\n            raise ValueError\n        return \"ok\"\n    return f\n\ndef run(label, fn):\n  
…[1043 chars elided]…
.5)(None))\nEOF\ncd ~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1 && PYTHONPATH=$PWD <work>/env-tenacity/bin/python -I /tmp/repro-tenacity/repro.py", "description": "Reproduce the three regressions with a script"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/repro-tenacity/repro.py", line 2, in <module>
    import tenacity
ModuleNotFoundError: No module named 'tenacity'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/repro-tenacity/repro.py", "description": "Reproduce regressions with PYTHONPATH set"}
[tool_result] sync wait=None EXC TypeError 'NoneType' object is not callable
async wait=None EXC TypeError 'NoneType' object is not callable
sync wait=0 EXC TypeError 'int' object is not callable
async wait=0 EXC TypeError 'int' object is not callable
sync wait=0 EXC TypeError 'int' object is not callable
async wait=0 EXC TypeError 'int' object is not callable
callable + wait_fixed EXC TypeError unsupported operand type(s) for +: 'function' and 'wait_fixed'
callable + wait_fixed value EXC TypeError unsupported operand type(s) for +: 'function' and 'wait_fixed'
sum with callables -> 3.0
wait_combine positional EXC TypeError other_name() got an unexpected keyword argument 'retry_state'
wait_combine any name EXC TypeError <lambda>.<locals>.<lambda>() got an unexpected keyword argument 'retry_state'
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1/tenacity/__init__.py", "old_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        retry_state.upcoming_sleep = self.wait(retry_state)", "new_string": "    def _run_wait(self, retry_state: \"RetryCallState\") -> None:\n        # `wait=None`, `wait=0` and `sum([])` are all accepted to mean \"no wait\".\n        if self.wait:\n            sleep = self.wait(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py", "old_string": "        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(\n            retry_state\n        )", "new_string": "        # `wait=None`, `wait=0` and `sum([])` are all accepted to mean \"no wait\".\n        if self.wait:\n            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)\n        else:\n            sleep = 0.0\n\n        retry_state.upcoming_sleep = sleep"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np = \"tenacity/wait.py\"\ns = open(p).read()\n\nold_radd = '''    def __add__(self, other: \"wait_base\") -> \"wait_combine\":\n        return wait_combine(self, other)\n\n    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, so tolerate that to\n        # make summing waits work. Any other left oper
…[1774 chars elided]…
al-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python /tmp/repro-tenacity/repro.py; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Apply wait.py fixes and rerun repro and tests"}
[tool_result] sync wait=None -> ok
async wait=None EXC RetryError RetryError[<Future at 0x103d117c0 state=finished raised ValueError>]
sync wait=0 -> ok
async wait=0 EXC RetryError RetryError[<Future at 0x103e6ce00 state=finished raised ValueError>]
sync wait=0 -> ok
async wait=0 EXC RetryError RetryError[<Future at 0x103e6d2e0 state=finished raised ValueError>]
callable + wait_fixed -> wait_combine
callable + wait_fixed value -> 3.0
sum with callables -> 3.0
wait_combine positional -> 4.0
wait_combine any name -> 1.5
...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.79s
[assistant] The async "RetryError" is a bug in my repro script, not the library: `fail_n(1)()` builds a fresh counter on every attempt, so it always fails. Fixing the script to build the callable once.
[tool_use Bash] {"command": "sed -i 's/    async def a(w=w):/    flaky = fail_n(1)\\n    async def a(w=w):/; s/(lambda: fail_n(1)())/(flaky)/; s/(fail_n(1)))$/(flaky))/' /tmp/repro-tenacity/repro.py && sed -i 's/^    run(f\"sync wait={w!r}\", lambda: Retrying(wait=w, stop=tenacity.stop_after_attempt(2), sleep=lambda s: None)(fail_n(1)))/    run(f\"sync wait={w!r}\", lambda: Retrying(wait=w, stop=tenacity.stop_after_attempt(2), sleep=lambda s: None)(fail_n(1)))/' /tmp/repro-tenacity/repro.py && PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/repro-tenacity/repro.py 2>&1 | head -4", "description": "Fix async repro script and rerun first lines"}
[tool_result ERROR] Exit code 1
sed: -I or -i may not be used with stdin
[tool_use Bash] {"command": "cat > /tmp/repro-tenacity/async_repro.py <<'EOF'\nimport asyncio\nimport tenacity\nfrom tenacity import AsyncRetrying\n\nasync def main():\n    for w in [None, 0, tenacity.wait_none()]:\n        calls = {\"i\": 0}\n        async def flaky():\n            calls[\"i\"] += 1\n            if calls[\"i\"] <= 1:\n                raise ValueError\n            return \"ok\"\n        r = Async
…[163 chars elided]…
ain())\nEOF\ncd ~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1 && PYTHONPATH=$PWD <work>/env-tenacity/bin/python /tmp/repro-tenacity/async_repro.py", "description": "Verify async wait values work with clean repro"}
[tool_result] async None -> ok
async 0 -> ok
async <tenacity.wait.wait_none object at 0x10149e9f0> -> ok
[assistant] Async works. Now the type checker and linter, since the repo enforces strict mypy and `truthy-bool`.
[tool_use Bash] {"command": "E=<work>/env-tenacity/bin; ls $E | grep -i \"mypy\\|ruff\"; ($E/mypy --version || which mypy ruff) 2>&1; ($E/mypy tenacity tests 2>&1 || true) | tail -15; ($E/ruff check tenacity tests 2>&1; $E/ruff format --check tenacity 2>&1) | tail -5", "description": "Run mypy and ruff if available"}
[tool_result] (eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
mypy not found
ruff not found
(eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
[assistant] The project's checker isn't in the test env, so I'll install mypy and ruff into a throwaway venv outside the repo to check the lint-sensitive lines.
[tool_use Bash] {"command": "python3 -m venv /tmp/repro-tenacity/lint && /tmp/repro-tenacity/lint/bin/pip install -q mypy ruff pytest 2>&1 | tail -2; /tmp/repro-tenacity/lint/bin/mypy tenacity tests 2>&1 | tail -15; /tmp/repro-tenacity/lint/bin/ruff check tenacity tests 2>&1 | tail -5; /tmp/repro-tenacity/lint/bin/ruff format --check tenacity tests 2>&1 | tail -3", "description": "Install lint tools in temp venv and run checks"}
[tool_result] [notice] A new release of pip is available: 25.0.1 -> 26.2.2
[notice] To update, run: python3.12 -m pip install --upgrade pip
tenacity/asyncio/__init__.py:67: error: Returning Any from function declared to return "Awaitable[None]"  [no-any-return]
tenacity/asyncio/__init__.py:151: error: Member "wait" has type "wait_base | Callable[[RetryCallState], float | int]" of which no members implement __bool__ or __len__ so it could always be true in boolean context  [truthy-bool]
tenacity/__init__.py:88
…[1159 chars elided]…
ion "test_retry" untyped  [untyped-decorator]
tests/test_tornado.py:50: error: Untyped decorator makes function "test_stop_after_attempt" untyped  [untyped-decorator]
tests/test_asyncio.py:24: error: Cannot find implementation or library stub for module named "trio"  [import-not-found]
Found 22 errors in 5 files (checked 19 source files)
    |
note: This is an unsafe fix and may change runtime behavior

Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
19 files already formatted
[assistant] Mypy flags my new `if self.wait:` guards with `truthy-bool`, which is the exact check that commit removed. The annotation `WaitBaseT` doesn't admit `None`/`0`, so mypy reads the guard as always-true. The other errors (tornado/trio imports, `no-any-return` at line 67, the ruff fix) look pre-existing or environmental; I'll confirm against the base commit.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\nfor p, old, new in [\n (\"tenacity/__init__.py\",\n  '        # `wait=None`, `wait=0` and `sum([])` are all accepted to mean \"no wait\".\\n        if self.wait:\\n',\n  '        # `wait=None`, `wait=0` and `sum([])` are all accepted to mean \"no wait\",\\n        # which `WaitBaseT` does not express, so the truthiness check is deliberate.\\n        if se
…[553 chars elided]…
nacity/lint/bin; $L/mypy tenacity tests 2>&1 | grep -v \"tornado\\|trio\" | tail -12; echo ---; $L/ruff check tenacity tests 2>&1 | head -12; echo ---; git stash list >/dev/null; git worktree list >/dev/null; git show HEAD:tenacity/asyncio/__init__.py > /tmp/repro-tenacity/base_async.py; echo \"(check baseline mypy count)\"; ", "description": "Add targeted truthy-bool ignores and rerun mypy/ruff"}
[tool_result] tenacity/asyncio/__init__.py:63: error: Cannot find implementation or library stub for module named "sniffio"  [import-not-found]
tenacity/asyncio/__init__.py:67: error: Returning Any from function declared to return "Awaitable[None]"  [no-any-return]
tenacity/__init__.py:88: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
tenacity/__init__.py:90: error: Unused "type: ignore" comment  [unused-ignore]
Found 20 errors in 5 files (checked 19 source files)
---
ICN001 `datetime` should be imported as `dt`
  --> tests/test_tenacity.py:17:8
   |
15 | # limitations under the License.
16 | import contextlib
17 | import datetime
   |        ^^^^^^^^
18 | import logging
19 | import pickle
   |
help: Alias `datetime` to `dt`
    |
---
(check baseline mypy count)
[assistant] Both files show as changed since my last read. I made those edits via script, so I'll check the actual diff and compare mypy output against the base commit to separate pre-existing errors from mine.
[tool_use Bash] {"command": "git diff && L=/tmp/repro-tenacity/lint/bin; $L/mypy tenacity tests 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/repro-tenacity/after.txt; git stash list --format='%H %gs' >/dev/null; rm -rf /tmp/repro-tenacity/basetree && mkdir -p /tmp/repro-tenacity/basetree && git archive HEAD | tar -x -C /tmp/repro-tenacity/basetree && (cd /tmp/repro-tenacity/basetree && $L/mypy tenacity tests 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/repro-tenacity/before.txt); diff /tmp/repro-tenacity/before.txt /tmp/repro-tenacity/after.txt && echo \"MYPY: identical error set to base\"", "description": "Review diff and compare mypy errors with base"}
[tool_result] diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 9ceaf16..6487149 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -415,7 +415,14 @@ class BaseRetrying(ABC):
         self.iter_state.retry_run_result = self.retry(retry_state)
 
     def _run_wait(self, retry_state: "RetryCallState") -> None:
-        retry_state.upcoming_sleep = self.wait(retry_state)
+        # `wait=None`, `wait=0` and `sum([])` are all accepted to mean "no wait",
+        # which `WaitBaseT` does 
…[2624 chars elided]…
self, *strategies: wait_base) -> None:
+    def __init__(self, *strategies: WaitBaseT) -> None:
         self.wait_funcs = strategies
 
     @override
     def __call__(self, retry_state: "RetryCallState") -> float:
-        return sum(x(retry_state=retry_state) for x in self.wait_funcs)
+        # Passed positionally: plain callables may name their parameter anything.
+        return sum(x(retry_state) for x in self.wait_funcs)
 
 
 class wait_chain(wait_base):
MYPY: identical error set to base
[assistant] Mypy's error set matches the base commit exactly, so the ignores introduce nothing new. The ruff hit is in an untouched test file (`ICN001`, pre-existing). Next I'll add regression tests so these don't recur, starting with the existing async test style.
[tool_use Bash] {"command": "sed -n 1,60p tests/test_asyncio.py | grep -n \"import\\|class \\|def \\|sleep\" | head -40; grep -n \"def test_\" tests/test_asyncio.py | head -5; grep -n \"^class\\|^def make_retry_state\" tests/test_tenacity.py | head", "description": "Look at async and sync test conventions"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
32:import tenacity
33:from tenacity import (
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
54:def asynctest(callable_: _F) -> Callable[..., Any]:
56:    def wrapper(*a: Any, **kw: Any) -> Any:

…[153 chars elided]…
 -> None:
98:    async def test_stop_after_attempt(self) -> None:
105:    def test_repr(self) -> None:
54:def make_retry_state(
87:class TestBase(unittest.TestCase):
114:class TestRetryingName(unittest.TestCase):
181:class TestStopConditions(unittest.TestCase):
285:class TestWaitConditions(unittest.TestCase):
722:class TestRetryConditions(unittest.TestCase):
959:class NoneReturnUntilAfterCount:
977:class NoIOErrorAfterCount:
995:class NoNameErrorAfterCount:
1013:class NoNameErrorCauseAfterCount:
[tool_use Bash] {"command": "sed -n 60,120p tests/test_asyncio.py", "description": "Read async test class structure"}
[tool_result] async def _async_function(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry
async def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry(stop=stop_after_attempt(2))
async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


class TestAsyncio(unittest.TestCase):
    @asynctest
    async def test_ret
…[951 chars elided]…
ert hasattr(_retryable_coroutine, "retry_with")

    @asynctest
    async def test_statistics_visible_through_outer_decorator(self) -> None:
        """Statistics must resolve when @retry is wrapped by another decorator.

        A well-behaved outer decorator uses functools.wraps, which copies the
        inner wrapper's ``__dict__`` (including ``statistics``). Rebinding the
        attribute on each call left the outer wrapper pointing at a stale empty
        dict. See issue #519.
        """
[assistant] I'll add regression tests next to the existing wait tests (sync) and in `TestAsyncio` (async). First checking what the test module imports.
[tool_use Bash] {"command": "sed -n 15,52p tests/test_tenacity.py | grep -v \"^#\"; sed -n 40,60p tests/test_asyncio.py | head -8; grep -n \"RetryCallState\" tenacity/__init__.py | head -3", "description": "Check test imports and RetryCallState export"}
[tool_result] import contextlib
import datetime
import logging
import pickle
import re
import time
import typing
import unittest
from fractions import Fraction
from unittest import mock

import pytest

import tenacity
from tenacity import RetryCallState, RetryError, Retrying, retry
from tenacity._utils import override
from tenacity.retry import retry_all, retry_any

_unset = object()


def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
    missing = []
    for k, v in kwargs.items()
…[522 chars elided]…
tate.start_time + Fraction(delay)
    assert retry_state.seconds_since_start == delay

    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
119:    actions: list[t.Callable[["RetryCallState"], t.Any]] = dataclasses.field(
215:    def __init__(self, retry_state: "RetryCallState") -> None:
253:        before: t.Callable[["RetryCallState"], None] = before_nothing,
[tool_use Bash] {"command": "python3 - <<'EOF'\np = \"tests/test_tenacity.py\"\ns = open(p).read()\nanchor = '''            self.assertLess(w, 9)\n            self.assertGreaterEqual(w, 6)\n\n    def _assert_range('''\nassert s.count(anchor) == 1\nnew = '''            self.assertLess(w, 9)\n            self.assertGreaterEqual(w, 6)\n\n    def test_falsy_wait_means_no_wait(self) -> None:\n        for wait in (None
…[2123 chars elided]…
eeps == [0.0]\n\n    def test_repr(self) -> None:'''\ns = s.replace(anchor, new)\nopen(p, \"w\").write(s)\nEOF\nE=<work>/env-tenacity/bin; $E/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Add regression tests and run project test suite"}
[tool_result] >           assert await retrying(_async_function, thing) == thing.go()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_asyncio.py:119: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tenacity/asyncio/__init__.py:121: in __call__
    do = await self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tenacity/asyncio/__init__.py:171: in iter
    result = await action(retry_state)
             ^^^^^^^^^^^^^^^^^^^^
…[399 chars elided]…
     retry_exc = self.retry_error_cls(fut)
        if self.reraise:
            retry_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x10c0af980 state=finished raised OSError>]

tenacity/__init__.py:478: RetryError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestAsyncio::test_falsy_wait_means_no_wait - te...
1 failed, 176 passed, 1 skipped, 12 subtests passed in 1.87s
[assistant] That failure is in my test, not the fix: `NoIOErrorAfterCount(2)` still fails on attempt 2 with a 2-attempt stop. Using count 1 so the second attempt succeeds.
[tool_use Bash] {"command": "sed -i 's/            thing = NoIOErrorAfterCount(2)\\n            sleeps/X/' tests/test_asyncio.py && python3 - <<'EOF'\np=\"tests/test_asyncio.py\"; s=open(p).read()\nold=\"            thing = NoIOErrorAfterCount(2)\\n            sleeps\"\nassert s.count(old)==1; open(p,\"w\").write(s.replace(old,\"            thing = NoIOErrorAfterCount(1)\\n            sleeps\"))\nEOF\nE=/private/
…[192 chars elided]…
o 2>&1 | tail -3; L=/tmp/repro-tenacity/lint/bin; $L/mypy tenacity tests 2>&1 | sed 's/:[0-9]*:/:/' | sort > /tmp/repro-tenacity/after2.txt; diff /tmp/repro-tenacity/before.txt /tmp/repro-tenacity/after2.txt && echo \"MYPY same as base\"; $L/ruff check tenacity tests 2>&1 | tail -2; $L/ruff format --check tenacity tests | tail -2", "description": "Fix async test count and rerun tests, mypy, ruff"}
[tool_result] sed: 2: "tests/test_asyncio.py
": undefined label 'ests/test_asyncio.py'
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestAsyncio::test_falsy_wait_means_no_wait - te...
1 failed, 176 passed, 1 skipped, 12 subtests passed in 1.81s
16a17
> tests/test_asyncio.py: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
Found 4 errors.
1 unsafe fix available with `--fix --unsafe-fixes`.
19 files already formatted
[assistant] My stray `sed` line errored, so the `&&` chain skipped the Python edit. Re-applying it, then checking the new mypy note and the ruff count.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"tests/test_asyncio.py\"; s=open(p).read()\nold=\"            thing = NoIOErrorAfterCount(2)\\n            sleeps\"\nassert s.count(old)==1; open(p,\"w\").write(s.replace(old,\"            thing = NoIOErrorAfterCount(1)\\n            sleeps\"))\nEOF\nE=<tmp>/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/
…[208 chars elided]…
(cd /tmp/repro-tenacity/basetree && $L/ruff check tenacity tests --output-format concise 2>&1 | tail -2); $L/mypy tenacity tests 2>&1 | grep -v \"note:\" | sed 's/:[0-9]*:/:/' | sort > /tmp/repro-tenacity/after3.txt; grep -v note /tmp/repro-tenacity/before.txt | diff - /tmp/repro-tenacity/after3.txt && echo \"MYPY: same errors as base\"", "description": "Apply async test fix and rerun all checks"}
[tool_result] ..............................................                           [100%]
177 passed, 1 skipped, 12 subtests passed in 1.80s
tests/test_asyncio.py:112:17: B023 Function definition does not bind loop variable `sleeps`
tests/test_tenacity.py:17:8: ICN001 `datetime` should be imported as `dt`
tests/test_tenacity.py:514:17: B023 Function definition does not bind loop variable `calls`
tests/test_tenacity.py:515:24: B023 Function definition does not bind loop variable `calls`
Found 4 errors.
1 unsafe fix available with `--fix --unsafe-fixes`.
Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
MYPY: same errors as base
[assistant] The test suite passes (177), and mypy's errors match the base. Ruff flags `B023` (closures over the loop variable) in my new tests, so I'll switch to `mock` objects, which removes the closures.
[tool_use Bash] {"command": "python3 - <<'EOF'\np = \"tests/test_tenacity.py\"\ns = open(p).read()\nold = '''    def test_falsy_wait_means_no_wait(self) -> None:\n        for wait in (None, 0, sum([])):\n            calls = []\n\n            def flaky() -> str:\n                calls.append(1)\n                if len(calls) < 2:\n                    raise ValueError\n                return \"ok\"\n\n            s
…[2296 chars elided]…
=no 2>&1 | tail -2; L=/tmp/repro-tenacity/lint/bin; $L/ruff check tenacity tests --output-format concise 2>&1 | tail -3; $L/ruff format --check tenacity tests | tail -1; $L/mypy tenacity tests 2>&1 | grep -v \"note:\" | sed 's/:[0-9]*:/:/' | sort | diff <(grep -v note /tmp/repro-tenacity/before.txt) - && echo \"MYPY: same as base\"", "description": "Switch new tests to mocks and rerun all checks"}
[tool_result] ..............................................                           [100%]
177 passed, 1 skipped, 12 subtests passed in 1.82s
tests/test_tenacity.py:17:8: ICN001 `datetime` should be imported as `dt`
Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
19 files already formatted
MYPY: same as base
[This command modified 1 file you've previously read: tests/test_asyncio.py. Call Read before editing.]
[assistant] All checks are green: 177 tests pass, mypy matches base, and the one remaining ruff hit (`ICN001`) also exists on the base commit. Last, I'll confirm the new tests actually catch the regressions by running them against the unmodified base code.
[tool_use Bash] {"command": "cp tests/test_tenacity.py tests/test_asyncio.py /tmp/repro-tenacity/basetree/tests/ && cd /tmp/repro-tenacity/basetree && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py tests/test_asyncio.py 2>&1 | grep -E \"FAILED|passed|failed\" | sed 's/ - .*//' | tail -8", "description": "Confirm new tests fail on unmodified base code"}
[tool_result] retry_state = <RetryCallState 4455682112: attempt #1; slept for 0.0; last result: failed (ValueError )>
args = (<RetryCallState 4455689360: attempt #1; slept for 0.0; last result: failed (OSError Hi there, I'm an IOError)>,)
FAILED tests/test_tenacity.py::TestWaitConditions::test_falsy_wait_means_no_wait
FAILED tests/test_tenacity.py::TestWaitConditions::test_plain_callable_added_to_wait_strategy
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_combine_passes_retry_state_positionally
FAILED tests/test_asyncio.py::TestAsyncio::test_falsy_wait_means_no_wait
4 failed, 162 passed, 1 skipped, 12 subtests passed in 1.87s
Shell cwd was reset to ~/.cache/lithify/work/repo-38fec5e48183/20261023-192822-three-regressions-that-only-appe/base-1
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Confirm changed files in worktree"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/wait.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 tenacity/__init__.py         |  9 ++++++++-
 tenacity/asyncio/__init__.py | 11 ++++++++---
 tenacity/wait.py             | 17 ++++++++++-------
 tests/test_asyncio.py        | 13 +++++++++++++
 tests/test_tenacity.py       | 27 +++++++++++++++++++++++++++
 5 files changed, 66 insertions(+), 11 deletions(-)
[assistant] All three regressions are fixed in the worktree, with regression tests added. The suite passes (177 passed, 1 skipped). I did not commit.

**1. `wait=None`, `wait=0`, `wait=sum([])` raised `TypeError`** (sync and async)
- Cause: commit `e6ef84a` removed the `if self.wait:` guard in `_run_wait`, on the reasoning that `wait` is never falsy. That's wrong once callers pass `None`/`0`/`sum([])`.
- Fix: restored the guard in `tenacity/__init__.py` and `tenacity/asyncio/__init__.py`. Falsy waits sleep `0.0`.
- Mypy's `truthy-bool` rule (enabled in this repo) flags that guard because `WaitBaseT` doesn
…[807 chars elided]…
 base code and pass with the fix.

**Checks:** mypy reports the same error set as the base commit. The remaining ruff finding (`ICN001` in `tests/test_tenacity.py`) also exists on base. Some mypy errors come from `tornado`/`trio`/`sniffio` not being installed in my lint venv; they appear on base too.

**Not changed, but worth a look:** `wait_chain.__call__` has the same keyword-argument call (`wait_func(retry_state=retry_state)`), so it will break for plain callables with non-`retry_state` parameter names. I left it alone because it wasn't in your list, and the fix is the same one-line change.
