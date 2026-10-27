# trajectory base-1

final message:
Multi-table MySQL `UPDATE` now parses and round-trips, for comma-separated tables and explicit joins. The full suite passes: 1112 tests, 18136 subtests.

**Cause:** the comma-join branch in the base parser reads the next table with the default alias tokens. MySQL's `TABLE_ALIAS_TOKENS` includes `SET`, so `UPDATE authors, books SET ...` consumed `SET` as the alias of `books` and failed on the next token. The single-table `UPDATE` path already excludes `SET` via `UPDATE_ALIAS_TOKENS`.

**Fix** (`sqlglot/parsers/mysql.py`): a MySQL-only `_parse_join` override. When the next token is a comma, it parses the following table with `UPDATE_ALIAS_TOKENS`; otherwise it defers to `super()`. This follows the existing ClickHouse override pattern. I kept it out of the base parser because the comma list is MySQL syntax.

**Round-trip results:**
- `UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()` now parses and round-trips.
- `UPDATE authors a, books b SET a.x = 1 WHERE ...` produces `UPDATE authors AS a, books AS b SET a.x = 1 WHERE ...`.
- `UPDATE authors INNER JOIN books ON ... SET ...` still round-trips unchanged.

**Tests:** three `validate_identity` cases added to `tests/dialects/test_mysql.py` next to the existing UPDATE identity tests. `ruff check` passes and `ruff format` was applied to `mysql.py`.

**Behaviour change to be aware of:** the override also applies to MySQL `SELECT ... FROM a, b`. The only difference is that `SET` can no longer be taken as a table alias there, and MySQL reserves `SET`, so no valid query changes.

Nothing is committed; the changes are in the working tree of this worktree.

## events
[assistant] I'll start by reading the MySQL dialect and the base parser's UPDATE handling.
[tool_use Bash] {"command": "grep -n \"UPDATE\\|Update\" sqlglot/dialects/mysql.py | head -50; echo ---; grep -n \"def _parse_update\" -A 40 sqlglot/parser.py | head -70; echo ---; grep -n \"class Update(\" -A 25 sqlglot/expressions.py", "description": "Find UPDATE handling in MySQL dialect and parser"}
[tool_result ERROR] Exit code 2
---
3642:    def _parse_update(self) -> exp.Update:
3643-        hint = self._parse_hint()
3644-        kwargs: dict[str, object] = {
3645-            "hint": hint,
3646-            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647-        }
3648-        while self._curr:
3649-            if self._match(TokenType.SET):
3650-                kwargs["expressions"] = self._parse_csv(self._parse_equality)
3651-            elif self._match(TokenType.RETURNI
…[1044 chars elided]…
e:
3672-        return self.expression(
3673-            exp.Use(
3674-                kind=self._parse_var_from_options(self.USABLES, raise_unmatched=False),
3675-                this=self._parse_table(schema=False),
3676-            )
3677-        )
3678-
3679-    def _parse_uncache(self) -> exp.Uncache:
3680-        if not self._match(TokenType.TABLE):
3681-            self.raise_error("Expecting TABLE after UNCACHE")
3682-
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
[assistant] The grep missed `expressions.py`, so the layout may differ. I'll check the tree and the MySQL dialect directly.
[tool_use Bash] {"command": "ls sqlglot | head -80; ls sqlglot/dialects | grep -i mysql; grep -rn \"class Update(\" sqlglot/ ; grep -rn \"UPDATE\" sqlglot/dialects/mysql.py | head", "description": "Inspect repo layout and locate Update expression and MySQL UPDATE code"}
[tool_result] __init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
mysql.py
sqlglot/expressions/dml.py:295:class Update(Expression, DML):
[tool_use Bash] {"command": "sed -n 290,330p sqlglot/expressions/dml.py; echo ---; grep -n \"Update\\|update\" sqlglot/dialects/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py 2>/dev/null; echo ---; grep -rn \"def update_sql\" -A 30 sqlglot/generator.py sqlglot/generators/*.py | head -60", "description": "Read Update expression and generator/parser UPDATE code"}
[tool_result]         "input_format": False,
        "serde": False,
    }


class Update(Expression, DML):
    arg_types = {
        "with_": False,
        "this": False,
        "expressions": False,
        "from_": False,
        "where": False,
        "returning": False,
        "order": False,
        "limit": False,
        "options": False,
        "hint": False,
    }

    def table(
        self,
        expression: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        
…[4945 chars elided]…
pression, "expression")
sqlglot/generators/teradata.py-145-
sqlglot/generators/teradata.py-146-        return f"{locking_clause} {query_sql}"
sqlglot/generators/teradata.py-147-
sqlglot/generators/teradata.py-148-    def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
sqlglot/generators/teradata.py-149-        kind = self.sql(expression, "kind").upper()
sqlglot/generators/teradata.py-150-        if kind == "TABLE" and locations.get(exp.Properties.Location.POST_NAME):
[assistant] The base parser's `_parse_update` reads a single table with `joins=True`, so a comma-separated list is never consumed. Next I'll reproduce the failure and read `_update_from_joins_sql`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now() WHERE authors.id = books.author_id', 'UPDATE authors INNER JOIN books ON authors.id = books.author_id 
…[79 chars elided]…
.id = b.aid']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e)[:300]); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"_update_from_joins_sql\" -A 25 sqlglot/generator.py | head -50; grep -n \"UPDATE\\|_parse_update\" sqlglot/parsers/*.py sqlglot/dialects/mysql.py | head", "description": "Reproduce MySQL multi-table UPDATE parse failure"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
ERR Invalid expression / Unexpected token. Line 1, Col: 33.
  UPDATE authors, books SET [4mauthors[0m.deleted_at = now(), books.deleted_at = now() WHERE authors.id = books.author_id
Update(
  this=Table(
    this
…[3965 chars elided]…
teradata.py:117:    # https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/Teradata-VantageTM-SQL-Data-Manipulation-Language-17.20/Statement-Syntax/UPDATE/UPDATE-Syntax-Basic-Form-FROM-Clause
sqlglot/parsers/teradata.py:118:    def _parse_update(self) -> exp.Update:
sqlglot/parsers/teradata.py:121:                this=self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS),
sqlglot/parsers/teradata.py:139:        # Also supports: SET QUERY_BAND = 'key=value;' UPDATE FOR SESSION|TRANSACTION
[assistant] Explicit `JOIN` already parses and round-trips. Only the comma form fails. Before choosing where to hook, I need to see how the parser treats commas in joins and how the MySQL parser is organized.
[tool_use Bash] {"command": "grep -n \"def _parse_join(\" -A 30 sqlglot/parser.py | grep -n \"COMMA\" ; grep -n \"COMMA\" sqlglot/parser.py | head -40; echo ---; grep -n \"class Parser\\|def _parse_\\|^    [A-Z_]* = \\|^    [A-Z_]*: \" sqlglot/parsers/mysql.py | head -60; echo ---; grep -n \"class Join\\b\\|class Join(\" -A3 sqlglot/expressions/*.py | head; echo; grep -n \"def join_sql\" -A 30 sqlglot/generator.py | grep -n \"comma\\|, \" ", "description": "Inspect comma handling in parser joins and MySQL parser layout"}
[tool_result] 4:4405-        if self._match(TokenType.COMMA):
681:        TokenType.COMMAND,
828:        TokenType.COMMAND,
971:            TokenType.COMMA,
1007:    LAMBDA_ARG_TERMINATORS: t.ClassVar[frozenset] = frozenset({TokenType.COMMA, TokenType.R_PAREN})
1670:    OPTYPE_FOLLOW_TOKENS: t.ClassVar = {TokenType.COMMA, TokenType.R_PAREN}
1680:    JSON_KEY_VALUE_SEPARATOR_TOKENS: t.ClassVar = {TokenType.COLON, TokenType.COMMA, TokenType.IS}
1712:    PRIVILEGE_FOLLOW_TOKENS: t.ClassVar = {TokenType.ON, Token
…[3971 chars elided]…
key(
---
sqlglot/expressions/query.py:668:class Join(Expression):
sqlglot/expressions/query.py-669-    arg_types = {
sqlglot/expressions/query.py-670-        "this": True,
sqlglot/expressions/query.py-671-        "on": False,

1:2697:    def join_sql(self, expression: exp.Join) -> str:
2:2698-        if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
19:2715-        match_cond = self.sql(expression, "match_condition")
21:2717-        on_sql = self.sql(expression, "on")
[tool_use Bash] {"command": "sed -n 4395,4415p sqlglot/parser.py; echo ---; sed -n 2697,2740p sqlglot/generator.py; echo ---; grep -n \"def _parse_table(\" -A 12 sqlglot/parser.py | head -30; echo ---; grep -n \"UPDATE_ALIAS_TOKENS\" -A3 sqlglot/parser.py | head; grep -n \"_parse_update\\|def _parse_\" sqlglot/parsers/mysql.py | grep -i \"update\\|delete\\|table\" ; python3 -c \"print(1)\" >/dev/null; PY=/private
…[62 chars elided]…
hify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT * FROM a, b', read='mysql').args['from_'].this)[:0])\nprint(sqlglot.parse_one('SELECT * FROM a, b').sql('mysql'))\nprint(sqlglot.parse_one('SELECT * FROM a, b').args.get('joins'))\n\"", "description": "Read comma-join parsing and table join generation"}
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
…[2555 chars elided]…
TRAILING", "BOTH"}
798-
--
3646:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
3647-        }
3648-        while self._curr:
3649-            if self._match(TokenType.SET):
306:    def _parse_alter_table_rename(self):
319:    def _parse_alter_table_modify(self, rename: bool = False) -> exp.Expr | None:
561:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:

SELECT * FROM a, b
[Join(
  this=Table(
    this=Identifier(this=b, quoted=False)))]
[assistant] `_parse_join` already turns a comma into a cross join, so the comma should be reachable. I'll check why `_parse_table(joins=True)` doesn't pick it up in UPDATE.
[tool_use Bash] {"command": "grep -n \"joins\" sqlglot/parser.py | sed -n 1,80p | grep -n \"4[78][0-9][0-9]:\\|47[0-9][0-9]:\\|48[0-9][0-9]:\"; sed -n 4790,4815p sqlglot/parser.py", "description": "Inspect how _parse_table handles joins"}
[tool_result] 21:4740:        joins: bool = False,
22:4747:        if not schema and not is_db_reference and not consume_pipe and not joins:
23:4790:            if joins:
24:4791:                for join in self._parse_joins():
25:4792:                    subquery.append("joins", join)
26:4862:        if joins:
27:4863:            for join in self._parse_joins():
28:4864:                this.append("joins", join)
            if joins:
                for join in self._parse_joins():
                    subque
…[267 chars elided]…
_parse_table)
            if self._match_text_seq("ROWS", "FROM")
            else None
        )
        rows_from = (
            self.expression(exp.Table(rows_from=rows_from_tables)) if rows_from_tables else None
        )

        only = self._match(TokenType.ONLY)

        this = t.cast(
            exp.Expr,
            bracket
            or rows_from
            or self._parse_bracket(
                self._parse_table_parts(schema=schema, is_db_reference=is_db_reference)
            ),
[assistant] `_parse_joins` is reached, so the failure is probably inside the join's table parse. My guess is that `SET` gets consumed as the alias of `books`, since the join branch uses the default alias tokens rather than `UPDATE_ALIAS_TOKENS`. I'll confirm that before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET x = 1', 'UPDATE authors, books b SET b.x = 1', 'UPDATE authors a, books b SET a.x = 1']:\n    try: print(sqlglot.parse_one(s, read='mysql').sql('mysql'))\n    excep
…[1 chars elided]…
 Exception as ex: print('ERR', s, '->', str(ex).splitlines()[0])\nfrom sqlglot.dialects.mysql import MySQL\nprint('SET' , [t for t in MySQL.Parser.TABLE_ALIAS_TOKENS if 'SET' in str(t)])\n\" ; grep -n \"TABLE_ALIAS_TOKENS\" -A6 sqlglot/parsers/mysql.py | head -12; grep -n \"def _parse_joins\" -A 12 sqlglot/parser.py | head -20", "description": "Test comma UPDATE variants and inspect alias tokens"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
83:    TABLE_ALIAS_TOKENS = (
84:        (parser.Parser.TABLE_ALIAS_TOKENS | {TokenType.ANTI, TokenType.SEMI})
85-        - parser.Parser.TABLE_INDEX_HINT_TOKENS
86-        - {TokenType.STRAIGHT_JOIN}
87-    )
88-
89-    RANGE_PARSERS = {
90-        **parser.Parser.RANGE_PARSERS,
5059:    def _parse_joins(self) -> t.Iterator[exp.Join]:
5060-        return iter(self._parse_join, None)
5061-
5062-    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
5063-        if not self._match(TokenType.INTO):
5064-            return None
5065-
5066-        return self.expression(
5067-            exp.UnpivotColumns(
5068-                this=self._match_text_seq("NAME") and self._parse_column(),
5069-                expressions=self._match_text_seq("VALUE") and self._parse_csv(self._parse_column),
5070-            )
5071-        )
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot.dialects.mysql import MySQL\nfor s in ['UPDATE authors, books SET x = 1', 'UPDATE authors, books b SET b.x = 1', 'UPDATE authors a, books b SET a.x = 1']:\n    try: print(sqlglot.parse_one(s, read='mysql').sql('mysql'))\n    except Exception as ex: print('ERR', s, '->', str(ex).splitlines()[0])\nprint('SET in mysql alias tokens:', sqlglot.exp and any(getattr(t,'name','')=='SET' for t in MySQL.Parser.TABLE_ALIAS_TOKENS))\n\"", "description": "Run comma UPDATE variants with repo on path"}
[tool_result] ERR UPDATE authors, books SET x = 1 -> Invalid expression / Unexpected token. Line 1, Col: 27.
UPDATE authors, books AS b SET b.x = 1
UPDATE authors AS a, books AS b SET a.x = 1
SET in mysql alias tokens: True
[assistant] Confirmed: in `UPDATE authors, books SET ...`, the comma-join table parse takes `SET` as an alias, because the join branch uses the default alias tokens and MySQL's `TABLE_ALIAS_TOKENS` includes `SET`. The fix has to make comma-joined UPDATE tables use `UPDATE_ALIAS_TOKENS`. I'll check the fast path in `_parse_table` before restructuring `_parse_update`.
[tool_use Bash] {"command": "sed -n 4747,4760p sqlglot/parser.py; echo ---; sed -n 4855,4870p sqlglot/parser.py; echo ---; grep -n \"UPDATE_ALIAS_TOKENS\" -B2 -A4 sqlglot/parsers/bigquery.py; echo ---; git log --oneline -3 -- sqlglot/parsers/mysql.py | cat; ls tests/dialects | grep -i mysql; grep -n \"UPDATE\" tests/dialects/test_mysql.py | head -40", "description": "Check table fast path, bigquery alias tokens, and MySQL update tests"}
[tool_result]         if not schema and not is_db_reference and not consume_pipe and not joins:
            index = self._index
            table = self._parse_table_parts(fast=True)

            if table is not None:
                curr_tt = self._curr.token_type
                next_tt = self._next.token_type

                fast_terminators = self.TABLE_TERMINATORS

                # only return the table if we're sure there are no other operators
                # MATCH_CONDITION is a special case becau
…[3446 chars elided]…
41:        self.validate_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS MANUAL UPDATE")
1700:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
1705:            "CREATE TRIGGER track_deletes BEFORE DELETE ON orders FOR EACH ROW BEGIN UPDATE statistics SET delete_count = delete_count + 1 WHERE table_name = 'orders' END",
[assistant] The fast path only applies when `joins` is False and falls back otherwise, so it's safe either way. Since the fix is MySQL-specific syntax, the CLAUDE.md guidance points to the MySQL parser rather than the base parser. I'll check the MySQL parser's flags and whether it already overrides `_parse_join`.
[tool_use Bash] {"command": "grep -rn \"JOINS_HAVE_EQUAL_PRECEDENCE\" sqlglot | head; grep -n \"_parse_join\\|def _parse_update\" sqlglot/parsers/*.py | head; sed -n 1,20p sqlglot/parsers/mysql.py; sed -n 300,306p sqlglot/parsers/mysql.py", "description": "Check MySQL parser imports and existing join-related overrides"}
[tool_result] sqlglot/parser.py:1818:    JOINS_HAVE_EQUAL_PRECEDENCE: t.ClassVar = False
sqlglot/parser.py:4409:            if cross_join and self.JOINS_HAVE_EQUAL_PRECEDENCE:
sqlglot/parsers/bigquery.py:150:    JOINS_HAVE_EQUAL_PRECEDENCE: t.ClassVar = True
sqlglot/parsers/hive.py:57:    JOINS_HAVE_EQUAL_PRECEDENCE = True
sqlglot/parsers/sqlite.py:21:    JOINS_HAVE_EQUAL_PRECEDENCE = True
sqlglot/parsers/clickhouse.py:246:    JOINS_HAVE_EQUAL_PRECEDENCE = True
sqlglot/parsers/clickhouse.py:654:    def _parse
…[1119 chars elided]…
isnull_to_is_null,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType


# All specifiers for time parts (as opposed to date parts)
# https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-format
TIME_SPECIFIERS = {"f", "H", "h", "I", "i", "k", "l", "p", "r", "S", "s", "T"}

    LOG_DEFAULTS_TO_LN = True
    STRING_ALIASES = True
    VALUES_FOLLOWED_BY_PAREN = False
    SUPPORTS_PARTITION_SELECTION = True

    def _parse_alter_table_rename(self):
[assistant] ClickHouse already overrides `_parse_join` and delegates to `super()`, so that pattern is established. I'll add a MySQL-only override: when the next token is a comma, parse the following table with `UPDATE_ALIAS_TOKENS` (so `SET` ends the table list); otherwise defer to the base implementation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-154308-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/mysql.py", "old_string": "    SUPPORTS_PARTITION_SELECTION = True\n\n    def _parse_alter_table_rename(self):", "new_string": "    SUPPORTS_PARTITION_SELECTION = True\n\n    def _parse_join(\n        self, skip_join_token: bool = False, p
…[165 chars elided]…
 self._match(TokenType.COMMA, advance=False):\n            self._advance()\n            table = self._try_parse(lambda: self._parse_table(alias_tokens=self.UPDATE_ALIAS_TOKENS))\n            return self.expression(exp.Join(this=table)) if table else None\n\n        return super()._parse_join(skip_join_token=skip_join_token, parse_bracket=parse_bracket)\n\n    def _parse_alter_table_rename(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-154308-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now I'll re-run the repro cases, plus a SELECT comma-join check to make sure the change doesn't affect MySQL SELECT.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()',\n          'UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now() WHERE au
…[317 chars elided]…
id SET authors.x = 1, books.y = 2',\n          'SELECT * FROM a, b']:\n    try: print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as ex: print('ERR', s, '->', str(ex).splitlines()[0])\n\"; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Verify comma UPDATE parses and run MySQL dialect tests"}
[tool_result] UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW() WHERE authors.id = books.author_id
UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.aid
UPDATE authors, books AS b, c SET b.x = 1
UPDATE authors JOIN books ON authors.id = books.aid, extra SET authors.x = 1
UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2
SELECT * FROM a, b
...................................................                                        [100%]
51 passed, 486 subtests passed in 0.71s
[assistant] The repro now parses and round-trips, and the existing MySQL tests pass (51 passed). Next I'll add regression tests next to the existing UPDATE identity tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-154308-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "offset": 20, "limit": 10}
[tool_result] 20	        self.validate_identity("CREATE TABLE foo (a VARCHAR(32) NOT NULL UNIQUE COMMENT 'test')")
21	        self.validate_identity("CREATE TABLE foo (id BIGINT)")
22	        self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
23	        self.validate_identity("CREATE TABLE temp (id SERIAL PRIMARY KEY)")
24	        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
25	        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
26	        self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
27	        self.validate_identity("DELETE /*+ MAX_EXECUTION_TIME(1) */ FROM t WHERE a = 1")
28	        self.validate_identity("DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id")
29	        self.validate_identity("CREATE TABLE foo (a BIGINT, INDEX USING BTREE (b))")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-154308-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n", "new_string": "        self.validate_identity(\"UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1\")\n        self.validat
…[8 chars elided]…
ty(\n            \"UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()\"\n        )\n        self.validate_identity(\n            \"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id\"\n        )\n        self.validate_identity(\n            \"UPDATE authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-154308-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the full suite with the project's required command, plus ruff for style, since one of my lines may be over the length limit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; echo \"--- ruff\"; ($PY -m ruff --version && $PY -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py; $PY -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -15", "description": "Run full test suite and ruff style checks"}
[tool_result] ................ [ 53%]
............................................................................................................................................................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 72.18s (0:01:12)
--- ruff
ruff 0.15.6
Would reformat: sqlglot/parsers/mysql.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parsers/mysql.py && git diff; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -1", "description": "Apply ruff formatting and show resulting diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index 9e12db747..85f124ae2 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -303,6 +303,19 @@ class MySQLParser(parser.Parser):
     VALUES_FOLLOWED_BY_PAREN = False
     SUPPORTS_PARTITION_SELECTION = True
 
+    def _parse_join(
+        self, skip_join_token: bool = False, parse_bracket: bool = False
+    ) -> exp.Join | None:
+        # Comma-separated tables in a multi-table UPDATE, wh
…[1383 chars elided]…
 authors INNER JOIN books ON authors.id = books.author_id SET authors.x = 1, books.y = 2"
+        )
         self.validate_identity("DELETE FROM t WHERE a <= 10 LIMIT 10")
         self.validate_identity("DELETE /*+ MAX_EXECUTION_TIME(1) */ FROM t WHERE a = 1")
         self.validate_identity("DELETE FROM t FORCE INDEX (idx) WHERE a > 5 ORDER BY id")
51 passed, 486 subtests passed in 0.17s
[This command modified 1 file you've previously read: sqlglot/parsers/mysql.py. Call Read before editing.]
[assistant] Multi-table MySQL `UPDATE` now parses and round-trips, for comma-separated tables and explicit joins. The full suite passes: 1112 tests, 18136 subtests.

**Cause:** the comma-join branch in the base parser reads the next table with the default alias tokens. MySQL's `TABLE_ALIAS_TOKENS` includes `SET`, so `UPDATE authors, books SET ...` consumed `SET` as the alias of `books` and failed on the next token. The single-table `UPDATE` path already excludes `SET` via `UPDATE_ALIAS_TOKENS`.

**Fix** (`sqlglot/parsers/mysql.py`): a MySQL-only `_parse_join` override. When the next token is a comma, it p
…[450 chars elided]…
a.x = 1 WHERE ...`.
- `UPDATE authors INNER JOIN books ON ... SET ...` still round-trips unchanged.

**Tests:** three `validate_identity` cases added to `tests/dialects/test_mysql.py` next to the existing UPDATE identity tests. `ruff check` passes and `ruff format` was applied to `mysql.py`.

**Behaviour change to be aware of:** the override also applies to MySQL `SELECT ... FROM a, b`. The only difference is that `SET` can no longer be taken as a table alias there, and MySQL reserves `SET`, so no valid query changes.

Nothing is committed; the changes are in the working tree of this worktree.
