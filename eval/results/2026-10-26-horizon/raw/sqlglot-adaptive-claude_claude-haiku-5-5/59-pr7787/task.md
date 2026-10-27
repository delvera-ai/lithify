Snowflake dialect: in `CREATE` statements Snowflake accepts `KEY = VALUE` properties both after and **before** the column definitions:

```sql
CREATE TABLE t CHANGE_TRACKING=TRUE (id INT);
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE;
```

The second form works; the first fails to parse. Support properties before the column definitions.
