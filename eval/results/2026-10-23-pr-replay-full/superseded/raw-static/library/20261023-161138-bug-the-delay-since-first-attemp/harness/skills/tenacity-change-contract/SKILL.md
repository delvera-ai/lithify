---
name: tenacity-change-contract
description: Load before finishing any change that alters tenacity's runtime behaviour or public API (bug fix, new feature, changed default, changed log/error text, retry-loop or `statistics` behaviour) — lists the files such a change must touch in this repo (release note, regression test), the conventions they follow, how to prove the test fails on the old code, and the sync/async invariants of the retry loop.
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
   repros as `tests/test_issue_<N>.py`. Add a test that fails on the old code — prove it with
   `fails_on_base.py` (DONE step 1), not by stashing or hand-reverting the fix. Follow the
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
- **Per-run `statistics` are owned by `BaseRetrying.begin()`** (`tenacity/__init__.py`): it
  clears the dict and initialises the keys every run starts with. `Retrying` and
  `AsyncRetrying` (`tenacity/asyncio/__init__.py`, incl. `__aiter__`) call it and do not
  override it, so a key that must exist from the start of a run is initialised there once.
  Later updates happen in `_run_stop` (`delay_since_first_attempt`) and the `next_action`
  closure (`idle_for`, `attempt_number`).
- **Sync and async retry loops are parallel implementations.** `AsyncRetrying` re-implements
  `_run_stop` / `iter` and the other action runners as async versions (e.g.
  `delay_since_first_attempt` is written in both `tenacity/__init__.py` and
  `tenacity/asyncio/__init__.py`). A change inside one of those methods must be mirrored in
  the other file; a change in `begin()` reaches both. Cover a loop/statistics fix with a sync
  test (`tests/test_tenacity.py`, e.g. `TestStatistics`) and an async one
  (`tests/test_asyncio.py`, e.g. `TestContextManager`).
- **`statistics` is thread-local** (`self._local`); the decorator exposes a per-call copy's
  dict as `wrapped_f.statistics` while `wrapped_f.retry.statistics` stays `{}`. The
  `test_retry_function_attributes` tests compare the whole `statistics` dict, so adding or
  removing a key is a change those tests pin down.
- **`with attempt:` swallows exceptions** (`AttemptManager.__exit__` records the exception as
  the attempt's outcome). A `KeyError` raised inside the block becomes a failed, retried
  attempt, not an error reaching the test: record values inside the block and assert after
  the loop, or read them from a `before=` hook to see the raw error.

## DONE means (run in this order, read each result)

1. **New tests fail on the old code** — one read-only call, from the repo root, with the
   project interpreter from `memory.md`:
   `<project-python> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>`
   Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.
