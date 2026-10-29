# trajectory base-1

final message:
I fixed the alias case of the MySQL null-ordering simulation. The bare-column case from the issue is only partly addressed, and I could not confirm the result against a real MySQL server because none is installed here.

**What changed**

- `sqlglot/generator.py` (`ordered_sql`): when the simulated `CASE` would copy a bare name that is a projection alias in the enclosing `SELECT`, it now uses the aliased expression. For example, `SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x` now emits `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`. The trailing `x` still refers to the alias, so the ordering is unchanged. Window `ORDER BY` clauses are untouched.
- `tests/dialects/test_duckdb.py`: added a DuckDB→MySQL case for that query.

**Verification**

- Full suite: 1109 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` are clean on both changed files.

**Not covered**

- A bare column that is not an alias, such as `SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x`, still emits `CASE WHEN x IS NULL ...`. Without schema information sqlglot cannot tell which table `x` belongs to, so this case still needs a fix. Possible approaches are qualifying from the schema when it is available, or having the optimizer qualify columns first.
- I did not check the MySQL behaviour directly, so the alias fix rests on reading MySQL's ORDER BY resolution rules rather than on a live run.

I have not committed. Let me know if you want a commit and PR, and whether to take on the bare-column case as well.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"nulls_first\\|NULLS\\|null_ordering\\|IS NULL\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -60", "description": "Find null ordering handling in MySQL and generator"}
[tool_result] sqlglot/dialects/mysql.py:32:    LEAST_GREATEST_IGNORES_NULLS = False
sqlglot/generator.py:298:    # Window functions that support NULLS FIRST/LAST
sqlglot/generator.py:302:    # FIRST(x IGNORE NULLS) OVER vs FIRST (x) IGNORE NULLS OVER
sqlglot/generator.py:303:    IGNORE_NULLS_IN_FUNC = False
sqlglot/generator.py:305:    # Whether IGNORE NULLS is placed before ORDER BY in the agg.
sqlglot/generator.py:306:    # FIRST(x IGNORE NULLS ORDER BY y) vs FIRST(x ORDER BY y IGNORE NULLS)
sqlglot/generat
…[1746 chars elided]…
ance(this, self.RESPECT_IGNORE_NULLS_UNSUPPORTED_EXPRESSIONS):
sqlglot/generator.py:5114:                f"RESPECT/IGNORE NULLS is not supported for {type(this).key} in {self.dialect.__class__.__name__}"
sqlglot/generator.py:5118:        if self.IGNORE_NULLS_IN_FUNC and not expression.meta.get("inline"):
sqlglot/generator.py:5119:            if self.IGNORE_NULLS_BEFORE_ORDER:
sqlglot/generator.py:5449:            self.dialect.ARRAY_AGG_INCLUDES_NULLS and array_agg_expr.args.get("nulls_excluded")
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093456-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "offset": 2950, "limit": 100}
[tool_result] 2950	        return self.op_expressions("CLUSTER BY", expression)
2951	
2952	    def distribute_sql(self, expression: exp.Distribute) -> str:
2953	        return self.op_expressions("DISTRIBUTE BY", expression)
2954	
2955	    def sort_sql(self, expression: exp.Sort) -> str:
2956	        return self.op_expressions("SORT BY", expression)
2957	
2958	    def ordered_sql(self, expression: exp.Ordered) -> str:
2959	        desc = expression.args.get("desc")
2960	        asc = not desc
2961	
2962	     
…[4196 chars elided]…
emeasure_sql(self, expression: exp.MatchRecognizeMeasure) -> str:
3040	        window_frame = self.sql(expression, "window_frame")
3041	        window_frame = f"{window_frame} " if window_frame else ""
3042	
3043	        this = self.sql(expression, "this")
3044	
3045	        return f"{window_frame}{this}"
3046	
3047	    def matchrecognize_sql(self, expression: exp.MatchRecognize) -> str:
3048	        partition = self.partition_by_sql(expression)
3049	        order = self.sql(expression, "order")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor q in [\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS z, b.y FROM a JOIN b ON a.id = b.id ORDER BY z',\n 'SELECT x FROM a ORDER BY x',\n 'SELECT a.x FROM a ORDER BY a.x DESC',\n]:\n  print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"", "description": "Reproduce DuckDB to MySQL NULL ordering output"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in [\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS z, b.y FROM a JOIN b ON a.id = b.id ORDER BY z',\n 'SELECT x FROM a ORDER BY x',\n 'SELECT a.x FROM a ORDER BY a.x DESC',\n]:\n  print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"", "description": "Reproduce DuckDB to MySQL NULL ordering output"}
[tool_result] SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS z, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN z IS NULL THEN 1 ELSE 0 END, z
SELECT x FROM a ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x FROM a ORDER BY a.x DESC
[tool_use Bash] {"command": "grep -rn \"IS NULL THEN 1 ELSE 0 END\" tests | head -40; which mysqld mysql 2>/dev/null; echo \"---\"; ls tests | grep -i null", "description": "Find existing tests for NULL ordering simulation"}
[tool_result] tests/dialects/test_redshift.py:245:                "mysql": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/dialects/test_redshift.py:252:                "starrocks": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number 
…[1107 chars elided]…
col2) FROM table1",
tests/dialects/test_mysql.py:1750:                "oracle": "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END NULLS FIRST, col2 NULLS FIRST) FROM table1",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10067:  SUM(CASE WHEN "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "no_promo",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10068:  SUM(CASE WHEN NOT "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "promo",
mysqld not found
mysql not found
---
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093456-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[902 chars elided]…
  p.this\n                                    for p in window.expressions\n                                    if isinstance(p, exp.Alias) and p.alias == sort_key.name\n                                ),\n                                sort_key,\n                            )\n\n                        this = f\"CASE WHEN {self.sql(sort_key)} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093456-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in [\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS z, b.y FROM a JOIN b ON a.id = b.id ORDER BY z DESC',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT SUM(v) AS s FROM t GROUP BY g ORDER BY s',\n]:\n  print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check new output and run full test suite"}
[tool_result] SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS z, b.y FROM a JOIN b ON a.id = b.id ORDER BY z DESC
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT SUM(v) AS s FROM t GROUP BY g ORDER BY CASE WHEN SUM(v) IS NULL THEN 1 ELSE 0 END, s
.........................................
…[625 chars elided]…
................................. [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1109 passed, 18038 subtests passed in 50.54s
[assistant] Existing suite passes (1109). Now I'll add a regression test next to the existing DuckDB→MySQL null-ordering cases.
[tool_use Bash] {"command": "sed -n 145,160p tests/dialects/test_duckdb.py", "description": "View nearby DuckDB test for placement"}
[tool_result]             "SELECT CASE WHEN delim IS NULL THEN NULL ELSE ARRAY_TO_STRING(LIST_TRANSFORM(arr, x -> COALESCE(CAST(x AS TEXT), '')), delim) END",
            read={
                "snowflake": "SELECT ARRAY_TO_STRING(arr, delim)",
            },
        )
        self.validate_all(
            "SELECT SUM(X) OVER (ORDER BY x)",
            write={
                "bigquery": "SELECT SUM(X) OVER (ORDER BY x)",
                "duckdb": "SELECT SUM(X) OVER (ORDER BY x)",
                "mysql": "SELECT SUM(X) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x)",
            },
        )
        self.validate_all(
            "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
            write={
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093456-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)\",", "new_string": "        self.validate_all(\n            \"SELECT a.x AS x, b.y FROM a J
…[34 chars elided]…
\n            write={\n                \"duckdb\": \"SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x\",\n                \"mysql\": \"SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x\",\n            },\n        )\n        self.validate_all(\n            \"SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093456-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Run DuckDB tests, ruff lint and format check"}
[tool_result] ............................................     [100%]
44 passed, 600 subtests passed in 0.26s
All checks passed!
2 files already formatted
[assistant] I fixed the alias case of the MySQL null-ordering simulation. The bare-column case from the issue is only partly addressed, and I could not confirm the result against a real MySQL server because none is installed here.

**What changed**

- `sqlglot/generator.py` (`ordered_sql`): when the simulated `CASE` would copy a bare name that is a projection alias in the enclosing `SELECT`, it now uses the aliased expression. For example, `SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x` now emits `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`. The trailing `x` still refers to the ali
…[343 chars elided]…
 alias, such as `SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x`, still emits `CASE WHEN x IS NULL ...`. Without schema information sqlglot cannot tell which table `x` belongs to, so this case still needs a fix. Possible approaches are qualifying from the schema when it is available, or having the optimizer qualify columns first.
- I did not check the MySQL behaviour directly, so the alias fix rests on reading MySQL's ORDER BY resolution rules rather than on a live run.

I have not committed. Let me know if you want a commit and PR, and whether to take on the bare-column case as well.
