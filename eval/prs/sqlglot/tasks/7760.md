SQLite (and other dialects with upsert): parsing `INSERT ... ON CONFLICT (...)` fails when the conflict target contains a complex expression instead of plain column names, for example a target matching a unique index on `(col_x, lower(col_y))`:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z)
SELECT x, y, z FROM src WHERE true
ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z
```

`ON CONFLICT` targets with expressions (and an optional `WHERE` on the target) should parse and round-trip.
