# trajectory base-1

final message:
`lineage()` now traces UNPIVOT value columns back to the IN-list source columns. For your example, `score` reaches `SRC.JAN` and `SRC.FEB`, and then `SALES.JAN` and `SALES.FEB`. The full test suite passes (1116 tests), and mypy and ruff are clean.

The change is in `sqlglot/lineage.py`, with a new `test_unpivot_with_cte` in `tests/test_lineage.py`.

- **Value column:** it maps to the IN-list column at the same position in each IN item. Multi-column UNPIVOT tuples are handled the same way.
- **Name column:** I chose to end its lineage at a leaf on the UNPIVOT node, since its values are the IN-list labels rather than data from any source column. It no longer produces a phantom `SRC.METRIC_NAME` column on the input. If you'd rather it point at `jan` and `feb`, that's a small change.
- **Other columns:** pass-through columns like `id` still trace to the source as before.
- **CTE resolution:** scope building drops the CTE link for a pivoted table reference, so the new branch looks the CTE up in `scope.cte_sources`. Without that, the trace stopped at `SRC.JAN`.

I haven't committed anything. I did not check whether PIVOT over a CTE has the same scope gap; my quick probe hit an "Unknown subquery scope" warning, but I didn't dig into it.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"Unpivot\\|unpivot\\|Pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py | head -60", "description": "Check status and find UNPIVOT handling"}
[tool_result] sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
sqlglot/optimizer/scope.py:98:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:508:    def pivots(self) -> list[exp.Pivot]:
sqlglot/optimizer/qualify_columns.py:614:            if scope.pivots and not column.find_ancestor(exp.Pivot):
sqlglot/optimizer/qualify_columns.py:615:                # If the column is under the Pivot expression, we need to qualify it
sqlglot/optimizer/qualify
…[232 chars elided]…
s.py:369:                            if pivot.unpivot
sqlglot/optimizer/annotate_types.py:658:    def _get_unpivot_column_types(
sqlglot/optimizer/annotate_types.py:659:        self, pivot: exp.Pivot, src_types: dict[str, exp.DataType | exp.DType]
sqlglot/optimizer/annotate_types.py:667:            if isinstance(first, exp.PivotAlias) and (alias_node := first.args.get("alias")):
sqlglot/optimizer/annotate_types.py:687:        self, pivot: exp.Pivot, src_types: dict[str, exp.DataType | exp.DType]
[tool_use Bash] {"command": "cat > /tmp/repro_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nnode = lineage(\"score\", sql, schema=schema, dialect=\"snowflake\")\nnode.print_tree()
…[73 chars elided]…
rint(n.name, \"|\", n.source.sql(dialect=\"snowflake\")[:80])\nprint(\"---name\")\nnode = lineage(\"metric_name\", sql, schema=schema, dialect=\"snowflake\")\nfor n in node.walk():\n    print(n.name, \"|\", n.source.sql(dialect=\"snowflake\")[:80])\nEOF\npython -I /tmp/repro_unpivot.py; echo; sed -n 340,420p sqlglot/lineage.py", "description": "Reproduce UNPIVOT lineage issue and read pivot code"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_unpivot.py", line 1, in <module>
    from sqlglot.lineage import lineage
ModuleNotFoundError: No module named 'sqlglot'

                _cache=_cache,
                _scope_meta=_scope_meta,
                on_node=on_node,
            )

    # if the select is a star add all scope sources as downstreams
    if isinstance(select, exp.Star):
        for src in scope.sources.values():
            src_expr = src.expression if isinstance(src, S
…[2906 chars elided]…
one using the unaliased column name.
            to_node(
                c.name,
                scope=col_source,
                dialect=dialect,
                scope_name=table,
                upstream=node,
                source_name=source_names.get(table) or source_name,
                reference_node_name=reference_node_name,
                trim_selects=trim_selects,
                _cache=_cache,
                _scope_meta=_scope_meta,
                on_node=on_node,
            )
[tool_use Bash] {"command": "PYTHONPATH=. python -I /tmp/repro_unpivot.py; echo; sed -n 420,470p sqlglot/lineage.py; sed -n 280,340p sqlglot/lineage.py", "description": "Run repro with repo on path and read lineage code"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_unpivot.py", line 1, in <module>
    from sqlglot.lineage import lineage
ModuleNotFoundError: No module named 'sqlglot'

            )
        elif pivot and pivot.alias_or_name == c.table:
            downstream_columns = []

            column_name = c.name
            if any(column_name == pivot_column.name for pivot_column in pivot_columns):
                downstream_columns.extend(pivot_column_mapping[column_name])
            else:
   
…[3830 chars elided]…
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
[tool_use Bash] {"command": "PYTHONPATH=$PWD python /tmp/repro_unpivot.py", "description": "Run repro with repo on PYTHONPATH"}
[tool_result] SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
---name
METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
SRC.METRIC_NAME | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
[tool_use Bash] {"command": "PYTHONPATH=$PWD python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one('''SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))''', read='snowflake')\np=e.find(exp.Pivot); print(repr(p)); print(p.args.get('columns'), p.args.get('field'))\ne2=sqlglot.parse_one('''SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan AS j, feb))''', read='snowflake')\nprint(repr(e2.find(exp.Pivot)))\n\"; sed -n 770,830p sqlglot/optimizer/qualify_columns.py; sed -n 655,720p sqlglot/optimizer/annotate_types.py; sed -n 500,530p sqlglot/optimizer/scope.py", "description": "Inspect UNPIVOT AST and related optimizer code"}
[tool_result] Pivot(
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
None None
Pivot(
  expressions=[
    Identifier(this=score, quoted=False)],
  fields=[
    In(
      this=Identifier(this=metric_name, quoted=False),
      expr
…[6017 chars elided]…
 -> set[str]:
        self._ensure_collected()
        return self._semi_anti_join_tables

    def source_columns(self, source_name: str) -> list[exp.Column]:
        """
        Get all columns in the current scope for a particular source.

        Args:
            source_name (str): Name of the source
        Returns:
            list[exp.Column]: Column instances that reference `source_name`
        """
        return [column for column in self.columns if column.text("table") == source_name]
[tool_use Bash] {"command": "PYTHONPATH=$PWD python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.scope import build_scope\nsql='''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nq=qualify(sqlglot.parse_one(sql,read='snowf
…[1 chars elided]…
ake'),schema=schema,dialect='snowflake')\nprint(q.sql('snowflake'))\ns=build_scope(q)\nprint(s.sources, s.pivots, [repr(c) for c in s.columns][:3])\nfor c in s.columns: print(c.table, c.name)\n\"; grep -n \"_pivots\\|pivots\" sqlglot/optimizer/scope.py | head; grep -n \"unpivot\" sqlglot/lineage.py tests/test_lineage.py | head", "description": "Inspect qualified AST and scope sources for UNPIVOT"}
[tool_result] WITH "SRC" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "SRC"."ID" AS "ID", "SRC"."METRIC_NAME" AS "METRIC_NAME", "SRC"."SCORE" AS "SCORE" FROM "SRC" AS "SRC" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SRC"
{'SRC': Table(
  this=Identifier(this='SRC', quoted=True),
  pivots=[
    Pivot(
      expressions=[
        Identifier(this='SCORE', quoted=True)],
      fields=[
        In(
          this=Identifier(this='METR
…[1506 chars elided]…
sion if expression.args.get("pivots") else expression.unnest()
508:    def pivots(self) -> list[exp.Pivot]:
509:        if self._pivots is None:
510:            self._pivots = [
511:                pivot for _, node in self.references for pivot in node.args.get("pivots") or []
514:        return self._pivots
845:                pivots = expression.args.get("pivots")
846:                if pivots:
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
[tool_use Bash] {"command": "PYTHONPATH=$PWD python -c \"\nfrom sqlglot.lineage import lineage\nsql='''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, a FROM src PIVOT (sum(jan) FOR id IN (1, 2)) AS p'''\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nfor n in lineage('a', sql, schema=schema, dialect='snowflake').walk(): print(n.name,'|',n.source.sql('snowflake')[:90])\n\"; grep -n \"pivot\\|PIVOT\\|UNPIVOT\" tests/test_lineage.py | head -30", "description": "Compare PIVOT lineage through CTE and existing tests"}
[tool_result] Unknown subquery scope: SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES
A | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES
SRC.A | SELECT SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES FROM 
SALES.ID | SALES AS SALES
SALES.FEB | SALES AS SALES
SALES.JAN | SALES AS SALES
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
[tool_use Bash] {"command": "sed -n 600,770p tests/test_lineage.py", "description": "Read existing pivot lineage tests"}
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
…[4833 chars elided]…
)
        self.assertEqual(
            node.downstream[0].downstream[0].downstream[0].name,
            "loan_ledger.product_type",
        )

        node = lineage('"2024-10"', sql, dialect="duckdb", schema=schema)
        self.assertEqual(node.downstream[0].name, "cte.2024-10")
        self.assertEqual(node.downstream[0].downstream[0].name, "_0.loan_id")
        self.assertEqual(node.downstream[0].downstream[0].downstream[0].name, "loan_ledger.loan_id")

    def test_copy_flag(self) -> None:
[tool_use Bash] {"command": "PYTHONPATH=$PWD python -c \"\nfrom sqlglot.lineage import lineage\nfrom sqlglot.optimizer.scope import build_scope\nimport sqlglot\nsql='''WITH t AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM t UNPIVOT (score FOR metric_name IN (jan, feb))'''\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nfor n in lineage('score', sql, schema=schema, dialect='snowflake').walk(): print(n.name,'|',n.source.sql('snowflake')[:90])\n\"; grep -n \"pivots\" sqlglot/optimizer/scope.py sqlglot/optimizer/qualify*.py | head", "description": "Test UNPIVOT lineage with CTE named differently"}
[tool_result] SCORE | WITH T AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) 
T.SCORE | T AS T UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS T
sqlglot/optimizer/qualify_columns.py:124:            if scope.external_columns and not scope.is_correlated_subquery and not scope.pivots:
sqlglot/optimizer/qualify_columns.py:602:                pivots := column_source.args.get("pivots")
sqlglot/optimizer/qualify_columns.py:604:                source_columns = pivots[0].output_colum
…[181 chars elided]…
     column.set("table", exp.to_identifier(scope.pivots[0].alias))
sqlglot/optimizer/qualify_columns.py:640:    for pivot in scope.pivots:
sqlglot/optimizer/qualify_columns.py:781:    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))
sqlglot/optimizer/scope.py:98:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:148:        self._pivots = None
sqlglot/optimizer/scope.py:440:                            expression if expression.args.get("pivots") else expression.unnest()
[tool_use Bash] {"command": "sed -n 425,450p sqlglot/optimizer/scope.py; sed -n 835,870p sqlglot/optimizer/scope.py", "description": "Read scope table source handling around pivots"}
[tool_result]     @property
    def references(self) -> list[tuple[str, exp.Selectable]]:
        if self._references is None:
            self._references = []

            for table in self.tables:
                self._references.append((table.alias_or_name, table))
            for _expr in itertools.chain(self.derived_tables, self.udtfs):
                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
                expression: exp.Expr = _expr
                self._referen
…[1508 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"cte_sources\" sqlglot/optimizer/scope.py | head -20; PYTHONPATH=$PWD python -c \"\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.scope import build_scope\nimport sqlglot\nsql='''WITH t AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM t AS x UNPIVOT (score FOR metric_name IN (jan, feb))'''\nschema={'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nq=qualify(sqlglot.parse_one(sql,read='snowflake'),schema=schema,dialect='snowflake')\nprint(q.sql('snowflake'))\ns=build_scope(q); print(s.sources.keys(), s.cte_sources.keys(), [type(v).__name__ for v in s.sources.values()])\n\"", "description": "Check scope cte_sources and aliased CTE pivot"}
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
WITH "T" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "X"."ID" AS "ID", "X"."METRIC_NAME" AS "METRIC_NAME", "X"."SCORE" AS "SCORE" FROM "T" AS "X" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "X"
dict_keys(['T', 'X']) dict_keys(['T']) ['Scope', 'Table']
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/lineage.py | grep -n \"import\" ; grep -n \"seq_get\\|exp.Tuple\\|PivotAlias\" sqlglot/lineage.py | head; sed -n 456,475p sqlglot/lineage.py", "description": "Check imports and tail of lineage source branch"}
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
16:    f
…[475 chars elided]…
nt, if a source is not found it means this column's lineage
            # is unknown. This can happen if the definition of a source used in a query is not
            # passed into the `sources` map.
            col_expr = col_source or exp.Placeholder()
            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
            node.downstream.append(leaf)
            if on_node:
                on_node(leaf)

    if _cache is not None:
        _cache[cache_key] = node
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:", "new_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    unpivot = pivots[0] if len(pivots) == 1 and pivots[0].unpivot else None\n    if pivot:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "        col_source: exp.Table | Scope | None = scope.sources.get(table)\n\n        if isinstance(col_source, Scope):\n            reference_node_name = None", "new_string": "        col_source: exp.Table | Scope | None 
…[2541 chars elided]…
ents=False),\n                        source=unpivot_scope or exp.Placeholder(),\n                        expression=unpivot_scope or exp.Placeholder(),\n                    )\n                    node.downstream.append(unpivot_leaf)\n                    if on_node:\n                        on_node(unpivot_leaf)\n        elif isinstance(col_source, Scope):\n            reference_node_name = None"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nfrom sqlglot.lineage import lineage\ndef dump(col, sql, **kw):\n    print(\"==\", col)\n    def rec(n, d=0):\n        print(\"  \" * d + f\"{n.name} | {n.source.sql('snowflake')[:70]}\")\n        for c in n.downstream: rec(c, d + 1)\n    rec(lineage(col, sql, **kw))\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\nfor sql in [
…[204 chars elided]…
tric_name, score FROM t AS x UNPIVOT (score FOR metric_name IN (jan, feb))\",\n    \"SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\",\n]:\n    for col in [\"score\", \"metric_name\", \"id\"]:\n        dump(col, sql, schema=schema, dialect=\"snowflake\")\nEOF\nPYTHONPATH=$PWD python /tmp/repro2.py", "description": "Run lineage repro across UNPIVOT variants"}
[tool_result] == score
SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
  SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
    SALES.JAN | SALES AS SALES
  SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
    SALES.FEB | SALES AS SALES
== metric_name
METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB
  SRC.METRIC_NAME | UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
== id
ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, S
…[781 chars elided]…
ES.JAN | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
  SALES.FEB | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
== metric_name
METRIC_NAME | SELECT SALES.METRIC_NAME AS METRIC_NAME FROM SALES AS SALES UNPIVOT(SC
  SALES.METRIC_NAME | UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
== id
ID | SELECT SALES.ID AS ID FROM SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAM
  SALES.ID | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py tests/test_optimizer.py 2>&1 | tail -15", "description": "Check project venv and run lineage/optimizer tests"}
[tool_result] <work>/env-sqlglot/bin/python
........................................................................ [ 61%]
....................... [ 81%]
......................       [100%]
117 passed, 3909 subtests passed in 15.58s
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "    def test_table_udtf_snowflake(self) -> None:", "new_string": "    def test_unpivot_with_cte(self) -> None:\n        schema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\n        sql = \"\"\
…[630 chars elided]…
    self.assertEqual(node.downstream[0].name, \"SRC.METRIC_NAME\")\n        self.assertEqual(node.downstream[0].downstream, [])\n\n        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\n\n    def test_table_udtf_snowflake(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py -k unpivot 2>&1 | tail -20; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; (ruff check sqlglot/lineage.py tests/test_lineage.py && ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -5; $P -m mypy sqlglot/lineage.py 2>&1 | tail -5", "description": "Run new test, full suite, ruff and mypy"}
[tool_result] .                                                                        [100%]
1 passed, 38 deselected in 0.03s
.............................................................................................................................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1116 passed, 18166 subtests passed in 49.82s
All checks passed!
2 files already formatted
sqlglot/lineage.py:437: error: Item "None" of "Expr | None" has no attribute "name"  [union-attr]
Found 1 error in 1 file (checked 1 source file)
[tool_use Bash] {"command": "sed -n 430,440p sqlglot/lineage.py", "description": "View line flagged by mypy"}
[tool_result]                     to_node(
                        downstream_column.name,
                        scope=unpivot_scope,
                        scope_name=table,
                        dialect=dialect,
                        upstream=node,
                        source_name=source_names.get(table) or source_name,
                        reference_node_name=unpivot_source.name
                        if unpivot_scope.scope_type == ScopeType.CTE
                        else None,
                        trim_selects=trim_selects,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "                        reference_node_name=unpivot_source.name\n                        if unpivot_scope.scope_type == ScopeType.CTE\n                        else None,", "new_string": "                        reference_node_name=unpivot_source.name\n                        if unpivot_scope.scope_type == ScopeType.CTE and unpivot_source\n                        else None,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095040-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m mypy sqlglot/lineage.py 2>&1 | tail -3; ruff format --check sqlglot/lineage.py tests/test_lineage.py; $P -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py tests/test_optimizer.py 2>&1 | tail -2; git diff --stat", "description": "Re-run mypy, format check, and lineage tests"}
[tool_result] Success: no issues found in 1 source file
2 files already formatted
.......................      [100%]
118 passed, 3909 subtests passed in 13.22s
 sqlglot/lineage.py    | 57 ++++++++++++++++++++++++++++++++++++++++++++++++++-
 tests/test_lineage.py | 26 +++++++++++++++++++++++
 2 files changed, 82 insertions(+), 1 deletion(-)
[assistant] `lineage()` now traces UNPIVOT value columns back to the IN-list source columns. For your example, `score` reaches `SRC.JAN` and `SRC.FEB`, and then `SALES.JAN` and `SALES.FEB`. The full test suite passes (1116 tests), and mypy and ruff are clean.

The change is in `sqlglot/lineage.py`, with a new `test_unpivot_with_cte` in `tests/test_lineage.py`.

- **Value column:** it maps to the IN-list column at the same position in each IN item. Multi-column UNPIVOT tuples are handled the same way.
- **Name column:** I chose to end its lineage at a leaf on the UNPIVOT node, since its values are the IN-l
…[49 chars elided]…
n. It no longer produces a phantom `SRC.METRIC_NAME` column on the input. If you'd rather it point at `jan` and `feb`, that's a small change.
- **Other columns:** pass-through columns like `id` still trace to the source as before.
- **CTE resolution:** scope building drops the CTE link for a pivoted table reference, so the new branch looks the CTE up in `scope.cte_sources`. Without that, the trace stopped at `SRC.JAN`.

I haven't committed anything. I did not check whether PIVOT over a CTE has the same scope gap; my quick probe hit an "Unknown subquery scope" warning, but I didn't dig into it.
