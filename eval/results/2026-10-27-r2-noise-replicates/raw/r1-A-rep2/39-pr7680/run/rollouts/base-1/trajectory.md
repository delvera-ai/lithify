# trajectory base-1

final message:
Multi-table MySQL `UPDATE` now parses and round-trips, for both comma-separated tables and explicit joins. The full suite passes (1112 tests) and ruff is clean. I haven't committed anything.

**Root cause:** the joined table in an `UPDATE` was parsed with the default table-alias tokens, so `SET` was consumed as the alias of the last table (`books SET`). `UPDATE` already had a set that excludes `SET`, but it only applied to the first table.

**Fix:**
- `sqlglot/parser.py`: `_parse_joins` and `_parse_join` take an optional `alias_tokens`, passed to the joined table and to nested joins. `_parse_table` forwards its `alias_tokens` to its joins. `UPDATE` already passes `UPDATE_ALIAS_TOKENS`, so its joins now use that set too. Non-UPDATE callers are unchanged, since they pass nothing.
- `sqlglot/parsers/clickhouse.py`: the `_parse_join` override accepts and forwards the new keyword.
- `tests/dialects/test_mysql.py`: identity tests for the comma form, the `INNER JOIN ... ON` form, and aliased comma tables.

**Behavior note:** `UPDATE authors JOIN books SET ...` (a join with no `ON`) is emitted as `UPDATE authors, books SET ...`. That's the generator's existing cross-join rendering, and it's equivalent in MySQL. I left it alone.

## events
[tool_use Bash] {"command": "grep -n \"UPDATE\\|_parse_update\\|def _parse_join\\|update_sql\" sqlglot/parser.py | head -60; grep -n \"Update\\|update\" sqlglot/dialects/mysql.py | head; grep -n \"class Update\" -A 25 sqlglot/expressions.py", "description": "Locate UPDATE parsing and generation code"}
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
…[639 chars elided]…
tch_set((TokenType.DELETE, TokenType.UPDATE)):
7447:                self.raise_error("Expected DELETE or UPDATE")
8124:    def _parse_join_hint(self, func_name: str) -> exp.JoinHint:
8950:        if self._match_text_seq("REF", "UPDATE"):
8952:            this = "UPDATE"
8954:                this = "UPDATE SET DANGLING TO NULL"
9008:                TokenType.UPDATE, advance=False
9074:            elif self._match(TokenType.UPDATE):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 3642,3665p sqlglot/parser.py; grep -rn \"class Update(\" -A 22 sqlglot/expressions/ ; grep -n \"def update_sql\" -A 25 sqlglot/generator.py; grep -n \"UPDATE\" sqlglot/dialects/mysql.py; ls sqlglot/dialects | head -50 | tr '\\n' ' '", "description": "Inspect update parsing, Update expression, and generator"}
[tool_result]     def _parse_update(self) -> exp.Update:
        hint = self._parse_hint()
        kwargs: dict[str, object] = {
            "hint": hint,
            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
        }
        while self._curr:
            if self._match(TokenType.SET):
                kwargs["expressions"] = self._parse_csv(self._parse_equality)
            elif self._match(TokenType.RETURNING, advance=False):
                kwargs["returning"] = self._pa
…[3379 chars elided]…
f.expressions(expression)
2570-            alias = self.sql(expression, "alias")
2571-            values = f"VALUES{self.seg('')}{args}"
__init__.py athena.py bigquery.py clickhouse.py databricks.py dialect.py doris.py dremio.py drill.py druid.py duckdb.py dune.py exasol.py fabric.py hive.py materialize.py mysql.py oracle.py postgres.py presto.py prql.py redshift.py risingwave.py singlestore.py snowflake.py solr.py spark.py spark2.py sqlite.py starrocks.py tableau.py teradata.py trino.py tsql.py
[assistant] Let me reproduce the failure and see how the generic parser handles the comma join.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n          'UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1=1',\n          'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id']:\n
…[9 chars elided]…
 in ['mysql','']:\n        try:\n            print(repr(sqlglot.parse_one(q, read=d)))\n            print(sqlglot.transpile(q, read=d, write='mysql'))\n        except Exception as e: print('ERR', d, str(e)[:200])\n\"; grep -n \"_parse_table(\" sqlglot/parser.py | head -3; grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30", "description": "Reproduce multi-table UPDATE parse failure"}
[tool_result] ERR mysql Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now()
ERR  Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now()
Update(
  this=Table(
    this=Identifier(this=authors, quoted=False),
    joins=[
      Join(
        this=Table(
          this=Identifier(this=books, quoted=False)),
        on=EQ(
          t
…[4001 chars elided]…
 bool = False,
4740-        joins: bool = False,
4741-        alias_tokens: t.Collection[TokenType] | None = None,
4742-        parse_bracket: bool = False,
4743-        is_db_reference: bool = False,
4744-        parse_partition: bool = False,
4745-        consume_pipe: bool = False,
4746-    ) -> exp.Expr | None:
4747-        if not schema and not is_db_reference and not consume_pipe and not joins:
4748-            index = self._index
4749-            table = self._parse_table_parts(fast=True)
[assistant] Explicit `JOIN` already parses; only the comma form fails. Checking how the parser handles comma joins.
[tool_use Bash] {"command": "sed -n 4402,4425p sqlglot/parser.py; grep -n \"TokenType.COMMA\" sqlglot/parser.py | head -30; grep -n \"def _update_from_joins_sql\" -A 20 sqlglot/generator.py", "description": "Inspect join parsing and comma handling"}
[tool_result]     def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(self._parse_table)
            cross_join = self.expression(exp.Join(this=table)) if table else None

            if cross_join and self.JOINS_HAVE_EQUAL_PRECEDENCE:
                cross_join.set("kind", "CROSS")

            return cross_join

        index = self._index
        method, side, kind = 
…[3018 chars elided]…
requires qualified column names in multi-table UPDATE to avoid ambiguity
2526-        target_table = expression.this
2527-        if isinstance(target_table, exp.Table):
2528-            target_name = exp.to_identifier(target_table.alias_or_name)
2529-            for eq in expression.expressions:
2530-                col = eq.this
2531-                if isinstance(col, exp.Column) and not col.table:
2532-                    col.set("table", target_name)
2533-
2534-        table = from_expr.this
[tool_use Bash] {"command": "awk 'NR>=4737 && NR<=4900 && /joins/ {print NR\": \"$0}' sqlglot/parser.py; sed -n 5059,5075p sqlglot/parser.py; grep -n \"UPDATE_STATEMENT_SUPPORTS_FROM\\|class Generator\\|TRANSFORMS\" sqlglot/dialects/mysql.py | head", "description": "Find where table joins are parsed"}
[tool_result] 4740:         joins: bool = False,
4747:         if not schema and not is_db_reference and not consume_pipe and not joins:
4790:             if joins:
4791:                 for join in self._parse_joins():
4792:                     subquery.append("joins", join)
4862:         if joins:
4863:             for join in self._parse_joins():
4864:                 this.append("joins", join)
    def _parse_joins(self) -> t.Iterator[exp.Join]:
        return iter(self._parse_join, None)

    def _parse_u
…[62 chars elided]…
not self._match(TokenType.INTO):
            return None

        return self.expression(
            exp.UnpivotColumns(
                this=self._match_text_seq("NAME") and self._parse_column(),
                expressions=self._match_text_seq("VALUE") and self._parse_csv(self._parse_column),
            )
        )

    # https://duckdb.org/docs/sql/statements/pivot
    def _parse_simplified_pivot(self, is_unpivot: bool | None = None) -> exp.Pivot:
        def _parse_on() -> exp.Expr | None:
[assistant] Comma joins go through `_parse_join`, which parses the joined table with default alias tokens. My guess: `SET` is being swallowed as the alias of `books`. Checking that.
[tool_use Bash] {"command": "sed -n 4425,4470p sqlglot/parser.py; grep -n \"UPDATE_ALIAS_TOKENS\\|TABLE_ALIAS_TOKENS:\" sqlglot/parser.py sqlglot/dialects/*.py | head; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['UPDATE authors JOIN books SET authors.x = 1','UPDATE authors, books SET x = 1']:\n  try: print(sqlglot.parse_one(q, read='mysql').sql('mysql'))\n  except Exception as e: print('ERR', str(e)[:80])\n\"", "description": "Check join table parsing and alias-token handling"}
[tool_result]             side = None

        outer_apply = self._match_pair(TokenType.OUTER, TokenType.APPLY, False)
        cross_apply = self._match_pair(TokenType.CROSS, TokenType.APPLY, False)

        if not skip_join_token and not join and not outer_apply and not cross_apply:
            return None

        kwargs: dict[str, t.Any] = {"this": self._parse_table(parse_bracket=parse_bracket)}
        if kind and kind.token_type == TokenType.ARRAY and self._match(TokenType.COMMA):
            kwargs["exp
…[1411 chars elided]…
 ID_VAR_TOKENS - {
sqlglot/parser.py:793:    COMMENT_TABLE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.IS}
sqlglot/parser.py:795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
sqlglot/parser.py:3646:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
ERR Invalid expression / Unexpected token. Line 1, Col: 37.
  UPDATE authors JOIN bo
ERR Invalid expression / Unexpected token. Line 1, Col: 27.
  UPDATE authors, books
[assistant] Confirmed: `SET` gets consumed as the alias of the joined table, for both the comma and the `JOIN` forms. The fix is to thread the UPDATE alias-token set through the join parsing. Checking callers before I change the signatures.
[tool_use Bash] {"command": "grep -rn \"_parse_joins(\\|_parse_join(\" sqlglot/ | grep -v \"def \" ; grep -rn \"joins=True\" sqlglot/ | head; sed -n 4855,4866p sqlglot/parser.py", "description": "Find all join parsing call sites"}
[tool_result] sqlglot/parser.py:1060:        exp.Join: lambda self: self._parse_join(),
sqlglot/parser.py:3657:                    table.set("joins", list(self._parse_joins()) or None)
sqlglot/parser.py:4118:            for join in self._parse_joins():
sqlglot/parser.py:4462:            joins: list | None = list(self._parse_joins())
sqlglot/parser.py:4791:                for join in self._parse_joins():
sqlglot/parser.py:4863:            for join in self._parse_joins():
sqlglot/parser.py:9825:        join = s
…[789 chars elided]…
=True, consume_pipe=True)
sqlglot/parsers/teradata.py:122:                from_=self._parse_from(joins=True),

        if not self.dialect.ALIAS_POST_TABLESAMPLE:
            this.set("sample", self._parse_table_sample())

        if not self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())

        if joins:
            for join in self._parse_joins():
                this.append("joins", join)

        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
[assistant] The ClickHouse parser overrides `_parse_join`, so a new keyword has to be accepted there too. Let me look at that override.
[tool_use Bash] {"command": "sed -n 664,672p sqlglot/parsers/clickhouse.py; grep -rn \"def _parse_join\\b\\|def _parse_joins\" sqlglot/ ", "description": "View ClickHouse _parse_join override"}
[tool_result]     def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        join = super()._parse_join(skip_join_token=skip_join_token, parse_bracket=True)
        if join:
            method = join.args.get("method")
            join.set("method", None)
            join.set("global_", method)
sqlglot/parser.py:4402:    def _parse_join(
sqlglot/parser.py:5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
sqlglot/parsers/clickhouse.py:665:    def _parse_join(
[tool_use Bash] {"command": "grep -n \"def _try_parse\" -A 4 sqlglot/parser.py; sed -n 4403,4406p sqlglot/parser.py; git status --short", "description": "Check _try_parse signature and clean worktree"}
[tool_result] 2007:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
2008-        index = self._index
2009-        error_level = self.error_level
2010-        this: T | None = None
2011-
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(self._parse_table)
[assistant] Plan: thread an optional `alias_tokens` through `_parse_joins` / `_parse_join` and the ClickHouse override, and have UPDATE's joins use `UPDATE_ALIAS_TOKENS`. Applying the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "    def _parse_join(\n        self, skip_join_token: bool = False, parse_bracket: bool = False\n    ) -> exp.Join | None:\n        if self._match(TokenType.COMMA):\n            table = self._try_parse(self._parse_table)", "new_string": "    def _parse_join(\n        self,\n        skip_join_token: bool = False,\n        parse_bracket: bool = False,\n        alias_tokens: t.Collection[TokenType] | None = None,\n    ) -> exp.Join | None:\n        if self._match(TokenType.COMMA):\n            table = self._try_parse(lambda: self._parse_table(alias_tokens=alias_tokens))"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, t.Any] = {\"this\": self._parse_table(parse_bracket=parse_bracket)}", "new_string": "        kwargs: dict[str, t.Any] = {\n            \"this\": self._parse_table(parse_bracket=parse_bracket, alias_tokens=alias_tokens)\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "            joins: list | None = list(self._parse_joins())\n\n            if joins and self._match(TokenType.ON):", "new_string": "            joins: list | None = list(self._parse_joins(alias_tokens))\n\n            if joins and self._match(TokenType.ON):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "    def _parse_joins(self) -> t.Iterator[exp.Join]:\n        return iter(self._parse_join, None)", "new_string": "    def _parse_joins(\n        self, alias_tokens: t.Collection[TokenType] | None = None\n    ) -> t.Iterator[exp.Join]:\n        return iter(lambda: self._parse_join(alias_tokens=alias_tokens), None)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        if joins:\n            for join in self._parse_joins():\n                this.append(\"joins\", join)", "new_string": "        if joins:\n            for join in self._parse_joins(alias_tokens):\n                this.append(\"joins\", join)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    def _parse_join(\n        self, skip_join_token: bool = False, parse_bracket: bool = False\n    ) -> exp.Join | None:\n        join = super()._parse_join(skip_join_token=skip_join_token, parse_bracket=True)", "new_string": "    def _parse_join(\n        self,\n        skip_join_token: bool = False,\n        parse_bracket: bool = False,\n        alias_tokens: t.Collection[TokenType] | None = None,\n    ) -> exp.Join | None:\n        join = super()._parse_join(\n            skip_join_token=skip_join_token, parse_bracket=True, alias_tokens=alias_tokens\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\\|TokenType\" sqlglot/parsers/clickhouse.py | head -8; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n      'UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1
…[92 chars elided]…
',\n      'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id',\n      'UPDATE authors, books SET x = 1 WHERE authors.id = books.id',\n      'UPDATE authors JOIN books SET authors.x = 1']\nfor q in qs:\n  try: print(sqlglot.transpile(q, read='mysql', write='mysql')[0])\n  except Exception as e: print('ERR', str(e)[:120])\n\"", "description": "Verify multi-table UPDATE parses and round-trips"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from collections import deque
7:from sqlglot import exp, parser
8:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import Token, TokenType
16:from builtins import type as Type
UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1
UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1
UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id
UPDATE authors, books SET x = 1 WHERE authors.id = books.id
UPDATE authors, books SET authors.x = 1
[assistant] All six forms parse now. The only surprise is `JOIN books SET` (no `ON`) being emitted as `, books`, which is the generator's existing cross-join rendering and is equivalent in MySQL. Next, I'll add tests and run the suite.
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n", "new_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n        self.validate_identity(\n            \"UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()\"\n        )\n        self.validate_identity(\n            \"UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1\"\n        )\n        self.validate_identity(\"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094255-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the full test suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite", "timeout": 600000}
[tool_result] ............................................................................................................................................................................................................................................... [ 21%]
.................................... [ 24%]
.................................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[276 chars elided]…
............................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 53.39s
[assistant] All 1112 tests pass. Running the linter/formatter on the changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/parsers/clickhouse.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/parsers/clickhouse.py tests/dialects/test_mysql.py) 2>&1 | tail -8; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
3 files already formatted
 M sqlglot/parser.py
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_mysql.py
[assistant] Multi-table MySQL `UPDATE` now parses and round-trips, for both comma-separated tables and explicit joins. The full suite passes (1112 tests) and ruff is clean. I haven't committed anything.

**Root cause:** the joined table in an `UPDATE` was parsed with the default table-alias tokens, so `SET` was consumed as the alias of the last table (`books SET`). `UPDATE` already had a set that excludes `SET`, but it only applied to the first table.

**Fix:**
- `sqlglot/parser.py`: `_parse_joins` and `_parse_join` take an optional `alias_tokens`, passed to the joined table and to nested joins. `_parse_t
…[39 chars elided]…
s joins. `UPDATE` already passes `UPDATE_ALIAS_TOKENS`, so its joins now use that set too. Non-UPDATE callers are unchanged, since they pass nothing.
- `sqlglot/parsers/clickhouse.py`: the `_parse_join` override accepts and forwards the new keyword.
- `tests/dialects/test_mysql.py`: identity tests for the comma form, the `INNER JOIN ... ON` form, and aliased comma tables.

**Behavior note:** `UPDATE authors JOIN books SET ...` (a join with no `ON`) is emitted as `UPDATE authors, books SET ...`. That's the generator's existing cross-join rendering, and it's equivalent in MySQL. I left it alone.
