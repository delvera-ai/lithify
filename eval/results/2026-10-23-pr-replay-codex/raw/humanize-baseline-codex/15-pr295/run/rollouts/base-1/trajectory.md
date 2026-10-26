# trajectory base-1

final message:
Fixed `naturaldelta()` to round year-only results: 1058 days now returns `"3 years"`.

Added regression tests for rounding boundaries, negative durations, numeric seconds, and both `months` settings.

Validation: 751 passed, 110 skipped; diff check passed.

## events
[assistant] I’ll check how `naturaldelta()` calculates years, add a regression case, and run the project’s checks.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*time*' -g 'pyproject.toml' -g '*test*'"
~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205557-bug-humanize-naturaldelta-trunca/base-1
src/humanize/time.py
AGENTS.md
tests/test_number.py
tests/test_lists.py
tests/test_i18n.py
tests/test_benchmarks.py
tests/test_time.py
tests/test_filesize.py
pyproject.toml
docs/time.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,280p' tests/test_time.py"
"""Tests for time humanizing."""

from __future__ import annotations

import datetime as dt
import typing

import pytest
from freezegun import freeze_time

import humanize
from humanize import time

ONE_DAY_DELTA = dt.timedelta(days=1)

# In seconds
ONE_MICROSECOND = 1 / 1000000
FOUR_MICROSECONDS = 4 / 1000000
ONE_MILLISECOND = 1 / 1000
FOUR_MILLISECONDS = 4 / 1000
MICROSECONDS_101_943 = 101943 / 1000000  # 101.94 milliseconds
MILLISECONDS_1_337 = 1337 / 1000  # 1.337 seconds
ONE_HOUR = 3600
ONE
…[10241 chars elided]…
/26/1984"], "02/26/1984"),
        ([dt.date(1982, 6, 27), "%Y.%m.%d"], "1982.06.27"),
        ([None], "None"),
        (["Not a date at all."], "Not a date at all."),
        ([VALUE_ERROR_TEST], str(VALUE_ERROR_TEST)),
        ([OVERFLOW_ERROR_TEST], str(OVERFLOW_ERROR_TEST)),
    ],
)
def test_naturalday(test_args: list[typing.Any], expected: str) -> None:
    assert humanize.naturalday(*test_args) == expected


@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
    "test_input, expected",

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,320p' src/humanize/time.py"
"""Time humanizing functions.

These are largely borrowed from Django's `contrib.humanize`.
"""

from __future__ import annotations

__lazy_modules__ = {"humanize.i18n", "humanize.number"}

from enum import Enum
from functools import total_ordering

from .i18n import _gettext as _
from .i18n import _ngettext
from .number import intcomma

TYPE_CHECKING = False
if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Iterable
    from typing import Any

__all__ = [
    "naturald
…[8510 chars elided]…
(dt.datetime, dt.timedelta)):
        future = date > now

    ago = _("%s from now") if future else _("%s ago")
    delta = naturaldelta(delta, months, minimum_unit)

    if delta == _("a moment"):
        return _("now")

    return str(ago % delta)


def _convert_aware_datetime(
    value: dt.datetime | dt.timedelta | float | None,
) -> Any:
    """Convert aware datetime to naive datetime and pass through any other type."""
    if value is None:
        return None

    import datetime as dt

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205557-bug-humanize-naturaldelta-trunca/base-1/src/humanize/time.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205557-bug-humanize-naturaldelta-trunca/base-1/tests/test_time.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  8%]
.....................sssssssssssssssssssssssssssssssssssssssssssssssssss [ 16%]
ssssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss....... [ 25%]
........................................................................ [ 33%]
........................................................................ [ 41%]
........................................................................ [ 50%]
....................
…[4344 chars elided]…
 15,228.7248 (>1000.0)   287;483        4.0286 (0.00)       3665           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
751 passed, 110 skipped in 9.31s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed `naturaldelta()` to round year-only results: 1058 days now returns `"3 years"`.

Added regression tests for rounding boundaries, negative durations, numeric seconds, and both `months` settings.

Validation: 751 passed, 110 skipped; diff check passed.
