# trajectory base-1

final message:
Multi-value UNPIVOT lineage is now correct: each value column traces only to the IN-list columns at its position. The full suite passes (1118 passed) and ruff is clean.

**What was wrong:** with `UNPIVOT((q1, q2) FOR metric IN ((jan_1, jan_2) AS 'jan', (feb_1, feb_2) AS 'feb'))`, `q1` traced to all four source columns, including `jan_2` and `feb_2`. The old code mapped every value column to the full IN-list.

**The fix** is in `_pivot_column_mapping` in `sqlglot/lineage.py`. Each value column now pairs with the IN-list column at the same position in each entry, the same pairing `annotate_types` uses. The name column still maps to every IN-list column, and single-value UNPIVOT output is unchanged.

**Test:** `test_unpivot_multiple_value_columns` in `tests/test_lineage.py` covers `q1`, `q2`, and the name column `metric`. I added it alongside the existing UNPIVOT tests and didn't modify any existing ones.

**What I checked and found already correct:** aliased IN-list entries, star selects, table and derived-table aliases, expressions over the value column, aggregates, nested subqueries with star, CTEs with renamed columns, joins with pass-through columns, and unaliased or aliased UNPIVOT in joins.

**Not fixed (out of lineage scope):**
- Chained `UNPIVOT ... PIVOT` on one source fails with `Cannot find column 'J'`. The error comes from `qualify_columns`, which only handles one PIVOT or UNPIVOT per scope. Lineage also skips its mapping when a scope has more than one pivot.
- Two UNPIVOTs over the same unaliased table in one join fail with `Alias already used`. This is also in the qualifier.

I haven't committed anything. The probe script lives at `/tmp/unpivot_probe/probe.py`, outside the repo.

## events
[assistant] I'll start by finding the existing UNPIVOT lineage support and its tests.
[tool_use Bash] {"command": "git log --oneline -5 && grep -rn -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50; grep -rln -i unpivot tests/ | head; git log --oneline -i --grep=unpivot | head", "description": "Locate UNPIVOT references in lineage code and tests"}
[tool_result] 0091d5058 lithify: probe base
3b56d5da3 eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
19558813d Fix(sqlglotc): pin sqlglot to the exact matching version (#7730)
df507aac2 fix(databricks)!: GET_JSON_OBJECT roundtrip (#7728)
sqlglot/lineage.py:473:    if pivot.unpivot:
sqlglot/lineage.py:474:        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
sqlglot/lineage.py:476:        unpivot_columns = [
sqlglot/lineage.py:484:                mapping[identi
…[1109 chars elided]…
f(parser): short-circuit _parse_pivots when next token isn't PIV...
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
a83b51194 feat(parser): PIVOT/UNPIVOT pipe syntax (#5222)
c0c7b673b fix(optimizer)!: avoid creating new alias for qualifying unpivot (#...
d82e1733d Fix: apply unpivot alias string conversion only for UNPIVOT (#4886)
0db654767 feat(duckdb): Support simplified UNPIVOT statement (#4545)
f2ba91872 feat(lineage): Extend lineage function to work with pivot operation...
[assistant] The initial UNPIVOT lineage commit is `74bef2f46`. I'll read its diff and the current pivot handling in `lineage.py`.
[tool_use Bash] {"command": "git show 74bef2f46 --stat && git show 74bef2f46 -- sqlglot/ | head -150; sed -n 420,520p sqlglot/lineage.py", "description": "Show initial UNPIVOT lineage commit and pivot handling code"}
[tool_result] commit 74bef2f4617f2fa25881dded12ae3851a7ddfa1f
Author: Jo <46752250+georgesittas@users.noreply.github.com>
Date:   Wed Jun 10 17:00:13 2026 +0300

    Feat(lineage): add support for `UNPIVOT` (#7729)

 sqlglot/lineage.py    | 69 ++++++++++++++++++++++++++++++++++++---------------
 tests/test_lineage.py | 35 ++++++++++++++++++++++++++
 2 files changed, 84 insertions(+), 20 deletions(-)
74bef2f46 Feat(lineage): add support for `UNPIVOT` (#7729) (5 months ago) <Jo>
sqlglot/lineage.py | 69 ++++++++
…[8506 chars elided]…
ount = len(pivot.expressions)

    mapping = {}
    for i, agg in enumerate(pivot.expressions):
        agg_cols = list(agg.find_all(exp.Column))
        for col_index in range(i, len(pivot_columns), pivot_aggs_count):
            mapping[pivot_columns[col_index].name] = agg_cols
    return mapping


class GraphHTML:
    """Node to HTML generator using vis.js.

    https://visjs.github.io/vis-network/docs/network/
    """

    def __init__(
        self,
        nodes: dict,
        edges: list,
[assistant] Next, the `to_node` body around the pivot loop, plus the test the initial commit added.
[tool_use Bash] {"command": "sed -n 330,420p sqlglot/lineage.py; echo ----; git show 74bef2f46 -- tests/test_lineage.py", "description": "Read to_node pivot section and UNPIVOT lineage tests"}
[tool_result]             logger.warning(f"Unknown subquery scope: {subquery.sql(dialect=dialect)}")
            continue

        for name in subquery.named_selects:
            to_node(
                name,
                scope=subquery_scope,
                dialect=dialect,
                upstream=node,
                trim_selects=trim_selects,
                _cache=_cache,
                _scope_meta=_scope_meta,
                on_node=on_node,
            )

    # if the select is a star add all s
…[4865 chars elided]…
stream[0].downstream[0].name, "SALES.JAN")
  +        self.assertEqual(node.downstream[1].downstream[0].name, "SALES.FEB")
  +
  +        node = lineage("id", sql, schema=schema, dialect="snowflake")
  +        self.assertEqual(node.downstream[0].name, "SRC.ID")
  +        self.assertEqual(node.downstream[0].downstream[0].name, "SALES.ID")
  +
       def test_table_udtf_snowflake(self) -> None:
           lateral_flatten = """
           SELECT f.value:external_id::string AS external_id
  +35 -0
[assistant] The current code handles one UNPIVOT per scope, with name and value columns both mapped to the IN-list. Before deciding what to change, I'll probe a range of query shapes to see which ones produce wrong lineage. First, confirming the test interpreter exists:
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python && cd ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1 && <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\"", "description": "Verify test interpreter and sqlglot import path"}
[tool_result] <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/sqlglot/__init__.py
[assistant] I'll write a probe script outside the repo that prints the leaf lineage for each query shape.
[tool_use Write] {"file_path": "/tmp/unpivot_probe/probe.py", "content": "import sys\n\nfrom sqlglot.lineage import lineage\n\nSCHEMA = {\n    \"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"jan_1\": \"int\", \"jan_2\": \"int\", \"feb_1\": \"int\", \"feb_2\": \"int\"},\n    \"other\": {\"id\": \"int\", \"x\": \"int\"},\n}\n\nCASES = [\n    (\"basic\", \"SELECT id, metric_name, score FROM sales U
…[2274 chars elided]…
r None\nfor name, sql, cols in CASES:\n    if only and name not in only:\n        continue\n    for col in cols:\n        try:\n            node = lineage(col, sql, schema=SCHEMA, dialect=\"snowflake\")\n            print(f\"{name:24} {col:10} -> {sorted(set(leaves(node)))}\")\n        except Exception as e:  # noqa: BLE001\n            print(f\"{name:24} {col:10} !! {type(e).__name__}: {e}\")\n"}
[tool_result] The file /tmp/unpivot_probe/probe.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_probe/probe.py 2>&1", "description": "Run UNPIVOT lineage probe across query shapes"}
[tool_result] basic                    score      -> ['SALES.FEB', 'SALES.JAN']
basic                    metric_name -> ['SALES.FEB', 'SALES.JAN']
basic                    id         -> ['SALES.ID']
aliased_in               score      -> ['SALES.FEB', 'SALES.JAN']
aliased_in               metric_name -> ['SALES.FEB', 'SALES.JAN']
multi_value              q1         -> ['SALES.FEB_1', 'SALES.FEB_2', 'SALES.JAN_1', 'SALES.JAN_2']
multi_value              q2         -> ['SALES.FEB_1', 'SALES.FEB_2', 'SALES.JAN_1
…[626 chars elided]…
me -> ['SALES.FEB', 'SALES.JAN']
nested_subquery_star     score      -> ['SALES.FEB', 'SALES.JAN']
two_unpivots_join        score2     !! OptimizeError: Alias already used: SALES
cte_passthrough_rename   key        -> ['SALES.ID']
cte_passthrough_rename   score      -> ['SALES.FEB', 'SALES.JAN']
cte_renamed_in           score      -> ['SALES.FEB', 'SALES.JAN']
cte_renamed_in           id         -> ['SALES.ID']
unpivot_then_pivot       j          !! SqlglotError: Cannot find column 'J' in query.
[assistant] Most shapes already trace correctly. Three things stand out:

- **Multi-value UNPIVOT** is over-broad: `q1` pulls in `*_2` columns too. It should map value column *i* to the *i*-th column of each IN-list tuple.
- **Two pivots in one scope** (`UNPIVOT ... PIVOT`) falls back to no mapping, so `j` fails.
- **Two UNPIVOTs in a join** raised `Alias already used`, which may be my SQL rather than the lineage code.

I'll check how `scope.pivots` is collected and retry the join case with distinct sources.
[tool_use Bash] {"command": "grep -n \"pivots\" sqlglot/optimizer/scope.py | head -20; grep -n \"def _get_unpivot_column_types\" -A30 sqlglot/optimizer/annotate_types.py | head -45", "description": "Inspect scope pivot collection and unpivot type helper"}
[tool_result] 12 matches in 6 files:

508:0:
509:0:
846:0:
98:0:list[exp.Pivot] | None
984:0:
sqlglot/optimizer/scope.py:148:self._pivots = None
sqlglot/optimizer/scope.py:440:expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:510:self._pivots = [
sqlglot/optimizer/scope.py:511:pivot for _, node in self.references for pivot in node.args.get("pivots") or []
sqlglot/optimizer/scope.py:514:return self._pivots
sqlglot/optimizer/scope.py:845:pivots = expression.args.get
…[1051 chars elided]…
-            for val_col, in_col in zip(val_cols, in_cols):
678-                new_types[val_col.output_name] = in_col.type
679-
680-        return {
681-            name: type_
682-            for name in pivot.output_columns(src_types)
683-            if (type_ := new_types.get(name) or src_types.get(name))
684-        }
685-
686-    def _get_pivot_column_types(
687-        self, pivot: exp.Pivot, src_types: dict[str, exp.DataType | exp.DType]
688-    ) -> dict[str, exp.DataType | exp.DType]:
[assistant] `annotate_types` already pairs value columns with IN-list entries by index, which is the model I need for the multi-value fix. Before editing, I'll add more pass-through and nesting shapes to the probe, and rewrite the join case with distinct derived sources.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && <work>/env-sqlglot/bin/python - <<'EOF'\nimport re\nsrc = open(\"probe.py\").read()\nnew_cases = '''    (\"join_passthrough\", \"SELECT u.id, o.x, u.score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u JOIN other AS o ON u.id = o.id\", [\"x\", \"id\", \"score\"]),\n    (\"two_unpivots_subq\", \"SELECT 
…[909 chars elided]…
ncd ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1 && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_probe/probe.py join_passthrough two_unpivots_subq cte_star_outer passthrough_expr passthrough_cte_join_in 2>&1", "description": "Probe join, nested, and pass-through unpivot shapes"}
[tool_result] join_passthrough         x          -> ['O.X']
join_passthrough         id         -> ['SALES.ID']
join_passthrough         score      -> ['SALES.FEB', 'SALES.JAN']
two_unpivots_subq        score2     -> ['SALES.FEB_1', 'SALES.FEB_2']
two_unpivots_subq        score      -> ['SALES.FEB', 'SALES.JAN']
cte_star_outer           score      -> ['SALES.FEB', 'SALES.JAN']
cte_star_outer           id         -> ['SALES.ID']
passthrough_expr         nxt        -> ['SALES.ID']
passthrough_cte_join_in  x          -> ['O.X']
[assistant] The probe file changed only because my own script rewrote it. Results on the new shapes are correct, and the join case passes. One suspect remains: the check `pivot.alias_or_name == c.table` may fail when the UNPIVOT is unaliased but the table is aliased or joined. I'll probe those, then check how `qualify_tables` assigns the pivot alias.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && <work>/env-sqlglot/bin/python - <<'EOF'\nsrc = open(\"probe.py\").read()\nnew = '''    (\"alias_join_score\", \"SELECT s.score, s.id, o.x FROM sales AS s UNPIVOT (score FOR metric_name IN (jan, feb)) JOIN other AS o ON s.id = o.id\", [\"score\", \"id\"]),\n    (\"unaliased_join_score\", \"SELECT sales.score, other.x 
…[425 chars elided]…
van/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1 && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_probe/probe.py alias_join_score unaliased_join_score unaliased_join_metric 2>&1; sed -n 160,180p sqlglot/optimizer/qualify_tables.py", "description": "Probe aliased and unaliased UNPIVOT in joins"}
[tool_result] alias_join_score         score      -> ['S.FEB', 'S.JAN']
alias_join_score         id         -> ['S.ID']
unaliased_join_score     score      -> ['SALES.FEB', 'SALES.JAN']
unaliased_join_metric    metric_name -> ['SALES.FEB', 'SALES.JAN']
                    normalize=True,
                    columns=function_columns,
                )

                source_fqn = ".".join(p.name for p in source.parts)
                had_explicit_alias = table_alias and table_alias.name
                if not
…[162 chars elided]…
:
                    target_alias = source.alias if pivot.unpivot else None
                    _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)

                    # This case corresponds to a pivoted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
[assistant] All of these are correct. `qualify_tables` always sets the UNPIVOT alias to the source alias, so the alias check holds. The only real defect I've confirmed is the multi-value case, where each value column is mapped to every IN-list column. The `UNPIVOT ... PIVOT` chain and the `Alias already used` join error both fail in the qualifier, outside lineage. I'll fix the multi-value mapping now, starting with the imports.
[tool_use Bash] {"command": "sed -n 1,25p sqlglot/lineage.py | grep -n \"import\"", "description": "Check lineage.py imports"}
[tool_result] 1:from __future__ import annotations
3:import json
4:import logging
5:import typing as t
6:from dataclasses import dataclass, field
8:from sqlglot import Schema, exp, maybe_parse
9:from sqlglot.errors import SqlglotError
10:from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
11:from sqlglot.optimizer.scope import ScopeType
14:    from sqlglot.dialects.dialect import DialectType
15:    from collections.abc import Iterator, Mapping, Sequence
16:    from sqlglot._typing import GraphHTMLArgs
17:    from typing_extensions import Unpack
[assistant] No `seq_get` import, so I'll index directly; UNPIVOT always has a value expression. Now the edit:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1286 chars elided]…
for value_column, in_column in zip(value_columns, in_columns):\n                    mapping.setdefault(value_column.output_name, []).extend(\n                        in_column.find_all(exp.Column)\n                    )\n\n            mapping[field.this.name] = [\n                col for in_expr in field.expressions for col in in_expr.find_all(exp.Column)\n            ]\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] I just made the name-column mapping per-field, which changes its meaning. It should stay "all IN-list columns" as before, so I'll compute that list once and keep the per-position value mapping separate.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "        value_expr = pivot.expressions[0]\n        value_columns = value_expr.expressions if isinstance(value_expr, exp.Tuple) else [value_expr]\n\n        for field in pivot.fields:\n            for in_expr in field.ex
…[1096 chars elided]…
isinstance(e, exp.PivotAlias) else e\n                in_columns = in_expr.expressions if isinstance(in_expr, exp.Tuple) else [in_expr]\n                for value_column, in_column in zip(value_columns, in_columns):\n                    mapping.setdefault(value_column.output_name, []).extend(\n                        in_column.find_all(exp.Column)\n                    )\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll re-run the probe against the multi-value and other UNPIVOT cases, then the existing lineage and UNPIVOT test files.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_probe/probe.py 2>&1; echo ---; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py tests/dialects/test_snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Re-run UNPIVOT probe and lineage/dialect tests"}
[tool_result] basic                    score      -> ['SALES.FEB', 'SALES.JAN']
basic                    metric_name -> ['SALES.FEB', 'SALES.JAN']
basic                    id         -> ['SALES.ID']
aliased_in               score      -> ['SALES.FEB', 'SALES.JAN']
aliased_in               metric_name -> ['SALES.FEB', 'SALES.JAN']
multi_value              q1         -> ['SALES.FEB_1', 'SALES.JAN_1']
multi_value              q2         -> ['SALES.FEB_2', 'SALES.JAN_2']
multi_value              metric     -> ['S
…[1529 chars elided]…
 score      -> ['S.FEB', 'S.JAN']
alias_join_score         id         -> ['S.ID']
unaliased_join_score     score      -> ['SALES.FEB', 'SALES.JAN']
unaliased_join_metric    metric_name -> ['SALES.FEB', 'SALES.JAN']
---
............................................................................ [ 42%]
..................................... [ 63%]
.................................................... [ 92%]
..............                              [100%]
179 passed, 2168 subtests passed in 0.73s
[assistant] The multi-value case now maps each value column to its own position. Only the chained `UNPIVOT ... PIVOT` still fails, and that comes from `qualify_columns`, which the docstring says only handles a single PIVOT or UNPIVOT. I'll add a regression test next to the existing UNPIVOT tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\
…[783 chars elided]…
"q2\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.JAN_2\", \"SALES.FEB_2\"])\n\n        node = lineage(\"metric\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(\n            [d.name for d in node.downstream],\n            [\"SALES.JAN_1\", \"SALES.JAN_2\", \"SALES.FEB_1\", \"SALES.FEB_2\"],\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162923-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py -k unpivot 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff --version 2>/dev/null && <work>/env-sqlglot/bin/python -m ruff check sqlglot/lineage.py tests/test_lineage.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/lineage.py tests/test_lineage.py", "description": "Run UNPIVOT tests and ruff lint/format checks"}
[tool_result ERROR] Exit code 1
...                                                                      [100%]
3 passed, 38 deselected in 0.04s
ruff 0.15.6
All checks passed!
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/lineage.py 2>&1 | head -30", "description": "Show ruff format diff for lineage.py"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -476,9 +476,14 @@
         # position, e.g. UNPIVOT((v1, v2) FOR name IN ((a1, a2) AS 'a', (b1, b2) AS 'b')) maps
         # v1 to a1 and b1, and v2 to a2 and b2
         value_expr = pivot.expressions[0]
-        value_columns = value_expr.expressions if isinstance(value_expr, exp.Tuple) else [value_expr]
+        value_columns = (
+            value_expr.expressions if isinstance(value_expr, exp.Tuple) else [value_expr]
+        )
         unpivot_columns = [
-            col for field in pivot.fields for e in field.expressions for col in e.find_all(exp.Column)
+            col
+            for field in pivot.fields
+            for e in field.expressions
+            for col in e.find_all(exp.Column)
         ]
 
         for field in pivot.fields:

1 file would be reformatted
[assistant] The only formatting diff is in my new lines, so I'll apply the formatter to the file and then run the full suite as the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/lineage.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/lineage.py tests/test_lineage.py && git diff --stat && timeout 600 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Format, lint, and run full test suite", "timeout": 600000}
[tool_result] 1 file reformatted
All checks passed!
sqlglot/lineage.py    | 24 +++++++++++++++++-------
 tests/test_lineage.py | 19 +++++++++++++++++++
 2 files changed, 36 insertions(+), 7 deletions(-)
(eval):1: command not found: timeout
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] `timeout` isn't available in this shell, so the suite didn't run. Re-running without it:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite", "timeout": 600000}
[tool_result] ........................................................................................ [ 38%]
...................................................................................................................... [ 49%]
............................ [ 51%]
................................................................................................................................................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1118 passed, 18166 subtests passed in 46.27s
[assistant] The full suite passes. I'll review the final diff once before reporting.
[tool_use Bash] {"command": "git diff -- sqlglot/lineage.py", "description": "Show final lineage.py diff"}
[tool_result] sqlglot/lineage.py | 24 +++++++++++++++++-------
 1 file changed, 17 insertions(+), 7 deletions(-)

--- Changes ---

sqlglot/lineage.py
  @@ -471,20 +471,30 @@ def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
  -        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
  -        # are derived from the IN-list source columns
  +        # UNPIVOT(val FOR name IN (a, b)): the name column is derived from all of the IN-list
  +        # source
…[1000 chars elided]…
        for e in field.expressions:
  +                in_expr = e.this if isinstance(e, exp.PivotAlias) else e
  +                in_columns = in_expr.expressions if isinstance(in_expr, exp.Tuple) else [in_expr]
  +                for value_column, in_column in zip(value_columns, in_columns):
  +                    mapping.setdefault(value_column.output_name, []).extend(
  +                        in_column.find_all(exp.Column)
  +                    )
   
           return mapping
   
  +17 -7
[assistant] Multi-value UNPIVOT lineage is now correct: each value column traces only to the IN-list columns at its position. The full suite passes (1118 passed) and ruff is clean.

**What was wrong:** with `UNPIVOT((q1, q2) FOR metric IN ((jan_1, jan_2) AS 'jan', (feb_1, feb_2) AS 'feb'))`, `q1` traced to all four source columns, including `jan_2` and `feb_2`. The old code mapped every value column to the full IN-list.

**The fix** is in `_pivot_column_mapping` in `sqlglot/lineage.py`. Each value column now pairs with the IN-list column at the same position in each entry, the same pairing `annotate_types
…[519 chars elided]…
h renamed columns, joins with pass-through columns, and unaliased or aliased UNPIVOT in joins.

**Not fixed (out of lineage scope):**
- Chained `UNPIVOT ... PIVOT` on one source fails with `Cannot find column 'J'`. The error comes from `qualify_columns`, which only handles one PIVOT or UNPIVOT per scope. Lineage also skips its mapping when a scope has more than one pivot.
- Two UNPIVOTs over the same unaliased table in one join fail with `Alias already used`. This is also in the qualifier.

I haven't committed anything. The probe script lives at `/tmp/unpivot_probe/probe.py`, outside the repo.
