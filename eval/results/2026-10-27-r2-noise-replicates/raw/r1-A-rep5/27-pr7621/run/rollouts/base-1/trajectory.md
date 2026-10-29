# trajectory base-1

final message:
After a dot, no-parenthesis function names now parse as column identifiers and round-trip unchanged. `SELECT mytable.current_user FROM mytable` stays `SELECT mytable.current_user FROM mytable` instead of becoming `mytable.CURRENT_USER()`. The full suite passes (1106 tests, including a new regression test) and ruff is clean.

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the parts of a dotted name were parsed with the default `optional_parens=True`, so a name like `current_user` matched `NO_PAREN_FUNCTIONS` and became a function call. I added an `optional_parens` flag to `_parse_column_reference` and `_parse_field` and pass `False` from the dot-handling branches. The change is in `sqlglot/parser.py`, with no behavior change for unqualified names.

**Left as-is, by design:**
- `x.CURRENT_USER()` with parentheses is still a qualified function call.
- Bare `current_user` (no dot) is still a function.

**Test:** `test_dotted_no_paren_function_names_are_identifiers` in `tests/test_parser.py` covers the dotted cases, the parenthesized form, and the bare form.

Nothing is committed. Say if you want a commit with the Haiku co-author line.

## events
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTION\" sqlglot/parser.py | head -40 && grep -n \"def _parse_column_ops\\|def _parse_column_reference\\|def _parse_field\\|def _parse_primary\\|def _parse_function\" sqlglot/parser.py", "description": "Locate no-paren function handling in parser"}
[tool_result] 432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
769:        *NO_PAREN_FUNCTIONS,
1468:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
5350:        self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
5354:        self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
6503:            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
6846:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6852:            if optional_parens and token_type in self.NO_PAREN_F
…[311 chars elided]…
ield(
6796:    def _parse_function(
6826:    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
6829:    def _parse_function_call(
6970:    def _parse_function_properties(self) -> exp.Properties | None:
6976:    def _parse_function_parameter(self) -> exp.Expr | None:
7072:    def _parse_field_def(self) -> exp.Expr | None:
7429:    def _parse_primary_key_part(self) -> exp.Expr | None:
7444:    def _parse_primary_key(
8391:    def _parse_primary_or_var(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6561,6700p sqlglot/parser.py && echo ---- && sed -n 6779,6870p sqlglot/parser.py", "description": "Read column reference and function parsing code"}
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
…[8016 chars elided]…
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
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT t.sysdate, t.current_date() FROM t','SELECT a.b.current_user FROM t', 'SELECT x.current_user.y FROM t']:\n    for d in [None,'bigquery','snowflake','oracle']:\n        try: print(d, sqlglot.transpile(s, read=d, write=d)[0], '|', repr(sqlglot.parse_one(s, read=d).selects[0])[:150])\n        except Exception as e: print(d, 'ERR', e)\n\" ; grep -n \"COLUMN_OPERATORS\\b\" sqlglot/parser.py | head -5", "description": "Reproduce the dotted no-paren function bug"}
[tool_result] None SELECT mytable.CURRENT_USER() FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
bigquery SELECT mytable.CURRENT_USER() FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
snowflake SELECT mytable.CURRENT_USER() FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser())
oracle SELECT mytable.CURRENT_USER() FROM mytable | Dot(
  this=Identifier(this=mytable, quoted=False
…[2471 chars elided]…
uoted=False))
oracle SELECT x.CURRENT_USER().y FROM t | Dot(
  this=Dot(
    this=Identifier(this=x, quoted=False),
    expression=CurrentUser()),
  expression=Identifier(this=y, quoted=False),
  join_mark=
1008:    COLUMN_OPERATORS: t.ClassVar = {
1040:    CAST_COLUMN_OPERATORS: t.ClassVar = {
6463:            next_type in self.COLUMN_OPERATORS
6511:                if curr_tt in self.COLUMN_OPERATORS or curr_tt in self.COLUMN_POSTFIX_TOKENS:
6663:        column_operators = self.COLUMN_OPERATORS
[assistant] The cause is in `_parse_column_ops`: after a dot it calls `_parse_column_reference` → `_parse_field` → `_parse_function`, which uses the default `optional_parens=True` and so turns `current_user` into `CurrentUser()`. I'll thread an `optional_parens` flag through those helpers and pass `False` from the dot branch.
[tool_use Bash] {"command": "grep -n \"_parse_column_reference\\|_parse_field(\" sqlglot/*.py sqlglot/dialects/*.py | head -40", "description": "Find callers of column reference and field parsers"}
[tool_result] sqlglot/parser.py:2813:        field = self._parse_field()
sqlglot/parser.py:3249:                this=self._parse_schema() or self._parse_bracket(self._parse_field())
sqlglot/parser.py:4513:        on = self._parse_field() if self._match(TokenType.ON) else None
sqlglot/parser.py:5011:            bucket_field = self._parse_field()
sqlglot/parser.py:5524:            count = self._parse_field(tokens=self.FETCH_TOKENS)
sqlglot/parser.py:6475:            this = self._parse_column_reference()
sqlglot
…[1622 chars elided]…
se_field())
sqlglot/parser.py:9418:                self._parse_wrapped_options() if self._match(TokenType.EQ) else self._parse_field()
sqlglot/parser.py:9426:                exp.var(self._prev.text) if self._match(TokenType.DEFAULT) else self._parse_field(),
sqlglot/parser.py:9429:            expr.set("region", self._parse_field())
sqlglot/parser.py:9434:        return self._parse_field()
sqlglot/parser.py:9924:        separator = self._parse_field() if self._match(TokenType.SEPARATOR) else None
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "    def _parse_column_reference(self) -> exp.Expr | None:\n        this = self._parse_field()", "new_string": "    def _parse_column_reference(self, optional_parens: bool = True) -> exp.Expr | None:\n        this = self._parse_field(optional_parens=optional_parens)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_column_reference() or self._parse_bitwise()", "new_string": "                field = (\n                    self._parse_column_reference(optional_parens=False) or self._parse_bitwise()\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous=anonymous_func, any_token=any_token)\n                o
…[382 chars elided]…
       self._parse_function(\n                    anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n                )\n                or self._parse_primary()\n            )\n        else:\n            field = self._parse_primary() or self._parse_function(\n                anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT t.sysdate, t.current_date() FROM t','SELECT a.b.current_user FROM t', 'SELECT x.current_user.y FROM t','SELECT x.CURRENT_USER() FROM t']:\n    for d in [None,'bigquery','snowflake','oracle']:\n        try: print(d, sqlglot.transpile(s, read=d, write=d)[0])\n        except Exception as e: print(d, 'ERR', e)\n\"", "description": "Verify fix on reproduction cases"}
[tool_result] None SELECT mytable.CURRENT_USER() FROM mytable
bigquery SELECT mytable.CURRENT_USER() FROM mytable
snowflake SELECT mytable.CURRENT_USER() FROM mytable
oracle SELECT mytable.CURRENT_USER() FROM mytable
None SELECT mytable.CURRENT_DATE FROM mytable
bigquery SELECT mytable.CURRENT_DATE FROM mytable
snowflake SELECT mytable.CURRENT_DATE FROM mytable
oracle SELECT mytable.CURRENT_DATE FROM mytable
None SELECT t.sysdate, t.current_date() FROM t
bigquery SELECT t.sysdate, t.current_date() FROM t
snow
…[77 chars elided]…
rrent_date() FROM t
None SELECT a.b.CURRENT_USER() FROM t
bigquery SELECT a.b.CURRENT_USER() FROM t
snowflake SELECT a.b.CURRENT_USER() FROM t
oracle SELECT a.b.CURRENT_USER() FROM t
None SELECT x.CURRENT_USER().y FROM t
bigquery SELECT x.CURRENT_USER().y FROM t
snowflake SELECT x.CURRENT_USER().y FROM t
oracle SELECT x.CURRENT_USER().y FROM t
None SELECT x.CURRENT_USER() FROM t
bigquery SELECT x.CURRENT_USER() FROM t
snowflake SELECT x.CURRENT_USER() FROM t
oracle SELECT x.CURRENT_USER() FROM t
[assistant] Still wrong for `mytable.current_user`, so the dot isn't going through the branch I changed alone. Let me trace it.
[tool_use Bash] {"command": "sed -n 6455,6530p sqlglot/parser.py", "description": "Read column parsing code around dot handling"}
[tool_result]         token_type = token.token_type

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

    def _parse_colu
…[1748 chars elided]…

                self._retreat(index)
                return None

            if parts is None:
                parts = []

            if comments:
                if all_comments is None:
                    all_comments = []
                all_comments.extend(comments)
                self._prev_comments = []

            parts.append(
                self.expression(
                    exp.Identifier(
                        this=token.text, quoted=token.token_type == TokenType.IDENTIFIER
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\nfrom sqlglot import exp\norig = exp.CurrentUser.__init__\ndef init(self, *a, **k):\n    traceback.print_stack(limit=8); orig(self,*a,**k)\nexp.CurrentUser.__init__ = init\nsqlglot.parse_one('SELECT mytable.current_user FROM mytable')\n\" 2>&1 | head -40; sed -n 6835,6870p sqlglot/parser.py | head -5", "description": "Trace where CurrentUser node is created"}
[tool_result]   File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6055, in _parse_type
    if not fallback_to_identifier and (atom := self._parse_atom()) is not None:
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6450, in _parse_atom
    and (column := self._parse_column()) is not None
  File "~/.cache/lithify/wor
…[761 chars elided]…
_parse_function
    func = self._parse_function_call(
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", line 6859, in _parse_function_call
    return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
  File "<string>", line 6, in init
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
[assistant] The path is the other branch: a dot maps to `op = None`, so it takes the `else` at `_parse_field(any_token=True, anonymous_func=True)`. That branch needs the same flag.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls", "new_string": "                field = self._parse_field(\n                    any_token=True, anonymous_func=True, optional_parens=False\n                )\n\n            # Function calls"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT t.sysdate, t.current_date() FROM t','SELECT a.b.current_user FROM t', 'SELECT x.current_user.y FROM t','SELECT x.CURRENT_USER() FROM t','SELECT x.current_user, current_user FROM t']:\n    for d in [None,'bigquery','oracle']:\n        try: print(d, sqlglot.transpile(s, read=d, write=d)[0])\n        except Exception as e: print(d, 'ERR', e)\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Recheck repro cases and run full test suite"}
[tool_result] None SELECT mytable.current_user FROM mytable
bigquery SELECT mytable.current_user FROM mytable
oracle SELECT mytable.current_user FROM mytable
None SELECT mytable.current_date FROM mytable
bigquery SELECT mytable.current_date FROM mytable
oracle SELECT mytable.current_date FROM mytable
None SELECT t.sysdate, t.current_date() FROM t
bigquery SELECT t.sysdate, t.current_date() FROM t
oracle SELECT t.sysdate, t.current_date() FROM t
None SELECT a.b.current_user FROM t
bigquery SELECT a.b.current_u
…[1235 chars elided]…
...................................... [ 70%]
..................................... [ 73%]
................................................................................................................... [ 83%]
................ [ 85%]
.................................................................................................................................................................                                                  [100%]
1105 passed, 17998 subtests passed in 56.83s
[assistant] All 1105 tests pass and the repro cases round-trip. Next I'll add a regression test next to the existing parser tests.
[tool_use Bash] {"command": "grep -n \"^class \\|def test_\" tests/test_parser.py | head -30; grep -n \"def test_.*dot\\|def test_column\" tests/test_parser.py", "description": "Find suitable test location in parser tests"}
[tool_result] 11:class TestParser(unittest.TestCase):
12:    def test_parse_empty(self):
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
160:    def test_sel
…[77 chars elided]…
f):
194:    def test_transactions(self):
223:    def test_identify(self):
240:    def test_multi(self):
256:    def test_expression(self):
273:    def test_parse_errors(self):
303:    def test_space(self):
317:    def test_missing_by(self):
321:    def test_parameter(self):
324:    def test_var(self):
328:    def test_comments_select(self):
366:    def test_comments_select_cte(self):
383:    def test_comments_insert(self):
398:    def test_comments_insert_cte(self):
94:    def test_column(self):
[tool_use Bash] {"command": "sed -n 94,100p tests/test_parser.py", "description": "Read existing test_column test"}
[tool_result]     def test_column(self):
        columns = parse_one("select a, ARRAY[1] b, case when 1 then 1 end").find_all(exp.Column)
        assert len(list(columns)) == 1

        self.assertIsNotNone(parse_one("date").find(exp.Column))

    def test_tuple(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_tuple(self):", "new_string": "        self.assertIsNotNone(parse_one(\"date\").find(exp.Column))\n\n    def test_dotted_no_paren_func
…[300 chars elided]…
h self.subTest(sql=sql):\n                self.assertEqual(parse_one(sql).sql(), sql)\n\n        self.assertIsInstance(parse_one(\"SELECT x.CURRENT_USER() FROM t\").selects[0].this, exp.Dot)\n        self.assertEqual(\n            parse_one(\"SELECT x.current_user, current_user FROM t\").sql(),\n            \"SELECT x.current_user, CURRENT_USER() FROM t\",\n        )\n\n    def test_tuple(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[assistant] I'll replace the brittle node-type assertion with a plain round-trip check, then run the tests and lint.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        self.assertIsInstance(parse_one(\"SELECT x.CURRENT_USER() FROM t\").selects[0].this, exp.Dot)\n        self.assertEqual(", "new_string": "        self.assertEqual(parse_one(\"SELECT x.CURRENT_USER() FROM t\").sql(), \"SELECT x.CURRENT_USER() FROM t\")\n        self.assertEqual("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-103635-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k dotted 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/test_parser.py 2>&1 | tail -3", "description": "Run new test, full suite, and ruff checks"}
[tool_result] .                                                                    [100%]
1 passed, 64 deselected, 4 subtests passed in 0.05s
..................................................................................................................................................................                                             [100%]
1106 passed, 18002 subtests passed in 57.30s
Would reformat: sqlglot/parser.py
Would reformat: tests/test_parser.py
2 files would be reformatted
All checks passed!
[tool_use Bash] {"command": "git stash list >/dev/null; git diff --stat; <work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/parser.py tests/test_parser.py 2>&1 | head -60", "description": "Show pending ruff formatting diffs"}
[tool_result]  sqlglot/parser.py    | 19 +++++++++++++------
 tests/test_parser.py | 16 ++++++++++++++++
 2 files changed, 29 insertions(+), 6 deletions(-)
--- sqlglot/parser.py
+++ sqlglot/parser.py
@@ -6675,9 +6675,7 @@
                 if not field:
                     self.raise_error("Expected type")
             elif op and self._curr:
-                field = (
-                    self._parse_column_reference(optional_parens=False) or self._parse_bitwise()
-                )
+                field = 
…[378 chars elided]…
    self.assertEqual(parse_one(sql).sql(), sql)
 
-        self.assertEqual(parse_one("SELECT x.CURRENT_USER() FROM t").sql(), "SELECT x.CURRENT_USER() FROM t")
         self.assertEqual(
+            parse_one("SELECT x.CURRENT_USER() FROM t").sql(), "SELECT x.CURRENT_USER() FROM t"
+        )
+        self.assertEqual(
             parse_one("SELECT x.current_user, current_user FROM t").sql(),
             "SELECT x.current_user, CURRENT_USER() FROM t",
         )

2 files would be reformatted
[assistant] The formatter's diffs touch only my lines, so I'll apply it and re-run the suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/parser.py tests/test_parser.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1 && git diff --stat", "description": "Apply ruff formatting and rerun full test suite"}
[tool_result] 2 files reformatted
1106 passed, 18002 subtests passed in 53.32s
 sqlglot/parser.py    | 17 +++++++++++------
 tests/test_parser.py | 18 ++++++++++++++++++
 2 files changed, 29 insertions(+), 6 deletions(-)
[This command modified 2 files you've previously read: sqlglot/parser.py, tests/test_parser.py. Call Read before editing.]
[assistant] The harness flagged that `test_parser.py` changed on disk. That was my own `ruff format` run, but I'll check the final diff to confirm.
[tool_use Bash] {"command": "git diff && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/test_parser.py | tail -1", "description": "Review final diff and lint status"}
[tool_result] diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 42f98dec9..9be530748 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -6558,8 +6558,8 @@ class Parser:
 
         return column
 
-    def _parse_column_reference(self) -> exp.Expr | None:
-        this = self._parse_field()
+    def _parse_column_reference(self, optional_parens: bool = True) -> exp.Expr | None:
+        this = self._parse_field(optional_parens=optional_parens)
         if (
             not this
             and 
…[2460 chars elided]…
  with self.subTest(sql=sql):
+                self.assertEqual(parse_one(sql).sql(), sql)
+
+        self.assertEqual(
+            parse_one("SELECT x.CURRENT_USER() FROM t").sql(), "SELECT x.CURRENT_USER() FROM t"
+        )
+        self.assertEqual(
+            parse_one("SELECT x.current_user, current_user FROM t").sql(),
+            "SELECT x.current_user, CURRENT_USER() FROM t",
+        )
+
     def test_tuple(self):
         parse_one("(a,)").assert_is(exp.Tuple)
 
All checks passed!
[assistant] After a dot, no-parenthesis function names now parse as column identifiers and round-trip unchanged. `SELECT mytable.current_user FROM mytable` stays `SELECT mytable.current_user FROM mytable` instead of becoming `mytable.CURRENT_USER()`. The full suite passes (1106 tests, including a new regression test) and ruff is clean.

**Cause:** in `_parse_column_ops` (`sqlglot/parser.py`), the parts of a dotted name were parsed with the default `optional_parens=True`, so a name like `current_user` matched `NO_PAREN_FUNCTIONS` and became a function call. I added an `optional_parens` flag to `_parse_column_reference` and `_parse_field` and pass `False` from the dot-handling branches. The change is in `sqlglot/parser.py`, with no behavior change for unqualified names.

**Left as-is, by design:**
- `x.CURRENT_USER()` with parentheses is still a qualified function call.
- Bare `current_user` (no dot) is still a function.

**Test:** `test_dotted_no_paren_function_names_are_identifiers` in `tests/test_parser.py` covers the dotted cases, the parenthesized form, and the bare form.

Nothing is committed. Say if you want a commit with the Haiku co-author line.
