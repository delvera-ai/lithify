DuckDB dialect: overloaded `MACRO` definitions fail to parse:

```python
import sqlglot
sqlglot.parse_one("CREATE OR REPLACE MACRO add_2(a, b) AS a + b;", dialect="duckdb")   # OK
sqlglot.parse_one('''
CREATE MACRO add_x
    (a, b) AS a + b,
    (a, b, c) AS a + b + c;''', read="duckdb")                                        # fails
```

Support DuckDB's overloaded macro syntax (several parameter lists, each with its own body, for scalar and table macros), round-tripping in DuckDB. (Stated requirement: the overloads are represented by an `exp.MacroOverloads` node holding one entry per overload.)
