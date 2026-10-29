Trino → Snowflake (and other dialects): `FROM_ISO8601_TIMESTAMP`, a Presto/Trino function that parses an ISO 8601 string into a timestamp with time zone, is only transpiled for DuckDB; every other dialect gets the literal `FROM_ISO8601_TIMESTAMP(...)`, which is invalid there:

```python
sqlglot.parse_one("select from_iso8601_timestamp('2022-07-01T07:00:00+00:00')", "trino").sql("snowflake")
# "SELECT FROM_ISO8601_TIMESTAMP('2022-07-01T07:00:00+00:00')"
```

Transpile it for the other dialects using their equivalent timezone-aware timestamp conversion (for Snowflake, `TO_TIMESTAMP`-family semantics).
