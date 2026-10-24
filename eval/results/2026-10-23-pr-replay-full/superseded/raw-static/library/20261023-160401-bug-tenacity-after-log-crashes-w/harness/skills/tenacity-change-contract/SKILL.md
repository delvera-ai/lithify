---
name: tenacity-change-contract
description: Load before finishing any change that alters tenacity's runtime behaviour or public API (bug fix, new feature, changed default, changed log/error text) — lists the files such a change must touch in this repo (release note, regression test) and the conventions they follow.
---

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex chars>.yaml`
   (e.g. `fix-local-context-overwrite-94190ba06a481631.yaml`). Content is a YAML doc starting
   with `---`, with a `fixes:` list for bug fixes or `features:` for additions, written for
   users, with inline code in RST double backticks:
   ```yaml
   ---
   fixes:
     - |
       Describe the user-visible behaviour that was wrong and what it is now.
   ```
   Do not edit `doc/source/changelog.rst`; it is generated from these notes (`reno.yaml`).
2. **Regression test.** Tests live in `tests/`, one module per area:
   `tests/test_utils.py` for `tenacity/_utils.py`, `tests/test_after.py` for `after_log`,
   core `Retrying`/`retry` behaviour in `tests/test_tenacity.py`, asyncio in
   `tests/test_asyncio.py`, issue-specific
   repros as `tests/test_issue_<N>.py`. Add a test that fails on the old code. Follow the
   existing style in that file (plain `def test_...() -> None:` functions with bare `assert` in
   `test_utils.py`).
3. **Confirm they agree:** the note describes the same behaviour the test pins down; the diff
   touches `tenacity/…`, `tests/…` and `releasenotes/notes/…`.

Pure refactors, CI, typing-only, or docs-only changes may skip the test; a user-visible change
should still get a note.

## INVARIANTS that new code and tests must satisfy

- **mypy is strict over `tenacity` and `tests`** (`pyproject.toml [tool.mypy] strict = true,
  files = ["tenacity", "tests"]`). Every new function, including test functions, needs full
  annotations (`-> None` on tests).
- **ruff** check + format (`tox -e pep8`), target py310 (`pyproject.toml`). Use py310+
  syntax; no compatibility shims for older Pythons. `line-length = 88` is only the
  formatter's target: `[tool.ruff.lint] ignore` includes `E501`, and existing log-message
  f-string lines in `tenacity/after.py`, `before.py`, `before_sleep.py` already run past 88
  (up to 114 in `__init__.py`). Don't restructure code just to get under 88 columns.
  `SIM108` is ignored too, so an `if/else` assignment and a ternary are both acceptable.
- **mypy and ruff are not installed in the project's check interpreter** (`python -m mypy` /
  `python -m ruff` → `No module named ...`). Don't spend steps retrying them; write
  code that satisfies the rules above by inspection, and say in the final message that
  they were not run.
- **Shared helpers in `tenacity/_utils.py` feed user-visible text.** `to_ordinal` /
  `find_ordinal` build the "Nth time calling it" messages in `tenacity/before.py` and
  `tenacity/after.py`, and `tests/test_after.py` computes its expected strings through
  `_utils.to_ordinal`. Fix such helpers in `_utils.py` itself (not at call sites), and test the
  helper directly in `tests/test_utils.py` — the logging tests will not catch a wrong helper
  because they call the same helper.
