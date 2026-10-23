# trajectory base-1

final message:
`naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` when `gnu` is False, matching the output before 4.12. The full test suite passes (607 passed, 24 skipped).

The cause was the `abs_bytes == 1` branch in `src/humanize/filesize.py`, which printed the raw value (`f"{bytes_} Byte"`). I changed it to `int(bytes_)`, the same fix already applied to the sub-kilobyte branch in commit 11e62ee.

I added two cases to `tests/test_filesize.py`: `1.0` and `"1"` both expect `"1 Byte"`. The existing `1` case is unchanged.

Other sub-kilobyte outputs are unchanged, e.g. `1.123` still gives `"1 Bytes"` and `0.5` gives `"0 Bytes"`.

## events
[tool_use Bash] {"command": "git log --oneline -3 && grep -n \"\" src/humanize/filesize.py | sed -n '1,200p'", "description": "Show recent commits and filesize module"}
[tool_result] 2629e6b lithify: probe base
f23e5fb lithify init
3f797c2 eval setup at 8059ebe1732c
1:"""Bits and bytes related humanization."""
2:
3:from __future__ import annotations
4:
5:suffixes = {
6:    "decimal": (
7:        " kB",
8:        " MB",
9:        " GB",
10:        " TB",
11:        " PB",
12:        " EB",
13:        " ZB",
14:        " YB",
15:        " RB",
16:        " QB",
17:    ),
18:    "binary": (
19:        " KiB",
20:        " MiB",
21:        " GiB",
22:        " TiB",
23:        "
…[1823 chars elided]…
str):
87:        bytes_ = float(value)
88:    else:
89:        bytes_ = value
90:
91:    abs_bytes = abs(bytes_)
92:
93:    if abs_bytes == 1 and not gnu:
94:        return f"{bytes_} Byte"
95:
96:    if abs_bytes < base:
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
98:
99:    for i, s in enumerate(suffix, 2):
100:        unit = base**i
101:        if abs_bytes < unit:
102:            break
103:
104:    ret: str = format % (base * (bytes_ / unit)) + s
105:    return ret
[tool_use Bash] {"command": "git log --oneline -- src/humanize/filesize.py | head; git tag | tail -5; grep -rn \"Byte\" tests/ | head -20", "description": "Check history and existing Byte tests"}
[tool_result] 11e62ee Fix regression in naturalsize for float
fb61d5a Update pre-commit (#226)
a178851 Fix overflow issue in naturalsize with np.int32 input
33119c0 Fix rollover from ZB to 1.0 YB
0e2cab4 Merge branch 'main' into ronna
4a37bd1 [pre-commit.ci] auto fixes from pre-commit.com hooks
ae20f3b Remove shebang from filesize.py
53a19af Fix args for stricter Google docstring parsing by Griffe
a0bb67a filesize: more cleanups
4551ca0 filesize: appease the linter
4.5.0
4.6.0
4.7.0
4.8.0
4.9.0
tests/test_filesize.py:14:        ([300], "300 Bytes"),
tests/test_filesize.py:36:        ([300, True], "300 Bytes"),
tests/test_filesize.py:71:        ([1, False, False], "1 Byte"),
tests/test_filesize.py:76:        ([1.123456789], "1 Bytes"),
[tool_use Bash] {"command": "git show 11e62ee --stat && git show 11e62ee -- src/humanize/filesize.py | head -60; sed -n 60,90p tests/test_filesize.py", "description": "Inspect the commit that changed the Byte branch"}
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
…[1247 chars elided]…
),
        ([1.123456789 * 10**3], "1.1 kB"),
        ([1.123456789 * 10**6], "1.1 MB"),
        ([1.123456789, False, True], "1B"),
        ([1.123456789 * 10**3, False, True], "1.1K"),
        ([1.123456789 * 10**6, False, True], "1.1M"),
    ],
)
def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    # Retest with negative input
    if isinstance(test_args[0], int):
        test_args[0] *= -1
    else:
[assistant] The bug is on line 94: the `abs_bytes == 1` branch formats the raw value, so `1.0` prints as `1.0 Byte`. The `< base` branch already uses `int(...)` for this reason (commit 11e62ee). I'll apply the same fix to the Byte branch and add test cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py", "old_string": "        ([1, False, False], \"1 Byte\"),\n", "new_string": "        ([1, False, False], \"1 Byte\"),\n        ([1.0, False, False], \"1 Byte\"),\n        ([\"1\", False, False], \"1 Byte\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite with project interpreter"}
[tool_result] ......................................................................ss [ 11%]
sssssssssssssssssssss......s............................................ [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 57%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 91%]
.......................................................                  [100%]
607 passed, 24 skipped in 0.47s
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"import humanize as h; print(repr(h.naturalsize(1.0)), repr(h.naturalsize('1')), repr(h.naturalsize(1)), repr(h.naturalsize(1.123)), repr(h.naturalsize(0.5)))\" && git diff --stat", "description": "Spot-check outputs and show diff stat"}
[tool_result] '1 Byte' '1 Byte' '1 Byte' '1 Bytes' '0 Bytes'
 src/humanize/filesize.py | 2 +-
 tests/test_filesize.py   | 2 ++
 2 files changed, 3 insertions(+), 1 deletion(-)
[assistant] `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` when `gnu` is False, matching the output before 4.12. The full test suite passes (607 passed, 24 skipped).

The cause was the `abs_bytes == 1` branch in `src/humanize/filesize.py`, which printed the raw value (`f"{bytes_} Byte"`). I changed it to `int(bytes_)`, the same fix already applied to the sub-kilobyte branch in commit 11e62ee.

I added two cases to `tests/test_filesize.py`: `1.0` and `"1"` both expect `"1 Byte"`. The existing `1` case is unchanged.

Other sub-kilobyte outputs are unchanged, e.g. `1.123` still gives `"1 Bytes"` and `0.5` gives `"0 Bytes"`.
