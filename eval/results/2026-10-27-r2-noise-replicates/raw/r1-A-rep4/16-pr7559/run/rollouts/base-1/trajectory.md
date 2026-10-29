# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of values. The full suite passes (1093 passed), and the new tests pass.

**Cause:** `JSONArray` declared four fixed arguments (`expressions`, `null_handling`, `return_type`, `strict`) and did not mark itself variable-length. The argument-count check in the parser then rejected any call with more than four values. The DuckDB parser hit this path, so `SELECT JSON_ARRAY(1,2,3,4,5,6)` raised a `ParseError` there.

**Fix** (`sqlglot/expressions/json.py`):
- `is_var_len_args = True` removes the four-argument cap.
- A `from_arg_list` override maps every positional argument into `expressions`. The default mapping would have put the second value into `null_handling`, so `exp.func("JSON_ARRAY", 1, 2)` would have built a broken node.

The Oracle, DuckDB, BigQuery, Snowflake and SingleStore parsers construct `JSONArray` directly with keyword arguments, so their parsing is unchanged. I did not touch any existing test.

**Tests added:**
- `tests/test_expressions.py`: `exp.func("JSON_ARRAY", *range(1, 7))` renders as `JSON_ARRAY(1, 2, 3, 4, 5, 6)`.
- `tests/dialects/test_duckdb.py`: identity round-trip for the six-argument DuckDB call.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot/ | grep -v \"^sqlglot/dialects/.*JSON_ARRAY_AGG\" | head -50", "description": "Find JSONArray references in sqlglot source"}
[tool_result] sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._p
…[184 chars elided]…
arse_oracle_json_array(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers/oracle.py:114:            exp.JSONArray,
sqlglot/typing/bigquery.py:280:            exp.JSONArray,
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
[tool_use Bash] {"command": "cat sqlglot/expressions/json.py | head -60 && sed -n 3565,3590p sqlglot/generator.py && sed -n 105,125p sqlglot/parsers/oracle.py && sed -n 270,290p sqlglot/parsers/bigquery.py && sed -n 495,510p sqlglot/generators/snowflake.py && sed -n 160,170p sqlglot/generators/singlestore.py && sed -n 275,290p sqlglot/typing/bigquery.py", "description": "Read JSONArray definition and its usages"}
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
        
…[5326 chars elided]…
     exp.JSONBExists: lambda self, e: self.func(
            "BSON_MATCH_ANY_EXISTS", e.this, e.args.get("path")
        ),
        }
    },
    **{
        expr_type: {"returns": exp.DType.JSON}
        for expr_type in {
            exp.JSONArray,
            exp.JSONArrayAppend,
            exp.JSONArrayInsert,
            exp.JSONObject,
            exp.JSONRemove,
            exp.JSONSet,
            exp.JSONStripNulls,
        }
    },
    **{
        expr_type: {"returns": exp.DType.TIME}
[tool_use Bash] {"command": "grep -n \"is_var_len_args\" -A12 sqlglot/expressions/core.py | head -80; grep -rn \"JSON_ARRAY(\" tests/ | head -30; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef'])))\n\" 2>&1 | tail -5", "description": "Check var-len args handling and reproduce the failure"}
[tool_result] 87:    is_var_len_args: t.ClassVar[bool] = False
88-    _hash_raw_args: t.ClassVar[bool] = False
89-    is_subquery: t.ClassVar[bool] = False
90-    is_cast: t.ClassVar[bool] = False
91-
92-    args: dict[str, t.Any]
93-    parent: Expr | None
94-    arg_key: str | None
95-    index: int | None
96-    comments: list[str] | None
97-    _type: DataType | None
98-    _meta: dict[str, t.Any] | None
99-    _hash: int | None
--
1233:            and not self.is_var_len_args
1234-        ):
1235-       
…[3951 chars elided]…
lects/test_duckdb.py:576:                "duckdb": "SELECT JSON_ARRAY()",
tests/dialects/test_mysql.py:269:        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
tests/fixtures/optimizer/annotate_functions.sql:1311:JSON_ARRAY(10);
tests/fixtures/optimizer/annotate_functions.sql:1315:JSON_ARRAY(10, [1, 2]);
      this=Identifier(this=d, quoted=False)),
    Column(
      this=Identifier(this=e, quoted=False)),
    Column(
      this=Identifier(this=f, quoted=False))])
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ncols=[exp.column(c) for c in 'abcdef']\ne=exp.func('JSON_ARRAY', *cols)\nprint(type(e).__name__, e.args.keys())\nprint(e.sql())\nprint(exp.JSONArray(expressions=cols).sql())\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='oracle', write='oracle'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='mysql', write='snowflake'))\nprint(exp.func('JSON_ARRAY', *cols).sql(dialect='snowflake'))\n\" 2>&1 | tail -30", "description": "Reproduce JSON_ARRAY with six args"}
[tool_result]   File "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 6017, in _parse_type
    if not fallback_to_identifier and (atom := self._parse_atom()) is not None:
                                               ^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 6412, in _parse_atom
    and (column := self._parse
…[1508 chars elided]…
   self.raise_error(error_message)
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 1991, in raise_error
    raise error
sqlglot.errors.ParseError: The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 30.
  SELECT JSON_ARRAY(1,2,3,4,5,6[4m)[0m
Anonymous dict_keys(['this', 'expressions'])
JSON_ARRAY(a, b, c, d, e, f)
JSON_ARRAY(a, b, c, d, e, f)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['JSON_ARRAY(1, 2)','JSON_ARRAY(1)','JSON_ARRAY()','JSON_ARRAY(1,2,3,4)']:\n    e=sqlglot.parse_one('SELECT '+s).selects[0]\n    print(s, {k:v for k,v in e.args.items()})\ne=exp.func('JSON_ARRAY', exp.column('a'), exp.column('b'))\nprint(e.args)\n\" 2>&1 | tail -20; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.__file__)\"", "description": "Inspect current parse shape for 0-4 args"}
[tool_result] JSON_ARRAY(1, 2) {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False)]}
JSON_ARRAY(1) {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False)]}
JSON_ARRAY() {'this': 'JSON_ARRAY', 'expressions': []}
JSON_ARRAY(1,2,3,4) {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False)]}
{'this': 'JSON_ARRAY', 'expressions': [Column(
  this=Identifier(this=a, quoted=False)), Column(
  this=Identifier(this=b, quoted=False))]}
~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "for d in \"\" duckdb oracle mysql snowflake bigquery singlestore; do <work>/env-sqlglot/bin/python -c \"\nimport sqlglot,sys\nd=sys.argv[1] or None\ntry: print(repr(d), sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read=d, write=d)[0])\nexcept Exception as e: print(repr(d), 'ERR', type(e).__name__, str(e).splitlines()[0])\n\" \"$d\"; done; grep -n \"ALL_FUNCTIONS\\|def build_\\|from_arg_list\" sqlglot/parser.py | head", "description": "Check JSON_ARRAY six-arg parse across dialects"}
[tool_result] None SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
'duckdb' ERR ParseError The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 30.
'oracle' SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
'mysql' SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
'snowflake' SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
'bigquery' SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
'singlestore' SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
45:def build_var_map(args: BuilderArgs) -> exp.StarMap | exp.VarMap:
58:def build_li
…[5 chars elided]…
gs: BuilderArgs) -> exp.Escape | exp.Like:
75:def build_logarithm(args: BuilderArgs, dialect: Dialect) -> exp.Func:
88:def build_hex(args: BuilderArgs, dialect: Dialect) -> exp.Hex | exp.LowerHex:
93:def build_lower(args: BuilderArgs) -> exp.Lower | exp.Hex:
99:def build_upper(args: BuilderArgs) -> exp.Upper | exp.Hex:
105:def build_extract_json_with_path(
122:def build_mod(args: BuilderArgs) -> exp.Mod:
133:def build_pad(args: BuilderArgs, is_left: bool = True):
142:def build_array_constructor(
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import parser, exp\nprint(parser.Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint(exp.JSONArray.from_arg_list([exp.column('a'), exp.column('b')]).args)\n\"; sed -n 1,40p sqlglot/parser.py | grep -n import; grep -n \"ALL_FUNCTIONS\" sqlglot/*.py | head -5", "description": "Check base FUNCTIONS mapping for JSON_ARRAY"}
[tool_result] None
{'expressions': Column(
  this=Identifier(this=a, quoted=False)), 'null_handling': Column(
  this=Identifier(this=b, quoted=False))}
1:from __future__ import annotations
3:import itertools
4:import logging
5:import re
6:import typing as t
7:from collections import defaultdict
9:from sqlglot import exp
10:from sqlglot.errors import (
18:from sqlglot.expressions import apply_index_offset
19:from sqlglot.helper import ensure_list, i64, seq_get
20:from sqlglot.trie import new_trie
21:from sqlglot.time import format_time
22:from sqlglot.tokens import Token, Tokenizer, TokenType
23:from sqlglot.trie import TrieResult, in_trie
24:from collections.abc import Sequence
25:from builtins import type as Type
28:    from sqlglot.expressions import ExpOrStr
29:    from sqlglot._typing import E, BuilderArgs
30:    from sqlglot.dialects.dialect import Dialect, DialectType
32:    from re import Pattern
[tool_use Bash] {"command": "grep -rn \"def from_arg_list\" -A3 sqlglot/expressions/ | head -30; grep -rn \"is_var_len_args = True\" -B4 sqlglot/expressions/json.py | head -20", "description": "Look for from_arg_list override precedents"}
[tool_result] sqlglot/expressions/core.py:1633:    def from_arg_list(cls, args: Sequence[object]) -> Self:
sqlglot/expressions/core.py-1634-        if cls.is_var_len_args:
sqlglot/expressions/core.py-1635-            all_arg_keys = tuple(cls.arg_types)
sqlglot/expressions/core.py-1636-            # If this function supports variable length argument treat the last argument as such.
sqlglot/expressions/json.py-29-
sqlglot/expressions/json.py-30-
sqlglot/expressions/json.py-31-class JSONArrayAppend(Expression, F
…[337 chars elided]…
is": True, "expressions": True}
sqlglot/expressions/json.py:44:    is_var_len_args = True
--
sqlglot/expressions/json.py-107-        "requires_json": False,
sqlglot/expressions/json.py-108-        "emits": False,
sqlglot/expressions/json.py-109-    }
sqlglot/expressions/json.py-110-    _sql_names = ["JSON_EXTRACT"]
sqlglot/expressions/json.py:111:    is_var_len_args = True
--
sqlglot/expressions/json.py-129-        "json_type": False,
sqlglot/expressions/json.py-130-        "scalar_only": False,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n    is_var_len_args = True\n\n    @classmethod\n    def from_arg_list(cls, args):\n        return cls(expressions=args)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in [None,'duckdb','oracle','mysql','snowflake','bigquery','singlestore']:\n    print(d, sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read=d, write=d)[0])\ne=exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef'])\nprint(e.sql(), e.sql('duckdb'), e.sql('snowflake'))\nprint(exp.func('JSON_ARRAY', 1, 2).sql())\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='duckdb', write='snowflake')[0])\n\" 2>&1 | tail -20", "description": "Verify six-arg JSON_ARRAY across dialects"}
[tool_result] None SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
duckdb SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
oracle SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
mysql SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
snowflake SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
bigquery SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
singlestore SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
JSON_ARRAY(a, b, c, d, e, f) JSON_ARRAY(a, b, c, d, e, f) JSON_ARRAY(a, b, c, d, e, f)
JSON_ARRAY(1, 2)
SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))
[assistant] Six-argument calls now work everywhere. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_expressions.py | head -5; grep -n \"exp.func(\" tests/test_expressions.py | head -5", "description": "Find a spot for a regression test"}
[tool_result] 12:    def test_to_s(self):
25:    def test_arg_key(self):
28:    def test_depth(self):
31:    def test_iter(self):
38:    def test_eq(self):
377:        self.assertEqual(exp.func("max", 1).sql(), "MAX(1)")
378:        self.assertEqual(exp.func("max", 1, 2).sql(), "MAX(1, 2)")
379:        self.assertEqual(exp.func("bla", 1, "foo").sql(), "BLA(1, foo)")
380:        self.assertEqual(exp.func("COUNT", exp.Star()).sql(), "COUNT(*)")
381:        self.assertEqual(exp.func("bloo").sql(), "BLOO()")
[tool_use Bash] {"command": "sed -n 370,390p tests/test_expressions.py", "description": "View surrounding test context"}
[tool_result]             exp.replace_placeholders(
                parse_one("select * from foo WHERE x > :int1 AND y IS :bool1"), int1=0, bool1=False
            ).sql(),
            "SELECT * FROM foo WHERE x > 0 AND y IS FALSE",
        )

    def test_function_building(self):
        self.assertEqual(exp.func("max", 1).sql(), "MAX(1)")
        self.assertEqual(exp.func("max", 1, 2).sql(), "MAX(1, 2)")
        self.assertEqual(exp.func("bla", 1, "foo").sql(), "BLA(1, foo)")
        self.assertEqual(exp.fu
…[7 chars elided]…
NT", exp.Star()).sql(), "COUNT(*)")
        self.assertEqual(exp.func("bloo").sql(), "BLOO()")
        self.assertEqual(
            exp.func("concat", exp.convert("a"), dialect="duckdb").sql("duckdb"), "CONCAT('a')"
        )
        self.assertEqual(
            exp.func("locate", "'x'", "'xo'", dialect="hive").sql("hive"), "LOCATE('x', 'xo')"
        )
        self.assertEqual(
            exp.func("log", exp.to_identifier("x"), 2, dialect="bigquery").sql("bigquery"),
            "LOG(x, 2)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/tests/test_expressions.py", "old_string": "        self.assertEqual(exp.func(\"bloo\").sql(), \"BLOO()\")\n        self.assertEqual(\n            exp.func(\"concat\", exp.convert(\"a\"), dialect=\"duckdb\").sql(\"duckdb\"), \"CONCAT('a')\"", "new_string": "        self.assertEqual(exp.func(\"bloo\").sql(), \"BLOO()\")\n        self.assertEqual(\n            exp.func(\"JSON_ARRAY\", *range(1, 7)).sql(), \"JSON_ARRAY(1, 2, 3, 4, 5, 6)\"\n        )\n        self.assertEqual(\n            exp.func(\"concat\", exp.convert(\"a\"), dialect=\"duckdb\").sql(\"duckdb\"), \"CONCAT('a')\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/tests/test_expressions.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 550,580p tests/dialects/test_duckdb.py", "description": "View existing duckdb JSON_ARRAY tests"}
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
   
…[157 chars elided]…
     )
        self.validate_all(
            "SELECT JSON_ARRAY(NULL)",
            write={
                "duckdb": "SELECT JSON_ARRAY(NULL)",
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_identity(\"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172829-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite", "timeout": 900000}
[tool_result] .... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................................... [ 41%]
....................................................................................................................................................... [ 55%]
.......................................... [ 59%]
......................................................... [ 64%]
................................................................................... [ 72%]
............................................. [ 76%]
............................................. [ 80%]
......................................... [ 84%]
....................................... [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1093 passed, 17868 subtests passed in 52.59s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/expressions/json.py tests/test_expressions.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/expressions/json.py tests/test_expressions.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; git diff --stat", "description": "Lint, format-check, and show diff stat"}
[tool_result] All checks passed!
Would reformat: tests/test_expressions.py
1 file would be reformatted, 2 files already formatted
 sqlglot/expressions/json.py   | 5 +++++
 tests/dialects/test_duckdb.py | 1 +
 tests/test_expressions.py     | 3 +++
 3 files changed, 9 insertions(+)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format tests/test_expressions.py && git diff", "description": "Apply formatter and show final diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/expressions/json.py b/sqlglot/expressions/json.py
index 8f006c49a..8f0e57247 100644
--- a/sqlglot/expressions/json.py
+++ b/sqlglot/expressions/json.py
@@ -16,6 +16,11 @@ class JSONArray(Expression, Func):
         "return_type": False,
         "strict": False,
     }
+    is_var_len_args = True
+
+    @classmethod
+    def from_arg_list(cls, args):
+        return cls(expressions=args)
 
 
 class JSONArrayAgg(Expression, AggFunc):
diff --git a/tests/dial
…[838 chars elided]…
ql(), "BLA(1, foo)")
         self.assertEqual(exp.func("COUNT", exp.Star()).sql(), "COUNT(*)")
         self.assertEqual(exp.func("bloo").sql(), "BLOO()")
+        self.assertEqual(exp.func("JSON_ARRAY", *range(1, 7)).sql(), "JSON_ARRAY(1, 2, 3, 4, 5, 6)")
         self.assertEqual(
             exp.func("concat", exp.convert("a"), dialect="duckdb").sql("duckdb"), "CONCAT('a')"
         )
[This command modified 1 file you've previously read: tests/test_expressions.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_expressions.py tests/dialects/test_duckdb.py 2>&1 | tail -2", "description": "Rerun the two touched test files"}
[tool_result] ...                                                         [100%]
113 passed, 623 subtests passed in 0.36s
[assistant] `JSON_ARRAY` now accepts any number of values. The full suite passes (1093 passed), and the new tests pass.

**Cause:** `JSONArray` declared four fixed arguments (`expressions`, `null_handling`, `return_type`, `strict`) and did not mark itself variable-length. The argument-count check in the parser then rejected any call with more than four values. The DuckDB parser hit this path, so `SELECT JSON_ARRAY(1,2,3,4,5,6)` raised a `ParseError` there.

**Fix** (`sqlglot/expressions/json.py`):
- `is_var_len_args = True` removes the four-argument cap.
- A `from_arg_list` override maps every positional 
…[20 chars elided]…
ssions`. The default mapping would have put the second value into `null_handling`, so `exp.func("JSON_ARRAY", 1, 2)` would have built a broken node.

The Oracle, DuckDB, BigQuery, Snowflake and SingleStore parsers construct `JSONArray` directly with keyword arguments, so their parsing is unchanged. I did not touch any existing test.

**Tests added:**
- `tests/test_expressions.py`: `exp.func("JSON_ARRAY", *range(1, 7))` renders as `JSON_ARRAY(1, 2, 3, 4, 5, 6)`.
- `tests/dialects/test_duckdb.py`: identity round-trip for the six-argument DuckDB call.

The changes are uncommitted in the worktree.
