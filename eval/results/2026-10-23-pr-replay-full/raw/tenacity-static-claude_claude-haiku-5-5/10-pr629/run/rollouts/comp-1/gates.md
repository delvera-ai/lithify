GATES: PASS — test=pass

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 0 (1.9s)
............s............................................... [ 37%]
........................................................................ [ 81%]
.............................                                            [100%]
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/comp-1/tests/test_tenacity.py:613: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
    fn = tenacity.wait_exponential_jitter(10, 5)

tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
  ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/comp-1/tests/test_tenacity.py:622: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
160 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.79s

