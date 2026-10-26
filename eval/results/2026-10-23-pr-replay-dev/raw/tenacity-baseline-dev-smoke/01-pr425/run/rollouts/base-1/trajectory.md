# trajectory base-1

final message:
`wait_random_exponential` now respects `min`. The sampled wait is drawn from `uniform(self.min, high)` instead of `uniform(0, high)` in `tenacity/wait.py`.

The full suite passes: 124 passed, 1 skipped.

- **Fix:** `high` is still the capped exponential value from `wait_exponential`, which already clamps to `min`, so when `min > high` the sample is exactly `min`. With the default `min=0`, behaviour is unchanged.
- **Regression test:** I added `test_wait_random_exponential_respects_min` in `tests/test_tenacity.py` with `multiplier=1, max=60, min=2`. It checks that every sample is at least 2 across attempts 1, 2, 4 and 9. I didn't run it against the old code, but the old `uniform(0, 2)` would fail the attempt-1 check almost every time.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"random_exponential\" --include=*.py . | head -50", "description": "Find wait_random_exponential definitions and usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"random_exponential\" . --exclude-dir=.git | head -50", "description": "Find wait_random_exponential references"}
[tool_result] tests/test_tenacity.py:461:    def test_wait_random_exponential(self):
tests/test_tenacity.py:462:        fn = tenacity.wait_random_exponential(0.5, 60.0)
tests/test_tenacity.py:475:        fn = tenacity.wait_random_exponential(10, 5)
tests/test_tenacity.py:480:        fn = tenacity.wait_random_exponential()
tests/test_tenacity.py:483:    def test_wait_random_exponential_statistically(self):
tests/test_tenacity.py:484:        fn = tenacity.wait_random_exponential(0.5, 60.0)
tenacity/stop.py:117:
…[148 chars elided]…
ntial for the latter case.
tenacity/wait.py:172:class wait_random_exponential(wait_exponential):
tenacity/wait.py:189:        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
tenacity/__init__.py:67:from .wait import wait_random_exponential  # noqa
tenacity/__init__.py:68:from .wait import wait_random_exponential as wait_full_jitter  # noqa
tenacity/__init__.py:696:    "wait_random_exponential",
doc/source/index.rst:195:    @retry(wait=wait_random_exponential(multiplier=1, max=60))
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tenacity/wait.py"}
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
…[7872 chars elided]…
tial = initial
223	        self.max = max
224	        self.exp_base = exp_base
225	        self.jitter = jitter
226	
227	    def __call__(self, retry_state: "RetryCallState") -> float:
228	        jitter = random.uniform(0, self.jitter)
229	        try:
230	            exp = self.exp_base ** (retry_state.attempt_number - 1)
231	            result = self.initial * exp + jitter
232	        except OverflowError:
233	            result = self.max
234	        return max(0, min(result, self.max))
235	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_tenacity.py", "offset": 455, "limit": 40}
[tool_result] 455	
456	        # Clear and restart retrying.
457	        self.assertRaises(tenacity.RetryError, always_return_1)
458	        self.assertEqual(sleep_intervals, [1.0, 2.0, 3.0, 3.0])
459	        sleep_intervals[:] = []
460	
461	    def test_wait_random_exponential(self):
462	        fn = tenacity.wait_random_exponential(0.5, 60.0)
463	
464	        for _ in range(1000):
465	            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 0, 0.5)
466	            self._assert_inclusive_range(fn
…[891 chars elided]…
  fn(make_retry_state(0, 0))
482	
483	    def test_wait_random_exponential_statistically(self):
484	        fn = tenacity.wait_random_exponential(0.5, 60.0)
485	
486	        attempt = []
487	        for i in range(10):
488	            attempt.append([fn(make_retry_state(i, 0)) for _ in range(4000)])
489	
490	        def mean(lst):
491	            return float(sum(lst)) / float(len(lst))
492	
493	        # skipping attempt 0
494	        self._assert_inclusive_epsilon(mean(attempt[1]), 0.25, 0.02)
[assistant] The cause is in `wait_random_exponential.__call__`: it samples `random.uniform(0, high)` and never reads `self.min`, which `wait_exponential` stores. I'll make the sample start at `self.min`, then add a regression test and run the project checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tenacity/wait.py", "old_string": "        high = super().__call__(retry_state=retry_state)\n        return random.uniform(0, high)", "new_string": "        high = super().__call__(retry_state=retry_state)\n        return random.uniform(self.min, high)"}
[tool_result] The file ~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tenacity/wait.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_tenacity.py", "offset": 494, "limit": 12}
[tool_result] 494	        self._assert_inclusive_epsilon(mean(attempt[1]), 0.25, 0.02)
495	        self._assert_inclusive_epsilon(mean(attempt[2]), 0.50, 0.04)
496	        self._assert_inclusive_epsilon(mean(attempt[3]), 1, 0.08)
497	        self._assert_inclusive_epsilon(mean(attempt[4]), 2, 0.16)
498	        self._assert_inclusive_epsilon(mean(attempt[5]), 4, 0.32)
499	        self._assert_inclusive_epsilon(mean(attempt[6]), 8, 0.64)
500	        self._assert_inclusive_epsilon(mean(attempt[7]), 16, 1.28)
501	        self._assert_inclusive_epsilon(mean(attempt[8]), 30, 2.56)
502	        self._assert_inclusive_epsilon(mean(attempt[9]), 30, 2.56)
503	
504	    def test_wait_exponential_jitter(self):
505	        fn = tenacity.wait_exponential_jitter(max=60)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_tenacity.py", "old_string": "        fn = tenacity.wait_random_exponential()\n        fn(make_retry_state(0, 0))\n\n    def test_wait_random_exponential_statistically(self):", "new_string": "        fn = tenacity.wait_random_exponential()\n    
…[183 chars elided]…
 in range(1000):\n            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 2.0, 2.0)\n            self._assert_inclusive_range(fn(make_retry_state(2, 0)), 2.0, 2.0)\n            self._assert_inclusive_range(fn(make_retry_state(4, 0)), 2.0, 8.0)\n            self._assert_inclusive_range(fn(make_retry_state(9, 0)), 2.0, 60.0)\n\n    def test_wait_random_exponential_statistically(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20", "description": "Run project test suite"}
[tool_result] ..........s................................................. [ 48%]
.................................................................        [100%]
=============================== warnings summary ===============================
tests/test_asyncio.py::TestAsyncio::test_attempt_number_is_correct_for_interleaved_coroutines
  ~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_asyncio.py:43: DeprecationWarning: There is no current event loop
    loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
124 passed, 1 skipped, 1 warning, 12 subtests passed in 1.83s
[assistant] `wait_random_exponential` now respects `min`. The sampled wait is drawn from `uniform(self.min, high)` instead of `uniform(0, high)` in `tenacity/wait.py`.

The full suite passes: 124 passed, 1 skipped.

- **Fix:** `high` is still the capped exponential value from `wait_exponential`, which already clamps to `min`, so when `min > high` the sample is exactly `min`. With the default `min=0`, behaviour is unchanged.
- **Regression test:** I added `test_wait_random_exponential_respects_min` in `tests/test_tenacity.py` with `multiplier=1, max=60, min=2`. It checks that every sample is at least 2 across attempts 1, 2, 4 and 9. I didn't run it against the old code, but the old `uniform(0, 2)` would fail the attempt-1 check almost every time.

I didn't commit anything.
