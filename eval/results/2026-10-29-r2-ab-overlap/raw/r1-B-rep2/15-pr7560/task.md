Optimizer: `(UN)PIVOT` over CTE sources must qualify correctly. Both of these fail or silently skip star expansion today, in BigQuery and other dialects:

```sql
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
```

Column resolution for a pivoted CTE source must use the CTE's columns, for both aliased and unaliased pivots.
