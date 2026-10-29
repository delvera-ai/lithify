# trajectory base-1

final message:
`FROM_ISO8601_DATE` from Trino now transpiles to a cast to `DATE` for other dialects, and still round-trips in Trino and Presto. The full suite passes (1122 passed), and the changes are uncommitted in the worktree.

- **Expression:** added `exp.FromISO8601Date` in `sqlglot/expressions/temporal.py`, mapped to `FROM_ISO8601_DATE`. There was no class for it before, so it was parsed as an unknown function.
- **Base generator:** `fromiso8601date_sql` in `sqlglot/generator.py` emits `CAST(x AS DATE)`. This mirrors the `FROM_ISO8601_TIMESTAMP` handling from commit 7db4d2515.
- **Presto/Trino generator:** `sqlglot/generators/presto.py` keeps the native `FROM_ISO8601_DATE(...)` name, so Trino and Presto round-trip.
- **Test:** added a `validate_all` case in `tests/dialects/test_presto.py` covering DuckDB, Snowflake, Spark, Databricks, BigQuery, Presto and Trino.

Output for `SELECT FROM_ISO8601_DATE('2020-05-11')` from Trino:
- Snowflake, DuckDB, Spark, BigQuery: `SELECT CAST('2020-05-11' AS DATE)`
- Trino, Presto: `SELECT FROM_ISO8601_DATE('2020-05-11')`

## events
[tool_use Bash] {"command": "git show 7db4d2515 --stat && git show 7db4d2515 | head -150 && grep -rn -i \"iso8601\" sqlglot/ | head -40", "description": "Inspect prior ISO8601 commit and grep references"}
[tool_result] commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 2026 +0300

    fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
    
    FROM_ISO8601_TIMESTAMP is a Presto/Trino function that returns a
    timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
 
…[3471 chars elided]…
    "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
             },
         )
         self.validate_all(
sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
[tool_use Bash] {"command": "sed -n 425,450p sqlglot/expressions/temporal.py && grep -rn \"FROM_ISO8601\\|FromISO8601\\|ISO8601\" sqlglot tests | grep -v \"^sqlglot/expressions/temporal\" ; grep -n \"ISO8601\" sqlglot/expressions/__init__.py; grep -rn \"DATE\\b\" sqlglot/generators/trino.py | head -3; grep -n \"class Trino\" -A3 sqlglot/dialects/trino.py", "description": "Inspect expression class and grep ISO8601 usages"}
[tool_result]     pass


class DateToDi(Expression, Func):
    pass


class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False, "default_year": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False
…[177 chars elided]…
mp: rename_func("FROM_ISO8601_TIMESTAMP"),
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
9:class Trino(Presto):
10-    SUPPORTS_USER_DEFINED_TYPES = False
11-    LOG_BASE_FIRST = True
12-    CONCAT_WS_COALESCE = True
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "offset": 3990, "limit": 6}
[tool_result] 3990	        this = self.sql(expression, "this")
3991	        zone = self.sql(expression, "zone")
3992	        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"
3993	
3994	    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
3995	        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "offset": 300, "limit": 10}
[tool_result] 300	        exp.Decode: lambda self, e: encode_decode_sql(self, e, "FROM_UTF8"),
301	        exp.DiToDate: lambda self, e: (
302	            f"CAST(DATE_PARSE(CAST({self.sql(e, 'this')} AS VARCHAR), {type(self.dialect).DATEINT_FORMAT}) AS DATE)"
303	        ),
304	        exp.Encode: lambda self, e: encode_decode_sql(self, e, "TO_UTF8"),
305	        exp.FileFormatProperty: lambda self, e: f"format={self.sql(exp.Literal.string(e.name))}",
306	        exp.First: _first_last_sql,
307	        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
308	        exp.FromTimeZone: lambda self, e: (
309	            f"WITH_TIMEZONE({self.sql(e, 'this')}, {self.sql(e, 'zone')}) AT TIME ZONE 'UTC'"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))", "new_string": "    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "offset": 30, "limit": 20}
[tool_result] 30	            },
31	            write={
32	                "presto": "CAST(x AS BOOLEAN)",
33	                "tsql": "CAST(x AS BIT)",
34	            },
35	        )
36	        self.validate_all(
37	            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
38	            write={
39	                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
40	                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
41	                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
42	                "snowflake": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
43	                "spark": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
44	                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
45	                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
46	            },
47	        )
48	        self.validate_all(
49	            "CAST(x AS INTERVAL YEAR TO MONTH)",
[assistant] Now I'll add a test next to the existing timestamp one, then run it to see the actual output across dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "        self.validate_all(\n            \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n            write={\n     
…[195 chars elided]…
-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131655-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nprint(repr(p.selects[0]))\nfor d in ['snowflake','duckdb','spark','bigquery','trino','presto']:\n    print(d, p.sql(d))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py 2>&1 | tail -15", "description": "Verify transpilation output and run Presto/Trino tests"}
[tool_result] FromISO8601Date(
  this=Literal(this='2020-05-11', is_string=True))
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
trino SELECT FROM_ISO8601_DATE('2020-05-11')
presto SELECT FROM_ISO8601_DATE('2020-05-11')
...........................                         [100%]
27 passed, 525 subtests passed in 0.23s
[assistant] Targeted tests pass and the output matches the request. Running the full suite now, since the base generator changed.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ............................................... [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 52.45s
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] `FROM_ISO8601_DATE` from Trino now transpiles to a cast to `DATE` for other dialects, and still round-trips in Trino and Presto. The full suite passes (1122 passed), and the changes are uncommitted in the worktree.

- **Expression:** added `exp.FromISO8601Date` in `sqlglot/expressions/temporal.py`, mapped to `FROM_ISO8601_DATE`. There was no class for it before, so it was parsed as an unknown function.
- **Base generator:** `fromiso8601date_sql` in `sqlglot/generator.py` emits `CAST(x AS DATE)`. This mirrors the `FROM_ISO8601_TIMESTAMP` handling from commit 7db4d2515.
- **Presto/Trino generator:** `sqlglot/generators/presto.py` keeps the native `FROM_ISO8601_DATE(...)` name, so Trino and Presto round-trip.
- **Test:** added a `validate_all` case in `tests/dialects/test_presto.py` covering DuckDB, Snowflake, Spark, Databricks, BigQuery, Presto and Trino.

Output for `SELECT FROM_ISO8601_DATE('2020-05-11')` from Trino:
- Snowflake, DuckDB, Spark, BigQuery: `SELECT CAST('2020-05-11' AS DATE)`
- Trino, Presto: `SELECT FROM_ISO8601_DATE('2020-05-11')`
