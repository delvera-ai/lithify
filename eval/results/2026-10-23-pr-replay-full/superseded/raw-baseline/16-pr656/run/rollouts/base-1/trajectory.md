# trajectory base-1

final message:
`wait_exponential` no longer raises `ValueError` when `max / multiplier` underflows to 0.0 or when `multiplier` is `inf`. It returns the capped wait instead. The project test suite passes: 172 passed, 1 skipped.

**The change** (`tenacity/wait.py`)
- The early-return check called `math.log(self.max / self.multiplier, ...)`. When that ratio is 0.0, `math.log` raises "math domain error". I added `self.max / self.multiplier == 0 or ...` ahead of the log call.
- The ratio is 0 only when `multiplier` is greater than `max` by more than the float range (or is `inf`). In that case the first wait, `multiplier * exp_base**0`, already exceeds `max`, so returning `max` is the correct capped value.
- Ordinary values never hit the new branch, since it only fires where the old code raised, so their results are unchanged.

**Tests** (`tests/test_tenacity.py`)
- Added `test_exponential_with_max_smaller_than_multiplier_underflow`: `multiplier=1e300, max=1e-100` returns `1e-100` on attempts 1 and 50.
- Added `test_exponential_with_infinite_multiplier`: `multiplier=math.inf, max=40` returns `40`.
- Added `import math` to the test module for the second test.
- No existing tests were edited.

I did not run the new tests against the unmodified code to confirm they fail there. The reasoning is that `math.log(0.0, 2)` raises `ValueError`, which is the reported bug.

## events
[tool_use Bash] {"command": "grep -n \"class wait_exponential\" -A 60 tenacity/wait.py", "description": "Show wait_exponential implementation"}
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
…[3501 chars elided]…

290-        self.jitter = _utils.to_seconds(jitter)
291-        self.min = _utils.to_seconds(min)
292-
293-    def __call__(self, retry_state: "RetryCallState") -> float:
294-        jitter = random.uniform(0, self.jitter)
295-        try:
296-            exp = self.exp_base ** (retry_state.attempt_number - 1)
297-            result = self.multiplier * exp + jitter
298-        except OverflowError:
299-            result = self.max
300-        return max(max(0, self.min), min(result, self.max))
[assistant] The overflow is in the early-return check: `math.log(self.max / self.multiplier, ...)` gets 0.0 when the ratio underflows (or when `multiplier` is `inf`), and `math.log(0)` raises. I'll look at the existing tests before changing anything.
[tool_use Bash] {"command": "grep -n \"wait_exponential(\" tests/*.py | head -40; grep -n \"def test_wait_exponential\\|def test_.*exponential\" -A 12 tests/test_tenacity.py | head -80", "description": "Find existing wait_exponential tests"}
[tool_result] tests/test_tenacity.py:340:        r = Retrying(wait=tenacity.wait_exponential())
tests/test_tenacity.py:351:        r = Retrying(wait=tenacity.wait_exponential(max=40))
tests/test_tenacity.py:367:        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=ExplodingPower(2)))
tests/test_tenacity.py:371:        r = Retrying(wait=tenacity.wait_exponential(min=20))
tests/test_tenacity.py:383:        r = Retrying(wait=tenacity.wait_exponential(max=50, multiplier=1))
tests/test_tenacity.py:3
…[4482 chars elided]…
= Retrying(wait=tenacity.wait_exponential(min=min_, max=max_))
413-                self.assertEqual(r.wait(make_retry_state(1, 0)), 10)
414-                self.assertEqual(r.wait(make_retry_state(2, 0)), 10)
415-                self.assertEqual(r.wait(make_retry_state(3, 0)), 10)
416-                self.assertEqual(r.wait(make_retry_state(4, 0)), 10)
417-                self.assertEqual(r.wait(make_retry_state(5, 0)), 16)
418-                self.assertEqual(r.wait(make_retry_state(6, 0)), 32)
[assistant] Tests pin the ordinary behaviour, so I'll add a regression test next to them. The fix: when `max / multiplier` underflows to 0 (which also covers `multiplier=inf`), every attempt is already past the cap, because `exp_base**exponent >= 1` makes the first wait `multiplier` alone, which exceeds `max`. So return `max` directly instead of calling `math.log(0)`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py", "old_string": "            and math.isfinite(self.max)\n            and exponent > math.log(self.max / self.multiplier, self.exp_base)\n        ):", "new_string": "            and math.isfinite(self.max)\n            # max / multiplier can underflow to 0.0 (or multiplier can be inf),\n            # in which case even the first wait exceeds max and log() would fail.\n            and (\n                self.max / self.multiplier == 0\n                or exponent > math.log(self.max / self.multiplier, self.exp_base)\n            )\n        ):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py", "old_string": "    def test_exponential_with_min_wait(self) -> None:\n        r = Retrying(wait=tenacity.wait_exponential(min=20))", "new_string": "    def test_exponential_with_max_smaller_than_multiplier_underflow(self) -> None
…[215 chars elided]…
00)\n\n    def test_exponential_with_infinite_multiplier(self) -> None:\n        r = Retrying(wait=tenacity.wait_exponential(multiplier=math.inf, max=40))\n        self.assertEqual(r.wait(make_retry_state(1, 0)), 40)\n        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n\n    def test_exponential_with_min_wait(self) -> None:\n        r = Retrying(wait=tenacity.wait_exponential(min=20))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^import\" tests/test_tenacity.py | head; ls <work>/env-tenacity/bin/python 2>&1; git stash list | head -0", "description": "Check imports and project python exists"}
[tool_result ERROR] Exit code 1
16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
27:import pytest
30:import tenacity
<work>/env-tenacity/bin/python
head: illegal line count -- 0
[assistant] The test file doesn't import `math`, so I'll add it before running the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py", "old_string": "import logging\nimport pickle", "new_string": "import logging\nimport math\nimport pickle"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164934-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git stash list >/dev/null; git -c core.pager=cat diff --stat", "description": "Run project test suite and show diff stat"}
[tool_result] ...............s.................................................................................................................... [ 76%]
.........................................                                [100%]
172 passed, 1 skipped, 12 subtests passed in 1.87s
 tenacity/wait.py       |  7 ++++++-
 tests/test_tenacity.py | 11 +++++++++++
 2 files changed, 17 insertions(+), 1 deletion(-)
[assistant] `wait_exponential` no longer raises `ValueError` when `max / multiplier` underflows to 0.0 or when `multiplier` is `inf`. It returns the capped wait instead. The project test suite passes: 172 passed, 1 skipped.

**The change** (`tenacity/wait.py`)
- The early-return check called `math.log(self.max / self.multiplier, ...)`. When that ratio is 0.0, `math.log` raises "math domain error". I added `self.max / self.multiplier == 0 or ...` ahead of the log call.
- The ratio is 0 only when `multiplier` is greater than `max` by more than the float range (or is `inf`). In that case the first wait, `mul
…[162 chars elided]…
re the old code raised, so their results are unchanged.

**Tests** (`tests/test_tenacity.py`)
- Added `test_exponential_with_max_smaller_than_multiplier_underflow`: `multiplier=1e300, max=1e-100` returns `1e-100` on attempts 1 and 50.
- Added `test_exponential_with_infinite_multiplier`: `multiplier=math.inf, max=40` returns `40`.
- Added `import math` to the test module for the second test.
- No existing tests were edited.

I did not run the new tests against the unmodified code to confirm they fail there. The reasoning is that `math.log(0.0, 2)` raises `ValueError`, which is the reported bug.
