# trajectory comp-1

final message:
Fixed: `fractional()` now gives `-1.3` → `"-1 3/10"` and `-2.5` → `"-2 1/2"`. The full suite passes: 704 passed, 69 skipped.

**The cause:** in the mixed-number return, `whole_number` already carries the sign, and so does `numerator` (since `Fraction(-0.3)` is negative). The format string printed both. The fix is `abs(numerator)` in that one return, in `src/humanize/number.py`.

**Tests:** I added three cases to the existing `test_fractional` list in `tests/test_number.py`: `-1.3`, `-2.5`, and `"-1.5"`. I checked each against the original `HEAD` source, and each one fails there (`'-1 -3/10'`, `'-2 -1/2'`, `'-1 -1/2'`). I didn't add `-0.3`, `-1`, or `-3`, because they already return the right output and the project rules say to leave those out. The `Examples:` docstring doesn't show a negative case, so I didn't change it.

**Checks:** I ran each negative branch of `fractional()` and each has exactly one leading `-`. I ran the project's check command without the `-I` flag I had tried first, which broke imports.

**Not changed, but worth a look:** `fractional(1.9999)` probably returns `"1 1/1"`. The fraction rounds up to `1/1` inside `limit_denominator`, and the code never normalises it. I saw this on the negative side (`-1.9999` → `"-1 -1/1"`, now `"-1 1/1"`) and haven't checked the positive case directly. It's outside this bug, so I left it alone. I haven't committed the change.

## events
[assistant] I'll load the project's number-output skill first, since this changes what `fractional` returns.
[tool_use Skill] {"skill": "humanize-number-output"}
[tool_result] Launching skill: humanize-number-output
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/.claude/skills/humanize-number-output

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

[tool_use Bash] {"command": "git status --short && grep -n \"def fractional\" -A 80 src/humanize/number.py", "description": "Check worktree status and show fractional() source"}
[tool_result] 309:def fractional(value: NumberOrString) -> str:
310-    """Convert to fractional number.
311-
312-    There will be some cases where one might not want to show ugly decimal places for
313-    floats and decimals.
314-
315-    This function returns a human-readable fractional number in form of fractions and
316-    mixed fractions.
317-
318-    Pass in a string, or a number or a float, and this function returns:
319-
320-    * a string representation of a fraction
321-    * or a whole number
32
…[1530 chars elided]…
sion: int = 2) -> str:
374-    """Return number in string scientific notation z.wq x 10ⁿ.
375-
376-    Examples:
377-        ```pycon
378-        >>> scientific(float(0.3))
379-        '3.00 x 10⁻¹'
380-        >>> scientific(int(500))
381-        '5.00 x 10²'
382-        >>> scientific(-1000)
383-        '-1.00 x 10³'
384-        >>> scientific(1000, 1)
385-        '1.0 x 10³'
386-        >>> scientific(1000, 3)
387-        '1.000 x 10³'
388-        >>> scientific("99")
389-        '9.90 x 10¹'
[assistant] The skill's checklist is loaded. Next I'll reproduce the bug on the unmodified code, then look at the existing tests.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; ls -la $PY 2>&1; PYTHONPATH=src $PY -c \"\nfrom humanize import fractional\nfor v in [-1.3,-2.5,-0.3,-1,-0.5,1.3,-3,'-1.3',-1.0000001,-1.9999]:\n    print(repr(v), '->', repr(fractional(v)))\n\" 2>&1; grep -n \"fractional\" -B2 -A40 tests/test_number.py | head -120", "description": "Reproduce fractional bug and read related tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:32 <work>/env-humanize/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
-1.3 -> '-1 -3/10'
-2.5 -> '-2 -1/2'
-0.3 -> '-3/10'
-1 -> '-1'
-0.5 -> '-1/2'
1.3 -> '1 3/10'
-3 -> '-3'
'-1.3' -> '-1 -3/10'
-1.0000001 -> '-1'
-1.9999 -> '-1 -1/1'
186-    ],
187-)
188:def test_fractional(tes
…[847 chars elided]…
-        ([math.inf], "+Inf"),
214-        ([-math.inf], "-Inf"),
215-        (["nan"], "NaN"),
216-        (["-inf"], "-Inf"),
217-    ],
218-)
219-def test_scientific(test_args: list[typing.Any], expected: str) -> None:
220-    assert humanize.scientific(*test_args) == expected
221-
222-
223-@pytest.mark.parametrize(
224-    "test_args, expected",
225-    [
226-        ([1], "1"),
227-        ([None], None),
228-        ([0.0001, "{:.0%}"], "0%"),
229-        ([0.0001, "{:.0%}", 0.01], "<1%"),
[assistant] Reproduced: `fractional(-1.3)` returns `'-1 -3/10'` and `fractional(-2.5)` returns `'-2 -1/2'`, matching the report. Next I'll read the existing `test_fractional` cases so the new ones match their format.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/tests/test_number.py", "offset": 160, "limit": 30}
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
[assistant] The bug is in the mixed-number return: `whole_number` already carries the sign, and `numerator` carries it too (from `Fraction(-0.3)`), so the minus appears twice. The fix is to use the absolute value of the numerator in that branch only. The `-3/10` branch (whole part is zero) still gets its sign from the numerator, and the whole-number branch is unaffected.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/src/humanize/number.py", "old_string": "    return f\"{whole_number:.0f} {numerator:.0f}/{denominator:.0f}\"\n\n\ndef scientific(", "new_string": "    return f\"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}\"\n\n\ndef scientific("}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/src/humanize/number.py has been updated successfully.
[assistant] Next I'll add test cases to the existing `test_fractional` list. I'm including only inputs whose output changes: `-1.3`, `-2.5`, and `-1.5` each fail on the original code. `-0.3`, `-1`, and `-3` already return correct output, so the skill says to leave them out.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/tests/test_number.py", "old_string": "        (0.333, \"333/1000\"),\n        (math.nan, \"NaN\"),", "new_string": "        (0.333, \"333/1000\"),\n        (-1.3, \"-1 3/10\"),\n        (-2.5, \"-2 1/2\"),\n        (\"-1.5\", \"-1 1/2\"),\n        (math.nan, \"NaN\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-143921-bug-humanize-fractional-1-3-retu/comp-1/tests/test_number.py has been updated successfully.
[assistant] Now I'll run every branch with negative inputs to check for a single leading `-`, then run the project's full check command.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -c \"\nfrom humanize import fractional\nfor v in [-1.3,-2.5,-1.5,-0.3,-0.5,-1,-3,-1.0,'-1.3',1.3,0.3,1.5,2.0]:\n    print(repr(v), '->', repr(fractional(v)))\n\"; PYTHONPATH=src $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Check negative branch outputs and run full test suite"}
[tool_result] -1.3 -> '-1 3/10'
-2.5 -> '-2 1/2'
-1.5 -> '-1 1/2'
-0.3 -> '-3/10'
-0.5 -> '-1/2'
-1 -> '-1'
-3 -> '-3'
-1.0 -> '-1'
'-1.3' -> '-1 3/10'
1.3 -> '1 3/10'
0.3 -> '3/10'
1.5 -> '1 1/2'
2.0 -> '2'
ERROR tests/test_lists.py
ERROR tests/test_number.py
ERROR tests/test_time.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
6 errors in 0.10s
[assistant] The outputs are right, but the pytest run failed at collection because I added `-I` to it. `-I` also ignores `PYTHONPATH`, so `src` wasn't importable. The project's check command doesn't use `-I`, so I'll rerun it exactly as the project's CLAUDE.md specifies.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run full project test suite"}
[tool_result] Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
704 passed, 69 skipped in 6.13s
[assistant] The full suite passes: 704 passed, 69 skipped. The project's rule is that each new case must fail on the original code, and I only reproduced the original output for `-1.3` and `-2.5`. I'll check `-1.5` against the original `HEAD` source too, without touching the working tree.
[tool_use Bash] {"command": "D=$(mktemp -d) && mkdir -p $D/humanize && git show HEAD:src/humanize/number.py > $D/humanize/number.py && for f in __init__ i18n; do git show HEAD:src/humanize/$f.py > $D/humanize/$f.py; done && git show HEAD:src/humanize/__init__.py > $D/humanize/__init__.py && PYTHONPATH=$D <work>/env-humanize/bin/python -c \"\nfrom humanize import fractional\nfor v in [-1.3,-2.5,'-1.5']: print(repr(v), '->', repr(fractional(v)))\n\" 2>&1 | tail -4; rm -rf $D; git status --short; git diff --stat", "description": "Confirm new cases fail on original HEAD code"}
[tool_result]   File "<string>", line 2, in <module>
  File "/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp.E5K6PyIvDD/humanize/__init__.py", line 5, in <module>
    from humanize.filesize import naturalsize
ModuleNotFoundError: No module named 'humanize.filesize'
 M src/humanize/number.py
 M tests/test_number.py
 src/humanize/number.py | 2 +-
 tests/test_number.py   | 3 +++
 2 files changed, 4 insertions(+), 1 deletion(-)
[assistant] The temp copy was missing modules that the package imports. I'll extract the whole `src/` tree from `HEAD` instead.
[tool_use Bash] {"command": "D=$(mktemp -d) && git archive HEAD src | tar -x -C $D && PYTHONPATH=$D/src <work>/env-humanize/bin/python -c \"\nimport humanize; print(humanize.__file__)\nfrom humanize import fractional\nfor v in [-1.3,-2.5,'-1.5']: print(repr(v), '->', repr(fractional(v)))\n\"; rm -rf $D", "description": "Run original HEAD fractional() on the three new inputs"}
[tool_result] /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmp.GqBHykPXOA/src/humanize/__init__.py
-1.3 -> '-1 -3/10'
-2.5 -> '-2 -1/2'
'-1.5' -> '-1 -1/2'
[assistant] Fixed: `fractional()` now gives `-1.3` → `"-1 3/10"` and `-2.5` → `"-2 1/2"`. The full suite passes: 704 passed, 69 skipped.

**The cause:** in the mixed-number return, `whole_number` already carries the sign, and so does `numerator` (since `Fraction(-0.3)` is negative). The format string printed both. The fix is `abs(numerator)` in that one return, in `src/humanize/number.py`.

**Tests:** I added three cases to the existing `test_fractional` list in `tests/test_number.py`: `-1.3`, `-2.5`, and `"-1.5"`. I checked each against the original `HEAD` source, and each one fails there (`'-1 -3/10'`, 
…[200 chars elided]…
ive case, so I didn't change it.

**Checks:** I ran each negative branch of `fractional()` and each has exactly one leading `-`. I ran the project's check command without the `-I` flag I had tried first, which broke imports.

**Not changed, but worth a look:** `fractional(1.9999)` probably returns `"1 1/1"`. The fraction rounds up to `1/1` inside `limit_denominator`, and the code never normalises it. I saw this on the negative side (`-1.9999` → `"-1 -1/1"`, now `"-1 1/1"`) and haven't checked the positive case directly. It's outside this bug, so I left it alone. I haven't committed the change.
