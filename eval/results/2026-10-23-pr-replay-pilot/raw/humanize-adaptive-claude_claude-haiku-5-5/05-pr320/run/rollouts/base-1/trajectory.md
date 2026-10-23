# trajectory base-1

final message:
`humanize.fractional` now renders negative mixed numbers in the conventional form: `-1.3` gives `"-1 3/10"` and `-2.5` gives `"-2 1/2"`. The full test suite passes (705 passed, 69 skipped).

**Cause:** for negative inputs, `int()` truncates toward zero, so the fractional part `number - whole_number` stayed negative. Its numerator carried its own minus sign, which produced the second `-`.

**Fix** (`src/humanize/number.py`): the function now works on the absolute value and applies the sign once at the end. The sign is prepended in all three return paths, so whole numbers, pure fractions and mixed numbers all stay consistent.

**Tests** (`tests/test_number.py`): I added four cases to the existing `test_fractional` parametrization: `-1.3 → "-1 3/10"`, `-2.5 → "-2 1/2"`, `-0.3 → "-3/10"` and `-1 → "-1"`. The `-0.3` case already worked before the fix and is there as a guard.

I haven't committed anything; the changes are in the working tree.

One thing I noticed but did not change: `fractional(0)` and `fractional(0.0)` return `"0/1"` rather than `"0"`. This predates my change and is outside the reported bug, but it's a likely follow-up if you want whole-number zero handled the same way as other integers.

## events
[tool_use Bash] {"command": "grep -rn \"fractional\" --include=*.py . | grep -v \"\\.git/\" | head -50", "description": "Locate fractional implementation and tests"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"fractional\" . --exclude-dir=.git | head -50", "description": "Search repo for fractional references"}
[tool_result] README.md:171:>>> humanize.fractional(1/3)
README.md:173:>>> humanize.fractional(1.5)
README.md:175:>>> humanize.fractional(0.3)
README.md:177:>>> humanize.fractional(0.333)
README.md:179:>>> humanize.fractional(1)
tests/test_benchmarks.py:32:def test_fractional(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:33:    benchmark(humanize.fractional, 1.5)
tests/test_number.py:188:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:189:    assert h
…[433 chars elided]…
     >>> fractional(float(1/3))
src/humanize/number.py:333:        >>> fractional(1)
src/humanize/number.py:335:        >>> fractional("ten")
src/humanize/number.py:337:        >>> fractional(None)
src/humanize/time.py:483:    A custom `format` can be specified to control how the fractional part
src/humanize/time.py:621:    # When adjusting we should not deal anymore with fractional days as all rounding has
src/humanize/__init__.py:11:    fractional,
src/humanize/__init__.py:35:    "fractional",
[tool_use Bash] {"command": "sed -n 300,390p src/humanize/number.py && echo ---- && sed -n 160,190p tests/test_number.py", "description": "Read fractional implementation and its tests"}
[tool_result]             return _format_not_finite(float(value))
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    if not 0 <= value < 10:
        return str(value)
    return _(_APNUMBER_WORDS[value])


def fractional(value: NumberOrString) -> str:
    """Convert to fractional number.

    There will be some cases where one might not want to show ugly decimal places for
    floats and decimals.

    This function returns a human-readable fractional number in form o
…[2222 chars elided]…
 "1 1/3"),
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
    ],
)
def test_fractional(test_input: float | str, expected: str) -> None:
    assert humanize.fractional(test_input) == expected
[assistant] The bug is in `fractional()`: for negative inputs, `int()` truncates toward zero, so `number - whole_number` is negative and the numerator carries its own minus sign. I'll fix it by working on the absolute value and applying the sign once.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142317-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py", "old_string": "    whole_number = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and deno
…[664 chars elided]…
 = frac.denominator\n    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{sign}{whole_number:.0f}\"\n\n    if not whole_number:\n        return f\"{sign}{numerator:.0f}/{denominator:.0f}\"\n\n    return f\"{sign}{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142317-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py has been updated successfully.
[assistant] Next I'll add regression cases for the negative inputs to the existing parametrized test, then run the project's checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142317-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py", "old_string": "        (0.333, \"333/1000\"),\n        (math.nan, \"NaN\"),", "new_string": "        (0.333, \"333/1000\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (-0.3, \"-3/10\"),\n        (-1, \"-1\"),\n        (math.nan, \"NaN\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142317-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"import humanize as h; print([h.fractional(x) for x in (-1.3,-2.5,-0.3,-1,1.3,0.0,-0.0)])\"", "description": "Run project test suite and spot-check outputs"}
[tool_result] test_naturalsize        416.9997 (3.14)       205,999.9970 (5.13)       561.2189 (3.58)      1,007.8409 (5.10)       541.0111 (3.61)      41.9968 (5.38)     391;6797    1,781.8358 (0.28)     155836           1
test_intcomma           457.9779 (3.45)       625,957.9968 (15.60)      991.0351 (6.33)      4,959.2561 (25.09)      542.0006 (3.62)      41.9968 (5.38)     501;9020    1,009.0460 (0.16)      46421           1
test_naturalday         540.9820 (4.07)     1,979,542.0230 (49.33)      856.8841
…[1362 chars elided]…
.03)      24793           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
705 passed, 69 skipped in 6.06s
['-1 3/10', '-2 1/2', '-3/10', '-1', '1 3/10', '0/1', '0/1']
[assistant] `humanize.fractional` now renders negative mixed numbers in the conventional form: `-1.3` gives `"-1 3/10"` and `-2.5` gives `"-2 1/2"`. The full test suite passes (705 passed, 69 skipped).

**Cause:** for negative inputs, `int()` truncates toward zero, so the fractional part `number - whole_number` stayed negative. Its numerator carried its own minus sign, which produced the second `-`.

**Fix** (`src/humanize/number.py`): the function now works on the absolute value and applies the sign once at the end. The sign is prepended in all three return paths, so whole numbers, pure fractions and mix
…[18 chars elided]…
y consistent.

**Tests** (`tests/test_number.py`): I added four cases to the existing `test_fractional` parametrization: `-1.3 → "-1 3/10"`, `-2.5 → "-2 1/2"`, `-0.3 → "-3/10"` and `-1 → "-1"`. The `-0.3` case already worked before the fix and is there as a guard.

I haven't committed anything; the changes are in the working tree.

One thing I noticed but did not change: `fractional(0)` and `fractional(0.0)` return `"0/1"` rather than `"0"`. This predates my change and is outside the reported bug, but it's a likely follow-up if you want whole-number zero handled the same way as other integers.
