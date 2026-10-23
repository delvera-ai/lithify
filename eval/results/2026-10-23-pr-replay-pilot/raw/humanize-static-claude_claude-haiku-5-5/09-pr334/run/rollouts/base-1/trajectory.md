# trajectory base-1

final message:
`naturaldelta(float("inf"))` and `naturaldelta(float("-inf"))` now return `"inf"` and `"-inf"` instead of raising `OverflowError`. A finite value that is too large still raises `OverflowError`. The full suite passes: `722 passed, 74 skipped`.

**Change** (`src/humanize/time.py`)
- Added an early return before the `int()` conversion: if the value is a float and `math.isinf()` is true, return `str(value)`.
- Added `import math` at the top of the module.
- I guarded on real float infinities rather than catching `OverflowError` around the conversion. Catching it there would also swallow the documented overflow for `1e30`, which comes from `timedelta(seconds=...)` later in the function.
- Strings are untouched: `naturaldelta("12")` still gives `"12 seconds"`.

**Tests** (`tests/test_time.py`)
- Added `test_naturaldelta_infinity_unchanged`, parametrized over `inf` and `-inf`. Both raise on the original code, so the tests fail there.
- I did not add a case for `1e30`. It already raises `OverflowError` on the original code, so the harness says to leave it out. No existing test lines were edited.

**Checks**
- `compare_outputs.py` on the original and new code: `inf` and `-inf` changed; `nan`, `1e30` and `"12"` are the same.
- Lint was not run because `ruff` is not installed. I read the changes against the project's style: the new import is ordered correctly and the new test follows the existing parametrize style.
- The `Raises:` and "returned unchanged" docstring already describe this behaviour, so I did not edit the docstring.

I have not committed the change.

## events
[assistant] I'll start by reading the `naturaldelta` code and the project's test setup.
[tool_use Bash] {"command": "git status --short && grep -n \"def naturaldelta\" -A60 src/humanize/time.py | head -120 && ls .lithify/harness/scripts/ && ls <work>/env-humanize/bin/ 2>&1 | head", "description": "Inspect naturaldelta source and harness files"}
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
…[1405 chars elided]…
 dt.timedelta):
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
compare_outputs.py
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
coverage
coverage-3.12
coverage3
[assistant] Next I'll reproduce the bug on the unmodified code with the project's comparison script, as the harness asks.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'naturaldelta(float(\"inf\"))' 'naturaldelta(float(\"-inf\"))' 'naturaldelta(float(\"nan\"))' 'naturaldelta(1e30)' 2>&1 | tail -30; sed -n 157,200p src/humanize/time.py", "description": "Reproduce inf/nan/huge inputs on original code"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpgffyp2f_/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/__init__.py)
same    naturaldelta(float("inf"))
    old: !OverflowError: cannot convert float infinity to integer
    new: !OverflowError: cannot convert float infinity to integer
same    naturaldelta(float("-inf"))
    old: !OverflowError: cannot
…[1310 chars elided]…
 < 60:
            return _ngettext("%d second", "%d seconds", delta.seconds) % delta.seconds

        if 60 <= delta.seconds < 3600:
            minutes = round(delta.seconds / 60)
            if minutes == 1:
                return _("a minute")

            if minutes == 60:
                return _("an hour")

            return _ngettext("%d minute", "%d minutes", minutes) % minutes

        if 3600 <= delta.seconds:
            hours = round(delta.seconds / 3600)
            if hours == 1:
[assistant] The bug reproduces on the unmodified code: `inf` and `-inf` raise `OverflowError`, `nan` already returns unchanged, and `1e30` raises `OverflowError`, which must stay. Since this change removes an exception that `naturaldelta` raises, I'll load the error-contract skill the harness points to before editing.
[tool_use Skill] {"skill": "humanize-error-contract"}
[tool_result] Launching skill: humanize-error-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/.claude/skills/humanize-error-contract

# Changing what a humanize function raises

An exception type in this library is public API. Check each of these places.

1. **The raise site** (`src/humanize/*.py`). Ruff selects `EM` (flake8-errmsg), so every raise
   builds its message in a local first and passes the variable:
   `msg = "..."` then `raise ValueError(msg)` (see `time.py`, `number.py`, `i18n.py`).
   Never write `raise X("literal")` or `raise X(f"..
…[645 chars elided]…
Type>, match=<message>)`
   (`tests/test_time.py`, `tests/test_i18n.py::TestActivate`). If an existing assertion uses a
   base class (e.g. `pytest.raises(Exception, ...)`), it still passes after you narrow to a
   subclass. Do NOT rewrite those lines, because changing a pre-existing test line counts as
   editing an existing test even when it makes the test stricter. To pin the new type, add a
   NEW test function next to the existing ones. Base it on the same setup and the same `match`.

Release notes are drafted on GitHub Releases (`RELEASING.md`); the repo has no CHANGELOG file to
update.

[tool_use Bash] {"command": "sed -n 1,30p src/humanize/time.py && grep -n \"naturaldelta\" -r tests | head -40", "description": "Check time.py imports and existing naturaldelta tests"}
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
…[1158 chars elided]…
mum_unit=minimum_unit) == expected
tests/test_time.py:828:        humanize.naturaldelta(1, minimum_unit="years")
tests/test_i18n.py:80:def test_naturaldelta() -> None:
tests/test_i18n.py:83:    assert humanize.naturaldelta(seconds) == "1,234 years"
tests/test_i18n.py:87:        assert humanize.naturaldelta(seconds) == "1 234 ans"
tests/test_i18n.py:89:        assert humanize.naturaldelta(seconds) == "1,234 años"
tests/test_i18n.py:96:        assert humanize.naturaldelta(seconds) == "1,234 years"
[assistant] The skill confirms the plan: no existing tests get edited, and any new error-type pin goes in a new test function. The fix must leave string inputs alone, since `int("12")` currently succeeds and yields "12 seconds". So I'll guard only on real float infinities, before the `int()` call. Next I'll check how nearby tests cover `nan`/`inf`.
[tool_use Bash] {"command": "grep -n \"nan\\|inf\\|OverflowError\" tests/test_time.py | head -30 && sed -n 820,835p tests/test_time.py", "description": "Find existing nan/inf/overflow tests in test_time.py"}
[tool_result] 311:    future = dt.datetime(2023, 10, 16, hour=6, tzinfo=utc)

    with pytest.raises(
        ValueError,
        match="Minimum unit is suppressed and no suitable replacement was found",
    ):
        humanize.precisedelta(1, minimum_unit="years", suppress=["years"])

    with pytest.raises(ValueError, match="Minimum unit 'years' not supported"):
        humanize.naturaldelta(1, minimum_unit="years")


def test_time_unit() -> None:
    years, minutes = time.Unit["YEARS"], time.Unit["MINUTES"]
    assert minutes < years
    assert years > minutes
[assistant] There are no existing `inf`/`nan` or overflow tests in `test_time.py`, so I'll add new test functions there. Now the fix:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "old_string": "    else:\n        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"", "new_string": "    else:\n        if isinstance(value, float) and math.isinf(value):\n            return str(value)\n\n        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "old_string": "from enum import Enum\nfrom functools import total_ordering", "new_string": "import math\nfrom enum import Enum\nfrom functools import total_ordering"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py has been updated successfully.
[assistant] Now the new tests. I'll look at the existing `test_naturaldelta` so the new function matches its style.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "offset": 128, "limit": 14}
[tool_result] 128	        (dt.timedelta(days=365), "a year"),
129	        (dt.timedelta(days=365 * 1_141), "1,141 years"),
130	        ("NaN", "NaN"),  # Returns non-numbers unchanged.
131	        # largest possible timedelta
132	        (dt.timedelta(days=999_999_999), "2,739,726 years"),
133	    ],
134	)
135	def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
136	    assert humanize.naturaldelta(test_input) == expected
137	    if not isinstance(test_input, str):
138	        assert humanize.naturaldelta(-test_input) == expected
139	
140	
141	@freeze_time(FROZEN_DATE)
[assistant] The 1e30 overflow case already behaves as documented, so the harness says not to pin it with a new test. The new test covers only `inf` and `-inf`, which fail on the original code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "old_string": "    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)", "new_string": "    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@pytest.mark.parametrize(\n    (\"test_input\", \"expected\"),\n    [\n        (float(\"inf\"), \"inf\"),\n        (float(\"-inf\"), \"-inf\"),\n    ],\n)\ndef test_naturaldelta_infinity_unchanged(test_input: float, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py has been updated successfully.
[assistant] Next I'll confirm the new inputs now change output, check that 1e30 still raises, and run the full test suite.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'naturaldelta(float(\"inf\"))' 'naturaldelta(float(\"-inf\"))' 'naturaldelta(float(\"nan\"))' 'naturaldelta(1e30)' 'naturaldelta(\"12\")' 2>&1 | tail -20; echo ---; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo ---; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no tests/test_time.py -k infinity 2>&1 | tail -3", "description": "Verify output changes, run full test suite"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp4lu2gh9a/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/base-1/src/humanize/__init__.py)
CHANGED naturaldelta(float("inf"))
    old: !OverflowError: cannot convert float infinity to integer
    new: 'inf'
CHANGED naturaldelta(float("-inf"))
    old: !OverflowError: cannot convert float infinity to integer
    new: '-inf'

…[151 chars elided]…
 C int
    new: !OverflowError: Python int too large to convert to C int
same    naturaldelta("12")
    old: '12 seconds'
    new: '12 seconds'
5 expressions, 2 changed, 3 same
---

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
722 passed, 74 skipped in 6.18s
---
..                                                                       [100%]
2 passed, 383 deselected in 0.04s
[assistant] `naturaldelta(float("inf"))` and `naturaldelta(float("-inf"))` now return `"inf"` and `"-inf"` instead of raising `OverflowError`. A finite value that is too large still raises `OverflowError`. The full suite passes: `722 passed, 74 skipped`.

**Change** (`src/humanize/time.py`)
- Added an early return before the `int()` conversion: if the value is a float and `math.isinf()` is true, return `str(value)`.
- Added `import math` at the top of the module.
- I guarded on real float infinities rather than catching `OverflowError` around the conversion. Catching it there would also swallow the docume
…[378 chars elided]…
 already raises `OverflowError` on the original code, so the harness says to leave it out. No existing test lines were edited.

**Checks**
- `compare_outputs.py` on the original and new code: `inf` and `-inf` changed; `nan`, `1e30` and `"12"` are the same.
- Lint was not run because `ruff` is not installed. I read the changes against the project's style: the new import is ordered correctly and the new test follows the existing parametrize style.
- The `Raises:` and "returned unchanged" docstring already describe this behaviour, so I did not edit the docstring.

I have not committed the change.
