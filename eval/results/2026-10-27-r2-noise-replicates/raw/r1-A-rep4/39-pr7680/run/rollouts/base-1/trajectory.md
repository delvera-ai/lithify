# trajectory base-1

final message:
MySQL multi-table `UPDATE` now parses and round-trips, covering both comma-separated tables and explicit joins. The full test suite passes (1112 tests) and ruff is clean.

**Root cause:** the target table already excluded `SET` as an alias, but comma-joined tables were parsed with the default alias tokens. So in `UPDATE authors, books SET ...`, `SET` was consumed as the alias for `books`, and the parser then failed on `authors`.

**Change** (`sqlglot/parser.py`):
- `_parse_update` parses the target table with `UPDATE_ALIAS_TOKENS`, then attaches any joins.
- A new `_parse_update_joins` handles comma-joined tables with the same alias restriction, and delegates explicit `JOIN ... ON` clauses to the existing `_parse_join`. Interleaved forms like `a JOIN b ON ..., c SET` also work.

**Tests** (`tests/dialects/test_mysql.py`): added round-trip identity cases for:
- `UPDATE authors, books SET ...` (the case from the report)
- aliased comma tables with `WHERE`
- explicit `INNER JOIN ... ON ... SET`
- a mix of explicit join and comma join

**Choices I made:**
- I put the fix in the base parser rather than the MySQL dialect class, because `_parse_update` is generic and the join handling is already shared. Other dialects will now also accept comma-joined `UPDATE` targets. Their output is unchanged for the single-table form.
- I did not run mypy; the pre-commit mypy hook is the remaining check I skipped.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"_parse_update\\|def _parse_join\\|UPDATE\" sqlglot/parser.py | head -50 && grep -n \"UPDATE\\|Update\" sqlglot/dialects/mysql.py | head -30 && grep -n \"class Update\" -A 25 sqlglot/expressions.py | head -40", "description": "Inspect repo state and locate UPDATE parsing code"}
[tool_result] 653:        TokenType.UPDATE,
756:        TokenType.UPDATE,
795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
1109:        TokenType.UPDATE: lambda self: self._parse_update(),
1385:                self._match(TokenType.UPDATE)
1583:        **dict.fromkeys(("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK", "UPDATE"), tuple()),
1584:        "DO": ("NOTHING", "UPDATE"),
1738:        "UPDATE": lambda self: self._parse_analyze_histogram(),
2645:                self.raise_
…[627 chars elided]…
tch_set((TokenType.DELETE, TokenType.UPDATE)):
7447:                self.raise_error("Expected DELETE or UPDATE")
8124:    def _parse_join_hint(self, func_name: str) -> exp.JoinHint:
8950:        if self._match_text_seq("REF", "UPDATE"):
8952:            this = "UPDATE"
8954:                this = "UPDATE SET DANGLING TO NULL"
9008:                TokenType.UPDATE, advance=False
9074:            elif self._match(TokenType.UPDATE):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()','UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Reproduce the parse error on MySQL UPDATE forms"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now()
Update(
  this=Table(
    this=Identifier(this=authors, quoted=False),
    joins=[
      Join(
        this=Table(
          this=Identifier(this=books, quoted=False)),
        kind=INNER,
        on=EQ(
          this=Column(
            this=Identifier(this=id, quoted=False),
            table=Identifier(this=authors, quoted=False)),
          expression=Column(
            this=Identifier(this=author_id, quoted=False),
            table=Identifier(this=books, quoted=False))))]),
  expressions=[
    EQ(
      this=Column(
        this=Identifier(this=x, quoted=False),
        table=Identifier(this=authors, quoted=False)),
      expression=Literal(this=1, is_string=False))])
UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1
[assistant] The reproduction confirms the failure: the comma-separated form errors at `SET`, while the explicit `INNER JOIN` form parses. Next I'll read `_parse_update` and the join-handling code.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "offset": 3640, "limit": 30}
[tool_result] 3640	        )
3641	
3642	    def _parse_update(self) -> exp.Update:
3643	        hint = self._parse_hint()
3644	        kwargs: dict[str, object] = {
3645	            "hint": hint,
3646	            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647	        }
3648	        while self._curr:
3649	            if self._match(TokenType.SET):
3650	                kwargs["expressions"] = self._parse_csv(self._parse_equality)
3651	            elif self._match(TokenType.RE
…[503 chars elided]…
from_
3660	            elif self._match(TokenType.WHERE, advance=False):
3661	                kwargs["where"] = self._parse_where()
3662	            elif self._match(TokenType.ORDER_BY, advance=False):
3663	                kwargs["order"] = self._parse_order()
3664	            elif self._match(TokenType.LIMIT, advance=False):
3665	                kwargs["limit"] = self._parse_limit()
3666	            else:
3667	                break
3668	
3669	        return self.expression(exp.Update(**kwargs))
[tool_use Bash] {"command": "grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30; grep -n \"Update\\b\" sqlglot/generator.py | head; grep -n \"def update_sql\" -A 30 sqlglot/generator.py; grep -n \"_parse_csv\\|COMMA\" sqlglot/parser.py | sed -n 1,5p; grep -n \"joins\\b\" sqlglot/parser.py | head -40", "description": "Read update parsing, table parsing and generator update_sql"}
[tool_result] 4737:    def _parse_table(
4738-        self,
4739-        schema: bool = False,
4740-        joins: bool = False,
4741-        alias_tokens: t.Collection[TokenType] | None = None,
4742-        parse_bracket: bool = False,
4743-        is_db_reference: bool = False,
4744-        parse_partition: bool = False,
4745-        consume_pipe: bool = False,
4746-    ) -> exp.Expr | None:
4747-        if not schema and not is_db_reference and not consume_pipe and not joins:
4748-            index = self.
…[3732 chars elided]…
           kwargs["this"].set("joins", joins if joins else None)
4740:        joins: bool = False,
4747:        if not schema and not is_db_reference and not consume_pipe and not joins:
4790:            if joins:
4791:                for join in self._parse_joins():
4792:                    subquery.append("joins", join)
4862:        if joins:
4863:            for join in self._parse_joins():
4864:                this.append("joins", join)
5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
[tool_use Bash] {"command": "sed -n 2514,2545p sqlglot/generator.py; sed -n 4402,4425p sqlglot/parser.py; grep -n \"UPDATE\" tests/dialects/test_mysql.py | head -30; grep -n \"def test_update\\|UPDATE\" tests/test_transpile.py tests/dialects/test_dialect.py | head", "description": "Read update join generator and comma-join parsing"}
[tool_result]     def _update_from_joins_sql(self, expression: exp.Update) -> tuple[str, str]:
        """
        Returns (join_sql, from_sql) for UPDATE statements.
        - join_sql: placed after UPDATE table, before SET
        - from_sql: placed after SET clause (standard position)
        Dialects like MySQL need to convert FROM to JOIN syntax.
        """
        if self.UPDATE_STATEMENT_SUPPORTS_FROM or not (from_expr := expression.args.get("from_")):
            return ("", self.sql(expression, "fro
…[6073 chars elided]…
ED AND EXISTS(SELECT b.name EXCEPT DISTINCT SELECT d.name) THEN UPDATE SET b.name = d.name",
tests/dialects/test_dialect.py:3084:                "snowflake": "MERGE INTO a AS b USING c AS d ON b.id = d.id WHEN MATCHED AND EXISTS(SELECT b.name EXCEPT SELECT d.name) THEN UPDATE SET b.name = d.name",
tests/dialects/test_dialect.py:3085:                "spark": "MERGE INTO a AS b USING c AS d ON b.id = d.id WHEN MATCHED AND EXISTS(SELECT b.name EXCEPT SELECT d.name) THEN UPDATE SET b.name = d.name",
[assistant] The root cause is visible now: in `UPDATE authors, books SET ...`, the comma-join's table parse uses the default alias tokens, so `SET` is consumed as the alias for `books`. The target table already excludes `SET` via `UPDATE_ALIAS_TOKENS`, but joined tables don't. I'll check how join tables get parsed to find the right hook.
[tool_use Bash] {"command": "sed -n 4425,4480p sqlglot/parser.py; sed -n 5059,5075p sqlglot/parser.py; grep -n \"UPDATE_ALIAS_TOKENS\\|TABLE_ALIAS_TOKENS\" sqlglot/parser.py sqlglot/dialects/*.py | head -20", "description": "Read join table parsing and alias token usage"}
[tool_result]             side = None

        outer_apply = self._match_pair(TokenType.OUTER, TokenType.APPLY, False)
        cross_apply = self._match_pair(TokenType.CROSS, TokenType.APPLY, False)

        if not skip_join_token and not join and not outer_apply and not cross_apply:
            return None

        kwargs: dict[str, t.Any] = {"this": self._parse_table(parse_bracket=parse_bracket)}
        if kind and kind.token_type == TokenType.ARRAY and self._match(TokenType.COMMA):
            kwargs["exp
…[2775 chars elided]…
e(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
sqlglot/parser.py:3646:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
sqlglot/parser.py:4046:            self._parse_id_var(any_token=any_token, tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
sqlglot/parser.py:4766:                        alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
sqlglot/parser.py:4837:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
[assistant] The fix belongs in `_parse_update`: parse the target, then consume comma-joined tables with `UPDATE_ALIAS_TOKENS` so `SET` is not taken as an alias. Explicit `JOIN ... ON` tables can keep the default path, since `ON` terminates them. I'll make the change and check how the generator renders the result.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:\n        hint = self._parse_hint()\n        kwargs: dict[str, object] = {\n            \"hint\": hint,\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UP
…[43 chars elided]…
le self._curr:", "new_string": "    def _parse_update(self) -> exp.Update:\n        hint = self._parse_hint()\n        this = self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS)\n        if this:\n            for join in self._parse_update_joins():\n                this.append(\"joins\", join)\n\n        kwargs: dict[str, object] = {\"hint\": hint, \"this\": this}\n        while self._curr:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        return self.expression(exp.Update(**kwargs))", "new_string": "        return self.expression(exp.Update(**kwargs))\n\n    def _parse_update_joins(self) -> t.Iterator[exp.Join]:\n        # A comma-joined table is followed by SET, so it must not take SET as its alias\n        while True:\n            if self._match(TokenType.COMMA):\n                table = self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS)\n                yield self.expression(exp.Join(this=table))\n            elif join := self._parse_join():\n                yield join\n            else:\n                break"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = [\n 'UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n 'UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1',\n 'UPDATE authors a, books b SET a.x = 1, b.y = 2 WHERE a.id = b.author_id',\n 'UPDATE authors a JOIN
…[113 chars elided]…
>= 5 LIMIT 10',\n]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', s, '\\n', ex)\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/test_transpile.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Verify fixed MySQL UPDATE forms and run related tests"}
[tool_result] UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1
UPDATE authors AS a, books AS b SET a.x = 1, b.y = 2 WHERE a.id = b.author_id
UPDATE authors AS a JOIN books AS b ON a.id = b.author_id, pubs AS p SET a.x = 1, p.y = 2
UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10
............................................................................ [ 42%]
............................................................................................. [ 95%]
........                           [100%]
177 passed, 4333 subtests passed in 0.84s
[assistant] All four forms parse and round-trip, and the related tests pass. Next I'll add regression tests next to the existing MySQL UPDATE identity tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "offset": 22, "limit": 6}
[tool_result] 22	        self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
23	        self.validate_identity("CREATE TABLE temp (id SERIAL PRIMARY KEY)")
24	        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
25	        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
26	        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
27	        self.validate_identity("DELETE /*+ MAX_EXECUTION_TIME(1) */ FROM t WHERE a = 1")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n", "new_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n        self.validat
…[155 chars elided]…
          \"UPDATE authors AS a, books AS b SET a.x = 1, b.y = 2 WHERE a.id = b.author_id\"\n        )\n        self.validate_identity(\n            \"UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1\"\n        )\n        self.validate_identity(\n            \"UPDATE authors AS a JOIN books AS b ON a.id = b.author_id, pubs AS p SET a.x = 1, p.y = 2\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-224831-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -m ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Run full test suite plus ruff lint and format checks"}
[tool_result] ............................................................................................................................................................................................................................................... [ 21%]
.................................... [ 24%]
.................................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[323 chars elided]…
.............................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 48.49s
All checks passed!
177 files already formatted
[assistant] Full suite passes (1112 tests) and ruff is clean. I'll review the final diff.
[tool_use Bash] {"command": "git diff --stat && git diff sqlglot/parser.py", "description": "Show final diff of parser changes"}
[tool_result]  sqlglot/parser.py            | 21 +++++++++++++++++----
 tests/dialects/test_mysql.py | 12 ++++++++++++
 2 files changed, 29 insertions(+), 4 deletions(-)
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 009573d91..2ad226160 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -3641,10 +3641,12 @@ class Parser:
 
     def _parse_update(self) -> exp.Update:
         hint = self._parse_hint()
-        kwargs: dict[str, object] = {
-            "hint": hint,
-            "this": self.
…[646 chars elided]…
# A comma-joined table is followed by SET, so it must not take SET as its alias
+        while True:
+            if self._match(TokenType.COMMA):
+                table = self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS)
+                yield self.expression(exp.Join(this=table))
+            elif join := self._parse_join():
+                yield join
+            else:
+                break
+
     def _parse_use(self) -> exp.Use:
         return self.expression(
             exp.Use(
[assistant] MySQL multi-table `UPDATE` now parses and round-trips, covering both comma-separated tables and explicit joins. The full test suite passes (1112 tests) and ruff is clean.

**Root cause:** the target table already excluded `SET` as an alias, but comma-joined tables were parsed with the default alias tokens. So in `UPDATE authors, books SET ...`, `SET` was consumed as the alias for `books`, and the parser then failed on `authors`.

**Change** (`sqlglot/parser.py`):
- `_parse_update` parses the target table with `UPDATE_ALIAS_TOKENS`, then attaches any joins.
- A new `_parse_update_joins` handles
…[216 chars elided]…
/test_mysql.py`): added round-trip identity cases for:
- `UPDATE authors, books SET ...` (the case from the report)
- aliased comma tables with `WHERE`
- explicit `INNER JOIN ... ON ... SET`
- a mix of explicit join and comma join

**Choices I made:**
- I put the fix in the base parser rather than the MySQL dialect class, because `_parse_update` is generic and the join handling is already shared. Other dialects will now also accept comma-joined `UPDATE` targets. Their output is unchanged for the single-table form.
- I did not run mypy; the pre-commit mypy hook is the remaining check I skipped.
