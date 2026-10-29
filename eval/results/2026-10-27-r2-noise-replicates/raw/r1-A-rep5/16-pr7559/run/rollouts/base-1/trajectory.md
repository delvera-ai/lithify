# trajectory base-1

final message:
`JSON_ARRAY` no longer rejects more than four values. The full suite passes (1093 passed), and the change is uncommitted in the worktree.

**Cause:** `Parser.validate_expression` compares the raw positional argument count with `len(arg_types)`. `JSONArray` has four keys, so DuckDB's `JSON_ARRAY(1, 2, 3, 4, 5, 6)` failed with "maximum number of supported arguments (4)". The DuckDB mapping passes `expressions=args` as a keyword, so only this check was tripping.

**Fix:** `sqlglot/expressions/json.py` — added `is_var_len_args = True` to `JSONArray`, the existing mechanism for variadic functions. The `arg_types` are unchanged.

**Parsing of existing dialects:** unchanged. The DuckDB, BigQuery, Oracle and SingleStore mappings all build `JSONArray` with keywords, so their output is the same. The Oracle and BigQuery tests, and the other dialect tests I ran, still pass.

**Test:** `tests/dialects/test_duckdb.py` — added a six-argument case with DuckDB identity and Snowflake output (`TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))`). No existing test was edited.

**Trade-off:** `JSONArray.from_arg_list` would now map positional args incorrectly, since no positional-constructor path can be right for these four keys. Nothing in the repo calls it for `JSONArray`, and the base parser doesn't register `JSON_ARRAY`, so I left it alone. Say if you'd rather I give `JSONArray` a dedicated builder.

## events
[tool_use Bash] {"command": "rtk git status --short && grep -rn \"JSONArray\\b\" sqlglot/ | head -50", "description": "Check status and find JSONArray references"}
[tool_result ERROR] Exit code 127
(eval):1: command not found: rtk
[tool_use Bash] {"command": "git status --short && grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot/ | head -60", "description": "Check status and find JSON_ARRAY references"}
[tool_result] sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._p
…[184 chars elided]…
exp.JSONArray:
sqlglot/parsers/oracle.py:114:            exp.JSONArray,
sqlglot/parsers/duckdb.py:133:        "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/typing/bigquery.py:280:            exp.JSONArray,
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/expressions/json.py && sed -n 3570,3585p sqlglot/generator.py && sed -n 105,125p sqlglot/parsers/oracle.py && sed -n 160,170p sqlglot/generators/singlestore.py && sed -n 495,510p sqlglot/generators/snowflake.py && grep -rn \"arg_types\" sqlglot/expressions/core.py | head -5; grep -n \"def _validate_arg\\|is_var_len_args\\|def validate_expression\" -A3 sqlglot/expressions/core.py | head -60", "description": "Inspect JSONArray definition and validation"}
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
        
…[5069 chars elided]…
rg, arg_key in zip(args, non_var_len_arg_keys)}
--
1945:    is_var_len_args = True
1946-
1947-    @property
1948-    def name(self) -> str:
--
1954:    is_var_len_args = True
1955-
1956-
1957-class CombinedAggFunc(AnonymousAggFunc):
--
1967:    is_var_len_args = True
1968-
1969-
1970-class Hll(Expression, AggFunc):
--
1972:    is_var_len_args = True
1973-
1974-
1975-class ApproxDistinct(Expression, AggFunc):
--
2273:    is_var_len_args = True
2274-
2275-
2276-class Pow(Expression, Binary, Func):
[tool_use Bash] {"command": "sed -n 1628,1665p sqlglot/expressions/core.py && grep -n \"class JSONObject\\b\" -A12 sqlglot/expressions/json.py && grep -rn \"JSON_ARRAY\\|JSONArray\" tests/ | head -40; P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['JSON_ARRAY(1, 2, 3, 4, 5, 6)','JSON_ARRAY(1, 2)','JSON_ARRAY(1, 2, 3, 4)']:\n    try:\n        e=sqlglot.parse_one(s); print(repr(e.args)); print(e.sql())\n    except Exception as ex: print('ERR',s,ex)\ntry:\n    print(exp.func('JSON_ARRAY',*[exp.Literal.number(i) for i in range(1,7)]).sql())\nexcept Exception as ex: print('ERR func', ex)\n\"", "description": "Read from_arg_list and test current JSON_ARRAY behavior"}
[tool_result ERROR] Exit code 1

    is_var_len_args: t.ClassVar[bool] = False
    _sql_names: t.ClassVar[list[str]] = []

    @classmethod
    def from_arg_list(cls, args: Sequence[object]) -> Self:
        if cls.is_var_len_args:
            all_arg_keys = tuple(cls.arg_types)
            # If this function supports variable length argument treat the last argument as such.
            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
            num_non_var = len(non_var_len_arg_ke
…[5552 chars elided]…
"",
tests/dialects/test_dialect.py:4838:                "": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
tests/dialects/test_dialect.py:4839:                "bigquery": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
tests/dialects/test_dialect.py:4842:                "bigquery": """JSON_ARRAY_APPEND(PARSE_JSON('["a", "b", "c"]'), '$', 1)""",
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['JSON_ARRAY(1, 2, 3, 4, 5, 6)','JSON_ARRAY(1, 2)','JSON_ARRAY(1, 2, 3, 4)']:\n    try:\n        e=sqlglot.parse_one(s); print(repr(e.args)); print(e.sql())\n    except Exception as ex: print('ERR',s,ex)\ntry:\n    print(exp.func('JSON_ARRAY',*[exp.L
…[76 chars elided]…
('ERR func', ex)\nfor d in ['duckdb','oracle','bigquery','snowflake','singlestore','mysql']:\n  try: print(d, sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read=d, write=d)[0])\n  except Exception as ex: print('ERR',d,ex)\n\"; grep -rn \"from_arg_list\\|is_var_len_args\" sqlglot/expressions/core.py | head; git log --oneline -1", "description": "Test current JSON_ARRAY parsing behavior"}
[tool_result] {'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False), Literal(this=3, is_string=False), Literal(this=4, is_string=False), Literal(this=5, is_string=False), Literal(this=6, is_string=False)]}
JSON_ARRAY(1, 2, 3, 4, 5, 6)
{'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=False)]}
JSON_ARRAY(1, 2)
{'this': 'JSON_ARRAY', 'expressions': [Literal(this=1, is_string=False), Literal(this=2, is_string=Fal
…[917 chars elided]…
 def from_arg_list(cls, args: Sequence[object]) -> Self:
sqlglot/expressions/core.py:1634:        if cls.is_var_len_args:
sqlglot/expressions/core.py:1637:            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
sqlglot/expressions/core.py:1665:        return {name: cls.from_arg_list for name in cls.sql_names()}
sqlglot/expressions/core.py:1945:    is_var_len_args = True
sqlglot/expressions/core.py:1954:    is_var_len_args = True
fa2aafb53 lithify: probe base
[tool_use Bash] {"command": "grep -rn \"maximum number of supported\" sqlglot/ | head; grep -rn \"JSON_ARRAY\\|json_array\" sqlglot/dialects/duckdb.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py 2>/dev/null; grep -rn \"def func\\b\" -A25 sqlglot/expressions/core.py | head -60", "description": "Find argument count validation source"}
[tool_result] sqlglot/expressions/core.py:1239:                f"the maximum number of supported arguments ({len(self.arg_types)})"
sqlglot/parsers/duckdb.py:133:        "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
[tool_use Bash] {"command": "sed -n 1215,1250p sqlglot/expressions/core.py; grep -n \"JSON_ARRAY\\|JSONArray\" -B2 -A8 sqlglot/generators/duckdb.py | head -30; sed -n 1,40p tests/dialects/test_duckdb.py | head -5; sed -n 550,580p tests/dialects/test_duckdb.py", "description": "Read validation code and duckdb JSON_ARRAY test"}
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
…[1539 chars elided]…
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
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot, traceback\ntry: sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb')\nexcept Exception: traceback.print_exc()\n\" 2>&1 | head -60", "description": "Get traceback for duckdb JSON_ARRAY failure"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/__init__.py", line 212, in transpile
    for expression in parse(sql, read, error_level=error_level)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/__init__.py",
…[4260 chars elided]…
.py", line 5701, in _parse_equality
    this = self._parse_comparison()
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 5713, in _parse_comparison
    this = self._parse_range()
           ^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 5723, in _parse_range
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot, traceback\ntry: sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb')\nexcept Exception: traceback.print_exc()\n\" 2>&1 | tail -30; sed -n 125,140p sqlglot/parsers/duckdb.py", "description": "Show tail of traceback and duckdb parser mapping"}
[tool_result]   File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 6012, in _parse_unary
    return self._parse_type()
           ^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 6017, in _parse_type
    if not fallback_to_identifier and (atom := self._parse_atom()) is not None:
                                   
…[2609 chars elided]…
   "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
        "LIST": exp.ArrayAgg.from_arg_list,
        "LIST_DISTINCT": exp.ArrayDistinct.from_arg_list,
        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
        "LIST_CONCAT": parser.build_array_concat,
        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
[tool_use Bash] {"command": "sed -n 6840,6885p sqlglot/parser.py; grep -n \"def validate_expression\" -A25 sqlglot/parser.py | head -40", "description": "Read parser function-call and validation code"}
[tool_result]                     # Backtrack one token since we've consumed the L_PAREN here. Instead, we'd like
                    # to parse "LIKE [ANY | ALL] (...)" as a whole into an exp.Tuple or exp.Paren
                    self._advance(-1)
                    expr = self._parse_bitwise()

                if expr:
                    return self.expression(subquery_predicate(this=expr), comments=comments)

            if functions is None:
                functions = self.FUNCTIONS

            funct
…[2057 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"^def func\" -A40 sqlglot/expressions/*.py | head -60; grep -rn \"is_var_len_args = True\" -B6 sqlglot/expressions/*.py | grep \"arg_types\" -A6 | head -60", "description": "Read exp.func and var-len precedents"}
[tool_result] sqlglot/expressions/builders.py:924:def func(
sqlglot/expressions/builders.py-925-    name: str, *args: t.Any, copy: bool = True, dialect: DialectType = None, **kwargs: t.Any
sqlglot/expressions/builders.py-926-) -> Func:
sqlglot/expressions/builders.py-927-    """
sqlglot/expressions/builders.py-928-    Returns a Func expression.
sqlglot/expressions/builders.py-929-
sqlglot/expressions/builders.py-930-    Examples:
sqlglot/expressions/builders.py-931-        >>> func("abs", 5).sql()
sqlglot/exp
…[5163 chars elided]…
ot/expressions/aggregate.py-189-class Minhash(Expression, AggFunc):
sqlglot/expressions/aggregate.py-190-    arg_types = {"this": True, "expressions": True}
sqlglot/expressions/aggregate.py:191:    is_var_len_args = True
--
sqlglot/expressions/aggregate.py-221-
sqlglot/expressions/aggregate.py-222-PERCENTILES = (PercentileCont, PercentileDisc)
sqlglot/expressions/aggregate.py-223-
sqlglot/expressions/aggregate.py-224-
--
sqlglot/expressions/aggregate.py-226-    arg_types = {"expressions": False}
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nfrom sqlglot import exp, parser, dialects\nfrom sqlglot.dialects.dialect import Dialect\nprint('base FUNCTIONS JSON_ARRAY:', parser.Parser.FUNCTIONS.get('JSON_ARRAY'))\nfor n in ['duckdb','bigquery','oracle','singlestore','snowflake','mysql','postgres']:\n    print(n, Dialect.get_or_raise(n).parser_class.FUNCTIONS.get('JSON_ARRAY'))\nprint(type(exp.func('JSON_ARRAY', 1,2,3,4,5,6)))\nprint(repr(exp.func('JSON_ARRAY', 1,2)))\n\"; grep -n \"JSON_ARRAY\\|JSON_BUILD_ARRAY\" -r sqlglot/parsers/*.py sqlglot/parser.py | head", "description": "Check which dialects map JSON_ARRAY to JSONArray"}
[tool_result] base FUNCTIONS JSON_ARRAY: None
duckdb <function DuckDBParser.<lambda> at 0x103c068e0>
bigquery None
oracle None
singlestore None
snowflake None
mysql None
postgres None
<class 'sqlglot.expressions.core.Anonymous'>
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False)])
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/duckdb.py:133:        "JSON_ARRAY": lambda args: exp.JSONArray
…[233 chars elided]…
rs/singlestore.py:87:        "JSON_ARRAY_CONTAINS_STRING": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:92:        "JSON_ARRAY_CONTAINS_DOUBLE": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:97:        "JSON_ARRAY_CONTAINS_JSON": lambda args: exp.JSONArrayContains(
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/tsql.py:411:        "JSON_ARRAYAGG": lambda self: self.expression(
[assistant] The failure is in `Parser.validate_expression`: it compares the raw positional argument count against `len(arg_types)`, which is 4 for `JSONArray`. DuckDB's `JSON_ARRAY` mapping passes `expressions=args` as a keyword, so the only thing that trips is that check. Setting `is_var_len_args` on `JSONArray` is the existing mechanism for this, and it leaves the keyword-based parsing untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n    is_var_len_args = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[assistant] Now a regression test next to the existing DuckDB `JSON_ARRAY` tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[182 chars elided]…
AY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095953-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='duckdb'))\nprint(exp.JSONArray(expressions=[exp.Literal.number(i) for i in range(6)]).sql())\n\" && $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_oracle.py tests/dialects/test_bigquery.py tests/dialects/test_singlestore.py 2>&1 | tail -5", "description": "Verify fix and run affected dialect tests"}
[tool_result] ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
JSON_ARRAY(0, 1, 2, 3, 4, 5)
........................ [ 15%]
................................................................................................................................  [100%]
152 passed, 2079 subtests passed in 0.61s
[assistant] Affected dialect tests pass. Now the full suite, the project's check command from CLAUDE.md.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short; git diff --stat", "description": "Run full test suite and show diff stats"}
[tool_result] ................................................................................................. [ 51%]
......................................................... [ 57%]
................................................................................................................................................................... [ 72%]
............................................. [ 76%]
............................................. [ 80%]
................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 51.26s
 M sqlglot/expressions/json.py
 M tests/dialects/test_duckdb.py
 sqlglot/expressions/json.py   | 1 +
 tests/dialects/test_duckdb.py | 7 +++++++
 2 files changed, 8 insertions(+)
[assistant] `JSON_ARRAY` no longer rejects more than four values. The full suite passes (1093 passed), and the change is uncommitted in the worktree.

**Cause:** `Parser.validate_expression` compares the raw positional argument count with `len(arg_types)`. `JSONArray` has four keys, so DuckDB's `JSON_ARRAY(1, 2, 3, 4, 5, 6)` failed with "maximum number of supported arguments (4)". The DuckDB mapping passes `expressions=args` as a keyword, so only this check was tripping.

**Fix:** `sqlglot/expressions/json.py` — added `is_var_len_args = True` to `JSONArray`, the existing mechanism for variadic functions. 
…[200 chars elided]…
 Oracle and BigQuery tests, and the other dialect tests I ran, still pass.

**Test:** `tests/dialects/test_duckdb.py` — added a six-argument case with DuckDB identity and Snowflake output (`TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))`). No existing test was edited.

**Trade-off:** `JSONArray.from_arg_list` would now map positional args incorrectly, since no positional-constructor path can be right for these four keys. Nothing in the repo calls it for `JSONArray`, and the base parser doesn't register `JSON_ARRAY`, so I left it alone. Say if you'd rather I give `JSONArray` a dedicated builder.
