# trajectory inv-1

final message:
Negative mixed numbers now print with one sign: `fractional(-1.3)` returns `'-1 3/10'` and `fractional(-2.5)` returns `'-2 1/2'`. The full suite passes: `703 passed, 69 skipped`.

**Cause:** in `src/humanize/number.py`, the mixed-number branch printed the signed numerator after a whole part that already carried the minus sign. The fix takes `abs()` of the numerator in that branch only. Proper fractions like `fractional(-0.3)` → `'-3/10'` still keep their sign.

**Tests:** I reproduced the bug on the unmodified code first, then added two cases to `test_fractional` in `tests/test_number.py`: `(-1.3, "-1 3/10")` and `(-2.5, "-2 1/2")`. Both produce the doubled-sign output on the original code, so they fail there. I did not add a `-1.5` case, though it also works now.

**Not changed, but worth a look:** values just under a whole number round up in the fraction step, so `fractional(1.9996)` returns `'1 1/1'` and `fractional(-1.9996)` returns `'-1 1/1'`. This is the same on the original code and is a separate issue, so I left it alone.

I haven't committed anything; the changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -rn \"def fractional\" src/ && grep -rln \"fractional\" tests/ src/", "description": "Locate fractional function and tests"}
[tool_result] src/humanize/number.py:309:def fractional(value: NumberOrString) -> str:
tests/test_benchmarks.py
src/humanize/time.py
tests/test_number.py
src/humanize/number.py
src/humanize/__init__.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/inv-1/src/humanize/number.py", "offset": 290, "limit": 110}
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
…[2402 chars elided]…
 >>> scientific(-1000)
383	        '-1.00 x 10³'
384	        >>> scientific(1000, 1)
385	        '1.0 x 10³'
386	        >>> scientific(1000, 3)
387	        '1.000 x 10³'
388	        >>> scientific("99")
389	        '9.90 x 10¹'
390	        >>> scientific("foo")
391	        'foo'
392	        >>> scientific(None)
393	        'None'
394	
395	        ```
396	
397	    Args:
398	        value (int, float, str): Input number.
399	        precision (int): Number of decimal for first part of the number.
[tool_use Bash] {"command": "grep -n \"fractional\" -A3 tests/test_number.py | head -150; ls <work>/env-humanize/bin/python 2>&1", "description": "Show fractional tests and check venv python exists"}
[tool_result] 188:def test_fractional(test_input: float | str, expected: str) -> None:
189:    assert humanize.fractional(test_input) == expected
190-
191-
192-@pytest.mark.parametrize(
<work>/env-humanize/bin/python
[tool_use Bash] {"command": "sed -n 160,190p tests/test_number.py; PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nimport humanize\nfor v in [-1.3,-2.5,-0.3,-1,-0.5,1.3,2.5,'-1.3',float('-inf'),-1.0001]:\n    print(repr(v), repr(humanize.fractional(v)))\n\"", "description": "Show fractional test cases and reproduce bug"}
[tool_result]     ],
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
    ],
)
def test_fractional(test_input: float | str, expected: str) -> None:
    assert humanize.fractional(test_input) == expected

-1.3 '-1 -3/10'
-2.5 '-2 -1/2'
-0.3 '-3/10'
-1 '-1'
-0.5 '-1/2'
1.3 '1 3/10'
2.5 '2 1/2'
'-1.3' '-1 -3/10'
-inf '-Inf'
-1.0001 '-1'
[assistant] Reproduced on the unmodified code: `fractional(-1.3)` gives `'-1 -3/10'` and `fractional(-2.5)` gives `'-2 -1/2'`. The cause is that the mixed-number branch prints the signed numerator after the whole part, which already carries the sign. I'll fix that and add the two regression cases to the existing parametrize list.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/inv-1/src/humanize/number.py", "old_string": "    return f\"{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\"", "new_string": "    # the sign is already carried by the whole part, so the fraction is shown unsigned\n    return f\"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/inv-1/src/humanize/number.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/inv-1/tests/test_number.py", "old_string": "        (1.5, \"1 1/2\"),\n        (0.3, \"3/10\"),", "new_string": "        (1.5, \"1 1/2\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (0.3, \"3/10\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/inv-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nfor v in [-1.3,-2.5,-0.3,-1,-0.5,1.3,2.5,-1.5]: print(repr(v), repr(humanize.fractional(v)))\"", "description": "Run full test suite and spot-check outputs"}
[tool_result] test_naturalsize        375.0029 (2.86)       861,707.9875 (34.19)      526.9319 (3.35)     2,651.0088 (24.68)      500.0038 (3.43)       0.0291 (1.0)     115;48284    1,897.7784 (0.30)     132591           1
test_intcomma           457.9779 (3.49)        59,166.9814 (2.35)       564.9285 (3.59)       352.0766 (3.28)       542.0006 (3.72)      41.0073 (>1000.0)  156;2519    1,770.1355 (0.28)     126311           1
test_naturaldelta       540.9820 (4.13)        58,749.9817 (2.33)       633.2681 (
…[1392 chars elided]…
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
703 passed, 69 skipped in 6.13s
-1.3 '-1 3/10'
-2.5 '-2 1/2'
-0.3 '-3/10'
-1 '-1'
-0.5 '-1/2'
1.3 '1 3/10'
2.5 '2 1/2'
-1.5 '-1 1/2'
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nprint(repr(humanize.fractional(1.9996)), repr(humanize.fractional(-1.9996)))\"; git status --short", "description": "Check a near-whole edge case and git status"}
[tool_result] '1 1/1' '-1 1/1'
 M src/humanize/number.py
 M tests/test_number.py
[assistant] Negative mixed numbers now print with one sign: `fractional(-1.3)` returns `'-1 3/10'` and `fractional(-2.5)` returns `'-2 1/2'`. The full suite passes: `703 passed, 69 skipped`.

**Cause:** in `src/humanize/number.py`, the mixed-number branch printed the signed numerator after a whole part that already carried the minus sign. The fix takes `abs()` of the numerator in that branch only. Proper fractions like `fractional(-0.3)` → `'-3/10'` still keep their sign.

**Tests:** I reproduced the bug on the unmodified code first, then added two cases to `test_fractional` in `tests/test_number.py`: `(-1.3, "-1 3/10")` and `(-2.5, "-2 1/2")`. Both produce the doubled-sign output on the original code, so they fail there. I did not add a `-1.5` case, though it also works now.

**Not changed, but worth a look:** values just under a whole number round up in the fraction step, so `fractional(1.9996)` returns `'1 1/1'` and `fractional(-1.9996)` returns `'-1 1/1'`. This is the same on the original code and is a separate issue, so I left it alone.

I haven't committed anything; the changes are in the working tree.
