# trajectory base-1

final message:
BigQuery `BIGNUMERIC`/`BIGDECIMAL` with explicit parameters now transpiles to DuckDB with only those parameters, and the default `DECIMAL(38, 5)` is used only when none are given. The full suite passes (1105 passed, 17950 subtests).

```
DECLARE x BIGNUMERIC(76, 38)  ->  DECLARE x DECIMAL(76, 38)     (was DECIMAL(38, 5)(76, 38))
DECLARE x BIGNUMERIC          ->  DECLARE x DECIMAL(38, 5)      (unchanged)
CAST(x AS BIGDECIMAL(10))     ->  CAST(x AS DECIMAL(10))
```

Changes:
- **`sqlglot/generators/duckdb.py`**: a new `datatype_sql` override. If the type is `BIGDECIMAL` and has parameters, it emits `DECIMAL(<params>)`. Otherwise it falls through to the base implementation, which keeps the default mapping.
- **`tests/dialects/test_bigquery.py`**: added a DuckDB assertion for `BIGNUMERIC(76, 38)` and its `BIGDECIMAL` alias inside the existing `test_bignumeric`. I did not add a BigQuery-side expectation.

Out of scope: BigQuery's own generator drops the parameters when writing `BIGNUMERIC(76, 38)` back to BigQuery (`CAST(1 AS BIGNUMERIC)`). That is a separate issue in the BigQuery generator, and I left it alone. I did not commit.

## events
[tool_use Bash] {"command": "grep -rn \"BIGNUMERIC\\|BIGDECIMAL\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/tokens.py sqlglot/expressions.py | head -40; grep -rn \"76, 38\\|(76\" sqlglot/ | head", "description": "Locate BIGNUMERIC handling in dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
[tool_use Bash] {"command": "grep -rn \"BIGDECIMAL\" sqlglot/ | grep -v \"^sqlglot/tokens.py\" ; rtk git status 2>/dev/null | head -3; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('DECLARE x BIGNUMERIC(76, 38)', read='bigquery', write='duckdb'))\nprint(sqlglot.transpile('DECLARE x BIGNUMERIC', read='bigquery', write='duckdb'))\nprint(sqlglot.transpile('CAST(x AS BIGNUMERIC(76, 38))', read='bigquery', write='duckdb'))\nprint(sqlglot.transpile('CAST(x AS BIGDECIMAL(10, 2))', read='bigquery', write='duckdb'))\n\"", "description": "Find BIGDECIMAL usages and reproduce the bug"}
[tool_result] sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/typing/bigquery.py:360:    exp.ParseBignumeric: {"returns": exp.DType.BIGDECIMAL},
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType
…[177 chars elided]…
sqlglot/expressions/datatypes.py:264:        DType.BIGDECIMAL,
sqlglot/expressions/datatypes.py:295:        DType.BIGDECIMAL,
sqlglot/generators/singlestore.py:343:        exp.DType.BIGDECIMAL: "DECIMAL",
sqlglot/generators/bigquery.py:413:        exp.DType.BIGDECIMAL: "BIGNUMERIC",
sqlglot/generators/snowflake.py:647:        exp.DType.BIGDECIMAL: "DOUBLE",
['DECLARE x DECIMAL(38, 5)(76, 38)']
['DECLARE x DECIMAL(38, 5)']
['CAST(x AS DECIMAL(38, 5)(76, 38))']
['CAST(x AS DECIMAL(38, 5)(10, 2))']
[tool_use Bash] {"command": "sed -n 1730,1760p sqlglot/generators/duckdb.py; grep -n \"def datatype_sql\" -A40 sqlglot/generator.py; grep -n \"def datatype_sql\" -A30 sqlglot/generators/duckdb.py", "description": "Inspect DuckDB type mapping and datatype_sql"}
[tool_result]         exp.DType.DATETIME: "TIMESTAMP",
        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
        exp.DType.FLOAT: "REAL",
        exp.DType.JSONB: "JSON",
        exp.DType.NCHAR: "TEXT",
        exp.DType.NVARCHAR: "TEXT",
        exp.DType.UINT: "UINTEGER",
        exp.DType.VARBINARY: "BLOB",
        exp.DType.ROWVERSION: "BLOB",
        exp.DType.VARCHAR: "TEXT",
        exp.DType.TIMESTAMPLTZ: "TIMESTAMPTZ",
        exp.DType.TIMESTAMPNTZ: "TIMESTAMP",
        exp.DType.TIMESTAMP_S: "TIMESTAM
…[1950 chars elided]…
IMITER[0]}{interior}{self.STRUCT_DELIMITER[1]}"
1673-                if expression.args.get("values") is not None:
1674-                    delimiters = ("[", "]") if type_value == exp.DType.ARRAY else ("(", ")")
1675-                    values = self.expressions(expression, key="values", flat=True)
1676-                    values = f"{delimiters[0]}{values}{delimiters[1]}"
1677-            elif type_value == exp.DType.INTERVAL:
1678-                nested = f" {interior}"
1679-            else:
[tool_use Bash] {"command": "sed -n 1679,1700p sqlglot/generator.py; grep -n \"TYPE_MAPPING\" sqlglot/generators/duckdb.py; grep -n \"DECIMAL\" sqlglot/generators/duckdb.py | head -20; grep -n \"BIGNUMERIC\\|bignumeric\" -i tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head", "description": "Read rest of datatype_sql and related tests"}
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
…[890 chars elided]…
elf.validate_identity("PARSE_BIGNUMERIC('1.2')")
tests/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
[tool_use Bash] {"command": "sed -n 3815,3845p tests/dialects/test_bigquery.py; sed -n 2440,2460p sqlglot/generators/duckdb.py; grep -n \"    def .*_sql\" sqlglot/generators/duckdb.py | head -5", "description": "Read existing BIGNUMERIC tests and duckdb method style"}
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

                sel
…[1026 chars elided]…
        Handle GREATEST/LEAST functions with dialect-aware NULL behavior.
334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:    def bitmapbitposition_sql(self, expression: exp.BitmapBitPosition) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def tonumber_sql(self, expression: exp.ToNumber) -> str:", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.this == exp.DType.BIGDECIMAL and expression.expressions:\n            return f\"DECIMAL({self.expressions(expression, flat=True)})\"\n        return super().datatype_sql(expression)\n\n    def tonumber_sql(self, expression: exp.ToNumber) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a regression test next to the existing BIGNUMERIC cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[356 chars elided]…
AST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)','DECLARE x BIGNUMERIC','CAST(x AS BIGDECIMAL(10))','CAST(x AS BIGNUMERIC(10, 2))']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] ['DECLARE x DECIMAL(76, 38)']
['DECLARE x DECIMAL(38, 5)']
['CAST(x AS DECIMAL(10))']
['CAST(x AS DECIMAL(10, 2))']
E   AssertionError: 'SELECT CAST(1 AS BIGNUMERIC)' != 'SELECT CAST(1 AS BIGNUMERIC(76, 38))'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
_ TestBigQuery.test_bignumeric [SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   Assertion
…[81 chars elided]…
   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT CAST(1 AS BIGNUMERIC(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
SUBFAILED[SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
2 failed, 1105 passed, 17948 subtests passed in 51.01s
[assistant] The DuckDB output is now correct. The two failures come from my test: BigQuery's own generator drops the parameters on `BIGNUMERIC`, which is outside this request, so I'll assert only the DuckDB side.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },", "new_string": "                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085840-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short", "description": "Rerun full test suite and show changed files"}
[tool_result] ................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 49.00s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] BigQuery `BIGNUMERIC`/`BIGDECIMAL` with explicit parameters now transpiles to DuckDB with only those parameters, and the default `DECIMAL(38, 5)` is used only when none are given. The full suite passes (1105 passed, 17950 subtests).

```
DECLARE x BIGNUMERIC(76, 38)  ->  DECLARE x DECIMAL(76, 38)     (was DECIMAL(38, 5)(76, 38))
DECLARE x BIGNUMERIC          ->  DECLARE x DECIMAL(38, 5)      (unchanged)
CAST(x AS BIGDECIMAL(10))     ->  CAST(x AS DECIMAL(10))
```

Changes:
- **`sqlglot/generators/duckdb.py`**: a new `datatype_sql` override. If the type is `BIGDECIMAL` and has parameters, it emits `DECIMAL(<params>)`. Otherwise it falls through to the base implementation, which keeps the default mapping.
- **`tests/dialects/test_bigquery.py`**: added a DuckDB assertion for `BIGNUMERIC(76, 38)` and its `BIGDECIMAL` alias inside the existing `test_bignumeric`. I did not add a BigQuery-side expectation.

Out of scope: BigQuery's own generator drops the parameters when writing `BIGNUMERIC(76, 38)` back to BigQuery (`CAST(1 AS BIGNUMERIC)`). That is a separate issue in the BigQuery generator, and I left it alone. I did not commit.
