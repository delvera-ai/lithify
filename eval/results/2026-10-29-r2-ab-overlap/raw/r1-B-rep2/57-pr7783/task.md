Snowflake dialect: the `PATTERN` clause of a staged-file query is dropped when there is no `FILE_FORMAT`:

```python
sqlglot.parse_one("SELECT * FROM @mystage (PATTERN => '.*data-100.*')", dialect="snowflake").sql(dialect="snowflake")
# actual:   SELECT * FROM @mystage
# expected: SELECT * FROM @mystage (PATTERN => '.*data-100.*')
```

`FILE_FORMAT` and `PATTERN` are independent optional parameters; each must be preserved on its own and together.
