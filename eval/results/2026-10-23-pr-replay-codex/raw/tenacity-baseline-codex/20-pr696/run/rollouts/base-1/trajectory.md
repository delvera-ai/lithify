# trajectory base-1

final message:
Fixed Tornado detection to read the live `tenacity.tornado` global at decoration time. Added regression coverage for both `@retry` and `@retry()` when it is `None`.

Tests: 180 passed, 1 skipped. Mypy was unavailable in the test environment.

## events
[assistant] I’ll check how `retry` detects Tornado, make the smallest fix, and run the project’s tests.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'tornado|def retry' tenacity tests; rg --files -g AGENTS.md"
~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202434-bug-setting-the-module-global-te/base-1
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
tests/test_t
…[781 chars elided]…
[P, R]": ...
tenacity/__init__.py:726:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
tenacity/__init__.py:730:def retry(
tenacity/__init__.py:748:def retry(
tenacity/__init__.py:765:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:805:    from tenacity.tornadoweb import TornadoRetrying
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '75,110p;760,815p' tenacity/__init__.py"
    wait_combine,
    wait_exception,
    wait_exponential,
    wait_exponential_jitter,
    wait_fixed,
    wait_incrementing,
    wait_none,
    wait_random,
    wait_random_exponential,
)
from .wait import wait_random_exponential as wait_full_jitter

try:
    import tornado
except ImportError:
    tornado = None  # type: ignore[assignment]

# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
# so testing the module object for truthiness reads as an always-true check.
…[1560 chars elided]…
outine_function")
            and tornado.gen.is_coroutine_function(f)
        ):
            r = TornadoRetrying(*dargs, **dkw)
        else:
            r = Retrying(*dargs, **dkw)

        return r.wraps(f)

    return wrap


from tenacity.asyncio import AsyncRetrying  # noqa: E402

if _HAS_TORNADO:
    from tenacity.tornadoweb import TornadoRetrying


__all__ = [
    "NO_RESULT",
    "AsyncRetrying",
    "AttemptManager",
    "BaseAction",
    "BaseRetrying",
    "DoAttempt",
    "DoSleep",

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,130p' tests/test_tenacity.py"
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
…[3488 chars elided]…
(Retrying()) == "<unknown>"

    def test_str_with_name(self) -> None:
        """With a name, str() returns the given name."""
        assert str(Retrying(name="my_block")) == "my_block"

    def test_str_preserved_by_copy(self) -> None:
        """copy() preserves the name."""
        r = Retrying(name="my_block")
        assert str(r.copy()) == "my_block"

    def test_str_overridden_by_copy(self) -> None:
        """copy() allows overriding the name."""
        r = Retrying(name="original")

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
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
…[2757 chars elided]…
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


[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202434-bug-setting-the-module-global-te/base-1/tenacity/__init__.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202434-bug-setting-the-module-global-te/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
................s................................................................................................................ [ 71%]
....................................................                     [100%]
180 passed, 1 skipped, 15 subtests passed in 1.89s

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m mypy'
<work>/env-tenacity/bin/python: No module named mypy

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed Tornado detection to read the live `tenacity.tornado` global at decoration time. Added regression coverage for both `@retry` and `@retry()` when it is `None`.

Tests: 180 passed, 1 skipped. Mypy was unavailable in the test environment.
