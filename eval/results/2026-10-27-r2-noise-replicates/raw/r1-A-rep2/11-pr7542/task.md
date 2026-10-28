Optimizer: qualifying a table function with a typed column alias list fails:

```python
from sqlglot.optimizer.qualify_tables import qualify_tables
qualify_tables(sqlglot.parse_one("SELECT * FROM fn() AS t(col INT)"), canonicalize_table_aliases=True)
# ValueError: Name needs to be a string or an Identifier, got: ColumnDef
```

Typed alias columns (column definitions) in a table alias must be handled when qualifying tables, keeping them intact.
