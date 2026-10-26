# 20261023-171136-bug-retrying-enabled-false-fn-an

**Task:** Bug: `Retrying(enabled=False)(fn)` and `AsyncRetrying(enabled=False)(fn)` ignore `enabled=False` when called directly: they run the full retry loop and wrap the original exception in `RetryError`. With `enabled=False`, calling the retrying object with a function should call it exactly once and propagate its exception unchanged (awaiting coroutine functions for the async version), matching the decorator and iterator paths.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
