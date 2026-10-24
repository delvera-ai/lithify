---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, the `enabled` switch, which exception escapes on give-up (`TryAgain`, `reraise=True`, `RetryError.reraise()`, `retry_error_cls`/`retry_error_callback`), adding, renaming or deprecating an argument of a wait/stop strategy (e.g. `wait_exponential_jitter`), emitting a `DeprecationWarning`, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or changing a strategy class, a performance/efficiency fix or rewrite of a strategy's arithmetic where results must stay the same (e.g. `wait_exponential` `exp_base ** n` past `max`)) — i.e. any edit under tenacity/ that a user of the library could notice, including speed. Lists the files such a change must touch besides the code (reno note, test, user docs in doc/source/index.rst).
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
  `fn.statistics` (base commit: `wraps` does `wrapped_f.statistics = copy.statistics`; see §1a1), not
  `fn.retry.statistics`.
- Statistics tests live in `TestStatistics` (`tests/test_tenacity.py`). To observe a value
  during an attempt, read `retry_state.retry_object.statistics[...]` from a `before`/`after`
  callback.
- An exception raised inside a callback (`before`, `after`, `stop`, `wait`, …) is not
  retried or wrapped: it propagates raw out of the call. Only exhausted retries raise
  `RetryError`. So a test that lets retries exhaust must use
  `contextlib.suppress(RetryError)` (or `assertRaises(RetryError)`), never
  `suppress(Exception)`, which hides the very `KeyError`/`TypeError` under test.

## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
Verified in `tenacity/__init__.py` (`BaseRetrying.wraps`, `_RetryDecorated`) and
`tenacity/asyncio/__init__.py` (`AsyncRetrying.wraps`). Use when a task is about what these
attributes show, including through another decorator (`functools.wraps`) or `retry_with`.
- The attribute surface is the `_RetryDecorated` protocol (`retry`, `statistics: dict`,
  `retry_with`). Both `wraps` set all three once at decoration (`statistics = {}`). Sync
  `wrapped_f` and async `async_wrapped` are separate code; a change to one must be mirrored.
- At the base commit, each call does `copy = self.copy()` (comment: so calls of the same
  function "multiple times in the same stack" don't overwrite each other), then REBINDS
  `wrapped_f.statistics = copy.statistics` and points `self._local.statistics` at it
  (#614, so `fn.retry.statistics` matches). `copy()` always starts with a fresh `_local`, so
  each call gets a new dict.
- `functools.wraps` (`WRAPPER_UPDATES`) copies the inner function's `__dict__` into an outer
  wrapper ONCE, at decoration. An attribute the inner wrapper later rebinds is stale on the
  outer one. Only objects that stay the same and are mutated in place stay visible there.
  `fn.retry` (the original `Retrying`) and `fn.retry_with` are never rebound, so
  `mock.patch.object(outer.retry, ...)` already works.
- INVARIANTS a change here must keep, or name as changed in the final message and reno note:
  per-thread statistics (the `statistics` property docstring says each thread has its own
  view); per-call isolation (a recursive or concurrent call of the same function must not
  `begin()`/`clear()` a dict that another running call is updating); `fn.retry.statistics is
  fn.statistics` after a call (#614); `enabled=False` returns before `self.copy()`, so it runs no
  `begin()` and leaves `fn.statistics` as it was (`{}` if never run; tests only assert the
  attribute exists); `fn.retry_with(...)` returns a new wrapped
  function with its own `statistics`. Sharing one dict across calls breaks per-call isolation
  and the per-thread note. If the fix does that, the final message must say so as a behaviour
  change, not leave it as an open question.
- Tests: the decorated-attribute tests are `TestDecoratorWrapper::test_retry_function_attributes`
  in BOTH `tests/test_tenacity.py` and `tests/test_asyncio.py`. Put the sync and async
  regression tests in the matching `TestDecoratorWrapper` classes. `tests/test_asyncio.py`
  already does `from functools import wraps`; `tests/test_tenacity.py` doesn't import
  `functools`.

## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
Use this when a task is about which exception escapes once retries stop.
- `TryAgain` is detected in `_begin_iter`. It sets `iter_state.is_explicit_retry`, which
  skips the `retry` strategy, so it is retried even with `retry=retry_never`. The attempt's
  `Future` holds the `TryAgain` instance itself. Any exception it was raised for is reachable
  only through its `__context__`/`__cause__`.
- Giving up happens once, in `_post_stop_check_actions`. If `retry_error_callback` is set,
  its return value is the result. Otherwise `exc_check` builds `self.retry_error_cls(fut)`.
  With `reraise=True` it calls `retry_exc.reraise()`; without it, it runs
  `raise retry_exc from fut.exception()`. `AsyncRetrying` (`tenacity/asyncio/__init__.py`)
  and `TornadoRetrying` don't override `_begin_iter`, `_post_retry_check_actions` or
  `_post_stop_check_actions`. A fix in these methods or in `RetryError.reraise()` covers
  every entry point: `__call__`, `for attempt in` / `with attempt:` (`AttemptManager.__exit__`
  stores the exception on the outcome), `async for`, and tornado. Don't add an async copy.
  State this in the final message.
- `RetryError.reraise()` is public API. Users call it themselves on a caught `RetryError`
  (`TestReraiseExceptions::test_reraise_from_retry_error`), and `retry_error_cls` lets them
  subclass `RetryError`. A change there therefore also changes the non-`reraise=True` path
  for callers of `.reraise()`. Name that in the final message and the reno note.
- Behaviour that stays guarded: a bare `TryAgain` (no underlying error) with `reraise=True`
  still raises `TryAgain` (`TestRetryConditions::test_retry_try_again_forever_reraise`). A
  last attempt that did NOT fail makes `reraise()` raise the `RetryError` itself
  (`TestReraiseExceptions::test_reraise_timeout_from_retry_error`,
  `test_reraise_no_exception`).
- Exception chains: `raise X` inside an `except` sets `X.__context__`. `raise X from e` sets
  `__cause__` (and also `__context__` when inside an `except`). `raise X from None` sets
  `__suppress_context__ = True` but keeps `__context__`. The repo's existing chain walk
  (`retry_if_exception_cause_type`, `tenacity/retry.py`) follows `__cause__`. A fix that reads
  the chain must say in the final message which of these forms it handles.
- Tests: the `TryAgain` tests are in `tests/test_tenacity.py::TestRetryConditions`
  (`test_retry_try_again*`), and the `reraise` tests in `TestReraiseExceptions`. Async
  `reraise` is in `tests/test_asyncio.py::TestContextManager::test_reraise`.

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

## 1b4. Exponential wait arithmetic (`tenacity/wait.py`)
Verified in `tenacity/wait.py`, `tenacity/_utils.py`, `tests/test_tenacity.py`.
- Exponential classes and where the power `self.exp_base ** (attempt_number - 1)` lives:
  `wait_exponential.__call__`; `wait_random_exponential` has no power of its own (it calls
  `super().__call__` and draws `random.uniform(self.min, high)`), so a change to
  `wait_exponential` covers it; `wait_exponential_jitter.__call__` has its OWN copy (adds
  `jitter`, and its `except OverflowError` sets `result = self.max` then clamps). A change to
  the power/cap logic of one must name in the final message whether the other copy got it;
  change `wait_exponential_jitter` only if the task names it.
- `max` defaults to `_utils.MAX_WAIT` (`sys.maxsize / 2`, a float), so every
  `wait_exponential()` has a finite cap; a cap short-circuit runs for default instances too.
- `wait_exponential.__call__` already HAS a cap short-circuit (#654): guarded by
  `multiplier > 0`, `max > 0`, `exp_base > 1`, `math.isfinite(max)`, it returns the cap when
  `exponent > math.log(max / multiplier, exp_base)`. `math.log` raises `ValueError: math
  domain error` on a ratio of 0.0, which the guards don't exclude: `multiplier=inf` or
  `multiplier` so much larger than `max` that the division underflows. Ratio 0.0 means
  `multiplier > max`, i.e. the cap applies from attempt 1. Other ratios are safe: a subnormal
  ratio logs finitely, an overflowed ratio (`inf`) logs to `inf` and falls through, and a NaN
  `multiplier` fails `> 0` and falls through (result is `0`, no exception). Any edit to this
  guard keeps every input that reached `math.log` before on the same comparison, so ordinary
  results stay identical; test the edge inputs in `TestWaitConditions`, one test per trigger.
- "Results unchanged" means matching BOTH existing exits of `wait_exponential.__call__`:
  `except OverflowError: return self.max` returns `max` WITHOUT the `min` clamp, while the
  normal path returns `max(max(0, self.min), min(result, self.max))`. They differ only when
  `min > max`. `OverflowError` comes from a float power or from `multiplier * <huge int>`
  (int→float conversion); an int base with int multiplier never overflows. A new cap
  short-circuit that returns through a different exit than the old code took for the same
  inputs changes the result: keep the old exit or name the `min > max` difference in the
  final message and the reno note.
- Tests: wait strategies are tested in `tests/test_tenacity.py::TestWaitConditions`
  (there is no `TestTenacity` class), calling `Retrying(wait=...).wait(make_retry_state(n, 0))`;
  `make_retry_state(previous_attempt_number, delay_since_first_attempt)` is the module helper.

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
  name the ones left out in the final message and the docs. `wraps` is not a run entry
  point; it calls `copy()` then `copy(f, ...)` (`__call__`).
- `enabled` (base commit): checked only in `wraps` — sync `wrapped_f` and async
  `async_wrapped` (`tenacity/asyncio/__init__.py`) — as `if not self.enabled: return f(...)`
  BEFORE `self.copy()`. So the decorator's disabled path is a raw call: no `begin()`, no
  `before`/`after`/`before_sleep`/`retry_error_callback`, and `fn.statistics` stays the `{}`
  set at decoration. The five run entry points above do not check it. List which ones honour
  it with `grep -n "self.enabled" tenacity/*.py tenacity/asyncio/__init__.py`. Tests:
  `tests/test_tenacity.py::TestEnabled`, `tests/test_asyncio.py::TestAsyncEnabled`. A fix
  that claims to "match the decorator path" for another entry point must say in the final
  message whether that path still runs `begin()`/`before` (iterating starts with `iter()`,
  which runs `before`), since the decorator path runs neither.
- `AsyncRetrying.__call__` can be handed a SYNC `fn`: `@retry(sleep=<async fn>)` picks
  `AsyncRetrying` for a plain function (see `TestSyncFunctionWithAsyncSleep`). A direct-call
  path must branch on `_utils.is_coroutine_callable(fn)` (as the loop does) or go through
  `_utils.wrap_to_async_func(fn)`; never a bare `await fn(...)`.
- Tests: one per changed entry point, in the file that owns it: sync/`retry_with` →
  `tests/test_tenacity.py`; async → `tests/test_asyncio.py` (`@asynctest`);
  tornado → `tests/test_tornado.py` (`testing.AsyncTestCase` + `@testing.gen_test`, functions
  decorated `@retry` over `@gen.coroutine`). Editing `tornadoweb.py` without a
  `test_tornado.py` test leaves that path unexecuted.

## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
Verified in `tenacity/__init__.py` and `tenacity/asyncio/__init__.py`.
- One `AttemptManager` (`tenacity/__init__.py`) serves both forms: `__aexit__` just returns
  `self.__exit__(...)`, so a change in `__exit__` covers `async with`/`with` inside
  `async for` too. Don't add an async copy. `__exit__` stores the exception with
  `retry_state.set_exception(...)` and returns `True`, which SWALLOWS it; on success it
  stores `set_result(None)`. `self.retry_state.retry_object` is the running `BaseRetrying`.
- The loop is driven from outside: sync `BaseRetrying.__iter__` is a generator (`begin()`,
  one `RetryCallState(self, fn=None, ...)`, then `iter()` → yield `AttemptManager` on
  `DoAttempt`, `self.sleep` on `DoSleep`, `break` otherwise). Async splits it:
  `__aiter__` does `begin()` and stores `self._retry_state`; each `__anext__` calls
  `await self.iter(...)` and raises `StopAsyncIteration` when `do` is `None` or not
  `DoAttempt`/`DoSleep`. `AsyncRetrying.__iter__` raises `TypeError`. A change to when the
  loop stops must be made in BOTH `__iter__` and `__anext__`; they share no code.
- The outcome of attempt N is judged only when the loop asks for attempt N+1 (`iter()` →
  `_begin_iter` → `_post_retry_check_actions`). A non-retried exception escapes because that
  next `iter()` runs `rs.outcome.result()`, re-raising it from inside the iterator; giving up
  raises `RetryError` (or the `reraise`/`retry_error_callback` result) the same way. Guarding
  tests: `tests/test_tenacity.py::TestContextManager` (`test_context_manager_on_error`,
  `_retry_error`, `_reraise`) and `tests/test_asyncio.py::TestContextManager`. Run both
  classes by node id after touching `AttemptManager`, `__iter__` or `__anext__`.
- `_begin_iter`/`iter()` are shared with every `__call__` (they return the function's
  result), so a branch there changes the call path too; a branch in `AttemptManager`,
  `__iter__` or `__anext__` affects iteration only. State which you chose and why.
- Docs: the iterator form is the "Retrying code block" section of `doc/source/index.rst`
  (`grep -n "for attempt in" doc/source/index.rst`). The "Disabling Retries" section
  just above it describes only the decorated function; a change that makes `enabled=False`
  work for another usage form updates that section's sentence.

## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long run) is a
fix: use `fixes:`. The `wait.py` commits without a note are ruff/lint/typing-syntax refactors
(#571, #584, #616, #619) and docstring fixes (#372, #548).
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
  tests included (`tox -e pep8`). ruff format puts NO blank line between a decorator and its
  `def`, including a multi-line `@retry(...)` call whose last line is `)`. Separate a nested
  decorated def from the code above it with a blank line before the `@`, never after the `)`.
- Check items 2 and 3 with `<project python> .lithify/harness/scripts/check_changed.py`; it
  checks the reno note's shape, the changed lines' length/spacing and that new defs are fully
  annotated (ruff/mypy can't run here).

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
