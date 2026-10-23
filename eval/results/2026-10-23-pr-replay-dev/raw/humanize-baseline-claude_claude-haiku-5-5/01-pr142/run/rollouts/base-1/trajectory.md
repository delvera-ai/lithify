# trajectory base-1

final message:
Ronna (R, 10²⁷) and quetta (Q, 10³⁰) are now supported for decimal, binary (RiB, QiB) and GNU-style sizes. Four existing test assertions fail, and I left them alone because they encode the old YB output that this change replaces.

**Failing existing assertions** (all in `tests/test_filesize.py`, values of 3×10²⁷ bytes):

| Input | Current expectation | New output |
|---|---|---|
| `10**26 * 30`, GNU | `2481.5Y` | `2.4R` |
| `10**26 * 30`, binary | `2481.5 YiB` | `2.4 RiB` |
| `10**26 * 30`, decimal | `3000.0 YB` | `3.0 RB` |
| `10**26 * 30`, binary, `%.3f` | `2481.542 YiB` | `2.423 RiB` |

Our project guardrail says not to edit existing tests to make them pass, so I haven't touched these. Updating them to the new values is the natural next step, but it needs your go-ahead.

**What changed**
- `src/humanize/filesize.py`: added `RB`/`QB`, `RiB`/`QiB` and GNU `R`/`Q` to the suffix tables. The lookup loop needed no change. The `naturalsize` docstring example for `10**28` now reads `'10.0 RB'`.
- `tests/test_filesize.py`: added a new parametrized test, `test_naturalsize_ronna_quetta`, covering 10 cases (decimal, binary, GNU, negatives, and values above Q). All pass.

**Test status:** 4 failed, 27 passed. The failures are the four assertions above; the 27 passes include the new cases and the doctests. I didn't commit anything.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"naturalsize\\|YB\\|yottabyte\" --include=*.py --include=*.md --include=*.rst . | grep -v \"^./.git/\" | head -50", "description": "Locate naturalsize implementation and references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"naturalsize\\|YB\\|yottabyte\" . --exclude-dir=.git | head -60", "description": "Locate naturalsize implementation and references"}
[tool_result] README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
tests/test_filesize.py:28:        ([10**26 * 30], "3000.0 YB"),
tests/test_filesize.py:36:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:37:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:41:    assert humanize.naturalsize(*args_with_
…[307 chars elided]…
/humanize/filesize.py:30:        >>> naturalsize(3000, False, True)
src/humanize/filesize.py:32:        >>> naturalsize(3000, False, True, "%.3f")
src/humanize/filesize.py:34:        >>> naturalsize(3000, True)
src/humanize/filesize.py:36:        >>> naturalsize(10**28)
src/humanize/filesize.py:37:        '10000.0 YB'
src/humanize/filesize.py:38:        >>> naturalsize(-4096, True)
src/humanize/__init__.py:5:from humanize.filesize import naturalsize
src/humanize/__init__.py:41:    "naturalsize",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/README.md", "offset": 145, "limit": 25}
[tool_result] 145	>>> humanize.naturaltime(delta)
146	'now'
147	>>> humanize.naturaltime(delta, minimum_unit="milliseconds")
148	'4 milliseconds ago'
149	>>> humanize.naturaltime(delta, minimum_unit="microseconds")
150	'4 milliseconds ago'
151	```
152	
153	### File size humanization
154	
155	```pycon
156	>>> import humanize
157	>>> humanize.naturalsize(1_000_000)
158	'1.0 MB'
159	>>> humanize.naturalsize(1_000_000, binary=True)
160	'976.6 KiB'
161	>>> humanize.naturalsize(1_000_000, gnu=True)
162	'976.6K'
163	```
164	
165	### Human-readable floating point numbers
166	
167	```pycon
168	>>> import humanize
169	>>> humanize.fractional(1/3)
[tool_use Bash] {"command": "grep -n \"doctest\\|addopts\" pyproject.toml setup.cfg tox.ini 2>/dev/null; ls <work>/env-humanize/bin/python 2>&1; PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider --color=no tests/test_filesize.py 2>&1 | tail -3", "description": "Check pytest config and baseline filesize tests"}
[tool_result] tox.ini:51:addopts = --color=yes --doctest-modules
pyproject.toml:101:addopts = "--color=yes"
<work>/env-humanize/bin/python
....................                                                     [100%]
20 passed in 0.02s
[assistant] Baseline is green (20 passed). The change itself is small: append the new suffixes to each tuple and extend the GNU letters. Making the edit now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPE
…[78 chars elided]…
n        \" GB\",\n        \" TB\",\n        \" PB\",\n        \" EB\",\n        \" ZB\",\n        \" YB\",\n        \" RB\",\n        \" QB\",\n    ),\n    \"binary\": (\n        \" KiB\",\n        \" MiB\",\n        \" GiB\",\n        \" TiB\",\n        \" PiB\",\n        \" EiB\",\n        \" ZiB\",\n        \" YiB\",\n        \" RiB\",\n        \" QiB\",\n    ),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py", "old_string": "            (`ls -sh` style) prefixes are used (K, M) with the 2**10 definition.", "new_string": "            (`ls -sh` style) prefixes are used (K, M, ..., R, Q) with the 2**10 definition."}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now the project's check command, to see exactly which existing assertions the new behaviour changes.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25; PYTHONPATH=src python3 -c \"\nimport humanize as h\nfor v,kw in [(10**27,{}),(10**30,{}),(10**33,{}),(3e27,{}),(10**27,{'binary':True}),(2**90,{'binary':True}),(2**100,{'binary':True}),(2**90,{'gnu':True}),(2**100,{'gnu':True}),(10**26*30,{'gnu':True}),(10**26*30,{'binary':True,'format':'%.3f'})]:\n    print(v,kw,h.naturalsize(v,**kw))\n\"", "description": "Run project checks and sample new suffix outputs"}
[tool_result]             ([1024, False, True], "1.0K"),
            ([10**26 * 30, False, True], "2481.5Y"),
            ([10**26 * 30, True], "2481.5 YiB"),
            ([10**26 * 30], "3000.0 YB"),
            ([1, False, False], "1 Byte"),
            ([3141592, False, False, "%.2f"], "3.14 MB"),
            ([3000, False, True, "%.3f"], "2.930K"),
            ([3000000000, False, True, "%.0f"], "3G"),
            ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
        ],
    )
    def test_naturals
…[770 chars elided]…
1.0 RB
1000000000000000000000000000000 {} 1.0 QB
1000000000000000000000000000000000 {} 1000.0 QB
3e+27 {} 3.0 RB
1000000000000000000000000000 {'binary': True} 827.2 YiB
1237940039285380274899124224 {'binary': True} 1.0 RiB
1267650600228229401496703205376 {'binary': True} 1.0 QiB
1237940039285380274899124224 {'gnu': True} 1.0R
1267650600228229401496703205376 {'gnu': True} 1.0Q
3000000000000000000000000000 {'gnu': True} 2.4R
3000000000000000000000000000 {'binary': True, 'format': '%.3f'} 2.423 RiB
[assistant] The four failures are exactly the existing assertions for 3×10²⁷ bytes, which the new spec moves from YB to RB. The project guardrail says not to edit existing tests to make them pass, so I'm leaving those four untouched. I'll add new cases for the new suffixes alongside them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py", "old_string": "def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:\n    assert humanize.naturalsize(*test_args) == expected\n\n    args_with_negative = test_args\n    args_with_negative[0] *= -1\
…[783 chars elided]…
alse, True], \"1.0R\"),\n        ([10**30 * 3, False, True, \"%.3f\"], \"2.910Q\"),\n    ],\n)\ndef test_naturalsize_ronna_quetta(test_args: list[int] | list[int | bool], expected: str) -> None:\n    assert humanize.naturalsize(*test_args) == expected\n\n    args_with_negative = test_args\n    args_with_negative[0] *= -1\n    assert humanize.naturalsize(*args_with_negative) == \"-\" + expected\n"}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] I guessed two expected values in that block; correcting them to the computed results (3×10²⁷ / 2⁹⁰ ≈ 2.42, 3×10³⁰ / 2¹⁰⁰ ≈ 2.367) and running the checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py", "old_string": "        ([10**27 * 3, False, True], \"1.0R\"),\n        ([10**30 * 3, False, True, \"%.3f\"], \"2.910Q\"),", "new_string": "        ([10**27 * 3, False, True], \"2.4R\"),\n        ([10**30 * 3, False, True, \"%.3f\"], \"2.367Q\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-646a82d8adbe/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_filesize.py src/humanize/filesize.py --doctest-modules 2>&1 | tail -8; git status --short", "description": "Run filesize tests and doctests, check git status"}
[tool_result] tests/test_filesize.py:37: AssertionError
=========================== short test summary info ============================
FAILED tests/test_filesize.py::test_naturalsize[test_args12-2481.5Y] - Assert...
FAILED tests/test_filesize.py::test_naturalsize[test_args13-2481.5 YiB] - Ass...
FAILED tests/test_filesize.py::test_naturalsize[test_args14-3000.0 YB] - Asse...
FAILED tests/test_filesize.py::test_naturalsize[test_args19-2481.542 YiB] - A...
4 failed, 27 passed in 0.03s
 M src/humanize/filesize.py
 M tests/test_filesize.py
[assistant] Ronna (R, 10²⁷) and quetta (Q, 10³⁰) are now supported for decimal, binary (RiB, QiB) and GNU-style sizes. Four existing test assertions fail, and I left them alone because they encode the old YB output that this change replaces.

**Failing existing assertions** (all in `tests/test_filesize.py`, values of 3×10²⁷ bytes):

| Input | Current expectation | New output |
|---|---|---|
| `10**26 * 30`, GNU | `2481.5Y` | `2.4R` |
| `10**26 * 30`, binary | `2481.5 YiB` | `2.4 RiB` |
| `10**26 * 30`, decimal | `3000.0 YB` | `3.0 RB` |
| `10**26 * 30`, binary, `%.3f` | `2481.542 YiB` | `2.423 RiB` |

Our
…[142 chars elided]…
al next step, but it needs your go-ahead.

**What changed**
- `src/humanize/filesize.py`: added `RB`/`QB`, `RiB`/`QiB` and GNU `R`/`Q` to the suffix tables. The lookup loop needed no change. The `naturalsize` docstring example for `10**28` now reads `'10.0 RB'`.
- `tests/test_filesize.py`: added a new parametrized test, `test_naturalsize_ronna_quetta`, covering 10 cases (decimal, binary, GNU, negatives, and values above Q). All pass.

**Test status:** 4 failed, 27 passed. The failures are the four assertions above; the 27 passes include the new cases and the doctests. I didn't commit anything.
