Bug: `humanize.metric()` can show one significant figure too many when rounding carries the mantissa up a power of ten:

```python
>>> metric(9999)
'10.00 k'    # 4 significant figures at the default precision=3; expected '10.0 k'
>>> metric(99999)
'100.0 k'    # expected '100 k'
>>> metric(9.99999)
'10.00'      # expected '10.0'
```

The output should always have `precision` significant digits, matching neighbours such as `metric(10000) == "10.0 k"`.
