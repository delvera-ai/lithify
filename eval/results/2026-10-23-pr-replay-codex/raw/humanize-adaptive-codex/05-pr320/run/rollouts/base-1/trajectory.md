# trajectory base-1

final message:
Fixed negative mixed numbers to use a single minus sign: `fractional(-1.3)` now returns `"-1 3/10"`.

Added regression tests for negative mixed numbers, numeric strings, proper fractions, and integers.

Validation: 707 passed, 69 skipped.

## events
[assistant] I’ll check how `fractional` handles signs, add regression coverage, and run the project checks.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```

[command exit=0] /bin/zsh -lc "pwd; rg --files -g AGENTS.md -g '*fraction*' -g '*number*' -g 'pyproject.toml' -g 'test*'"
~/.cache/lithify/work/repo-f19ff99309c1/20261023-205047-bug-humanize-fractional-1-3-retu/base-1
src/humanize/number.py
AGENTS.md
pyproject.toml
tests/test_number.py
tests/test_lists.py
tests/test_i18n.py
tests/test_benchmarks.py
tests/test_time.py
tests/test_filesize.py
docs/number.md

[command exit=0] /bin/zsh -lc "rtk rg -n -A 90 -B 10 'def fractional|fractional' src/humanize/number.py tests/test_number.py"
src/humanize/number.py-299-        if not math.isfinite(float(value)):
src/humanize/number.py-300-            return _format_not_finite(float(value))
src/humanize/number.py-301-        value = int(value)
src/humanize/number.py-302-    except (TypeError, ValueError):
src/humanize/number.py-303-        return str(value)
src/humanize/number.py-304-    if not 0 <= value < 10:
src/humanize/number.py-305-        return str(value)
src/humanize/number.py-306-    return _(_APNUMBER_WORDS[value])
src/huma
…[11549 chars elided]…
0.0012], "1.20 m"),
tests/test_number.py-271-        ([0.00012], "120 μ"),
tests/test_number.py-272-        ([1e-23], "10.0 y"),
tests/test_number.py-273-        ([1e-24], "1.00 y"),
tests/test_number.py-274-        ([1e-25], "100 r"),
tests/test_number.py-275-        ([1e-26], "10.0 r"),
tests/test_number.py-276-        ([1, "°"], "1.00°"),
tests/test_number.py-277-        ([0.1, "°"], "100m°"),
tests/test_number.py-278-        ([100], "100"),
tests/test_number.py-279-        ([0.1], "100 m"),

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '145,192p' tests/test_number.py"
    [
        (0, "zero"),
        (1, "one"),
        (2, "two"),
        (4, "four"),
        (5, "five"),
        (9, "nine"),
        (10, "10"),
        ("7", "seven"),
        (None, "None"),
        (math.nan, "NaN"),
        (math.inf, "+Inf"),
        (-math.inf, "-Inf"),
        ("nan", "NaN"),
        ("-inf", "-Inf"),
    ],
)
def test_apnumber(test_input: int | str, expected: str) -> None:
    assert humanize.apnumber(test_input) == expected


@pytest.mark.parametrize(
    "test_inp
…[107 chars elided]…
, "5/6"),
        ("7", "7"),
        ("8.9", "8 9/10"),
        ("ten", "ten"),
        (None, "None"),
        (1 / 3, "1/3"),
        (1.5, "1 1/2"),
        (0.3, "3/10"),
        (0.333, "333/1000"),
        (math.nan, "NaN"),
        (math.inf, "+Inf"),
        (-math.inf, "-Inf"),
        ("nan", "NaN"),
        ("-inf", "-Inf"),
    ],
)
def test_fractional(test_input: float | str, expected: str) -> None:
    assert humanize.fractional(test_input) == expected


@pytest.mark.parametrize(

[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml'
[build-system]
build-backend = "hatchling.build"
requires = [
  "hatch-vcs",
  "hatchling>=1.27",
]

[project]
name = "humanize"
description = "Python humanize utilities"
readme = "README.md"
keywords = [
  "humanize time size",
]
license = "MIT"
license-files = [ "LICENCE" ]
maintainers = [ { name = "Hugo van Kemenade" } ]
authors = [ { name = "Jason Moiron", email = "jmoiron@jmoiron.net" } ]
requires-python = ">=3.10"
classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Intended
…[2546 chars elided]…
 import annotations" ]
lint.pydocstyle.convention = "google"
lint.future-annotations = true

[tool.pyproject-fmt]
max_supported_python = "3.15"

[tool.mypy]
pretty = true
strict = true
show_error_codes = true

[tool.pytest]
minversion = "9.0"
addopts = [ "--color=yes" ]
testpaths = [ "tests" ]
filterwarnings = [ "error" ]

[tool.coverage]
# Regexes for lines to exclude from consideration
report.exclude_also = [
  # Don't complain if non-runnable code isn't run:
  "if __name__ == .__main__.:",
]

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205047-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py
[command exit=1] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_number.py -k fractional_negative'
FFFF..                                                                   [100%]
=================================== FAILURES ===================================
____________________ test_fractional_negative[-1.3--1 3/10] ____________________

test_input = -1.3, expected = '-1 3/10'

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (-1.3, "-1 3/10"),
            (-2.5, "-2 1/2"),
            (-4 / 3, "-1 1/3"),
            ("-8.9", "-8 9/10"),
            (-0.3,
…[2418 chars elided]…
 ?    +

tests/test_number.py:204: AssertionError
=========================== short test summary info ============================
FAILED tests/test_number.py::test_fractional_negative[-1.3--1 3/10] - Asserti...
FAILED tests/test_number.py::test_fractional_negative[-2.5--2 1/2] - Assertio...
FAILED tests/test_number.py::test_fractional_negative[-1.3333333333333333--1 1/3]
FAILED tests/test_number.py::test_fractional_negative[-8.9--8 9/10] - Asserti...
4 failed, 2 passed, 219 deselected in 0.04s

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205047-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  9%]
.............sssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
sssssssss......s........................................................ [ 27%]
........................................................................ [ 37%]
........................................................................ [ 46%]
........................................................................ [ 55%]
....................
…[4263 chars elided]…
  16,437.5015 (>1000.0)    67;377        4.1856 (0.00)       3941           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
707 passed, 69 skipped in 8.10s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed negative mixed numbers to use a single minus sign: `fractional(-1.3)` now returns `"-1 3/10"`.

Added regression tests for negative mixed numbers, numeric strings, proper fractions, and integers.

Validation: 707 passed, 69 skipped.
