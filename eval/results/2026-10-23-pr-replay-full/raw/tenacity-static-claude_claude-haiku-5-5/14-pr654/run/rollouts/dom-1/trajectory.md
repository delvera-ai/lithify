# trajectory dom-1

final message:
`wait_exponential` no longer computes `exp_base ** n` once the exponential is past `max`. Results are unchanged, and the full suite passes. The changes are uncommitted in the worktree.

**The change** (`tenacity/wait.py`)
- A new `_is_past_max` helper checks in log space whether `multiplier * exp_base ** n` is above `max`. `__call__` returns `self.max` directly when it is, so the power is never computed for those attempts.
- The check only short-circuits when both existing exits of `__call__` would return `max`. That keeps the `OverflowError` path and the `min > max` edge exactly as before.
- The margin is `1e-9` in log space, so float rounding can't flip the answer. The only attempts that still compute the power are those whose exponential is within a relative 1e-9 of `max`.
- I first used a margin of a factor of e, which would have computed the power for attempts between `max` and `e × max`. I tightened it to meet the requirement as written.

**Tests and checks**
- Regression test `TestWaitConditions::test_exponential_does_not_compute_power_past_max`: it counts `__pow__` calls on a float subclass used as `exp_base`. It failed on the unfixed code (`[1] != []`) and passes now.
- Full suite via `run_tests.py`: exit 0, 168 passed, 1 skipped.
- `check_changed.py`: exit 0, 0 problems. ruff and mypy were not run (unavailable here), and PyYAML was not available, so the new reno note was not parsed.
- An ad hoc brute-force comparison of the old and new formulas over 938,520 parameter combinations (multipliers, `max`, `exp_base`, `min`, attempt numbers, int and float types) found 0 mismatches. That script lives in `/tmp/eqcheck`, not in the repo.
- Reno note added: `releasenotes/notes/wait-exponential-max-cap-63ca6607ff9e92aa.yaml` (under `fixes:`).

**Choices to review**
- `wait_random_exponential` inherits the fix. `wait_exponential_jitter` has its own copy of the power and is unchanged, since the task named only `wait_exponential`. It still computes the power past its cap.
- No docs change in `doc/source/index.rst`, because user-visible results are unchanged.

## events
[assistant] I'll start by reading the current `wait_exponential` code and the harness docs it points to.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"class wait_exponential\" -A 40 tenacity/wait.py && ls .lithify/harness/scripts/ .lithify/harness/skills/ && cat .lithify/memory.md 2>/dev/null | head -20; ls releasenotes/notes | tail -3", "description": "Inspect wait_exponential source and harness layout"}
[tool_result] 31f16b9 lithify: probe base
178:class wait_exponential(wait_base):
179-    """Wait strategy that applies exponential backoff.
180-
181-    It allows for a customized multiplier and an ability to restrict the
182-    upper and lower limits to some maximum and minimum value.
183-
184-    The intervals are fixed (i.e. there is no jitter), so this strategy is
185-    suitable for balancing retries against latency when a required resource is
186-    unavailable for an unknown duration, but *not* suit
…[2696 chars elided]…
ds(max)
279-        self.exp_base = exp_base
280-        self.jitter = _utils.to_seconds(jitter)
281-        self.min = _utils.to_seconds(min)
282-
283-    def __call__(self, retry_state: "RetryCallState") -> float:
.lithify/harness/scripts/:
check_changed.py
run_tests.py

.lithify/harness/skills/:
deprecate-parameter
tenacity-change-contract
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; grep -n \"wait_exponential\" -n tests/test_tenacity.py | head -30", "description": "Read tenacity change contract and existing wait tests"}
[tool_result] <persisted-output>
Output too large (30.5KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261023-212750-performance-wait-exponential-max-dom-1/6f01e8a5-29da-4df3-b59a-f58d2b8da578/tool-results/bsiv55j4q.txt

Preview (first 2KB):
---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, 
…[1272 chars elided]…
ository history and config. Check each item before finishing.

## 1. Code goes in the module that owns the concern
- `tenacity/_utils.py` — shared helpers (`find_ordinal`/`to_ordinal`, `get_callback_name`,
  `LoggerProtocol`, `MAX_WAIT`). The logging callbacks in `tenacity/before.py`,
  `tenacity/after.py`, `tenacity/before_sleep.py` call these helpers; fix the helper, not the
  callers.
- Strategies live in `tenacity/wait.py`, `tenacity/stop.py`, `tenacity/retry.py`; the
...
</persisted-output>
[tool_use Bash] {"command": "sed -n 1,200p .lithify/harness/skills/tenacity-change-contract/SKILL.md | tail -n +20 | head -150; echo ----; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ----; ls tests | head -30; grep -rn \"exp_base\\|OverflowError\" tests/*.py | head -20", "description": "Read rest of contract skill and find existing exponential tests"}
[tool_result] - `BaseRetrying` owns the loop once: `begin()` (start of every run), `_begin_iter`,
  `_post_retry_check_actions`, `_post_stop_check_actions` are shared by sync, async and
  tornado (`tenacity/tornadoweb.py`); `AsyncRetrying` and `TornadoRetrying` call
  `self.begin()` and do not override it. A fix in one of these shared methods needs no async
  copy — say so rather than editing `tenacity/asyncio/`.
- `AsyncRetrying` (`tenacity/asyncio/__init__.py`) re-implements `_run_retry`, `_run_wait`,
  `_r
…[11176 chars elided]…
gy classes (`retry.py`, `stop.py`, `wait.py`, `tenacity/asyncio/retry.py`):
  store constructor arguments as plain attributes and compute in `__call__`
  (`retry_if_exception_cause_type`, `stop_after_attempt`, `wait_fixed` do this). Never store a
  lambda or nested `def` built in `__init__`: it cannot be pickled
----
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
----
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "grep -n \"performance\\|efficiency\\|wait_exponential\" -A 12 .lithify/harness/skills/tenacity-change-contract/SKILL.md | sed -n 1,140p; echo ----; grep -n \"class TestWaitExp\\|wait_exponential(\" tests/test_tenacity.py | head; ls releasenotes/notes | wc -l", "description": "Read perf and wait_exponential guidance in contract skill"}
[tool_result] 3:description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, the `enabled` switch, which excepti
…[6592 chars elided]…
tyle:
335-  ```yaml
336-  ---
337-  fixes:
338-    - |
----
340:        r = Retrying(wait=tenacity.wait_exponential())
351:        r = Retrying(wait=tenacity.wait_exponential(max=40))
363:        r = Retrying(wait=tenacity.wait_exponential(min=20))
375:        r = Retrying(wait=tenacity.wait_exponential(max=50, multiplier=1))
387:        r = Retrying(wait=tenacity.wait_exponential(min=20, multiplier=2))
404:                r = Retrying(wait=tenacity.wait_exponential(min=min_, max=max_))
      50
[assistant] The contract skill flags two things that constrain the fix: the `OverflowError` exit returns `max` without the `min` clamp, and `wait_exponential_jitter` has its own copy of the power. Next I'll check the test class layout, the imports in `wait.py`, and how `run_tests.py` is invoked.
[tool_use Bash] {"command": "sed -n 1,20p tenacity/wait.py; echo ----; grep -n \"class TestWaitConditions\" -A 12 tests/test_tenacity.py; grep -n \"def test_wait_exponential\" tests/test_tenacity.py | head -3; sed -n 1,30p tests/test_tenacity.py | grep -n import; echo ----; sed -n 1,40p .lithify/harness/scripts/run_tests.py", "description": "Read wait.py imports, test class layout, and run_tests usage"}
[tool_result] # Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS O
…[2251 chars elided]…
 node id alone with
          --timeout 60; if it is a test you wrote, make its retry loop bounded
          (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
[assistant] Before writing the regression test I need the existing `wait_exponential` tests and the project python path.
[tool_use Bash] {"command": "sed -n 396,430p tests/test_tenacity.py; ls <work>/env-tenacity/bin/python 2>&1; ls .lithify/; grep -n \"to_seconds\" -A8 tenacity/_utils.py | head -15", "description": "Read exponential tests and locate project python"}
[tool_result]         self.assertEqual(r.wait(make_retry_state(20, 0)), 1048576)

    def test_exponential_with_min_wait_andmax__wait(self) -> None:
        for min_, max_ in (
            (10, 100),
            (datetime.timedelta(seconds=10), datetime.timedelta(seconds=100)),
        ):
            with self.subTest():
                r = Retrying(wait=tenacity.wait_exponential(min=min_, max=max_))
                self.assertEqual(r.wait(make_retry_state(1, 0)), 10)
                self.assertEqual(r.wait(m
…[1246 chars elided]…
e(
<work>/env-tenacity/bin/python
harness
library
state.json
84:def to_seconds(time_unit: time_unit_type) -> float:
85-    return float(
86-        time_unit.total_seconds() if isinstance(time_unit, timedelta) else time_unit
87-    )
88-
89-
90-def is_coroutine_callable(call: typing.Callable[..., typing.Any]) -> bool:
91-    if inspect.isclass(call):
92-        return False
[assistant] `to_seconds` always returns a float, so `self.max` is a float on every path. I'll add the regression test first. It counts calls to `__pow__` on a float subclass used as `exp_base`, which directly checks the stated requirement that the power is not computed past the cap.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tests/test_tenacity.py", "old_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)\n\n    def test_legacy_explicit_wait_type(self) -> None:", "new_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)
…[158 chars elided]…
           def __pow__(self, other: typing.Any) -> typing.Any:\n                pow_calls.append(1)\n                return super().__pow__(other)\n\n        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=CountingBase(2)))\n        self.assertEqual(r.wait(make_retry_state(100, 0)), 40)\n        self.assertEqual(pow_calls, [])\n\n    def test_legacy_explicit_wait_type(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_exponential_does_not_compute_power_past_max\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -n 30 /tmp/red.txt", "description": "Run new regression test against unfixed code"}
[tool_result] exit=1
self = <tests.test_tenacity.TestWaitConditions testMethod=test_exponential_does_not_compute_power_past_max>

    def test_exponential_does_not_compute_power_past_max(self) -> None:
        pow_calls: typing.List[int] = []
    
        class CountingBase(float):
            def __pow__(self, other: typing.Any) -> typing.Any:
                pow_calls.append(1)
                return super().__pow__(other)
    
        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=CountingBas
…[172 chars elided]…
   First list contains 1 additional elements.
E       First extra element 0:
E       1
E       
E       - [1]
E       ?  -
E       
E       + []

tests/test_tenacity.py:426: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_does_not_compute_power_past_max
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The test fails on the unfixed code for the stated reason: the power is computed once past the cap (`[1] != []`). Now the fix. I'm putting the cap check in a helper that runs in log space, and it only short-circuits when both old exits would return `max`, so results don't change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py", "old_string": "    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowErro
…[919 chars elided]…
oat:\n        if self._is_past_max(retry_state.attempt_number - 1):\n            return self.max\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowError:\n            return self.max\n        return max(max(0, self.min), min(result, self.max))\n\n\nclass wait_random_exponential(wait_exponential):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py", "old_string": "import abc\nimport random", "new_string": "import abc\nimport math\nimport random"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py has been updated successfully.
[assistant] Next, the regression test should go green. Then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_exponential_does_not_compute_power_past_max\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -n 4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"full exit=$?\"; tail -n 8 /tmp/full.txt", "description": "Run regression test green, then full test suite"}
[tool_result] exit=0

============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
full exit=0
tests/test_tornado.py::TestTornado::test_retry PASSED                    [ 98%]
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 168 passed, 1 skipped, 12 subtests passed in 2.85s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Regression test is green and the full suite passes (168 passed, 1 skipped). The contract skill says results must match the old code exactly, including the `min > max` and `OverflowError` exits, so I'll brute-force the old and new formulas against each other over a parameter grid.
[tool_use Bash] {"command": "mkdir -p /tmp/eqcheck && cat > /tmp/eqcheck/eq.py <<'EOF'\nimport sys, types, math\nsys.path.insert(0, \"~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1\")\nfrom tenacity.wait import wait_exponential\nfrom tenacity._utils import MAX_WAIT\n\ndef old(m, mx, b, mn, n):\n    try:\n        exp = b ** (n - 1)\n        result = m * 
…[1006 chars elided]…
  bad.append((m, mx, b, mn, n, a, c))\nprint(\"checked\", checked, \"mismatches\", len(bad))\nfor x in bad[:10]: print(x)\nEOF\n<work>/env-tenacity/bin/python -I /tmp/eqcheck/eq.py 2>&1 | tail -n 15", "description": "Brute-force compare old and new wait_exponential formulas"}
[tool_result] checked 938520 mismatches 455114
(0, 40, 2, 10, 1, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 2, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 3, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 4, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 5, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 6, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 7, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 8, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 9, ('ok', 'int', 10), ('ok', 'float', 10.0))
(0, 40, 2, 10, 10, ('ok', 'int', 10), ('ok', 'float', 10.0))
[assistant] Most of those mismatches come from my harness, not the fix: `wait_exponential` converts `min` and `max` with `to_seconds` (always float), but my reference function used the raw values. I'll make the reference convert the same way and rerun.
[tool_use Bash] {"command": "cd /tmp/eqcheck && sed -i 's/return mx$/return mx/; s/a = run(lambda: old(m, float(mx) if False else mx, b, mn, n))/a = run(lambda: old(m, float(mx), b, float(mn), n))/' eq.py && <work>/env-tenacity/bin/python -I /tmp/eqcheck/eq.py 2>&1 | tail -n 15", "description": "Rerun equivalence check with float-converted bounds"}
[tool_result ERROR] Exit code 1
sed: 1: "eq.py
": invalid command code e
[tool_use Bash] {"command": "cd /tmp/eqcheck && sed -i 's/a = run(lambda: old(m, float(mx) if False else mx, b, mn, n))/a = run(lambda: old(m, float(mx), b, float(mn), n))/' eq.py && grep -n \"a = run\" eq.py && <work>/env-tenacity/bin/python -I /tmp/eqcheck/eq.py 2>&1 | tail -n 15", "description": "Fix reference bounds conversion and rerun comparison"}
[tool_result ERROR] Exit code 1
sed: 1: "eq.py
": invalid command code e
[assistant] The `sed` route keeps failing on the quoting, so I'll make the edit with the Edit tool.
[tool_use Edit] {"replace_all": false, "file_path": "/tmp/eqcheck/eq.py", "old_string": "          a = run(lambda: old(m, float(mx) if False else mx, b, mn, n))", "new_string": "          a = run(lambda: old(m, float(mx), b, float(mn), n))"}
[tool_result] The file /tmp/eqcheck/eq.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -I /tmp/eqcheck/eq.py > /tmp/eqcheck/out.txt 2>&1; echo \"exit=$?\"; tail -n 12 /tmp/eqcheck/out.txt", "description": "Rerun equivalence check and capture output"}
[tool_result] exit=0
checked 938520 mismatches 0
[assistant] Zero mismatches across 938,520 combinations, including `min > max`, the `OverflowError` paths, and int vs float results. Next is the reno note the contract requires for a user-noticeable fix, followed by the stdlib lint substitute.
[tool_use Bash] {"command": "h=$(openssl rand -hex 8) && echo \"$h\" && printf '%s\\n' '---' 'fixes:' '  - |' '    `wait_exponential` (and `wait_random_exponential`, which inherits it) no longer' '    computes `exp_base ** attempt` once the exponential is past `max`. Long-running' '    retries no longer slow down as the attempt number grows; the returned wait is' '    unchanged.' > releasenotes/notes/wait-exponential-max-cap-$h.yaml && cat releasenotes/notes/wait-exponential-max-cap-$h.yaml && echo \"$h\" > /tmp/eqcheck/hex.txt", "description": "Create reno release note with random hex suffix"}
[tool_result] 63ca6607ff9e92aa
---
fixes:
  - |
    `wait_exponential` (and `wait_random_exponential`, which inherits it) no longer
    computes `exp_base ** attempt` once the exponential is past `max`. Long-running
    retries no longer slow down as the attempt number grows; the returned wait is
    unchanged.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check exit=$?\"; tail -n 20 /tmp/check.txt; git status --short; git diff --stat", "description": "Run stdlib lint check and show changed files"}
[tool_result] check exit=0
changed: releasenotes/notes/wait-exponential-max-cap-63ca6607ff9e92aa.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-max-cap-63ca6607ff9e92aa.yaml
 tenacity/wait.py       | 15 +++++++++++++++
 tests/test_tenacity.py | 12 ++++++++++++
 2 files changed, 27 insertions(+)
[assistant] The stdlib check passes and only the three intended files changed. Before finishing I rechecked the margin I chose. It's `+ 1` in log space, which means a factor of e. That means attempts whose exponential is between `max` and `e × max` still compute the power, which doesn't meet the requirement that the power is not computed once the value would exceed `max`. A margin of `1e-9` in log space is still far above float error for these magnitudes, and it narrows the computed band to values within a relative 1e-9 of `max`. I'll tighten it and re-verify.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py", "old_string": "        # True when multiplier * exp_base ** exponent is certainly above max, so\n        # the power need not be computed. Checked in log space with a margin of 1\n        # (a factor of e), so float rounding cannot flip
…[738 chars elided]…
ies when max >= max(0,\n        # min): then both exits of __call__ return max.\n        if not (self.exp_base > 1 and self.multiplier > 0):\n            return False\n        if not (0 < self.max and self.max >= max(0, self.min)):\n            return False\n        log_result = exponent * math.log(self.exp_base) + math.log(self.multiplier)\n        return log_result >= math.log(self.max) + 1e-9"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/dom-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I /tmp/eqcheck/eq.py > /tmp/eqcheck/out2.txt 2>&1; echo \"eq exit=$?\"; tail -n 3 /tmp/eqcheck/out2.txt; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_exponential_does_not_compute_power_past_max\" > /tmp/green2.txt 2>&1; echo \"target exit=$?\"; $PY .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; echo \"full exit=$?\"; tail -n 4 /tmp/full2.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"check exit=$?\"; tail -n 2 /tmp/check2.txt", "description": "Re-verify equivalence, target test, full suite, and lint check"}
[tool_result] eq exit=0
checked 938520 mismatches 0
target exit=0
full exit=0

============== 168 passed, 1 skipped, 12 subtests passed in 1.84s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
check exit=0
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] `wait_exponential` no longer computes `exp_base ** n` once the exponential is past `max`. Results are unchanged, and the full suite passes. The changes are uncommitted in the worktree.

**The change** (`tenacity/wait.py`)
- A new `_is_past_max` helper checks in log space whether `multiplier * exp_base ** n` is above `max`. `__call__` returns `self.max` directly when it is, so the power is never computed for those attempts.
- The check only short-circuits when both existing exits of `__call__` would return `max`. That keeps the `OverflowError` path and the `min > max` edge exactly as before.
- 
…[890 chars elided]…
0 parameter combinations (multipliers, `max`, `exp_base`, `min`, attempt numbers, int and float types) found 0 mismatches. That script lives in `/tmp/eqcheck`, not in the repo.
- Reno note added: `releasenotes/notes/wait-exponential-max-cap-63ca6607ff9e92aa.yaml` (under `fixes:`).

**Choices to review**
- `wait_random_exponential` inherits the fix. `wait_exponential_jitter` has its own copy of the power and is unchanged, since the task named only `wait_exponential`. It still computes the power past its cap.
- No docs change in `doc/source/index.rst`, because user-visible results are unchanged.
