# 20261023-165927-bug-when-tryagain-is-raised-from

**Task:** Bug: when `TryAgain` is raised from inside an `except` block to drive a manual retry (e.g. with `retry=retry_never`) and `reraise=True`, the error raised after the attempts are exhausted is the opaque `TryAgain` sentinel instead of the underlying exception that caused the retry:

```python
def call():
    try:
        raise ValueError("the real error")
    except ValueError:
        raise tenacity.TryAgain

Retrying(stop=stop_after_attempt(2), retry=retry_never, reraise=True)(call)
# raises tena

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
