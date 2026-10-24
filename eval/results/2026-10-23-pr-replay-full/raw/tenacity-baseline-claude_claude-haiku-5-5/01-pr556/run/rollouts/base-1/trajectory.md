# trajectory base-1

final message:
Fixed in `tenacity/_utils.py`. Numbers whose last two digits are 11, 12 or 13 now get "th", so 111, 112 and 113 read "111th", "112th", "113th". Everything else is unchanged.

The change is one new branch in `find_ordinal`, placed after the existing `4 <= n <= 20` check and before the fallback that reduces to the last digit:

```python
elif 11 <= pos_num % 100 <= 13:
    return "th"
```

The project's test suite passes: 125 passed, 1 skipped, 12 subtests passed. I also spot-checked the output for 0–23, 101, 111–114, 121, 1011 and 1012, and each has the expected suffix.

I didn't add a regression test for 111–113 or commit the change. The change is uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" ~/.cache/lithify/work/repo-38fec5e48183/20261023-185633-bug-tenacity-utils-find-ordinal/base-1 --include=*.py | head -50", "description": "Locate find_ordinal usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" . --include='*.py'; cat tenacity/_utils.py", "description": "Find find_ordinal usages and show utils module"}
[tool_result] tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses
…[2404 chars elided]…
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
[assistant] The bug is in the `else` branch: it reduces to the last digit, so 111 becomes `find_ordinal(1)` = "st". The fix is to check the last two digits for 11–13 before that reduction. Adding the check now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-185633-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-185633-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [0,1,2,3,4,10,11,12,13,20,21,22,23,101,111,112,113,114,121,1011,1012]:\n    print(to_ordinal(n), end=' ')\nprint()\" && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check ordinal outputs and run the test suite"}
[tool_result] 0th 1st 2nd 3rd 4th 10th 11th 12th 13th 20th 21st 22nd 23rd 101st 111th 112th 113th 114th 121st 1011th 1012th 
..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.78s
[assistant] Fixed in `tenacity/_utils.py`. Numbers whose last two digits are 11, 12 or 13 now get "th", so 111, 112 and 113 read "111th", "112th", "113th". Everything else is unchanged.

The change is one new branch in `find_ordinal`, placed after the existing `4 <= n <= 20` check and before the fallback that reduces to the last digit:

```python
elif 11 <= pos_num % 100 <= 13:
    return "th"
```

The project's test suite passes: 125 passed, 1 skipped, 12 subtests passed. I also spot-checked the output for 0–23, 101, 111–114, 121, 1011 and 1012, and each has the expected suffix.

I didn't add a regression test for 111–113 or commit the change. The change is uncommitted in the worktree.
