# 20261023-165956-bug-when-a-retry-decorated-funct

**Task:** Bug: when a `@retry`-decorated function is further wrapped by another decorator that uses `functools.wraps` (for example a timing decorator), `func.statistics` on the outer wrapper is an empty `{}` instead of the real runtime statistics. The statistics must stay visible through such wrappers, for sync and async functions (the outer wrapper's `statistics` should be the same object as the inner one's).

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
