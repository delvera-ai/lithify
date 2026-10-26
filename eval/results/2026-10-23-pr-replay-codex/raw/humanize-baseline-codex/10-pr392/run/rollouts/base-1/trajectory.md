# trajectory base-1

final message:
Fixed `intcomma` to bypass float conversion for integers when `ndigits=None`, preserving every digit in very large positive and negative values. Numeric strings and explicit `ndigits` retain their existing behavior.

Added regression tests. Full suite: **727 passed, 110 skipped**.

## events
[assistant] I’ll check how `intcomma` handles integers, make a minimal fix, and run the project tests.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; rg -n 'def intcomma|intcomma' src/humanize/number.py tests/test_number.py; rg --files -g AGENTS.md"
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
tests/test_number.
…[290 chars elided]…
 accepts floats.
src/humanize/number.py:124:        >>> intcomma(100)
src/humanize/number.py:126:        >>> intcomma("1000")
src/humanize/number.py:128:        >>> intcomma(1_000_000)
src/humanize/number.py:130:        >>> intcomma(1_234_567.25)
src/humanize/number.py:132:        >>> intcomma(1234.5454545, 2)
src/humanize/number.py:134:        >>> intcomma(14308.40, 1)
src/humanize/number.py:136:        >>> intcomma("14308.40", 1)
src/humanize/number.py:138:        >>> intcomma(None)
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,230p' src/humanize/number.py"
"""Humanizing functions for numbers."""

from __future__ import annotations

__lazy_modules__ = {"bisect"}

import bisect

from .i18n import _gettext as _
from .i18n import _ngettext, decimal_separator, thousands_separator
from .i18n import _ngettext_noop as NS_
from .i18n import _pgettext as P_

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import TypeAlias

    # This type can be better defined by typing.SupportsFloat
    # but that's a Python 3.8 only typing option.
    NumberOrStri
…[5190 chars elided]…
rd(8100000000000000000000000000000000)
        '8.1 decillion'
        >>> intword(None)
        'None'
        >>> intword("1234000", "%0.3f")
        '1.234 million'

        ```

    Args:
        value (int, float, str): Integer to convert.
        format (str): To change the number of decimal or general format of the number
            portion.

    Returns:
        str: Friendly text representation as a string, unless the value passed could not
            be coaxed into an `int`.
    """

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,120p' tests/test_number.py"
"""Number tests."""

from __future__ import annotations

import math
import typing

import pytest

import humanize
from humanize import number


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("1", "1st"),
        ("2", "2nd"),
        ("3", "3rd"),
        ("4", "4th"),
        ("11", "11th"),
        ("12", "12th"),
        ("13", "13th"),
        ("101", "101st"),
        ("102", "102nd"),
        ("103", "103rd"),
        ("111", "111th"),
        ("something else", "som
…[2740 chars elided]…
00000000000000"], "1.0 quadrillion"),
        (["1300000000000000"], "1.3 quadrillion"),
        (["-1300000000000000"], "-1.3 quadrillion"),
        (["3500000000000000000000"], "3.5 sextillion"),
        (["8100000000000000000000000000000000"], "8.1 decillion"),
        (["-8100000000000000000000000000000000"], "-8.1 decillion"),
        ([1_000_000_000_000_000_000_000_000_000_000_000_000], "1000.0 decillion"),
        ([1_100_000_000_000_000_000_000_000_000_000_000_000], "1100.0 decillion"),

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk rg -n 'intcomma|activate|deactivate' tests/test_i18n.py pyproject.toml"
tests/test_i18n.py:30:        humanize.i18n.activate("lv")
tests/test_i18n.py:34:        humanize.i18n.activate("ru_RU")
tests/test_i18n.py:39:        humanize.i18n.activate("si_LK")
tests/test_i18n.py:47:        humanize.i18n.deactivate()
tests/test_i18n.py:53:def test_intcomma() -> None:
tests/test_i18n.py:56:    assert humanize.intcomma(number) == "10,000,000"
tests/test_i18n.py:59:        humanize.i18n.activate("de_DE")
tests/test_i18n.py:60:        assert humanize.intcomma(number) == "10.00
…[1934 chars elided]…
_RU")
tests/test_i18n.py:314:        humanize.i18n.activate("en_US")
tests/test_i18n.py:317:        humanize.i18n.activate("en_GB")
tests/test_i18n.py:320:        humanize.i18n.deactivate()
tests/test_i18n.py:327:            humanize.i18n.activate("fr")
tests/test_i18n.py:330:            humanize.i18n.activate(None)
tests/test_i18n.py:337:            humanize.i18n.deactivate()
tests/test_i18n.py:347:        humanize.i18n.activate(locale)
tests/test_i18n.py:353:        humanize.i18n.deactivate()

[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205050-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205050-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
src/humanize/number.py | 2 +-
 tests/test_number.py   | 3 +++
 2 files changed, 4 insertions(+), 1 deletion(-)

[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  8%]
...................sssssssssssssssssssssssssssssssssssssssssssssssssssss [ 17%]
ssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss......... [ 25%]
........................................................................ [ 34%]
........................................................................ [ 43%]
........................................................................ [ 51%]
....................
…[4363 chars elided]…
28,915.9943 (>1000.0)    18;379        4.0323 (0.00)       3914           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
727 passed, 110 skipped in 7.98s

[assistant] Fixed `intcomma` to bypass float conversion for integers when `ndigits=None`, preserving every digit in very large positive and negative values. Numeric strings and explicit `ndigits` retain their existing behavior.

Added regression tests. Full suite: **727 passed, 110 skipped**.
