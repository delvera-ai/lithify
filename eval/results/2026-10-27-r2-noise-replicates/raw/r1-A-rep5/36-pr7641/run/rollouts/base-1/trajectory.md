# trajectory base-1

final message:
When MySQL has to simulate NULLS LAST and the ORDER BY uses a bare projection alias, the generated `CASE` now tests the aliased expression instead of the bare name. The full suite passes (1110 tests, 18038 subtests) and ruff is clean. I did not commit.

**Cause:** in `ORDER BY x`, MySQL resolves `x` to the projection alias. Inside the simulated `CASE WHEN x IS NULL`, it resolves `x` against the FROM tables instead, which fails when two tables have that column. Example: `SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY x` (DuckDB → MySQL).

**Fix** (`sqlglot/generator.py`, `ordered_sql`): when the ORDER BY term is an unqualified name that matches a projection in the same SELECT, the `CASE` check uses that projection's underlying expression. The sort key itself is unchanged.

Output now:
- `... ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`
- `... ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x` for qualified references, which were already correct.

**Choices I made:**
- I substitute the projection expression rather than qualifying the alias. An alias has no table to qualify with, so the aliased expression is the unambiguous equivalent.
- The substitution applies only to ORDER BY directly under a SELECT. Window `ORDER BY` clauses are left alone.

**Tests:** added `test_unsupported_null_ordering_ambiguous_columns` in `tests/dialects/test_dialect.py`, covering the alias case and the qualified case.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"nulls_first\\|nulls_are\\|null_ordering\\|NULL_ORDERING\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -50", "description": "Find null ordering handling in generator and MySQL"}
[tool_result] sqlglot/generator.py:296:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generator.py:299:    WINDOW_FUNCS_WITH_NULL_ORDERING: t.ClassVar[tuple[type[exp.Expression], ...]] = ()
sqlglot/generator.py:2962:        nulls_first = expression.args.get("nulls_first")
sqlglot/generator.py:2963:        nulls_last = not nulls_first
sqlglot/generator.py:2964:        nulls_are_large = self.dialect.NULL_ORDERING == "nulls_are_large"
sqlglot/generator.py:2965:        nulls_are_small = self.dialect.NULL
…[329 chars elided]…
     and ((asc and nulls_are_small) or (desc and nulls_are_large))
sqlglot/generator.py:2979:            and not nulls_are_last
sqlglot/generator.py:2984:        if nulls_sort_change and not self.NULL_ORDERING_SUPPORTED:
sqlglot/generator.py:2999:                isinstance(window_this, self.WINDOW_FUNCS_WITH_NULL_ORDERING)
sqlglot/generator.py:3007:                elif self.NULL_ORDERING_SUPPORTED is False and (
sqlglot/generator.py:3022:                elif self.NULL_ORDERING_SUPPORTED is None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120454-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "offset": 2950, "limit": 100}
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
[tool_use Bash] {"command": "grep -n \"NULL_ORDERING_SUPPORTED\\|nulls_first\\|NULLS\" sqlglot/dialects/mysql.py tests/dialects/test_mysql.py | head -30; grep -rn \"IS NULL THEN 1 ELSE 0\" tests/ | head", "description": "Check MySQL dialect and tests for null ordering"}
[tool_result] sqlglot/dialects/mysql.py:32:    LEAST_GREATEST_IGNORES_NULLS = False
tests/dialects/test_mysql.py:1111:                "postgres": "STRING_AGG(DISTINCT x, ',' ORDER BY y DESC NULLS LAST)",
tests/dialects/test_mysql.py:1121:                "postgres": "STRING_AGG(x, z ORDER BY y NULLS FIRST)",
tests/dialects/test_mysql.py:1131:                "postgres": "STRING_AGG(DISTINCT x, '' ORDER BY y DESC NULLS LAST)",
tests/dialects/test_mysql.py:1172:                "postgres": "STRING_AGG(a || b || c,
…[3871 chars elided]…
 WHEN col2 IS NULL THEN 1 ELSE 0 END, col2) FROM table1",
tests/dialects/test_mysql.py:1750:                "oracle": "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END NULLS FIRST, col2 NULLS FIRST) FROM table1",
tests/dialects/test_dialect.py:3444:        sql_nulls_last = "SELECT * FROM t ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END, c"
tests/dialects/test_dialect.py:3445:        sql_nulls_first = "SELECT * FROM t ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c"
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nqs = [\n 'SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT * FROM a 
…[107 chars elided]…
,\n]\nfor q in qs:\n    try:\n        print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n    except Exception as e: print('ERR', e)\n\" 2>&1; git log --oneline -3 -- sqlglot/generator.py; <work>/env-sqlglot/bin/python -I -c \"import sqlglot,sys;print(sqlglot.__file__)\"", "description": "Reproduce DuckDB to MySQL ORDER BY transpilation cases"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
f00bb4a24 Refactor(postgres)!: rename `Distance3d` to `DistanceNd`
cc448ac48 feat(postgres): add support for PostGIS 3D distance operator <<->> (#7655)
10af77782 feat(tsql): support FOR JSON clause [CLAUDE] (#7649)
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "cat > /tmp/repro_nulls.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport sqlglot\nqs = [\n 'SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT * FROM a JOIN
…[9 chars elided]…
d = b.id ORDER BY \"a\".\"x\"',\n 'SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1',\n]\nfor q in qs:\n    try:\n        print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n    except Exception as e: print('ERR', e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_nulls.py $(pwd)", "description": "Run transpile repro against this worktree"}
[tool_result] 'NULLS LAST' translation not supported with positional ordering
SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN v IS NULL THEN 1 ELSE 0 END, v
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT * FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN `a`.`x` IS NULL THEN 1 ELSE 0 END, `a`.`x`
SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1
[tool_use Bash] {"command": "sed -n 3425,3470p tests/dialects/test_dialect.py", "description": "View existing NULL ordering simulation tests"}
[tool_result]   SELECT
    *
  FROM tmp2
)
SELECT
  *
FROM subquery2""",
            },
            pretty=True,
        )

    def test_unsupported_null_ordering(self):
        # We'll transpile a portable query from the following dialects to MySQL / T-SQL, which
        # both treat NULLs as small values, so the expected output queries should be equivalent
        with_last_nulls = "duckdb"
        with_small_nulls = "spark"
        with_large_nulls = "postgres"

        sql = "SELECT * FROM t ORDER BY c"
 
…[946 chars elided]…
, sql_nulls_last),
            (with_large_nulls, True, None, sql_nulls_first),
            (with_large_nulls, False, True, sql),
            (with_large_nulls, True, True, sql_nulls_first),
            (with_large_nulls, False, False, sql_nulls_last),
            (with_large_nulls, True, False, sql),
        ):
            with self.subTest(
                f"read: {read_dialect}, descending: {desc}, nulls first: {nulls_first}"
            ):
                sort_order = " DESC" if desc else ""
[tool_use Bash] {"command": "sed -n 3470,3490p tests/dialects/test_dialect.py; grep -n \"def validate_all\\|def validate_identity\" tests/dialects/test_dialect.py | head -3", "description": "View rest of unsupported null ordering test"}
[tool_result]                 sort_order = " DESC" if desc else ""
                null_order = (
                    " NULLS FIRST"
                    if nulls_first
                    else (" NULLS LAST" if nulls_first is not None else "")
                )

                expected_sql = f"{expected_sql}{sort_order}"
                expression = parse_one(f"{sql}{sort_order}{null_order}", read=read_dialect)

                self.assertEqual(expression.sql(dialect="mysql"), expected_sql)
                self.assertEqual(expression.sql(dialect="tsql"), expected_sql)

    def test_random(self):
        self.validate_all(
            "RAND()",
            write={
                "bigquery": "RAND()",
                "clickhouse": "randCanonical()",
                "databricks": "RAND()",
                "doris": "RAND()",
53:    def validate_identity(
68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
[tool_use Bash] {"command": "grep -n \"def unalias\" -A8 sqlglot/expressions.py | head -12", "description": "Confirm unalias helper exists"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"def unalias\" -A6 sqlglot/exp.py sqlglot/expressions/ 2>/dev/null | head -12; ls sqlglot | head -50", "description": "Locate unalias helper in expression modules"}
[tool_result] sqlglot/expressions/core.py:401:    def unalias(self) -> Expr:
sqlglot/expressions/core.py-402-        """
sqlglot/expressions/core.py-403-        Returns the inner expression if this is an Alias.
sqlglot/expressions/core.py-404-        """
sqlglot/expressions/core.py-405-        raise NotImplementedError
sqlglot/expressions/core.py-406-
sqlglot/expressions/core.py-407-    def unnest_operands(self) -> tuple[Expr, ...]:
--
sqlglot/expressions/core.py:1198:    def unalias(self) -> Expr:
sqlglot/expressions/core.py-1199-        if isinstance(self, Alias):
sqlglot/expressions/core.py-1200-            return self.this
sqlglot/expressions/core.py-1201-        return self
__init__.py
__main__.py
__pycache__
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
[assistant] Now the fix: when a bare ORDER BY name is a projection alias, the simulated `CASE` should test the aliased expression instead of the alias, since MySQL resolves the bare name in `CASE` against the FROM tables and that can be ambiguous.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120454-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[1108 chars elided]…
                  if p.alias_or_name == expression.this.name\n                                ),\n                                None,\n                            )\n                            if projection:\n                                null_check = self.sql(projection.unalias())\n                        this = f\"CASE WHEN {null_check} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120454-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a regression test next to the existing NULL-ordering test, then the repro and the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120454-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_dialect.py", "old_string": "                self.assertEqual(expression.sql(dialect=\"mysql\"), expected_sql)\n                self.assertEqual(expression.sql(dialect=\"tsql\"), expected_sql)\n\n    def test_random(self):", "new_strin
…[521 chars elided]…
x IS NULL THEN 1 ELSE 0 END, x\",\n        )\n        self.assertEqual(\n            parse_one(\n                \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x\", read=\"duckdb\"\n            ).sql(dialect=\"mysql\"),\n            \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x\",\n        )\n\n    def test_random(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-120454-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_dialect.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_nulls.py $(pwd) && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k null_ordering 2>&1 | tail -15", "description": "Rerun repro and targeted NULL ordering tests"}
[tool_result] 'NULLS LAST' translation not supported with positional ordering
SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, v
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT * FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN `a`.`x` IS NULL THEN 1 ELSE 0 END, `a`.`x`
SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1
..                                                     [100%]
2 passed, 97 deselected, 18 subtests passed in 0.12s
[assistant] Targeted tests pass and the repro outputs look right. Running the full suite with the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/dialects/test_dialect.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_dialect.py 2>&1 | tail -3", "description": "Run full test suite and ruff checks"}
[tool_result] ......................................... [ 57%]
........................................................................................................ [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
......................................................................     [100%]
1110 passed, 18038 subtests passed in 51.09s
All checks passed!
2 files already formatted
[assistant] When MySQL has to simulate NULLS LAST and the ORDER BY uses a bare projection alias, the generated `CASE` now tests the aliased expression instead of the bare name. The full suite passes (1110 tests, 18038 subtests) and ruff is clean. I did not commit.

**Cause:** in `ORDER BY x`, MySQL resolves `x` to the projection alias. Inside the simulated `CASE WHEN x IS NULL`, it resolves `x` against the FROM tables instead, which fails when two tables have that column. Example: `SELECT a.x AS x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY x` (DuckDB → MySQL).

**Fix** (`sqlglot/generator.py`, `order
…[244 chars elided]…
 NULL THEN 1 ELSE 0 END, x`
- `... ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x` for qualified references, which were already correct.

**Choices I made:**
- I substitute the projection expression rather than qualifying the alias. An alias has no table to qualify with, so the aliased expression is the unambiguous equivalent.
- The substitution applies only to ORDER BY directly under a SELECT. Window `ORDER BY` clauses are left alone.

**Tests:** added `test_unsupported_null_ordering_ambiguous_columns` in `tests/dialects/test_dialect.py`, covering the alias case and the qualified case.
