- The project venv (python in memory.md) runs pytest but has no pip, ruff, mypy or PyYAML, and
  `uv`/`uvx` are not on PATH. Don't probe for them; `.lithify/harness/scripts/check_changed.py`
  builds the one throwaway `/tmp` venv that has them.
- The shell is zsh: quote globs (`--include='*.py'`), or the command fails with "no matches found".
- Run one test by node id: `<project python> -m pytest -q -p no:cacheprovider tests/test_x.py::Class::test_name`.
