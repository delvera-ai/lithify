SQLite and other dialects: a `WINDOW` clause is rejected when the query has no `FROM`:

```python
sqlglot.parse_one("SELECT 1 WINDOW a AS (PARTITION BY fake_column);", read="sqlite")
# ParseError: Invalid expression / Unexpected token. Line 1, Col: 17.
```

With a `FROM` clause the same works. Allow the `WINDOW` clause without `FROM`.
