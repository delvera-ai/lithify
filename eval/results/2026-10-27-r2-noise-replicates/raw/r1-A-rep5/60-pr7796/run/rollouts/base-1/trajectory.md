# trajectory base-1

final message:
Snowflake now parses dynamic function calls through `IDENTIFIER()` with zero or more arguments, and all three cases from the report round-trip unchanged. The full suite passes (1127 tests), and ruff check and format are clean on the changed files.

**Cause:** `IDENTIFIER` is registered as a function that returns `DynamicIdentifier`, so the parser stopped after `IDENTIFIER(...)` and never consumed the `(args)` that follow.

**Changes:**
- `sqlglot/parsers/snowflake.py`: a `_parse_function_call` override. When the call returns a `DynamicIdentifier` and a `(` follows, it parses the argument list and returns an `exp.Anonymous` whose `this` is the `DynamicIdentifier`.
- `sqlglot/generators/snowflake.py`: an `anonymous_sql` override. For that case it skips name normalization. Without this, `IDENTIFIER('my_func')` would have been upper-cased to `IDENTIFIER('MY_FUNC')`, which changes the string literal.
- `tests/dialects/test_snowflake.py`: three `validate_identity` lines next to the existing `IDENTIFIER` tests, covering the three cases from the report.

**Choices I made:**
- I used `exp.Anonymous` rather than adding a new expression class, so the call's shape stays the same as ordinary function calls.
- The override is Snowflake-only, so other dialects are unaffected.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py | head -50; grep -n \"def _parse_column_ops\\|def _parse_primary\\|def _parse_function\\|def _parse_id_var\\|def _parse_alias\" sqlglot/parser.py", "description": "Find IDENTIFIER handling in Snowflake dialect and parser"}
[tool_result] 5178:        def _parse_aliased_expression() -> exp.Expr | None:
6768:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6866:    def _parse_primary(self) -> exp.Expr | None:
6911:    def _parse_function(
6941:    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
6944:    def _parse_function_call(
7091:    def _parse_function_properties(self) -> exp.Properties | None:
7111:    def _parse_function_parameter(self) -> exp.Expr | None:
7599:    def _parse_primary_key_part(self) -> exp.Expr | None:
7614:    def _parse_primary_key(
8462:    def _parse_alias(self, this: exp.Expr | None, explicit: bool = False) -> exp.Expr | None:
8505:    def _parse_id_var(
8566:    def _parse_primary_or_var(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6768,6945p sqlglot/parser.py; grep -n \"IDENTIFIER\" sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/snowflake.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -40", "description": "Read column ops and primary parsing, grep IDENTIFIER"}
[tool_result]     def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
        while self._curr.token_type in self.BRACKETS:
            this = self._parse_bracket(this)

        column_operators = self.COLUMN_OPERATORS
        cast_column_operators = self.CAST_COLUMN_OPERATORS
        while self._curr:
            op_token = self._curr.token_type

            if op_token not in column_operators:
                break
            op = column_operators[op_token]
            self._advance()

 
…[8905 chars elided]…
en_type != TokenType.IDENTIFIER
sqlglot/parser.py:7850:            tokens={TokenType.BINARY, TokenType.IDENTIFIER},
sqlglot/parser.py:8537:        if self._match(TokenType.IDENTIFIER):
sqlglot/dialects/dialect.py:278:        klass.IDENTIFIER_START, klass.IDENTIFIER_END = list(
sqlglot/dialects/dialect.py:279:            klass.tokenizer_class._IDENTIFIERS.items()
sqlglot/dialects/dialect.py:348:    IDENTIFIERS_CAN_START_WITH_DIGIT = False
sqlglot/dialects/dialect.py:792:    IDENTIFIER_START = '"'
[tool_use Bash] {"command": "grep -rn '\"IDENTIFIER\"' sqlglot/ | head; grep -rn \"IDENTIFIER(\" tests/dialects/test_snowflake.py | head -20", "description": "Search for IDENTIFIER function handling and tests"}
[tool_result] sqlglot/generator.py:1965:        return self.func("IDENTIFIER", this)
sqlglot/parsers/clickhouse.py:555:            self._match_text_seq("IDENTIFIER") and "Identifier"
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1164:        if self._match_text_seq("IDENTIFIER", "("):
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
tests/dialects/test_snowflake.py:770:        self.validate_
…[81 chars elided]…
lects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "sed -n 1150,1185p sqlglot/parsers/snowflake.py; grep -n \"class DynamicIdentifier\" -A8 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; sed -n 1955,1970p sqlglot/generator.py; grep -rn \"DynamicIdentifier\" sqlglot/ | grep -v \"^sqlglot/expressions\" | head", "description": "Read Snowflake IDENTIFIER parse and DynamicIdentifier class"}
[tool_result]             table_from_rows = table.this
            for arg in exp.TableFromRows.arg_types:
                if arg != "this":
                    table_from_rows.set(arg, table.args.get(arg))

            table = table_from_rows

        return table

    def _parse_id_var(
        self,
        any_token: bool = True,
        tokens: Collection[TokenType] | None = None,
    ) -> exp.Expr | None:
        if self._match_text_seq("IDENTIFIER", "("):
            identifier = (
                supe
…[1712 chars elided]…
 str:
        text = expression.name
        lower = text.lower()
        quoted = expression.quoted
sqlglot/generator.py:1960:    def dynamicidentifier_sql(self, expression: exp.DynamicIdentifier) -> str:
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1169:            return self.expression(exp.DynamicIdentifier(this=identifier))
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)); print(e.sql('snowflake'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1 | tail -40; grep -n \"class Anonymous\\|class Func\\b\" sqlglot/expressions/*.py | head", "description": "Reproduce the ParseError cases"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/expressions/core.py:1641:class Func(Condition):
sqlglot/expressions/core.py:1978:class Anonymous(Expression, Func):
sqlglot/expressions/core.py:1987:class AnonymousAggFunc(Expression, AggFunc):
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)); print(e.sql('snowflake'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1 | tail -60", "description": "Reproduce parse errors with repo on path"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)); print(e.sql('snowflake'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1 | tail -60", "description": "Reproduce parse errors with repo on path"}
[tool_result] ParseError Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ParseError Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ParseError Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
[tool_use Bash] {"command": "sed -n 6944,7090p sqlglot/parser.py; grep -n \"def anonymous_sql\" -A12 sqlglot/generator.py; sed -n 1978,1990p sqlglot/expressions/core.py; sed -n 720,730p sqlglot/parsers/snowflake.py", "description": "Read function call parsing and anonymous generation"}
[tool_result]     def _parse_function_call(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
        if not self._curr:
            return None

        comments = self._curr.comments
        prev = self._prev
        token = self._curr
        token_type = self._curr.token_type
        this: str | exp.Expr = self._curr.text
        upper = self._curr.text.uppe
…[5992 chars elided]…
l.number("1"),
        ),
        "STRTOK_TO_ARRAY": lambda args: exp.StrtokToArray(
            this=seq_get(args, 0),
            expression=seq_get(args, 1) or exp.Literal.string(" "),
        ),
        "SYSTIMESTAMP": exp.CurrentTimestamp.from_arg_list,
        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
        "UNICODE": lambda args: exp.Unicode(this=seq_get(args, 0), empty_is_zero=True),
        "WEEKISO": exp.WeekOfYear.from_arg_list,
        "WEEKOFYEAR": exp.Week.from_arg_list,
[tool_use Bash] {"command": "grep -n \"    def func(\" -A22 sqlglot/generator.py; grep -n \"def normalize_func\" -A8 sqlglot/generator.py; sed -n 470,480p sqlglot/generators/snowflake.py; grep -n \"def _parse_function_call\\|def _parse_id_var\" sqlglot/parsers/snowflake.py sqlglot/parser.py", "description": "Inspect generator func helper and normalization"}
[tool_result] 4597:    def func(
4598-        self,
4599-        name: str,
4600-        *args: t.Any,
4601-        prefix: str = "(",
4602-        suffix: str = ")",
4603-        normalize: bool = True,
4604-    ) -> str:
4605-        name = self.normalize_func(name) if normalize else name
4606-        return f"{name}{prefix}{self.format_args(*args)}{suffix}"
4607-
4608-    def format_args(self, *args: t.Any, sep: str = ", ") -> str:
4609-        arg_sqls = tuple(
4610-            self.sql(arg) for arg in ar
…[953 chars elided]…
k: rename_func("DAYOFWEEK"),
        exp.DayOfWeekIso: rename_func("DAYOFWEEKISO"),
        exp.DayOfYear: rename_func("DAYOFYEAR"),
        exp.DotProduct: rename_func("VECTOR_INNER_PRODUCT"),
        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
        exp.Explode: rename_func("FLATTEN"),
        exp.Extract: lambda self, e: self.func(
sqlglot/parsers/snowflake.py:1159:    def _parse_id_var(
sqlglot/parser.py:6944:    def _parse_function_call(
sqlglot/parser.py:8505:    def _parse_id_var(
[tool_use Bash] {"command": "grep -n \"anonymous_sql\\|def dynamic\\|def _parse_function\\b\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py; sed -n 1,40p sqlglot/parsers/snowflake.py | grep -n \"import\\|class\"; grep -n \"def _parse_function_args\\|def _parse_lambda\" sqlglot/parser.py", "description": "Check existing Snowflake anonymous/function overrides"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import is_date_unit, is_int, seq_get
19:from sqlglot.tokens import TokenType
20:from sqlglot.trie import new_trie
23:    from collections.abc import Collection
25:    from sqlglot._typing import B, E
26:    from sqlglot.dialects.dialect import Dialect
6941:    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
7178:    def _parse_lambda_arg(self) -> exp.Expr | None:
7181:    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
[assistant] I've traced the cause: `IDENTIFIER(...)` is registered as a function, so the parser returns a `DynamicIdentifier` and never consumes the `(args)` that follow. I'll wrap that node in an `Anonymous` call in the Snowflake parser, and skip name normalization for it in the Snowflake generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _parse_show_snowflake(", "new_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _
…[343 chars elided]…
           optional_parens=optional_parens,\n            any_token=any_token,\n        )\n\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            args = self._parse_function_args()\n            self._match_r_paren()\n            return self.expression(exp.Anonymous(this=func, expressions=args))\n\n        return func\n\n    def _parse_show_snowflake("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^class Generator\\|    def \\w*_sql\" sqlglot/generators/snowflake.py | head -5; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py", "description": "Locate Snowflake generator class and imports"}
[tool_result] 620:    def sortarray_sql(self, expression: exp.SortArray) -> str:
627:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
681:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
687:    def datatype_sql(self, expression: exp.DataType) -> str:
718:    def tonumber_sql(self, expression: exp.ToNumber) -> str:
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
27:from sqlglot.generator import unsupported_args
28:from sqlglot.helper import find_new_name, flatten, seq_get
29:from sqlglot.optimizer.scope import build_scope, find_all_in_scope
30:from sqlglot.parsers.snowflake import (
36:from sqlglot.tokens import TokenType
37:from collections import defaultdict
[tool_use Bash] {"command": "sed -n 612,626p sqlglot/generators/snowflake.py", "description": "View code around sortarray_sql for insertion point"}
[tool_result]         exp.ByteLength: rename_func("OCTET_LENGTH"),
        exp.Flatten: rename_func("ARRAY_FLATTEN"),
        exp.ArrayConcatAgg: lambda self, e: self.func("ARRAY_FLATTEN", exp.ArrayAgg(this=e.this)),
        exp.SHA2Digest: lambda self, e: self.func(
            "SHA2_BINARY", e.this, e.args.get("length") or exp.Literal.number(256)
        ),
    }

    def sortarray_sql(self, expression: exp.SortArray) -> str:
        asc = expression.args.get("asc")
        nulls_first = expression.args.get("nulls_first")
        if asc == exp.false() and nulls_first == exp.true():
            nulls_first = None
        return self.func("ARRAY_SORT", expression.this, asc, nulls_first)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py", "old_string": "    def sortarray_sql(self, expression: exp.SortArray) -> str:\n        asc = expression.args.get(\"asc\")", "new_string": "    def anonymous_sql(self, expression: exp.Anonymous) -> str:\n        if isinstance(expression.this, exp.DynamicIdentifier):\n            return self.func(\n                self.sql(expression, \"this\"), *expression.expressions, normalize=False\n            )\n        return super().anonymous_sql(expression)\n\n    def sortarray_sql(self, expression: exp.SortArray) -> str:\n        asc = expression.args.get(\"asc\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', 'SELECT IDENTIFIER(\\'foo\\') FROM x', 'SELECT IDENTIFIER(\\$fn)(1) AS r FROM t WHERE IDENTIFIER(\\$fn)(x) > 1']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1 | tail -30", "description": "Verify the reported cases now parse and round-trip"}
[tool_result] SET fn = 'add_one'
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER('foo') FROM x
SELECT IDENTIFIER($fn)(1) AS r FROM t WHERE IDENTIFIER($fn)(x) > 1
[assistant] All reported cases now round-trip. Next I'll add regression tests next to the existing `IDENTIFIER` tests and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-133306-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite"}
[tool_result] ..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
..................................... [ 41%]
........................................................... [ 47%]
...................................... [ 50%]
................................................... [ 55%]
........................................
…[111 chars elided]…
................................................ [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 61.72s (0:01:01)
[assistant] The full suite passes (1127 tests). Now a style check on the changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py 2>&1; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py 2>&1) | tail -10", "description": "Check formatting and lint of changed files"}
[tool_result] Would reformat: sqlglot/generators/snowflake.py
1 file would be reformatted, 2 files already formatted
All checks passed!
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/generators/snowflake.py && git diff --stat && git diff sqlglot/generators/snowflake.py", "description": "Apply ruff formatting and show diff stats"}
[tool_result] 1 file reformatted
 sqlglot/generators/snowflake.py  |  5 +++++
 sqlglot/parsers/snowflake.py     | 21 +++++++++++++++++++++
 tests/dialects/test_snowflake.py |  3 +++
 3 files changed, 29 insertions(+)
diff --git a/sqlglot/generators/snowflake.py b/sqlglot/generators/snowflake.py
index 401188f4e..7afb4d7ed 100644
--- a/sqlglot/generators/snowflake.py
+++ b/sqlglot/generators/snowflake.py
@@ -617,6 +617,11 @@ class SnowflakeGenerator(generator.Generator):
         ),
     }
 
+    def anonymous_
…[40 chars elided]…
str:
+        if isinstance(expression.this, exp.DynamicIdentifier):
+            return self.func(self.sql(expression, "this"), *expression.expressions, normalize=False)
+        return super().anonymous_sql(expression)
+
     def sortarray_sql(self, expression: exp.SortArray) -> str:
         asc = expression.args.get("asc")
         nulls_first = expression.args.get("nulls_first")
[This command modified 1 file you've previously read: sqlglot/generators/snowflake.py. Call Read before editing.]
[assistant] Formatting only collapsed my own new method onto one line. Re-running the Snowflake tests after that change:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -2 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Rerun Snowflake tests and full suite"}
[tool_result] ................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.61s
1127 passed, 18278 subtests passed in 53.87s
[assistant] Snowflake now parses dynamic function calls through `IDENTIFIER()` with zero or more arguments, and all three cases from the report round-trip unchanged. The full suite passes (1127 tests), and ruff check and format are clean on the changed files.

**Cause:** `IDENTIFIER` is registered as a function that returns `DynamicIdentifier`, so the parser stopped after `IDENTIFIER(...)` and never consumed the `(args)` that follow.

**Changes:**
- `sqlglot/parsers/snowflake.py`: a `_parse_function_call` override. When the call returns a `DynamicIdentifier` and a `(` follows, it parses the argument list 
…[109 chars elided]…
an `anonymous_sql` override. For that case it skips name normalization. Without this, `IDENTIFIER('my_func')` would have been upper-cased to `IDENTIFIER('MY_FUNC')`, which changes the string literal.
- `tests/dialects/test_snowflake.py`: three `validate_identity` lines next to the existing `IDENTIFIER` tests, covering the three cases from the report.

**Choices I made:**
- I used `exp.Anonymous` rather than adding a new expression class, so the call's shape stays the same as ordinary function calls.
- The override is Snowflake-only, so other dialects are unaffected.

I did not commit anything.
