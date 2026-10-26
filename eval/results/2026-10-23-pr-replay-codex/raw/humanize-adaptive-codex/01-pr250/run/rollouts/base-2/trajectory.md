# trajectory base-2

final message:
Fixed the singular-byte formatting so `naturalsize(1.0)` and `naturalsize("1")` return `"1 Byte"` when `gnu=False`.

Added regression coverage for decimal and binary modes, including negative inputs. All checks passed: 609 tests passed, 24 skipped.

## events
[assistant] I’ll check the size formatting code, make a minimal fix, and run the project’s tests.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*filesize*' -g '*size*' -g 'pyproject.toml'"
~/.cache/lithify/work/repo-f19ff99309c1/20261023-204305-regression-when-gnu-is-false-hum/base-2
src/humanize/filesize.py
docs/filesize.md
pyproject.toml
AGENTS.md
tests/test_filesize.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat src/humanize/filesize.py tests/test_filesize.py pyproject.toml'
"""Bits and bytes related humanization."""

from __future__ import annotations

suffixes = {
    "decimal": (
        " kB",
        " MB",
        " GB",
        " TB",
        " PB",
        " EB",
        " ZB",
        " YB",
        " RB",
        " QB",
    ),
    "binary": (
        " KiB",
        " MiB",
        " GiB",
        " TiB",
        " PiB",
        " EiB",
        " ZiB",
        " YiB",
        " RiB",
        " QiB",
    ),
    "gnu": "KMGTPEZYRQ",
}


def naturalsize(
    
…[8092 chars elided]…
own-first-party = [ "humanize" ]
lint.isort.required-imports = [ "from __future__ import annotations" ]
lint.pydocstyle.convention = "google"

[tool.pyproject-fmt]
max_supported_python = "3.14"

[tool.pytest.ini_options]
addopts = "--color=yes"
filterwarnings = [
  "error",
  # https://github.com/dateutil/dateutil/issues/1314
  "ignore:datetime.datetime.utcfromtimestamp:DeprecationWarning:dateutil.tz.tz",
]
testpaths = [ "tests" ]

[tool.mypy]
pretty = true
strict = true
show_error_codes = true

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-204305-regression-when-gnu-is-false-hum/base-2/src/humanize/filesize.py, update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-204305-regression-when-gnu-is-false-hum/base-2/tests/test_filesize.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [ 11%]
sssssssssssssssssssssss......s.......................................... [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 90%]
.........................................................                [100%]
609 passed, 24 skipped in 0.70s

[assistant] Fixed the singular-byte formatting so `naturalsize(1.0)` and `naturalsize("1")` return `"1 Byte"` when `gnu=False`.

Added regression coverage for decimal and binary modes, including negative inputs. All checks passed: 609 tests passed, 24 skipped.
