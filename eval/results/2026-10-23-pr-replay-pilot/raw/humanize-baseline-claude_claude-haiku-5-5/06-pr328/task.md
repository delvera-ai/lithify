Bug: `humanize.metric()` can output a four-digit mantissa with a prefix that is too small, contradicting its docstring (the prefix is chosen so that non-significant zero digits are not needed):

```python
>>> metric(999.9, "V")
'1000 V'      # expected '1.00 kV'
>>> metric(999999, "V")
'1000 kV'     # expected '1.00 MV'
>>> metric(0.0009999, "V")
'1000 μV'     # expected '1.00 mV'
```

When rounding reaches 1000, the result should move to the next SI prefix. Values already at the largest prefix should be unchanged.
