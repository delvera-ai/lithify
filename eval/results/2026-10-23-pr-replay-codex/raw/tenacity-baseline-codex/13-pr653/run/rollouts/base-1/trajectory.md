# trajectory base-1

final message:
Fixed sync and async retry wrappers to preserve the statistics dictionary’s identity through `functools.wraps`.

Added regression tests for live statistics and repeated calls.

Validation: 167 passed, 1 skipped. Ruff was unavailable in the environment.

## events
[assistant] I’ll inspect how retry statistics are attached, fix the sync and async paths, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg -n 'statistics|def wraps' tenacity tests | head -100"
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
…[5936 chars elided]…
statistics["attempt_number"] = 1
tenacity/__init__.py:390:        self.statistics["idle_for"] = 0
tenacity/__init__.py:391:        self.statistics["delay_since_first_attempt"] = 0
tenacity/__init__.py:408:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:467:            self.statistics["idle_for"] += sleep
tenacity/__init__.py:468:            self.statistics["attempt_number"] += 1
tenacity/__init__.py:656:    statistics: dict[str, t.Any]

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '350,395p' tenacity/__init__.py"

    @property
    def iter_state(self) -> IterState:
        if not hasattr(self._local, "iter_state"):
            self._local.iter_state = IterState()
        return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.
        """

        @functools.wraps(
            f, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaul
…[816 chars elided]…
]
        wrapped_f.statistics = {}  # type: ignore[attr-defined]

        return t.cast("_RetryDecorated[P, R]", wrapped_f)

    def begin(self) -> None:
        self.statistics.clear()
        self.statistics["start_time"] = time.monotonic()
        self.statistics["attempt_number"] = 1
        self.statistics["idle_for"] = 0
        self.statistics["delay_since_first_attempt"] = 0

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '195,230p' tenacity/asyncio/__init__.py"
                self._retry_state.prepare_for_next_attempt()
                await self.sleep(do)  # type: ignore[misc]
            else:
                raise StopAsyncIteration

    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        wrapped = super().wraps(fn)
        # Ensure wrapper is recognized as a coroutine function.

        @functools.wraps(
            fn, functools.WRAPPER_ASSIGNMENTS + ("__defaults__", "__kwdefaults__")
        )
        async def async_wrapped(
…[478 chars elided]…
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
    "retry_if_exception",

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1435,1515p' tests/test_tenacity.py"
        """Test that functools.wraps doesn't cause problems with callable objects.

        It raises an error upon trying to wrap it in Py2, because __name__
        attribute is missing. It's fixed in Py3 but was never backported.
        """

        class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
        )
        h = retrying.wraps(Hello())
       
…[2183 chars elided]…
 in succeeds_first_try.statistics
            assert succeeds_first_try.statistics["delay_since_first_attempt"] == 0
            return True

        succeeds_first_try()
        assert succeeds_first_try.statistics["delay_since_first_attempt"] == 0


class TestEnabled:
    def test_enabled_false_skips_retry(self) -> None:
        """When enabled=False, the function is called directly without retrying."""
        call_count = 0

        @retry(enabled=False, stop=tenacity.stop_after_attempt(3))

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '480,565p' tests/test_asyncio.py"

            return attempts

        result = await test()

        self.assertEqual(3, result)

    @asynctest
    async def test_async_retying_iterator(self) -> None:
        thing = NoIOErrorAfterCount(5)
        with pytest.raises(TypeError):
            for attempts in AsyncRetrying():
                with attempts:
                    await _async_function(thing)


class TestDecoratorWrapper(unittest.TestCase):
    @asynctest
    async def test_retry_function_attributes(self) -> None:
   
…[1760 chars elided]…
yable_coroutine_with_2_attempts.retry.statistics,
                    expected_stats,
                )
            else:
                self.fail("RetryError should have been raised after 1 attempt")


# make sure mypy accepts passing an async sleep function
# https://github.com/jd/tenacity/issues/399
async def my_async_sleep(x: float) -> None:
    await asyncio.sleep(x)


@retry(sleep=my_async_sleep)
async def foo() -> None:
    pass


class TestSyncFunctionWithAsyncSleep(unittest.TestCase):

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[assistant] `functools.wraps` copies the initial statistics dictionary by reference, but Tenacity replaces that dictionary on each call. I’ll keep its identity stable so outer wrappers see the runtime updates, and add regression tests for repeated sync and async calls.
[command exit=0] /bin/zsh -lc 'rtk proxy head -45 tests/test_asyncio.py'
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
…[146 chars elided]…
rt Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar
from unittest import mock

try:
    import trio
except ImportError:
    have_trio = False
else:
    have_trio = True

import pytest

import tenacity
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
)
from tenacity import asyncio as tasyncio
from tenacity.wait import wait_fixed

from .test_tenacity import (

[command exit=0] /bin/zsh -lc 'rtk proxy head -40 tests/test_tenacity.py'
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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[159 chars elided]…
rt datetime
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


[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for filename, name in [('tests/test_tenacity.py', 'sync'), ('tests/test_asyncio.py', 'async')]:
 p=Path(filename)
 s=p.read_text()
 if 
…[1785 chars elided]…
cs
            assert inner.retry.statistics is statistics
            assert statistics[\"attempt_number\"] == failures + 1

'''
 assert marker in s
 p.write_text(s.replace(marker,test+marker,1))
PY"

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no -k statistics_through_functools_wraps'
FF                                                                       [100%]
=================================== FAILURES ===================================
_________ TestDecoratorWrapper.test_statistics_through_functools_wraps _________

failures = 2

    @retry(stop=stop_after_attempt(3))
    async def inner(failures: int) -> str:
>       assert outer.statistics is inner.statistics
E       AssertionError: assert {} is {'start_time': 241880.7283535, 'attempt_number': 3, 'idle_for': 0.0, 'de
…[5468 chars elided]…
_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x1097faa80 state=finished raised AssertionError>]

tenacity/__init__.py:458: RetryError
=========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_through_functools_wraps
FAILED tests/test_tenacity.py::TestDecoratorWrapper::test_statistics_through_functools_wraps
2 failed, 166 deselected in 0.18s

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for filename, wrapper in [('tenacity/__init__.py','wrapped_f'), ('tenacity/asyncio/__init__.py','async_wrapped')]:
 p=Path(filename)
 s
…[101 chars elided]…
ned]',f'            # Keep the dictionary shared with decorators using functools.wraps.\\n            copy._local.statistics = {wrapper}.statistics  # type: ignore[attr-defined]')
 p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
..............s............................................... [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.81s

[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py         |  3 ++-
 tenacity/asyncio/__init__.py |  3 ++-
 tests/test_asyncio.py        | 21 +++++++++++++++++++++
 tests/test_tenacity.py       | 21 +++++++++++++++++++++
 4 files changed, 46 insertions(+), 2 deletions(-)

[assistant] The sync and async regression tests now pass, including object identity checks during execution and across repeated calls. The full suite also passes: 167 passed, 1 skipped.
[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m ruff check tenacity/__init__.py tenacity/asyncio/__init__.py tests/test_tenacity.py tests/test_asyncio.py'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed sync and async retry wrappers to preserve the statistics dictionary’s identity through `functools.wraps`.

Added regression tests for live statistics and repeated calls.

Validation: 167 passed, 1 skipped. Ruff was unavailable in the environment.
