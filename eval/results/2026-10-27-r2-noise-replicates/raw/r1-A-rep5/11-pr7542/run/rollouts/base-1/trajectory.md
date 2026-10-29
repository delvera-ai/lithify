# trajectory base-1

final message:
Qualifying a table function with a typed alias column list now works. `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` returns `SELECT * FROM FN() AS _0(col INT)`, and the column definitions are kept intact.

**Cause:** in `_set_alias` (`sqlglot/optimizer/qualify_tables.py`), the alias column list was run through `exp.to_identifier` on every entry. With a typed list, those entries are `ColumnDef` nodes, not names, so `to_identifier` raised the `ValueError`.

**Fix:**
- `_set_alias` keeps `ColumnDef` entries as they are and still converts plain names (`t(a, b)`) to identifiers.
- The `columns` and `function_columns` type hints now allow expressions as well as strings and identifiers.

**Test:** I added a case to `test_qualify_tables` in `tests/test_optimizer.py` for the typed alias with canonical aliases. I didn't modify any existing assertions.

**Verification:** the full suite passes (1089 tests, 17847 subtests) with the project's Python, and ruff lint and format checks pass on both changed files. I didn't run `make check` itself, since it also runs mypy and the C-extension tests.

I didn't commit the change.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/qualify_tables.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nprint(repr(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)')))\nqualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicalize_table_aliases=True)\n\" 2>&1 | tail -15", "description": "Read qualify_tables and reproduce the error"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.dialects.dialect import Dialect, DialectType
from sqlglot.helper import name_sequence, seq_get, ensure_list
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.scope import Scope, traverse_scope

if t.TYPE_CHECKING:
    from sqlglot._typing import E
    from collections.abc import Sequence


def qualify_tables(
    expression: E,
    db: str | exp.Identifier |
…[8341 chars elided]…
(f"Name needs to be a string or an Identifier, got: {name.__class__}")
ValueError: Name needs to be a string or an Identifier, got: <class 'sqlglot.expressions.query.ColumnDef'>
Select(
  expressions=[
    Star()],
  from_=From(
    this=Table(
      this=Anonymous(this=fn),
      alias=TableAlias(
        this=Identifier(this=t, quoted=False),
        columns=[
          ColumnDef(
            this=Identifier(this=col, quoted=False),
            kind=DataType(this=DType.INT, nested=False))]))))
[assistant] The failure is in `_set_alias`: when a table function has an explicit alias column list, `function_columns` is the alias's own `columns` list, which holds `ColumnDef` nodes, and those get passed through `exp.to_identifier`. I'll keep `ColumnDef` nodes intact and only convert plain names.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        columns: Sequence[str | exp.Identifier] | None = None,\n    ) -> None:", "new_string": "        columns: Sequence[str | exp.Expr] | None = None,\n    ) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])", "new_string": "            alias.set(\n                \"columns\",\n                [c if isinstance(c, exp.ColumnDef) else exp.to_identifier(c) for c in columns],\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "                function_columns: Sequence[str | exp.Identifier] | None = None", "new_string": "                function_columns: Sequence[str | exp.Expr] | None = None"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[assistant] Now I'll check the fix and look at the existing qualify_tables tests so I can add a regression test beside them.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor sql in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(a, b)', 'SELECT * FROM fn() AS t(col INT, other TEXT)']:\n    print(qualify_tables(sqlglot.parse_one(sql), canonicalize_table_aliases=True).sql())\n    print(qualify_tables(sqlglot.parse_one(sql)).sql())\n\"; grep -n \"def test_\\|canonicalize\" tests/test_optimizer.py | grep -i -A3 \"qualify_tables\" | head -30", "description": "Verify fix output and find qualify_tables tests"}
[tool_result] SELECT * FROM FN() AS _0(col INT)
SELECT * FROM FN() AS t(col INT)
SELECT * FROM FN() AS _0(a, b)
SELECT * FROM FN() AS t(a, b)
SELECT * FROM FN() AS _0(col INT, other TEXT)
SELECT * FROM FN() AS t(col INT, other TEXT)
248:    def test_qualify_tables(self):
309:    def test_normalize(self):
328:    def test_qualify_columns(self, logger):
622:    def test_validate_columns(self):
[assistant] The fix produces the right SQL in both modes. Next I'll add a regression test next to the existing `test_qualify_tables` cases.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py", "offset": 248, "limit": 62}
[tool_result] 248	    def test_qualify_tables(self):
249	        tables = set()
250	        optimizer.qualify.qualify(
251	            parse_one("with foo AS (select * from bar) select * from foo join baz"),
252	            qualify_columns=False,
253	            on_qualify=lambda t: tables.add(t.name),
254	        )
255	        self.assertEqual(tables, {"bar", "baz"})
256	
257	        self.assertEqual(
258	            optimizer.qualify.qualify(
259	                parse_one("WITH tesT AS (SELECT * FROM t1) SE
…[1503 chars elided]…
        ).sql(),
294	            "SELECT a FROM b AS b",
295	        )
296	
297	        self.assertEqual(
298	            optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"').sql(),
299	            'SELECT a FROM "DB".b AS b',
300	        )
301	
302	        self.check_file(
303	            "qualify_tables",
304	            optimizer.qualify_tables.qualify_tables,
305	            db="db",
306	            catalog="c",
307	        )
308	
309	    def test_normalize(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(\n            optimizer.qualify_tables.qualify_tables(parse_one(\"select a from b\"), db='\"DB\"').sql(),\n            'SELECT a FROM \"DB\".b AS b',\n        )\n", "new_string": "        
…[65 chars elided]…
ables(parse_one(\"select a from b\"), db='\"DB\"').sql(),\n            'SELECT a FROM \"DB\".b AS b',\n        )\n\n        self.assertEqual(\n            optimizer.qualify_tables.qualify_tables(\n                parse_one(\"SELECT * FROM fn() AS t(col INT)\"),\n                canonicalize_table_aliases=True,\n            ).sql(),\n            \"SELECT * FROM FN() AS _0(col INT)\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093219-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k qualify 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Add regression test and run optimizer and full test suites"}
[tool_result] ..... [100%]
5 passed, 71 deselected, 465 subtests passed in 2.63s
.................................................................................................................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 53.42s
[assistant] Tests pass. I'll run the linter and formatter on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py 2>&1 | tail -3; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/optimizer/qualify_tables.py
 M tests/test_optimizer.py
[assistant] Qualifying a table function with a typed alias column list now works. `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` returns `SELECT * FROM FN() AS _0(col INT)`, and the column definitions are kept intact.

**Cause:** in `_set_alias` (`sqlglot/optimizer/qualify_tables.py`), the alias column list was run through `exp.to_identifier` on every entry. With a typed list, those entries are `ColumnDef` nodes, not names, so `to_identifier` raised the `ValueError`.

**Fix:**
- `_set_alias` keeps `ColumnDef` entries as they are and still converts plain names (`t(a, b)`) to identifiers.
- The `columns` and `function_columns` type hints now allow expressions as well as strings and identifiers.

**Test:** I added a case to `test_qualify_tables` in `tests/test_optimizer.py` for the typed alias with canonical aliases. I didn't modify any existing assertions.

**Verification:** the full suite passes (1089 tests, 17847 subtests) with the project's Python, and ruff lint and format checks pass on both changed files. I didn't run `make check` itself, since it also runs mypy and the C-extension tests.

I didn't commit the change.
