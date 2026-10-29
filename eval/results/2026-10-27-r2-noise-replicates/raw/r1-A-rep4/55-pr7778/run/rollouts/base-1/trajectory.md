# trajectory base-1

final message:
Trino's `FROM_ISO8601_DATE` now transpiles to a `DATE` cast for other dialects and round-trips in Presto and Trino. The full suite passes (1122 tests) and ruff check and format are clean.

```python
p = sqlglot.parse_one("SELECT FROM_ISO8601_DATE('2020-05-11')", "trino")
# snowflake / duckdb / spark / bigquery -> SELECT CAST('2020-05-11' AS DATE)
# trino / presto                        -> SELECT FROM_ISO8601_DATE('2020-05-11')
```

The change follows the same pattern as the existing `FROM_ISO8601_TIMESTAMP` handling:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression, mapped to the `FROM_ISO8601_DATE` name.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(... AS DATE)`, so every dialect that doesn't override it gets the cast.
- **`sqlglot/generators/presto.py`**: keeps the native `FROM_ISO8601_DATE` name for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering the cast output for DuckDB, Snowflake, Spark, Databricks and BigQuery, plus the Presto and Trino round-trip.

I haven't committed anything. The changes are in the working tree for you to review.

## events
[tool_use Bash] {"command": "git show 7db4d2515 --stat && grep -rn -i \"ISO8601\" sqlglot/ tests/ | head -50", "description": "Inspect recent commit and grep ISO8601 references"}
[tool_result] commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 2026 +0300

    fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
    
    FROM_ISO8601_TIMESTAMP is a Presto/Trino function that returns a
    timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
 
…[492 chars elided]…
STAMP"),
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
tests/dialects/test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Bash] {"command": "sed -n 3985,4005p sqlglot/generator.py && grep -n -i \"FromISO8601\\|iso8601\" -r sqlglot/ | head -30 && sed -n 425,445p sqlglot/expressions/temporal.py && grep -n -i \"class DateFromParts\\|class TsOrDsToDate\\|class Date(\" sqlglot/expressions/*.py | head; sed -n 25,50p tests/dialects/test_presto.py", "description": "Read relevant generator and expression code"}
[tool_result]         this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone}"

    def fromtimezone_sql(self, expression: exp.FromTimeZone) -> str:
        this = self.sql(expression, "this")
        zone = self.sql(expression, "zone")
        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"

    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
        return self.sql(exp.cast(expression.this, exp.DType
…[2138 chars elided]…
ino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
                "snowflake": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
                "spark": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
                "databricks": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
                "bigquery": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)",
            },
        )
        self.validate_all(
            "CAST(x AS INTERVAL YEAR TO MONTH)",
            write={
[tool_use Bash] {"command": "grep -n \"FromISO8601\\|FROM_ISO\" -r sqlglot tests | grep -v \"^tests/dialects/test_presto.py:3[7-9]\\|^tests/dialects/test_presto.py:4[01]\"; grep -n \"DType.DATE\\b\" sqlglot/generator.py | head -3; grep -n \"class Trino\" -A5 sqlglot/dialects/trino.py | head; grep -n \"TRANSFORMS\" -A3 sqlglot/generators/trino.py | head", "description": "Check existing references and Trino generator overrides"}
[tool_result] sqlglot/generator.py:3994:    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:
sqlglot/expressions/temporal.py:436:class FromISO8601Timestamp(Expression, Func):
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
5112:                    exp.DType.DATE,
5116:        if isinstance(this, exp.TsOrDsToDate) or this.is_type(exp.DType.DATE):
5120:            return self.sql(exp.TryCast(this=this, to=exp.DataType(this=exp.DType.DATE)))
9:class Trino(Presto):
10-    SUPPORTS_USER_DEFINED_TYPES = False
11-    LOG_BASE_FIRST = True
12-    CONCAT_WS_COALESCE = True
13-
14-    class Tokenizer(Presto.Tokenizer):
21:    TRANSFORMS = {
22:        **PrestoGenerator.TRANSFORMS,
23-        exp.ArraySum: lambda self, e: (
24-            f"REDUCE({self.sql(e, 'this')}, 0, (acc, x) -> acc + x, acc -> acc)"
25-        ),
[assistant] Now I'll make the change: add the expression class, a base generator method that casts to `DATE`, and keep the native name for Presto/Trino.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n\n\nclass FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n", "new_string": "        return self.sql(exp.cast(expression.this, exp.DType.TIMESTAMPTZ))\n\n    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "offset": 303, "limit": 8}
[tool_result] 303	        ),
304	        exp.Encode: lambda self, e: encode_decode_sql(self, e, "TO_UTF8"),
305	        exp.FileFormatProperty: lambda self, e: f"format={self.sql(exp.Literal.string(e.name))}",
306	        exp.First: _first_last_sql,
307	        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
308	        exp.FromTimeZone: lambda self, e: (
309	            f"WITH_TIMEZONE({self.sql(e, 'this')}, {self.sql(e, 'zone')}) AT TIME ZONE 'UTC'"
310	        ),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "offset": 36, "limit": 2}
[tool_result] 36	        self.validate_all(
37	            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "                \"bigquery\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "
…[417 chars elided]…
-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"databricks\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083510-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\np = sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", 'trino')\nfor d in ['snowflake','duckdb','spark','bigquery','trino','presto']:\n    print(d, p.sql(d))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py 2>&1 | tail -5", "description": "Verify transpilation output and run Presto/Trino tests"}
[tool_result] snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
trino SELECT FROM_ISO8601_DATE('2020-05-11')
presto SELECT FROM_ISO8601_DATE('2020-05-11')
...........................                         [100%]
27 passed, 525 subtests passed in 0.21s
[assistant] The targeted tests pass and the output matches the request. Running the full suite now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; (<work>/env-sqlglot/bin/python -m ruff check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_presto.py) 2>&1 | tail -3; git status --short", "description": "Run full test suite and lint checks"}
[tool_result] ............... [ 82%]
.................................................................. [ 88%]
.......... [ 89%]
..........................................................................................................................                                                        [100%]
1122 passed, 18191 subtests passed in 53.06s
All checks passed!
177 files already formatted
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
[assistant] Trino's `FROM_ISO8601_DATE` now transpiles to a `DATE` cast for other dialects and round-trips in Presto and Trino. The full suite passes (1122 tests) and ruff check and format are clean.

```python
p = sqlglot.parse_one("SELECT FROM_ISO8601_DATE('2020-05-11')", "trino")
# snowflake / duckdb / spark / bigquery -> SELECT CAST('2020-05-11' AS DATE)
# trino / presto                        -> SELECT FROM_ISO8601_DATE('2020-05-11')
```

The change follows the same pattern as the existing `FROM_ISO8601_TIMESTAMP` handling:

- **`sqlglot/expressions/temporal.py`**: new `FromISO8601Date` expression, mapped to the `FROM_ISO8601_DATE` name.
- **`sqlglot/generator.py`**: base `fromiso8601date_sql` emits `CAST(... AS DATE)`, so every dialect that doesn't override it gets the cast.
- **`sqlglot/generators/presto.py`**: keeps the native `FROM_ISO8601_DATE` name for Presto and Trino.
- **`tests/dialects/test_presto.py`**: a `validate_all` case covering the cast output for DuckDB, Snowflake, Spark, Databricks and BigQuery, plus the Presto and Trino round-trip.

I haven't committed anything. The changes are in the working tree for you to review.
