# trajectory base-1

final message:
`ON CONFLICT` targets can now contain expressions, so your example parses and round-trips.

**The fix:** in `sqlglot/parser.py`, `_parse_on_conflict` parsed the conflict target with `_parse_id_var`, which accepts only bare identifiers. I changed it to `_parse_assignment`, so `(col_x, lower(col_y))` parses. The optional `WHERE` on the target was already handled, and it works with expression targets too.

**Output:**
```
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```
The same parse also works for `postgres` and `duckdb`, since the change is in the shared parser. Because the generator already emits `ON CONFLICT(` with no space, that's the canonical form the test expects.

**Tests:** I added `test_upsert_conflict_target` to `tests/dialects/test_sqlite.py`. It covers your example and a target with a `WHERE` clause plus `DO NOTHING`. The full suite passes (1122 tests, 18178 subtests), and `ruff check` and `ruff format --check` are clean on both files.

I didn't run `make check` or the C-extension tests (`make testc`).

## events
[tool_use Bash] {"command": "grep -n \"ON CONFLICT\\|OnConflict\\|conflict\" sqlglot/parser.py | head -60; grep -n \"class OnConflict\" -A 12 sqlglot/expressions.py; grep -rn \"OnConflict\\|ON CONFLICT\\|conflict\" sqlglot/generator.py sqlglot/dialects/sqlite.py | head -30", "description": "Locate ON CONFLICT handling in parser and generator"}
[tool_result] 3512:                conflict=self._parse_on_conflict(),
3533:    def _parse_on_conflict(self) -> exp.OnConflict | None:
3534:        conflict = self._match_text_seq("ON", "CONFLICT")
3537:        if not conflict and not duplicate:
3540:        conflict_keys = None
3543:        if conflict:
3547:                conflict_keys = self._parse_csv(self._parse_id_var)
3560:            exp.OnConflict(
3564:                conflict_keys=conflict_keys,
7496:                on_conflict=self._parse_on_conf
…[877 chars elided]…
ICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if conflict_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
[tool_use Bash] {"command": "sed -n 3533,3575p sqlglot/parser.py; sed -n 2296,2320p sqlglot/generator.py; grep -n \"class OnConflict\" -A 12 sqlglot/expressions/*.py", "description": "Show ON CONFLICT parser and generator code"}
[tool_result]     def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        if not conflict and not duplicate:
            return None

        conflict_keys = None
        constraint = None

        if conflict:
            if self._match_text_seq("ON", "CONSTRAINT"):
                constraint = self._parse_id_var()
            elif self._match(TokenType.L_PAREN):
              
…[2288 chars elided]…
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
[tool_use Bash] {"command": "cat > /tmp/repro_oc.py <<'EOF'\nimport sqlglot\nsql = \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z\"\nfor d in [\"sqlite\", \"postgres\", \"duckdb\"]:\n    try:\n        print(d, sqlglot.transpile(sql, read=d, write=d)[0])\n    except Exception as e:\n        print(d, \"ERR\", type(e
…[100 chars elided]…
er(b)) WHERE b > 0 DO NOTHING\"\nprint(sqlglot.transpile(sql2, read=\"sqlite\", write=\"sqlite\")[0])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_oc.py; grep -n \"def _parse_assignment\\|def _parse_conjunction\\|def _parse_disjunction\\|def _parse_expression\" sqlglot/parser.py", "description": "Reproduce ON CONFLICT parse failure across dialects"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_oc.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
5765:    def _parse_expression(self) -> exp.Expr | None:
5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
5802:    def _parse_conjunction(self) -> exp.Expr | None:
8624:    def _parse_expressions(self) -> list[exp.Expr]:
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I /tmp/repro_oc.py", "description": "Rerun repro with repo on the import path"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/repro_oc.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "ls <work>/env-sqlglot/lib/python*/site-packages | grep -i sqlglot; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"import sys; print(sys.path)\"", "description": "Inspect env site-packages for sqlglot install"}
[tool_result] sqlglot_mypy-2.3.0.post2.dist-info
['', '~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/repro_oc.py", "description": "Run repro script with repo on PYTHONPATH"}
[tool_result ERROR] Exit code 1
sqlite ERR ParseError Expecting ). Line 1, Col: 101.
postgres ERR ParseError Expecting ). Line 1, Col: 101.
duckdb ERR ParseError Expecting ). Line 1, Col: 101.
Traceback (most recent call last):
  File "/tmp/repro_oc.py", line 9, in <module>
    print(sqlglot.transpile(sql2, read="sqlite", write="sqlite")[0])
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/b
…[2613 chars elided]…
ithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", line 9414, in _match_r_paren
    self.raise_error("Expecting )")
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", line 2002, in raise_error
    raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 57.
  INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT (a, lower[4m([0mb)) WHERE b > 0 DO NOTHING
[tool_use Bash] {"command": "grep -rn \"conflict_keys\" sqlglot tests | head; grep -rln \"ON CONFLICT\" tests | head", "description": "Find conflict_keys usages and ON CONFLICT tests"}
[tool_result] sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3564:                conflict_keys=conflict_keys,
sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if conflict_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/expressions/dml.py:270:        "conflict_keys": False,
tests/dialects/test_sqlite.py
tests/dialects/test_materialize.py
tests/dialects/test_postgres.py
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_assignment)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/repro_oc.py", "description": "Rerun repro after parser fix"}
[tool_result] sqlite INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
postgres INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
duckdb INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO NOTHING
[assistant] Parsing and round-trip now work. Next I'll add a regression test next to the existing SQLite upsert tests and run the suite.
[tool_use Bash] {"command": "grep -n \"ON CONFLICT\" -B2 -A3 tests/dialects/test_sqlite.py | head -60", "description": "Show existing ON CONFLICT tests in sqlite suite"}
[tool_result] 287-    def test_ddl(self):
288-        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
291-
292-        self.validate_identity("CREATE TABLE over (x, y)")
293-        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
[tool_use Bash] {"command": "grep -n \"def test_\\|^class\" tests/dialects/test_sqlite.py | head -40; grep -rn \"ON CONFLICT\" tests/dialects/test_postgres.py | head -5", "description": "List sqlite test methods and postgres conflict tests"}
[tool_result] 7:class TestSQLite(Validator):
10:    def test_sqlite(self):
209:    def test_strftime(self):
232:    def test_datediff(self):
246:    def test_hexadecimal_literal(self):
255:    def test_window_null_treatment(self):
263:    def test_longvarchar_dtype(self):
269:    def test_warnings(self):
278:    def test_trunc(self):
287:    def test_ddl(self):
380:    def test_analyze(self):
384:    def test_create_trigger(self):
tests/dialects/test_postgres.py:1199:            "INSERT INTO book (isbn, title
…[184 chars elided]…
able AS t(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1"
tests/dialects/test_postgres.py:1251:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO NOTHING RETURNING *"
tests/dialects/test_postgres.py:1254:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = 1 RETURNING *"
tests/dialects/test_postgres.py:1257:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = excluded.id RETURNING *"
[tool_use Bash] {"command": "sed -n 286,296p tests/dialects/test_sqlite.py", "description": "View start of sqlite ddl test"}
[tool_result]     def test_ddl(self):
        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
            with self.subTest(f"ON CONFLICT {conflict_action}"):
                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")

        self.validate_identity("CREATE TABLE over (x, y)")
        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_ddl(self):\n        for conflict_action", "new_string": "    def test_upsert_conflict_target(self):\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\",\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO NOTHING\",\n        )\n\n    def test_ddl(self):\n        for conflict_action"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-102923-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite with project's interpreter"}
[tool_result] ..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
.........
…[129 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
....                                                                     [100%]
1122 passed, 18178 subtests passed in 50.16s
[assistant] All 1122 tests pass. I'll run the linter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files; show status"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[assistant] `ON CONFLICT` targets can now contain expressions, so your example parses and round-trips.

**The fix:** in `sqlglot/parser.py`, `_parse_on_conflict` parsed the conflict target with `_parse_id_var`, which accepts only bare identifiers. I changed it to `_parse_assignment`, so `(col_x, lower(col_y))` parses. The optional `WHERE` on the target was already handled, and it works with expression targets too.

**Output:**
```
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```
The same parse also works for `postgres` and `duckdb`, since the change is in the shared parser. Because the generator already emits `ON CONFLICT(` with no space, that's the canonical form the test expects.

**Tests:** I added `test_upsert_conflict_target` to `tests/dialects/test_sqlite.py`. It covers your example and a target with a `WHERE` clause plus `DO NOTHING`. The full suite passes (1122 tests, 18178 subtests), and `ruff check` and `ruff format --check` are clean on both files.

I didn't run `make check` or the C-extension tests (`make testc`).
