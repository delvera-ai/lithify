# trajectory base-1

final message:
`naturalday()` and `naturaldate()` now decide "today" in the datetime's own timezone when it is tz-aware. The full suite passes (688 passed, 60 skipped), and the new regression tests fail on the original code.

**The change** (`src/humanize/time.py`):
- A new helper, `_today_for(value)`, returns `datetime.now(value.tzinfo).date()` for tz-aware datetimes and `date.today()` otherwise.
- Both public functions take "today" from that helper before they reduce the value to a date, since that reduction drops the timezone.
- The comparison logic moved into a private `_natural_day(value, today, format)`, so `naturaldate()` passes its own "today" down instead of having `naturalday()` re-read the system date.
- Naive datetimes and plain dates take the same path as before.

**Tests** (`tests/test_time.py`): a new parametrised test, frozen at `2023-10-15 23:00 UTC`, covers the AEDT case from the report (`2023-10-16 17:00+11:00` now reads "today"), plus yesterday, tomorrow, and a date more than five months away in both functions. Three of the four cases fail on the original code; the fourth is a control that passes either way.

Nothing is committed. I read the bug as covering both functions, since `naturaldate()` has the same flaw.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"naturalday\\|naturaldate\" src/humanize/*.py | head -50", "description": "Check status and locate naturalday functions"}
[tool_result] src/humanize/__init__.py:19:    naturaldate,
src/humanize/__init__.py:20:    naturalday,
src/humanize/__init__.py:40:    "naturaldate",
src/humanize/__init__.py:41:    "naturalday",
src/humanize/time.py:22:    "naturaldate",
src/humanize/time.py:23:    "naturalday",
src/humanize/time.py:311:def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
src/humanize/time.py:343:def naturaldate(value: dt.date | dt.datetime) -> str:
src/humanize/time.py:344:    """Like `naturalday`, but append a year for dates more than ~five months away."""
src/humanize/time.py:357:        return naturalday(value, "%b %d %Y")
src/humanize/time.py:358:    return naturalday(value)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142151-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "offset": 300, "limit": 70}
[tool_result] 300	def _convert_aware_datetime(
301	    value: dt.datetime | dt.timedelta | float | None,
302	) -> Any:
303	    """Convert aware datetime to naive datetime and pass through any other type."""
304	    import datetime as dt
305	
306	    if isinstance(value, dt.datetime) and value.tzinfo is not None:
307	        value = dt.datetime.fromtimestamp(value.timestamp())
308	    return value
309	
310	
311	def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
312	    """Return a natu
…[1299 chars elided]…
      return str(value)
355	    delta = _abs_timedelta(value - dt.date.today())
356	    if delta.days >= 5 * 365 / 12:
357	        return naturalday(value, "%b %d %Y")
358	    return naturalday(value)
359	
360	
361	def _quotient_and_remainder(
362	    value: float,
363	    divisor: float,
364	    unit: Unit,
365	    minimum_unit: Unit,
366	    suppress: Iterable[Unit],
367	    format: str,
368	) -> tuple[float, float]:
369	    """Divide `value` by `divisor`, returning the quotient and remainder.
[tool_use Bash] {"command": "grep -n \"today\\|naturalday\\|naturaldate\\|tz\\|freeze\\|mock\" tests/*.py | head -80; sed -n 1,30p src/humanize/time.py | grep -n import; ls <work>/env-humanize/bin/python 2>&1", "description": "Inspect existing naturalday tests and env"}
[tool_result] tests/test_i18n.py:9:from freezegun import freeze_time
tests/test_i18n.py:13:with freeze_time("2020-02-02"):
tests/test_i18n.py:14:    NOW = dt.datetime.now(tz=dt.timezone.utc)
tests/test_i18n.py:17:@freeze_time("2020-02-02")
tests/test_i18n.py:282:    @freeze_time("2020-02-02")
tests/test_i18n.py:295:    @freeze_time("2020-02-02")
tests/test_time.py:9:from freezegun import freeze_time
tests/test_time.py:28:with freeze_time(FROZEN_DATE):
tests/test_time.py:30:    NOW_UTC = dt.datetime.now(tz=dt.
…[1025 chars elided]…
s/test_time.py:480:@freeze_time(FROZEN_DATE)
6:from __future__ import annotations
8:from enum import Enum
9:from functools import total_ordering
11:from .i18n import _gettext as _
12:from .i18n import _ngettext
13:from .number import intcomma
17:    import datetime as dt
18:    from collections.abc import Iterable
19:    from typing import Any
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "sed -n 20,35p tests/test_time.py; sed -n 236,300p tests/test_time.py", "description": "Read existing naturalday test cases"}
[tool_result] FOUR_MILLISECONDS = 4 / 1000
MICROSECONDS_101_943 = 101943 / 1000000  # 101.94 milliseconds
MILLISECONDS_1_337 = 1337 / 1000  # 1.337 seconds
ONE_HOUR = 3600
ONE_DAY = 24 * ONE_HOUR
ONE_YEAR = 365.25 * ONE_DAY
FROZEN_DATE = "2010-02-02"

with freeze_time(FROZEN_DATE):
    NOW = dt.datetime.now()
    NOW_UTC = dt.datetime.now(tz=dt.timezone.utc)
    NOW_UTC_PLUS_01_00 = dt.datetime.now(tz=dt.timezone(offset=dt.timedelta(hours=1)))
    TODAY = dt.date.today()
    TOMORROW = TODAY + ONE_DAY_DELTA
 
…[1968 chars elided]…
"),
        (dt.date(2010, 7, 2), "Jul 02"),
        (dt.date(2010, 8, 2), "Aug 02 2010"),
        (dt.date(2010, 9, 2), "Sep 02 2010"),
        (dt.date(2010, 10, 2), "Oct 02 2010"),
        (dt.date(2010, 11, 2), "Nov 02 2010"),
        (dt.date(2010, 12, 2), "Dec 02 2010"),
        (dt.date(2011, 1, 2), "Jan 02 2011"),
        (dt.date(2011, 2, 2), "Feb 02 2011"),
    ],
)
def test_naturaldate(test_input: dt.date, expected: str) -> None:
    assert humanize.naturaldate(test_input) == expected
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142151-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "def naturalday(value: dt.date | dt.datetime, format: str = \"%b %d\") -> str:\n    \"\"\"Return a natural day.\n\n    For date values that are tomorrow, today or yesterday compared to\n    present day return represen
…[3028 chars elided]…
value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = _abs_timedelta(value - today)\n    if delta.days >= 5 * 365 / 12:\n        return _natural_day(value, today, \"%b %d %Y\")\n    return _natural_day(value, today, \"%b %d\")"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142151-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[assistant] Fix is in. Now I'll add regression tests next to the existing `naturalday`/`naturaldate` tests.
[tool_use Bash] {"command": "grep -n \"^def test_naturaldate\" -A2 tests/test_time.py", "description": "Locate end of naturaldate test"}
[tool_result] 299:def test_naturaldate(test_input: dt.date, expected: str) -> None:
300-    assert humanize.naturaldate(test_input) == expected
301-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142151-bug-humanize-naturalday-and-huma/base-1/tests/test_time.py", "old_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    assert humanize.naturaldate(test_input) == expected\n", "new_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    asser
…[657 chars elided]…
w\"),\n        (dt.datetime(2023, 3, 5, 9, 0, tzinfo=AEDT), \"Mar 05\", \"Mar 05 2023\"),\n    ],\n)\ndef test_naturalday_aware_datetime_uses_own_timezone(\n    test_input: dt.datetime,\n    expected_naturalday: str,\n    expected_naturaldate: str,\n) -> None:\n    assert humanize.naturalday(test_input) == expected_naturalday\n    assert humanize.naturaldate(test_input) == expected_naturaldate\n"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142151-bug-humanize-naturalday-and-huma/base-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ......................................................................ss [  9%]
sssssssssssssssssssssssssssssssssssssssssssssssssssssssss......s........ [ 19%]
........................................................................ [ 28%]
........................................................................ [ 38%]
........................................................................ [ 48%]
........................................................................ [ 57%]
........................................................................ [ 67%]
........................................................................ [ 77%]
........................................................................ [ 86%]
........................................................................ [ 96%]
............................                                             [100%]
688 passed, 60 skipped in 0.55s
[assistant] Suite passes. I'll confirm the new test actually fails on the original code, so it's a real regression check.
[tool_use Bash] {"command": "R=$(pwd) && T=$(mktemp -d) && cp -R src tests \"$T\"/ && git show HEAD:src/humanize/time.py > \"$T/src/humanize/time.py\" && cd \"$T\" && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_time.py -k aware 2>&1 | tail -5; cd \"$R\" && git status --short", "description": "Confirm new test fails on original code"}
[tool_result] =========================== short test summary info ============================
FAILED tests/test_time.py::test_naturalday_aware_datetime_uses_own_timezone[test_input0-today-today]
FAILED tests/test_time.py::test_naturalday_aware_datetime_uses_own_timezone[test_input1-yesterday-yesterday]
FAILED tests/test_time.py::test_naturalday_aware_datetime_uses_own_timezone[test_input2-tomorrow-tomorrow]
3 failed, 1 passed, 382 deselected in 0.07s
 M src/humanize/time.py
 M tests/test_time.py
[assistant] `naturalday()` and `naturaldate()` now decide "today" in the datetime's own timezone when it is tz-aware. The full suite passes (688 passed, 60 skipped), and the new regression tests fail on the original code.

**The change** (`src/humanize/time.py`):
- A new helper, `_today_for(value)`, returns `datetime.now(value.tzinfo).date()` for tz-aware datetimes and `date.today()` otherwise.
- Both public functions take "today" from that helper before they reduce the value to a date, since that reduction drops the timezone.
- The comparison logic moved into a private `_natural_day(value, today, format)
…[37 chars elided]…
"today" down instead of having `naturalday()` re-read the system date.
- Naive datetimes and plain dates take the same path as before.

**Tests** (`tests/test_time.py`): a new parametrised test, frozen at `2023-10-15 23:00 UTC`, covers the AEDT case from the report (`2023-10-16 17:00+11:00` now reads "today"), plus yesterday, tomorrow, and a date more than five months away in both functions. Three of the four cases fail on the original code; the fourth is a control that passes either way.

Nothing is committed. I read the bug as covering both functions, since `naturaldate()` has the same flaw.
