# trajectory base-1

final message:
`naturalsize()` now rolls over to YB for large integers. Both reported inputs print `1.0 YB`, and the test suite passes (583 passed, 23 skipped).

**Cause:** the unit loop compared `float(value)` against integer thresholds. `float(10**24)` is 999999999999999983222784, which is below 10**24, so the loop stayed on ZB and `%.1f` printed `1000.0 ZB`. The second input also rounds to that same float.

**Fix** (`src/humanize/filesize.py`): the unit is now chosen from the exact decimal value as written, so int, str and float inputs all behave the same. The formatted value still comes from the float, as before. Non-finite inputs keep the old float comparison, since `Decimal` comparisons with NaN raise.

**Tests** (`tests/test_filesize.py`): I added three cases to the existing parametrized list: `10**24` → `1.0 YB`, the second reported value → `1.0 YB`, and `10**27` → `1.0 RB`. No existing expectations changed. The negative-input variant of the test also passes for them.

I did not commit. Ruff and mypy aren't installed in the project env, so I only checked line length by hand.

**Not changed:** a value just under a threshold can still display as `1000.x` after rounding. For example `10**24 - 1` gives `1000.0 ZB`, and the existing `999_960` gives `1000.0 kB`. That's a display-rounding issue that affects every unit, and fixing it would change output for smaller values too. Tell me if you want rollover based on the rounded display value instead.

## events
[tool_use Bash] {"command": "grep -n \"naturalsize\\|def \\|ZB\\|YB\\|1000\\|1024\" src/humanize/filesize.py | head -80; ls src/humanize", "description": "Locate naturalsize implementation"}
[tool_result] 13:        " ZB",
14:        " YB",
34:def naturalsize(
48:        >>> naturalsize(3000000)
50:        >>> naturalsize(300, False, True)
52:        >>> naturalsize(3000, False, True)
54:        >>> naturalsize(3000, False, True, "%.3f")
56:        >>> naturalsize(3000, True)
58:        >>> naturalsize(10**28)
60:        >>> naturalsize(10**34 * 3)
62:        >>> naturalsize(-4096, True)
85:    base = 1024 if (gnu or binary) else 1000
__init__.py
_version.py
filesize.py
i18n.py
locale
number.py
py.typed
time.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py"}
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
[assistant] The loop compares `float(value)` against integer thresholds, so I suspect float rounding at the 10^24 boundary. Let me confirm that and check the existing tests before changing anything.
[tool_use Bash] {"command": "ls <work>/env-humanize/bin/python 2>&1; PY=$(ls <work>/env-humanize/bin/python 2>/dev/null || which python3); echo \"PY=$PY\"; PYTHONPATH=src $PY -c \"\nfrom humanize import naturalsize as n\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 999_960, 999_960_000, 10**27-1, 10**24-1, 10**21, 3*10**34]:\n    print(v, repr(float(v)), n(v))\nprint(float(10**24) < 10**24)\n\"; grep -rn \"naturalsize\\|filesize\" tests | head -40", "description": "Reproduce the bug and locate related tests"}
[tool_result] <work>/env-humanize/bin/python
PY=<work>/env-humanize/bin/python
1000000000000000000000000 1e+24 1000.0 ZB
1000000000000000050331648 1e+24 1000.0 ZB
999960 999960.0 1000.0 kB
999960000 999960000.0 1000.0 MB
999999999999999999999999999 1e+27 1.0 RB
999999999999999999999999 1e+24 1000.0 ZB
1000000000000000000000 1e+21 1.0 ZB
30000000000000000000000000000000000 3e+34 30000.0 QB
True
tests/test_filesize.py:3:"""Tests for filesize humanizing."""
tests/test_filesize.py:67:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:68:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:72:    assert humanize.naturalsize(*args_with_negative) == "-" + expected
[assistant] Confirmed: `float(10**24) < 10**24` is `True`, because `float()` rounds 10^24 down to 999999999999999983222784. The loop then picks ZB, and `%.1f` prints 1000.0. The same thing happens to the second input and to float inputs like `1e24`. Next I'll check the test file and supported Python versions before choosing the fix.
[tool_use Bash] {"command": "sed -n 1,75p tests/test_filesize.py; grep -n \"requires-python\\|python_requires\" pyproject.toml setup.* 2>/dev/null; sed -n 1,12p src/humanize/number.py", "description": "Read filesize tests and Python version constraints"}
[tool_result ERROR] Exit code 1
#!/usr/bin/env python

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
        ([1
…[1735 chars elided]…
"], "3.14 MB"),
        ([3000, False, True, "%.3f"], "2.930K"),
        ([3000000000, False, True, "%.0f"], "3G"),
        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
    ],
)
def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    args_with_negative = test_args
    args_with_negative[0] *= -1
    assert humanize.naturalsize(*args_with_negative) == "-" + expected
(eval):1: no matches found: setup.*
[assistant] I'll compare the exact decimal value (as written) against the thresholds, rather than the float. That covers int, str and float inputs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py", "old_string": "from __future__ import annotations\n\nsuffixes = {", "new_string": "from __future__ import annotations\n\nimport math\nfrom decimal import Decimal\n\nsuffixes = {"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py", "old_string": "    bytes_ = float(value)\n    abs_bytes = abs(bytes_)\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % b
…[447 chars elided]…
tes = abs(Decimal(value if isinstance(value, (int, str)) else repr(value)))\n    else:\n        exact_bytes = abs_bytes\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % bytes_\n\n    for i, s in enumerate(suffix, 2):\n        unit = base**i\n        if exact_bytes < unit:\n            break"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import naturalsize as n\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 10**24-1, 10**27, 1e24, '1000000000000000050331648', '1e24', -10**24, 10**34*3, float('nan'), float('inf'), True, 300, 3000, 1024]:\n    print(repr(v), '->', n(v), '|', n(v, True))\n\"; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix on reported and edge inputs, run tests"}
[tool_result] 1000000000000000000000000 -> 1.0 YB | 847.0 ZiB
1000000000000000050331648 -> 1.0 YB | 847.0 ZiB
999999999999999999999999 -> 1000.0 ZB | 847.0 ZiB
1000000000000000000000000000 -> 1.0 RB | 827.2 YiB
1e+24 -> 1.0 YB | 847.0 ZiB
'1000000000000000050331648' -> 1.0 YB | 847.0 ZiB
'1e24' -> 1.0 YB | 847.0 ZiB
-1000000000000000000000000 -> -1.0 YB | -847.0 ZiB
30000000000000000000000000000000000 -> 30000.0 QB | 23665.8 QiB
nan -> nan QB | nan QiB
inf -> inf QB | inf QiB
True -> 1 Byte | 1 Byte
300 -> 300 Bytes | 300 Bytes
3000 -> 3.0 kB | 2.9 KiB
1024 -> 1.0 kB | 1.0 KiB
........................................................................ [ 71%]
........................................................................ [ 83%]
........................................................................ [ 95%]
...........................                                              [100%]
580 passed, 23 skipped in 0.56s
[assistant] The reported inputs now give `1.0 YB`, and all existing tests pass (580 passed, 23 skipped). I'll add regression cases to the existing parametrized test. Adding cases is fine; I'm not changing any existing expectation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n    ],", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),\n        ([10**24], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648], \"1.0 YB\"),\n        ([10**27], \"1.0 RB\"),\n    ],"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list >/dev/null; git status --short; git diff --stat; ls ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/CHANGELOG* 2>/dev/null; PYTHONPATH=src $PY -m ruff --version 2>/dev/null; PYTHONPATH=src $PY -m mypy --version 2>/dev/null", "description": "Run tests with new cases and check lint tools"}
[tool_result ERROR] Exit code 1
..............................                                           [100%]
583 passed, 23 skipped in 0.45s
 M src/humanize/filesize.py
 M tests/test_filesize.py
 src/humanize/filesize.py | 12 +++++++++++-
 tests/test_filesize.py   |  3 +++
 2 files changed, 14 insertions(+), 1 deletion(-)
(eval):1: no matches found: ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/CHANGELOG*
[assistant] Tests pass with the new cases (583 passed). I'll check the project's line-length limit, since one new line is long.
[tool_use Bash] {"command": "grep -rn \"line-length\\|line_length\\|max-line\" pyproject.toml setup.cfg .flake8 tox.ini .pre-commit-config.yaml 2>/dev/null; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' src/humanize/filesize.py", "description": "Check configured line length and long lines"}
[tool_result] src/humanize/filesize.py: 95: 91
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py", "old_string": "    if math.isfinite(bytes_):\n        exact_bytes = abs(Decimal(value if isinstance(value, (int, str)) else repr(value)))\n    else:", "new_string": "    if math.isfinite(bytes_):\n        exact = value if isinstance(value, (int, str)) else repr(value)\n        exact_bytes = abs(Decimal(exact))\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; PYTHONPATH=src $PY -c \"from humanize import naturalsize as n; print(n(10**24), n(1_000_000_000_000_000_050_331_648), n(-10**24))\"; git diff", "description": "Re-run tests after line-length tidy and show diff"}
[tool_result] 583 passed, 23 skipped in 0.68s
1.0 YB 1.0 YB -1.0 YB
diff --git a/src/humanize/filesize.py b/src/humanize/filesize.py
index 996506e..352fe87 100644
--- a/src/humanize/filesize.py
+++ b/src/humanize/filesize.py
@@ -2,6 +2,9 @@
 
 from __future__ import annotations
 
+import math
+from decimal import Decimal
+
 suffixes = {
     "decimal": (
         " kB",
@@ -85,6 +88,14 @@ def naturalsize(
     base = 1024 if (gnu or binary) else 1000
     bytes_ = float(value)
     abs_bytes = abs(bytes_)
+  
…[766 chars elided]…
ndex 416cbf1..0c8ea93 100644
--- a/tests/test_filesize.py
+++ b/tests/test_filesize.py
@@ -62,6 +62,9 @@ import humanize
         ([3000, False, True, "%.3f"], "2.930K"),
         ([3000000000, False, True, "%.0f"], "3G"),
         ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
+        ([10**24], "1.0 YB"),
+        ([1_000_000_000_000_000_050_331_648], "1.0 YB"),
+        ([10**27], "1.0 RB"),
     ],
 )
 def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
[assistant] `naturalsize()` now rolls over to YB for large integers. Both reported inputs print `1.0 YB`, and the test suite passes (583 passed, 23 skipped).

**Cause:** the unit loop compared `float(value)` against integer thresholds. `float(10**24)` is 999999999999999983222784, which is below 10**24, so the loop stayed on ZB and `%.1f` printed `1000.0 ZB`. The second input also rounds to that same float.

**Fix** (`src/humanize/filesize.py`): the unit is now chosen from the exact decimal value as written, so int, str and float inputs all behave the same. The formatted value still comes from the float, a
…[257 chars elided]…
nd `10**27` → `1.0 RB`. No existing expectations changed. The negative-input variant of the test also passes for them.

I did not commit. Ruff and mypy aren't installed in the project env, so I only checked line length by hand.

**Not changed:** a value just under a threshold can still display as `1000.x` after rounding. For example `10**24 - 1` gives `1000.0 ZB`, and the existing `999_960` gives `1000.0 kB`. That's a display-rounding issue that affects every unit, and fixing it would change output for smaller values too. Tell me if you want rollover based on the rounded display value instead.
