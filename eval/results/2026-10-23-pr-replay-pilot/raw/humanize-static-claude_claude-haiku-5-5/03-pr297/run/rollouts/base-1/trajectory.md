# trajectory base-1

final message:
`naturalday()` and `naturaldate()` now decide "today", "tomorrow" and "yesterday" in the datetime's own timezone when it is tz-aware. Naive datetimes and plain dates still use the system date. The full suite passes: 691 passed, 60 skipped (684 before, plus 7 new tests).

The fix is in `src/humanize/time.py`. A new `_today()` helper returns `datetime.now(value.tzinfo).date()` for aware datetimes and `date.today()` otherwise. Both functions use it in place of `dt.date.today()`.

`naturaldate()` also passes the original value to `naturalday()` rather than the converted date. Otherwise the "today" label would fall back to the system date.

The tests are in `tests/test_time.py`. They cover your AEDT example, a Pacific case where the system date is one day ahead of the local date, and a far-date case that checks the year is appended. Six of the seven new tests fail on the original code, so they reproduce the bug. The seventh (far-date) passes either way.

I didn't commit anything. ruff and mypy aren't installed in the project's test environment, so I couldn't run lint or type checks. I also didn't load the `humanize-error-contract` skill, since no exception types or messages changed.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"naturalday\\|naturaldate\" -r src | head -50", "description": "Check git status and locate naturalday functions"}
[tool_result] src/humanize/time.py:22:    "naturaldate",
src/humanize/time.py:23:    "naturalday",
src/humanize/time.py:311:def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
src/humanize/time.py:343:def naturaldate(value: dt.date | dt.datetime) -> str:
src/humanize/time.py:344:    """Like `naturalday`, but append a year for dates more than ~five months away."""
src/humanize/time.py:357:        return naturalday(value, "%b %d %Y")
src/humanize/time.py:358:    return naturalday(value)
src/humanize/__init__.py:19:    naturaldate,
src/humanize/__init__.py:20:    naturalday,
src/humanize/__init__.py:40:    "naturaldate",
src/humanize/__init__.py:41:    "naturalday",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "offset": 1, "limit": 60}
[tool_result] 1	"""Time humanizing functions.
2	
3	These are largely borrowed from Django's `contrib.humanize`.
4	"""
5	
6	from __future__ import annotations
7	
8	from enum import Enum
9	from functools import total_ordering
10	
11	from .i18n import _gettext as _
12	from .i18n import _ngettext
13	from .number import intcomma
14	
15	TYPE_CHECKING = False
16	if TYPE_CHECKING:
17	    import datetime as dt
18	    from collections.abc import Iterable
19	    from typing import Any
20	
21	__all__ = [
22	    "naturald
…[384 chars elided]…
her.__class__:
43	            return self.value < other.value
44	        return NotImplemented
45	
46	
47	def _now() -> dt.datetime:
48	    import datetime as dt
49	
50	    return dt.datetime.now()
51	
52	
53	def _abs_timedelta(delta: dt.timedelta) -> dt.timedelta:
54	    """Return an "absolute" value for a timedelta, always representing a time distance.
55	
56	    Args:
57	        delta (datetime.timedelta): Input timedelta.
58	
59	    Returns:
60	        datetime.timedelta: Absolute timedelta.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "offset": 300, "limit": 70}
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
[tool_use Bash] {"command": "grep -rn \"naturalday\\|naturaldate\\|freeze\\|today()\" tests | head -60; ls tests; ls <work>/env-humanize/bin/python 2>&1", "description": "Find existing naturalday tests and check test interpreter"}
[tool_result] tests/test_i18n.py:9:from freezegun import freeze_time
tests/test_i18n.py:13:with freeze_time("2020-02-02"):
tests/test_i18n.py:17:@freeze_time("2020-02-02")
tests/test_i18n.py:282:    @freeze_time("2020-02-02")
tests/test_i18n.py:295:    @freeze_time("2020-02-02")
tests/test_time.py:9:from freezegun import freeze_time
tests/test_time.py:28:with freeze_time(FROZEN_DATE):
tests/test_time.py:32:    TODAY = dt.date.today()
tests/test_time.py:141:@freeze_time(FROZEN_DATE)
tests/test_time.py:190:@fre
…[396 chars elided]…
me.py:300:    assert humanize.naturaldate(test_input) == expected
tests/test_time.py:371:@freeze_time(FROZEN_DATE)
tests/test_time.py:394:@freeze_time(FROZEN_DATE)
tests/test_time.py:440:@freeze_time(FROZEN_DATE)
tests/test_time.py:480:@freeze_time(FROZEN_DATE)
__init__.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "sed -n 20,40p tests/test_time.py && sed -n 225,302p tests/test_time.py && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Read naturalday tests and run baseline test suite"}
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
 
…[2675 chars elided]…
t.date(2010, 11, 2), "Nov 02 2010"),
        (dt.date(2010, 12, 2), "Dec 02 2010"),
        (dt.date(2011, 1, 2), "Jan 02 2011"),
        (dt.date(2011, 2, 2), "Feb 02 2011"),
    ],
)
def test_naturaldate(test_input: dt.date, expected: str) -> None:
    assert humanize.naturaldate(test_input) == expected


........................................................................ [ 96%]
........................                                                 [100%]
684 passed, 60 skipped in 0.55s
[assistant] Baseline is 684 passed, 60 skipped. The bug is that both functions compare the value's own calendar date with `dt.date.today()`, which is the system-local date. I'll add a helper that returns "today" in the datetime's own timezone when it is aware, and leave naive values and plain dates on `dt.date.today()`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "    return value\n\n\ndef naturalday(value: dt.date | dt.datetime, format: str = \"%b %d\") -> str:\n    \"\"\"Return a natural day.\n\n    For date values that are tomorrow, today or yesterday compared to\n    prese
…[1184 chars elided]…
datetime's own timezone.\n\n    \"\"\"\n    import datetime as dt\n\n    try:\n        today = _today(value)\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = value - today"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "    \"\"\"Like `naturalday`, but append a year for dates more than ~five months away.\"\"\"\n    import datetime as dt\n\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeErr
…[317 chars elided]…
ive months away.\"\"\"\n    import datetime as dt\n\n    try:\n        today = _today(value)\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = _abs_timedelta(value - today)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[assistant] `naturaldate` has a gap: after converting `value` to a plain `date`, it calls `naturalday(value)`, which would fall back to the system date. I'll have it pass the original value through so `naturalday` applies the same timezone rule.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py", "old_string": "    try:\n        today = _today(value)\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (Overflo
…[318 chars elided]…
.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = _abs_timedelta(day - today)\n    if delta.days >= 5 * 365 / 12:\n        return naturalday(value, \"%b %d %Y\")\n    return naturalday(value)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/src/humanize/time.py has been updated successfully.
[assistant] Now the regression tests. I'll add them after the existing `test_naturaldate`, using fixed-offset timezones and frozen UTC times.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/tests/test_time.py", "old_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    assert humanize.naturaldate(test_input) == expected\n", "new_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    asser
…[1165 chars elided]…
nd_utc(\n    test_input: dt.datetime, expected: str\n) -> None:\n    assert humanize.naturalday(test_input) == expected\n    assert humanize.naturaldate(test_input) == expected\n\n\n@freeze_time(\"2023-10-15 23:00:00\")\ndef test_naturaldate_aware_far_date_appends_year() -> None:\n    value = dt.datetime(2024, 6, 1, 12, 0, tzinfo=AEDT)\n    assert humanize.naturaldate(value) == \"Jun 01 2024\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/base-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"--- new tests against original code:\"; git stash list >/dev/null; git show HEAD:src/humanize/time.py > /tmp/orig_time.py; cp src/humanize/time.py /tmp/new_time.py && cp /tmp/orig_time.py src/humanize/time.py && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no tests/test_time.py -k aware 2>&1 | tail -3; cp /tmp/new_time.py src/humanize/time.py && git diff --stat", "description": "Run full suite, then check new tests fail on original code"}
[tool_result] ........................................................................ [ 76%]
........................................................................ [ 86%]
........................................................................ [ 95%]
...............................                                          [100%]
691 passed, 60 skipped in 0.56s
--- new tests against original code:
FAILED tests/test_time.py::test_naturalday_aware_uses_datetime_timezone_behind_utc[test_input1-tomorrow]
FAILED tests/test_time.py::test_naturalday_aware_uses_datetime_timezone_behind_utc[test_input2-yesterday]
6 failed, 1 passed, 382 deselected in 0.08s
 src/humanize/time.py | 20 ++++++++++++++++----
 tests/test_time.py   | 42 ++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 58 insertions(+), 4 deletions(-)
[assistant] The suite passes (691 passed, 60 skipped; the 7 new tests account for the increase). Against the original code, 6 of the 7 new tests fail, as expected. The seventh is the far-date check, which passes either way. I'll run the linters the repo uses, if they're available.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin; ls $PY | grep -E \"ruff|mypy\"; for t in ruff mypy; do if [ -x $PY/$t ]; then $PY/$t --version; fi; done; which ruff 2>/dev/null; $PY/ruff check src/humanize/time.py tests/test_time.py 2>&1 | tail -3; $PY/ruff format --check src/humanize/time.py tests/test_time.py 2>&1 | tail -2; $PY/mypy src/humanize/time.py 2>&1 | tail -2", "description": "Run ruff and mypy on changed files if installed"}
[tool_result] ruff not found
(eval):1: no such file or directory: <work>/env-humanize/bin/ruff
(eval):1: no such file or directory: <work>/env-humanize/bin/ruff
(eval):1: no such file or directory: <work>/env-humanize/bin/mypy
[tool_use Bash] {"command": "git diff src/humanize/time.py", "description": "Show the source diff for review"}
[tool_result] diff --git a/src/humanize/time.py b/src/humanize/time.py
index f0b24fa..0a4cf9f 100644
--- a/src/humanize/time.py
+++ b/src/humanize/time.py
@@ -308,17 +308,28 @@ def _convert_aware_datetime(
     return value
 
 
+def _today(value: dt.date | dt.datetime) -> dt.date:
+    """Return the current date, in the timezone of `value` if it is timezone-aware."""
+    import datetime as dt
+
+    if isinstance(value, dt.datetime) and value.tzinfo is not None:
+        return dt.datetime.now(value.tzinfo).
…[1161 chars elided]…
y)
+        today = _today(value)
+        day = dt.date(value.year, value.month, value.day)
     except AttributeError:
         # Passed value wasn't date-ish
         return str(value)
     except (OverflowError, ValueError):
         # Date arguments out of range
         return str(value)
-    delta = _abs_timedelta(value - dt.date.today())
+    delta = _abs_timedelta(day - today)
     if delta.days >= 5 * 365 / 12:
         return naturalday(value, "%b %d %Y")
     return naturalday(value)
[assistant] `naturalday()` and `naturaldate()` now decide "today", "tomorrow" and "yesterday" in the datetime's own timezone when it is tz-aware. Naive datetimes and plain dates still use the system date. The full suite passes: 691 passed, 60 skipped (684 before, plus 7 new tests).

The fix is in `src/humanize/time.py`. A new `_today()` helper returns `datetime.now(value.tzinfo).date()` for aware datetimes and `date.today()` otherwise. Both functions use it in place of `dt.date.today()`.

`naturaldate()` also passes the original value to `naturalday()` rather than the converted date. Otherwise the "today" label would fall back to the system date.

The tests are in `tests/test_time.py`. They cover your AEDT example, a Pacific case where the system date is one day ahead of the local date, and a far-date case that checks the year is appended. Six of the seven new tests fail on the original code, so they reproduce the bug. The seventh (far-date) passes either way.

I didn't commit anything. ruff and mypy aren't installed in the project's test environment, so I couldn't run lint or type checks. I also didn't load the `humanize-error-contract` skill, since no exception types or messages changed.
