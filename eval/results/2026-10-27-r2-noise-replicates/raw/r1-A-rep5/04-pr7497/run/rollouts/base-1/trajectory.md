# trajectory base-1

final message:
`JSON_ARRAY` now transpiles from DuckDB to valid Snowflake: `SELECT JSON_ARRAY('a', 'b', 'c')` becomes `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`. The full suite passes (1085 tests) and ruff lint and format are clean.

The fix has three parts:

- **DuckDB parser** (`sqlglot/parsers/duckdb.py`): `JSON_ARRAY` is now parsed into `exp.JSONArray` instead of an untyped function call. This is the root cause: nothing downstream recognised the call.
- **Snowflake generator** (`sqlglot/generators/snowflake.py`): added a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT(...)`. It uses `@unsupported_args` for `null_handling`, `return_type` and `strict`, which Snowflake can't express, so those raise a warning instead of producing bad SQL.
- **Test** (`tests/dialects/test_duckdb.py`): added `test_json_array`, which checks the DuckDB round-trip and the Snowflake output.

Choices to review:

- **Output form:** I emit `ARRAY_CONSTRUCT(...)` as the issue names it. Snowflake's own `exp.Array` renders as `['a', 'b']`, which is equally valid. Say if you'd rather have that form.
- **Wider effect:** the Snowflake change applies to every source dialect that produces `exp.JSONArray`, including BigQuery, Oracle and SingleStore. Their `JSON_ARRAY` / `JSON_BUILD_ARRAY` now also become `ARRAY_CONSTRUCT` when written to Snowflake. I checked that the existing tests for those dialects still pass.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\|ARRAY_CONSTRUCT\" sqlglot/ | grep -v \"\\.pyc\" | head -60", "description": "Search for JSON_ARRAY handling in sqlglot source"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3575:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.
…[4203 chars elided]…
      "json_array_push_double",
sqlglot/generators/singlestore.py:840:        "json_array_push_json",
sqlglot/generators/singlestore.py:841:        "json_array_push_string",
sqlglot/generators/singlestore.py:1454:    def jsonarraycontains_sql(self, expression: exp.JSONArrayContains) -> str:
sqlglot/generators/singlestore.py:1459:                f"JSON_ARRAY_CONTAINS_{json_type}", expression.expression, expression.this
sqlglot/generators/singlestore.py:1463:            "JSON_ARRAY_CONTAINS_JSON",
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['duckdb']:\n    e = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read=d)\n    print(repr(e))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\n\"", "description": "Inspect how DuckDB parses JSON_ARRAY and transpile to Snowflake"}
[tool_result] Select(
  expressions=[
    Anonymous(
      this=JSON_ARRAY,
      expressions=[
        Literal(this='a', is_string=True),
        Literal(this='b', is_string=True),
        Literal(this='c', is_string=True)])])
["SELECT JSON_ARRAY('a', 'b', 'c')"]
[assistant] DuckDB parses `JSON_ARRAY` as an `Anonymous` call, so nothing downstream recognizes it. Next I'll check the generic `JSONArray` generator, DuckDB's parser function table, and Snowflake's generator.
[tool_use Bash] {"command": "sed -n 3560,3575p sqlglot/generator.py; echo ----; sed -n 8,22p sqlglot/expressions/json.py; echo ----; grep -n \"FUNCTIONS\\|JSON\\|_parse_json\" sqlglot/parsers/duckdb.py | head -40; echo ----; grep -n \"ARRAY_CONSTRUCT\\|exp.Array:\\|JSONArray\\|class Generator\\|TRANSFORMS = {\" sqlglot/generators/snowflake.py | head; echo ----; grep -rn \"JSONArray\" tests/dialects/*.py | head -20", "description": "Read generator, expression, and dialect parser sources for JSON arrays"}
[tool_result]             name,
            *expression.expressions,
            suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
        )

    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
        null_handling = expression.args.get("null_handling")
        null_handling = f" {null_handling}" if null_handling else ""
        return_type = self.sql(expression, "return_type")
        return_type = f" RETURNING {return_type}" if return_type else ""
        strict = " STRICT" if expr
…[824 chars elided]…
n ("DATE_SUB", "GLOB")},
132:        "JSON": exp.ParseJSON.from_arg_list,
133:        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
134:        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
----
408:    TRANSFORMS = {
413:        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
----
tests/dialects/test_singlestore.py:257:        self.validate_identity("JSON_BUILD_ARRAY(id, name)").assert_is(exp.JSONArray)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT ARRAY_CONSTRUCT('a', 'b')\\\", read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b')\\\", read='bigquery', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b')\\\", read='oracle', write='sno
…[175 chars elided]…
 read='duckdb', write='duckdb'))\n\"; grep -n \"unsupported_args\" sqlglot/generators/snowflake.py | head -3; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py; grep -n \"rename_func\\|def func\" sqlglot/generators/snowflake.py | head -3; sed -n 1,20p sqlglot/generators/snowflake.py | grep -n \"import\"", "description": "Check Snowflake array output and other dialect JSON_ARRAY outputs"}
[tool_result] ["SELECT ['a', 'b']"]
["SELECT JSON_ARRAY('a', 'b')"]
["SELECT JSON_ARRAY('a', 'b')"]
['SELECT JSON_ARRAY(1, 2)']
["SELECT JSON_ARRAY('a', 'b')"]
27:from sqlglot.generator import unsupported_args
508:        exp.Levenshtein: unsupported_args("ins_cost", "del_cost", "sub_cost")(
926:    @unsupported_args("weight", "accuracy")
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
27:from sqlglot.generator
…[63 chars elided]…
_name, flatten, seq_get
29:from sqlglot.optimizer.scope import build_scope, find_all_in_scope
30:from sqlglot.parsers.snowflake import (
36:from sqlglot.tokens import TokenType
37:from collections import defaultdict
19:    rename_func,
410:        exp.ApproxDistinct: rename_func("APPROX_COUNT_DISTINCT"),
411:        exp.ArgMax: rename_func("MAX_BY"),
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
[assistant] Findings so far:

- DuckDB parses `JSON_ARRAY` as an untyped `Anonymous` function, so it never becomes `exp.JSONArray`.
- Snowflake has no `JSONArray` handling, so the generic `JSON_ARRAY` output passes through.
- Snowflake's `exp.Array` renders as `['a', 'b']`, not `ARRAY_CONSTRUCT`, so I'll generate `ARRAY_CONSTRUCT` explicitly.

The fix has two parts: a DuckDB parser entry and a Snowflake generator method. I'll read the exact spots before editing.
[tool_use Bash] {"command": "sed -n 100,140p sqlglot/parsers/duckdb.py; echo ----; sed -n 405,420p sqlglot/generators/snowflake.py; echo ----; sed -n 920,935p sqlglot/generators/snowflake.py; echo ----; grep -n \"def test_\\|validate_all(\\\"JSON\\|JSON_\" tests/dialects/test_duckdb.py | head -30", "description": "Read target regions in DuckDB parser, Snowflake generator, and tests"}
[tool_result]     }

    FUNCTIONS = {
        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
        "ARRAY_PREPEND": _build_array_prepend,
        "ARRAY_REVERSE_SORT": _build_sort_array_desc,
        "ARRAY_INTERSECT": lambda args: exp.ArrayIntersect(expressions=args),
        "ARRAY_SORT": exp.SortArray.from_arg_list,
        "BIT_AND": exp.BitwiseAndAgg.from_arg_list,
        
…[4470 chars elided]…
JSON_EXTRACT_PATH_TEXT(x, '$.family')",
1561:    def test_array_index(self):
1601:    def test_array_insert(self):
1642:    def test_array_remove(self):
1667:    def test_array_remove_at(self):
1732:    def test_time(self):
1902:    def test_sample(self):
1950:    def test_array(self):
1954:    def test_cast(self):
2130:    def test_encode_decode(self):
2162:    def test_sha(self):
2169:    def test_rename_table(self):
2187:    def test_timestamps_with_units(self):
2195:    def test_isnan(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\": parser.build_extract_json_with_path(exp.JSONExtract),", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\": parser.build_extract_json_with_path(exp.JSONExtract),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "    @unsupported_args(\"weight\", \"accuracy\")\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        return self.func(\"APPROX_PERCENTILE\", expression.this, expression.args.ge
…[71 chars elided]…
"accuracy\")\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        return self.func(\"APPROX_PERCENTILE\", expression.this, expression.args.get(\"quantile\"))\n\n    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll add a regression test to the DuckDB dialect tests, near the existing `test_array` case, then verify the output.
[tool_use Bash] {"command": "sed -n 1948,1954p tests/dialects/test_duckdb.py", "description": "Read context around test_array in DuckDB tests"}
[tool_result]         )

    def test_array(self):
        self.validate_identity("ARRAY(SELECT id FROM t)")
        self.validate_identity("ARRAY((SELECT id FROM t))")

    def test_cast(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_cast(self):", "new_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_json_array(self):\n        self.validate_identity(\"SELECT JSON_ARRAY('a', 'b', 'c')\")\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n\n    def test_cast(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-091158-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY()\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, NULL)\\\", read='duckdb', write='snowflake'))\npri
…[161 chars elided]…
='duckdb', write='duckdb'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_bigquery.py tests/dialects/test_oracle.py tests/dialects/test_singlestore.py 2>&1 | tail -15", "description": "Verify transpile output and run related dialect tests"}
[tool_result] ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()']
['SELECT ARRAY_CONSTRUCT(1, NULL)']
["SELECT ARRAY_CONSTRUCT('a')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
........................................................................................................................................................................................................................................................        [100%]
248 passed, 3633 subtests passed in 1.08s
[assistant] The targeted dialect tests pass and the output is right. Next I'll run the full suite with the project's check command, since the Snowflake generator change touches every source dialect.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Run full test suite plus ruff lint and format checks"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
............................................................................................................................................ [ 37%]
................................................................... [ 43%]
..............................................................
…[218 chars elided]…
......................... [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1085 passed, 17838 subtests passed in 49.14s
All checks passed!
3 files already formatted
[assistant] `JSON_ARRAY` now transpiles from DuckDB to valid Snowflake: `SELECT JSON_ARRAY('a', 'b', 'c')` becomes `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`. The full suite passes (1085 tests) and ruff lint and format are clean.

The fix has three parts:

- **DuckDB parser** (`sqlglot/parsers/duckdb.py`): `JSON_ARRAY` is now parsed into `exp.JSONArray` instead of an untyped function call. This is the root cause: nothing downstream recognised the call.
- **Snowflake generator** (`sqlglot/generators/snowflake.py`): added a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT(...)`. It uses `@unsupported_args` f
…[208 chars elided]…
ch checks the DuckDB round-trip and the Snowflake output.

Choices to review:

- **Output form:** I emit `ARRAY_CONSTRUCT(...)` as the issue names it. Snowflake's own `exp.Array` renders as `['a', 'b']`, which is equally valid. Say if you'd rather have that form.
- **Wider effect:** the Snowflake change applies to every source dialect that produces `exp.JSONArray`, including BigQuery, Oracle and SingleStore. Their `JSON_ARRAY` / `JSON_BUILD_ARRAY` now also become `ARRAY_CONSTRUCT` when written to Snowflake. I checked that the existing tests for those dialects still pass.

Nothing is committed.
