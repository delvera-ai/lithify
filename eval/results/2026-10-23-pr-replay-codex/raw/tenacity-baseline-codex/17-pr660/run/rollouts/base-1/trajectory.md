# trajectory base-1

final message:
Fixed cause-chain traversal to stop when an exception identity repeats, while preserving matching causes throughout the chain.

Added regression coverage for self-cycles, two-exception cycles, and ordinary chains.

Checks: 172 passed, 1 skipped. Ruff was unavailable in the project environment.

## events
[assistant] I’ll inspect the cause-chain predicate, add cycle detection and regression tests, then run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'retry_if_exception_cause_type' .; rg --files -g AGENTS.md"
~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202023-bug-retry-if-exception-cause-typ/base-1
./tenacity/retry.py:160:class retry_if_exception_cause_type(retry_base):
./releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml:4:    Add a new `retry_base` class called `retry_if_exception_cause_type` that
./releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
./tests/test_tenacity.py:1170:@retry(retry=tenacity.retry_if_exception_cause_type(NameError))
./tests/test_tenacity.py:1433:    def test_retry_if_exception_cause_type(self) -> None:
./tenacity/__init__.py:49:    retry_if_exception_cause_type,
./tenacity/__init__.py:803:    "retry_if_exception_cause_type",
AGENTS.md

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


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1360,1505p' tests/test_tenacity.py"
            # no input should catch all subclasses of Exception
            self.assertTrue(
                _retryable_test_with_unless_exception_type_no_input(
                    NameErrorUntilCount(5)
                )
            )
        except NameError as e:
            s = _retryable_test_with_unless_exception_type_no_input.statistics
            self.assertTrue(s["attempt_number"] == 6)
            print(e)
        else:
            self.fail("Expected NameError")

    def test_retry_
…[4681 chars elided]…
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
[command exit=0] /bin/zsh -lc "rtk rg -n 'RetryCallState|set_exception|Future.construct' tests/test_tenacity.py"
31:from tenacity import RetryCallState, RetryError, Retrying, retry
37:def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
46:def _set_delay_since_start(retry_state: RetryCallState, delay: typing.Any) -> None:
59:) -> RetryCallState:
60:    """Construct RetryCallState for given attempt number & delay.
68:        raise _make_unset_exception(
74:    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
98:        rs = RetryCallState(None, None, (), {}
…[2589 chars elided]…
 0, last_result=tenacity.Future.construct(1, RuntimeError(), True)
953:            1, 0, last_result=tenacity.Future.construct(1, RuntimeError("boom"), True)
1691:        def return_text(retry_state: RetryCallState) -> str:
1708:        def _before(retry_state: RetryCallState) -> None:
1726:        def _after(retry_state: RetryCallState) -> None:
1743:        def _before_sleep(retry_state: RetryCallState) -> None:
1988:        def retry_error_callback(retry_state: RetryCallState) -> typing.Any:

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


[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202023-bug-retry-if-exception-cause-typ/base-1/tenacity/retry.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202023-bug-retry-if-exception-cause-typ/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '50,65p' tests/test_tenacity.py"
    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
    assert retry_state.seconds_since_start == delay


def make_retry_state(
    previous_attempt_number: typing.Any,
    delay_since_first_attempt: typing.Any,
    last_result: typing.Any = None,
    upcoming_sleep: typing.Any = 0,
) -> RetryCallState:
    """Construct RetryCallState for given attempt number & delay.

    Only used in testing and thus is extra careful about timestamp arithmetics.
    """
    required_parameter_unset = (
        previous_attempt_number is _unset or delay_since_first_attempt is _unset

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...............s............................................................................................................ [ 71%]
.................................................                        [100%]
172 passed, 1 skipped, 20 subtests passed in 1.84s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m ruff check tenacity/retry.py tests/test_tenacity.py'
<work>/env-tenacity/bin/python: No module named ruff

[assistant] Fixed cause-chain traversal to stop when an exception identity repeats, while preserving matching causes throughout the chain.

Added regression coverage for self-cycles, two-exception cycles, and ordinary chains.

Checks: 172 passed, 1 skipped. Ruff was unavailable in the project environment.
