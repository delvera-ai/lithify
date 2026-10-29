# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB's `STRPTIME` with the arguments in the right order:

```python
sqlglot.transpile("SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')", read="bigquery", write="duckdb")
# ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

The full suite passes (1120 tests) and ruff is clean on the changed files.

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which reuses `str_to_time_sql`. It sits next to the existing `parsetime_sql`, which handles BigQuery's `PARSE_TIME` the same way.
- `tests/dialects/test_bigquery.py`: added a `validate_all` case asserting the DuckDB output above.

BigQuery round-trips are unchanged. The parser still builds `ParseDatetime`, so BigQuery output keeps `PARSE_DATETIME`.

I haven't committed anything. Two gaps I left alone:
- **`SAFE.PARSE_DATETIME`** still loses its `SAFE` wrapper and becomes a plain `STRPTIME`. That means bad input raises an error in DuckDB, where BigQuery returns NULL. The `StrToTime` path already has a `TRY_STRPTIME` mode for this, so wiring it up would be a follow-up.
- **The optional timezone argument** of `PARSE_DATETIME` is dropped in the DuckDB output, the same as the existing `StrToTime` path.

## events
[tool_use Bash] {"command": "grep -rn -i \"parse_datetime\\|ParseDatetime\\|PARSE_TIMESTAMP\\|ParseTimestamp\\|StrToTime\\|strptime\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/expressions.py | head -60", "description": "Search for parse datetime handling in dialects"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -rn -i \"parse_datetime\\|ParseDatetime\\|PARSE_TIMESTAMP\\|StrToTime\\|STRPTIME\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py | head -60", "description": "Search BigQuery and DuckDB dialects for datetime parsing"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  4.2K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  1.2K
sqlglot.png  7.2K
[tool_use Bash] {"command": "grep -rn -i \"PARSE_DATETIME\\|ParseDatetime\\|PARSE_TIMESTAMP\\|StrToTime\\|STRPTIME\" sqlglot/ | head -80", "description": "Search sqlglot package for datetime parsing references"}
[tool_result] sqlglot/parsers/clickhouse.py:290:        "PARSEDATETIME": _build_datetime_format(exp.ParseDatetime),
sqlglot/parsers/singlestore.py:27:        "TO_TIMESTAMP": build_formatted_time(exp.StrToTime),
sqlglot/parsers/spark2.py:66:            else build_formatted_time(exp.StrToTime)(args, dialect)
sqlglot/parsers/bigquery.py:95:def _build_parse_timestamp(args: list, dialect: Dialect) -> exp.StrToTime:
sqlglot/parsers/bigquery.py:96:    this = build_formatted_time(exp.StrToTime)([seq_get(args, 1), seq
…[6388 chars elided]…
tgres.py:365:        exp.StrToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, self.format_time(e)),
sqlglot/generators/postgres.py:371:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/drill.py:10:    timestrtotime_sql,
sqlglot/generators/drill.py:91:        exp.StrToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, self.format_time(e)),
sqlglot/generators/drill.py:93:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/presto.py:23:    timestrtotime_sql,
[tool_use Bash] {"command": "sed -n 90,100p sqlglot/parsers/bigquery.py && sed -n 246,256p sqlglot/parsers/bigquery.py && sed -n 436,462p sqlglot/expressions/temporal.py && sed -n 1780,1800p sqlglot/dialects/dialect.py && grep -n \"StrToTime\\|ParseDatetime\\|STRPTIME\" sqlglot/generators/duckdb.py && grep -n \"def build_formatted_time\" -A30 sqlglot/dialects/dialect.py | head -50", "description": "Inspect BigQuery builder, ParseDatetime class, DuckDB generator"}
[tool_result]         expression=seq_get(args, 1),
        max_dist=max_dist.expression if max_dist else None,
    )


def _build_parse_timestamp(args: list, dialect: Dialect) -> exp.StrToTime:
    this = build_formatted_time(exp.StrToTime)([seq_get(args, 1), seq_get(args, 0)], dialect)
    this.set("zone", seq_get(args, 2))
    return this


        ),
        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        
…[3570 chars elided]…
  target_dialect = (
1563-            t.cast(Dialect, Dialect[dialect_override])
1564-            if isinstance(dialect_override, str)
1565-            else dialect
1566-        )
1567-
1568-        fmt = seq_get(args, 1)
1569-        if not fmt:
1570-            fmt = target_dialect.TIME_FORMAT if default is True else default or None
1571-
1572-        return exp_class(this=seq_get(args, 0), format=target_dialect.format_time(fmt))
1573-
1574-    return _builder
1575-
1576-
1577-def time_format(
[tool_use Bash] {"command": "sed -n 2620,2690p sqlglot/generators/duckdb.py && grep -n \"def parsedatetime\\|def parsetime\\|ParseTime\\|ParseDatetime\" sqlglot/generators/*.py && grep -n \"ParseDatetime\\|PARSE_DATETIME\" tests/dialects/*.py | head -30", "description": "Inspect DuckDB str-to-time generator and existing tests"}
[tool_result]             if length := expression.args.get("length"):
                length = exp.If(this=length < 0, true=exp.Literal.number(0), false=length)

            return self.func("SUBSTRING", expression.this, start, length)

        return self.function_fallback_sql(expression)

    def strtotime_sql(self, expression: exp.StrToTime) -> str:
        # Check if target_type requires TIMESTAMPTZ (for LTZ/TZ variants)
        target_type = expression.args.get("target_type")
        needs_tz = target_ty
…[2882 chars elided]…
.py:121:"SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')",
tests/dialects/test_bigquery.py:122:).assert_is(exp.SafeFunc).this.assert_is(exp.ParseDatetime)
tests/dialects/test_bigquery.py:1976:"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')"
tests/dialects/test_dialect.py:801:"presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST('2020-01-01' AS VARCHAR),...
tests/dialects/test_hive.py:487:"presto": "TO_UNIXTIME(COALESCE(TRY(DATE_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d ...
[assistant] The DuckDB generator already has a `parsetime_sql` precedent for BigQuery's `PARSE_TIME`, so `PARSE_DATETIME` should follow the same pattern. I'll confirm the current output and check the test environment before editing.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d', x, 'UTC')\\\", read='bigquery', write='duckdb'))\n\" ; sed -n 1970,1985p tests/dialects/test_bigquery.py", "description": "Reproduce the bug and view related BigQuery test"}
[tool_result] ["SELECT PARSE_DATETIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT SAFE.PARSE_DATETIME('2024-01-15 10:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT PARSE_DATETIME(x, '%Y-%m-%d')"]
            write={
                "bigquery": "SELECT CAST(col AS STRUCT<fld1 STRUCT<fld2 INT64>>).fld1.fld2",
                "snowflake": "SELECT CAST(col AS OBJECT(fld1 OBJECT(fld2 INT))):fld1.fld2",
            },
        )
        self.validate_identity(
            "SELECT PARSE_DATETIME('%a %b %e %I:%M:%
…[58 chars elided]…
.validate_identity("FORMAT_TIME('%R', CAST('15:30:00' AS TIME))")
        self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
        self.validate_identity("BYTE_LENGTH('foo')")
        self.validate_identity("BYTE_LENGTH(b'foo')")
        self.validate_identity("CODE_POINTS_TO_STRING([65, 255])")
        self.validate_identity("APPROX_TOP_COUNT(col, 2)")
        self.validate_identity("ARPOX_TOP_SUM(col, 1.5, 2)")
        self.validate_identity("SAFE_CONVERT_BYTES_TO_STRING(b'\xc2')")
[assistant] Reproduced: the output is the unchanged BigQuery form, with arguments in the wrong order and no `STRPTIME`. I'll add a DuckDB generator method next to `parsetime_sql`, following the same pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    def parsetime_sql(self, expression: exp.ParseTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", 
…[178 chars elided]…
seTime) -> str:\n        formatted_time = self.format_time(expression)\n        return self.sql(\n            exp.cast(\n                self.func(\"STRPTIME\", expression.this, formatted_time),\n                exp.DataType(this=exp.DType.TIME),\n            )\n        )\n\n    def parsedatetime_sql(self, expression: exp.ParseDatetime) -> str:\n        return str_to_time_sql(self, expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll verify the fix and add a regression test next to the existing `PARSE_DATETIME` identity test.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%Y-%m-%d', x)\\\", read='bigquery', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT PARSE_DATETIME('%F %T', x)\\\", read='bigquery', write='bigquery'))\n\"; grep -n \"validate_all\" tests/dialects/test_bigquery.py | head -3", "description": "Verify the fix output and find validate_all usage"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME(x, '%Y-%m-%d')"]
["SELECT PARSE_DATETIME('%F %T', x)"]
271 matches in 2 files:

949:0:"MIN(x, y)"})
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\n            \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )\n", "new_string": "        self.validate_identity(\n            \"SELEC
…[145 chars elided]…
 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            },\n            write={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[assistant] The `read=` entry I just wrote is wrong: `validate_all` would generate the default dialect's output for the first argument, not the BigQuery text. I'll rewrite it so the BigQuery input is the first argument and only `write` is checked.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_all(\n            \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            read={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:
…[210 chars elided]…
%d %H:%M:%S')\",\n            },\n        )\n", "new_string": "        self.validate_all(\n            \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n            write={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run BigQuery and DuckDB dialect tests"}
[tool_result] .................. [ 17%]
....................................................................................                                     [100%]
=================================== FAILURES ===================================
_ TestBigQuery.test_bigquery [PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00') -> bigquery] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')" != "PARSE_DATETIME
…[7 chars elided]…
-%d %H:%M:%S', '2023-01-15 14:30:00')"
E   - PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')
E   ?                  ^^ ^
E   + PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')
E   ?                  ^^ ^^^^^^^^^^^^^
=========================== short test summary info ============================
SUBFAILED[PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00') -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bigquery
1 failed, 102 passed, 1661 subtests passed in 0.62s
[assistant] The BigQuery generator normalizes `%Y-%m-%d %H:%M:%S` to `%F %T`, so my BigQuery expectation was wrong. The test is about DuckDB, so I'll drop that entry.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "            write={\n                \"bigquery\": \"PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },", "new_string": "            write={\n                \"duckdb\": \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201623-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[assistant] Now the project's full check suite, plus the linter on the two changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -3", "description": "Run full test suite and lint the changed files"}
[tool_result] ................................................................................................................................................... [ 64%]
......................................................................................................................................................................................................................... [ 83%]
....................... [ 85%]
........................................................... [ 91%]
.................................. [ 94%]
................. [ 95%]
................................................          [100%]
1120 passed, 18167 subtests passed in 46.72s
All checks passed!
2 files already formatted
[assistant] `PARSE_DATETIME` now transpiles to DuckDB's `STRPTIME` with the arguments in the right order:

```python
sqlglot.transpile("SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')", read="bigquery", write="duckdb")
# ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

The full suite passes (1120 tests) and ruff is clean on the changed files.

**Change**
- `sqlglot/generators/duckdb.py`: added `parsedatetime_sql`, which reuses `str_to_time_sql`. It sits next to the existing `parsetime_sql`, which handles BigQuery's `PARSE_TIME` the same way.
- `tests/dialects/test_big
…[52 chars elided]…
 DuckDB output above.

BigQuery round-trips are unchanged. The parser still builds `ParseDatetime`, so BigQuery output keeps `PARSE_DATETIME`.

I haven't committed anything. Two gaps I left alone:
- **`SAFE.PARSE_DATETIME`** still loses its `SAFE` wrapper and becomes a plain `STRPTIME`. That means bad input raises an error in DuckDB, where BigQuery returns NULL. The `StrToTime` path already has a `TRY_STRPTIME` mode for this, so wiring it up would be a follow-up.
- **The optional timezone argument** of `PARSE_DATETIME` is dropped in the DuckDB output, the same as the existing `StrToTime` path.
