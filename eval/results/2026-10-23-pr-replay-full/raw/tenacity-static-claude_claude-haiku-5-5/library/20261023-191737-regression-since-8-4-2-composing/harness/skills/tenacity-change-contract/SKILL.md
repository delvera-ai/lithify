---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version) — i.e. any edit under tenacity/ that a user of the library could notice. Lists the files such a change must touch besides the code.
---

# What a behaviour change in tenacity must touch

Verified against the repository history and config. Check each item before finishing.

## 1. Code goes in the module that owns the concern
- `tenacity/_utils.py` — shared helpers (`find_ordinal`/`to_ordinal`, `get_callback_name`,
  `LoggerProtocol`, `MAX_WAIT`). The logging callbacks in `tenacity/before.py`,
  `tenacity/after.py`, `tenacity/before_sleep.py` call these helpers; fix the helper, not the
  callers.
- Strategies live in `tenacity/wait.py`, `tenacity/stop.py`, `tenacity/retry.py`; the
  `Retrying`/`retry()` core and its type overloads in `tenacity/__init__.py`; async in
  `tenacity/asyncio/`.

## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
- `BaseRetrying` owns the loop once: `begin()` (start of every run), `_begin_iter`,
  `_post_retry_check_actions`, `_post_stop_check_actions` are shared by sync, async and
  tornado (`tenacity/tornadoweb.py`); `AsyncRetrying` and `TornadoRetrying` call
  `self.begin()` and do not override it. A fix in one of these shared methods needs no async
  copy — say so rather than editing `tenacity/asyncio/`.
- `AsyncRetrying` (`tenacity/asyncio/__init__.py`) re-implements `_run_retry`, `_run_wait`,
  `_run_stop`, `iter`, `__call__`, `__aiter__`/`__anext__` and `wraps` as async copies. A
  change to the sync version of any of these must be mirrored there (check with
  `grep -n "<changed line>" tenacity/__init__.py tenacity/asyncio/__init__.py`).
- `statistics` is per-thread (`self._local`). Per-run keys are seeded in `begin()` after
  `statistics.clear()`; later updates happen in `_run_stop` (`delay_since_first_attempt`)
  and `next_action` (`idle_for`, `attempt_number`). A key that must exist "from the start"
  belongs in `begin()`. Decorated functions expose the running copy's dict as
  `fn.statistics` (`wraps` does `wrapped_f.statistics = copy.statistics`), not
  `fn.retry.statistics`.
- Statistics tests live in `TestStatistics` (`tests/test_tenacity.py`). To observe a value
  during an attempt, read `retry_state.retry_object.statistics[...]` from a `before`/`after`
  callback.
- An exception raised inside a callback (`before`, `after`, `stop`, `wait`, …) is not
  retried or wrapped: it propagates raw out of the call. Only exhausted retries raise
  `RetryError`. So a test that lets retries exhaust must use
  `contextlib.suppress(RetryError)` (or `assertRaises(RetryError)`), never
  `suppress(Exception)`, which hides the very `KeyError`/`TypeError` under test.

## 1b. Strategy composition (`|`, `&`) and sync/async mixing
- Sync combinators (`tenacity/retry.py` `retry_any`/`retry_all`) call members directly. Async
  ones (`tenacity/asyncio/retry.py`) await each member through `_utils.wrap_to_async_func`,
  so they accept sync and async members alike. A sync combinator must never hold an async
  member: the call returns a coroutine, which is truthy. Retry then never stops, and the
  suite hangs instead of failing.
- `retry_base.__or__`/`__and__` call `other.__ror__(self)`/`other.__rand__(self)` on purpose.
  For `sync_strategy | async_strategy` the right operand is not a subclass of the left one, so
  Python calls the left `__or__`. Delegating is the only way `async_retry_base.__ror__` builds
  the async combinator. When extending these operators, keep that delegation for
  `isinstance(other, retry_base)` and build `retry_any(self, other)`/`retry_all(self, other)`
  directly only for anything else (plain callables). A plain callable on the LEFT already
  reaches `retry_base.__ror__`/`__rand__`.
- Guarding tests: `tests/test_asyncio.py::TestContextManager::test_retry_with_async_result_or`
  (and `_ror`, `_and`, `_rand`)
  mix sync and async strategies. Run them by node id after touching either operator set.
- Type aliases: sync `RetryBaseT` (`tenacity/retry.py`) and async `RetryBaseT`
  (`tenacity/asyncio/retry.py`). Inside `tenacity/asyncio/` the sync one is imported under
  `TYPE_CHECKING` as `SyncRetryBaseT` (see `tenacity/asyncio/__init__.py`). They are defined
  after `retry_base`, so annotations that use them in the class body are quoted strings.

## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it.
- File name: `<short-kebab-slug>-<16 hex chars>.yaml` (what `reno new <slug>` produces; the
  repo exposes it as `tox -e reno -- new <slug>`). Any unique hex suffix is acceptable.
- Content: a YAML doc starting with `---`, one section key, a list of entries. Bug fixes use
  `fixes:`; new API uses `features:`; dropped support uses `upgrade:`. House style:
  ```yaml
  ---
  fixes:
    - |
      One or two sentences describing the user-visible fix.
  ```
- Rendered by `doc/source/changelog.rst` (`.. release-notes::`), so it must be valid YAML.

## 3. A regression test in the matching test file
- `tenacity/_utils.py` → `tests/test_utils.py`; callbacks/strategies/core → `tests/test_tenacity.py`
  (`tests/test_after.py` for `after_log`); async → `tests/test_asyncio.py`.
- mypy runs `strict = true` over BOTH `tenacity` and `tests` (`pyproject.toml [tool.mypy]`), so
  every new test function needs full parameter and `-> None` annotations.
- ruff (`line-length = 88`, `target-version = "py310"`) checks and format-checks the whole repo,
  tests included (`tox -e pep8`).
- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape and the changed lines' length/spacing (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
