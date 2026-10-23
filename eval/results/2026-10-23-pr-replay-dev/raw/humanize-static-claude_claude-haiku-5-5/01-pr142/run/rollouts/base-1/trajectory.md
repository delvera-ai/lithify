# trajectory base-1

final message:
`naturalsize()` now supports ronna and quetta in decimal (RB, QB), binary (RiB, QiB) and GNU (R, Q) forms. The full suite passes (558 passed, 23 skipped), including the doctests.

**Changes**
- `src/humanize/filesize.py`: added `RB`/`QB` to the decimal table, `RiB`/`QiB` to the binary table, and `RQ` to the GNU string (`"KMGTPEZYRQ"`). The docstring example `naturalsize(10**28)` now returns `'10.0 RB'` instead of `'10000.0 YB'`.
- `tests/test_filesize.py`: added cases for RB, QB, RiB, QiB, R and Q, including values past Q that stay in Q.

**Existing test expectations I changed.** Four assertions encoded the old YB/YiB/Y output for 3×10²⁷. That value now falls in the ronna range, so the output is different by design:
- `"3000.0 YB"` → `"3.0 RB"`
- `"2481.5 YiB"` → `"2.4 RiB"`
- `"2481.5Y"` → `"2.4R"`
- `"2481.542 YiB"` → `"2.423 RiB"`

These follow directly from your request, but the project's CLAUDE.md says not to edit existing tests to make them pass. I treated these as spec changes rather than weakened checks, so please confirm you're happy with them.

**Not done**
- I haven't committed anything.
- Ruff and mypy aren't installed in the project venv, so I didn't run lint or type checks.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"naturalsize\\|yottabyte\\|YB\\|YiB\" --include=*.py --include=*.md --include=*.rst . | grep -v \"\\.git/\" | head -50", "description": "Locate naturalsize implementation and references"}
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
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"naturalsize\\|yottabyte\\|YiB\" . --exclude-dir=.git | head -60; cat AGENTS.md | head -80", "description": "Search repo for naturalsize references and read AGENTS.md"}
[tool_result] README.md:157:>>> humanize.naturalsize(1_000_000)
README.md:159:>>> humanize.naturalsize(1_000_000, binary=True)
README.md:161:>>> humanize.naturalsize(1_000_000, gnu=True)
tests/test_filesize.py:27:        ([10**26 * 30, True], "2481.5 YiB"),
tests/test_filesize.py:33:        ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
tests/test_filesize.py:36:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:37:    assert humanize.naturalsiz
…[1220 chars elided]…
only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py"}
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
[tool_use Bash] {"command": "grep -n \"doctest\" pyproject.toml tox.ini; ls <work>/env-humanize/bin/python 2>&1; git log --oneline -1 -- src/humanize/filesize.py; grep -rn \"YB\\|yotta\\|zetta\" docs | head", "description": "Check doctest config, venv, and docs mentions of units"}
[tool_result] tox.ini:51:addopts = --color=yes --doctest-modules
<work>/env-humanize/bin/python
4a37bd1 [pre-commit.ci] auto fixes from pre-commit.com hooks
[assistant] Doctests run under pytest, so the docstring example needs updating too. Making the edits to the suffix tables and docstring first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py", "old_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\"),\n    \"gnu\": \"KMGTPEZY\",", "new_string": "    \"decimal\": (\" kB\", \" MB\", \" GB\", \" TB\", \" PB\", \" EB\", \" ZB\", \" YB\", \" RB\", \" QB\"),\n    \"binary\": (\" KiB\", \" MiB\", \" GiB\", \" TiB\", \" PiB\", \" EiB\", \" ZiB\", \" YiB\", \" RiB\", \" QiB\"),\n    \"gnu\": \"KMGTPEZYRQ\","}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py", "old_string": "        >>> naturalsize(10**28)\n        '10000.0 YB'", "new_string": "        >>> naturalsize(10**28)\n        '10.0 RB'"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/src/humanize/filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll run the suite to see which existing expectations shift, and check the actual outputs before touching any test.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize as h\nfor a in [(10**26*30,), (10**26*30,True), (10**26*30,True,False,'%.3f'), (10**26*30,False,True), (10**30,), (10**30,True), (10**30,False,True), (10**27,), (10**27,True), (10**27,False,True), (-3*10**27,)]:\n    print(a, repr(h.naturalsize(*a)))\n\"", "description": "Run test suite and print new outputs for large values"}
[tool_result]     @pytest.mark.parametrize(
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
            ([3000, False, True], "2.9K"),
            ([3000000, False, True], "2.9M"
…[1281 chars elided]…

(3000000000000000000000000000, True) '2.4 RiB'
(3000000000000000000000000000, True, False, '%.3f') '2.423 RiB'
(3000000000000000000000000000, False, True) '2.4R'
(1000000000000000000000000000000,) '1.0 QB'
(1000000000000000000000000000000, True) '807.8 RiB'
(1000000000000000000000000000000, False, True) '807.8R'
(1000000000000000000000000000,) '1.0 RB'
(1000000000000000000000000000, True) '827.2 YiB'
(1000000000000000000000000000, False, True) '827.2Y'
(-3000000000000000000000000000,) '-3.0 RB'
[assistant] The four failures are all the 3×10²⁷ input, which the new spec moves out of the YB/YiB/Y range into RB/RiB/R. The new outputs match the spec, so I'm updating those four expectations and adding coverage for the new units.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, False, True], \"2481.5Y\"),\n        ([10**26 * 30, True], \"2481.5 YiB\"),\n        ([10**26 * 30], \"3000.0 YB\"),", "new_string": "        ([10**26 * 30, False, True], \"2.4R\"),\n        
…[53 chars elided]…
 * 30], \"3.0 RB\"),\n        ([10**26 * 10**3], \"1.0 RB\"),\n        ([10**26 * 10**3, False, True], \"1.0R\"),\n        ([10**26 * 10**3, True], \"827.2 YiB\"),\n        ([10**30], \"1.0 QB\"),\n        ([10**33], \"1000.0 QB\"),\n        ([2**90, True], \"1.0 RiB\"),\n        ([2**90, False, True], \"1.0R\"),\n        ([2**100, True], \"1.0 QiB\"),\n        ([2**100, False, True], \"1.0Q\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py", "old_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2481.542 YiB\"),", "new_string": "        ([10**26 * 30, True, False, \"%.3f\"], \"2.423 RiB\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] I typed `10**26 * 10**3` (1e29) where I meant 1e27 for the boundary cases. Correcting those three lines and then checking every expectation against the actual code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py", "old_string": "        ([10**26 * 10**3], \"1.0 RB\"),\n        ([10**26 * 10**3, False, True], \"1.0R\"),\n        ([10**26 * 10**3, True], \"827.2 YiB\"),", "new_string": "        ([10**27], \"1.0 RB\"),\n        ([10**27, True], \"827.2 YiB\"),\n        ([10**27, False, True], \"827.2Y\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-74aaec9fc419/20261023-133822-extend-humanize-naturalsize-to-s/base-1/tests/test_filesize.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no --doctest-modules src/humanize/filesize.py 2>&1 | tail -2; PYTHONPATH=src $PY -m ruff check src tests 2>&1 | tail -2; PYTHONPATH=src $PY -m mypy src 2>&1 | tail -1", "description": "Run full tests, doctests, and lint checks"}
[tool_result] ........................................................................ [ 74%]
........................................................................ [ 86%]
........................................................................ [ 99%]
.....                                                                    [100%]
558 passed, 23 skipped in 0.52s
.                                                                        [100%]
1 passed in 0.01s
<work>/env-humanize/bin/python: No module named ruff
<work>/env-humanize/bin/python: No module named mypy
[assistant] `naturalsize()` now supports ronna and quetta in decimal (RB, QB), binary (RiB, QiB) and GNU (R, Q) forms. The full suite passes (558 passed, 23 skipped), including the doctests.

**Changes**
- `src/humanize/filesize.py`: added `RB`/`QB` to the decimal table, `RiB`/`QiB` to the binary table, and `RQ` to the GNU string (`"KMGTPEZYRQ"`). The docstring example `naturalsize(10**28)` now returns `'10.0 RB'` instead of `'10000.0 YB'`.
- `tests/test_filesize.py`: added cases for RB, QB, RiB, QiB, R and Q, including values past Q that stay in Q.

**Existing test expectations I changed.** Four assertio
…[6 chars elided]…
oded the old YB/YiB/Y output for 3×10²⁷. That value now falls in the ronna range, so the output is different by design:
- `"3000.0 YB"` → `"3.0 RB"`
- `"2481.5 YiB"` → `"2.4 RiB"`
- `"2481.5Y"` → `"2.4R"`
- `"2481.542 YiB"` → `"2.423 RiB"`

These follow directly from your request, but the project's CLAUDE.md says not to edit existing tests to make them pass. I treated these as spec changes rather than weakened checks, so please confirm you're happy with them.

**Not done**
- I haven't committed anything.
- Ruff and mypy aren't installed in the project venv, so I didn't run lint or type checks.
