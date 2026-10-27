# trajectory base-1

final message:
Fixed the one UNPIVOT lineage defect I could reproduce: in a multi-column UNPIVOT, each value column was traced to every IN-list column, not just its own position.

**The bug:** for `UNPIVOT ((a, b) FOR n IN ((jan, mar) AS 'Q1', (feb, apr) AS 'Q2'))`, lineage of `a` listed `JAN, MAR, FEB, APR`. It should be `JAN, FEB`, and `b` should be `MAR, APR`.

**The fix** is in `_pivot_column_mapping` in `sqlglot/lineage.py`. The i-th value column now maps only to the i-th column of each IN-list entry. This handles both aliased (`(…) AS 'Q1'`) and bare tuple entries. The name column still maps to every IN-list column, as before.

**Tests:** I added `test_unpivot_multiple_value_columns` to `tests/test_lineage.py`. I didn't touch existing tests.

**Verification:**
- Full suite via `run_suite.py`: `SUMMARY: 1118 passed, 18166 subtests passed in 54.84s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both files.

**Shapes I checked that were already correct, so I left them alone:** single-column UNPIVOT (value, name, and pass-through columns), qualified and aliased pass-through columns, joins after UNPIVOT, UNPIVOT over a derived table with a computed IN-list column, UNPIVOT inside a CTE with `SELECT *`, CTE column aliases, and Databricks/DuckDB syntax.

I haven't committed anything.

## events
[assistant] I'll start by finding the existing UNPIVOT lineage code and its tests.
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50; grep -rn -i \"unpivot\" tests/test_lineage.py | head; ls .lithify/harness 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -20", "description": "Locate UNPIVOT references in lineage and optimizer code"}
[tool_result] a47a1259d lithify: probe base
372d271eb eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/lineage.py:473:    if pivot.unpivot:
sqlglot/lineage.py:474:        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
sqlglot/lineage.py:476:        unpivot_columns = [
sqlglot/lineage.py:484:                mapping[identifier.name] = unpivot_columns
sqlglot/lineage.py:487:                mapping[field.this.name] = unpivot_columns
sqlglot/optimizer/annotate
…[352 chars elided]…
erator
sqlglot/optimizer/qualify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
tests/test_lineage.py:688:    def test_unpivot(self) -> None:
tests/test_lineage.py:691:        FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
tests/test_lineage.py:704:    def test_unpivot_with_cte(self) -> None:
tests/test_lineage.py:710:        FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The Docs tools that just appeared aren't relevant here, so I'll stay on the lineage code. Next I'll read the current UNPIVOT handling and its tests.
[tool_use Bash] {"command": "sed -n 380,560p sqlglot/lineage.py; echo ----; sed -n 670,740p tests/test_lineage.py", "description": "Read lineage pivot handling and existing tests"}
[tool_result]         col_source: exp.Table | Scope | None = scope.sources.get(table)

        if isinstance(col_source, Scope):
            reference_node_name = None
            if col_source.scope_type == ScopeType.DERIVED_TABLE and table not in source_names:
                reference_node_name = table
            elif col_source.scope_type == ScopeType.CTE:
                selected_node, _ = scope.selected_sources.get(table, (None, None))
                reference_node_name = selected_node.name if selecte
…[9117 chars elided]…
ents) AS f
        """
        table_flatten = """
        SELECT f.value:external_id::string AS external_id
        FROM database_name.schema_name.table_name AS raw
        JOIN TABLE(FLATTEN(events)) AS f
        """

        lateral_node = lineage("external_id", lateral_flatten, dialect="snowflake")
        table_node = lineage("external_id", table_flatten, dialect="snowflake")

        self.assertEqual(lateral_node.name, "EXTERNAL_ID")
        self.assertEqual(table_node.name, "EXTERNAL_ID")
[assistant] The current code maps every UNPIVOT value and name column to the full IN-list. Before deciding what's wrong, I'll probe real query shapes against the current behaviour. First I'll check the harness notes and the parser's UNPIVOT node shape.
[tool_use Bash] {"command": "cat .lithify/harness/memory.md | head -30; grep -n \"def _parse_pivot\" -A60 sqlglot/parser.py | grep -n -i \"unpivot\\|fields\\|expressions\\|include\\|In(\" | head -40", "description": "Read harness python path and pivot parser notes"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 
…[1720 chars elided]…
5211-        if unpivot:
116:5212-            expressions = self._parse_csv(self._parse_column)
118:5214-            expressions = self._parse_csv(self._parse_pivot_aggregation)
120:5216-        if not expressions:
126:5222-        fields = []
131:5227-            fields.append(field)
143:5239-                expressions=expressions,
144:5240-                fields=fields,
145:5241-                unpivot=unpivot,
146:5242-                include_nulls=include_nulls,
152:5248-        if unpivot:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; mkdir -p /tmp/unp && cat > /tmp/unp/probe.py <<'EOF'\nfrom sqlglot.lineage import lineage\nfrom sqlglot import parse_one\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}}\ncases = [\n (\
…[1852 chars elided]…
         print(\"  \"*d + node.name, \"<-\", node.source.sql(\"snowflake\")[:60] if hasattr(node.source,'sql') else node.source)\n            for c in node.downstream: show(c, d+1)\n        show(n)\n    except Exception as e:\n        print(\"  ERR\", type(e).__name__, e)\nEOF\nPYTHONPATH=. $PY /tmp/unp/probe.py 2>&1 | head -150", "description": "Probe UNPIVOT lineage across several query shapes"}
[tool_result] == score | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
SCORE <- SELECT SALES.SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCOR
  SALES.JAN <- SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) 
  SALES.FEB <- SALES AS SALES UNPIVOT(SCORE FOR METRIC_NAME IN (JAN, FEB)) 
== id | SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
ID <- SELECT SALES.ID AS ID FROM SALES AS SALES UNPIVOT(SCORE FOR 
  SALES.ID <- SALE
…[4439 chars elided]…
SCORE AS SCORE FROM SALES AS SALES UNPIVOT(SCOR
    SALES.JAN <- SALES AS SALES UNPIVOT(SCORE FOR M IN (JAN, FEB)) AS SALES
    SALES.FEB <- SALES AS SALES UNPIVOT(SCORE FOR M IN (JAN, FEB)) AS SALES
== id | SELECT x.id FROM (SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))) AS x
ID <- SELECT X.ID AS ID FROM (SELECT SALES.ID AS ID, SALES.MAR AS 
  X.ID <- SELECT SALES.ID AS ID FROM SALES AS SALES UNPIVOT(SCORE FOR 
    SALES.ID <- SALES AS SALES UNPIVOT(SCORE FOR M IN (JAN, FEB)) AS SALES
[assistant] The probes show one clear defect: in a multi-column UNPIVOT, each value column is traced to every IN-list column, so `a` wrongly lists `MAR` and `ID`. I'll probe more shapes (joins, qualified pass-through columns, CTE column aliases, Databricks syntax) before deciding on the full set of fixes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/unp/probe2.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}, \"other\": {\"id\": \"int\", \"x\": \"int\"}}\ncases = [\n (\"id\"
…[1540 chars elided]…
n    try:\n        n = lineage(col, sql, schema=schema, dialect=d)\n        def show(node, dep=0):\n            print(\"  \"*dep + node.name)\n            for c in node.downstream: show(c, dep+1)\n        show(n)\n    except Exception as e:\n        print(\"  ERR\", type(e).__name__, e)\nEOF\nPYTHONPATH=. $PY /tmp/unp/probe2.py 2>&1 | head -150", "description": "Probe more UNPIVOT lineage shapes"}
[tool_result] == id | SELECT sales.id FROM sales UNPIVOT (score FOR m IN (jan, feb)) snowflake
ID
  SALES.ID
== id | SELECT u.id, o.x FROM sales AS s UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN other AS o ON u.id = o.id snowflake
ID
  S.ID
== x | SELECT u.id, o.x FROM sales AS s UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN other AS o ON u.id = o.id snowflake
X
  O.X
== score | WITH src(id, j, f) AS (SELECT id, jan, feb FROM sales) SELECT score FROM src UNPIVOT (score FOR m IN (j, f)) snowflake
SCORE
  SRC.
…[702 chars elided]…
 score FROM sales UNPIVOT INCLUDE NULLS (score FOR m IN (jan, feb)) databricks
score
  sales.jan
  sales.feb
== score | SELECT score FROM sales UNPIVOT (score FOR m IN (jan, feb)) AS u duckdb
score
  sales.jan
  sales.feb
== mar | SELECT mar FROM sales UNPIVOT (score FOR m IN (jan, feb)) snowflake
MAR
  SALES.MAR
== m | SELECT m FROM sales UNPIVOT (score FOR m IN (jan, feb)) snowflake
M
  SALES.JAN
  SALES.FEB
== id | SELECT id FROM sales s UNPIVOT (score FOR m IN (jan, feb)) snowflake
ID
  S.ID
[assistant] Most shapes are already correct, including joins, qualified pass-through columns, CTE column aliases, and Databricks. The `SCORE` error on `score AS s` is my probe's fault: lineage was asked for an output name that doesn't exist. The one real defect is the multi-column UNPIVOT over-approximation. Next I'll inspect the AST for that shape.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nfrom sqlglot import parse_one, exp\nt = parse_one('SELECT a FROM sales UNPIVOT ((a, b) FOR n IN ((jan, mar) AS \\'Q1\\', (feb, id) AS \\'Q2\\'))', read='snowflake')\np = t.find(exp.Pivot)\nprint(repr(p.expressions)); print(repr(p.fields))\nt = parse_one('SELECT a FROM sales UNPIVOT (a FOR n IN (jan AS \\'Q1\\', feb))', read='snowflake')\nprint(repr(t.find(exp.Pivot).fields))\n\"; grep -n \"_pivot_column_mapping\\|pivot_column_mapping\" sqlglot/lineage.py", "description": "Inspect UNPIVOT AST for multi-column form"}
[tool_result] [Tuple(
  expressions=[
    Identifier(this=a, quoted=False),
    Identifier(this=b, quoted=False)])]
[In(
  this=Identifier(this=n, quoted=False),
  expressions=[
    PivotAlias(
      this=Tuple(
        expressions=[
          Column(
            this=Identifier(this=jan, quoted=False)),
          Column(
            this=Identifier(this=mar, quoted=False))]),
      alias=Literal(this='Q1', is_string=True)),
    PivotAlias(
      this=Tuple(
        expressions=[
          Column(
           
…[218 chars elided]…
ressions=[
    PivotAlias(
      this=Column(
        this=Identifier(this=jan, quoted=False)),
      alias=Literal(this='Q1', is_string=True)),
    Column(
      this=Identifier(this=feb, quoted=False))])]
376:    pivot_column_mapping = _pivot_column_mapping(pivot) if pivot else {}
408:            if column_name in pivot_column_mapping:
409:                downstream_columns.extend(pivot_column_mapping[column_name])
469:def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
[assistant] The multi-column form is `pivot.expressions == [Tuple(a, b)]` and each IN entry is either a bare `Tuple` or `PivotAlias(Tuple)`. So the i-th value column should map only to the i-th column of each entry. I'll make that change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1362 chars elided]…
column in enumerate(value_columns):\n            source_columns = [\n                col\n                for e in in_entries\n                for col in (e.expressions[i] if isinstance(e, exp.Tuple) else e).find_all(exp.Column)\n            ]\n            for identifier in value_column.find_all(exp.Identifier):\n                mapping[identifier.name] = source_columns\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll re-run both probe scripts to check the new mapping and confirm nothing else moved.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/unp/probe3.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}}\nfor col, sql in [\n (\"a\",\"SELECT a, n FROM sales UNPIVOT ((a, 
…[482 chars elided]…
"mar\",\"SELECT mar FROM sales UNPIVOT (score FOR m IN (jan, feb))\"),\n]:\n    n = lineage(col, sql, schema=schema, dialect=\"snowflake\")\n    print(col, \"->\", [d.name for d in n.downstream])\nEOF\nPYTHONPATH=. $PY /tmp/unp/probe3.py; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Re-run UNPIVOT probes and lineage test file"}
[tool_result] a -> ['SALES.JAN', 'SALES.FEB']
b -> ['SALES.MAR', 'SALES.ID']
n -> ['SALES.JAN', 'SALES.MAR', 'SALES.FEB', 'SALES.ID']
b -> ['SALES.MAR', 'SALES.ID']
score -> ['SALES.JAN', 'SALES.FEB']
m -> ['SALES.JAN', 'SALES.FEB']
mar -> ['SALES.MAR']
........................................                                 [100%]
40 passed in 0.10s
[assistant] The multi-column mapping is now positional (`a` → JAN, FEB; `b` → MAR, ID), and all 40 existing lineage tests pass. Next I'll check a few more shapes: derived-table expressions feeding the IN list, chained UNPIVOTs, and star through a CTE.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/unp/probe4.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}}\ndef show(node, dep=0):\n    print(\"  \"*dep + node.name)\n    fo
…[515 chars elided]…
T s2 FROM (SELECT * FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score AS s2 FOR m IN (jan, feb)))\"),\n]:\n    print(\"==\", col, sql)\n    try: show(lineage(col, sql, schema=schema, dialect=\"snowflake\"))\n    except Exception as e: print(\"  ERR\", type(e).__name__, e)\nEOF\nPYTHONPATH=. $PY /tmp/unp/probe4.py 2>&1 | head -80", "description": "Probe derived-table and chained UNPIVOT shapes"}
[tool_result] == score SELECT score FROM (SELECT id, jan * 2 AS jan, feb FROM sales) AS d UNPIVOT (score FOR m IN (jan, feb))
SCORE
  D.JAN
    SALES.JAN
  D.FEB
    SALES.FEB
== score WITH u AS (SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))) SELECT score FROM u
SCORE
  U.SCORE
    SALES.JAN
    SALES.FEB
== id WITH u AS (SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))) SELECT id FROM u
ID
  U.ID
    SALES.ID
== s2 WITH u AS (SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))) SELECT score AS s2 FROM u
S2
  U.SCORE
    SALES.JAN
    SALES.FEB
== s2 SELECT s2 FROM (SELECT * FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score AS s2 FOR m IN (jan, feb)))
  ERR ParseError Expecting FOR. Line 1, Col: 80.
  SELECT s2 FROM (SELECT * FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score [4mAS[0m s2 FOR m IN (jan, feb)))
[assistant] Those shapes are all correct; the last ParseError is my probe's invalid SQL, not a lineage problem. The fix is narrow, so I'll add one regression test covering the multi-column form next to the existing UNPIVOT tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "    def test_table_udtf_snowflake(self) -> None:", "new_string": "    def test_unpivot_multiple_value_columns(self) -> None:\n        sql = \"\"\"\n        SELECT a, b, id, n\n        FROM sales UNPIVOT ((a, b) FOR n
…[530 chars elided]…
\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(\n            [d.name for d in node.downstream], [\"SALES.JAN\", \"SALES.MAR\", \"SALES.FEB\", \"SALES.ID\"]\n        )\n\n        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.ID\"])\n\n    def test_table_udtf_snowflake(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[assistant] The test I just wrote is invalid SQL: `id` appears both in the IN list (so it's consumed by the UNPIVOT) and as a pass-through output. I'll swap the IN-list column for a new `apr` column so the pass-through case stays valid.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        FROM sales UNPIVOT ((a, b) FOR n IN ((jan, mar) AS 'Q1', (feb, id) AS 'Q2'))\n        \"\"\"\n        schema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"mar\": \"int\"}}\n\n        n
…[949 chars elided]…
EB\"])\n\n        node = lineage(\"b\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.MAR\", \"SALES.APR\"])\n\n        node = lineage(\"n\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(\n            [d.name for d in node.downstream], [\"SALES.JAN\", \"SALES.MAR\", \"SALES.FEB\", \"SALES.APR\"]\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[assistant] Next I'll run the lint/format checks on the two edited files and the lineage test file.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Run ruff checks and lineage tests"}
[tool_result] All checks passed!
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
.........................................                                [100%]
41 passed in 0.10s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff sqlglot/lineage.py 2>&1 | head -30; $PY -m ruff format sqlglot/lineage.py && git diff --stat", "description": "Show and apply ruff formatting to lineage.py"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -492,7 +492,9 @@
             source_columns = [
                 col
                 for e in in_entries
-                for col in (e.expressions[i] if isinstance(e, exp.Tuple) else e).find_all(exp.Column)
+                for col in (e.expressions[i] if isinstance(e, exp.Tuple) else e).find_all(
+                    exp.Column
+                )
             ]
             for identifier in value_column.find_all(exp.Identifier):
                 mapping[identifier.name] = source_columns

1 file would be reformatted
1 file reformatted
 sqlglot/lineage.py    | 29 +++++++++++++++++++++--------
 tests/test_lineage.py | 21 +++++++++++++++++++++
 2 files changed, 42 insertions(+), 8 deletions(-)
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] The formatter wrapped that comprehension awkwardly. I'll read the current block and rewrite it as a plain loop, which reads better.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "offset": 469, "limit": 40}
[tool_result] 469	def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
470	    """Map each (UN)PIVOT output column name to the source columns it's derived from."""
471	    mapping: dict[str, list[exp.Column]] = {}
472	
473	    if pivot.unpivot:
474	        # UNPIVOT(v1, v2 FOR name IN ((a1, a2) AS 'x', (b1, b2) AS 'y')): the name column is derived
475	        # from every IN-list source column, while the i-th value column is only derived from the
476	        # i-th source column of each
…[1132 chars elided]…
3	
504	    # For each aggregation function, the pivot creates a new column for each field in category
505	    # combined with the aggfunc. So the columns parsed have this order: cat_a_value_sum, cat_a,
506	    # b_value_sum, b. Because of this step wise manner the aggfunc 'sum(value) as value_sum'
507	    # belongs to the column indices 0, 2, and the aggfunc 'max(price)' without an alias belongs
508	    # to the column indices 1, 3. Here, only the columns used in the aggregations are of interest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "        for i, value_column in enumerate(value_columns):\n            source_columns = [\n                col\n                for e in in_entries\n                for col in (e.expressions[i] if isinstance(e, exp.Tuple
…[232 chars elided]…
        for i, value_column in enumerate(value_columns):\n            source_columns = []\n            for e in in_entries:\n                source = e.expressions[i] if isinstance(e, exp.Tuple) else e\n                source_columns.extend(source.find_all(exp.Column))\n            for identifier in value_column.find_all(exp.Identifier):\n                mapping[identifier.name] = source_columns"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-104426-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now I'll re-run ruff and the lineage tests, then start the full suite as its own foreground call, as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -2; PYTHONPATH=. $PY /tmp/unp/probe3.py", "description": "Lint, format-check, and rerun lineage tests and probes"}
[tool_result] All checks passed!
2 files already formatted
.........................................                                [100%]
41 passed in 0.10s
a -> ['SALES.JAN', 'SALES.FEB']
b -> ['SALES.MAR', 'SALES.ID']
n -> ['SALES.JAN', 'SALES.MAR', 'SALES.FEB', 'SALES.ID']
b -> ['SALES.MAR', 'SALES.ID']
score -> ['SALES.JAN', 'SALES.FEB']
m -> ['SALES.JAN', 'SALES.FEB']
mar -> ['SALES.MAR']
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:15:10 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-d8ccf94911.log
ELAPSED: 279s
SUMMARY: 1118 passed, 18166 subtests passed in 54.84s
EXIT: 0
[assistant] Fixed the one UNPIVOT lineage defect I could reproduce: in a multi-column UNPIVOT, each value column was traced to every IN-list column, not just its own position.

**The bug:** for `UNPIVOT ((a, b) FOR n IN ((jan, mar) AS 'Q1', (feb, apr) AS 'Q2'))`, lineage of `a` listed `JAN, MAR, FEB, APR`. It should be `JAN, FEB`, and `b` should be `MAR, APR`.

**The fix** is in `_pivot_column_mapping` in `sqlglot/lineage.py`. The i-th value column now maps only to the i-th column of each IN-list entry. This handles both aliased (`(…) AS 'Q1'`) and bare tuple entries. The name column still maps to every I
…[102 chars elided]…
eage.py`. I didn't touch existing tests.

**Verification:**
- Full suite via `run_suite.py`: `SUMMARY: 1118 passed, 18166 subtests passed in 54.84s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both files.

**Shapes I checked that were already correct, so I left them alone:** single-column UNPIVOT (value, name, and pass-through columns), qualified and aliased pass-through columns, joins after UNPIVOT, UNPIVOT over a derived table with a computed IN-list column, UNPIVOT inside a CTE with `SELECT *`, CTE column aliases, and Databricks/DuckDB syntax.

I haven't committed anything.
