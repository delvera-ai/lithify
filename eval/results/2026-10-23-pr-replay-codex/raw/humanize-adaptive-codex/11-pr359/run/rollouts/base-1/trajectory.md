# trajectory base-1

final message:
Fixed `metric()` to remove the extra decimal place when rounding adds an integer digit. All three examples now return the expected output.

Added 16 regression cases covering signs, prefixes, precisions, and nearby values. Existing tests remain unchanged.

Validation: 742 passed, 110 skipped; `git diff --check` passed.

## events
[assistant] I’ll check the formatting logic, add regression tests for rounding carry, and run the project’s checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*metric*' -g 'pyproject.toml' -g 'tox.ini'"
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
~/.cache/lithify/work/repo-f19ff99309c1/20261023-205631-bug-humanize-metric-can-show-one/base-1
src/humanize/number.py
docs/number.md
pyproject.toml
tox.ini
tests/test_number.py
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'cat AGENTS.md; rg -n \"def metric|metric\\(\" src/humanize/number.py tests/test_number.py; cat pyproject.toml; cat tox.ini; git status --short'"
<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never modify or skip existing tests, even to strengthen assertions. Add regression t
…[4858 chars elided]…
commands =
    {envpython} -m pytest \
      --cov humanize \
      --cov tests \
      --cov-report html \
      --cov-report term \
      --cov-report xml \
      {posargs}

[testenv:docs]
deps =
    -r docs/requirements.txt
commands =
    mkdocs build

[testenv:lint]
skip_install = true
deps =
    prek
commands =
    prek run --all-files --show-diff-on-failure

[testenv:mypy]
deps =
    -r requirements-mypy.txt
commands =
    mypy . {posargs}

[pytest]
addopts = --color=yes --doctest-modules

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"490,610p\" src/humanize/number.py; sed -n \"255,345p\" tests/test_number.py'"
    else:
        token = ""

    if isinstance(format, str):
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
     
…[3675 chars elided]…
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

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205631-bug-humanize-metric-can-show-one/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-205631-bug-humanize-metric-can-show-one/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  8%]
...................sssssssssssssssssssssssssssssssssssssssssssssssssssss [ 16%]
ssssssssssssssssssss......sssssssssssssssssssssssssssssssssssss......... [ 25%]
........................................................................ [ 33%]
........................................................................ [ 42%]
........................................................................ [ 50%]
....................
…[4363 chars elided]…
16,625.9997 (>1000.0)    58;462        4.1797 (0.00)       3814           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
742 passed, 110 skipped in 8.83s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed `metric()` to remove the extra decimal place when rounding adds an integer digit. All three examples now return the expected output.

Added 16 regression cases covering signs, prefixes, precisions, and nearby values. Existing tests remain unchanged.

Validation: 742 passed, 110 skipped; `git diff --check` passed.
