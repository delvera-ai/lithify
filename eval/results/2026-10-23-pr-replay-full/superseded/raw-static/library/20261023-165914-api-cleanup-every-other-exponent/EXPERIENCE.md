# 20261023-165914-api-cleanup-every-other-exponent

**Task:** API cleanup: every other exponential wait class uses `multiplier`, but `wait_exponential_jitter` uses `initial`. Add a `multiplier` parameter (default 1) to `wait_exponential_jitter` with the same meaning, and deprecate `initial`: passing `initial` (by keyword or positionally) must still work but emit a `DeprecationWarning`, and passing both `initial` and `multiplier` must raise `ValueError`.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
