# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of values. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses for DuckDB and transpiles to Snowflake. The full suite passes (1093 tests) and ruff is clean on the changed files. I haven't committed.

**Cause:** `JSONArray` in `sqlglot/expressions/json.py` had four `arg_types` and wasn't marked variadic. DuckDB builds it as `exp.JSONArray(expressions=args)`, and `Expression.error_messages` rejected any call with more than four arguments.

**Fix:** I moved `expressions` to the last position in `arg_types` and set `is_var_len_args = True`. This matches how `JSONArrayAppend` and `JSONArrayInsert` in the same file are declared.

**Existing dialects:** Oracle, BigQuery, DuckDB and SingleStore all construct `JSONArray` with keyword arguments, so their parsing is unchanged. The one behavioural difference is positional construction through `from_arg_list`, which now maps positional values after the fixed keywords rather than onto `expressions`. Nothing in the repo or tests uses it that way.

**Test:** I added a case to `tests/dialects/test_duckdb.py` covering six arguments, round-tripped in DuckDB and transpiled to Snowflake.

## events
[tool_use Bash] {"command": "grep -rn \"JsonArray\\b\\|JSON_ARRAY\\|JSONArray\\b\" --include=*.py sqlglot tests | head -60", "description": "Find JSON_ARRAY references in source and tests"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot tests | grep -v \"JSON_ARRAY_\" | head -60", "description": "Find JSON_ARRAY references in source and tests"}
[tool_result] sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._p
…[1947 chars elided]…

tests/dialects/test_singlestore.py:254:                "oracle": "SELECT JSON_ARRAY(id, name) FROM t",
tests/dialects/test_singlestore.py:257:        self.validate_identity("JSON_BUILD_ARRAY(id, name)").assert_is(exp.JSONArray)
tests/dialects/test_oracle.py:81:            "SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
tests/fixtures/optimizer/annotate_functions.sql:1311:JSON_ARRAY(10);
tests/fixtures/optimizer/annotate_functions.sql:1315:JSON_ARRAY(10, [1, 2]);
[tool_use Bash] {"command": "cat sqlglot/expressions/json.py | head -40 && grep -n \"class Func\\b\" -A5 sqlglot/expressions/core.py | head; grep -rn \"is_var_len_args\\|_parse_csv\\|arg_types = \" sqlglot/expressions/json.py | head -5; grep -n \"is_var_len_args\" sqlglot/expressions/*.py | head -5; cat sqlglot/parsers/oracle.py | sed -n 105,130p; sed -n 3570,3585p sqlglot/generator.py", "description": "Inspect JSONArray definition and related parsers"}
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
        
…[2523 chars elided]…
lse ""
        return_type = self.sql(expression, "return_type")
        return_type = f" RETURNING {return_type}" if return_type else ""
        strict = " STRICT" if expression.args.get("strict") else ""
        return self.func(
            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
        )

    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
        this = self.sql(expression, "this")
        order = self.sql(expression, "order")
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.func('JSON_ARRAY', *[exp.Literal.number(i) for i in range(1,7)])))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb'))\n\" 2>&1 | tail -5; sed -n 1616,1660p sqlglot/expressions/core.py; grep -n \"def validate_expression\" -A40 sqlglot/expressions/core.py | head -60", "description": "Reproduce JSON_ARRAY argument limit and read validation code"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
class Func(Condition):
    """
    The base class for all function expressions.

    Attributes:
        is_var_len_args (bool): if set to True the last argument defined in arg_types will be
            treated as a variable length argument and the argument's value will be stored as a list.
        _sql_names (list): the SQL name (1st item in the list) and aliases (subsequent 
…[1081 chars elided]…


    @classmethod
    def sql_names(cls) -> list[str]:
        if cls is Func:
            raise NotImplementedError(
                "SQL name is only supported by concrete function implementations"
            )
        if not cls._sql_names:
            return [camel_to_snake_case(cls.__name__)]
        return cls._sql_names

    @classmethod
    def sql_name(cls) -> str:
        sql_names = cls.sql_names()
        assert sql_names, f"Expected non-empty 'sql_names' for Func: {cls.__name__}."
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls $P && PYTHONPATH=. $P -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.func('JSON_ARRAY', *[exp.Literal.number(i) for i in range(1,7)])))\n\" 2>&1 | tail -5; PYTHONPATH=. $P -I -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='oracle', write='oracle'))\n\" 2>&1 | tail -5", "description": "Reproduce JSON_ARRAY limit with project interpreter"}
[tool_result] <work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pip list 2>/dev/null | head -30; python3 -c \"import sqlglot,sys;print(sqlglot.__file__)\" 2>&1 | tail -1", "description": "Check which packages the project env has"}
[tool_result] ~/.cache/lithify/work/repo-161bf5b46800/20261026-184756-json-array-accepts-at-most-four/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls -la $P; $P -m pytest --version 2>&1 | tail -1; python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.func('JSON_ARRAY', *[exp.Literal.number(i) for i in range(1,7)])))\n\" 2>&1 | tail -3; python3 -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='oracle', write='oracle'))\n\" 2>&1 | tail -3", "description": "Check project env and reproduce with system python"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
pytest 9.1.1
    Literal(this=4, is_string=False),
    Literal(this=5, is_string=False),
    Literal(this=6, is_string=False)])
    raise error
sqlglot.errors.ParseError: The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 35.
  SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6[4m)[0m
[tool_use Bash] {"command": "grep -rn \"maximum number of supported\" sqlglot | head; grep -n \"def validate_expression\" -A30 sqlglot/expressions/core.py sqlglot/*.py | head -50", "description": "Locate argument count validation code"}
[tool_result] sqlglot/expressions/core.py:1239:                f"the maximum number of supported arguments ({len(self.arg_types)})"
sqlglot/parser.py:1995:    def validate_expression(self, expression: E, args: list | None = None) -> E:
sqlglot/parser.py-1996-        if self.max_nodes > -1:
sqlglot/parser.py-1997-            self._node_count += 1
sqlglot/parser.py-1998-            if self._node_count > self.max_nodes:
sqlglot/parser.py-1999-                self.raise_error(f"Maximum number of AST nodes ({self.
…[1008 chars elided]…
er.py-2017-                self._retreat(index)
sqlglot/parser.py-2018-            self.error_level = error_level
sqlglot/parser.py-2019-
sqlglot/parser.py-2020-        return this
sqlglot/parser.py-2021-
sqlglot/parser.py-2022-    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
sqlglot/parser.py-2023-        """
sqlglot/parser.py-2024-        Parses a list of tokens and returns a list of syntax trees, one tree
sqlglot/parser.py-2025-        per parsed SQL statement.
[tool_use Bash] {"command": "sed -n 1215,1260p sqlglot/expressions/core.py; grep -n \"is_var_len_args\" sqlglot/expressions/core.py sqlglot/expressions/*.py | head -40", "description": "Read argument validation logic in Expression"}
[tool_result]         if UNITTEST:
            for k in self.args:
                if k not in self.arg_types:
                    raise TypeError(f"Unexpected keyword: '{k}' for {self.__class__}")

        errors: list[str] | None = None

        for k in self.required_args:
            v = self.args.get(k)
            if v is None or (isinstance(v, list) and not v):
                if errors is None:
                    errors = []
                errors.append(f"Required keyword: '{k}' missing for {self.__
…[3259 chars elided]…
ns/core.py:1621:        is_var_len_args (bool): if set to True the last argument defined in arg_types will be
sqlglot/expressions/core.py:1629:    is_var_len_args: t.ClassVar[bool] = False
sqlglot/expressions/core.py:1634:        if cls.is_var_len_args:
sqlglot/expressions/core.py:1637:            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
sqlglot/expressions/core.py:1945:    is_var_len_args = True
sqlglot/expressions/core.py:1954:    is_var_len_args = True
[tool_use Bash] {"command": "sed -n 1,60p sqlglot/expressions/json.py | grep -n \"class\\|arg_types\\|is_var\" ; grep -n \"class JSONObject\\b\" -A12 sqlglot/expressions/json.py; python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['JSON_ARRAY(1, 2, 3)','JSON_ARRAY(1, 2, 3, 4, 5, 6)']:\n    try: print(repr(sqlglot.parse_one(s)))\n    except Exception as e: print('ERR', e)\n    try: print(sqlglot.transpile(s, read='duckdb', write='duckdb'))\n    except Exception as e: print('ERR', e)\n\"", "description": "Inspect JSONObject pattern and base-dialect parse of JSON_ARRAY"}
[tool_result] 8:class CheckJson(Expression, Func):
9:    arg_types = {"this": True}
12:class JSONArray(Expression, Func):
13:    arg_types = {
21:class JSONArrayAgg(Expression, AggFunc):
22:    arg_types = {
31:class JSONArrayAppend(Expression, Func):
32:    arg_types = {"this": True, "expressions": True}
33:    is_var_len_args = True
37:class JSONArrayContains(Expression, Binary, Predicate, Func):
38:    arg_types = {"this": True, "expression": True, "json_type": False}
42:class JSONArrayInsert(Expression, F
…[787 chars elided]…
),
    Literal(this=3, is_string=False)])
['JSON_ARRAY(1, 2, 3)']
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False),
    Literal(this=3, is_string=False),
    Literal(this=4, is_string=False),
    Literal(this=5, is_string=False),
    Literal(this=6, is_string=False)])
ERR The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 28.
  JSON_ARRAY(1, 2, 3, 4, 5, 6[4m)[0m
[assistant] Reproduced: duckdb's `JSON_ARRAY` builds `exp.JSONArray(expressions=args)`, and `error_messages` rejects it because `JSONArray` has four `arg_types` and isn't marked variadic. The fix is to make `expressions` the variadic last key, as other variadic functions in this file do (`JSONArrayAppend`, `JSONArrayInsert`).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-184756-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n        \"expressions\": False,\n    }\n    is_var_len_args = True"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-184756-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\ns='SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)'\nprint(sqlglot.transpile(s, read='duckdb', write='duckdb'))\nprint(sqlglot.transpile(s, read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY()', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURN
…[43 chars elided]…
acle'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1,2,3,4,5,6)', read='oracle', write='oracle'))\n\"; git diff --stat; P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run the project test suite"}
[tool_result] ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
['SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))']
['SELECT JSON_ARRAY()']
['SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)']
['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
 sqlglot/expressions/json.py | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................................... [ 41%]
......................................
…[270 chars elided]…
................................................. [ 72%]
............................................. [ 76%]
............................................. [ 80%]
......................................... [ 84%]
....................................... [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1093 passed, 17868 subtests passed in 55.03s
[assistant] The full suite passes with the fix. I'll add a regression test next to the existing duckdb `JSON_ARRAY` cases.
[tool_use Bash] {"command": "sed -n 570,580p tests/dialects/test_duckdb.py", "description": "View existing duckdb JSON_ARRAY tests"}
[tool_result]                 "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT(NULL))",
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-184756-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[186 chars elided]…
()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-184756-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git -c core.pager=cat diff --stat; (ruff --version && ruff check sqlglot/expressions/json.py tests/dialects/test_duckdb.py && ruff format --check sqlglot/expressions/json.py tests/dialects/test_duckdb.py) 2>&1 | tail -3", "description": "Run full tests and lint changed files"}
[tool_result] ................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 69.66s (0:01:09)
 sqlglot/expressions/json.py   | 3 ++-
 tests/dialects/test_duckdb.py | 7 +++++++
 2 files changed, 9 insertions(+), 1 deletion(-)
ruff 0.15.6
All checks passed!
2 files already formatted
[assistant] `JSON_ARRAY` now accepts any number of values. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses for DuckDB and transpiles to Snowflake. The full suite passes (1093 tests) and ruff is clean on the changed files. I haven't committed.

**Cause:** `JSONArray` in `sqlglot/expressions/json.py` had four `arg_types` and wasn't marked variadic. DuckDB builds it as `exp.JSONArray(expressions=args)`, and `Expression.error_messages` rejected any call with more than four arguments.

**Fix:** I moved `expressions` to the last position in `arg_types` and set `is_var_len_args = True`. This matches how `JSONArrayAppend` and `JSONArrayInsert` in the same file are declared.

**Existing dialects:** Oracle, BigQuery, DuckDB and SingleStore all construct `JSONArray` with keyword arguments, so their parsing is unchanged. The one behavioural difference is positional construction through `from_arg_list`, which now maps positional values after the fixed keywords rather than onto `expressions`. Nothing in the repo or tests uses it that way.

**Test:** I added a case to `tests/dialects/test_duckdb.py` covering six arguments, round-tripped in DuckDB and transpiled to Snowflake.
