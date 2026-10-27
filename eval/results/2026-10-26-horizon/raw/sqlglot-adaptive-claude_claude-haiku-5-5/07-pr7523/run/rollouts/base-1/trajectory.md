# trajectory base-1

final message:
MySQL `UPDATE` and `DELETE` now parse and round-trip optimizer hints, like `SELECT` and `INSERT` already did. The full test suite passes (1087 tests), and ruff check and format are clean on the changed files. I haven't committed.

Changes:
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call the existing `_parse_hint()` right after the keyword, the same way `_parse_insert` does, and store the result in a `hint` arg.
- **`sqlglot/expressions/dml.py`**: added `"hint": False` to `Update.arg_types` and `Delete.arg_types`.
- **`sqlglot/generator.py`**: `update_sql` and `delete_sql` emit the hint directly after the keyword, e.g. `UPDATE /*+ ... */ t SET ...`.
- **`tests/dialects/test_mysql.py`**: round-trip cases for `UPDATE`, `DELETE`, and multi-table `DELETE` with hints. I also added an `INSERT` case alongside them, which was already supported and not previously covered by a round-trip test.

The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so only the parser and generator needed changes. The parser change is in the shared base parser, so hints on these statements now parse in every dialect, the same as `SELECT` and `INSERT` do today.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"hint\" sqlglot/parser.py | head -80 && grep -n -i \"hint\" sqlglot/generator.py | head -40 && grep -n -i \"hint\" sqlglot/dialects/mysql.py | head", "description": "Check status and find hint handling code"}
[tool_result] 950:    JOIN_HINTS: t.ClassVar[set[str]] = set()
1042:        exp.Hint: lambda self: self._parse_hint_body(),
1656:    TABLE_INDEX_HINT_TOKENS: t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
3394:        hint = self._parse_hint()
3428:                hint=hint,
3798:            hint = self._parse_hint()
3835:                    hint=hint,
4098:    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
4104:        return exp.Hint(expressions=[self._find_sql(start, end)])
4
…[3044 chars elided]…
       expression.hint if self.JOIN_HINTS else None,
3063:        hint = self.sql(expression, "hint")
3109:        top_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{distinct}"
4439:    def joinhint_sql(self, expression: exp.JoinHint) -> str:
4484:        hints = table.args.get("hints")
4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3385,3440p sqlglot/parser.py && echo ---- && sed -n 3790,3800p sqlglot/parser.py && echo ---- && grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_merge\" sqlglot/parser.py && echo ---- && grep -n \"class Update\\|class Delete\" -A 22 sqlglot/expressions.py | head -70 && echo ---- && grep -n \"def update_sql\\|def delete_sql\" -A 25 sqlglot/generator.py && grep -n \"hint\" -i tests/dialects/test_mysql.py | head -20", "description": "Inspect select/insert hint parsing and update/delete generation"}
[tool_result]             expression = parse_conditional_insert()

        return self.expression(
            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
            comments=comments,
        )

    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
        comments: list[str] = []
        hint = self._parse_hint()
        overwrite = self._match(TokenType.OVERWRITE)
        ignore = self._match(TokenType.IGNORE)
        local = self._match_text_seq("LO
…[5191 chars elided]…
an `INSERT INTO ..` statement, for example
2490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
126:            "/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
127:            "/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
298:        # Index hints
[tool_use Bash] {"command": "sed -n 3582,3640p sqlglot/parser.py && echo ---- && grep -n \"^class Update(\\|^class Delete(\\|^class Insert(\" -A 20 sqlglot/expressions/*.py | grep -n \"arg_types\\|class\\|hint\" ; grep -rn \"\\\"hint\\\"\" sqlglot/expressions/ | head; echo ----; sed -n 2150,2160p sqlglot/generator.py; sed -n 290,310p tests/dialects/test_mysql.py", "description": "Read delete/update parsers and Insert/Update/Delete definitions"}
[tool_result]     def _parse_delete(self) -> exp.Delete:
        # This handles MySQL's "Multiple-Table Syntax"
        # https://dev.mysql.com/doc/refman/8.0/en/delete.html
        tables = None
        if not self._match(TokenType.FROM, advance=False):
            tables = self._parse_csv(self._parse_table) or None

        returning = self._parse_returning()

        return self.expression(
            exp.Delete(
                tables=tables,
                this=self._match(TokenType.FROM) and self._par
…[3653 chars elided]…
       )
        self.validate_identity(
            "SELECT * FROM table1 IGNORE INDEX (col3_index) WHERE col1 = 1 AND col2 = 2 AND col3 = 3"
        )
        self.validate_identity(
            "SELECT * FROM t1 USE INDEX (i1) IGNORE INDEX FOR ORDER BY (i2) ORDER BY a"
        )
        self.validate_identity("SELECT * FROM t1 USE INDEX (i1) USE INDEX (i1, i1)")
        self.validate_identity("SELECT * FROM t1 USE INDEX FOR JOIN (i1) FORCE INDEX FOR JOIN (i2)")
        self.validate_identity(
[tool_use Bash] {"command": "sed -n 71,90p sqlglot/expressions/dml.py && sed -n 293,310p sqlglot/expressions/dml.py && echo ---- && grep -rn \"/\\*+\" tests/dialects/test_mysql.py | head -20 && echo ---- && grep -n \"def update_sql\\|def delete_sql\" -B2 sqlglot/dialects/*.py | head -20; grep -n \"HINT\" sqlglot/tokens.py sqlglot/dialects/mysql.py | head", "description": "Check Delete/Update arg types and existing MySQL hint tests"}
[tool_result] class Delete(Expression, DML):
    arg_types = {
        "with_": False,
        "this": False,
        "using": False,
        "where": False,
        "returning": False,
        "order": False,
        "limit": False,
        "tables": False,  # Multiple-Table Syntax (MySQL)
        "cluster": False,  # Clickhouse
    }

    def delete(
        self,
        table: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
    ) -> De
…[926 chars elided]…
/tokens.py:106:        if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107:            cls._COMMENTS[cls.HINT_START] = "*/"
sqlglot/tokens.py:184:    HINT_START = "/*+"
sqlglot/tokens.py:186:    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE}
sqlglot/tokens.py:204:        HINT_START: TokenType.HINT,
sqlglot/tokens.py:560:            hint_start=self.HINT_START,
sqlglot/tokens.py:561:            tokens_preceding_hint=self.TOKENS_PRECEDING_HINT,
[assistant] Tokenizer already recognizes hints after `UPDATE`/`DELETE`. Let me check what currently happens.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT /*+ MAX_EXECUTION_TIME(1000) */ 1 FROM t','INSERT /*+ NO_ENGINE_SUBSTITUTION */ INTO t VALUES (1)','UPDATE /*+ NO_ENGINE_SUBSTITUTION */ t SET a = 1','DELETE /*+ QB_NAME(del) */ FROM t WHERE a = 1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n    except Exception as x: print('ERR', x)\n\"", "description": "Check current hint parsing on DML statements in MySQL"}
[tool_result] Select(
  hint=Hint(
    expressions=[
      Anonymous(
        this=MAX_EXECUTION_TIME,
        expressions=[
          Literal(this=1000, is_string=False)])]),
  expressions=[
    Literal(this=1, is_string=False)],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))))
SELECT /*+ MAX_EXECUTION_TIME(1000) */ 1 FROM t
Insert(
  hint=Hint(
    expressions=[
      Var(this=NO_ENGINE_SUBSTITUTION)]),
  is_function=False,
  this=Table(
    this=Identifier(this=t, quoted=False))
…[190 chars elided]…
UES (1)
ERR Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_ENGINE_SUBSTITUTION */, line: 1, col: 36, start: 7, end: 35, comments: [' NO_ENGINE_SUBSTITUTION ']>. Line 1, Col: 36.
  UPDATE [4m/*+ NO_ENGINE_SUBSTITUTION */[0m t SET a = 1
ERR Expected table name but got <Token token_type: TokenType.HINT, text: /*+ QB_NAME(del) */, line: 1, col: 26, start: 7, end: 25, comments: [' QB_NAME(del) ']>. Line 1, Col: 26.
  DELETE [4m/*+ QB_NAME(del) */[0m FROM t WHERE a = 1
[assistant] Current behavior: hints on `UPDATE`/`DELETE` are tokenized but the parser rejects them. Let me confirm how the statement dispatcher consumes the keyword before making edits.
[tool_use Bash] {"command": "grep -n \"TokenType.UPDATE:\\|TokenType.DELETE:\\|TokenType.INSERT:\" sqlglot/parser.py && grep -n \"def _parse_statement\" -A 14 sqlglot/parser.py | head -30 && grep -n \"UPDATE\\|DELETE\" sqlglot/dialects/mysql.py | head", "description": "Confirm statement parser dispatch for DML keywords"}
[tool_result] 1075:        TokenType.DELETE: lambda self: self._parse_delete(),
1081:        TokenType.INSERT: lambda self: self._parse_insert(),
1093:        TokenType.UPDATE: lambda self: self._parse_update(),
3481:        if self._prev.token_type == TokenType.UPDATE:
2253:    def _parse_statement(self) -> exp.Expr | None:
2254-        if not self._curr:
2255-            return None
2256-
2257-        if self._match_set(self.STATEMENT_PARSERS):
2258-            comments = self._prev_comments
2259-            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
2260-            stmt.add_comments(comments, prepend=True)
2261-            return stmt
2262-
2263-        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
2264-            return self._parse_command()
2265-
2266-        if self._match_text_seq("WHILE"):
2267-            return self._parse_whileblock()
[assistant] The keyword is consumed before the parser method runs, so the same `_parse_hint()` call used by `INSERT` works here. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.ex
…[34 chars elided]…
\n                tables=tables,", "new_string": "        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests, next to the existing MySQL hint tests.
[tool_use Bash] {"command": "sed -n 244,256p tests/dialects/test_mysql.py", "description": "View existing MySQL hint test block"}
[tool_result]         self.validate_identity("SELECT @var1 := 1, @var2")
        self.validate_identity("UNLOCK TABLES")
        self.validate_identity("LOCK TABLES `app_fields` WRITE", check_command_warning=True)
        self.validate_identity("SELECT 1 XOR 0")
        self.validate_identity("SELECT 1 && 0", "SELECT 1 AND 0")
        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
    
…[10 chars elided]…
alidate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("""SELECT 'ab' MEMBER OF('[23, "abc", 17, "ab", 10]')""")
        self.validate_identity("""SELECT * FROM foo WHERE 'ab' MEMBER OF(content)""")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"INSERT /*+ NO_ENGINE_SUBSTITUTION */ INTO t VALUES (1)\")\n        self.validate_identity(\"UPDATE /*+ NO_ENGINE_SUBSTITUTION */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(del) */ FROM t WHERE a = 1\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(del) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160240-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run MySQL dialect tests then full test suite"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.57s
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
.................................................................................................................................................................................
…[328 chars elided]…
.................................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 76.60s (0:01:16)
[assistant] All tests pass. Now the linters the project uses.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py && $PY/ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 4 ++++
 4 files changed, 13 insertions(+), 2 deletions(-)
[assistant] MySQL `UPDATE` and `DELETE` now parse and round-trip optimizer hints, like `SELECT` and `INSERT` already did. The full test suite passes (1087 tests), and ruff check and format are clean on the changed files. I haven't committed.

Changes:
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call the existing `_parse_hint()` right after the keyword, the same way `_parse_insert` does, and store the result in a `hint` arg.
- **`sqlglot/expressions/dml.py`**: added `"hint": False` to `Update.arg_types` and `Delete.arg_types`.
- **`sqlglot/generator.py`**: `update_sql` and `delete_sql` emit the hint directly after the keyword, e.g. `UPDATE /*+ ... */ t SET ...`.
- **`tests/dialects/test_mysql.py`**: round-trip cases for `UPDATE`, `DELETE`, and multi-table `DELETE` with hints. I also added an `INSERT` case alongside them, which was already supported and not previously covered by a round-trip test.

The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so only the parser and generator needed changes. The parser change is in the shared base parser, so hints on these statements now parse in every dialect, the same as `SELECT` and `INSERT` do today.
