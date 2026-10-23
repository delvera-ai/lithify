# trajectory comp-1

final message:
`naturalsize()` now supports ronna and quetta in all three modes: RB/QB (decimal), RiB/QiB (binary), and R/Q (GNU). The full suite passes with 562 passed and 23 skipped, and the `filesize.py` doctests pass when run explicitly.

**Changes**
- `src/humanize/filesize.py`: appended `" RB", " QB"`, `" RiB", " QiB"` and `"RQ"` to the three `suffixes` entries. The loop is unchanged. The three tables are still the same length (10 each).
- The docstring example `naturalsize(10**28)` changed from `'10000.0 YB'` to `'10.0 RB'`.
- `tests/test_filesize.py`: added 13 rows (boundary, just-inside and overflow for each new unit in each mode). The README examples are unaffected.

**Existing assertions I changed (the task requires these, since 3·10²⁷ is above the yottabyte range):**

| Row | Old | New |
|---|---|---|
| `10**26 * 30, False, True` | `"2481.5Y"` | `"2.4R"` |
| `10**26 * 30, True` | `"2481.5 YiB"` | `"2.4 RiB"` |
| `10**26 * 30` | `"3000.0 YB"` | `"3.0 RB"` |
| `10**26 * 30, True, False, "%.3f"` | `"2481.542 YiB"` | `"2.423 RiB"` |

**Not fixed: a float precision issue that predates this change.** `naturalsize` converts the value with `float()` before comparing it to the integer unit. Python can't hold `10**24` or `10**27` exactly, so values just below a decimal boundary round into the next unit. For example, `naturalsize(10**24)` gives `'1000.0 ZB'`, and `naturalsize(10**27 - 1)` gives `'1.0 RB'`. I picked test values that avoid this (such as `999 * 10**24`). Binary boundaries are powers of two, so they are exact. Fixing it means changing how the value is compared, which goes beyond this task.

**Not run:** `ruff` and `mypy` aren't installed in the project venv, so lint and typecheck were not run.

## events
[tool_use Skill] {"skill": "humanize-filesize-units"}
[tool_result] Launching skill: humanize-filesize-units
[user] Base directory for this skill: ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/.claude/skills/humanize-filesize-units

# naturalsize / filesize maintainer rules

All facts below are from `src/humanize/filesize.py` and `tests/test_filesize.py`.

## INVARIANT 1 — `suffixes` is the only unit table
`suffixes` (module-level dict in `filesize.py`) owns every byte-size unit name. The only other
prefix list in `src/` is the independent SI string inside `number.metric()`
(`src/humanize/number.py`, already `"kMGTPEZYRQ"`); it is not shared wit
…[2114 chars elided]…
tests/test_filesize.py`: the single `@pytest.mark.parametrize` table of
   `([value, binary, gnu, format], expected)` rows. Add new coverage as rows there, not new test
   functions. Each row is also asserted negated (`"-" + expected`), so write the positive value
   and unsigned expected string; use a list (the test mutates `test_args[0]`).

New rows should cover, per new unit and per mode (decimal / binary / GNU): the exact boundary
(`1000**k`, `1024**k`), a value just inside it, and the overflow case past the new top unit
(Invariant 2) — the property the old top-unit rows existed to check.

[tool_use Bash] {"command": "cat src/humanize/filesize.py; echo ---; grep -n \"naturalsize\\|YB\\|yotta\\|Yi\" -r tests docs README.md | head -80", "description": "Read filesize module and find related tests/docs"}
[tool_result] """Bits and bytes related humanization."""

from __future__ import annotations

suffixes = {
    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"),
    "binary": (" KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"),
    "gnu": "KMGTPEZY",
}


def naturalsize(
    value: float | str,
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
) -> str:
    """Format a number of bytes like a human readable filesize (e.g. 10 kB).

    By default, decimal
…[1838 chars elided]…
ue, False, "%.3f"], "2481.542 YiB"),
tests/test_filesize.py:36:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:37:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:41:    assert humanize.naturalsize(*args_with_negative) == "-" + expected
README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
[assistant] The skill's rules call for three things: keep the three `suffixes` tables parallel, update every example whose value changes unit, and add boundary/inside/overflow rows per mode. Next I'll read the test file, the README section, and check the project venv.
[tool_use Bash] {"command": "cat tests/test_filesize.py; echo ---; sed -n 145,170p README.md; echo ---; ls <work>/env-humanize/bin/python 2>&1; git status --short", "description": "Read filesize tests, README section, check venv"}
[tool_result] #!/usr/bin/env python

"""Tests for filesize humanizing."""
from __future__ import annotations

import pytest

import humanize


@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([300], "300 Bytes"),
        ([3000], "3.0 kB"),
        ([3000000], "3.0 MB"),
        ([3000000000], "3.0 GB"),
        ([3000000000000], "3.0 TB"),
        ([300, True], "300 Bytes"),
        ([3000, True], "2.9 KiB"),
        ([3000000, True], "2.9 MiB"),
        ([300, False, True], "300B"),
     
…[991 chars elided]…
s ago'
```

### File size humanization

```pycon
>>> import humanize
>>> humanize.naturalsize(1_000_000)
'1.0 MB'
>>> humanize.naturalsize(1_000_000, binary=True)
'976.6 KiB'
>>> humanize.naturalsize(1_000_000, gnu=True)
'976.6K'
```

### Human-readable floating point numbers

```pycon
>>> import humanize
>>> humanize.fractional(1/3)
'1/3'
---
<work>/env-humanize/bin/python
[assistant] Baseline run first, then I'll compute the new values for the rows the change affects.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run baseline test suite"}
[tool_result] ........................................................................ [ 88%]
....................................................................     [100%]
549 passed, 23 skipped in 0.59s
[assistant] Baseline is green (549 passed, 23 skipped). Now the edit to the unit table, with the loop and everything else unchanged:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPE
…[78 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py has been updated successfully.
[assistant] Next I'll check the new outputs directly, including the rows whose old values will change.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -I -c '\nimport humanize as h\nfrom humanize.filesize import suffixes as s\nprint(len(s[\"decimal\"]),len(s[\"binary\"]),len(s[\"gnu\"]))\ncases=[([10**26*30,False,True],),([10**26*30,True],),([10**26*30],),([
…[242 chars elided]…
1024**10,False,True],),([1024**10-1,False,True],),([10**27,False,True],),([10**30,False,True],),([10**33,False,True],),([1024**9,True],),([1024**10,True],),([1024**10*1000,True],),([10**30,True],),\n([1000**8,False,True],),([1024**8,False,True],), ([10**27-1],), ([1000**9-1],)]\nfor c in cases: print(c, repr(h.naturalsize(*c[0])))\n'", "description": "Check outputs for new units and changed rows"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
[assistant] `-I` ignores `PYTHONPATH`, and this is our own repo code, so I'll drop the flag.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c '\nimport humanize as h\nfrom humanize.filesize import suffixes as s\nprint(len(s[\"decimal\"]),len(s[\"binary\"]),len(s[\"gnu\"]))\ncases=[([10**26*30,False,True],),([10**26*30,True],),([10**26*30],),([10*
…[239 chars elided]…
1024**10,False,True],),([1024**10-1,False,True],),([10**27,False,True],),([10**30,False,True],),([10**33,False,True],),([1024**9,True],),([1024**10,True],),([1024**10*1000,True],),([10**30,True],),\n([1000**8,False,True],),([1024**8,False,True],), ([10**27-1],), ([1000**9-1],)]\nfor c in cases: print(c, repr(h.naturalsize(*c[0])))\n'", "description": "Check outputs for new units and changed rows"}
[tool_result] 10 10 10
([3000000000000000000000000000, False, True],) '2.4R'
([3000000000000000000000000000, True],) '2.4 RiB'
([3000000000000000000000000000],) '3.0 RB'
([3000000000000000000000000000, True, False, '%.3f'],) '2.423 RiB'
([10000000000000000000000000000],) '10.0 RB'
([1000000000000000000000000],) '1000.0 ZB'
([999999999999999999999999],) '1000.0 ZB'
([1000000000000000000000000000],) '1.0 RB'
([999999999999999999999999000],) '1.0 RB'
([1000000000000000000000000000000],) '1.0 QB'
([50000000000000
…[555 chars elided]…
00000000, False, True],) '807.8R'
([1000000000000000000000000000000000, False, True],) '788.9Q'
([1237940039285380274899124224, True],) '1.0 RiB'
([1267650600228229401496703205376, True],) '1.0 QiB'
([1267650600228229401496703205376000, True],) '1000.0 QiB'
([1000000000000000000000000000000, True],) '807.8 RiB'
([1000000000000000000000000, False, True],) '847.0Z'
([1208925819614629174706176, False, True],) '1.0Y'
([999999999999999999999999999],) '1.0 RB'
([999999999999999999999999999],) '1.0 RB'
[assistant] The outputs for the top units look right, but a few lines don't match my hand calculation, and I'd rather check than guess. I'll rerun with labelled cases.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c '\nimport humanize as h\nfor label,v,b,g in [(\"1e24\",10**24,False,False),(\"1e24-1\",10**24-1,False,False),(\"1e27\",10**27,False,False),(\"1e27-1\",10**27-1,False,False),(\"1e30\",10**30,False,False),(\"1e30-1\",10**30-1,False,False),(\"1e21\",10**21,False,False),(\"1e21-1\",10**21-1,False,False)]:\n    print(label, repr(h.naturalsize(v,b,g)))\n'", "description": "Check decimal boundary outputs with labels"}
[tool_result] 1e24 '1000.0 ZB'
1e24-1 '1000.0 ZB'
1e27 '1.0 RB'
1e27-1 '1.0 RB'
1e30 '1.0 QB'
1e30-1 '1.0 QB'
1e21 '1.0 ZB'
1e21-1 '1.0 ZB'
[assistant] The odd lines come from a pre-existing float issue, not the new units. `naturalsize` converts the value with `float(value)` and then compares it to an int `unit`. Python's float can't hold `10**24` or `10**27` exactly, so values just under a decimal boundary round up into the next unit. For example, `10**24` already printed `1000.0 ZB` before my change. I'll leave that alone, since fixing it changes behaviour the task didn't ask for, and I'll report it. For the new decimal boundary tests I'll use values that avoid it, such as `999 * 10**24`, and binary boundaries are exact because they are powers of two.

Now the docstring example that changes (`10**28` was `10000.0 YB`) and the test table:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),\n        ([1, False, False], \"1 Byte\"),\n        ([3141592, False, False
…[786 chars elided]…
10**33], \"1000.0 QB\"),\n        ([1024**9, True], \"1.0 RiB\"),\n        ([1023 * 1024**8, True], \"1023.0 YiB\"),\n        ([1024**10, True], \"1.0 QiB\"),\n        ([1024**11, True], \"1024.0 QiB\"),\n        ([1024**9, False, True], \"1.0R\"),\n        ([1023 * 1024**8, False, True], \"1023.0Y\"),\n        ([1024**10, False, True], \"1.0Q\"),\n        ([1024**11, False, True], \"1024.0Q\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/tests/test_filesize.py has been updated successfully.
[assistant] Now the full check command, plus the explicit doctest run for `filesize.py`, since the default run doesn't collect docstring examples.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---DOCTEST; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -5", "description": "Run full test suite and filesize doctests"}
[tool_result] .................................sssssssssssssssssssssss................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 36%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 73%]
........................................................................ [ 86%]
........................................................................ [ 98%]
.........                                                                [100%]
562 passed, 23 skipped in 0.46s
---DOCTEST
.                                                                        [100%]
1 passed in 0.01s
[assistant] All green: 562 passed (549 before, plus 13 new rows; the 23 skips were there before), and the filesize doctest passes. One last check is the tuple line length, since I wrapped the table and want it to match the surrounding style.
[tool_use Bash] {"command": "printf '%s' '    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\", \" RB\", \" QB\"),' | wc -c; printf '%s' '    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\", \" RiB\", \" QiB\"),' | wc -c; git diff --stat", "description": "Measure suffix line lengths and diff stat"}
[tool_result]       86
      95
 src/humanize/filesize.py | 30 ++++++++++++++++++++++++++----
 tests/test_filesize.py   | 21 +++++++++++++++++----
 2 files changed, 43 insertions(+), 8 deletions(-)
[assistant] The decimal line fits in 88 columns, so I'll put it back on one line and keep only the binary tuple wrapped, which keeps the diff smaller.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\n        \" kB\",\n        \" MB\",\n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),", "new_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\", \" RB\", \" QB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/comp-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -1; git diff src/humanize/filesize.py", "description": "Rerun tests, doctests, and show source diff"}
[tool_result] 562 passed, 23 skipped in 0.46s
1 passed in 0.01s
diff --git a/src/humanize/filesize.py b/src/humanize/filesize.py
index ca4d468..015685f 100644
--- a/src/humanize/filesize.py
+++ b/src/humanize/filesize.py
@@ -3,9 +3,20 @@
 from __future__ import annotations
 
 suffixes = {
-    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"),
-    "binary": (" KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"),
-    "gnu": "KMGTPEZY",
+    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB", " RB", " QB"),
+    "binary": (
+        " KiB",
+        " MiB",
+        " GiB",
+        " TiB",
+        " PiB",
+        " EiB",
+        " ZiB",
+        " YiB",
+        " RiB",
+        " QiB",
+    ),
+    "gnu": "KMGTPEZYRQ",
 }
 
 
@@ -34,7 +45,7 @@ def naturalsize(
         >>> naturalsize(3000, True)
         '2.9 KiB'
         >>> naturalsize(10**28)
-        '10000.0 YB'
+        '10.0 RB'
         >>> naturalsize(-4096, True)
         '-4.0 KiB'
[assistant] `naturalsize()` now supports ronna and quetta in all three modes: RB/QB (decimal), RiB/QiB (binary), and R/Q (GNU). The full suite passes with 562 passed and 23 skipped, and the `filesize.py` doctests pass when run explicitly.

**Changes**
- `src/humanize/filesize.py`: appended `" RB", " QB"`, `" RiB", " QiB"` and `"RQ"` to the three `suffixes` entries. The loop is unchanged. The three tables are still the same length (10 each).
- The docstring example `naturalsize(10**28)` changed from `'10000.0 YB'` to `'10.0 RB'`.
- `tests/test_filesize.py`: added 13 rows (boundary, just-inside and overflow
…[521 chars elided]…
` converts the value with `float()` before comparing it to the integer unit. Python can't hold `10**24` or `10**27` exactly, so values just below a decimal boundary round into the next unit. For example, `naturalsize(10**24)` gives `'1000.0 ZB'`, and `naturalsize(10**27 - 1)` gives `'1.0 RB'`. I picked test values that avoid this (such as `999 * 10**24`). Binary boundaries are powers of two, so they are exact. Fixing it means changing how the value is compared, which goes beyond this task.

**Not run:** `ruff` and `mypy` aren't installed in the project venv, so lint and typecheck were not run.
