- The host is macOS: `sed -i` is BSD sed and fails with GNU syntax (`sed -i 's/…/'` → "undefined
  label"). Make file edits with the Edit tool, not `sed -i`.
- Do not chain an edit and the test run in one shell command; if the edit step fails, the test
  output misleads. Edit, then run the checks as a separate step and read the result.
