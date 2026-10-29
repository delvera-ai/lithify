# trajectory base-1

final message:
Parameterised `BIGNUMERIC` / `BIGDECIMAL` now generate only the supplied parameters for DuckDB, and the default `DECIMAL(38, 5)` applies only when none are given.

```
DECLARE x BIGNUMERIC(76, 38)  →  DECLARE x DECIMAL(76, 38)
DECLARE x BIGNUMERIC          →  DECLARE x DECIMAL(38, 5)
CAST(x AS BIGNUMERIC(20))     →  CAST(x AS DECIMAL(20))
```

**Cause:** the DuckDB `TYPE_MAPPING` for `BIGDECIMAL` was `DECIMAL(38, 5)`, and the generic `datatype_sql` appended the parsed parameters after it.

**Change** (`sqlglot/generators/duckdb.py`):
- `TYPE_MAPPING[BIGDECIMAL]` is now the bare `DECIMAL`.
- A new `datatype_sql` override swaps in `DECIMAL(38, 5)` only when a `BIGDECIMAL` has no parameters, then defers to the base implementation.

**Test** (`tests/dialects/test_bigquery.py`, `test_bignumeric`): I added a case for `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` expecting `DECIMAL(76, 38)` in DuckDB. I did not edit existing assertions.

**Verification:** full suite passes (1105 tests, 17950 subtests), and `ruff check` and `ruff format --check` are clean on both files.

BigQuery's own generator still drops the parameters when round-tripping `BIGNUMERIC(76, 38)`. That is existing behaviour outside this issue, so I left it alone and kept the new test to the DuckDB output only.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n -i \"bignumeric\\|bigdecimal\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/expressions.py | head -50", "description": "Find BIGNUMERIC handling in dialect code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
[tool_use Bash] {"command": "grep -rn -i \"BIGNUMERIC\\|BIGDECIMAL\" sqlglot/ | grep -v \"\\.pyc\" | head -60", "description": "Search all sqlglot sources for BIGNUMERIC"}
[tool_result] sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/typing/bigquery.py:16:    |  INPUT  | INT64   | NUMERIC | BIGNUMERIC | FLOAT64 |
sqlglot/typing/bigquery.py:18:    |  OUTPUT | FLOAT64 | NUMERIC | BIGNUMERIC | FLOAT64 |
sqlglot/typing
…[1213 chars elided]…
ons/datatypes.py:264:        DType.BIGDECIMAL,
sqlglot/expressions/datatypes.py:295:        DType.BIGDECIMAL,
sqlglot/expressions/string.py:577:class ParseBignumeric(Expression, Func):
sqlglot/generators/singlestore.py:343:        exp.DType.BIGDECIMAL: "DECIMAL",
sqlglot/generators/bigquery.py:413:        exp.DType.BIGDECIMAL: "BIGNUMERIC",
sqlglot/generators/snowflake.py:647:        exp.DType.BIGDECIMAL: "DOUBLE",
sqlglot/generators/duckdb.py:1745:        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
[tool_use Bash] {"command": "sed -n 1725,1800p sqlglot/generators/duckdb.py; grep -n \"TYPE_MAPPING\\|def datatype_sql\" sqlglot/generators/duckdb.py | head; grep -n \"def datatype_sql\" -A60 sqlglot/generator.py | head -120", "description": "Inspect DuckDB type mapping and datatype_sql"}
[tool_result]     TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.BINARY: "BLOB",
        exp.DType.BPCHAR: "TEXT",
        exp.DType.CHAR: "TEXT",
        exp.DType.DATETIME: "TIMESTAMP",
        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
        exp.DType.FLOAT: "REAL",
        exp.DType.JSONB: "JSON",
        exp.DType.NCHAR: "TEXT",
        exp.DType.NVARCHAR: "TEXT",
        exp.DType.UINT: "UINTEGER",
        exp.DType.VARBINARY: "BLOB",
        exp.DType.ROWVERSION: "BLOB",
  
…[3790 chars elided]…
 directory_sql(self, expression: exp.Directory) -> str:
1692-        local = "LOCAL " if expression.args.get("local") else ""
1693-        row_format = self.sql(expression, "row_format")
1694-        row_format = f" {row_format}" if row_format else ""
1695-        return f"{local}DIRECTORY {self.sql(expression, 'this')}{row_format}"
1696-
1697-    def delete_sql(self, expression: exp.Delete) -> str:
1698-        hint = self.sql(expression, "hint")
1699-        this = self.sql(expression, "this")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'DECLARE x BIGNUMERIC', 'SELECT CAST(x AS BIGNUMERIC(76, 38))', 'SELECT CAST(x AS BIGDECIMAL)']:\n    e = sqlglot.parse_one(s, read='bigquery')\n    print(repr(e.sql('duckdb')))\n\"; grep -rn -i \"bignumeric\\|bigdecimal\" tests/dialects/*.py | head -30", "description": "Reproduce BIGNUMERIC generation to DuckDB and check tests"}
[tool_result] 'DECLARE x DECIMAL(38, 5)(76, 38)'
'DECLARE x DECIMAL(38, 5)'
'SELECT CAST(x AS DECIMAL(38, 5)(76, 38))'
'SELECT CAST(x AS DECIMAL(38, 5))'
tests/dialects/test_bigquery.py:223:        self.validate_identity("CAST(x AS BIGNUMERIC)")
tests/dialects/test_bigquery.py:1924:        self.validate_identity("PARSE_BIGNUMERIC('1.2')")
tests/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_b
…[15 chars elided]…
:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
tests/dialects/test_snowflake.py:2424:                "bigquery": "SELECT CAST(1 AS BIGDECIMAL), CAST(1 AS BIGNUMERIC)",
tests/dialects/test_singlestore.py:711:                "bigquery": "CREATE TABLE testTypes (a BIGDECIMAL(10, 20))",
[assistant] Reproduced: the DuckDB `TYPE_MAPPING` entry `DECIMAL(38, 5)` is emitted and then the parsed `(76, 38)` is appended. I'll map `BIGDECIMAL` to the bare `DECIMAL` and only fall back to `(38, 5)` when no parameters are given.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.DType.BIGDECIMAL: \"DECIMAL(38, 5)\",\n    }", "new_string": "        exp.DType.BIGDECIMAL: \"DECIMAL\",\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def .*_sql(self, expression: exp.DataType\\|def cast_sql\\|def datatype_sql\" sqlglot/generators/duckdb.py | head", "description": "Check existing DuckDB datatype overrides"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"^    def \\|^class \" sqlglot/generators/duckdb.py | sed -n 1,12p", "description": "List DuckDB generator method definitions"}
[tool_result] 334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
704:    def replace_seq(node: exp.Expr) -> exp.Expr:
1455:class DuckDBGenerator(generator.Generator):
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:    def bitmapbitposition_sql(self, expression: exp.BitmapBitPosition) -> str:
2268:    def bitmapconstructagg_sql(self, expression: exp.BitmapConstructAgg) -> str:
2282:    def compress_sql(self, expression: exp.Compress) -> str:
2286:    def encrypt_sql(self, expression: exp.Encrypt) -> str:
2290:    def decrypt_sql(self, expression: exp.Decrypt) -> str:
2295:    def decryptraw_sql(self, expression: exp.DecryptRaw) -> str:
[tool_use Bash] {"command": "sed -n 2176,2184p sqlglot/generators/duckdb.py", "description": "View code around insertion point"}
[tool_result]     )

    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
        return self.sql(
            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
        )

    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:\n        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))\n        return self.sql(\n  
…[324 chars elided]…
sql(\n            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)\n        )\n\n    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.BIGDECIMAL) and not expression.expressions:\n            expression = exp.DataType.build(\"DECIMAL(38, 5)\", dialect=self.dialect)\n        return super().datatype_sql(expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'DECLARE x BIGNUMERIC', 'SELECT CAST(x AS BIGNUMERIC(76, 38))', 'SELECT CAST(x AS BIGDECIMAL)', 'SELECT CAST(x AS BIGNUMERIC(20))']:\n    e = sqlglot.parse_one(s, read='bigquery')\n    print(repr(e.sql('duckdb')))\n\"", "description": "Verify BIGNUMERIC generation to DuckDB after fix"}
[tool_result] 'DECLARE x DECIMAL(76, 38)'
'DECLARE x DECIMAL(38, 5)'
'SELECT CAST(x AS DECIMAL(76, 38))'
'SELECT CAST(x AS DECIMAL(38, 5))'
'SELECT CAST(x AS DECIMAL(20))'
[assistant] The fix works for all cases. Now I'll add a regression test next to the existing BIGNUMERIC test and run the checks.
[tool_use Bash] {"command": "sed -n 3815,3840p tests/dialects/test_bigquery.py", "description": "View existing BIGNUMERIC test"}
[tool_result]     def test_bignumeric(self):
        # BIGDECIMAL is an alias of BIGNUMERIC
        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
            with self.subTest(f"Testing BigQuery's {type_}"):
                self.validate_all(
                    f"SELECT {type_} '1'",
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[356 chars elided]…
AST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ............................................. [ 78%]
........................................................... [ 83%]
........................... [ 86%]
.......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
=================================== FAILURES ===================================
_ TestBigQuery.test_bignumeric [SELECT CAST(1 AS BIGNUMERIC(7
…[562 chars elided]…
   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT CAST(1 AS BIGNUMERIC(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
SUBFAILED[SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
2 failed, 1105 passed, 17948 subtests passed in 52.64s
[assistant] Two failures, both in my new test: BigQuery's own generator drops the parameters for `BIGNUMERIC`. That's existing BigQuery behaviour and outside this issue, so I'll only assert the DuckDB output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },", "new_string": "                    write={\"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175952-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py 2>&1 | tail -2; git status --short", "description": "Rerun tests, lint, and format check", "timeout": 900000}
[tool_result] .......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 51.96s
All checks passed!
2 files already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] Parameterised `BIGNUMERIC` / `BIGDECIMAL` now generate only the supplied parameters for DuckDB, and the default `DECIMAL(38, 5)` applies only when none are given.

```
DECLARE x BIGNUMERIC(76, 38)  →  DECLARE x DECIMAL(76, 38)
DECLARE x BIGNUMERIC          →  DECLARE x DECIMAL(38, 5)
CAST(x AS BIGNUMERIC(20))     →  CAST(x AS DECIMAL(20))
```

**Cause:** the DuckDB `TYPE_MAPPING` for `BIGDECIMAL` was `DECIMAL(38, 5)`, and the generic `datatype_sql` appended the parsed parameters after it.

**Change** (`sqlglot/generators/duckdb.py`):
- `TYPE_MAPPING[BIGDECIMAL]` is now the bare `DECIMAL`.
- A 
…[111 chars elided]…
o the base implementation.

**Test** (`tests/dialects/test_bigquery.py`, `test_bignumeric`): I added a case for `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` expecting `DECIMAL(76, 38)` in DuckDB. I did not edit existing assertions.

**Verification:** full suite passes (1105 tests, 17950 subtests), and `ruff check` and `ruff format --check` are clean on both files.

BigQuery's own generator still drops the parameters when round-tripping `BIGNUMERIC(76, 38)`. That is existing behaviour outside this issue, so I left it alone and kept the new test to the DuckDB output only.

Nothing is committed.
