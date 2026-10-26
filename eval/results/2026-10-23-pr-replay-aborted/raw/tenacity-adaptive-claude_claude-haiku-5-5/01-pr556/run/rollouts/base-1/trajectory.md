# trajectory base-1

final message:
Fixed. `find_ordinal` now returns "th" for 111, 112 and 113, and every other number keeps its existing suffix. The test suite passes (126 passed, 1 skipped).

The change is in `tenacity/_utils.py`. The function only looked at the last digit for numbers above 20, so 111 became "st" (from 1), 112 "nd" and 113 "rd". I added a branch that returns "th" when the last two digits are 11–13.

I also added `test_find_ordinal` to `tests/test_utils.py` to cover the teen cases, the 1st/2nd/3rd cases, and 111–113 and 1011. The repo had no existing ordinal tests. Nothing is committed yet.

## events
[tool_use Bash] {"command": "grep -n \"find_ordinal\" -A 12 tenacity/_utils.py; grep -rn \"find_ordinal\" tests/ | head", "description": "Locate find_ordinal implementation and tests"}
[tool_result] 40:def find_ordinal(pos_num: int) -> str:
41-    # See: https://en.wikipedia.org/wiki/English_numerals#Ordinal_numbers
42-    if pos_num == 0:
43-        return "th"
44-    elif pos_num == 1:
45-        return "st"
46-    elif pos_num == 2:
47-        return "nd"
48-    elif pos_num == 3:
49-        return "rd"
50-    elif 4 <= pos_num <= 20:
51-        return "th"
52-    else:
53:        return find_ordinal(pos_num % 10)
54-
55-
56-def to_ordinal(pos_num: int) -> str:
57:    return f"{pos_num}{find_ordinal(pos_num)}"
58-
59-
60-def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
61-    """Get a callback fully-qualified name.
62-
63-    If no name can be produced ``repr(cb)`` is called and returned.
64-    """
65-    segments = []
66-    try:
67-        segments.append(cb.__qualname__)
68-    except AttributeError:
69-        try:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import find_ordinal, to_ordinal\nfor n in [0,1,2,3,4,10,11,12,13,14,20,21,22,23,101,102,103,111,112,113,114,121,122,123,1011,1012,1013]:\n    print(to_ordinal(n), end=' ')\n\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Check ordinal outputs and run test suite"}
[tool_result] 0th 1st 2nd 3rd 4th 10th 11th 12th 13th 14th 20th 21st 22nd 23rd 101st 102nd 103rd 111th 112th 113th 114th 121st 122nd 123rd 1011th 1012th 1013th ..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.79s
[tool_use Bash] {"command": "ls tests; grep -n \"^import\\|^from\" tests/test_utils.py 2>/dev/null; git status --short", "description": "Check existing utils tests and git status"}
[tool_result] __init__.py
__pycache__
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
1:import functools
3:from tenacity import _utils
 M tenacity/_utils.py
[tool_use Bash] {"command": "cat tests/test_utils.py", "description": "Read existing utils test file"}
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
[assistant] Adding a regression test alongside the existing utils tests, then re-running the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_find_ordinal() -> None:\n    assert _utils.find_ord
…[311 chars elided]…
nd_ordinal(13) == \"th\"\n    assert _utils.find_ordinal(21) == \"st\"\n    assert _utils.find_ordinal(22) == \"nd\"\n    assert _utils.find_ordinal(23) == \"rd\"\n    assert _utils.find_ordinal(111) == \"th\"\n    assert _utils.find_ordinal(112) == \"th\"\n    assert _utils.find_ordinal(113) == \"th\"\n    assert _utils.find_ordinal(121) == \"st\"\n    assert _utils.find_ordinal(1011) == \"th\""}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Run test suite and show diff stat"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.80s
 tenacity/_utils.py  |  2 ++
 tests/test_utils.py | 19 +++++++++++++++++++
 2 files changed, 21 insertions(+)
[assistant] Fixed. `find_ordinal` now returns "th" for 111, 112 and 113, and every other number keeps its existing suffix. The test suite passes (126 passed, 1 skipped).

The change is in `tenacity/_utils.py`. The function only looked at the last digit for numbers above 20, so 111 became "st" (from 1), 112 "nd" and 113 "rd". I added a branch that returns "th" when the last two digits are 11–13.

I also added `test_find_ordinal` to `tests/test_utils.py` to cover the teen cases, the 1st/2nd/3rd cases, and 111–113 and 1011. The repo had no existing ordinal tests. Nothing is committed yet.
