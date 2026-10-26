- The shell is zsh: an unquoted glob that matches nothing is an error (`no matches found`), not a
  literal. Quote glob arguments, e.g. `grep -rn name --include='*.py' .`.
- For ad-hoc checks that import the package (`-c "from tenacity... import ..."`), run the project
  interpreter from `memory.md` from the repo root, without `-I`: `-I` drops the current directory
  from the import path, so the import fails with `ModuleNotFoundError: No module named 'tenacity'`.
