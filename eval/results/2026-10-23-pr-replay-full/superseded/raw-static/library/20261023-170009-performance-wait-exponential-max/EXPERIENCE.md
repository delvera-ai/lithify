# 20261023-170009-performance-wait-exponential-max

**Task:** Performance: `wait_exponential(max=...)` still computes `exp_base ** attempt_number` on every retry even after the result has reached `max`, so long-running polling gets more and more expensive (the integer grows without bound). Once the exponential would exceed `max`, return `max` without performing the power operation. (Stated requirement: the power must not be computed for attempts beyond the cap.) Results must otherwise be unchanged.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
