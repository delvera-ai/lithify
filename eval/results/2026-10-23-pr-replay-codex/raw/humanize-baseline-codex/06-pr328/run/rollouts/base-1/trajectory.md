# trajectory base-1

final message:
Fixed `metric()` to advance to the next SI prefix when rounding reaches 1000, preserving precision and leaving the largest prefix unchanged.

Added regression coverage for the reported examples, negative values, precision settings, and prefix limits.

Checks passed: **716 passed, 69 skipped**; diff check clean.

## events
[assistant] I’ll check how `metric()` chooses its prefix, fix the rounding boundary, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*number*' -g '*metric*' -g 'pyproject.toml' -g 'tox.ini'"
~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204641-bug-humanize-metric-can-output-a/base-1
src/humanize/number.py
tox.ini
docs/number.md
AGENTS.md
tests/test_number.py
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,120p' AGENTS.md"
<!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->

[command exit=0] /bin/zsh -lc "rtk proxy rg -n -A 155 '"'^def metric'"' src/humanize/number.py"
502:def metric(value: float, unit: str = "", precision: int = 3) -> str:
503-    """Return a value with a metric SI unit-prefix appended.
504-
505-    Examples:
506-        ```pycon
507-        >>> metric(1500, "V")
508-        '1.50 kV'
509-        >>> metric(2e8, "W")
510-        '200 MW'
511-        >>> metric(220e-6, "F")
512-        '220 μF'
513-        >>> metric(1e-14, precision=4)
514-        '10.00 f'
515-
516-        ```
517-
518-    The unit prefix is always chosen so that non-signifi
…[951 chars elided]…
value /= 10 ** (exponent // 3 * 3)
547-    if exponent >= 3:
548-        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
549-    elif exponent < 0:
550-        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
551-    else:
552-        ordinal_ = ""
553-    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
554-    if not (unit or ordinal_) or unit in ("°", "′", "″"):
555-        space = ""
556-    else:
557-        space = " "
558-
559-    return f"{value_}{space}{ordinal_}{unit}"

[command exit=0] /bin/zsh -lc "rtk proxy rg -n -A 100 -B 10 'def test_metric|metric\\(' tests/test_number.py"
301-        ([10, "", 3], "10.0"),
302-        ([100, "", 3], "100"),
303-        ([1000, "", 3], "1.00 k"),
304-        ([math.nan], "NaN"),
305-        ([math.nan, "m"], "NaN"),
306-        ([math.inf], "+Inf"),
307-        ([-math.inf], "-Inf"),
308-    ],
309-    ids=str,
310-)
311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
312:    assert humanize.metric(*test_args) == expected

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '245,315p' tests/test_number.py"

@pytest.mark.parametrize(
    "test_args, expected",
    [
        ([0], "0.00"),
        ([1, "Hz"], "1.00 Hz"),
        ([1.0, "W"], "1.00 W"),
        ([3, "C"], "3.00 C"),
        ([3, "W", 5], "3.0000 W"),
        ([1.23456], "1.23"),
        ([12.3456], "12.3"),
        ([123.456], "123"),
        ([1234.56], "1.23 k"),
        ([12345, "", 6], "12.3450 k"),
        ([200_000], "200 k"),
        ([1e25, "m"], "10.0 Ym"),
        ([1e26, "m"], "100 Ym"),
        ([1e27, "A"], "1.00 RA"),
 
…[1056 chars elided]…
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

[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml tox.ini'
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
…[3213 chars elided]…
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

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204641-bug-humanize-metric-can-output-a/base-1/src/humanize/number.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204641-bug-humanize-metric-can-output-a/base-1/tests/test_number.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [  9%]
.............sssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 18%]
sssssssss......s........................................................ [ 27%]
........................................................................ [ 36%]
........................................................................ [ 45%]
........................................................................ [ 55%]
....................
…[4283 chars elided]…
217,562.9925 (>1000.0)   320;217        2.6972 (0.00)       3972           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
716 passed, 69 skipped in 9.51s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
src/humanize/number.py |  6 +++++-
 tests/test_number.py   | 12 ++++++++++++
 2 files changed, 17 insertions(+), 1 deletion(-)

[assistant] Fixed `metric()` to advance to the next SI prefix when rounding reaches 1000, preserving precision and leaving the largest prefix unchanged.

Added regression coverage for the reported examples, negative values, precision settings, and prefix limits.

Checks passed: **716 passed, 69 skipped**; diff check clean.
