GATES: FAIL — test=FAIL(1)

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 1 (2.2s)
      return 0.5
    
        for wait, expected in (
            (EmptyContainerWait(), 0.25),
            (FalseBoolWait(), 0.5),
        ):
            with self.subTest(wait=type(wait).__name__):
                r = Retrying(wait=wait, stop=tenacity.stop_after_attempt(2))
                r.begin()
                retry_state = RetryCallState(r, lambda: None, (), {})
                r.iter(retry_state)
>               self.assertEqual(retry_state.upcoming_sleep, expected)
E               AssertionError: 0.0 != 0.25

tests/test_tenacity.py:556: AssertionError
_ TestWaitConditions.test_falsy_callable_wait_is_still_called (wait='FalseBoolWait') _

self = <tests.test_tenacity.TestWaitConditions testMethod=test_falsy_callable_wait_is_still_called>

    def test_falsy_callable_wait_is_still_called(self) -> None:
        # A callable wait strategy is only "no wait" if it is None or 0. An
        # empty container or a `__bool__` returning False must still be called.
        class EmptyContainerWait(list):  # type: ignore[type-arg]
            def __call__(self, retry_state: RetryCallState) -> float:
                return 0.25
    
        class FalseBoolWait:
            def __bool__(self) -> bool:
                return False
    
            def __call__(self, retry_state: RetryCallState) -> float:
                return 0.5
    
        for wait, expected in (
            (EmptyContainerWait(), 0.25),
            (FalseBoolWait(), 0.5),
        ):
            with self.subTest(wait=type(wait).__name__):
                r = Retrying(wait=wait, stop=tenacity.stop_after_attempt(2))
                r.begin()
                retry_state = RetryCallState(r, lambda: None, (), {})
                r.iter(retry_state)
>               self.assertEqual(retry_state.upcoming_sleep, expected)
E               AssertionError: 0.0 != 0.5

tests/test_tenacity.py:556: AssertionError
=========================== short test summary info ============================
SUBFAILED(wait='EmptyContainerWait') tests/test_asyncio.py::TestAsyncio::test_falsy_callable_wait_is_still_called
SUBFAILED(wait='FalseBoolWait') tests/test_asyncio.py::TestAsyncio::test_falsy_callable_wait_is_still_called
SUBFAILED(wait='EmptyContainerWait') tests/test_tenacity.py::TestWaitConditions::test_falsy_callable_wait_is_still_called
SUBFAILED(wait='FalseBoolWait') tests/test_tenacity.py::TestWaitConditions::test_falsy_callable_wait_is_still_called
4 failed, 185 passed, 1 skipped, 15 subtests passed in 2.00s

