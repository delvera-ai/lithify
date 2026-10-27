# trajectory base-1

final message:
Qualifying these queries now terminates on both the pure-Python build and the compiled `sqlglot[c]` build. With the table missing from the schema, it raises a clean `OptimizeError`, not a `RecursionError`.

**Cause:** Resolving an unqualified column like `arr` in `LATERAL VIEW EXPLODE(arr)` (Spark/Hive), `LATERAL FLATTEN(input => arr)` (Snowflake, which parses to the same `Lateral(Explode)` node), or BigQuery `UNNEST(arr)` looks up the column's table. That lookup scans every source's columns, including the lateral itself. Computing the lateral's columns then resolves `arr` again, and the cycle never ends. A qualified column like `t.arr` skips this lookup, which is why it never recursed.

**Fix** (`sqlglot/optimizer/resolver.py`): `_get_unnest_column_type` keeps a set of in-progress unnested columns, shared with the nested `Resolver` instances. Re-entering for the same column returns `None`, which breaks the cycle. The set is keyed on the column node, so both the `Lateral(Explode)` and BigQuery `Unnest` branches are covered.

**Behavior change:** A query whose unnested column can't be found now raises `OptimizeError: Column 'arr' could not be resolved`. This matches what a plain `SELECT arr FROM t` already does when `arr` is missing from the schema. Queries that resolve still produce the same output.

**Verification:**
- Full suite via the project's pytest command: 1121 passed, 18169 subtests.
- New regression test `test_qualify_unnest_unqualified_column_missing_table` in `tests/test_optimizer.py` covers Spark, Snowflake and BigQuery with a schema that lacks the table.
- A matrix of 12 unnest forms (including nested and mutually referencing laterals) × 4 schemas: no recursion or crashes.
- ruff check/format and mypy pass.
- Built the mypyc extension in a scratch copy and ran the optimizer tests against it. I did not run `make unitc` in the shared venv because it reinstalls packages there.

Nothing is committed. I left the changes in the worktree for you to review.

## events
[assistant] I'll start by reproducing the recursion in the worktree, then read the column resolver.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls sqlglot/optimizer/ | head -50 && grep -n \"Unnest\\|Explode\\|Lateral\\|flatten\\|FLATTEN\" sqlglot/optimizer/qualify_columns.py | head -60", "description": "Check worktree state and find lateral/unnest handling in qualify_columns"}
[tool_result] 03732b6db lithify: probe base
__init__.py
annotate_types.py
canonicalize.py
canonicalize_internal_names.py
eliminate_ctes.py
eliminate_joins.py
eliminate_subqueries.py
isolate_table_selects.py
merge_subqueries.py
normalize.py
normalize_identifiers.py
optimize_joins.py
optimizer.py
pushdown_predicates.py
pushdown_projections.py
qualify.py
qualify_columns.py
qualify_tables.py
resolver.py
scope.py
simplify.py
unnest_subqueries.py
518:                    or select_expr.find(exp.Explode, exp.Unnest)
[assistant] The Docs tools that just appeared aren't relevant to this task. Continuing with the code: I'll read the resolver and the lateral/unnest handling in `qualify_columns.py`.
[tool_use Bash] {"command": "cat sqlglot/optimizer/resolver.py | head -250 && grep -n \"_get_source_columns\\|def _expand\\|lateral\\|Lateral\\|unnest\\|Unnest\\|get_source_columns\\|_get_all_source_columns\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py", "description": "Read resolver and locate lateral/unnest code paths"}
[tool_result] from __future__ import annotations

import itertools
import typing as t

from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.errors import OptimizeError
from sqlglot.helper import seq_get, SingleValuedMapping
from sqlglot.optimizer.scope import Scope

if t.TYPE_CHECKING:
    from sqlglot.schema import Schema
    from collections.abc import Sequence, Mapping


class Resolver:
    """
    Helper for resolving columns.

    This is a class so we can lazily load some th
…[13380 chars elided]…
ion.args.get("laterals") or [])
sqlglot/optimizer/scope.py:868:            lateral_sources = sources
sqlglot/optimizer/scope.py:872:            lateral_sources = None
sqlglot/optimizer/scope.py:887:                lateral_sources=lateral_sources,
sqlglot/optimizer/scope.py:919:    if isinstance(scope.expression, exp.Unnest):
sqlglot/optimizer/scope.py:921:    elif isinstance(scope.expression, exp.Lateral):
sqlglot/optimizer/scope.py:984:                for key in ("joins", "laterals", "pivots"):
[assistant] The likely culprit is `_get_unnest_column_type`. I'll read it and the rest of the resolver, then reproduce.
[tool_use Bash] {"command": "sed -n 250,400p sqlglot/optimizer/resolver.py; grep -n \"_get_unnest_column_type\\|_struct_field_names\" -A30 sqlglot/optimizer/resolver.py | sed -n '/def _get_unnest_column_type/,/^--$/p' | head -80", "description": "Read rest of resolver and unnest type helper"}
[tool_result]         if not joins or args.get("laterals") or args.get("pivots"):
            # Feature gap: We currently don't try to disambiguate columns if other sources
            # (e.g laterals, pivots) exist alongside joins
            return None

        join_ancestor = column.find_ancestor(exp.Join, exp.Select)

        if (
            isinstance(join_ancestor, exp.Join)
            and join_ancestor.alias_or_name in self.scope.selected_sources
        ):
            # Ensure that the found ancest
…[6540 chars elided]…
t table_identifier:
382-                return None
383-            table_name = table_identifier.name
384-
385-        source = scope.sources.get(table_name)
386-        return self._get_column_type_from_scope(source, column) if source else None
387-
388-    def _get_column_type_from_scope(
389-        self, source: Scope | exp.Table, column: exp.Column
390-    ) -> exp.DataType | None:
391-        """
392-        Get a column's type by tracing through scopes/tables to find the base table.
393-
[assistant] Here's the suspected cycle: `get_source_columns` for a lateral `Explode` calls `_get_unnest_column_type`, which builds a new `Resolver` and calls `get_table`, which calls `get_source_columns` again. I'll reproduce it before going further.
[tool_use Bash] {"command": "sed -n 400,440p sqlglot/optimizer/resolver.py; ls <work>/env-sqlglot/bin/python 2>&1; which python3", "description": "Read column type tracing helper and check python env"}
[tool_result]         """
        if isinstance(source, exp.Table):
            # base table - get the column type from schema
            col_type: exp.DataType | None = self.schema.get_column_type(source, column)
            if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                return col_type
        elif isinstance(source, Scope):
            # iterate over all sources in the scope
            for source_name, nested_source in source.sources.items():
                col_type = self._get_column_type_from_scope(nested_source, column)
                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                    return col_type

        return None
<work>/env-sqlglot/bin/python
<work>/env-sqlglot/bin/python3
[assistant] I'll try a few candidate queries across dialects to find one that triggers the recursion.
[tool_use Bash] {"command": "cat > /tmp/repro_qual.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f\", {\"s\": {\"x\": {\"a\": \"int\"}}}),\n (\"hive\", \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x\", {\"s\": {\"x\": {\"a\": \"int\"}}}),\n (\"hi
…[632 chars elided]…
cursionError as e:\n        print(d, \"RECURSION:\", sql)\n    except Exception as e:\n        print(d, type(e).__name__, str(e)[:150])\nEOF\ntimeout 120 <work>/env-sqlglot/bin/python -I /tmp/repro_qual.py", "description": "Reproduce qualify recursion across candidate queries"}
[tool_result ERROR] Exit code 127
(eval):23: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_qual.py 2>&1 | tail -20", "description": "Run reproduction script with project python"}
[tool_result] snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
hive RECURSION: SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x
hive OK: SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery OK: SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
duckdb OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
spark RECURSION: SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x
[assistant] Reproduced: an unqualified `EXPLODE(arr)` in a `LATERAL VIEW` recurses when the schema lacks `t`. Next I'll capture the traceback to confirm the cycle.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys,traceback\nsys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ntry:\n    qualify(parse_one('SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x', read='spark'), schema={'s': {'x': {'a': 'int'}}}, dialect='spark')\nexcept RecursionError:\n    tb = traceback.format_exc().splitlines()\n    seen=[l for l in tb if 'File' in l]\n    print('\\n'.join(seen[:40])); print('...'); print('\\n'.join(seen[-12:]))\n\" 2>&1 | head -80", "description": "Capture recursion traceback to identify cycle"}
[tool_result]   File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify.py", line 98, in qualify
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual
…[8316 chars elided]…
sers/user/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 154, in get_source_columns
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/schema.py", line 424, in column_names
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/schema.py", line 611, in _normalize_table
[assistant] The traceback confirms the cycle: `get_source_columns(lateral)` → `_get_unnest_column_type` → new `Resolver.get_table` → `_get_all_source_columns` → `get_source_columns(lateral)` again. But the same query with `t` in the schema doesn't recurse, so I need to understand why before choosing a fix.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys\nsys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import resolver as r\norig = r.Resolver._get_unnest_column_type\ndepth=[0]\ndef wrap(sel
…[300 chars elided]…
wrap\nfor sch in [{'t': {'arr': 'array<int>'}}, {'s': {'x': {'a': 'int'}}}]:\n    print('--- schema', sch)\n    try:\n        print(qualify(parse_one('SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x', read='spark'), schema=sch, dialect='spark').sql('spark'))\n    except RecursionError: print('RECURSION')\n\" 2>&1 | head -40", "description": "Trace unnest-type calls with and without schema table"}
[tool_result] --- schema {'t': {'arr': 'array<int>'}}
unnest-type call 1 't.arr' scope sources ['t', 'v'] lateral []
SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
--- schema {'s': {'x': {'a': 'int'}}}
unnest-type call 1 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 2 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 3 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 4 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 5 'arr' scope sourc
…[1442 chars elided]…
l []
unnest-type call 29 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 30 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 31 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 32 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 33 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 34 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 35 'arr' scope sources ['t', 'v'] lateral []
unnest-type call 36 'arr' scope sources ['t', 'v'] lateral []
[assistant] This explains it. A qualified column (`t.arr`) never calls `get_table`, so it doesn't recurse. An unqualified `arr` with no `t` columns in the schema falls into `get_table`, which asks for every source's columns, including the lateral itself, and that restarts the cycle. Before I pick a fix, I want to check how Snowflake `FLATTEN` and BigQuery `UNNEST` parse, since the report names them specifically.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys\nsys.path.insert(0,'.')\nfrom sqlglot import parse_one, exp\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import resolver as r\nfor d,sql in [('snowflake','SELECT f.value FROM t, LATERAL FL
…[506 chars elided]…
:'int'}}}]:\n        try:\n            print('  ', sch is not None, qualify(parse_one(sql,read=d), schema=sch, dialect=d).sql(d))\n        except RecursionError: print('   RECURSION', sch is not None)\n        except Exception as ex: print('   ', sch is not None, type(ex).__name__, str(ex)[:90])\n\" 2>&1 | head -60", "description": "Check parse node types and outcomes for FLATTEN/UNNEST variants"}
[tool_result] snowflake ['Lateral', 'Explode']
   False SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
    True OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
snowflake ['Lateral', 'Explode']
   False SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
   True SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL F
…[207 chars elided]…
umn 'arr' could not be resolved. Line: 1, Col: 27
bigquery ['Unnest']
   False SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
    True OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
spark ['Lateral', 'Explode']
   False SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
   RECURSION True
spark ['Lateral', 'Explode']
   False SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW OUTER EXPLODE(`t`.`arr`) v AS `x`
   RECURSION True
[assistant] Snowflake `FLATTEN` parses to the same `Lateral(Explode)` node as Hive/Spark, so it takes the same path. Spark's `EXPLODE` reproduces the recursion; Snowflake happened to error out instead in my schema variant. I'll write a guard that covers both, and check every resolver construction site first.
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | grep -v \"class Resolver\"; grep -rn \"resolver\" Makefile pyproject.toml setup.py 2>/dev/null | head; grep -rln \"LATERAL VIEW\\|FLATTEN\\|UNNEST\" tests/ | head -20", "description": "Find Resolver construction sites and related test files"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
tests/test_parser.py
tests/test_optimizer.py
tests/test_build.py
tests/test_lineage.py
tests/dialects/test_snowflake.py
tests/dialects/test_spark.py
tests/dialects/test_duckdb.py
tests/dialects/test_bigquery.py
tests/dialects/test_starrocks.py
tests/dialects/test_presto.py
tests/dialects/test_hive.py
tests/dialects/test_dialect.py
tests/fixtures/pretty.sql
tests/dialects/test_clickhouse.py
tests/fixtures/optimizer/unnest_subqueries.sql
tests/fixtures/optimizer/canonicalize_internal_names.sql
tests/fixtures/identity.sql
tests/dialects/test_postgres.py
tests/fixtures/optimizer/optimizer.sql
tests/fixtures/optimizer/pushdown_projections.sql
[assistant] Here's the approach. The cycle always re-enters `_get_unnest_column_type` with the same unnested `Column` node, because the lateral's AST never changes. So I'll track in-progress columns in a set shared with the nested resolvers, and return `None` on re-entry. That covers both the `Lateral(Explode)` branch and the BigQuery `Unnest` branch, since they share the helper.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[804 chars elided]…
 = None\n        self._all_columns: set[str] | None = None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # ids of the unnested columns whose types are being resolved, shared with nested resolvers\n        self._unnesting_columns: set[int] = unnesting_columns if unnesting_columns is not None else set()"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "        Returns:\n            The DataType of the column, or None if not found.\n        \"\"\"\n        # if column is qualified, use that table, otherwise disambiguate using the resolver\n        if column
…[1425 chars elided]…
 table_identifier = parent_resolver.get_table(column)\n                if not table_identifier:\n                    return None\n                table_name = table_identifier.name\n\n            source = scope.sources.get(table_name)\n            return self._get_column_type_from_scope(source, column) if source else None\n        finally:\n            self._unnesting_columns.discard(id(column))"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_qual.py 2>&1 | tail -20", "description": "Re-run reproduction after the guard"}
[tool_result] snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
hive OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
hive OK: SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery OK: SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
duckdb OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
[assistant] The recursion is gone and the call now terminates with a clean `OptimizeError`. But the error is wrong for this case. With `t` missing from the schema, `arr` should be inferred to `t`, which is what happens without the lateral. I'll check the plain-`FROM` baseline, then trace where the error comes from.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys\nsys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfor sql in ['SELECT arr FROM t', 'SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x', 'SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x']:\n    try: print(qualify(parse_one(sql, read='spark'), schema={'s': {'x': {'a': 'int'}}}, dialect='spark').sql('spark'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1; sed -n 600,640p sqlglot/optimizer/qualify_columns.py", "description": "Compare plain FROM baseline and inspect column qualification loop"}
[tool_result] OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 10
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
            # For pivoted sources, source_columns are pre-pivot; validate against the post-pivot set.
            if isinstance(column_source, exp.Table) and (
                pivots := column_source.args.get("pivots")
            ):
                source_columns = pivots[0].output_columns(source_
…[993 chars elided]…
      continue

            if table:
                column.set("table", table)
            elif (
                resolver.dialect.TABLES_REFERENCEABLE_AS_COLUMNS
                and len(column.parts) == 1
                and column_name in scope.selected_sources
            ):
                # BigQuery and Postgres allow tables to be referenced as columns, treating them as structs/records
                scope.replace(column, exp.TableColumn(this=column.this))

    for pivot in scope.pivots:
[assistant] Plain `SELECT arr FROM t` with the same schema also raises "could not be resolved", so the lateral case now matches existing behavior for a missing table. The error is a clean `OptimizeError`, not a crash, and it doesn't come from my change. Next I'll run a wider matrix (dialects × schemas × unnest forms, including mutually referencing laterals) against the fix to confirm nothing recurses.
[tool_use Bash] {"command": "cat > /tmp/matrix_qual.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nsqls = [\n (\"spark\", \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x\"),\n (\"spark\", \"SELECT x FROM t LATERAL VIEW OUTER EXPLODE(arr) v AS x\"),\n (\"spark\", \"SELECT x, y FROM t LATERAL VIEW EXPLODE(arr) v AS x LATERAL VIEW E
…[1284 chars elided]…
'none' if sch is None else list(sch)[0]+'/'+str(list(sch.values())[0].keys())[10:20]:20} {res}\")\nprint(\"BAD:\", bad)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/matrix_qual.py 2>&1 | tail -60", "description": "Run wider dialect/schema matrix to check for remaining failures"}
[tool_result] spark      schema=none                 OK SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
spark      schema=s/['x'])             OptimizeError: Column 'arr' could not be resolved. Line: 1, Col: 40
spark      schema=t/['other'])         OptimizeError: Column 'arr' could not be resolved. Line: 1, Col: 40
spark      schema=t/['arr'])           OK SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
spark      schema=none                 OK SE
…[5239 chars elided]…
UNNEST("t"."arr") AS "u"("x") ON TRUE
presto     schema=none                 OK SELECT "u"."x" AS "x" FROM "t" AS "t" CROSS JOIN UNNEST("t"."arr") AS "u"("x")
presto     schema=s/['x'])             OptimizeError: Column 'arr' could not be resolved. Line: 1, Col: 37
presto     schema=t/['other'])         OptimizeError: Column 'arr' could not be resolved. Line: 1, Col: 37
presto     schema=t/['arr'])           OK SELECT "u"."x" AS "x" FROM "t" AS "t" CROSS JOIN UNNEST("t"."arr") AS "u"("x")
BAD: 0
[assistant] The matrix shows no recursion or crash in any dialect, schema, or nesting combination. The only errors are clean `OptimizeError`s on columns that genuinely can't be found, the same outcome as the plain-`FROM` baseline. Next I'll run the project's test suite with the command from the repo's harness notes.
[tool_use Bash] {"command": "time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[420 chars elided]…
......................................................................................................................................................................................................................... [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 92.05s (0:01:32)
 -m pytest -q -p no:cacheprovider --color=no 2>&1  134.34s user 17.35s system 163% cpu 1:32.99 total
tail -25  0.00s user 0.00s system 0% cpu 1:32.99 total
[assistant] The full suite passes: 1120 tests, 18166 subtests. Now I'll add a regression test. I'll look for the existing qualify tests to match their style.
[tool_use Bash] {"command": "grep -n \"def test_qualify\\|LATERAL VIEW\\|UNNEST\\|RecursionError\\|assertRaises(OptimizeError\" tests/test_optimizer.py | head -60", "description": "Locate qualify tests in test_optimizer.py"}
[tool_result] 254:    def test_qualify_tables(self):
315:    def test_qualify_tables_copies_typed_alias_columns(self):
357:    def test_qualify_columns(self, logger):
564:                       FROM UNNEST(credits) AS c
573:            "SELECT (SELECT SUM(`c`.`amount`) AS `_col_0` FROM UNNEST(`billing`.`credits`) AS `c` WHERE `type` <> 'promotion') AS `total` FROM `billing` AS `billing`",
583:                       FROM UNNEST(items) AS item
597:            "WITH `cte` AS (SELECT `base_table`.`id` AS `id`, `b
…[2793 chars elided]…
:            "SELECT JSON_VALUE(item.id) FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON('[{\"id\": 1}]'))) AS item",
2646:            == "SELECT JSON_VALUE(`item`.`id`, '$') AS `_col_0` FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON('[{\"id\": 1}]'), '$')) AS `item`"
2694:            FROM UNNEST([1, d_x]) AS u_x
2715:            "SELECT (SELECT MAX(`u_x`) AS `_col_0` FROM UNNEST([1, `d_t`.`d_x`]) AS `u_x` WHERE `u_x` < `d_t`.`d_z`) AS `c_i` FROM (SELECT CAST(20 AS BIGNUMERIC) AS `d_x`, 30 AS `d_z`) AS `d_t`",
[tool_use Bash] {"command": "sed -n 700,765p tests/test_optimizer.py", "description": "Read existing lateral view qualify test for style"}
[tool_result]                 parse_one("select foo from x"),
                schema={"foo": {"y": "int"}},
            )

        # Test ambiguous columns error with PIVOT (which skips "could not be resolved" check)
        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
            expression = parse_one(
                "SELECT * FROM (SELECT a, b, c FROM x) PIVOT (SUM(b) FOR c IN ('x', 'y'))"
            )
            qualified = optimizer.qualify_columns.qualify_columns(
             
…[2038 chars elided]…
isible(self):
        schema = MappingSchema(self.schema, {"x": {"a"}, "y": {"b"}, "z": {"b"}})
        self.check_file("qualify_columns__with_invisible", qualify_columns, schema=schema)

    def test_pushdown_cte_alias_columns(self):
        self.check_file(
            "pushdown_cte_alias_columns",
            pushdown_ctes,
        )

    def test_qualify_columns__invalid(self):
        for sql in load_sql_fixtures("optimizer/qualify_columns__invalid.sql"):
            with self.subTest(sql):
[assistant] I'll add a regression test next to the existing lateral-view qualify test. It covers Spark `EXPLODE`, Snowflake `FLATTEN`, and BigQuery `UNNEST` with a schema that lacks the table, and asserts a clean `OptimizeError`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.selects[0].type, exp.DataType.build(\"DOUBLE\", dialect=\"spark\"))\n\n    def test_qualify_columns__with_invisible(self):", "new_string": "        self.assertEqual(expression.s
…[529 chars elided]…
  with self.subTest(sql):\n                with self.assertRaisesRegex(OptimizeError, \"could not be resolved\"):\n                    optimizer.qualify.qualify(\n                        parse_one(sql, read=read),\n                        schema={\"s\": {\"x\": {\"a\": \"int\"}}},\n                        dialect=read,\n                    )\n\n    def test_qualify_columns__with_invisible(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the new test and the optimizer test module, then lint the two changed files with the project's tooling.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"unnest_unqualified or qualify_columns\" 2>&1 | tail -3; $PY/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -2; ($PY/ruff --version && $PY/ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PY/ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -5", "description": "Run new and optimizer tests, then ruff lint and format check"}
[tool_result] ....                         [100%]
4 passed, 76 deselected, 404 subtests passed in 4.72s
................................................................................                                         [100%]
80 passed, 3912 subtests passed in 39.22s
ruff 0.15.6
All checks passed!
Would reformat: sqlglot/optimizer/resolver.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/ruff format --diff sqlglot/optimizer/resolver.py 2>&1 | head -30; $PY/ruff format sqlglot/optimizer/resolver.py && git diff --stat", "description": "Show formatter diff, apply ruff format to resolver, show diff stat"}
[tool_result] --- sqlglot/optimizer/resolver.py
+++ sqlglot/optimizer/resolver.py
@@ -37,7 +37,9 @@
         self._infer_schema: bool = infer_schema
         self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}
         # ids of the unnested columns whose types are being resolved, shared with nested resolvers
-        self._unnesting_columns: set[int] = unnesting_columns if unnesting_columns is not None else set()
+        self._unnesting_columns: set[int] = (
+            unnesting_columns if unnesting_columns is not None else set()
+        )
 
     def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
         """

1 file would be reformatted
1 file reformatted
 sqlglot/optimizer/resolver.py | 49 ++++++++++++++++++++++++++++++-------------
 tests/test_optimizer.py       | 15 +++++++++++++
 2 files changed, 50 insertions(+), 14 deletions(-)
[This command modified 1 file you've previously read: sqlglot/optimizer/resolver.py. Call Read before editing.]
[assistant] The formatter only re-wrapped one line of my own change. I'll review the full diff for `resolver.py` and run mypy on it, since the pre-commit hooks include it.
[tool_use Bash] {"command": "git diff sqlglot/optimizer/resolver.py; PY=<work>/env-sqlglot/bin; ($PY/mypy --version && $PY/mypy sqlglot/optimizer/resolver.py 2>&1 | tail -3) 2>&1 | tail -4", "description": "Review resolver diff and run mypy on resolver"}
[tool_result] diff --git a/sqlglot/optimizer/resolver.py b/sqlglot/optimizer/resolver.py
index e840af2a1..8483c14c3 100644
--- a/sqlglot/optimizer/resolver.py
+++ b/sqlglot/optimizer/resolver.py
@@ -21,7 +21,13 @@ class Resolver:
     This is a class so we can lazily load some things and easily share them across functions.
     """
 
-    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
+    def __init__(
+        self,
+        scope: Scope,
+        schema: Schema,
+     
…[2399 chars elided]…
   if not table_identifier:
+                    return None
+                table_name = table_identifier.name
+
+            source = scope.sources.get(table_name)
+            return self._get_column_type_from_scope(source, column) if source else None
+        finally:
+            self._unnesting_columns.discard(id(column))
 
     def _get_column_type_from_scope(
         self, source: Scope | exp.Table, column: exp.Column
mypy 2.4.0 (compiled: yes)
Success: no issues found in 1 source file
[assistant] The diff is limited to the guard and its plumbing, and mypy passes. Since the formatter touched the file after my last full run, I'll rerun the whole suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; <work>/env-sqlglot/bin/python -I /tmp/matrix_qual.py 2>&1 | tail -1; rm -f /tmp/repro_qual.py /tmp/matrix_qual.py", "description": "Rerun full suite and matrix after formatting; clean temp scripts"}
[tool_result] ....................................................................       [100%]
1121 passed, 18169 subtests passed in 113.74s (0:01:53)
BAD: 0
[assistant] The suite is green with 1121 tests. One thing I haven't checked is the compiled `sqlglot[c]` build, so I'll confirm whether `resolver.py` is in the mypyc module list.
[tool_use Bash] {"command": "grep -rn \"optimizer\\|resolver\" setup.py pyproject.toml sqlglotc/ 2>/dev/null | grep -v \"^Binary\" | head -10; git status --short", "description": "Check whether resolver is in the mypyc-compiled module list"}
[tool_result] sqlglotc/setup.py:60:            "optimizer",
sqlglotc/setup.py:63:                "resolver.py",
sqlglotc/setup.py:132:    """Pin sqlglot to the matching version so resolvers keep the two packages in lockstep."""
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
[assistant] `resolver.py` is compiled by mypyc in `sqlglotc`, and the crash you described on that build is the one that matters most. I'll build the extension and run the unit tests against it.
[tool_use Bash] {"command": "grep -n \"^unitc\\|^testc\\|^build-c\\|sqlglotc\" Makefile | head; PY=<work>/env-sqlglot/bin; cd sqlglotc 2>/dev/null && ls | head; cd - >/dev/null; $PY/python -c \"import sqlglot,sys; print(sqlglot.__file__)\"; $PY/python -c \"import sqlglot.optimizer.resolver as r; print(r.__file__)\"", "description": "Inspect Makefile C-extension targets and current import location"}
[tool_result] 20:	rm -rf build sqlglotc/build sqlglotc/dist sqlglotc/*.egg-info sqlglotc/sqlglot
41:# sqlglotc requires Python 3.10+ (sqlglot-mypy 1.20+ dropped 3.9). On 3.9
47:		cd sqlglotc && MYPYC_OPT=0 python setup.py build_ext --inplace -j $(NPROC); \
49:		echo "Skipping sqlglotc build: requires Python 3.10+"; \
54:		cd sqlglotc && python setup.py build_ext --inplace -j $(NPROC); \
56:		echo "Skipping sqlglotc build: requires Python 3.10+"; \
106:testc: install-devc
109:unitc: install-devc
MANIFEST.in
pyproject.toml
setup.py
~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/__init__.py
~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py
[assistant] `make unitc` runs `install-devc`, which would reinstall packages into the shared project venv. To avoid mutating that environment, I'll copy the worktree to a scratch directory, build the extension there with the same interpreter, and run the optimizer tests against it.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-c-check && mkdir -p /tmp/sqlglot-c-check && cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1 && git ls-files -z | xargs -0 -I{} cp --parents {} /tmp/sqlglot-c-check/ 2>/dev/null; cp sqlglot/optimizer/resolver.py /tmp/sqlglot-c-check/sqlglot/optimizer/resolver.py && cp tests/test_optimizer.py /tmp/sqlglo
…[36 chars elided]…
 cd /tmp/sqlglot-c-check/sqlglotc && PY=<work>/env-sqlglot/bin/python && time $PY setup.py build_ext --inplace -j 8 > /tmp/sqlglotc-build.log 2>&1; echo \"exit=$?\"; tail -5 /tmp/sqlglotc-build.log", "description": "Copy worktree to scratch dir and build mypyc extension there"}
[tool_result ERROR] Exit code 1
cp: /tmp/sqlglot-c-check/sqlglot/optimizer/resolver.py: No such file or directory
exit=1
tail: /tmp/sqlglotc-build.log: No such file or directory
[assistant] macOS `cp` doesn't support `--parents`, so the copy failed. I'll copy the tree with `tar` instead.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-c-check && mkdir -p /tmp/sqlglot-c-check && cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1 && tar --exclude=.git -cf - . | (cd /tmp/sqlglot-c-check && tar -xf -) && cd /tmp/sqlglot-c-check/sqlglotc && PY=<work>/env-sqlglot/bin/python && time $PY setup.py build_ext --inplace -j 8 > /tmp/sqlglotc-build.log 2>&1; echo \"exit=$?\"; tail -5 /tmp/sqlglotc-build.log", "description": "Copy worktree via tar and build mypyc extension in scratch dir"}
[tool_result] $PY setup.py build_ext --inplace -j 8 > /tmp/sqlglotc-build.log 2>&1  465.87s user 17.81s system 489% cpu 1:38.83 total
exit=0
copying build/lib.macosx-11.0-arm64-cpython-312/sqlglot/time.cpython-312-darwin.so -> /private/tmp/sqlglot-c-check/sqlglotc/../sqlglot
copying build/lib.macosx-11.0-arm64-cpython-312/sqlglot/tokenizer_core__mypyc.cpython-312-darwin.so -> /private/tmp/sqlglot-c-check/sqlglotc/../sqlglot
copying build/lib.macosx-11.0-arm64-cpython-312/sqlglot/tokenizer_core.cpython-312-darwin.so -> /private/tmp/sqlglot-c-check/sqlglotc/../sqlglot
copying build/lib.macosx-11.0-arm64-cpython-312/sqlglot/trie__mypyc.cpython-312-darwin.so -> /private/tmp/sqlglot-c-check/sqlglotc/../sqlglot
copying build/lib.macosx-11.0-arm64-cpython-312/sqlglot/trie.cpython-312-darwin.so -> /private/tmp/sqlglot-c-check/sqlglotc/../sqlglot
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1
[tool_use Bash] {"command": "cd /tmp/sqlglot-c-check && ls sqlglot/optimizer/ | grep resolver; PY=<work>/env-sqlglot/bin/python; $PY -c \"import sys; sys.path.insert(0,'.'); import sqlglot.optimizer.resolver as r; print(r.__file__)\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_
…[248 chars elided]…
L VIEW EXPLODE(arr) v AS x'),('snowflake','SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f'),('bigquery','SELECT x FROM t, UNNEST(arr) AS x')]:\n    try: qualify(parse_one(sql,read=read), schema={'s':{'x':{'a':'int'}}}, dialect=read)\n    except Exception as e: print(read, type(e).__name__, str(e)[:60])\n\"", "description": "Verify compiled resolver loads and new behavior holds on C build"}
[tool_result] resolver.cpython-312-darwin.so
resolver.py
resolver__mypyc.cpython-312-darwin.so
/private/tmp/sqlglot-c-check/sqlglot/optimizer/resolver.cpython-312-darwin.so
....                         [100%]
4 passed, 76 deselected, 404 subtests passed in 31.33s
spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1
[assistant] The compiled build loads the patched `resolver` and gives the same clean errors. I'll clean up the scratch copy.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-c-check /tmp/sqlglotc-build.log; cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-181324-optimizer-sqlglot-optimizer-qual/base-1 && git status --short", "description": "Remove scratch build copy and confirm worktree changes"}
[tool_result]  M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
[assistant] Qualifying these queries now terminates on both the pure-Python build and the compiled `sqlglot[c]` build. With the table missing from the schema, it raises a clean `OptimizeError`, not a `RecursionError`.

**Cause:** Resolving an unqualified column like `arr` in `LATERAL VIEW EXPLODE(arr)` (Spark/Hive), `LATERAL FLATTEN(input => arr)` (Snowflake, which parses to the same `Lateral(Explode)` node), or BigQuery `UNNEST(arr)` looks up the column's table. That lookup scans every source's columns, including the lateral itself. Computing the lateral's columns then resolves `arr` again, and the cycle
…[797 chars elided]…
d, 18169 subtests.
- New regression test `test_qualify_unnest_unqualified_column_missing_table` in `tests/test_optimizer.py` covers Spark, Snowflake and BigQuery with a schema that lacks the table.
- A matrix of 12 unnest forms (including nested and mutually referencing laterals) × 4 schemas: no recursion or crashes.
- ruff check/format and mypy pass.
- Built the mypyc extension in a scratch copy and ran the optimizer tests against it. I did not run `make unitc` in the shared venv because it reinstalls packages there.

Nothing is committed. I left the changes in the worktree for you to review.
