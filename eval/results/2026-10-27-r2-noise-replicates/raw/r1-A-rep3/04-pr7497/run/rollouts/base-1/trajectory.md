# trajectory base-1

final message:
`DuckDB JSON_ARRAY(...)` now transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`. The full suite passes (1084 tests), and ruff check and format are clean on the changed files.

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output now
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The cause was that DuckDB's parser had no entry for `JSON_ARRAY`, so it became a generic function and passed through unchanged. The fix has three parts:

- **`sqlglot/parsers/duckdb.py`**: maps `JSON_ARRAY` to the existing `exp.JSONArray` expression.
- **`sqlglot/generators/snowflake.py`**: adds a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT`. It is marked `unsupported_args` for `null_handling`, `return_type` and `strict`, which Snowflake lacks, so those get a warning rather than silently disappearing.
- **`tests/dialects/test_duckdb.py`**: adds a `validate_all` case for the DuckDB and Snowflake output.

Other dialects are unchanged. DuckDB `JSON_ARRAY` still round-trips to `JSON_ARRAY` for DuckDB, BigQuery, MySQL, Postgres and Spark, because the base generator already emitted that form. The change is uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\b\\|ARRAY_CONSTRUCT\\|JSONArray\" sqlglot/ | grep -v \"^sqlglot/.*\\.pyc\" | head -80", "description": "Search for JSON array references in sqlglot source"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3575:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.
…[4314 chars elided]…
enerators/singlestore.py:841:        "json_array_push_string",
sqlglot/generators/singlestore.py:1454:    def jsonarraycontains_sql(self, expression: exp.JSONArrayContains) -> str:
sqlglot/generators/singlestore.py:1459:                f"JSON_ARRAY_CONTAINS_{json_type}", expression.expression, expression.this
sqlglot/generators/singlestore.py:1463:            "JSON_ARRAY_CONTAINS_JSON",
sqlglot/generators/mysql.py:643:    def jsonarraycontains_sql(self, expression: exp.JSONArrayContains) -> str:
[tool_use Bash] {"command": "sed -n 1,60p sqlglot/expressions/json.py && sed -n 3555,3590p sqlglot/generator.py && grep -rn \"JSON_ARRAY\\b\\|JSONArray\\b\" sqlglot/dialects/duckdb.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>/dev/null", "description": "Inspect JSONArray expression and related dialect code"}
[tool_result] """sqlglot expressions - JSON functions."""

from __future__ import annotations

from sqlglot.expressions.core import Expression, Func, AggFunc, Binary, Predicate


class CheckJson(Expression, Func):
    arg_types = {"this": True}


class JSONArray(Expression, Func):
    arg_types = {
        "expressions": False,
        "null_handling": False,
        "return_type": False,
        "strict": False,
    }


class JSONArrayAgg(Expression, AggFunc):
    arg_types = {
        "this": True,
        
…[1951 chars elided]…
andling}" if null_handling else ""
        return_type = self.sql(expression, "return_type")
        return_type = f" RETURNING {return_type}" if return_type else ""
        strict = " STRICT" if expression.args.get("strict") else ""
        return self.func(
            "JSON_ARRAYAGG",
            this,
            suffix=f"{order}{null_handling}{return_type}{strict})",
        )

    def jsoncolumndef_sql(self, expression: exp.JSONColumnDef) -> str:
        path = self.sql(expression, "path")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nt = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(t.selects[0]))\nprint(t.sql('snowflake'))\nprint(sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='snowflake').sql('duckdb'))\nprint(sqlglot.transpile(\\\"
…[337 chars elided]…
 read='duckdb', write='oracle'))\n\"; grep -rn \"ARRAY_CONSTRUCT\\|JSON_ARRAY\\|ARRAY_CONSTRUCTOR\\|ARRAY_CONSTRUCT_COMPACT\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py | head; grep -n \"JSON_ARRAY\\|json_array\" sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py", "description": "Reproduce DuckDB JSON_ARRAY transpilation and check Snowflake code"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfrom sqlglot import exp\nt = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(t.selects[0]))\nprint(t.sql('snowflake'))\nprint(sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='snowflake').sql('duckd
…[177 chars elided]…
 grep -rn \"ARRAY_CONSTRUCT\\|JSON_ARRAY\\|json_array\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parsers/snowflake.py | head; grep -n \"JSON_ARRAY\\|json_array\" sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py; git log --oneline -3 -- sqlglot/generators/snowflake.py", "description": "Reproduce JSON_ARRAY transpilation across dialects"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
SELECT JSON_ARRAY('a', 'b', 'c')
SELECT JSON_ARRAY('a', 'b', 'c')
bigquery ["SELECT JSON_ARRAY('a', 'b', 'c')"]
mysql ["SELECT JSON_ARRAY('a', 'b', 'c')"]
postgres ["SELECT JSON_ARRAY('a', 'b', 'c')"]
oracle ["SELECT JSON_ARRAY('a', 'b', 'c')"]
spark ["SELECT JSON_ARRAY('a', 'b', 'c')"]
presto ["SELECT JSON_ARRAY('a', 'b', 'c')"]
sqlglot/parsers/snowflake.py:407:        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
c16630f61 fix(snowflake): map JSON type to VARIANT in Snowflake generator [CLAUDE] (#7496)
713e95fb9 Fix(snowflake): parse GET_DDL #unknown_policy in ROW ACCESS POLICY [CLAUDE] (#7491)
800c0c44b Fix(snowflake): emit proper `HANDLER` property syntax
[tool_use Bash] {"command": "grep -n \"exp.Array\\b\\|exp.Array:\\|def array_sql\\|ARRAY_CONSTRUCT\\|unsupported_args\" sqlglot/generators/snowflake.py | head -30; grep -n \"FUNCTIONS\\b\" -A3 sqlglot/parsers/duckdb.py | head -20; grep -n \"\\\"JSON\" sqlglot/parsers/duckdb.py | head; grep -rn \"JSON_ARRAY\\|json_array\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_dialect.py | head -20", "description": "Inspect Snowflake array generation and DuckDB parser functions"}
[tool_result] 27:from sqlglot.generator import unsupported_args
271:                if not isinstance(unnest_expr, exp.Array):
413:        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
508:        exp.Levenshtein: unsupported_args("ins_cost", "del_cost", "sub_cost")(
926:    @unsupported_args("weight", "accuracy")
1051:    def array_sql(self, expression: exp.Array) -> str:
72:    NO_PAREN_FUNCTIONS = {
73:        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: 
…[1587 chars elided]…
py:4853:                "": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4854:                "bigquery": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4857:                "bigquery": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4858:                "mysql": """JSON_ARRAY_INSERT('["a", ["b", "c"], "d"]', '$[1]', 1)""",
[tool_use Bash] {"command": "sed -n 1045,1060p sqlglot/generators/snowflake.py; sed -n 500,515p sqlglot/generators/snowflake.py; sed -n 102,140p sqlglot/parsers/duckdb.py; grep -n \"JSONArray\\b\\|exp.JSONArray\" sqlglot/generators/*.py | head; grep -n \"def test_\" tests/dialects/test_duckdb.py | head -3; grep -n \"json\" -i tests/dialects/test_duckdb.py | head -20", "description": "Check Snowflake array_sql and DuckDB JSON tests"}
[tool_result]         return expr_sql

    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:
        return self.func("ARRAY_TO_STRING", expression.this, expression.expression)

    def array_sql(self, expression: exp.Array) -> str:
        expressions = expression.expressions

        first_expr = seq_get(expressions, 0)
        if isinstance(first_expr, exp.Select):
            # SELECT AS STRUCT foo AS alias_foo -> ARRAY_AGG(OBJECT_CONSTRUCT('alias_foo', foo))
            if first_expr.tex
…[5395 chars elided]…
ll}'), 'a'))""",
549:            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
553:            "SELECT col FROM t WHERE JSON_EXTRACT_STRING(col, '$.id') NOT IN ('b')",
561:            "SELECT JSON_EXTRACT_STRING(c, '$.k1') = 'v1'",
565:            "SELECT JSON_EXTRACT(c, '$.k1') = 'v1'",
569:            "SELECT JSON_EXTRACT(c, '$[*].id')[0:2]",
573:            "SELECT JSON_EXTRACT_STRING(c, '$[*].id')[0:2]",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "offset": 130, "limit": 6}
[tool_result] 130	        ),
131	        "JARO_WINKLER_SIMILARITY": exp.JarowinklerSimilarity.from_arg_list,
132	        "JSON": exp.ParseJSON.from_arg_list,
133	        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
134	        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
135	        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "offset": 1048, "limit": 4}
[tool_result] 1048	    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:
1049	        return self.func("ARRAY_TO_STRING", expression.this, expression.expression)
1050	
1051	    def array_sql(self, expression: exp.Array) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\": ", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\":"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:\n        return self.func(\"ARRAY_TO_STRING\", expression.this, expression.expression)\n", "new_string": "    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:\n        return self.func(\"ARRAY_TO_STRING\", expression.this, expression.expression)\n\n    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in [\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", 'SELECT JSON_ARRAY()']:\n    print(sqlglot.transpile(q, read='duckdb', write='snowflake'))\n    for d in ['duckdb','bigquery','mysql','postgres','spark']:\n        print(' ', d, sqlglot.transpile(q, read='duckdb', write=d))\n\"", "description": "Verify DuckDB JSON_ARRAY transpiles to Snowflake"}
[tool_result] ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"]
  duckdb ["SELECT JSON_ARRAY('a', 'b', 'c')"]
  bigquery ["SELECT JSON_ARRAY('a', 'b', 'c')"]
  mysql ["SELECT JSON_ARRAY('a', 'b', 'c')"]
  postgres ["SELECT JSON_ARRAY('a', 'b', 'c')"]
  spark ["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()']
  duckdb ['SELECT JSON_ARRAY()']
  bigquery ['SELECT JSON_ARRAY()']
  mysql ['SELECT JSON_ARRAY()']
  postgres ['SELECT JSON_ARRAY()']
  spark ['SELECT JSON_ARRAY()']
[assistant] Snowflake output is now valid. Next I'll add a regression test next to the existing DuckDB JSON tests.
[tool_use Bash] {"command": "sed -n 318,345p tests/dialects/test_duckdb.py", "description": "Read DuckDB JSON test region"}
[tool_result]         )
        self.validate_all(
            """SELECT JSON('{"fruit":"banana"}') -> 'fruit'""",
            write={
                "duckdb": """SELECT JSON('{"fruit":"banana"}') -> '$.fruit'""",
                "snowflake": """SELECT GET_PATH(PARSE_JSON('{"fruit":"banana"}'), 'fruit')""",
            },
        )
        self.validate_all(
            """SELECT JSON('{"fruit": {"foo": "banana"}}') -> 'fruit' -> 'foo'""",
            write={
                "duckdb": """SELECT JSON('{"fruit
…[222 chars elided]…
ll(
            "CASE WHEN JSON_TYPE(x) = 'NULL' THEN NULL ELSE x END",
            read={
                "snowflake": "STRIP_NULL_VALUE(x)",
            },
        )
        self.validate_all(
            """SELECT CASE WHEN JSON_TYPE(JSON('{"a": null}') -> '$.a') = 'NULL' THEN NULL ELSE JSON('{"a": null}') -> '$.a' END""",
            read={
                "snowflake": """SELECT STRIP_NULL_VALUE(GET_PATH(PARSE_JSON('{"a": null}'), 'a'))""",
            },
        )
        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"CASE WHEN JSON_TYPE(x) = 'NULL' THEN NULL ELSE x END\",\n            read={", "new_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n        self.validate_all(\n            \"CASE WHEN JSON_TYPE(x) = 'NULL' THEN NULL ELSE x END\",\n            read={"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the project's check command from the harness config, to confirm nothing else regressed.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
................................. [ 27%]
...........................................................................................................................................................
…[262 chars elided]…
.............................................................. [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1084 passed, 17838 subtests passed in 49.11s
[assistant] All 1084 tests pass. I'll run the linter on the changed files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
Would reformat: sqlglot/parsers/duckdb.py
1 file would be reformatted, 2 files already formatted
 sqlglot/generators/snowflake.py | 4 ++++
 sqlglot/parsers/duckdb.py       | 3 ++-
 tests/dialects/test_duckdb.py   | 7 +++++++
 3 files changed, 13 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "git diff sqlglot/parsers/duckdb.py; git stash list >/dev/null; <work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/parsers/duckdb.py 2>&1 | head -30", "description": "Show duckdb parser diff and format diff"}
[tool_result] diff --git a/sqlglot/parsers/duckdb.py b/sqlglot/parsers/duckdb.py
index db132a958..d07108614 100644
--- a/sqlglot/parsers/duckdb.py
+++ b/sqlglot/parsers/duckdb.py
@@ -130,7 +130,8 @@ class DuckDBParser(parser.Parser):
         ),
         "JARO_WINKLER_SIMILARITY": exp.JarowinklerSimilarity.from_arg_list,
         "JSON": exp.ParseJSON.from_arg_list,
-        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
+        "JSON_ARRAY": lambda args: exp.JSONArray(expressions
…[454 chars elided]…
 "JSON": exp.ParseJSON.from_arg_list,
         "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
-        "JSON_EXTRACT_PATH":parser.build_extract_json_with_path(exp.JSONExtract),
+        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
         "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
         "LIST_APPEND": exp.ArrayAppend.from_arg_list,
         "LIST_CONCAT": parser.build_array_concat,

1 file would be reformatted
[assistant] The edit dropped a space after `"JSON_EXTRACT_PATH":`. Fixing that so the file is formatted correctly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON_EXTRACT_PATH\":parser.build_extract_json_with_path(exp.JSONExtract),", "new_string": "        \"JSON_EXTRACT_PATH\": parser.build_extract_json_with_path(exp.JSONExtract),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111137-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -2", "description": "Recheck formatting and run duckdb/snowflake tests", "timeout": 300000}
[tool_result] 3 files already formatted
...........................................................................................................................................              [100%]
139 passed, 2152 subtests passed in 0.60s
[assistant] `DuckDB JSON_ARRAY(...)` now transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`. The full suite passes (1084 tests), and ruff check and format are clean on the changed files.

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output now
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The cause was that DuckDB's parser had no entry for `JSON_ARRAY`, so it became a generic function and passed through unchanged. The fix has three parts:

- **`sqlglot/parsers/duckdb.py`**: maps `JSON_ARRAY` to the existing `exp.JSONArray` expression.
- **`sqlglot/generators/snowflake.py`**: adds a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT`. It is marked `unsupported_args` for `null_handling`, `return_type` and `strict`, which Snowflake lacks, so those get a warning rather than silently disappearing.
- **`tests/dialects/test_duckdb.py`**: adds a `validate_all` case for the DuckDB and Snowflake output.

Other dialects are unchanged. DuckDB `JSON_ARRAY` still round-trips to `JSON_ARRAY` for DuckDB, BigQuery, MySQL, Postgres and Spark, because the base generator already emitted that form. The change is uncommitted in the worktree.
