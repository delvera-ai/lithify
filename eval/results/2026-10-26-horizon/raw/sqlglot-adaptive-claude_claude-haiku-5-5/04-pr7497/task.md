Transpiling DuckDB's `JSON_ARRAY` function to Snowflake produces invalid SQL, because Snowflake has no `JSON_ARRAY` (its equivalent is `ARRAY_CONSTRUCT`):

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output today (invalid)
SELECT JSON_ARRAY('a', 'b', 'c')
```

DuckDB `JSON_ARRAY(...)` should be understood as a function and generate valid Snowflake SQL.
