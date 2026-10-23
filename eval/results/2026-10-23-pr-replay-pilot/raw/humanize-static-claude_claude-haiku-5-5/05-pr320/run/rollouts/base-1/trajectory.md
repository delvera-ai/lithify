# trajectory base-1

final message:
Fixed. `fractional(-1.3)` now returns `"-1 3/10"` and `fractional(-2.5)` returns `"-2 1/2"`. The full suite passes: 706 passed, 69 skipped. I did not run the skipped tests or the doctests separately.

The cause was in `src/humanize/number.py`. For negative input, `int()` truncates toward zero, so the whole part and the fraction both carried the minus sign. The function now formats the absolute value and applies the sign once.

Two edge cases I checked:
- `-0.3` still gives `"-3/10"`.
- `-0.0001` gives `"0/1"`, the same as before, so the fix doesn't introduce a `"-0/1"` output.

I added cases to `test_fractional` in `tests/test_number.py`: `-1.3`, `-2.5`, `-1.0`, `-0.3` and `-0.0001`. No existing test was changed.

I did not commit anything. The changes are in the working tree of this worktree.

## events
[tool_use Bash] {"command": "grep -rn \"fractional\" src/ tests/ | head -50", "description": "Locate fractional function and its tests"}
[tool_result] src/humanize/time.py:483:    A custom `format` can be specified to control how the fractional part
src/humanize/time.py:621:    # When adjusting we should not deal anymore with fractional days as all rounding has
src/humanize/__init__.py:11:    fractional,
src/humanize/__init__.py:35:    "fractional",
src/humanize/number.py:309:def fractional(value: NumberOrString) -> str:
src/humanize/number.py:310:    """Convert to fractional number.
src/humanize/number.py:315:    This function returns a human
…[218 chars elided]…
(1/3))
src/humanize/number.py:333:        >>> fractional(1)
src/humanize/number.py:335:        >>> fractional("ten")
src/humanize/number.py:337:        >>> fractional(None)
tests/test_benchmarks.py:32:def test_fractional(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:33:    benchmark(humanize.fractional, 1.5)
tests/test_number.py:188:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:189:    assert humanize.fractional(test_input) == expected
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py", "offset": 290, "limit": 90}
[tool_result] 290	
291	    Returns:
292	        str: For numbers 0-9, the number spelled out. Otherwise, the number. This always
293	            returns a string unless the value was not `int`-able, then `str(value)`
294	            is returned.
295	    """
296	    import math
297	
298	    try:
299	        if not math.isfinite(float(value)):
300	            return _format_not_finite(float(value))
301	        value = int(value)
302	    except (TypeError, ValueError):
303	        return str(value)
304	    if no
…[1828 chars elided]…
variants of that integer like 1.0000)
365	        return f"{whole_number:.0f}"
366	
367	    if not whole_number:
368	        return f"{numerator:.0f}/{denominator:.0f}"
369	
370	    return f"{whole_number:.0f} {numerator:.0f}/{denominator:.0f}"
371	
372	
373	def scientific(value: NumberOrString, precision: int = 2) -> str:
374	    """Return number in string scientific notation z.wq x 10ⁿ.
375	
376	    Examples:
377	        ```pycon
378	        >>> scientific(float(0.3))
379	        '3.00 x 10⁻¹'
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py", "offset": 160, "limit": 40}
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
178	        (1.5, "1 1/2
…[136 chars elided]…
   (-math.inf, "-Inf"),
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
195	        ([1000], "1.00 x 10³"),
196	        ([-1000], "-1.00 x 10³"),
197	        ([5.5], "5.50 x 10⁰"),
198	        ([5781651000], "5.78 x 10⁹"),
199	        (["1000"], "1.00 x 10³"),
[assistant] The bug is in the mixed-number branch: for negative input, `int()` truncates toward zero, so the whole part is negative while `number - whole_number` is also negative, and the sign lands on both parts. I'll get a baseline test run first, using the project's documented command.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ls -la $PY 2>&1; PYTHONPATH=src $PY -c \"import humanize,sys; print(humanize.fractional(-1.3), humanize.fractional(-2.5), humanize.fractional(-0.3))\" 2>&1", "description": "Check project interpreter and reproduce the bug"}
[tool_result] lrwxr-xr-x@ 1 donovan  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
-1 -3/10 -2 -1/2 -3/10
[assistant] Reproduced: `-1 -3/10` and `-2 -1/2`. Now the fix. I'll take the sign from the input and format the absolute value, so the whole part and the fraction are both positive. I'm keeping the `-0/1` case from appearing for tiny negatives like `-0.0001`, which currently prints `0/1`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py", "old_string": "    whole_number = int(number)\n    frac = Fraction(number - whole_number).limit_denominator(1000)\n    numerator = frac.numerator\n    denominator = frac.denominator\n    if whole_number and not numerator and deno
…[693 chars elided]…
umerator) else \"\"\n    if whole_number and not numerator and denominator == 1:\n        # this means that an integer was passed in\n        # (or variants of that integer like 1.0000)\n        return f\"{sign}{whole_number:.0f}\"\n\n    if not whole_number:\n        return f\"{sign}{numerator:.0f}/{denominator:.0f}\"\n\n    return f\"{sign}{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py", "old_string": "        (0.333, \"333/1000\"),\n        (math.nan, \"NaN\"),", "new_string": "        (0.333, \"333/1000\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (-1.0, \"-1\"),\n        (-0.3, \"-3/10\"),\n        (-0.0001, \"0/1\"),\n        (math.nan, \"NaN\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py has been updated successfully.
[assistant] Now the full project test suite, plus a check that the new cases behave as intended.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src $PY -c \"import humanize as h; print([h.fractional(x) for x in (-1.3,-2.5,-0.3,-1.0,-0.0001,1.3,0.3,-1000/999)])\"", "description": "Run full test suite and spot-check negative values"}
[tool_result] test_naturalsize        375.0029 (2.97)      71,999.9953 (27.83)      503.0781 (3.48)       370.1409 (12.33)      500.0038 (3.58)      41.0073 (>1000.0)    477;9125    1,987.7629 (0.29)     184604           1
test_intcomma           416.0102 (3.30)     144,332.9966 (55.79)      536.4321 (3.71)       601.5290 (20.04)      540.9820 (3.87)      41.9968 (>1000.0)    314;4201    1,864.1690 (0.27)     129033           1
test_naturaldelta       500.0038 (3.96)     108,625.0122 (41.99)      636.0627 (4.
…[1365 chars elided]…
890           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
706 passed, 69 skipped in 6.03s
['-1 3/10', '-2 1/2', '-3/10', '-1', '0/1', '1 3/10', '3/10', '-1 1/999']
[assistant] Fixed. `fractional(-1.3)` now returns `"-1 3/10"` and `fractional(-2.5)` returns `"-2 1/2"`. The full suite passes: 706 passed, 69 skipped. I did not run the skipped tests or the doctests separately.

The cause was in `src/humanize/number.py`. For negative input, `int()` truncates toward zero, so the whole part and the fraction both carried the minus sign. The function now formats the absolute value and applies the sign once.

Two edge cases I checked:
- `-0.3` still gives `"-3/10"`.
- `-0.0001` gives `"0/1"`, the same as before, so the fix doesn't introduce a `"-0/1"` output.

I added cases to `test_fractional` in `tests/test_number.py`: `-1.3`, `-2.5`, `-1.0`, `-0.3` and `-0.0001`. No existing test was changed.

I did not commit anything. The changes are in the working tree of this worktree.
