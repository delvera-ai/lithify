# trajectory base-1

final message:
The MySQL null-ordering simulation now avoids the ambiguous reference for projection aliases. The full suite passes (1109 tests) and ruff is clean. I could not run the queries against a real MySQL server, since none is installed here, so the MySQL behaviour is inferred from the generated SQL.

**What was wrong:** the simulated key copied the ORDER BY reference verbatim. For `SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ... ORDER BY x`, the output was `ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x`. The bare `x` inside the `CASE` is what MySQL can't resolve unambiguously across the join.

**The change** (`sqlglot/generator.py`, `ordered_sql`): when the ORDER BY key is an unqualified column that names a projection alias in the same SELECT's ORDER BY, the `CASE` now uses the aliased expression. The output becomes `ORDER BY CASE WHEN t1.a IS NULL THEN 1 ELSE 0 END, x`. The second key stays as the original reference.

**Choices I made:**
- **Qualified references are unchanged.** `ORDER BY t1.a` already produces `CASE WHEN t1.a IS NULL ... , t1.a`, so no change was needed.
- **Bare columns that aren't aliases are unchanged.** If a bare name is a column in several joined tables and not an alias, the original query is already ambiguous, so the simulation doesn't make it worse.
- **The alias lookup only applies to a SELECT's own ORDER BY.** Window `ORDER BY` clauses are excluded, so a window that references a column with the same name as an alias keeps its original reference.

**Test:** I added a case to `tests/dialects/test_duckdb.py` that checks the DuckDB → MySQL output for the aliased join query. I didn't commit anything.

## events
[assistant] I'll start by finding where the MySQL generator simulates `NULLS FIRST/LAST`.
[tool_use Bash] {"command": "rg -n \"IS NULL|nulls_are|NULLS_ARE|null_ordering|def ordered_sql|def _ordered\" sqlglot/generator.py sqlglot/dialects/mysql.py | head -50", "description": "Locate null ordering simulation code"}
[tool_result] sqlglot/generator.py:2958:    def ordered_sql(self, expression: exp.Ordered) -> str:
sqlglot/generator.py:2964:        nulls_are_large = self.dialect.NULL_ORDERING == "nulls_are_large"
sqlglot/generator.py:2965:        nulls_are_small = self.dialect.NULL_ORDERING == "nulls_are_small"
sqlglot/generator.py:2966:        nulls_are_last = self.dialect.NULL_ORDERING == "nulls_are_last"
sqlglot/generator.py:2973:            (asc and nulls_are_large) or (desc and nulls_are_small) or nulls_are_last
sqlglot/generator.py:2978:            and ((asc and nulls_are_small) or (desc and nulls_are_large))
sqlglot/generator.py:2979:            and not nulls_are_last
sqlglot/generator.py:3030:                            f"CASE WHEN {this} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}"
sqlglot/generator.py:3522:            # Wrap the entire call in a CASE expression that returns NULL if any input IS NULL.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "offset": 2955, "limit": 90}
[tool_result] 2955	    def sort_sql(self, expression: exp.Sort) -> str:
2956	        return self.op_expressions("SORT BY", expression)
2957	
2958	    def ordered_sql(self, expression: exp.Ordered) -> str:
2959	        desc = expression.args.get("desc")
2960	        asc = not desc
2961	
2962	        nulls_first = expression.args.get("nulls_first")
2963	        nulls_last = not nulls_first
2964	        nulls_are_large = self.dialect.NULL_ORDERING == "nulls_are_large"
2965	        nulls_are_small = self.dialect.
…[3741 chars elided]…

3033	
3034	        with_fill = self.sql(expression, "with_fill")
3035	        with_fill = f" {with_fill}" if with_fill else ""
3036	
3037	        return f"{this}{sort_order}{nulls_sort_change}{with_fill}"
3038	
3039	    def matchrecognizemeasure_sql(self, expression: exp.MatchRecognizeMeasure) -> str:
3040	        window_frame = self.sql(expression, "window_frame")
3041	        window_frame = f"{window_frame} " if window_frame else ""
3042	
3043	        this = self.sql(expression, "this")
3044	
[assistant] The simulation copies `this` verbatim, so the bug depends on how the ORDER BY reference is written. I'll reproduce it across the reference forms before deciding on a fix.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = [\n 'SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY a',\n 'SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY t1.a',\n 'SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x',\n 'SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x DESC',\n 'SELECT a FROM t1 ORDER BY a',\n]\nfor q in qs:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; git log --oneline -5 -- sqlglot/generator.py | cat; rg -n \"NULLS_FIRST|nulls_first|IS NULL THEN 1\" tests/dialects/test_mysql.py | head", "description": "Reproduce MySQL null ordering simulation output"}
[tool_result] SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN a IS NULL THEN 1 ELSE 0 END, a
SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN t1.a IS NULL THEN 1 ELSE 0 END, t1.a
SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x DESC
SELECT a FROM t1 ORDER BY CASE WHEN a IS NULL THEN 1 ELSE 0 END, a
f00bb4a24 Refactor(postgres)!: rename `Distance
…[199 chars elided]…
`CHANGE COLUMN`. (#7638)
80e0929cc Feat(parser): handle `COLLATE` in nested types and `CAST` closes #7624 (#7630)
1744:            "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END, col2) FROM table1",
1749:                "mysql": "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END, col2) FROM table1",
1750:                "oracle": "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END NULLS FIRST, col2 NULLS FIRST) FROM table1",
[assistant] Two of the five forms are ambiguous in MySQL: a bare name that's also a column in several tables (`ORDER BY a` over a join), and a projection alias (`ORDER BY x`). In the alias case, the copied `x` inside the `CASE` is what MySQL can't resolve. Before I change anything, I'll check whether a MySQL server is available to confirm, and look at the existing NULL-ordering tests.
[tool_use Bash] {"command": "which mysql mysqld 2>&1; rg -n \"NULL_ORDERING_SUPPORTED\" sqlglot/ | head; rg -n \"IS NULL THEN 1 ELSE 0 END\" tests/ | head -20", "description": "Check MySQL availability and existing tests"}
[tool_result] mysql not found
mysqld not found
sqlglot/generator.py:296:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generator.py:2984:        if nulls_sort_change and not self.NULL_ORDERING_SUPPORTED:
sqlglot/generator.py:3007:                elif self.NULL_ORDERING_SUPPORTED is False and (
sqlglot/generator.py:3022:                elif self.NULL_ORDERING_SUPPORTED is None:
sqlglot/generators/singlestore.py:29:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generators/mysql.py:134:    NULL
…[1773 chars elided]…
/test_redshift.py:256:                "tsql": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10067:  SUM(CASE WHEN "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "no_promo",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10068:  SUM(CASE WHEN NOT "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "promo",
[assistant] No MySQL server is available, so I can't run the query against MySQL. I'll fix it by reasoning from the generated SQL. The only form where the original query is valid but the simulated `CASE` is ambiguous is the projection-alias case. For an ORDER BY that names a projection alias, the `CASE` will reference the aliased expression instead of the bare alias name. Qualified references are already copied with their qualifier, so they need no change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[951 chars elided]…
pressions:\n                                if isinstance(projection, exp.Alias) and projection.alias == null_key.name:\n                                    null_key = projection.this\n                                    break\n                        null_key_sql = self.sql(null_key)\n                        this = f\"CASE WHEN {null_key_sql} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll check the outputs for each form and run the existing test suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = [\n 'SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY a',\n 'SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY t1.a',\n 'SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x',\n 'SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x DESC',\n 'SELECT t1.a AS x, ROW_NUMBER() OVER (ORDER BY x) AS rn FROM t1',\n 'SELECT a FROM t1 ORDER BY a',\n]\nfor q in qs:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify new outputs and run full test suite"}
[tool_result] SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN a IS NULL THEN 1 ELSE 0 END, a
SELECT t1.a, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN t1.a IS NULL THEN 1 ELSE 0 END, t1.a
SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN t1.a IS NULL THEN 1 ELSE 0 END, x
SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x DESC
SELECT t1.a AS x, ROW_NUMBER() OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) AS rn FROM t1
SELECT a 
…[724 chars elided]…
................................. [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1109 passed, 18038 subtests passed in 49.99s
[assistant] The full suite passes (1109 tests) and the alias case now resolves through the projection. I'll add a regression test next to the existing DuckDB→MySQL ordering checks.
[tool_use Bash] {"command": "rg -n \"def test_order_by|NULLS FIRST|\\\"mysql\\\": \\\"SELECT.*ORDER BY\" tests/dialects/test_duckdb.py | head -20", "description": "Find DuckDB ordering tests to extend"}
[tool_result] 84:                "mysql": "SELECT FIRST_VALUE(c) RESPECT NULLS OVER (PARTITION BY gb ORDER BY CASE WHEN ob IS NULL THEN 1 ELSE 0 END, ob) FROM t",
155:                "mysql": "SELECT SUM(X) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x)",
163:                "mysql": "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
170:                "mysql": "SELECT * FROM x ORDER BY 1",
1115:        self.validate_identity("SELECT LIST_SORT(x, 'ASC', 'NULLS FIRST')")
1117:        self.validate_identity("SELECT LIST_SORT(x, 'DESC', 'NULLS FIRST')")
1123:            "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
1125:                "": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname NULLS LAST",
1126:                "duckdb": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC, lname",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "offset": 1120, "limit": 20}
[tool_result] 1120	        self.validate_identity("SELECT LIST_SORT(x, 'DESC', 'NULLS' || ' FIRST')")
1121	        self.validate_identity("SELECT LIST_SORT(x, 'DE' || 'SC', 'NULLS' || ' FIRST')")
1122	        self.validate_all(
1123	            "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
1124	            write={
1125	                "": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname NULLS LAST",
1126	     
…[68 chars elided]…
age DESC NULLS FIRST, fname ASC, lname",
1127	            },
1128	        )
1129	        self.validate_all(
1130	            "MONTH('2021-03-01')",
1131	            write={
1132	                "duckdb": "MONTH('2021-03-01')",
1133	                "presto": "MONTH('2021-03-01')",
1134	                "hive": "MONTH('2021-03-01')",
1135	                "spark": "MONTH('2021-03-01')",
1136	            },
1137	        )
1138	        self.validate_all(
1139	            "LIST_CONCAT([1, 2], [3, 4])",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "                \"duckdb\": \"SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC, lname\",\n            },\n        )\n        self.validate_all(\n            \"MONTH('2021-03-01')
…[136 chars elided]…
",\n            },\n        )\n        self.validate_all(\n            \"SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY x\",\n            write={\n                \"mysql\": \"SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ON t1.id = t2.id ORDER BY CASE WHEN t1.a IS NULL THEN 1 ELSE 0 END, x\",\n            },\n        )\n        self.validate_all(\n            \"MONTH('2021-03-01')\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130805-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py 2>&1 | tail -3", "description": "Run tests and lint on changed files"}
[tool_result] ............................... [ 93%]
......................................................................     [100%]
1109 passed, 18039 subtests passed in 52.02s
Would reformat: sqlglot/generator.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[assistant] Tests pass, but `ruff format` wants to reformat `generator.py`. I'll check that its diff touches only my lines before applying it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/generator.py 2>&1 | head -30", "description": "Preview ruff formatting diff"}
[tool_result] --- sqlglot/generator.py
+++ sqlglot/generator.py
@@ -3037,7 +3037,10 @@
                             and isinstance(order.parent, exp.Select)
                         ):
                             for projection in order.parent.expressions:
-                                if isinstance(projection, exp.Alias) and projection.alias == null_key.name:
+                                if (
+                                    isinstance(projection, exp.Alias)
+                                    and projection.alias == null_key.name
+                                ):
                                     null_key = projection.this
                                     break
                         null_key_sql = self.sql(null_key)

1 file would be reformatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/generator.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects 2>&1 | tail -1 && git status --short && git diff --stat", "description": "Apply formatting and rerun dialect tests"}
[tool_result] 1 file reformatted
730 passed, 11058 subtests passed in 2.64s
 M sqlglot/generator.py
 M tests/dialects/test_duckdb.py
 sqlglot/generator.py          | 22 +++++++++++++++++++---
 tests/dialects/test_duckdb.py |  6 ++++++
 2 files changed, 25 insertions(+), 3 deletions(-)
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The MySQL null-ordering simulation now avoids the ambiguous reference for projection aliases. The full suite passes (1109 tests) and ruff is clean. I could not run the queries against a real MySQL server, since none is installed here, so the MySQL behaviour is inferred from the generated SQL.

**What was wrong:** the simulated key copied the ORDER BY reference verbatim. For `SELECT t1.a AS x, t2.b FROM t1 JOIN t2 ... ORDER BY x`, the output was `ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x`. The bare `x` inside the `CASE` is what MySQL can't resolve unambiguously across the join.

**The c
…[442 chars elided]…
L ... , t1.a`, so no change was needed.
- **Bare columns that aren't aliases are unchanged.** If a bare name is a column in several joined tables and not an alias, the original query is already ambiguous, so the simulation doesn't make it worse.
- **The alias lookup only applies to a SELECT's own ORDER BY.** Window `ORDER BY` clauses are excluded, so a window that references a column with the same name as an alias keeps its original reference.

**Test:** I added a case to `tests/dialects/test_duckdb.py` that checks the DuckDB → MySQL output for the aliased join query. I didn't commit anything.
