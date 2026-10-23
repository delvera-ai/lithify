# trajectory base-2

final message:
Fixed. `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again, matching 4.11.

**Cause:** The 4.12 change in `fb61d5a` swapped `"%d Byte" % bytes_` for `f"{bytes_} Byte"`. The f-string formats the float directly, so `1.0` (and `"1"`, which parses to `1.0`) came out as `"1.0 Byte"`.

**Change:** In `src/humanize/filesize.py`, the 1-byte branch now uses `f"{int(bytes_)} Byte"`. That matches the `< base` branch right below it, which already uses `int(bytes_)`, and it reproduces the old `%d` truncation.

**Tests:** I added four cases to `tests/test_filesize.py`: `1.0` and `"1"`, each with and without the other arguments. No existing test was changed.

**Checks:** The suite passes with the project's command from CLAUDE.md: 609 passed, 24 skipped. Spot checks: `naturalsize(1.0)` → `'1 Byte'`, `naturalsize('1')` → `'1 Byte'`, `naturalsize(1.5)` → `'1 Bytes'`, `naturalsize(1.0, gnu=True)` → `'1B'`.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask me to.

## events
[tool_use Bash] {"command": "grep -n \"gnu\\|def naturalsize\" -A3 src/humanize/filesize.py | head -150", "description": "Locate naturalsize implementation"}
[tool_result] 30:    "gnu": "KMGTPEZYRQ",
31-}
32-
33-
34:def naturalsize(
35-    value: float | str,
36-    binary: bool = False,
37:    gnu: bool = False,
38-    format: str = "%.1f",
39-) -> str:
40-    """Format a number of bytes like a human-readable filesize (e.g. 10 kB).
--
71:        gnu (bool): If `True`, the binary argument is ignored and GNU-style
72-            (`ls -sh` style) prefixes are used (K, M) with the 2**10 definition.
73-        format (str): Custom formatter.
74-
--
78:    if gnu:
79:        suffix = suffixes["gnu"]
80-    elif binary:
81-        suffix = suffixes["binary"]
82-    else:
--
85:    base = 1024 if (gnu or binary) else 1000
86-    if isinstance(value, str):
87-        bytes_ = float(value)
88-    else:
--
93:    if abs_bytes == 1 and not gnu:
94-        return f"{bytes_} Byte"
95-
96-    if abs_bytes < base:
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
98-
99-    for i, s in enumerate(suffix, 2):
100-        unit = base**i
[tool_use Bash] {"command": "sed -n 76,115p src/humanize/filesize.py; git log --oneline -3 -- src/humanize/filesize.py; grep -n \"Byte\\|1)\" tests/test_i18n.py tests/test_filesize.py 2>/dev/null | head -40; ls tests", "description": "View naturalsize body, history, and tests"}
[tool_result]         str: Human readable representation of a filesize.
    """
    if gnu:
        suffix = suffixes["gnu"]
    elif binary:
        suffix = suffixes["binary"]
    else:
        suffix = suffixes["decimal"]

    base = 1024 if (gnu or binary) else 1000
    if isinstance(value, str):
        bytes_ = float(value)
    else:
        bytes_ = value

    abs_bytes = abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return f"{bytes_} Byte"

    if abs_bytes < base:
        return f"{int(byte
…[282 chars elided]…
 pre-commit (#226)
a178851 Fix overflow issue in naturalsize with np.int32 input
tests/test_i18n.py:50:        assert humanize.intcomma(1_234_567.8901) == "1.234.567,8901"
tests/test_filesize.py:14:        ([300], "300 Bytes"),
tests/test_filesize.py:36:        ([300, True], "300 Bytes"),
tests/test_filesize.py:71:        ([1, False, False], "1 Byte"),
tests/test_filesize.py:76:        ([1.123456789], "1 Bytes"),
__init__.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
[tool_use Bash] {"command": "git show 11e62ee -- src/humanize/filesize.py tests/test_filesize.py; sed -n 60,80p tests/test_filesize.py", "description": "Show the commit that changed the 1-byte branch"}
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
[tool_use Bash] {"command": "git tag --list | grep -E \"4\\.1[12]\" ; git log --oneline -S'Byte\"' -- src/humanize/filesize.py | head; git show $(git log -S'{bytes_} Byte' --format=%h -- src/humanize/filesize.py | tail -1) -- src/humanize/filesize.py | head -80", "description": "Find when the 1-byte branch was introduced"}
[tool_result] 4.11.0
4.12.0
4.12.1
4.12.2
4.12.3
5850014 Format with Black
commit fb61d5aae902e4526cd733a90d7a96ecded11b0e
Author: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>
Date:   Tue Jan 7 12:05:03 2025 +0200

    Update pre-commit (#226)
    
    Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>
    Co-authored-by: Hugo van Kemenade <1324225+hugovk@users.noreply.github.com>

diff --git a/src/humanize/filesize.py b/src/humanize/filesize.py
index 560754c..bdadd55 100644
--- a/src/humanize/filesize.py
+++ b/src/humanize/filesize.py
@@ -91,10 +91,10 @@ def naturalsize(
     abs_bytes = abs(bytes_)
 
     if abs_bytes == 1 and not gnu:
-        return "%d Byte" % bytes_
+        return f"{bytes_} Byte"
 
     if abs_bytes < base:
-        return ("%dB" if gnu else "%d Bytes") % bytes_
+        return f"{bytes_}B" if gnu else f"{bytes_} Bytes"
 
     for i, s in enumerate(suffix, 2):
         unit = base**i
[assistant] The 1-byte branch is the cause. Before 4.12 it used `"%d Byte" % bytes_`, which truncates to an int. The 4.12 change to `f"{bytes_} Byte"` formats the float directly, so `1.0` and `"1"` (parsed to `1.0`) render as `"1.0 Byte"`. The `< base` branch already uses `int(bytes_)`, so I'll make the 1-byte branch match it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-2/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-2/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-2/tests/test_filesize.py", "old_string": "        ([1, False, False], \"1 Byte\"),\n", "new_string": "        ([1, False, False], \"1 Byte\"),\n        ([1.0], \"1 Byte\"),\n        ([\"1\"], \"1 Byte\"),\n        ([1.0, False, False], \"1 Byte\"),\n        ([\"1\", False, False], \"1 Byte\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142110-regression-when-gnu-is-false-hum/base-2/tests/test_filesize.py has been updated successfully.
[assistant] Now I'll run the project's checks using the command from CLAUDE.md.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"import humanize as h; print(repr(h.naturalsize(1.0)), repr(h.naturalsize('1')), repr(h.naturalsize(1.5)), repr(h.naturalsize(1.0, gnu=True)))\"", "description": "Run test suite and check reported outputs"}
[tool_result] ........................................................................ [ 11%]
sssssssssssssssssssssss......s.......................................... [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 90%]
.........................................................                [100%]
609 passed, 24 skipped in 0.70s
'1 Byte' '1 Byte' '1 Bytes' '1B'
[assistant] Fixed. `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again, matching 4.11.

**Cause:** The 4.12 change in `fb61d5a` swapped `"%d Byte" % bytes_` for `f"{bytes_} Byte"`. The f-string formats the float directly, so `1.0` (and `"1"`, which parses to `1.0`) came out as `"1.0 Byte"`.

**Change:** In `src/humanize/filesize.py`, the 1-byte branch now uses `f"{int(bytes_)} Byte"`. That matches the `< base` branch right below it, which already uses `int(bytes_)`, and it reproduces the old `%d` truncation.

**Tests:** I added four cases to `tests/test_filesize.py`: `1.0` and `"1"`, each with and without the other arguments. No existing test was changed.

**Checks:** The suite passes with the project's command from CLAUDE.md: 609 passed, 24 skipped. Spot checks: `naturalsize(1.0)` → `'1 Byte'`, `naturalsize('1')` → `'1 Byte'`, `naturalsize(1.5)` → `'1 Bytes'`, `naturalsize(1.0, gnu=True)` → `'1B'`.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask me to.
