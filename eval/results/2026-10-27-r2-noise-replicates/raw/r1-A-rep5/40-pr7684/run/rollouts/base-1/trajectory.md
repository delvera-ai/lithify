# trajectory base-1

final message:
`COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip. The full suite passes (1112 tests), and the formatter is clean.

**Cause:** `_parse_comment` in `sqlglot/parser.py` parsed these kinds with `_parse_id_var`, which stops at the dot in `foo.mood`. The parser then failed on the missing `IS`/expression.

**Fix:** I added a branch for those four kinds that uses `_parse_table_parts()`, the same helper the parser already uses for qualified table names. `COMMENT ON TABLE` keeps its existing path.

**Tests:** I added four `validate_identity` cases to `tests/dialects/test_postgres.py`, one per kind, next to the existing `COMMENT ON TABLE`/`MATERIALIZED VIEW` checks.

**Choice to note:** the change lives in the shared parser, not the Postgres dialect, because `_parse_comment` is generic. Other dialects that use `COMMENT ON VIEW`/`INDEX` with qualified names will now parse them too. The existing suite passes across all dialects, so I didn't see a regression, but that's a behavior change beyond Postgres.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n -i \"comment\" sqlglot/dialects/postgres.py sqlglot/parser.py | head -60; grep -n -i \"COMMENT\" sqlglot/tokens.py | head", "description": "Find COMMENT handling in parser and postgres dialect"}
[tool_result] sqlglot/parser.py:320:        "_prev_comments",
sqlglot/parser.py:682:        TokenType.COMMENT,
sqlglot/parser.py:793:    COMMENT_TABLE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.IS}
sqlglot/parser.py:1087:        TokenType.COMMENT: lambda self: self._parse_comment(),
sqlglot/parser.py:1246:        "COMMENT": lambda self: self._parse_property_assignment(exp.SchemaCommentProperty),
sqlglot/parser.py:1353:        "COMMENT": lambda self: self.expression(
sqlglot/parser.py:1354:    
…[3910 chars elided]…
   COMMENTS: t.ClassVar[list[str | tuple[str, str]]]
89:    _COMMENTS: t.ClassVar[dict[str, str | None]]
116:        cls._COMMENTS = {
117:            **{c: None for c in cls.COMMENTS if isinstance(c, str)},
118:            **{c[0]: c[1] for c in cls.COMMENTS if not isinstance(c, str)},
119:            "{#": "#}",  # Ensure Jinja comments are tokenized correctly in all dialects
122:            cls._COMMENTS[cls.HINT_START] = "*/"
127:                *cls._COMMENTS,
197:    NESTED_COMMENTS = True
[tool_use Bash] {"command": "sed -n 2178,2215p sqlglot/parser.py; grep -n -i \"comment\" sqlglot/generator.py | grep -i \"def comment\\|Comment\" | head; grep -n -i \"COMMENT ON\" tests/dialects/*.py | head -20", "description": "Read _parse_comment and related tests"}
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
…[1292 chars elided]…
OMMENTS: t.ClassVar[tuple[type[exp.Expr], ...]] = (
842:        "comments",
867:        comments: bool = True,
882:        self.comments = comments
tests/dialects/test_postgres.py:70:        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
tests/dialects/test_postgres.py:71:        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
tests/dialects/test_postgres.py:241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
[tool_use Bash] {"command": "grep -n \"CREATABLES\" -A 20 sqlglot/parser.py | head -30; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in ['COMMENT ON TYPE foo.mood IS \\'x\\';', 'COMMENT ON VIEW foo.bat IS \\'x\\';', 'COMMENT ON SEQUENCE foo.s IS \\'x\\';', 'COMMENT ON INDEX foo.i IS \\'x\\';', 'COMMENT ON TYPE mood IS \\'x\\';']:\n    try: print(sqlglot.transpile(sql, read='postgres'))\n    except Exception as e: print('ERR', sql, type(e).__name__, str(e)[:150])\n\"", "description": "Check CREATABLES and reproduce the failures"}
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
…[713 chars elided]…
ressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON VIEW foo[4m.[0mbat IS 'x';
ERR COMMENT ON SEQUENCE foo.s IS 'x'; ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 24.
  COMMENT ON SEQUENCE foo[4m.[0ms IS 'x';
ERR COMMENT ON INDEX foo.i IS 'x'; ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 21.
  COMMENT ON INDEX foo[4m.[0mi IS 'x';
["COMMENT ON TYPE mood IS 'x'"]
[tool_use Bash] {"command": "grep -n \"def comment_sql\" -A 25 sqlglot/generator.py; grep -n \"def _parse_table_parts\" -A3 sqlglot/parser.py", "description": "Inspect comment generator and table parts parser"}
[tool_result] 3980:    def comment_sql(self, expression: exp.Comment) -> str:
3981-        this = self.sql(expression, "this")
3982-        kind = expression.args["kind"]
3983-        materialized = " MATERIALIZED" if expression.args.get("materialized") else ""
3984-        exists_sql = " IF EXISTS " if expression.args.get("exists") else " "
3985-        expression_sql = self.sql(expression, "expression")
3986-        return f"COMMENT{exists_sql}ON{materialized} {kind} {this} IS {expression_sql}"
3987-
3988- 
…[932 chars elided]…
gates = self.seg("SET") + self.seg(aggregates) if aggregates else ""
4004-
4005-        if not (where or group or aggregates) and len(expression.expressions) == 1:
4608:    def _parse_table_parts_fast(self) -> exp.Table | None:
4609-        index = self._index
4610-        parts: list[exp.Identifier] | None = None
4611-        all_comments: list[str] | None = None
--
4671:    def _parse_table_parts(
4672-        self,
4673-        schema: bool = False,
4674-        is_db_reference: bool = False,
[assistant] The failure is in `_parse_comment`: the generic branch uses `_parse_id_var`, which stops at the dot in `foo.mood`. I'll route the four qualifiable kinds through `_parse_table_parts`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121619-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type == TokenType.COLUMN:", "new_string": "        elif kind.token_type == TokenType.TABLE:\n            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)\n        elif kind.token_type in (TokenType.INDEX, TokenType.SEQUENCE, TokenType.TYPE, TokenType.VIEW):\n            this = self._parse_table_parts()\n        elif kind.token_type == TokenType.COLUMN:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121619-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in ['COMMENT ON TYPE foo.mood IS \\'x\\';', 'COMMENT ON VIEW foo.bat IS \\'x\\';', 'COMMENT ON SEQUENCE foo.s IS \\'x\\';', 'COMMENT ON INDEX foo.i IS \\'x\\';', 'COMMENT ON TYPE mood IS \\'x\\';', 'COMMENT ON TABLE foo.bar IS \\'x\\';']:\n    print(sqlglot.transpile(sql, read='postgres'))\n\"; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix and run full test suite"}
[tool_result] ["COMMENT ON TYPE foo.mood IS 'x'"]
["COMMENT ON VIEW foo.bat IS 'x'"]
["COMMENT ON SEQUENCE foo.s IS 'x'"]
["COMMENT ON INDEX foo.i IS 'x'"]
["COMMENT ON TYPE mood IS 'x'"]
["COMMENT ON TABLE foo.bar IS 'x'"]
............................ [ 85%]
........................................................................ [ 91%]
.................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 53.88s
[assistant] All four now parse and round-trip, and the full suite passes. Next I'll add regression tests next to the existing `COMMENT ON` identity tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121619-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "offset": 68, "limit": 5}
[tool_result] 68	        self.validate_identity("STRING_AGG(DISTINCT x, ',' ORDER BY y DESC)")
69	        self.validate_identity("SELECT CASE WHEN SUBSTRING('abcdefg') IN ('ab') THEN 1 ELSE 0 END")
70	        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
71	        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
72	        self.validate_identity("SELECT e'\\xDEADBEEF'")
[tool_use Bash] {"command": "git status --short", "description": "Check working tree status"}
[tool_result]  M sqlglot/parser.py
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121619-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.seq IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.idx IS 'x'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121619-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Rerun full test suite and show diff stat"}
[tool_result] .................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 51.42s
 sqlglot/parser.py               | 2 ++
 tests/dialects/test_postgres.py | 4 ++++
 2 files changed, 6 insertions(+)
[assistant] The new `elif` line may exceed the project's line length, so I'll run the formatter check.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff format --check sqlglot/parser.py tests/dialects/test_postgres.py || $PY -m ruff format sqlglot/parser.py && git diff sqlglot/parser.py) 2>&1 | tail -20", "description": "Check formatting of changed files"}
[tool_result] 1 file would be reformatted, 1 file already formatted
1 file reformatted
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index f7295acdf..1a382fb6b 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -2190,6 +2190,13 @@ class Parser:
             this = self._parse_user_defined_function(kind=kind.token_type)
         elif kind.token_type == TokenType.TABLE:
             this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
+        elif kind.token_type in (
+            TokenType.INDEX,
+            TokenType.SEQUENCE,
+            TokenType.TYPE,
+            TokenType.VIEW,
+        ):
+            this = self._parse_table_parts()
         elif kind.token_type == TokenType.COLUMN:
             this = self._parse_column()
         else:
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot tests/dialects/test_postgres.py && $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Confirm formatting and rerun tests"}
[tool_result] 177 files already formatted
1112 passed, 18158 subtests passed in 54.03s
[assistant] `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now accept schema-qualified targets and round-trip. The full suite passes (1112 tests), and the formatter is clean.

**Cause:** `_parse_comment` in `sqlglot/parser.py` parsed these kinds with `_parse_id_var`, which stops at the dot in `foo.mood`. The parser then failed on the missing `IS`/expression.

**Fix:** I added a branch for those four kinds that uses `_parse_table_parts()`, the same helper the parser already uses for qualified table names. `COMMENT ON TABLE` keeps its existing path.

**Tests:** I added four `validate_identity` cases to `tests/dialects/test_postgres.py`, one per kind, next to the existing `COMMENT ON TABLE`/`MATERIALIZED VIEW` checks.

**Choice to note:** the change lives in the shared parser, not the Postgres dialect, because `_parse_comment` is generic. Other dialects that use `COMMENT ON VIEW`/`INDEX` with qualified names will now parse them too. The existing suite passes across all dialects, so I didn't see a regression, but that's a behavior change beyond Postgres.

The changes are uncommitted in the worktree.
