# trajectory base-1

final message:
Fixed both sync and async retry loops to call falsy callable wait strategies. `None`, `0`, and `sum([])` still mean no wait.

Added regression tests for empty-container and `__bool__`-false strategies, including async callables.

Validation: 185 passed, 1 skipped; diff check passed.

## events
[assistant] I’ll check how the sync and async loops handle wait strategies, add regression coverage, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg -n 'if .*wait|def _run_wait|class wait|sum\\(' tenacity tests | head -100"
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
…[1588 chars elided]…
ait_base):
tenacity/wait.py:95:class wait_combine(wait_base):
tenacity/wait.py:107:        return float(sum(x(retry_state) for x in self.wait_funcs))
tenacity/wait.py:110:class wait_chain(wait_base):
tenacity/wait.py:138:class wait_exception(wait_base):
tenacity/wait.py:178:class wait_incrementing(wait_base):
tenacity/wait.py:201:class wait_exponential(wait_base):
tenacity/wait.py:247:class wait_random_exponential(wait_exponential):
tenacity/wait.py:279:class wait_exponential_jitter(wait_base):

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git status --short; sed -n \"405,440p\" tenacity/__init__.py; sed -n \"145,172p\" tenacity/asyncio/__init__.py; sed -n \"440,550p\" tests/test_tenacity.py; rg -n \"no_wait|wait.*sentinel|wait.*None|run_wait\" tests/test_asyncio.py; sed -n \"1,100p\" tests/test_asyncio.py; sed -n \"1,80p\" tenacity/wait.py'"
        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
        self.statistics.clear()
        self.statistics["start_time"] = time.monotonic()
        self.statistics["attempt_number"] = 1
        self.statistics["idle_for"] = 0
        self.statistics["delay_since_first_attempt"] = 0

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)

    def _run_retry(self, retry_state: "RetryCallState") -> None:
  
…[11529 chars elided]…
h retry."""

    def __init__(self, wait: _utils.time_unit_type) -> None:
        self.wait_fixed = _utils.to_seconds(wait)

    @override
    def __call__(self, retry_state: "RetryCallState") -> float:
        return self.wait_fixed


class wait_none(wait_fixed):
    """Wait strategy that doesn't wait at all before retrying."""

    def __init__(self) -> None:
        super().__init__(0)


class wait_random(wait_base):
    """Wait strategy that waits a random amount of time between min/max."""

[command exit=1] /bin/zsh -lc "rtk proxy sh -c 'rg --files -g AGENTS.md -g pyproject.toml -g tox.ini; sed -n \"1,90p\" tests/test_tenacity.py; cat tox.ini'"
AGENTS.md
pyproject.toml
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRAN
…[2071 chars elided]…
e.attempt_number = previous_attempt_number
    if last_result is not None:
        retry_state.outcome = last_result
    else:
        retry_state.set_result(None)

    retry_state.upcoming_sleep = upcoming_sleep

    _set_delay_since_start(retry_state, delay_since_first_attempt)
    return retry_state


class TestBase(unittest.TestCase):
    def test_retrying_repr(self) -> None:
        class ConcreteRetrying(tenacity.BaseRetrying):
            @override
cat: tox.ini: No such file or directory

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for filename in ('tenacity/__init__.py', 'tenacity/asyncio/__init__.py'):
 p=Path(filename); s=p.read_text(); start=s.index('        # 
…[2724 chars elided]…
)
                self.assertEqual(await retrying(flaky), \"ok\")
                calls.assert_called_once_with(1)
                sleep.assert_awaited_once_with(1.5)

'''+s[pos:];p.write_text(s)
PY
"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...................s......................................................................................................... [ 67%]
.............................................................            [100%]
185 passed, 1 skipped, 19 subtests passed in 1.88s

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git diff --check; git diff --stat; cat pyproject.toml'"
 tenacity/__init__.py         |  8 +++-----
 tenacity/asyncio/__init__.py |  6 +++---
 tests/test_asyncio.py        | 29 +++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 28 ++++++++++++++++++++++++++++
 4 files changed, 63 insertions(+), 8 deletions(-)
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "tenacity/_version.py"

[project]
name = "tenacity"
dynamic = ["v
…[3023 chars elided]…
n = "3.10"
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
    "truthy-bool",
    "truthy-iterable",
    "unused-awaitable",
]


[assistant] Both loops now call falsy callable strategies while preserving `None` and zero as no-wait values. The new tests verify the requested delay reaches the sleep function, including for an async strategy. The suite passes: 185 passed, 1 skipped.
[command exit=1] /bin/zsh -lc "rtk proxy sh -c 'command -v mypy; command -v ruff; ls <work>/env-tenacity/bin/ | rg \"mypy|ruff\"'"

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for filename, annotation in [('tests/test_tenacity.py', 'typing.Any'), ('tests/test_asyncio.py', 'Any')]:
 p=Path(filename); s=p.read_text().replace('class EmptyWait(dict):', f'class EmptyWait(dict[str, {annotation}]):');p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...................s......................................................................................................... [ 67%]
.............................................................            [100%]
185 passed, 1 skipped, 19 subtests passed in 1.83s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed both sync and async retry loops to call falsy callable wait strategies. `None`, `0`, and `sum([])` still mean no wait.

Added regression tests for empty-container and `__bool__`-false strategies, including async callables.

Validation: 185 passed, 1 skipped; diff check passed.
