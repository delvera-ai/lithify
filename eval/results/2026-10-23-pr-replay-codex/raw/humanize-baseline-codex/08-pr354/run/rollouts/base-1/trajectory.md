# trajectory base-1

final message:
Fixed `fractional()` to combine whole-number fractions into a plain integer, including zero and negative inputs.

Added regression coverage for rounding near zero and whole numbers. All checks passed: **725 passed, 74 skipped**.

## events
[assistant] I’ll inspect `fractional()` and its tests, fix integer normalization, and run the project checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'def fractional|fractional\\(' src tests; rg --files -g AGENTS.md -g pyproject.toml -g tox.ini"
tests/test_number.py:192:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:193:    assert humanize.fractional(test_input) == expected
src/humanize/number.py:311:def fractional(value: NumberOrString) -> str:
src/humanize/number.py:329:        >>> fractional(0.3)
src/humanize/number.py:331:        >>> fractional(1.3)
src/humanize/number.py:333:        >>> fractional(float(1/3))
src/humanize/number.py:335:        >>> fractional(1)
src/humanize/number.py:337:        >>> fractional("ten")
src/humanize/number.py:339:        >>> fractional(None)
tests/test_benchmarks.py:32:def test_fractional(benchmark: BenchmarkFixture) -> None:
AGENTS.md
tox.ini
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '300,390p' src/humanize/number.py"
    try:
        if not math.isfinite(float(value)):
            return _format_not_finite(float(value))
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    if not 0 <= value < 10:
        return str(value)
    return _(_APNUMBER_WORDS[value])


def fractional(value: NumberOrString) -> str:
    """Convert to fractional number.

    There will be some cases where one might not want to show ugly decimal places for
    floats and decimals.

    This function
…[1634 chars elided]…
 part; absorb it
    # from the fractional part so the result reads as a normal mixed
    # fraction.
    return f"{whole_number:.0f} {abs(numerator):.0f}/{denominator:.0f}"


def scientific(value: NumberOrString, precision: int = 2) -> str:
    """Return number in string scientific notation z.wq x 10ⁿ.

    Examples:
        ```pycon
        >>> scientific(float(0.3))
        '3.00 x 10⁻¹'
        >>> scientific(int(500))
        '5.00 x 10²'
        >>> scientific(-1000)
        '-1.00 x 10³'

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '140,205p' tests/test_number.py"
def test_intword(test_args: list[str], expected: str) -> None:
    assert humanize.intword(*test_args) == expected


@pytest.mark.parametrize(
    "test_input, expected",
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
        ("-inf", "-Inf"
…[621 chars elided]…
    (-1.3, "-1 3/10"),
        (-2.5, "-2 1/2"),
        (-0.5, "-1/2"),
    ],
)
def test_fractional(test_input: float | str, expected: str) -> None:
    assert humanize.fractional(test_input) == expected


@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([1000], "1.00 x 10³"),
        ([-1000], "-1.00 x 10³"),
        ([5.5], "5.50 x 10⁰"),
        ([5781651000], "5.78 x 10⁹"),
        (["1000"], "1.00 x 10³"),
        (["99"], "9.90 x 10¹"),
        ([0.3], "3.00 x 10⁻¹"),

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
…[2747 chars elided]…
ons" ]
lint.pydocstyle.convention = "google"
lint.future-annotations = true

[tool.pyproject-fmt]
max_supported_python = "3.15"

[tool.mypy]
strict = true
pretty = true
num_workers = 4
show_error_codes = true

[tool.pytest]
addopts = [ "--color=yes" ]
filterwarnings = [ "error" ]
minversion = "9.0"
testpaths = [ "tests" ]

[tool.coverage]
# Regexes for lines to exclude from consideration
report.exclude_also = [
  # Don't complain if non-runnable code isn't run:
  "if __name__ == .__main__.:",
]

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204912-bug-humanize-fractional-produces/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204912-bug-humanize-fractional-produces/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff'
src/humanize/number.py |  7 +++----
 tests/test_number.py   | 10 ++++++++++
 2 files changed, 13 insertions(+), 4 deletions(-)

--- Changes ---

src/humanize/number.py
  @@ -361,10 +361,9 @@ def fractional(value: NumberOrString) -> str:
  -    if whole_number and not numerator and denominator == 1:
  -        # this means that an integer was passed in
  -        # (or variants of that integer like 1.0000)
  -        return f"{whole_number:.0f}"
  +    if denominator == 1:
  +        # The fracti
…[177 chars elided]…
nator:.0f}"
  +3 -4

tests/test_number.py
  @@ -167,6 +167,16 @@ def test_apnumber(test_input: int | str, expected: str) -> None:
  +        (0, "0"),
  +        (-0.0, "0"),
  +        (0.0000001, "0"),
  +        (-0.0000001, "0"),
  +        (0.9999999, "1"),
  +        (-0.9999999, "-1"),
  +        (2.9999999, "3"),
  +        (-2.9999999, "-3"),
  +        (2.0000001, "2"),
  +        (-2.0000001, "-2"),
           (1, "1"),
           (2.0, "2"),
           (4.0 / 3.0, "1 1/3"),
  +10 -0

[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  9%]
...................sssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
ssssssssssssssssssss......s............................................. [ 27%]
........................................................................ [ 36%]
........................................................................ [ 45%]
........................................................................ [ 54%]
....................
…[4325 chars elided]…
)  27,540.9911 (>1000.0)   204;250        4.6883 (0.00)       3945           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
725 passed, 74 skipped in 8.07s

[assistant] Fixed `fractional()` to combine whole-number fractions into a plain integer, including zero and negative inputs.

Added regression coverage for rounding near zero and whole numbers. All checks passed: **725 passed, 74 skipped**.
