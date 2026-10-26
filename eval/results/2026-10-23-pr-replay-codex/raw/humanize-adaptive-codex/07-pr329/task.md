Bug: `humanize.naturalsize()` can show the base value with the smaller suffix when rounding pushes a value up to the next unit:

```python
>>> naturalsize(999999)
'1000.0 kB'      # expected '1.0 MB'
>>> naturalsize(1024 ** 2 - 1, binary=True)
'1024.0 KiB'     # expected '1.0 MiB'
```

This happens at every decimal, binary and GNU boundary. After rounding, a value that reaches the base should be shown in the next unit. Values already at the largest suffix (QB/QiB) are unaffected.
