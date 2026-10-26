# trajectory base-1

final message:
Implemented keyword-only `multiplier`, defaulting to 1.

- Positional and keyword `initial` still work and emit `DeprecationWarning`.
- Passing both raises `ValueError`.
- Added regression tests.

Checks passed: 157 tests passed, 1 skipped.

## events
[assistant] I’ll check the constructor and tests, add the compatibility handling, then run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; rg -n 'class wait_exponential_jitter|wait_exponential_jitter' tenacity tests; rg --files -g AGENTS.md"
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
tenacity/wait.py:2
…[334 chars elided]…
py:612:        fn = tenacity.wait_exponential_jitter(10, 5)
tests/test_tenacity.py:617:        fn = tenacity.wait_exponential_jitter()
tests/test_tenacity.py:620:    def test_wait_exponential_jitter_min(self) -> None:
tests/test_tenacity.py:621:        fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)
tests/test_tenacity.py:630:    def test_wait_exponential_jitter_timedelta(self) -> None:
tests/test_tenacity.py:633:        fn = tenacity.wait_exponential_jitter(
AGENTS.md

[command exit=2] /bin/zsh -lc "rtk proxy sed -n '1,65p;130,310p' tenacity/wait.py; rtk proxy sed -n '550,665p' tests/test_tenacity.py; rtk proxy rg -n 'DeprecationWarning|warnings.warn|filterwarnings' tenacity tests pyproject.toml setup.cfg"
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
…[11673 chars elided]…
        retry=(
                tenacity.retry_if_exception_type()
                | tenacity.retry_if_result(lambda result: result == 123)
            ),
        )

        def returnval() -> int:
            return 123

        try:
            retrying(returnval)
        except ExtractCallState as err:
rg: setup.cfg: No such file or directory (os error 2)
pyproject.toml:95:filterwarnings = [
pyproject.toml:96:    "once::DeprecationWarning",
tenacity/__init__.py:719:            warnings.warn(

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '85,110p' pyproject.toml; rtk proxy sed -n '15,40p' tests/test_tenacity.py; rtk git status --short"
]

[tool.poe.tasks.all]
sequence = [
    { ref = "lint" },
    { ref = "mypy" },
    { ref = "check" },
]

[tool.pytest.ini_options]
filterwarnings = [
    "once::DeprecationWarning",
]

[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"
exclude = ["tenacity/_version.py"]

[tool.ruff.lint]
select = ["ASYNC", "B", "C4", "DTZ", "E", "EXE", "F", "FLY", "FURB", "I", "ICN", "ISC", "LOG", "PERF", "PGH", "PIE", "PTH", "PYI", "RET", "RSE", "RUF", "SIM", "SLF", "SLOT", "T10", "TC", "U
…[281 chars elided]…
 datetime
import logging
import pickle
import re
import time
import typing
import unittest
from fractions import Fraction
from unittest import mock

import pytest
from typeguard import check_type

import tenacity
from tenacity import RetryCallState, RetryError, Retrying, retry
from tenacity.retry import retry_all, retry_any

_unset = object()


def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
    missing = []
    for k, v in kwargs.items():
        if v is _unset:
ok
[assistant] I’ll keep `initial` in the first positional slot so existing calls still work, and make `multiplier` keyword-only. An internal sentinel will distinguish omitted arguments from explicit values, so passing both—even as `1`—raises `ValueError`.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/wait.py')
s=p.read_text().replace('import typing\\n','import typing\\nimport warnings\\n').replace('\\n\\nclass wait_b
…[2758 chars elided]…
 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no"
............s............................................... [ 37%]
........................................................................ [ 83%]
..........................                                               [100%]
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201304-api-cleanup-every-other-exponent/base-1/tests/t
…[133 chars elided]…
5)

tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
  ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201304-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:645: DeprecationWarning: initial is deprecated; use multiplier instead
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
157 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.83s

[command exit=0] /bin/zsh -lc "rtk git diff --stat; rtk proxy sed -n '245,310p' tenacity/wait.py"
tenacity/wait.py       | 30 +++++++++++++++++++++++++-----
 tests/test_tenacity.py | 24 ++++++++++++++++++++++++
 2 files changed, 49 insertions(+), 5 deletions(-)
    """Wait strategy that applies exponential backoff and jitter.

    It allows for a customized multiplier, maximum wait, jitter and minimum.
    The multiplier defaults to 1. The initial parameter is deprecated;
    use the keyword-only multiplier parameter instead.

    This implements the strategy described here:
    https://clou
…[1035 chars elided]…
conds(max)
        self.exp_base = exp_base
        self.jitter = _utils.to_seconds(jitter)
        self.min = _utils.to_seconds(min)

    def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.multiplier * exp + jitter
        except OverflowError:
            result = self.max
        return max(max(0, self.min), min(result, self.max))

[assistant] Implemented keyword-only `multiplier`, defaulting to 1.

- Positional and keyword `initial` still work and emit `DeprecationWarning`.
- Passing both raises `ValueError`.
- Added regression tests.

Checks passed: 157 tests passed, 1 skipped.
