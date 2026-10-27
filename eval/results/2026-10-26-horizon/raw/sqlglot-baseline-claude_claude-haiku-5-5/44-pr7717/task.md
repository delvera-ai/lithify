ClickHouse dialect: the `file` table function is parsed incorrectly and does not round-trip:

```python
sqlglot.parse_one("CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)", dialect="clickhouse").sql(dialect="clickhouse")
# 'CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet)'
```

`file(...)` should be parsed as a table function and round-trip unchanged.
