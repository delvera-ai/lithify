# trajectory base-1

final message:
Fixed both sync and async retry loops to call falsy wait strategies while preserving `None` and integer `0` as no-wait values.

Added regression coverage for empty-container and `__bool__`-false strategies.

Validation: 185 passed, 1 skipped. Diff checks pass. Ruff and mypy were unavailable in the environment.

## events
[assistant] I’ll check how wait strategies are selected, fix both retry loops, and run the project tests.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'if .*wait|self.wait|class .*Retry' tenacity tests | head -100"
~/.cache/lithify/work/repo-553f5f2e6879/20261023-202643-bug-retrying-skips-the-wait-stra/base-1
tenacity/asyncio/__init__.py:75:class AsyncRetrying(BaseRetrying):
tenacity/asyncio/__init__.py:157:        if not self.wait:  # type: ignore[truthy-bool]
tenacity/asyncio/__init__.py:160:            retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
tests/test_tenacity.py:89:        class ConcreteRetrying(tenacity.BaseRetrying):
tests/test_tenacity.py:114:class Test
…[1250 chars elided]…
tenacity/wait.py:69:        return self.wait_fixed
tenacity/wait.py:85:        self.wait_random_min = _utils.to_seconds(min)
tenacity/wait.py:86:        self.wait_random_max = _utils.to_seconds(max)
tenacity/wait.py:90:        return self.wait_random_min + (
tenacity/wait.py:91:            random.random() * (self.wait_random_max - self.wait_random_min)
tenacity/wait.py:99:        self.wait_funcs = strategies
tenacity/wait.py:107:        return float(sum(x(retry_state) for x in self.wait_funcs))

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '410,435p' tenacity/__init__.py"
        self.statistics["attempt_number"] = 1
        self.statistics["idle_for"] = 0
        self.statistics["delay_since_first_attempt"] = 0

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)

    def _run_retry(self, retry_state: "RetryCallState") -> None:
        self.iter_state.retry_run_result = self.retry(retry_state)

    def _run_wait(self, retry_state: "RetryCallState") -> None:
        # `wait` is annotated as always set, so
…[254 chars elided]…
elf.wait:  # type: ignore[truthy-bool]
            retry_state.upcoming_sleep = 0.0
        else:
            retry_state.upcoming_sleep = self.wait(retry_state)

    def _run_stop(self, retry_state: "RetryCallState") -> None:
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = self.stop(retry_state)

    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '145,170p' tenacity/asyncio/__init__.py"
        self.iter_state.actions.append(_utils.wrap_to_async_func(fn))

    @override
    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.iter_state.retry_run_result = await _utils.wrap_to_async_func(self.retry)(
            retry_state
        )

    @override
    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        # See BaseRetrying._run_wait: falsy `wait` values mean "no wait" and
        
…[93 chars elided]…
       retry_state.upcoming_sleep = 0.0
        else:
            retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
                retry_state
            )

    @override
    async def _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
            retry_state
        )


[command exit=0] /bin/zsh -lc "rtk rg -n 'wait=None|wait=0|sum\\(|wait strategy|test_wait' tests/test_tenacity.py tests/test_asyncio.py tenacity/wait.py"
tests/test_asyncio.py:87:    async def test_wait_falsy_values_mean_no_wait(self) -> None:
tenacity/wait.py:40:    # `other` is `int` rather than `Literal[0]` because typeshed's `sum()`
tenacity/wait.py:42:    # `sum()` over wait strategies need a `type: ignore`. A non-zero number is
tenacity/wait.py:46:            # `sum()` seeds its accumulator with the int 0; treat that as
tenacity/wait.py:48:            # is not a wait strategy, and saying so here raises TypeError at
tenacity/wait.py:107:    
…[1707 chars elided]…
tial_jitter_min(self) -> None:
tests/test_tenacity.py:697:    def test_wait_exponential_jitter_timedelta(self) -> None:
tests/test_tenacity.py:710:    def test_wait_exponential_jitter_multiplier(self) -> None:
tests/test_tenacity.py:717:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:723:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:727:    def test_wait_retry_state_attributes(self) -> None:

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '500,535p' tests/test_tenacity.py"
                ]
            )
        )
        # Test it a few time since it's random
        for _ in range(1000):
            w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

    def test_wait_falsy_values_mean_no_wait(self) -> None:
        # Untyped callers pass None or 0 to mean "no wait", and `sum([])`
        # over an empty list of strategies yields the int 0. All must reach
        # the retry path without blowing up insi
…[329 chars elided]…
m([])):
            with self.subTest(wait=wait):
                flaky = make_flaky()
                r = Retrying(
                    wait=wait,  # type: ignore[arg-type]
                    stop=tenacity.stop_after_attempt(3),
                )
                self.assertEqual(r(flaky), "ok")

    def test_wait_radd_plain_callable(self) -> None:
        # A plain callable is a valid WaitBaseT, and functions have no
        # __add__, so `callable + strategy` goes through wait_base.__radd__.

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,125p' tests/test_asyncio.py"
# Copyright 2016 Étienne Bersac
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the spe
…[2543 chars elided]…
unt

    @asynctest
    async def test_stop_after_attempt(self) -> None:
        thing = NoIOErrorAfterCount(2)
        try:
            await _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tasyncio.AsyncRetrying())

    def test_retry_attributes(self) -> None:
        assert hasattr(_retryable_coroutine, "retry")
        assert hasattr(_retryable_coroutine, "retry_with")

    @asynctest

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '28,60p' tenacity/wait.py"


class wait_base(abc.ABC):
    """Abstract base class for wait strategies."""

    @abc.abstractmethod
    def __call__(self, retry_state: "RetryCallState") -> float:
        pass

    def __add__(self, other: "wait_base") -> "wait_combine":
        return wait_combine(self, other)

    # `other` is `int` rather than `Literal[0]` because typeshed's `sum()`
    # protocol demands `__radd__(x: int)`; narrowing it would make every
    # `sum()` over wait strategies need a `type: ignore`. A non-zer
…[329 chars elided]…
     # is not a wait strategy, and saying so here raises TypeError at
            # the `+` rather than building a combination that fails when called.
            if other == 0:
                return self
            return NotImplemented
        # A plain callable -- `WaitBaseT` admits those, and a function has no
        # `__add__` of its own to handle `callable + strategy`.
        return wait_combine(self, other)


WaitBaseT = wait_base | typing.Callable[["RetryCallState"], float | int]



[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/__init__.py')
s=p.read_text().replace('''        # "'`wait` is annotated as always set, so a type checker sees this gu
…[745 chars elided]…
e[truthy-bool]
'"''','''        # See BaseRetrying._run_wait for the supported no-wait values.
        if self.wait is None or (isinstance(self.wait, int) and self.wait == 0):
''')
p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_tenacity.py')
s=p.read_text(); marker='    def test_wait_radd_plain_callable(self) -> None:\\n'
s=s.replace(marker,'
…[2269 chars elided]…
ises(RetryError):
                    await retrying(lambda: None)
                self.assertEqual(calls, [1, 2])
                sleep.assert_awaited_once_with(0.25)

'''+marker);p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...................s......................................................................................................... [ 67%]
.............................................................            [100%]
185 passed, 1 skipped, 19 subtests passed in 1.86s

[command exit=2] /bin/zsh -lc "rtk rg -n 'RetryCallState|mypy|ruff' tests/test_tenacity.py pyproject.toml setup.cfg tox.ini"
rg: setup.cfg: No such file or directory (os error 2)
rg: tox.ini: No such file or directory (os error 2)
pyproject.toml:56:    "ruff==0.16.9",
pyproject.toml:57:    "mypy==2.3.1",
pyproject.toml:69:mypy = "mypy"
pyproject.toml:74:    { cmd = "ruff check --fix ." },
pyproject.toml:75:    { cmd = "ruff format ." },
pyproject.toml:80:    { cmd = "ruff check ." },
pyproject.toml:81:    { cmd = "ruff format --check ." },
pyproject.toml:87:    { ref = "mypy" },
pyproject.toml:96:[tool.ruff]
pyproject
…[1812 chars elided]…
 None:
tests/test_tenacity.py:1868:        def _after(retry_state: RetryCallState) -> None:
tests/test_tenacity.py:1885:        def _before_sleep(retry_state: RetryCallState) -> None:
tests/test_tenacity.py:2131:        def retry_error_callback(retry_state: RetryCallState) -> typing.Any:
tests/test_tenacity.py:2291:        The annotations below are the assertions; mypy checks them when it runs
tests/test_tenacity.py:2327:        does fail under `mypy --strict`, which also type-checks this file.

[assistant] Both loops now check explicitly for the supported no-wait values. Regression tests confirm that falsy callable strategies run and their returned delays reach the sleep function, including an async strategy. The full test suite passes; I’m checking lint and typing next.
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '65,135p' pyproject.toml"
docs-doctest = "sphinx-build -a -E -W -b doctest doc/source doc/build"
docs-html = "sphinx-build -a -E -W -b html doc/source doc/build"
docs = ["docs-doctest", "docs-html"]
check = ["test", "docs"]
mypy = "mypy"
reno = "reno"

[tool.poe.tasks.fmt]
sequence = [
    { cmd = "ruff check --fix ." },
    { cmd = "ruff format ." },
]

[tool.poe.tasks.lint]
sequence = [
    { cmd = "ruff check ." },
    { cmd = "ruff format --check ." },
]

[tool.poe.tasks.all]
sequence = [
    { ref = "lint" },
    { 
…[1227 chars elided]…
ng that the code is valid on the oldest one we support.
python_version = "3.10"
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]
# `strict` is not "everything" -- these are checks it leaves off.
warn_unreachable = true
disallow_any_unimported = true
extra_checks = true
enable_error_code = [
    "deprecated",
    "exhaustive-match",
    "explicit-override",
    "ignore-without-code",
    "mutable-override",
    "possibly-undefined",
    "redundant-expr",

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/ruff check .'
rtk: Failed to execute command: <work>/env-tenacity/bin/ruff: No such file or directory (os error 2)

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/mypy'
rtk: Failed to execute command: <work>/env-tenacity/bin/mypy: No such file or directory (os error 2)

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for name, any_type in [('tests/test_tenacity.py', 'typing.Any'), ('tests/test_asyncio.py', 'Any')]:
 p=Path(name);s=p.read_text().repla
…[61 chars elided]…
}]):').replace('                calls = []\\n', '                calls: list[int] = []\\n').replace('                sleeps = []\\n', '                sleeps: list[float] = []\\n');p.write_text(s)
PY"

[command exit=1] /bin/zsh -lc 'rtk proxy python -m ruff check .'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py         |  8 +++-----
 tenacity/asyncio/__init__.py |  5 ++---
 tests/test_asyncio.py        | 30 ++++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 29 +++++++++++++++++++++++++++++
 4 files changed, 64 insertions(+), 8 deletions(-)

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...................s......................................................................................................... [ 67%]
.............................................................            [100%]
185 passed, 1 skipped, 19 subtests passed in 1.92s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed both sync and async retry loops to call falsy wait strategies while preserving `None` and integer `0` as no-wait values.

Added regression coverage for empty-container and `__bool__`-false strategies.

Validation: 185 passed, 1 skipped. Diff checks pass. Ruff and mypy were unavailable in the environment.
