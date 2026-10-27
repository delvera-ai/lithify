Doris and StarRocks dialects: both support the two-argument form of `DATE_ADD` / `DATE_SUB` without the `INTERVAL` keyword (the second argument is a number of days), but sqlglot cannot parse it:

```python
import sqlglot
sqlglot.parse("select date_add('2025-01-01', 1) from a", dialect="doris", error_level=sqlglot.ErrorLevel.IMMEDIATE)
# ParseError: INTERVAL expression expected but got '1'
```

Support the two-argument form for both dialects (parse and generate).
