# 20261023-165537-improvement-composing-several-re

**Task:** Improvement: composing several retry conditions with `|` or `&` currently nests containers, e.g. `a | b | c` becomes `retry_any(retry_any(a, b), c)`. Chained operators should flatten into a single container instead: `a | b | c` must produce one `retry_any` whose `retries` holds `a`, `b` and `c`, and likewise `&` must produce one `retry_all`; the same for the async retry strategies. Behaviour of the combined condition must not change. (Stated requirement: the flattened object exposes its members 

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
