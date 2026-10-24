# trajectory base-2

final message:
Fixed: numbers ending in 11, 12 or 13 now get "th" even above 20 (111 → "111th", 112 → "112th", 113 → "113th"). All other suffixes are unchanged. The full suite passes: 126 passed, 1 skipped.

The cause was the fallback branch in `find_ordinal` (`tenacity/_utils.py`). It recursed on `pos_num % 10` alone, so 111 reduced to 1 and got "st". The 11–13 exception now checks the last two digits:

```python
elif 4 <= pos_num <= 20 or 11 <= pos_num % 100 <= 13:
    return "th"
```

I also added a `test_to_ordinal` test in `tests/test_utils.py` covering the 0–4, 11–13, 21–23 and 111–113 cases, plus 121 and 1011. No existing test was changed. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include=*.py . && cat tenacity/_utils.py | head -80", "description": "Locate find_ordinal and read utils module"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" . --exclude-dir=.git; echo ---; cat tenacity/_utils.py", "description": "Search for find_ordinal and read utils module"}
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
[assistant] The bug is in the `else` branch: it recurses on `pos_num % 10` alone, so 111 reduces to 1 and gets "st". The 11–13 exception has to look at the last two digits. I'll make that change, then check the existing tests and the project's test command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-2/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"", "new_string": "    elif 4 <= pos_num <= 20 or 11 <= pos_num % 100 <= 13:\n        return \"th\""}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-2/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "grep -rln \"ordinal\" tests/ ; ls <work>/env-tenacity/bin/python && <work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [0,1,2,3,4,11,12,13,21,22,23,24,101,111,112,113,114,121,1011,1012]:\n    print(to_ordinal(n), end=' ')\n\"", "description": "Check ordinal tests and verify outputs for sample numbers"}
[tool_result] tests/test_after.py
<work>/env-tenacity/bin/python
0th 1st 2nd 3rd 4th 11th 12th 13th 21st 22nd 23rd 24th 101st 111th 112th 113th 114th 121st 1011th 1012th
[assistant] The outputs are right for every sample, including 111–113 and 1011. Next I'll look at the existing ordinal test in `tests/test_after.py` and run the full suite.
[tool_use Bash] {"command": "grep -n -B3 -A12 \"ordinal\" tests/test_after.py; echo ---; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Show existing ordinal test and run full test suite"}
[tool_result] 46-            self.log_level,
47-            f"Finished call to '{fn_name}' "
48-            f"after {sec_format % retry_state.seconds_since_start}(s), "
49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
50-        )
51-
52-    def test_02_custom_sec_format(self):
53-        """Test log formatting with custom int format.."""
54-        log = unittest.mock.MagicMock(spec="logging.Logger.log")
55-        logger = unittest.mock.MagicMock(spec="logging
…[199 chars elided]…
er, delay_since_first_attempt
--
71-            self.log_level,
72-            f"Finished call to '{fn_name}' "
73-            f"after {sec_format % retry_state.seconds_since_start}(s), "
74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
75-        )
---
..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] The full suite passes (125 passed, 1 skipped), but nothing tests `find_ordinal` directly. I'll add a regression test for it.
[tool_use Bash] {"command": "ls tests/ && grep -n \"^import\\|^from\\|^class\\|^def \" tests/test_utils.py 2>/dev/null | head -30", "description": "List tests directory and inspect test_utils imports"}
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
6:def test_is_coroutine_callable() -> None:
[tool_use Bash] {"command": "cat tests/test_utils.py", "description": "Read the existing utils test file"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-2/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_to_ordinal() -> None:\n    assert _utils.to_ordinal
…[310 chars elided]…
al(13) == \"13th\"\n    assert _utils.to_ordinal(21) == \"21st\"\n    assert _utils.to_ordinal(22) == \"22nd\"\n    assert _utils.to_ordinal(23) == \"23rd\"\n    assert _utils.to_ordinal(111) == \"111th\"\n    assert _utils.to_ordinal(112) == \"112th\"\n    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\"\n    assert _utils.to_ordinal(1011) == \"1011th\""}
[tool_result] The file ~/.cache/lithify/work/repo-3690df7bc95f/20261023-154952-bug-tenacity-utils-find-ordinal/base-2/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short; git diff --stat", "description": "Run test suite and show changed files"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.76s
 M tenacity/_utils.py
 M tests/test_utils.py
 tenacity/_utils.py  |  2 +-
 tests/test_utils.py | 19 +++++++++++++++++++
 2 files changed, 20 insertions(+), 1 deletion(-)
[assistant] Fixed: numbers ending in 11, 12 or 13 now get "th" even above 20 (111 → "111th", 112 → "112th", 113 → "113th"). All other suffixes are unchanged. The full suite passes: 126 passed, 1 skipped.

The cause was the fallback branch in `find_ordinal` (`tenacity/_utils.py`). It recursed on `pos_num % 10` alone, so 111 reduced to 1 and got "st". The 11–13 exception now checks the last two digits:

```python
elif 4 <= pos_num <= 20 or 11 <= pos_num % 100 <= 13:
    return "th"
```

I also added a `test_to_ordinal` test in `tests/test_utils.py` covering the 0–4, 11–13, 21–23 and 111–113 cases, plus 121 and 1011. No existing test was changed. Nothing is committed.
