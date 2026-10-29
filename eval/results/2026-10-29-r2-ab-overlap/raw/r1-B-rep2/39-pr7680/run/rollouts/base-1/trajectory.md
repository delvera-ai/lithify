# trajectory base-1

final message:
MySQL's comma-separated multi-table `UPDATE` now parses and round-trips. The reported statement is fixed, and the full suite passes with exit 0 (1112 passed).

**Cause:** `_parse_update` in `sqlglot/parser.py` parsed the target table, but comma-separated tables went through the generic join path, which uses the default alias tokens. Those include `SET`, so `books SET` read `SET` as an alias and then failed on `authors`. Explicit `JOIN`s worked because they have an `ON` clause.

**Fix:** `_parse_update` now parses the target with `UPDATE_ALIAS_TOKENS`. It then loops over comma-separated tables (also parsed with `UPDATE_ALIAS_TOKENS`) and explicit joins (via `_parse_join`), attaching both to the target table as before. The `SET`-excluded alias set is what the single-table form already used.

**Tests:** I added three `validate_identity` cases to the existing MySQL UPDATE block in `tests/dialects/test_mysql.py`, covering the reported statement, an aliased comma form with `WHERE`, and a comma form followed by a `LEFT JOIN`. The MySQL file passes (51 tests), and ruff check and format are clean on both files.

**Probe results after the fix:** every variant reads OK, including:
- `UPDATE authors, books SET ... WHERE ...`
- `UPDATE authors AS a, books AS b SET ...`
- `UPDATE authors, books LEFT JOIN x ON ... SET ...`
- `UPDATE items, orders SET ... ORDER BY ... LIMIT 10`
- the existing explicit-JOIN and single-table forms

**Things to know:**
- The fix is in the generic `_parse_update`, not a MySQL-only override, so other dialects now also accept `UPDATE a, b SET ...`. Postgres and others use `FROM` for this, so the change is permissive there, not wrong. Say if you'd rather scope it to MySQL.
- The probe script's `-I` flag ignores `PYTHONPATH`, so `probe_parse.py` fails with `No module named 'sqlglot'` under the interpreter in `memory.md`. I ran it without `-I` and with `PYTHONPATH` set to the worktree. That is a harness issue, not part of this fix.
- No other parse failures surfaced in the variants I probed.

## events
[tool_use Skill] {"skill": "parse-failure-triage", "args": "MySQL multi-table UPDATE fails to parse: UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()"}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/.claude/skills/parse-failure-triage

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: inpu
…[644 chars elided]…
ng the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.


ARGUMENTS: MySQL multi-table UPDATE fails to parse: UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()
[tool_use Bash] {"command": "grep -n \"UPDATE\" sqlglot/dialects/mysql.py | head -30; grep -n \"def _parse_update\\|UPDATE:\\|def _parse_table_parts\\|def _parse_from(\\|def _parse_join(\" sqlglot/parser.py; ls .lithify/harness/scripts/"}
[tool_result] 0 matches for 'UPDATE'
rg: regex parse error:
    (?:def _parse_update|UPDATE:|def _parse_table_parts|def _parse_from(|def _parse_join()
                                                                       ^
error: unclosed group
0 matches for 'def _parse_update\|UPDATE:\|def _parse_table_parts\|def _parse_from(\|def _parse_join('
probe_parse.py  2.2K
[tool_use Bash] {"command": "mkdir -p /tmp/mysql-upd-probe && printf '%s\\n' \"UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()\" \"UPDATE authors SET deleted_at = now()\" \"UPDATE authors AS a JOIN books AS b ON a.id = b.author_id SET a.deleted_at = now(), b.deleted_at = now()\" \"UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1 WHERE books.y = 2\" \
…[160 chars elided]…
\" > /tmp/mysql-upd-probe/stmts.sql && <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read mysql < /tmp/mysql-upd-probe/stmts.sql; echo \"---\"; rg -n \"def _parse_update|\\\"UPDATE\\\"|TokenType.UPDATE\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -20", "description": "Probe reported MySQL multi-table UPDATE variants"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
---
17 matches in 1 files:

sqlglot/parser.py:653:TokenType.UPDATE,
sqlglot/parser.py:756:TokenType.UPDATE,
sqlglot/parser.py:1109:TokenType.UPDATE: lambda self: self._parse_update(),
sqlglot/parser.py:1385:self._match(
…[411 chars elided]…
arser.py:3642:def _parse_update(self) -> exp.Update:
sqlglot/parser.py:5595:if self._match_text_seq("FOR", "UPDATE"):
sqlglot/parser.py:5603:elif self._match_text_seq("FOR", "NO", "KEY", "UPDATE"):
sqlglot/parser.py:7446:if not self._match_set((TokenType.DELETE, TokenType.UPDATE)):
sqlglot/parser.py:8950:if self._match_text_seq("REF", "UPDATE"):
sqlglot/parser.py:8952:this = "UPDATE"
sqlglot/parser.py:9008:TokenType.UPDATE, advance=False
sqlglot/parser.py:9074:elif self._match(TokenType.UPDATE):
[tool_use Bash] {"command": "sed -n 1,30p .lithify/harness/scripts/probe_parse.py; ls .lithify/harness/; cat .lithify/harness/memory.md 2>/dev/null | head -30", "description": "Inspect probe script and harness memory notes"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[287 chars elided]…
s.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

scripts/
skills/
guardrails.md  147B
memory.md  153B
system.md  260B
tool_guidance.md  535B
- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sys; print(sys.path[:3])\"; PYTHONPATH=$PWD $PY -I .lithify/harness/scripts/probe_parse.py --read mysql < /tmp/mysql-upd-probe/stmts.sql; echo \"exit=$?\"", "description": "Run probe with repo on PYTHONPATH"}
[tool_result] ['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12']
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit=1
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read mysql < /tmp/mysql-upd-probe/stmts.sql; echo \"exit=$?\"", "description": "Probe MySQL UPDATE variants with repo on path"}
[tool_result] ERR       UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 33.
OK        UPDATE authors SET deleted_at = now()
          UPDATE authors SET deleted_at = NOW()
OK        UPDATE authors AS a JOIN books AS b ON a.id = b.author_id SET a.deleted_at = now(), b.deleted_at = now()
          UPDATE authors AS a JOIN books AS b ON a.id = b.author_id SET a.deleted_at = NOW(), b.deleted_at = NOW()
OK     
…[64 chars elided]…
id SET authors.x = 1 WHERE books.y = 2
          UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1 WHERE books.y = 2
ERR       UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 33.
OK        UPDATE authors LEFT JOIN books ON authors.id = books.author_id SET authors.x = 1
          UPDATE authors LEFT JOIN books ON authors.id = books.author_id SET authors.x = 1
exit=1
[assistant] Reproduced: the comma-separated form fails at the comma, while explicit JOINs already parse. Now the parser.
[tool_use Bash] {"command": "sed -n 3642,3670p sqlglot/parser.py; rg -n \"class Update\\b|class Update\\(\" sqlglot/expressions*.py sqlglot/*/*.py 2>/dev/null; rg -n \"class Update\\(\" sqlglot -r . | head; rg -n \"def update_sql\" -A25 sqlglot/generator.py", "description": "Read _parse_update and Update generator"}
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
…[2062 chars elided]…
 values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
2565-        values_as_table = values_as_table and self.VALUES_AS_TABLE
2566-
2567-        # The VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2568-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2569-            args = self.expressions(expression)
2570-            alias = self.sql(expression, "alias")
2571-            values = f"VALUES{self.seg('')}{args}"
[tool_use Bash] {"command": "rg -n \"def _update_from_joins_sql\" -A22 sqlglot/generator.py; rg -n \"COMMA\" sqlglot/parser.py | head -20; rg -n \"def _parse_join\\b|def _parse_join\\(\" -A12 sqlglot/parser.py | head -30; rg -n \"_parse_update|UPDATE\" sqlglot/dialects/mysql.py", "description": "Inspect update join generation and comma join parsing"}
[tool_result ERROR] Exit code 1
2514:    def _update_from_joins_sql(self, expression: exp.Update) -> tuple[str, str]:
2515-        """
2516-        Returns (join_sql, from_sql) for UPDATE statements.
2517-        - join_sql: placed after UPDATE table, before SET
2518-        - from_sql: placed after SET clause (standard position)
2519-        Dialects like MySQL need to convert FROM to JOIN syntax.
2520-        """
2521-        if self.UPDATE_STATEMENT_SUPPORTS_FROM or not (from_expr := expression.args.get("from_")
…[770 chars elided]…
e)
46 matches in 27 files:

1007:0:t.ClassVar[frozenset] = frozenset({TokenType.COMMA, TokenType.R_PAREN})
1670:0:t.ClassVar = {TokenType.COMMA, TokenType.R_PAREN}
1680:0:t.ClassVar = {TokenType.COLON, TokenType.COMMA, TokenType.IS}
1712:0:t.ClassVar = {TokenType.ON, TokenType.COMMA, TokenType.L_PAREN}
1781:0:t.ClassVar = True
2279:0:
2410:0:
2580:0:
3976:0:
4405:0:
4434:0:
5137:0:
5507:0:
6257:0:
6778:0:
7658:0:
7693:0:
7729:0:
grep: parentheses not balanced
0 matches for '_parse_update|UPDATE'
[tool_use Bash] {"command": "sed -n 2534,2545p sqlglot/generator.py; rg -n \"UPDATE_STATEMENT_SUPPORTS_FROM\" sqlglot | head; rg -n \"def _parse_join\" -A14 sqlglot/parser.py | head -40; rg -n \"_parse_update|Update\" sqlglot/dialects/mysql.py", "description": "Read rest of update join generator and join parsing"}
[tool_result ERROR] Exit code 1
        table = from_expr.this
        if nested_joins := table.args.get("joins", []):
            table.set("joins", None)

        join_sql = self.sql(exp.Join(this=table, on=exp.true()))
        for nested in nested_joins:
            if not nested.args.get("on") and not nested.args.get("using"):
                nested.set("on", exp.true())
            join_sql += self.sql(nested)

        return (join_sql, "")

5 matches in 4 files:

sqlglot/generator.py:601:UPDATE_STATEMENT_SUPP
…[1515 chars elided]…

4413-
4414-        index = self._index
4415-        method, side, kind = self._parse_join_parts()
4416-        directed = self._match_text_seq("DIRECTED")
--
5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
5060-        return iter(self._parse_join, None)
5061-
5062-    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
5063-        if not self._match(TokenType.INTO):
5064-            return None
5065-
5066-        return self.expression(
0 matches for '_parse_update|Update'
[tool_use Bash] {"command": "rg -n \"def _parse_table\\(\" -A6 sqlglot/parser.py; rg -n \"joins: bool|if joins\" -A4 sqlglot/parser.py | head -40; rg -n \"_parse_table\\(joins=True|this\\.set\\(\\\"joins\\\"|\\\"joins\\\"\" sqlglot/parser.py | head -20", "description": "Locate _parse_table joins handling"}
[tool_result] grep: parentheses not balanced
9 matches in 4 files:

3633:0:self._parse_table(joins=True)),
3646:0:self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
4087:0:
sqlglot/parser.py:3631:this=self._match(TokenType.FROM) and self._parse_table(joins=True),
sqlglot/parser.py:3657:table.set("joins", list(self._parse_joins()) or None)
sqlglot/parser.py:4119:this.append("joins", join)
sqlglot/parser.py:4472:kwargs["this"].set("joins", joins if joins else None)
sqlglot/parser.py:4792:subquery.append("joins", join)
sqlglot/parser.py:4864:this.append("joins", join)
[tool_use Bash] {"command": "sed -n 4105,4125p sqlglot/parser.py; sed -n 4860,4868p sqlglot/parser.py", "description": "Read join attachment logic in table parsing"}
[tool_result]             refs.add(normalized_table.alias_or_name)

        return this

    @t.overload
    def _parse_query_modifiers(self, this: E) -> E: ...

    @t.overload
    def _parse_query_modifiers(self, this: None) -> None: ...

    def _parse_query_modifiers(self, this):
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for lateral in iter(self._parse_lateral, None):
                this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
            this.set("version", self._parse_version())

        if joins:
            for join in self._parse_joins():
                this.append("joins", join)

        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
            this.set("ordinality", True)
            this.set("alias", self._parse_table_alias())
[assistant] The generic join parser already handles comma joins, so I need to see where the comma form actually breaks. Checking the parsed tree directly:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['mysql','']:\n    try:\n        print(repr(sqlglot.parse_one('UPDATE authors, books SET authors.x = 1', read=d)))\n    except Exception as e: print(d, 'ERR', str(e)[:200])\nprint(repr(sqlglot.parse_one('UPDATE authors, books SET x = 1', read='')))\n\" 2>&1 | head -40", "description": "Inspect parse tree for comma UPDATE"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 8, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/sqlglot/dialects/dialect.py", line 1119, in parse
    return self.p
…[925 chars elided]…
lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", line 1993, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 27.
  UPDATE authors, books SET [4mx[0m = 1
mysql ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.x = 1
 ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.x = 1
[assistant] Parsing stops at `SET`: the comma-join's table parse takes `SET` as a table alias. Checking the alias token sets:
[tool_use Bash] {"command": "rg -n \"UPDATE_ALIAS_TOKENS\" -A3 sqlglot/parser.py | head -20; rg -n \"UPDATE_ALIAS_TOKENS|class Parser\" sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py 2>/dev/null; ls sqlglot/parsers 2>/dev/null | head -50 | tr '\\n' ' '", "description": "Check UPDATE alias token definition and MySQL parser location"}
[tool_result] 795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
796-
797-    TRIM_TYPES: t.ClassVar = {"LEADING", "TRAILING", "BOTH"}
798-
--
3646:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647-        }
3648-        while self._curr:
3649-            if self._match(TokenType.SET):
0 matches for 'UPDATE_ALIAS_TOKENS|class Parser'
__init__.py  1B athena.py  2.3K base.py  582B bigquery.py  28.4K clickhouse.py  32.7K databricks.py  1.7K doris.py  5.0K dremio.py  3.8K drill.py  662B druid.py  108B duckdb.py  15.4K dune.py  124B exasol.py  6.5K fabric.py  1.3K hive.py  11.0K materialize.py  1.3K mysql.py  24.1K oracle.py  8.6K postgres.py  12.9K presto.py  5.3K prql.py  6.9K redshift.py  5.8K risingwave.py  2.2K singlestore.py  10.4K snowflake.py  52.4K solr.py  353B spark.py  5.2K spark2.py  4.2K sqlite.py  3.5K starrocks.py  6.4K tableau.py  507B teradata.py  7.4K trino.py  2.0K tsql.py  26.4K
[assistant] The cause: `UPDATE_ALIAS_TOKENS` excludes `SET`, but the comma-join path inside `_parse_join` uses the default alias set, so `books SET` reads `SET` as an alias. Fix: in `_parse_update`, parse the target and any comma-separated tables with `UPDATE_ALIAS_TOKENS`, and keep delegating explicit joins to `_parse_join`. Let me check how the generator prints joins on the target table first.
[tool_use Bash] {"command": "rg -n \"def table_sql\" -A25 sqlglot/generator.py | rg -n \"joins\" ; rg -n \"def join_sql\" -A12 sqlglot/generator.py | head -30; rg -n \"def test_mysql|def test_\" tests/dialects/test_mysql.py | rg -i \"update\" ; rg -n \"UPDATE\" tests/dialects/test_mysql.py | head -30", "description": "Check join rendering and existing MySQL update tests"}
[tool_result] 2697:    def join_sql(self, expression: exp.Join) -> str:
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
2709-                expression.ki
…[2267 chars elided]…
 col1 WITH 5 BUCKETS")
tests/dialects/test_mysql.py:1640:...date_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS AUTO UPDATE")
tests/dialects/test_mysql.py:1641:...ate_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS MANUAL UPDATE"...
tests/dialects/test_mysql.py:1700:"CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT ...
tests/dialects/test_mysql.py:1705:...orders FOR EACH ROW BEGIN UPDATE statistics SET delete_count = delete_count + 1 ...
[assistant] The existing MySQL test at line 245 covers the explicit-JOIN form. I'll make the parser change in the generic `_parse_update`, since the comma-join handling lives there and the explicit-JOIN path is unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py", "old_string": "        hint = self._parse_hint()\n        kwargs: dict[str, object] = {\n            \"hint\": hint,\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }\n        whil
…[215 chars elided]…
       join = self.expression(\n                    exp.Join(this=self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS))\n                )\n            else:\n                join = self._parse_join()\n\n            if not join:\n                break\n\n            this.append(\"joins\", join)\n\n        kwargs: dict[str, object] = {\"hint\": hint, \"this\": this}\n        while self._curr:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()\" \"UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id\" \"UPDATE authors AS a, books AS b SET a.x = 1\" \"UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1 
…[340 chars elided]…
ks AS b ON a.id = b.author_id SET a.deleted_at = now(), b.deleted_at = now()\" \"UPDATE items, orders SET items.qty = 0 WHERE items.id = orders.item_id ORDER BY items.id LIMIT 10\" > /tmp/mysql-upd-probe/stmts2.sql; PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read mysql < /tmp/mysql-upd-probe/stmts2.sql; echo \"exit=$?\"", "description": "Apply parser fix and probe the variants"}
[tool_result] OK        UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()
          UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
OK        UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
          UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
OK        UPDATE authors AS a, books AS b SET a.x = 1
          UPDATE authors AS a, books AS b SET a.x = 1
OK        UPDATE authors INNER JOIN books ON
…[756 chars elided]…
          UPDATE authors SET deleted_at = NOW()
OK        UPDATE authors AS a JOIN books AS b ON a.id = b.author_id SET a.deleted_at = now(), b.deleted_at = now()
          UPDATE authors AS a JOIN books AS b ON a.id = b.author_id SET a.deleted_at = NOW(), b.deleted_at = NOW()
OK        UPDATE items, orders SET items.qty = 0 WHERE items.id = orders.item_id ORDER BY items.id LIMIT 10
          UPDATE items, orders SET items.qty = 0 WHERE items.id = orders.item_id ORDER BY items.id LIMIT 10
exit=0
[assistant] All variants now round-trip. Next, a regression test next to the existing multi-table UPDATE case in the MySQL test file.
[tool_use Bash] {"command": "sed -n 236,252p tests/dialects/test_mysql.py", "description": "View existing multi-table UPDATE test cases"}
[tool_result]         self.validate_identity("ALTER TABLE t ALTER INDEX i VISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET INVISIBLE")
        self.validate_identity("ALTER TABLE t ALTER COLUMN c SET VISIBLE")
        self.validate_identity("ALTER TABLE t RENAME INDEX a TO b")
        self.validate_identity(
            "ALTER TABLE t RENAME KEY a TO b",
            "ALTER TABLE t RENAME INDEX a TO b",
        )
        self.validate_identity(
            "UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id"
        )

        # PARTITION BY RANGE - simple column
        self.validate_identity(
            "CREATE TABLE t (id INT, created_at DATE) PARTITION BY RANGE (id) (PARTITION p0 VALUES LESS THAN (10), PARTITION p1 VALUES LESS THAN (20), PARTITION p2 VALUES LESS THAN (MAXVALUE))"
        )
        self.validate_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id\"\n        )\n", "new_string": "        self.validate_identity(\n            \"UPDATE foo JOI
…[72 chars elided]…
    self.validate_identity(\n            \"UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()\"\n        )\n        self.validate_identity(\n            \"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id\"\n        )\n        self.validate_identity(\n            \"UPDATE authors, books LEFT JOIN x ON books.id = x.id SET authors.x = 1\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155936-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; echo \"=== full suite ===\"; PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run MySQL dialect tests then full suite"}
[tool_result] ...................................................                                        [100%]
51 passed, 486 subtests passed in 0.26s
=== full suite ===
............................................................................................................................................................................................................................................... [ 21%]
.................................... [ 24%]
....................................................
…[439 chars elided]…
....................................................................................... [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 48.78s
exit=
[assistant] Tests pass. The `exit=` line came back empty because of how I captured it, so I'll confirm the full-suite exit code and run the linter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no > /tmp/mysql-upd-probe/full.log 2>&1; echo \"pytest exit=$?\"; tail -1 /tmp/mysql-upd-probe/full.log; ($PY -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git status --short", "description": "Confirm full suite exit code and lint changed files"}
[tool_result] pytest exit=0
1112 passed, 18136 subtests passed in 55.24s
All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_mysql.py
[assistant] MySQL's comma-separated multi-table `UPDATE` now parses and round-trips. The reported statement is fixed, and the full suite passes with exit 0 (1112 passed).

**Cause:** `_parse_update` in `sqlglot/parser.py` parsed the target table, but comma-separated tables went through the generic join path, which uses the default alias tokens. Those include `SET`, so `books SET` read `SET` as an alias and then failed on `authors`. Explicit `JOIN`s worked because they have an `ON` clause.

**Fix:** `_parse_update` now parses the target with `UPDATE_ALIAS_TOKENS`. It then loops over comma-separated tables 
…[835 chars elided]…
s

**Things to know:**
- The fix is in the generic `_parse_update`, not a MySQL-only override, so other dialects now also accept `UPDATE a, b SET ...`. Postgres and others use `FROM` for this, so the change is permissive there, not wrong. Say if you'd rather scope it to MySQL.
- The probe script's `-I` flag ignores `PYTHONPATH`, so `probe_parse.py` fails with `No module named 'sqlglot'` under the interpreter in `memory.md`. I ran it without `-I` and with `PYTHONPATH` set to the worktree. That is a harness issue, not part of this fix.
- No other parse failures surfaced in the variants I probed.
