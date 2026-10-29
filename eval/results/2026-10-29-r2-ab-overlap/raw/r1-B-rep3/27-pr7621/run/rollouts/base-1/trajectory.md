# trajectory base-1

final message:
Fixed. After a dot, no-parenthesis function names like `current_user`, `current_date`, and `sysdate` now stay plain identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   -> SELECT mytable.current_user FROM mytable
SELECT t.current_date, t.sysdate FROM t    -> SELECT t.current_date, t.sysdate FROM t
SELECT current_user FROM t                 -> SELECT CURRENT_USER() FROM t   (unchanged)
SELECT t.CURRENT_USER() FROM t             -> SELECT t.CURRENT_USER() FROM t (unchanged)
```

**Cause:** In `_parse_column_ops` (`sqlglot/parser.py`), the dot branch parsed the right-hand side with `_parse_field(anonymous_func=True)`. That called `_parse_function` with `optional_parens=True`, so a bare `current_user` after a dot was matched as a no-paren function.

**Change:**
- `sqlglot/parser.py`: `_parse_field` takes a new `optional_parens` flag (default `True`, so other callers are unaffected). The dot branch passes `optional_parens=False`, so only the paren form `x.f()` is treated as a function call.
- `tests/test_parser.py`: added `test_no_paren_function_names_after_dot`, which round-trips the dotted cases and checks that unqualified `current_user` still parses to `exp.CurrentUser`.

**Verification:** the full suite passes with the project's interpreter (1106 tests, up from 1105 with the new one). `ruff check` and `ruff format --check` are clean on both files.

I haven't committed anything. The `t.current_user()` paren form still produces an `Anonymous` node inside a `Dot`, as before; I left that alone.

## events
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTION\\|CURRENT_USER\\|SYSDATE\" sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/dialect.py | head -50; grep -n \"def _parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\|def _parse_primary\\|def _parse_function\" sqlglot/parser.py", "description": "Locate no-paren function handling in parser"}
[tool_result] 12 matches in 2 files:

sqlglot/parser.py:432:NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
sqlglot/parser.py:437:TokenType.CURRENT_USER: exp.CurrentUser,
sqlglot/parser.py:769:*NO_PAREN_FUNCTIONS,
sqlglot/parser.py:834:TokenType.CURRENT_USER,
sqlglot/parser.py:1468:NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
sqlglot/parser.py:5350:self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
sqlglot/parser.py:5354:self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
sqlglot/parser.py:6503:if parts is
…[215 chars elided]…
CTIONS:
sqlglot/parser.py:6854:return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
sqlglot/tokens.py:275:"CURRENT_USER": TokenType.CURRENT_USER,
13 matches in 10 files:

6561:0:
6659:0:exp.Expr | None) -> exp.Expr | None:
6757:0:
6826:0:bool = False) -> list[exp.Expr]:
6970:0:
6976:0:
7072:0:
7429:0:
8391:0:
sqlglot/parser.py:6779:def _parse_field(
sqlglot/parser.py:6796:def _parse_function(
sqlglot/parser.py:6829:def _parse_function_call(
sqlglot/parser.py:7444:def _parse_primary_key(
[tool_use Bash] {"command": "sed -n 6775,6870p sqlglot/parser.py; echo ----; sed -n 6490,6520p sqlglot/parser.py", "description": "Read field and function parsing code"}
[tool_result]             return exp.Literal.number(f"0.{self._prev.text}")

        return self._parse_paren()

    def _parse_field(
        self,
        any_token: bool = False,
        tokens: t.Collection[TokenType] | None = None,
        anonymous_func: bool = False,
    ) -> exp.Expr | None:
        if anonymous_func:
            field = (
                self._parse_function(anonymous=anonymous_func, any_token=any_token)
                or self._parse_primary()
            )
        else:
           
…[3320 chars elided]…
ex)
                return None

            has_dot = self._match(TokenType.DOT)
            curr_tt = self._curr.token_type

            if not has_dot:
                if curr_tt in self.COLUMN_OPERATORS or curr_tt in self.COLUMN_POSTFIX_TOKENS:
                    self._retreat(index)
                    return None
            elif curr_tt not in self.IDENTIFIER_TOKENS:
                self._retreat(index)
                return None

            if parts is None:
                parts = []
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user, t.current_timestamp FROM t','SELECT current_user FROM t','SELECT a.current_user.x FROM t', 'SELECT t.CURRENT_USER FROM t']:\n    for d in [None,'oracle','snowflake','postgres']:\n        try: print(d, sqlglot.transpile(s, read=d, write=d)[0])\n        except Exception as e: print(d,'ERR',e)\n\"; grep -n \"CURRENT_USER\\|SYSDATE\" sqlglot/parser.py sqlglot/dialects/*.py | head -30", "description": "Reproduce the dot-qualified no-paren function bug"}
[tool_result] None SELECT mytable.CURRENT_USER() FROM mytable
oracle SELECT mytable.CURRENT_USER() FROM mytable
snowflake SELECT mytable.CURRENT_USER() FROM mytable
postgres SELECT mytable.CURRENT_USER FROM mytable
None SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER(), t.CURRENT_TIMESTAMP() FROM t
oracle SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER(), t.CURRENT_TIMESTAMP FROM t
snowflake SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER(), t.CURRENT_TIMESTAMP() FROM t
postgres SELECT t.CURRENT_DATE, t.sy
…[270 chars elided]…
 t
snowflake SELECT a.CURRENT_USER().x FROM t
postgres SELECT a.CURRENT_USER.x FROM t
None SELECT t.CURRENT_USER() FROM t
oracle SELECT t.CURRENT_USER() FROM t
snowflake SELECT t.CURRENT_USER() FROM t
postgres SELECT t.CURRENT_USER FROM t
4 matches in 3 files:

sqlglot/dialects/exasol.py:57:"USER": TokenType.CURRENT_USER,
sqlglot/dialects/tsql.py:178:"SYSTEM_USER": TokenType.CURRENT_USER,
sqlglot/parser.py:437:TokenType.CURRENT_USER: exp.CurrentUser,
sqlglot/parser.py:834:TokenType.CURRENT_USER,
[tool_use Bash] {"command": "grep -n \"def _parse_column_ops\\|def _parse_column(\\|def _parse_column_parts\\|def _parse_column_reference\" sqlglot/parser.py; sed -n \"$(grep -n 'def _parse_column_ops' sqlglot/parser.py | cut -d: -f1),+75p\" sqlglot/parser.py", "description": "Read column ops parsing"}
[tool_result] rg: regex parse error:
    (?:def _parse_column_ops|def _parse_column(|def _parse_column_parts|def _parse_column_reference)
    ^
error: unclosed group
0 matches for 'def _parse_column_ops\|def _parse_column(\|def _parse_column_parts\|def _parse_column_reference'
    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
        while self._curr.token_type in self.BRACKETS:
            this = self._parse_bracket(this)

        column_operators = self.COLUMN_OPERATORS
        cast
…[2309 chars elided]…
his)

        return this

    def _parse_paren(self) -> exp.Expr | None:
        if not self._match(TokenType.L_PAREN):
            return None

        comments = self._prev_comments
        query = self._parse_select()

        if query:
            expressions = [query]
        else:
            expressions = self._parse_expressions()

        this = seq_get(expressions, 0)

        if not this and self._match(TokenType.R_PAREN, advance=False):
            this = self.expression(exp.Tuple())
[tool_use Bash] {"command": "grep -n \"_parse_field(\" sqlglot/parser.py sqlglot/dialects/*.py | head -30; git status --short", "description": "Find _parse_field callers and check git state"}
[tool_result] rg: regex parse error:
    (?:_parse_field()
    ^
error: unclosed group
0 matches for '_parse_field('
ok
[tool_use Bash] {"command": "grep -rn \"_parse_field(\" sqlglot/ | grep -v \"def \"", "description": "List _parse_field call sites"}
[tool_result] sqlglot/parsers/clickhouse.py:482:            exp.EngineProperty(this=self._parse_field(any_token=True, anonymous_func=True))
sqlglot/parsers/risingwave.py:46:            header = self._parse_field()
sqlglot/parsers/hive.py:233:        this = self._parse_field(any_token=True)
sqlglot/parsers/hive.py:238:        column_new = self._parse_field(any_token=True)
sqlglot/parsers/materialize.py:26:        return self._parse_field()
sqlglot/parsers/oracle.py:166:                this=kind, expression=sel
…[2098 chars elided]…
se_field())
sqlglot/parser.py:9418:                self._parse_wrapped_options() if self._match(TokenType.EQ) else self._parse_field()
sqlglot/parser.py:9426:                exp.var(self._prev.text) if self._match(TokenType.DEFAULT) else self._parse_field(),
sqlglot/parser.py:9429:            expr.set("region", self._parse_field())
sqlglot/parser.py:9434:        return self._parse_field()
sqlglot/parser.py:9924:        separator = self._parse_field() if self._match(TokenType.SEPARATOR) else None
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        tokens: t.Collection[TokenType] | None = None,\n        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous
…[182 chars elided]…
ous_func: bool = False,\n        optional_parens: bool = True,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(\n                    anonymous=anonymous_func,\n                    optional_parens=optional_parens,\n                    any_token=any_token,\n                )\n                or self._parse_primary()\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls", "new_string": "                field = self._parse_field(\n                    any_token=True, anonymous_func=True, optional_parens=False\n                )\n\n            # Function calls"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user, t.current_timestamp FROM t','SELECT current_user FROM t','SELECT a.current_user.x FROM t', 'SELECT t.CURRENT_USER() FROM t', 'SELECT x.y.CURRENT_DATE FROM t']:\n    for d in [None,'oracle','snowflake','bigquery']:\n        print(d, sqlglot.transpile(s, read=d, write=d)[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] None SELECT mytable.current_user FROM mytable
oracle SELECT mytable.current_user FROM mytable
snowflake SELECT mytable.current_user FROM mytable
bigquery SELECT mytable.current_user FROM mytable
None SELECT t.current_date, t.sysdate, t.current_user, t.current_timestamp FROM t
oracle SELECT t.current_date, t.sysdate, t.current_user, t.current_timestamp FROM t
snowflake SELECT t.current_date, t.sysdate, t.current_user, t.current_timestamp FROM t
bigquery SELECT t.current_date, t.sysdate, t.current
…[1448 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 46.89s
[assistant] Fix works and the full suite passes (1105 tests). Now I'll add a regression test.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_parser.py | head -60; grep -n \"^class \\|def test_column\" tests/test_parser.py | head", "description": "Find parser test location"}
[tool_result] 64 matches in 64 files:

100:0:
103:0:
1032:0:
1042:0:
1048:0:
1054:0:
1067:0:
1082:0:
1088:0:
112:0:
115:0:
12:0:
122:0:
128:0:
131:0:
135:0:
16:0:
160:0:
175:0:
185:0:
194:0:
223:0:
240:0:
256:0:
273:0:
303:0:
317:0:
321:0:
324:0:
328:0:
366:0:
383:0:
398:0:
414:0:
432:0:
448:0:
45:0:
465:0:
480:0:
524:0:
559:0:
567:0:
582:0:
594:0:
605:0:
66:0:
779:0:
796:0:
801:0:
804:0:
815:0:
823:0:
838:0:
890:0:
907:0:
920:0:
94:0:
940:0:
2 matches in 2 files:

11:0:
94:0:
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/test_parser.py | head -20; sed -n 1,30p tests/test_parser.py", "description": "Inspect parser test file structure"}
[tool_result] 64 matches in 64 files:

100:0:
103:0:
1032:0:
1042:0:
1048:0:
1054:0:
1067:0:
1082:0:
1088:0:
112:0:
115:0:
12:0:
122:0:
128:0:
131:0:
135:0:
16:0:
160:0:
import time
import unittest
from unittest.mock import patch

from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains


class TestParser(unittest.TestCase):
    def test_parse_empty(self):
        with
…[520 chars elided]…
sertIsInstance(parse_one("left join foo", into=exp.Join), exp.Join)
        self.assertIsInstance(parse_one("int", into=exp.DataType), exp.DataType)
        self.assertIsInstance(parse_one("array<int>", into=exp.DataType), exp.DataType)
        self.assertIsInstance(parse_one("foo", into=exp.Table), exp.Table)
        self.assertIsInstance(
            parse_one(
                "WHEN MATCHED THEN UPDATE SET target.salary = COALESCE(source.salary, target.salary)",
                into=exp.Whens,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "    def test_parse_empty(self):\n        with self.assertRaises(ParseError):\n            parse_one(\"\")\n", "new_string": "    def test_parse_empty(self):\n        with self.assertRaises(ParseError):\n            p
…[145 chars elided]…
able\",\n            \"SELECT t.current_date, t.sysdate, t.current_timestamp FROM t\",\n        ):\n            with self.subTest(sql=sql):\n                self.assertEqual(parse_one(sql).sql(), sql)\n\n        self.assertIsInstance(parse_one(\"SELECT current_user\").selects[0], exp.CurrentUser)\n        self.assertIsInstance(parse_one(\"SELECT t.current_user()\").selects[0], exp.CurrentUser)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one\nprint(repr(parse_one('SELECT t.current_user()').selects[0]))\" ; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -20", "description": "Check AST shape and run parser tests"}
[tool_result] Dot(
  this=Identifier(this=t, quoted=False),
  expression=Anonymous(this=current_user))
    def test_no_paren_function_names_after_dot(self):
        for sql in (
            "SELECT mytable.current_user FROM mytable",
            "SELECT t.current_date, t.sysdate, t.current_timestamp FROM t",
        ):
            with self.subTest(sql=sql):
                self.assertEqual(parse_one(sql).sql(), sql)
    
        self.assertIsInstance(parse_one("SELECT current_user").selects[0], exp.CurrentUs
…[137 chars elided]…
  this=Identifier(this=t, quoted=False),
E         expression=Anonymous(this=current_user)) is not an instance of <class 'sqlglot.expressions.functions.CurrentUser'>

tests/test_parser.py:25: AssertionError
----------------------------- Captured stdout call -----------------------------
uu
=========================== short test summary info ============================
FAILED tests/test_parser.py::TestParser::test_no_paren_function_names_after_dot
1 failed, 64 passed, 73 subtests passed in 9.44s
[assistant] The `t.current_user()` case is an `Anonymous` call node, which is existing behaviour and out of scope here. I'll drop that assertion rather than pin it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsInstance(parse_one(\"SELECT current_user\").selects[0], exp.CurrentUser)\n        self.assertIsInstance(parse_one(\"SELECT t.current_user()\").selects[0], exp.CurrentUser)\n", "new_string": "        self.assertIsInstance(parse_one(\"SELECT current_user\").selects[0], exp.CurrentUser)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-185700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; git diff --stat; $PY -m ruff check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -2", "description": "Run full suite, diff stat, and lint"}
[tool_result] ................ [ 85%]
..................................................................................................................................................................                                               [100%]
1106 passed, 18000 subtests passed in 46.38s
sqlglot/parser.py    | 11 +++++++++--
 tests/test_parser.py | 10 ++++++++++
 2 files changed, 19 insertions(+), 2 deletions(-)
All checks passed!
2 files already formatted
[assistant] Fixed. After a dot, no-parenthesis function names like `current_user`, `current_date`, and `sysdate` now stay plain identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   -> SELECT mytable.current_user FROM mytable
SELECT t.current_date, t.sysdate FROM t    -> SELECT t.current_date, t.sysdate FROM t
SELECT current_user FROM t                 -> SELECT CURRENT_USER() FROM t   (unchanged)
SELECT t.CURRENT_USER() FROM t             -> SELECT t.CURRENT_USER() FROM t (unchanged)
```

**Cause:** In `_parse_column_ops` (`sqlglot/parser.py`), the dot branch parsed the ri
…[347 chars elided]…
`optional_parens=False`, so only the paren form `x.f()` is treated as a function call.
- `tests/test_parser.py`: added `test_no_paren_function_names_after_dot`, which round-trips the dotted cases and checks that unqualified `current_user` still parses to `exp.CurrentUser`.

**Verification:** the full suite passes with the project's interpreter (1106 tests, up from 1105 with the new one). `ruff check` and `ruff format --check` are clean on both files.

I haven't committed anything. The `t.current_user()` paren form still produces an `Anonymous` node inside a `Dot`, as before; I left that alone.
