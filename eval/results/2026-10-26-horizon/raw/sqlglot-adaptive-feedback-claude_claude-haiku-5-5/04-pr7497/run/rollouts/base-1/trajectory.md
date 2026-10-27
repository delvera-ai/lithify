# trajectory base-1

final message:
`JSON_ARRAY(...)` from DuckDB now transpiles to valid Snowflake, and the full test suite passes (1085 tests).

**Fix**
- **DuckDB parser** (`sqlglot/parsers/duckdb.py`): `JSON_ARRAY` used to parse into a generic `Anonymous` node. It now parses into `exp.JSONArray`, the existing canonical class that the other dialects already use.
- **Snowflake generator** (`sqlglot/generators/snowflake.py`): added `jsonarray_sql`, which emits the same array form that `exp.Array` already produces in Snowflake. It rejects the `null_handling`, `return_type` and `strict` arguments, which DuckDB never sets.
- **Test** (`tests/dialects/test_duckdb.py`): `test_json_array` asserts the parsed node is `exp.JSONArray`, then checks the DuckDB, MySQL and Snowflake output.

**Output**
- `SELECT JSON_ARRAY('a', 'b', 'c')` → Snowflake: `SELECT ['a', 'b', 'c']`
- The empty form (`JSON_ARRAY()`) → `SELECT []`, and nested arrays also work.
- DuckDB, MySQL, Postgres and BigQuery output is unchanged.

**Choice to confirm:** the issue says Snowflake's equivalent is `ARRAY_CONSTRUCT`. I emitted the bracket form instead because sqlglot already writes every Snowflake array that way (`SELECT ARRAY(1, 2)` → `SELECT [1, 2]`), and that form is valid Snowflake. If you want the literal `ARRAY_CONSTRUCT(...)` spelling, it's a one-line change in `jsonarray_sql`, but it would then differ from how plain arrays are written.

## events
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/.claude/skills/sqlglot-dialect-functions

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

[tool_use Bash] {"command": "grep -rn -i \"json_array\\|JSONArray\\b\" sqlglot/ | grep -v \"\\.pyc\" | head -60", "description": "Search codebase for JSON_ARRAY references"}
[tool_result] sqlglot/generator.py:3565:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/generator.py:3584:            "JSON_ARRAYAGG",
sqlglot/parsers/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers
…[1975 chars elided]…

sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/expressions/json.py:34:    _sql_names = ["JSON_ARRAY_APPEND"]
sqlglot/expressions/json.py:39:    _sql_names = ["JSON_ARRAY_CONTAINS"]
sqlglot/expressions/json.py:45:    _sql_names = ["JSON_ARRAY_INSERT"]
sqlglot/generators/postgres.py:446:                    self.unsupported("Unsupported JSON_ARRAY_ELEMENTS with offset")
sqlglot/generators/postgres.py:448:                return f"JSON_ARRAY_ELEMENTS({arg_as_json}){alias}"
[tool_use Bash] {"command": "ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/ 2>&1; PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(e.selects[0]))\nprint(e.sql('snowflake'))\nprint(e.sql('duckdb'))\n\"", "description": "Check python env and reproduce DuckDB JSON_ARRAY transpile"}
[tool_result] ast_check.py
lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
SELECT JSON_ARRAY('a', 'b', 'c')
SELECT JSON_ARRAY('a', 'b', 'c')
[assistant] DuckDB's `JSON_ARRAY` currently parses into a generic `Anonymous` node. `exp.JSONArray` already exists, so I'll check its definition, the base generator, and the Snowflake and DuckDB wiring.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/expressions/json.py; echo ----; sed -n 3560,3580p sqlglot/generator.py; echo ----; grep -n \"ARRAY_CONSTRUCT\\|JSONArray\\|JSON_ARRAY\" sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/dialects/snowflake.py sqlglot/dialects/duckdb.py; echo ----; grep -rn \"JSON_ARRAY(\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head; sed -n 270,290p sqlglot/parsers/bigquery.py", "description": "Inspect JSONArray class, generator, and dialect wiring"}
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
        
…[1948 chars elided]…
slate(),
        "FEATURES_AT_TIME": lambda self: self._parse_features_at_time(),
        "GENERATE_EMBEDDING": lambda self: self._parse_ml(exp.GenerateEmbedding),
        "GENERATE_TEXT_EMBEDDING": lambda self: self._parse_ml(exp.GenerateEmbedding, is_text=True),
        "GENERATE_TEXT": lambda self: self._parse_generate(exp.GenerateText),
        "GENERATE_TABLE": lambda self: self._parse_generate(exp.GenerateTable),
        "GENERATE_BOOL": lambda self: self._parse_generate(exp.GenerateBool),
[assistant] The canonical class `exp.JSONArray` exists and the base generator already emits it. So the fix is: DuckDB parses `JSON_ARRAY` into `exp.JSONArray`, and Snowflake generates `ARRAY_CONSTRUCT` for it. Next I'll check how the existing code is structured in those files.
[tool_use Bash] {"command": "grep -n \"FUNCTIONS = {\" -A3 sqlglot/parsers/duckdb.py | head -20; grep -n \"\\\"JSON\" sqlglot/parsers/duckdb.py | head; echo ----; grep -n \"unsupported_args\\|^from\\|^import\" sqlglot/generators/snowflake.py | head -20; grep -n \"def .*_sql(self\" sqlglot/generators/snowflake.py | head -60; grep -n \"exp.Array:\" -A3 sqlglot/generators/snowflake.py; grep -n \"def array_sql\" -A10 sqlglot/generators/snowflake.py; echo ----; grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/*.py | head -30", "description": "Inspect DuckDB parser and Snowflake generator conventions"}
[tool_result] 72:    NO_PAREN_FUNCTIONS = {
73-        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: exp.Localtime,
75-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
--
102:    FUNCTIONS = {
103-        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
104-        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
105-        "ARRAY_PREPEND": _build_array_prepend,
132:        "JSON": exp.ParseJSON.from_arg_list,
1
…[7576 chars elided]…
SON)) AS x(tbox)
tests/dialects/test_postgres.py:1537:CROSS JOIN JSON_ARRAY_ELEMENTS(CAST(JSON_EXTRACT_PATH(tbox, 'boxes') AS JSON)) AS y(boxes)"""
tests/dialects/test_oracle.py:78:            "SELECT JSON_ARRAYAGG(JSON_OBJECT('RNK': RNK, 'RATING_CODE': RATING_CODE, 'DATE_VALUE': DATE_VALUE, 'AGENT_ID': AGENT_ID RETURNING CLOB) RETURNING CLOB) AS JSON_DATA FROM tablename"
tests/dialects/test_oracle.py:81:            "SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
[assistant] Snowflake already routes `exp.Array` to `ARRAY_CONSTRUCT`, so the Snowflake side can reuse it. I'll check the `exp.array` helper and the end of `array_sql`, then make the edits.
[tool_use Bash] {"command": "grep -n \"^def array(\" -A12 sqlglot/expressions/*.py | head -20; sed -n 1051,1075p sqlglot/generators/snowflake.py; sed -n 924,930p sqlglot/generators/snowflake.py", "description": "Check exp.array helper and Snowflake array_sql"}
[tool_result] sqlglot/expressions/builders.py:1014:def array(
sqlglot/expressions/builders.py-1015-    *expressions: ExpOrStr,
sqlglot/expressions/builders.py-1016-    copy: bool = True,
sqlglot/expressions/builders.py-1017-    dialect: DialectType = None,
sqlglot/expressions/builders.py-1018-    **kwargs: Unpack[ParserNoDialectArgs],
sqlglot/expressions/builders.py-1019-) -> Array:
sqlglot/expressions/builders.py-1020-    """
sqlglot/expressions/builders.py-1021-    Returns an array.
sqlglot/expressions/buil
…[1274 chars elided]…
self.sql(first_expr.subquery())

        return inline_array_sql(self, expression)

    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
        return self.func("OBJECT_CONSTRUCT", *flatten(zip(keys, values)))

    @unsupported_args("weight", "accuracy")
    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:
        return self.func("APPROX_PERCENTILE", expression.this, expression.args.get("quantile"))

    def alterset_sql(self, expression: exp.AlterSet) -> str:
[assistant] Both halves are clear. I'll make the two edits: a `JSON_ARRAY` builder in the DuckDB parser, and a `jsonarray_sql` method in the Snowflake generator that reuses the existing `Array` path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "offset": 1072, "limit": 5}
[tool_result] 1072	
1073	        return inline_array_sql(self, expression)
1074	
1075	    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
1076	        zone = self.sql(expression, "this")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        return inline_array_sql(self, expression)\n\n    def currentdate_sql(self, expression: exp.CurrentDate) -> str:", "new_string": "        return inline_array_sql(self, expression)\n\n    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.sql(exp.array(*expression.expressions))\n\n    def currentdate_sql(self, expression: exp.CurrentDate) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll verify the AST node and the output across dialects, including zero-arg and nested forms.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor sql in [\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", 'SELECT JSON_ARRAY()', \\\"SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))\\\"]:\n    e = sqlglot.parse_one(sql, read='duckdb')\n    print(type(e.selects[0]).__name__, sql)\n    for d in ['duckdb','snowflake','mysql','postgres','bigquery']:\n        print('  ', d, '->', e.sql(d))\n\"", "description": "Verify JSONArray node and cross-dialect output"}
[tool_result] JSONArray SELECT JSON_ARRAY('a', 'b', 'c')
   duckdb -> SELECT JSON_ARRAY('a', 'b', 'c')
   snowflake -> SELECT ['a', 'b', 'c']
   mysql -> SELECT JSON_ARRAY('a', 'b', 'c')
   postgres -> SELECT JSON_ARRAY('a', 'b', 'c')
   bigquery -> SELECT JSON_ARRAY('a', 'b', 'c')
JSONArray SELECT JSON_ARRAY()
   duckdb -> SELECT JSON_ARRAY()
   snowflake -> SELECT []
   mysql -> SELECT JSON_ARRAY()
   postgres -> SELECT JSON_ARRAY()
   bigquery -> SELECT JSON_ARRAY()
JSONArray SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))
   duckdb -> SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))
   snowflake -> SELECT [1, [2, 3]]
   mysql -> SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))
   postgres -> SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))
   bigquery -> SELECT JSON_ARRAY(1, JSON_ARRAY(2, 3))
[assistant] The DuckDB node is now `JSONArray`, but Snowflake emits bracket syntax `['a', 'b', 'c']`, not `ARRAY_CONSTRUCT` as the issue expects. I'll check what plain arrays produce in Snowflake today to see whether this is the existing convention.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT ARRAY(1, 2)', read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_CONSTRUCT(1, 2)', read='snowflake', write='snowflake'))\n\"; grep -n \"ARRAY_CONSTRUCT\" tests/dialects/test_snowflake.py | head -5; grep -n \"def inline_array_sql\" -A8 sqlglot/dialects/dialect.py", "description": "Compare existing Snowflake array output conventions"}
[tool_result] ['SELECT [1, 2]']
['SELECT [1, 2]']
115:            "SELECT BITMAP_COUNT(BITMAP_CONSTRUCT_AGG(value)) FROM TABLE(FLATTEN(INPUT => ARRAY_CONSTRUCT(1, 2, 3, 5)))",
1234:            "ARRAY_CONSTRUCT_COMPACT(1, null, 2)",
1237:                "snowflake": "ARRAY_CONSTRUCT_COMPACT(1, NULL, 2)",
2169:            """SELECT ARRAY_CONSTRUCT('foo')::VARIANT[0]""",
4061:            "ARRAY_CONSTRUCT(0, 1, 2)",
1205:def inline_array_sql(self: Generator, expression: exp.Expr) -> str:
1206-    return f"[{self.expressions(expression, dynamic=True, new_line=True, skip_first=True, skip_last=True)}]"
1207-
1208-
1209-def inline_array_unless_query(self: Generator, expression: exp.Expr) -> str:
1210-    elem = seq_get(expression.expressions, 0)
1211-    if isinstance(elem, exp.Expr) and elem.find(exp.Query):
1212-        return self.func("ARRAY", elem)
1213-    return inline_array_sql(self, expression)
[assistant] Snowflake's existing convention for arrays is bracket syntax (`SELECT ARRAY(1, 2)` → `SELECT [1, 2]`), so `JSON_ARRAY` now matches how sqlglot already emits arrays there. That is valid Snowflake. Next I'll add a test next to the existing DuckDB JSON tests.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|def test_json\" tests/dialects/test_duckdb.py | head -30", "description": "Locate JSON tests in DuckDB test file"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_duckdb.py | head -20; grep -n \"JSON\" tests/dialects/test_duckdb.py | head -20", "description": "List DuckDB test methods and JSON references"}
[tool_result] 13:    def test_duckdb(self):
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
2202:    
…[1577 chars elided]…
ll}'), 'a'))""",
549:            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
553:            "SELECT col FROM t WHERE JSON_EXTRACT_STRING(col, '$.id') NOT IN ('b')",
561:            "SELECT JSON_EXTRACT_STRING(c, '$.k1') = 'v1'",
565:            "SELECT JSON_EXTRACT(c, '$.k1') = 'v1'",
569:            "SELECT JSON_EXTRACT(c, '$[*].id')[0:2]",
573:            "SELECT JSON_EXTRACT_STRING(c, '$[*].id')[0:2]",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "offset": 1948, "limit": 7}
[tool_result] 1948	        )
1949	
1950	    def test_array(self):
1951	        self.validate_identity("ARRAY(SELECT id FROM t)")
1952	        self.validate_identity("ARRAY((SELECT id FROM t))")
1953	
1954	    def test_cast(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_cast(self):", "new_string": "        self.validate_identity(\"ARRAY((SELECT id FROM t))\")\n\n    def test_json_array(self):\n    
…[84 chars elided]…
f.assertIsInstance(expr.selects[0], exp.JSONArray)\n        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"mysql\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ['a', 'b', 'c']\",\n            },\n        )\n\n    def test_cast(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160035-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the DuckDB test file, then the full project test command from the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k json_array 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run DuckDB json_array test then full test suite", "timeout": 900000}
[tool_result] .                                                                     [100%]
1 passed, 44 deselected, 3 subtests passed in 0.11s
................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
...................................................................
…[392 chars elided]…
............................................................ [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1085 passed, 17839 subtests passed in 81.22s (0:01:21)
[assistant] The full suite passes (1085 tests). I'll run the linter and formatter on the changed files, since the project's `make check` includes style.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; FILES=\"sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py\"; $PY -m ruff check $FILES 2>&1 | tail -3; $PY -m ruff format --check $FILES 2>&1 | tail -3; git status --short; git diff --stat", "description": "Lint, format-check, and show diff stats"}
[tool_result] --> sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
error: Failed to format sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generators/snowflake.py |  4 ++++
 sqlglot/parsers/duckdb.py       |  1 +
 tests/dialects/test_duckdb.py   | 12 ++++++++++++
 3 files changed, 17 insertions(+)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff --version; $PY -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | head -20; grep -n \"^style\" -A3 Makefile", "description": "Get full ruff output and Makefile style target"}
[tool_result] ruff 0.15.6
All checks passed!
80:style:
81-	pre-commit run --all-files
82-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
83-
[assistant] Lint passes. The earlier error came from the combined `ruff format` call, so I'll re-run the format check one file at a time.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for f in sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py; do $PY -m ruff format --check \"$f\"; done", "description": "Format-check each changed file individually"}
[tool_result] 1 file already formatted
1 file already formatted
1 file already formatted
[assistant] `JSON_ARRAY(...)` from DuckDB now transpiles to valid Snowflake, and the full test suite passes (1085 tests).

**Fix**
- **DuckDB parser** (`sqlglot/parsers/duckdb.py`): `JSON_ARRAY` used to parse into a generic `Anonymous` node. It now parses into `exp.JSONArray`, the existing canonical class that the other dialects already use.
- **Snowflake generator** (`sqlglot/generators/snowflake.py`): added `jsonarray_sql`, which emits the same array form that `exp.Array` already produces in Snowflake. It rejects the `null_handling`, `return_type` and `strict` arguments, which DuckDB never sets.
- **Tes
…[194 chars elided]…
, 'c')` → Snowflake: `SELECT ['a', 'b', 'c']`
- The empty form (`JSON_ARRAY()`) → `SELECT []`, and nested arrays also work.
- DuckDB, MySQL, Postgres and BigQuery output is unchanged.

**Choice to confirm:** the issue says Snowflake's equivalent is `ARRAY_CONSTRUCT`. I emitted the bracket form instead because sqlglot already writes every Snowflake array that way (`SELECT ARRAY(1, 2)` → `SELECT [1, 2]`), and that form is valid Snowflake. If you want the literal `ARRAY_CONSTRUCT(...)` spelling, it's a one-line change in `jsonarray_sql`, but it would then differ from how plain arrays are written.
