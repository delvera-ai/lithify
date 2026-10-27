# trajectory base-1

final message:
Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments. The full suite passes (1127 tests), and the changes are uncommitted in the worktree.

The fix has two parts:

- **Parser** (`sqlglot/parsers/snowflake.py`): a new `_parse_function` override. When `IDENTIFIER(...)` is followed by `(args)`, it wraps the existing `exp.DynamicIdentifier` as the callee of an `exp.Anonymous`. `Anonymous` already accepts a non-string `this`, so no new node was needed.
- **Generator** (`sqlglot/generators/snowflake.py`): an `anonymous_sql` override for that case only. Without it, the generated callee was upper-cased, turning `'my_func'` into `'MY_FUNC'` and `$fn` into `$FN`. The base generator is unchanged.

Tests added to `tests/dialects/test_snowflake.py` as `validate_identity` round-trips:
- `SELECT IDENTIFIER($fn)(41)`
- `SELECT IDENTIFIER('my_func')(1, 2)`
- `SELECT IDENTIFIER($fn)()`
- `SELECT IDENTIFIER($fn)(41) AS x FROM t`

`SET fn = 'add_one'` already parsed, and `ruff check` and `ruff format` are clean on the changed files.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes wi
…[2310 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn \"IDENTIFIER\" sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/parser.py | head -50", "description": "Find IDENTIFIER handling in Snowflake and base parser"}
[tool_result] sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1164:        if self._match_text_seq("IDENTIFIER", "("):
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
sqlglot/parser.py:573:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:616:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:706:        TokenType.IDENTIFIER,
sqlglot/parser.py:799:    IDENTIFIER_TOKENS: t.ClassVar[frozense
…[883 chars elided]…
           this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
sqlglot/parser.py:7045:                if token_type == TokenType.IDENTIFIER:
sqlglot/parser.py:7485:        if self._match(TokenType.IDENTIFIER, advance=False) or not self._match_texts(
sqlglot/parser.py:7503:            and self._curr.token_type != TokenType.IDENTIFIER
sqlglot/parser.py:7850:            tokens={TokenType.BINARY, TokenType.IDENTIFIER},
sqlglot/parser.py:8537:        if self._match(TokenType.IDENTIFIER):
[tool_use Bash] {"command": "sed -n 1150,1200p sqlglot/parsers/snowflake.py && grep -rn \"DynamicIdentifier\" sqlglot/ tests/ | head -30", "description": "Show Snowflake IDENTIFIER parser and DynamicIdentifier usages"}
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
…[1401 chars elided]…
elf._parse_table_parts()
sqlglot/generator.py:1960:    def dynamicidentifier_sql(self, expression: exp.DynamicIdentifier) -> str:
sqlglot/parsers/snowflake.py:727:        "IDENTIFIER": exp.DynamicIdentifier.from_arg_list,
sqlglot/parsers/snowflake.py:1169:            return self.expression(exp.DynamicIdentifier(this=identifier))
sqlglot/expressions/core.py:1811:class DynamicIdentifier(Expression, Func):
sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, e)\n\"", "description": "Reproduce the parse errors with the project python"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()']:\n    try:\n        print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as e: print('ERR', s, type(e).__name__, str(e)[:200])\n\"; sed -n 1950,1970p sqlglot/generator.py; sed -n 1805,1820p sqlglot/expressions/core.py", "description": "Reproduce IDENTIFIER parse errors and show node/generator"}
[tool_result] SET fn = 'add_one'
ERR SELECT IDENTIFIER($fn)(41) ParseError Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 25.
  SELECT IDENTIFIER($fn)([4m41[0m)
ERR SELECT IDENTIFIER('my_func')(1, 2) ParseError Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 30.
  SELECT IDENTIFIER('my_func')([4m1[0m, 2)
ERR SELECT IDENTIFIER($fn)() ParseError Required keyword: 'expressions' missing for <class 'sqlgl
…[821 chars elided]…
p.Identifier) -> str:
        text = expression.name
        lower = text.lower()
        quoted = expression.quoted
    @property
    def output_name(self) -> str:
        return self.name


# https://docs.snowflake.com/en/sql-reference/identifier-literal
class DynamicIdentifier(Expression, Func):
    pass


class Opclass(Expression):
    arg_types = {"this": True, "expression": True}


class Star(Expression):
    arg_types = {"except_": False, "replace": False, "rename": False, "ilike": False}
[tool_use Bash] {"command": "grep -n \"Aliases\" sqlglot/parser.py | head; grep -n \"def _parse_function_call\\|def _parse_function(\\|def _parse_column_ops\\|def _parse_primary\\|def _parse_column_reference\\|def _parse_field(\" sqlglot/parser.py; grep -n \"class Aliases\" -A3 sqlglot/expressions/*.py; grep -rn \"IDENTIFIER\" tests/dialects/test_snowflake.py | head", "description": "Locate Aliases construction and function-call parsing"}
[tool_result] 8482:                exp.Aliases(
6674:    def _parse_column_reference(self) -> exp.Expr | None:
6768:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6866:    def _parse_primary(self) -> exp.Expr | None:
6894:    def _parse_field(
6911:    def _parse_function(
6944:    def _parse_function_call(
7599:    def _parse_primary_key_part(self) -> exp.Expr | None:
7614:    def _parse_primary_key(
8566:    def _parse_primary_or_var(self) -> exp.Expr | None:
sqlglot/expressions/
…[346 chars elided]…
lects/test_snowflake.py:771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
tests/dialects/test_snowflake.py:4275:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
tests/dialects/test_snowflake.py:4276:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
tests/dialects/test_snowflake.py:6822:        self.validate_identity("UNDROP SNAPSHOT IDENTIFIER('my_snap')")
[tool_use Bash] {"command": "sed -n 6674,6700p sqlglot/parser.py; echo ----; sed -n 6894,7010p sqlglot/parser.py; echo ----; sed -n 8470,8495p sqlglot/parser.py", "description": "Read column reference, field, and function parsing code"}
[tool_result]     def _parse_column_reference(self) -> exp.Expr | None:
        this = self._parse_field()
        if (
            not this
            and self._match(TokenType.VALUES, advance=False)
            and self.VALUES_FOLLOWED_BY_PAREN
            and (not self._next or self._next.token_type != TokenType.L_PAREN)
        ):
            this = self._parse_id_var()

        if isinstance(this, exp.Identifier):
            # We bubble up comments from the Identifier to the Column
            this = s
…[4975 chars elided]…
pression(
                exp.Aliases(
                    this=this, expressions=self._parse_csv(lambda: self._parse_id_var(any_token))
                ),
                comments=comments,
            )
            self._match_r_paren(aliases)
            return aliases

        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
            self.STRING_ALIASES and self._parse_string_as_identifier()
        )

        if alias:
            comments.extend(alias.pop_comments())
[tool_use Bash] {"command": "grep -n \"def anonymous_sql\" -A12 sqlglot/generator.py; grep -n \"class Anonymous\" -A8 sqlglot/expressions/*.py; sed -n 7010,7040p sqlglot/parser.py; grep -n \"def _parse_function_call\\|_parse_function_call\" sqlglot/parsers/snowflake.py | head -3; grep -n \"def _parse_user_defined_function\\|def _parse_udf\" sqlglot/parser.py", "description": "Inspect anonymous function generation and parser tail"}
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
…[2269 chars elided]…
 if func_builder accepts 'dialect'.
                try:
                    func = func_builder(args)
                except TypeError:
                    func = func_builder(args, dialect=self.dialect)

                func = self.validate_expression(func, args)
                if self.dialect.PRESERVE_ORIGINAL_NAMES:
7108:    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7114:    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
[tool_use Bash] {"command": "grep -n \"def _parse_function\\b\\|def _parse_function(\\|^import\\|^from\" sqlglot/parsers/snowflake.py; grep -n \"_match_r_paren(\" sqlglot/parser.py | head -2; grep -n \"def _match_r_paren\" -A3 sqlglot/parser.py", "description": "Check imports and existing overrides in Snowflake parser"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import is_date_unit, is_int, seq_get
19:from sqlglot.tokens import TokenType
20:from sqlglot.trie import new_trie
3005:            self._match_r_paren()
3113:        self._match_r_paren()
9432:    def _match_r_paren(self, expression: exp.Expr | None = None) -> None:
9433-        if not self._match(TokenType.R_PAREN, expression=expression):
9434-            self.raise_error("Expecting )")
9435-
[assistant] Adding a Snowflake `_parse_function` override that turns `IDENTIFIER(...)` followed by `(args)` into an `exp.Anonymous` call whose callee is the `DynamicIdentifier`. `exp.Anonymous` already accepts a non-string `this` (its `name` property handles it), so no new node is needed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_id_var(\n        self,\n        any_token: bool = True,\n        tokens: Collection[TokenType] | None = None,\n    ) -> exp.Expr | None:\n        if self._match_text_seq(\"IDENTIFIER\", \"(\"):\
…[1199 chars elided]…
       anonymous=anonymous,\n            optional_parens=optional_parens,\n            any_token=any_token,\n        )\n\n        if isinstance(func, exp.DynamicIdentifier) and self._match(TokenType.L_PAREN):\n            call = self.expression(exp.Anonymous(this=func, expressions=self._parse_function_args()))\n            self._match_r_paren(call)\n            return call\n\n        return func"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SET fn = \\'add_one\\'', 'SELECT IDENTIFIER(\\$fn)(41)', \\\"SELECT IDENTIFIER('my_func')(1, 2)\\\", 'SELECT IDENTIFIER(\\$fn)()', 'SELECT IDENTIFIER(\\$fn)(41) AS x FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, type(ex).__name__, str(ex)[:200])\n\"", "description": "Re-run the reproduction cases after the parser change"}
[tool_result] SET fn = 'add_one'
SELECT IDENTIFIER($FN)(41)
SELECT IDENTIFIER('MY_FUNC')(1, 2)
SELECT IDENTIFIER($FN)()
SELECT IDENTIFIER($FN)(41) AS x FROM t
[assistant] The parse now succeeds, but the output upper-cases the callee (`$FN`, `'MY_FUNC'`), so the round-trip would fail. Checking how `func` normalizes names.
[tool_use Bash] {"command": "grep -n \"def func(\" -A22 sqlglot/generator.py; grep -n \"def normalize_func\" -A8 sqlglot/generator.py", "description": "Read Generator.func and normalize_func"}
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
…[293 chars elided]…
  return sep.join(arg_sqls)
4617-
4618-    def too_wide(self, args: t.Iterable) -> bool:
4619-        return sum(len(arg) for arg in args) > self.max_text_width
1059:    def normalize_func(self, name: str) -> str:
1060-        if self.normalize_functions == "upper" or self.normalize_functions is True:
1061-            return name.upper()
1062-        if self.normalize_functions == "lower":
1063-            return name.lower()
1064-        return name
1065-
1066-    def indent(
1067-        self,
[assistant] The callee's generated text is passed through `normalize_func`, which upper-cases the whole thing. I'll keep this Snowflake-specific: a generator override for calls whose callee is a `DynamicIdentifier`, so the base `anonymous_sql` is unchanged. Checking for an existing override first.
[tool_use Bash] {"command": "grep -n \"anonymous_sql\\|def dynamicidentifier\\|DynamicIdentifier\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py; sed -n 470,482p sqlglot/generators/snowflake.py", "description": "Check existing anonymous_sql overrides in Snowflake generator"}
[tool_result] sqlglot/generators/snowflake.py:478:        exp.DynamicIdentifier: rename_func("IDENTIFIER"),
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
            "DATE_PART", map_date_part(e.this, self.dialect), e.expression
        ),
[tool_use Bash] {"command": "grep -n \"    def [a-z_]*_sql(\" sqlglot/generators/snowflake.py | head -5", "description": "Find first generator method in Snowflake generator"}
[tool_result] 620:    def sortarray_sql(self, expression: exp.SortArray) -> str:
627:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
681:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
687:    def datatype_sql(self, expression: exp.DataType) -> str:
718:    def tonumber_sql(self, expression: exp.ToNumber) -> str:
[tool_use Bash] {"command": "sed -n 616,628p sqlglot/generators/snowflake.py", "description": "Read context around sortarray_sql"}
[tool_result]             "SHA2_BINARY", e.this, e.args.get("length") or exp.Literal.number(256)
        ),
    }

    def sortarray_sql(self, expression: exp.SortArray) -> str:
        asc = expression.args.get("asc")
        nulls_first = expression.args.get("nulls_first")
        if asc == exp.false() and nulls_first == exp.true():
            nulls_first = None
        return self.func("ARRAY_SORT", expression.this, asc, nulls_first)

    def nthvalue_sql(self, expression: exp.NthValue) -> str:
        result = self.func("NTH_VALUE", expression.this, expression.args.get("offset"))
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py", "old_string": "    def sortarray_sql(self, expression: exp.SortArray) -> str:\n        asc = expression.args.get(\"asc\")", "new_string": "    def anonymous_sql(self, expression: exp.Anonymous) -> str:\n        if isinstance(expression.this, exp.DynamicIdentifier):\n            return self.func(\n                self.sql(expression, \"this\"), *expression.expressions, normalize=False\n            )\n        return super().anonymous_sql(expression)\n\n    def sortarray_sql(self, expression: exp.SortArray) -> str:\n        asc = expression.args.get(\"asc\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll add the round-trip tests next to the existing `IDENTIFIER` tests in the Snowflake test file, then run the Snowflake suite.
[tool_use Bash] {"command": "sed -n 4272,4278p tests/dialects/test_snowflake.py", "description": "Show test context near existing IDENTIFIER tests"}
[tool_result]         self.validate_identity("CREATE MATERIALIZED VIEW a COMMENT='...' AS SELECT 1 FROM x")
        self.validate_identity("CREATE DATABASE mytestdb_clone CLONE mytestdb")
        self.validate_identity("CREATE SCHEMA mytestschema_clone CLONE testschema")
        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
        self.validate_identity("CREATE TAG cost_center ALLOWED_VALUES 'a', 'b'")
        self.validate_identity("CREATE WAREHOUSE x").this.assert_is(exp.Identifier)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n", "new_string": "        self.validate_identity(\"WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41)\")\n        self.validate_identity(\"SELECT IDENTIFIER('my_func')(1, 2)\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)()\")\n        self.validate_identity(\"SELECT IDENTIFIER($fn)(41) AS x FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103827-snowflake-dialect-snowflake-can/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -30", "description": "Run the Snowflake dialect test file"}
[tool_result] ................. [ 17%]
................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.57s
[assistant] Snowflake tests pass. Running the full suite to check for regressions from the parser and generator changes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the full test suite"}
[tool_result] ..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
..................................... [ 41%]
........................................................... [ 47%]
...................................... [ 50%]
................................................... [ 55%]
........................................
…[101 chars elided]…
.......................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                    [100%]
1127 passed, 18278 subtests passed in 55.60s
[assistant] Full suite passes (1127 tests). Running the formatter and linter on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py || $PY/ruff format --diff sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py 2>&1 | head -30); $PY/ruff check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py 2>&1 | tail -3; git status --short", "description": "Check formatting and lint on changed files"}
[tool_result] Would reformat: sqlglot/generators/snowflake.py
Would reformat: sqlglot/parsers/snowflake.py
2 files would be reformatted, 1 file already formatted
--- sqlglot/generators/snowflake.py
+++ sqlglot/generators/snowflake.py
@@ -619,9 +619,7 @@
 
     def anonymous_sql(self, expression: exp.Anonymous) -> str:
         if isinstance(expression.this, exp.DynamicIdentifier):
-            return self.func(
-                self.sql(expression, "this"), *expression.expressions, normalize=False
-          
…[367 chars elided]…
ntifier) and self._match(TokenType.L_PAREN):
-            call = self.expression(exp.Anonymous(this=func, expressions=self._parse_function_args()))
+            call = self.expression(
+                exp.Anonymous(this=func, expressions=self._parse_function_args())
+            )
             self._match_r_paren(call)
             return call
 

2 files would be reformatted
All checks passed!
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/ruff format sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py && $PY/ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py && $PY/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -1; git diff --stat", "description": "Apply ruff formatting and re-run Snowflake tests"}
[tool_result] 2 files reformatted
2 files already formatted
97 passed, 1568 subtests passed in 0.46s
 sqlglot/generators/snowflake.py  |  5 +++++
 sqlglot/parsers/snowflake.py     | 23 +++++++++++++++++++++++
 tests/dialects/test_snowflake.py |  4 ++++
 3 files changed, 32 insertions(+)
[This command modified 2 files you've previously read: sqlglot/parsers/snowflake.py, sqlglot/generators/snowflake.py. Call Read before editing.]
[assistant] The "changed on disk" notice is from my own `ruff format` run just before it. I'll check the final diff to confirm it's what I intended.
[tool_use Bash] {"command": "git diff", "description": "Show the final diff"}
[tool_result] diff --git a/sqlglot/generators/snowflake.py b/sqlglot/generators/snowflake.py
index 401188f4e..7afb4d7ed 100644
--- a/sqlglot/generators/snowflake.py
+++ b/sqlglot/generators/snowflake.py
@@ -617,6 +617,11 @@ class SnowflakeGenerator(generator.Generator):
         ),
     }
 
+    def anonymous_sql(self, expression: exp.Anonymous) -> str:
+        if isinstance(expression.this, exp.DynamicIdentifier):
+            return self.func(self.sql(expression, "this"), *expression.expressions, normalize
…[1908 chars elided]…
) FROM x")
+        self.validate_identity("SELECT IDENTIFIER($fn)(41)")
+        self.validate_identity("SELECT IDENTIFIER('my_func')(1, 2)")
+        self.validate_identity("SELECT IDENTIFIER($fn)()")
+        self.validate_identity("SELECT IDENTIFIER($fn)(41) AS x FROM t")
         self.validate_identity("INITCAP('iqamqinterestedqinqthisqtopic', 'q')")
         self.validate_identity("OBJECT_CONSTRUCT(*)")
         self.validate_identity("SELECT CAST('2021-01-01' AS DATE) + INTERVAL '1 DAY'")
[assistant] Snowflake now parses and round-trips dynamic function calls through `IDENTIFIER()`, with zero or more arguments. The full suite passes (1127 tests), and the changes are uncommitted in the worktree.

The fix has two parts:

- **Parser** (`sqlglot/parsers/snowflake.py`): a new `_parse_function` override. When `IDENTIFIER(...)` is followed by `(args)`, it wraps the existing `exp.DynamicIdentifier` as the callee of an `exp.Anonymous`. `Anonymous` already accepts a non-string `this`, so no new node was needed.
- **Generator** (`sqlglot/generators/snowflake.py`): an `anonymous_sql` override for that case only. Without it, the generated callee was upper-cased, turning `'my_func'` into `'MY_FUNC'` and `$fn` into `$FN`. The base generator is unchanged.

Tests added to `tests/dialects/test_snowflake.py` as `validate_identity` round-trips:
- `SELECT IDENTIFIER($fn)(41)`
- `SELECT IDENTIFIER('my_func')(1, 2)`
- `SELECT IDENTIFIER($fn)()`
- `SELECT IDENTIFIER($fn)(41) AS x FROM t`

`SET fn = 'add_one'` already parsed, and `ruff check` and `ruff format` are clean on the changed files.
