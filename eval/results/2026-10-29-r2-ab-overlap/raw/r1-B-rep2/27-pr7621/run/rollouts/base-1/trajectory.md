# trajectory base-1

final message:
After a dot, no-parenthesis function names such as `CURRENT_USER` and `CURRENT_DATE` now parse as column identifiers and round-trip unchanged. The full suite passes (1106 tests, 18001 subtests) and ruff check and format are clean.

```
SELECT mytable.current_user FROM mytable  ->  SELECT mytable.current_user FROM mytable
```

**The change** is in `sqlglot/parser.py`, in `_parse_column_ops`. A DOT has no operator function, so it fell through to `_parse_field`, which parsed `current_user` as a function call. I added a branch that, when the token after a DOT is a no-paren function name and not followed by `(`, parses it as an identifier. Everything else is untouched:
- `t.current_user()` still parses as a qualified function call.
- Bare `current_user` still becomes `CURRENT_USER()`.
- `t.current_user + 1` and `a.current_user.b` keep the column form.

**Test:** I added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It covers the round-trips above and checks that bare `current_user` still becomes `CURRENT_USER()`.

I haven't committed anything; the diff is in the working tree.

## events
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTION\\|_parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\b\\|def _parse_primary\" sqlglot/parser.py | head -60; ls .lithify/harness/scripts/", "description": "Locate no-paren function handling in parser"}
[tool_result] 23 matches in 11 files:

1468:0:t.ClassVar = {
432:0:t.ClassVar[dict] = {
5350:0:self.expression(
6503:0:
6561:0:
6659:0:exp.Expr | None) -> exp.Expr | None:
6757:0:
6852:0:
7429:0:
8391:0:
sqlglot/parser.py:769:*NO_PAREN_FUNCTIONS,
sqlglot/parser.py:5354:self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
sqlglot/parser.py:5824:return self._parse_column_ops(this)
sqlglot/parser.py:6059:return self._parse_column_ops(interval)
sqlglot/parser.py:6069:return self._parse_column_ops(data_type)
sqlglot/parser
…[16 chars elided]…
self._parse_column_ops(this)
sqlglot/parser.py:6107:return self._parse_column_ops(data_type)
sqlglot/parser.py:6478:column = self._parse_column_ops(this) if this else this
sqlglot/parser.py:6680:field = self._parse_column_ops(field)
sqlglot/parser.py:6779:def _parse_field(
sqlglot/parser.py:6846:parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
sqlglot/parser.py:6854:return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
sqlglot/parser.py:7444:def _parse_primary_key(
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 6779,6870p sqlglot/parser.py; echo ----; sed -n 6640,6700p sqlglot/parser.py; echo ----; cat .lithify/harness/scripts/probe_parse.py | head -40", "description": "Read field and no-paren parsing code"}
[tool_result]     def _parse_field(
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
            field = self._parse_primary() or self._parse_function(
                anonymous=anonymous_func, a
…[6046 chars elided]…
ef probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT mytable.current_date FROM mytable' 'SELECT t.sysdate FROM t' 'SELECT a.current_user.b FROM t' 'SELECT current_user FROM t' 'SELECT t.current_timestamp, t.localtime FROM t' | $PY -I .lithify/harness/scripts/probe_parse.py --read oracle; echo; p
…[56 chars elided]…
 'SELECT t.current_date FROM t' | $PY -I .lithify/harness/scripts/probe_parse.py --read postgres; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' | $PY -I .lithify/harness/scripts/probe_parse.py --read \"\"; echo; $PY -I -c \"import sqlglot;print(repr(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').selects[0]))\"", "description": "Reproduce the bug across several dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'

Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT mytable.current_date FROM mytable' 'SELECT t.sysdate FROM t' 'SELECT a.current_user.b FROM t' 'SELECT current_user FROM t' 'SELECT t.current_timestamp, t.localtime FROM t' | $PY .lithify/harness/scripts/probe_parse.py --read oracle; echo; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT t.current_date FROM t' | $PY .lithify/harness/scripts/probe_parse.py --read postgres; echo; $PY -c \"import sqlglot;print(sqlglot.__file__);print(repr(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').selects[0]))\"", "description": "Reproduce the bug with PYTHONPATH set to worktree"}
[tool_result] OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.CURRENT_USER() FROM mytable
OK        SELECT mytable.current_date FROM mytable
          SELECT mytable.CURRENT_DATE FROM mytable
OK        SELECT t.sysdate FROM t
          SELECT t.sysdate FROM t
OK        SELECT a.current_user.b FROM t
          SELECT a.CURRENT_USER().b FROM t
OK        SELECT current_user FROM t
          SELECT CURRENT_USER() FROM t
OK        SELECT t.current_timestamp, t.localtime FROM t
          SELECT t.CURRENT_TIMESTAMP, t.localtime FROM t

OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.CURRENT_USER FROM mytable
OK        SELECT t.current_date FROM t
          SELECT t.CURRENT_DATE FROM t

~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/__init__.py
Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
[tool_use Bash] {"command": "grep -n \"TokenType.DOT:\" sqlglot/parser.py | head; grep -n \"COLUMN_OPERATORS = \" -A12 sqlglot/parser.py | head -30; grep -n \"def _parse_column_reference\" -A12 sqlglot/parser.py; grep -n \"NO_PAREN_FUNCTIONS = \" -A3 sqlglot/parser.py; grep -n \"def _parse_id_var\" -A6 sqlglot/parser.py", "description": "Inspect column operator and id parsing helpers"}
[tool_result] 2 matches in 2 files:

1009:0:None,
3834:0:
6561:    def _parse_column_reference(self) -> exp.Expr | None:
6562-        this = self._parse_field()
6563-        if (
6564-            not this
6565-            and self._match(TokenType.VALUES, advance=False)
6566-            and self.VALUES_FOLLOWED_BY_PAREN
6567-            and (not self._next or self._next.token_type != TokenType.L_PAREN)
6568-        ):
6569-            this = self._parse_id_var()
6570-
6571-        if isinstance(this, exp.Identifier):
6572-            # We bubble up comments from the Identifier to the Column
6573-            this = self.expression(exp.Column(this=this), comments=this.pop_comments())
8330:    def _parse_id_var(
8331-        self,
8332-        any_token: bool = True,
8333-        tokens: t.Collection[TokenType] | None = None,
8334-    ) -> exp.Expr | None:
8335-        expression = self._parse_identifier()
8336-        if not expression and (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "            elif op and self._curr:\n                field = self._parse_column_reference() or self._parse_bitwise()", "new_string": "            elif op and self._curr:\n                if (\n                    op_token == TokenType.DOT\n                    and self._curr.token_type in self.NO_PAREN_FUNCTIONS\n                    and (not self._next or self._next.token_type != TokenType.L_PAREN)\n                ):\n                    field = self.expression(exp.Column(this=self._parse_id_var()))\n                else:\n                    field = self._parse_column_reference() or self._parse_bitwise()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT mytable.current_date FROM mytable' 'SELECT t.sysdate FROM t' 'SELECT a.current_user.b FROM t' 'SELECT current_user FROM t' 'SELECT t.current_user + 1 FROM t' 'SELECT t.current_user() FROM t' 'SELECT t.current_timestamp,
…[42 chars elided]…
s/scripts/probe_parse.py --read oracle; echo; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT t.current_date FROM t' 'SELECT t.current_user() FROM t' | $PY .lithify/harness/scripts/probe_parse.py --read postgres; $PY -c \"import sqlglot;print(repr(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').selects[0]))\"", "description": "Verify fix with probe across dialects"}
[tool_result] OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.CURRENT_USER() FROM mytable
OK        SELECT mytable.current_date FROM mytable
          SELECT mytable.CURRENT_DATE FROM mytable
OK        SELECT t.sysdate FROM t
          SELECT t.sysdate FROM t
OK        SELECT a.current_user.b FROM t
          SELECT a.CURRENT_USER().b FROM t
OK        SELECT current_user FROM t
          SELECT CURRENT_USER() FROM t
OK        SELECT t.current_user + 1 FROM t
          SELECT t.CURR
…[60 chars elided]…
 t
          SELECT t.current_user() FROM t
OK        SELECT t.current_timestamp, t.localtime FROM t
          SELECT t.CURRENT_TIMESTAMP, t.localtime FROM t

OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.CURRENT_USER FROM mytable
OK        SELECT t.current_date FROM t
          SELECT t.CURRENT_DATE FROM t
OK        SELECT t.current_user() FROM t
          SELECT t.current_user() FROM t
Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
[tool_use Bash] {"command": "grep -n \"TokenType.DOT\\|exp.Dot\\b\\|def _parse_dot\\|def _parse_column(\" sqlglot/parser.py | head -30; grep -rn \"def build_dot\\|def to_dot\" sqlglot/*.py | head", "description": "Find where DOT nodes are built in parser"}
[tool_result] rg: regex parse error:
    (?:TokenType.DOT|exp.Dot\b|def _parse_dot|def _parse_column()
    ^
error: unclosed group
0 matches for 'TokenType.DOT\|exp.Dot\b\|def _parse_dot\|def _parse_column('
[tool_use Bash] {"command": "grep -n \"TokenType.DOT\" sqlglot/parser.py | head -30; grep -n \"def _parse_column(\" -A12 sqlglot/parser.py; grep -n \"DOT: lambda\\|TokenType.DOT:\" sqlglot/parser.py sqlglot/dialects/dialect.py | head", "description": "Locate DOT token handling in parser"}
[tool_result] 16 matches in 13 files:

1009:0:None,
1010:0:lambda self, this, to: self.expression(exp.JSONCast(this=this, to=to)),
3356:0:
3834:0:
4335:0:
4671:0:
6131:0:
6609:0:
6686:0:
6781:0:
7009:0:
7583:0:
sqlglot/parser.py:1041:TokenType.DOTCOLON,
sqlglot/parser.py:4603:has_dot = self._match(TokenType.DOT)
sqlglot/parser.py:6507:has_dot = self._match(TokenType.DOT)
sqlglot/parser.py:6679:op_token == TokenType.DOT
6472:    def _parse_column(self) -> exp.Expr | None:
6473-        column: exp.Expr | None =
…[226 chars elided]…
n = self._parse_column_ops(this) if this else this
6479-
6480-        if column:
6481-            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
6482-                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
6483-            if self.COLON_IS_VARIANT_EXTRACT:
6484-                column = self._parse_colon_as_variant_extract(column)
2 matches in 1 files:

sqlglot/parser.py:1009:TokenType.DOT: None,
sqlglot/parser.py:3834:if self._next and not self._next.token_type == TokenType.DOT:
[tool_use Bash] {"command": "sed -n 6495,6560p sqlglot/parser.py", "description": "Read the fast column parts parser"}
[tool_result]         index = self._index
        parts: list[exp.Identifier] | None = None
        all_comments: list[str] | None = None

        while self._match_set(self.IDENTIFIER_TOKENS):
            token = self._prev
            comments = self._prev_comments

            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
                self._retreat(index)
                return None

            has_dot = self._match(TokenType.DOT)
            curr_tt = self._curr.token_type
…[1035 chars elided]…
this=parts[0])
        elif n == 2:
            column = exp.Column(this=parts[1], table=parts[0])
        elif n == 3:
            column = exp.Column(this=parts[2], table=parts[1], db=parts[0])
        else:
            column = exp.Column(this=parts[3], table=parts[2], db=parts[1], catalog=parts[0])

            for i in range(4, n):
                column = exp.Dot(this=column, expression=parts[i])

        if all_comments:
            column.add_comments(all_comments)

        return column
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.tokens import Tokenizer\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects import Dialect\nt=Dialect.get_or_raise('').tokenize('mytable.current_user')\nprint([(x.token_type,x.text) for x in t])\nprint(Parser.NO_PAREN_FUNCTIONS.keys() if hasattr(Parser,'NO_PAREN_FUNCTIONS') else None)\nprint(Parser.COLUMN_OPERATORS.get(__import__('sqlglot').tokens.TokenType.DOT))\n\"; grep -n \"_parse_column_parts_fast()\" -B3 sqlglot/parser.py | head; grep -n \"IDENTIFIER_TOKENS = \\|^ID_VAR_TOKENS\" sqlglot/parser.py", "description": "Inspect tokens and parser config for the DOT case"}
[tool_result ERROR] Exit code 1
[(<TokenType.VAR: 87>, 'mytable'), (<TokenType.DOT: 8>, '.'), (<TokenType.CURRENT_USER: 249>, 'current_user')]
dict_keys([<TokenType.CURRENT_DATE: 244>, <TokenType.CURRENT_DATETIME: 245>, <TokenType.CURRENT_TIME: 247>, <TokenType.CURRENT_TIMESTAMP: 248>, <TokenType.CURRENT_USER: 249>, <TokenType.CURRENT_ROLE: 250>])
None
6470-        return primary_parser(self, token)
6471-
6472-    def _parse_column(self) -> exp.Expr | None:
6473:        column: exp.Expr | None = self._parse_column_parts_fast()
0 matches for 'IDENTIFIER_TOKENS = \|^ID_VAR_TOKENS'
[assistant] The fast path isn't involved. The real cause: `DOT` maps to `None` in `COLUMN_OPERATORS`, so my edit sat in a branch the DOT never reaches; the DOT goes through the `else` branch, which calls `_parse_field`, and that parses `current_user` as a function. I'll move the check into that path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "            elif op and self._curr:\n                if (\n                    op_token == TokenType.DOT\n                    and self._curr.token_type in self.NO_PAREN_FUNCTIONS\n                    and (not self._next or self._next.token_type != TokenType.L_PAREN)\n                ):\n                    field = self.expression(exp.Column(this=self._parse_id_var()))\n                else:\n                    field = self._parse_column_reference() or self._parse_bitwise()", "new_string": "            elif op and self._curr:\n                field = self._parse_column_reference() or self._parse_bitwise()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                if isinstance(field, exp.Column) and self._match(TokenType.DOT, advance=False):\n                    field = self._parse_column_ops(field)\n            else:\n                field = self._parse_field(an
…[325 chars elided]…
lf._curr.token_type in self.NO_PAREN_FUNCTIONS\n                and (not self._next or self._next.token_type != TokenType.L_PAREN)\n            ):\n                # After a dot, a no-parenthesis function name such as CURRENT_USER is a column identifier\n                field = self._parse_id_var()\n            else:\n                field = self._parse_field(any_token=True, anonymous_func=True)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-152057-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; printf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT mytable.current_date FROM mytable' 'SELECT t.sysdate FROM t' 'SELECT a.current_user.b FROM t' 'SELECT current_user FROM t' 'SELECT t.current_user + 1 FROM t' 'SELECT t.current_user() FROM t' 'SELECT t.current_timestamp,
…[89 chars elided]…
rintf '%s\\n' 'SELECT mytable.current_user FROM mytable' 'SELECT t.current_date FROM t' 'SELECT t.current_user() FROM t' 'SELECT t.current_user, current_user FROM t' | $PY .lithify/harness/scripts/probe_parse.py --read postgres; $PY -c \"import sqlglot;print(repr(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').selects[0]))\"", "description": "Re-verify the fix with the probe script"}
[tool_result] OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.current_user FROM mytable
OK        SELECT mytable.current_date FROM mytable
          SELECT mytable.current_date FROM mytable
OK        SELECT t.sysdate FROM t
          SELECT t.sysdate FROM t
OK        SELECT a.current_user.b FROM t
          SELECT a.current_user.b FROM t
OK        SELECT current_user FROM t
          SELECT CURRENT_USER() FROM t
OK        SELECT t.current_user + 1 FROM t
          SELECT t.current_
…[188 chars elided]…
amp, t.localtime FROM t

OK        SELECT mytable.current_user FROM mytable
          SELECT mytable.current_user FROM mytable
OK        SELECT t.current_date FROM t
          SELECT t.current_date FROM t
OK        SELECT t.current_user() FROM t
          SELECT t.current_user() FROM t
OK        SELECT t.current_user, current_user FROM t
          SELECT t.current_user, CURRENT_USER FROM t
Column(
  this=Identifier(this=current_user, quoted=False),
  table=Identifier(this=mytable, quoted=False))
[assistant] The fix works and the function-call forms are unchanged. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "grep -rn \"current_user\\|CURRENT_USER\" tests/*.py tests/dialects/*.py | head; grep -n \"def test_\" tests/test_parser.py | head -5; grep -n \"def test_\" tests/dialects/test_dialect.py | head -3", "description": "Find existing tests covering current_user"}
[tool_result] tests/test_transpile.py:935:            "ALTER AGGREGATE bla(foo) OWNER TO CURRENT_USER",
tests/test_transpile.py:937:            "ALTER ROLE CURRENT_USER WITH REPLICATION",
tests/dialects/test_clickhouse.py:1860:            "CREATE VIEW v SQL SECURITY DEFINER DEFINER=CURRENT_USER AS SELECT 1",
tests/dialects/test_clickhouse.py:1867:            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER=CURRENT_USER",
tests/dialects/test_exasol.py:18:        self.validate_identity("SELECT USER", "SELECT 
…[42 chars elided]…
py:19:        self.validate_identity("SELECT USER()", "SELECT CURRENT_USER")
tests/dialects/test_exasol.py:20:        self.validate_identity("SELECT CURRENT_USER", "SELECT CURRENT_USER")
tests/dialects/test_exasol.py:672:            "SELECT CURRENT_USER",
tests/dialects/test_exasol.py:675:                "spark": "SELECT CURRENT_USER()",
tests/dialects/test_exasol.py:676:                "trino": "SELECT CURRENT_USER",
64 matches in 64 files:

100:0:
103:0:
1032:0:
98 matches in 98 files:

115:0:
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/test_parser.py | head -3; sed -n 1,30p tests/test_parser.py | grep -n \"class\\|import\"", "description": "Look at test_parser.py structure"}
[tool_result] 64 matches in 64 files:

100:0:
1:import time
2:import unittest
3:from unittest.mock import patch
5:from sqlglot import Parser, exp, parse, parse_one
6:from sqlglot.errors import ErrorLevel, ParseError
7:from sqlglot.parser import logger as parser_logger
8:from tests.helpers import assert_logger_contains
11:class TestParser(unittest.TestCase):
[tool_use Bash] {"command": "tail -20 tests/test_parser.py; grep -n \"def test_\" tests/test_parser.py | tail -3", "description": "View end of test_parser.py"}
[tool_result]         self.assertIsInstance(parse_one(sql, max_nodes=1_000_000), exp.Select)

        width = 10000
        depth = 100
        expr = "x" + "=x" * depth
        cols = [expr for _ in range(width)]
        sql = f"SELECT {','.join(cols)}"

        with self.assertRaises(ParseError) as ctx:
            parse_one(sql, max_nodes=1_000_000)
        self.assertIn("Maximum number of AST nodes", str(ctx.exception))

        with self.assertRaises(ParseError) as ctx:
            parse_one(sql, max_nodes=50_000)
        self.assertIn("(50000)", str(ctx.exception))

        # Hitting a limit in one parse doesn't affect the next
        with self.assertRaises(ParseError):
            parse_one("SELECT " + ",".join(f"x={i}" for i in range(100)), max_nodes=5)
        self.assertIsInstance(parse_one("SELECT 1, 2, 3"), exp.Select)
973:0:
978:0:
990:0:
[tool_use Bash] {"command": "cat >> tests/test_parser.py <<'EOF'\n\n    def test_no_paren_function_names_after_dot(self):\n        for sql in (\n            \"SELECT mytable.current_user FROM mytable\",\n            \"SELECT mytable.current_date FROM mytable\",\n            \"SELECT a.current_user.b FROM t\",\n        ):\n            with self.subTest(sql=sql):\n                self.assertEqual(parse_one(sql).sql
…[63 chars elided]…
current_user()\").selects[0], exp.Anonymous | exp.CurrentUser | exp.Func)\n        self.assertEqual(parse_one(\"SELECT current_user\").sql(), \"SELECT CURRENT_USER()\")\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -15", "description": "Add regression test and run it"}
[tool_result]         ):
            with self.subTest(sql=sql):
                self.assertEqual(parse_one(sql).sql(), sql)
    
>       self.assertIsInstance(parse_one("SELECT t.current_user()").selects[0], exp.Anonymous | exp.CurrentUser | exp.Func)
E       AssertionError: Dot(
E         this=Identifier(this=t, quoted=False),
E         expression=Anonymous(this=current_user)) is not an instance of sqlglot.expressions.core.Anonymous | sqlglot.expressions.functions.CurrentUser | sqlglot.expressions.core.Func

tests/test_parser.py:1123: AssertionError
----------------------------- Captured stdout call -----------------------------
uuu
=========================== short test summary info ============================
FAILED tests/test_parser.py::TestParser::test_no_paren_function_names_after_dot
1 failed, 64 deselected, 3 subtests passed in 0.06s
[assistant] My extra assertion was wrong: `t.current_user()` parses as a qualified `Anonymous` call, which is existing behavior. I'll drop that line and keep the round-trip checks.
[tool_use Bash] {"command": "python3 - <<'EOF'\np=\"tests/test_parser.py\"\ns=open(p).read()\ns=s.replace('        self.assertIsInstance(parse_one(\"SELECT t.current_user()\").selects[0], exp.Anonymous | exp.CurrentUser | exp.Func)\\n','')\nopen(p,\"w\").write(s)\nEOF\ntail -12 tests/test_parser.py; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -3; git diff --stat", "description": "Trim bad assertion and rerun the new test"}
[tool_result]         self.assertIsInstance(parse_one("SELECT 1, 2, 3"), exp.Select)

    def test_no_paren_function_names_after_dot(self):
        for sql in (
            "SELECT mytable.current_user FROM mytable",
            "SELECT mytable.current_date FROM mytable",
            "SELECT a.current_user.b FROM t",
        ):
            with self.subTest(sql=sql):
                self.assertEqual(parse_one(sql).sql(), sql)

        self.assertEqual(parse_one("SELECT current_user").sql(), "SELECT CURRENT_USER()")
.                                                                     [100%]
1 passed, 64 deselected, 3 subtests passed in 0.04s
 sqlglot/parser.py    |  8 ++++++++
 tests/test_parser.py | 11 +++++++++++
 2 files changed, 19 insertions(+)
[assistant] Now the full suite as the final gate, plus the style check.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 600 $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; ($PY -m ruff check sqlglot/parser.py tests/test_parser.py && $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py) 2>&1 | tail -5", "description": "Run full test suite and lint checks", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 600000}
[tool_result] ................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
............................................
…[299 chars elided]…
......................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                              [100%]
1106 passed, 18001 subtests passed in 59.01s
[assistant] After a dot, no-parenthesis function names such as `CURRENT_USER` and `CURRENT_DATE` now parse as column identifiers and round-trip unchanged. The full suite passes (1106 tests, 18001 subtests) and ruff check and format are clean.

```
SELECT mytable.current_user FROM mytable  ->  SELECT mytable.current_user FROM mytable
```

**The change** is in `sqlglot/parser.py`, in `_parse_column_ops`. A DOT has no operator function, so it fell through to `_parse_field`, which parsed `current_user` as a function call. I added a branch that, when the token after a DOT is a no-paren function name and not followed by `(`, parses it as an identifier. Everything else is untouched:
- `t.current_user()` still parses as a qualified function call.
- Bare `current_user` still becomes `CURRENT_USER()`.
- `t.current_user + 1` and `a.current_user.b` keep the column form.

**Test:** I added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It covers the round-trips above and checks that bare `current_user` still becomes `CURRENT_USER()`.

I haven't committed anything; the diff is in the working tree.
