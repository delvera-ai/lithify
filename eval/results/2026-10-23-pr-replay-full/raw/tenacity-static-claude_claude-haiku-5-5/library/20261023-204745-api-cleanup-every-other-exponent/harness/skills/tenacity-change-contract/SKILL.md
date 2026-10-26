---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, adding, renaming or deprecating an argument of a wait/stop strategy (e.g. `wait_exponential_jitter`), emitting a `DeprecationWarning`, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or changing a strategy class) — i.e. any edit under tenacity/ that a user of the library could notice. Lists the files such a change must touch besides the code (reno note, test, user docs in doc/source/index.rst).
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
- INVARIANT (shape of a combined condition): `retry_any`/`retry_all` (sync and async) keep
  their members in `self.retries`, a tuple, evaluated left to right with short-circuit. Code
  that rewrites how operators build containers (e.g. flattening `a | b | c`) must keep that
  member order and must not mutate an operand's `retries`; build a new container.
- Absorbing a container's members is safe only in one direction. An ASYNC container may
  splice in a SYNC `retry_any`/`retry_all`'s members (it awaits every member through
  `wrap_to_async_func`, with the same short-circuit). A SYNC container must never splice in
  an async container's members (see the hang above). Mixed chains reach the async operators:
  `sync_a | sync_b | async_c` evaluates `(sync retry_any) | async_c`, which delegates to
  `async_retry_base.__ror__`. If that path checks only for the async container type, this
  chain stays nested. Handle it, or name it as left nested in the final message.
- Subclasses of `retry_any`/`retry_all` may override `__call__`. Splice members only from
  operands whose type is exactly the container (`type(x) is retry_any`), not `isinstance`.
- Guarding tests: `tests/test_asyncio.py::TestContextManager::test_retry_with_async_result_or`
  (and `_ror`, `_and`, `_rand`)
  mix sync and async strategies. Run them by node id after touching either operator set.
- Sync composition tests live in `tests/test_tenacity.py::TestRetryConditions`
  (`test_retry_or`, `test_retry_and`, `test_retry_or_with_plain_function`, …); there is no
  `TestRetry` class. Async composition tests are in `tests/test_asyncio.py::TestContextManager`.
- `stop.py` (`stop_any`/`stop_all` via `|`/`&`) and `wait.py` (`wait_combine` via `+`) have
  their own combinators. A task about retry composition does not cover them; leave them alone
  unless the task names them.
- Type aliases: sync `RetryBaseT` (`tenacity/retry.py`) and async `RetryBaseT`
  (`tenacity/asyncio/retry.py`). Inside `tenacity/asyncio/` the sync one is imported under
  `TYPE_CHECKING` as `SyncRetryBaseT` (see `tenacity/asyncio/__init__.py`). They are defined
  after `retry_base`, so annotations that use them in the class body are quoted strings.

## 1b2. Object state, pickling and copying (`Retrying`, strategies)
Verified in `tenacity/__init__.py`, `retry.py`, `before*.py`, `after.py`, `stop.py`, `nap.py`.
- `BaseRetrying.__init__` stores `self._local = threading.local()`. The `statistics` and
  `iter_state` properties lazily create `_local.statistics` / `_local.iter_state`, so any
  object rebuilt without going through `__init__` (unpickling, `copy.copy`) must get a fresh
  `_local` before either property is read. `iter_state.actions` holds per-run lambdas and
  closures from `_begin_iter`/`_post_stop_check_actions` (`exc_check`, `next_action`): it is
  per-run state, never something to serialise.
- Object-level hooks (`__getstate__`/`__setstate__`, `__copy__`) go on `BaseRetrying` once.
  `Retrying`, `AsyncRetrying` and `TornadoRetrying` add no instance state of their own beyond
  `sleep`, so they inherit them; no async copy needed.
- `BaseRetrying.copy()` (used by `wraps`' per-call copy and `retry_with`) rebuilds through
  `self.__class__(...)`, not the `copy` module, so it always starts with a fresh `_local` and
  empty statistics; pickle hooks don't change it. `copy.copy(retrying)` DOES go through
  `__getstate__`/`__setstate__` once they exist (before, the copy shared `_local`). State
  that change in the final message.
- INVARIANT for strategy classes (`retry.py`, `stop.py`, `wait.py`, `tenacity/asyncio/retry.py`):
  store constructor arguments as plain attributes and compute in `__call__`
  (`retry_if_exception_cause_type`, `stop_after_attempt`, `wait_fixed` do this). Never store a
  lambda or nested `def` built in `__init__`: it cannot be pickled
  (`Can't get local object '<cls>.__init__.<locals>.<lambda>'`). If an existing class must keep
  a `predicate` attribute (`retry_if_exception` subclasses), bind a module-level function with
  `functools.partial`. Check: `grep -nE "lambda|^ {8,}def " tenacity/retry.py tenacity/stop.py
  tenacity/wait.py tenacity/asyncio/retry.py` (quote it; zsh). It should return no hit inside
  an `__init__`. The `wait.py` hits at docstring examples (`wait_chained`, `http_error`,
  `http_get_request`) are not code. At the base commit the hits are
  `retry_if_exception_type`, `retry_if_not_exception_type`, `retry_unless_exception_type`,
  `retry_if_exception_message` (`message_fnc`/`match_fnc`) and
  `retry_if_not_exception_message`.
- Unpicklable by design, because they hold user or OS objects: the closures that
  `before_log`/`after_log`/`before_sleep_log` return (nested `log_it`), and the
  `threading.Event` in `stop_when_event_set` (`stop.py`) and `sleep_using_event` (`nap.py`). The same
  goes for user callables passed to `retry_if_result`, `retry_if_exception`, `wait_exception`,
  and `_utils.wrap_to_async_func`'s `inner`. A task about "built-in strategies" doesn't cover
  these. Name them as out of scope in the final message; don't redesign them.
- A module-level `@retry` function pickles by reference (`functools.wraps` copies
  `__qualname__`), so `Pool.map(fn, ...)` doesn't pickle the `Retrying`. Pickling is exercised
  only when `fn.retry`, a `Retrying` or a strategy crosses the process boundary. Test those
  objects directly with `pickle.loads(pickle.dumps(obj))`. Include a `Retrying` that has run
  (non-empty `statistics`) and check that the restored object still runs. An existing pickle
  test lives in `tests/test_tenacity.py::TestRetryException::test_retry_error_is_pickleable`.

## 1b3. Arguments of a wait/stop strategy; renaming or deprecating one
Verified in `tenacity/wait.py`, `tests/test_tenacity.py`, `pyproject.toml`, `reno.yaml`.
- Every constructor argument is stored as a same-named public attribute
  (`wait_exponential.multiplier`, `wait_exponential_jitter.initial`, `.max`, `.min`, ...).
  Renaming the argument and dropping the old `self.<old>` removes public API: user code
  reading `strategy.<old>` gets `AttributeError`. CONTRACT for a rename/deprecation: keep
  the old attribute readable (e.g. a read-only `@property` returning the new attribute),
  or name the removal under "breaking" in the final message and reno note. A read-only
  property makes `strategy.<old> = x` raise `AttributeError`: say so in the final message.
- Strategy arguments are positional-or-keyword, and existing tests call them positionally
  (`wait_exponential_jitter(10, 5)` in `TestWaitConditions`). A new argument goes LAST; a
  deprecated one keeps its position so old positional calls keep their meaning and warn.
- "Same meaning as" another class: `wait_exponential.__call__` computes
  `multiplier * exp_base ** (attempt_number - 1)` and clamps with
  `max(max(0, self.min), min(result, self.max))`; reuse those exact forms.
- Deprecation warnings: tenacity has no deprecation helper. The only `warnings.warn` in the
  package is in `retry()` (`tenacity/__init__.py`, `stacklevel=2`); `wait.py` does not import
  `warnings`. Use `warnings.warn(..., DeprecationWarning, stacklevel=2)` from `__init__` so
  the warning points at the caller.
- pytest config is `filterwarnings = ["once::DeprecationWarning"]` (`pyproject.toml`): warnings
  are shown once, never raised as errors, so existing tests that still pass the deprecated
  argument keep passing and only add to the "warnings" count. Do not edit those tests. Assert
  a warning with `self.assertWarns(DeprecationWarning)` or `pytest.warns` (both reset the
  filter). A bare `warnings.catch_warnings(record=True)` without `simplefilter("always")` can
  record nothing under "once".
- "Passing both old and new raises": with a real default (`multiplier: float = 1`) an explicit
  `multiplier=1` is indistinguishable from omission. Default both to `None` and resolve to the
  documented default after the conflict check; state the visible signature in the final message.
- Reno: `reno.yaml` defines no custom sections, so reno's default `deprecations:` section is
  valid (no note uses it yet). A deprecation note has `features:` for the new argument and
  `deprecations:` for the old one.
- Docs: `doc/source/index.rst` has no `wait_exponential_jitter(...)` example. Its wait section
  defines `def wait_exponential_jitter():` (decorated with `wait_random_exponential`) inside a
  `.. testcode::` block; the doctest namespace is shared (`testsetup` does `from tenacity import *`),
  so any example of the class placed AFTER that block calls the function instead and fails.
  Put a new example above that block.

## 1c. CONTRACT: a new keyword on `Retrying`/`AsyncRetrying`/`@retry`
A constructor option is stored on `BaseRetrying` and must appear in every place below.
Check each with `grep -n "<existing kwarg, e.g. retry_error_callback>" tenacity/*.py tenacity/asyncio/__init__.py`;
every hit list must gain the new name.
- `BaseRetrying.__init__` (param + `self.<attr>`) and `BaseRetrying.copy()` (param typed
  `<T> | object = _unset`, passed as `_first_set(<new>, self.<attr>)`). `copy()` is what
  `wraps`' per-call copy and `fn.retry_with(...)` use, so an option missing there is
  silently dropped by `retry_with`.
- `AsyncRetrying.__init__` (`tenacity/asyncio/__init__.py`) re-lists every parameter
  explicitly and forwards to `super().__init__`: add it there too. `TornadoRetrying.__init__`
  forwards `**kwargs`, so it needs no edit.
- `retry()` in `tenacity/__init__.py`: two keyword `@t.overload`s (the async one with
  `sleep: Awaitable` and `= ...` defaults, the sync one with real defaults). The
  implementation forwards `**dkw` unchanged, so only the overloads need the new param.
- A run-time option is honoured on EVERY entry point that starts a run, each of which
  calls `self.begin()` itself: `Retrying.__call__`, `BaseRetrying.__iter__`
  (`for attempt in Retrying(...)`), `AsyncRetrying.__call__`, `AsyncRetrying.__aiter__`
  (`async for`), `TornadoRetrying.__call__` (`tenacity/tornadoweb.py`). Handle each one, or
  name the ones left out in the final message and the docs.
- `AsyncRetrying.__call__` can be handed a SYNC `fn`: `@retry(sleep=<async fn>)` picks
  `AsyncRetrying` for a plain function (see `TestSyncFunctionWithAsyncSleep`). A direct-call
  path must branch on `_utils.is_coroutine_callable(fn)` (as the loop does) or go through
  `_utils.wrap_to_async_func(fn)`; never a bare `await fn(...)`.
- Tests: one per changed entry point, in the file that owns it: sync/`retry_with` →
  `tests/test_tenacity.py`; async → `tests/test_asyncio.py` (`@asynctest`);
  tornado → `tests/test_tornado.py` (`testing.AsyncTestCase` + `@testing.gen_test`, functions
  decorated `@retry` over `@gen.coroutine`). Editing `tornadoweb.py` without a
  `test_tornado.py` test leaves that path unexecuted.

## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it.
- File name: `<short-kebab-slug>-<16 hex chars>.yaml` (what `reno new <slug>` produces; the
  repo exposes it as `tox -e reno -- new <slug>`). Any unique hex suffix is acceptable.
- Content: a YAML doc starting with `---`, one section key, a list of entries. Bug fixes use
  `fixes:`; new API uses `features:`; dropped support uses `upgrade:`; changes that keep
  behaviour (typing, packaging, `__all__`, internal structure) use `other:` (11 notes in the
  repo use it). House style:
  ```yaml
  ---
  fixes:
    - |
      One or two sentences describing the user-visible fix.
  ```
- Rendered by `doc/source/changelog.rst` (`.. release-notes::`), so it must be valid YAML.

## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
Feature commits that add API or a new way to use it also edit `doc/source/index.rst`, next
to the example of the existing form (e.g. #222 async iterator, #369, #423
`stop_before_delay`, #463 trio). Bug fixes that change no documented usage don't need this.
- `README.rst` is a symlink to `doc/source/index.rst`. Edit `index.rst` only.
- Find the section with `grep -n "<existing usage, e.g. 'with attempt:'>" doc/source/index.rst`,
  not just the class name. Usage sections often don't name the class (the "Retrying code
  block" section shows `with attempt:` and never says `AttemptManager`).
- Examples are `.. testcode::` blocks, run by `sphinx-build -W -b doctest` (`poe docs`,
  `pyproject.toml [tool.poe.tasks]`). They must be valid, runnable Python. Async examples
  only define `async def function(): ...` and never run it. Copy that shape.
- `doc/source/api.rst` uses `autoclass`/`automodule`, so docstrings there update by
  themselves.

## 3. A regression test in the matching test file
- `tenacity/_utils.py` → `tests/test_utils.py`; callbacks/strategies/core → `tests/test_tenacity.py`
  (`tests/test_after.py` for `after_log`); async → `tests/test_asyncio.py`;
  `tenacity/tornadoweb.py` → `tests/test_tornado.py`.
- mypy runs `strict = true` over BOTH `tenacity` and `tests` (`pyproject.toml [tool.mypy]`), so
  every new test function needs full parameter and `-> None` annotations.
- ruff (`line-length = 88`, `target-version = "py310"`) checks and format-checks the whole repo,
  tests included (`tox -e pep8`).
- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
  annotated (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
