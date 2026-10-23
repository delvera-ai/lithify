# trajectory base-1

final message:
`naturaldelta()` now returns `float("inf")` and `float("-inf")` unchanged as `"inf"` and `"-inf"`, matching how NaN already behaves. A finite value that is too large, such as `1e30`, still raises `OverflowError`. The full suite passes: 724 passed, 74 skipped.

The cause was the `int(value)` probe in `src/humanize/time.py`. It raises `OverflowError` for infinities, and that error was not in the caught set. I catch `OverflowError` only around that probe, so the `OverflowError` for `1e30` (raised later, when the timedelta is built) still propagates.

I also added two tests to `tests/test_time.py`: one checks that inf, -inf and NaN come back unchanged, and one checks that `1e30` raises. No existing tests were changed.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"naturaldelta\" src | head -20; grep -rn \"def naturaldelta\" -A60 src | head -120", "description": "Locate naturaldelta implementation"}
[tool_result] src/humanize/time.py:26:    "naturaldelta",
src/humanize/time.py:97:def naturaldelta(
src/humanize/time.py:134:        >>> assert naturaldelta(later - now) == "30 minutes"
src/humanize/time.py:294:    delta = naturaldelta(delta, months, minimum_unit)
src/humanize/__init__.py:30:    naturaldelta,
src/humanize/__init__.py:51:    "naturaldelta",
src/humanize/time.py:97:def naturaldelta(
src/humanize/time.py-98-    value: dt.timedelta | float,
src/humanize/time.py-99-    months: bool = True,
src/hum
…[2888 chars elided]…
humanize/time.py-149-    else:
src/humanize/time.py-150-        try:
src/humanize/time.py-151-            int(value)  # Explicitly don't support string such as "NaN" or "inf"
src/humanize/time.py-152-            value = float(value)
src/humanize/time.py-153-            delta = dt.timedelta(seconds=value)
src/humanize/time.py-154-        except (ValueError, TypeError):
src/humanize/time.py-155-            return str(value)
src/humanize/time.py-156-
src/humanize/time.py-157-    use_months = months
[tool_use Bash] {"command": "sed -n 1,25p src/humanize/time.py; grep -rn \"nan\\|inf\" tests/*.py | head -30; git status --short", "description": "Check imports, existing nan/inf tests, git status"}
[tool_result] """Time humanizing functions.

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
…[1097 chars elided]…
      (math.nan, "NaN"),
tests/test_number.py:183:        (math.inf, "+Inf"),
tests/test_number.py:184:        (-math.inf, "-Inf"),
tests/test_number.py:185:        ("nan", "NaN"),
tests/test_number.py:186:        ("-inf", "-Inf"),
tests/test_number.py:221:        ([math.nan], "NaN"),
tests/test_number.py:222:        ([math.inf], "+Inf"),
tests/test_number.py:223:        ([-math.inf], "-Inf"),
tests/test_number.py:224:        (["nan"], "NaN"),
tests/test_number.py:225:        (["-inf"], "-Inf"),
[tool_use Bash] {"command": "sed -n 157,175p src/humanize/time.py; grep -n \"naturaldelta\" -A3 tests/test_time.py | grep -n \"nan\\|inf\\|Overflow\\|1e\" ", "description": "Read rest of naturaldelta and related tests"}
[tool_result]     use_months = months

    delta = abs(delta)
    years = delta.days // 365
    days = delta.days % 365
    num_months = round(days / 30.5)

    if years == 0 and days < 1:
        if delta.seconds == 0:
            if min_unit == Unit.MICROSECONDS and delta.microseconds < 1000:
                return (
                    _ngettext("%d microsecond", "%d microseconds", delta.microseconds)
                    % delta.microseconds
                )

            if min_unit == Unit.MILLISECONDS or (
                min_unit == Unit.MICROSECONDS and 1000 <= delta.microseconds < 1_000_000
            ):
                milliseconds = delta.microseconds / 1000
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142627-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "offset": 146, "limit": 14}
[tool_result] 146	
147	    if isinstance(value, dt.timedelta):
148	        delta = value
149	    else:
150	        try:
151	            int(value)  # Explicitly don't support string such as "NaN" or "inf"
152	            value = float(value)
153	            delta = dt.timedelta(seconds=value)
154	        except (ValueError, TypeError):
155	            return str(value)
156	
157	    use_months = months
158	
159	    delta = abs(delta)
[assistant] The `int(value)` probe raises `OverflowError` for infinities, and that error is not caught. A plain `OverflowError` catch around the whole block would also swallow the `OverflowError` that `1e30` should still raise, so I'm scoping the catch to the probe only.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142627-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "old_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeE
…[28 chars elided]…
tr(value)", "new_string": "        try:\n            # Explicitly don't support string such as \"NaN\" or \"inf\". Infinite floats\n            # raise OverflowError here, so they are returned unchanged like NaN.\n            int(value)\n        except (ValueError, TypeError, OverflowError):\n            return str(value)\n        value = float(value)\n        delta = dt.timedelta(seconds=value)"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142627-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py has been updated successfully.
[assistant] Now I'll verify the behaviour directly, then run the project's test command.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c '\nimport math\nfrom humanize import naturaldelta\nprint(repr(naturaldelta(float(\"inf\"))), repr(naturaldelta(float(\"-inf\"))), repr(naturaldelta(float(\"nan\"))))\ntry:\n    naturaldelta(1e30); print(\"no error!\")\nexcept OverflowError as e: print(\"OverflowError ok:\", e)\nprint(naturaldelta(90))\n'; PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check inf, nan, and 1e30 behaviour, then run test suite"}
[tool_result] 'inf' '-inf' 'nan'
OverflowError ok: Python int too large to convert to C int
2 minutes
test_intcomma           457.9779 (3.41)      33,124.9903 (3.95)       583.1951 (3.84)       170.3404 (4.38)       583.0079 (3.87)      41.9968 (6.23)     118;4023    1,714.6919 (0.26)     155836           1
test_naturalsize        540.9820 (4.02)      43,959.0076 (5.24)       669.7834 (4.41)       310.8340 (7.99)       667.0016 (4.43)      41.9968 (6.23)     381;4492    1,493.0200 (0.23)     113753           
…[1359 chars elided]…
34.0083 (38.75)    208.9655 (30.99)     206;718      167.2232 (0.03)      21799           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
720 passed, 74 skipped in 7.39s
[assistant] Infinities now return unchanged, `1e30` still raises `OverflowError`, and the suite passes. I'll add a regression test next to the existing `naturaldelta` tests.
[tool_use Bash] {"command": "grep -n \"nan\\|OverflowError\\|def test_naturaldelta\\|parametrize\" tests/test_time.py | head -40", "description": "Find naturaldelta test patterns"}
[tool_result] 79:@pytest.mark.parametrize(
88:def test_naturaldelta_nomonths(test_input: dt.timedelta, expected: str) -> None:
92:@pytest.mark.parametrize(
135:def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
142:@pytest.mark.parametrize(
191:@pytest.mark.parametrize(
240:@pytest.mark.parametrize(
260:@pytest.mark.parametrize(
329:@pytest.mark.parametrize(
343:def test_naturaldelta_minimum_unit_default(seconds: float, expected: str) -> None:
351:@pytest.mark.parametrize(
386:def test_naturaldelta_minimum_unit_explicit(
398:@pytest.mark.parametrize(
421:@pytest.mark.parametrize(
467:@pytest.mark.parametrize(
507:@pytest.mark.parametrize(
546:@pytest.mark.parametrize(
573:@pytest.mark.parametrize(
637:@pytest.mark.parametrize(
739:@pytest.mark.parametrize(
840:@pytest.mark.parametrize(
[tool_use Bash] {"command": "sed -n 1,20p tests/test_time.py; sed -n 125,142p tests/test_time.py", "description": "Read test file header and naturaldelta test block"}
[tool_result] """Tests for time humanizing."""

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
        (dt.timedelta(days=35), "a month"),
        (dt.timedelta(days=65), "2 months"),
        (dt.timedelta(days=9), "9 days"),
 
…[57 chars elided]…
medelta(days=365 * 1_141), "1,141 years"),
        ("NaN", "NaN"),  # Returns non-numbers unchanged.
        # largest possible timedelta
        (dt.timedelta(days=999_999_999), "2,739,726 years"),
    ],
)
def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
    assert humanize.naturaldelta(test_input) == expected
    if not isinstance(test_input, str):
        assert humanize.naturaldelta(-test_input) == expected


@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142627-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "old_string": "    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)", "new_string": "    if not isinstance(test_input, str):\n        assert humanize.na
…[34 chars elided]…
d\n\n\n@pytest.mark.parametrize(\"test_input\", [float(\"inf\"), float(\"-inf\"), float(\"nan\")])\ndef test_naturaldelta_non_finite_unchanged(test_input: float) -> None:\n    assert humanize.naturaldelta(test_input) == str(test_input)\n\n\ndef test_naturaldelta_too_large_raises() -> None:\n    with pytest.raises(OverflowError):\n        humanize.naturaldelta(1e30)\n\n\n@freeze_time(FROZEN_DATE)"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142627-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no --benchmark-disable 2>&1 | tail -3; git diff --stat", "description": "Run test suite and show diff stat"}
[tool_result] ........................................................................ [ 99%]
......                                                                   [100%]
724 passed, 74 skipped in 0.56s
 src/humanize/time.py | 10 ++++++----
 tests/test_time.py   | 10 ++++++++++
 2 files changed, 16 insertions(+), 4 deletions(-)
[assistant] `naturaldelta()` now returns `float("inf")` and `float("-inf")` unchanged as `"inf"` and `"-inf"`, matching how NaN already behaves. A finite value that is too large, such as `1e30`, still raises `OverflowError`. The full suite passes: 724 passed, 74 skipped.

The cause was the `int(value)` probe in `src/humanize/time.py`. It raises `OverflowError` for infinities, and that error was not in the caught set. I catch `OverflowError` only around that probe, so the `OverflowError` for `1e30` (raised later, when the timedelta is built) still propagates.

I also added two tests to `tests/test_time.py`: one checks that inf, -inf and NaN come back unchanged, and one checks that `1e30` raises. No existing tests were changed.

Changes are uncommitted in the worktree.
