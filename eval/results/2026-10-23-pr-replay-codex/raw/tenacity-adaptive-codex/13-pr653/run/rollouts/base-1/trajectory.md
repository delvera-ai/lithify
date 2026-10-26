# trajectory base-1

final message:
Fixed sync and async retry wrappers to preserve the statistics dictionary, keeping outer `functools.wraps` wrappers linked to the same object.

Added regression coverage for object identity, runtime visibility, failed retries, and subsequent successful calls.

Checks passed: 167 tests, 12 subtests; 1 skipped.

## events
[assistant] I’ll inspect how retry wrappers expose statistics, add sync and async regression tests, and run the project checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'statistics|def wraps' tenacity/__init__.py tenacity/asyncio/__init__.py; rg --files -g '*test*' -g AGENTS.md"
tenacity/__init__.py:326:    def statistics(self) -> dict[str, t.Any]:
tenacity/__init__.py:327:        """Return a dictionary of runtime statistics.
tenacity/__init__.py:336:                     change between major releases as new statistics are
tenacity/__init__.py:343:                  their own view of statistics they have collected (in the
tenacity/__init__.py:345:                  statistics from each thread).
tenacity/__init__.py:347:        if not hasattr(self._local, "statistics"):
ten
…[1582 chars elided]…
o/__init__.py:214:            self._local.statistics = copy.statistics
tenacity/asyncio/__init__.py:220:        async_wrapped.statistics = {}  # type: ignore[attr-defined]
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
AGENTS.md
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/test_utils.py

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '300,395p' tenacity/__init__.py"
        )

    def __getstate__(self) -> dict[str, t.Any]:
        # Exclude threading.local which cannot be pickled
        return {k: v for k, v in self.__dict__.items() if k != "_local"}

    def __setstate__(self, state: dict[str, t.Any]) -> None:
        self.__dict__.update(state)
        self._local = threading.local()

    def __str__(self) -> str:
        return self._name if self._name is not None else "<unknown>"

    def __repr__(self) -> str:
        return (
            f"<{self.__
…[2993 chars elided]…
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


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '190,230p' tenacity/asyncio/__init__.py"
            if do is None:
                raise StopAsyncIteration
            if isinstance(do, DoAttempt):
                return AttemptManager(retry_state=self._retry_state)
            if isinstance(do, DoSleep):
                self._retry_state.prepare_for_next_attempt()
                await self.sleep(do)  # type: ignore[misc]
            else:
                raise StopAsyncIteration

    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        wrapped = super().wraps(f
…[697 chars elided]…
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

[command exit=0] /bin/zsh -lc "rtk proxy rg -n 'statistics|import functools' tests/test_tenacity.py tests/test_asyncio.py; rtk git status --short"
tests/test_asyncio.py:291:        self.assertEqual(2, retrying.statistics["attempt_number"])
tests/test_asyncio.py:501:        - statistics contains the value for the latest function run
tests/test_asyncio.py:503:        - retry object statistics are synced with function statistics
tests/test_asyncio.py:517:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:521:            _retryable_coroutine_with_2_attempts.retry.statistics,
tests/test_asyncio.py:542:           
…[3093 chars elided]…
t_tenacity.py:1890:    def test_retry_object_statistics_during_execution(self) -> None:
tests/test_tenacity.py:1891:        """Test that func.retry.statistics is accessible during execution."""
tests/test_tenacity.py:1900:            attempts.append(_foobar.retry.statistics["attempt_number"])
tests/test_tenacity.py:2153:        # Access statistics to populate _local
tests/test_tenacity.py:2154:        _ = retrying.statistics
tests/test_tenacity.py:2159:        assert restored.statistics == {}
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,45p' tests/test_asyncio.py; rtk proxy sed -n '490,560p' tests/test_asyncio.py; rtk proxy sed -n '1840,1910p' tests/test_tenacity.py; rtk proxy head -40 tests/test_tenacity.py"
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
…[5899 chars elided]…
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

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_tenacity.py')
s=p.read_text().replace('import datetime\\n','import datetime\\nimport functools\\n')
needle='class Te
…[1448 chars elided]…
            outer(True)', '            await outer(True)').replace('self.assertEqual(outer(False), 42)', 'self.assertEqual(await outer(False), 42)');s=s.replace(needle,needle+test);p.write_text(s)
PY"

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py::TestStatistics::test_statistics_through_wraps tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_through_wraps'
FF                                                                       [100%]
=================================== FAILURES ===================================
_________________ TestStatistics.test_statistics_through_wraps _________________

self = <tests.test_tenacity.TestStatistics testMethod=test_statistics_through_wraps>

    def test_statistics_through_wraps(self) -> None:
        @retry(stop=tenacity.stop_after_attempt(2))
        def inner(fail: bool) -> int:
            self.assertIs(ou
…[1532 chars elided]…
sertIs(outer.statistics, inner.statistics)
E       AssertionError: {} is not {'start_time': 241870.668158083, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt': 8.72919918037951e-05}

tests/test_asyncio.py:515: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestStatistics::test_statistics_through_wraps
FAILED tests/test_asyncio.py::TestDecoratorWrapper::test_statistics_through_wraps
2 failed in 0.11s

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
for filename, wrapper in [('tenacity/__init__.py', 'wrapped_f'), ('tenacity/asyncio/__init__.py', 'async_wrapped')]:
 p=Path(filename);
…[105 chars elided]…
ined]',f'            # Keep the dictionary shared with decorators using functools.wraps.\\n            copy._local.statistics = {wrapper}.statistics  # type: ignore[attr-defined]');p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
..............s............................................... [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.82s

[assistant] Both regression tests reproduced the bug: each call replaced the statistics dictionary, leaving outer wrappers with the original empty one. Sync and async wrappers now retain that dictionary so outer wrappers can see updates during and after calls. The full test suite is running.
[command exit=0] /bin/zsh -lc 'rtk git diff --stat; rtk git diff --check'
tenacity/__init__.py         |  3 ++-
 tenacity/asyncio/__init__.py |  3 ++-
 tests/test_asyncio.py        | 24 ++++++++++++++++++++++++
 tests/test_tenacity.py       | 24 ++++++++++++++++++++++++
 4 files changed, 52 insertions(+), 2 deletions(-)


[assistant] Fixed sync and async retry wrappers to preserve the statistics dictionary, keeping outer `functools.wraps` wrappers linked to the same object.

Added regression coverage for object identity, runtime visibility, failed retries, and subsequent successful calls.

Checks passed: 167 tests, 12 subtests; 1 skipped.
