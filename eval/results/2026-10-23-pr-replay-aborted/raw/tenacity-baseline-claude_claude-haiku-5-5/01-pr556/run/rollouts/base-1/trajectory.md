# trajectory base-1

final message:
Fixed: `find_ordinal` now gives "th" for 111, 112 and 113, and every other number keeps its suffix. The project's test command passes (126 passed, 1 skipped).

The cause was the fallback branch. For 111 it recursed on `111 % 10 = 1`, which returned "st". I added a check on the last two digits before that fallback:

```python
elif 11 <= pos_num % 100 <= 13:
    return "th"
```

This covers 111–113, 211–213, 1011–1013, and so on. Numbers 4–20 are still handled by the earlier branch, and 21, 22 and 23 still give "st", "nd" and "rd".

I also added `test_to_ordinal` to `tests/test_utils.py`. It covers the small cases, the teens, and 111–113 as regression cases. The change is in `tenacity/_utils.py` and `tests/test_utils.py`; nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include=*.py . | head; ", "description": "Locate find_ordinal definition and usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" . --exclude-dir=.git | head", "description": "Search repo for find_ordinal references"}
[tool_result] tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "offset": 35, "limit": 30}
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
[assistant] The bug is in the `else` branch: 111 falls through to `find_ordinal(111 % 10)`, which is `find_ordinal(1)`, giving "st". I'll add the teen check on the last two digits before that fallback.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b561bbaa0f70/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:\n        return find_ordinal(pos_num % 10)", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:\n        return find_ordinal(pos_num % 10)"}
[tool_result] The file ~/.cache/lithify/work/repo-b561bbaa0f70/20261023-154952-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[assistant] Now I'll check the fix against the cases in the report and run the project's test command.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [0,1,2,3,4,11,12,13,21,22,23,101,111,112,113,114,121,122,1011,1012,1013]: print(to_ordinal(n), end=' ')\n\" && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 15", "description": "Check ordinal outputs and run project test suite"}
[tool_result] 0th 1st 2nd 3rd 4th 11th 12th 13th 21st 22nd 23rd 101st 111th 112th 113th 114th 121st 122nd 1011th 1012th 1013th ..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.81s
[assistant] The fix works and the suite passes. I'll check whether there's an existing ordinal test to extend with a regression case.
[tool_use Bash] {"command": "grep -rn \"ordinal\" tests/ | head", "description": "Search tests for ordinal coverage"}
[tool_result] tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
[tool_use Bash] {"command": "ls tests/ && sed -n 1,20p tests/test_utils.py 2>/dev/null", "description": "List tests directory and check for utils test file"}
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
[tool_use Bash] {"command": "cat >> tests/test_utils.py <<'EOF'\n\n\ndef test_to_ordinal() -> None:\n    assert _utils.to_ordinal(1) == \"1st\"\n    assert _utils.to_ordinal(2) == \"2nd\"\n    assert _utils.to_ordinal(3) == \"3rd\"\n    assert _utils.to_ordinal(4) == \"4th\"\n    assert _utils.to_ordinal(11) == \"11th\"\n    assert _utils.to_ordinal(12) == \"12th\"\n    assert _utils.to_ordinal(13) == \"13th\"\n 
…[141 chars elided]…
    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\"\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 3; git status --short", "description": "Add ordinal regression test and rerun suite"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.78s
 M tenacity/_utils.py
 M tests/test_utils.py
[assistant] Fixed: `find_ordinal` now gives "th" for 111, 112 and 113, and every other number keeps its suffix. The project's test command passes (126 passed, 1 skipped).

The cause was the fallback branch. For 111 it recursed on `111 % 10 = 1`, which returned "st". I added a check on the last two digits before that fallback:

```python
elif 11 <= pos_num % 100 <= 13:
    return "th"
```

This covers 111–113, 211–213, 1011–1013, and so on. Numbers 4–20 are still handled by the earlier branch, and 21, 22 and 23 still give "st", "nd" and "rd".

I also added `test_to_ordinal` to `tests/test_utils.py`. It covers the small cases, the teens, and 111–113 as regression cases. The change is in `tenacity/_utils.py` and `tests/test_utils.py`; nothing is committed.
