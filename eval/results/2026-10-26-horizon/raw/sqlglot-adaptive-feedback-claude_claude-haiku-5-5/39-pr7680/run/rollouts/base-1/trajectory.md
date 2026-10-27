# trajectory base-1

final message:
Multi-table MySQL `UPDATE` now parses and round-trips, both comma-separated tables and explicit joins. The full suite passes: `SUMMARY: 1112 passed, 18136 subtests passed in 63.50s`, `EXIT: 0`, run after my last edit.

**Root cause:** the comma-joined table `books` was parsed with MySQL's default table-alias tokens, which accept `SET`. So `SET` was read as the alias, and parsing failed at `authors.deleted_at`. The main table already excluded `SET` for UPDATE, but the join path did not. `SET` is a reserved word in MySQL, so I excluded it in MySQL's `TABLE_ALIAS_TOKENS`.

**Changes:**
- `sqlglot/parsers/mysql.py`: `TABLE_ALIAS_TOKENS` now also excludes `TokenType.SET`. This is a one-line change. Doris and StarRocks inherit it, and their tests pass too.
- `tests/dialects/test_mysql.py`: added round-trip tests for the task's statement, aliased comma tables, three comma-separated tables, a comma table next to an explicit JOIN, and an explicit JOIN followed by a comma table.

**AST shape:** a comma-joined table is stored as an unconditioned `Join` on the `Table`'s `joins`, the same way explicit joins are already stored. I did not add a new node or argument.

**Probes:** all the forms I tried round-trip exactly, including WHERE, ORDER BY, LIMIT, and aliases in first, middle, and last position. The task's example differs only in `now()` becoming `NOW()`, which is existing function-name normalisation.

**Not covered:** transpiling a joined UPDATE to another dialect is not rewritten. `UPDATE authors, books ...` now comes out unchanged for Postgres, T-SQL, and SQLite, and those engines reject it. Explicit `JOIN` UPDATEs already behave the same way, since they also come out unchanged. Making those targets valid means moving the joins into `FROM`, which is a separate cross-dialect change. I left it out of this fix, and it's the natural follow-up if you want it.

## events
[assistant] I'll start by finding the Python environment and the relevant parser code, and I'll read the dialect skill that matches a parse failure.
[tool_use Bash] {"command": "ls .lithify/harness/ && cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md | head -150 && grep -n \"UPDATE\" sqlglot/parser.py | head -40 && grep -n \"UPDATE\\|Update\" sqlglot/parsers/mysql.py sqlglot/dialects/mysql.py sqlglot/generators/mysql.py | head -30", "description": "List harness, read dialect skill, grep UPDATE handling"}
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTE
…[12166 chars elided]…
Type.DELETE, TokenType.UPDATE)):
7447:                self.raise_error("Expected DELETE or UPDATE")
8950:        if self._match_text_seq("REF", "UPDATE"):
8952:            this = "UPDATE"
8954:                this = "UPDATE SET DANGLING TO NULL"
9008:                TokenType.UPDATE, advance=False
9074:            elif self._match(TokenType.UPDATE):
sqlglot/generators/mysql.py:137:    DUPLICATE_KEY_UPDATE_WITH_SET = False
sqlglot/generators/mysql.py:151:    UPDATE_STATEMENT_SUPPORTS_FROM = False
[tool_use Bash] {"command": "cat .lithify/harness/memory.md; sed -n 3630,3680p sqlglot/parser.py; grep -n \"UPDATE\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py; grep -n \"def update_sql\" -A30 sqlglot/generators/base.py | head -50; grep -n \"class Update(\" -A20 sqlglot/expressions/*.py", "description": "Read memory file, parser UPDATE code, generator update_sql"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 
…[3275 chars elided]…
py-306-        "hint": False,
sqlglot/expressions/dml.py-307-    }
sqlglot/expressions/dml.py-308-
sqlglot/expressions/dml.py-309-    def table(
sqlglot/expressions/dml.py-310-        self,
sqlglot/expressions/dml.py-311-        expression: ExpOrStr,
sqlglot/expressions/dml.py-312-        dialect: DialectType = None,
sqlglot/expressions/dml.py-313-        copy: bool = True,
sqlglot/expressions/dml.py-314-        **opts: Unpack[ParserNoDialectArgs],
sqlglot/expressions/dml.py-315-    ) -> Update:
[assistant] Let me reproduce the failure and look at the generator's `update_sql`.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; cat > /tmp/probe_upd.py <<'EOF'\nimport sqlglot\ncases = [\n \"UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()\",\n \"UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id\",\n \"U
…[368 chars elided]…
.sql(\"mysql\"))\n        print(\"   this:\", type(e.this).__name__, \"joins:\", [type(j).__name__ for j in (e.args.get('joins') or [])])\n    except Exception as ex:\n        print(\"ERR\", c, \"->\", str(ex).splitlines()[0])\nEOF\nPYTHONPATH=. $P /tmp/probe_upd.py; grep -n \"def update_sql\" -A40 sqlglot/generators/*.py | head -80", "description": "Probe multi-table UPDATE parse and generation"}
[tool_result] ERR UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now() -> Invalid expression / Unexpected token. Line 1, Col: 33.
ERR UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id -> Invalid expression / Unexpected token. Line 1, Col: 33.
OK  UPDATE authors JOIN books ON authors.id = books.author_id SET books.x = 1
   this: Table joins: []
OK  UPDATE authors LEFT JOIN books ON authors.id = books.author_id SET books.x = 1 WHERE books.id IS NULL
   this: Ta
…[2913 chars elided]…
data.py-156-            )
sqlglot/generators/teradata.py-157-            this_schema = self.schema_columns_sql(expression.this)
sqlglot/generators/teradata.py-158-            return f"{this_name}{this_properties}{self.sep()}{this_schema}"
sqlglot/generators/teradata.py-159-
sqlglot/generators/teradata.py-160-        return super().createable_sql(expression, locations)
sqlglot/generators/teradata.py-161-
sqlglot/generators/teradata.py-162-    def extract_sql(self, expression: exp.Extract) -> str:
[assistant] Explicit `JOIN` forms already parse. The gap is the comma form. I need to see how the parser handles comma joins and how `Table` stores its joins before choosing a shape.
[tool_use Bash] {"command": "grep -n \"COMMA\" sqlglot/parser.py | head -40; grep -n \"def _parse_table(\" -A12 sqlglot/parser.py | head -30; grep -n \"joins\" sqlglot/parser.py | sed -n 1,60p; grep -n \"def join_sql\" -A30 sqlglot/generators/base.py | head -50; grep -n \"def table_sql\" -A25 sqlglot/generators/base.py | grep -n \"joins\"; grep -n \"class Table(\" -A25 sqlglot/expressions/query.py | head -40", "description": "Inspect comma-join parsing and Table joins handling"}
[tool_result] 681:        TokenType.COMMAND,
828:        TokenType.COMMAND,
971:            TokenType.COMMA,
1007:    LAMBDA_ARG_TERMINATORS: t.ClassVar[frozenset] = frozenset({TokenType.COMMA, TokenType.R_PAREN})
1670:    OPTYPE_FOLLOW_TOKENS: t.ClassVar = {TokenType.COMMA, TokenType.R_PAREN}
1680:    JSON_KEY_VALUE_SEPARATOR_TOKENS: t.ClassVar = {TokenType.COLON, TokenType.COMMA, TokenType.IS}
1712:    PRIVILEGE_FOLLOW_TOKENS: t.ClassVar = {TokenType.ON, TokenType.COMMA, TokenType.L_PAREN}
1781:    NO_PAREN
…[4795 chars elided]…
 "joins": False,
951-        "pivots": False,
952-        "hints": False,
953-        "system_time": False,
954-        "version": False,
955-        "format": False,
956-        "pattern": False,
957-        "ordinality": False,
958-        "when": False,
959-        "only": False,
960-        "partition": False,
961-        "changes": False,
962-        "rows_from": False,
963-        "sample": False,
964-        "indexed": False,
965-    }
966-
967-    @property
968-    def name(self) -> str:
[tool_use Bash] {"command": "sed -n 5059,5075p sqlglot/parser.py; sed -n 1812,1822p sqlglot/parser.py; grep -n \"def join_sql\" -A40 sqlglot/generators/generator.py | grep -n \"COMMA\\|\\\", \\\"\\|, \\|comma\" ; grep -n \"def table_sql\" -A30 sqlglot/generators/generator.py | grep -n \"joins\"; grep -n \"\\\"joins\\\"\" sqlglot/generators/generator.py | head", "description": "Read _parse_joins and join SQL generation"}
[tool_result]     def _parse_joins(self) -> t.Iterator[exp.Join]:
        return iter(self._parse_join, None)

    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
        if not self._match(TokenType.INTO):
            return None

        return self.expression(
            exp.UnpivotColumns(
                this=self._match_text_seq("NAME") and self._parse_column(),
                expressions=self._match_text_seq("VALUE") and self._parse_csv(self._parse_column),
            )
        )

   
…[501 chars elided]…
ot the case in some dialects, such
    # as BigQuery, where all joins have the same precedence.
    JOINS_HAVE_EQUAL_PRECEDENCE: t.ClassVar = False

    # Whether TIMESTAMP <literal> can produce a zone-aware timestamp
    ZONE_AWARE_TIMESTAMP_CONSTRUCTOR: t.ClassVar = False

ugrep: warning: sqlglot/generators/generator.py: No such file or directory
ugrep: warning: sqlglot/generators/generator.py: No such file or directory
ugrep: warning: sqlglot/generators/generator.py: No such file or directory
[assistant] The `ugrep` alias is failing on paths, so I'll use `/usr/bin/grep` and locate the base generator file and `_parse_join`.
[tool_use Bash] {"command": "ls sqlglot | head -80; /usr/bin/grep -n \"def _parse_join(\" -A30 sqlglot/parser.py | head -45; /usr/bin/grep -n \"def join_sql\" -A45 sqlglot/generator.py | head -60; /usr/bin/grep -n \"def table_sql\" -A40 sqlglot/generator.py | /usr/bin/grep -n \"joins\"", "description": "Locate base generator and join parse/gen code"}
[tool_result] __init__.py
__main__.py
__pycache__
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
4402:    def _parse_join(
4403-        self, skip_join_token: bool = False, parse_bracket: bool = False
4404-    ) -> exp.Join | None:
4405-        if self._match(TokenType.COMMA):
4406-            table 
…[2670 chars elided]…
   if using:
2734-                on_sql = f"{space}USING ({on_sql})"
2735-            else:
2736-                on_sql = f"{space}ON {on_sql}"
2737-        elif not op_sql:
2738-            if isinstance(this, exp.Lateral) and this.args.get("cross_apply") is not None:
2739-                return f" {this_sql}"
2740-
2741-            return f", {this_sql}"
2742-
28:2387-        joins = self.indent(
29:2388-            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
[assistant] The comma path already exists in `_parse_join`, so the failure is probably elsewhere. The error column points near `authors.deleted_at`, which suggests `SET` is being consumed as a table alias on the comma-joined table. I'll check that directly.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; cat > /tmp/probe_upd2.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfor c in [\"UPDATE authors, books SET x = 1\", \"UPDATE authors, books AS b SET x = 1\", \"UPDATE authors AS a, books AS b SET a.x = 1\", \"UPDATE authors, b
…[223 chars elided]…
" \"))\n    except Exception as ex:\n        print(\"ERR\", c, \"->\", str(ex).splitlines()[0])\nEOF\nPYTHONPATH=. $P /tmp/probe_upd2.py; /usr/bin/grep -n \"UPDATE_ALIAS_TOKENS\\|TABLE_ALIAS_TOKENS\" sqlglot/parser.py sqlglot/parsers/mysql.py | head; /usr/bin/grep -n \"def _parse_table_alias\" -A20 sqlglot/parser.py | head -30", "description": "Probe comma-join UPDATE variants and alias handling"}
[tool_result] ERR UPDATE authors, books SET x = 1 -> Invalid expression / Unexpected token. Line 1, Col: 27.
OK  UPDATE authors, books AS b SET x = 1 | repr: Update(   this=Table(     this=Identifier(this=authors, quoted=False),     joins=[       Join(         this=Table(           this=Identifier(this=books, quoted=False),           alias=TableAlias(             this=Identifier(this=b, quoted=False))))]),   expressions=[     EQ(       this=Column(      
OK  UPDATE authors AS a, books AS b SET a.x = 1 | repr:
…[2273 chars elided]…
enType.ALIAS)
4045-        alias = (
4046-            self._parse_id_var(any_token=any_token, tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4047-            or self._parse_string_as_identifier()
4048-        )
4049-
4050-        index = self._index
4051-        if self._match(TokenType.L_PAREN):
4052-            columns = self._parse_csv(self._parse_function_parameter)
4053-            self._match_r_paren() if columns else self._retreat(index)
4054-        else:
4055-            columns = None
[assistant] The root cause is clear now. The comma-joined table `books` is parsed with the default `TABLE_ALIAS_TOKENS`, which accepts `SET` as an alias. The main table uses `UPDATE_ALIAS_TOKENS`, which excludes `SET`, so only the join path is wrong. Let me see how MySQL defines its alias tokens.
[tool_use Bash] {"command": "sed -n 75,110p sqlglot/parsers/mysql.py; sed -n 768,800p sqlglot/parser.py; /usr/bin/grep -n \"SET\" sqlglot/parsers/mysql.py | head -20", "description": "Read MySQL parser alias token config"}
[tool_result]         TokenType.XOR: exp.Xor,
    }

    DISJUNCTION = {
        **parser.Parser.DISJUNCTION,
        TokenType.DPIPE: exp.Or,
    }

    TABLE_ALIAS_TOKENS = (
        (parser.Parser.TABLE_ALIAS_TOKENS | {TokenType.ANTI, TokenType.SEMI})
        - parser.Parser.TABLE_INDEX_HINT_TOKENS
        - {TokenType.STRAIGHT_JOIN}
    )

    RANGE_PARSERS = {
        **parser.Parser.RANGE_PARSERS,
        TokenType.SOUNDS_LIKE: lambda self, this: self.expression(
            exp.EQ(
                this
…[1792 chars elided]…
75:        "CHARSET": _show_parser("CHARACTER SET"),
231:    SET_PARSERS = {
232:        **parser.Parser.SET_PARSERS,
235:        "CHARACTER SET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
236:        "CHARSET": lambda self: self._parse_set_item_charset("CHARACTER SET"),
241:    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)
282:        TokenType.SET,
287:        TokenType.SET,
463:            offset = self._parse_number() if self._match_text_seq("OFFSET") else None
[assistant] The fix is small. MySQL reserves `SET`, and the base parser already excludes it from update aliases, but MySQL's `TABLE_ALIAS_TOKENS` re-admits it. That lets `SET` be taken as the alias of a comma-joined table. Before editing, I'll get a baseline of the MySQL test file.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3; /usr/bin/grep -n \"UPDATE\" tests/dialects/test_mysql.py | head -30", "description": "Run MySQL dialect tests for baseline and grep UPDATE tests"}
[tool_result] ...................................................                                        [100%]
51 passed, 486 subtests passed in 0.68s
24:        self.validate_identity("UPDATE items SET items.price = 0 WHERE items.id >= 5 LIMIT 10")
25:        self.validate_identity("UPDATE /*+ MAX_EXECUTION_TIME(1) */ t SET a = 1")
84:            "INSERT INTO things (a, b) VALUES (1, 2) AS new_data ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), a = new_data.a, b = new_data.b"
93:            "UPDATE items 
…[1892 chars elided]…
41:        self.validate_identity("ANALYZE tbl UPDATE HISTOGRAM ON col1 WITH 5 BUCKETS MANUAL UPDATE")
1700:            "CREATE TRIGGER audit_update AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (OLD.user_id, OLD.balance, NEW.balance, NOW()) END",
1705:            "CREATE TRIGGER track_deletes BEFORE DELETE ON orders FOR EACH ROW BEGIN UPDATE statistics SET delete_count = delete_count + 1 WHERE table_name = 'orders' END",
[assistant] Baseline is green (51 passed). Now the edit: exclude `SET` from MySQL's table alias tokens, matching the base parser's `UPDATE_ALIAS_TOKENS` intent.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101630-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/mysql.py", "old_string": "        - parser.Parser.TABLE_INDEX_HINT_TOKENS\n        - {TokenType.STRAIGHT_JOIN}\n    )", "new_string": "        - parser.Parser.TABLE_INDEX_HINT_TOKENS\n        - {TokenType.STRAIGHT_JOIN, TokenType.SET}\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101630-mysql-dialect-multi-table-update/base-1/sqlglot/parsers/mysql.py has been updated successfully.
[assistant] Now I'll re-probe a wider set of positions: comma-joined tables first, middle, and last, with and without aliases, mixed with explicit joins, and with WHERE/ORDER/LIMIT. I'll also check the AST shape against the existing explicit-JOIN form.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; cat > /tmp/probe_upd3.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n \"UPDATE authors, books SET authors.deleted_at = now(), books.deleted_at = now()\",\n \"UPDATE authors, books SET x = 1\",\n \"UPDATE authors, bo
…[935 chars elided]…
ET x = 1\", \"UPDATE authors JOIN books ON authors.id = books.id SET x = 1\"]:\n    t = sqlglot.parse_one(c, read=\"mysql\").this\n    print(type(t).__name__, [type(j).__name__ + (\"(kind=%s,on=%s)\" % (j.args.get(\"kind\"), bool(j.args.get(\"on\")))) for j in t.args.get(\"joins\") or []])\nEOF\nPYTHONPATH=. $P /tmp/probe_upd3.py", "description": "Re-probe multi-table UPDATE forms and AST shapes"}
[tool_result] DIFF UPDATE authors, books SET authors.deleted_at = NOW(), books.deleted_at = NOW()
RT  UPDATE authors, books SET x = 1
RT  UPDATE authors, books AS b SET x = 1
RT  UPDATE authors AS a, books AS b SET a.x = 1
RT  UPDATE a, b, c SET a.x = 1
RT  UPDATE a, b, c AS cc SET a.x = 1
RT  UPDATE a AS aa, b, c SET a.x = 1
RT  UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1
RT  UPDATE a JOIN b ON a.id = b.id, c SET a.x = 1
RT  UPDATE a, b SET a.x = 1 WHERE a.id = b.id
RT  UPDATE a, b SET a.x = 1 WHERE a.id = b.id ORDER BY a.id LIMIT 5
RT  UPDATE a INNER JOIN b ON a.id = b.id SET a.x = 1
RT  UPDATE a LEFT JOIN b ON a.id = b.id SET a.x = 1 WHERE b.id IS NULL
RT  UPDATE a, b SET a.x = 1 RETURNING a.id
--- AST shape, comma vs explicit JOIN ---
Table ['Join(kind=None,on=False)']
Table ['Join(kind=None,on=True)']
[assistant] Every form round-trips. The one `DIFF` is only `now()` → `NOW()` case normalization, not a structural change. The comma join is stored as a `Join` with no kind or `ON` on the `Table`, the same convention as the existing explicit JOIN. Next I'll look at the neighbouring MySQL UPDATE test to place the new tests, and check what other dialects emit now that this parses.
[tool_use Bash] {"command": "sed -n 240,252p tests/dialects/test_mysql.py; P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\nfor d in ['postgres','tsql','sqlite']:\n    print(d, '->', sqlglot.transpile('UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id', read='mysql', write=d)[0])\n\"", "description": "View neighbouring UPDATE test and transpile outputs"}
[tool_result]         self.validate_identity(
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
postgres -> UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
tsql -> UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
sqlite -> UPDATE authors, books SET authors.x = 1 WHERE authors.id = books.author_id
[assistant] Parsing now works, but transpiling to Postgres, T-SQL, or SQLite emits `UPDATE authors, books`, which those engines reject. Before deciding whether that's in scope, I'll check how the existing explicit-JOIN form already transpiles, since it shares the same `Update` shape.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=. $P -c \"\nimport sqlglot\nfor d in ['postgres','tsql']:\n    print(d, '->', sqlglot.transpile('UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1', read='mysql', write=d)[0])\n\"; git stash list >/dev/null; git diff --stat", "description": "Check explicit JOIN UPDATE transpile for comparison"}
[tool_result] postgres -> UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1
tsql -> UPDATE authors JOIN books ON authors.id = books.author_id SET authors.x = 1
 sqlglot/parsers/mysql.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
[assistant] The explicit JOIN form already emits MySQL syntax unchanged for Postgres and T-SQL, so the comma form now behaves the same way. Rewriting joined `UPDATE` into the target's `FROM` form is a separate cross-dialect feature, and I'll flag it rather than expand scope. Now I'll add tests next to the existing `UPDATE ... JOIN` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101630-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"UPDATE foo JOIN bar ON TRUE SET foo.a = bar.a WHERE foo.id = bar.id\"\n        )\n", "new_string": "        self.validate_identity(\n            \"UPDATE foo JOI
…[180 chars elided]…
ed_at = NOW()\"\n        )\n        self.validate_identity(\"UPDATE authors AS a, books AS b SET a.x = 1 WHERE a.id = b.author_id\")\n        self.validate_identity(\"UPDATE a, b, c SET a.x = 1 WHERE a.id = b.id AND b.id = c.id\")\n        self.validate_identity(\"UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1\")\n        self.validate_identity(\"UPDATE a JOIN b ON a.id = b.id, c SET a.x = 1\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101630-mysql-dialect-multi-table-update/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Next I'll run the MySQL test file, then ruff on the two edited files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3; ($P -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py; $P -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py) 2>&1 | tail -8", "description": "Run MySQL tests and ruff checks on edited files"}
[tool_result] ...................................................                                        [100%]
51 passed, 486 subtests passed in 0.22s
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format tests/dialects/test_mysql.py && git diff", "description": "Apply ruff formatting to test file and show diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index 9e12db747..cca9c285d 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -83,7 +83,7 @@ class MySQLParser(parser.Parser):
     TABLE_ALIAS_TOKENS = (
         (parser.Parser.TABLE_ALIAS_TOKENS | {TokenType.ANTI, TokenType.SEMI})
         - parser.Parser.TABLE_INDEX_HINT_TOKENS
-        - {TokenType.STRAIGHT_JOIN}
+        - {TokenType.STRAIGHT_JOIN, TokenType.SET}
     )
 
     RANGE_PAR
…[577 chars elided]…
b SET a.x = 1 WHERE a.id = b.author_id"
+        )
+        self.validate_identity("UPDATE a, b, c SET a.x = 1 WHERE a.id = b.id AND b.id = c.id")
+        self.validate_identity("UPDATE a, b JOIN c ON b.id = c.id SET a.x = 1")
+        self.validate_identity("UPDATE a JOIN b ON a.id = b.id, c SET a.x = 1")
 
         # PARTITION BY RANGE - simple column
         self.validate_identity(
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[assistant] Ruff reformatted the test file. The baseline probe already showed the comma forms failing before the parser change, so the new tests exercise the fix. Per the harness, I'll run the full suite in the foreground as its own call.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:46:50 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  84574       00:11 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-d29f7821d8.log
ELAPSED: 64s
SUMMARY: 1112 passed, 18136 subtests passed in 63.50s (0:01:03)
EXIT: 0
[assistant] Multi-table MySQL `UPDATE` now parses and round-trips, both comma-separated tables and explicit joins. The full suite passes: `SUMMARY: 1112 passed, 18136 subtests passed in 63.50s`, `EXIT: 0`, run after my last edit.

**Root cause:** the comma-joined table `books` was parsed with MySQL's default table-alias tokens, which accept `SET`. So `SET` was read as the alias, and parsing failed at `authors.deleted_at`. The main table already excluded `SET` for UPDATE, but the join path did not. `SET` is a reserved word in MySQL, so I excluded it in MySQL's `TABLE_ALIAS_TOKENS`.

**Changes:**
- `sqlglot
…[680 chars elided]…
 middle, and last position. The task's example differs only in `now()` becoming `NOW()`, which is existing function-name normalisation.

**Not covered:** transpiling a joined UPDATE to another dialect is not rewritten. `UPDATE authors, books ...` now comes out unchanged for Postgres, T-SQL, and SQLite, and those engines reject it. Explicit `JOIN` UPDATEs already behave the same way, since they also come out unchanged. Making those targets valid means moving the joins into `FROM`, which is a separate cross-dialect change. I left it out of this fix, and it's the natural follow-up if you want it.
