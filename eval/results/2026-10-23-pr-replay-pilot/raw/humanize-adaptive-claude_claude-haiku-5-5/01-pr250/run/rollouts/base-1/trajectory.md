# trajectory base-1

final message:
Fixed. `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` when `gnu` is False, matching the output before 4.12.

**Cause:** In `src/humanize/filesize.py`, the one-byte branch returned `f"{bytes_} Byte"` without converting to int. A float `1.0` (or the string `"1"`, which is parsed to a float) printed as `"1.0 Byte"`. The sub-kilobyte branch was already using `int(bytes_)`, so only this branch was wrong.

**Change:**
- `src/humanize/filesize.py`: the one-byte branch now returns `f"{int(bytes_)} Byte"`.
- `tests/test_filesize.py`: added `([1.0, False, False], "1 Byte")` and `(["1", False, False], "1 Byte")` next to the existing `([1, False, False], "1 Byte")` case. No existing test was changed.

**Verification:** The project test command (with the scratchpad `env-humanize` Python) reports 607 passed, 24 skipped. Spot checks: `1.0` → `"1 Byte"`, `"1"` → `"1 Byte"`, `-1.0` → `"-1 Byte"`, and `gnu=True` still gives `"1B"`.

I haven't committed the change.

## events
[tool_use Bash] {"command": "git log --oneline -3 && ls && grep -n \"gnu\\|Byte\\|def naturalsize\" -n src/humanize/filesize.py | head -80", "description": "Inspect repo and naturalsize implementation"}
[tool_result] 2629e6b lithify: probe base
f23e5fb lithify init
3f797c2 eval setup at 8059ebe1732c
AGENTS.md
CLAUDE.md
LICENCE
README.md
RELEASING.md
docs
mkdocs.yml
pyproject.toml
requirements-mypy.txt
scripts
src
tests
tox.ini
30:    "gnu": "KMGTPEZYRQ",
34:def naturalsize(
37:    gnu: bool = False,
71:        gnu (bool): If `True`, the binary argument is ignored and GNU-style
78:    if gnu:
79:        suffix = suffixes["gnu"]
85:    base = 1024 if (gnu or binary) else 1000
93:    if abs_bytes == 1 and not gnu:
94:        return f"{bytes_} Byte"
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
[tool_use Bash] {"command": "sed -n 1,130p src/humanize/filesize.py && git log --oneline -5 -- src/humanize/filesize.py && grep -n \"Byte\\|1\\.0\\|naturalsize(1\" tests/test_i18n.py tests/test_filesize.py 2>/dev/null | head -40; ls tests; ls <work>/env-humanize/bin/python 2>&1", "description": "Read filesize module and related tests"}
[tool_result] """Bits and bytes related humanization."""

from __future__ import annotations

suffixes = {
    "decimal": (
        " kB",
        " MB",
        " GB",
        " TB",
        " PB",
        " EB",
        " ZB",
        " YB",
        " RB",
        " QB",
    ),
    "binary": (
        " KiB",
        " MiB",
        " GiB",
        " TiB",
        " PiB",
        " EiB",
        " ZiB",
        " YiB",
        " RiB",
        " QiB",
    ),
    "gnu": "KMGTPEZYRQ",
}


def naturalsize(
    
…[3145 chars elided]…
tests/test_filesize.py:37:        ([1024**1 * 31, True], "31.0 KiB"),
tests/test_filesize.py:70:        ([1024, False, True], "1.0K"),
tests/test_filesize.py:71:        ([1, False, False], "1 Byte"),
tests/test_filesize.py:76:        ([1.123456789], "1 Bytes"),
__init__.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "git show 11e62ee -- src/humanize/filesize.py tests/test_filesize.py && sed -n 60,80p tests/test_filesize.py", "description": "Show the commit that introduced the regression"}
[tool_result] commit 11e62eeedb8990298c3612af82376dc2344d24f8
Author: Hugo van Kemenade <1324225+hugovk@users.noreply.github.com>
Date:   Mon Feb 17 23:29:34 2025 +0200

    Fix regression in naturalsize for float

diff --git a/src/humanize/filesize.py b/src/humanize/filesize.py
index bdadd55..5650d02 100644
--- a/src/humanize/filesize.py
+++ b/src/humanize/filesize.py
@@ -94,7 +94,7 @@ def naturalsize(
         return f"{bytes_} Byte"
 
     if abs_bytes < base:
-        return f"{bytes_}B" if gnu else f"{by
…[1337 chars elided]…
1024, False, True], "1.0K"),
        ([1, False, False], "1 Byte"),
        ([3141592, False, False, "%.2f"], "3.14 MB"),
        ([3000, False, True, "%.3f"], "2.930K"),
        ([3000000000, False, True, "%.0f"], "3G"),
        ([10**26 * 30, True, False, "%.3f"], "2.423 RiB"),
        ([1.123456789], "1 Bytes"),
        ([1.123456789 * 10**3], "1.1 kB"),
        ([1.123456789 * 10**6], "1.1 MB"),
        ([1.123456789, False, True], "1B"),
        ([1.123456789 * 10**3, False, True], "1.1K"),
[assistant] The regression is in the `abs_bytes == 1` branch: it formats `bytes_` directly, so `1.0` prints as `"1.0 Byte"`, while the sub-kilobyte branch was already changed to use `int(bytes_)`. I'll apply the same int conversion there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nprint(repr(humanize.naturalsize(1.0)), repr(humanize.naturalsize('1')), repr(humanize.naturalsize(1)), repr(humanize.naturalsize(-1.0)), repr(humanize.naturalsize(1.0, gnu=True)))\" && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Check outputs and run project test suite"}
[tool_result] '1 Byte' '1 Byte' '1 Byte' '-1 Byte' '1B'
........................................................................ [ 68%]
........................................................................ [ 80%]
........................................................................ [ 91%]
.....................................................                    [100%]
605 passed, 24 skipped in 0.58s
[assistant] The fix works and the full suite passes. I'll add regression cases next to the existing `"1 Byte"` test so this stays covered.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py", "old_string": "        ([1, False, False], \"1 Byte\"),\n", "new_string": "        ([1, False, False], \"1 Byte\"),\n        ([1.0, False, False], \"1 Byte\"),\n        ([\"1\", False, False], \"1 Byte\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2 && git diff --stat", "description": "Rerun tests and show diff stat"}
[tool_result] .......................................................                  [100%]
607 passed, 24 skipped in 0.48s
 src/humanize/filesize.py | 2 +-
 tests/test_filesize.py   | 2 ++
 2 files changed, 3 insertions(+), 1 deletion(-)
[assistant] Fixed. `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` when `gnu` is False, matching the output before 4.12.

**Cause:** In `src/humanize/filesize.py`, the one-byte branch returned `f"{bytes_} Byte"` without converting to int. A float `1.0` (or the string `"1"`, which is parsed to a float) printed as `"1.0 Byte"`. The sub-kilobyte branch was already using `int(bytes_)`, so only this branch was wrong.

**Change:**
- `src/humanize/filesize.py`: the one-byte branch now returns `f"{int(bytes_)} Byte"`.
- `tests/test_filesize.py`: added `([1.0, False, False], "1 Byte")` and `(["1", False, False], "1 Byte")` next to the existing `([1, False, False], "1 Byte")` case. No existing test was changed.

**Verification:** The project test command (with the scratchpad `env-humanize` Python) reports 607 passed, 24 skipped. Spot checks: `1.0` → `"1 Byte"`, `"1"` → `"1 Byte"`, `-1.0` → `"-1 Byte"`, and `gnu=True` still gives `"1B"`.

I haven't committed the change.
