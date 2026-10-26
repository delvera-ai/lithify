---
name: deprecate-parameter
description: Load when a task renames, replaces or deprecates a parameter/argument of a public function or class (e.g. "add X with the same meaning and deprecate Y", "Y must still work but warn", "passing both must raise"). Gives the call-form test matrix, including the no-warning cases, and the warning/attribute checks to run before finishing.
---

# Deprecating or renaming a parameter

Use this together with `tenacity-change-contract`. That skill's §1b3 has the repository facts
(pytest's `once::DeprecationWarning` filter, `warnings.warn` precedent and `stacklevel=2`,
`None` defaults for "both passed", keeping the old attribute, reno `deprecations:`, docs
placement). This skill covers the call forms a deprecation has to handle and how to prove
each one.

## 1. Before editing: list every call form
Write this matrix down. Each row is one test, run red against the unfixed code first
(system.md step 1):
| call | expected |
|---|---|
| new name by keyword | works, value used, **no** warning |
| no arguments (defaults) | works with the documented default, **no** warning |
| old name by keyword | works, same value, DeprecationWarning |
| old name positionally (if it had a position) | works, DeprecationWarning |
| old and new together, including new == its default value | the error the task names |

The two **no warning** rows are the ones that get skipped. Without them, an implementation
that warns on every call passes every other row. Assert them with
`warnings.catch_warnings()` + `warnings.simplefilter("error")` around the call. The project
filter is `once`, so a bare call can hide a repeat warning.
"Default (no args) emits no warning" already passes before the fix. That is fine: it is a
guard, not a red test. Say so in the final message.

## 2. Implementation checks
- Keep the old positional slot where it is, so old positional calls still mean the same.
  Add the new parameter where it cannot shift existing positions, or make it keyword-only.
- "Both passed" must be detectable even when the new value equals its default, so both
  parameters need a "not passed" default (`None`). State the signature you chose in the
  final message.
- `stacklevel` must point at the user's call. Check: in a `-c` script under
  `warnings.catch_warnings(record=True)` + `simplefilter("always")`, construct the object
  with the old name and print `w[0].filename`. It must be `<string>`, not a `tenacity/` path.
- Old attribute: if the class stored the old name (`self.<old>`), grep for readers
  (`grep -rn "\.<old>\b" tenacity tests doc`). Then keep it readable (e.g. a property that
  returns the new attribute) or name its removal in the final message as a compatibility
  break.

## 3. Old-name usages elsewhere
`grep -rn "<old>=" tenacity tests doc/source --include='*.py' --include='*.rst'` (quote the
globs; zsh).
- Library code calling the old name: switch it to the new name. Library code must not
  trigger its own deprecation warning.
- Docs (`doc/source/index.rst`), docstrings, and the formula or description text in the
  class docstring: use the new name.
- Existing tests that pass the old name: do not rewrite them. They now cover the deprecated
  path. After the full run, read the warnings summary and list each new warning, with its
  test node id, in the final message.

## 4. Done
- Every matrix row has a test, and each row that can be red was seen red, then green.
- The `stacklevel` filename check above was printed and read.
- The full suite (`run_tests.py`) and `check_changed.py` exit 0. The warnings summary was read
  and its new entries reported.
