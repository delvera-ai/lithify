# trajectory base-1

final message:
`ON CONFLICT` targets with expressions now parse and round-trip. The full suite passes (1121 tests), and `ruff` lint and format checks are clean.

The bug was in `_parse_on_conflict` in `sqlglot/parser.py`. The conflict target list was parsed with `_parse_id_var`, so `lower(col_y)` failed. I changed it to `_parse_assignment`, so each target item can be any expression. A `WHERE` predicate on the target was already parsed and only needed the column list fixed.

Your example now produces:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

This holds for sqlite, postgres and duckdb. The `WHERE` on the target also works, e.g. `ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO NOTHING`.

I added regression tests to `tests/dialects/test_sqlite.py` (`test_ddl`) and `tests/dialects/test_postgres.py` (`test_ddl`). I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"CONFLICT\" sqlglot/parser.py sqlglot/dialects/*.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Find ON CONFLICT handling in source"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:1582:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:3534:        conflict = self._match_text_seq("ON", "CONFLICT")
sqlglot/parser.py:3552:        action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/parser.py:9197:                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/generator.py:2297:        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
[tool_use Bash] {"command": "sed -n 3525,3590p sqlglot/parser.py && echo ---- && sed -n 2290,2330p sqlglot/generator.py && echo ---- && grep -n \"class OnConflict\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Read conflict parsing and generation code"}
[tool_result ERROR] Exit code 2
            this.set("alias", self._parse_table_alias())
        return this

    def _parse_kill(self) -> exp.Kill:
        kind = exp.var(self._prev.text) if self._match_texts(("CONNECTION", "QUERY")) else None

        return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))

    def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        
…[3993 chars elided]…
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
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres','duckdb']:\n    try: print(d, sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', str(e)[:200])\nq2='''INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO NOTHING'''\ntry: print(sqlglot.transpile(q2, read='sqlite', write='sqlite')[0])\nexcept Exception as e: print('ERR', str(e)[:300])\n\"; grep -rn \"conflict_keys\\|ON CONFLICT (\" tests/ | head -30", "description": "Reproduce ON CONFLICT parse failures across dialects"}
[tool_result] sqlite ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
postgres ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
duckdb ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
ERR Expecting ). Line 1, Col: 51.
  INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower[4m([0mb)) WHERE a > 0 DO NOTHING
[tool_use Bash] {"command": "grep -rn \"ON CONFLICT\" tests/ | head -40; grep -n \"def _parse_assignment\\|def _parse_disjunction\\|def _parse_expression\\|def _parse_id_var\" sqlglot/parser.py", "description": "Find existing ON CONFLICT tests and parse helpers"}
[tool_result] tests/dialects/test_materialize.py:16:            "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_materialize.py:19:                "postgres": "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_sqlite.py:289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT I
…[821 chars elided]…
 "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO NOTHING RETURNING *"
tests/dialects/test_postgres.py:1263:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO UPDATE SET x.id = 1 RETURNING *"
5765:    def _parse_expression(self) -> exp.Expr | None:
5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
8485:    def _parse_id_var(
8624:    def _parse_expressions(self) -> list[exp.Expr]:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)\n                self._match_r_paren()", "new_string": "                conflict_keys = self._parse_csv(self._parse_assignment)\n                self._match_r_paren()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres','duckdb']:\n    print(d, sqlglot.transpile(q, read=d, write=d)[0])\nq2='''INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO NOTHING'''\nprint(sqlglot.transpile(q2, read='sqlite', write='sqlite')[0])\nprint(sqlglot.transpile('INSERT INTO t (a) VALUES (1) ON CONFLICT (\\\"A\\\", lower(\\\"B\\\")) DO NOTHING', read='postgres', write='postgres')[0])\nprint(sqlglot.transpile(q2, read='sqlite', write='postgres')[0])\n\"", "description": "Verify fixed parsing and round-trip output"}
[tool_result] sqlite INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
postgres INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
duckdb INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO NOTHING
INSERT INTO t (a) VALUES (1) ON CONFLICT("A", LOWER("B")) DO NOTHING
INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO NOTHING
[assistant] Parsing and round-trip now work. Next I'll add regression tests to the SQLite and Postgres dialect test files.
[tool_use Bash] {"command": "grep -n \"def test_\\|INSERT\" tests/dialects/test_sqlite.py | head -60; sed -n 1195,1205p tests/dialects/test_postgres.py", "description": "Locate test methods in sqlite and postgres tests"}
[tool_result] 10:    def test_sqlite(self):
101:            "INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
103:                "mysql": "INSERT IGNORE INTO foo (x, y) VALUES (1, 2)",
104:                "sqlite": "INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
209:    def test_strftime(self):
232:    def test_datediff(self):
246:    def test_hexadecimal_literal(self):
255:    def test_window_null_treatment(self):
263:    def test_longvarchar_dtype(self):
269:    def test_warnings(self):
278:    def test_
…[1129 chars elided]…
)")
        self.validate_identity(
            "INSERT INTO book (isbn, title) VALUES ($1, $2) ON CONFLICT(isbn) WHERE deleted_at IS NULL DO UPDATE SET title = EXCLUDED.title RETURNING id, isbn"
        )
        self.validate_identity(
            "INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1"
        )
        self.validate_identity(
            "ALTER TABLE tested_table ADD CONSTRAINT unique_example UNIQUE (column_name) NOT VALID"
[tool_use Bash] {"command": "sed -n 286,300p tests/dialects/test_sqlite.py", "description": "View sqlite ddl test section"}
[tool_result]     def test_ddl(self):
        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
            with self.subTest(f"ON CONFLICT {conflict_action}"):
                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")

        self.validate_identity("CREATE TABLE over (x, y)")
        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)")
        self.validate_identity("CREATE TEMPORARY TABLE foo (id INTEGER)")
        self.validate_identity("CREATE VIRTUAL TABLE docs USING fts5(title, content)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)\")\n        self.validate_identity(\"CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)\")", "new_string": "        self.validate_
…[73 chars elided]…
elf.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) VALUES (1, 2, 3) ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO NOTHING\"\n        )\n        self.validate_identity(\"CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1\"\n        )", "new_string": "        self.validate_identity(\n            \"INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1\"\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b IS NOT NULL DO NOTHING\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now the full test suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite"}
[tool_result]             "INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b IS NOT NULL DO NOTHING"
        )

tests/dialects/test_postgres.py:1204: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/dialects/test_dialect.py:63: in validate_identity
    self.assertEqual(
E   AssertionError: 'INSE[24 chars](1, 2) ON CONFLICT(a, LOWER(b)) WHERE b IS NOT NULL DO NOTHING' != 'INSE[24 chars](1, 2) ON CONFLICT(a, LOWER(b)) WHERE NOT b IS NULL DO NOTHING'
E   -
…[64 chars elided]…
RE b IS NOT NULL DO NOTHING
E   ?                                                                   -----
E   + INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE NOT b IS NULL DO NOTHING
E   ?                                                                      +++++
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_ddl - AssertionErr...
1 failed, 1120 passed, 18163 subtests passed in 51.73s
[assistant] That failure is my test's fault, not the parser: sqlglot normalizes `IS NOT NULL` to `NOT b IS NULL`. I'll use a simpler predicate.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py", "old_string": "ON CONFLICT(a, LOWER(b)) WHERE b IS NOT NULL DO NOTHING\"", "new_string": "ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO NOTHING\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141136-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_sqlite.py tests/dialects/test_postgres.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects 2>&1 | tail -3; git status --short", "description": "Rerun tests, lint and format check"}
[tool_result] .......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 50.36s
All checks passed!
210 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_postgres.py
 M tests/dialects/test_sqlite.py
[assistant] `ON CONFLICT` targets with expressions now parse and round-trip. The full suite passes (1121 tests), and `ruff` lint and format checks are clean.

The bug was in `_parse_on_conflict` in `sqlglot/parser.py`. The conflict target list was parsed with `_parse_id_var`, so `lower(col_y)` failed. I changed it to `_parse_assignment`, so each target item can be any expression. A `WHERE` predicate on the target was already parsed and only needed the column list fixed.

Your example now produces:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

This holds for sqlite, postgres and duckdb. The `WHERE` on the target also works, e.g. `ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO NOTHING`.

I added regression tests to `tests/dialects/test_sqlite.py` (`test_ddl`) and `tests/dialects/test_postgres.py` (`test_ddl`). I did not commit anything.
