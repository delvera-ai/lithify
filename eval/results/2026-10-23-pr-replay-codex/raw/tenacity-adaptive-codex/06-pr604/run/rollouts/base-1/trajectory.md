# trajectory base-1

final message:
Implemented `enabled=True` for `Retrying`, `AsyncRetrying`, and `@retry`.

With `enabled=False`, calls run exactly once, bypass retry hooks and waits, and propagate the original exception unchanged. Supports `copy()` and `retry_with()`; documentation and regression tests added.

Validation: 161 passed, 1 skipped. Ruff checks unavailable because Ruff isn’t installed.

## events
[assistant] I’ll check how the retry controllers and decorator call functions, add the bypass, and run the project’s checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*py' -g 'pyproject.toml' -g 'tox.ini' | head -60"
~/.cache/lithify/work/repo-553f5f2e6879/20261023-200633-feature-add-an-enabled-parameter/base-1
AGENTS.md
doc/source/conf.py
tenacity/_utils.py
tenacity/asyncio/retry.py
tenacity/asyncio/__init__.py
tenacity/tornadoweb.py
tenacity/retry.py
tenacity/after.py
tenacity/nap.py
tenacity/__init__.py
tenacity/wait.py
tenacity/stop.py
tenacity/_version.py
tenacity/before_sleep.py
tenacity/before.py
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/__init__.py
tests/test_utils.py
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '210,340p' tenacity/__init__.py"
        if exc_type is not None and exc_value is not None:
            self.retry_state.set_exception((exc_type, exc_value, traceback))
            return True  # Swallow exception.
        # We don't have the result, actually.
        self.retry_state.set_result(None)
        return None

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: t.Optional
…[4447 chars elided]…
.statistics = t.cast("dict[str, t.Any]", {})
        return self._local.statistics  # type: ignore[no-any-return]

    @property
    def iter_state(self) -> IterState:
        if not hasattr(self._local, "iter_state"):
            self._local.iter_state = IterState()
        return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
        """Wrap a function for retrying.

        :param f: A function to wrap for retrying.

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '440,680p' tenacity/__init__.py"
        def next_action(rs: "RetryCallState") -> None:
            sleep = rs.upcoming_sleep
            rs.next_action = RetryAction(sleep)
            rs.idle_for += sleep
            self.statistics["idle_for"] += sleep
            self.statistics["attempt_number"] += 1

        self._add_action_func(next_action)

        if self.before_sleep is not None:
            self._add_action_func(self.before_sleep)

        self._add_action_func(lambda rs: DoSleep(rs.upcoming_sleep))

    def __iter_
…[7114 chars elided]…
["RetryCallState"], t.Any | t.Awaitable[t.Any]]
    | None = ...,
) -> _AsyncRetryDecorator: ...


@t.overload
def retry(
    sleep: t.Callable[[int | float], None] = sleep,
    stop: "StopBaseT" = stop_never,
    wait: "WaitBaseT" = wait_none(),
    retry: "RetryBaseT | tasyncio.retry.RetryBaseT" = retry_if_exception_type(),
    before: t.Callable[["RetryCallState"], None | t.Awaitable[None]] = before_nothing,
    after: t.Callable[["RetryCallState"], None | t.Awaitable[None]] = after_nothing,

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

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '675,760p' tenacity/__init__.py"
    sleep: t.Callable[[int | float], None] = sleep,
    stop: "StopBaseT" = stop_never,
    wait: "WaitBaseT" = wait_none(),
    retry: "RetryBaseT | tasyncio.retry.RetryBaseT" = retry_if_exception_type(),
    before: t.Callable[["RetryCallState"], None | t.Awaitable[None]] = before_nothing,
    after: t.Callable[["RetryCallState"], None | t.Awaitable[None]] = after_nothing,
    before_sleep: t.Callable[["RetryCallState"], None | t.Awaitable[None]]
    | None = None,
    reraise: bool = False,
 
…[1671 chars elided]…
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

[command exit=0] /bin/zsh -lc 'rtk proxy head -85 tests/test_asyncio.py'
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
…[1126 chars elided]…
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


[command exit=0] /bin/zsh -lc "rtk proxy rg -n 'retry_with|copy\\(|name=|Disabl' tests/test_tenacity.py doc/source/index.rst"
doc/source/index.rst:563:using the `retry_with` function attached to the wrapped function:
doc/source/index.rst:572:        raise_my_exception.retry_with(stop=stop_after_attempt(4))()
tests/test_tenacity.py:121:        assert str(Retrying(name="my_block")) == "my_block"
tests/test_tenacity.py:123:    def test_str_preserved_by_copy(self) -> None:
tests/test_tenacity.py:124:        """copy() preserves the name."""
tests/test_tenacity.py:125:        r = Retrying(name="my_block")
tests/test_tenacity
…[680 chars elided]…
 = _retryable_test_with_stop.retry_with(
tests/test_tenacity.py:1430:            _retryable.retry_with(stop=tenacity.stop_after_attempt(2))()
tests/test_tenacity.py:1442:        result = _retryable.retry_with(stop=tenacity.stop_after_attempt(5))()
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

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p = Path('tenacity/__init__.py')
s = p.read_text().replace('        name: str | None = None,\\n', '        name: str | None = None,\\n 
…[1487 chars elided]…
_text().replace('        self.begin()\\n', '        if not self.enabled:\\n            result = yield fn(*args, **kwargs)\\n            return result\\n        self.begin()\\n', 1)
p.write_text(s)
PY"

[assistant] The bypass is in place before retry state or callbacks run. I also added `enabled` to `copy()` so it carries through decorated calls and can be overridden with `retry_with()`. Next I’ll check single-call behavior, return values, exception identity, and that retry hooks stay unused.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
Path('tests/test_enabled.py').write_text('''from unittest import mock

import pytest

from tenacity import AsyncRetrying, Retrying, Try
…[3880 chars elided]…
g decorated function with
``development_call.retry_with(enabled=False)()``.

'"'''
if idx < 0:
    raise RuntimeError('missing documentation anchor')
s = s[:idx] + prefix + s[idx:]
p.write_text(s)
PY"
              raise MyException("not yet")

.. testoutput::
   :hide:

   ...


Changing Arguments at Run Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can change th

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...........s........................................................ [ 41%]
................................................................ [ 81%]
..............................                                           [100%]
161 passed, 1 skipped, 12 subtests passed in 1.84s

[command exit=1] /bin/zsh -lc 'rtk proxy python -m ruff check tenacity tests/test_enabled.py'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=1] /bin/zsh -lc 'rtk proxy python -m ruff format --check tenacity tests/test_enabled.py'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=0] /bin/zsh -lc 'rtk proxy git diff --stat'
 doc/source/index.rst         | 17 +++++++++++++++++
 tenacity/__init__.py         |  8 ++++++++
 tenacity/asyncio/__init__.py |  4 ++++
 tenacity/tornadoweb.py       |  3 +++
 4 files changed, 32 insertions(+)

[command exit=0] /bin/zsh -lc 'rtk proxy git diff -- tenacity/__init__.py tenacity/asyncio/__init__.py tenacity/tornadoweb.py'
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 57af68a..23cc9bb 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -240,7 +240,9 @@ class BaseRetrying(ABC):
         retry_error_cls: type[RetryError] = RetryError,
         retry_error_callback: t.Callable[["RetryCallState"], t.Any] | None = None,
         name: str | None = None,
+        enabled: bool = True,
     ):
+        self.enabled = enabled
         self.sleep = sleep
         self.stop = stop
         self.
…[2557 chars elided]…
/tornadoweb.py
index 0d46ed7..deecce3 100644
--- a/tenacity/tornadoweb.py
+++ b/tenacity/tornadoweb.py
@@ -43,6 +43,9 @@ class TornadoRetrying(BaseRetrying):
         *args: typing.Any,
         **kwargs: typing.Any,
     ) -> "typing.Generator[typing.Any, typing.Any, _RetValT]":
+        if not self.enabled:
+            result = yield fn(*args, **kwargs)
+            return result
         self.begin()
 
         retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)

[command exit=1] /bin/zsh -lc 'rtk proxy which ruff mypy uv'
~/.local/bin/uv

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p = Path('tests/test_enabled.py')
s = p.read_text().replace('from unittest import mock\\n', 'import asyncio\\nfrom typing import Any\\n
…[622 chars elided]…
 -> Any:\\n        if decorate:\\n            return wrapped(*args, **kwargs)\\n        return controller(fn, *args, **kwargs)\\n\\n')
s = s.replace('    import asyncio\\n\\n', '')
p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...........s........................................................ [ 41%]
................................................................ [ 81%]
..............................                                           [100%]
161 passed, 1 skipped, 12 subtests passed in 1.77s

[command exit=0] /bin/zsh -lc 'rtk git status --short'
 M doc/source/index.rst
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
?? tests/test_enabled.py
[assistant] Implemented `enabled=True` for `Retrying`, `AsyncRetrying`, and `@retry`.

With `enabled=False`, calls run exactly once, bypass retry hooks and waits, and propagate the original exception unchanged. Supports `copy()` and `retry_with()`; documentation and regression tests added.

Validation: 161 passed, 1 skipped. Ruff checks unavailable because Ruff isn’t installed.
