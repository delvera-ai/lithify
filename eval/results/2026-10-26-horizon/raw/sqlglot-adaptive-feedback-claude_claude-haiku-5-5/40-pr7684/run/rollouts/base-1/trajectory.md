# trajectory base-1

final message:
`COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip when the target is schema-qualified. The full suite finished with `SUMMARY: 1112 passed, 18158 subtests passed in 50.90s` and `EXIT: 0`, taken after my last edit.

**The fix:** in `Parser._parse_comment` (`sqlglot/parser.py`), the fallback branch for object kinds that aren't FUNCTION, PROCEDURE, TABLE or COLUMN used `_parse_id_var()`, which stops at the dot. It now uses `_parse_table_parts()`, the same parser TABLE already uses, so `foo.mood` becomes a `Table` with `db=foo`.

**Shape change to review:** the fallback now applies to every kind routed there, not only the four you named. Unqualified targets such as `COMMENT ON TYPE mood` and `COMMENT ON DATABASE d` now produce `exp.Table(this=Identifier)` where they used to produce a bare `Identifier`. The generated SQL is unchanged, and nothing in `sqlglot/` reads `Comment.this`. If you'd rather keep the old shape for unqualified names, I can narrow the change to the four kinds or keep the `Identifier` when there's no dot.

**Tests:** I added round-trip identities for the four forms to `tests/dialects/test_postgres.py`, next to the existing `COMMENT ON TABLE` cases. I did not add an assertion on the node shape.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn -i \"comment\" sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py sqlglot/parser.py | grep -i \"on\\b\\|COMMENT_ON\\|_parse_comment\" | head -40; cat .lithify/harness/skills/sqlglot-ddl-statements/SKILL.md | head -80", "description": "Find COMMENT ON parsing code and read DDL skill"}
[tool_result] sqlglot/parser.py:1087:        TokenType.COMMENT: lambda self: self._parse_comment(),
sqlglot/parser.py:1353:        "COMMENT": lambda self: self.expression(
sqlglot/parser.py:1912:    def _add_comments(self, expression: exp.Expr | None) -> None:
sqlglot/parser.py:1913:        if expression and self._prev_comments:
sqlglot/parser.py:1914:            expression.add_comments(self._prev_comments)
sqlglot/parser.py:1923:            self._add_comments(expression)
sqlglot/parser.py:2178:    def _parse
…[5875 chars elided]…
whatever your parser printed.

## Done means, read from output after your last edit
- For every form the task names, `repr()` of the parsed `exp.Create` shows `this` = the name
  (`Table`, no Schema unless the columns precede `AS`) and `expression` = the body node.
- Each form round-trips in the dialect, and transpiling to one other dialect still prints
  `AS <body>`, not the body glued onto the name.
- Unsupported variants still parse as `exp.Command`, and existing CREATE TABLE/VIEW tests pass.
[tool_use Bash] {"command": "sed -n 2170,2215p sqlglot/parser.py; grep -n \"_parse_comment\\|COMMENT\" sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/*.py | head -30; grep -n \"COMMENT ON\" tests/dialects/test_postgres.py | head -30", "description": "Read base COMMENT parser and find postgres COMMENT tests"}
[tool_result]     def _parse_command(self) -> exp.Command:
        self._warn_unsupported()
        comments = self._prev_comments
        return self.expression(
            exp.Command(this=self._prev.text.upper(), expression=self._parse_string()),
            comments=comments,
        )

    def _parse_comment(self, allow_exists: bool = True) -> exp.Expr:
        start = self._prev
        exists = self._parse_exists() if allow_exists else None

        self._match(TokenType.ON)

        materialized = se
…[916 chars elided]…
(
        self,
    ) -> exp.ToTableProperty:
        table = self._parse_table_parts(schema=True)
        return self.expression(exp.ToTableProperty(this=table))

sqlglot/expressions/properties.py:591:        "COMMENT": SchemaCommentProperty,
70:        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
71:        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
241:            "COMMENT ON TABLE mytable IS $$doc this$$", "COMMENT ON TABLE mytable IS 'doc this'"
[tool_use Bash] {"command": "grep -n \"def comment_sql\" -A25 sqlglot/generator.py; grep -rn \"COMMENT ON\" tests/ | grep -v \"COMMENT ON TABLE\" | head -30; grep -n \"CREATABLES = \" -A25 sqlglot/parser.py | head -40; grep -n \"class Comment\" -A12 sqlglot/expressions/*.py", "description": "Inspect comment generator, tests, CREATABLES, Comment class"}
[tool_result] 3980:    def comment_sql(self, expression: exp.Comment) -> str:
3981-        this = self.sql(expression, "this")
3982-        kind = expression.args["kind"]
3983-        materialized = " MATERIALIZED" if expression.args.get("materialized") else ""
3984-        exists_sql = " IF EXISTS " if expression.args.get("exists") else " "
3985-        expression_sql = self.sql(expression, "expression")
3986-        return f"COMMENT{exists_sql}ON{materialized} {kind} {this} IS {expression_sql}"
3987-
3988- 
…[2574 chars elided]…
ue,
sqlglot/expressions/ddl.py-301-        "kind": True,
sqlglot/expressions/ddl.py-302-        "expression": True,
sqlglot/expressions/ddl.py-303-        "exists": False,
sqlglot/expressions/ddl.py-304-        "materialized": False,
sqlglot/expressions/ddl.py-305-    }
sqlglot/expressions/ddl.py-306-
sqlglot/expressions/ddl.py-307-
sqlglot/expressions/ddl.py-308-class Comprehension(Expression):
sqlglot/expressions/ddl.py-309-    arg_types = {
sqlglot/expressions/ddl.py-310-        "this": True,
[tool_use Bash] {"command": "cat > /tmp/probe_comment.py <<'EOF'\nfrom sqlglot import parse_one, parse\nfor sql in [\"COMMENT ON TYPE foo.mood IS 'x'\", \"COMMENT ON VIEW foo.bat IS 'x'\", \"COMMENT ON SEQUENCE foo.s IS 'x'\", \"COMMENT ON INDEX foo.i IS 'x'\", \"COMMENT ON TYPE mood IS 'x'\", \"COMMENT ON TABLE foo.bar IS 'x'\", \"COMMENT ON DATABASE d IS 'x'\"]:\n    try:\n        e = parse_one(sql, read=\"post
…[39 chars elided]…
\"), \"|\", type(e.this).__name__, repr(e.this)[:80])\n    except Exception as ex:\n        print(\"ERR\", sql, type(ex).__name__, str(ex)[:120])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_comment.py", "description": "Reproduce COMMENT ON failures in postgres"}
[tool_result] ERR COMMENT ON TYPE foo.mood IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON TYPE
ERR COMMENT ON VIEW foo.bat IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 20.
  COMMENT ON VIEW
ERR COMMENT ON SEQUENCE foo.s IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 24.
  COMMENT ON SEQU
ERR COMMENT ON INDEX foo.i IS 'x' ParseError Required keyword: 'expression' missing for <class 'sqlglot.expressions.ddl.Comment'>. Line 1, Col: 21.
  COMMENT ON INDE
COMMENT ON TYPE mood IS 'x' | Identifier Identifier(this=mood, quoted=False)
COMMENT ON TABLE foo.bar IS 'x' | Table Table(
  this=Identifier(this=bar, quoted=False),
  db=Identifier(this=foo, quot
COMMENT ON DATABASE d IS 'x' | Identifier Identifier(this=d, quoted=False)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-102015-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py", "old_string": "        elif kind.token_type == TokenType.COLUMN:\n            this = self._parse_column()\n        else:\n            this = self._parse_id_var()", "new_string": "        elif kind.token_type == TokenType.COLUMN:\n            this = self._parse_column()\n        else:\n            this = self._parse_table_parts()"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-102015-postgres-dialect-comment-on-fail/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_comment.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py tests/test_transpile.py tests/test_parser.py tests/test_expressions.py 2>&1 | tail -15", "description": "Re-run probe and targeted test files"}
[tool_result] COMMENT ON TYPE foo.mood IS 'x' | Table Table(
  this=Identifier(this=mood, quoted=False),
  db=Identifier(this=foo, quo
COMMENT ON VIEW foo.bat IS 'x' | Table Table(
  this=Identifier(this=bat, quoted=False),
  db=Identifier(this=foo, quot
COMMENT ON SEQUENCE foo.s IS 'x' | Table Table(
  this=Identifier(this=s, quoted=False),
  db=Identifier(this=foo, quoted
COMMENT ON INDEX foo.i IS 'x' | Table Table(
  this=Identifier(this=i, quoted=False),
  db=Identifier(this=foo, quoted
COMMENT ON TYPE mo
…[60 chars elided]…
=False))
COMMENT ON TABLE foo.bar IS 'x' | Table Table(
  this=Identifier(this=bar, quoted=False),
  db=Identifier(this=foo, quot
COMMENT ON DATABASE d IS 'x' | Table Table(
  this=Identifier(this=d, quoted=False))
............................................................................. [ 40%]
............................... [ 57%]
.................................................................................                               [100%]
189 passed, 1509 subtests passed in 10.67s
[assistant] The probe passes and the targeted files are green. Since unqualified names now become `Table` rather than `Identifier`, I'll check whether anything consumes `exp.Comment.this` and add tests.
[tool_use Bash] {"command": "grep -rn \"exp.Comment\\b\\|Comment)\" sqlglot/ | grep -v CommentColumn | head; sed -n 66,74p tests/dialects/test_postgres.py", "description": "Find consumers of Comment node and test location"}
[tool_result] sqlglot/parser.py:2201:            exp.Comment(
sqlglot/generator.py:3980:    def comment_sql(self, expression: exp.Comment) -> str:
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y)")
        self.validate_identity("STRING_AGG(x, ',' ORDER BY y DESC)")
        self.validate_identity("STRING_AGG(DISTINCT x, ',' ORDER BY y DESC)")
        self.validate_identity("SELECT CASE WHEN SUBSTRING('abcdefg') IN ('ab') THEN 1 ELSE 0 END")
        self.validate_identity("COMMENT ON TABLE mytable IS 'this'")
        self.validate_identity("COMMENT ON MATERIALIZED VIEW my_view IS 'this'")
        self.validate_identity("SELECT e'\\xDEADBEEF'")
        self.validate_identity("SELECT CAST(e'\\176' AS BYTEA)")
        self.validate_identity("SELECT * FROM x WHERE SUBSTRING('Thomas' FROM '...$') IN ('mas')")
[assistant] Nothing else reads `Comment.this`. Adding round-trip tests next to the existing `COMMENT ON` identities:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-102015-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n", "new_string": "        self.validate_identity(\"COMMENT ON MATERIALIZED VIEW my_view IS 'this'\")\n        self.validate_identity(\"COMMENT ON TYPE foo.mood IS 'x'\")\n        self.validate_identity(\"COMMENT ON VIEW foo.bat IS 'x'\")\n        self.validate_identity(\"COMMENT ON SEQUENCE foo.s IS 'x'\")\n        self.validate_identity(\"COMMENT ON INDEX foo.i IS 'x'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-102015-postgres-dialect-comment-on-fail/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py tests/dialects/test_postgres.py 2>&1 | tail -5; $PY -m ruff check sqlglot/parser.py tests/dialects/test_postgres.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Run postgres tests and lint checks"}
[tool_result] RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/dialects/test_postgres.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-e40ee01c19.log
ELAPSED: 1s
SUMMARY: 26 passed, 389 subtests passed in 0.32s
EXIT: 0
All checks passed!
177 files already formatted
[assistant] Postgres tests pass and lint is clean. Now the full suite, run in the foreground as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:49:48 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  88748       00:35 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-e40ee01c19.log
ELAPSED: 51s
SUMMARY: 1112 passed, 18158 subtests passed in 50.90s
EXIT: 0
[assistant] `COMMENT ON TYPE`, `VIEW`, `SEQUENCE` and `INDEX` now parse and round-trip when the target is schema-qualified. The full suite finished with `SUMMARY: 1112 passed, 18158 subtests passed in 50.90s` and `EXIT: 0`, taken after my last edit.

**The fix:** in `Parser._parse_comment` (`sqlglot/parser.py`), the fallback branch for object kinds that aren't FUNCTION, PROCEDURE, TABLE or COLUMN used `_parse_id_var()`, which stops at the dot. It now uses `_parse_table_parts()`, the same parser TABLE already uses, so `foo.mood` becomes a `Table` with `db=foo`.

**Shape change to review:** the fallback now
…[74 chars elided]…
ied targets such as `COMMENT ON TYPE mood` and `COMMENT ON DATABASE d` now produce `exp.Table(this=Identifier)` where they used to produce a bare `Identifier`. The generated SQL is unchanged, and nothing in `sqlglot/` reads `Comment.this`. If you'd rather keep the old shape for unqualified names, I can narrow the change to the four kinds or keep the `Identifier` when there's no dot.

**Tests:** I added round-trip identities for the four forms to `tests/dialects/test_postgres.py`, next to the existing `COMMENT ON TABLE` cases. I did not add an assertion on the node shape.

Nothing is committed.
