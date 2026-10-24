# trajectory base-1

final message:
All three regressions are fixed. The project's test command passes (176 passed, 1 skipped), and the three new tests fail on the base commit and pass with the fix.

1. **No-wait values** (`tenacity/__init__.py`): `BaseRetrying.__init__` now stores `wait_none()` when `wait` is `None`, `0`, or `sum([])` (which is the int 0). Since `AsyncRetrying` goes through the same constructor, it's covered too. I confirmed sync and async retry loops run with all three values.
2. **Callable + strategy** (`tenacity/wait.py`): `wait_base.__radd__` now returns `wait_combine(other, self)` when the left operand is callable, so `my_callable + wait_fixed(1)` sums both in the original order. The old code returned `NotImplemented` for anything except 0.
3. **Positional state** (`tenacity/wait.py`): `wait_combine` calls each strategy as `x(retry_state)`, so plain callables can use any parameter name.

I also added:
- Three tests in `tests/test_tenacity.py`, placed beside the existing wait-sum tests. No existing tests were changed.
- A reno note in `releasenotes/notes/`, following the repo's convention for fixes.

Decisions for you to check:
- I left the `wait` type annotations on `BaseRetrying` alone, so `Retrying(wait=None)` may still be flagged by type checkers. Widening the signature is a public API change, so I didn't make it.
- `wait_chain` has the same keyword call (`wait_func(retry_state=retry_state)`), so a plain callable with a non-`retry_state` parameter name will fail there too. You scoped the fix to `wait_combine`, so I didn't touch it. It's a one-line change if you want it.

Ruff and mypy aren't installed in this environment, so I didn't run them. The new test line is wrapped to the project's line length by hand.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls && cat tenacity/wait.py && grep -n \"wait\" tenacity/__init__.py | head -80", "description": "Inspect repo state and wait module"}
[tool_result] eabed99 lithify: probe base
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
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to i
…[11864 chars elided]…
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
[tool_use Bash] {"command": "sed -n 240,310p tenacity/__init__.py && sed -n 410,425p tenacity/__init__.py && grep -n \"_first_set\\|_unset\" -A6 tenacity/__init__.py | head -40 && grep -rn \"wait_combine\\|__radd__\\|wait=0\\|wait=None\\|sum(\" tests | head -30; cat AGENTS.md | head -60", "description": "Read Retrying init and related tests"}
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
   
…[5885 chars elided]…
it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[tool_use Bash] {"command": "sed -n 430,510p tests/test_tenacity.py; grep -rn \"wait=None\\|wait=0\\|wait is None\\|sum(\\[\\])\\|__radd__\" tests tenacity doc releasenotes | head; git log --oneline -S\"__radd__\" -- tenacity | head; git log --oneline -S\"wait_none()\" -- tenacity | head -3", "description": "Look at wait tests and history for radd/wait_none"}
[tool_result]     def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

    def test_wait_func(self) -> None:
        def wait_func(retry_state: RetryCallState) -> typing.Any:
            return retry_state.attempt_number * retry_state.seconds_since_start  # type: ignore[operator]

        r = Retrying(wait=wait_func)
        self.assertEqual(r.wait(make_retry_state(1, 5)), 5)
        self.assertEqual(r.wait(make_retry_state(2, 11)), 22)
      
…[2448 chars elided]…
f _assert_range(self, wait: float, min_: float, max_: float) -> None:
        self.assertLess(wait, max_)
tenacity/wait.py:40:    def __radd__(self, other: int) -> "wait_base":
releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml:4:    `wait_base.__radd__` is now annotated as taking the `int` seed that
9a1b4b7 Implement '+' operator for wait strategies
21137e7 Add async strategies (#451)
b49eb37 chore(typing): improve typing of WrappedFn (#390)
d442271 Do not package tests with tenacity (#308)
[tool_use Bash] {"command": "cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml; sed -n 1,80p tests/test_tenacity.py | grep -n \"import\\|def make_retry\" ; grep -n \"wait\" tenacity/asyncio/__init__.py | head -20; ls releasenotes/notes | tail -5; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Read release note, async wait code, and run tests"}
[tool_result] ---
fixes:
  - |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typin
…[1701 chars elided]…
o-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.87s
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport tenacity\nfrom tenacity import Retrying, wait_fixed, wait_combine\ndef f(s): return 1\nfor w in [None, 0, sum([])]:\n    try: r=Retrying(wait=w); print('ok', w, r.wait)\n    except Exception as e: print('ERR', 
…[82 chars elided]…
', e)\ndef g(state, extra=None): return 2\nc = wait_combine(lambda rs: 1, wait_fixed(1))\nclass X:\n    pass\ndef h(*, rs): return 1\ntry: print(wait_combine(h)(retry_state=None))\nexcept Exception as e: print('ERR combine', e)\ntry: print(wait_combine(lambda foo: 3)(retry_state=None))\nexcept Exception as e: print('ERR combine2', e)\n\"", "description": "Reproduce the three reported regressions"}
[tool_result] ok None None
ok 0 0
ok 0 0
ERR add unsupported operand type(s) for +: 'function' and 'wait_fixed'
ERR combine h() got an unexpected keyword argument 'retry_state'
ERR combine2 <lambda>() got an unexpected keyword argument 'retry_state'
[assistant] Reproduced all three. Now the fixes: normalize "no wait" values in `BaseRetrying.__init__`, make `__radd__` accept plain callables, and pass the state positionally in `wait_combine`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __radd__(self, other: int) -> \"wait_base\":\n        # `sum()` seeds its accumulator with the int 0, so tolerate that to\n        # make summing waits work. Any other left operand is a `wait_base`,\n        # wh
…[218 chars elided]…
 seeds its accumulator with the int 0, so tolerate that to\n        # make summing waits work.\n        if other == 0:\n            return self\n        # A plain callable on the left has no `__add__`, so Python falls back\n        # to this method. Keep the operands in their original order.\n        if callable(other):\n            return wait_combine(other, self)\n        return NotImplemented"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/wait.py", "old_string": "    def __init__(self, *strategies: wait_base) -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        return sum(x(retry_state=retry_state) for x in self.wait_funcs)", "new_string": "    def __init__(self, *strategies: \"WaitBaseT\") -> None:\n        self.wait_funcs = strategies\n\n    @override\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        # Pass the state positionally so plain callables may name it anything.\n        return sum(x(retry_state) for x in self.wait_funcs)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/__init__.py", "old_string": "        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry", "new_string": "        self.sleep = sleep\n        self.stop = stop\n        # `None`, `0` and `sum([])` (which is the int 0) all mean \"no wait\".\n        self.wait = wait_none() if wait is None or wait == 0 else wait\n        self.retry = retry"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll re-run the reproduction, check the async path, and run the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport asyncio\nfrom tenacity import Retrying, AsyncRetrying, wait_fixed, wait_combine, stop_after_attempt, retry_if_exception_type\nfrom tenacity.asyncio import AsyncRetrying as AR\nfrom tenacity.wait import wait_bas
…[1194 chars elided]…
]<2: raise ValueError\n    return 'done'\nasync def main():\n    for w in [None, 0, sum([])]:\n        n['c']=0\n        print('async run', w, await AsyncRetrying(wait=w, stop=stop_after_attempt(3), retry=retry_if_exception_type(ValueError))(fn))\nasyncio.run(main())\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Verify fixes sync, async, and run test suite"}
[tool_result] sync None 0.0
async None ok
done
sync 0 0.0
async 0 ok
done
sync 0 0.0
async 0 ok
done
add 2.0 wait_combine
sum 3.0
radd order 11.0
combine named 4.0
async run None done
async run 0 done
async run 0 done
...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.83s
[assistant] The fixes work for sync and async, and the existing suite still passes. I'll add regression tests next to the existing wait-sum tests, since none cover these three cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tests/test_tenacity.py", "old_string": "    def _assert_range(self, wait: float, min_: float, max_: float) -> None:", "new_string": "    def test_wait_no_wait_values(self) -> None:\n        for no_wait in (None, 0, sum([])):\n            r = Retrying(wai
…[455 chars elided]…
n\n    def test_wait_combine_plain_callable_any_param_name(self) -> None:\n        def plain(state: RetryCallState) -> float:\n            return 4.0\n\n        r = Retrying(wait=tenacity.wait_combine(plain, tenacity.wait_fixed(1)))  # type: ignore[arg-type]\n        self.assertEqual(r.wait(make_retry_state(1, 5)), 5)\n\n    def _assert_range(self, wait: float, min_: float, max_: float) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git -c advice.detachedHead=false show HEAD:tenacity/wait.py > /dev/null && cp tenacity/wait.py /tmp/wait_new.py && cp tenacity/__init__.p
…[195 chars elided]…
2>&1 | tail -4; cp /tmp/wait_new.py tenacity/wait.py && cp /tmp/init_new.py tenacity/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; (ruff --version && ruff check tenacity tests && ruff format --check tenacity tests) 2>&1 | tail -4; (mypy --version && mypy tenacity) 2>&1 | tail -3; git status --short", "description": "Run tests, confirm new tests fail on base, lint"}
[tool_result] ...............s.................................................................................................................... [ 74%]
.............................................                            [100%]
176 passed, 1 skipped, 12 subtests passed in 1.86s
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_combine_plain_callable_any_param_name
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_no_wait_values
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_plain_callable_plus_strategy
3 failed, 135 deselected in 0.06s
176 passed, 1 skipped, 12 subtests passed in 1.85s
(eval):1: command not found: ruff
(eval):1: command not found: mypy
 M tenacity/__init__.py
 M tenacity/wait.py
 M tests/test_tenacity.py
[This command modified 2 files you've previously read: tenacity/__init__.py, tenacity/wait.py. Call Read before editing.]
[assistant] The three new tests fail on the base code and pass with the fix. One test line is over the project's line length, so I'll wrap it and then review the diff.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tests/test_tenacity.py", "old_string": "        r = Retrying(wait=tenacity.wait_combine(plain, tenacity.wait_fixed(1)))  # type: ignore[arg-type]", "new_string": "        r = Retrying(\n            wait=tenacity.wait_combine(plain, tenacity.wait_fixed(1))  # type: ignore[arg-type]\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff -- tenacity; git status --short", "description": "Rerun tests and show the source diff"}
[tool_result] 176 passed, 1 skipped, 12 subtests passed in 1.87s
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 9ceaf16..87798ea 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -261,7 +261,8 @@ class BaseRetrying(ABC):
     ) -> None:
         self.sleep = sleep
         self.stop = stop
-        self.wait = wait
+        # `None`, `0` and `sum([])` (which is the int 0) all mean "no wait".
+        self.wait = wait_none() if wait is None or wait == 0 else wait
         self.ret
…[1347 chars elided]…
ne:
+    def __init__(self, *strategies: "WaitBaseT") -> None:
         self.wait_funcs = strategies
 
     @override
     def __call__(self, retry_state: "RetryCallState") -> float:
-        return sum(x(retry_state=retry_state) for x in self.wait_funcs)
+        # Pass the state positionally so plain callables may name it anything.
+        return sum(x(retry_state) for x in self.wait_funcs)
 
 
 class wait_chain(wait_base):
 M tenacity/__init__.py
 M tenacity/wait.py
 M tests/test_tenacity.py
[assistant] The diff is limited to the three fixes and their tests. This repo records fixes in reno release notes, so I'll add one to match.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-no-wait-and-callable-add-4c2e9a7d1f083b65.yaml", "content": "---\nfixes:\n  - |\n    `wait=None`, `wait=0` and `wait=sum([])` mean \"no wait\" again. They\n    raised `TypeError: 'NoneType' object is not callable` when a retry\n    happened, for both `Retrying` and `AsyncRetrying`.\n  - |\n    Adding a plain callable to a wait strategy, such as\n    `my_callable + wait_fixed(1)`, builds a `wait_combine` that sums both\n    again, instead of raising `TypeError`.\n  - |\n    `wait_combine` passes the retry state to its strategies positionally, so\n    plain callables may use any parameter name.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-fd67065479be/20261023-163152-three-regressions-that-only-appe/base-1/releasenotes/notes/wait-no-wait-and-callable-add-4c2e9a7d1f083b65.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git status --short", "description": "Final test run and status check"}
[tool_result] 176 passed, 1 skipped, 12 subtests passed in 1.88s
 M tenacity/__init__.py
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-no-wait-and-callable-add-4c2e9a7d1f083b65.yaml
[assistant] All three regressions are fixed. The project's test command passes (176 passed, 1 skipped), and the three new tests fail on the base commit and pass with the fix.

1. **No-wait values** (`tenacity/__init__.py`): `BaseRetrying.__init__` now stores `wait_none()` when `wait` is `None`, `0`, or `sum([])` (which is the int 0). Since `AsyncRetrying` goes through the same constructor, it's covered too. I confirmed sync and async retry loops run with all three values.
2. **Callable + strategy** (`tenacity/wait.py`): `wait_base.__radd__` now returns `wait_combine(other, self)` when the left operand is 
…[528 chars elided]…
ck:
- I left the `wait` type annotations on `BaseRetrying` alone, so `Retrying(wait=None)` may still be flagged by type checkers. Widening the signature is a public API change, so I didn't make it.
- `wait_chain` has the same keyword call (`wait_func(retry_state=retry_state)`), so a plain callable with a non-`retry_state` parameter name will fail there too. You scoped the fix to `wait_combine`, so I didn't touch it. It's a one-line change if you want it.

Ruff and mypy aren't installed in this environment, so I didn't run them. The new test line is wrapped to the project's line length by hand.
