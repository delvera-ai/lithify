# trajectory base-1

final message:
`INSERT ... ON CONFLICT (...)` now accepts expressions in the conflict target, and the query from your report parses and round-trips in both SQLite and Postgres.

**The fix:** in `_parse_on_conflict` (`sqlglot/parser.py`), the conflict target was parsed with `_parse_id_var`, which only accepts plain identifiers. I switched it to `_parse_assignment`, so `lower(col_y)` and similar expressions parse. The optional `WHERE` on the target was already handled, so no other change was needed.

**Output:**
```
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z
```

**Test:** I added a round-trip case to `test_sqlite` in `tests/dialects/test_sqlite.py`, covering the expression target with a `WHERE` predicate.

**Verification:**
- Full suite (`pytest` with the project's interpreter): 1121 passed, 18178 subtests passed.
- `ruff format --check` and `ruff check` pass on both changed files.

Two things to be aware of:
- Plain column targets now come back as `Column` nodes rather than `Identifier` nodes, since `_parse_assignment` is more general. The generated SQL is unchanged, and no existing test depended on the node type, but any downstream code that inspects `conflict_keys` will see the new type.
- I did not commit the change.

## events
[tool_use Bash] {"command": "grep -rn \"CONFLICT\" sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generator.py sqlglot/generators/*.py sqlglot/expressions/*.py | head -60", "description": "Find ON CONFLICT handling in parser/generator"}
[tool_result] sqlglot/parser.py:1582:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:3534:        conflict = self._match_text_seq("ON", "CONFLICT")
sqlglot/parser.py:3552:        action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/parser.py:9197:                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/generator.py:2297:        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
[tool_use Bash] {"command": "sed -n 3525,3580p sqlglot/parser.py && echo ---- && sed -n 2290,2330p sqlglot/generator.py && echo ---- && grep -n \"class OnConflict\" -A 12 sqlglot/expressions/*.py", "description": "Read ON CONFLICT parser and generator code"}
[tool_result]             this.set("alias", self._parse_table_alias())
        return this

    def _parse_kill(self) -> exp.Kill:
        kind = exp.var(self._prev.text) if self._match_texts(("CONNECTION", "QUERY")) else None

        return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))

    def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        if not confl
…[3545 chars elided]…
dml.py-268-        "expressions": False,
sqlglot/expressions/dml.py-269-        "action": False,
sqlglot/expressions/dml.py-270-        "conflict_keys": False,
sqlglot/expressions/dml.py-271-        "index_predicate": False,
sqlglot/expressions/dml.py-272-        "constraint": False,
sqlglot/expressions/dml.py-273-        "where": False,
sqlglot/expressions/dml.py-274-    }
sqlglot/expressions/dml.py-275-
sqlglot/expressions/dml.py-276-
sqlglot/expressions/dml.py-277-class Returning(Expression):
[tool_use Bash] {"command": "grep -n \"def _parse_assignment\\|def _parse_disjunction\\|def _parse_conjunction\" sqlglot/parser.py; P=<work>/env-sqlglot/bin/python; ls $P 2>/dev/null; python3 -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres']:\n  try: print(sqlglot.transpile(s, read=d, write=d)[0])\n  except Exception as e: print(type(e).__name__, str(e)[:200])\n\"", "description": "Locate parse helpers and reproduce the failure"}
[tool_result] 5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
5802:    def _parse_conjunction(self) -> exp.Expr | None:
<work>/env-sqlglot/bin/python
ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col
ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101316-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)\n                self._match_r_paren()", "new_string": "                conflict_keys = self._parse_csv(self._parse_assignment)\n                self._match_r_paren()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101316-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres']:\n  print(sqlglot.transpile(s, read=d, write=d)[0])\nprint(sqlglot.transpile('INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) DO NOTHING', read='postgres', write='sqlite')[0])\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix round-trips and run the test suite"}
[tool_result] INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z
INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) DO NOTHING
................................................ [ 32%]
.........................................................
…[416 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 52.46s
[assistant] The fix works and the full suite passes (1121 tests). Now I'll add a regression test next to the existing upsert tests.
[tool_use Bash] {"command": "grep -rn \"ON CONFLICT\" tests/dialects/test_sqlite.py | head; grep -n \"def test_\" tests/dialects/test_sqlite.py | head -5", "description": "Find existing ON CONFLICT tests in sqlite suite"}
[tool_result] tests/dialects/test_sqlite.py:289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
10:    def test_sqlite(self):
209:    def test_strftime(self):
232:    def test_datediff(self):
246:    def test_hexadecimal_literal(self):
255:    def test_window_null_treatment(self):
[tool_use Bash] {"command": "sed -n 200,210p tests/dialects/test_sqlite.py; grep -rn \"ON CONFLICT\" tests/dialects/test_postgres.py | head -3", "description": "View test insertion point and postgres conflict tests"}
[tool_result]             "ATTACH 'foo' || '.foo2' AS schema_name",
        )
        self.validate_identity("DETACH DATABASE schema_name", "DETACH schema_name")
        self.validate_identity("SELECT * FROM t WHERE NULL IS y")
        self.validate_identity(
            "SELECT * FROM t WHERE NULL IS NOT y", "SELECT * FROM t WHERE NOT NULL IS y"
        )
        self.validate_identity("SELECT SQLITE_VERSION()")

    def test_strftime(self):
        self.validate_identity("SELECT STRFTIME('%Y/%m/%d', 'now')")
tests/dialects/test_postgres.py:1199:            "INSERT INTO book (isbn, title) VALUES ($1, $2) ON CONFLICT(isbn) WHERE deleted_at IS NULL DO UPDATE SET title = EXCLUDED.title RETURNING id, isbn"
tests/dialects/test_postgres.py:1202:            "INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1"
tests/dialects/test_postgres.py:1251:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO NOTHING RETURNING *"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101316-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"SELECT SQLITE_VERSION()\")\n\n    def test_strftime(self):", "new_string": "        self.validate_identity(\"SELECT SQLITE_VERSION()\")\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_x > 0 DO UPDATE SET col_z = excluded.col_z\"\n        )\n\n    def test_strftime(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101316-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py 2>&1 | tail -3; (ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py && ruff check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -3; git status --short", "description": "Run sqlite tests and lint changed files"}
[tool_result] ...........                                                             [100%]
11 passed, 73 subtests passed in 0.09s
2 files already formatted
All checks passed!
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[assistant] `INSERT ... ON CONFLICT (...)` now accepts expressions in the conflict target, and the query from your report parses and round-trips in both SQLite and Postgres.

**The fix:** in `_parse_on_conflict` (`sqlglot/parser.py`), the conflict target was parsed with `_parse_id_var`, which only accepts plain identifiers. I switched it to `_parse_assignment`, so `lower(col_y)` and similar expressions parse. The optional `WHERE` on the target was already handled, so no other change was needed.

**Output:**
```
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, L
…[142 chars elided]…
/test_sqlite.py`, covering the expression target with a `WHERE` predicate.

**Verification:**
- Full suite (`pytest` with the project's interpreter): 1121 passed, 18178 subtests passed.
- `ruff format --check` and `ruff check` pass on both changed files.

Two things to be aware of:
- Plain column targets now come back as `Column` nodes rather than `Identifier` nodes, since `_parse_assignment` is more general. The generated SQL is unchanged, and no existing test depended on the node type, but any downstream code that inspects `conflict_keys` will see the new type.
- I did not commit the change.
