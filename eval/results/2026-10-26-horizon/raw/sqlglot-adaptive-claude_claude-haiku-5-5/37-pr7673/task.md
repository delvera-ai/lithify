BigQuery → DuckDB: BigQuery's `PARSE_TIME` is emitted verbatim for DuckDB, which has no such function:

```python
sqlglot.transpile("SELECT PARSE_TIME('%H:%M', '14:30')", read="bigquery", write="duckdb")
# ["SELECT PARSE_TIME('14:30', '%H:%M')"]   (invalid in DuckDB)
```

`PARSE_DATE` already transpiles (to `CAST(STRPTIME(...) AS DATE)`). Transpile `PARSE_TIME` to DuckDB in the equivalent way, producing a `TIME`.
