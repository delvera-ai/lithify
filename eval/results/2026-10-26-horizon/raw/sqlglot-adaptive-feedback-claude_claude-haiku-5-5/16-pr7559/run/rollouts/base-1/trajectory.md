# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of arguments. The full suite passes after the last edit: `SUMMARY: 1093 passed, 17870 subtests passed in 60.94s`, `EXIT: 0`.

**Cause:** `sqlglot/expressions/json.py` declared `JSONArray` without `is_var_len_args`. The parser's argument-count check then compared the call's arguments against the four `arg_types` keys. DuckDB builds this node through an explicit lambda, so `JSON_ARRAY(1, 2, 3, 4, 5, 6)` raised `ParseError`. BigQuery and Oracle already accepted it because they build the node differently.

**Change:**
- `sqlglot/expressions/json.py`: set `is_var_len_args = True` on `JSONArray` and moved `expressions` to the last key of `arg_types`. That order is what the flag's contract expects (the last key is the variadic list). Nothing observable depends on the order, because no dialect uses the default `from_arg_list` for this class.
- `tests/dialects/test_duckdb.py`: added a `validate_all` case for a 6-argument `JSON_ARRAY`, with the DuckDB and Snowflake outputs.

**Checks:**
- Before and after, I compared the parse result of `JSON_ARRAY` with 0–6 arguments, with and without `NULL ON NULL` / `RETURNING ... STRICT`, across about 18 dialects. The only difference is DuckDB 6-argument calls, which went from `ParseError` to a `JSONArray` with 6 expressions.
- BigQuery, Oracle and the other dialects produce the same output as before.

I did not commit. Two things I did not change: the base dialect still parses `JSON_ARRAY` as `Anonymous`, and `JSON_ARRAY ... NULL ON NULL` still fails in the base dialect. Both were already like that and are outside this task.

## events
[tool_use Bash] {"command": "grep -rn \"JSONArray\\b\\|JSON_ARRAY\\b\" sqlglot/ | grep -v \"JSON_ARRAY_\" | head -50; grep -rn \"class JSONArray\\b\" -A 12 sqlglot/expressions/", "description": "Locate JSONArray expression and usages"}
[tool_result] sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/generator.py:3580:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._p
…[870 chars elided]…
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201252-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "limit": 40}
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
[tool_use Bash] {"command": "sed -n 3570,3585p sqlglot/generator.py && grep -n \"JSON_ARRAY\\|JSONArray\" tests/dialects/*.py | head -30 && cat .lithify/harness/memory.md 2>/dev/null | head -20; ls .lithify/harness/ 2>/dev/null", "description": "Show generator method and existing tests for JSON_ARRAY"}
[tool_result]             suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
        )

    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
        null_handling = expression.args.get("null_handling")
        null_handling = f" {null_handling}" if null_handling else ""
        return_type = self.sql(expression, "return_type")
        return_type = f" RETURNING {return_type}" if return_type else ""
        strict = " STRICT" if expression.args.get("strict") else ""
        return self.f
…[4080 chars elided]…
erator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 tests) takes 60–80 s when it runs alone. The slowest test is
  `tests/test_executor.py::TestExecutor::test_execute_tpcds`; with several pytest runs competing
  for CPU it sits there for minutes and looks hung, but it is only slow. Run the dialect's own
  test file first (well under a second), then the full suite once.
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The expression declares no `is_var_len_args`, so `from_arg_list` maps positional args onto the four named keys. Let me reproduce before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.func('JSON_ARRAY', *[exp.Literal.number(i) for i in range(1,7)])))\ntry:\n    e = exp.JSONArray(expressions=[exp.Literal.number(i) for i in range(1,7)])\n    print(
…[104 chars elided]…
bigquery', 'singlestore', 'oracle', 'snowflake']:\n    try: print(d, sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read=d or None, write=d or None))\n    except Exception as ex: print(d, 'ERR', ex)\n\"; grep -n \"is_var_len_args\" sqlglot/expressions/core.py | head; grep -rn \"is_var_len_args = True\" sqlglot/expressions/ | head -3", "description": "Reproduce JSON_ARRAY argument limit"}
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
[]
 ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
duckdb ERR The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 35.
  SELECT JSON_ARRAY(1, 2
…[420 chars elided]…
   is_var_len_args: t.ClassVar[bool] = False
1634:        if cls.is_var_len_args:
1637:            non_var_len_arg_keys = all_arg_keys[:-1] if cls.is_var_len_args else all_arg_keys
1945:    is_var_len_args = True
1954:    is_var_len_args = True
1967:    is_var_len_args = True
1972:    is_var_len_args = True
sqlglot/expressions/functions.py:124:    is_var_len_args = True
sqlglot/expressions/functions.py:130:    is_var_len_args = True
sqlglot/expressions/functions.py:139:    is_var_len_args = True
[assistant] Reproduced: DuckDB's `FUNCTIONS` entry (`lambda args: exp.JSONArray(expressions=args)`) goes through the generic path and rejects 6 args. Let me check how `is_var_len_args` interacts with `arg_types` ordering before choosing a fix.
[tool_use Bash] {"command": "sed -n 1615,1690p sqlglot/expressions/core.py; sed -n 1225,1240p sqlglot/expressions/core.py", "description": "Read var-len args handling in core expressions"}
[tool_result] @trait
class Func(Condition):
    """
    The base class for all function expressions.

    Attributes:
        is_var_len_args (bool): if set to True the last argument defined in arg_types will be
            treated as a variable length argument and the argument's value will be stored as a list.
        _sql_names (list): the SQL name (1st item in the list) and aliases (subsequent items) for this
            function expression. These values are used to map this node to a name during parsing a
…[2242 chars elided]…
ppend(f"Required keyword: '{k}' missing for {self.__class__}")

        if (
            args
            and isinstance(self, Func)
            and len(args) > len(self.arg_types)
            and not self.is_var_len_args
        ):
            if errors is None:
                errors = []
            errors.append(
                f"The number of provided arguments ({len(args)}) is greater than "
                f"the maximum number of supported arguments ({len(self.arg_types)})"
            )
[assistant] The var-len mechanism treats the *last* `arg_types` key as the list, and `expressions` is currently first. Before picking a fix, I need the current AST for each dialect's parse path, since the default `from_arg_list` positional mapping may already be mis-assigning args in the base dialect.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_ja.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nsqls = [\"JSON_ARRAY()\", \"JSON_ARRAY(1)\", \"JSON_ARRAY(1, 2)\", \"JSON_ARRAY(1, 2, 3, 4)\", \"JSON_ARRAY(1, 2, 3, 4, 5, 6)\", \"JSON_ARRAY(1, 2, 3, 4, 5, 6
…[718 chars elided]…
name__ + \":\" + e.selects[0].sql_name() if hasattr(e.selects[0], 'sql_name') else type(e.selects[0]).__name__\n        except Exception as ex:\n            out = \"ERR \" + type(ex).__name__\n        print(f\"{s!r:50} {str(d):12} {out}\")\nEOF\n$PY -I /tmp/probe_ja.py > /tmp/before.txt 2>&1; cat /tmp/before.txt | head -150", "description": "Snapshot current JSON_ARRAY parse ASTs across dialects"}
[tool_result] Traceback (most recent call last):
  File "/tmp/probe_ja.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/probe_ja.py > /tmp/before.txt 2>&1; wc -l /tmp/before.txt; head -130 /tmp/before.txt", "description": "Snapshot current JSON_ARRAY parse ASTs across dialects"}
[tool_result]      126 /tmp/before.txt
'JSON_ARRAY()'                                     None         Anonymous:ANONYMOUS
'JSON_ARRAY()'                                     duckdb       JSONArray(exprs=0, nh=None, rt=None, strict=None)
'JSON_ARRAY()'                                     bigquery     JSONArray(exprs=0, nh=None, rt=None, strict=None)
'JSON_ARRAY()'                                     snowflake    Anonymous:ANONYMOUS
'JSON_ARRAY()'                                     mysql        Anonymous:ANONY
…[9853 chars elided]…
eradata     ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     presto       ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     sqlite       ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     redshift     ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     databricks   ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     hive         ERR ParseError
'JSON_ARRAY(1, 2, 3) RETURNING VARCHAR STRICT'     trino        ERR ParseError
[assistant] Useful baseline. Key findings:
- The base dialect never builds `JSONArray` (it stays `Anonymous`), so the default `from_arg_list` path only matters via `exp.func(...)` / the expression builder.
- DuckDB rejects 6 args; BigQuery and Oracle accept them. Existing dialect outputs must stay identical.

Next I need to see what the validator counts, and whether `from_arg_list` is overridden anywhere, to choose between reordering `arg_types` and overriding the builder.
[tool_use Bash] {"command": "sed -n 1200,1224p sqlglot/expressions/core.py; grep -rn \"def from_arg_list\" sqlglot/ ; grep -rn \"from_arg_list\" sqlglot/ | grep -v \"def from_arg_list\" | head", "description": "Inspect validator and from_arg_list overrides"}
[tool_result]         if not isinstance(self, type_):
            raise AssertionError(f"{self} is not {type_}.")
        return self

    def error_messages(self, args: Sequence[object] | None = None) -> list[str]:
        """
        Checks if this expression is valid (e.g. all mandatory args are set).

        Args:
            args: a sequence of values that were used to instantiate a Func expression. This is used
                to check that the provided arguments don't exceed the function argument limi
…[879 chars elided]…
,
sqlglot/parsers/dremio.py:100:        "ARRAY_GENERATE_RANGE": exp.GenerateSeries.from_arg_list,
sqlglot/parsers/dremio.py:101:        "BIT_AND": exp.BitwiseAndAgg.from_arg_list,
sqlglot/parsers/dremio.py:102:        "BIT_OR": exp.BitwiseOrAgg.from_arg_list,
sqlglot/parsers/dremio.py:106:        "REGEXP_MATCHES": exp.RegexpLike.from_arg_list,
sqlglot/parsers/dremio.py:107:        "REPEATSTR": exp.Repeat.from_arg_list,
sqlglot/parsers/dremio.py:110:        "DATE_PART": exp.Extract.from_arg_list,
[assistant] The validator's count check runs on the positional args the parser hands it, and it skips only when `is_var_len_args` is set. Setting that flag alone is not enough, because `from_arg_list` would then treat the last key (`strict`) as the variadic list. Let me check how `exp.func` builds calls, since that decides whether the builder mapping needs its own fix.
[tool_use Bash] {"command": "grep -n \"^def func\" -A 40 sqlglot/expressions/builders.py sqlglot/expressions/*.py 2>/dev/null | grep -n \"from_arg_list\\|def func\\|validate\\|except\\|Anonymous\\|return\" | head -20", "description": "Check exp.func builder path"}
[tool_result] 1:sqlglot/expressions/builders.py:924:def func(
42:sqlglot/expressions/builders.py:924:def func(
[tool_use Bash] {"command": "sed -n 924,990p sqlglot/expressions/builders.py | grep -v '^\\s*$' | head -70", "description": "Read exp.func implementation"}
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
   
…[1367 chars elided]…
= constructor(**kwargs)
            else:
                raise ValueError(
                    f"Unable to convert '{name}' into a Func. Either manually construct "
                    "the Func expression of interest or parse the function call."
                )
    else:
        kwargs = kwargs or {"expressions": converted}
        function = Anonymous(this=name, **kwargs)
    for error_message in function.error_messages(converted):
        raise ValueError(error_message)
    return function
[assistant] `exp.func` resolves through `parser_class.FUNCTIONS`, and every dialect that has `JSON_ARRAY` maps it to an explicit lambda (`exp.JSONArray(expressions=args)`). So the limit comes only from the validator's count check, and `is_var_len_args = True` removes it. I'll also move `expressions` to the last key so the flag's documented contract ("last argument is the variadic list") is true. No dialect uses the default `from_arg_list` for this class, so the reorder is not observable in parsing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201252-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n        \"expressions\": False,\n    }\n    is_var_len_args = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201252-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/probe_ja.py > /tmp/after.txt 2>&1; diff /tmp/before.txt /tmp/after.txt; echo \"---\"; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['duckdb','bigquery','oracle','singlestore'
…[205 chars elided]…
', [e.name for e in j.expressions], 'errors', j.error_messages())\nprint(exp.func('JSON_ARRAY', 1,2,3,4,5,6, dialect='duckdb').sql('duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='oracle', write='duckdb'))\n\"", "description": "Re-run AST probe and verify 6-arg cases"}
[tool_result ERROR] Exit code 1
74c74
< 'JSON_ARRAY(1, 2, 3, 4, 5, 6)'                     duckdb       ERR ParseError
---
> 'JSON_ARRAY(1, 2, 3, 4, 5, 6)'                     duckdb       JSONArray(exprs=6, nh=None, rt=None, strict=None)
---
Traceback (most recent call last):
  File "<string>", line 7, in <module>
AttributeError: 'NoneType' object has no attribute 'expressions'
duckdb ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
  exprs ['1', '2', '3', '4', '5', '6'] errors []
bigquery ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
  exprs ['1', '2', '3', '4', '5', '6'] errors []
oracle ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
  exprs ['1', '2', '3', '4', '5', '6'] errors []
singlestore ['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
[assistant] The only AST diff is the intended one: DuckDB now yields a 6-element `JSONArray` instead of a ParseError. The exception at the end is from my probe script (singlestore leaves `JSON_ARRAY` as `Anonymous`, same as before), not from the change. Let me verify the remaining paths and look at the existing DuckDB tests to add one next to them.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(exp.func('JSON_ARRAY', 1,2,3,4,5,6, dialect='duckdb').sql('duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='oracle', write='duckdb'))\nprint(sqlglot.transpile('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='bigquery', write='duckdb'))\n\"; sed -n 548,580p tests/dialects/test_duckdb.py", "description": "Verify builder and cross-dialect output; view DuckDB tests"}
[tool_result] JSON_ARRAY(1, 2, 3, 4, 5, 6)
['SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))']
['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
['SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)']
        self.validate_identity(
            """SELECT JSON_EXTRACT_STRING('{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }', ['$.family', '$.species'])""",
            """SELECT '{ "family": "anatidae", "species": [ "duck", "goose", "swan", null ] }' ->> ['$.family', '$.species']""",
        )
        self.val
…[502 chars elided]…
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
[assistant] The existing DuckDB tests cover 0–3 args through `validate_all`. I'll add a 6-arg case alongside them, matching that style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201252-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_identity(", "new_string": "                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201252-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the dialect file first (fast), then the full suite once, as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_bigquery.py tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Run DuckDB, BigQuery, Oracle dialect test files"}
[tool_result] ........................ [ 19%]
.............................................................................................. [ 93%]
........                             [100%]
126 passed, 1862 subtests passed in 0.54s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-00:42:49 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-acace42ebf.log
ELAPSED: 61s
SUMMARY: 1093 passed, 17870 subtests passed in 60.94s (0:01:00)
EXIT: 0
[assistant] `JSON_ARRAY` now accepts any number of arguments. The full suite passes after the last edit: `SUMMARY: 1093 passed, 17870 subtests passed in 60.94s`, `EXIT: 0`.

**Cause:** `sqlglot/expressions/json.py` declared `JSONArray` without `is_var_len_args`. The parser's argument-count check then compared the call's arguments against the four `arg_types` keys. DuckDB builds this node through an explicit lambda, so `JSON_ARRAY(1, 2, 3, 4, 5, 6)` raised `ParseError`. BigQuery and Oracle already accepted it because they build the node differently.

**Change:**
- `sqlglot/expressions/json.py`: set `is_var
…[415 chars elided]…

**Checks:**
- Before and after, I compared the parse result of `JSON_ARRAY` with 0–6 arguments, with and without `NULL ON NULL` / `RETURNING ... STRICT`, across about 18 dialects. The only difference is DuckDB 6-argument calls, which went from `ParseError` to a `JSONArray` with 6 expressions.
- BigQuery, Oracle and the other dialects produce the same output as before.

I did not commit. Two things I did not change: the base dialect still parses `JSON_ARRAY` as `Anonymous`, and `JSON_ARRAY ... NULL ON NULL` still fails in the base dialect. Both were already like that and are outside this task.
