Optimizer (Spark/Hive): optimizing a `LATERAL VIEW EXPLODE` over an `ARRAY<STRUCT<...>>` and then accessing a field on the generated alias fails:

```python
from sqlglot.optimizer import optimize
sql = "SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci"
schema = {"my_table": {"items": "ARRAY<STRUCT<name:STRING>>"}}
optimize(sqlglot.parse_one(sql, read="spark"), schema=schema, dialect="spark")
# OptimizeError
```

`EXPLODE` aliases must be qualified and type-annotated so field access on the exploded struct works.
