# trajectory dom-1

final message:
`naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again, matching 4.11.0. The full suite passes (610 passed, 24 skipped).

The bug was one line in `src/humanize/filesize.py`: the `abs_bytes == 1` branch rendered the raw float (`f"{bytes_} Byte"`). It now uses `int(bytes_)`, the same truncation that 4.11.0's `%d` did. The other sub-kilobyte branch already used `int()`, and no unwrapped `{bytes_}` remains in the file.

I added cases to `test_naturalsize` in `tests/test_filesize.py`: `1.0` and `"1"` give `"1 Byte"`, `1.0` with `gnu=True` gives `"1B"`, and `300.0` and `"300"` give `"300 Bytes"`. The existing negative re-run covers the sign path for each.

I didn't commit the change.

## events
[tool_use Skill] {"skill": "humanize-output-formatting"}
[tool_result] Launching skill: humanize-output-formatting
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/dom-1/.claude/skills/humanize-output-formatting

# Changing humanize output: maintainer rules

## Where things live
- One module per concern in `src/humanize/`: `filesize.py` (`naturalsize`), `number.py`,
  `time.py`, `lists.py`, `i18n.py`. Tests mirror them: `tests/test_<module>.py`.
- Every hand-written module (all but generated `_version.py`) starts with `from __future__ import annotations` (ruff isort
  `required-imports`); docstrings use Google convention (`
…[1348 chars elided]…
`float()` raises).
- Every new case's expected value must also be correct with a leading `-`.
- Float cases therefore also exercise the string-input path for their negative.

## Docstring examples are not run by the project check
`pyproject.toml` `[tool.pytest.ini_options]` (testpaths `tests`, no `--doctest-modules`) takes
precedence over tox.ini's `[pytest]`, so the `pycon` examples in `src/` are not executed.
If you change a function's output, update its docstring examples by hand so they match;
`docs/<module>.md` is just `::: humanize.<module>` (mkdocstrings), so the docstring is the docs.

[tool_use Bash] {"command": "git status --short && git log --oneline -3 && cat src/humanize/filesize.py", "description": "Check worktree status and read filesize module"}
[tool_result] ce19682 lithify: probe base
2bf3f71 lithify init
3f797c2 eval setup at 8059ebe1732c
"""Bits and bytes related humanization."""

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
     
…[1511 chars elided]…
e = 1024 if (gnu or binary) else 1000
    if isinstance(value, str):
        bytes_ = float(value)
    else:
        bytes_ = value

    abs_bytes = abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return f"{bytes_} Byte"

    if abs_bytes < base:
        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"

    for i, s in enumerate(suffix, 2):
        unit = base**i
        if abs_bytes < unit:
            break

    ret: str = format % (base * (bytes_ / unit)) + s
    return ret
[assistant] The skill's invariant matches the bug: the `abs_bytes == 1` branch renders the raw float `bytes_`. I'll compare against the 4.11.0 tag and check the existing tests before editing.
[tool_use Bash] {"command": "git tag --list | tail -5; echo ---; git show 4.11.0:src/humanize/filesize.py 2>/dev/null | sed -n '/abs_bytes = /,$p'; echo ---; grep -n \"Byte\\|bytes_}\" src/humanize/filesize.py; echo ---; sed -n 1,200p tests/test_filesize.py", "description": "Compare with 4.11.0 and inspect filesize tests"}
[tool_result] 4.5.0
4.6.0
4.7.0
4.8.0
4.9.0
---
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
---
94:        return f"{bytes_} Byte"
97:        return f"{int(bytes_)}B" if gnu else f"{int(bytes_)} Bytes"
-
…[2866 chars elided]…
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
[assistant] The 4.11.0 tag used `%d` (truncating), and `int(bytes_)` matches that. The `== 1` branch at `filesize.py:94` is the only place still rendering the raw float. I'll fix it and add cases for float and numeric-string inputs below one kilobyte.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/dom-1/src/humanize/filesize.py", "old_string": "        return f\"{bytes_} Byte\"", "new_string": "        return f\"{int(bytes_)} Byte\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/dom-1/src/humanize/filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/dom-1/tests/test_filesize.py", "old_string": "        ([1.123456789], \"1 Bytes\"),\n", "new_string": "        ([1.123456789], \"1 Bytes\"),\n        ([1.0], \"1 Byte\"),\n        ([\"1\"], \"1 Byte\"),\n        ([1.0, False, True], \"1B\"),\n        ([300.0], \"300 Bytes\"),\n        ([\"300\"], \"300 Bytes\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142110-regression-when-gnu-is-false-hum/dom-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "ls <work>/env-humanize/bin/python && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail 
…[47 chars elided]…
ers-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-humanize/bin/python -c \"import humanize as h; print(h.naturalsize(1.0), '|', h.naturalsize('1'), '|', h.naturalsize(-1.0), '|', h.naturalsize(0.5))\"; grep -n '{bytes_}' src/humanize/filesize.py; echo \"grep exit: $?\"", "description": "Run project test suite and verify the reported cases"}
[tool_result] <work>/env-humanize/bin/python
........................................................................ [ 11%]
.sssssssssssssssssssssss......s......................................... [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 90%]
..........................................................               [100%]
610 passed, 24 skipped in 0.65s
1 Byte | 1 Byte | -1 Byte | 0 Bytes
grep exit: 1
[assistant] `naturalsize(1.0)` and `naturalsize("1")` now return `"1 Byte"` again, matching 4.11.0. The full suite passes (610 passed, 24 skipped).

The bug was one line in `src/humanize/filesize.py`: the `abs_bytes == 1` branch rendered the raw float (`f"{bytes_} Byte"`). It now uses `int(bytes_)`, the same truncation that 4.11.0's `%d` did. The other sub-kilobyte branch already used `int()`, and no unwrapped `{bytes_}` remains in the file.

I added cases to `test_naturalsize` in `tests/test_filesize.py`: `1.0` and `"1"` give `"1 Byte"`, `1.0` with `gnu=True` gives `"1B"`, and `300.0` and `"300"` give `"300 Bytes"`. The existing negative re-run covers the sign path for each.

I didn't commit the change.
