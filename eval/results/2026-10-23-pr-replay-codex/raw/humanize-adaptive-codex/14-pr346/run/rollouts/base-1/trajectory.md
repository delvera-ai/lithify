# trajectory base-1

final message:
Fixed `intword()` rollover by comparing the rounded value with the ratio between magnitudes, avoiding precision loss from multiplying large floats.

Added regression coverage for all four reported magnitudes, negative values, multiple precisions, and values that must stay below rollover.

Checks passed: 764 tests passed, 110 skipped; diff check clean.

## events
[assistant] I’ll check how `intword()` handles magnitude rollover, add regression tests, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*intword*' -g 'pyproject.toml' -g 'tox.ini'"
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```
~/.cache/lithify/work/repo-f19ff99309c1/20261023-210005-bug-humanize-intword-fails-to-ca/base-1
src/humanize/number.py
tox.ini
docs/number.md
AGENTS.md
pyproject.toml
tests/test_number.py

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,300p' src/humanize/number.py"
"""Humanizing functions for numbers."""

from __future__ import annotations

__lazy_modules__ = {"bisect"}

import bisect

from .i18n import _gettext as _
from .i18n import _gettext_noop as N_
from .i18n import _ngettext, decimal_separator, thousands_separator
from .i18n import _ngettext_noop as NS_
from .i18n import _pgettext as P_
from .i18n import _pgettext_noop as PS_

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import TypeAlias

    # This type can be better defined by typing.Su
…[7177 chars elided]…
rs[ordinal + 1]:
        # After rounding, we end up just at the next power
        ordinal += 1
        rounded_value = 1.0

    singular, plural = human_powers[ordinal]
    unit = _ngettext(singular, plural, math.ceil(rounded_value))
    decimal_sep = decimal_separator()
    number = (format % rounded_value).replace(".", decimal_sep)
    return f"{negative_prefix}{number} {unit}"


def apnumber(value: NumberOrString) -> str:
    """Converts an integer to Associated Press style.

    Examples:

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'rg -n \"intword\" tests/test_number.py; cat pyproject.toml; cat tox.ini; git status --short'"
93:def test_intword_powers() -> None:
147:def test_intword(test_args: list[str], expected: str) -> None:
148:    assert humanize.intword(*test_args) == expected
249:        ([1, humanize.intword, 1e6, None, "under "], "under 1.0 million"),
[build-system]
build-backend = "hatchling.build"
requires = [
  "hatch-vcs",
  "hatchling>=1.27",
]

[project]
name = "humanize"
description = "Python humanize utilities"
readme = "README.md"
keywords = [
  "humanize time size",
]
license = "MIT"
license-files
…[3658 chars elided]…
commands =
    {envpython} -m pytest \
      --cov humanize \
      --cov tests \
      --cov-report html \
      --cov-report term \
      --cov-report xml \
      {posargs}

[testenv:docs]
deps =
    -r docs/requirements.txt
commands =
    mkdocs build

[testenv:lint]
skip_install = true
deps =
    prek
commands =
    prek run --all-files --show-diff-on-failure

[testenv:mypy]
deps =
    -r requirements-mypy.txt
commands =
    mypy . {posargs}

[pytest]
addopts = --color=yes --doctest-modules

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '75,165p' tests/test_number.py"
        ([-math.inf], "-Inf"),
        (["nan"], "NaN"),
        (["-inf"], "-Inf"),
    ],
)
def test_intcomma(
    test_args: list[int] | list[float] | list[str], expected: str
) -> None:
    assert humanize.intcomma(*test_args) == expected


@pytest.mark.parametrize("sign", [1, -1])
def test_intcomma_large_integer(sign: int) -> None:
    value = sign * (10**400 + 123)
    expected = ("-" if sign < 0 else "") + "10" + ",000" * 132 + ",123"
    assert humanize.intcomma(value) == expected


def 
…[2115 chars elided]…
(["999499", "%.0f"], "999 thousand"),
    ],
)
def test_intword(test_args: list[str], expected: str) -> None:
    assert humanize.intword(*test_args) == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (0, "zero"),
        (1, "one"),
        (2, "two"),
        (4, "four"),
        (5, "five"),
        (9, "nine"),
        (10, "10"),
        ("7", "seven"),
        (None, "None"),
        (math.nan, "NaN"),
        (math.inf, "+Inf"),
        (-math.inf, "-Inf"),

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-210005-bug-humanize-intword-fails-to-ca/base-1/tests/test_number.py
[command exit=1] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_number.py -k large_magnitude_rounding'
FFFFFFFFFFFFFFFFFFFFFFFF                                                 [100%]
=================================== FAILURES ===================================
_____ test_intword_large_magnitude_rounding[0-1-24-sextillion-septillion] ______

exponent = 24, lower_unit = 'sextillion', upper_unit = 'septillion', sign = 1
precision = 0

    @pytest.mark.parametrize(
        "exponent, lower_unit, upper_unit",
        [
            (24, "sextillion", "septillion"),
            (27, "septillion", "oc
…[28187 chars elided]…
_number.py::test_intword_large_magnitude_rounding[2-1-33-nonillion-decillion]
FAILED tests/test_number.py::test_intword_large_magnitude_rounding[2--1-24-sextillion-septillion]
FAILED tests/test_number.py::test_intword_large_magnitude_rounding[2--1-27-septillion-octillion]
FAILED tests/test_number.py::test_intword_large_magnitude_rounding[2--1-30-octillion-nonillion]
FAILED tests/test_number.py::test_intword_large_magnitude_rounding[2--1-33-nonillion-decillion]
24 failed, 240 deselected in 0.10s

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-210005-bug-humanize-intword-fails-to-ca/base-1/src/humanize/number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  8%]
.....................sssssssssssssssssssssssssssssssssssssssssssssssssss [ 16%]
ssssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss....... [ 24%]
........................................................................ [ 32%]
........................................................................ [ 41%]
........................................................................ [ 49%]
....................
…[4443 chars elided]…
18,895.7783 (>1000.0)   111;645        3.9464 (0.00)       3885           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
764 passed, 110 skipped in 9.20s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
src/humanize/number.py |  2 +-
 tests/test_number.py   | 25 +++++++++++++++++++++++++
 2 files changed, 26 insertions(+), 1 deletion(-)

[assistant] Fixed `intword()` rollover by comparing the rounded value with the ratio between magnitudes, avoiding precision loss from multiplying large floats.

Added regression coverage for all four reported magnitudes, negative values, multiple precisions, and values that must stay below rollover.

Checks passed: 764 tests passed, 110 skipped; diff check clean.
