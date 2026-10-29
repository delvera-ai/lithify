# trajectory base-1

final message:
`JSON_ARRAY(...)` from DuckDB now transpiles to valid Snowflake:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full test suite passes (1085 passed), and ruff check and format are clean on the changed files.

**Root cause:** DuckDB's parser had no entry for `JSON_ARRAY`, so it produced an untyped `Anonymous` function that Snowflake passed through unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: map `JSON_ARRAY` to `exp.JSONArray`, the existing expression class.
- `sqlglot/generators/snowflake.py`: add a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT(...)`. It uses `@unsupported_args("null_handling", "return_type", "strict")`, so Oracle-style options that Snowflake can't express produce a warning instead of being dropped silently.
- `tests/dialects/test_duckdb.py`: add `test_json_array`, which checks the DuckDB round-trip and the Snowflake output.

**Side effect:** the Snowflake change applies to every source dialect that produces `exp.JSONArray`, not just DuckDB. For example, BigQuery's `JSON_ARRAY(1, 2)` now also becomes `ARRAY_CONSTRUCT(1, 2)` for Snowflake, where it previously emitted the invalid `JSON_ARRAY`.

Snowflake's generator renders `exp.Array` as `[...]`, so I emitted `ARRAY_CONSTRUCT` directly rather than reusing that path. The issue names `ARRAY_CONSTRUCT` as the target, so I matched it.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\b\" sqlglot/ | grep -v \"^Binary\" | head -50; echo ---; grep -rn -i \"json_array\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head", "description": "Search JSON_ARRAY handling across sqlglot"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers
…[1979 chars elided]…
t/generators/singlestore.py:841:        "json_array_push_string",
sqlglot/generators/singlestore.py:1459:                f"JSON_ARRAY_CONTAINS_{json_type}", expression.expression, expression.this
sqlglot/generators/singlestore.py:1463:            "JSON_ARRAY_CONTAINS_JSON",
sqlglot/generators/postgres.py:446:                    self.unsupported("Unsupported JSON_ARRAY_ELEMENTS with offset")
sqlglot/generators/postgres.py:448:                return f"JSON_ARRAY_ELEMENTS({arg_as_json}){alias}"
---
[tool_use Bash] {"command": "sed -n 3555,3580p sqlglot/generator.py; echo ---; sed -n 1,35p sqlglot/expressions/json.py; echo ---; grep -n \"JSONArray\\b\\|JSON_ARRAY\\|ARRAY_CONSTRUCT\" sqlglot/dialects/duckdb.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py 2>/dev/null; echo ---; grep -rn \"JSON_ARRAY\\b\" tests/dialects/*.py | head -20", "description": "Inspect generator, expression, and dialect code"}
[tool_result]         if not name:
            name = "JSON_OBJECT" if isinstance(expression, exp.JSONObject) else "JSON_OBJECTAGG"

        return self.func(
            name,
            *expression.expressions,
            suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
        )

    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
        null_handling = expression.args.get("null_handling")
        null_handling = f" {null_handling}" if null_handling else ""
        return_type 
…[1872 chars elided]…
JSON_ARRAY(STRUCT(10 AS a, 'foo' AS b))")
tests/dialects/test_bigquery.py:3342:        self.validate_identity("JSON_ARRAY(10, ['foo', 'bar'], [20, 30])")
tests/dialects/test_mysql.py:247:        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
tests/dialects/test_oracle.py:81:            "SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
tests/dialects/test_singlestore.py:254:                "oracle": "SELECT JSON_ARRAY(id, name) FROM t",
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\ne = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(e.selects[0]))\nprint(e.sql('snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT ARRAY_CONSTRUCT('a')\\\", read='snowflake', write='duckdb'))\n\"; grep -n \"ARRAY_CONSTRUCT\\|JSON_\" sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py | head -40", "description": "Reproduce the DuckDB to Snowflake JSON_ARRAY issue"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parsers/duckdb.py:133:        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
sqlglot/parsers/duckdb.py:134:        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
sqlglot/generators/snowflake.py:387:    JSON_KEY_VALUE_PAIR_SEP = ","
sqlglot/generators/snowflake.py:502:            "JSON_EXTRACT_PATH_TEXT", e.this, e.expression
sqlglot/generators/snowflake.py:634:    SUPPORTED_JSON_PATH_PARTS = {
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(e.selects[0]))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\",
…[42 chars elided]…
lglot.transpile(\\\"SELECT ARRAY_CONSTRUCT('a')\\\", read='snowflake', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='snowflake', write='duckdb'))\n\"; grep -n \"JSON\\|json\" sqlglot/parsers/duckdb.py | head -30; grep -n \"json\\|JSON\" sqlglot/generators/duckdb.py | head -40", "description": "Reproduce transpile output and inspect DuckDB JSON handling"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT ['a']"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
132:        "JSON": exp.ParseJSON.from_arg_list,
133:        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
134:        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(e
…[2134 chars elided]…
32:    def checkjson_sql(self, expression: exp.CheckJson) -> str:
2637:                exp.or_(arg.is_(exp.Null()), arg.eq(""), exp.func("json_valid", arg)),
2640:            .else_(exp.Literal.string("Invalid JSON"))
2643:    def parsejson_sql(self, expression: exp.ParseJSON) -> str:
2648:                .when(exp.func("json_valid", arg), exp.cast(arg.copy(), "JSON"))
2651:        return self.func("JSON", arg)
2666:            .when(exp.func("json_type", expression.this).eq("NULL"), exp.null())
[tool_use Bash] {"command": "grep -n \"unsupported_args\\|exp.Array\\|def array_sql\\|def .*_sql(self\" sqlglot/generators/snowflake.py | head -80; echo ---; sed -n 160,170p sqlglot/generators/singlestore.py; echo ---; grep -n \"unsupported_args\" sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py | head -3; echo ---; grep -n \"def unsupported_args\" -A3 sqlglot/*.py sqlglot/*/*.py | head; echo ---; grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/test_*.py | head", "description": "Inspect Snowflake generator patterns and related tests"}
[tool_result] 27:from sqlglot.generator import unsupported_args
63:def _regexpilike_sql(self: SnowflakeGenerator, expression: exp.RegexpILike) -> str:
189:                    exp.select(exp.ArrayAgg(this=exp.Star())).from_(unnest).subquery()
271:                if not isinstance(unnest_expr, exp.Array):
413:        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
414:        exp.ArrayConcat: array_concat_sql("ARRAY_CAT"),
415:        exp.ArrayAppend: array_append_sql("ARRAY_APPEND"),
…[3816 chars elided]…
--
sqlglot/generators/snowflake.py:27:from sqlglot.generator import unsupported_args
sqlglot/generators/snowflake.py:508:        exp.Levenshtein: unsupported_args("ins_cost", "del_cost", "sub_cost")(
sqlglot/generators/snowflake.py:926:    @unsupported_args("weight", "accuracy")
---
sqlglot/generator.py:30:def unsupported_args(
sqlglot/generator.py-31-    *args: str | tuple[str, str],
sqlglot/generator.py-32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
sqlglot/generator.py-33-    """
---
[tool_use Bash] {"command": "sed -n 1051,1075p sqlglot/generators/snowflake.py; echo ---; sed -n 920,930p sqlglot/generators/snowflake.py; echo ---; grep -n \"def test_\\|JSON_ARRAY\\|json_array\" tests/dialects/test_duckdb.py | head -20; grep -n \"def test_\" tests/dialects/test_snowflake.py | head -3; sed -n 400,412p sqlglot/parsers/duckdb.py; grep -n \"\\\"JSON_\" sqlglot/parsers/duckdb.py", "description": "Read Snowflake array_sql and DuckDB parser function map"}
[tool_result]     def array_sql(self, expression: exp.Array) -> str:
        expressions = expression.expressions

        first_expr = seq_get(expressions, 0)
        if isinstance(first_expr, exp.Select):
            # SELECT AS STRUCT foo AS alias_foo -> ARRAY_AGG(OBJECT_CONSTRUCT('alias_foo', foo))
            if first_expr.text("kind").upper() == "STRUCT":
                object_construct_args = []
                for expr in first_expr.expressions:
                    # Alias case: SELECT AS STRUCT foo 
…[1704 chars elided]…
ameter_token(self):
2216:    def test_iceberg_property_no_warning(self):
2223:    def test_non_iceberg_property_still_warns(self):
2233:    def test_ignore_nulls(self):
2256:    def test_attach_detach(self):
15:    def test_snowflake(self):
3357:    def test_null_treatment(self):
3398:    def test_staged_files(self):
133:        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
134:        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
[tool_use Bash] {"command": "sed -n 128,134p sqlglot/parsers/duckdb.py; grep -n \"def jsonextract_sql\" -B2 sqlglot/generators/snowflake.py", "description": "View DuckDB parser entry and Snowflake JSON method"}
[tool_result]         "GET_BIT": lambda args: exp.Getbit(
            this=seq_get(args, 0), expression=seq_get(args, 1), zero_is_msb=True
        ),
        "JARO_WINKLER_SIMILARITY": exp.JarowinklerSimilarity.from_arg_list,
        "JSON": exp.ParseJSON.from_arg_list,
        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
969-        )
970-
971:    def jsonextract_sql(self, expression: exp.JSONExtract):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\"", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "    def jsonextract_sql(self, expression: exp.JSONExtract):", "new_string": "    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.sql(exp.Array(expressions=expression.expressions))\n\n    def jsonextract_sql(self, expression: exp.JSONExtract):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", 'SELECT JSON_ARRAY()', 'SELECT JSON_ARRAY(x, NULL)']:\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'), sqlglot.transpile(s, read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1) FORMAT', read='oracle', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1) NULL ON NULL', read='oracle', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2)', read='bigquery', write='snowflake'))\n\"", "description": "Verify transpilation output after the change"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/__init__.py", line 212, in transpile
    for expression in parse(sql, read, error_level=error_level)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/_
…[1226 chars elided]…
expected token")
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/parser.py", line 1977, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 28.
  SELECT JSON_ARRAY(1) NULL [4mON[0m NULL
["SELECT ['a', 'b', 'c']"] ["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT []'] ['SELECT JSON_ARRAY()']
['SELECT [x, NULL]'] ['SELECT JSON_ARRAY(x, NULL)']
['SELECT [1] AS FORMAT']
[assistant] The core case now works. The Oracle error is just my malformed input, not a regression. Next I'll add regression tests.
[tool_use Bash] {"command": "grep -n \"snowflake\\\": \\\"SELECT OBJECT_CONSTRUCT\\|\\\"snowflake\\\": \\\"SELECT .*JSON\" tests/dialects/test_duckdb.py | head -5; grep -n \"def test_array(self)\" -A4 tests/dialects/test_duckdb.py", "description": "Find a good spot for DuckDB JSON tests"}
[tool_result] 1950:    def test_array(self):
1951-        self.validate_identity("ARRAY(SELECT id FROM t)")
1952-        self.validate_identity("ARRAY((SELECT id FROM t))")
1953-
1954-    def test_cast(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_cast(self):", "new_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_json_array(self):\n        self.validate_identity(\"SELECT JSON_ARRAY('a', 'b', 'c')\")\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n\n    def test_cast(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] The Snowflake output came back as `['a', 'b', 'c']`, not `ARRAY_CONSTRUCT`. I need to check what Snowflake's existing array rendering does before I trust that output.
[tool_use Bash] {"command": "grep -n \"ARRAY_CONSTRUCT\" tests/dialects/test_snowflake.py | head -8; grep -n \"\\\"snowflake\\\": \\\"SELECT \\[\" tests/dialects/*.py | head -5; grep -n \"def inline_array_sql\" -A6 sqlglot/dialects/dialect.py sqlglot/generator.py | head -12", "description": "Check how Snowflake renders array literals in tests"}
[tool_result] 115:            "SELECT BITMAP_COUNT(BITMAP_CONSTRUCT_AGG(value)) FROM TABLE(FLATTEN(INPUT => ARRAY_CONSTRUCT(1, 2, 3, 5)))",
1234:            "ARRAY_CONSTRUCT_COMPACT(1, null, 2)",
1237:                "snowflake": "ARRAY_CONSTRUCT_COMPACT(1, NULL, 2)",
2169:            """SELECT ARRAY_CONSTRUCT('foo')::VARIANT[0]""",
4061:            "ARRAY_CONSTRUCT(0, 1, 2)",
6701:            "SELECT ARRAY_POSITION(2, ARRAY_CONSTRUCT(1, 2, 3))",
sqlglot/dialects/dialect.py:1205:def inline_array_sql(self: Gen
…[29 chars elided]…
 -> str:
sqlglot/dialects/dialect.py-1206-    return f"[{self.expressions(expression, dynamic=True, new_line=True, skip_first=True, skip_last=True)}]"
sqlglot/dialects/dialect.py-1207-
sqlglot/dialects/dialect.py-1208-
sqlglot/dialects/dialect.py-1209-def inline_array_unless_query(self: Generator, expression: exp.Expr) -> str:
sqlglot/dialects/dialect.py-1210-    elem = seq_get(expression.expressions, 0)
sqlglot/dialects/dialect.py-1211-    if isinstance(elem, exp.Expr) and elem.find(exp.Query):
[assistant] Snowflake's generator renders `exp.Array` as `[...]`, but the issue asks for `ARRAY_CONSTRUCT`, which is valid Snowflake. I'll emit `ARRAY_CONSTRUCT` directly with `self.func`, which is the pattern the project's rules recommend.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        return self.sql(exp.Array(expressions=expression.expressions))", "new_string": "        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", 'SELECT JSON_ARRAY()', 'SELECT JSON_ARRAY(x, NULL)']:\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'), sqlglot.transpile(s, read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2)', read='bigquery', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2 NULL ON NULL)', read='oracle', write='snowflake'))\n\"", "description": "Re-verify transpilation with ARRAY_CONSTRUCT output"}
[tool_result] Argument 'null_handling' is not supported for expression 'JSONArray' when targeting Snowflake.
["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"] ["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()'] ['SELECT JSON_ARRAY()']
['SELECT ARRAY_CONSTRUCT(x, NULL)'] ['SELECT JSON_ARRAY(x, NULL)']
['SELECT ARRAY_CONSTRUCT(1, 2)']
['SELECT ARRAY_CONSTRUCT(1, 2)']
[assistant] The output is correct now. Oracle's `NULL ON NULL` produces the expected unsupported-argument warning. Next I'll run the test suite with the project's checker command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_oracle.py tests/dialects/test_bigquery.py tests/dialects/test_singlestore.py 2>&1 | tail -15", "description": "Run dialect tests for touched dialects"}
[tool_result] ................................................................................................................................................... [ 59%]
.....................................................................................................        [100%]
248 passed, 3633 subtests passed in 1.09s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and check working tree"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
............................................................................................................................................ [ 37%]
................................................................... [ 43%]
..............................................................
…[270 chars elided]…
............................ [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1085 passed, 17838 subtests passed in 49.42s
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] The full suite passes. I'll run the linter on the changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; git diff", "description": "Lint changed files and show the diff"}
[tool_result] All checks passed!
3 files already formatted
diff --git a/sqlglot/generators/snowflake.py b/sqlglot/generators/snowflake.py
index 44fc1f68c..1e7a1dc36 100644
--- a/sqlglot/generators/snowflake.py
+++ b/sqlglot/generators/snowflake.py
@@ -968,6 +968,10 @@ class SnowflakeGenerator(generator.Generator):
             )
         )
 
+    @unsupported_args("null_handling", "return_type", "strict")
+    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
+        return self.func("ARRAY_CONSTRUC
…[1139 chars elided]…
  def test_json_array(self):
+        self.validate_identity("SELECT JSON_ARRAY('a', 'b', 'c')")
+        self.validate_all(
+            "SELECT JSON_ARRAY('a', 'b', 'c')",
+            write={
+                "duckdb": "SELECT JSON_ARRAY('a', 'b', 'c')",
+                "snowflake": "SELECT ARRAY_CONSTRUCT('a', 'b', 'c')",
+            },
+        )
+
     def test_cast(self):
         self.validate_identity("x::int[3]", "CAST(x AS INT[3])")
         self.validate_identity("CAST(x AS REAL)")
[assistant] The `validate_identity` line duplicates the DuckDB entry in `validate_all`, so I'll drop it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"SELECT JSON_ARRAY('a', 'b', 'c')\")\n        self.validate_all(", "new_string": "        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163731-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2", "description": "Re-run DuckDB dialect tests after test cleanup"}
[tool_result] .............................................                 [100%]
45 passed, 587 subtests passed in 0.24s
[assistant] `JSON_ARRAY(...)` from DuckDB now transpiles to valid Snowflake:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full test suite passes (1085 passed), and ruff check and format are clean on the changed files.

**Root cause:** DuckDB's parser had no entry for `JSON_ARRAY`, so it produced an untyped `Anonymous` function that Snowflake passed through unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: map `JSON_ARRAY` to `exp.JSONArray`, the existing expression class.
- `sqlglot/generators/snowflake.py`: add a `jsonar
…[238 chars elided]…
ialects/test_duckdb.py`: add `test_json_array`, which checks the DuckDB round-trip and the Snowflake output.

**Side effect:** the Snowflake change applies to every source dialect that produces `exp.JSONArray`, not just DuckDB. For example, BigQuery's `JSON_ARRAY(1, 2)` now also becomes `ARRAY_CONSTRUCT(1, 2)` for Snowflake, where it previously emitted the invalid `JSON_ARRAY`.

Snowflake's generator renders `exp.Array` as `[...]`, so I emitted `ARRAY_CONSTRUCT` directly rather than reusing that path. The issue names `ARRAY_CONSTRUCT` as the target, so I matched it.

I did not commit anything.
