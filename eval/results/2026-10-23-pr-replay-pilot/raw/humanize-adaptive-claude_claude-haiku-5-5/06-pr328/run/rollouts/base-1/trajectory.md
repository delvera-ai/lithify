# trajectory base-1

final message:
`metric()` now moves to the next prefix when rounding reaches 1000, so the three reported cases give `1.00 kV`, `1.00 MV` and `1.00 mV`.

The fix is in `src/humanize/number.py`. The prefix was chosen from the unrounded exponent, so a mantissa that rounded up to `1000` kept the smaller prefix. The function now formats the mantissa first and, if it reaches 1000 below the largest prefix, rescales one step up before picking the prefix. Values at the largest prefix (Q) are left as they were, so they still print `1000 QV`. Negative values are handled through `abs()`.

I added regression cases to `tests/test_number.py`: the three reported inputs, a negative `-999.9`, `0.9999` (which now gives `1.00`), and the Q boundary. The project's test command passes with 710 passed and 69 skipped. I didn't check whether the skips were already there before this change. A sweep of exponents -29 to 30 across several mantissas and precisions found no output with a mantissa of 1000 or more.

Nothing is committed yet. Say if you want a commit or PR.

## events
[tool_use Bash] {"command": "grep -n \"def metric\" -A80 src/humanize/*.py | head -150", "description": "Locate metric function source"}
[tool_result] src/humanize/number.py:502:def metric(value: float, unit: str = "", precision: int = 3) -> str:
src/humanize/number.py-503-    """Return a value with a metric SI unit-prefix appended.
src/humanize/number.py-504-
src/humanize/number.py-505-    Examples:
src/humanize/number.py-506-        ```pycon
src/humanize/number.py-507-        >>> metric(1500, "V")
src/humanize/number.py-508-        '1.50 kV'
src/humanize/number.py-509-        >>> metric(2e8, "W")
src/humanize/number.py-510-        '200 MW'
s
…[2284 chars elided]…
umanize/number.py-551-    else:
src/humanize/number.py-552-        ordinal_ = ""
src/humanize/number.py-553-    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
src/humanize/number.py-554-    if not (unit or ordinal_) or unit in ("°", "′", "″"):
src/humanize/number.py-555-        space = ""
src/humanize/number.py-556-    else:
src/humanize/number.py-557-        space = " "
src/humanize/number.py-558-
src/humanize/number.py-559-    return f"{value_}{space}{ordinal_}{unit}"
[assistant] The bug is in `metric()` at `src/humanize/number.py:546-553`: the prefix is picked from the unrounded exponent, so a mantissa that rounds up to `1000` never moves to the next prefix. I'll make the rounding check, then re-scale, before choosing the ordinal. Let me check the existing tests first.
[tool_use Bash] {"command": "grep -rn \"metric\" tests/ | head -40", "description": "Find existing metric tests"}
[tool_result] tests/test_benchmarks.py:44:def test_metric(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:45:    benchmark(humanize.metric, 1500, "W")
tests/test_number.py:311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:312:    assert humanize.metric(*test_args) == expected
[tool_use Bash] {"command": "sed -n 270,315p tests/test_number.py", "description": "View metric test cases"}
[tool_result]         ([-1500, "V"], "-1.50 kV"),
        ([0.12], "120 m"),
        ([0.012], "12.0 m"),
        ([0.0012], "1.20 m"),
        ([0.00012], "120 μ"),
        ([1e-23], "10.0 y"),
        ([1e-24], "1.00 y"),
        ([1e-25], "100 r"),
        ([1e-26], "10.0 r"),
        ([1, "°"], "1.00°"),
        ([0.1, "°"], "100m°"),
        ([100], "100"),
        ([0.1], "100 m"),
        ([1.5123, "", 0], "2"),
        ([10.5123, "", 0], "11"),
        ([10.5123, "", 1], "11"),
        ([10.5123, "", 
…[300 chars elided]…
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
[assistant] The existing tests cover only non-boundary cases, so I'll add the three reported cases plus the top-prefix boundary. Now the fix:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142356-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py", "old_string": "    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n
…[365 chars elided]…
9 -> \"1000\"), so move up one prefix.\n        exponent = exponent // 3 * 3 + 3\n        value /= 1000\n        value_ = format(value, f\".{int(max(0, precision - exponent % 3 - 1))}f\")\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n        ordinal_ = \"\"\n    if not"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142356-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py has been updated successfully.
[assistant] Next, I'll add regression tests for the reported cases, the negative sign, and the top-prefix boundary.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142356-bug-humanize-metric-can-output-a/base-1/tests/test_number.py", "old_string": "        ([1e-26], \"10.0 r\"),\n        ([1, \"\u00b0\"], \"1.00\u00b0\"),", "new_string": "        ([1e-26], \"10.0 r\"),\n        ([999.9, \"V\"], \"1.00 kV\"),\n        ([-999.9, \"V\"], \"-1.00 kV\"),\n        ([999999, \"V\"], \"1.00 MV\"),\n        ([0.0009999, \"V\"], \"1.00 mV\"),\n        ([0.9999], \"1.00\"),\n        ([999.9e30, \"V\"], \"1000 QV\"),\n        ([1, \"\u00b0\"], \"1.00\u00b0\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142356-bug-humanize-metric-can-output-a/base-1/tests/test_number.py has been updated successfully.
[assistant] Now I'll run the project's checks using the interpreter and command from the project's CLAUDE.md.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run project test suite"}
[tool_result] ........................................................................ [ 64%]
........................................................................ [ 73%]
........................................................................ [ 83%]
........................................................................ [ 92%]
...........................................................              [100%]

------------------------------------------------------------------------------------------- benchma
…[3497 chars elided]…
,291.9786 (36.91)    208.9655 (205.14)   530;1316      185.0463 (0.03)      30770           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
710 passed, 69 skipped in 6.47s
[assistant] The suite passes. I'll also sweep many magnitudes to confirm no mantissa ever prints as `1000` below the top prefix, and check the reported examples directly.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -I -c '\nimport humanize, math, re\nfor v in [999.9, 999999, 0.0009999]: print(repr(humanize.metric(v, \"V\")))\nbad = []\nfor e in range(-31, 34):\n    for m in [9.9999, 9.99999, 9.9, 1.0, 5.5]:\n        for p in [1,
…[81 chars elided]…
*m*10**e, \"V\", p)\n                num = re.match(r\"-?([\\d.]+)\", out)\n                if num and float(num.group(1)) >= 1000 and not out.endswith((\"QV\", \"x 10\u2074\u2070\")) and \"x 10\" not in out and \"QV\" not in out:\n                    bad.append((e, m, p, out))\nprint(\"bad:\", bad[:10], len(bad))\n'", "description": "Check reported examples and sweep for leftover 1000 mantissas"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
[assistant] `-I` ignores `PYTHONPATH`, and this is the project's own source rather than downloaded code, so I'll drop that flag.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c '\nimport humanize, math, re\nfor v in [999.9, 999999, 0.0009999]: print(repr(humanize.metric(v, \"V\")))\nbad = []\nfor e in range(-29, 31):\n    for m in [9.9999, 9.99999, 9.9, 1.0, 5.5]:\n        for p in [1,2,3,4,5]:\n            for s in (1, -1):\n                out = humanize.metric(s*m*10**e, \"V\", p)\n                num = re.match(r\"-?([\\d.]+)\", out)\n                if num and float(num.group(1)) >= 1000:\n                    bad.append((e, m, p, out))\nprint(\"bad:\", bad[:10], len(bad))\n'", "description": "Check reported examples and sweep for leftover 1000 mantissas"}
[tool_result] '1.00 kV'
'1.00 MV'
'1.00 mV'
bad: [] 0
[assistant] `metric()` now moves to the next prefix when rounding reaches 1000, so the three reported cases give `1.00 kV`, `1.00 MV` and `1.00 mV`.

The fix is in `src/humanize/number.py`. The prefix was chosen from the unrounded exponent, so a mantissa that rounded up to `1000` kept the smaller prefix. The function now formats the mantissa first and, if it reaches 1000 below the largest prefix, rescales one step up before picking the prefix. Values at the largest prefix (Q) are left as they were, so they still print `1000 QV`. Negative values are handled through `abs()`.

I added regression cases to `tests/test_number.py`: the three reported inputs, a negative `-999.9`, `0.9999` (which now gives `1.00`), and the Q boundary. The project's test command passes with 710 passed and 69 skipped. I didn't check whether the skips were already there before this change. A sweep of exponents -29 to 30 across several mantissas and precisions found no output with a mantissa of 1000 or more.

Nothing is committed yet. Say if you want a commit or PR.
