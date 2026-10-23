# trajectory base-1

final message:
Both examples from the report now roll over to `1.0 YB`, and the project test suite passes (582 passed, 23 skipped).

**Cause:** `naturalsize` converted every input with `float(value)` before choosing a unit. Large ints lose precision in that conversion. `10**24` became `999999999999999983222784.0`, which is just under the ZB/YB boundary, so the code picked ZB and formatted it as `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): when the input is an `int`, the unit comparison now uses the exact int value. Float input and string input behave as before.

**Test** (`tests/test_filesize.py`): I added the two reported values as new parametrized cases. No existing test was changed.

Two related cases still show `1000.x`, and I left them alone because they are not large-int precision problems:

- **Rounding at the top of a unit.** `999_999_999_999_999_999_999_999` still prints `1000.0 ZB`, because the value is below 1000 ZB but rounds up to 1000.0 with `%.1f`. The same thing happens at smaller units: `naturalsize(999_960)` gives `1000.0 kB`. So the claim that smaller units never show `1000.x` is not quite right. Fixing this needs the unit choice to look at the formatted value, which depends on the caller's `format` string. I can do that if you want it.
- **Numeric strings.** `naturalsize("1000000000000000000000000")` still gives `1000.0 ZB`, because strings go through `float()` as well. Parsing integer strings exactly would fix it.

The changes are uncommitted in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"naturalsize\" --include=*.py . | head -30", "description": "Locate naturalsize implementation"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"naturalsize\\|YB\\|ZB\" --exclude-dir=.git . | head -40", "description": "Search repo for naturalsize and unit references"}
[tool_result] README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
tests/test_filesize.py:21:        ([1000**7 * 37], "37.0 ZB"),
tests/test_filesize.py:22:        ([1000**8 * 38], "38.0 YB"),
tests/test_filesize.py:67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:68:    assert humanize.naturalsize(*test_args) == expected
tests/t
…[461 chars elided]…
   >>> naturalsize(3000000)
src/humanize/filesize.py:50:        >>> naturalsize(300, False, True)
src/humanize/filesize.py:52:        >>> naturalsize(3000, False, True)
src/humanize/filesize.py:54:        >>> naturalsize(3000, False, True, "%.3f")
src/humanize/filesize.py:56:        >>> naturalsize(3000, True)
src/humanize/filesize.py:58:        >>> naturalsize(10**28)
src/humanize/filesize.py:60:        >>> naturalsize(10**34 * 3)
src/humanize/filesize.py:62:        >>> naturalsize(-4096, True)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133910-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py"}
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
…[1646 chars elided]…
s["decimal"]
84	
85	    base = 1024 if (gnu or binary) else 1000
86	    bytes_ = float(value)
87	    abs_bytes = abs(bytes_)
88	
89	    if abs_bytes == 1 and not gnu:
90	        return "%d Byte" % bytes_
91	
92	    if abs_bytes < base:
93	        return ("%dB" if gnu else "%d Bytes") % bytes_
94	
95	    for i, s in enumerate(suffix, 2):
96	        unit = base**i
97	        if abs_bytes < unit:
98	            break
99	
100	    ret: str = format % (base * bytes_ / unit) + s
101	    return ret
102	
[tool_use Bash] {"command": "sed -n 1,75p tests/test_filesize.py; ls <work>/env-humanize/bin/python 2>&1; PYTHONPATH=src python3 -c \"\nimport humanize\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 999_960, 10**27, 10**30]:\n    print(v, humanize.naturalsize(v), humanize.naturalsize(v, binary=True), humanize.naturalsize(v, gnu=True))\n\"", "description": "Read tests and reproduce the bug"}
[tool_result] #!/usr/bin/env python

"""Tests for filesize humanizing."""
from __future__ import annotations

import pytest

import humanize


@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([300], "300 Bytes"),
        ([1000**1 * 31], "31.0 kB"),
        ([1000**2 * 32], "32.0 MB"),
        ([1000**3 * 33], "33.0 GB"),
        ([1000**4 * 34], "34.0 TB"),
        ([1000**5 * 35], "35.0 PB"),
        ([1000**6 * 36], "36.0 EB"),
        ([1000**7 * 37], "37.0 ZB"),
        ([1000**8 * 38]
…[2091 chars elided]…
gs_with_negative[0] *= -1
    assert humanize.naturalsize(*args_with_negative) == "-" + expected
<work>/env-humanize/bin/python
1000000000000000000000000 1000.0 ZB 847.0 ZiB 847.0Z
1000000000000000050331648 1000.0 ZB 847.0 ZiB 847.0Z
999960 1000.0 kB 976.5 KiB 976.5K
1000000000000000000000000000 1.0 RB 827.2 YiB 827.2Y
1000000000000000000000000000000 1.0 QB 807.8 RiB 807.8R
[assistant] Reproduced. The cause is in `naturalsize`: `float(value)` rounds large ints. `10**24` becomes `999999999999999983222784.0`, which sits just under the ZB boundary, so the unit loop picks ZB and the value formats as `1000.0 ZB`. I'll keep int inputs exact for the comparisons.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133910-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py", "old_string": "    bytes_ = float(value)\n    abs_bytes = abs(bytes_)", "new_string": "    bytes_ = float(value)\n    # Compare ints exactly: float() can round a large int below a unit boundary\n    abs_bytes = abs(value) if isinstance(value, int) else abs(bytes_)"}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133910-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133910-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n    ],", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n        ([10**24], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648], \"1.0 YB\"),\n    ],"}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133910-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 10**24-1, -10**24]:\n    print(v, humanize.naturalsize(v), humanize.naturalsize(v, binary=True), humanize.naturalsize(v, gnu=True))\n\" && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check repro outputs and run the project test suite"}
[tool_result] 1000000000000000000000000 1.0 YB 847.0 ZiB 847.0Z
1000000000000000050331648 1.0 YB 847.0 ZiB 847.0Z
999999999999999999999999 1000.0 ZB 847.0 ZiB 847.0Z
-1000000000000000000000000 -1.0 YB -847.0 ZiB -847.0Z
.....................................................sssssssssssssssssss [ 11%]
ssss.................................................................... [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 59%]
........................................................................ [ 71%]
........................................................................ [ 83%]
........................................................................ [ 95%]
.............................                                            [100%]
582 passed, 23 skipped in 0.54s
[assistant] The reported cases now roll over, and the suite passes (582 passed, 23 skipped). Two related inputs still show `1000.0`, so I'll check them before reporting.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nprint(humanize.naturalsize('1000000000000000000000000'))\nprint(humanize.naturalsize(999_960))\n\" && git status --short && git diff --stat", "description": "Check string input and rounding edge cases; show diff stat"}
[tool_result] 1000.0 ZB
1000.0 kB
 M src/humanize/filesize.py
 M tests/test_filesize.py
 src/humanize/filesize.py | 3 ++-
 tests/test_filesize.py   | 2 ++
 2 files changed, 4 insertions(+), 1 deletion(-)
[assistant] Both examples from the report now roll over to `1.0 YB`, and the project test suite passes (582 passed, 23 skipped).

**Cause:** `naturalsize` converted every input with `float(value)` before choosing a unit. Large ints lose precision in that conversion. `10**24` became `999999999999999983222784.0`, which is just under the ZB/YB boundary, so the code picked ZB and formatted it as `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): when the input is an `int`, the unit comparison now uses the exact int value. Float input and string input behave as before.

**Test** (`tests/test_filesize.py`): I 
…[300 chars elided]…
cause the value is below 1000 ZB but rounds up to 1000.0 with `%.1f`. The same thing happens at smaller units: `naturalsize(999_960)` gives `1000.0 kB`. So the claim that smaller units never show `1000.x` is not quite right. Fixing this needs the unit choice to look at the formatted value, which depends on the caller's `format` string. I can do that if you want it.
- **Numeric strings.** `naturalsize("1000000000000000000000000")` still gives `1000.0 ZB`, because strings go through `float()` as well. Parsing integer strings exactly would fix it.

The changes are uncommitted in the working tree.
