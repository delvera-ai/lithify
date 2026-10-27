MySQL dialect: `ALTER TABLE ... MODIFY [COLUMN] col_name column_definition [FIRST | AFTER col_name]` redefines the whole column. It has different semantics from `ALTER [COLUMN] col_name {SET DEFAULT ... | DROP DEFAULT | SET {VISIBLE|INVISIBLE}}`, but sqlglot treats it as an alter-column. Support `MODIFY COLUMN` with a full column definition and optional position, round-tripping for example:

```sql
ALTER TABLE t MODIFY COLUMN c INT NOT NULL DEFAULT 5
ALTER TABLE t MODIFY COLUMN c VARCHAR(50) NOT NULL DEFAULT 'foo'
ALTER TABLE t MODIFY COLUMN c INT COMMENT 'hi'
ALTER TABLE t MODIFY COLUMN c INT FIRST
```
