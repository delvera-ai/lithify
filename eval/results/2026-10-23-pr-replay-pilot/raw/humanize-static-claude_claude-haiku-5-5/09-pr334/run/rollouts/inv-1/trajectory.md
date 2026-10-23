# trajectory inv-1

final message:
Infinite inputs to `naturaldelta()` now return `"inf"` and `"-inf"` unchanged, matching how `nan` already behaves. Finite values that are too large still raise `OverflowError`.

**Change** (`src/humanize/time.py`): the `int(value)` probe is now in its own `try`. It catches `OverflowError` and returns `str(value)`. The float conversion and `timedelta` call stay in the original `try`, so `1e30` still raises as documented. A single `try` with `OverflowError` added would have swallowed that error too.

**Test** (`tests/test_time.py`): a new `test_naturaldelta_infinity` covers `math.inf` → `"inf"` and `-math.inf` → `"-inf"`. I added it as a separate function because the existing `test_naturaldelta` also asserts `naturaldelta(-x)`, which would expect `"inf"` for `-inf`. I added `import math` for it. No existing test was edited.

**Verification**
- Reproduced first on HEAD with `compare_outputs.py`: `inf` and `-inf` raised `OverflowError`, `nan` returned `'nan'`, and `1e30` raised `OverflowError`.
- After the change, the comparison shows exactly two changed outputs (`inf`, `-inf`). The string inputs `'inf'`, `'1e3'`, and `10**400` are unchanged, as are `nan`, `1e30`, and `-1e30`.
- Full suite: `722 passed, 74 skipped`. I did not check why the 74 are skipped; they are not from this change.
- `lint_changed.py`: `0 findings`. Ruff was not run; it is not installed in this environment.

**Left out on purpose:** I did not add test cases for `nan` or `1e30`. Both already behave as documented, so the harness says to leave them out. The `Raises:` and `returns unchanged` docstrings were already accurate, so I did not edit them.

I have not committed the change.

## events
[assistant] I'll start by reading the naturaldelta code and reproducing the bug on the unmodified tree.
[tool_use Bash] {"command": "git status --short && grep -n \"def naturaldelta\" -A 60 src/humanize/time.py | head -120; ls <work>/env-humanize/bin/python 2>&1", "description": "Inspect naturaldelta source and check interpreter"}
[tool_result] 97:def naturaldelta(
98-    value: dt.timedelta | float,
99-    months: bool = True,
100-    minimum_unit: str = "seconds",
101-) -> str:
102-    """Return a natural representation of a timedelta or number of seconds.
103-
104-    This is similar to `naturaltime`, but does not add tense to the result.
105-
106-    The timedelta will be rounded to the nearest unit that makes sense.
107-
108-    Args:
109-        value (datetime.timedelta, int or float): A timedelta or a number of seconds.
110-   
…[1417 chars elided]…
a):
148-        delta = value
149-    else:
150-        try:
151-            int(value)  # Explicitly don't support string such as "NaN" or "inf"
152-            value = float(value)
153-            delta = dt.timedelta(seconds=value)
154-        except (ValueError, TypeError):
155-            return str(value)
156-
157-    use_months = months
<work>/env-humanize/bin/python
[assistant] The harness requires reproducing on HEAD with `compare_outputs.py` before editing. I'll run that for the infinity cases and the large finite case.
[tool_use Bash] {"command": "<work>/env-humanize/bin/python .lithify/harness/scripts/compare_outputs.py \"naturaldelta(float('inf'))\" \"naturaldelta(float('-inf'))\" \"naturaldelta(float('nan'))\" \"naturaldelta(1e30)\" \"naturaldelta(-1e30)\" 2>&1; echo \"exit=$?\"", "description": "Reproduce naturaldelta behavior on HEAD vs working tree"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpg6o1cjbw/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/src/humanize/__init__.py)
same    naturaldelta(float('inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: !OverflowError: cannot convert float infinity to integer
same    naturaldelta(float('-inf'))
    old: !OverflowError: cannot 
…[23 chars elided]…
to integer
    new: !OverflowError: cannot convert float infinity to integer
same    naturaldelta(float('nan'))
    old: 'nan'
    new: 'nan'
same    naturaldelta(1e30)
    old: !OverflowError: Python int too large to convert to C int
    new: !OverflowError: Python int too large to convert to C int
same    naturaldelta(-1e30)
    old: !OverflowError: Python int too large to convert to C int
    new: !OverflowError: Python int too large to convert to C int
5 expressions, 0 changed, 5 same
exit=0
[assistant] The bug reproduces: `inf` and `-inf` raise `OverflowError` from the `int(value)` probe, while `nan` already returns unchanged and `1e30` raises as documented. Next I'll check the existing patterns for non-finite handling and the related tests, and load the error-contract skill since this change alters an exception path.
[tool_use Bash] {"command": "grep -rn \"isfinite\\|isinf\\|isnan\\|^import\\|^from\" src/humanize/time.py | head -20; echo ---; grep -rn \"isfinite\\|isinf\" src/humanize | head; echo ---; grep -rn \"naturaldelta\" tests | grep -i \"inf\\|nan\\|overflow\\|1e\" | head -30; echo ---; grep -n \"OverflowError\" -B3 -A3 tests/test_time.py | head -60; echo ---; ls .claude/skills .lithify/harness 2>/dev/null; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Search for non-finite handling patterns and related tests"}
[tool_result] src/humanize/time.py:6:from __future__ import annotations
src/humanize/time.py:10:from enum import Enum
src/humanize/time.py:11:from functools import total_ordering
src/humanize/time.py:13:from .i18n import _gettext as _
src/humanize/time.py:14:from .i18n import _ngettext
src/humanize/time.py:15:from .number import intcomma
---
src/humanize/number.py:59:    if math.isinf(value) and value < 0:
src/humanize/number.py:61:    if math.isinf(value) and value > 0:
src/humanize/number.py:106:        if 
…[422 chars elided]…
   if not math.isfinite(value):
src/humanize/number.py:481:    if not math.isfinite(value):
---
---
---
.claude/skills:
humanize-error-contract
humanize-number-output

.lithify/harness:
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "cat .claude/skills/humanize-error-contract/*.md; echo ----; sed -n 1,10p src/humanize/time.py; echo ----; ls tests; grep -rln \"naturaldelta\" tests; grep -rn \"inf\\|nan\" tests/*time* | head -30; echo ---; sed -n 50,65p src/humanize/number.py; sed -n 470,490p src/humanize/number.py", "description": "Read error-contract skill and related test/source context"}
[tool_result] ---
name: humanize-error-contract
description: Load when a task adds, removes or changes an exception that a humanize function raises (e.g. narrowing a bare `Exception`, adding a `ValueError`/`TypeError`), or changes an error message in src/humanize/.
---

# Changing what a humanize function raises

An exception type in this library is public API. Check each of these places.

1. **The raise site** (`src/humanize/*.py`). Ruff selects `EM` (flake8-errmsg), so every raise
   builds its message in a
…[2288 chars elided]…
d floor and
            ceil. If the number is larger than ceil or smaller than floor, the output
            will be prepended with a token indicating as such.

    """
    import math

    if value is None:
        return None

    if not math.isfinite(value):
        return _format_not_finite(value)

    if floor is not None and value < floor:
        value = floor
        token = floor_token
    elif ceil is not None and value > ceil:
        value = ceil
        token = ceil_token
    else:
[assistant] The error-contract skill applies here, since the change alters which inputs raise `OverflowError`. I'll read its guidance-relevant tests next: the existing `naturaldelta` tests and any `OverflowError` assertions.
[tool_use Bash] {"command": "grep -rn \"Overflow\\|nan\\|NaN\\|\\\"inf\\\"\" tests/ | head -30; echo ---; grep -n \"def test_naturaldelta\\|class Test\\|parametrize\" tests/test_time.py | head -40; echo; sed -n 157,185p src/humanize/time.py", "description": "Find existing overflow/nan tests and naturaldelta test layout"}
[tool_result] tests/test_time.py:73:    assert time._date_and_delta("NaN") == (None, "NaN")
tests/test_time.py:130:        ("NaN", "NaN"),  # Returns non-numbers unchanged.
tests/test_time.py:181:        ("NaN", "NaN"),
tests/test_time.py:230:        ("NaN", "NaN"),
tests/test_number.py:30:        (math.nan, "NaN"),
tests/test_number.py:33:        ("nan", "NaN"),
tests/test_number.py:73:        ([math.nan], "NaN"),
tests/test_number.py:76:        (["nan"], "NaN"),
tests/test_number.py:127:        ([math.nan],
…[1809 chars elided]…
        if min_unit == Unit.MILLISECONDS or (
                min_unit == Unit.MICROSECONDS and 1000 <= delta.microseconds < 1_000_000
            ):
                milliseconds = delta.microseconds / 1000
                return (
                    _ngettext("%d millisecond", "%d milliseconds", int(milliseconds))
                    % milliseconds
                )
            return _("a moment")

        if delta.seconds == 1:
            return _("a second")

        if delta.seconds < 60:
[tool_use Bash] {"command": "sed -n 92,141p tests/test_time.py; echo ---; sed -n 1,20p tests/test_time.py; grep -n \"pytest.raises\" tests/test_time.py | head", "description": "Read naturaldelta parametrized test block"}
[tool_result] @pytest.mark.parametrize(
    "test_input, expected",
    [
        (0, "a moment"),
        (1, "a second"),
        (23.5, "23 seconds"),
        (30, "30 seconds"),
        (dt.timedelta(microseconds=13), "a moment"),
        (dt.timedelta(minutes=1, seconds=29), "a minute"),
        (dt.timedelta(minutes=1, seconds=30), "2 minutes"),
        (dt.timedelta(minutes=1, seconds=59), "2 minutes"),
        (dt.timedelta(minutes=2), "2 minutes"),
        (dt.timedelta(minutes=59), "59 minutes"),
  
…[1762 chars elided]…
humanizing."""

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
821:    with pytest.raises(
827:    with pytest.raises(ValueError, match="Minimum unit 'years' not supported"):
836:    with pytest.raises(TypeError):
[assistant] The existing `test_naturaldelta` helper also asserts `naturaldelta(-x)`, so an `inf` entry there would expect `"inf"` for `-inf` too and fail. The `inf` cases need their own test function. Per the harness, I'll leave out `nan` and `1e30` since they already behave as documented.

I'll make the fix now. The `int(value)` probe raises `OverflowError` only for infinite values. The `timedelta` call is inside the same `try`, so catching `OverflowError` there would also swallow the documented error for `1e30`. I'll split the probe into its own `try`, so only the probe's `OverflowError` is caught.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/src/humanize/time.py", "offset": 146, "limit": 14}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/src/humanize/time.py", "old_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeEr
…[93 chars elided]…
 Explicitly don't support string such as \"NaN\" or \"inf\"\n        except (OverflowError, ValueError, TypeError):\n            # OverflowError is raised for an infinite float; return it unchanged.\n            return str(value)\n        try:\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeError):\n            return str(value)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/src/humanize/time.py has been updated successfully.
[assistant] Next, the test. I'll add a new function after `test_naturaldelta`, since the existing helper's `-x` assertion doesn't fit infinities.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/tests/test_time.py", "offset": 134, "limit": 9}
[tool_result] 134	)
135	def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
136	    assert humanize.naturaldelta(test_input) == expected
137	    if not isinstance(test_input, str):
138	        assert humanize.naturaldelta(-test_input) == expected
139	
140	
141	@freeze_time(FROZEN_DATE)
142	@pytest.mark.parametrize(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/tests/test_time.py", "old_string": "        assert humanize.naturaldelta(-test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)", "new_string": "        assert humanize.naturaldelta(-test_input) == expected\n\n\n@pytest.mark.parametrize(\n    \"test_input, expected\",\n    [\n        (math.inf, \"inf\"),  # Returns non-convertible values unchanged.\n        (-math.inf, \"-inf\"),\n    ],\n)\ndef test_naturaldelta_infinity(test_input: float, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/tests/test_time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/tests/test_time.py", "old_string": "import datetime as dt\nimport typing", "new_string": "import datetime as dt\nimport math\nimport typing"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/tests/test_time.py has been updated successfully.
[assistant] Now I'll verify: the old-vs-new comparison, the full test suite, and the lint script.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py \"naturaldelta(float('inf'))\" \"naturaldelta(float('-inf'))\" \"naturaldelta(float('nan'))\" \"naturaldelta(1e30)\" \"naturaldelta(-1e30)\" \"naturaldelta('inf')\" \"naturaldelta('1e3')\" \"naturaldelta(10**400)\" 2>&1; echo \"exit=$?\"; echo ---; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; $PY .lithify/harness/scripts/lint_changed.py 2>&1; echo \"exit=$?\"", "description": "Compare outputs, run full test suite, and run lint script"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp9_foi5i0/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/inv-1/src/humanize/__init__.py)
CHANGED naturaldelta(float('inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: 'inf'
CHANGED naturaldelta(float('-inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: '-inf'
s
…[2568 chars elided]…
           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
722 passed, 74 skipped in 6.17s
---
rules checked: EM101, EM102, PT006
0 findings in 2 changed files
exit=0
[assistant] Infinite inputs to `naturaldelta()` now return `"inf"` and `"-inf"` unchanged, matching how `nan` already behaves. Finite values that are too large still raise `OverflowError`.

**Change** (`src/humanize/time.py`): the `int(value)` probe is now in its own `try`. It catches `OverflowError` and returns `str(value)`. The float conversion and `timedelta` call stay in the original `try`, so `1e30` still raises as documented. A single `try` with `OverflowError` added would have swallowed that error too.

**Test** (`tests/test_time.py`): a new `test_naturaldelta_infinity` covers `math.inf` → `"inf"` 
…[472 chars elided]…
ts (`inf`, `-inf`). The string inputs `'inf'`, `'1e3'`, and `10**400` are unchanged, as are `nan`, `1e30`, and `-1e30`.
- Full suite: `722 passed, 74 skipped`. I did not check why the 74 are skipped; they are not from this change.
- `lint_changed.py`: `0 findings`. Ruff was not run; it is not installed in this environment.

**Left out on purpose:** I did not add test cases for `nan` or `1e30`. Both already behave as documented, so the harness says to leave them out. The `Raises:` and `returns unchanged` docstrings were already accurate, so I did not edit them.

I have not committed the change.
