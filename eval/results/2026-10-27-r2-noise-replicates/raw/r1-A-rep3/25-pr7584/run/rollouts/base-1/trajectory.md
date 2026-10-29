# trajectory base-1

final message:
Parameterised `BIGNUMERIC` / `BIGDECIMAL` now generate DuckDB's parameters in place of the default mapping, so `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`. Without parameters the output is still `DECIMAL(38, 5)`. The full suite passes (1105 tests), and ruff is clean.

**Change**
- `sqlglot/generators/duckdb.py`: a `datatype_sql` override. When a `BIGDECIMAL` type has parameters, it emits `DECIMAL(<params>)` via `self.func`. Otherwise it defers to the base generator.
- `tests/dialects/test_bigquery.py`: a case in `test_bignumeric` for `CAST(1 AS BIGNUMERIC(76, 38))` → `DECIMAL(76, 38)`.

**Things to know**
- **DuckDB caps DECIMAL width at 38.** `DECIMAL(76, 38)` will likely fail when DuckDB runs it, even though the output now matches what you asked for. I didn't clamp it, because that would silently change the precision the user declared. If you want clamping or an error instead, say so.
- The BigQuery generator still drops the parameters on a BigQuery → BigQuery round trip (`CAST(x AS BIGNUMERIC(76, 38))` comes back as `CAST(x AS BIGNUMERIC)`). That's outside this fix, so I left it alone.

## events
[tool_use Bash] {"command": "grep -rn -i \"bignumeric\\|BIGDECIMAL\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/parser.py sqlglot/expressions.py | head -50", "description": "Find BIGNUMERIC handling in relevant modules"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
[tool_use Bash] {"command": "rg -n -i \"BIGDECIMAL|BIGNUMERIC|76\" sqlglot/ | grep -v \"^sqlglot/.*\\.pyc\" | head -60; echo ---; rg -n \"DECIMAL\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py | head -40", "description": "Search BIGNUMERIC and DECIMAL mappings"}
[tool_result] sqlglot/generators/duckdb.py:82:MAX_BIT_POSITION = exp.Literal.number(32768)
sqlglot/generators/duckdb.py:1745:        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
sqlglot/generators/duckdb.py:1917:    # Supports values in range 0-32767, this version returns NULL if any value is out of range
sqlglot/generators/duckdb.py:1960:            WHEN LENGTH(l) != LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL
sqlglot/generators/duckdb.py:2225:        - Each bucket covers 32,768 values
sqlglo
…[2715 chars elided]…
BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/oracle.py:24:    # See section 8: https://docs.oracle.com/cd/A97630_01/server.920/a96540/sql_elements9a.htm
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
---
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
[tool_use Bash] {"command": "sed -n 1725,1760p sqlglot/generators/duckdb.py; echo ---; rg -n \"def datatype_sql\" -A40 sqlglot/generator.py | head -80; echo ---; rg -n \"BIGDECIMAL|BIGNUMERIC|DECIMAL\\(38\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -20", "description": "Inspect DuckDB type mapping and datatype_sql"}
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
  
…[4600 chars elided]…
1.2')")
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3823:                        "duckdb": "SELECT CAST('1' AS DECIMAL(38, 5))",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'SELECT CAST(x AS BIGNUMERIC(76, 38))', 'SELECT CAST(x AS BIGNUMERIC)', 'SELECT CAST(x AS BIGDECIMAL(10))']:\n    e = sqlglot.parse_one(s, read='bigquery')\n    print(repr(e.sql('duckdb')))\nprint(repr(sqlglot.parse_one('CAST(x AS BIGNUMERIC(76, 38))', read='bigquery').find(sqlglot.exp.DataType).args))\n\" 2>&1 | tail -20; git log --oneline -1; git status --short", "description": "Reproduce parameterised BIGNUMERIC generation in DuckDB"}
[tool_result] 'DECLARE x DECIMAL(38, 5)(76, 38)'
'SELECT CAST(x AS DECIMAL(38, 5)(76, 38))'
'SELECT CAST(x AS DECIMAL(38, 5))'
'SELECT CAST(x AS DECIMAL(38, 5)(10))'
{'this': <DType.BIGDECIMAL: 'BIGDECIMAL'>, 'expressions': [DataTypeParam(
  this=Literal(this=76, is_string=False)), DataTypeParam(
  this=Literal(this=38, is_string=False))], 'nested': False}
6a1ae4975 lithify: probe base
[tool_use Bash] {"command": "rg -n \"def datatype_sql|def .*_sql\\(self, expression: exp.DataType\" sqlglot/generators/*.py | head; sed -n 3812,3840p tests/dialects/test_bigquery.py", "description": "Check existing datatype overrides and BigQuery tests"}
[tool_result] sqlglot/generators/clickhouse.py:517:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/fabric.py:78:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/exasol.py:306:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/hive.py:432:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/risingwave.py:27:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/redshif
…[809 chars elided]…
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
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/generators/duckdb.py | grep -n import; rg -n \"    def [a-z_]+_sql\\(self\" sqlglot/generators/duckdb.py | head -5; sed -n 300,312p sqlglot/generators/exasol.py", "description": "Check DuckDB generator method style"}
[tool_result] 1:from __future__ import annotations
3:from decimal import Decimal
4:from itertools import groupby
5:import re
6:import typing as t
8:from sqlglot import exp, generator, transforms
10:from sqlglot.dialects.dialect import (
334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapb
…[209 chars elided]…
TIMESTAMPTZ: "TIMESTAMP",
        exp.DType.TIMESTAMPLTZ: "TIMESTAMP",
        exp.DType.TIMESTAMPNTZ: "TIMESTAMP",
    }

    def datatype_sql(self, expression: exp.DataType) -> str:
        # Exasol supports a fixed default precision of 3 for TIMESTAMP WITH LOCAL TIME ZONE
        # and does not allow specifying a different custom precision
        if expression.is_type(exp.DType.TIMESTAMPLTZ):
            return "TIMESTAMP WITH LOCAL TIME ZONE"

        return super().datatype_sql(expression)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122914-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "offset": 2176, "limit": 9}
[tool_result] 2176	    )
2177	
2178	    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2179	        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
2180	        return self.sql(
2181	            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
2182	        )
2183	
2184	    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122914-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:\n        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))", "new_string": "    def data
…[192 chars elided]…
g appended to it\n        if expression.this == exp.DType.BIGDECIMAL and expression.expressions:\n            return self.func(\"DECIMAL\", *expression.expressions)\n\n        return super().datatype_sql(expression)\n\n    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:\n        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122914-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now I'll verify the fix and add a test next to the existing BIGNUMERIC cases.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'SELECT CAST(x AS BIGNUMERIC(76, 38))', 'SELECT CAST(x AS BIGNUMERIC)', 'SELECT CAST(x AS BIGDECIMAL(10))', 'SELECT CAST(x AS BIGNUMERIC(76, 38)) AS y']:\n    print(repr(sqlglot.parse_one(s, read='bigquery').sql('duckdb')))\nprint(sqlglot.parse_one('SELECT CAST(x AS BIGNUMERIC(76, 38))', read='bigquery').sql('bigquery'))\n\"", "description": "Verify fixed BIGNUMERIC output for DuckDB"}
[tool_result] 'DECLARE x DECIMAL(76, 38)'
'SELECT CAST(x AS DECIMAL(76, 38))'
'SELECT CAST(x AS DECIMAL(38, 5))'
'SELECT CAST(x AS DECIMAL(10))'
'SELECT CAST(x AS DECIMAL(76, 38)) AS y'
SELECT CAST(x AS BIGNUMERIC)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122914-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[279 chars elided]…
SELECT CAST(1 AS BIGNUMERIC)\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122914-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ....... [ 39%]
............................ [ 42%]
........................................................... [ 47%]
........................................................................................ [ 55%]
.................................................... [ 60%]
.............................. [ 63%]
..................................................................... [ 69%]
...................................................... [ 74%]
............................................. [ 78%]
........................................................... [ 83%]
........................... [ 86%]
.......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 51.20s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generators/duckdb.py    | 8 ++++++++
 tests/dialects/test_bigquery.py | 7 +++++++
 2 files changed, 15 insertions(+)
[assistant] Parameterised `BIGNUMERIC` / `BIGDECIMAL` now generate DuckDB's parameters in place of the default mapping, so `DECLARE x BIGNUMERIC(76, 38)` becomes `DECLARE x DECIMAL(76, 38)`. Without parameters the output is still `DECIMAL(38, 5)`. The full suite passes (1105 tests), and ruff is clean.

**Change**
- `sqlglot/generators/duckdb.py`: a `datatype_sql` override. When a `BIGDECIMAL` type has parameters, it emits `DECIMAL(<params>)` via `self.func`. Otherwise it defers to the base generator.
- `tests/dialects/test_bigquery.py`: a case in `test_bignumeric` for `CAST(1 AS BIGNUMERIC(76, 38))` → `DECIMAL(76, 38)`.

**Things to know**
- **DuckDB caps DECIMAL width at 38.** `DECIMAL(76, 38)` will likely fail when DuckDB runs it, even though the output now matches what you asked for. I didn't clamp it, because that would silently change the precision the user declared. If you want clamping or an error instead, say so.
- The BigQuery generator still drops the parameters on a BigQuery → BigQuery round trip (`CAST(x AS BIGNUMERIC(76, 38))` comes back as `CAST(x AS BIGNUMERIC)`). That's outside this fix, so I left it alone.
