---
name: tenacity-change-contract
description: Load before finishing any change that alters tenacity's runtime behaviour or public API (bug fix, new feature, changed default, changed log/error text, retry-loop or `statistics` behaviour, `|`/`&`/`+` composition of retry/stop/wait strategies or their type annotations, a new constructor parameter on `Retrying`/`AsyncRetrying`/`@retry`) — lists the files such a change must touch in this repo (release note, regression test), the conventions they follow, how to prove the test fails on the old code, and the sync/async invariants of the retry loop.
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

## CONTRACT: new constructor parameter on `Retrying` / `AsyncRetrying` / `@retry`

Precedent: `name` (#597, `git show 70083b8`). The parameter must appear in every place below;
confirm with `grep -n "<param>" tenacity/__init__.py tenacity/asyncio/__init__.py`.

1. `BaseRetrying.__init__` (`tenacity/__init__.py`): parameter + stored attribute.
2. `BaseRetrying.copy()`: `<param>: <type> | object = _unset` and
   `<param>=_first_set(<param>, self.<attr>)`. Not optional: `wraps()` runs every decorated
   call on `self.copy()` and `retry_with` is `self.copy(*args, **kwargs).wraps(f)`, so a value
   missing from `copy()` is silently dropped by `@retry(...)` and `retry_with(...)`.
3. `AsyncRetrying.__init__` (`tenacity/asyncio/__init__.py`) re-declares every parameter and
   forwards each one to `super().__init__` by keyword: add it in both places.
   `TornadoRetrying.__init__` takes `**kwargs`, so it needs nothing.
4. Both keyword overloads of `retry()` in `tenacity/__init__.py`: the async-`sleep` one
   (defaults written `= ...`, returns `_AsyncRetryDecorator`) and the sync one (real defaults).
   mypy strict covers `tests/`, so a test calling `@retry(<param>=...)` is a type error without
   them. `name` is missing from these overloads today; don't copy that gap.
5. `BaseRetrying.__repr__` lists the configuration (`name=` was added by #597); add the new
   field there too.
6. If the parameter changes how calls run, it must reach every execution path. Each has its own
   loop: `Retrying.__call__`, `BaseRetrying.__iter__` (`for attempt in Retrying(...)`),
   `AsyncRetrying.__call__`, `AsyncRetrying.__aiter__`/`__anext__`, and
   `TornadoRetrying.__call__` (`tenacity/tornadoweb.py`; `retry()` picks it for tornado
   coroutines). All of them drive `self.iter()` → `BaseRetrying._begin_iter`, which is shared,
   so a change there reaches every iterator path. A short-circuit in one `__call__` does not.
   Test each path you change: `tests/test_tenacity.py`, `tests/test_asyncio.py`,
   `tests/test_tornado.py` (tornado is installed in the project interpreter; trio is not).
7. Release note under `features:`; for the fail-on-base result to expect, see DONE step 1.

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
- **Strategy composition lives on the base classes, and sync/async differ.**
  - `retry_base` (`tenacity/retry.py`) defines `__and__`/`__or__` by delegating to
    `other.__rand__(self)` / `other.__ror__(self)`; that is how `sync | async` ends up as the
    async `retry_any`. Anything without those methods (a plain function) breaks the
    delegation, so a fix has to handle non-`retry_base` operands. Don't drop the delegation.
  - `async_retry_base` (`tenacity/asyncio/retry.py`) overrides all four operators to build
    `tenacity.asyncio.retry_any`/`retry_all` directly. Those wrap each member with
    `_utils.wrap_to_async_func`. Sync `retry_any`/`retry_all` call members directly.
    `stop_base` (`stop.py`) and `wait_base` (`wait.py`, `__add__`/`__radd__`) build
    `stop_any`/`stop_all`/`wait_combine` directly.
  - A composition bug can be confined to one base class. Before writing the async test,
    find which operand (sync `retry_base` or `async_retry_base`) takes the broken path. A
    test built only from `tasyncio.*` strategies never reaches `retry_base.__or__`.
  - Type aliases already exist: `RetryBaseT` (`retry.py`, `retry_base | Callable[[RetryCallState], bool]`),
    async `RetryBaseT` (`asyncio/retry.py`), `StopBaseT`, `WaitBaseT`. When widening an
    annotation to accept plain callables, use these aliases rather than a new
    `Callable[..., Any]`. `asyncio/retry.py` shadows the name `RetryBaseT`, so
    `asyncio/__init__.py` imports the sync one as `SyncRetryBaseT`.
  - Tests: sync composition in `tests/test_tenacity.py` (`TestRetryConditions.test_retry_or`/
    `test_retry_and`, `TestStopConditions`, `TestWaitConditions`). Mixed sync/async
    composition run through `AsyncRetrying` in `tests/test_asyncio.py` (`TestContextManager`,
    around the `retry_if_result(...) | tasyncio.retry_if_exception(...)` tests).
- **`with attempt:` swallows exceptions** (`AttemptManager.__exit__` records the exception as
  the attempt's outcome). A `KeyError` raised inside the block becomes a failed, retried
  attempt, not an error reaching the test: record values inside the block and assert after
  the loop, or read them from a `before=` hook to see the raw error.

## DONE means (run in this order, read each result)

1. **New tests fail on the old code** — one read-only call, from the repo root, with the
   project interpreter from `memory.md`:
   `<project-python> .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py <new test node ids>; echo "exit=$?"`
   Don't pipe it through `tail`: it already prints only the last 40 lines, and a pipe hides
   its exit code. Exit 0 = fails on HEAD (read the printed failure and check it is the bug; quote it in the
   final message). Exit 1 = test passes on HEAD: rework the test, rerun once. Exit 2 = the
   check could not run: do not improvise a stash/revert round-trip; say in the final message
   that fail-on-base was not verified.
   For a **new parameter or name**, exit 0 with `TypeError: ... unexpected keyword argument` /
   `ImportError` on HEAD is expected, but it only shows the name is new. It does not show the
   behaviour is right. So each behaviour test must also prove it can tell the cases apart: in
   the same test, run the scenario with the parameter's default value and assert the result
   differs (e.g. it retries). Then a fix that ignored the new parameter would fail the test.
2. **Full suite last**, once, after the final edit (command in `memory.md`).
3. **`git status --short`** — confirms the untracked reno note is present and nothing else
   stray is left.
