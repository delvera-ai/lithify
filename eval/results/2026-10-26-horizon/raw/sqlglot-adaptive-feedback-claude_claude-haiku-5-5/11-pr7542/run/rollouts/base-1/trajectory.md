# trajectory base-1

final message:
Qualifying a table function with a typed alias column list now works. `qualify_tables` keeps the `ColumnDef` nodes intact instead of raising.

The full suite passed after my last edit: `SUMMARY: 1089 passed, 17847 subtests passed in 52.21s`, `EXIT: 0`. Ruff check and format are clean on both changed files.

**The cause:** `_set_alias` passed every alias column through `exp.to_identifier`, which only accepts strings or identifiers. Typed columns come back as `ColumnDef` nodes.

**The fix** (`sqlglot/optimizer/qualify_tables.py`): `ColumnDef` entries are kept as they are, and only plain names are converted to identifiers. I also widened the type hints to allow `ColumnDef`.

**Verified on the AST, not just the string:**
- `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` gives `SELECT * FROM FN() AS _0(col INT)`. The alias column is still a `ColumnDef` with kind `INT`.
- With `canonicalize_table_aliases=False`, it gives `SELECT * FROM FN() AS t(col INT)`.
- `SELECT t.col FROM fn() AS t(col INT)` with `db='db'` rewrites the reference to `_0.col`.

**Test:** I added one assertion to `test_qualify_tables` in `tests/test_optimizer.py` covering the reported case. I did not touch any existing test.

I did not commit anything.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/qualify_tables.py && git status --short && ls .lithify/harness/scripts/ 2>/dev/null", "description": "Read qualify_tables source and check repo state"}
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
…[7658 chars elided]…
RTS[1:]:
                        column.set(p, None)

                    column.set("table", table_alias.copy())
            elif (
                canonical_aliases
                and column_table
                and (canonical_table := canonical_aliases.get(column_table, "")) != column_table
            ):
                # Amend existing aliases, e.g. t.c -> _0.c if t is aliased to _0
                column.set("table", exp.to_identifier(canonical_table))

    return expression
run_suite.py
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qua
…[20 chars elided]…
epr(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)').args['from_'].this.args['alias'].columns))\nqualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicalize_table_aliases=True)\n\" 2>&1 | tail -5; grep -rn \"def columns\" -A8 sqlglot/expressions/*.py | grep -A8 -i \"tablealias\\|TableAlias\" | head -20", "description": "Reproduce the bug and inspect TableAlias.columns"}
[tool_result] <work>/env-sqlglot/bin/python
    raise ValueError(f"Name needs to be a string or an Identifier, got: {name.__class__}")
ValueError: Name needs to be a string or an Identifier, got: <class 'sqlglot.expressions.query.ColumnDef'>
[ColumnDef(
  this=Identifier(this=col, quoted=False),
  kind=DataType(this=DType.INT, nested=False))]
[assistant] Reproduced. `TableAlias.columns` returns `ColumnDef` nodes for typed aliases, and `_set_alias` wraps every entry in `exp.to_identifier`, which only accepts strings or identifiers. I'll keep `ColumnDef` entries as they are and convert only the names.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        columns: Sequence[str | exp.Identifier] | None = None,\n    ) -> None:", "new_string": "        columns: Sequence[str | exp.Identifier | exp.ColumnDef] | None = None,\n    ) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])", "new_string": "            alias.set(\n                \"columns\",\n                [c if isinstance(c, exp.ColumnDef) else exp.to_identifier(c) for c in columns],\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "                function_columns: Sequence[str | exp.Identifier] | None = None", "new_string": "                function_columns: Sequence[str | exp.Identifier | exp.ColumnDef] | None = None"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[assistant] Now I'll check the output and the AST node itself, with and without `canonicalize_table_aliases`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor canon in (True, False):\n    e = qualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicaliz
…[75 chars elided]…
.args['alias'].columns\n    print([type(c).__name__ for c in cols], cols[0].kind.sql() if isinstance(cols[0], exp.ColumnDef) else None)\nprint(qualify_tables(sqlglot.parse_one('SELECT t.col FROM fn() AS t(col INT)'), db='db', canonicalize_table_aliases=True).sql())\n\" 2>&1 | tail -8; grep -rln \"qualify_tables\" tests/ | head", "description": "Verify fixed output and AST for typed alias columns"}
[tool_result] SELECT * FROM FN() AS _0(col INT)
['ColumnDef'] INT
SELECT * FROM FN() AS t(col INT)
['ColumnDef'] INT
SELECT _0.col FROM FN() AS _0(col INT)
tests/test_optimizer.py
[assistant] The AST keeps `ColumnDef` with type `INT`, and column references are rewritten to the canonical alias. Next I'll add a regression test next to the existing `qualify_tables` tests.
[tool_use Bash] {"command": "grep -n \"qualify_tables\" tests/test_optimizer.py | head -20", "description": "Locate qualify_tables tests"}
[tool_result] 42:    expression = optimizer.qualify_tables.qualify_tables(expression)
248:    def test_qualify_tables(self):
269:            optimizer.qualify_tables.qualify_tables(
280:            optimizer.qualify_tables.qualify_tables(
291:            optimizer.qualify_tables.qualify_tables(
298:            optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"').sql(),
303:            "qualify_tables",
304:            optimizer.qualify_tables.qualify_tables,
921:                optimizer.qualify_tables.qualify_tables,
[tool_use Bash] {"command": "sed -n 248,310p tests/test_optimizer.py", "description": "Read existing qualify_tables test body"}
[tool_result]     def test_qualify_tables(self):
        tables = set()
        optimizer.qualify.qualify(
            parse_one("with foo AS (select * from bar) select * from foo join baz"),
            qualify_columns=False,
            on_qualify=lambda t: tables.add(t.name),
        )
        self.assertEqual(tables, {"bar", "baz"})

        self.assertEqual(
            optimizer.qualify.qualify(
                parse_one("WITH tesT AS (SELECT * FROM t1) SELECT * FROM test", "bigquery"),
                
…[1281 chars elided]…
ect a from b"), catalog="catalog"
            ).sql(),
            "SELECT a FROM b AS b",
        )

        self.assertEqual(
            optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"').sql(),
            'SELECT a FROM "DB".b AS b',
        )

        self.check_file(
            "qualify_tables",
            optimizer.qualify_tables.qualify_tables,
            db="db",
            catalog="c",
        )

    def test_normalize(self):
        self.assertEqual(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py", "old_string": "            'SELECT a FROM \"DB\".b AS b',\n        )\n\n        self.check_file(\n            \"qualify_tables\",", "new_string": "            'SELECT a FROM \"DB\".b AS b',\n        )\n\n        self.assertEqual(\n            optimizer.qualify_tables.qualify_tables(\n                parse_one(\"SELECT * FROM fn() AS t(col INT)\"),\n                canonicalize_table_aliases=True,\n            ).sql(),\n            \"SELECT * FROM FN() AS _0(col INT)\",\n        )\n\n        self.check_file(\n            \"qualify_tables\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-193501-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the optimizer test file first, then the full suite once after the last edit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -15", "description": "Run optimizer test file", "timeout": 300000}
[tool_result] ...... [  7%]
....................................................... [ 80%]
...............                                     [100%]
76 passed, 3704 subtests passed in 15.68s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -15; echo \"EXIT: ${PIPESTATUS[0]}\"", "description": "Run full test suite after final edit", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-00:10:51 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-e9fc972127.log
ELAPSED: 53s
SUMMARY: 1089 passed, 17847 subtests passed in 52.21s
EXIT: 0
EXIT:
[assistant] The full suite passed after the last edit. I'll run the linter on the two changed files as well.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py && $PY -m ruff format --check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py; git diff --stat", "description": "Lint and format-check changed files", "timeout": 120000}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/optimizer/qualify_tables.py | 9 ++++++---
 tests/test_optimizer.py             | 8 ++++++++
 2 files changed, 14 insertions(+), 3 deletions(-)
[assistant] Qualifying a table function with a typed alias column list now works. `qualify_tables` keeps the `ColumnDef` nodes intact instead of raising.

The full suite passed after my last edit: `SUMMARY: 1089 passed, 17847 subtests passed in 52.21s`, `EXIT: 0`. Ruff check and format are clean on both changed files.

**The cause:** `_set_alias` passed every alias column through `exp.to_identifier`, which only accepts strings or identifiers. Typed columns come back as `ColumnDef` nodes.

**The fix** (`sqlglot/optimizer/qualify_tables.py`): `ColumnDef` entries are kept as they are, and only plain names ar
…[60 chars elided]…
 allow `ColumnDef`.

**Verified on the AST, not just the string:**
- `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` gives `SELECT * FROM FN() AS _0(col INT)`. The alias column is still a `ColumnDef` with kind `INT`.
- With `canonicalize_table_aliases=False`, it gives `SELECT * FROM FN() AS t(col INT)`.
- `SELECT t.col FROM fn() AS t(col INT)` with `db='db'` rewrites the reference to `_0.col`.

**Test:** I added one assertion to `test_qualify_tables` in `tests/test_optimizer.py` covering the reported case. I did not touch any existing test.

I did not commit anything.
