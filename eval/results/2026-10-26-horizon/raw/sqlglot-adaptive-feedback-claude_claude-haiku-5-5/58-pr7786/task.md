Exasol dialect: the second argument of `LISTAGG` is the separator, but sqlglot folds it into the value:

```python
sqlglot.parse_one("SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t", read="exasol")
# value parsed as CONCAT(x, ','), separator=None  (wrong)
```

Oracle, Snowflake, Trino and DuckDB parse the same SQL with `x` as the value and `','` as the separator. Exasol `LISTAGG` must do the same, and round-trip.
