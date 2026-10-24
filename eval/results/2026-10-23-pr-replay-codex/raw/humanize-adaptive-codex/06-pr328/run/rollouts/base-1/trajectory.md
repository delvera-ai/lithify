# trajectory base-1

final message:
Fixed `metric()` to advance to the next SI prefix when rounding reaches 1000, while preserving output at the largest prefix.

Added 14 regression cases covering the reported examples, negative values, precision, and prefix limits. All checks passed: 718 tests passed, 69 skipped.

## events
[assistant] I’ll check how `metric()` selects prefixes, add regression tests for rounding to 1000, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*metric*' -g 'pyproject.toml' -g 'test*'"
~/.cache/lithify/work/repo-f19ff99309c1/20261023-205142-bug-humanize-metric-can-output-a/base-1
src/humanize/number.py
AGENTS.md
docs/number.md
pyproject.toml
tests/test_number.py
tests/test_lists.py
tests/test_i18n.py
tests/test_benchmarks.py
tests/test_time.py
tests/test_filesize.py

[command exit=0] /bin/zsh -lc "rtk rg -n 'def metric|metric\\(|SI_PREFIX' src/humanize/number.py tests/test_number.py"
tests/test_number.py:311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:312:    assert humanize.metric(*test_args) == expected
src/humanize/number.py:502:def metric(value: float, unit: str = "", precision: int = 3) -> str:
src/humanize/number.py:507:        >>> metric(1500, "V")
src/humanize/number.py:509:        >>> metric(2e8, "W")
src/humanize/number.py:511:        >>> metric(220e-6, "F")
src/humanize/number.py:513:        >>> metric(1e-14, precision=4)
src/humanize/number.py:524:    >>> metric(1e40)

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc 'rtk cat pyproject.toml'
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

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '490,610p' src/humanize/number.py"
        return token + format.format(value)

    if callable(format):
        return token + format(value)

    msg = (
        "Invalid format. Must be either a valid formatting string, or a function "
        "that accepts value and returns a string."
    )
    raise ValueError(msg)


def metric(value: float, unit: str = "", precision: int = 3) -> str:
    """Return a value with a metric SI unit-prefix appended.

    Examples:
        ```pycon
        >>> metric(1500, "V")
        '1.50 kV'
  
…[1007 chars elided]…
return scientific(value, precision - 1) + unit

    value /= 10 ** (exponent // 3 * 3)
    if exponent >= 3:
        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
    elif exponent < 0:
        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
    else:
        ordinal_ = ""
    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
    if not (unit or ordinal_) or unit in ("°", "′", "″"):
        space = ""
    else:
        space = " "

    return f"{value_}{space}{ordinal_}{unit}"

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '230,325p' tests/test_number.py"
        ([None], None),
        ([0.0001, "{:.0%}"], "0%"),
        ([0.0001, "{:.0%}", 0.01], "<1%"),
        ([0.9999, "{:.0%}", None, 0.99], ">99%"),
        ([0.0001, "{:.0%}", 0.01, None, "under ", None], "under 1%"),
        ([0.9999, "{:.0%}", None, 0.99, None, "above "], "above 99%"),
        ([1, humanize.intword, 1e6, None, "under "], "under 1.0 million"),
        ([math.nan], "NaN"),
        ([math.inf], "+Inf"),
        ([-math.inf], "-Inf"),
    ],
)
def test_clamp(test_args: list[t
…[1643 chars elided]…
 2], "1.0"),
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

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205142-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py
[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205142-bug-humanize-metric-can-output-a/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  9%]
.............sssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
sssssssss......s........................................................ [ 27%]
........................................................................ [ 36%]
........................................................................ [ 45%]
........................................................................ [ 54%]
....................
…[4263 chars elided]…
  20,291.0160 (>1000.0)   312;622        4.1128 (0.00)       4066           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
718 passed, 69 skipped in 8.17s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff'
src/humanize/number.py |  7 ++++++-
 tests/test_number.py   | 25 +++++++++++++++++++++++++
 2 files changed, 31 insertions(+), 1 deletion(-)

--- Changes ---

src/humanize/number.py
  @@ -544,13 +544,18 @@ def metric(value: float, unit: str = "", precision: int = 3) -> str:
  +    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
  +    if abs(float(value_)) >= 1000 and exponent < 30:
  +        value /= 1000
  +        exponent = (exponent // 3 + 1) * 3
  +        value_ 
…[905 chars elided]…
, "999.9 V"),
  +        (999.99, "V", 4, "1.000 kV"),
  +        (999.9, "", 0, "1 k"),
  +        (999.9, "°", 3, "1.00k°"),
  +        (9.999e-28, "V", 3, "1.00 rV"),
  +        (9.999e29, "V", 3, "1.00 QV"),
  +        (9.999e32, "V", 3, "1000 QV"),
  +        (-9.999e32, "V", 3, "-1000 QV"),
  +    ],
  +)
  +def test_metric_rounding_prefix(
  +    value: float, unit: str, precision: int, expected: str
  +) -> None:
  +    assert humanize.metric(value, unit, precision) == expected
  +25 -0

[assistant] Fixed `metric()` to advance to the next SI prefix when rounding reaches 1000, while preserving output at the largest prefix.

Added 14 regression cases covering the reported examples, negative values, precision, and prefix limits. All checks passed: 718 tests passed, 69 skipped.
