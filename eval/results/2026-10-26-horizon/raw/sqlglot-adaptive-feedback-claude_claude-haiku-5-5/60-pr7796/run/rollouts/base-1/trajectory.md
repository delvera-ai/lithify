# trajectory base-1

final message:
Snowflake now parses `IDENTIFIER(...)` followed by an argument list, and all three forms round-trip unchanged. The full suite ends with `SUMMARY: 1127 passed, 18280 subtests passed in 53.81s` and `EXIT: 0`, run after my last edit. I haven't committed anything.

```
SELECT IDENTIFIER($fn)(41)            -> SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)    -> SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()              -> SELECT IDENTIFIER($fn)()
```

**What changed**
- **`sqlglot/expressions/core.py`**: a new `exp.DynamicFunction` node with `this` (the callee) and `expressions` (the arguments). I added a node because `exp.Anonymous` takes a string name, and the callee here is an expression.
- **`sqlglot/generator.py`**: `dynamicfunction_sql` emits the callee and argument list. It is auto-discovered by name, so no `TRANSFORMS` entry is needed.
- **`sqlglot/parsers/snowflake.py`**: a `_parse_function_call` override. When the call returns a `DynamicIdentifier` and a `(` follows, it parses the arguments into `DynamicFunction`. Zero arguments are allowed.
- **`tests/dialects/test_snowflake.py`**: node-class assertions for the `$fn` and literal forms, round-trips for the zero-argument form and a `FROM IDENTIFIER('t') AS x (a, b)` alias guard, and a DuckDB transpile check.

**Results**
- The Snowflake dialect test file passes (97 tests). `ast_check.py` reports `DynamicFunction` for each requested form, with no `[DIFFERS]`, `[FUNCTION CHANGED]` or `[WORDS DROPPED]` lines.
- The literal form transpiles to `my_func(1, 2)` in DuckDB and Postgres, since the name is resolved statically. I did not execute the query.
- The `$fn` form has no static name, so DuckDB and Postgres emit `IDENTIFIER($fn)(41)` with the existing "non-literal arguments" warning, as they already did for `IDENTIFIER($fn)`.

**Decision for you:** the override only builds a call when `optional_parens` is true. The table-part parser passes `False`, and without that gate `FROM IDENTIFIER('t') (a, b)` would stop being a table alias with a column list. I checked the baseline and that alias case already works, so it stays as it was. Say if you'd rather handle that case another way.

## events
[assistant] I'll start by reading the dialect-functions skill and the Snowflake parser to see how `IDENTIFIER` is handled today.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md; echo ----; grep -rn \"IDENTIFIER\" sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/parser.py sqlglot/expressions/*.py | head -50", "description": "Read skill and find IDENTIFIER handling"}
[tool_result] ---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — replacing an in
…[21750 chars elided]…
str) and SAFE_IDENTIFIER_RE.match(name):
sqlglot/expressions/builders.py:778:            if identify or not SAFE_IDENTIFIER_RE.match(part.name)
sqlglot/expressions/core.py:2792:SAFE_IDENTIFIER_RE: t.Pattern[str] = re.compile(r"^[_a-zA-Z][\w]*$")
sqlglot/expressions/core.py:2825:            quoted=not SAFE_IDENTIFIER_RE.match(name) if quoted is None else quoted,
sqlglot/expressions/core.py:3028:    # We don't set the "alias" arg for Window expressions, because that would add an IDENTIFIER node in
[tool_use Bash] {"command": "cat <work>/env-sqlglot/../memory.md 2>/dev/null; ls .lithify/harness/; ls .lithify/harness/skills/", "description": "Read skill, find IDENTIFIER handling, list harness"}
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
sqlglot-clause-element-lists
sqlglot-data-types
sqlglot-ddl-statements
sqlglot-dialect-functions
sqlglot-json-table
sqlglot-lineage
sqlglot-null-ordering
sqlglot-optimizer-rewrites
sqlglot-parser-options
sqlglot-query-modifiers
sqlglot-time-parsing
sqlglot-upsert-on-conflict
[assistant] The harness requires reading matching skills before editing, and I've read `sqlglot-dialect-functions`. Next I'll look at the existing `IDENTIFIER` code and reproduce the error.
[tool_use Bash] {"command": "sed -n 1150,1200p sqlglot/parsers/snowflake.py; echo ----; grep -n \"class DynamicIdentifier\" -A8 sqlglot/expressions/*.py; echo ----; grep -n \"DynamicIdentifier\" -r sqlglot tests | head; echo ----; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', \\\"SELECT IDENTIFIER('a.b')\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, ex)\n\"", "description": "Inspect Snowflake IDENTIFIER parsing and reproduce"}
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
…[2524 chars elided]…
IER($fn)([4m41[0m)
ERR SELECT IDENTIFIER('my_func')(1, 2) Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR SELECT IDENTIFIER($fn)() Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
Select(
  expressions=[
    DynamicIdentifier(
      this=Literal(this='a.b', is_string=True))])
SELECT IDENTIFIER('a.b')
[assistant] The current code treats `IDENTIFIER(...)` as a name, or as a function that returns a `DynamicIdentifier` with no call. Next I'll find where base parsing builds function calls so I can attach an argument list.
[tool_use Bash] {"command": "grep -n \"def _parse_function\\b\\|def _parse_function_call\\|def _parse_primary\\|FUNCTION_PARSERS\\b\" sqlglot/parser.py | head -30; echo ----; grep -n \"def _parse_function_call\" -A75 sqlglot/parser.py | head -120", "description": "Locate base function-call parsing"}
[tool_result] 1470:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
1488:    FUNCTION_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
5433:        self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
5437:        self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
6616:            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
6866:    def _parse_primary(self) -> exp.Expr | None:
6911:    def _parse_function(
6944:    def _parse_function_call(
6962:        parser = self.NO_P
…[3025 chars elided]…
t anonymous
7012-
7013-            alias = not known_function or upper in self.FUNCTIONS_WITH_ALIASED_ARGS
7014-            args = self._parse_function_args(alias)
7015-
7016-            post_func_comments = self._curr.comments if self._curr else None
7017-            if known_function and post_func_comments:
7018-                # If the user-inputted comment "/* sqlglot.anonymous */" is following the function
7019-                # call we'll construct it as exp.Anonymous, even if it's "known"
[tool_use Bash] {"command": "sed -n 7019,7060p sqlglot/parser.py; echo ----; sed -n 6911,6943p sqlglot/parser.py; echo ----; grep -n \"def anonymous_sql\" -A12 sqlglot/generator.py; grep -n \"class Anonymous\" -A5 sqlglot/expressions/functions.py sqlglot/expressions/core.py | head -20", "description": "Read rest of function-call parsing and Anonymous"}
[tool_result]                 # call we'll construct it as exp.Anonymous, even if it's "known"
                if any(
                    comment.lstrip().startswith(exp.SQLGLOT_ANONYMOUS)
                    for comment in post_func_comments
                ):
                    known_function = False

            if alias and known_function:
                args = self._kv_to_prop_eq(args)

            if known_function:
                func_builder = t.cast(t.Callable, function)

                # mypyc 
…[3018 chars elided]…
xpressions/core.py-1981-
sqlglot/expressions/core.py-1982-    @property
sqlglot/expressions/core.py-1983-    def name(self) -> str:
--
sqlglot/expressions/core.py:1987:class AnonymousAggFunc(Expression, AggFunc):
sqlglot/expressions/core.py-1988-    arg_types = {"this": True, "expressions": False}
sqlglot/expressions/core.py-1989-    is_var_len_args = True
sqlglot/expressions/core.py-1990-
sqlglot/expressions/core.py-1991-
sqlglot/expressions/core.py-1992-class CombinedAggFunc(AnonymousAggFunc):
[assistant] Base parsing builds `exp.Anonymous` for unknown names, and `anonymous_sql` already calls `self.sql(expression, "this")`, so `this` can be an expression. I need to check whether `self.func` would case-normalize that rendered callee string, which would break `$fn`.
[tool_use Bash] {"command": "grep -n \"    def func(\" -A22 sqlglot/generator.py; grep -n \"def normalize_func\" -A8 sqlglot/generator.py; grep -n \"def dynamicidentifier_sql\" -A4 sqlglot/generator.py; grep -n \"Anonymous\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/normalize_identifiers.py sqlglot/expressions/core.py | head", "description": "Inspect generator func helper"}
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
…[829 chars elided]…
self, expression: exp.DynamicIdentifier) -> str:
1961-        this = expression.this
1962-        if this and this.is_string:
1963-            return maybe_parse(this.name).sql(self.dialect)
1964-        self.unsupported("IDENTIFIER() with non-literal arguments is not supported")
sqlglot/expressions/core.py:1978:class Anonymous(Expression, Func):
sqlglot/expressions/core.py:1987:class AnonymousAggFunc(Expression, AggFunc):
sqlglot/expressions/core.py:1992:class CombinedAggFunc(AnonymousAggFunc):
[assistant] Here's the picture. Snowflake already emits `DynamicIdentifier` as `IDENTIFIER(...)`. The parse breaks because the `(41)` after the call is left unconsumed, and the function call parser has no node for "call a dynamic name". I'll add a small `DynamicFunction` node that wraps the `DynamicIdentifier` callee and its argument list. The Snowflake parser will build it when `IDENTIFIER(...)` is directly followed by `(`. I'll check the generator context first, then make the edits.
[tool_use Bash] {"command": "sed -n 1955,1968p sqlglot/generator.py; echo ----; sed -n 1805,1813p sqlglot/expressions/core.py; echo ----; grep -n \"_parse_function_call\\|def _parse_id_var\" sqlglot/parsers/snowflake.py | head; grep -n \"^from\\|^import\" sqlglot/parsers/snowflake.py | head -20", "description": "Read generator, node, and parser context"}
[tool_result]         index = "INDEX " if not table else ""

        params = self.sql(expression, "params")
        return f"{unique}{primary}{amp}{index}{name}{table}{params}"

    def dynamicidentifier_sql(self, expression: exp.DynamicIdentifier) -> str:
        this = expression.this
        if this and this.is_string:
            return maybe_parse(this.name).sql(self.dialect)
        self.unsupported("IDENTIFIER() with non-literal arguments is not supported")
        return self.func("IDENTIFIER", this)
…[98 chars elided]…
----
    @property
    def output_name(self) -> str:
        return self.name


# https://docs.snowflake.com/en/sql-reference/identifier-literal
class DynamicIdentifier(Expression, Func):
    pass

----
1159:    def _parse_id_var(
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import is_date_unit, is_int, seq_get
19:from sqlglot.tokens import TokenType
20:from sqlglot.trie import new_trie
[assistant] Now the edits: the node, the generator method (auto-discovered by name), and the Snowflake parser hook.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/expressions/core.py", "old_string": "# https://docs.snowflake.com/en/sql-reference/identifier-literal\nclass DynamicIdentifier(Expression, Func):\n    pass\n", "new_string": "# https://docs.snowflake.com/en/sql-reference/identifier-literal\nclass DynamicIdentifier(Expression, Func):\n    pass\n\n\n# A call whose callee is a dynamically resolved name, e.g. IDENTIFIER($fn)(1, 2)\nclass DynamicFunction(Expression, Func):\n    arg_types = {\"this\": True, \"expressions\": False}\n    is_var_len_args = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/expressions/core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py", "old_string": "        self.unsupported(\"IDENTIFIER() with non-literal arguments is not supported\")\n        return self.func(\"IDENTIFIER\", this)\n", "new_string": "        self.unsupported(\"IDENTIFIER() with non-literal arguments is not supported\")\n        return self.func(\"IDENTIFIER\", this)\n\n    def dynamicfunction_sql(self, expression: exp.DynamicFunction) -> str:\n        return self.func(\n            self.sql(expression, \"this\"), *expression.expressions, normalize=False\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_id_var(\n        self,\n        any_token: bool = True,\n        tokens: Collection[TokenType] | None = None,\n    ) -> exp.Expr | None:", "new_string": "    def _parse_function_call(\n        s
…[439 chars elided]…
amicIdentifier) and self._match(TokenType.L_PAREN):\n            args = self._parse_function_args()\n            self._match_r_paren()\n            return self.expression(exp.DynamicFunction(this=func, expressions=args))\n\n        return func\n\n    def _parse_id_var(\n        self,\n        any_token: bool = True,\n        tokens: Collection[TokenType] | None = None,\n    ) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Next I'll run the probe against the three example statements and check the node shape.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', \\\"SELECT IDENTIFIER('a.b')\\\", \\\"SELECT * FRO
…[35 chars elided]…
ROM IDENTIFIER('t') (a, b)\\\", \\\"SELECT IDENTIFIER('f')(1) AS r FROM IDENTIFIER('t')\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(s, '->', e.sql('snowflake'))\n        print(repr(e.selects[0]) if isinstance(e, exp.Select) else '')\n    except Exception as ex: print('ERR', s, ex)\n\" 2>&1 | head -60", "description": "Probe the new Snowflake IDENTIFIER call parsing"}
[tool_result] SELECT IDENTIFIER($fn)(41) -> SELECT IDENTIFIER($fn)(41)
DynamicFunction(
  this=DynamicIdentifier(
    this=Parameter(
      this=Var(this=fn))),
  expressions=[
    Literal(this=41, is_string=False)])
SELECT IDENTIFIER('my_func')(1, 2) -> SELECT IDENTIFIER('my_func')(1, 2)
DynamicFunction(
  this=DynamicIdentifier(
    this=Literal(this='my_func', is_string=True)),
  expressions=[
    Literal(this=1, is_string=False),
    Literal(this=2, is_string=False)])
SELECT IDENTIFIER($fn)() -> SELECT ID
…[184 chars elided]…
=Literal(this='a.b', is_string=True))
SELECT * FROM t AS x (a, b) -> SELECT * FROM t AS x(a, b)
Star()
SELECT * FROM IDENTIFIER('t') (a, b) -> SELECT * FROM IDENTIFIER('t')(a, b)
Star()
SELECT IDENTIFIER('f')(1) AS r FROM IDENTIFIER('t') -> SELECT IDENTIFIER('f')(1) AS r FROM IDENTIFIER('t')
Alias(
  this=DynamicFunction(
    this=DynamicIdentifier(
      this=Literal(this='f', is_string=True)),
    expressions=[
      Literal(this=1, is_string=False)]),
  alias=Identifier(this=r, quoted=False))
[assistant] The three requested forms now parse into `DynamicFunction`. One side effect needs checking: `FROM IDENTIFIER('t') (a, b)` now renders as a call. I'll compare against the unmodified HEAD so I know whether that case worked before.
[tool_use Bash] {"command": "D=$(mktemp -d /tmp/base-sqlglot.XXXX); git archive HEAD sqlglot | tar -x -C \"$D\"; PY=<work>/env-sqlglot/bin/python; cd \"$D\" && PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM t AS x (a, b)\\\", \\\"SELECT * FROM IDENTIFIER('t') (a, b)\\\", \\\"SELECT * FROM IDENTIFIER('t') AS (a, b)\\\", \\\"SELECT * FROM IDENTIFIER('t') AS x (a, b)\\\"]:\n    try: print(s, '->', sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', s, ex)\n\"; cd - >/dev/null; rm -rf \"$D\"", "description": "Compare table-alias behavior against HEAD baseline"}
[tool_result] SELECT * FROM t AS x (a, b) -> SELECT * FROM t AS x(a, b)
SELECT * FROM IDENTIFIER('t') (a, b) -> SELECT * FROM IDENTIFIER('t') AS _t0(a, b)
SELECT * FROM IDENTIFIER('t') AS (a, b) -> SELECT * FROM IDENTIFIER('t') AS _t0(a, b)
SELECT * FROM IDENTIFIER('t') AS x (a, b) -> SELECT * FROM IDENTIFIER('t') AS x(a, b)
[assistant] HEAD turns `FROM IDENTIFIER('t') (a, b)` into a table alias with a column list, and my change breaks that. Table context needs to stay as it was. I'll find how the table-part parser reaches the function call.
[tool_use Bash] {"command": "grep -n \"def _parse_table_part\\b\" -A25 sqlglot/parser.py | head -45", "description": "Read table-part parser path"}
[tool_result] 4664:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
4665-        return (
4666-            (not schema and self._parse_function(optional_parens=False))
4667-            or self._parse_id_var(any_token=False)
4668-            or self._parse_string_as_identifier()
4669-            or self._parse_placeholder()
4670-        )
4671-
4672-    def _parse_table_parts_fast(self) -> exp.Table | None:
4673-        index = self._index
4674-        parts: list[exp.Identifier] | Non
…[105 chars elided]…
.IDENTIFIER_TOKENS):
4678-            token = self._prev
4679-            comments = self._prev_comments
4680-
4681-            has_dot = self._match(TokenType.DOT)
4682-            curr_tt = self._curr.token_type
4683-
4684-            if not has_dot:
4685-                if curr_tt in self.TABLE_POSTFIX_TOKENS:
4686-                    self._retreat(index)
4687-                    return None
4688-            elif curr_tt not in self.IDENTIFIER_TOKENS:
4689-                self._retreat(index)
[assistant] The table path calls `_parse_function(optional_parens=False)`. Before choosing a gate, I'll check which callers pass that flag.
[tool_use Bash] {"command": "grep -rn \"optional_parens=False\" sqlglot/ | head; grep -rn \"_parse_table_part(\" sqlglot/parser.py sqlglot/parsers/ | head", "description": "Find callers passing optional_parens=False"}
[tool_result] sqlglot/parser.py:4666:            (not schema and self._parse_function(optional_parens=False))
sqlglot/parser.py:3599:                into=self._match(TokenType.INTO) and self._parse_table_part(),
sqlglot/parser.py:4664:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
sqlglot/parser.py:4747:        table: exp.Expr | str | None = self._parse_table_part(schema=schema)
sqlglot/parser.py:4753:                    exp.Dot(this=table, expression=self._parse_table_part(schema=schema))
sqlglot/parser.py:4759:                table = self._parse_table_part(schema=schema) or ""
sqlglot/parsers/bigquery.py:381:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
sqlglot/parsers/bigquery.py:382:        this = super()._parse_table_part(schema=schema) or self._parse_number()
[assistant] Only the table-part parser passes `optional_parens=False`. In that context a following parenthesised list is a column alias, not a call, so I'll gate the call parse on that flag with a short comment saying why.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):", "new_string": "        # In a table part (optional_parens=False), a following paren list is a column alias\n        if (\n            optional_parens\n            and isinstance(func, exp.DynamicIdentifier)\n            and self._match(TokenType.L_PAREN)\n        ):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', \\\"SELECT * FROM IDENTIFIER('t') (a, b)\\\", \\\
…[229 chars elided]…
ake').sql('snowflake'))\n    except Exception as ex: print('ERR', s, ex)\n\"; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\"]:\n    print(sqlglot.transpile(s, read='snowflake', write='duckdb'), sqlglot.transpile(s, read='snowflake', write='postgres'))\n\"", "description": "Re-probe Snowflake forms and table alias cases"}
[tool_result] SET fn = 'add_one' -> SET fn = 'add_one'
SELECT IDENTIFIER($fn)(41) -> SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2) -> SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)() -> SELECT IDENTIFIER($fn)()
SELECT * FROM IDENTIFIER('t') (a, b) -> SELECT * FROM IDENTIFIER('t') AS _t0(a, b)
SELECT * FROM IDENTIFIER('t') AS x (a, b) -> SELECT * FROM IDENTIFIER('t') AS x(a, b)
SELECT IDENTIFIER('f')(1) AS r FROM IDENTIFIER('t') -> SELECT IDENTIFIER('f')(1) AS r FROM IDENTIFIER('t')
SELECT IDENTIFIER($fn)(IDENTIFIER('a')(1), 2 + 3) -> SELECT IDENTIFIER($fn)(IDENTIFIER('a')(1), 2 + 3)
IDENTIFIER() with non-literal arguments is not supported
IDENTIFIER() with non-literal arguments is not supported
['SELECT IDENTIFIER($fn)(41)'] ['SELECT IDENTIFIER($fn)(41)']
['SELECT my_func(1, 2)'] ['SELECT my_func(1, 2)']
[assistant] The table-alias case is back to HEAD's behavior, the three requested forms round-trip, and the literal form transpiles to DuckDB and Postgres as `my_func(1, 2)`. Next I'll find the existing `IDENTIFIER` tests and run the harness's AST checker on the forms.
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" tests/dialects/test_snowflake.py | head -20; ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/; sed -n 1,40p .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py | head -50", "description": "Find existing IDENTIFIER tests and checker script"}
[tool_result] 770:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
ast_check.py
into_dialec
…[1543 chars elided]…
r sqlglot not importable from the current directory;
4 = parsed, but at least one statement has FUNCTION CHANGED or WORDS DROPPED.
"""
import argparse
import os
import re
import sys
from collections import Counter

_CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_WORD = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_STRING = re.compile(r"'(?:[^']|'')*'")
_ELIDED = {"ASC", "AS", "INNER", "OUTER", "ALL"}


def _norm(sql: str) -> str:
    return " ".join(sql.upper().split()).rstrip(";").rstrip()
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read snowflake --write duckdb,postgres,snowflake \"SET fn = 'add_one'\" \"SELECT IDENTIFIER(\\$fn)(41)\" \"SELECT IDENTIFIER('my_func')(1, 2)\" \"SELECT IDENTIFIER(\\$fn)()\" 2>&1 | head -60; echo \"EXIT $?\"; sed -n 765,772p tests/dialects/test_snowflake.py", "description": "Run AST checker on the requested Snowflake forms"}
[tool_result] IDENTIFIER() with non-literal arguments is not supported
IDENTIFIER() with non-literal arguments is not supported
IDENTIFIER() with non-literal arguments is not supported
IDENTIFIER() with non-literal arguments is not supported
== SET fn = 'add_one'
  node: Set
  snowflake (round-trip): SET fn = 'add_one'
  duckdb: SET VARIABLE fn = 'add_one'
  postgres: SET fn = 'add_one'
  snowflake: SET fn = 'add_one'
== SELECT IDENTIFIER($fn)(41)
  node: DynamicFunction
  snowflake (round-trip): SELECT IDENT
…[623 chars elided]…
       "SELECT STDDEV_SAMP(x) OVER (PARTITION BY 1)", "SELECT STDDEV(x) OVER (PARTITION BY 1)"
        )
        self.validate_identity("SELECT KURTOSIS(x)")
        self.validate_identity("SELECT KURTOSIS(x) OVER (PARTITION BY 1)")
        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
        self.validate_identity("INITCAP('iqamqinterestedqinqthisqtopic', 'q')")
[assistant] The checker reports the expected node (`DynamicFunction`) for every form, with no dropped words or changed functions. Next I'll add regression tests beside the existing `IDENTIFIER` tests, checking the test file's imports and the enclosing test method first.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_snowflake.py; grep -n \"    def test_\" tests/dialects/test_snowflake.py | awk -F: '$1<771' | tail -1", "description": "Check test imports and enclosing test method"}
[tool_result] from unittest import mock

from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify_columns import quote_identifiers
from sqlglot.parser import logger as parser_logger
from tests.dialects.test_dialect import Validator


class TestSnowflake(Validator):
    maxDiff = None
15:    def test_snowflake(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM
…[449 chars elided]…
NTIFIER('t')\")\n        self.validate_identity(\"SELECT * FROM IDENTIFIER('t') AS x (a, b)\", \"SELECT * FROM IDENTIFIER('t') AS x(a, b)\")\n        self.validate_all(\n            \"SELECT IDENTIFIER('my_func')(1, 2)\",\n            write={\n                \"snowflake\": \"SELECT IDENTIFIER('my_func')(1, 2)\",\n                \"duckdb\": \"SELECT my_func(1, 2)\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120759-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] I'll format the touched files with the project's ruff, then run the Snowflake dialect tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parsers/snowflake.py sqlglot/generator.py sqlglot/expressions/core.py tests/dialects/test_snowflake.py && $PY -m ruff check sqlglot/parsers/snowflake.py sqlglot/generator.py sqlglot/expressions/core.py tests/dialects/test_snowflake.py; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -30", "description": "Format, lint, and run Snowflake dialect tests"}
[tool_result] 2 files reformatted, 2 files left unchanged
All checks passed!
................. [ 17%]
................................................................................                                                              [100%]
97 passed, 1570 subtests passed in 0.63s
[This command modified 2 files you've previously read: sqlglot/generator.py, tests/dialects/test_snowflake.py. Call Read before editing.]
[assistant] The Snowflake tests pass (97 passed). The formatter reformatted two files, so I'll check its diff touched only my lines.
[tool_use Bash] {"command": "git diff --stat; git diff sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/expressions/core.py", "description": "Review the full diff after formatting"}
[tool_result]  sqlglot/expressions/core.py      |  6 ++++++
 sqlglot/generator.py             |  3 +++
 sqlglot/parsers/snowflake.py     | 26 ++++++++++++++++++++++++++
 tests/dialects/test_snowflake.py | 19 +++++++++++++++++++
 4 files changed, 54 insertions(+)
diff --git a/sqlglot/expressions/core.py b/sqlglot/expressions/core.py
index c2cbee6d4..a12076e8c 100644
--- a/sqlglot/expressions/core.py
+++ b/sqlglot/expressions/core.py
@@ -1812,6 +1812,12 @@ class DynamicIdentifier(Expression, Func):
     pass
 

…[1642 chars elided]…
ble part (optional_parens=False), a following paren list is a column alias
+        if (
+            optional_parens
+            and isinstance(func, exp.DynamicIdentifier)
+            and self._match(TokenType.L_PAREN)
+        ):
+            args = self._parse_function_args()
+            self._match_r_paren()
+            return self.expression(exp.DynamicFunction(this=func, expressions=args))
+
+        return func
+
     def _parse_id_var(
         self,
         any_token: bool = True,
[assistant] The diff is limited to my changes. Next is the full suite, run in the foreground as the harness requires, so I can quote its summary line.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -30", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-16:38:40 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-b645cbd8fc.log
ELAPSED: 54s
SUMMARY: 1127 passed, 18280 subtests passed in 53.81s
EXIT: 0
[assistant] Snowflake now parses `IDENTIFIER(...)` followed by an argument list, and all three forms round-trip unchanged. The full suite ends with `SUMMARY: 1127 passed, 18280 subtests passed in 53.81s` and `EXIT: 0`, run after my last edit. I haven't committed anything.

```
SELECT IDENTIFIER($fn)(41)            -> SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)    -> SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()              -> SELECT IDENTIFIER($fn)()
```

**What changed**
- **`sqlglot/expressions/core.py`**: a new `exp.DynamicFunction` node with `this` (the callee) and `ex
…[995 chars elided]…
he name is resolved statically. I did not execute the query.
- The `$fn` form has no static name, so DuckDB and Postgres emit `IDENTIFIER($fn)(41)` with the existing "non-literal arguments" warning, as they already did for `IDENTIFIER($fn)`.

**Decision for you:** the override only builds a call when `optional_parens` is true. The table-part parser passes `False`, and without that gate `FROM IDENTIFIER('t') (a, b)` would stop being a table alias with a column list. I checked the baseline and that alias case already works, so it stays as it was. Say if you'd rather handle that case another way.
