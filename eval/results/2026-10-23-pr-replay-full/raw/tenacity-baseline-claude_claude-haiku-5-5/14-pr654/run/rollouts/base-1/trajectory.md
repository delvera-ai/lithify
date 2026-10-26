# trajectory base-1

final message:
`wait_exponential` no longer computes the power once the result has reached `max`. The full suite passes (168 passed, 1 skipped, including one new test), and the changes are uncommitted in the worktree.

**The change** (`tenacity/wait.py`):
- A new `_exceeds_max(exponent)` helper decides in log space whether `multiplier * exp_base ** exponent` is already above `max`. If so, `__call__` uses `max` and skips the power. The original clamp still runs on that value, so the output is unchanged.
- The check uses a small log margin (`1e-9`), so float rounding can never mark an in-range value as capped. Attempts whose result lands just above `max` may still compute the power once, because the check is conservative.
- The helper falls back to the original computation when `multiplier <= 0`, `exp_base <= 1`, `max <= 0`, or `min > max`. The last case matters: there an overflowing power returns `max` unclamped, and the fast path would have returned `min` instead.

**Verification:**
- I compared the new `__call__` against the original logic over about 608k combinations of multiplier, max, exp_base, min, and attempt number (including `inf`, zero, negative, and huge attempts). There were zero mismatches. The first draft had a mismatch in the `min > max` overflow case, which is why that fallback exists.
- The new test `test_exponential_with_max_wait_huge_attempt` checks that attempt 10⁷ returns `40` with `max=40`. I added it as a new test and did not modify existing ones.
- Lint: the wrapped lines fit the project's 88-character limit. I didn't run ruff, since it isn't installed in the test environment.

I haven't committed. Say if you want a commit, and the attribution line will go on it.

## events
[tool_use Bash] {"command": "grep -rn \"class wait_exponential\" -A 40 tenacity/wait.py && git status --short", "description": "Locate wait_exponential implementation"}
[tool_result] tenacity/wait.py:178:class wait_exponential(wait_base):
tenacity/wait.py-179-    """Wait strategy that applies exponential backoff.
tenacity/wait.py-180-
tenacity/wait.py-181-    It allows for a customized multiplier and an ability to restrict the
tenacity/wait.py-182-    upper and lower limits to some maximum and minimum value.
tenacity/wait.py-183-
tenacity/wait.py-184-    The intervals are fixed (i.e. there is no jitter), so this strategy is
tenacity/wait.py-185-    suitable for balancing ret
…[3777 chars elided]…
         )
tenacity/wait.py-275-            multiplier = initial
tenacity/wait.py-276-
tenacity/wait.py-277-        self.multiplier = multiplier
tenacity/wait.py-278-        self.max = _utils.to_seconds(max)
tenacity/wait.py-279-        self.exp_base = exp_base
tenacity/wait.py-280-        self.jitter = _utils.to_seconds(jitter)
tenacity/wait.py-281-        self.min = _utils.to_seconds(min)
tenacity/wait.py-282-
tenacity/wait.py-283-    def __call__(self, retry_state: "RetryCallState") -> float:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py", "offset": 1, "limit": 40}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITH
…[401 chars elided]…
  """Abstract base class for wait strategies."""
30	
31	    @abc.abstractmethod
32	    def __call__(self, retry_state: "RetryCallState") -> float:
33	        pass
34	
35	    def __add__(self, other: "wait_base") -> "wait_combine":
36	        return wait_combine(self, other)
37	
38	    def __radd__(self, other: "wait_base") -> "wait_combine | wait_base":
39	        # make it possible to use multiple waits with the built-in sum function
40	        if other == 0:  # type: ignore[comparison-overlap]
[tool_use Bash] {"command": "grep -rn \"exp_base\\|wait_exponential\" tests | head -40", "description": "Find existing tests covering wait_exponential"}
[tool_result] tests/test_tenacity.py:340:        r = Retrying(wait=tenacity.wait_exponential())
tests/test_tenacity.py:351:        r = Retrying(wait=tenacity.wait_exponential(max=40))
tests/test_tenacity.py:363:        r = Retrying(wait=tenacity.wait_exponential(min=20))
tests/test_tenacity.py:375:        r = Retrying(wait=tenacity.wait_exponential(max=50, multiplier=1))
tests/test_tenacity.py:387:        r = Retrying(wait=tenacity.wait_exponential(min=20, multiplier=2))
tests/test_tenacity.py:404:           
…[851 chars elided]…
ty.py:648:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:654:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:656:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:660:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:662:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
[tool_use Bash] {"command": "grep -n \"MAX_WAIT\\|def to_seconds\" -A3 tenacity/_utils.py | head -20; sed -n 330,410p tests/test_tenacity.py; ls <work>/env-tenacity/bin/python 2>&1", "description": "Inspect helpers, existing tests, and check env python"}
[tool_result] 25:MAX_WAIT = sys.maxsize / 2
26-
27-
28-class LoggerProtocol(typing.Protocol):
--
84:def to_seconds(time_unit: time_unit_type) -> float:
85-    return float(
86-        time_unit.total_seconds() if isinstance(time_unit, timedelta) else time_unit
87-    )
        times.add(r.wait(make_retry_state(1, 6546)))
        times.add(r.wait(make_retry_state(1, 6546)))

        # this is kind of non-deterministic...
        self.assertTrue(len(times) > 1)
        for t in times:
            self.assertTru
…[3744 chars elided]…

                self.assertEqual(r.wait(make_retry_state(2, 0)), 10)
                self.assertEqual(r.wait(make_retry_state(3, 0)), 10)
                self.assertEqual(r.wait(make_retry_state(4, 0)), 10)
                self.assertEqual(r.wait(make_retry_state(5, 0)), 16)
                self.assertEqual(r.wait(make_retry_state(6, 0)), 32)
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run test suite for baseline"}
[tool_result] ...............s.............................................. [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.83s
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowErr
…[819 chars elided]…
 cap. The\n        # margin keeps float rounding in the logs from flagging a value at or below max.\n        if self.multiplier <= 0 or self.exp_base <= 1 or self.max <= 0:\n            return False\n        return (\n            math.log(self.multiplier) + exponent * math.log(self.exp_base)\n            > math.log(self.max) + 1e-9\n        )\n\n\nclass wait_random_exponential(wait_exponential):"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "import abc\nimport random", "new_string": "import abc\nimport math\nimport random"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2\nmkdir -p /tmp/wexp-check && cat > /tmp/wexp-check/check.py <<'EOF'\nimport sys, time, math, datetime\nsys.path.insert(0, sys.argv[1])\nimport tenacity\nfrom tenacity import
…[1603 chars elided]…
 wait_exponential(max=datetime.timedelta(seconds=40), min=datetime.timedelta(seconds=1))\nprint(\"timedelta\", w(S(10**7)), w(S(3)))\nEOF\n<work>/env-tenacity/bin/python -I /tmp/wexp-check/check.py \"$PWD\"", "description": "Run tests and equivalence check against old logic"}
[tool_result] ....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.81s
MISMATCH 0.5 1 1.5 20 5000 20.0 1.0
MISMATCH 0.5 1 1.5 20 1000000 20.0 1.0
MISMATCH 0.5 1 1.5 1000000000000.0 5000 1000000000000.0 1.0
MISMATCH 0.5 1 1.5 1000000000000.0 1000000 1000000000000.0 1.0
MISMATCH 0.5 1 2 20 5000 20.0 1.0
MISMATCH 0.5 1 2 20 1000000 20.0 1.0
MISMATCH 0.5 1 2 1000000000000.0 5000 1000000000000.0 1.0
MISMATCH 0.5 1 2 1000000000000.0 1000000 1000000000000.0 1.0
MISMATCH 0.5 1 2.0 20 5000 20.0 1.0
checked 607824 mismatches 1570
attempt 1e7 -> 40.0 in 0.0000s
timedelta 40.0 4
[assistant] The equivalence check found a real gap. When `min > max` and the power overflows a float, the old code returns `max` unclamped, while the clamped path returns `min`. The fast path has to fall back to the original computation in that case to keep results identical.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "        # above max, so the power is never evaluated once it has hit the cap. The\n        # margin keeps float rounding in the logs from flagging a value at or below max.\n        if self.multiplier <= 0 or self.exp_bas
…[109 chars elided]…
r evaluated once it has hit the cap. The\n        # margin keeps float rounding in the logs from flagging a value at or below max.\n        # With min above max, an overflowing power returns max unclamped, so keep the\n        # original path there to leave results unchanged.\n        if self.multiplier <= 0 or self.exp_base <= 1 or self.max <= 0 or self.min > self.max:\n            return False"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $P -I /tmp/wexp-check/check.py \"$PWD\"", "description": "Rerun tests and equivalence check"}
[tool_result] ....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.80s
checked 607824 mismatches 0
attempt 1e7 -> 40.0 in 0.0000s
timedelta 40.0 4
[assistant] Tests pass and the 607k-case comparison against the original logic shows zero mismatches. Next I'll check the line length against the project's lint config.
[tool_use Bash] {"command": "grep -n \"line-length\\|line_length\\|max-line\" pyproject.toml setup.cfg tox.ini .pre-commit-config.yaml 2>/dev/null; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/wait.py; P=<work>/env-tenacity/bin/python; $P -m ruff --version 2>/dev/null && $P -m ruff check tenacity/wait.py && $P -m ruff format --check tenacity/wait.py", "description": "Check line length and lint config"}
[tool_result ERROR] Exit code 1
99:line-length = 88
tenacity/wait.py: 221: 94
tenacity/wait.py: 268: 90
tenacity/wait.py: 283: 90
[tool_use Bash] {"command": "sed -n 219,223p tenacity/wait.py; git diff --stat", "description": "Show the long line and diff stat"}
[tool_result]         # With min above max, an overflowing power returns max unclamped, so keep the
        # original path there to leave results unchanged.
        if self.multiplier <= 0 or self.exp_base <= 1 or self.max <= 0 or self.min > self.max:
            return False
        return (
 tenacity/wait.py | 27 ++++++++++++++++++++++-----
 1 file changed, 22 insertions(+), 5 deletions(-)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "        # Decide in log space whether multiplier * exp_base ** exponent is already\n        # above max, so the power is never evaluated once it has hit the cap. The\n        # margin keeps float rounding in the logs fro
…[511 chars elided]…
float rounding in the logs from flagging a value at or below\n        # max. With min above max, an overflowing power returns max unclamped, so\n        # keep the original path there to leave results unchanged.\n        if (\n            self.multiplier <= 0\n            or self.exp_base <= 1\n            or self.max <= 0\n            or self.min > self.max\n        ):\n            return False"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; $P -I /tmp/wexp-check/check.py \"$PWD\" | head -1; git diff", "description": "Rerun tests, equivalence check, and show diff"}
[tool_result] 167 passed, 1 skipped, 12 subtests passed in 1.82s
checked 607824 mismatches 0
diff --git a/tenacity/wait.py b/tenacity/wait.py
index 3b53da2..47d110f 100644
--- a/tenacity/wait.py
+++ b/tenacity/wait.py
@@ -15,6 +15,7 @@
 # limitations under the License.
 
 import abc
+import math
 import random
 import typing
 import warnings
@@ -201,13 +202,34 @@ class wait_exponential(wait_base):
         self.exp_base = exp_base
 
     def __call__(self, retry_state: "RetryCallState") -> float:
-        try
…[951 chars elided]…
 keep the original path there to leave results unchanged.
+        if (
+            self.multiplier <= 0
+            or self.exp_base <= 1
+            or self.max <= 0
+            or self.min > self.max
+        ):
+            return False
+        return (
+            math.log(self.multiplier) + exponent * math.log(self.exp_base)
+            > math.log(self.max) + 1e-9
+        )
+
 
 class wait_random_exponential(wait_exponential):
     """Random wait with exponentially widening window.
[assistant] The fix is in place and verified. I'll add a regression test for the capped case so the behavior stays pinned down.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_exponential_with_min_wait(self) -> None:", "new_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_exponential_with_max_wait_huge_attempt(self) -> None:\n        # Past the cap the power must not be evaluated, so a huge attempt is cheap.\n        r = Retrying(wait=tenacity.wait_exponential(max=40))\n        self.assertEqual(r.wait(make_retry_state(10**7, 0)), 40)\n\n    def test_exponential_with_min_wait(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-191924-performance-wait-exponential-max/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git stash list >/dev/null; git -c core.pager=cat diff --stat; rm -rf /tmp/wexp-check", "description": "Run full test suite with new regression test"}
[tool_result] 168 passed, 1 skipped, 12 subtests passed in 1.83s
 tenacity/wait.py       | 32 +++++++++++++++++++++++++++-----
 tests/test_tenacity.py |  5 +++++
 2 files changed, 32 insertions(+), 5 deletions(-)
[assistant] `wait_exponential` no longer computes the power once the result has reached `max`. The full suite passes (168 passed, 1 skipped, including one new test), and the changes are uncommitted in the worktree.

**The change** (`tenacity/wait.py`):
- A new `_exceeds_max(exponent)` helper decides in log space whether `multiplier * exp_base ** exponent` is already above `max`. If so, `__call__` uses `max` and skips the power. The original clamp still runs on that value, so the output is unchanged.
- The check uses a small log margin (`1e-9`), so float rounding can never mark an in-range value as capped.
…[499 chars elided]…
, min, and attempt number (including `inf`, zero, negative, and huge attempts). There were zero mismatches. The first draft had a mismatch in the `min > max` overflow case, which is why that fallback exists.
- The new test `test_exponential_with_max_wait_huge_attempt` checks that attempt 10⁷ returns `40` with `max=40`. I added it as a new test and did not modify existing ones.
- Lint: the wrapped lines fit the project's 88-character limit. I didn't run ruff, since it isn't installed in the test environment.

I haven't committed. Say if you want a commit, and the attribution line will go on it.
