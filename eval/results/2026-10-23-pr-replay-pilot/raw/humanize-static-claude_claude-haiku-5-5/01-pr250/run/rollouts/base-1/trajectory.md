# trajectory base-1

final message:
`naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again when `gnu` is False. The full suite passes: 609 passed, 24 skipped.

The cause was one line in `src/humanize/filesize.py`. The 1-byte branch formatted the raw value (`f"{bytes_} Byte"`), so floats printed as `1.0`. In 4.11 this branch used `%d`. Commit 11e62ee had already switched the "less than one kilobyte" branch to `int(bytes_)` but missed this one. I changed it to `f"{int(bytes_)} Byte"`, which matches that existing branch.

In `tests/test_filesize.py` I added cases for `1.0`, `"1"` and `"1.0"` (expecting `"1 Byte"`), plus `1.0` with `gnu=True` (expecting `"1B"`). The existing test helper already checks the negative versions of each case. No existing tests were changed.

Two things I didn't check: the `gnu=True` path was already correct, and I didn't run any other test suites or linters beyond the project's pytest command.

## events
[tool_use Bash] {"command": "rtk grep -n \"def naturalsize\" -A80 src/humanize/filesize.py && git log --oneline -3 -- src/humanize/filesize.py", "description": "Locate naturalsize implementation"}
[tool_result ERROR] Exit code 127
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"def naturalsize\" -A90 src/humanize/filesize.py; git log --oneline -3 -- src/humanize/filesize.py", "description": "Show naturalsize implementation and history"}
[tool_result] 34:def naturalsize(
35-    value: float | str,
36-    binary: bool = False,
37-    gnu: bool = False,
38-    format: str = "%.1f",
39-) -> str:
40-    """Format a number of bytes like a human-readable filesize (e.g. 10 kB).
41-
42-    By default, decimal suffixes (kB, MB) are used.
43-
44-    Non-GNU modes are compatible with jinja2's `filesizeformat` filter.
45-
46-    Examples:
47-        ```pycon
48-        >>> naturalsize(3000000)
49-        '3.0 MB'
50-        >>> naturalsize(300, False, Tr
…[1313 chars elided]…
nd not gnu:
94-        return f"{bytes_} Byte"
95-
96-    if abs_bytes < base:
97-        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
98-
99-    for i, s in enumerate(suffix, 2):
100-        unit = base**i
101-        if abs_bytes < unit:
102-            break
103-
104-    ret: str = format % (base * (bytes_ / unit)) + s
105-    return ret
11e62ee Fix regression in naturalsize for float
fb61d5a Update pre-commit (#226)
a178851 Fix overflow issue in naturalsize with np.int32 input
[tool_use Bash] {"command": "git show 11e62ee --stat && git show 11e62ee -- src/humanize/filesize.py && git tag --list | tail -5; grep -n \"Byte\" tests/*.py | head -30", "description": "Inspect regression commit and related tests"}
[tool_result] commit 11e62eeedb8990298c3612af82376dc2344d24f8
Author: Hugo van Kemenade <1324225+hugovk@users.noreply.github.com>
Date:   Mon Feb 17 23:29:34 2025 +0200

    Fix regression in naturalsize for float

 src/humanize/filesize.py | 2 +-
 tests/test_filesize.py   | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
commit 11e62eeedb8990298c3612af82376dc2344d24f8
Author: Hugo van Kemenade <1324225+hugovk@users.noreply.github.com>
Date:   Mon Feb 17 23:29:34 2025 +0200

    Fix regression in na
…[241 chars elided]…
yte"
 
     if abs_bytes < base:
-        return f"{bytes_}B" if gnu else f"{bytes_} Bytes"
+        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
 
     for i, s in enumerate(suffix, 2):
         unit = base**i
4.5.0
4.6.0
4.7.0
4.8.0
4.9.0
tests/test_filesize.py:14:        ([300], "300 Bytes"),
tests/test_filesize.py:36:        ([300, True], "300 Bytes"),
tests/test_filesize.py:71:        ([1, False, False], "1 Byte"),
tests/test_filesize.py:76:        ([1.123456789], "1 Bytes"),
[tool_use Bash] {"command": "git tag --list '4.1*'; for t in 4.11.0 4.12.0; do echo \"== $t\"; git show $t:src/humanize/filesize.py 2>/dev/null | grep -n \"Byte\\|int(bytes_)\\|abs_bytes ==\" ; done; sed -n 60,80p tests/test_filesize.py", "description": "Compare Byte handling in older releases and tests"}
[tool_result] 4.1.0
4.10.0
4.11.0
4.12.0
4.12.1
4.12.2
4.12.3
4.13.0
4.14.0
4.15.0
4.16.0
== 4.11.0
(eval):1: bad substitution
== 4.12.0
(eval):1: bad substitution
        ([1000**4 * 34, False, True], "30.9T"),
        ([1000**5 * 35, False, True], "31.1P"),
        ([1000**6 * 36, False, True], "31.2E"),
        ([1000**7 * 37, False, True], "31.3Z"),
        ([1000**8 * 38, False, True], "31.4Y"),
        ([1000**9 * 39, False, True], "31.5R"),
        ([1000**10 * 40, False, True], "31.6Q"),
        ([300
…[116 chars elided]…
1024, False, True], "1.0K"),
        ([1, False, False], "1 Byte"),
        ([3141592, False, False, "%.2f"], "3.14 MB"),
        ([3000, False, True, "%.3f"], "2.930K"),
        ([3000000000, False, True, "%.0f"], "3G"),
        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
        ([1.123456789], "1 Bytes"),
        ([1.123456789 * 10**3], "1.1 kB"),
        ([1.123456789 * 10**6], "1.1 MB"),
        ([1.123456789, False, True], "1B"),
        ([1.123456789 * 10**3, False, True], "1.1K"),
[tool_use Bash] {"command": "for t in 4.11.0 4.12.0; do echo \"== $t\"; git show \"$t:src/humanize/filesize.py\" | grep -n 'Byte\\|int(bytes_)\\|abs_bytes ==' ; done", "description": "Check Byte handling in 4.11 and 4.12 releases"}
[tool_result ERROR] Exit code 1
== 4.11.0
(eval):1: bad substitution
== 4.12.0
(eval):1: bad substitution
[tool_use Bash] {"command": "bash -c 'for t in 4.11.0 4.12.0; do echo \"== $t\"; git show \"$t:src/humanize/filesize.py\" | grep -n -e \"Byte\" -e \"abs_bytes ==\" ; done'", "description": "Check Byte handling in 4.11 and 4.12 releases"}
[tool_result] == 4.11.0
93:    if abs_bytes == 1 and not gnu:
94:        return "%d Byte" % bytes_
97:        return ("%dB" if gnu else "%d Bytes") % bytes_
== 4.12.0
93:    if abs_bytes == 1 and not gnu:
94:        return f"{bytes_} Byte"
97:        return f"{bytes_}B" if gnu else f"{bytes_} Bytes"
[assistant] The cause is line 94: `f"{bytes_} Byte"` formats the float directly, while 4.11 used `%d`. Commit 11e62ee already switched the sub-kilobyte branch on line 97 to `int(bytes_)`, but missed this one. I'll apply the same fix and add test cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py", "offset": 1, "limit": 30}
[tool_result] 1	#!/usr/bin/env python
2	
3	"""Tests for filesize humanizing."""
4	from __future__ import annotations
5	
6	import pytest
7	
8	import humanize
9	
10	
11	@pytest.mark.parametrize(
12	    "test_args, expected",
13	    [
14	        ([300], "300 Bytes"),
15	        (["1000"], "1.0 kB"),
16	        ([10**3], "1.0 kB"),
17	        ([10**6], "1.0 MB"),
18	        ([10**9], "1.0 GB"),
19	        ([10**12], "1.0 TB"),
20	        ([10**15], "1.0 PB"),
21	        ([10**18], "1.0 EB"),
22	        ([10**21], "1.0 ZB"),
23	        ([10**24], "1.0 YB"),
24	        ([10**27], "1.0 RB"),
25	        ([10**30], "1.0 QB"),
26	        ([1000**1 * 31], "31.0 kB"),
27	        ([1000**2 * 32], "32.0 MB"),
28	        ([1000**3 * 33], "33.0 GB"),
29	        ([1000**4 * 34], "34.0 TB"),
30	        ([1000**5 * 35], "35.0 PB"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py", "old_string": "        ([1, False, False], \"1 Byte\"),\n", "new_string": "        ([1, False, False], \"1 Byte\"),\n        ([1.0], \"1 Byte\"),\n        ([\"1\"], \"1 Byte\"),\n        ([\"1.0\"], \"1 Byte\"),\n        ([-1.0], \"-1 Byte\"),\n        ([1.0, False, True], \"1B\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite with project interpreter"}
[tool_result]         elif binary:
            suffix = suffixes["binary"]
        else:
            suffix = suffixes["decimal"]
    
        base = 1024 if (gnu or binary) else 1000
        if isinstance(value, str):
>           bytes_ = float(value)
                     ^^^^^^^^^^^^
E           ValueError: could not convert string to float: '--1.0'

src/humanize/filesize.py:87: ValueError
=========================== short test summary info ============================
FAILED tests/test_filesize.py::test_naturalsize[test_args61--1 Byte] - ValueE...
1 failed, 609 passed, 24 skipped in 0.53s
[tool_use Bash] {"command": "grep -n \"def test_naturalsize\" -B3 -A6 tests/test_filesize.py", "description": "Show naturalsize test function"}
[tool_result] 86-        ([1.123456789 * 10**6, False, True], "1.1M"),
87-    ],
88-)
89:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
90-    assert humanize.naturalsize(*test_args) == expected
91-
92-    # Retest with negative input
93-    if isinstance(test_args[0], int):
94-        test_args[0] *= -1
95-    else:
[tool_use Bash] {"command": "sed -n 92,105p tests/test_filesize.py", "description": "Show negative-retest logic in test"}
[tool_result]     # Retest with negative input
    if isinstance(test_args[0], int):
        test_args[0] *= -1
    else:
        test_args[0] = f"-{test_args[0]}"

    assert humanize.naturalsize(*test_args) == "-" + expected
[assistant] The test helper already checks negative inputs by prefixing a string with `-`, so a literal `-1.0` case double-negates. I'll drop that line; the helper covers the negative path for my new float and string cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py", "old_string": "        ([-1.0], \"-1 Byte\"),\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; PYTHONPATH=src <work>/env-humanize/bin/python -c \"import humanize; print(repr(humanize.naturalsize(1.0)), repr(humanize.naturalsize('1')), repr(humanize.naturalsize(1.0, gnu=True)))\"; git status --short", "description": "Rerun tests, spot-check outputs, show status"}
[tool_result] ........................................................................ [ 90%]
.........................................................                [100%]
609 passed, 24 skipped in 0.47s
'1 Byte' '1 Byte' '1B'
 M src/humanize/filesize.py
 M tests/test_filesize.py
[assistant] `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again when `gnu` is False. The full suite passes: 609 passed, 24 skipped.

The cause was one line in `src/humanize/filesize.py`. The 1-byte branch formatted the raw value (`f"{bytes_} Byte"`), so floats printed as `1.0`. In 4.11 this branch used `%d`. Commit 11e62ee had already switched the "less than one kilobyte" branch to `int(bytes_)` but missed this one. I changed it to `f"{int(bytes_)} Byte"`, which matches that existing branch.

In `tests/test_filesize.py` I added cases for `1.0`, `"1"` and `"1.0"` (expecting `"1 Byte"`), plus `1.0` with `gnu=True` (expecting `"1B"`). The existing test helper already checks the negative versions of each case. No existing tests were changed.

Two things I didn't check: the `gnu=True` path was already correct, and I didn't run any other test suites or linters beyond the project's pytest command.
