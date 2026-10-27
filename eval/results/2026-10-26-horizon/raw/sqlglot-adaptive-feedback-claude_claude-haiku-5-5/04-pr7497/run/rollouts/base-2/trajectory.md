# trajectory base-2

final message:
DuckDB `JSON_ARRAY(...)` now parses to `exp.JSONArray` and transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`. The full test suite passes (1085 tests), and ruff check and format are clean on the changed files.

Before the fix, `JSON_ARRAY` parsed to a generic `exp.Anonymous`, so it was copied through unchanged. The cause is that `exp.JSONArray`'s auto-derived SQL name is `J_S_O_N_ARRAY`, so no parser ever registered `JSON_ARRAY`.

Changes:
- **`sqlglot/parsers/duckdb.py`**: `"JSON_ARRAY": lambda args: exp.JSONArray(expressions=args)`. I kept this dialect-scoped rather than fixing the class name globally, because that would change parsing for every dialect.
- **`sqlglot/generators/snowflake.py`**: `exp.JSONArray` maps to `rename_func("ARRAY_CONSTRUCT")`, wrapped in `unsupported_args("null_handling", "return_type", "strict")`, which matches the singlestore precedent. Those three options have no Snowflake equivalent, so they warn rather than being dropped silently.
- **`tests/dialects/test_duckdb.py`**: new `test_json_array` asserts the parsed node is `exp.JSONArray`, checks the DuckDB identity round-trip, and checks the Snowflake and MySQL outputs.

Verified output:
- `SELECT JSON_ARRAY('a', 'b', 'c')` → Snowflake: `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`
- `SELECT JSON_ARRAY()` → Snowflake: `SELECT ARRAY_CONSTRUCT()`
- MySQL and BigQuery output keeps `JSON_ARRAY(...)`.

I haven't changed the behaviour of `JSON_ARRAY` in MySQL or other dialects, which still parse it as `Anonymous`. Making it a typed node everywhere would mean fixing the class's SQL name, which is a broader change.

## events
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot/
…[4286 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\b\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -60", "description": "Search for JSON_ARRAY references in sqlglot and tests"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers
…[5295 chars elided]…
e AS JSON)) AS x(tbox)
tests/dialects/test_postgres.py:1537:CROSS JOIN JSON_ARRAY_ELEMENTS(CAST(JSON_EXTRACT_PATH(tbox, 'boxes') AS JSON)) AS y(boxes)"""
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/singlestore.py:836:        "json_array_contains_double",
sqlglot/generators/singlestore.py:837:        "json_array_contains_json",
sqlglot/generators/singlestore.py:838:        "json_array_contains_string",
[tool_use Bash] {"command": "ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/ 2>&1; ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"import sqlglot,sys;print(sqlglot.__file__)\" 2>&1; sed -n 1,30p sqlglot/expressions/json.py", "description": "Check helper script, python env, and JSONArray class"}
[tool_result] ast_check.py
<work>/env-sqlglot/bin/python
~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/sqlglot/__init__.py
"""sqlglot expressions - JSON functions."""

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
        "order": False,
        "null_handling": False,
        "return_type": False,
        "strict": False,
    }
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read duckdb --write duckdb,snowflake,mysql,postgres --repr \"SELECT JSON_ARRAY('a', 'b', 'c')\"; echo \"exit=$?\"; $P -c \"\nimport sqlglot\nfor d in ['duckdb']:\n    e = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read=d)\n    print(repr(e.selects[0]))\n    print(e.sql('snowflake'))\n\" ; $P -c \"import sqlglot;print(sqlglot.__version__)\"", "description": "Reproduce DuckDB JSON_ARRAY parse and transpile"}
[tool_result] == SELECT JSON_ARRAY('a', 'b', 'c')
  node: Anonymous  <-- GENERIC node: is there a typed exp class for this function?
  Anonymous(
    this=JSON_ARRAY,
    expressions=[
      Literal(this='a', is_string=True),
      Literal(this='b', is_string=True),
      Literal(this='c', is_string=True)])
  duckdb (round-trip): SELECT JSON_ARRAY('a', 'b', 'c')
  duckdb: SELECT JSON_ARRAY('a', 'b', 'c')
  snowflake: SELECT JSON_ARRAY('a', 'b', 'c')
  mysql: SELECT JSON_ARRAY('a', 'b', 'c')
  postgres: SELECT JSON_ARRAY('a', 'b', 'c')
exit=0
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
SELECT JSON_ARRAY('a', 'b', 'c')
0.0.0+eval
[assistant] Confirmed: DuckDB `JSON_ARRAY` parses to a generic `Anonymous`, so it falls through unchanged. Next I'll look at the generic `JSONArray` generator and how Snowflake and DuckDB handle arrays today.
[tool_use Bash] {"command": "sed -n 3560,3580p sqlglot/generator.py; echo ----; grep -n \"ArrayConstruct\\|exp.Array\\b\\|exp.Array:\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py | head; echo ----; grep -n \"JSONArray\\|exp.JSON\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head -30; echo ----; grep -n \"ARRAY_CONSTRUCT\\|\\\"ARRAY\\\"\" sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py | head", "description": "Inspect generic JSONArray generator and dialect hooks"}
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
…[2325 chars elided]…
NPathKey,
sqlglot/generators/duckdb.py:1719:        exp.JSONPathRoot,
sqlglot/generators/duckdb.py:1720:        exp.JSONPathSubscript,
sqlglot/generators/duckdb.py:1721:        exp.JSONPathWildcard,
sqlglot/generators/duckdb.py:4364:    def jsonextractscalar_sql(self, expression: exp.JSONExtractScalar) -> str:
sqlglot/generators/duckdb.py:4366:            expression = exp.JSONExtractScalar(
----
sqlglot/parsers/snowflake.py:407:        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
[assistant] The fix needs three pieces: a DuckDB parser mapping to `exp.JSONArray`, a Snowflake generator emitting `ARRAY_CONSTRUCT`, and tests. Before editing, I'll check why the base parser doesn't already map `JSON_ARRAY` to `JSONArray`, and look at the singlestore precedent.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nfrom sqlglot.parser import Parser\nfrom sqlglot import exp\nprint('base has JSON_ARRAY:', 'JSON_ARRAY' in Parser.FUNCTIONS, Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint(exp.JSONArray.sql_names())\n\"; sed -n 160,170p sqlglot
…[44 chars elided]…
supported_args\" -A3 sqlglot/dialects/dialect.py sqlglot/*.py | head; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py | head -30; grep -n \"rename_func\\|unsupported_args\" sqlglot/generators/snowflake.py | head -5; sed -n 400,412p sqlglot/parsers/snowflake.py; grep -n \"FUNCTIONS: dict\" -A3 sqlglot/parsers/duckdb.py", "description": "Check base JSON_ARRAY mapping and helper imports"}
[tool_result] base has JSON_ARRAY: False None
['J_S_O_N_ARRAY']
        exp.JSONPathRoot: lambda *_: "",
        exp.JSONFormat: unsupported_args("options", "is_json")(rename_func("JSON_PRETTY")),
        exp.JSONArrayAgg: unsupported_args("null_handling", "return_type", "strict")(
            lambda self, e: self.func("JSON_AGG", e.this, suffix=f"{self.sql(e, 'order')})")
        ),
        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
            rename_func("JSON_BUILD_ARRAY")

…[1112 chars elided]…

            preserve_end_of_month=True,
        ),
        "APPROX_PERCENTILE": exp.ApproxQuantile.from_arg_list,
        "CURRENT_TIME": lambda args: exp.Localtime(this=seq_get(args, 0)),
        "APPROX_TOP_K": _build_approx_top_k,
        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
        "ARRAY_CONTAINS": lambda args: exp.ArrayContains(
            this=seq_get(args, 1),
            expression=seq_get(args, 0),
            ensure_variant=False,
            check_null=True,
[assistant] Root cause found: `exp.JSONArray` auto-derives its SQL name as `J_S_O_N_ARRAY`, so the base parser never registers `JSON_ARRAY` and it falls back to `Anonymous`. I'll keep the fix dialect-scoped: map it in the DuckDB parser, and emit `ARRAY_CONSTRUCT` from Snowflake. Let me look at the DuckDB parser `FUNCTIONS` block and the Snowflake generator `TRANSFORMS`.
[tool_use Bash] {"command": "sed -n 120,140p sqlglot/parsers/duckdb.py; echo ----; sed -n 405,418p sqlglot/generators/snowflake.py; echo ----; grep -n \"^from\\|^    rename_func\\|^    unsupported\" sqlglot/parsers/duckdb.py | head; grep -n \"JSON_ARRAY\\|json_array\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head", "description": "View DuckDB parser FUNCTIONS and Snowflake TRANSFORMS"}
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
…[1151 chars elided]…
rray_append_sql("ARRAY_APPEND"),
        exp.ArrayPrepend: array_append_sql("ARRAY_PREPEND"),
        exp.ArrayContains: lambda self, e: self.func(
            "ARRAY_CONTAINS",
----
1:from __future__ import annotations
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
[assistant] Now the edits: map `JSON_ARRAY` to `exp.JSONArray` in the DuckDB parser, and add a Snowflake `TRANSFORMS` entry that emits `ARRAY_CONSTRUCT`, following the singlestore `unsupported_args` pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON_EXTRACT_STRING\": parser.build_extract_json_with_path(exp.JSONExtractScalar),\n", "new_string": "        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_STRING\": parser.build_extract_json_with_path(exp.JSONExtractScalar),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"exp.JSON\\|exp.Lateral\" sqlglot/generators/snowflake.py | head; grep -n \"class TestSnowflake\\|def test_\" tests/dialects/test_snowflake.py | head -5; grep -n \"def test_\" tests/dialects/test_duckdb.py | head -3", "description": "Find Snowflake TRANSFORMS anchor and test file layout"}
[tool_result] 168:            lateral = exp.Lateral(this=unnest_parent.this.pop())
230:    self: SnowflakeGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
232:    json_extract = exp.JSONExtract(this=expression.this, expression=expression.expression)
235:    if isinstance(expression, exp.JSONValueArray):
500:        exp.JSONExtractArray: _json_extract_value_array_sql,
501:        exp.JSONExtractScalar: lambda self, e: self.func(
504:        exp.JSONKeys: rename_func("OBJECT_KEYS"),
505:        exp.JSONObject: lambda self, e: self.func("OBJECT_CONSTRUCT_KEEP_NULL", *e.expressions),
506:        exp.JSONPathRoot: lambda *_: "",
507:        exp.JSONValueArray: _json_extract_value_array_sql,
11:class TestSnowflake(Validator):
15:    def test_snowflake(self):
3357:    def test_null_treatment(self):
3398:    def test_staged_files(self):
3446:    def test_sample(self):
13:    def test_duckdb(self):
1561:    def test_array_index(self):
1601:    def test_array_insert(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/sqlglot/generators/snowflake.py", "old_string": "        exp.JSONKeys: rename_func(\"OBJECT_KEYS\"),\n", "new_string": "        exp.JSONArray: unsupported_args(\"null_handling\", \"return_type\", \"strict\")(\n            rename_func(\"ARRAY_CONSTRUCT\")\n        ),\n        exp.JSONKeys: rename_func(\"OBJECT_KEYS\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll verify the AST node and the transpiled output before writing the test.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read duckdb --write duckdb,snowflake,mysql,postgres,bigquery --repr \"SELECT JSON_ARRAY('a', 'b', 'c')\"; $P -c \"\nimport sqlglot\nprint(sqlglot.transpile(
…[218 chars elided]…
LL)\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT ARRAY_CONSTRUCT(1, 2)\\\", read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='duckdb', write='bigquery'))\n\"", "description": "Verify AST node and Snowflake transpile output"}
[tool_result] == SELECT JSON_ARRAY('a', 'b', 'c')
  node: JSONArray
  JSONArray(
    expressions=[
      Literal(this='a', is_string=True),
      Literal(this='b', is_string=True),
      Literal(this='c', is_string=True)])
  duckdb (round-trip): SELECT JSON_ARRAY('a', 'b', 'c')
  duckdb: SELECT JSON_ARRAY('a', 'b', 'c')
  snowflake: SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
  mysql: SELECT JSON_ARRAY('a', 'b', 'c')
  postgres: SELECT JSON_ARRAY('a', 'b', 'c')
  bigquery: SELECT JSON_ARRAY('a', 'b', 'c')
["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()']
['SELECT ARRAY_CONSTRUCT(1, NULL)']
['SELECT [1, 2]']
['SELECT ARRAY_CONSTRUCT(1, 2)']
['SELECT JSON_ARRAY(1, 2)']
[assistant] The AST is now `JSONArray`, and Snowflake emits `ARRAY_CONSTRUCT`. Next I'll add a test next to the existing DuckDB JSON tests, asserting the node class as the skill requires.
[tool_use Bash] {"command": "grep -n \"def test_.*json\" tests/dialects/test_duckdb.py; grep -n \"JSON_EXTRACT_STRING\\|JSON_EXTRACT_PATH\" tests/dialects/test_duckdb.py | head -3", "description": "Locate existing DuckDB JSON tests"}
[tool_result] 549:            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
553:            "SELECT col FROM t WHERE JSON_EXTRACT_STRING(col, '$.id') NOT IN ('b')",
561:            "SELECT JSON_EXTRACT_STRING(c, '$.k1') = 'v1'",
[tool_use Bash] {"command": "sed -n 540,575p tests/dialects/test_duckdb.py; grep -n \"^from\\|^import\" tests/dialects/test_duckdb.py", "description": "View surrounding DuckDB JSON test code"}
[tool_result]         self.validate_identity(
            "SELECT $🦆$foo$🦆$",
            "SELECT 'foo'",
        )
        self.validate_identity(
            "SELECT * FROM t PIVOT(FIRST(t) AS t, FOR quarter IN ('Q1', 'Q2'))",
            "SELECT * FROM t PIVOT(FIRST(t) AS t FOR quarter IN ('Q1', 'Q2'))",
        )
        self.validate_identity(
            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
            """S
…[885 chars elided]…
 -> '$[*].id')[0:2]",
        )
        self.validate_identity(
            "SELECT JSON_EXTRACT_STRING(c, '$[*].id')[0:2]",
            "SELECT (c ->> '$[*].id')[0:2]",
        )
1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
[assistant] I'll add a focused `test_json_array` method before `test_array_index`, covering the node class, identity round-trip, and cross-dialect output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/tests/dialects/test_duckdb.py", "old_string": "    def test_array_index(self):", "new_string": "    def test_json_array(self):\n        self.assertIsInstance(\n            self.validate_identity(\"SELECT JSON_ARRAY('a', 'b', 'c')\").selects[0], exp.JSONArray\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n                \"mysql\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            },\n        )\n\n    def test_array_index(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-2/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll run the DuckDB tests, then the full suite with the project's command.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Run DuckDB and Snowflake dialect tests"}
[tool_result] ........................... [ 19%]
.................................................................................................................            [100%]
140 passed, 2153 subtests passed in 1.11s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
.............................................................................................................................................................. [ 38%]
......... [ 39%]
.............
…[263 chars elided]…
............................................................ [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1085 passed, 17839 subtests passed in 76.19s (0:01:16)
[assistant] The full suite passes (1085 tests). I'll run the project's linter and formatter on the changed files as well.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff --version || python3 -m ruff --version) 2>&1; F=\"sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py\"; ($P/ruff check $F && $P/ruff format --check $F) 2>&1 | tail -5; git status --short; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
E902 No such file or directory (os error 2)
--> sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generators/snowflake.py |  3 +++
 sqlglot/parsers/duckdb.py       |  1 +
 tests/dialects/test_duckdb.py   | 13 +++++++++++++
 3 files changed, 17 insertions(+)
[assistant] My lint call passed the file list as one quoted string, so ruff looked for a file that doesn't exist. I'll rerun it with separate arguments.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && $P/ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py", "description": "Run ruff check and format check on changed files"}
[tool_result] All checks passed!
3 files already formatted
[assistant] DuckDB `JSON_ARRAY(...)` now parses to `exp.JSONArray` and transpiles to Snowflake as `ARRAY_CONSTRUCT(...)`. The full test suite passes (1085 tests), and ruff check and format are clean on the changed files.

Before the fix, `JSON_ARRAY` parsed to a generic `exp.Anonymous`, so it was copied through unchanged. The cause is that `exp.JSONArray`'s auto-derived SQL name is `J_S_O_N_ARRAY`, so no parser ever registered `JSON_ARRAY`.

Changes:
- **`sqlglot/parsers/duckdb.py`**: `"JSON_ARRAY": lambda args: exp.JSONArray(expressions=args)`. I kept this dialect-scoped rather than fixing the class name
…[403 chars elided]…
ckdb.py`**: new `test_json_array` asserts the parsed node is `exp.JSONArray`, checks the DuckDB identity round-trip, and checks the Snowflake and MySQL outputs.

Verified output:
- `SELECT JSON_ARRAY('a', 'b', 'c')` → Snowflake: `SELECT ARRAY_CONSTRUCT('a', 'b', 'c')`
- `SELECT JSON_ARRAY()` → Snowflake: `SELECT ARRAY_CONSTRUCT()`
- MySQL and BigQuery output keeps `JSON_ARRAY(...)`.

I haven't changed the behaviour of `JSON_ARRAY` in MySQL or other dialects, which still parse it as `Anonymous`. Making it a typed node everywhere would mean fixing the class's SQL name, which is a broader change.
