# trajectory inv-1

final message:
`wait_exponential` no longer computes the power once the wait is past `max`. Results are unchanged: the old-vs-new probe reports `IDENTICAL` across 96,390 cases, and the full suite passes.

**What changed**
- `tenacity/wait.py`: `wait_exponential.__call__` first asks a new helper `_capped_result(exponent)`. That helper decides in log space whether the wait is past `max`, and returns the same value the old code would have produced, without calling `**`. When the decision is too close to a boundary, it returns `None` and the original code runs.
- Added `import math` and `import sys` to support this.
- `tests/test_tenacity.py`: new `test_exponential_max_skips_power_past_cap`. It uses a float subclass that records every `__pow__` call. It failed on the unfixed code with `[49, 999999999] != []`, and passes now.

**Verification**
- Regression test, red then green: as above.
- Full suite: `exit=0`, 168 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: `PASS: 0 problem(s)` after I fixed one 100-column docstring line. ruff and mypy were not run; they are unavailable in this environment.
- Equivalence probe: `cases: 96390  differing: 0`, `IDENTICAL`. The grid covers both sides of the cap, int and float bases and multipliers, zero and negative values, `min > max` misconfigurations, bases below 1, and attempt numbers up to 10^6.

**Limits and choices to review**
- The power is still computed for an exponent within about 1e-9 (relative) of the float-overflow boundary, when a float is involved. Deciding that case requires the power, so the stated "never compute beyond the cap" requirement is not fully met for that narrow band. This matters only when `max` is close to the float range, and the probe covers it.
- The shortcut applies only to finite positive int/float `exp_base`, `multiplier` and `max`, with `exp_base > 1` and `multiplier > 0`. Anything else takes the original path.
- The old code returned `max` unclamped on overflow, which differs from the clamped result when `min > max`. The new code reproduces that inconsistency on purpose.
- Sibling left unchanged: `wait_exponential_jitter.__call__` (`tenacity/wait.py:323`) has the same `exp_base ** (attempt_number - 1)` pattern. I did not change it because the request named only `wait_exponential(max=...)`. It could take the same change if you want it.
- No reno note or docs were added. Results are identical, so this is not a user-visible behaviour change.

## events
[tool_use Skill] {"skill": "behavior-preserving-change"}
[tool_result] Launching skill: behavior-preserving-change
[user] Base directory for this skill: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/.claude/skills/behavior-preserving-change

# Changing how something is computed without changing what it returns

Two requirements, proved separately: (A) the stated cost is gone, (B) every result is the
same as before. Do both before the system.md full-suite step.

## A. Prove the cost is gone (regression test, red first)
- A timing assertion is flaky. Count the operation instead. For example, pass a subclass whose
  dunder (`__pow__`, `__mul__`, ...) appe
…[1964 chars elided]…
aviour on misconfigured input. Change the
  code to reproduce the old value and re-run until `IDENTICAL`. If you truly cannot match it,
  write it in the final message as an **unmet requirement** with the case. Do not offer it
  as a choice or an improvement.
- Quote the final verdict line (`IDENTICAL`, `cases: N`) in the final message.

## C. Then finish with system.md steps 2–3
Also check the sibling implementations. A subclass or copy that repeats the same expression
(grep the old expression across the package) either gets the same change or is named in the
final message as left unchanged.

[tool_use Bash] {"command": "grep -n \"class wait_exponential\" -A 40 tenacity/wait.py; echo ---; grep -rn \"wait_exponential\" tests/ | head -30; echo ---; ls .lithify/harness/scripts/", "description": "Show wait_exponential source, its tests, and harness scripts"}
[tool_result] 178:class wait_exponential(wait_base):
179-    """Wait strategy that applies exponential backoff.
180-
181-    It allows for a customized multiplier and an ability to restrict the
182-    upper and lower limits to some maximum and minimum value.
183-
184-    The intervals are fixed (i.e. there is no jitter), so this strategy is
185-    suitable for balancing retries against latency when a required resource is
186-    unavailable for an unknown duration, but *not* suitable for resolving
187-    c
…[4273 chars elided]…
it_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:654:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:656:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:660:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:662:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
---
check_changed.py
run_tests.py
[tool_use Bash] {"command": "ls .lithify/harness/skills/behavior-preserving-change/scripts/ 2>&1; echo ---; ls <work>/env-tenacity/bin/python 2>&1; echo ---; grep -n \"MAX_WAIT\" tenacity/_utils.py; echo ---; sed -n 1,30p tenacity/wait.py | grep -n import", "description": "Check harness scripts, project python, and imports"}
[tool_result] compare_old_new.py
---
<work>/env-tenacity/bin/python
---
25:MAX_WAIT = sys.maxsize / 2
---
17:import abc
18:import random
19:import typing
20:import warnings
22:from tenacity import _utils
25:    from tenacity import RetryCallState
[tool_use Bash] {"command": "grep -n '^class ' tests/test_tenacity.py | head; sed -n 335,360p tests/test_tenacity.py; grep -n \"^import\\|^from\" tests/test_tenacity.py | head -20", "description": "Inspect test file structure around wait_exponential tests"}
[tool_result] 87:class TestBase(unittest.TestCase):
113:class TestRetryingName(unittest.TestCase):
180:class TestStopConditions(unittest.TestCase):
284:class TestWaitConditions(unittest.TestCase):
710:class TestRetryConditions(unittest.TestCase):
921:class NoneReturnUntilAfterCount:
939:class NoIOErrorAfterCount:
957:class NoNameErrorAfterCount:
975:class NoNameErrorCauseAfterCount:
1000:class NoIOErrorCauseAfterCount:
        for t in times:
            self.assertTrue(t >= 0)
            self.assertTrue(t <
…[1140 chars elided]…
sertEqual(r.wait(make_retry_state(8, 0)), 40)
        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n", "new_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_exponential_max_skips_power_past_cap(self) -> None:\n   
…[194 chars elided]…
      return float.__pow__(self, other)\n\n        fn = tenacity.wait_exponential(max=40, exp_base=CountingBase(2))\n        self.assertEqual(fn(make_retry_state(3, 0)), 4)\n        self.assertEqual(len(powers), 1)\n        del powers[:]\n        self.assertEqual(fn(make_retry_state(50, 0)), 40)\n        self.assertEqual(fn(make_retry_state(10**9, 0)), 40)\n        self.assertEqual(powers, [])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_exponential_max_skips_power_past_cap\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red.txt", "description": "Run new regression test alone against unfixed code"}
[tool_result] exit=1
    def test_exponential_max_skips_power_past_cap(self) -> None:
        powers: typing.List[typing.Any] = []
    
        class CountingBase(float):
            def __pow__(self, other: typing.Any) -> typing.Any:
                powers.append(other)
                return float.__pow__(self, other)
    
        fn = tenacity.wait_exponential(max=40, exp_base=CountingBase(2))
        self.assertEqual(fn(make_retry_state(3, 0)), 4)
        self.assertEqual(len(powers), 1)
        del power
…[219 chars elided]…
]
E       
E       First list contains 2 additional elements.
E       First extra element 0:
E       49
E       
E       - [49, 999999999]
E       + []

tests/test_tenacity.py:376: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_max_skips_power_past_cap
============================== 1 failed in 0.07s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py", "old_string": "    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowErro
…[1787 chars elided]…
 log_float_max) <= 1e-9 * (1 + log_float_max):\n                return None\n            if log_power > log_float_max:\n                return self.max\n        if abs(log_power - log_cap) <= 1e-9 * (1 + abs(log_cap)):\n            return None\n        if log_power > log_cap:\n            return max(max(0, self.min), cap)\n        return None\n\n\nclass wait_random_exponential(wait_exponential):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py", "old_string": "import abc\nimport random\nimport typing\nimport warnings", "new_string": "import abc\nimport math\nimport random\nimport sys\nimport typing\nimport warnings"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py has been updated successfully.
[assistant] Now the probe for the old-vs-new equivalence check, then the regression test and full suite.
[tool_use Bash] {"command": "cat > /tmp/probe.py <<'EOF'\nimport itertools, types\n\ndef cases():\n    bases = [0.5, 1, 1.0, 1.5, 2, 2.0, 3, 10.0, 1.0000001, 0, -2, 1e300, float(\"inf\"), float(\"nan\")]\n    mults = [1, 1.0, 0, 0.0, -1, 0.5, 2, 1e-300, 1e300]\n    caps = [40, 40.0, 0, -5, 1e18, 1e308, 2**80, 2**1024 * 0 + 1e300, 1e-9]\n    mins = [0, 0.0, 5, 50, -1]\n    attempts = [0, 1, 2, 3, 5, 10, 33, 64, 10
…[460 chars elided]…
-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python\n$PY .lithify/harness/skills/behavior-preserving-change/scripts/compare_old_new.py --file tenacity/wait.py --probe /tmp/probe.py --timeout 60 > /tmp/eq.txt 2>&1; echo \"exit=$?\"; tail -25 /tmp/eq.txt", "description": "Run old-vs-new equivalence probe on wait.py"}
[tool_result] exit=0
cases: 96390  differing: 0
IDENTICAL
[assistant] The probe is identical across 96,390 cases. Now the regression test, the full suite, and the lint substitute.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_exponential_max_skips_power_past_cap\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green.txt; echo ---FULL; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -5 /tmp/full.txt; echo ---LINT; $PY .lithify/harness/scripts/check_changed.py > /tmp/lint.txt 2>&1; echo \"exit=$?\"; tail -15 /tmp/lint.txt", "description": "Run regression test green, full suite, and check_changed"}
[tool_result] exit=0
============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
---FULL
exit=0
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 168 passed, 1 skipped, 12 subtests passed in 1.83s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---LINT
exit=1
changed: tenacity/wait.py, tests/test_tenacity.py
FAIL tenacity/wait.py:218: line is 100 columns (max 88)
FAIL: 1 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py", "old_string": "        \"\"\"Return the wait for an exponent whose power is past ``max``, without computing the power.\n\n        Returns None when the power has to be computed: the wait is not past ``max``,\n        or it is too close to a boundary to decide from logarithms.\n        \"\"\"", "new_string": "        \"\"\"Return the wait for an exponent past ``max``, without computing the power.\n\n        Returns None when the power has to be computed: the wait is not past ``max``,\n        or it is too close to a boundary to decide from logarithms.\n        \"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/inv-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/lint.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/lint.txt; echo ---SIBLINGS; grep -rn \"exp_base \\*\\*\\|exp_base\\*\\*\" tenacity/ ; echo ---; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full.txt; echo ---EQ; $PY .lithify/harness/skills/behavior-preserving-change/scripts/compare_old_new.py --file tenacity/wait.py --probe /tmp/probe.py --timeout 60 > /tmp/eq.txt 2>&1; echo \"exit=$?\"; tail -2 /tmp/eq.txt", "description": "Re-run lint, sibling grep, full suite, and equivalence check"}
[tool_result] exit=0
changed: tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---SIBLINGS
tenacity/wait.py:211:            exp = self.exp_base ** exponent
tenacity/wait.py:323:            exp = self.exp_base ** (retry_state.attempt_number - 1)
---
exit=0
============== 168 passed, 1 skipped, 12 subtests passed in 1.85s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---EQ
exit=0
cases: 96390  differing: 0
IDENTICAL
[tool_use Bash] {"command": "sed -n 316,330p tenacity/wait.py; echo ---; git diff --stat", "description": "Confirm sibling implementation and diff stats"}
[tool_result]         self.exp_base = exp_base
        self.jitter = _utils.to_seconds(jitter)
        self.min = _utils.to_seconds(min)

    def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.multiplier * exp + jitter
        except OverflowError:
            result = self.max
        return max(max(0, self.min), min(result, self.max))
---
 tenacity/wait.py       | 39 ++++++++++++++++++++++++++++++++++++++-
 tests/test_tenacity.py | 16 ++++++++++++++++
 2 files changed, 54 insertions(+), 1 deletion(-)
[assistant] `wait_exponential` no longer computes the power once the wait is past `max`. Results are unchanged: the old-vs-new probe reports `IDENTICAL` across 96,390 cases, and the full suite passes.

**What changed**
- `tenacity/wait.py`: `wait_exponential.__call__` first asks a new helper `_capped_result(exponent)`. That helper decides in log space whether the wait is past `max`, and returns the same value the old code would have produced, without calling `**`. When the decision is too close to a boundary, it returns `None` and the original code runs.
- Added `import math` and `import sys` to support t
…[1247 chars elided]…
 and `multiplier > 0`. Anything else takes the original path.
- The old code returned `max` unclamped on overflow, which differs from the clamped result when `min > max`. The new code reproduces that inconsistency on purpose.
- Sibling left unchanged: `wait_exponential_jitter.__call__` (`tenacity/wait.py:323`) has the same `exp_base ** (attempt_number - 1)` pattern. I did not change it because the request named only `wait_exponential(max=...)`. It could take the same change if you want it.
- No reno note or docs were added. Results are identical, so this is not a user-visible behaviour change.
