# trajectory base-1

final message:
Fixed disabled sync and async iterators to run exactly once and propagate the original exception unchanged.

Added regression coverage for success, exceptions, `TryAgain`, controller reuse, and both context-manager forms.

Tests: 164 passed, 1 skipped. Ruff was unavailable in the project environment.

## events
[assistant] I’ll compare the iterator and decorator paths, fix the disabled behavior, and run the project’s tests.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*retry*' -g 'pyproject.toml' -g 'tox.ini' -g 'setup.cfg'"
~/.cache/lithify/work/repo-553f5f2e6879/20261023-201506-bug-retrying-enabled-false-is-ig/base-1
releasenotes/notes/retrycallstate-repr-94947f7b00ee15e1.yaml
releasenotes/notes/fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml
releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml
releasenotes/notes/fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
AGENTS.md
pyproject.toml
tenacity/retry.py
tenacity/asyncio/retry.py

[command exit=0] /bin/zsh -lc "rtk rg -n 'enabled|def __iter__|def __next__|AttemptManager|def __aiter__|def __anext__' tenacity tests"
tenacity/asyncio/__init__.py:24:    AttemptManager,
tenacity/asyncio/__init__.py:94:        enabled: bool = True,
tenacity/asyncio/__init__.py:108:            enabled=enabled,
tenacity/asyncio/__init__.py:165:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:168:    def __aiter__(self) -> "AsyncRetrying":
tenacity/asyncio/__init__.py:173:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:179:                return AttemptMa
…[1814 chars elided]…
  enabled: bool | object = _unset,
tenacity/__init__.py:299:            enabled=_first_set(enabled, self.enabled),
tenacity/__init__.py:367:            if not self.enabled:
tenacity/__init__.py:477:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/__init__.py:484:                yield AttemptManager(retry_state=retry_state)
tenacity/__init__.py:693:    enabled: bool = ...,
tenacity/__init__.py:711:    enabled: bool = True,
tenacity/__init__.py:761:    "AttemptManager",

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc 'rtk cat pyproject.toml'
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "tenacity/_version.py"

[project]
name = "tenacity"
dynamic = ["version"]
description = "Retry code until it succeeds"
readme = "README.rst"
license = "Apache-2.0"
requires-python = ">=3.10"
authors = [
    { name = "Julien Danjou", email = "julien@danjou.info" },
]
classifiers = [
    "Intended Audience :: Developers",
    "Prog
…[2204 chars elided]…
ions
    "RUF003",  # ambiguous unicode characters in comments (copyright names)
    "RUF005",  # iterable unpacking vs concatenation (less readable for tuple +)
    "RUF012",  # mutable class default (test constant, never mutated)
    "SIM108",  # ternary instead of if-else (less readable in context)
]

[tool.mypy]
strict = true
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]

[[tool.mypy.overrides]]
module = "tornado.*"
ignore_missing_imports = true


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '200,240p;350,385p;470,505p' tenacity/__init__.py"
        return f"{self.__class__.__name__}[{self.last_attempt}]"


class AttemptManager:
    """Manage attempt context."""

    def __init__(self, retry_state: "RetryCallState"):
        self.retry_state = retry_state

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: "types.TracebackType | None",
    ) -> bool | None:
        if exc_type is not None and exc_valu
…[2614 chars elided]…
   yield AttemptManager(retry_state=retry_state)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                self.sleep(do)
            else:
                break

    @abstractmethod
    def __call__(
        self,
        fn: t.Callable[..., WrappedFnReturnT],
        *args: t.Any,
        **kwargs: t.Any,
    ) -> WrappedFnReturnT:
        pass


class Retrying(BaseRetrying):
    """Retrying controller."""

    def __call__(
        self,

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '150,215p' tenacity/asyncio/__init__.py"
        retry_state.upcoming_sleep = sleep

    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
            retry_state
        )

    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
    
…[1713 chars elided]…
tistics = copy.statistics
            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]

        # Preserve attributes
        async_wrapped.retry = self  # type: ignore[attr-defined]
        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]
        async_wrapped.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
    "AsyncRetrying",
    "WrappedFn",
    "retry_all",
    "retry_any",

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1480,1580p' tests/test_tenacity.py"
                }
                self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)
                self.assertEqual(exc.last_attempt.attempt_number, 1)
                self.assertEqual(
                    _retryable_test_with_stop.retry.statistics, expected_stats
                )
            else:
                self.fail("RetryError should have been raised after 1 attempt")


class TestStatisticsKeys:
    def test_delay_since_first_attempt_available_on_first_attempt(sel
…[2537 chars elided]…
wait(self) -> None:
        start = current_time_ms()
        result = _retryable_test_with_wait.retry_with(wait=tenacity.wait_fixed(0.1))(
            NoneReturnUntilAfterCount(5)
        )
        t = current_time_ms() - start
        assert t >= 500
        assert result is True

    def test_redefine_stop(self) -> None:
        result = _retryable_test_with_stop.retry_with(
            stop=tenacity.stop_after_attempt(5)
        )(NoneReturnUntilAfterCount(4))
        assert result is True


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '130,260p' tests/test_asyncio.py"
        self.assertEqual(
            function_with_kwdefaults.__kwdefaults__,
            wrapped_kwdefaults_function.__kwdefaults__,  # type: ignore[attr-defined]
        )

    @asynctest
    async def test_attempt_number_is_correct_for_interleaved_coroutines(self) -> None:
        attempts: list[Any] = []

        def after(retry_state: RetryCallState) -> None:
            attempts.append((retry_state.args[0], retry_state.attempt_number))

        thing1 = NoIOErrorAfterCount(3)
        thin
…[3200 chars elided]…
Exception):
            pass

        async def _test() -> None:
            try:
                raise UnderlyingError("boom")
            except UnderlyingError:
                # Implicit chaining via __context__ is exactly what we test.
                raise tenacity.TryAgain  # noqa: B904

        retrying = tasyncio.AsyncRetrying(
            stop=stop_after_attempt(2),
            retry=tenacity.retry_never,
            reraise=True,
        )
        with pytest.raises(UnderlyingError):

[assistant] The iterators always enter the retry machinery, and the attempt context manager always suppresses exceptions. I’ll add a single-attempt path for disabled iterators and let exceptions pass through the context manager unchanged. Regression tests will cover both iterator types and both context-manager forms.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p = Path('tenacity/__init__.py')
s = p.read_text().replace('''        if exc_type is not None and exc_value is not None:
            se
…[1094 chars elided]…
              raise StopAsyncIteration
            self._disabled_attempt_yielded = True
            return AttemptManager(retry_state=self._retry_state)
        while True:
''',1)
p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p = Path('tests/test_tenacity.py')
s=p.read_text().replace('''class TestEnabled:
''','''class TestEnabled:
    @pytest.mark.parametrize
…[2346 chars elided]…
est.raises(type(error)) as exc_info:
                            await run()
                        assert exc_info.value is error
                    assert attempts == 1

''',1)
p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.............s...................................................................................................................... [ 80%]
.................................                                        [100%]
164 passed, 1 skipped, 12 subtests passed in 1.87s

[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py         |  5 +++++
 tenacity/asyncio/__init__.py |  6 ++++++
 tests/test_asyncio.py        | 34 ++++++++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 28 ++++++++++++++++++++++++++++
 4 files changed, 73 insertions(+)

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m ruff check tenacity/__init__.py tenacity/asyncio/__init__.py tests/test_tenacity.py tests/test_asyncio.py'
<work>/env-tenacity/bin/python: No module named ruff

[assistant] Fixed disabled sync and async iterators to run exactly once and propagate the original exception unchanged.

Added regression coverage for success, exceptions, `TryAgain`, controller reuse, and both context-manager forms.

Tests: 164 passed, 1 skipped. Ruff was unavailable in the project environment.
