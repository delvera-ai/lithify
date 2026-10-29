BigQuery → DuckDB: BigQuery's `PARSE_DATETIME` is emitted verbatim for DuckDB, which rejects it:

```python
sqlglot.transpile("SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')", read="bigquery", write="duckdb")
# today: ["SELECT PARSE_DATETIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
# expected: ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

Transpile it to DuckDB correctly.
