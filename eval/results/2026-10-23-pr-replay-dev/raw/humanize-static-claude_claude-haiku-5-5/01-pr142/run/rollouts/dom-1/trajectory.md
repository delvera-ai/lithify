# trajectory dom-1

final message:
`humanize.naturalsize()` now supports ronna and quetta. Values past the YB range are expressed in RB/QB, RiB/QiB, or R/Q. The full suite passes (564 passed, 23 skipped), and the filesize doctest passes with `--doctest-modules`. The changes are uncommitted.

- **`src/humanize/filesize.py`**: appended `RB`, `QB`, `RiB`, `QiB` to the decimal and binary tables, and `RQ` to the GNU string. All three tables still have 10 entries in the same order.
- **Docstring**: `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.
- **`tests/test_filesize.py`**:
  - Four existing rows use the same inputs but new expectations: `2481.5Y` → `2.4R`, `2481.5 YiB` → `2.4 RiB`, `3000.0 YB` → `3.0 RB`, and `2481.542 YiB` → `2.423 RiB`. The project guardrail says not to weaken existing tests. Here the old expectations are the behaviour you asked me to remove, so I changed them. Please confirm that reading.
  - Added rows for each new unit in each mode: the exact boundary, a value just inside it, and overflow past the new top unit (`10**33` → `1000.0 QB`, `1024**11` → `1024.0 QiB` / `1024.0Q`).
- **README**: unchanged, since its examples are all in MB or smaller.
- **`number.metric()`**: untouched, as the skill notes it has its own separate prefix list.

Decision for you: the input `10**27 - 1` rounds to `1.0 RB`, not `1000.0 YB`. That is because `float()` conversion rounds it to exactly `1e27`. This predates my change and is not something I fixed.

## events
[tool_use Skill] {"skill": "humanize-filesize-units", "args": "Extend humanize.naturalsize() with ronna (R, 10^27) and quetta (Q, 10^30) decimal units, binary RiB/QiB, and GNU single-letter R/Q suffixes. Values beyond the YB range should now use RB/QB (RiB/QiB, R/Q)."}
[tool_result] Launching skill: humanize-filesize-units
[user] Base directory for this skill: ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/.claude/skills/humanize-filesize-units

# naturalsize / filesize maintainer rules

All facts below are from `src/humanize/filesize.py` and `tests/test_filesize.py`.

## INVARIANT 1 — `suffixes` is the only unit table
`suffixes` (module-level dict in `filesize.py`) owns every byte-size unit name. The only other
prefix list in `src/` is the independent SI string inside `number.metric()`
(`src/humanize/number.py`, already `"kMGTPEZYRQ"`); it is not shared with
…[2330 chars elided]…
(`"-" + expected`), so write the positive value
   and unsigned expected string; use a list (the test mutates `test_args[0]`).

New rows should cover, per new unit and per mode (decimal / binary / GNU): the exact boundary
(`1000**k`, `1024**k`), a value just inside it, and the overflow case past the new top unit
(Invariant 2) — the property the old top-unit rows existed to check.


ARGUMENTS: Extend humanize.naturalsize() with ronna (R, 10^27) and quetta (Q, 10^30) decimal units, binary RiB/QiB, and GNU single-letter R/Q suffixes. Values beyond the YB range should now use RB/QB (RiB/QiB, R/Q).
[tool_use Bash] {"command": "cat src/humanize/filesize.py; echo ---; grep -n \"YB\\|YiB\\|yotta\\|Y\\b\" tests/test_filesize.py | head -50; echo ---; grep -rn \"YB\\|YiB\" docs/ README* src/humanize/__init__.py 2>/dev/null | head", "description": "Read filesize module and related tests/docs"}
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
…[1361 chars elided]…
 gnu:
        return "%d Bytes" % bytes_

    if abs_bytes < base and gnu:
        return "%dB" % bytes_

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)

        if abs_bytes < unit:
            break

    ret: str = format % (base * bytes_ / unit) + s
    return ret
---
26:        ([10**26 * 30, False, True], "2481.5Y"),
27:        ([10**26 * 30, True], "2481.5 YiB"),
28:        ([10**26 * 30], "3000.0 YB"),
33:        ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
---
[tool_use Bash] {"command": "cat tests/test_filesize.py; echo ---; grep -n -i \"naturalsize\\|filesize\\|YB\\|YiB\\|kB\" README.md docs/*.md | head -30; echo ---; grep -n \"YB\\|YiB\\|Y\\b\" src/humanize/number.py | head", "description": "Read filesize tests, README and docs references"}
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
     
…[585 chars elided]…
r) -> None:
    assert humanize.naturalsize(*test_args) == expected

    args_with_negative = test_args
    args_with_negative[0] *= -1
    assert humanize.naturalsize(*args_with_negative) == "-" + expected
---
docs/filesize.md:1:# Filesize
docs/filesize.md:3:::: humanize.filesize
README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
docs/index.md:7:- [Filesize](filesize.md)
---
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZ
…[77 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py has been updated successfully.
[assistant] Now I'll check the new outputs for the boundary, in-range, and overflow values before I write any expectations.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -I -c \"\nfrom humanize import naturalsize as n\ncases=[(10**27,False,False),(10**30,False,False),(2*10**30,False,False),(10**33,False,False),(10**28,False,False),(10**26*30,False,False),(10**26*30,True,False),(10**26*30,False,True),\n(1024**9,True,False),(1024**10,True,False),(10**33,True,False),(1024**9,False,True),(1024**10,False,True),(10**33,False,True),(10**27,False,True),(10**26*30,False,True,'%.3f'),(10**26*30,True,False,'%.3f'),(10**24,False,True),(10**24,True,False),(-10**27,False,False),(10**27-1,False,False)]\nfor c in cases: print(c, repr(n(*c)))\n\"", "description": "Compute new naturalsize outputs for boundary cases"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nfrom humanize import naturalsize as n\ncases=[(10**27,False,False),(10**30,False,False),(2*10**30,False,False),(10**33,False,False),(10**28,False,False),(10**26*30,False,False),(10**26*30,True,False),(10**26*30,False,True),\n(1024**9,True,False),(1024**10,True,False),(10**33,True,False),(1024**9,False,True),(1024**10,False,True),(10**33,False,True),(10**27,False,True),(10**26*30,False,True,'%.3f'),(10**26*30,True,False,'%.3f'),(10**24,False,True),(10**24,True,False),(-10**27,False,False),(10**27-1,False,False)]\nfor c in cases: print(c, repr(n(*c)))\n\"", "description": "Compute new naturalsize outputs for boundary cases"}
[tool_result] (1000000000000000000000000000, False, False) '1.0 RB'
(1000000000000000000000000000000, False, False) '1.0 QB'
(2000000000000000000000000000000, False, False) '2.0 QB'
(1000000000000000000000000000000000, False, False) '1000.0 QB'
(10000000000000000000000000000, False, False) '10.0 RB'
(3000000000000000000000000000, False, False) '3.0 RB'
(3000000000000000000000000000, True, False) '2.4 RiB'
(3000000000000000000000000000, False, True) '2.4R'
(1237940039285380274899124224, True, False) '1.0 RiB'

…[172 chars elided]…
267650600228229401496703205376, False, True) '1.0Q'
(1000000000000000000000000000000000, False, True) '788.9Q'
(1000000000000000000000000000, False, True) '827.2Y'
(3000000000000000000000000000, False, True, '%.3f') '2.423R'
(3000000000000000000000000000, True, False, '%.3f') '2.423 RiB'
(1000000000000000000000000, False, True) '847.0Z'
(1000000000000000000000000, True, False) '847.0 ZiB'
(-1000000000000000000000000000, False, False) '-1.0 RB'
(999999999999999999999999999, False, False) '1.0 RB'
[assistant] The new outputs match the spec: RB/QB for decimal, RiB/QiB for binary, and R/Q for GNU, with overflow past QB/QiB/Q. Next I'll update the four existing rows whose expectations moved (same inputs, new unit) and add boundary, just-inside, and overflow rows for each new unit and mode.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),\n        ([1, False, False], \"1 Byte\"),\n        ([3141592, False, False,
…[998 chars elided]…
024**10, True, False], \"1.0 QiB\"),\n        ([1023 * 1024**10, True, False], \"1023.0 QiB\"),\n        ([1024**11, True, False], \"1024.0 QiB\"),\n        ([1024**9, False, True], \"1.0R\"),\n        ([1023 * 1024**9, False, True], \"1023.0R\"),\n        ([1024**10, False, True], \"1.0Q\"),\n        ([1023 * 1024**10, False, True], \"1023.0Q\"),\n        ([1024**11, False, True], \"1024.0Q\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/tests/test_filesize.py has been updated successfully.
[assistant] Now the docstring example that showed the old YB output for 10**28.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -c \"\nimport sys,pytest\nsys.exit(pytest.main(['-q','-p','no:cacheprovider','--color=no','tests/test_filesize.py']))\" ; echo \"== doctest\"; PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -3; echo \"== full\"; PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"== lint\"; git diff --stat", "description": "Run filesize tests, doctests, and full suite"}
[tool_result] ...................................                                      [100%]
35 passed in 0.01s
== doctest
.                                                                        [100%]
1 passed in 0.01s
== full
........................................................................ [ 98%]
...........                                                              [100%]
564 passed, 23 skipped in 0.49s
== lint
 src/humanize/filesize.py | 30 ++++++++++++++++++++++++++----
 tests/test_filesize.py   | 23 +++++++++++++++++++----
 2 files changed, 45 insertions(+), 8 deletions(-)
[assistant] `humanize.naturalsize()` now supports ronna and quetta. Values past the YB range are expressed in RB/QB, RiB/QiB, or R/Q. The full suite passes (564 passed, 23 skipped), and the filesize doctest passes with `--doctest-modules`. The changes are uncommitted.

- **`src/humanize/filesize.py`**: appended `RB`, `QB`, `RiB`, `QiB` to the decimal and binary tables, and `RQ` to the GNU string. All three tables still have 10 entries in the same order.
- **Docstring**: `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.
- **`tests/test_filesize.py`**:
  - Four existing rows use the sam
…[259 chars elided]…
 so I changed them. Please confirm that reading.
  - Added rows for each new unit in each mode: the exact boundary, a value just inside it, and overflow past the new top unit (`10**33` → `1000.0 QB`, `1024**11` → `1024.0 QiB` / `1024.0Q`).
- **README**: unchanged, since its examples are all in MB or smaller.
- **`number.metric()`**: untouched, as the skill notes it has its own separate prefix list.

Decision for you: the input `10**27 - 1` rounds to `1.0 RB`, not `1000.0 YB`. That is because `float()` conversion rounds it to exactly `1e27`. This predates my change and is not something I fixed.
