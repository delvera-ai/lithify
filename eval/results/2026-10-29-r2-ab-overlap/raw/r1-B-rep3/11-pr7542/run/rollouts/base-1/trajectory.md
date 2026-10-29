# trajectory base-1

final message:
Fixed. `qualify_tables` no longer crashes on a table function with a typed column alias list, and the `ColumnDef` nodes stay intact.

**Cause:** `_set_alias` in `sqlglot/optimizer/qualify_tables.py` converted every alias column with `exp.to_identifier`, which only accepts strings or identifiers. A typed column like `col INT` is a `ColumnDef`, so it raised.

**Change:** in `_set_alias`, `ColumnDef` entries are kept as they are and everything else is still converted to an identifier. I also widened the type hints for `columns` and `function_columns` to include `exp.ColumnDef`.

Output after the fix:
- `SELECT * FROM fn() AS t(col INT)` → `SELECT * FROM FN() AS t(col INT)`
- With `canonicalize_table_aliases=True` → `SELECT * FROM FN() AS _0(col INT)`
- Untyped aliases (`AS t(a, b)`) behave as before.

The `FN()` upper-casing is existing behavior for anonymous functions, so I left it alone.

**Tests:**
- Added one case to `tests/fixtures/optimizer/qualify_tables.sql`, with the duckdb dialect and canonical aliases. I chose the dialect myself because your example didn't specify one. I didn't edit any existing test.
- Full suite: 1089 passed, 17848 subtests passed.
- `ruff check` and `ruff format --check` pass on the changed file.

I haven't committed anything. The change is in the working tree for you to review.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/qualify_tables.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nprint(repr(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)')))\nprint(qualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicalize_table_aliases=True).sql())\n\"", "description": "Show qualify_tables source and reproduce the error"}
[tool_result ERROR] Exit code 1
from __future__ import annotations

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
    db: str | exp.
…[8918 chars elided]…
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
[assistant] Reproduced: `_set_alias` passes the alias's `ColumnDef` nodes through `exp.to_identifier`, which only accepts strings or identifiers. I'll let `ColumnDef` nodes through unchanged and widen the type hints to match.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        columns: Sequence[str | exp.Identifier] | None = None,\n    ) -> None:", "new_string": "        columns: Sequence[str | exp.Identifier | exp.ColumnDef] | None = None,\n    ) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])", "new_string": "            alias.set(\n                \"columns\",\n                [c if isinstance(c, exp.ColumnDef) else exp.to_identifier(c) for c in columns],\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "                function_columns: Sequence[str | exp.Identifier] | None = None", "new_string": "                function_columns: Sequence[str | exp.Identifier | exp.ColumnDef] | None = None"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-175243-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"qualify_tables\" tests/test_optimizer.py | head -30", "description": "Find existing qualify_tables tests"}
[tool_result] 9 matches in 2 files:

248:0:
tests/test_optimizer.py:42:expression = optimizer.qualify_tables.qualify_tables(expression)
tests/test_optimizer.py:269:optimizer.qualify_tables.qualify_tables(
tests/test_optimizer.py:280:optimizer.qualify_tables.qualify_tables(
tests/test_optimizer.py:291:optimizer.qualify_tables.qualify_tables(
tests/test_optimizer.py:298:optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"')...
tests/test_optimizer.py:303:"qualify_tables",
tests/test_optimizer.py:304:optimizer.qualify_tables.qualify_tables,
tests/test_optimizer.py:921:optimizer.qualify_tables.qualify_tables,
[tool_use Bash] {"command": "sed -n 905,935p tests/test_optimizer.py && ls tests/fixtures/optimizer/ | grep qualify_tables && grep -n \"\" tests/fixtures/optimizer/qualify_tables.sql | tail -30", "description": "View qualify_tables test fixtures"}
[tool_result]             optimizer.eliminate_joins.eliminate_joins,
            pretty=True,
        )

    def test_eliminate_ctes(self):
        self.check_file(
            "eliminate_ctes",
            optimizer.eliminate_ctes.eliminate_ctes,
            pretty=True,
        )

    @patch("sqlglot.generator.logger")
    def test_merge_subqueries(self, logger):
        optimize = partial(
            optimizer.optimize,
            rules=[
                optimizer.qualify_tables.qualify_tables,
         
…[2007 chars elided]…
n_schema.tables;
tests/fixtures/optimizer/qualify_tables.sql:30:SELECT * FROM x.y.`information_schema.tables` AS tables;
tests/fixtures/optimizer/qualify_tables.sql:31:
tests/fixtures/optimizer/qualify_tables.sql:34:SELECT * FROM x.y.information_schema.tables AS z;
tests/fixtures/optimizer/qualify_tables.sql:35:SELECT * FROM x.y.`information_schema.tables` AS z;
tests/fixtures/optimizer/qualify_tables.sql:36:
tests/fixtures/optimizer/qualify_tables.sql:39:SELECT 1 FROM y.z AS z, z.a;
[+172 more]
[assistant] Let me check the output in both modes before adding a fixture case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor sql in ['SELECT * FROM fn() AS t(col INT)', 'SELECT * FROM fn() AS t(col INT, other VARCHAR) JOIN u ON TRUE', 'SELECT * FROM fn() AS t(a, b)']:\n    for c in (True, False):\n        print(c, qualify_tables(sqlglot.parse_one(sql), canonicalize_table_aliases=c).sql())\n\" && tail -5 tests/fixtures/optimizer/qualify_tables.sql | cat -A | tail -3 && grep -n \"def test_qualify_tables\" -A8 tests/test_optimizer.py", "description": "Check qualified output with and without canonical aliases"}
[tool_result] True SELECT * FROM FN() AS _0(col INT)
False SELECT * FROM FN() AS t(col INT)
True SELECT * FROM FN() AS _0(col INT, other VARCHAR) JOIN u AS _1 ON TRUE
False SELECT * FROM FN() AS t(col INT, other VARCHAR) JOIN u AS u ON TRUE
True SELECT * FROM FN() AS _0(a, b)
False SELECT * FROM FN() AS t(a, b)
cat: illegal option -- A
usage: cat [-belnstuv] [file ...]

thread 'main' (43779016) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
248:    def test_qualify_tables(self):
249-        tables = set()
250-        optimizer.qualify.qualify(
251-            parse_one("with foo AS (select * from bar) select * from foo join baz"),
252-            qualify_columns=False,
253-            on_qualify=lambda t: tables.add(t.name),
254-        )
255-        self.assertEqual(tables, {"bar", "baz"})
256-
[assistant] The output is correct in both modes (`FN()` upper-casing is existing behavior). Now I'll add a fixture case, following the file's format.
[tool_use Bash] {"command": "tail -n 8 tests/fixtures/optimizer/qualify_tables.sql", "description": "Show end of qualify_tables fixture file"}
[tool_result] SELECT g FROM GENERATE_SERIES(1,2) AS t(g);
SELECT g FROM GENERATE_SERIES(1, 2) AS t(g);

# title: Qualify GENERATE_SERIES with explicit column and canonicalize_table_aliases
# dialect: postgres
# canonicalize_table_aliases: true
SELECT g FROM GENERATE_SERIES(1,2) AS t(g);
SELECT g FROM GENERATE_SERIES(1, 2) AS _0(g);
[tool_use Bash] {"command": "printf '\\n# title: Qualify table function with typed column alias list\\n# dialect: duckdb\\n# canonicalize_table_aliases: true\\nSELECT * FROM fn() AS t(col INT);\\nSELECT * FROM FN() AS _0(col INT);\\n' >> tests/fixtures/optimizer/qualify_tables.sql && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"qualify\" 2>&1 | tail -n 15", "description": "Add fixture case and run qualify-related optimizer tests"}
[tool_result] ..... [100%]
5 passed, 71 deselected, 466 subtests passed in 2.20s
[assistant] The qualify tests pass. Now the full suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 15; <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/qualify_tables.py 2>&1 | tail -n 3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/qualify_tables.py 2>&1 | tail -n 3", "description": "Run full test suite and lint the changed file"}
[tool_result] .......................................................................................................................................... [ 48%]
.............................................. [ 52%]
.................... [ 54%]
...................................................... [ 59%]
.......... [ 60%]
....................................... [ 63%]
.......... [ 64%]
..................................... [ 68%]
............................................... [ 72%]
.................................................................................................................... [ 83%]
............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
.                                                                        [100%]
1089 passed, 17848 subtests passed in 45.96s
All checks passed!
1 file already formatted
[assistant] Fixed. `qualify_tables` no longer crashes on a table function with a typed column alias list, and the `ColumnDef` nodes stay intact.

**Cause:** `_set_alias` in `sqlglot/optimizer/qualify_tables.py` converted every alias column with `exp.to_identifier`, which only accepts strings or identifiers. A typed column like `col INT` is a `ColumnDef`, so it raised.

**Change:** in `_set_alias`, `ColumnDef` entries are kept as they are and everything else is still converted to an identifier. I also widened the type hints for `columns` and `function_columns` to include `exp.ColumnDef`.

Output after the 
…[127 chars elided]…
CT * FROM FN() AS _0(col INT)`
- Untyped aliases (`AS t(a, b)`) behave as before.

The `FN()` upper-casing is existing behavior for anonymous functions, so I left it alone.

**Tests:**
- Added one case to `tests/fixtures/optimizer/qualify_tables.sql`, with the duckdb dialect and canonical aliases. I chose the dialect myself because your example didn't specify one. I didn't edit any existing test.
- Full suite: 1089 passed, 17848 subtests passed.
- `ruff check` and `ruff format --check` pass on the changed file.

I haven't committed anything. The change is in the working tree for you to review.
