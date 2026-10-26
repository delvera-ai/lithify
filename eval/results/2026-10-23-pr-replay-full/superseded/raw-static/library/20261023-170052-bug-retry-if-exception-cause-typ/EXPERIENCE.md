# 20261023-170052-bug-retry-if-exception-cause-typ

**Task:** Bug: `retry_if_exception_cause_type` hangs forever (100% CPU, stop conditions never run) when an exception's `__cause__` chain is cyclic, e.g. `raise e from e`, or two exceptions whose causes point at each other. Walking the cause chain must terminate on cycles while still finding a matching cause type anywhere in a non-cyclic chain.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
