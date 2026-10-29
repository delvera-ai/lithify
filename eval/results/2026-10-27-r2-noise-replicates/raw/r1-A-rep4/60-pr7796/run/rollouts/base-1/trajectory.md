# trajectory base-1

final message:
Snowflake now parses and round-trips `IDENTIFIER(...)` invocations with zero or more arguments. All three queries from the report come back unchanged, and the full suite passes (1127 tests).

The cause was that `IDENTIFIER(...)` was parsed as a function, and the `(...)` after it was then taken as an alias column list, which is where the `Aliases` error came from. The fix:

- **Parser** (`sqlglot/parsers/snowflake.py`): `_parse_function_call` now checks whether a parsed `DynamicIdentifier` is followed by `(`. If so, it reads the argument list into an `exp.Anonymous` call whose callee is the `IDENTIFIER(...)` expression.
- **Generator** (`sqlglot/generators/snowflake.py`): `anonymous_sql` skips the usual function-name uppercasing when the callee is a `DynamicIdentifier`. Without this, `IDENTIFIER($fn)` would come out as `IDENTIFIER($FN)`, which changes the variable name.
- **Tests** (`tests/dialects/test_snowflake.py`): three identity checks added next to the existing `IDENTIFIER` tests.

Ruff formatting and lint pass on the changed files. I did not commit.

## events
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py | head -50; grep -rn \"IDENTIFIER\" tests/dialects/test_snowflake.py | head -30", "description": "Find IDENTIFIER handling in Snowflake dialect"}
[tool_result] tests/dialects/test_snowflake.py:770:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
tests/dialects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "grep -rn \"IDENTIFIER\\|\\\"IDENTIFIER\\\"\" sqlglot/ | grep -v \"IDENTIFIERS\\|_IDENTIFIER\\b\" | head -30; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT IDENTIFIER(\\$fn)(41)\\\", \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", \\\"SELECT IDENTIFIER(\\$fn)()\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='snowflake'); print(repr(e))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Locate IDENTIFIER references and reproduce parse errors"}
[tool_result] sqlglot/tokens.py:68:    IDENTIFIER_ESCAPES: t.ClassVar[list[str]]
sqlglot/tokens.py:88:    _IDENTIFIER_ESCAPES: t.ClassVar[set[str]]
sqlglot/tokens.py:115:        cls._IDENTIFIER_ESCAPES = set(cls.IDENTIFIER_ESCAPES)
sqlglot/tokens.py:186:    IDENTIFIER_ESCAPES: t.ClassVar[list[str]] = []
sqlglot/tokens.py:207:    _IDENTIFIER_ESCAPES: t.ClassVar[set[str]] = set()
sqlglot/tokens.py:574:            identifier_escapes=self._IDENTIFIER_ESCAPES,
sqlglot/tokenizer_core.py:96:    IDENTIFIER = auto()
s
…[1831 chars elided]…
er.py:8537:        if self._match(TokenType.IDENTIFIER):
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
[tool_use Bash] {"command": "grep -rn \"Aliases\\|IDENTIFIER\\b\" sqlglot/dialects/snowflake.py sqlglot/parser.py | grep -i \"ident\\|Aliases\" | head; grep -n \"class Aliases\" -A8 sqlglot/expressions/*.py; grep -n \"\\\"IDENTIFIER\\\"\\|'IDENTIFIER'\\|IDENTIFIER\\\"\" -r sqlglot | head", "description": "Find Aliases class and IDENTIFIER function handling"}
[tool_result] sqlglot/parser.py:573:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:616:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:706:        TokenType.IDENTIFIER,
sqlglot/parser.py:799:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
sqlglot/parser.py:840:        TokenType.IDENTIFIER,
sqlglot/parser.py:1480:        TokenType.IDENTIFIER,
sqlglot/parser.py:4704:                        this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
s
…[958 chars elided]…

sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1164:        if self._match_text_seq("IDENTIFIER", "("):
sqlglot/dialects/tsql.py:182:            "UNIQUEIDENTIFIER": TokenType.UUID,
sqlglot/generators/fabric.py:69:        exp.DType.UUID: "UNIQUEIDENTIFIER",
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
sqlglot/generators/tsql.py:186:        exp.DType.UUID: "UNIQUEIDENTIFIER",
[tool_use Bash] {"command": "grep -n \"class DynamicIdentifier\" -A6 sqlglot/expressions/*.py; sed -n 1150,1185p sqlglot/parsers/snowflake.py; sed -n 1955,1970p sqlglot/generators/snowflake.py 2>/dev/null; sed -n 1958,1970p sqlglot/generator.py; grep -n \"Aliases\" sqlglot/parser.py | head", "description": "Inspect DynamicIdentifier and snowflake IDENTIFIER parsing"}
[tool_result] sqlglot/expressions/core.py:1811:class DynamicIdentifier(Expression, Func):
sqlglot/expressions/core.py-1812-    pass
sqlglot/expressions/core.py-1813-
sqlglot/expressions/core.py-1814-
sqlglot/expressions/core.py-1815-class Opclass(Expression):
sqlglot/expressions/core.py-1816-    arg_types = {"this": True, "expression": True}
sqlglot/expressions/core.py-1817-
            table_from_rows = table.this
            for arg in exp.TableFromRows.arg_types:
                if arg != "this":
         
…[1160 chars elided]…
self, expression: exp.DynamicIdentifier) -> str:
        this = expression.this
        if this and this.is_string:
            return maybe_parse(this.name).sql(self.dialect)
        self.unsupported("IDENTIFIER() with non-literal arguments is not supported")
        return self.func("IDENTIFIER", this)

    def identifier_sql(self, expression: exp.Identifier) -> str:
        text = expression.name
        lower = text.lower()
        quoted = expression.quoted
8482:                exp.Aliases(
[tool_use Bash] {"command": "sed -n 8460,8500p sqlglot/parser.py; sed -n 720,730p sqlglot/parsers/snowflake.py; grep -n \"def _parse_function_call\" -A3 sqlglot/parser.py | head; grep -n \"ID_VAR_TOKENS\\|_parse_id_var\" sqlglot/parsers/snowflake.py | head", "description": "View alias-parsing code and snowflake function registration"}
[tool_result]         }

    def _parse_alias(self, this: exp.Expr | None, explicit: bool = False) -> exp.Expr | None:
        # In some dialects, LIMIT and OFFSET can act as both identifiers and keywords (clauses)
        # so this section tries to parse the clause version and if it fails, it treats the token
        # as an identifier (alias)
        if self._can_parse_limit_or_offset():
            return this

        # WINDOW is in ID_VAR_TOKENS, so it can be consumed as an implicit alias. Detect the
   
…[1920 chars elided]…
NS,
380:    COLON_PLACEHOLDER_TOKENS = ID_VAR_TOKENS | {TokenType.NUMBER}
754:                expressions=self._parse_csv(self._parse_id_var),
1002:                    and self._parse_wrapped_csv(self._parse_id_var),
1039:            expressions = self._parse_wrapped_csv(self._parse_id_var)
1159:    def _parse_id_var(
1166:                super()._parse_id_var(any_token=any_token, tokens=tokens) or self._parse_string()
1171:        return super()._parse_id_var(any_token=any_token, tokens=tokens)
[tool_use Bash] {"command": "sed -n 6944,7090p sqlglot/parser.py; grep -n \"def anonymous_sql\" -A12 sqlglot/generator.py", "description": "Read function-call parsing and anonymous SQL generation"}
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
…[5078 chars elided]…
ase-sensitive
3938-        parent = expression.parent
3939-        is_qualified = isinstance(parent, exp.Dot) and expression is parent.expression
3940-
3941-        return self.func(
3942-            self.sql(expression, "this"), *expression.expressions, normalize=not is_qualified
3943-        )
3944-
3945-    def paren_sql(self, expression: exp.Paren) -> str:
3946-        sql = self.seg(self.indent(self.sql(expression, "this")), sep="")
3947-        return f"({sql}{self.seg(')', sep='')}"
3948-
[tool_use Bash] {"command": "grep -n \"def _parse_function_args\\|def _parse_function(\" -A12 sqlglot/parser.py | head -60; grep -n \"_parse_function_call\\|^class\\|    def _parse_\" sqlglot/parsers/snowflake.py | head -20; sed -n 1,30p sqlglot/parsers/snowflake.py | grep import", "description": "Check function-args parsing and snowflake parser imports"}
[tool_result] 6911:    def _parse_function(
6912-        self,
6913-        functions: dict[str, t.Callable] | None = None,
6914-        anonymous: bool = False,
6915-        optional_parens: bool = True,
6916-        any_token: bool = False,
6917-    ) -> exp.Expr | None:
6918-        # This allows us to also parse {fn <function>} syntax (Snowflake, MySQL support this)
6919-        # See: https://community.snowflake.com/s/article/SQL-Escape-Sequences
6920-        fn_syntax = False
6921-        if (
6922-    
…[1538 chars elided]…
exp.Command:
1231:    def _parse_put(self) -> exp.Put | exp.Command:
1243:    def _parse_get(self) -> exp.Expr | None:
from __future__ import annotations
import typing as t
from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
from sqlglot.helper import is_date_unit, is_int, seq_get
from sqlglot.tokens import TokenType
from sqlglot.trie import new_trie
    from collections.abc import Collection
    from sqlglot._typing import B, E
    from sqlglot.dialects.dialect import Dialect
[tool_use Bash] {"command": "grep -n \"    def func(\" -A12 sqlglot/generator.py; grep -n \"def normalize_func\" -A10 sqlglot/generator.py; grep -n \"anonymous_sql\\|dynamicidentifier\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py; grep -n \"class DynamicIdentifier\" -B2 sqlglot/expressions/core.py; grep -n \"def _match_r_paren\" -A3 sqlglot/parser.py", "description": "Check generator func helper and related snowflake hooks"}
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
1059:    def normalize_func(self, name: str)
…[180 chars elided]…
lower":
1063-            return name.lower()
1064-        return name
1065-
1066-    def indent(
1067-        self,
1068-        sql: str,
1069-        level: int = 0,
1809-
1810-# https://docs.snowflake.com/en/sql-reference/identifier-literal
1811:class DynamicIdentifier(Expression, Func):
9432:    def _match_r_paren(self, expression: exp.Expr | None = None) -> None:
9433-        if not self._match(TokenType.R_PAREN, expression=expression):
9434-            self.raise_error("Expecting )")
9435-
[tool_use Bash] {"command": "grep -rn \"def dynamicidentifier_sql\" sqlglot/; grep -n \"def dynamicidentifier_sql\" -B3 -A3 sqlglot/generators/snowflake.py; sed -n 470,480p sqlglot/generators/snowflake.py", "description": "Locate dynamicidentifier generator method"}
[tool_result] sqlglot/generator.py:1960:    def dynamicidentifier_sql(self, expression: exp.DynamicIdentifier) -> str:
            e.args.get("encryption_method"),
            e.args.get("aead"),
        ),
        exp.DayOfMonth: rename_func("DAYOFMONTH"),
        exp.DayOfWeek: rename_func("DAYOFWEEK"),
        exp.DayOfWeekIso: rename_func("DAYOFWEEKISO"),
        exp.DayOfYear: rename_func("DAYOFYEAR"),
        exp.DotProduct: rename_func("VECTOR_INNER_PRODUCT"),
        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
        exp.Explode: rename_func("FLATTEN"),
        exp.Extract: lambda self, e: self.func(
[tool_use Bash] {"command": "grep -n \"^    def \\|^class \" sqlglot/generators/snowflake.py | head -30; sed -n 1155,1160p sqlglot/parsers/snowflake.py", "description": "List snowflake generator methods and parser context"}
[tool_result] 53:    def _builder(args: list) -> E:
102:    def _flatten_structured_type(expression: exp.Expr) -> exp.Expr:
375:class SnowflakeGenerator(generator.Generator):
620:    def sortarray_sql(self, expression: exp.SortArray) -> str:
627:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
678:    def with_properties(self, properties: exp.Properties) -> str:
681:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
687:    def datatype_sql(self, expression: exp
…[1066 chars elided]…
xQuantile) -> str:
940:    def alterset_sql(self, expression: exp.AlterSet) -> str:
952:    def strtotime_sql(self, expression: exp.StrToTime):
972:    def timestampsub_sql(self, expression: exp.TimestampSub):
981:    def jsonextract_sql(self, expression: exp.JSONExtract):
997:    def timetostr_sql(self, expression: exp.TimeToStr) -> str:
1004:    def datesub_sql(self, expression: exp.DateSub) -> str:
            table = table_from_rows

        return table

    def _parse_id_var(
        self,
[assistant] Now I'll make the parser change: after a parsed `IDENTIFIER(...)` function, consume a following argument list into an `Anonymous` call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_id_var(\n        self,\n        any_token: bool = True,", "new_string": "    def _parse_function_call(\n        self,\n        functions: dict[str, t.Callable] | None = None,\n        anonymous:
…[252 chars elided]…
TIFIER($fn)(41) or IDENTIFIER('my_func')(1, 2)\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            call = self.expression(exp.Anonymous(this=func, expressions=self._parse_function_args()))\n            self._match_r_paren(call)\n            return call\n\n        return func\n\n    def _parse_id_var(\n        self,\n        any_token: bool = True,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py", "old_string": "    def sortarray_sql(self, expression: exp.SortArray) -> str:", "new_string": "    def anonymous_sql(self, expression: exp.Anonymous) -> str:\n        if isinstance(expression.this, exp.DynamicIdentifier):\n            return self.func(\n                self.sql(expression, \"this\"), *expression.expressions, normalize=False\n            )\n        return super().anonymous_sql(expression)\n\n    def sortarray_sql(self, expression: exp.SortArray) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SET fn = 'add_one'\\\", \\\"SELECT IDENTIFIER(\\$fn)(41)\\\", \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", \\\"SELECT IDENTIFIER(\\$fn)()\\\", \\\"SELECT IDENTIFIER('f')(1) AS x FROM t\\\", \\\"SELECT IDENTIFIER('foo') FROM x\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Verify the reported queries parse and round-trip"}
[tool_result] SET fn = 'add_one'
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER('f')(1) AS x FROM t
SELECT IDENTIFIER('foo') FROM x
[assistant] Round-trips work. Now I'll add regression tests next to the existing `IDENTIFIER` tests and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-085228-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
........
…[350 chars elided]…
.......................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 49.57s
[assistant] All 1127 tests pass. Checking formatting on the touched files, since one of my lines may be long.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py 2>&1 || true) | tail -5; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py 2>&1 | tail -3", "description": "Check ruff formatting and lint on changed files"}
[tool_result] Would reformat: sqlglot/generators/snowflake.py
Would reformat: sqlglot/parsers/snowflake.py
2 files would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py && git diff --stat && git diff sqlglot/ && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -2", "description": "Apply ruff formatting, review diff, rerun Snowflake tests"}
[tool_result] 2 files reformatted
 sqlglot/generators/snowflake.py  |  5 +++++
 sqlglot/parsers/snowflake.py     | 19 +++++++++++++++++++
 tests/dialects/test_snowflake.py |  3 +++
 3 files changed, 27 insertions(+)
diff --git a/sqlglot/generators/snowflake.py b/sqlglot/generators/snowflake.py
index 401188f4e..7afb4d7ed 100644
--- a/sqlglot/generators/snowflake.py
+++ b/sqlglot/generators/snowflake.py
@@ -617,6 +617,11 @@ class SnowflakeGenerator(generator.Generator):
         ),
     }
 
+    def anonymous_s
…[1331 chars elided]…
 )
+            self._match_r_paren(call)
+            return call
+
+        return func
+
     def _parse_id_var(
         self,
         any_token: bool = True,
................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.45s
[This command modified 2 files you've previously read: sqlglot/parsers/snowflake.py, sqlglot/generators/snowflake.py. Call Read before editing.]
[assistant] Snowflake now parses and round-trips `IDENTIFIER(...)` invocations with zero or more arguments. All three queries from the report come back unchanged, and the full suite passes (1127 tests).

The cause was that `IDENTIFIER(...)` was parsed as a function, and the `(...)` after it was then taken as an alias column list, which is where the `Aliases` error came from. The fix:

- **Parser** (`sqlglot/parsers/snowflake.py`): `_parse_function_call` now checks whether a parsed `DynamicIdentifier` is followed by `(`. If so, it reads the argument list into an `exp.Anonymous` call whose callee is the `IDENTIFIER(...)` expression.
- **Generator** (`sqlglot/generators/snowflake.py`): `anonymous_sql` skips the usual function-name uppercasing when the callee is a `DynamicIdentifier`. Without this, `IDENTIFIER($fn)` would come out as `IDENTIFIER($FN)`, which changes the variable name.
- **Tests** (`tests/dialects/test_snowflake.py`): three identity checks added next to the existing `IDENTIFIER` tests.

Ruff formatting and lint pass on the changed files. I did not commit.
