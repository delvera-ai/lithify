# trajectory base-1

final message:
Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments:

```
SELECT IDENTIFIER($fn)(41)         -> SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2) -> SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()           -> SELECT IDENTIFIER($fn)()
```

The full suite passes (1127 tests), and `ruff check` and `ruff format --check` are clean. I didn't commit.

**Cause:** `IDENTIFIER(...)` in a function position parsed as a `DynamicIdentifier`, and the trailing `(41)` was left for the alias parser, which read it as a column alias list.

**Changes:**
- `sqlglot/parsers/snowflake.py`: a `_parse_function_call` override. If the call produces a `DynamicIdentifier` and an `(` follows, it parses the arguments into an `exp.Anonymous` whose callee is that `DynamicIdentifier`.
- `sqlglot/generator.py`: `anonymous_sql` skips name normalization when the callee is a `DynamicIdentifier`. Without this, the whole rendered callee was uppercased, giving `IDENTIFIER($FN)` and `IDENTIFIER('MY_FUNC')`, which changes the semantics of the string literal.
- `tests/dialects/test_snowflake.py`: three `validate_identity` round-trips added next to the existing `IDENTIFIER` tests.

The generator change is in shared code, but it only triggers for `DynamicIdentifier` callees, so other dialects and quoted-identifier calls are unaffected.

## events
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py | head -50; grep -n \"IDENTIFIER\" sqlglot/parser.py | head", "description": "Find IDENTIFIER handling in Snowflake and parser"}
[tool_result] 573:        TokenType.OBJECT_IDENTIFIER,
616:    } - {TokenType.IDENTIFIER}
706:        TokenType.IDENTIFIER,
799:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
840:        TokenType.IDENTIFIER,
1480:        TokenType.IDENTIFIER,
4677:        while self._match_set(self.IDENTIFIER_TOKENS):
4688:            elif curr_tt not in self.IDENTIFIER_TOKENS:
4704:                        this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
6276:        if type_token == TokenType.OBJECT_IDENTIFIER:
[tool_use Bash] {"command": "grep -rn -i \"identifier(\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py | grep -v \"_IDENTIFIER\\|IDENTIFIER_\" | head -30; grep -rn \"\\\"IDENTIFIER\\\"\\|'IDENTIFIER'\" sqlglot/ | head; cd ~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1 && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)','SELECT IDENTIFIER(\\'my_func\\')(1, 2)','SELECT IDENTIFIER(\\$fn)()']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', e)\n\"", "description": "Locate IDENTIFIER references and reproduce the parse error"}
[tool_result] sqlglot/generator.py:1964:        self.unsupported("IDENTIFIER() with non-literal arguments is not supported")
sqlglot/generator.py:2547:                    exp.PivotAlias(this=e, alias=exp.to_identifier(stored_full, quoted=True))
sqlglot/generator.py:2553:                    exp.PivotAlias(this=e, alias=exp.to_identifier(stored_value, quoted=True))
sqlglot/generator.py:2633:            target_name = exp.to_identifier(target_table.alias_or_name)
sqlglot/generator.py:3976:                alias.re
…[2308 chars elided]…
       exp.DynamicIdentifier: rename_func("IDENTIFIER"),
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
[tool_use Bash] {"command": "sed -n 1150,1185p sqlglot/parsers/snowflake.py; grep -n \"class DynamicIdentifier\" -A12 sqlglot/expressions/*.py; sed -n 1955,1970p sqlglot/generators/snowflake.py 2>/dev/null || sed -n 1955,1970p sqlglot/generator.py; grep -n \"DynamicIdentifier\\|Aliases\" sqlglot/parsers/snowflake.py sqlglot/parser.py | head -20", "description": "Inspect the Snowflake IDENTIFIER parser and related expression"}
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
…[1163 chars elided]…
essions/core.py-1820-    arg_types = {"except_": False, "replace": False, "rename": False, "ilike": False}
sqlglot/expressions/core.py-1821-
sqlglot/expressions/core.py-1822-    @property
sqlglot/expressions/core.py-1823-    def name(self) -> str:
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1169:            return self.expression(exp.DynamicIdentifier(this=identifier))
sqlglot/parser.py:8482:                exp.Aliases(
[tool_use Bash] {"command": "sed -n 8465,8495p sqlglot/parser.py; grep -n \"def anonymous_sql\" -A12 sqlglot/generator.py; grep -n \"def _parse_function_call\" -A5 sqlglot/parser.py | head; grep -n \"_parse_id_var()\\|_parse_id_var(\" sqlglot/parser.py | head -40", "description": "Inspect alias parsing and anonymous function generation"}
[tool_result]         # as an identifier (alias)
        if self._can_parse_limit_or_offset():
            return this

        # WINDOW is in ID_VAR_TOKENS, so it can be consumed as an implicit alias. Detect the
        # named-window clause shape (`WINDOW <ident> AS (...)`) and avoid swallowing it.
        if self._can_parse_named_window():
            return this

        any_token = self._match(TokenType.ALIAS)
        comments = self._prev_comments

        if explicit and not any_token:
            retu
…[3747 chars elided]…
kens)
7112:        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7170:        this = self._parse_id_var() or self._parse_primary()
7179:        return self._parse_id_var()
7444:        this = self._parse_id_var() if self._match(TokenType.CONSTRAINT) else None
7467:            exp.Constraint(this=self._parse_id_var(), expressions=self._parse_unnamed_constraints())
7507:        return self._parse_id_var(any_token=False)
7633:            this = self._parse_id_var()
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)', 'SELECT IDENTIFIER(\\'my_func\\')', 'SELECT IDENTIFIER(\\$fn)(1)', 'SELECT my_func(1)']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', str(e)[:80])\n\"; git log --oneline -3 -- sqlglot/parsers/snowflake.py; grep -rn \"IDENTIFIER\" tests/dialects/test_snowflake.py | head -20", "description": "Check AST for IDENTIFIER without call and existing tests"}
[tool_result] Select(
  expressions=[
    DynamicIdentifier(
      this=Parameter(
        this=Var(this=fn)))])
Select(
  expressions=[
    DynamicIdentifier(
      this=Literal(this='my_func', is_string=True))])
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Ali
Select(
  expressions=[
    Anonymous(
      this=my_func,
      expressions=[
        Literal(this=1, is_string=False)])])
523f7c255 feat(snowflake): support properties before column definitions in `CREATE` stateme
…[313 chars elided]…
lects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "sed -n 6944,7010p sqlglot/parser.py; grep -n \"def func\" -A25 sqlglot/generator.py | head -45; grep -n \"def normalize_func\" -A10 sqlglot/generator.py", "description": "Read function call parsing and generator func helpers"}
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
…[3477 chars elided]…
eturn sum(len(arg) for arg in args) > self.max_text_width
4620-
4621-    def format_time(
4622-        self,
1059:    def normalize_func(self, name: str) -> str:
1060-        if self.normalize_functions == "upper" or self.normalize_functions is True:
1061-            return name.upper()
1062-        if self.normalize_functions == "lower":
1063-            return name.lower()
1064-        return name
1065-
1066-    def indent(
1067-        self,
1068-        sql: str,
1069-        level: int = 0,
[tool_use Bash] {"command": "sed -n 7010,7050p sqlglot/parser.py; grep -n \"_parse_function_call\" sqlglot/parsers/snowflake.py sqlglot/parser.py | head; grep -n \"exp.Anonymous(this=exp\\.\\|Anonymous(this=[a-z_.]*Identifier\\|Anonymous(this=exp.to_identifier\" -r sqlglot | head", "description": "Read the rest of function call parsing and Anonymous usages"}
[tool_result]             function = functions.get(upper)
            known_function = function and not anonymous

            alias = not known_function or upper in self.FUNCTIONS_WITH_ALIASED_ARGS
            args = self._parse_function_args(alias)

            post_func_comments = self._curr.comments if self._curr else None
            if known_function and post_func_comments:
                # If the user-inputted comment "/* sqlglot.anonymous */" is following the function
                # call we'll con
…[939 chars elided]…
 result = func
            else:
                if token_type == TokenType.IDENTIFIER:
                    this = exp.Identifier(this=this, quoted=True).update_positions(token)

                result = self.expression(exp.Anonymous(this=this, expressions=args))

            result = result.update_positions(token)
sqlglot/parser.py:4229:        return self._parse_function_call()
sqlglot/parser.py:6929:        func = self._parse_function_call(
sqlglot/parser.py:6944:    def _parse_function_call(
[tool_use Bash] {"command": "grep -n \"def _parse_function_args\" -A8 sqlglot/parser.py; sed -n 7050,7062p sqlglot/parser.py; grep -n \"class SnowflakeParser\\|^from\\|^import\\|def _parse_id_var\" sqlglot/parsers/snowflake.py | head -20", "description": "Check function args parser signature and Snowflake parser imports"}
[tool_result] 6941:    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
6942-        return self._parse_csv(lambda: self._parse_lambda(alias=alias))
6943-
6944-    def _parse_function_call(
6945-        self,
6946-        functions: dict[str, t.Callable] | None = None,
6947-        anonymous: bool = False,
6948-        optional_parens: bool = True,
6949-        any_token: bool = False,
            result = result.update_positions(token)

        if isinstance(result, exp.Expr):
         
…[150 chars elided]…
ch_r_paren(result)
        return self._parse_window(result)

    def _to_prop_eq(self, expression: exp.Expr, index: int) -> exp.Expr:
        return expression
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import is_date_unit, is_int, seq_get
19:from sqlglot.tokens import TokenType
20:from sqlglot.trie import new_trie
330:class SnowflakeParser(parser.Parser):
1159:    def _parse_id_var(
[tool_use Bash] {"command": "sed -n 1155,1160p sqlglot/parsers/snowflake.py", "description": "Show insertion point in Snowflake parser"}
[tool_result]             table = table_from_rows

        return table

    def _parse_id_var(
        self,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return table\n\n    def _parse_id_var(\n        self,", "new_string": "        return table\n\n    def _parse_function_call(\n        self,\n        functions: dict[str, t.Callable] | None = None,\n   
…[265 chars elided]…
on invocation, e.g. IDENTIFIER($fn)(1, 2)\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            result = self.expression(\n                exp.Anonymous(this=func, expressions=self._parse_function_args())\n            )\n            self._match_r_paren(result)\n            return result\n\n        return func\n\n    def _parse_id_var(\n        self,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', 'SELECT IDENTIFIER(\\'my_func\\')(1, 2)', 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', str(ex)[:120])\n\"", "description": "Test the new parse and round-trip output"}
[tool_result] SET fn = 'add_one'
SELECT IDENTIFIER($FN)(41)
SELECT IDENTIFIER('MY_FUNC')(1, 2)
SELECT IDENTIFIER($FN)()
[assistant] The parse now works, but the outer `Anonymous` call uppercases the whole rendered callee, which turns `$fn` into `$FN` and `'my_func'` into `'MY_FUNC'`. I'll stop normalization from touching a dynamic callee.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py", "old_string": "        is_qualified = isinstance(parent, exp.Dot) and expression is parent.expression\n\n        return self.func(\n            self.sql(expression, \"this\"), *expression.expressions, normalize=not is_qualified\n   
…[59 chars elided]…
arent, exp.Dot) and expression is parent.expression\n        # Dynamic callees such as IDENTIFIER('x') carry literals that must not be normalized\n        is_dynamic = isinstance(expression.this, exp.DynamicIdentifier)\n\n        return self.func(\n            self.sql(expression, \"this\"),\n            *expression.expressions,\n            normalize=not (is_qualified or is_dynamic),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', 'SELECT IDENTIFIER(\\'my_func\\')(1, 2)', 'SELECT IDENTIFIER(\\$fn)()', 'SELECT IDENTIFIER(\\'my_func\\')(1, 2) AS x FROM t']:\n    e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Verify round-trips and run the full test suite"}
[tool_result] SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER('my_func')(1, 2) AS x FROM t
..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
..................................... [ 41%]
........................................................... [ 47%]
...........
…[235 chars elided]…
.......................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 49.41s
[assistant] All 1127 tests pass. Next I'll add Snowflake round-trip tests next to the existing `IDENTIFIER` tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162421-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -2; $P -m ruff check sqlglot tests/dialects/test_snowflake.py 2>&1 | tail -2; $P -m ruff format --check sqlglot tests/dialects/test_snowflake.py 2>&1 | tail -2; git status --short", "description": "Rerun tests, lint and format checks, and show changed files"}
[tool_result] ....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 49.31s
All checks passed!
177 files already formatted
 M sqlglot/generator.py
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[assistant] Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments:

```
SELECT IDENTIFIER($fn)(41)         -> SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2) -> SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()           -> SELECT IDENTIFIER($fn)()
```

The full suite passes (1127 tests), and `ruff check` and `ruff format --check` are clean. I didn't commit.

**Cause:** `IDENTIFIER(...)` in a function position parsed as a `DynamicIdentifier`, and the trailing `(41)` was left for the alias parser, which read it as a column al
…[195 chars elided]…
onymous` whose callee is that `DynamicIdentifier`.
- `sqlglot/generator.py`: `anonymous_sql` skips name normalization when the callee is a `DynamicIdentifier`. Without this, the whole rendered callee was uppercased, giving `IDENTIFIER($FN)` and `IDENTIFIER('MY_FUNC')`, which changes the semantics of the string literal.
- `tests/dialects/test_snowflake.py`: three `validate_identity` round-trips added next to the existing `IDENTIFIER` tests.

The generator change is in shared code, but it only triggers for `DynamicIdentifier` callees, so other dialects and quoted-identifier calls are unaffected.
