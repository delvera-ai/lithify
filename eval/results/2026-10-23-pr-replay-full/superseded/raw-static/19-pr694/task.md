Three regressions that only appear once a retry actually happens:
1. `Retrying(wait=None)`, `wait=0` and `wait=sum([])` now raise `TypeError: 'NoneType' object is not callable`; these values mean "no wait" and must work again (sync and async).
2. Adding a plain callable to a wait strategy (`my_callable + wait_fixed(1)`) must produce a `wait_combine` that sums both.
3. `wait_combine` must pass the retry state to its strategies positionally, so plain callables with any parameter name work.
