# trajectory base-1

final message:
`metric()` now moves to the next SI prefix when rounding reaches 1000. All three reported cases are fixed, and the full suite passes (`708 passed, 69 skipped`).

```
>>> metric(999.9, "V")
'1.00 kV'
>>> metric(999999, "V")
'1.00 MV'
>>> metric(0.0009999, "V")
'1.00 mV'
```

**The fix** (`src/humanize/number.py`): after the value is scaled, if its rounded mantissa reaches 1000 and a larger prefix exists, the exponent goes up by one before formatting. Negative values work the same way (`-999.9 V` → `-1.00 kV`). The NaN/Inf guard is untouched because the change sits after it.

**Tests** (`tests/test_number.py`): I added four cases to the existing `test_metric` list: `999.9 V`, `-999.9 V`, `999999 V`, and `0.0009999 V`. Each one fails on the original code, which I reproduced before editing.

**Checks beyond the test suite:**
- I compared old and new output over about 38,000 inputs across several precisions and both signs. The 660 changed outputs are all carry cases, where the old mantissa was at least 1000.
- The largest-prefix case is unchanged: `metric(9.999e32, "V")` still gives `'1000 QV'`. I left it out of the tests because it already behaved correctly, per the CLAUDE.md rule.
- The docstring examples don't change, so I didn't edit them.

**Not verified:** `ruff` isn't installed in this environment, so I didn't run the lint or format check. The new source line is under 100 characters.

## events
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths
…[890 chars elided]…
t negated (`*-1` for ints, `"-"` prefixed for strings and floats). Only positive
   inputs belong there.
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[tool_use Bash] {"command": "grep -n \"def metric\" -A 80 src/humanize/number.py", "description": "Show metric function in number.py"}
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
…[950 chars elided]…
 value /= 10 ** (exponent // 3 * 3)
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
[assistant] The skill's checklist is practical and matches the task, so I'll follow it. First I need to reproduce the bug on the unmodified code, as the project CLAUDE.md requires.
[tool_use Bash] {"command": "PYTHONPATH=src python3 -I -c \"\nfrom humanize import metric\nfor a in [(999.9,'V'),(999999,'V'),(0.0009999,'V'),(999.9999,'V'),(-999.9,'V'),(1e30,'V'),(999.9e30,'V')]:\n    print(a, repr(metric(*a)))\n\"; ls <work>/env-humanize/bin/python 2>&1", "description": "Reproduce metric bug on unmodified code"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'humanize'
<work>/env-humanize/bin/python
[assistant] The `-I` flag also ignores `PYTHONPATH`, so I'll rerun with the project's venv interpreter.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nfrom humanize import metric\nfor a in [(999.9,'V'),(999999,'V'),(0.0009999,'V'),(999.9999,'V'),(-999.9,'V'),(999.9e30,'V'),(999.9e-30,'V'),(1e30,'V')]:\n    print(a, repr(metric(*a)))\n\"", "description": "Reproduce metric bug with project venv"}
[tool_result] (999.9, 'V') '1000 V'
(999999, 'V') '1000 kV'
(0.0009999, 'V') '1000 μV'
(999.9999, 'V') '1000 V'
(-999.9, 'V') '-1000 V'
(9.999e+32, 'V') '1000 QV'
(9.999e-28, 'V') '1000 qV'
(1e+30, 'V') '1.00 QV'
[assistant] Reproduced on the unmodified code: `999.9 V`→`1000 V`, `999999 V`→`1000 kV`, and `0.0009999 V`→`1000 μV`, as reported. The negative input also gives `-1000 V`. Now I'll look at the existing metric tests.
[tool_use Bash] {"command": "grep -n \"metric\" -B 3 -A 60 tests/test_number.py | head -150", "description": "Show metric tests in test_number.py"}
[tool_result] 308-    ],
309-    ids=str,
310-)
311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
312:    assert humanize.metric(*test_args) == expected
[tool_use Bash] {"command": "sed -n 255,312p tests/test_number.py", "description": "Read metric parametrize list"}
[tool_result]         ([12.3456], "12.3"),
        ([123.456], "123"),
        ([1234.56], "1.23 k"),
        ([12345, "", 6], "12.3450 k"),
        ([200_000], "200 k"),
        ([1e25, "m"], "10.0 Ym"),
        ([1e26, "m"], "100 Ym"),
        ([1e27, "A"], "1.00 RA"),
        ([1.234e28, "A"], "12.3 RA"),
        ([1.234e-28, "A"], "123 qA"),
        ([1.235e29, "A"], "124 RA"),
        ([2.56e-30, "V"], "2.56 qV"),
        ([2.596e32, "F"], "260 QF"),
        ([1e50], "1.00 x 10⁵⁰"),
        ([1e-50], "1.
…[814 chars elided]…
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
[assistant] The existing list already pins negative inputs, so I'll add the three reported cases and one negative case there. Next, the fix: after scaling, if the value rounds to 1000 and a larger prefix exists, move up one exponent before formatting.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py", "old_string": "    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:", "new_string": "    scaled = abs(value) / 10 ** (exponent // 3 * 3)\n    if exponent < 32 and float(format(scaled, f\".{max(0, precision - exponent % 3 - 1)}f\")) >= 1000:\n        # Rounding carried into the next prefix, e.g. 999.9 V -> 1.00 kV\n        exponent += 1\n    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py has been updated successfully.
[assistant] Now I'll add the regression cases to the existing list.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1/tests/test_number.py", "old_string": "        ([1e-26], \"10.0 r\"),\n", "new_string": "        ([1e-26], \"10.0 r\"),\n        ([999.9, \"V\"], \"1.00 kV\"),\n        ([-999.9, \"V\"], \"-1.00 kV\"),\n        ([999999, \"V\"], \"1.00 MV\"),\n        ([0.0009999, \"V\"], \"1.00 mV\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1/tests/test_number.py has been updated successfully.
[assistant] Next I'll run the project's full check command, as the CLAUDE.md requires.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] test_intcomma           415.9810 (3.23)      51,875.0167 (22.95)      534.6415 (3.83)       242.7527 (10.29)      541.0111 (3.94)      41.9968 (>1000.0)  176;7191    1,870.4122 (0.26)     164366           1
test_metric             500.0038 (3.89)      64,624.9973 (28.59)      629.6973 (4.51)       325.2996 (13.78)      625.0048 (4.55)      41.0073 (>1000.0)  242;3676    1,588.0647 (0.22)      90564           1
test_naturaldelta       540.9820 (4.20)      43,292.0060 (19.15)      627.4444 (4.49) 
…[1271 chars elided]…
09.0036 (37.95)    125.0301 (>1000.0)  402;1947      188.8186 (0.03)      24465           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
708 passed, 69 skipped in 7.05s
[assistant] The suite passes: `708 passed, 69 skipped`. Next I'll check that the fix changes only the carry cases by sweeping old and new output over many inputs.
[tool_use Bash] {"command": "rm -rf /tmp/metric-old && mkdir -p /tmp/metric-old && cp -r src/humanize /tmp/metric-old/ && git show HEAD:src/humanize/number.py > /tmp/metric-old/humanize/number.py && cat > /tmp/metric-sweep.py <<'EOF'\nimport importlib.util, sys\ndef load(path, name):\n    spec = importlib.util.spec_from_file_location(name, path + \"/humanize/__init__.py\", submodule_search_locations=[path + \"/hu
…[956 chars elided]…
ic(9.999e32,\"V\"))\nfor x in (999.9, 999999, 0.0009999, -999.9, 999.9999, 0.9999, 1e30, 999.9e30):\n    print(x, new.metric(x, \"V\"))\nEOF\nPYTHONPATH=src <work>/env-humanize/bin/python /tmp/metric-sweep.py", "description": "Compare old and new metric outputs over a sweep"}
[tool_result] changed: 0
largest-prefix unchanged: True 1000 QV
999.9 1.00 kV
999999 1.00 MV
0.0009999 1.00 mV
-999.9 -1.00 kV
999.9999 1.00 kV
0.9999 1.00 V
1e+30 1.00 QV
9.999e+32 1000 QV
[assistant] The sweep reported zero changes, which can't be right because the old run should produce `1000 V`. The two module loads likely share `sys.modules` entries, so I'll run each version in its own process and diff the outputs.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && cat > /tmp/metric-dump.py <<'EOF'\nimport math\nfrom humanize import metric\nvals = [10.0**(e/7) * s for e in range(-300, 300) for s in (1, 1.5, 2.5, 9.9, 9.9999, 9.9996, 9.99949, 9.99951)]\nvals += [999.9, 999.95, 999.949, 0.
…[214 chars elided]…
H=/tmp/metric-old $PY /tmp/metric-dump.py > /tmp/old.txt && PYTHONPATH=src $PY /tmp/metric-dump.py > /tmp/new.txt && wc -l /tmp/old.txt /tmp/new.txt && diff /tmp/old.txt /tmp/new.txt | grep '^>' | wc -l && diff /tmp/old.txt /tmp/new.txt | head -20 && PYTHONPATH=/tmp/metric-old $PY -c \"import humanize.number as n; print(n.__file__)\"", "description": "Diff metric outputs before and after the fix"}
[tool_result]    38488 /tmp/old.txt
   38488 /tmp/new.txt
   76976 total
     660
6689,6707c6689,6707
< '1000 qV'
< '1000 qV'
< '1000 qV'
< '1000.0 qV'
< '-1000 qV'
< '-1000 qV'
< '-1000 qV'
< '-1000.0 qV'
< '1000 qV'
< '1000 qV'
< '1000 qV'
< '1000.0 qV'
< '-1000 qV'
< '-1000 qV'
< '-1000 qV'
< '-1000.0 qV'
< '1000 qV'
< '1000 qV'
< '1000 qV'
/tmp/metric-old/humanize/number.py
[assistant] Of 38,488 outputs, 660 changed. I'll confirm every changed pair is a carry case, where the old mantissa was at least 1000 and the new one is below it.
[tool_use Bash] {"command": "cd /tmp && PY=<work>/env-humanize/bin/python && $PY -c \"\nimport ast\no=[ast.literal_eval(l) for l in open('/tmp/old.txt')]\nn=[ast.literal_eval(l) for l in open('/tmp/new.txt')]\nbad=[]; qs=0\nfor a,b in zip(o,n):\n    if a!=b:\n        ma=float(a.split()[0]); 
…[251 chars elided]…
d[:5])\nprint('changed pairs at Q prefix:', qs)\nprint('any new output with mantissa >=1000 and prefix present:', sum(1 for b in n if float(b.split()[0])>=1000 and len(b.split())>1 and b.split()[-1][0] in 'kMGTPEZYRQm\u03bcnpfazyrq'))\n\"; rm -rf /tmp/metric-old /tmp/metric-sweep.py /tmp/metric-dump.py /tmp/old.txt /tmp/new.txt", "description": "Verify all changed outputs match the carry pattern"}
[tool_result] changed pairs not matching carry pattern: 50 [('1000 V', '1 kV'), ('1000 V', '1.0 kV'), ('1000 V', '1.00 kV'), ('1000.0 V', '1.000 kV'), ('-1000 V', '-1 kV')]
changed pairs at Q prefix: 30
any new output with mantissa >=1000 and prefix present: 18
Shell cwd was reset to ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/base-1
[assistant] My check had a bug: `split()[-1][:-1]` is empty for `1000 V`, so those 50 entries are false alarms of the check, not real mismatches. I'll fix the check and inspect the remaining cases directly.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && PYTHONPATH=src $PY -c \"\nfrom humanize import metric\nimport math\n# outputs still showing a 4-digit mantissa with a prefix, across the sweep\nvals=[10.0**(e/7)*s for e in range(-300,300) for s in (1,1.5,2.5,9.9,9.9999,9.9996
…[92 chars elided]…
29]\nseen=set()\nfor v in vals:\n  for p in (1,2,3,4):\n    s=metric(v,'V',p)\n    m=s.split()[0]\n    if float(m)>=1000 and len(s.split())>1: seen.add(s)\nprint(sorted(seen))\n\" && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no tests/test_number.py -k metric 2>&1 | tail -2 && git status --short && git diff", "description": "Check remaining 4-digit prefixed outputs and show diff"}
[tool_result] ['1000 QV', '1000.0 QV']
...............................................................          [100%]
63 passed, 163 deselected in 0.02s
 M src/humanize/number.py
 M tests/test_number.py
diff --git a/src/humanize/number.py b/src/humanize/number.py
index 1cbfc2b..eb62239 100644
--- a/src/humanize/number.py
+++ b/src/humanize/number.py
@@ -543,6 +543,10 @@ def metric(value: float, unit: str = "", precision: int = 3) -> str:
     if exponent >= 33 or exponent < -30:
         return scientific(va
…[452 chars elided]…

index d8f9100..cb94323 100644
--- a/tests/test_number.py
+++ b/tests/test_number.py
@@ -276,6 +276,10 @@ def test_clamp(test_args: list[typing.Any], expected: str) -> None:
         ([1e-24], "1.00 y"),
         ([1e-25], "100 r"),
         ([1e-26], "10.0 r"),
+        ([999.9, "V"], "1.00 kV"),
+        ([-999.9, "V"], "-1.00 kV"),
+        ([999999, "V"], "1.00 MV"),
+        ([0.0009999, "V"], "1.00 mV"),
         ([1, "°"], "1.00°"),
         ([0.1, "°"], "100m°"),
         ([100], "100"),
[assistant] The only 4-digit output left is `1000 QV` at the largest prefix, which the spec says should stay as is. Last, a lint check on the changed line, since it's long.
[tool_use Bash] {"command": "(ruff --version && ruff check src/humanize/number.py tests/test_number.py && ruff format --check src/humanize/number.py tests/test_number.py) 2>&1 | tail -5; grep -n \"line-length\" pyproject.toml ruff.toml 2>/dev/null", "description": "Lint and format-check the changed files"}
[tool_result ERROR] Exit code 2
(eval):1: command not found: ruff
[tool_use Bash] {"command": "grep -rn \"line-length\\|line_length\\|max-line\" pyproject.toml tox.ini setup.cfg .pre-commit-config.yaml 2>/dev/null; awk 'length > 100 {print FILENAME\": \"FNR\": \"length}' src/humanize/number.py | head", "description": "Check configured line length and long lines"}
[tool_result] (Bash completed with no output)
[assistant] `metric()` now moves to the next SI prefix when rounding reaches 1000. All three reported cases are fixed, and the full suite passes (`708 passed, 69 skipped`).

```
>>> metric(999.9, "V")
'1.00 kV'
>>> metric(999999, "V")
'1.00 MV'
>>> metric(0.0009999, "V")
'1.00 mV'
```

**The fix** (`src/humanize/number.py`): after the value is scaled, if its rounded mantissa reaches 1000 and a larger prefix exists, the exponent goes up by one before formatting. Negative values work the same way (`-999.9 V` → `-1.00 kV`). The NaN/Inf guard is untouched because the change sits after it.

**Tests** (`tests/t
…[208 chars elided]…
beyond the test suite:**
- I compared old and new output over about 38,000 inputs across several precisions and both signs. The 660 changed outputs are all carry cases, where the old mantissa was at least 1000.
- The largest-prefix case is unchanged: `metric(9.999e32, "V")` still gives `'1000 QV'`. I left it out of the tests because it already behaved correctly, per the CLAUDE.md rule.
- The docstring examples don't change, so I didn't edit them.

**Not verified:** `ruff` isn't installed in this environment, so I didn't run the lint or format check. The new source line is under 100 characters.
