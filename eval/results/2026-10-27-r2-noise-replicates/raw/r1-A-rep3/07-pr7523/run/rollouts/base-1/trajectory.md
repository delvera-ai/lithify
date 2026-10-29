# trajectory base-1

final message:
MySQL `UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests), and ruff check and format are clean. I haven't committed.

**Changes:**
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching `Insert`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` right after the keyword, as `_parse_insert` already does.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t1 ...` and `delete_sql` emits `DELETE /*+ ... */ FROM t1 ...`.
- **`tests/dialects/test_mysql.py`**: two identity tests, one for `UPDATE` and one for `DELETE`, placed next to the existing SELECT hint tests.

**Choices I made:**
- I put the hint parsing in the base parser rather than the MySQL dialect, following how `Insert` already works. Other dialects that use `/*+ */` on UPDATE or DELETE will now keep the hint instead of dropping it. If you want this limited to MySQL, that's a small move.
- The `DELETE` multi-table form also keeps its hint, e.g. `DELETE /*+ X */ t1 FROM t1 JOIN t2 ...`.

## events
[tool_use Bash] {"command": "grep -n -i \"hint\" sqlglot/parser.py | head -80; echo ---; grep -n -i \"hint\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -40", "description": "Find hint handling in parser and generator"}
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
…[3594 chars elided]…
glot/generator.py:3109:        top_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{distinct}"
sqlglot/generator.py:4439:    def joinhint_sql(self, expression: exp.JoinHint) -> str:
sqlglot/generator.py:4484:        hints = table.args.get("hints")
sqlglot/generator.py:4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3385,3440p sqlglot/parser.py; echo ----; sed -n 3790,3800p sqlglot/parser.py; echo ----; grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_insert\" sqlglot/parser.py; echo ----; grep -n \"class Update\\|class Delete\\|class Insert\" -A 22 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | grep -n \"hint\\|class \" ; echo ----; sed -n 2150,2160p sqlglot/generator.py; grep -n \"def update_sql\\|def delete_sql\" -A 25 sqlglot/generator.py | head -70", "description": "Inspect hint parsing and update/delete generation"}
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
…[5633 chars elided]…
: exp.Values, values_as_table: bool = True) -> str:
2487-        values_as_table = values_as_table and self.VALUES_AS_TABLE
2488-
2489-        # The VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
[tool_use Bash] {"command": "sed -n 3582,3640p sqlglot/parser.py; echo ----; sed -n 60,95p sqlglot/expressions/dml.py; echo ----; sed -n 290,310p sqlglot/expressions/dml.py; echo ----; grep -rn \"hint\" sqlglot/dialects/mysql.py | head; echo ----; grep -rn \"/\\*+\" tests/dialects/test_mysql.py | head -20; grep -n \"hint\" tests/dialects/test_mysql.py | head -30", "description": "Read delete/update parsers, expression defs, MySQL tests"}
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
…[3423 chars elided]…
idate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
tests/dialects/test_mysql.py:250:        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
tests/dialects/test_mysql.py:251:        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
126:            "/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
127:            "/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
298:        # Index hints
[tool_use Bash] {"command": "grep -rn \"INSERT /\\*+\\|DELETE /\\*+\\|UPDATE /\\*+\" tests/ | head; echo ----; grep -n \"hint\" sqlglot/expressions/dml.py | head; sed -n 190,200p sqlglot/expressions/dml.py; echo ---; grep -n \"_parse_hint()\" -B3 -A3 sqlglot/parser.py | sed -n 1,30p; echo; ls <work>/env-sqlglot/bin/python && git status --short | head", "description": "Check existing hint tests and env"}
[tool_result] tests/test_lineage.py:519:        INSERT /*+ HINT1 */
tests/dialects/test_oracle.py:410:        self.validate_identity("INSERT /*+ APPEND */ INTO IAP_TBL (id, col1) VALUES (2, 'test2')")
tests/dialects/test_oracle.py:411:        self.validate_identity("INSERT /*+ APPEND_VALUES */ INTO dest_table VALUES (i, 'Value')")
tests/dialects/test_oracle.py:412:        self.validate_identity("INSERT /*+ APPEND(d) */ INTO dest d VALUES (i, 'Value')")
tests/dialects/test_oracle.py:414:            "INSERT /*+
…[507 chars elided]…
 = self._match(TokenType.OVERWRITE)
3396-        ignore = self._match(TokenType.IGNORE)
3397-        local = self._match_text_seq("LOCAL")
--
3795-        if self._match(TokenType.SELECT):
3796-            comments = self._prev_comments
3797-
3798:            hint = self._parse_hint()
3799-
3800-            if self._next and not self._next.token_type == TokenType.DOT:
3801-                all_ = self._match(TokenType.ALL)

<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "grep -rn \"\\\"hint\\\"\\|hint=\" sqlglot/ | grep -v \"join\\|Join\" | head -20; grep -n \"TokenType.UPDATE\\|TokenType.DELETE\" sqlglot/parser.py | head", "description": "Check hint arg usages and statement dispatch"}
[tool_result] sqlglot/tokens.py:561:            tokens_preceding_hint=self.TOKENS_PRECEDING_HINT,
sqlglot/parser.py:3428:                hint=hint,
sqlglot/parser.py:3835:                    hint=hint,
sqlglot/parser.py:4388:            kwargs["hint"] = hint
sqlglot/generator.py:2156:        hint = self.sql(expression, "hint")
sqlglot/generator.py:3063:        hint = self.sql(expression, "hint")
sqlglot/optimizer/merge_subqueries.py:55:    "hint",
sqlglot/optimizer/merge_subqueries.py:426:    inner_scope_hint
…[617 chars elided]…
ints])
638:        TokenType.UPDATE,
639:        TokenType.DELETE,
674:        TokenType.DELETE,
741:        TokenType.UPDATE,
1075:        TokenType.DELETE: lambda self: self._parse_delete(),
1093:        TokenType.UPDATE: lambda self: self._parse_update(),
1369:                self._match(TokenType.UPDATE)
3481:        if self._prev.token_type == TokenType.UPDATE:
7329:            if not self._match_set((TokenType.DELETE, TokenType.UPDATE)):
8880:                TokenType.UPDATE, advance=False
[assistant] Hints already flow through `Insert` via `_parse_hint()` right after the keyword, so I'll mirror that for `Update` and `Delete`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.ex
…[34 chars elided]…
\n                tables=tables,", "new_string": "        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add MySQL round-trip tests next to the existing SELECT hint tests, then run them to see what happens.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "offset": 246, "limit": 8}
[tool_result] 246	        self.validate_identity("LOCK TABLES `app_fields` WRITE", check_command_warning=True)
247	        self.validate_identity("SELECT 1 XOR 0")
248	        self.validate_identity("SELECT 1 && 0", "SELECT 1 AND 0")
249	        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
250	        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
251	        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
252	        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
253	        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_RANGE_OPTIMIZATION(t1) */ t1 SET c = 1 WHERE id = 2\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(del) */ FROM t1 WHERE id = 2\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112153-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_RANGE_OPTIMIZATION(t1) */ t1 SET c = 1 WHERE id = 2','DELETE /*+ QB_NAME(del) */ FROM t1 WHERE id = 2','DELETE /*+ X */ t1 FROM t1 JOIN t2 ON 1=1','UPDATE t SET c=1']:\n    e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('hint')), '->', e.sql('mysql'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Verify hint round-trip and run MySQL/Oracle tests"}
[tool_result] Hint(
  expressions=[
    Anonymous(
      this=NO_RANGE_OPTIMIZATION,
      expressions=[
        Column(
          this=Identifier(this=t1, quoted=False))])]) -> UPDATE /*+ NO_RANGE_OPTIMIZATION(t1) */ t1 SET c = 1 WHERE id = 2
Hint(
  expressions=[
    Anonymous(
      this=QB_NAME,
      expressions=[
        Column(
          this=Identifier(this=del, quoted=False))])]) -> DELETE /*+ QB_NAME(del) */ FROM t1 WHERE id = 2
Hint(
  expressions=[
    Var(this=X)]) -> DELETE /*+ X */ t1 FROM t1 JOIN t2 ON 1 = 1
None -> UPDATE t SET c = 1
.............................. [ 40%]
............................................                         [100%]
74 passed, 694 subtests passed in 0.33s
[assistant] Targeted tests pass and the hints round-trip. Now the project's full check suite and lint.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; ($PY -m ruff check sqlglot tests && $PY -m ruff format --check sqlglot tests) 2>&1 | tail -3", "description": "Run full test suite and ruff checks"}
[tool_result] ....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 54.54s
All checks passed!
232 files already formatted
[assistant] MySQL `UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests), and ruff check and format are clean. I haven't committed.

**Changes:**
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching `Insert`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` right after the keyword, as `_parse_insert` already does.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t1 ...` and `delete_sql` emits `DELETE /*+ ... */ FROM t1 ...`.
- **`tests/dialects/test_mysql.py`**: two identity tests, one for `UPDATE` and one for `DELETE`, placed next to the existing SELECT hint tests.

**Choices I made:**
- I put the hint parsing in the base parser rather than the MySQL dialect, following how `Insert` already works. Other dialects that use `/*+ */` on UPDATE or DELETE will now keep the hint instead of dropping it. If you want this limited to MySQL, that's a small move.
- The `DELETE` multi-table form also keeps its hint, e.g. `DELETE /*+ X */ t1 FROM t1 JOIN t2 ...`.
