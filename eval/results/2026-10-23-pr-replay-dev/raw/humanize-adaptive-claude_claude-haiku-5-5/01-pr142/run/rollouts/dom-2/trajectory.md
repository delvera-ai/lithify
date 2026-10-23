# trajectory dom-2

final message:
Ronna (R, 10^27) and quetta (Q, 10^30) are now supported in `naturalsize()`, in decimal (RB/QB), binary (RiB/QiB) and GNU (R/Q) modes. The project's test command passes (555 passed, 23 skipped), and the filesize doctest passes when run on its own. I didn't commit anything.

**What changed**

- **`src/humanize/filesize.py`**: appended `RB`/`QB`, `RiB`/`QiB` and `R`/`Q` to the three suffix tables, so all three stay at 10 entries. The `naturalsize` docstring example `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.
- **`tests/test_filesize.py`**:
  - Changed the expected output of the three existing rows that pinned 3·10^27 bytes: `"2481.5Y"` → `"2.4R"`, `"2481.5 YiB"` → `"2.4 RiB"`, `"3000.0 YB"` → `"3.0 RB"`. I also changed `"2481.542 YiB"` → `"2.423 RiB"`. These are the only expected values I changed. No rows were removed or loosened.
  - Added rows for `10**27`, `10**28` (gnu), `10**30` (decimal, binary, gnu) and `10**33`.

**Verified values**

- 3·10^27 → `3.0 RB`, `2.4 RiB`, `2.4R`
- 10^28 → `10.0 RB`
- 10^30 → `1.0 QB`, `807.8 RiB`, `807.8R`
- 10^33 → `1000.0 QB`

Values from 10^27 up to 10^30 now show in RB rather than YB. This is the behaviour the task asked for.

**Not verified:** black and ruff aren't installed in the project's venv, so I couldn't run the formatter/linter check. I wrote the grown suffix tuples one item per line to match black's style. `README.md` is unchanged because its examples don't change output.

## events
[tool_use Skill] {"skill": "humanize-filesize-units"}
[tool_result] Launching skill: humanize-filesize-units
[user] Base directory for this skill: ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/.claude/skills/humanize-filesize-units

# naturalsize / filesize: maintainer facts

All of this lives in `src/humanize/filesize.py`; nothing else in `src/` reads `suffixes`
(`humanize/__init__.py` only re-exports `naturalsize`).

## INVARIANT: three parallel suffix tables
- `suffixes["decimal"]` (tuple, `" kB"`, `" MB"`, … leading space), `suffixes["binary"]`
  (tuple, `" KiB"`, …) and `suffixes["gnu"]` (a plain string of single letters, `"KMGTPEZY"`,
  no 
…[1464 chars elided]…
put. They
   are the existing spec for the old behaviour (see guardrails), so update them in place. The file has
   only this one table, so new cases fit as extra rows in it, where they get the negation check
   for free.
4. `README.md` "File size humanization" examples (1_000_000 only): touch them only if their
   output changes.

## Conventions
- Formatting is black plus ruff (`.pre-commit-config.yaml`). Black's line length is 88, so a
  suffix tuple that grows past it gets exploded one item per line.
- Size units are not translated: `naturalsize` uses no `_()`/gettext, so no `.po` changes.

[tool_use Bash] {"command": "cat src/humanize/filesize.py; git log --oneline -1; ls tests 2>/dev/null; grep -rn \"YB\\|yottabyte\\|naturalsize\" tests docs README* 2>/dev/null | head -60", "description": "Read filesize module and find related tests and docs"}
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
…[1773 chars elided]…
       ([10**26 * 30], "3000.0 YB"),
tests/test_filesize.py:36:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:37:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:41:    assert humanize.naturalsize(*args_with_negative) == "-" + expected
README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
[tool_use Bash] {"command": "cat tests/test_filesize.py; cat docs/filesize.md 2>/dev/null; echo ---; sed -n 150,170p README.md; echo ---; ls <work>/env-humanize/bin/python 2>&1", "description": "Read tests, docs, README section, and check env python"}
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
     
…[844 chars elided]…
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
[assistant] Now I'll extend the three suffix tables with the new prefixes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZ
…[77 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-humanize/bin/python; PYTHONPATH=src $P -I -c '\nimport humanize as h\nfor a,k in [(10**26*30,{}),(10**26*30,{\"binary\":True}),(10**26*30,{\"gnu\":True}),(10**26*30,{\"binary\":True,\"format\":\"%.3f\"}),(10**28,{}),(10**30,{}),(10**30,{\"binary\":True}),(10**33,{}),(10**28,{\"gnu\":True}),(10**27,{\"binary\":True}),(10**26*30,{\"gnu\":True,\"format\":\"%.0f\"})]:\n    print(a,k,repr(h.naturalsize(a,**k)))\n'", "description": "Check new outputs for boundary values"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
[tool_use Bash] {"command": "P=<work>/env-humanize/bin/python; PYTHONPATH=src $P -c '\nimport humanize as h\nfor a,k in [(10**26*30,{}),(10**26*30,{\"binary\":True}),(10**26*30,{\"gnu\":True}),(10**26*30,{\"binary\":True,\"format\":\"%.3f\"}),(10**28,{}),(10**30,{}),(10**30,{\"binary\":True}),(10**33,{}),(10**28,{\"gnu\":True}),(10**27,{\"binary\":True}),(10**26*30,{\"gnu\":True,\"format\":\"%.0f\"})]:\n    print(a,k,repr(h.naturalsize(a,**k)))\n'", "description": "Check new outputs for boundary values"}
[tool_result] 3000000000000000000000000000 {} '3.0 RB'
3000000000000000000000000000 {'binary': True} '2.4 RiB'
3000000000000000000000000000 {'gnu': True} '2.4R'
3000000000000000000000000000 {'binary': True, 'format': '%.3f'} '2.423 RiB'
10000000000000000000000000000 {} '10.0 RB'
1000000000000000000000000000000 {} '1.0 QB'
1000000000000000000000000000000 {'binary': True} '807.8 RiB'
1000000000000000000000000000000000 {} '1000.0 QB'
10000000000000000000000000000 {'gnu': True} '8.1R'
1000000000000000000000000000 {'binary': True} '827.2 YiB'
3000000000000000000000000000 {'gnu': True, 'format': '%.0f'} '2R'
[assistant] Outputs match the expected unit boundaries. Now I'll update the rows that pinned the old YB/YiB/Y output for 3·10^27 bytes, and add rows for the new units.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),", "new_string": "        ([10**26 * 30, False, True], \"2.4R\"),\n        ([10**26 * 30, True], \"2.4 RiB\"),\n        ([10**26 * 30], \"3.0 RB\"),\n        ([10**27], \"1.0 RB\"),\n        ([10**28, False, True], \"8.1R\"),\n        ([10**30], \"1.0 QB\"),\n        ([10**30, True], \"807.8 RiB\"),\n        ([10**30, False, True], \"807.8R\"),\n        ([10**33], \"1000.0 QB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2481.542 YiB\"),", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/dom-2/src/humanize/filesize.py has been updated successfully.
[assistant] Now the project's test command, the filesize doctests (which the default run doesn't collect), and the formatters.
[tool_use Bash] {"command": "P=<work>/env-humanize/bin/python; PYTHONPATH=src $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"--- doctest\"; PYTHONPATH=src $P -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -5; echo \"--- lint\"; $P -m black --check src/humanize/filesize.py tests/test_filesize.py 2>&1 | tail -3; $P -m ruff check src/humanize/filesize.py tests/test_filesize.py 2>&1 | tail -3; echo \"--- len\"; PYTHONPATH=src $P -c 'from humanize.filesize import suffixes as s; print(len(s[\"decimal\"]),len(s[\"binary\"]),len(s[\"gnu\"]))'", "description": "Run tests, doctests, linters, and check table lengths"}
[tool_result] ..........................sssssssssssssssssssssss....................... [ 12%]
........................................................................ [ 24%]
........................................................................ [ 37%]
........................................................................ [ 49%]
........................................................................ [ 62%]
........................................................................ [ 74%]
....................
…[242 chars elided]…
 in 0.46s
--- doctest
.                                                                        [100%]
1 passed in 0.01s
--- lint
<work>/env-humanize/bin/python: No module named black
<work>/env-humanize/bin/python: No module named ruff
--- len
10 10 10
[assistant] Ronna (R, 10^27) and quetta (Q, 10^30) are now supported in `naturalsize()`, in decimal (RB/QB), binary (RiB/QiB) and GNU (R/Q) modes. The project's test command passes (555 passed, 23 skipped), and the filesize doctest passes when run on its own. I didn't commit anything.

**What changed**

- **`src/humanize/filesize.py`**: appended `RB`/`QB`, `RiB`/`QiB` and `R`/`Q` to the three suffix tables, so all three stay at 10 entries. The `naturalsize` docstring example `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.
- **`tests/test_filesize.py`**:
  - Changed the expected outp
…[269 chars elided]…
 - Added rows for `10**27`, `10**28` (gnu), `10**30` (decimal, binary, gnu) and `10**33`.

**Verified values**

- 3·10^27 → `3.0 RB`, `2.4 RiB`, `2.4R`
- 10^28 → `10.0 RB`
- 10^30 → `1.0 QB`, `807.8 RiB`, `807.8R`
- 10^33 → `1000.0 QB`

Values from 10^27 up to 10^30 now show in RB rather than YB. This is the behaviour the task asked for.

**Not verified:** black and ruff aren't installed in the project's venv, so I couldn't run the formatter/linter check. I wrote the grown suffix tuples one item per line to match black's style. `README.md` is unchanged because its examples don't change output.
