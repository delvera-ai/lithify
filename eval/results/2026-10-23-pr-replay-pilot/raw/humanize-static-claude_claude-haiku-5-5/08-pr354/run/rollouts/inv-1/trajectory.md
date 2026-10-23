# trajectory inv-1

final message:
`humanize.fractional()` now returns plain integers when the fractional part rounds to a whole number. The five reported inputs give `"3"`, `"1"`, `"0"`, and the negative cases give `"-3"` and `"-1"`.

**Cause:** the function only returned a plain integer when the fractional numerator was zero. A fractional part that limits to `1/1` or `-1/1` got past that check and produced `"2 1/1"`-style output.

**Fix** (`src/humanize/number.py`): the check now looks at the denominator. If the fractional part is a whole number (0 or ±1), the function returns `whole_number + numerator` as an integer. This also covers ordinary integers like `5` and `-7`, which the old branch already handled.

**Tests** (`tests/test_number.py`): I added five cases to the existing `test_fractional` list: `0`, `2.9999999`, `0.9999999`, `-0.9999999`, `-2.9999999`. I reproduced the bug on the unmodified code first, and each of these five changes output. I did not add the `1.0000001` and `0.9996` cases, because `1.0000001` already returned `"1"` and `0.9996` is covered by the same rounding.

**Verification:**
- Old-vs-new comparison on 17 expressions: 9 changed, all of them degenerate or rounding cases (for example `-1.9999999` went from `"-1 1/1"` to `"-2"`). The ordinary outputs (`1 1/2`, `-1 3/10`, `3/10`, `333/1000`, `-0.5`) are unchanged.
- Full test run: 720 passed, 74 skipped, no failures.
- Lint was not run: ruff isn't installed in this environment. I checked the changed lines by hand against the project's line length; the longest is 87 characters.

I haven't committed anything.

## events
[assistant] I'll start by reading the current `fractional` implementation and the project's skill for number output.
[tool_use Bash] {"command": "git status --short && grep -n \"def fractional\" -A 80 src/humanize/number.py | head -120 && ls .lithify/harness/ 2>/dev/null; ls <work>/env-humanize/bin/python 2>&1"}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/.claude/skills/humanize-number-output/SKILL.md"}
[tool_result] 1	---
2	name: humanize-number-output
3	description: Load when a task fixes or changes the string a number/filesize formatter returns (fractional, intword, intcomma, apnumber, ordinal, scientific, clamp, metric in src/humanize/number.py, or naturalsize in filesize.py), e.g. wrong output for negative, zero, float or string inputs.
4	---
5	
6	# Changing what a humanize number formatter returns
7	
8	Check each item against your finished diff.
9	
10	1. **Input guard stays first.** Every public functi
…[1498 chars elided]…
g `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
29	   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
30	   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
31	   change alters an output that an `Examples:` block shows, edit that block by hand. The
32	   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
33	   published documentation.
34	
[tool_result] 311:def fractional(value: NumberOrString) -> str:
312-    """Convert to fractional number.
313-
314-    There will be some cases where one might not want to show ugly decimal places for
315-    floats and decimals.
316-
317-    This function returns a human-readable fractional number in form of fractions and
318-    mixed fractions.
319-
320-    Pass in a string, or a number or a float, and this function returns:
321-
322-    * a string representation of a fraction
323-    * or a whole number
32
…[1923 chars elided]…
 z.wq x 10ⁿ.
382-
383-    Examples:
384-        ```pycon
385-        >>> scientific(float(0.3))
386-        '3.00 x 10⁻¹'
387-        >>> scientific(int(500))
388-        '5.00 x 10²'
389-        >>> scientific(-1000)
390-        '-1.00 x 10³'
391-        >>> scientific(1000, 1)
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
<work>/env-humanize/bin/python
[assistant] The project skill points at `number.py`'s `fractional` and asks for a reproduction on the unmodified code first. I'll check the interpreter note, the existing `fractional` tests, and the compare script's usage.
[tool_use Bash] {"command": "cat .lithify/harness/memory.md; echo ---; grep -n \"fractional\" -B3 -A40 tests/test_number.py | head -120; echo ---; ls .lithify/harness/scripts; sed -n 1,40p .lithify/harness/scripts/compare_outputs.py"}
[tool_result] - The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
---
189-        (-0.5, "-1/2"),
190-    ],
191-)
192:def test_fractional(test_input: float | str, expected: str) -> None:
193:    assert humanize.fractional(test_input) == expected
194-
195-
196-@pytest.mark.parametrize(
197-    "test_args, expected",
…[2475 chars elided]…
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
[tool_use Bash] {"command": "sed -n 170,192p tests/test_number.py; PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0)' 'fractional(0.0)' 'fractional(-0.5)' 'fractional(1.0000001)' 'fractional(0.9996)' 'fractional(-1.9999999)' 'fractional(-0.0)'"}
[tool_result]         (1, "1"),
        (2.0, "2"),
        (4.0 / 3.0, "1 1/3"),
        (5.0 / 6.0, "5/6"),
        ("7", "7"),
        ("8.9", "8 9/10"),
        ("ten", "ten"),
        (None, "None"),
        (1 / 3, "1/3"),
        (1.5, "1 1/2"),
        (0.3, "3/10"),
        (0.333, "333/1000"),
        (math.nan, "NaN"),
        (math.inf, "+Inf"),
        (-math.inf, "-Inf"),
        ("nan", "NaN"),
        ("-inf", "-Inf"),
        (-1.3, "-1 3/10"),
        (-2.5, "-2 1/2"),
        (-0.5, "-1/2")
…[584 chars elided]…
/1'
same    fractional(-0.9999999)
    old: '-1/1'
    new: '-1/1'
same    fractional(-0)
    old: '0/1'
    new: '0/1'
same    fractional(0.0)
    old: '0/1'
    new: '0/1'
same    fractional(-0.5)
    old: '-1/2'
    new: '-1/2'
same    fractional(1.0000001)
    old: '1'
    new: '1'
same    fractional(0.9996)
    old: '1/1'
    new: '1/1'
same    fractional(-1.9999999)
    old: '-1 1/1'
    new: '-1 1/1'
same    fractional(-0.0)
    old: '0/1'
    new: '0/1'
12 expressions, 0 changed, 12 same
[assistant] Reproduced on the unmodified code: all five reported inputs give the degenerate output (`'2 1/1'`, `'1/1'`, `'0/1'`, and the negative variants). No existing test pins `0/1`, so the fix doesn't conflict with anything.

The cause is that the code only special-cases a whole number when the fractional numerator is zero. A fractional part that limits to `1/1` or `-1/1` slips past that check. The fix is to check the denominator first: if the fractional part is an integer, fold it into the whole part and return a plain integer.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/src/humanize/number.py", "old_string": "    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{whole_number:.0f}\"", "new_string": "    if denominator == 1:\n        # the fractional part is a whole number: an integer was passed in (or a variant\n        # like 1.0000), or it rounded to 0 or \u00b11 (e.g. 2.9999999 -> 3)\n        return f\"{whole_number + numerator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (0, \"0\"),\n        (2.9999999, \"3\"),\n        (0.9999999, \"1\"),\n        (-0.9999999, \"-1\"),\n        (-2.9999999, \"-3\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/tests/test_number.py has been updated successfully.
[assistant] Now I'll confirm the new outputs against the original code, run the full test suite, and check the other `fractional` outputs for regressions.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0)' 'fractional(0.0)' 'fractional(-0.5)' 'fractional(1.0000001)' 'fractional(0.9996)' 'fractional(-1.9999999)' 'fractional(1.5)' 'fractional(-1.3)' 'fractional(5)' 'fractional(-7)' 'fractional(0.3)' 'fractional(0.333)'; echo ===; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result ERROR] Exit code 1
old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp29q_nrxd/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/inv-1/src/humanize/__init__.py)
CHANGED fractional(2.9999999)
    old: '2 1/1'
    new: '3'
CHANGED fractional(0.9999999)
    old: '1/1'
    new: '1'
CHANGED fractional(0)
    old: '0/1'
    new: '0'
CHANGED fractional(-2.9999999)
    old: '-2 1/1'
    ne
…[301 chars elided]…
al(0.9996)
    old: '1/1'
    new: '1'
CHANGED fractional(-1.9999999)
    old: '-1 1/1'
    new: '-2'
same    fractional(1.5)
    old: '1 1/2'
    new: '1 1/2'
same    fractional(-1.3)
    old: '-1 3/10'
    new: '-1 3/10'
same    fractional(5)
    old: '5'
    new: '5'
same    fractional(-7)
    old: '-7'
    new: '-7'
same    fractional(0.3)
    old: '3/10'
    new: '3/10'
same    fractional(0.333)
    old: '333/1000'
    new: '333/1000'
17 expressions, 9 changed, 8 same
(eval):1: == not found
[assistant] The comparison shows only the degenerate cases changed; the ordinary outputs (`1 1/2`, `-1 3/10`, `3/10`, `333/1000`, `-7`) are unchanged. The `exit code 1` came from my `echo ===` line, which the shell parsed as an assignment, so I'll rerun the test suite on its own.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit=$?\"; git diff"}
[tool_result] test_intcomma           416.0102 (3.19)        55,584.0088 (12.00)      532.8203 (3.60)        349.4832 (7.76)       540.9820 (3.74)      41.9968 (41.23)     427;4363    1,876.8054 (0.28)     180440           1
test_naturalsize        540.9820 (4.15)       192,417.0065 (41.56)      779.3137 (5.26)      1,261.9074 (28.01)      667.0016 (4.61)      42.0259 (41.26)     321;7667    1,283.1803 (0.19)      71003           1
test_naturaldelta       542.0006 (4.16)        46,499.9757 (10.04)      682.53
…[2712 chars elided]…
/test_number.py b/tests/test_number.py
index 78639c3..7b9b4a4 100644
--- a/tests/test_number.py
+++ b/tests/test_number.py
@@ -187,6 +187,11 @@ def test_apnumber(test_input: int | str, expected: str) -> None:
         (-1.3, "-1 3/10"),
         (-2.5, "-2 1/2"),
         (-0.5, "-1/2"),
+        (0, "0"),
+        (2.9999999, "3"),
+        (0.9999999, "1"),
+        (-0.9999999, "-1"),
+        (-2.9999999, "-3"),
     ],
 )
 def test_fractional(test_input: float | str, expected: str) -> None:
[assistant] The full suite passes (720 passed, 74 skipped, no failures). The `exit=0` above is from `tail`, not pytest, but the summary line shows no failures. Ruff isn't installed here, so I'll check the changed lines against the configured line length and look for non-ASCII characters by hand.
[tool_use Bash] {"command": "grep -n \"line-length\\|RUF\\|select\" pyproject.toml | head; awk 'NR>=362 && NR<=366 {print NR\": \"length($0)}' src/humanize/number.py; grep -nP '[^\\x00-\\x7F]' src/humanize/number.py | sed -n 1,3p"}
[tool_result] 60:lint.select = [
75:  "RUF022", # unsorted-dunder-all
76:  "RUF046", # unnecessary-cast-to-int
77:  "RUF100", # unused noqa (yesqa)
362: 30
363: 34
364: 24
365: 87
366: 71
24:    "0": "⁰",
25:    "1": "¹",
26:    "2": "²",
[assistant] `humanize.fractional()` now returns plain integers when the fractional part rounds to a whole number. The five reported inputs give `"3"`, `"1"`, `"0"`, and the negative cases give `"-3"` and `"-1"`.

**Cause:** the function only returned a plain integer when the fractional numerator was zero. A fractional part that limits to `1/1` or `-1/1` got past that check and produced `"2 1/1"`-style output.

**Fix** (`src/humanize/number.py`): the check now looks at the denominator. If the fractional part is a whole number (0 or ±1), the function returns `whole_number + numerator` as an integer. This al
…[374 chars elided]…
ases, because `1.0000001` already returned `"1"` and `0.9996` is covered by the same rounding.

**Verification:**
- Old-vs-new comparison on 17 expressions: 9 changed, all of them degenerate or rounding cases (for example `-1.9999999` went from `"-1 1/1"` to `"-2"`). The ordinary outputs (`1 1/2`, `-1 3/10`, `3/10`, `333/1000`, `-0.5`) are unchanged.
- Full test run: 720 passed, 74 skipped, no failures.
- Lint was not run: ruff isn't installed in this environment. I checked the changed lines by hand against the project's line length; the longest is 87 characters.

I haven't committed anything.
