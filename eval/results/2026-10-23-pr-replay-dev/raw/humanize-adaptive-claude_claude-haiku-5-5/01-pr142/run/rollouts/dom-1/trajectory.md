# trajectory dom-1

final message:
`naturalsize()` now supports R/Q for decimal, binary and GNU sizes, and values above the yottabyte range come out as RB/QB, RiB/QiB or R/Q. The full test suite passes (556 passed, 23 skipped) and the `filesize.py` doctests pass.

**Changes**

- **`src/humanize/filesize.py`**: added `" RB"`, `" QB"`, `" RiB"`, `" QiB"` to the decimal and binary tables, and `"KMGTPEZYRQ"` to the GNU table. The tables stay aligned in length and order, and the letters match `metric()`'s prefix order.
- **Docstring**: `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`, and I added `naturalsize(10**31)` → `'10.0 QB'`.
- **`tests/test_filesize.py`**: I updated the expected strings of four existing rows whose inputs are above the YB range (inputs unchanged):
  - `10**26 * 30`, GNU: `"2481.5Y"` → `"2.4R"`
  - `10**26 * 30`, binary: `"2481.5 YiB"` → `"2.4 RiB"`
  - `10**26 * 30`, decimal: `"3000.0 YB"` → `"3.0 RB"`
  - `10**26 * 30`, binary, `%.3f`: `"2481.542 YiB"` → `"2.423 RiB"`

  I added rows for `10**28` and `10**31` in decimal, binary and GNU, plus `3 * 10**30` in GNU. The expected values come from running the implementation and match hand calculation.

**Checks I did not run:** `README.md` has no affected values (its examples use `1_000_000`). I did not touch `number.py`'s `metric()`, since the task is about `naturalsize` only.

## events
[tool_use Skill] {"skill": "humanize-output-change"}
[tool_result] Launching skill: humanize-output-change
[user] Base directory for this skill: ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/.claude/skills/humanize-output-change

# Changing the output of a humanize function

## Where things live (verified in the source)
- Public functions are implemented in `src/humanize/{filesize,number,time}.py` and re-exported
  from `src/humanize/__init__.py` (`__all__`). A new public name needs both.
- `docs/<module>.md` is only `::: humanize.<module>` (mkdocstrings): the docs render the
  docstring. Do not edit docs/*.md for an output change; edit the doc
…[2003 chars elided]…
e — all of these must agree
1. Implementation in `src/humanize/<module>.py`.
2. The docstring `>>>` examples of that function (update outputs that the change alters).
3. Existing rows in `tests/test_<module>.py` that the task's new behaviour supersedes (see the
   guardrail's scoped exception) plus new rows/test covering the new outputs, added to the
   existing parametrize style.
4. `README.md` examples, if any shows an affected value.
Confirm by listing every place an affected input appears (grep the input expressions in
`src/`, `tests/`, `README.md`) and checking each against the new rule.

[tool_use Bash] {"command": "cat src/humanize/filesize.py; ls tests; git log --oneline -1", "description": "Read filesize module and list tests"}
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
…[1245 chars elided]…
= abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return "%d Byte" % bytes_

    if abs_bytes < base and not gnu:
        return "%d Bytes" % bytes_

    if abs_bytes < base and gnu:
        return "%dB" % bytes_

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)

        if abs_bytes < unit:
            break

    ret: str = format % (base * bytes_ / unit) + s
    return ret
__init__.py
test_filesize.py
test_i18n.py
test_number.py
test_time.py
0002bb8 lithify: probe base
[tool_use Bash] {"command": "cat tests/test_filesize.py; grep -n -i \"YB\\|ZB\\|EiB\\|naturalsize\\|10\\*\\*2\\|kB\" README.md docs/*.md src/humanize/*.py | head -80", "description": "Show filesize tests and find affected references"}
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
     
…[1536 chars elided]…
ize.py:26:        >>> naturalsize(3000000)
src/humanize/filesize.py:28:        >>> naturalsize(300, False, True)
src/humanize/filesize.py:30:        >>> naturalsize(3000, False, True)
src/humanize/filesize.py:32:        >>> naturalsize(3000, False, True, "%.3f")
src/humanize/filesize.py:34:        >>> naturalsize(3000, True)
src/humanize/filesize.py:36:        >>> naturalsize(10**28)
src/humanize/filesize.py:37:        '10000.0 YB'
src/humanize/filesize.py:38:        >>> naturalsize(-4096, True)
[assistant] The skill's contract applies here: the suffix tables, the docstring example that currently overflows into YB, and the test rows that assert YB/YiB/Y output all change together. I'll edit the implementation first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZ
…[77 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'\n        >>> naturalsize(10**31)\n        '10.0 QB'"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/src/humanize/filesize.py has been updated successfully.
[assistant] Next, I'll compute the new outputs for the affected inputs before touching the tests, so the expected strings come from the implementation and not from my arithmetic.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -I -c \"\nimport humanize as h\nfor a in [(10**26*30,),(10**26*30,True),(10**26*30,False,True),(10**26*30,True,False,'%.3f'),(10**26*30,False,False),(10**28,),(10**31,),(10**28,True),(10**28,False,True),(10**31,True),(10**31,False,True),(3*10**24,),(3*10**27,True),(3*10**30,),(3*10**30,False,True)]:\n    print(a, repr(h.naturalsize(*a)))\n\"; PYTHONPATH=src python3 -I -m doctest -v src/humanize/filesize.py | tail -3", "description": "Compute new outputs for affected inputs and run doctests"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
8 tests in 2 items.
8 passed and 0 failed.
Test passed.
[assistant] The `-I` flag ignores `PYTHONPATH`, so the import failed. I'll rerun with the project's interpreter from the CLAUDE.md check command.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nimport humanize as h\nfor a in [(10**26*30,),(10**26*30,True),(10**26*30,False,True),(10**26*30,True,False,'%.3f'),(10**26*30,False,False),(10**28,),(10**31,),(10**28,True),(10**28,False,True),(10**31,True),(10**31,False,True),(3*10**24,),(3*10**27,True),(3*10**30,),(3*10**30,False,True)]:\n    print(a, repr(h.naturalsize(*a)))\n\"", "description": "Print new naturalsize outputs for affected inputs"}
[tool_result] (3000000000000000000000000000,) '3.0 RB'
(3000000000000000000000000000, True) '2.4 RiB'
(3000000000000000000000000000, False, True) '2.4R'
(3000000000000000000000000000, True, False, '%.3f') '2.423 RiB'
(3000000000000000000000000000, False, False) '3.0 RB'
(10000000000000000000000000000,) '10.0 RB'
(10000000000000000000000000000000,) '10.0 QB'
(10000000000000000000000000000, True) '8.1 RiB'
(10000000000000000000000000000, False, True) '8.1R'
(10000000000000000000000000000000, True) '7.9 QiB'
(10000000000000000000000000000000, False, True) '7.9Q'
(3000000000000000000000000,) '3.0 YB'
(3000000000000000000000000000, True) '2.4 RiB'
(3000000000000000000000000000000,) '3.0 QB'
(3000000000000000000000000000000, False, True) '2.4Q'
[assistant] The new outputs match my hand calculations. Now I'll update the four existing rows that assert the old YB/YiB/Y output (keeping their inputs) and add rows for the new units.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),\n        ([1, False, False], \"1 Byte\"),\n        ([3141592, False, False,
…[511 chars elided]…
 ([10**31, True], \"7.9 QiB\"),\n        ([10**31, False, True], \"7.9Q\"),\n        ([3 * 10**30, False, True], \"2.4Q\"),\n        ([1, False, False], \"1 Byte\"),\n        ([3141592, False, False, \"%.2f\"], \"3.14 MB\"),\n        ([3000, False, True, \"%.3f\"], \"2.930K\"),\n        ([3000000000, False, True, \"%.0f\"], \"3G\"),\n        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src $PY -m doctest src/humanize/filesize.py && echo DOCTEST_OK; git status --short", "description": "Run project test suite and filesize doctests"}
[tool_result] ...........................sssssssssssssssssssssss...................... [ 12%]
........................................................................ [ 24%]
........................................................................ [ 37%]
........................................................................ [ 49%]
........................................................................ [ 62%]
........................................................................ [ 74%]
........................................................................ [ 87%]
........................................................................ [ 99%]
...                                                                      [100%]
556 passed, 23 skipped in 0.48s
DOCTEST_OK
 M src/humanize/filesize.py
 M tests/test_filesize.py
[assistant] `naturalsize()` now supports R/Q for decimal, binary and GNU sizes, and values above the yottabyte range come out as RB/QB, RiB/QiB or R/Q. The full test suite passes (556 passed, 23 skipped) and the `filesize.py` doctests pass.

**Changes**

- **`src/humanize/filesize.py`**: added `" RB"`, `" QB"`, `" RiB"`, `" QiB"` to the decimal and binary tables, and `"KMGTPEZYRQ"` to the GNU table. The tables stay aligned in length and order, and the letters match `metric()`'s prefix order.
- **Docstring**: `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`, and I added `naturalsize(10
…[149 chars elided]…
s unchanged):
  - `10**26 * 30`, GNU: `"2481.5Y"` → `"2.4R"`
  - `10**26 * 30`, binary: `"2481.5 YiB"` → `"2.4 RiB"`
  - `10**26 * 30`, decimal: `"3000.0 YB"` → `"3.0 RB"`
  - `10**26 * 30`, binary, `%.3f`: `"2481.542 YiB"` → `"2.423 RiB"`

  I added rows for `10**28` and `10**31` in decimal, binary and GNU, plus `3 * 10**30` in GNU. The expected values come from running the implementation and match hand calculation.

**Checks I did not run:** `README.md` has no affected values (its examples use `1_000_000`). I did not touch `number.py`'s `metric()`, since the task is about `naturalsize` only.
