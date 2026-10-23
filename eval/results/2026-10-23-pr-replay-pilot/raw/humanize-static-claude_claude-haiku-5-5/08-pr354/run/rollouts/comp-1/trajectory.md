# trajectory comp-1

final message:
`fractional()` now returns a plain integer when the fractional part rounds to a whole number, including for negative inputs and `0`. The full test suite passes: `720 passed, 74 skipped`.

**Reproduction on the unmodified code:** `2.9999999` → `'2 1/1'`, `0.9999999` → `'1/1'`, `0` → `'0/1'`, matching the report.

**Cause:** `limit_denominator(1000)` can round the fractional part up to exactly 1, giving `1/1`. The existing integer shortcut only fired when `whole_number` was nonzero, so the `0` case and the carry cases fell through to the fraction branches.

**Fix** (`src/humanize/number.py`): the shortcut now fires whenever the reduced fraction's denominator is 1, and returns `whole_number + numerator`. The NaN/Inf guard and the `try`/`except` path are untouched. The fraction branches are unchanged, and I checked that negative outputs still carry one leading `-`.

**Tests** (`tests/test_number.py`, added to the existing `test_fractional` list): `2.9999999 → "3"`, `0.9999999 → "1"`, `-2.9999999 → "-3"`, `-0.9999999 → "-1"`, `0 → "0"`. All five change output from HEAD, so each would fail on the original code.

**Old vs. new outputs** (via `compare_outputs.py`): 9 of 17 probed expressions changed, all in the intended way. `0.9995` now gives `'1'` (was `'1/1'`) and `1.9996` gives `'2'` (was `'1 1/1'`). Unrelated cases such as `-0.3`, `1.5`, `-2.5`, `1`, and `-1` are unchanged.

**Not done:**
- The `Examples:` docstring block in `fractional` shows no output this change alters, so I left it as is.
- ruff and mypy aren't installed in the project environment, so lint and type checks were not run. I read the changed lines against the `[tool.ruff]` rules (line length, docstring and parametrize conventions) by eye.
- Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"def fractional\" -A 80 src/humanize/number.py && cat .lithify/harness/memory.md 2>/dev/null; ls <work>/env-humanize/bin/python", "description": "Inspect fractional implementation and environment"}
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
…[2106 chars elided]…

389-        >>> scientific(-1000)
390-        '-1.00 x 10³'
391-        >>> scientific(1000, 1)
- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<work>/env-humanize/bin/python
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths
…[1642 chars elided]…
umentation.
5. **Lint rules to check by reading** (ruff isn't installed, see tool_guidance). The pyproject
   `[tool.ruff]` rules that matter for formatter edits are `RUF046` (no `int()` around a value
   that is already an int, such as `int(round(x))` or `int(math.floor(x))`), `D` with the Google
   convention for any docstring you touch in `src/` (tests are exempt), `PT` csv parametrize
   names (item 3), and `EM` for any raise (see skill `humanize-error-contract`). mypy is
   configured `strict`, so new locals need consistent types: don't rebind an `int` name to a
   `Fraction` or `float`.

[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0.3)' 'fractional(-1.3)' 'fractional(-0.0000001)' 'fractional(1)' 'fractional(-1)' 'fractional(0.0000001)' 2>&1; echo EXIT $?", "description": "Load skill and reproduce bug on unmodified code"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmphwf73tqo/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/src/humanize/__init__.py)
same    fractional(2.9999999)
    old: '2 1/1'
    new: '2 1/1'
same    fractional(0.9999999)
    old: '1/1'
    new: '1/1'
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
same    fractional(-0.0000001)
    old: '0/1'
    new: '0/1'
same    fractional(1)
    old: '1'
    new: '1'
same    fractional(-1)
    old: '-1'
    new: '-1'
same    fractional(0.0000001)
    old: '0/1'
    new: '0/1'
11 expressions, 0 changed, 11 same
EXIT 0
[assistant] Reproduced on the unmodified code: `2.9999999` → `'2 1/1'`, `0.9999999` → `'1/1'`, `0` → `'0/1'`, matching the report. Now I'll look at the test list and the surrounding code before editing.
[tool_use Bash] {"command": "grep -n \"fractional\" -B3 -A40 tests/test_number.py | head -120", "description": "Show existing fractional test cases"}
[tool_result] 189-        (-0.5, "-1/2"),
190-    ],
191-)
192:def test_fractional(test_input: float | str, expected: str) -> None:
193:    assert humanize.fractional(test_input) == expected
194-
195-
196-@pytest.mark.parametrize(
197-    "test_args, expected",
198-    [
199-        ([1000], "1.00 x 10³"),
200-        ([-1000], "-1.00 x 10³"),
201-        ([5.5], "5.50 x 10⁰"),
202-        ([5781651000], "5.78 x 10⁹"),
203-        (["1000"], "1.00 x 10³"),
204-        (["99"], "9.90 x 10¹"),
205-        ([0.3
…[419 chars elided]…
-        ([math.inf], "+Inf"),
218-        ([-math.inf], "-Inf"),
219-        (["nan"], "NaN"),
220-        (["-inf"], "-Inf"),
221-    ],
222-)
223-def test_scientific(test_args: list[typing.Any], expected: str) -> None:
224-    assert humanize.scientific(*test_args) == expected
225-
226-
227-@pytest.mark.parametrize(
228-    "test_args, expected",
229-    [
230-        ([1], "1"),
231-        ([None], None),
232-        ([0.0001, "{:.0%}"], "0%"),
233-        ([0.0001, "{:.0%}", 0.01], "<1%"),
[tool_use Bash] {"command": "sed -n 170,191p tests/test_number.py", "description": "Show fractional parametrize list head"}
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
        (-0.5, "-1/2"),
    ],
)
[assistant] Root cause: `limit_denominator(1000)` can round the fractional part up to exactly 1, giving `1/1`. The existing integer shortcut only fires when `whole_number` is nonzero, so the carry case and `0` fall through to the `n/d` or mixed branches. I'll generalize that shortcut to any result whose fraction is a whole number, after the existing guard.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/src/humanize/number.py", "old_string": "    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{whole_number:.0f}\"", "new_string": "    if denominator == 1:\n        # the value is a whole number, either because an integer was passed in\n        # (or variants of that integer like 1.0000) or because the fractional\n        # part rounded to 1 (e.g. 2.9999999), so there is no fraction to show\n        return f\"{whole_number + numerator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (2.9999999, \"3\"),\n        (0.9999999, \"1\"),\n        (-2.9999999, \"-3\"),\n        (-0.9999999, \"-1\"),\n        (0, \"0\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(-0.0000001)' 'fractional(0.0000001)' 'fractional(-0.3)' 'fractional(-1.3)' 'fractional(1.5)' 'fractional(-2.5)' 'fractional(1)' 'fractional(-1)' 'fractional(1.0000001)' 'fractional(-1.0000001)' 'fractional(0.9995)' 'fractional(1.9996)' 2>&1; echo EXIT $?; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Compare old and new outputs and run full test suite"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp490slc96/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/comp-1/src/humanize/__init__.py)
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
…[484 chars elided]…
1)
    old: '-1'
    new: '-1'
same    fractional(1.0000001)
    old: '1'
    new: '1'
same    fractional(-1.0000001)
    old: '-1'
    new: '-1'
CHANGED fractional(0.9995)
    old: '1/1'
    new: '1'
CHANGED fractional(1.9996)
    old: '1 1/1'
    new: '2'
17 expressions, 9 changed, 8 same
EXIT 0

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
720 passed, 74 skipped in 6.41s
[assistant] `fractional()` now returns a plain integer when the fractional part rounds to a whole number, including for negative inputs and `0`. The full test suite passes: `720 passed, 74 skipped`.

**Reproduction on the unmodified code:** `2.9999999` → `'2 1/1'`, `0.9999999` → `'1/1'`, `0` → `'0/1'`, matching the report.

**Cause:** `limit_denominator(1000)` can round the fractional part up to exactly 1, giving `1/1`. The existing integer shortcut only fired when `whole_number` was nonzero, so the `0` case and the carry cases fell through to the fraction branches.

**Fix** (`src/humanize/number.py`): th
…[555 chars elided]…
ompare_outputs.py`): 9 of 17 probed expressions changed, all in the intended way. `0.9995` now gives `'1'` (was `'1/1'`) and `1.9996` gives `'2'` (was `'1 1/1'`). Unrelated cases such as `-0.3`, `1.5`, `-2.5`, `1`, and `-1` are unchanged.

**Not done:**
- The `Examples:` docstring block in `fractional` shows no output this change alters, so I left it as is.
- ruff and mypy aren't installed in the project environment, so lint and type checks were not run. I read the changed lines against the `[tool.ruff]` rules (line length, docstring and parametrize conventions) by eye.
- Nothing is committed.
