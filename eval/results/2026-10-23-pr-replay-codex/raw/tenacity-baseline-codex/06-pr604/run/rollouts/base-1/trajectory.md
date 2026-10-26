# trajectory base-1

final message:
Implemented `enabled=True` for `Retrying`, `AsyncRetrying`, and `@retry`.

With `enabled=False`, calls run exactly once, bypass retry callbacks and sleeps, and propagate exceptions unchanged. Supports `copy()` and `retry_with()`. Added documentation and regression tests.

Checks: 155 passed, 1 skipped. Ruff was unavailable in the project environment.

## events
[assistant] I’ll check how the retry controllers and decorator call functions, add the bypass, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*test*' -g '*__init__.py' -g '*async*' -g 'pyproject.toml' -g 'setup.cfg'"
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
…[365 chars elided]…
actions-b249c527d99723bb.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
releasenotes/notes/fix-async-loop-with-result-f68e913ccb425aca.yaml
AGENTS.md
tenacity/asyncio/__init__.py
tenacity/__init__.py
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/__init__.py
tests/test_utils.py
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '200,570p' tenacity/__init__.py"

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: t.Optional["types.TracebackType"],
    ) -> bool | None:
        if exc_type is not None and exc_value is not None:
            self.retry_state.set_exception((exc_type, exc_value, traceback))
            return True  # Swallow exception.
        # We don't have the result, actually.
        self.retry_state.set_
…[12896 chars elided]…
 decided by the retry manager
        self.next_action: RetryAction | None = None
        #: Next sleep time as decided by the retry manager.
        self.upcoming_sleep: float = 0.0

    def get_fn_name(self) -> str:
        """Get the name of the function being retried.

        Returns the fully-qualified name of the wrapped function when used as a
        decorator, the ``name`` passed to the retrying object when used as a
        context manager, or ``"<unknown>"`` if neither is available.

[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/asyncio/__init__.py'
# Copyright 2016 Étienne Bersac
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
# WITHOUT
…[6747 chars elided]…
copy(fn, *args, **kwargs)  # type: ignore[type-var]

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
    "retry_if_result",
]

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '640,760p' tenacity/__init__.py"
        self, fn: t.Callable[P, t.Coroutine[t.Any, t.Any, R]]
    ) -> "_RetryDecorated[P, t.Coroutine[t.Any, t.Any, R]]": ...
    @t.overload
    def __call__(
        self, fn: t.Callable[P, t.Awaitable[R]]
    ) -> "_RetryDecorated[P, t.Awaitable[R]]": ...
    @t.overload
    def __call__(
        self, fn: t.Callable[P, R]
    ) -> "_RetryDecorated[P, t.Awaitable[R]]": ...


@t.overload
def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...


@t.overload
def retry(
    *,
    sleep:
…[2806 chars elided]…
rying",
    "AttemptManager",
    "BaseAction",
    "BaseRetrying",
    "DoAttempt",
    "DoSleep",
    "Future",
    "RetryAction",
    "RetryCallState",
    "RetryError",
    "Retrying",
    "TryAgain",
    "WrappedFn",
    "after_log",
    "after_nothing",
    "before_log",
    "before_nothing",
    "before_sleep_log",
    "before_sleep_nothing",
    "retry",
    "retry_all",
    "retry_always",
    "retry_any",
    "retry_base",
    "retry_if_exception",
    "retry_if_exception_cause_type",

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
    "Lice
…[2092 chars elided]…
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


[command exit=0] /bin/zsh -lc "rtk proxy rg -n 'retry_with|copy\\(|pytest.mark.asyncio|def test.*retry|Retrying' tests/test_asyncio.py tests/test_tenacity.py doc/source/index.rst"
doc/source/index.rst:500:            loglevel, 'Retrying %s: attempt %s ended with: %s',
doc/source/index.rst:545:    from tenacity import Retrying
doc/source/index.rst:547:    for attempt in Retrying(stop=stop_after_attempt(3)):
doc/source/index.rst:563:using the `retry_with` function attached to the wrapped function:
doc/source/index.rst:572:        raise_my_exception.retry_with(stop=stop_after_attempt(4))()
doc/source/index.rst:584:to use the `retry` decorator - you can instead use `Retrying`
…[12637 chars elided]…
ty.py:1841:        retry = Retrying(reraise=True, stop=tenacity.stop_after_attempt(2))
tests/test_tenacity.py:1848:    def test_retry_error_is_pickleable(self) -> None:
tests/test_tenacity.py:1858:    def test_retry_type_annotations(self) -> None:
tests/test_tenacity.py:1883:    oldfilters = copy(warnings.filters)
tests/test_tenacity.py:1924:    def test_decorated_retry_with(self, mock_sleep: typing.Any) -> None:
tests/test_tenacity.py:1925:        fail_faster = self._decorated_fail.retry_with(

[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/tornadoweb.py'
# Copyright 2017 Elisey Zanko
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
# See the License for the speci
…[1091 chars elided]…
      if isinstance(do, DoAttempt):
                try:
                    result = yield fn(*args, **kwargs)
                except BaseException:
                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]
                else:
                    retry_state.set_result(result)
            elif isinstance(do, DoSleep):
                retry_state.prepare_for_next_attempt()
                yield self.sleep(do)
            else:
                raise gen.Return(do)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '15,85p' tests/test_asyncio.py"
import asyncio
import inspect
import unittest
from collections.abc import Callable, Coroutine
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
from tenacity import asyncio as tasyn
…[551 chars elided]…
le_coroutine(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry(stop=stop_after_attempt(2))
async def _retryable_coroutine_with_2_attempts(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


class TestAsyncio(unittest.TestCase):
    @asynctest
    async def test_retry(self) -> None:
        thing = NoIOErrorAfterCount(5)
        await _retryable_coroutine(thing)
        assert thing.counter == thing.count


[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/__init__.py')
s=p.read_text().replace('        name: str | None = None,\\n','        name: str | None = None,\\n      
…[1450 chars elided]…
text().replace('        self.begin()\\n','        if not self.enabled:\\n            result = yield fn(*args, **kwargs)\\n            return result\\n\\n        self.begin()\\n',1);p.write_text(s)
PY"

[assistant] The bypass is in place before retry processing begins. The setting is also preserved by `copy()` and can be changed with `retry_with()`. I’ll test that disabled calls preserve arguments, results, and exception identity without invoking retry callbacks.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
Path('tests/test_enabled.py').write_text('''import asyncio
from typing import Any
from unittest import mock

import pytest

from tenaci
…[3420 chars elided]…
arameter, defaulting to True, to retry controllers and the
    retry decorator. With enabled=False, functions are called once without retry
    processing and exceptions propagate unchanged.
''')
PY
"

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...........s........................................................ [ 43%]
................................................................ [ 84%]
........................                                                 [100%]
155 passed, 1 skipped, 12 subtests passed in 1.84s

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_enabled.py');s=p.read_text().replace('    options = dict(\\n','    options: Any = dict(\\n').replace('    wrapped = 
…[377 chars elided]…
 asyncio.run(result)\\n        return result\\n').replace('    assert wrapped.statistics == {}\\n','    assert (wrapped.statistics if wrapped else controller.statistics) == {}\\n');p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk proxy git diff --stat'
 doc/source/index.rst         | 17 +++++++++++++++++
 tenacity/__init__.py         |  9 +++++++++
 tenacity/asyncio/__init__.py |  5 +++++
 tenacity/tornadoweb.py       |  4 ++++
 4 files changed, 35 insertions(+)

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m ruff check tenacity tests/test_enabled.py'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=0] /bin/zsh -lc 'rtk proxy git status --short'
 M doc/source/index.rst
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
?? releasenotes/notes/enabled-parameter.yaml
?? tests/test_enabled.py

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_enabled.py'
................                                                         [100%]
16 passed in 0.02s

[command exit=0] /bin/zsh -lc 'rtk proxy git diff --check'

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...........s........................................................ [ 43%]
................................................................ [ 84%]
........................                                                 [100%]
155 passed, 1 skipped, 12 subtests passed in 1.79s

[assistant] Implemented `enabled=True` for `Retrying`, `AsyncRetrying`, and `@retry`.

With `enabled=False`, calls run exactly once, bypass retry callbacks and sleeps, and propagate exceptions unchanged. Supports `copy()` and `retry_with()`. Added documentation and regression tests.

Checks: 155 passed, 1 skipped. Ruff was unavailable in the project environment.
