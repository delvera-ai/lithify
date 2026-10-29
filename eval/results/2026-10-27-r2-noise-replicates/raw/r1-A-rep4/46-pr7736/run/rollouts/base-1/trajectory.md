# trajectory base-1

final message:
UNPIVOT lineage now handles multi-value UNPIVOT correctly, and the full suite passes (1120 tests). The changes are uncommitted in the worktree.

**What was wrong**
- **Multi-value UNPIVOT over-approximated.** For `UNPIVOT((a, b) FOR q IN ((jan, feb) AS 'Q1', (mar, apr) AS 'Q2'))`, `a` was reported as coming from all four columns. It should come only from `jan` and `mar`.

**What I changed**
- `sqlglot/lineage.py`, in `_pivot_column_mapping`: each value column now maps only to the IN-list entries at its position in the tuple. The name column still maps to every IN-list entry. `PivotAlias` wrappers are unwrapped so aliased entries such as `jan AS j` resolve to their columns.
- `tests/test_lineage.py`: three new tests:
  - `test_unpivot_multiple_value_columns`
  - `test_unpivot_aliased_in_list`
  - `test_unpivot_passthrough_from_subquery`

**What I checked and left alone**
- Pass-through columns (`id`, `mar`, `u.id`) already traced correctly through subqueries, aliases and CTEs. The new tests lock that in.
- A literal-label IN list such as `IN ('JAN' AS j, 'FEB' AS f)` gives no value-column lineage. Snowflake's UNPIVOT IN-list takes column names, so I treated that query as invalid rather than a case to fix.

**Verification**
- Full suite: `1120 passed` with the harness command.
- `ruff check` passes. I also ran `ruff format` on `lineage.py`, which only re-wrapped my new block.

I did not commit anything. If you want the change as a commit, I can make one with the Co-Authored-By line from the repo instructions.

## events
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50 && grep -rln -i \"unpivot\" tests/ | head", "description": "Locate UNPIVOT references in lineage and optimizer"}
[tool_result] 04f7ac1d5 lithify: probe base
cfe483308 eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/lineage.py:473:    if pivot.unpivot:
sqlglot/lineage.py:474:        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
sqlglot/lineage.py:476:        unpivot_columns = [
sqlglot/lineage.py:484:                mapping[identifier.name] = unpivot_columns
sqlglot/lineage.py:487:                mapping[field.this.name] = unpivot_columns
sqlglot/optimizer/annotate
…[269 chars elided]…
qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
sqlglot/optimizer/qualify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
tests/test_optimizer.py
tests/test_transpile.py
tests/test_lineage.py
tests/dialects/test_databricks.py
tests/dialects/test_snowflake.py
tests/dialects/test_oracle.py
tests/dialects/test_bigquery.py
tests/dialects/test_redshift.py
tests/dialects/test_duckdb.py
tests/dialects/test_pipe_syntax.py
[tool_use Bash] {"command": "sed -n 380,560p sqlglot/lineage.py && git show --stat HEAD~2 | head -5; git log --oneline -i --grep=unpivot -5", "description": "Read lineage pivot handling code"}
[tool_result]         col_source: exp.Table | Scope | None = scope.sources.get(table)

        if isinstance(col_source, Scope):
            reference_node_name = None
            if col_source.scope_type == ScopeType.DERIVED_TABLE and table not in source_names:
                reference_node_name = table
            elif col_source.scope_type == ScopeType.CTE:
                selected_node, _ = scope.selected_sources.get(table, (None, None))
                reference_node_name = selected_node.name if selecte
…[6733 chars elided]…
a1401ffd84eab83cebe593b8f3f8c1ee2992
Author: George Sittas <giwrgos.sittas@gmail.com>
Date:   Thu Jun 11 13:22:12 2026 +0300

    Sync w/ integration tests
74bef2f46 Feat(lineage): add support for `UNPIVOT` (#7729)
a20ec0ee4 fix(optimizer): unpivot annotate types (#7543)
cf0ffd99e fix(optimizer): qualify (UN)PIVOT on CTE sources (#7560)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
[tool_use Bash] {"command": "git show 74bef2f46 --stat && git show 74bef2f46 -- tests/ | head -150 && sed -n 330,380p sqlglot/lineage.py", "description": "Review prior UNPIVOT lineage commit and context"}
[tool_result] commit 74bef2f4617f2fa25881dded12ae3851a7ddfa1f
Author: Jo <46752250+georgesittas@users.noreply.github.com>
Date:   Wed Jun 10 17:00:13 2026 +0300

    Feat(lineage): add support for `UNPIVOT` (#7729)

 sqlglot/lineage.py    | 69 ++++++++++++++++++++++++++++++++++++---------------
 tests/test_lineage.py | 35 ++++++++++++++++++++++++++
 2 files changed, 84 insertions(+), 20 deletions(-)
commit 74bef2f4617f2fa25881dded12ae3851a7ddfa1f
Author: Jo <46752250+georgesittas@users.noreply.github.com>
Dat
…[3635 chars elided]…
 else:
        derived_tables = scope.derived_tables

    source_names = {
        dt.alias: dt.comments[0].split()[1]
        for dt in derived_tables
        if dt.comments and dt.comments[0].startswith("source: ")
    }

    pivots = scope.pivots
    pivot = pivots[0] if len(pivots) == 1 else None
    pivot_column_mapping = _pivot_column_mapping(pivot) if pivot else {}

    for c in source_columns:
        table = c.table
        col_source: exp.Table | Scope | None = scope.sources.get(table)
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[assistant] I'll keep going on the UNPIVOT lineage work. Next I'm probing the current behaviour across several query shapes so I can see which ones are wrong before changing anything.
[tool_use Bash] {"command": "cat > /tmp/probe_unpivot.py <<'EOF'\nfrom sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}}\ncases = [\n    (\"score\", \"SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\"),\n    (\"metric_name\", \"SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name
…[430 chars elided]…
   print(col, \"->\", [d.name for d in node.downstream], \"|\", sql)\n    except Exception as e:\n        print(col, \"ERROR\", type(e).__name__, e, \"|\", sql)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/probe_unpivot.py').read())\"", "description": "Probe current UNPIVOT lineage across query shapes"}
[tool_result] score -> ['SALES.JAN', 'SALES.FEB'] | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
metric_name -> ['SALES.JAN', 'SALES.FEB'] | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan AS j, feb AS f))
id -> ['SALES.ID'] | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
mar -> ['SALES.MAR'] | SELECT mar FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
score -> ['SALES.JAN', 'SALES.FEB'] | SELECT * FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
[assistant] Baseline cases are correct. Now the shapes most likely to break: literal IN labels, multi-value UNPIVOT, and pass-through columns via a subquery.
[tool_use Bash] {"command": "cat > /tmp/probe_unpivot2.py <<'EOF'\nfrom sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\", \"apr\": \"int\"}}\ncases = [\n    (\"metric_name\", \"SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\"),\n    (\"metric_name\", \"SELECT metric_name FROM sales UNPIVOT (score FOR metric_n
…[1003 chars elided]…
col, \"->\", [d.name for d in node.downstream], \"|\", sql)\n    except Exception as e:\n        print(col, \"ERROR\", type(e).__name__, str(e)[:120], \"|\", sql)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/probe_unpivot2.py').read())\"", "description": "Probe harder UNPIVOT shapes for lineage errors"}
[tool_result] metric_name -> ['SALES.JAN', 'SALES.FEB'] | SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
metric_name -> [] | SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN ('JAN' AS j, 'FEB' AS f))
score -> [] | SELECT score FROM sales UNPIVOT (score FOR metric_name IN ('JAN' AS j, 'FEB' AS f))
q1 -> ['SALES.Q1'] | SELECT q1 FROM sales UNPIVOT ((a, b) FOR q IN ((jan, feb) AS 'Q1', (mar, apr) AS 'Q2'))
a -> ['SALES.JAN', 'SALES.FEB', 'SALES.MAR', 'SALES.APR'] | SEL
…[129 chars elided]…
an, feb FROM sales) s UNPIVOT (score FOR metric_name IN (jan, feb))
id -> ['SALES.ID'] | SELECT id, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
score -> ['SALES.JAN', 'SALES.FEB'] | SELECT u.score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
metric_name -> ['SALES.JAN', 'SALES.FEB'] | SELECT u.metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
id -> ['U.ID'] | SELECT u.id FROM sales AS u UNPIVOT (score FOR metric_name IN (jan, feb))
[assistant] Three problems showed up. Literal IN labels produce no lineage for the value column (`score -> []`). Multi-value UNPIVOT over-approximates (`a` pulls in `jan, feb, mar, apr` when it should only get `jan, mar`). The subquery and alias cases are correct. Before changing `_pivot_column_mapping`, I need the AST shape for these forms.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot import exp\nfor sql in [\n \\\"SELECT 1 FROM sales UNPIVOT (score FOR metric_name IN ('JAN' AS j, 'FEB' AS f))\\\",\n \\\"SELECT 1 FROM sales UNPIVOT ((a, b) FOR q IN ((jan, feb) AS 'Q1', (mar, apr) AS 'Q2'))\\\",\n]:\n    p = sqlglot.parse_one(sql, read='snowflake').find(exp.Pivot)\n    print('unpivot', p.unpivot, 'expressions', [type(e).__name__ for e in p.expressions])\n    for f in p.fields:\n        print(' field', type(f).__name__, 'this=', f.this.sql(), 'exprs=', [(type(e).__name__, e.sql()) for e in f.expressions])\n\"", "description": "Dump UNPIVOT AST shape for literal and tuple forms"}
[tool_result] unpivot True expressions ['Identifier']
 field In this= metric_name exprs= [('PivotAlias', "'JAN' AS j"), ('PivotAlias', "'FEB' AS f")]
unpivot True expressions ['Tuple']
 field In this= q exprs= [('PivotAlias', "(jan, feb) AS 'Q1'"), ('PivotAlias', "(mar, apr) AS 'Q2'")]
[assistant] The AST confirms it: each IN entry is a `PivotAlias` wrapping either a literal, a column, or a tuple, and the multi-value form is a single `Tuple` in `pivot.expressions`. The current mapping collects every column under every value name, which is the over-approximation. I'll read the exact block before editing.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "offset": 466, "limit": 26}
[tool_result] 466	    return node
467	
468	
469	def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
470	    """Map each (UN)PIVOT output column name to the source columns it's derived from."""
471	    mapping: dict[str, list[exp.Column]] = {}
472	
473	    if pivot.unpivot:
474	        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
475	        # are derived from the IN-list source columns
476	        unpivot_columns = [
477	            col
478	          
…[105 chars elided]…
all(exp.Column)
481	        ]
482	        for value_column in pivot.expressions:
483	            for identifier in value_column.find_all(exp.Identifier):
484	                mapping[identifier.name] = unpivot_columns
485	        for field in pivot.fields:
486	            if isinstance(field, exp.In):
487	                mapping[field.this.name] = unpivot_columns
488	
489	        return mapping
490	
491	    # For each aggregation function, the pivot creates a new column for each field in category
[assistant] The fix is to map each value column to the IN-list entries at its own tuple position, unwrap `PivotAlias` so literal labels are handled, and keep the name column derived from all entries as before.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n            for field in pivo
…[1140 chars elided]…
ol in (entry.expressions[i] if isinstance(entry, exp.Tuple) else entry).find_all(\n                    exp.Column\n                )\n            ]\n        name_columns = [col for entry in entries for col in entry.find_all(exp.Column)]\n        for field in pivot.fields:\n            if isinstance(field, exp.In):\n                mapping[field.this.name] = name_columns\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/probe_unpivot2.py').read())\"; $P -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/probe_unpivot.py').read())\"; $P -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Re-run UNPIVOT probes and lineage test file"}
[tool_result] metric_name -> ['SALES.JAN', 'SALES.FEB'] | SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
metric_name -> [] | SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN ('JAN' AS j, 'FEB' AS f))
score -> [] | SELECT score FROM sales UNPIVOT (score FOR metric_name IN ('JAN' AS j, 'FEB' AS f))
q1 -> ['SALES.Q1'] | SELECT q1 FROM sales UNPIVOT ((a, b) FOR q IN ((jan, feb) AS 'Q1', (mar, apr) AS 'Q2'))
a -> ['SALES.JAN', 'SALES.MAR'] | SELECT a FROM sales UNPIVOT (
…[771 chars elided]…
| SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan AS j, feb AS f))
id -> ['SALES.ID'] | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
mar -> ['SALES.MAR'] | SELECT mar FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
score -> ['SALES.JAN', 'SALES.FEB'] | SELECT * FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
........................................                                 [100%]
40 passed in 0.16s
[assistant] The multi-value case is now precise (`a -> JAN, MAR`), and the 40 existing lineage tests pass. The literal-label `score -> []` result is not a real bug: Snowflake's UNPIVOT IN-list takes column names, not string literals, so that query is not valid UNPIVOT SQL. I'll leave it alone and say so. Next I'll add regression tests for the fixed and previously-working shapes.
[tool_use Bash] {"command": "grep -n \"def test_table_udtf_snowflake\" tests/test_lineage.py", "description": "Find insertion point for new UNPIVOT tests"}
[tool_result] 723:    def test_table_udtf_snowflake(self) -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "offset": 718, "limit": 6}
[tool_result] 718	
719	        node = lineage("id", sql, schema=schema, dialect="snowflake")
720	        self.assertEqual(node.downstream[0].name, "SRC.ID")
721	        self.assertEqual(node.downstream[0].downstream[0].name, "SALES.ID")
722	
723	    def test_table_udtf_snowflake(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\
…[2188 chars elided]…
chema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"S.ID\"])\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\n\n        node = lineage(\"score\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"S.JAN\", \"S.FEB\"])\n\n    def test_table_udtf_snowflake(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-060150-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[assistant] Now I'll run the full project test command from the harness config, plus the linter.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $P -I -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $P -I -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[372 chars elided]…
......................................................................................................................................................................................................................................................................... [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 89.35s (0:01:29)
All checks passed!
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
[assistant] The full suite passes (1120 tests) and lint is clean. Ruff wants to reformat `lineage.py`, so I'll apply it and check that it only touched my hunk.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -m ruff format sqlglot/lineage.py && $P -I -m ruff format --check sqlglot/lineage.py tests/test_lineage.py && git diff -- sqlglot/lineage.py && $P -I -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -2", "description": "Apply ruff format and show lineage diff"}
[tool_result] 1 file reformatted
2 files already formatted
diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 6db18a09f..a571c0d6b 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -471,20 +471,27 @@ def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
     mapping: dict[str, list[exp.Column]] = {}
 
     if pivot.unpivot:
-        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
-        # are derived from the IN-list source columns
-   
…[1101 chars elided]…
e_columns = [col for entry in entries for col in entry.find_all(exp.Column)]
         for field in pivot.fields:
             if isinstance(field, exp.In):
-                mapping[field.this.name] = unpivot_columns
+                mapping[field.this.name] = name_columns
 
         return mapping
 
...........................................                              [100%]
43 passed in 0.15s
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] UNPIVOT lineage now handles multi-value UNPIVOT correctly, and the full suite passes (1120 tests). The changes are uncommitted in the worktree.

**What was wrong**
- **Multi-value UNPIVOT over-approximated.** For `UNPIVOT((a, b) FOR q IN ((jan, feb) AS 'Q1', (mar, apr) AS 'Q2'))`, `a` was reported as coming from all four columns. It should come only from `jan` and `mar`.

**What I changed**
- `sqlglot/lineage.py`, in `_pivot_column_mapping`: each value column now maps only to the IN-list entries at its position in the tuple. The name column still maps to every IN-list entry. `PivotAlias` wrapp
…[332 chars elided]…
ady traced correctly through subqueries, aliases and CTEs. The new tests lock that in.
- A literal-label IN list such as `IN ('JAN' AS j, 'FEB' AS f)` gives no value-column lineage. Snowflake's UNPIVOT IN-list takes column names, so I treated that query as invalid rather than a case to fix.

**Verification**
- Full suite: `1120 passed` with the harness command.
- `ruff check` passes. I also ran `ruff format` on `lineage.py`, which only re-wrapped my new block.

I did not commit anything. If you want the change as a commit, I can make one with the Co-Authored-By line from the repo instructions.
