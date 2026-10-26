# trajectory base-1

final message:
Chained `|` and `&` now build one `retry_any` or `retry_all` whose `.retries` holds every condition, for both the sync and async strategies. The full suite passes: 150 passed, 1 skipped (up from 144 passed, since I added six tests).

What changed:

- **`tenacity/retry.py`**: a small `_flatten_retries` helper. The sync operators use it, so `a | b | c` and `a & b & c` produce one flat container.
- **`tenacity/asyncio/retry.py`**: the async operators use the same helper. They also absorb sync containers, so mixed chains like `sync | sync | async` stay flat. An async container already awaits sync members, so the behaviour is the same.
- **Tests**: new cases in `tests/test_tenacity.py` and `tests/test_asyncio.py` cover flattening for `|` and `&`, right-grouped chains, plain callables, the mixed sync/async case, and the result values. I did not edit any existing test.
- **Release note**: `releasenotes/notes/flatten-retry-composition-3c1f8e2a9b7d4f10.yaml`, since `.retries` is now visible to users. Drop it if you'd rather not have one.

Decisions for you to check:

- **Exact type, not `isinstance`.** Only containers of exactly `retry_any` or `retry_all` are merged. A user subclass that overrides `__call__` stays a single member, so its behaviour can't be lost. There is a test for this.
- **Explicit construction is unchanged.** `retry_any(retry_any(a, b), c)` still nests, because the request was about the operators. Flattening in the constructor would change what people pass in directly.
- **Evaluation order is unchanged.** Members are still checked left to right with short-circuiting, so the combined result matches the old nested form.

I did not run mypy or ruff: neither is installed in the project's test environment. I checked by hand that none of my added lines go past the 88-column limit. I also did not commit anything.

## events
[assistant] I'll start by finding where `|` and `&` build the retry containers.
[tool_use Bash] {"command": "git status --short && grep -rn \"retry_any\\|retry_all\\|__or__\\|__and__\\|__ror__\\|__rand__\" --include=*.py . | grep -v \"/tests/\" | head -80", "description": "Locate retry_any/retry_all and operator definitions"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rln \"retry_any\" . --exclude-dir=.git | head -30", "description": "Find files referencing retry_any"}
[tool_result] tests/test_tenacity.py
tenacity/__init__.py
tenacity/retry.py
tenacity/asyncio/retry.py
tenacity/asyncio/__init__.py
doc/source/index.rst
[tool_use Bash] {"command": "cat tenacity/retry.py | head -150; echo ----; cat tenacity/asyncio/retry.py", "description": "Read sync and async retry modules"}
[tool_result] # Copyright 2016–2021 Julien Danjou
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
…[7869 chars elided]…



class retry_all(async_retry_base):
    """Retries if all the retries condition are valid."""

    def __init__(self, *retries: retry_base | async_retry_base) -> None:
        self.retries = retries

    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
        result = True
        for r in self.retries:
            result = result and await _utils.wrap_to_async_func(r)(retry_state)
            if not result:
                break
        return result
[tool_use Bash] {"command": "grep -n \"class retry_any\" -A 40 tenacity/retry.py; grep -n \"class retry_all\" -A 25 tenacity/retry.py; echo ----; grep -n \"__or__\\|__and__\\|retry_any\\|retry_all\\|\\.retries\" tests/test_tenacity.py | head -60; ls tests; cat tenacity/asyncio/__init__.py | grep -n \"retry_any\\|retry_all\\|import\"", "description": "Read retry_any/all classes and related tests"}
[tool_result] 258:class retry_any(retry_base):
259-    """Retries if any of the retries condition is valid."""
260-
261-    def __init__(self, *retries: "RetryBaseT") -> None:
262-        self.retries = retries
263-
264-    def __call__(self, retry_state: "RetryCallState") -> bool:
265-        return any(r(retry_state) for r in self.retries)
266-
267-
268-class retry_all(retry_base):
269-    """Retries if all the retries condition are valid."""
270-
271-    def __init__(self, *retries: "RetryBaseT") -> None:

…[1080 chars elided]…
 from tenacity.retry import RetryBaseT as SyncRetryBaseT
47:    from tenacity.stop import StopBaseT
48:    from tenacity.wait import WaitBaseT
57:    # If trio is already imported, then importing it is cheap.
58:    # If trio isn't already imported, then it's definitely not running, so we
62:        import sniffio
63:        import trio
68:    # Lazy import asyncio as it's expensive (responsible for 25-50% of total import overhead).
69:    import asyncio
213:    "retry_all",
214:    "retry_any",
[assistant] The sync and async `retry_any`/`retry_all` classes are separate, and the operators build nested containers. Next I'll read the existing operator tests and check the test-runner path from the project notes.
[tool_use Bash] {"command": "sed -n 680,800p tests/test_tenacity.py; echo ----; grep -n \"retry_any\\|retry_all\\|retry_base\" tenacity/__init__.py; echo ----; ls <work>/env-tenacity/bin/python 2>&1; grep -n \"retry_any\\|retry_all\\|__or__\\|__and__\" tests/test_asyncio.py | head", "description": "Read operator tests and check test environment"}
[tool_result]         def r(fut: tenacity.Future) -> bool:
            retry_state = make_retry_state(1, 1.0, last_result=fut)
            return retry(retry_state)

        self.assertTrue(r(tenacity.Future.construct(1, 2, False)))
        self.assertFalse(r(tenacity.Future.construct(1, 1, False)))

    def test_retry_any(self) -> None:
        retry = tenacity.retry_any(
            tenacity.retry_if_result(lambda x: x == 1),
            tenacity.retry_if_result(lambda x: x == 2),
        )

        def r(f
…[4474 chars elided]…
forever_reraise(self) -> None:
----
44:    retry_all,
46:    retry_any,
47:    retry_base,
264:        retry: retry_base | object = _unset,
709:        if isinstance(f, retry_base):
711:                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
763:    "retry_all",
765:    "retry_any",
766:    "retry_base",
----
<work>/env-tenacity/bin/python
[assistant] The project's test interpreter exists. I'll run the baseline suite before changing anything.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run baseline test suite"}
[tool_result] ............s............................................... [ 41%]
........................................................................ [ 91%]
.............                                                            [100%]
144 passed, 1 skipped, 12 subtests passed in 1.86s
[assistant] Baseline is green: 144 passed, 1 skipped. Plan:

- Add one helper in `tenacity/retry.py` that expands an operand when its exact type is the container being built. Exact type, not `isinstance`, so a user subclass that overrides `__call__` is never silently flattened away.
- Sync operators flatten sync containers only.
- Async operators flatten async containers and sync ones too, since an async container already accepts sync members. That covers mixed chains like `sync | sync | async`.

Starting with the sync module:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py", "old_string": "RetryBaseT = retry_base | typing.Callable[[\"RetryCallState\"], bool]\n\n\nclass _retry_never(retry_base):", "new_string": "RetryBaseT = retry_base | typing.Callable[[\"RetryCallState\"], bool]\n\n\ndef _flatten_retries
…[23 chars elided]…
], *operands: typing.Any) -> list[typing.Any]:\n    \"\"\"Expand operands of the given container types so chained ``|``/``&`` stay flat.\"\"\"\n    retries: list[typing.Any] = []\n    for operand in operands:\n        if type(operand) in kinds:\n            retries.extend(operand.retries)\n        else:\n            retries.append(operand)\n    return retries\n\n\nclass _retry_never(retry_base):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py", "old_string": "        return retry_all(self, other)\n\n    def __rand__(self, other: \"RetryBaseT\") -> \"retry_all\":\n        return retry_all(other, self)\n\n    def __or__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        i
…[403 chars elided]…
tten_retries((retry_all,), other, self))\n\n    def __or__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        if isinstance(other, retry_base):\n            return other.__ror__(self)\n        return retry_any(*_flatten_retries((retry_any,), self, other))\n\n    def __ror__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        return retry_any(*_flatten_retries((retry_any,), other, self))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 60,70p tenacity/retry.py | head -3; grep -n \"^line-length\\|line_length\\|max-line\" pyproject.toml setup.cfg tox.ini .pre-commit-config.yaml 2>/dev/null; grep -n \"^def \\|^from\\|^import\" tenacity/_utils.py | head", "description": "Check line-length config and utils"}
[tool_result]     return retries


100:line-length = 88
16:import contextlib
17:import functools
18:import inspect
19:import sys
20:import typing
21:from datetime import timedelta
40:def find_ordinal(pos_num: int) -> str:
59:def to_ordinal(pos_num: int) -> str:
63:def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
86:def to_seconds(time_unit: time_unit_type) -> float:
[assistant] The helper's signature and docstring lines run past the 88-column limit in `pyproject.toml`. Fixing that before the async side:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py", "old_string": "def _flatten_retries(kinds: tuple[type, ...], *operands: typing.Any) -> list[typing.Any]:\n    \"\"\"Expand operands of the given container types so chained ``|``/``&`` stay flat.\"\"\"", "new_string": "def _flatten_retries(\n    kinds: tuple[type, ...], *operands: typing.Any\n) -> list[typing.Any]:\n    \"\"\"Expand operands of the given containers so chained ``|``/``&`` stay flat.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py", "old_string": "from tenacity import _utils, retry_base\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n\n\nclass async_retry_base(retry_base):\n    \"\"\"Abstract base class for async retry strategies.\"\
…[1675 chars elided]…
\n\n    def __or__(  # type: ignore[override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_flatten_retries(_any_kinds, self, other))\n\n    def __ror__(  # type: ignore[misc,override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_flatten_retries(_any_kinds, other, self))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py has been updated successfully.
[assistant] I referenced `_sync_retry`, `_all_kinds` and `_any_kinds` without defining them. Rather than add module globals, I'll import the sync containers by name and pass the tuples inline:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py", "old_string": "from tenacity import _utils, retry_base\nfrom tenacity import retry as _sync_retry\nfrom tenacity.retry import _flatten_retries\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n\n\nclass asy
…[2113 chars elided]…
override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_flatten_retries((retry_any, _sync_retry_any), self, other))\n\n    def __ror__(  # type: ignore[misc,override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_flatten_retries((retry_any, _sync_retry_any), other, self))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -c \"\nimport tenacity as t\nfrom tenacity.asyncio import retry as ar\na=t.retry_if_result(lambda x: x==1); b=t.retry_if_result(lambda x: x==2); c=t.retry_if_re
…[266 chars elided]…
)\nr=ar.retry_if_result(lambda x: x==1)|ar.retry_if_result(lambda x: x==2)|a; print(type(r).__name__, len(r.retries))\nr=a|b|ar.retry_if_result(lambda x: x==3); print(type(r).__name__, len(r.retries))\n\"; $PY -m mypy tenacity 2>&1 | tail -3; $PY -m ruff check tenacity 2>&1 | tail -3; $PY -m ruff format --check tenacity 2>&1 | tail -3", "description": "Run tests, flattening checks, mypy and ruff"}
[tool_result] ........................................................................ [ 91%]
.............                                                            [100%]
144 passed, 1 skipped, 12 subtests passed in 1.79s
retry_any 3 retry_if_result
retry_all 3
retry_any 3
retry_any 3
retry_any 3
retry_any 3
<work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[assistant] Flattening works in every case I tried, and the existing 144 tests still pass. mypy and ruff aren't installed in the project env, so I'll check line lengths by hand. Next I'll look at the async test file's structure so I can add regression tests in the right style.
[tool_use Bash] {"command": "grep -n \"^class \\|^def \\|^import\\|^from\\|async def test_\\|asyncio.run\\|retry_any\\|retry_all\\|retry_if_result\" tests/test_asyncio.py | head -60; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/retry.py tenacity/asyncio/retry.py", "description": "Inspect async test structure and line lengths"}
[tool_result] 15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
30:import pytest
32:import tenacity
33:from tenacity import (
39:    retry_if_result,
42:from tenacity import asyncio as tasyncio
43:from tenacity.wait import wait_fixed
45:from .test_tenacity import (
54:def asynctest(callable_: _F) -> Callable[..., Any]:
57:        return asyncio.run(callable_(*a
…[1837 chars elided]…
  async def test_retry_function_attributes(self) -> None:
513:class TestSyncFunctionWithAsyncSleep(unittest.TestCase):
515:    async def test_sync_function_with_async_sleep(self) -> None:
524:            retry=retry_if_result(lambda x: x is None),
tenacity/retry.py: 155: 90
tenacity/retry.py: 220: 90
tenacity/retry.py: 239: 95
tenacity/asyncio/retry.py: 32: 94
tenacity/asyncio/retry.py: 70: 94
tenacity/asyncio/retry.py: 90: 94
tenacity/asyncio/retry.py: 105: 94
tenacity/asyncio/retry.py: 120: 94
[assistant] The over-88 lines in those files are all pre-existing, none of mine. Before writing async tests I need the pattern the file uses to run coroutine test methods.
[tool_use Bash] {"command": "sed -n 44,80p tests/test_asyncio.py; sed -n 388,412p tests/test_asyncio.py; sed -n 160,180p tests/test_asyncio.py", "description": "Read async test helpers and an example test"}
[tool_result] from .test_tenacity import (
    NoIOErrorAfterCount,
    NoneReturnUntilAfterCount,
    current_time_ms,
)

_F = TypeVar("_F", bound=Callable[..., Coroutine[Any, Any, Any]])


def asynctest(callable_: _F) -> Callable[..., Any]:
    @wraps(callable_)
    def wrapper(*a: Any, **kw: Any) -> Any:
        return asyncio.run(callable_(*a, **kw))

    return wrapper


async def _async_function(thing: NoIOErrorAfterCount) -> Any:
    await asyncio.sleep(0.00001)
    return thing.go()


@retry
async def
…[1171 chars elided]…
try(self) -> None:
        """When enabled=False, async function is called directly without retrying."""
        call_count = 0

        @retry(enabled=False, stop=stop_after_attempt(3))
        async def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            await always_fails()
        assert call_count == 1


@unittest.skipIf(not have_trio, "trio not installed")
[assistant] I'll confirm `make_retry_state` is a module-level helper in `test_tenacity.py` so the async tests can reuse it, then write the regression tests.
[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A 12 tests/test_tenacity.py; grep -n \"def test_retry_and_with_plain_function\\|def _raise_try_again\" tests/test_tenacity.py", "description": "Find make_retry_state helper and insertion point"}
[tool_result] 55:def make_retry_state(
56-    previous_attempt_number: typing.Any,
57-    delay_since_first_attempt: typing.Any,
58-    last_result: typing.Any = None,
59-    upcoming_sleep: typing.Any = 0,
60-) -> RetryCallState:
61-    """Construct RetryCallState for given attempt number & delay.
62-
63-    Only used in testing and thus is extra careful about timestamp arithmetics.
64-    """
65-    required_parameter_unset = (
66-        previous_attempt_number is _unset or delay_since_first_attempt is _unset
67-    )
763:    def test_retry_and_with_plain_function(self) -> None:
780:    def _raise_try_again(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_tenacity.py", "old_string": "        # plain_callable & retry_base (exercises __rand__ via reflection)\n        retry2 = my_retry & tenacity.retry_if_result(lambda x: x == 1)\n        self.assertTrue(retry2(retry_state))\n", "new_string": "   
…[2361 chars elided]…
 single member.\"\"\"\n\n        class my_any(tenacity.retry_any):\n            pass\n\n        a = tenacity.retry_if_result(lambda x: x == 1)\n        b = tenacity.retry_if_result(lambda x: x == 2)\n\n        retry = my_any(a, b) | a\n        self.assertIs(type(retry), tenacity.retry_any)\n        self.assertEqual(2, len(retry.retries))\n        self.assertIsInstance(retry.retries[0], my_any)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_asyncio.py", "old_string": "class TestAsyncEnabled(unittest.TestCase):", "new_string": "class TestRetryComposition(unittest.TestCase):\n    @asynctest\n    async def test_async_chain_is_flat(self) -> None:\n        async def lt_3(x: float) -> 
…[1118 chars elided]…
y_any)\n        self.assertEqual((a, b, c), any_retry.retries)\n\n        for value, expected in [(1, True), (2, True), (3, True), (4, False)]:\n            retry_state = make_retry_state(\n                1, 1.0, last_result=tenacity.Future.construct(1, value, False)\n            )\n            self.assertIs(expected, await any_retry(retry_state))\n\n\nclass TestAsyncEnabled(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] The async test calls `make_retry_state`, which `test_asyncio.py` doesn't import yet. Adding it to the existing `.test_tenacity` import block:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_asyncio.py", "old_string": "from .test_tenacity import (\n    NoIOErrorAfterCount,\n    NoneReturnUntilAfterCount,\n    current_time_ms,\n)", "new_string": "from .test_tenacity import (\n    NoIOErrorAfterCount,\n    NoneReturnUntilAfterCount,\n    current_time_ms,\n    make_retry_state,\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; git stash list | head -0; git diff -U0 -- tenacity | grep '^+' | awk 'length > 89 {print \"LONG: \"$0}'", "description": "Run full test suite and check added line lengths"}
[tool_result] ..............s..................................................................................................................... [ 87%]
...................                                                      [100%]
150 passed, 1 skipped, 12 subtests passed in 1.85s
---
head: illegal line count -- 0
[assistant] Full suite passes: 150 passed, up from 144 with the six new tests, and no added line runs past 88 columns. Last, I'll check whether the docs or a changelog describe the operators and need a note.
[tool_use Bash] {"command": "ls; grep -n \"retry_any\\|retry_all\\| | \\| & \" doc/source/index.rst | head; git status --short; git diff --stat", "description": "Check docs/changelog mentions and diff summary"}
[tool_result] AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
144:    @retry(stop=(stop_after_delay(10) | stop_after_attempt(5)))
260:    retry_any
261:    retry_all
271:    @retry(retry=(retry_if_result(is_none_p) | retry_if_exception_type()))
 M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
 tenacity/asyncio/retry.py | 12 ++++++---
 tenacity/retry.py         | 21 +++++++++++++---
 tests/test_asyncio.py     | 51 ++++++++++++++++++++++++++++++++++++++
 tests/test_tenacity.py    | 63 +++++++++++++++++++++++++++++++++++++++++++++++
 4 files changed, 139 insertions(+), 8 deletions(-)
[assistant] The repo uses `reno` release notes, and there's an `AGENTS.md` I haven't read. I'll check whether it asks for a release note with each change.
[tool_use Bash] {"command": "cat AGENTS.md | head -60; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | tail -1)", "description": "Read AGENTS.md and a recent release note"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[237 chars elided]…
ratchpad/pr-work/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[assistant] The repo's convention is one `reno` note per user-visible change, and this changes the `.retries` structure users can inspect. I'll add a short note.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/releasenotes/notes/flatten-retry-composition-3c1f8e2a9b7d4f10.yaml", "content": "---\nother:\n  - |\n    Chaining ``|`` or ``&`` between retry conditions now builds a single\n    ``retry_any`` or ``retry_all`` holding every condition in ``.retries``,\n    instead of nesting them. The behaviour of the combined condition is\n    unchanged. This applies to the async retry strategies as well.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163439-improvement-composing-several-re/base-1/releasenotes/notes/flatten-retry-composition-3c1f8e2a9b7d4f10.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git diff -- tenacity", "description": "Rerun tests and review final library diff"}
[tool_result] ...................                                                      [100%]
150 passed, 1 skipped, 12 subtests passed in 1.83s
diff --git a/tenacity/asyncio/retry.py b/tenacity/asyncio/retry.py
index cbb332e..5452fa7 100644
--- a/tenacity/asyncio/retry.py
+++ b/tenacity/asyncio/retry.py
@@ -17,6 +17,9 @@ import abc
 import typing
 
 from tenacity import _utils, retry_base
+from tenacity.retry import _flatten_retries
+from tenacity.retry import retry_all as _sync_retry_all
+from tenacity.retr
…[2492 chars elided]…
 
 
+def _flatten_retries(
+    kinds: tuple[type, ...], *operands: typing.Any
+) -> list[typing.Any]:
+    """Expand operands of the given containers so chained ``|``/``&`` stay flat."""
+    retries: list[typing.Any] = []
+    for operand in operands:
+        if type(operand) in kinds:
+            retries.extend(operand.retries)
+        else:
+            retries.append(operand)
+    return retries
+
+
 class _retry_never(retry_base):
     """Retry strategy that never rejects any result."""
[assistant] Chained `|` and `&` now build one `retry_any` or `retry_all` whose `.retries` holds every condition, for both the sync and async strategies. The full suite passes: 150 passed, 1 skipped (up from 144 passed, since I added six tests).

What changed:

- **`tenacity/retry.py`**: a small `_flatten_retries` helper. The sync operators use it, so `a | b | c` and `a & b & c` produce one flat container.
- **`tenacity/asyncio/retry.py`**: the async operators use the same helper. They also absorb sync containers, so mixed chains like `sync | sync | async` stay flat. An async container already awaits sync 
…[648 chars elided]…
 behaviour can't be lost. There is a test for this.
- **Explicit construction is unchanged.** `retry_any(retry_any(a, b), c)` still nests, because the request was about the operators. Flattening in the constructor would change what people pass in directly.
- **Evaluation order is unchanged.** Members are still checked left to right with short-circuiting, so the combined result matches the old nested form.

I did not run mypy or ruff: neither is installed in the project's test environment. I checked by hand that none of my added lines go past the 88-column limit. I also did not commit anything.
