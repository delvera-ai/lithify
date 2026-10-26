# trajectory base-1

final message:
`wait_exponential` now returns the capped wait in both failing cases instead of raising `ValueError: math domain error`. The full suite passes: 172 passed, 1 skipped.

**The cause:** the early-return check computed `math.log(max / multiplier, exp_base)`. When `max / multiplier` underflows to 0.0 (for example `multiplier=1e300, max=1e-100`), or when `multiplier` is `inf`, `math.log(0.0)` raises.

**The fix** (`tenacity/wait.py`): the ratio is computed once, and a zero ratio returns the cap directly. A zero ratio means `multiplier` is far larger than `max`, so the cap applies on every attempt. Ordinary values take the same path as before.

**Tests** (`tests/test_tenacity.py`): I added two regression tests next to the existing exponential tests, one for the underflowing ratio and one for an infinite multiplier. Both raised `ValueError` before the change. I used `float("inf")` in the test rather than adding a `math` import.

I haven't committed the change.

## events
[tool_use Bash] {"command": "grep -n \"class wait_exponential\" -A 60 tenacity/wait.py && git log -1 --format=%H -- tenacity/wait.py && ls", "description": "Show wait_exponential implementation and repo layout"}
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
…[3638 chars elided]…
state: "RetryCallState") -> float:
294-        jitter = random.uniform(0, self.jitter)
295-        try:
296-            exp = self.exp_base ** (retry_state.attempt_number - 1)
297-            result = self.multiplier * exp + jitter
298-        except OverflowError:
299-            result = self.max
300-        return max(max(0, self.min), min(result, self.max))
29d398bd21af492abeecd9fc9d33c48dc4d5fc08
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
[tool_use Bash] {"command": "ls <work>/env-tenacity/bin/python; PY=<work>/env-tenacity/bin/python; PYTHONPATH=. $PY -c \"\nfrom tenacity import wait_exponential\nfrom t
…[44 chars elided]…
def st(n):\n    class S: attempt_number=n\n    return S()\nfor kw in [dict(multiplier=1e300,max=1e-100), dict(multiplier=float('inf'),max=10), dict(multiplier=1,max=10)]:\n    w=wait_exponential(**kw)\n    for n in (1,2,5):\n        try: print(kw,n,w(st(n)))\n        except Exception as e: print(kw,n,'ERR',repr(e))\n\"; git status --short", "description": "Reproduce the wait_exponential failures"}
[tool_result] <work>/env-tenacity/bin/python
{'multiplier': 1e+300, 'max': 1e-100} 1 ERR ValueError('math domain error')
{'multiplier': 1e+300, 'max': 1e-100} 2 ERR ValueError('math domain error')
{'multiplier': 1e+300, 'max': 1e-100} 5 ERR ValueError('math domain error')
{'multiplier': inf, 'max': 10} 1 ERR ValueError('math domain error')
{'multiplier': inf, 'max': 10} 2 ERR ValueError('math domain error')
{'multiplier': inf, 'max': 10} 5 ERR ValueError('math domain error')
{'multiplier': 1, 'max': 10} 1 1
{'multiplier': 1, 'max': 10} 2 2
{'multiplier': 1, 'max': 10} 5 10.0
[assistant] The failure is reproduced: when `max / multiplier` underflows to 0.0 (or `multiplier` is `inf`), `math.log(0.0)` raises. In that case the true ratio is positive but below float range, so the cap already applies at every attempt. I'll return the cap for a zero ratio instead of taking the log.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py", "old_string": "        exponent = retry_state.attempt_number - 1\n        if (\n            self.multiplier > 0\n            and self.max > 0\n            and self.exp_base > 1\n            and math.isfinite(self.max)\n            and 
…[315 chars elided]…
 > 1\n            and math.isfinite(self.max)\n        ):\n            # A zero ratio means max/multiplier underflowed (e.g. multiplier is\n            # inf or huge), so the cap is reached on every attempt.\n            ratio = self.max / self.multiplier\n            if ratio == 0 or exponent > math.log(ratio, self.exp_base):\n                return max(max(0, self.min), self.max)\n        try:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `wait_exponential` tests, then run the suite.
[tool_use Bash] {"command": "grep -n \"wait_exponential\" tests/*.py | head -40", "description": "Find existing wait_exponential tests"}
[tool_result] tests/test_tenacity.py:340:        r = Retrying(wait=tenacity.wait_exponential())
tests/test_tenacity.py:351:        r = Retrying(wait=tenacity.wait_exponential(max=40))
tests/test_tenacity.py:367:        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=ExplodingPower(2)))
tests/test_tenacity.py:371:        r = Retrying(wait=tenacity.wait_exponential(min=20))
tests/test_tenacity.py:383:        r = Retrying(wait=tenacity.wait_exponential(max=50, multiplier=1))
tests/test_tenacity.py:3
…[967 chars elided]…
ty.py:656:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:662:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:664:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:668:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:670:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
[tool_use Bash] {"command": "sed -n 336,400p tests/test_tenacity.py", "description": "Read existing wait_exponential tests"}
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
…[2560 chars elided]…
f.assertEqual(r.wait(make_retry_state(50, 0)), 50)

    def test_exponential_with_min_wait_and_multiplier(self) -> None:
        r = Retrying(wait=tenacity.wait_exponential(min=20, multiplier=2))
        self.assertEqual(r.wait(make_retry_state(1, 0)), 20)
        self.assertEqual(r.wait(make_retry_state(2, 0)), 20)
        self.assertEqual(r.wait(make_retry_state(3, 0)), 20)
        self.assertEqual(r.wait(make_retry_state(4, 0)), 20)
        self.assertEqual(r.wait(make_retry_state(5, 0)), 32)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py", "old_string": "        r = Retrying(wait=tenacity.wait_exponential(max=40, exp_base=ExplodingPower(2)))\n        self.assertEqual(r.wait(make_retry_state(50, 0)), 40)\n", "new_string": "        r = Retrying(wait=tenacity.wait_exp
…[372 chars elided]…
ertEqual(r.wait(make_retry_state(1, 0)), 1e-100)\n        self.assertEqual(r.wait(make_retry_state(5, 0)), 1e-100)\n\n    def test_exponential_infinite_multiplier_returns_max(self) -> None:\n        r = Retrying(wait=tenacity.wait_exponential(multiplier=math.inf, max=40))\n        self.assertEqual(r.wait(make_retry_state(1, 0)), 40)\n        self.assertEqual(r.wait(make_retry_state(5, 0)), 40)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^import math\\|^import\" tests/test_tenacity.py | head; PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the test suite with the project's command"}
[tool_result] 16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
27:import pytest
30:import tenacity
.........................................                                [100%]
=================================== FAILURES ===================================
_____ TestWaitConditions.test_exponential_infinite_multiplier_returns_max ______

self = <tests.test_tenacity.TestWaitConditions testMethod=test_exponential_infinit
…[108 chars elided]…
 = Retrying(wait=tenacity.wait_exponential(multiplier=math.inf, max=40))
                                                               ^^^^
E       NameError: name 'math' is not defined. Did you forget to import 'math'

tests/test_tenacity.py:377: NameError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_exponential_infinite_multiplier_returns_max
1 failed, 171 passed, 1 skipped, 12 subtests passed in 1.95s
[assistant] The test file doesn't import `math`, so I'll use `float("inf")` rather than add an import.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py", "old_string": "multiplier=math.inf, max=40))", "new_string": "multiplier=float(\"inf\"), max=40))"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162702-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git diff --stat", "description": "Rerun test suite and show diff stats"}
[tool_result] ...............s.................................................................................................................... [ 76%]
.........................................                                [100%]
172 passed, 1 skipped, 12 subtests passed in 1.87s
 tenacity/wait.py       |  7 +++++--
 tests/test_tenacity.py | 11 +++++++++++
 2 files changed, 16 insertions(+), 2 deletions(-)
[assistant] `wait_exponential` now returns the capped wait in both failing cases instead of raising `ValueError: math domain error`. The full suite passes: 172 passed, 1 skipped.

**The cause:** the early-return check computed `math.log(max / multiplier, exp_base)`. When `max / multiplier` underflows to 0.0 (for example `multiplier=1e300, max=1e-100`), or when `multiplier` is `inf`, `math.log(0.0)` raises.

**The fix** (`tenacity/wait.py`): the ratio is computed once, and a zero ratio returns the cap directly. A zero ratio means `multiplier` is far larger than `max`, so the cap applies on every attempt. Ordinary values take the same path as before.

**Tests** (`tests/test_tenacity.py`): I added two regression tests next to the existing exponential tests, one for the underflowing ratio and one for an infinite multiplier. Both raised `ValueError` before the change. I used `float("inf")` in the test rather than adding a `math` import.

I haven't committed the change.
