# trajectory base-1

final message:
`ON CONFLICT` targets now accept expressions, so the query from the report parses and round-trips in SQLite, Postgres and DuckDB. The full suite passes (1122 tests) and ruff is clean.

**The fix:** in `sqlglot/parser.py` (`_parse_on_conflict`), the conflict target was parsed with `_parse_id_var`, which accepts only a bare identifier. I changed it to `_parse_disjunction`, the same expression parser used for `WHERE` conditions. The optional `WHERE` on the target was already parsed and needed no change.

**Verified output:**
- `ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET ...` → `ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET ...`
- `ON CONFLICT (a, lower(b)) WHERE c > 0 DO NOTHING` round-trips unchanged.

**Test:** added `test_upsert` to `tests/dialects/test_sqlite.py` covering both cases. The first input uses `WHERE TRUE`, so the test is stable against the generator's existing normalization of `true` to `TRUE`.

**Behaviour change to be aware of:** conflict keys are now full expressions, so a plain column target like `ON CONFLICT(id)` is stored as a `Column` node instead of an `Identifier`. Output text is unchanged, and nothing else in the codebase reads `conflict_keys`, but any downstream code that inspects that AST node type would see the difference.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"CONFLICT\\|conflict\" sqlglot/parser.py sqlglot/dialects/sqlite.py sqlglot/generator.py sqlglot/dialects/*.py | grep -v \"^.*#\" | head -80", "description": "Find ON CONFLICT handling in parser and generator"}
[tool_result] sqlglot/parser.py:1582:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:3512:                conflict=self._parse_on_conflict(),
sqlglot/parser.py:3533:    def _parse_on_conflict(self) -> exp.OnConflict | None:
sqlglot/parser.py:3534:        conflict = self._match_text_seq("ON", "CONFLICT")
sqlglot/parser.py:3537:        if not conflict and not duplicate:
sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3543:        if conflict:
sqlglot/parser.py:3547:   
…[1204 chars elided]…
ICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
sqlglot/generator.py:2302:        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:        if conflict_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "offset": 3530, "limit": 40}
[tool_result] 3530	
3531	        return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))
3532	
3533	    def _parse_on_conflict(self) -> exp.OnConflict | None:
3534	        conflict = self._match_text_seq("ON", "CONFLICT")
3535	        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")
3536	
3537	        if not conflict and not duplicate:
3538	            return None
3539	
3540	        conflict_keys = None
3541	        constraint = None
3542	
3543	        if conflict:
3544	            i
…[562 chars elided]…
parse_equality)
3556	        else:
3557	            expressions = None
3558	
3559	        return self.expression(
3560	            exp.OnConflict(
3561	                duplicate=duplicate,
3562	                expressions=expressions,
3563	                action=action,
3564	                conflict_keys=conflict_keys,
3565	                index_predicate=index_predicate,
3566	                constraint=constraint,
3567	                where=self._parse_where(),
3568	            )
3569	        )
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/sqlglot/generator.py", "offset": 2294, "limit": 26}
[tool_result] 2294	        return expression.name
2295	
2296	    def onconflict_sql(self, expression: exp.OnConflict) -> str:
2297	        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
2298	
2299	        constraint = self.sql(expression, "constraint")
2300	        constraint = f" ON CONSTRAINT {constraint}" if constraint else ""
2301	
2302	        conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
2303	        if conflict_keys:
2304	            
…[206 chars elided]…
= self.sql(expression, "action")
2310	
2311	        expressions = self.expressions(expression, flat=True)
2312	        if expressions:
2313	            set_keyword = "SET " if self.DUPLICATE_KEY_UPDATE_WITH_SET else ""
2314	            expressions = f" {set_keyword}{expressions}"
2315	
2316	        where = self.sql(expression, "where")
2317	        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
2318	
2319	    def returning_sql(self, expression: exp.Returning) -> str:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z'\nfor d in ['sqlite','postgres','duckdb']:\n    try: print(d, sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(d, 
…[34 chars elided]…
NTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE c > 0 DO NOTHING'\nprint(sqlglot.transpile(q2, read='sqlite', write='sqlite')[0] if False else '')\n\" 2>&1 | tail -20; grep -n \"def _parse_expression\\|def _parse_assignment\\|def _parse_disjunction\\|def _parse_conjunction\\|def _parse_bitwise\\|def _parse_ordered\" sqlglot/parser.py", "description": "Reproduce the ON CONFLICT parse failure"}
[tool_result] sqlite ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
postgres ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z
duckdb ERR Expecting ). Line 1, Col: 101.
  INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower[4m([0mcol_y)) DO UPDATE SET col_z = excluded.col_z

7 matches in 7 files:

5765:0:
5768:0:
5790:0:
5802:0:
6042:0:
8624:0:
sqlglot/parser.py:5471:def _parse_ordered(
[tool_use Bash] {"command": "grep -n \"    def _parse_\\(conjunction\\|assignment\\|disjunction\\|equality\\|expression\\|bitwise\\|field\\|id_var\\)\\b\" sqlglot/parser.py; grep -n \"_parse_csv(self._parse_\\(conjunction\\|assignment\\|expression\\|disjunction\\)\" sqlglot/parser.py | head; grep -n \"conflict\\|OnConflict\" tests/dialects/*.py | head -30", "description": "Locate expression parse helpers and existing conflict tests"}
[tool_result] 1147 matches in 227 files:

10020:0:self._parse_csv(self._parse_declareitem))
10022:0:
10053:0:
10094:0:
1011:0:lambda self, this, to: self.expression(exp.JSONCast(this=this, to=to)),
1015:0:lambda self, this, path: self.expression(
1022:0:lambda self, this, path: self.expression(
1030:0:lambda self, this, path: self.expression(
1033:0:lambda self, this, path: self.expression(
1036:0:lambda self, this, key: self.expression(
1050:0:lambda self: self._parse_disjunction(),
1052:0:lambda self: self.
…[7649 chars elided]…
rder_by_expression_list> [ASC | DESC]).
80:0:
[+947 more]
rg: regex parse error:
    (?:_parse_csv(self._parse_\(conjunction|assignment|expression|disjunction\))
    ^
error: unclosed group
0 matches for '_parse_csv(self._parse_\(conjunction\|assignment\|expression\|disjunction\)'
2 matches in 1 files:

tests/dialects/test_sqlite.py:288:for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
tests/dialects/test_sqlite.py:289:with self.subTest(f"ON CONFLICT {conflict_action}"):
[tool_use Grep] {"pattern": "ON CONFLICT \\(", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/tests", "-n": "true", "output_mode": "content"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Grep] {"pattern": "def _parse_(assignment|disjunction|expression|conjunction)\\(", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "grep -rn \"ON CONFLICT (\" tests/ | head -20; echo ---; grep -n \"    def _parse_\\(assignment\\|disjunction\\|expression\\|conjunction\\)(\" sqlglot/parser.py", "description": "Find existing ON CONFLICT tests and parse helper defs"}
[tool_result ERROR] Exit code 2
---
rg: regex parse error:
    (?:    def _parse_\(assignment|disjunction|expression|conjunction\)()
    ^
error: unclosed group
0 matches for '    def _parse_\(assignment\|disjunction\|expression\|conjunction\)('
[tool_use Bash] {"command": "rg -n \"ON CONFLICT \\(\" tests/ | head -20; echo ---; rg -n \"    def _parse_(assignment|disjunction|expression|conjunction)\\(\" sqlglot/parser.py", "description": "Find existing ON CONFLICT tests and parse helper defs"}
[tool_result] 0 matches for 'ON CONFLICT \('
---
4 matches in 4 files:

5765:0:
5768:0:
5790:0:
5802:0:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport re,pathlib\nfor p in pathlib.Path('.').rglob('*.py'):\n    if '.git' in p.parts: continue\n    for i,l in enumerate(p.read_text(errors='ignore').splitlines(),1):\n        if re.search(r'ON CONFLICT \\(|def _parse_(assignment|disjunction|expression|conjunction)\\(', l): print(p,i,l.strip())\n\"", "description": "Search repo for conflict tests and parse helper defs"}
[tool_result] sqlglot/parser.py 5765 def _parse_expression(self) -> exp.Expr | None:
sqlglot/parser.py 5768 def _parse_assignment(self) -> exp.Expr | None:
sqlglot/parser.py 5790 def _parse_disjunction(self) -> exp.Expr | None:
sqlglot/parser.py 5802 def _parse_conjunction(self) -> exp.Expr | None:
sqlglot/parsers/clickhouse.py 531 def _parse_assignment(self) -> exp.Expr | None:
sqlglot/parsers/clickhouse.py 876 def _parse_expression(self) -> exp.Expr | None:
sqlglot/parsers/prql.py 162 def _parse_expression(self) -> exp.Expr | None:
sqlglot/parsers/duckdb.py 263 def _parse_expression(self) -> exp.Expr | None:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport pathlib\nfor p in pathlib.Path('tests').rglob('*.py'):\n    for i,l in enumerate(p.read_text(errors='ignore').splitlines(),1):\n        if 'CONFLICT' in l.upper(): print(p,i,l.strip()[:160])\n\"; sed -n 5765,5800p sqlglot/parser.py", "description": "List test lines mentioning CONFLICT and view parse helpers"}
[tool_result] tests/test_optimizer.py 2456 def test_qualify_group_by_conflict_bigquery(self):
tests/dialects/test_materialize.py 16 "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_materialize.py 19 "postgres": "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_sqlite.py 288 for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
tests/dialects/test_sqlite.py 289 with self.subTest(f"ON CONF
…[1969 chars elided]…
           comments=comments,
            )

        return this

    def _parse_disjunction(self) -> exp.Expr | None:
        this = self._parse_conjunction()
        while self._match_set(self.DISJUNCTION):
            comments = self._prev_comments
            this = self.expression(
                self.DISJUNCTION[self._prev.token_type](
                    this=this, expression=self._parse_conjunction()
                ),
                comments=comments,
            )
        return this
[tool_use Bash] {"command": "rg -n \"conflict_keys\" sqlglot/ | head; <work>/env-sqlglot/bin/python -I -c \"\nimport pathlib\nfor p in pathlib.Path('sqlglot').rglob('*.py'):\n    for i,l in enumerate(p.read_text().splitlines(),1):\n        if 'conflict_keys' in l or 'index_predicate' in l: print(p,i,l.strip())\n\"", "description": "Check other uses of conflict_keys and index_predicate"}
[tool_result] 9 matches in 3 files:

sqlglot/expressions/dml.py:270:"conflict_keys": False,
sqlglot/generator.py:2302:conflict_keys = self.expressions(expression, key="conflict_keys", flat=True)
sqlglot/generator.py:2303:if conflict_keys:
sqlglot/generator.py:2304:conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2307:conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/parser.py:3540:conflict
…[462 chars elided]…
eys", flat=True)
sqlglot/generator.py 2303 if conflict_keys:
sqlglot/generator.py 2304 conflict_keys = f"({conflict_keys})"
sqlglot/generator.py 2306 index_predicate = self.sql(expression, "index_predicate")
sqlglot/generator.py 2307 conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py 2317 return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/expressions/dml.py 270 "conflict_keys": False,
sqlglot/expressions/dml.py 271 "index_predicate": False,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_disjunction)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nqs=['INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z',\n'INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE c > 0 DO NOTHING',\n'INSERT INTO t (a) VALUES (1) ON CONFLICT(id) WHERE deleted_at IS NULL DO UPDATE SET a = 1']\nfor q in qs:\n  for d in ['sqlite','postgres','duckdb']:\n    try: print(d, '|', sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', str(e)[:200])\n\" 2>&1", "description": "Apply parser fix and verify round-trips"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=['INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z',\n'INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE c > 0 DO NOTHING',\n'INSERT INTO t (a) VALUES (1) ON CONFLICT(id) WHERE deleted_at IS NULL DO UPDATE SET a = 1']\nfor q in qs:\n  for d in ['sqlite','postgres','duckdb']:\n    try: print(d, '|', sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', str(e)[:200])\n\" 2>&1", "description": "Verify round-trips with repo sources on path"}
[tool_result] sqlite | INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
postgres | INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
duckdb | INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
sqlite | INSERT INTO t (a) VALUES (1
…[22 chars elided]…
(b)) WHERE c > 0 DO NOTHING
postgres | INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE c > 0 DO NOTHING
duckdb | INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE c > 0 DO NOTHING
sqlite | INSERT INTO t (a) VALUES (1) ON CONFLICT(id) WHERE deleted_at IS NULL DO UPDATE SET a = 1
postgres | INSERT INTO t (a) VALUES (1) ON CONFLICT(id) WHERE deleted_at IS NULL DO UPDATE SET a = 1
duckdb | INSERT INTO t (a) VALUES (1) ON CONFLICT(id) WHERE deleted_at IS NULL DO UPDATE SET a = 1
[tool_use Bash] {"command": "rg -n \"def test_|INSERT\" tests/dialects/test_sqlite.py | head -60", "description": "Outline sqlite test file structure"}
[tool_result] 21 matches in 14 files:

10:0:
103:0:"INSERT IGNORE INTO foo (x, y) VALUES (1, 2)",
104:0:"INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
209:0:
232:0:
246:0:
255:0:
263:0:
269:0:
278:0:
287:0:
380:0:
384:0:
tests/dialects/test_sqlite.py:101:"INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)",
tests/dialects/test_sqlite.py:293:self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
tests/dialects/test_sqlite.py:294:self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 
…[58 chars elided]…
ity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
tests/dialects/test_sqlite.py:296:self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
tests/dialects/test_sqlite.py:297:self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
tests/dialects/test_sqlite.py:387:"CREATE TRIGGER log_insert AFTER INSERT ON users BEGIN INSERT INTO audit_log ...
tests/dialects/test_sqlite.py:397:"CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view BEGIN INSERT I...
[tool_use Bash] {"command": "sed -n 284,300p tests/dialects/test_sqlite.py", "description": "View sqlite test context around upsert tests"}
[tool_result]             self.validate_identity("TRUNC(3.14, 2)", "TRUNC(3.14)").assert_is(exp.Trunc)
            self.assertIn("'decimals' is not supported", cm.output[0])

    def test_ddl(self):
        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
            with self.subTest(f"ON CONFLICT {conflict_action}"):
                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")

        self.validate_identity("CREATE TABLE over (x, y)")
        s
…[136 chars elided]…
LUES (1, 2)")
        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)")
        self.validate_identity("CREATE TEMPORARY TABLE foo (id INTEGER)")
        self.validate_identity("CREATE VIRTUAL TABLE docs USING fts5(title, content)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_ddl(self):\n        for conflict_action in", "new_string": "    def test_upsert(self):\n        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM
…[61 chars elided]…
T col_z = excluded.col_z\",\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\",\n        )\n        self.validate_identity(\n            \"INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE c > 0 DO NOTHING\"\n        )\n\n    def test_ddl(self):\n        for conflict_action in"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\",\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\",\n        )", "new_string": "        self.validate_identity(\n            \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202237-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py tests/dialects/test_postgres.py tests/dialects/test_materialize.py 2>&1 | tail -15", "description": "Run sqlite, postgres, materialize dialect tests"}
[tool_result] ....................................... [100%]
39 passed, 474 subtests passed in 0.27s
[assistant] Targeted tests pass. Now the full suite, which is the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
.........
…[183 chars elided]…
................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
....                                                                     [100%]
1122 passed, 18178 subtests passed in 46.09s
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git diff", "description": "Lint changed files and show diff"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/parser.py             | 2 +-
 tests/dialects/test_sqlite.py | 8 ++++++++
 2 files changed, 9 insertions(+), 1 deletion(-)

--- Changes ---

sqlglot/parser.py
  @@ -3544,7 +3544,7 @@ class Parser:
  -                conflict_keys = self._parse_csv(self._parse_id_var)
  +                conflict_keys = self._parse_csv(self._parse_disjunction)
                   self._match_r_paren()
   
           index_predicate = self._parse_where()
  +1 -1

t
…[155 chars elided]…
      "INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z"
  +        )
  +        self.validate_identity(
  +            "INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE c > 0 DO NOTHING"
  +        )
  +
       def test_ddl(self):
           for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
               with self.subTest(f"ON CONFLICT {conflict_action}"):
  +8 -0
[assistant] `ON CONFLICT` targets now accept expressions, so the query from the report parses and round-trips in SQLite, Postgres and DuckDB. The full suite passes (1122 tests) and ruff is clean.

**The fix:** in `sqlglot/parser.py` (`_parse_on_conflict`), the conflict target was parsed with `_parse_id_var`, which accepts only a bare identifier. I changed it to `_parse_disjunction`, the same expression parser used for `WHERE` conditions. The optional `WHERE` on the target was already parsed and needed no change.

**Verified output:**
- `ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET ...` → `ON CONFLICT(c
…[105 chars elided]…
nchanged.

**Test:** added `test_upsert` to `tests/dialects/test_sqlite.py` covering both cases. The first input uses `WHERE TRUE`, so the test is stable against the generator's existing normalization of `true` to `TRUE`.

**Behaviour change to be aware of:** conflict keys are now full expressions, so a plain column target like `ON CONFLICT(id)` is stored as a `Column` node instead of an `Identifier`. Output text is unchanged, and nothing else in the codebase reads `conflict_keys`, but any downstream code that inspects that AST node type would see the difference.

I haven't committed anything.
