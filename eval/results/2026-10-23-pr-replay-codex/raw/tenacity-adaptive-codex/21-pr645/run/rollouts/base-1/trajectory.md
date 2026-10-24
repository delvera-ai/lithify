# trajectory base-1

final message:
Fixed both direct-call paths to honor `enabled=False`: they call once and propagate the original exception unchanged. The async version awaits coroutine functions.

Added regression coverage for arguments, return values, call counts, and exception identity.

Validation: 181 passed, 1 skipped, 15 subtests passed. Diff checks passed.

## events
[assistant] I’ll check how `enabled` is handled in each call path, add the smallest fix with regression tests, and run the project’s checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*retry*' -g 'test*' -g 'pyproject.toml' -g 'tox.ini' -g 'setup.cfg'"
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```
~/.ca
…[260 chars elided]…
22bd544800cd1f36.yaml
releasenotes/notes/fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
AGENTS.md
tenacity/asyncio/retry.py
tenacity/retry.py
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/test_utils.py
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk rg -n 'enabled|def __call__|class Retrying' tenacity/__init__.py tenacity/asyncio/__init__.py tests/test_tenacity.py tests/test_asyncio.py"
tests/test_asyncio.py:203:    async def test_enabled_false_skips_retry(self) -> None:
tests/test_asyncio.py:204:        """When enabled=False, async function is called directly without retrying."""
tests/test_asyncio.py:207:        @retry(enabled=False, stop=stop_after_attempt(3))
tests/test_asyncio.py:218:    async def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests
…[2969 chars elided]…
y:1711:        """When enabled=False, the iterator protocol raises the original exception,
tests/test_tenacity.py:1715:            enabled=False,
tests/test_tenacity.py:1726:    def test_enabled_false_iter_succeeds_on_first_attempt(self) -> None:
tests/test_tenacity.py:1727:        """When enabled=False, the iterator protocol runs the body once and stops."""
tests/test_tenacity.py:1730:            enabled=False,
tests/test_tenacity.py:2295:            def __call__(self, seconds: float) -> None:

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '490,570p' tenacity/__init__.py"
            self.statistics["idle_for"] += sleep
            self.statistics["attempt_number"] += 1

        self._add_action_func(next_action)

        if self.before_sleep is not None:
            self._add_action_func(self.before_sleep)

        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))

    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
        if not self.enabled:
            retry_state = RetryCallState(self, fn=None, args=(), kwargs={})
            yield
…[1673 chars elided]…
      self.sleep(do)
            else:
                return do  # type: ignore[no-any-return]


class Future(futures.Future[t.Any]):
    """Encapsulates a (future or past) attempted call to a target function."""

    def __init__(self, attempt_number: int) -> None:
        super().__init__()
        self.attempt_number = attempt_number

    @property
    def failed(self) -> bool:
        """Return whether a exception is being held in this future."""
        return self.exception() is not None

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '110,150p' tenacity/asyncio/__init__.py"
        )

    @override
    async def __call__(  # type: ignore[override]
        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        is_async = _utils.is_coroutine_callable(fn)
        while True:
            do = await self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
                try:
                    if is_async:
  
…[641 chars elided]…
> None:
        self.iter_state.actions.append(_utils.wrap_to_async_func(fn))

    @override
    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.iter_state.retry_run_result = await _utils.wrap_to_async_func(self.retry)(
            retry_state
        )

    @override
    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        # See BaseRetrying._run_wait: falsy `wait` values mean "no wait" and

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '175,250p' tests/test_asyncio.py"
        attempts: list[Any] = []

        def after(retry_state: RetryCallState) -> None:
            attempts.append((retry_state.args[0], retry_state.attempt_number))

        thing1 = NoIOErrorAfterCount(3)
        thing2 = NoIOErrorAfterCount(3)

        await asyncio.gather(
            _retryable_coroutine.retry_with(after=after)(thing1),
            _retryable_coroutine.retry_with(after=after)(thing2),
        )

        # There's no waiting on retry, only a wait in the coroutine, so the

…[1685 chars elided]…
n enabled=False, the async iterator runs the body once and stops."""
        call_count = 0
        retrying = AsyncRetrying(
            enabled=False,
            stop=stop_after_attempt(5),
        )
        async for attempt in retrying:
            with attempt:
                call_count += 1
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
class TestTrio(unittest.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1640,1745p' tests/test_tenacity.py"

            return typing.cast("_F", wrapper)

        @outer
        @retry(stop=tenacity.stop_after_attempt(3))
        def my_call() -> str:
            return "ok"

        assert my_call() == "ok"
        assert my_call.statistics["attempt_number"] == 1
        assert my_call.statistics is my_call.__wrapped__.statistics


class TestEnabled:
    def test_enabled_false_skips_retry(self) -> None:
        """When enabled=False, the function is called directly without retrying."""
        call_
…[2577 chars elided]…
ying = Retrying(
            enabled=False,
            stop=tenacity.stop_after_attempt(5),
            wait=tenacity.wait_none(),
        )
        for attempt in retrying:
            with attempt:
                call_count += 1
        assert call_count == 1


class TestRetryWith:
    def test_redefine_wait(self) -> None:
        start = current_time_ms()
        result = _retryable_test_with_wait.retry_with(wait=tenacity.wait_fixed(0.1))(
            NoneReturnUntilAfterCount(5)
        )

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_tenacity.py')
s=p.read_text(); marker='class TestEnabled:\\n'
s=s.replace(marker,marker+'''    def test_enabled_fals
…[1479 chars elided]…
            assert calls == [\"failure\"]
            assert await retrying(fn, \"success\", fail=False) == \"success\"
            assert calls == [\"failure\", \"success\"]

''');p.write_text(s)
PY"

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py tests/test_asyncio.py -k enabled_false_direct_call'
FF                                                                       [100%]
=================================== FAILURES ===================================
__________________ TestEnabled.test_enabled_false_direct_call __________________

value = 'failure', fail = True

    def fn(value: str, *, fail: bool) -> str:
        calls.append(value)
        if fail:
>           raise error

tests/test_tenacity.py:1661: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
…[4605 chars elided]…
lf.reraise:
            retry_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x106fa1850 state=finished raised ValueError>]

tenacity/__init__.py:481: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call - ...
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call
2 failed, 168 deselected in 0.42s

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/__init__.py');s=p.read_text();start=s.index('class Retrying(BaseRetrying):');s=s[:start]+s[start:].replace('        se
…[312 chars elided]…
led:\\n            if _utils.is_coroutine_callable(fn):\\n                return await fn(*args, **kwargs)\\n            return fn(*args, **kwargs)\\n\\n        self.begin()\\n',1);p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.................s.............................................. [ 35%]
................................................................. [ 70%]
.....................................................                    [100%]
181 passed, 1 skipped, 15 subtests passed in 1.81s

[assistant] The regression tests reproduced both failures. Both direct-call methods now bypass the retry loop when disabled, and the async version awaits coroutine functions. The tests check that each call runs once, receives its arguments, returns its result, and propagates the same exception object. The full suite is running.
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed both direct-call paths to honor `enabled=False`: they call once and propagate the original exception unchanged. The async version awaits coroutine functions.

Added regression coverage for arguments, return values, call counts, and exception identity.

Validation: 181 passed, 1 skipped, 15 subtests passed. Diff checks passed.
