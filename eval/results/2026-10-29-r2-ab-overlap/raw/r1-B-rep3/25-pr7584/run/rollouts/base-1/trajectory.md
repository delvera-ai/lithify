# trajectory base-1

final message:
Parameterised BigQuery `BIGNUMERIC` / `BIGDECIMAL` now transpiles to DuckDB with only the parameters the user gave. Before the fix, `(76, 38)` was appended to the default: `DECLARE x DECIMAL(38, 5)(76, 38)`. Now it produces `DECLARE x DECIMAL(76, 38)`. With no parameters, the default `DECIMAL(38, 5)` is unchanged.

The fix is a `datatype_sql` override in `sqlglot/generators/duckdb.py`. When a `BIGDECIMAL` type has explicit parameters, it renders them as a plain `DECIMAL(p, s)`. Otherwise it falls through to the existing default mapping.

I added one `validate_all` case to `test_bignumeric` in `tests/dialects/test_bigquery.py` covering `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` → DuckDB. The existing assertions are untouched.

The full suite passes (1105 passed) and ruff check and format are clean on the changed files.

One thing I did not change: the BigQuery generator drops the parameters when writing `BIGNUMERIC` back out (`CAST(1 AS BIGNUMERIC(76, 38))` → `CAST(1 AS BIGNUMERIC)`). That is existing behaviour and outside this request, so my test asserts only the DuckDB side. Say if you want the BigQuery round-trip fixed too.

## events
[tool_use Bash] {"command": "grep -n -i \"bignumeric\\|bigdecimal\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn -i \"bignumeric\\|bigdecimal\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -30", "description": "Locate BIGNUMERIC handling in code and tests"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
tests/dialects/test_bigquery.py:223:        self.validate_identity("CAST(x AS BIGNUMERIC)")
tests/dialects/test_bigquery.py:1924:        self.validate_identity("PARSE_BIGNUMERIC('1.2')")
tests/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
[tool_use Bash] {"command": "sed -n 3810,3850p tests/dialects/test_bigquery.py; grep -n \"BIGDECIMAL\\|BIGNUMERIC\\|76, 38\" sqlglot/dialects/*.py sqlglot/*.py | head -40; grep -n \"BIGDECIMAL\\|BIGNUMERIC\" -r sqlglot | head -40", "description": "Inspect existing BIGNUMERIC test and mappings"}
[tool_result]             with self.assertRaises(UnsupportedError):
                self.parse_one("APPROX_QUANTILES(x, 2 RESPECT NULLS)").sql(
                    "duckdb", unsupported_level=ErrorLevel.RAISE
                )

    def test_bignumeric(self):
        # BIGDECIMAL is an alias of BIGNUMERIC
        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
            with self.subTest(f"Testing BigQuery's {type_}"):
                self.validate_all(
                    f"SELECT {type_} '1'",
                 
…[2610 chars elided]…
qlglot/expressions/datatypes.py:36:    BIGDECIMAL = auto()
sqlglot/expressions/datatypes.py:264:        DType.BIGDECIMAL,
sqlglot/expressions/datatypes.py:295:        DType.BIGDECIMAL,
sqlglot/generators/singlestore.py:343:        exp.DType.BIGDECIMAL: "DECIMAL",
sqlglot/generators/bigquery.py:413:        exp.DType.BIGDECIMAL: "BIGNUMERIC",
sqlglot/generators/snowflake.py:647:        exp.DType.BIGDECIMAL: "DOUBLE",
sqlglot/generators/duckdb.py:1745:        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
[tool_use Bash] {"command": "sed -n 1725,1760p sqlglot/generators/duckdb.py; grep -n \"def datatype_sql\" -A60 sqlglot/generators/duckdb.py | head -90; grep -n \"TYPE_MAPPING\\|def datatype_sql\" sqlglot/generator.py | head", "description": "Read DuckDB type mapping and datatype_sql"}
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
  
…[347 chars elided]…
duckdb/duckdb/blob/ff7f24fd8e3128d94371827523dae85ebaf58713/third_party/libpg_query/grammar/keywords/reserved_keywords.list#L1-L77
    RESERVED_KEYWORDS = {
        "array",
        "analyse",
        "union",
        "all",
        "when",
        "in_p",
        "default",
        "create_p",
        "window",
        "asymmetric",
        "to",
3 matches in 3 files:

1639:0:exp.DataType) -> str:
608:0:t.ClassVar = {
sqlglot/generator.py:1665:self.TYPE_MAPPING.get(type_value, type_value.value)
[tool_use Bash] {"command": "sed -n 1636,1700p sqlglot/generator.py; grep -n \"TYPE_MAPPING.get\\|def datatype_sql\" -n sqlglot/generators/*.py | head; cat > /tmp/chk.py <<'EOF'\nimport sqlglot\nfor s in [\"SELECT CAST(1 AS BIGNUMERIC(76, 38))\", \"SELECT CAST(1 AS BIGNUMERIC)\", \"DECLARE x BIGNUMERIC(76, 38)\", \"DECLARE x BIGNUMERIC\"]:\n    print(sqlglot.transpile(s, read=\"bigquery\", write=\"duckdb\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/chk.py').read())\"", "description": "Read generic datatype_sql and reproduce the bug"}
[tool_result]         specifier = f" {specifier}" if specifier and self.DATA_TYPE_SPECIFIERS_ALLOWED else ""
        return f"{this}{specifier}"

    def datatype_sql(self, expression: exp.DataType) -> str:
        nested = ""
        values = ""

        expr_nested = expression.args.get("nested")
        interior = (
            self.expressions(
                expression, dynamic=True, new_line=True, skip_first=True, skip_last=True
            )
            if expr_nested and self.pretty
            else 
…[2762 chars elided]…
   def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/singlestore.py:1468:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/redshift.py:325:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/snowflake.py:686:    def datatype_sql(self, expression: exp.DataType) -> str:
['SELECT CAST(1 AS DECIMAL(38, 5)(76, 38))']
['SELECT CAST(1 AS DECIMAL(38, 5))']
['DECLARE x DECIMAL(38, 5)(76, 38)']
['DECLARE x DECIMAL(38, 5)']
[assistant] Reproduced: the explicit `(76, 38)` is appended to the `TYPE_MAPPING` default `DECIMAL(38, 5)`. I'll find a spot in the DuckDB generator for a `datatype_sql` override.
[tool_use Bash] {"command": "grep -n \"    def [a-z_]*_sql(self\" sqlglot/generators/duckdb.py | head -20; grep -n \"^from\\|^import\" sqlglot/generators/duckdb.py", "description": "Find method layout in DuckDB generator"}
[tool_result] rg: regex parse error:
    (?:    def [a-z_]*_sql(self)
    ^
error: unclosed group
0 matches for '    def [a-z_]*_sql(self'
10 matches in 1 files:

sqlglot/generators/duckdb.py:1:from __future__ import annotations
sqlglot/generators/duckdb.py:3:from decimal import Decimal
sqlglot/generators/duckdb.py:4:from itertools import groupby
sqlglot/generators/duckdb.py:5:import re
sqlglot/generators/duckdb.py:6:import typing as t
sqlglot/generators/duckdb.py:8:from sqlglot import exp, generator, transforms
sqlglot/generators/duckdb.py:10:from sqlglot.dialects.dialect import (
sqlglot/generators/duckdb.py:40:from sqlglot.generator import unsupported_args
sqlglot/generators/duckdb.py:41:from sqlglot.helper import is_date_unit, seq_get
sqlglot/generators/duckdb.py:42:from builtins import type as Type
[tool_use Bash] {"command": "grep -n \"    def .*_sql(\" sqlglot/generators/duckdb.py | head -20; sed -n 1,30p sqlglot/generators/clickhouse.py | head -0; sed -n 517,530p sqlglot/generators/clickhouse.py", "description": "List DuckDB generator method definitions"}
[tool_result] rg: regex parse error:
    (?:    def .*_sql()
    ^
error: unclosed group
0 matches for '    def .*_sql('
head: illegal line count -- 0
    def datatype_sql(self, expression: exp.DataType) -> str:
        # String is the standard ClickHouse type, every other variant is just an alias.
        # Additionally, any supplied length parameter will be ignored.
        #
        # https://clickhouse.com/docs/en/sql-reference/data-types/string
        if expression.this in self.STRING_TYPE_MAPPING:
            dtype = "String"
        else:
            dtype = super().datatype_sql(expression)

        # This section changes the type to `Nullable(...)` if the following conditions hold:
        # - It's marked as nullable - this ensures we won't wrap ClickHouse types with `Nullable`
        #   and change their semantics
        # - It's not the key type of a `Map`. This is because ClickHouse enforces the following
[tool_use Grep] {"pattern": "    def \\w+_sql\\(self", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "awk '/^    def [a-z_]+_sql\\(self/{print NR\": \"$0}' sqlglot/generators/duckdb.py | head -15", "description": "List DuckDB generator method definitions"}
[tool_result] 334:     def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
2178:     def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:     def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:     def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:     def bitmapbitposition_sql(self, expression: exp.BitmapBitPosition) -> str:
2268:     def bitmapconstructagg_sql(self, expression: exp.BitmapCon
…[155 chars elided]…
:     def decrypt_sql(self, expression: exp.Decrypt) -> str:
2295:     def decryptraw_sql(self, expression: exp.DecryptRaw) -> str:
2300:     def encryptraw_sql(self, expression: exp.EncryptRaw) -> str:
2304:     def parseurl_sql(self, expression: exp.ParseUrl) -> str:
2308:     def parseip_sql(self, expression: exp.ParseIp) -> str:
2312:     def decompressstring_sql(self, expression: exp.DecompressString) -> str:
2316:     def decompressbinary_sql(self, expression: exp.DecompressBinary) -> str:
[tool_use Bash] {"command": "sed -n 2176,2184p sqlglot/generators/duckdb.py", "description": "View context around insertion point"}
[tool_result]     )

    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
        return self.sql(
            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
        )

    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
[assistant] Adding a `datatype_sql` override that, when the BIGDECIMAL has explicit parameters, renders them as a plain `DECIMAL(p, s)` and otherwise falls through to the default mapping.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def timeslice_sql(self, expression: exp.TimeSlice) -> str:", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.this == exp.DType.BIGDECIMAL and expression.expressions:\n            params = [param.copy() for param in expression.expressions]\n            return super().datatype_sql(exp.DataType(this=exp.DType.DECIMAL, expressions=params))\n\n        return super().datatype_sql(expression)\n\n    def timeslice_sql(self, expression: exp.TimeSlice) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a regression test alongside the existing `test_bignumeric` (adding a new test, not editing the existing one).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[360 chars elided]…
T(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/chk.py').read())\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Verify fix and run BigQuery and DuckDB dialect tests"}
[tool_result] ['SELECT CAST(1 AS DECIMAL(76, 38))']
['SELECT CAST(1 AS DECIMAL(38, 5))']
['DECLARE x DECIMAL(76, 38)']
['DECLARE x DECIMAL(38, 5)']
E   AssertionError: 'SELECT CAST(1 AS BIGNUMERIC)' != 'SELECT CAST(1 AS BIGNUMERIC(76, 38))'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
_ TestBigQuery.test_bignumeric [SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEq
…[96 chars elided]…
'
E   - SELECT CAST(1 AS BIGNUMERIC)
E   + SELECT CAST(1 AS BIGNUMERIC(76, 38))
E   ?                            ++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT CAST(1 AS BIGNUMERIC(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
SUBFAILED[SELECT CAST(1 AS BIGDECIMAL(76, 38)) -> bigquery] tests/dialects/test_bigquery.py::TestBigQuery::test_bignumeric
2 failed, 102 passed, 1649 subtests passed in 0.56s
[assistant] The DuckDB output is now correct. The two failures are in my new test's BigQuery expectation: the BigQuery generator drops the parameters when writing `BIGNUMERIC` back, which is existing behaviour outside this request. I'll drop that assertion and check only the DuckDB output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC(76, 38))\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },", "new_string": "                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185117-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run BigQuery/DuckDB tests, then the full suite"}
[tool_result] ........................................ [ 39%]
..............................................................                                                [100%]
102 passed, 1651 subtests passed in 0.45s
........................... [ 86%]
.......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 46.82s
[tool_use Bash] {"command": "(ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/generators/duckdb.py    | 7 +++++++
 tests/dialects/test_bigquery.py | 5 +++++
 2 files changed, 12 insertions(+)
[assistant] Parameterised BigQuery `BIGNUMERIC` / `BIGDECIMAL` now transpiles to DuckDB with only the parameters the user gave. Before the fix, `(76, 38)` was appended to the default: `DECLARE x DECIMAL(38, 5)(76, 38)`. Now it produces `DECLARE x DECIMAL(76, 38)`. With no parameters, the default `DECIMAL(38, 5)` is unchanged.

The fix is a `datatype_sql` override in `sqlglot/generators/duckdb.py`. When a `BIGDECIMAL` type has explicit parameters, it renders them as a plain `DECIMAL(p, s)`. Otherwise it falls through to the existing default mapping.

I added one `validate_all` case to `test_bignumeric` in `tests/dialects/test_bigquery.py` covering `BIGNUMERIC(76, 38)` and `BIGDECIMAL(76, 38)` → DuckDB. The existing assertions are untouched.

The full suite passes (1105 passed) and ruff check and format are clean on the changed files.

One thing I did not change: the BigQuery generator drops the parameters when writing `BIGNUMERIC` back out (`CAST(1 AS BIGNUMERIC(76, 38))` → `CAST(1 AS BIGNUMERIC)`). That is existing behaviour and outside this request, so my test asserts only the DuckDB side. Say if you want the BigQuery round-trip fixed too.
