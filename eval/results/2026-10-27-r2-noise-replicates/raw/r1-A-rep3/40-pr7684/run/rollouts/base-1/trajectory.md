# trajectory base-1

final message:
`COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip unchanged. The full suite passes (1112 tests) and ruff is clean.

**The cause:** `_parse_comment` in `sqlglot/parser.py` read these kinds with `_parse_id_var`, which stops at the dot. The parser then expected `IS` and failed on `.mood`. `TABLE` already used `_parse_table`, which is why it worked.

**The fix:** I added one branch in `_parse_comment` that sends `TYPE`, `VIEW`, `SEQUENCE` and `INDEX` through `_parse_table_parts()`. It is in the generic parser rather than the Postgres dialect, so other dialects that use these kinds also accept qualified names. Ruff reformatted the new `elif` onto multiple lines.

**Tests:** I added four `validate_identity` cases to `tests/dialects/test_postgres.py` next to the existing `COMMENT ON` cases, one per kind. Each uses a schema-qualified name.

I haven't committed anything. The branch has the two modified files unstaged.

## events
[tool_use Bash] {"command": "rtk grep -n \"COMMENT\" sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py | head -50; rtk grep -rn \"COMMENT ON\" tests/dialects/test_postgres.py | head -30", "description": "Find COMMENT ON handling in parser, generator, tests"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"COMMENT\" sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py | head -50; echo ---; grep -n \"COMMENT ON\" tests/dialects/test_postgres.py tests/dialects/*.py | head -30", "description": "Find COMMENT ON handling in parser, generator, tests"}
[tool_result] sqlglot/generator.py:159:        exp.CommentColumnConstraint: lambda self, e: f"COMMENT {self.sql(e, 'this')}",
sqlglot/generator.py:781:    WITH_SEPARATED_COMMENTS: t.ClassVar[tuple[type[exp.Expr], ...]] = (
sqlglot/generator.py:802:    EXCLUDE_COMMENTS: t.ClassVar[tuple[type[exp.Expr], ...]] = (
sqlglot/generator.py:1006:        if not comments or isinstance(expression, self.EXCLUDE_COMMENTS):
sqlglot/generator.py:1018:        if separated or isinstance(expression, self.WITH_SEPARATED_COMMENTS
…[1075 chars elided]…
ew IS 'this'")
tests/dialects/test_postgres.py:241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
tests/dialects/test_postgres.py:70:        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
tests/dialects/test_postgres.py:71:        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
tests/dialects/test_postgres.py:241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
[tool_use Bash] {"command": "sed -n 8675,8720p sqlglot/parser.py; echo ---; sed -n 3970,3990p sqlglot/generator.py; echo ---; grep -n \"_parse_comment_on\\|def _parse_comment\" sqlglot/parser.py sqlglot/dialects/*.py", "description": "Show COMMENT ON parser and generator code"}
[tool_result]             return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)

        # Many dialects support the ALTER [COLUMN] syntax, so if there is no
        # keyword after ALTER we default to parsing this statement
        self._match(TokenType.COLUMN)
        column = self._parse_field(any_token=True)

        if self._match_pair(TokenType.DROP, TokenType.DEFAULT):
            return self.expression(exp.AlterColumn(this=column, drop=True))
        if self._match_pair(TokenType.SET, TokenTy
…[2424 chars elided]…
_sql = " IF EXISTS " if expression.args.get("exists") else " "
        expression_sql = self.sql(expression, "expression")
        return f"COMMENT{exists_sql}ON{materialized} {kind} {this} IS {expression_sql}"

    def mergetreettlaction_sql(self, expression: exp.MergeTreeTTLAction) -> str:
        this = self.sql(expression, "this")
        delete = " DELETE" if expression.args.get("delete") else ""
---
sqlglot/parser.py:2178:    def _parse_comment(self, allow_exists: bool = True) -> exp.Expr:
[tool_use Bash] {"command": "sed -n 2178,2230p sqlglot/parser.py; echo ---; grep -n \"COMMENT\" sqlglot/dialects/postgres.py; grep -n \"Comment(\" sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head", "description": "Show _parse_comment implementation"}
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
…[1124 chars elided]…
(exp.MergeTreeTTLAction(this=this, delete=True))
            if self._match_text_seq("RECOMPRESS"):
                return self.expression(
                    exp.MergeTreeTTLAction(this=this, recompress=self._parse_bitwise())
                )
            if self._match_text_seq("TO", "DISK"):
                return self.expression(
                    exp.MergeTreeTTLAction(this=this, to_disk=self._parse_string())
                )
---
sqlglot/expressions/ddl.py:298:class Comment(Expression):
[tool_use Bash] {"command": "grep -n \"CREATABLES\" -A 22 sqlglot/parser.py | head -40; grep -n \"def _parse_table_parts\" -A3 sqlglot/parser.py; cat > /tmp/repro_comment.py <<'EOF'\nfrom sqlglot import parse_one\nfor sql in [\"COMMENT ON TYPE foo.mood IS 'x';\", \"COMMENT ON VIEW foo.bat IS 'x';\", \"COMMENT ON SEQUENCE foo.s IS 'x';\", \"COMMENT ON INDEX foo.i IS 'x';\", \"COMMENT ON TABLE foo.bar IS 'x'\"]:\n    e = parse_one(sql, read=\"postgres\")\n    print(type(e).__name__, e.sql(\"postgres\"))\nEOF\npython3 -I /tmp/repro_comment.py 2>&1 | tail -8", "description": "Check creatable kinds and reproduce failures"}
[tool_result] 619:    DB_CREATABLES: t.ClassVar = {
620-        TokenType.DATABASE,
621-        TokenType.DICTIONARY,
622-        TokenType.FILE_FORMAT,
623-        TokenType.MODEL,
624-        TokenType.NAMESPACE,
625-        TokenType.SCHEMA,
626-        TokenType.SEMANTIC_VIEW,
627-        TokenType.SEQUENCE,
628-        TokenType.SINK,
629-        TokenType.SOURCE,
630-        TokenType.STAGE,
631-        TokenType.STORAGE_INTEGRATION,
632-        TokenType.STREAMLIT,
633-        TokenType.TABLE,
634-    
…[640 chars elided]…
:    def _parse_table_parts_fast(self) -> exp.Table | None:
4609-        index = self._index
4610-        parts: list[exp.Identifier] | None = None
4611-        all_comments: list[str] | None = None
--
4671:    def _parse_table_parts(
4672-        self,
4673-        schema: bool = False,
4674-        is_db_reference: bool = False,
Traceback (most recent call last):
  File "/tmp/repro_comment.py", line 1, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/repro_comment.py 2>&1 | tail -8", "description": "Reproduce COMMENT ON failures with project python"}
[tool_result]     instance = self.validate_expression(instance)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", line 2004, in validate_expression
    self.raise_error(error_message)
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", line 1993, in raise_error
    raise error
sqlglot.errors.ParseError: Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON TYPE foo[4m.[0mmood IS 'x';
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type == TokenType.COLUMN:", "new_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type in (TokenType.TYPE, TokenType.VIEW, TokenType.SEQUENCE, TokenType.INDEX):\n            this = self._parse_table_parts()\n        elif kind.token_type == TokenType.COLUMN:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 66,74p tests/dialects/test_postgres.py", "description": "View existing COMMENT ON tests"}
[tool_result]         self.validate_identity("STRING_AGG(x, ',' ORDER BY y)")
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y DESC)")
        self.validate_identity("STRING_AGG(DISTINCT x, ',' ORDER BY y DESC)")
        self.validate_identity("SELECT CASE WHEN SUBSTRING('abcdefg') IN ('ab') THEN 1 ELSE 0 END")
        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
        self.validate_identity("SELECT e'\\xDEADBEEF'")
        self.validate_identity("SELECT CAST(e'\\176' AS BYTEA)")
        self.validate_identity("SELECT * FROM x WHERE SUBSTRING('Thomas' FROM '...$') IN ('mas')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.seq IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.idx IS 'x'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132228-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/repro_comment.py 2>&1 | tail -8; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py tests/test_parser.py tests/test_transpile.py 2>&1 | tail -5", "description": "Verify fix and run postgres/parser tests"}
[tool_result] Comment COMMENT ON TYPE foo.mood IS 'x'
Comment COMMENT ON VIEW foo.bat IS 'x'
Comment COMMENT ON SEQUENCE foo.s IS 'x'
Comment COMMENT ON INDEX foo.i IS 'x'
Comment COMMENT ON TABLE foo.bar IS 'x'
........................................................................................................................                                                       [100%]
120 passed, 1482 subtests passed in 10.75s
[assistant] Both examples now parse and round-trip. Next I'll run the full project check suite and the style linter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; ls $(dirname $PY) | grep -i \"ruff\\|mypy\"; $(dirname $PY)/ruff check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3; $(dirname $PY)/ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -3", "description": "Run full test suite and ruff checks"}
[tool_result] ........................................................................ [ 91%]
.................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 51.06s
dmypy
mypy
mypyc
ruff
All checks passed!
Would reformat: sqlglot/parser.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/ruff; $R format sqlglot/parser.py && git diff --stat && git diff sqlglot/parser.py && PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -1", "description": "Apply ruff format and recheck diff and postgres tests"}
[tool_result] 1 file reformatted
 sqlglot/parser.py               | 7 +++++++
 tests/dialects/test_postgres.py | 4 ++++
 2 files changed, 11 insertions(+)
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
26 passed, 389 subtests passed in 0.20s
[assistant] `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip unchanged. The full suite passes (1112 tests) and ruff is clean.

**The cause:** `_parse_comment` in `sqlglot/parser.py` read these kinds with `_parse_id_var`, which stops at the dot. The parser then expected `IS` and failed on `.mood`. `TABLE` already used `_parse_table`, which is why it worked.

**The fix:** I added one branch in `_parse_comment` that sends `TYPE`, `VIEW`, `SEQUENCE` and `INDEX` through `_parse_table_parts()`. It is in the generic parser rather than the Postgres dialect, so other dialects that use these kinds also accept qualified names. Ruff reformatted the new `elif` onto multiple lines.

**Tests:** I added four `validate_identity` cases to `tests/dialects/test_postgres.py` next to the existing `COMMENT ON` cases, one per kind. Each uses a schema-qualified name.

I haven't committed anything. The branch has the two modified files unstaged.
