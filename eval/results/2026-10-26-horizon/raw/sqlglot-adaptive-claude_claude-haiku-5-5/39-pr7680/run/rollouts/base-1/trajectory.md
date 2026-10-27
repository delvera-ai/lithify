# trajectory base-1

final message:
MySQL multi-table `UPDATE` now parses and round-trips, for both comma-separated tables and explicit joins. The full test suite passes (1112 passed), and ruff format and lint are clean.

**Root cause:** the target table already excluded `SET` from alias parsing (`UPDATE_ALIAS_TOKENS`), but tables in the join list used the default alias tokens. So in `UPDATE authors, books SET ...`, the `SET` keyword was consumed as the alias of `books`, and parsing failed at `authors`.

**Fix:**
- `sqlglot/parser.py`: `_parse_join`, `_parse_joins` and the `joins=True` path of `_parse_table` now accept `alias_tokens` and pass it to the joined table. `_parse_update` passes `UPDATE_ALIAS_TOKENS` through, so the join tables stop at `SET`.
- `sqlglot/parsers/clickhouse.py`: its `_parse_join` override takes the new parameter and forwards it. Without this, the override would break when the base parser passes the argument.
- No generator change was needed: the existing `_update_from_joins_sql` renders these joins correctly.

**Tests** (`tests/dialects/test_mysql.py`, next to the existing UPDATE identities):
- `UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()`, the example from the issue. `now()` canonicalizes to `NOW()`, so the test uses that form.
- `UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id`
- `UPDATE authors a, books b SET ...`, with the expected output `AS a, AS b`
- `UPDATE authors JOIN books USING (id) SET authors.x = 1, books.y = 2`

The explicit `JOIN ... ON` and `LEFT JOIN ... ON` forms already worked and still do.

Choice for you: I changed the parser's join plumbing rather than special-casing UPDATE. That touches shared code used by SELECT and other statements, although the full suite passes. If you'd prefer a narrower change, the alternative is to parse the UPDATE join list in `_parse_update` itself.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "git status --short && grep -n \"_parse_update\\|def _parse_update\" sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/dialects/mysql.py 2>/dev/null; ls sqlglot/parsers 2>/dev/null | head -50", "description": "Check git status and locate update parsing code"}
[tool_result] sqlglot/parser.py:1109:        TokenType.UPDATE: lambda self: self._parse_update(),
sqlglot/parser.py:3642:    def _parse_update(self) -> exp.Update:
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "offset": 3642, "limit": 40}
[tool_result] 3642	    def _parse_update(self) -> exp.Update:
3643	        hint = self._parse_hint()
3644	        kwargs: dict[str, object] = {
3645	            "hint": hint,
3646	            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647	        }
3648	        while self._curr:
3649	            if self._match(TokenType.SET):
3650	                kwargs["expressions"] = self._parse_csv(self._parse_equality)
3651	            elif self._match(TokenType.RETURNING, advance=Fals
…[952 chars elided]…
pression(exp.Update(**kwargs))
3670	
3671	    def _parse_use(self) -> exp.Use:
3672	        return self.expression(
3673	            exp.Use(
3674	                kind=self._parse_var_from_options(self.USABLES, raise_unmatched=False),
3675	                this=self._parse_table(schema=False),
3676	            )
3677	        )
3678	
3679	    def _parse_uncache(self) -> exp.Uncache:
3680	        if not self._match(TokenType.TABLE):
3681	            self.raise_error("Expecting TABLE after UNCACHE")
[tool_use Bash] {"command": "grep -rn \"class Update\\b\\|class Update(\" sqlglot/expressions/ ; grep -n \"def update_sql\" -A 25 sqlglot/generator.py; grep -n \"UPDATE\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py; grep -n \"multi\\|UPDATE\" tests/dialects/test_mysql.py | grep -i update", "description": "Find Update node, generator, and MySQL update references"}
[tool_result] sqlglot/expressions/dml.py:295:class Update(Expression, DML):
2546:    def update_sql(self, expression: exp.Update) -> str:
2547-        hint = self.sql(expression, "hint")
2548-        this = self.sql(expression, "this")
2549-        join_sql, from_sql = self._update_from_joins_sql(expression)
2550-        set_sql = self.expressions(expression, flat=True)
2551-        where_sql = self.sql(expression, "where")
2552-        returning = self.sql(expression, "returning")
2553-        order = self.s
…[3483 chars elided]…
41:        self.validate_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS MANUAL UPDATE")
1700:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
1705:            "CREATE TRIGGER track_deletes BEFORE DELETE ON orders FOR EACH ROW BEGIN UPDATE statistics SET delete_count = delete_count + 1 WHERE table_name = 'orders' END",
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n          'UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1=1',\n          'UPDATE authors LEFT JOIN books ON a = b SET authors.x = 1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('this'))[:300]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\" 2>&1 | head -40", "description": "Reproduce multi-table UPDATE parse failures"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now()
Table(
  this=Identifier(this=authors, quoted=False),
  joins=[
    Join(
      this=Table(
        this=Identifier(this=books, quoted=False)),
      on=EQ(
        this=Column(
          this=Identifier(this=id, quoted=False),
          table=Identifier(this=authors, quoted=False)),
        express
UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1
Table(
  this=Identifier(this=authors, quoted=False),
  joins=[
    Join(
      this=Table(
        this=Identifier(this=books, quoted=False)),
      side=LEFT,
      on=EQ(
        this=Column(
          this=Identifier(this=a, quoted=False)),
        expression=Column(
          this=Identifier(th
UPDATE authors LEFT JOIN books ON a = b SET authors.x = 1
[tool_use Bash] {"command": "grep -n \"TokenType.COMMA\" sqlglot/parser.py | head -30; grep -n \"def _parse_join(\" -A 12 sqlglot/parser.py; grep -n \"def _update_from_joins_sql\" -A 20 sqlglot/generator.py; grep -n \"def join_sql\" -A 12 sqlglot/generator.py | head -30", "description": "Inspect comma join parsing and join generation"}
[tool_result] 681:        TokenType.COMMAND,
828:        TokenType.COMMAND,
971:            TokenType.COMMA,
1007:    LAMBDA_ARG_TERMINATORS: t.ClassVar[frozenset] = frozenset({TokenType.COMMA, TokenType.R_PAREN})
1670:    OPTYPE_FOLLOW_TOKENS: t.ClassVar = {TokenType.COMMA, TokenType.R_PAREN}
1680:    JSON_KEY_VALUE_SEPARATOR_TOKENS: t.ClassVar = {TokenType.COLON, TokenType.COMMA, TokenType.IS}
1712:    PRIVILEGE_FOLLOW_TOKENS: t.ClassVar = {TokenType.ON, TokenType.COMMA, TokenType.L_PAREN}
2410:            
…[3105 chars elided]…
7:    def join_sql(self, expression: exp.Join) -> str:
2698-        if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
2699-            side = None
2700-        else:
2701-            side = expression.side
2702-
2703-        op_sql = " ".join(
2704-            op
2705-            for op in (
2706-                expression.method,
2707-                "GLOBAL" if expression.args.get("global_") else None,
2708-                side,
2709-                expression.kind,
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('UPDATE authors, books WHERE 1=1', read='mysql').args['this'].args.get('joins')))\nprint(sqlglot.parse_one('SELECT * FROM a, b', read='mysql').sql('mysql'))\n\" 2>&1 | head -30; grep -n \"UPDATE_ALIAS_TOKENS\" -A 3 sqlglot/parser.py | head; grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30", "description": "Check comma-join parse for UPDATE table list"}
[tool_result] [Join(
  this=Table(
    this=Identifier(this=books, quoted=False)))]
SELECT * FROM a, b
795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
796-
797-    TRIM_TYPES: t.ClassVar = {"LEADING", "TRAILING", "BOTH"}
798-
--
3646:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647-        }
3648-        while self._curr:
3649-            if self._match(TokenType.SET):
4737:    def _parse_table(
4738-        self,
4739-        schema
…[1 chars elided]…
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
[tool_use Bash] {"command": "sed -n 4749,4800p sqlglot/parser.py | grep -n \"joins\\|alias\" ; grep -n \"def _parse_joins\\|def _parse_join(\\|def _parse_table_alias\" -A 3 sqlglot/parser.py; sed -n 4414,4440p sqlglot/parser.py; grep -n \"TABLE_ALIAS_TOKENS\" sqlglot/parser.py | head", "description": "Inspect table/join alias parsing paths"}
[tool_result] 10:                # MATCH_CONDITION is a special case because it accepts any alias before it like LIMIT
17:                    if alias := self._parse_table_alias(
18:                        alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
20:                        table.set("alias", alias)
42:            if joins:
43:                for join in self._parse_joins():
44:                    subquery.append("joins", join)
4035:    def _parse_table_alias(
4036-        self, alias_tokens: t.Col
…[1901 chars elided]…
r = TABLE_ALIAS_TOKENS - {TokenType.SET}
1695:    UNNEST_OFFSET_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - SET_OPERATIONS
2192:            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
4046:            self._parse_id_var(any_token=any_token, tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4766:                        alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
4837:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
[tool_use Bash] {"command": "grep -rn \"def _parse_join\\b\\|def _parse_join(\\|def _parse_joins\" sqlglot/ ; grep -n \"_parse_joins(\" sqlglot/parser.py | wc -l; grep -n \"_parse_join(\" sqlglot/parser.py | head -20; sed -n 4780,4800p sqlglot/parser.py; sed -n 4836,4842p sqlglot/parser.py", "description": "Check overrides and call sites for join parsing"}
[tool_result] sqlglot/parser.py:4402:    def _parse_join(
sqlglot/parser.py:5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
sqlglot/parsers/clickhouse.py:665:    def _parse_join(
       6
1060:        exp.Join: lambda self: self._parse_join(),
4402:    def _parse_join(
9825:        join = self._parse_join()

        if unnest := self._parse_unnest():
            return unnest

        if values := self._parse_derived_table_values():
            return values

        if subquery := self._parse_select
…[335 chars elided]…
d self._parse_bracket(None)
        bracket = self.expression(exp.Table(this=bracket)) if bracket else None

        rows_from_tables = (
            self._parse_wrapped_csv(self._parse_table)
            if self._match_text_seq("ROWS", "FROM")

        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
        if alias:
            this.set("alias", alias)

        if self._match(TokenType.INDEXED_BY):
            this.set("indexed", self._parse_table_parts())
[tool_use Bash] {"command": "sed -n 4800,4836p sqlglot/parser.py | grep -n \"joins\" ; grep -n \"_parse_joins()\" sqlglot/parser.py; sed -n 660,680p sqlglot/parsers/clickhouse.py", "description": "Find joins call sites inside table parsing"}
[tool_result] 3657:                    table.set("joins", list(self._parse_joins()) or None)
4118:            for join in self._parse_joins():
4462:            joins: list | None = list(self._parse_joins())
4791:                for join in self._parse_joins():
4863:            for join in self._parse_joins():
        side = self._prev if self._match_set(self.JOIN_SIDES) else None
        kind = self._prev if self._match_set(self.JOIN_KINDS) else None

        return is_global, side or kind, kind_pre or kind


…[189 chars elided]…
arse_bracket=True)
        if join:
            method = join.args.get("method")
            join.set("method", None)
            join.set("global_", method)

            # tbl ARRAY JOIN arr <-- this should be a `Column` reference, not a `Table`
            # https://clickhouse.com/docs/en/sql-reference/statements/select/array-join
            if join.kind == "ARRAY":
                for table in join.find_all(exp.Table):
                    table.replace(table.to_column())

        return join
[tool_use Bash] {"command": "sed -n 4860,4866p sqlglot/parser.py", "description": "View the remaining joins call site in table parsing"}
[tool_result]             this.set("version", self._parse_version())

        if joins:
            for join in self._parse_joins():
                this.append("joins", join)

        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
[tool_use Bash] {"command": "grep -n \"def _try_parse\" -A 6 sqlglot/parser.py; sed -n 2697,2735p sqlglot/generator.py | grep -n \"COMMA\\|, \\|return\" ", "description": "Check _try_parse and comma join rendering"}
[tool_result] 2007:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
2008-        index = self._index
2009-        error_level = self.error_level
2010-        this: T | None = None
2011-
2012-        self.error_level = ErrorLevel.IMMEDIATE
2013-        try:
1:    def join_sql(self, expression: exp.Join) -> str:
2:        if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
19:        match_cond = self.sql(expression, "match_condition")
21:        on_sql = self.sql(expression, "on")
35:            on_sql = self.indent(on_sql, skip_first=True)
[assistant] Root cause: the comma/explicit join tables inside UPDATE are parsed with the default `TABLE_ALIAS_TOKENS`, so `SET` is swallowed as the alias of `books`. The target table already excludes `SET` via `UPDATE_ALIAS_TOKENS`, so I'll thread that alias set through the join parsing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "    def _parse_join(\n        self, skip_join_token: bool = False, parse_bracket: bool = False\n    ) -> exp.Join | None:\n        if self._match(TokenType.COMMA):\n            table = self._try_parse(self._parse_table)", "new_string": "    def _parse_join(\n        self,\n        skip_join_token: bool = False,\n        parse_bracket: bool = False,\n        alias_tokens: t.Collection[TokenType] | None = None,\n    ) -> exp.Join | None:\n        if self._match(TokenType.COMMA):\n            table = self._try_parse(lambda: self._parse_table(alias_tokens=alias_tokens))"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 4418,4424p sqlglot/parser.py", "description": "View the join table parsing lines to edit"}
[tool_result]         method, side, kind = self._parse_join_parts()
        directed = self._match_text_seq("DIRECTED")
        hint = self._prev.text if self._match_texts(self.JOIN_HINTS) else None
        join = self._match(TokenType.JOIN) or (kind and kind.token_type == TokenType.STRAIGHT_JOIN)
        join_comments = self._prev_comments

        if not skip_join_token and not join:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, t.Any] = {\"this\": self._parse_table(parse_bracket=parse_bracket)}\n        if kind and kind.token_type == TokenType.ARRAY and self._match(TokenType.COMMA):\n            kwargs[\"expressions\"
…[104 chars elided]…
  )", "new_string": "        kwargs: dict[str, t.Any] = {\n            \"this\": self._parse_table(parse_bracket=parse_bracket, alias_tokens=alias_tokens)\n        }\n        if kind and kind.token_type == TokenType.ARRAY and self._match(TokenType.COMMA):\n            kwargs[\"expressions\"] = self._parse_csv(\n                lambda: self._parse_table(parse_bracket=parse_bracket)\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\nold=\"\"\"    def _parse_joins(self) -> t.Iterator[exp.Join]:\n        return iter(self._parse_join, None)\n\"\"\"\nnew=\"\"\"    def _parse_joins(\n        self, alias_tokens: t.Collection[TokenType] | None = None\n    ) -> t.Iterator[exp.Join]:\n        return iter(lambda: self._parse_join(alias_tokens=alias_toke
…[899 chars elided]…
] | None = None,\n    ) -> exp.Join | None:\n        join = super()._parse_join(\n            skip_join_token=skip_join_token, parse_bracket=True, alias_tokens=alias_tokens\n        )\n\"\"\")\nopen(p,'w').write(s)\nEOF\ngrep -n \"^import typing\\|^from sqlglot.tokens\\|TokenType\" sqlglot/parsers/clickhouse.py | head -3", "description": "Thread alias tokens through joins and ClickHouse override"}
[tool_result] 3:import typing as t
15:from sqlglot.tokens import Token, TokenType
319:        TokenType.AND,
[assistant] Now the `_parse_update` side: pass the UPDATE alias set into the target table's joins.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n          'UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id',\n          'UPDATE
…[96 chars elided]…
          'UPDATE authors LEFT JOIN books ON a = b SET authors.x = 1',\n          'UPDATE authors a, books b SET a.x = 1',\n          'UPDATE authors JOIN books USING (id) SET authors.x = 1']:\n    try:\n        print(sqlglot.parse_one(s, read='mysql').sql('mysql'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\"", "description": "Test multi-table UPDATE variants after parser change"}
[tool_result] UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1
UPDATE authors LEFT JOIN books ON a = b SET authors.x = 1
UPDATE authors AS a, books AS b SET a.x = 1
UPDATE authors JOIN books USING (id) SET authors.x = 1
[assistant] All variants parse and round-trip. Now I'll add MySQL tests next to the existing UPDATE identities.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "offset": 22, "limit": 6}
[tool_result] 22	        self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
23	        self.validate_identity("CREATE TABLE temp (id SERIAL PRIMARY KEY)")
24	        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
25	        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
26	        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
27	        self.validate_identity("DELETE /*+ MAX_EXECUTION_TIME(1) */ FROM t WHERE a = 1")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n", "new_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n        self.validat
…[111 chars elided]…
      )\n        self.validate_identity(\n            \"UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id\"\n        )\n        self.validate_identity(\n            \"UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.author_id\"\n        )\n        self.validate_identity(\n            \"UPDATE authors JOIN books USING (id) SET authors.x = 1, books.y = 2\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Some of these identities may not match exactly (e.g. aliases get normalized to `AS`). I'll run the MySQL and full test suite to confirm.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30", "description": "Run MySQL dialect tests"}
[tool_result]         self.validate_identity("CREATE TABLE bar (abacate DOUBLE(10, 2) UNSIGNED)")
        self.validate_identity("CREATE TABLE t (id DECIMAL(20, 4) UNSIGNED)")
        self.validate_identity("CREATE TABLE foo (a BIGINT, UNIQUE (b) USING BTREE)")
        self.validate_identity("CREATE TABLE foo (a VARCHAR(32) NOT NULL UNIQUE COMMENT 'test')")
        self.validate_identity("CREATE TABLE foo (id BIGINT)")
        self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
        self.validate_identi
…[856 chars elided]…
a.x = 1 WHERE a.id = b.author_id' != 'UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id'
E   - UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.author_id
E   + UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id
E   ?                +++         +++
=========================== short test summary info ============================
FAILED tests/dialects/test_mysql.py::TestMySQL::test_ddl - AssertionError: 'U...
1 failed, 50 passed, 476 subtests passed in 0.29s
[assistant] As expected, the aliased form canonicalizes to `AS`. I'll fix that test to use the canonical output form.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.author_id\"\n        )", "new_string": "        self.validate_identity(\n            \"UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.author_id\",\n            \"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-065407-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; $PY -m ruff format sqlglot tests/dialects/test_mysql.py 2>&1 | tail -2; $PY -m ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; git status --short", "description": "Run MySQL tests, full suite, and lint/format"}
[tool_result] ...................................................                                        [100%]
51 passed, 486 subtests passed in 0.16s
Command did not complete within its 120s timeout and was moved to the background (ID: bps5yykat). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. It is running now: do not start a second copy while it runs. If it is no longer needed, stop it with TaskStop. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "sleep 100; tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output", "description": "Wait briefly and check full test suite output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Monitor] {"description": "Wait for full test suite to finish", "command": "until grep -qE \"passed|failed|error\" /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output 2>/dev/null; do sleep 5; done; tail -8 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output"}
[tool_result] Monitor started (task bhu16d95d, expires in 5m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot tests/dialects/test_mysql.py 2>&1 | tail -2; $PY -m ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; git status --short; git diff --stat", "description": "Run ruff format and lint on changed files"}
[tool_result] 177 files left unchanged
All checks passed!
 M sqlglot/parser.py
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_mysql.py
 sqlglot/parser.py             | 19 +++++++++++++------
 sqlglot/parsers/clickhouse.py |  9 +++++++--
 tests/dialects/test_mysql.py  | 13 +++++++++++++
 3 files changed, 33 insertions(+), 8 deletions(-)
[assistant] That monitor fired on the MySQL-only run, so the full suite is still going. I'll check its output file directly.
[tool_use Bash] {"command": "sleep 5; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-065407-mysql-dialect-multi-table-update-base-1/5ee7fc01-c0f6-4700-a846-94dbefd1e3ee/tasks/bps5yykat.output | tail -8", "description": "Check full test suite output so far"}
[tool_result] 1112 passed, 18136 subtests passed in 56.60s
177 files left unchanged
All checks passed!
 M sqlglot/parser.py
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_mysql.py

[exited with code 0]
[assistant] MySQL multi-table `UPDATE` now parses and round-trips, for both comma-separated tables and explicit joins. The full test suite passes (1112 passed), and ruff format and lint are clean.

**Root cause:** the target table already excluded `SET` from alias parsing (`UPDATE_ALIAS_TOKENS`), but tables in the join list used the default alias tokens. So in `UPDATE authors, books SET ...`, the `SET` keyword was consumed as the alias of `books`, and parsing failed at `authors`.

**Fix:**
- `sqlglot/parser.py`: `_parse_join`, `_parse_joins` and the `joins=True` path of `_parse_table` now accept `alias_to
…[680 chars elided]…
TE authors, books SET authors.x = 1 WHERE authors.id = books.author_id`
- `UPDATE authors a, books b SET ...`, with the expected output `AS a, AS b`
- `UPDATE authors JOIN books USING (id) SET authors.x = 1, books.y = 2`

The explicit `JOIN ... ON` and `LEFT JOIN ... ON` forms already worked and still do.

Choice for you: I changed the parser's join plumbing rather than special-casing UPDATE. That touches shared code used by SELECT and other statements, although the full suite passes. If you'd prefer a narrower change, the alternative is to parse the UPDATE join list in `_parse_update` itself.
