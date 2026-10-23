# trajectory base-1

final message:
`humanize.fractional()` now returns a plain integer when the fractional part rounds to a whole number. `fractional(2.9999999)` gives `"3"`, `fractional(0.9999999)` gives `"1"`, and `fractional(0)` gives `"0"`. Negative inputs follow the same rule: `-2.9999999` gives `"-3"` and `-0.9999999` gives `"-1"`.

**Cause:** `Fraction(...).limit_denominator(1000)` can round the fractional part to exactly ±1, and the code never folded that back into the whole part. The zero case failed because the integer branch required a non-zero whole part.

**Change (`src/humanize/number.py`):**
- If the rounded fraction is ±1, add it to the whole part and reset the fraction to 0.
- The integer branch now fires whenever the numerator is 0 and the denominator is 1, including when the whole part is 0.

**Tests (`tests/test_number.py`):** I added five cases to the existing `test_fractional` parametrize list: `0`, `2.9999999`, `0.9999999`, `-2.9999999` and `-0.9999999`. I reproduced the bug on the unmodified code first, and all five outputs changed with the fix.

**Verification:** The full suite passes (`720 passed, 74 skipped`). Ruff isn't installed in the project's venv, so I did not lint.

**Behaviour change beyond the reported inputs:** Any input that rounds to zero now prints `"0"` instead of `"0/1"`. For example, `fractional(0.0001)` and `fractional(-0.0001)` used to return `"0/1"` and now return `"0"`. I did not add tests for these because they are not the reported bug, but it is an intended consequence of the same fix. Say if you'd rather scope the change to the carry case only.

The docstring examples are unaffected, since none of them change.

## events
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths
…[1054 chars elided]…
u=True`
   uses base 1024 even when `binary=False` (so `999999` with gnu is `976.6K`, not a carry case).
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[tool_use Bash] {"command": "grep -n \"def fractional\" -A 60 src/humanize/number.py; ls .lithify/harness/scripts/ ; ls <work>/env-humanize/bin/python", "description": "Show fractional() source and tooling paths"}
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
…[1075 chars elided]…
rac.denominator
364-    if whole_number and not numerator and denominator == 1:
365-        # this means that an integer was passed in
366-        # (or variants of that integer like 1.0000)
367-        return f"{whole_number:.0f}"
368-
369-    if not whole_number:
370-        return f"{numerator:.0f}/{denominator:.0f}"
371-
compare_outputs.py
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "sed -n 371,380p src/humanize/number.py; grep -n \"fractional\" -B2 -A40 tests/test_number.py | head -90; PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0.3)' 'fractional(-1.3)' 'fractional(-1)' 'fractional(0.5)' 'fractional(-0.0)'", "description": "Show rest of fractional() and reproduce on unmodified code"}
[tool_result]     # int() truncates toward zero, so for a negative number both
    # whole_number and numerator carry the minus sign, which prints as
    # "-1 -3/10". The sign already rides on the whole part; absorb it
    # from the fractional part so the result reads as a normal mixed
    # fraction.
    return f"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}"


def scientific(value: NumberOrString, precision: int = 2) -> str:
190-    ],
191-)
192:def test_fractional(test_input: float | str, exp
…[1711 chars elided]…
'
same    fractional(0)
    old: '0/1'
    new: '0/1'
same    fractional(-2.9999999)
    old: '-2 1/1'
    new: '-2 1/1'
same    fractional(-0.9999999)
    old: '-1/1'
    new: '-1/1'
same    fractional(-0.3)
    old: '-3/10'
    new: '-3/10'
same    fractional(-1.3)
    old: '-1 3/10'
    new: '-1 3/10'
same    fractional(-1)
    old: '-1'
    new: '-1'
same    fractional(0.5)
    old: '1/2'
    new: '1/2'
same    fractional(-0.0)
    old: '0/1'
    new: '0/1'
10 expressions, 0 changed, 10 same
[assistant] Reproduced on the unmodified code: `2.9999999` → `'2 1/1'`, `0.9999999` → `'1/1'`, `0` → `'0/1'`. The cause is that `limit_denominator` can round the fractional part to exactly ±1, and the code never folds that back into the whole part. Let me check the existing test cases before editing.
[tool_use Bash] {"command": "sed -n 160,191p tests/test_number.py", "description": "Show existing fractional test cases"}
[tool_result]         ("-inf", "-Inf"),
    ],
)
def test_apnumber(test_input: int | str, expected: str) -> None:
    assert humanize.apnumber(test_input) == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (1, "1"),
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
        (-0.5, "-1/2"),
    ],
)
[assistant] I'll fold a rounded-to-±1 remainder into the whole part, and make the zero-numerator integer branch apply when the whole part is 0 too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "old_string": "    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and denominator == 1:\n        # this me
…[311 chars elided]…
,\n        # so carry it into the whole part instead of printing \"1/1\"\n        whole_number += int(frac)\n        frac = Fraction(0)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000, or 0)\n        return f\"{whole_number:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (0, \"0\"),\n        (2.9999999, \"3\"),\n        (0.9999999, \"1\"),\n        (-2.9999999, \"-3\"),\n        (-0.9999999, \"-1\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0.3)' 'fractional(-1.3)' 'fractional(-1)' 'fractional(0.5)' 'fractional(-0.0)' 'fractional(0.0001)' 'fractional(-0.0001)' 'fractional(1.0000001)' 'fractional(-1.9999999)' 'fractional(1/3)' 'fractional(2.5)'; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; cat tox.ini 2>/dev/null | head -0; ls", "description": "Compare outputs, run full test suite, list repo root"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpsif27_qg/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/base-1/src/humanize/__init__.py)
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
    new: '-3'
CHA
…[575 chars elided]…
 fractional(1/3)
    old: '1/3'
    new: '1/3'
same    fractional(2.5)
    old: '2 1/2'
    new: '2 1/2'
16 expressions, 9 changed, 7 same

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
720 passed, 74 skipped in 6.48s
head: illegal line count -- 0
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
[assistant] All five target inputs now change as expected, and the suite passes. I'll run the linter on the two edited files and confirm the diff.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ($PY -m ruff check src/humanize/number.py tests/test_number.py 2>&1 || $PY -m ruff --version 2>&1) | tail -3; git diff --stat", "description": "Lint edited files and show diff stat"}
[tool_result] <work>/env-humanize/bin/python: No module named ruff
<work>/env-humanize/bin/python: No module named ruff
 src/humanize/number.py | 9 +++++++--
 tests/test_number.py   | 5 +++++
 2 files changed, 12 insertions(+), 2 deletions(-)
[assistant] `humanize.fractional()` now returns a plain integer when the fractional part rounds to a whole number. `fractional(2.9999999)` gives `"3"`, `fractional(0.9999999)` gives `"1"`, and `fractional(0)` gives `"0"`. Negative inputs follow the same rule: `-2.9999999` gives `"-3"` and `-0.9999999` gives `"-1"`.

**Cause:** `Fraction(...).limit_denominator(1000)` can round the fractional part to exactly ±1, and the code never folded that back into the whole part. The zero case failed because the integer branch required a non-zero whole part.

**Change (`src/humanize/number.py`):**
- If the rounded frac
…[452 chars elided]…
**Verification:** The full suite passes (`720 passed, 74 skipped`). Ruff isn't installed in the project's venv, so I did not lint.

**Behaviour change beyond the reported inputs:** Any input that rounds to zero now prints `"0"` instead of `"0/1"`. For example, `fractional(0.0001)` and `fractional(-0.0001)` used to return `"0/1"` and now return `"0"`. I did not add tests for these because they are not the reported bug, but it is an intended consequence of the same fix. Say if you'd rather scope the change to the carry case only.

The docstring examples are unaffected, since none of them change.
