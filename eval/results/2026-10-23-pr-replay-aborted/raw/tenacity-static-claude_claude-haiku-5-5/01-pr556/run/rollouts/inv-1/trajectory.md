# trajectory inv-1

final message:
`find_ordinal` now gives "th" for 111, 112 and 113, and the rest of the suffixes are unchanged. The project's test run passes: 126 passed, 1 skipped.

The cause was the recursion for numbers above 20. It reduced the number to its last digit and then applied the 11–13 exception to that digit, so 111 was treated as 1.

The fix is in `tenacity/_utils.py`: the "th" branch now also matches when `pos_num % 100` is 11, 12 or 13, so the check looks at the last two digits. I also added a `test_find_ordinal` test in `tests/test_utils.py` covering 0–4, 11–13, 21–23, 111–113 and 121. I did not change any existing tests.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n -A25 \"def find_ordinal\" tenacity/_utils.py; grep -rn \"find_ordinal\" --include='*.py' tests tenacity | head", "description": "Show find_ordinal implementation and usages"}
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
53-        return find_ordinal(pos_num % 10)
54-
55-
56-def to_ordinal(pos_num: int) -> str:
57-    return f"{pos_num}{find_ordinal(pos_num)}"
58-
59-
60-def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
61-    """Get a callback fully-qualified name.
62-
63-    If no name can be produced ``repr(cb)`` is called and returned.
64-    """
65-    segments = []
tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
[tool_use Bash] {"command": "grep -rn \"ordinal\" tests | head; ls tests | head -30", "description": "Find existing ordinal tests"}
[tool_result] tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[assistant] The bug is in the recursion: for anything above 20 it reduces to `pos_num % 10` and then ignores the teen rule, so 111 becomes 1 and gets "st". I'll make the teen check look at the last two digits instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/inv-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"", "new_string": "    elif 4 <= pos_num <= 20 or pos_num % 100 in (11, 12, 13):\n        return \"th\""}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/inv-1/tenacity/_utils.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/inv-1/tests/test_utils.py"}
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
[assistant] Next I'll add a regression test covering the suffixes, then run the project's test command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/inv-1/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_find_ordinal() -> None:\n    assert _utils.to_ordi
…[265 chars elided]…
inal(12) == \"12th\"\n    assert _utils.to_ordinal(13) == \"13th\"\n    assert _utils.to_ordinal(21) == \"21st\"\n    assert _utils.to_ordinal(22) == \"22nd\"\n    assert _utils.to_ordinal(23) == \"23rd\"\n    assert _utils.to_ordinal(111) == \"111th\"\n    assert _utils.to_ordinal(112) == \"112th\"\n    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/inv-1/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no", "description": "Run project test suite"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.84s
[assistant] `find_ordinal` now gives "th" for 111, 112 and 113, and the rest of the suffixes are unchanged. The project's test run passes: 126 passed, 1 skipped.

The cause was the recursion for numbers above 20. It reduced the number to its last digit and then applied the 11–13 exception to that digit, so 111 was treated as 1.

The fix is in `tenacity/_utils.py`: the "th" branch now also matches when `pos_num % 100` is 11, 12 or 13, so the check looks at the last two digits. I also added a `test_find_ordinal` test in `tests/test_utils.py` covering 0–4, 11–13, 21–23, 111–113 and 121. I did not change any existing tests.

Nothing is committed.
