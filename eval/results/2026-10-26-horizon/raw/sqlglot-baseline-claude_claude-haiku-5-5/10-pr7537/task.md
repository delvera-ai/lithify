MySQL / MariaDB: `SHOW TABLES IN <schema>` is a synonym for `SHOW TABLES FROM <schema>`, but only `FROM` is parsed:

```python
sqlglot.parse_one("SHOW TABLES IN test", dialect="mysql")
# ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
```

Accept `IN` as well (it may generate as the `FROM` form) without breaking other `SHOW ... IN` forms such as `SHOW BINLOG EVENTS IN 'logfile'`.
