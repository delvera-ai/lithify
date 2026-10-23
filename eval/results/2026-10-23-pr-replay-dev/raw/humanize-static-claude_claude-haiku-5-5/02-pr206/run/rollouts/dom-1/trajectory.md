# trajectory dom-1

final message:
Large integer inputs now roll over to the next unit. `naturalsize(10**24)` and `naturalsize(10**24 + 50331648)` both return `'1.0 YB'`, and the project's test run passes (587 passed, 23 skipped).

**Cause:** the unit loop compared `abs(float(value))` against the exact int `base**i`. Above 2**53 the float can round below the int: `float(10**24)` is `999999999999999983222784`, which is less than `10**24`, so the value stayed in ZB.

**Change** (`src/humanize/filesize.py`): when the input is an `int`, the loop compares the exact int. Every other input type (float, numeric string, `Decimal`, `bool`) still goes through the existing float comparison, so their behavior is unchanged. The displayed number still uses float division.

**Tests** (`tests/test_filesize.py`): I added rows for the decimal boundary at 10**21, 10**24 (with the reported offset value), and 10**27. I also added binary (`1024**8`, `1024**8 + 2**20` → `1.0 YiB`) and gnu (`1024**8` → `1.0Y`) rows. I generated the expected strings by running the fixed code.

Things to know:
- **Not run:** `mypy --strict` and `ruff` aren't installed in the project's check environment, so I couldn't run them. I also didn't run the docstring doctests; the explicit `--doctest-modules` run on `filesize.py` passed.
- **Not covered:** numeric strings such as `"1000000000000000000000000"` still take the float path and still print `1000.0 ZB`. Supporting them would need a separate int-parsing branch, which I left out to keep the change narrow.
- **Display rounding, out of scope:** `naturalsize(10**24 - 1)` still prints `'1000.0 ZB'`, because `%.1f` rounds up at the top of a unit. The same happens for small units (`naturalsize(999_960)` → `'1000.0 kB'`), so the issue's claim that you never see "1000.x" doesn't hold for kB either. Fixing it would change output for every unit and needs a decision on whether to adopt the `intword`-style re-division. I didn't make that change.

I haven't committed anything.

## events
[tool_use Skill] {"skill": "humanize-filesize-units"}
[tool_result] Launching skill: humanize-filesize-units
[user] Base directory for this skill: ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/.claude/skills/humanize-filesize-units

# naturalsize / filesize.py — maintainer invariants

## Where things live
- `src/humanize/filesize.py` owns `naturalsize()` and the module-level `suffixes` dict. Nothing
  else in the package formats byte sizes; `number.py` (`intword`, `metric`) is separate.
- Tests: the single parametrize table in `tests/test_filesize.py::test_naturalsize`.
- Docs: the `pycon` block in the `naturalsize` docstring, and the `naturalsiz
…[3152 chars elided]…
ult pytest run uses `[tool.pytest.ini_options]` from `pyproject.toml`, which wins over
`tox.ini`'s `--doctest-modules`. So it does NOT collect docstring examples. Check them with
an explicit `--doctest-modules src/humanize/filesize.py` run.

## Style (from pyproject.toml)
- Every module starts with `from __future__ import annotations` (ruff isort `required-imports`).
  Imports are isort-ordered, stdlib first.
- Use Google-style docstrings, and stay within ruff's default 88-character lines (no
  `line-length` is configured). mypy runs `--strict`, so keep `naturalsize`'s annotations
  accurate.

[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/src/humanize/filesize.py"}
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
[assistant] The skill's invariants point at exact int comparison in the unit-selection loop. Before changing anything, I'll reproduce both reported outputs and check the existing tests and the `intword` rollover pattern.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\nfor v in [10**24, 10**24+50331648, 10**27, 10**24-1, 10**21, 999_960, 10**28, 10**34*3]:\n    print(repr(v), n(v), '|', n(v, binary=True), '|', n(v, gnu=True))\nprint(n(float(10**24)))\n\" ; grep -n \"1000\\|intword\\|def \\|float(\" src/humanize/number.py | head -60", "description": "Reproduce reported outputs and inspect number.py rollover"}
[tool_result] 1000000000000000000000000 1000.0 ZB | 847.0 ZiB | 847.0Z
1000000000000000050331648 1000.0 ZB | 847.0 ZiB | 847.0Z
1000000000000000000000000000 1.0 RB | 827.2 YiB | 827.2Y
999999999999999999999999 1000.0 ZB | 847.0 ZiB | 847.0Z
1000000000000000000000 1.0 ZB | 867.4 EiB | 867.4E
999960 1000.0 kB | 976.5 KiB | 976.5K
10000000000000000000000000000 10.0 RB | 8.1 RiB | 8.1R
30000000000000000000000000000000000 30000.0 QB | 23665.8 QiB | 23665.8Q
1000.0 ZB
26:def _format_not_finite(value: float) -> str:
…[1463 chars elided]…
mber = float(value)
364:    frac = Fraction(number - whole_number).limit_denominator(1000)
378:def scientific(value: NumberOrString, precision: int = 2) -> str:
383:        >>> scientific(float(0.3))
387:        >>> scientific(-1000)
389:        >>> scientific(1000, 1)
391:        >>> scientific(1000, 3)
423:        value = float(value)
443:def clamp(
466:        >>> clamp(1, format=intword, floor=1e6, floor_token="under ")
518:def metric(value: float, unit: str = "", precision: int = 3) -> str:
[assistant] Both outputs reproduce: `10**24` and `10**24 + 50331648` both print `1000.0 ZB`. The cause is the unit comparison: `float(10**24)` rounds down to `999999999999999983222784`, so `abs_bytes < 10**24` is true. The fix is to compare the exact int when the input is an int. Next I'll look at the test table before editing.
[tool_use Bash] {"command": "grep -n \"naturalsize\" -A3 tests/test_filesize.py | head -80; grep -n \"naturalsize\" README.md", "description": "Inspect filesize tests and README examples"}
[tool_result] 67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
68:    assert humanize.naturalsize(*test_args) == expected
69-
70-    args_with_negative = test_args
71-    args_with_negative[0] *= -1
72:    assert humanize.naturalsize(*args_with_negative) == "-" + expected
157:>>> humanize.naturalsize(1_000_000)
159:>>> humanize.naturalsize(1_000_000, binary=True)
161:>>> humanize.naturalsize(1_000_000, gnu=True)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/tests/test_filesize.py"}
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
15	        ([1000**1 * 31], "31.0 kB"),
16	        ([1000**2 * 32], "32.0 MB"),
17	        ([1000**3 * 33], "33.0 GB"),
18	        ([1000**4 * 34], "34.0 TB"),
19	        ([1000**5 * 35], "35.0 PB"),
20	        ([1000**6 * 36], "36.0 EB"),
21	      
…[1898 chars elided]…
], "3.14 MB"),
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
[assistant] Now the fix: compare the exact int when the input is an `int`, and keep the float path for everything else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/src/humanize/filesize.py", "old_string": "    bytes_ = float(value)\n    abs_bytes = abs(bytes_)\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % by
…[257 chars elided]…
% bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % bytes_\n\n    # Compare ints exactly: float(10**24) rounds down, which would keep\n    # 10**24 in the lower unit.\n    abs_exact: float | int = abs(value) if isinstance(value, int) else abs_bytes\n    for i, s in enumerate(suffix, 2):\n        unit = base**i\n        if abs_exact < unit:\n            break"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll generate the expected strings by running the fixed code, then add rows for the boundary cases to the parametrize table.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\ncases = [\n (10**24, {}), (10**24+50331648, {}), (10**27, {}), (10**21, {}), (10**21*999, {}),\n (1024**8, {'binary':True}), (1024**8+2**20, {'binary':True}), (1024**9, {'binary':True}),\n (1000**8, {'gnu':True}), (1000**8+10**15, {'gnu':True}), (1024**8, {'gnu':True}),\n]\nfor v,kw in cases: print(repr(v), kw, repr(n(v,**kw)), repr(n(-v,**kw)))\n\" ; PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n; print(n(10**24-1), n(999_960))\"", "description": "Generate expected strings from the fixed code"}
[tool_result] 1000000000000000000000000 {} '1.0 YB' '-1.0 YB'
1000000000000000050331648 {} '1.0 YB' '-1.0 YB'
1000000000000000000000000000 {} '1.0 RB' '-1.0 RB'
1000000000000000000000 {} '1.0 ZB' '-1.0 ZB'
999000000000000000000000 {} '999.0 ZB' '-999.0 ZB'
1208925819614629174706176 {'binary': True} '1.0 YiB' '-1.0 YiB'
1208925819614629175754752 {'binary': True} '1.0 YiB' '-1.0 YiB'
1237940039285380274899124224 {'binary': True} '1.0 RiB' '-1.0 RiB'
1000000000000000000000000 {'gnu': True} '847.0Z' '-847.0Z'
1000000001000000000000000 {'gnu': True} '847.0Z' '-847.0Z'
1208925819614629174706176 {'gnu': True} '1.0Y' '-1.0Y'
1000.0 ZB 1000.0 kB
[assistant] The fixed outputs look right. I'll leave `10**24 - 1` out of the tests: it displays `1000.0 ZB` because `%.1f` rounds up, which the skill notes is a separate display-rounding issue. Adding the boundary rows now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n    ],", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n        ([10**21], \"1.0 ZB\"),\n        ([10**24], \"1.0 YB\"),\n        ([10**24 + 50331648], \"1.0 YB\"),\n        ([10**27], \"1.0 RB\"),\n        ([1024**8, True], \"1.0 YiB\"),\n        ([1024**8 + 2**20, True], \"1.0 YiB\"),\n        ([1024**8, False, True], \"1.0Y\"),\n    ],"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/dom-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll run the project's checks: the test suite using the command from CLAUDE.md, the docstring doctests, mypy, and ruff.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ls $PY >/dev/null 2>&1 && echo \"env ok\" || echo \"env missing\"; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -3; $PY -m mypy --strict src/humanize/filesize.py 2>&1 | tail -3; $PY -m ruff check src tests 2>&1 | tail -3; $PY -m ruff format --check src tests 2>&1 | tail -2", "description": "Run tests, doctests, mypy and ruff checks"}
[tool_result] env ok
..........................................................ssssssssssssss [ 11%]
sssssssss............................................................... [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 59%]
........................................................................ [ 70%]
.............
…[387 chars elided]…
-donovan-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-humanize/bin/python: No module named mypy
<work>/env-humanize/bin/python: No module named ruff
<work>/env-humanize/bin/python: No module named ruff
[assistant] Large integer inputs now roll over to the next unit. `naturalsize(10**24)` and `naturalsize(10**24 + 50331648)` both return `'1.0 YB'`, and the project's test run passes (587 passed, 23 skipped).

**Cause:** the unit loop compared `abs(float(value))` against the exact int `base**i`. Above 2**53 the float can round below the int: `float(10**24)` is `999999999999999983222784`, which is less than `10**24`, so the value stayed in ZB.

**Change** (`src/humanize/filesize.py`): when the input is an `int`, the loop compares the exact int. Every other input type (float, numeric string, `Decimal`, `bool
…[769 chars elided]…
h and still print `1000.0 ZB`. Supporting them would need a separate int-parsing branch, which I left out to keep the change narrow.
- **Display rounding, out of scope:** `naturalsize(10**24 - 1)` still prints `'1000.0 ZB'`, because `%.1f` rounds up at the top of a unit. The same happens for small units (`naturalsize(999_960)` → `'1000.0 kB'`), so the issue's claim that you never see "1000.x" doesn't hold for kB either. Fixing it would change output for every unit and needs a decision on whether to adopt the `intword`-style re-division. I didn't make that change.

I haven't committed anything.
