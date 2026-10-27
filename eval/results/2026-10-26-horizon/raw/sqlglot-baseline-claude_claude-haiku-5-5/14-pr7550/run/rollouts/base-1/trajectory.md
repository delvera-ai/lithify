# trajectory base-1

final message:
`qualify` now leaves UNPIVOT's new output names unqualified, so the example query comes out valid in BigQuery, DuckDB and Snowflake. The full suite passes (1092 tests), and ruff format and check are clean. I haven't committed.

**What was wrong:** the CTE's columns were already visible. The problem was that the UNPIVOT's new names (`v` and `m`) were treated as columns of `c`. `Resolver` lists them as columns of the pivoted source, so `_qualify_columns` set their table to `c`, giving `UNPIVOT(c.v FOR c.m IN (c.jan, c.feb))`, which is invalid.

**The fix** (`sqlglot/optimizer/qualify_columns.py`):
- New helper `_is_unpivot_output_column`, which is true for the value columns before `FOR` and the `FOR` name column.
- Both qualification loops in `_qualify_columns` skip those columns. The `IN (...)` items still get qualified as source columns.

**Test:** a new case in `tests/fixtures/optimizer/qualify_columns.sql` with `# execute: false`, matching the existing UNPIVOT fixtures.

**Found but not fixed:** the full `optimize()` pipeline drops the CTE entirely and leaves `FROM c` pointing at a table that no longer exists. This happens on the unmodified base commit too. For pivoted sources, `scope.py` (around line 813) registers the pivoted CTE reference as a plain `Table` rather than the CTE scope, so `ref_count` never counts it and `eliminate_ctes` removes the CTE. I left it alone because fixing it changes source resolution for every pivot, and it's outside `qualify`. It deserves its own issue, and I can take it if you want.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"unpivot\\|pivot\" sqlglot/optimizer/qualify_columns.py | head -60", "description": "Check status and find pivot handling in qualify_columns"}
[tool_result] 54:        - Currently only handles a single PIVOT or UNPIVOT operator
124:            if scope.external_columns and not scope.is_correlated_subquery and not scope.pivots:
141:            if unqualified_columns and scope.pivots and scope.pivots[0].unpivot:
142:                # New columns produced by the UNPIVOT can't be qualified, but there may be columns
143:                # under the UNPIVOT's IN clause that can and should be qualified. We recompute
145:                unpivot_columns = set
…[1530 chars elided]…
            if pivot:
870:                if pivot_output_columns and pivot_exclude_columns:
871:                    pivot_columns = [c for c in columns if c not in pivot_exclude_columns]
872:                    pivot_columns.extend(pivot_output_columns)
874:                    pivot_columns = pivot.alias_column_names
876:                if pivot_columns:
878:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
879:                        for name in pivot_columns
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor d in ['bigquery','duckdb','snowflake','spark']:\n    try:\n        e = qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read=d), dialect=d)\n        print(d, e.sql(d))\n    except Exception as ex: print(d, 'ERR', repr(ex))\n\"", "description": "Reproduce the bug across dialects"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
spark WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM (SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `m` IN (`jan`, `feb`))) AS `c`
[tool_use Bash] {"command": "sed -n 115,205p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 610,660p sqlglot/optimizer/qualify_columns.py", "description": "Read unpivot handling in qualify_columns"}
[tool_result] def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
    """Raise an `OptimizeError` if any columns aren't qualified"""
    all_unqualified_columns = []
    for scope in traverse_scope(expression):
        if isinstance(scope.expression, exp.Select):
            unqualified_columns = scope.unqualified_columns

            if scope.external_columns and not scope.is_correlated_subquery and not scope.pivots:
                column = scope.external_columns[0]
                for
…[4666 chars elided]…
:
            if not column.table and column.name in resolver.all_columns:
                table = resolver.get_table(column.name)
                if table:
                    column.set("table", table)


def _expand_struct_stars_no_parens(
    expression: exp.Dot,
) -> list[exp.Alias]:
    """[BigQuery] Expand/Flatten foo.bar.* where bar is a struct column"""

    dot_column = expression.find(exp.Column)
    if not isinstance(dot_column, exp.Column) or not dot_column.is_type(exp.DType.STRUCT):
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\nprint(repr(e.args['from'].this.args.get('pivots')))\n\" ; grep -n \"def _qualify_columns\\|def qualify_columns\\|scope.columns\\|all_columns\" sqlglot/optimizer/qualify_columns.py | head -40", "description": "Inspect parsed UNPIVOT tree and qualify_columns hooks"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'from'
21:def qualify_columns(
176:    for column in scope.columns:
294:        for column in scope.columns:
557:    for column in itertools.chain(scope.columns, scope.stars):
595:        # a `for column in scope.columns` iteration, even though they shouldn't be
599:def _qualify_columns(
605:    for column in scope.columns:
648:            if not column.table and column.name in resolver.all_columns:
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\nprint(repr(e.find(sqlglot.exp.Pivot)))\n\" ; sed -n 21,30p sqlglot/optimizer/qualify_columns.py; sed -n 280,300p sqlglot/optimizer/qualify_columns.py; sed -n 550,600p sqlglot/optimizer/qualify_columns.py", "description": "Show parsed Pivot node and relevant qualify code"}
[tool_result] Pivot(
  expressions=[
    Column(
      this=Identifier(this=v, quoted=False))],
  fields=[
    In(
      this=Column(
        this=Identifier(this=m, quoted=False)),
      expressions=[
        Column(
          this=Identifier(this=jan, quoted=False)),
        Column(
          this=Identifier(this=feb, quoted=False))])],
  unpivot=True,
  default_on_null=False)
def qualify_columns(
    expression: exp.Expr,
    schema: dict[str, object] | Schema,
    expand_alias_refs: bool = True,
    expan
…[2520 chars elided]…
:
                    # Remove the actual column parts from the rest of dot parts
                    new_column.meta["dot_parts"] = dot_parts[2 if was_qualified else 1 :]

                column.replace(exp.Dot.build([new_column, *parts]))

    if converted:
        # We want to re-aggregate the converted columns, otherwise they'd be skipped in
        # a `for column in scope.columns` iteration, even though they shouldn't be
        scope.clear_cache()


def _qualify_columns(
    scope: Scope,
[tool_use Bash] {"command": "grep -n -i \"pivot\" sqlglot/optimizer/*.py | grep -v \"^sqlglot/optimizer/qualify_columns.py:\\(1[0-9][0-9]\\|7[89][0-9]\\|8[0-9][0-9]\\)\" | head -50; sed -n 599,610p sqlglot/optimizer/qualify_columns.py", "description": "Find all pivot references in optimizer"}
[tool_result] sqlglot/optimizer/eliminate_subqueries.py:125:    # - drop the "pivot" arg from a pivoted subquery
sqlglot/optimizer/eliminate_subqueries.py:128:    if not parent_scope or parent_scope.pivots or isinstance(parent_scope.expression, exp.Lateral):
sqlglot/optimizer/pushdown_projections.py:117:                    if scope.pivots or isinstance(select, exp.QueryTransform):
sqlglot/optimizer/resolver.py:239:        if not joins or args.get("laterals") or args.get("pivots"):
sqlglot/optimizer/resolver.p
…[2814 chars elided]…
timizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
def _qualify_columns(
    scope: Scope,
    resolver: Resolver,
    allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring each column specifies a source"""
    for column in scope.columns:
        column_table = column.table
        column_name = column.name

        if column_table and column_table in scope.sources:
            source_columns = resolver.get_source_columns(column_table)
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.normalize_identifiers import normalize_identifiers\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\ne = qualify_tables(e, dialect='duckdb')\nprint(e.sql('duckdb'))\ns = build_scope(e)\nfor sc in s.traverse():\n    print(sc.expression.sql()[:60], [c.sql() for c in sc.columns], [p.alias for p in sc.pivots])\n\"", "description": "Trace qualify_tables and scope columns for the query"}
[tool_result] WITH c AS (SELECT id, jan, feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS c
SELECT id, jan, feb FROM t AS t ['id', 'jan', 'feb'] []
WITH c AS (SELECT id, jan, feb FROM t AS t) SELECT * FROM c  ['v', 'm', 'jan', 'feb'] ['c']
[tool_use Bash] {"command": "sed -n 60,112p sqlglot/optimizer/qualify_columns.py; sed -n 170,190p sqlglot/optimizer/qualify_columns.py", "description": "Read qualify_columns main flow"}
[tool_result]     pseudocolumns = dialect.PSEUDOCOLUMNS

    for scope in traverse_scope(expression):
        if dialect.PREFER_CTE_ALIAS_COLUMN:
            pushdown_cte_alias_columns(scope)

        scope_expression = scope.expression
        is_select = isinstance(scope_expression, exp.Select)

        _separate_pseudocolumns(scope, pseudocolumns)

        resolver = Resolver(scope, schema, infer_schema=infer_schema)
        _pop_table_column_aliases(scope.ctes)
        _pop_table_column_aliases(scope.deri
…[1357 chars elided]…
     return

    has_pseudocolumns = False
    scope_expression = scope.expression

    for column in scope.columns:
        name = column.name.upper()
        if name not in pseudocolumns:
            continue

        if name != "LEVEL" or (
            isinstance(scope_expression, exp.Select) and scope_expression.args.get("connect")
        ):
            column.replace(exp.Pseudocolumn(**column.args))
            has_pseudocolumns = True

    if has_pseudocolumns:
        scope.clear_cache()
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify_columns import _qualify_columns\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot import exp\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan
…[37 chars elided]…
(v FOR m IN (jan, feb))', read='duckdb')\ne = qualify_tables(e, dialect='duckdb')\ns = build_scope(e)\nsc = [x for x in s.traverse() if isinstance(x.expression, exp.Select)][-1]\nr = Resolver(sc, {}, infer_schema=True)\nfor c in sc.columns: print(c.sql(), '->', r.get_table(c), c.table)\nprint(sc.pivots[0].alias, sc.pivots[0].sql())\n\"", "description": "Inspect resolver results for pivot columns"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 13, in <module>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", line 27, in __init__
    self.dialect = schema.dialect or Dialect()
                   ^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'dialect'
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.schema import ensure_schema\nfrom sqlglot import exp\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\ne = qualify_tables(e, dialect='duckdb')\ns = build_scope(e)\nsc = [x for x in s.traverse() if isinstance(x.expression, exp.Select)][-1]\nr = Resolver(sc, ensure_schema({}, dialect='duckdb'), infer_schema=True)\nfor c in sc.columns: print(c.sql(), '->', r.get_table(c), c.table)\nprint(sc.pivots[0].alias)\n\"", "description": "Inspect resolver results for pivot columns"}
[tool_result] v -> c 
m -> c 
jan -> c 
feb -> c 
c
[assistant] The root cause is visible now: `Resolver` treats the unpivot output names (`v`, `m`) as columns of the pivoted CTE source, so `_qualify_columns` assigns them the `c` table. I'll exclude the UNPIVOT's new output names from both qualification loops.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if not column_table:\n            if scope.pivots and not column.find_ancestor(exp.Pivot):", "new_string": "        if not column_table:\n            if _is_unpivot_output_column(column):\n                continue\n\n            if scope.pivots and not column.find_ancestor(exp.Pivot):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "python - <<'EOF'\nimport re\np='sqlglot/optimizer/qualify_columns.py'\ns=open(p).read()\nold=\"\"\"    for pivot in scope.pivots:\n        for column in pivot.find_all(exp.Column):\n            if not column.table and column.name in resolver.all_columns:\"\"\"\nnew=\"\"\"    for pivot in scope.pivots:\n        for column in pivot.find_all(exp.Column):\n            if not column.table 
…[519 chars elided]…
on -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor d in ['bigquery','duckdb','snowflake','spark','']:\n    e = qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read=d or None), dialect=d)\n    print(d or 'sqlglot', e.sql(d or None))\n\"", "description": "Add unpivot output helper and apply it; rerun repro"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
spark WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM (SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))) AS `c`
sqlglot WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("c"."jan", "c"."feb")) AS "c"
[assistant] The repro now gives correct output for BigQuery, DuckDB and Snowflake. Next I'll add a regression fixture and run the test suite.
[tool_use Bash] {"command": "git diff --stat && grep -n -i \"unpivot\" tests/fixtures/optimizer/qualify_columns.sql | head; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Check diff, existing unpivot fixtures, and project python"}
[tool_result]  sqlglot/optimizer/qualify_columns.py | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql tests/test_optimizer.py | head -20; git diff", "description": "Find existing unpivot tests and show current diff"}
[tool_result] tests/fixtures/optimizer/optimizer.sql:696:# title: unpivoted table source with a single value column, unpivot columns can't be qualified
tests/fixtures/optimizer/optimizer.sql:699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
tests/fixtures/optimizer/optimizer.sql:706:UNPIVOT("SALES" FOR "MONTH" IN ("JAN", "FEB")) AS "M_SALES"
tests/fixtures/optimizer/optimizer.sql:710:# title: unpivoted table source, unpivot has column aliases
te
…[2649 chars elided]…
 of the pivoted source instead of the pivot's alias
@@ -645,7 +653,7 @@ def _qualify_columns(
 
     for pivot in scope.pivots:
         for column in pivot.find_all(exp.Column):
-            if not column.table and column.name in resolver.all_columns:
+            if not column.table and column.name in resolver.all_columns and not _is_unpivot_output_column(column):
                 table = resolver.get_table(column.name)
                 if table:
                     column.set("table", table)
[assistant] The diff is as intended. The new loop condition is over the line-length limit, so I'll wrap it, then add a fixture next to the existing UNPIVOT cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            if not column.table and column.name in resolver.all_columns and not _is_unpivot_output_column(column):", "new_string": "            if (\n                not column.table\n                and column.name in resolver.all_columns\n                and not _is_unpivot_output_column(column)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "offset": 748, "limit": 16}
[tool_result] 748	
749	# title: unpivoted table source with a single value column, unpivot columns can be qualified
750	# execute: false
751	# dialect: bigquery
752	# note: the named columns aren not supported by BQ but we add them here to avoid defining a schema
753	SELECT * FROM produce AS produce(product, q1, q2, q3, q4) UNPIVOT(sales FOR quarter IN (q1, q2, q3, q4));
754	SELECT
755	  `produce`.`product` AS `product`,
756	  `produce`.`quarter` AS `quarter`,
757	  `produce`.`sales` AS `sales`
758	FROM `produce` AS `produce`
759	UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`, `produce`.`q3`, `produce`.`q4`)) AS `produce`;
760	
761	# title: unpivoted table source with multiple value columns
762	# execute: false
763	# dialect: bigquery
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "old_string": "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`, `produce`.`q3`, `produce`.`q4`)) AS `produce`;\n\n", "new_string": "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`
…[104 chars elided]…
are not qualified\n# execute: false\n# dialect: bigquery\nWITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));\nWITH `c` AS (\n  SELECT\n    `t`.`id` AS `id`,\n    `t`.`jan` AS `jan`,\n    `t`.`feb` AS `feb`\n  FROM `t` AS `t`\n)\nSELECT\n  `c`.`id` AS `id`,\n  `v` AS `v`,\n  `m` AS `m`\nFROM `c` AS `c`\nUNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`;\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql has been updated successfully.
[assistant] I wrote that expected output by hand, so I'll check it against the real output before trusting it.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -60", "description": "Run optimizer tests"}
[tool_result]                 dialect = meta.get("dialect")
                leave_tables_isolated = meta.get("leave_tables_isolated")
                validate_qualify_columns = meta.get("validate_qualify_columns")
                canonicalize_table_aliases = meta.get("canonicalize_table_aliases")
    
                func_kwargs = kwargs.copy()
    
                if leave_tables_isolated is not None:
                    func_kwargs["leave_tables_isolated"] = string_to_bool(leave_tables_isolated)
    
      
…[1660 chars elided]…
      -   `c`.`id` AS `id`,
E               -   `v` AS `v`,
E               -   `m` AS `m`
E                 FROM `c` AS `c`
E                 UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[unpivoted CTE source, unpivot output names are not qualified] tests/test_optimizer.py::TestOptimizer::test_optimize
1 failed, 77 passed, 3705 subtests passed in 19.98s
[assistant] The fixture runs the full optimizer pipeline, not just `qualify`, so my hand-written expectation was wrong. I'll print the actual output and verify it is semantically correct before updating the fixture.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nprint(optimize(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery'), dialect='bigquery').sql('bigquery', pretty=True))\n\"; git stash list | head -0; git diff --stat", "description": "Show full optimizer output for the new case"}
[tool_result] SELECT
  *
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
head: illegal line count -- 0
 sqlglot/optimizer/qualify_columns.py   | 14 +++++++++++++-
 tests/fixtures/optimizer/optimizer.sql | 18 ++++++++++++++++++
 2 files changed, 31 insertions(+), 1 deletion(-)
[assistant] The full optimizer drops the CTE and leaves `FROM c` pointing at a table that no longer exists, which is a separate problem from the qualify bug. I'll check whether this also happens on the unmodified base commit.
[tool_use Bash] {"command": "D=$(mktemp -d /tmp/sqlglot-base.XXXX) && git archive HEAD sqlglot | tar -x -C \"$D\" && P=<work>/env-sqlglot/bin/python; cd \"$D\" && $P -c \"\nimport sqlglot; print(sqlglot.__file__)\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qu
…[53 chars elided]…
ELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery'), dialect='bigquery').sql('bigquery', pretty=True))\nprint(qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery'), dialect='bigquery').sql('bigquery'))\n\"", "description": "Compare optimizer output against unmodified base commit"}
[tool_result] /private/tmp/sqlglot-base.eSw7/sqlglot/__init__.py
SELECT
  *
FROM `c` AS `c`
UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
Shell cwd was reset to ~/.cache/lithify/work/repo-b63a38b63828/20261026-140614-optimizer-select-from-cte-unpivo/base-1
[assistant] The unmodified base has the same drop, so it's pre-existing. Before deciding whether it's in scope, I'll find which optimizer rule removes the CTE.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.qualify import qualify\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery')\nfor rule in RULES:\n    try:\n        e = rule(e.copy(), dialect='bigquery') if rule.__name__ not in ('qualify',) else e\n    except TypeError:\n        e = rule(e.copy())\n    print(rule.__name__, '|', e.sql('bigquery').replace(chr(10),' '))\n\" 2>&1 | head -40", "description": "Step through optimizer rules to locate CTE removal"}
[tool_result] qualify | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
pushdown_projections | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
normalize | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
unnest_subqueries | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
pushdown_predicates | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR 
…[527 chars elided]…
N (jan, feb))
quote_identifiers | WITH `c` AS (SELECT `id`, `jan`, `feb` FROM `t`) SELECT * FROM `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))
annotate_types | WITH `c` AS (SELECT `id`, `jan`, `feb` FROM `t`) SELECT * FROM `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))
canonicalize | WITH `c` AS (SELECT `id`, `jan`, `feb` FROM `t`) SELECT * FROM `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))
simplify | WITH `c` AS (SELECT `id`, `jan`, `feb` FROM `t`) SELECT * FROM `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer import optimize\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nfor k in range(1, len(RULES)+1):\n    out = optimize(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery', rules=RULES[:k])\n    print(RULES[k-1].__name__, '|', out.sql('bigquery').replace(chr(10),' '))\n\" 2>&1 | head -40", "description": "Run optimizer with growing rule prefixes"}
[tool_result] qualify | WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
pushdown_projections | WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
normalize | WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
unnest_subqueries | WITH c AS (SELECT t.id AS id, t.jan AS jan
…[799 chars elided]…
S c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
eliminate_ctes | SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
quote_identifiers | SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
annotate_types | SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
canonicalize | SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
simplify | SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[assistant] The CTE is removed by `eliminate_ctes`, which doesn't count the pivoted `c` reference as a use. Let me look at that rule.
[tool_use Bash] {"command": "cat sqlglot/optimizer/eliminate_ctes.py | head -60", "description": "Read eliminate_ctes rule"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot.optimizer.scope import Scope, build_scope


if t.TYPE_CHECKING:
    from sqlglot._typing import E


def eliminate_ctes(expression: E) -> E:
    """
    Remove unused CTEs from an expression.

    Example:
        >>> import sqlglot
        >>> sql = "WITH y AS (SELECT a FROM x) SELECT a FROM z"
        >>> expression = sqlglot.parse_one(sql)
        >>> eliminate_ctes(expression).sql()
        'SELECT a FROM z'

    Args:
     
…[625 chars elided]…
               cte_node.pop()

                    # Pop the entire WITH clause if this is the last CTE
                    if with_node and len(with_node.expressions) <= 0:
                        with_node.pop()

                    # Decrement the ref count for all sources this CTE selects from
                    for _, source in scope.selected_sources.values():
                        if isinstance(source, Scope):
                            ref_count[id(source)] -= 1

    return expression
[tool_use Bash] {"command": "sed -n 800,830p sqlglot/optimizer/scope.py; grep -n \"def ref_count\" -A 25 sqlglot/optimizer/scope.py | head -40", "description": "Read scope source resolution for pivoted tables"}
[tool_result]         expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (
…[1348 chars elided]…
 in scope._semi_anti_join_tables:
592-                # semi/anti join sources are not actually selected but we still need to
593-                # increment their ref count to avoid them being optimized away
594-                if name in scope.sources:
595-                    scope_ref_count[id(scope.sources[name])] += 1
596-
597-        return scope_ref_count
598-
599-
600-def traverse_scope(expression: exp.Expr) -> list[Scope]:
601-    """
602-    Traverse an expression by its "scopes".
603-
[assistant] This is a separate bug: the pivoted-CTE reference is registered as a plain `Table` source, so `ref_count` never counts the CTE and `eliminate_ctes` drops it. That's outside `qualify`, and fixing it means changing source resolution for pivots, so I'll report it rather than widen this change. The fixture belongs in the `qualify_columns` fixtures, which run only the qualify step, so I'll move it there.
[tool_use Bash] {"command": "git checkout -- tests/fixtures/optimizer/optimizer.sql && grep -n -i \"pivot\" tests/fixtures/optimizer/qualify_columns.sql | head; tail -5 tests/fixtures/optimizer/qualify_columns.sql; grep -n \"qualify_columns.sql\" -A 12 tests/test_optimizer.py | head -30", "description": "Revert optimizer fixture; locate qualify_columns fixtures"}
[tool_result] 269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 ORDER BY _0.EMPID;
593:# title: Expand PIVOT column combinations
595:WITH cities AS (SELECT * FROM (VALUES ('nl', 'amsterdam', 2000, 1005)) AS t(country, name, year, population)) SELECT * FROM cities PIVOT(SUM(population) AS total, COUNT(populat
…[1184 chars elided]…
ion) AS total, COUNT(population) AS count FOR country IN ('nl', 'us') year IN (2000, 2010) name IN ('amsterdam', 'seattle')) AS _0;
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x SEMI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;

# title: ANTI + normal joins reinclude the table on scope
SELECT * FROM x ANTI JOIN y USING (b) JOIN y USING (b);
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;
[tool_use Bash] {"command": "grep -n \"# dialect\" tests/fixtures/optimizer/qualify_columns.sql | head -3; grep -n \"^# \" tests/fixtures/optimizer/qualify_columns.sql | tail -3; printf '%s\\n' '' '# title: unpivot output names of a CTE source are not qualified' '# dialect: bigquery' 'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));' 'WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`;' >> tests/fixtures/optimizer/qualify_columns.sql && tail -6 tests/fixtures/optimizer/qualify_columns.sql | cut -c1-120", "description": "Append unpivot CTE regression fixture to qualify_columns fixtures"}
[tool_result] 106:# dialect: oracle
111:# dialect: oracle
134:# dialect: bigquery
1043:# title: ANTI JOIN table is excluded from the scope
1047:# title: SEMI + normal joins reinclude the table on scope
1051:# title: ANTI + normal joins reinclude the table on scope
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = 

# title: unpivot output names of a CTE source are not qualified
# dialect: bigquery
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` U
[assistant] Now I'll run the full project test suite with the project's pytest command.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite with project interpreter"}
[tool_result]                 optimized = future.result()
                actual = optimized.sql(pretty=pretty, dialect=dialect)
>               self.assertEqual(
                    expected,
                    actual,
                )
E               AssertionError: 'WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan[122 chars] `c`' != 'WITH c AS (SELECT t.id AS id, t.jan AS jan, t.[80 chars]AS c'
E               - WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) S
…[225 chars elided]…
-     - -     - - -   -  - - -   -      - -
E               + WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[unpivot output names of a CTE source are not qualified] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
1 failed, 1092 passed, 17865 subtests passed in 56.42s
[assistant] The qualify fixture runner renders in the default dialect, so my expected string used the wrong dialect. I'll rewrite the fixture with no dialect line and the default-dialect output, which I already confirmed is correct.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/fixtures/optimizer/qualify_columns.sql'\ns=open(p).read()\ni=s.index('# title: unpivot output names of a CTE source')\ns=s[:i]+'''# title: unpivot output names of a CTE source are not qualified\nWITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));\nWITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT
…[174 chars elided]…
s-donovan-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $P -m ruff format --check sqlglot/optimizer/qualify_columns.py 2>&1 | tail -2; $P -m ruff check sqlglot/optimizer/qualify_columns.py 2>&1 | tail -2", "description": "Fix fixture expectation, rerun suite and lint"}
[tool_result] # title: unpivot output names of a CTE source are not qualified
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c;
=========================== short test summary info ============================
SUBFAILED[(execute) unpivot output names of a CTE source are not qualified] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
1 failed, 1092 passed, 17865 subtests passed in 57.74s
1 file already formatted
All checks passed!
[assistant] The fixture is also being executed against a database, and the query has no real table `t`. Existing UNPIVOT fixtures use `# execute: false`, so I'll do the same.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/fixtures/optimizer/qualify_columns.sql'\ns=open(p).read()\ns=s.replace('# title: unpivot output names of a CTE source are not qualified\\n','# title: unpivot output names of a CTE source are not qualified\\n# execute: false\\n')\nopen(p,'w').write(s)\nEOF\nP=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short; rm -rf /tmp/sqlglot-base.*", "description": "Mark fixture non-executing, rerun full suite, clean temp copy"}
[tool_result] ............................ [ 83%]
.........................................................................................................................................................................................                                                   [100%]
1092 passed, 17866 subtests passed in 53.33s
 M sqlglot/optimizer/qualify_columns.py
 M tests/fixtures/optimizer/qualify_columns.sql
[assistant] `qualify` now leaves UNPIVOT's new output names unqualified, so the example query comes out valid in BigQuery, DuckDB and Snowflake. The full suite passes (1092 tests), and ruff format and check are clean. I haven't committed.

**What was wrong:** the CTE's columns were already visible. The problem was that the UNPIVOT's new names (`v` and `m`) were treated as columns of `c`. `Resolver` lists them as columns of the pivoted source, so `_qualify_columns` set their table to `c`, giving `UNPIVOT(c.v FOR c.m IN (c.jan, c.feb))`, which is invalid.

**The fix** (`sqlglot/optimizer/qualify_columns.py`
…[341 chars elided]…
lse`, matching the existing UNPIVOT fixtures.

**Found but not fixed:** the full `optimize()` pipeline drops the CTE entirely and leaves `FROM c` pointing at a table that no longer exists. This happens on the unmodified base commit too. For pivoted sources, `scope.py` (around line 813) registers the pivoted CTE reference as a plain `Table` rather than the CTE scope, so `ref_count` never counts it and `eliminate_ctes` removes the CTE. I left it alone because fixing it changes source resolution for every pivot, and it's outside `qualify`. It deserves its own issue, and I can take it if you want.
