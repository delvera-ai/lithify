# trajectory base-1

final message:
`ON CONFLICT` targets can now contain expressions, so the statement from your report parses and round-trips in SQLite and Postgres.

**Cause:** `_parse_on_conflict` in `sqlglot/parser.py` parsed the target list with `_parse_id_var`, which accepts only bare names. `lower(col_y)` broke it with "Expecting )".

**Change:** The target list now uses `_parse_assignment`, which parses full expressions, including plain column names. The optional `WHERE` on the target was already parsed, so it needed no change.

**Tests:** I added two identity round-trips to `tests/dialects/test_sqlite.py` in `test_ddl`. One covers the expression target from your report. The other adds a `WHERE` predicate on the target. The full suite passes (1121 tests), and `ruff format --check` and `ruff check` are clean on the changed files.

Nothing is committed. The changes are in the working tree, and I can commit them with the model suffix in the title if you want.

## events
[tool_use Bash] {"command": "grep -rn \"CONFLICT\\|conflict\" sqlglot/parser.py sqlglot/expressions.py sqlglot/generator.py sqlglot/dialects/sqlite.py sqlglot/dialects/postgres.py | head -80", "description": "Find ON CONFLICT handling in parser, generator, and dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:1260:        on_conflict = self.sql(expression, "on_conflict")
sqlglot/generator.py:1261:        on_conflict = f" {on_conflict}" if on_conflict else ""
sqlglot/generator.py:1265:        return f"UNIQUE{nulls_sql}{this}{index_type}{on_conflict}{options}"
sqlglot/generator.py:2258:        on_conflict = self.sql(expression, "conflict")
sqlglot/generator.py:2259:        on_conflict = f" {on_conflict}" if on_confli
…[1270 chars elided]…
:        conflict_keys = None
sqlglot/parser.py:3543:        if conflict:
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3552:        action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/parser.py:3564:                conflict_keys=conflict_keys,
sqlglot/parser.py:7496:                on_conflict=self._parse_on_conflict(),
sqlglot/parser.py:9197:                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
[tool_use Bash] {"command": "sed -n 3530,3575p sqlglot/parser.py && echo ---- && sed -n 2294,2320p sqlglot/generator.py && echo ---- && grep -n \"class OnConflict\" -A 14 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; grep -rn \"ON CONFLICT\\|on_conflict\" tests/dialects/test_sqlite.py tests/dialects/test_postgres.py | head -30", "description": "Inspect OnConflict parser, generator, and tests"}
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
…[3814 chars elided]…
'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = 1 RETURNING *"
tests/dialects/test_postgres.py:1257:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = excluded.id RETURNING *"
tests/dialects/test_postgres.py:1260:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO NOTHING RETURNING *"
tests/dialects/test_postgres.py:1263:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO UPDATE SET x.id = 1 RETURNING *"
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python; PYTHONPATH=. python3 -c \"\nimport sqlglot\ns='''INSERT INTO tbl_a (col_x, col_y, col_z)\nSELECT x, y, z FROM src WHERE true\nON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'''\nfor d in ['sqlite','postgres']:\n    try: print(sqlglot.transpile(s, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', str(e)[:200])\n\"; grep -n \"def _parse_assignment\\|def _parse_disjunction\\|def _parse_conjunction\\|def _parse_ordered\\|def _parse_bitwise\\|def _parse_lambda\\|def _parse_expression\" sqlglot/parser.py", "description": "Reproduce the ON CONFLICT parse failure"}
[tool_result] <work>/env-sqlglot/bin/python
sqlite ERR Expecting ). Line 3, Col: 26.
  INSERT INTO tbl_a (col_x, col_y, col_z)
SELECT x, y, z FROM src WHERE true
ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
postgres ERR Expecting ). Line 3, Col: 26.
  INSERT INTO tbl_a (col_x, col_y, col_z)
SELECT x, y, z FROM src WHERE true
ON CONFLICT (col_x, lower[4m(
…[48 chars elided]…
5471:    def _parse_ordered(
5765:    def _parse_expression(self) -> exp.Expr | None:
5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
5802:    def _parse_conjunction(self) -> exp.Expr | None:
6042:    def _parse_bitwise(self) -> exp.Expr | None:
7158:    def _parse_lambda_arg(self) -> exp.Expr | None:
7161:    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
8624:    def _parse_expressions(self) -> list[exp.Expr]:
[tool_use Bash] {"command": "grep -rn \"conflict_keys\" --include=*.py . | grep -v \"^./tests/fixtures\" ", "description": "Find all uses of conflict_keys"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"conflict_keys\" sqlglot tests | head", "description": "Find all uses of conflict_keys"}
[tool_result] sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if conflict_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3564:                conflict_keys=conflict_keys,
sqlglot/expressions/dml.py:270:        "conflict_keys": False,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_assignment)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "                self.validate_identity(\"CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)\")", "new_string": "                self.validate_identity(\"CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[assistant] I accidentally added a stray blank line to `test_sqlite.py`. Reverting that and finding the right spot for a real test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "                self.validate_identity(\"CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)\")\n\n", "new_string": "                self.validate_identity(\"CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "git diff --stat && grep -n \"def test_\\|INSERT\" tests/dialects/test_sqlite.py | head -40", "description": "Verify revert and list sqlite test methods"}
[tool_result]  sqlglot/parser.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
10:    def test_sqlite(self):
101:            "INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
103:                "mysql": "INSERT IGNORE INTO foo (x, y) VALUES (1, 2)",
104:                "sqlite": "INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
209:    def test_strftime(self):
232:    def test_datediff(self):
246:    def test_hexadecimal_literal(self):
255:    def test_window_null_treatment(self):
263:    def test_lo
…[459 chars elided]…
     self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
380:    def test_analyze(self):
384:    def test_create_trigger(self):
387:            "CREATE TRIGGER log_insert AFTER INSERT ON users BEGIN INSERT INTO audit_log (user_id, action, created_at) VALUES (NEW.id, 'INSERT', datetime('now')) END",
397:            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view BEGIN INSERT INTO employees (id, name, department) VALUES (NEW.id, NEW.name, NEW.department) END",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "offset": 286, "limit": 14}
[tool_result] 286	
287	    def test_ddl(self):
288	        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
289	            with self.subTest(f"ON CONFLICT {conflict_action}"):
290	                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
291	
292	        self.validate_identity("CREATE TABLE over (x, y)")
293	        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
294	        self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 2)")
295	        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
296	        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
297	        self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
298	        self.validate_identity("CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)")
299	        self.validate_identity("CREATE TEMPORARY TABLE foo (id INTEGER)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)\")\n        self.validate_identity(\"CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)\")", "new_string": "        self.validate_
…[185 chars elided]…
 ON CONFLICT (col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT (col_x, LOWER(col_y)) WHERE col_z IS NOT NULL DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\"CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfor s in ['INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) WHERE col_z IS NOT NULL DO UPDATE SET col_z = excluded.col_z', 'INSERT INTO x VALUES (1) ON CONFLICT(id) DO NOTHING']:\n  print(sqlglot.transpile(s, read='sqlite', write='sqlite')[0])\n  print(sqlglot.transpile(s, read='postgres', write='postgres')[0])\n\"", "description": "Check round-trip output for expression conflict targets"}
[tool_result] INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE NOT col_z IS NULL DO UPDATE SET col_z = excluded.col_z
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE NOT col_z IS NULL DO UPDATE SET col_z = excluded.col_z
INSERT INTO x VALUES (1) ON CONFLICT(id) DO NOTHING
INSERT INTO x VALUES (1) ON CONFLICT(id) DO NOTHING
[assistant] Round-trip works. Two details in my test strings need fixing to match the existing generator output: no space before `(`, and `IS NOT NULL` normalizes to `NOT ... IS NULL`, so I'll use a non-normalizing predicate.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT (col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n
…[275 chars elided]…
ty(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_z > 0 DO UPDATE SET col_z = excluded.col_z\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-184526-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PYTHON=<work>/env-sqlglot/bin/python; $PYTHON -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run sqlite and postgres dialect tests"}
[tool_result] .....................................      [100%]
37 passed, 462 subtests passed in 0.27s
[assistant] Targeted tests pass. Now the full suite, as the project harness specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[39 chars elided]…
.................................. [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 80.66s (0:01:20)
[assistant] All 1121 tests pass. Checking lint on the changed files.
[tool_use Bash] {"command": "(ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py && ruff check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git diff", "description": "Lint changed files and show diff"}
[tool_result] 2 files already formatted
All checks passed!
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 9fa6b9261..2010ff893 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -3544,7 +3544,7 @@ class Parser:
             if self._match_text_seq("ON", "CONSTRAINT"):
                 constraint = self._parse_id_var()
             elif self._match(TokenType.L_PAREN):
-                conflict_keys = self._parse_csv(self._parse_id_var)
+                conflict_keys = self._parse_csv(self._par
…[750 chars elided]…
T col_z = excluded.col_z"
+        )
+        self.validate_identity(
+            "INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) WHERE col_z > 0 DO UPDATE SET col_z = excluded.col_z"
+        )
         self.validate_identity("CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)")
         self.validate_identity("CREATE TEMPORARY TABLE foo (id INTEGER)")
         self.validate_identity("CREATE VIRTUAL TABLE docs USING fts5(title, content)")
[assistant] `ON CONFLICT` targets can now contain expressions, so the statement from your report parses and round-trips in SQLite and Postgres.

**Cause:** `_parse_on_conflict` in `sqlglot/parser.py` parsed the target list with `_parse_id_var`, which accepts only bare names. `lower(col_y)` broke it with "Expecting )".

**Change:** The target list now uses `_parse_assignment`, which parses full expressions, including plain column names. The optional `WHERE` on the target was already parsed, so it needed no change.

**Tests:** I added two identity round-trips to `tests/dialects/test_sqlite.py` in `test_ddl`. One covers the expression target from your report. The other adds a `WHERE` predicate on the target. The full suite passes (1121 tests), and `ruff format --check` and `ruff check` are clean on the changed files.

Nothing is committed. The changes are in the working tree, and I can commit them with the model suffix in the title if you want.
