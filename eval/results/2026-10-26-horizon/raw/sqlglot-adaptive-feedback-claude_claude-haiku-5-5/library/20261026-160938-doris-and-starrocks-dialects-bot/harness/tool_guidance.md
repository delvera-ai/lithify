- The shell is macOS zsh: `timeout` is not installed. Run commands without it and use the Bash
  tool's own timeout for long runs. BSD `sed -i` needs `sed -i '' ...`. zsh does not word-split
  `$VAR`, so `F="a.py b.py"; ruff check $F` passes one bogus path; list files literally. Quote
  globs in flags (`--include='*.py'`).
- Running tests: use `<python> .lithify/harness/scripts/run_suite.py [test paths]` (python from
  `memory.md`) in the FOREGROUND with Bash `timeout: 600000`. It runs one pytest to a log file,
  refuses to start if a run from this checkout is already going (exit 3), kills itself at 540 s
  (exit 124, prints the test it was on), and prints FAILED lines plus the summary. Do not use
  the default 120 s Bash timeout for the full suite: it gets auto-backgrounded and you lose track
  of it.
- Never start a second full-suite run while one is in progress, and never `sleep` to wait (it is
  blocked). If a run is slow, read the script's WARNING about other pytest processes first;
  only kill pytest processes you started. `pytest -n` (xdist) is not installed. A `| tail`
  pipeline hides the left side's exit code, so `cmd | tail || fallback` never falls back.
