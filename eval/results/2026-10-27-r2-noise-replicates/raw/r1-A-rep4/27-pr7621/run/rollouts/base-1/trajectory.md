# trajectory base-1

final message:
Fixed. After a dot, `current_user`, `current_date` and the other registered no-paren names now parse as column identifiers and round-trip unchanged. The full suite passes (1106 tests, including a new regression test), and ruff check and format are clean.

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the dot operator fell into the branch that calls `_parse_field(anonymous_func=True)`. That call allowed no-paren functions, so `current_user` became `CurrentUser()`.

**Change:**
- `_parse_field` takes a new `optional_parens` flag (default `True`, so other callers are unchanged) and passes it to `_parse_function`.
- The dot path in `_parse_column_ops` passes `optional_parens=False`. A name followed by `()` still parses as a function call, so `t.CURRENT_USER()` is unchanged.

**Test:** `test_no_paren_function_names_after_dot` in `tests/test_parser.py` covers `mytable.current_user`, `mytable.current_date`, `a.b.current_user` and `a.current_user.x`.

`SYSDATE` isn't a registered no-paren function in this codebase, so `t.sysdate` already round-tripped and needed no change.

I haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short && rtk grep -n \"NO_PAREN_FUNCTION\\|_parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\b\" sqlglot/parser.py | head -50", "description": "Locate no-paren function and column parsing code"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTION\\|def _parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\b\\|def _parse_primary\\|def _parse_function\" sqlglot/parser.py | head -50", "description": "Locate no-paren function and column parsing code"}
[tool_result] 432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
769:        *NO_PAREN_FUNCTIONS,
1468:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
5350:        self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
5354:        self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
6503:            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
6561:    def _parse_column_reference(self) -> exp.Expr | None:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Exp
…[255 chars elided]…
 = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6852:            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
6970:    def _parse_function_properties(self) -> exp.Properties | None:
6976:    def _parse_function_parameter(self) -> exp.Expr | None:
7429:    def _parse_primary_key_part(self) -> exp.Expr | None:
7444:    def _parse_primary_key(
8391:    def _parse_primary_or_var(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6480,6560p sqlglot/parser.py && echo ---- && sed -n 6659,6700p sqlglot/parser.py && echo ---- && sed -n 6757,6870p sqlglot/parser.py", "description": "Read column reference and function call parsing"}
[tool_result]         if column:
            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
            if self.COLON_IS_VARIANT_EXTRACT:
                column = self._parse_colon_as_variant_extract(column)

        return column

    def _parse_column_parts_fast(self) -> exp.Column | exp.Dot | None:
        """Fast path for simple column and dot references (a, a.b, ...).

        Greedily consumes VAR/IDENTIFIER tokens separated by DOT
…[7588 chars elided]…
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
[assistant] Let me reproduce the bug before reading further.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT t.sysdate FROM t','SELECT a.b.current_user FROM t','SELECT current_user FROM t','SELECT a.current_user.x FROM t', 'SELECT t.current_user, 1 FROM t']:\n    e = sqlglot.parse_one(s)\n    print(repr(s), '->', e.sql(), '|', repr(e.selects[0])[:300])\n\"; sed -n 6561,6600p sqlglot/parser.py", "description": "Reproduce the dotted no-paren function bug"}
[tool_result] 'SELECT mytable.current_user FROM mytable' -> SELECT mytable.CURRENT_USER() FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
'SELECT mytable.current_date FROM mytable' -> SELECT mytable.CURRENT_DATE FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentDate())
'SELECT t.sysdate FROM t' -> SELECT t.sysdate FROM t | Column(
  this=Identifier(this=sysdate, quoted=False),
  table=Identifier(this=t, quoted=False))
'SELECT 
…[1597 chars elided]…
ONPath(expressions=path_parts, escape=escape),
                    variant_extract=True,
                    requires_json=self.JSON_EXTRACT_REQUIRES_JSON_EXPRESSION,
                )
            )
            path_parts = [exp.JSONPathRoot()]

        return this, path_parts

    def _parse_colon_as_variant_extract(self, this: exp.Expr | None) -> exp.Expr | None:
        path_parts: list[exp.JSONPathPart] = [exp.JSONPathRoot()]
        escape = None

        while self._match(TokenType.COLON):
[assistant] Bug reproduced: `mytable.current_user` becomes `Dot(..., CurrentUser())`. Next I'll check the dot operator path and which names are no-paren functions.
[tool_use Bash] {"command": "grep -n \"COLUMN_OPERATORS\\b\" sqlglot/parser.py | head -3; grep -n \"TokenType.DOT: None\\|TokenType.DCOLON\\|TokenType.ARROW\" sqlglot/parser.py | head; sed -n 432,470p sqlglot/parser.py; sed -n 1468,1475p sqlglot/parser.py; sed -n 6440,6470p sqlglot/parser.py", "description": "Inspect column operators and no-paren function tables"}
[tool_result] 1008:    COLUMN_OPERATORS: t.ClassVar = {
1040:    CAST_COLUMN_OPERATORS: t.ClassVar = {
6463:            next_type in self.COLUMN_OPERATORS
989:        TokenType.ARROW: lambda self, expressions: self.expression(
1009:        TokenType.DOT: None,
1011:        TokenType.DCOLON: lambda self, this, to: self.build_cast(
1014:        TokenType.ARROW: lambda self, this, path: self.expression(
1042:        TokenType.DCOLON,
6640:                elif self._match(TokenType.DCOLON):
    NO_PAREN_FUNCTIONS
…[1898 chars elided]…
  token = self._curr
        token_type = token.token_type

        if not (primary_parser := self.PRIMARY_PARSERS.get(token_type)):
            return None

        next_type = self._next.token_type

        if (
            next_type in self.COLUMN_OPERATORS
            or next_type in self.COLUMN_POSTFIX_TOKENS
            or (token_type == TokenType.STRING and next_type == TokenType.STRING)
        ):
            return None

        self._advance()
        return primary_parser(self, token)
[assistant] The cause is in `_parse_column_ops`: the DOT operator (`op is None`) falls into the `else` branch, which calls `_parse_field(anonymous_func=True)`. That path calls `_parse_function` with `optional_parens=True`, so the no-paren table turns the name into a function. Let me check the remaining details: the DOT entry, SYSDATE, and the `_parse_field` callers.
[tool_use Bash] {"command": "grep -rn -i \"sysdate\" sqlglot/dialects/*.py sqlglot/parser.py sqlglot/tokens.py | head; grep -n \"_parse_field(\" sqlglot/parser.py sqlglot/dialects/*.py | wc -l; grep -n \"_parse_field(.*anonymous_func\" sqlglot/parser.py sqlglot/dialects/*.py", "description": "Check SYSDATE handling and _parse_field callers"}
[tool_result]       26
sqlglot/parser.py:6682:                field = self._parse_field(any_token=True, anonymous_func=True)
[assistant] SYSDATE isn't registered as a no-paren function in this codebase, so `t.sysdate` already round-trips; the bug is limited to the registered names (`CURRENT_DATE`, `CURRENT_USER`, etc.). I'll thread an `optional_parens` flag through `_parse_field` and use it for the dot path only.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous=anonymous_func, any_token=any_token)\n                o
…[382 chars elided]…
       self._parse_function(\n                    anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n                )\n                or self._parse_primary()\n            )\n        else:\n            field = self._parse_primary() or self._parse_function(\n                anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)", "new_string": "                field = self._parse_field(\n                    any_token=True, anonymous_func=True, optional_parens=False\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT a.b.current_user FROM t','SELECT a.current_user.x FROM t','SELECT current_user FROM t','SELECT t.CURRENT_USER() FROM t','SELECT a.b.CURRENT_DATE() FROM t']:\n    e = sqlglot.parse_one(s)\n    print(s, '->', e.sql(), '|', type(e.selects[0]).__name__)\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] SELECT mytable.current_user FROM mytable -> SELECT mytable.current_user FROM mytable | Column
SELECT mytable.current_date FROM mytable -> SELECT mytable.current_date FROM mytable | Column
SELECT a.b.current_user FROM t -> SELECT a.b.current_user FROM t | Column
SELECT a.current_user.x FROM t -> SELECT a.current_user.x FROM t | Column
SELECT current_user FROM t -> SELECT CURRENT_USER() FROM t | CurrentUser
SELECT t.CURRENT_USER() FROM t -> SELECT t.CURRENT_USER() FROM t | Dot
SELECT a.b.CURRENT_D
…[857 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 52.77s
[assistant] The fix works and the full suite passes (1105 tests). Now I'll add a regression test next to the existing parser tests.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_parser.py | head -60; grep -rn \"CURRENT_USER\\|current_user\" tests/*.py | head", "description": "Find parser test file and existing current_user tests"}
[tool_result] 12:    def test_parse_empty(self):
16:    def test_parse_into(self):
45:    def test_parse_into_error(self):
66:    def test_parse_into_errors(self):
94:    def test_column(self):
100:    def test_tuple(self):
103:    def test_structs(self):
112:    def test_float(self):
115:    def test_unnest(self):
122:    def test_unnest_projection(self):
128:    def test_unary_plus(self):
131:    def test_table(self):
135:    def test_union(self):
160:    def test_select(self):
175:    def test_command(self
…[1466 chars elided]…
f):
955:    def test_parse_prop_eq(self):
958:    def test_collate(self):
973:    def test_drop_column(self):
978:    def test_udf_meta(self):
990:    def test_token_position_meta(self):
1032:    def test_quoted_identifier_meta(self):
1042:    def test_qualified_function(self):
1048:    def test_pivot_missing_agg_func(self):
tests/test_transpile.py:935:            "ALTER AGGREGATE bla(foo) OWNER TO CURRENT_USER",
tests/test_transpile.py:937:            "ALTER ROLE CURRENT_USER WITH REPLICATION",
[tool_use Bash] {"command": "sed -n 1042,1048p tests/test_parser.py", "description": "Read the neighbouring qualified-function test"}
[tool_result]     def test_qualified_function(self):
        sql = "a.b.c.d.e.f.g.foo()"
        ast = parse_one(sql)
        assert not any(isinstance(n, exp.Column) for n in ast.walk())
        assert len(list(ast.find_all(exp.Dot))) == 7

    def test_pivot_missing_agg_func(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_pivot_missing_agg_func(self):", "new_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_no_paren_function_names_after_d
…[113 chars elided]…
mytable.current_date FROM mytable\",\n            \"SELECT a.b.current_user FROM t\",\n            \"SELECT a.current_user.x FROM t\",\n        ):\n            with self.subTest(sql):\n                ast = parse_one(sql)\n                assert not list(ast.find_all(exp.CurrentUser, exp.CurrentDate))\n                self.assertEqual(ast.sql(), sql)\n\n    def test_pivot_missing_agg_func(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-180700-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren_function 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list | head -0; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -2; git diff --stat", "description": "Run new test, full suite, and lint checks"}
[tool_result] .                                                                    [100%]
1 passed, 64 deselected, 4 subtests passed in 0.04s
..................................................................................................................................................................                                             [100%]
1106 passed, 18002 subtests passed in 51.32s
head: illegal line count -- 0
All checks passed!
2 files already formatted
 sqlglot/parser.py    | 11 ++++++++---
 tests/test_parser.py | 12 ++++++++++++
 2 files changed, 20 insertions(+), 3 deletions(-)
[assistant] Fixed. After a dot, `current_user`, `current_date` and the other registered no-paren names now parse as column identifiers and round-trip unchanged. The full suite passes (1106 tests, including a new regression test), and ruff check and format are clean.

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the dot operator fell into the branch that calls `_parse_field(anonymous_func=True)`. That call allowed no-paren functions, so `current_user` became `CurrentUser()`.

**Change:**
- `_parse_field` takes a new `optional_parens` flag (default `True`, so other callers are unchanged) and passes it to `_parse_function`.
- The dot path in `_parse_column_ops` passes `optional_parens=False`. A name followed by `()` still parses as a function call, so `t.CURRENT_USER()` is unchanged.

**Test:** `test_no_paren_function_names_after_dot` in `tests/test_parser.py` covers `mytable.current_user`, `mytable.current_date`, `a.b.current_user` and `a.current_user.x`.

`SYSDATE` isn't a registered no-paren function in this codebase, so `t.sysdate` already round-tripped and needed no change.

I haven't committed anything.
