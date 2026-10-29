# trajectory base-1

final message:
Both failing shapes now qualify correctly, for aliased and unaliased pivots. The full suite passes (1092 tests, 17864 subtests), and the new assertions fail on the untouched `HEAD`. The changes are uncommitted in the worktree.

**The fix** (`sqlglot/optimizer/qualify_columns.py`): the column-existence check in `_disambiguate_columns` used the pre-pivot CTE columns for any source, so `u.v` was rejected. It now uses the pivot's visible columns (the source columns minus those the pivot consumes, plus its output columns) whenever the pivot alias matches the source name. The pivot output logic moved into `_pivot_output_columns`, which `_expand_stars` also uses, so the two can't drift apart.

**What changed in behavior:**
- `SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u` now resolves to `u.v`. It previously raised `Unknown column: v`.
- `SELECT c.v, c.m FROM c UNPIVOT(...)` now resolves too. It also previously raised `Unknown column: v`, which the task described for the unaliased case.
- `SELECT u.jan FROM c UNPIVOT(...) AS u` now raises `Unknown column: jan`, because `jan` is consumed by the unpivot.

**Star expansion:** I could not reproduce the star failure. `SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))` already expands to `id, m, v` through both `qualify` and `optimize`, in BigQuery, DuckDB, Snowflake and Spark, with and without a schema. The star path is unchanged in behavior and still covered. If you have a case that skips star expansion, send it and I'll look at that specifically.

**Known gap I did not fix:** `FROM c AS x UNPIVOT(...) AS u` (the CTE referenced under a different alias than its name) fails with `Ambiguous column 'jan'`. That shape already fails on `HEAD` (even `SELECT 1 ... FROM c AS x UNPIVOT(...)`), because the CTE stays registered as a source under its own name. My change only altered the error for the `u.v` variant of that query, from `Unknown column` to `Ambiguous column`. Fixing it means changing how `scope.py` registers referenced CTEs, which is a broader change than this task.

**Tests:** I added assertions to `test_qualify_columns` in `tests/test_optimizer.py`, next to the existing UNPIVOT-over-CTE case. They cover the aliased and qualified forms, the consumed-column rejection, and the expected SQL output. `ruff format`, `ruff check` and `mypy` are clean on the changed files.

## events
[assistant] I'll start by reproducing both failing queries against the current code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_columns import *\nqs = [\n ('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'),\n ('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v F
…[162 chars elided]…
TH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS c2 UNPIVOT(v FOR m IN (jan, feb)) AS u'),\n]\nfor d,q in qs:\n    try:\n        print(qualify(sqlglot.parse_one(q,read=d),dialect=d,schema={'t':{'id':'int','jan':'int','feb':'int'}}).sql(d))\n    except Exception as e: print('ERR',type(e).__name__,e)\n\"; git log --oneline -1", "description": "Reproduce the UNPIVOT-over-CTE qualify failures"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR OptimizeError Unknown column: v
ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 84)
61300712d lithify: probe base
[assistant] The repro confirms all three failure modes. Next I'll look at how the qualifier handles pivots.
[tool_use Bash] {"command": "grep -n -i \"pivot\" sqlglot/optimizer/*.py | head -80", "description": "Find pivot handling in optimizer modules"}
[tool_result] sqlglot/optimizer/eliminate_subqueries.py:125:    # - drop the "pivot" arg from a pivoted subquery
sqlglot/optimizer/eliminate_subqueries.py:128:    if not parent_scope or parent_scope.pivots or isinstance(parent_scope.expression, exp.Lateral):
sqlglot/optimizer/merge_subqueries.py:209:        and not outer_scope.pivots
sqlglot/optimizer/pushdown_projections.py:117:                    if scope.pivots or isinstance(select, exp.QueryTransform):
sqlglot/optimizer/qualify_columns.py:54:        - Cur
…[5119 chars elided]…
/optimizer/scope.py:483:        return self._pivots
sqlglot/optimizer/scope.py:813:                # it is pivoted, because then we get back a new table and hence a new source.
sqlglot/optimizer/scope.py:814:                pivots = expression.args.get("pivots")
sqlglot/optimizer/scope.py:815:                if pivots:
sqlglot/optimizer/scope.py:816:                    sources[pivots[0].alias] = expression
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "sed -n 120,180p sqlglot/optimizer/resolver.py && echo ---- && sed -n 110,185p sqlglot/optimizer/qualify_tables.py && echo ---- && sed -n 800,830p sqlglot/optimizer/scope.py", "description": "Read resolver, qualify_tables, and scope pivot code"}
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
…[6824 chars elided]…
urce_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
                sources[source_name] = expression

            # Make sure to not include the joins twice
            if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
[assistant] Pivoted CTE references are stored in `scope.sources` as `exp.Table` under the pivot alias. I'll dump the scope sources and resolver output to see where the lookup goes wrong.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.normalize_identifiers import normalize_identifiers\nfrom sqlglot.optimizer.qualify import qual
…[479 chars elided]…
()}, 'cte_sources:', list(s.cte_sources))\n    try:\n        qq = qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema={'t':{'id':'int','jan':'int','feb':'int'}}, validate_qualify_columns=False)\n        print('  ->', qq.sql('bigquery'))\n    except Exception as ex:\n        import traceback; print('  ERR', ex)\n\"", "description": "Inspect scope sources for pivoted CTE queries"}
[tool_result] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
  sources: {'c': 'Scope', '': 'Table'} cte_sources: ['c']
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  sources: {'c': 'Scope', 'u': 'Table'} cte_sources: ['c']
  ERR Unknown column: v
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR m IN ('a', 'b'))
  sources: {'c': 'Scope', '': 'Table'} cte_sources: ['c']
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `_0`.`id` AS `id`, `_0`.`feb` AS `feb`, `_0`.`a` AS `a`, `_0`.`b` AS `b` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `m` IN ('a', 'b')) AS `_0`
[assistant] Two of the three queries behave differently than the report implies. Query 1 expands without error here, and the aliased query fails with `Unknown column: v`. I'll check star expansion across dialects and with no schema, since the report says it is silently skipped.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nq1='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nq2='WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u'\nq3='WITH c AS (SELECT id, jan, feb FROM t) SELECT * 
…[185 chars elided]…
ark']:\n  for q in [q1,q2,q3,q4]:\n    for sch in [None, {'t':{'id':'int','jan':'int','feb':'int'}}]:\n      try:\n        print(d, sch is not None, qualify(sqlglot.parse_one(q,read=d),dialect=d,schema=sch).sql(d))\n      except Exception as ex: print(d, sch is not None, 'ERR', type(ex).__name__, ex)\n\" 2>&1 | cut -c1-400", "description": "Test star expansion across dialects and schema presence"}
[tool_result] bigquery False WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery True WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery False ERR OptimizeErro
…[4999 chars elided]…
 AS `u`
spark False WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `_0`.`id` AS `id`, `_0`.`1` AS `1`, `_0`.`2` AS `2` FROM (SELECT * FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `feb` IN (1, 2))) AS `_0`
spark True WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `_0`.`id` AS `id`, `_0`.`1` AS `1`, `_0`.`2` AS `2` FROM (SELECT * FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `feb` IN (1, 2))) AS `_0`
[assistant] Star expansion works for the unaliased UNPIVOT in every dialect I tried. The real break is the aliased form, where `u.v` can't resolve because the pivot's output columns are missing from the resolver's source columns. Next I'll look at how star expansion gets pivot columns and how the resolver looks up named sources.
[tool_use Bash] {"command": "sed -n 600,660p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 770,810p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 180,200p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 180,215p sqlglot/optimizer/resolver.py", "description": "Read pivot-related column qualification code"}
[tool_result]     allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring each column specifies a source"""
    for column in scope.columns:
        column_table = column.table
        column_name = column.name

        if column_table and column_table in scope.sources:
            source_columns = resolver.get_source_columns(column_table)
            if (
                not allow_partial_qualification
                and source_columns
                and column_name not in sourc
…[5458 chars elided]…
       # If the source's columns are aliased, their aliases shadow the corresponding column names.
                # This can be expensive if there are lots of columns, so only do this if column_aliases exist.
                columns = [
                    alias or name
                    for (name, alias) in itertools.zip_longest(columns, column_aliases)
                ]

            self._get_source_columns_cache[cache_key] = columns

        return self._get_source_columns_cache[cache_key]
[assistant] The resolver returns the CTE's pre-pivot columns for a pivoted source, so `u.v` can't match, and the unaliased path qualifies `c.v` against a source name that isn't in `scope.sources`, so that check is skipped entirely. Before designing the fix I'll check whether the same aliased pivot works over a real table, which would show the intended pattern.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nfor q in ['SELECT u.v FROM t UNPIVOT(v FOR m IN (jan, feb)) AS u','SELECT v, m FROM t UNPIVOT(v FOR m IN (jan, feb))','SELECT u.* FROM t UNPIVOT(v FOR m IN (jan, feb)) AS u',\n 'WITH c AS (SELECT
…[317 chars elided]…
u.\\`1\\` FROM c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS u']:\n  try: print(qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch).sql('bigquery'))\n  except Exception as ex: print('ERR',type(ex).__name__,ex)\n\"; grep -n \"^from\\|^import\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/resolver.py", "description": "Compare aliased pivot behavior over real table vs CTE"}
[tool_result] SELECT `u`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `u`
SELECT `t`.`v` AS `v`, `t`.`m` AS `m` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
ERR OptimizeError Unknown table: u
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FR
…[1437 chars elided]…
m __future__ import annotations
sqlglot/optimizer/resolver.py:3:import itertools
sqlglot/optimizer/resolver.py:4:import typing as t
sqlglot/optimizer/resolver.py:6:from sqlglot import exp
sqlglot/optimizer/resolver.py:7:from sqlglot.dialects.dialect import Dialect
sqlglot/optimizer/resolver.py:8:from sqlglot.errors import OptimizeError
sqlglot/optimizer/resolver.py:9:from sqlglot.helper import seq_get, SingleValuedMapping
sqlglot/optimizer/resolver.py:10:from sqlglot.optimizer.scope import Scope
[assistant] The real-table aliased form works, so there's an existing mechanism I should reuse. I'll instrument the resolver to see what it returns for `u` in that case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.resolver as r\norig = r.Resolver.get_source_columns\ndef dbg(self, name, only_visible=False):\n    res = orig(self, name, only_visible)\n    print('  get_source_columns', repr(name), '->', list(res))\n    return res\nr.Resolver.get_source_columns = dbg\nfrom sqlglo
…[88 chars elided]…
q in ['SELECT u.v FROM t UNPIVOT(v FOR m IN (jan, feb)) AS u','WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u']:\n  print(q)\n  try: print(qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch).sql('bigquery'))\n  except Exception as ex: print('ERR',ex)\n\"", "description": "Trace resolver source column lookups for aliased pivots"}
[tool_result] SELECT u.v FROM t UNPIVOT(v FOR m IN (jan, feb)) AS u
  get_source_columns 't' -> ['id', 'jan', 'feb']
  get_source_columns 't' -> ['id', 'jan', 'feb']
SELECT `u`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `u`
WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  get_source_columns 't' -> ['id', 'jan', 'feb']
  get_source_columns 't' -> ['id', 'jan', 'feb']
  get_source_columns 'c' -> ['id', 'jan', 'feb']
  get_source_columns 'u' -> ['id', 'jan', 'feb']
ERR Unknown column: v
[assistant] The real-table case passes only because `u` is never a key in `scope.sources`, so the check is skipped rather than satisfied. The CTE case is the one that gets checked, and its `u` resolves to the pre-pivot CTE columns. I need the star-expansion pivot logic to design a shared helper, so I'll read that block in full.
[tool_use Bash] {"command": "sed -n 810,890p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 136,150p sqlglot/optimizer/resolver.py && grep -n \"def \\|pivot\" sqlglot/optimizer/resolver.py | head -60", "description": "Read star expansion pivot column logic and resolver structure"}
[tool_result]         annotator.annotate_scope(scope)

    scope_expression = scope.expression

    if not isinstance(scope_expression, exp.Selectable):
        return

    for expression in scope_expression.selects:
        tables: list[str] = []
        if isinstance(expression, exp.Star):
            tables.extend(scope.selected_sources)
            _add_except_columns(expression, tables, except_columns)
            _add_replace_columns(expression, tables, replace_columns)
            _add_rename_columns(e
…[4279 chars elided]…
E reference is stored as an exp.Table in the scope sources (see
sqlglot/optimizer/resolver.py:144:# column information we need to resolve pre-pivot columns.
sqlglot/optimizer/resolver.py:148:and source.args.get("pivots")
sqlglot/optimizer/resolver.py:227:def _get_table_name_from_sources(
sqlglot/optimizer/resolver.py:252:# (e.g laterals, pivots) exist alongside joins
sqlglot/optimizer/resolver.py:296:def _get_unambiguous_columns(
sqlglot/optimizer/resolver.py:388:def _get_column_type_from_scope(
[assistant] Star expansion calls `get_source_columns` and then applies the pivot itself. So if I change the resolver to return post-pivot columns, the star path would apply the pivot twice. Before choosing between that and a narrower fix, I'll check every caller and test the unaliased form with a qualified reference, which the task also calls out.
[tool_use Bash] {"command": "grep -rn \"get_source_columns\\|get_table(\" sqlglot/ | grep -v \"def \" ; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nfor q in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT c.v, c.m FROM c UNPIVOT(v FOR m IN (jan, feb))',\n 'WITH c AS (
…[241 chars elided]…
u.m FROM c AS x UNPIVOT(v FOR m IN (jan, feb)) AS u',\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.id FROM c UNPIVOT(v FOR m IN (jan, feb)) AS c2']:\n  try: print(qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch).sql('bigquery'))\n  except Exception as ex: print('ERR',type(ex).__name__,ex)\n\"", "description": "Find resolver callers and test more pivoted CTE forms"}
[tool_result] sqlglot/optimizer/qualify_columns.py:218:        for column_name in resolver.get_source_columns(source_name):
sqlglot/optimizer/qualify_columns.py:247:        join_columns = resolver.get_source_columns(join_table)
sqlglot/optimizer/qualify_columns.py:268:                    if identifier in resolver.get_source_columns(t)
sqlglot/optimizer/qualify_columns.py:351:            table = resolver.get_table(column.name) if resolve_table and not column.table else None
sqlglot/optimizer/qualify_columns.py
…[1986 chars elided]…
_resolver.get_table(column)
sqlglot/optimizer/pushdown_projections.py:168:                    alias(exp.column(name, table=resolver.get_table(name)), name, copy=False)
ERR OptimizeError Unknown column: v
ERR OptimizeError Unknown column: v
ERR OptimizeError Unknown column: v
ERR OptimizeError Unknown column: v
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c2`
[assistant] Qualified references fail in both forms: `c.v` breaks on the unaliased form too, while `c.id` (a pre-pivot column) resolves. The star path is the one place where the resolver's pre-pivot result is correct, so I'll keep that contract. I'll check the remaining star variants, including `u.*` and `c.*`, before deciding where the fix goes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nfor q in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT u.* FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.* FROM c UNPIVOT(v FOR m IN (jan, feb)
…[273 chars elided]…
jan) FOR feb IN (1, 2)) AS u(x, y, z)',\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM (SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb)))',\n]:\n  try: print(qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch).sql('bigquery'))\n  except Exception as ex: print('ERR',type(ex).__name__,ex)\n\"", "description": "Test additional star expansion variants over pivoted CTEs"}
[tool_result] Named columns are not supported in table alias.
Named columns are not supported in table alias.
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m
…[467 chars elided]…
S (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`x` AS `x`, `u`.`y` AS `y`, `u`.`z` AS `z` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `c`.`feb` IN (1, 2)) AS `u`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `_0`.`id` AS `id`, `_0`.`m` AS `m`, `_0`.`v` AS `v` FROM (SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`) AS `_0`
[assistant] Two of the six variants printed only a warning and no SQL, so I need to rerun them alone to see what actually happened.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nfor q in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT u.* FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.* FROM c UNPIVOT(v FOR m IN (jan, feb))']:\n  try: print('OUT', qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch).sql('bigquery'))\n  except Exception as ex: print('ERR',type(ex).__name__,ex)\n  print('---')\n\" 2>&1", "description": "Rerun the two star queries in isolation"}
[tool_result] OUT WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
---
OUT WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
---
[assistant] Both star variants expand correctly under `qualify`. The task names the optimizer as the entry point, so I'll run the full `optimize()` pipeline on all the queries, since later rules such as merge and eliminate-subqueries could cause the star problem the report describes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n'WITH c AS 
…[30 chars elided]…
ELECT c.v FROM c UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','duckdb']:\n  for q in qs:\n    for sch_ in [None, sch]:\n      try: print(d, sch_ is not None, 'OUT', optimize(sqlglot.parse_one(q,read=d),dialect=d,schema=sch_).sql(d))\n      except Exception as ex: print(d, sch_ is not None, 'ERR',type(ex).__name__,ex)\n\" 2>&1", "description": "Run full optimize() on pivoted CTE queries"}
[tool_result] bigquery False OUT SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery True OUT SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery False ERR OptimizeError Unknown column: v
bigquery True ERR OptimizeError Unknown column: v
bigquery False ERR OptimizeError Unknown column: v
bigquery True ERR OptimizeError Unknown column: v
duckdb False OUT SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
duckdb True OUT SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
duckdb False ERR OptimizeError Unknown column: v
duckdb True ERR OptimizeError Unknown column: v
duckdb False ERR OptimizeError Unknown column: v
duckdb True ERR OptimizeError Unknown column: v
[assistant] `optimize()` matches `qualify`: the unaliased star expands correctly, and both `u.v` and `c.v` fail. My plan is to keep the resolver's pre-pivot contract, since star expansion depends on it, and make the column-existence check in `_disambiguate_columns` pivot-aware. I'll factor the pivot output/consumed-column logic out of `_expand_stars` so both paths share it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    pivot_output_columns = None\n    pivot_exclude_columns: set[str] = set()\n\n    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n    if isinstance(pivot, exp.Pivot) and not pivot.a
…[648 chars elided]…
       pivot_output_columns = [c.alias_or_name for c in pivot.expressions]\n", "new_string": "    pivot_output_columns = None\n    pivot_exclude_columns: set[str] = set()\n\n    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n    if isinstance(pivot, exp.Pivot) and not pivot.alias_column_names:\n        pivot_output_columns, pivot_exclude_columns = _pivot_output_columns(pivot)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Now I'll add the shared helpers next to `_unpivot_columns`, and use them in the column-existence check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pop_table_column_aliases(", "new_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pivot_output_columns(pivo
…[950 chars elided]…
ces its consumed columns with its output\n    \"\"\"\n    columns = resolver.get_source_columns(name)\n    pivot = next((p for p in scope.pivots if p.alias == name), None)\n    if not pivot:\n        return columns\n\n    output, consumed = _pivot_output_columns(pivot)\n    return [c for c in columns if c not in consumed] + (pivot.alias_column_names or output)\n\n\ndef _pop_table_column_aliases("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)", "new_string": "        if column_table and column_table in scope.sources:\n            source_columns = _pivoted_source_columns(scope, resolver, column_table)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Next I'll rerun the full set of repro queries through both `qualify` and `optimize`, checking the expected output for each.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c 
…[537 chars elided]…
OT(v FOR m IN (jan, feb)) AS u',\n]\nfor q in qs:\n  for f in [lambda e: qualify(e,dialect='bigquery',schema=sch), lambda e: optimize(e,dialect='bigquery',schema=sch)]:\n    try: print('OUT', f(sqlglot.parse_one(q,read='bigquery')).sql('bigquery'))\n    except Exception as ex: print('ERR',type(ex).__name__,ex)\n  print()\n\" 2>&1", "description": "Rerun repro queries through qualify and optimize"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` drops the working directory from `sys.path`, so `sqlglot` isn't importable. Earlier runs without `-I` imported from the cwd, which is the worktree. I'll set `PYTHONPATH` explicitly so I know which copy is loaded.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot; print(sqlglot.__file__)\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT i
…[576 chars elided]…
T(v FOR m IN (jan, feb)) AS u',\n]\nfor q in qs:\n  for f in [lambda e: qualify(e,dialect='bigquery',schema=sch), lambda e: optimize(e,dialect='bigquery',schema=sch)]:\n    try: print('OUT', f(sqlglot.parse_one(q,read='bigquery')).sql('bigquery'))\n    except Exception as ex: print('ERR',type(ex).__name__,ex)\n  print()\n\" 2>&1", "description": "Rerun repro queries with worktree sqlglot on path"}
[tool_result] Named columns are not supported in table alias.
Named columns are not supported in table alias.
~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/__init__.py
OUT WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
OUT SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v
…[1274 chars elided]…
(`c`.`jan`) FOR `c`.`feb` IN (1, 2)) AS `_0`

OUT WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`x` AS `x` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `c`.`feb` IN (1, 2)) AS `u`
OUT WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`x` AS `x` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) FOR `c`.`feb` IN (1, 2)) AS `u`

ERR OptimizeError Unknown column: jan
ERR OptimizeError Unknown column: jan
[assistant] Most cases now resolve correctly, and `u.jan` (a consumed column) is rejected as it should be. Query 4 (`FROM c AS x` with an aliased pivot) changed from an `Unknown column` error to an `Ambiguous column` error. I want a clean baseline to tell whether that's a regression, so I'll extract `HEAD` into a fresh directory and compare.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-baseline-ro && mkdir -p /tmp/sqlglot-baseline-ro && git archive HEAD | tar -x -C /tmp/sqlglot-baseline-ro && cat > /tmp/sqlglot-baseline-ro/../cmp_check.py <<'EOF'\nimport sys\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nprint(sqlglot.__file__)\nsch = {'t': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nqs = [\n 'WITH c AS (SELECT id, jan, feb FROM t) SELE
…[488 chars elided]…
tion as ex: print('ERR', type(ex).__name__, ex)\nEOF\necho BASELINE; PYTHONPATH=/tmp/sqlglot-baseline-ro <work>/env-sqlglot/bin/python /tmp/cmp_check.py; echo WORKTREE; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/cmp_check.py", "description": "Compare aliased-source pivot behavior against HEAD baseline"}
[tool_result] BASELINE
/tmp/sqlglot-baseline-ro/sqlglot/__init__.py
ERR OptimizeError Unknown column: v
ERR OptimizeError Unknown column: v
OUT SELECT `x`.`id` AS `id` FROM `c` AS `x` UNPIVOT(`v` FOR `m` IN (`x`.`jan`, `x`.`feb`)) AS `x`
OUT SELECT `u`.`v` AS `v` FROM `t` AS `x` UNPIVOT(`v` FOR `m` IN (`x`.`jan`, `x`.`feb`)) AS `u`
WORKTREE
~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/__init__.py
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 96)
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 85)
OUT SELECT `x`.`id` AS `id` FROM `c` AS `x` UNPIVOT(`v` FOR `m` IN (`x`.`jan`, `x`.`feb`)) AS `x`
OUT SELECT `u`.`v` AS `v` FROM `t` AS `x` UNPIVOT(`v` FOR `m` IN (`x`.`jan`, `x`.`feb`)) AS `u`
[assistant] This is a real regression in the error path, not a fixed query. The baseline fails earlier with `Unknown column: v`, which my change now gets past, and then `jan` in the IN list reports as ambiguous. I'll trace the resolver for that query to find which two sources are matching.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\nfrom sqlglot.optimizer.qualify import qualify\norig = qc._disambiguate_columns\nimport sqlglot.optimizer.resolver as r\nog = r.Resolver.get_table\ndef gt(self, column):\n    res = og(self, column)\n    print('get_table', colum
…[106 chars elided]…
rn res\nr.Resolver.get_table = gt\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c AS x UNPIVOT(v FOR m IN (jan, feb)) AS u'\ntry: qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch)\nexcept Exception as e: print('ERR', e)\n\" 2>&1 | head -30", "description": "Trace get_table calls for aliased CTE pivot ambiguity"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 5, in <module>
AttributeError: module 'sqlglot.optimizer.qualify_columns' has no attribute '_disambiguate_columns'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nimport sqlglot.optimizer.resolver as r\nog = r.Resolver.get_table\ndef gt(self, column):\n    res = og(self, column)\n    print('get_table', column, '->', res, 'sources', list(self.scope.sources), 'cte', list(self.scope.cte_sou
…[16 chars elided]…
rn res\nr.Resolver.get_table = gt\nsch={'t':{'id':'int','jan':'int','feb':'int'}}\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c AS x UNPIVOT(v FOR m IN (jan, feb)) AS u'\ntry: qualify(sqlglot.parse_one(q,read='bigquery'),dialect='bigquery',schema=sch)\nexcept Exception as e: print('ERR', e)\n\" 2>&1 | head -30", "description": "Trace get_table calls for aliased CTE pivot ambiguity"}
[tool_result] get_table id -> t sources ['t'] cte []
get_table jan -> t sources ['t'] cte []
get_table feb -> t sources ['t'] cte []
get_table jan -> None sources ['c', 'u'] cte ['c']
get_table feb -> None sources ['c', 'u'] cte ['c']
ERR Ambiguous column 'jan' (Line: 1, Col: 85)
[assistant] The scope holds two sources, `c` (the CTE reference) and `u` (the pivoted table), so the unqualified `jan` matches both. I'll check whether the baseline already reports that ambiguity for a query that doesn't hit the `u.v` check, to see if this is pre-existing.
[tool_use Bash] {"command": "cd /tmp && cat > /tmp/amb_check.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nprint(sqlglot.__file__)\nsch = {'t': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nqs = [\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.m FROM c AS x UNPIVOT(v FOR m IN (jan, feb)) AS u',\n 'WITH c AS (SELECT id, jan, feb FROM t) SELECT 1 AS one FROM c AS x UNPIVOT(v FOR m IN (jan, f
…[373 chars elided]…
Users/user/.cache/lithify-dev/r2-noise-scratch/env-sqlglot/bin/python /tmp/amb_check.py; echo WORKTREE; PYTHONPATH=~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1 <work>/env-sqlglot/bin/python /tmp/amb_check.py", "description": "Check whether aliased-CTE pivot ambiguity predates the change"}
[tool_result] BASELINE
/tmp/sqlglot-baseline-ro/sqlglot/__init__.py
ERR OptimizeError Unknown column: m
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 90)
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 83)
WORKTREE
~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/__init__.py
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 85)
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 90)
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 83)
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1
[assistant] The `FROM c AS x` ambiguity also happens on the untouched baseline (`SELECT 1 ... FROM c AS x UNPIVOT` already fails), so it's a separate, pre-existing scope bug: the CTE is still registered as source `c` when it's referenced under a different alias. My change only moved the error for that shape. I'll leave it and report it. Next I'll find the existing pivot fixtures so I can add regression tests in the right place.
[tool_use Bash] {"command": "grep -rn -i \"unpivot\\|pivot\" tests/fixtures/optimizer/qualify_columns.sql | head -40; grep -rln -i \"pivot\" tests/*.py tests/fixtures/optimizer/*.sql", "description": "Locate existing pivot tests and fixtures"}
[tool_result] tests/fixtures/optimizer/qualify_columns.sql:269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
tests/fixtures/optimizer/qualify_columns.sql:270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 ORDER BY _0.EMPID;
tests/fixtures/optimizer/qualify_columns.sql:593:# title: Expand PIVOT column combinations
tests/fixtures/optimizer/qualify_columns.sql:
…[1285 chars elided]…
le_total AS us_2010_seattle_total, _0.us_2010_seattle_count AS us_2010_seattle_count FROM cities AS cities PIVOT(SUM(population) AS total, COUNT(population) AS count FOR country IN ('nl', 'us') year IN (2000, 2010) name IN ('amsterdam', 'seattle')) AS _0;
tests/test_expressions.py
tests/test_lineage.py
tests/test_optimizer.py
tests/test_parser.py
tests/test_transpile.py
tests/fixtures/optimizer/optimizer.sql
tests/fixtures/optimizer/qualify_columns.sql
tests/fixtures/optimizer/qualify_tables.sql
[tool_use Bash] {"command": "grep -n -i \"pivot\" tests/test_optimizer.py | head -40; grep -n -i \"pivot\" tests/fixtures/optimizer/optimizer.sql | head; sed -n 585,600p tests/fixtures/optimizer/qualify_columns.sql | cut -c1-200; tail -5 tests/fixtures/optimizer/qualify_columns.sql | cut -c1-200", "description": "Look at pivot tests in optimizer test suite"}
[tool_result] 271:                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y'))"
276:            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS _0",
282:                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias"
287:            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",

…[1882 chars elided]…
ountry, name, year, population)) SELECT _0.n

--------------------------------------
-- CTEs
--------------------------------------
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x SEMI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;

# title: ANTI + normal joins reinclude the table on scope
SELECT * FROM x ANTI JOIN y USING (b) JOIN y USING (b);
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;
[assistant] The existing UNPIVOT coverage lives in `tests/test_optimizer.py` around line 630. I'll read that block so the new tests match its style.
[tool_use Bash] {"command": "sed -n 628,675p tests/test_optimizer.py", "description": "Read existing UNPIVOT and PIVOT optimizer tests"}
[tool_result]                 parse_one("SELECT * FROM t"),
                schema={"t": {"end": "text"}},
                quote_identifiers=False,
            ).sql(),
            "SELECT t.end AS end FROM t AS t",
        )

        self.assertEqual(
            optimizer.qualify.qualify(
                parse_one(
                    "WITH produce AS (SELECT 'Kale' AS product, 51 AS q1, 23 AS q2) "
                    "SELECT * FROM produce UNPIVOT(sales FOR quarter IN (q1, q2))",
                    diale
…[1156 chars elided]…
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
[assistant] I'll add the regression assertions directly after the existing UNPIVOT-over-CTE assertion in `test_optimizer.py`, which keeps them next to the coverage they extend. First I'll confirm which test method contains it.
[tool_use Bash] {"command": "awk 'NR<=650 && /def test_/ {l=NR\": \"$0} END{}; NR==650{print l}' tests/test_optimizer.py", "description": "Find enclosing test method for the UNPIVOT assertion"}
[tool_result] 650:     def test_validate_columns(self):
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/test_optimizer.py | awk -F: '$1<640' | tail -2", "description": "Get the test method name containing the UNPIVOT block"}
[tool_result] 322:0:
341:0:
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_optimizer.py | awk -F: '$1<640' | tail -2", "description": "List test methods before the UNPIVOT block"}
[tool_result] 322:0:
341:0:
[assistant] The output format is off (`rtk` seems to be rewriting `grep`), so I'll read the surrounding lines directly.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "offset": 560, "limit": 70}
[tool_result] 560	        self.assertEqual(
561	            optimizer.qualify.qualify(
562	                parse_one(
563	                    """
564	                    WITH cte AS (SELECT * FROM base_table)
565	                    SELECT
566	                      (SELECT SUM(item.price)
567	                       FROM UNNEST(items) AS item
568	                       WHERE category = 'electronics') as electronics_total
569	                    FROM cte
570	                    """,
571	                    read
…[2067 chars elided]…
0	                    "SELECT 1 FROM dbo.a JOIN dbo.b ON dbo.b.id = dbo.a.id JOIN dbo.b AS x ON x.id = dbo.a.id"
621	                ),
622	            ).sql(),
623	            'SELECT 1 AS "1" FROM "dbo"."a" AS "a" JOIN "dbo"."b" AS "b" ON "b"."id" = "a"."id" JOIN "dbo"."b" AS "x" ON "x"."id" = "a"."id"',
624	        )
625	
626	        self.assertEqual(
627	            optimizer.qualify.qualify(
628	                parse_one("SELECT * FROM t"),
629	                schema={"t": {"end": "text"}},
[assistant] The UNPIVOT block sits in `test_qualify_columns`, right before `test_validate_columns`. I'll add the assertions after the existing `produce` case, then fill in the expected strings from the verified outputs above.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "old_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`\",\n        )\n\n    def test_validate_columns(self):", "new_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (
…[2101 chars elided]…
gex(OptimizeError, \"Unknown column: jan\"):\n            optimizer.qualify.qualify(\n                parse_one(\n                    pivot_cte + \"SELECT u.jan FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n                    read=\"bigquery\",\n                ),\n                schema=pivot_schema,\n                dialect=\"bigquery\",\n            )\n\n    def test_validate_columns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the project's check command, the full pytest suite, from the worktree.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite with pytest", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite with pytest", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
................................................................................................ [ 20%]
..................... [ 22%]
............................................................................................................... [ 32%]
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................
…[332 chars elided]…
[ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
....................................................................................... [ 88%]
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 48.11s
[assistant] The full suite passes: 1092 tests and 17864 subtests. Next I'll confirm the new assertions actually fail on the baseline, and run the style checks on the changed files.
[tool_use Bash] {"command": "cp tests/test_optimizer.py /tmp/sqlglot-baseline-ro/tests/test_optimizer.py && cd /tmp/sqlglot-baseline-ro && PYTHONPATH=/tmp/sqlglot-baseline-ro <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k test_qualify_columns 2>&1 | tail -6; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-180941-optimizer-un-pivot-over-cte-sour/base-1 && grep -n -A6 \"^style\" Makefile; ls <work>/env-sqlglot/bin | grep -i \"ruff\\|mypy\"", "description": "Verify new test fails on baseline and find style tools"}
[tool_result] uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu [ 33%]
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu [ 33%]
uuuuuuuuuuuuu
=========================== short test summary info ============================
FAILED tests/test_optimizer.py::TestOptimizer::test_qualify_columns - sqlglot...
1 failed, 2 passed, 74 deselected, 399 subtests passed in 2.18s
84:style:
85-	pre-commit run --all-files
86-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
87-
88-check: style test testc
89-
90-docs:
dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py; $R/ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py; $R/mypy sqlglot/optimizer/qualify_columns.py 2>&1 | tail -3; rm -rf /tmp/sqlglot-baseline-ro /tmp/cmp_check.py /tmp/amb_check.py", "description": "Run ruff format, ruff lint, and mypy on changed files"}
[tool_result] 2 files already formatted
All checks passed!
Success: no issues found in 1 source file
[assistant] Formatting, lint, and mypy are clean. I'll review the final diff once before wrapping up.
[tool_use Bash] {"command": "git diff -- sqlglot/ && git status --short", "description": "Show the source diff and changed file list"}
[tool_result] sqlglot/optimizer/qualify_columns.py | 49 ++++++++++++++++++++++++------------
 1 file changed, 33 insertions(+), 16 deletions(-)

--- Changes ---

sqlglot/optimizer/qualify_columns.py
  @@ -197,6 +197,37 @@ def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
  +def _pivot_output_columns(pivot: exp.Pivot) -> tuple[list[str], set[str]]:
  +    """Returns the columns a pivot outputs, and the source columns it consumes"""
  +    if pivot.unpivot:
  +        consumed = {
  +       
…[2170 chars elided]…
        pivot_output_columns = [c.output_name for c in pivot.args.get("columns", [])]
  -            if not pivot_output_columns:
  -                pivot_output_columns = [c.alias_or_name for c in pivot.expressions]
  +        pivot_output_columns, pivot_exclude_columns = _pivot_output_columns(pivot)
   
       if dialect.SUPPORTS_STRUCT_STAR_EXPANSION and any(
           isinstance(col, exp.Dot) for col in scope.stars
  +33 -16
 M sqlglot/optimizer/qualify_columns.py
 M tests/test_optimizer.py
[assistant] Both failing shapes now qualify correctly, for aliased and unaliased pivots. The full suite passes (1092 tests, 17864 subtests), and the new assertions fail on the untouched `HEAD`. The changes are uncommitted in the worktree.

**The fix** (`sqlglot/optimizer/qualify_columns.py`): the column-existence check in `_disambiguate_columns` used the pre-pivot CTE columns for any source, so `u.v` was rejected. It now uses the pivot's visible columns (the source columns minus those the pivot consumes, plus its output columns) whenever the pivot alias matches the source name. The pivot output logic move
…[1152 chars elided]…
.)`), because the CTE stays registered as a source under its own name. My change only altered the error for the `u.v` variant of that query, from `Unknown column` to `Ambiguous column`. Fixing it means changing how `scope.py` registers referenced CTEs, which is a broader change than this task.

**Tests:** I added assertions to `test_qualify_columns` in `tests/test_optimizer.py`, next to the existing UNPIVOT-over-CTE case. They cover the aliased and qualified forms, the consumed-column rejection, and the expected SQL output. `ruff format`, `ruff check` and `mypy` are clean on the changed files.
