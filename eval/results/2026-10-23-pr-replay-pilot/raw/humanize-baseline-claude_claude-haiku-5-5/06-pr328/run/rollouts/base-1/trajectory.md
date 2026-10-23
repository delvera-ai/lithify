# trajectory base-1

final message:
`humanize.metric()` now moves to the next SI prefix when rounding carries the mantissa to 1000. All three cases from the report now return the expected output: `999.9` gives `1.00 kV`, `999999` gives `1.00 MV`, and `0.0009999` gives `1.00 mV`.

The fix is in `src/humanize/number.py`. After formatting the mantissa, if it reads 1000 or more and the value isn't already at the largest prefix (Q), the exponent moves up one prefix step and the mantissa is formatted again. Values already at Q are unchanged, so `999999e27` still gives `1000 QV`.

I also added regression cases to `test_metric` in `tests/test_number.py`. They cover the three reported inputs, a value that rounds up to 1 without changing prefix, a negative value, and the Q boundary. I added cases rather than editing any existing ones.

The full suite passes with the project's test command: 710 passed, 69 skipped. I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"def metric\" src/ && git status --short | head", "description": "Locate metric function and check git status"}
[tool_result] src/humanize/number.py:502:def metric(value: float, unit: str = "", precision: int = 3) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142344-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py", "offset": 480, "limit": 90}
[tool_result] 480	    if floor is not None and value < floor:
481	        value = floor
482	        token = floor_token
483	    elif ceil is not None and value > ceil:
484	        value = ceil
485	        token = ceil_token
486	    else:
487	        token = ""
488	
489	    if isinstance(format, str):
490	        return token + format.format(value)
491	
492	    if callable(format):
493	        return token + format(value)
494	
495	    msg = (
496	        "Invalid format. Must be either a valid formatting strin
…[1579 chars elided]…
e /= 10 ** (exponent // 3 * 3)
547	    if exponent >= 3:
548	        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
549	    elif exponent < 0:
550	        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
551	    else:
552	        ordinal_ = ""
553	    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
554	    if not (unit or ordinal_) or unit in ("°", "′", "″"):
555	        space = ""
556	    else:
557	        space = " "
558	
559	    return f"{value_}{space}{ordinal_}{unit}"
560	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142344-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py", "old_string": "    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n
…[468 chars elided]…
nt < 30:\n        exponent = exponent // 3 * 3 + 3\n        value_ = format(\n            value / 10**exponent,\n            f\".{int(max(0, precision - exponent % 3 - 1))}f\",\n        )\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n        ordinal_ = \"\"\n    if not"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142344-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nfrom humanize import metric\nfor v,u in [(999.9,'V'),(999999,'V'),(0.0009999,'V'),(1500,'V'),(2e8,'W'),(220e-6,'F'),(1e-14,''),(0.9999,'A'),(-999.9,'V'),(999999e27,'V'),(1e40,''),(999.4,'V'),(0,'V')]:\n    print(repr(v), repr(metric(v,u)))\nprint(metric(1e-14, precision=4))\n\" && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check the reported cases and run the test suite"}
[tool_result] 999.9 '1.00 kV'
999999 '1.00 MV'
0.0009999 '1.00 mV'
1500 '1.50 kV'
200000000.0 '200 MW'
0.00022 '220 μF'
1e-14 '10.0 f'
0.9999 '1.00 A'
-999.9 '-1.00 kV'
9.99999e+32 '1000 QV'
1e+40 '1.00 x 10⁴⁰'
999.4 '999 V'
0 '0.00 V'
10.00 f
test_naturalsize        415.9810 (3.20)      18,708.0004 (3.42)       561.0564 (3.63)       195.0077 (2.67)       542.0006 (3.73)      83.9937 (>1000.0)  978;2268    1,782.3519 (0.28)     193537           1
test_intcomma           457.9779 (3.52)      54,083.0079 (9.87)
…[1501 chars elided]…
74.9827 (37.02)    333.0060 (>1000.0)  907;3465      179.7821 (0.03)      27714           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
704 passed, 69 skipped in 7.72s
[assistant] The fix works and the suite passes. I'll add regression tests next to the existing `metric` tests.
[tool_use Bash] {"command": "grep -rn \"metric\" tests/ | head -40", "description": "Find existing metric tests"}
[tool_result] tests/test_benchmarks.py:44:def test_metric(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:45:    benchmark(humanize.metric, 1500, "W")
tests/test_number.py:311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:312:    assert humanize.metric(*test_args) == expected
[tool_use Bash] {"command": "sed -n 280,315p tests/test_number.py", "description": "View existing metric test parameters"}
[tool_result]         ([0.1, "°"], "100m°"),
        ([100], "100"),
        ([0.1], "100 m"),
        ([1.5123, "", 0], "2"),
        ([10.5123, "", 0], "11"),
        ([10.5123, "", 1], "11"),
        ([10.5123, "", 2], "11"),
        ([10.5123, "", 3], "10.5"),
        ([1, "", 0], "1"),
        ([10, "", 0], "10"),
        ([100, "", 0], "100"),
        ([1000, "", 0], "1 k"),
        ([1, "", 1], "1"),
        ([10, "", 1], "10"),
        ([100, "", 1], "100"),
        ([1000, "", 1], "1 k"),
        ([1
…[4 chars elided]…
, 2], "1.0"),
        ([10, "", 2], "10"),
        ([100, "", 2], "100"),
        ([1000, "", 2], "1.0 k"),
        ([1, "", 3], "1.00"),
        ([10, "", 3], "10.0"),
        ([100, "", 3], "100"),
        ([1000, "", 3], "1.00 k"),
        ([math.nan], "NaN"),
        ([math.nan, "m"], "NaN"),
        ([math.inf], "+Inf"),
        ([-math.inf], "-Inf"),
    ],
    ids=str,
)
def test_metric(test_args: list[typing.Any], expected: str) -> None:
    assert humanize.metric(*test_args) == expected
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142344-bug-humanize-metric-can-output-a/base-1/tests/test_number.py", "old_string": "        ([1000, \"\", 3], \"1.00 k\"),\n        ([math.nan], \"NaN\"),", "new_string": "        ([1000, \"\", 3], \"1.00 k\"),\n        ([999.9, \"V\"], \"1.00 kV\"),\n        ([999999, \"V\"], \"1.00 MV\"),\n        ([0.0009999, \"V\"], \"1.00 mV\"),\n        ([0.9999, \"A\"], \"1.00 A\"),\n        ([-999.9, \"V\"], \"-1.00 kV\"),\n        ([999999e27, \"V\"], \"1000 QV\"),\n        ([math.nan], \"NaN\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142344-bug-humanize-metric-can-output-a/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_number.py -k metric 2>&1 | tail -3 && PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git status --short", "description": "Run metric tests and full suite, check git status"}
[tool_result] .................................................................        [100%]
65 passed, 163 deselected in 0.02s
710 passed, 69 skipped in 6.72s
 M src/humanize/number.py
 M tests/test_number.py
[assistant] `humanize.metric()` now moves to the next SI prefix when rounding carries the mantissa to 1000. All three cases from the report now return the expected output: `999.9` gives `1.00 kV`, `999999` gives `1.00 MV`, and `0.0009999` gives `1.00 mV`.

The fix is in `src/humanize/number.py`. After formatting the mantissa, if it reads 1000 or more and the value isn't already at the largest prefix (Q), the exponent moves up one prefix step and the mantissa is formatted again. Values already at Q are unchanged, so `999999e27` still gives `1000 QV`.

I also added regression cases to `test_metric` in `tests/test_number.py`. They cover the three reported inputs, a value that rounds up to 1 without changing prefix, a negative value, and the Q boundary. I added cases rather than editing any existing ones.

The full suite passes with the project's test command: 710 passed, 69 skipped. I haven't committed anything.
