# trajectory base-1

final message:
Fixed: after a dot, no-parenthesis function names like `current_user`, `current_date` and `sysdate` now parse as column identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   ->  SELECT mytable.current_user FROM mytable
```

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the field after a dot was parsed with `_parse_field(anonymous_func=True)`. That path allows optional-parens functions, so the bare name matched `CurrentUser` and was emitted as `CURRENT_USER()`.

**Change:** the field after a dot is now parsed with `optional_parens=False`, falling back to `_parse_primary()` and then `_parse_id_var(any_token=True)`. Explicit calls like `t.current_user()` still parse as functions, and unqualified `CURRENT_USER` still becomes `CurrentUser()`.

**Tests:**
- Added `test_no_paren_function_names_as_column_parts` to `tests/test_parser.py`. It checks the three example names round-trip with no function nodes, and that `mytable.current_user()` still parses as a call.
- Full suite with the project's pytest command: 1106 passed. Ruff check and format are clean on both files.

I did not add a dialect-specific test, since the bug is in the base parser and the default dialect covers it. The change applies to every dialect that goes through this path.

## events
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTION\\|_parse_column_ops\\|def _parse_column\\b\\|def _parse_column(\" sqlglot/parser.py | head -50; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').sql())\""}
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
…[187 chars elided]…
3:            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
6659:    def _parse_column_ops(self, this: exp.Expr | None) -> exp.Expr | None:
6680:                    field = self._parse_column_ops(field)
6846:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6852:            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
SELECT mytable.CURRENT_USER() FROM mytable
[tool_use Bash] {"command": "sed -n 6472,6530p sqlglot/parser.py; echo ----; sed -n 6835,6870p sqlglot/parser.py; echo ----; sed -n 6659,6700p sqlglot/parser.py"}
[tool_result]     def _parse_column(self) -> exp.Expr | None:
        column: exp.Expr | None = self._parse_column_parts_fast()
        if column is None:
            this = self._parse_column_reference()
            if not this:
                this = self._parse_bracket(this)
            column = self._parse_column_ops(this) if this else this

        if column:
            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
            if 
…[4417 chars elided]…
          lambda n: n.to_dot(include_dots=False) if isinstance(n, exp.Column) else n
                )

            if op:
                this = op(self, this, field)
            elif isinstance(this, exp.Column) and not this.args.get("catalog"):
                this = self.expression(
                    exp.Column(
                        this=field,
                        table=this.this,
                        db=this.args.get("table"),
                        catalog=this.args.get("db"),
[tool_use Bash] {"command": "grep -n \"def _parse_field\\|def _parse_function_call\\|def _parse_primary\\|def _parse_column_reference\" -A12 sqlglot/parser.py | head -120; sed -n 6700,6720p sqlglot/parser.py"}
[tool_result] 6561:    def _parse_column_reference(self) -> exp.Expr | None:
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
6572-            # We bubble up com
…[4358 chars elided]…
pression(exp.Dot(this=this, expression=field.this))
                field.set("this", window_func)
                this = field
            else:
                this = self.expression(exp.Dot(this=this, expression=field))

            if field and field.comments:
                t.cast(exp.Expr, this).add_comments(field.pop_comments())

            this = self._parse_bracket(this)

        return this

    def _parse_paren(self) -> exp.Expr | None:
        if not self._match(TokenType.L_PAREN):
[tool_use Bash] {"command": "sed -n 6790,6800p sqlglot/parser.py; grep -n \"    def _parse_function(\" -A22 sqlglot/parser.py"}
[tool_result]         else:
            field = self._parse_primary() or self._parse_function(
                anonymous=anonymous_func, any_token=any_token
            )
        return field or self._parse_id_var(any_token=any_token, tokens=tokens)

    def _parse_function(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
6796:    def _parse_function(
6797-        self,
6798-        functions: dict[str, t.Callable] | 
…[342 chars elided]…
es
6805-        fn_syntax = False
6806-        if (
6807-            self._match(TokenType.L_BRACE, advance=False)
6808-            and self._next
6809-            and self._next.text.upper() == "FN"
6810-        ):
6811-            self._advance(2)
6812-            fn_syntax = True
6813-
6814-        func = self._parse_function_call(
6815-            functions=functions,
6816-            anonymous=anonymous,
6817-            optional_parens=optional_parens,
6818-            any_token=any_token,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "            else:\n                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls can be qualified", "new_string": "            else:\n                field = (\n                    self._parse_function(anonymous=True, optional_parens=False, any_token=True)\n                    or self._parse_primary()\n                    or self._parse_id_var(any_token=True)\n                )\n\n            # Function calls can be qualified"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user() FROM t','SELECT a.b.current_user FROM t','SELECT CURRENT_USER FROM t','SELECT t.current_date + 1 FROM t', 'SELECT t.current_user.x FROM t']:\n    e=sqlglot.parse_one(s); print(e.sql(), '|', repr(e.selects[0])[:120])\n\"; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] SELECT mytable.current_user FROM mytable | Column(
  this=Identifier(this=current_user, quoted=False),
  table=Identifier(this=mytable, quoted=False))
SELECT t.current_date, t.sysdate, t.current_user() FROM t | Column(
  this=Identifier(this=current_date, quoted=False),
  table=Identifier(this=t, quoted=False))
SELECT a.b.current_user FROM t | Column(
  this=Identifier(this=current_user, quoted=False),
  table=Identifier(this=b, quoted=False),
  db=Identifier(th
SELECT CURRENT_USER() FROM t | Cu
…[1124 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 49.49s
[assistant] All 1105 tests pass with the fix. Now a regression test, placed next to the existing column-parsing tests.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_parser.py | head -60; grep -n \"CURRENT_USER\\|current_user\" tests/test_parser.py | head"}
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
…[1292 chars elided]…
eate_schema(self):
907:    def test_values_as_identifier(self):
920:    def test_alter_set(self):
940:    def test_distinct_from(self):
943:    def test_trailing_comments(self):
955:    def test_parse_prop_eq(self):
958:    def test_collate(self):
973:    def test_drop_column(self):
978:    def test_udf_meta(self):
990:    def test_token_position_meta(self):
1032:    def test_quoted_identifier_meta(self):
1042:    def test_qualified_function(self):
1048:    def test_pivot_missing_agg_func(self):
[tool_use Bash] {"command": "sed -n 1042,1048p tests/test_parser.py"}
[tool_result]     def test_qualified_function(self):
        sql = "a.b.c.d.e.f.g.foo()"
        ast = parse_one(sql)
        assert not any(isinstance(n, exp.Column) for n in ast.walk())
        assert len(list(ast.find_all(exp.Dot))) == 7

    def test_pivot_missing_agg_func(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_pivot_missing_agg_func(self):", "new_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_no_paren_function_names_as_colu
…[261 chars elided]…
         ast = parse_one(sql)\n                assert not list(ast.find_all(exp.CurrentUser, exp.CurrentDate, exp.Sysdate))\n                self.assertEqual(ast.sql(), sql)\n\n        self.assertEqual(\n            parse_one(\"SELECT mytable.current_user() FROM mytable\").sql(),\n            \"SELECT mytable.current_user() FROM mytable\",\n        )\n\n    def test_pivot_missing_agg_func(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -5; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list >/dev/null; git diff --stat"}
[tool_result] =========================== short test summary info ============================
SUBFAILED(sql='SELECT mytable.current_user FROM mytable') tests/test_parser.py::TestParser::test_no_paren_function_names_as_column_parts
SUBFAILED(sql='SELECT mytable.current_date FROM mytable') tests/test_parser.py::TestParser::test_no_paren_function_names_as_column_parts
SUBFAILED(sql='SELECT a.b.sysdate FROM t') tests/test_parser.py::TestParser::test_no_paren_function_names_as_column_parts
3 failed, 1 passed, 64 deselected in 0.06s
SUBFAILED(sql='SELECT a.b.sysdate FROM t') tests/test_parser.py::TestParser::test_no_paren_function_names_as_column_parts
3 failed, 1106 passed, 17998 subtests passed in 51.98s
 sqlglot/parser.py    |  6 +++++-
 tests/test_parser.py | 16 ++++++++++++++++
 2 files changed, 21 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | grep -B3 \"Error\\|assert\" | head -40"}
[tool_result]         ):
            with self.subTest(sql=sql):
                ast = parse_one(sql)
>               assert not list(ast.find_all(exp.CurrentUser, exp.CurrentDate, exp.Sysdate))
                                                                               ^^^^^^^^^^^
E               AttributeError: module 'sqlglot.expressions' has no attribute 'Sysdate'

tests/test_parser.py:1056: AttributeError
--
        ):
            with self.subTest(sql=sql):
                ast = parse_one(sql)
>     
…[214 chars elided]…
le 'sqlglot.expressions' has no attribute 'Sysdate'

tests/test_parser.py:1056: AttributeError
--
        ):
            with self.subTest(sql=sql):
                ast = parse_one(sql)
>               assert not list(ast.find_all(exp.CurrentUser, exp.CurrentDate, exp.Sysdate))
                                                                               ^^^^^^^^^^^
E               AttributeError: module 'sqlglot.expressions' has no attribute 'Sysdate'

tests/test_parser.py:1056: AttributeError
[assistant] The test referenced a non-existent `exp.Sysdate` class. I'll assert that no function nodes appear at all instead, which is what the bug is about.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "                assert not list(ast.find_all(exp.CurrentUser, exp.CurrentDate, exp.Sysdate))", "new_string": "                assert not list(ast.find_all(exp.Func))"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-123501-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -2; git stash list >/dev/null; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git diff --stat"}
[tool_result] .                                                                     [100%]
1 passed, 64 deselected, 3 subtests passed in 0.04s
..................................................................................................................................................................                                              [100%]
1106 passed, 18001 subtests passed in 51.51s
 sqlglot/parser.py    |  6 +++++-
 tests/test_parser.py | 16 ++++++++++++++++
 2 files changed, 21 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/test_parser.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/test_parser.py) 2>&1 | tail -3"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Fixed: after a dot, no-parenthesis function names like `current_user`, `current_date` and `sysdate` now parse as column identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   ->  SELECT mytable.current_user FROM mytable
```

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the field after a dot was parsed with `_parse_field(anonymous_func=True)`. That path allows optional-parens functions, so the bare name matched `CurrentUser` and was emitted as `CURRENT_USER()`.

**Change:** the field after a dot is now parsed with `optional_parens=False`, falling back 
…[95 chars elided]…
user()` still parse as functions, and unqualified `CURRENT_USER` still becomes `CurrentUser()`.

**Tests:**
- Added `test_no_paren_function_names_as_column_parts` to `tests/test_parser.py`. It checks the three example names round-trip with no function nodes, and that `mytable.current_user()` still parses as a call.
- Full suite with the project's pytest command: 1106 passed. Ruff check and format are clean on both files.

I did not add a dialect-specific test, since the bug is in the base parser and the default dialect covers it. The change applies to every dialect that goes through this path.
