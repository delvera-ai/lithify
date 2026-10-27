# trajectory base-1

final message:
UNPIVOT lineage is now correct for multi-value UNPIVOT, and the full suite passes (1119 tests, 18166 subtests). The changes are in the working tree, not committed.

**What was wrong.** The name and value columns were both mapped to every IN-list source column. For `UNPIVOT((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))`, `a` and `b` each traced back to all four of `jan`, `mar`, `feb`, `apr`. Each value column should trace only to its own position in each tuple.

**What changed.**
- `sqlglot/lineage.py`, `_pivot_column_mapping`: the i-th value column now maps to the i-th source column of each IN-list tuple. So `a` → `jan`, `feb` and `b` → `mar`, `apr`. The name column still maps to every IN-list column, as before.
- `tests/test_lineage.py`: two new tests.
  - `test_unpivot_multiple_value_columns` covers the multi-value case above.
  - `test_unpivot_aliased_in_list_and_expression` covers aliased IN entries (`jan AS 'J'`) and an expression over the value column (`score * 2 AS x`).

**What I checked and found already correct.** Pass-through columns (`id`, `region`) trace to the unpivot source, including through table aliases, subqueries, CTEs, `INCLUDE NULLS`, a `WHERE` clause, and a join with an unpivoted table. Single-value UNPIVOT lineage was unchanged. The "Cannot find column" errors I hit while probing were my own mistake: I asked for the source name when the query outputs an alias.

**Checks.** Lineage tests: 42 pass. Full suite: 1119 pass. `ruff check` passes, and `ruff format` reformatted `lineage.py` (the only formatting change).

I did not commit. The scratch probe scripts are in `/tmp/unpivot_probe`, outside the repo.

## events
[assistant] I'll start by finding the existing UNPIVOT lineage code and its tests.
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\\|pivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50; grep -rln -i \"unpivot\" tests/ | head", "description": "Locate UNPIVOT references in lineage and optimizer"}
[tool_result] 4fb1cbfe7 lithify: probe base
7f77fe5f3 eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/lineage.py:374:    pivots = scope.pivots
sqlglot/lineage.py:375:    pivot = pivots[0] if len(pivots) == 1 else None
sqlglot/lineage.py:376:    pivot_column_mapping = _pivot_column_mapping(pivot) if pivot else {}
sqlglot/lineage.py:404:        elif pivot and pivot.alias_or_name == c.table:
sqlglot/lineage.py:408:            if column_name in pivot_column_mapping:
sqlglot/lineage.py:409: 
…[3858 chars elided]…
  val_expr = seq_get(pivot.expressions, 0)
sqlglot/optimizer/annotate_types.py:682:            for name in pivot.output_columns(src_types)
sqlglot/optimizer/annotate_types.py:686:    def _get_pivot_column_types(
tests/test_optimizer.py
tests/test_transpile.py
tests/test_lineage.py
tests/dialects/test_snowflake.py
tests/dialects/test_redshift.py
tests/dialects/test_databricks.py
tests/dialects/test_oracle.py
tests/dialects/test_bigquery.py
tests/dialects/test_duckdb.py
tests/fixtures/identity.sql
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "offset": 340, "limit": 150}
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
…[6032 chars elided]…
 for field in pivot.fields
479	            for e in field.expressions
480	            for col in e.find_all(exp.Column)
481	        ]
482	        for value_column in pivot.expressions:
483	            for identifier in value_column.find_all(exp.Identifier):
484	                mapping[identifier.name] = unpivot_columns
485	        for field in pivot.fields:
486	            if isinstance(field, exp.In):
487	                mapping[field.this.name] = unpivot_columns
488	
489	        return mapping
[tool_use Bash] {"command": "grep -n -i \"unpivot\" tests/test_lineage.py", "description": "Find UNPIVOT tests in lineage test file"}
[tool_result] 688:    def test_unpivot(self) -> None:
691:        FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
704:    def test_unpivot_with_cte(self) -> None:
710:        FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "offset": 640, "limit": 110}
[tool_result] 640	            SELECT
641	                a as other_a
642	            FROM sample_data
643	            PIVOT (
644	                sum(value)
645	                FOR category IN ('a', 'b')
646	            )
647	        )
648	        select other_a from t
649	        """
650	        node = lineage("other_a", sql)
651	
652	        self.assertEqual(node.downstream[0].name, "t.other_a")
653	        self.assertEqual(node.downstream[0].reference_node_name, "t")
654	        self.assertEqual(node.down
…[3554 chars elided]…
flake")
737	
738	        self.assertEqual(lateral_node.name, "EXTERNAL_ID")
739	        self.assertEqual(table_node.name, "EXTERNAL_ID")
740	
741	        lateral_node = lateral_node.downstream[0]
742	        table_node = table_node.downstream[0]
743	
744	        self.assertEqual(lateral_node.name, "F.VALUE")
745	        self.assertEqual(
746	            lateral_node.source.sql("snowflake"),
747	            "LATERAL FLATTEN(RAW.EVENTS) AS F(SEQ, KEY, PATH, INDEX, VALUE, THIS)",
748	        )
749	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "offset": 489, "limit": 30}
[tool_result] 489	        return mapping
490	
491	    # For each aggregation function, the pivot creates a new column for each field in category
492	    # combined with the aggfunc. So the columns parsed have this order: cat_a_value_sum, cat_a,
493	    # b_value_sum, b. Because of this step wise manner the aggfunc 'sum(value) as value_sum'
494	    # belongs to the column indices 0, 2, and the aggfunc 'max(price)' without an alias belongs
495	    # to the column indices 1, 3. Here, only the columns used in the
…[363 chars elided]…
ns)
502	
503	    mapping = {}
504	    for i, agg in enumerate(pivot.expressions):
505	        agg_cols = list(agg.find_all(exp.Column))
506	        for col_index in range(i, len(pivot_columns), pivot_aggs_count):
507	            mapping[pivot_columns[col_index].name] = agg_cols
508	    return mapping
509	
510	
511	class GraphHTML:
512	    """Node to HTML generator using vis.js.
513	
514	    https://visjs.github.io/vis-network/docs/network/
515	    """
516	
517	    def __init__(
518	        self,
[assistant] The current code maps the value and name columns to every IN-list column and sends pass-through columns to the unpivot's source. Before changing anything, I'll run the existing lineage tests and probe several query shapes to find where it actually breaks.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Run lineage tests with project python"}
[tool_result] <work>/env-sqlglot/bin/python
........................................                                 [100%]
40 passed in 0.33s
[assistant] Existing lineage tests pass (40). Now I'll probe a set of UNPIVOT shapes with a script kept outside the repo.
[tool_use Bash] {"command": "mkdir -p /tmp/unpivot_probe && cat > /tmp/unpivot_probe/probe.py <<'EOF'\nfrom sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"text\"}}\n\ndef show(node, indent=0):\n    print(\"  \" * indent + f\"{node.name}  [src={node.source.sql()[:60] if node.source is not None else None}]\")\n    for d in node.downstream:\
…[2304 chars elided]…
ype(e).__name__, e)\nEOF\ncd /tmp/unpivot_probe && PYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1 <work>/env-sqlglot/bin/python -I probe.py 2>&1", "description": "Probe UNPIVOT lineage across query shapes"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/private/tmp/unpivot_probe/probe.py", line 1, in <module>
    from sqlglot.lineage import lineage
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores `PYTHONPATH`, so I'll drop it; this is my own script, not untrusted input.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && PYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1 <work>/env-sqlglot/bin/python probe.py 2>&1", "description": "Run UNPIVOT lineage probe without -I flag"}
[tool_result] ================================================================================
score :: SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  SCORE  [src=SELECT SALES.SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCOR]
    SALES.JAN  [src=SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (SALES.JAN, ]
    SALES.FEB  [src=SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (SALES.JAN, ]
================================================================================
id
…[6245 chars elided]…
(SCORE FOR METRIC_NAME IN (SALES.JAN, ]
================================================================================
region :: SELECT sales.region FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  REGION  [src=SELECT SALES.REGION AS REGION FROM SALES AS SALES UNPIVOT(SC]
    SALES.REGION  [src=SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (SALES.JAN, ]
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1
[assistant] Most shapes already work. Three failures stand out:

- `metric_name` with aliased IN entries (`jan AS 'J'`) raises "Cannot find column".
- `score * 2` inside an expression raises the same error.
- The multi-value query I wrote was wrong, since its outputs are `a` and `b`, not `score`.

I'll get tracebacks for the two errors and check the multi-value case with the correct columns.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && cat > probe2.py <<'EOF'\nimport traceback\nfrom sqlglot.lineage import lineage\nfrom sqlglot import parse_one\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"text\", \"mar\": \"int\", \"apr\": \"int\"}}\nfor col, sql in [\n    (\"metric_name\", \"SELECT metric_name AS m FROM sales UNPIVOT (score FOR metric_name IN (jan
…[710 chars elided]…
 for d in n.downstream])\nEOF\nPYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1 <work>/env-sqlglot/bin/python probe2.py 2>&1 | tail -80", "description": "Get tracebacks and check multi-value UNPIVOT lineage"}
[tool_result] Traceback (most recent call last):
  File "/private/tmp/unpivot_probe/probe2.py", line 10, in <module>
    lineage(col, sql, schema=schema, dialect="snowflake")
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", line 158, in lineage
    raise SqlglotError(f"Cannot find column '{column_name}' in query.")
sqlglot.errors.SqlglotError: Cannot find column 'METRIC_NAME' in query.
Traceback (most recent call last):
  
…[491 chars elided]…
robe2.py", line 13, in <module>
    print(repr(parse_one("SELECT a, b FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))", read="snowflake").args["from"].this.args["pivots"][0]))
               ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'from'
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1
[assistant] Both errors are mistakes in my probe, not bugs. The query outputs `m` and `x`, so asking for `metric_name` or `score` correctly fails. I'll re-probe using the output names and fix the parse call.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && cat > probe3.py <<'EOF'\nfrom sqlglot.lineage import lineage\nfrom sqlglot import parse_one\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"text\", \"mar\": \"int\", \"apr\": \"int\"}}\ndef show(node, indent=1):\n    print(\"  \" * indent + node.name)\n    for d in node.downstream: show(d, indent + 1)\nfor col, sql in 
…[1019 chars elided]…
rint(\"  ERROR\", type(e).__name__, e)\nEOF\nPYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1 <work>/env-sqlglot/bin/python probe3.py 2>&1", "description": "Re-probe UNPIVOT with correct output column names"}
[tool_result] ============================================================
m :: SELECT metric_name AS m FROM sales UNPIVOT (score FOR metric_name IN (jan AS 'J', feb AS 'F'))
  M
    SALES.JAN
    SALES.FEB
============================================================
x :: SELECT score * 2 AS x FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  X
    SALES.JAN
    SALES.FEB
============================================================
x :: SELECT id + score AS x FROM sales UNPIVOT (score FOR metric_name
…[710 chars elided]…
=================================
nm :: SELECT a, b, nm FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))
  NM
    SALES.JAN
    SALES.MAR
    SALES.FEB
    SALES.APR
============================================================
score :: SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  SCORE
    SALES.JAN
    SALES.FEB
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1
[assistant] Two real problems show up. In multi-value UNPIVOT, output `a` maps to all four source columns, but it should map only to the first element of each IN tuple (`jan`, `feb`), and `b` only to the second (`mar`, `apr`). I'll inspect the AST shape for that case and check a join-with-UNPIVOT query before changing anything.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && cat > probe4.py <<'EOF'\nfrom sqlglot import parse_one, exp\nfrom sqlglot.lineage import lineage\nq = parse_one(\"SELECT a, b FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))\", read=\"snowflake\")\np = q.find(exp.Pivot)\nprint(\"expressions:\", [repr(e) for e in p.expressions])\nprint(\"fields:\", [type(f).__name__ for f in p.field
…[703 chars elided]…
ept Exception as e: print(\"join ERR\", e)\nEOF\nPYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1 <work>/env-sqlglot/bin/python probe4.py 2>&1", "description": "Inspect multi-value UNPIVOT AST and join case"}
[tool_result] expressions: ['Tuple(\n  expressions=[\n    Identifier(this=a, quoted=False),\n    Identifier(this=b, quoted=False)])']
fields: ['In']
 field.this: Identifier(this=nm, quoted=False)
 field.expressions: ["PivotAlias:(jan, mar) AS 'x'", "PivotAlias:(feb, apr) AS 'y'"]
unpivot: True
join nm: ['SALES.JAN', 'SALES.FEB']
join id: ['T.ID']
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1
[assistant] The AST confirms the shape: a multi-value UNPIVOT stores one `Tuple` of value identifiers in `pivot.expressions`, and each IN entry's `.this` is a `Tuple` of source columns. Position `i` in each tuple pairs with value `i`. The join case is correct. I'll make `_pivot_column_mapping` pair value columns positionally with the IN-list tuples.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1282 chars elided]…
     mapping[value_column.name] = [\n                col\n                for source in in_sources\n                for col in (source.expressions[i] if isinstance(source, exp.Tuple) else source).find_all(exp.Column)\n            ]\n\n        for field in pivot.fields:\n            if isinstance(field, exp.In):\n                mapping[field.this.name] = unpivot_columns\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll rerun the probes and the existing lineage tests against the change.
[tool_use Bash] {"command": "cd /tmp/unpivot_probe && export PYTHONPATH=~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1; PY=<work>/env-sqlglot/bin/python; $PY probe3.py 2>&1 | sed -n '/nm ::/,$p' | head -5; $PY probe3.py 2>&1 | grep -A5 \"^a ::\\|^b ::\"; cd $PYTHONPATH && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Rerun probes and lineage tests after fix"}
[tool_result] nm :: SELECT a, b, nm FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))
  NM
    SALES.JAN
    SALES.MAR
    SALES.FEB
a :: SELECT a, b FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))
  A
    SALES.JAN
    SALES.FEB
============================================================
b :: SELECT a, b FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))
  B
    SALES.MAR
    SALES.APR
============================================================
nm :: SELECT a, b, nm FROM sales UNPIVOT ((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))
........................................                                 [100%]
40 passed in 0.09s
[assistant] Multi-value lineage is now positional (`a` ← jan, feb; `b` ← mar, apr), and the 40 existing lineage tests still pass. Next I'll add a regression test next to the existing UNPIVOT tests.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\
…[1392 chars elided]…
\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\n\n        node = lineage(\"m\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.JAN\", \"SALES.FEB\"])\n\n        node = lineage(\"x\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.JAN\", \"SALES.FEB\"])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-173833-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3", "description": "Run lineage tests, then ruff format and lint checks"}
[tool_result] ..........................................                               [100%]
42 passed in 0.14s
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/lineage.py && git diff --stat && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Apply ruff formatting and run full test suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bw0e9ulbo). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-173833-lineage-further-improve-lineage-base-1/c4c309c6-1ccb-4032-800b-39b981240c2a/tasks/bw0e9ulbo.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite is running in the background. Meanwhile I'll review the diff, since `lineage.py` was reformatted.
[tool_use Bash] {"command": "git diff -- sqlglot/lineage.py", "description": "Show current lineage.py diff"}
[tool_result] diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 6db18a09f..ea7cb4783 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -471,17 +471,30 @@ def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
     mapping: dict[str, list[exp.Column]] = {}
 
     if pivot.unpivot:
-        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
-        # are derived from the IN-list source columns
-        unpivot_columns = [
-            col
+  
…[956 chars elided]…
xpressions
+        )
+        for i, value_column in enumerate(value_columns):
+            mapping[value_column.name] = [
+                col
+                for source in in_sources
+                for col in (
+                    source.expressions[i] if isinstance(source, exp.Tuple) else source
+                ).find_all(exp.Column)
+            ]
+
         for field in pivot.fields:
             if isinstance(field, exp.In):
                 mapping[field.this.name] = unpivot_columns
[assistant] The diff matches the intended change. I'll wait for the full suite to finish.
[tool_use Bash] {"command": "sleep 100; tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-173833-lineage-further-improve-lineage-base-1/c4c309c6-1ccb-4032-800b-39b981240c2a/tasks/bw0e9ulbo.output", "description": "Check background full test suite output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-173833-lineage-further-improve-lineage-base-1/c4c309c6-1ccb-4032-800b-39b981240c2a/tasks/bw0e9ulbo.output. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Bash] {"command": "tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-173833-lineage-further-improve-lineage-base-1/c4c309c6-1ccb-4032-800b-39b981240c2a/tasks/bw0e9ulbo.output", "description": "Read background test suite output tail"}
[tool_result] 1 file reformatted
 sqlglot/lineage.py    | 29 +++++++++++++++++++++--------
 tests/test_lineage.py | 31 +++++++++++++++++++++++++++++++
 2 files changed, 52 insertions(+), 8 deletions(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 580 $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite in foreground", "timeout": 590000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite in foreground", "timeout": 590000}
[tool_result] ........................................ [ 30%]
........................................................................................ [ 38%]
...................................................................................................................... [ 48%]
............................ [ 51%]
................................................................................................................................................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
..............................................            [100%]
1119 passed, 18166 subtests passed in 70.00s (0:01:10)
[assistant] UNPIVOT lineage is now correct for multi-value UNPIVOT, and the full suite passes (1119 tests, 18166 subtests). The changes are in the working tree, not committed.

**What was wrong.** The name and value columns were both mapped to every IN-list source column. For `UNPIVOT((a, b) FOR nm IN ((jan, mar) AS 'x', (feb, apr) AS 'y'))`, `a` and `b` each traced back to all four of `jan`, `mar`, `feb`, `apr`. Each value column should trace only to its own position in each tuple.

**What changed.**
- `sqlglot/lineage.py`, `_pivot_column_mapping`: the i-th value column now maps to the i-th source column
…[462 chars elided]…
 columns (`id`, `region`) trace to the unpivot source, including through table aliases, subqueries, CTEs, `INCLUDE NULLS`, a `WHERE` clause, and a join with an unpivoted table. Single-value UNPIVOT lineage was unchanged. The "Cannot find column" errors I hit while probing were my own mistake: I asked for the source name when the query outputs an alias.

**Checks.** Lineage tests: 42 pass. Full suite: 1119 pass. `ruff check` passes, and `ruff format` reformatted `lineage.py` (the only formatting change).

I did not commit. The scratch probe scripts are in `/tmp/unpivot_probe`, outside the repo.
