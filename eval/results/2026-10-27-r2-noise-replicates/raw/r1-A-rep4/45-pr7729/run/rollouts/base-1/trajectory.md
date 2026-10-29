# trajectory base-1

final message:
`lineage()` now traces UNPIVOT output columns back to the unpivoted source columns. Your example gives `score` → `SRC.JAN`, `SRC.FEB` → `SALES.JAN`, `SALES.FEB` through the CTE, instead of a phantom `SRC.SCORE` on the input.

**Cause:** `scope.pivots` includes UNPIVOT nodes, but `lineage.py` explicitly excluded them from the pivot branch. The UNPIVOT output columns fell through to the leaf case and returned the pivoted table itself.

**Changes**
- `sqlglot/lineage.py`: UNPIVOT now goes through the existing pivot branch. A new helper, `_unpivot_downstream_columns`, maps:
  - value columns and the name column to the columns in the IN list;
  - any other column (e.g. `id`) to the same column on the unpivoted source.
- `sqlglot/lineage.py`: a pivoted CTE reference is resolved back to its CTE scope. This is shared with PIVOT, so PIVOT over a CTE now also resolves through the CTE rather than stopping at the pivoted table. Existing tests still pass.
- `tests/test_lineage.py`: added `test_unpivot_with_cte`, covering `score`, `metric_name` and `id`. No existing tests were changed.

**Choices I made**
- The name column (`metric_name`) traces to the IN-list columns (`jan`, `feb`), since its values are the names of those columns. It does not trace to a literal or to a phantom column. If you'd rather it stop at the UNPIVOT node, say so.
- For multi-value UNPIVOT (`(a, b) FOR ... IN ((x, y), ...)`), each value column maps to all IN-list columns. That is a superset of the exact mapping, not a precise one.

**Verification**
- `tests/test_lineage.py`: 39 passed.
- Related files (lineage, optimizer, snowflake, duckdb): 257 passed.
- Full `tests/`: 1116 passed, before a cosmetic `ruff format` reflow of one condition. I did not get a clean full run after that reflow. The machine was under load, and a full run was taking over 15 minutes. `test_max_nodes`, which was the last test it stalled on, passes alone.
- `ruff check` passes on both changed files.

I did not commit anything.

## events
[tool_use Bash] {"command": "cat > /tmp/repro_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nfor col in [\"score\", \"metric_name\", \"id\"]:\n    node = lineage(col, sql, schema=s
…[189 chars elided]…
e.__class__.__name__)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/repro_unpivot.py').read())\"; grep -n \"Unpivot\\|unpivot\\|Pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -50", "description": "Reproduce UNPIVOT lineage issue and grep pivot handling"}
[tool_result] score
   SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.SCORE AS SCORE FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
   SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
metric_name
   METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.METRIC_NAME AS METRIC_NAME FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB))
…[441 chars elided]…
unpivot else None
sqlglot/optimizer/qualify_columns.py:614:            if scope.pivots and not column.find_ancestor(exp.Pivot):
sqlglot/optimizer/qualify_columns.py:615:                # If the column is under the Pivot expression, we need to qualify it
sqlglot/optimizer/qualify_columns.py:781:    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))
sqlglot/optimizer/scope.py:98:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:508:    def pivots(self) -> list[exp.Pivot]:
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/lineage.py | head -5; sed -n 330,430p sqlglot/lineage.py; grep -n \"pivot\\|Pivot\" sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -40", "description": "Read pivot handling in lineage and scope code"}
[tool_result] from __future__ import annotations

import json
import logging
import typing as t
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
                _scope_meta=_scope_meta,
     
…[6503 chars elided]…
pe.pivots, 0))
sqlglot/optimizer/qualify_columns.py:844:            if pivot:
sqlglot/optimizer/qualify_columns.py:845:                pivot_columns = pivot.output_columns(columns) or pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:847:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:849:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:850:                        for name in pivot_columns
[tool_use Bash] {"command": "sed -n 430,470p sqlglot/lineage.py; grep -n \"def output_columns\" -A25 sqlglot/expressions.py | sed -n 1,200p | grep -A25 -i \"pivot\" | head -60; grep -n \"class Pivot\" -A40 sqlglot/expressions.py | head -60", "description": "Read rest of pivot lineage branch and Pivot class"}
[tool_result]                 pivot_parent = pivot.parent
                downstream_columns.append(
                    exp.column(c.this, table=pivot_parent.alias_or_name if pivot_parent else "")
                )

            for downstream_column in downstream_columns:
                table = downstream_column.table
                col_source = scope.sources.get(table)
                if isinstance(col_source, Scope):
                    to_node(
                        downstream_column.name,
           
…[1119 chars elided]…
s column's lineage
            # is unknown. This can happen if the definition of a source used in a query is not
            # passed into the `sources` map.
            col_expr = col_source or exp.Placeholder()
            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
            node.downstream.append(leaf)
            if on_node:
ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"class Pivot(\" -A30 sqlglot/expressions/ | head -45; grep -rn \"def output_columns\" -A22 sqlglot/expressions/ | grep -B2 -A22 \"unpivot\\|Pivot\" | head -60", "description": "Locate Pivot class and output_columns logic"}
[tool_result] sqlglot/expressions/query.py:1747:class Pivot(Expression):
sqlglot/expressions/query.py-1748-    arg_types = {
sqlglot/expressions/query.py-1749-        "this": False,
sqlglot/expressions/query.py-1750-        "alias": False,
sqlglot/expressions/query.py-1751-        "expressions": False,
sqlglot/expressions/query.py-1752-        "fields": False,
sqlglot/expressions/query.py-1753-        "unpivot": False,
sqlglot/expressions/query.py-1754-        "using": False,
sqlglot/expressions/query.py-1755
…[2632 chars elided]…
y.py-1792-                expressions: value Identifier(s), or Tuple(Identifiers) for multi-value
sqlglot/expressions/query.py-1793-                fields:      [In(this=Identifier(name), expressions=[Column(a), Column(b)])]
sqlglot/expressions/query.py-1794-                             For literal-aliased entries (`a AS 'x'`) the IN expressions
sqlglot/expressions/query.py-1795-                             are wrapped in PivotAlias(this=Column, alias=Literal).
sqlglot/expressions/query.py-1796-
[tool_use Bash] {"command": "sed -n 1796,1860p sqlglot/expressions/query.py; cat > /tmp/probe.py <<'EOF'\nfrom sqlglot import parse_one, exp\nsql = \"WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))\"\nq = parse_one(sql, read=\"snowflake\")\np = q.find(exp.Pivot)\nprint(repr(p)[:800])\nprint(list(p.output_columns([\"id\",\"jan\",\"feb\"])))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe.py').read())\"", "description": "Read UNPIVOT output_columns and inspect AST shape"}
[tool_result]         Args:
            pre_pivot_columns: Columns visible to the operator before it runs
                (e.g. the source table or subquery's projections).
        """
        if self.unpivot:
            excluded: set[str] = set()
            name_columns: list[Identifier] = []
            for field in self.fields:
                if not isinstance(field, In):
                    continue
                if isinstance(field.this, Identifier):
                    name_columns.append(field.thi
…[1659 chars elided]…
      "spec": False,
        "alias": False,
        "over": False,
        "first": False,
    }


class WindowSpec(Expression):
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
[tool_use Bash] {"command": "sed -n 825,855p sqlglot/optimizer/scope.py; grep -n \"pivot\\|PIVOT\\|UNPIVOT\" tests/test_lineage.py | head -30", "description": "Read scope source registration for pivots and lineage tests"}
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
…[846 chars elided]…
       PIVOT (
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
[tool_use Bash] {"command": "sed -n 600,780p tests/test_lineage.py", "description": "Read existing pivot lineage tests"}
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
…[5108 chars elided]…
24-10")
        self.assertEqual(node.downstream[0].downstream[0].name, "_0.loan_id")
        self.assertEqual(node.downstream[0].downstream[0].downstream[0].name, "loan_ledger.loan_id")

    def test_copy_flag(self) -> None:
        schema = {
            "x": {
                "a": "int",
            },
        }

        query = sqlglot.parse_one("SELECT a FROM z")
        sources = {
            "y": sqlglot.parse_one("SELECT * FROM x"),
            "z": sqlglot.parse_one("SELECT * FROM y"),
[tool_use Bash] {"command": "cat > /tmp/probe2.py <<'EOF'\nfrom sqlglot import parse_one, exp\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nsql = \"WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))\"\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nq = qua
…[315 chars elided]…
or k, v in root.sources.items()})\nfor s in root.traverse():\n    print(s.scope_type, list(s.sources.keys()), {k: type(v).__name__ for k, v in s.sources.items()})\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe2.py').read())\"", "description": "Probe qualified AST and scope sources for UNPIVOT query"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "<string>", line 9, in <module>
AttributeError: 'NoneType' object has no attribute 'alias_or_name'
WITH "SRC" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "SRC"."ID" AS "ID", "SRC"."METRIC_NAME" AS "METRIC_NAME", "SRC"."SCORE" AS "SCORE" FROM "SRC" AS "SRC" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SRC"
[tool_use Bash] {"command": "sed -i 's/^p = q.find(exp.Pivot)/p = q.find(exp.Pivot); print(\"parent:\", type(p.parent).__name__, p.parent.alias_or_name)/; s/^print(\"this:\".*$//' /tmp/probe2.py && <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe2.py').read())\"", "description": "Re-run probe with corrected pivot parent lookup"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/probe2.py
": extra characters at the end of p command
[tool_use Bash] {"command": "cat > /tmp/probe2.py <<'EOF'\nfrom sqlglot import parse_one, exp\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nsql = \"WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))\"\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nq = qua
…[160 chars elided]…
t.alias_or_name, \"| pivot alias:\", p.alias_or_name)\nroot = build_scope(q)\nfor s in root.traverse():\n    print(s.scope_type, {k: type(v).__name__ for k, v in s.sources.items()})\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe2.py').read())\"", "description": "Probe pivot parent and scope sources"}
[tool_result] pivot parent: Table SRC | pivot alias: SRC
ScopeType.CTE {'SALES': 'Table'}
ScopeType.ROOT {'SRC': 'Table'}
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def selected_sources\" sqlglot/optimizer/scope.py | head -20; grep -n \"def to_node\" -A20 sqlglot/lineage.py | head -40", "description": "Check Scope CTE source attributes and to_node signature"}
[tool_result] 64:        cte_sources: Sources from CTES
109:        cte_sources: dict[str, exp.Table | Scope] | None = None,
115:        self.cte_sources = cte_sources or {}
117:        self.sources.update(self.cte_sources)
156:        cte_sources: dict[str, exp.Table | Scope] | None = None,
166:            cte_sources={**self.cte_sources, **(cte_sources or {})},
399:    def selected_sources(self) -> dict[str, tuple[exp.Selectable, exp.Table | Scope]]:
698:            yield from _traverse_scope(Scope(ddl_expr
…[518 chars elided]…
 _cache: dict[tuple, Node] | None = None,
201-    _scope_meta: dict[int, tuple[bool, dict[str, exp.Expr]]] | None = None,
202-    on_node: t.Callable[[Node], None] | None = None,
203-) -> Node:
204-    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)
205-
206-    if _cache is not None and cache_key in _cache:
207-        cached_node = _cache[cache_key]
208-        if upstream:
209-            upstream.downstream.append(cached_node)
210-        return cached_node
211-
[assistant] Root cause is clear: `scope.pivots` excludes UNPIVOT (`not pivots[0].unpivot`), so the UNPIVOT falls through to the leaf branch and returns the pivoted table itself. I'll route UNPIVOT through the existing pivot branch, with its own downstream mapping.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:", "new_string": "    pivot = pivots[0] if len(pivots) == 1 else None\n    if pivot and not pivot.unpivot:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            column_name = c.name\n            if any(column_name == pivot_column.name for pivot_column in pivot_columns):", "new_string": "            column_name = c.name\n            if pivot.unpivot:\n                downstream_columns.extend(_unpivot_downstream_columns(pivot, column_name))\n            elif any(column_name == pivot_column.name for pivot_column in pivot_columns):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "                col_source = scope.sources.get(table)\n                if isinstance(col_source, Scope):\n                    to_node(\n                        downstream_column.name,", "new_string": "                co
…[67 chars elided]…
col_source, exp.Table) and not col_source.db and col_source.name in scope.cte_sources:\n                    # A pivoted CTE reference is registered as the pivoted table, so resolve it back to the CTE\n                    col_source = scope.cte_sources[col_source.name]\n                if isinstance(col_source, Scope):\n                    to_node(\n                        downstream_column.name,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "def to_node(\n    column: str | int,", "new_string": "def _unpivot_downstream_columns(pivot: exp.Pivot, column_name: str) -> list[exp.Column]:\n    \"\"\"Returns the pre-unpivot columns that the given output column of a
…[547 chars elided]…
elds if isinstance(field.this, exp.Identifier)}\n    if column_name in value_names | name_names:\n        return [\n            exp.column(column.name, table=source)\n            for field in in_fields\n            for e in field.expressions\n            for column in e.find_all(exp.Column)\n        ]\n\n    return [exp.column(column_name, table=source)]\n\n\ndef to_node(\n    column: str | int,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ndef show(n, d=0):\n    print(\"  \" * d, n.name, \"|\", n.source.sql(dialect=\"snowflake\")[:70])\n    for c in n.downstream: show(c, d + 1)\nfor col in [\"score\", \"metric_name\", \"id\"]:\n    print(col); show(lineage(col, sql, schema=schema, dialect=\"snowflake\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro2.py').read())\"", "description": "Re-run UNPIVOT lineage repro with the fix"}
[tool_result] score
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
   SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
     SALES.FEB | SALES AS SALES
metric_name
 METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
     SALES.JAN | SALES AS SALES
   SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
     SALES.FEB | SALES AS SALES
id
 ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
   SRC.ID | SELECT SALES.ID AS ID FROM SALES AS SALES
     SALES.ID | SALES AS SALES
[assistant] The fix traces `score` and `metric_name` to `jan`/`feb` through the CTE, and `id` now reaches `sales.id` instead of a phantom. Next I'll add regression tests and run the project's test command.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "    def test_copy_flag(self) -> None:", "new_string": "    def test_unpivot_with_cte(self) -> None:\n        schema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\n\n        sql = \"\"\"\n      
…[531 chars elided]…
ame\", sql, dialect=\"snowflake\", schema=schema)\n        self.assertEqual([d.name for d in node.downstream], [\"SRC.JAN\", \"SRC.FEB\"])\n\n        node = lineage(\"id\", sql, dialect=\"snowflake\", schema=schema)\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\n\n    def test_copy_flag(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run lineage tests and full test suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: btqtgr5u0). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/btqtgr5u0.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -15", "description": "Run lineage test file only"}
[tool_result] .......................................                                  [100%]
39 passed in 0.08s
[assistant] Lineage tests pass (39, including the new one). The full suite is still running in the background, so I'll check its output.
[tool_use Bash] {"command": "sleep 100; tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/btqtgr5u0.output", "description": "Wait and check full test suite output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/btqtgr5u0.output. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Bash] {"command": "timeout 600000 <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no -x tests/ 2>&1 | tail -15", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] Command did not complete within its 600s timeout and was moved to the background (ID: b2eqphjnx). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/b2eqphjnx.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite is slow and the background run was stopped by its time limit. I'll run the linter on the changed files while I check the second background run.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -I -m ruff check sqlglot/lineage.py tests/test_lineage.py && <work>/env-sqlglot/bin/python -I -m ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -8; tail -3 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/b2eqphjnx.output", "description": "Lint and format-check changed files; check suite output"}
[tool_result] All checks passed!
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m ruff format --diff sqlglot/lineage.py 2>&1 | head -30", "description": "Show formatting diff for lineage.py"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -461,7 +461,11 @@
             for downstream_column in downstream_columns:
                 table = downstream_column.table
                 col_source = scope.sources.get(table)
-                if isinstance(col_source, exp.Table) and not col_source.db and col_source.name in scope.cte_sources:
+                if (
+                    isinstance(col_source, exp.Table)
+                    and not col_source.db
+                    and col_source.name in scope.cte_sources
+                ):
                     # A pivoted CTE reference is registered as the pivoted table, so resolve it back to the CTE
                     col_source = scope.cte_sources[col_source.name]
                 if isinstance(col_source, Scope):

1 file would be reformatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m ruff format sqlglot/lineage.py && <work>/env-sqlglot/bin/python -I -m ruff check sqlglot/lineage.py tests/test_lineage.py && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py tests/test_optimizer.py tests/dialects/test_snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -4", "description": "Format lineage.py, lint, and run related test files"}
[tool_result] 1 file reformatted
All checks passed!
....................... [ 36%]
.......................... [ 47%]
........................................................................................................................................   [100%]
257 passed, 6077 subtests passed in 14.84s
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] That notice is from my own `ruff format` run, which only reflowed a line. Related tests pass (257). Now I'll run the full suite in the background with a longer timeout.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/ > /tmp/full_suite.log 2>&1; echo \"exit=$?\" >> /tmp/full_suite.log", "description": "Run full test suite, logging to file", "timeout": 1800000, "run_in_background": true}
[tool_result] Command running in background with ID: b1upoxdnc. Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/b1upoxdnc.output. You will be notified when it completes. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "tail -4 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/b2eqphjnx.output", "description": "Check output of earlier full suite run"}
[tool_result] .................               [100%]
1116 passed, 18166 subtests passed in 62.79s (0:01:02)

[exited with code 0]
[tool_use Bash] {"command": "cat /tmp/full_suite.log | tail -3; cd ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1 && git status --short && git diff --stat", "description": "Check full suite log and git diff stat"}
[tool_result] ............................ [ 51%]
................................................................................................................................................... [ 64%]
................................................... M sqlglot/lineage.py
 M tests/test_lineage.py
 sqlglot/lineage.py    | 39 ++++++++++++++++++++++++++++++++++++---
 tests/test_lineage.py | 21 +++++++++++++++++++++
 2 files changed, 57 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "sleep 45; tail -3 /tmp/full_suite.log", "description": "Wait briefly then read full suite log"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 45 followed by: tail -3 /tmp/full_suite.log. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Bash] {"command": "tail -3 /tmp/full_suite.log", "description": "Read full suite log tail"}
[tool_result] ............................ [ 51%]
................................................................................................................................................... [ 64%]
...................................................
[tool_use Bash] {"command": "until grep -q \"^exit=\" /tmp/full_suite.log; do sleep 3; done; tail -3 /tmp/full_suite.log", "description": "Wait for full suite to finish and show result", "timeout": 400000}
[tool_result] Command did not complete within its 400s timeout and was moved to the background (ID: bi6dfsudk). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/bi6dfsudk.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "tail -c 600 /tmp/full_suite.log; echo; ps aux | grep -c \"pytest\" ", "description": "Inspect full suite progress and running processes"}
[tool_result] ........................................ [ 24%]
........................... [ 27%]
........................................ [ 30%]
........................................................................................ [ 38%]
...................................................................................................................... [ 49%]
............................ [ 51%]
................................................................................................................................................... [ 64%]
........................................................
6
[tool_use Bash] {"command": "ps -eo pid,etime,pcpu,command | grep -i \"pytest\" | grep -v grep | cut -c1-220", "description": "List running pytest processes"}
[tool_result] 34204 05-09:43:49   0.0 /bin/zsh -c source ~/.claude/shell-snapshots/snapshot-zsh-1792775860252-0z2ieb.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin un
34207 05-09:43:49  44.9 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=
50483       15:26   0.0 /bin/zsh -c source ~/.claude/shell-snapshots/snapshot-zsh-1793238356943-a6t1hc.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin un
50487       15:26  49.8 <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/
[assistant] My full-suite run has been going for 15 minutes, while the earlier identical run finished in 63s. I'll stop it and rerun verbosely to find where it stalls.
[tool_use Bash] {"command": "kill 50487 2>/dev/null; cd ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1 && <work>/env-sqlglot/bin/python -I -m pytest -v -p no:cacheprovider --color=no tests/ > /tmp/full_suite_v.log 2>&1 & sleep 1; echo started", "description": "Kill stalled run and restart verbose suite in background"}
[tool_result] started
[tool_use Bash] {"command": "tail -3 /tmp/full_suite.log; tail -3 /tmp/full_suite_v.log", "description": "Check results of both suite logs"}
[tool_result] ............................ [ 51%]
................................................................................................................................................... [ 64%]
.................................................................................................................................................................................................................................exit=143
tests/dialects/test_tsql.py::TestTSQL::test_string 
tests/dialects/test_tsql.py::TestTSQL::test_string PASSED                [ 64%]
tests/dialects/test_tsql.py::TestTSQL::test_system_time
[assistant] The first log's `exit=143` is from my own kill, not a test result. The verbose run is slow on `test_tsql` rather than hung, so I'll wait for it to finish.
[tool_use Bash] {"command": "until grep -qE \"passed|failed|error\" /tmp/full_suite_v.log && grep -qE \"^=+|[0-9]+ passed\" /tmp/full_suite_v.log; do sleep 5; done; tail -3 /tmp/full_suite_v.log", "description": "Wait for verbose suite to finish and show summary", "timeout": 500000}
[tool_result] tests/test_executor.py::TestExecutor::test_execute_subqueries PASSED     [ 69%]
tests/test_executor.py::TestExecutor::test_execute_tables PASSED         [ 69%]
tests/test_executor.py::TestExecutor::test_execute_tpcds
[tool_use Bash] {"command": "until grep -qE \"[0-9]+ passed\" /tmp/full_suite_v.log; do sleep 5; done; tail -2 /tmp/full_suite_v.log", "description": "Wait for pytest summary line in verbose log", "timeout": 590000}
[tool_result] Command did not complete within its 590s timeout and was moved to the background (ID: bib9i8hh0). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-034552-lineage-sqlglot-lineage-lineage-base-1/564faff3-1010-45c9-8968-a4ba77829647/tasks/bib9i8hh0.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "tail -c 400 /tmp/full_suite_v.log; echo; ps -eo pid,etime,pcpu,command | grep \"pytest\" | grep -v grep | grep sqlglot | cut -c1-120", "description": "Check verbose suite progress and process state"}
[tool_result] n PASSED                [ 90%]
tests/test_parser.py::TestParser::test_expression PASSED                 [ 90%]
tests/test_parser.py::TestParser::test_float PASSED                      [ 90%]
tests/test_parser.py::TestParser::test_identify PASSED                   [ 90%]
tests/test_parser.py::TestParser::test_lambda_struct PASSED              [ 90%]
tests/test_parser.py::TestParser::test_max_nodes 
51106       14:46  99.4 <work>/env-sqlglot/bin/python -I -m pytest -v -p no:
[assistant] The run is now stuck at `tests/test_parser.py::test_max_nodes`, which doesn't touch lineage code. I'll run that test alone to see whether it is slow or hung.
[tool_use Bash] {"command": "kill 51106 2>/dev/null; cd ~/.cache/lithify/work/repo-d5521a213087/20261029-034552-lineage-sqlglot-lineage-lineage/base-1 && grep -n \"def test_max_nodes\" -A12 tests/test_parser.py; <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -3", "description": "Inspect and run test_max_nodes in isolation", "timeout": 300000}
[tool_result] 1117:    def test_max_nodes(self):
1118-        self.assertIsInstance(parse_one("SELECT 1", max_nodes=1_000_000), exp.Select)
1119-
1120-        cols = [f"col{i}" for i in range(500)]
1121-        sql = f"SELECT {','.join(cols)} FROM t"
1122-        self.assertIsInstance(parse_one(sql, max_nodes=1_000_000), exp.Select)
1123-
1124-        width = 10000
1125-        depth = 100
1126-        expr = "x" + "=x" * depth
1127-        cols = [expr for _ in range(width)]
1128-        sql = f"SELECT {','.join(cols)}"
1129-
.                                                                        [100%]
1 passed, 65 deselected in 11.62s
[assistant] `test_max_nodes` passes in isolation (11.6s), so the stall was machine load, not a hang. The full suite passed earlier (1116 passed) before a cosmetic reformat. I'll review the final diff.
[tool_use Bash] {"command": "git diff sqlglot/lineage.py", "description": "Show final lineage.py diff"}
[tool_result] diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 4b84f7ba7..50b76e9a4 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -188,6 +188,30 @@ def lineage(
     return result
 
 
+def _unpivot_downstream_columns(pivot: exp.Pivot, column_name: str) -> list[exp.Column]:
+    """Returns the pre-unpivot columns that the given output column of an UNPIVOT is derived from."""
+    source = pivot.parent.alias_or_name
+    in_fields = [field for field in pivot.fields if isinstance(field, e
…[2177 chars elided]…
    if (
+                    isinstance(col_source, exp.Table)
+                    and not col_source.db
+                    and col_source.name in scope.cte_sources
+                ):
+                    # A pivoted CTE reference is registered as the pivoted table, so resolve it back to the CTE
+                    col_source = scope.cte_sources[col_source.name]
                 if isinstance(col_source, Scope):
                     to_node(
                         downstream_column.name,
[assistant] `lineage()` now traces UNPIVOT output columns back to the unpivoted source columns. Your example gives `score` → `SRC.JAN`, `SRC.FEB` → `SALES.JAN`, `SALES.FEB` through the CTE, instead of a phantom `SRC.SCORE` on the input.

**Cause:** `scope.pivots` includes UNPIVOT nodes, but `lineage.py` explicitly excluded them from the pivot branch. The UNPIVOT output columns fell through to the leaf case and returned the pivoted table itself.

**Changes**
- `sqlglot/lineage.py`: UNPIVOT now goes through the existing pivot branch. A new helper, `_unpivot_downstream_columns`, maps:
  - value columns and t
…[792 chars elided]…
((x, y), ...)`), each value column maps to all IN-list columns. That is a superset of the exact mapping, not a precise one.

**Verification**
- `tests/test_lineage.py`: 39 passed.
- Related files (lineage, optimizer, snowflake, duckdb): 257 passed.
- Full `tests/`: 1116 passed, before a cosmetic `ruff format` reflow of one condition. I did not get a clean full run after that reflow. The machine was under load, and a full run was taking over 15 minutes. `test_max_nodes`, which was the last test it stalled on, passes alone.
- `ruff check` passes on both changed files.

I did not commit anything.
