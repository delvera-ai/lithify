# trajectory base-1

final message:
`ON CONFLICT` targets can now contain expressions, so the query from the report parses and round-trips in SQLite, Postgres and DuckDB:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

The cause was in `_parse_on_conflict` (`sqlglot/parser.py`): the conflict-target list was parsed with `_parse_id_var`, which accepts only bare identifiers. I changed it to `_parse_assignment`, the general expression parser. A `WHERE` on the target already worked and still does.

- **Test:** added `test_upsert` to `tests/dialects/test_sqlite.py`, covering the reported query and a target with both an expression and a `WHERE` predicate.
- **Results:** full suite passes (1122 tests, 18178 subtests). `ruff check` and `ruff format --check` are clean on both files.
- **Side effect:** conflict targets are now parsed as general expressions rather than identifiers. Plain column targets such as `ON CONFLICT(id)` still round-trip unchanged. Nothing else in the repo reads `conflict_keys`, so no other code is affected.

I haven't committed anything. Only `sqlglot/parser.py` and `tests/dialects/test_sqlite.py` are modified.

## events
[tool_use Bash] {"command": "grep -n \"ON CONFLICT\\|_parse_on_conflict\\|conflict_keys\\|index_predicate\\|OnConflict\" sqlglot/parser.py sqlglot/expressions.py sqlglot/generator.py sqlglot/dialects/*.py | head -80", "description": "Find ON CONFLICT handling in parser, expressions, generator"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:2296:    def onconflict_sql(self, expression: exp.OnConflict) -> str:
sqlglot/generator.py:2297:        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if conflict_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({con
…[440 chars elided]…
.OnConflict | None:
sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3550:        index_predicate = self._parse_where()
sqlglot/parser.py:3560:            exp.OnConflict(
sqlglot/parser.py:3564:                conflict_keys=conflict_keys,
sqlglot/parser.py:3565:                index_predicate=index_predicate,
sqlglot/parser.py:7496:                on_conflict=self._parse_on_conflict(),
[tool_use Bash] {"command": "sed -n 3530,3570p sqlglot/parser.py && sed -n 2294,2320p sqlglot/generator.py && grep -n \"class OnConflict\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Show ON CONFLICT parser and generator code"}
[tool_result ERROR] Exit code 2

        return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))

    def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        if not conflict and not duplicate:
            return None

        conflict_keys = None
        constraint = None

        if conflict:
            if self._match_text_seq("ON", "CONSTRAINT"):
                con
…[2226 chars elided]…
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
[assistant] Parser reads conflict keys with `_parse_id_var`, so an expression like `lower(col_y)` fails there. Let me reproduce before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'\nfor d in ['sqlite','postgres','duckdb']:\n    try: print(d, sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', type(e).__name__, str(e)[:200])\nq2='INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING'\nprint(sqlglot.transpile(q2, read='sqlite', write='sqlite')[0])\n\"", "description": "Reproduce ON CONFLICT expression parse failure"}
[tool_result] sqlite ERR ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
postgres ERR ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
duckdb ERR ParseError Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO t (a) VALUES (1) ON CONFLICT(a) WHERE a > 0 DO NOTHING
[assistant] Reproduced: the key list only accepts bare identifiers. Next I'll find the general-expression parser method this version uses.
[tool_use Bash] {"command": "grep -n \"def _parse_assignment\\|def _parse_disjunction\\|def _parse_expression\\|def _parse_conjunction\" sqlglot/parser.py && grep -rn \"ON CONFLICT\" tests/ | head -20", "description": "Locate expression parser methods and existing ON CONFLICT tests"}
[tool_result] 5765:    def _parse_expression(self) -> exp.Expr | None:
5768:    def _parse_assignment(self) -> exp.Expr | None:
5790:    def _parse_disjunction(self) -> exp.Expr | None:
5802:    def _parse_conjunction(self) -> exp.Expr | None:
8624:    def _parse_expressions(self) -> list[exp.Expr]:
tests/dialects/test_materialize.py:16:            "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_materialize.py:19:                "postgres": "INSERT INTO exa
…[851 chars elided]…
stgres.py:1260:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO NOTHING RETURNING *"
tests/dialects/test_postgres.py:1263:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT ON CONSTRAINT pkey DO UPDATE SET x.id = 1 RETURNING *"
tests/dialects/test_sqlite.py:289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
[tool_use Bash] {"command": "grep -rn \"conflict_keys\\|index_predicate\" --include=*.py . | grep -v \"^./tests/fixtures\" ", "description": "Find all uses of conflict_keys and index_predicate"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"conflict_keys\\|index_predicate\" sqlglot tests | grep -v fixtures", "description": "Find all uses of conflict_keys and index_predicate"}
[tool_result] sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3550:        index_predicate = self._parse_where()
sqlglot/parser.py:3564:                conflict_keys=conflict_keys,
sqlglot/parser.py:3565:                index_predicate=index_predicate,
sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if 
…[6 chars elided]…
ct_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2306:        index_predicate = self.sql(expression, "index_predicate")
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/expressions/dml.py:270:        "conflict_keys": False,
sqlglot/expressions/dml.py:271:        "index_predicate": False,
[assistant] No other code consumes `conflict_keys`, so switching the element parser is safe. I'll make the change and check the reproduction.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130559-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_assignment)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130559-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'\nfor d in ['sqlite','postgres','duckdb']:\n    print(sqlglot.transpile(q, read=d, write=d)[0])\nprint(sqlglot.transpile('INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT (a, lower(b)) WHERE b > 0 DO UPDATE SET a = 1', read='sqlite', write='sqlite')[0])\nprint(sqlglot.transpile('INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING', read='sqlite', write='sqlite')[0])\n\"", "description": "Check fixed parse of expression conflict targets"}
[tool_result] INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO UPDATE SET a = 1
INSERT INTO t (a) VALUES (1) ON CONFLICT(a) WHERE a > 0 DO NOTHING
[assistant] The parse now works in all three dialects and round-trips. Next I'll add a regression test next to the existing SQLite upsert coverage.
[tool_use Bash] {"command": "grep -n \"DO UPDATE\\|DO NOTHING\\|def test_\" tests/dialects/test_sqlite.py | head -40", "description": "Find SQLite test layout and upsert tests"}
[tool_result] 10:    def test_sqlite(self):
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
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_sqlite.py && sed -n 376,384p tests/dialects/test_sqlite.py", "description": "Read SQLite test file structure"}
[tool_result] from tests.dialects.test_dialect import Validator

from sqlglot import exp
from sqlglot.helper import logger as helper_logger


class TestSQLite(Validator):
    dialect = "sqlite"

    def test_sqlite(self):
        self.validate_identity("WITH xyz(x) AS (SELECT 1) SELECT x FROM xyz")
        self.validate_identity("SELECT * FROM t AS t INDEXED BY s.i")
        self.validate_identity("SELECT * FROM t INDEXED BY s.i")
        self.validate_identity("SELECT * FROM t INDEXED BY i")
        self.val
…[1000 chars elided]…

        self.validate_identity("SELECT (JULIANDAY('now') - 2440587.5) * 86400.0")
        self.validate_identity("SELECT UNIXEPOCH('now', 'subsec')")
        self.validate_identity(
            "CREATE TABLE store (store_id INTEGER PRIMARY KEY AUTOINCREMENT, mgr_id INTEGER NOT NULL UNIQUE REFERENCES staff ON UPDATE CASCADE)"
        )

    def test_analyze(self):
        self.validate_identity("ANALYZE tbl")
        self.validate_identity("ANALYZE schma.tbl")

    def test_create_trigger(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130559-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")", "new_string": "    def test_upsert(self):\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\",\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a, b) VALUES (1, 2) ON CONFLICT(a, LOWER(b)) WHERE b > 0 DO UPDATE SET a = 1\",\n        )\n\n    def test_analyze(self):\n        self.validate_identity(\"ANALYZE tbl\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130559-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run new upsert test and full test suite"}
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
1122 passed, 18178 subtests passed in 54.47s
[assistant] The full suite passes (1122 tests). I'll run the project's linter on the two changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[assistant] `ON CONFLICT` targets can now contain expressions, so the query from the report parses and round-trips in SQLite, Postgres and DuckDB:

```sql
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
```

The cause was in `_parse_on_conflict` (`sqlglot/parser.py`): the conflict-target list was parsed with `_parse_id_var`, which accepts only bare identifiers. I changed it to `_parse_assignment`, the general expression parser. A `WHERE` on the target already worked and still does.

- **Test:** added `test_ups
…[15 chars elided]…
dialects/test_sqlite.py`, covering the reported query and a target with both an expression and a `WHERE` predicate.
- **Results:** full suite passes (1122 tests, 18178 subtests). `ruff check` and `ruff format --check` are clean on both files.
- **Side effect:** conflict targets are now parsed as general expressions rather than identifiers. Plain column targets such as `ON CONFLICT(id)` still round-trip unchanged. Nothing else in the repo reads `conflict_keys`, so no other code is affected.

I haven't committed anything. Only `sqlglot/parser.py` and `tests/dialects/test_sqlite.py` are modified.
