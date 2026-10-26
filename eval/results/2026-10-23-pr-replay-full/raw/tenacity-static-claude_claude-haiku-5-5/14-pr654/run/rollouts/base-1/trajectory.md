# trajectory base-1

final message:
`wait_exponential` no longer computes the power once the exponential is past `max`. The full suite passes and the new regression test fails on the old code for the right reason.

**What changed**
- `tenacity/wait.py`: `__call__` first asks a new helper, `_exceeds_max(n)`, whether `multiplier * exp_base ** n` is clearly above `max`. The check runs in log space (`n * log(exp_base) > log(max / multiplier)`), so the power is never computed past the cap. If the answer is yes, the result is `self.max` and it goes through the same final clamp as before. Otherwise the original power and overflow code runs unchanged.
- `tests/test_tenacity.py`: `test_exponential_with_max_wait_does_not_compute_power_past_cap` uses a float subclass that records every `**` call. At attempt 10**6 with `max=40`, the old code recorded `[999999]`; the new code records nothing and still returns 40.

**Verification**
- Regression test, run alone against the unfixed code: failed with `[999999] != []`. After the fix: passed.
- Full suite (`run_tests.py`, no args): `exit=0`, 168 passed, 1 skipped, 12 subtests passed.
- `check_changed.py`: `PASS: 0 problem(s)`.
- Equivalence: I compared the old and new `wait_exponential` over 6.9M combinations of multiplier, max, min, exp_base (float and int), and attempt numbers up to 10**6. Results matched exactly in every case where `min <= max`, including the overflow and exception paths.
- Not run: ruff and mypy (unavailable in this environment, as the project notes say).

**One edge case to decide on**
When `min > max` (a misconfiguration), the old code returned `max` unclamped once the float power overflowed, but the clamped `min` value earlier. The new code returns the clamped value consistently. I kept it consistent rather than copy the old inconsistency. If you want the old overflow result preserved exactly, say so and I'll adjust.

**Choices I made**
- I did not add a reno release note. This is a performance change with no change in results, so I judged it not user-visible behavior.
- I did not commit, since you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -n \"class wait_exponential\" -A 45 tenacity/wait.py && git status --short && ls .lithify/harness/scripts/ && ls doc/source/ | head -5 && ls releasenotes/notes 2>/dev/null | tail -3", "description": "Read wait_exponential implementation and repo layout"}
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
…[3038 chars elided]…
f, retry_state: "RetryCallState") -> float:
284-        jitter = random.uniform(0, self.jitter)
285-        try:
286-            exp = self.exp_base ** (retry_state.attempt_number - 1)
287-            result = self.multiplier * exp + jitter
288-        except OverflowError:
check_changed.py
run_tests.py
api.rst
changelog.rst
conf.py
index.rst
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 224,242p tenacity/wait.py && grep -n \"MAX_WAIT\" tenacity/_utils.py && ls tests && grep -n \"wait_exponential\\b\\|def test_wait_exponential\" -n tests/test_tenacity.py | head -30 && head -40 .lithify/harness/scripts/run_tests.py && ls <work>/env-tenacity/bin/python", "description": "Inspect wait strategies, tests, and harness scripts"}
[tool_result]     It allows for a custom multiplier and an ability to restrict the upper
    limit of the random interval to some maximum value.

    Example::

        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
                                max=60)          # max 60s timeout

    When waiting for an unavailable resource to become available again, as
    opposed to trying to resolve contention for a shared resource, the
    wait_exponential strategy (which uses a fixed interval) may be p
…[2345 chars elided]…
ting test, check
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
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 336,420p tests/test_tenacity.py && sed -n 1,30p tests/test_tenacity.py | grep -n import", "description": "Read existing wait_exponential tests"}
[tool_result]             self.assertTrue(t >= 0)
            self.assertTrue(t <= 2)

    def test_exponential(self) -> None:
        r = Retrying(wait=tenacity.wait_exponential())
        self.assertEqual(r.wait(make_retry_state(1, 0)), 1)
        self.assertEqual(r.wait(make_retry_state(2, 0)), 2)
        self.assertEqual(r.wait(make_retry_state(3, 0)), 4)
        self.assertEqual(r.wait(make_retry_state(4, 0)), 8)
        self.assertEqual(r.wait(make_retry_state(5, 0)), 16)
        self.assertEqual(r.wait
…[3898 chars elided]…
   def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

    def test_wait_func(self) -> None:
        def wait_func(retry_state: RetryCallState) -> typing.Any:
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tests/test_tenacity.py", "old_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)\n\n    def test_legacy_explicit_wait_type(self) -> None:", "new_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100
…[258 chars elided]…
append(other)\n                return super().__pow__(other)\n\n        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=RecordingBase(2)))\n        self.assertEqual(r.wait(make_retry_state(7, 0)), 40)\n        powers.clear()\n        self.assertEqual(r.wait(make_retry_state(10**6, 0)), 40)\n        self.assertEqual(powers, [])\n\n    def test_legacy_explicit_wait_type(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestTenacity::test_exponential_with_max_wait_does_not_compute_power_past_cap\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red.txt", "description": "Run the new regression test against unfixed code"}
[tool_result] exit=4
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collected 0 items

============================ no tests ran in 0.04s =============================
ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tests/test_tenacity.py::TestTenacity::test_exponential_with_max_wait_does_not_compute_power_past_cap
(no match in any of [<Module test_tenacity.py>])

---
exit=4 (pytest); full log: /tmp/run_tests.log
[assistant] The class name in my node id was a guess; I'll find the real one.
[tool_use Bash] {"command": "grep -n \"^class \" tests/test_tenacity.py | head -5 && <work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 -k compute_power_past_cap > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red.txt", "description": "Find test class and rerun regression test"}
[tool_result] 87:class TestBase(unittest.TestCase):
113:class TestRetryingName(unittest.TestCase):
180:class TestStopConditions(unittest.TestCase):
284:class TestWaitConditions(unittest.TestCase):
724:class TestRetryConditions(unittest.TestCase):
exit=1
self = <tests.test_tenacity.TestWaitConditions testMethod=test_exponential_with_max_wait_does_not_compute_power_past_cap>

    def test_exponential_with_max_wait_does_not_compute_power_past_cap(self) -> None:
        powers: list[typing.Any] = []
    
        
…[523 chars elided]…
 First list contains 1 additional elements.
E       First extra element 0:
E       999999
E       
E       - [999999]
E       + []

tests/test_tenacity.py:428: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_with_max_wait_does_not_compute_power_past_cap
====================== 1 failed, 168 deselected in 0.08s =======================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Red for the right reason: the power is computed at attempt 10**6 (`[999999] != []`). Now the fix.
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py | grep -n \"import\"", "description": "Check imports in wait module"}
[tool_result] 17:import abc
18:import random
19:import typing
20:import warnings
22:from tenacity import _utils
25:    from tenacity import RetryCallState
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "import abc\nimport random", "new_string": "import abc\nimport math\nimport random"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowErr
…[727 chars elided]…
       Decided in log space so the power is never computed past the cap. The\n        small margin keeps values near max on the exact path.\n        \"\"\"\n        if self.multiplier <= 0 or self.exp_base <= 1 or self.max <= 0:\n            return False\n        return n * math.log(self.exp_base) > math.log(self.max / self.multiplier) + 1e-9\n\n\nclass wait_random_exponential(wait_exponential):"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now the regression test should go green, then the full suite and the stdlib checker.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 -k compute_power_past_cap > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"full exit=$?\"; tail -6 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/chk.txt 2>&1; echo \"check exit=$?\"; tail -8 /tmp/chk.txt", "description": "Run regression test, full suite, and check_changed script"}
[tool_result] exit=0

====================== 1 passed, 168 deselected in 0.04s =======================
---
exit=0 (pytest); full log: /tmp/run_tests.log
full exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 168 passed, 1 skipped, 12 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
check exit=0
changed: tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Green. Next, an equivalence check against the original `wait.py` over a parameter grid, including attempts near the cap and far past it.
[tool_use Bash] {"command": "mkdir -p /tmp/eqcheck && cd ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1 && git show HEAD:tenacity/wait.py > /tmp/eqcheck/old_wait.py && cat > /tmp/eqcheck/eq.py <<'EOF'\nimport importlib.util, itertools, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-expone
…[1346 chars elided]…
       bad += 1\n            if bad <= 10: print(\"DIFF\", m, mx, mn, eb, n, a, c)\nprint(\"checked\", checked, \"diffs\", bad)\nEOF\n<work>/env-tenacity/bin/python /tmp/eqcheck/eq.py 2>&1 | tail -15", "description": "Compare old and new wait_exponential outputs over a grid"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: boiiuw50h). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261023-212750-performance-wait-exponential-max-base-1/2a44248a-adae-47e8-bd4c-fef93029a531/tasks/boiiuw50h.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
Session cwd remains ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1; directory changes made by the backgrounded command do not apply to subsequent commands.
[assistant] The old code is very slow on `2 ** 10**9` with integer bases, which is the cost being fixed. I'll stop it and drop that exponent from the grid.
[tool_use TaskStop] {"task_id": "boiiuw50h"}
[tool_result] {"message":"Successfully stopped task: boiiuw50h (mkdir -p /tmp/eqcheck && cd ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1 && git show HEAD:tenacity/wait.py > /tmp/eqcheck/old_wait.py && cat > /tmp/eqcheck/eq.py <<'EOF'\nimport importlib.util, itertools, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1\")\nimport tenacity\nfrom tenacity import wait
…[3225 chars elided]…
 (\"exc\", type(e))\n        try:\n            c = w(S(n))\n        except Exception as e:\n            c = (\"exc\", type(e))\n        checked += 1\n        if a != c:\n            bad += 1\n            if bad <= 10: print(\"DIFF\", m, mx, mn, eb, n, a, c)\nprint(\"checked\", checked, \"diffs\", bad)\nEOF\n<work>/env-tenacity/bin/python /tmp/eqcheck/eq.py 2>&1 | tail -15"}
[tool_use Bash] {"command": "cd /tmp/eqcheck && sed -i 's/, 10\\*\\*9\\]/]/' eq.py && grep -n \"ns = \" eq.py && timeout 110 <work>/env-tenacity/bin/python eq.py 2>&1 | tail -15", "description": "Rerun equivalence grid without the huge exponent"}
[tool_result ERROR] Exit code 1
sed: 1: "eq.py
": invalid command code e
[assistant] macOS `sed -i` needs an explicit backup suffix; retrying with that.
[tool_use Bash] {"command": "cd /tmp/eqcheck && sed -i '' 's/, 10\\*\\*9\\]/]/' eq.py && grep -n \"ns = \" eq.py && timeout 110 <work>/env-tenacity/bin/python eq.py 2>&1 | tail -15", "description": "Drop huge exponent from grid and rerun comparison"}
[tool_result] 15:mins = [0, 1, 20, 1e6]
17:ns = list(range(1, 2000)) + [10**4, 10**6]
(eval):1: command not found: timeout
Shell cwd was reset to ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1
[tool_use Bash] {"command": "cd /tmp/eqcheck && <work>/env-tenacity/bin/python eq.py > out.txt 2>&1; echo \"exit=$?\"; tail -15 out.txt", "description": "Run equivalence comparison and capture output", "timeout": 600000}
[tool_result] exit=0
DIFF 0.001 0.5 1 1.5 1752 0.5 1.0
DIFF 0.001 0.5 1 1.5 1753 0.5 1.0
DIFF 0.001 0.5 1 1.5 1754 0.5 1.0
DIFF 0.001 0.5 1 1.5 1755 0.5 1.0
DIFF 0.001 0.5 1 1.5 1756 0.5 1.0
DIFF 0.001 0.5 1 1.5 1757 0.5 1.0
DIFF 0.001 0.5 1 1.5 1758 0.5 1.0
DIFF 0.001 0.5 1 1.5 1759 0.5 1.0
DIFF 0.001 0.5 1 1.5 1760 0.5 1.0
DIFF 0.001 0.5 1 1.5 1761 0.5 1.0
checked 6915456 diffs 359310
Shell cwd was reset to ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1
[assistant] Diffs appear when `min > max`, the edge case I expected: the old float-overflow branch returned `self.max` unclamped. I'll confirm that every diff falls in that class.
[tool_use Bash] {"command": "cd /tmp/eqcheck && sed -e 's/        if a != c:/        if a != c and mn <= mx:/' eq.py > eq2.py && <work>/env-tenacity/bin/python eq2.py > out2.txt 2>&1; echo \"exit=$?\"; tail -12 out2.txt", "description": "Recheck equivalence restricted to min at most max", "timeout": 600000}
[tool_result] exit=0
checked 6915456 diffs 0
Shell cwd was reset to ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-212750-performance-wait-exponential-max/base-1
[assistant] Zero diffs whenever `min <= max`, across 6.9M cases including overflow and exception paths. Last, a review of the final diff.
[tool_use Bash] {"command": "git diff --stat && git diff -- tenacity/wait.py && rm -rf /tmp/eqcheck /tmp/red.txt /tmp/green.txt /tmp/full.txt /tmp/chk.txt", "description": "Show final diff and clean scratch files"}
[tool_result]  tenacity/wait.py       | 25 ++++++++++++++++++++-----
 tests/test_tenacity.py | 14 ++++++++++++++
 2 files changed, 34 insertions(+), 5 deletions(-)
diff --git a/tenacity/wait.py b/tenacity/wait.py
index 3b53da2..3953723 100644
--- a/tenacity/wait.py
+++ b/tenacity/wait.py
@@ -15,6 +15,7 @@
 # limitations under the License.
 
 import abc
+import math
 import random
 import typing
 import warnings
@@ -201,13 +202,27 @@ class wait_exponential(wait_base):
         self.exp_base = exp_base
 
     d
…[690 chars elided]…
iplier * exp_base ** n is clearly above max.
+
+        Decided in log space so the power is never computed past the cap. The
+        small margin keeps values near max on the exact path.
+        """
+        if self.multiplier <= 0 or self.exp_base <= 1 or self.max <= 0:
+            return False
+        return n * math.log(self.exp_base) > math.log(self.max / self.multiplier) + 1e-9
+
 
 class wait_random_exponential(wait_exponential):
     """Random wait with exponentially widening window.
[assistant] `wait_exponential` no longer computes the power once the exponential is past `max`. The full suite passes and the new regression test fails on the old code for the right reason.

**What changed**
- `tenacity/wait.py`: `__call__` first asks a new helper, `_exceeds_max(n)`, whether `multiplier * exp_base ** n` is clearly above `max`. The check runs in log space (`n * log(exp_base) > log(max / multiplier)`), so the power is never computed past the cap. If the answer is yes, the result is `self.max` and it goes through the same final clamp as before. Otherwise the original power and overflow code 
…[873 chars elided]…
the project notes say).

**One edge case to decide on**
When `min > max` (a misconfiguration), the old code returned `max` unclamped once the float power overflowed, but the clamped `min` value earlier. The new code returns the clamped value consistently. I kept it consistent rather than copy the old inconsistency. If you want the old overflow result preserved exactly, say so and I'll adjust.

**Choices I made**
- I did not add a reno release note. This is a performance change with no change in results, so I judged it not user-visible behavior.
- I did not commit, since you didn't ask for one.
