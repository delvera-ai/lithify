# trajectory base-1

final message:
`SELECT 1 WINDOW a AS (PARTITION BY c)` now parses in SQLite (and the other dialects), with or without a `FROM`. The full suite passes: 1107 tests, including a new regression test.

**The cause:** `WINDOW` is in the parser's select-alias token set, so `1 WINDOW` was read as "`1` aliased as `window`", and the parser then failed on `a`. With a `FROM`, table aliases already exclude `WINDOW`, which is why that form worked.

**The fix** (`sqlglot/parser.py`, in `_parse_alias`): if the current token is `WINDOW` and the token two positions ahead is `AS`, it's a window definition, so the alias parser returns without consuming it. This is deliberately narrow. My first attempt removed `WINDOW` from the select-alias tokens globally, but that broke `SELECT x window FROM t` (it silently mis-parsed into `FROM AS t`), so I reverted it.

**Test:** `tests/dialects/test_sqlite.py::test_window_clause_without_from` checks `SELECT 1 WINDOW a AS (PARTITION BY c)` and `SELECT x AS window FROM t`.

I ran `pytest` and `ruff check`/`ruff format --check` on the changed files; both pass. I did not run `make check`, and I did not commit.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\\|_parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head -60", "description": "Locate WINDOW and query modifier parsing"}
[tool_result] 759:        TokenType.WINDOW,
781:        TokenType.WINDOW,
872:        TokenType.WINDOW,
1528:        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
1655:    WINDOW_EXCLUDE_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1676:    WINDOW_BEFORE_PAREN_TOKENS: t.ClassVar = {TokenType.OVER}
1677:    WINDOW_SIDES: t.ClassVar = {"FOLLOWING", "PRECEDING"}
2290:        return self._parse_query_m
…[909 chars elided]…
PAREN_TOKENS):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8252:                self._parse_var_from_options(self.WINDOW_EXCLUDE_OPTIONS)
8286:        if self._match_set(self.WINDOW_BEFORE_PAREN_TOKENS, advance=False):
8305:            "side": self._prev.text if self._match_texts(self.WINDOW_SIDES) else None,
8488:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
8499:        return self._parse_query_modifiers(
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT 1 FROM t WINDOW a AS (PARTITION BY c)', read='sqlite')))\n\" 2>&1 | tail -3", "description": "Check WINDOW parsing with FROM in sqlite"}
[tool_result]       partition_by=[
        Column(
          this=Identifier(this=c, quoted=False))])])
[tool_use Bash] {"command": "sed -n 4107,4125p sqlglot/parser.py && grep -n \"_parse_from\\|\\\"from\\\"\" sqlglot/parser.py | head -30", "description": "Read query modifiers and FROM parsing"}
[tool_result]     def _parse_query_modifiers(self, this):
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for lateral in iter(self._parse_lateral, None):
                this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
                    parser = self.QUERY_MODIFIER_PARSERS[mo
…[237 chars elided]…
f"Found multiple '{modifier_token.text.upper()}' clauses",
                                token=modifier_token,
                            )
1052:        exp.From: lambda self: self._parse_from(joins=True),
3649:                from_ = self._parse_from(joins=True)
3742:            from_ = self._parse_from(joins=True, skip_from_token=True, consume_pipe=True)
3824:            self._parse_from(joins=True, consume_pipe=True)
3899:                from_ = self._parse_from()
4198:    def _parse_from(
[tool_use Bash] {"command": "sed -n 3815,3835p sqlglot/parser.py && sed -n 3890,3910p sqlglot/parser.py", "description": "Read select parsing around FROM handling"}
[tool_result]                 this.set("with_", cte)
            else:
                self.raise_error(f"{this.key} does not support CTE")
                this = cte

            return this

        # duckdb supports leading with FROM x
        from_ = (
            self._parse_from(joins=True, consume_pipe=True)
            if self._match(TokenType.FROM, advance=False)
            else None
        )

        if self._match(TokenType.SELECT):
            comments = self._prev_comments

            hint = s
…[247 chars elided]…
o()
            if into:
                this.set("into", into)

            if not from_:
                from_ = self._parse_from()

            if from_:
                this.set("from_", from_)

            this = self._parse_query_modifiers(this)
        elif (table or nested) and self._match(TokenType.L_PAREN):
            comments = self._prev_comments
            this = self._parse_wrapped_select(table=table)

            if this:
                this.add_comments(comments, prepend=True)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT 1 WINDOW a AS (PARTITION BY c)', 'SELECT 1 WINDOW a AS (PARTITION BY c);']:\n  for d in ['sqlite','duckdb','']:\n    try: print(d, repr(sqlglot.parse_one(s, read=d or None)).split(chr(10))[0])\n    except Exception as e: print(d, 'ERR', str(e).splitlines()[0])\n\" 2>&1; sed -n 750,790p sqlglot/parser.py; sed -n 865,875p sqlglot/parser.py", "description": "Reproduce WINDOW failure and inspect token sets"}
[tool_result] sqlite ERR Invalid expression / Unexpected token. Line 1, Col: 17.
duckdb ERR Invalid expression / Unexpected token. Line 1, Col: 17.
 ERR Invalid expression / Unexpected token. Line 1, Col: 17.
sqlite ERR Invalid expression / Unexpected token. Line 1, Col: 17.
duckdb ERR Invalid expression / Unexpected token. Line 1, Col: 17.
 ERR Invalid expression / Unexpected token. Line 1, Col: 17.
        TokenType.TOP,
        TokenType.TRUE,
        TokenType.TRUNCATE,
        TokenType.UNIQUE,
        T
…[748 chars elided]…

    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS

    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS

    ARRAY_CONSTRUCTORS: t.ClassVar = {
        "ARRAY": exp.Array,
        "LIST": exp.List,
        TokenType.TABLE,
        TokenType.TIMESTAMP,
        TokenType.TIMESTAMPTZ,
        TokenType.TRUNCATE,
        TokenType.UTC_DATE,
        TokenType.UTC_TIME,
        TokenType.UTC_TIMESTAMP,
        TokenType.WINDOW,
        TokenType.XOR,
        *TYPE_TOKENS,
        *SUBQUERY_PREDICATES,
[assistant] The `WINDOW` token is being consumed as a column alias for `1` (the error points at `a`, col 17). With a `FROM`, table aliases already exclude `WINDOW` via `TABLE_ALIAS_TOKENS`, but `ALIAS_TOKENS` (used for select-list aliases) still includes it. I'll check for existing overrides and run the suite after the change.
[tool_use Bash] {"command": "grep -rn \"ALIAS_TOKENS\" sqlglot/ | grep -v TABLE_ALIAS | head; grep -n \"ALIAS_TOKENS\" sqlglot/parser.py", "description": "Find ALIAS_TOKENS usages"}
[tool_result] sqlglot/parser.py:784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
sqlglot/parser.py:1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
sqlglot/parser.py:1743:    AMBIGUOUS_ALIAS_TOKENS: t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET)
sqlglot/parser.py:3641:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
sqlglot/parser.py:4956:                any_token=False, tokens=self.UNNEST_OFFSET_ALIAS_TOKENS
sqlglot/parser
…[1310 chars elided]…
            alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
4828:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4956:                any_token=False, tokens=self.UNNEST_OFFSET_ALIAS_TOKENS
5546:        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8331:        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
[assistant] Select-list aliases use `ALIAS_TOKENS`, which is `ID_VAR_TOKENS` and so includes `WINDOW`. I'll mirror the existing `TABLE_ALIAS_TOKENS` exclusion there and run the full suite to see what it affects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS\n\n", "new_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.WINDOW}\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['SELECT 1 WINDOW a AS (PARTITION BY c);', 'SELECT 1 AS window', 'SELECT x window FROM t']:\n  for d in ['sqlite','duckdb','']:\n    try: print(d, sqlglot.transpile(s, read=d or None)[0])\n    except Exception as e: print(d, 'ERR', str(e).splitlines()[0])\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run the full test suite"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 
…[366 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 49.92s
[assistant] The suite passes (1106 tests). The verification script failed only because `-I` drops the working directory from the import path, so I'll rerun it with `PYTHONPATH` set. I'll also add a regression test.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT 1 WINDOW a AS (PARTITION BY c);', 'SELECT 1 AS window', 'SELECT x window FROM t']:\n  for d in ['sqlite','duckdb','']:\n    try: print(d, sqlglot.transpile(s, read=d or None)[0])\n    except Exception as e: print(d, 'ERR', str(e).splitlines()[0])\n\"; grep -n \"WINDOW\" tests/dialects/test_sqlite.py | head -5; grep -n \"def test_\" tests/dialects/test_sqlite.py | tail -2", "description": "Check behavior with local package and find test spot"}
[tool_result] sqlite SELECT 1 WINDOW a AS (PARTITION BY c)
duckdb SELECT 1 WINDOW a AS (PARTITION BY c)
 SELECT 1 WINDOW a AS (PARTITION BY c)
sqlite SELECT 1 AS window
duckdb SELECT 1 AS "window"
 SELECT 1 AS window
sqlite SELECT x WINDOW FROM AS t
duckdb SELECT x WINDOW "FROM" AS t
 SELECT x WINDOW FROM AS t
361:    def test_analyze(self):
365:    def test_create_trigger(self):
[assistant] The fix works for the reported case, but it introduced a regression: `SELECT x window FROM t` (a column aliased `window`) now silently mis-parses into `FROM AS t`. Excluding `WINDOW` from all select aliases is too broad. I'll look at the alias parser to narrow it to the case where `WINDOW` begins a window clause.
[tool_use Bash] {"command": "git checkout sqlglot/parser.py && sed -n 8320,8345p sqlglot/parser.py && grep -n \"def _parse_window_clause\" -A3 sqlglot/parser.py && grep -n \"self._tokens\\[\" sqlglot/parser.py | head -5", "description": "Revert edit and read alias parser"}
[tool_result] Updated 1 path from the index

        if self._match(TokenType.L_PAREN):
            aliases = self.expression(
                exp.Aliases(
                    this=this, expressions=self._parse_csv(lambda: self._parse_id_var(any_token))
                ),
                comments=comments,
            )
            self._match_r_paren(aliases)
            return aliases

        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
            self.STRING_ALIASES and self._pars
…[482 chars elided]…
(self) -> list[exp.Expr] | None:
8155-        return self._parse_csv(self._parse_named_window) if self._match(TokenType.WINDOW) else None
8156-
8157-    def _parse_named_window(self) -> exp.Expr | None:
2163:        sql = self._find_sql(self._tokens[0], self._tokens[-1])[: self.error_message_context]
2861:            pre_volatile_token = self._tokens[self._index - 2]
4152:        end = self._tokens[self._index - 1]
8861:            mode = f"WITH {self._tokens[self._index - 2].text.upper()} MODE"
[assistant] Narrowing it: `WINDOW` should only stop being an alias when it begins a window definition, i.e. `WINDOW <name> AS`. I'll check the `AS` token type and how `_index` maps to `_curr`, then add a lookahead in `_parse_alias`.
[tool_use Bash] {"command": "grep -n \"def _advance\" -A12 sqlglot/parser.py | head -20; grep -n \"self._next = \\|self._curr = \" sqlglot/parser.py | head -4; grep -n \"def _parse_alias\" -A6 sqlglot/parser.py", "description": "Inspect token cursor helpers and _parse_alias header"}
[tool_result] 1884:    def _advance(self, times: i64 = 1) -> None:
1885-        index = self._index + times
1886-        self._index = index
1887-        tokens = self._tokens
1888-        size = self._tokens_size
1889-        self._curr = tokens[index] if index < size else SENTINEL_NONE
1890-        self._next = tokens[index + 1] if index + 1 < size else SENTINEL_NONE
1891-
1892-        if index > 0:
1893-            prev = tokens[index - 1]
1894-            self._prev = prev
1895-            self._prev_comm
…[787 chars elided]…
04-                if isinstance(alias, exp.Column) and not alias.db:
--
8308:    def _parse_alias(self, this: exp.Expr | None, explicit: bool = False) -> exp.Expr | None:
8309-        # In some dialects, LIMIT and OFFSET can act as both identifiers and keywords (clauses)
8310-        # so this section tries to parse the clause version and if it fails, it treats the token
8311-        # as an identifier (alias)
8312-        if self._can_parse_limit_or_offset():
8313-            return this
8314-
[assistant] I'll add a narrow lookahead to `_parse_alias`: `WINDOW` is not treated as an alias only when the token two positions ahead is `AS` (the `WINDOW <name> AS (...)` shape). Slicing avoids index errors at the end of a token chunk.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "            self._match_r_paren(aliases)\n            return aliases\n\n        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (", "new_string": "            self._match_r_paren(aliases)\n           
…[8 chars elided]…
aliases\n\n        # `SELECT 1 WINDOW w AS (...)` starts a WINDOW clause rather than aliasing the projection\n        if self._curr and self._curr.token_type == TokenType.WINDOW:\n            if any(t.token_type == TokenType.ALIAS for t in self._tokens[self._index + 2 : self._index + 3]):\n                return this\n\n        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or ("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT 1 WINDOW a AS (PARTITION BY c)', 'SELECT 1 WINDOW a AS (PARTITION BY c), b AS (ORDER BY d)', 'SELECT 1 AS window', 'SELECT x window FROM t', 'SELECT x AS y FROM t WINDOW a AS (PARTITION BY c)']:\n  for d in ['sqlite','duckdb']:\n    try: print(d, sqlglot.transpile(s, read=d)[0])\n    except Exception as e: print(d, 'ERR', str(e).splitlines()[0])\n\"", "description": "Verify narrowed fix across several queries"}
[tool_result] sqlite SELECT 1 WINDOW a AS (PARTITION BY c)
duckdb SELECT 1 WINDOW a AS (PARTITION BY c)
sqlite SELECT 1 WINDOW a AS (PARTITION BY c), b AS (ORDER BY d)
duckdb SELECT 1 WINDOW a AS (PARTITION BY c), b AS (ORDER BY d)
sqlite SELECT 1 AS window
duckdb SELECT 1 AS "window"
sqlite SELECT x AS window FROM t
duckdb SELECT x AS "window" FROM t
sqlite SELECT x AS y FROM t WINDOW a AS (PARTITION BY c)
duckdb SELECT x AS y FROM t WINDOW a AS (PARTITION BY c)
[assistant] The narrowed fix handles the reported case, leaves `window` usable as a column alias, and keeps the `FROM ... WINDOW` form unchanged. The tool warned that the file changed on disk since I last read it, so I'll check the diff before going further.
[tool_use Bash] {"command": "git status --short && git diff", "description": "Check working tree diff"}
[tool_result]  M sqlglot/parser.py
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index ec98ea564..6318848fc 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -8328,6 +8328,11 @@ class Parser:
             self._match_r_paren(aliases)
             return aliases
 
+        # `SELECT 1 WINDOW w AS (...)` starts a WINDOW clause rather than aliasing the projection
+        if self._curr and self._curr.token_type == TokenType.WINDOW:
+            if any(t.token_type == TokenType.ALIAS for t in self._tokens[self._index + 2 : self._index + 3]):
+                return this
+
         alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
             self.STRING_ALIASES and self._parse_string_as_identifier()
         )
[assistant] The diff contains only my change. The `any(...)` line runs past the usual 100-column limit, so I'll wrap it, add a regression test in the SQLite dialect tests, then run the suite and ruff.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "            if any(t.token_type == TokenType.ALIAS for t in self._tokens[self._index + 2 : self._index + 3]):\n                return this", "new_string": "            after_name = self._tokens[self._index + 2 : self._index + 3]\n            if any(t.token_type == TokenType.ALIAS for t in after_name):\n                return this"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "offset": 355, "limit": 15}
[tool_result] 355	        )
356	
357	        self.validate_identity(
358	            "CREATE TABLE store (store_id INTEGER PRIMARY KEY AUTOINCREMENT, mgr_id INTEGER NOT NULL UNIQUE REFERENCES staff ON UPDATE CASCADE)"
359	        )
360	
361	    def test_analyze(self):
362	        self.validate_identity("ANALYZE tbl")
363	        self.validate_identity("ANALYZE schma.tbl")
364	
365	    def test_create_trigger(self):
366	        """Test that SQLite CREATE TRIGGER statements fall back to Command parsing."""
367	        self.validate_identity(
368	            "CREATE TRIGGER log_insert AFTER INSERT ON users BEGIN INSERT INTO audit_log (user_id, action, created_at) VALUES (NEW.id, 'INSERT', datetime('now')) END",
369	            check_command_warning=True,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")", "new_string": "    def test_window_clause_without_from(self):\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY c)\")\n        self.validate_identity(\"SELECT x AS window FROM t\")\n\n    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091525-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py -k window 2>&1 | tail -2; (ruff --version && ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -4", "description": "Run full tests, new test, and ruff checks"}
[tool_result] ............................. [ 87%]
.......................................................................................................................................                                               [100%]
1107 passed, 17999 subtests passed in 49.46s
..                                                                      [100%]
2 passed, 10 deselected, 1 subtests passed in 0.04s
ruff 0.15.6
All checks passed!
2 files already formatted
[assistant] `SELECT 1 WINDOW a AS (PARTITION BY c)` now parses in SQLite (and the other dialects), with or without a `FROM`. The full suite passes: 1107 tests, including a new regression test.

**The cause:** `WINDOW` is in the parser's select-alias token set, so `1 WINDOW` was read as "`1` aliased as `window`", and the parser then failed on `a`. With a `FROM`, table aliases already exclude `WINDOW`, which is why that form worked.

**The fix** (`sqlglot/parser.py`, in `_parse_alias`): if the current token is `WINDOW` and the token two positions ahead is `AS`, it's a window definition, so the alias parser returns without consuming it. This is deliberately narrow. My first attempt removed `WINDOW` from the select-alias tokens globally, but that broke `SELECT x window FROM t` (it silently mis-parsed into `FROM AS t`), so I reverted it.

**Test:** `tests/dialects/test_sqlite.py::test_window_clause_without_from` checks `SELECT 1 WINDOW a AS (PARTITION BY c)` and `SELECT x AS window FROM t`.

I ran `pytest` and `ruff check`/`ruff format --check` on the changed files; both pass. I did not run `make check`, and I did not commit.
