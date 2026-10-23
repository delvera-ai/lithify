# trajectory base-1

final message:
`humanize.intcomma(10**400 + 123)` now returns the full grouped number, `10,000,…,000,123`, instead of raising `OverflowError`. The project's test run passes: 726 passed, 110 skipped.

The cause was in `intcomma` (`src/humanize/number.py`): every non-string input went through `float(value)` as a finiteness check. `float()` overflows on very large ints, and that `OverflowError` isn't in the `except (TypeError, ValueError)` clause. Ints are always finite, so I skipped that check for them. Strings, floats, `None`, NaN/inf and explicit `ndigits` follow the same code paths as before. I also checked negative huge ints (`-10,000,…,123`).

I added two cases to the `test_intcomma` parametrization in `tests/test_number.py`, one positive and one negative huge int, with the expected strings checked against Python's own `f"{n:,}"`. I didn't touch any existing test.

I didn't commit the change.

## events
[tool_use Bash] {"command": "grep -rn \"intcomma\" src/ | head -20 && cat -n src/humanize/i18n.py 2>/dev/null | head -5", "description": "Locate intcomma implementation"}
[tool_result] src/humanize/time.py:15:from .number import intcomma
src/humanize/time.py:258:    return _ngettext("%d year", "%d years", years).replace("%d", "%s") % intcomma(years)
src/humanize/time.py:667:                texts.append(fmt_txt % intcomma(fmt_value))
src/humanize/number.py:116:def intcomma(value: NumberOrString, ndigits: int | None = None) -> str:
src/humanize/number.py:120:    compatibility with Django's `intcomma`, this function also accepts floats.
src/humanize/number.py:124:        >>> intc
…[169 chars elided]…
mma(1_234_567.25)
src/humanize/number.py:132:        >>> intcomma(1234.5454545, 2)
src/humanize/number.py:134:        >>> intcomma(14308.40, 1)
src/humanize/number.py:136:        >>> intcomma("14308.40", 1)
src/humanize/number.py:138:        >>> intcomma(None)
src/humanize/__init__.py:21:    intcomma,
src/humanize/__init__.py:45:    "intcomma",
     1	"""Activate, get and deactivate translations."""
     2	
     3	from __future__ import annotations
     4	
     5	import gettext as gettext_module
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py", "offset": 1, "limit": 180}
[tool_result] 1	"""Humanizing functions for numbers."""
2	
3	from __future__ import annotations
4	
5	__lazy_modules__ = {"bisect"}
6	
7	import bisect
8	
9	from .i18n import _gettext as _
10	from .i18n import _ngettext, decimal_separator, thousands_separator
11	from .i18n import _ngettext_noop as NS_
12	from .i18n import _pgettext as P_
13	
14	TYPE_CHECKING = False
15	if TYPE_CHECKING:
16	    from typing import TypeAlias
17	
18	    # This type can be better defined by typing.SupportsFloat
19	    # but that's a
…[4263 chars elided]…
66	            float(value)
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
180	human_powers = (
[assistant] The overflow comes from line 164: `float(value)` runs on every non-string input, and `float(10**400)` raises `OverflowError`, which the `except (TypeError, ValueError)` doesn't catch. Ints don't need that finiteness check, so I'll skip it for them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py", "old_string": "        else:\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)\n    except (TypeError, ValueError):\n        return str(value)\n\n 
…[2 chars elided]…
 if ndigits is not None:", "new_string": "        elif not isinstance(value, int):\n            # Ints are always finite, and `float()` would overflow for very large ones.\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)\n    except (TypeError, ValueError):\n        return str(value)\n\n    if ndigits is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py has been updated successfully.
[tool_use Bash] {"command": "grep -rn \"intcomma\" tests/ | head -30; PYTHONPATH=src python3 -c \"\nimport humanize\nprint(humanize.intcomma(10**400+123)); print(humanize.intcomma(-(10**400+123))); print(humanize.intcomma(10**30)); print(humanize.intcomma(None)); print(humanize.intcomma(float('nan'))); print(humanize.intcomma(1234)); print(humanize.intcomma(1234.5, 1))\"", "description": "Check intcomma fix and existing intcomma tests"}
[tool_result] tests/test_benchmarks.py:36:def test_intcomma(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:37:    benchmark(humanize.intcomma, 1_234_567_890)
tests/test_i18n.py:53:def test_intcomma() -> None:
tests/test_i18n.py:56:    assert humanize.intcomma(number) == "10,000,000"
tests/test_i18n.py:60:        assert humanize.intcomma(number) == "10.000.000"
tests/test_i18n.py:61:        assert humanize.intcomma(1_234_567.8901) == "1.234.567,8901"
tests/test_i18n.py:62:        assert humaniz
…[1474 chars elided]…
000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,123
1,000,000,000,000,000,000,000,000,000,000
None
NaN
1,234
1,234.5
[assistant] The fix works for positive and negative huge ints, and the other paths are unchanged. Next I'll add a regression test next to the existing parametrized `intcomma` cases.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "offset": 55, "limit": 35}
[tool_result] 55	        (["1234567.1234567"], "1,234,567.1234567"),
56	        (["1234567.1234567", 0], "1,234,567"),
57	        (["1234567.1234567", 1], "1,234,567.1"),
58	        (["1234567.1234567", 10], "1,234,567.1234567000"),
59	        (["1234567", 1], "1,234,567.0"),
60	        ([None], "None"),
61	        ([14308.40], "14,308.4"),
62	        ([14308.40, None], "14,308.4"),
63	        ([14308.40, 1], "14,308.4"),
64	        ([14308.40, 2], "14,308.40"),
65	        ([14308.40, 3], "14,308.400"),
66	  
…[340 chars elided]…
], "NaN"),
74	        ([math.inf], "+Inf"),
75	        ([-math.inf], "-Inf"),
76	        (["nan"], "NaN"),
77	        (["-inf"], "-Inf"),
78	    ],
79	)
80	def test_intcomma(
81	    test_args: list[int] | list[float] | list[str], expected: str
82	) -> None:
83	    assert humanize.intcomma(*test_args) == expected
84	
85	
86	def test_intword_powers() -> None:
87	    # make sure that powers & human_powers have the same number of items
88	    assert len(number.powers) == len(number.human_powers)
89	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "old_string": "        ([\"-inf\"], \"-Inf\"),\n    ],\n)\ndef test_intcomma(", "new_string": "        ([\"-inf\"], \"-Inf\"),\n        ([10**400 + 123], \"1\" + \",000\" * 133 + \",123\"),\n        ([-(10**400 + 123)], \"-1\" + \",000\" * 133 + \",123\"),\n    ],\n)\ndef test_intcomma("}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py has been updated successfully.
[assistant] I'll verify the expected string in Python rather than trust my hand count.
[tool_use Bash] {"command": "python3 -c \"\nn=10**400+123\nprint(f'{n:,}' == '10' + ',000'*132 + ',123', len(str(n)))\" && ls <work>/env-humanize/bin/python 2>&1", "description": "Verify expected grouping and check project venv exists"}
[tool_result] True 401
<work>/env-humanize/bin/python
[assistant] My hand count was wrong: the number has 401 digits, so the expected string is `"10" + ",000"*132 + ",123"`. I'll fix the test and run the project's check command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "old_string": "        ([10**400 + 123], \"1\" + \",000\" * 133 + \",123\"),\n        ([-(10**400 + 123)], \"-1\" + \",000\" * 133 + \",123\"),", "new_string": "        ([10**400 + 123], \"10\" + \",000\" * 132 + \",123\"),\n        ([-(10**400 + 123)], \"-10\" + \",000\" * 132 + \",123\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142721-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run project test suite"}
[tool_result] ------------------------------------------------------------------------------------------- benchmark: 15 tests --------------------------------------------------------------------------------------------
Name (time in ns)            Min                     Max                  Mean              StdDev                Median                IQR             Outliers  OPS (Kops/s)            Rounds  Iterations
------------------------------------------------------------------------------------------
…[3097 chars elided]…
999.9875 (38.82)    84.0228 (82.49)     353;1203      165.9000 (0.03)      25807           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
726 passed, 110 skipped in 6.24s
[assistant] `humanize.intcomma(10**400 + 123)` now returns the full grouped number, `10,000,…,000,123`, instead of raising `OverflowError`. The project's test run passes: 726 passed, 110 skipped.

The cause was in `intcomma` (`src/humanize/number.py`): every non-string input went through `float(value)` as a finiteness check. `float()` overflows on very large ints, and that `OverflowError` isn't in the `except (TypeError, ValueError)` clause. Ints are always finite, so I skipped that check for them. Strings, floats, `None`, NaN/inf and explicit `ndigits` follow the same code paths as before. I also checked negative huge ints (`-10,000,…,123`).

I added two cases to the `test_intcomma` parametrization in `tests/test_number.py`, one positive and one negative huge int, with the expected strings checked against Python's own `f"{n:,}"`. I didn't touch any existing test.

I didn't commit the change.
