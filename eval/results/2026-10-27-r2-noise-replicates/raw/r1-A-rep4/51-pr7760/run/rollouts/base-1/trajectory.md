# trajectory base-1

final message:
`ON CONFLICT` targets can now contain expressions, so your example parses and round-trips in SQLite, Postgres and DuckDB. The full test suite passes (1122 tests), and ruff lint and format checks are clean.

**Cause:** `_parse_on_conflict` in `sqlglot/parser.py` parsed the target items with `_parse_id_var`, which accepts only bare identifiers, so `lower(col_y)` failed with "Expecting )".

**Change:** I switched those items to `_parse_disjunction`, a general expression parser. The optional `WHERE` on the target was already parsed, so it works with expression targets too. Output:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

**Tests added:**
- `tests/dialects/test_sqlite.py`: `test_on_conflict_expression_target`, covering your example and a target with `WHERE b > 0`.
- `tests/dialects/test_postgres.py`: one identity case with an expression target.

I didn't commit anything. The three changed files are unstaged in the worktree.

## events
[tool_use Bash] {"command": "grep -rn \"ON CONFLICT\\|conflict_target\\|OnConflict\\|_parse_on_conflict\" sqlglot/ | head -60", "description": "Find ON CONFLICT handling in source"}
[tool_result] sqlglot/generator.py:2296:    def onconflict_sql(self, expression: exp.OnConflict) -> str:
sqlglot/generator.py:2297:        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
sqlglot/parser.py:3512:                conflict=self._parse_on_conflict(),
sqlglot/parser.py:3533:    def _parse_on_conflict(self) -> exp.OnConflict | None:
sqlglot/parser.py:3560:            exp.OnConflict(
sqlglot/parser.py:7496:                on_conflict=self._parse_on_conflict(),
sqlglot/expressions/dml.py:265:class OnConflict(Expression):
sqlglot/generators/materialize.py:28:        exp.OnConflict: lambda self, e: "",
[tool_use Bash] {"command": "sed -n 3530,3575p sqlglot/parser.py && echo ---- && sed -n 2290,2330p sqlglot/generator.py && echo ---- && sed -n 260,285p sqlglot/expressions/dml.py", "description": "Show parser, generator, and expression for OnConflict"}
[tool_result]         return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))

    def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        if not conflict and not duplicate:
            return None

        conflict_keys = None
        constraint = None

        if conflict:
            if self._match_text_seq("ON", "CONSTRAINT"):
                constraint = sel
…[2985 chars elided]…
=copy,
            **opts,
        )


class OnConflict(Expression):
    arg_types = {
        "duplicate": False,
        "expressions": False,
        "action": False,
        "conflict_keys": False,
        "index_predicate": False,
        "constraint": False,
        "where": False,
    }


class Returning(Expression):
    arg_types = {"expressions": True, "into": False}


class LoadData(Expression):
    arg_types = {
        "this": True,
        "local": False,
        "overwrite": False,
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres','duckdb']:\n  try: print(sqlglot.transpile(s, read=d, write=d)[0])\n  except Exception as e: print(d, type(e).__name__, str(e)[:200])\n\" ; grep -n \"def _parse_assignment\\|def _parse_disjunction\\|def _parse_conjunction\\|def _parse_bitwise\\|def _parse_ordered\\|def _parse_index_params\\|def _parse_wrapped_csv\" sqlglot/parser.py", "description": "Reproduce the ON CONFLICT parse failure"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
4551:    def _parse_index_params(self) -> exp.IndexParameters:
5471:    def _parse_ordered(
5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
5802:    def _parse_conjunction(self) -> exp.Expr | None:
6042:    def _parse_bitwise(self) -> exp.Expr | None:
8605:    def _parse_wrapped_csv(
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -I -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres','duckdb']:\n  try: print(sqlglot.transpile(s, read=d, write=d)[0])\n  except Exception as e: print(d, type(e).__name__, str(e)[:200])\n\"; sed -n 5768,5790p sqlglot/parser.py", "description": "Reproduce failure with repo sources on path"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
    def _parse_assignment(self) -> exp.Expr | None:
        this = self._parse_disjunction()
        if not this and self._next.token_type in self.ASSIGNMENT:
            # This allows us to parse <non-identifier token> := <expr>
            this = exp.column(
                t.cast(str, self._advance_any(ignore_reserved=True) and self._prev.text)
            )

        while self._match_set(self.ASSIGNMENT):
            if isinstance(this, exp.Column) and len(this.parts) == 1:
                this = this.this

            comments = self._prev_comments
            this = self.expression(
                self.ASSIGNMENT[self._prev.token_type](
                    this=this, expression=self._parse_assignment()
                ),
                comments=comments,
            )

        return this

    def _parse_disjunction(self) -> exp.Expr | None:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres','duckdb']:\n  try: print(sqlglot.transpile(s, read=d, write=d)[0])\n  except Exception as e: print(d, type(e).__name__, str(e)[:200])\n\"", "description": "Reproduce failure from repo directory"}
[tool_result] sqlite ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
postgres ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
duckdb ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
[assistant] Reproduced: the conflict target is parsed with `_parse_id_var`, so `lower(col_y)` fails. I'll switch the target items to a general expression parser and keep the existing optional `WHERE` handling.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_disjunction)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\ncases=['''INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z''',\n'''INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT (a, lower(b)) WHERE b > 0 DO UPDATE SET b = excluded.b''',\n'''INSERT INT
…[61 chars elided]…
\n'''INSERT INTO t (a) VALUES (1) ON CONFLICT (a) DO NOTHING''']\nfor s in cases:\n  for d in ['sqlite','postgres','duckdb']:\n    try: print(d, sqlglot.transpile(s, read=d, write=d)[0])\n    except Exception as e: print(d, type(e).__name__, str(e)[:200])\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects 2>&1 | tail -15", "description": "Verify fix on cases and run dialect tests"}
[tool_result] sqlite INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
postgres INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
duckdb INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
sqlite INSERT INTO t (a, b) VALUES (1, 2) 
…[1099 chars elided]…
......................................................................... [ 62%]
........................................................................................................................................................ [ 83%]
.................. [ 85%]
.................... [ 88%]
....................... [ 91%]
.............. [ 93%]
............ [ 95%]
..................................                                                 [100%]
735 passed, 11097 subtests passed in 2.65s
[assistant] The fix works for all three cases and the dialect suite passes. Now I'll add a regression test next to the existing upsert tests.
[tool_use Bash] {"command": "grep -rn \"ON CONFLICT\" tests/dialects/test_sqlite.py | head; grep -n \"def test_\" tests/dialects/test_sqlite.py | head -5", "description": "Locate existing ON CONFLICT tests in sqlite suite"}
[tool_result] tests/dialects/test_sqlite.py:289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
10:    def test_sqlite(self):
209:    def test_strftime(self):
232:    def test_datediff(self):
246:    def test_hexadecimal_literal(self):
255:    def test_window_null_treatment(self):
[tool_use Bash] {"command": "grep -rln \"ON CONFLICT\" tests/ | head; grep -rn \"ON CONFLICT (\" tests/dialects/*.py | head -5", "description": "Find existing ON CONFLICT test locations"}
[tool_result] tests/dialects/test_materialize.py
tests/dialects/test_postgres.py
tests/dialects/test_sqlite.py
[tool_use Bash] {"command": "grep -n \"CONFLICT\" tests/dialects/test_postgres.py tests/dialects/test_sqlite.py | head -20; sed -n 240,256p tests/dialects/test_sqlite.py", "description": "Show existing CONFLICT tests in postgres and sqlite"}
[tool_result] tests/dialects/test_sqlite.py:289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
tests/dialects/test_postgres.py:1199:            "INSERT INTO book (isbn, title) VALUES ($1, $2) ON CONFLICT(isbn) WHERE deleted_at IS NULL DO UPDATE SET title = EXCLUDED.title RETURNING id, isbn"
tests/dialects/test_postgres.py:1202:            "INSERT INTO newtable A
…[752 chars elided]…
O UPDATE SET x.id = 1 RETURNING *"
        )
        self.validate_all(
            "DATEDIFF(a, b, 'year')",
            write={"sqlite": "CAST((JULIANDAY(a) - JULIANDAY(b)) / 365.0 AS INTEGER)"},
        )

    def test_hexadecimal_literal(self):
        self.validate_all(
            "SELECT 0XCC",
            write={
                "sqlite": "SELECT x'CC'",
                "mysql": "SELECT x'CC'",
            },
        )

    def test_window_null_treatment(self):
        self.validate_all(
[tool_use Bash] {"command": "sed -n 1196,1206p tests/dialects/test_postgres.py; sed -n 1258,1268p tests/dialects/test_postgres.py", "description": "View postgres ON CONFLICT test block"}
[tool_result]         self.validate_identity("ALTER TABLE t1 SET TABLESPACE tablespace")
        self.validate_identity("ALTER TABLE t1 SET (fillfactor = 5, autovacuum_enabled = TRUE)")
        self.validate_identity(
            "INSERT INTO book (isbn, title) VALUES ($1, $2) ON CONFLICT(isbn) WHERE deleted_at IS NULL DO UPDATE SET title = EXCLUDED.title RETURNING id, isbn"
        )
        self.validate_identity(
            "INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET 
…[157 chars elided]…
 NOT VALID"
        )
        )
        self.validate_identity(
            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO NOTHING RETURNING *"
        )
        self.validate_identity(
            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO UPDATE SET x.id = 1 RETURNING *"
        )
        self.validate_identity(
            "DELETE FROM event USING sales AS s WHERE event.eventid = s.eventid RETURNING a"
        )
        self.validate_identity(
[assistant] I'll add a SQLite test for the expression target and the target `WHERE` clause, plus a Postgres identity check since the issue names other upsert dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_window_null_treatment(self):", "new_string": "    def test_on_conflict_expression_target(self):\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO UPDATE SET b = excluded.b\"\n        )\n\n    def test_window_null_treatment(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1\"\n        )", "new_string": "        self.validate_identity(\n            \"INSERT INTO newtable AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1\"\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) DO UPDATE SET b = EXCLUDED.b\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082508-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now the project's check command across the full suite.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ....................... [ 60%]
................................................................................................ [ 68%]
............................................... [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
....                                                                     [100%]
1122 passed, 18178 subtests passed in 62.77s (0:01:02)
 M sqlglot/parser.py
 M tests/dialects/test_postgres.py
 M tests/dialects/test_sqlite.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_sqlite.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py tests/dialects/test_postgres.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
3 files already formatted
[assistant] `ON CONFLICT` targets can now contain expressions, so your example parses and round-trips in SQLite, Postgres and DuckDB. The full test suite passes (1122 tests), and ruff lint and format checks are clean.

**Cause:** `_parse_on_conflict` in `sqlglot/parser.py` parsed the target items with `_parse_id_var`, which accepts only bare identifiers, so `lower(col_y)` failed with "Expecting )".

**Change:** I switched those items to `_parse_disjunction`, a general expression parser. The optional `WHERE` on the target was already parsed, so it works with expression targets too. Output:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

**Tests added:**
- `tests/dialects/test_sqlite.py`: `test_on_conflict_expression_target`, covering your example and a target with `WHERE b > 0`.
- `tests/dialects/test_postgres.py`: one identity case with an expression target.

I didn't commit anything. The three changed files are unstaged in the worktree.
