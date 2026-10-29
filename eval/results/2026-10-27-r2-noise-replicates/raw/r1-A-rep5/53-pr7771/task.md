Druid dialect: the `RETURNING <type>` clause of `JSON_VALUE` is not supported:

```python
sqlglot.parse_one("SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t", dialect="druid")
# ParseError: Expecting ). Line 1, Col: 36.
```

It should parse and round-trip unchanged in Druid (as it already does for MySQL, Trino and Exasol).
