# 20261023-170038-bug-wait-exponential-can-raise-v

**Task:** Bug: `wait_exponential` can raise `ValueError: math domain error` instead of returning a wait time when `multiplier` and `max` are finite and positive but `max / multiplier` underflows to 0.0 (e.g. `wait_exponential(multiplier=1e300, max=1e-100)`), or when `multiplier` is not finite. It should return the capped wait instead; results for ordinary values must not change.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
