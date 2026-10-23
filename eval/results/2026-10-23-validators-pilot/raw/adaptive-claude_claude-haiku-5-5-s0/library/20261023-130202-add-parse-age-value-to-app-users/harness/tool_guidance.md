- The shell is zsh on macOS. Quote globs (`grep -rn PAT --include='*.py' app tests`); an unquoted
  glob aborts with "no matches found". Scope searches to `app tests`, not `.`.
- `sed` is BSD sed: `sed -i 's/…/' f` fails ("undefined label"). Use the Edit tool for in-place
  edits. In a chained command, check each step's output; later results (e.g. test failures) may
  only reflect an earlier failed step.
