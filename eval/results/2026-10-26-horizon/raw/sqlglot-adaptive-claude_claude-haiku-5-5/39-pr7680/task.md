MySQL dialect: multi-table `UPDATE` fails to parse:

```sql
UPDATE authors, books
SET authors.deleted_at = now(), books.deleted_at = now()
-- ParseError: Invalid expression / Unexpected token. Line 5, Col: 9.
```

The single-table form works. Support MySQL's joined-table `UPDATE` syntax (comma-separated tables and explicit joins) so it parses and round-trips.
