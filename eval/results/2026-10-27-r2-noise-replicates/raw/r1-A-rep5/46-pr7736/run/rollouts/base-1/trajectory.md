# trajectory base-1

final message:
UNPIVOT lineage is now correct for multi-column unpivots, where the value columns were previously over-attributed to every IN-list column. Aliased and pass-through shapes already worked, and I added regression tests for both. The full suite passes (1119 tests).

**What changed**
- `sqlglot/lineage.py`, `_pivot_column_mapping`: each value column now maps to the IN-list element in the same position. Before, `UNPIVOT((amount, quantity) FOR m IN ((jan_amt, jan_qty), (feb_amt, feb_qty)))` gave `amount` the lineage `jan_amt, jan_qty, feb_amt, feb_qty`. It now gives `jan_amt, feb_amt`, and `quantity` gives `jan_qty, feb_qty`. The `(...) AS 'alias'` form is handled too.
- `tests/test_lineage.py`: two new tests, one for multi-column value lineage and one for aliased UNPIVOT with pass-through and value columns.

**Choices I made**
- The name column still maps to all IN-list source columns. Semantically its values are literal column names, but the existing `test_unpivot` asserts the current behaviour and I didn't weaken it.
- I left the comment-line and formatting conventions as the existing code has them.

**Checked and already correct** (no change needed): aliased outer and inner UNPIVOT, pass-through through a CTE or derived table, pass-through in a join, `INCLUDE NULLS`, and value columns used in aggregates or WHERE.

**Not fixed:** chained UNPIVOTs (`... UNPIVOT (a ...) UNPIVOT (b ...)`) still fall back to the raw source table, so `score2` reports `SALES.SCORE2` instead of the real inputs. The code only handles a single PIVOT/UNPIVOT per scope, and handling chains would need recursion through the pivot chain. I left it out to keep this change small. Say if you want it done next.

## events
[tool_use Bash] {"command": "git log --oneline -3 && grep -rn -i \"unpivot\" sqlglot/lineage.py sqlglot/optimizer/*.py | head -50; grep -rln -i \"unpivot\" tests/ | head", "description": "Find UNPIVOT references in lineage and optimizer"}
[tool_result] 33fa96f94 lithify: probe base
6f87f8fca eval setup at ffd3a1401ffd
ffd3a1401 Sync w/ integration tests
sqlglot/optimizer/annotate_types.py:368:                            self._get_unpivot_column_types(pivot, src_types)
sqlglot/optimizer/annotate_types.py:369:                            if pivot.unpivot
sqlglot/optimizer/annotate_types.py:658:    def _get_unpivot_column_types(
sqlglot/lineage.py:473:    if pivot.unpivot:
sqlglot/lineage.py:474:        # UNPIVOT(val FOR name IN (a, b)): both the 
…[273 chars elided]…
ify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
sqlglot/optimizer/qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
tests/test_optimizer.py
tests/dialects/test_databricks.py
tests/test_lineage.py
tests/test_transpile.py
tests/dialects/test_oracle.py
tests/dialects/test_snowflake.py
tests/dialects/test_redshift.py
tests/dialects/test_duckdb.py
tests/dialects/test_bigquery.py
tests/fixtures/optimizer/optimizer.sql
[tool_use Bash] {"command": "sed -n 420,560p sqlglot/lineage.py; grep -n -i \"unpivot\" tests/test_lineage.py", "description": "Read lineage pivot handling and existing tests"}
[tool_result]                 col_source = scope.sources.get(table)
                if isinstance(col_source, exp.Table) and not col_source.db:
                    # A pivoted CTE reference maps to the raw table in `scope.sources`,
                    # so recover the CTE's scope to keep tracing through it
                    col_source = scope.cte_sources.get(col_source.name, col_source)
                if isinstance(col_source, Scope):
                    to_node(
                        downstream_column.n
…[4586 chars elided]…
           "widthConstraint": {
                    "maximum": 300,
                },
            },
            **(options or {}),
        }

        self.nodes = nodes
        self.edges = edges

    def __str__(self):
        nodes = json.dumps(list(self.nodes.values()))
688:    def test_unpivot(self) -> None:
691:        FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
704:    def test_unpivot_with_cte(self) -> None:
710:        FROM src UNPIVOT (score FOR metric_name IN (jan, feb))
[tool_use Bash] {"command": "sed -n 340,420p sqlglot/lineage.py; sed -n 640,730p tests/test_lineage.py", "description": "Read pivot lineage logic and existing UNPIVOT tests"}
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
…[5844 chars elided]…
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
[tool_use Bash] {"command": "mkdir -p /tmp/unp && cat > /tmp/unp/probe.py <<'EOF'\nimport sys\nfrom sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"int\"}, \"other\": {\"id\": \"int\", \"name\": \"varchar\"}}\ncases = {\n \"alias_outer\": (\"u.score\", \"\"\"SELECT u.id, u.metric_name, u.score FROM sales UNPIVOT (score FOR metric_name IN (
…[1789 chars elided]…
how(n, depth=0):\n            print(\"  \"*depth + n.name)\n            for c in n.downstream: show(c, depth+1)\n        show(node, 1)\n    except Exception as e:\n        print(\"==\", name, \"ERROR\", type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python /tmp/unp/probe.py 2>&1 | head -150", "description": "Probe UNPIVOT lineage across query shapes"}
[tool_result] Traceback (most recent call last):
  File "/tmp/unp/probe.py", line 2, in <module>
    from sqlglot.lineage import lineage
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe.py 2>&1 | head -150", "description": "Run UNPIVOT probe with repo on path"}
[tool_result] == alias_outer ERROR SqlglotError Cannot find column 'u.score' in query.
== alias_in_from ERROR SqlglotError Cannot find column 'u.score' in query.
== subquery score
  SCORE
    _0.JAN
      SALES.JAN
    _0.FEB
      SALES.FEB
== in_alias score
  SCORE
    SALES.JAN
    SALES.FEB
== passthrough_join id
  ID
    SALES.ID
== passthrough_join_name name
  NAME
    O.NAME
== multi_value_v1 score
  SCORE
    SALES.JAN
    SALES.REGION
    SALES.FEB
    SALES.ID
== multi_value_v2 reg
  REG
    SALES.JAN
    SALES.REGION
    SALES.FEB
    SALES.ID
== select_star_passthru id
  ID
    SALES.ID
== cte_passthrough id
  ID
    X.ID
      SALES.ID
== expr_in_select score2
  SCORE2
    SALES.JAN
    SALES.FEB
[tool_use Bash] {"command": "sed -i 's/(\"u.score\", \"\"\"SELECT u.id, u.metric_name, u.score/(\"score\", \"\"\"SELECT u.id, u.metric_name, u.score/; s/(\"u.score\", \"\"\"SELECT u.score/(\"score\", \"\"\"SELECT u.score/' /tmp/unp/probe.py && cat >> /tmp/unp/probe.py <<'EOF'\nfor col, sql in [\n (\"metric_name\", \"SELECT metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u\"),\n (\"metric_n
…[509 chars elided]…
  node = lineage(col, sql, schema=schema, dialect=\"oracle\")\n        print(\"==\", col, \"|\", sql[:70]); show(node, 1)\n    except Exception as e:\n        print(\"==\", col, \"ERROR\", type(e).__name__, e)\nEOF\nPYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe.py 2>&1 | head -150", "description": "Re-run probe with aliased UNPIVOT cases"}
[tool_result] sed: 1: "/tmp/unp/probe.py
": invalid command code u
== alias_outer ERROR SqlglotError Cannot find column 'u.score' in query.
== alias_in_from ERROR SqlglotError Cannot find column 'u.score' in query.
== subquery score
  SCORE
    _0.JAN
      SALES.JAN
    _0.FEB
      SALES.FEB
== in_alias score
  SCORE
    SALES.JAN
    SALES.FEB
== passthrough_join id
  ID
    SALES.ID
== passthrough_join_name name
  NAME
    O.NAME
== multi_value_v1 score
  SCORE
    SALES.JAN
    SALES.REGION
    SALES.FEB
    SALES.ID
== multi_value_v2 reg
  REG
    SALES.JAN
    SALES.REGION
    SALES.FEB
    SALES.ID
== select_star_passthru id
  ID
    SALES.ID
== cte_passthrough id
  ID
    X.ID
      SALES.ID
== expr_in_select score2
  SCORE2
    SALES.JAN
    SALES.FEB
[tool_use Write] {"file_path": "/tmp/unp/probe2.py", "content": "from sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"int\"}, \"other\": {\"id\": \"int\", \"name\": \"varchar\"}}\n\n\ndef show(n, depth=1):\n    print(\"  \" * depth + n.name)\n    for c in n.downstream:\n        show(c, depth + 1)\n\n\ncases = [\n    (\"score\", \"SELECT u.s
…[1781 chars elided]…
gion > 1\"),\n    (\"region\", \"SELECT region FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) WHERE region > 1\"),\n]\nfor col, sql in cases:\n    try:\n        node = lineage(col, sql, schema=schema, dialect=\"oracle\")\n        print(\"==\", col, \"|\", sql)\n        show(node)\n    except Exception as e:\n        print(\"==\", col, \"|\", sql, \"\\n   ERROR\", type(e).__name__, e)\n"}
[tool_result] The file /tmp/unp/probe2.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe2.py 2>&1", "description": "Run UNPIVOT probe with aliased and other shapes"}
[tool_result] == score | SELECT u.score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  SCORE
    SALES.JAN
    SALES.FEB
== score | SELECT u.id, u.metric_name, u.score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  SCORE
    SALES.JAN
    SALES.FEB
== metric_name | SELECT u.metric_name FROM sales AS s UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  METRIC_NAME
    S.JAN
    S.FEB
== region | SELECT region FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  REGION

…[1443 chars elided]…
M sales) SELECT id FROM x UNPIVOT (score FOR metric_name IN (jan, feb))
  ID
    X.ID
      SALES.ID
== score | SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) UNPIVOT (score2 FOR m2 IN (score))
  SCORE
    SALES.SCORE
== score | SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) WHERE region > 1
  SCORE
    SALES.JAN
    SALES.FEB
== region | SELECT region FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) WHERE region > 1
  REGION
    SALES.REGION
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT score FROM sales UNPIVOT ((score, reg) FOR metric_name IN ((jan, region), (feb, id)))', read='oracle')\np = e.find(exp.Pivot)\nprint(repr(p.expressions)); print(repr(p.fields))\nprint(p.alias_or_name)\ne = sqlglot.parse_one('SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan AS \\'J\\', feb))', read='oracle')\nprint(repr(e.find(exp.Pivot).fields))\n\" 2>&1 | head -40", "description": "Inspect UNPIVOT AST for multi-value form"}
[tool_result] [Tuple(
  expressions=[
    Identifier(this=score, quoted=False),
    Identifier(this=reg, quoted=False)],
  join_mark=False)]
[In(
  this=Identifier(this=metric_name, quoted=False),
  expressions=[
    Tuple(
      expressions=[
        Column(
          this=Identifier(this=jan, quoted=False),
          join_mark=False),
        Column(
          this=Identifier(this=region, quoted=False),
          join_mark=False)],
      join_mark=False),
    Tuple(
      expressions=[
        Column(
     
…[10 chars elided]…
Identifier(this=feb, quoted=False),
          join_mark=False),
        Column(
          this=Identifier(this=id, quoted=False),
          join_mark=False)],
      join_mark=False)])]

[In(
  this=Identifier(this=metric_name, quoted=False),
  expressions=[
    PivotAlias(
      this=Column(
        this=Identifier(this=jan, quoted=False),
        join_mark=False),
      alias=Literal(this='J', is_string=True)),
    Column(
      this=Identifier(this=feb, quoted=False),
      join_mark=False)])]
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT score FROM sales UNPIVOT ((score, reg) FOR m IN ((jan, region) AS \\'J\\', (feb, id)))', read='oracle')\nprint(repr(e.find(exp.Pivot).fields[0].expressions[0]))\n\" 2>&1 | head -30; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Check PivotAlias around tuple and baseline lineage tests"}
[tool_result] PivotAlias(
  this=Tuple(
    expressions=[
      Column(
        this=Identifier(this=jan, quoted=False),
        join_mark=False),
      Column(
        this=Identifier(this=region, quoted=False),
        join_mark=False)],
    join_mark=False),
  alias=Literal(this='J', is_string=True))
........................................                                 [100%]
40 passed in 0.17s
[assistant] The current code gives every value column the full IN-list, so a multi-column UNPIVOT over-approximates. I'll map each value column to its matching position in each IN-list tuple, including the `(...) AS 'alias'` form.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "    if pivot.unpivot:\n        # UNPIVOT(val FOR name IN (a, b)): both the value column(s) and the name column\n        # are derived from the IN-list source columns\n        unpivot_columns = [\n            col\n      
…[1299 chars elided]…
xpressions:\n                if isinstance(in_item, exp.PivotAlias):\n                    in_item = in_item.this\n\n                sources = in_item.expressions if isinstance(in_item, exp.Tuple) else [in_item]\n                for value_name, source in zip(value_names, sources):\n                    mapping.setdefault(value_name, []).extend(source.find_all(exp.Column))\n\n        return mapping"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe2.py 2>&1 | sed -n '/reg |/,/metric_name |/p' ; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nschema = {'sales': {'id': 'int', 'jan': 'int', 'feb': 'int', 'region': 'int'}}\nfor col in ['score','
…[281 chars elided]…
NPIVOT ((score, reg) FOR metric_name IN ((jan, region), (feb, id))) AS u', schema=schema, dialect='oracle')\nprint([d.name for d in n.downstream])\n\" ; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Verify multi-value UNPIVOT mapping and run lineage tests"}
[tool_result] == reg | SELECT reg FROM sales UNPIVOT ((score, reg) FOR metric_name IN ((jan, region), (feb, id)))
  REG
    SALES.REGION
    SALES.ID
== metric_name | SELECT metric_name FROM sales UNPIVOT ((score, reg) FOR metric_name IN ((jan, region), (feb, id)))
score ['SALES.JAN', 'SALES.FEB']
reg ['SALES.REGION', 'SALES.ID']
metric_name ['SALES.JAN', 'SALES.REGION', 'SALES.FEB', 'SALES.ID']
['SALES.REGION', 'SALES.ID']
........................................                                 [100%]
40 passed in 0.09s
[assistant] Multi-value mapping is now positional and the existing 40 lineage tests pass. Next I'll check the pass-through shapes.
[tool_use Write] {"file_path": "/tmp/unp/probe3.py", "content": "from sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"int\"}, \"other\": {\"id\": \"int\", \"name\": \"varchar\"}}\n\n\ndef show(n, depth=1):\n    print(\"  \" * depth + n.name)\n    for c in n.downstream:\n        show(c, depth + 1)\n\n\ncases = [\n    (\"id\", \"SELECT sales.
…[1099 chars elided]…
\", \"WITH u AS (SELECT score, metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))) SELECT score FROM u\"),\n]\nfor col, sql in cases:\n    try:\n        node = lineage(col, sql, schema=schema, dialect=\"oracle\")\n        print(\"==\", col, \"|\", sql)\n        show(node)\n    except Exception as e:\n        print(\"==\", col, \"|\", sql, \"\\n   ERROR\", type(e).__name__, e)\n"}
[tool_result] The file /tmp/unp/probe3.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe3.py 2>&1", "description": "Run pass-through UNPIVOT lineage probe"}
[tool_result] == id | SELECT sales.id FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  ID
    SALES.ID
== region | SELECT u.region FROM sales AS s UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  REGION
    S.REGION
== id | SELECT u.id FROM (SELECT id, jan, feb FROM sales) AS s UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  ID
    S.ID
      SALES.ID
== name | SELECT u.name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u JOIN other AS o ON u.id = o.id
  NAME
    SALES.NAME
==
…[491 chars elided]…
ales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  TOTAL
    SALES.JAN
    SALES.FEB
== score | SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) WHERE score > 0
  SCORE
    SALES.JAN
    SALES.FEB
== id | SELECT id FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) AS u
  ID
    SALES.ID
== score | WITH u AS (SELECT score, metric_name FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))) SELECT score FROM u
  SCORE
    U.SCORE
      SALES.JAN
      SALES.FEB
[assistant] Pass-through columns resolve correctly in these shapes. The `Cannot find column` errors are my probe asking for the wrong output name, not a bug. Now I'll check stars and chained UNPIVOTs, which fall back to the raw table today.
[tool_use Write] {"file_path": "/tmp/unp/probe4.py", "content": "from sqlglot.lineage import lineage\n\nschema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\", \"region\": \"int\"}}\n\n\ndef show(n, depth=1):\n    print(\"  \" * depth + n.name)\n    for c in n.downstream:\n        show(c, depth + 1)\n\n\ncases = [\n    (\"id\", \"SELECT * FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score FOR 
…[470 chars elided]…
(\"score2\", \"SELECT score2 FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) UNPIVOT (score2 FOR m2 IN (score))\"),\n]\nfor col, sql in cases:\n    try:\n        node = lineage(col, sql, schema=schema, dialect=\"oracle\")\n        print(\"==\", col, \"|\", sql)\n        show(node)\n    except Exception as e:\n        print(\"==\", col, \"|\", sql, \"\\n   ERROR\", type(e).__name__, e)\n"}
[tool_result] The file /tmp/unp/probe4.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unp/probe4.py 2>&1", "description": "Probe star and chained UNPIVOT lineage"}
[tool_result] == id | SELECT * FROM (SELECT id, jan, feb FROM sales) UNPIVOT (score FOR metric_name IN (jan, feb))
  ID
    _0.ID
      SALES.ID
== score | SELECT * FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  SCORE
    SALES.JAN
    SALES.FEB
== metric_name | SELECT * FROM sales UNPIVOT (score FOR metric_name IN (jan, feb))
  METRIC_NAME
    SALES.JAN
    SALES.FEB
== id | SELECT id FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) UNPIVOT (score2 FOR m2 IN (score))
  ID
    SALES.ID
== score | SELECT score FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) UNPIVOT (score2 FOR m2 IN (score))
  SCORE
    SALES.SCORE
== score2 | SELECT score2 FROM sales UNPIVOT (score FOR metric_name IN (jan, feb)) UNPIVOT (score2 FOR m2 IN (score))
  SCORE2
    SALES.SCORE2
[assistant] Chained UNPIVOTs still fall back to the raw table, which is a separate gap I'll report rather than expand into. Now I'll add regression tests for the multi-value and pass-through shapes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/tests/test_lineage.py", "old_string": "        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual(node.downstream[0].name, \"SRC.ID\")\n        self.assertEqual(node.downstream[0].downstream[0].name, \"SALES.ID\")\
…[1501 chars elided]…
      schema = {\"sales\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\n\n        node = lineage(\"id\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"S.ID\"])\n\n        node = lineage(\"score\", sql, schema=schema, dialect=\"snowflake\")\n        self.assertEqual([d.name for d in node.downstream], [\"S.JAN\", \"S.FEB\"])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30; git stash list >/dev/null; git diff --stat", "description": "Run lineage tests including new UNPIVOT tests"}
[tool_result] ..........................................                               [100%]
42 passed in 0.11s
 sqlglot/lineage.py    | 22 +++++++++++++++-------
 tests/test_lineage.py | 34 ++++++++++++++++++++++++++++++++++
 2 files changed, 49 insertions(+), 7 deletions(-)
[assistant] The lineage tests pass (42, including the 2 new ones). Next I'll run the full project check and the linter on the changed file.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff --version && $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py) 2>&1 | tail -15", "description": "Run full test suite and ruff checks"}
[tool_result] ............................ [ 51%]
................................................................................................................................................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
..............................................            [100%]
1119 passed, 18166 subtests passed in 57.38s
ruff 0.15.6
All checks passed!
Would reformat: sqlglot/lineage.py
Would reformat: tests/test_lineage.py
2 files would be reformatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git stash list >/dev/null; git show HEAD:sqlglot/lineage.py > /tmp/unp/orig_lineage.py; git show HEAD:tests/test_lineage.py > /tmp/unp/orig_test_lineage.py; $PY -m ruff format --diff sqlglot/lineage.py tests/test_lineage.py 2>&1 | head -60; echo ---; $PY -m ruff format --diff /tmp/unp/orig_lineage.py /tmp/unp/orig_test_lineage.py 2>&1 | head -5", "description": "Show ruff format diff for changed files"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -474,7 +474,11 @@
         # UNPIVOT(val FOR name IN (a, b)): the name column is derived from all the IN-list source columns
         # UNPIVOT((v1, v2) FOR name IN ((a1, a2), (b1, b2))): v1 is derived from the first element of each
         # IN-list tuple (a1, b1) and v2 from the second (a2, b2)
-        value_names = [identifier.name for value in pivot.expressions for identifier in value.find_all(exp.Identifier)]
+        value_names = [
+     
…[405 chars elided]…
))
         """
         schema = {
-            "sales": {"id": "int", "jan_amt": "int", "jan_qty": "int", "feb_amt": "int", "feb_qty": "int"}
+            "sales": {
+                "id": "int",
+                "jan_amt": "int",
+                "jan_qty": "int",
+                "feb_amt": "int",
+                "feb_qty": "int",
+            }
         }
 
         node = lineage("amount", sql, schema=schema, dialect="snowflake")

2 files would be reformatted
---
2 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py tests/test_optimizer.py 2>&1 | tail -2 && git diff sqlglot/lineage.py", "description": "Apply ruff formatting and re-run targeted tests"}
[tool_result] 2 files reformatted
All checks passed!
.........................................................................................................................   [100%]
121 passed, 3909 subtests passed in 17.04s
diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 6db18a09f..0af688225 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -471,20 +471,32 @@ def _pivot_column_mapping(pivot: exp.Pivot) -> dict[str, list[exp.Column]]:
     mapping: dict[str, list[exp.Column]] = {}
 
   
…[1305 chars elided]…
      if isinstance(in_item, exp.PivotAlias):
+                    in_item = in_item.this
+
+                sources = in_item.expressions if isinstance(in_item, exp.Tuple) else [in_item]
+                for value_name, source in zip(value_names, sources):
+                    mapping.setdefault(value_name, []).extend(source.find_all(exp.Column))
 
         return mapping
[This command modified 2 files you've previously read: tests/test_lineage.py, sqlglot/lineage.py. Call Read before editing.]
[assistant] The diff is what I intended; the on-disk note is just my ruff reformat. Two comment lines run past 100 columns, so I'll tighten them and re-run.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/sqlglot/lineage.py", "old_string": "        # UNPIVOT(val FOR name IN (a, b)): the name column is derived from all the IN-list source columns\n        # UNPIVOT((v1, v2) FOR name IN ((a1, a2), (b1, b2))): v1 is derived from the first element of each\n        # IN-list tuple (a1, b1) and v2 from the second (a2, b2)", "new_string": "        # UNPIVOT(val FOR name IN (a, b)): the name column is derived from all IN-list columns\n        # UNPIVOT((v1, v2) FOR name IN ((a1, a2), (b1, b2))): v1 is derived from a1 and b1,\n        # v2 from a2 and b2"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124138-lineage-further-improve-lineage/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; rm -rf /tmp/unp; git status --short", "description": "Final format, lint, and full test run"}
[tool_result ERROR] Exit code 144
2 files already formatted
All checks passed!
[assistant] The full run exited with code 144 before reporting, so I'll re-run it on its own.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short", "description": "Re-run full test suite", "timeout": 300000}
[tool_result] .............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
..............................................            [100%]
1119 passed, 18166 subtests passed in 103.88s (0:01:43)
 M sqlglot/lineage.py
 M tests/test_lineage.py
[assistant] UNPIVOT lineage is now correct for multi-column unpivots, where the value columns were previously over-attributed to every IN-list column. Aliased and pass-through shapes already worked, and I added regression tests for both. The full suite passes (1119 tests).

**What changed**
- `sqlglot/lineage.py`, `_pivot_column_mapping`: each value column now maps to the IN-list element in the same position. Before, `UNPIVOT((amount, quantity) FOR m IN ((jan_amt, jan_qty), (feb_amt, feb_qty)))` gave `amount` the lineage `jan_amt, jan_qty, feb_amt, feb_qty`. It now gives `jan_amt, feb_amt`, and `quantity`
…[501 chars elided]…
e has them.

**Checked and already correct** (no change needed): aliased outer and inner UNPIVOT, pass-through through a CTE or derived table, pass-through in a join, `INCLUDE NULLS`, and value columns used in aggregates or WHERE.

**Not fixed:** chained UNPIVOTs (`... UNPIVOT (a ...) UNPIVOT (b ...)`) still fall back to the raw source table, so `score2` reports `SALES.SCORE2` instead of the real inputs. The code only handles a single PIVOT/UNPIVOT per scope, and handling chains would need recursion through the pivot chain. I left it out to keep this change small. Say if you want it done next.
