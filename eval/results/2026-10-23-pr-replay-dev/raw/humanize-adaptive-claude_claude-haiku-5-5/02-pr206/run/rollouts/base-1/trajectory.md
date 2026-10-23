# trajectory base-1

final message:
Large integers now roll over to the next unit: `naturalsize(10**24)` and `naturalsize(1_000_000_000_000_000_050_331_648)` both return `'1.0 YB'`. The project suite passes (584 passed, 23 skipped).

**Cause:** `naturalsize` converts the input to a float, then compares it to the exact integer unit (`base**i`). `float(10**24)` is `999999999999999983222784`, which is slightly below the integer `10**24`, so the loop stopped one unit early at ZB.

**Fix** (`src/humanize/filesize.py`): the unit is now `float(base**i)`, so the comparison uses the same float as the input. I added a comment explaining why.

**Tests** (`tests/test_filesize.py`): added cases for `10**24`, `10**24 - 1`, the second example from the report, and `10**27` (→ `1.0 RB`).

I did not commit. I also left one thing alone: small values near a unit boundary still print the 1000.x form, e.g. `naturalsize(999999)` gives `'1000.0 kB'`. That is existing behaviour outside this bug, and changing it would alter output for many inputs, so I kept this change to the large-integer boundary. Say if you want the boundary rule applied to every unit.

## events
[tool_use Bash] {"command": "grep -rn \"def naturalsize\" --include=*.py . | head; git status --short | head", "description": "Locate naturalsize implementation"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"def naturalsize\" . ; git status --short | head", "description": "Locate naturalsize implementation"}
[tool_result] src/humanize/filesize.py:34:def naturalsize(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py"}
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
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\nfor v in [999999, 999_999_999, 10**24, 10**24-1, 1_000_000_000_000_000_050_331_648, 10**27, 10**21, 999*10**21]:\n    print(v, n(v))\n\"; ls <work>/env-humanize/bin/python 2>&1 | tail -1", "description": "Reproduce naturalsize boundary cases"}
[tool_result] 999999 1000.0 kB
999999999 1000.0 MB
1000000000000000000000000 1000.0 ZB
999999999999999999999999 1000.0 ZB
1000000000000000050331648 1000.0 ZB
1000000000000000000000000000 1.0 RB
1000000000000000000000 1.0 ZB
999000000000000000000000 999.0 ZB
<work>/env-humanize/bin/python
[assistant] Reproduced. The cause is a float-vs-int comparison: `float(10**24)` is `999999999999999983222784`, which is slightly below the exact integer `10**24`, so `abs_bytes < unit` is true and the loop stops at ZB. The fix is to compare against the same float the input is converted to.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py", "old_string": "        unit = base**i\n        if abs_bytes < unit:", "new_string": "        # Compare as floats: `abs_bytes` is a float, and an exact int boundary\n        # such as 10**24 can sit above float(10**24), which would stop the loop\n        # one unit too early and print \"1000.0 ZB\" instead of \"1.0 YB\".\n        unit = float(base**i)\n        if abs_bytes < unit:"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\nfor v in [10**24, 10**24-1, 1_000_000_000_000_000_050_331_648, 10**27, 10**21, 999*10**21, 3*10**34, -10**24]:\n    print(v, n(v), n(v, binary=True))\n\" && <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix and run project test suite"}
[tool_result] 1000000000000000000000000 1.0 YB 847.0 ZiB
999999999999999999999999 1.0 YB 847.0 ZiB
1000000000000000050331648 1.0 YB 847.0 ZiB
1000000000000000000000000000 1.0 RB 827.2 YiB
1000000000000000000000 1.0 ZB 867.4 EiB
999000000000000000000000 999.0 ZB 846.2 ZiB
30000000000000000000000000000000000 30000.0 QB 23665.8 QiB
-1000000000000000000000000 -1.0 YB -847.0 ZiB
ERROR tests/test_i18n.py
ERROR tests/test_number.py
ERROR tests/test_time.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
4 errors in 0.12s
[assistant] The fix behaves correctly. The test run failed at collection, so I'll rerun it with the `PYTHONPATH=src` the project's checks specify.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git stash list | head -0; git diff --stat", "description": "Run project tests with PYTHONPATH and show diff stat"}
[tool_result] ........................................................................ [ 71%]
........................................................................ [ 83%]
........................................................................ [ 95%]
...........................                                              [100%]
580 passed, 23 skipped in 0.47s
head: illegal line count -- 0
 src/humanize/filesize.py | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)
[assistant] The suite passes. I'll add a regression test next to the existing filesize tests.
[tool_use Bash] {"command": "ls tests | grep -i size; grep -n \"QB\\|def test\" tests/test_filesize.py | tail -15", "description": "Find existing filesize test file and cases"}
[tool_result] test_filesize.py
24:        ([1000**10 * 40], "40.0 QB"),
67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py", "offset": 15, "limit": 15}
[tool_result] 15	        ([1000**1 * 31], "31.0 kB"),
16	        ([1000**2 * 32], "32.0 MB"),
17	        ([1000**3 * 33], "33.0 GB"),
18	        ([1000**4 * 34], "34.0 TB"),
19	        ([1000**5 * 35], "35.0 PB"),
20	        ([1000**6 * 36], "36.0 EB"),
21	        ([1000**7 * 37], "37.0 ZB"),
22	        ([1000**8 * 38], "38.0 YB"),
23	        ([1000**9 * 39], "39.0 RB"),
24	        ([1000**10 * 40], "40.0 QB"),
25	        ([300, True], "300 Bytes"),
26	        ([1024**1 * 31, True], "31.0 KiB"),
27	        ([1024**2 * 32, True], "32.0 MiB"),
28	        ([1024**3 * 33, True], "33.0 GiB"),
29	        ([1024**4 * 34, True], "34.0 TiB"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py", "old_string": "        ([1000**10 * 40], \"40.0 QB\"),\n", "new_string": "        ([1000**10 * 40], \"40.0 QB\"),\n        ([10**24], \"1.0 YB\"),\n        ([10**24 - 1], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648], \"1.0 YB\"),\n        ([10**27], \"1.0 RB\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Rerun project tests with new regression cases"}
[tool_result] ...............................                                          [100%]
584 passed, 23 skipped in 0.79s
[assistant] Large integers now roll over to the next unit: `naturalsize(10**24)` and `naturalsize(1_000_000_000_000_000_050_331_648)` both return `'1.0 YB'`. The project suite passes (584 passed, 23 skipped).

**Cause:** `naturalsize` converts the input to a float, then compares it to the exact integer unit (`base**i`). `float(10**24)` is `999999999999999983222784`, which is slightly below the integer `10**24`, so the loop stopped one unit early at ZB.

**Fix** (`src/humanize/filesize.py`): the unit is now `float(base**i)`, so the comparison uses the same float as the input. I added a comment explaining why.

**Tests** (`tests/test_filesize.py`): added cases for `10**24`, `10**24 - 1`, the second example from the report, and `10**27` (→ `1.0 RB`).

I did not commit. I also left one thing alone: small values near a unit boundary still print the 1000.x form, e.g. `naturalsize(999999)` gives `'1000.0 kB'`. That is existing behaviour outside this bug, and changing it would alter output for many inputs, so I kept this change to the large-integer boundary. Say if you want the boundary rule applied to every unit.
