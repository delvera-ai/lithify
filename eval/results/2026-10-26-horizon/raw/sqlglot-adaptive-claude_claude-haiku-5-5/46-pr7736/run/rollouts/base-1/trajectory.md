# trajectory base-1

final message:
UNPIVOT lineage now handles two more query shapes: a scope with several (UN)PIVOTs, and multi-value `UNPIVOT((a, b) FOR ...)`. The full suite passes (1119 tests), along with ruff and mypy on the changed files. The changes are uncommitted.

**What was broken**

- **Two pivots in one scope:** the lookup only worked when a scope had exactly one pivot. With two, `score` in `FROM sales UNPIVOT (...) AS u JOIN prices UNPIVOT (...) AS v` became a dead leaf with no link to `SALES.JAN`/`SALES.FEB`.
- **Multi-value UNPIVOT:** every value column was mapped to every IN-list column. `amt` and `qty` both showed all four source columns.

**What changed** (`sqlglot/lineage.py`)

- The pivot is now chosen by matching the column's table alias against the scope's pivots, rather than requiring exactly one. The mapping is computed only for the pivot that owns the column.
- For multi-value UNPIVOT, each value column maps to the IN-list columns at its own position. `UNPIVOT((amt, qty) FOR q IN ((jan, feb) AS 'Q1', (feb, jan) AS 'Q2'))` now gives `amt → JAN, FEB` and `qty → FEB, JAN`.
- Single-value UNPIVOT and passthrough columns resolve exactly as before.

**Tests** (`tests/test_lineage.py`)

- `test_unpivot_with_multiple_value_columns` covers the Oracle tuple form.
- `test_unpivot_with_multiple_sources` covers two UNPIVOTs joined in one scope.

**Choices I made**

- The name column still maps to the IN-list columns, as the existing `test_unpivot` expects. I kept that behaviour rather than changing it.
- With literal IN-lists (`IN ('x', 'y')`), the name and value columns have no upstream. I left that as is.

**Not addressed:** two UNPIVOTs over the *same* table in one query fail earlier, in the qualify step (`OptimizeError: Alias already used`), before lineage runs. That's an optimizer issue, so I left it alone.

## events
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50; grep -rln -i \"unpivot\" tests/ | head; git log --oneline --all -i --grep=unpivot | head", "description": "Inspect repo state and find UNPIVOT references"}
[tool_result] 00816f41d lithify: probe base
95179f5e5 eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/lineage.py:473:    if pivot.unpivot:
sqlglot/lineage.py:474:        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column
sqlglot/lineage.py:476:        unpivot_columns = [
sqlglot/lineage.py:484:                mapping[identifier.name] = unpivot_columns
sqlglot/lineage.py:487:                mapping[field.this.name] = unpivot_columns
sqlglot/optimizer/annotate
…[999 chars elided]…
8030)
5e08bb934 fix(oracle)!: preserve UNPIVOT IN-list literal labels [CLAUDE] (#7877)
f3ba8e4d2 Feat(lineage): more `UNPIVOT` lineage improvements (#7736)
74bef2f46 Feat(lineage): add support for `UNPIVOT` (#7729)
a20ec0ee4 fix(optimizer): unpivot annotate types (#7543)
cf0ffd99e fix(optimizer): qualify (UN)PIVOT on CTE sources (#7560)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
[tool_use Bash] {"command": "git merge-base --is-ancestor f3ba8e4d2 HEAD && echo ANCESTOR; git log --oneline HEAD -i --grep=unpivot | head; sed -n 380,520p sqlglot/lineage.py", "description": "Check ancestry and read lineage pivot handling"}
[tool_result] 74bef2f46 Feat(lineage): add support for `UNPIVOT` (#7729)
a20ec0ee4 fix(optimizer): unpivot annotate types (#7543)
cf0ffd99e fix(optimizer): qualify (UN)PIVOT on CTE sources (#7560)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
a83b51194 feat(parser): PIVOT/UNPIVOT pipe syntax (#5222)
c0c7b673b fix(optimizer)!: avoid creating new alias for qualifying unpivot (#5121)
d82e1733d Fix:
…[5882 chars elided]…
ount = len(pivot.expressions)

    mapping = {}
    for i, agg in enumerate(pivot.expressions):
        agg_cols = list(agg.find_all(exp.Column))
        for col_index in range(i, len(pivot_columns), pivot_aggs_count):
            mapping[pivot_columns[col_index].name] = agg_cols
    return mapping


class GraphHTML:
    """Node to HTML generator using vis.js.

    https://visjs.github.io/vis-network/docs/network/
    """

    def __init__(
        self,
        nodes: dict,
        edges: list,
[tool_use Bash] {"command": "git show 74bef2f46 --stat && grep -n -i \"unpivot\\|pivot\" tests/test_lineage.py | head -40; sed -n 300,380p sqlglot/lineage.py", "description": "Review initial UNPIVOT lineage commit and tests"}
[tool_result] commit 74bef2f4617f2fa25881dded12ae3851a7ddfa1f
Author: Jo <46752250+georgesittas@users.noreply.github.com>
Date:   Wed Jun 10 17:00:13 2026 +0300

    Feat(lineage): add support for `UNPIVOT` (#7729)

 sqlglot/lineage.py    | 69 ++++++++++++++++++++++++++++++++++++---------------
 tests/test_lineage.py | 35 ++++++++++++++++++++++++++
 2 files changed, 84 insertions(+), 20 deletions(-)
607:    def test_pivot_without_alias(self) -> None:
612:        PIVOT (
622:    def test_pivot_with_alias(self)
…[3238 chars elided]…
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
[tool_use Bash] {"command": "sed -n 600,730p tests/test_lineage.py; sed -n 760,800p tests/test_lineage.py; sed -n 1,60p tests/test_lineage.py | grep -n \"def \\|import\" ", "description": "Read existing pivot/unpivot lineage tests"}
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
…[5168 chars elided]…
tEqual(node.downstream[0].downstream[0].name, "_0.product_type")
        self.assertEqual(
            node.downstream[0].downstream[0].downstream[0].name,
            "loan_ledger.product_type",
        )

        node = lineage('"2024-10"', sql, dialect="duckdb", schema=schema)
1:from __future__ import annotations
3:import unittest
5:import sqlglot
6:from sqlglot.lineage import lineage
7:from sqlglot.schema import MappingSchema
14:    def setUpClass(cls):
17:    def test_lineage(self) -> None:
[tool_use Bash] {"command": "ls; which python; cat > /tmp/probe_unpivot.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one, exp\nfrom sqlglot.lineage import lineage\nfrom sqlglot.optimizer import qualify\nschema = {\"sales\": {\"id\": \"int\", \"region\": \"text\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = [\n (\"snowflake\", \"SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan
…[1470 chars elided]…
       out.extend(walk(c, d+1))\n                return out\n            print(f\"   [{col}]\"); print(\"\\n\".join(\"      \"+l for l in walk(node)) or \"      (no downstream)\")\n        except Exception as e:\n            print(f\"   [{col}] ERR {type(e).__name__}: {e}\")\nEOF\npython -I /tmp/probe_unpivot.py 2>&1 | head -150", "description": "Write probe script and run UNPIVOT lineage shapes"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
<work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "/tmp/probe_unpivot.py", line 2, in <module>
    from sqlglot import parse_one, exp
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. python /tmp/probe_unpivot.py 2>&1 | head -150", "description": "Run UNPIVOT lineage probe with repo on path"}
[tool_result] == SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
   PARSE/ERR 'from'
   [score]
      SALES.JAN
      SALES.FEB
   [metric_name]
      SALES.JAN
      SALES.FEB
   [id]
      SALES.ID
== SELECT s.id, u.score FROM sales AS s UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
   PARSE/ERR 'from'
   [score]
      S.JAN
      S.FEB
   [id]
      S.ID
== SELECT id, metric_name, score FROM sales UNPIVOT (score FOR metric_name IN (jan AS 'Jan', feb AS 'Feb'))
  
…[527 chars elided]…
ic_name IN (jan, feb))
   PARSE/ERR 'from'
   [ident]
      _0.ID
        SALES.ID
   [score]
      _0.JAN
        SALES.JAN
      _0.FEB
        SALES.FEB
== SELECT id, q, amt, qty FROM sales UNPIVOT ((amt, qty) FOR q IN ((jan, feb) AS 'Q1', (feb, jan) AS 'Q2'))
   PARSE/ERR 'from'
   [amt]
      SALES.JAN
      SALES.FEB
      SALES.FEB
      SALES.JAN
   [qty]
      SALES.JAN
      SALES.FEB
      SALES.FEB
      SALES.JAN
   [q]
      SALES.JAN
      SALES.FEB
      SALES.FEB
      SALES.JAN
[tool_use Bash] {"command": "cat > /tmp/probe2.py <<'EOF'\nfrom sqlglot.lineage import lineage\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}, \"dim\": {\"id\": \"int\", \"label\": \"text\"}}\ndef walk(n, d=0):\n    out = []\n    for c in n.downstream:\n        out.append(\"  \"*d + f\"{c.name}\")\n        out.extend(walk(c, d+1))\n    return out\nU = \"UNPIVOT (score FOR metric_name 
…[1243 chars elided]…
e = lineage(col, sql, schema=schema, dialect=dialect)\n            print(f\"   [{col}]\"); print(\"\\n\".join(\"      \"+l for l in walk(node)) or \"      (no downstream)\")\n        except Exception as e:\n            print(f\"   [{col}] ERR {type(e).__name__}: {e}\")\nEOF\nPYTHONPATH=. python /tmp/probe2.py 2>&1 | head -150", "description": "Probe join, nested, and multi-unpivot lineage shapes"}
[tool_result] == SELECT u.id, u.score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
   [id]
      SALES.ID
   [score]
      SALES.JAN
      SALES.FEB
== SELECT u.id, d.label FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u JOIN dim d ON d.id = u.id
   [id]
      SALES.ID
   [label]
      D.LABEL
== SELECT u.metric_name, d.label FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u JOIN dim d ON d.id = u.id
   [metric_name]
      SALES.JAN
      SALES.FEB
== SELECT x FROM (
…[632 chars elided]…
OT (score FOR metric_name IN (jan, feb)) AS y
   [score] ERR OptimizeError: Alias already used: SALES
== SELECT id, m, v FROM sales UNPIVOT (v FOR m IN ('x' AS jan, 'y' AS feb))
   [m]
      (no downstream)
   [v]
      (no downstream)
== SELECT id, score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) WHERE metric_name = 'jan'
   [score]
      SALES.JAN
      SALES.FEB
== SELECT * FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) 
   [metric_name]
      SALES.JAN
      SALES.FEB
[tool_use Bash] {"command": "cat > /tmp/probe3.py <<'EOF'\nfrom sqlglot.lineage import lineage\nfrom sqlglot import exp, parse_one\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}, \"prices\": {\"id\": \"int\", \"mar\": \"int\", \"apr\": \"int\"}, \"dim\": {\"id\": \"int\", \"label\": \"text\"}}\ndef walk(n, d=0):\n    out = []\n    for c in n.downstream:\n        out.append(\"  \"*d + 
…[754 chars elided]…
node = lineage(col, sql, schema=schema, dialect=dialect)\n            print(f\"   [{col}]\"); print(\"\\n\".join(\"      \"+l for l in walk(node)) or \"      (no downstream)\")\n        except Exception as e:\n            print(f\"   [{col}] ERR {type(e).__name__}: {e}\")\nEOF\nPYTHONPATH=. python /tmp/probe3.py 2>&1 | head -80", "description": "Probe multi-unpivot and multi-value lineage shapes"}
[tool_result] == SELECT u.score, v.price FROM sales UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN prices UNPIVOT (price FOR n IN (mar, apr)) AS v ON u.id = v.id
   [score]
      U.SCORE
   [price]
      V.PRICE
== SELECT u.score, d.label FROM sales UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN dim d ON u.id = d.id
   [score]
      SALES.JAN
      SALES.FEB
== SELECT id, q, amt, qty FROM sales UNPIVOT ((amt, qty) FOR q IN ((jan, feb) AS 'Q1', (feb, jan) AS 'Q2'))
   [amt]
      SALES.JAN
      SALES.FEB
      SALES.FEB
      SALES.JAN
   [qty]
      SALES.JAN
      SALES.FEB
      SALES.FEB
      SALES.JAN
== SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))
   [score]
      SALES.JAN
      SALES.FEB
[tool_use Bash] {"command": "cat > /tmp/probe4.py <<'EOF'\nfrom sqlglot import exp, parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.scope import build_scope\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}, \"prices\": {\"id\": \"int\", \"mar\": \"int\", \"apr\": \"int\"}}\nfor sql in [\n \"SELECT id, score FROM sales UNPIVOT (score FOR m IN (jan, feb))\
…[437 chars elided]…
ake\")\n    print(q.sql(\"snowflake\"))\n    s = build_scope(q)\n    print(\"  pivots:\", [(p.alias_or_name, p.parent.__class__.__name__, p.parent.alias_or_name) for sc in s.traverse() for p in sc.pivots])\n    print(\"  cols:\", [(c.table, c.name) for c in q.find_all(exp.Column)])\nEOF\nPYTHONPATH=. python /tmp/probe4.py 2>&1 | head -60", "description": "Inspect qualified AST for unpivot shapes"}
[tool_result] SELECT "SALES"."ID" AS "ID", "SALES"."SCORE" AS "SCORE" FROM "SALES" AS "SALES" UNPIVOT("SCORE" FOR "M" IN ("JAN", "FEB")) AS "SALES"
  pivots: [('SALES', 'Table', 'SALES')]
  cols: [('SALES', 'ID'), ('SALES', 'SCORE'), ('SALES', 'JAN'), ('SALES', 'FEB')]
SELECT "U"."ID" AS "ID", "U"."SCORE" AS "SCORE" FROM "SALES" AS "SALES" UNPIVOT("SCORE" FOR "M" IN ("JAN", "FEB")) AS "U"
  pivots: [('U', 'Table', 'SALES')]
  cols: [('U', 'ID'), ('U', 'SCORE'), ('SALES', 'JAN'), ('SALES', 'FEB')]
SELECT "U"."
…[319 chars elided]…
'U', 'ID'), ('V', 'ID'), ('SALES', 'JAN'), ('SALES', 'FEB'), ('PRICES', 'MAR'), ('PRICES', 'APR')]
SELECT "SALES"."ID" AS "ID", "SALES"."SCORE" AS "SCORE" FROM "SALES" AS "SALES" UNPIVOT("SCORE" FOR "M" IN ("JAN", "FEB")) AS "SALES", "PRICES" AS "PRICES" UNPIVOT("PRICE" FOR "N" IN ("MAR", "APR")) AS "PRICES"
  pivots: [('SALES', 'Table', 'SALES'), ('PRICES', 'Table', 'PRICES')]
  cols: [('SALES', 'ID'), ('SALES', 'SCORE'), ('SALES', 'JAN'), ('SALES', 'FEB'), ('PRICES', 'MAR'), ('PRICES', 'APR')]
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nfrom sqlglot import parse_one, exp\nfor d,s in [('oracle','SELECT * FROM sales UNPIVOT ((amt, qty) FOR q IN ((jan, feb) AS \\'Q1\\', (feb, jan) AS \\'Q2\\'))'),('snowflake','SELECT * FROM sales UNPIVOT (score FOR m IN (jan AS \\'J\\', feb))'),('duckdb','SELECT * FROM sales UNPIVOT (score FOR m IN (jan AS \\'J\\', feb)) AS u')]:\n    p = parse_one(s, read=d).
…[104 chars elided]…
ressions], [e.sql() for e in p.expressions])\n    for f in p.fields:\n        print(' field', type(f).__name__, f.this.sql(), [ (type(e).__name__, e.sql()) for e in f.expressions])\n\"; grep -n \"def _parse_pivot\\b\" -A60 sqlglot/parsers/*.py sqlglot/parser.py | grep -n \"unpivot\\|In(\\|fields\\|expressions\" | head -30", "description": "Inspect UNPIVOT AST structure for single and multi-value"}
[tool_result] oracle dict_keys(['expressions', 'fields', 'unpivot', 'include_nulls', 'default_on_null', 'group'])
 expressions ['Tuple'] ['(amt, qty)']
 field In q [('PivotAlias', "(jan, feb) AS 'Q1'"), ('PivotAlias', "(feb, jan) AS 'Q2'")]
snowflake dict_keys(['expressions', 'fields', 'unpivot', 'include_nulls', 'default_on_null', 'group'])
 expressions ['Identifier'] ['score']
 field In m [('PivotAlias', "jan AS 'J'"), ('Column', 'feb')]
duckdb dict_keys(['expressions', 'fields', 'unpivot', 'include_nulls',
…[552 chars elided]…
parse_column)
27:sqlglot/parser.py-5214-            expressions = self._parse_csv(self._parse_pivot_aggregation)
29:sqlglot/parser.py-5216-        if not expressions:
35:sqlglot/parser.py-5222-        fields = []
40:sqlglot/parser.py-5227-            fields.append(field)
52:sqlglot/parser.py-5239-                expressions=expressions,
53:sqlglot/parser.py-5240-                fields=fields,
54:sqlglot/parser.py-5241-                unpivot=unpivot,
61:sqlglot/parser.py-5248-        if unpivot:
[tool_use Bash] {"command": "grep -rn \"class PivotAlias\" sqlglot/expressions/ ; grep -n \":= \" sqlglot/lineage.py | head -3; grep -n \"^from\\|^import\" sqlglot/lineage.py", "description": "Check PivotAlias base class and imports in lineage"}
[tool_result] sqlglot/expressions/core.py:1905:class PivotAlias(Alias):
1:from __future__ import annotations
3:import json
4:import logging
5:import typing as t
6:from dataclasses import dataclass, field
8:from sqlglot import Schema, exp, maybe_parse
9:from sqlglot.errors import SqlglotError
10:from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
11:from sqlglot.optimizer.scope import ScopeType
[assistant] Confirmed two concrete gaps: a scope with two (UN)PIVOTs loses lineage entirely (`score` becomes a dead leaf), and multi-value `UNPIVOT((a, b) ...)` maps every value column to every IN-list column. Fixing both now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095509-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1594 chars elided]…
s, positional_columns):\n            for identifier in value_column.find_all(exp.Identifier):\n                mapping[identifier.name] = columns\n\n        unpivot_columns = [col for columns in positional_columns for col in columns]\n        for field in pivot.fields:\n            if isinstance(field, exp.In):\n                mapping[field.this.name] = unpivot_columns\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095509-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095509-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "        value_columns = pivot.expressions[0].expressions if len(pivot.expressions) == 1 and isinstance(pivot.expressions[0], exp.Tuple) else pivot.expressions\n        for value_column, columns in zip(value_columns, positional_columns):", "new_string": "        value_columns = pivot.expressions\n        if len(value_columns) == 1 and isinstance(value_columns[0], exp.Tuple):\n            value_columns = value_columns[0].expressions\n\n        for value_column, columns in zip(value_columns, positional_columns):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095509-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the pivot lookup: pick the (UN)PIVOT that owns the column's table alias instead of requiring exactly one pivot per scope.
[tool_use Bash] {"command": "python - <<'EOF'\nimport re\np = \"sqlglot/lineage.py\"\ns = open(p).read()\nold1 = \"\"\"    pivots = scope.pivots\n    pivot = pivots[0] if len(pivots) == 1 else None\n    pivot_column_mapping = _pivot_column_mapping(pivot) if pivot else {}\n\n\"\"\"\nnew1 = \"\"\"    pivots = {pivot.alias_or_name: pivot for pivot in scope.pivots}\n\n\"\"\"\nold2 = \"\"\"        elif pivot and pivot
…[281 chars elided]…
olumns = []\n\n            column_name = c.name\n\"\"\"\nassert s.count(old1) == 1 and s.count(old2) == 1\ns = s.replace(old1, new1).replace(old2, new2)\nopen(p, \"w\").write(s)\nEOF\nPYTHONPATH=. python /tmp/probe3.py; PYTHONPATH=. python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Apply pivot lookup change and rerun probe and lineage tests"}
[tool_result] == SELECT u.score, v.price FROM sales UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN prices UNPIVOT (price FOR n IN (mar, apr)) AS v ON u.id = v.id
   [score]
      SALES.JAN
      SALES.FEB
   [price]
      PRICES.MAR
      PRICES.APR
== SELECT u.score, d.label FROM sales UNPIVOT (score FOR m IN (jan, feb)) AS u JOIN dim d ON u.id = d.id
   [score]
      SALES.JAN
      SALES.FEB
== SELECT id, q, amt, qty FROM sales UNPIVOT ((amt, qty) FOR q IN ((jan, feb) AS 'Q1', (feb, jan) AS 'Q2'))
   [amt]
      SALES.JAN
      SALES.FEB
   [qty]
      SALES.FEB
      SALES.JAN
== SELECT * FROM sales UNPIVOT (score FOR m IN (jan, feb))
   [score]
      SALES.JAN
      SALES.FEB
........................................                                 [100%]
40 passed in 0.09s
[assistant] The file changed on disk after my last edit, so I'll re-read the changed regions before going further.
[tool_use Bash] {"command": "git diff && git status --short", "description": "Show current diff of working tree"}
[tool_result] diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 6db18a09f..2b3392c7a 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -371,9 +371,7 @@ def to_node(
         if dt.comments and dt.comments[0].startswith("source: ")
     }
 
-    pivots = scope.pivots
-    pivot = pivots[0] if len(pivots) == 1 else None
-    pivot_column_mapping = _pivot_column_mapping(pivot) if pivot else {}
+    pivots = {pivot.alias_or_name: pivot for pivot in scope.pivots}
 
     for c in source_columns:

…[2018 chars elided]…
 for value_column, columns in zip(value_columns, positional_columns):
             for identifier in value_column.find_all(exp.Identifier):
-                mapping[identifier.name] = unpivot_columns
+                mapping[identifier.name] = columns
+
+        unpivot_columns = [col for columns in positional_columns for col in columns]
         for field in pivot.fields:
             if isinstance(field, exp.In):
                 mapping[field.this.name] = unpivot_columns
 M sqlglot/lineage.py
[assistant] The diff matches what I intended. Next I'll add regression tests next to the existing UNPIVOT tests.
[tool_use Bash] {"command": "python - <<'EOF'\np = \"tests/test_lineage.py\"\ns = open(p).read()\nanchor = \"    def test_table_udtf_snowflake(self) -> None:\\n\"\nnew = '''    def test_unpivot_with_multiple_value_columns(self) -> None:\n        sql = \"\"\"\n        SELECT id, q, amt, qty\n        FROM sales UNPIVOT ((amt, qty) FOR q IN ((jan, feb) AS 'Q1', (feb, jan) AS 'Q2'))\n        \"\"\"\n        schema = 
…[1480 chars elided]…
d\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"SALES.ID\"])\n\n'''\nassert s.count(anchor) == 1\ns = s.replace(anchor, new + anchor)\nopen(p, \"w\").write(s)\nEOF\nPYTHONPATH=. python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Add UNPIVOT lineage regression tests and run them"}
[tool_result] ..........................................                               [100%]
42 passed in 0.10s
[assistant] Both new tests pass, and the probe output showed the old code failing these exact shapes. Now the full suite plus lint/format.
[tool_use Bash] {"command": "PYTHONPATH=. python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -5; (ruff --version && ruff check sqlglot/lineage.py tests/test_lineage.py && ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -8", "description": "Run full test suite and ruff lint/format check"}
[tool_result] ............................ [ 51%]
................................................................................................................................................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
..............................................            [100%]
1119 passed, 18166 subtests passed in 57.83s
ruff 0.15.6
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "(mypy sqlglot/lineage.py 2>&1 | tail -3) ; git diff --stat", "description": "Run mypy on lineage module and show diff stat"}
[tool_result] Success: no issues found in 1 source file
 sqlglot/lineage.py    | 40 ++++++++++++++++++++++++++--------------
 tests/test_lineage.py | 38 ++++++++++++++++++++++++++++++++++++++
 2 files changed, 64 insertions(+), 14 deletions(-)
[assistant] UNPIVOT lineage now handles two more query shapes: a scope with several (UN)PIVOTs, and multi-value `UNPIVOT((a, b) FOR ...)`. The full suite passes (1119 tests), along with ruff and mypy on the changed files. The changes are uncommitted.

**What was broken**

- **Two pivots in one scope:** the lookup only worked when a scope had exactly one pivot. With two, `score` in `FROM sales UNPIVOT (...) AS u JOIN prices UNPIVOT (...) AS v` became a dead leaf with no link to `SALES.JAN`/`SALES.FEB`.
- **Multi-value UNPIVOT:** every value column was mapped to every IN-list column. `amt` and `qty` both sh
…[621 chars elided]…
alue_columns` covers the Oracle tuple form.
- `test_unpivot_with_multiple_sources` covers two UNPIVOTs joined in one scope.

**Choices I made**

- The name column still maps to the IN-list columns, as the existing `test_unpivot` expects. I kept that behaviour rather than changing it.
- With literal IN-lists (`IN ('x', 'y')`), the name and value columns have no upstream. I left that as is.

**Not addressed:** two UNPIVOTs over the *same* table in one query fail earlier, in the qualify step (`OptimizeError: Alias already used`), before lineage runs. That's an optimizer issue, so I left it alone.
