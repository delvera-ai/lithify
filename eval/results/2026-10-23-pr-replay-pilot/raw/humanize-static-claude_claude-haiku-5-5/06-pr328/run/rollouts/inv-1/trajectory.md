# trajectory inv-1

final message:
`metric()` now moves to the next SI prefix when rounding pushes the mantissa to 1000, so all three reported outputs are fixed. The full suite passes: 710 passed, 69 skipped. The skips are all i18n tests that need a `.mo` generation script, unrelated to this change.

**Results on the reported inputs:**
- `metric(999.9, "V")` → `'1.00 kV'` (was `'1000 V'`)
- `metric(999999, "V")` → `'1.00 MV'` (was `'1000 kV'`)
- `metric(0.0009999, "V")` → `'1.00 mV'` (was `'1000 μV'`)

**The fix** (`src/humanize/number.py`, `metric`): the mantissa is formatted as before. If the rounded value is at least 1000 and a larger prefix exists, the exponent moves up one group and the mantissa is divided by 1000 and reformatted. The non-finite guard is unchanged and still runs first. The negative branch is also fixed: `metric(-999.9, "V")` → `'-1.00 kV'`, with one leading minus.

**Choices I made:**
- **Largest prefix left alone.** `metric(999.9e30, "V")` still returns `'1000 QV'`, since Q is the largest prefix and the spec says those values stay unchanged. I didn't add a test for it because its output doesn't change.
- **Tests added** to the existing `test_metric` parametrize list in `tests/test_number.py`: `999.9 V`, `999999 V`, `0.0009999 V`, `-999.9 V`, `999.9` at precision 1 (`'1 k'`), and `999.9999` at precision 4 (`'1.000 kV'`). I checked each against the original code with `compare_outputs.py`, and each one changed.
- **Docstring examples** (`1.50 kV`, `200 MW`, `220 μF`, `10.00 f`, `1.00 x 10⁴⁰`) take paths this change doesn't touch, so I left them alone.

I did not run `ruff` or `mypy`, since neither is installed in the project environment. I also haven't committed the change.

## events
[assistant] I'll start by reading the `metric` code and the project's memory notes for the interpreter path.
[tool_use Bash] {"command": "grep -n \"def metric\" -A80 src/humanize/number.py; echo ---; cat .lithify/memory.md 2>/dev/null; ls .lithify; echo ---; git status --short", "description": "Read metric function and project notes"}
[tool_result] 502:def metric(value: float, unit: str = "", precision: int = 3) -> str:
503-    """Return a value with a metric SI unit-prefix appended.
504-
505-    Examples:
506-        ```pycon
507-        >>> metric(1500, "V")
508-        '1.50 kV'
509-        >>> metric(2e8, "W")
510-        '200 MW'
511-        >>> metric(220e-6, "F")
512-        '220 μF'
513-        >>> metric(1e-14, precision=4)
514-        '10.00 f'
515-
516-        ```
517-
518-    The unit prefix is always chosen so that non-signifi
…[985 chars elided]…

547-    if exponent >= 3:
548-        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
549-    elif exponent < 0:
550-        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
551-    else:
552-        ordinal_ = ""
553-    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
554-    if not (unit or ordinal_) or unit in ("°", "′", "″"):
555-        space = ""
556-    else:
557-        space = " "
558-
559-    return f"{value_}{space}{ordinal_}{unit}"
---
harness
library
state.json
---
[assistant] The bug is in the rounding step: `value_` is formatted after scaling, but the prefix is picked before rounding, so a mantissa that rounds up to 1000 keeps the smaller prefix. Next I'll load the project's number-output skill and check the test layout and the interpreter path.
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/inv-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths 
…[889 chars elided]…
t negated (`*-1` for ints, `"-"` prefixed for strings and floats). Only positive
   inputs belong there.
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[tool_use Bash] {"command": "ls <work>/env-humanize/bin/python; grep -rn \"metric\" tests/ | head -40; ls .lithify/harness", "description": "Check interpreter, find metric tests"}
[tool_result] <work>/env-humanize/bin/python
tests/test_benchmarks.py:44:def test_metric(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:45:    benchmark(humanize.metric, 1500, "W")
tests/test_number.py:311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:312:    assert humanize.metric(*test_args) == expected
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The skill's checklist confirms what I need: keep the non-finite guard first, add cases to the existing `test_metric` parametrize list, and check negatives. Next I'll reproduce the three reported outputs on the unmodified code, plus a negative input, before editing.
[tool_use Bash] {"command": "<work>/env-humanize/bin/python .lithify/harness/scripts/compare_outputs.py 'metric(999.9, \"V\")' 'metric(999999, \"V\")' 'metric(0.0009999, \"V\")' 'metric(-999.9, \"V\")' 'metric(999.9e30, \"V\")' 'metric(999.9, \"V\", 1)' 'metric(999.9999, \"V\", 4)' 2>&1; echo \"---\"; sed -n 280,312p tests/test_number.py", "description": "Reproduce metric outputs and view test list"}
[tool_result] same    metric(999.9, "V")
    HEAD: '1000 V'
same    metric(999999, "V")
    HEAD: '1000 kV'
same    metric(0.0009999, "V")
    HEAD: '1000 μV'
same    metric(-999.9, "V")
    HEAD: '-1000 V'
same    metric(999.9e30, "V")
    HEAD: '1000 QV'
same    metric(999.9, "V", 1)
    HEAD: '1000 V'
same    metric(999.9999, "V", 4)
    HEAD: '1000.0 V'
old side imported /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/compare-outputs-tb91argn/src/humanize/__init__.py
new side imported ~/.cac
…[655 chars elided]…
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
[assistant] Reproduced: all three reported outputs come out wrong on HEAD, and the negative case `-999.9` shows the same bug with a sign. Now the fix: after formatting the mantissa, if rounding reached 1000 and a larger prefix exists, move up one group and reformat. The non-finite guard and the rest of the function stay as they are.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/inv-1/src/humanize/number.py", "old_string": "    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n 
…[357 chars elided]…
x (e.g. 999.9 -> \"1000\"), so use it.\n        exponent = exponent // 3 * 3 + 3\n        value /= 1000\n        value_ = format(value, f\".{int(max(0, precision - exponent % 3 - 1))}f\")\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n        ordinal_ = \"\"\n    if not"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/inv-1/src/humanize/number.py has been updated successfully.
[assistant] The code change is in. Before adding test cases, I'll check which inputs actually change, so only those get pinned. The `999.9e30` case should stay `1000 QV`, since Q is the largest prefix.
[tool_use Bash] {"command": "<work>/env-humanize/bin/python .lithify/harness/scripts/compare_outputs.py 'metric(999.9, \"V\")' 'metric(999999, \"V\")' 'metric(0.0009999, \"V\")' 'metric(-999.9, \"V\")' 'metric(999.9e30, \"V\")' 'metric(999.9, \"\", 1)' 'metric(999.9999, \"V\", 4)' 'metric(999.4, \"V\")' 'metric(-0.0009999, \"V\")' 'metric(1e-14, precision=4)' 'metric(999.9e-30, \"V\")' 'metric(999.9e-6, \"V\")' 2>&1 | grep -v imported", "description": "Compare metric outputs before and after fix"}
[tool_result] CHANGED metric(999.9, "V")
    HEAD: '1000 V'
    work: '1.00 kV'
CHANGED metric(999999, "V")
    HEAD: '1000 kV'
    work: '1.00 MV'
CHANGED metric(0.0009999, "V")
    HEAD: '1000 μV'
    work: '1.00 mV'
CHANGED metric(-999.9, "V")
    HEAD: '-1000 V'
    work: '-1.00 kV'
same    metric(999.9e30, "V")
    HEAD: '1000 QV'
CHANGED metric(999.9, "", 1)
    HEAD: '1000'
    work: '1 k'
CHANGED metric(999.9999, "V", 4)
    HEAD: '1000.0 V'
    work: '1.000 kV'
same    metric(999.4, "V")
    HEAD: '999 V'
CHANGED metric(-0.0009999, "V")
    HEAD: '-1000 μV'
    work: '-1.00 mV'
same    metric(1e-14, precision=4)
    HEAD: '10.00 f'
CHANGED metric(999.9e-30, "V")
    HEAD: '1000 qV'
    work: '1.00 rV'
CHANGED metric(999.9e-6, "V")
    HEAD: '1000 μV'
    work: '1.00 mV'
12 expressions, 9 changed, 3 same
[assistant] Nine of the twelve inputs change, and each is a case where the mantissa rounded to 1000. The largest-prefix case (`1000 QV`) and the non-overflow cases are unchanged, so they stay out of the tests. I'll add the changed cases to the existing `test_metric` list.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/inv-1/tests/test_number.py", "old_string": "        ([1000, \"\", 3], \"1.00 k\"),\n        ([math.nan], \"NaN\"),", "new_string": "        ([1000, \"\", 3], \"1.00 k\"),\n        ([999.9, \"\", 1], \"1 k\"),\n        ([999.9, \"V\"], \"1.00 kV\"),\n        ([999.9999, \"V\", 4], \"1.000 kV\"),\n        ([-999.9, \"V\"], \"-1.00 kV\"),\n        ([999999, \"V\"], \"1.00 MV\"),\n        ([0.0009999, \"V\"], \"1.00 mV\"),\n        ([math.nan], \"NaN\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/inv-1/tests/test_number.py has been updated successfully.
[assistant] Every new test input changed in the comparison above, so each would fail on the original code. Now I'll run the project's full check command and read its final summary.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] test_naturalsize        375.0029 (2.89)      44,209.0095 (4.20)       490.9406 (3.34)       246.0618 (6.35)       499.9747 (3.52)      41.9968 (6.26)     217;2487    2,036.9064 (0.30)      75954           1
test_intcomma           416.9997 (3.21)      42,792.0022 (4.07)       560.1103 (3.81)       213.9463 (5.52)       542.0006 (3.81)      41.9968 (6.26)    1515;9258    1,785.3627 (0.26)     179083           1
test_naturaldelta       540.9820 (4.16)      31,041.0105 (2.95)       625.7023 (4.26) 
…[1271 chars elided]…
08.0140 (36.64)    208.9946 (31.15)   1047;2056      186.3543 (0.03)      22901           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
710 passed, 69 skipped in 6.65s
[assistant] The full suite passes: 710 passed, 69 skipped. I'll confirm the metric tests themselves ran and were not among the skips, and that the skips are unrelated to this change.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -p no:cacheprovider --color=no -k \"metric\" -rs -q 2>&1 | grep -E \"passed|failed|SKIP\" | tail -5; PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -p no:cacheprovider --color=no -rs -q --benchmark-disable 2>&1 | grep -E \"SKIPPED\" | sed 's/:[0-9]*:/ /' | sort | uniq -c | head; git diff --stat", "description": "Run metric tests and inspect skips and diff"}
[tool_result] 66 passed, 713 deselected in 1.15s
   5 SKIPPED [1] tests/test_i18n.py  Generate .mo with scripts/generate-translation-binaries.sh
   1 SKIPPED [44] tests/test_i18n.py  Generate .mo with scripts/generate-translation-binaries.sh
   1 SKIPPED [6] tests/test_i18n.py  Generate .mo with scripts/generate-translation-binaries.sh
   2 SKIPPED [7] tests/test_i18n.py  Generate .mo with scripts/generate-translation-binaries.sh
 src/humanize/number.py | 7 ++++++-
 tests/test_number.py   | 6 ++++++
 2 files changed, 12 insertions(+), 1 deletion(-)
[assistant] `metric()` now moves to the next SI prefix when rounding pushes the mantissa to 1000, so all three reported outputs are fixed. The full suite passes: 710 passed, 69 skipped. The skips are all i18n tests that need a `.mo` generation script, unrelated to this change.

**Results on the reported inputs:**
- `metric(999.9, "V")` → `'1.00 kV'` (was `'1000 V'`)
- `metric(999999, "V")` → `'1.00 MV'` (was `'1000 kV'`)
- `metric(0.0009999, "V")` → `'1.00 mV'` (was `'1000 μV'`)

**The fix** (`src/humanize/number.py`, `metric`): the mantissa is formatted as before. If the rounded value is at least 1000 an
…[487 chars elided]…
tput doesn't change.
- **Tests added** to the existing `test_metric` parametrize list in `tests/test_number.py`: `999.9 V`, `999999 V`, `0.0009999 V`, `-999.9 V`, `999.9` at precision 1 (`'1 k'`), and `999.9999` at precision 4 (`'1.000 kV'`). I checked each against the original code with `compare_outputs.py`, and each one changed.
- **Docstring examples** (`1.50 kV`, `200 MW`, `220 μF`, `10.00 f`, `1.00 x 10⁴⁰`) take paths this change doesn't touch, so I left them alone.

I did not run `ruff` or `mypy`, since neither is installed in the project environment. I also haven't committed the change.
