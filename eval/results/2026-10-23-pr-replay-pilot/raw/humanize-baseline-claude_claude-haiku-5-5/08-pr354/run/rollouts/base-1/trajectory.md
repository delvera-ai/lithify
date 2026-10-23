# trajectory base-1

final message:
`humanize.fractional()` now returns a plain integer whenever the fractional part is zero or rounds to ±1. All three reported cases are fixed, and so are their negative counterparts.

**The cause:** the function only returned a plain integer when the fraction was exactly zero. A fraction that rounded to `1/1` fell through to the mixed-number branch, and a zero fraction in the `0` case produced `0/1`.

**The fix** (`src/humanize/number.py`): when the limited fraction has denominator 1, the code now folds its numerator into the whole part and returns that as an integer. The folding is what makes negative inputs correct: `-2.9999999` gives `-3`, not `-2 1/1`.

**Tests** (`tests/test_number.py`): I added five cases to the existing `test_fractional` parametrization: `0`, `0.9999999`, `2.9999999`, `-2.9999999`, and `-0.9999999`. No existing expectations were changed.

The project suite passes with the project's test command: 720 passed, 74 skipped. I also spot-checked the reported inputs and a few existing ones (`1.3`, `-1.3`, `-0.5`, `4/3`), which all return the same output as before.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"def fractional\" src | head; grep -rln \"fractional\" tests | head", "description": "Locate fractional function and its tests"}
[tool_result] src/humanize/number.py:311:def fractional(value: NumberOrString) -> str:
tests/test_benchmarks.py
tests/test_number.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "offset": 300, "limit": 120}
[tool_result] 300	    try:
301	        if not math.isfinite(float(value)):
302	            return _format_not_finite(float(value))
303	        value = int(value)
304	    except (TypeError, ValueError):
305	        return str(value)
306	    if not 0 <= value < 10:
307	        return str(value)
308	    return _(_APNUMBER_WORDS[value])
309	
310	
311	def fractional(value: NumberOrString) -> str:
312	    """Convert to fractional number.
313	
314	    There will be some cases where one might not want to show ugly de
…[2814 chars elided]…
  Args:
405	        value (int, float, str): Input number.
406	        precision (int): Number of decimal for first part of the number.
407	
408	    Returns:
409	        str: Number in scientific notation z.wq x 10ⁿ.
410	    """
411	    import math
412	
413	    try:
414	        value = float(value)
415	        if not math.isfinite(value):
416	            return _format_not_finite(value)
417	    except (ValueError, TypeError):
418	        return str(value)
419	    fmt = f"{{:.{int(precision)}e}}"
[tool_use Bash] {"command": "grep -n \"fractional\" -A3 tests/test_number.py | head -150; grep -n \"fractional\" tests/test_benchmarks.py", "description": "Show existing fractional tests"}
[tool_result] 192:def test_fractional(test_input: float | str, expected: str) -> None:
193:    assert humanize.fractional(test_input) == expected
194-
195-
196-@pytest.mark.parametrize(
32:def test_fractional(benchmark: BenchmarkFixture) -> None:
33:    benchmark(humanize.fractional, 1.5)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/tests/test_number.py", "offset": 160, "limit": 35}
[tool_result] 160	        ("-inf", "-Inf"),
161	    ],
162	)
163	def test_apnumber(test_input: int | str, expected: str) -> None:
164	    assert humanize.apnumber(test_input) == expected
165	
166	
167	@pytest.mark.parametrize(
168	    "test_input, expected",
169	    [
170	        (1, "1"),
171	        (2.0, "2"),
172	        (4.0 / 3.0, "1 1/3"),
173	        (5.0 / 6.0, "5/6"),
174	        ("7", "7"),
175	        ("8.9", "8 9/10"),
176	        ("ten", "ten"),
177	        (None, "None"),
178	        (1 / 3, "1/3"),
179	        (1.5, "1 1/2"),
180	        (0.3, "3/10"),
181	        (0.333, "333/1000"),
182	        (math.nan, "NaN"),
183	        (math.inf, "+Inf"),
184	        (-math.inf, "-Inf"),
185	        ("nan", "NaN"),
186	        ("-inf", "-Inf"),
187	        (-1.3, "-1 3/10"),
188	        (-2.5, "-2 1/2"),
189	        (-0.5, "-1/2"),
190	    ],
191	)
192	def test_fractional(test_input: float | str, expected: str) -> None:
193	    assert humanize.fractional(test_input) == expected
194	
[assistant] The rounding carry is missing: when the fractional part reduces to `n/1`, the code prints it as a fraction instead of folding it into the whole part. I'll fold it in before choosing the output format.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "old_string": "    whole_number = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and deno
…[364 chars elided]…
inator\n    if denominator == 1:\n        # the fractional part is zero (an integer was passed in, or a variant\n        # of one like 1.0000) or it rounded to exactly +/-1, e.g. 2.9999999.\n        # Fold any rounded-up unit into the whole part so it reads as an integer.\n        whole_number += numerator\n        numerator = 0\n        return f\"{whole_number:.0f}\"\n\n    if not whole_number:"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "old_string": "        whole_number += numerator\n        numerator = 0\n        return f\"{whole_number:.0f}\"", "new_string": "        return f\"{whole_number + numerator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/src/humanize/number.py has been updated successfully.
[assistant] Next I'll add regression cases alongside the existing parametrized tests, without changing any existing expectations.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (0, \"0\"),\n        (0.9999999, \"1\"),\n        (2.9999999, \"3\"),\n        (-2.9999999, \"-3\"),\n        (-0.9999999, \"-1\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142542-bug-humanize-fractional-produces/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] test_intcomma           458.0070 (3.44)        34,458.0039 (3.23)       584.0104 (3.72)       189.9394 (4.07)       583.0079 (3.77)      41.9968 (10.33)    146;3231    1,712.2982 (0.27)     137137           1
test_naturaldelta       542.0006 (4.07)       106,999.9998 (10.02)      755.0773 (4.81)       762.6245 (16.35)      667.0016 (4.32)      41.0073 (10.09)   5179;6509    1,324.3678 (0.21)      93024           1
test_naturalday         565.4292 (4.25)     2,948,613.1430 (276.19)     728.9591 (
…[1291 chars elided]…
.0156 (38.01)    207.9760 (51.16)   1318;2347      144.9605 (0.02)      26579           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
720 passed, 74 skipped in 6.63s
[tool_use Bash] {"command": "git diff --stat && PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nfor v in [2.9999999, 0.9999999, 0, -2.9999999, -0.9999999, 1.3, -1.3, -0.5, 4/3]: print(repr(v), repr(humanize.fractional(v)))\"", "description": "Show diff stats and spot-check reported inputs"}
[tool_result]  src/humanize/number.py | 9 +++++----
 tests/test_number.py   | 5 +++++
 2 files changed, 10 insertions(+), 4 deletions(-)
2.9999999 '3'
0.9999999 '1'
0 '0'
-2.9999999 '-3'
-0.9999999 '-1'
1.3 '1 3/10'
-1.3 '-1 3/10'
-0.5 '-1/2'
1.3333333333333333 '1 1/3'
[assistant] `humanize.fractional()` now returns a plain integer whenever the fractional part is zero or rounds to ±1. All three reported cases are fixed, and so are their negative counterparts.

**The cause:** the function only returned a plain integer when the fraction was exactly zero. A fraction that rounded to `1/1` fell through to the mixed-number branch, and a zero fraction in the `0` case produced `0/1`.

**The fix** (`src/humanize/number.py`): when the limited fraction has denominator 1, the code now folds its numerator into the whole part and returns that as an integer. The folding is what makes negative inputs correct: `-2.9999999` gives `-3`, not `-2 1/1`.

**Tests** (`tests/test_number.py`): I added five cases to the existing `test_fractional` parametrization: `0`, `0.9999999`, `2.9999999`, `-2.9999999`, and `-0.9999999`. No existing expectations were changed.

The project suite passes with the project's test command: 720 passed, 74 skipped. I also spot-checked the reported inputs and a few existing ones (`1.3`, `-1.3`, `-0.5`, `4/3`), which all return the same output as before.

The changes are uncommitted in the worktree.
