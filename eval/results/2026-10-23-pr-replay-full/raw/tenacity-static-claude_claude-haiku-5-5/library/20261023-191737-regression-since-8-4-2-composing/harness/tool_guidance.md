- The project venv (python in memory.md) runs pytest but has no pip, ruff, mypy or PyYAML;
  `uv`/`uvx` are not on PATH, and a new `/tmp` venv dies in ensurepip (SIGABRT). Don't probe or
  build one; `.lithify/harness/scripts/check_changed.py` is the stdlib substitute.
- The shell is zsh: quote globs (`--include='*.py'`), or the command fails with "no matches found".
  `${PIPESTATUS[0]}` prints empty; use `cmd > /tmp/out.txt 2>&1; echo "exit=$?"; tail /tmp/out.txt`.
  A word starting with `=` (e.g. `echo ===`) aborts the command ("== not found"); use `echo ---`.
- Run tests with `<project python> .lithify/harness/scripts/run_tests.py [--timeout S] [node ids]`
  (default 300 s, full log in /tmp/run_tests.log). Raw `pytest` has no time limit here: the full
  suite once hung with no output until the 900 s kill (a sync combinator holding an async
  strategy; see the tenacity-change-contract skill, §1b). A hang is a bug, not a slow suite.
