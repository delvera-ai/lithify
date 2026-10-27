DuckDB dialect: "FROM-first" queries fail when the joined sources are subqueries:

```python
sqlglot.parse_one('''
from (FROM tbl_1) t1
positional join (FROM tbl_2) t2
select t1.x as x1, t2.x as x2
''', read="duckdb")
# ParseError: Invalid expression / Unexpected token
```

The same query works with plain tables instead of subqueries, or with `SELECT` first. FROM-first queries with joined subqueries must parse.
