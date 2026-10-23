# trajectory base-1

final message:
`humanize.fractional()` now returns plain integers when the fractional part rounds to a whole number, including for negative inputs. The full suite passes: 720 passed, 74 skipped.

**Cause:** `Fraction(...).limit_denominator(1000)` can round the fractional part to exactly `1/1`. The function only handled that when the whole part was nonzero and the numerator was zero, so `2.9999999` fell into the mixed-fraction branch and printed `2 1/1`. `0.9999999` and `0` fell into the plain-fraction branch and printed `1/1` and `0/1`.

**Fix** (`src/humanize/number.py`): right after the fraction is computed, if the denominator is 1, return `whole_number + numerator` as an integer. That replaces the old special case, which only covered the zero-numerator path.

**Outputs checked:**
- `2.9999999` → `3`
- `0.9999999` → `1`
- `0` → `0`
- `-2.9999999` → `-3`
- `-0.9999999` → `-1`
- `-1.3` → `-1 3/10` (unchanged)
- `-0.5` → `-1/2` (unchanged)

**Tests:** I added five cases to the existing `test_fractional` parametrize list in `tests/test_number.py` for the inputs above. I did not change any existing expectations.

I have not committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"def fractional\" --include=*.py . | head; git status --short | head", "description": "Locate fractional function definition"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short | head; grep -rn \"def fractional\" . --exclude-dir=.git | head", "description": "Locate fractional function definition"}
[tool_result] src/humanize/number.py:311:def fractional(value: NumberOrString) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "offset": 290, "limit": 150}
[tool_result] 290	    Args:
291	        value (int, float, str): Integer to convert.
292	
293	    Returns:
294	        str: For numbers 0-9, the number spelled out. Otherwise, the number. This always
295	            returns a string unless the value was not `int`-able, then `str(value)`
296	            is returned.
297	    """
298	    import math
299	
300	    try:
301	        if not math.isfinite(float(value)):
302	            return _format_not_finite(float(value))
303	        value = int(value)
304	    exce
…[3924 chars elided]…
_TRANS)
425	
426	
427	def clamp(
428	    value: float,
429	    format: str = "{:}",
430	    floor: float | None = None,
431	    ceil: float | None = None,
432	    floor_token: str = "<",
433	    ceil_token: str = ">",
434	) -> str:
435	    """Returns number with the specified format, clamped between floor and ceil.
436	
437	    If the number is larger than ceil or smaller than floor, then the respective limit
438	    will be returned, formatted and prepended with a token specifying as such.
439	
[tool_use Bash] {"command": "grep -rn \"fractional\" tests/ docs/ 2>/dev/null | head -60; ls <work>/env-humanize/bin/python 2>&1", "description": "Find existing fractional tests and check env python"}
[tool_result] tests/test_benchmarks.py:32:def test_fractional(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:33:    benchmark(humanize.fractional, 1.5)
tests/test_number.py:192:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:193:    assert humanize.fractional(test_input) == expected
<work>/env-humanize/bin/python
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/tests/test_number.py", "offset": 165, "limit": 35}
[tool_result] 165	
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
195	
196	@pytest.mark.parametrize(
197	    "test_args, expected",
198	    [
199	        ([1000], "1.00 x 10³"),
[assistant] The cause is clear: `limit_denominator(1000)` can round the fractional part to exactly `1/1`, and the function then only special-cases that when `whole_number` is nonzero and the numerator is zero. I'll handle the rounded-to-whole case once, before any branching, by folding it into the integer.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/src/humanize/number.py", "old_string": "    whole_number = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and deno
…[219 chars elided]…
r = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if denominator == 1:\n        # the fractional part is zero, or has rounded to a whole number (e.g.\n        # 2.9999999 -> 1/1), so the value is just an integer\n        return f\"{whole_number + numerator:.0f}\"\n\n    if not whole_number:"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/src/humanize/number.py has been updated successfully.
[assistant] Now I'll add regression cases for the reported inputs and the negative variants. Adding cases doesn't touch the existing tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/tests/test_number.py", "old_string": "        (-0.5, \"-1/2\"),\n    ],\n)\ndef test_fractional(", "new_string": "        (-0.5, \"-1/2\"),\n        (0, \"0\"),\n        (0.9999999, \"1\"),\n        (2.9999999, \"3\"),\n        (-0.9999999, \"-1\"),\n        (-2.9999999, \"-3\"),\n    ],\n)\ndef test_fractional("}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142552-bug-humanize-fractional-produces/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nfor v in [2.9999999,0.9999999,0,-2.9999999,-0.9999999,-1.3,-0.5,1.5,5.0,-0.0,1e20]: print(repr(v), humanize.fractional(v))\"", "description": "Run project test suite and spot-check outputs"}
[tool_result] test_intcomma           458.9965 (3.34)       113,291.9861 (20.60)      627.1429 (3.93)        484.5989 (10.68)      583.9975 (3.75)      41.9968 (5.65)     4348;6606    1,594.5328 (0.25)     139529           1
test_naturaldelta       582.9788 (4.25)       150,999.9856 (27.45)      745.2928 (4.67)        645.4461 (14.23)      708.9984 (4.56)      42.0259 (5.66)      700;7351    1,341.7545 (0.21)     123077           1
test_naturalsize        582.9788 (4.25)        51,374.9837 (9.34)       741.03
…[1441 chars elided]…
------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
720 passed, 74 skipped in 6.77s
2.9999999 3
0.9999999 1
0 0
-2.9999999 -3
-0.9999999 -1
-1.3 -1 3/10
-0.5 -1/2
1.5 1 1/2
5.0 5
-0.0 0
1e+20 100000000000000000000
[assistant] `humanize.fractional()` now returns plain integers when the fractional part rounds to a whole number, including for negative inputs. The full suite passes: 720 passed, 74 skipped.

**Cause:** `Fraction(...).limit_denominator(1000)` can round the fractional part to exactly `1/1`. The function only handled that when the whole part was nonzero and the numerator was zero, so `2.9999999` fell into the mixed-fraction branch and printed `2 1/1`. `0.9999999` and `0` fell into the plain-fraction branch and printed `1/1` and `0/1`.

**Fix** (`src/humanize/number.py`): right after the fraction is computed, if the denominator is 1, return `whole_number + numerator` as an integer. That replaces the old special case, which only covered the zero-numerator path.

**Outputs checked:**
- `2.9999999` → `3`
- `0.9999999` → `1`
- `0` → `0`
- `-2.9999999` → `-3`
- `-0.9999999` → `-1`
- `-1.3` → `-1 3/10` (unchanged)
- `-0.5` → `-1/2` (unchanged)

**Tests:** I added five cases to the existing `test_fractional` parametrize list in `tests/test_number.py` for the inputs above. I did not change any existing expectations.

I have not committed anything.
