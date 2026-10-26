# trajectory base-1

final message:
Fixed: 111, 112 and 113 now get "th" (so "111th", "112th", "113th"), and other numbers keep their suffixes.

The cause was the fallback branch in `find_ordinal` (`tenacity/_utils.py`). For numbers above 20 it recursed on `pos_num % 10`, which discards the tens digit, so 111 was treated as 1. I added a check before the recursion: if the last two digits are 11–13, return "th". So 1011 and 1111 also get "th", while 101, 121 and 1001 keep "st".

The project's test command passes (125 passed, 1 skipped). I also checked sample outputs directly: 1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101, 102, 103, 111, 112, 113, 114, 121 and 1011 all produce the expected suffixes. I didn't add a regression test for the 111–113 case; say if you want one. I haven't committed the change.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include=*.py . ; cat tenacity/_utils.py", "description": "Locate find_ordinal and read utils module"}
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
[assistant] The bug is in the `else` branch: `find_ordinal(pos_num % 10)` strips the tens digit, so 111 is treated as 1. I'll add a check on the last two digits before recursing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "python3 -I -c \"\nfrom tenacity._utils import to_ordinal\nfor n in [1,2,3,4,11,12,13,21,22,23,101,102,103,111,112,113,114,121,1011,1012,1013,1111,1112,1113,1121]:\n    print(to_ordinal(n), end=' ')\n\"; echo; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check ordinal outputs and run project test suite"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'tenacity'

..........s................................................. [ 47%]
..................................................................       [100%]
125 passed, 1 skipped, 12 subtests passed in 1.80s
[assistant] The test suite passes. My quick check failed only because `python3 -I` ignores the working directory, so I'll rerun it with the project's interpreter.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -c \"\nfrom tenacity._utils import to_ordinal\nprint(' '.join(to_ordinal(n) for n in [1,2,3,4,11,12,13,21,22,23,101,102,103,111,112,113,114,121,1011,1012,1013,1111]))\n\"; git status --short", "description": "Print sample ordinals and show changed files"}
[tool_result] 1st 2nd 3rd 4th 11th 12th 13th 21st 22nd 23rd 101st 102nd 103rd 111th 112th 113th 114th 121st 1011th 1012th 1013th 1111th
 M tenacity/_utils.py
[assistant] Fixed: 111, 112 and 113 now get "th" (so "111th", "112th", "113th"), and other numbers keep their suffixes.

The cause was the fallback branch in `find_ordinal` (`tenacity/_utils.py`). For numbers above 20 it recursed on `pos_num % 10`, which discards the tens digit, so 111 was treated as 1. I added a check before the recursion: if the last two digits are 11–13, return "th". So 1011 and 1111 also get "th", while 101, 121 and 1001 keep "st".

The project's test command passes (125 passed, 1 skipped). I also checked sample outputs directly: 1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101, 102, 103, 111, 112, 113, 114, 121 and 1011 all produce the expected suffixes. I didn't add a regression test for the 111–113 case; say if you want one. I haven't committed the change.
