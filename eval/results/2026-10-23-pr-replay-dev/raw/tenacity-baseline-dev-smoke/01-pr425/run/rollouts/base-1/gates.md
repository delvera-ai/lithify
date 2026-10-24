GATES: PASS — test=pass

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 0 (1.9s)
..........s................................................. [ 48%]
.................................................................        [100%]
=============================== warnings summary ===============================
tests/test_asyncio.py::TestAsyncio::test_attempt_number_is_correct_for_interleaved_coroutines
  ~/.cache/lithify/work/repo-55b1cd98de98/20261023-154911-bug-wait-random-exponential-min/base-1/tests/test_asyncio.py:43: DeprecationWarning: There is no current event loop
    loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
124 passed, 1 skipped, 1 warning, 12 subtests passed in 1.81s

