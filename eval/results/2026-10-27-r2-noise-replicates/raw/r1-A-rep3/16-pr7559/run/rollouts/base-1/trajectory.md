# trajectory base-1

final message:
`JSON_ARRAY` now accepts any number of values. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses and round-trips in DuckDB, which was the only dialect that rejected it.

**Cause:** `JSONArray` declared four argument slots and wasn't marked variadic, so argument validation rejected anything beyond four. DuckDB was the one dialect that routes `JSON_ARRAY` through that validated path. The other dialects either map it to an untyped function or build it some other way.

**Change** (`sqlglot/expressions/json.py`):
- `JSONArray` is now `is_var_len_args = True`, which skips the arity check.
- It overrides `from_arg_list` to put every positional value into `expressions`. Without this, the variadic flag would send the overflow into `strict`.

**Existing dialects:** I captured how every dialect parses `JSON_ARRAY` with 0–6 arguments before and after the change. Only the two DuckDB rows (5 and 6 arguments) differ, going from a parse error to correct output. Everything else is byte-identical.

**Test:** added a 6-argument case to `tests/dialects/test_duckdb.py`, next to the existing `JSON_ARRAY` cases. No existing test was modified.

**Checks:** the full suite passes (1093 tests, 17870 subtests) and ruff check and format are clean on both files.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo asks for.

## events
[tool_use Bash] {"command": "rtk grep -n \"class JSONArray\\b\" -A 12 sqlglot/expressions.py; rtk grep -rn \"JSONArray\\b\" sqlglot/ | head -50", "description": "Locate JSONArray expression and usages"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"class JSONArray\\b\" -A 12 sqlglot/expressions.py; grep -rn \"JSONArray\\b\" sqlglot/ | head -50", "description": "Locate JSONArray expression and usages"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3573:    def jsonarray_sql(self, expression: exp.JSONArray) -> str:
sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._parse_bitwise))
sqlglot/parsers/duckdb.py:133:        "JSON_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers/oracle.py:114:            exp.JSONArray,
sqlglot/typing/bigquery.py:280:            exp.JSONArray,
sqlglot/expressions/json.py:12:class JSONArray(Expression, Func):
sqlglot/generators/singlestore.py:165:        exp.JSONArray: unsupported_args("null_handling", "return_type", "strict")(
sqlglot/generators/snowflake.py:500:        exp.JSONArray: lambda self, e: self.func(
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/expressions/json.py; grep -n \"JSON_ARRAY\\|JSONArray\" -B2 -A8 sqlglot/parsers/*.py sqlglot/parser.py | head -150; sed -n 3565,3595p sqlglot/generator.py; sed -n 495,510p sqlglot/generators/snowflake.py; sed -n 105,120p sqlglot/parsers/oracle.py", "description": "Read JSONArray definition and parsers"}
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
        
…[13218 chars elided]…
, upper = lower_upper

            return exp.Rand(lower=lower, upper=upper)

        self._retreat(self._index - 1)
        return None

    def _parse_oracle_json_array(self) -> exp.JSONArray:
        return self._parse_json_array(
            exp.JSONArray,
            expressions=self._parse_csv(lambda: self._parse_format_json(self._parse_bitwise())),
        )

    def _parse_oracle_json_arrayagg(self) -> exp.JSONArrayAgg:
        return self._parse_json_array(
            exp.JSONArrayAgg,
[assistant] Reproducing the failure with the project's Python first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(exp.JSONArray(expressions=[exp.column(c) for c in 'abcdef']).sql())\n\" 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nprint(exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef']).sql())\nprint(exp.JSONArray.from_arg_list([exp.column(c) for c in 'abcdef']).sql())\n\" 2>&1 | tail -5; grep -n \"is_var_len_args\" sqlglot/expressions/core.py | head; grep -n \"def from_arg_list\" -A 20 sqlglot/expressions/core.py | head -40", "description": "Reproduce JSON_ARRAY argument limit failure"}
[tool_result] JSON_ARRAY(a, b, c, d, e, f)
           ^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/sqlglot/expressions/core.py", line 1394, in __iter__
    raise TypeError(f"'{self.__class__.__name__}' object is not iterable")
TypeError: 'Column' object is not iterable
JSON_ARRAY(a, b, c, d, e, f)
87:    is_var_len_args: t.ClassVar[bool] = False
1233:            and not self.is_var_len_args
1621:        is_var_len_args (bool): i
…[893 chars elided]…
641-            args_dict[all_arg_keys[-1]] = args[num_non_var:]
1642-        else:
1643-            args_dict = {arg_key: arg for arg, arg_key in zip(args, cls.arg_types)}
1644-
1645-        return cls(**args_dict)
1646-
1647-    @classmethod
1648-    def sql_names(cls) -> list[str]:
1649-        if cls is Func:
1650-            raise NotImplementedError(
1651-                "SQL name is only supported by concrete function implementations"
1652-            )
1653-        if not cls._sql_names:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nprint(sqlglot.parse_one('JSON_ARRAY(1, 2, 3, 4, 5, 6)', read='duckdb').sql('duckdb'))\nprint(sqlglot.parse_one('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)').sql())\n\" 2>&1 | tail -4; $P -c \"\nfrom sqlglot import exp\nprint(exp.JSONArray.from_arg_list([exp.column(c) for c in 'abcdef']).sql())\n\" 2>&1 | tail -4; $P -c \"\nfrom sqlglot import exp\nprint(exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef']).sql())\n\" 2>&1 | tail -4", "description": "Test JSON_ARRAY parse and builder paths"}
[tool_result]   File "~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/sqlglot/parser.py", line 1991, in raise_error
    raise error
sqlglot.errors.ParseError: The number of provided arguments (6) is greater than the maximum number of supported arguments (4). Line 1, Col: 28.
  JSON_ARRAY(1, 2, 3, 4, 5, 6[4m)[0m
           ^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/sqlglot/expressions/core.py", line 1394, in __iter__
    raise TypeError(f"'{self.__class__.__name__}' object is not iterable")
TypeError: 'Column' object is not iterable
JSON_ARRAY(a, b, c, d, e, f)
[assistant] Reproduced: base-parser and builder calls with more than four values fail with "maximum number of supported arguments (4)". Next I'll check how similar variadic functions declare their args and what tests cover `JSON_ARRAY`.
[tool_use Bash] {"command": "grep -n \"class JSONObject\\b\" -A 10 sqlglot/expressions/json.py; grep -n \"class Coalesce\\|class Concat\\b\\|class Greatest\" -B1 -A 8 sqlglot/expressions/*.py | head -60; grep -rn \"JSON_ARRAY(\" tests/ | grep -v -i \"oracle\\|bigquery\\|duckdb\\|singlestore\" | head -30; grep -rn \"def from_arg_list\" -A3 sqlglot/expressions/*.py | head -30", "description": "Check variadic patterns and JSON_ARRAY tests"}
[tool_result] 155:class JSONObject(Expression, Func):
156-    arg_types = {
157-        "expressions": False,
158-        "null_handling": False,
159-        "unique_keys": False,
160-        "return_type": False,
161-        "encoding": False,
162-    }
163-
164-
165-class JSONObjectAgg(Expression, AggFunc):
sqlglot/expressions/functions.py-121-
sqlglot/expressions/functions.py:122:class Coalesce(Expression, Func):
sqlglot/expressions/functions.py-123-    arg_types = {"this": True, "expressions": False, "is_
…[1767 chars elided]…
optimizer/annotate_functions.sql:1311:JSON_ARRAY(10);
tests/fixtures/optimizer/annotate_functions.sql:1315:JSON_ARRAY(10, [1, 2]);
sqlglot/expressions/core.py:1633:    def from_arg_list(cls, args: Sequence[object]) -> Self:
sqlglot/expressions/core.py-1634-        if cls.is_var_len_args:
sqlglot/expressions/core.py-1635-            all_arg_keys = tuple(cls.arg_types)
sqlglot/expressions/core.py-1636-            # If this function supports variable length argument treat the last argument as such.
[assistant] The existing variadic pattern (`is_var_len_args`) assumes the variadic key is last, but `JSONArray`'s `expressions` is first, so reordering would break positional parsing. Before changing anything I'll record a baseline of how every dialect parses `JSON_ARRAY` with 0–6 args, so I can prove existing dialect output is unchanged.
[tool_use Bash] {"command": "mkdir -p /tmp/jsonarr && cat > /tmp/jsonarr/baseline.py <<'EOF'\nimport sqlglot\nfrom sqlglot.dialects.dialect import Dialect\nout = []\nfor d in sorted(Dialect.classes):\n    for n in range(0, 7):\n        args = \", \".join(str(i + 1) for i in range(n))\n        sql = f\"SELECT JSON_ARRAY({args})\"\n        try:\n            r = sqlglot.transpile(sql, read=d, write=d)[0]\n        ex
…[246 chars elided]…
ost-four/base-1 && <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/jsonarr/baseline.py').read())\" > /tmp/jsonarr/before.txt 2>&1; wc -l /tmp/jsonarr/before.txt; grep \"|[2-6]|\" /tmp/jsonarr/before.txt | head -20; grep -c ERR /tmp/jsonarr/before.txt", "description": "Capture JSON_ARRAY baseline across dialects"}
[tool_result]      238 /tmp/jsonarr/before.txt
|2|SELECT JSON_ARRAY(1, 2)
|3|SELECT JSON_ARRAY(1, 2, 3)
|4|SELECT JSON_ARRAY(1, 2, 3, 4)
|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
athena|2|SELECT JSON_ARRAY(1, 2)
athena|3|SELECT JSON_ARRAY(1, 2, 3)
athena|4|SELECT JSON_ARRAY(1, 2, 3, 4)
athena|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
athena|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
bigquery|2|SELECT JSON_ARRAY(1, 2)
bigquery|3|SELECT JSON_ARRAY(1, 2, 3)
bigquery|4|SELECT JSON_ARRAY(1, 2, 3, 4)
bigquery|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
bigquery|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
clickhouse|2|SELECT JSON_ARRAY(1, 2)
clickhouse|3|SELECT JSON_ARRAY(1, 2, 3)
clickhouse|4|SELECT JSON_ARRAY(1, 2, 3, 4)
clickhouse|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
clickhouse|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
9
[tool_use Bash] {"command": "cd /tmp/jsonarr && grep ERR before.txt; grep \"^sqlglot|\\|^duckdb|\\|^oracle|\\|^snowflake|\" before.txt", "description": "Show error and key dialect baseline rows"}
[tool_result] duckdb|5|ERR ParseError: The number of provided arguments (5) is greater than the maximum number of suppo
duckdb|6|ERR ParseError: The number of provided arguments (6) is greater than the maximum number of suppo
prql|0|ERR ParseError: Invalid expression / Unexpected token. Line 1, Col: 6.
prql|1|ERR ParseError: Invalid expression / Unexpected token. Line 1, Col: 6.
prql|2|ERR ParseError: Invalid expression / Unexpected token. Line 1, Col: 6.
prql|3|ERR ParseError: Invalid expression / Unexpected
…[796 chars elided]…
, 3, 4)
oracle|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
oracle|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
snowflake|0|SELECT JSON_ARRAY()
snowflake|1|SELECT JSON_ARRAY(1)
snowflake|2|SELECT JSON_ARRAY(1, 2)
snowflake|3|SELECT JSON_ARRAY(1, 2, 3)
snowflake|4|SELECT JSON_ARRAY(1, 2, 3, 4)
snowflake|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
snowflake|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1
[assistant] DuckDB is the failing dialect: its parser calls `exp.JSONArray(expressions=args)`, so the limit comes from validation rather than `from_arg_list`. Checking that path.
[tool_use Bash] {"command": "sed -n 1215,1250p sqlglot/expressions/core.py; grep -n \"maximum number of supported\" -B12 sqlglot/parser.py | head -40", "description": "Inspect argument count validation logic"}
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
…[181 chars elided]…
            if errors is None:
                errors = []
            errors.append(
                f"The number of provided arguments ({len(args)}) is greater than "
                f"the maximum number of supported arguments ({len(self.arg_types)})"
            )

        return errors or []

    def and_(
        self,
        *expressions: ExpOrStr | None,
        dialect: DialectType = None,
        copy: bool = True,
        wrap: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
[assistant] Root cause: `error_messages` rejects any call where the positional arg count exceeds `len(arg_types)`, and `JSONArray` has four keys. Setting `is_var_len_args` skips that check, but `from_arg_list` would then send the overflow into `strict`. So I'll also make the positional builder put every value into `expressions`. Applying that change now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py", "old_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n", "new_string": "class JSONArray(Expression, Func):\n    arg_types = {\n        \"expressions\": False,\n        \"null_handling\": False,\n        \"return_type\": False,\n        \"strict\": False,\n    }\n    is_var_len_args = True\n\n    @classmethod\n    def from_arg_list(cls, args):\n        return cls(expressions=args)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/jsonarr/baseline.py').read())\" > /tmp/jsonarr/after.txt 2>&1; diff /tmp/jsonarr/before.txt /tmp/jsonarr/after.txt; echo \"---\"; $P -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import exp, parse_one\nprint(exp.func('JSON_ARRAY', *[exp.column(c) for c in 'abcdef']).sql())\nprint(parse_one('SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)').sql())\n\"", "description": "Re-run baseline diff and six-arg checks"}
[tool_result] 69,70c69,70
< duckdb|5|ERR ParseError: The number of provided arguments (5) is greater than the maximum number of suppo
< duckdb|6|ERR ParseError: The number of provided arguments (6) is greater than the maximum number of suppo
---
> duckdb|5|SELECT JSON_ARRAY(1, 2, 3, 4, 5)
> duckdb|6|SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
---
JSON_ARRAY(a, b, c, d, e, f)
SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)
[assistant] The only baseline rows that changed are the two DuckDB errors, which now succeed. Every other dialect's output is byte-identical. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "grep -n \"JSON_ARRAY\" tests/dialects/test_duckdb.py tests/test_expressions.py tests/test_build.py 2>/dev/null | head", "description": "Find existing JSON_ARRAY tests in DuckDB suite"}
[tool_result] tests/dialects/test_duckdb.py:553:            "SELECT JSON_ARRAY('a', 'b', 'c')",
tests/dialects/test_duckdb.py:555:                "duckdb": "SELECT JSON_ARRAY('a', 'b', 'c')",
tests/dialects/test_duckdb.py:560:            "SELECT JSON_ARRAY(NULL, 'a', 1)",
tests/dialects/test_duckdb.py:562:                "duckdb": "SELECT JSON_ARRAY(NULL, 'a', 1)",
tests/dialects/test_duckdb.py:567:            "SELECT JSON_ARRAY(NULL)",
tests/dialects/test_duckdb.py:569:                "duckdb": "SELECT JSON_ARRAY(NULL)",
tests/dialects/test_duckdb.py:574:            "SELECT JSON_ARRAY()",
tests/dialects/test_duckdb.py:576:                "duckdb": "SELECT JSON_ARRAY()",
[tool_use Bash] {"command": "sed -n 548,582p tests/dialects/test_duckdb.py", "description": "Read existing DuckDB JSON_ARRAY test block"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY()\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(
…[186 chars elided]…
()\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT())\",\n            },\n        )\n        self.validate_all(\n            \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)\",\n                \"snowflake\": \"SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120331-json-array-accepts-at-most-four/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Running the project's test command, as specified in the repo's harness instructions.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ............................................. [ 11%]
................................................................................................ [ 20%]
..................... [ 22%]
............................................................................................................................................. [ 35%]
............................. [ 37%]
.............................. [ 40%]
........................... [ 43%]
.......................................................
…[213 chars elided]…
................................................................. [ 72%]
............................................. [ 76%]
............................................. [ 80%]
................................................................................ [ 87%]
........................................................................................................................................                                              [100%]
1093 passed, 17870 subtests passed in 54.52s
[assistant] All 1093 tests pass. I'll run a quick lint on the two changed files and clean up the scratch files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/expressions/json.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/expressions/json.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; rm -rf /tmp/jsonarr; git status --short; git diff", "description": "Lint changed files and show diff"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/expressions/json.py
 M tests/dialects/test_duckdb.py
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
+        return c
…[363 chars elided]…
))",
             },
         )
+        self.validate_all(
+            "SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)",
+            write={
+                "duckdb": "SELECT JSON_ARRAY(1, 2, 3, 4, 5, 6)",
+                "snowflake": "SELECT TO_VARIANT(ARRAY_CONSTRUCT(1, 2, 3, 4, 5, 6))",
+            },
+        )
         self.validate_identity(
             "SELECT col FROM t WHERE JSON_EXTRACT_STRING(col, '$.id') NOT IN ('b')",
             "SELECT col FROM t WHERE NOT (col ->> '$.id') IN ('b')",
[assistant] `JSON_ARRAY` now accepts any number of values. `JSON_ARRAY(1, 2, 3, 4, 5, 6)` parses and round-trips in DuckDB, which was the only dialect that rejected it.

**Cause:** `JSONArray` declared four argument slots and wasn't marked variadic, so argument validation rejected anything beyond four. DuckDB was the one dialect that routes `JSON_ARRAY` through that validated path. The other dialects either map it to an untyped function or build it some other way.

**Change** (`sqlglot/expressions/json.py`):
- `JSONArray` is now `is_var_len_args = True`, which skips the arity check.
- It overrides `from_a
…[151 chars elided]…
** I captured how every dialect parses `JSON_ARRAY` with 0–6 arguments before and after the change. Only the two DuckDB rows (5 and 6 arguments) differ, going from a parse error to correct output. Everything else is byte-identical.

**Test:** added a 6-argument case to `tests/dialects/test_duckdb.py`, next to the existing `JSON_ARRAY` cases. No existing test was modified.

**Checks:** the full suite passes (1093 tests, 17870 subtests) and ruff check and format are clean on both files.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo asks for.
