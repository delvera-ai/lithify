# 20261023-165846-bug-retrying-objects-and-the-bui

**Task:** Bug: `Retrying` objects and the built-in retry strategies cannot be pickled, so `@retry`-decorated functions cannot be used with `multiprocessing` (e.g. `Pool.map`). Make `Retrying` instances (including ones that have already been used and have statistics) and the retry strategy classes picklable with the standard `pickle` module, restoring an equivalent working object.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
