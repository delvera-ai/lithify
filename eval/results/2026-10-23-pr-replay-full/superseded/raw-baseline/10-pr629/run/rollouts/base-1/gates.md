GATES: PASS — test=pass

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 0 (1.9s)
............s............................................... [ 38%]
........................................................................ [ 85%]
.......................                                                  [100%]
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:612: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
    fn = tenacity.wait_exponential_jitter(10, 5)

tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
  ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:621: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
154 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.81s

