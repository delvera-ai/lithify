# trajectory base-1

final message:
`lineage()` now traces UNPIVOT value columns back to their source columns, and the name column no longer produces a phantom. The full suite passes (1116 tests) and ruff is clean. I haven't committed.

On your example, `score` now reaches `sales.jan` and `sales.feb`, and `metric_name` has no upstream columns, like a literal. `id` also traces through to `sales.id`, which it previously didn't.

Two things were behind the bug:
- **Value and name columns:** `lineage()` skipped UNPIVOT entirely, so `score` was treated as a column of the input relation. A new helper, `_unpivot_upstream_columns` in `sqlglot/lineage.py`, rewrites value columns into their IN-list columns and drops the name column.
- **Resolving the CTE:** for a pivoted CTE reference, the scope registers the pivoted table, not the CTE, so the walk stopped at the pivot. For UNPIVOT queries, `lineage()` now resolves that reference back to the CTE via `scope.cte_sources`. I limited this to UNPIVOT so existing PIVOT lineage is unchanged.

I added `test_unpivot_with_cte` to `tests/test_lineage.py`, covering the value column, the name column, and a pass-through column. Aliased UNPIVOTs (`FROM src AS s UNPIVOT ... AS u`) also resolve correctly, though I didn't add a test for that case.

Multi-value UNPIVOTs map each value column to the same position in every IN-list tuple. I checked that by reading the code, not by running a case.

## events
[tool_use Bash] {"command": "git status --short | head && cat > /tmp/repro_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nfor col in [\"score\", \"metric_name\", \"id\"]:\n    node
…[43 chars elided]…
=\"snowflake\")\n    print(col)\n    for n in node.walk():\n        print(\"  \", n.name, \"|\", n.source.sql(dialect=\"snowflake\")[:60] if n.source else None)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unpivot.py').read())\"", "description": "Check worktree state and reproduce unpivot lineage"}
[tool_result] score
   SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.
   SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S
metric_name
   METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.
   SRC.METRIC_NAME | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S
id
   ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.
   SRC.ID | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S
[assistant] Reproduced: `score` resolves to a phantom `SRC.SCORE` instead of `jan`/`feb`. Next I'll look at how the scope and lineage code handles `Pivot`/`Unpivot`.
[tool_use Bash] {"command": "grep -n -i \"pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py | head -60; grep -n \"class Pivot\" -A 25 sqlglot/expressions.py", "description": "Find pivot handling in lineage and optimizer"}
[tool_result ERROR] Exit code 2
sqlglot/optimizer/scope.py:98:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:148:        self._pivots = None
sqlglot/optimizer/scope.py:440:                            expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:508:    def pivots(self) -> list[exp.Pivot]:
sqlglot/optimizer/scope.py:509:        if self._pivots is None:
sqlglot/optimizer/scope.py:510:            self._pivots = [
sqlglot/optimizer/scope.py:511:        
…[4981 chars elided]…
ants) * len(agg_types)
sqlglot/optimizer/annotate_types.py:704:            raise OptimizeError(f"Negative pivot column offset: {agg_cols_offset}")
sqlglot/optimizer/annotate_types.py:715:            (a for _ in pivot_constants for a in agg_types),
sqlglot/lineage.py:374:    pivots = scope.pivots
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
sqlglot/lineage.py:376:    if pivot:
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 340,440p sqlglot/lineage.py; echo ----; grep -rn \"class Pivot(\" -A 40 sqlglot/expressions/*.py | head -60", "description": "Read lineage pivot handling and Pivot class"}
[tool_result]                 _cache=_cache,
                _scope_meta=_scope_meta,
                on_node=on_node,
            )

    # if the select is a star add all scope sources as downstreams
    if isinstance(select, exp.Star):
        for src in scope.sources.values():
            src_expr = src.expression if isinstance(src, Scope) else src
            star_node = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)
            node.downstream.append(star_node)
            if
…[6488 chars elided]…
CT * FROM t UNPIVOT(val FOR name IN (a, b))").find(exp.Pivot)
sqlglot/expressions/query.py-1782-            >>> list(piv.output_columns(["a", "b", "c"]))
sqlglot/expressions/query.py-1783-            ['c', 'name', 'val']
sqlglot/expressions/query.py-1784-
sqlglot/expressions/query.py-1785-        AST shape:
sqlglot/expressions/query.py-1786-            PIVOT(SUM(val) FOR name IN ('a', 'b')):
sqlglot/expressions/query.py-1787-                expressions: aggregate(s), e.g. [Sum(this=Column(val))]
[assistant] The lineage code skips unpivots entirely (`not pivots[0].unpivot`). Before deciding the fix, I'll check the UNPIVOT AST shape and what `output_columns` returns.
[tool_use Bash] {"command": "sed -n 1786,1830p sqlglot/expressions/query.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))''', read='snowflake')\np = e.find(exp.Pivot)\nprint(repr(p))\nprint(list(p.output_columns(['id','jan','feb'])))\nprint(p.args.get('columns'))\n\"", "description": "Inspect UNPIVOT AST and output_columns"}
[tool_result]             PIVOT(SUM(val) FOR name IN ('a', 'b')):
                expressions: aggregate(s), e.g. [Sum(this=Column(val))]
                fields:      [In(this=Column(name), expressions=[Literal('a'), Literal('b')])]
                columns:     optional explicit output identifiers (e.g. set by Snowflake)

            UNPIVOT(val FOR name IN (a, b)):
                expressions: value Identifier(s), or Tuple(Identifiers) for multi-value
                fields:      [In(this=Identifier(name), e
…[1525 chars elided]…
n excluded] + outputs

        alias = self.args.get("alias")
        renames = alias.args.get("columns") if alias else None
Pivot(
  expressions=[
    Identifier(this=score, quoted=False)],
  fields=[
    In(
      this=Identifier(this=metric_name, quoted=False),
      expressions=[
        Column(
          this=Identifier(this=jan, quoted=False)),
        Column(
          this=Identifier(this=feb, quoted=False))])],
  unpivot=True,
  default_on_null=False)
['id', 'metric_name', 'score']
None
[assistant] The UNPIVOT AST is clear: `expressions` holds the value column (`score`), and `fields[0]` holds the name column (`metric_name`) plus the IN list (`jan`, `feb`). Next I need to see how the outer columns get qualified and how the rest of the lineage loop uses `pivot`.
[tool_use Bash] {"command": "sed -n 440,480p sqlglot/lineage.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.optimizer import qualify\nfrom sqlglot import parse_one\nsql='''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''\nprint(qualify.qualify(parse_one(sql, read='snowflake'), schema={'sales': {'id':'int','jan':'int','feb':'int'}}, dialect='snowflake').sql('snowflake'))\n\"; ls tests | grep -i lineage", "description": "Read rest of lineage loop and qualified SQL"}
[tool_result]                         downstream_column.name,
                        scope=col_source,
                        scope_name=table,
                        dialect=dialect,
                        upstream=node,
                        source_name=source_names.get(table) or source_name,
                        reference_node_name=reference_node_name,
                        trim_selects=trim_selects,
                        _cache=_cache,
                        _scope_meta=_scope_meta,
        
…[998 chars elided]…
.downstream.append(leaf)
            if on_node:
                on_node(leaf)

    if _cache is not None:
        _cache[cache_key] = node

    if on_node:
        on_node(node)

    return node

WITH "SRC" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "SRC"."ID" AS "ID", "SRC"."METRIC_NAME" AS "METRIC_NAME", "SRC"."SCORE" AS "SCORE" FROM "SRC" AS "SRC" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SRC"
test_lineage.py
[assistant] The outer columns are qualified as `"SRC"."SCORE"`, and the pivot's alias is also `SRC`. So the phantom comes from `scope.sources["SRC"]` (the CTE) receiving `score`, which the CTE doesn't have. My plan is to rewrite the unpivot's value columns into their IN-list source columns and drop the name column before the existing loop runs. I'll check imports and whether lineage qualifies the query first.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/lineage.py; grep -n \"qualify\" sqlglot/lineage.py | head; grep -n \"^def \\|^class \" sqlglot/lineage.py", "description": "Check lineage imports and qualify usage"}
[tool_result] from __future__ import annotations

import json
import logging
import typing as t
from dataclasses import dataclass, field

from sqlglot import Schema, exp, maybe_parse
from sqlglot.errors import SqlglotError
from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
from sqlglot.optimizer.scope import ScopeType

if t.TYPE_CHECKING:
    from sqlglot.dialects.dialect import DialectType
    from collections.abc import Iterator, Mapping, Sequence
    from sq
…[327 chars elided]…
""

10:from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
137:        expression = qualify.qualify(
141:            **{"validate_qualify_columns": False, "identify": False, **kwargs},  # type: ignore
23:class Node:
81:def lineage(column: str | exp.Column, sql: str | exp.Expr, **kwargs: t.Any) -> Node: ...
85:def lineage(column: None, sql: str | exp.Expr, **kwargs: t.Any) -> dict[str, Node]: ...
88:def lineage(
191:def to_node(
482:class GraphHTML:
[assistant] Lineage qualifies the query first, so the table names are reliable. Now I'll make the edit: a helper that rewrites unpivot columns, applied right after `source_columns` is collected.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    source_columns = set(find_all_in_scope(select, exp.Column))\n\n    # If the source is a UDTF", "new_string": "    source_columns = set(find_all_in_scope(select, exp.Column))\n\n    unpivots = [pivot for pivot in scope.pivots if pivot.unpivot]\n    if len(unpivots) == 1:\n        source_columns = {\n            upstream\n            for c in source_columns\n            for upstream in _unpivot_upstream_columns(c, unpivots[0])\n        }\n\n    # If the source is a UDTF"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "def to_node(\n", "new_string": "def _unpivot_upstream_columns(column: exp.Column, pivot: exp.Pivot) -> list[exp.Column]:\n    if column.table != pivot.alias_or_name:\n        return [column]\n\n    in_field = pivot.fiel
…[533 chars elided]…
ource_table = pivot.parent.alias_or_name if pivot.parent else \"\"\n    upstream = []\n    for entry in in_field.expressions:\n        entry = entry.this if isinstance(entry, exp.PivotAlias) else entry\n        source = entry.expressions[index] if isinstance(entry, exp.Tuple) else entry\n        upstream.append(exp.column(source.name, table=source_table))\n    return upstream\n\n\ndef to_node(\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll rerun the repro, plus an aliased variant and a case with an aliased IN entry.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = [\n ('''WITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))''', [\"score\",\"metric_name\",\"id\"]),\n ('''WITH src AS (SELECT id, jan, feb FROM sales)\nSEL
…[443 chars elided]…
\"sales.id\") or n.name.upper().endswith((\"JAN\",\"FEB\",\"ID\",\"SCORE\",\"METRIC_NAME\"))])\n        print(\"   leaves:\", sorted({n.name for n in node.walk() if not n.downstream}))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro2.py').read())\"", "description": "Rerun unpivot lineage repro cases"}
[tool_result] score -> ['SCORE', 'SRC.FEB', 'SRC.JAN']
   leaves: ['SRC.FEB', 'SRC.JAN']
metric_name -> ['METRIC_NAME']
   leaves: ['METRIC_NAME']
id -> ['ID', 'SRC.ID']
   leaves: ['SRC.ID']
score -> ['SCORE', 'S.FEB', 'S.JAN']
   leaves: ['S.FEB', 'S.JAN']
metric_name -> ['METRIC_NAME']
   leaves: ['METRIC_NAME']
[assistant] The phantom is gone: `score` now reaches `jan`/`feb`, and `metric_name` is a leaf. But the leaves read `SRC.JAN` instead of `SALES.JAN`, so the walk may not be descending into the CTE. The untouched `id` pass-through shows the same shape, so I'll check whether this is pre-existing behavior for a plain CTE.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nsql='WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, jan FROM src'\ndef show(n, d=0):\n    print('  '*d, n.name, '|', n.source.sql() if n.source else None)\n    for c in n.downstream: show(c, d+1)\nshow(lineage('jan', sql, schema=schema, dialect='snowflake'))\n\"", "description": "Compare plain CTE lineage tree shape"}
[tool_result]  JAN | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.JAN AS JAN FROM SRC AS SRC
   SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
[assistant] A plain CTE chains correctly down to `SALES.JAN`, so my unpivot case is cutting the chain somewhere. I'll print the full tree for the unpivot case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nsql='WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'\ndef show(n, d=0):\n    print('  '*d, n.name, '|', n.source.sql()[:90] if n.source else None)\n    for c in n.downstream: show(c, d+1)\nshow(lineage('score', sql, schema=schema, dialect='snowflake'))\n\"", "description": "Print full unpivot lineage tree"}
[tool_result]  SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES
   SRC.FEB | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (SRC.JAN, SRC.FEB)) AS SRC
   SRC.JAN | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (SRC.JAN, SRC.FEB)) AS SRC
[assistant] Found it. For a pivoted source, `scope.sources` maps the pivot alias to the pivot's `Table` expression, not the CTE's `Scope`, so the recursion falls to the leaf branch. Let me read that scope code.
[tool_use Bash] {"command": "sed -n 830,855p sqlglot/optimizer/scope.py", "description": "Read scope source registration for pivoted tables"}
[tool_result]     if isinstance(scope.expression, exp.Table):
        expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
          
…[151 chars elided]…
w table and hence a new source.
                pivots = expression.args.get("pivots")
                if pivots:
                    sources[pivots[0].alias] = expression
                else:
                    sources[source_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
                sources[source_name] = expression

            # Make sure to not include the joins twice
[assistant] The scope code deliberately registers a pivoted CTE reference under the pivot alias as a new `Table`, so the CTE `Scope` isn't reachable under that key. Let me see what `Scope` exposes for CTE lookup.
[tool_use Bash] {"command": "grep -n \"cte_sources\\|self.sources\\b\" sqlglot/optimizer/scope.py | head -30; grep -n \"def sources\\|cte_sources\" sqlglot/optimizer/scope.py", "description": "Locate cte_sources on Scope"}
[tool_result] 64:        cte_sources: Sources from CTES
109:        cte_sources: dict[str, exp.Table | Scope] | None = None,
113:        self.sources = sources or {}
115:        self.cte_sources = cte_sources or {}
116:        self.sources.update(self.lateral_sources)
117:        self.sources.update(self.cte_sources)
156:        cte_sources: dict[str, exp.Table | Scope] | None = None,
166:            cte_sources={**self.cte_sources, **(cte_sources or {})},
420:                if name in self.sources:
421:    
…[643 chars elided]…
self.cte_sources = cte_sources or {}
117:        self.sources.update(self.cte_sources)
156:        cte_sources: dict[str, exp.Table | Scope] | None = None,
166:            cte_sources={**self.cte_sources, **(cte_sources or {})},
698:            yield from _traverse_scope(Scope(ddl_expression, cte_sources=scope.cte_sources))
705:                yield from _traverse_scope(Scope(query, cte_sources=scope.cte_sources))
778:                cte_sources=sources,
791:    scope.cte_sources.update(sources)
[assistant] `Scope.cte_sources` holds the CTE scopes, so the fix is to resolve a pivoted CTE reference back to its CTE scope. I'll scope that to unpivot queries so existing PIVOT lineage behavior is untouched. I'll also move the unpivot rewrite after `pivots = scope.pivots` so it sits with the pivot logic.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    unpivots = [pivot for pivot in scope.pivots if pivot.unpivot]\n    if len(unpivots) == 1:\n        source_columns = {\n            upstream\n            for c in source_columns\n            for upstream in _unpivot_upstream_columns(c, unpivots[0])\n        }\n\n    # If the source is a UDTF", "new_string": "    # If the source is a UDTF"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None", "new_string": "    pivots = scope.pivots\n    unpivot = pivots[0] if len(pivots) == 1 and pivots[0].unpivot else None\n    if unpivot:\n        source_columns = {\n            upstream for c in source_columns for upstream in _unpivot_upstream_columns(c, unpivot)\n        }\n\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "        col_source: exp.Table | Scope | None = scope.sources.get(table)\n\n        if isinstance(col_source, Scope):", "new_string": "        col_source: exp.Table | Scope | None = scope.sources.get(table)\n        if unpivot and isinstance(col_source, exp.Table) and col_source.args.get(\"pivots\"):\n            # A pivoted CTE reference is registered as its pivoted table, so resolve the CTE itself\n            col_source = scope.cte_sources.get(col_source.name, col_source)\n\n        if isinstance(col_source, Scope):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ndef show(n, d=0):\n    print('  '*d, n.name, '|', n.source.sql()[:70].replace(chr(10),' ') if n.source else None)\n    for c in n.downstream: show(c, d+1)\nsql='''\nWI
…[318 chars elided]…
score FROM src AS s UNPIVOT (score FOR metric_name IN (jan AS \\'Jan\\', feb)) AS u'\nprint('== alias'); show(lineage('score', sql2, schema=schema, dialect='snowflake'))\nsql3='SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))'\nprint('== real table'); show(lineage('score', sql3, schema=schema, dialect='snowflake'))\n\"", "description": "Verify unpivot lineage trees after fix"}
[tool_result] == score
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
     SALES.FEB | SALES AS SALES
   SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
== metric_name
 METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
== id
 ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   SRC.ID | SELECT SALES.ID AS ID FROM SALES AS SALES
     SALES.ID | SALES AS SALES
== alias
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   S.JAN | ?
   S.FEB | ?
== real table
 SCORE | SELECT SALES.SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCORE FOR METR
   SALES.FEB | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (SALES.JAN, SALES.FEB)
   SALES.JAN | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (SALES.JAN, SALES.FEB)
[assistant] The main case now reaches `SALES.JAN` and `SALES.FEB`, `metric_name` is a leaf, and `id` also traces through to `SALES.ID`. The aliased case still fails: `FROM src AS s UNPIVOT ... AS u` produces placeholders, because I pointed the upstream columns at the parent's alias (`s`), which isn't a key in `scope.sources`. The pivot's own alias (`u`) is the key that maps to the pivoted table, so I'll use that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    index = value_names.index(column.name)\n    source_table = pivot.parent.alias_or_name if pivot.parent else \"\"\n    upstream = []\n    for entry in in_field.expressions:\n        entry = entry.this if isinstance(en
…[189 chars elided]…
    return upstream", "new_string": "    index = value_names.index(column.name)\n    upstream = []\n    for entry in in_field.expressions:\n        entry = entry.this if isinstance(entry, exp.PivotAlias) else entry\n        source = entry.expressions[index] if isinstance(entry, exp.Tuple) else entry\n        upstream.append(exp.column(source.name, table=pivot.alias_or_name))\n    return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ndef show(n, d=0):\n    print('  '*d, n.name, '|', n.source.sql()[:70].replace(chr(10),' ') if n.source else None)\n    for c in n.downstream: show(c, d+1)\nsql2='WITH 
…[281 chars elided]…
etric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb)) AS u'\nprint('== alias2'); show(lineage('score', sql4, schema=schema, dialect='snowflake'))\n\"; <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unpivot.py').read())\" | head -3", "description": "Recheck aliased unpivot lineage cases"}
[tool_result] == alias
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   U.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
   U.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
     SALES.FEB | SALES AS SALES
== alias2
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   U.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
   U.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
     SALES.FEB | SALES AS SALES
score
   SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.
   SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
[assistant] Aliased cases now resolve through to `SALES.JAN`/`SALES.FEB`. Next I'll add a regression test next to the existing lineage tests and run the suite.
[tool_use Bash] {"command": "grep -n -i \"pivot\" tests/test_lineage.py | head; grep -n \"def test_\" tests/test_lineage.py | tail -5; tail -30 tests/test_lineage.py", "description": "Find pivot tests and style in lineage tests"}
[tool_result] 607:    def test_pivot_without_alias(self) -> None:
612:        PIVOT (
622:    def test_pivot_with_alias(self) -> None:
627:            PIVOT (
637:    def test_pivot_with_cte(self) -> None:
643:            PIVOT (
656:    def test_pivot_with_implicit_column_of_pivoted_source(self) -> None:
660:            PIVOT(SUM(amount) FOR quarter IN (
670:    def test_pivot_with_implicit_column_of_pivoted_source_and_cte(self) -> None:
675:            PIVOT(SUM(amount) FOR quarter IN (
905:    def test_lin
…[975 chars elided]…
      "WITH t AS (SELECT a, b FROM x) SELECT a, a + b AS ab FROM t",
            schema={"x": {"a": "int", "b": "int"}},
            on_node=hook,
        )

        # Walk every reachable Node from both output columns; each should
        # have been emitted to the hook exactly once.
        seen: set[int] = set()
        for top in result.values():
            for node in top.walk():
                seen.add(id(node))
        for nid in seen:
            self.assertEqual(counts.get(nid, 0), 1)
[tool_use Bash] {"command": "sed -n 636,690p tests/test_lineage.py", "description": "Read existing pivot lineage tests"}
[tool_result]     def test_pivot_with_cte(self) -> None:
        sql = """
        WITH t as (
            SELECT
                a as other_a
            FROM sample_data
            PIVOT (
                sum(value)
                FOR category IN ('a', 'b')
            )
        )
        select other_a from t
        """
        node = lineage("other_a", sql)

        self.assertEqual(node.downstream[0].name, "t.other_a")
        self.assertEqual(node.downstream[0].reference_node_name, "t")
        self.
…[732 chars elided]…
                '2023_Q2',
                '2023_Q3'))
        )
        select empid from t
        """
        node = lineage("empid", sql)

        self.assertEqual(node.downstream[0].name, "t.empid")
        self.assertEqual(node.downstream[0].reference_node_name, "t")
        self.assertEqual(node.downstream[0].downstream[0].name, "quarterly_sales.empid")

    def test_table_udtf_snowflake(self) -> None:
        lateral_flatten = """
        SELECT f.value:external_id::string AS external_id
[assistant] I'll add a regression test after the existing pivot-with-CTE tests, using the same style, and run the lineage tests to confirm the expected names.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(node.downstream[0].name, \"t.empid\")\n        self.assertEqual(node.downstream[0].reference_node_name, \"t\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"quarterly_sal
…[786 chars elided]…
.jan\"],\n        )\n\n        node = lineage(\"metric_name\", sql, schema=schema)\n        self.assertEqual(list(node.walk())[-1].name, \"metric_name\")\n        self.assertFalse(node.downstream)\n\n        node = lineage(\"id\", sql, schema=schema)\n        self.assertEqual(\n            sorted(leaf.name for leaf in node.walk() if not leaf.downstream),\n            [\"sales.id\"],\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[assistant] That `metric_name` assertion is clumsy; I'll simplify it to check the node has no downstream.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"metric_name\", sql, schema=schema)\n        self.assertEqual(list(node.walk())[-1].name, \"metric_name\")\n        self.assertFalse(node.downstream)", "new_string": "        node = lineage(\"metric_name\", sql, schema=schema)\n        self.assertFalse(node.downstream)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100728-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py -k \"unpivot or pivot\" 2>&1 | tail -30", "description": "Run pivot-related lineage tests"}
[tool_result] .......                                                                  [100%]
7 passed, 32 deselected in 0.07s
[assistant] Pivot tests pass. Now the project's full check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 27%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[270 chars elided]…
......... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1116 passed, 18166 subtests passed in 48.38s
[assistant] All 1116 tests pass. I'll run the linter and formatter on the two changed files, since the project pre-commit hooks use ruff.
[tool_use Bash] {"command": "E=<work>/env-sqlglot/bin; ($E/ruff --version && $E/ruff check sqlglot/lineage.py tests/test_lineage.py && $E/ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -8; git diff --stat", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 sqlglot/lineage.py    | 36 ++++++++++++++++++++++++++++++++++++
 tests/test_lineage.py | 23 +++++++++++++++++++++++
 2 files changed, 59 insertions(+)
[assistant] `lineage()` now traces UNPIVOT value columns back to their source columns, and the name column no longer produces a phantom. The full suite passes (1116 tests) and ruff is clean. I haven't committed.

On your example, `score` now reaches `sales.jan` and `sales.feb`, and `metric_name` has no upstream columns, like a literal. `id` also traces through to `sales.id`, which it previously didn't.

Two things were behind the bug:
- **Value and name columns:** `lineage()` skipped UNPIVOT entirely, so `score` was treated as a column of the input relation. A new helper, `_unpivot_upstream_columns` in `s
…[202 chars elided]…
 so the walk stopped at the pivot. For UNPIVOT queries, `lineage()` now resolves that reference back to the CTE via `scope.cte_sources`. I limited this to UNPIVOT so existing PIVOT lineage is unchanged.

I added `test_unpivot_with_cte` to `tests/test_lineage.py`, covering the value column, the name column, and a pass-through column. Aliased UNPIVOTs (`FROM src AS s UNPIVOT ... AS u`) also resolve correctly, though I didn't add a test for that case.

Multi-value UNPIVOTs map each value column to the same position in every IN-list tuple. I checked that by reading the code, not by running a case.
