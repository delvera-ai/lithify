- Old-vs-new output: to reproduce a bug on the unmodified code, or to show that a planned test
  input changes output, run `<memory.md python> .lithify/harness/scripts/compare_outputs.py
  'naturalsize(999999)' ...` (or `--file exprs.txt`) from the repo root. It evaluates each
  expression on HEAD (via `git archive` into a temp dir) and on the working tree, each in its own
  subprocess, and ends with `N expressions, C changed, S same`. Exit 2 = setup failure: read the
  message and fix the call; don't fall back to a hand-rolled check. Never `git show`/`cp` HEAD
  files over the working tree, `git stash`, or import both versions in one process (a shared
  `sys.modules` silently reports no change).
- Run Python with the interpreter from memory.md and `PYTHONPATH=src`; never pass `-I` (it
  ignores `PYTHONPATH`, so `import humanize` fails).
