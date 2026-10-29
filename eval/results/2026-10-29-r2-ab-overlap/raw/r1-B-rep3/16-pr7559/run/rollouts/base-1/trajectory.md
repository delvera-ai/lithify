# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of arguments. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses and round-trips in duckdb, bigquery, oracle, singlestore and mysql, and the full suite passes (1093 passed).

**The change:** `sqlglot/expressions/json.py` adds `is_var_len_args = True` to `JSONArray`. The argument-count check in `Expression.error_messages` skips the four-key limit when that flag is set. Before the fix, duckdb raised `The number of provided arguments (6) is greater than the maximum number of supported arguments (4)`.

**Existing dialects are unchanged:** every dialect builds `JSONArray(expressions=...)` directly, and the base parser never maps `JSON_ARRAY` to `JSONArray` (it stays `Anonymous`), so only the validation path changed.

**Test:** I added a six-argument case to `test_duckdb.py`, next to the existing `JSON_ARRAY` cases, checking duckdb and snowflake output. I did not commit.

**Left alone:** `JSONArray.from_arg_list` still maps positional arguments onto the flag keys, so `exp.JSONArray.from_arg_list` with more than three arguments is wrong. Nothing on the parse path calls it for `JSON_ARRAY`, so I didn't touch it. Say if you want it fixed too.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn \"JSONArray\\b\\|JSON_ARRAY\\\"\" sqlglot/ | head -50", "description": "Locate JSONArray references in sqlglot"}
[tool_result] oksqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._parse_bitwise))
sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parse
…[186 chars elided]…
xp.JSONArray,
sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "limit": 40}
[tool_result] 1	"""sqlglot expressions - JSON functions."""
2	
3	from __future__ import annotations
4	
5	from sqlglot.expressions.core import Expression, Func, AggFunc, Binary, Predicate
6	
7	
8	class CheckJson(Expression, Func):
9	    arg_types = {"this": True}
10	
11	
12	class JSONArray(Expression, Func):
13	    arg_types = {
14	        "expressions": False,
15	        "null_handling": False,
16	        "return_type": False,
17	        "strict": False,
18	    }
19	
20	
21	class JSONArrayAgg(Expression, AggF
…[57 chars elided]…
      "order": False,
25	        "null_handling": False,
26	        "return_type": False,
27	        "strict": False,
28	    }
29	
30	
31	class JSONArrayAppend(Expression, Func):
32	    arg_types = {"this": True, "expressions": True}
33	    is_var_len_args = True
34	    _sql_names = ["JSON_ARRAY_APPEND"]
35	
36	
37	class JSONArrayContains(Expression, Binary, Predicate, Func):
38	    arg_types = {"this": True, "expression": True, "json_type": False}
39	    _sql_names = ["JSON_ARRAY_CONTAINS"]
40	
[tool_use Bash] {"command": "grep -rn \"_parse_oracle_json_array\" -A12 sqlglot/parsers/oracle.py | sed -n '1,30p'; grep -rn \"JSON_ARRAY\\|JSONArray\" tests/ | head -30", "description": "Inspect JSONArray definition, Oracle parser, and tests"}
[tool_result] sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:57:        "JSON_ARRAYAGG": lambda self: self._parse_oracle_json_arrayagg(),
sqlglot/parsers/oracle.py-58-        "JSON_EXISTS": lambda self: self._parse_json_exists(),
sqlglot/parsers/oracle.py-59-    }
sqlglot/parsers/oracle.py-60-
sqlglot/parsers/oracle.py-61-    PROPERTY_PARSERS = {
sqlglot/parsers/oracle.py-62-        **parser.Parser.PROPERTY_PARSERS,
sqlglot/parsers/or
…[4431 chars elided]…
ON_ARRAY()",
tests/dialects/test_dialect.py:4836:            """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
tests/dialects/test_dialect.py:4838:                "": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
tests/dialects/test_dialect.py:4839:                "bigquery": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
tests/dialects/test_dialect.py:4842:                "bigquery": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
[tool_use Bash] {"command": "grep -n \"is_var_len_args\" -B3 -A12 sqlglot/expressions/core.py | head -80; grep -rn \"is_var_len_args = True\" sqlglot/expressions/ | head -5; grep -n \"def jsonarray_sql\" -A10 sqlglot/generator.py", "description": "Check how var-len args are mapped in Func"}
[tool_result] 84-    key: t.ClassVar[str] = "expression"
85-    arg_types: t.ClassVar[dict[str, bool]] = {"this": True}
86-    required_args: t.ClassVar[set[str]] = {"this"}
87:    is_var_len_args: t.ClassVar[bool] = False
88-    _hash_raw_args: t.ClassVar[bool] = False
89-    is_subquery: t.ClassVar[bool] = False
90-    is_cast: t.ClassVar[bool] = False
91-
92-    args: dict[str, t.Any]
93-    parent: Expr | None
94-    arg_key: str | None
95-    index: int | None
96-    comments: list[str] | None
97-    _ty
…[3219 chars elided]…
_handling = f" {null_handling}" if null_handling else ""
3576-        return_type = self.sql(expression, "return_type")
3577-        return_type = f" RETURNING {return_type}" if return_type else ""
3578-        strict = " STRICT" if expression.args.get("strict") else ""
3579-        return self.func(
3580-            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
3581-        )
3582-
3583-    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['', 'duckdb', 'mysql', 'bigquery', 'oracle', 'snowflake']:\n    for q in ['JSON_ARRAY(1, 2, 3, 4, 5, 6)', 'JSON_ARRAY(1, 2)']:\n        try:\n            print(d, q, '->', sqlglot.transpile(q, read=d, write=d, unsupported_level=sqlglot.ErrorLevel.IGNORE)[0])\n        except Exception as e: print(d, q, 'ERR', type(e).__name__, str(e)[:200])\nprint(repr(exp.func('JSON_ARRAY', *range(6))))\n\" 2>&1 | head -60", "description": "Reproduce JSON_ARRAY failure across dialects"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['', 'duckdb', 'mysql', 'bigquery', 'oracle', 'snowflake']:\n    for q in ['JSON_ARRAY(1, 2, 3, 4, 5, 6)', 'JSON_ARRAY(1, 2)']:\n        try:\n            print(d, q, '->', sqlglot.transpile(q, read=d, write=d)[0])\n        except Exception as e: print(d, q, 'ERR', type(e).__name__, str(e)[:200])\nprint(repr(exp.func('JSON_ARRAY', *range(6))))\n\" 2>&1 | head -60", "description": "Reproduce JSON_ARRAY failure across dialects"}
[tool_result]  JSON_ARRAY(1, 2, 3, 4, 5, 6) -> JSON_ARRAY(1, 2, 3, 4, 5, 6)
 JSON_ARRAY(1, 2) -> JSON_ARRAY(1, 2)
duckdb JSON_ARRAY(1, 2, 3, 4, 5, 6) ERR ParseError The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 28.
  JSON_ARRAY(1, 2, 3, 4, 5, 6[4m)[0m
duckdb JSON_ARRAY(1, 2) -> JSON_ARRAY(1, 2)
mysql JSON_ARRAY(1, 2, 3, 4, 5, 6) -> JSON_ARRAY(1, 2, 3, 4, 5, 6)
mysql JSON_ARRAY(1, 2) -> JSON_ARRAY(1, 2)
bigquery JSON_ARRAY(1, 2, 3, 4, 5, 6) -
…[81 chars elided]…
le JSON_ARRAY(1, 2, 3, 4, 5, 6) -> JSON_ARRAY(1, 2, 3, 4, 5, 6)
oracle JSON_ARRAY(1, 2) -> JSON_ARRAY(1, 2)
snowflake JSON_ARRAY(1, 2, 3, 4, 5, 6) -> JSON_ARRAY(1, 2, 3, 4, 5, 6)
snowflake JSON_ARRAY(1, 2) -> JSON_ARRAY(1, 2)
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=0, is_string=False),
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False),
    Literal(this=3, is_string=False),
    Literal(this=4, is_string=False),
    Literal(this=5, is_string=False)])
[tool_use Bash] {"command": "sed -n 1215,1234p sqlglot/expressions/core.py; grep -rn \"is_var_len_args\" sqlglot/expressions/functions.py | head -3; sed -n 120,132p sqlglot/expressions/functions.py", "description": "Read argument validation logic"}
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
…[173 chars elided]…
     ):
sqlglot/expressions/functions.py:124:    is_var_len_args = True
sqlglot/expressions/functions.py:130:    is_var_len_args = True
sqlglot/expressions/functions.py:139:    is_var_len_args = True


class Coalesce(Expression, Func):
    arg_types = {"this": True, "expressions": False, "is_nvl": False, "is_null": False}
    is_var_len_args = True
    _sql_names = ["COALESCE", "IFNULL", "NVL"]


class DecodeCase(Expression, Func):
    arg_types = {"expressions": True}
    is_var_len_args = True
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(exp.JSONArray.sql_names())\nprint(repr(exp.JSONArray.from_arg_list([exp.Literal.number(i) for i in range(6)])))\ntry: print(exp.JSONArray(expressions=[exp.Literal.number(i) for i in range(6)]).error_messages())\nexcept Exception as e: print('ERR', e)\nprint(exp.func('JSON_ARRAY', 1,2).__class__)\n\" 2>&1 | head -30; grep -n \"def func\" -A30 sqlglot/expressions/functions.py | grep -n \"ALL_FUNCTIONS\\|sql_names\\|Anonymous\" ; grep -rn \"def func(\" sqlglot/expressions/*.py", "description": "Probe JSONArray construction and func lookup"}
[tool_result] ['J_S_O_N_ARRAY']
JSONArray(
  expressions=Literal(this=0, is_string=False),
  null_handling=Literal(this=1, is_string=False),
  return_type=Literal(this=2, is_string=False),
  strict=Literal(this=3, is_string=False))
[]
<class 'sqlglot.expressions.core.Anonymous'>
sqlglot/expressions/builders.py:924:def func(
[assistant] Root cause: `JSONArray` lacks `is_var_len_args`, so the argument-count check in `Expression.error_messages` rejects anything past the four declared keys. Dialect lambdas (duckdb, singlestore, bigquery, oracle) all build `JSONArray(expressions=...)` directly, so adding the flag only affects the validation path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n    is_var_len_args = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "offset": 548, "limit": 32}
[tool_result] 548	        self.validate_identity(
549	            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
550	            """SELECT '{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }' ->> ['$.family', '$.species']""",
551	        )
552	        self.validate_all(
553	            "SELECT JSON_ARRAY('a', 'b', 'c')",
554	            write={
555	                "duckdb": "SELECT JSON_ARRAY('a', 'b', 
…[432 chars elided]…
validate_all(
567	            "SELECT JSON_ARRAY(NULL)",
568	            write={
569	                "duckdb": "SELECT JSON_ARRAY(NULL)",
570	                "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT(NULL))",
571	            },
572	        )
573	        self.validate_all(
574	            "SELECT JSON_ARRAY()",
575	            write={
576	                "duckdb": "SELECT JSON_ARRAY()",
577	                "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT())",
578	            },
579	        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[182 chars elided]…
AY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-181610-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll run the targeted tests, then the full suite with the project's command.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['duckdb','bigquery','oracle','singlestore','mysql']:\n    print(d, sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read=d, write=d)[0])\nprint(exp.JSONArray(expressions=[exp.Literal.number(i) for i in range(6)]).error_messages())\n\" 2>&1; git stash list | head -0; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_oracle.py tests/dialects/test_bigquery.py tests/dialects/test_singlestore.py tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Verify fix and run dialect tests"}
[tool_result] duckdb SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
bigquery SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
oracle SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
singlestore SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
mysql SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
[]
head: illegal line count -- 0

thread 'main' (43933562) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
........................ [  9%]
............................................................................................................................................................................................................................. [ 99%]
..                                                                  [100%]
247 passed, 3648 subtests passed in 1.19s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full project test suite"}
[tool_result] ................................................................................................. [ 51%]
......................................................... [ 57%]
................................................................................................................................................................... [ 72%]
............................................. [ 76%]
............................................. [ 80%]
................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 51.20s
[assistant] `JSON_ARRAY` now accepts any number of arguments. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses and round-trips in duckdb, bigquery, oracle, singlestore and mysql, and the full suite passes (1093 passed).

**The change:** `sqlglot/expressions/json.py` adds `is_var_len_args = True` to `JSONArray`. The argument-count check in `Expression.error_messages` skips the four-key limit when that flag is set. Before the fix, duckdb raised `The number of provided arguments (6) is greater than the maximum number of supported arguments (4)`.

**Existing dialects are unchanged:** every dialect builds `JSONArray(expressions=...)` directly, and the base parser never maps `JSON_ARRAY` to `JSONArray` (it stays `Anonymous`), so only the validation path changed.

**Test:** I added a six-argument case to `test_duckdb.py`, next to the existing `JSON_ARRAY` cases, checking duckdb and snowflake output. I did not commit.

**Left alone:** `JSONArray.from_arg_list` still maps positional arguments onto the flag keys, so `exp.JSONArray.from_arg_list` with more than three arguments is wrong. Nothing on the parse path calls it for `JSON_ARRAY`, so I didn't touch it. Say if you want it fixed too.
