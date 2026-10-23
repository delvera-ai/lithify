# trajectory inv-1

final message:
`humanize.naturalsize(1.0)` and `naturalsize("1")` now both return `"1 Byte"` again when `gnu` is False. The full suite passes: 607 passed, 24 skipped.

**Cause:** commit `fb61d5a` changed `"%d Byte" % bytes_` to `f"{bytes_} Byte"`, so a float `1.0` printed as `1.0 Byte`. The `< base` branch got the matching `int()` fix in `11e62ee`, but the one-byte branch was missed.

**Change:**
- `src/humanize/filesize.py`: the one-byte branch now returns `f"{int(bytes_)} Byte"`, matching the 4.12 output.
- `tests/test_filesize.py`: added the positive cases `([1.0], "1 Byte")` and `(["1"], "1 Byte")`. The existing negation retest covers the negative side.

I left the changes uncommitted in the worktree.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"gnu\\|def naturalsize\" -A0 src/humanize/filesize.py | head -50", "description": "Check worktree status and locate naturalsize"}
[tool_result] 30:    "gnu": "KMGTPEZYRQ",
34:def naturalsize(
37:    gnu: bool = False,
71:        gnu (bool): If `True`, the binary argument is ignored and GNU-style
78:    if gnu:
79:        suffix = suffixes["gnu"]
85:    base = 1024 if (gnu or binary) else 1000
93:    if abs_bytes == 1 and not gnu:
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/inv-1/src/humanize/filesize.py"}
[tool_result] 1	"""Bits and bytes related humanization."""
2	
3	from __future__ import annotations
4	
5	suffixes = {
6	    "decimal": (
7	        " kB",
8	        " MB",
9	        " GB",
10	        " TB",
11	        " PB",
12	        " EB",
13	        " ZB",
14	        " YB",
15	        " RB",
16	        " QB",
17	    ),
18	    "binary": (
19	        " KiB",
20	        " MiB",
21	        " GiB",
22	        " TiB",
23	        " PiB",
24	        " EiB",
25	        " ZiB",
26	        " YiB",
27	        " RiB",
2
…[1744 chars elided]…

87	        bytes_ = float(value)
88	    else:
89	        bytes_ = value
90	
91	    abs_bytes = abs(bytes_)
92	
93	    if abs_bytes == 1 and not gnu:
94	        return f"{bytes_} Byte"
95	
96	    if abs_bytes < base:
97	        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
98	
99	    for i, s in enumerate(suffix, 2):
100	        unit = base**i
101	        if abs_bytes < unit:
102	            break
103	
104	    ret: str = format % (base * (bytes_ / unit)) + s
105	    return ret
106	
[tool_use Bash] {"command": "git log --oneline -5 -- src/humanize/filesize.py && git log -p -3 --format='--- %h %s' -- src/humanize/filesize.py | head -150; sed -n 1,200p tests/test_filesize.py | grep -n \"1\\b\\|Byte\" | head -60", "description": "Read filesize module, history, and related tests"}
[tool_result] 11e62ee Fix regression in naturalsize for float
fb61d5a Update pre-commit (#226)
a178851 Fix overflow issue in naturalsize with np.int32 input
33119c0 Fix rollover from ZB to 1.0 YB
0e2cab4 Merge branch 'main' into ronna
--- 11e62ee Fix regression in naturalsize for float

diff --git a/src/humanize/filesize.py b/src/humanize/filesize.py
index bdadd55..5650d02 100644
--- a/src/humanize/filesize.py
+++ b/src/humanize/filesize.py
@@ -94,7 +94,7 @@ def naturalsize(
         return f"{bytes_} Byte"
 
…[2341 chars elided]…
   ([1000**9 * 39, False, True], "31.5R"),
66:        ([1000**10 * 40, False, True], "31.6Q"),
70:        ([1024, False, True], "1.0K"),
71:        ([1, False, False], "1 Byte"),
76:        ([1.123456789], "1 Bytes"),
77:        ([1.123456789 * 10**3], "1.1 kB"),
78:        ([1.123456789 * 10**6], "1.1 MB"),
79:        ([1.123456789, False, True], "1B"),
80:        ([1.123456789 * 10**3, False, True], "1.1K"),
81:        ([1.123456789 * 10**6, False, True], "1.1M"),
89:        test_args[0] *= -1
[tool_use Bash] {"command": "sed -n 1,12p tests/test_filesize.py && sed -n 66,110p tests/test_filesize.py; ls <work>/env-humanize/bin/python 2>&1", "description": "View test file structure and check project venv exists"}
[tool_result] #!/usr/bin/env python

"""Tests for filesize humanizing."""
from __future__ import annotations

import pytest

import humanize


@pytest.mark.parametrize(
    "test_args, expected",
        ([1000**10 * 40, False, True], "31.6Q"),
        ([300, False, True], "300B"),
        ([3000, False, True], "2.9K"),
        ([3000000, False, True], "2.9M"),
        ([1024, False, True], "1.0K"),
        ([1, False, False], "1 Byte"),
        ([3141592, False, False, "%.2f"], "3.14 MB"),
        ([3000, Fa
…[434 chars elided]…
aturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    # Retest with negative input
    if isinstance(test_args[0], int):
        test_args[0] *= -1
    else:
        test_args[0] = f"-{test_args[0]}"

    assert humanize.naturalsize(*test_args) == "-" + expected
<work>/env-humanize/bin/python
[assistant] Root cause: commit fb61d5a changed `"%d Byte" % bytes_` to `f"{bytes_} Byte"`, so a float `1.0` now prints as `1.0 Byte`. The `< base` branch was already fixed to use `int()` in 11e62ee, but the `== 1` branch was missed. I'll reproduce it first, then fix it.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -I -c 'import humanize; print(repr(humanize.naturalsize(1.0)), repr(humanize.naturalsize(\"1\")))'", "description": "Reproduce the float and string 1-byte output"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'humanize'
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c 'import humanize; print(repr(humanize.naturalsize(1.0)), repr(humanize.naturalsize(\"1\")))'", "description": "Reproduce the float and string 1-byte output"}
[tool_result] '1.0 Byte' '1.0 Byte'
[assistant] Reproduced. Now the fix, which matches the `%d` behaviour from 4.12 and the `int()` already used in the `< base` branch:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/inv-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/inv-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/inv-1/tests/test_filesize.py", "old_string": "        ([1, False, False], \"1 Byte\"),\n", "new_string": "        ([1, False, False], \"1 Byte\"),\n        ([1.0], \"1 Byte\"),\n        ([\"1\"], \"1 Byte\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/inv-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c 'import humanize; print(repr(humanize.naturalsize(1.0)), repr(humanize.naturalsize(\"1\")), repr(humanize.naturalsize(1.0, gnu=True)), repr(humanize.naturalsize(0.5)))'", "description": "Run project test suite and recheck outputs"}
[tool_result] ......................................................................ss [ 11%]
sssssssssssssssssssss......s............................................ [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 57%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 91%]
.......................................................                  [100%]
607 passed, 24 skipped in 0.49s
'1 Byte' '1 Byte' '1B' '0 Bytes'
[assistant] `humanize.naturalsize(1.0)` and `naturalsize("1")` now both return `"1 Byte"` again when `gnu` is False. The full suite passes: 607 passed, 24 skipped.

**Cause:** commit `fb61d5a` changed `"%d Byte" % bytes_` to `f"{bytes_} Byte"`, so a float `1.0` printed as `1.0 Byte`. The `< base` branch got the matching `int()` fix in `11e62ee`, but the one-byte branch was missed.

**Change:**
- `src/humanize/filesize.py`: the one-byte branch now returns `f"{int(bytes_)} Byte"`, matching the 4.12 output.
- `tests/test_filesize.py`: added the positive cases `([1.0], "1 Byte")` and `(["1"], "1 Byte")`. The existing negation retest covers the negative side.

I left the changes uncommitted in the worktree.
