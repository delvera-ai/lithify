# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of values. The full suite passes (1093 tests), including a new six-argument DuckDB case.

**Cause:** `JSONArray` in `sqlglot/expressions/json.py` wasn't marked variadic. The parser checks argument count against the number of declared keys (four), so DuckDB's `JSON_ARRAY(1, 2, 3, 4, 5, 6)` raised a ParseError.

**Fix:**
- Added `is_var_len_args = True` to `JSONArray`.
- Moved `expressions` to the last position in `arg_types`, since the variadic key must be last. Nothing depends on the key order, so this shouldn't change output.

**Existing dialects:** DuckDB, BigQuery, Oracle and SingleStore pass `expressions=` explicitly, so their parsing is unchanged. The six-argument call now round-trips through DuckDB, BigQuery, Oracle and Snowflake.

**Test:** Added a `validate_all` case in `tests/dialects/test_duckdb.py`, next to the existing `JSON_ARRAY` cases.

One caveat I left alone: calling `exp.JSONArray.from_arg_list` directly still maps positional args onto the optional keys (`null_handling`, etc.) rather than onto `expressions`. That was already wrong before this change, and no parser path uses it, so I didn't touch it. Say if you want it fixed too.

## events
[tool_use Bash] {"command": "grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot/ | head -50", "description": "Find JSONArray references in source"}
[tool_result] sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._parse_bitwise))
sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers
…[184 chars elided]…
xp.JSONArray,
sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/expressions/json.py && grep -n \"arg_types\\|class \\|_args\" sqlglot/expressions/json.py | head -80 && grep -rn \"JSON_ARRAY\\|JSONArray\" tests/ | head -30; grep -n \"JSON_ARRAY\\|JSONArray\" -n sqlglot/parsers/*.py sqlglot/dialects/*.py 2>/dev/null | head", "description": "Inspect JSONArray expression definition"}
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
        
…[6015 chars elided]…
n))
sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:57:        "JSON_ARRAYAGG": lambda self: self._parse_oracle_json_arrayagg(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers/oracle.py:114:            exp.JSONArray,
sqlglot/parsers/oracle.py:118:    def _parse_oracle_json_arrayagg(self) -> exp.JSONArrayAgg:
sqlglot/parsers/oracle.py:120:            exp.JSONArrayAgg,
[tool_use Bash] {"command": "grep -n \"def from_arg_list\" -A25 sqlglot/expressions/core.py; grep -n \"is_var_len_args\" sqlglot/*.py sqlglot/*/*.py | head -30; sed -n 3570,3585p sqlglot/generator.py; sed -n 108,125p sqlglot/parsers/oracle.py", "description": "Inspect arg-list builder and JSON array generator"}
[tool_result] 1633:    def from_arg_list(cls, args: Sequence[object]) -> Self:
1634-        if cls.is_var_len_args:
1635-            all_arg_keys = tuple(cls.arg_types)
1636-            # If this function supports variable length argument treat the last argument as such.
1637-            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
1638-            num_non_var = len(non_var_len_arg_keys)
1639-
1640-            args_dict = {arg_key: arg for arg, arg_key in zip(args, non_var
…[3349 chars elided]…
.JSONArray:
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

    def _parse_json_array(self, expr_type: type[E], **kwargs) -> E:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['JSON_ARRAY(1, 2, 3, 4, 5, 6)', 'JSON_ARRAY(1, 2)']:\n    e = sqlglot.parse_one(s)\n    print(repr(e))\n    print(e.sql())\ntry:\n    print(exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef']).sql())\nexcept Exception as x: print('ERR', type(x), x)\nprint(exp.JSONArray(expressions=[exp.column(c) for c in 'abcdef']).sql())\n\"; sed -n 1225,1240p sqlglot/expressions/core.py; sed -n 1940,1950p sqlglot/expressions/core.py", "description": "Reproduce JSON_ARRAY with six arguments"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False),
    Literal(this=3, is_string=False),
    Literal(this=4, is_string=False),
    Literal(this=5, is_string=False),
    Literal(this=6, is_string=False)])
JSON_ARRAY(1, 2, 3, 4, 5, 6)
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False)])
JSON_ARRAY(1, 2)
JSON_ARRAY(a, b, c, d, e, f)
JSON_ARRAY(a, b, c, d, e, f
…[395 chars elided]…
  errors.append(
                f"The number of provided arguments ({len(args)}) is greater than "
                f"the maximum number of supported arguments ({len(self.arg_types)})"
            )
    arg_types = {"this": True, "expressions": True, "params": True}


class Anonymous(Expression, Func):
    arg_types = {"this": True, "expressions": False}
    is_var_len_args = True

    @property
    def name(self) -> str:
        return self.this if isinstance(self.this, str) else self.this.name
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nargs=[exp.column(c) for c in 'abcdef']\nfor f in [lambda: exp.JSONArray.from_arg_list(args), lambda: exp.JSONArray(*args), lambda: exp.func('JSON_ARRAY', *args), lambda: exp.JSONArray.from_arg_list(args[:2]), lambda: exp.JSONArray.from_arg_list(args[:1])]:\n    try:\n        r=f(); print(repr(r)[:200]); print(r.sql())\n    except Exception as x: print('ERR', type(x).__name__, x)\n\" 2>&1; grep -n \"def func(\" -A30 sqlglot/expressions/*.py | grep -n \"validate\\|from_arg_list\\|Anonymous\" | head", "description": "Test JSONArray construction from argument lists"}
[tool_result] JSONArray(
  expressions=Column(
    this=Identifier(this=a, quoted=False)),
  null_handling=Column(
    this=Identifier(this=b, quoted=False)),
  return_type=Column(
    this=Identifier(this=c, quote
ERR TypeError 'Column' object is not iterable
ERR TypeError Expr.__init__() takes 1 positional argument but 7 were given
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Column(
      this=Identifier(this=a, quoted=False)),
    Column(
      this=Identifier(this=b, quoted=False)),
    Column(
      this=Identifier(this
JSON_ARRAY(a, b, c, d, e, f)
JSONArray(
  expressions=Column(
    this=Identifier(this=a, quoted=False)),
  null_handling=Column(
    this=Identifier(this=b, quoted=False)))
ERR TypeError 'Column' object is not iterable
JSONArray(
  expressions=Column(
    this=Identifier(this=a, quoted=False)))
ERR TypeError 'Column' object is not iterable
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.dialects.dialect import Dialect\nfor d in Dialect.classes:\n    try:\n        e = sqlglot.parse_one('JSON_ARRAY(1, 2, 3, 4, 5, 6)', read=d)\n        print(d or 'base', type(e).__name__, [a for a in e.args if e.args[a] is not None and a!='this'] , len(e.expressions) if hasattr(e,'expressions') else '')\n    except Exception as x: print(d, 'ERR', type(x).__name__, str(x)[:120])\n\" 2>&1 | head -50; grep -rn \"ALL_FUNCTIONS\" sqlglot/parser.py | head -5", "description": "Parse JSON_ARRAY across all dialects"}
[tool_result] base Anonymous ['expressions'] 6
hive Anonymous ['expressions'] 6
mysql Anonymous ['expressions'] 6
presto Anonymous ['expressions'] 6
trino Anonymous ['expressions'] 6
athena Anonymous ['expressions'] 6
bigquery JSONArray ['expressions'] 6
clickhouse Anonymous ['expressions'] 6
spark2 Anonymous ['expressions'] 6
spark Anonymous ['expressions'] 6
databricks Anonymous ['expressions'] 6
doris Anonymous ['expressions'] 6
dremio Anonymous ['expressions'] 6
drill Anonymous ['expressions'] 6
druid Ano
…[332 chars elided]…
ions'] 6
materialize Anonymous ['expressions'] 6
oracle JSONArray ['return_type', 'strict', 'expressions', 'join_mark'] 6
prql Anonymous ['expressions'] 6
redshift Anonymous ['expressions', 'join_mark'] 6
risingwave Anonymous ['expressions'] 6
singlestore Anonymous ['expressions'] 6
snowflake Anonymous ['expressions'] 6
solr Anonymous ['expressions'] 6
sqlite Anonymous ['expressions'] 6
starrocks Anonymous ['expressions'] 6
tableau Anonymous ['expressions'] 6
teradata Anonymous ['expressions'] 6
[assistant] The root cause is in `JSONArray` itself: it isn't marked variadic, so the parser's argument-count check rejects anything past the four declared keys. Marking it `is_var_len_args` requires `expressions` to be the last key in `arg_types`, so I'll reorder those too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143014-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n        \"expressions\": False,\n    }\n    is_var_len_args = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143014-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(sqlglot.transpile('JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='bigquery'))\nprint(sqlglot.transpile('JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='oracle'
…[40 chars elided]…
1, 2, 3, 4, 5, 6)', read='duckdb', write='snowflake'))\nprint(exp.JSONArray(expressions=[exp.column(c) for c in 'abcdef']).sql())\nprint(sqlglot.parse_one('JSON_ARRAY(1, 2)', read='bigquery').sql('duckdb'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] ['JSON_ARRAY(1, 2, 3, 4, 5, 6)']
['JSON_ARRAY(1, 2, 3, 4, 5, 6)']
['JSON_ARRAY(1, 2, 3, 4, 5, 6)']
['TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))']
JSON_ARRAY(a, b, c, d, e, f)
JSON_ARRAY(1, 2)
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................................... [ 41%]
....................................................................................................................................................... [ 55%]
.............
…[136 chars elided]…
................................................. [ 72%]
............................................. [ 76%]
............................................. [ 80%]
......................................... [ 84%]
....................................... [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1093 passed, 17868 subtests passed in 54.76s
[assistant] All 1093 tests pass. I'll add a regression test for the six-argument case next to the existing DuckDB `JSON_ARRAY` tests.
[tool_use Bash] {"command": "sed -n 550,582p tests/dialects/test_duckdb.py", "description": "View existing DuckDB JSON_ARRAY tests"}
[tool_result]             """SELECT '{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }' ->> ['$.family', '$.species']""",
        )
        self.validate_all(
            "SELECT JSON_ARRAY('a', 'b', 'c')",
            write={
                "duckdb": "SELECT JSON_ARRAY('a', 'b', 'c')",
                "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT('a', 'b', 'c'))",
            },
        )
        self.validate_all(
            "SELECT JSON_ARRAY(NULL, 'a', 1)",
            write={
   
…[311 chars elided]…
        "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT(NULL))",
            },
        )
        self.validate_all(
            "SELECT JSON_ARRAY()",
            write={
                "duckdb": "SELECT JSON_ARRAY()",
                "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT())",
            },
        )
        self.validate_identity(
            "SELECT col FROM t WHERE JSON_EXTRACT_STRING(col, '$.id') NOT IN ('b')",
            "SELECT col FROM t WHERE NOT (col ->> '$.id') IN ('b')",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143014-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[186 chars elided]…
()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143014-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git -c core.pager=cat diff --stat", "description": "Rerun test suite and show diff stats"}
[tool_result] ................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 57.18s
sqlglot/expressions/json.py   | 3 ++-
 tests/dialects/test_duckdb.py | 7 +++++++
 2 files changed, 9 insertions(+), 1 deletion(-)
[assistant] `JSON_ARRAY` now accepts any number of values. The full suite passes (1093 tests), including a new six-argument DuckDB case.

**Cause:** `JSONArray` in `sqlglot/expressions/json.py` wasn't marked variadic. The parser checks argument count against the number of declared keys (four), so DuckDB's `JSON_ARRAY(1, 2, 3, 4, 5, 6)` raised a ParseError.

**Fix:**
- Added `is_var_len_args = True` to `JSONArray`.
- Moved `expressions` to the last position in `arg_types`, since the variadic key must be last. Nothing depends on the key order, so this shouldn't change output.

**Existing dialects:** DuckDB, BigQuery, Oracle and SingleStore pass `expressions=` explicitly, so their parsing is unchanged. The six-argument call now round-trips through DuckDB, BigQuery, Oracle and Snowflake.

**Test:** Added a `validate_all` case in `tests/dialects/test_duckdb.py`, next to the existing `JSON_ARRAY` cases.

One caveat I left alone: calling `exp.JSONArray.from_arg_list` directly still maps positional args onto the optional keys (`null_handling`, etc.) rather than onto `expressions`. That was already wrong before this change, and no parser path uses it, so I didn't touch it. Say if you want it fixed too.
