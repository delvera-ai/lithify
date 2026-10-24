# trajectory base-1

final message:
`wait_exponential` now returns the capped wait instead of raising `ValueError: math domain error` for `multiplier=1e300, max=1e-100` and for `multiplier=float("inf")`. The full suite passes, and the changes are uncommitted in the worktree.

**Cause:** the short-circuit that skips the power calculation once the cap is reached calls `math.log(max / multiplier, exp_base)`. When `max / multiplier` underflows to 0.0 (or `multiplier` is infinite), `math.log(0.0)` raises.

**Fix (`tenacity/wait.py`):** if `max / multiplier == 0`, the cap is already below the first term, so the short-circuit applies. Otherwise the `math.log` comparison is unchanged. Only inputs that used to raise take the new branch, so ordinary results are identical.

**Changes:**
- `tests/test_tenacity.py`: two regression tests, one per trigger. I ran them against the unfixed code first and both failed with the reported `ValueError`.
- `tenacity/wait.py`: the guard above, with a short comment.
- `releasenotes/notes/wait-exponential-underflow-24362740e3ef10d9.yaml`: a `fixes:` note, which the tenacity contract requires for user-visible fixes.

**Verification:**
- New tests: 2 passed after the fix.
- Full suite (`run_tests.py`): exit 0, 172 passed, 1 skipped.
- `check_changed.py`: PASS, 0 problems.
- Not run: ruff and mypy, which aren't available here.
- Skipped: no user-docs change, since the fix doesn't alter documented usage.

**Choices to review:**
- The new branch returns `max(max(0, min), max)`, the same exit as the existing cap short-circuit. The `OverflowError` path returns `max` without the `min` clamp. The two differ only when `min > max`.
- `wait_exponential_jitter` has its own copy of the arithmetic, but it has no `math.log` path. I probed it with both inputs and it returns the cap, so it needed no change.

## events
[tool_use Bash] {"command": "grep -n \"class wait_exponential\" -A 40 tenacity/wait.py && cat .lithify/harness/memory.md 2>/dev/null | head -20; ls .lithify/harness/scripts/", "description": "Show wait_exponential implementation and harness files"}
[tool_result] 179:class wait_exponential(wait_base):
180-    """Wait strategy that applies exponential backoff.
181-
182-    It allows for a customized multiplier and an ability to restrict the
183-    upper and lower limits to some maximum and minimum value.
184-
185-    The intervals are fixed (i.e. there is no jitter), so this strategy is
186-    suitable for balancing retries against latency when a required resource is
187-    unavailable for an unknown duration, but *not* suitable for resolving
188-    c
…[2544 chars elided]…
max = _utils.to_seconds(max)
289-        self.exp_base = exp_base
290-        self.jitter = _utils.to_seconds(jitter)
291-        self.min = _utils.to_seconds(min)
292-
293-    def __call__(self, retry_state: "RetryCallState") -> float:
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
check_changed.py
run_tests.py
[tool_use Bash] {"command": "S=.lithify/harness/skills/tenacity-change-contract/SKILL.md && wc -c $S && grep -n '^## ' $S && ls releasenotes/notes | tail -5 && grep -n \"exponential\" tests/test_tenacity.py | head -40", "description": "List skill sections, release notes, and exponential tests"}
[tool_result]    29888 .lithify/harness/skills/tenacity-change-contract/SKILL.md
10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Re
…[2719 chars elided]…
acity.wait_exponential_jitter(
655:    def test_wait_exponential_jitter_multiplier(self) -> None:
656:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
662:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
664:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
668:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
670:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
[tool_use Bash] {"command": "S=.lithify/harness/skills/tenacity-change-contract/SKILL.md && sed -n '229,251p;321,380p' $S && sed -n '339,425p' tests/test_tenacity.py && cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml && cat .lithify/harness/scripts/run_tests.py | head -30", "description": "Read skill sections, existing tests, and a sample release note"}
[tool_result] ## 1b4. Exponential wait arithmetic (`tenacity/wait.py`)
Verified in `tenacity/wait.py`, `tenacity/_utils.py`, `tests/test_tenacity.py`.
- Exponential classes and where the power `self.exp_base ** (attempt_number - 1)` lives:
  `wait_exponential.__call__`; `wait_random_exponential` has no power of its own (it calls
  `super().__call__` and draws `random.uniform(self.min, high)`), so a change to
  `wait_exponential` covers it; `wait_exponential_jitter.__call__` has its OWN copy (adds
  `jitter`, 
…[10858 chars elided]…
s, ...)
    124   TIMEOUT: process group killed; `HUNG IN: <node id>` names the test.
          Do not re-run the suite unchanged. Run that node id alone with
          --timeout 60; if it is a test you wrote, make its retry loop bounded
          (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
[tool_use Bash] {"command": "sed -n 1,20p tests/test_tenacity.py && grep -n \"^import\\|^from\" tests/test_tenacity.py", "description": "Check test module imports"}
[tool_result] # Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[102 chars elided]…
d
# limitations under the License.
import contextlib
import datetime
import logging
import pickle
import re
16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
24:from fractions import Fraction
25:from unittest import mock
27:import pytest
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
[assistant] Before fixing, I'll write the two regression tests (one per trigger) and confirm they fail for the reported reason.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-124648-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py", "old_string": "    def test_legacy_explicit_wait_type(self) -> None:", "new_string": "    def test_exponential_with_max_below_multiplier_underflow(self) -> None:\n        # max / multiplier underflows to 0.0; the cap must still b
…[235 chars elided]…
  self.assertEqual(r.wait(make_retry_state(50, 0)), 1e-100)\n\n    def test_exponential_with_infinite_multiplier(self) -> None:\n        r = Retrying(wait=tenacity.wait_exponential(multiplier=float(\"inf\"), max=40))\n        self.assertEqual(r.wait(make_retry_state(1, 0)), 40)\n        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_legacy_explicit_wait_type(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-124648-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_exponential_with_max_below_multiplier_underflow tests/test_tenacity.py::TestWaitConditions::test_exponential_with_infinite_multiplier > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
>           and exponent > math.log(self.max / self.multiplier, self.exp_base)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ):
E       ValueError: math domain error

tenacity/wait.py:211: ValueError
_________ TestWaitConditions.test_exponential_with_infinite_multiplier _________

self = <tests.test_tenacity.TestWaitConditions testMethod=test_exponential_with_infinite_multiplier>

    def test_exponential_with_infinite_multiplier(self) -> None:
   
…[883 chars elided]…
^^^^^^^^
        ):
E       ValueError: math domain error

tenacity/wait.py:211: ValueError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_with_max_below_multiplier_underflow
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_with_infinite_multiplier
============================== 2 failed in 0.08s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Both tests fail with the reported `ValueError: math domain error` from `math.log(0.0)`. Now the fix: when `max / multiplier` underflows to 0.0, the cap is already below the first term (`multiplier * exp_base**0 = multiplier > max`), so the short-circuit should apply.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-124648-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py", "old_string": "            and math.isfinite(self.max)\n            and exponent > math.log(self.max / self.multiplier, self.exp_base)\n        ):\n            return max(max(0, self.min), self.max)\n        try:\n            exp = sel
…[461 chars elided]…
ultiplier == 0\n                or exponent > math.log(self.max / self.multiplier, self.exp_base)\n            )\n        ):\n            return max(max(0, self.min), self.max)\n        try:\n            exp = self.exp_base**exponent\n            result = self.multiplier * exp\n        except OverflowError:\n            return self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-124648-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_exponential_with_max_below_multiplier_underflow tests/test_tenacity.py::TestWaitConditions::test_exponential_with_infinite_multiplier > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/green.txt; <work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt", "description": "Run new tests green, then the full suite"}
[tool_result] exit=0
tests/test_tenacity.py::TestWaitConditions::test_exponential_with_infinite_multiplier PASSED [100%]

============================== 2 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 172 passed, 1 skipped, 12 subtests passed in 1.84s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Full suite is green (172 passed, 1 skipped). The skill requires a reno note for user-visible fixes, so I'll add one, then run the checker.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8) && echo \"$H\" && printf '%s\\n' '---' 'fixes:' '  - |' '    ``wait_exponential`` no longer raises ``ValueError: math domain error`` when' '    ``multiplier`` is infinite or ``max / multiplier`` underflows to zero (for' '    example ``wait_exponential(multiplier=1e300, max=1e-100)``). It now returns' '    the capped wait time, as it does for other values above
…[86 chars elided]…
otes/notes/wait-exponential-underflow-$H.yaml && <work>/env-tenacity/bin/python .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt; git status --short", "description": "Add reno release note and run changed-file checks"}
[tool_result] 24362740e3ef10d9
---
fixes:
  - |
    ``wait_exponential`` no longer raises ``ValueError: math domain error`` when
    ``multiplier`` is infinite or ``max / multiplier`` underflows to zero (for
    example ``wait_exponential(multiplier=1e300, max=1e-100)``). It now returns
    the capped wait time, as it does for other values above the maximum.
exit=0
changed: releasenotes/notes/wait-exponential-underflow-24362740e3ef10d9.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-underflow-24362740e3ef10d9.yaml
[assistant] Checks pass. The skill says to name whether the sibling `wait_exponential_jitter` has the same logic, so I'll check it.
[tool_use Bash] {"command": "sed -n '/class wait_exponential_jitter/,/^class /p' tenacity/wait.py | sed -n '/def __call__/,/return/p' && <work>/env-tenacity/bin/python -c \"\nimport tenacity\nfrom tenacity import Retrying\nfor kw in [dict(multiplier=1e300, max=1e-100), dict(multiplier=float('inf'), max=40)]:\n    try:\n        print('jitter', kw, Retrying(wait=tenacity.wait_exponential_jitter(jitter=0, **kw)).wait(__import__('tests.test_tenacity', fromlist=['x']).make_retry_state(1,0)))\n    except Exception as e: print('jitter', kw, type(e).__name__, e)\n\" 2>&1 | tail -3", "description": "Inspect and probe wait_exponential_jitter for the same bug"}
[tool_result]     def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.multiplier * exp + jitter
        except OverflowError:
            result = self.max
        return max(max(0, self.min), min(result, self.max))
jitter {'multiplier': 1e+300, 'max': 1e-100} 1e-100
jitter {'multiplier': inf, 'max': 40} 40.0
[assistant] `wait_exponential` now returns the capped wait instead of raising `ValueError: math domain error` for `multiplier=1e300, max=1e-100` and for `multiplier=float("inf")`. The full suite passes, and the changes are uncommitted in the worktree.

**Cause:** the short-circuit that skips the power calculation once the cap is reached calls `math.log(max / multiplier, exp_base)`. When `max / multiplier` underflows to 0.0 (or `multiplier` is infinite), `math.log(0.0)` raises.

**Fix (`tenacity/wait.py`):** if `max / multiplier == 0`, the cap is already below the first term, so the short-circuit applies. 
…[607 chars elided]…
exit 0, 172 passed, 1 skipped.
- `check_changed.py`: PASS, 0 problems.
- Not run: ruff and mypy, which aren't available here.
- Skipped: no user-docs change, since the fix doesn't alter documented usage.

**Choices to review:**
- The new branch returns `max(max(0, min), max)`, the same exit as the existing cap short-circuit. The `OverflowError` path returns `max` without the `min` clamp. The two differ only when `min > max`.
- `wait_exponential_jitter` has its own copy of the arithmetic, but it has no `math.log` path. I probed it with both inputs and it returns the cap, so it needed no change.
