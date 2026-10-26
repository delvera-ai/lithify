# 20261023-171102-refactor-mark-every-method-that

**Task:** Refactor: mark every method that overrides a base-class method (on `retry_base`, `wait_base`, `stop_base`, `BaseRetrying` and their subclasses, and in the test helpers) with an `@override` decorator, so renaming a base method can no longer silently orphan subclass implementations. tenacity has no runtime dependencies and supports Python 3.10+, so provide `override` from `tenacity._utils`: use `typing.override` where available and a small PEP 698-compatible fallback (which sets `__override__ = Tr

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
