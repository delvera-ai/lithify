# trajectory base-1

final message:
`PARSE_DATETIME` now transpiles to DuckDB correctly:

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

Full suite after the final edit: `SUMMARY: 1120 passed, 18169 subtests passed in 51.47s` / `EXIT: 0`. `ruff check` and `ruff format --check` are clean on the changed files.

**Cause:** The BigQuery parser already builds `exp.ParseDatetime` with the correct arguments. The DuckDB generator had no handler for that node, so it fell back to emitting the function name unchanged.

**Changes:**
- `sqlglot/generators/duckdb.py`: `exp.ParseDatetime` now uses the existing `str_to_time_sql` helper, which emits `STRPTIME(value, format)`. The format is converted to DuckDB's syntax the same way `STRPTIME` already is.
- `sqlglot/generators/duckdb.py`: the `SAFE.PARSE_DATETIME(...)` form was also emitting `SAFE.STRPTIME(...)`, which DuckDB rejects. It now emits `CAST(TRY_STRPTIME(x, fmt) AS TIMESTAMP)`. This goes through a small `_safe_func_sql` helper, because the base `SafeFunc` transform takes precedence over an auto-discovered method. All other `SAFE.` functions keep the old output.
- `tests/dialects/test_bigquery.py`: added `validate_all` cases for the plain and `SAFE.` forms. The expected DuckDB strings come from the task wording and DuckDB's `STRPTIME` / `TRY_STRPTIME` rules, not from the generator's output. The BigQuery round-trip is unchanged.

**Probed and still wrong, outside this change:**
- `SAFE.PARSE_DATE(...)` → `SAFE.CAST(STRPTIME(x, ...) AS DATE)` and `SAFE.TIMESTAMP(...)` → `SAFE.CAST(x AS TIMESTAMPTZ)` still contain `SAFE.` for DuckDB. These are different constructs and I left them alone. The `SafeFunc` fix is a natural place to address them if you want that done too.
- `PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)` written back to BigQuery becomes `PARSE_DATETIME('%F %T', x)`. This comes from the existing BigQuery format normalisation and predates this change.

## events
[tool_use Bash] {"command": "grep -rn \"PARSE_DATETIME\\|ParseDatetime\\|StrToTime\\|PARSE_TIMESTAMP\\|ParseTimestamp\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/expressions/*.py | head -50; ls .lithify/harness/skills/sqlglot-dialect-functions/"}
[tool_result] sqlglot/generators/bigquery.py:178:def _str_to_datetime_sql(self: BigQueryGenerator, expression: exp.StrToDate | exp.StrToTime) -> str:
sqlglot/generators/bigquery.py:358:        exp.ParseDatetime: lambda self, e: self.func("PARSE_DATETIME", self.format_time(e), e.this),
sqlglot/generators/bigquery.py:380:        exp.StrToTime: _str_to_datetime_sql,
sqlglot/generators/bigquery.py:389:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/parsers/bigquery.py:95:def _build_parse_timestamp(args: lis
…[578 chars elided]…
trtotime_sql(self, expression: exp.StrToTime) -> str:
sqlglot/expressions/core.py:2385:        from sqlglot.expressions.temporal import TimeStrToTime as _TimeStrToTime
sqlglot/expressions/core.py:2387:        return _TimeStrToTime(this=datetime_literal, zone=tz)
sqlglot/expressions/temporal.py:440:class ParseDatetime(Expression, Func):
sqlglot/expressions/temporal.py:452:class StrToTime(Expression, Func):
sqlglot/expressions/temporal.py:464:class TimeStrToTime(Expression, Func):
SKILL.md
scripts
[tool_use Bash] {"command": "sed -n 240,260p sqlglot/parsers/bigquery.py; sed -n 350,362p sqlglot/generators/bigquery.py; sed -n 435,465p sqlglot/expressions/temporal.py; sed -n 2620,2650p sqlglot/generators/duckdb.py; grep -n \"ParseDatetime\\|StrToTime\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py"}
[tool_result]             this=seq_get(args, 0), form=seq_get(args, 1), is_casefold=True
        ),
        "OCTET_LENGTH": exp.ByteLength.from_arg_list,
        "TO_HEX": _build_to_hex,
        "PARSE_DATE": lambda args, dialect: build_formatted_time(exp.StrToDate)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIME": lambda args, dialect: build_formatted_time(exp.ParseTime)(
            [seq_get(args, 1), seq_get(args, 0)], dialect
        ),
        "PARSE_TIMESTAMP": 
…[2981 chars elided]…
 expression)
        if needs_tz:
            return self.sql(
                exp.cast(
                    base_sql,
                    exp.DataType(this=exp.DType.TIMESTAMPTZ),
                )
            )
        return base_sql
sqlglot/parsers/duckdb.py:180:        "STRPTIME": build_formatted_time(exp.StrToTime),
sqlglot/generators/duckdb.py:1664:        exp.TimeStrToTime: timestrtotime_sql,
sqlglot/generators/duckdb.py:2627:    def strtotime_sql(self, expression: exp.StrToTime) -> str:
[tool_use Bash] {"command": "grep -rn \"def str_to_time_sql\" -A8 sqlglot/dialects/dialect.py; grep -rn \"PARSE_DATETIME\\|ParseDatetime\" tests | head -20; grep -n \"def format_time\" -A3 sqlglot/generator.py"}
[tool_result] sqlglot/dialects/dialect.py:1795:def str_to_time_sql(self: Generator, expression: exp.Expr) -> str:
sqlglot/dialects/dialect.py-1796-    return self.func("STRPTIME", expression.this, self.format_time(expression))
sqlglot/dialects/dialect.py-1797-
sqlglot/dialects/dialect.py-1798-
sqlglot/dialects/dialect.py-1799-def concat_to_dpipe_sql(self: Generator, expression: exp.Concat) -> str:
sqlglot/dialects/dialect.py-1800-    return self.sql(reduce(lambda x, y: exp.DPipe(this=x, expression=y), express
…[1138 chars elided]…
_PARSE(CAST(x AS VARCHAR), '%Y-%m-%d %T')), PARSE_DATETIME(DATE_FORMAT(x, '%Y-%m-%d %T'), 'yyyy-MM-dd HH:mm:ss')))",
tests/fixtures/optimizer/annotate_functions.sql:1109:SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00');
tests/fixtures/optimizer/annotate_functions.sql:1449:PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008');
4589:    def format_time(
4590-        self,
4591-        expression: exp.Expr,
4592-        inverse_time_mapping: dict[str, str] | None = None,
[tool_use Bash] {"command": "grep -n \"str_to_time_sql\\|timestrtotime_sql\" sqlglot/generators/duckdb.py | head; sed -n 1655,1668p sqlglot/generators/duckdb.py; sed -n 1970,1980p tests/dialects/test_bigquery.py; grep -n \"class TestBigQuery\\|def test_bigquery\\|duckdb\" tests/dialects/test_bigquery.py | head -5"}
[tool_result] 36:    str_to_time_sql,
37:    timestrtotime_sql,
1664:        exp.TimeStrToTime: timestrtotime_sql,
2642:        base_sql = str_to_time_sql(self, expression)
        exp.Time: no_time_sql,
        exp.TimeDiff: _timediff_sql,
        exp.Timestamp: no_timestamp_sql,
        exp.TimestampAdd: _date_delta_to_binary_interval_op(),
        exp.TimestampDiff: lambda self, e: self.func(
            "DATE_DIFF", exp.Literal.string(e.unit), e.expression, e.this
        ),
        exp.TimestampSub: _dat
…[821 chars elided]…
      self.validate_identity("PARSE_TIME('%I:%M:%S', '07:30:00')")
        self.validate_identity("BYTE_LENGTH('foo')")
22:class TestBigQuery(Validator):
26:    def test_bigquery(self):
211:                "duckdb": "SELECT ARG_MAX_NULL(fruit, sold) FROM Store",
218:                "duckdb": "SELECT ARG_MIN_NULL(fruit, sold) FROM Store",
225:                "duckdb": "SELECT category, ARG_MAX_NULL(product, price), ARG_MIN_NULL(product, cost), ANY_VALUE(supplier) FROM products GROUP BY category",
[tool_use Bash] {"command": "grep -n \"        exp.P[a-zA-Z]*:\" sqlglot/generators/duckdb.py; grep -n \"^    TRANSFORMS\" sqlglot/generators/duckdb.py"}
[tool_result] 1634:        exp.PercentileCont: rename_func("QUANTILE_CONT"),
1635:        exp.PercentileDisc: rename_func("QUANTILE_DISC"),
1638:        exp.Pivot: transforms.preprocess([transforms.unqualify_columns]),
1639:        exp.PreviousDay: _day_navigation_sql,
1491:    TRANSFORMS = {
[tool_use Bash] {"command": "sed -n 1636,1640p sqlglot/generators/duckdb.py"}
[tool_result]         # DuckDB doesn't allow qualified columns inside of PIVOT expressions.
        # See: https://github.com/duckdb/duckdb/blob/671faf92411182f81dce42ac43de8bfb05d9909e/src/planner/binder/tableref/bind_pivot.cpp#L61-L62
        exp.Pivot: transforms.preprocess([transforms.unqualify_columns]),
        exp.PreviousDay: _day_navigation_sql,
        exp.RegexpILike: lambda self, e: self.func(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.PreviousDay: _day_navigation_sql,\n        exp.RegexpILike", "new_string": "        exp.ParseDatetime: str_to_time_sql,\n        exp.PreviousDay: _day_navigation_sql,\n        exp.RegexpILike"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1630,1634p sqlglot/generators/duckdb.py"}
[tool_result]         exp.SHA2: lambda self, e: _sha_sql(self, e, "SHA256"),
        exp.SHA2Digest: lambda self, e: _sha_sql(self, e, "SHA256", is_binary=True),
        exp.MonthsBetween: months_between_sql,
        exp.NextDay: _day_navigation_sql,
        exp.PercentileCont: rename_func("QUANTILE_CONT"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.ParseDatetime: str_to_time_sql,\n        exp.PreviousDay: _day_navigation_sql,", "new_string": "        exp.PreviousDay: _day_navigation_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.NextDay: _day_navigation_sql,\n        exp.PercentileCont:", "new_string": "        exp.NextDay: _day_navigation_sql,\n        exp.ParseDatetime: str_to_time_sql,\n        exp.PercentileCont:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now let me probe the output, the AST node, and the no-format edge case.
[tool_use Bash] {"command": "cat > /tmp/probe_pdt.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nprint(sqlglot.transpile(\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\", read=\"bigquery\", write=\"duckdb\"))\nprint(sqlglot.transpile(\"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', x)\", read=\"bigquery\", write=\"duckdb\"))\nprint(sqlglot.transpile(\"SELECT SAFE.PARSE_DATETIME('%F %T', 
…[264 chars elided]…
me)))\nprint(sqlglot.transpile(\"SELECT PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2023-01-15 14:30:00')\", read=\"bigquery\", write=\"duckdb\")[0] == \"SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\")\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pdt.py"}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME(x, '%a %b %-d %I:%M:%S %Y')"]
["SELECT SAFE.STRPTIME(x, '%Y-%m-%d %H:%M:%S')"]
["SELECT PARSE_DATETIME('%F %T', x)"]
ParseDatetime(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  format=Literal(this='%Y-%m-%d', is_string=True))
True
[assistant] The core case now matches the expected output. The `SAFE.` prefix in the third probe is wrong for DuckDB, so I'm checking how other BigQuery `SAFE.` functions are handled.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SAFE.PARSE_DATE(\\'%Y\\', x)','SAFE.PARSE_TIMESTAMP(\\'%Y\\', x)','SAFE.PARSE_TIME(\\'%H\\', x)']:\n    print(sqlglot.transpile('SELECT '+s, read='bigquery', write='duckdb'))\n\"; grep -rn \"SafeFunc\\|safe_func\" sqlglot/generators/*.py sqlglot/generator.py sqlglot/expressions/*.py sqlglot/parsers/bigquery.py sqlglot/dialects/duckdb.py | head -20; grep -n \"SAFE\" tests/dialects/test_bigquery.py | head"}
[tool_result] ["SELECT SAFE.CAST(STRPTIME(x, '%Y') AS DATE)"]
["SELECT SAFE.STRPTIME(x, '%Y')"]
["SELECT SAFE.CAST(STRPTIME(x, '%H') AS TIME)"]
sqlglot/generator.py:247:        exp.SafeFunc: lambda self, e: f"SAFE.{self.sql(e, 'this')}",
sqlglot/expressions/core.py:1956:class SafeFunc(Expression, Func):
sqlglot/parsers/bigquery.py:751:                func = exp.SafeFunc
108:        self.validate_identity("SAFE.SOME_RANDOM_FUNC(a, b, c)").assert_is(exp.SafeFunc)
110:            "SAFE.SUBSTR('foo', 0, -2)",
112
…[117 chars elided]…
"SAFE.PARSE_DATE('%Y-%m-%d', '2024-01-15')",
117:            "SAFE.PARSE_DATE('%F', '2024-01-15')",
120:            "SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00')",
121:            "SAFE.PARSE_DATETIME('%F %T', '2024-01-15 10:30:00')",
124:            "SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', '2024-01-15 10:30:00')",
125:            "SAFE.PARSE_TIMESTAMP('%F %T', '2024-01-15 10:30:00')",
236:        self.validate_identity("SAFE_CAST(encrypted_value AS STRING FORMAT 'BASE64')")
[tool_use Bash] {"command": "sed -n 735,775p sqlglot/parsers/bigquery.py; grep -n \"safe\" sqlglot/generators/duckdb.py sqlglot/dialects/dialect.py | head -20"}
[tool_result]                 options=self._parse_properties(),
                this=self._match_text_seq("AS") and self._parse_select(nested=True),
            )
        )

    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
        func_index = self._index + 1
        this = super()._parse_column_ops(this)

        if isinstance(this, exp.Dot) and isinstance(this.expression, exp.Func):
            prefix = this.this.name.upper()

            func: type[exp.Func] | None = None
        
…[2411 chars elided]…
py:2438:        is_safe = expression.args.get("safe")
sqlglot/generators/duckdb.py:2442:            func_name = "TRY_TO_BINARY" if is_safe else "TO_BINARY"
sqlglot/generators/duckdb.py:2456:            if is_safe:
sqlglot/generators/duckdb.py:2461:        return f"TRY({result})" if is_safe else result
sqlglot/generators/duckdb.py:2636:        if expression.args.get("safe"):
sqlglot/generators/duckdb.py:2655:        function_name = "STRPTIME" if not expression.args.get("safe") else "TRY_STRPTIME"
[tool_use Bash] {"command": "grep -n \"_sql_method\\|def sql(\" -A3 sqlglot/generator.py | head -60; sed -n 1950,1962p sqlglot/expressions/core.py"}
[tool_result] 1077:    def sql(
1078-        self,
1079-        expression: str | exp.Expr | None,
1080-        key: str | None = None,


class HavingMax(Expression):
    arg_types = {"this": True, "expression": True, "max": True}


class SafeFunc(Expression, Func):
    pass


class Typeof(Expression, Func):
    pass
[tool_use Bash] {"command": "sed -n 1077,1130p sqlglot/generator.py | grep -n \"TRANSFORMS\\|_sql\\|getattr\" "}
[tool_result] 24:            sql = self.function_fallback_sql(expression)
26:            sql = self.property_sql(expression)
32:    def uncache_sql(self, expression: exp.Uncache) -> str:
34:        exists_sql = " IF EXISTS" if expression.args.get("exists") else ""
35:        return f"UNCACHE TABLE{exists_sql} {table}"
37:    def cache_sql(self, expression: exp.Cache) -> str:
47:    def characterset_sql(self, expression: exp.CharacterSet) -> str:
[tool_use Bash] {"command": "sed -n 1085,1105p sqlglot/generator.py"}
[tool_result]         if isinstance(expression, str):
            return expression

        if key:
            value = expression.args.get(key)
            if value:
                return self.sql(value)
            return ""

        handler = self._dispatch.get(expression.__class__)

        if handler:
            sql = handler(self, expression)
        elif isinstance(expression, exp.Func):
            sql = self.function_fallback_sql(expression)
        elif isinstance(expression, exp.Property):
            sql = self.property_sql(expression)
        else:
            raise ValueError(f"Unsupported expression type {expression.__class__.__name__}")
[tool_use Bash] {"command": "grep -rn \"_dispatch\\b\\|_dispatch =\" sqlglot/generator.py | head; grep -n \"def _dispatch\\|TRANSFORMS.items\\|_sql\\\"\" -A6 sqlglot/generator.py | head -40"}
[tool_result] sqlglot/generator.py:77:def _build_dispatch(
sqlglot/generator.py:853:        "_dispatch",
sqlglot/generator.py:912:            dispatch = _build_dispatch(cls)
sqlglot/generator.py:914:        self._dispatch = dispatch
sqlglot/generator.py:1095:        handler = self._dispatch.get(expression.__class__)
83:        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
84-            continue
85-
86-        expr_key = attr_name[:-4]
87-        expr_cls = exp.EXPR_CLASSES.get(expr_key)
88-
89-        if expr_cls and expr_cls not in dispatch:
--
4015:                ops.add(getattr(self, f"{node.key}_sql")(node, stack))
4016-            else:
4017-                sql = self.sql(node)
4018-                if sqls and sqls[-1] in ops:
4019-                    sqls[-1] += f" {sql}"
4020-                else:
4021-                    sqls.append(sql)
[tool_use Bash] {"command": "sed -n 77,100p sqlglot/generator.py"}
[tool_result] def _build_dispatch(
    cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and expr_cls not in dispatch:
            dispatch[expr_cls] = getattr(cls, attr_name)

    return dispatch


class Generator:
    """
    Generator converts a given syntax tree to the corresponding SQL string.

    Args:
        pretty: Whether to format the produced SQL string.
[assistant] The base `SafeFunc` transform in `TRANSFORMS` takes precedence over an auto-discovered method, so the DuckDB fix for `SAFE.PARSE_DATETIME` has to go through a module-level helper in `TRANSFORMS`. Let me find a good spot for it.
[tool_use Bash] {"command": "grep -n \"^def _sha_sql\\|^def _day_navigation_sql\\|^def _\\w*sql\" sqlglot/generators/duckdb.py | head -30; grep -n \"exp.SafeFunc\\|exp.Safe\" sqlglot/generators/duckdb.py"}
[tool_result] 144:def _base64_decode_sql(self: DuckDBGenerator, expression: exp.Expr, to_string: bool) -> str:
166:def _last_day_sql(self: DuckDBGenerator, expression: exp.LastDay) -> str:
238:def _to_boolean_sql(self: DuckDBGenerator, expression: exp.ToBoolean) -> str:
292:def _date_sql(self: DuckDBGenerator, expression: exp.Date) -> str:
310:def _timediff_sql(self: DuckDBGenerator, expression: exp.TimeDiff) -> str:
364:def _array_insert_sql(self: DuckDBGenerator, expression: exp.ArrayInsert) -> str:
458:def
…[1165 chars elided]…
nerator, expression: exp.AnyValue) -> str:
1034:def _bitwise_agg_sql(
1067:def _literal_sql_with_ws_chr(self: DuckDBGenerator, literal: str) -> str:
1113:def _build_capitalization_sql(
1150:def _initcap_sql(self: DuckDBGenerator, expression: exp.Initcap) -> str:
1163:def _boolxor_agg_sql(self: DuckDBGenerator, expression: exp.BoolxorAgg) -> str:
1178:def _bitshift_sql(
1214:def _scale_rounding_sql(
1262:def _regr_val_sql(
1330:def _date_from_parts_sql(self, expression: exp.DateFromParts) -> str:
[tool_use Bash] {"command": "sed -n 1025,1034p sqlglot/generators/duckdb.py"}
[tool_result] def _anyvalue_sql(self: DuckDBGenerator, expression: exp.AnyValue) -> str:
    # Transform ANY_VALUE(expr HAVING MAX/MIN having_expr) to ARG_MAX_NULL/ARG_MIN_NULL
    having = expression.this
    if isinstance(having, exp.HavingMax):
        func_name = "ARG_MAX_NULL" if having.args.get("max") else "ARG_MIN_NULL"
        return self.func(func_name, having.this, having.expression)
    return self.function_fallback_sql(expression)


def _bitwise_agg_sql(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "    return self.function_fallback_sql(expression)\n\n\ndef _bitwise_agg_sql(", "new_string": "    return self.function_fallback_sql(expression)\n\n\ndef _safe_func_sql(self: DuckDBGenerator, expression: exp.SafeFunc) -> str:\n    func = expression.this\n    if isinstance(func, exp.ParseDatetime):\n        return self.sql(\n            exp.StrToTime(this=func.this, format=func.args.get(\"format\"), safe=True)\n        )\n    return f\"SAFE.{self.sql(expression, 'this')}\"\n\n\ndef _bitwise_agg_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.PreviousDay: _day_navigation_sql,", "new_string": "        exp.PreviousDay: _day_navigation_sql,\n        exp.SafeFunc: _safe_func_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pdt.py && PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT SAFE.PARSE_DATETIME(\\'%Y\\', x), SAFE.TIMESTAMP(x), SAFE.PARSE_DATE(\\'%Y\\', x) FROM t', read='bigquery', write='duckdb'))\nprint(sqlglot.transpile('SELECT PARSE_DATETIME(\\'%Y-%m-%d\\', x) AS d FROM t', read='bigquery', write='duckdb', pretty=True))\n\""}
[tool_result] ["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
["SELECT STRPTIME(x, '%a %b %-d %I:%M:%S %Y')"]
["SELECT CAST(TRY_STRPTIME(x, '%Y-%m-%d %H:%M:%S') AS TIMESTAMP)"]
["SELECT PARSE_DATETIME('%F %T', x)"]
ParseDatetime(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  format=Literal(this='%Y-%m-%d', is_string=True))
True
["SELECT CAST(TRY_STRPTIME(x, '%Y') AS TIMESTAMP), SAFE.CAST(x AS TIMESTAMPTZ), SAFE.CAST(STRPTIME(x, '%Y') AS DATE) FROM t"]
["SELECT\n  STRPTIME(x, '%Y-%m-%d') AS d\nFROM t"]
[assistant] Both the plain and `SAFE.` forms now produce valid DuckDB. Next I'll add tests next to the existing `PARSE_DATETIME` identity test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py", "old_string": "        self.validate_identity(\n            \"SELECT PARSE_DATETIME('%a %b %e %I:%M:%S %Y', 'Thu Dec 25 07:30:00 2008')\"\n        )\n", "new_string": "        self.validate_identity(\n            \"SELEC
…[236 chars elided]…
": \"PARSE_DATETIME('%F %T', '2023-01-15 14:30:00')\",\n                \"duckdb\": \"STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')\",\n            },\n        )\n        self.validate_all(\n            \"SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)\",\n            write={\n                \"duckdb\": \"CAST(TRY_STRPTIME(x, '%Y-%m-%d %H:%M:%S') AS TIMESTAMP)\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-110302-bigquery-duckdb-bigquery-s-parse/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py", "description": "Run bigquery and duckdb dialect tests", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:33:11 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0139ede6aa.log
ELAPSED: 1s
SUMMARY: 102 passed, 1663 subtests passed in 0.57s
EXIT: 0
[assistant] The dialect tests pass. Now the full suite, which is the required check after the last edit.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:33:14 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0139ede6aa.log
ELAPSED: 51s
SUMMARY: 1120 passed, 18169 subtests passed in 50.25s
EXIT: 0
[assistant] The full suite passes. I'll run the linter and formatter on the changed files, since the repo's `make check` requires it.
[tool_use Bash] {"command": "(ruff --version && ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
Would reformat: sqlglot/generators/duckdb.py
1 file would be reformatted, 1 file already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[tool_use Bash] {"command": "ruff format --diff sqlglot/generators/duckdb.py 2>&1 | head -30", "description": "Show formatter diff for duckdb generator"}
[tool_result] --- sqlglot/generators/duckdb.py
+++ sqlglot/generators/duckdb.py
@@ -1034,9 +1034,7 @@
 def _safe_func_sql(self: DuckDBGenerator, expression: exp.SafeFunc) -> str:
     func = expression.this
     if isinstance(func, exp.ParseDatetime):
-        return self.sql(
-            exp.StrToTime(this=func.this, format=func.args.get("format"), safe=True)
-        )
+        return self.sql(exp.StrToTime(this=func.this, format=func.args.get("format"), safe=True))
     return f"SAFE.{self.sql(expression, 'this')}"
 
 

1 file would be reformatted
[tool_use Bash] {"command": "ruff format sqlglot/generators/duckdb.py && ruff format --check sqlglot/generators/duckdb.py && <work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py && git diff --stat", "description": "Format duckdb generator and rerun dialect tests", "timeout": 600000}
[tool_result] 1 file reformatted
1 file already formatted
WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:34:12 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0139ede6aa.log
ELAPSED: 1s
SUMMARY: 102 passed, 1663 subtests passed in 0.51s
EXIT: 0
 sqlglot/generators/duckdb.py    |  9 +++++++++
 tests/dialects/test_bigquery.py | 13 +++++++++++++
 2 files changed, 22 insertions(+)
[This command modified 1 file you've previously read: sqlglot/generators/duckdb.py. Call Read before editing.]
[assistant] The formatter changed the file after the last full run, so I'm rerunning the full suite to get a summary that postdates the final edit.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Rerun full test suite after formatting", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:34:17 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0139ede6aa.log
ELAPSED: 52s
SUMMARY: 1120 passed, 18169 subtests passed in 51.47s
EXIT: 0
[assistant] `PARSE_DATETIME` now transpiles to DuckDB correctly:

```
["SELECT STRPTIME('2023-01-15 14:30:00', '%Y-%m-%d %H:%M:%S')"]
```

Full suite after the final edit: `SUMMARY: 1120 passed, 18169 subtests passed in 51.47s` / `EXIT: 0`. `ruff check` and `ruff format --check` are clean on the changed files.

**Cause:** The BigQuery parser already builds `exp.ParseDatetime` with the correct arguments. The DuckDB generator had no handler for that node, so it fell back to emitting the function name unchanged.

**Changes:**
- `sqlglot/generators/duckdb.py`: `exp.ParseDatetime` now uses the existing `str_to
…[715 chars elided]…
 from the generator's output. The BigQuery round-trip is unchanged.

**Probed and still wrong, outside this change:**
- `SAFE.PARSE_DATE(...)` → `SAFE.CAST(STRPTIME(x, ...) AS DATE)` and `SAFE.TIMESTAMP(...)` → `SAFE.CAST(x AS TIMESTAMPTZ)` still contain `SAFE.` for DuckDB. These are different constructs and I left them alone. The `SafeFunc` fix is a natural place to address them if you want that done too.
- `PARSE_DATETIME('%Y-%m-%d %H:%M:%S', x)` written back to BigQuery becomes `PARSE_DATETIME('%F %T', x)`. This comes from the existing BigQuery format normalisation and predates this change.
