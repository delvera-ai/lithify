Bug: when `TryAgain` is raised from inside an `except` block to drive a manual retry (e.g. with `retry=retry_never`) and `reraise=True`, the error raised after the attempts are exhausted is the opaque `TryAgain` sentinel instead of the underlying exception that caused the retry:

```python
def call():
    try:
        raise ValueError("the real error")
    except ValueError:
        raise tenacity.TryAgain

Retrying(stop=stop_after_attempt(2), retry=retry_never, reraise=True)(call)
# raises tenacity.TryAgain; expected the ValueError
```

With `reraise=True`, the underlying exception should be re-raised; this must work for sync and async retrying.
