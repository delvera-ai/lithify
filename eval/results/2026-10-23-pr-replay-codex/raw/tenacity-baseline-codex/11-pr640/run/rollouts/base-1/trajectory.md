# trajectory base-1

final message:
Fixed the shared re-raise path: with `reraise=True`, `TryAgain` now re-raises its underlying exception when present. Standalone `TryAgain` behavior is preserved.

Added sync and async regression tests. Full suite: **159 passed, 1 skipped**.

## events
[assistant] I’ll trace how `TryAgain` reaches the final re-raise, add sync and async regression tests, and run the project checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'TryAgain|def reraise|class RetryError' tenacity tests; rg --files -g AGENTS.md -g '*toml' -g 'setup.cfg'"
tests/test_tenacity.py:843:            raise tenacity.TryAgain
tests/test_tenacity.py:854:            raise tenacity.TryAgain
tests/test_tenacity.py:862:            raise tenacity.TryAgain
tests/test_tenacity.py:869:        self.assertRaises(tenacity.TryAgain, r, _r)
tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:179:class RetryError(Exception):
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:421:            fut.exception(), TryAgain
tenacity/__init__.py:763:    "TryAgain",
AGENTS.md
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '170,205p;370,465p' tenacity/__init__.py"


_unset = object()


def _first_set(first: t.Any | object, second: t.Any) -> t.Any:
    return second if first is _unset else first


class RetryError(Exception):
    """Encapsulates the last attempt instance right before giving up."""

    def __init__(self, last_attempt: "Future") -> None:
        self.last_attempt = last_attempt
        super().__init__(last_attempt)

    def reraise(self) -> t.NoReturn:
        if self.last_attempt.failed:
            raise self.last_attempt.result()
      
…[3440 chars elided]…
rom fut.exception()

            self._add_action_func(exc_check)
            return

        def next_action(rs: "RetryCallState") -> None:
            sleep = rs.upcoming_sleep
            rs.next_action = RetryAction(sleep)
            rs.idle_for += sleep
            self.statistics["idle_for"] += sleep
            self.statistics["attempt_number"] += 1

        self._add_action_func(next_action)

        if self.before_sleep is not None:
            self._add_action_func(self.before_sleep)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '790,900p' tests/test_tenacity.py"
            return retry_state.outcome is not None and not retry_state.outcome.failed

        # retry_base | plain_callable (exercises __or__ fallback)
        retry = tenacity.retry_if_exception_type(Exception) | my_retry
        retry_state = make_retry_state(
            1, 1.0, last_result=tenacity.Future.construct(1, "ok", False)
        )
        self.assertTrue(retry(retry_state))

        # plain_callable | retry_base (exercises __ror__ via reflection)
        retry2 = my_retry | tenaci
…[3148 chars elided]…
invoking a method several times in a row."""

    def __init__(self, count: int) -> None:
        self.counter = 0
        self.count = count

    def go(self) -> typing.Any:
        """Return None until after count threshold has been crossed.

        Then return True.
        """
        if self.counter < self.count:
            self.counter += 1
            return None
        return True


class NoIOErrorAfterCount:
    """Holds counter state for invoking a method several times in a row."""

[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml;'
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


[command exit=0] /bin/zsh -lc 'rtk proxy ls tests;'
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,100p' tests/test_asyncio.py"
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
…[1674 chars elided]…
ction(self) -> None:
        assert asyncio.iscoroutinefunction(_retryable_coroutine)
        assert inspect.iscoroutinefunction(_retryable_coroutine)

    @asynctest
    async def test_retry_using_async_retying(self) -> None:
        thing = NoIOErrorAfterCount(5)
        retrying = AsyncRetrying()
        await retrying(_async_function, thing)
        assert thing.counter == thing.count

    @asynctest
    async def test_stop_after_attempt(self) -> None:
        thing = NoIOErrorAfterCount(2)

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201357-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201357-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py
[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py tests/test_asyncio.py -k reraises_context'
FF                                                                       [100%]
=================================== FAILURES ===================================
__________ TestRetryConditions.test_retry_try_again_reraises_context ___________

    def call() -> None:
        try:
>           raise error

tests/test_tenacity.py:877: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def call() -> None:
        try:
>           raise error
E           ValueError:
…[4230 chars elided]…
_ _ _ _ _ _ _ _ 

    async def call() -> None:
        try:
            raise error
        except ValueError:
>           raise tenacity.TryAgain
E           tenacity.TryAgain

tests/test_asyncio.py:88: TryAgain
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_try_again_reraises_context
FAILED tests/test_asyncio.py::TestAsyncio::test_retry_try_again_reraises_context
2 failed, 147 deselected in 0.20s

[assistant] Both regression tests reproduce the bug. Sync and async retrying share `RetryError.reraise()`, so the fix can live there and preserve the existing behavior for a `TryAgain` raised without an underlying exception.
[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201357-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.............s...................................................................................................................... [ 82%]
............................                                             [100%]
159 passed, 1 skipped, 12 subtests passed in 1.80s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py   |  3 +++
 tests/test_asyncio.py  | 20 ++++++++++++++++++++
 tests/test_tenacity.py | 19 +++++++++++++++++++
 3 files changed, 42 insertions(+)

[assistant] Fixed the shared re-raise path: with `reraise=True`, `TryAgain` now re-raises its underlying exception when present. Standalone `TryAgain` behavior is preserved.

Added sync and async regression tests. Full suite: **159 passed, 1 skipped**.
