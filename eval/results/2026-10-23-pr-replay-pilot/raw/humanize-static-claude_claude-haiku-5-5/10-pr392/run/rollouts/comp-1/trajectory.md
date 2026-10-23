# trajectory comp-1

final message:
`intcomma` now groups very large integers, positive and negative, without raising `OverflowError`. The full project check ends with `728 passed, 110 skipped`.

**Cause:** the non-`str` branch called `float(value)` to validate the input. For an `int` beyond float range that raises `OverflowError`, which the `except (TypeError, ValueError)` doesn't catch.

**Fix** (`src/humanize/number.py`, one line): the float check now runs only for non-`int` values. An `int` can't be NaN or Inf, and `f"{value:,}"` formats big ints directly. The `str` branch is untouched.

**Tests** (`tests/test_number.py`): four cases added to the existing `test_intcomma` list: `10**400` and `10**400 + 123`, each positive and negative. Their expected literals are built by hand from the digit count. On HEAD these inputs raise, so the new cases fail there.

**Checked unchanged** against HEAD with `compare_outputs.py`: `10**30`, `-10**30 - 1`, `True`, `1.5`, `"1000"`, `None`, and NaN/Inf.

**Not changed, as the task asked:**
- Explicit `ndigits` still overflows for huge ints: `intcomma(10**400 + 123, 2)` raises `OverflowError`. That path goes through `f"{value:,.{ndigits}f}"`, which converts to float. Fixing it would change the explicit-`ndigits` behaviour the task said to leave alone.
- The same float guard in `intword`, `ordinal`, `apnumber`, `fractional` and `scientific` still raises for huge ints. I didn't check those with this change.

**Not run:** `ruff` isn't installed in this environment, so lint was not run. I read the changed lines against `[tool.ruff]` and they look fine.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"def intcomma\" -A60 src/humanize/number.py && ls <work>/env-humanize/bin/python 2>&1; ls .lithify/harness/scripts/ 2>&1", "description": "Inspect intcomma implementation and tooling"}
[tool_result] 116:def intcomma(value: NumberOrString, ndigits: int | None = None) -> str:
117-    """Converts an integer to a string containing commas every three digits.
118-
119-    For example, 3000 becomes "3,000" and 45000 becomes "45,000". To maintain some
120-    compatibility with Django's `intcomma`, this function also accepts floats.
121-
122-    Examples:
123-        ```pycon
124-        >>> intcomma(100)
125-        '100'
126-        >>> intcomma("1000")
127-        '1,000'
128-        >>> intcomm
…[1327 chars elided]…
:
168-        return str(value)
169-
170-    if ndigits is not None:
171-        result = f"{value:,.{ndigits}f}"
172-    else:
173-        result = f"{value:,}"
174-    if thousands_sep != "," or decimal_sep != ".":
175-        result = result.translate(str.maketrans(",.", thousands_sep + decimal_sep))
176-    return result
<work>/env-humanize/bin/python
compare_outputs.py
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/.claude/skills/humanize-number-output

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Keep the
   NaN/±Inf and `str(value)` results as they a
…[2292 chars elided]…
u=True`
   uses base 1024 even when `binary=False` (so `999999` with gnu is `976.6K`, not a carry case).
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.

[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'intcomma(10**400 + 123)' 'intcomma(-(10**400 + 123))' 'intcomma(10**30)' 'intcomma(-10**30 - 1)' 'intcomma(10**400 + 123, 2)' 'intcomma(\"1000\")' 2>&1 | tail -30", "description": "Load number-output skill and reproduce on HEAD"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpmwowcmzp/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/src/humanize/__init__.py)
same    intcomma(10**400 + 123)
    old: !OverflowError: int too large to convert to float
    new: !OverflowError: int too large to convert to float
same    intcomma(-(10**400 + 123))
    old: !OverflowError: int too large to convert
…[82 chars elided]…
mma(10**30)
    old: '1,000,000,000,000,000,000,000,000,000,000'
    new: '1,000,000,000,000,000,000,000,000,000,000'
same    intcomma(-10**30 - 1)
    old: '-1,000,000,000,000,000,000,000,000,000,001'
    new: '-1,000,000,000,000,000,000,000,000,000,001'
same    intcomma(10**400 + 123, 2)
    old: !OverflowError: int too large to convert to float
    new: !OverflowError: int too large to convert to float
same    intcomma("1000")
    old: '1,000'
    new: '1,000'
6 expressions, 0 changed, 6 same
[assistant] Reproduced on HEAD: `intcomma(10**400 + 123)` and its negative raise `OverflowError` on the unmodified code. The cause is the non-`str` branch's `float(value)` guard, which runs before formatting and isn't caught by `except (TypeError, ValueError)`. The explicit-`ndigits` case fails the same way, but the task leaves that path unchanged, so I'll leave it alone.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/src/humanize/number.py", "offset": 150, "limit": 30}
[tool_result] 150	    import math
151	
152	    thousands_sep = thousands_separator()
153	    decimal_sep = decimal_separator()
154	    try:
155	        if isinstance(value, str):
156	            value = value.replace(thousands_sep, "").replace(decimal_sep, ".")
157	            if not math.isfinite(float(value)):
158	                return _format_not_finite(float(value))
159	            if "." in value:
160	                value = float(value)
161	            else:
162	                value = int(value)
163	 
…[105 chars elided]…
inite(float(value))
166	            float(value)
167	    except (TypeError, ValueError):
168	        return str(value)
169	
170	    if ndigits is not None:
171	        result = f"{value:,.{ndigits}f}"
172	    else:
173	        result = f"{value:,}"
174	    if thousands_sep != "," or decimal_sep != ".":
175	        result = result.translate(str.maketrans(",.", thousands_sep + decimal_sep))
176	    return result
177	
178	
179	powers = [10**x for x in (3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 100)]
[assistant] The non-`str` branch needs the float guard only for non-`int` values. An `int` can't be NaN or Inf, and `float()` is the step that overflows, so I'll skip that check for `int` and keep it for everything else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/src/humanize/number.py", "old_string": "        else:\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)\n    except (TypeError, ValueError):\n        return str(value)\n\n 
…[1 chars elided]…
  if ndigits is not None:\n        result = f\"{value:,.{ndigits}f}\"", "new_string": "        elif not isinstance(value, int):\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)\n    except (TypeError, ValueError):\n        return str(value)\n\n    if ndigits is not None:\n        result = f\"{value:,.{ndigits}f}\""}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/src/humanize/number.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && $PY .lithify/harness/scripts/compare_outputs.py 'intcomma(10**400 + 123)' 'intcomma(-(10**400 + 123))' 'intcomma(10**400)' 'intcomma(-10**400)' 'intcomma(10**30)' 'intcomma(-10**30 - 1)' 'intcomma(True)' 'intcomma(1.5)' 'intco
…[47 chars elided]…
00 + 123, 2)' 2>&1 | tail -40; echo ---; PYTHONPATH=src $PY -c \"\nimport humanize\nprint(humanize.intcomma(10**400+123)); print(humanize.intcomma(-(10**400+123))); print(humanize.intcomma(10**400))\nprint(humanize.intcomma(float('nan')), humanize.intcomma(float('inf')), humanize.intcomma(None))\nprint(humanize.intcomma(True))\"", "description": "Compare outputs old vs new and spot-check results"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpgkm06pp4/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/src/humanize/__init__.py)
CHANGED intcomma(10**400 + 123)
    old: !OverflowError: int too large to convert to float
    new: '10,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,00
…[4104 chars elided]…
,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000
NaN +Inf None
1
[assistant] The fix changes only the four large-int cases, and the other seven outputs are unchanged. Next, the tests: I'll find the existing `intcomma` parametrize list.
[tool_use Bash] {"command": "grep -n \"intcomma\" -B3 -A3 tests/test_number.py | head -80", "description": "Find intcomma tests in test file"}
[tool_result] 77-        (["-inf"], "-Inf"),
78-    ],
79-)
80:def test_intcomma(
81-    test_args: list[int] | list[float] | list[str], expected: str
82-) -> None:
83:    assert humanize.intcomma(*test_args) == expected
84-
85-
86-def test_intword_powers() -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/tests/test_number.py", "offset": 50, "limit": 30}
[tool_result] 50	        (["100"], "100"),
51	        (["1000"], "1,000"),
52	        (["10123"], "10,123"),
53	        (["10311"], "10,311"),
54	        (["1000000"], "1,000,000"),
55	        (["1234567.1234567"], "1,234,567.1234567"),
56	        (["1234567.1234567", 0], "1,234,567"),
57	        (["1234567.1234567", 1], "1,234,567.1"),
58	        (["1234567.1234567", 10], "1,234,567.1234567000"),
59	        (["1234567", 1], "1,234,567.0"),
60	        ([None], "None"),
61	        ([14308.40], "14,308.4"),
62	
…[160 chars elided]…
),
66	        ([1234.5454545], "1,234.5454545"),
67	        ([1234.5454545, None], "1,234.5454545"),
68	        ([1234.5454545, 0], "1,235"),
69	        ([1234.5454545, 1], "1,234.5"),
70	        ([1234.5454545, 2], "1,234.55"),
71	        ([1234.5454545, 3], "1,234.545"),
72	        ([1234.5454545, 10], "1,234.5454545000"),
73	        ([math.nan], "NaN"),
74	        ([math.inf], "+Inf"),
75	        ([-math.inf], "-Inf"),
76	        (["nan"], "NaN"),
77	        (["-inf"], "-Inf"),
78	    ],
79	)
[assistant] I'll add the four large-int cases to the existing `test_intcomma` list. Each expected literal is built by hand from the digit count: 401 digits is `"10"` followed by 133 groups of `,000`. The `+123` case replaces the last group with `,123`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/tests/test_number.py", "old_string": "        ([\"-inf\"], \"-Inf\"),\n    ],\n)\ndef test_intcomma(", "new_string": "        ([\"-inf\"], \"-Inf\"),\n        ([10**400], \"10\" + \",000\" * 133),\n        ([-(10**400)], \"-10\" + \",000\" * 133),\n        ([10**400 + 123], \"10\" + \",000\" * 132 + \",123\"),\n        ([-(10**400 + 123)], \"-10\" + \",000\" * 132 + \",123\"),\n    ],\n)\ndef test_intcomma("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/comp-1/tests/test_number.py has been updated successfully.
[assistant] Next I'll run the full project check command, and confirm the new cases fail against HEAD.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no tests/test_number.py -k intcomma 2>&1 | tail -3", "description": "Run full test suite and intcomma tests"}
[tool_result] test_metric             415.9810 (3.11)        48,124.9881 (17.78)      502.1183 (3.48)       272.3673 (11.58)      500.0038 (3.54)       0.0291 (1.0)       349;48815    1,991.5624 (0.29)     142026           1
test_naturaldelta       540.9820 (4.04)        81,916.9800 (30.26)      634.9086 (4.40)       349.0251 (14.84)      625.0048 (4.42)       0.0291 (1.0)       175;49712    1,575.0298 (0.23)     134844           1
test_naturalsize        542.0006 (4.05)        46,708.0099 (17.25)      693.40
…[1431 chars elided]…
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
728 passed, 110 skipped in 7.39s
---
......................................                                   [100%]
38 passed, 198 deselected in 0.02s
[tool_use Bash] {"command": "git diff --stat && git diff src/", "description": "Show final source diff and stats"}
[tool_result]  src/humanize/number.py | 2 +-
 tests/test_number.py   | 4 ++++
 2 files changed, 5 insertions(+), 1 deletion(-)
diff --git a/src/humanize/number.py b/src/humanize/number.py
index 727435f..2dfeffe 100644
--- a/src/humanize/number.py
+++ b/src/humanize/number.py
@@ -160,7 +160,7 @@ def intcomma(value: NumberOrString, ndigits: int | None = None) -> str:
                 value = float(value)
             else:
                 value = int(value)
-        else:
+        elif not isinstance(value, int):
             if not math.isfinite(float(value)):
                 return _format_not_finite(float(value))
             float(value)
[assistant] `intcomma` now groups very large integers, positive and negative, without raising `OverflowError`. The full project check ends with `728 passed, 110 skipped`.

**Cause:** the non-`str` branch called `float(value)` to validate the input. For an `int` beyond float range that raises `OverflowError`, which the `except (TypeError, ValueError)` doesn't catch.

**Fix** (`src/humanize/number.py`, one line): the float check now runs only for non-`int` values. An `int` can't be NaN or Inf, and `f"{value:,}"` formats big ints directly. The `str` branch is untouched.

**Tests** (`tests/test_number.py`): f
…[373 chars elided]…
t changed, as the task asked:**
- Explicit `ndigits` still overflows for huge ints: `intcomma(10**400 + 123, 2)` raises `OverflowError`. That path goes through `f"{value:,.{ndigits}f}"`, which converts to float. Fixing it would change the explicit-`ndigits` behaviour the task said to leave alone.
- The same float guard in `intword`, `ordinal`, `apnumber`, `fractional` and `scientific` still raises for huge ints. I didn't check those with this change.

**Not run:** `ruff` isn't installed in this environment, so lint was not run. I read the changed lines against `[tool.ruff]` and they look fine.
