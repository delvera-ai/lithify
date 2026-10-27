Trino → other dialects: `FROM_ISO8601_DATE` only exists in Presto/Trino, but sqlglot parses it as an unknown function and passes it through unchanged:

```python
p = sqlglot.parse_one("SELECT FROM_ISO8601_DATE('2020-05-11')", "trino")
for d in ["snowflake", "duckdb", "spark", "bigquery"]:
    print(d, p.sql(d))   # all emit FROM_ISO8601_DATE(...)
```

For other dialects it should be transpiled to a cast to `DATE` (and round-trip in Presto/Trino).
