# trajectory base-1

final message:
All three regressions are fixed. The full suite passes: 177 passed, 1 skipped (the original 173 plus 4 new tests). I reproduced each failure first, and the new tests fail on the original code.

**What caused each one**
1. **`None` / `0` / `sum([])`**: commit e6ef84a removed the `if self.wait:` guard in both `_run_wait` methods. Its reasoning assumed `wait` is always a strategy object, which isn't true for these falsy values. The fix is in `BaseRetrying.__init__` (`tenacity/__init__.py`): any non-callable `wait` becomes `wait_none()`. The sync, async and tornado retriers all go through that constructor.
2. **`my_callable + wait_fixed(1)`**: commit 7c3c45c made `__radd__` return `NotImplemented` for every non-zero operand, which also rejected plain callables. `__radd__` (`tenacity/wait.py`) now returns `wait_combine(other, self)` for a callable. Non-zero plain numbers still raise `TypeError`, as that commit intended.
3. **`wait_combine` keyword call**: it now passes the retry state positionally. The `*strategies` annotations are widened to `WaitBaseT` so plain callables type-check.

**Tests and notes**
- I added four tests without touching existing ones: falsy waits (sync and async), callable + strategy, and `wait_combine` with a differently named parameter.
- I added a reno note under `releasenotes/notes/`, matching the earlier wait fix. You didn't ask for it, so drop it if you don't want it.
- Nothing is committed.

**Things to check**
- **`wait_chain` has the same keyword call** (`wait_func(retry_state=retry_state)`), so a plain callable with another parameter name fails there too. I left it alone because you scoped the fix to `wait_combine`. It's a one-line change if you want it.
- **Lint and types are unverified**: mypy and ruff aren't installed in this environment, and the project's check is pytest. The repo runs strict mypy with `truthy-bool` and `redundant-expr` enabled, so `callable(wait)` in `__init__` might get flagged. Running mypy in CI would settle it.

## events
[assistant] I'll start by reading the wait strategy code and the retry call path.
[tool_use Bash] {"command": "git status --short && git log --oneline -3 && ls && cat tenacity/wait.py && grep -n \"wait\" tenacity/__init__.py | head -80", "description": "Inspect repo state and wait module"}
[tool_result] 0c81ee3 lithify: probe base
db1fdbc eval setup at a09999688c8d
a099996 refactor: mark overridden methods with @override (#682)
AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

…[11963 chars elided]…
waitable[None] | None] = after_nothing,
748:    before_sleep: t.Callable[["RetryCallState"], t.Awaitable[None] | None]
752:    retry_error_callback: t.Callable[["RetryCallState"], t.Any | t.Awaitable[t.Any]]
846:    "wait_chain",
847:    "wait_combine",
848:    "wait_exception",
849:    "wait_exponential",
850:    "wait_exponential_jitter",
851:    "wait_fixed",
852:    "wait_full_jitter",
853:    "wait_incrementing",
854:    "wait_none",
855:    "wait_random",
856:    "wait_random_exponential",
[assistant] The wait module already shows two of the likely causes: `__radd__` returns `NotImplemented` for any non-zero left operand, and `wait_combine` calls strategies with `retry_state=` as a keyword. Next I'll check how `Retrying` stores `wait`, and whether the project's test interpreter exists.
[tool_use Bash] {"command": "sed -n 240,300p tenacity/__init__.py && sed -n 410,425p tenacity/__init__.py && grep -n \"wait\" tenacity/asyncio/__init__.py | head -30 && grep -rn \"wait\" tenacity/_utils.py | head; ls <work>/env-tenacity/bin/python 2>&1; cat AGENTS.md | head -60", "description": "Read Retrying init and async wait usage"}
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
   
…[4823 chars elided]…
it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[assistant] Nothing normalizes `wait` before it is called: `Retrying` stores whatever it's given, and `_run_wait` calls it directly. Before choosing a fix I'll check git history and the tests for how `None`, `0` and `sum([])` were meant to be handled.
[tool_use Bash] {"command": "git log --oneline -S\"wait is None\" | head; git log --oneline -S\"__radd__\" | head; grep -rn \"wait=None\\|wait=0\\|sum(\\[\\])\\|__radd__\\|wait_combine\\|retry_state=\" tests | head -40", "description": "Search history and tests for wait normalization"}
[tool_result] cb49928 Declutter __init__ by using strategy selection
5271e77 remove need for specification of stop/wait type
7c3c45c fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
9a1b4b7 Implement '+' operator for wait strategies
tests/test_tenacity.py:442:    def test_wait_combine(self) -> None:
tests/test_tenacity.py:444:            wait=tenacity.wait_combine(
[tool_use Bash] {"command": "git show cb49928 -- tenacity/__init__.py | head -120; git show 5271e77 --stat | head; git show 7c3c45c | head -60; git show 9a1b4b7 -- tenacity/wait.py | head -80", "description": "Inspect history of wait normalization commits"}
[tool_result] commit 5271e7790e9e2bbe52ea03a61c6e1f5d4fc751b1
Author: Derek Wilson <dwilson@domaintools.com>
Date:   Fri May 2 14:52:06 2014 -0700

    remove need for specification of stop/wait type
    
    because it can be inferred from the args passed in

 AUTHORS.rst      |  1 +
 README.rst       | 10 +++---
commit 7c3c45cf57a3f10f6ee1334b137d607ead4974c1
Author: Julien Danjou <julien@danjou.info>
Date:   Wed Aug 5 17:42:32 2026 +0200

    fix: annotate wait_base.__radd__ as taking the int seed from sum
…[4245 chars elided]…
/max."""
 
     def __init__(self, min=0, max=1):
@@ -59,7 +80,7 @@ class wait_random(object):
                    * (self.wait_random_max - self.wait_random_min)))
 
 
-class wait_combine(object):
+class wait_combine(wait_base):
     """Combine several waiting strategies."""
 
     def __init__(self, *strategies):
@@ -71,7 +92,7 @@ class wait_combine(object):
             self.wait_funcs))
 
 
-class wait_chain(object):
+class wait_chain(wait_base):
     """Chain two or more waiting strategies.
[assistant] The history explains regression 2: commit 7c3c45c made `__radd__` return `NotImplemented` for every non-zero operand, which also rejects plain callables. For regression 1, the old `wait` normalization (None/number → strategy) must have been removed at some point. I'll find that commit and check the test expectations.
[tool_use Bash] {"command": "git log --oneline -S\"wait_none()\" -- tenacity | head; git log --oneline -S\"isinstance(wait\" -- tenacity | head; git log --oneline -S\"if wait is None\" -- tenacity | head; grep -n \"wait_arbitrary_sum\\|def test_wait_combine\\|wait=None\\|wait=0\\|5 + \" -A12 tests/test_tenacity.py | head -90", "description": "Locate removed wait normalization and related tests"}
[tool_result] 21137e7 Add async strategies (#451)
b49eb37 chore(typing): improve typing of WrappedFn (#390)
d442271 Do not package tests with tenacity (#308)
9a1b4b7 Implement '+' operator for wait strategies
74ba03f Move to a folder structure
de409a0 feat: accept `datetime.timedelta` instances as argument to `stop_after_delay` (#371)
18d05a6 Support `datetime.timedelta` as a valid wait unit type (#342)
52e0181 Move backward-compatibility-related utils to tenacity.compat
abf2329 Tweak wait funcs to accept cal
…[554 chars elided]…
elf) -> None:
--
492:    def test_wait_arbitrary_sum(self) -> None:
493-        r = Retrying(
494-            wait=sum(  # type: ignore[arg-type]
495-                [
496-                    tenacity.wait_fixed(1),
497-                    tenacity.wait_random(0, 3),
498-                    tenacity.wait_fixed(5),
499-                    tenacity.wait_none(),
500-                ]
501-            )
502-        )
503-        # Test it a few time since it's random
504-        for _ in range(1000):
[tool_use Bash] {"command": "for c in $(git log --format=%h -S\"wait_fixed(wait)\" -- tenacity/__init__.py tenacity/*.py | head -3); do echo \"== $c\"; git show $c | grep -n \"^[-+].*wait\" | head -30; done; git log --format='%h %s' -n 15 -- tenacity/__init__.py tenacity/wait.py", "description": "Trace earlier wait-coercion code in history"}
[tool_result] a099996 refactor: mark overridden methods with @override (#682)
d6690dc refactor: declare BaseAction's REPR_FIELDS and NAME as ClassVar (#680)
e6ef84a refactor: drop always-true truthiness checks and enable truthy-bool (#679)
7c3c45c fix: annotate wait_base.__radd__ as taking the int seed from sum() (#677)
a2af454 Fix static typing of @retry decorated instance methods (fixes #532) (#668)
6fec225 Improve inline type annotations (#664)
ac30991 chore: pin ruff to 0.16.1 (#670)
c650fb4 Fix exponenti
…[120 chars elided]…
 visible when @retry is further wrapped (fixes #519) (#653)
4ee186c wait_chain: reject empty strategy list with ValueError instead of IndexError (#646)
868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
1106b9a feat: deprecate `initial` in favor of `multiplier` in `wait_exponential_jitter` (#629)
3233040 feat: add `min` param and `timedelta` support to `wait_exponential_jitter` (#628)
[tool_use Bash] {"command": "git log -p -n 12 -- tenacity/__init__.py tenacity/wait.py tenacity/asyncio/__init__.py | grep -n \"^[-+].*\\(wait\\b\\|wait=\\|wait is\\|callable\\|isinstance\\|_run_wait\\|self.wait\\)\" | head -60", "description": "Scan recent diffs for wait coercion changes"}
[tool_result] 194:--- a/tenacity/wait.py
195:+++ b/tenacity/wait.py
389:-        if self.wait:
390:-            sleep = self.wait(retry_state)
395:+        retry_state.upcoming_sleep = self.wait(retry_state)
425:-        if self.wait:
426:-            sleep = await _utils.wrap_to_async_func(self.wait)(retry_state)
431:+        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
477:--- a/tenacity/wait.py
478:+++ b/tenacity/wait.py
523:+    # plain callable attribute rather than a descriptor, so accessing a
695:--- a/tenacity/wait.py
696:+++ b/tenacity/wait.py
724:--- a/tenacity/wait.py
725:+++ b/tenacity/wait.py
873:--- a/tenacity/wait.py
874:+++ b/tenacity/wait.py
[assistant] Found the cause of regression 1. An earlier version guarded the call with `if self.wait:`, so falsy values (`None`, `0`, `sum([])`) meant "no wait". Commit e6ef84a removed that guard as an "always-true truthiness check", which is wrong for these values. I'll look at the exact diff.
[tool_use Bash] {"command": "git show e6ef84a --stat && git show e6ef84a -- tenacity/__init__.py tenacity/asyncio/__init__.py tenacity/wait.py | head -250", "description": "Show the truthiness-check removal commit"}
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
[assistant] The removal commit assumed `wait` is always a `wait_base` object. That's false for the values the user listed: `None`, `0` and `sum([])` (which is `0`) are all falsy and need the "no wait" branch. Before editing, I'll get a baseline test run and check which lint/type tools the project enables, since `truthy-bool` was turned on by that same commit.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; grep -n \"truthy\\|warn_unreachable\\|\\[tool.mypy\\]\\|\\[tool.ruff\" -A3 pyproject.toml | head -40; ls $(dirname $PY) | grep -i \"mypy\\|ruff\"", "description": "Run baseline test suite and check lint tools"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.87s
96:[tool.ruff]
97-line-length = 88
98-indent-width = 4
99-target-version = "py310"
--
102:[tool.ruff.lint]
103-select = ["ASYNC", "B", "C4", "DTZ", "E", "EXE", "F", "FLY", "FURB", "I", "ICN", "ISC", "LOG", "PERF", "PGH", "PIE", "
…[75 chars elided]…
"W"]
104-ignore = [
105-    "B008",  # function calls in default arguments (intentional API design)
--
115:[tool.mypy]
116-strict = true
117-# Match `requires-python`, so results do not depend on which interpreter
118-# happens to run mypy. Without this it defaults to the running version and
--
125:warn_unreachable = true
126-disallow_any_unimported = true
127-extra_checks = true
128-enable_error_code = [
--
136:    "truthy-bool",
137:    "truthy-iterable",
138-    "unused-awaitable",
139-]
140-
[assistant] Baseline is green (173 passed, 1 skipped). Next I'll reproduce all three regressions with a small script outside the repo before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/repro_wait.py <<'EOF'\nimport asyncio\nfrom tenacity import Retrying, wait_fixed, wait_combine, retry_state_for_test if False else Retrying\nimport tenacity\nfrom tenacity import RetryCallState\n\ndef state():\n    s 
…[809 chars elided]…
(\"callable + wait_fixed\", lambda: type(plain + wait_fixed(1)).__name__)\nattempt(\"callable + wait_fixed value\", lambda: (plain + wait_fixed(1))(state()))\n\ndef named(rs): return 3.0\nattempt(\"wait_combine named param\", lambda: wait_combine(named, wait_fixed(1))(state()))\nEOF\n$PY -I /tmp/repro_wait.py 2>&1 | head -30", "description": "Reproduce the three regressions with a scratch script"}
[tool_result]   File "/tmp/repro_wait.py", line 2
    from tenacity import Retrying, wait_fixed, wait_combine, retry_state_for_test if False else Retrying
                                                                                  ^^
SyntaxError: invalid syntax
[assistant] My first script had a syntax error. I'll rewrite it cleanly and point `sys.path` at the repo, since `-I` ignores the working directory.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cat > /tmp/repro_wait.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport tenacity\nfrom tenacity import Retrying, RetryCallState, wait_fixed, wait_combine, stop_after_attempt\n\n\ndef make_state():\n    s = RetryCal
…[573 chars elided]…
n 3.0\n\n\nattempt(\"callable + wait_fixed type\", lambda: type(plain + wait_fixed(1)).__name__)\nattempt(\"callable + wait_fixed value\", lambda: (plain + wait_fixed(1))(make_state()))\nattempt(\"wait_combine named param\", lambda: wait_combine(named, wait_fixed(1))(make_state()))\nEOF\n$PY -I /tmp/repro_wait.py \"$PWD\" 2>&1 | head -30", "description": "Run reproduction script against the repo"}
[tool_result] sync wait=None RAISED TypeError 'NoneType' object is not callable
sync wait=0 RAISED TypeError 'int' object is not callable
sync wait=sum([]) RAISED TypeError 'int' object is not callable
callable + wait_fixed type RAISED TypeError unsupported operand type(s) for +: 'function' and 'wait_fixed'
callable + wait_fixed value RAISED TypeError unsupported operand type(s) for +: 'function' and 'wait_fixed'
wait_combine named param RAISED TypeError named() got an unexpected keyword argument 'retry_state'
[assistant] All three reproduce with the exact errors from the report. Before choosing the fix for regression 1, I'll check whether the project's mypy and ruff are available, because the `truthy-bool` rule decides what a restored guard looks like.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m mypy --version 2>&1 | tail -1; $PY -m ruff --version 2>&1 | tail -1; which mypy ruff uv 2>&1; sed -n 115,140p pyproject.toml", "description": "Check whether mypy and ruff are installed"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
mypy not found
ruff not found
uv not found
[tool.mypy]
strict = true
# Match `requires-python`, so results do not depend on which interpreter
# ha
…[161 chars elided]…
ion = "3.10"
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]
# `strict` is not "everything" -- these are checks it leaves off.
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
[assistant] mypy and ruff aren't installed in the project's environment, and the project's check is pytest, so I'll rely on the test suite and keep the types consistent by reading. I'll look at the existing wait tests and the async test layout so the new tests match them.
[tool_use Bash] {"command": "sed -n 485,520p tests/test_tenacity.py; ls tests; grep -n \"def make_retry_state\" -A12 tests/test_tenacity.py; grep -n \"class .*Test\\|async def test_wait\\|def test_.*wait\" tests/*.py | head -30; sed -n 1,30p releasenotes/notes/$(ls releasenotes/notes | grep wait-radd | head -1) 2>/dev/null; ls releasenotes/notes | tail -3", "description": "Read existing wait tests and release note layout"}
[tool_result]         )
        # Test it a few time since it's random
        for _i in range(1000):
            w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

    def test_wait_arbitrary_sum(self) -> None:
        r = Retrying(
            wait=sum(  # type: ignore[arg-type]
                [
                    tenacity.wait_fixed(1),
                    tenacity.wait_random(0, 3),
                    tenacity.wait_fixed(5),
                 
…[3817 chars elided]…
- |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[assistant] I have what I need. Here's the plan:

1. **Falsy `wait` (`None`, `0`, `sum([])`)**: `BaseRetrying.__init__` is shared by sync, async and tornado, and `_run_wait` calls `self.wait` directly. I'll normalize there: anything that isn't callable becomes `wait_none()`. That keeps `_run_wait` unchanged and avoids the `truthy-bool` rule that the removal commit enabled.
2. **Plain callable + strategy**: `__radd__` gets a callable branch that builds `wait_combine(other, self)`. Non-zero non-callable operands still return `NotImplemented`, as the 7c3c45c commit intended.
3. **`wait_combine`**: call strategies positionally.

I'll start with `wait.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __add__(self, other: \"wait_base\") -> \"wait_combine\":\n        return wait_combine(self, other)\n\n    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, 
…[436 chars elided]…
)` seeds its accumulator with the int 0, so tolerate that to\n        # make summing waits work.\n        if other == 0:\n            return self\n        # A plain callable on the left has no `__add__` that accepts a wait\n        # strategy, so Python falls back to this reflected operator.\n        if callable(other):\n            return wait_combine(other, self)\n        return NotImplemented"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __init__(self, *strategies: wait_base) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state=retry_state) for x in self.wait_funcs)", "new_string": "    def __init__(self, *strategies: WaitBaseT) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        # Pass positionally so plain callables may name their parameter freely.\n        return sum(x(retry_state) for x in self.wait_funcs)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now the normalization in `BaseRetrying.__init__`. `wait_none` is already imported there, and the async `Retrying` passes its `wait` through `super().__init__`, so one change covers both.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/__init__.py", "old_string": "        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry", "new_string": "        self.sleep = sleep\n        self.stop = stop\n        # `None`, `0` and `sum([])` all mean \"no wait\".\n        self.wait = wait if callable(wait) else wait_none()\n        self.retry = retry"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Next I'll confirm that the async and tornado retriers both reach `BaseRetrying.__init__`, and look at the async test style before adding regression tests.
[tool_use Bash] {"command": "grep -n \"super().__init__\\|class .*Retrying\" tenacity/asyncio/__init__.py tenacity/tornadoweb.py; grep -n \"^class \\|asyncio.run\\|async def test_\" tests/test_asyncio.py | head -20; grep -n \"IsolatedAsyncioTestCase\\|^import\\|^from\" tests/test_asyncio.py | head", "description": "Check retrier inheritance and async test style"}
[tool_result] tenacity/tornadoweb.py:29:class TornadoRetrying(BaseRetrying):
tenacity/tornadoweb.py:37:        super().__init__(**kwargs)
tenacity/asyncio/__init__.py:75:class AsyncRetrying(BaseRetrying):
tenacity/asyncio/__init__.py:97:        super().__init__(
57:        return asyncio.run(callable_(*a, **kw))
79:class TestAsyncio(unittest.TestCase):
81:    async def test_retry(self) -> None:
87:    async def test_iscoroutinefunction(self) -> None:
91:    async def test_retry_using_async_retying(self) -> No
…[694 chars elided]…
_manager(self) -> None:
280:    async def test_reraise(self) -> None:
296:    async def test_reraise_try_again_with_cause(self) -> None:
319:    async def test_sleeps(self) -> None:
333:    async def test_retry_with_result(self) -> None:
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
[tool_use Bash] {"command": "sed -n 79,100p tests/test_asyncio.py; sed -n 319,333p tests/test_asyncio.py", "description": "Read async test examples"}
[tool_result] class TestAsyncio(unittest.TestCase):
    @asynctest
    async def test_retry(self) -> None:
        thing = NoIOErrorAfterCount(5)
        await _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @asynctest
    async def test_iscoroutinefunction(self) -> None:
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
        thing = NoIOErrorAfterCount(5)
        retrying = AsyncRetrying
…[185 chars elided]…
rorAfterCount(2)
        try:
    async def test_sleeps(self) -> None:
        start = current_time_ms()
        try:
            async for attempt in tasyncio.AsyncRetrying(
                stop=stop_after_attempt(1), wait=wait_fixed(1)
            ):
                with attempt:
                    raise Exception
        except RetryError:
            pass
        t = current_time_ms() - start
        self.assertLess(t, 1.1)

    @asynctest
    async def test_retry_with_result(self) -> None:
[assistant] Next I'll check the imports the new tests need, then add regression tests next to the existing wait tests (sync) and the async retry tests. I won't modify any existing test.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|    RetryCallState\\|    RetryError\\|    stop_after_attempt\\|    wait_fixed\\|    AsyncRetrying\" tests/test_tenacity.py tests/test_asyncio.py | head -60; sed -n 33,50p tests/test_asyncio.py", "description": "Check test module imports"}
[tool_result] tests/test_asyncio.py:15:import asyncio
tests/test_asyncio.py:16:import inspect
tests/test_asyncio.py:17:import unittest
tests/test_asyncio.py:18:from collections.abc import Callable, Coroutine
tests/test_asyncio.py:19:from functools import wraps
tests/test_asyncio.py:20:from typing import Any, TypeVar
tests/test_asyncio.py:21:from unittest import mock
tests/test_asyncio.py:30:import pytest
tests/test_asyncio.py:32:import tenacity
tests/test_asyncio.py:33:from tenacity import (
tests/test_asynci
…[932 chars elided]…
 Retrying, retry
tests/test_tenacity.py:31:from tenacity._utils import override
tests/test_tenacity.py:32:from tenacity.retry import retry_all, retry_any
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)
[assistant] Imports are all present. I'll add the sync tests after `test_wait_arbitrary_sum`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tests/test_tenacity.py", "old_string": "        # Test it a few time since it's random\n        for _ in range(1000):\n            w = r.wait(make_retry_state(1, 5))\n            self.assertLess(w, 9)\n            self.assertGreaterEqual(w, 6)\n\n    def
…[907 chars elided]…
IsInstance(w, tenacity.wait_combine)\n        self.assertEqual(w(make_retry_state(1, 5)), 3.0)\n\n    def test_wait_combine_plain_callable_any_param_name(self) -> None:\n        def custom(state: RetryCallState) -> float:\n            return 2.0\n\n        w = tenacity.wait_combine(custom, tenacity.wait_fixed(1))\n        self.assertEqual(w(make_retry_state(1, 5)), 3.0)\n\n    def _assert_range("}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next, the async counterpart in `tests/test_asyncio.py`, which covers the `AsyncRetrying` path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tests/test_asyncio.py", "old_string": "        retrying = AsyncRetrying()\n        await retrying(_async_function, thing)\n        assert thing.counter == thing.count\n\n    @asynctest\n    async def test_stop_after_attempt(self) -> None:", "new_string":
…[317 chars elided]…
AsyncRetrying(\n                wait=wait,  # type: ignore[arg-type]\n                stop=stop_after_attempt(2),\n                sleep=sleep,\n            )\n            with self.assertRaises(RetryError):\n                await retrying(mock.AsyncMock(side_effect=ValueError))\n            sleep.assert_awaited_once_with(0)\n\n    @asynctest\n    async def test_stop_after_attempt(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Now I'll run the full suite and the reproduction script against the changed code.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I /tmp/repro_wait.py \"$PWD\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run reproduction script and full test suite"}
[tool_result] sync wait=None RAISED RetryError RetryError[<Future at 0x1014cec30 state=finished raised ValueError>]
sync wait=0 RAISED RetryError RetryError[<Future at 0x1014af470 state=finished raised ValueError>]
sync wait=sum([]) RAISED RetryError RetryError[<Future at 0x1017fc200 state=finished raised ValueError>]
callable + wait_fixed type -> wait_combine
callable + wait_fixed value -> 3.0
wait_combine named param -> 4.0
................s................................................................................................................... [ 74%]
..............................................                           [100%]
177 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] All 177 pass (173 original + 4 new). The repro's `RetryError` for the falsy cases is the expected result: the function fails twice and the retry limit is reached, with no `TypeError`. To confirm the new tests actually catch the regressions, I'll run them against the original source in a scratch copy.
[tool_use Bash] {"command": "rm -rf /tmp/verify-base && mkdir /tmp/verify-base && git archive HEAD | tar -x -C /tmp/verify-base && cp tests/test_tenacity.py tests/test_asyncio.py /tmp/verify-base/tests/ && PY=<work>/env-tenacity/bin/python; cd /tmp/verify-base && $PY -m pytest -q -p no:cacheprovider --color=no -k \"falsy or plain_callable or any_param_name\" 2>&1 | grep -E \"passed|failed|FAILED|Error\" | tail -12", "description": "Confirm new tests fail on original code"}
[tool_result] tenacity/wait.py:94: TypeError
            with self.assertRaises(RetryError):
>               r(mock.Mock(side_effect=ValueError))
E       TypeError: 'NoneType' object is not callable
tenacity/__init__.py:418: TypeError
E       TypeError: unsupported operand type(s) for +: 'function' and 'wait_fixed'
tests/test_tenacity.py:525: TypeError
FAILED tests/test_asyncio.py::TestAsyncio::test_wait_falsy_values_mean_no_wait
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_combine_plain_callable_any_param_name
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_falsy_values_mean_no_wait
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_plain_callable_sum
4 failed, 174 deselected in 0.15s
Shell cwd was reset to ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1
[assistant] All four new tests fail on the original code and pass with the fix. The previous wait fix in this repo shipped with a reno release note, so I'll add a matching one for these fixes.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-falsy-callable-combine-3c8e1d5f7a2b9046.yaml", "content": "---\nfixes:\n  - |\n    `wait=None`, `wait=0` and `wait=sum([])` mean \"no wait\" again, for both\n    `Retrying` and `AsyncRetrying`. They raised\n    ``TypeError: 'NoneType' object is not callable`` once a retry happened.\n  - |\n    Adding a plain callable to a wait strategy, as in\n    ``my_callable + wait_fixed(1)``, now builds a ``wait_combine`` that sums\n    both, instead of raising ``TypeError``.\n  - |\n    ``wait_combine`` passes the retry state to its strategies positionally, so\n    plain callables may name their parameter anything.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165328-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-falsy-callable-combine-3c8e1d5f7a2b9046.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "rm -rf /tmp/verify-base /tmp/repro_wait.py && git status --short && git diff -- tenacity/", "description": "Clean scratch files and review source diff"}
[tool_result]  M tenacity/__init__.py
 M tenacity/wait.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-falsy-callable-combine-3c8e1d5f7a2b9046.yaml
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 9ceaf16..2c2b1b6 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -261,7 +261,8 @@ class BaseRetrying(ABC):
     ) -> None:
         self.sleep = sleep
         self.stop = stop
-        self.wait = wait
+        # `None`, `0` and `sum([])` all mean "no w
…[1501 chars elided]…
 strategies."""
 
-    def __init__(self, *strategies: wait_base) -> None:
+    def __init__(self, *strategies: WaitBaseT) -> None:
         self.wait_funcs = strategies
 
     @override
     def __call__(self, retry_state: "RetryCallState") -> float:
-        return sum(x(retry_state=retry_state) for x in self.wait_funcs)
+        # Pass positionally so plain callables may name their parameter freely.
+        return sum(x(retry_state) for x in self.wait_funcs)
 
 
 class wait_chain(wait_base):
[assistant] All three regressions are fixed. The full suite passes: 177 passed, 1 skipped (the original 173 plus 4 new tests). I reproduced each failure first, and the new tests fail on the original code.

**What caused each one**
1. **`None` / `0` / `sum([])`**: commit e6ef84a removed the `if self.wait:` guard in both `_run_wait` methods. Its reasoning assumed `wait` is always a strategy object, which isn't true for these falsy values. The fix is in `BaseRetrying.__init__` (`tenacity/__init__.py`): any non-callable `wait` becomes `wait_none()`. The sync, async and tornado retriers all go through that con
…[798 chars elided]…
u don't want it.
- Nothing is committed.

**Things to check**
- **`wait_chain` has the same keyword call** (`wait_func(retry_state=retry_state)`), so a plain callable with another parameter name fails there too. I left it alone because you scoped the fix to `wait_combine`. It's a one-line change if you want it.
- **Lint and types are unverified**: mypy and ruff aren't installed in this environment, and the project's check is pytest. The repo runs strict mypy with `truthy-bool` and `redundant-expr` enabled, so `callable(wait)` in `__init__` might get flagged. Running mypy in CI would settle it.
