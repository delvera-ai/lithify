Postgres dialect: `COMMENT ON` fails for schema-qualified targets of some object kinds:

```python
from sqlglot import parse
for sql in ["COMMENT ON TYPE foo.mood IS 'x';", "COMMENT ON VIEW foo.bat IS 'x';"]:
    parse(sql, read="postgres")   # fails
```

(`COMMENT ON TABLE foo.bar IS 'x'` works.) Support schema-qualified `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` so they parse and round-trip.
