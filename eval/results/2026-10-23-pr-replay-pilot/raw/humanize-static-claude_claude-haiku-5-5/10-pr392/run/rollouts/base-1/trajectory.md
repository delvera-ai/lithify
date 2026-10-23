# trajectory base-1

final message:
Fixed: `intcomma(10**400 + 123)` now returns the fully grouped digits, and `intcomma(-(10**400 + 123))` returns the same with a leading `-`. The project check passes: `726 passed, 110 skipped` (no failures). I didn't commit.

**Cause:** `intcomma` checks `math.isfinite(float(value))` before formatting, and `float()` overflows on integers above about 1.8e308. Ints can't be NaN or infinite, so the check now runs only for non-int inputs (`src/humanize/number.py`, `elif not isinstance(value, int):`). Python then formats the int directly with `f"{value:,}"`.

**Tests:** I added two cases to the existing `test_intcomma` parametrize list in `tests/test_number.py`: the positive and negative 10**400 + 123. Both raised `OverflowError` on HEAD, so they fail on the original code. Their expected values are built with `f"{...:,}"`, so the test checks against Python's own grouping rather than a hand-written 400-digit literal.

**Compared against HEAD** with the harness script, for the sake of the other behaviour:
- Unchanged: `intcomma(10**30)`, `intcomma(None)`, `intcomma(True)`, `intcomma("1" + "0"*400)` (still `+Inf`), `intcomma(float(10**30))`.
- Unchanged with explicit `ndigits`: `intcomma(10**400 + 123, 2)` still raises `OverflowError`, as the spec required. Python's `f"{int:,.2f}"` converts to float internally, so that path needs a separate fix if you want it handled.

Lint was not run: `ruff` isn't installed in the project environment, so I read the changed lines against `[tool.ruff]` by hand.

## events
[tool_use Bash] {"command": "grep -n \"def intcomma\" -A60 src/humanize/number.py && ls .lithify/harness/scripts/ && cat <work>/env-humanize/bin/python 2>/dev/null | head -c 0; ls <work>/env-humanize/bin/python; grep -n \"intcomma\" -B2 -A3 tests/*.py | head -80"}
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
…[3962 chars elided]…
sert humanize.intcomma(number) == "10.000.000"
tests/test_i18n.py-74-
tests/test_i18n.py-75-    except FileNotFoundError:
tests/test_i18n.py-76-        pytest.skip("Generate .mo with scripts/generate-translation-binaries.sh")
--
tests/test_i18n.py-78-    finally:
tests/test_i18n.py-79-        humanize.i18n.deactivate()
tests/test_i18n.py:80:        assert humanize.intcomma(number) == "10,000,000"
tests/test_i18n.py-81-
tests/test_i18n.py-82-
tests/test_i18n.py-83-def test_naturaldelta() -> None:
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'intcomma(10**400 + 123)' 'intcomma(-(10**400 + 123))' 'intcomma(10**30)' 'intcomma(10**400 + 123, 2)' 'intcomma(float(10**30))' 'intcomma(\"1\"+\"0\"*400)' 2>&1 | tail -30; find .claude* -name \"*humanize-number-output*\" 2>/dev/null; ls ~/.claude/skills 2>/dev/null | head"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpnav6kcxy/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/src/humanize/__init__.py)
same    intcomma(10**400 + 123)
    old: !OverflowError: int too large to convert to float
    new: !OverflowError: int too large to convert to float
same    intcomma(-(10**400 + 123))
    old: !OverflowError: int too large to convert
…[97 chars elided]…
 old: '1,000,000,000,000,000,000,000,000,000,000'
    new: '1,000,000,000,000,000,000,000,000,000,000'
same    intcomma(10**400 + 123, 2)
    old: !OverflowError: int too large to convert to float
    new: !OverflowError: int too large to convert to float
same    intcomma(float(10**30))
    old: '1e+30'
    new: '1e+30'
same    intcomma("1"+"0"*400)
    old: '+Inf'
    new: '+Inf'
6 expressions, 0 changed, 6 same
.claude/skills/humanize-number-output
agent-optimize
autoproject
find-skills
synced
[tool_use Bash] {"command": "cat .claude/skills/humanize-number-output/SKILL.md; sed -n 1,30p src/humanize/number.py | grep -n \"lazy\\|import\"; sed -n 60,80p tests/test_number.py"}
[tool_result] ---
name: humanize-number-output
description: Load when a task fixes or changes the string a number/filesize formatter returns (fractional, intword, intcomma, apnumber, ordinal, scientific, clamp, metric in src/humanize/number.py, or naturalsize in filesize.py), e.g. wrong output for negative, zero, float or string inputs.
---

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sen
…[2399 chars elided]…
08.40, 3], "14,308.400"),
        ([1234.5454545], "1,234.5454545"),
        ([1234.5454545, None], "1,234.5454545"),
        ([1234.5454545, 0], "1,235"),
        ([1234.5454545, 1], "1,234.5"),
        ([1234.5454545, 2], "1,234.55"),
        ([1234.5454545, 3], "1,234.545"),
        ([1234.5454545, 10], "1,234.5454545000"),
        ([math.nan], "NaN"),
        ([math.inf], "+Inf"),
        ([-math.inf], "-Inf"),
        (["nan"], "NaN"),
        (["-inf"], "-Inf"),
    ],
)
def test_intcomma(
[assistant] Reproduced on unmodified HEAD: `intcomma(10**400 + 123)` raises `OverflowError` from the `float(value)` finiteness check, which runs before formatting. Ints can't be non-finite, so the check only needs to apply to non-int inputs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py", "old_string": "        else:\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)", "new_string": "        elif not isinstance(value, int):\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; $PY .lithify/harness/scripts/compare_outputs.py 'intcomma(10**400 + 123)' 'intcomma(-(10**400 + 123))' 'intcomma(10**30)' 'intcomma(10**400 + 123, 2)' 'intcomma(None)' 'intcomma(True)' 'intcomma(\"1\"+\"0\"*400)' 'intcomma(float(10**30))' 'intcomma(-(10**400))' 2>&1 | tail -30"}
[tool_result] old = HEAD (/private/var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/tmpgtlwnzqe/old/src/humanize/__init__.py)
new = working tree (~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/src/humanize/__init__.py)
CHANGED intcomma(10**400 + 123)
    old: !OverflowError: int too large to convert to float
    new: '10,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,00
…[1727 chars elided]…
00,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000'
9 expressions, 3 changed, 6 same
[assistant] Explicit `ndigits` still raises, as the spec requires. Now the tests: I'll add the failing cases to the existing parametrize list. Let me look at its int section.
[tool_use Bash] {"command": "sed -n 40,60p tests/test_number.py"}
[tool_result] @pytest.mark.parametrize(
    "test_args, expected",
    [
        ([100], "100"),
        ([1000], "1,000"),
        ([10123], "10,123"),
        ([10311], "10,311"),
        ([1_000_000], "1,000,000"),
        ([1_234_567.25], "1,234,567.25"),
        (["100"], "100"),
        (["1000"], "1,000"),
        (["10123"], "10,123"),
        (["10311"], "10,311"),
        (["1000000"], "1,000,000"),
        (["1234567.1234567"], "1,234,567.1234567"),
        (["1234567.1234567", 0], "1,234,567"),
        (["1234567.1234567", 1], "1,234,567.1"),
        (["1234567.1234567", 10], "1,234,567.1234567000"),
        (["1234567", 1], "1,234,567.0"),
        ([None], "None"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "old_string": "        ([1_234_567.25], \"1,234,567.25\"),\n        ([\"100\"], \"100\"),", "new_string": "        ([1_234_567.25], \"1,234,567.25\"),\n        ([10**400 + 123], f\"{10**400 + 123:,}\"),\n        ([-(10**400 + 123)], f\"{-(10**400 + 123):,}\"),\n        ([\"100\"], \"100\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-151747-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py has been updated successfully.
[assistant] Both new cases raise `OverflowError` on HEAD, so they fail on the original code as required. Running the project's full check now.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python; PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short; git diff"}
[tool_result] test_intcomma           415.9810 (3.21)      42,375.0025 (22.86)      505.6797 (3.58)       196.0925 (11.71)      500.0038 (3.59)       0.0291 (1.0)     341;58469    1,977.5363 (0.28)     147233           1
test_naturaldelta       540.9820 (4.17)     337,500.0088 (182.08)     675.9968 (4.79)     1,060.6111 (63.34)      625.0048 (4.49)      41.0073 (>1000.0) 1369;7898    1,479.2969 (0.21)     121213           1
test_naturalsize        540.9820 (4.17)     199,833.0117 (107.81)     687.1405 (4.87) 
…[2367 chars elided]…
st_number.py b/tests/test_number.py
index cf55ee1..6679e7b 100644
--- a/tests/test_number.py
+++ b/tests/test_number.py
@@ -47,6 +47,8 @@ def test_ordinal(test_input: str, expected: str) -> None:
         ([10311], "10,311"),
         ([1_000_000], "1,000,000"),
         ([1_234_567.25], "1,234,567.25"),
+        ([10**400 + 123], f"{10**400 + 123:,}"),
+        ([-(10**400 + 123)], f"{-(10**400 + 123):,}"),
         (["100"], "100"),
         (["1000"], "1,000"),
         (["10123"], "10,123"),
[assistant] Fixed: `intcomma(10**400 + 123)` now returns the fully grouped digits, and `intcomma(-(10**400 + 123))` returns the same with a leading `-`. The project check passes: `726 passed, 110 skipped` (no failures). I didn't commit.

**Cause:** `intcomma` checks `math.isfinite(float(value))` before formatting, and `float()` overflows on integers above about 1.8e308. Ints can't be NaN or infinite, so the check now runs only for non-int inputs (`src/humanize/number.py`, `elif not isinstance(value, int):`). Python then formats the int directly with `f"{value:,}"`.

**Tests:** I added two cases to the exi
…[311 chars elided]…
igit literal.

**Compared against HEAD** with the harness script, for the sake of the other behaviour:
- Unchanged: `intcomma(10**30)`, `intcomma(None)`, `intcomma(True)`, `intcomma("1" + "0"*400)` (still `+Inf`), `intcomma(float(10**30))`.
- Unchanged with explicit `ndigits`: `intcomma(10**400 + 123, 2)` still raises `OverflowError`, as the spec required. Python's `f"{int:,.2f}"` converts to float internally, so that path needs a separate fix if you want it handled.

Lint was not run: `ruff` isn't installed in the project environment, so I read the changed lines against `[tool.ruff]` by hand.
