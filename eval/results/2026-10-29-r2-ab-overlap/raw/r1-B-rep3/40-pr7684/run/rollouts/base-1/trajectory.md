# trajectory base-1

final message:
Schema-qualified `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip. The full suite passes (1112 tests) with the project's pytest command.

**Cause:** `_parse_comment` in `sqlglot/parser.py` handled `TABLE` and `COLUMN` specially, but everything else went through `_parse_id_var()`. That reads a single identifier, so it stopped at the dot in `foo.mood`, and the parser then failed on the missing `expression`.

**Fix:** I added a branch so those four kinds use `_parse_table_parts()`, the same parser `TABLE` targets use. It is in the base parser rather than the Postgres dialect, so it applies to every dialect that accepts these `COMMENT ON` forms.

**Tests:** I added the four statements to `validate_identity` in `tests/dialects/test_postgres.py`.

Unqualified names like `COMMENT ON TYPE mood` now produce a `Table` node where they used to produce an `Identifier`. The output SQL is unchanged.

`COMMENT ON INDEX IF EXISTS foo.i IS 'x'` still fails. The `IF EXISTS` placement is a separate existing quirk that also applies to `TABLE`, and it isn't valid Postgres syntax anyway, so I left it alone.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"COMMENT\\|Comment\" sqlglot/dialects/postgres.py | head -50; grep -n \"_parse_comment\\|def _parse_comment\" -A40 sqlglot/parser.py | head -80", "description": "Find COMMENT parsing code"}
[tool_result] 0 matches for 'COMMENT\|Comment'
1087:        TokenType.COMMENT: lambda self: self._parse_comment(),
1088-        TokenType.COMMIT: lambda self: self._parse_commit_or_rollback(),
1089-        TokenType.COPY: lambda self: self._parse_copy(),
1090-        TokenType.CREATE: lambda self: self._parse_create(),
1091-        TokenType.DELETE: lambda self: self._parse_delete(),
1092-        TokenType.DESC: lambda self: self._parse_describe(),
1093-        TokenType.DESCRIBE: lambda self: self._parse_des
…[3189 chars elided]…
ssion(
2201-            exp.Comment(
2202-                this=this,
2203-                kind=kind.text,
2204-                expression=self._parse_string(),
2205-                exists=exists,
2206-                materialized=materialized,
2207-            )
2208-        )
2209-
2210-    def _parse_to_table(
2211-        self,
2212-    ) -> exp.ToTableProperty:
2213-        table = self._parse_table_parts(schema=True)
2214-        return self.expression(exp.ToTableProperty(this=table))
2215-
[assistant] The `else` branch calls `_parse_id_var`, which takes a single identifier, so `foo.mood` stops at the dot. Let me check the generator and existing tests before changing it.
[tool_use Bash] {"command": "grep -n \"def comment_sql\" -A25 sqlglot/generator.py; grep -rn \"COMMENT ON\" tests/ | head -40; grep -n \"def _parse_table_parts\" -A3 sqlglot/parser.py", "description": "Inspect comment generator and existing tests"}
[tool_result] 3980:    def comment_sql(self, expression: exp.Comment) -> str:
3981-        this = self.sql(expression, "this")
3982-        kind = expression.args["kind"]
3983-        materialized = " MATERIALIZED" if expression.args.get("materialized") else ""
3984-        exists_sql = " IF EXISTS " if expression.args.get("exists") else " "
3985-        expression_sql = self.sql(expression, "expression")
3986-        return f"COMMENT{exists_sql}ON{materialized} {kind} {this} IS {expression_sql}"
3987-
3988- 
…[1861 chars elided]…
ity.sql:727:COMMENT ON TABLE my_schema.my_table IS 'Employee Information'
tests/fixtures/identity.sql:728:COMMENT ON TABLE my_schema.my_table IS N'National String'
4608:    def _parse_table_parts_fast(self) -> exp.Table | None:
4609-        index = self._index
4610-        parts: list[exp.Identifier] | None = None
4611-        all_comments: list[str] | None = None
--
4671:    def _parse_table_parts(
4672-        self,
4673-        schema: bool = False,
4674-        is_db_reference: bool = False,
[assistant] Reproducing the failures first, and checking which token types `COMMENT ON` accepts.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nfrom sqlglot import parse_one\nfor s in ['COMMENT ON TYPE foo.mood IS \\'x\\'','COMMENT ON VIEW foo.bat IS \\'x\\'','COMMENT ON SEQUENCE foo.s IS \\'x\\'','COMMENT ON INDEX foo.i IS \\'x\\'','COMMENT ON TYPE mood IS \\'x\\'','COMMENT ON TABLE foo.bar IS \\'x\\'']:\n    e = parse_one(s, read='postgres'); print(type(e.this).__name__, e.sql('postgres'))\n\" 2>&1 | tail -15; grep -n \"CREATABLES\" -A3 sqlglot/parser.py | head -8", "description": "Reproduce COMMENT ON parse failures"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
619:    DB_CREATABLES: t.ClassVar = {
620-        TokenType.DATABASE,
621-        TokenType.DICTIONARY,
622-        TokenType.FILE_FORMAT,
--
639:    CREATABLES: t.ClassVar = {
640-        TokenType.COLUMN,
641-        TokenType.CONSTRAINT,
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfor s in ['COMMENT ON TYPE foo.mood IS \\'x\\'','COMMENT ON VIEW foo.bat IS \\'x\\'','COMMENT ON SEQUENCE foo.s IS \\'x\\'','COMMENT ON INDEX foo.i IS \\'x\\'','COMMENT ON TYPE mood IS \\'x\\'','COMMENT ON TABLE foo.bar IS \\'x\\'']:\n    try:\n        e = parse_one(s, read='postgres'); print(type(e.this).__name__, e.sql('postgres'))\n    except Exception as ex: print('ERR', s, str(ex).splitlines()[0])\n\" 2>&1 | tail -15; sed -n 639,680p sqlglot/parser.py | tr -s ' ' | tr '\\n' ' '", "description": "Reproduce COMMENT ON parse failures with local sqlglot"}
[tool_result] ERR COMMENT ON TYPE foo.mood IS 'x' Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
ERR COMMENT ON VIEW foo.bat IS 'x' Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
ERR COMMENT ON SEQUENCE foo.s IS 'x' Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 24.
ERR COMMENT ON INDEX foo.i IS 'x' Required keyword: 'expression' missing for <class
…[397 chars elided]…
okenType.UPDATE,  TokenType.DELETE,  TokenType.TRUNCATE,  }   ALTERABLES: t.ClassVar = {  TokenType.INDEX,  TokenType.TABLE,  TokenType.VIEW,  TokenType.SESSION,  }   # Tokens that can represent identifiers  ID_VAR_TOKENS: t.ClassVar[set] = {  TokenType.ALL,  TokenType.ANALYZE,  TokenType.ATTACH,  TokenType.VAR,  TokenType.ANTI,  TokenType.APPLY,  TokenType.ASC,  TokenType.ASOF,  TokenType.AUTO_INCREMENT,  TokenType.BEGIN,  TokenType.BPCHAR,  TokenType.CACHE,  TokenType.CASE,  TokenType.COLLATE,
[assistant] The dotted name is the problem: `_parse_id_var` stops at the dot, so `IS` never matches and the required `expression` is missing. `TYPE`, `VIEW`, `SEQUENCE` and `INDEX` all reach the `else` branch, so I'll route them through `_parse_table_parts()`, the same way `TABLE` gets a qualified name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193945-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.COLUMN:\n            this = self._parse_column()\n        else:\n            this = self._parse_id_var()\n\n        self._match(TokenType.IS)", "new_string": "        elif kind.token_type == TokenType.COLUMN:\n            this = self._parse_column()\n        elif kind.token_type in (TokenType.INDEX, TokenType.SEQUENCE, TokenType.TYPE, TokenType.VIEW):\n            this = self._parse_table_parts()\n        else:\n            this = self._parse_id_var()\n\n        self._match(TokenType.IS)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193945-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll add regression tests to the Postgres dialect test file and run the reproduction again.
[tool_use Bash] {"command": "sed -n 66,74p tests/dialects/test_postgres.py", "description": "View existing COMMENT ON tests in postgres suite"}
[tool_result]         self.validate_identity("STRING_AGG(x, ',' ORDER BY y)")
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y DESC)")
        self.validate_identity("STRING_AGG(DISTINCT x, ',' ORDER BY y DESC)")
        self.validate_identity("SELECT CASE WHEN SUBSTRING('abcdefg') IN ('ab') THEN 1 ELSE 0 END")
        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
        self.validate_identity("SELECT e'\\xDEADBEEF'")
        self.validate_identity("SELECT CAST(e'\\176' AS BYTEA)")
        self.validate_identity("SELECT * FROM x WHERE SUBSTRING('Thomas' FROM '...$') IN ('mas')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193945-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.seq IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.idx IS 'x'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193945-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import parse_one\nfor s in ['COMMENT ON TYPE foo.mood IS \\'x\\'','COMMENT ON VIEW foo.bat IS \\'x\\'','COMMENT ON SEQUENCE foo.s IS \\'x\\'','COMMENT ON INDEX foo.i IS \\'x\\'','COMMENT ON TYPE mood IS \\'x\\'','COMMENT ON INDEX IF EXISTS foo.i IS \\'x\\'']:\n    try:\n        e = parse_one(s, read='postgres'); print(e.sql('postgres'))\n    except Exception as ex: print('ERR', s, str(ex).splitlines()[0])\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] COMMENT ON TYPE foo.mood IS 'x'
COMMENT ON VIEW foo.bat IS 'x'
COMMENT ON SEQUENCE foo.s IS 'x'
COMMENT ON INDEX foo.i IS 'x'
COMMENT ON TYPE mood IS 'x'
ERR COMMENT ON INDEX IF EXISTS foo.i IS 'x' Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 26.
.......................................................................................................................................................................................................
…[587 chars elided]…
5%]
................................................................................................................................................................................................ [ 82%]
............................ [ 85%]
........................................................................ [ 91%]
.................................................................................. [ 98%]
............                           [100%]
1112 passed, 18158 subtests passed in 47.21s
[assistant] All four statements now parse and round-trip, and the full suite passes (1112 tests). One of my new lines is probably over the project's line-length limit, so I'll run the formatter and linter.
[tool_use Bash] {"command": "(ruff format sqlglot/parser.py tests/dialects/test_postgres.py && ruff check sqlglot/parser.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git diff --stat; git diff sqlglot/parser.py", "description": "Format, lint, and review the diff"}
[tool_result] 1 file reformatted, 1 file left unchanged
Ruff: No issues found
sqlglot/parser.py               | 7 +++++++
 tests/dialects/test_postgres.py | 4 ++++
 2 files changed, 11 insertions(+)
sqlglot/parser.py | 7 +++++++
 1 file changed, 7 insertions(+)

--- Changes ---

sqlglot/parser.py
  @@ -2192,6 +2192,13 @@ class Parser:
  +        elif kind.token_type in (
  +            TokenType.INDEX,
  +            TokenType.SEQUENCE,
  +            TokenType.TYPE,
  +            TokenType.VIEW,
  +        ):
  +            this = self._parse_table_parts()
           else:
               this = self._parse_id_var()
   
  +7 -0
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] The formatter wrapped the new condition across lines. I'll re-run the Postgres tests after that change.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Run Postgres dialect tests after formatting"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.19s
[assistant] Schema-qualified `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip. The full suite passes (1112 tests) with the project's pytest command.

**Cause:** `_parse_comment` in `sqlglot/parser.py` handled `TABLE` and `COLUMN` specially, but everything else went through `_parse_id_var()`. That reads a single identifier, so it stopped at the dot in `foo.mood`, and the parser then failed on the missing `expression`.

**Fix:** I added a branch so those four kinds use `_parse_table_parts()`, the same parser `TABLE` targets use. It is in the base parser rather than the Postgres dialect, so it applies to every dialect that accepts these `COMMENT ON` forms.

**Tests:** I added the four statements to `validate_identity` in `tests/dialects/test_postgres.py`.

Unqualified names like `COMMENT ON TYPE mood` now produce a `Table` node where they used to produce an `Identifier`. The output SQL is unchanged.

`COMMENT ON INDEX IF EXISTS foo.i IS 'x'` still fails. The `IF EXISTS` placement is a separate existing quirk that also applies to `TABLE`, and it isn't valid Postgres syntax anyway, so I left it alone.

I haven't committed anything.
