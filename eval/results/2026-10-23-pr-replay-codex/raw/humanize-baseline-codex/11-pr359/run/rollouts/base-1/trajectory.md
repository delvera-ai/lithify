# trajectory base-1

final message:
Fixed `metric()` to reduce decimal places when rounding carries into an extra integer digit. All three examples now produce the expected output.

Added 10 regression cases covering negative values, SI prefixes, and custom precision.

Validation: 736 passed, 110 skipped; `git diff --check` passed.

## events
[assistant] I’ll check the formatting logic, add regression tests for rounding carries, and run the project’s checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'def metric|metric\\(' src/humanize/number.py tests/test_number.py; rg --files -g AGENTS.md"
tests/test_number.py:328:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:329:    assert humanize.metric(*test_args) == expected
src/humanize/number.py:506:def metric(value: float, unit: str = "", precision: int = 3) -> str:
src/humanize/number.py:511:        >>> metric(1500, "V")
src/humanize/number.py:513:        >>> metric(2e8, "W")
src/humanize/number.py:515:        >>> metric(220e-6, "F")
src/humanize/number.py:517:        >>> metric(1e-14, precision=4)
src/humanize/number.py:528:    >>> metric(1e40)
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '506,610p' src/humanize/number.py"
def metric(value: float, unit: str = "", precision: int = 3) -> str:
    """Return a value with a metric SI unit-prefix appended.

    Examples:
        ```pycon
        >>> metric(1500, "V")
        '1.50 kV'
        >>> metric(2e8, "W")
        '200 MW'
        >>> metric(220e-6, "F")
        '220 μF'
        >>> metric(1e-14, precision=4)
        '10.00 f'

        ```

    The unit prefix is always chosen so that non-significant zero digits are required.
    i.e. `123,000` will become `123k`
…[1003 chars elided]…
ent // 3 * 3
        value /= 10 ** (new_bucket - old_bucket)
        digits = int(max(0, precision - exponent % 3 - 1))

    if exponent >= 3:
        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
    elif exponent < 0:
        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
    else:
        ordinal_ = ""
    value_ = format(value, f".{digits}f")
    if not (unit or ordinal_) or unit in ("°", "′", "″"):
        space = ""
    else:
        space = " "

    return f"{value_}{space}{ordinal_}{unit}"

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '240,340p' tests/test_number.py"
    "test_args, expected",
    [
        ([1], "1"),
        ([None], None),
        ([0.0001, "{:.0%}"], "0%"),
        ([0.0001, "{:.0%}", 0.01], "<1%"),
        ([0.9999, "{:.0%}", None, 0.99], ">99%"),
        ([0.0001, "{:.0%}", 0.01, None, "under ", None], "under 1%"),
        ([0.9999, "{:.0%}", None, 0.99, None, "above "], "above 99%"),
        ([1, humanize.intword, 1e6, None, "under "], "under 1.0 million"),
        ([math.nan], "NaN"),
        ([math.inf], "+Inf"),
        ([-math.inf
…[1843 chars elided]…
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

[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205137-bug-humanize-metric-can-show-one/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205137-bug-humanize-metric-can-show-one/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  8%]
...................sssssssssssssssssssssssssssssssssssssssssssssssssssss [ 17%]
ssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss......... [ 25%]
........................................................................ [ 34%]
........................................................................ [ 42%]
........................................................................ [ 51%]
....................
…[4325 chars elided]…
  20,125.9827 (>1000.0)   112;265        4.3585 (0.00)       3772           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
736 passed, 110 skipped in 9.08s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
src/humanize/number.py |  3 +++
 tests/test_number.py   | 10 ++++++++++
 2 files changed, 13 insertions(+)

[assistant] Fixed `metric()` to reduce decimal places when rounding carries into an extra integer digit. All three examples now produce the expected output.

Added 10 regression cases covering negative values, SI prefixes, and custom precision.

Validation: 736 passed, 110 skipped; `git diff --check` passed.
