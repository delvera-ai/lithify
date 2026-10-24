# trajectory base-1

final message:
`find_ordinal` now returns "th" for 111, 112 and 113, so messages read "111th", "112th" and "113th". The full suite passes (126 passed, 1 skipped).

The cause was the fallback branch: for any number over 20 it recursed on the last digit, so 111 became 1 and got "st". The fix is one added branch in `tenacity/_utils.py` that returns "th" when the last two digits are 11, 12 or 13, placed before that fallback. Every other number keeps its existing suffix. I spot-checked 1–4, 11–13, 21–23, 31, 101–104, 110–114, 121–122, 1000 and 1011–1013, and they all come out as expected.

I also added `test_to_ordinal` to `tests/test_utils.py`, covering the 111/112/113 cases alongside the existing ones. No existing tests were changed.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include=*.py . && cat tenacity/_utils.py", "description": "Locate find_ordinal and read utils module"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" . --exclude-dir=.git; echo ---; cat tenacity/_utils.py", "description": "Locate find_ordinal and read utils module"}
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
[assistant] The bug is clear: for 111, the `else` branch recurses on `111 % 10 == 1`, which returns "st". The fix is to check the last two digits for 11–13 before recursing. I'll check for existing tests first.
[tool_use Bash] {"command": "ls tests; grep -rn \"ordinal\\|_utils\" tests | head -20", "description": "List tests and search for ordinal test coverage"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
tests/test_utils.py:3:from tenacity import _utils
tests/test_utils.py:29:    assert _utils.is_coroutine_callable(async_func) is True
tests/test_utils.py:30:    assert _utils.is_coroutine_callable(sync_func) is False
tests/test_utils.py:31:    assert _utils.is_coroutine_callable(AsyncClass) is False
tests/test_utils.py:32:    assert _utils.is_coroutine_callable(AsyncClass()) is True
tests/te
…[653 chars elided]…
coroutine_callable(partial_lambda_fn) is False
tests/test_after.py:6:from tenacity import _utils  # noqa
tests/test_after.py:43:            else _utils.get_callback_name(retry_state.fn)
tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:68:            else _utils.get_callback_name(retry_state.fn)
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
[assistant] Now the fix: check the last two digits for 11–13 before falling through to the single-digit recursion.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [1,2,3,4,11,12,13,21,22,23,31,101,102,103,104,110,111,112,113,114,121,122,1000,1011,1012,1013]:\n    print(to_ordinal(n), end=' ')\nprint()\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Spot-check ordinals and run the project test suite"}
[tool_result] 1st 2nd 3rd 4th 11th 12th 13th 21st 22nd 23rd 31st 101st 102nd 103rd 104th 110th 111th 112th 113th 114th 121st 122nd 1000th 1011th 1012th 1013th 
..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.92s
[assistant] The spot checks are right and the suite passes. I'll add a regression test for the reported case, so I'm reading the end of the test file first.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tests/test_utils.py"}
[tool_result] 1	import functools
2	
3	from tenacity import _utils
4	
5	
6	def test_is_coroutine_callable() -> None:
7	    async def async_func() -> None:
8	        pass
9	
10	    def sync_func() -> None:
11	        pass
12	
13	    class AsyncClass:
14	        async def __call__(self) -> None:
15	            pass
16	
17	    class SyncClass:
18	        def __call__(self) -> None:
19	            pass
20	
21	    lambda_fn = lambda: None  # noqa: E731
22	
23	    partial_async_func = functools.partial(async_func)
2
…[563 chars elided]…
s False
34	    assert _utils.is_coroutine_callable(SyncClass()) is False
35	    assert _utils.is_coroutine_callable(lambda_fn) is False
36	
37	    assert _utils.is_coroutine_callable(partial_async_func) is True
38	    assert _utils.is_coroutine_callable(partial_sync_func) is False
39	    assert _utils.is_coroutine_callable(partial_async_class) is True
40	    assert _utils.is_coroutine_callable(partial_sync_class) is False
41	    assert _utils.is_coroutine_callable(partial_lambda_fn) is False
42	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_to_ordinal() -> None:\n    assert _utils.to_ordin
…[84 chars elided]…
rdinal(3) == \"3rd\"\n    assert _utils.to_ordinal(11) == \"11th\"\n    assert _utils.to_ordinal(12) == \"12th\"\n    assert _utils.to_ordinal(13) == \"13th\"\n    assert _utils.to_ordinal(21) == \"21st\"\n    assert _utils.to_ordinal(111) == \"111th\"\n    assert _utils.to_ordinal(112) == \"112th\"\n    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short", "description": "Run test suite again and show changed files"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.78s
 M tenacity/_utils.py
 M tests/test_utils.py
[assistant] `find_ordinal` now returns "th" for 111, 112 and 113, so messages read "111th", "112th" and "113th". The full suite passes (126 passed, 1 skipped).

The cause was the fallback branch: for any number over 20 it recursed on the last digit, so 111 became 1 and got "st". The fix is one added branch in `tenacity/_utils.py` that returns "th" when the last two digits are 11, 12 or 13, placed before that fallback. Every other number keeps its existing suffix. I spot-checked 1–4, 11–13, 21–23, 31, 101–104, 110–114, 121–122, 1000 and 1011–1013, and they all come out as expected.

I also added `test_to_ordinal` to `tests/test_utils.py`, covering the 111/112/113 cases alongside the existing ones. No existing tests were changed.

The changes are uncommitted in the worktree.
