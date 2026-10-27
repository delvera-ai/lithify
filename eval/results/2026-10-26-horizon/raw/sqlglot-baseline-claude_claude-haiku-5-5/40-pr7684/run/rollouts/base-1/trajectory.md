# trajectory base-1

final message:
`COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip with schema-qualified targets. The full suite passes (1112 tests, 18158 subtests).

The cause was in `_parse_comment` (`sqlglot/parser.py`). Only `TABLE` used the dotted-name parser. The other kinds fell through to `_parse_id_var()`, which stopped at the dot. I added a branch that routes those four kinds through `_parse_table_parts()`, the same parser the `TABLE` case depends on.

Changes:
- `sqlglot/parser.py`: the new branch in `_parse_comment`.
- `tests/dialects/test_postgres.py`: identity checks for `COMMENT ON TYPE foo.mood`, `VIEW foo.bat`, `SEQUENCE foo.seq` and `INDEX foo.idx`, beside the existing `COMMENT ON` checks.

The change is in the shared base parser, so it applies to every dialect, not just Postgres. Unqualified names still work, and `COMMENT ON TABLE` is untouched. I didn't add a dedicated test for the unqualified forms beyond the existing suite.

## events
[tool_use Bash] {"command": "grep -n -i \"comment\" sqlglot/dialects/postgres.py sqlglot/parser.py | head -60; grep -rn -i \"COMMENT ON\" tests/dialects/test_postgres.py | head", "description": "Find COMMENT ON handling in parser and tests"}
[tool_result] sqlglot/parser.py:320:        "_prev_comments",
sqlglot/parser.py:682:        TokenType.COMMENT,
sqlglot/parser.py:793:    COMMENT_TABLE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.IS}
sqlglot/parser.py:1087:        TokenType.COMMENT: lambda self: self._parse_comment(),
sqlglot/parser.py:1246:        "COMMENT": lambda self: self._parse_property_assignment(exp.SchemaCommentProperty),
sqlglot/parser.py:1353:        "COMMENT": lambda self: self.expression(
sqlglot/parser.py:1354:    
…[3717 chars elided]…
          if comments:
sqlglot/parser.py:4632:                if all_comments is None:
sqlglot/parser.py:4633:                    all_comments = []
tests/dialects/test_postgres.py:70:        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
tests/dialects/test_postgres.py:71:        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
tests/dialects/test_postgres.py:241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
[tool_use Bash] {"command": "sed -n 2178,2215p sqlglot/parser.py; grep -n \"CREATABLES\\|_parse_comment\\|\\\"COMMENT\\\"\" sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py | head -20", "description": "Read _parse_comment and related definitions"}
[tool_result]     def _parse_comment(self, allow_exists: bool = True) -> exp.Expr:
        start = self._prev
        exists = self._parse_exists() if allow_exists else None

        self._match(TokenType.ON)

        materialized = self._match_text_seq("MATERIALIZED")
        kind = self._match_set(self.CREATABLES) and self._prev
        if not kind:
            return self._parse_as_command(start)

        if kind.token_type in (TokenType.FUNCTION, TokenType.PROCEDURE):
            this = self._parse_user_d
…[1719 chars elided]…
self._prev.text.upper()
sqlglot/parser.py:2372:        create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2377:            create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2504:        elif create_token_type in self.DB_CREATABLES:
sqlglot/parser.py:3353:        kind = self._prev.text if self._match_set(self.CREATABLES) else None
sqlglot/parser.py:9599:        kind = self._prev.text.upper() if self._match_set(self.CREATABLES) else None
[tool_use Bash] {"command": "grep -rn \"COMMENT ON\" tests/ | head -30; grep -n \"def comment_sql\" -A25 sqlglot/generator.py; grep -n \"def _parse_table_parts\" sqlglot/parser.py", "description": "Find COMMENT ON tests and generator comment_sql"}
[tool_result] tests/test_transpile.py:948:            "COMMENT ON ACCESS METHOD gin IS 'GIN index access method'",
tests/fixtures/identity.sql:724:COMMENT ON COLUMN my_schema.my_table.my_column IS 'Employee ID number'
tests/fixtures/identity.sql:725:COMMENT ON DATABASE my_database IS 'Development Database'
tests/fixtures/identity.sql:726:COMMENT ON PROCEDURE my_proc(integer, integer) IS 'Runs a report'
tests/fixtures/identity.sql:727:COMMENT ON TABLE my_schema.my_table IS 'Employee Information'
tests/fixtures
…[1621 chars elided]…
ql(self, expression: exp.MergeTreeTTL) -> str:
4000-        where = self.sql(expression, "where")
4001-        group = self.sql(expression, "group")
4002-        aggregates = self.expressions(expression, key="aggregates")
4003-        aggregates = self.seg("SET") + self.seg(aggregates) if aggregates else ""
4004-
4005-        if not (where or group or aggregates) and len(expression.expressions) == 1:
4608:    def _parse_table_parts_fast(self) -> exp.Table | None:
4671:    def _parse_table_parts(
[tool_use Bash] {"command": "sed -n 619,660p sqlglot/parser.py; sed -n 4671,4680p sqlglot/parser.py; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Inspect creatable token sets and test env"}
[tool_result]     DB_CREATABLES: t.ClassVar = {
        TokenType.DATABASE,
        TokenType.DICTIONARY,
        TokenType.FILE_FORMAT,
        TokenType.MODEL,
        TokenType.NAMESPACE,
        TokenType.SCHEMA,
        TokenType.SEMANTIC_VIEW,
        TokenType.SEQUENCE,
        TokenType.SINK,
        TokenType.SOURCE,
        TokenType.STAGE,
        TokenType.STORAGE_INTEGRATION,
        TokenType.STREAMLIT,
        TokenType.TABLE,
        TokenType.TAG,
        TokenType.VIEW,
        TokenType.WAR
…[453 chars elided]…
RABLES: t.ClassVar = {
        TokenType.INDEX,
        TokenType.TABLE,
    def _parse_table_parts(
        self,
        schema: bool = False,
        is_db_reference: bool = False,
        wildcard: bool = False,
        fast: bool = False,
    ) -> exp.Table | exp.Dot | None:
        if fast:
            return self._parse_table_parts_fast()

<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in ['COMMENT ON TYPE foo.mood IS \\'x\\'', 'COMMENT ON VIEW foo.bat IS \\'x\\'', 'COMMENT ON SEQUENCE foo.s IS \\'x\\'', 'COMMENT ON INDEX foo.i IS \\'x\\'', 'COMMENT ON TABLE foo.bar IS \\'x\\'']:\n    try: print(sqlglot.transpile(sql, read='postgres'))\n    except Exception as e: print('FAIL', sql, type(e).__name__, str(e)[:120])\n\"", "description": "Reproduce COMMENT ON failures"}
[tool_result] FAIL COMMENT ON TYPE foo.mood IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON TYPE
FAIL COMMENT ON VIEW foo.bat IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON VIEW
FAIL COMMENT ON SEQUENCE foo.s IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 24.
  COMMENT ON SEQU
FAIL COMMENT ON INDEX foo.i IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 21.
  COMMENT ON INDE
["COMMENT ON TABLE foo.bar IS 'x'"]
[assistant] Reproduced. `_parse_comment` falls through to `_parse_id_var()` for these kinds, which stops at the dot. I'll route them through `_parse_table_parts()`, the same dotted-name parser the `TABLE` branch relies on.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-154700-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type == TokenType.COLUMN:", "new_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type in (TokenType.TYPE, TokenType.VIEW, TokenType.SEQUENCE, TokenType.INDEX):\n            this = self._parse_table_parts()\n        elif kind.token_type == TokenType.COLUMN:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-154700-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll add Postgres tests next to the existing `COMMENT ON` identity checks, then verify.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-154700-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.seq IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.idx IS 'x'\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-154700-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor sql in ['COMMENT ON TYPE foo.mood IS \\'x\\'', 'COMMENT ON VIEW foo.bat IS \\'x\\'', 'COMMENT ON SEQUENCE foo.s IS \\'x\\'', 'COMMENT ON INDEX foo.i IS \\'x\\'', 'COMMENT ON INDEX i IS \\'x\\'']:\n    print(sqlglot.transpile(sql, read='postgres'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] ["COMMENT ON TYPE foo.mood IS 'x'"]
["COMMENT ON VIEW foo.bat IS 'x'"]
["COMMENT ON SEQUENCE foo.s IS 'x'"]
["COMMENT ON INDEX foo.i IS 'x'"]
["COMMENT ON INDEX i IS 'x'"]
.................................................................................................................................................................................................................................................................................. [ 24%]
........................... [ 27%]
...........
…[458 chars elided]…
5%]
................................................................................................................................................................................................ [ 82%]
............................ [ 85%]
........................................................................ [ 91%]
.................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 52.18s
[assistant] Full suite passes. I'll check the formatter, since the new parser line is long.
[tool_use Bash] {"command": "(ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 || true); (ruff check sqlglot/parser.py 2>&1 | tail -3 || true); git diff --stat", "description": "Check formatting and lint on changed files"}
[tool_result] Would reformat: sqlglot/parser.py
1 file would be reformatted, 1 file already formatted
All checks passed!
 sqlglot/parser.py               | 2 ++
 tests/dialects/test_postgres.py | 4 ++++
 2 files changed, 6 insertions(+)
[tool_use Bash] {"command": "ruff format sqlglot/parser.py && git diff sqlglot/parser.py && ruff format --check sqlglot/parser.py", "description": "Apply ruff format and show parser diff"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index f7295acdf..78176b358 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -2190,6 +2190,13 @@ class Parser:
             this = self._parse_user_defined_function(kind=kind.token_type)
         elif kind.token_type == TokenType.TABLE:
             this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
+        elif kind.token_type in (
+            TokenType.TYPE,
+            TokenType.VIEW,
+            TokenType.SEQUENCE,
+            TokenType.INDEX,
+        ):
+            this = self._parse_table_parts()
         elif kind.token_type == TokenType.COLUMN:
             this = self._parse_column()
         else:
1 file already formatted
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Rerun Postgres dialect tests after formatting"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.30s
[assistant] `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip with schema-qualified targets. The full suite passes (1112 tests, 18158 subtests).

The cause was in `_parse_comment` (`sqlglot/parser.py`). Only `TABLE` used the dotted-name parser. The other kinds fell through to `_parse_id_var()`, which stopped at the dot. I added a branch that routes those four kinds through `_parse_table_parts()`, the same parser the `TABLE` case depends on.

Changes:
- `sqlglot/parser.py`: the new branch in `_parse_comment`.
- `tests/dialects/test_postgres.py`: identity checks for `COMMENT ON TYPE foo.mood`, `VIEW foo.bat`, `SEQUENCE foo.seq` and `INDEX foo.idx`, beside the existing `COMMENT ON` checks.

The change is in the shared base parser, so it applies to every dialect, not just Postgres. Unqualified names still work, and `COMMENT ON TABLE` is untouched. I didn't add a dedicated test for the unqualified forms beyond the existing suite.
