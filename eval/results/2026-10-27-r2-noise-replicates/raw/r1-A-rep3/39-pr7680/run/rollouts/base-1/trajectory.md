# trajectory base-1

final message:
Multi-table MySQL `UPDATE` now parses and round-trips, covering both comma-separated tables and explicit joins. The full suite passes (1112 tests), and ruff and mypy are clean.

**Cause:** the explicit `JOIN` form already worked. The comma form failed because the comma branch of `_parse_join` parsed `books` with the default table-alias tokens, so `SET` was swallowed as an alias.

**Fix** (`sqlglot/parser.py`):
- `_parse_update` now parses the target table with `UPDATE_ALIAS_TOKENS`, which already excludes `SET`, and collects any following joins.
- A new `_parse_update_join` helper handles a comma as a cross join, using `UPDATE_ALIAS_TOKENS` for the table. Other joins go through `_parse_join` as before.
- Joins are still attached to the target table, so the AST shape matches the existing `UPDATE a JOIN b ON …` representation.

**Tests** (`tests/dialects/test_mysql.py`): added MySQL identity round-trips for the issue's statement, a `WHERE` on a comma-joined update, aliased comma tables with `ORDER BY`/`LIMIT`, and a comma table followed by an explicit `JOIN`.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"_parse_update\\|UPDATE\" sqlglot/parser.py | head -50; grep -n \"UPDATE\\|Update\" sqlglot/dialects/mysql.py | head; grep -n \"class Update\" -A 25 sqlglot/expressions.py", "description": "Locate UPDATE parsing code"}
[tool_result ERROR] Exit code 2
653:        TokenType.UPDATE,
756:        TokenType.UPDATE,
795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
1109:        TokenType.UPDATE: lambda self: self._parse_update(),
1385:                self._match(TokenType.UPDATE)
1583:        **dict.fromkeys(("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK", "UPDATE"), tuple()),
1584:        "DO": ("NOTHING", "UPDATE"),
1738:        "UPDATE": lambda self: self._parse_analyze_histogram(),
2645:               
…[455 chars elided]…
t_seq("FOR", "NO", "KEY", "UPDATE"):
7446:            if not self._match_set((TokenType.DELETE, TokenType.UPDATE)):
7447:                self.raise_error("Expected DELETE or UPDATE")
8950:        if self._match_text_seq("REF", "UPDATE"):
8952:            this = "UPDATE"
8954:                this = "UPDATE SET DANGLING TO NULL"
9008:                TokenType.UPDATE, advance=False
9074:            elif self._match(TokenType.UPDATE):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 3640,3665p sqlglot/parser.py; grep -rn \"class Update(\" -A 25 sqlglot/expressions/*.py | head -40; grep -n \"def update_sql\" -A 30 sqlglot/generator.py; grep -n \"UPDATE\" sqlglot/dialects/mysql.py", "description": "Inspect update parsing and generation code"}
[tool_result]         )

    def _parse_update(self) -> exp.Update:
        hint = self._parse_hint()
        kwargs: dict[str, object] = {
            "hint": hint,
            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
        }
        while self._curr:
            if self._match(TokenType.SET):
                kwargs["expressions"] = self._parse_csv(self._parse_equality)
            elif self._match(TokenType.RETURNING, advance=False):
                kwargs["returning"]
…[3434 chars elided]…
ment, for example
2568-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2569-            args = self.expressions(expression)
2570-            alias = self.sql(expression, "alias")
2571-            values = f"VALUES{self.seg('')}{args}"
2572-            values = (
2573-                f"({values})"
2574-                if self.WRAP_DERIVED_VALUES
2575-                and (alias or isinstance(expression.parent, (exp.From, exp.Table)))
2576-                else values
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()', 'UPDATE authors JOIN books ON authors.id = books.author_id SET books.x = 1 WHERE 1=1', 'UPDATE a INNER JOIN b ON a.id=b.id SET a.x=1']:\n  try: print(repr(sqlglot.parse_one(s, read='mysql')))\n  except Exception as e: print('ERR', e)\n\" 2>&1 | head -30; grep -rn \"UPDATE.*, \" tests/dialects/test_mysql.py | head; grep -n \"_update_from_joins_sql\" -A 25 sqlglot/generator.py | head -40", "description": "Reproduce parse failure and inspect generator helper"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now()
Update(
  this=Table(
    this=Identifier(this=authors, quoted=False),
    joins=[
      Join(
        this=Table(
          this=Identifier(this=books, quoted=False)),
        on=EQ(
          this=Column(
            this=Identifier(this=id, quoted=False),
            table=Identifier(this=authors, quoted=False)),
          expression=Column(
    
…[2734 chars elided]…
pression, "order")
2554-        limit = self.sql(expression, "limit")
2555-        if self.RETURNING_END:
2556-            expression_sql = f"{from_sql}{where_sql}{returning}"
2557-        else:
2558-            expression_sql = f"{returning}{from_sql}{where_sql}"
2559-        options = self.expressions(expression, key="options")
2560-        options = f" OPTION({options})" if options else ""
2561-        sql = f"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}"
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('UPDATE authors, books SET x = 1', read='mysql')))\nprint(repr(sqlglot.parse_one('SELECT * FROM authors, books', read='mysql').args['joins']))\n\" 2>&1 | head -40; grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30; grep -n \"def _parse_join(\" -A 30 sqlglot/parser.py | grep -n \"COMMA\" ", "description": "Debug comma-separated update parsing"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/dialects/dialect.py", line 1119, in parse
    return self.p
…[1313 chars elided]…

4741-        alias_tokens: t.Collection[TokenType] | None = None,
4742-        parse_bracket: bool = False,
4743-        is_db_reference: bool = False,
4744-        parse_partition: bool = False,
4745-        consume_pipe: bool = False,
4746-    ) -> exp.Expr | None:
4747-        if not schema and not is_db_reference and not consume_pipe and not joins:
4748-            index = self._index
4749-            table = self._parse_table_parts(fast=True)
4:4405-        if self._match(TokenType.COMMA):
[tool_use Bash] {"command": "sed -n 4395,4420p sqlglot/parser.py; sed -n 4750,4800p sqlglot/parser.py; grep -n \"def join_sql\" -A 40 sqlglot/generator.py | grep -n \"COMMA\\|\\\", \\\"\\|\\\",\\\"\" ", "description": "Read join parsing and table parsing code"}
[tool_result]             this = self._parse_column()
            if isinstance(this, exp.Column):
                return this.this
            return this

        return self._parse_wrapped_csv(_parse_column_as_identifier, optional=True)

    def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(self._parse_table)
            cross_join = self.expression(exp.Join(this=ta
…[2031 chars elided]…
                for join in self._parse_joins():
                    subquery.append("joins", join)
            return subquery

        bracket = parse_bracket and self._parse_bracket(None)
        bracket = self.expression(exp.Table(this=bracket)) if bracket else None

        rows_from_tables = (
            self._parse_wrapped_csv(self._parse_table)
            if self._match_text_seq("ROWS", "FROM")
2:2698-        if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
[tool_use Bash] {"command": "sed -n 4420,4470p sqlglot/parser.py; grep -n \"TABLE_ALIAS_TOKENS\\b\" sqlglot/parser.py | head -3; grep -n \"def _parse_joins\" -A 8 sqlglot/parser.py; grep -n \"TokenType.SET\" sqlglot/parser.py sqlglot/dialects/mysql.py | head", "description": "Read join table parsing and alias token config"}
[tool_result]         if not skip_join_token and not join:
            self._retreat(index)
            kind = None
            method = None
            side = None

        outer_apply = self._match_pair(TokenType.OUTER, TokenType.APPLY, False)
        cross_apply = self._match_pair(TokenType.CROSS, TokenType.APPLY, False)

        if not skip_join_token and not join and not outer_apply and not cross_apply:
            return None

        kwargs: dict[str, t.Any] = {"this": self._parse_table(parse_bracket=
…[2272 chars elided]…
enType.SET: lambda self: self._parse_set(),
sqlglot/parser.py:2243:        if group and self._match(TokenType.SET):
sqlglot/parser.py:3512:            self._match(TokenType.SET)
sqlglot/parser.py:3649:            if self._match(TokenType.SET):
sqlglot/parser.py:7409:                elif self._match_pair(TokenType.SET, TokenType.NULL):
sqlglot/parser.py:7411:                elif self._match_pair(TokenType.SET, TokenType.DEFAULT):
sqlglot/parser.py:7453:            elif self._match(TokenType.SET):
[tool_use Bash] {"command": "grep -n \"if joins\" -B2 -A8 sqlglot/parser.py | sed -n 1,60p; sed -n 3665,3685p sqlglot/parser.py", "description": "Read joins handling in table parsing and update tail"}
[tool_result] 4462-            joins: list | None = list(self._parse_joins())
4463-
4464:            if joins and self._match(TokenType.ON):
4465-                kwargs["on"] = self._parse_disjunction()
4466:            elif joins and self._match(TokenType.USING):
4467-                kwargs["using"] = self._parse_using_identifiers()
4468-            else:
4469-                joins = None
4470-                self._retreat(index)
4471-
4472:            kwargs["this"].set("joins", joins if joins else None)
44
…[1365 chars elided]…
    return self.expression(
            exp.Use(
                kind=self._parse_var_from_options(self.USABLES, raise_unmatched=False),
                this=self._parse_table(schema=False),
            )
        )

    def _parse_uncache(self) -> exp.Uncache:
        if not self._match(TokenType.TABLE):
            self.raise_error("Expecting TABLE after UNCACHE")

        return self.expression(
            exp.Uncache(exists=self._parse_exists(), this=self._parse_table(schema=True))
        )
[assistant] The explicit `JOIN` form already parses. The comma form fails because `_parse_join`'s comma branch parses `books` with the default table-alias tokens, so `SET` gets swallowed as an alias. I'll make the UPDATE parser handle comma-separated tables itself with `UPDATE_ALIAS_TOKENS`, which already excludes `SET`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        hint = self._parse_hint()\n        kwargs: dict[str, object] = {\n            \"hint\": hint,\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }\n        while self._curr:", "new_string": "        hint = self._parse_hint()\n        this = self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS)\n        while join := self._parse_update_join():\n            this.append(\"joins\", join)\n\n        kwargs: dict[str, object] = {\"hint\": hint, \"this\": this}\n        while self._curr:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:", "new_string": "    def _parse_update_join(self) -> exp.Join | None:\n        # A comma-separated table is a cross join. Its alias is parsed with UPDATE_ALIAS_TOKENS\n        # so that the SET keyword isn't consumed as an alias when the table is followed by SET\n        if self._match(TokenType.COMMA):\n            return self.expression(exp.Join(this=self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS)))\n\n        return self._parse_join()\n\n    def _parse_update(self) -> exp.Update:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n 'UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id',\n 'UPDATE authors JOIN books ON authors.id = books.author_id SET books.x = 1 WHERE 1=1',\n 'UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1',\n 'UPDATE a AS x, b y SET x.v = 1, y.v = 2 ORDER BY x.v LIMIT 1',\n 'UPDATE t SET a = 1']:\n  print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n\" 2>&1 | tail -20; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects tests/test_parser.py tests/test_transpile.py 2>&1 | tail -15", "description": "Verify round-trips and run parser test suites"}
[tool_result] UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
UPDATE authors JOIN books ON authors.id = books.author_id SET books.x = 1 WHERE 1 = 1
UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1
UPDATE a AS x, b AS y SET x.v = 1, y.v = 2 ORDER BY x.v LIMIT 1
UPDATE t SET a = 1
...................................................................................................................................
…[332 chars elided]…
......................................................................................................................................................... [ 70%]
................ [ 72%]
...................................................................................................................................................................................................... [ 96%]
............................                               [100%]
826 passed, 12176 subtests passed in 12.61s
[assistant] Round-trips work and the existing parser and dialect suites pass. Now I'll add a MySQL test and run the full suite plus lint.
[tool_use Bash] {"command": "grep -n \"UPDATE\" tests/dialects/test_mysql.py | head -30", "description": "Find existing MySQL UPDATE tests"}
[tool_result] 24:        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
25:        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
84:            "INSERT INTO things (a, b) VALUES (1, 2) AS new_data ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), a = new_data.a, b = new_data.b"
93:            "UPDATE items SET items.price = 0 WHERE items.id >= 5 ORDER BY items.id LIMIT 10"
111:            "INSERT INTO t1 (a, b, c) VALUES (1, 2, 3), (4, 5, 6) 
…[1754 chars elided]…
41:        self.validate_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS MANUAL UPDATE")
1700:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
1705:            "CREATE TRIGGER track_deletes BEFORE DELETE ON orders FOR EACH ROW BEGIN UPDATE statistics SET delete_count = delete_count + 1 WHERE table_name = 'orders' END",
[tool_use Bash] {"command": "sed -n 22,27p tests/dialects/test_mysql.py", "description": "View context around UPDATE identity tests"}
[tool_result]         self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
        self.validate_identity("CREATE TABLE temp (id SERIAL PRIMARY KEY)")
        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
        self.validate_identity("DELETE /*+ MAX_EXECUTION_TIME(1) */ FROM t WHERE a = 1")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n", "new_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n        self.validat
…[42 chars elided]…
 books SET authors.deleted_at = NOW(), books.deleted_at = NOW()\"\n        )\n        self.validate_identity(\n            \"UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id\"\n        )\n        self.validate_identity(\"UPDATE a AS x, b AS y SET x.v = 1, y.v = 2 ORDER BY x.v LIMIT 1\")\n        self.validate_identity(\"UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -8", "description": "Run full test suite and lint checks"}
[tool_result] ................ [ 53%]
............................................................................................................................................................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 47.68s
All checks passed!
Would reformat: sqlglot/parser.py
1 file would be reformatted, 1 file already formatted
[assistant] The full suite passes (1112). Ruff wants to reformat my new helper, so I'll apply that and re-check.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parser.py && git diff sqlglot/parser.py && $PY -m ruff check sqlglot tests && $PY -m ruff format --check sqlglot tests | tail -1 && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -1", "description": "Format parser and show resulting diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 009573d91..37d25d564 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -3639,12 +3639,23 @@ class Parser:
             )
         )
 
+    def _parse_update_join(self) -> exp.Join | None:
+        # A comma-separated table is a cross join. Its alias is parsed with UPDATE_ALIAS_TOKENS
+        # so that the SET keyword isn't consumed as an alias when the table is followed by SET
+        if self._match(TokenType.C
…[501 chars elided]…
KENS)
+        while join := self._parse_update_join():
+            this.append("joins", join)
+
+        kwargs: dict[str, object] = {"hint": hint, "this": this}
         while self._curr:
             if self._match(TokenType.SET):
                 kwargs["expressions"] = self._parse_csv(self._parse_equality)
All checks passed!
236 files already formatted
51 passed, 486 subtests passed in 0.19s
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] Formatting and lint are clean. I'll run mypy too, since the pre-commit config includes it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 300 $PY -m mypy sqlglot/parser.py 2>&1 | tail -3", "description": "Type-check parser module with mypy"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py 2>&1 | tail -3", "description": "Type-check parser module with mypy"}
[tool_result] sqlglot/parser.py:3656: error: Item "None" of "Expr | None" has no attribute "append"  [union-attr]
Found 1 error in 1 file (checked 1 source file)
[assistant] mypy flags that `_parse_table` can return `None`. I'll only collect joins when a target table was parsed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        while join := self._parse_update_join():\n            this.append(\"joins\", join)", "new_string": "        while this and (join := self._parse_update_join()):\n            this.append(\"joins\", join)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-131813-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[assistant] The edit tool reports the file changed on disk since my last read. I'll check the diff for anything I didn't make before re-running checks.
[tool_use Bash] {"command": "git status --short && git diff --stat && PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py 2>&1 | tail -1; $PY -m ruff check sqlglot tests | tail -1; $PY -m ruff format --check sqlglot tests | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Check working tree changes and rerun all checks"}
[tool_result]  M sqlglot/parser.py
 M tests/dialects/test_mysql.py
 sqlglot/parser.py            | 19 +++++++++++++++----
 tests/dialects/test_mysql.py |  8 ++++++++
 2 files changed, 23 insertions(+), 4 deletions(-)
Success: no issues found in 1 source file
All checks passed!
237 files already formatted
1112 passed, 18136 subtests passed in 49.59s
[assistant] Multi-table MySQL `UPDATE` now parses and round-trips, covering both comma-separated tables and explicit joins. The full suite passes (1112 tests), and ruff and mypy are clean.

**Cause:** the explicit `JOIN` form already worked. The comma form failed because the comma branch of `_parse_join` parsed `books` with the default table-alias tokens, so `SET` was swallowed as an alias.

**Fix** (`sqlglot/parser.py`):
- `_parse_update` now parses the target table with `UPDATE_ALIAS_TOKENS`, which already excludes `SET`, and collects any following joins.
- A new `_parse_update_join` helper handles a comma as a cross join, using `UPDATE_ALIAS_TOKENS` for the table. Other joins go through `_parse_join` as before.
- Joins are still attached to the target table, so the AST shape matches the existing `UPDATE a JOIN b ON …` representation.

**Tests** (`tests/dialects/test_mysql.py`): added MySQL identity round-trips for the issue's statement, a `WHERE` on a comma-joined update, aliased comma tables with `ORDER BY`/`LIMIT`, and a comma table followed by an explicit `JOIN`.

Changes are uncommitted in the worktree.
