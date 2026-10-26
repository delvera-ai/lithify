- The shell is zsh on macOS (BSD userland): an unquoted glob that matches nothing is an error
  (`no matches found`), so quote globs (`grep -rn name --include='*.py' .`); `${PIPESTATUS[0]}` is
  empty (zsh uses `$pipestatus[1]`), and GNU-only flags such as `cat -A` fail (use `cat -vet`).
  To read a command's exit code, don't pipe it: `cmd; echo "exit=$?"`.
- For ad-hoc checks that import the package (`-c "from tenacity... import ..."`), run the project
  interpreter from `memory.md` from the repo root, without `-I`: `-I` drops the current directory
  from the import path, so the import fails with `ModuleNotFoundError: No module named 'tenacity'`.
