- Harness files are in the working tree: skills at `.lithify/harness/skills/<name>/SKILL.md`,
  scripts at `.lithify/harness/scripts/`. Read a skill there with `cat`; never `find /` or read
  copies outside the working tree (one search did both and returned a 55 KB dump).
- The project venv (python in memory.md) runs pytest but has no pip, ruff, mypy or PyYAML;
  `uv`/`uvx` are not on PATH, and a new `/tmp` venv dies in ensurepip (SIGABRT). Don't probe or
  build one; `.lithify/harness/scripts/check_changed.py` is the stdlib substitute.
- The shell is zsh: quote every glob, including grep's (`--include='*.py'`), or the whole command
  fails with "no matches found"; on that error, quote and re-run once.
  `${PIPESTATUS[0]}` prints empty; use `cmd > /tmp/out.txt 2>&1; echo "exit=$?"; tail /tmp/out.txt`.
  A word starting with `=` (e.g. `echo ===`) aborts the command ("== not found"); use `echo ---`.
- Raw `pytest` has no time limit here (the suite once hung silently until a 900 s kill); always
  go through `run_tests.py` (full log in /tmp/run_tests.log). A hang is a bug, not a slow suite.
