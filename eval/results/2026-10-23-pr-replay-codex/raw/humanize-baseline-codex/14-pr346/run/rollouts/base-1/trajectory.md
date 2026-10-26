# trajectory base-1

final message:
Fixed `intword()` rollover at 10²⁴, 10²⁷, 10³⁰, and 10³³ by avoiding precision loss in the carry comparison.

Added regression coverage for both signs, custom precision, and nearby values that must not roll over.

Validation: 756 passed, 110 skipped; diff checks passed.

## events
[assistant] I’ll check how `intword()` handles rounding near magnitude boundaries, add regression coverage, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*intword*' -g 'pyproject.toml' -g 'test*'"
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
~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205456-bug-humanize-intword-fails-to-ca/base-1
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

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'cat AGENTS.md; git status --short; rg -n \"def intword|powers|human_powers|intword\" src/humanize/number.py tests/test_number.py; cat pyproject.toml'"
<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[5308 chars elided]…
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

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '200,300p' src/humanize/number.py"
        result = f"{value:,}"
    if thousands_sep != "," or decimal_sep != ".":
        result = result.translate(str.maketrans(",.", thousands_sep + decimal_sep))
    return result


powers = [10**x for x in (3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 100)]
human_powers = (
    NS_("thousand", "thousand"),
    NS_("million", "million"),
    NS_("billion", "billion"),
    NS_("trillion", "trillion"),
    NS_("quadrillion", "quadrillion"),
    NS_("quintillion", "quintillion"),
    NS_("sextillion
…[2042 chars elided]…
rs[ordinal + 1]:
        # After rounding, we end up just at the next power
        ordinal += 1
        rounded_value = 1.0

    singular, plural = human_powers[ordinal]
    unit = _ngettext(singular, plural, math.ceil(rounded_value))
    decimal_sep = decimal_separator()
    number = (format % rounded_value).replace(".", decimal_sep)
    return f"{negative_prefix}{number} {unit}"


def apnumber(value: NumberOrString) -> str:
    """Converts an integer to Associated Press style.

    Examples:

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '85,155p' tests/test_number.py"

@pytest.mark.parametrize("sign", [1, -1])
def test_intcomma_large_integer(sign: int) -> None:
    value = sign * (10**400 + 123)
    expected = ("-" if sign < 0 else "") + "10" + ",000" * 132 + ",123"
    assert humanize.intcomma(value) == expected


def test_intword_powers() -> None:
    # make sure that powers & human_powers have the same number of items
    assert len(number.powers) == len(number.human_powers)


@pytest.mark.parametrize(
    "test_args, expected",
    [
        (["0"], "0"),
…[1636 chars elided]…
       (["1234567", "%.0f"], "1 million"),
        (["1234567", "%.1f"], "1.2 million"),
        (["1234567", "%.2f"], "1.23 million"),
        (["1234567", "%.3f"], "1.235 million"),
        (["999500", "%.0f"], "1 million"),
        (["999499", "%.0f"], "999 thousand"),
    ],
)
def test_intword(test_args: list[str], expected: str) -> None:
    assert humanize.intword(*test_args) == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (0, "zero"),
        (1, "one"),

[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205456-bug-humanize-intword-fails-to-ca/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-205456-bug-humanize-intword-fails-to-ca/base-1/tests/test_number.py
[assistant] The carry check multiplies a rounded float by a large integer, which loses precision at these magnitudes. I changed it to compare the rounded value with the ratio between magnitudes. The new tests cover all four reported boundaries, both signs, two decimal formats, and nearby values that must stay in the lower magnitude.
[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'"
........................................................................ [  8%]
.....................sssssssssssssssssssssssssssssssssssssssssssssssssss [ 16%]
ssssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss....... [ 24%]
........................................................................ [ 33%]
........................................................................ [ 41%]
........................................................................ [ 49%]
....................
…[4443 chars elided]…
00,854.5078 (>1000.0)   181;502        3.3475 (0.00)       3996           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
756 passed, 110 skipped in 8.24s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed `intword()` rollover at 10²⁴, 10²⁷, 10³⁰, and 10³³ by avoiding precision loss in the carry comparison.

Added regression coverage for both signs, custom precision, and nearby values that must not roll over.

Validation: 756 passed, 110 skipped; diff checks passed.
