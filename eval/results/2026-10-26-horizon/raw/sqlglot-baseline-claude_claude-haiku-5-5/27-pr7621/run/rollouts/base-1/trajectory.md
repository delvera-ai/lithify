# trajectory base-1

final message:
Fixed. After a dot, `current_user`, `current_date`, `sysdate` and the other no-paren names now stay column identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   -> SELECT mytable.current_user FROM mytable
SELECT t.sysdate, t.current_date FROM t    -> SELECT t.sysdate, t.current_date FROM t
```

**Cause:** after a dot, `_parse_column_ops` parsed the name with optional parentheses allowed. A bare `CURRENT_USER` then matched the no-paren function table and became a function call.

**Change** (`sqlglot/parser.py`):
- `_parse_field` takes a new `optional_parens` flag, defaulting to `True`, and passes it to `_parse_function`. The existing caller in `clickhouse.py` is unaffected.
- The dot branch of `_parse_column_ops` passes `optional_parens=False`. Qualified calls like `x.y.FOO()` still parse as functions.

**Test** (`tests/test_parser.py`): `test_no_paren_function_names_as_column_identifiers` checks the round-trip and that no `CurrentUser`/`CurrentDate` nodes appear. It fails on the original code and passes with the fix.

**Verification:** ruff format, ruff check, and the full suite pass with the project's venv Python: 1106 tests, 18000 subtests.

**Side effect to be aware of:** the same rule now applies to all no-paren keywords after a dot, so `t.case` and `t.any` also stay identifiers. The suite passes, but I did not compare their output against the original code.

I haven't committed. Tell me if you want a commit with the attribution line.

## events
[assistant] I'll start by finding where the parser decides a name is a no-parenthesis function, and how it handles the dotted case.
[tool_use Bash] {"command": "git status --short | head && grep -n \"NO_PAREN_FUNCTION\\|_parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\|def _parse_primary\\|def _parse_function\" sqlglot/parser.py | head -60", "description": "Locate relevant parser functions"}
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
…[730 chars elided]…
      if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
6970:    def _parse_function_properties(self) -> exp.Properties | None:
6976:    def _parse_function_parameter(self) -> exp.Expr | None:
7072:    def _parse_field_def(self) -> exp.Expr | None:
7429:    def _parse_primary_key_part(self) -> exp.Expr | None:
7444:    def _parse_primary_key(
8391:    def _parse_primary_or_var(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6480,6530p sqlglot/parser.py && echo ---- && sed -n 6555,6700p sqlglot/parser.py && echo ---- && sed -n 6757,6800p sqlglot/parser.py && echo ---- && sed -n 6829,6870p sqlglot/parser.py", "description": "Read column reference and function parsing code"}
[tool_result]         if column:
            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
            if self.COLON_IS_VARIANT_EXTRACT:
                column = self._parse_colon_as_variant_extract(column)

        return column

    def _parse_column_parts_fast(self) -> exp.Column | exp.Dot | None:
        """Fast path for simple column and dot references (a, a.b, ...).

        Greedily consumes VAR/IDENTIFIER tokens separated by DOT
…[9984 chars elided]…
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
[assistant] Reading the code, `_parse_column_ops` calls `_parse_column_reference()` for the part after a dot, and that goes through `_parse_function` with optional parens allowed. So `current_user` becomes a function. I'll reproduce it first.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && $PY -I -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user FROM t','SELECT a.CURRENT_TIMESTAMP FROM a','SELECT CURRENT_USER FROM t']:\n    for d in ['', 'oracle','snowflake','postgres','bigquery']:\n        try: print(d, '|', sqlglot.transpile(s, read=d or None, write=d or None)[0])\n        except Exception as e: print(d,'ERR',e)\n\" ; grep -n \"NO_PAREN_FUNCTIONS: t.ClassVar\" -A 12 sqlglot/parser.py", "description": "Reproduce the bug across dialects"}
[tool_result] <work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
433-        TokenType.CURRENT_DATE: exp.CurrentDate,
434-        TokenType.CURRENT_DATETIME: exp.CurrentDate,
435-        TokenType.CURRENT_TIME: exp.CurrentTime,
436-        TokenType.CURRENT_TIMESTAMP: exp.CurrentTimestamp,
437-        TokenType.CURRENT_USER: exp.CurrentUser,
438-        TokenType.CURRENT_ROLE: exp.CurrentRole,
439-    }
440-
441-    STRUCT_TYPE_TOKENS: t.ClassVar = {
442-        TokenType.NESTED,
443-        TokenType.OBJECT,
444-        TokenType.STRUCT,
[assistant] The `-I` flag also drops the working directory from `sys.path`, so sqlglot can't import. This is the trusted repo, so I'll run without `-I` and point `PYTHONPATH` at the repo.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user FROM t','SELECT a.CURRENT_TIMESTAMP FROM a','SELECT CURRENT_USER FROM t']:\n    for d in ['', 'oracle','snowflake','postgres']:\n        try: print(repr(d), '|', sqlglot.transpile(s, read=d or None, write=d or None)[0])\n        except Exception as e: print(d,'ERR',e)\nprint(sqlglot.__file__)\n\"", "description": "Reproduce the bug with the repo's sqlglot"}
[tool_result] '' | SELECT mytable.CURRENT_USER() FROM mytable
'oracle' | SELECT mytable.CURRENT_USER() FROM mytable
'snowflake' | SELECT mytable.CURRENT_USER() FROM mytable
'postgres' | SELECT mytable.CURRENT_USER FROM mytable
'' | SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER() FROM t
'oracle' | SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER() FROM t
'snowflake' | SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER() FROM t
'postgres' | SELECT t.CURRENT_DATE, t.sysdate, t.CURRENT_USER FROM t
'' | SELECT a.CURRENT_TIMESTAMP() FROM a
'oracle' | SELECT a.CURRENT_TIMESTAMP FROM a
'snowflake' | SELECT a.CURRENT_TIMESTAMP() FROM a
'postgres' | SELECT a.CURRENT_TIMESTAMP FROM a
'' | SELECT CURRENT_USER() FROM t
'oracle' | SELECT CURRENT_USER() FROM t
'snowflake' | SELECT CURRENT_USER() FROM t
'postgres' | SELECT CURRENT_USER FROM t
~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/__init__.py
[assistant] Reproduced: the dotted `current_user`, `current_date`, and `current_timestamp` all turn into function calls, and the output differs by dialect. Next I'll look at how the dot operator is wired and what the fast path does.
[tool_use Bash] {"command": "grep -n \"COLUMN_OPERATORS\\b\" sqlglot/parser.py | head -5; grep -n \"COLUMN_OPERATORS: t.ClassVar\" -A 25 sqlglot/parser.py | head -40; sed -n 6700,6715p sqlglot/parser.py; grep -n \"def _parse_id_var\" -A 30 sqlglot/parser.py | head -45", "description": "Inspect COLUMN_OPERATORS and id-var parsing"}
[tool_result] 1008:    COLUMN_OPERATORS: t.ClassVar = {
1040:    CAST_COLUMN_OPERATORS: t.ClassVar = {
6463:            next_type in self.COLUMN_OPERATORS
6511:                if curr_tt in self.COLUMN_OPERATORS or curr_tt in self.COLUMN_POSTFIX_TOKENS:
6663:        column_operators = self.COLUMN_OPERATORS
1008:    COLUMN_OPERATORS: t.ClassVar = {
1009-        TokenType.DOT: None,
1010-        TokenType.DOTCOLON: lambda self, this, to: self.expression(exp.JSONCast(this=this, to=to)),
1011-        TokenType.DC
…[3366 chars elided]…
exp.Identifier | None:
8350-        if not self._match(TokenType.STRING):
8351-            return None
8352-        output = exp.to_identifier(self._prev.text, quoted=True)
8353-        output.update_positions(self._prev)
8354-        return output
8355-
8356-    def _parse_number(self) -> exp.Expr | None:
8357-        if self._match_set(self.NUMERIC_PARSERS):
8358-            return self.NUMERIC_PARSERS[self._prev.token_type](self, self._prev)
8359-        return self._parse_placeholder()
8360-
[assistant] The dot operator has `op=None`, so it falls into the `else` branch, which calls `_parse_field(any_token=True, anonymous_func=True)`. That reaches `_parse_function_call` with `optional_parens=True`, which is what accepts a bare `CURRENT_USER`. I need to see who else calls `_parse_field(anonymous_func=True)` before changing its signature.
[tool_use Bash] {"command": "grep -rn \"anonymous_func=True\\|optional_parens=False\" sqlglot/ | head -20; sed -n 6796,6828p sqlglot/parser.py; sed -n 1468,1475p sqlglot/parser.py", "description": "Find callers of anonymous_func and optional_parens"}
[tool_result] sqlglot/parser.py:4588:            (not schema and self._parse_function(optional_parens=False))
sqlglot/parser.py:6682:                field = self._parse_field(any_token=True, anonymous_func=True)
sqlglot/parsers/clickhouse.py:482:            exp.EngineProperty(this=self._parse_field(any_token=True, anonymous_func=True))
    def _parse_function(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        an
…[747 chars elided]…
    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
        return self._parse_csv(lambda: self._parse_lambda(alias=alias))

    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
        "ANY": lambda self: self.expression(exp.Any(this=self._parse_bitwise())),
        "CASE": lambda self: self._parse_case(),
        "CONNECT_BY_ROOT": lambda self: self.expression(
            exp.ConnectByRoot(this=self._parse_column())
        ),
        "IF": lambda self: self._parse_if(),
    }
[assistant] Only one caller in `parser.py` and one in `clickhouse.py` use this path, and both would keep their current behavior with a defaulted parameter. My plan: thread an `optional_parens` flag through `_parse_field`, and have the dot branch pass `False`. That still allows `x.y.FOO()` qualified calls, but a bare name after a dot becomes an identifier.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        tokens: t.Collection[TokenType] | None = None,\n        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous
…[139 chars elided]…
n[TokenType] | None = None,\n        anonymous_func: bool = False,\n        optional_parens: bool = True,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(\n                    anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n                )\n                or self._parse_primary()\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls", "new_string": "                # After a dot, a bare name is a column identifier, even if it's also a no-paren function\n                field = self._parse_field(any_token=True, anonymous_func=True, optional_parens=False)\n\n            # Function calls"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT t.current_date, t.sysdate, t.current_user FROM t','SELECT a.CURRENT_TIMESTAMP FROM a','SELECT CURRENT_USE
…[24 chars elided]…
O() FROM t', 'SELECT t.case, t.any FROM t']:\n    for d in ['', 'oracle','postgres']:\n        print(repr(d), '|', sqlglot.transpile(s, read=d or None, write=d or None)[0])\nprint(repr(sqlglot.parse_one('SELECT mytable.current_user FROM mytable').selects[0]))\n\"; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run the full test suite"}
[tool_result] '' | SELECT mytable.current_user FROM mytable
'oracle' | SELECT mytable.current_user FROM mytable
'postgres' | SELECT mytable.current_user FROM mytable
'' | SELECT t.current_date, t.sysdate, t.current_user FROM t
'oracle' | SELECT t.current_date, t.sysdate, t.current_user FROM t
'postgres' | SELECT t.current_date, t.sysdate, t.current_user FROM t
'' | SELECT a.CURRENT_TIMESTAMP FROM a
'oracle' | SELECT a.CURRENT_TIMESTAMP FROM a
'postgres' | SELECT a.CURRENT_TIMESTAMP FROM a
'' | SELECT CURRENT_
…[1218 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 51.54s
[assistant] The fix works and the full suite passes (1105 tests, 17998 subtests). Next I'll add a regression test. I'll check where existing no-paren and dot-identifier tests live.
[tool_use Bash] {"command": "grep -rni \"current_user\\|sysdate\" tests/*.py tests/dialects/*.py | head -20; grep -n \"def test_\" tests/test_parser.py | head -5; grep -n \"def test_identifier\\|def test_column\" tests/test_parser.py tests/test_transpile.py tests/test_expressions.py | head", "description": "Find existing tests for no-paren functions"}
[tool_result] tests/test_transpile.py:935:            "ALTER AGGREGATE bla(foo) OWNER TO CURRENT_USER",
tests/test_transpile.py:937:            "ALTER ROLE CURRENT_USER WITH REPLICATION",
tests/dialects/test_clickhouse.py:1860:            "CREATE VIEW v SQL SECURITY DEFINER DEFINER=CURRENT_USER AS SELECT 1",
tests/dialects/test_clickhouse.py:1867:            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER=CURRENT_USER",
tests/dialects/test_exasol.py:18:        self.validate_identity("SELECT USER", "SELECT 
…[1118 chars elided]…
dialects/test_oracle.py:748:            "TRUNC(SYSDATE, 'YEAR')",
tests/dialects/test_oracle.py:751:                "oracle": "TRUNC(SYSDATE, 'YEAR')",
12:    def test_parse_empty(self):
16:    def test_parse_into(self):
45:    def test_parse_into_error(self):
66:    def test_parse_into_errors(self):
94:    def test_column(self):
tests/test_parser.py:94:    def test_column(self):
tests/test_expressions.py:777:    def test_column(self):
tests/test_expressions.py:859:    def test_identifier(self):
[tool_use Bash] {"command": "sed -n 94,135p tests/test_parser.py", "description": "Read existing test_column in test_parser"}
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
…[650 chars elided]…

        self.assertIsInstance(expr.selects[0], exp.Alias)
        self.assertEqual(expr.selects[0].output_name, "bar")
        self.assertIsNotNone(parse_one("select unnest(x)").find(exp.Unnest))

    def test_unary_plus(self):
        self.assertEqual(parse_one("+15"), exp.Literal.number(15))

    def test_table(self):
        tables = [t.sql() for t in parse_one("select * from a, b.c, .d").find_all(exp.Table)]
        self.assertEqual(set(tables), {"a", "b.c", "d"})

    def test_union(self):
[assistant] I'll add a parser-level test next to `test_column`. It checks the AST shape, since a round-trip alone would also pass for the old output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_tuple(self):", "new_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_no_paren_function_na
…[117 chars elided]…
e, t.current_date FROM t\"):\n            with self.subTest(sql=sql):\n                self.assertEqual(parse_one(sql).sql(), sql)\n                for column in parse_one(sql).find_all(exp.Column):\n                    self.assertIsInstance(column.this, exp.Identifier)\n                self.assertFalse(list(parse_one(sql).find_all(exp.CurrentUser, exp.CurrentDate)))\n\n    def test_tuple(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[assistant] I'll run the new test, confirm it fails on the original code, then run the lint and full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -3; git stash list >/dev/null; git show HEAD:sqlglot/parser.py > /tmp/orig_parser_check.py; cp sqlglot/parser.py /tmp/new_par
…[27 chars elided]…
ig_parser_check.py sqlglot/parser.py && PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k no_paren 2>&1 | tail -2; cp /tmp/new_parser_backup.py sqlglot/parser.py && git diff --stat; $PY -m ruff --version 2>/dev/null || echo \"no ruff in venv\"; grep -n \"^style\" -A4 Makefile", "description": "Check the new test fails pre-fix and passes post-fix; find lint tool"}
[tool_result] .                                                                      [100%]
1 passed, 64 deselected, 2 subtests passed in 0.04s
SUBFAILED(sql='SELECT t.sysdate, t.current_date FROM t') tests/test_parser.py::TestParser::test_no_paren_function_names_as_column_identifiers
2 failed, 1 passed, 64 deselected in 0.07s
 sqlglot/parser.py    | 8 ++++++--
 tests/test_parser.py | 8 ++++++++
 2 files changed, 14 insertions(+), 2 deletions(-)
ruff 0.15.6
96:style:
97-	pre-commit run --all-files
98-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
99-
100-check: style test testc
[assistant] The test fails on the original code and passes with the fix; the fixed parser was restored afterward. Next, ruff format/lint on the two files and the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parser.py tests/test_parser.py && $PY -m ruff check sqlglot/parser.py tests/test_parser.py && git diff && PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Format, lint, show diff, and run full suite"}
[tool_result] 2 files reformatted
All checks passed!
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 42f98dec9..6be5a512e 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -6679,7 +6679,10 @@ class Parser:
                 if isinstance(field, exp.Column) and self._match(TokenType.DOT, advance=False):
                     field = self._parse_column_ops(field)
             else:
-                field = self._parse_field(any_token=True, anonymous_func=True)
+                # After a dot, a ba
…[1758 chars elided]…
l(exp.CurrentUser, exp.CurrentDate)))
+
     def test_tuple(self):
         parse_one("(a,)").assert_is(exp.Tuple)
 
..................................................................................................................................................................                                               [100%]
1106 passed, 18000 subtests passed in 51.10s
[This command modified 2 files you've previously read: sqlglot/parser.py, tests/test_parser.py. Call Read before editing.]
[assistant] Ruff format reflowed the code and the full suite passes (1106 tests). The "changed on disk" note is just the formatter I ran. The new comment line runs past 100 columns, so I'll shorten it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                # After a dot, a bare name is a column identifier, even if it's also a no-paren function", "new_string": "                # After a dot, a bare name is a column identifier, even if it's a no-paren function"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-150116-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py && $PY -m ruff check sqlglot/parser.py tests/test_parser.py && PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Re-check formatting, lint, and full test suite"}
[tool_result] 2 files already formatted
All checks passed!
1106 passed, 18000 subtests passed in 51.05s
[assistant] Fixed. After a dot, `current_user`, `current_date`, `sysdate` and the other no-paren names now stay column identifiers and round-trip unchanged.

```
SELECT mytable.current_user FROM mytable   -> SELECT mytable.current_user FROM mytable
SELECT t.sysdate, t.current_date FROM t    -> SELECT t.sysdate, t.current_date FROM t
```

**Cause:** after a dot, `_parse_column_ops` parsed the name with optional parentheses allowed. A bare `CURRENT_USER` then matched the no-paren function table and became a function call.

**Change** (`sqlglot/parser.py`):
- `_parse_field` takes a new `optional_parens` flag
…[294 chars elided]…
n_function_names_as_column_identifiers` checks the round-trip and that no `CurrentUser`/`CurrentDate` nodes appear. It fails on the original code and passes with the fix.

**Verification:** ruff format, ruff check, and the full suite pass with the project's venv Python: 1106 tests, 18000 subtests.

**Side effect to be aware of:** the same rule now applies to all no-paren keywords after a dot, so `t.case` and `t.any` also stay identifiers. The suite passes, but I did not compare their output against the original code.

I haven't committed. Tell me if you want a commit with the attribution line.
