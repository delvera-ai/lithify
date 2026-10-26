# trajectory inv-1

final message:
`find_ordinal` now gives "th" for 111, 112 and 113, and every other number keeps its suffix. The full test suite passes: 126 passed, 1 skipped.

The fix is one new branch in `tenacity/_utils.py`. The function recursed on `pos_num % 10`, which turned 111 into 1 and gave "st". The new branch checks `pos_num % 100` against 11, 12 and 13 before that recursion, so 111, 1011, 1111 and similar numbers get "th".

I also added a `test_to_ordinal` test to `tests/test_utils.py` covering the teen cases and some neighbouring numbers. I didn't modify any existing test. The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include='*.py' . ; echo ---; cat \"$(grep -rl 'def find_ordinal' --include='*.py' .)\"", "description": "Locate find_ordinal and show its source"}
[tool_result] tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
---
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/lice
…[2408 chars elided]…
   partial_call = isinstance(call, functools.partial) and call.func
    dunder_call = partial_call or getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(dunder_call)


def wrap_to_async_func(
    call: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
    if is_coroutine_callable(call):
        return call

    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return call(*args, **kwargs)

    return inner
[assistant] The bug is clear: `find_ordinal` recurses on `pos_num % 10`, so 111 drops to 1 and gets "st". I'll add a branch for the teen values (11, 12, 13) under the last two digits before the recursion. First I'll check the existing tests and the project interpreter.
[tool_use Bash] {"command": "grep -rn \"ordinal\" tests/ | head -30; ls <work>/env-tenacity/bin/python 2>&1", "description": "Find ordinal tests and check interpreter path"}
[tool_result] tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
<work>/env-tenacity/bin/python
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/inv-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif pos_num % 100 in (11, 12, 13):\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/inv-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [1,2,3,4,11,12,13,21,22,23,101,102,103,111,112,113,114,121,1011,1012,1013,1111]:\n    print(to_ordinal(n))\n\"", "description": "Check ordinal output for sample numbers"}
[tool_result] 1st
2nd
3rd
4th
11th
12th
13th
21st
22nd
23rd
101st
102nd
103rd
111th
112th
113th
114th
121st
1011th
1012th
1013th
1111th
[assistant] Sample outputs match the spec. Now I'll run the project checks, and look for an existing utils test file to add a regression case to.
[tool_use Bash] {"command": "ls tests/; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "List tests and run the full test suite"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.82s
[tool_use Bash] {"command": "cat tests/test_utils.py", "description": "Read existing utils tests"}
[tool_result] import functools

from tenacity import _utils


def test_is_coroutine_callable() -> None:
    async def async_func() -> None:
        pass

    def sync_func() -> None:
        pass

    class AsyncClass:
        async def __call__(self) -> None:
            pass

    class SyncClass:
        def __call__(self) -> None:
            pass

    lambda_fn = lambda: None  # noqa: E731

    partial_async_func = functools.partial(async_func)
    partial_sync_func = functools.partial(sync_func)
    part
…[445 chars elided]…
outine_callable(SyncClass) is False
    assert _utils.is_coroutine_callable(SyncClass()) is False
    assert _utils.is_coroutine_callable(lambda_fn) is False

    assert _utils.is_coroutine_callable(partial_async_func) is True
    assert _utils.is_coroutine_callable(partial_sync_func) is False
    assert _utils.is_coroutine_callable(partial_async_class) is True
    assert _utils.is_coroutine_callable(partial_sync_class) is False
    assert _utils.is_coroutine_callable(partial_lambda_fn) is False
[assistant] The existing suite passes. I'll add a regression test for the teen cases in `tests/test_utils.py`, without touching the existing test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/inv-1/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_to_ordinal() -> None:\n    assert _utils.to_ordinal(
…[171 chars elided]…
inal(11) == \"11th\"\n    assert _utils.to_ordinal(12) == \"12th\"\n    assert _utils.to_ordinal(13) == \"13th\"\n    assert _utils.to_ordinal(21) == \"21st\"\n    assert _utils.to_ordinal(102) == \"102nd\"\n    assert _utils.to_ordinal(111) == \"111th\"\n    assert _utils.to_ordinal(112) == \"112th\"\n    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/inv-1/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git diff --stat", "description": "Run test suite and show diff stats"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.80s
 tenacity/_utils.py  |  2 ++
 tests/test_utils.py | 16 ++++++++++++++++
 2 files changed, 18 insertions(+)
[assistant] `find_ordinal` now gives "th" for 111, 112 and 113, and every other number keeps its suffix. The full test suite passes: 126 passed, 1 skipped.

The fix is one new branch in `tenacity/_utils.py`. The function recursed on `pos_num % 10`, which turned 111 into 1 and gave "st". The new branch checks `pos_num % 100` against 11, 12 and 13 before that recursion, so 111, 1011, 1111 and similar numbers get "th".

I also added a `test_to_ordinal` test to `tests/test_utils.py` covering the teen cases and some neighbouring numbers. I didn't modify any existing test. The changes are uncommitted in the worktree.
