# trajectory base-1

final message:
Fixed. After a dot, names like `current_user`, `current_date` and `current_timestamp` now stay identifiers, so `SELECT mytable.current_user FROM mytable` round-trips unchanged.

The cause was the dot branch in `_parse_column_ops` (`sqlglot/parser.py`). It parsed the field with `anonymous_func=True` and the default `optional_parens=True`, so a no-paren function name was built as a function before the identifier fallback ran. I added an `optional_parens` argument to `_parse_field` and pass `False` from that dot branch. Parenthesised calls such as `x.CURRENT_DATE()` still parse as calls. `DOT` is the only operator that maps to `None` in `COLUMN_OPERATORS`, so the change touches only dotted names.

I added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It covers the dotted cases, including `db.t.current_timestamp` and `x.current_user.y`, plus a check that bare `CURRENT_USER` is still a function and `x.CURRENT_DATE()` keeps its parentheses.

The full suite passes with the project's interpreter (1106 passed, including the new test). `ruff check` and `ruff format --check` are clean on both files. I did not run mypy or `make check`.

Nothing is committed. The change is two files in the worktree, and I can commit it on a branch if you want.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"NO_PAREN_FUNCTIONS\\|NO_PAREN_FUNCTION_PARSERS\\|_parse_column_ops\\|def _parse_column_reference\\|def _parse_field\" sqlglot/parser.py | head -60", "description": "Check status and locate parser no-paren logic"}
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
…[237 chars elided]…
parse_column_reference(self) -> exp.Expr | None:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6680:                    field = self._parse_column_ops(field)
6779:    def _parse_field(
6846:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6852:            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
7072:    def _parse_field_def(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6555,6700p sqlglot/parser.py && echo ---- && sed -n 6779,6870p sqlglot/parser.py", "description": "Read column reference and field parsing code"}
[tool_result]         if all_comments:
            column.add_comments(all_comments)

        return column

    def _parse_column_reference(self) -> exp.Expr | None:
        this = self._parse_field()
        if (
            not this
            and self._match(TokenType.VALUES, advance=False)
            and self.VALUES_FOLLOWED_BY_PAREN
            and (not self._next or self._next.token_type != TokenType.L_PAREN)
        ):
            this = self._parse_id_var()

        if isinstance(this, exp.Identifi
…[8111 chars elided]…
   return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())

            return None

        if any_token:
            if token_type in self.RESERVED_TOKENS:
                return None
        elif token_type not in self.FUNC_TOKENS:
            return None

        self._advance(2)

        parser = self.FUNCTION_PARSERS.get(upper)
        if parser and not anonymous:
            result = parser(self)
        else:
            subquery_predicate = self.SUBQUERY_PREDICATES.get(token_type)
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; for q in \"SELECT mytable.current_user FROM mytable\" \"SELECT mytable.sysdate FROM mytable\" \"SELECT a.current_date, b.x FROM a JOIN b ON a.current_date = b.current_date\" \"SELECT x.current_user.y FROM x\" \"SELECT current_user FROM x\" \"SELECT x.CURRENT_DATE()\" \"SELECT db.t.current_date FROM db.t\"; do PYTHONPATH=. python3 -c \"import sys,sqlglot; print(sqlglot.transpile(sys.argv[1])[0])\" \"$q\" 2>&1 | tail -1; done", "description": "Reproduce the reported round-trip issue"}
[tool_result] <work>/env-sqlglot/bin/python
SELECT mytable.CURRENT_USER() FROM mytable
SELECT mytable.sysdate FROM mytable
SELECT a.CURRENT_DATE, b.x FROM a JOIN b ON a.CURRENT_DATE = b.CURRENT_DATE
SELECT x.CURRENT_USER().y FROM x
SELECT CURRENT_USER() FROM x
SELECT x.CURRENT_DATE()
SELECT db.t.CURRENT_DATE FROM db.t
[assistant] Reproduced: `x.current_user` becomes `x.CURRENT_USER()`, while `x.CURRENT_DATE()` (with parens) must stay a call. The field after a dot goes through `_parse_column_reference` → `_parse_field` → `_parse_function`, which defaults to `optional_parens=True`. I'll thread an `optional_parens` flag through those helpers and pass `False` from the dot-operator branch only.
[tool_use Bash] {"command": "grep -n \"_parse_column_reference\\|self._parse_field(\" sqlglot/*.py sqlglot/*/*.py | head -30", "description": "Find callers of column reference and field parsers"}
[tool_result] sqlglot/parser.py:2813:        field = self._parse_field()
sqlglot/parser.py:3249:                this=self._parse_schema() or self._parse_bracket(self._parse_field())
sqlglot/parser.py:4513:        on = self._parse_field() if self._match(TokenType.ON) else None
sqlglot/parser.py:5011:            bucket_field = self._parse_field()
sqlglot/parser.py:5524:            count = self._parse_field(tokens=self.FETCH_TOKENS)
sqlglot/parser.py:6475:            this = self._parse_column_reference()
sqlglot
…[1577 chars elided]…
se_field())
sqlglot/parser.py:9418:                self._parse_wrapped_options() if self._match(TokenType.EQ) else self._parse_field()
sqlglot/parser.py:9426:                exp.var(self._prev.text) if self._match(TokenType.DEFAULT) else self._parse_field(),
sqlglot/parser.py:9429:            expr.set("region", self._parse_field())
sqlglot/parser.py:9434:        return self._parse_field()
sqlglot/parser.py:9924:        separator = self._parse_field() if self._match(TokenType.SEPARATOR) else None
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "    def _parse_column_reference(self) -> exp.Expr | None:\n        this = self._parse_field()", "new_string": "    def _parse_column_reference(self, optional_parens: bool = True) -> exp.Expr | None:\n        this = self._parse_field(optional_parens=optional_parens)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_column_reference() or self._parse_bitwise()", "new_string": "                field = (\n                    self._parse_column_reference(optional_parens=False) or self._parse_bitwise()\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous=anonymous_func, any_token=any_token)\n                o
…[382 chars elided]…
       self._parse_function(\n                    anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n                )\n                or self._parse_primary()\n            )\n        else:\n            field = self._parse_primary() or self._parse_function(\n                anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "for q in \"SELECT mytable.current_user FROM mytable\" \"SELECT mytable.sysdate FROM mytable\" \"SELECT a.current_date, b.x FROM a JOIN b ON a.current_date = b.current_date\" \"SELECT x.current_user.y FROM x\" \"SELECT current_user FROM x\" \"SELECT x.CURRENT_DATE()\" \"SELECT db.t.current_date FROM db.t\" \"SELECT t.current_date::DATE FROM t\"; do PYTHONPATH=. python3 -c \"import sys,
…[175 chars elided]…
e','SELECT x.CURRENT_DATE()']:\n    print(repr(sqlglot.parse_one(s).expressions[0]))\n\"; PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no -x 2>&1 | tail -15", "description": "Recheck repro cases and run full test suite", "timeout": 600000}
[tool_result] SELECT mytable.CURRENT_USER() FROM mytable
SELECT mytable.sysdate FROM mytable
SELECT a.CURRENT_DATE, b.x FROM a JOIN b ON a.CURRENT_DATE = b.CURRENT_DATE
SELECT x.CURRENT_USER().y FROM x
SELECT CURRENT_USER() FROM x
SELECT x.CURRENT_DATE()
SELECT db.t.CURRENT_DATE FROM db.t
SELECT CAST(t.CURRENT_DATE AS DATE) FROM t
Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
Dot(
  this=Identifier(this=x, quoted=False),
  expression=Anonymous(this=CURRENT_DATE))
............
…[790 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 55.76s
[assistant] The suite passes, but the repro output is still wrong, so my change isn't on the path that's producing this. I'll check which module is loaded and trace where the field gets built.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"import sqlglot;print(sqlglot.__file__)\"; sed -n 6460,6520p sqlglot/parser.py; grep -n \"COLUMN_OPERATORS\\b\" sqlglot/parser.py | head; grep -n \"TokenType.DOT: \" sqlglot/parser.py", "description": "Confirm loaded module and inspect dot-handling paths"}
[tool_result] ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/__init__.py
        next_type = self._next.token_type

        if (
            next_type in self.COLUMN_OPERATORS
            or next_type in self.COLUMN_POSTFIX_TOKENS
            or (token_type == TokenType.STRING and next_type == TokenType.STRING)
        ):
            return None

        self._advance()
        return primary_parser(self, token)

    def _parse_column(self)
…[1756 chars elided]…
 self._retreat(index)
                return None

            if parts is None:
                parts = []

1008:    COLUMN_OPERATORS: t.ClassVar = {
1040:    CAST_COLUMN_OPERATORS: t.ClassVar = {
6463:            next_type in self.COLUMN_OPERATORS
6511:                if curr_tt in self.COLUMN_OPERATORS or curr_tt in self.COLUMN_POSTFIX_TOKENS:
6663:        column_operators = self.COLUMN_OPERATORS
6664:        cast_column_operators = self.CAST_COLUMN_OPERATORS
1009:        TokenType.DOT: None,
[assistant] The fast path `_parse_column_parts_fast` handles `a.b` before my code runs. Let me read the rest of it.
[tool_use Bash] {"command": "sed -n 6520,6558p sqlglot/parser.py", "description": "Read remainder of fast column path"}
[tool_result]             if comments:
                if all_comments is None:
                    all_comments = []
                all_comments.extend(comments)
                self._prev_comments = []

            parts.append(
                self.expression(
                    exp.Identifier(
                        this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
                    ),
                    token,
                )
            )

            if not has_dot:
             
…[135 chars elided]…
| exp.Dot = exp.Column(this=parts[0])
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
[assistant] The fast path bails on `current_user` because its token type isn't in `IDENTIFIER_TOKENS`. The slow path then reaches `_parse_column_ops`, where my flag stops the function parse, but `_parse_id_var` also rejects that token type, so the code falls through to `_parse_bitwise` and builds the function anyway. Let me check which token types are involved.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nfrom sqlglot.dialects.dialect import Dialect\nfrom sqlglot.tokens import Tokenizer\nfrom sqlglot.parser import Parser\nfrom sqlglot import exp\nfor s in ['current_user','current_date','sysdate','current_timestamp','localtime']:\n    toks=Tokenizer().tokenize(s); print(s, toks[0].token_type)\n    print(' in ID_VAR', toks[0].token_type in Parser.ID_VAR_TOKENS, 'in NO_PAREN_FUNCTIONS', toks[0].token_type in Parser.NO_PAREN_FUNCTIONS, 'in NPFP', s.upper() in Parser.NO_PAREN_FUNCTION_PARSERS)\n\"; grep -n \"CURRENT_USER\\|CURRENT_DATE\\b\" sqlglot/parser.py | head -20", "description": "Inspect token types for no-paren keyword names"}
[tool_result] current_user TokenType.CURRENT_USER
 in ID_VAR True in NO_PAREN_FUNCTIONS True in NPFP False
current_date TokenType.CURRENT_DATE
 in ID_VAR True in NO_PAREN_FUNCTIONS True in NPFP False
sysdate TokenType.VAR
 in ID_VAR True in NO_PAREN_FUNCTIONS False in NPFP False
current_timestamp TokenType.CURRENT_TIMESTAMP
 in ID_VAR True in NO_PAREN_FUNCTIONS True in NPFP False
localtime TokenType.LOCALTIME
 in ID_VAR True in NO_PAREN_FUNCTIONS False in NPFP False
433:        TokenType.CURRENT_DATE: exp.CurrentDate,
437:        TokenType.CURRENT_USER: exp.CurrentUser,
829:        TokenType.CURRENT_DATE,
834:        TokenType.CURRENT_USER,
[assistant] Those token types are in `ID_VAR_TOKENS`, so the id-var fallback should succeed, which means my theory about the path is incomplete. I'll trace the actual call stack that constructs `CurrentUser`.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport traceback\nfrom sqlglot import exp, parse_one\norig = exp.CurrentUser.__init__\ndef patched(self, **kw):\n    traceback.print_stack(limit=12)\n    orig(self, **kw)\nexp.CurrentUser.__init__ = patched\nparse_one('SELECT mytable.current_user FROM mytable')\n\" 2>&1 | grep -v \"^    \" | head -40", "description": "Trace stack that builds CurrentUser node"}
[tool_result]   File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 5962, in _parse_bitwise
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 5995, in _parse_term
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6018, in _parse_factor
  File
…[858 chars elided]…
rk/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6790, in _parse_field
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6819, in _parse_function
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6859, in _parse_function_call
  File "<string>", line 6, in patched
[assistant] The trace shows the call comes from line 6684, the `else` branch in `_parse_column_ops`, not the `op and self._curr` branch I changed. `TokenType.DOT` maps to `None` in `COLUMN_OPERATORS`, so the dot case goes through `else`. Let me confirm which operators hit that branch before I change anything.
[tool_use Bash] {"command": "sed -n 1008,1040p sqlglot/parser.py | grep -n \"None\"; grep -rn \"COLUMN_OPERATORS\" sqlglot --include=*.py | grep -v \"parser.py:10\\|in self.COLUMN\\|in column\" | head", "description": "List column operators that map to None"}
[tool_result] 2:        TokenType.DOT: None,
(eval):1: no matches found: --include=*.py
[assistant] Only `DOT` maps to `None`, so the `else` branch is the dot path. My change to the `op and self._curr` branch and to `_parse_column_reference` is unnecessary, so I'll revert them and keep the change to `_parse_field` only, applied in the dot branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = (\n                    self._parse_column_reference(optional_parens=False) or self._parse_bitwise()\n                )", "new_string": "                field = self._parse_column_reference() or self._parse_bitwise()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "    def _parse_column_reference(self, optional_parens: bool = True) -> exp.Expr | None:\n        this = self._parse_field(optional_parens=optional_parens)", "new_string": "    def _parse_column_reference(self) -> exp.Expr | None:\n        this = self._parse_field()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls", "new_string": "                field = self._parse_field(\n                    any_token=True, anonymous_func=True, optional_parens=False\n                )\n\n            # Function calls"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "for q in \"SELECT mytable.current_user FROM mytable\" \"SELECT mytable.sysdate FROM mytable\" \"SELECT a.current_date, b.x FROM a JOIN b ON a.current_date = b.current_date\" \"SELECT x.current_user.y FROM x\" \"SELECT current_user FROM x\" \"SELECT x.CURRENT_DATE()\" \"SELECT x.current_date()\" \"SELECT db.t.current_date FROM db.t\" \"SELECT t.current_date::DATE FROM t\" \"SELECT a.b.
…[99 chars elided]…
 -c \"import sys,sqlglot; print(sqlglot.transpile(sys.argv[1])[0])\" \"$q\" 2>&1 | tail -1; done; PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Recheck repro cases and full test suite", "timeout": 600000}
[tool_result] SELECT mytable.current_user FROM mytable
SELECT mytable.sysdate FROM mytable
SELECT a.current_date, b.x FROM a JOIN b ON a.current_date = b.current_date
SELECT x.current_user.y FROM x
SELECT CURRENT_USER() FROM x
SELECT x.CURRENT_DATE()
SELECT x.current_date()
SELECT db.t.current_date FROM db.t
SELECT CAST(t.current_date AS DATE) FROM t
SELECT a.b.c.current_timestamp FROM x
SELECT db.t.current_timestamp() FROM db.t
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 48.68s
[assistant] The repro cases now round-trip, and the full suite passes (1105 tests). Next I'll add regression tests, so first I'll check where similar cases are tested.
[tool_use Bash] {"command": "grep -rn -i \"\\.current_\\(date\\|user\\|timestamp\\)\\|\\.sysdate\" tests/*.py tests/dialects/*.py | head; grep -n \"def test_column\\b\\|def test_identifier\\|class TestParser\" tests/test_parser.py | head", "description": "Find existing tests for dotted no-paren names"}
[tool_result] 11:class TestParser(unittest.TestCase):
94:    def test_column(self):
[tool_use Bash] {"command": "sed -n 94,125p tests/test_parser.py", "description": "Read existing column test in test_parser"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_tuple(self):", "new_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_no_paren_function_na
…[248 chars elided]…
.t\",\n            \"SELECT x.current_user.y FROM x\",\n        ):\n            with self.subTest(sql):\n                self.assertEqual(parse_one(sql).sql(), sql)\n\n        self.assertIsInstance(parse_one(\"SELECT CURRENT_USER FROM x\").selects[0], exp.CurrentUser)\n        self.assertEqual(parse_one(\"SELECT x.CURRENT_DATE()\").sql(), \"SELECT x.CURRENT_DATE()\")\n\n    def test_tuple(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-203618-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; (ruff --version && ruff check sqlglot/parser.py tests/test_parser.py && ruff format --check sqlglot/parser.py tests/test_parser.py) 2>&1 | tail -4; git stash list | head -0; git diff --stat", "description": "Run new test, full suite, and ruff checks", "timeout": 600000}
[tool_result] .                                                                    [100%]
1 passed, 64 deselected, 4 subtests passed in 0.04s
..................................................................................................................................................................                                             [100%]
1106 passed, 18002 subtests passed in 49.43s
ruff 0.15.6
All checks passed!
2 files already formatted
head: illegal line count -- 0
 sqlglot/parser.py    | 11 ++++++++---
 tests/test_parser.py | 13 +++++++++++++
 2 files changed, 21 insertions(+), 3 deletions(-)
[assistant] Fixed. After a dot, names like `current_user`, `current_date` and `current_timestamp` now stay identifiers, so `SELECT mytable.current_user FROM mytable` round-trips unchanged.

The cause was the dot branch in `_parse_column_ops` (`sqlglot/parser.py`). It parsed the field with `anonymous_func=True` and the default `optional_parens=True`, so a no-paren function name was built as a function before the identifier fallback ran. I added an `optional_parens` argument to `_parse_field` and pass `False` from that dot branch. Parenthesised calls such as `x.CURRENT_DATE()` still parse as calls. `DOT` is
…[72 chars elided]…
nge touches only dotted names.

I added `test_no_paren_function_names_after_dot` to `tests/test_parser.py`. It covers the dotted cases, including `db.t.current_timestamp` and `x.current_user.y`, plus a check that bare `CURRENT_USER` is still a function and `x.CURRENT_DATE()` keeps its parentheses.

The full suite passes with the project's interpreter (1106 passed, including the new test). `ruff check` and `ruff format --check` are clean on both files. I did not run mypy or `make check`.

Nothing is committed. The change is two files in the worktree, and I can commit it on a branch if you want.
