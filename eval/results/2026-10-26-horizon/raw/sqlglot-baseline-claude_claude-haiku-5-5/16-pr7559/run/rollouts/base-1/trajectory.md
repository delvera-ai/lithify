# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of arguments. A six-argument DuckDB call that used to raise a `ParseError` now parses and round-trips, and the full suite passes (1093 tests).

**The fix** is in `sqlglot/expressions/json.py`. `JSONArray` had no variadic marker, so the parser's argument-count check capped it at the four keys in `arg_types`. I set `is_var_len_args = True` and moved `expressions` to the end of `arg_types`. That follows the convention `JSONExtract` and `JSONKeys` already use.

**Existing dialects are unchanged.** Before and after, I parsed and regenerated `JSON_ARRAY` with 0, 1, 2, 3, 4 and 6 arguments across every registered dialect and diffed the output. The only difference was the DuckDB six-argument case that used to fail. Base and Snowflake parse `JSON_ARRAY` as an anonymous function, so they were never affected.

**Test:** I added a six-argument case to `tests/dialects/test_duckdb.py`, covering DuckDB round-trip and Snowflake output.

**Checks:** the full suite passes with the project interpreter, and `ruff check` and `ruff format --check` are clean on the touched files.

**Decision for you:** reordering `arg_types` changes what the generic `from_arg_list` does positionally for `JSONArray`. That path isn't reached for `JSON_ARRAY` in any dialect today, so I left it. If you want it covered, I can add an explicit `from_arg_list` override.

The changes are uncommitted in the worktree. I haven't committed, since you didn't ask for that. The project's CLAUDE.md asks for the model name at the end of commit messages and PR titles, so I'll include it if you want a commit.

## events
[tool_use Bash] {"command": "rtk grep -rn \"JSONArray\\b\" sqlglot/ | head -50", "description": "Find JSONArray references in sqlglot source"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot/ | head -60", "description": "Find JSONArray references in sqlglot source"}
[tool_result] sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/duckdb.py:133:        "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.express
…[184 chars elided]…
arse_oracle_json_array(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers/oracle.py:114:            exp.JSONArray,
sqlglot/typing/bigquery.py:280:            exp.JSONArray,
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/expressions/json.py; echo ----; sed -n 3570,3585p sqlglot/generator.py; echo ----; sed -n 110,120p sqlglot/parsers/oracle.py; echo ----; sed -n 495,505p sqlglot/generators/snowflake.py; echo ----; sed -n 160,170p sqlglot/generators/singlestore.py; echo ---; sed -n 275,285p sqlglot/typing/bigquery.py", "description": "Read JSONArray definition and its usages"}
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
        
…[2517 chars elided]…
null_handling", "return_type", "strict")(
            rename_func("JSON_BUILD_ARRAY")
        ),
        exp.JSONBExists: lambda self, e: self.func(
            "BSON_MATCH_ANY_EXISTS", e.this, e.args.get("path")
        ),
---
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
[assistant] The likely cause is that `JSONArray` is missing `is_var_len_args = True`, which `JSONArrayAppend` sets. Let me reproduce before changing anything.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(exp.JSONArray.is_var_len_args)\nprint(exp.func('JSON_ARRAY', 1,2,3,4,5,6).sql())\nprint(exp.JSONArray(expressions=[exp.Literal.number(i) for i in range(1,7)]).sql())\ntry:\n    print(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='duckdb', write='duckdb'))\nexcept Exception as e: print('ERR', e)\n\" ; grep -n \"is_var_len_args\" sqlglot/expressions/core.py sqlglot/*.py | head -20", "description": "Reproduce JSON_ARRAY argument limit issue"}
[tool_result] False
JSON_ARRAY(1, 2, 3, 4, 5, 6)
JSON_ARRAY(1, 2, 3, 4, 5, 6)
ERR The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 30.
  SELECT JSON_ARRAY(1,2,3,4,5,6[4m)[0m
sqlglot/expressions/core.py:87:    is_var_len_args: t.ClassVar[bool] = False
sqlglot/expressions/core.py:1233:            and not self.is_var_len_args
sqlglot/expressions/core.py:1621:        is_var_len_args (bool): if set to True the last argument defined in arg_types will
…[74 chars elided]…
 = False
sqlglot/expressions/core.py:1634:        if cls.is_var_len_args:
sqlglot/expressions/core.py:1637:            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
sqlglot/expressions/core.py:1945:    is_var_len_args = True
sqlglot/expressions/core.py:1954:    is_var_len_args = True
sqlglot/expressions/core.py:1967:    is_var_len_args = True
sqlglot/expressions/core.py:1972:    is_var_len_args = True
sqlglot/expressions/core.py:2273:    is_var_len_args = True
[assistant] Reproduced: parsing a six-argument `JSON_ARRAY` raises. Next I'll check how `is_var_len_args` works, since the last `arg_types` key is the one it applies to.
[tool_use Bash] {"command": "sed -n 1615,1660p sqlglot/expressions/core.py; echo ----; sed -n 1222,1245p sqlglot/expressions/core.py; echo ----; grep -n \"is_var_len_args\" -B3 sqlglot/expressions/json.py sqlglot/expressions/*.py | grep -v core.py | head -30", "description": "Read is_var_len_args handling in core"}
[tool_result] @trait
class Func(Condition):
    """
    The base class for all function expressions.

    Attributes:
        is_var_len_args (bool): if set to True the last argument defined in arg_types will be
            treated as a variable length argument and the argument's value will be stored as a list.
        _sql_names (list): the SQL name (1st item in the list) and aliases (subsequent items) for this
            function expression. These values are used to map this node to a name during parsing a
…[3225 chars elided]…
ssions/json.py-144-
sqlglot/expressions/json.py-145-class JSONKeys(Expression, Func):
sqlglot/expressions/json.py-146-    arg_types = {"this": True, "expression": False, "expressions": False}
sqlglot/expressions/json.py:147:    is_var_len_args = True
--
sqlglot/expressions/json.py-174-
sqlglot/expressions/json.py-175-class JSONRemove(Expression, Func):
sqlglot/expressions/json.py-176-    arg_types = {"this": True, "expressions": True}
sqlglot/expressions/json.py:177:    is_var_len_args = True
--
[assistant] The convention is that the variadic key is the last entry in `arg_types`, but `JSONArray` has `expressions` first. Moving it would change positional parsing in `from_arg_list`, so I need a baseline before deciding. I'll snapshot how each dialect parses `JSON_ARRAY` now.
[tool_use Bash] {"command": "mkdir -p /tmp/jsonarr_probe && cat > /tmp/jsonarr_probe/probe.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.dialect import Dialect\nout = []\ndialects = [None] + sorted(Dialect.classes)\nfor d in dialects:\n    for n in [0, 1, 2, 3, 4, 6]:\n        sql = f\"SELECT JSON_ARRAY({', '.join(str(i) for i in range(1, n + 1))})\"\n        try:\n            tree = 
…[383 chars elided]…
ception as e:\n            out.append(f\"{d} n={n} sql -> ERR {type(e).__name__}\")\nprint(\"\\n\".join(out))\nEOF\nPYTHONPATH=. python -I /tmp/jsonarr_probe/probe.py > /tmp/jsonarr_probe/before.txt 2>&1; wc -l /tmp/jsonarr_probe/before.txt; grep -E \"^(None|duckdb|oracle|bigquery|snowflake) n=(4|6)\" /tmp/jsonarr_probe/before.txt", "description": "Snapshot JSON_ARRAY parsing across all dialects"}
[tool_result]        4 /tmp/jsonarr_probe/before.txt
[tool_use Bash] {"command": "cat /tmp/jsonarr_probe/before.txt", "description": "Show probe output"}
[tool_result] Traceback (most recent call last):
  File "/tmp/jsonarr_probe/probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` also ignores `PYTHONPATH`, so I'll run the probe without it. The script lives outside the repo, so nothing gets shadowed.
[tool_use Bash] {"command": "PYTHONPATH=. python /tmp/jsonarr_probe/probe.py > /tmp/jsonarr_probe/before.txt 2>&1; wc -l /tmp/jsonarr_probe/before.txt; grep -E \"^(None|duckdb|oracle|bigquery|snowflake) n=(4|6)\" /tmp/jsonarr_probe/before.txt", "description": "Snapshot JSON_ARRAY parsing across all dialects"}
[tool_result]      414 /tmp/jsonarr_probe/before.txt
None n=4 -> None
None n=4 sql -> SELECT JSON_ARRAY(1, 2, 3, 4)
None n=6 -> None
None n=6 sql -> SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
bigquery n=4 -> {'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False)]}
bigquery n=4 sql -> SELECT JSON_ARRAY(1, 2, 3, 4)
bigquery n=6 -> {'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(
…[866 chars elided]…
ndling': None, 'return_type': False, 'strict': False, 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False), Literal(this=5, is_string=False), Literal(this=6, is_string=False)], 'join_mark': False}
oracle n=6 sql -> SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
snowflake n=4 -> None
snowflake n=4 sql -> SELECT JSON_ARRAY(1, 2, 3, 4)
snowflake n=6 -> None
snowflake n=6 sql -> SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
[assistant] The probe shows base dialect parses `JSON_ARRAY` as `Anonymous`, so only the dialects that build `JSONArray` are affected. Next I'll check how `exp.func` and `from_arg_list` treat `JSONArray` and whether any existing class overrides `from_arg_list`.
[tool_use Bash] {"command": "grep -n \"^def func\" -A60 sqlglot/expressions/*.py | grep -n \"from_arg_list\\|Anonymous\\|def func\\|is_var\" | head; echo ----; grep -rn \"def from_arg_list\" sqlglot/ | head; echo ----; PYTHONPATH=. python -c \"\nfrom sqlglot import exp\nfor args in [(1,2),(1,2,3,4,5,6)]:\n    e = exp.func('JSON_ARRAY', *args)\n    print(type(e).__name__, repr(e.args)[:200])\nprint(exp.JSONArray(expressions=[exp.column('a')]).sql())\n\"; grep -n \"_parse_json_array\" -A25 sqlglot/parser.py | head -40", "description": "Inspect exp.func, from_arg_list overrides, and JSON array parser"}
[tool_result] 1:sqlglot/expressions/builders.py:924:def func(
45:sqlglot/expressions/builders.py-968-        elif constructor.__name__ == "from_arg_list":
60:sqlglot/expressions/builders.py-983-        function = Anonymous(this=name, **kwargs)
----
sqlglot/expressions/core.py:1633:    def from_arg_list(cls, args: Sequence[object]) -> Self:
----
Anonymous {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False)]}
Anonymous {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False), Literal(this=5, is_string
JSON_ARRAY(a)
[tool_use Bash] {"command": "sed -n 924,990p sqlglot/expressions/builders.py; echo ----; grep -rn \"_parse_json_array\" sqlglot/ | head -5", "description": "Read exp.func builder implementation"}
[tool_result] def func(
    name: str, *args: t.Any, copy: bool = True, dialect: DialectType = None, **kwargs: t.Any
) -> Func:
    """
    Returns a Func expression.

    Examples:
        >>> func("abs", 5).sql()
        'ABS(5)'

        >>> func("cast", this=5, to=DataType.build("DOUBLE")).sql()
        'CAST(5 AS DOUBLE)'

    Args:
        name: the name of the function to build.
        args: the args used to instantiate the function of interest.
        copy: whether to copy the argument expressions.

…[1622 chars elided]…
."
                )
    else:
        kwargs = kwargs or {"expressions": converted}
        function = Anonymous(this=name, **kwargs)

    for error_message in function.error_messages(converted):
        raise ValueError(error_message)

    return function


----
sqlglot/parsers/oracle.py:113:        return self._parse_json_array(
sqlglot/parsers/oracle.py:119:        return self._parse_json_array(
sqlglot/parsers/oracle.py:125:    def _parse_json_array(self, expr_type: type[E], **kwargs) -> E:
[assistant] `exp.func` only yields `JSONArray` if the dialect registers `JSON_ARRAY` in `FUNCTIONS`, so the bounded path is the parser's `validate_expression`. Let me confirm where the limit is applied.
[tool_use Bash] {"command": "sed -n 1195,1222p sqlglot/expressions/core.py; echo ----; grep -n \"def validate_expression\" -A25 sqlglot/parser.py | head -40", "description": "Read error_messages and validate_expression"}
[tool_result]             >>> import sqlglot
            >>> sqlglot.parse_one("SELECT x from y").assert_is(sqlglot.exp.Select).select("z").sql()
            'SELECT x, z FROM y'
        """
        if not isinstance(self, type_):
            raise AssertionError(f"{self} is not {type_}.")
        return self

    def error_messages(self, args: Sequence[object] | None = None) -> list[str]:
        """
        Checks if this expression is valid (e.g. all mandatory args are set).

        Args:
            args
…[1158 chars elided]…
 bool = False) -> T | None:
2006-        index = self._index
2007-        error_level = self.error_level
2008-        this: T | None = None
2009-
2010-        self.error_level = ErrorLevel.IMMEDIATE
2011-        try:
2012-            this = parse_method()
2013-        except ParseError:
2014-            this = None
2015-        finally:
2016-            if not this or retreat:
2017-                self._retreat(index)
2018-            self.error_level = error_level
2019-
2020-        return this
[assistant] The limit comes from `error_messages(args)` comparing the positional count against `len(arg_types)`. Setting `is_var_len_args` skips that check, but `from_arg_list` then treats the last `arg_types` key as variadic. I need to know whether the generic `from_arg_list` path can reach `JSONArray` before I change the key order.
[tool_use Bash] {"command": "grep -rn \"ALL_FUNCTIONS\" sqlglot/ | head; echo ----; grep -n \"FUNCTION_BY_NAME\\b\" sqlglot/expressions/*.py | head -5; echo ----; sed -n 95,112p sqlglot/expressions/json.py; echo ----; grep -n \"JSON_ARRAY\\|JSONArray\" tests/*.py tests/dialects/*.py | head -40", "description": "Check function registry and existing JSON_ARRAY tests"}
[tool_result] sqlglot/expressions/__init__.py:49:ALL_FUNCTIONS = subclasses(__name__, Func, {AggFunc, Anonymous, Func})
sqlglot/expressions/__init__.py:50:FUNCTION_BY_NAME = {name: func for func in ALL_FUNCTIONS for name in func.sql_names()}
sqlglot/generators/python.py:78:        **{klass: _rename for klass in exp.ALL_FUNCTIONS},
----
sqlglot/expressions/__init__.py:50:FUNCTION_BY_NAME = {name: func for func in ALL_FUNCTIONS for name in func.sql_names()}
sqlglot/expressions/builders.py:971:            from s
…[4791 chars elided]…
) AS element
tests/dialects/test_postgres.py:428:  JSON_ARRAY_ELEMENTS(JSON_EXTRACT_PATH(json_data.data, field_ids.field_id)) AS element
tests/dialects/test_postgres.py:1546:CROSS JOIN JSON_ARRAY_ELEMENTS(CAST(boxcrate AS JSON)) AS x(tbox)
tests/dialects/test_postgres.py:1547:CROSS JOIN JSON_ARRAY_ELEMENTS(CAST(JSON_EXTRACT_PATH(tbox, 'boxes') AS JSON)) AS y(boxes)"""
tests/dialects/test_singlestore.py:224:        self.validate_identity("SELECT JSON_ARRAY_CONTAINS_STRING('[\"a\", \"b\"]', 'b')")
[assistant] Base-dialect `FUNCTIONS` doesn't register `JSON_ARRAY`, so `from_arg_list` isn't reached for it in any dialect today. That makes the repo convention safe to follow: put the variadic `expressions` key last and set `is_var_len_args = True`, as `JSONExtract` and `JSONKeys` already do. Applying that now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142539-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n        \"expressions\": False,\n    }\n    is_var_len_args = True"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142539-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python /tmp/jsonarr_probe/probe.py > /tmp/jsonarr_probe/after.txt 2>&1; diff /tmp/jsonarr_probe/before.txt /tmp/jsonarr_probe/after.txt", "description": "Re-run probe and diff against baseline"}
[tool_result] 131,132c131,132
< duckdb n=6 -> ERR ParseError: The number of provided arguments (6) is greater than the maximum number of suppo
< duckdb n=6 sql -> ERR ParseError
---
> duckdb n=6 -> {'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False), Literal(this=5, is_string=False), Literal(this=6, is_string=False)]}
> duckdb n=6 sql -> SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
[assistant] The only behavior change is the intended one: a six-argument DuckDB `JSON_ARRAY` now parses. Next I'll add a regression test next to the existing DuckDB `JSON_ARRAY` tests.
[tool_use Bash] {"command": "sed -n 548,582p tests/dialects/test_duckdb.py", "description": "Read existing DuckDB JSON_ARRAY tests"}
[tool_result]         self.validate_identity(
            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
            """SELECT '{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }' ->> ['$.family', '$.species']""",
        )
        self.validate_all(
            "SELECT JSON_ARRAY('a', 'b', 'c')",
            write={
                "duckdb": "SELECT JSON_ARRAY('a', 'b', 'c')",
                "snowflak
…[490 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142539-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[182 chars elided]…
AY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142539-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the project's test command from the harness instructions. I'll confirm that interpreter exists first.
[tool_use Bash] {"command": "ls -la <work>/env-sqlglot/bin/python 2>&1; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_oracle.py tests/dialects/test_bigquery.py tests/dialects/test_snowflake.py tests/dialects/test_singlestore.py 2>&1 | tail -15", "description": "Run targeted dialect tests with project interpreter"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
........................ [  9%]
........................................................................................................................ [ 58%]
................................................... [ 78%]
.......................................... [ 95%]
......... [ 99%]
.                                                                  [100%]
247 passed, 3648 subtests passed in 1.04s
[assistant] The targeted dialect tests pass. Next I'll run the full suite and the repo's style check.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; echo \"--- ruff:\"; ($PY -m ruff check sqlglot/expressions/json.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/expressions/json.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Run full test suite and ruff checks"}
[tool_result] ................................................................................................. [ 51%]
......................................................... [ 57%]
................................................................................................................................................................... [ 72%]
............................................. [ 76%]
............................................. [ 80%]
................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 56.77s
--- ruff:
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "git diff --stat && git diff sqlglot/ && rm -rf /tmp/jsonarr_probe", "description": "Show final diff and clean up probe files"}
[tool_result]  sqlglot/expressions/json.py   | 3 ++-
 tests/dialects/test_duckdb.py | 7 +++++++
 2 files changed, 9 insertions(+), 1 deletion(-)
diff --git a/sqlglot/expressions/json.py b/sqlglot/expressions/json.py
index 8f006c49a..bc3096d42 100644
--- a/sqlglot/expressions/json.py
+++ b/sqlglot/expressions/json.py
@@ -11,11 +11,12 @@ class CheckJson(Expression, Func):
 
 class JSONArray(Expression, Func):
     arg_types = {
-        "expressions": False,
         "null_handling": False,
         "return_type": False,
         "strict": False,
+        "expressions": False,
     }
+    is_var_len_args = True
 
 
 class JSONArrayAgg(Expression, AggFunc):
[assistant] `JSON_ARRAY` now accepts any number of arguments. A six-argument DuckDB call that used to raise a `ParseError` now parses and round-trips, and the full suite passes (1093 tests).

**The fix** is in `sqlglot/expressions/json.py`. `JSONArray` had no variadic marker, so the parser's argument-count check capped it at the four keys in `arg_types`. I set `is_var_len_args = True` and moved `expressions` to the end of `arg_types`. That follows the convention `JSONExtract` and `JSONKeys` already use.

**Existing dialects are unchanged.** Before and after, I parsed and regenerated `JSON_ARRAY` with 0, 1
…[412 chars elided]…
e project interpreter, and `ruff check` and `ruff format --check` are clean on the touched files.

**Decision for you:** reordering `arg_types` changes what the generic `from_arg_list` does positionally for `JSONArray`. That path isn't reached for `JSON_ARRAY` in any dialect today, so I left it. If you want it covered, I can add an explicit `from_arg_list` override.

The changes are uncommitted in the worktree. I haven't committed, since you didn't ask for that. The project's CLAUDE.md asks for the model name at the end of commit messages and PR titles, so I'll include it if you want a commit.
