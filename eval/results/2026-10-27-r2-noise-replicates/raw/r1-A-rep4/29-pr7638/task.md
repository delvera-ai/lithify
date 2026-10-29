MySQL dialect: support `CHANGE [COLUMN]`, which redefines a column and can rename it:

```
ALTER TABLE t CHANGE [COLUMN] old_col_name new_col_name column_definition [FIRST | AFTER col_name]
```

It should parse and round-trip, consistent with how sqlglot represents MySQL's `MODIFY COLUMN` (the same full redefinition, plus the original column name).
