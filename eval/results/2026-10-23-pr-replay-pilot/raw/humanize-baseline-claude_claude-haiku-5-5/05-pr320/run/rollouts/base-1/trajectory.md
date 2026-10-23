# trajectory base-1

final message:
Negative mixed numbers now render with a single minus sign: `fractional(-1.3)` gives `"-1 3/10"` and `fractional(-2.5)` gives `"-2 1/2"`. The full suite passes (704 passed, 69 skipped).

The cause was in `src/humanize/number.py`. `int(-1.3)` truncates to `-1`, but `Fraction(-1.3 - (-1))` keeps the negative sign on its numerator, so the mixed-number branch printed `-1 -3/10`. The fix takes the absolute value of the numerator in that branch only. Values with no whole part, like `-0.3`, still come out as `-3/10` because the sign stays on the fraction there.

I added three cases to `test_fractional` in `tests/test_number.py`: `-0.3`, `-1.3` and `-2.5`. I did not commit the change.

## events
[tool_use Bash] {"command": "grep -rn \"fractional\" --include=*.py . | head -50", "description": "Locate fractional function references"}
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
umber.py:310:    """Convert to fractional number.
src/humanize/number.py:315:    This function returns a human-readable fractional number in form of fractions and
src/humanize/number.py:327:        >>> fractional(0.3)
src/humanize/number.py:329:        >>> fractional(1.3)
src/humanize/number.py:331:        >>> fractional(float(1/3))
src/humanize/number.py:333:        >>> fractional(1)
src/humanize/number.py:335:        >>> fractional("ten")
src/humanize/number.py:337:        >>> fractional(None)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py", "offset": 300, "limit": 90}
[tool_result] 300	            return _format_not_finite(float(value))
301	        value = int(value)
302	    except (TypeError, ValueError):
303	        return str(value)
304	    if not 0 <= value < 10:
305	        return str(value)
306	    return _(_APNUMBER_WORDS[value])
307	
308	
309	def fractional(value: NumberOrString) -> str:
310	    """Convert to fractional number.
311	
312	    There will be some cases where one might not want to show ugly decimal places for
313	    floats and decimals.
314	
315	    Th
…[1800 chars elided]…
sion: int = 2) -> str:
374	    """Return number in string scientific notation z.wq x 10ⁿ.
375	
376	    Examples:
377	        ```pycon
378	        >>> scientific(float(0.3))
379	        '3.00 x 10⁻¹'
380	        >>> scientific(int(500))
381	        '5.00 x 10²'
382	        >>> scientific(-1000)
383	        '-1.00 x 10³'
384	        >>> scientific(1000, 1)
385	        '1.0 x 10³'
386	        >>> scientific(1000, 3)
387	        '1.000 x 10³'
388	        >>> scientific("99")
389	        '9.90 x 10¹'
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py", "offset": 160, "limit": 35}
[tool_result] 160	    ],
161	)
162	def test_apnumber(test_input: int | str, expected: str) -> None:
163	    assert humanize.apnumber(test_input) == expected
164	
165	
166	@pytest.mark.parametrize(
167	    "test_input, expected",
168	    [
169	        (1, "1"),
170	        (2.0, "2"),
171	        (4.0 / 3.0, "1 1/3"),
172	        (5.0 / 6.0, "5/6"),
173	        ("7", "7"),
174	        ("8.9", "8 9/10"),
175	        ("ten", "ten"),
176	        (None, "None"),
177	        (1 / 3, "1/3"),
178	        (1.5, "1 1/2"),
179	        (0.3, "3/10"),
180	        (0.333, "333/1000"),
181	        (math.nan, "NaN"),
182	        (math.inf, "+Inf"),
183	        (-math.inf, "-Inf"),
184	        ("nan", "NaN"),
185	        ("-inf", "-Inf"),
186	    ],
187	)
188	def test_fractional(test_input: float | str, expected: str) -> None:
189	    assert humanize.fractional(test_input) == expected
190	
191	
192	@pytest.mark.parametrize(
193	    "test_args, expected",
194	    [
[assistant] The cause is clear: `int(-1.3)` truncates to `-1`, but `Fraction(-1.3 - -1)` keeps the negative sign on the numerator (`-3/10`), so the mixed branch prints both signs. I'll take the absolute value of the numerator in the mixed-number branch only, so the whole-number-only case (`-0.3` → `-3/10`) keeps its sign.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py", "old_string": "    return f\"{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\"", "new_string": "    # the sign is carried by the whole number, so the fraction part must be positive\n    return f\"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py", "old_string": "        (0.3, \"3/10\"),\n        (0.333, \"333/1000\"),", "new_string": "        (0.3, \"3/10\"),\n        (-0.3, \"-3/10\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (0.333, \"333/1000\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142307-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py has been updated successfully.
[assistant] Now I'll run the project's test command from CLAUDE.md.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run project test suite"}
[tool_result] ........................................................................ [ 65%]
........................................................................ [ 74%]
........................................................................ [ 83%]
........................................................................ [ 93%]
.....................................................                    [100%]

--------------------------------------------------------------------------------------------- bench
…[3573 chars elided]…
.0182 (37.99)    166.0082 (46.48)    422;1560      185.7370 (0.03)      29484           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
704 passed, 69 skipped in 6.96s
[assistant] Negative mixed numbers now render with a single minus sign: `fractional(-1.3)` gives `"-1 3/10"` and `fractional(-2.5)` gives `"-2 1/2"`. The full suite passes (704 passed, 69 skipped).

The cause was in `src/humanize/number.py`. `int(-1.3)` truncates to `-1`, but `Fraction(-1.3 - (-1))` keeps the negative sign on its numerator, so the mixed-number branch printed `-1 -3/10`. The fix takes the absolute value of the numerator in that branch only. Values with no whole part, like `-0.3`, still come out as `-3/10` because the sign stays on the fraction there.

I added three cases to `test_fractional` in `tests/test_number.py`: `-0.3`, `-1.3` and `-2.5`. I did not commit the change.
