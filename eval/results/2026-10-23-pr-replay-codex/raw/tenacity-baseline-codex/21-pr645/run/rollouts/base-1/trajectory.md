# trajectory base-1

final message:
Fixed both direct-call paths to honor `enabled=False`: they call the function once, preserve its result or original exception, and await coroutine functions in the async version.

Added regression coverage for success, exception identity, argument forwarding, and call counts.

Validation: 182 passed, 1 skipped, 15 subtests passed.

## events
[assistant] I’ll check the direct-call paths, add a regression test, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*retry*' -g 'test*' -g 'pyproject.toml' -g 'setup.cfg'"
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
…[260 chars elided]…
22bd544800cd1f36.yaml
releasenotes/notes/fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
releasenotes/notes/add_retry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
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

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git status --short; rg -n \"enabled|def __call__\" tenacity/__init__.py tenacity/asyncio/__init__.py tests/test_tenacity.py tests/test_asyncio.py; cat pyproject.toml'"
tests/test_asyncio.py:203:    async def test_enabled_false_skips_retry(self) -> None:
tests/test_asyncio.py:204:        """When enabled=False, async function is called directly without retrying."""
tests/test_asyncio.py:207:        @retry(enabled=False, stop=stop_after_attempt(3))
tests/test_asyncio.py:218:    async def test_enabled_false_aiter_raises_original_exception(self) -> None:
tests/test_asyncio.py:219:        """When enabled=False, the async iterator raises the original exception,
tests
…[6671 chars elided]…
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


[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"360,395p;490,570p\" tenacity/__init__.py; sed -n \"110,145p;200,240p\" tenacity/asyncio/__init__.py; sed -n \"1635,1745p\" tests/test_tenacity.py; sed -n \"170,255p\" tests/test_asyncio.py; rg -n \"wrap_to_async_func\" tenacity/_utils.py'"
                  statistics from each thread).
        """
        if not hasattr(self._local, "statistics"):
            self._local.statistics = t.cast("dict[str, t.Any]", {})
        return self._local.statistics  # type: ignore[no-any-return]

    @property
    def iter_state(self) -> IterState:
        if not hasattr(self._local, "iter_state"):
            self._local.iter_state = IterState()
        return self._local.iter_state  # type: ignore[no-any-return]

    def wraps(self, f: t.Cal
…[13551 chars elided]…
           stop=stop_after_attempt(5),
        )
        async for attempt in retrying:
            with attempt:
                call_count += 1
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
class TestTrio(unittest.TestCase):
    def test_trio_basic(self) -> None:
        thing = NoIOErrorAfterCount(5)

        @retry
        async def trio_function() -> Any:
            await trio.sleep(0.00001)
            return thing.go()
123:def wrap_to_async_func(

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"118,140p\" tenacity/_utils.py; sed -n \"20,60p\" tenacity/asyncio/__init__.py; sed -n \"15,50p\" tests/test_asyncio.py'"
    partial_call = isinstance(call, functools.partial) and call.func
    dunder_call = partial_call or getattr(call, "__call__", None)  # noqa: B004
    return inspect.iscoroutinefunction(dunder_call)


def wrap_to_async_func(
    call: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
    if is_coroutine_callable(call):
        return call

    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return call(*args, **kwargs)

 
…[1178 chars elided]…
ar
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
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)


[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_tenacity.py')
s=p.read_text(); marker='class TestEnabled:\\n'; s=s.replace(marker,marker+'''    @pytest.mark.paramet
…[1893 chars elided]…
  assert exc_info.value is error
                else:
                    assert await retrying(target, result, fail=False) is result
                assert call_count == 1

''');p.write_text(s)
PY
"

[command exit=1] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py tests/test_asyncio.py -k enabled_false_direct_call'
.FF                                                                      [100%]
=================================== FAILURES ===================================
_______________ TestEnabled.test_enabled_false_direct_call[True] _______________

value = <object object at 0x102cc9b20>, fail = True

    def fn(value: object, *, fail: bool) -> object:
        nonlocal call_count
        call_count += 1
        if fail:
>           raise error

tests/test_tenacity.py:1664: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ 
…[6594 chars elided]…
:
            retry_exc.reraise()
>       raise retry_exc from fut.exception()
E       tenacity.RetryError: RetryError[<Future at 0x1097097f0 state=finished raised ValueError>]

tenacity/__init__.py:481: RetryError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestEnabled::test_enabled_false_direct_call[True]
FAILED tests/test_asyncio.py::TestAsyncEnabled::test_enabled_false_direct_call
2 failed, 1 passed, 168 deselected in 0.16s

[assistant] The regression tests reproduce the `RetryError` wrapping. Both direct-call methods enter the retry loop without checking `enabled`. I’ll add an early return, using the existing async helper to handle both synchronous and coroutine callables.
[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/__init__.py'); s=p.read_text(); marker='''    ) -> WrappedFnReturnT:
        self.begin()
'''; assert s.count(marker)=
…[274 chars elided]…
 -> WrappedFnReturnT:
        if not self.enabled:
            return await _utils.wrap_to_async_func(fn)(*args, **kwargs)  # type: ignore[no-any-return]

        self.begin()
''');p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'command -v ruff; command -v mypy; git diff --check; git diff --stat'"
 tenacity/__init__.py         |  3 +++
 tenacity/asyncio/__init__.py |  3 +++
 tests/test_asyncio.py        | 29 +++++++++++++++++++++++++++++
 tests/test_tenacity.py       | 22 ++++++++++++++++++++++
 4 files changed, 57 insertions(+)

[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.................s.............................................. [ 34%]
................................................................. [ 70%]
......................................................                   [100%]
182 passed, 1 skipped, 15 subtests passed in 1.82s

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'ls <work>/env-tenacity/bin | head -25; git diff --check'"
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
py.test
pydoc.bat
pygmentize
pytest
python
python3
python3.12

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_asyncio.py');s=p.read_text();start=s.index('        for is_async in (False, True):', s.index('class TestAsyncEnabled
…[212 chars elided]…
ils: bool) -> None:\\n'+body+'\\n\\n        for is_async in (False, True):\\n            for fails in (False, True):\\n                await check_call(is_async, fails)\\n'+s[end:];p.write_text(s)
PY"

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
.................s.............................................. [ 34%]
................................................................. [ 70%]
......................................................                   [100%]
182 passed, 1 skipped, 15 subtests passed in 1.80s

[assistant] Fixed both direct-call paths to honor `enabled=False`: they call the function once, preserve its result or original exception, and await coroutine functions in the async version.

Added regression coverage for success, exception identity, argument forwarding, and call counts.

Validation: 182 passed, 1 skipped, 15 subtests passed.
