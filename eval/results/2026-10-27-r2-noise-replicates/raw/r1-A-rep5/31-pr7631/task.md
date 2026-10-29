MySQL → Exasol: when alias references in `WHERE`, `GROUP BY` or `HAVING` are rewritten to Exasol's `LOCAL.<alias>` form, the match is case-sensitive. Exasol folds unquoted identifiers to upper case, so an alias `idField` and a reference `idfield` are the same identifier, but the rewrite misses it and produces invalid SQL:

```python
sqlglot.transpile("SELECT 1 AS idField FROM t GROUP BY idfield", read="mysql", write="exasol")
```

Match unquoted aliases case-insensitively, following Exasol's identifier rules.
