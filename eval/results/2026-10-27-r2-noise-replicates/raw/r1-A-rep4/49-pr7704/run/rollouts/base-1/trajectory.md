# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB's `STRPTIME`, and your example produces the expected output:

```
SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which emits `STRPTIME(value, format)`. It sits beside `parsetime_sql`, which handles the sibling `PARSE_TIME` case the same way. The method has no cast, because DuckDB's `STRPTIME` already returns a timestamp.
- `tests/dialects/test_duckdb.py`: added a `validate_all` case for your example, next to the `PARSE_TIME` cases.

**Verification**
- Full suite: 1120 passed.
- `ruff format --check` and `ruff check` pass on both files.
- The `%a %b %e` format from the existing BigQuery test also transpiles cleanly.

I haven't committed anything.

**Not fixed: `SAFE.PARSE_DATETIME`.** BigQuery's `SAFE.` prefix still comes out as `SAFE.STRPTIME(...)`, which DuckDB rejects. This is not specific to this change. `SAFE.PARSE_DATE`, `SAFE.PARSE_TIME`, and `SAFE.PARSE_TIMESTAMP` already produce the same invalid `SAFE.` output for DuckDB. The fix belongs in a shared handler for `exp.SafeFunc` in the DuckDB generator, probably mapping to `TRY_STRPTIME` so that failures return NULL as BigQuery's `SAFE` does. I left it out because it changes behavior for every `SAFE.*` function, so it should be its own change.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|StrToDate\\|StrToTime\\b\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -50", "description": "Search for PARSE_DATETIME and related expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|TimeToStr\\b\" sqlglot/ tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -50", "description": "Search sqlglot and tests for PARSE_DATETIME"}
[tool_result] sqlglot/generator.py:5218:                transformed = cast(this=exp.TimeToStr(this=value, format=fmt), to=to, safe=safe)
sqlglot/generator.py:5220:                transformed = exp.TimeToStr(this=value, format=fmt)
sqlglot/parsers/dremio.py:21:def to_char_is_numeric_handler(args: list, dialect: DialectType) -> exp.TimeToStr | exp.ToChar:
sqlglot/parsers/dremio.py:104:        "DATE_FORMAT": build_formatted_time(exp.TimeToStr),
sqlglot/parsers/singlestore.py:30:        "DATE_FORMAT": build_forma
…[3731 chars elided]…
 timetostr_sql(self, expression: exp.TimeToStr) -> str:
sqlglot/generators/snowflake.py:989:    def timetostr_sql(self, expression: exp.TimeToStr) -> str:
sqlglot/generators/sqlite.py:185:        exp.TimeToStr: lambda self, e: self.func("STRFTIME", e.args.get("format"), e.this),
sqlglot/generators/hive.py:527:    def timetostr_sql(self, expression: exp.TimeToStr) -> str:
sqlglot/generators/presto.py:357:        exp.TimeToStr: lambda self, e: self.func("DATE_FORMAT", e.this, self.format_time(e)),
[tool_use Bash] {"command": "sed -n 430,475p sqlglot/expressions/temporal.py; echo ----; grep -n \"STRPTIME\\|StrToTime\\|TimeStrToTime\\|ParseDatetime\\|TimeToStr\\|StrToDate\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py; echo ----; sed -n 245,260p sqlglot/parsers/bigquery.py; echo ---; grep -n \"PARSE_DATETIME\" tests/dialects/*.py | head; echo ---; grep -n \"class StrToTime\" -A12 sqlglot/expressions/temporal.py", "description": "Inspect expression defs, parser/generator mappings"}
[tool_result] class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}


class StrToDate(Expression, Func):
    arg_types = {"this": True, "format": False, "safe": False}


class StrToTime(Expression, Func):
    arg_types = {"this": True, "format":
…[3651 chars elided]…
COALESCE(TRY(DATE_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d %T')), PARSE_DATETIME(DATE_FORMAT(x, '%Y-%m-%d %T'), 'yyyy-MM-dd HH:mm:ss')))",
---
452:class StrToTime(Expression, Func):
453-    arg_types = {"this": True, "format": True, "zone": False, "safe": False, "target_type": False}
454-
455-
456-class StrToUnix(Expression, Func):
457-    arg_types = {"this": False, "format": False}
458-
459-
460-class TimeStrToDate(Expression, Func):
461-    pass
462-
463-
464-class TimeStrToTime(Expression, Func):
[tool_use Bash] {"command": "sed -n 2620,2650p sqlglot/generators/duckdb.py; echo ----; sed -n 1640,1670p sqlglot/generators/duckdb.py; echo ----; grep -n \"ParseDatetime\\|StrToTime\" sqlglot/generators/*.py sqlglot/dialects/*.py | head -40; echo; git log --oneline -3 -- sqlglot/generators/duckdb.py", "description": "Read DuckDB strtotime generator and related mappings"}
[tool_result]             if length := expression.args.get("length"):
                length = exp.If(this=length < 0, true=exp.Literal.number(0), false=length)

            return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_ty
…[5515 chars elided]…
ql(self: TSQLGenerator, expression: exp.TimeStrToTime):
sqlglot/generators/tsql.py:235:        exp.TimeStrToTime: _timestrtotime_sql,
sqlglot/generators/sqlite.py:184:        exp.TimeStrToTime: lambda self, e: self.sql(e, "this"),

6ae53c2e8 feat(duckdb): Add transpilation support for TRY_CAST date-format (#7707)
e23a9eece feat(duckdb): Add transpilation support for BOOLEAN and TEXT cases of TRY_CAST function (#7681)
a7e21a49f fix(duckdb): add transpilation support for bq func PARSE_TIME (#7673)
[assistant] There's a recent precedent for this exact pattern (`PARSE_TIME` → DuckDB). Let me look at that commit.
[tool_use Bash] {"command": "git show a7e21a49f --stat && git show a7e21a49f -- sqlglot/ tests/ | head -150", "description": "Show the PARSE_TIME precedent commit"}
[tool_result] commit a7e21a49f6c83e2917b9e02fc39c9e4237f4850a
Author: William Goode <95141298+william-goode@users.noreply.github.com>
Date:   Mon May 25 11:08:41 2026 -0400

    fix(duckdb): add transpilation support for bq func PARSE_TIME (#7673)
    
    * fix: add ParseTime transpilation for BigQuery to DuckDB
    
    BigQuery's PARSE_TIME is parsed into exp.ParseTime but DuckDB's
    generator has no handler, so it falls through to function_fallback_sql
    and emits PARSE_TIME(...) verbatim, which DuckD
…[2549 chars elided]…
ST(STRPTIME('14:30', '%H:%M') AS TIME)",
+            read={"bigquery": "SELECT PARSE_TIME('%H:%M', '14:30')"},
+        )
+        self.validate_all(
+            "SELECT CAST(STRPTIME('15:30:00.123456', '%H:%M:%S.%f') AS TIME)",
+            read={"bigquery": "SELECT PARSE_TIME('%H:%M:%E6S', '15:30:00.123456')"},
+        )
         self.validate_all(
             "SELECT CAST('2020-01-01' AS DATE) + INTERVAL '-1' DAY",
             read={"mysql": "SELECT DATE '2020-01-01' + INTERVAL -1 DAY"},
[assistant] The precedent is clear: add a `parsetime_sql`-style method to the DuckDB generator. For `PARSE_DATETIME` the expected output is a bare `STRPTIME` (no cast), since DuckDB's `STRPTIME` already returns a timestamp. I'll add the method next to `parsetime_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081806-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", 
…[215 chars elided]…
me = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, formatted_time),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return self.func(\"STRPTIME\", expression.this, self.format_time(expression))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081806-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a test alongside the PARSE_TIME ones, then a check of the exact repro.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081806-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M:%E6S', '15:30:00.123456')\"},\n        )\n", "new_string": "            read={\"bigquery\": \"SELECT PARSE_TIME('%H:%M:%E6S', '15:30:00.123456')\"},\n        )\n        self.validate_all(\n            \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\"bigquery\": \"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081806-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\\\", read='bigquery', write='duckdb'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -30", "description": "Verify repro output and run BigQuery/DuckDB tests"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT SAFE.STRPTIME('2024-01-15 10:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME('Thu Dec 25 07:30:00 2008', '%a %b %-d %I:%M:%S %Y')"]
........................ [ 23%]
..............................................................................                                      [100%]
102 passed, 1661 subtests passed in 0.69s
[assistant] The main repro is fixed, but the `SAFE.PARSE_DATETIME` output (`SAFE.STRPTIME`) is invalid DuckDB. Let me see how the BigQuery parser represents `SAFE.` and whether other functions handle it.
[tool_use Bash] {"command": "grep -n '\"SAFE\"' sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py | head; grep -n \"SAFE\\.\" tests/dialects/test_duckdb.py | head; echo ---; grep -n \"SAFE\\.\" tests/dialects/test_bigquery.py | head -20", "description": "Find how SAFE. prefix is handled"}
[tool_result] sqlglot/parsers/bigquery.py:750:            elif prefix == "SAFE":
---
108:        self.validate_identity("SAFE.SOME_RANDOM_FUNC(a, b, c)").assert_is(exp.SafeFunc)
110:            "SAFE.SUBSTR('foo', 0, -2)",
112:        self.validate_identity("SAFE.TIMESTAMP(foo, zone)").assert_is(exp.SafeFunc).this.assert_is(
116:            "SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')",
117:            "SAFE.PARSE_DATE('%F', '2024-01-15')",
120:            "SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00')",
121:            "SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')",
124:            "SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00')",
125:            "SAFE.PARSE_TIMESTAMP('%F %T', '2024-01-15 10:30:00')",
[tool_use Bash] {"command": "sed -n 740,765p sqlglot/parsers/bigquery.py; echo ---; grep -n \"class SafeFunc\" -A3 sqlglot/expressions/*.py; grep -rn \"SafeFunc\\|safefunc\" sqlglot/generators/*.py sqlglot/dialects/duckdb.py | head; echo ---; sed -n 100,130p tests/dialects/test_duckdb.py", "description": "Inspect SafeFunc handling in parser and generators"}
[tool_result]     def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
        func_index = self._index + 1
        this = super()._parse_column_ops(this)

        if isinstance(this, exp.Dot) and isinstance(this.expression, exp.Func):
            prefix = this.this.name.upper()

            func: type[exp.Func] | None = None
            if prefix == "NET":
                func = exp.NetFunc
            elif prefix == "SAFE":
                func = exp.SafeFunc

            if func:
        
…[1507 chars elided]…
ght_join`",
            },
        )
        self.validate_all(
            'STRUCT_PACK("a b" := 1)',
            write={
                "duckdb": "{'a b': 1}",
                "spark": "STRUCT(1 AS `a b`)",
                "snowflake": "OBJECT_CONSTRUCT('a b', 1)",
            },
        )
        self.validate_all(
            "ARRAY_TO_STRING(arr, delim)",
            read={
                "bigquery": "ARRAY_TO_STRING(arr, delim)",
                "postgres": "ARRAY_TO_STRING(arr, delim)",
[assistant] `SafeFunc` is a generic wrapper. Let me check what the base generator does with it and how the other `SAFE.PARSE_*` functions currently come out for DuckDB, to decide whether this is in scope.
[tool_use Bash] {"command": "grep -rn \"SafeFunc\" sqlglot/ | grep -v \"^sqlglot/expressions/core.py:1956\" | head; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in [\\\"SELECT SAFE.PARSE_DATE('%F', '2024-01-15')\\\", \\\"SELECT SAFE.PARSE_TIME('%H:%M', '14:30')\\\", \\\"SELECT SAFE.PARSE_TIMESTAMP('%F %T', '2024-01-15 10:30:00')\\\", \\\"SELECT SAFE.PARSE_
…[11 chars elided]…
F %T', '2024-01-15 10:30:00')\\\"]:\n    print(sqlglot.transpile(q, read='bigquery', write='duckdb'))\n\"; cd ~/.cache/lithify/work/repo-d5521a213087/20261029-081806-bigquery-duckdb-bigquery-s-parse/base-1 && git stash list | head -0; git -C . show HEAD:sqlglot/generators/duckdb.py > /dev/null && echo ok", "description": "Check SafeFunc generation and SAFE.PARSE_* outputs for DuckDB"}
[tool_result] sqlglot/generator.py:247:        exp.SafeFunc: lambda self, e: f"SAFE.{self.sql(e, 'this')}",
sqlglot/parsers/bigquery.py:751:                func = exp.SafeFunc
sqlglot/typing/bigquery.py:196:            exp.SafeFunc,
["SELECT SAFE.CAST(STRPTIME('2024-01-15', '%Y-%m-%d') AS DATE)"]
["SELECT SAFE.CAST(STRPTIME('14:30', '%H:%M') AS TIME)"]
["SELECT SAFE.STRPTIME('2024-01-15 10:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT SAFE.STRPTIME('2024-01-15 10:30:00', '%Y-%m-%d %H:%M:%S')"]
head: illegal line count -- 0
ok
[assistant] The `SAFE.` problem is pre-existing and affects all of `SAFE.PARSE_DATE/TIME/TIMESTAMP` the same way, so it isn't specific to this change. I'll leave it out of this fix and report it. Now the full project test suite, which is the required check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ........................................................................................................................................................................................ [ 24%]
................................... [ 27%]
............... [ 29%]
........................................................................................................ [ 38%]
..................................................... [ 43%]
.....................................................................
…[259 chars elided]…
......................................................................................................................................................... [ 83%]
....................... [ 85%]
........................................................... [ 91%]
.................................. [ 94%]
................. [ 95%]
................................................          [100%]
1120 passed, 18167 subtests passed in 52.69s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] Full suite passes (1120 tests). I'll run the style check on the two edited files, since the repo uses ruff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py 2>&1) | tail -8", "description": "Run ruff format and lint checks on edited files"}
[tool_result] 2 files already formatted
All checks passed!
[assistant] `PARSE_DATETIME` now transpiles to DuckDB's `STRPTIME`, and your example produces the expected output:

```
SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')
```

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which emits `STRPTIME(value, format)`. It sits beside `parsetime_sql`, which handles the sibling `PARSE_TIME` case the same way. The method has no cast, because DuckDB's `STRPTIME` already returns a timestamp.
- `tests/dialects/test_duckdb.py`: added a `validate_all` case for your example, next to the `PARSE_TIME` cases.

**Verification**
- Full suite: 
…[149 chars elided]…
anly.

I haven't committed anything.

**Not fixed: `SAFE.PARSE_DATETIME`.** BigQuery's `SAFE.` prefix still comes out as `SAFE.STRPTIME(...)`, which DuckDB rejects. This is not specific to this change. `SAFE.PARSE_DATE`, `SAFE.PARSE_TIME`, and `SAFE.PARSE_TIMESTAMP` already produce the same invalid `SAFE.` output for DuckDB. The fix belongs in a shared handler for `exp.SafeFunc` in the DuckDB generator, probably mapping to `TRY_STRPTIME` so that failures return NULL as BigQuery's `SAFE` does. I left it out because it changes behavior for every `SAFE.*` function, so it should be its own change.
