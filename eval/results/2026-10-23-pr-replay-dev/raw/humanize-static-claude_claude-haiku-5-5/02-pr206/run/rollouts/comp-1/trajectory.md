# trajectory comp-1

final message:
`naturalsize()` now rolls over to YB for large integer inputs: `10**24` and `1_000_000_000_000_000_050_331_648` both return `'1.0 YB'`. The project's `verify.py` reports tests PASS (586 passed, 23 skipped) and doctests PASS. Nothing is committed.

**Cause:** `abs_bytes` is `abs(float(value))`, and above 2**53 the float can land just under a unit boundary. `float(10**24) < 10**24` is `True`, so the unit loop stopped at ZB and displayed `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): for `int` inputs, the unit loop compares the exact int, `exact_bytes = abs(value)`. Every other input type keeps the float comparison. The displayed number is still computed the same way.

**Tests and docs:**
- `tests/test_filesize.py`: added rows for the boundary (`10**24`), just above it (the reported case), just inside (`10**24 - 10**20` → `999.9 ZB`), past the top unit (`10**34 * 3` → `30000.0 QB`), and the binary and GNU boundaries (`1024**8` → `1.0 YiB` / `1.0Y`). The expected strings came from running the code. The existing test helper also checks each row negated.
- `naturalsize` docstring: added a `10**24` → `'1.0 YB'` example.

**Not changed, for you to decide:**
- **Display rounding.** Values just below a boundary still show the next unit's `1000.0`: `10**24 - 1` → `'1000.0 ZB'`, `2**80 - 1` (binary) → `'1024.0 ZiB'`, and the existing `999_960` → `'1000.0 kB'`. The issue asks that you never see `1000.x` of a unit, which would need a `number.intword`-style re-divide. That changes output for small units too, so I left it out of this fix.
- **String inputs.** `naturalsize("1000000000000000000000000")` still goes through `float()` and returns `'1000.0 ZB'`. I kept the change to `int` inputs. Extending it to integer strings is a small follow-up.

**Not verified:** ruff and mypy aren't installed in the project's test environment, so `verify.py` reports them NOT AVAILABLE. I checked for both and they aren't present.

## events
[tool_use Skill] {"skill": "humanize-filesize-units"}
[tool_result] Launching skill: humanize-filesize-units
[user] Base directory for this skill: ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/.claude/skills/humanize-filesize-units

# naturalsize / filesize.py — maintainer invariants

## Where things live
- `src/humanize/filesize.py` owns `naturalsize()` and the module-level `suffixes` dict. Nothing
  else in the package formats byte sizes; `number.py` (`intword`, `metric`) is separate.
- Tests: the single parametrize table in `tests/test_filesize.py::test_naturalsize`.
- Docs: the `pycon` block in the `naturalsize` docstring, and the `naturalsi
…[3212 chars elided]…
ject.toml`, which wins over
`tox.ini`'s `--doctest-modules`. So it does NOT collect docstring examples. `.lithify/harness/scripts/verify.py` runs
`--doctest-modules` on changed `src/` modules; otherwise run it on `src/humanize/filesize.py`.

## Style (from pyproject.toml)
- Every module starts with `from __future__ import annotations` (ruff isort `required-imports`).
  Imports are isort-ordered, stdlib first.
- Use Google-style docstrings, and stay within ruff's default 88-character lines (no
  `line-length` is configured). mypy runs `--strict`, so keep `naturalsize`'s annotations
  accurate.

[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness/ 2>/dev/null; cat src/humanize/filesize.py", "description": "Read memory notes and filesize module"}
[tool_result] - The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
"""Bits and bytes related humanization."""

from __future__ import annotations

suffixes = {
    "decimal": (
        " kB",
        " MB",
        " GB",
        " TB",
        " PB",

…[1660 chars elided]…
uffix = suffixes["binary"]
    else:
        suffix = suffixes["decimal"]

    base = 1024 if (gnu or binary) else 1000
    bytes_ = float(value)
    abs_bytes = abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return "%d Byte" % bytes_

    if abs_bytes < base:
        return ("%dB" if gnu else "%d Bytes") % bytes_

    for i, s in enumerate(suffix, 2):
        unit = base**i
        if abs_bytes < unit:
            break

    ret: str = format % (base * bytes_ / unit) + s
    return ret
[assistant] The skill's invariants point at the cause: `abs_bytes` is a float, so the `< unit` comparison is inexact above 2**53. I'll read the tests, README, and verify script before editing.
[tool_use Bash] {"command": "cat tests/test_filesize.py; echo ----; grep -n -i -B2 -A12 \"naturalsize\" README.md | head -80; echo ----; ls .lithify/harness/scripts/; git status --short; git log --oneline -1", "description": "Read tests, README naturalsize section, harness scripts"}
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
…[2179 chars elided]…
expected
----
155-```pycon
156->>> import humanize
157:>>> humanize.naturalsize(1_000_000)
158-'1.0 MB'
159:>>> humanize.naturalsize(1_000_000, binary=True)
160-'976.6 KiB'
161:>>> humanize.naturalsize(1_000_000, gnu=True)
162-'976.6K'
163-```
164-
165-### Human-readable floating point numbers
166-
167-```pycon
168->>> import humanize
169->>> humanize.fractional(1/3)
170-'1/3'
171->>> humanize.fractional(1.5)
172-'1 1/2'
173->>> humanize.fractional(0.3)
----
verify.py
ec514b0 lithify: probe base
[assistant] Next I'll reproduce the bug with the project interpreter from the memory notes.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; echo \"PY=$PY\"; PYTHONPATH=src $PY -c '\nfrom humanize import naturalsize as n\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 10**24-1, 10**24*3, 10**25, 999_960]:\n    print(repr(v), n(v), n(v, binary=True), n(v, gnu=True))\nprint(n(str(10**24)), n(float(10**24)), n(10**24, binary=True))\n'; echo \"exit=$?\"", "description": "Reproduce the naturalsize rollover bug"}
[tool_result] PY=<work>/env-humanize/bin/python
1000000000000000000000000 1000.0 ZB 847.0 ZiB 847.0Z
1000000000000000050331648 1000.0 ZB 847.0 ZiB 847.0Z
999999999999999999999999 1000.0 ZB 847.0 ZiB 847.0Z
3000000000000000000000000 3.0 YB 2.5 YiB 2.5Y
10000000000000000000000000 10.0 YB 8.3 YiB 8.3Y
999960 1000.0 kB 976.5 KiB 976.5K
1000.0 ZB 1000.0 ZB 847.0 ZiB
exit=0
[assistant] Reproduced: `10**24` and `10**24 + 50331648` both print `1000.0 ZB`. The cause is `abs_bytes = abs(float(value))`: `float(10**24) < 10**24` is `True`, so the loop stops one unit too late. The fix is to compare the exact int when the input is an `int`, and keep the float path for everything else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py", "old_string": "    bytes_ = float(value)\n    abs_bytes = abs(bytes_)\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % b
…[295 chars elided]…
k the unit from the exact int when there is one.\n    exact_bytes = abs(value) if isinstance(value, int) else abs_bytes\n\n    if abs_bytes == 1 and not gnu:\n        return \"%d Byte\" % bytes_\n\n    if abs_bytes < base:\n        return (\"%dB\" if gnu else \"%d Bytes\") % bytes_\n\n    for i, s in enumerate(suffix, 2):\n        unit = base**i\n        if exact_bytes < unit:\n            break"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py has been updated successfully.
[assistant] Now I'll check the new output across the three modes, the negative inputs, and the string and float paths.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c '\nfrom humanize import naturalsize as n\nfrom decimal import Decimal\nfor v in [10**24, 1_000_000_000_000_000_050_331_648, 10**24-1, 10**24*3, 10**25, 999_960, 10**27-1, 10**30]:\n    print(repr(v), \"|\", n(v), \"|\", n(-v), \"|\", n(v, binary=True), \"|\", n(v, gnu=True))\nprint(\"str\", n(str(10**24)), \"float\", n(float(10**24)), \"dec\", n(Decimal(10**24)), \"nan\", n(float(\"nan\")), \"inf\", n(float(\"inf\")))\n'; echo \"exit=$?\"", "description": "Check fixed output across modes and input types"}
[tool_result] 1000000000000000000000000 | 1.0 YB | -1.0 YB | 847.0 ZiB | 847.0Z
1000000000000000050331648 | 1.0 YB | -1.0 YB | 847.0 ZiB | 847.0Z
999999999999999999999999 | 1000.0 ZB | -1000.0 ZB | 847.0 ZiB | 847.0Z
3000000000000000000000000 | 3.0 YB | -3.0 YB | 2.5 YiB | 2.5Y
10000000000000000000000000 | 10.0 YB | -10.0 YB | 8.3 YiB | 8.3Y
999960 | 1000.0 kB | -1000.0 kB | 976.5 KiB | 976.5K
999999999999999999999999999 | 1000.0 YB | -1000.0 YB | 827.2 YiB | 827.2Y
1000000000000000000000000000000 | 1.0 QB | -1.0 QB | 807.8 RiB | 807.8R
str 1000.0 ZB float 1000.0 ZB dec 1000.0 ZB nan nan QB inf inf QB
exit=0
[assistant] The fix holds for the reported inputs, and negatives and the float path stay consistent. The `10**24 - 1` case still shows `1000.0 ZB`; that's display rounding (invariant 6), which I'll report rather than change. Before writing test rows, I want to check the binary modes at 2**k-1 boundaries, where the same float rounding could bite.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c '\nfrom humanize import naturalsize as n\nfor k in [70, 80]:\n    v = 2**k - 1\n    print(k, n(v, binary=True), n(v, gnu=True), n(2**k, binary=True), n(2**k, gnu=True))\nprint(n(1000**8 * 38), n(10**34*3), n(10**24-10**20), n(10**24-10**20, binary=True))\n'; echo \"exit=$?\"", "description": "Check binary-mode boundary values"}
[tool_result] 70 1024.0 EiB 1024.0E 1.0 ZiB 1.0Z
80 1024.0 ZiB 1024.0Z 1.0 YiB 1.0Y
38.0 YB 30000.0 QB 999.9 ZB 846.9 ZiB
exit=0
[assistant] The binary `2**k - 1` cases print `1024.0 ZiB`/`1024.0 EiB`, which is the same display-rounding behaviour as `999_960` → `1000.0 kB`, not the exact-comparison bug. I'll leave that alone and mention it. Now I'll add parametrize rows (boundary, just inside, past the top unit) for each mode, plus the docstring example. The expected values come from the runs above.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py", "offset": 14, "limit": 12}
[tool_result] 14	        ([300], "300 Bytes"),
15	        ([1000**1 * 31], "31.0 kB"),
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py", "old_string": "        ([1000**10 * 40], \"40.0 QB\"),\n        ([300, True], \"300 Bytes\"),", "new_string": "        ([1000**10 * 40], \"40.0 QB\"),\n        ([10**24], \"1.0 YB\"),\n        ([1_000_000_000_000_000_050_331_648], \"1.0 YB\"),\n        ([10**24 - 10**20], \"999.9 ZB\"),\n        ([10**34 * 3], \"30000.0 QB\"),\n        ([300, True], \"300 Bytes\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py", "old_string": "        ([1024**10 * 40, True], \"40.0 QiB\"),", "new_string": "        ([1024**10 * 40, True], \"40.0 QiB\"),\n        ([1024**8, True], \"1.0 YiB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py", "old_string": "        ([1000**10 * 40, False, True], \"31.6Q\"),", "new_string": "        ([1000**10 * 40, False, True], \"31.6Q\"),\n        ([1024**8, False, True], \"1.0Y\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10.0 RB'", "new_string": "        >>> naturalsize(10**24)\n        '1.0 YB'\n        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py has been updated successfully.
[assistant] Now the required verification: the project's `verify.py` script, with the interpreter from the memory notes.
[tool_use Bash] {"command": "export PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/verify.py; echo \"exit=$?\"", "description": "Run project verification script"}
[tool_result] --- tests: <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no
   .........................................................sssssssssssssss [ 11%]
   ssssssss................................................................ [ 23%]
   ........................................................................ [ 35%]
   ......................................
…[843 chars elided]…
[100%]
   1 passed in 0.02s
RESULT doctests: PASS
RESULT ruff: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
RESULT mypy: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
OVERALL: PASS
exit=0
[assistant] Tests and doctests pass. Ruff and mypy are reported NOT AVAILABLE, so I'll confirm that directly and review the diff.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY -m ruff --version; echo \"ruff exit=$?\"; $PY -m mypy --version; echo \"mypy exit=$?\"; which ruff mypy; echo; git diff --stat; git diff src/", "description": "Check ruff/mypy availability and show the diff"}
[tool_result] <work>/env-humanize/bin/python: No module named ruff
ruff exit=1
<work>/env-humanize/bin/python: No module named mypy
mypy exit=1
ruff not found
mypy not found

 src/humanize/filesize.py | 7 ++++++-
 tests/test_filesize.py   | 6 ++++++
 2 files changed
…[607 chars elided]…
a large int below a unit boundary (float(10**24) < 10**24),
+    # so pick the unit from the exact int when there is one.
+    exact_bytes = abs(value) if isinstance(value, int) else abs_bytes
 
     if abs_bytes == 1 and not gnu:
         return "%d Byte" % bytes_
@@ -94,7 +99,7 @@ def naturalsize(
 
     for i, s in enumerate(suffix, 2):
         unit = base**i
-        if abs_bytes < unit:
+        if exact_bytes < unit:
             break
 
     ret: str = format % (base * bytes_ / unit) + s
[assistant] Ruff and mypy aren't installed in that environment, so they stay unverified. One thing I can fix by reading: my new comment line is about 90 characters, over the 88-column limit in the skill's style notes. I'll shorten it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py", "old_string": "    # float(value) can round a large int below a unit boundary (float(10**24) < 10**24),\n    # so pick the unit from the exact int when there is one.", "new_string": "    # float(value) can round a large int below a unit boundary, so compare the\n    # exact int when the input is one."}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-134509-bug-humanize-naturalsize-does-no/comp-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "export PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/verify.py 2>&1 | grep -E \"RESULT|OVERALL|passed|failed\"; echo \"exit=$?\"", "description": "Re-run project verification after comment edit"}
[tool_result]    586 passed, 23 skipped in 0.47s
RESULT tests: PASS
   1 passed in 0.01s
RESULT doctests: PASS
RESULT ruff: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
RESULT mypy: NOT AVAILABLE (not importable by <work>/env-humanize/bin/python, not on PATH)
OVERALL: PASS
exit=0
[assistant] `naturalsize()` now rolls over to YB for large integer inputs: `10**24` and `1_000_000_000_000_000_050_331_648` both return `'1.0 YB'`. The project's `verify.py` reports tests PASS (586 passed, 23 skipped) and doctests PASS. Nothing is committed.

**Cause:** `abs_bytes` is `abs(float(value))`, and above 2**53 the float can land just under a unit boundary. `float(10**24) < 10**24` is `True`, so the unit loop stopped at ZB and displayed `1000.0 ZB`.

**Fix** (`src/humanize/filesize.py`): for `int` inputs, the unit loop compares the exact int, `exact_bytes = abs(value)`. Every other input type ke
…[734 chars elided]…
d the existing `999_960` → `'1000.0 kB'`. The issue asks that you never see `1000.x` of a unit, which would need a `number.intword`-style re-divide. That changes output for small units too, so I left it out of this fix.
- **String inputs.** `naturalsize("1000000000000000000000000")` still goes through `float()` and returns `'1000.0 ZB'`. I kept the change to `int` inputs. Extending it to integer strings is a small follow-up.

**Not verified:** ruff and mypy aren't installed in the project's test environment, so `verify.py` reports them NOT AVAILABLE. I checked for both and they aren't present.
