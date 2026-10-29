# trajectory base-1

final message:
I fixed the multi-value `UNPIVOT` case in `lineage()`. The full test suite passes (1118 tests) and ruff is clean.

**The bug:** in `UNPIVOT((a, b) FOR metric_name IN ((jan, jan_amt) AS 'Jan', (feb, feb_amt) AS 'Feb'))`, every value column was mapped to every IN-list column. So `a` wrongly showed `JAN_AMT` and `FEB_AMT` as upstream.

**The fix** (`sqlglot/lineage.py`, `_pivot_column_mapping`): the name column still depends on all IN-list columns. Each value column now depends only on the IN-list entries at its own position. Single-value `UNPIVOT` behaves exactly as before.

**Test:** added `test_unpivot_multiple_value_columns` to `tests/test_lineage.py`, covering `a`, `b`, and the name column. I ran ruff format on that file, which reflowed my new test lines. I didn't touch any existing test.

**Probed and already correct, so unchanged:** single-value UNPIVOT with aliased IN-list entries, pass-through columns (plain, renamed, star, and through CTEs or derived tables), UNPIVOT aliases used as qualifiers, nested UNPIVOT inside a CTE with an outer aggregate, UNPIVOT inside a subquery filter, and UNPIVOT joined with a plain table.

**Not addressed:** `_pivot_column_mapping` only applies when the scope contains exactly one pivot (`pivots[0] if len(pivots) == 1`). A scope with two pivots falls back to the leaf-level behavior. I tried a self-join of two UNPIVOTs, but it failed in qualification ("Alias already used"), so I couldn't check what lineage does there. Fixing it would mean matching pivots by alias rather than taking the only one. That's a larger change, so I left it for a follow-up.

## events
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\\|pivot\" sqlglot/lineage.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -60 && grep -rn -i \"unpivot\" tests/test_lineage.py | head -40", "description": "Inspect repo state and UNPIVOT references"}
[tool_result] 72ae15e8b lithify: probe base
fb57d7e4c eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/optimizer/scope.py:98:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:148:        self._pivots = None
sqlglot/optimizer/scope.py:440:                            expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:508:    def pivots(self) -> list[exp.Pivot]:
sqlglot/optimizer/scope.py:509:        if self._pivots is None:
sqlglot/
…[4928 chars elided]…
_sum, MAX(price)) FOR category IN ('a' AS cat_a, 'b')
sqlglot/lineage.py:500:    pivot_columns = pivot.args["columns"]
sqlglot/lineage.py:501:    pivot_aggs_count = len(pivot.expressions)
tests/test_lineage.py:688:    def test_unpivot(self) -> None:
tests/test_lineage.py:691:        FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
tests/test_lineage.py:704:    def test_unpivot_with_cte(self) -> None:
tests/test_lineage.py:710:        FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
[tool_use Bash] {"command": "sed -n 350,520p sqlglot/lineage.py && sed -n 670,730p tests/test_lineage.py", "description": "Read lineage pivot handling and existing tests"}
[tool_result]             node.downstream.append(star_node)
            if on_node:
                on_node(star_node)

    # Find all columns that went into creating this one to list their lineage nodes.
    source_columns = set(find_all_in_scope(select, exp.Column))

    # If the source is a UDTF find columns used in the UDTF to generate the table
    if isinstance(source, exp.UDTF):
        source_columns |= set(source.find_all(exp.Column))
        derived_tables: Sequence[exp.Expr] = [
            src.exp
…[8754 chars elided]…
hema=schema, dialect="snowflake")
        self.assertEqual(node.downstream[0].name, "SRC.ID")
        self.assertEqual(node.downstream[0].downstream[0].name, "SALES.ID")

    def test_table_udtf_snowflake(self) -> None:
        lateral_flatten = """
        SELECT f.value:external_id::string AS external_id
        FROM database_name.schema_name.table_name AS raw,
        LATERAL FLATTEN(events) AS f
        """
        table_flatten = """
        SELECT f.value:external_id::string AS external_id
[tool_use Bash] {"command": "grep -n \"unpivot\" sqlglot/parser.py | head -30 && grep -n \"class Pivot\" -A 25 sqlglot/expressions.py | head -50 && PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\ne=parse_one('SELECT id, metric_name, score FROM sales UNPIVOT ((a,b) FOR metric_name IN ((jan,jan2) AS \\'Jan\\', (feb,feb2) AS \\'Feb\\'))', read='snowflake')\nprint(repr(e.args['from'].this.args['pivots'][0]))\n\"", "description": "Check UNPIVOT parse tree shape"}
[tool_result ERROR] Exit code 1
278:def _unpivot_target(expr: exp.Expr) -> exp.Expr:
283:        expr.set("expressions", [_unpivot_target(e) for e in expr.expressions])
1108:        TokenType.UNPIVOT: lambda self: self._parse_simplified_pivot(is_unpivot=True),
3782:                is_unpivot=self._prev.token_type == TokenType.UNPIVOT
5107:    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
5119:    def _parse_simplified_pivot(self, is_unpivot: bool | None = None) -> exp.Pivot:
5134:        into = sel
…[197 chars elided]…
anual/sql-ref-syntax-qry-select-unpivot.html#syntax
5211:        if unpivot:
5241:                unpivot=unpivot,
5248:        if unpivot:
5249:            pivot.set("expressions", [_unpivot_target(e) for e in pivot.expressions])
5252:                    pivot_field.set("this", _unpivot_target(pivot_field.this))
5257:        if not unpivot:
ugrep: warning: sqlglot/expressions.py: No such file or directory
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'from'
[tool_use Bash] {"command": "sed -n 270,290p sqlglot/parser.py && sed -n 5105,5270p sqlglot/parser.py && grep -rn \"class Pivot(\" -A 40 sqlglot/expressions/*.py | head -70", "description": "Read UNPIVOT parser code and Pivot expression"}
[tool_result] def _resolve_dialect(dialect: DialectType) -> Dialect:
    from sqlglot.dialects.dialect import Dialect

    return Dialect.get_or_raise(dialect)


def _unpivot_target(expr: exp.Expr) -> exp.Expr:
    # UNPIVOT's pre-FOR values and FOR field are new output names, not column references.
    if isinstance(expr, exp.Column) and not expr.table:
        return expr.this
    if isinstance(expr, exp.Tuple):
        expr.set("expressions", [_unpivot_target(e) for e in expr.expressions])
    return expr

…[8142 chars elided]…
CT * FROM t UNPIVOT(val FOR name IN (a, b))").find(exp.Pivot)
sqlglot/expressions/query.py-1782-            >>> list(piv.output_columns(["a", "b", "c"]))
sqlglot/expressions/query.py-1783-            ['c', 'name', 'val']
sqlglot/expressions/query.py-1784-
sqlglot/expressions/query.py-1785-        AST shape:
sqlglot/expressions/query.py-1786-            PIVOT(SUM(val) FOR name IN ('a', 'b')):
sqlglot/expressions/query.py-1787-                expressions: aggregate(s), e.g. [Sum(this=Column(val))]
[tool_use Bash] {"command": "mkdir -p /tmp/unpivot_probe && cat > /tmp/unpivot_probe/probe.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage\n\ndef tree(node, depth=0, out=None):\n    out = [] if out is None else out\n    out.append(\"  \" * depth + node.name + (f\"  [ref={node.reference_node_name}]\" if node.reference_node_name else \"\"))\n    for d in node.downstream:\n    
…[2014 chars elided]…
\n        print(\"\\n\".join(tree(n)))\n    except Exception as e:\n        print(\"ERROR\", type(e).__name__, e)\nEOF\ncd ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101134-lineage-further-improve-lineage/base-1 && <work>/env-sqlglot/bin/python -I /tmp/unpivot_probe/probe.py", "description": "Probe UNPIVOT lineage across query shapes"}
[tool_result] === A basic: score
SCORE
  SALES.JAN
  SALES.FEB
=== B alias IN-list: score
SCORE
  SALES.JAN
  SALES.FEB
=== C multi-value: a
A
  SALES.JAN
  SALES.JAN_AMT
  SALES.FEB
  SALES.FEB_AMT
=== C multi-value: b
B
  SALES.JAN
  SALES.JAN_AMT
  SALES.FEB
  SALES.FEB_AMT
=== D qualified passthrough
ID
  S.ID
=== E renamed passthrough
CID
  SALES.ID
=== F star
ID
  SALES.ID
=== G alias pivot qualified
ID
  SALES.ID
=== H derived subquery
SCORE
  _0.JAN
    SALES.JAN
  _0.FEB
    SALES.FEB
=== I passthrough via ref cte
ID
  SRC.ID
    SALES.ID
=== J expr over value
ERROR SqlglotError Cannot find column 'SCORE' in query.
=== K name col, star cte
METRIC_NAME
  SRC.JAN
    SALES.JAN
  SRC.FEB
    SALES.FEB
[tool_use Bash] {"command": "cat > /tmp/unpivot_probe/probe2.py <<'EOF'\nimport sys, traceback\nsys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nS = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"jan_amt\": \"int\", \"feb_amt\": \"int\", \"name\": \"text\"}}\nfor sql, col in [\n  (\"SELECT s.id FROM s
…[437 chars elided]…
exc(limit=-6)\nprint(qualify(parse_one(\"SELECT id, score * 10 AS s10 FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))\", read=\"snowflake\"), schema=S, dialect=\"snowflake\").sql(\"snowflake\"))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/unpivot_probe/probe2.py 2>&1 | tail -60", "description": "Compare UNPIVOT vs plain lineage and trace error"}
[tool_result] SELECT s.id FROM sales AS s id -> ['S.ID']
SELECT id, score * 10 AS s10 FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) s10 -> ['SALES.JAN', 'SALES.FEB']
SELECT id, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) score -> ['SALES.JAN', 'SALES.FEB']
SELECT "SALES"."ID" AS "ID", "SALES"."SCORE" * 10 AS "S10" FROM "SALES" AS "SALES" UNPIVOT("SCORE" FOR "METRIC_NAME" IN ("JAN", "FEB")) AS "SALES"
[tool_use Bash] {"command": "cat > /tmp/unpivot_probe/probe3.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage\ndef tree(node, depth=0, out=None):\n    out = [] if out is None else out\n    out.append(\"  \" * depth + node.name)\n    for d in node.downstream:\n        tree(d, depth + 1, out)\n    return out\nS = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\",
…[1662 chars elided]…
 cases:\n    print(\"=== \" + label)\n    try:\n        print(\"\\n\".join(tree(lineage(col, sql, schema=S, dialect=\"snowflake\"))))\n    except Exception as e:\n        print(\"ERROR\", type(e).__name__, str(e)[:200])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/unpivot_probe/probe3.py 2>&1 | head -150", "description": "Probe more UNPIVOT query shapes"}
[tool_result] === alias-qualified value
SCORE
  SALES.JAN
  SALES.FEB
=== alias-qualified name
METRIC_NAME
  SALES.JAN
  SALES.FEB
=== two unpivots joined, score
ERROR OptimizeError Alias already used: SALES
=== unpivot joined w/ table, region
REGION
  O.REGION
=== unpivot joined w/ table, score
SCORE
  SALES.JAN
  SALES.FEB
=== nested unpivot in CTE
SCORE
  A.SCORE
    SALES.JAN
    SALES.FEB
=== unpivot in cte, outer aggregate
TOTAL
  A.SCORE
    SALES.JAN
    SALES.FEB
=== unpivot in subquery filter
ID
  SALES.ID
=== unpivot in where only
ID
  SALES.ID
=== passthrough star+cte
JAN_AMT
  S.JAN_AMT
    SALES.JAN_AMT
=== multi-value via cte
A
  S.JAN
    SALES.JAN
  S.JAN_AMT
    SALES.JAN_AMT
  S.FEB
    SALES.FEB
  S.FEB_AMT
    SALES.FEB_AMT
=== name col in expression
ERROR SqlglotError Cannot find column 'METRIC_NAME' in query.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one, exp\ne=parse_one('SELECT * FROM sales UNPIVOT ((a, b) FOR metric_name IN ((jan, jan_amt) AS \\'Jan\\', (feb, feb_amt) AS \\'Feb\\'))', read='snowflake')\np=e.find(exp.Pivot)\nprint(repr(p.expressions)); print(repr(p.fields[0].expressions))\n\" 2>&1 | head -30; git -C . status --short | head", "description": "Inspect multi-value UNPIVOT AST shape"}
[tool_result] [Tuple(
  expressions=[
    Identifier(this=a, quoted=False),
    Identifier(this=b, quoted=False)])]
[PivotAlias(
  this=Tuple(
    expressions=[
      Column(
        this=Identifier(this=jan, quoted=False)),
      Column(
        this=Identifier(this=jan_amt, quoted=False))]),
  alias=Literal(this='Jan', is_string=True)), PivotAlias(
  this=Tuple(
    expressions=[
      Column(
        this=Identifier(this=feb, quoted=False)),
      Column(
        this=Identifier(this=feb_amt, quoted=False))]),
  alias=Literal(this='Feb', is_string=True))]
[assistant] Confirmed the one real gap so far: in a multi-value `UNPIVOT ((a, b) FOR ...)`, every value column is mapped to every IN-list column, so `a` wrongly depends on `jan_amt`/`feb_amt`. I'll fix the mapping so each value column only follows the IN-list entries at its own position.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101134-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1454 chars elided]…
          for identifier in (value.expressions if isinstance(value, exp.Tuple) else [value])\n        ]\n        for i, identifier in enumerate(value_names):\n            mapping[identifier.name] = [\n                col\n                for parts in value_entries\n                if i < len(parts)\n                for col in parts[i].find_all(exp.Column)\n            ]\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101134-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/unpivot_probe/probe.py 2>&1 | sed -n 1,20p", "description": "Re-run UNPIVOT probe after fix"}
[tool_result] === A basic: score
SCORE
  SALES.JAN
  SALES.FEB
=== B alias IN-list: score
SCORE
  SALES.JAN
  SALES.FEB
=== C multi-value: a
A
  SALES.JAN
  SALES.FEB
=== C multi-value: b
B
  SALES.JAN_AMT
  SALES.FEB_AMT
=== D qualified passthrough
ID
  S.ID
=== E renamed passthrough
[assistant] Multi-value now maps per position. Adding a regression test next to the existing UNPIVOT tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101134-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\
…[799 chars elided]…
eage(\"b\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.JAN_AMT\", \"SALES.FEB_AMT\"])\n\n        node = lineage(\"metric_name\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(\n            [d.name for d in node.downstream], [\"SALES.JAN\", \"SALES.JAN_AMT\", \"SALES.FEB\", \"SALES.FEB_AMT\"]\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101134-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -5", "description": "Run lineage tests then full test suite"}
[tool_result] .........................................                                [100%]
41 passed in 0.11s
................................................................................................................................................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1118 passed, 18166 subtests passed in 50.69s
[assistant] Full suite passes (1118 tests). Running the linter on the changed files, since the project's pre-commit uses ruff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -20; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
 sqlglot/lineage.py    | 30 ++++++++++++++++++++++--------
 tests/test_lineage.py | 18 ++++++++++++++++++
 2 files changed, 40 insertions(+), 8 deletions(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_lineage.py && git diff tests/test_lineage.py | head -60 && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -2", "description": "Apply ruff formatting and re-run lineage tests"}
[tool_result] 1 file reformatted
diff --git a/tests/test_lineage.py b/tests/test_lineage.py
index 5ddb8fccd..304e42db6 100644
--- a/tests/test_lineage.py
+++ b/tests/test_lineage.py
@@ -720,6 +720,27 @@ class TestLineage(unittest.TestCase):
         self.assertEqual(node.downstream[0].name, "SRC.ID")
         self.assertEqual(node.downstream[0].downstream[0].name, "SALES.ID")
 
+    def test_unpivot_multiple_value_columns(self) -> None:
+        sql = """
+        SELECT id, metric_name, a, b
+        FROM sa
…[652 chars elided]…
    self.assertEqual(
+            [d.name for d in node.downstream],
+            ["SALES.JAN", "SALES.JAN_AMT", "SALES.FEB", "SALES.FEB_AMT"],
+        )
+
     def test_table_udtf_snowflake(self) -> None:
         lateral_flatten = """
         SELECT f.value:external_id::string AS external_id
.........................................                                [100%]
41 passed in 0.10s
[This command modified 1 file you've previously read: tests/test_lineage.py. Call Read before editing.]
[assistant] I fixed the multi-value `UNPIVOT` case in `lineage()`. The full test suite passes (1118 tests) and ruff is clean.

**The bug:** in `UNPIVOT((a, b) FOR metric_name IN ((jan, jan_amt) AS 'Jan', (feb, feb_amt) AS 'Feb'))`, every value column was mapped to every IN-list column. So `a` wrongly showed `JAN_AMT` and `FEB_AMT` as upstream.

**The fix** (`sqlglot/lineage.py`, `_pivot_column_mapping`): the name column still depends on all IN-list columns. Each value column now depends only on the IN-list entries at its own position. Single-value `UNPIVOT` behaves exactly as before.

**Test:** added `tes
…[409 chars elided]…
ifiers, nested UNPIVOT inside a CTE with an outer aggregate, UNPIVOT inside a subquery filter, and UNPIVOT joined with a plain table.

**Not addressed:** `_pivot_column_mapping` only applies when the scope contains exactly one pivot (`pivots[0] if len(pivots) == 1`). A scope with two pivots falls back to the leaf-level behavior. I tried a self-join of two UNPIVOTs, but it failed in qualification ("Alias already used"), so I couldn't check what lineage does there. Fixing it would mean matching pivots by alias rather than taking the only one. That's a larger change, so I left it for a follow-up.
