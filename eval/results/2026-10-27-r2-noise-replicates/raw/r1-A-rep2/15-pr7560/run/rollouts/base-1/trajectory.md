# trajectory base-1

final message:
Both queries now qualify correctly, and the full suite passes (1092 passed, exit 0). The changes are uncommitted in the worktree.

**The bug:** Star expansion already handled pivots, but the explicit-column check (`SELECT u.v` / `SELECT c.v`) validated against the CTE's pre-pivot columns, so `v` was rejected as "Unknown column". It affected both aliased and unaliased UNPIVOTs.

**The fix** (`sqlglot/optimizer/qualify_columns.py`):
- Extracted the pivot output-column logic from `_expand_stars` into `_pivot_columns(pivot, columns)`. Star expansion calls it with the same results as before.
- The explicit-column validation now calls the same helper for a pivoted source, so `v` resolves against the post-UNPIVOT columns.
- I left `Resolver.get_source_columns` and `get_table` alone on purpose. Columns inside the pivot clause (like `jan` in `IN (jan, feb)`) still need to resolve against the CTE's own columns.

**Tests** (`tests/test_optimizer.py`): added the aliased-UNPIVOT-over-CTE case with its expected BigQuery output, plus a negative check that `u.jan` (a column the UNPIVOT consumed) still raises "Unknown column: jan". Those assertions sit inside the existing UNPIVOT test method.

**Checks:** full pytest suite passes, ruff format/check clean, mypy clean on `qualify_columns.py`.

**Notes:**
- I didn't reproduce a star-expansion failure: `SELECT *` over both UNPIVOT forms already expanded correctly in my runs, so if you saw one, it likely needs a schema or a different query shape. Tell me the input and I'll check.
- I haven't run the queries against live BigQuery; the verification is `qualify()` output in BigQuery and DuckDB dialects.
- Unrelated quirk I left alone: the star path applies a scope's pivot to every table in a `SELECT *`, not only the pivoted one. It shows up with a join next to a pivoted source. Say if you want it fixed too.

## events
[assistant] I'll start by reproducing both failing queries against the current code.
[tool_use Bash] {"command": "git status --short && <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR m IN (\\'a\\'))']\nfor q in qs:\n  for d in ['bigquery','duckdb']:\n    try:\n      print(d, qualify(sqlglot.parse_one(q,read=d),dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',type(e).__name__,e)\n\"", "description": "Check git status and reproduce both queries"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The env python doesn't have sqlglot installed as a package, so I'll point it at this worktree's source.
[tool_use Bash] {"command": "git status --short; cat > /tmp/repro_pivot.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR m IN (\\'a\\'))']\nfor q in qs:\n  for d in ['bigquery','duckdb']:\n    try:\n      print(d, qualify(sqlglot.parse_one(q,read=d),dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',type(e).__name__,e)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/repro_pivot.py", "description": "Reproduce the UNPIVOT-over-CTE qualify failures"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
bigquery ERR OptimizeError Unknown column: v
duckdb ERR OptimizeError Unknown column: v
bigquery ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
duckdb ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
[assistant] Both reported queries fail or mis-resolve. Unaliased `SELECT *` yields `c.id, c.m, c.v`, which looks right, but the aliased `u.v` fails with "Unknown column: v". I'll look at how the optimizer builds pivot output columns.
[tool_use Bash] {"command": "grep -rn -i \"pivot\" sqlglot/optimizer/*.py | head -80", "description": "Find pivot handling in optimizer modules"}
[tool_result] sqlglot/optimizer/eliminate_subqueries.py:125:    # - drop the "pivot" arg from a pivoted subquery
sqlglot/optimizer/eliminate_subqueries.py:128:    if not parent_scope or parent_scope.pivots or isinstance(parent_scope.expression, exp.Lateral):
sqlglot/optimizer/merge_subqueries.py:209:        and not outer_scope.pivots
sqlglot/optimizer/resolver.py:142:            # A pivoted CTE reference is stored as an exp.Table in the scope sources (see
sqlglot/optimizer/resolver.py:144:            # column
…[5119 chars elided]…
s]
sqlglot/optimizer/qualify_columns.py:870:                    pivot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns.py:872:                    pivot_columns = pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:874:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:876:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:877:                        for name in pivot_columns
[tool_use Bash] {"command": "sed -n 120,160p sqlglot/optimizer/resolver.py && echo ---- && sed -n 770,900p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 600,660p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 180,200p sqlglot/optimizer/qualify_columns.py", "description": "Read resolver and qualify_columns pivot code"}
[tool_result]             # We use dict.fromkeys to deduplicate keys and maintain insertion order
            if side == "LEFT":
                columns = left
            elif side == "FULL":
                columns = list(dict.fromkeys(left + right))
            elif kind == "INNER":
                columns = list(dict.fromkeys(left).keys() & dict.fromkeys(right).keys())
        else:
            columns = set_op.named_selects

        return columns

    def get_source_columns(self, name: str, only_visible
…[9549 chars elided]…
fier]:
    name_columns = [
        field.this
        for field in unpivot.fields
        if isinstance(field, exp.In) and isinstance(field.this, exp.Identifier)
    ]
    value_columns = (
        ident
        for e in unpivot.expressions
        for ident in (e.expressions if isinstance(e, exp.Tuple) else [e])
        if isinstance(ident, exp.Identifier)
    )

    return itertools.chain(name_columns, value_columns)


def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
[assistant] The star path already has pivot-aware output logic (`pivot_output_columns`), but the explicit-column path validates `u.v` against `resolver.get_source_columns`, which returns only the CTE's pre-pivot columns. I'll confirm what the scope sources look like in the aliased case.
[tool_use Bash] {"command": "cat > /tmp/dbg_pivot.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.resolver import Resolver\nfor q in ['WITH c AS (SELECT id, jan, feb FR
…[431 chars elided]…
, s.cte_sources.keys() if hasattr(s,'cte_sources') else None)\n    print(e.sql(\"bigquery\"))\n    print()\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/dbg_pivot.py; grep -n \"def get_table\\|def get_source_columns\\|def all_columns\\|class Resolver\" sqlglot/optimizer/resolver.py", "description": "Inspect scope sources for pivoted CTE queries"}
[tool_result] Select {'t': 'Table'} [] dict_keys([])
Select {'c': 'Scope', 'u': 'Table'} ['u'] dict_keys(['c'])
WITH c AS (SELECT id, jan, feb FROM t AS t) SELECT u.v FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS u

Select {'t': 'Table'} [] dict_keys([])
Select {'c': 'Table'} ['c'] dict_keys(['c'])
WITH c AS (SELECT id, jan, feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS c

17:class Resolver:
34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
87:    def all_columns(self) -> set[str]:
95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
[assistant] The aliased case is the bug: source `u` is an `exp.Table` named `c` with pivots, and `get_source_columns` swaps in the CTE's columns but never applies the pivot. The unaliased star path does apply it, but in a separate code path. Next I'll read the resolver and find where `Pivot.columns` gets populated.
[tool_use Bash] {"command": "sed -n 1,95p sqlglot/optimizer/resolver.py && echo ---- && sed -n 160,200p sqlglot/optimizer/resolver.py && echo ---- && grep -n \"\\\"columns\\\"\" sqlglot/parser.py sqlglot/optimizer/*.py | head -20 && grep -n \"class Pivot\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -30", "description": "Read resolver and Pivot expression definition"}
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
…[7636 chars elided]…
sions": False,
sqlglot/expressions/query.py-1746-        "fields": False,
sqlglot/expressions/query.py-1747-        "unpivot": False,
sqlglot/expressions/query.py-1748-        "using": False,
sqlglot/expressions/query.py-1749-        "group": False,
sqlglot/expressions/query.py-1750-        "columns": False,
sqlglot/expressions/query.py-1751-        "include_nulls": False,
sqlglot/expressions/query.py-1752-        "default_on_null": False,
sqlglot/expressions/query.py-1753-        "into": False,
[assistant] Before designing a fix I want the full failure picture. I'll test a matrix: star vs explicit columns, aliased vs unaliased, UNPIVOT vs PIVOT with real columns, and a couple of dialects.
[tool_use Bash] {"command": "cat > /tmp/matrix.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nC=\"WITH c AS (SELECT id, jan, feb FROM t) \"\nqs = {\n \"star-unalias-unpivot\": C+\"SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n \"star-alias-unpivot\": C+\"SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n \"col-alias-unpivot\": C+\"SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, f
…[607 chars elided]…
   out = qualify(sqlglot.parse_one(q,read=d),dialect=d).sql(d)\n      print(f\"{name:22} {d:10} OK  {out.split('SELECT',2)[-1][:150]}\")\n    except Exception as e: print(f\"{name:22} {d:10} ERR {type(e).__name__}: {e}\")\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/matrix.py", "description": "Run qualify matrix over pivot/unpivot CTE variants"}
[tool_result] star-unalias-unpivot   bigquery   OK   `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
star-unalias-unpivot   duckdb     OK   "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
star-unalias-unpivot   snowflake  OK   "C"."ID" AS "ID", "C"."M" AS "M", "C"."V" AS "V" FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
star-alias-unpivot     bigquery   OK   `u`
…[2623 chars elided]…
1, 2)) AS p
col-unalias-pivot      bigquery   ERR OptimizeError: Unknown column: 1
col-unalias-pivot      duckdb     ERR ParseError: Invalid expression / Unexpected token. Line 1, Col: 50.
  WITH c AS (SELECT id, jan, feb FROM t) SELECT c.`[4m1[0m` FROM c PIVOT(SUM(feb) FOR jan IN (1, 2))
col-unalias-pivot      snowflake  ERR ParseError: Invalid expression / Unexpected token. Line 1, Col: 50.
  WITH c AS (SELECT id, jan, feb FROM t) SELECT c.`[4m1[0m` FROM c PIVOT(SUM(feb) FOR jan IN (1, 2))
[assistant] Findings from the matrix:

- **Explicit-column validation is the broken path.** `SELECT u.v` and `SELECT c.v` over an UNPIVOT fail with "Unknown column", for both aliased and unaliased pivots.
- **Star expansion already works** for these strings, so the star path just needs to share the logic, not be fixed.
- The PIVOT column cases in my matrix were malformed (a backtick-quoted `1`), so I'll redo those separately.

The fix belongs in `qualify_columns.py`. The star path computes post-pivot columns inline, and the validation check at line ~612 uses the pre-pivot CTE columns. I'll extract the star path's logic into a helper and reuse it in validation. I'm keeping `get_source_columns` and `get_table` unchanged, because pivot-clause columns like `jan` still have to resolve against the CTE's pre-pivot columns. First I'll check the `alias_column_names` type and the existing tests.
[tool_use Bash] {"command": "grep -n \"def alias_column_names\" -A 4 sqlglot/expressions/query.py && sed -n 600,615p sqlglot/optimizer/qualify_columns.py && grep -rn -i \"unpivot\\|pivot\" tests/fixtures/optimizer/*.sql | wc -l && grep -rln -i \"pivot\" tests/ | head -20", "description": "Check alias_column_names and pivot test coverage"}
[tool_result ERROR] Exit code 1
[tool_use Bash] {"command": "grep -rn \"alias_column_names\" sqlglot/expressions/*.py | head -5; sed -n 600,615p sqlglot/optimizer/qualify_columns.py; grep -rl -i \"pivot\" tests/ | head -20", "description": "Check alias_column_names and pivot tests"}
[tool_result] sqlglot/expressions/core.py:166:    def alias_column_names(self) -> list[str]:
sqlglot/expressions/core.py:678:    def alias_column_names(self) -> list[str]:
    allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring each column specifies a source"""
    for column in scope.columns:
        column_table = column.table
        column_name = column.name

        if column_table and column_table in scope.sources:
            source_columns = resolver.get_source_columns(
…[355 chars elided]…
t_optimizer.py
tests/test_transpile.py
tests/test_lineage.py
tests/dialects/test_drill.py
tests/dialects/test_databricks.py
tests/dialects/test_redshift.py
tests/dialects/test_spark.py
tests/dialects/test_snowflake.py
tests/dialects/test_duckdb.py
tests/dialects/test_oracle.py
tests/dialects/test_bigquery.py
tests/dialects/test_pipe_syntax.py
tests/fixtures/identity.sql
tests/fixtures/optimizer/optimizer.sql
tests/fixtures/optimizer/qualify_columns.sql
tests/fixtures/optimizer/qualify_tables.sql
[assistant] I'll get a baseline test run before editing so I can tell pre-existing failures from ones I cause.
[tool_use Bash] {"command": "time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite for baseline", "timeout": 900000}
[tool_result] Command did not complete within its 600s timeout and was moved to the background (ID: br339i7j9). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/br339i7j9.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "for i in $(seq 1 55); do if grep -q -E \"passed|failed|error\" /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/br339i7j9.output 2>/dev/null; then break; fi; sleep 10; done; tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/br339i7j9.output", "description": "Wait for baseline test run to finish", "timeout": 600000}
[tool_result] 1092 passed, 17864 subtests passed in 53.96s
<work>/env-sqlglot/bin/python -m   129.03s user 18.76s system 15% cpu 15:54.89 total
tail -15  0.00s user 0.00s system 0% cpu 15:54.89 total

[exited with code 0]
[assistant] Baseline is green: 1092 passed, 17864 subtests, exit 0. Now the change. I'm extracting the post-pivot column logic from the star path into `_pivot_columns` and calling it from the explicit-column validation too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    pivot_output_columns = None\n    pivot_exclude_columns: set[str] = set()\n\n    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n    if isinstance(pivot, exp.Pivot) and not pivot.a
…[445 chars elided]…
 set(c.output_name for c in pivot.find_all(exp.Column))\n\n            pivot_output_columns = [c.output_name for c in pivot.args.get(\"columns\", [])]\n            if not pivot_output_columns:\n                pivot_output_columns = [c.alias_or_name for c in pivot.expressions]\n\n    if dialect", "new_string": "    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n\n    if dialect"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            if pivot:\n                if pivot_output_columns and pivot_exclude_columns:\n                    pivot_columns = [c for c in columns if c not in pivot_exclude_columns]\n                    pivot_columns.extend(pivot_output_columns)\n                else:\n                    pivot_columns = pivot.alias_column_names\n\n                if pivot_columns:", "new_string": "            if pivot:\n                pivot_columns = _pivot_columns(pivot, columns)\n                if pivot_columns:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)\n            if (", "new_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)\n            if source_columns and (\n                pivot := next((p for p in scope.pivots if p.alias == column_table), None)\n            ):\n                source_columns = _pivot_columns(pivot, source_columns)\n            if ("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    return itertools.chain(name_columns, value_columns)\n\n", "new_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pivot_columns(pivot: exp.Pivot, columns: t.Sequence[str])
…[529 chars elided]…
   else:\n        exclude_columns = {c.output_name for c in pivot.find_all(exp.Column)}\n        output_columns = [c.output_name for c in pivot.args.get(\"columns\", [])] or [\n            c.alias_or_name for c in pivot.expressions\n        ]\n\n    if not exclude_columns or not output_columns:\n        return []\n\n    return [c for c in columns if c not in exclude_columns] + output_columns\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Now I'll rerun the matrix and the two reported queries against the edited code.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/matrix.py 2>&1 | grep -v \"pivot  *\\(bigquery\\|duckdb\\|snowflake\\)  *ERR ParseError\" ; PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/repro_pivot.py", "description": "Rerun matrix and repro after the fix"}
[tool_result] star-unalias-unpivot   bigquery   OK   `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
star-unalias-unpivot   duckdb     OK   "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
star-unalias-unpivot   snowflake  OK   "C"."ID" AS "ID", "C"."M" AS "M", "C"."V" AS "V" FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
star-alias-unpivot     bigquery   OK   `u`
…[3497 chars elided]…
TH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "u"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "u"
bigquery ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
duckdb ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
[assistant] Both reported queries now qualify correctly in BigQuery and DuckDB. The unaliased-PIVOT `c.1` error is my test's fault: an unaliased non-UNPIVOT pivot gets the generated alias `_0`, so `c.1` isn't valid SQL. The `m` error is also my bogus input, since `m` is not a column of `c`. Next I'll check the failure mode for a genuinely missing column and then look at the existing fixtures to add tests.
[tool_use Bash] {"command": "cat > /tmp/neg.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nC=\"WITH c AS (SELECT id, jan, feb FROM t) \"\nfor q in [C+\"SELECT u.jan FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n          C+\"SELECT u.nope FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n          \"SELECT u.v FROM (SELECT id, jan, feb FROM t) UNPIVOT(v FOR m IN (jan, feb)) AS u\"]:\n   
…[71 chars elided]…
ct=\"duckdb\").sql(\"duckdb\"))\n    except Exception as e: print(\"ERR\", type(e).__name__, e)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/neg.py; grep -n -i \"pivot\" tests/fixtures/optimizer/qualify_columns.sql | head -40; grep -n -i \"pivot\" tests/test_optimizer.py | head", "description": "Check negative cases and existing pivot fixtures"}
[tool_result] ERR OptimizeError Unknown column: jan
ERR OptimizeError Unknown column: nope
OK  SELECT "u"."v" AS "v" FROM (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") AS "_0" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "u"
269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 O
…[1939 chars elided]…
ITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",
639:                    "SELECT * FROM produce UNPIVOT(sales FOR quarter IN (q1, q2))",
647:            "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`",
659:        # Test ambiguous columns error with PIVOT (which skips "could not be resolved" check)
662:                "SELECT * FROM (SELECT a, b, c FROM x) PIVOT (SUM(b) FOR c IN ('x', 'y'))"
[assistant] Negative cases still raise, and the derived-table UNPIVOT now resolves. Next I'll add regression tests next to the existing UNPIVOT tests in `tests/test_optimizer.py`.
[tool_use Bash] {"command": "sed -n 625,675p tests/test_optimizer.py", "description": "Read existing UNPIVOT tests in test_optimizer"}
[tool_result]         self.assertEqual(
            optimizer.qualify.qualify(
                parse_one("SELECT * FROM t"),
                schema={"t": {"end": "text"}},
                quote_identifiers=False,
            ).sql(),
            "SELECT t.end AS end FROM t AS t",
        )

        self.assertEqual(
            optimizer.qualify.qualify(
                parse_one(
                    "WITH produce AS (SELECT 'Kale' AS product, 51 AS q1, 23 AS q2) "
                    "SELECT * FROM produce U
…[1221 chars elided]…
                expression, schema={"x": {"a": "int", "b": "int", "c": "str"}}
            )
            optimizer.qualify_columns.validate_qualify_columns(qualified)

        schema = {"my_table": {"items": "ARRAY<STRUCT<name STRING, age INT>>"}}
        expression = annotate_types(
            optimizer.qualify.qualify(
                parse_one(
                    "SELECT ci.name, ci.age FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci",
                    read="spark",
                ),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "old_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`\",\n        )\n\n    def test_validate_columns(self):", "new_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (
…[650 chars elided]…
`feb`)) AS `u`\",\n        )\n\n        with self.assertRaisesRegex(OptimizeError, \"Unknown column: jan\"):\n            optimizer.qualify.qualify(\n                parse_one(\n                    \"WITH c AS (SELECT id, jan, feb FROM t) \"\n                    \"SELECT u.jan FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n                ),\n            )\n\n    def test_validate_columns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the targeted test, then the whole suite in the background and the repo's style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"validate or qualify\" 2>&1 | tail -15; grep -n \"^style\" -A 4 Makefile", "description": "Run targeted optimizer tests and check style target", "timeout": 600000}
[tool_result] .......                                [100%]
7 passed, 70 deselected, 466 subtests passed in 2.58s
84:style:
85-	pre-commit run --all-files
86-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
87-
88-check: style test testc
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30) ; ls <work>/env-sqlglot/bin/ | grep -E \"^(ruff|mypy)$\"", "description": "Run full test suite after the fix", "timeout": 600000}
[tool_result] Command did not complete within its 600s timeout and was moved to the background (ID: blwoc03cm). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/blwoc03cm.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] While the suite runs, I'll check formatting. The env has no ruff binary, so I'll look for one on PATH and check line lengths against the project config.
[tool_use Bash] {"command": "which ruff pre-commit 2>/dev/null; grep -n \"line-length\" pyproject.toml setup.cfg ruff.toml .ruff.toml 2>/dev/null; git diff -U0 | grep \"^+\" | awk 'length > 101 {print length\": \"$0}'", "description": "Check ruff availability and added line lengths"}
[tool_result] <work>/env-sqlglot/bin/ruff
<work>/env-sqlglot/bin/pre-commit
pyproject.toml:47:line-length = 100
109: +            "WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) "
107: +            "SELECT `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`",
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/ruff; $R format --diff sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1 | head -60; $R check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1 | tail -3", "description": "Check ruff format and lint on changed files"}
[tool_result] 2 files already formatted
All checks passed!
[assistant] Ruff passes, but two of my expected-output string lines run past the project's 100-column limit. I'll wrap them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "old_string": "            \"WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) \"\n            \"SELECT `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`\",", "new_string": "            \"WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` \"\n            \"FROM `t` AS `t`) SELECT `u`.`v` AS `v` FROM `c` AS `c` \"\n            \"UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-183700-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/ruff; $R format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && $R check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"validate or qualify\" 2>&1 | tail -2", "description": "Recheck format, lint, and targeted tests", "timeout": 300000}
[tool_result] 2 files already formatted
All checks passed!
.......                                [100%]
7 passed, 70 deselected, 466 subtests passed in 2.70s
[tool_use Bash] {"command": "for i in $(seq 1 55); do if grep -q -E \"passed|failed|rror\" /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/blwoc03cm.output 2>/dev/null; then break; fi; sleep 10; done; tail -30 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-fdb04f649b80-20261027-183700-optimizer-un-pivot-over-cte-sour-base-1/3f648c8f-dcbb-4cda-a19e-c2e1bdea7550/tasks/blwoc03cm.output", "description": "Wait for full test suite result", "timeout": 600000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
................................................................................................ [ 20%]
..................... [ 22%]
............................................................................................................... [ 32%]
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................
…[364 chars elided]…
................................................................................... [ 76%]
............................................. [ 80%]
....................................................................................... [ 88%]
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 54.30s
mypy
ruff

[exited with code 0]
[assistant] The full suite is green (1092 passed, exit 0, same count as baseline since the new assertions live inside an existing test method). The pre-commit config also runs mypy, so I'll run it on the changed module.
[tool_use Bash] {"command": "timeout 500 <work>/env-sqlglot/bin/mypy sqlglot/optimizer/qualify_columns.py 2>&1 | tail -5; git diff --stat", "description": "Run mypy on changed module and show diff stat", "timeout": 540000}
[tool_result] (eval):1: command not found: timeout
 sqlglot/optimizer/qualify_columns.py | 56 ++++++++++++++++++++----------------
 tests/test_optimizer.py              | 22 ++++++++++++++
 2 files changed, 53 insertions(+), 25 deletions(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/mypy sqlglot/optimizer/qualify_columns.py 2>&1 | tail -5", "description": "Run mypy on the changed optimizer module", "timeout": 540000}
[tool_result] Success: no issues found in 1 source file
[assistant] mypy is clean. I'll review the final diff once before reporting.
[tool_use Bash] {"command": "git diff sqlglot/optimizer/qualify_columns.py", "description": "Review the source diff"}
[tool_result] diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..6ef2b9907 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -197,6 +197,32 @@ def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
     return itertools.chain(name_columns, value_columns)
 
 
+def _pivot_columns(pivot: exp.Pivot, columns: t.Sequence[str]) -> list[str]:
+    """The columns a PIVOT / UNPIVOT produces over a source 
…[2771 chars elided]…
s and pivot_exclude_columns:
-                    pivot_columns = [c for c in columns if c not in pivot_exclude_columns]
-                    pivot_columns.extend(pivot_output_columns)
-                else:
-                    pivot_columns = pivot.alias_column_names
-
+                pivot_columns = _pivot_columns(pivot, columns)
                 if pivot_columns:
                     new_selections.extend(
                         alias(exp.column(name, table=pivot.alias), name, copy=False)
[assistant] Both queries now qualify correctly, and the full suite passes (1092 passed, exit 0). The changes are uncommitted in the worktree.

**The bug:** Star expansion already handled pivots, but the explicit-column check (`SELECT u.v` / `SELECT c.v`) validated against the CTE's pre-pivot columns, so `v` was rejected as "Unknown column". It affected both aliased and unaliased UNPIVOTs.

**The fix** (`sqlglot/optimizer/qualify_columns.py`):
- Extracted the pivot output-column logic from `_expand_stars` into `_pivot_columns(pivot, columns)`. Star expansion calls it with the same results as before.
- The 
…[664 chars elided]…
clean on `qualify_columns.py`.

**Notes:**
- I didn't reproduce a star-expansion failure: `SELECT *` over both UNPIVOT forms already expanded correctly in my runs, so if you saw one, it likely needs a schema or a different query shape. Tell me the input and I'll check.
- I haven't run the queries against live BigQuery; the verification is `qualify()` output in BigQuery and DuckDB dialects.
- Unrelated quirk I left alone: the star path applies a scope's pivot to every table in a `SELECT *`, not only the pivoted one. It shows up with a join next to a pivoted source. Say if you want it fixed too.
