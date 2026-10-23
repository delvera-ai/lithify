# trajectory base-1

final message:
Fixed: `naturalday()` and `naturaldate()` now decide "today" in the datetime's own timezone when it is tz-aware. The full suite passes (693 passed, 60 skipped).

**Change in `src/humanize/time.py`:**
- New helper `_today(value)`. For a tz-aware datetime it returns `datetime.now(tz=value.tzinfo).date()`. For naive datetimes, plain dates and anything else it returns `dt.date.today()`, as before.
- `naturalday()` compares the value's date against `_today(value)`.
- `naturaldate()` had the same problem, and it also dropped the timezone before calling `naturalday()`, which would have reintroduced the bug. It now passes the original value through, so the timezone is kept.
- The `naturalday` docstring notes the tz-aware behaviour.

**Tests added to `tests/test_time.py`** (existing tests untouched). They freeze the clock at `2023-10-15 23:00 UTC` and use an AEDT (`+11:00`) value at `2023-10-16 17:00`, which should read "today". I also covered tomorrow, yesterday, a UTC-aware value, and a naive datetime that must not change. Against the original `time.py`, the six tz-aware cases fail (e.g. "tomorrow" instead of "today"), and the naive and UTC cases pass on both versions.

**Not done:**
- I did not commit. The changes are in the working tree.
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run lint or type checks.

## events
[tool_use Bash] {"command": "grep -n \"naturalday\\|naturaldate\\|def _date_and_delta\\|def naturaltime\" -A3 src/humanize/*.py | head -80; ls <work>/env-humanize/bin/python 2>&1", "description": "Locate naturalday code and check test env"}
[tool_result] src/humanize/__init__.py:19:    naturaldate,
src/humanize/__init__.py:20:    naturalday,
src/humanize/__init__.py-21-    naturaldelta,
src/humanize/__init__.py-22-    naturaltime,
src/humanize/__init__.py-23-    precisedelta,
--
src/humanize/__init__.py:40:    "naturaldate",
src/humanize/__init__.py:41:    "naturalday",
src/humanize/__init__.py-42-    "naturaldelta",
src/humanize/__init__.py-43-    "naturalsize",
src/humanize/__init__.py-44-    "naturaltime",
src/humanize/time.py:22:    "natural
…[1169 chars elided]…
"
src/humanize/time.py-345-    import datetime as dt
src/humanize/time.py-346-
src/humanize/time.py-347-    try:
--
src/humanize/time.py:357:        return naturalday(value, "%b %d %Y")
src/humanize/time.py:358:    return naturalday(value)
src/humanize/time.py-359-
src/humanize/time.py-360-
src/humanize/time.py-361-def _quotient_and_remainder(
<work>/env-humanize/bin/python
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "offset": 60, "limit": 110}
[tool_result] 60	        datetime.timedelta: Absolute timedelta.
61	    """
62	    if delta.days < 0:
63	        now = _now()
64	        return now - (now + delta)
65	    return delta
66	
67	
68	def _date_and_delta(
69	    value: Any, *, now: dt.datetime | None = None, precise: bool = False
70	) -> tuple[Any, Any]:
71	    """Turn a value into a date and a timedelta which represents how long ago it was.
72	
73	    If that's not possible, return `(None, value)`.
74	    """
75	    import datetime as dt
76	
77	  
…[2780 chars elided]…
onths = months
156	
157	    delta = abs(delta)
158	    years = delta.days // 365
159	    days = delta.days % 365
160	    num_months = round(days / 30.5)
161	
162	    if years == 0 and days < 1:
163	        if delta.seconds == 0:
164	            if min_unit == Unit.MICROSECONDS and delta.microseconds < 1000:
165	                return (
166	                    _ngettext("%d microsecond", "%d microseconds", delta.microseconds)
167	                    % delta.microseconds
168	                )
169	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "offset": 305, "limit": 60}
[tool_result] 305	
306	    if isinstance(value, dt.datetime) and value.tzinfo is not None:
307	        value = dt.datetime.fromtimestamp(value.timestamp())
308	    return value
309	
310	
311	def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
312	    """Return a natural day.
313	
314	    For date values that are tomorrow, today or yesterday compared to
315	    present day return representing string. Otherwise, return a string
316	    formatted according to `format`.
317	
318	    """
31
…[885 chars elided]…
   except AttributeError:
350	        # Passed value wasn't date-ish
351	        return str(value)
352	    except (OverflowError, ValueError):
353	        # Date arguments out of range
354	        return str(value)
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
[tool_use Bash] {"command": "grep -n \"def _now\" -A12 src/humanize/time.py; grep -rn \"naturalday\\|naturaldate\\|today\" tests/ | head -40; git log --oneline -1; ls tests", "description": "Inspect _now helper and existing naturalday tests"}
[tool_result] 47:def _now() -> dt.datetime:
48-    import datetime as dt
49-
50-    return dt.datetime.now()
51-
52-
53-def _abs_timedelta(delta: dt.timedelta) -> dt.timedelta:
54-    """Return an "absolute" value for a timedelta, always representing a time distance.
55-
56-    Args:
57-        delta (datetime.timedelta): Input timedelta.
58-
59-    Returns:
tests/test_time.py:32:    TODAY = dt.date.today()
tests/test_time.py:243:        ([TODAY], "today"),
tests/test_time.py:255:def test_naturalday(test_args
…[13 chars elided]…
.Any], expected: str) -> None:
tests/test_time.py:256:    assert humanize.naturalday(*test_args) == expected
tests/test_time.py:263:        (TODAY, "today"),
tests/test_time.py:284:        (dt.date(2010, 2, 2), "today"),
tests/test_time.py:299:def test_naturaldate(test_input: dt.date, expected: str) -> None:
tests/test_time.py:300:    assert humanize.naturaldate(test_input) == expected
4aa96bb lithify: probe base
__init__.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
[tool_use Bash] {"command": "sed -n 236,302p tests/test_time.py; grep -n \"freeze\\|mock\\|monkeypatch\" tests/test_time.py | head", "description": "Read naturalday/naturaldate tests"}
[tool_result]     assert humanize.naturaltime(test_input, months=False) == expected


@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([TODAY], "today"),
        ([TOMORROW], "tomorrow"),
        ([YESTERDAY], "yesterday"),
        ([dt.date(TODAY.year, 3, 5)], "Mar 05"),
        (["02/26/1984"], "02/26/1984"),
        ([dt.date(1982, 6, 27), "%Y.%m.%d"], "1982.06.27"),
        ([None], "None"),
        (["Not a date at all."], "Not a date at all."),
        ([VALU
…[1742 chars elided]…
 02 2011"),
        (dt.date(2011, 2, 2), "Feb 02 2011"),
    ],
)
def test_naturaldate(test_input: dt.date, expected: str) -> None:
    assert humanize.naturaldate(test_input) == expected


9:from freezegun import freeze_time
28:with freeze_time(FROZEN_DATE):
141:@freeze_time(FROZEN_DATE)
190:@freeze_time(FROZEN_DATE)
239:@freeze_time(FROZEN_DATE)
259:@freeze_time(FROZEN_DATE)
371:@freeze_time(FROZEN_DATE)
394:@freeze_time(FROZEN_DATE)
440:@freeze_time(FROZEN_DATE)
480:@freeze_time(FROZEN_DATE)
[assistant] The root cause is clear: `naturalday` and `naturaldate` compare against `dt.date.today()` (the system local date), not the date in the datetime's own timezone. `naturaldate` also drops the timezone before it calls `naturalday`, so the fix has to cover both. I'll add a helper that returns "today" in the value's timezone for tz-aware datetimes and fall back to the existing behaviour otherwise.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "def naturalday(value: dt.date | dt.datetime, format: str = \"%b %d\") -> str:\n    \"\"\"Return a natural day.\n\n    For date values that are tomorrow, today or yesterday compared to\n    present day return represen
…[1126 chars elided]…
atetime's own\n    timezone.\n\n    \"\"\"\n    import datetime as dt\n\n    today = _today(value)\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = value - today"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "    \"\"\"Like `naturalday`, but append a year for dates more than ~five months away.\"\"\"\n    import datetime as dt\n\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeErr
…[539 chars elided]…
date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = _abs_timedelta(date - today)\n    if delta.days >= 5 * 365 / 12:\n        return naturalday(value, \"%b %d %Y\")\n    return naturalday(value)"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142201-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[assistant] Now I'll add regression tests. First I need the test file's imports and the frozen-date constants.
[tool_use Bash] {"command": "sed -n 1,40p tests/test_time.py; tail -5 tests/test_time.py; grep -n \"zoneinfo\\|dateutil\\|pytz\" pyproject.toml tests/*.py | head", "description": "Read test file header and check tz libraries"}
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
MICROSECONDS_101_943 = 101943 / 1000000  # 101.94 milliseconds
MILLISECONDS_1_337 = 1337 / 1000  # 1.337 seconds
ONE_HOUR = 3600
ONE
…[213 chars elided]…
.datetime.now(tz=dt.timezone(offset=dt.timedelta(hours=1)))
    TODAY = dt.date.today()
    TOMORROW = TODAY + ONE_DAY_DELTA
    YESTERDAY = TODAY - ONE_DAY_DELTA


class FakeDate:
    def __init__(self, year: int, month: int, day: int) -> None:
        self.year, self.month, self.day = year, month, day

        ("%d", 1.9999999999999999, 2),
    ],
)
def test_rounding_by_fmt(fmt: str, value: float, expected: float) -> None:
    assert time._rounding_by_fmt(fmt, value) == pytest.approx(expected)
[tool_use Bash] {"command": "cat >> tests/test_time.py <<'EOF'\n\n\nAEDT = dt.timezone(dt.timedelta(hours=11))\n\n\n@freeze_time(\"2023-10-15 23:00:00\")\n@pytest.mark.parametrize(\n    \"test_input, expected\",\n    [\n        # System date is 2023-10-15, but in AEDT it is already 2023-10-16.\n        (dt.datetime(2023, 10, 16, 17, 0, tzinfo=AEDT), \"today\"),\n        (dt.datetime(2023, 10, 17, 10, 0, tzinfo=AE
…[843 chars elided]…
: dt.datetime, expected: str) -> None:\n    assert humanize.naturaldate(test_input) == expected\nEOF\nPYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add tz-aware regression tests and run full suite"}
[tool_result] ......................................................................ss [  9%]
sssssssssssssssssssssssssssssssssssssssssssssssssssssssss......s........ [ 19%]
........................................................................ [ 28%]
........................................................................ [ 38%]
........................................................................ [ 47%]
........................................................................ [ 57%]
........................................................................ [ 66%]
........................................................................ [ 76%]
........................................................................ [ 86%]
........................................................................ [ 95%]
.................................                                        [100%]
693 passed, 60 skipped in 0.54s
[assistant] The full suite passes. Next I'll confirm the new tests actually catch the bug by running them against the original `time.py` from HEAD.
[tool_use Bash] {"command": "D=$(mktemp -d) && cp -R src/humanize \"$D/humanize\" && git show HEAD:src/humanize/time.py > \"$D/humanize/time.py\" && PYTHONPATH=\"$D\" <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_time.py -k timezone_aware 2>&1 | tail -
…[136 chars elided]…
bf9e87d20/scratchpad/pr-work/env-humanize/bin/python -m ruff check src tests 2>&1 | tail -3; PYTHONPATH=src <work>/env-humanize/bin/python -m mypy src/humanize/time.py 2>&1 | tail -2; git status --short", "description": "Check new tests fail on original code and run linters"}
[tool_result] E         - yesterday
E         + today

tests/test_time.py:861: AssertionError
=========================== short test summary info ============================
FAILED tests/test_time.py::test_naturalday_timezone_aware[test_input0-today]
FAILED tests/test_time.py::test_naturalday_timezone_aware[test_input1-tomorrow]
FAILED tests/test_time.py::test_naturalday_timezone_aware[test_input2-yesterday]
FAILED tests/test_time.py::test_naturaldate_timezone_aware[test_input0-today]
FAILED tests/test_time.
…[83 chars elided]…
::test_naturaldate_timezone_aware[test_input2-yesterday]
6 failed, 3 passed, 382 deselected in 0.08s
<work>/env-humanize/bin/python: No module named ruff
<work>/env-humanize/bin/python: No module named mypy
 M src/humanize/time.py
 M tests/test_time.py
[assistant] Fixed: `naturalday()` and `naturaldate()` now decide "today" in the datetime's own timezone when it is tz-aware. The full suite passes (693 passed, 60 skipped).

**Change in `src/humanize/time.py`:**
- New helper `_today(value)`. For a tz-aware datetime it returns `datetime.now(tz=value.tzinfo).date()`. For naive datetimes, plain dates and anything else it returns `dt.date.today()`, as before.
- `naturalday()` compares the value's date against `_today(value)`.
- `naturaldate()` had the same problem, and it also dropped the timezone before calling `naturalday()`, which would have reintroduced t
…[161 chars elided]…
st_time.py`** (existing tests untouched). They freeze the clock at `2023-10-15 23:00 UTC` and use an AEDT (`+11:00`) value at `2023-10-16 17:00`, which should read "today". I also covered tomorrow, yesterday, a UTC-aware value, and a naive datetime that must not change. Against the original `time.py`, the six tz-aware cases fail (e.g. "tomorrow" instead of "today"), and the naive and UTC cases pass on both versions.

**Not done:**
- I did not commit. The changes are in the working tree.
- `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run lint or type checks.
