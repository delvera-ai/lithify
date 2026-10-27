# trajectory base-1

final message:
DuckDB `JSON_ARRAY(...)` now transpiles to valid Snowflake: `SELECT JSON_ARRAY('a', 'b', 'c')` becomes `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`. The full test suite passes (1085 passed) and ruff lint and format are clean on the changed files. I haven't committed.

**Root cause:** DuckDB's parser had no mapping for `JSON_ARRAY`, so it parsed as a generic function and was copied through verbatim. Snowflake's generator then emitted it unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: map `JSON_ARRAY` to `exp.JSONArray`, the same way SingleStore maps `JSON_BUILD_ARRAY`.
- `sqlglot/generators/snowflake.py`: added `jsonarray_sql`, which renders `exp.JSONArray` as `ARRAY_CONSTRUCT(...)`. It's decorated with `@unsupported_args("null_handling", "return_type", "strict")`, so those options emit a warning instead of being silently dropped.
- `tests/dialects/test_duckdb.py`: added `test_json_array`, covering the identity round-trip and the Snowflake output for both the three-argument and empty cases.

**Choices to check:**
- I used `ARRAY_CONSTRUCT(...)` because the issue names it as the equivalent. Snowflake's generator already renders `exp.Array` as bracket syntax (`['a', 'b']`), so if you'd rather match that, it's a one-line change.
- Other dialects are unaffected. DuckDB `JSON_ARRAY` now parses as `JSONArray` and still regenerates as `JSON_ARRAY` for DuckDB, MySQL, and BigQuery.

**Semantic caveat:** DuckDB's `json_array` returns a JSON value, while Snowflake's `ARRAY_CONSTRUCT` returns an ARRAY (VARIANT). The output is valid SQL, but downstream code that relies on the JSON type may need a cast.

## events
[assistant] I'll start by finding where DuckDB's `JSON_ARRAY` is handled and how Snowflake's generator treats it.
[tool_use Bash] {"command": "grep -rn -i \"json_array\\b\\|JSONArray\\b\\|JSON_ARRAY\" sqlglot/ tests/ | grep -v \"JSON_ARRAYAGG\\|JSONB_ARRAY\" | head -60", "description": "Search for JSON_ARRAY references in sqlglot and tests"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:97:        "JSON_ARRAY_CONTAINS_JSON": 
…[5080 chars elided]…
s/dialects/test_dialect.py:4857:                "bigquery": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4858:                "mysql": """JSON_ARRAY_INSERT('["a", ["b", "c"], "d"]', '$[1]', 1)""",
tests/dialects/test_oracle.py:81:            "SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
tests/dialects/test_mysql.py:247:        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
[assistant] Next I'll check how DuckDB parses `JSON_ARRAY` and what the generic `jsonarray_sql` emits. I also want to see how Snowflake handles `ARRAY_CONSTRUCT` today.
[tool_use Bash] {"command": "sed -n 3560,3575p sqlglot/generator.py && echo ---- && sed -n 1,30p sqlglot/expressions/json.py && echo ---- && grep -rn \"ArrayConstruct\\|ARRAY_CONSTRUCT\\|\\\"ARRAY\\\"\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py | head -20 && echo ---- && python3 -c \"import sqlglot\" 2>&1; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Inspect generator, JSONArray class, and Snowflake array handling"}
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
…[618 chars elided]…
se,
        "strict": False,
    }


class JSONArrayAgg(Expression, AggFunc):
    arg_types = {
        "this": True,
        "order": False,
        "null_handling": False,
        "return_type": False,
        "strict": False,
    }


----
sqlglot/parsers/snowflake.py:407:        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
----
<work>/env-sqlglot/bin/python
[assistant] Let me reproduce the bug with the project's Python and see what the DuckDB parse produces.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(e.selects[0]))\nprint(e.sql('snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARR
…[323 chars elided]…
read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 'b')\\\", read='oracle', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 'b')\\\", read='oracle', write='duckdb'))\n\"; cat -n sqlglot/generators/snowflake.py | grep -n \"exp.Array\\b\\|def array_sql\\|Array:\" | head; ", "description": "Reproduce DuckDB to Snowflake JSON_ARRAY transpile"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
SELECT JSON_ARRAY('a', 'b', 'c')
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY(1, 'b')"]
["SELECT ['a', 'b']"]
["SELECT ['a', 'b']"]
["SELECT JSON_ARRAY(1, 'b')"]
["SELECT JSON_ARRAY(1, 'b')"]
271:   271	                if not isinstance(unnest_expr, exp.Array):
413:   413	        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
500:   500	        exp.JSONExtractArray: _json_extract_value_array_sql,
507:   507	        exp.JSONValueArray: _json_extract_value_array_sql,
569:   569	        exp.StringToArray: rename_func("STRTOK_TO_ARRAY"),
586:   586	        exp.ToArray: rename_func("TO_ARRAY"),
1051:  1051	    def array_sql(self, expression: exp.Array) -> str:
[assistant] The root cause is on the DuckDB side. DuckDB's parser doesn't map `JSON_ARRAY`, so it stays an `Anonymous` function and gets copied verbatim. I'll look at the DuckDB parser, the Snowflake `array_sql`, and how SingleStore handles unsupported `JSONArray` args before choosing the fix.
[tool_use Bash] {"command": "ls sqlglot/parsers/ | grep -i duck; grep -n \"FUNCTIONS = {\" -A3 sqlglot/parsers/duckdb.py; grep -n \"\\\"JSON\" sqlglot/parsers/duckdb.py | head; echo ----; sed -n 1051,1062p sqlglot/generators/snowflake.py; echo ----; sed -n 160,170p sqlglot/generators/singlestore.py; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py | head -30; echo ----; grep -n \"def jsonarray_sql\\|JSONArray\" sqlglot/generators/*.py | head", "description": "Check DuckDB parser, Snowflake array_sql, and JSONArray generators"}
[tool_result] duckdb.py
72:    NO_PAREN_FUNCTIONS = {
73-        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: exp.Localtime,
75-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
--
102:    FUNCTIONS = {
103-        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
104-        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
105-        "ARRAY_PREPEND": _build_array_prepend,
132:        "JSON": exp.ParseJSON.from_a
…[2152 chars elided]…
) -> str:
sqlglot/generators/singlestore.py:162:        exp.JSONArrayAgg: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/singlestore.py:1454:    def jsonarraycontains_sql(self, expression: exp.JSONArrayContains) -> str:
sqlglot/generators/sqlite.py:141:        exp.JSONArrayAgg: unsupported_args("order", "null_handling", "return_type", "strict")(
[assistant] The fix has two parts. The DuckDB parser needs to map `JSON_ARRAY` to `exp.JSONArray`, and the Snowflake generator needs to render `JSONArray` as `ARRAY_CONSTRUCT`. I'll check where the Snowflake generator keeps its JSON methods so the new one sits in the right place.
[tool_use Bash] {"command": "grep -n \"    def .*json.*_sql\\|    def array_sql\\|@unsupported_args\" sqlglot/generators/snowflake.py; sed -n 100,103p sqlglot/parsers/duckdb.py; grep -n \"exp.JSON\\|exp.Array\" sqlglot/generators/snowflake.py | head -30", "description": "Locate JSON methods in Snowflake generator"}
[tool_result] 926:    @unsupported_args("weight", "accuracy")
971:    def jsonextract_sql(self, expression: exp.JSONExtract):
1051:    def array_sql(self, expression: exp.Array) -> str:
    }

    FUNCTIONS = {
        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
189:                    exp.select(exp.ArrayAgg(this=exp.Star())).from_(unnest).subquery()
230:    self: SnowflakeGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
232:    json_extract = exp.JS
…[1278 chars elided]…
636:        exp.JSONPathRoot,
637:        exp.JSONPathSubscript,
670:    RESPECT_IGNORE_NULLS_UNSUPPORTED_EXPRESSIONS = (exp.ArrayAgg,)
971:    def jsonextract_sql(self, expression: exp.JSONExtract):
976:        if not isinstance(this, (exp.ParseJSON, exp.JSONExtract)) and not expression.args.get(
1032:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
1048:    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:
1051:    def array_sql(self, expression: exp.Array) -> str:
[assistant] I'll read the insertion area before editing, then make both changes.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "offset": 1028, "limit": 10}
[tool_result] 1028	            return f"{this_name}{self.sep()}{copy_grants}{this_schema}"
1029	
1030	        return super().createable_sql(expression, locations)
1031	
1032	    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
1033	        this = expression.this
1034	
1035	        # If an ORDER BY clause is present, we need to remove it from ARRAY_AGG
1036	        # and add it later as part of the WITHIN GROUP clause
1037	        order = this if isinstance(this, exp.Order) else None
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        return super().createable_sql(expression, locations)\n\n    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:", "new_string": "        return super().createable_sql(expression, locations)\n\n    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)\n\n    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now I'll re-run the reproduction and a few edge cases: a zero-arg call, the `strict` warning path, and DuckDB round-tripping.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY()\\\", read='duckdb', write='snowflake'))\nprint(sqlgl
…[97 chars elided]…
.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='duckdb', write='mysql'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='duckdb', write='bigquery'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='duckdb', write='singlestore'))\n\" && $PY -c \"import duckdb; print(duckdb.__version__)\" 2>&1 | tail -1", "description": "Verify DuckDB to Snowflake JSON_ARRAY output"}
[tool_result] ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()']
["SELECT JSON_ARRAY('a', NULL)"]
['SELECT JSON_ARRAY(1, 2)']
['SELECT JSON_ARRAY(1, 2)']
['SELECT JSON_BUILD_ARRAY(1, 2)']
1.5.6
[assistant] The output is now valid Snowflake for the reported case and the edge cases I checked. Next I'll add a regression test next to the existing DuckDB-to-Snowflake tests, following their style.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_duckdb.py | head -80 | tail -40; grep -n \"def test_json\" tests/dialects/test_duckdb.py; grep -n \"ARRAY_CONSTRUCT\" tests/dialects/test_snowflake.py | head -3", "description": "Find test locations in DuckDB and Snowflake test files"}
[tool_result] 1667:    def test_array_remove_at(self):
1732:    def test_time(self):
1902:    def test_sample(self):
1950:    def test_array(self):
1954:    def test_cast(self):
2130:    def test_encode_decode(self):
2162:    def test_sha(self):
2169:    def test_rename_table(self):
2187:    def test_timestamps_with_units(self):
2195:    def test_isnan(self):
2202:    def test_isinf(self):
2209:    def test_parameter_token(self):
2216:    def test_iceberg_property_no_warning(self):
2223:    def test_non_icebe
…[779 chars elided]…
def test_current_schema(self):
2635:    def test_current_schemas(self):
2647:    def test_map_delete(self):
2667:    def test_map_size(self):
2687:    def test_map_pick(self):
2722:    def test_to_array(self):
2751:    def test_map_insert(self):
115:            "SELECT BITMAP_COUNT(BITMAP_CONSTRUCT_AGG(value)) FROM TABLE(FLATTEN(INPUT => ARRAY_CONSTRUCT(1, 2, 3, 5)))",
1234:            "ARRAY_CONSTRUCT_COMPACT(1, null, 2)",
1237:                "snowflake": "ARRAY_CONSTRUCT_COMPACT(1, NULL, 2)",
[tool_use Bash] {"command": "sed -n 2722,2751p tests/dialects/test_duckdb.py", "description": "Read the to_array test for style reference"}
[tool_result]     def test_to_array(self):
        self.validate_all(
            "SELECT CASE WHEN 'hello, snowman' IS NULL THEN NULL ELSE ['hello, snowman'] END AS result",
            read={
                "snowflake": "SELECT TO_ARRAY('hello, snowman') AS result",
            },
            write={
                "duckdb": "SELECT CASE WHEN 'hello, snowman' IS NULL THEN NULL ELSE ['hello, snowman'] END AS result",
            },
        )
        self.validate_all(
            "SELECT CASE WHEN 4.2 IS N
…[98 chars elided]…
O_ARRAY(4.2) AS result",
            },
            write={
                "duckdb": "SELECT CASE WHEN 4.2 IS NULL THEN NULL ELSE [4.2] END AS result",
            },
        )
        self.validate_all(
            "SELECT ['a', 'b'] AS result",
            read={
                "snowflake": "SELECT TO_ARRAY(ARRAY_CONSTRUCT('a', 'b')) AS result",
            },
            write={
                "duckdb": "SELECT ['a', 'b'] AS result",
            },
        )

    def test_map_insert(self):
[assistant] I'll add one focused test in the DuckDB dialect file, covering identity, the Snowflake output, and an empty call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "                \"duckdb\": \"SELECT ['a', 'b'] AS result\",\n            },\n        )\n\n    def test_map_insert(self):", "new_string": "                \"duckdb\": \"SELECT ['a', 'b'] AS result\",\n       
…[339 chars elided]…
         \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n        self.validate_all(\n            \"SELECT ARRAY_CONSTRUCT()\",\n            read={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n            },\n            write={\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT()\",\n            },\n        )\n\n    def test_map_insert(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Next I'll run the full project test suite with the command from the repo's harness notes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 600000}
[tool_result] .................... [ 26%]
......................................................................................................................................... [ 38%]
......... [ 39%]
..................... [ 41%]
................... [ 43%]
.................... [ 45%]
.......................................................................................... [ 53%]
................................................................................................................................
…[1025 chars elided]…
assertEqual(
E   AssertionError: 'SELECT JSON_ARRAY()' != 'SELECT ARRAY_CONSTRUCT()'
E   - SELECT JSON_ARRAY()
E   + SELECT ARRAY_CONSTRUCT()
=========================== short test summary info ============================
SUBFAILED[duckdb -> SELECT ARRAY_CONSTRUCT('a', 'b', 'c')] tests/dialects/test_duckdb.py::TestDuckDB::test_json_array
SUBFAILED[duckdb -> SELECT ARRAY_CONSTRUCT()] tests/dialects/test_duckdb.py::TestDuckDB::test_json_array
2 failed, 1085 passed, 17838 subtests passed in 49.51s
[assistant] Both failures are in my test, not the fix. `validate_all` takes the DuckDB-side SQL as its first argument and checks the `write` entries against it, so I had the two sides swapped. I'll fix the test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"SELECT JSON_ARRAY('a', 'b', 'c')\")\n        self.validate_all(\n            \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            read={\n                \"duckdb\": \"SELE
…[507 chars elided]…
AY('a', 'b', 'c')\")\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT()\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-155049-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k json_array 2>&1 | tail -2; git status --short", "description": "Re-run full suite and check git status", "timeout": 600000}
[tool_result] .......................... [ 98%]
..................              [100%]
1085 passed, 17838 subtests passed in 58.88s
.                                                                      [100%]
1 passed, 44 deselected, 2 subtests passed in 0.07s
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] The full suite passes. Repo guidance also asks for lint and format checks, so I'll run ruff on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && ($PY -m ruff --version && $PY -m ruff check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
[assistant] DuckDB `JSON_ARRAY(...)` now transpiles to valid Snowflake: `SELECT JSON_ARRAY('a', 'b', 'c')` becomes `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`. The full test suite passes (1085 passed) and ruff lint and format are clean on the changed files. I haven't committed.

**Root cause:** DuckDB's parser had no mapping for `JSON_ARRAY`, so it parsed as a generic function and was copied through verbatim. Snowflake's generator then emitted it unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: map `JSON_ARRAY` to `exp.JSONArray`, the same way SingleStore maps `JSON_BUILD_ARRAY`.
- `sqlglot/generators/
…[418 chars elided]…
 to check:**
- I used `ARRAY_CONSTRUCT(...)` because the issue names it as the equivalent. Snowflake's generator already renders `exp.Array` as bracket syntax (`['a', 'b']`), so if you'd rather match that, it's a one-line change.
- Other dialects are unaffected. DuckDB `JSON_ARRAY` now parses as `JSONArray` and still regenerates as `JSON_ARRAY` for DuckDB, MySQL, and BigQuery.

**Semantic caveat:** DuckDB's `json_array` returns a JSON value, while Snowflake's `ARRAY_CONSTRUCT` returns an ARRAY (VARIANT). The output is valid SQL, but downstream code that relies on the JSON type may need a cast.
