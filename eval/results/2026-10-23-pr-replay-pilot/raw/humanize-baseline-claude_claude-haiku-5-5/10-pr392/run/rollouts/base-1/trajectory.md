# trajectory base-1

final message:
The fix is in, and the full suite passes: 726 passed, 110 skipped, with no failures.

**Cause:** `intcomma` called `float(value)` on every non-string input. For an int too large for a float, that raises `OverflowError`, which the `except (TypeError, ValueError)` block doesn't catch.

**Change** (`src/humanize/number.py`): integers skip the float check entirely, since they are formatted exactly at any size. Only non-int, non-string values still go through the `isfinite` check, so NaN/inf handling is unchanged. I also removed a trailing `float(value)` call that was redundant once the check ran.

**Tests** (`tests/test_number.py`): I added a positive and a negative case to the existing `test_intcomma` parametrization, each compared against Python's own `f"{n:,}"`. Spot checks:
- `intcomma(10**400 + 123)` gives `10,000,…,000,123` with all 401 digits kept.
- `intcomma(-(10**400) - 123)` gives the same with a leading `-`.

Numeric strings, `ndigits` handling, locale separators, and `None` are unchanged; the existing tests cover them and pass.

I haven't committed. Also, I didn't run the new cases against the unfixed code to watch them fail; the overflow path is clear from the code, but that's a step I skipped.

## events
[tool_use Bash] {"command": "grep -rn \"intcomma\" src | head -30 && cat src/humanize/i18n.py 2>/dev/null | head -5; find . -name \"*.py\" -path \"*src*\" | grep -i -E \"number|intcomma|i18n\" ", "description": "Locate intcomma implementation"}
[tool_result] src/humanize/time.py:15:from .number import intcomma
src/humanize/time.py:258:    return _ngettext("%d year", "%d years", years).replace("%d", "%s") % intcomma(years)
src/humanize/time.py:667:                texts.append(fmt_txt % intcomma(fmt_value))
src/humanize/number.py:116:def intcomma(value: NumberOrString, ndigits: int | None = None) -> str:
src/humanize/number.py:120:    compatibility with Django's `intcomma`, this function also accepts floats.
src/humanize/number.py:124:        >>> intc
…[182 chars elided]…
.25)
src/humanize/number.py:132:        >>> intcomma(1234.5454545, 2)
src/humanize/number.py:134:        >>> intcomma(14308.40, 1)
src/humanize/number.py:136:        >>> intcomma("14308.40", 1)
src/humanize/number.py:138:        >>> intcomma(None)
src/humanize/__init__.py:21:    intcomma,
src/humanize/__init__.py:45:    "intcomma",
"""Activate, get and deactivate translations."""

from __future__ import annotations

import gettext as gettext_module
./src/humanize/number.py
./src/humanize/i18n.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py", "offset": 100, "limit": 80}
[tool_result] 100	    Returns:
101	        str: Ordinal string.
102	    """
103	    import math
104	
105	    try:
106	        if not math.isfinite(float(value)):
107	            return _format_not_finite(float(value))
108	        value = int(value)
109	    except (TypeError, ValueError):
110	        return str(value)
111	    gender = "male" if gender == "male" else "female"
112	    digit = 0 if value % 100 in (11, 12, 13) else value % 10
113	    return f"{value}{P_(f'{digit} ({gender})', _ORDINAL_SUFFIXES[dig
…[1757 chars elided]…
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
[assistant] The overflow comes from line 164/166: `float(value)` runs on every non-string input, and for an int larger than float's range it raises `OverflowError`, which the `except` doesn't catch. Ints never need the finiteness check, so I'll skip it for them. Let me check the existing tests first.
[tool_use Bash] {"command": "grep -rn \"intcomma\" tests | head -40; ls <work>/env-humanize/bin/python 2>&1", "description": "Find intcomma tests and check test interpreter"}
[tool_result] tests/test_benchmarks.py:36:def test_intcomma(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:37:    benchmark(humanize.intcomma, 1_234_567_890)
tests/test_number.py:80:def test_intcomma(
tests/test_number.py:83:    assert humanize.intcomma(*test_args) == expected
tests/test_i18n.py:53:def test_intcomma() -> None:
tests/test_i18n.py:56:    assert humanize.intcomma(number) == "10,000,000"
tests/test_i18n.py:60:        assert humanize.intcomma(number) == "10.000.000"
tests/test_i18n
…[493 chars elided]…
10 000 000"
tests/test_i18n.py:69:        assert humanize.intcomma(1_234_567.89) == "1 234 567,89"
tests/test_i18n.py:70:        assert humanize.intcomma("1 234 567,89") == "1 234 567,89"
tests/test_i18n.py:73:        assert humanize.intcomma(number) == "10.000.000"
tests/test_i18n.py:80:        assert humanize.intcomma(number) == "10,000,000"
<work>/env-humanize/bin/python
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py", "old_string": "        else:\n            if not math.isfinite(float(value)):\n                return _format_not_finite(float(value))\n            float(value)\n    except (TypeError, ValueError):", "new_string": "        elif not isinstance(value, int) and not math.isfinite(float(value)):\n            # Integers are exact at any size, so only non-int values are range-checked as floats.\n            return _format_not_finite(float(value))\n    except (TypeError, ValueError):"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/src/humanize/number.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `intcomma` cases.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "offset": 55, "limit": 35}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "old_string": "        ([\"-inf\"], \"-Inf\"),\n    ],\n)\ndef test_intcomma(\n    test_args: list[int] | list[float] | list[str], expected: str\n) -> None:\n    assert humanize.intcomma(*test_args) == expected\n", "new_string": " 
…[173 chars elided]…
    test_args: list[int] | list[float] | list[str], expected: str\n) -> None:\n    assert humanize.intcomma(*test_args) == expected\n\n\ndef test_intcomma_huge_int_keeps_every_digit() -> None:\n    value = 10**400 + 123\n    result = humanize.intcomma(value)\n    assert result.replace(\",\", \"\") == str(value)\n    assert result.startswith(\"1,000,\")\n    assert result.endswith(\",000,123\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py has been updated successfully.
[assistant] The `startswith("1,000,")` assertion I just wrote is wrong: 10**400 has 401 digits, so the output starts with `10,`. The parametrized cases already compare against Python's own `:,` formatting, so I'll drop the extra test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py", "old_string": "    assert humanize.intcomma(*test_args) == expected\n\n\ndef test_intcomma_huge_int_keeps_every_digit() -> None:\n    value = 10**400 + 123\n    result = humanize.intcomma(value)\n    assert result.replace(\",\", \"\") == str(value)\n    assert result.startswith(\"1,000,\")\n    assert result.endswith(\",000,123\")\n", "new_string": "    assert humanize.intcomma(*test_args) == expected\n"}
[tool_result] The file ~/.cache/lithify/work/repo-5d1412bdc274/20261023-142722-bug-humanize-intcomma-10-400-123/base-1/tests/test_number.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; PYTHONPATH=src <work>/env-humanize/bin/python -c \"\nimport humanize\nprint(humanize.intcomma(10**400+123)); print(humanize.intcomma(-(10**400)-123)); print(humanize.intcomma(10**400+123, 2) if False else 'ok')\nprint(humanize.intcomma('1234567'), humanize.intcomma(None), humanize.intcomma(1234.5, 2))\"", "description": "Run full test suite and spot-check outputs"}
[tool_result] test_metric             457.9779 (3.13)     130,041.0077 (23.46)      563.2752 (3.43)       930.1621 (26.01)      542.0006 (3.34)       0.9895 (1.0)      265;37052    1,775.3312 (0.29)     101266           1
test_naturaldelta       582.9788 (3.98)      27,875.0085 (5.03)       674.6588 (4.11)       191.3745 (5.35)       667.0016 (4.11)       0.9895 (1.0)      116;33758    1,482.2307 (0.24)      91609           1
test_naturalday         608.3501 (4.15)       5,543.7500 (1.0)        664.7488 (4.05
…[2380 chars elided]…
0,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,123
ok
1,234,567 None 1,234.50
[assistant] The fix is in, and the full suite passes: 726 passed, 110 skipped, with no failures.

**Cause:** `intcomma` called `float(value)` on every non-string input. For an int too large for a float, that raises `OverflowError`, which the `except (TypeError, ValueError)` block doesn't catch.

**Change** (`src/humanize/number.py`): integers skip the float check entirely, since they are formatted exactly at any size. Only non-int, non-string values still go through the `isfinite` check, so NaN/inf handling is unchanged. I also removed a trailing `float(value)` call that was redundant once the check ran.

…[23 chars elided]…
_number.py`): I added a positive and a negative case to the existing `test_intcomma` parametrization, each compared against Python's own `f"{n:,}"`. Spot checks:
- `intcomma(10**400 + 123)` gives `10,000,…,000,123` with all 401 digits kept.
- `intcomma(-(10**400) - 123)` gives the same with a leading `-`.

Numeric strings, `ndigits` handling, locale separators, and `None` are unchanged; the existing tests cover them and pass.

I haven't committed. Also, I didn't run the new cases against the unfixed code to watch them fail; the overflow path is clear from the code, but that's a step I skipped.
