# trajectory dom-1

final message:
`humanize.fractional` now prints negative mixed numbers with one minus sign: `-1.3` gives `"-1 3/10"` and `-2.5` gives `"-2 1/2"`. The full suite passes (705 passed, 69 skipped).

The cause was that `int(number)` and the fraction both kept the sign, so the minus showed up twice. The fix in `src/humanize/number.py` formats the absolute value and adds a single `-` in front. The NaN/Inf and non-numeric guards above it are unchanged.

I added `-1.3`, `-2.5`, `-0.3` and `-1` to the existing `test_fractional` parametrize list in `tests/test_number.py`. Nothing was committed.

One behaviour to be aware of: a negative value that rounds to zero, such as `-0.0001`, still returns `"0/1"`, the same as before. I kept that rather than printing `"-0/1"`.

## events
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/dom-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths 
…[852 chars elided]…
t negated (`*-1` for ints, `"-"` prefixed for strings and floats). Only positive
   inputs belong there.
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[tool_use Bash] {"command": "grep -n \"def fractional\" -A 80 src/humanize/number.py", "description": "Show the fractional function in number.py"}
[tool_result] 309:def fractional(value: NumberOrString) -> str:
310-    """Convert to fractional number.
311-
312-    There will be some cases where one might not want to show ugly decimal places for
313-    floats and decimals.
314-
315-    This function returns a human-readable fractional number in form of fractions and
316-    mixed fractions.
317-
318-    Pass in a string, or a number or a float, and this function returns:
319-
320-    * a string representation of a fraction
321-    * or a whole number
32
…[1530 chars elided]…
sion: int = 2) -> str:
374-    """Return number in string scientific notation z.wq x 10ⁿ.
375-
376-    Examples:
377-        ```pycon
378-        >>> scientific(float(0.3))
379-        '3.00 x 10⁻¹'
380-        >>> scientific(int(500))
381-        '5.00 x 10²'
382-        >>> scientific(-1000)
383-        '-1.00 x 10³'
384-        >>> scientific(1000, 1)
385-        '1.0 x 10³'
386-        >>> scientific(1000, 3)
387-        '1.000 x 10³'
388-        >>> scientific("99")
389-        '9.90 x 10¹'
[tool_use Bash] {"command": "grep -n \"fractional\" -B 30 tests/test_number.py | head -80", "description": "Show existing fractional tests"}
[tool_result] 158-        ("nan", "NaN"),
159-        ("-inf", "-Inf"),
160-    ],
161-)
162-def test_apnumber(test_input: int | str, expected: str) -> None:
163-    assert humanize.apnumber(test_input) == expected
164-
165-
166-@pytest.mark.parametrize(
167-    "test_input, expected",
168-    [
169-        (1, "1"),
170-        (2.0, "2"),
171-        (4.0 / 3.0, "1 1/3"),
172-        (5.0 / 6.0, "5/6"),
173-        ("7", "7"),
174-        ("8.9", "8 9/10"),
175-        ("ten", "ten"),
176-        (None, "None"),
177-        (1 / 3, "1/3"),
178-        (1.5, "1 1/2"),
179-        (0.3, "3/10"),
180-        (0.333, "333/1000"),
181-        (math.nan, "NaN"),
182-        (math.inf, "+Inf"),
183-        (-math.inf, "-Inf"),
184-        ("nan", "NaN"),
185-        ("-inf", "-Inf"),
186-    ],
187-)
188:def test_fractional(test_input: float | str, expected: str) -> None:
189:    assert humanize.fractional(test_input) == expected
[assistant] The bug is in the sign handling: `int(number)` and `Fraction(number - whole_number)` both keep the sign, so the minus appears once in the whole part and again in the fraction. I'll format the magnitude and add one sign in front.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/dom-1/src/humanize/number.py", "old_string": "    whole_number = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and denom
…[689 chars elided]…
umerator) else \"\"\n    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{sign}{whole_number:.0f}\"\n\n    if not whole_number:\n        return f\"{sign}{numerator:.0f}/{denominator:.0f}\"\n\n    return f\"{sign}{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/dom-1/src/humanize/number.py has been updated successfully.
[assistant] Next I'll add the negative cases to the existing parametrize list and run the test suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/dom-1/tests/test_number.py", "old_string": "        (0.333, \"333/1000\"),\n        (math.nan, \"NaN\"),\n        (math.inf, \"+Inf\"),", "new_string": "        (0.333, \"333/1000\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (-0.3, \"-3/10\"),\n        (-1, \"-1\"),\n        (math.nan, \"NaN\"),\n        (math.inf, \"+Inf\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/dom-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"import humanize as h; print([h.fractional(x) for x in (-1.3,-2.5,-0.3,-1,-0.0001,0.0,1.3)])\"", "description": "Run test suite and spot-check negative outputs"}
[tool_result] test_naturalsize        415.9810 (3.09)     1,064,750.0167 (131.93)     538.5209 (3.57)     3,972.2286 (52.68)      500.0038 (3.53)      40.9782 (41.41)     47;3362    1,856.9383 (0.28)     179116           1
test_intcomma           416.9997 (3.10)       104,083.0102 (12.90)      559.2756 (3.70)       493.6708 (6.55)       542.0006 (3.83)      41.9968 (42.44)   1679;6976    1,788.0273 (0.27)     158958           1
test_naturaldelta       541.0111 (4.02)        63,708.0229 (7.89)       668.5872 (
…[1352 chars elided]…
0.03)      28303           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
705 passed, 69 skipped in 5.85s
['-1 3/10', '-2 1/2', '-3/10', '-1', '0/1', '0/1', '1 3/10']
[assistant] `humanize.fractional` now prints negative mixed numbers with one minus sign: `-1.3` gives `"-1 3/10"` and `-2.5` gives `"-2 1/2"`. The full suite passes (705 passed, 69 skipped).

The cause was that `int(number)` and the fraction both kept the sign, so the minus showed up twice. The fix in `src/humanize/number.py` formats the absolute value and adds a single `-` in front. The NaN/Inf and non-numeric guards above it are unchanged.

I added `-1.3`, `-2.5`, `-0.3` and `-1` to the existing `test_fractional` parametrize list in `tests/test_number.py`. Nothing was committed.

One behaviour to be aware of: a negative value that rounds to zero, such as `-0.0001`, still returns `"0/1"`, the same as before. I kept that rather than printing `"-0/1"`.
