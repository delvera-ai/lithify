# 20261023-171150-bug-retrying-skips-the-wait-stra

**Task:** Bug: retrying skips the wait strategy whenever the strategy object is falsy, so a callable wait strategy that is an empty container or defines `__bool__` returning False is never called. Only the "no wait" values (`None`, `0`, and `sum([])` over no strategies) should mean no wait; any other wait strategy must be called, in both the sync and async retry loops.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
