# trajectory base-1

final message:
Implemented pickle support for `Retrying` and built-in retry strategies.

- Preserves statistics and recreates thread-local storage.
- Restored controllers remain usable.
- Added round-trip and spawned `Pool.map` regression tests.

Checks: **269 passed, 1 skipped**. Ruff was unavailable in the environment.

Custom callbacks still need to be picklable by standard `pickle`.

## events
[assistant] I’ll inspect how retry state and strategies are stored, add pickle support, and run the project’s checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*retry*' -g '*test*' -g 'setup*' -g 'pyproject.toml'"
~/.cache/lithify/work/repo-553f5f2e6879/20261023-200950-bug-retrying-objects-and-the-bui/base-1
releasenotes/notes/retrycallstate-repr-94947f7b00ee15e1.yaml
releasenotes/notes/fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml
releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
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

[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/retry.py tenacity/__init__.py'
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS O
…[34829 chars elided]…
lt",
    "retry_never",
    "retry_unless_exception_type",
    "sleep",
    "sleep_using_event",
    "stop_after_attempt",
    "stop_after_delay",
    "stop_all",
    "stop_any",
    "stop_before_delay",
    "stop_never",
    "stop_when_event_set",
    "wait_chain",
    "wait_combine",
    "wait_exception",
    "wait_exponential",
    "wait_exponential_jitter",
    "wait_fixed",
    "wait_full_jitter",
    "wait_incrementing",
    "wait_none",
    "wait_random",
    "wait_random_exponential",
]

[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml; rtk git status --short'
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
    "Lice
…[2094 chars elided]…
n)
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

ok
[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/asyncio/retry.py; rtk proxy head -65 tests/test_tenacity.py'
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS O
…[5801 chars elided]…
re[assignment]
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

[assistant] Two things prevent pickling: `Retrying` stores thread-local state, and several built-in strategies store lambdas or nested functions. I’ll preserve statistics, recreate the thread-local storage on restore, and replace those predicates with picklable callables. Pending iteration actions will be reset so the restored controller can start a new call.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/__init__.py')
s=p.read_text(); pos=s.index('    def copy(\\n',s.index('class BaseRetrying'))
s=s[:pos]+'''    def __ge
…[2150 chars elided]…
nvert predicate');b=s.index('    def __call__',a)
s=s[:a]+'''    def _predicate(self, exception: BaseException) -> bool:
        return not super()._predicate(exception)

'''+s[b:];p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
Path('tests/test_pickle.py').write_text('''import pickle
import re
import sys
import typing

import pytest

import tenacity


@pytest.m
…[3331 chars elided]…
 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no"
............s........................................................... [ 26%]
........................................................................ [ 53%]
............................................................ [ 76%]
................................................................         [100%]
267 passed, 1 skipped, 12 subtests passed in 1.82s

[command exit=1] /bin/zsh -lc 'rtk proxy python -m ruff check tenacity/retry.py tenacity/__init__.py tests/test_pickle.py; rtk proxy python -m ruff format --check tenacity/retry.py tenacity/__init__.py tests/test_pickle.py'
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff

[command exit=1] /bin/zsh -lc 'rtk git diff --stat; rtk git diff -- tenacity/retry.py; rtk proxy which ruff'
tenacity/__init__.py | 13 ++++++++++++
 tenacity/retry.py    | 57 ++++++++++++++++++++++++++++++++--------------------
 2 files changed, 48 insertions(+), 22 deletions(-)
tenacity/retry.py | 57 ++++++++++++++++++++++++++++++++++---------------------
 1 file changed, 35 insertions(+), 22 deletions(-)

--- Changes ---

tenacity/retry.py
  @@ -15,6 +15,7 @@
  +import functools
   import re
   import typing
   
  @@ -22,6 +23,20 @@ if typing.TYPE_CHECKING:
  +def _is_exception_type(
  +    exception
…[2783 chars elided]…
on_message):
  @@ -250,9 +264,8 @@ class retry_if_not_exception_message(retry_if_exception_message):
  -        # invert predicate
  -        if_predicate = self.predicate
  -        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
  +    def _predicate(self, exception: BaseException) -> bool:
  +        return not super()._predicate(exception)
   
       def __call__(self, retry_state: "RetryCallState") -> bool:
           if retry_state.outcome is None:
  +35 -22

[assistant] The suite passes with round-trip tests for every pickle protocol, composed strategies, and controllers used for both successful and exhausted retries. Restored controllers retain statistics and can run again. I’ll add a direct `Pool.map` regression check as well.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_pickle.py');s=p.read_text().replace('import pickle\\n','import multiprocessing\\nimport pickle\\n');s+='''

def test
…[611 chars elided]…
 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no"
............s........................................................... [ 26%]
........................................................................ [ 53%]
............................................................ [ 75%]
..................................................................       [100%]
269 passed, 1 skipped, 12 subtests passed in 1.89s

[command exit=0] /bin/zsh -lc 'rtk git status --short; rtk git diff --check'
 M tenacity/__init__.py
 M tenacity/retry.py
?? tests/test_pickle.py

[assistant] Implemented pickle support for `Retrying` and built-in retry strategies.

- Preserves statistics and recreates thread-local storage.
- Restored controllers remain usable.
- Added round-trip and spawned `Pool.map` regression tests.

Checks: **269 passed, 1 skipped**. Ruff was unavailable in the environment.

Custom callbacks still need to be picklable by standard `pickle`.
