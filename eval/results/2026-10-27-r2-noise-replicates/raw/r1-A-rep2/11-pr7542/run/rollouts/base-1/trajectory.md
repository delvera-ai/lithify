# trajectory base-1

final message:
Qualifying a table function with a typed alias column list no longer raises. `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` now returns `SELECT * FROM FN() AS _0(col INT)`, and the `col INT` definition is kept.

**Cause:** For table functions with an explicit alias column list, `qualify_tables` passed the alias's own `ColumnDef` nodes back into `_set_alias`, which rebuilt them from names with `exp.to_identifier` and failed.

**Fix** (`sqlglot/optimizer/qualify_tables.py`): `_set_alias` only sets the alias columns when the alias doesn't already have them. The other paths pass columns only into a fresh or column-less alias, so they're unaffected.

**Test:** I added a case to `tests/fixtures/optimizer/qualify_tables.sql` using postgres `GENERATE_SERIES(1,2) AS t(g INT)`. I used a known function because an unknown name like `fn` gets uppercased by the optimizer, which is existing behavior I didn't change.

**Results:** `tests/test_optimizer.py` passes (76 tests, 3705 subtests), and the full suite passes (1089 tests, 17848 subtests). The changes are not committed.

## events
[tool_use Bash] {"command": "cat sqlglot/optimizer/qualify_tables.py && rtk <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)')))\n\"", "description": "Read qualify_tables and inspect parsed AST"}
[tool_result ERROR] Exit code 127
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
    db: str | ex
…[7692 chars elided]…
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
(eval):1: command not found: rtk
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\ne = sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)')\nprint(repr(e.args['from'].this.args['alias']))\nprint(repr(e.args['from'].this.this))\ntry:\n    print(qualify_tables(e, canonicalize_table_aliases=True).sql())\nexcept Exception as ex:\n    import traceback; traceback.print_exc()\n\"", "description": "Reproduce the error and inspect the parsed alias"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'from'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\ne = sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)')\nt = e.args['from'] if 'from' in e.args else e.args.get('from_')\nprint(repr(e.find(sqlglot.exp.Table).args.get('alias')))\nprint(repr(e.find(sqlglot.exp.Table).this))\ntry:\n    print(qualify_tables(e, canonicalize_table_aliases=True).sql())\nexcept Exception as ex:\n    import traceback; traceback.print_exc()\n\"", "description": "Reproduce the error and inspect the parsed alias"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 9, in <module>
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161909-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", line 153, in qualify_tables
    _set_alias(
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161909-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", line 100, in _set_alias
    alias.set("columns", [exp.to_identifier(c) f
…[136 chars elided]…
61909-optimizer-qualifying-a-table-fun/base-1/sqlglot/expressions/core.py", line 2789, in to_identifier
    raise ValueError(f"Name needs to be a string or an Identifier, got: {name.__class__}")
ValueError: Name needs to be a string or an Identifier, got: <class 'sqlglot.expressions.query.ColumnDef'>
TableAlias(
  this=Identifier(this=t, quoted=False),
  columns=[
    ColumnDef(
      this=Identifier(this=col, quoted=False),
      kind=DataType(this=DType.INT, nested=False))])
Anonymous(this=fn)
[assistant] The failure is in `_set_alias`: for a table function with an explicit alias column list, `function_columns` is set to the existing `ColumnDef` nodes, and `exp.to_identifier` rejects them. Let me check the existing fixtures before changing anything.
[tool_use Bash] {"command": "grep -n \"FROM fn\\|UNNEST\\|AS t(\" tests/fixtures/optimizer/qualify_tables.sql | head -30; grep -n \"qualify_tables\" tests/test_optimizer.py | head; grep -n \"def columns\" -A3 sqlglot/expressions/query.py | head", "description": "Find existing qualify_tables tests and fixtures"}
[tool_result] 45:SELECT results FROM c.db.Coordinates AS coordinates CROSS JOIN UNNEST(coordinates.position) AS results;
50:SELECT results FROM c.db.coordinates AS coordinates CROSS JOIN UNNEST(Coordinates.position) AS results;
162:SELECT x FROM t, LATERAL UNNEST(t.xs) AS x;
163:SELECT x FROM c.db.t AS t, LATERAL UNNEST(t.xs) AS x;
166:SELECT x FROM t, LATERAL UNNEST(t.xs);
167:SELECT x FROM c.db.t AS t, LATERAL UNNEST(t.xs) AS _0;
276:SELECT g FROM GENERATE_SERIES(1,2) AS t(g);
277:SELECT g FROM GENERATE_SER
…[206 chars elided]…
alify_tables.qualify_tables(
280:            optimizer.qualify_tables.qualify_tables(
291:            optimizer.qualify_tables.qualify_tables(
298:            optimizer.qualify_tables.qualify_tables(parse_one("select a from b"), db='"DB"').sql(),
303:            "qualify_tables",
304:            optimizer.qualify_tables.qualify_tables,
921:                optimizer.qualify_tables.qualify_tables,
471:    def columns(self) -> list[t.Any]:
472-        return self.args.get("columns") or []
473-
474-
[tool_use Bash] {"command": "sed -n 270,300p tests/fixtures/optimizer/qualify_tables.sql; echo ---; sed -n 248,310p tests/test_optimizer.py", "description": "View table-function fixtures and qualify_tables tests"}
[tool_result] # dialect: postgres
SELECT g FROM GENERATE_SERIES(1,2) AS g;
SELECT g FROM GENERATE_SERIES(1, 2) AS _0(g);

# title: Qualify GENERATE_SERIES with alias on table and columns
# dialect: postgres
SELECT g FROM GENERATE_SERIES(1,2) AS t(g);
SELECT g FROM GENERATE_SERIES(1, 2) AS t(g);

# title: Qualify GENERATE_SERIES with explicit column and canonicalize_table_aliases
# dialect: postgres
# canonicalize_table_aliases: true
SELECT g FROM GENERATE_SERIES(1,2) AS t(g);
SELECT g FROM GENERATE_SERIES(1, 
…[1798 chars elided]…
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
[assistant] The existing fixture covers plain column names (`AS t(g)`) but not typed columns. The explicit-columns branch passes the alias's own `ColumnDef` nodes back into `_set_alias`, which then rebuilds them from names. Skipping that rebuild when the alias already has columns keeps the typed definitions intact, and it doesn't change the other paths, since those only pass columns into a fresh or column-less alias.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161909-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        if columns:\n            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])", "new_string": "        if columns and not alias.columns:\n            alias.set(\"columns\", [exp.to_identifier(c) for c in columns])"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161909-optimizer-qualifying-a-table-fun/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[assistant] Now I'll add a fixture for the typed case, next to the existing GENERATE_SERIES entries, and run the reproduction plus the test suite.
[tool_use Bash] {"command": "cat >> tests/fixtures/optimizer/qualify_tables.sql <<'EOF'\n\n# title: Qualify table function with typed column alias and canonicalize_table_aliases\n# dialect: duckdb\n# canonicalize_table_aliases: true\nSELECT * FROM fn() AS t(col INT);\nSELECT * FROM fn() AS _0(col INT);\nEOF\ntail -c 300 tests/fixtures/optimizer/qualify_tables.sql | od -c | tail -3; ~/.cache/lithify-d
…[119 chars elided]…
optimizer.qualify_tables import qualify_tables\nprint(qualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicalize_table_aliases=True).sql())\nprint(qualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)', read='duckdb'), canonicalize_table_aliases=True, dialect='duckdb').sql('duckdb'))\n\"", "description": "Add typed-alias fixture and verify the repro now works"}
[tool_result] 0000420    *       F   R   O   M       f   n   (   )       A   S       _
0000440    0   (   c   o   l       I   N   T   )   ;  \n                
0000454
SELECT * FROM FN() AS _0(col INT)
SELECT * FROM FN() AS _0(col INT)
[assistant] The repro now produces `FN() AS _0(col INT)`, with the typed column definition kept. Next I'll run the optimizer tests and then the full suite using the project's test command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -30", "description": "Run optimizer tests"}
[tool_result]                 future = pool.submit(parse_and_optimize, func, sql, dialect, **func_kwargs)
                results[future] = (
                    sql,
                    title,
                    expected,
                    dialect,
                    execute if meta.get("execute") is None else False,
                )
    
        for future in as_completed(results):
            sql, title, expected, dialect, execute = results[future]
    
            with self.subTest(title):
          
…[322 chars elided]…
E               - SELECT * FROM fn() AS _0(col INT)
E               ?               ^^
E               + SELECT * FROM FN() AS _0(col INT)
E               ?               ^^

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[Qualify table function with typed column alias and canonicalize_table_aliases] tests/test_optimizer.py::TestOptimizer::test_qualify_tables
1 failed, 76 passed, 3704 subtests passed in 14.56s
[assistant] The failure is in my fixture's expected output, not the fix. The optimizer uppercases unquoted unknown function names (`fn` → `FN`), so I'll switch the fixture to a known table function, `GENERATE_SERIES`, to match the existing fixtures and avoid that noise.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python - <<'EOF'\nimport re\np = \"tests/fixtures/optimizer/qualify_tables.sql\"\ns = open(p).read()\nold = \"\"\"# title: Qualify table function with typed column alias and canonicalize_table_aliases\n# dialect: duckdb\n# canonicalize_table_aliases: true\nSELECT * FROM fn() AS t(col INT);\nSELECT * FROM fn() AS _0(col
…[192 chars elided]…
RATE_SERIES(1,2) AS t(g INT);\nSELECT g FROM GENERATE_SERIES(1, 2) AS _0(g INT);\n\"\"\"\nassert s.count(old) == 1\nopen(p, \"w\").write(s.replace(old, new))\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -3", "description": "Switch fixture to GENERATE_SERIES and rerun optimizer tests"}
[tool_result] ...................................................... [ 78%]
................                                    [100%]
76 passed, 3705 subtests passed in 15.33s
[assistant] Optimizer tests pass. Now the full project check suite, plus a stash-free confirmation that the original repro passes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nprint(qualify_tables(sqlglot.parse_one('SELECT * FROM fn() AS t(col INT)'), canonicalize_table_aliases=True).sql())\n\"; git diff --stat", "description": "Run full test suite and verify diff"}
[tool_result] ............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
.                                                                        [100%]
1089 passed, 17848 subtests passed in 56.33s
SELECT * FROM FN() AS _0(col INT)
 sqlglot/optimizer/qualify_tables.py         | 2 +-
 tests/fixtures/optimizer/qualify_tables.sql | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] Qualifying a table function with a typed alias column list no longer raises. `SELECT * FROM fn() AS t(col INT)` with `canonicalize_table_aliases=True` now returns `SELECT * FROM FN() AS _0(col INT)`, and the `col INT` definition is kept.

**Cause:** For table functions with an explicit alias column list, `qualify_tables` passed the alias's own `ColumnDef` nodes back into `_set_alias`, which rebuilt them from names with `exp.to_identifier` and failed.

**Fix** (`sqlglot/optimizer/qualify_tables.py`): `_set_alias` only sets the alias columns when the alias doesn't already have them. The other paths pass columns only into a fresh or column-less alias, so they're unaffected.

**Test:** I added a case to `tests/fixtures/optimizer/qualify_tables.sql` using postgres `GENERATE_SERIES(1,2) AS t(g INT)`. I used a known function because an unknown name like `fn` gets uppercased by the optimizer, which is existing behavior I didn't change.

**Results:** `tests/test_optimizer.py` passes (76 tests, 3705 subtests), and the full suite passes (1089 tests, 17848 subtests). The changes are not committed.
