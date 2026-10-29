# trajectory base-1

final message:
DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

**Cause:** DuckDB's parser had no entry for `JSON_ARRAY`, so it became an anonymous function and was emitted unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: `JSON_ARRAY` now parses to `exp.JSONArray`, the same expression other dialects use.
- `sqlglot/generators/snowflake.py`: `exp.JSONArray` is generated as `ARRAY_CONSTRUCT(...)`. `null_handling`, `return_type` and `strict` are flagged as unsupported, matching the Singlestore generator.
- `tests/dialects/test_duckdb.py`: a DuckDB→Snowflake case that checks the new output and a DuckDB round-trip.

**Verification:** the full suite passes (1084 tests), and ruff lint and format checks pass on the changed files.

**Things to know:**
- I used a lambda rather than `rename_func`. `rename_func` passes every arg value through, so an Oracle `ABSENT ON NULL` leaked into the output as an argument. The lambda avoids that.
- The change also affects other inputs that parse to `JSONArray`, such as BigQuery `JSON_ARRAY` and Oracle `JSON_ARRAY`. Those used to produce invalid Snowflake SQL and now produce `ARRAY_CONSTRUCT`.
- Semantic difference: DuckDB's `JSON_ARRAY` returns a JSON value, while Snowflake's `ARRAY_CONSTRUCT` returns an ARRAY (VARIANT). The output is valid SQL and matches the usual mapping, but downstream code that expects a JSON string may behave differently.

I haven't committed anything. The changes are in the worktree for you to review.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"json_array\\|JSONArray\\|ARRAY_CONSTRUCT\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py sqlglot/generator.py sqlglot/parser.py | head -60", "description": "Search for JSON_ARRAY handling across dialects"}
[tool_result] okgrep: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3575:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parser.py:142:def build_array_constructor(
sqlglot/parser.py:147:    if exp_class == exp.Array and dialect.HAS_DISTINCT_ARRAY_CONSTRUCTORS:
sqlglot/parser.py:773:    ARRAY_CONSTRUCTORS: t.ClassVar = {
sqlglot/parser.py:7465:            this = build_array_constructor(
sqlglot/parser.py:7469:            constructor_type = self.ARRAY_CONSTRUCTORS.get(this.name.upper())
sqlglot/parser.py:7471:                return build_array_constructor(
[tool_use Bash] {"command": "grep -rn -i \"JSONArray\\b\\|JSON_ARRAY\\\"\\|\\\"JSON_ARRAY\\|ARRAY_CONSTRUCT\\|JSONArray:\" sqlglot/ | grep -v JSONArrayAgg | head -40; echo ---; grep -n -A12 \"class JSONArray(\" sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Locate JSONArray expression and related handling"}
[tool_result ERROR] Exit code 2
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:97:        "JSON_ARRAY_CONTAINS_JSON": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lam
…[2930 chars elided]…
xpressions/json.py-15-        "null_handling": False,
sqlglot/expressions/json.py-16-        "return_type": False,
sqlglot/expressions/json.py-17-        "strict": False,
sqlglot/expressions/json.py-18-    }
sqlglot/expressions/json.py-19-
sqlglot/expressions/json.py-20-
sqlglot/expressions/json.py-21-class JSONArrayAgg(Expression, AggFunc):
sqlglot/expressions/json.py-22-    arg_types = {
sqlglot/expressions/json.py-23-        "this": True,
sqlglot/expressions/json.py-24-        "order": False,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake')))\nprint(repr(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='duckdb')))\nprint(repr(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='
…[366 chars elided]…
son_array\\|JSONArray\" sqlglot/dialects/duckdb.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py; grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head; git log --oneline -3 -- sqlglot/generators/snowflake.py", "description": "Reproduce JSON_ARRAY transpilation across dialects"}
[tool_result] ["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
0 matches for 'JSON_ARRAY\|JSONArray'
c16630f61 fix(snowflake): map JSON type to VARIANT in Snowflake generator [CLAUDE] (#7496)
713e95fb9 Fix(snowflake): parse GET_DDL #unknown_policy in ROW ACCESS POLICY [CLAUDE] (#7491)
800c0c44b Fix(snowflake): emit proper `HANDLER` property syntax
[tool_use Bash] {"command": "grep -n \"exp.Array\\b\\|exp.Array:\\|ARRAY_CONSTRUCT\\|def array_sql\\|unsupported_args\" sqlglot/generators/snowflake.py | head -20; echo ---; grep -n \"FUNCTIONS\\|\\\"JSON\\|ARRAY\" sqlglot/parsers/duckdb.py | head -40; echo ---; sed -n 160,175p sqlglot/generators/singlestore.py; echo ---; grep -n \"def jsonarray_sql\" -A10 sqlglot/generator.py; echo; grep -rn \"JSON_ARRAY\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_bigquery.py | head", "description": "Inspect Snowflake/DuckDB parser and generator code"}
[tool_result] 6 matches in 5 files:

1051:0:exp.Array) -> str:
271:0:
413:0:transforms.preprocess([transforms.inherit_struct_field_names]),
508:0:unsupported_args("ins_cost", "del_cost", "sub_cost")(
sqlglot/generators/snowflake.py:27:from sqlglot.generator import unsupported_args
sqlglot/generators/snowflake.py:926:@unsupported_args("weight", "accuracy")
---
13 matches in 10 files:

103:0:v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
105:0:_build_array_prepend,
106:0:_build
…[2343 chars elided]…
_element => FALSE)"""
tests/dialects/test_bigquery.py:3338:        self.validate_identity("JSON_ARRAY()")
tests/dialects/test_bigquery.py:3339:        self.validate_identity("JSON_ARRAY(10)")
tests/dialects/test_bigquery.py:3340:        self.validate_identity("JSON_ARRAY([])")
tests/dialects/test_bigquery.py:3341:        self.validate_identity("JSON_ARRAY(STRUCT(10 AS a, 'foo' AS b))")
tests/dialects/test_bigquery.py:3342:        self.validate_identity("JSON_ARRAY(10, ['foo', 'bar'], [20, 30])")
[tool_use Bash] {"command": "sed -n 1045,1060p sqlglot/generators/snowflake.py; echo ---; sed -n 100,135p sqlglot/parsers/duckdb.py; echo ---; grep -n \"ARRAY_CONSTRUCT\\|exp.Array:\" sqlglot/generators/*.py | head; echo ---; grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/test_*.py | head", "description": "Inspect Snowflake array generation and DuckDB parser table"}
[tool_result]         return expr_sql

    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:
        return self.func("ARRAY_TO_STRING", expression.this, expression.expression)

    def array_sql(self, expression: exp.Array) -> str:
        expressions = expression.expressions

        first_expr = seq_get(expressions, 0)
        if isinstance(first_expr, exp.Select):
            # SELECT AS STRUCT foo AS alias_foo -> ARRAY_AGG(OBJECT_CONSTRUCT('alias_foo', foo))
            if first_expr.tex
…[2319 chars elided]…
 self, e: f"ARRAY[{self.expressions(e)}]",
sqlglot/generators/duckdb.py:1498:exp.Array: transforms.preprocess(
sqlglot/generators/hive.py:243:exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
sqlglot/generators/presto.py:270:exp.Array: transforms.preprocess(
sqlglot/generators/snowflake.py:413:exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
sqlglot/generators/starrocks.py:90:exp.Array: inline_array_sql,
---
0 matches for 'JSON_ARRAY\|JSONArray'
[tool_use Bash] {"command": "grep -n \"def test_\\|JSON_EXTRACT_PATH\\|\\\"JSON\\\"\" tests/dialects/test_duckdb.py | head -80; echo ---; grep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/snowflake.py | head; grep -n \"rename_func\\|unsupported_args\" sqlglot/generators/snowflake.py | head -5", "description": "Find test and transform locations for edits"}
[tool_result] 46 matches in 45 files:

13:0:
1561:0:
1601:0:
1642:0:
1667:0:
1732:0:
1902:0:
1950:0:
1954:0:
2130:0:
2162:0:
2169:0:
2187:0:
2195:0:
2202:0:
2209:0:
2216:0:
2223:0:
2233:0:
2256:0:
2277:0:
2305:0:
2319:0:
2322:0:
2405:0:
2431:0:
2438:0:
2455:0:
2473:0:
2484:0:
2489:0:
2498:0:
2510:0:
2518:0:
2541:0:
2592:0:
2611:0:
2623:0:
2635:0:
2647:0:
2667:0:
2687:0:
2722:0:
2751:0:
tests/dialects/test_duckdb.py:597:"JSON_EXTRACT_PATH(x, '$.family')",
tests/dialects/test_duckdb.py:605:"JSON_EXTRACT_PATH_TEXT(x, '$.family')",
---
408:    TRANSFORMS = {
409-        **generator.Generator.TRANSFORMS,
410-        exp.ApproxDistinct: rename_func("APPROX_COUNT_DISTINCT"),
411-        exp.ArgMax: rename_func("MAX_BY"),
59 matches in 54 files:

410:0:rename_func("APPROX_COUNT_DISTINCT"),
411:0:rename_func("MAX_BY"),
412:0:rename_func("MIN_BY"),
[tool_use Bash] {"command": "sed -n 590,612p tests/dialects/test_duckdb.py; echo ---; grep -n \"exp.JSON\\|exp.Array:\" sqlglot/generators/snowflake.py | head; grep -n \"JSON_EXTRACT_STRING\\|\\\"JSON\\\":\" sqlglot/parsers/duckdb.py", "description": "View JSON test block and snowflake transforms"}
[tool_result]             "SELECT 'foo'",
        )
        self.validate_identity(
            "JSON_EXTRACT(x, '$.family')",
            "x -> '$.family'",
        )
        self.validate_identity(
            "JSON_EXTRACT_PATH(x, '$.family')",
            "x -> '$.family'",
        )
        self.validate_identity(
            "JSON_EXTRACT_STRING(x, '$.family')",
            "x ->> '$.family'",
        )
        self.validate_identity(
            "JSON_EXTRACT_PATH_TEXT(x, '$.family')",
            "x -
…[200 chars elided]…
s in 12 files:

230:0:SnowflakeGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
235:0:
413:0:transforms.preprocess([transforms.inherit_struct_field_names]),
500:0:_json_extract_value_array_sql,
501:0:lambda self, e: self.func(
504:0:rename_func("OBJECT_KEYS"),
505:0:lambda self, e: self.func("OBJECT_CONSTRUCT_KEEP_NULL", *e.expressions),
506:0:lambda *_: "",
2 matches in 2 files:

132:0:exp.ParseJSON.from_arg_list,
134:0:parser.build_extract_json_with_path(exp.JSONExtractScalar),
[assistant] Confirmed: DuckDB parses `JSON_ARRAY` as an anonymous function, so it passes through unchanged. I'll map it to `exp.JSONArray` in the DuckDB parser, then map `JSONArray` to `ARRAY_CONSTRUCT` in the Snowflake generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\": ", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\":"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "offset": 406, "limit": 20}
[tool_result] 406	    TRY_SUPPORTED = False
407	
408	    TRANSFORMS = {
409	        **generator.Generator.TRANSFORMS,
410	        exp.ApproxDistinct: rename_func("APPROX_COUNT_DISTINCT"),
411	        exp.ArgMax: rename_func("MAX_BY"),
412	        exp.ArgMin: rename_func("MIN_BY"),
413	        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
414	        exp.ArrayConcat: array_concat_sql("ARRAY_CAT"),
415	        exp.ArrayAppend: array_append_sql("ARRAY_APPEND"),
416	        exp.ArrayPrepend: array_append_sql("ARRAY_PREPEND"),
417	        exp.ArrayContains: lambda self, e: self.func(
418	            "ARRAY_CONTAINS",
419	            e.expression
420	            if e.args.get("ensure_variant") is False
421	            else exp.cast(e.expression, exp.DType.VARIANT, copy=False),
422	            e.this,
423	        ),
424	        exp.ArrayPosition: lambda self, e: self.func(
425	            "ARRAY_POSITION",
[tool_use Bash] {"command": "awk 'NR>=408 && NR<=560 && /^        exp\\.[A-Za-z]+:/ {print NR\": \"$0}' sqlglot/generators/snowflake.py | sed -n '1,200p' | grep -n \"exp\\.I\\|exp\\.J\\|exp\\.L\" ", "description": "Find alphabetical insertion point in Snowflake TRANSFORMS"}
[tool_result] 25:446:         exp.Localtime: lambda self, e: (
26:449:         exp.Localtimestamp: lambda self, e: (
49:499:         exp.If: if_sql(name="IFF", false_value="NULL"),
50:500:         exp.JSONExtractArray: _json_extract_value_array_sql,
51:501:         exp.JSONExtractScalar: lambda self, e: self.func(
52:504:         exp.JSONKeys: rename_func("OBJECT_KEYS"),
53:505:         exp.JSONObject: lambda self, e: self.func("OBJECT_CONSTRUCT_KEEP_NULL", *e.expressions),
54:506:         exp.JSONPathRoot: lambda *_: "",
55:507:         exp.JSONValueArray: _json_extract_value_array_sql,
56:508:         exp.Levenshtein: unsupported_args("ins_cost", "del_cost", "sub_cost")(
57:511:         exp.LocationProperty: lambda self, e: f"LOCATION={self.sql(e, 'this')}",
58:512:         exp.LogicalAnd: rename_func("BOOLAND_AGG"),
59:513:         exp.LogicalOr: rename_func("BOOLOR_AGG"),
70:534:         exp.JSONFormat: rename_func("TO_JSON"),
81:559:         exp.LowerHex: rename_func("TO_CHAR"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        exp.JSONExtractArray: _json_extract_value_array_sql,\n        exp.JSONExtractScalar: lambda self, e: self.func(", "new_string": "        exp.JSONArray: unsupported_args(\"null_handling\", \"return_type\", \"strict\")(\n            rename_func(\"ARRAY_CONSTRUCT\")\n        ),\n        exp.JSONExtractArray: _json_extract_value_array_sql,\n        exp.JSONExtractScalar: lambda self, e: self.func("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor w in ['snowflake','duckdb','bigquery','postgres']:\n    print(w, sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c'), JSON_ARRAY()\\\", read='duckdb', write=w))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, NULL ABSENT ON NULL)', read='oracle', write='snowflake'))\n\"", "description": "Verify transpilation output for several dialects"}
[tool_result] Argument 'null_handling' is not supported for expression 'JSONArray' when targeting Snowflake.
snowflake ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c'), ARRAY_CONSTRUCT()"]
duckdb ["SELECT JSON_ARRAY('a', 'b', 'c'), JSON_ARRAY()"]
bigquery ["SELECT JSON_ARRAY('a', 'b', 'c'), JSON_ARRAY()"]
postgres ["SELECT JSON_ARRAY('a', 'b', 'c'), JSON_ARRAY()"]
['SELECT ARRAY_CONSTRUCT(ABSENT ON NULL, 1, NULL)']
[assistant] The DuckDB→Snowflake case now produces `ARRAY_CONSTRUCT`. The Oracle case looks wrong, though: `ABSENT ON NULL` leaks into the argument list. I'll check whether that is pre-existing or caused by my change.
[tool_use Bash] {"command": "sed -n 110,125p sqlglot/parsers/oracle.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, NULL ABSENT ON NULL)', read='oracle', write='oracle'))\nprint(repr(sqlglot.parse_one('SELECT JSON_ARRAY(1, NULL ABSENT ON NULL)', read='oracle').selects[0].args))\n\"; git stash list | head -0; git diff --stat", "description": "Check Oracle JSON_ARRAY parse tree and round-trip"}
[tool_result]         return None

    def _parse_oracle_json_array(self) -> exp.JSONArray:
        return self._parse_json_array(
            exp.JSONArray,
            expressions=self._parse_csv(lambda: self._parse_format_json(self._parse_bitwise())),
        )

    def _parse_oracle_json_arrayagg(self) -> exp.JSONArrayAgg:
        return self._parse_json_array(
            exp.JSONArrayAgg,
            this=self._parse_format_json(self._parse_bitwise()),
            order=self._parse_order(),
        )

 
…[179 chars elided]…
: False, 'expressions': [Literal(this=1, is_string=False), Null()], 'join_mark': False}
head: illegal line count -- 0

thread 'main' (41241521) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
sqlglot/generators/snowflake.py | 3 +++
 sqlglot/parsers/duckdb.py       | 3 ++-
 2 files changed, 5 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "grep -n \"def unsupported_args\" -A25 sqlglot/generator.py | head -40; grep -n \"def rename_func\" -A8 sqlglot/dialects/dialect.py", "description": "Read unsupported_args and rename_func implementations"}
[tool_result] 30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
34-    Decorator that can be used to mark certain args of an `Expr` subclass as unsupported.
35-    It expects a sequence of argument names or pairs of the form (argument_name, diagnostic_msg).
36-    """
37-    diagnostic_by_arg: dict[str, str | None] = {}
38-    for arg in args:
39-        if isinstance(arg, str):
40-            diagnostic_by_arg[arg] = None
41-     
…[592 chars elided]…
_name, dialect_name
54-                    )
55-                    generator.unsupported(diagnostic)
1161:def rename_func(name: str) -> t.Callable[[Generator, exp.Expr], str]:
1162-    return lambda self, expression: self.func(name, *flatten(expression.args.values()))
1163-
1164-
1165-def bracket_to_element_at_sql(self: Generator, expression: exp.Bracket) -> str:
1166-    index = seq_get(
1167-        apply_index_offset(
1168-            expression.this,
1169-            expression.expressions,
[assistant] `rename_func` passes every arg value through, so `null_handling` leaks into the call. The Snowflake generator already uses the `self.func(..., *e.expressions)` idiom for `JSONObject`, so I'll follow that instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        exp.JSONArray: unsupported_args(\"null_handling\", \"return_type\", \"strict\")(\n            rename_func(\"ARRAY_CONSTRUCT\")\n        ),", "new_string": "        exp.JSONArray: unsupported_args(\"null_handling\", \"return_type\", \"strict\")(\n            lambda self, e: self.func(\"ARRAY_CONSTRUCT\", *e.expressions)\n        ),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c'), JSON_ARRAY()\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, NULL ABSENT ON NULL)', read='oracle', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a')\\\", read='bigquery', write='snowflake'))\n\"", "description": "Re-verify Snowflake output after generator fix"}
[tool_result] Argument 'null_handling' is not supported for expression 'JSONArray' when targeting Snowflake.
["SELECT ARRAY_CONSTRUCT('a', 'b', 'c'), ARRAY_CONSTRUCT()"]
['SELECT ARRAY_CONSTRUCT(1, NULL)']
["SELECT ARRAY_CONSTRUCT('a')"]
[assistant] Output is now valid Snowflake for DuckDB, BigQuery, and Oracle inputs. Next I'll add a regression test to the DuckDB test file, next to the existing JSON tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\n            \"JSON_EXTRACT_PATH_TEXT(x, '$.family')\",\n            \"x ->> '$.family'\",\n        )\n", "new_string": "        self.validate_identity(\n            \"JSON_EXTRACT_PATH_TEXT(x, '$.family')\",\n            \"x ->> '$.family'\",\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_oracle.py tests/dialects/test_bigquery.py tests/dialects/test_singlestore.py 2>&1 | tail -15", "description": "Run related dialect test files"}
[tool_result] ................................................................................................................................................... [ 59%]
............................................... [ 78%]
.....................................................         [100%]
247 passed, 3633 subtests passed in 1.02s
[assistant] Related dialect tests pass. Now the full suite, which is the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git diff", "description": "Run full test suite and show final diff"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
................................. [ 27%]
................................................................................................................................................................................................. [ 45%]
...........................................
…[1842 chars elided]…
 parser.build_array_concat,
  +2 -1

tests/dialects/test_duckdb.py
  @@ -605,6 +605,13 @@ class TestDuckDB(Validator):
  +        self.validate_all(
  +            "SELECT JSON_ARRAY('a', 'b', 'c')",
  +            write={
  +                "duckdb": "SELECT JSON_ARRAY('a', 'b', 'c')",
  +                "snowflake": "SELECT ARRAY_CONSTRUCT('a', 'b', 'c')",
  +            },
  +        )
           self.validate_all(
               "SELECT NOT (data -> '$.value')",
               read={
  +7 -0
[assistant] The full suite passes (1084 tests). The diff shows a missing space after `"JSON_EXTRACT_PATH":` in the DuckDB parser, which my edit introduced. I'll fix that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON_EXTRACT_PATH\":parser.build_extract_json_with_path(exp.JSONExtract),", "new_string": "        \"JSON_EXTRACT_PATH\": parser.build_extract_json_with_path(exp.JSONExtract),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-133835-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "git diff sqlglot/parsers/duckdb.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2 && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Fix spacing, rerun DuckDB tests and lint/format checks"}
[tool_result] sqlglot/parsers/duckdb.py | 1 +
 1 file changed, 1 insertion(+)

--- Changes ---

sqlglot/parsers/duckdb.py
  @@ -130,6 +130,7 @@ class DuckDBParser(parser.Parser):
  +        "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
           "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
           "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
           "LIST_APPEND": exp.ArrayAppend.from_arg_list,
  +1 -0
............................................                  [100%]
44 passed, 587 subtests passed in 0.23s
All checks passed!
3 files already formatted
[assistant] DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

**Cause:** DuckDB's parser had no entry for `JSON_ARRAY`, so it became an anonymous function and was emitted unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: `JSON_ARRAY` now parses to `exp.JSONArray`, the same expression other dialects use.
- `sqlglot/generators/snowflake.py`: `exp.JSONArray` is generated as `ARRAY_CONSTRUCT(...)`. `null_handling`, `return_type` and `strict` are flagged as un
…[415 chars elided]…
eaked into the output as an argument. The lambda avoids that.
- The change also affects other inputs that parse to `JSONArray`, such as BigQuery `JSON_ARRAY` and Oracle `JSON_ARRAY`. Those used to produce invalid Snowflake SQL and now produce `ARRAY_CONSTRUCT`.
- Semantic difference: DuckDB's `JSON_ARRAY` returns a JSON value, while Snowflake's `ARRAY_CONSTRUCT` returns an ARRAY (VARIANT). The output is valid SQL and matches the usual mapping, but downstream code that expects a JSON string may behave differently.

I haven't committed anything. The changes are in the worktree for you to review.
