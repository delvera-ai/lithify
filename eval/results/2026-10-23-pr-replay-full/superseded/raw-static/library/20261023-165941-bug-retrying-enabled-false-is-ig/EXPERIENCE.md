# 20261023-165941-bug-retrying-enabled-false-is-ig

**Task:** Bug: `Retrying(enabled=False)` is ignored when used with the iterator pattern (`for attempt in retrying: with attempt: ...` and `async for attempt in AsyncRetrying(enabled=False)`): the full retry loop runs (several attempts) and a `RetryError` is raised. With `enabled=False` the body should run exactly once and any exception should propagate unchanged, matching the decorator path.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
