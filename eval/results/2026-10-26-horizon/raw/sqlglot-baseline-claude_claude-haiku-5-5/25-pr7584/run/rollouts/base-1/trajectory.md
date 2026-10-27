# trajectory base-1

final message:
BigQuery `BIGNUMERIC` / `BIGDECIMAL` with explicit parameters now transpiles to DuckDB using only those parameters. `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`, not the concatenated form. The default mapping is still used when no parameters are given.

**The change**
- `sqlglot/generators/duckdb.py`: added a `datatype_sql` override. When the type is `BIGDECIMAL` and has parameters, it emits `DECIMAL(<params>)`. Otherwise it defers to the base class, so `DECIMAL(38, 5)` from `TYPE_MAPPING` still applies.
- `tests/dialects/test_bigquery.py`: extended `test_bignumeric` to cover both `BIGNUMERIC` and `BIGDECIMAL` with `(76, 38)`. I did not change or weaken any existing assertions.

**Verification**
- Before the fix, the reported output reproduced exactly (`DECLARE x DECIMAL(38, 5)(76, 38)`).
- `test_bigquery.py` and `test_duckdb.py`: 102 passed.
- Full suite: 1105 passed, 17952 subtests passed.

I did not commit. The changes are in the working tree.

**Something to decide:** DuckDB's `DECIMAL` caps precision at 38, so `DECIMAL(76, 38)` is valid SQL text but will fail when DuckDB executes it. I followed your rule and emit the user's parameters as given. If you'd rather clamp or warn when precision exceeds 38, that is a small follow-up.

## events
[tool_use Bash] {"command": "grep -n -i \"bignumeric\\|bigdecimal\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/parser.py sqlglot/expressions.py sqlglot/dialects/dialect.py tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -80", "description": "Find BIGNUMERIC/BIGDECIMAL references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
tests/dialects/test_bigquery.py:223:        self.validate_identity("CAST(x AS BIGNUMERIC)")
tests/dialects/test_bigquery.py:1924:        self.validate_identity("PARSE
…[24 chars elided]…
ts/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
[tool_use Bash] {"command": "grep -n -i \"BIGNUMERIC\\|BIGDECIMAL\\|DType.DECIMAL\\b\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/dialects/dialect.py sqlglot/parser.py | head -60; echo ---; grep -n \"def datatype_sql\" -A60 sqlglot/generator.py | head -90", "description": "Locate BIGNUMERIC mapping and datatype_sql"}
[tool_result] sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
---
1639:    def datatype_sql(self, expression: exp.DataType) -> str:
1640-        nested = ""
1641-        values = ""
1642-
1643-        expr_nested = expression.args.get("nested
…[2112 chars elided]…
 directory_sql(self, expression: exp.Directory) -> str:
1692-        local = "LOCAL " if expression.args.get("local") else ""
1693-        row_format = self.sql(expression, "row_format")
1694-        row_format = f" {row_format}" if row_format else ""
1695-        return f"{local}DIRECTORY {self.sql(expression, 'this')}{row_format}"
1696-
1697-    def delete_sql(self, expression: exp.Delete) -> str:
1698-        hint = self.sql(expression, "hint")
1699-        this = self.sql(expression, "this")
[tool_use Bash] {"command": "grep -n -i \"BIGNUMERIC\\|BIGDECIMAL\\|BIGNUM\" sqlglot/dialects/*.py sqlglot/*.py | head -40; echo ---; sed -n 3805,3840p tests/dialects/test_bigquery.py", "description": "Search all dialects for BIGNUMERIC handling"}
[tool_result] sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/tokenizer_core.py:126:    BIGNUM = auto()
sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:481:        TokenType.BIGNUM,
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/tokens.py:447:      
…[854 chars elided]…
                 write={
                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST('1' AS DECIMAL(38, 5))",
                    },
                )

                self.validate_all(
                    f"SELECT CAST(1 AS {type_})",
                    write={
                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST(1 AS DECIMAL(38, 5))",
                    },
                )
[tool_use Bash] {"command": "grep -n \"38\\|76\\|DECIMAL\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py | head -40; echo ---; grep -rn \"def datatype_sql\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py", "description": "Find DECIMAL default parameter handling"}
[tool_result] sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
---
[tool_use Bash] {"command": "grep -rn \"BIGDECIMAL\\|(38, 5)\\|DECIMAL_PRECISION\\|76\" sqlglot/ --include=*.py | grep -v \"^sqlglot/tokens.py:44\\|tokenizer_core\" | head -30; echo ---; grep -n \"DataType.Type.DECIMAL\\|DType.DECIMAL\" sqlglot/dialects/*.py sqlglot/generator.py | head -30", "description": "Search for DECIMAL default and BIGDECIMAL usage"}
[tool_result] (eval):1: no matches found: --include=*.py
---
sqlglot/dialects/__init__.py:49:            exp.DType.DECIMAL: "NUMERIC",
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
[tool_use Bash] {"command": "grep -rn \"BIGDECIMAL\\|(38, 5)\\|38, 5\\|DECIMAL_DEFAULT\\|76\" sqlglot/ | grep -v \"\\.pyc\" | head -30; echo ---; grep -n \"DType.DECIMAL\\|DECIMAL\" sqlglot/dialects/duckdb.py | head; echo; grep -n \"def _parse_types\\|DECIMAL\" sqlglot/parser.py | head -20", "description": "Search sqlglot source for decimal default mapping"}
[tool_result] sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects
…[2295 chars elided]…
sions arg gets set by the parser when we have something like DECIMAL(38, 0)
6073:            # in the input SQL. In that case, we'll produce these tokens: DECIMAL ( 38 , 0 )
6076:            # consumed additional tokens such as the DECIMAL scale and precision in the above example.
6080:            # callable in the TYPE_CONVERTERS mapping. For example, Snowflake converts DECIMAL to
6081:            # DECIMAL(38, 0)) in order to facilitate the data type's transpilation.
6116:    def _parse_types(
[tool_use Bash] {"command": "sed -n 1715,1760p sqlglot/generators/duckdb.py; echo ---; grep -n \"TYPE_MAPPING\\|def datatype_sql\" sqlglot/generators/duckdb.py | head; echo ---; grep -n \"TYPE_MAPPING\" -A3 sqlglot/generator.py | head -20", "description": "Read DuckDB type mapping around BIGDECIMAL"}
[tool_result]         exp.LastDay: _last_day_sql,
    }

    SUPPORTED_JSON_PATH_PARTS = {
        exp.JSONPathKey,
        exp.JSONPathRoot,
        exp.JSONPathSubscript,
        exp.JSONPathWildcard,
    }

    TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.BINARY: "BLOB",
        exp.DType.BPCHAR: "TEXT",
        exp.DType.CHAR: "TEXT",
        exp.DType.DATETIME: "TIMESTAMP",
        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
        exp.DType.FLOAT: "REAL",
        exp.DType.J
…[828 chars elided]…
create_p",
        "window",
        "asymmetric",
        "to",
---
1725:    TYPE_MAPPING = {
1726:        **generator.Generator.TYPE_MAPPING,
---
608:    TYPE_MAPPING: t.ClassVar = {
609-        exp.DType.DATETIME2: "TIMESTAMP",
610-        exp.DType.NCHAR: "CHAR",
611-        exp.DType.NVARCHAR: "VARCHAR",
--
1665:                self.TYPE_MAPPING.get(type_value, type_value.value)
1666-                if isinstance(type_value, exp.DType)
1667-                else type_value
1668-            )
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && $PY -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)','SELECT CAST(1 AS BIGDECIMAL(20))','SELECT CAST(1 AS BIGNUMERIC)']:\n    e = sqlglot.parse_one(s, read='bigquery')\n    print(repr(e.find(sqlglot.exp.DataType)))\n    print(e.sql('duckdb'))\n\"; grep -n \"def datatype_sql\" sqlglot/generators/*.py | head", "description": "Reproduce the BIGNUMERIC parameterised output in DuckDB"}
[tool_result] <work>/env-sqlglot/bin/python
DataType(
  this=DType.BIGDECIMAL,
  expressions=[
    DataTypeParam(
      this=Literal(this=76, is_string=False)),
    DataTypeParam(
      this=Literal(this=38, is_string=False))],
  nested=False)
DECLARE x DECIMAL(38, 5)(76, 38)
DataType(
  this=DType.BIGDECIMAL,
  expressions=[
    DataTypeParam(
      this=Literal(this=20, is_string=False))
…[585 chars elided]…
: exp.DataType) -> str:
sqlglot/generators/exasol.py:306:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/risingwave.py:27:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/postgres.py:477:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/mysql.py:628:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/snowflake.py:686:    def datatype_sql(self, expression: exp.DataType) -> str:
[assistant] Reproduced: the default mapping and the explicit parameters are both emitted. I'll look at an existing `datatype_sql` override to match the style.
[tool_use Bash] {"command": "sed -n 75,85p sqlglot/generators/dremio.py; sed -n 35,45p sqlglot/generators/materialize.py; grep -n \"def datatype_sql\" -A12 sqlglot/generators/duckdb.py | head -5; grep -n \"^    def \\w*_sql\" sqlglot/generators/duckdb.py | head -5", "description": "Read existing datatype_sql overrides for style"}
[tool_result]     def datatype_sql(self, expression: exp.DataType) -> str:
        """
        Reject time-zone-aware TIMESTAMPs, which Dremio does not accept
        """
        if expression.is_type(
            exp.DType.TIMESTAMPTZ,
            exp.DType.TIMESTAMPLTZ,
        ):
            self.unsupported("Dremio does not support time-zone-aware TIMESTAMP")

        return super().datatype_sql(expression)
    def datatype_sql(self, expression: exp.DataType) -> str:
        if expression.is_type(exp.DTyp
…[318 chars elided]…
} => {self.sql(value)}]"

        return super().datatype_sql(expression)
334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:    def bitmapbitposition_sql(self, expression: exp.BitmapBitPosition) -> str:
[assistant] The fix: keep the default mapping for the unparameterised case, and emit `DECIMAL(...)` with the user's parameters when they're given. I'll add the override in the DuckDB generator next to the other type-related methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145510-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def timeslice_sql(self, expression: exp.TimeSlice) -> str:", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.BIGDECIMAL) and expression.expressions:\n            return f\"DECIMAL({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)\n\n    def timeslice_sql(self, expression: exp.TimeSlice) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145510-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Next I'll add a regression test next to the existing BIGNUMERIC test, then run the check command from the project harness.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145510-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[332 chars elided]…
  \"duckdb\": \"SELECT CAST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"DECLARE x {type_}(76, 38)\",\n                    write={\n                        \"bigquery\": \"DECLARE x BIGNUMERIC(76, 38)\",\n                        \"duckdb\": \"DECLARE x DECIMAL(76, 38)\",\n                    },\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145510-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run BigQuery and DuckDB dialect tests"}
[tool_result] ................................................................... [ 65%]
.......................... [ 91%]
.........                                              [100%]
102 passed, 1653 subtests passed in 0.62s
[assistant] Targeted tests pass. Now the full suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('DECLARE x BIGNUMERIC(76, 38)', read='bigquery', write='duckdb'))\nprint(sqlglot.transpile('SELECT CAST(1 AS BIGDECIMAL)', read='bigquery', write='duckdb'))\"", "description": "Run full test suite and spot-check outputs"}
[tool_result] ........... [ 19%]
............................................................... [ 25%]
....................................................................... [ 31%]
......................... [ 34%]
...................................................................................... [ 41%]
............................................................... [ 47%]
............................... [ 50%]
..............................................................................................
…[155 chars elided]…
..................... [ 74%]
............................................. [ 78%]
........................................................... [ 83%]
............. [ 84%]
......................................................................... [ 91%]
.................................................................................................                        [100%]
1105 passed, 17952 subtests passed in 62.99s (0:01:02)
['DECLARE x DECIMAL(76, 38)']
['SELECT CAST(1 AS DECIMAL(38, 5))']
[assistant] BigQuery `BIGNUMERIC` / `BIGDECIMAL` with explicit parameters now transpiles to DuckDB using only those parameters. `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`, not the concatenated form. The default mapping is still used when no parameters are given.

**The change**
- `sqlglot/generators/duckdb.py`: added a `datatype_sql` override. When the type is `BIGDECIMAL` and has parameters, it emits `DECIMAL(<params>)`. Otherwise it defers to the base class, so `DECIMAL(38, 5)` from `TYPE_MAPPING` still applies.
- `tests/dialects/test_bigquery.py`: extended `test_bignumeric` to c
…[73 chars elided]…
 or weaken any existing assertions.

**Verification**
- Before the fix, the reported output reproduced exactly (`DECLARE x DECIMAL(38, 5)(76, 38)`).
- `test_bigquery.py` and `test_duckdb.py`: 102 passed.
- Full suite: 1105 passed, 17952 subtests passed.

I did not commit. The changes are in the working tree.

**Something to decide:** DuckDB's `DECIMAL` caps precision at 38, so `DECIMAL(76, 38)` is valid SQL text but will fail when DuckDB executes it. I followed your rule and emit the user's parameters as given. If you'd rather clamp or warn when precision exceeds 38, that is a small follow-up.
