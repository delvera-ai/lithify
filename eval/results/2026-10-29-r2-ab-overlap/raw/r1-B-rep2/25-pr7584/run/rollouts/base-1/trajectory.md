# trajectory base-1

final message:
Parameterised BigQuery `BIGNUMERIC` / `BIGDECIMAL` types now generate only the explicit parameters for DuckDB. `BIGNUMERIC(76, 38)` becomes `DECIMAL(76, 38)` instead of `DECIMAL(38, 5)(76, 38)`. Without parameters, the default `DECIMAL(38, 5)` mapping still applies. The full suite passes (1105 tests) and ruff is clean.

**Change:** I added a `datatype_sql` override to `DuckDBGenerator` in `sqlglot/generators/duckdb.py`. When the type is `BIGDECIMAL` and has parameters, it rewrites the type to `DECIMAL` before calling the base method. This follows the existing `datatype_sql` override pattern in the Postgres generator.

**Test:** I added a DuckDB case to `test_bignumeric` in `tests/dialects/test_bigquery.py`. It covers both the `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` spellings.

**Choices you may want to revisit:**
- The BigQuery writer still drops the parameters when it re-emits the type (`BIGNUMERIC(76, 38)` → `BIGNUMERIC`). That is existing behaviour and outside this request, so I left it alone and kept the test to the DuckDB output.
- DuckDB caps `DECIMAL` at 38 digits. Per your instruction, `BIGNUMERIC(76, 38)` is emitted as `DECIMAL(76, 38)`, which DuckDB will reject at execution time. I did not clamp it.

## events
[tool_use Bash] {"command": "grep -rn -i \"bignumeric\\|BIGDECIMAL\" sqlglot/ | head -50", "description": "Locate BIGNUMERIC handling in sqlglot"}
[tool_result] sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
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
[tool_use Bash] {"command": "sed -n 1700,1800p sqlglot/generators/duckdb.py && grep -n \"def datatype_sql\" -A40 sqlglot/generator.py | head -80 && grep -n \"BIGDECIMAL\\|BIGNUMERIC\\|bignumeric\" -i tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head", "description": "Inspect DuckDB type mapping and generic datatype_sql"}
[tool_result]             exp.Extract(
                this=exp.Var(this="ISOYEAR"),
                expression=e.this,
            )
        ),
        exp.YearOfWeekIso: lambda self, e: self.sql(
            exp.Extract(
                this=exp.Var(this="ISOYEAR"),
                expression=e.this,
            )
        ),
        exp.Xor: _xor_sql,
        exp.JSONObjectAgg: rename_func("JSON_GROUP_OBJECT"),
        exp.JSONBObjectAgg: rename_func("JSON_GROUP_OBJECT"),
        exp.DateBin: rename_func("T
…[4194 chars elided]…
elf.validate_identity("PARSE_BIGNUMERIC('1.2')")
tests/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
[tool_use Bash] {"command": "sed -n 1679,1700p sqlglot/generator.py && sed -n 3812,3845p tests/dialects/test_bigquery.py && cat .lithify/harness/scripts/probe_parse.py | head -30 && printf \"CREATE TABLE t (x BIGNUMERIC(76, 38))\\nDECLARE x BIGNUMERIC(76, 38)\\nDECLARE x BIGNUMERIC\\nSELECT CAST(1 AS BIGNUMERIC(76, 38))\\n\" | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py 2>&1 | head -30", "description": "Read generator tail, existing tests, and probe current output"}
[tool_result]             else:
                nested = f"({interior})"

        type_sql = f"{type_sql}{nested}{values}"
        if self.TZ_TO_WITH_TIME_ZONE and type_value in (
            exp.DType.TIMETZ,
            exp.DType.TIMESTAMPTZ,
        ):
            type_sql = f"{type_sql} WITH TIME ZONE"

        return type_sql

    def directory_sql(self, expression: exp.Directory) -> str:
        local = "LOCAL " if expression.args.get("local") else ""
        row_format = self.sql(expression, "row_forma
…[2014 chars elided]…
ys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"import sqlglot,sys;print(sqlglot.__file__)\"; printf \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\\nSELECT CAST(1 AS BIGNUMERIC)\\nSELECT CAST(1 AS BIGDECIMAL(76, 38))\\n\" | PYTHONPATH=$PWD $P .lithify/harness/scripts/probe_parse.py --read bigquery --write duckdb 2>&1 | head -30", "description": "Probe current BigQuery to DuckDB output for parameterised BIGNUMERIC"}
[tool_result] ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/sqlglot/__init__.py
ERR       SELECT CAST(1 AS BIGNUMERIC(76, 38))
          output does not re-parse: ParseError: Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 34.
OK        SELECT CAST(1 AS BIGNUMERIC)
          SELECT CAST(1 AS DECIMAL(38, 5))
ERR       SELECT CAST(1 AS BIGDECIMAL(76, 38))
          output does not re-parse: ParseError: Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 34.
[tool_use Bash] {"command": "grep -n \"def datatype_sql\\|DECFLOAT\\|exp.DType.DECIMAL\" sqlglot/generators/duckdb.py sqlglot/generators/bigquery.py; grep -n \"def datatype_sql\" -A25 sqlglot/generators/duckdb.py", "description": "Check existing datatype handling in DuckDB generator"}
[tool_result ERROR] Exit code 1
3 matches in 2 files:

sqlglot/generators/bigquery.py:419:exp.DType.DECIMAL: "NUMERIC",
sqlglot/generators/duckdb.py:1731:exp.DType.DECFLOAT: "DECIMAL(38, 5)",
sqlglot/generators/duckdb.py:4181:exp.DType.DECIMAL,
[tool_use Bash] {"command": "grep -n \"    def .*_sql(self\" sqlglot/generators/duckdb.py | head -5; grep -n \"^class Generator\" sqlglot/generators/duckdb.py", "description": "Find method placement in DuckDB generator"}
[tool_result ERROR] Exit code 1
rg: regex parse error:
    (?:    def .*_sql(self)
    ^
error: unclosed group
0 matches for '    def .*_sql(self'
0 matches for '^class Generator'
[tool_use Bash] {"command": "grep -n \"    def [a-z_]*_sql(self\" sqlglot/generators/duckdb.py | head -5; grep -n \"class Generator\" sqlglot/generators/duckdb.py", "description": "Find method placement in DuckDB generator"}
[tool_result ERROR] Exit code 1
rg: regex parse error:
    (?:    def [a-z_]*_sql(self)
    ^
error: unclosed group
0 matches for '    def [a-z_]*_sql(self'
0 matches for 'class Generator'
[tool_use Bash] {"command": "rg -n \"def \\w+_sql\" sqlglot/generators/duckdb.py | head -5; rg -n \"class Generator\" sqlglot/generators/duckdb.py", "description": "Find method placement in DuckDB generator"}
[tool_result ERROR] Exit code 1
168 matches in 158 files:

1025:0:DuckDBGenerator, expression: exp.AnyValue) -> str:
1067:0:DuckDBGenerator, literal: str) -> str:
1150:0:DuckDBGenerator, expression: exp.Initcap) -> str:
0 matches for 'class Generator'
[tool_use Bash] {"command": "rg -n \"class DuckDBGenerator|    def \\w+\\(self\" sqlglot/generators/duckdb.py | head -40", "description": "List generator class and method definitions in DuckDB"}
[tool_result] 132 matches in 132 files:

1455:0:
2178:0:exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:0:exp.TimeSlice) -> str:
2220:0:exp.BitmapBucketNumber) -> str:
2245:0:exp.BitmapBitPosition) -> str:
2268:0:exp.BitmapConstructAgg) -> str:
2282:0:exp.Compress) -> str:
2286:0:exp.Encrypt) -> str:
2290:0:exp.Decrypt) -> str:
2295:0:exp.DecryptRaw) -> str:
2300:0:exp.EncryptRaw) -> str:
2304:0:exp.ParseUrl) -> str:
2308:0:exp.ParseIp) -> str:
2312:0:exp.DecompressString) -> str:
2316:0:exp.Decompress
…[257 chars elided]…
 -> str:
2482:0:exp.Generator) -> str:
2496:0:exp.Greatest) -> str:
2499:0:exp.Least) -> str:
2502:0:exp.Lambda, arrow_sep: str = "->", wrap: bool = True) -> str:
2513:0:exp.Show) -> str:
2518:0:exp.Soundex) -> str:
2522:0:exp.SortArray) -> str:
2549:0:exp.Install) -> str:
2556:0:exp.ApproxTopK) -> str:
2562:0:exp.FromISO8601Timestamp) -> str:
2565:0:exp.StrPosition) -> str:
2595:0:exp.Substring) -> str:
2609:0:exp.StrToTime) -> str:
2634:0:exp.StrToDate) -> str:
2644:0:exp.TsOrDsToTime) -> str:
[tool_use Bash] {"command": "awk '/^class |^    def /{print FILENAME\": \"FNR\": \"$0}' sqlglot/generators/duckdb.py | head -60", "description": "List class and method definitions in DuckDB generator"}
[tool_result] sqlglot/generators/duckdb.py: 334:     def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
sqlglot/generators/duckdb.py: 704:     def replace_seq(node: exp.Expr) -> exp.Expr:
sqlglot/generators/duckdb.py: 1455: class DuckDBGenerator(generator.Generator):
sqlglot/generators/duckdb.py: 2178:     def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
sqlglot/generators/duckdb.py: 2184:     def timeslice_sql(self, expression: exp.TimeS
…[5085 chars elided]…
p.Join) -> str:
sqlglot/generators/duckdb.py: 2994:     def countif_sql(self, expression: exp.CountIf) -> str:
sqlglot/generators/duckdb.py: 3001:     def bracket_sql(self, expression: exp.Bracket) -> str:
sqlglot/generators/duckdb.py: 3023:     def withingroup_sql(self, expression: exp.WithinGroup) -> str:
sqlglot/generators/duckdb.py: 3065:     def length_sql(self, expression: exp.Length) -> str:
sqlglot/generators/duckdb.py: 3092:     def bitlength_sql(self, expression: exp.BitLength) -> str:
[tool_use Bash] {"command": "awk '/def datatype_sql/{print FILENAME\": \"FNR}' sqlglot/generators/*.py sqlglot/generator.py; awk '/def datatype_sql/{f=1} f&&n<30{print; n++}' sqlglot/generators/postgres.py | head -30", "description": "Find existing datatype_sql overrides in generators"}
[tool_result] sqlglot/generators/clickhouse.py: 517
sqlglot/generators/dremio.py: 75
sqlglot/generators/exasol.py: 306
sqlglot/generators/fabric.py: 78
sqlglot/generators/hive.py: 432
sqlglot/generators/materialize.py: 35
sqlglot/generators/mysql.py: 628
sqlglot/generators/postgres.py: 477
sqlglot/generators/redshift.py: 325
sqlglot/generators/risingwave.py: 27
sqlglot/generators/singlestore.py: 1468
sqlglot/generators/snowflake.py: 686
sqlglot/generator.py: 1639
    def datatype_sql(self, expression: exp.Dat
…[820 chars elided]…
ance(this, exp.IntDiv) and expression.to == exp.DType.DECIMAL.into_expr():
            return self.sql(this)

        return super().cast_sql(expression, safe_prefix=safe_prefix)

    def array_sql(self, expression: exp.Array) -> str:
        exprs = expression.expressions
        func_name = self.normalize_func("ARRAY")

        if isinstance(seq_get(exprs, 0), exp.Select):
            return f"{func_name}({self.sql(exprs[0])})"

        return f"{func_name}{inline_array_sql(self, expression)}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "offset": 2176, "limit": 10}
[tool_result] 2176	    )
2177	
2178	    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2179	        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
2180	        return self.sql(
2181	            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
2182	        )
2183	
2184	    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2185	        """
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)\n        )\n\n    def timeslice_sql(", "new_string": "            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)\n        )\n\n    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.BIGDECIMAL) and expression.expressions:\n            expression = expression.copy()\n            expression.set(\"this\", exp.DType.DECIMAL)\n\n        return super().datatype_sql(expression)\n\n    def timeslice_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; printf \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\\nSELECT CAST(1 AS BIGDECIMAL(76, 38))\\nSELECT CAST(1 AS BIGNUMERIC)\\nDECLARE x BIGNUMERIC(76, 38)\\nDECLARE x BIGNUMERIC\\n\" | PYTHONPATH=$PWD $P .lithify/harness/scripts/probe_parse.py --read bigquery --write duckdb 2>&1 | head -30", "description": "Re-probe BigQuery to DuckDB output after fix"}
[tool_result] OK        SELECT CAST(1 AS BIGNUMERIC(76, 38))
          SELECT CAST(1 AS DECIMAL(76, 38))
OK        SELECT CAST(1 AS BIGDECIMAL(76, 38))
          SELECT CAST(1 AS DECIMAL(76, 38))
OK        SELECT CAST(1 AS BIGNUMERIC)
          SELECT CAST(1 AS DECIMAL(38, 5))
ERR       DECLARE x BIGNUMERIC(76, 38)
          output does not re-parse: ParseError: Invalid expression / Unexpected token. Line 1, Col: 17.
ERR       DECLARE x BIGNUMERIC
          output does not re-parse: ParseError: Invalid expression / Unexpected token. Line 1, Col: 17.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)','DECLARE x BIGNUMERIC','DECLARE x BIGDECIMAL(76, 38)']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"", "description": "Transpile DECLARE statements from BigQuery to DuckDB"}
[tool_result] ['DECLARE x DECIMAL(76, 38)']
['DECLARE x DECIMAL(38, 5)']
['DECLARE x DECIMAL(76, 38)']
[assistant] Output is correct for both cast and DECLARE forms. Now I'll add a regression test next to the existing BIGNUMERIC test.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "offset": 3826, "limit": 12}
[tool_result] 3826	
3827	                self.validate_all(
3828	                    f"SELECT CAST(1 AS {type_})",
3829	                    write={
3830	                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
3831	                        "duckdb": "SELECT CAST(1 AS DECIMAL(38, 5))",
3832	                    },
3833	                )
3834	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n    def test_", "new_string": "                        \"duckdb\": \"SELECT CAST(1 AS 
…[8 chars elided]…
38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )\n\n    def test_"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:                         "duckdb": "SELECT CAST(1 AS DECIMAL(38, 5))",
                    },
                )

    def test_</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n", "new_string"
…[124 chars elided]…
T(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite as final gate", "timeout": 400000}
[tool_result] E   AssertionError: 'SELECT CAST(1 AS BIGNUMERIC)' != 'SELECT CAST(1 AS BIGNUMERIC(76, 38))'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
_ TestBigQuery.test_bignumeric [SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: 'SELECT CAST(1 AS BIGNUMERIC)' != 'SELECT CAST(1 AS BIGNUMERIC(76, 38))'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT CAST(1 AS BIGNUMERIC(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
SUBFAILED[SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
2 failed, 1105 passed, 17948 subtests passed in 55.09s
[assistant] The BigQuery writer drops the parameters on its own output path, which is outside this request. I'll keep the test scoped to the DuckDB output the user asked about.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },", "new_string": "                    write={\"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151206-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; git status --short", "description": "Run full suite again and check changed files", "timeout": 400000}
[tool_result] .......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 54.10s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Parameterised BigQuery `BIGNUMERIC` / `BIGDECIMAL` types now generate only the explicit parameters for DuckDB. `BIGNUMERIC(76, 38)` becomes `DECIMAL(76, 38)` instead of `DECIMAL(38, 5)(76, 38)`. Without parameters, the default `DECIMAL(38, 5)` mapping still applies. The full suite passes (1105 tests) and ruff is clean.

**Change:** I added a `datatype_sql` override to `DuckDBGenerator` in `sqlglot/generators/duckdb.py`. When the type is `BIGDECIMAL` and has parameters, it rewrites the type to `DECIMAL` before calling the base method. This follows the existing `datatype_sql` override pattern in
…[34 chars elided]…
* I added a DuckDB case to `test_bignumeric` in `tests/dialects/test_bigquery.py`. It covers both the `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` spellings.

**Choices you may want to revisit:**
- The BigQuery writer still drops the parameters when it re-emits the type (`BIGNUMERIC(76, 38)` → `BIGNUMERIC`). That is existing behaviour and outside this request, so I left it alone and kept the test to the DuckDB output.
- DuckDB caps `DECIMAL` at 38 digits. Per your instruction, `BIGNUMERIC(76, 38)` is emitted as `DECIMAL(76, 38)`, which DuckDB will reject at execution time. I did not clamp it.
