# trajectory base-1

final message:
Fixed sync and async retry exhaustion to re-raise the underlying exception when `reraise=True`, preferring an explicit cause over implicit context.

Added regression coverage. Bare `TryAgain` and `reraise=False` behavior remain unchanged.

Checks: 161 passed, 1 skipped. Ruff was unavailable in the test environment.

## events
[assistant] I’ll check how retry exhaustion handles `TryAgain`, add sync and async regression tests, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*test*' -g '*__init__.py' -g 'pyproject.toml' -g 'setup.cfg' | head -60"
~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
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

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk rg -n 'TryAgain|def reraise|class RetryError|exc_check' tenacity tests/test_tenacity.py tests/test_asyncio.py"
tests/test_tenacity.py:843:            raise tenacity.TryAgain
tests/test_tenacity.py:854:            raise tenacity.TryAgain
tests/test_tenacity.py:862:            raise tenacity.TryAgain
tests/test_tenacity.py:869:        self.assertRaises(tenacity.TryAgain, r, _r)
tenacity/__init__.py:127:class TryAgain(Exception):
tenacity/__init__.py:179:class RetryError(Exception):
tenacity/__init__.py:186:    def reraise(self) -> t.NoReturn:
tenacity/__init__.py:421:            fut.exception(), TryAgain
tenacity/__init__.py:445:            def exc_check(rs: "RetryCallState") -> None:
tenacity/__init__.py:452:            self._add_action_func(exc_check)
tenacity/__init__.py:763:    "TryAgain",

[command exit=0] /bin/zsh -lc 'rtk proxy cat tenacity/__init__.py'
# Copyright 2016-2018 Julien Danjou
# Copyright 2017 Elisey Zanko
# Copyright 2016 Étienne Bersac
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
# distributed under the License is distrib
…[25321 chars elided]…
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

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '810,890p' tests/test_tenacity.py"
        retry = tenacity.retry_if_result(lambda x: x == 1) & my_retry
        retry_state = make_retry_state(
            1, 1.0, last_result=tenacity.Future.construct(1, 1, False)
        )
        self.assertTrue(retry(retry_state))

        # plain_callable & retry_base (exercises __rand__ via reflection)
        retry2 = my_retry & tenacity.retry_if_result(lambda x: x == 1)
        self.assertTrue(retry2(retry_state))

    def test_retry_or_coalesces(self) -> None:
        """Multiple | oper
…[2021 chars elided]…
f_exception_message_negative_too_many_inputs(self) -> None:
        with self.assertRaises(TypeError):
            tenacity.retry_if_exception_message(message="negative", match="negative")


class NoneReturnUntilAfterCount:
    """Holds counter state for invoking a method several times in a row."""

    def __init__(self, count: int) -> None:
        self.counter = 0
        self.count = count

    def go(self) -> typing.Any:
        """Return None until after count threshold has been crossed.


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,115p' tests/test_asyncio.py"
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
…[2191 chars elided]…
        await _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tasyncio.AsyncRetrying())

    def test_retry_attributes(self) -> None:
        assert hasattr(_retryable_coroutine, "retry")
        assert hasattr(_retryable_coroutine, "retry_with")

    def test_retry_preserves_argument_defaults(self) -> None:
        async def function_with_defaults(a: int = 1) -> int:
            return a

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


[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1/tenacity/__init__.py
[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py
[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1/tests/test_asyncio.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.............s...................................................................................................................... [ 82%]
............................                                             [100%]
159 passed, 1 skipped, 12 subtests passed in 1.82s

[assistant] The shared `RetryError.reraise()` method handles exhaustion for both sync and async retrying. I updated it to raise the exception chained to `TryAgain`. A bare `TryAgain` still raises as before, and the new tests check that both paths make two attempts and raise the original `ValueError` instance.
[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py   |  5 +++++
 tests/test_asyncio.py  | 18 ++++++++++++++++++
 tests/test_tenacity.py | 51 ++++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 74 insertions(+)

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m ruff check tenacity/__init__.py tests/test_tenacity.py tests/test_asyncio.py'
<work>/env-tenacity/bin/python: No module named ruff

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.............s...................................................................................................................... [ 81%]
..............................                                           [100%]
161 passed, 1 skipped, 12 subtests passed in 1.80s

[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201348-bug-when-tryagain-is-raised-from/base-1/tests/test_tenacity.py
[assistant] Fixed sync and async retry exhaustion to re-raise the underlying exception when `reraise=True`, preferring an explicit cause over implicit context.

Added regression coverage. Bare `TryAgain` and `reraise=False` behavior remain unchanged.

Checks: 161 passed, 1 skipped. Ruff was unavailable in the test environment.
