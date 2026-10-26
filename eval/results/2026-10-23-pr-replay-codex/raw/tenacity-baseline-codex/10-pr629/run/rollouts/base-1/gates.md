GATES: PASS — test=pass

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 0 (1.9s)
............s............................................... [ 37%]
........................................................................ [ 83%]
..........................                                               [100%]
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201304-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:612: DeprecationWarning: initial is deprecated; use multiplier instead
    fn = tenacity.wait_exponential_jitter(10, 5)

tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
  ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201304-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:645: DeprecationWarning: initial is deprecated; use multiplier instead
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
157 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.77s

