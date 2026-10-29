Optimizer: `SELECT * FROM cte UNPIVOT(...)` does not qualify correctly in BigQuery and other dialects: column resolution for an unpivoted CTE does not see the CTE's columns. The value column(s) before `FOR` and the `FOR` name column in `UNPIVOT` are new output names, not references to existing columns; only the `IN (...)` items reference source columns. Make `qualify` handle `UNPIVOT` over CTE sources, e.g.:

```sql
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
```
