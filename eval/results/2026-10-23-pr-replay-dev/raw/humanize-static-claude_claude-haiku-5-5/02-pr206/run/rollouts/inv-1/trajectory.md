# trajectory inv-1

final message:
Large integers now roll over to the next unit. Both examples from the report return `'1.0 YB'`, and `verify.py` passes on tests and doctests.

**Cause:** `naturalsize` called `float(value)` before choosing a unit. Above 2**53 a float cannot hold every integer, so `10**24` became `999999999999999983222784.0`. That is just below `10**24`, so the ZB unit was picked and the result printed as `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): a new helper `_to_number` keeps ints, and int strings, exact. Float inputs still go through `float()` as before. The unit comparison is now exact for integer input.

**Tests:** I added three cases to `tests/test_filesize.py`: `10**24`, the second example from the report, and `999 * 10**21` expecting `'999.0 ZB'`. I also added a `naturalsize(10**24)` → `'1.0 YB'` doctest. No existing tests were changed.

**Verify output:**
- tests: PASS (583 passed, 23 skipped)
- doctests: PASS
- ruff and mypy: NOT AVAILABLE. Neither is importable from the harness interpreter, so I did not run them.

**Not changed:**
- **Float inputs:** `naturalsize(1e24)` still returns `'1000.0 ZB'`. The float value is really 999999999999999983222784 bytes, so fixing it would need a different rule. I left it alone.
- **Rounding at other units:** the report says smaller units never show `1000.x`, but that is not true. For example `naturalsize(999_950)` returns `'1000.0 kB'`, and `naturalsize(999_999_999)` returns `'1000.0 MB'`. The same display-rounding issue exists at every decimal and binary unit. It is a separate rounding question and would change existing output, so I did not fix it here. Say if you want it addressed.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"def naturalsize\" src/ && cat .lithify/harness/memory.md 2>/dev/null | head -30; ls .lithify/harness/ 2>/dev/null", "description": "Locate naturalsize implementation and harness memory"}
[tool_result] src/humanize/filesize.py:34:def naturalsize(
- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
guardrails.md
memory.md
scripts
system.md
tool_guidance.md
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py"}
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
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize.filesize import naturalsize as n\nfor v in [999949, 999950, 999999, 10**6-1, 10**9-1, 10**24, 10**24+50331648, 1e24, 10**27-1, 10**30, 10**33, 999*10**21, 999_999*10**21, 10**36]:\n    print(v, repr(n(v)), repr(n(v, True)))\n\"; ls tests 2>/dev/null; grep -rn \"naturalsize\" tests | head -5; PY=<work>/env-humanize/bin/python; ls $PY 2>&1; git status --short", "description": "Reproduce naturalsize rollover behavior across magnitudes"}
[tool_result] 999949 '999.9 kB' '976.5 KiB'
999950 '1000.0 kB' '976.5 KiB'
999999 '1000.0 kB' '976.6 KiB'
999999 '1000.0 kB' '976.6 KiB'
999999999 '1000.0 MB' '953.7 MiB'
1000000000000000000000000 '1000.0 ZB' '847.0 ZiB'
1000000000000000050331648 '1000.0 ZB' '847.0 ZiB'
1e+24 '1000.0 ZB' '847.0 ZiB'
999999999999999999999999999 '1.0 RB' '827.2 YiB'
1000000000000000000000000000000 '1.0 QB' '807.8 RiB'
1000000000000000000000000000000000 '1000.0 QB' '788.9 QiB'
999000000000000000000000 '999.0 ZB' '846.2 ZiB'
9999
…[131 chars elided]…
t_filesize.py
test_i18n.py
test_number.py
test_time.py
tests/test_filesize.py:67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:68:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:72:    assert humanize.naturalsize(*args_with_negative) == "-" + expected
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "sed -n 1,80p tests/test_filesize.py; grep -n \"1000\\.0\" tests/test_filesize.py | head; cat .lithify/harness/scripts/verify.py | head -40 | grep -n \"ruff\\|mypy\\|RESULT\" ", "description": "Read existing filesize tests and verify script hints"}
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
…[1829 chars elided]…
], "3G"),
        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
    ],
)
def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    args_with_negative = test_args
    args_with_negative[0] *= -1
    assert humanize.naturalsize(*args_with_negative) == "-" + expected
12:  3. ruff / mypy       run only if importable or on PATH; otherwise reported as
36:        print(f"RESULT {label}: COULD NOT RUN ({exc})")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py", "old_string": "    base = 1024 if (gnu or binary) else 1000\n    bytes_ = float(value)\n    abs_bytes = abs(bytes_)", "new_string": "    base = 1024 if (gnu or binary) else 1000\n    bytes_ = _to_number(value)\n    abs_bytes = abs(bytes_)"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py", "old_string": "def naturalsize(\n    value: float | str,", "new_string": "def _to_number(value: float | str) -> int | float:\n    \"\"\"Return integers exactly, so large values are not rounded by `float()`.\"\"\"\n    if isinstance(value, (int, str)):\n        try:\n            return int(value)\n        except ValueError:\n            pass\n    return float(value)\n\n\ndef naturalsize(\n    value: float | str,"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**34 * 3)\n        '30000.0 QB'", "new_string": "        >>> naturalsize(10**34 * 3)\n        '30000.0 QB'\n        >>> naturalsize(10**24)\n        '1.0 YB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n    ],", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n        ([10**24], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648], \"1.0 YB\"),\n        ([10**21 * 999], \"999.0 ZB\"),\n    ],"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/inv-1/tests/test_filesize.py has been updated successfully.
[assistant] Edits are in. Now running the project's verify script, using the interpreter from the harness memory.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/verify.py; echo \"exit=$?\"", "description": "Run project verify script (tests, doctests, lint)"}
[tool_result] --- tests: <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no
   ......................................................ssssssssssssssssss [ 11%]
   sssss................................................................... [ 23%]
   ........................................................................ [ 35%]
   ......................................
…[843 chars elided]…
[100%]
   1 passed in 0.01s
RESULT doctests: PASS
RESULT ruff: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
RESULT mypy: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
OVERALL: PASS
exit=0
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize.filesize import naturalsize as n\nprint(n(1_000_000_000_000_000_000_000_000), n(1_000_000_000_000_000_050_331_648), n('1000000000000000000000000'), n(999_999 * 10**21), n(-10**24), n(3000, True), n(1e24))\n\"; git status --short", "description": "Check the issue's examples and changed files"}
[tool_result] 1.0 YB 1.0 YB 1.0 YB 1000.0 YB -1.0 YB 2.9 KiB 1000.0 ZB
 M src/humanize/filesize.py
 M tests/test_filesize.py
[assistant] Large integers now roll over to the next unit. Both examples from the report return `'1.0 YB'`, and `verify.py` passes on tests and doctests.

**Cause:** `naturalsize` called `float(value)` before choosing a unit. Above 2**53 a float cannot hold every integer, so `10**24` became `999999999999999983222784.0`. That is just below `10**24`, so the ZB unit was picked and the result printed as `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): a new helper `_to_number` keeps ints, and int strings, exact. Float inputs still go through `float()` as before. The unit comparison is now exact for integer
…[491 chars elided]…
till returns `'1000.0 ZB'`. The float value is really 999999999999999983222784 bytes, so fixing it would need a different rule. I left it alone.
- **Rounding at other units:** the report says smaller units never show `1000.x`, but that is not true. For example `naturalsize(999_950)` returns `'1000.0 kB'`, and `naturalsize(999_999_999)` returns `'1000.0 MB'`. The same display-rounding issue exists at every decimal and binary unit. It is a separate rounding question and would change existing output, so I did not fix it here. Say if you want it addressed.

Changes are uncommitted in the worktree.
