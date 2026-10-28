# trajectory base-1

final message:
MySQL optimizer hints now parse and round-trip on `UPDATE` and `DELETE`, the same way they already do on `SELECT` and `INSERT`. The full suite passes (1087 tests) and ruff check and format are clean on the changed files.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`. The parser was the gap: it failed with "Expected table name but got … HINT".

Changes:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` parse the hint right after the keyword, matching `_parse_insert`.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ … */ t …` and `delete_sql` emits `DELETE /*+ … */ FROM t …`.
- **`tests/dialects/test_mysql.py`**: added round-trip cases for a single-table `UPDATE`, a single-table `DELETE`, and a multi-table `DELETE` with a hint.

The changes are uncommitted in the worktree. I didn't commit, since you only asked for the code change.

## events
[tool_use Bash] {"command": "grep -n \"hint\" sqlglot/parser.py | head -80; echo ---; grep -n -i \"hint\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -40", "description": "Find hint handling in parser and generator"}
[tool_result] 1042:        exp.Hint: lambda self: self._parse_hint_body(),
3394:        hint = self._parse_hint()
3428:                hint=hint,
3798:            hint = self._parse_hint()
3835:                    hint=hint,
4098:    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
4106:    def _parse_hint_function_call(self) -> exp.Expr | None:
4109:    def _parse_hint_body(self) -> exp.Hint | None:
4113:        hints = []
4115:            for hint in iter(
4117:                    lambda: self._
…[3017 chars elided]…
glot/generator.py:3109:        top_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{distinct}"
sqlglot/generator.py:4439:    def joinhint_sql(self, expression: exp.JoinHint) -> str:
sqlglot/generator.py:4484:        hints = table.args.get("hints")
sqlglot/generator.py:4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3380,3440p sqlglot/parser.py; echo ----; sed -n 3780,3850p sqlglot/parser.py; echo ----; sed -n 4095,4140p sqlglot/parser.py; echo ----; grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_merge\" sqlglot/parser.py", "description": "Read hint parsing and SELECT/INSERT paths"}
[tool_result]             )

        expression = parse_conditional_insert()
        while expression is not None:
            expressions.append(expression)
            expression = parse_conditional_insert()

        return self.expression(
            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
            comments=comments,
        )

    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
        comments: list[str] = []
        hint = self._parse_hin
…[5572 chars elided]…
-> exp.Hint | None:
        if self._match(TokenType.HINT) and self._prev_comments:
            return exp.maybe_parse(self._prev_comments[0], into=exp.Hint, dialect=self.dialect)

        return None

    def _parse_into(self) -> exp.Into | None:
        if not self._match(TokenType.INTO):
            return None

----
3049:    def _parse_mergeblockratio(
3582:    def _parse_delete(self) -> exp.Delete:
3605:    def _parse_update(self) -> exp.Update:
8896:    def _parse_merge(self) -> exp.Merge:
[tool_use Bash] {"command": "sed -n 3582,3630p sqlglot/parser.py; echo ----; grep -n \"class Update\\|class Delete\\|class Insert\\|class Select(\" -A 12 sqlglot/expressions/*.py | grep -n \"hint\\|class\\|arg_types\" | head; echo ----; grep -n \"def update_sql\\|def delete_sql\" -A 25 sqlglot/generator.py | head -80; echo ----; grep -rn \"hint\" tests/dialects/test_mysql.py | head -30", "description": "Read update/delete parsers and generator"}
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
…[5049 chars elided]…
.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
----
tests/dialects/test_mysql.py:126:            "/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
tests/dialects/test_mysql.py:127:            "/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
tests/dialects/test_mysql.py:298:        # Index hints
[tool_use Bash] {"command": "sed -n 71,90p sqlglot/expressions/dml.py; echo ----; sed -n 293,310p sqlglot/expressions/dml.py; echo ----; grep -rn \"/\\*+\" tests/ | grep -i \"insert\\|update\\|delete\" | head -20; echo ----; grep -n \"HINT\" sqlglot/tokens.py sqlglot/dialects/mysql.py | head", "description": "Inspect DML arg_types and existing hint tests"}
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
…[1128 chars elided]…
/tokens.py:106:        if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107:            cls._COMMENTS[cls.HINT_START] = "*/"
sqlglot/tokens.py:184:    HINT_START = "/*+"
sqlglot/tokens.py:186:    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE}
sqlglot/tokens.py:204:        HINT_START: TokenType.HINT,
sqlglot/tokens.py:560:            hint_start=self.HINT_START,
sqlglot/tokens.py:561:            tokens_preceding_hint=self.TOKENS_PRECEDING_HINT,
[assistant] Tokenizer already emits hint tokens after `UPDATE` and `DELETE`. Let me check what actually happens today.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT /*+ NO_INDEX(t) */ 1 FROM t','INSERT /*+ IGNORE */ INTO t VALUES (1)','UPDATE /*+ NO_INDEX(t) */ t SET a = 1','DELETE /*+ NO_INDEX(t) */ FROM t WHERE a = 1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('hint'))); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"TOKENS_PRECEDING_HINT\\|hint\" sqlglot/tokenizer_core.py | head", "description": "Check current hint behavior on DML in MySQL"}
[tool_result] Hint(
  expressions=[
    Anonymous(
      this=NO_INDEX,
      expressions=[
        Column(
          this=Identifier(this=t, quoted=False))])])
SELECT /*+ NO_INDEX(t) */ 1 FROM t
Hint(
  expressions=[
    IGNORE])
INSERT /*+ IGNORE */ INTO t VALUES (1)
ERR Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX(t) */, line: 1, col: 25, start: 7, end: 24, comments: [' NO_INDEX(t) ']>. Line 1, Col: 25.
  UPDATE [4m/*+ NO_INDEX(t) */[0m t SET a = 1
ERR Expected table 
…[85 chars elided]…
l: 25, start: 7, end: 24, comments: [' NO_INDEX(t) ']>. Line 1, Col: 25.
  DELETE [4m/*+ NO_INDEX(t) */[0m FROM t WHERE a = 1
559:        "hint_start",
560:        "tokens_preceding_hint",
590:        hint_start: str,
591:        tokens_preceding_hint: set[TokenType],
618:        self.hint_start = hint_start
619:        self.tokens_preceding_hint = tokens_preceding_hint
901:            comment_start == self.hint_start
903:            and self.tokens[-1].token_type in self.tokens_preceding_hint
[assistant] Confirmed: `UPDATE`/`DELETE` hints tokenize but the parser fails on them. The fix mirrors what `INSERT` already does: add a `hint` arg, parse it at the start of the statement, and emit it in the generator. Let me check how the statement dispatcher calls these.
[tool_use Bash] {"command": "grep -n \"_parse_update\\|_parse_delete\\|_parse_insert\\b\" sqlglot/parser.py sqlglot/dialects/*.py | head; echo ---; grep -n \"UPDATE\\b\" tests/dialects/test_mysql.py | head -5", "description": "Locate update/delete parser dispatch and mysql tests"}
[tool_result] sqlglot/parser.py:1075:        TokenType.DELETE: lambda self: self._parse_delete(),
sqlglot/parser.py:1081:        TokenType.INSERT: lambda self: self._parse_insert(),
sqlglot/parser.py:1093:        TokenType.UPDATE: lambda self: self._parse_update(),
sqlglot/parser.py:3392:    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
sqlglot/parser.py:3582:    def _parse_delete(self) -> exp.Delete:
sqlglot/parser.py:3605:    def _parse_update(self) -> exp.Update:
---
24:        self.valida
…[61 chars elided]…
>= 5 LIMIT 10")
57:            "INSERT INTO things (a, b) VALUES (1, 2) AS new_data ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), a = new_data.a, b = new_data.b"
66:            "UPDATE items SET items.price = 0 WHERE items.id >= 5 ORDER BY items.id LIMIT 10"
84:            "INSERT INTO t1 (a, b, c) VALUES (1, 2, 3), (4, 5, 6) ON DUPLICATE KEY UPDATE c = VALUES(a) + VALUES(b)"
87:            "INSERT INTO t1 (a, b) SELECT c, d FROM t2 UNION SELECT e, f FROM t3 ON DUPLICATE KEY UPDATE b = b + c"
[assistant] The dispatcher consumes the keyword before calling `_parse_update`/`_parse_delete`, so the same `_parse_hint()`-first pattern as `_parse_insert` applies. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_delete(self) -> exp.Delete:\n        # This handles MySQL's \"Multiple-Table Syntax\"\n        # https://dev.mysql.com/doc/refman/8.0/en/delete.html\n        tables = None\n        if not self._match(Toke
…[364 chars elided]…
ps://dev.mysql.com/doc/refman/8.0/en/delete.html\n        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        tables = f\" {tables}\" if tables else \"\"\n        if self.RETURNING_END:\n            expression_sql = f\"{this}{using}{cluster}{where}{returning}{order}{limit}\"\n        else:\n            expression_sql
…[179 chars elided]…
 f\" {tables}\" if tables else \"\"\n        hint = self.sql(expression, \"hint\")\n        if self.RETURNING_END:\n            expression_sql = f\"{this}{using}{cluster}{where}{returning}{order}{limit}\"\n        else:\n            expression_sql = f\"{returning}{this}{using}{cluster}{where}{order}{limit}\"\n        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")\n        join_sql, from_sql = self._update_from_joins_sql(expression)", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")\n        join_sql, from_sql = self._update_from_joins_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests. I'll add round-trip cases to the MySQL test file next to the existing `UPDATE`/`DELETE` identity checks.
[tool_use Bash] {"command": "grep -n \"DELETE\\|def test_\" tests/dialects/test_mysql.py | head -30; sed -n 20,30p tests/dialects/test_mysql.py", "description": "Locate DELETE tests and test method layout in mysql tests"}
[tool_result] 12:    def test_ddl(self):
25:        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
26:        self.validate_identity("DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id")
72:            "DELETE t1 FROM t1 LEFT JOIN t2 ON t1.id = t2.id WHERE t2.id IS NULL"
75:            "DELETE t1, t2 FROM t1 INNER JOIN t2 INNER JOIN t3 WHERE t1.id = t2.id AND t2.id = t3.id"
78:            "DELETE FROM t1, t2 USING t1 INNER JOIN t2 INNER JOIN t3 WHERE t1.id = t2.id AND t2.id = t3.id"
238: 
…[1276 chars elided]…
= 5 LIMIT 10")
        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
        self.validate_identity("DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id")
        self.validate_identity("CREATE TABLE foo (a BIGINT, INDEX USING BTREE (b))")
        self.validate_identity("CREATE TABLE foo (a BIGINT, FULLTEXT INDEX (b))")
        self.validate_identity("CREATE TABLE foo (a BIGINT, SPATIAL INDEX (b))")
        self.validate_identity("CREATE TABLE foo (a INT UNSIGNED ZEROFILL)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id\")\n", "new_string": "        self.validate_identity(\"DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id\")\n        self.validate_identity(\"UPDATE /*+ NO_INDEX(t) */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t) */ FROM t WHERE a = 1\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t1) */ t1 FROM t1 INNER JOIN t2 WHERE t1.id = t2.id\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-160703-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Running the MySQL tests first, then the full suite with the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Run MySQL dialect tests"}
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.57s
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[177 chars elided]…
.................................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 71.65s (0:01:11)
[assistant] All 1087 tests pass. Let me run the linter and formatter on the changed files, since the project's `make check` includes style.
[tool_use Bash] {"command": "F=\"sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py\"; (<work>/env-sqlglot/bin/python -m ruff check $F && <work>/env-sqlglot/bin/python -m ruff format --check $F) 2>&1 | tail -10; git diff --stat", "description": "Lint, format-check changed files and show diff stat"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py:1:1

Found 1 error.
 sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 3 +++
 4 files changed, 12 insertions(+), 2 deletions(-)
[assistant] The failure is from my shell command: the file list didn't split (the shell isn't word-splitting the variable). Re-running with explicit paths.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py 2>&1 | tail -5", "description": "Run ruff check and format check on changed files"}
[tool_result] All checks passed!
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format tests/dialects/test_mysql.py && git diff", "description": "Apply ruff formatting to test file and show diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/expressions/dml.py b/sqlglot/expressions/dml.py
index ed5098322..394325360 100644
--- a/sqlglot/expressions/dml.py
+++ b/sqlglot/expressions/dml.py
@@ -71,6 +71,7 @@ class DML(Expr):
 class Delete(Expression, DML):
     arg_types = {
         "with_": False,
+        "hint": False,
         "this": False,
         "using": False,
         "where": False,
@@ -293,6 +294,7 @@ class LoadData(Expression):
 class Update(Expression, DML):
     arg_types = {
    
…[3659 chars elided]…
a = 1")
+        self.validate_identity(
+            "DELETE /*+ NO_INDEX(t1) */ t1 FROM t1 INNER JOIN t2 WHERE t1.id = t2.id"
+        )
         self.validate_identity("CREATE TABLE foo (a BIGINT, INDEX USING BTREE (b))")
         self.validate_identity("CREATE TABLE foo (a BIGINT, FULLTEXT INDEX (b))")
         self.validate_identity("CREATE TABLE foo (a BIGINT, SPATIAL INDEX (b))")
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[assistant] Formatting only touched my new test lines. One last run of the MySQL tests after the reformat.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Re-run MySQL tests after formatting"}
[tool_result] ....................                                              [100%]
50 passed, 481 subtests passed in 0.31s
[assistant] MySQL optimizer hints now parse and round-trip on `UPDATE` and `DELETE`, the same way they already do on `SELECT` and `INSERT`. The full suite passes (1087 tests) and ruff check and format are clean on the changed files.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`. The parser was the gap: it failed with "Expected table name but got … HINT".

Changes:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` parse the hint right after the keyword, matching `_parse_insert`.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ … */ t …` and `delete_sql` emits `DELETE /*+ … */ FROM t …`.
- **`tests/dialects/test_mysql.py`**: added round-trip cases for a single-table `UPDATE`, a single-table `DELETE`, and a multi-table `DELETE` with a hint.

The changes are uncommitted in the worktree. I didn't commit, since you only asked for the code change.
