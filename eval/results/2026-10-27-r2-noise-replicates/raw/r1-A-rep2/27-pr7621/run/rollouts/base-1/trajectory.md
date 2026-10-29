# trajectory base-1

final message:
Fixed. A name that is also a no-parenthesis function (`CURRENT_USER`, `CURRENT_DATE`, `SYSDATE`, …) now stays a column identifier after a dot, so `SELECT mytable.current_user FROM mytable` round-trips unchanged.

**Cause:** the dotted part of a column reference was parsed with `_parse_field(anonymous_func=True)`, which calls `_parse_function` with `optional_parens=True`. That turned a bare name into a function call. The fix is in `sqlglot/parser.py`:
- `_parse_field` takes a new `optional_parens` argument (default `True`, so other callers are unchanged).
- The dot-field branch of `_parse_column_ops` passes `optional_parens=False`.

Names followed by `()` still parse as function calls, so `mytable.current_user()` is unchanged.

**Verification:**
- Reproduced the bug before the change; after it, `mytable.current_user`, `a.b.current_date`, `x.sysdate` and `current_timestamp` all round-trip across the default, Oracle, Snowflake and Postgres dialects.
- Added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It checks the round-trip for bare dotted names and that `()` still produces a function.
- Full suite with the project's pytest command: 1106 passed, 18000 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

I haven't committed anything. The unqualified `SELECT current_user` still becomes `CURRENT_USER()` in the default dialect, which is existing behaviour and outside this change.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"NO_PAREN_FUNCTIONS\\|NO_PAREN_FUNCTION_PARSERS\\|_parse_column_ops\\|def _parse_column(\" sqlglot/parser.py | head -50 && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT current_user FROM mytable','SELECT a.current_date, b.sysdate FROM t a']:\n    print(repr(sqlglot.transpile(s)[0]))\n\"", "description": "Check parser code locations and reproduce bug"}
[tool_result] 432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
769:        *NO_PAREN_FUNCTIONS,
1468:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
5350:        self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
5354:        self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
5824:        return self._parse_column_ops(this)
6059:            return self._parse_column_ops(interval)
6069:            return self._parse_column_ops(data_type)
6077:                this = self._parse_column_ops(this)
6107
…[273 chars elided]…
S:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6680:                    field = self._parse_column_ops(field)
6846:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6852:            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
'SELECT mytable.CURRENT_USER() FROM mytable'
'SELECT CURRENT_USER() FROM mytable'
'SELECT a.CURRENT_DATE, b.sysdate FROM t AS a'
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "offset": 6472, "limit": 70}
[tool_result] 6472	    def _parse_column(self) -> exp.Expr | None:
6473	        column: exp.Expr | None = self._parse_column_parts_fast()
6474	        if column is None:
6475	            this = self._parse_column_reference()
6476	            if not this:
6477	                this = self._parse_bracket(this)
6478	            column = self._parse_column_ops(this) if this else this
6479	
6480	        if column:
6481	            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
6482	                column.set("join_mar
…[1802 chars elided]…
nts)
6525	                self._prev_comments = []
6526	
6527	            parts.append(
6528	                self.expression(
6529	                    exp.Identifier(
6530	                        this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
6531	                    ),
6532	                    token,
6533	                )
6534	            )
6535	
6536	            if not has_dot:
6537	                break
6538	
6539	        if parts is None:
6540	            return None
6541	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "offset": 6659, "limit": 45}
[tool_result] 6659	    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6660	        while self._curr.token_type in self.BRACKETS:
6661	            this = self._parse_bracket(this)
6662	
6663	        column_operators = self.COLUMN_OPERATORS
6664	        cast_column_operators = self.CAST_COLUMN_OPERATORS
6665	        while self._curr:
6666	            op_token = self._curr.token_type
6667	
6668	            if op_token not in column_operators:
6669	                break
6670	            op
…[1242 chars elided]…
    this = op(self, this, field)
6694	            elif isinstance(this, exp.Column) and not this.args.get("catalog"):
6695	                this = self.expression(
6696	                    exp.Column(
6697	                        this=field,
6698	                        table=this.this,
6699	                        db=this.args.get("table"),
6700	                        catalog=this.args.get("db"),
6701	                    ),
6702	                    comments=this.comments,
6703	                )
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "offset": 6835, "limit": 30}
[tool_result] 6835	    ) -> exp.Expr | None:
6836	        if not self._curr:
6837	            return None
6838	
6839	        comments = self._curr.comments
6840	        prev = self._prev
6841	        token = self._curr
6842	        token_type = self._curr.token_type
6843	        this: str | exp.Expr = self._curr.text
6844	        upper = self._curr.text.upper()
6845	
6846	        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6847	        if optional_parens and parser and token_type not in self.INVALID_FU
…[146 chars elided]…
ype != TokenType.L_PAREN:
6852	            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6853	                self._advance()
6854	                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
6855	
6856	            return None
6857	
6858	        if any_token:
6859	            if token_type in self.RESERVED_TOKENS:
6860	                return None
6861	        elif token_type not in self.FUNC_TOKENS:
6862	            return None
6863	
6864	        self._advance(2)
[tool_use Bash] {"command": "grep -n \"def _parse_field\\|def _parse_function_call\\|def _parse_primary\\|def _parse_function(\" sqlglot/parser.py && sed -n '/def _parse_field(/,/^    def /p' sqlglot/parser.py | head -30", "description": "Locate _parse_field definition"}
[tool_result] 6757:    def _parse_primary(self) -> exp.Expr | None:
6779:    def _parse_field(
6796:    def _parse_function(
6829:    def _parse_function_call(
7072:    def _parse_field_def(self) -> exp.Expr | None:
7429:    def _parse_primary_key_part(self) -> exp.Expr | None:
7444:    def _parse_primary_key(
8391:    def _parse_primary_or_var(self) -> exp.Expr | None:
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
            field = self._parse_primary() or self._parse_function(
                anonymous=anonymous_func, any_token=any_token
            )
        return field or self._parse_id_var(any_token=any_token, tokens=tokens)

    def _parse_function(
[tool_use Bash] {"command": "sed -n 6796,6812p sqlglot/parser.py && grep -rn \"anonymous_func=True\" sqlglot/ | head", "description": "Inspect _parse_function signature and callers"}
[tool_result]     def _parse_function(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
        # This allows us to also parse {fn <function>} syntax (Snowflake, MySQL support this)
        # See: https://community.snowflake.com/s/article/SQL-Escape-Sequences
        fn_syntax = False
        if (
            self._match(TokenType.L_BRACE, advance=False)
            and self._next
            and self._next.text.upper() == "FN"
        ):
            self._advance(2)
            fn_syntax = True
sqlglot/parser.py:6682:                field = self._parse_field(any_token=True, anonymous_func=True)
sqlglot/parsers/clickhouse.py:482:            exp.EngineProperty(this=self._parse_field(any_token=True, anonymous_func=True))
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\nold=\"\"\"        tokens: t.Collection[TokenType] | None = None,\n        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous=anonymous_func, any_token=any_token)\n                or self._parse_primary()\n      
…[1011 chars elided]…
for s in ['SELECT mytable.current_user FROM mytable','SELECT a.b.current_date, x.sysdate FROM t','SELECT mytable.current_user() FROM mytable','SELECT current_user FROM mytable','SELECT CURRENT_DATE, a.current_timestamp FROM t']:\n    for d in [None,'oracle','snowflake','postgres']:\n        print(d, sqlglot.transpile(s, read=d, write=d)[0])\n\"", "description": "Apply fix in parser and reproduce"}
[tool_result] None SELECT mytable.current_user FROM mytable
oracle SELECT mytable.current_user FROM mytable
snowflake SELECT mytable.current_user FROM mytable
postgres SELECT mytable.current_user FROM mytable
None SELECT a.b.current_date, x.sysdate FROM t
oracle SELECT a.b.current_date, x.sysdate FROM t
snowflake SELECT a.b.current_date, x.sysdate FROM t
postgres SELECT a.b.current_date, x.sysdate FROM t
None SELECT mytable.current_user() FROM mytable
oracle SELECT mytable.current_user() FROM mytable
snowflake SELECT mytable.current_user() FROM mytable
postgres SELECT mytable.current_user() FROM mytable
None SELECT CURRENT_USER() FROM mytable
oracle SELECT CURRENT_USER() FROM mytable
snowflake SELECT CURRENT_USER() FROM mytable
postgres SELECT CURRENT_USER FROM mytable
None SELECT CURRENT_DATE, a.current_timestamp FROM t
oracle SELECT CURRENT_DATE, a.current_timestamp FROM t
snowflake SELECT CURRENT_DATE, a.current_timestamp FROM t
postgres SELECT CURRENT_DATE, a.current_timestamp FROM t
[assistant] The fix round-trips the dotted names. Now I'll add a regression test and run the project's test suite.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_parser.py | head -5; grep -n \"CURRENT_DATE\\|current_date\" tests/*.py | head", "description": "Find existing tests for no-paren functions"}
[tool_result] 12:    def test_parse_empty(self):
16:    def test_parse_into(self):
45:    def test_parse_into_error(self):
66:    def test_parse_into_errors(self):
94:    def test_column(self):
tests/test_executor.py:713:            ("DAY(CURRENT_DATETIME())", now.day),
tests/test_executor.py:714:            ("YEAR(CURRENT_DATE())", now.year),
tests/test_executor.py:715:            ("MONTH(CURRENT_DATE())", now.month),
tests/test_executor.py:716:            ("DAY(CURRENT_DATE())", now.day),
tests/test_executo
…[149 chars elided]…
TE()) + 1, YEAR(CURRENT_DATE()) * 10)",
tests/test_executor.py:729:            ("YEAR(CURRENT_DATE()) = (YEAR(CURRENT_DATE()))", True),
tests/test_executor.py:730:            ("YEAR(CURRENT_DATE()) <> (YEAR(CURRENT_DATE()))", False),
tests/test_optimizer.py:2008:                        "SELECT x FROM UNNEST(GENERATE_DATE_ARRAY('2021-01-01', current_date(), interval 1 day)) AS x"
tests/test_transpile.py:40:        self.assertEqual(transpile("SELECT 1 current_date")[0], "SELECT 1 AS current_date")
[tool_use Bash] {"command": "sed -n 94,125p tests/test_parser.py", "description": "View test_column for placement"}
[tool_result]     def test_column(self):
        columns = parse_one("select a, ARRAY[1] b, case when 1 then 1 end").find_all(exp.Column)
        assert len(list(columns)) == 1

        self.assertIsNotNone(parse_one("date").find(exp.Column))

    def test_tuple(self):
        parse_one("(a,)").assert_is(exp.Tuple)

    def test_structs(self):
        cast = parse_one("cast(x as struct<int>)")
        self.assertIsInstance(cast.to.expressions[0], exp.DataType)
        self.assertEqual(cast.sql(), "CAST(x AS S
…[269 chars elided]…
e_one(".2"), parse_one("0.2"))

    def test_unnest(self):
        unnest_sql = "UNNEST(foo)"
        expr = parse_one(unnest_sql)
        self.assertIsInstance(expr, exp.Unnest)
        self.assertIsInstance(expr.expressions, list)
        self.assertEqual(expr.sql(), unnest_sql)

    def test_unnest_projection(self):
        expr = parse_one("SELECT foo IN UNNEST(bla) AS bar")
        self.assertIsInstance(expr.selects[0], exp.Alias)
        self.assertEqual(expr.selects[0].output_name, "bar")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_tuple(self):", "new_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_no_paren_function_na
…[181 chars elided]…
      with self.subTest(sql=sql):\n                self.assertEqual(transpile(sql)[0], sql)\n                self.assertFalse(parse_one(sql).find(exp.CurrentUser, exp.CurrentDate, exp.Sysdate))\n\n        self.assertEqual(\n            transpile(\"SELECT mytable.current_user() FROM mytable\")[0],\n            \"SELECT mytable.current_user() FROM mytable\",\n        )\n\n    def test_tuple(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "head -10 tests/test_parser.py | grep import; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k dot 2>&1 | tail -15", "description": "Run new parser test"}
[tool_result] import time
import unittest
from unittest.mock import patch
from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains
        self.assertEqual(
>           transpile("SELECT mytable.current_user() FROM mytable")[0],
            ^^^^^^^^^
            "SELECT mytable.current_user() FROM mytable",
        )
E       NameError: name 'transpile' is not defined


…[76 chars elided]…
tdout call -----------------------------
uu
=========================== short test summary info ============================
SUBFAILED(sql='SELECT mytable.current_user FROM mytable') tests/test_parser.py::TestParser::test_no_paren_function_names_after_dot
SUBFAILED(sql='SELECT a.b.current_date, x.sysdate FROM t') tests/test_parser.py::TestParser::test_no_paren_function_names_after_dot
FAILED tests/test_parser.py::TestParser::test_no_paren_function_names_after_dot
3 failed, 64 deselected in 0.07s
[assistant] The test used `transpile`, which isn't imported in this file, and the `find` check was unnecessary. I'll rewrite it to use `parse_one` and check the round-trip and the node type directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        for sql in (\n            \"SELECT mytable.current_user FROM mytable\",\n            \"SELECT a.b.current_date, x.sysdate FROM t\",\n        ):\n            with self.subTest(sql=sql):\n                self.a
…[459 chars elided]…
 FROM t\",\n        ):\n            with self.subTest(sql=sql):\n                self.assertEqual(parse_one(sql).sql(), sql)\n                self.assertFalse(any(isinstance(n, exp.Func) for n in parse_one(sql).walk()))\n\n        self.assertEqual(\n            parse_one(\"SELECT mytable.current_user() FROM mytable\").sql(),\n            \"SELECT mytable.current_user() FROM mytable\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-090535-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k dot 2>&1 | tail -3; git stash list >/dev/null; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run new test then full project test suite"}
[tool_result] .                                                                      [100%]
1 passed, 64 deselected, 2 subtests passed in 0.05s
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
..................................................................................................................................................................                                               [100%]
1106 passed, 18000 subtests passed in 49.97s
[assistant] Full suite passes. Quick lint check on the changed files:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parser.py tests/test_parser.py && $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 sqlglot/parser.py    |  9 +++++++--
 tests/test_parser.py | 14 ++++++++++++++
 2 files changed, 21 insertions(+), 2 deletions(-)
[assistant] Fixed. A name that is also a no-parenthesis function (`CURRENT_USER`, `CURRENT_DATE`, `SYSDATE`, …) now stays a column identifier after a dot, so `SELECT mytable.current_user FROM mytable` round-trips unchanged.

**Cause:** the dotted part of a column reference was parsed with `_parse_field(anonymous_func=True)`, which calls `_parse_function` with `optional_parens=True`. That turned a bare name into a function call. The fix is in `sqlglot/parser.py`:
- `_parse_field` takes a new `optional_parens` argument (default `True`, so other callers are unchanged).
- The dot-field branch of `_parse_colum
…[246 chars elided]…
`, `x.sysdate` and `current_timestamp` all round-trip across the default, Oracle, Snowflake and Postgres dialects.
- Added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It checks the round-trip for bare dotted names and that `()` still produces a function.
- Full suite with the project's pytest command: 1106 passed, 18000 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

I haven't committed anything. The unqualified `SELECT current_user` still becomes `CURRENT_USER()` in the default dialect, which is existing behaviour and outside this change.
