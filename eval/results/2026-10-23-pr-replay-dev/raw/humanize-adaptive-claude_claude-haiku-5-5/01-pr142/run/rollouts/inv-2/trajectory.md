# trajectory inv-2

final message:
`humanize.naturalsize()` now supports R (ronna, 10^27) and Q (quetta, 10^30) in decimal, binary and GNU modes. Values beyond the yottabyte range now come out as RB/QB, RiB/QiB, or R/Q. The full suite passes: 555 passed, 23 skipped, up from 549 passed at baseline. The filesize doctests pass too. I haven't committed anything.

The change is in `src/humanize/filesize.py`:
- Decimal suffixes gain ` RB` and ` QB`, binary gain ` RiB` and ` QiB`, and the GNU string is now `KMGTPEZYRQ`.
- The docstring example `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.

In `tests/test_filesize.py` I changed four expected values, all for the `10**26 * 30` inputs that now fall in the new range, which is the change the task asks for:
- `"2481.5Y"` → `"2.4R"`
- `"2481.5 YiB"` → `"2.4 RiB"`
- `"3000.0 YB"` → `"3.0 RB"`
- `"2481.542 YiB"` → `"2.423 RiB"`

The inputs and the number of cases are unchanged. I also added a separate parametrized test, `test_naturalsize_ronna_quetta`, covering RB, QB, RiB, QiB, R and Q at their boundaries. That is additive and touches no existing case.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"naturalsize\" --include='*.py' --include='*.rst' --include='*.md' . | head -50", "description": "Inspect repo and find naturalsize references"}
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
README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
tests/test_filesize.py:36:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:37:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:41
…[202 chars elided]…
ilesize.py:12:def naturalsize(
src/humanize/filesize.py:26:        >>> naturalsize(3000000)
src/humanize/filesize.py:28:        >>> naturalsize(300, False, True)
src/humanize/filesize.py:30:        >>> naturalsize(3000, False, True)
src/humanize/filesize.py:32:        >>> naturalsize(3000, False, True, "%.3f")
src/humanize/filesize.py:34:        >>> naturalsize(3000, True)
src/humanize/filesize.py:36:        >>> naturalsize(10**28)
src/humanize/filesize.py:38:        >>> naturalsize(-4096, True)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/src/humanize/filesize.py"}
[tool_result] 1	"""Bits and bytes related humanization."""
2	
3	from __future__ import annotations
4	
5	suffixes = {
6	    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"),
7	    "binary": (" KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"),
8	    "gnu": "KMGTPEZY",
9	}
10	
11	
12	def naturalsize(
13	    value: float | str,
14	    binary: bool = False,
15	    gnu: bool = False,
16	    format: str = "%.1f",
17	) -> str:
18	    """Format a number of bytes like a human readable fi
…[1385 chars elided]…
 bytes_ = float(value)
63	    abs_bytes = abs(bytes_)
64	
65	    if abs_bytes == 1 and not gnu:
66	        return "%d Byte" % bytes_
67	
68	    if abs_bytes < base and not gnu:
69	        return "%d Bytes" % bytes_
70	
71	    if abs_bytes < base and gnu:
72	        return "%dB" % bytes_
73	
74	    for i, s in enumerate(suffix):
75	        unit = base ** (i + 2)
76	
77	        if abs_bytes < unit:
78	            break
79	
80	    ret: str = format % (base * bytes_ / unit) + s
81	    return ret
82	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/tests/test_filesize.py"}
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
15	        ([3000], "3.0 kB"),
16	        ([3000000], "3.0 MB"),
17	        ([3000000000], "3.0 GB"),
18	        ([3000000000000], "3.0 TB"),
19	        ([300, True], "300 Bytes"),
20	        ([3000, True], "2.9 KiB"),
21	        ([3000000, True], "
…[409 chars elided]…
"3.14 MB"),
31	        ([3000, False, True, "%.3f"], "2.930K"),
32	        ([3000000000, False, True, "%.0f"], "3G"),
33	        ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
34	    ],
35	)
36	def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
37	    assert humanize.naturalsize(*test_args) == expected
38	
39	    args_with_negative = test_args
40	    args_with_negative[0] *= -1
41	    assert humanize.naturalsize(*args_with_negative) == "-" + expected
42	
[assistant] Baseline first, using the project's test command from CLAUDE.md.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ls -la $PY 2>&1; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; grep -rn \"YiB\\|YB\\|doctest\" --include='*.py' --include='*.md' --include='*.toml' --include='*.ini' . | grep -v \"^./src/humanize/filesize.py\" | head", "description": "Run baseline test suite and search for suffix docs"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
....................sssssssssssssssssssssss............................. [ 12%]
........................................................................ [ 25%]
...................................................
…[490 chars elided]…
yes --doctest-modules
tests/test_filesize.py:27:        ([10**26 * 30, True], "2481.5 YiB"),
tests/test_filesize.py:28:        ([10**26 * 30], "3000.0 YB"),
tests/test_filesize.py:33:        ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
src/humanize/filesize.py:6:    "decimal": (" kB", " MB", " GB", " TB", " PB", " EB", " ZB", " YB"),
src/humanize/filesize.py:7:    "binary": (" KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"),
src/humanize/filesize.py:37:        '10000.0 YB'
[assistant] Baseline is green (549 passed, 23 skipped). Now the source change: add the R and Q suffixes to all three tables, and update the docstring example.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZ
…[77 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll run the suite to see which existing expectations pin the old YB/YiB/Y output.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | grep -E \"FAILED|passed|failed\"; PYTHONPATH=src $PY -c \"\nimport humanize as h\nfor a in [(10**26*30,),(10**26*30,True),(10**26*30,True,False,'%.3f'),(10**26*30,False,True),(10**28,),(10**30,),(10**33,),(2**100,True),(10**30*3,False,True)]:\n    print(a, repr(h.naturalsize(*a)))\n\"", "description": "Run suite after change and print new outputs"}
[tool_result] FAILED tests/test_filesize.py::test_naturalsize[test_args12-2481.5Y] - Assert...
FAILED tests/test_filesize.py::test_naturalsize[test_args13-2481.5 YiB] - Ass...
FAILED tests/test_filesize.py::test_naturalsize[test_args14-3000.0 YB] - Asse...
FAILED tests/test_filesize.py::test_naturalsize[test_args19-2481.542 YiB] - A...
4 failed, 545 passed, 23 skipped in 0.53s
(3000000000000000000000000000,) '3.0 RB'
(3000000000000000000000000000, True) '2.4 RiB'
(3000000000000000000000000000, True, False, '%.3f') '2.423 RiB'
(3000000000000000000000000000, False, True) '2.4R'
(10000000000000000000000000000,) '10.0 RB'
(1000000000000000000000000000000,) '1.0 QB'
(1000000000000000000000000000000000,) '1000.0 QB'
(1267650600228229401496703205376, True) '1.0 QiB'
(3000000000000000000000000000000, False, True) '2.4Q'
[assistant] The four failures are exactly the `10**26 * 30` cases, which now fall in the RB/RiB/R range the task asks for. I'll update only those four expected values and leave their inputs and the case count unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),", "new_string": "        ([10**26 * 30, False, True], \"2.4R\"),\n        ([10**26 * 30, True], \"2.4 RiB\"),\n        ([10**26 * 30], \"3.0 RB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2481.542 YiB\"),\n    ],\n)\ndef test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:\n    assert humanize.naturalsize(*test_args) == exp
…[604 chars elided]…
      ([10**27], \"1.0 RB\"),\n        ([10**30], \"1.0 QB\"),\n        ([2**90, True], \"1.0 RiB\"),\n        ([2**100, True], \"1.0 QiB\"),\n        ([2**90, False, True], \"1.0R\"),\n        ([2**100, False, True], \"1.0Q\"),\n    ],\n)\ndef test_naturalsize_ronna_quetta(test_args: list[int] | list[int | bool], expected: str) -> None:\n    assert humanize.naturalsize(*test_args) == expected\n"}
[tool_result] The file ~/.cache/lithify/work/repo-84d744a165f5/20261023-133822-extend-humanize-naturalsize-to-s/inv-2/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"exit=$?\"; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -3; git diff --stat", "description": "Run full suite and filesize doctests"}
[tool_result] ........................................................................ [ 99%]
..                                                                       [100%]
555 passed, 23 skipped in 0.47s
exit=0
.                                                                        [100%]
1 passed in 0.01s
 src/humanize/filesize.py | 30 ++++++++++++++++++++++++++----
 tests/test_filesize.py   | 23 +++++++++++++++++++----
 2 files changed, 45 insertions(+), 8 deletions(-)
[assistant] `humanize.naturalsize()` now supports R (ronna, 10^27) and Q (quetta, 10^30) in decimal, binary and GNU modes. Values beyond the yottabyte range now come out as RB/QB, RiB/QiB, or R/Q. The full suite passes: 555 passed, 23 skipped, up from 549 passed at baseline. The filesize doctests pass too. I haven't committed anything.

The change is in `src/humanize/filesize.py`:
- Decimal suffixes gain ` RB` and ` QB`, binary gain ` RiB` and ` QiB`, and the GNU string is now `KMGTPEZYRQ`.
- The docstring example `naturalsize(10**28)` now shows `'10.0 RB'` instead of `'10000.0 YB'`.

In `tests/test_filesize.py` I changed four expected values, all for the `10**26 * 30` inputs that now fall in the new range, which is the change the task asks for:
- `"2481.5Y"` → `"2.4R"`
- `"2481.5 YiB"` → `"2.4 RiB"`
- `"3000.0 YB"` → `"3.0 RB"`
- `"2481.542 YiB"` → `"2.423 RiB"`

The inputs and the number of cases are unchanged. I also added a separate parametrized test, `test_naturalsize_ronna_quetta`, covering RB, QB, RiB, QiB, R and Q at their boundaries. That is additive and touches no existing case.
