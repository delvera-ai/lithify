# trajectory dom-1

final message:
`naturaldelta(float("inf"))` and `naturaldelta(float("-inf"))` now return `"inf"` and `"-inf"` instead of raising `OverflowError`. The full suite passes (`722 passed, 74 skipped`).

**Cause:** `naturaldelta` calls `int(value)` as a guard, and `int(inf)` raises `OverflowError`. The surrounding `except (ValueError, TypeError)` didn't catch it.

**Fix** (`src/humanize/time.py`): the `int()` guard now has its own `try` that also catches `OverflowError` and returns `str(value)`. The float and timedelta conversion keeps its original handling, so a finite value that's too large (`1e30`, `-1e30`, `10**400`) still raises `OverflowError`.

**Tests** (`tests/test_time.py`): I added `test_naturaldelta_non_finite` with `inf` and `-inf` cases, next to `test_naturaldelta`. I didn't add them to `test_naturaldelta`, because it also checks the negated input and `-inf` gives `"-inf"`, not `"inf"`.

**Verification:**
- **Before the edit:** on the unmodified code, `inf` and `-inf` raised `OverflowError`, while `nan` returned `'nan'` and `1e30` raised.
- **Old vs new output** (`compare_outputs.py`, 19 expressions): 4 changed, all intended (`inf` and `-inf`, with and without `minimum_unit`). `nan`, `-nan`, `"inf"`, `"-inf"`, `"nan"`, `"5"`, `b"5"`, `None`, `5`, `30.5` and every too-large finite value are unchanged. The `object()` entry differs only in its memory address.
- **Not added as tests:** the `1e30` case still raises. Its output is unchanged, so per the harness I left it out of the test file rather than pinning existing behaviour.
- **Lint:** not run, because `ruff` isn't installed. I checked the added lines against the default 88-character limit by hand, and none exceed it.

**Not fixed:** `naturaltime(float("inf"))` and `precisedelta(float("inf"))` raise the same `OverflowError`. You only asked for `naturaldelta`, so I left them alone. They would need their own fix, which I can make if you want it.

## events
[assistant] I'll start by reading the current `naturaldelta` code and the time-output skill the project harness points to.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"def \\|nan\\|inf\\|OverflowError\\|isfinite\" src/humanize/time.py | head -80 && cat <work>/memory.md 2>/dev/null | head -20; ls .claude 2>/dev/null; ls .lithify/harness 2>/dev/null", "description": "Inspect time.py, repo state and harness files"}
[tool_result] f171297 lithify: probe base
43:    def __lt__(self, other: Any) -> Any:
49:def _now() -> dt.datetime:
55:def _abs_timedelta(delta: dt.timedelta) -> dt.timedelta:
70:def _date_and_delta(
97:def naturaldelta(
117:            converted to int (cannot be float due to 'inf' or 'nan').
121:        OverflowError: If `value` is too large to convert to datetime.timedelta.
151:            int(value)  # Explicitly don't support string such as "NaN" or "inf"
251:def naturaltime(
302:def _convert_aware_datet
…[440 chars elided]…
) and value.tzinfo is not None:
361:            today = dt.datetime.now(value.tzinfo).date()
368:    except (OverflowError, ValueError):
377:def _quotient_and_remainder(
422:def _suitable_minimum_unit(min_unit: Unit, suppress: Iterable[Unit]) -> Unit:
451:def _suppress_lower_units(min_unit: Unit, suppress: Iterable[Unit]) -> set[Unit]:
467:def precisedelta(
674:def _rounding_by_fmt(format: str, value: float) -> float | int:
skills
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "ls -a && find / -name \"humanize-time-output*\" -not -path \"*/proc/*\" 2>/dev/null | head; ls .lithify 2>/dev/null", "description": "Check git status, skill files and harness scripts"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bkt51n2w2). Output is being written to: <tmp>/-Users-user--cache-lithify-work-repo-591a89d5b953-20261023-150818-bug-humanize-naturaldelta-docume-dom-1/d3fc9cba-ea14-4242-818e-7bba0a979b32/tasks/bkt51n2w2.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The broad `find /` got backgrounded, so I'll stop it and read the files directly.
[tool_use Bash] {"command": "pkill -f \"find / -name\" 2>/dev/null; ls -a; ls .claude/skills .lithify/harness/skills .lithify/harness/scripts 2>/dev/null; sed -n 1,160p src/humanize/time.py", "description": "Read the naturaldelta implementation"}
[tool_result] .
..
.agents
.claude
.git
.github
.gitignore
.lithify
.pre-commit-config.yaml
.readthedocs.yml
.yamlfmt.yaml
AGENTS.md
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
.claude/skills:
humanize-error-contract
humanize-number-output
humanize-time-output

.lithify/harness/scripts:
compare_outputs.py

.lithify/harness/skills:
humanize-error-contract
humanize-number-output
humanize-time-output
"""Time humanizing functions.

These 
…[3690 chars elided]…
  msg = f"Minimum unit '{minimum_unit}' not supported"
        raise ValueError(msg)
    min_unit = tmp

    if isinstance(value, dt.timedelta):
        delta = value
    else:
        try:
            int(value)  # Explicitly don't support string such as "NaN" or "inf"
            value = float(value)
            delta = dt.timedelta(seconds=value)
        except (ValueError, TypeError):
            return str(value)

    use_months = months

    delta = abs(delta)
    years = delta.days // 365
[assistant] The task notification is from the backgrounded `find`, which I'd already stopped, so it doesn't change anything. Next I'll read the time-output skill, the rest of `naturaldelta`, and check the project interpreter.
[tool_use Bash] {"command": "sed -n 160,250p src/humanize/time.py; echo ----; cat .claude/skills/humanize-time-output/SKILL.md 2>/dev/null || ls -R .claude/skills; echo ----; ls -la <work>/env-humanize/bin/python 2>&1", "description": "Read rest of naturaldelta, skill doc and interpreter path"}
[tool_result]     years = delta.days // 365
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
                min_unit == Unit.MICROSECOND
…[4014 chars elided]…
ocumentation.** `docs/*.md` are `::: humanize.<module>` mkdocstrings
   stubs. If behaviour now matches what the `Returns:`/`Raises:` text already says, leave it;
   if it no longer matches, edit that text.
----
lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
[assistant] The bug is in `naturaldelta`'s `int(value)` guard: `int(float("inf"))` raises `OverflowError`, which the `except (ValueError, TypeError)` doesn't catch. Before changing anything, I'll reproduce it on the unmodified tree and check the existing tests.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import naturaldelta\nfor v in [float('nan'), float('inf'), float('-inf'), 1e30, 'inf', 'nan', b'5', '5']:\n    try: print(repr(v), '->', repr(naturaldelta(v)))\n    except Exception as e: print(repr(v), 'RAISES', type(e).__name__, e)\n\"; echo ---; grep -n \"nan\\|inf\\|Overflow\\|def test_naturaldelta\" tests/test_time.py | head -40; echo ---; sed -n 1,40p .lithify/harness/scripts/compare_outputs.py | head -60", "description": "Reproduce bug on unmodified code and inspect tests"}
[tool_result] nan -> 'nan'
inf RAISES OverflowError cannot convert float infinity to integer
-inf RAISES OverflowError cannot convert float infinity to integer
1e+30 RAISES OverflowError Python int too large to convert to C int
'inf' -> 'inf'
'nan' -> 'nan'
b'5' -> '5 seconds'
'5' -> '5 seconds'
---
88:def test_naturaldelta_nomonths(test_input: dt.timedelta, expected: str) -> None:
135:def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
311:    future = dt.datetime(2023, 10, 16, ho
…[1437 chars elided]…
hatever the count); 2 = setup failure (not a git repo, bad
revision, import from the wrong place, no expressions). Nothing is written outside a temp dir.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RUNNER = r"""
import json, os, sys
pkg, expected_root = sys.argv[1], os.path.realpath(sys.argv[2])
mod = __import__(pkg)
where = os.path.realpath(getattr(mod, "__file__", "") or "")
[assistant] Reproduced: `inf` and `-inf` raise `OverflowError`, while `nan` returns `'nan'` and `1e30` raises as documented. Now I'll look at the existing parametrized test to see where the new cases go.
[tool_use Bash] {"command": "sed -n 95,150p tests/test_time.py; grep -n \"raises\" tests/test_time.py | head", "description": "Read naturaldelta test cases"}
[tool_result]         (0, "a moment"),
        (1, "a second"),
        (23.5, "23 seconds"),
        (30, "30 seconds"),
        (dt.timedelta(microseconds=13), "a moment"),
        (dt.timedelta(minutes=1, seconds=29), "a minute"),
        (dt.timedelta(minutes=1, seconds=30), "2 minutes"),
        (dt.timedelta(minutes=1, seconds=59), "2 minutes"),
        (dt.timedelta(minutes=2), "2 minutes"),
        (dt.timedelta(minutes=59), "59 minutes"),
        (dt.timedelta(minutes=59, seconds=30), "an hour"),
   
…[1726 chars elided]…
ected",
    [
        (NOW, "now"),
        (NOW - dt.timedelta(seconds=1), "a second ago"),
        (NOW - dt.timedelta(seconds=30), "30 seconds ago"),
        (NOW - dt.timedelta(minutes=1, seconds=29), "a minute ago"),
        (NOW - dt.timedelta(minutes=1, seconds=30), "2 minutes ago"),
        (NOW - dt.timedelta(minutes=2), "2 minutes ago"),
821:    with pytest.raises(
827:    with pytest.raises(ValueError, match="Minimum unit 'years' not supported"):
836:    with pytest.raises(TypeError):
[assistant] Following the harness: `float("inf")` doesn't belong in `test_naturaldelta` because its negation `-inf` gives a different string, so the new cases go in a separate parametrized function. The fix will keep the `try` for the float/timedelta conversion untouched, so `1e30` still raises from `timedelta`. I'm making the edit now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/dom-1/src/humanize/time.py", "old_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeEr
…[43 chars elided]…
_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n        except (ValueError, TypeError, OverflowError):  # OverflowError: float(\"inf\")\n            return str(value)\n        try:\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeError):\n            return str(value)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/dom-1/src/humanize/time.py has been updated successfully.
[assistant] Now I'll compare old and new output on a set of inputs with the project's harness script, which evaluates HEAD and the working tree in separate subprocesses.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py \"naturaldelta(float('inf'))\" \"naturaldelta(float('-inf'))\" \"naturaldelta(float('nan'))\" \"naturaldelta(1e30)\" \"naturaldelta(-1e30)\" \"naturaldelta(10**400)\" \"naturaldelt
…[43 chars elided]…
)\" \"naturaldelta('inf')\" \"naturaldelta('nan')\" \"naturaldelta('5')\" \"naturaldelta(b'5')\" \"naturaldelta(None)\" \"naturaldelta(5)\" \"naturaldelta(30.5)\" \"naturaldelta(float('-nan'))\" \"naturaldelta('-inf')\" \"naturaldelta(object())\" \"naturaldelta(1e18)\" \"naturaldelta(1e30, minimum_unit='x')\"; echo \"exit=$?\"", "description": "Compare naturaldelta output on HEAD vs working tree"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp83jue4yd/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/dom-1/src/humanize/__init__.py)
CHANGED naturaldelta(float('inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: 'inf'
CHANGED naturaldelta(float('-inf'))
    old: !OverflowError: cannot convert float infinity to integer
    new: '-inf'
s
…[1160 chars elided]…

    old: 'nan'
    new: 'nan'
same    naturaldelta('-inf')
    old: '-inf'
    new: '-inf'
CHANGED naturaldelta(object())
    old: '<object object at 0x1010fc650>'
    new: '<object object at 0x100b94630>'
same    naturaldelta(1e18)
    old: !OverflowError: Python int too large to convert to C int
    new: !OverflowError: Python int too large to convert to C int
same    naturaldelta(1e30, minimum_unit='x')
    old: !KeyError: 'X'
    new: !KeyError: 'X'
19 expressions, 4 changed, 15 same
exit=0
[assistant] The four changed results are the intended ones: `inf` and `-inf` now return their string (with and without `minimum_unit`). `1e30`, `-1e30`, `10**400` and `1e18` still raise `OverflowError`. The `object()` "change" is only the memory address in `str(object())`, so it's noise, not a real change. Next I'll add tests for the new cases, placed after `test_naturaldelta`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/dom-1/tests/test_time.py", "old_string": "def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-t
…[176 chars elided]…
ted\n    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-test_input) == expected\n\n\n@pytest.mark.parametrize(\n    \"test_input, expected\",\n    [\n        (float(\"inf\"), \"inf\"),\n        (float(\"-inf\"), \"-inf\"),\n    ],\n)\ndef test_naturaldelta_non_finite(test_input: float, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150818-bug-humanize-naturaldelta-docume/dom-1/tests/test_time.py has been updated successfully.
[assistant] Now the full check the harness specifies, which I'll read to the summary line:
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"---targeted\"; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no tests/test_time.py -k \"non_finite\" 2>&1 | tail -3; echo ---; git diff", "description": "Run full test suite and show the diff"}
[tool_result] test_intcomma           452.0749 (3.50)        38,139.6007 (35.18)      502.4719 (3.52)        194.9425 (9.55)       487.4993 (3.50)      15.6004 (536.02)   606;4446    1,990.1611 (0.28)      52403          40
test_naturaldelta       499.9747 (3.87)        27,999.9804 (25.83)      631.1600 (4.43)        203.3334 (9.96)       625.0048 (4.49)       0.0291 (1.0)     379;48291    1,584.3843 (0.23)     129736           1
test_naturalsize        499.9747 (3.87)        38,666.0104 (35.66)      619.3237
…[2636 chars elided]…
_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
         assert humanize.naturaldelta(-test_input) == expected
 
 
+@pytest.mark.parametrize(
+    "test_input, expected",
+    [
+        (float("inf"), "inf"),
+        (float("-inf"), "-inf"),
+    ],
+)
+def test_naturaldelta_non_finite(test_input: float, expected: str) -> None:
+    assert humanize.naturaldelta(test_input) == expected
+
+
 @freeze_time(FROZEN_DATE)
 @pytest.mark.parametrize(
     "test_input, expected",
[assistant] The full suite passes: `722 passed, 74 skipped`. Ruff isn't installed here, so I'll check the new lines' length against the project's configured limit by hand.
[tool_use Bash] {"command": "grep -n \"line-length\\|line_length\" pyproject.toml; git diff -U0 | grep '^+' | awk '{ if (length($0)-1 > 88) print length($0)-1\": \"$0 }'; echo \"max-check-done\"", "description": "Check changed lines against line-length limit"}
[tool_result] max-check-done
[assistant] No added line exceeds 88 characters. The skill notes that `naturaltime` and `precisedelta` take a different path, so I'll check whether they share this bug before reporting.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import naturaltime, precisedelta\nfor f in [lambda: naturaltime(float('inf')), lambda: precisedelta(float('inf'))]:\n    try: print(repr(f()))\n    except Exception as e: print('RAISES', type(e).__name__, e)\n\"", "description": "Check naturaltime and precisedelta on infinity"}
[tool_result] RAISES OverflowError cannot convert float infinity to integer
RAISES OverflowError cannot convert float infinity to integer
[assistant] `naturaldelta(float("inf"))` and `naturaldelta(float("-inf"))` now return `"inf"` and `"-inf"` instead of raising `OverflowError`. The full suite passes (`722 passed, 74 skipped`).

**Cause:** `naturaldelta` calls `int(value)` as a guard, and `int(inf)` raises `OverflowError`. The surrounding `except (ValueError, TypeError)` didn't catch it.

**Fix** (`src/humanize/time.py`): the `int()` guard now has its own `try` that also catches `OverflowError` and returns `str(value)`. The float and timedelta conversion keeps its original handling, so a finite value that's too large (`1e30`, `-1e30`, `10*
…[718 chars elided]…
`object()` entry differs only in its memory address.
- **Not added as tests:** the `1e30` case still raises. Its output is unchanged, so per the harness I left it out of the test file rather than pinning existing behaviour.
- **Lint:** not run, because `ruff` isn't installed. I checked the added lines against the default 88-character limit by hand, and none exceed it.

**Not fixed:** `naturaltime(float("inf"))` and `precisedelta(float("inf"))` raise the same `OverflowError`. You only asked for `naturaldelta`, so I left them alone. They would need their own fix, which I can make if you want it.
