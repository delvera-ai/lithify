Lineage: `sqlglot.lineage.lineage()` does not trace the value and name columns produced by `UNPIVOT` back to their source columns. It returns a phantom column on the input relation instead:

```python
from sqlglot.lineage import lineage
sql = '''
WITH src AS (SELECT id, jan, feb FROM sales)
SELECT id, metric_name, score
FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
'''
schema = {"sales": {"id": "int", "jan": "int", "feb": "int"}}
lineage("score", sql, schema=schema, dialect="snowflake")
```

Lineage of an `UNPIVOT` value column should reach the unpivoted source columns (`jan`, `feb`), and the name column should be handled correctly.
