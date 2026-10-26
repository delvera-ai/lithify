# trajectory base-2

final message:
Fixed `find_ordinal` so 111, 112 and 113 get "th". The full project suite passes (126 passed, 1 skipped).

The cause was the recursive fallback: `find_ordinal(pos_num % 10)` throws away the tens digit, so 111 was treated as 1. I added a check in `tenacity/_utils.py` that returns "th" when `pos_num % 100` is 11, 12 or 13, before the last-digit fallback. Numbers 0–20 and every other suffix are unchanged.

I also added `test_find_ordinal` to `tests/test_utils.py` covering the boundary cases (11–13, 21–23, 101–103, 111–113, 1011, 121). No existing tests were modified.

The changes are uncommitted in the worktree. I didn't add a release note, since the repo uses `releasenotes/notes/` and you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -n \"find_ordinal\" -r src tests 2>/dev/null; grep -n \"\" src/tenacity/_utils.py | sed -n '1,80p' | grep -n -A20 \"def find_ordinal\"", "description": "Locate find_ordinal and its tests"}
[tool_result] ugrep: warning: src/tenacity/_utils.py: No such file or directory
[tool_use Bash] {"command": "git ls-files | grep -i -E \"utils|test\" | head -50; echo ---; git grep -n \"find_ordinal\"", "description": "List utils and test files, grep find_ordinal"}
[tool_result] releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
tenacity/_utils.py
tests/__init__.py
tests/test_after.py
tests/test_asyncio.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_tornado.py
tests/test_utils.py
---
tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-2/tenacity/_utils.py", "offset": 35, "limit": 30}
[tool_result] 35	    def log(
36	        self, level: int, msg: str, /, *args: typing.Any, **kwargs: typing.Any
37	    ) -> typing.Any: ...
38	
39	
40	def find_ordinal(pos_num: int) -> str:
41	    # See: https://en.wikipedia.org/wiki/English_numerals#Ordinal_numbers
42	    if pos_num == 0:
43	        return "th"
44	    elif pos_num == 1:
45	        return "st"
46	    elif pos_num == 2:
47	        return "nd"
48	    elif pos_num == 3:
49	        return "rd"
50	    elif 4 <= pos_num <= 20:
51	        return "th"
52	    else:
53	        return find_ordinal(pos_num % 10)
54	
55	
56	def to_ordinal(pos_num: int) -> str:
57	    return f"{pos_num}{find_ordinal(pos_num)}"
58	
59	
60	def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
61	    """Get a callback fully-qualified name.
62	
63	    If no name can be produced ``repr(cb)`` is called and returned.
64	    """
[tool_use Bash] {"command": "cat tests/test_utils.py", "description": "Show existing utils tests"}
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
[assistant] The bug is in the recursive fallback: `find_ordinal(pos_num % 10)` discards the tens digit, so 111 is treated as 1. The fix is to check the last two digits for 11–13 before falling back to the last digit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-2/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif pos_num % 100 in (11, 12, 13):\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-2/tenacity/_utils.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-2/tests/test_utils.py", "old_string": "def test_is_coroutine_callable() -> None:", "new_string": "def test_find_ordinal() -> None:\n    assert _utils.find_ordinal(0) == \"th\"\n    assert _utils.find_ordinal(1) == \"st\"\n    assert _utils.find_ordinal(2) =
…[355 chars elided]…
rdinal(101) == \"st\"\n    assert _utils.find_ordinal(102) == \"nd\"\n    assert _utils.find_ordinal(103) == \"rd\"\n    assert _utils.find_ordinal(111) == \"th\"\n    assert _utils.find_ordinal(112) == \"th\"\n    assert _utils.find_ordinal(113) == \"th\"\n    assert _utils.find_ordinal(1011) == \"th\"\n    assert _utils.find_ordinal(121) == \"st\"\n\n\ndef test_is_coroutine_callable() -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-155945-bug-tenacity-utils-find-ordinal/base-2/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no", "description": "Run project test suite"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] Fixed `find_ordinal` so 111, 112 and 113 get "th". The full project suite passes (126 passed, 1 skipped).

The cause was the recursive fallback: `find_ordinal(pos_num % 10)` throws away the tens digit, so 111 was treated as 1. I added a check in `tenacity/_utils.py` that returns "th" when `pos_num % 100` is 11, 12 or 13, before the last-digit fallback. Numbers 0–20 and every other suffix are unchanged.

I also added `test_find_ordinal` to `tests/test_utils.py` covering the boundary cases (11–13, 21–23, 101–103, 111–113, 1011, 121). No existing tests were modified.

The changes are uncommitted in the worktree. I didn't add a release note, since the repo uses `releasenotes/notes/` and you didn't ask for one.
