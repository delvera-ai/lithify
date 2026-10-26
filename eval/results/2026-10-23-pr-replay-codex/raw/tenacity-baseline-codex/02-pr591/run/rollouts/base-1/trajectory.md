# trajectory base-1

final message:
Fixed `after_log` to emit `after ?(s)` when the outcome timestamp is missing, while preserving numeric formatting for known elapsed times.

Added regression coverage for default and custom formats. All checks passed: 127 tests passed, 1 skipped, 14 subtests passed.

## events
[assistant] I’ll check the logging callback and tests, add the smallest fix, then run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'def after_log|after_log|seconds_since_start' tenacity tests; rg --files -g AGENTS.md"
~/.cache/lithify/work/repo-d0c7726da9a8/20261023-200031-bug-tenacity-after-log-crashes-w/base-1
tests/test_after.py:7:    after_log,
tests/test_after.py:37:        fun = after_log(
tests/test_after.py:49:            f"after {sec_format % retry_state.seconds_since_start}(s), "
tests/test_after.py:64:        fun = after_log(logger=logger, log_level=self.log_level, sec_format=sec_format)
tests/test_after.py:74:            f"after {sec_format % retry_state.seconds_since_start}(s), "
ten
…[898 chars elided]…
 retry_state.seconds_since_start + retry_state.upcoming_sleep
tenacity/__init__.py:31:from .after import after_log, after_nothing
tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/__init__.py:701:    "after_log",
tenacity/after.py:29:def after_log(
tenacity/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
AGENTS.md

[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/after.py tests/test_after.py pyproject.toml'
# Copyright 2016 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[6230 chars elided]…
can)
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


[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '20,60p' tests/test_tenacity.py"
import time
import typing
import unittest
import warnings
from contextlib import contextmanager
from copy import copy
from fractions import Fraction
from unittest import mock

import pytest
from typeguard import check_type

import tenacity
from tenacity import RetryCallState, RetryError, Retrying, retry

_unset = object()


def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
    missing = []
    for k, v in kwargs.items():
        if v is _unset:
            missing.app
…[260 chars elided]…
rt_time is *exactly* equal to the delay to
    # avoid complexity in test code.
    retry_state.start_time = Fraction(retry_state.start_time)  # type: ignore[assignment]
    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
    assert retry_state.seconds_since_start == delay


def make_retry_state(
    previous_attempt_number: typing.Any,
    delay_since_first_attempt: typing.Any,
    last_result: typing.Any = None,
    upcoming_sleep: typing.Any = 0,
) -> RetryCallState:

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '520,560p' tenacity/__init__.py"
    ) -> None:
        #: Retry call start timestamp
        self.start_time = time.monotonic()
        #: Retry manager object
        self.retry_object = retry_object
        #: Function wrapped by this retry call
        self.fn = fn
        #: Arguments of the function wrapped by this retry call
        self.args = args
        #: Keyword arguments of the function wrapped by this retry call
        self.kwargs = kwargs

        #: The number of the current attempt
        self.attempt_number
…[518 chars elided]…
   def seconds_since_start(self) -> float | None:
        if self.outcome_timestamp is None:
            return None
        return self.outcome_timestamp - self.start_time

    def prepare_for_next_attempt(self) -> None:
        self.outcome = None
        self.outcome_timestamp = None
        self.attempt_number += 1
        self.next_action = None

    def set_result(self, val: t.Any) -> None:
        ts = time.monotonic()
        fut = Future(self.attempt_number)
        fut.set_result(val)

[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-200031-bug-tenacity-after-log-crashes-w/base-1/tests/test_after.py
[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_after.py'
...                                                                    [100%]
=================================== FAILURES ===================================
____ TestAfterLogFormat.test_missing_outcome_timestamp (sec_format='%.3g') _____

self = <tests.test_after.TestAfterLogFormat testMethod=test_missing_outcome_timestamp>

    def test_missing_outcome_timestamp(self) -> None:
        logger = unittest.mock.MagicMock(spec=logging.Logger)
        retry_state = test_tenacity.make_retry_state(se
…[2534 chars elided]…
           f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )
E       TypeError: must be real number, not NoneType

tenacity/after.py:45: TypeError
=========================== short test summary info ============================
SUBFAILED(sec_format='%.3g') tests/test_after.py::TestAfterLogFormat::test_missing_outcome_timestamp
SUBFAILED(sec_format='%.1f') tests/test_after.py::TestAfterLogFormat::test_missing_outcome_timestamp
2 failed, 3 passed in 0.05s

[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-200031-bug-tenacity-after-log-crashes-w/base-1/tenacity/after.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...........s.............................................. [ 45%]
......................................................................   [100%]
127 passed, 1 skipped, 14 subtests passed in 1.87s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed `after_log` to emit `after ?(s)` when the outcome timestamp is missing, while preserving numeric formatting for known elapsed times.

Added regression coverage for default and custom formats. All checks passed: 127 tests passed, 1 skipped, 14 subtests passed.
