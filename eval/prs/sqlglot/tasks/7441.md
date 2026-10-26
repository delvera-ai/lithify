SQLite dialect: support the full `PRAGMA` syntax. This query fails to parse:

```python
import sqlglot
sqlglot.parse_one("PRAGMA full_column_names=on;", read="sqlite")
# ParseError: Required keyword: 'expression' missing for EQ. Line 1, Col: 27.
```

With values such as `off`, `1` or `2` instead of `on` it parses. All forms of SQLite's PRAGMA statement (see https://sqlite.org/pragma.html) should parse and round-trip.
