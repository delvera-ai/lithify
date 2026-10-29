# trajectory base-1

final message:
`SELECT 1 WINDOW a AS (...)` now parses without a `FROM` clause. The full suite passes (1107 tests), and ruff's format and lint checks are clean.

The cause was that `WINDOW` is an ID-like token, so the parser read it as an implicit alias for the projection `1` and then failed on `a`. The fix is in `_parse_alias` in `sqlglot/parser.py`: `WINDOW` is not treated as an alias only when it is followed by `<name> AS`, which is the shape of a window clause. Excluding `WINDOW` from alias tokens outright was my first attempt, but it broke `SELECT x window FROM t`, so I narrowed it.

I added `test_window_clause_without_from` to `tests/dialects/test_sqlite.py`. It covers the no-`FROM` case, the `FROM` case, and `SELECT x AS window FROM t`. Changes are uncommitted.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\" sqlglot/parser.py | head -50", "description": "Find WINDOW references in parser"}
[tool_result] 759:        TokenType.WINDOW,
781:        TokenType.WINDOW,
872:        TokenType.WINDOW,
1528:        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
1655:    WINDOW_EXCLUDE_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1676:    WINDOW_BEFORE_PAREN_TOKENS: t.ClassVar = {TokenType.OVER}
1677:    WINDOW_SIDES: t.ClassVar = {"FOLLOWING", "PRECEDING"}
8155:        return self._parse_csv(self._parse_named_window) if self._match(TokenType.WINDOW) else None
8222:        elif not self._match_set(self.WINDOW_BEFORE_PAREN_TOKENS):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8252:                self._parse_var_from_options(self.WINDOW_EXCLUDE_OPTIONS)
8286:        if self._match_set(self.WINDOW_BEFORE_PAREN_TOKENS, advance=False):
8305:            "side": self._prev.text if self._match_texts(self.WINDOW_SIDES) else None,
[tool_use Bash] {"command": "sed -n 8140,8160p sqlglot/parser.py && grep -n \"_parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head; grep -n \"WINDOW\\|windows\" sqlglot/parser.py | sed -n 1,5p; grep -n \"def _parse_query_modifiers\" -A 40 sqlglot/parser.py | head -80", "description": "Inspect window clause parsing and query modifiers"}
[tool_result]         if self._match_set((TokenType.FROM, TokenType.COMMA)):
            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
            expression = self._parse_bitwise()

            if invert_order:
                this, expression = expression, this

        if self._match(TokenType.COLLATE):
            collation = self._parse_bitwise()

        return self.expression(
            exp.Trim(this=this, position=position, expression=expression, collation=collati
…[2860 chars elided]…
sion.expressions
4137-                                expression.set("expressions", None)
4138-                                offset.set("expressions", limit_by_expressions)
4139-                        continue
4140-                break
4141-
4142-        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
4143-            this = self._implicit_unnests_to_explicit(this)
4144-
4145-        return this
4146-
4147-    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite')))\n    except Exception as e: print('ERR', e)\n\"; sed -n 3794,3830p sqlglot/parser.py; grep -n \"MODIFIABLES\\|QUERY_MODIFIER_PARSERS\" sqlglot/parser.py | head", "description": "Reproduce the WINDOW parse error and inspect select parsing"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 17.
  SELECT 1 WINDOW [4ma[0m AS (PARTITION BY fake_column)
Select(
  expressions=[
    Literal(this=1, is_string=False)],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  windows=[
    Window(
      this=Identifier(this=a, quoted=False),
      partition_by=[
        Column(
          this=Identifier(this=fake_column, quoted=False))])])
    def _parse_select_query(
        self,
        nested: bool = False,

…[963 chars elided]…
ch(TokenType.SELECT):
            comments = self._prev_comments
1521:    QUERY_MODIFIER_PARSERS: t.ClassVar = {
1549:    QUERY_MODIFIER_TOKENS: t.ClassVar = set(QUERY_MODIFIER_PARSERS)
1751:    MODIFIABLES: t.ClassVar = (exp.Query, exp.Table, exp.TableFromRows, exp.Values)
4108:        if isinstance(this, self.MODIFIABLES):
4115:                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4117:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
[tool_use Bash] {"command": "sed -n 745,790p sqlglot/parser.py; sed -n 860,880p sqlglot/parser.py; grep -n \"TABLE_ALIAS_TOKENS\\|ALIAS_TOKENS\" sqlglot/parser.py | head -20", "description": "Inspect token sets containing WINDOW"}
[tool_result]         TokenType.SETTINGS,
        TokenType.SHOW,
        TokenType.STREAM,
        TokenType.STREAMLIT,
        TokenType.TEMPORARY,
        TokenType.TOP,
        TokenType.TRUE,
        TokenType.TRUNCATE,
        TokenType.UNIQUE,
        TokenType.UNNEST,
        TokenType.UNPIVOT,
        TokenType.UPDATE,
        TokenType.USE,
        TokenType.VOLATILE,
        TokenType.WINDOW,
        TokenType.CURRENT_CATALOG,
        TokenType.LOCALTIME,
        TokenType.LOCALTIMESTAMP,
        T
…[2077 chars elided]…
            alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
4828:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4956:                any_token=False, tokens=self.UNNEST_OFFSET_ALIAS_TOKENS
5546:        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8331:        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
[tool_use Bash] {"command": "sed -n 8320,8345p sqlglot/parser.py; grep -rn \"ALIAS_TOKENS\" sqlglot/dialects | head", "description": "Inspect _parse_alias and dialect alias token overrides"}
[tool_result]         if self._match(TokenType.L_PAREN):
            aliases = self.expression(
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
            this = self.expression(exp.Alias(this=this, alias=alias), comments=comments)
            column = this.this

            # Moves the comment next to the alias in `expr /* comment */ AS alias`
            if not this.comments and column and column.comments:
                this.comments = column.pop_comments()

        return this
[assistant] The cause: `WINDOW` is in `ID_VAR_TOKENS`, and `ALIAS_TOKENS` defaults to that set, so the parser reads `WINDOW` as an implicit alias for `1` and then chokes on `a`. `TABLE_ALIAS_TOKENS` already excludes `WINDOW` for this reason, so I'll mirror that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS\n", "new_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.WINDOW}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)','SELECT 1 AS window','SELECT x window FROM t']:\n    try: print(sqlglot.parse_one(q, read='sqlite').sql('sqlite'))\n    except Exception as e: print('ERR', e)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run the full test suite"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)
SELECT 1 AS window
SELECT x WINDOW FROM AS t
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
..................
…[393 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 55.68s
[assistant] The fix works for the reported case, and the full suite passes (1106 passed). But `SELECT x window FROM t` now renders as `SELECT x WINDOW FROM AS t`. Before this change, `window` was accepted as an implicit column alias, so I've regressed that. I'll narrow the exclusion so `WINDOW` only stops being an alias when it starts a window clause (`WINDOW <name> AS`).
[tool_use Bash] {"command": "grep -n \"self._next\\b\\|self._tokens\\[self._index\" sqlglot/parser.py | head; git diff --stat; sed -n 8300,8320p sqlglot/parser.py", "description": "Look for lookahead helpers and alias parsing context"}
[tool_result] 1861:        self._next: Token = SENTINEL_NONE
1876:        self._next = SENTINEL_NONE
1890:        self._next = tokens[index + 1] if index + 1 < size else SENTINEL_NONE
1936:        if self._curr.token_type == token_type_a and self._next.token_type == token_type_b:
2118:            if expressions and not self._next and self._match(TokenType.END):
2861:            pre_volatile_token = self._tokens[self._index - 2]
2979:        if not self._next:
3834:            if self._next and not self._next.
…[571 chars elided]…
None, explicit: bool = False) -> exp.Expr | None:
        # In some dialects, LIMIT and OFFSET can act as both identifiers and keywords (clauses)
        # so this section tries to parse the clause version and if it fails, it treats the token
        # as an identifier (alias)
        if self._can_parse_limit_or_offset():
            return this

        any_token = self._match(TokenType.ALIAS)
        comments = self._prev_comments

        if explicit and not any_token:
            return this
[assistant] I'll keep `WINDOW` as an alias token in general, and only exclude it when the upcoming tokens are `WINDOW <name> AS`. That's the one position where it must be a clause keyword.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.WINDOW}\n", "new_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (\n            self.STRING_ALIASES and self._parse_string_as_identifier()\n        )", "new_string": "        # WINDOW <name> AS starts a WINDOW
…[73 chars elided]…
w_clause = self._match(TokenType.WINDOW, advance=False) and self._tokens[\n            self._index + 2 : self._index + 3\n        ] == [self._tokens[self._index + 2]] * (self._index + 3 <= len(self._tokens))\n        alias = None if is_window_clause else self._parse_id_var(\n            any_token, tokens=self.ALIAS_TOKENS\n        ) or (self.STRING_ALIASES and self._parse_string_as_identifier())"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[assistant] That expression came out convoluted and hard to read. I'll rewrite it as a plain lookahead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        # WINDOW <name> AS starts a WINDOW clause (e.g. SELECT 1 WINDOW w AS (...)), not an alias\n        is_window_clause = self._match(TokenType.WINDOW, advance=False) and self._tokens[\n            self._index + 2 :
…[457 chars elided]…
se = (\n            self._match(TokenType.WINDOW, advance=False)\n            and self._index + 2 < len(self._tokens)\n            and self._tokens[self._index + 2].token_type == TokenType.ALIAS\n        )\n\n        alias = None if is_window_clause else self._parse_id_var(\n            any_token, tokens=self.ALIAS_TOKENS\n        ) or (self.STRING_ALIASES and self._parse_string_as_identifier())"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:         # WINDOW <name> AS starts a WINDOW clause (e.g. SELECT 1 WINDOW w AS (...)), not an alias
        is_window_clause = self._match(TokenType.WINDOW, advance=False) and self._tokens[
            self._index + 2 : self._index + 3
        ] == [self._tokens[self._index + 2]] * (self._index + 3 <= len(self._tokens))
        alias = None if is_window_clause else self._parse_id_var(
            any_token, tokens=self.ALIAS_TOKENS
        ) or (
            self.STRING_ALIASES and self._parse_string_as_identifier()
        )</tool_use_error>
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)','SELECT 1 AS window','SELECT x window FROM t','SELECT 1 window']:\n    try: print(sqlglot.parse_one(q, read='sqlite').sql('sqlite'))\n
…[81 chars elided]…
/r2-noise-scratch/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/ruff check sqlglot/parser.py 2>&1 | tail -2; <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py 2>&1|tail -2", "description": "Verify fix, run full tests, and lint/format check"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)
ERR list index out of range
SELECT x WINDOW FROM AS t
ERR list index out of range
=========================== short test summary info ============================
FAILED tests/dialects/test_clickhouse.py::TestClickhouse::test_clickhouse - A...
1 failed, 1105 passed, 17884 subtests passed in 52.52s
All checks passed!
Would reformat: sqlglot/parser.py
1 file would be reformatted
[assistant] The edit didn't match, so the file is in a broken intermediate state (the list-index error). I'll look at the current text and fix it directly.
[tool_use Bash] {"command": "grep -n \"is_window_clause\" -B2 -A8 sqlglot/parser.py", "description": "Show current window-alias block in parser"}
[tool_result] 8330-
8331-        # WINDOW <name> AS starts a WINDOW clause (e.g. SELECT 1 WINDOW w AS (...)), not an alias
8332:        is_window_clause = self._match(TokenType.WINDOW, advance=False) and self._tokens[
8333-            self._index + 2 : self._index + 3
8334-        ] == [self._tokens[self._index + 2]] * (self._index + 3 <= len(self._tokens))
8335:        alias = None if is_window_clause else self._parse_id_var(
8336-            any_token, tokens=self.ALIAS_TOKENS
8337-        ) or (self.STRING_ALIASES and self._parse_string_as_identifier())
8338-
8339-        if alias:
8340-            comments.extend(alias.pop_comments())
8341-            this = self.expression(exp.Alias(this=this, alias=alias), comments=comments)
8342-            column = this.this
8343-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        is_window_clause = self._match(TokenType.WINDOW, advance=False) and self._tokens[\n            self._index + 2 : self._index + 3\n        ] == [self._tokens[self._index + 2]] * (self._index + 3 <= len(self._toke
…[235 chars elided]…
se = (\n            self._match(TokenType.WINDOW, advance=False)\n            and self._index + 2 < len(self._tokens)\n            and self._tokens[self._index + 2].token_type == TokenType.ALIAS\n        )\n\n        alias = None if is_window_clause else self._parse_id_var(\n            any_token, tokens=self.ALIAS_TOKENS\n        ) or (self.STRING_ALIASES and self._parse_string_as_identifier())"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)','SELECT 1 AS window','SELECT x window FROM t','SELECT 1 window']:\n    try: print(sqlglot.parse_one(q, read='sqlite').sql('sqlite'))\n
…[76 chars elided]…
y-dev/r2-noise-scratch/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py 2>&1|tail -2; <work>/env-sqlglot/bin/ruff check sqlglot/parser.py | tail -1", "description": "Verify fix, run full tests, and lint/format check"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)
SELECT 1 AS window
SELECT x AS window FROM t
SELECT 1 AS window
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 52.58s
Would reformat: sqlglot/parser.py
1 file would be reformatted
All checks passed!
[assistant] All 1106 tests pass, and `SELECT x window FROM t` keeps its implicit alias. The one remaining item is formatting, so I'll apply ruff's formatter and check the diff.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format sqlglot/parser.py && git diff", "description": "Apply ruff format and show the diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index ec98ea564..c2d87bcd4 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -8328,8 +8328,18 @@ class Parser:
             self._match_r_paren(aliases)
             return aliases
 
-        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
-            self.STRING_ALIASES and self._parse_string_as_identifier()
+        # WINDOW <name> AS starts a WINDOW clause (e.g. SELECT 1 WINDOW w AS (...)), not
…[93 chars elided]…
lse)
+            and self._index + 2 < len(self._tokens)
+            and self._tokens[self._index + 2].token_type == TokenType.ALIAS
+        )
+
+        alias = (
+            None
+            if is_window_clause
+            else self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS)
+            or (self.STRING_ALIASES and self._parse_string_as_identifier())
         )
 
         if alias:
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] The formatter touched only my hunk. Next I'll add a regression test to the SQLite dialect tests and check whether the existing suite already covers `WINDOW` clauses.
[tool_use Bash] {"command": "grep -n \"WINDOW\" tests/dialects/test_sqlite.py | head; grep -n \"def test_\" tests/dialects/test_sqlite.py | tail -3; tail -5 tests/dialects/test_sqlite.py", "description": "Find existing WINDOW tests in SQLite test file"}
[tool_result] 280:    def test_ddl(self):
361:    def test_analyze(self):
365:    def test_create_trigger(self):

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view BEGIN INSERT INTO employees (id, name, department) VALUES (NEW.id, NEW.name, NEW.department) END",
            check_command_warning=True,
        )
[tool_use Bash] {"command": "sed -n 355,366p tests/dialects/test_sqlite.py", "description": "View end of test method section in SQLite tests"}
[tool_result]         )

        self.validate_identity(
            "CREATE TABLE store (store_id INTEGER PRIMARY KEY AUTOINCREMENT, mgr_id INTEGER NOT NULL UNIQUE REFERENCES staff ON UPDATE CASCADE)"
        )

    def test_analyze(self):
        self.validate_identity("ANALYZE tbl")
        self.validate_identity("ANALYZE schma.tbl")

    def test_create_trigger(self):
        """Test that SQLite CREATE TRIGGER statements fall back to Command parsing."""
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")\n        self.validate_identity(\"ANALYZE schma.tbl\")\n", "new_string": "    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")\n        self.validate_identity(\"ANALYZE schma.tbl\")\n\n    def test_window_clause_without_from(self):\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\")\n        self.validate_identity(\"SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)\")\n        self.validate_identity(\"SELECT x AS window FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-124635-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; <work>/env-sqlglot/bin/ruff format --check sqlglot tests | tail -1; <work>/env-sqlglot/bin/ruff check sqlglot tests | tail -1; git status --short", "description": "Run full tests, format and lint checks, git status"}
[tool_result] .......................................................................................................................................                                               [100%]
1107 passed, 17999 subtests passed in 51.83s
235 files already formatted
All checks passed!
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[assistant] `SELECT 1 WINDOW a AS (...)` now parses without a `FROM` clause. The full suite passes (1107 tests), and ruff's format and lint checks are clean.

The cause was that `WINDOW` is an ID-like token, so the parser read it as an implicit alias for the projection `1` and then failed on `a`. The fix is in `_parse_alias` in `sqlglot/parser.py`: `WINDOW` is not treated as an alias only when it is followed by `<name> AS`, which is the shape of a window clause. Excluding `WINDOW` from alias tokens outright was my first attempt, but it broke `SELECT x window FROM t`, so I narrowed it.

I added `test_window_clause_without_from` to `tests/dialects/test_sqlite.py`. It covers the no-`FROM` case, the `FROM` case, and `SELECT x AS window FROM t`. Changes are uncommitted.
