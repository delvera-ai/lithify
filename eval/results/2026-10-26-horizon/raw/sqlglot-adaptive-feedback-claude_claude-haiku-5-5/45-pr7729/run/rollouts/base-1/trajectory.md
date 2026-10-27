# trajectory base-1

final message:
`lineage()` now traces `UNPIVOT` value and name columns back to the IN-list columns, and through the CTE they read from. The full suite passed after the last edit: `SUMMARY: 1116 passed, 18166 subtests passed in 52.59s`, `EXIT: 0`.

Your example now gives:

- `score` → `SRC.JAN`, `SRC.FEB` → `SALES.JAN`, `SALES.FEB`
- `metric_name` → the same `JAN`/`FEB` chain
- `id` (pass-through) → `SRC.ID` → `SALES.ID`

Before the change, `score` ended at a phantom `SRC.SCORE` leaf on the input relation.

**What changed**

- `sqlglot/lineage.py`:
  - The unpivot case was previously excluded from the pivot handling. It now maps the value and name columns to the IN-list columns, and non-unpivoted columns keep their existing pass-through behaviour.
  - An UNPIVOT's alias shadows the CTE it reads from in `scope.sources`. The code now resolves the CTE through `scope.cte_sources`, so the trace reaches `sales` rather than stopping at the alias.
- `tests/test_lineage.py`: added `test_unpivot_with_cte`, which checks the `score`, `metric_name` and `id` chains above.

**Choices to check**

- The name column is treated as derived from the IN-list columns, so `metric_name` also points at `jan` and `feb`. Its values are the literal column names, so this is my reading rather than something the request spelled out. If you want it to have no source columns, that is a small change.
- Aliased IN-list entries such as `jan AS 'J'` are unwrapped to the underlying column.

**Not changed**

- The scope builder still treats a pivoted table as a new source, so a `PIVOT` over a CTE has the same shadowing problem. I left PIVOT alone because the request was about UNPIVOT.

## events
[tool_use Bash] {"command": "git status --short | head && ls .lithify/harness/ && ls <work>/env-sqlglot/bin/python 2>&1; grep -n -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -40", "description": "Check repo state, python env, and unpivot references"}
[tool_use Bash] {"command": "cat sqlglot/lineage.py | head -250", "description": "Read lineage module"}
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
…[7851 chars elided]…
 = meta
            select = select_by_name.get(column, exp.Star() if is_star else scope.expression)

    if isinstance(scope.expression, exp.Subquery):
        for inner_scope in scope.subquery_scopes:
            result = to_node(
                column,
                scope=inner_scope,
                dialect=dialect,
                upstream=upstream,
                source_name=source_name,
                reference_node_name=reference_node_name,
                trim_selects=trim_selects,
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
<work>/env-sqlglot/bin/python
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
sqlglot/optimizer/qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
[tool_use Bash] {"command": "sed -n 250,520p sqlglot/lineage.py; cat .lithify/harness/tool_guidance.md | head -5 >/dev/null", "description": "Read rest of lineage module"}
[tool_result]                 trim_selects=trim_selects,
                _cache=_cache,
                _scope_meta=_scope_meta,
                on_node=on_node,
            )
            # Skip caching a passed-in upstream returned by an inner SetOp:
            # a sibling call at the same key with that node as its upstream
            # would otherwise self-loop on the cache hit.
            if _cache is not None and result is not upstream:
                _cache[cache_key] = result
            return resu
…[9698 chars elided]…
         "nodeSpacing": 200,
                    "sortMethod": "directed",
                },
            },
            "interaction": {
                "dragNodes": False,
                "selectable": False,
            },
            "physics": {
                "enabled": False,
            },
            "edges": {
                "arrows": "to",
            },
            "nodes": {
                "font": "20px monaco",
                "shape": "box",
                "widthConstraint": {
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nsql='''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema={'sales': {'id': 'int', 
…[187 chars elided]…
,schema=schema,validate_qualify_columns=False,identify=False)\nprint(e.sql('snowflake',pretty=True))\nfor n in ['score','metric_name']:\n  node=lineage(n,sql,schema=schema,dialect='snowflake')\n  print(n)\n  for x in node.walk(): print('  ',x.name,'|',x.expression.sql('snowflake'),'|',type(x.expression).__name__, x.source_name)\n\"", "description": "Probe current lineage output for UNPIVOT query"}
[tool_result] WITH SRC AS (
  SELECT
    SALES.ID AS ID,
    SALES.JAN AS JAN,
    SALES.FEB AS FEB
  FROM SALES AS SALES
)
SELECT
  SRC.ID AS ID,
  SRC.METRIC_NAME AS METRIC_NAME,
  SRC.SCORE AS SCORE
FROM SRC AS SRC
UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
score
   SCORE | SRC.SCORE AS SCORE | Alias 
   SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
metric_name
   METRIC_NAME | SRC.METRIC_NAME AS METRIC_NAME | Alias 
   SRC.METRIC_NAME | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))',read='snowflake')\nprint(repr(e.args['from'].this.args.get('pivots')))\ne=sqlglot.parse_one('SELECT * FROM src PIVOT (SUM(v) AS s FOR c IN (\\'a\\' AS A, \\'b\\'))',read='snowflake')\nprint(repr(e.args['from'].this.args.get('pivots')))\n\"; grep -n -i \"pivot\\|unpivot\" tests/test_lineage.py | head -30", "description": "Inspect UNPIVOT AST shape and existing lineage pivot tests"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'from'
607:    def test_pivot_without_alias(self) -> None:
612:        PIVOT (
622:    def test_pivot_with_alias(self) -> None:
627:            PIVOT (
637:    def test_pivot_with_cte(self) -> None:
643:            PIVOT (
656:    def test_pivot_with_implicit_column_of_pivoted_source(self) -> None:
660:            PIVOT(SUM(amount) FOR quarter IN (
670:    def test_pivot_with_implicit_column_of_pivoted_source_and_cte(self) -> None:
675:            PIVOT(SUM(amount) FOR quarter IN (
733:    def test_pivot_with_subquery(self) -> None:
747:            ) PIVOT (
[tool_use Bash] {"command": "sed -n 600,760p tests/test_lineage.py; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))',read='snowflake')\np=e.find(sqlglot.exp.Pivot)\nprint(repr(p))\n\"", "description": "Read existing pivot lineage tests and Pivot AST"}
[tool_result]         sql = "SELECT * FROM (SELECT x /* c */ FROM t1) AS t2"
        node = lineage("x", sql)

        self.assertEqual(len(node.downstream), 1)
        self.assertEqual(len(node.downstream[0].downstream), 1)
        self.assertEqual(node.downstream[0].downstream[0].name, "t1.x")

    def test_pivot_without_alias(self) -> None:
        sql = """
        SELECT
            a as other_a
        FROM (select value,category from sample_data)
        PIVOT (
            sum(value)
            FOR c
…[4700 chars elided]…
tEqual(node.downstream[0].name, "cte.product_type")
        self.assertEqual(node.downstream[0].downstream[0].name, "_0.product_type")
        self.assertEqual(
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
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM src UNPIVOT (score FOR metric_name IN (jan AS \\'J\\', feb))',read='snowflake')\np=e.find(sqlglot.exp.Pivot); print(repr(p.args['fields'][0].expressions))\nfrom sql
…[32 chars elided]…
=qualify.qualify(sqlglot.parse_one('SELECT id FROM src UNPIVOT (score FOR metric_name IN (jan, feb))',read='snowflake'),dialect='snowflake',schema={'src':{'id':'int','jan':'int','feb':'int'}},validate_qualify_columns=False,identify=False)\nprint(q.sql('snowflake'))\n\"; grep -n \"class Pivot\" -A 25 sqlglot/expressions/*.py | head -40", "description": "Check aliased IN-list shape and Pivot class"}
[tool_result] [PivotAlias(
  this=Column(
    this=Identifier(this=jan, quoted=False)),
  alias=Literal(this='J', is_string=True)), Column(
  this=Identifier(this=feb, quoted=False))]
SELECT SRC.ID AS ID FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
sqlglot/expressions/core.py:1905:class PivotAlias(Alias):
sqlglot/expressions/core.py-1906-    pass
sqlglot/expressions/core.py-1907-
sqlglot/expressions/core.py-1908-
sqlglot/expressions/core.py:1909:class PivotAny(Expression):
sqlglot/expre
…[1517 chars elided]…
.py-1748-    arg_types = {
sqlglot/expressions/query.py-1749-        "this": False,
sqlglot/expressions/query.py-1750-        "alias": False,
sqlglot/expressions/query.py-1751-        "expressions": False,
sqlglot/expressions/query.py-1752-        "fields": False,
sqlglot/expressions/query.py-1753-        "unpivot": False,
sqlglot/expressions/query.py-1754-        "using": False,
sqlglot/expressions/query.py-1755-        "group": False,
sqlglot/expressions/query.py-1756-        "columns": False,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:", "new_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 else None\n  
…[67 chars elided]…
 of an UNPIVOT are fed by the columns listed in its IN clause\n        unpivot_outputs = {e.name for e in pivot.expressions} | {f.this.name for f in pivot.args[\"fields\"]}\n        unpivot_columns = [\n            col.this if isinstance(col, exp.PivotAlias) else col\n            for f in pivot.args[\"fields\"]\n            for col in f.expressions\n        ]\n    if pivot and not pivot.unpivot:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"elif pivot and pivot.alias_or_name\" -A 22 sqlglot/lineage.py", "description": "Show the pivot branch to edit"}
[tool_result] 429:        elif pivot and pivot.alias_or_name == c.table:
430-            downstream_columns = []
431-
432-            column_name = c.name
433-            if any(column_name == pivot_column.name for pivot_column in pivot_columns):
434-                downstream_columns.extend(pivot_column_mapping[column_name])
435-            else:
436-                # The column is not in the pivot, so it must be an implicit column of the
437-                # pivoted source -- adapt column to be from the im
…[192 chars elided]…
e if pivot_parent else "")
441-                )
442-
443-            for downstream_column in downstream_columns:
444-                table = downstream_column.table
445-                col_source = scope.sources.get(table)
446-                if isinstance(col_source, Scope):
447-                    to_node(
448-                        downstream_column.name,
449-                        scope=col_source,
450-                        scope_name=table,
451-                        dialect=dialect,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            column_name = c.name\n            if any(column_name == pivot_column.name for pivot_column in pivot_columns):\n                downstream_columns.extend(pivot_column_mapping[column_name])\n            else:\
…[946 chars elided]…
(pivot_column_mapping[column_name])\n            else:\n                # The column is not in the pivot, so it must be an implicit column of the\n                # pivoted source -- adapt column to be from the implicit pivoted source.\n                downstream_columns.append(\n                    exp.column(c.this, table=pivot_parent.alias_or_name if pivot_parent else \"\")\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nsql='''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema={'sales': {'id': 'int', 
…[152 chars elided]…
de.walk(): print('  ',x.name,'|',x.expression.sql('snowflake'),'|',type(x.expression).__name__, x.source_name)\nsql2='SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan AS \\'J\\', feb))'\nnode=lineage('score',sql2,schema=schema,dialect='snowflake')\nfor x in node.walk(): print('  ',x.name,'|',x.expression.sql('snowflake'))\n\"", "description": "Probe lineage after the UNPIVOT change"}
[tool_result] score
   SCORE | SRC.SCORE AS SCORE | Alias 
   SRC.JAN | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
   SRC.FEB | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
metric_name
   METRIC_NAME | SRC.METRIC_NAME AS METRIC_NAME | Alias 
   SRC.JAN | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
   SRC.FEB | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
id
   ID | SRC.ID AS ID | Alias 
   SRC.ID | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | Table 
   SCORE | SALES.SCORE AS SCORE
   SALES.JAN | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN AS J, FEB)) AS SALES
   SALES.FEB | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN AS J, FEB)) AS SALES
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import qualify, build_scope\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nfor sql in ['''WITH src AS (SELECT
…[332 chars elided]…
se_one(sql,read='snowflake'),dialect='snowflake',schema=schema,validate_qualify_columns=False,identify=False)\n  s=build_scope(e)\n  print(e.sql('snowflake'))\n  print({k:type(v).__name__ for k,v in s.sources.items()})\n  n=lineage('score',sql,schema=schema,dialect='snowflake')\n  print([x.name for x in n.walk()])\n\" 2>&1 | head -40", "description": "Compare scope sources for CTE-backed UNPIVOT"}
[tool_result] WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.ID AS ID, SRC.SCORE AS SCORE FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
{'SRC': 'Table'}
['SCORE', 'SRC.JAN', 'SRC.FEB']
WITH T AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT T.ID AS ID, T.SCORE AS SCORE FROM T AS T UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS T
{'T': 'Table'}
['SCORE', 'T.JAN', 'T.FEB']
SELECT SALES.ID AS ID, SALES.SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
{'SALES': 'Table'}
['SCORE', 'SALES.JAN', 'SALES.FEB']
[tool_use Bash] {"command": "grep -n \"pivot\\|cte_sources\\[\" sqlglot/optimizer/scope.py | head -40", "description": "Find pivot and CTE source handling in scope builder"}
[tool_result] 98:    _pivots: list[exp.Pivot] | None
148:        self._pivots = None
440:                            expression if expression.args.get("pivots") else expression.unnest()
508:    def pivots(self) -> list[exp.Pivot]:
509:        if self._pivots is None:
510:            self._pivots = [
511:                pivot for _, node in self.references for pivot in node.args.get("pivots") or []
514:        return self._pivots
844:                # it is pivoted, because then we get back a new table and hence a new source.
845:                pivots = expression.args.get("pivots")
846:                if pivots:
847:                    sources[pivots[0].alias] = expression
984:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "sed -n 825,870p sqlglot/optimizer/scope.py", "description": "Read scope source assignment for pivoted tables"}
[tool_result]         expressions.append(from_.this)

    for join in scope.expression.args.get("joins") or []:
        expressions.append(join.this)

    if isinstance(scope.expression, exp.Table):
        expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = express
…[825 chars elided]…
pe.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
            continue

        # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable/UDTF trait vtable dispatch
        node: exp.Expr = expression

        if isinstance(expression, exp.UDTF):
            lateral_sources = sources
            scope_type = ScopeType.UDTF
            scopes = scope.udtf_scopes
[tool_use Bash] {"command": "grep -n \"cte_sources\" sqlglot/optimizer/scope.py | head -20; grep -n \"def selected_sources\" -B3 -A3 sqlglot/optimizer/scope.py | head", "description": "Check how scope tracks CTE sources"}
[tool_result] 64:        cte_sources: Sources from CTES
109:        cte_sources: dict[str, exp.Table | Scope] | None = None,
115:        self.cte_sources = cte_sources or {}
117:        self.sources.update(self.cte_sources)
156:        cte_sources: dict[str, exp.Table | Scope] | None = None,
166:            cte_sources={**self.cte_sources, **(cte_sources or {})},
698:            yield from _traverse_scope(Scope(ddl_expression, cte_sources=scope.cte_sources))
705:                yield from _traverse_scope(Scope(query, cte_sources=scope.cte_sources))
778:                cte_sources=sources,
791:    scope.cte_sources.update(sources)
396-        return self._table_columns
397-
398-    @property
399:    def selected_sources(self) -> dict[str, tuple[exp.Selectable, exp.Table | Scope]]:
400-        """
401-        Mapping of nodes and sources that are actually selected from in this scope.
402-
[tool_use Bash] {"command": "grep -n \"pivot_parent = pivot.parent\" -B6 -A40 sqlglot/lineage.py | sed -n 1,60p", "description": "Show current pivot branch with downstream loop"}
[tool_result] 427-                on_node=on_node,
428-            )
429-        elif pivot and pivot.alias_or_name == c.table:
430-            downstream_columns = []
431-
432-            column_name = c.name
433:            pivot_parent = pivot.parent
434-            if pivot.unpivot and column_name in unpivot_outputs:
435-                downstream_columns.extend(
436-                    exp.column(col.this, table=pivot_parent.alias_or_name if pivot_parent else "")
437-                    for col in unpivo
…[1339 chars elided]…
ects,
463-                        _cache=_cache,
464-                        _scope_meta=_scope_meta,
465-                        on_node=on_node,
466-                    )
467-                else:
468-                    col_expr = col_source or exp.Placeholder()
469-                    pivot_leaf = Node(
470-                        name=downstream_column.sql(comments=False),
471-                        source=col_expr,
472-                        expression=col_expr,
473-                    )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "                    exp.column(c.this, table=pivot_parent.alias_or_name if pivot_parent else \"\")\n                )\n\n            for downstream_column in downstream_columns:\n                table = downstream_colum
…[240 chars elided]…
 the CTE it reads from in scope.sources, so look that up directly\n            unpivoted_source = (\n                scope.cte_sources.get(pivot_parent.name) if pivot.unpivot and pivot_parent else None\n            )\n            for downstream_column in downstream_columns:\n                table = downstream_column.table\n                col_source = unpivoted_source or scope.sources.get(table)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nfor sql,d in [('''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (sc
…[74 chars elided]…
OM sales AS s UNPIVOT (score FOR metric_name IN (jan AS \\'J\\', feb))','snowflake')]:\n  for n in ['score','metric_name','id']:\n    try: node=lineage(n,sql,schema=schema,dialect=d)\n    except Exception as ex: print(n, 'ERR', ex); continue\n    print(n)\n    for x in node.walk(): print('  ',x.name,'|',x.expression.sql('snowflake'))\n\"", "description": "Probe lineage through CTE-backed UNPIVOT"}
[tool_result] score
   SCORE | SRC.SCORE AS SCORE
   SRC.JAN | SALES.JAN AS JAN
   SALES.JAN | SALES AS SALES
   SRC.FEB | SALES.FEB AS FEB
   SALES.FEB | SALES AS SALES
metric_name
   METRIC_NAME | SRC.METRIC_NAME AS METRIC_NAME
   SRC.JAN | SALES.JAN AS JAN
   SALES.JAN | SALES AS SALES
   SRC.FEB | SALES.FEB AS FEB
   SALES.FEB | SALES AS SALES
id
   ID | SRC.ID AS ID
   SRC.ID | SALES.ID AS ID
   SALES.ID | SALES AS SALES
score
   SCORE | S.SCORE AS SCORE
   S.JAN | SALES AS S UNPIVOT(SCORE FOR METRIC_NAME IN (JAN AS J, FEB)) AS S
   S.FEB | SALES AS S UNPIVOT(SCORE FOR METRIC_NAME IN (JAN AS J, FEB)) AS S
metric_name ERR Cannot find column 'METRIC_NAME' in query.
id
   ID | S.ID AS ID
   S.ID | SALES AS S UNPIVOT(SCORE FOR METRIC_NAME IN (JAN AS J, FEB)) AS S
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "    def test_table_udtf_snowflake(self) -> None:", "new_string": "    def test_unpivot_with_cte(self) -> None:\n        schema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\n        sql = \"\"\
…[551 chars elided]…
 schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SRC.JAN\", \"SRC.FEB\"])\n\n        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\n\n    def test_table_udtf_snowflake(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104020-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/lineage.py tests/test_lineage.py 2>&1; <work>/env-sqlglot/bin/python -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; git diff --stat", "description": "Format and lint edited files, show diff stat"}
[tool_result] 1 file reformatted, 1 file left unchanged
All checks passed!
 sqlglot/lineage.py    | 31 ++++++++++++++++++++++++++-----
 tests/test_lineage.py | 20 ++++++++++++++++++++
 2 files changed, 46 insertions(+), 5 deletions(-)
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py tests/test_lineage.py", "description": "Run lineage test file", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:11:12 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/test_lineage.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-a9ab02e355.log
ELAPSED: 0s
SUMMARY: 39 passed in 0.12s
EXIT: 0
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:11:15 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-a9ab02e355.log
ELAPSED: 53s
SUMMARY: 1116 passed, 18166 subtests passed in 52.59s
EXIT: 0
[tool_use Bash] {"command": "git diff sqlglot/lineage.py", "description": "Review final lineage diff"}
[tool_result] diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 4b84f7ba7..4af0d9dd0 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -372,8 +372,18 @@ def to_node(
     }
 
     pivots = scope.pivots
-    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
-    if pivot:
+    pivot = pivots[0] if len(pivots) == 1 else None
+    if pivot and pivot.unpivot:
+        # The value and name columns of an UNPIVOT are fed by the columns listed in its IN clause
+        unpiv
…[1911 chars elided]…
voted_source = (
+                scope.cte_sources.get(pivot_parent.name) if pivot.unpivot and pivot_parent else None
+            )
             for downstream_column in downstream_columns:
                 table = downstream_column.table
-                col_source = scope.sources.get(table)
+                col_source = unpivoted_source or scope.sources.get(table)
                 if isinstance(col_source, Scope):
                     to_node(
                         downstream_column.name,
[tool_use Bash] {"command": "grep -n \"__len__\\|__bool__\" sqlglot/optimizer/scope.py; git status --short", "description": "Check Scope truthiness and changed files"}
[tool_result]  M sqlglot/lineage.py
 M tests/test_lineage.py
[assistant] `lineage()` now traces `UNPIVOT` value and name columns back to the IN-list columns, and through the CTE they read from. The full suite passed after the last edit: `SUMMARY: 1116 passed, 18166 subtests passed in 52.59s`, `EXIT: 0`.

Your example now gives:

- `score` → `SRC.JAN`, `SRC.FEB` → `SALES.JAN`, `SALES.FEB`
- `metric_name` → the same `JAN`/`FEB` chain
- `id` (pass-through) → `SRC.ID` → `SALES.ID`

Before the change, `score` ended at a phantom `SRC.SCORE` leaf on the input relation.

**What changed**

- `sqlglot/lineage.py`:
  - The unpivot case was previously excluded from the pivot h
…[457 chars elided]…
.

**Choices to check**

- The name column is treated as derived from the IN-list columns, so `metric_name` also points at `jan` and `feb`. Its values are the literal column names, so this is my reading rather than something the request spelled out. If you want it to have no source columns, that is a small change.
- Aliased IN-list entries such as `jan AS 'J'` are unwrapped to the underlying column.

**Not changed**

- The scope builder still treats a pivoted table as a new source, so a `PIVOT` over a CTE has the same shadowing problem. I left PIVOT alone because the request was about UNPIVOT.
