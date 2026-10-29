# trajectory base-1

final message:
Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments. The full test suite passes (1127 tests), and ruff lint and format are clean on the changed files. The changes are uncommitted in the worktree.

```
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
```

The cause was that `IDENTIFIER` maps to `exp.DynamicIdentifier`, so the trailing `(...)` was never treated as a call and got parsed as an alias list.

Changes:
- **`sqlglot/parsers/snowflake.py`**: a `_parse_function_call` override. When `IDENTIFIER(...)` is followed by `(`, it builds an `exp.Anonymous` whose callee is the `DynamicIdentifier`.
- **`sqlglot/generator.py`**: `anonymous_sql` skips name normalization when the callee is a `DynamicIdentifier`. Without this, `'my_func'` would have been upper-cased to `'MY_FUNC'`. The change is narrow and leaves quoted-callee behavior alone.
- **`tests/dialects/test_snowflake.py`**: four `validate_identity` cases covering the three forms above plus an aliased `FROM` variant.

One behavior to be aware of: transpiling a dynamic call to DuckDB resolves the literal name statically, so `IDENTIFIER('my_func')(1, 2)` becomes `my_func(1, 2)`. That matches how a plain `IDENTIFIER('x')` already transpiles, so I left it alone.

## events
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -50; grep -rn \"IDENTIFIER(\" tests/dialects/test_snowflake.py | head -20", "description": "Find IDENTIFIER handling in Snowflake and parser"}
[tool_result] sqlglot/parser.py:573:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:616:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:706:        TokenType.IDENTIFIER,
sqlglot/parser.py:799:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
sqlglot/parser.py:840:        TokenType.IDENTIFIER,
sqlglot/parser.py:1480:        TokenType.IDENTIFIER,
sqlglot/parser.py:4677:        while self._match_set(self.IDENTIFIER_TOKENS):
sqlglot/parser.py:4688:            
…[1252 chars elided]…
lects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e))\n    except Exception as ex: print('ERR', s, ex)\n\"", "description": "Reproduce the ParseError on the three queries"}
[tool_result] ERR SELECT IDENTIFIER($fn)(41) Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ERR SELECT IDENTIFIER('my_func')(1, 2) Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR SELECT IDENTIFIER($fn)() Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
[assistant] Reproduced all three. Now I'll find where `IDENTIFIER(...)` is parsed and where `Aliases` comes from.
[tool_use Bash] {"command": "grep -rn -i \"\\\"IDENTIFIER\\\"\\|Aliases\\|identifier\\b\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/expressions/*.py | grep -i \"identifier\\\"\\|aliases\" | head -40", "description": "Locate IDENTIFIER function and Aliases references"}
[tool_result] sqlglot/expressions/core.py:1648:        _sql_names (list): the SQL name (1st item in the list) and aliases (subsequent items) for this
sqlglot/expressions/core.py:1923:class Aliases(Expression):
sqlglot/expressions/core.py:1927:    def aliases(self) -> list[Expr]:
sqlglot/parser.py:1779:    # Whether string aliases are supported `SELECT COUNT(*) 'count'`
sqlglot/parser.py:1780:    STRING_ALIASES: t.ClassVar = False
sqlglot/parser.py:8481:            aliases = self.expression(
sqlglot/parser.py:
…[81 chars elided]…
r_paren(aliases)
sqlglot/parser.py:8488:            return aliases
sqlglot/parser.py:8491:            self.STRING_ALIASES and self._parse_string_as_identifier()
sqlglot/expressions/builders.py:139:        with_: dictionary of CTE aliases / select statements to include in a WITH clause.
sqlglot/expressions/query.py:10:    Aliases,
sqlglot/expressions/query.py:1654:            elif isinstance(e, Aliases):
sqlglot/expressions/query.py:1655:                selects.extend([a.name for a in e.aliases])
[tool_use Bash] {"command": "sed -n 8440,8500p sqlglot/parser.py; echo ----; grep -n \"_parse_identifier_function\\|IDENTIFIER\\|Identifier(\" sqlglot/parser.py | head; echo ----; grep -n \"IDENTIFIER\" sqlglot/tokens.py sqlglot/dialects/dialect.py | head; grep -rn \"def _parse_function\\b\\|def _parse_function_call\" sqlglot/parser.py", "description": "View alias-list parsing and locate function-call parsing"}
[tool_result]         if self._match_set(self.WINDOW_BEFORE_PAREN_TOKENS, advance=False):
            return self._parse_window(window, alias=alias)

        return window

    def _parse_partition_and_order(
        self,
    ) -> tuple[list[exp.Expr], exp.Expr | None]:
        return self._parse_partition_by(), self._parse_order()

    def _parse_window_spec(self) -> dict[str, str | exp.Expr | None]:
        self._match(TokenType.BETWEEN)

        return {
            "value": (
                (self._match
…[2788 chars elided]…
sVar[set[str]]
sqlglot/tokens.py:96:        cls._IDENTIFIERS = _convert_quotes(cls.IDENTIFIERS)
sqlglot/tokens.py:115:        cls._IDENTIFIER_ESCAPES = set(cls.IDENTIFIER_ESCAPES)
sqlglot/tokens.py:176:    IDENTIFIERS: t.ClassVar[list[str | tuple[str, str]]] = ['"']
sqlglot/tokens.py:186:    IDENTIFIER_ESCAPES: t.ClassVar[list[str]] = []
sqlglot/tokens.py:189:    HEREDOC_TAG_IS_IDENTIFIER = False
sqlglot/parser.py:6911:    def _parse_function(
sqlglot/parser.py:6944:    def _parse_function_call(
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.dialects.snowflake import Snowflake\nfor s in ['SELECT IDENTIFIER(\\$fn)', 'SELECT IDENTIFIER(\\'a\\')', 'SELECT IDENTIFIER(\\'a\\')(1)', 'SELECT foo(1)']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as ex: print('ERR', s, str(ex)[:100])\n\"; grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py sqlglot/tokens.py | grep -v \"IDENTIFIERS\\|_IDENT\" ; grep -rn \"\\\"IDENTIFIER\\\"\" sqlglot/ | head", "description": "Inspect AST for IDENTIFIER forms in Snowflake"}
[tool_result] Select(
  expressions=[
    DynamicIdentifier(
      this=Parameter(
        this=Var(this=fn)))])
Select(
  expressions=[
    DynamicIdentifier(
      this=Literal(this='a', is_string=True))])
ERR SELECT IDENTIFIER('a')(1) Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col:
Select(
  expressions=[
    Anonymous(
      this=foo,
      expressions=[
        Literal(this=1, is_string=False)])])
sqlglot/tokens.py:68:    IDENTIFIER_ESCAPES: t.ClassVar
…[25 chars elided]…
s.py:186:    IDENTIFIER_ESCAPES: t.ClassVar[list[str]] = []
sqlglot/generator.py:1965:        return self.func("IDENTIFIER", this)
sqlglot/parsers/clickhouse.py:555:            self._match_text_seq("IDENTIFIER") and "Identifier"
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1164:        if self._match_text_seq("IDENTIFIER", "("):
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
[assistant] `IDENTIFIER` maps to `exp.DynamicIdentifier` via the FUNCTIONS table, so the trailing `(...)` is never treated as a call. Let me check the existing Snowflake parser hooks and how a call on a non-name callee could be represented.
[tool_use Bash] {"command": "sed -n 1155,1180p sqlglot/parsers/snowflake.py; echo ----; grep -n \"class DynamicIdentifier\" -A8 sqlglot/expressions/*.py; echo ----; sed -n 6911,6990p sqlglot/parser.py; echo ----; grep -n \"def anonymous_sql\\|def _parse_column_ops\\|def _parse_primary\\|def _parse_function_call\" -A3 sqlglot/generator.py sqlglot/parser.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py | head -40", "description": "Inspect Snowflake IDENTIFIER parsing and function-call parser"}
[tool_result]             table = table_from_rows

        return table

    def _parse_id_var(
        self,
        any_token: bool = True,
        tokens: Collection[TokenType] | None = None,
    ) -> exp.Expr | None:
        if self._match_text_seq("IDENTIFIER", "("):
            identifier = (
                super()._parse_id_var(any_token=any_token, tokens=tokens) or self._parse_string()
            )
            self._match_r_paren()
            return self.expression(exp.DynamicIdentifier(this=identi
…[4783 chars elided]…
imeConstraint | None:
--
sqlglot/parser.py:7614:    def _parse_primary_key(
sqlglot/parser.py-7615-        self,
sqlglot/parser.py-7616-        wrapped_optional: bool = False,
sqlglot/parser.py-7617-        in_props: bool = False,
--
sqlglot/parser.py:8566:    def _parse_primary_or_var(self) -> exp.Expr | None:
sqlglot/parser.py-8567-        return self._parse_primary() or self._parse_var(any_token=True)
sqlglot/parser.py-8568-
sqlglot/parser.py-8569-    def _parse_null(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6990,7010p sqlglot/parser.py; echo ----; sed -n 3936,3950p sqlglot/generator.py; echo ----; grep -n \"class Anonymous\" -A6 sqlglot/expressions/*.py; echo ----; grep -n \"_parse_column_ops\\|def _parse_column(\" sqlglot/parser.py | head -5; grep -n \"class Snowflake\" sqlglot/parsers/snowflake.py | head -3; grep -n \"def _parse_function\\|def _parse_column_ops\\|def _parse_primary\" sqlglot/parsers/snowflake.py", "description": "Inspect remaining function-call parse and Anonymous shape"}
[tool_result]         else:
            subquery_predicate = self.SUBQUERY_PREDICATES.get(token_type)

            if subquery_predicate:
                expr = None
                if self._curr.token_type in self.SUBQUERY_TOKENS:
                    expr = self._parse_select()
                    self._match_r_paren()
                elif prev and prev.token_type in (TokenType.LIKE, TokenType.ILIKE):
                    # Backtrack one token since we've consumed the L_PAREN here. Instead, we'd like
        
…[1905 chars elided]…
e.py-1991-
sqlglot/expressions/core.py-1992-class CombinedAggFunc(AnonymousAggFunc):
sqlglot/expressions/core.py-1993-    arg_types = {"this": True, "expressions": False}
----
5927:        return self._parse_column_ops(this)
6162:            return self._parse_column_ops(interval)
6172:            return self._parse_column_ops(data_type)
6180:                this = self._parse_column_ops(this)
6210:                return self._parse_column_ops(data_type)
330:class SnowflakeParser(parser.Parser):
[assistant] `Anonymous.this` is typed as a string but the `name` property already handles expressions. Before choosing that route, I need to see how `self.func` normalizes the callee name, since it could upper-case the `'my_func'` literal inside `IDENTIFIER(...)`.
[tool_use Bash] {"command": "grep -n \"    def func(\" -A22 sqlglot/generator.py; grep -n \"def normalize_func\" -A8 sqlglot/generator.py; grep -n \"def _parse_function_call\" -B2 sqlglot/parsers/*.py | head; grep -n \"Anonymous(this=\" sqlglot/parsers/snowflake.py sqlglot/parser.py | head -5", "description": "Read generator func() and normalize_func"}
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
…[792 chars elided]…
,
sqlglot/parsers/snowflake.py:128:        return exp.Anonymous(this=name, expressions=args)
sqlglot/parsers/snowflake.py:141:            return exp.Anonymous(this=name, expressions=args)
sqlglot/parsers/snowflake.py:692:            else exp.Anonymous(this="TO_GEOGRAPHY", expressions=args)
sqlglot/parsers/snowflake.py:697:            else exp.Anonymous(this="TO_GEOMETRY", expressions=args)
sqlglot/parser.py:7048:                result = self.expression(exp.Anonymous(this=this, expressions=args))
[assistant] Using `Anonymous` with a `DynamicIdentifier` callee would route through `func(..., normalize=True)` and upper-case the `'my_func'` literal, so the generator side needs care too. Let me look at the generic call-argument parsing so the Snowflake path mirrors it.
[tool_use Bash] {"command": "sed -n 7010,7060p sqlglot/parser.py; echo ----; sed -n 1,30p sqlglot/parsers/snowflake.py | grep -n import; grep -n \"def _parse_function_call\\|def _parse_function(\" sqlglot/parsers/*.py", "description": "Read generic function-call argument parsing"}
[tool_result]             function = functions.get(upper)
            known_function = function and not anonymous

            alias = not known_function or upper in self.FUNCTIONS_WITH_ALIASED_ARGS
            args = self._parse_function_args(alias)

            post_func_comments = self._curr.comments if self._curr else None
            if known_function and post_func_comments:
                # If the user-inputted comment "/* sqlglot.anonymous */" is following the function
                # call we'll con
…[1547 chars elided]…
t annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import is_date_unit, is_int, seq_get
19:from sqlglot.tokens import TokenType
20:from sqlglot.trie import new_trie
23:    from collections.abc import Collection
25:    from sqlglot._typing import B, E
26:    from sqlglot.dialects.dialect import Dialect
sqlglot/parsers/clickhouse.py:689:    def _parse_function(
sqlglot/parsers/teradata.py:170:    def _parse_function(
[assistant] The generic path already puts an `Identifier` (for quoted names) into `Anonymous.this`, so an expression callee has precedent. Let me check how that quoted-callee case currently generates, since it shares the `normalize` path I need to avoid for `IDENTIFIER`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT \\\"foo\\\"(1)', read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT IDENTIFIER('my_func')\\\", read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT IDENTIFIER(\\$fn)\\\", read='snowflake', write='duckdb'))\n\"; grep -n \"class Anonymous\\|Anonymous(this=\" sqlglot/expressions/*.py | head -3; grep -rn \"normalize_functions\" sqlglot/generator.py | head -3", "description": "Check quoted-callee and IDENTIFIER generation baselines"}
[tool_result] IDENTIFIER() with non-literal arguments is not supported
['SELECT "FOO"(1)']
["SELECT IDENTIFIER('my_func')"]
['SELECT IDENTIFIER($fn)']
sqlglot/expressions/builders.py:988:        function = Anonymous(this=name, **kwargs)
sqlglot/expressions/core.py:1978:class Anonymous(Expression, Func):
sqlglot/expressions/core.py:1987:class AnonymousAggFunc(Expression, AggFunc):
sqlglot/generator.py:115:        normalize_functions: How to normalize function names. Possible values are:
sqlglot/generator.py:849:        "normalize_functions",
sqlglot/generator.py:874:        normalize_functions: str | bool | None = None,
[assistant] Baseline confirmed: the callee gets upper-cased (`"foo"` becomes `"FOO"`), and `IDENTIFIER('my_func')` stays intact only because it isn't a callee yet. My plan:

1. **Parser (Snowflake):** after `IDENTIFIER(...)` is parsed as a function, a following `(` becomes an `exp.Anonymous` call whose `this` is the `DynamicIdentifier`.
2. **Generator (base):** don't normalize the callee when it's a `DynamicIdentifier`, so the literal inside isn't upper-cased. This is narrow and leaves quoted-callee behavior alone.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _parse_show_snowflake(", "new_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _
…[440 chars elided]…
   # Dynamic invocation, e.g. IDENTIFIER($fn)(41), where the callee is resolved at runtime\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            args = self._parse_function_args()\n            self._match_r_paren()\n            return self.expression(exp.Anonymous(this=func, expressions=args))\n\n        return func\n\n    def _parse_show_snowflake("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py", "old_string": "        is_qualified = isinstance(parent, exp.Dot) and expression is parent.expression\n\n        return self.func(\n            self.sql(expression, \"this\"), *expression.expressions, normalize=not is_qualified\n   
…[69 chars elided]…
.Dot) and expression is parent.expression\n        # A dynamic callee such as IDENTIFIER('my_func') carries a literal that must not be normalized\n        is_dynamic = isinstance(expression.this, exp.DynamicIdentifier)\n\n        return self.func(\n            self.sql(expression, \"this\"),\n            *expression.expressions,\n            normalize=not (is_qualified or is_dynamic),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', 'SELECT IDENTIFIER(\\$fn)(41) AS r FROM t', \\\"SELECT IDENTIFIER('my_func')(1, 2) x\\\"]:\n    try:\n        out = sqlglot.transpile(s, read='snowflake', write='snowflake')[0]; print(out)\n    except Exception as ex: print('ERR', s, str(ex)[:150])\nprint(sqlglot.transpile(\\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", read='snowflake', write='duckdb'))\n\"", "description": "Verify the three queries round-trip in Snowflake"}
[tool_result] SET fn = 'add_one'
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER($fn)(41) AS r FROM t
SELECT IDENTIFIER('my_func')(1, 2) AS x
['SELECT my_func(1, 2)']
[assistant] All three forms now round-trip in Snowflake. The DuckDB output resolves the literal name statically, which matches how `IDENTIFIER('x')` already transpiles, so I'm leaving that as-is. Next I'll add regression tests next to the existing `IDENTIFIER` tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "offset": 768, "limit": 5}
[tool_result] 768	        self.validate_identity("SELECT KURTOSIS(x)")
769	        self.validate_identity("SELECT KURTOSIS(x) OVER (PARTITION BY 1)")
770	        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
771	        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
772	        self.validate_identity("INITCAP('iqamqinterestedqinqthisqtopic', 'q')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41) AS r FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105933-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now the project's check command, run on the full suite.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
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
1127 passed, 18278 subtests passed in 53.70s
[assistant] The full suite passes (1127 tests). Let me also run the linter and formatter on the changed files, since the project's guidelines call for it.
[tool_use Bash] {"command": "PYDIR=<work>/env-sqlglot/bin; ls $PYDIR | grep -i \"ruff\\|mypy\"; $PYDIR/ruff check sqlglot/parsers/snowflake.py sqlglot/generator.py tests/dialects/test_snowflake.py 2>&1 | tail -3; $PYDIR/ruff format --check sqlglot/parsers/snowflake.py sqlglot/generator.py tests/dialects/test_snowflake.py 2>&1 | tail -3; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] dmypy
mypy
mypyc
ruff
All checks passed!
3 files already formatted
 M sqlglot/generator.py
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[assistant] Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments. The full test suite passes (1127 tests), and ruff lint and format are clean on the changed files. The changes are uncommitted in the worktree.

```
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
```

The cause was that `IDENTIFIER` maps to `exp.DynamicIdentifier`, so the trailing `(...)` was never treated as a call and got parsed as an alias list.

Changes:
- **`sqlglot/parsers/snowflake.py`**: a `_parse_function_call` override. When `IDENTIFI
…[125 chars elided]…
**: `anonymous_sql` skips name normalization when the callee is a `DynamicIdentifier`. Without this, `'my_func'` would have been upper-cased to `'MY_FUNC'`. The change is narrow and leaves quoted-callee behavior alone.
- **`tests/dialects/test_snowflake.py`**: four `validate_identity` cases covering the three forms above plus an aliased `FROM` variant.

One behavior to be aware of: transpiling a dynamic call to DuckDB resolves the literal name statically, so `IDENTIFIER('my_func')(1, 2)` becomes `my_func(1, 2)`. That matches how a plain `IDENTIFIER('x')` already transpiles, so I left it alone.
