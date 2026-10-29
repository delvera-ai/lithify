# trajectory base-1

final message:
UNPIVOT lineage now reaches the unpivoted source columns. The value column `score` resolves to `src.jan` and `src.feb` instead of the phantom `SRC.SCORE`, and the name column `metric_name` also resolves to the IN-list columns.

**Change** (`sqlglot/lineage.py`): the pivot branch skipped UNPIVOT entirely (`not pivots[0].unpivot`), so its columns fell through to the leaf case and produced the phantom. UNPIVOT now takes the same branch as PIVOT, with two differences:
- The value and name columns map to the columns listed in the `IN (...)` clause.
- Any other column from the source, such as `id`, is passed through to the source table as PIVOT already does for implicit columns.

**Tests** (`tests/test_lineage.py`): I added `test_unpivot_value_column` and `test_unpivot_name_column_and_implicit_column`. The lineage module passes (40/40), the full suite passes (1117 passed), and ruff check and format are clean. I have not committed.

**Choices to check:**
- I mapped the name column to the IN-list columns, since its values are those column names. If you'd rather it have no upstream columns, that's a small change.
- For a CTE source, the leaves stop at `src.jan` and `src.feb` rather than continuing to `sales.jan`. The scope builder deliberately keeps a pivoted CTE reference as a table, and PIVOT behaves the same way. Subquery sources do trace all the way down. Tracing through a CTE would mean changing how scope handles pivoted references, so I left that out.

## events
[tool_use Bash] {"command": "git status --short | head && cat sqlglot/lineage.py | head -150 && grep -n -i \"pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -60", "description": "Check status and read lineage module with pivot references"}
[tool_result] okfrom __future__ import annotations

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
    from 
…[9166 chars elided]…
pe.pivots, 0))
sqlglot/optimizer/qualify_columns.py:844:            if pivot:
sqlglot/optimizer/qualify_columns.py:845:                pivot_columns = pivot.output_columns(columns) or pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:847:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:849:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:850:                        for name in pivot_columns
[tool_use Bash] {"command": "sed -n 340,480p sqlglot/lineage.py", "description": "Read pivot lineage handling section"}
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
[assistant] Let me reproduce the bug and inspect how the UNPIVOT node is structured.
[tool_use Bash] {"command": "cat > /tmp/repro_unpivot.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one, exp\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nnode = linea
…[47 chars elided]…
wflake\")\nfor n in node.walk():\n    print(repr(n.name), type(n.expression).__name__, n.source.sql(dialect=\"snowflake\")[:80] if n.source else None)\nprint(\"---\")\np = parse_one(sql, read=\"snowflake\").find(exp.Pivot)\nprint(repr(p))\nEOF\npython -I /tmp/repro_unpivot.py 2>&1 | tail -40; ls .lithify/harness/scripts/ 2>/dev/null", "description": "Reproduce UNPIVOT lineage issue with a script"}
[tool_result] 'SCORE' Alias WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
'SRC.SCORE' Table SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
---
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
probe_parse.py
[assistant] The bug reproduces: the value column yields a phantom `SRC.SCORE` leaf. The existing pivot logic skips UNPIVOT entirely (`not pivots[0].unpivot`). Before editing, I'll check the UNPIVOT AST shape and whether the IN-list columns are qualified.
[tool_use Bash] {"command": "cat > /tmp/probe_unpivot2.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import exp\nfrom sqlglot.optimizer import qualify\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"fe
…[279 chars elided]…
[c.sql() for c in p.args[\"fields\"][0].find_all(exp.Column)])\nfor n in lineage(\"metric_name\", sql, schema=schema, dialect=\"snowflake\").walk(): print(\"metric_name:\", n.name)\nfor n in lineage(\"id\", sql, schema=schema, dialect=\"snowflake\").walk(): print(\"id:\", n.name)\nEOF\npython -I /tmp/probe_unpivot2.py 2>&1 | tail -30", "description": "Inspect UNPIVOT AST and other column lineage"}
[tool_result] ['SCORE'] METRIC_NAME ['SRC.JAN', 'SRC.FEB']
metric_name: METRIC_NAME
metric_name: SRC.METRIC_NAME
id: ID
id: SRC.ID
[assistant] The IN-list columns are already qualified (`SRC.JAN`, `SRC.FEB`), so the fix can route them through the existing downstream loop. I'll make UNPIVOT take the pivot branch, with value and name columns mapped to the IN-list columns and pass-through columns handled as the pivot code already does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:\n        # For each aggregation function, the pivot creates a new column for each field in category
…[2295 chars elided]…
     pivot_columns = pivot.args[\"columns\"]\n        pivot_aggs_count = len(pivot.expressions)\n\n        pivot_column_mapping = {}\n        for i, agg in enumerate(pivot.expressions):\n            agg_cols = list(agg.find_all(exp.Column))\n            for col_index in range(i, len(pivot_columns), pivot_aggs_count):\n                pivot_column_mapping[pivot_columns[col_index].name] = agg_cols"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the branch that resolves each output column against the pivot:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            column_name = c.name\n            if any(column_name == pivot_column.name for pivot_column in pivot_columns):\n                downstream_columns.extend(pivot_column_mapping[column_name])\n            else:"
…[17 chars elided]…
            column_name = c.name\n            if pivot.unpivot and column_name in unpivot_names:\n                downstream_columns.extend(unpivot_columns)\n            elif not pivot.unpivot and any(\n                column_name == pivot_column.name for pivot_column in pivot_columns\n            ):\n                downstream_columns.extend(pivot_column_mapping[column_name])\n            else:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "python -I /tmp/repro_unpivot.py 2>&1 | head -12; cat >> /tmp/repro_unpivot.py <<'EOF'\nfor col in (\"metric_name\", \"id\"):\n    print(col, [n.name for n in lineage(col, sql, schema=schema, dialect=\"snowflake\").walk()])\nEOF\npython -I /tmp/repro_unpivot.py 2>&1 | tail -3", "description": "Rerun the reproduction after the fix"}
[tool_result] 'SCORE' Alias WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
'SRC.JAN' Table SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
'SRC.FEB' Table SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
---
Pivot(
  expressions=[
    Identifier(this=score, quoted=False)],
  fields=[
    In(
      this=Identifier(this=metric_name, quoted=False),
      expressions=[
        Column(
  default_on_null=False)
metric_name ['METRIC_NAME', 'SRC.JAN', 'SRC.FEB']
id ['ID', 'SRC.ID']
[assistant] Value lineage now reaches `SRC.JAN` and `SRC.FEB` instead of a phantom. But those are leaf nodes, not traced through the `src` CTE to `sales.jan`. I'll check why the pivoted source is a Table rather than a Scope.
[tool_use Bash] {"command": "sed -n 832,852p sqlglot/optimizer/scope.py", "description": "Read scope source handling for pivoted tables"}
[tool_result]     expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless
                # it is pivoted, because then we get back a new table and hence a new source.
                pivots = expression.args.get("pivots")
                if pivots:
                    sources[pivots[0].alias] = expression
                else:
                    sources[source_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
[assistant] A pivoted CTE reference is intentionally kept as a Table source in scope.py (the pivot creates a new relation), and the existing PIVOT path behaves the same way, so the leaf at `SRC.JAN` is consistent with it. Next I'll check the other source shapes, since the pivot branch has an existing `reference_node_name` variable that may be unassigned on some paths.
[tool_use Bash] {"command": "cat > /tmp/probe_shapes.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = {\n \"plain table\": \"SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\",\n \"subquery\": \"SELECT id, metric_name, score FROM (SELECT id, jan, feb FRO
…[204 chars elided]…
tems():\n    for col in (\"score\", \"metric_name\", \"id\"):\n        try:\n            print(name, col, [n.name for n in lineage(col, sql, schema=schema, dialect=\"snowflake\").walk()])\n        except Exception as ex:\n            print(name, col, \"ERROR\", type(ex).__name__, ex)\nEOF\npython -I /tmp/probe_shapes.py 2>&1 | tail -20", "description": "Check UNPIVOT lineage across source shapes"}
[tool_result] plain table score ['SCORE', 'SALES.JAN', 'SALES.FEB']
plain table metric_name ['METRIC_NAME', 'SALES.JAN', 'SALES.FEB']
plain table id ['ID', 'SALES.ID']
subquery score ['SCORE', 'S.JAN', 'SALES.JAN', 'S.FEB', 'SALES.FEB']
subquery metric_name ['METRIC_NAME', 'S.JAN', 'SALES.JAN', 'S.FEB', 'SALES.FEB']
subquery id ['ID', 'S.ID', 'SALES.ID']
aliased in-list score ['SCORE', 'SALES.JAN', 'SALES.FEB']
aliased in-list metric_name ERROR SqlglotError Cannot find column 'METRIC_NAME' in query.
aliased in-list id ERROR SqlglotError Cannot find column 'ID' in query.
[assistant] Those all trace through correctly. The `aliased in-list` errors are a bug in my probe, not the code: that query only selects `score`, so `metric_name` and `id` aren't output columns. Next I'll add a regression test next to the existing PIVOT lineage tests.
[tool_use Bash] {"command": "grep -n -i \"pivot\" tests/test_lineage.py | head; grep -n \"def test_\" tests/test_lineage.py | head -5", "description": "Locate existing pivot lineage tests"}
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
38 matches in 38 files:

1005:0:
128:0:
148:0:
[tool_use Bash] {"command": "sed -n 637,700p tests/test_lineage.py", "description": "Read existing pivot test patterns"}
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
…[1120 chars elided]…
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
[assistant] I'll add regression tests alongside the existing PIVOT tests, using the issue's query with the default dialect to match the surrounding tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(node.downstream[0].name, \"t.empid\")\n        self.assertEqual(node.downstream[0].reference_node_name, \"t\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"quarterly_sal
…[836 chars elided]…
       FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\n        \"\"\"\n\n        node = lineage(\"metric_name\", sql)\n        self.assertEqual(\n            [downstream.name for downstream in node.downstream[0].downstream],\n            [\"sales.jan\", \"sales.feb\"],\n        )\n\n        node = lineage(\"id\", sql)\n        self.assertEqual(node.downstream[0].name, \"sales.id\")\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Run lineage test module"}
[tool_result] ____________________ TestLineage.test_unpivot_value_column _____________________

self = <tests.test_lineage.TestLineage testMethod=test_unpivot_value_column>

    def test_unpivot_value_column(self) -> None:
        sql = """
        WITH src AS (SELECT id, jan, feb FROM sales)
        SELECT id, metric_name, score
        FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
        """
        node = lineage("score", sql)
    
>       self.assertEqual(
            [downstream.name for downst
…[139 chars elided]…
', 'src.feb']
E       
E       Second list contains 2 additional elements.
E       First extra element 0:
E       'src.jan'
E       
E       - []
E       + ['src.jan', 'src.feb']

tests/test_lineage.py:696: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_unpivot_name_column_and_implicit_column
FAILED tests/test_lineage.py::TestLineage::test_unpivot_value_column - Assert...
2 failed, 38 passed in 0.13s
[assistant] The failures are in my test indexing, not the fix. For a top-level column, the leaves hang directly off `node.downstream`; the extra `downstream[0]` hop only applies when the column comes from a CTE. I'll correct the indexing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"score\", sql)\n\n        self.assertEqual(\n            [downstream.name for downstream in node.downstream[0].downstream],\n            [\"src.jan\", \"src.feb\"],\n        )", "new_string": "        node = lineage(\"score\", sql)\n\n        self.assertEqual([downstream.name for downstream in node.downstream], [\"src.jan\", \"src.feb\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"metric_name\", sql)\n        self.assertEqual(\n            [downstream.name for downstream in node.downstream[0].downstream],\n            [\"sales.jan\", \"sales.feb\"],\n        )\n\n     
…[4 chars elided]…
ode = lineage(\"id\", sql)\n        self.assertEqual(node.downstream[0].name, \"sales.id\")", "new_string": "        node = lineage(\"metric_name\", sql)\n        self.assertEqual([downstream.name for downstream in node.downstream], [\"sales.jan\", \"sales.feb\"])\n\n        node = lineage(\"id\", sql)\n        self.assertEqual([downstream.name for downstream in node.downstream], [\"sales.id\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162616-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list | head -0; git status --short", "description": "Run lineage tests then full suite", "timeout": 400000}
[tool_result] ........................................                                 [100%]
40 passed in 0.09s
.......................... [ 98%]
..................              [100%]
1117 passed, 18166 subtests passed in 49.63s
head: illegal line count -- 0

thread 'main' (43196234) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
 M sqlglot/lineage.py
 M tests/test_lineage.py
[assistant] Lineage tests pass (40/40) and the full suite passes (1117). I'll run the linter on the two changed files, since a couple of my test lines are long.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/lineage.py tests/test_lineage.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -8", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format tests/test_lineage.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -1", "description": "Apply formatter and rerun lineage tests"}
[tool_result] 1 file reformatted
sqlglot/lineage.py    | 15 ++++++++++++---
 tests/test_lineage.py | 26 ++++++++++++++++++++++++++
 2 files changed, 38 insertions(+), 3 deletions(-)
40 passed in 0.09s
[This command modified 1 file you've previously read: tests/test_lineage.py. Call Read before editing.]
[assistant] UNPIVOT lineage now reaches the unpivoted source columns. The value column `score` resolves to `src.jan` and `src.feb` instead of the phantom `SRC.SCORE`, and the name column `metric_name` also resolves to the IN-list columns.

**Change** (`sqlglot/lineage.py`): the pivot branch skipped UNPIVOT entirely (`not pivots[0].unpivot`), so its columns fell through to the leaf case and produced the phantom. UNPIVOT now takes the same branch as PIVOT, with two differences:
- The value and name columns map to the columns listed in the `IN (...)` clause.
- Any other column from the source, such as `id`, 
…[272 chars elided]…
assed), and ruff check and format are clean. I have not committed.

**Choices to check:**
- I mapped the name column to the IN-list columns, since its values are those column names. If you'd rather it have no upstream columns, that's a small change.
- For a CTE source, the leaves stop at `src.jan` and `src.feb` rather than continuing to `sales.jan`. The scope builder deliberately keeps a pivoted CTE reference as a table, and PIVOT behaves the same way. Subquery sources do trace all the way down. Tracing through a CTE would mean changing how scope handles pivoted references, so I left that out.
