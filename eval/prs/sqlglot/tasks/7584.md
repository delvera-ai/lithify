BigQuery → DuckDB: a parameterised `BIGNUMERIC` / `BIGDECIMAL` type is generated with both the default mapping parameters and the explicit ones concatenated:

```
DECLARE x DECIMAL(38, 5)(76, 38)
```

When the user supplies parameters, generate them instead of the default ones (and use the default mapping only when none are given).
