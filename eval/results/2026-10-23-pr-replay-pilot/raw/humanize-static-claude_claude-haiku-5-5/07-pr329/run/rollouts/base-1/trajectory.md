# trajectory base-1

final message:
`naturalsize()` now moves a value to the next unit when rounding reaches the base, so `naturalsize(999999)` returns `'1.0 MB'` and `naturalsize(1024**2 - 1, binary=True)` returns `'1.0 MiB'`. The full suite passes: 711 passed, 69 skipped, 0 failed.

**The fix** (`src/humanize/filesize.py`): after the exponent is picked, if the value formatted at that unit equals the base formatted the same way (e.g. `"1000.0"`), the exponent goes up by one. The check is skipped at the largest suffix (QB/QiB), so those values are unchanged. The input guards and the `abs_bytes == 1` / `< base` early returns are untouched. The comparison uses the absolute value, so negatives keep exactly one `-`.

**Tests** (`tests/test_filesize.py`): I added three positive cases to the existing `test_naturalsize` list, one each for decimal, binary and GNU. The test file also checks each one with a negated input. On the original code, all three fail (`1000.0 kB`, `1024.0 KiB`, `1024.0K`), and they pass with the fix.

**Choices to check:**
- I did not add a QB/QiB boundary case. Those outputs already behave correctly, so pinning them would only lock in existing behaviour, as the project's CLAUDE.md asks.
- The docstring examples don't show a boundary case, so I left them alone.
- The fix also covers GNU mode (`naturalsize(1024**2 - 1, gnu=True)` now returns `'1.0M'`). The original `'1024.0K'` was the same bug, so it's included.

I did not commit anything.

## events
[tool_use Bash] {"command": "git status --short && cat src/humanize/filesize.py && ls tests && ls <work>/env-humanize/bin/python 2>&1", "description": "Read naturalsize source and list tests"}
[tool_result] """Bits and bytes related humanization."""

from __future__ import annotations

from math import log

from humanize.i18n import _gettext as _

suffixes = {
    "decimal": (
        "kB",
        "MB",
        "GB",
        "TB",
        "PB",
        "EB",
        "ZB",
        "YB",
        "RB",
        "QB",
    ),
    "binary": (
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB",
        "EiB",
        "ZiB",
        "YiB",
        "RiB",
        "QiB",
    ),
    "gn
…[1673 chars elided]…
 return f"{int(bytes_)}B" if gnu else _("%d Bytes") % int(bytes_)

    exp = int(min(log(abs_bytes, base), len(suffix)))
    space = "" if gnu else " "
    ret: str = format % (bytes_ / (base**exp)) + space + _(suffix[exp - 1])
    return ret
__init__.py
test_benchmarks.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import naturalsize as n\nprint(repr(n(999999)), repr(n(1024**2-1, binary=True)), repr(n(999999, gnu=True)), repr(n(1023, gnu=True)), repr(n(1024**2-1, gnu=True)), repr(n(999.96)), repr(n(-999999)))\n\"; grep -n \"naturalsize\" -A3 tests/test_filesize.py | head -80", "description": "Reproduce bug on unmodified code and view tests"}
[tool_result] '1000.0 kB' '1024.0 KiB' '976.6K' '1023B' '1024.0K' '999 Bytes' '-1000.0 kB'
87:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
88:    assert humanize.naturalsize(*test_args) == expected
89-
90-    # Retest with negative input
91-    if isinstance(test_args[0], int):
--
96:    assert humanize.naturalsize(*test_args) == "-" + expected
[assistant] The bug reproduces, and GNU mode shows it too (`1024.0K`). Now the test parametrization.
[tool_use Bash] {"command": "sed -n 1,100p tests/test_filesize.py", "description": "View filesize test file"}
[tool_result] #!/usr/bin/env python

"""Tests for filesize humanizing."""

from __future__ import annotations

import pytest

import humanize


@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([300], "300 Bytes"),
        (["1000"], "1.0 kB"),
        ([10**3], "1.0 kB"),
        ([10**6], "1.0 MB"),
        ([10**9], "1.0 GB"),
        ([10**12], "1.0 TB"),
        ([10**15], "1.0 PB"),
        ([10**18], "1.0 EB"),
        ([10**21], "1.0 ZB"),
        ([10**24], "1.0 YB"),
        ([10**
…[2446 chars elided]…
56789, False, True], "1B"),
        ([1.123456789 * 10**3, False, True], "1.1K"),
        ([1.123456789 * 10**6, False, True], "1.1M"),
    ],
)
def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    # Retest with negative input
    if isinstance(test_args[0], int):
        test_args[0] *= -1
    else:
        test_args[0] = f"-{test_args[0]}"

    assert humanize.naturalsize(*test_args) == "-" + expected
[assistant] Reproduced on the unmodified code: decimal and binary show `1000.0 kB` / `1024.0 KiB`, and GNU shows `1024.0K`. The project's CLAUDE.md points at a `humanize-number-output` skill for this kind of change, so I'll load it before editing.
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-145531-bug-humanize-naturalsize-can-sho/base-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths
…[890 chars elided]…
t negated (`*-1` for ints, `"-"` prefixed for strings and floats). Only positive
   inputs belong there.
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[assistant] The skill's checklist fits this change: the fix goes after the existing guards, negatives must keep a single `-`, and the new cases go into the existing parametrize list. Applying the fix at the exponent computation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-145531-bug-humanize-naturalsize-can-sho/base-1/src/humanize/filesize.py", "old_string": "    exp = int(min(log(abs_bytes, base), len(suffix)))\n    space", "new_string": "    exp = int(min(log(abs_bytes, base), len(suffix)))\n    # Rounding can carry the value up to the next unit (999999 -> \"1000.0 kB\"),\n    # so move to that unit when the rounded value reaches the base.\n    if exp < len(suffix) and format % (abs_bytes / base**exp) == format % base:\n        exp += 1\n    space"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-145531-bug-humanize-naturalsize-can-sho/base-1/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-145531-bug-humanize-naturalsize-can-sho/base-1/tests/test_filesize.py", "old_string": "        ([1.123456789, False, True], \"1B\"),", "new_string": "        ([999999], \"1.0 MB\"),\n        ([1024**2 - 1, True], \"1.0 MiB\"),\n        ([1024**2 - 1, False, True], \"1.0M\"),\n        ([1.123456789, False, True], \"1B\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-145531-bug-humanize-naturalsize-can-sho/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import naturalsize as n\nfor a in [(999999,),(1024**2-1,True),(1024**2-1,False,True),(-999999,),(-(1024**2-1),True),(-(1024**2-1),False,True),(10**30*999.99,),(10**34*999,),(999.4,),(999.96,),(999999,False,True,'%d')]: print(a, repr(n(*a)))\n\"", "description": "Check fixed outputs for positive and negative inputs"}
[tool_result] (999999,) '1.0 MB'
(1048575, True) '1.0 MiB'
(1048575, False, True) '1.0M'
(-999999,) '-1.0 MB'
(-1048575, True) '-1.0 MiB'
(-1048575, False, True) '-1.0M'
(9.999900000000001e+32,) '1000.0 QB'
(9990000000000000000000000000000000000,) '9990000.0 QB'
(999.4,) '999 Bytes'
(999.96,) '999 Bytes'
(999999, False, True, '%d') '976K'
[assistant] Outputs look right, with one sign per negative. Now the full project check command.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git stash list >/dev/null; git show HEAD:src/humanize/filesize.py > /tmp/orig_filesize.py && cp src/humanize/filesize.py /tmp/new_filesize.py && cp /tmp/orig
…[73 chars elided]…
de-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_filesize.py 2>&1 | grep -E \"FAILED|passed|failed\" ; cp /tmp/new_filesize.py src/humanize/filesize.py && git diff --stat", "description": "Run full test suite, then confirm new cases fail on original code"}
[tool_result] Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
711 passed, 69 skipped in 7.07s
FAILED tests/test_filesize.py::test_naturalsize[test_args67-1.0 MB] - Asserti...
FAILED tests/test_filesize.py::test_naturalsize[test_args68-1.0 MiB] - Assert...
FAILED tests/test_filesize.py::test_naturalsize[test_args69-1.0M] - Assertion...
3 failed, 70 passed in 0.03s
 src/humanize/filesize.py | 4 ++++
 tests/test_filesize.py   | 3 +++
 2 files changed, 7 insertions(+)
[assistant] `naturalsize()` now moves a value to the next unit when rounding reaches the base, so `naturalsize(999999)` returns `'1.0 MB'` and `naturalsize(1024**2 - 1, binary=True)` returns `'1.0 MiB'`. The full suite passes: 711 passed, 69 skipped, 0 failed.

**The fix** (`src/humanize/filesize.py`): after the exponent is picked, if the value formatted at that unit equals the base formatted the same way (e.g. `"1000.0"`), the exponent goes up by one. The check is skipped at the largest suffix (QB/QiB), so those values are unchanged. The input guards and the `abs_bytes == 1` / `< base` early returns are 
…[241 chars elided]…
 file also checks each one with a negated input. On the original code, all three fail (`1000.0 kB`, `1024.0 KiB`, `1024.0K`), and they pass with the fix.

**Choices to check:**
- I did not add a QB/QiB boundary case. Those outputs already behave correctly, so pinning them would only lock in existing behaviour, as the project's CLAUDE.md asks.
- The docstring examples don't show a boundary case, so I left them alone.
- The fix also covers GNU mode (`naturalsize(1024**2 - 1, gnu=True)` now returns `'1.0M'`). The original `'1024.0K'` was the same bug, so it's included.

I did not commit anything.
