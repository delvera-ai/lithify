# trajectory base-1

final message:
Fixed: `find_ordinal` now returns "th" for 111, 112 and 113, and the other suffixes are unchanged. The project's test command passes (126 passed, 1 skipped).

**Cause:** the `else` branch reduced any number above 20 to its last digit, so 111 became 1 and got "st". 

**Change:** in `tenacity/_utils.py` I added a branch before the `else` that returns "th" when the last two digits are 11–13. This also covers 1011, 1012 and similar.

**Test:** I added `test_find_ordinal` to `tests/test_utils.py`, which covers the small cases, the 11–13 cases, and the 111–113 cases from the report. The change is uncommitted in the worktree.

## events
[tool_use Bash] {"command": "cat tenacity/_utils.py && grep -rn \"find_ordinal\" --include=*.py . | head -30", "description": "Read find_ordinal and its usages"}
[tool_result] # Copyright 2016 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[2253 chars elided]…
s.partial) and call.func
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
(eval):1: no matches found: --include=*.py
[assistant] The bug is in the `else` branch: `111 % 10 == 1` recurses to `find_ordinal(1)`, which returns "st". I'll add a branch that catches the 11–13 endings before that recursion, then run the project's test command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "grep -rn \"ordinal\" tests/ | head; <work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import find_ordinal\nfor n in [0,1,2,3,4,11,12,13,21,22,23,101,111,112,113,114,121,122,1011,1012]: print(n, find_ordinal(n))\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check ordinal tests, spot-check outputs, run project tests"}
[tool_result] tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
0 th
1 st
2 nd
3 rd
4 th
11 th
12 th
13 th
21 st
22 nd
23 rd
101 st
111 th
112 th
113 th
114 th
121 st
122 nd
1011 th
1012 th
..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] The fix works and the suite passes. There is no existing unit test for `find_ordinal`, so I'll add a regression test to pin the behaviour.
[tool_use Bash] {"command": "ls tests/ && head -30 tests/test_utils.py 2>/dev/null; git status --short", "description": "Look at existing utils test file"}
[tool_result] __init__.py
__pycache__
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
import functools

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
    partial_async_class = functools.partial(AsyncClass().__call__)
    partial_sync_class = functools.partial(SyncClass().__call__)
    partial_lambda_fn = functools.partial(lambda_fn)

    assert _utils.is_coroutine_callable(async_func) is True
    assert _utils.is_coroutine_callable(sync_func) is False
 M tenacity/_utils.py
[tool_use Bash] {"command": "cat >> tests/test_utils.py <<'EOF'\n\n\ndef test_find_ordinal() -> None:\n    assert _utils.find_ordinal(0) == \"th\"\n    assert _utils.find_ordinal(1) == \"st\"\n    assert _utils.find_ordinal(2) == \"nd\"\n    assert _utils.find_ordinal(3) == \"rd\"\n    assert _utils.find_ordinal(4) == \"th\"\n    assert _utils.find_ordinal(11) == \"th\"\n    assert _utils.find_ordinal(12) == \"th
…[328 chars elided]…
n    assert _utils.find_ordinal(121) == \"st\"\n    assert _utils.find_ordinal(1011) == \"th\"\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Add find_ordinal regression test and rerun suite"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.77s
 tenacity/_utils.py  |  2 ++
 tests/test_utils.py | 19 +++++++++++++++++++
 2 files changed, 21 insertions(+)
[assistant] Fixed: `find_ordinal` now returns "th" for 111, 112 and 113, and the other suffixes are unchanged. The project's test command passes (126 passed, 1 skipped).

**Cause:** the `else` branch reduced any number above 20 to its last digit, so 111 became 1 and got "st". 

**Change:** in `tenacity/_utils.py` I added a branch before the `else` that returns "th" when the last two digits are 11–13. This also covers 1011, 1012 and similar.

**Test:** I added `test_find_ordinal` to `tests/test_utils.py`, which covers the small cases, the 11–13 cases, and the 111–113 cases from the report. The change is uncommitted in the worktree.
