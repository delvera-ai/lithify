# trajectory comp-1

final message:
`naturalsize` now returns `"1 Byte"` for `1.0` and `"1"` with `gnu=False`, as it did before 4.12. The full suite passes (610 passed, 24 skipped).

The cause was line 94 of `src/humanize/filesize.py`: the `== 1` branch formatted `bytes_` directly, so a float printed as `1.0`. It now uses `int(bytes_)`, matching the `< base` branch, which already did. The skill's invariant check (no bare `{bytes_}` in `filesize.py`) passes.

I also added cases to `test_naturalsize` in `tests/test_filesize.py`: `1`, `1.0`, `"1"`, `300`, `300.0` and `"300"`. Each is also checked with a leading `-` by the test's negation step.

Nothing else changed. I did not add a regression test that fails on the old code, and I did not run the docstring examples, which the project check doesn't execute. None of them cover sub-kilobyte output.

## events
[tool_use Skill] {"skill": "humanize-output-formatting"}
[tool_result] Launching skill: humanize-output-formatting
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/.claude/skills/humanize-output-formatting

# Changing humanize output: maintainer rules

## Where things live
- One module per concern in `src/humanize/`: `filesize.py` (`naturalsize`), `number.py`,
  `time.py`, `lists.py`, `i18n.py`. Tests mirror them: `tests/test_<module>.py`.
- Every hand-written module (all but generated `_version.py`) starts with `from __future__ import annotations` (ruff isort
  `required-imports`); docstrings use Google convention (
…[1487 chars elided]…
`float()` raises).
- Every new case's expected value must also be correct with a leading `-`.
- Float cases therefore also exercise the string-input path for their negative.

## Docstring examples are not run by the project check
`pyproject.toml` `[tool.pytest.ini_options]` (testpaths `tests`, no `--doctest-modules`) takes
precedence over tox.ini's `[pytest]`, so the `pycon` examples in `src/` are not executed.
If you change a function's output, update its docstring examples by hand so they match;
`docs/<module>.md` is just `::: humanize.<module>` (mkdocstrings), so the docstring is the docs.

[tool_use Bash] {"command": "git log --oneline -n 3 && git status --short && grep -n \"gnu\\|def naturalsize\\|Byte\\|float\\|str(\" src/humanize/filesize.py | head -80", "description": "Check repo state and locate naturalsize code"}
[tool_result] f791052 lithify: probe base
2bf3f71 lithify init
3f797c2 eval setup at 8059ebe1732c
30:    "gnu": "KMGTPEZYRQ",
34:def naturalsize(
35:    value: float | str,
37:    gnu: bool = False,
68:        value (int, float, str): Integer to convert.
71:        gnu (bool): If `True`, the binary argument is ignored and GNU-style
78:    if gnu:
79:        suffix = suffixes["gnu"]
85:    base = 1024 if (gnu or binary) else 1000
87:        bytes_ = float(value)
93:    if abs_bytes == 1 and not gnu:
94:        return f"{bytes_} Byte"
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
[assistant] The skill's invariant matches the bug: line 94 formats `bytes_` directly, so a float `1.0` prints as `1.0 Byte`. I'll read the function and the test file before editing.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/src/humanize/filesize.py"}
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
…[1744 chars elided]…

87	        bytes_ = float(value)
88	    else:
89	        bytes_ = value
90	
91	    abs_bytes = abs(bytes_)
92	
93	    if abs_bytes == 1 and not gnu:
94	        return f"{bytes_} Byte"
95	
96	    if abs_bytes < base:
97	        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
98	
99	    for i, s in enumerate(suffix, 2):
100	        unit = base**i
101	        if abs_bytes < unit:
102	            break
103	
104	    ret: str = format % (base * (bytes_ / unit)) + s
105	    return ret
106	
[tool_use Bash] {"command": "git show 4.11.0:src/humanize/filesize.py | sed -n '/def naturalsize/,/^def /p' | tail -40; echo ---; git log --oneline -- src/humanize/filesize.py | head -5; echo ---; grep -n \"Byte\\|B\\\"\" tests/test_filesize.py | head -40", "description": "Show pre-4.12 naturalsize and related test cases"}
[tool_result]     Args:
        value (int, float, str): Integer to convert.
        binary (bool): If `True`, uses binary suffixes (KiB, MiB) with base
            2<sup>10</sup> instead of 10<sup>3</sup>.
        gnu (bool): If `True`, the binary argument is ignored and GNU-style
            (`ls -sh` style) prefixes are used (K, M) with the 2**10 definition.
        format (str): Custom formatter.

    Returns:
        str: Human readable representation of a filesize.
    """
    if gnu:
        suffix = s
…[1972 chars elided]…
**7 * 37, True], "37.0 ZiB"),
44:        ([1024**8 * 38, True], "38.0 YiB"),
45:        ([1024**9 * 39, True], "39.0 RiB"),
46:        ([1024**10 * 40, True], "40.0 QiB"),
47:        ([1000**1 * 31, True], "30.3 KiB"),
48:        ([1000**2 * 32, True], "30.5 MiB"),
49:        ([1000**3 * 33, True], "30.7 GiB"),
50:        ([1000**4 * 34, True], "30.9 TiB"),
51:        ([1000**5 * 35, True], "31.1 PiB"),
52:        ([1000**6 * 36, True], "31.2 EiB"),
53:        ([1000**7 * 37, True], "31.3 ZiB"),
[assistant] The pre-4.12 code used `%d` in both sub-kilobyte branches. The `< base` branch already uses `int(bytes_)`, so the only defect is line 94, the `== 1` branch. I'll fix that and add test cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/tests/test_filesize.py", "limit": 16}
[tool_result] 1	#!/usr/bin/env python
2	
3	"""Tests for filesize humanizing."""
4	from __future__ import annotations
5	
6	import pytest
7	
8	import humanize
9	
10	
11	@pytest.mark.parametrize(
12	    "test_args, expected",
13	    [
14	        ([300], "300 Bytes"),
15	        (["1000"], "1.0 kB"),
16	        ([10**3], "1.0 kB"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/tests/test_filesize.py", "old_string": "        ([300], \"300 Bytes\"),\n        ([\"1000\"], \"1.0 kB\"),", "new_string": "        ([1], \"1 Byte\"),\n        ([1.0], \"1 Byte\"),\n        ([\"1\"], \"1 Byte\"),\n        ([300], \"300 Bytes\"),\n        ([300.0], \"300 Bytes\"),\n        ([\"300\"], \"300 Bytes\"),\n        ([\"1000\"], \"1.0 kB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/comp-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; PYTHONPATH=src <work>/env-humanize/bin/python -c 'import humanize as h; print(repr(h.naturalsize(1.0)), repr(h.naturalsize(\"1\")), repr(h.naturalsize(1.0, gnu=True)), repr(h.naturalsize(\"300\")))'", "description": "Run test suite and spot-check outputs"}
[tool_result] ........................................................................ [ 11%]
.sssssssssssssssssssssss......s......................................... [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 90%]
..........................................................               [100%]
610 passed, 24 skipped in 0.45s
---
'1 Byte' '1 Byte' '1B' '300 Bytes'
[tool_use Bash] {"command": "grep -n \"{bytes_}\" src/humanize/filesize.py; echo \"exit=$?\"; git diff --stat", "description": "Verify invariant grep and diff stats"}
[tool_result] exit=1
 src/humanize/filesize.py | 2 +-
 tests/test_filesize.py   | 5 +++++
 2 files changed, 6 insertions(+), 1 deletion(-)
[assistant] `naturalsize` now returns `"1 Byte"` for `1.0` and `"1"` with `gnu=False`, as it did before 4.12. The full suite passes (610 passed, 24 skipped).

The cause was line 94 of `src/humanize/filesize.py`: the `== 1` branch formatted `bytes_` directly, so a float printed as `1.0`. It now uses `int(bytes_)`, matching the `< base` branch, which already did. The skill's invariant check (no bare `{bytes_}` in `filesize.py`) passes.

I also added cases to `test_naturalsize` in `tests/test_filesize.py`: `1`, `1.0`, `"1"`, `300`, `300.0` and `"300"`. Each is also checked with a leading `-` by the test's negation step.

Nothing else changed. I did not add a regression test that fails on the old code, and I did not run the docstring examples, which the project check doesn't execute. None of them cover sub-kilobyte output.
