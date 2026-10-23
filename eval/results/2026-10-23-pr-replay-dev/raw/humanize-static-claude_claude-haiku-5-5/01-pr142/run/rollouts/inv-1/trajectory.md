# trajectory inv-1

final message:
`naturalsize()` now supports ronna (RB, 10^27), quetta (QB, 10^30), RiB/QiB, and the GNU `R`/`Q` suffixes. The full suite passes (556 passed, 23 skipped, up from 549 passed) and the module doctests pass.

**Changes**
- `src/humanize/filesize.py`: added `RB`/`QB` to the decimal table, `RiB`/`QiB` to the binary table, and `RQ` to the GNU string (`"KMGTPEZYRQ"`). The existing loop handles the new units without other changes. Values from 10^24 up to 10^27 still show as YB, and anything at or above 10^27 shows as RB.
- `tests/test_filesize.py`: added cases for `10**27` and `10**30` in decimal, `2**90` and `2**100` in binary, and `2**90` and `2**100` in GNU.

**Pre-existing assertions changed by the task (old → new)**

The task moves `10**26 * 30` (3·10^27 bytes) out of the YB range, so these assertions can't hold alongside it. I changed them rather than leaving the suite red:
- `([10**26 * 30], "3000.0 YB")` → `"3.0 RB"`
- `([10**26 * 30, False, True], "2481.5Y")` → `"2.4R"`
- `([10**26 * 30, True], "2481.5 YiB")` → `"2.4 RiB"`
- `([10**26 * 30, True, False, "%.3f"], "2481.542 YiB")` → `"2.423 RiB"`
- Docstring example `naturalsize(10**28)`: `'10000.0 YB'` → `'10.0 RB'`

**Notes**
- Lint and typecheck were not run. `ruff` and `mypy` aren't installed in the project venv, per the project notes.
- The suffix tuples are now written one entry per line, which is longer than the original single-line form. I did that to keep the lines short; say if you'd prefer the compact style.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"naturalsize\\|YB\\|yotta\" src tests docs README* CHANGELOG* 2>/dev/null | head -80", "description": "Inspect repo layout and naturalsize references"}
[tool_result] AGENTS.md
CLAUDE.md
LICENCE
README.md
RELEASING.md
docs
mkdocs.yml
pyproject.toml
scripts
src
tests
tox.ini
(eval):1: no matches found: CHANGELOG*
[tool_use Bash] {"command": "cat CLAUDE.md | head -5; grep -rln \"naturalsize\" . --exclude-dir=.git; grep -rn \"YB\\|yotta\\|ZB\" . --exclude-dir=.git | head -40", "description": "Locate naturalsize and yotta references"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

README.md
tests/test_filesize.py
src/humanize/__init__.py
src/humanize/filesize.py
tests/test_filesize.py:28:        ([10**26 * 30], "3000.0 YB"),
src/humanize/filesize.py:6:    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"),
src/humanize/filesize.py:37:        '10000.0 YB'
[tool_use Bash] {"command": "cat src/humanize/filesize.py; cat tests/test_filesize.py; grep -n -i \"naturalsize\\|YB\\|suffix\" -A3 README.md | head -80; cat CLAUDE.md | sed -n 5,200p | grep -v \"^$\" | head -80", "description": "Read filesize module, tests, and docs"}
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
…[4421 chars elided]…
or=no`.
### Tool guidance
- The shell is zsh: an unquoted glob in an argument aborts the whole command with `no matches found`. Quote patterns (`grep -rn PAT . --include='*.py' --exclude-dir=.git`) or use the Grep tool.
- `ruff` and `mypy` are not installed in the project venv (`python -m ruff` / `python -m mypy` fail with `No module named ...`). Do not install them; the test command in memory is the available check. Say in the final message that lint/typecheck were not run.
<!-- lithify:end -->
[assistant] The existing tests and one docstring example pin `10**26 * 30` and `10**28` to YB/YiB output, which this change will alter. I'll get a baseline run first, then check the new values.
[tool_use Bash] {"command": "VENV=<work>/env-humanize/bin/python; ls -la $VENV 2>&1; PYTHONPATH=src $VENV -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; PYTHONPATH=src $VENV -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -3", "description": "Run baseline test suite and doctests"}
[tool_result] lrwxr-xr-x@ 1 donovan  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
........................................................................ [ 88%]
....................................................................     [100%]
549 passed, 23 skipped in 0.55s
.                                                                        [100%]
1 passed in 0.01s
[assistant] Baseline is green (549 passed, 23 skipped). Now the change to the suffix tables:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZ
…[77 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize as h\nfor a in [([10**26*30]),([10**26*30,False,True]),([10**26*30,True]),([10**26*30,True,False,'%.3f']),([10**28]),([10**27]),([10**30]),([2**90,True]),([2**100,True]),([2**90,False,True]),([2**100,False,True]),([10**27,False,True]),([10**30,False,True]),([10**33])]:\n    print(a, repr(h.naturalsize(*a)))\n\"", "description": "Apply suffix change and print new outputs for key values"}
[tool_result] [3000000000000000000000000000] '3.0 RB'
[3000000000000000000000000000, False, True] '2.4R'
[3000000000000000000000000000, True] '2.4 RiB'
[3000000000000000000000000000, True, False, '%.3f'] '2.423 RiB'
[10000000000000000000000000000] '10.0 RB'
[1000000000000000000000000000] '1.0 RB'
[1000000000000000000000000000000] '1.0 QB'
[1237940039285380274899124224, True] '1.0 RiB'
[1267650600228229401496703205376, True] '1.0 QiB'
[1237940039285380274899124224, False, True] '1.0R'
[1267650600228229401496703205376, False, True] '1.0Q'
[1000000000000000000000000000, False, True] '827.2Y'
[1000000000000000000000000000000, False, True] '807.8R'
[1000000000000000000000000000000000] '1000.0 QB'
[assistant] The new outputs match the intended scheme. Four existing test assertions and one docstring example change because the task moves those values from YB/YiB/Y to RB/RiB/R. I'm updating them and adding cases for the new units.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),", "new_string": "        ([10**26 * 30, False, True], \"2.4R\"),\n        ([10**26 * 30, True], \"2.4 RiB\"),\n        ([10**26 * 30], \"3.0 RB\"),\n        ([10**27], \"1.0 RB\"),\n        ([10**30], \"1.0 QB\"),\n        ([2**90, True], \"1.0 RiB\"),\n        ([2**100, True], \"1.0 QiB\"),\n        ([10**27, False, True], \"827.2Y\"),\n        ([2**90, False, True], \"1.0R\"),\n        ([2**100, False, True], \"1.0Q\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2481.542 YiB\"),", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/tests/test_filesize.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/src/humanize/filesize.py", "old_string": "        '10000.0 YB'", "new_string": "        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/inv-1/src/humanize/filesize.py has been updated successfully.
[tool_use Bash] {"command": "VENV=<work>/env-humanize/bin/python; PYTHONPATH=src $VENV -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; PYTHONPATH=src $VENV -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -3; git diff --stat", "description": "Run full test suite, module doctests, and diff stat"}
[tool_result] ........................................................................ [ 99%]
...                                                                      [100%]
556 passed, 23 skipped in 0.49s
.                                                                        [100%]
1 passed in 0.01s
 src/humanize/filesize.py | 30 ++++++++++++++++++++++++++----
 tests/test_filesize.py   | 15 +++++++++++----
 2 files changed, 37 insertions(+), 8 deletions(-)
[assistant] `naturalsize()` now supports ronna (RB, 10^27), quetta (QB, 10^30), RiB/QiB, and the GNU `R`/`Q` suffixes. The full suite passes (556 passed, 23 skipped, up from 549 passed) and the module doctests pass.

**Changes**
- `src/humanize/filesize.py`: added `RB`/`QB` to the decimal table, `RiB`/`QiB` to the binary table, and `RQ` to the GNU string (`"KMGTPEZYRQ"`). The existing loop handles the new units without other changes. Values from 10^24 up to 10^27 still show as YB, and anything at or above 10^27 shows as RB.
- `tests/test_filesize.py`: added cases for `10**27` and `10**30` in decimal, `2**
…[291 chars elided]…
**26 * 30], "3000.0 YB")` → `"3.0 RB"`
- `([10**26 * 30, False, True], "2481.5Y")` → `"2.4R"`
- `([10**26 * 30, True], "2481.5 YiB")` → `"2.4 RiB"`
- `([10**26 * 30, True, False, "%.3f"], "2481.542 YiB")` → `"2.423 RiB"`
- Docstring example `naturalsize(10**28)`: `'10000.0 YB'` → `'10.0 RB'`

**Notes**
- Lint and typecheck were not run. `ruff` and `mypy` aren't installed in the project venv, per the project notes.
- The suffix tuples are now written one entry per line, which is longer than the original single-line form. I did that to keep the lines short; say if you'd prefer the compact style.
