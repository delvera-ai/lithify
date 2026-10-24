# trajectory base-1

final message:
Fixed `fractional()` to return plain integers when the fractional part rounds to a whole number, including zero and negative inputs.

Added 10 regression cases without modifying existing tests. All checks passed: 725 tests passed, 74 skipped; diff whitespace check passed.

## events
[assistant] I’ll check how `fractional()` formats these values, add regression tests, and run the project’s checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*fraction*' -g 'pyproject.toml'"
~/.cache/lithify/work/repo-f19ff99309c1/20261023-205349-bug-humanize-fractional-produces/base-1
src/humanize/number.py
AGENTS.md
docs/number.md
pyproject.toml
tests/test_number.py

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git status --short; rg -n \"def fractional|fractional\" src/humanize/number.py tests/test_number.py; cat pyproject.toml'"
tests/test_number.py:192:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:193:    assert humanize.fractional(test_input) == expected
src/humanize/number.py:311:def fractional(value: NumberOrString) -> str:
src/humanize/number.py:312:    """Convert to fractional number.
src/humanize/number.py:317:    This function returns a human-readable fractional number in form of fractions and
src/humanize/number.py:329:        >>> fractional(0.3)
src/humanize/number.p
…[3605 chars elided]…
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

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"311,400p\" src/humanize/number.py; sed -n \"140,215p\" tests/test_number.py; find src tests -name AGENTS.md'"
def fractional(value: NumberOrString) -> str:
    """Convert to fractional number.

    There will be some cases where one might not want to show ugly decimal places for
    floats and decimals.

    This function returns a human-readable fractional number in form of fractions and
    mixed fractions.

    Pass in a string, or a number or a float, and this function returns:

    * a string representation of a fraction
    * or a whole number
    * or a mixed fraction
    * or the str output of t
…[3536 chars elided]…
x 10³"),
        ([5.5], "5.50 x 10⁰"),
        ([5781651000], "5.78 x 10⁹"),
        (["1000"], "1.00 x 10³"),
        (["99"], "9.90 x 10¹"),
        ([0.3], "3.00 x 10⁻¹"),
        (["foo"], "foo"),
        ([None], "None"),
        ([1000, 1], "1.0 x 10³"),
        ([0.3, 1], "3.0 x 10⁻¹"),
        ([1000, 0], "1 x 10³"),
        ([0.3, 0], "3 x 10⁻¹"),
        ([1e20], "1.00 x 10²⁰"),
        ([2e-20], "2.00 x 10⁻²⁰"),
        ([-3e20], "-3.00 x 10²⁰"),
        ([-4e-20], "-4.00 x 10⁻²⁰"),

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205349-bug-humanize-fractional-produces/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205349-bug-humanize-fractional-produces/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'"
........................................................................ [  9%]
...................sssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
ssssssssssssssssssss......s............................................. [ 27%]
........................................................................ [ 36%]
........................................................................ [ 45%]
........................................................................ [ 54%]
....................
…[4420 chars elided]…
,292.0270 (>1000.0)    38;190        2.4121 (0.00)       2826           1
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
725 passed, 74 skipped in 9.94s

[assistant] Fixed `fractional()` to return plain integers when the fractional part rounds to a whole number, including zero and negative inputs.

Added 10 regression cases without modifying existing tests. All checks passed: 725 tests passed, 74 skipped; diff whitespace check passed.
