BigQuery pipe syntax: when a pipe query has leading CTEs, its generated intermediate CTEs (`__tmp1`, ...) are replaced by the leading CTEs, producing a query that references a CTE that does not exist:

```sql
WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2
-- today:    WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
-- expected: WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

Leading CTEs and the pipe syntax's intermediate CTEs must both be kept.
