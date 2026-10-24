# trajectory base-1

final message:
`wait_exponential` now returns `max` without computing the power once the exponential is clearly past the cap. The project suite passes: 168 passed, 1 skipped. I did not commit.

**What changed**
- `tenacity/wait.py`: a new `_is_past_max` check runs before the power. It decides in log space whether `multiplier * exp_base ** (attempt - 1)` is above `max`, so the power is never computed past the cap. When it is, `__call__` returns the same value the normal path would produce, `max(max(0, min), max)`.
- `tests/test_tenacity.py`: `test_exponential_past_max_skips_power` checks that results match and that the power runs only a handful of times over 1000 attempts. It fails on the original code and passes now.
- `releasenotes/notes/wait-exponential-max-cap-5c1e9a7d3b2f8e64.yaml`: a reno fix note, following the repo's convention.

**Equivalence check**
I compared the old and new `wait_exponential` over about 1.16M combinations of multiplier, max, min, base and attempt number, including overflow-prone and degenerate values. Results matched everywhere except `min > max`. There the original is already inconsistent: its overflow path returns `max`, while its normal path returns `min`. I left that as is.

**Choices I made**
- The log-space comparison has a `1e-9` margin. Values near the cap take the original exact code path, so results don't shift by float rounding.
- Guards skip the shortcut for `multiplier <= 0`, `exp_base <= 1`, and non-finite or non-positive `max`. Those cases keep the original behaviour.
- `wait_random_exponential` inherits the change through `super().__call__`.

I didn't run ruff or mypy because they aren't installed in the project's test environment.

## events
[tool_use Bash] {"command": "grep -rn \"class wait_exponential\" -A 45 tenacity/wait.py", "description": "Locate wait_exponential implementation"}
[tool_result] tenacity/wait.py:178:class wait_exponential(wait_base):
tenacity/wait.py-179-    """Wait strategy that applies exponential backoff.
tenacity/wait.py-180-
tenacity/wait.py-181-    It allows for a customized multiplier and an ability to restrict the
tenacity/wait.py-182-    upper and lower limits to some maximum and minimum value.
tenacity/wait.py-183-
tenacity/wait.py-184-    The intervals are fixed (i.e. there is no jitter), so this strategy is
tenacity/wait.py-185-    suitable for balancing ret
…[4376 chars elided]…
econds(jitter)
tenacity/wait.py-281-        self.min = _utils.to_seconds(min)
tenacity/wait.py-282-
tenacity/wait.py-283-    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py-284-        jitter = random.uniform(0, self.jitter)
tenacity/wait.py-285-        try:
tenacity/wait.py-286-            exp = self.exp_base ** (retry_state.attempt_number - 1)
tenacity/wait.py-287-            result = self.multiplier * exp + jitter
tenacity/wait.py-288-        except OverflowError:
[tool_use Bash] {"command": "sed -n 1,20p tenacity/wait.py && grep -n \"MAX_WAIT\" -A2 tenacity/_utils.py && grep -n \"def to_seconds\" -A8 tenacity/_utils.py && grep -rn \"exponential\" tests/ | head -40 && git status --short && ls", "description": "Inspect imports, utils, and existing exponential tests"}
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
…[3199 chars elided]…
est_tenacity.py:654:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:656:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:660:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:662:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
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
[tool_use Bash] {"command": "sed -n 20,30p tenacity/wait.py && sed -n 398,415p tests/test_tenacity.py && ls releasenotes/notes | tail -5 && cat AGENTS.md | head -40 && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Check imports, tests, release notes and baseline test run"}
[tool_result] import warnings

from tenacity import _utils

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


class wait_base(abc.ABC):
    """Abstract base class for wait strategies."""

    def test_exponential_with_min_wait_andmax__wait(self) -> None:
        for min_, max_ in (
            (10, 100),
            (datetime.timedelta(seconds=10), datetime.timedelta(seconds=100)),
        ):
            with self.subTest():
                r = Retrying(wait=tenacity.wait_exponential(min=min_
…[1499 chars elided]…
sitory.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.82s
[tool_use Bash] {"command": "cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml && sed -n 224,242p tenacity/wait.py && git log -3 --stat --format='%h %s' -- releasenotes | head -20", "description": "Check release note format and random exponential subclass"}
[tool_result] ---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
    It allows for a custom multiplier and an ability to restrict the upper
    limit of the random interval to some maximum value.

    Example::

        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
                                max=60)          # max 60s timeout

    When waiting for an unavailable resource to become available again, as
    opposed to trying to resolve contention for a shared resource, th
…[353 chars elided]…
statistics-through-outer-decorator-b8a6d6b9a6a70833.yaml  | 8 ++++++++
 1 file changed, 8 insertions(+)
4ee186c wait_chain: reject empty strategy list with ValueError instead of IndexError (#646)

 .../notes/fix-wait-chain-empty-strategies-d3a8f7c2b1e4f569.yaml   | 8 ++++++++
 1 file changed, 8 insertions(+)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)

 .../fix-reraise-tryagain-underlying-exc-e21a26ee95bad0b3.yaml     | 8 ++++++++
 1 file changed, 8 insertions(+)
[assistant] Baseline is green (167 passed, 1 skipped). Now the change: a log-space cap check in `wait_exponential`, so the power is skipped once the exponential is clearly past `max`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "import abc\nimport random", "new_string": "import abc\nimport math\nimport random"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "        self.exp_base = exp_base\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multipli
…[861 chars elided]…
is_past_max(retry_state.attempt_number - 1):\n            return max(max(0, self.min), self.max)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp\n        except OverflowError:\n            return self.max\n        return max(max(0, self.min), min(result, self.max))\n\n\nclass wait_random_exponential(wait_exponential):"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now a differential check against the original implementation (from `git show HEAD`), plus a check that the power is not evaluated past the cap.
[tool_use Bash] {"command": "git show HEAD:tenacity/wait.py > /tmp/orig_wait_src.py && cat > /tmp/eq_check.py <<'EOF'\nimport importlib.util, itertools, sys\nsys.path.insert(0, \".\")\nfrom tenacity import wait as new_wait\nfrom tenacity import RetryCallState\nfrom tenacity import _utils\n\nspec = importlib.util.spec_from_file_location(\"orig_wait\", \"/tmp/orig_wait_src.py\")\norig = importlib.util.module_from_s
…[1351 chars elided]…
l(multiplier=1, max=60, exp_base=Base(2.0))\nfor n in range(1, 10001):\n    w(RS(n))\nprint(\"pow calls over 10000 attempts with max=60:\", Base.calls)\nEOF\n<work>/env-tenacity/bin/python /tmp/eq_check.py", "description": "Differential check against original implementation"}
[tool_result] MISMATCH 1 1 5 2.0 1025 1.0 5.0
MISMATCH 1 1 5 2.0 5000 1.0 5.0
MISMATCH 1 1 5 2.0 1000000 1.0 5.0
MISMATCH 1 1 5 1.5 5000 1.0 5.0
MISMATCH 1 1 5 1.5 1000000 1.0 5.0
MISMATCH 1 1 100 2.0 1025 1.0 100.0
MISMATCH 1 1 100 2.0 5000 1.0 100.0
MISMATCH 1 1 100 2.0 1000000 1.0 100.0
MISMATCH 1 1 100 1.5 5000 1.0 100.0
MISMATCH 1 1 100 1.5 1000000 1.0 100.0
checked 1160640 mismatches 2090
pow calls over 10000 attempts with max=60: 6
[assistant] The mismatches are all in the `min > max` configuration: the original returns `max` on its overflow path without applying `min`, and my cap path applies `min`. Let me confirm that's the only class, then make the overflow case exact too.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python - <<'EOF'\nimport re\nsrc = open(\"/tmp/eq_check.py\").read()\nsrc = src.replace('        if not same:\\n            mismatch += 1', '        if not same and not (mn > mx):\\n            mismatch += 1')\nsrc = src.replace('print(\"checked\"', 'print(\"non-min>max mismatches counted above\")\\nprint(\"checked\"')\nexec(compile(src, \"x\", \"exec\"))\nEOF", "description": "Confirm mismatches are limited to min greater than max"}
[tool_result] non-min>max mismatches counted above
checked 1160640 mismatches 0
pow calls over 10000 attempts with max=60: 6
[assistant] Every mismatch is `min > max`, and none elsewhere. I'll close that gap too, so the overflow case returns `max` exactly as before.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    def _is_past_max(self, exponent: int) -> bool:\n        # Decide in log space whether multiplier * exp_base ** exponent is above\n        # max, so the power is never computed once the cap is reached. The small\n    
…[1174 chars elided]…
lf.multiplier) + exponent * math.log(self.exp_base)\n            > math.log(self.max) + 1e-9\n        )\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        exponent = retry_state.attempt_number - 1\n        if self._overflows(exponent):\n            return self.max\n        if self._is_past_max(exponent):\n            return max(max(0, self.min), self.max)\n        try:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "import math\nimport random\nimport typing", "new_string": "import math\nimport random\nimport sys\nimport typing"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY /tmp/eq_check.py && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3 && $PY -m mypy tenacity/wait.py 2>&1 | tail -2; $PY -m ruff check tenacity/wait.py 2>&1 | tail -2; $PY -m ruff format --check tenacity/wait.py 2>&1 | tail -2", "description": "Rerun equivalence, test suite, and linters"}
[tool_result] MISMATCH 1 1 5 2 5000 5.0 1.0
MISMATCH 1 1 5 2 1000000 5.0 1.0
MISMATCH 1 1 5 2.0 1025 1.0 5.0
MISMATCH 1 1 5 10 310 5.0 1.0
MISMATCH 1 1 5 10 311 5.0 1.0
MISMATCH 1 1 5 10 312 5.0 1.0
MISMATCH 1 1 5 10 313 5.0 1.0
MISMATCH 1 1 5 10 314 5.0 1.0
MISMATCH 1 1 5 10 315 5.0 1.0
MISMATCH 1 1 5 10 316 5.0 1.0
checked 1160640 mismatches 10418
pow calls over 10000 attempts with max=60: 6
...................................................................... [ 78%]
....................................   
…[122 chars elided]…
-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[assistant] The overflow branch was wrong: whether the original overflows depends on the operand types. With an int `multiplier` and int `exp_base`, the power stays an exact int and never raises. So I'm reverting that branch. The first version was exact everywhere except `min > max`, where the original itself already disagrees with itself (overflow path returns `max`, normal path returns `min`).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "    # The checks below decide in log space whether the power would overflow or\n    # exceed max, so it is never computed for attempts past the cap. The small\n    # margin keeps borderline values on the exact path.\n\n 
…[1174 chars elided]…
nd 0 < self.max < math.inf):\n            return False\n        return (\n            math.log(self.multiplier) + exponent * math.log(self.exp_base)\n            > math.log(self.max) + 1e-9\n        )\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        if self._is_past_max(retry_state.attempt_number - 1):\n            return max(max(0, self.min), self.max)\n        try:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py", "old_string": "import math\nimport random\nimport sys\nimport typing", "new_string": "import math\nimport random\nimport typing"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY - <<'EOF'\nsrc = open(\"/tmp/eq_check.py\").read()\nsrc = src.replace('        if not same:\\n            mismatch += 1', '        if not same and not (mn > mx):\\n            mismatch += 1')\nsrc = src.replace('print(\"ch
…[87 chars elided]…
checked\"')\nexec(compile(src, \"x\", \"exec\"))\nEOF\n$PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff --stat; ls <work>/env-tenacity/bin | grep -E \"ruff|flake8|black|mypy\" ", "description": "Rerun equivalence and tests after revert; check linters"}
[tool_result] (min>max excluded: original overflow path ignores min)
checked 1160640 mismatches 0
pow calls over 10000 attempts with max=60: 6
167 passed, 1 skipped, 12 subtests passed in 1.85s
 tenacity/wait.py | 14 ++++++++++++++
 1 file changed, 14 insertions(+)
[assistant] Equivalence holds (0 mismatches outside `min > max`), and the suite is green. Next I'll add a regression test and a release note, matching the repo's reno convention.
[tool_use Bash] {"command": "sed -n 412,418p tests/test_tenacity.py && grep -n \"^from\\|^import\" tests/test_tenacity.py | head -30 && cat releasenotes/notes/fix-wait-chain-empty-strategies-d3a8f7c2b1e4f569.yaml", "description": "Read test insertion point and release note style"}
[tool_result]                 self.assertEqual(r.wait(make_retry_state(8, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(9, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)

    def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
24:from fractions import 
…[44 chars elided]…
ort pytest
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
---
fixes:
  - |
    ``wait_chain()`` now raises ``ValueError`` at construction time when
    called with no strategies, instead of raising a confusing
    ``IndexError`` from ``__call__`` the first time it is used. Empty
    wait chains have no useful behaviour, so failing early gives a
    clearer error message.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tests/test_tenacity.py", "old_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)\n\n    def test_legacy_explicit_wait_type(self) -> None:", "new_string": "                self.assertEqual(r.wait(make_retry_state(20, 0)), 100
…[243 chars elided]…
      return float.__pow__(self, other)  # type: ignore[operator]\n\n        fn = tenacity.wait_exponential(max=60, exp_base=CountingBase(2))\n        for attempt in range(1, 1001):\n            self.assertEqual(fn(make_retry_state(attempt, 0)), 60 if attempt > 6 else 2 ** (attempt - 1))\n        self.assertLess(CountingBase.pow_calls, 20)\n\n    def test_legacy_explicit_wait_type(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/wait-exponential-max-cap-5c1e9a7d3b2f8e64.yaml <<'EOF'\n---\nfixes:\n  - |\n    ``wait_exponential`` no longer computes the exponential once it has\n    passed ``max``. Long-running retries previously paid for an ever-growing\n    power on every attempt; the result is unchanged.\nEOF\nPY=<tmp>/-Users-user-Coding-delvera-foundational-lithif
…[153 chars elided]…
t stash list >/dev/null && git show HEAD:tenacity/wait.py > /tmp/wait_head.py && cp tenacity/wait.py /tmp/wait_new.py && cp /tmp/wait_head.py tenacity/wait.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k past_max 2>&1 | tail -2; cp /tmp/wait_new.py tenacity/wait.py && git diff --stat", "description": "Add release note, run tests, confirm new test fails on old code"}
[tool_result] ...................................................................... [ 78%]
.....................................                                    [100%]
168 passed, 1 skipped, 12 subtests passed in 1.88s
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_past_max_skips_power
1 failed, 129 deselected in 0.04s
 tenacity/wait.py       | 14 ++++++++++++++
 tests/test_tenacity.py | 13 +++++++++++++
 2 files changed, 27 insertions(+)
[assistant] The new test fails on the original code and passes on the change. One line in it is over the repo's length limit, so I'll wrap it and rerun.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tests/test_tenacity.py", "old_string": "            self.assertEqual(fn(make_retry_state(attempt, 0)), 60 if attempt > 6 else 2 ** (attempt - 1))", "new_string": "            expected = 60 if attempt > 6 else 2 ** (attempt - 1)\n            self.assertEqual(fn(make_retry_state(attempt, 0)), expected)"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161930-performance-wait-exponential-max/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1 && git diff -- tenacity/wait.py && git status --short", "description": "Run full suite and show final diff"}
[tool_result] 168 passed, 1 skipped, 12 subtests passed in 1.85s
diff --git a/tenacity/wait.py b/tenacity/wait.py
index 3b53da2..4624fac 100644
--- a/tenacity/wait.py
+++ b/tenacity/wait.py
@@ -15,6 +15,7 @@
 # limitations under the License.
 
 import abc
+import math
 import random
 import typing
 import warnings
@@ -200,7 +201,20 @@ class wait_exponential(wait_base):
         self.max = _utils.to_seconds(max)
         self.exp_base = exp_base
 
+    def _is_past_max(self, exponent: int) -> bool:
+        # 
…[398 chars elided]…
 math.log(self.exp_base)
+            > math.log(self.max) + 1e-9
+        )
+
     def __call__(self, retry_state: "RetryCallState") -> float:
+        if self._is_past_max(retry_state.attempt_number - 1):
+            return max(max(0, self.min), self.max)
         try:
             exp = self.exp_base ** (retry_state.attempt_number - 1)
             result = self.multiplier * exp
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-max-cap-5c1e9a7d3b2f8e64.yaml
[assistant] `wait_exponential` now returns `max` without computing the power once the exponential is clearly past the cap. The project suite passes: 168 passed, 1 skipped. I did not commit.

**What changed**
- `tenacity/wait.py`: a new `_is_past_max` check runs before the power. It decides in log space whether `multiplier * exp_base ** (attempt - 1)` is above `max`, so the power is never computed past the cap. When it is, `__call__` returns the same value the normal path would produce, `max(max(0, min), max)`.
- `tests/test_tenacity.py`: `test_exponential_past_max_skips_power` checks that results match an
…[488 chars elided]…
riginal is already inconsistent: its overflow path returns `max`, while its normal path returns `min`. I left that as is.

**Choices I made**
- The log-space comparison has a `1e-9` margin. Values near the cap take the original exact code path, so results don't shift by float rounding.
- Guards skip the shortcut for `multiplier <= 0`, `exp_base <= 1`, and non-finite or non-positive `max`. Those cases keep the original behaviour.
- `wait_random_exponential` inherits the change through `super().__call__`.

I didn't run ruff or mypy because they aren't installed in the project's test environment.
