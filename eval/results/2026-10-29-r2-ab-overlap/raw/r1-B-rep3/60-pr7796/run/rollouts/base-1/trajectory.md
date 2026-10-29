# trajectory base-1

final message:
Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, including zero-argument calls. The full test suite passes (1127 tests), and ruff lint and format are clean on the changed files. I didn't commit.

All three statements from the report now round-trip unchanged in Snowflake:

```sql
SELECT IDENTIFIER($fn)(41)        -- unchanged
SELECT IDENTIFIER('my_func')(1, 2) -- unchanged
SELECT IDENTIFIER($fn)()          -- unchanged
```

The fix has two parts:

- **Parser** (`sqlglot/parsers/snowflake.py`): a new `_parse_function_call` override. When a call to `IDENTIFIER(...)` is followed by `(`, it parses the argument list and builds an `exp.Anonymous` whose callee is the existing `exp.DynamicIdentifier`. Before, the trailing `(41)` was read as a column alias list, which caused the `ParseError`.
- **Generator** (`sqlglot/generator.py`): `anonymous_sql` no longer uppercases the callee when it is a `DynamicIdentifier`. Without this, `$fn` came out as `$FN` and `'my_func'` as `'MY_FUNC'`, because the whole callee string was normalized.

I added four `validate_identity` cases to `tests/dialects/test_snowflake.py`, next to the existing `IDENTIFIER` tests. I didn't change any existing test.

Transpiling `IDENTIFIER($fn)(41)` to DuckDB still logs the existing "non-literal arguments is not supported" warning. That is the current `DynamicIdentifier` behavior, not something this change introduced.

## events
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py | head -50; grep -rn \"IDENTIFIER(\" tests/dialects/test_snowflake.py | head -20", "description": "Find IDENTIFIER handling in Snowflake dialect and tests"}
[tool_result] 0 matches for 'IDENTIFIER'
tests/dialects/test_snowflake.py:770:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
tests/dialects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -rn \"IDENTIFIER\" sqlglot/ | grep -v \"\\.pyc\" | head -30", "description": "Reproduce the parse error and locate IDENTIFIER references"}
[tool_result] ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 24.
  SELECT IDENTIFIER($fn)([4m)[0m
sqlglot/parsers/clickhouse.py:555:            self._matc
…[1780 chars elided]…
y:498:        """Returns an IDENTIFIER token with `identifier` as its text."""
sqlglot/tokenizer_core.py:499:        return cls(TokenType.IDENTIFIER, identifier)
sqlglot/tokenizer_core.py:1011:            self._add(TokenType.IDENTIFIER)
sqlglot/tokenizer_core.py:1021:            self._add(TokenType.IDENTIFIER)
sqlglot/tokenizer_core.py:1103:        self._add(TokenType.IDENTIFIER, text)
sqlglot/parser.py:573:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:616:    } - {TokenType.IDENTIFIER}
[tool_use Bash] {"command": "sed -n 1155,1185p sqlglot/parsers/snowflake.py; sed -n 720,730p sqlglot/parsers/snowflake.py; grep -n \"class DynamicIdentifier\" -A 12 sqlglot/expressions/*.py; grep -rn \"DynamicIdentifier\" sqlglot/ | grep -v pyc", "description": "Inspect Snowflake IDENTIFIER parsing and DynamicIdentifier class"}
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
…[1746 chars elided]…
  def name(self) -> str:
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1169:            return self.expression(exp.DynamicIdentifier(this=identifier))
sqlglot/generator.py:1960:    def dynamicidentifier_sql(self, expression: exp.DynamicIdentifier) -> str:
sqlglot/expressions/core.py:1811:class DynamicIdentifier(Expression, Func):
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
[tool_use Bash] {"command": "grep -n \"def _parse_function\\b\\|def _parse_function_call\\|def _parse_column_ops\\|def _parse_primary\\|def _parse_alias\\|def _parse_unary\\|def _parse_type\\b\\|def _parse_column\\b\\|def _parse_field\\b\\|def _parse_wrapped_csv\\|def _parse_csv\" sqlglot/parser.py sqlglot/parsers/*.py | head -30; grep -n \"class Anonymous\" -A 5 sqlglot/expressions/*.py", "description": "Locate parser function-call and alias parsing methods"}
[tool_result] 29 matches in 9 files:

sqlglot/parser.py:5178:def _parse_aliased_expression() -> exp.Expr | None:
sqlglot/parser.py:6150:def _parse_unary(self) -> exp.Expr | None:
sqlglot/parser.py:6155:def _parse_type(
sqlglot/parser.py:6585:def _parse_column(self) -> exp.Expr | None:
sqlglot/parser.py:6768:def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:6866:def _parse_primary(self) -> exp.Expr | None:
sqlglot/parser.py:6894:def _parse_field(
sqlglot/parser.py:6911:de
…[1675 chars elided]…
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
[tool_use Bash] {"command": "sed -n 6768,6800p sqlglot/parser.py; echo ----; sed -n 6866,7060p sqlglot/parser.py", "description": "Read column ops, primary, and function call parsing"}
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

 
…[7735 chars elided]…
ENTIFIER:
                    this = exp.Identifier(this=this, quoted=True).update_positions(token)

                result = self.expression(exp.Anonymous(this=this, expressions=args))

            result = result.update_positions(token)

        if isinstance(result, exp.Expr):
            result.add_comments(comments)

        if parser:
            self._match(TokenType.R_PAREN, expression=result)
        else:
            self._match_r_paren(result)
        return self._parse_window(result)
[tool_use Bash] {"command": "grep -n \"def anonymous_sql\" -A 12 sqlglot/generator.py; sed -n 1955,1965p sqlglot/generator.py; grep -n \"def _parse_function_call\\|def _parse_function\\b\" -A 3 sqlglot/parsers/snowflake.py; git log --oneline -3 -- sqlglot/parsers/snowflake.py | cat; git log -S\"DynamicIdentifier\" --oneline | cat", "description": "Check Anonymous generation and DynamicIdentifier history"}
[tool_result] 3936:    def anonymous_sql(self, expression: exp.Anonymous) -> str:
3937-        # We don't normalize qualified functions such as a.b.foo(), because they can be case-sensitive
3938-        parent = expression.parent
3939-        is_qualified = isinstance(parent, exp.Dot) and expression is parent.expression
3940-
3941-        return self.func(
3942-            self.sql(expression, "this"), *expression.expressions, normalize=not is_qualified
3943-        )
3944-
3945-    def paren_sql(self, expres
…[508 chars elided]…
s.name).sql(self.dialect)
        self.unsupported("IDENTIFIER() with non-literal arguments is not supported")
        return self.func("IDENTIFIER", this)
523f7c255 feat(snowflake): support properties before column definitions in `CREATE` statements (#7787)
78c5cf92f feat(snowflake): transpile Snowflake IDENTIFIER function to DuckDB (#7723)
4804de408 Feat(snowflake): support `RENAME TO` clause in `UNDROP` statement
78c5cf92f feat(snowflake): transpile Snowflake IDENTIFIER function to DuckDB ...
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/snowflake.py | grep -n \"import\\|^from\"; grep -n \"    def _parse_\\(id_var\\|lambda\\|function_args\\)\\|^    def _parse_function\" sqlglot/parsers/snowflake.py | head; grep -n \"^    def \\|^    [A-Z_]* = \" sqlglot/parsers/snowflake.py | head -5", "description": "Check imports and method layout in Snowflake parser"}
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
109 matches in 108 files:

1215:0:self._parse_var(any_token=True, upper=True)),
1287:0:
1327:0:self._parse_alias(self._parse_disjunction(), explicit=True)
391:0:lambda self, this: self.expression(
398:0:lambda args: exp.StrPosition(
404:0:lambda args: exp.AddMonths(
410:0:lambda args: exp.Localtime(this=seq_get(args, 0)),
412:0:lambda args: exp.Array(expressions=args),
70 matches in 36 files:

1017:0:
1026:0:
1043:0:
[assistant] Snowflake's `_parse_id_var` already handles `IDENTIFIER(...)` in identifier positions. The failure is in function position: `IDENTIFIER($fn)` is parsed as a function, and the trailing `(41)` is then taken as a column alias list. I'll add a Snowflake override of `_parse_function_call` that consumes an argument list after a `DynamicIdentifier`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204716-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _parse_show_snowflake(", "new_string": "        return super()._parse_id_var(any_token=any_token, tokens=tokens)\n\n    def _
…[442 chars elided]…
 # Dynamic invocation, e.g. IDENTIFIER($fn)(1, 2), where the callee is resolved at runtime\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            args = self._parse_function_args()\n            self._match_r_paren()\n            return self.expression(exp.Anonymous(this=func, expressions=args))\n\n        return func\n\n    def _parse_show_snowflake("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-204716-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', 'SELECT IDENTIFIER(\\$fn)(1) AS x FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(repr(e)[:300]); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Verify the three example queries parse and round-trip"}
[tool_result] Set(
  expressions=[
    SetItem(
      this=EQ(
        this=Column(
          this=Identifier(this=fn, quoted=False)),
        expression=Literal(this='add_one', is_string=True)),
      kind=VARIABLE)],
  unset=False,
  tag=False)
SET fn = 'add_one'
Select(
  expressions=[
    Anonymous(
      this=DynamicIdentifier(
        this=Parameter(
          this=Var(this=fn))),
      expressions=[
        Literal(this=41, is_string=False)])])
SELECT IDENTIFIER($FN)(41)
Select(
  expressions=[
    Ano
…[224 chars elided]…
NC')(1, 2)
Select(
  expressions=[
    Anonymous(
      this=DynamicIdentifier(
        this=Parameter(
          this=Var(this=fn))))])
SELECT IDENTIFIER($FN)()
Select(
  expressions=[
    Alias(
      this=Anonymous(
        this=DynamicIdentifier(
          this=Parameter(
            this=Var(this=fn))),
        expressions=[
          Literal(this=1, is_string=False)]),
      alias=Identifier(this=x, quoted=False))],
  from_=From(
    this=Table(
      
SELECT IDENTIFIER($FN)(1) AS x FROM t
[assistant] Parsing now works, but the output case is wrong: `$fn` becomes `$FN` and `'my_func'` becomes `'MY_FUNC'`. `anonymous_sql` normalizes the whole callee SQL string, string contents included. I'll skip normalization when the callee is a `DynamicIdentifier`.
[tool_use Bash] {"command": "grep -n \"normalize\" sqlglot/generator.py | grep -n \"def func\\|normalize_func\\|normalize=\" | head; grep -n \"    def func(\" -A 12 sqlglot/generator.py | head -30", "description": "Inspect generator func normalization logic"}
[tool_result] 13:sqlglot/generator.py:849:"normalize_functions",
15:sqlglot/generator.py:898:self.normalize_functions = (
16:sqlglot/generator.py:899:self.dialect.NORMALIZE_FUNCTIONS if normalize_functions is None else normalize_f...
19:sqlglot/generator.py:3942:...elf.sql(expression, "this"), *expression.expressions, normalize=not is_qualified
20:sqlglot/generator.py:4605:name = self.normalize_func(name) if normalize else name
4597:    def func(
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
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/generator.py'\ns=open(p).read()\nold='''        is_qualified = isinstance(parent, exp.Dot) and expression is parent.expression\n\n        return self.func(\n            self.sql(expression, \"this\"), *expression.expressions, normalize=not is_qualified\n        )'''\nnew='''        is_qualified = isinstance(parent, exp.Dot) and expression is pa
…[591 chars elided]…
AS x FROM t', 'SELECT IDENTIFIER(\\$fn)(1)']:\n    print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\nprint(sqlglot.transpile(\\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT IDENTIFIER(\\$fn)(41)', read='snowflake', write='duckdb'))\n\"", "description": "Skip normalization for dynamic callee and recheck round-trips"}
[tool_result] IDENTIFIER() with non-literal arguments is not supported
SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER($fn)(1) AS x FROM t
SELECT IDENTIFIER($fn)(1)
['SELECT my_func(1, 2)']
['SELECT IDENTIFIER($fn)(41)']
[assistant] Round-trips are correct now. One line printed a warning, `IDENTIFIER() with non-literal arguments is not supported`, which I need to check. Let me see whether it is pre-existing behavior or something my change introduced.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT IDENTIFIER(\\$fn)(41)', read='snowflake', write='snowflake', unsupported_level=sqlglot.ErrorLevel.RAISE))\" 2>&1 | tail -3; git stash list | head -0; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT IDENTIFIER(\\$fn) FROM t', read='snowflake', write='snowflake'))\" 2>&1 | tail -3", "description": "Check whether the unsupported warning is emitted for Snowflake output"}
[tool_result] ['SELECT IDENTIFIER($fn)(41)']
head: illegal line count -- 0

thread 'main' (45018985) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
['SELECT IDENTIFIER($fn) FROM t']
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in 'SELECT IDENTIFIER($fn)(41)' \"SELECT IDENTIFIER('my_func')(1, 2)\" 'SELECT IDENTIFIER($fn)()' 'SELECT IDENTIFIER($fn)(1) AS x FROM t'; do echo \"== $s\"; $PY -c \"\nimport sys, sqlglot\nprint(sqlglot.transpile(sys.argv[1], read='snowflake', write='snowflake')[0])\" \"$s\" 2>&1; done", "description": "Run each statement separately to find the warning source"}
[tool_result] == SELECT IDENTIFIER($fn)(41)
SELECT IDENTIFIER($fn)(41)
== SELECT IDENTIFIER('my_func')(1, 2)
SELECT IDENTIFIER('my_func')(1, 2)
== SELECT IDENTIFIER($fn)()
SELECT IDENTIFIER($fn)()
== SELECT IDENTIFIER($fn)(1) AS x FROM t
SELECT IDENTIFIER($fn)(1) AS x FROM t
[assistant] The warning comes from the DuckDB transpile at the end of my earlier check, not from the Snowflake round-trips. That is the existing `DynamicIdentifier` behavior for non-literal arguments, and it's expected. Next I'll add tests next to the existing `IDENTIFIER` tests and run the suite.
[tool_use Bash] {"command": "sed -n 764,775p tests/dialects/test_snowflake.py", "description": "View existing IDENTIFIER tests for placement"}
[tool_result]         self.validate_identity("SELECT STDDEV_SAMP(x)", "SELECT STDDEV(x)")
        self.validate_identity(
            "SELECT STDDEV_SAMP(x) OVER (PARTITION BY 1)", "SELECT STDDEV(x) OVER (PARTITION BY 1)"
        )
        self.validate_identity("SELECT KURTOSIS(x)")
        self.validate_identity("SELECT KURTOSIS(x) OVER (PARTITION BY 1)")
        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
        self.validate_identity("INITCAP('iqamqinterestedqinqthisqtopic', 'q')")
        self.validate_identity("OBJECT_CONSTRUCT(*)")
        self.validate_identity("SELECT CAST('2021-01-01' AS DATE) + INTERVAL '1 DAY'")
        self.validate_identity("SELECT HLL(*)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-204716-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"INITCAP(", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(1) AS x FROM t\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"INITCAP("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-204716-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"identifier or Identifier or Snowflake\" 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run Snowflake tests then the full project test suite"}
[tool_result] ................. [ 17%]
................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.54s
..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
..................................... [ 
…[318 chars elided]…
.......................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 46.74s
[assistant] The full suite passes (1127 tests). Next I'll run the linter and formatter on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parsers/snowflake.py sqlglot/generator.py tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot/parsers/snowflake.py sqlglot/generator.py tests/dialects/test_snowflake.py) 2>&1 | tail -8; git status --short; git diff --stat | cat", "description": "Run ruff lint and format checks on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generator.py
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.pysqlglot/generator.py             |  5 ++++-
 sqlglot/parsers/snowflake.py     | 22 ++++++++++++++++++++++
 tests/dialects/test_snowflake.py |  4 ++++
 3 files changed, 30 insertions(+), 1 deletion(-)
[assistant] Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, including zero-argument calls. The full test suite passes (1127 tests), and ruff lint and format are clean on the changed files. I didn't commit.

All three statements from the report now round-trip unchanged in Snowflake:

```sql
SELECT IDENTIFIER($fn)(41)        -- unchanged
SELECT IDENTIFIER('my_func')(1, 2) -- unchanged
SELECT IDENTIFIER($fn)()          -- unchanged
```

The fix has two parts:

- **Parser** (`sqlglot/parsers/snowflake.py`): a new `_parse_function_call` override. When a call to `IDENTIFIER(.
…[232 chars elided]…
*Generator** (`sqlglot/generator.py`): `anonymous_sql` no longer uppercases the callee when it is a `DynamicIdentifier`. Without this, `$fn` came out as `$FN` and `'my_func'` as `'MY_FUNC'`, because the whole callee string was normalized.

I added four `validate_identity` cases to `tests/dialects/test_snowflake.py`, next to the existing `IDENTIFIER` tests. I didn't change any existing test.

Transpiling `IDENTIFIER($fn)(41)` to DuckDB still logs the existing "non-literal arguments is not supported" warning. That is the current `DynamicIdentifier` behavior, not something this change introduced.
