# trajectory inv-1

final message:
Fixed: `naturalday()` and `naturaldate()` now take "today" from the datetime's own timezone when the datetime is tz-aware. Naive datetimes and plain dates still use the system date as before.

**The change** (`src/humanize/time.py`)
- New private helper `_today(value)`. For a tz-aware datetime it returns `dt.datetime.now(value.tzinfo).date()`. Otherwise it returns `dt.date.today()`, which is the old behaviour.
- `naturalday()` uses that helper for the comparison.
- `naturaldate()` also uses it. It no longer overwrites `value` before the call to `naturalday()`, so the original datetime reaches `naturalday()` and the timezone is not lost.

**Tests** (`tests/test_time.py`, new tests only; no existing test touched)
- `test_naturalday_aware_uses_datetime_timezone` covers `today`, `tomorrow` and `yesterday` cases in AEDT (+11) and PST (−8), checked against both functions.
- `test_naturaldate_aware_long_distance_uses_datetime_timezone` checks that the year is appended for a far-off aware date.

**Checks**
- Baseline before editing: 684 passed, 60 skipped.
- After the change, full suite: 691 passed, 60 skipped (the 7 new tests pass), exit 0.
- `fails_on_base.py tests/test_time.py -k aware`: exit 0. Four of the new tests fail on the unmodified source, which are the AEDT cases from the bug report. The other three pass on the base source. Two are the PST cases, which were already correct there because the frozen system date happens to match. The third is the long-distance test; it is a regression guard, not a reproducer.
- Not run: `ruff` and `mypy`. The project notes say they aren't installed in the test environment, so I checked the style by reading the code.

**Choices I made**
- The helper is placed just above `naturaldate()`, not at the top of the module.
- The `utcoffset() is not None` check keeps a tzinfo that reports no offset on the old path.

Nothing is committed. The working tree has the two modified files.

## events
[tool_use Bash] {"command": "cat memory.md 2>/dev/null; ls; grep -n \"def naturalday\\|def naturaldate\" -A45 src/humanize/time.py | head -150", "description": "Locate naturalday and naturaldate source"}
[tool_result] AGENTS.md
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
311:def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
312-    """Return a natural day.
313-
314-    For date values that are tomorrow, today or yesterday compared to
315-    present day return representing string. Otherwise, return a string
316-    formatted according to `format`.
317-
318-    """
319-    import datetime as dt
320-
321-    tr
…[1986 chars elided]…
er(36, 24, Unit.DAYS, Unit.DAYS, [], "%0.2f")
378-    (1.5, 0)
379-
380-    If `unit` is in `suppress`, the quotient will be zero and the remainder will be the
381-    initial value. The idea is that if we cannot use `unit`, we are forced to use a
382-    lower unit, so we cannot do the division.
383-
384-    >>> _quotient_and_remainder(36, 24, Unit.DAYS, Unit.HOURS, [Unit.DAYS], "%0.2f")
385-    (0, 36)
386-
387-    In other cases, return the quotient and remainder as `divmod` would do it.
388-
[tool_use Bash] {"command": "sed -n 1,30p src/humanize/time.py && grep -n \"today\\|now\\|mock\\|freez\" tests/test_i18n.py tests/test_time.py 2>/dev/null | head -40; ls tests; cat .lithify/harness/scripts/fails_on_base.py | head -30; ls <work>/env-humanize/bin/python", "description": "Inspect time module imports, tests, and harness script"}
[tool_result] """Time humanizing functions.

These are largely borrowed from Django's `contrib.humanize`.
"""

from __future__ import annotations

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
    "naturaldate",
    "naturalday",
    "naturaldelta",
    "naturalt
…[3834 chars elided]…
eproduced)
    1  every selected test PASSES on the base source (tests do not show the bug)
    2  setup error, or pytest collected/ran nothing or errored for another reason
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


def main() -> int:
<work>/env-humanize/bin/python
[assistant] Baseline run before editing, using the project's test command from CLAUDE.md.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run baseline test suite before editing"}
[tool_result] ........................................................................ [ 77%]
........................................................................ [ 87%]
........................................................................ [ 96%]
........................                                                 [100%]
684 passed, 60 skipped in 0.60s
exit=
[assistant] Baseline: 684 passed, 60 skipped. Now the existing naturalday tests, so the fix matches what they already assert.
[tool_use Bash] {"command": "grep -n \"naturalday\\|naturaldate\\|aware\\|tzinfo\\|timezone\" tests/test_time.py | head -60", "description": "Find existing naturalday and tz tests"}
[tool_result] 30:    NOW_UTC = dt.datetime.now(tz=dt.timezone.utc)
31:    NOW_UTC_PLUS_01_00 = dt.datetime.now(tz=dt.timezone(offset=dt.timedelta(hours=1)))
255:def test_naturalday(test_args: list[typing.Any], expected: str) -> None:
256:    assert humanize.naturalday(*test_args) == expected
299:def test_naturaldate(test_input: dt.date, expected: str) -> None:
300:    assert humanize.naturaldate(test_input) == expected
476:def test_naturaltime_timezone(test_input: dt.datetime, expected: str) -> None:
516:def test_naturaltime_timezone_when(test_input: dt.datetime, expected: str) -> None:
[tool_use Bash] {"command": "sed -n 20,40p tests/test_time.py && sed -n 230,300p tests/test_time.py", "description": "Read naturalday test cases"}
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
 
…[2251 chars elided]…
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
[assistant] The root cause is clear: both functions strip the datetime down to a plain `date` and then compare it with `dt.date.today()`, the system-local date. The fix is to take "today" from the value's own timezone when it is tz-aware, and to leave the naive path alone. `naturaldate` also currently drops the original value before calling `naturalday`, so I'll pass the original through.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/src/humanize/time.py", "old_string": "    \"\"\"\n    import datetime as dt\n\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except
…[172 chars elided]…
g": "    \"\"\"\n    import datetime as dt\n\n    today = _today(value)\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowError, ValueError):\n        # Date arguments out of range\n        return str(value)\n    delta = value - today\n\n    if delta.days == 0:"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/src/humanize/time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/src/humanize/time.py", "old_string": "    import datetime as dt\n\n    try:\n        value = dt.date(value.year, value.month, value.day)\n    except AttributeError:\n        # Passed value wasn't date-ish\n        return str(value)\n    except (OverflowEr
…[868 chars elided]…
.\n\n    For timezone-aware datetimes this is the current date in the datetime's own\n    timezone, so that \"today\" matches the day the value is shown on. Otherwise it\n    is the system's local date.\n    \"\"\"\n    import datetime as dt\n\n    if isinstance(value, dt.datetime) and value.utcoffset() is not None:\n        return dt.datetime.now(value.tzinfo).date()\n    return dt.date.today()"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/src/humanize/time.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `naturaldate` tests. I'm adding new tests only; existing ones are untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/tests/test_time.py", "old_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    assert humanize.naturaldate(test_input) == expected\n", "new_string": "def test_naturaldate(test_input: dt.date, expected: str) -> None:\n    assert
…[800 chars elided]…
str\n) -> None:\n    assert humanize.naturalday(test_input) == expected\n    assert humanize.naturaldate(test_input) == expected\n\n\n@freeze_time(\"2023-10-15 23:00:00\")  # UTC; 2023-10-16 10:00 in AEDT\ndef test_naturaldate_aware_long_distance_uses_datetime_timezone() -> None:\n    value = dt.datetime(2024, 3, 1, 12, 0, tzinfo=AEDT)\n    assert humanize.naturaldate(value) == \"Mar 01 2024\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"exit=$?\"; PYTHONPATH=src <work>/env-humanize/bin/python .lithify/harness/scripts/fails_on_base.py tests/test_time.py -k aware 2>&1 | tail -15; echo \"fails_on_base exit=$?\"", "description": "Run full suite and base-source reproduction check"}
[tool_result] =========================== short test summary info ============================
FAILED tests/test_time.py::test_naturaldate_aware_long_distance_uses_datetime_timezone
1 failed, 690 passed, 60 skipped in 0.59s
exit=0
>       assert humanize.naturaldate(value) == "Mar 01 2024"
E       AssertionError: assert 'Mar 01' == 'Mar 01 2024'
E         
E         - Mar 01 2024
E         + Mar 01

tests/test_time.py:329: AssertionError
=========================== short test summary info ====================
…[100 chars elided]…
FAILED tests/test_time.py::test_naturalday_aware_uses_datetime_timezone[test_input1-today]
FAILED tests/test_time.py::test_naturalday_aware_uses_datetime_timezone[test_input2-tomorrow]
FAILED tests/test_time.py::test_naturalday_aware_uses_datetime_timezone[test_input3-yesterday]
FAILED tests/test_time.py::test_naturaldate_aware_long_distance_uses_datetime_timezone
5 failed, 2 passed, 382 deselected in 0.12s
RESULT: tests FAIL on base source -> they reproduce the bug (exit 0)
fails_on_base exit=0
[assistant] Two things to sort out. The long-distance test expectation was my mistake: 2024-03-01 is only ~137 days after 2023-10-16, under the ~152-day threshold, so it correctly returns "Mar 01". I'll move the date to 2024-04-01 (168 days out). The base-source run is what the harness wants: the aware-datetime tests fail on the unmodified source, so they reproduce the bug.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/tests/test_time.py", "old_string": "    value = dt.datetime(2024, 3, 1, 12, 0, tzinfo=AEDT)\n    assert humanize.naturaldate(value) == \"Mar 01 2024\"", "new_string": "    value = dt.datetime(2024, 4, 1, 12, 0, tzinfo=AEDT)\n    assert humanize.naturaldate(value) == \"Apr 01 2024\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142958-bug-humanize-naturalday-and-huma/inv-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no > /tmp/full_run.txt 2>&1; echo \"full exit=$?\"; tail -1 /tmp/full_run.txt; PYTHONPATH=src $PY .lithify/harness/scripts/fails_on_base.py tests/test_time.py -k aware > /tmp/base_run.txt 2>&1; echo \"fails_on_base exit=$?\"; tail -2 /tmp/base_run.txt; git diff --stat", "description": "Rerun full suite, base-source check, and diff stat"}
[tool_result] full exit=0
691 passed, 60 skipped in 0.58s
fails_on_base exit=0
4 failed, 3 passed, 382 deselected in 0.10s
RESULT: tests FAIL on base source -> they reproduce the bug (exit 0)
 src/humanize/time.py | 22 +++++++++++++++++++---
 tests/test_time.py   | 29 +++++++++++++++++++++++++++++
 2 files changed, 48 insertions(+), 3 deletions(-)
[assistant] Fixed: `naturalday()` and `naturaldate()` now take "today" from the datetime's own timezone when the datetime is tz-aware. Naive datetimes and plain dates still use the system date as before.

**The change** (`src/humanize/time.py`)
- New private helper `_today(value)`. For a tz-aware datetime it returns `dt.datetime.now(value.tzinfo).date()`. Otherwise it returns `dt.date.today()`, which is the old behaviour.
- `naturalday()` uses that helper for the comparison.
- `naturaldate()` also uses it. It no longer overwrites `value` before the call to `naturalday()`, so the original datetime reaches 
…[740 chars elided]…
e source. Two are the PST cases, which were already correct there because the frozen system date happens to match. The third is the long-distance test; it is a regression guard, not a reproducer.
- Not run: `ruff` and `mypy`. The project notes say they aren't installed in the test environment, so I checked the style by reading the code.

**Choices I made**
- The helper is placed just above `naturaldate()`, not at the top of the module.
- The `utcoffset() is not None` check keeps a tzinfo that reports no offset on the old path.

Nothing is committed. The working tree has the two modified files.
