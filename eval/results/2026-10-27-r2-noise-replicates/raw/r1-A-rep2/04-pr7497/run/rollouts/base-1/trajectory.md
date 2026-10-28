# trajectory base-1

final message:
DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full test suite passes (1084 tests), and ruff check and format are clean on the changed files. I haven't committed anything.

The change has three parts:

- **`sqlglot/parsers/duckdb.py`**: DuckDB's `JSON_ARRAY` now parses to `exp.JSONArray` instead of an opaque `Anonymous` function. Same-dialect output is unchanged (`JSON_ARRAY('a', 'b', 'c')`).
- **`sqlglot/generators/snowflake.py`**: a new `jsonarray_sql` emits `ARRAY_CONSTRUCT(...)`. It is decorated with `@unsupported_args("null_handling", "return_type", "strict")`, since Snowflake has no equivalent for those options. Those are only set by Oracle-style syntax, so this doesn't affect DuckDB input.
- **`tests/dialects/test_duckdb.py`**: a `validate_all` case covering the DuckDB-to-Snowflake mapping and the DuckDB round trip.

One decision to review: my first attempt used `exp.Array`, but Snowflake rendered it as bracket syntax (`['a', 'b', 'c']`) rather than `ARRAY_CONSTRUCT`. I switched to calling `ARRAY_CONSTRUCT` directly, which matches the function you named.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\b\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -50", "description": "Search for JSON_ARRAY references in sources and tests"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers
…[4002 chars elided]…
B) AS JSON_DATA FROM tablename"
tests/dialects/test_oracle.py:81:            "SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
tests/dialects/test_oracle.py:84:            "SELECT JSON_ARRAYAGG(FOO() FORMAT JSON ORDER BY bar NULL ON NULL RETURNING CLOB STRICT)"
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/expressions/json.py:34:    _sql_names = ["JSON_ARRAY_APPEND"]
sqlglot/expressions/json.py:39:    _sql_names = ["JSON_ARRAY_CONTAINS"]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT JSON_ARRAY(\\'a\\', \\'b\\', \\'c\\')']:\n    e = sqlglot.parse_one(s, read='duckdb')\n    print(repr(e))\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'))\n\"", "description": "Check no JSON_ARRAY hits and inspect parsed AST"}
[tool_result] Select(
  expressions=[
    Anonymous(
      this=JSON_ARRAY,
      expressions=[
        Literal(this='a', is_string=True),
        Literal(this='b', is_string=True),
        Literal(this='c', is_string=True)])])
["SELECT JSON_ARRAY('a', 'b', 'c')"]
[assistant] The DuckDB parser leaves `JSON_ARRAY` as an `Anonymous` function. Next I'll check the base `JSONArray` generator and how Snowflake handles array construction.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/expressions/json.py && sed -n 3560,3580p sqlglot/generator.py && grep -n \"ArrayConstruct\\|JSONArray\\|ARRAY_CONSTRUCT\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py 2>/dev/null; grep -n \"class JSONArray\\|class ArrayConstruct\\|class Array(\" -A6 sqlglot/expressions/*.py | head -40", "description": "Inspect JSONArray expr, generator, and Snowflake array handling"}
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
        
…[3070 chars elided]…
pes = {"this": True, "expressions": True}
sqlglot/expressions/json.py-33-    is_var_len_args = True
sqlglot/expressions/json.py-34-    _sql_names = ["JSON_ARRAY_APPEND"]
sqlglot/expressions/json.py-35-
sqlglot/expressions/json.py-36-
sqlglot/expressions/json.py:37:class JSONArrayContains(Expression, Binary, Predicate, Func):
sqlglot/expressions/json.py-38-    arg_types = {"this": True, "expression": True, "json_type": False}
sqlglot/expressions/json.py-39-    _sql_names = ["JSON_ARRAY_CONTAINS"]
[assistant] The fix has two parts: DuckDB should parse `JSON_ARRAY` into `exp.JSONArray`, and Snowflake should generate that as `ARRAY_CONSTRUCT`. I'll check the existing DuckDB parser `FUNCTIONS` table, the Snowflake generator, and the `unsupported_args` pattern.
[tool_use Bash] {"command": "ls sqlglot/parsers/ | grep -i \"duck\\|snow\"; grep -n \"FUNCTIONS\" -A3 sqlglot/parsers/duckdb.py | head; grep -n \"\\\"JSON_\\|JSON\" sqlglot/parsers/duckdb.py | head -30; grep -n \"unsupported_args\\|^from\\|^import\" sqlglot/generators/snowflake.py | head -20; grep -n \"def .*_sql\\|exp.Array:\" sqlglot/generators/snowflake.py | head -80 | grep -i \"array\\|json\"; grep -n \"exp.Array\\b\" -A3 sqlglot/generators/snowflake.py | head", "description": "Locate DuckDB/Snowflake parser and generator code"}
[tool_result] duckdb.py
snowflake.py
72:    NO_PAREN_FUNCTIONS = {
73:        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: exp.Localtime,
75-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
76-        TokenType.CURRENT_CATALOG: exp.CurrentCatalog,
--
95:    FUNCTIONS_WITH_ALIASED_ARGS = {*parser.Parser.FUNCTIONS_WITH_ALIASED_ARGS, "STRUCT_PACK"}
96-
97-    SHOW_PARSERS = {
98-        "TABLES": _show_parser("TABLES"),
132:        "JSON": exp.ParseJSON.from_arg_list,
133:        "JSO
…[1152 chars elided]…
:    def array_sql(self, expression: exp.Array) -> str:
271:                if not isinstance(unnest_expr, exp.Array):
272-                    continue
273-
274-                for array_expr in unnest_expr.expressions:
--
413:        exp.Array: transforms.preprocess([transforms.inherit_struct_field_names]),
414-        exp.ArrayConcat: array_concat_sql("ARRAY_CAT"),
415-        exp.ArrayAppend: array_append_sql("ARRAY_APPEND"),
416-        exp.ArrayPrepend: array_append_sql("ARRAY_PREPEND"),
--
[tool_use Bash] {"command": "sed -n 120,145p sqlglot/parsers/duckdb.py; sed -n 1045,1060p sqlglot/generators/snowflake.py; sed -n 920,935p sqlglot/generators/snowflake.py; grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head; grep -n \"def test_json\\|def test_duckdb\" tests/dialects/test_duckdb.py | head -5", "description": "View Snowflake array_sql, unsupported examples, and DuckDB test layout"}
[tool_result]         "EDITDIST3": exp.Levenshtein.from_arg_list,
        "ENCODE": lambda args: exp.Encode(
            this=seq_get(args, 0), charset=exp.Literal.string("utf-8")
        ),
        "EPOCH": exp.TimeToUnix.from_arg_list,
        "EPOCH_MS": lambda args: exp.UnixToTime(this=seq_get(args, 0), scale=exp.UnixToTime.MILLIS),
        "GENERATE_SERIES": _build_generate_series(),
        "GET_CURRENT_TIME": exp.CurrentTime.from_arg_list,
        "GET_BIT": lambda args: exp.Getbit(
            this=se
…[2053 chars elided]…
n.this, expression.args.get("quantile"))

    def alterset_sql(self, expression: exp.AlterSet) -> str:
        exprs = self.expressions(expression, flat=True)
        exprs = f" {exprs}" if exprs else ""
        file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
        file_format = f" STAGE_FILE_FORMAT = ({file_format})" if file_format else ""
        copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
13:    def test_duckdb(self):
[assistant] Plan: (1) map DuckDB's `JSON_ARRAY` to `exp.JSONArray` in the DuckDB parser; (2) have the Snowflake generator emit `JSONArray` as an `exp.Array`, which Snowflake renders as `ARRAY_CONSTRUCT`. Before editing, I'll look at an existing `validate_all` test in the DuckDB test file.
[tool_use Bash] {"command": "grep -n \"write={\" -B4 -A4 tests/dialects/test_duckdb.py | sed -n 1,30p; grep -n \"\\\"snowflake\\\": \\\"ARRAY_CONSTRUCT\" tests/dialects/*.py | head -3", "description": "Look at existing validate_all test style"}
[tool_result] 68-            },
69-        )
70-        self.validate_all(
71-            "SELECT FIRST_VALUE(c IGNORE NULLS) OVER (PARTITION BY gb ORDER BY ob) FROM t",
72:            write={
73-                "duckdb": "SELECT FIRST_VALUE(c IGNORE NULLS) OVER (PARTITION BY gb ORDER BY ob) FROM t",
74-                "sqlite": UnsupportedError,
75-                "mysql": UnsupportedError,
76-                "postgres": UnsupportedError,
77-            },
78-        )
79-        self.validate_all(
80-      
…[679 chars elided]…
(x AS STRING)",
92-                "duckdb": "CAST(x AS UUID)",
93-            },
94-        )
95-
96-        self.validate_all(
97-            "SELECT APPROX_TOP_K(category, 3) FROM t",
tests/dialects/test_duckdb.py:718:                "snowflake": "ARRAY_CONSTRUCT_COMPACT(1, 2, 3, 4, 5)",
tests/dialects/test_duckdb.py:725:                "snowflake": "ARRAY_CONSTRUCT_COMPACT()",
tests/dialects/test_duckdb.py:732:                "snowflake": "ARRAY_CONSTRUCT_COMPACT('a', NULL, 'b', NULL, 'c')",
[assistant] Now I'll make the edits: the DuckDB parser entry, the Snowflake generator method, and a test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\"", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "    @unsupported_args(\"weight\", \"accuracy\")\n    def approxquantile_sql(", "new_string": "    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.sql(exp.Array(expressions=expression.expressions))\n\n    @unsupported_args(\"weight\", \"accuracy\")\n    def approxquantile_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"CAST(x AS UUID)\",", "new_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS UUID)\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns=\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\"\nprint(sqlglot.transpile(s, read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(s, read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY()', read='duckdb', write='snowflake'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_bigquery.py tests/dialects/test_oracle.py tests/dialects/test_singlestore.py 2>&1 | tail -15", "description": "Verify transpile output and run dialect tests"}
[tool_result] ["SELECT ['a', 'b', 'c']"]
["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT []']
........................................................................................................................................................................................................................ [ 87%]
...............................         [100%]
=================================== FAILURES ===================================
____ TestDuckDB.test_duckdb [SELECT JSON_ARRAY('a', 'b', 'c') -> snowflake] ____
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "SELECT ['a', 'b', 'c']" != "SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"
E   - SELECT ['a', 'b', 'c']
E   + SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
=========================== short test summary info ============================
SUBFAILED[SELECT JSON_ARRAY('a', 'b', 'c') -> snowflake] tests/dialects/test_duckdb.py::TestDuckDB::test_duckdb
1 failed, 247 passed, 3632 subtests passed in 1.13s
[assistant] Snowflake renders `exp.Array` with bracket notation here, not `ARRAY_CONSTRUCT`. The task names `ARRAY_CONSTRUCT` as the target, so I'll emit that function directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        return self.sql(exp.Array(expressions=expression.expressions))", "new_string": "        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155739-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY()', read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, NULL)', read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, NULL)', read='duckdb', write='mysql'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Recheck transpile output and run full test suite"}
[tool_result] ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()']
['SELECT ARRAY_CONSTRUCT(1, NULL)']
['SELECT JSON_ARRAY(1, NULL)']
.................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1084 passed, 17838 subtests passed in 50.00s
[assistant] The full suite passes (1084 tests). I'll run the linter and formatter on the changed files, since the project's CI uses them.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff --version && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py) 2>&1 | tail -8; git status --short; git diff --stat", "description": "Lint, format-check, and show changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generators/snowflake.py | 4 ++++
 sqlglot/parsers/duckdb.py       | 1 +
 tests/dialects/test_duckdb.py   | 7 +++++++
 3 files changed, 12 insertions(+)
[assistant] DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full test suite passes (1084 tests), and ruff check and format are clean on the changed files. I haven't committed anything.

The change has three parts:

- **`sqlglot/parsers/duckdb.py`**: DuckDB's `JSON_ARRAY` now parses to `exp.JSONArray` instead of an opaque `Anonymous` function. Same-dialect output is unchanged (`JSON_ARRAY('a', 'b', 'c')`).
- **`sqlglot/generators/snowflake.py`**: a new 
…[34 chars elided]…
RUCT(...)`. It is decorated with `@unsupported_args("null_handling", "return_type", "strict")`, since Snowflake has no equivalent for those options. Those are only set by Oracle-style syntax, so this doesn't affect DuckDB input.
- **`tests/dialects/test_duckdb.py`**: a `validate_all` case covering the DuckDB-to-Snowflake mapping and the DuckDB round trip.

One decision to review: my first attempt used `exp.Array`, but Snowflake rendered it as bracket syntax (`['a', 'b', 'c']`) rather than `ARRAY_CONSTRUCT`. I switched to calling `ARRAY_CONSTRUCT` directly, which matches the function you named.
