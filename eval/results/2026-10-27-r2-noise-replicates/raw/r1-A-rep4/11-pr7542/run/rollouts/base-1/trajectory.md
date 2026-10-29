# trajectory base-1

final message:
Fixed. `qualify_tables` now keeps typed table-alias columns like `t(col INT)` intact instead of crashing.

**Cause:** in `sqlglot/optimizer/qualify_tables.py`, `_set_alias` ran every alias column through `exp.to_identifier()`. That works for names (strings or identifiers), but a typed column is a `ColumnDef` node, so it raised the `ValueError`.

**Change:**
- `_set_alias` only converts `str` and `exp.Identifier` columns. Anything else, such as a `ColumnDef`, is passed through unchanged.
- The type hints for `columns` / `function_columns` now allow `exp.Expr`.

**Result:**
- `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` now gives `SELECT * FROM FN() AS _0(col INT)`.
- Untyped aliases such as `t(col)` behave as before.
- With `canonicalize_table_aliases=False`, the alias is kept as written, `t(col INT)`.

**Test:** I added one assertion for the reported case to `test_qualify_tables` in `tests/test_optimizer.py`. The full suite passes (1089 passed) and ruff check and format are clean on both files. I did not run `make check`, which also includes mypy.

The change is uncommitted in the worktree.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/qualify_tables.py && git status --short | head", "description": "Read qualify_tables module and check git status"}
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
…[7645 chars elided]…
exp.COLUMN_PARTS[1:]:
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
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor s in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(col)', 'SELECT * FROM UNNEST([1]) AS t(col INT)']:\n    for c in [True, False]:\n        try: print(qualify_tables(sqlglot.parse_one(s), canonicalize_table_aliases=c).sql())\n        except Exception as e: print(type(e).__name__, e)\n\" 2>&1; grep -n \"def columns\" -A8 sqlglot/expressions.py | head -30", "description": "Reproduce the error and inspect TableAlias.columns"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor s in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(col)', 'SELECT * FROM UNNEST([1]) AS t(col INT)']:\n    for c in [True, False]:\n        try: print(qualify_tables(sqlglot.parse_one(s), canonicalize_table_aliases=c).sql())\n        except Exception as e: print(type(e).__name__, e)\n\" 2>&1; grep -n \"class TableAlias\" -A12 sqlglot/expressions.py", "description": "Reproduce the error with the repo on the import path"}
[tool_result ERROR] Exit code 2
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "pwd && ls && git rev-parse --show-toplevel && ls sqlglot | head -5", "description": "Check the worktree layout"}
[tool_result] ~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1
__init__.py
__main__.py
_typing.py
_version.py
dialects
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor s in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(col)', 'SELECT * FROM UNNEST([1]) AS t(col INT)']:\n    for c in [True, False]:\n        try: print(qualify_tables(sqlglot.parse_one(s), canonicalize_table_aliases=c).sql())\n        except Exception as e: print(type(e).__name__, e)\n\" 2>&1; grep -n \"class TableAlias\" -A12 sqlglot/expressions.py", "description": "Reproduce the error from the repo checkout"}
[tool_result ERROR] Exit code 2
ValueError Name needs to be a string or an Identifier, got: <class 'sqlglot.expressions.query.ColumnDef'>
SELECT * FROM FN() AS t(col INT)
SELECT * FROM FN() AS _0(col)
SELECT * FROM FN() AS t(col)
SELECT * FROM UNNEST(ARRAY(1)) AS _0(col INT)
SELECT * FROM UNNEST(ARRAY(1)) AS t(col INT)
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -n \"class TableAlias\" -A14 sqlglot/expressions/query.py; grep -rn \"ColumnDef\" sqlglot/optimizer/*.py | head", "description": "Inspect TableAlias definition and optimizer ColumnDef usage"}
[tool_result] 467:class TableAlias(Expression):
468-    arg_types = {"this": False, "columns": False}
469-
470-    @property
471-    def columns(self) -> list[t.Any]:
472-        return self.args.get("columns") or []
473-
474-
475-class BitString(Expression, Condition):
476-    is_primitive = True
477-
478-
479-class HexString(Expression, Condition):
480-    arg_types = {"this": True, "is_integer": False}
481-    is_primitive = True
sqlglot/optimizer/annotate_types.py:311:                            if isinst
…[229 chars elided]…
  exp.ColumnDef(
sqlglot/optimizer/annotate_types.py:808:    def _annotate_struct_value(self, expression: exp.Expr) -> exp.DataType | None | exp.ColumnDef:
sqlglot/optimizer/annotate_types.py:827:            return exp.ColumnDef(this=this, kind=kind)
sqlglot/optimizer/qualify_columns.py:663:    # All nested struct values are ColumnDefs, so normalize the first exp.Column in one
sqlglot/optimizer/qualify_columns.py:665:    starting_struct = exp.ColumnDef(this=dot_column.this, kind=dot_column.type)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        columns: Sequence[str | exp.Identifier] | None = None,\n    ) -> None:", "new_string": "        columns: Sequence[str | exp.Expr] | None = None,\n    ) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])", "new_string": "            alias.set(\n                \"columns\",\n                [exp.to_identifier(c) if isinstance(c, (str, exp.Identifier)) else c for c in columns],\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "                function_columns: Sequence[str | exp.Identifier] | None = None", "new_string": "                function_columns: Sequence[str | exp.Expr] | None = None"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor s in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(col INT, b VARCHAR)', 'SELECT * FROM fn() AS t(col)']:\n    for c in [True, False]:\n        print(qualify_tables(sqlglot.parse_one(s), canonicalize_table_aliases=c).sql())\n\"; grep -n \"qualify_tables\" tests/*.py | head; cat tests/fixtures/optimizer/qualify_tables.sql | head -40", "description": "Re-run repro and locate qualify_tables test fixtures"}
[tool_result] SELECT * FROM FN() AS _0(col INT)
SELECT * FROM FN() AS t(col INT)
SELECT * FROM FN() AS _0(col INT, b VARCHAR)
SELECT * FROM FN() AS t(col INT, b VARCHAR)
SELECT * FROM FN() AS _0(col)
SELECT * FROM FN() AS t(col)
tests/test_optimizer.py:42:    expression = optimizer.qualify_tables.qualify_tables(expression)
tests/test_optimizer.py:248:    def test_qualify_tables(self):
tests/test_optimizer.py:269:            optimizer.qualify_tables.qualify_tables(
tests/test_optimizer.py:280:            optim
…[1099 chars elided]…
tables;

# title: information schema with db, catalog
# dialect: bigquery
SELECT * FROM x.y.information_schema.tables;
SELECT * FROM x.y.`information_schema.tables` AS tables;

# title: information schema with db, catalog, alias
# dialect: bigquery
SELECT * FROM x.y.information_schema.tables AS z;
SELECT * FROM x.y.`information_schema.tables` AS z;

# title: redshift unnest syntax, z.a should be a column, not a table
# dialect: redshift
SELECT 1 FROM y.z AS z, z.a;
SELECT 1 FROM c.y.z AS z, z.a;
[tool_use Bash] {"command": "sed -n 248,300p tests/test_optimizer.py", "description": "Read existing qualify_tables unit tests"}
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
                
…[1059 chars elided]…
* FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",
        )

        self.assertEqual(
            optimizer.qualify_tables.qualify_tables(
                parse_one("select a from b"), catalog="catalog"
            ).sql(),
            "SELECT a FROM b AS b",
        )

        self.assertEqual(
            optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"').sql(),
            'SELECT a FROM "DB".b AS b',
        )
[assistant] Reproduction now passes. I'll add a regression assertion next to the existing `qualify_tables` tests, then run the optimizer tests and the project's check command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(\n            optimizer.qualify_tables.qualify_tables(parse_one(\"select a from b\"), db='\"DB\"').sql(),\n            'SELECT a FROM \"DB\".b AS b',\n        )", "new_string": "        se
…[61 chars elided]…
_tables(parse_one(\"select a from b\"), db='\"DB\"').sql(),\n            'SELECT a FROM \"DB\".b AS b',\n        )\n\n        self.assertEqual(\n            optimizer.qualify_tables.qualify_tables(\n                parse_one(\"SELECT * FROM fn() AS t(col INT)\"),\n                canonicalize_table_aliases=True,\n            ).sql(),\n            \"SELECT * FROM FN() AS _0(col INT)\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165540-optimizer-qualifying-a-table-fun/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -15; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run optimizer tests and full test suite"}
[tool_result] ...... [  7%]
....................................................... [ 80%]
...............                                     [100%]
76 passed, 3704 subtests passed in 15.99s
.......... [ 64%]
..................................... [ 68%]
............................................... [ 72%]
.................................................................................................................... [ 83%]
.............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1089 passed, 17847 subtests passed in 50.75s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ($P -m ruff check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py && $P -m ruff format --check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
Would reformat: sqlglot/optimizer/qualify_tables.py
1 file would be reformatted, 1 file already formatted
 sqlglot/optimizer/qualify_tables.py | 9 ++++++---
 tests/test_optimizer.py             | 8 ++++++++
 2 files changed, 14 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format --diff sqlglot/optimizer/qualify_tables.py 2>&1 | head -30", "description": "Show the formatter diff for qualify_tables"}
[tool_result] --- sqlglot/optimizer/qualify_tables.py
+++ sqlglot/optimizer/qualify_tables.py
@@ -99,7 +99,10 @@
         if columns:
             alias.set(
                 "columns",
-                [exp.to_identifier(c) if isinstance(c, (str, exp.Identifier)) else c for c in columns],
+                [
+                    exp.to_identifier(c) if isinstance(c, (str, exp.Identifier)) else c
+                    for c in columns
+                ],
             )
 
         expression.set("alias", alias)

1 file would be reformatted
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format sqlglot/optimizer/qualify_tables.py && $P -m ruff format --check sqlglot/optimizer/qualify_tables.py tests/test_optimizer.py && git diff", "description": "Apply formatter and show final diff"}
[tool_result] 1 file reformatted
2 files already formatted
diff --git a/sqlglot/optimizer/qualify_tables.py b/sqlglot/optimizer/qualify_tables.py
index ffd2c1dec..ca6b1a84c 100644
--- a/sqlglot/optimizer/qualify_tables.py
+++ b/sqlglot/optimizer/qualify_tables.py
@@ -80,7 +80,7 @@ def qualify_tables(
         target_alias: str | None = None,
         scope: Scope | None = None,
         normalize: bool = False,
-        columns: Sequence[str | exp.Identifier] | None = None,
+        columns: Sequence[str | ex
…[1310 chars elided]…
 self.assertEqual(
+            optimizer.qualify_tables.qualify_tables(
+                parse_one("SELECT * FROM fn() AS t(col INT)"),
+                canonicalize_table_aliases=True,
+            ).sql(),
+            "SELECT * FROM FN() AS _0(col INT)",
+        )
+
         self.check_file(
             "qualify_tables",
             optimizer.qualify_tables.qualify_tables,
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_tables.py. Call Read before editing.]
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Re-run full test suite after formatting"}
[tool_result] .......................................................................... [100%]
1089 passed, 17847 subtests passed in 49.22s
[assistant] Fixed. `qualify_tables` now keeps typed table-alias columns like `t(col INT)` intact instead of crashing.

**Cause:** in `sqlglot/optimizer/qualify_tables.py`, `_set_alias` ran every alias column through `exp.to_identifier()`. That works for names (strings or identifiers), but a typed column is a `ColumnDef` node, so it raised the `ValueError`.

**Change:**
- `_set_alias` only converts `str` and `exp.Identifier` columns. Anything else, such as a `ColumnDef`, is passed through unchanged.
- The type hints for `columns` / `function_columns` now allow `exp.Expr`.

**Result:**
- `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` now gives `SELECT * FROM FN() AS _0(col INT)`.
- Untyped aliases such as `t(col)` behave as before.
- With `canonicalize_table_aliases=False`, the alias is kept as written, `t(col INT)`.

**Test:** I added one assertion for the reported case to `test_qualify_tables` in `tests/test_optimizer.py`. The full suite passes (1089 passed) and ruff check and format are clean on both files. I did not run `make check`, which also includes mypy.

The change is uncommitted in the worktree.
