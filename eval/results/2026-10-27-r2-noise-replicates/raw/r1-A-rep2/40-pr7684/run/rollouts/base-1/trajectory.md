# trajectory base-1

final message:
`COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip unchanged. The full suite passes (1112 tests) and ruff is clean.

**Cause:** `_parse_comment` in `sqlglot/parser.py` read the target for these kinds with `_parse_id_var()`, which takes a single identifier. It stopped at the `.`, so the parser then expected `IS` and failed. `TABLE` already used the table-aware path.

**Fix:** these four kinds now go through `_parse_table_parts()`, the same helper used for table names, so they accept `schema.name`. Other kinds (`FUNCTION`, `SCHEMA`, `DATABASE`, etc.) are unchanged.

**Tests:** I added round-trip cases for `COMMENT ON TYPE foo.mood`, `VIEW foo.bat`, `SEQUENCE foo.seq` and `INDEX foo.idx` to `tests/dialects/test_postgres.py`. No existing test was modified.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -n -i \"comment\" sqlglot/parser.py | head -60; grep -n -i \"comment\" sqlglot/dialects/postgres.py | head; grep -rn -i \"comment on\" tests/dialects/test_postgres.py | head -20", "description": "Find COMMENT ON parsing code and tests"}
[tool_result] 320:        "_prev_comments",
682:        TokenType.COMMENT,
793:    COMMENT_TABLE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.IS}
1087:        TokenType.COMMENT: lambda self: self._parse_comment(),
1246:        "COMMENT": lambda self: self._parse_property_assignment(exp.SchemaCommentProperty),
1353:        "COMMENT": lambda self: self.expression(
1354:            exp.CommentColumnConstraint(this=self._parse_string())
1864:        self._prev_comments: list[str] = []
1879:        s
…[2637 chars elided]…
mments = self._prev_comments
4631:            if comments:
4632:                if all_comments is None:
4633:                    all_comments = []
tests/dialects/test_postgres.py:70:        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
tests/dialects/test_postgres.py:71:        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
tests/dialects/test_postgres.py:241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
[tool_use Bash] {"command": "sed -n 2178,2215p sqlglot/parser.py; grep -n \"_parse_table_parts\\|def _parse_table(\" sqlglot/parser.py | head -5; grep -n \"COMMENT ON\\|comment_sql\\|Comment\" sqlglot/generator.py sqlglot/dialects/postgres.py | head", "description": "Read _parse_comment and related helpers"}
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
…[965 chars elided]…
parts(schema=True, is_db_reference=kind == "SCHEMA")
2459:            table = self._parse_table_parts()
2460:            referenced_table = self._parse_table_parts() if self._match(TokenType.FROM) else None
sqlglot/generator.py:159:        exp.CommentColumnConstraint: lambda self, e: f"COMMENT {self.sql(e, 'this')}",
sqlglot/generator.py:739:        exp.SchemaCommentProperty: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:3980:    def comment_sql(self, expression: exp.Comment) -> str:
[tool_use Bash] {"command": "sed -n 3980,3995p sqlglot/generator.py; grep -n \"CREATABLES\" sqlglot/parser.py | head -3; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfor s in ['COMMENT ON TYPE foo.mood IS \\'x\\';','COMMENT ON VIEW foo.bat IS \\'x\\';','COMMENT ON SEQUENCE foo.s IS \\'x\\';','COMMENT ON INDEX foo.i IS \\'x\\';','COMMENT ON TABLE foo.bar IS \\'x\\'']:\n    try: print(parse_one(s, read='postgres').sql('postgres'))\n    except Exception as e: print('ERR', s, type(e).__name__, str(e)[:120])\n\"", "description": "Read comment generator and reproduce parse failures"}
[tool_result]     def comment_sql(self, expression: exp.Comment) -> str:
        this = self.sql(expression, "this")
        kind = expression.args["kind"]
        materialized = " MATERIALIZED" if expression.args.get("materialized") else ""
        exists_sql = " IF EXISTS " if expression.args.get("exists") else " "
        expression_sql = self.sql(expression, "expression")
        return f"COMMENT{exists_sql}ON{materialized} {kind} {this} IS {expression_sql}"

    def mergetreettlaction_sql(self, expressio
…[743 chars elided]…
ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON VIEW
ERR COMMENT ON SEQUENCE foo.s IS 'x'; ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 24.
  COMMENT ON SEQU
ERR COMMENT ON INDEX foo.i IS 'x'; ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 21.
  COMMENT ON INDE
COMMENT ON TABLE foo.bar IS 'x'
[tool_use Bash] {"command": "sed -n 639,650p sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfrom sqlglot.tokens import TokenType\nfor k in ['TYPE','VIEW','SEQUENCE','INDEX']: print(k, getattr(TokenType,k,None))\"", "description": "Check CREATABLES and token types for kinds"}
[tool_result]     CREATABLES: t.ClassVar = {
        TokenType.COLUMN,
        TokenType.CONSTRAINT,
        TokenType.FOREIGN_KEY,
        TokenType.FUNCTION,
        TokenType.INDEX,
        TokenType.PROCEDURE,
        TokenType.TRIGGER,
        TokenType.TYPE,
        *DB_CREATABLES,
    }

TYPE TokenType.TYPE
VIEW TokenType.VIEW
SEQUENCE TokenType.SEQUENCE
INDEX TokenType.INDEX
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094559-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type == TokenType.COLUMN:", "new_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type in (TokenType.TYPE, TokenType.VIEW, TokenType.SEQUENCE, TokenType.INDEX):\n            this = self._parse_table_parts()\n        elif kind.token_type == TokenType.COLUMN:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094559-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll check the repro cases and add tests to the Postgres dialect test file.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfor s in ['COMMENT ON TYPE foo.mood IS \\'x\\';','COMMENT ON VIEW foo.bat IS \\'x\\';','COMMENT ON SEQUENCE foo.s IS \\'x\\';','COMMENT ON INDEX foo.i IS \\'x\\';','COMMENT ON TYPE mood IS \\'x\\';','COMMENT ON TABLE foo.bar IS \\'x\\'']:\n    try: print(parse_one(s, read='postgres').sql('postgres'))\n    except Exception as e: print('ERR', s, type(e).__name__, str(e)[:120])\n\"; sed -n 66,74p tests/dialects/test_postgres.py", "description": "Verify fix and view nearby test lines"}
[tool_result] COMMENT ON TYPE foo.mood IS 'x'
COMMENT ON VIEW foo.bat IS 'x'
COMMENT ON SEQUENCE foo.s IS 'x'
COMMENT ON INDEX foo.i IS 'x'
COMMENT ON TYPE mood IS 'x'
COMMENT ON TABLE foo.bar IS 'x'
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y)")
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y DESC)")
        self.validate_identity("STRING_AGG(DISTINCT x, ',' ORDER BY y DESC)")
        self.validate_identity("SELECT CASE WHEN SUBSTRING('abcdefg') IN ('ab') THEN 1 ELSE 0 END")
        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
        self.validate_identity("SELECT e'\\xDEADBEEF'")
        self.validate_identity("SELECT CAST(e'\\176' AS BYTEA)")
        self.validate_identity("SELECT * FROM x WHERE SUBSTRING('Thomas' FROM '...$') IN ('mas')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094559-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.seq IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.idx IS 'x'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094559-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now the project's test command, plus a lint/format check on the touched files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3", "description": "Run full test suite and ruff checks"}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
........................... [ 27%]
.......................................................................................................................................................................................
…[393 chars elided]…
......................................................................................... [ 82%]
............................ [ 85%]
........................................................................ [ 91%]
.................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 57.00s
All checks passed!
Would reformat: sqlglot/parser.py
1 file would be reformatted, 1 file already formatted
[assistant] The suite passes (1112 tests). Ruff wants to reformat `parser.py`, so I'll check whether that's my line or pre-existing.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/parser.py 2>&1 | head -30", "description": "Show ruff format diff for parser.py"}
[tool_result] --- sqlglot/parser.py
+++ sqlglot/parser.py
@@ -2190,7 +2190,12 @@
             this = self._parse_user_defined_function(kind=kind.token_type)
         elif kind.token_type == TokenType.TABLE:
             this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
-        elif kind.token_type in (TokenType.TYPE, TokenType.VIEW, TokenType.SEQUENCE, TokenType.INDEX):
+        elif kind.token_type in (
+            TokenType.TYPE,
+            TokenType.VIEW,
+            TokenType.SEQUENCE,
+            TokenType.INDEX,
+        ):
             this = self._parse_table_parts()
         elif kind.token_type == TokenType.COLUMN:
             this = self._parse_column()

1 file would be reformatted
[assistant] It's my line. I'll apply the formatter's change and re-check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/parser.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Apply formatting, verify diff and postgres tests"}
[tool_result] 1 file reformatted
2 files already formatted
 sqlglot/parser.py               | 7 +++++++
 tests/dialects/test_postgres.py | 4 ++++
 2 files changed, 11 insertions(+)
..........................                  [100%]
26 passed, 389 subtests passed in 0.23s
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff", "description": "Show final diff of changes"}
[tool_result] diff --git a/sqlglot/parser.py b/sqlglot/parser.py
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
+            TokenType.SEQU
…[685 chars elided]…
this'")
+        self.validate_identity("COMMENT ON TYPE foo.mood IS 'x'")
+        self.validate_identity("COMMENT ON VIEW foo.bat IS 'x'")
+        self.validate_identity("COMMENT ON SEQUENCE foo.seq IS 'x'")
+        self.validate_identity("COMMENT ON INDEX foo.idx IS 'x'")
         self.validate_identity("SELECT e'\\xDEADBEEF'")
         self.validate_identity("SELECT CAST(e'\\176' AS BYTEA)")
         self.validate_identity("SELECT * FROM x WHERE SUBSTRING('Thomas' FROM '...$') IN ('mas')")
[assistant] `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip unchanged. The full suite passes (1112 tests) and ruff is clean.

**Cause:** `_parse_comment` in `sqlglot/parser.py` read the target for these kinds with `_parse_id_var()`, which takes a single identifier. It stopped at the `.`, so the parser then expected `IS` and failed. `TABLE` already used the table-aware path.

**Fix:** these four kinds now go through `_parse_table_parts()`, the same helper used for table names, so they accept `schema.name`. Other kinds (`FUNCTION`, `SCHEMA`, `DATABASE`, etc.) are unchanged.

**Tests:** I added round-trip cases for `COMMENT ON TYPE foo.mood`, `VIEW foo.bat`, `SEQUENCE foo.seq` and `INDEX foo.idx` to `tests/dialects/test_postgres.py`. No existing test was modified.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask for one.
