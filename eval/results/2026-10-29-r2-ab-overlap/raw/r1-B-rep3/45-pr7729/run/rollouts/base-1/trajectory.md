# trajectory base-1

final message:
UNPIVOT lineage now reaches the source columns. `lineage("score", ...)` returns `SRC.JAN` → `SALES.JAN` and `SRC.FEB` → `SALES.FEB` instead of the phantom `SRC.SCORE` leaf. The full suite passes (1116 tests), and mypy and ruff are clean. I haven't committed anything.

**Root cause:** `to_node` in `sqlglot/lineage.py` only handled PIVOT. The branch was gated on `not pivots[0].unpivot`, so every UNPIVOT column fell through to the generic leaf.

**Changes in `sqlglot/lineage.py`:**
- **Value columns** (`score`) map to the IN-list columns (`jan`, `feb`). Multi-value unpivots (`(a, b) FOR ...`) are handled too.
- **Name column** (`metric_name`) has no downstream columns. Its values are the IN-list labels, which are literals, so it no longer points at a phantom column on the input. This is my reading of "handled correctly"; if you want it to point at `jan`/`feb` instead, that's a one-line change.
- **Passthrough columns** (`id`) now reach the CTE. They were stopping at `SRC.ID` before.
- **Pivoted CTE input:** the pivoted alias overwrites the CTE in `scope.sources`, so the lookup now goes through `scope.cte_sources`. This is what makes the lineage reach `SALES.*`.
- **Helper:** the `reference_node_name` logic moved into `_reference_node_name`. The pivot downstream loop was reading that variable without assigning it.

**Tests:** I added `test_unpivot_with_cte` to `tests/test_lineage.py`. I didn't change any existing test. I also checked a real-table UNPIVOT, a derived-table UNPIVOT, a multi-value UNPIVOT, and an aliased IN label; all resolve to the right source columns.

**Not fixed:** PIVOT over a CTE returns the same result before and after this change. Both give `SALES.JAN` for the aggregated column, so I didn't touch that path beyond the shared `cte_sources` lookup.

## events
[assistant] I'll reproduce the bug first, then read how lineage handles `Unpivot`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nfor c in ['score','metric_name','id']:\n    n = lineag
…[65 chars elided]…
n.print_tree() if hasattr(n,'print_tree') else print(n)\n    for leaf in n.walk():\n        print('  ', leaf.name, leaf.source.sql() if hasattr(leaf.source,'sql') else leaf.source)\n\" 2>&1 | head -80; grep -n -i \"unpivot\\|pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -50", "description": "Reproduce unpivot lineage bug and grep pivot handling"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/lineage.py:374:    pivots = scope.pivots
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
sqlglot/lineage.py:376:    if pivot:
sqlglot/lineage.py:377:        # For each aggregation function, the pivot creates a new column for each field in category
sqlglot/lineage.py:382:        # in the lineage, so lookup the pivot c
…[3816 chars elided]…
identifier(scope.pivots[0].alias))
sqlglot/optimizer/qualify_columns.py:640:    for pivot in scope.pivots:
sqlglot/optimizer/qualify_columns.py:641:        for column in pivot.find_all(exp.Column):
sqlglot/optimizer/qualify_columns.py:781:    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))
sqlglot/optimizer/qualify_columns.py:844:            if pivot:
sqlglot/optimizer/qualify_columns.py:845:                pivot_columns = pivot.output_columns(columns) or pivot.alias_column_names
[assistant] The reproduction failed because `-I` drops the working directory from `sys.path`. Rerunning from the worktree without it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot; print(sqlglot.__file__)\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ndef show(n, d=0):\n    print('  '*d, n.name, '|', n.source.sql(dialect='snowflake')[:80] if n.source else None)\n    for c in n.downstream: show(c, d+1)\nfor c in ['score','metric_name','id']:\n    print('==', c)\n    show(lineage(c, sql, schema=schema, dialect='snowflake'))\n\" 2>&1 | head -60", "description": "Reproduce unpivot lineage from worktree"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/__init__.py
== score
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
   SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
== metric_name
 METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
   SRC.METRIC_NAME | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
== id
 ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALE
   SRC.ID | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
[assistant] Reproduced: `score` stops at a phantom `SRC.SCORE` leaf, and `metric_name` does too. Now the pivot handling in `lineage.py`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "offset": 340, "limit": 150}
[tool_result] 340	                _cache=_cache,
341	                _scope_meta=_scope_meta,
342	                on_node=on_node,
343	            )
344	
345	    # if the select is a star add all scope sources as downstreams
346	    if isinstance(select, exp.Star):
347	        for src in scope.sources.values():
348	            src_expr = src.expression if isinstance(src, Scope) else src
349	            star_node = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)
350	            node
…[6112 chars elided]…
False), source=col_expr, expression=col_expr)
469	            node.downstream.append(leaf)
470	            if on_node:
471	                on_node(leaf)
472	
473	    if _cache is not None:
474	        _cache[cache_key] = node
475	
476	    if on_node:
477	        on_node(node)
478	
479	    return node
480	
481	
482	class GraphHTML:
483	    """Node to HTML generator using vis.js.
484	
485	    https://visjs.github.io/vis-network/docs/network/
486	    """
487	
488	    def __init__(
489	        self,
[assistant] The pivot branch is gated on `not pivots[0].unpivot`, so an UNPIVOT falls through to the generic leaf at line 467. Before deciding the fix, I'll check the AST shape for UNPIVOT and the existing pivot tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('''SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb AS f))''', read='snowflake')\np = e.find(exp.Pivot)\nprint(repr(p))\nprint(p.args.get('columns'), p.expressions, p.args.get('field'))\ne2 = sqlglot.parse_one('''SELECT id, metric_name, score FROM src UNPIVOT INCLUDE NULLS (score FOR metric_name IN (jan, feb))''', read='snowflake')\nprint(repr(e2.find(exp.Pivot)))\n\"; grep -n \"unpivot\\|UNPIVOT\" tests/test_lineage.py | head; grep -n \"def test_.*pivot\" tests/test_lineage.py", "description": "Inspect UNPIVOT AST and existing lineage pivot tests"}
[tool_result] Pivot(
  expressions=[
    Identifier(this=score, quoted=False)],
  fields=[
    In(
      this=Identifier(this=metric_name, quoted=False),
      expressions=[
        Column(
          this=Identifier(this=jan, quoted=False)),
        PivotAlias(
          this=Column(
            this=Identifier(this=feb, quoted=False)),
          alias=Identifier(this=f, quoted=False))])],
  unpivot=True,
  default_on_null=False)
None [Identifier(this=score, quoted=False)] None
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
  include_nulls=True,
  default_on_null=False)
0 matches for 'unpivot\|UNPIVOT'
6 matches in 6 files:

607:0:
622:0:
637:0:
656:0:
670:0:
733:0:
[assistant] The UNPIVOT bug has two parts. The pivot branch is disabled for UNPIVOT, so the value column never reaches its IN-list sources. The implicit passthrough column `id` takes the same dead path and also stops at `SRC.ID`. Next I'll check `reference_node_name` (the downstream loop uses it without assigning it) and the existing pivot tests.
[tool_use Bash] {"command": "grep -n \"reference_node_name\" sqlglot/lineage.py; grep -n -i \"pivot\" tests/test_lineage.py | head -30; sed -n 230,262p sqlglot/lineage.py", "description": "Locate reference_node_name uses and pivot lineage tests"}
[tool_result] 11 matches in 3 files:

198:0:str | None = None,
29:0:str = ""
sqlglot/lineage.py:204:cache_key = (column, id(scope), scope_name, source_name, reference_node_name)
sqlglot/lineage.py:249:reference_node_name=reference_node_name,
sqlglot/lineage.py:289:reference_node_name=reference_node_name,
sqlglot/lineage.py:317:reference_node_name=reference_node_name or "",
sqlglot/lineage.py:400:reference_node_name = None
sqlglot/lineage.py:402:reference_node_name = table
sqlglot/lineage.py:405:reference_node
…[1731 chars elided]…
a,
                on_node=on_node,
            )
            # Skip caching a passed-in upstream returned by an inner SetOp:
            # a sibling call at the same key with that node as its upstream
            # would otherwise self-loop on the cache hit.
            if _cache is not None and result is not upstream:
                _cache[cache_key] = result
            return result
    if isinstance(scope.expression, exp.SetOperation):
        name = type(scope.expression).__name__.upper()
[assistant] Existing pivot tests cover the CTE and implicit-column cases. I'll read them to match the expected output format.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "offset": 605, "limit": 130}
[tool_result] 605	        self.assertEqual(node.downstream[0].downstream[0].name, "t1.x")
606	
607	    def test_pivot_without_alias(self) -> None:
608	        sql = """
609	        SELECT
610	            a as other_a
611	        FROM (select value,category from sample_data)
612	        PIVOT (
613	            sum(value)
614	            FOR category IN ('a', 'b')
615	        );
616	        """
617	        node = lineage("other_a", sql)
618	
619	        self.assertEqual(node.downstream[0].name, "_0.value")
620	
…[3853 chars elided]…
al(lateral_node.name, "RAW.EVENTS")
722	        self.assertEqual(
723	            lateral_node.source.sql("snowflake"),
724	            "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME AS RAW",
725	        )
726	
727	        self.assertEqual(table_node.name, "RAW.EVENTS")
728	        self.assertEqual(
729	            table_node.source.sql("snowflake"),
730	            "DATABASE_NAME.SCHEMA_NAME.TABLE_NAME AS RAW",
731	        )
732	
733	    def test_pivot_with_subquery(self) -> None:
734	        schema = {
[assistant] The derived-table/CTE path through the pivot downstream loop reads `reference_node_name` without assigning it in that block. I'll confirm how `Pivot` exposes its name column and value columns, then make the change.
[tool_use Bash] {"command": "grep -n \"class Pivot\" -A 40 sqlglot/expressions.py | head -80; grep -n \"def selected_sources\" -A3 sqlglot/optimizer/scope.py", "description": "Read Pivot expression class and scope selected_sources"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
399:    def selected_sources(self) -> dict[str, tuple[exp.Selectable, exp.Table | Scope]]:
400-        """
401-        Mapping of nodes and sources that are actually selected from in this scope.
402-
[tool_use Bash] {"command": "grep -rn \"class Pivot(\" -A 30 sqlglot/expressions/ | head -50", "description": "Locate Pivot expression class definition"}
[tool_result] sqlglot/expressions/query.py:1747:class Pivot(Expression):
sqlglot/expressions/query.py-1748-    arg_types = {
sqlglot/expressions/query.py-1749-        "this": False,
sqlglot/expressions/query.py-1750-        "alias": False,
sqlglot/expressions/query.py-1751-        "expressions": False,
sqlglot/expressions/query.py-1752-        "fields": False,
sqlglot/expressions/query.py-1753-        "unpivot": False,
sqlglot/expressions/query.py-1754-        "using": False,
sqlglot/expressions/query.py-1755
…[967 chars elided]…
st[Expr]:
sqlglot/expressions/query.py-1772-        return self.args.get("fields", [])
sqlglot/expressions/query.py-1773-
sqlglot/expressions/query.py-1774-    def output_columns(self, pre_pivot_columns: t.Iterable[str]) -> dict[str, str]:
sqlglot/expressions/query.py-1775-        """
sqlglot/expressions/query.py-1776-        Returns an ordered map of post-rename output column name -> pre-rename
sqlglot/expressions/query.py-1777-        source-side name, in the order the (UN)PIVOT produces them.
[tool_use Bash] {"command": "sed -n 1774,1830p sqlglot/expressions/query.py", "description": "Read Pivot.output_columns implementation"}
[tool_result]     def output_columns(self, pre_pivot_columns: t.Iterable[str]) -> dict[str, str]:
        """
        Returns an ordered map of post-rename output column name -> pre-rename
        source-side name, in the order the (UN)PIVOT produces them.

        For callers that just want the names, iterate the dict (or call .keys()):
            >>> from sqlglot import parse_one, exp
            >>> piv = parse_one("SELECT * FROM t UNPIVOT(val FOR name IN (a, b))").find(exp.Pivot)
            >>> list(piv
…[1736 chars elided]…
lse:
            excluded = {c.output_name for c in self.find_all(Column)}
            outputs = [c.output_name for c in self.args.get("columns") or []]
            if not outputs:
                outputs = [c.alias_or_name for c in self.expressions]

        if not excluded or not outputs:
            return {}

        pre_rename = [c for c in pre_pivot_columns if c not in excluded] + outputs

        alias = self.args.get("alias")
        renames = alias.args.get("columns") if alias else None
[assistant] `Pivot.output_columns` confirms the AST shape: UNPIVOT value identifiers may be a `Tuple` for multi-value unpivots, and the name column is `fields[0].this`. Two things to verify after the edit: whether the IN-list columns arrive qualified with the pivot's source alias, and how the Scope branch behaves for a CTE parent.

My plan is to build one `pivot_column_mapping` for both PIVOT and UNPIVOT. For UNPIVOT, each value column maps to the IN-list columns, and the name column maps to nothing, since its values are literal labels. I'll also factor the `reference_node_name` logic into a helper so the pivot downstream loop computes it instead of reading an unassigned variable.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None\n    if pivot:\n        # For each aggregation function, the pivot creates a new column for each field in category
…[2449 chars elided]…
ategory IN ('a' AS cat_a, 'b')\n        pivot_columns = pivot.args[\"columns\"]\n        pivot_aggs_count = len(pivot.expressions)\n\n        for i, agg in enumerate(pivot.expressions):\n            agg_cols = list(agg.find_all(exp.Column))\n            for col_index in range(i, len(pivot_columns), pivot_aggs_count):\n                pivot_column_mapping[pivot_columns[col_index].name] = agg_cols"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the loop body: route pivot-derived columns through the mapping for both kinds, and compute `reference_node_name` for the Scope case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "        elif pivot and pivot.alias_or_name == c.table:\n            downstream_columns = []\n\n            column_name = c.name\n            if any(column_name == pivot_column.name for pivot_column in pivot_columns):\n 
…[1977 chars elided]…
                       downstream_column.name,\n                        scope=col_source,\n                        scope_name=table,\n                        dialect=dialect,\n                        upstream=node,\n                        source_name=source_names.get(table) or source_name,\n                        reference_node_name=_reference_node_name(scope, col_source, table, source_names),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll switch the first Scope branch to the same helper and define it at module level.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "        if isinstance(col_source, Scope):\n            reference_node_name = None\n            if col_source.scope_type == ScopeType.DERIVED_TABLE and table not in source_names:\n                reference_node_name = ta
…[794 chars elided]…
 into that one using the unaliased column name.\n            to_node(\n                c.name,\n                scope=col_source,\n                dialect=dialect,\n                scope_name=table,\n                upstream=node,\n                source_name=source_names.get(table) or source_name,\n                reference_node_name=_reference_node_name(scope, col_source, table, source_names),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^def \\|^class \" sqlglot/lineage.py | head -20", "description": "List top-level definitions in lineage module"}
[tool_result] 6 matches in 5 files:

23:0:
481:0:
81:0:str | exp.Column, sql: str | exp.Expr, **kwargs: t.Any) -> Node: ...
85:0:None, sql: str | exp.Expr, **kwargs: t.Any) -> dict[str, Node]: ...
sqlglot/lineage.py:88:def lineage(
sqlglot/lineage.py:191:def to_node(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "offset": 180, "limit": 12}
[tool_result] 180	            scope,
181	            dialect,
182	            trim_selects=trim_selects,
183	            _cache=cache,
184	            _scope_meta=scope_meta,
185	            on_node=on_node,
186	        )
187	
188	    return result
189	
190	
191	def to_node(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "    return result\n\n\ndef to_node(", "new_string": "    return result\n\n\ndef _reference_node_name(\n    scope: Scope, col_source: Scope, table: str, source_names: dict[str, str]\n) -> str | None:\n    if col_source.scope_type == ScopeType.DERIVED_TABLE and table not in source_names:\n        return table\n    if col_source.scope_type == ScopeType.CTE:\n        selected_node, _ = scope.selected_sources.get(table, (None, None))\n        return selected_node.name if selected_node else None\n    return None\n\n\ndef to_node("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll rerun the repro, then the lineage test module.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ndef show(n, d=0):\n    print('  '*d, n.name, '|',
…[1 chars elided]…
n.source.sql(dialect='snowflake')[:60] if n.source else None, '| ref=', n.reference_node_name)\n    for c in n.downstream: show(c, d+1)\nfor c in ['score','metric_name','id']:\n    print('==', c); show(lineage(c, sql, schema=schema, dialect='snowflake'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Rerun repro and lineage test module"}
[tool_result] == score
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
   SRC.JAN | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S | ref= 
   SRC.FEB | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S | ref= 
== metric_name
 METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
== id
 ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
   SRC.ID | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS S | ref= 
......................................                                   [100%]
38 passed in 0.10s
[assistant] Progress: `score` now fans out to `SRC.JAN` and `SRC.FEB`. But those leaves still stop at the pivot's own `SRC` entry rather than reaching the CTE, so the outer lookup resolves to the pivot source instead of the underlying relation. I'll look at how scope registers pivoted sources.
[tool_use Bash] {"command": "sed -n 832,852p sqlglot/optimizer/scope.py; sed -n 430,445p sqlglot/optimizer/scope.py", "description": "Read scope.py pivot source registration"}
[tool_result]     expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless
     
…[642 chars elided]…
          # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
                expression: exp.Expr = _expr
                self._references.append(
                    (
                        _get_source_alias(expression),
                        (
                            expression if expression.args.get("pivots") else expression.unnest()
                        ).assert_is(exp.Selectable),
                    )
                )

        return self._references
[assistant] The pivot-over-CTE case is the real gap. Scope stores the pivoted table under the pivot's alias (`SRC`), which is the same key the CTE is registered under, so the CTE's Scope is overwritten. I'll check whether the CTE scope is still reachable (`cte_sources`) and what keys the scope holds.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nsql = '''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''\ne = qualify(sqlglot.parse_one(sql, read='sn
…[154 chars elided]…
t sources', {k: type(v).__name__ for k,v in root.sources.items()})\nprint('cte_sources', list(root.cte_sources.keys()) if hasattr(root,'cte_sources') else None)\np = e.find(sqlglot.exp.Pivot); print('pivot alias', p.alias, 'parent', p.parent.name, p.parent.alias_or_name, [c.table for c in p.find_all(sqlglot.exp.Column)])\n\"", "description": "Inspect scope sources and CTE scope for unpivot query"}
[tool_result] WITH "SRC" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "SRC"."ID" AS "ID", "SRC"."METRIC_NAME" AS "METRIC_NAME", "SRC"."SCORE" AS "SCORE" FROM "SRC" AS "SRC" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SRC"
root sources {'SRC': 'Table'}
cte_sources ['SRC']
pivot alias SRC parent SRC SRC ['SRC', 'SRC']
[assistant] Confirmed: `root.sources['SRC']` is overwritten by the pivoted `Table`, but `root.cte_sources['SRC']` still holds the CTE Scope, and the IN columns are qualified with the pivot alias `SRC`. I'll check that `cte_sources` is a public `Scope` property, then route the pivot's input through it.
[tool_use Bash] {"command": "grep -n \"def cte_sources\" -A 12 sqlglot/optimizer/scope.py | head -20", "description": "Read Scope.cte_sources property"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"cte_sources\" sqlglot/optimizer/scope.py | head; ", "description": "Find cte_sources definition in scope module"}
[tool_result] 10 matches in 4 files:

109:0:dict[str, exp.Table | Scope] | None = None,
156:0:dict[str, exp.Table | Scope] | None = None,
64:0:Sources from CTES
sqlglot/optimizer/scope.py:115:self.cte_sources = cte_sources or {}
sqlglot/optimizer/scope.py:117:self.sources.update(self.cte_sources)
sqlglot/optimizer/scope.py:166:cte_sources={**self.cte_sources, **(cte_sources or {})},
sqlglot/optimizer/scope.py:698:yield from _traverse_scope(Scope(ddl_expression, cte_sources=scope.cte_sources))
sqlglot/optimizer/scope.py:705:yield from _traverse_scope(Scope(query, cte_sources=scope.cte_sources))
[assistant] `cte_sources` is a plain attribute on `Scope`. I'll wire the pivot's CTE input into the pivot branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            for downstream_column in downstream_columns:\n                table = downstream_column.table\n                col_source = scope.sources.get(table)\n                if isinstance(col_source, Scope):\n      
…[1061 chars elided]…
                       downstream_column.name,\n                        scope=col_source,\n                        scope_name=table,\n                        dialect=dialect,\n                        upstream=node,\n                        source_name=source_names.get(table) or source_name,\n                        reference_node_name=_reference_node_name(scope, col_source, table, source_names),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ndef show(n, d=0):\n    print('  '*d, n.name, '|',
…[9 chars elided]…
.sql(dialect='snowflake')[:60] if n.source else None, '| ref=', n.reference_node_name)\n    for c in n.downstream: show(c, d+1)\nfor c in ['score','metric_name','id']:\n    print('==', c); show(lineage(c, sql, schema=schema, dialect='snowflake'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Rerun repro and lineage tests after CTE fix"}
[tool_result] == score
 SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
   SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES | ref= SRC
     SALES.JAN | SALES AS SALES | ref= 
   SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES | ref= SRC
     SALES.FEB | SALES AS SALES | ref= 
== metric_name
 METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
== id
 ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES. | ref= 
   SRC.ID | SELECT SALES.ID AS ID FROM SALES AS SALES | ref= SRC
     SALES.ID | SALES AS SALES | ref= 
......................................                                   [100%]
38 passed in 0.08s
[assistant] Now `score` reaches `SALES.JAN` and `SALES.FEB` through the CTE, `id` reaches `SALES.ID`, and `metric_name` no longer produces a phantom column. I'll check the variants that go through the same code: a real-table UNPIVOT, a derived-table UNPIVOT, a multi-value UNPIVOT, an aliased IN label, and PIVOT over a CTE.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\ncases = {\n 'real table': ('score', 'SELECT id, score FROM sales UNPIVOT (score FOR m IN (jan, feb))'),\n 'derived': ('score', 'SELECT score FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score FOR 
…[437 chars elided]…
IN (1, 2))'),\n}\ndef leaves(n):\n    if not n.downstream: return [n.name]\n    return [x for c in n.downstream for x in leaves(c)]\nfor k,(c,sql) in cases.items():\n    try:\n        print(k, '->', leaves(lineage(c, sql, schema=schema, dialect='snowflake')))\n    except Exception as e: print(k, 'ERR', type(e).__name__, e)\n\"", "description": "Check unpivot variants and pivot-over-CTE behaviour"}
[tool_result] real table -> ['SALES.JAN', 'SALES.FEB']
derived -> ['SALES.JAN', 'SALES.FEB']
multi-value -> ['SALES.JAN', 'SALES.JAN', 'SALES.FEB', 'SALES.FEB']
alias label -> ['SALES.JAN', 'SALES.FEB']
pivot over cte ERR SqlglotError Cannot find column 'S' in query.
[assistant] The UNPIVOT variants all resolve. The pivot-over-CTE error is from my test SQL, which referenced a column name that doesn't exist. I'll retry with a valid PIVOT and compare against the pre-change code to see whether that path changed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/pv_check.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int'}}\nsql = \"WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, \\\"1\\\" AS x FROM src PIVOT (SUM(jan) FOR feb IN (1, 2))\"\ndef leaves(n):\n    if not n.downstream: return [n.
…[359 chars elided]…
age_orig.py; mkdir -p /tmp/orig_pkg && rm -rf /tmp/orig_pkg/sqlglot && cp -r sqlglot /tmp/orig_pkg/ && cp /tmp/lineage_orig.py /tmp/orig_pkg/sqlglot/lineage.py && cd /tmp/orig_pkg && $PY -I -c \"import sys; sys.path.insert(0,'/tmp/orig_pkg'); exec(open('/tmp/pv_check.py').read())\"; rm -rf /tmp/orig_pkg /tmp/lineage_orig.py", "description": "Compare pivot-over-CTE lineage before and after change"}
[tool_result] after:
Traceback (most recent call last):
  File "/tmp/pv_check.py", line 1, in <module>
    from sqlglot.lineage import lineage
ModuleNotFoundError: No module named 'sqlglot'
before:
pivot over cte -> ['SALES.JAN']
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1
[assistant] The "after" run failed only because `-I` hid the worktree package. Rerunning it with the worktree on `sys.path`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/pv_check.py; rm -f /tmp/pv_check.py", "description": "Run pivot-over-CTE check against worktree code"}
[tool_result] pivot over cte -> ['SALES.JAN']
[assistant] Pivot-over-CTE output is the same before and after, so no regression there. Now I'll add a regression test next to the existing pivot tests, covering the value column, the name column, and the passthrough column.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(node.downstream[0].name, \"t.empid\")\n        self.assertEqual(node.downstream[0].reference_node_name, \"t\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"quarterly_sal
…[952 chars elided]…
l, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\n\n        # The name column holds the IN-list labels, so it has no source columns\n        node = lineage(\"metric_name\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream, [])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195803-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -15; echo ---FULL---; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; echo ---LINT---; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3", "description": "Run lineage tests, full suite, and ruff checks"}
[tool_result] .......................................                                  [100%]
39 passed in 0.08s
---FULL---
...................................................................................................................... [ 49%]
............................ [ 51%]
................................................................................................................................................... [ 64%]
.........................................................................
…[29 chars elided]…
........................................................................................................................................................................................................................................................ [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1116 passed, 18166 subtests passed in 45.79s
---LINT---
All checks passed!
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
[assistant] All 1116 tests pass and ruff check is clean. Ruff format wants to rewrite `lineage.py`, so I'll apply it and review the result.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/lineage.py && git diff --stat && $PY -m mypy sqlglot/lineage.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -1", "description": "Apply ruff format, run mypy and lineage tests"}
[tool_result] 1 file reformatted
sqlglot/lineage.py    | 54 ++++++++++++++++++++++++++++++++++-----------------
 tests/test_lineage.py | 21 ++++++++++++++++++++
 2 files changed, 57 insertions(+), 18 deletions(-)
Success: no issues found in 1 source file
39 passed in 0.08s
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] That notice is from my own `ruff format` run, so the file is in the state I expect. I'll review the final diff before wrapping up.
[tool_use Bash] {"command": "git diff sqlglot/lineage.py", "description": "Show final lineage.py diff"}
[tool_result] sqlglot/lineage.py | 54 ++++++++++++++++++++++++++++++++++++------------------
 1 file changed, 36 insertions(+), 18 deletions(-)

--- Changes ---

sqlglot/lineage.py
  @@ -188,6 +188,17 @@ def lineage(
  +def _reference_node_name(
  +    scope: Scope, col_source: Scope, table: str, source_names: dict[str, str]
  +) -> str | None:
  +    if col_source.scope_type == ScopeType.DERIVED_TABLE and table not in source_names:
  +        return table
  +    if col_source.scope_type == ScopeType.CTE:
  +
…[4150 chars elided]…
           to_node(
                           downstream_column.name,
  @@ -443,7 +459,9 @@ def to_node(
  -                        reference_node_name=reference_node_name,
  +                        reference_node_name=_reference_node_name(
  +                            scope, col_source, table, source_names
  +                        ),
                           trim_selects=trim_selects,
                           _cache=_cache,
                           _scope_meta=_scope_meta,
  +36 -18
[assistant] UNPIVOT lineage now reaches the source columns. `lineage("score", ...)` returns `SRC.JAN` → `SALES.JAN` and `SRC.FEB` → `SALES.FEB` instead of the phantom `SRC.SCORE` leaf. The full suite passes (1116 tests), and mypy and ruff are clean. I haven't committed anything.

**Root cause:** `to_node` in `sqlglot/lineage.py` only handled PIVOT. The branch was gated on `not pivots[0].unpivot`, so every UNPIVOT column fell through to the generic leaf.

**Changes in `sqlglot/lineage.py`:**
- **Value columns** (`score`) map to the IN-list columns (`jan`, `feb`). Multi-value unpivots (`(a, b) FOR ...`) are
…[593 chars elided]…
e `reference_node_name` logic moved into `_reference_node_name`. The pivot downstream loop was reading that variable without assigning it.

**Tests:** I added `test_unpivot_with_cte` to `tests/test_lineage.py`. I didn't change any existing test. I also checked a real-table UNPIVOT, a derived-table UNPIVOT, a multi-value UNPIVOT, and an aliased IN label; all resolve to the right source columns.

**Not fixed:** PIVOT over a CTE returns the same result before and after this change. Both give `SALES.JAN` for the aggregated column, so I didn't touch that path beyond the shared `cte_sources` lookup.
