# trajectory base-1

final message:
`ON CONFLICT` targets with expressions now parse and round-trip, including with a `WHERE` on the target. The full test suite passes (1121 passed) and ruff is clean.

**Cause:** the parser read the conflict target with `_parse_id_var`, which only accepts plain names, so `lower(col_y)` broke it with `Expecting )`.

**Fix** (`sqlglot/parser.py`, `_parse_on_conflict`): the target is now parsed with `_parse_field`. That still returns identifiers for plain column names, so the AST for existing statements is unchanged, and it also accepts function calls like `lower(...)`. I didn't touch the generator, which already handled arbitrary expressions in that slot.

**Test** (`tests/dialects/test_sqlite.py`, `test_ddl`): added two round-trip cases, your statement and a target with both an expression and a `WHERE`.

Probing with `probe_parse.py` also showed these now work:
- `ON CONFLICT (lower(a)) ...` (expression only)
- The same statements under `--read postgres`

I did not add a Postgres-specific test. The shared parser change covers it, and the existing Postgres tests still pass.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"CONFLICT\" sqlglot/parser.py sqlglot/dialects/*.py sqlglot/generator.py | head -50; ls .lithify/harness/scripts/ 2>/dev/null"}
[tool_result] sqlglot/parser.py:1582:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:3534:        conflict = self._match_text_seq("ON", "CONFLICT")
sqlglot/parser.py:3552:        action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/parser.py:9197:                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/generator.py:2297:        conflict = "ON DUPLICATE KEY" if expression.args.get("duplicate") else "ON CONFLICT"
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 3525,3580p sqlglot/parser.py; sed -n 2285,2330p sqlglot/generator.py; grep -n \"class OnConflict\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; cat .lithify/harness/scripts/probe_parse.py | head -30"}
[tool_result]             this.set("alias", self._parse_table_alias())
        return this

    def _parse_kill(self) -> exp.Kill:
        kind = exp.var(self._prev.text) if self._match_texts(("CONNECTION", "QUERY")) else None

        return self.expression(exp.Kill(this=self._parse_primary(), kind=kind))

    def _parse_on_conflict(self) -> exp.OnConflict | None:
        conflict = self._match_text_seq("ON", "CONFLICT")
        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")

        if not confl
…[4741 chars elided]…
hows both

Exits 0 if every statement is OK, 1 if any statement is ERR or UNSTABLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
  <python> -I .lithify/harness/scripts/probe_parse.py --read oracle < variants.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c\" | $PY -I .lithify/harness/scripts/probe_parse.py --read sqlite; grep -rn \"conflict_keys\\|index_predicate\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -30"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parser.py:3540:        conflict_keys = None
sqlglot/parser.py:3547:                conflict_keys = self._parse_csv(self._parse_id_var)
sqlglot/parser.py:3550:        index_predicate = self._parse_where()
sqlglot
…[287 chars elided]…
ct_keys:
sqlglot/generator.py:2304:            conflict_keys = f"({conflict_keys})"
sqlglot/generator.py:2306:        index_predicate = self.sql(expression, "index_predicate")
sqlglot/generator.py:2307:        conflict_keys = f"{conflict_keys}{index_predicate} "
sqlglot/generator.py:2317:        return f"{conflict}{constraint}{conflict_keys}{action}{expressions}{where}"
sqlglot/expressions/dml.py:270:        "conflict_keys": False,
sqlglot/expressions/dml.py:271:        "index_predicate": False,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) DO UPDATE SET c = excluded.c WHERE t.d > 1\" | PYTHONPATH=$PWD $PY -I .lithify/harness/scripts/probe_parse.py --read sqlite"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) DO UPDATE SET c = excluded.c WHERE t.d > 1\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read sqlite"}
[tool_result ERROR] Exit code 1
ERR       INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z
          ParseError: Expecting ). Line 1, Col: 101.
OK        INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a) WHERE a > 0 DO NOTHING
ERR       INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c
          ParseError: Expecting ). Line 1, Col: 51.
OK        INSERT INTO t (a) VALUES (1) ON CONFLICT (a) DO UPDATE SET c = excluded.c WHERE t.d > 1
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a) DO UPDATE SET c = excluded.c WHERE t.d > 1
[tool_use Bash] {"command": "grep -n \"def _parse_expression\\|def _parse_assignment\\|def _parse_disjunction\\|def _parse_field\\b\\|def _parse_ordered\" sqlglot/parser.py; grep -rn \"ON CONFLICT\" tests/ | grep \"(.*(\" | head; grep -rn \"ON CONFLICT\\|ON DUPLICATE\" tests/ | wc -l"}
[tool_result] 6 matches in 5 files:

5765:0:
5768:0:
5790:0:
8624:0:
sqlglot/parser.py:5471:def _parse_ordered(
sqlglot/parser.py:6874:def _parse_field(
tests/dialects/test_materialize.py:16:            "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_materialize.py:19:                "postgres": "INSERT INTO example (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO NOTHING",
tests/dialects/test_sqlite.py:290:                self.validate_identity("CREATE TA
…[321 chars elided]…
(a, b, c) VALUES (1, 2, 3) ON CONFLICT(c) DO UPDATE SET a = t.a + 1 WHERE t.a < 1"
tests/dialects/test_postgres.py:1251:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO NOTHING RETURNING *"
tests/dialects/test_postgres.py:1254:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = 1 RETURNING *"
tests/dialects/test_postgres.py:1257:            "INSERT INTO x VALUES (1, 'a', 2.0) ON CONFLICT(id) DO UPDATE SET x.id = excluded.id RETURNING *"
      16
[tool_use Bash] {"command": "grep -n \"    def _parse_\\(expression\\|conjunction\\|equality\\|bitwise\\|assignment\\|disjunction\\)\\b\" sqlglot/parser.py; grep -n \"self._parse_conjunction\\b\\|_parse_assignment()\" sqlglot/parser.py | head -3"}
[tool_result] 122 matches in 30 files:

1116:0:lambda self: self.expression(exp.Not(this=self._parse_equality())),
1231:0:lambda self: self._parse_property_assignment(exp.AlgorithmProperty),
1233:0:lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
1243:0:lambda self, **kwargs: self._parse_property_assignment(
1246:0:lambda self: self._parse_property_assignment(exp.SchemaCommentProperty),
1259:0:lambda self: self._parse_property_assignment(exp.DistStyleProperty),
1261:0:lambda self: self
…[2696 chars elided]…
_parse_wrapped_csv(self._parse_equality)
sqlglot/parser.py:5125:this = self._parse_bitwise()
sqlglot/parser.py:5160:alias = self._parse_bitwise()
sqlglot/parser.py:5234:self._parse_bitwise
sqlglot/parser.py:5383:kind(expressions=[] if with_prefix else self._parse_wrapped_csv(self._parse_b...
sqlglot/parser.py:5394:return self._parse_grouping_sets() or self._parse_cube_or_rollup() or self._p...
sqlglot/parser.py:5412:exp.Prior(this=self._parse_bitwise())
[+68 more]
17 matches in 3 files:

5768:0:
[tool_use Bash] {"command": "sed -n 6874,6890p sqlglot/parser.py"}
[tool_result]     def _parse_field(
        self,
        any_token: bool = False,
        tokens: t.Collection[TokenType] | None = None,
        anonymous_func: bool = False,
    ) -> exp.Expr | None:
        if anonymous_func:
            field = (
                self._parse_function(anonymous=anonymous_func, any_token=any_token)
                or self._parse_primary()
            )
        else:
            field = self._parse_primary() or self._parse_function(
                anonymous=anonymous_func, any_token=any_token
            )
        return field or self._parse_id_var(any_token=any_token, tokens=tokens)
[assistant] `_parse_field` keeps plain names as identifiers (same AST as today) and also accepts function calls, so I'll switch the conflict-key parser to it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py", "old_string": "                conflict_keys = self._parse_csv(self._parse_id_var)", "new_string": "                conflict_keys = self._parse_csv(self._parse_field)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO 
…[136 chars elided]…
TO t (a) VALUES (1) ON CONFLICT (a, lower(b)) DO NOTHING\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read sqlite; printf '%s\\n' \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c\" \"INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) DO NOTHING\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read postgres"}
[tool_result] OK        INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE true ON CONFLICT (col_x, lower(col_y)) DO UPDATE SET col_z = excluded.col_z
          INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z
OK        INSERT INTO t (a) VALUES (1) ON CONFLICT (a) WHERE a > 0 DO NOTHING
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a) WHERE a > 0 DO NOTHING
OK        INSERT INTO t (a) VALUES
…[394 chars elided]…
SERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) DO NOTHING
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) DO NOTHING
OK        INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) WHERE a > 0 DO UPDATE SET c = excluded.c
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO UPDATE SET c = excluded.c
OK        INSERT INTO t (a) VALUES (1) ON CONFLICT (a, lower(b)) DO NOTHING
          INSERT INTO t (a) VALUES (1) ON CONFLICT(a, LOWER(b)) DO NOTHING
[assistant] Parsing and round-trip now work for SQLite and Postgres. Next I'll add a regression test next to the existing SQLite upsert tests.
[tool_use Bash] {"command": "grep -n \"CONFLICT\" -B3 -A3 tests/dialects/test_sqlite.py"}
[tool_result] 286-
287-    def test_ddl(self):
288-        for conflict_action in ("ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"):
289:            with self.subTest(f"ON CONFLICT {conflict_action}"):
290:                self.validate_identity("CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)")
291-
292-        self.validate_identity("CREATE TABLE over (x, y)")
293-        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
[tool_use Bash] {"command": "sed -n 292,300p tests/dialects/test_sqlite.py"}
[tool_result]         self.validate_identity("CREATE TABLE over (x, y)")
        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)")
        self.validate_identity("CREATE TEMPORARY TABLE foo (id INTEGER)")
        self.validate_identity("CREATE VIRTUAL TABLE docs USING fts5(title, content)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"CREATE TABLE over (x, y)\")\n        self.validate_identity(\"INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)\")", "new_string": "        self.validate_identity(\"CREATE TABLE 
…[63 chars elided]…
INSERT INTO tbl_a (col_x, col_y, col_z) SELECT x, y, z FROM src WHERE TRUE ON CONFLICT(col_x, LOWER(col_y)) DO UPDATE SET col_z = excluded.col_z\"\n        )\n        self.validate_identity(\n            \"INSERT INTO foo (a) VALUES (1) ON CONFLICT(a, LOWER(b)) WHERE a > 0 DO UPDATE SET c = excluded.c\"\n        )\n        self.validate_identity(\"INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164713-sqlite-and-other-dialects-with-u/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py tests/dialects/test_postgres.py tests/dialects/test_materialize.py 2>&1 | tail -5 && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] ...................................... [100%]
38 passed, 474 subtests passed in 0.29s
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 45.85s
[assistant] Full suite passes. Now a style check on the two edited files.
[tool_use Bash] {"command": "(ruff --version && ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git status --short; git diff --stat"}
[tool_result] ruff 0.15.6
Ruff: No issues found
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.pysqlglot/parser.py             | 2 +-
 tests/dialects/test_sqlite.py | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] `ON CONFLICT` targets with expressions now parse and round-trip, including with a `WHERE` on the target. The full test suite passes (1121 passed) and ruff is clean.

**Cause:** the parser read the conflict target with `_parse_id_var`, which only accepts plain names, so `lower(col_y)` broke it with `Expecting )`.

**Fix** (`sqlglot/parser.py`, `_parse_on_conflict`): the target is now parsed with `_parse_field`. That still returns identifiers for plain column names, so the AST for existing statements is unchanged, and it also accepts function calls like `lower(...)`. I didn't touch the generator, which already handled arbitrary expressions in that slot.

**Test** (`tests/dialects/test_sqlite.py`, `test_ddl`): added two round-trip cases, your statement and a target with both an expression and a `WHERE`.

Probing with `probe_parse.py` also showed these now work:
- `ON CONFLICT (lower(a)) ...` (expression only)
- The same statements under `--read postgres`

I did not add a Postgres-specific test. The shared parser change covers it, and the existing Postgres tests still pass.

I haven't committed anything.
