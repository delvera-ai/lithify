# trajectory base-1

final message:
Fixed the singular-byte formatting so `naturalsize(1.0)` and `naturalsize("1")` return `"1 Byte"` when `gnu=False`.

Added regression coverage for decimal, binary, GNU, and negative inputs. All checks passed: 611 tests passed, 24 skipped.

## events
[assistant] I’ll check the byte formatting logic, make a targeted fix, and run the project’s tests.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g AGENTS.md -g '*filesize*' -g '*test*' -g 'pyproject.toml'"
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
~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204305-regression-when-gnu-is-false-hum/base-1
AGENTS.md
pyproject.toml
docs/filesize.md
tests/test_filesize.py
tests/test_time.py
tests/test_i18n.py
tests/test_number.py
tests/test_lists.py
src/humanize/filesize.py

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
[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204305-regression-when-gnu-is-false-hum/base-1/src/humanize/filesize.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204305-regression-when-gnu-is-false-hum/base-1/tests/test_filesize.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
........................................................................ [ 11%]
..sssssssssssssssssssssss......s........................................ [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 90%]
...........................................................              [100%]
611 passed, 24 skipped in 0.65s

[assistant] Fixed the singular-byte formatting so `naturalsize(1.0)` and `naturalsize("1")` return `"1 Byte"` when `gnu=False`.

Added regression coverage for decimal, binary, GNU, and negative inputs. All checks passed: 611 tests passed, 24 skipped.
