# trajectory base-1

final message:
Fixed negative mixed fractions to show one minus sign: `-1 3/10` and `-2 1/2`.

Added regression coverage for negative mixed numbers, strings, integers, and proper fractions.

Checks passed: **706 passed, 69 skipped**; diff check clean.

## events
[assistant] I’ll check the formatter and tests, fix the sign handling, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'def fractional|fractional\\(' src tests; rg --files -g AGENTS.md"
~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204601-bug-humanize-fractional-1-3-retu/base-1
tests/test_number.py:188:def test_fractional(test_input: float | str, expected: str) -> None:
tests/test_number.py:189:    assert humanize.fractional(test_input) == expected
src/humanize/number.py:309:def fractional(value: NumberOrString) -> str:
src/humanize/number.py:327:        >>> fractional(0.3)
src/humanize/number.py:329:        >>> fractional(1.3)
src/humanize/number.py:331:        >>> fractional(float(1/3))
src/humanize/number.py:333:        >>> fractional(1)
src/humanize/number.py:335:        >>> fractional("ten")
src/humanize/number.py:337:        >>> fractional(None)
tests/test_benchmarks.py:32:def test_fractional(benchmark: BenchmarkFixture) -> None:
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '300,380p' src/humanize/number.py"
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

    This function returns a human-readable fractional number in form o
…[1212 chars elided]…
s passed in
        # (or variants of that integer like 1.0000)
        return f"{whole_number:.0f}"

    if not whole_number:
        return f"{numerator:.0f}/{denominator:.0f}"

    return f"{whole_number:.0f} {numerator:.0f}/{denominator:.0f}"


def scientific(value: NumberOrString, precision: int = 2) -> str:
    """Return number in string scientific notation z.wq x 10ⁿ.

    Examples:
        ```pycon
        >>> scientific(float(0.3))
        '3.00 x 10⁻¹'
        >>> scientific(int(500))

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '120,200p' tests/test_number.py"
        ([1_100_000_000_000_000_000_000_000_000_000_000_000], "1100.0 decillion"),
        ([2_100_000_000_000_000_000_000_000_000_000_000_000], "2100.0 decillion"),
        ([2e100], "2.0 googol"),
        ([None], "None"),
        (["1230000", "%0.2f"], "1.23 million"),
        ([10**101], "10.0 googol"),
        ([math.nan], "NaN"),
        ([math.inf], "+Inf"),
        ([-math.inf], "-Inf"),
        (["nan"], "NaN"),
        (["-inf"], "-Inf"),
        (["1234567", "%.0f"], "1 million"),
   
…[1248 chars elided]…
      (math.inf, "+Inf"),
        (-math.inf, "-Inf"),
        ("nan", "NaN"),
        ("-inf", "-Inf"),
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

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204601-bug-humanize-fractional-1-3-retu/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204601-bug-humanize-fractional-1-3-retu/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  9%]
.............sssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
sssssssss......s........................................................ [ 27%]
........................................................................ [ 37%]
........................................................................ [ 46%]
........................................................................ [ 55%]
....................
…[4244 chars elided]…
)  19,041.0065 (>1000.0)   262;330        4.8813 (0.00)       4149           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
706 passed, 69 skipped in 7.90s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed negative mixed fractions to show one minus sign: `-1 3/10` and `-2 1/2`.

Added regression coverage for negative mixed numbers, strings, integers, and proper fractions.

Checks passed: **706 passed, 69 skipped**; diff check clean.
