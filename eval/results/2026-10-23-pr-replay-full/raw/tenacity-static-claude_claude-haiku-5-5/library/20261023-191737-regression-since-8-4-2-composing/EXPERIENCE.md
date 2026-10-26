# 20261023-191737-regression-since-8-4-2-composing

**Task:** Regression since 8.4.2: composing a `retry_base` instance with a plain function using `|` or `&` (e.g. `retry_if_exception_type(IOError) | my_predicate`, in either order) raises an exception instead of producing a `retry_any`/`retry_all`. Composition with plain callables worked in 8.3.0 and should work again for both sync and async retry strategies; type annotations should accept plain callables too.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
