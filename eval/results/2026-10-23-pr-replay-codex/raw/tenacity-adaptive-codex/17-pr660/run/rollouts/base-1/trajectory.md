# trajectory base-1

final message:
Fixed cause-chain traversal to stop when it revisits an exception, using identity tracking.

Added regression coverage for cyclic and non-cyclic chains, matching causes, and stop-condition execution.

Validation: 173 passed, 1 skipped; all 28 subtests passed.

## events
[assistant] I’ll inspect the cause-chain predicate, add cycle detection and regression tests, then run the project’s checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; rg -n 'retry_if_exception_cause_type' .; rg --files -g AGENTS.md -g pyproject.toml -g tox.ini -g setup.cfg"
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
./releasenotes/not
…[213 chars elided]…
8ace4ae0ad.yaml:4:    Add a new `retry_base` class called `retry_if_exception_cause_type` that
./tenacity/retry.py:160:class retry_if_exception_cause_type(retry_base):
./tenacity/__init__.py:49:    retry_if_exception_cause_type,
./tenacity/__init__.py:803:    "retry_if_exception_cause_type",
./tests/test_tenacity.py:1170:@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
./tests/test_tenacity.py:1433:    def test_retry_if_exception_cause_type(self) -> None:
AGENTS.md
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '130,205p' tenacity/retry.py"


class retry_unless_exception_type(retry_if_exception):
    """Retries until an exception is raised of one or more types."""

    def __init__(
        self,
        exception_types: type[BaseException]
        | tuple[type[BaseException], ...] = Exception,
    ) -> None:
        self.exception_types = exception_types
        super().__init__(self._check)

    def _check(self, e: BaseException) -> bool:
        return not isinstance(e, self.exception_types)

    def __call__(self, retry_state: 
…[1527 chars elided]…
elf, predicate: typing.Callable[[typing.Any], bool]) -> None:
        self.predicate = predicate

    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        if not retry_state.outcome.failed:
            return self.predicate(retry_state.outcome.result())
        return False


class retry_if_not_result(retry_base):
    """Retries if the result refutes a predicate."""


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1380,1505p' tests/test_tenacity.py"
        except RetryError as e:
            self.assertTrue(isinstance(e, RetryError))
            print(e)

    def test_retry_if_exception_message(self) -> None:
        try:
            self.assertTrue(
                _retryable_test_if_exception_message_message(NoCustomErrorAfterCount(3))
            )
        except CustomError:
            print(_retryable_test_if_exception_message_message.statistics)
            self.fail("CustomError should've been retried from errormessage")

    def t
…[3877 chars elided]…
n be modified to change its behaviour (useful to patch in tests)
        - retry object statistics are synced with function statistics
        """

        self.assertTrue(_retryable_test_with_stop(NoneReturnUntilAfterCount(2)))

        expected_stats = {
            "attempt_number": 3,
            "delay_since_first_attempt": mock.ANY,
            "idle_for": mock.ANY,
            "start_time": mock.ANY,
        }
        self.assertEqual(_retryable_test_with_stop.statistics, expected_stats)

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml'
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


[command exit=0] /bin/zsh -lc "rtk rg -n 'set_exception|Future.construct|RetryCallState\\(' tests/test_tenacity.py"
37:def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
68:        raise _make_unset_exception(
74:    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
98:        rs = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
106:            0, 0, last_result=tenacity.Future.construct(1, ValueError("aaa"), True)
151:        rs = RetryCallState(r, None, (), {})
157:        rs = RetryCallState(r, None, (), {})
460:        fut1 = tenacity.Future
…[1609 chars elided]…
           1, 1.0, last_result=tenacity.Future.construct(1, "ok", False)
827:            1, 1.0, last_result=tenacity.Future.construct(1, 1, False)
939:            1, 0, last_result=tenacity.Future.construct(1, RuntimeError(), True)
942:            1, 0, last_result=tenacity.Future.construct(1, RuntimeError("boom"), True)
950:            1, 0, last_result=tenacity.Future.construct(1, RuntimeError(), True)
953:            1, 0, last_result=tenacity.Future.construct(1, RuntimeError("boom"), True)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '40,95p' tests/test_tenacity.py"
        if v is _unset:
            missing.append(k)
    missing_str = ", ".join(repr(s) for s in missing)
    return TypeError(func_name + " func missing parameters: " + missing_str)


def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
    # Ensure outcome_timestamp - start_time is *exactly* equal to the delay to
    # avoid complexity in test code.
    retry_state.start_time = Fraction(retry_state.start_time)  # type: ignore[assignment]
    retry_state.outcome
…[1033 chars elided]…

        retry_state.set_result(None)

    retry_state.upcoming_sleep = upcoming_sleep

    _set_delay_since_start(retry_state, delay_since_first_attempt)
    return retry_state


class TestBase(unittest.TestCase):
    def test_retrying_repr(self) -> None:
        class ConcreteRetrying(tenacity.BaseRetrying):
            def __call__(
                self, fn: typing.Any, *args: typing.Any, **kwargs: typing.Any
            ) -> typing.Any:
                pass

        repr(ConcreteRetrying())

[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-202028-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py, update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-202028-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...............s.................................................................................................... [ 66%]
..........................................................               [100%]
173 passed, 1 skipped, 28 subtests passed in 1.85s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed cause-chain traversal to stop when it revisits an exception, using identity tracking.

Added regression coverage for cyclic and non-cyclic chains, matching causes, and stop-condition execution.

Validation: 173 passed, 1 skipped; all 28 subtests passed.
