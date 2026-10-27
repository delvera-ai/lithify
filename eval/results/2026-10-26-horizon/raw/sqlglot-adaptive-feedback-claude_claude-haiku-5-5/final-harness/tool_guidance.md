- Harness files are under `.lithify/harness/` (not `.lithify/`); skills are
  `.lithify/harness/skills/<name>/SKILL.md`.
- The shell is macOS zsh: `timeout` is not installed; use the Bash tool's timeout. BSD `sed -i`
  needs `sed -i '' ...`. zsh does not word-split `$VAR`; list files literally.
- Running tests: use `<python> .lithify/harness/scripts/run_suite.py [test paths]` (python from
  `memory.md`) in the FOREGROUND with Bash `timeout: 600000`. It runs one pytest to a log file,
  refuses to start if a run from this checkout is already going (exit 3), kills itself at 540 s
  (exit 124, prints the test it was on), and prints FAILED lines plus the summary. Do not use
  the default 120 s Bash timeout for the full suite: it gets auto-backgrounded and you lose track
  of it. Run it as its own Bash call (not chained after ruff etc.).
- If the full run is backgrounded anyway or exits 124 while the WARNING lists other pytest
  processes: do not end your turn with "still pending". Fallback, once: run
  `run_suite.py tests/dialects tests/test_parser.py` in the foreground, quote its `SUMMARY`/`EXIT`,
  and say plainly the full suite did not finish. Do not retry the full run more than once.
- Never start a second full-suite run while one is in progress, and never `sleep` to wait (it is
  blocked). If a run is slow, read the script's WARNING about other pytest processes first;
  only kill pytest processes you started. `pytest -n` (xdist) is not installed. A `| tail`
  pipeline hides the left side's exit code, so `cmd | tail || fallback` never falls back, and
  zsh has no `$PIPESTATUS`. `run_suite.py` prints its own `EXIT:` line: don't pipe it.
- sqlglot is not installed in the project python; a probe script outside the repo needs
  `PYTHONPATH=. <python> /tmp/probe.py` from the repo root (`-I` ignores PYTHONPATH and fails).
