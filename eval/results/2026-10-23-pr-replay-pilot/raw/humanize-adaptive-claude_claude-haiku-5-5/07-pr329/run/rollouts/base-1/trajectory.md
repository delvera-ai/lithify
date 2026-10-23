# trajectory base-1

final message:
`naturalsize()` now moves a value that rounds up to the base into the next unit. The full test suite passes (715 passed, 69 skipped).

The fix is in `src/humanize/filesize.py`. The suffix was chosen from `log()` before rounding, so `999999` formatted to `1000.0` and kept `kB`. The function now formats the value, and if the rounded number reaches the base and a larger suffix exists, it re-formats with the next one. The change covers decimal, binary and GNU. The largest suffix is left alone, so `10**33 - 1` still gives `1000.0 QB`.

I added regression cases to `tests/test_filesize.py`:
- `999999` → `1.0 MB`
- `999999999` with `%.0f` → `1 GB`
- `1024**2 - 1` binary → `1.0 MiB`, and `1024**3 - 1` binary → `1.0 GiB`
- The same two values in GNU mode → `1.0M` and `1.0G`
- The `QB` ceiling case

The negative-input retest in the existing test also covers these.

One thing to be aware of: the check calls `float()` on the formatted number. That works for the documented formats (`%.Nf`, `%d`), but a custom format that adds non-numeric text around the number would now raise `ValueError`. I did not find any such usage in the repo.

I have not committed anything.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"\" src/humanize/filesize.py | head -200", "description": "Check status and read filesize module"}
[tool_result] 1:"""Bits and bytes related humanization."""
2:
3:from __future__ import annotations
4:
5:from math import log
6:
7:from humanize.i18n import _gettext as _
8:
9:suffixes = {
10:    "decimal": (
11:        "kB",
12:        "MB",
13:        "GB",
14:        "TB",
15:        "PB",
16:        "EB",
17:        "ZB",
18:        "YB",
19:        "RB",
20:        "QB",
21:    ),
22:    "binary": (
23:        "KiB",
24:        "MiB",
25:        "GiB",
26:        "TiB",
27:        "PiB",
28:        "EiB",
…[1715 chars elided]…
8:
89:    base = 1024 if (gnu or binary) else 1000
90:    bytes_ = float(value)
91:    abs_bytes = abs(bytes_)
92:
93:    if abs_bytes == 1 and not gnu:
94:        return _("%d Byte") % int(bytes_)
95:
96:    if abs_bytes < base:
97:        return f"{int(bytes_)}B" if gnu else _("%d Bytes") % int(bytes_)
98:
99:    exp = int(min(log(abs_bytes, base), len(suffix)))
100:    space = "" if gnu else " "
101:    ret: str = format % (bytes_ / (base**exp)) + space + _(suffix[exp - 1])
102:    return ret
[tool_use Bash] {"command": "grep -rn \"naturalsize\" tests/ | head -60; ls; git log --oneline -3 -- src/humanize/filesize.py", "description": "Find naturalsize tests and history"}
[tool_result] tests/test_filesize.py:87:def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
tests/test_filesize.py:88:    assert humanize.naturalsize(*test_args) == expected
tests/test_filesize.py:96:    assert humanize.naturalsize(*test_args) == "-" + expected
tests/test_i18n.py:185:def test_naturalsize_i18n(locale: str, value: float, expected_result: str) -> None:
tests/test_i18n.py:191:        assert humanize.naturalsize(value) == expected_result
tests/test_i18n.py:196:def
…[117 chars elided]…
) == "2.9 Kio"
tests/test_benchmarks.py:64:def test_naturalsize(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:65:    benchmark(humanize.naturalsize, 1_234_567_890)
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
b172d67 Add i18n support for `naturalsize()` and French translation (#294)
bb99238 Optimize `naturalsize` algorithm by using `math.log` (#253)
a79fb3a 1.0 Byte should be displayed as 1 Byte
[tool_use Bash] {"command": "sed -n 1,100p tests/test_filesize.py; grep -n \"format\" tests/test_filesize.py | head; ls <work>/env-humanize/bin/python 2>&1", "description": "Read existing naturalsize tests"}
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
…[2601 chars elided]…
aturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
    assert humanize.naturalsize(*test_args) == expected

    # Retest with negative input
    if isinstance(test_args[0], int):
        test_args[0] *= -1
    else:
        test_args[0] = f"-{test_args[0]}"

    assert humanize.naturalsize(*test_args) == "-" + expected
<work>/env-humanize/bin/python
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142505-bug-humanize-naturalsize-can-sho/base-1/src/humanize/filesize.py", "old_string": "    exp = int(min(log(abs_bytes, base), len(suffix)))\n    space = \"\" if gnu else \" \"\n    ret: str = format % (bytes_ / (base**exp)) + space + _(suffix[exp - 1])\n    return ret", "new_string": "    exp = in
…[34 chars elided]…
ffix)))\n    num = format % (bytes_ / (base**exp))\n    # Rounding can push the value up to the base (e.g. 999999 -> \"1000.0\"),\n    # so show it with the next suffix instead.\n    if exp < len(suffix) and abs(float(num)) >= base:\n        exp += 1\n        num = format % (bytes_ / (base**exp))\n    space = \"\" if gnu else \" \"\n    ret: str = num + space + _(suffix[exp - 1])\n    return ret"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142505-bug-humanize-naturalsize-can-sho/base-1/src/humanize/filesize.py has been updated successfully.
[assistant] Now I'll add regression cases for each boundary (decimal, binary, GNU) and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142505-bug-humanize-naturalsize-can-sho/base-1/tests/test_filesize.py", "old_string": "        ([1.123456789, False, True], \"1B\"),", "new_string": "        ([999999], \"1.0 MB\"),\n        ([999999999, False, False, \"%.0f\"], \"1 GB\"),\n        ([1024**2 - 1, True], \"1.0 MiB\"),\n        ([1024**3 - 1, True], \"1.0 GiB\"),\n        ([1024**2 - 1, False, True], \"1.0M\"),\n        ([1024**3 - 1, False, True], \"1.0G\"),\n        ([10**30 * 1000 - 1], \"1000.0 QB\"),\n        ([1.123456789, False, True], \"1B\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142505-bug-humanize-naturalsize-can-sho/base-1/tests/test_filesize.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize as h\nprint(h.naturalsize(999999), h.naturalsize(1024**2-1, binary=True), h.naturalsize(1024**2-1, False, True), h.naturalsize(-999999))\"", "description": "Run project test suite and spot-check outputs"}
[tool_result] test_intcomma           499.9747 (3.58)        51,749.9866 (1.98)       626.0442 (3.64)        434.6080 (2.17)       583.9975 (3.71)      41.9968 (5.77)    3163;5659    1,597.3313 (0.27)     181818           1
test_naturalsize        500.0038 (3.58)        66,457.9857 (2.54)       631.0490 (3.67)        371.1832 (1.86)       625.0048 (3.97)      41.0073 (5.64)     999;3658    1,584.6631 (0.27)     137931           1
test_naturalday         542.0006 (3.88)     1,683,583.0174 (64.43)      849.0060
…[1329 chars elided]…
.40)    165;2921      124.6675 (0.02)      15239           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
715 passed, 69 skipped in 6.60s
1.0 MB 1.0 MiB 1.0M -1.0 MB
[assistant] `naturalsize()` now moves a value that rounds up to the base into the next unit. The full test suite passes (715 passed, 69 skipped).

The fix is in `src/humanize/filesize.py`. The suffix was chosen from `log()` before rounding, so `999999` formatted to `1000.0` and kept `kB`. The function now formats the value, and if the rounded number reaches the base and a larger suffix exists, it re-formats with the next one. The change covers decimal, binary and GNU. The largest suffix is left alone, so `10**33 - 1` still gives `1000.0 QB`.

I added regression cases to `tests/test_filesize.py`:
- `999999` → `1.0 MB`
- `999999999` with `%.0f` → `1 GB`
- `1024**2 - 1` binary → `1.0 MiB`, and `1024**3 - 1` binary → `1.0 GiB`
- The same two values in GNU mode → `1.0M` and `1.0G`
- The `QB` ceiling case

The negative-input retest in the existing test also covers these.

One thing to be aware of: the check calls `float()` on the formatted number. That works for the documented formats (`%.Nf`, `%d`), but a custom format that adds non-numeric text around the number would now raise `ValueError`. I did not find any such usage in the repo.

I have not committed anything.
