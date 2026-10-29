# trajectory base-1

final message:
Multi-table MySQL `UPDATE` now parses and round-trips, for comma-separated tables and for explicit `JOIN ... ON` joins. The full suite passes (1112 tests) and ruff is clean. The changes are uncommitted in the worktree.

**The cause:** `_parse_update` parsed the target with `_parse_table(joins=True)`. The comma branch of `_parse_join` then parsed `books` with the default alias tokens, which include `SET`, so `SET` was taken as an alias for `books`.

**The fix** (`sqlglot/parser.py`, `_parse_update`): the target table is parsed without joins, and the following comma-separated tables and joins are parsed in a loop. Comma-separated tables use `UPDATE_ALIAS_TOKENS`, which excludes `SET`. Explicit joins still go through `_parse_join`, and the existing `UPDATE foo JOIN bar ON TRUE` behavior is unchanged. Nothing in the MySQL generator needed changing.

**Tests** (`tests/dialects/test_mysql.py`) added three round-trip cases:
- `UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()`
- `UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id`
- `UPDATE a, b JOIN c ON b.x = c.x, d SET a.x = 1, d.y = 2`

**Known gap:** a join without `ON`, such as `UPDATE a CROSS JOIN b SET ...`, still fails to parse. The same `SET`-as-alias problem applies there. Fixing it means threading an alias-token argument through `_parse_join`, which ClickHouse overrides, so I left it out of this change. I can take it on as a follow-up if you want it covered.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"_parse_update\\|UPDATE\" sqlglot/parser.py | head -40 && grep -n \"def _parse_update\\|UPDATE\\|Update\" sqlglot/dialects/mysql.py | head -30 && grep -n \"class Update\" -A 25 sqlglot/expressions.py | head -40"}
[tool_result] ok22 matches in 13 files:

1109:0:lambda self: self._parse_update(),
1584:0:("NOTHING", "UPDATE"),
1738:0:lambda self: self._parse_analyze_histogram(),
3511:0:
3642:0:
3646:0:self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
5595:0:
5603:0:
7446:0:
795:0:t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
8950:0:
9074:0:
sqlglot/parser.py:653:TokenType.UPDATE,
sqlglot/parser.py:756:TokenType.UPDATE,
sqlglot/parser.py:1385:self._match(TokenType.UPDATE)
sqlglot/parser.py:1583:**d
…[87 chars elided]…
arser.py:2645:self.raise_error("Expected trigger event (INSERT, UPDATE, DELETE, TRUNCATE)")
sqlglot/parser.py:2649:if event_type == "UPDATE" and self._match_text_seq("OF")
sqlglot/parser.py:7447:self.raise_error("Expected DELETE or UPDATE")
sqlglot/parser.py:8952:this = "UPDATE"
sqlglot/parser.py:8954:this = "UPDATE SET DANGLING TO NULL"
sqlglot/parser.py:9008:TokenType.UPDATE, advance=False
0 matches for 'def _parse_update\|UPDATE\|Update'
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 3630,3680p sqlglot/parser.py && grep -n \"def _parse_update\" -A 40 sqlglot/parser.py | head -60 && grep -n \"class Update(\" -A 25 sqlglot/expressions/*.py | head -40"}
[tool_result]                 tables=tables,
                this=self._match(TokenType.FROM) and self._parse_table(joins=True),
                using=self._match(TokenType.USING)
                and self._parse_csv(lambda: self._parse_table(joins=True)),
                cluster=self._match(TokenType.ON) and self._parse_on_property(),
                where=self._parse_where(),
                returning=returning or self._parse_returning(),
                order=self._parse_order(),
                limit=self.
…[4613 chars elided]…
-        dialect: DialectType = None,
sqlglot/expressions/dml.py-313-        copy: bool = True,
sqlglot/expressions/dml.py-314-        **opts: Unpack[ParserNoDialectArgs],
sqlglot/expressions/dml.py-315-    ) -> Update:
sqlglot/expressions/dml.py-316-        """
sqlglot/expressions/dml.py-317-        Set the table to update.
sqlglot/expressions/dml.py-318-
sqlglot/expressions/dml.py-319-        Example:
sqlglot/expressions/dml.py-320-            >>> Update().table("my_table").set_("x = 1").sql()
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()', 'UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1=1', 'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id', 'UPDATE t1 LEFT JOIN t2 ON t1.a=t2.a SET t1.x=1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\"; grep -n \"UPDATE\" tests/dialects/test_mysql.py | head -30; grep -rn \"def update_sql\\|Update\" sqlglot/generator.py | head"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
27 matches in 4 files:

1087:0:"SELECT a FROM tbl FOR UPDATE",
1088:0:"SELECT a FROM tbl FOR UPDATE",
1089:0:"SELECT a FROM tbl FOR UPDATE",
tests/dialects/test_mysql.py:24:self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIM...
tests/dialects/test_mysql.py:25:self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
tests/dialects/t
…[2406 chars elided]…
224:        exp.OnUpdateColumnConstraint: lambda self, e: f"ON UPDATE {self.sql(e, 'this')}",
sqlglot/generator.py:796:        exp.Update,
sqlglot/generator.py:2514:    def _update_from_joins_sql(self, expression: exp.Update) -> tuple[str, str]:
sqlglot/generator.py:2546:    def update_sql(self, expression: exp.Update) -> str:
sqlglot/generator.py:4613:        elif isinstance(then_expression, exp.Update):
sqlglot/generator.py:4622:        if isinstance(then_expression, (exp.Insert, exp.Update)):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; sed -n 240,250p tests/dialects/test_mysql.py; sed -n 2514,2580p sqlglot/generator.py; PYTHONPATH=. $PY -I -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()', 'UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1=1', 'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id', 'UPDATE t1 LEFT JOIN t2 ON t1.a=t2.a SET t1.x=1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\""}
[tool_result ERROR] Exit code 1
        self.validate_identity(
            "ALTER TABLE t RENAME KEY a TO b",
            "ALTER TABLE t RENAME INDEX a TO b",
        )
        self.validate_identity(
            "UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id"
        )

        # PARTITION BY RANGE - simple column
        self.validate_identity(
            "CREATE TABLE t (id INT, created_at DATE) PARTITION BY RANGE (id) (PARTITION p0 VALUES LESS THAN (10), PARTITION p1 VALUES LESS THAN (20
…[2844 chars elided]…
 f"VALUES{self.seg('')}{args}"
            values = (
                f"({values})"
                if self.WRAP_DERIVED_VALUES
                and (alias or isinstance(expression.parent, (exp.From, exp.Table)))
                else values
            )
            values = self.query_modifiers(expression, values)
            return f"{values} AS {alias}" if alias else values

Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()', 'UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1=1', 'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id', 'UPDATE t1 LEFT JOIN t2 ON t1.a=t2.a SET t1.x=1', 'SELECT * FROM a, b']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)[:400]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\"; $PY -c \"import sqlglot;print(sqlglot.__file__)\""}
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
          exp
…[921 chars elided]…
s=t1, quoted=False)),
          expression=Column(
            this=Identifier(this=a, quoted=False
UPDATE t1 LEFT JOIN t2 ON t1.a = t2.a SET t1.x = 1
Select(
  expressions=[
    Star()],
  from_=From(
    this=Table(
      this=Identifier(this=a, quoted=False))),
  joins=[
    Join(
      this=Table(
        this=Identifier(this=b, quoted=False)))])
SELECT * FROM a, b
~/.cache/lithify/work/repo-6e430de19896/20261029-193631-mysql-dialect-multi-table-update/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "grep -n \"def _parse_join(\" -A 30 sqlglot/parser.py | grep -n \"COMMA\" ; grep -n \"def _parse_joins\" -A 8 sqlglot/parser.py; grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30; grep -n \"def join_sql\" -A 40 sqlglot/generator.py | grep -n \"COMMA\\|, \\|sep\" | head"}
[tool_result] 4:4405-        if self._match(TokenType.COMMA):
5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
5060-        return iter(self._parse_join, None)
5061-
5062-    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
5063-        if not self._match(TokenType.INTO):
5064-            return None
5065-
5066-        return self.expression(
5067-            exp.UnpivotColumns(
4737:    def _parse_table(
4738-        self,
4739-        schema: bool = False,
4740-        joins: bool = Fa
…[296 chars elided]…
ema and not is_db_reference and not consume_pipe and not joins:
4748-            index = self._index
4749-            table = self._parse_table_parts(fast=True)
1:2697:    def join_sql(self, expression: exp.Join) -> str:
2:2698-        if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
19:2715-        match_cond = self.sql(expression, "match_condition")
21:2717-        on_sql = self.sql(expression, "on")
35:2731-            on_sql = self.indent(on_sql, skip_first=True)
[tool_use Bash] {"command": "sed -n 4395,4415p sqlglot/parser.py; sed -n 2697,2760p sqlglot/generator.py"}
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
…[2241 chars elided]…
   args = self.expressions(expression, flat=True)
        args = f"({args})" if wrap and len(args.split(",")) > 1 else args
        return f"{args} {arrow_sep} {self.sql(expression, 'this')}"

    def lateral_op(self, expression: exp.Lateral) -> str:
        cross_apply = expression.args.get("cross_apply")

        # https://www.mssqltips.com/sqlservertip/1958/sql-server-cross-apply-and-outer-apply/
        if cross_apply is True:
            op = "INNER JOIN "
        elif cross_apply is False:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET x = 1', 'UPDATE authors, books SET authors.x = 1', 'UPDATE authors, books SET books.x = 1', 'UPDATE authors, books b SET b.x = 1', 'UPDATE authors a, books SET a.x = 1', 'UPDATE a, b SET a.x = 1','UPDATE a SET a.x = 1']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print('OK', e.sql('mysql'))\n    except Exception as ex: print('ERR', s, str(ex)[:80].replace(chr(10),' '))\n\"; sed -n 4749,4800p sqlglot/parser.py"}
[tool_result] ERR UPDATE authors, books SET x = 1 Invalid expression / Unexpected token. Line 1, Col: 27.   UPDATE authors, books 
ERR UPDATE authors, books SET authors.x = 1 Invalid expression / Unexpected token. Line 1, Col: 33.   UPDATE authors, books 
ERR UPDATE authors, books SET books.x = 1 Invalid expression / Unexpected token. Line 1, Col: 31.   UPDATE authors, books 
OK UPDATE authors, books AS b SET b.x = 1
ERR UPDATE authors a, books SET a.x = 1 Invalid expression / Unexpected token. Line 1, Col: 2
…[1626 chars elided]…
pivots"):
                subquery.set("pivots", self._parse_pivots())
            if joins:
                for join in self._parse_joins():
                    subquery.append("joins", join)
            return subquery

        bracket = parse_bracket and self._parse_bracket(None)
        bracket = self.expression(exp.Table(this=bracket)) if bracket else None

        rows_from_tables = (
            self._parse_wrapped_csv(self._parse_table)
            if self._match_text_seq("ROWS", "FROM")
[tool_use Bash] {"command": "sed -n 4415,4470p sqlglot/parser.py; grep -n \"UPDATE_ALIAS_TOKENS\\|TABLE_ALIAS_TOKENS =\" sqlglot/parser.py sqlglot/dialects/*.py | head"}
[tool_result]         method, side, kind = self._parse_join_parts()
        directed = self._match_text_seq("DIRECTED")
        hint = self._prev.text if self._match_texts(self.JOIN_HINTS) else None
        join = self._match(TokenType.JOIN) or (kind and kind.token_type == TokenType.STRAIGHT_JOIN)
        join_comments = self._prev_comments

        if not skip_join_token and not join:
            self._retreat(index)
            kind = None
            method = None
            side = None

        outer_app
…[1522 chars elided]…
atch(TokenType.ON):
                kwargs["on"] = self._parse_disjunction()
            elif joins and self._match(TokenType.USING):
                kwargs["using"] = self._parse_using_identifiers()
            else:
                joins = None
                self._retreat(index)
2 matches in 1 files:

sqlglot/parser.py:795:UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
sqlglot/parser.py:3646:"this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
[tool_use Bash] {"command": "awk 'NR>=4800 && NR<=4900 && /joins/ {print NR\": \"$0}' sqlglot/parser.py; grep -n \"class Subquery\" -A 12 sqlglot/expressions/query.py | grep -n joins"}
[tool_result] 4862:         if joins:
4863:             for join in self._parse_joins():
4864:                 this.append("joins", join)
[tool_use Bash] {"command": "sed -n 4855,4870p sqlglot/parser.py; grep -rn \"class Subquery(\" -A 12 sqlglot/expressions/ | head -20"}
[tool_result]         if not self.dialect.ALIAS_POST_TABLESAMPLE:
            this.set("sample", self._parse_table_sample())

        if not self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())

        if joins:
            for join in self._parse_joins():
                this.append("joins", join)

        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
            this.set("ordinality", True)
            this.set("alias", self._parse_table_alias())

        ret
…[318 chars elided]…
alias": False,
sqlglot/expressions/query.py-1672-        "with_": False,
sqlglot/expressions/query.py-1673-        **QUERY_MODIFIERS,
sqlglot/expressions/query.py-1674-    }
sqlglot/expressions/query.py-1675-
sqlglot/expressions/query.py-1676-    def unnest(self) -> Expr:
sqlglot/expressions/query.py-1677-        """Returns the first non subquery."""
sqlglot/expressions/query.py-1678-        expression: Expr = self
sqlglot/expressions/query.py-1679-        while isinstance(expression, Subquery):
[assistant] The root cause: `_parse_update` parses the target with `_parse_table(joins=True)`, and the comma branch of `_parse_join` parses the next table with the default alias tokens, which include `SET`. So `books SET` reads `SET` as an alias. I'll parse the update target and its joins in `_parse_update`, using `UPDATE_ALIAS_TOKENS` for comma-separated tables.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193631-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        hint = self._parse_hint()\n        kwargs: dict[str, object] = {\n            \"hint\": hint,\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }\n        whil
…[378 chars elided]…
he last table\n            if self._match(TokenType.COMMA):\n                join = self.expression(\n                    exp.Join(this=self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS))\n                )\n            else:\n                join = self._parse_join()\n\n            if not join:\n                break\n\n            this.append(\"joins\", join)\n\n        while self._curr:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193631-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()', 'UPDATE authors, books SET x = 1', 'UPDATE authors a, books b SET a.x = 1 WHERE a.id = b.id', 'UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 
…[77 chars elided]…
 JOIN t2 ON t1.a=t2.a SET t1.x=1', 'UPDATE a CROSS JOIN b SET a.x = 1', 'UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id', 'UPDATE items SET items.price = 0 WHERE items.id >= 5 ORDER BY items.id LIMIT 10']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print('OK', e.sql('mysql'))\n    except Exception as ex: print('ERR', s, str(ex)[:120].replace(chr(10),' '))\n\""}
[tool_result] OK UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
OK UPDATE authors, books SET x = 1
OK UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id
OK UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2 WHERE 1 = 1
OK UPDATE a, b JOIN c ON b.x = c.x, d SET a.x = 1
OK UPDATE t1 LEFT JOIN t2 ON t1.a = t2.a SET t1.x = 1
ERR UPDATE a CROSS JOIN b SET a.x = 1 Invalid expression / Unexpected token. Line 1, Col: 27.   UPDATE a CROSS JOIN b SET [4ma[0m.x = 1
OK UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id
OK UPDATE items SET items.price = 0 WHERE items.id >= 5 ORDER BY items.id LIMIT 10
[assistant] Explicit `CROSS JOIN` / `JOIN` without `ON` hits the same alias problem, since `_parse_join` parses its table with default alias tokens. MySQL allows these forms in multi-table UPDATE, so I'll thread the alias tokens through `_parse_join` rather than special-casing the comma.
[tool_use Bash] {"command": "grep -rn \"_parse_join(\" sqlglot/ | head -30"}
[tool_result] sqlglot/parsers/clickhouse.py:665:    def _parse_join(
sqlglot/parsers/clickhouse.py:668:        join = super()._parse_join(skip_join_token=skip_join_token, parse_bracket=True)
sqlglot/parser.py:1060:        exp.Join: lambda self: self._parse_join(),
sqlglot/parser.py:3654:                join = self._parse_join()
sqlglot/parser.py:4415:    def _parse_join(
sqlglot/parser.py:9838:        join = self._parse_join()
[tool_use Bash] {"command": "sed -n 660,680p sqlglot/parsers/clickhouse.py; sed -n 4415,4418p sqlglot/parser.py"}
[tool_result]         side = self._prev if self._match_set(self.JOIN_SIDES) else None
        kind = self._prev if self._match_set(self.JOIN_KINDS) else None

        return is_global, side or kind, kind_pre or kind

    def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        join = super()._parse_join(skip_join_token=skip_join_token, parse_bracket=True)
        if join:
            method = join.args.get("method")
            join.set("metho
…[53 chars elided]…
          # tbl ARRAY JOIN arr <-- this should be a `Column` reference, not a `Table`
            # https://clickhouse.com/docs/en/sql-reference/statements/select/array-join
            if join.kind == "ARRAY":
                for table in join.find_all(exp.Table):
                    table.replace(table.to_column())

        return join
    def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
[assistant] I'll leave `_parse_join`'s signature alone: ClickHouse overrides it, and threading a kwarg through would widen the change. Explicit joins keep the existing path, so only `CROSS JOIN`/`JOIN` without `ON` stays a known gap, which I'll report. Next, tests in the MySQL test file, then the full suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193631-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id\"\n        )\n", "new_string": "        self.validate_identity(\n            \"UPDATE foo JOI
…[52 chars elided]…
d\"\n        )\n        self.validate_identity(\n            \"UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()\"\n        )\n        self.validate_identity(\n            \"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id\",\n        )\n        self.validate_identity(\n            \"UPDATE a, b JOIN c ON b.x = c.x, d SET a.x = 1, d.y = 2\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193631-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] ...................................................                                        [100%]
51 passed, 486 subtests passed in 0.27s
............................................................................................................................................................................................................................................... [ 21%]
.................................... [ 24%]
.................................................... [ 29%]
...........
…[414 chars elided]…
............................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 45.89s
[assistant] The full suite passes (1112 tests). Now lint and format checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -8; git diff --stat"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
sqlglot/parser.py            | 21 +++++++++++++++++----
 tests/dialects/test_mysql.py |  9 +++++++++
 2 files changed, 26 insertions(+), 4 deletions(-)
[assistant] Multi-table MySQL `UPDATE` now parses and round-trips, for comma-separated tables and for explicit `JOIN ... ON` joins. The full suite passes (1112 tests) and ruff is clean. The changes are uncommitted in the worktree.

**The cause:** `_parse_update` parsed the target with `_parse_table(joins=True)`. The comma branch of `_parse_join` then parsed `books` with the default alias tokens, which include `SET`, so `SET` was taken as an alias for `books`.

**The fix** (`sqlglot/parser.py`, `_parse_update`): the target table is parsed without joins, and the following comma-separated tables and joins ar
…[276 chars elided]…
dialects/test_mysql.py`) added three round-trip cases:
- `UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()`
- `UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.id`
- `UPDATE a, b JOIN c ON b.x = c.x, d SET a.x = 1, d.y = 2`

**Known gap:** a join without `ON`, such as `UPDATE a CROSS JOIN b SET ...`, still fails to parse. The same `SET`-as-alias problem applies there. Fixing it means threading an alias-token argument through `_parse_join`, which ClickHouse overrides, so I left it out of this change. I can take it on as a follow-up if you want it covered.
