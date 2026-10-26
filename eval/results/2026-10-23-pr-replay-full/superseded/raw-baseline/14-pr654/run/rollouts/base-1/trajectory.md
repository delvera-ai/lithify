# trajectory base-1

final message:
`wait_exponential` now returns `max` once the exponential is past the cap, without computing the power. The project's test suite passes (168 passed, 1 skipped), including a new regression test.

**What changed** (`tenacity/wait.py`):
- A new `_exceeds_max(exponent)` check decides whether `multiplier * exp_base ** exponent` is certainly at or above `max`. It uses a log-space comparison with a margin of 1 (a factor of about e), so float rounding can't flip a result near the cap.
- `__call__` returns `self.max` directly when that check passes. Otherwise it runs the original code unchanged.
- `import math` was added.

**Decision for you:** the short-circuit only applies when `max(0, min) <= max`. When `min` is above `max`, the original code's overflow path returns `max` unclamped while its normal path clamps to `min`, so the two disagree. Short-circuiting there would change results, so those configs keep the original computation. That's a degenerate config, so the performance benefit is unaffected in practice. Say if you'd rather I preserve the cap in that case too.

**Verification:**
- I compared the new code against the original formula over about 331,000 combinations of multiplier, max, base, min and attempt number, including edge values such as multiplier 0 or −1, max 0, and a huge `MAX_WAIT`. After the `min > max` fix there were zero mismatches.
- A counting-base test confirms the power is not evaluated past the cap: attempt 10⁶ returns 40 with no power call for it.

**Test added** (`tests/test_tenacity.py`): `test_exponential_with_max_wait_skips_power_past_cap`. I did not modify existing tests.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"\" tenacity/wait.py | sed -n '1,200p' | grep -n -A30 \"class wait_exponential\"", "description": "Locate wait_exponential class in wait.py"}
[tool_result] 178:178:class wait_exponential(wait_base):
179-179:    """Wait strategy that applies exponential backoff.
180-180:
181-181:    It allows for a customized multiplier and an ability to restrict the
182-182:    upper and lower limits to some maximum and minimum value.
183-183:
184-184:    The intervals are fixed (i.e. there is no jitter), so this strategy is
185-185:    suitable for balancing retries against latency when a required resource is
186-186:    unavailable for an unknown duration, but *n
…[87 chars elided]…
ed resource. Use
188-188:    wait_random_exponential for the latter case.
189-189:    """
190-190:
191-191:    def __init__(
192-192:        self,
193-193:        multiplier: float = 1,
194-194:        max: _utils.time_unit_type = _utils.MAX_WAIT,
195-195:        exp_base: float = 2,
196-196:        min: _utils.time_unit_type = 0,
197-197:    ) -> None:
198-198:        self.multiplier = multiplier
199-199:        self.min = _utils.to_seconds(min)
200-200:        self.max = _utils.to_seconds(max)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py", "offset": 200, "limit": 30}
[tool_result] 200	        self.max = _utils.to_seconds(max)
201	        self.exp_base = exp_base
202	
203	    def __call__(self, retry_state: "RetryCallState") -> float:
204	        try:
205	            exp = self.exp_base ** (retry_state.attempt_number - 1)
206	            result = self.multiplier * exp
207	        except OverflowError:
208	            return self.max
209	        return max(max(0, self.min), min(result, self.max))
210	
211	
212	class wait_random_exponential(wait_exponential):
213	    """Rand
…[313 chars elided]…
 and corresponds to the "Full Jitter" algorithm described in
219	    this blog post:
220	
221	    https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
222	
223	    Each retry occurs at a random time in a geometrically expanding interval.
224	    It allows for a custom multiplier and an ability to restrict the upper
225	    limit of the random interval to some maximum value.
226	
227	    Example::
228	
229	        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py && grep -n \"MAX_WAIT\\|def to_seconds\" -A3 tenacity/_utils.py && grep -rn \"exp_base\\|wait_exponential\" tests | head -30", "description": "Check imports, MAX_WAIT, and existing exponential tests"}
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
…[1980 chars elided]…
ty.py:648:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:654:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:656:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:660:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:662:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowErr
…[787 chars elided]…
ate\") -> float:\n        exponent = retry_state.attempt_number - 1\n        if self._exceeds_max(exponent):\n            result = self.max\n        else:\n            try:\n                exp = self.exp_base ** exponent\n                result = self.multiplier * exp\n            except OverflowError:\n                return self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "sed -i '' 's/^import abc$/import abc\\nimport math/' tenacity/wait.py && sed -n 16,22p tenacity/wait.py && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Add math import and run the test suite"}
[tool_result] import abc
import math
import random
import typing
import warnings

...............s.............................................. [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.84s
[This command modified 1 file you've previously read: tenacity/wait.py. Call Read before editing.]
[assistant] The suite passes. Next I'll confirm the results match the original formula across a range of inputs, including the edge cases.
[tool_use Bash] {"command": "cat > /tmp/equiv_check.py <<'EOF'\nimport itertools, math, random, sys\nsys.path.insert(0, \".\")\nfrom tenacity import wait_exponential, _utils\n\nclass RS:\n    def __init__(self, n): self.attempt_number = n\n\ndef orig(mult, mx, base, mn, n):\n    try:\n        exp = base ** (n - 1)\n        result = mult * exp\n    except OverflowError:\n        return mx\n    return max(max(0, mn
…[1282 chars elided]…
nprint(\"result at attempt 10000:\", w(RS(10000)), \"pow calls:\", calls)\nEOF\n<work>/env-tenacity/bin/python -I /tmp/equiv_check.py; rm -f /tmp/equiv_check.py; cd . && git diff --stat", "description": "Compare new vs original formula over many inputs; check pow is skipped"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: byzc8ygr0). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-b58808c83cd1-20261023-164513-performance-wait-exponential-max-base-1/ff31079a-a709-45bf-8aab-874efc45c607/tasks/byzc8ygr0.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
Session cwd remains ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1; directory changes made by the backgrounded command do not apply to subsequent commands.
[assistant] The reference computation is too slow: `orig` computes huge powers like `10 ** 10**6`, which is the cost this change removes. I'll stop it and rerun with bounded exponents.
[tool_use Bash] {"command": "pkill -f equiv_check.py; cat > /tmp/equiv_check.py <<'EOF'\nimport itertools, math, random, sys\nsys.path.insert(0, \".\")\nfrom tenacity import wait_exponential, _utils\n\nclass RS:\n    def __init__(self, n): self.attempt_number = n\n\ndef orig(mult, mx, base, mn, n):\n    try:\n        exp = base ** (n - 1)\n        result = mult * exp\n    except OverflowError:\n        return mx\
…[1063 chars elided]…
se=CountingBase(2))\nprint(\"result at attempt 10000:\", w(RS(10000)), \"pow calls:\", calls)\nEOF\ntimeout 100 <work>/env-tenacity/bin/python -I /tmp/equiv_check.py; rm -f /tmp/equiv_check.py; git diff --stat", "description": "Rerun equivalence check with bounded exponents"}
[tool_result] (eval):44: command not found: timeout
 tenacity/wait.py | 30 +++++++++++++++++++++++++-----
 1 file changed, 25 insertions(+), 5 deletions(-)
[assistant] `timeout` isn't installed here, and the `rm` still ran. I'll rewrite the check in a scratch directory outside the repo and run it directly; the bounded exponents should keep it fast.
[tool_use Bash] {"command": "mkdir -p <tmp>/equiv && cat > <tmp>/equiv/equiv_check.py <<'EOF'\nimport itertools, random, sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1\")\nfrom tenacity import wait_exponential, _utils\n\nclass RS:\n    def __init__(self, n): self.attempt_number = n\n\ndef or
…[1193 chars elided]…
ax=60, exp_base=CountingBase(2))\nprint(\"result at attempt 10000:\", w(RS(10000)), \"pow calls:\", calls)\nEOF\n<work>/env-tenacity/bin/python -I <tmp>/equiv/equiv_check.py; echo \"exit=$?\"", "description": "Run equivalence check from a scratch directory"}
[tool_result] MISMATCH 0.5 1 2 5 1150 1.0 5.0
MISMATCH 0.5 1 2 5 1108 1.0 5.0
MISMATCH 0.5 1 2 5 1094 1.0 5.0
MISMATCH 0.5 1 2 100 1025 1.0 100.0
checked 331128 mismatches 653
result at attempt 10000: 60.0 pow calls: []
exit=0
[assistant] The check found 653 mismatches. They are all degenerate configs where `min > max`. In the original, the overflow path returns `self.max` unclamped, while the normal path clamps to `min`, so the two disagree when the floor is above the cap. I'll make the short-circuit apply only when `max(0, min) <= max`, which is the only case where both paths return `max`. Other configs fall through to the original code.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py", "offset": 205, "limit": 30}
[tool_result] 205	        # Conservative check that multiplier * exp_base ** exponent is certainly
206	        # >= self.max, so the power need not be computed. The margin of 1 in log
207	        # space (a factor of about e) keeps float rounding from changing results.
208	        if not (
209	            self.multiplier > 0
210	            and self.exp_base > 1
211	            and 0 < self.max < math.inf
212	            and exponent >= 0
213	        ):
214	            return False
215	        return exponent
…[223 chars elided]…
empt_number - 1
221	        if self._exceeds_max(exponent):
222	            result = self.max
223	        else:
224	            try:
225	                exp = self.exp_base ** exponent
226	                result = self.multiplier * exp
227	            except OverflowError:
228	                return self.max
229	        return max(max(0, self.min), min(result, self.max))
230	
231	
232	class wait_random_exponential(wait_exponential):
233	    """Random wait with exponentially widening window.
234	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    def _exceeds_max(self, exponent: int) -> bool:\n        # Conservative check that multiplier * exp_base ** exponent is certainly\n        # >= self.max, so the power need not be computed. The margin of 1 in log\n    
…[1644 chars elided]…
call__(self, retry_state: \"RetryCallState\") -> float:\n        exponent = retry_state.attempt_number - 1\n        if self._exceeds_max(exponent):\n            return self.max\n        try:\n            exp = self.exp_base**exponent\n            result = self.multiplier * exp\n        except OverflowError:\n            return self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -I <tmp>/equiv/equiv_check.py; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Rerun equivalence check and test suite"}
[tool_result] checked 331128 mismatches 0
result at attempt 10000: 60.0 pow calls: []
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.85s
[assistant] Zero mismatches across 331k comparisons, and the suite passes. I'll add a regression test for the no-power-past-cap behaviour, following the existing style.
[tool_use Bash] {"command": "sed -n 336,362p tests/test_tenacity.py", "description": "View existing wait_exponential tests"}
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
…[369 chars elided]…
ry_state(2, 0)), 2)
        self.assertEqual(r.wait(make_retry_state(3, 0)), 4)
        self.assertEqual(r.wait(make_retry_state(4, 0)), 8)
        self.assertEqual(r.wait(make_retry_state(5, 0)), 16)
        self.assertEqual(r.wait(make_retry_state(6, 0)), 32)
        self.assertEqual(r.wait(make_retry_state(7, 0)), 40)
        self.assertEqual(r.wait(make_retry_state(8, 0)), 40)
        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)

    def test_exponential_with_min_wait(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tests/test_tenacity.py", "old_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_exponential_with_min_wait(self) -> None:", "new_string": "        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_
…[197 chars elided]…
-untyped-def]\n                powers.append(other)\n                return int.__pow__(self, other)\n\n        wait = tenacity.wait_exponential(max=40, exp_base=CountingBase(2))\n        self.assertEqual(wait(make_retry_state(7, 0)), 40)\n        self.assertEqual(wait(make_retry_state(10**6, 0)), 40)\n        self.assertEqual(powers, [6])\n\n    def test_exponential_with_min_wait(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short; git diff tenacity/wait.py", "description": "Run tests and show final diff"}
[tool_result] .....................................                                    [100%]
168 passed, 1 skipped, 12 subtests passed in 1.88s
 M tenacity/wait.py
 M tests/test_tenacity.py
diff --git a/tenacity/wait.py b/tenacity/wait.py
index 3b53da2..98e1e5f 100644
--- a/tenacity/wait.py
+++ b/tenacity/wait.py
@@ -15,6 +15,7 @@
 # limitations under the License.
 
 import abc
+import math
 import random
 import typing
 import warnings
@@ -200,9 +201,29 @@ class wait_exponential(wait_base):
         self.ma
…[740 chars elided]…
se) > (
+            math.log(self.max) - math.log(self.multiplier) + 1
+        )
+
     def __call__(self, retry_state: "RetryCallState") -> float:
+        exponent = retry_state.attempt_number - 1
+        if self._exceeds_max(exponent):
+            return self.max
         try:
-            exp = self.exp_base ** (retry_state.attempt_number - 1)
+            exp = self.exp_base**exponent
             result = self.multiplier * exp
         except OverflowError:
             return self.max
[tool_use Bash] {"command": "rm -rf <tmp>/equiv; cd ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164513-performance-wait-exponential-max/base-1 && git status --short", "description": "Remove scratch check script and confirm worktree state"}
[tool_result]  M tenacity/wait.py
 M tests/test_tenacity.py
[assistant] `wait_exponential` now returns `max` once the exponential is past the cap, without computing the power. The project's test suite passes (168 passed, 1 skipped), including a new regression test.

**What changed** (`tenacity/wait.py`):
- A new `_exceeds_max(exponent)` check decides whether `multiplier * exp_base ** exponent` is certainly at or above `max`. It uses a log-space comparison with a margin of 1 (a factor of about e), so float rounding can't flip a result near the cap.
- `__call__` returns `self.max` directly when that check passes. Otherwise it runs the original code unchanged.
- `imp
…[465 chars elided]…
hat case too.

**Verification:**
- I compared the new code against the original formula over about 331,000 combinations of multiplier, max, base, min and attempt number, including edge values such as multiplier 0 or −1, max 0, and a huge `MAX_WAIT`. After the `min > max` fix there were zero mismatches.
- A counting-base test confirms the power is not evaluated past the cap: attempt 10⁶ returns 40 with no power call for it.

**Test added** (`tests/test_tenacity.py`): `test_exponential_with_max_wait_skips_power_past_cap`. I did not modify existing tests.

Changes are uncommitted in the worktree.
