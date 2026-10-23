# trajectory dom-1

final message:
`fractional()` now returns a plain integer when the fractional part rounds to a whole number, including for negative inputs. The full test suite passes (721 passed, 74 skipped).

**Cause:** `Fraction(...).limit_denominator(1000)` returns `1/1` for any fraction within 0.0005 of a whole number. The function only handled `denominator == 1` when the whole number was nonzero and the numerator was zero. So `2.9999999` printed as `2 1/1`, `0.9999999` as `1/1`, and `0` as `0/1`.

**Fix** (`src/humanize/number.py`): the whole-number branch now checks `denominator == 1` alone and returns `round(number)`. It covers the old integer case and the rounding cases. The input guard for NaN/Inf and the `try` conversion are untouched.

**Output changes**, checked against HEAD with `compare_outputs.py`:

| Input | Before | After |
|---|---|---|
| `2.9999999` | `2 1/1` | `3` |
| `0.9999999` | `1/1` | `1` |
| `0` | `0/1` | `0` |
| `-2.9999999` | `-2 1/1` | `-3` |
| `-0.9999999` | `-1/1` | `-1` |
| `0.0001` | `0/1` | `0` |

Inputs such as `1.0`, `2.5`, `-1.3` and `0.3` are unchanged, so I left them out of the tests. The docstring examples are also unaffected.

**Tests** (`tests/test_number.py`): I added six cases to the existing `test_fractional` parametrize list, one for each changed input except `-0.0`, which is covered by `0`. Each one gives a different result on HEAD, so each would fail there.

**Not run:** `mypy` and `ruff` are not installed in the project venv, so I could not run them. I checked the change by reading it against the project's lint and type rules. The `round()` result is an `int` and the f-string format is unchanged from the existing code.

## events
[assistant] I'll load the project's number-output skill first, since this changes `fractional()` output.
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths 
…[1805 chars elided]…
t `[tool.ruff]`, run by the
   pre-commit hook `ruff-check`) still governs the diff, so check by reading it. The rules that
   matter for formatter edits are `RUF046` (no `int()` around a value that is already an int,
   such as `int(round(x))` or `int(math.floor(x))`), `D` with the Google convention for any
   docstring you touch in `src/` (tests are exempt), `PT` csv parametrize names (item 3), and
   `EM` for any raise (see skill `humanize-error-contract`). mypy runs `strict` (tox `mypy`
   env), so new locals need consistent types: don't rebind an `int` name to a `Fraction` or
   `float`.

[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness 2>/dev/null; grep -n \"def fractional\" -A 80 src/humanize/number.py", "description": "Read fractional() source and harness memory"}
[tool_result] - The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
311:def fractional(value: NumberOrString) -> str:
312-    """Convert to fractional number.
313-
314-    There will be some cases where one might not want to show ugly decimal places for
…[2017 chars elided]…
 fraction.
377-    return f"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}"
378-
379-
380-def scientific(value: NumberOrString, precision: int = 2) -> str:
381-    """Return number in string scientific notation z.wq x 10ⁿ.
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
[assistant] The skill's checklist is loaded. Next I'll reproduce the bug on the unmodified code, as the project harness requires, before editing.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import fractional\nfor v in [2.9999999, 0.9999999, 0, -2.9999999, -0.9999999, -0.0, 1.0, -1.0, 2.5, -2.5, 0.3, -0.3, -1.3, 1.3, 2.9996]:\n    print(repr(v), repr(fractional(v)))\n\"; echo ---; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 2>&1 | tail -20", "description": "Reproduce fractional() bug on unmodified code"}
[tool_result] 2.9999999 '2 1/1'
0.9999999 '1/1'
0 '0/1'
-2.9999999 '-2 1/1'
-0.9999999 '-1/1'
-0.0 '0/1'
1.0 '1'
-1.0 '-1'
2.5 '2 1/2'
-2.5 '-2 1/2'
0.3 '3/10'
-0.3 '-3/10'
-1.3 '-1 3/10'
1.3 '1 3/10'
2.9996 '2 1/1'
---
old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp9dzjqjc4/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/src/humanize/__init__.py)
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
5 expressions, 0 changed, 5 same
[assistant] Reproduced on unmodified code: `2.9999999` → `'2 1/1'`, `0.9999999` → `'1/1'`, `0` → `'0/1'`, and the negatives behave the same way. The cause is that `limit_denominator(1000)` returns `1/1` for a fraction that is within 0.0005 of a whole number, and the function only special-cases `denominator == 1` when the fraction is already zero. I'll make the whole-number check depend on the denominator alone, so it covers the rounded-up case too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/src/humanize/number.py", "old_string": "    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{whole_number:.0f}\"\n\n    if not whole_number:", "new_string": "    if denominator == 1:\n        # the value is a whole number: either an integer was passed in (or a variant\n        # like 1.0000), or the fractional part rounded up to one (2.9999999) or down to\n        # zero (0.0001). Print the rounded value rather than a degenerate \"2 1/1\".\n        return f\"{round(number):.0f}\"\n\n    if not whole_number:"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/src/humanize/number.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import fractional\nfor v in [2.9999999, 0.9999999, 0, -0.0, 0.0001, -2.9999999, -0.9999999, 1.0, -1.0, 2.5, -2.5, 0.3, -0.3, -1.3, 1.3, 2.9996, 3.0004, 1.0000001]:\n    print(repr(v), repr(fractional(v)))\n\"; echo ---; $PY .lithify/harness/scripts/compare_outputs.py 'fractional(2.9999999)' 'fractional(0.9999999)' 'fractional(0)' 'fractional(-2.9999999)' 'fractional(-0.9999999)' 'fractional(0.0001)' 'fractional(2.9996)' 'fractional(-0.0)' 'fractional(1.0)' 'fractional(2.5)' 'fractional(-1.3)' 2>&1 | tail -40", "description": "Verify fix and compare old vs new outputs"}
[tool_result] 2.9999999 '3'
0.9999999 '1'
0 '0'
-0.0 '0'
0.0001 '0'
-2.9999999 '-3'
-0.9999999 '-1'
1.0 '1'
-1.0 '-1'
2.5 '2 1/2'
-2.5 '-2 1/2'
0.3 '3/10'
-0.3 '-3/10'
-1.3 '-1 3/10'
1.3 '1 3/10'
2.9996 '3'
3.0004 '3'
1.0000001 '1'
---
old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpzc_fwhpm/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/src/humanize/__init__.py)
CHANGED fract
…[148 chars elided]…
w: '0'
CHANGED fractional(-2.9999999)
    old: '-2 1/1'
    new: '-3'
CHANGED fractional(-0.9999999)
    old: '-1/1'
    new: '-1'
CHANGED fractional(0.0001)
    old: '0/1'
    new: '0'
CHANGED fractional(2.9996)
    old: '2 1/1'
    new: '3'
CHANGED fractional(-0.0)
    old: '0/1'
    new: '0'
same    fractional(1.0)
    old: '1'
    new: '1'
same    fractional(2.5)
    old: '2 1/2'
    new: '2 1/2'
same    fractional(-1.3)
    old: '-1 3/10'
    new: '-1 3/10'
11 expressions, 8 changed, 3 same
[assistant] The fix changes the eight degenerate inputs and leaves the others alone. Next I'll find the existing `fractional` test list.
[tool_use Bash] {"command": "grep -n \"fractional\" -B 3 -A 30 tests/test_number.py | head -80", "description": "Find fractional test parametrize list"}
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
…[140 chars elided]…
"3.0 x 10⁻¹"),
210-        ([1000, 0], "1 x 10³"),
211-        ([0.3, 0], "3 x 10⁻¹"),
212-        ([1e20], "1.00 x 10²⁰"),
213-        ([2e-20], "2.00 x 10⁻²⁰"),
214-        ([-3e20], "-3.00 x 10²⁰"),
215-        ([-4e-20], "-4.00 x 10⁻²⁰"),
216-        ([math.nan], "NaN"),
217-        ([math.inf], "+Inf"),
218-        ([-math.inf], "-Inf"),
219-        (["nan"], "NaN"),
220-        (["-inf"], "-Inf"),
221-    ],
222-)
223-def test_scientific(test_args: list[typing.Any], expected: str) -> None:
[tool_use Bash] {"command": "sed -n 160,193p tests/test_number.py", "description": "Read existing fractional test cases"}
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
def test_fractional(test_input: float | str, expected: str) -> None:
    assert humanize.fractional(test_input) == expected
[assistant] I'll add the changed inputs to the existing parametrize list. The unchanged inputs (`1.0`, `2.5`, `-1.3`) stay out, per the project rule.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (0, \"0\"),\n        (0.0001, \"0\"),\n        (0.9999999, \"1\"),\n        (2.9999999, \"3\"),\n        (-0.9999999, \"-1\"),\n        (-2.9999999, \"-3\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-150254-bug-humanize-fractional-produces/dom-1/tests/test_number.py has been updated successfully.
[assistant] The docstring examples (`0.3`, `1.3`, `1/3`, `1`) are unaffected, so they need no edit. Now the full check: the project's pytest command, plus mypy if it's in the venv.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"--- mypy:\"; PYTHONPATH=src $PY -m mypy src/humanize/number.py 2>&1 | tail -3; echo \"--- old-test check (HEAD tests against new code should fail only for new cases):\"; git diff --stat", "description": "Run full pytest suite, mypy, and show diff stat"}
[tool_result] Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
721 passed, 74 skipped in 6.60s
--- mypy:
<work>/env-humanize/bin/python: No module named mypy
--- old-test check (HEAD tests against new code should fail only for new cases):
 src/humanize/number.py | 9 +++++----
 tests/test_number.py   | 6 ++++++
 2 files changed, 11 insertions(+), 4 deletions(-)
[assistant] `fractional()` now returns a plain integer when the fractional part rounds to a whole number, including for negative inputs. The full test suite passes (721 passed, 74 skipped).

**Cause:** `Fraction(...).limit_denominator(1000)` returns `1/1` for any fraction within 0.0005 of a whole number. The function only handled `denominator == 1` when the whole number was nonzero and the numerator was zero. So `2.9999999` printed as `2 1/1`, `0.9999999` as `1/1`, and `0` as `0/1`.

**Fix** (`src/humanize/number.py`): the whole-number branch now checks `denominator == 1` alone and returns `round(number)`
…[464 chars elided]…
e unchanged, so I left them out of the tests. The docstring examples are also unaffected.

**Tests** (`tests/test_number.py`): I added six cases to the existing `test_fractional` parametrize list, one for each changed input except `-0.0`, which is covered by `0`. Each one gives a different result on HEAD, so each would fail there.

**Not run:** `mypy` and `ruff` are not installed in the project venv, so I could not run them. I checked the change by reading it against the project's lint and type rules. The `round()` result is an `int` and the f-string format is unchanged from the existing code.
