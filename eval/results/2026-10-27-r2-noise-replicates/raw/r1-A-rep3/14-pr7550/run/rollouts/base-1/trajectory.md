# trajectory base-1

final message:
`qualify` now resolves `SELECT * FROM cte UNPIVOT(...)` correctly, and the full optimizer keeps the CTE. The project suite passes (1092 tests, 17867 subtests), and ruff and mypy are clean on the changed modules. Nothing is committed.

**Root cause:** the unpivoted CTE was registered as a plain table in the scope. Its columns were looked up in the schema, so `id`, `jan`, `feb` were unknown. The IN-list `jan` stayed unqualified and validation raised `Ambiguous column 'jan'`. The handling of the new output names (`v`, `m`) was already correct.

**Changes:**
- `sqlglot/optimizer/resolver.py`: a pivoted source whose name matches a CTE now takes its columns from that CTE. Those columns feed star expansion and column resolution.
- `sqlglot/optimizer/scope.py`: a second bug surfaced in full `optimize`. For `c UNPIVOT(...)` the pivot alias defaults to `c`, which overwrote the CTE's `c` entry. `eliminate_ctes` then saw the CTE as unused and dropped it, leaving `FROM c` dangling. `ref_count` now counts a pivoted CTE selection against the CTE.
- Fixtures: a BigQuery `qualify_columns` case in `tests/fixtures/optimizer/qualify_columns.sql` and a full-optimizer case in `tests/fixtures/optimizer/optimizer.sql`. Both use `# execute: false`, as the existing UNPIVOT fixtures do.

**Result for your example**, `WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))`, now qualifies in BigQuery, DuckDB and Snowflake. The full optimizer output keeps the `WITH`.

**Choices to check:**
- I fixed the dropped CTE as part of this, since without it `optimize` produces broken SQL for the same input. It is a separate change to the reference counting, so say if you'd rather it land separately.
- In DuckDB the IN-list columns stay unqualified (`IN (jan, feb)`), while BigQuery qualifies them (`IN (c.jan, c.feb)`). Derived-table UNPIVOTs already behave this way, so I left it. Both forms are valid.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n -i \"unpivot\" sqlglot/optimizer/*.py sqlglot/optimizer/*/*.py 2>/dev/null | head -50; grep -n \"class Pivot\" -A 30 sqlglot/expressions.py | head -60", "description": "Check repo state and find UNPIVOT handling in optimizer"}
[tool_result] 70fc81f77 lithify: probe base
(eval):1: no matches found: sqlglot/optimizer/*/*.py
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "pwd && ls -la && git rev-parse --show-toplevel && git worktree list", "description": "Inspect working directory layout and git worktree"}
[tool_result] ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
total 3808
drwxr-xr-x@ 30 user  staff      960 Oct 28 11:44 .
drwxr-xr-x@  4 user  staff      128 Oct 28 11:44 ..
drwxr-xr-x@  3 user  staff       96 Oct 28 11:44 .agents
drwxr-xr-x@  3 user  staff       96 Oct 28 11:44 .claude
-rw-r--r--@  1 user  staff      121 Oct 28 11:44 .git
drwxr-xr-x@  5 user  staff      160 Oct 28 11:44 .github
-rw-r--r--@  1 user  staff     
…[1369 chars elided]…
sqlglot.png
drwxr-xr-x@  5 user  staff      160 Oct 28 11:44 sqlglotc
drwxr-xr-x@ 30 user  staff      960 Oct 28 11:44 tests
~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
<run>/repo                   573b1aee1 [eval]
~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1 70fc81f77 (detached HEAD)
[tool_use Bash] {"command": "ls sqlglot sqlglot/optimizer && grep -rn -i \"unpivot\" sqlglot/optimizer/ | head -40; grep -rn \"class Pivot\" -A 25 sqlglot/expressions* | head -50", "description": "Search optimizer for UNPIVOT handling and Pivot class"}
[tool_result] sqlglot:
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing

sqlglot/optimizer:
__init__.py
annotate_types.py
canonicalize.py
eliminate_ctes.py
eliminate_joins.py
eliminate_subqueries.py
isolate_table_selects.py
merge_subqueries.py
normalize.py
normalize_identifiers.
…[3882 chars elided]…
ndition):
sqlglot/expressions/core.py-1897-    # https://cloud.google.com/bigquery/docs/reference/standard-sql/operators#array_subscript_operator
sqlglot/expressions/core.py-1898-    arg_types = {
sqlglot/expressions/core.py-1899-        "this": True,
sqlglot/expressions/core.py-1900-        "expressions": True,
sqlglot/expressions/core.py-1901-        "offset": False,
sqlglot/expressions/core.py-1902-        "safe": False,
sqlglot/expressions/core.py-1903-        "returns_list_for_maps": False,
[tool_use Bash] {"command": "sed -n 100,210p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 770,830p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 150,190p sqlglot/optimizer/qualify_tables.py", "description": "Read UNPIVOT handling in qualify_columns and qualify_tables"}
[tool_result]                     pseudocolumns,
                    annotator,
                )
            qualify_outputs(scope)

        _expand_group_by(scope, dialect)

        # DISTINCT ON and ORDER BY follow the same rules (tested in DuckDB, Postgres, ClickHouse)
        # https://www.postgresql.org/docs/current/sql-select.html#SQL-DISTINCT
        _expand_order_by_and_distinct_on(scope, resolver)

        if dialect.ANNOTATE_ALL_SCOPES:
            annotator.annotate_scope(scope)

    return expres
…[7589 chars elided]…
   if on_qualify:
                        on_qualify(source)
            elif isinstance(source, Scope) and source.is_udtf:
                _set_alias(udtf := source.expression, canonical_aliases)

                table_alias = udtf.args["alias"]

                if isinstance(udtf, exp.Values) and not table_alias.columns:
                    column_aliases = [
                        normalize_identifiers(i, dialect=dialect)
                        for i in dialect.generate_values_aliases(udtf)
[tool_use Bash] {"command": "mkdir -p /tmp/unpivot-repro && cat > /tmp/unpivot-repro/repro.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"bigquery\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"),\n    (\"duckdb\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, f
…[576 chars elided]…
lect))\n    except Exception as ex:\n        print(dialect, \"ERR \", type(ex).__name__, ex)\nEOF\ncd /tmp/unpivot-repro && PYTHONPATH=~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1 <work>/env-sqlglot/bin/python -I repro.py", "description": "Reproduce UNPIVOT qualify failures across dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/private/tmp/unpivot-repro/repro.py", line 2, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && sed -i '1i import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")' repro.py && <work>/env-sqlglot/bin/python -I repro.py", "description": "Rerun UNPIVOT repro with repo on sys.path"}
[tool_result ERROR] Exit code 1
sed: -I or -i may not be used with stdin
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > repro.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"bigquery\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, fe
…[570 chars elided]…
{\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\"}}, validate_qualify_columns=True, identify=False)\n        print(dialect, \"OK  \", e.sql(dialect=dialect))\n    except Exception as ex:\n        print(dialect, \"ERR \", type(ex).__name__, ex)\nEOF\n<work>/env-sqlglot/bin/python -I repro.py", "description": "Rerun UNPIVOT repro with repo on sys.path"}
[tool_result] bigquery ERR  OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
duckdb ERR  OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
snowflake ERR  OptimizeError Ambiguous column 'JAN' (Line: 1, Col: 78)
duckdb OK   SELECT _1.id AS id, _1.m AS m, _1.v AS v FROM (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) AS _0 UNPIVOT(v FOR m IN (jan, feb)) AS _1
duckdb ERR  OptimizeError Ambiguous column 'jan' (Line: 1, Col: 85)
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "grep -n -i \"pivot\" sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/qualify_tables.py | head -80", "description": "Find all pivot references in optimizer modules"}
[tool_result] sqlglot/optimizer/resolver.py:239:        if not joins or args.get("laterals") or args.get("pivots"):
sqlglot/optimizer/resolver.py:241:            # (e.g laterals, pivots) exist alongside joins
sqlglot/optimizer/scope.py:81:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:130:        self._pivots = None
sqlglot/optimizer/scope.py:411:                            expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:477:    def pivots(self) 
…[5059 chars elided]…
:= seq_get(source.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py:169:                if pivot:
sqlglot/optimizer/qualify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
sqlglot/optimizer/qualify_tables.py:171:                    _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)
sqlglot/optimizer/qualify_tables.py:173:                    # This case corresponds to a pivoted CTE, we don't want to qualify that
[tool_use Bash] {"command": "sed -n 600,670p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 800,830p sqlglot/optimizer/scope.py && echo ---- && sed -n 120,150p sqlglot/optimizer/qualify_tables.py && echo ---- && sed -n 225,250p sqlglot/optimizer/resolver.py", "description": "Read column qualification and scope pivot code"}
[tool_result]     scope: Scope,
    resolver: Resolver,
    allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring each column specifies a source"""
    for column in scope.columns:
        column_table = column.table
        column_name = column.name

        if column_table and column_table in scope.sources:
            source_columns = resolver.get_source_columns(column_table)
            if (
                not allow_partial_qualification
                and source_columns
  
…[5740 chars elided]…
 or args.get("pivots"):
            # Feature gap: We currently don't try to disambiguate columns if other sources
            # (e.g laterals, pivots) exist alongside joins
            return None

        join_ancestor = column.find_ancestor(exp.Join, exp.Select)

        if (
            isinstance(join_ancestor, exp.Join)
            and join_ancestor.alias_or_name in self.scope.selected_sources
        ):
            # Ensure that the found ancestor is a join that contains an actual source,
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > tree.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one, exp\nfor d in [\"duckdb\", \"bigquery\", \"snowflake\"]:\n    e = parse_one(\"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\", read=d)\n    p = e.find(exp.Pivot)\n    print(d, repr(p))\n    print(\"  expressions:\", p.expressions, \"fields:\", p.fields)\nEOF\n<work>/env-sqlglot/bin/python -I tree.py", "description": "Dump UNPIVOT parse tree structure"}
[tool_result] duckdb Pivot(
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
  expressions: [Column(
  this=Identifier(this=v, quoted=False))] fields: [In(
  this=Column(
    this=Identifier(this=m, quo
…[1089 chars elided]…
       this=Identifier(this=feb, quoted=False))])],
  unpivot=True,
  default_on_null=False)
  expressions: [Column(
  this=Identifier(this=v, quoted=False))] fields: [In(
  this=Column(
    this=Identifier(this=m, quoted=False)),
  expressions=[
    Column(
      this=Identifier(this=jan, quoted=False)),
    Column(
      this=Identifier(this=feb, quoted=False))])]
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "grep -n \"def get_source_columns\" -A 40 sqlglot/optimizer/resolver.py && grep -n \"def all_columns\" -A 12 sqlglot/optimizer/resolver.py && grep -n \"def columns\" -A 30 sqlglot/optimizer/scope.py | head -50", "description": "Read resolver source column lookup and scope columns"}
[tool_result] 95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
96-        if isinstance(expression, exp.Select):
97-            return expression.named_selects
98-        if isinstance(expression, exp.Subquery) and isinstance(expression.this, exp.SetOperation):
99-            # Different types of SET modifiers can be chained together if they're explicitly grouped by nesting
100-            return self.get_source_columns_from_set_op(expression.this)
101-        if not isinsta
…[5455 chars elided]…
),
326-                )
327-                for column in scope.external_columns
328-            ]
329-
330-            expr = self.expression
331-            named_selects = set(expr.named_selects) if isinstance(expr, exp.Query) else set()
332-
333-            self._columns = []
334-            for column in columns + external_columns:
335-                ancestor = column.find_ancestor(
336-                    exp.Select,
337-                    exp.Qualify,
338-                    exp.Order,
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def is_cte\\|self.cte\" sqlglot/optimizer/scope.py | head -20 && grep -n \"pivot\" sqlglot/optimizer/merge_subqueries.py sqlglot/optimizer/pushdown_projections.py sqlglot/optimizer/eliminate_ctes.py sqlglot/optimizer/pushdown_predicates.py sqlglot/optimizer/eliminate_subqueries.py | head -20; grep -n \"pivot\" tests/test_optimizer.py | head -60", "description": "Check CTE source handling and existing pivot optimizer tests"}
[tool_result] 48:        cte_sources: Sources from CTES
92:        cte_sources: dict[str, exp.Table | Scope] | None = None,
98:        self.cte_sources = cte_sources or {}
100:        self.sources.update(self.cte_sources)
107:        self.cte_scopes: list[Scope] = []
138:        cte_sources: dict[str, exp.Table | Scope] | None = None,
148:            cte_sources={**self.cte_sources, **(cte_sources or {})},
517:    def is_cte(self) -> bool:
667:            yield from _traverse_scope(Scope(ddl_expression, cte_s
…[410 chars elided]…
t/optimizer/eliminate_subqueries.py:125:    # - drop the "pivot" arg from a pivoted subquery
sqlglot/optimizer/eliminate_subqueries.py:128:    if not parent_scope or parent_scope.pivots or isinstance(parent_scope.expression, exp.Lateral):
282:                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias"
287:            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",
[tool_use Bash] {"command": "sed -n 265,300p tests/test_optimizer.py && grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql | head -40", "description": "Inspect existing pivot optimizer tests and fixtures"}
[tool_result]             "WITH test AS (SELECT * FROM catalog.db.t1 AS t1) SELECT * FROM test AS test",
        )

        self.assertEqual(
            optimizer.qualify_tables.qualify_tables(
                parse_one(
                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y'))"
                ),
                db="db",
                catalog="catalog",
            ).sql(),
            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVO
…[2461 chars elided]…
N (`produce`.`q1`, `produce`.`q2`, `produce`.`q3`, `produce`.`q4`)) AS `produce`;
tests/fixtures/optimizer/optimizer.sql:761:# title: unpivoted table source with multiple value columns
tests/fixtures/optimizer/optimizer.sql:764:SELECT * FROM produce AS produce(product, q1, q2, q3, q4) UNPIVOT((first_half_sales, second_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'));
tests/fixtures/optimizer/optimizer.sql:771:UNPIVOT((`first_half_sales`, `second_half_sales`) FOR
[tool_use Bash] {"command": "sed -n 690,800p tests/fixtures/optimizer/optimizer.sql; grep -n -i \"pivot\" tests/fixtures/optimizer/*.sql | grep -v \"^tests/fixtures/optimizer/optimizer.sql:\\(69\\|7[0-7]\\)\" | head -30", "description": "Read existing unpivot qualify fixtures"}
[tool_result] SELECT
  "FINAL"."ID" AS "ID",
  "FINAL"."TIMESTAMP_1" AS "TIMESTAMP_1"
FROM "SOURCE" AS "SOURCE"
PIVOT(MAX("SOURCE"."VALUE") FOR "SOURCE"."KEY" IN ('a', 'b', 'c')) AS "FINAL"("ID", "TIMESTAMP_1", "TIMESTAMP_2", "COL_1", "COL_2", "COL_3");

# title: unpivoted table source with a single value column, unpivot columns can't be qualified
# execute: false
# dialect: snowflake
SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
SELECT
  "M_SAL
…[6336 chars elided]…
rom a pivoted source, pivot has column aliases
tests/fixtures/optimizer/optimizer.sql:677:  PIVOT(MAX(value) FOR key IN ('a', 'b', 'c'))
tests/fixtures/optimizer/qualify_columns.sql:269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
tests/fixtures/optimizer/qualify_columns.sql:270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 ORDER BY _0.EMPID;
[tool_use Bash] {"command": "sed -n 618,635p tests/fixtures/optimizer/optimizer.sql; cd /tmp/unpivot-repro && cat > pivot.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nsql = \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FR
…[26 chars elided]…
b IN (1, 2))\"\ne = qualify(parse_one(sql, read=\"duckdb\"), dialect=\"duckdb\", schema={\"t\": {\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\"}}, validate_qualify_columns=True, identify=False)\nprint(e.sql(dialect=\"duckdb\"))\nEOF\n<work>/env-sqlglot/bin/python -I pivot.py", "description": "Check PIVOT over CTE qualifies correctly for comparison"}
[tool_result] # title: selecting all columns from a pivoted CTE source, using alias for the aggregation and generating bigquery
# execute: false
# dialect: bigquery
WITH u_cte(f, g, h) AS (SELECT * FROM u) SELECT * FROM u_cte PIVOT(SUM(f) AS sum FOR h IN ('x', 'y'));
WITH `u_cte` AS (
  SELECT
    `u`.`f` AS `f`,
    `u`.`g` AS `g`,
    `u`.`h` AS `h`
  FROM `u` AS `u`
)
SELECT
  `_0`.`g` AS `g`,
  `_0`.`sum_x` AS `sum_x`,
  `_0`.`sum_y` AS `sum_y`
FROM `u_cte` AS `u_cte`
PIVOT(SUM(`u_cte`.`f`) AS `sum` FOR `u_cte`.`h` IN ('x', 'y')) AS `_0`;

WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT _0.id AS id, _0."1" AS "1", _0."2" AS "2" FROM c AS c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS _0
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > dbg.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one, exp\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_columns import _unpivot_colu
…[976 chars elided]…
scratch/env-sqlglot/bin/python -I dbg.py \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"; echo ---; <work>/env-sqlglot/bin/python -I dbg.py \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR feb IN (1, 2))\"", "description": "Debug scope sources and columns for UNPIVOT vs PIVOT over CTE"}
[tool_result] SCOPE Select sources: {'t': 'Table'}
  pivots: [] columns: ['id', 'jan', 'feb'] unqual: ['id', 'jan', 'feb']
SCOPE Select sources: {'c': 'Table'}
  pivots: ['c'] columns: ['v', 'm', 'jan', 'feb'] unqual: ['v', 'm', 'jan', 'feb']
---
SCOPE Select sources: {'t': 'Table'}
  pivots: [] columns: ['id', 'jan', 'feb'] unqual: ['id', 'jan', 'feb']
SCOPE Select sources: {'c': 'Scope', '_0': 'Table'}
  pivots: ['_0'] columns: ['jan', 'feb'] unqual: ['jan', 'feb']
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "sed -n 60,70p sqlglot/optimizer/scope.py >/dev/null; sed -n 805,820p sqlglot/optimizer/scope.py", "description": "Re-read the pivoted-table source assignment in scope.py"}
[tool_result]         if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless
                # it is pivoted, because then we get back a new table and hence a new source.
                pivots = expression.args.get("pivots")
                if pivots:
                    sources[pivots[0].alias] = expression
                else:
                    sources[source_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                if pivots:\n                    sources[pivots[0].alias] = expression\n                else:", "new_string": "                if pivots:\n                    sources[pivots[0].alias] = scope.sources[table_name]\n                else:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && <work>/env-sqlglot/bin/python -I repro.py", "description": "Rerun UNPIVOT repro after scope change"}
[tool_result] bigquery ERR  OptimizeError Ambiguous column 'id'
duckdb ERR  OptimizeError Ambiguous column 'id'
snowflake ERR  OptimizeError Ambiguous column 'ID'
duckdb OK   SELECT _1.id AS id, _1.m AS m, _1.v AS v FROM (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) AS _0 UNPIVOT(v FOR m IN (jan, feb)) AS _1
duckdb ERR  OptimizeError Ambiguous column 'id' (Line: 1, Col: 48)
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > nov.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nsql = sys.argv[1]\ne = qualify(parse_one(sql, read=\"duckdb\"), dialect=\"duckdb\", schema={\"t\": {\"id\": \"INT\",
…[162 chars elided]…
2-noise-scratch/env-sqlglot/bin/python -I nov.py \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"; <work>/env-sqlglot/bin/python -I nov.py \"WITH c AS (SELECT id, jan, feb FROM t) SELECT id, v, m FROM c UNPIVOT(v FOR m IN (jan, feb))\"", "description": "Inspect qualified output without validation for CTE UNPIVOT"}
[tool_result] WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT "".id AS id, "".m AS m, "".v AS v FROM c AS c UNPIVOT(v FOR m IN (jan, feb))
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT "".id AS id, "".v AS v, "".m AS m FROM c AS c UNPIVOT(v FOR m IN (jan, feb))
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                if pivots:\n                    sources[pivots[0].alias] = scope.sources[table_name]\n                else:", "new_string": "                if pivots:\n                    sources[pivots[0].alias] = expression\n                else:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "git status --short && sed -n 173,200p sqlglot/optimizer/resolver.py && sed -n 90,100p sqlglot/optimizer/scope.py", "description": "Confirm scope.py reverted and read resolver source lookup tail"}
[tool_result]             elif isinstance(source, Scope) and isinstance(source.expression, exp.SetOperation):
                columns = self.get_source_columns_from_set_op(source.expression)
            else:
                selectable = source.expression.assert_is(exp.Selectable)
                select = seq_get(selectable.selects, 0)

                if isinstance(select, exp.QueryTransform):
                    # https://spark.apache.org/docs/3.5.1/sql-ref-syntax-qry-select-transform.html
                 
…[985 chars elided]…
pe_type: ScopeType = ScopeType.ROOT,
        lateral_sources: dict[str, exp.Table | Scope] | None = None,
        cte_sources: dict[str, exp.Table | Scope] | None = None,
        can_be_correlated: bool | None = None,
    ) -> None:
        self.expression = expression
        self.sources = sources or {}
        self.lateral_sources = lateral_sources or {}
        self.cte_sources = cte_sources or {}
        self.sources.update(self.lateral_sources)
        self.sources.update(self.cte_sources)
[tool_use Bash] {"command": "sed -n 133,142p sqlglot/optimizer/resolver.py", "description": "Re-read resolver get_source_columns head before editing"}
[tool_result]     def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._get_source_columns_cache:
            if name not in self.scope.sources:
                raise OptimizeError(f"Unknown table: {name}")

            source = self.scope.sources[name]

            if isinstance(source, exp.Table):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            source = self.scope.sources[name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)", "new_string": "            source = self.scope.sources[name]\n\n            if isinstance(source, exp.Table) and source.args.get(\"pivots\"):\n                # A pivoted CTE is registered as a Table, but its columns are the CTE's\n                source = self.scope.cte_sources.get(source.name, source)\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && <work>/env-sqlglot/bin/python -I repro.py; <work>/env-sqlglot/bin/python -I nov.py \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"; <work>/env-sqlglot/bin/python -I pivot.py", "description": "Rerun repros after resolver fix for pivoted CTE columns"}
[tool_result] bigquery OK   WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT c.id AS id, c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c
duckdb OK   WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT c.id AS id, c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS c
snowflake OK   WITH C AS (SELECT T.ID AS ID, T.JAN AS JAN, T.FEB AS FEB FROM T AS T) SELECT C.ID AS ID, C.M AS M, C.V AS V FROM C AS C UNPIVOT(V FOR M IN (JAN
…[300 chars elided]…
 AS c UNPIVOT(v FOR m IN (jan, feb)) AS c
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT c.id AS id, c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS c
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT _0.id AS id, _0."1" AS "1", _0."2" AS "2" FROM c AS c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS _0
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[assistant] The repro now qualifies in all dialects. Running the project's test suite to check for regressions.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
....................................................................................................................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
.........
…[291 chars elided]…
[ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                    [100%]
1092 passed, 17865 subtests passed in 51.20s
[assistant] Full suite passes (1092 tests). Now I'll add a regression fixture next to the existing UNPIVOT fixtures, using the full optimizer's output.
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > opt.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import optimize\nsql = \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"\nfor d in [\"bigquery\", \"
…[330 chars elided]…
rk/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/test_optimizer.py | head; grep -n \"unpivoted table source with multiple\" -B2 -A22 ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql | tail -4", "description": "Generate expected full-optimizer output for new fixture"}
[tool_result] SELECT
  `c`.`id` AS `id`,
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
----
SELECT
  "c"."id" AS "id",
  "c"."m" AS "m",
  "c"."v" AS "v"
FROM "c" AS "c"
UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
----
282:                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias"
287:            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",
780-with cte1("id", foo) as (select 1, 2) select "id" from cte1;
781-WITH "CTE1" AS (
782-  SELECT
783-    1 AS "id"
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[assistant] The full optimizer drops the `WITH` clause, leaving `FROM c` dangling. Before deciding whether that's mine to fix, I'll check whether it happens on the untouched HEAD.
[tool_use Bash] {"command": "rm -rf /tmp/orig-sqlglot && mkdir -p /tmp/orig-sqlglot && cd ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1 && git archive HEAD sqlglot | tar -x -C /tmp/orig-sqlglot && cd /tmp/unpivot-repro && sed 's#20261028-114454-optimizer-select-from-cte-unpivo/base-1#../../../../../../tmp/orig-sqlglot#' opt.py > /dev/null; cat > opt_o
…[298 chars elided]…
\n        print(optimize(parse_one(sql, read=d), schema={\"t\": {\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\"}}, dialect=d).sql(d, pretty=True))\n    except Exception as ex:\n        print(\"ERR\", type(ex).__name__, ex)\nEOF\n<work>/env-sqlglot/bin/python -I opt_orig.py", "description": "Compare full optimizer output against untouched HEAD copy"}
[tool_result] /tmp/orig-sqlglot/sqlglot/__init__.py
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > rules.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.qualify import qualify\nd = \"bigquery\"\nschema = {\"t\": {\"id\": \"INT\", \"jan\": \"INT
…[366 chars elided]…
alify\",): continue\n    try:\n        e = rule(e, schema=schema, dialect=d) if \"schema\" in rule.__code__.co_varnames else rule(e, dialect=d)\n    except TypeError:\n        e = rule(e)\n    print(rule.__name__, \"->\", e.sql(d))\nEOF\n<work>/env-sqlglot/bin/python -I rules.py 2>&1 | head -30", "description": "Trace which optimizer rule drops the CTE"}
[tool_result] qualify: WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
pushdown_projections -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
normalize -> WITH `c` AS (S
…[1997 chars elided]…
m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
canonicalize -> SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
simplify -> SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "cat sqlglot/optimizer/eliminate_ctes.py | sed -n 1,60p", "description": "Read eliminate_ctes to see how CTE references are counted"}
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
[tool_use Bash] {"command": "grep -n \"def ref_count\" -A 25 sqlglot/optimizer/scope.py; grep -n \"def selected_sources\" -A 40 sqlglot/optimizer/scope.py | head -60", "description": "Read ref_count and selected_sources in scope.py"}
[tool_result] 578:    def ref_count(self) -> dict[int, int]:
579-        """
580-        Count the number of times each scope in this tree is referenced.
581-
582-        Returns:
583-            dict[int, int]: Mapping of Scope instance ID to reference count
584-        """
585-        scope_ref_count: dict[int, int] = defaultdict(int)
586-
587-        for scope in self.traverse():
588-            for _, source in scope.selected_sources.values():
589-                scope_ref_count[id(source)] += 1
590-
591-
…[1935 chars elided]…
2-            for table in self.tables:
403-                self._references.append((table.alias_or_name, table))
404-            for _expr in itertools.chain(self.derived_tables, self.udtfs):
405-                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
406-                expression: exp.Expr = _expr
407-                self._references.append(
408-                    (
409-                        _get_source_alias(expression),
410-                        (
[assistant] Root cause of the dropped CTE: for `c UNPIVOT(...)` the pivot alias defaults to `c`, so the pivoted source overwrites the CTE's `c` key in `scope.sources`. `ref_count` only sees `selected_sources`, so the CTE looks unreferenced and `eliminate_ctes` removes it. I'll check who consumes `selected_sources` before touching it.
[tool_use Bash] {"command": "grep -rn \"selected_sources\" sqlglot/ | grep -v \"def selected_sources\" ", "description": "Find consumers of Scope.selected_sources"}
[tool_result] sqlglot/lineage.py:325:                selected_node, _ = scope.selected_sources.get(table, (None, None))
sqlglot/optimizer/isolate_table_selects.py:24:        if len(scope.selected_sources) == 1:
sqlglot/optimizer/isolate_table_selects.py:27:        for _, source in scope.selected_sources.values():
sqlglot/optimizer/pushdown_predicates.py:47:                selected_sources = scope.selected_sources
sqlglot/optimizer/pushdown_predicates.py:55:                for k, (node, source) in selected_sou
…[2561 chars elided]…
ne
sqlglot/optimizer/scope.py:380:        if self._selected_sources is None:
sqlglot/optimizer/scope.py:394:            self._selected_sources = result
sqlglot/optimizer/scope.py:395:        return self._selected_sources
sqlglot/optimizer/scope.py:588:            for _, source in scope.selected_sources.values():
sqlglot/generators/exasol.py:184:    if not scope or not scope.selected_sources:
sqlglot/generators/exasol.py:189:    for source_name, (source_expr, _) in scope.selected_sources.items():
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > opt2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import optimize\nschema = {\"t\": {\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\"}}\nfor sql in [\"WITH c AS (SELECT id, jan, feb FROM
…[124 chars elided]…
 c UNPIVOT(v FOR m IN (jan, feb))\"]:\n    try:\n        print(optimize(parse_one(sql, read=\"duckdb\"), schema=schema, dialect=\"duckdb\").sql(\"duckdb\"))\n    except Exception as ex:\n        print(\"ERR\", type(ex).__name__, ex)\nEOF\n<work>/env-sqlglot/bin/python -I opt2.py", "description": "Check full optimize output for PIVOT vs UNPIVOT over CTE"}
[tool_result] WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "_0"."id" AS "id", "_0"."1" AS "1", "_0"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "feb" IN (1, 2)) AS "_0"
SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > sel.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfor sql in [\"WITH c AS (SELECT id, jan, feb FROM t) 
…[234 chars elided]…
\n    root = build_scope(e)\n    for s in root.traverse():\n        print(type(s.expression).__name__, {k: (type(n).__name__, type(v).__name__) for k, (n, v) in s.selected_sources.items()}, \"refcount:\", dict(root.ref_count()).values())\nEOF\n<work>/env-sqlglot/bin/python -I sel.py", "description": "Print selected_sources for PIVOT vs UNPIVOT over CTE"}
[tool_result] Select {'t': ('Table', 'Table')} refcount: dict_values([1, 1])
Select {'c': ('Table', 'Scope')} refcount: dict_values([1, 1])
Select {'t': ('Table', 'Table')} refcount: dict_values([1, 1])
Select {'c': ('Table', 'Table')} refcount: dict_values([1, 1])
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[assistant] PIVOT counts the CTE because its `c` key still maps to the CTE `Scope`. UNPIVOT's `c` key is overwritten by the pivoted `Table`. The minimal fix that keeps the resolver change is to count a pivoted-CTE selection against the CTE in `ref_count`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "        for scope in self.traverse():\n            for _, source in scope.selected_sources.values():\n                scope_ref_count[id(source)] += 1", "new_string": "        for scope in self.traverse():\n            for _, source in scope.selected_sources.values():\n                if isinstance(source, exp.Table) and source.args.get(\"pivots\"):\n                    # A pivoted CTE is selected as a Table, but it still references the CTE\n                    if cte := scope.cte_sources.get(source.name):\n                        source = cte\n\n                scope_ref_count[id(source)] += 1"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && <work>/env-sqlglot/bin/python -I opt2.py && <work>/env-sqlglot/bin/python -I opt.py && <work>/env-sqlglot/bin/python -I repro.py", "description": "Verify full optimize output keeps CTE for UNPIVOT"}
[tool_result] WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "_0"."id" AS "id", "_0"."1" AS "1", "_0"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "feb" IN (1, 2)) AS "_0"
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
WITH `c` AS (
  SELECT
    `t`.`id` AS `id`,
    `t`.`jan` AS `jan`,
    
…[890 chars elided]…
S C UNPIVOT(V FOR M IN (JAN, FEB)) AS C
duckdb OK   SELECT _1.id AS id, _1.m AS m, _1.v AS v FROM (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) AS _0 UNPIVOT(v FOR m IN (jan, feb)) AS _1
duckdb OK   WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT c.id AS id, c.v AS v, c.m AS m FROM c AS c UNPIVOT(v FOR m IN (jan, feb)) AS c
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[assistant] Full optimize output now keeps the CTE and qualifies correctly. Next I'll add regression fixtures, starting with the format of the existing `qualify_columns.sql` PIVOT entries.
[tool_use Bash] {"command": "sed -n 255,285p tests/fixtures/optimizer/qualify_columns.sql; grep -n \"qualify_columns.sql\" -A 25 tests/test_optimizer.py | head -60; grep -n \"^# title\" tests/fixtures/optimizer/qualify_columns.sql | tail -3; tail -5 tests/fixtures/optimizer/qualify_columns.sql", "description": "Inspect qualify_columns fixture format and test runner"}
[tool_result] WITH T1 AS (SELECT 1 AS C1, 1 AS C2, 'Y' AS TOP_PARENT_INDICATOR, 1 AS ID FROM DUAL DUAL), T2 AS (SELECT 1 AS C2, 2 AS ID FROM DUAL DUAL) SELECT T1.C1 AS C1 FROM T1 T1 LEFT JOIN T2 T2 ON T1.C2 = T2.C2 WHERE (T1.TOP_PARENT_INDICATOR = 'Y' OR LEVEL = 1) START WITH (NOT T1.ID IS NULL) CONNECT BY PRIOR T1.ID = T2.ID;

# execute: false
# dialect: postgres
SELECT * FROM ROWS FROM (GENERATE_SERIES(1, 3), GENERATE_SERIES(10, 12)) AS t(a, b);
SELECT t.a AS a, t.b AS b FROM ROWS FROM (GENERATE_SERIES(1, 3
…[1088 chars elided]…
scope
1047:# title: SEMI + normal joins reinclude the table on scope
1051:# title: ANTI + normal joins reinclude the table on scope
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x SEMI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;

# title: ANTI + normal joins reinclude the table on scope
SELECT * FROM x ANTI JOIN y USING (b) JOIN y USING (b);
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;
[tool_use Bash] {"command": "grep -n \"def test_qualify_columns\\b\" -A 12 tests/test_optimizer.py; grep -n \"def check_file\" -A 3 tests/test_optimizer.py; grep -n \"\\\"qualify_columns\\\"\\|'qualify_columns'\\|qualify_columns.sql\\|validate_qualify\" tests/test_optimizer.py | head", "description": "Locate qualify_columns fixture test driver and schema"}
[tool_result] 341:    def test_qualify_columns(self, logger):
342-        self.assertEqual(
343-            optimizer.qualify.qualify(
344-                parse_one(
345-                    """
346-                    SELECT Teams.Name, count(*)
347-                    FROM raw.TeamMemberships as TeamMemberships
348-                    join raw.Teams
349-                        on Teams.Id = TeamMemberships.TeamId
350-                    GROUP BY 1
351-                    """,
352-                    read="bi
…[307 chars elided]…
alidate_qualify_columns")
177:                if validate_qualify_columns is not None:
178:                    func_kwargs["validate_qualify_columns"] = string_to_bool(
179:                        validate_qualify_columns
585:            "qualify_columns",
652:            optimizer.qualify_columns.validate_qualify_columns(qualified)
710:                    optimizer.qualify_columns.validate_qualify_columns(expression)
735:            optimizer.qualify_columns.validate_qualify_columns(expression)
[tool_use Bash] {"command": "sed -n 580,592p tests/test_optimizer.py; sed -n 20,30p tests/test_optimizer.py; grep -n \"^SCHEMA\\|schema = {\" tests/test_optimizer.py | head -3; sed -n 1,40p tests/fixtures/optimizer/qualify_columns.sql | head -40", "description": "Read qualify_columns fixture driver and the default test schema"}
[tool_result]             ).sql(dialect="bigquery"),
            "WITH `cte` AS (SELECT `base_table`.`id` AS `id`, `base_table`.`items` AS `items` FROM `base_table` AS `base_table`) SELECT (SELECT SUM(`item`.`price`) AS `_col_0` FROM UNNEST(`cte`.`items`) AS `item` WHERE `category` = 'electronics') AS `electronics_total` FROM `cte` AS `cte`",
        )

        self.check_file(
            "qualify_columns",
            qualify_columns,
            execute=True,
            schema=self.schema,
        )
     
…[911 chars elided]…
yy.p AS p FROM (SELECT xx.x AS x FROM xx AS xx) AS xx CROSS JOIN yy AS yy;

SELECT a FROM x AS z;
SELECT z.a AS a FROM x AS z;

SELECT a AS a FROM x;
SELECT x.a AS a FROM x AS x;

SELECT x.a FROM x;
SELECT x.a AS a FROM x AS x;

SELECT x.a AS a FROM x;
SELECT x.a AS a FROM x AS x;

SELECT a AS b FROM x;
SELECT x.a AS b FROM x AS x;

# execute: false
SELECT 1, 2 + 3 FROM x;
SELECT 1 AS "1", 2 + 3 AS _col_1 FROM x AS x;

# execute: false
SELECT a + b FROM x;
SELECT x.a + x.b AS _col_0 FROM x AS x;
[tool_use Bash] {"command": "sed -n 117,135p tests/test_optimizer.py; grep -n \"CREATE\\|create\" tests/fixtures/optimizer/qualify_columns_ddl.sql | head -3", "description": "Read the qualify_columns fixture schema"}
[tool_result]         self.schema = {
            "x": {
                "a": "INT",
                "b": "INT",
            },
            "y": {
                "b": "INT",
                "c": "INT",
            },
            "z": {
                "b": "INT",
                "c": "INT",
            },
            "w": {
                "d": "TEXT",
                "e": "TEXT",
            },
            "temporal": {
                "d": "DATE",
2:WITH cte AS (SELECT b FROM y) CREATE TABLE s AS SELECT * FROM cte;
3:WITH cte AS (SELECT y.b AS b FROM y AS y) CREATE TABLE s AS SELECT cte.b AS b FROM cte AS cte;
6:WITH cte1 AS (SELECT b FROM y) CREATE TABLE s AS WITH cte2 AS (SELECT b FROM cte1) SELECT * FROM cte2;
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > gen.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"x\": {\"a\": \"INT\", \"b\": \"INT\"}}\nfor d, sql in [\n    (\"bigquery\", \"WITH c AS (SELECT a, b FRO
…[128 chars elided]…
v FOR m IN (a, b));\"),\n    (\"duckdb\", \"WITH c AS (SELECT a, b FROM x) SELECT m, v FROM c UNPIVOT(v FOR m IN (a, b));\"),\n]:\n    print(d, qualify(parse_one(sql, read=d), schema=schema, dialect=d, validate_qualify_columns=True).sql(d))\nEOF\n<work>/env-sqlglot/bin/python -I gen.py", "description": "Generate expected qualify output for new fixtures"}
[tool_result] bigquery WITH `c` AS (SELECT `x`.`a` AS `a`, `x`.`b` AS `b` FROM `x` AS `x`) SELECT `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`a`, `c`.`b`)) AS `c`
duckdb WITH "c" AS (SELECT "x"."a" AS "a", "x"."b" AS "b" FROM "x" AS "x") SELECT "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("a", "b")) AS "c"
duckdb WITH "c" AS (SELECT "x"."a" AS "a", "x"."b" AS "b" FROM "x" AS "x") SELECT "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("a", "b")) AS "c"
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[tool_use Bash] {"command": "grep -n \"\\\"optimizer\\\",\" -B2 -A8 tests/test_optimizer.py | head -30; grep -n \"def test_optimize\" -A 3 tests/test_optimizer.py | head; tail -4 tests/fixtures/optimizer/optimizer.sql", "description": "Check optimizer fixture driver and file tail"}
[tool_result] 231-
232-        self.check_file(
233:            "optimizer",
234-            optimizer.optimize,
235-            infer_schema=True,
236-            pretty=True,
237-            execute=True,
238-            schema=schema,
239-        )
240-
241-    def test_isolate_table_selects(self):
222:    def test_optimize(self, logger):
223-        self.assertEqual(optimizer.optimize("x = 1 + 1", identify=False).sql(), "x = 2")
224-
225-        schema = {
--
740:    def test_optimize_error_highlighting(self):
741-        # highlighting works with sql parameter
742-        sql = "SELECT nonexistent FROM x"
743-
--
SELECT
  ARRAY_AGG("T"."ID") WITHIN GROUP (ORDER BY
    "T"."ID") OVER (PARTITION BY "T"."GRP") AS "_col_0"
FROM "T" AS "T";
[tool_use Bash] {"command": "sed -n 222,231p tests/test_optimizer.py && sed -n 300,340p tests/test_optimizer.py | grep -n \"def \\|assertEqual\" | head", "description": "Read test_optimize schema and surrounding structure"}
[tool_result]     def test_optimize(self, logger):
        self.assertEqual(optimizer.optimize("x = 1 + 1", identify=False).sql(), "x = 2")

        schema = {
            "x": {"a": "INT", "b": "INT"},
            "y": {"b": "INT", "c": "INT"},
            "z": {"a": "INT", "c": "INT"},
            "u": {"f": "INT", "g": "INT", "h": "TEXT"},
        }

10:    def test_qualify_tables_copies_typed_alias_columns(self):
21:        self.assertEqual(original.sql(), new.sql())
23:    def test_normalize(self):
24:        self.assertEqual(
32:        self.assertEqual(
[tool_use Bash] {"command": "cd /tmp/unpivot-repro && cat > gen2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import optimize\nschema = {\"x\": {\"a\": \"INT\", \"b\": \"INT\"}, \"y\": {\"b\": \"INT\", \"c\": \"INT\"}, \"z\": {\"a\": \"INT\", \"c\":
…[59 chars elided]…
"TEXT\"}}\nsql = \"WITH c AS (SELECT a, b FROM x) SELECT * FROM c UNPIVOT(v FOR m IN (a, b));\"\nprint(optimize(parse_one(sql, read=\"bigquery\"), schema=schema, dialect=\"bigquery\", pretty=True).sql(\"bigquery\", pretty=True))\nEOF\n<work>/env-sqlglot/bin/python -I gen2.py", "description": "Generate expected full-optimizer output for BigQuery fixture"}
[tool_result] WITH `c` AS (
  SELECT
    `x`.`a` AS `a`,
    `x`.`b` AS `b`
  FROM `x` AS `x`
)
SELECT
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`a`, `c`.`b`)) AS `c`
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1
[assistant] Both fixtures' expected output is generated from the fixed code. Adding them now.
[tool_use Bash] {"command": "tail -c 200 tests/fixtures/optimizer/qualify_columns.sql | od -c | tail -3", "description": "Check trailing newline state of qualify_columns fixture"}
[tool_result] 0000260        A   S       y   _   2       O   N       x   .   b       =
0000300        y   _   2   .   b   ;  \n                                
0000310
[tool_use Bash] {"command": "cat >> tests/fixtures/optimizer/qualify_columns.sql <<'EOF'\n\n# execute: false\n# dialect: bigquery\nWITH c AS (SELECT a, b FROM x) SELECT * FROM c UNPIVOT(v FOR m IN (a, b));\nWITH `c` AS (SELECT `x`.`a` AS `a`, `x`.`b` AS `b` FROM `x` AS `x`) SELECT `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`a`, `c`.`b`)) AS `c`;\nEOF\ntail -c 120 tests/fixtures/optimizer/optimizer.sql | od -c | tail -2", "description": "Append BigQuery UNPIVOT-over-CTE qualify fixture"}
[tool_result] 0000160        A   S       "   T   "   ;                                
0000170
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "old_string": "# title: quoting is preserved\n# dialect: snowflake", "new_string": "# title: unpivoted CTE source keeps the CTE and qualifies its columns\n# execute: false\n# dialect: bigquery\nWITH c AS (SELECT a, b FROM x) SELECT * FROM c UNPIVOT(v FOR m IN (a, b));\nWITH `c` AS (\n  SELECT\n    `x`.`a` AS `a`,\n    `x`.`b` AS `b`\n  FROM `x` AS `x`\n)\nSELECT\n  `c`.`m` AS `m`,\n  `c`.`v` AS `v`\nFROM `c` AS `c`\nUNPIVOT(`v` FOR `m` IN (`c`.`a`, `c`.`b`)) AS `c`;\n\n# title: quoting is preserved\n# dialect: snowflake"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -30", "description": "Run optimizer test module with new fixtures", "timeout": 600000}
[tool_result]                     )
    
                future = pool.submit(parse_and_optimize, func, sql, dialect, **func_kwargs)
                results[future] = (
                    sql,
                    title,
                    expected,
                    dialect,
                    execute if meta.get("execute") is None else False,
                )
    
        for future in as_completed(results):
            sql, title, expected, dialect, execute = results[future]
    
            with self
…[754 chars elided]…
    - - - -  - - - -      - -
E               + WITH c AS (SELECT x.a AS a, x.b AS b FROM x AS x) SELECT c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.a, c.b)) AS c

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[240, WITH c AS (SELECT a, b FROM x) SELECT * FROM c UNPIVOT(v FOR m IN (a, b))] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
1 failed, 77 passed, 3706 subtests passed in 13.28s
[assistant] The fixture expectation was wrong: this driver emits unquoted identifiers. Correcting the expected line to match the actual output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/qualify_columns.sql", "old_string": "WITH `c` AS (SELECT `x`.`a` AS `a`, `x`.`b` AS `b` FROM `x` AS `x`) SELECT `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`a`, `c`.`b`)) AS `c`;", "new_string": "WITH c AS (SELECT x.a AS a, x.b AS b FROM x AS x) SELECT c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.a, c.b)) AS c;"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114454-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/qualify_columns.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short; cat Makefile | grep -A3 \"^style\"", "description": "Run full test suite and check changed files and style target", "timeout": 900000}
[tool_result] ............................................................................................................ [ 76%]
............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                  [100%]
1092 passed, 17867 subtests passed in 50.06s
 M sqlglot/optimizer/resolver.py
 M sqlglot/optimizer/scope.py
 M tests/fixtures/optimizer/optimizer.sql
 M tests/fixtures/optimizer/qualify_columns.sql
style:
	pre-commit run --all-files
	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
[assistant] Full suite passes with the new fixtures (1092 tests, 17867 subtests). Running the linters on the changed code.
[tool_use Bash] {"command": "B=<work>/env-sqlglot/bin; ls $B | grep -i \"ruff\\|mypy\"; ($B/ruff check sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py && $B/ruff format --check sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check the changed optimizer files"}
[tool_result] dmypy
mypy
mypyc
ruff
All checks passed!
2 files already formatted
 sqlglot/optimizer/resolver.py                |  4 ++++
 sqlglot/optimizer/scope.py                   |  5 +++++
 tests/fixtures/optimizer/optimizer.sql       | 16 ++++++++++++++++
 tests/fixtures/optimizer/qualify_columns.sql |  5 +++++
 4 files changed, 30 insertions(+)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/mypy sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py 2>&1 | tail -5; git diff sqlglot/", "description": "Run mypy on changed modules and show the source diff", "timeout": 600000}
[tool_result] Success: no issues found in 2 source files
diff --git a/sqlglot/optimizer/resolver.py b/sqlglot/optimizer/resolver.py
index 1868c662f..2969d19e5 100644
--- a/sqlglot/optimizer/resolver.py
+++ b/sqlglot/optimizer/resolver.py
@@ -139,6 +139,10 @@ class Resolver:
 
             source = self.scope.sources[name]
 
+            if isinstance(source, exp.Table) and source.args.get("pivots"):
+                # A pivoted CTE is registered as a Table, but its columns are the CTE's
+                sourc
…[429 chars elided]…
s Scope:
 
         for scope in self.traverse():
             for _, source in scope.selected_sources.values():
+                if isinstance(source, exp.Table) and source.args.get("pivots"):
+                    # A pivoted CTE is selected as a Table, but it still references the CTE
+                    if cte := scope.cte_sources.get(source.name):
+                        source = cte
+
                 scope_ref_count[id(source)] += 1
 
             for name in scope._semi_anti_join_tables:
[assistant] `qualify` now resolves `SELECT * FROM cte UNPIVOT(...)` correctly, and the full optimizer keeps the CTE. The project suite passes (1092 tests, 17867 subtests), and ruff and mypy are clean on the changed modules. Nothing is committed.

**Root cause:** the unpivoted CTE was registered as a plain table in the scope. Its columns were looked up in the schema, so `id`, `jan`, `feb` were unknown. The IN-list `jan` stayed unqualified and validation raised `Ambiguous column 'jan'`. The handling of the new output names (`v`, `m`) was already correct.

**Changes:**
- `sqlglot/optimizer/resolver.py`: a pi
…[725 chars elided]…
LECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))`, now qualifies in BigQuery, DuckDB and Snowflake. The full optimizer output keeps the `WITH`.

**Choices to check:**
- I fixed the dropped CTE as part of this, since without it `optimize` produces broken SQL for the same input. It is a separate change to the reference counting, so say if you'd rather it land separately.
- In DuckDB the IN-list columns stay unqualified (`IN (jan, feb)`), while BigQuery qualifies them (`IN (c.jan, c.feb)`). Derived-table UNPIVOTs already behave this way, so I left it. Both forms are valid.
