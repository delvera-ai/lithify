# trajectory base-1

final message:
`a | b | c` and `a & b & c` now each produce one container whose `retries` holds the three members, for both sync and async strategies. The full suite passes and the changed-file checker is clean. I did not commit.

**The fix**
- `tenacity/_utils.py`: new `flatten_retries(kind, *operands)`. It splices in an operand's members only when its type is exactly `kind`, so a subclass that overrides `__call__` stays as one member.
- `tenacity/retry.py` and `tenacity/asyncio/retry.py`: the four operator methods in each (`__and__`, `__rand__`, `__or__`, `__ror__`) build their container through that helper. The short-circuit order is unchanged, because the members are evaluated in the same left-to-right order as before.

**Tests**
- Regression tests written first and run against the unfixed code. All four failed on the nested `retry_any` object in `retries`. They were:
  - `tests/test_tenacity.py`: `test_retry_or_chain_is_flat`, `test_retry_and_chain_is_flat`, `test_retry_chain_with_plain_function_is_flat`
  - `tests/test_asyncio.py`: `test_async_retry_chains_are_flat`
- After the fix, all four pass.
- Full suite via `run_tests.py`: `exit=0`, 148 passed, 1 skipped. I did not check whether the skip was already there before my change.
- `check_changed.py`: exit 0, 0 problems.
- ruff and mypy were not run (unavailable in this environment), so the lint and typing checks are unverified.

**Release note**
- `releasenotes/notes/flatten-retry-chains-a1b807578efa8090.yaml`, under `other:`, since behaviour is unchanged. Use `fixes:` if you'd rather it show up as a fix.

**Choices you may want to redirect**
- Flattening is type-exact. Mixed sync/async chains are only flattened when both operands are the same family. For example, `sync_any | async_b` still produces an async `retry_any` that holds the sync `retry_any` as one member.
- I did not add user docs. The contract only requires them when documented usage changes, and it doesn't here.

## events
[assistant] I'll start by reading the composition code and the change-contract skill this task falls under.
[tool_use Bash] {"command": "git status --short && ls && cat .lithify/harness/skills/tenacity-change-contract/SKILL.md && grep -n \"retry_any\\|retry_all\\|__or__\\|__and__\\|class \\|retries\" tenacity/retry.py | head -80 && cat .lithify/memory.md 2>/dev/null | head -20", "description": "Inspect repo state, skill, and retry code"}
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
---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version) — i.e. any
…[10365 chars elided]…
:class retry_any(retry_base):
259:    """Retries if any of the retries condition is valid."""
261:    def __init__(self, *retries: "RetryBaseT") -> None:
262:        self.retries = retries
265:        return any(r(retry_state) for r in self.retries)
268:class retry_all(retry_base):
269:    """Retries if all the retries condition are valid."""
271:    def __init__(self, *retries: "RetryBaseT") -> None:
272:        self.retries = retries
275:        return all(r(retry_state) for r in self.retries)
[assistant] Only the sync `retry.py` was in that output, so next I'll read the async combinators and the existing composition tests.
[tool_use Bash] {"command": "sed -n 1,60p tenacity/retry.py && sed -n 250,280p tenacity/retry.py && echo ---ASYNC && cat tenacity/asyncio/retry.py && echo ---TESTS && grep -n \"retry_any\\|retry_all\\|__or__\\|\\bor\\b.*retry\\|_ror\\|_rand\" tests/*.py | head -60 && ls releasenotes/notes | tail -3 && cat releasenotes/notes/$(ls releasenotes/notes | tail -1)", "description": "Read retry combinators, async retry, and tests"}
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
…[8009 chars elided]…
k)
tests/test_tenacity.py:759:        # plain_callable | retry_base (exercises __ror__ via reflection)
tests/test_tenacity.py:776:        # plain_callable & retry_base (exercises __rand__ via reflection)
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[assistant] The sync and async combinators are structurally the same, so one flattening helper can serve both. Next I'll check the existing tests, `_utils` imports (to avoid a cycle), and the reno config.
[tool_use Bash] {"command": "sed -n 1,40p tenacity/_utils.py | grep -n \"import\" ; sed -n 680,800p tests/test_tenacity.py; echo ---ASYNC; sed -n 340,440p tests/test_asyncio.py; echo ---REno; cat reno.yaml; grep -rn \"retry_any\\|retry_all\" doc/source/index.rst | head", "description": "Read existing composition tests and config"}
[tool_result] 16:import contextlib
17:import functools
18:import inspect
19:import sys
20:import typing
21:from datetime import timedelta

        def r(fut: tenacity.Future) -> bool:
            retry_state = make_retry_state(1, 1.0, last_result=fut)
            return retry(retry_state)

        self.assertTrue(r(tenacity.Future.construct(1, 2, False)))
        self.assertFalse(r(tenacity.Future.construct(1, 1, False)))

    def test_retry_any(self) -> None:
        retry = tenacity.retry_any(
            t
…[7414 chars elided]…
         attempt.retry_state.set_result(attempts)

            return attempts

        result = await test()

        self.assertEqual(3, result)

    @asynctest
    async def test_async_retying_iterator(self) -> None:
        thing = NoIOErrorAfterCount(5)
        with pytest.raises(TypeError):
            for attempts in AsyncRetrying():
                with attempts:
---REno
---
unreleased_version_title: Unreleased
doc/source/index.rst:260:    retry_any
doc/source/index.rst:261:    retry_all
[assistant] I have what I need. Per the harness, the regression tests come first. I'll add a sync and an async test that assert the chain is flat, then run them against the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_tenacity.py", "old_string": "        # plain_callable & retry_base (exercises __rand__ via reflection)\n        retry2 = my_retry & tenacity.retry_if_result(lambda x: x == 1)\n        self.assertTrue(retry2(retry_state))\n", "new_string": "   
…[963 chars elided]…
n_function_is_flat(self) -> None:\n        def my_retry(retry_state: tenacity.RetryCallState) -> bool:\n            return True\n\n        a = tenacity.retry_if_result(lambda x: x == 1)\n        b = tenacity.retry_if_result(lambda x: x == 2)\n\n        retry = my_retry | a | b\n\n        self.assertIsInstance(retry, tenacity.retry_any)\n        self.assertEqual((my_retry, a, b), retry.retries)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_asyncio.py", "old_string": "        retry_strategy = retry_if_result(gt_0) & tasyncio.retry_if_result(lt_3)\n            async for attempt in tasyncio.AsyncRetrying(retry=retry_strategy):\n                with attempt:\n                    att
…[942 chars elided]…
lt(is_two)\n        c = tasyncio.retry_if_result(is_three)\n\n        retry_any_chain = a | b | c\n        self.assertIsInstance(retry_any_chain, tasyncio.retry_any)\n        self.assertEqual((a, b, c), retry_any_chain.retries)\n\n        retry_all_chain = a & b & c\n        self.assertIsInstance(retry_all_chain, tasyncio.retry_all)\n        self.assertEqual((a, b, c), retry_all_chain.retries)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_asyncio.py has been updated successfully.
[assistant] Next I'll run the new tests alone against the unfixed code, through the harness runner and the project interpreter named in CLAUDE.md.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestRetry::test_retry_or_chain_is_flat tests/test_tenacity.py::TestRetry::test_retry_and_chain_is_flat tests/test_tenacity.py::TestRetry::test_retry_chain_with_plain_function_is_flat tests/test_asyncio.py::TestContextManager::test_async_retry_chains_are_flat > /tmp/red1.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red1.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
exit=4
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <tmp>/-Users-user-Coding-delvera-foun
…[668 chars elided]…
/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_tenacity.py::TestRetry::test_retry_and_chain_is_flat
(no match in any of [<Module test_tenacity.py>])

ERROR: not found: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tests/test_tenacity.py::TestRetry::test_retry_chain_with_plain_function_is_flat
(no match in any of [<Module test_tenacity.py>])

---
exit=4 (pytest); full log: /tmp/run_tests.log
[assistant] The node IDs are wrong: the sync tests sit in a different class. I'll find the actual class names and re-run.
[tool_use Bash] {"command": "grep -n \"^class \\|def test_retry_or_chain_is_flat\\|def test_async_retry_chains_are_flat\" tests/test_tenacity.py tests/test_asyncio.py | awk -F: '$2<2000' | tail -40", "description": "Find test class names for node IDs"}
[tool_result] tests/test_asyncio.py:79:class TestAsyncio(unittest.TestCase):
tests/test_asyncio.py:163:class TestAsyncEnabled(unittest.TestCase):
tests/test_asyncio.py:181:class TestTrio(unittest.TestCase):
tests/test_asyncio.py:195:class TestContextManager(unittest.TestCase):
tests/test_asyncio.py:435:    def test_async_retry_chains_are_flat(self) -> None:
tests/test_asyncio.py:466:class TestDecoratorWrapper(unittest.TestCase):
tests/test_asyncio.py:535:class TestSyncFunctionWithAsyncSleep(unittest.TestCase)
…[1357 chars elided]…
Exceptions(unittest.TestCase):
tests/test_tenacity.py:1758:class TestStatistics(unittest.TestCase):
tests/test_tenacity.py:1779:class TestRetryErrorCallback(unittest.TestCase):
tests/test_tenacity.py:1812:class TestContextManager(unittest.TestCase):
tests/test_tenacity.py:1867:class TestInvokeAsCallable:
tests/test_tenacity.py:1937:class TestRetryException(unittest.TestCase):
tests/test_tenacity.py:1947:class TestRetryTyping(unittest.TestCase):
tests/test_tenacity.py:1982:class TestMockingSleep:
[assistant] The sync tests belong to `TestRetryConditions` and the async one to `TestContextManager` in `test_asyncio.py`. Re-running with those IDs:
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestRetryConditions::test_retry_or_chain_is_flat tests/test_tenacity.py::TestRetryConditions::test_retry_and_chain_is_flat tests/test_tenacity.py::TestRetryConditions::test_retry_chain_with_plain_function_is_flat tests/test_asyncio.py::TestContextManager::test_async_retry_chains_are_flat > /tmp/red1.txt 2>&1; echo \"exit=$?\"; grep -n \"AssertionError\\|FAILED\\|passed\\|failed\\|Error\" /tmp/red1.txt | head -30; tail -5 /tmp/red1.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
15:E       AssertionError: Tuples differ: (<ten[21 chars]etry_if_result object at 0x1074227b0>, <tenaci[115 chars]5f0>) != (<ten[21 chars]etry_any object at 0x107421340>, <tenacity.asy[45 chars]5f0>)
34:tests/test_asyncio.py:451: AssertionError
36:FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_or_chain_is_flat
37:FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_and_chain_is_flat
38:FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_chain_with_plain_function_is_flat
39:FAILED tests/test_asyncio.py::TestContextManager::test_async_retry_chains_are_flat
40:============================== 4 failed in 0.05s ===============================
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_chain_with_plain_function_is_flat
FAILED tests/test_asyncio.py::TestContextManager::test_async_retry_chains_are_flat
============================== 4 failed in 0.05s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All four new tests fail on the unfixed code, and the failure is the reported one: `retries` holds a nested `retry_any` object rather than the three members. Before writing the fix I'll check how the modules import `_utils` and where a helper fits.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" tenacity/*.py tenacity/asyncio/*.py | grep -v \"typing\\|__future__\" ; grep -n \"^def \\|^T = \\|^_T\" tenacity/_utils.py", "description": "Check import patterns and _utils layout"}
[tool_result] tenacity/after.py:19:from tenacity import _utils
tenacity/__init__.py:18:import dataclasses
tenacity/__init__.py:19:import functools
tenacity/__init__.py:20:import sys
tenacity/__init__.py:21:import threading
tenacity/__init__.py:22:import time
tenacity/__init__.py:24:import warnings
tenacity/__init__.py:25:from abc import ABC, abstractmethod
tenacity/__init__.py:26:from concurrent import futures
tenacity/__init__.py:28:from . import _utils
tenacity/__init__.py:31:from .after import after_log, a
…[1487 chars elided]…
b.py:20:from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState
tenacity/asyncio/retry.py:16:import abc
tenacity/asyncio/retry.py:19:from tenacity import _utils, retry_base
40:def find_ordinal(pos_num: int) -> str:
59:def to_ordinal(pos_num: int) -> str:
63:def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
86:def to_seconds(time_unit: time_unit_type) -> float:
92:def is_coroutine_callable(call: typing.Callable[..., typing.Any]) -> bool:
102:def wrap_to_async_func(
[assistant] `_utils` is already imported by `wait.py`, `stop.py` and the async retry module, so the shared helper goes there. I'll read the end of the file to place it.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/_utils.py", "offset": 90}
[tool_result] 90	
91	
92	def is_coroutine_callable(call: typing.Callable[..., typing.Any]) -> bool:
93	    if inspect.isclass(call):
94	        return False
95	    if inspect.iscoroutinefunction(call):
96	        return True
97	    partial_call = isinstance(call, functools.partial) and call.func
98	    dunder_call = partial_call or getattr(call, "__call__", None)  # noqa: B004
99	    return inspect.iscoroutinefunction(dunder_call)
100	
101	
102	def wrap_to_async_func(
103	    call: typing.Callable[..., typing.Any],
104	) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
105	    if is_coroutine_callable(call):
106	        return call
107	
108	    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
109	        return call(*args, **kwargs)
110	
111	    return inner
112	
[assistant] I'll add one helper to `_utils`. It splices in members only from operands of exactly the combinator's type, so a subclass that overrides `__call__` is never flattened away.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/_utils.py", "old_string": "    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:\n        return call(*args, **kwargs)\n\n    return inner\n", "new_string": "    async def inner(*args: typing.Any, **kwargs: typing.Any) -> t
…[191 chars elided]…
*...)``, splicing in operands of exactly ``kind``.\n\n    Only the exact type is spliced: a subclass may override ``__call__``, so it is kept\n    as a single member.\n    \"\"\"\n    members: list[typing.Any] = []\n    for operand in operands:\n        if type(operand) is kind:\n            members.extend(operand.retries)\n        else:\n            members.append(operand)\n    return members\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/_utils.py has been updated successfully.
[assistant] Next, the four sync operator methods in `retry.py`. I'll route them through the helper.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/retry.py", "old_string": "import abc\nimport re\nimport typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState\n\n\nclass retry_base(abc.ABC):\n    \"\"\"Abstract base class for retry strategies.\"\"\"\n\n    @abc.abstractme
…[1356 chars elided]…
n_retries(retry_all, other, self))\n\n    def __or__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        if isinstance(other, retry_base):\n            return other.__ror__(self)\n        return retry_any(*_utils.flatten_retries(retry_any, self, other))\n\n    def __ror__(self, other: \"RetryBaseT\") -> \"retry_any\":\n        return retry_any(*_utils.flatten_retries(retry_any, other, self))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/retry.py has been updated successfully.
[assistant] Now the async operators in `asyncio/retry.py`, which already import `_utils`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py", "old_string": "    def __and__(  # type: ignore[override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_all\":\n        return retry_all(self, other)\n\n    def __rand__(  # type: ignore[misc,overri
…[893 chars elided]…
f __or__(  # type: ignore[override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_utils.flatten_retries(retry_any, self, other))\n\n    def __ror__(  # type: ignore[misc,override]\n        self, other: \"retry_base | async_retry_base\"\n    ) -> \"retry_any\":\n        return retry_any(*_utils.flatten_retries(retry_any, other, self))"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-201420-improvement-composing-several-re/base-1/tenacity/asyncio/retry.py has been updated successfully.
[assistant] All four edits are in. I'll re-run the four target tests, which should now pass.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestRetryConditions::test_retry_or_chain_is_flat tests/test_tenacity.py::TestRetryConditions::test_retry_and_chain_is_flat tests/test_tenacity.py::TestRetryConditions::test_retry_chain_with_plain_function_is_flat tests/test_asyncio.py::TestContextManager::test_async_retry_chains_are_flat > /tmp/green1.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green1.txt", "description": "Run the regression tests after the fix"}
[tool_result] exit=0

============================== 4 passed in 0.03s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The four target tests pass. Next is the reno release note. The change is behaviour-preserving, so it goes under `other:` rather than `fixes:`. I'll generate the 16-hex suffix the contract asks for.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8) && echo \"$H\" && printf '%s\\n' \"---\" \"other:\" \"  - |\" \"    Chaining retry conditions with \\`\\`|\\`\\` or \\`\\`&\\`\\` now builds a single \\`\\`retry_any\\`\\` or\" \"    \\`\\`retry_all\\`\\` whose \\`\\`retries\\`\\` holds every member, instead of nesting one container\" \"    per operator. The combined condition's behaviour is unchanged.\" > releasenotes/notes/flatten-retry-chains-$H.yaml && cat releasenotes/notes/flatten-retry-chains-$H.yaml", "description": "Create reno release note for the change"}
[tool_result] a1b807578efa8090
---
other:
  - |
    Chaining retry conditions with ``|`` or ``&`` now builds a single ``retry_any`` or
    ``retry_all`` whose ``retries`` holds every member, instead of nesting one container
    per operator. The combined condition's behaviour is unchanged.
[assistant] Now the full suite through the harness runner, in the foreground, then the stdlib checker.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt; echo ---CHECK; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check_exit=$?\"; cat /tmp/check.txt | tail -20", "description": "Run full test suite and changed-file checks"}
[tool_result] exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 148 passed, 1 skipped, 12 subtests passed in 1.79s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---CHECK
check_exit=0
changed: releasenotes/notes/flatten-retry-chains-a1b807578efa8090.yaml, tenacity/_utils.py, tenacity/asyncio/retry.py, tenacity/retry.py, tests/test_asyncio.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] `a | b | c` and `a & b & c` now each produce one container whose `retries` holds the three members, for both sync and async strategies. The full suite passes and the changed-file checker is clean. I did not commit.

**The fix**
- `tenacity/_utils.py`: new `flatten_retries(kind, *operands)`. It splices in an operand's members only when its type is exactly `kind`, so a subclass that overrides `__call__` stays as one member.
- `tenacity/retry.py` and `tenacity/asyncio/retry.py`: the four operator methods in each (`__and__`, `__rand__`, `__or__`, `__ror__`) build their container through that helpe
…[750 chars elided]…
the lint and typing checks are unverified.

**Release note**
- `releasenotes/notes/flatten-retry-chains-a1b807578efa8090.yaml`, under `other:`, since behaviour is unchanged. Use `fixes:` if you'd rather it show up as a fix.

**Choices you may want to redirect**
- Flattening is type-exact. Mixed sync/async chains are only flattened when both operands are the same family. For example, `sync_any | async_b` still produces an async `retry_any` that holds the sync `retry_any` as one member.
- I did not add user docs. The contract only requires them when documented usage changes, and it doesn't here.
