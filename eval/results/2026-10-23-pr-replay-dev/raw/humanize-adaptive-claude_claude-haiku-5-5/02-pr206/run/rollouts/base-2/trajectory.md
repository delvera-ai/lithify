# trajectory base-2

final message:
Large integers now roll over to the next unit: `naturalsize(10**24)` and `naturalsize(1_000_000_000_000_000_050_331_648)` both return `'1.0 YB'`. The full suite passes (583 passed, 23 skipped) using the project's interpreter.

**Cause:** `naturalsize` converts the input to a float and picks the unit by comparing that float to `base**i`. A large integer loses precision in the conversion. `10**24` becomes `999999999999999983222784.0`, which is genuinely below `10**24`, so the loop stopped at ZB and printed `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): unit selection now compares an exact `Decimal(str(value))` instead of the float. The float is still used for the displayed number. The `Decimal` import is from the standard library.

**Tests:** I added three cases to the existing parametrized `test_naturalsize` in `tests/test_filesize.py`: `10**24`, the second example from the report, and `10**27` (which should give `1.0 RB`). The existing cases are unchanged, and the negative-value check covers the new ones too.

**Not changed:** the report says smaller units never show `1000.x`, but that isn't true today. `naturalsize(999_999)` returns `'1000.0 kB'`, because the value is below the MB threshold and then rounds up when formatted. The same happens for every unit below ZB. Fixing that means choosing the unit from the rounded display value, which changes output for ordinary sizes, so I left it alone. If you want that invariant enforced everywhere, it's a separate change; I can make it if you want.

I have not committed anything.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -n \"naturalsize\" -r src | head -30", "description": "Inspect repo layout and find naturalsize"}
[tool_result] AGENTS.md
CLAUDE.md
LICENCE
README.md
RELEASING.md
docs
mkdocs.yml
pyproject.toml
scripts
src
tests
tox.ini
src/humanize/__init__.py:5:from humanize.filesize import naturalsize
src/humanize/__init__.py:41:    "naturalsize",
src/humanize/filesize.py:34:def naturalsize(
src/humanize/filesize.py:48:        >>> naturalsize(3000000)
src/humanize/filesize.py:50:        >>> naturalsize(300, False, True)
src/humanize/filesize.py:52:        >>> naturalsize(3000, False, True)
src/humanize/filesize.py:54:        >>> naturalsize(3000, False, True, "%.3f")
src/humanize/filesize.py:56:        >>> naturalsize(3000, True)
src/humanize/filesize.py:58:        >>> naturalsize(10**28)
src/humanize/filesize.py:60:        >>> naturalsize(10**34 * 3)
src/humanize/filesize.py:62:        >>> naturalsize(-4096, True)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/src/humanize/filesize.py"}
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
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\nfor v in [10**24, 10**24+50331648, 999_960, 999_950, 999_999, 999_960_000_000_000_000_000_000, 10**27, 10**30-1, 10**33, 3*10**34, 999999*10**24]:\n    print(v, repr(n(v)), repr(n(v, binary=True)), repr(n(v, gnu=True)))\n\" ; ls tests; PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider --color=no tests/test_filesize.py 2>&1 | tail -3", "description": "Reproduce the bug and run filesize tests"}
[tool_result] 1000000000000000000000000 '1000.0 ZB' '847.0 ZiB' '847.0Z'
1000000000000000050331648 '1000.0 ZB' '847.0 ZiB' '847.0Z'
999960 '1000.0 kB' '976.5 KiB' '976.5K'
999950 '1000.0 kB' '976.5 KiB' '976.5K'
999999 '1000.0 kB' '976.6 KiB' '976.6K'
999960000000000000000000 '1000.0 ZB' '847.0 ZiB' '847.0Z'
1000000000000000000000000000 '1.0 RB' '827.2 YiB' '827.2Y'
999999999999999999999999999999 '1.0 QB' '807.8 RiB' '807.8R'
1000000000000000000000000000000000 '1000.0 QB' '788.9 QiB' '788.9Q'
30000000000000000000000000000000000 '30000.0 QB' '23665.8 QiB' '23665.8Q'
999999000000000000000000000000 '1000.0 RB' '807.8 RiB' '807.8R'
__init__.py
test_filesize.py
test_i18n.py
test_number.py
test_time.py
...................................................                      [100%]
51 passed in 0.02s
[tool_use Bash] {"command": "grep -n \"1000\\|10\\*\\*\\|def test\" tests/test_filesize.py | head -80; ls <work>/env-humanize/bin/python 2>&1 | tail -1; git log --oneline -3 -- src/humanize/filesize.py", "description": "Check existing filesize tests and project venv"}
[tool_result] 15:        ([1000**1 * 31], "31.0 kB"),
16:        ([1000**2 * 32], "32.0 MB"),
17:        ([1000**3 * 33], "33.0 GB"),
18:        ([1000**4 * 34], "34.0 TB"),
19:        ([1000**5 * 35], "35.0 PB"),
20:        ([1000**6 * 36], "36.0 EB"),
21:        ([1000**7 * 37], "37.0 ZB"),
22:        ([1000**8 * 38], "38.0 YB"),
23:        ([1000**9 * 39], "39.0 RB"),
24:        ([1000**10 * 40], "40.0 QB"),
36:        ([1000**1 * 31, True], "30.3 KiB"),
37:        ([1000**2 * 32, True], "30.5 MiB"),
38:  
…[828 chars elided]…
),
55:        ([1000**10 * 40, False, True], "31.6Q"),
64:        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
<work>/env-humanize/bin/python
0e2cab4 Merge branch 'main' into ronna
4a37bd1 [pre-commit.ci] auto fixes from pre-commit.com hooks
ae20f3b Remove shebang from filesize.py
[assistant] The cause is in the unit-selection loop: `abs_bytes` is a float, so a large integer like `10**24` rounds to a float just below `1e24`, and the `< unit` check picks ZB instead of YB. I'll keep the exact value for that comparison.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/src/humanize/filesize.py", "old_string": "    base = 1024 if (gnu or binary) else 1000\n    bytes_ = float(value)\n    abs_bytes = abs(bytes_)\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n       
…[356 chars elided]…
becomes\n    # slightly below 1e24), so pick the unit from the exact value.\n    exact_bytes = abs(Decimal(str(value)))\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % bytes_\n\n    for i, s in enumerate(suffix, 2):\n        unit = base**i\n        if exact_bytes < unit:\n            break"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/src/humanize/filesize.py", "old_string": "from __future__ import annotations\n\nsuffixes", "new_string": "from __future__ import annotations\n\nfrom decimal import Decimal\n\nsuffixes"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll add regression tests next to the existing parametrized cases, then run the suite with the project's interpreter.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/tests/test_filesize.py", "offset": 55, "limit": 20}
[tool_result] 55	        ([1000**10 * 40, False, True], "31.6Q"),
56	        ([300, False, True], "300B"),
57	        ([3000, False, True], "2.9K"),
58	        ([3000000, False, True], "2.9M"),
59	        ([1024, False, True], "1.0K"),
60	        ([1, False, False], "1 Byte"),
61	        ([3141592, False, False, "%.2f"], "3.14 MB"),
62	        ([3000, False, True, "%.3f"], "2.930K"),
63	        ([3000000000, False, True, "%.0f"], "3G"),
64	        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
65	    ],
66	)
67	def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
68	    assert humanize.naturalsize(*test_args) == expected
69	
70	    args_with_negative = test_args
71	    args_with_negative[0] *= -1
72	    assert humanize.naturalsize(*args_with_negative) == "-" + expected
73	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n    ],\n)", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n        ([10**24, False, False], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648, False, False], \"1.0 YB\"),\n        ([10**27, False, False], \"1.0 RB\"),\n    ],\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-134527-bug-humanize-naturalsize-does-no/base-2/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nfrom humanize import naturalsize as n\nprint(n(10**24), n(10**24+50331648), n(10**24, binary=True), n(1e24), n('1000000000000000000000000'), n(10**27), n(-10**24), n(999_999), n(3000))\"", "description": "Run full test suite and spot-check outputs"}
[tool_result] ........................................................................ [ 71%]
........................................................................ [ 83%]
........................................................................ [ 95%]
..............................                                           [100%]
583 passed, 23 skipped in 0.50s
1.0 YB 1.0 YB 847.0 ZiB 1.0 YB 1.0 YB 1.0 RB -1.0 YB 1000.0 kB 3.0 kB
[assistant] Large integers now roll over to the next unit: `naturalsize(10**24)` and `naturalsize(1_000_000_000_000_000_050_331_648)` both return `'1.0 YB'`. The full suite passes (583 passed, 23 skipped) using the project's interpreter.

**Cause:** `naturalsize` converts the input to a float and picks the unit by comparing that float to `base**i`. A large integer loses precision in the conversion. `10**24` becomes `999999999999999983222784.0`, which is genuinely below `10**24`, so the loop stopped at ZB and printed `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): unit selection now compares an exact `
…[352 chars elided]…
ng cases are unchanged, and the negative-value check covers the new ones too.

**Not changed:** the report says smaller units never show `1000.x`, but that isn't true today. `naturalsize(999_999)` returns `'1000.0 kB'`, because the value is below the MB threshold and then rounds up when formatted. The same happens for every unit below ZB. Fixing that means choosing the unit from the rounded display value, which changes output for ordinary sizes, so I left it alone. If you want that invariant enforced everywhere, it's a separate change; I can make it if you want.

I have not committed anything.
