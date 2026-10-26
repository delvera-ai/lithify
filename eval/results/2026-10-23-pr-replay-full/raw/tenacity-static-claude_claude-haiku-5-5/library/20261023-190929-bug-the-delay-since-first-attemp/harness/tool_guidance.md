- The project venv (python in memory.md) runs pytest but has no pip, ruff, mypy or PyYAML;
  `uv`/`uvx` are not on PATH, and a new `/tmp` venv dies in ensurepip (SIGABRT). Don't probe or
  build one; `.lithify/harness/scripts/check_changed.py` is the stdlib substitute.
- The shell is zsh: quote globs (`--include='*.py'`), or the command fails with "no matches found".
  `${PIPESTATUS[0]}` prints empty; use `cmd > /tmp/out.txt 2>&1; echo "exit=$?"; tail /tmp/out.txt`.
  A word starting with `=` (e.g. `echo ===`) aborts the command ("== not found"); use `echo ---`.
- Run one test by node id: `<project python> -m pytest -q -p no:cacheprovider tests/test_x.py::Class::test_name`.
