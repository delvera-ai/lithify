# trajectory base-1

final message:
`lineage()` now traces UNPIVOT value columns back to their source columns. For your example, `score` reaches `SRC.JAN`/`SRC.FEB` and then `SALES.JAN`/`SALES.FEB`. The full suite passes (1116 tests), and ruff check and format are clean.

**The cause:** the lineage code only handled PIVOT. The UNPIVOT branch was excluded by `not pivots[0].unpivot`, so every column from the UNPIVOT fell through to a leaf on the UNPIVOT itself, which is the phantom you saw.

**The fix** (in `sqlglot/lineage.py`):
- **Value columns** (`score`) map to the matching IN-list columns (`jan`, `feb`). Multi-value tuples such as `((a, b) AS 'x', ...)` are matched by position.
- **Name column** (`metric_name`) has no source column; its values are the IN-list labels. It now ends in a leaf whose source is the IN list (`METRIC_NAME IN (SRC.JAN, SRC.FEB)`), rather than a phantom column on the input.
- **Pass-through columns** (`id`) also used to stop at a phantom. They now recurse into the CTE and reach `SALES.ID`.

I took the CTE scope from `scope.cte_sources`, because `scope.sources` gets overwritten by the pivot registration for a CTE source. I checked that aliased CTEs, derived-table sources, and physical tables also resolve.

**Tests:** I added `test_unpivot_with_cte` to `tests/test_lineage.py` and didn't touch any existing test.

**Not covered:**
- I didn't add a test for a multi-value tuple UNPIVOT, so that positional mapping is verified only by reading the code.
- Lineage through a pivoted CTE for PIVOT (not UNPIVOT) is unchanged. I didn't check whether it has the same phantom-column problem.

I haven't committed these changes.

## events
[tool_use Bash] {"command": "rtk grep -n -i \"unpivot\\|pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -60; cat > /tmp/repro_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\nsql = '''\nWITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score\nFROM src UNPIVOT (score FOR metric_name IN (jan, feb))\n'''\nschema = {\"sales\": {\"id\": \"in
…[124 chars elided]…
ema, dialect=\"snowflake\")\n    print(col)\n    for n in node.walk():\n        print(\"  \", n.name, \"|\", n.source.sql(dialect=\"snowflake\") if n.source else None)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unpivot.py').read())\"", "description": "Search pivot handling and reproduce the bug"}
[tool_result] (eval):1: command not found: rtk
score
   SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.SCORE AS SCORE FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
   SRC.SCORE | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
metric_name
   METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.METRIC_NAME AS METRIC_NAME FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
   SRC.METRIC_NAME | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
[assistant] Reproduced: both `score` and `metric_name` stop at a phantom column on the `src` relation. Next I'll find where pivots are handled in scope and qualification.
[tool_use Bash] {"command": "grep -n -i \"pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/qualify_tables.py sqlglot/optimizer/annotate_types.py | head -60; grep -n \"class Pivot\" -A 25 sqlglot/expressions.py | head -50", "description": "Search pivot handling in optimizer and expressions"}
[tool_result] sqlglot/optimizer/qualify_tables.py:128:            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py:129:                _set_alias(pivot, canonical_aliases)
sqlglot/optimizer/qualify_tables.py:135:                # When the name is empty, it means that we have a non-table source, e.g. a pivoted cte
sqlglot/optimizer/qualify_tables.py:138:                if pivot := seq_get(source.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py
…[4880 chars elided]…
t("pivots") or []
sqlglot/optimizer/scope.py:514:        return self._pivots
sqlglot/optimizer/scope.py:844:                # it is pivoted, because then we get back a new table and hence a new source.
sqlglot/optimizer/scope.py:845:                pivots = expression.args.get("pivots")
sqlglot/optimizer/scope.py:846:                if pivots:
sqlglot/optimizer/scope.py:847:                    sources[pivots[0].alias] = expression
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 340,480p sqlglot/lineage.py; grep -rn \"class Pivot(\" -A 30 sqlglot/expressions/*.py | head -45", "description": "Read lineage pivot handling and Pivot class"}
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
…[7322 chars elided]…
st[Expr]:
sqlglot/expressions/query.py-1772-        return self.args.get("fields", [])
sqlglot/expressions/query.py-1773-
sqlglot/expressions/query.py-1774-    def output_columns(self, pre_pivot_columns: t.Iterable[str]) -> dict[str, str]:
sqlglot/expressions/query.py-1775-        """
sqlglot/expressions/query.py-1776-        Returns an ordered map of post-rename output column name -> pre-rename
sqlglot/expressions/query.py-1777-        source-side name, in the order the (UN)PIVOT produces them.
[assistant] The pivot branch is gated on `not pivots[0].unpivot`, so UNPIVOT columns fall through to the final leaf, which is the phantom. Next I'll check how the parser stores UNPIVOT's value, name, and IN-list parts.
[tool_use Bash] {"command": "sed -n 1774,1830p sqlglot/expressions/query.py; grep -n \"def _parse_pivot\" -A 75 sqlglot/parser.py | grep -n \"unpivot\\|fields\\|columns\\|expressions\\|value\\|name\" | head -50; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM src UNPIVOT (score FOR metric_name IN (jan AS j, feb))', read='snowflake')\np=e.find(sqlglot.exp.Pivot); print(repr(p)[:1500])\n\"", "description": "Inspect UNPIVOT output_columns and AST shape"}
[tool_result]     def output_columns(self, pre_pivot_columns: t.Iterable[str]) -> dict[str, str]:
        """
        Returns an ordered map of post-rename output column name -> pre-rename
        source-side name, in the order the (UN)PIVOT produces them.

        For callers that just want the names, iterate the dict (or call .keys()):
            >>> from sqlglot import parse_one, exp
            >>> piv = parse_one("SELECT * FROM t UNPIVOT(val FOR name IN (a, b))").find(exp.Pivot)
            >>> list(piv
…[4130 chars elided]…
elds:
167:5263-                pivot_field_expressions = pivot_field.expressions
Pivot(
  expressions=[
    Identifier(this=score, quoted=False)],
  fields=[
    In(
      this=Identifier(this=metric_name, quoted=False),
      expressions=[
        PivotAlias(
          this=Column(
            this=Identifier(this=jan, quoted=False)),
          alias=Identifier(this=j, quoted=False)),
        Column(
          this=Identifier(this=feb, quoted=False))])],
  unpivot=True,
  default_on_null=False)
[assistant] The AST gives me what I need: `expressions` holds the value identifiers, and `fields[0]` is an `In` whose `this` is the name identifier and whose entries hold the source columns (optionally wrapped in `PivotAlias`). Before designing the fix, I want to see how scope registers a pivoted CTE source, since that determines whether pass-through columns like `id` can recurse into the CTE.
[tool_use Bash] {"command": "sed -n 832,852p sqlglot/optimizer/scope.py; grep -n \"def test.*pivot\\|def test.*unpivot\" -i tests/test_lineage.py tests/test_optimizer.py | head; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.lineage import lineage\nsql='''WITH src AS (SELECT id, jan, feb FROM sales) SELECT id, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''\ns={'sales': {'id':'int','jan':'int','feb':'int'}}\nn=lineage('id',sql,schema=s,dialect='snowflake')\nfor x in n.walk(): print(x.name,'|',x.source.sql(dialect='snowflake') if x.source else None)\n\"", "description": "Read scope source registration and test implicit column lineage"}
[tool_result]     expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless
     
…[702 chars elided]…
st_pivot_with_implicit_column_of_pivoted_source(self) -> None:
tests/test_lineage.py:670:    def test_pivot_with_implicit_column_of_pivoted_source_and_cte(self) -> None:
tests/test_lineage.py:733:    def test_pivot_with_subquery(self) -> None:
ID | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES) SELECT SRC.ID AS ID FROM SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
SRC.ID | SRC AS SRC UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SRC
[assistant] The pivoted-CTE case registers the pivoted `Table` itself as the source, so pass-through columns also stop there. I'll check what the existing PIVOT lineage tests expect for that pattern before deciding how far the fix should go.
[tool_use Bash] {"command": "sed -n 607,690p tests/test_lineage.py; grep -n -i \"unpivot\" tests/test_lineage.py tests/dialects/*.py | head -20", "description": "Read existing PIVOT lineage tests"}
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
      
…[4787 chars elided]…
les"
tests/dialects/test_duckdb.py:2363:            "WITH unpivot_alias AS (UNPIVOT monthly_sales ON COLUMNS(* EXCLUDE (empid, dept)) INTO NAME month VALUE sales) SELECT * FROM unpivot_alias"
tests/dialects/test_duckdb.py:2366:            "SELECT * FROM (UNPIVOT monthly_sales ON COLUMNS(* EXCLUDE (empid, dept)) INTO NAME month VALUE sales) AS unpivot_alias"
tests/dialects/test_snowflake.py:855:            "SELECT * FROM table AT (TIMESTAMP => '2024-07-24') UNPIVOT(a FOR b IN (c)) AS pivot_table"
[assistant] The existing PIVOT tests only cover physical tables, so pivoted CTE sources have no recursion path today. Before writing anything, I need to confirm whether a CTE's scope is still reachable from the pivot's scope after `scope.sources` is overwritten.
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def sources\\|self.sources\\b\" sqlglot/optimizer/scope.py | head -30; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nsql='''WITH src AS (SELECT id, jan, feb FROM 
…[69 chars elided]…
an, feb))'''\ne=qualify(parse_one(sql,read='snowflake'),schema={'sales': {'id':'int','jan':'int','feb':'int'}},dialect='snowflake')\nprint(e.sql(dialect='snowflake'))\nroot=build_scope(e)\nfor s in root.traverse():\n    print(s.scope_type, list(s.sources.keys()), [type(v).__name__ for v in s.sources.values()], [p.alias for p in s.pivots])\n\"", "description": "Check scope sources for pivoted CTE"}
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
…[347 chars elided]…
5:                yield from _traverse_scope(Scope(query, cte_sources=scope.cte_sources))
778:                cte_sources=sources,
791:    scope.cte_sources.update(sources)
WITH "SRC" AS (SELECT "SALES"."ID" AS "ID", "SALES"."JAN" AS "JAN", "SALES"."FEB" AS "FEB" FROM "SALES" AS "SALES") SELECT "SRC"."ID" AS "ID", "SRC"."SCORE" AS "SCORE" FROM "SRC" AS "SRC" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SRC"
ScopeType.CTE ['SALES'] ['Table'] []
ScopeType.ROOT ['SRC'] ['Table'] ['SRC']
[assistant] `scope.cte_sources` keeps the CTE's `Scope` under its name even after `scope.sources` is overwritten by the pivot registration, so the value and pass-through columns can recurse into the CTE. Next I'll check `to_node`'s signature and the module helpers so the new code matches them.
[tool_use Bash] {"command": "grep -n \"^def \\|^class \" sqlglot/lineage.py; grep -n \"^def to_node\" -A 22 sqlglot/lineage.py", "description": "List lineage functions and to_node signature"}
[tool_result] 23:class Node:
81:def lineage(column: str | exp.Column, sql: str | exp.Expr, **kwargs: t.Any) -> Node: ...
85:def lineage(column: None, sql: str | exp.Expr, **kwargs: t.Any) -> dict[str, Node]: ...
88:def lineage(
191:def to_node(
482:class GraphHTML:
191:def to_node(
192-    column: str | int,
193-    scope: Scope,
194-    dialect: DialectType,
195-    scope_name: str | None = None,
196-    upstream: Node | None = None,
197-    source_name: str | None = None,
198-    reference_node_name: str | 
…[218 chars elided]…
 | None = None,
203-) -> Node:
204-    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)
205-
206-    if _cache is not None and cache_key in _cache:
207-        cached_node = _cache[cache_key]
208-        if upstream:
209-            upstream.downstream.append(cached_node)
210-        return cached_node
211-
212-    # Find the specific select clause that is the source of the column we want.
213-    # This can either be a specific, named select or a generic `*` clause.
[assistant] I have what I need. The plan:

- Add a helper that maps each UNPIVOT value column to the IN-list source columns and returns the name column.
- Add an `unpivot` branch in `to_node`. Value columns recurse into the upstream relation, pass-through columns do the same by name, and the name column becomes a leaf on the IN list.

Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "def to_node(\n    column: str | int,", "new_string": "def _unpivot_outputs(unpivot: exp.Pivot) -> tuple[str, dict[str, list[str]]]:\n    \"\"\"\n    Returns the UNPIVOT's name column and a map of each value column to th
…[447 chars elided]…
r entry in unpivot.fields[0].expressions:\n        entry = entry.this if isinstance(entry, exp.PivotAlias) else entry\n        entry_columns = entry.expressions if isinstance(entry, exp.Tuple) else [entry]\n        for value, column in zip(value_columns, entry_columns):\n            mapping[value.name].append(column.name)\n    return name_column, mapping\n\n\ndef to_node(\n    column: str | int,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "            for col_index in range(i, len(pivot_columns), pivot_aggs_count):\n                pivot_column_mapping[pivot_columns[col_index].name] = agg_cols\n\n    for c in source_columns:", "new_string": "            for col_index in range(i, len(pivot_columns), pivot_aggs_count):\n                pivot_column_mapping[pivot_columns[col_index].name] = agg_cols\n\n    unpivot = pivots[0] if len(pivots) == 1 and pivots[0].unpivot else None\n    if unpivot:\n        unpivot_name_column, unpivot_column_mapping = _unpivot_outputs(unpivot)\n\n    for c in source_columns:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py", "old_string": "        elif pivot and pivot.alias_or_name == c.table:\n            downstream_columns = []", "new_string": "        elif unpivot and unpivot.alias_or_name == c.table:\n            unpivot_source = unpivot.parent\n     
…[1382 chars elided]…
mn, table=unpivot_source.alias_or_name).sql(comments=False),\n                        source=unpivot_source,\n                        expression=unpivot_source,\n                    )\n                    node.downstream.append(leaf)\n                    if on_node:\n                        on_node(leaf)\n        elif pivot and pivot.alias_or_name == c.table:\n            downstream_columns = []"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Edits are in. Now I'll rerun the reproduction and a few variants: the name column, multi-value tuples, an aliased CTE, a subquery source, and a physical table.
[tool_use Bash] {"command": "cat > /tmp/check_unpivot.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = {\n    \"repro score\": (\"score\", '''WITH src AS (SELECT id, jan, feb FROM sales)\nSELECT id, metric_name, score FROM src UNPIVOT (score FOR metric_name IN (jan, feb))'''),\n    \"repro
…[897 chars elided]…
alect=\"snowflake\")\n        for n in root.walk():\n            print(\"   \", n.name, \"|\", n.source.sql(dialect=\"snowflake\")[:90] if n.source else None)\n    except Exception as e:\n        print(\"   ERROR\", type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/check_unpivot.py", "description": "Run lineage checks on UNPIVOT variants"}
[tool_result] == repro score
    SCORE | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES
    SRC.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
    SALES.JAN | SALES AS SALES
    SRC.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
    SALES.FEB | SALES AS SALES
== repro name
    METRIC_NAME | WITH SRC AS (SELECT SALES.ID AS ID, SALES.JAN AS JAN, SALES.FEB AS FEB FROM SALES AS SALES
    SRC.METRIC_NAME | METRIC_NAME IN (SRC.JAN, SRC.FEB)
== passthrough id
    ID 
…[545 chars elided]…
D, SALES.JAN AS JAN, SALES.FEB AS FEB F
    _0.JAN | SELECT SALES.JAN AS JAN FROM SALES AS SALES
    SALES.JAN | SALES AS SALES
    _0.FEB | SELECT SALES.FEB AS FEB FROM SALES AS SALES
    SALES.FEB | SALES AS SALES
== physical
    SCORE | SELECT SALES.SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB
    SALES.JAN | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
    SALES.FEB | SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) AS SALES
[assistant] All variants resolve to the source columns, and the name column ends at the IN list. I'll add regression tests next to the existing pivot lineage tests, following their style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py", "old_string": "    def test_table_udtf_snowflake(self) -> None:", "new_string": "    def test_unpivot_with_cte(self) -> None:\n        sql = \"\"\"\n        WITH src AS (SELECT id, jan, feb FROM sales)\n        SELECT id, metric_na
…[346 chars elided]…
with(\"SRC.\") or n.name.startswith(\"SALES.\")),\n            [\"SALES.FEB\", \"SALES.JAN\", \"SRC.FEB\", \"SRC.JAN\"],\n        )\n\n        node = lineage(\"metric_name\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.METRIC_NAME\")\n        self.assertFalse(node.downstream[0].downstream)\n\n    def test_table_udtf_snowflake(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-134030-lineage-sqlglot-lineage-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -25; $PY -I -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -5; $PY -I -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3", "description": "Run lineage tests and ruff checks"}
[tool_result] .......................................                                  [100%]
39 passed in 0.11s
All checks passed!
Would reformat: sqlglot/lineage.py
Would reformat: tests/test_lineage.py
2 files would be reformatted
[assistant] All 39 lineage tests pass and ruff check is clean. `ruff format` wants changes in both files, so I'll check whether those are from my lines or pre-existing.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m ruff format --diff sqlglot/lineage.py tests/test_lineage.py 2>&1 | head -60; git stash list | head -0; git show HEAD:sqlglot/lineage.py > /tmp/orig_lineage.py && $PY -I -m ruff format --check /tmp/orig_lineage.py 2>&1 | tail -1", "description": "Show ruff format diff for the edited files"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -446,7 +446,11 @@
             unpivot_source = unpivot.parent
             if c.name == unpivot_name_column:
                 # The name column is produced from the IN list's labels, not from any source column
-                leaf = Node(name=c.sql(comments=False), source=unpivot.fields[0], expression=unpivot.fields[0])
+                leaf = Node(
+                    name=c.sql(comments=False),
+                    source=unpivot.fields[0],
+
…[811 chars elided]…
hema, dialect="snowflake")
         self.assertEqual(
-            sorted(n.name for n in node.walk() if n.name.startswith("SRC.") or n.name.startswith("SALES.")),
+            sorted(
+                n.name
+                for n in node.walk()
+                if n.name.startswith("SRC.") or n.name.startswith("SALES.")
+            ),
             ["SALES.FEB", "SALES.JAN", "SRC.FEB", "SRC.JAN"],
         )
 

2 files would be reformatted
head: illegal line count -- 0
1 file already formatted
[assistant] All of the format differences are in my new lines, and the original file was already clean, so I'll apply the formatter and then run the whole test suite with the project's command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m ruff format sqlglot/lineage.py tests/test_lineage.py && $PY -I -m ruff check sqlglot/lineage.py tests/test_lineage.py | tail -1 && $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Format edited files and run full test suite"}
[tool_result] 2 files reformatted
All checks passed!
........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 27%]
........................................ [ 30%]
.......................................................................................
…[434 chars elided]…
.................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1116 passed, 18166 subtests passed in 50.58s
[This command modified 2 files you've previously read: sqlglot/lineage.py, tests/test_lineage.py. Call Read before editing.]
[assistant] The full suite passed (1116 tests). The "changed on disk" notice is from my own `ruff format` run. I'll confirm the final diff contains only my intended changes.
[tool_use Bash] {"command": "git status --short && git diff --stat && PY=<work>/env-sqlglot/bin/python && $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -1", "description": "Confirm changed files and rerun lineage tests"}
[tool_result]  M sqlglot/lineage.py
 M tests/test_lineage.py
 sqlglot/lineage.py    | 68 +++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_lineage.py | 22 +++++++++++++++++
 2 files changed, 90 insertions(+)
39 passed in 0.08s
[assistant] `lineage()` now traces UNPIVOT value columns back to their source columns. For your example, `score` reaches `SRC.JAN`/`SRC.FEB` and then `SALES.JAN`/`SALES.FEB`. The full suite passes (1116 tests), and ruff check and format are clean.

**The cause:** the lineage code only handled PIVOT. The UNPIVOT branch was excluded by `not pivots[0].unpivot`, so every column from the UNPIVOT fell through to a leaf on the UNPIVOT itself, which is the phantom you saw.

**The fix** (in `sqlglot/lineage.py`):
- **Value columns** (`score`) map to the matching IN-list columns (`jan`, `feb`). Multi-value tuples s
…[428 chars elided]…
e.cte_sources`, because `scope.sources` gets overwritten by the pivot registration for a CTE source. I checked that aliased CTEs, derived-table sources, and physical tables also resolve.

**Tests:** I added `test_unpivot_with_cte` to `tests/test_lineage.py` and didn't touch any existing test.

**Not covered:**
- I didn't add a test for a multi-value tuple UNPIVOT, so that positional mapping is verified only by reading the code.
- Lineage through a pivoted CTE for PIVOT (not UNPIVOT) is unchanged. I didn't check whether it has the same phantom-column problem.

I haven't committed these changes.
