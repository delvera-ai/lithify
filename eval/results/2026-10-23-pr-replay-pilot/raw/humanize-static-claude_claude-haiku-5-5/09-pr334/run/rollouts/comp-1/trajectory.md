# trajectory comp-1

final message:
`naturaldelta()` now returns `"inf"` and `"-inf"` for infinite floats instead of raising `OverflowError`. Finite values that are too large, such as `1e30`, still raise as documented.

**The fix** is in `src/humanize/time.py`. The conversion's `except` now catches `OverflowError` separately. If the value is `±inf`, it returns `str(value)`; otherwise it re-raises. I added a local `import math` at the top of the function, following the project's import convention.

**Tests:** I added `test_naturaldelta_infinite` in `tests/test_time.py`, beside `test_naturaldelta`, with `(inf, "inf")` and `(-inf, "-inf")`. It is a separate function because `test_naturaldelta` re-checks negated inputs, and `-inf` should return `"-inf"`.

**Verification:**
- **Before the edit:** `inf` and `-inf` raised `OverflowError`, which reproduces the report.
- **Output comparison** (`compare_outputs.py`, HEAD vs. working tree): only `naturaldelta(inf)` and `naturaldelta(-inf)` changed. `nan`, `1e30`, `-1e30` and `10**400` produce the same output as before, so I did not add tests for them. They already behaved correctly.
- **Full suite:** `722 passed, 74 skipped`.
- **Lint:** `lint_changed.py` reported `0 findings`. Ruff itself is not installed here, so it was not run.

The docstring already says non-convertible values are returned unchanged and that `OverflowError` is raised for values too large for `timedelta`, so I left it as it was.

**Not fixed:** `naturaltime(inf)`, `naturaltime(-inf)`, `precisedelta(inf)` and `precisedelta(-inf)` still raise the same `OverflowError`. The report named only `naturaldelta`, so I left them alone. They go through a different code path, and a fix there would be a separate change.

## events
[assistant] I'll start by reading `naturaldelta` and the harness memory file, since the project's checks and interpreter path are recorded there.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls .lithify/harness 2>/dev/null; cat .lithify/harness/memory.md 2>/dev/null; grep -n \"def naturaldelta\" -A 70 src/humanize/time.py", "description": "Check repo state, memory file, and naturaldelta source"}
[tool_use Skill] {"skill": "humanize-time-output"}
[tool_result] 011b6f2 lithify: probe base
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Tests: `@pytest.mark.parametrize` names are one csv string, `"test_input, expected"`, never a
  tuple (`[tool.ruff]` `parametrize-names-type = "csv"`, rule
…[2604 chars elided]…
= float(value)
153-            delta = dt.timedelta(seconds=value)
154-        except (ValueError, TypeError):
155-            return str(value)
156-
157-    use_months = months
158-
159-    delta = abs(delta)
160-    years = delta.days // 365
161-    days = delta.days % 365
162-    num_months = round(days / 30.5)
163-
164-    if years == 0 and days < 1:
165-        if delta.seconds == 0:
166-            if min_unit == Unit.MICROSECONDS and delta.microseconds < 1000:
167-                return (
[tool_result] Launching skill: humanize-time-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/.claude/skills/humanize-time-output

# Changing what a humanize time formatter returns

Check each item against your finished diff.

1. **Unconvertible input returns `str(value)`.** `naturaldelta` (the `try` around
   `int(value)` / `dt.timedelta(seconds=value)`) and `naturaltime` (via `_date_and_delta`, which
   returns `(None, value)`) hand back `str(value)` for input they cannot convert. That is not
   `number.py`'s `_format_not_finite` (`"NaN"`/`"+Inf"
…[206 chars elided]…
or `precisedelta`. Fix only
   the function the task names, and mention the others in the final message.
2. **Imports.** Follow the function-local import convention in memory.md.
3. **Tests.** Mind the negation re-check in `test_naturaldelta` (memory.md). Error cases use
   `pytest.raises(<Type>, match=...)` (see `test_time.py` near the `minimum_unit="years"` check).
4. **Docstring is the documentation.** `docs/*.md` are `::: humanize.<module>` mkdocstrings
   stubs. If behaviour now matches what the `Returns:`/`Raises:` text already says, leave it;
   if it no longer matches, edit that text.

[assistant] The skill's checklist says the fix belongs in `naturaldelta` only, with function-local imports and the docstring kept in sync. Next I'll reproduce the bug on the unmodified code using the harness script.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ls -la $PY; PYTHONPATH=src $PY -c \"\nfrom humanize import naturaldelta\nfor v in [float('nan'), float('inf'), float('-inf'), 1e30, '1e30', 'inf']:\n    try: print(repr(v), '->', repr(naturaldelta(v)))\n    except Exception as e: print(repr(v), 'RAISES', type(e).__name__, e)\n\"; sed -n 164,200p src/humanize/time.py", "description": "Reproduce inf/nan/huge behavior on unmodified code"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
nan -> 'nan'
inf RAISES OverflowError cannot convert float infinity to integer
-inf RAISES OverflowError cannot convert float infinity to integer
1e+30 RAISES OverflowError Python int too large to convert to C i
…[844 chars elided]…
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
[assistant] The bug reproduces: `inf` and `-inf` raise `OverflowError`, `nan` passes through, and `1e30` raises as documented. Next I'll check the existing import convention and the current inf/nan tests before editing.
[tool_use Bash] {"command": "sed -n 1,30p src/humanize/time.py; grep -n \"import math\" -B3 -A3 src/humanize/time.py; grep -n \"inf\\|nan\\|OverflowError\\|def test_naturaldelta\" tests/test_time.py | head -60", "description": "Check imports and existing inf/nan tests"}
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
…[132 chars elided]…
s", usecs),
641-    ]
642-
643:    import math
644-
645-    texts: list[str] = []
646-    for unit, fmt in zip(reversed(Unit), fmts):
88:def test_naturaldelta_nomonths(test_input: dt.timedelta, expected: str) -> None:
135:def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
311:    future = dt.datetime(2023, 10, 16, hour=6, tzinfo=utc)
343:def test_naturaldelta_minimum_unit_default(seconds: float, expected: str) -> None:
386:def test_naturaldelta_minimum_unit_explicit(
[tool_use Bash] {"command": "sed -n 60,160p tests/test_time.py; grep -n \"raises\" -B6 -A4 tests/test_time.py | head -60", "description": "Read naturaldelta tests and raises patterns"}
[tool_result] def test_date_and_delta() -> None:
    now = dt.datetime.now()
    td = dt.timedelta
    int_tests = (3, 29, 86399, 86400, 86401 * 30)
    date_tests = [now - td(seconds=x) for x in int_tests]
    td_tests = [td(seconds=x) for x in int_tests]
    results = [(now - td(seconds=x), td(seconds=x)) for x in int_tests]
    for t in (int_tests, date_tests, td_tests):
        for arg, result in zip(t, results):
            date, d = time._date_and_delta(arg)
            assert_equal_datetime(date, resul
…[4189 chars elided]…
humanize.precisedelta(1, minimum_unit="years", suppress=["years"])
826-
827:    with pytest.raises(ValueError, match="Minimum unit 'years' not supported"):
828-        humanize.naturaldelta(1, minimum_unit="years")
829-
830-
831-def test_time_unit() -> None:
832-    years, minutes = time.Unit["YEARS"], time.Unit["MINUTES"]
833-    assert minutes < years
834-    assert years > minutes
835-
836:    with pytest.raises(TypeError):
837-        _ = years < "foo"
838-
839-
840-@pytest.mark.parametrize(
[assistant] Before editing, I'll use the harness's comparison script to check which candidate inputs actually change output. Per the project rules, only inputs whose output changes go into tests.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py \"naturaldelta(float('inf'))\" \"naturaldelta(float('-inf'))\" \"naturaldelta(float('nan'))\" \"naturaldelta(1e30)\" \"naturaldelta(-1e30)\" 2>&1; echo \"exit=$?\"", "description": "Compare candidate test inputs on HEAD vs working tree"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpzg0yebb4/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/__init__.py)
same    naturaldelta(float('inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: !OverflowError: cannot convert float infinity to integer
same    naturaldelta(float('-inf'))
    old: !OverflowError: cannot
…[24 chars elided]…
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
[assistant] The first run is on the unmodified tree, so "same" everywhere is expected. I'll re-run it after the edit to confirm that only `±inf` change. Now the fix, placed in the `naturaldelta` function only, with `math` imported locally as the project requires:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/time.py", "old_string": "    import datetime as dt\n\n    tmp = Unit[minimum_unit.upper()]", "new_string": "    import datetime as dt\n    import math\n\n    tmp = Unit[minimum_unit.upper()]"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/time.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/time.py", "old_string": "            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeError):\n            return str(value)\n\n    use_months = months", "new_string": "            delta = dt.timedelta(seconds=value)\n        except OverflowError:\n            # int(inf) raises OverflowError: return infinities unchanged, but a finite\n            # value too large for timedelta must still raise.\n            if value in (math.inf, -math.inf):\n                return str(value)\n            raise\n        except (ValueError, TypeError):\n            return str(value)\n\n    use_months = months"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/time.py has been updated successfully.
[assistant] Next, the tests. `-inf` should return `"-inf"`, not `"inf"`, so the sign-dependent cases go in a new function beside `test_naturaldelta`, as the project's notes require. I'm adding only the `±inf` cases, since they are the only inputs whose output changes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/tests/test_time.py", "old_string": "    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)", "new_string": "    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@pytest.mark.parametrize(\n    \"test_input, expected\",\n    [\n        (float(\"inf\"), \"inf\"),\n        (float(\"-inf\"), \"-inf\"),\n    ],\n)\ndef test_naturaldelta_infinite(test_input: float, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n\n\n@freeze_time(FROZEN_DATE)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/tests/test_time.py has been updated successfully.
[assistant] Now I'll check the result three ways: the old-vs-new comparison, the full test suite, and the lint script.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py \"naturaldelta(float('inf'))\" \"naturaldelta(float('-inf'))\" \"naturaldelta(float('nan'))\" \"naturaldelta(1e30)\" \"naturaldelta(-1e30)\" \"naturaldelta(10**400)\" 2>&1; echo \"compare exit=$?\"; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"pytest exit=${PIPESTATUS[0]}\"; $PY .lithify/harness/scripts/lint_changed.py 2>&1 | tail -3; echo \"lint exit=$?\"", "description": "Run output comparison, full tests, and lint check"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp3z5d0l9l/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/comp-1/src/humanize/__init__.py)
CHANGED naturaldelta(float('inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: 'inf'
CHANGED naturaldelta(float('-inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: '-inf'

…[371 chars elided]…
ert to C int
same    naturaldelta(10**400)
    old: !OverflowError: int too large to convert to float
    new: !OverflowError: int too large to convert to float
6 expressions, 2 changed, 4 same
compare exit=0

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
722 passed, 74 skipped in 6.11s
pytest exit=
rules checked: EM101, EM102, PT006
0 findings in 2 changed files
lint exit=0
[assistant] The changed outputs are exactly `±inf`; `nan`, `1e30`, and `10**400` are unchanged. All tests pass and lint reports 0 findings. Last, I'll check whether the sibling functions share the bug, so I can report it accurately.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nimport humanize\nfor f in ['naturaltime','precisedelta']:\n    for v in [float('inf'), float('-inf')]:\n        try: print(f, v, repr(getattr(humanize,f)(v)))\n        except Exception as e: print(f, v, 'RAISES', type(e).__name__, e)\n\"; git diff --stat", "description": "Check sibling time functions on infinite input"}
[tool_result] naturaltime inf RAISES OverflowError cannot convert float infinity to integer
naturaltime -inf RAISES OverflowError cannot convert float infinity to integer
precisedelta inf RAISES OverflowError cannot convert float infinity to integer
precisedelta -inf RAISES OverflowError cannot convert float infinity to integer
 src/humanize/time.py |  7 +++++++
 tests/test_time.py   | 11 +++++++++++
 2 files changed, 18 insertions(+)
[assistant] `naturaldelta()` now returns `"inf"` and `"-inf"` for infinite floats instead of raising `OverflowError`. Finite values that are too large, such as `1e30`, still raise as documented.

**The fix** is in `src/humanize/time.py`. The conversion's `except` now catches `OverflowError` separately. If the value is `±inf`, it returns `str(value)`; otherwise it re-raises. I added a local `import math` at the top of the function, following the project's import convention.

**Tests:** I added `test_naturaldelta_infinite` in `tests/test_time.py`, beside `test_naturaldelta`, with `(inf, "inf")` and `(-inf, 
…[508 chars elided]…
Full suite:** `722 passed, 74 skipped`.
- **Lint:** `lint_changed.py` reported `0 findings`. Ruff itself is not installed here, so it was not run.

The docstring already says non-convertible values are returned unchanged and that `OverflowError` is raised for values too large for `timedelta`, so I left it as it was.

**Not fixed:** `naturaltime(inf)`, `naturaltime(-inf)`, `precisedelta(inf)` and `precisedelta(-inf)` still raise the same `OverflowError`. The report named only `naturaldelta`, so I left them alone. They go through a different code path, and a fix there would be a separate change.
