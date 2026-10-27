# trajectory base-1

final message:
BigQuery → DuckDB now emits the user's parameters for `BIGNUMERIC` / `BIGDECIMAL` instead of appending them to the default. `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`, and a bare `BIGNUMERIC` still becomes `DECIMAL(38, 5)`.

**Cause:** the DuckDB `TYPE_MAPPING` maps `BIGDECIMAL` to the fixed string `DECIMAL(38, 5)`, and the base `datatype_sql` then appends the explicit `(76, 38)`.

**Fix** (`sqlglot/generators/duckdb.py`): I added a `datatype_sql` override. When the type is `BIGDECIMAL` and has parameters, it generates a `DECIMAL` with those parameters; otherwise it uses the default mapping. The `TYPE_MAPPING` entry is unchanged.

**Tests** (`tests/dialects/test_bigquery.py`): added a DuckDB assertion for `CAST(1 AS BIGNUMERIC(76, 38))` and `BIGDECIMAL(76, 38)` → `DECIMAL(76, 38)`. The existing default-mapping assertions still pass.

**Verification:** the BigQuery and DuckDB dialect suites pass, the full suite passes (1105 tests), and ruff check and format are clean.

Two things to be aware of:
- **DuckDB caps DECIMAL precision at 38.** `BIGNUMERIC(76, 38)` is valid in BigQuery but will fail when run on DuckDB. I followed your spec, so this only surfaces when the SQL executes.
- **BigQuery's own generator drops parameters on `BIGNUMERIC`** (`CAST(1 AS BIGNUMERIC(76, 38))` round-trips as `BIGNUMERIC`). That is pre-existing and outside this fix, so I left it alone and kept my test to the DuckDB output.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"bignumeric\\|bigdecimal\" sqlglot/ | head -50", "description": "Search for BIGNUMERIC handling in sqlglot"}
[tool_result] sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
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
[tool_use Bash] {"command": "sed -n 1725,1760p sqlglot/generators/duckdb.py && grep -n \"def datatype_sql\\|DataType.Type.DECIMAL\\|DType.DECIMAL\\|TYPE_MAPPING\" sqlglot/generators/duckdb.py sqlglot/generator.py | head -30 && sed -n 400,430p sqlglot/generators/bigquery.py", "description": "Inspect DuckDB type mapping and datatype generation"}
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
  
…[1663 chars elided]…
OOL",
        exp.DType.CHAR: "STRING",
        exp.DType.DECIMAL: "NUMERIC",
        exp.DType.DOUBLE: "FLOAT64",
        exp.DType.FLOAT: "FLOAT64",
        exp.DType.INT: "INT64",
        exp.DType.NCHAR: "STRING",
        exp.DType.NVARCHAR: "STRING",
        exp.DType.SMALLINT: "INT64",
        exp.DType.TEXT: "STRING",
        exp.DType.TIMESTAMP: "DATETIME",
        exp.DType.TIMESTAMPNTZ: "DATETIME",
        exp.DType.TIMESTAMPTZ: "TIMESTAMP",
        exp.DType.TIMESTAMPLTZ: "TIMESTAMP",
[tool_use Bash] {"command": "sed -n 1635,1700p sqlglot/generator.py && grep -n \"DECIMAL\" sqlglot/generators/duckdb.py | head; grep -n -i \"bignumeric\\|bigdecimal\" tests/dialects/*.py | head -30; python3 -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'DECLARE x BIGNUMERIC', 'CAST(x AS BIGNUMERIC(10,2))']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\" 2>&1 | tail -5", "description": "Read datatype_sql and reproduce the bug"}
[tool_result]         specifier = self.sql(expression, "expression")
        specifier = f" {specifier}" if specifier and self.DATA_TYPE_SPECIFIERS_ALLOWED else ""
        return f"{this}{specifier}"

    def datatype_sql(self, expression: exp.DataType) -> str:
        nested = ""
        values = ""

        expr_nested = expression.args.get("nested")
        interior = (
            self.expressions(
                expression, dynamic=True, new_line=True, skip_first=True, skip_last=True
            )
     
…[3038 chars elided]…
          "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
tests/dialects/test_singlestore.py:711:                "bigquery": "CREATE TABLE testTypes (a BIGDECIMAL(10, 20))",
tests/dialects/test_snowflake.py:2424:                "bigquery": "SELECT CAST(1 AS BIGDECIMAL), CAST(1 AS BIGNUMERIC)",
['DECLARE x DECIMAL(38, 5)(76, 38)']
['DECLARE x DECIMAL(38, 5)']
['CAST(x AS DECIMAL(38, 5)(10, 2))']
[assistant] Reproduced: the DuckDB type mapping and the explicit parameters are both emitted. Let me check the existing BigQuery test and how DECIMAL params render in DuckDB before changing anything.
[tool_use Bash] {"command": "sed -n 3812,3840p tests/dialects/test_bigquery.py; grep -n \"DECIMAL\" sqlglot/generator.py | head -5; python3 -c \"\nimport sqlglot\nfor s in ['DECLARE x NUMERIC(10, 2)', 'DECLARE x BIGNUMERIC(76)']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Read existing BIGNUMERIC test and check DECIMAL rendering"}
[tool_result]                     "duckdb", unsupported_level=ErrorLevel.RAISE
                )

    def test_bignumeric(self):
        # BIGDECIMAL is an alias of BIGNUMERIC
        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
            with self.subTest(f"Testing BigQuery's {type_}"):
                self.validate_all(
                    f"SELECT {type_} '1'",
                    write={
                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST('1
…[70 chars elided]…
           self.validate_all(
                    f"SELECT CAST(1 AS {type_})",
                    write={
                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST(1 AS DECIMAL(38, 5))",
                    },
                )
['DECLARE x DECIMAL(10, 2)']
['DECLARE x DECIMAL(38, 5)(76)']
<work>/env-sqlglot/bin/python
[assistant] The root cause is that `TYPE_MAPPING` maps `BIGDECIMAL` to a fixed `DECIMAL(38, 5)` string, and the base `datatype_sql` then appends the explicit parameters. I'll override `datatype_sql` in the DuckDB generator so that a parameterised BIGDECIMAL is emitted as DECIMAL with the user's parameters, and the default mapping applies only when there are none.
[tool_use Bash] {"command": "grep -n \"    def [a-z_]*_sql\" sqlglot/generators/duckdb.py | head -8", "description": "Find method insertion point in DuckDB generator"}
[tool_result] 334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:    def bitmapbitposition_sql(self, expression: exp.BitmapBitPosition) -> str:
2268:    def bitmapconstructagg_sql(self, expression: exp.BitmapConstructAgg) -> str:
2282:    def compress_sql(self, expression: exp.Compress) -> str:
2286:    def encrypt_sql(self, expression: exp.Encrypt) -> str:
[tool_use Bash] {"command": "sed -n 2170,2184p sqlglot/generators/duckdb.py", "description": "Read code around insertion point"}
[tool_result]             WHEN :delimiter = '' THEN NULL
            WHEN :part_index < 0 THEN NULL
            WHEN :string IS NULL OR :delimiter IS NULL OR :part_index IS NULL THEN NULL
            ELSE :base_func
        END
        """
    )

    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
        return self.sql(
            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
        )

    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def timeslice_sql(self, expression: exp.TimeSlice) -> str:", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.this == exp.DType.BIGDECIMAL and expression.expressions:\n            expression = exp.DataType(this=exp.DType.DECIMAL, expressions=expression.expressions)\n        return super().datatype_sql(expression)\n\n    def timeslice_sql(self, expression: exp.TimeSlice) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll add tests covering the parameterised case alongside the existing default-mapping test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[360 chars elided]…
T(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'DECLARE x BIGNUMERIC', 'DECLARE x BIGNUMERIC(76)', 'CAST(x AS BIGDECIMAL(10,2))']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Verify output and run BigQuery and DuckDB dialect tests"}
[tool_result] ['DECLARE x DECIMAL(76, 38)']
['DECLARE x DECIMAL(38, 5)']
['DECLARE x DECIMAL(76)']
['CAST(x AS DECIMAL(10, 2))']
E   AssertionError: 'SELECT CAST(1 AS BIGNUMERIC)' != 'SELECT CAST(1 AS BIGNUMERIC(76, 38))'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
_ TestBigQuery.test_bignumeric [SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionE
…[77 chars elided]…
'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT CAST(1 AS BIGNUMERIC(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
SUBFAILED[SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
2 failed, 102 passed, 1649 subtests passed in 0.61s
[assistant] The DuckDB output is now correct. The two failures are in my new test's BigQuery round-trip: the BigQuery generator already drops parameters on `BIGNUMERIC` (pre-existing, outside this fix), so I'll narrow the assertion to the DuckDB output the fix is about.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },", "new_string": "                    write={\"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-202725-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run BigQuery/DuckDB tests then full suite"}
[tool_result] ........................................ [ 39%]
..............................................................                                                [100%]
102 passed, 1651 subtests passed in 0.45s
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 51.54s
[assistant] Both dialect suites and the full suite pass. I'll run the linter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && $PY/ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git -C . diff --stat", "description": "Lint and format-check changed files, show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generators/duckdb.py    | 5 +++++
 tests/dialects/test_bigquery.py | 5 +++++
 2 files changed, 10 insertions(+)
[assistant] BigQuery → DuckDB now emits the user's parameters for `BIGNUMERIC` / `BIGDECIMAL` instead of appending them to the default. `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`, and a bare `BIGNUMERIC` still becomes `DECIMAL(38, 5)`.

**Cause:** the DuckDB `TYPE_MAPPING` maps `BIGDECIMAL` to the fixed string `DECIMAL(38, 5)`, and the base `datatype_sql` then appends the explicit `(76, 38)`.

**Fix** (`sqlglot/generators/duckdb.py`): I added a `datatype_sql` override. When the type is `BIGDECIMAL` and has parameters, it generates a `DECIMAL` with those parameters; otherwise it use
…[275 chars elided]…
ification:** the BigQuery and DuckDB dialect suites pass, the full suite passes (1105 tests), and ruff check and format are clean.

Two things to be aware of:
- **DuckDB caps DECIMAL precision at 38.** `BIGNUMERIC(76, 38)` is valid in BigQuery but will fail when run on DuckDB. I followed your spec, so this only surfaces when the SQL executes.
- **BigQuery's own generator drops parameters on `BIGNUMERIC`** (`CAST(1 AS BIGNUMERIC(76, 38))` round-trips as `BIGNUMERIC`). That is pre-existing and outside this fix, so I left it alone and kept my test to the DuckDB output.

I did not commit anything.
