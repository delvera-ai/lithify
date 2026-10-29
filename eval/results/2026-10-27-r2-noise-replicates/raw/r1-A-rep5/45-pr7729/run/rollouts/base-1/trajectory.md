# trajectory base-1

final message:
UNPIVOT lineage now reaches the source columns. In your example, `score` traces to `SRC.JAN` and `SRC.FEB`, then to `sales.jan` and `sales.feb`. Before, it returned a phantom `SRC.SCORE` with no upstream.

**Cause:** `sqlglot/lineage.py` only handled pivots when `not pivot.unpivot`, so UNPIVOT columns fell through to a leaf on the input relation. Also, a pivoted CTE is overwritten in `scope.sources` by its `Table` node, so the CTE scope was never reachable from there.

**Fix (`sqlglot/lineage.py`):**
- The pivot aggregate mapping now applies only to real PIVOTs.
- A new helper, `_unpivot_source_columns`, maps each output column to input columns:
  - **Value columns** map to their IN-list columns. For multi-value UNPIVOTs, each tuple position maps to its own column (`a` → `jan_a`, `feb_a`; `b` → `jan_b`, `feb_b`).
  - **Name column** maps to its unaliased IN-list columns. Literal-aliased entries like `jan AS 'J'` have no source column, so they add nothing.
  - **Passthrough columns** such as `id` map to the same-named input column.
- Input columns resolve through `scope.cte_sources`, so the chain continues into the CTE.

**Judgment call:** I mapped the name column to the IN-list columns, since those determine its values. If you'd rather treat it as a constant with no column lineage, that's a small change in the helper.

**Beyond the issue:** the passthrough `id` previously ended at a leaf. It now reaches `sales.id` too. I didn't see this in your report, but it's the same code path.

**Tests:** I added `test_unpivot_value_and_name_columns` and `test_unpivot_multi_value_columns` to `tests/test_lineage.py`. The full suite passes (1117 tests), and `ruff check` and `ruff format --check` are clean. I haven't committed anything.

## events
[assistant] I'll reproduce the bug first, then look at how lineage and scope handle `Unpivot`.
[tool_use Bash] {"command": "cat > /tmp/repro_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nnode = lineage(\"score\", sql, schema=schema, dialect=\"snowflake\")\nprint(node.to_htm
…[320 chars elided]…
.expression.sql(\"snowflake\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unpivot.py').read())\"; grep -n -i \"unpivot\\|pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -60", "description": "Reproduce UNPIVOT lineage bug and grep pivot handling"}
[tool_result] 'SCORE' | SRC.SCORE AS SCORE | downstream: ['SRC.SCORE']
'SRC.SCORE' | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC | downstream: []
---metric_name
'METRIC_NAME' | SRC.METRIC_NAME AS METRIC_NAME
'SRC.METRIC_NAME' | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
sqlglot/lineage.py:374:    pivots = scope.pivots
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
sqlglot/lineage.py:376:    if pivot:
sqlglot/lineage.p
…[4283 chars elided]…
/optimizer/scope.py:514:        return self._pivots
sqlglot/optimizer/scope.py:844:                # it is pivoted, because then we get back a new table and hence a new source.
sqlglot/optimizer/scope.py:845:                pivots = expression.args.get("pivots")
sqlglot/optimizer/scope.py:846:                if pivots:
sqlglot/optimizer/scope.py:847:                    sources[pivots[0].alias] = expression
sqlglot/optimizer/scope.py:984:                for key in ("joins", "laterals", "pivots"):
[assistant] The bug reproduces: `SCORE` resolves to a phantom `SRC.SCORE` with no downstream to `jan`/`feb`. The pivot branch in `lineage.py` explicitly excludes unpivots (`not pivots[0].unpivot`), so I'll read that section.
[tool_use Bash] {"command": "sed -n 340,480p sqlglot/lineage.py", "description": "Show pivot lineage handling in lineage.py"}
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
…[5353 chars elided]…
age
            # is unknown. This can happen if the definition of a source used in a query is not
            # passed into the `sources` map.
            col_expr = col_source or exp.Placeholder()
            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
            node.downstream.append(leaf)
            if on_node:
                on_node(leaf)

    if _cache is not None:
        _cache[cache_key] = node

    if on_node:
        on_node(node)

    return node
[assistant] The existing pivot branch only handles non-unpivot pivots. Before designing the fix I need the `Pivot` node layout for unpivots (value columns, name column, IN list).
[tool_use Bash] {"command": "grep -n \"class Pivot\" -A 40 sqlglot/expressions.py | head -60; grep -n \"def _parse_pivot\" -A 75 sqlglot/parser.py | grep -n \"unpivot\\|field\\|columns\\|expressions\\|output_columns\" ; grep -rn \"unpivot\" tests/test_lineage.py tests/test_optimizer.py | head; grep -n \"def output_columns\" -A 25 sqlglot/expressions.py | sed -n 1,40p", "description": "Inspect Pivot expression and unpivot parsing"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
11:5107-    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
18:5114-                expressions=self._match_text_seq("VALUE") and self._parse_csv(self._parse_column),
23:5119-    def _parse_simplified_pivot(self, is_unpivot: bool | None = None) -> exp.Pivot:
37:5133-        expressions = self._match(TokenType.ON) and self._parse_csv(_parse_on)
38:5134-        into = self._parse_unpivot_columns()
47:5143-            
…[1223 chars elided]…
p.In):
156:5252-                    pivot_field.set("this", _unpivot_target(pivot_field.this))
161:5257-        if not unpivot:
162:5258-            names = self._pivot_column_names(t.cast(list[exp.Expr], expressions))
164:5260-            columns: list[exp.Expr] = []
165:5261-            all_fields = []
166:5262-            for pivot_field in pivot.fields:
167:5263-                pivot_field_expressions = pivot_field.expressions
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"class Pivot(\" -A 30 sqlglot/expressions/*.py | head -45; sed -n 5160,5180p sqlglot/parser.py; sed -n 5256,5300p sqlglot/parser.py; grep -rn \"def _unpivot_target\" -A 12 sqlglot/parser.py; grep -rn \"def output_columns\" -A 22 sqlglot/expressions/*.py | head -40", "description": "Read Pivot class, unpivot parsing and output_columns"}
[tool_result] sqlglot/expressions/query.py:1747:class Pivot(Expression):
sqlglot/expressions/query.py-1748-    arg_types = {
sqlglot/expressions/query.py-1749-        "this": False,
sqlglot/expressions/query.py-1750-        "alias": False,
sqlglot/expressions/query.py-1751-        "expressions": False,
sqlglot/expressions/query.py-1752-        "fields": False,
sqlglot/expressions/query.py-1753-        "unpivot": False,
sqlglot/expressions/query.py-1754-        "using": False,
sqlglot/expressions/query.py-1755
…[6490 chars elided]…
y.py-1792-                expressions: value Identifier(s), or Tuple(Identifiers) for multi-value
sqlglot/expressions/query.py-1793-                fields:      [In(this=Identifier(name), expressions=[Column(a), Column(b)])]
sqlglot/expressions/query.py-1794-                             For literal-aliased entries (`a AS 'x'`) the IN expressions
sqlglot/expressions/query.py-1795-                             are wrapped in PivotAlias(this=Column, alias=Literal).
sqlglot/expressions/query.py-1796-
[assistant] The `Pivot` layout is clear: for an unpivot, `expressions` holds the value identifiers, `fields[0]` is the name column with the IN list, and `columns` is unused. Next I need to see how `scope.sources` registers a pivoted table, since that decides whether passthrough columns like `id` can reach the CTE.
[tool_use Bash] {"command": "sed -n 836,852p sqlglot/optimizer/scope.py; sed -n 1796,1830p sqlglot/expressions/query.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nsql='''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''\nschema={'sales': {'id':'int','jan':'int','feb':'int'}}\nfor col in ['id']:\n    n=lineage(col, sql, schema=schema, dialect='snowflake')\n    for x in n.walk(): print(col, repr(x.name), type(x.source).__name__, x.expression.sql('snowflake')[:60])\n\"", "description": "Check scope source registration and passthrough lineage"}
[tool_result]         if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless
                # it is pivoted, because then we get back a new table and hence a new source.
               
…[1395 chars elided]…
name for c in self.args.get("columns") or []]
            if not outputs:
                outputs = [c.alias_or_name for c in self.expressions]

        if not excluded or not outputs:
            return {}

        pre_rename = [c for c in pre_pivot_columns if c not in excluded] + outputs

        alias = self.args.get("alias")
        renames = alias.args.get("columns") if alias else None
id 'ID' Select SRC.ID AS ID
id 'SRC.ID' Table SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S
[assistant] Passthrough `id` also dead-ends at the pivoted `Table` rather than the CTE. Before I design the fix, I want to know whether the existing non-unpivot `PIVOT` branch can reach a CTE source at all, since `scope.sources[pivot.alias]` is overwritten with the `Table` node.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema={'sales': {'id':'int','cat':'varchar','amt':'int'}}\nsql='''WITH src AS (SELECT id, cat, amt FROM sales) SELECT * FROM src PIVOT (SUM(amt) FOR cat IN ('a','b'))'''\nfor col in ['A','ID']:\n    try:\n        n=lineage(col, s
…[225 chars elided]…
ITH src AS (SELECT id, cat, amt FROM sales) SELECT id, a FROM src PIVOT (SUM(amt) FOR cat IN ('a','b')) AS p(id, a, b)'''\nn=lineage('a', sql2, schema=schema, dialect='snowflake')\nfor x in n.walk(): print('a', repr(x.name), type(x.source).__name__, x.expression.sql('snowflake')[:70])\n\"; grep -n \"pivot\" tests/test_lineage.py | head", "description": "Check existing PIVOT lineage on CTE source"}
[tool_result] Unknown subquery scope: SELECT SALES.ID AS ID, SALES.CAT AS CAT, SALES.AMT AS AMT FROM SALES AS SALES
A ERR Cannot find column 'A' in query.
ID 'ID' Select _0.ID AS ID
ID 'SRC.ID' Select SALES.ID AS ID
ID 'SALES.ID' Table SALES AS SALES
---
a 'A' Select P.A AS A
a 'SRC.A' Select SELECT SALES.ID AS ID, SALES.CAT AS CAT, SALES.AMT AS AMT FROM SALES A
a 'SALES.AMT' Table SALES AS SALES
a 'SALES.CAT' Table SALES AS SALES
a 'SALES.ID' Table SALES AS SALES
607:    def test_pivot_without_alias(self) -> None:
622:    def test_pivot_with_alias(self) -> None:
637:    def test_pivot_with_cte(self) -> None:
656:    def test_pivot_with_implicit_column_of_pivoted_source(self) -> None:
670:    def test_pivot_with_implicit_column_of_pivoted_source_and_cte(self) -> None:
733:    def test_pivot_with_subquery(self) -> None:
[assistant] Existing tests cover pivots over CTEs (`test_pivot_with_cte`, `test_pivot_with_implicit_column_of_pivoted_source_and_cte`), so the pivot path must reach CTEs somehow. I'll read those tests to see the expected shape.
[tool_use Bash] {"command": "sed -n 607,700p tests/test_lineage.py", "description": "Read existing pivot lineage tests"}
[tool_result]     def test_pivot_without_alias(self) -> None:
        sql = """
        SELECT
            a as other_a
        FROM (select value,category from sample_data)
        PIVOT (
            sum(value)
            FOR category IN ('a', 'b')
        );
        """
        node = lineage("other_a", sql)

        self.assertEqual(node.downstream[0].name, "_0.value")
        self.assertEqual(node.downstream[0].downstream[0].name, "sample_data.value")

    def test_pivot_with_alias(self) -> None:
      
…[2021 chars elided]…
snowflake(self) -> None:
        lateral_flatten = """
        SELECT f.value:external_id::string AS external_id
        FROM database_name.schema_name.table_name AS raw,
        LATERAL FLATTEN(events) AS f
        """
        table_flatten = """
        SELECT f.value:external_id::string AS external_id
        FROM database_name.schema_name.table_name AS raw
        JOIN TABLE(FLATTEN(events)) AS f
        """

        lateral_node = lineage("external_id", lateral_flatten, dialect="snowflake")
[assistant] Those tests all use a real base table, where passthrough columns end at a `table.col` leaf. My failing case is different: the pivoted source is a CTE, and `scope.py:847` overwrites the CTE's `Scope` with the `Table` node. I need a way to recover the CTE scope for the unpivot's input, so I'll check what the scope exposes.
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def selected_sources\\|self.sources\\b\" sqlglot/optimizer/scope.py | head -30; sed -n 300,340p sqlglot/lineage.py", "description": "Find CTE source tracking in scope and lineage"}
[tool_result] 64:        cte_sources: Sources from CTES
109:        cte_sources: dict[str, exp.Table | Scope] | None = None,
113:        self.sources = sources or {}
115:        self.cte_sources = cte_sources or {}
116:        self.sources.update(self.lateral_sources)
117:        self.sources.update(self.cte_sources)
156:        cte_sources: dict[str, exp.Table | Scope] | None = None,
166:            cte_sources={**self.cte_sources, **(cte_sources or {})},
399:    def selected_sources(self) -> dict[str, tuple
…[1604 chars elided]…
*exp.UNWRAPPED_QUERIES):
        subquery_scope: Scope | None = subquery_scopes.get(id(subquery))
        if not subquery_scope:
            logger.warning(f"Unknown subquery scope: {subquery.sql(dialect=dialect)}")
            continue

        for name in subquery.named_selects:
            to_node(
                name,
                scope=subquery_scope,
                dialect=dialect,
                upstream=node,
                trim_selects=trim_selects,
                _cache=_cache,
[assistant] `scope.cte_sources` still holds the CTE `Scope` by name, so the unpivot input can be resolved from there. My plan:

- Stop excluding unpivots from the `pivot` selection. Keep the aggregate-column mapping for real pivots only.
- For an unpivot, map each output column to its input columns: value columns to the IN-list columns (per tuple position for multi-value), the name column to the unaliased IN-list columns, and passthrough columns to the same-named input column.
- Resolve those input columns through `scope.cte_sources` when the input is a CTE, so the chain continues into the CTE.

I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:", "new_string": "    pivot = pivots[0] if len(pivots) == 1 else None\n    if pivot and not pivot.unpivot:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            column_name = c.name\n            if any(column_name == pivot_column.name for pivot_column in pivot_columns):\n                downstream_columns.extend(pivot_column_mapping[column_name])\n            else:", "new_string": "            column_name = c.name\n            if pivot.unpivot:\n                downstream_columns.extend(_unpivot_source_columns(pivot, column_name))\n            elif any(column_name == pivot_column.name for pivot_column in pivot_columns):\n                downstream_columns.extend(pivot_column_mapping[column_name])\n            else:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            for downstream_column in downstream_columns:\n                table = downstream_column.table\n                col_source = scope.sources.get(table)\n                if isinstance(col_source, Scope):", "new_
…[129 chars elided]…
  unpivot_source = scope.cte_sources.get(pivot.parent.name) if pivot.unpivot else None\n            for downstream_column in downstream_columns:\n                table = downstream_column.table\n                col_source = (\n                    unpivot_source if isinstance(unpivot_source, Scope) else scope.sources.get(table)\n                )\n                if isinstance(col_source, Scope):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the helper. I'll find where the module's top-level functions sit so it goes in the same place.
[tool_use Bash] {"command": "grep -n \"^def \\|^class \\|^from\\|^import\" sqlglot/lineage.py", "description": "List top-level definitions in lineage.py"}
[tool_result] 1:from __future__ import annotations
3:import json
4:import logging
5:import typing as t
6:from dataclasses import dataclass, field
8:from sqlglot import Schema, exp, maybe_parse
9:from sqlglot.errors import SqlglotError
10:from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
11:from sqlglot.optimizer.scope import ScopeType
23:class Node:
81:def lineage(column: str | exp.Column, sql: str | exp.Expr, **kwargs: t.Any) -> Node: ...
85:def lineage(column: None, sql: str | exp.Expr, **kwargs: t.Any) -> dict[str, Node]: ...
88:def lineage(
191:def to_node(
488:class GraphHTML:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "def to_node(\n", "new_string": "def _unpivot_source_columns(pivot: exp.Pivot, column_name: str) -> list[exp.Column]:\n    \"\"\"Columns of the unpivoted relation that feed the UNPIVOT output column `column_name`.\"\"\"\
…[872 chars elided]…
  if field.this.name == column_name:\n            # Only unaliased IN entries take their value from a column; aliased ones are literals\n            return [exp.column(e.name, table=table) for e in field.expressions if isinstance(e, exp.Column)]\n\n    # Any other column is passed through from the unpivoted relation unchanged\n    return [exp.column(column_name, table=table)]\n\n\ndef to_node(\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll rerun the repro and a few edge cases: multi-value UNPIVOT, literal-aliased IN entries, a real-table source, and the name column.
[tool_use Bash] {"command": "cat > /tmp/check_unpivot.py <<'EOF'\nimport sys\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = {\n    \"issue\": (\"score\", '''WITH src AS (SELECT id, jan, feb FROM sales)\n        SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''),\n    \"name\": (\"metric_name\", '''WIT
…[1037 chars elided]…
        print(\"   \", repr(n.name), \"| source:\", type(n.source).__name__)\n    except Exception as e:\n        print(f\"== {name}: ERROR {type(e).__name__}: {e}\")\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/check_unpivot.py').read())\"", "description": "Run UNPIVOT lineage cases against the change"}
[tool_result] Unknown subquery scope: SELECT SALES.ID AS ID, JAN_A AS JAN_A, JAN_B AS JAN_B, FEB_A AS FEB_A, FEB_B AS FEB_B FROM SALES AS SALES
== issue: score
    'SCORE' | source: Select
    'SRC.JAN' | source: Select
    'SALES.JAN' | source: Table
    'SRC.FEB' | source: Select
    'SALES.FEB' | source: Table
== name: metric_name
    'METRIC_NAME' | source: Select
    'SRC.JAN' | source: Select
    'SALES.JAN' | source: Table
    'SRC.FEB' | source: Select
    'SALES.FEB' | source: Table
== passthrough: i
…[72 chars elided]…
 | source: Table
== aliased_literal: metric_name
    'METRIC_NAME' | source: Select
    'SRC.FEB' | source: Select
    'SALES.FEB' | source: Table
== real_table: score
    'SCORE' | source: Select
    'SALES.JAN' | source: Table
    'SALES.FEB' | source: Table
== multi_value: q2
    'Q2' | source: Select
    'U.Q2' | source: Select
    'FEB_B' | source: Placeholder
    'JAN_A' | source: Placeholder
    'FEB_A' | source: Placeholder
    'JAN_B' | source: Placeholder
    'SALES.ID' | source: Table
[assistant] The issue case now traces `score` → `SRC.JAN`/`SRC.FEB` → `sales.jan`/`sales.feb`, and the name and passthrough columns resolve too. The multi-value case selected `q2`, which doesn't exist in my test SQL, so I'll fix that case and rerun it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan_a': 'int', 'jan_b': 'int', 'feb_a': 'int', 'feb_b': 'int'}}\nsql='''WITH src AS (SELECT id, jan_a, jan_b, feb_a, feb_b FROM sales)\nSELECT id, m, a, b FROM src UNPIVOT ((a, b) FOR m IN ((jan_a, jan_b) AS 'J', (feb_a, feb_b) AS 'F')) AS u(id, m, a, b)'''\nfor col in ['a','b']:\n    n = lineage(col, sql, schema=schema, dialect='snowflake')\n    print('==', col)\n    for x in n.walk(): print('   ', repr(x.name))\n\"", "description": "Check multi-value UNPIVOT lineage"}
[tool_result] == a
    'A'
    'U.JAN_A'
    'SALES.JAN_A'
    'U.FEB_A'
    'SALES.FEB_A'
== b
    'B'
    'U.JAN_B'
    'SALES.JAN_B'
    'U.FEB_B'
    'SALES.FEB_B'
[assistant] Multi-value maps each value position to its own input column (`a` → `jan_a`/`feb_a`, `b` → `jan_b`/`feb_b`). Next I'll add a regression test alongside the existing pivot tests, then run the project's check command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(node.downstream[0].name, \"t.empid\")\n        self.assertEqual(node.downstream[0].reference_node_name, \"t\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"quarterly_sal
…[1473 chars elided]…
nt\", \"jan_b\": \"int\", \"feb_a\": \"int\", \"feb_b\": \"int\"}}\n\n        node = lineage(\"a\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"U.JAN_A\", \"U.FEB_A\"])\n\n        node = lineage(\"b\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"U.JAN_B\", \"U.FEB_B\"])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123602-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Run lineage test file"}
[tool_result] ........................................                                 [100%]
40 passed in 0.12s
[assistant] All 40 lineage tests pass. Now the project's full check command, and the linter, since my helper has a long line.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff --version && ruff check sqlglot/lineage.py tests/test_lineage.py && ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -15", "description": "Run full test suite and ruff checks"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 27%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[641 chars elided]…
6%]
.......................... [ 98%]
..................              [100%]
1117 passed, 18166 subtests passed in 57.11s
ruff 0.15.6
F402 Import `field` from line 6 shadowed by loop variable
   --> sqlglot/lineage.py:203:17
    |
202 |             sources = []
203 |             for field in in_fields:
    |                 ^^^^^
204 |                 for entry in field.expressions:
205 |                     entry = entry.this if isinstance(entry, exp.PivotAlias) else entry
    |

Found 1 error.
[assistant] The full suite passes (1117 tests). Ruff flags my loop variable `field`, which shadows the `dataclasses.field` import. I'll rename it and run the formatter check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport re\np='sqlglot/lineage.py'\ns=open(p).read()\nstart=s.index('def _unpivot_source_columns'); end=s.index('def to_node(')\nbody=s[start:end]\nbody=re.sub(r'\\bfield\\b(?!\\w)', 'in_field', body).replace('in_in_field','in_field')\nbody=body.replace('in_fields = [in_field for in_field in pivot.field
…[8 chars elided]…
nstance(in_field, exp.In)]','in_fields = [pivot_field for pivot_field in pivot.fields if isinstance(pivot_field, exp.In)]')\nopen(p,'w').write(s[:start]+body+s[end:])\n\" && sed -n 191,225p sqlglot/lineage.py && ruff check sqlglot/lineage.py tests/test_lineage.py && ruff format --check sqlglot/lineage.py tests/test_lineage.py", "description": "Rename shadowing loop variable and lint/format check"}
[tool_result ERROR] Exit code 1
def _unpivot_source_columns(pivot: exp.Pivot, column_name: str) -> list[exp.Column]:
    """Columns of the unpivoted relation that feed the UNPIVOT output column `column_name`."""
    in_fields = [pivot_field for pivot_field in pivot.fields if isinstance(pivot_field, exp.In)]
    table = pivot.alias_or_name

    for value in pivot.expressions:
        values = value.expressions if isinstance(value, exp.Tuple) else [value]
        for index, value_name in enumerate(values):
          
…[687 chars elided]…
ed ones are literals
            return [exp.column(e.name, table=table) for e in in_field.expressions if isinstance(e, exp.Column)]

    # Any other column is passed through from the unpivoted relation unchanged
    return [exp.column(column_name, table=table)]


def to_node(
    column: str | int,
    scope: Scope,
    dialect: DialectType,
    scope_name: str | None = None,
All checks passed!
Would reformat: sqlglot/lineage.py
Would reformat: tests/test_lineage.py
2 files would be reformatted
[assistant] Ruff lint passes. The formatter wants to reformat both files. I'll check whether the files were already clean at HEAD before running the formatter, so I don't pull unrelated lines into the diff.
[tool_use Bash] {"command": "git show HEAD:sqlglot/lineage.py | ruff format --check --stdin-filename sqlglot/lineage.py - ; echo \"rc=$?\"; git show HEAD:tests/test_lineage.py | ruff format --check --stdin-filename tests/test_lineage.py - ; echo \"rc=$?\"; ruff format --diff sqlglot/lineage.py tests/test_lineage.py 2>&1 | head -60", "description": "Check formatter status at HEAD and diff for my files"}
[tool_result] rc=0
rc=0
--- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -212,7 +212,11 @@
     for in_field in in_fields:
         if in_field.this.name == column_name:
             # Only unaliased IN entries take their value from a column; aliased ones are literals
-            return [exp.column(e.name, table=table) for e in in_field.expressions if isinstance(e, exp.Column)]
+            return [
+                exp.column(e.name, table=table)
+                for e in in_field.expressions
+             
…[834 chars elided]…
an_a, jan_b) AS 'J', (feb_a, feb_b) AS 'F')) AS u(id, m, a, b)
         """
-        schema = {"sales": {"id": "int", "jan_a": "int", "jan_b": "int", "feb_a": "int", "feb_b": "int"}}
+        schema = {
+            "sales": {"id": "int", "jan_a": "int", "jan_b": "int", "feb_a": "int", "feb_b": "int"}
+        }
 
         node = lineage("a", sql, schema=schema, dialect="snowflake")
         self.assertEqual([d.name for d in node.downstream], ["U.JAN_A", "U.FEB_A"])

2 files would be reformatted
[assistant] HEAD was clean and the diff only touches my lines, so I'll apply the formatter and rerun lint, format, and the full suite.
[tool_use Bash] {"command": "ruff format sqlglot/lineage.py tests/test_lineage.py && ruff check sqlglot/lineage.py tests/test_lineage.py && ruff format --check sqlglot/lineage.py tests/test_lineage.py && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2 && <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unpivot.py').read())\" | head -3 && git status --short", "description": "Format, lint, run full suite, and check status"}
[tool_result] 2 files reformatted
All checks passed!
2 files already formatted
..................              [100%]
1117 passed, 18166 subtests passed in 55.58s

'SCORE' | SRC.SCORE AS SCORE | downstream: ['SRC.JAN', 'SRC.FEB']
'SRC.JAN' | SALES.JAN AS JAN | downstream: ['SALES.JAN']
 M sqlglot/lineage.py
 M tests/test_lineage.py
[This command modified 2 files you've previously read: tests/test_lineage.py, sqlglot/lineage.py. Call Read before editing.]
[assistant] UNPIVOT lineage now reaches the source columns. In your example, `score` traces to `SRC.JAN` and `SRC.FEB`, then to `sales.jan` and `sales.feb`. Before, it returned a phantom `SRC.SCORE` with no upstream.

**Cause:** `sqlglot/lineage.py` only handled pivots when `not pivot.unpivot`, so UNPIVOT columns fell through to a leaf on the input relation. Also, a pivoted CTE is overwritten in `scope.sources` by its `Table` node, so the CTE scope was never reachable from there.

**Fix (`sqlglot/lineage.py`):**
- The pivot aggregate mapping now applies only to real PIVOTs.
- A new helper, `_unpivot_sourc
…[550 chars elided]…
all:** I mapped the name column to the IN-list columns, since those determine its values. If you'd rather treat it as a constant with no column lineage, that's a small change in the helper.

**Beyond the issue:** the passthrough `id` previously ended at a leaf. It now reaches `sales.id` too. I didn't see this in your report, but it's the same code path.

**Tests:** I added `test_unpivot_value_and_name_columns` and `test_unpivot_multi_value_columns` to `tests/test_lineage.py`. The full suite passes (1117 tests), and `ruff check` and `ruff format --check` are clean. I haven't committed anything.
