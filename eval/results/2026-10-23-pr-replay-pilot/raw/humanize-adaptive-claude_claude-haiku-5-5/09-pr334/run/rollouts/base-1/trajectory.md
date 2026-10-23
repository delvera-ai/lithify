# trajectory base-1

final message:
`naturaldelta()` now returns `float("inf")` and `float("-inf")` unchanged as `"inf"` and `"-inf"`, and finite values that are too large still raise `OverflowError`. The full suite passes: 723 passed, 74 skipped.

**The cause:** `int(float("inf"))` raises `OverflowError`, and the existing `except (ValueError, TypeError)` didn't catch it. Widening that clause would also have swallowed the `OverflowError` from `dt.timedelta(seconds=1e30)`, which the docstring says must propagate. So I moved the `int()` probe into its own `try` block that also catches `OverflowError`. The `float()` and `timedelta` conversions now sit outside it.

**Changes:**
- `src/humanize/time.py`: the fix described above.
- `tests/test_time.py`: two new tests, `test_naturaldelta_infinite_returned_unchanged` (parametrized over `inf` and `-inf`) and `test_naturaldelta_too_large_raises` (checks that `1e30` raises). I didn't touch any existing tests.

I haven't committed. Say the word if you want a commit with the `Co-Authored-By` line.

## events
[tool_use Grep] {"pattern": "def naturaldelta", "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "grep -rn \"naturaldelta\\|OverflowError\" --include=*.py . | head -50", "description": "Locate naturaldelta and OverflowError usages"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"naturaldelta\\|OverflowError\" . --exclude-dir=.git | head -50", "description": "Locate naturaldelta and OverflowError usages"}
[tool_result] tests/test_time.py:88:def test_naturaldelta_nomonths(test_input: dt.timedelta, expected: str) -> None:
tests/test_time.py:89:    assert humanize.naturaldelta(test_input, months=False) == expected
tests/test_time.py:135:def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
tests/test_time.py:136:    assert humanize.naturaldelta(test_input) == expected
tests/test_time.py:138:        assert humanize.naturaldelta(-test_input) == expected
tests/test_time.py:343:def test_natu
…[1484 chars elided]…
elta(
src/humanize/time.py:121:        OverflowError: If `value` is too large to convert to datetime.timedelta.
src/humanize/time.py:134:        >>> assert naturaldelta(later - now) == "30 minutes"
src/humanize/time.py:294:    delta = naturaldelta(delta, months, minimum_unit)
src/humanize/time.py:337:    except (OverflowError, ValueError):
src/humanize/time.py:368:    except (OverflowError, ValueError):
src/humanize/__init__.py:30:    naturaldelta,
src/humanize/__init__.py:51:    "naturaldelta",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "offset": 95, "limit": 90}
[tool_result] 95	
96	
97	def naturaldelta(
98	    value: dt.timedelta | float,
99	    months: bool = True,
100	    minimum_unit: str = "seconds",
101	) -> str:
102	    """Return a natural representation of a timedelta or number of seconds.
103	
104	    This is similar to `naturaltime`, but does not add tense to the result.
105	
106	    The timedelta will be rounded to the nearest unit that makes sense.
107	
108	    Args:
109	        value (datetime.timedelta, int or float): A timedelta or a number of seconds.
…[2282 chars elided]…
it == Unit.MILLISECONDS or (
173	                min_unit == Unit.MICROSECONDS and 1000 <= delta.microseconds < 1_000_000
174	            ):
175	                milliseconds = delta.microseconds / 1000
176	                return (
177	                    _ngettext("%d millisecond", "%d milliseconds", int(milliseconds))
178	                    % milliseconds
179	                )
180	            return _("a moment")
181	
182	        if delta.seconds == 1:
183	            return _("a second")
184	
[tool_use Bash] {"command": "grep -n \"inf\\|nan\\|Overflow\" tests/test_time.py | head -30; ls <work>/env-humanize/bin/python 2>&1", "description": "Find existing inf/nan/overflow tests and check test interpreter"}
[tool_result] 311:    future = dt.datetime(2023, 10, 16, hour=6, tzinfo=utc)
<work>/env-humanize/bin/python
[assistant] Confirmed the cause: `int(float("inf"))` raises `OverflowError`, which the `except (ValueError, TypeError)` on line 154 doesn't catch. The `timedelta` construction on line 153 also can raise `OverflowError` for finite values like `1e30`, so I can't just widen the existing except clause. I'll move the `int()` probe into its own try block.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py", "old_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n            value = float(value)\n            delta = dt.timedelta(seconds=value)\n        except (ValueError, TypeError):\n            return str(value)", "new_string": "        try:\n            int(value)  # Explicitly don't support string such as \"NaN\" or \"inf\"\n        except (ValueError, TypeError, OverflowError):  # OverflowError: float(\"inf\")\n            return str(value)\n        value = float(value)\n        delta = dt.timedelta(seconds=value)"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/src/humanize/time.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `naturaldelta` tests. First, the file's style around the existing error test:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "offset": 120, "limit": 25}
[tool_result] 120	        # regression tests for bugs in post-release humanize
121	        (dt.timedelta(days=10000), "27 years"),
122	        (dt.timedelta(days=365 + 35), "1 year, 1 month"),
123	        (dt.timedelta(days=365 * 2 + 65), "2 years"),
124	        (dt.timedelta(days=365 + 4), "1 year, 4 days"),
125	        (dt.timedelta(days=35), "a month"),
126	        (dt.timedelta(days=65), "2 months"),
127	        (dt.timedelta(days=9), "9 days"),
128	        (dt.timedelta(days=365), "a year"),
129	        
…[100 chars elided]…
unchanged.
131	        # largest possible timedelta
132	        (dt.timedelta(days=999_999_999), "2,739,726 years"),
133	    ],
134	)
135	def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:
136	    assert humanize.naturaldelta(test_input) == expected
137	    if not isinstance(test_input, str):
138	        assert humanize.naturaldelta(-test_input) == expected
139	
140	
141	@freeze_time(FROZEN_DATE)
142	@pytest.mark.parametrize(
143	    "test_input, expected",
144	    [
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "offset": 818, "limit": 14}
[tool_result] 818	def test_precisedelta_bogus_call() -> None:
819	    assert humanize.precisedelta(None) == "None"
820	
821	    with pytest.raises(
822	        ValueError,
823	        match="Minimum unit is suppressed and no suitable replacement was found",
824	    ):
825	        humanize.precisedelta(1, minimum_unit="years", suppress=["years"])
826	
827	    with pytest.raises(ValueError, match="Minimum unit 'years' not supported"):
828	        humanize.naturaldelta(1, minimum_unit="years")
829	
830	
831	def test_time_unit() -> None:
[assistant] The existing parametrized test negates its input, so `inf` and `-inf` need a separate test. I'll add one after `test_naturaldelta`, plus the overflow guard for finite values.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py", "old_string": "def test_naturaldelta(test_input: float | dt.timedelta, expected: str) -> None:\n    assert humanize.naturaldelta(test_input) == expected\n    if not isinstance(test_input, str):\n        assert humanize.naturaldelta(-
…[245 chars elided]…
e.naturaldelta(-test_input) == expected\n\n\n@pytest.mark.parametrize(\"test_input\", [float(\"inf\"), float(\"-inf\")])\ndef test_naturaldelta_infinite_returned_unchanged(test_input: float) -> None:\n    assert humanize.naturaldelta(test_input) == str(test_input)\n\n\ndef test_naturaldelta_too_large_raises() -> None:\n    with pytest.raises(OverflowError):\n        humanize.naturaldelta(1e30)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142636-bug-humanize-naturaldelta-docume/base-1/tests/test_time.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run project test suite"}
[tool_use Bash] {"command": "git stash list >/dev/null; git diff --stat; PYTHONPATH=src <work>/env-humanize/bin/python -I -c \"\nimport sys; sys.path.insert(0,'src')\nimport humanize\nprint(humanize.naturaldelta(float('inf')), humanize.naturaldelta(float('-inf')), humanize.naturaldelta(float('nan')), humanize.naturaldelta('inf'))\ntry: humanize.naturaldelta(1e30)\nexcept OverflowError as e: print('OverflowError', e)\n\"", "description": "Run test suite and spot-check edge values"}
[tool_result] ---------------------------------------------------------------------------------------------- benchmark: 15 tests ----------------------------------------------------------------------------------------------
Name (time in ns)            Min                       Max                  Mean                 StdDev                Median                 IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
--------------------------------------------------------------------------------
…[3191 chars elided]…
9897 (37.25)    250.0019 (238.61)    12;1385      164.7045 (0.03)      26345           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
723 passed, 74 skipped in 6.36s
[tool_result]  src/humanize/time.py |  6 +++---
 tests/test_time.py   | 10 ++++++++++
 2 files changed, 13 insertions(+), 3 deletions(-)
inf -inf nan inf
OverflowError Python int too large to convert to C int
[assistant] `naturaldelta()` now returns `float("inf")` and `float("-inf")` unchanged as `"inf"` and `"-inf"`, and finite values that are too large still raise `OverflowError`. The full suite passes: 723 passed, 74 skipped.

**The cause:** `int(float("inf"))` raises `OverflowError`, and the existing `except (ValueError, TypeError)` didn't catch it. Widening that clause would also have swallowed the `OverflowError` from `dt.timedelta(seconds=1e30)`, which the docstring says must propagate. So I moved the `int()` probe into its own `try` block that also catches `OverflowError`. The `float()` and `timedelta` conversions now sit outside it.

**Changes:**
- `src/humanize/time.py`: the fix described above.
- `tests/test_time.py`: two new tests, `test_naturaldelta_infinite_returned_unchanged` (parametrized over `inf` and `-inf`) and `test_naturaldelta_too_large_raises` (checks that `1e30` raises). I didn't touch any existing tests.

I haven't committed. Say the word if you want a commit with the `Co-Authored-By` line.
