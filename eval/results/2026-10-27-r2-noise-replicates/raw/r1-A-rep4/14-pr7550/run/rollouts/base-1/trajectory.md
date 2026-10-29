# trajectory base-1

final message:
`SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))` now qualifies correctly over a CTE. The `v` and `m` names stay unqualified, the `IN (...)` items resolve to the CTE's columns, and the CTE is no longer dropped. The full suite passes (1092 tests, plus the new fixture subtest) and ruff is clean. I haven't committed anything.

There were three separate causes:

- **Resolver (`sqlglot/optimizer/resolver.py`)**: a pivoted CTE reference is a bare `Table`, so the resolver had no column list for it. It fell back to inference and assigned `v`/`m` to the CTE. It now looks up the CTE's columns through `cte_sources`.
- **Ref counting (`sqlglot/optimizer/scope.py`, `ref_count`)**: the outer query's reference to the CTE went through the pivoted `Table`, so the CTE's count was 0 and `eliminate_ctes` removed it. The optimized output had `FROM c` with no `WITH`. The count now maps the pivoted table back to the CTE scope.
- **Test (`tests/fixtures/optimizer/optimizer.sql`)**: added a BigQuery fixture using the query from the report, placed beside the existing UNPIVOT cases.

I didn't touch `qualify_columns.py`. The pivot-alias branch there is correct once the resolver knows the CTE's columns.

One side effect to review: PIVOT over a CTE now qualifies its source columns at the qualify stage (`SUM("c"."jan")` where HEAD left `SUM("jan")`). The full optimizer output for that case is unchanged and no test covers it, so I didn't add one. Table-sourced PIVOTs already behave this way.

Not covered: `eliminate_ctes` only decrements counts for `Scope` sources, so a CTE that is itself dropped and pivots another CTE leaves that inner CTE in place. The result is an unused CTE, not wrong SQL. I left it alone to keep the change small.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor d in ['bigquery','duckdb','snowflake']:\n    try:\n        print(d, qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read=d), dialect=d).sql(d))\n    except Exception as e: print(d, 'ERR', repr(e))\n\" ; grep -n -i \"unpivot\\|pivot\" sqlglot/optimizer/*.py | head -50", "description": "Reproduce UNPIVOT qualify issue and grep pivot handling"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/optimizer/eliminate_subqueries.py:125:    # - drop the "pivot" arg from a pivoted subquery
sqlglot/optimizer/eliminate_subqueries.py:128:    if not parent_scope or parent_scope.pivots or isinstance(parent_scope.expression, exp.Lateral):
sqlglot/optimizer/merge_subqueries.py:209:        and not outer_scope.pivots
sqlglot/optimizer/scope.py:81:    _pivots: list[exp.Pivot
…[4293 chars elided]…
ames:
sqlglot/optimizer/qualify_columns.py:792:        if pivot.unpivot:
sqlglot/optimizer/qualify_columns.py:793:            pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/optimizer/qualify_columns.py:795:            for field in pivot.fields:
sqlglot/optimizer/qualify_columns.py:797:                    pivot_exclude_columns.update(
sqlglot/optimizer/qualify_columns.py:802:            pivot_exclude_columns = set(c.output_name for c in pivot.find_all(exp.Column))
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nfor d in ['bigquery','duckdb','snowflake','']:\n    try:\n        print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d, 'ERR', repr(e))\n\"; sed -n 100,215p sqlglot/optimizer/qualify_columns.py; sed -n 600,660p sqlglot/optimizer/qualify_columns.py; sed -n 770,830p sqlglot/optimizer/qualify_columns.py", "description": "Run qualify repro and read relevant qualify_columns code"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("
…[8993 chars elided]…
urces)
            _add_except_columns(expression, tables, except_columns)
            _add_replace_columns(expression, tables, replace_columns)
            _add_rename_columns(expression, tables, rename_columns)
        elif expression.is_star:
            if isinstance(expression, exp.Column):
                tables.append(expression.table)
                _add_except_columns(expression.this, tables, except_columns)
                _add_replace_columns(expression.this, tables, replace_columns)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor q in ['SELECT * FROM t UNPIVOT(v FOR m IN (jan, feb))', 'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan
…[42 chars elided]…
read='duckdb')\n  print(repr(e.args['from'].this.args.get('pivots'))[:900] if e.args.get('from') else '')\n  print(qualify(e, dialect='duckdb').sql('duckdb'))\n\"; grep -n \"def _set_alias\" -A30 sqlglot/optimizer/qualify_tables.py | head -50; grep -n \"unpivot\" sqlglot/optimizer/scope.py sqlglot/optimizer/qualify.py | head", "description": "Compare UNPIVOT on table vs CTE and inspect pivot AST"}
[tool_result] SELECT * FROM "t" AS "t" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "t"

WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"

WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "u"."id" AS "id", "u"."m" AS "m", "u"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "u"
77:    def _set_alias(
78-        expression: exp.
…[640 chars elided]…
lize and target_alias:
93-                new_alias_name = normalize_identifiers(new_alias_name, dialect=dialect).name
94-        else:
95-            return
96-
97-        alias.set("this", exp.to_identifier(new_alias_name))
98-
99-        if columns:
100-            alias.set(
101-                "columns",
102-                [exp.to_identifier(c) if isinstance(c, str) else c.copy() for c in columns],
103-            )
104-
105-        expression.set("alias", alias)
106-
107-        if scope:
[tool_use Bash] {"command": "cd <work> && cd ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1 && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['SELECT * FROM t UNPIVOT(v FOR m IN (jan, feb))','W
…[12 chars elided]…
LECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"; sed -n 830,900p sqlglot/optimizer/qualify_columns.py", "description": "Compare bigquery and default qualify output for CTE vs table UNPIVOT"}
[tool_result] bigquery SELECT * FROM `t` AS `t` UNPIVOT(`t`.`v` FOR `t`.`m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
 SELECT * FROM "t" AS "t" UNPIVOT("t"."v" FOR "t"."m" IN ("t"."jan", "t"."feb")) AS "t"
 WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVO
…[3133 chars elided]…
.column(name, table=table) for table in using_tables]

                    new_selections.append(
                        alias(exp.func("coalesce", *coalesce_args), alias=name, copy=False)
                    )
                else:
                    alias_ = renamed_columns.get(name, name)
                    selection_expr = replaced_columns.get(name) or exp.column(name, table=table)
                    new_selections.append(
                        alias(selection_expr, alias_, copy=False)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nfor d in ['','duckdb']:\n  e=sqlglot.parse_one(q, read=d)\n  p=e.find(sqlglot.exp.Pivot)\n  print(d, repr(p)[:700])\n  print(d, [type(c).__name__ for c in p.find_all(sqlglot.exp.Column)])\n\"; grep -n \"PIVOT\\|UNPIVOT\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py sqlglot/dialects/dialect.py | head; grep -n \"def _parse_pivot\" -A30 sqlglot/parser.py | grep -n \"unpivot\\|expressions\\|_parse_column\\|_parse_id\" ", "description": "Inspect UNPIVOT AST node types across dialects"}
[tool_result]  Pivot(
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
 ['Column', 'Column', 'Column', 'Column']
duckdb Pivot(
  expressions=[
    Column(
      this=Identifier(this=v, quoted=False))],

…[991 chars elided]…
elf.expression(exp.In(this=value, field=self._parse_id_var()))
75:5090-            unpivot = False
77:5092-            unpivot = True
79:5094-            # https://docs.databricks.com/en/sql/language-manual/sql-ref-syntax-qry-select-unpivot.html#syntax
87:5102-        expressions = []
93:5108-        if unpivot:
94:5109-            expressions = self._parse_csv(self._parse_column)
96:5111-            expressions = self._parse_csv(self._parse_pivot_aggregation)
98:5113-        if not expressions:
[tool_use Bash] {"command": "grep -n \"set(\\\"table\\\"\\|\\.set('table'\\|def _qualify_columns\\|def qualify_columns\\|def _expand_alias_refs\\|def _qualify_outputs\" sqlglot/optimizer/qualify_columns.py; grep -n \"def get_table\" -A25 sqlglot/optimizer/qualify_columns.py | head -40", "description": "Locate table-assignment points in qualify_columns"}
[tool_result] 21:def qualify_columns(
314:def _expand_alias_refs(
385:                column.set("table", table)
474:                        col.set("table", resolver.get_table(col.name))
599:def _qualify_columns(
623:                column.set("table", exp.to_identifier(scope.pivots[0].alias))
637:                column.set("table", table)
651:                    column.set("table", table)
[tool_use Bash] {"command": "sed -n 21,100p sqlglot/optimizer/qualify_columns.py; sed -n 314,400p sqlglot/optimizer/qualify_columns.py; sed -n 460,480p sqlglot/optimizer/qualify_columns.py", "description": "Read qualify_columns entry and alias-ref expansion"}
[tool_result] def qualify_columns(
    expression: exp.Expr,
    schema: dict[str, object] | Schema,
    expand_alias_refs: bool = True,
    expand_stars: bool = True,
    infer_schema: bool | None = None,
    allow_partial_qualification: bool = False,
    dialect: DialectType = None,
) -> exp.Expr:
    """
    Rewrite sqlglot AST to have fully qualified columns.

    Example:
        >>> import sqlglot
        >>> schema = {"tbl": {"col": "INT"}}
        >>> expression = sqlglot.parse_one("SELECT col FROM tb
…[7101 chars elided]…
itional_references(
                scope, modifier_expressions, resolver.dialect, alias=True
            ),
        ):
            for agg in original.find_all(exp.AggFunc):
                for col in agg.find_all(exp.Column):
                    if not col.table:
                        col.set("table", resolver.get_table(col.name))

            original.replace(expanded)

        if expr.args.get("group"):
            selects = {s.this: exp.column(s.alias_or_name) for s in expression.selects}
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\nfrom sqlglot import exp\nfrom sqlglot.optimizer.qualify import qualify\norig=exp.Expr.set\ndef spy(self, arg_key, value, *a, **k):\n    if arg_key=='table' and isinstance(self, exp.Column) and self.name in ('v','m'):\n        print('SET', self.name, '->', value); traceback.print_stack(limit=4)\n    return orig(self, arg_key, value, *a, **k)\nexp.Expr.set=spy\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(q), dialect='')\n\" 2>&1 | head -60", "description": "Trace where pivot column v gets a table qualifier"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"    def set\\b\\|def set(\" sqlglot/expressions*.py sqlglot/expressions/*.py 2>/dev/null | head -3; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=qualify(sqlglot.parse_one(q), dialect='')\nprint(e.sql())\nprint(repr(e.find(sqlglot.exp.Pivot).expressions[0]))\n\"", "description": "Check default-dialect qualify output and AST"}
[tool_result] (eval):1: no matches found: sqlglot/expressions*.py
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("c"."v" FOR "c"."m" IN ("c"."jan", "c"."feb")) AS "c"
Column(
  this=Identifier(this='v', quoted=True),
  table=Identifier(this='c', quoted=True))
[tool_use Bash] {"command": "grep -rn \"def set(\" sqlglot/*.py | head -3; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\nfrom sqlglot import exp\nfrom sqlglot.optimizer import qualify as Q\nimport sqlglot.optimizer.qualify as qmod\nimport sqlglot.optimizer.qualify_columns as qc\nimport sqlglot.optimizer.qualify_tables as qt\nfor mod in 
…[126 chars elided]…
startswith(('_','qual')):\n      def w(*a,_f=f,_n=n,**k):\n        r=_f(*a,**k); print('CALL',_n); return r\n      setattr(mod,n,w)\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nimport sqlglot.optimizer.qualify as qq\nqq.qualify(sqlglot.parse_one(q), dialect='')\n\" 2>&1 | head -80", "description": "Trace which qualify step runs and assigns the table"}
[tool_result] CALL _separate_pseudocolumns
CALL _pop_table_column_aliases
CALL _pop_table_column_aliases
CALL _expand_using
CALL _expand_alias_refs
CALL _convert_columns_to_dots
CALL _qualify_columns
CALL _expand_stars
CALL qualify_outputs
CALL _expand_group_by
CALL _expand_order_by_and_distinct_on
CALL _separate_pseudocolumns
CALL _pop_table_column_aliases
CALL _pop_table_column_aliases
CALL _expand_using
CALL _expand_alias_refs
CALL _convert_columns_to_dots
CALL _qualify_columns
CALL _unpivot_columns
CALL _add_except_columns
CALL _add_replace_columns
CALL _add_rename_columns
CALL _expand_stars
CALL qualify_outputs
CALL _expand_group_by
CALL _expand_order_by_and_distinct_on
CALL qualify
[tool_use Bash] {"command": "grep -n \"def get_table\\|def all_columns\\|def _get_all_source_columns\\|def get_source_columns\" -A28 sqlglot/optimizer/qualify_columns.py | sed -n 1,200p | head -150", "description": "Read Resolver.get_table and column lookup logic"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"def get_table\" sqlglot/optimizer/ ; F=$(grep -rln \"class Resolver\" sqlglot/optimizer/); echo $F; grep -n \"def get_table\" -A30 $F", "description": "Locate Resolver class and get_table implementation"}
[tool_result] sqlglot/optimizer/resolver.py:34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
sqlglot/optimizer/resolver.py
34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
35-        """
36-        Get the table for a column name.
37-
38-        Args:
39-            column: The column expression (or column name) to find the table for.
40-        Returns:
41-            The table name if it can be found/inferred.
42-        """
43-        column_name 
…[805 chars elided]…
ch OptimizeError if column is still ambiguous and try to resolve with schema inference below
55-                try:
56-                    table_name = self._get_table_name_from_sources(
57-                        column_name, self._get_available_source_columns(join_context)
58-                    )
59-                except OptimizeError:
60-                    pass
61-
62-        if not table_name and self._infer_schema:
63-            sources_without_schema = tuple(
64-                source
[tool_use Bash] {"command": "sed -n 60,110p sqlglot/optimizer/resolver.py; grep -n \"def _get_table_name_from_sources\" -A25 sqlglot/optimizer/resolver.py; grep -n \"def get_source_columns\\|def all_columns\\|def _get_source_columns\" -A22 sqlglot/optimizer/resolver.py | head -80", "description": "Read resolver inference fallback and source column lookup"}
[tool_result]                     pass

        if not table_name and self._infer_schema:
            sources_without_schema = tuple(
                source
                for source, columns in self._get_all_source_columns().items()
                if not columns or "*" in columns
            )
            if len(sources_without_schema) == 1:
                table_name = sources_without_schema[0]

        if table_name not in self.scope.selected_sources:
            return exp.to_identifier(table_name)

   
…[5325 chars elided]…
            # directly select a struct field in a query.
151-                # this handles the case where the unnest is statically defined.
152-                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):
153-                    if not source_expr.type or source_expr.type.is_type(exp.DType.UNKNOWN):
154-                        unnest_expr = seq_get(source_expr.expressions, 0)
155-                        if isinstance(unnest_expr, exp.Column) and self.scope.parent:
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_columns import Resolver\nimport sqlglot.optimizer.qualify_columns as qc\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.schema import ensure_schema\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('SOURCES', {
…[128 chars elided]…
T v', resolver.get_table('v'), 'infer', resolver._infer_schema)\n    return orig(scope,resolver,**k)\nqc._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nqualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'), dialect='')\n\" 2>&1 | head -30", "description": "Inspect resolver sources and inferred table for pivot column"}
[tool_result] SOURCES {'t': 'Table'}
ALLCOLS {'t': []}
GET v t infer True
SOURCES {'c': 'Table'}
ALLCOLS {'c': []}
GET v c infer True
[tool_use Bash] {"command": "sed -n 395,425p sqlglot/optimizer/scope.py; sed -n 795,830p sqlglot/optimizer/scope.py", "description": "Read scope.py source registration for pivoted tables"}
[tool_result]         return self._selected_sources

    @property
    def references(self) -> list[tuple[str, exp.Selectable]]:
        if self._references is None:
            self._references = []

            for table in self.tables:
                self._references.append((table.alias_or_name, table))
            for _expr in itertools.chain(self.derived_tables, self.udtfs):
                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
                expression: exp.Exp
…[1623 chars elided]…
urce_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
                sources[source_name] = expression

            # Make sure to not include the joins twice
            if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
[assistant] The root cause is in `scope.py`: a pivoted CTE reference is registered as the bare `Table` node, so the resolver has no columns for it and falls back to inference, which attributes `v` and `m` to the source. Let me get a test baseline before changing anything.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no -x -q tests 2>&1 | tail -5", "description": "Run full test suite for baseline"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -5", "description": "Run full test suite for baseline"}
[tool_result] ............................................................................................................ [ 76%]
............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                    [100%]
1092 passed, 17865 subtests passed in 48.28s
[assistant] Baseline is green (1092 passed). Now the change: register a pivoted CTE reference against the CTE's scope so the resolver sees its columns.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless\n                # it is pivoted, because then we get back a new table and hence a new source.\n               
…[248 chars elided]…
ctual table, unless\n                # it is pivoted, because then we get back a new table and hence a new source.\n                # The pivoted source is still backed by the parent's columns, so we keep its scope.\n                pivots = expression.args.get(\"pivots\")\n                if pivots:\n                    sources[pivots[0].alias] = scope.sources[table_name]\n                else:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM
…[28 chars elided]…
M(jan) FOR id IN (1, 2))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb','snowflake']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"", "description": "Verify qualify output for CTE UNPIVOT and PIVOT across dialects"}
[tool_result] bigquery ERR OptimizeError("Ambiguous column 'id'")
bigquery ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
bigquery ERR OptimizeError("Ambiguous column 'feb'")
bigquery ERR OptimizeError("Ambiguous column 'jan' (Line: 1, Col: 83)")
 ERR OptimizeError("Ambiguous column 'id'")
 ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
 ERR OptimizeError("Ambiguous column 'feb'")
 ERR OptimizeError("Ambiguous column 'jan' (Line: 1, Col: 83)")
duckdb ERR OptimizeError("Ambiguous column 'id'")
duckdb ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
duckdb ERR OptimizeError("Ambiguous column 'feb'")
duckdb ERR OptimizeError("Ambiguous column 'jan' (Line: 1, Col: 83)")
snowflake ERR OptimizeError("Ambiguous column 'ID'")
snowflake ERR OptimizeError("Ambiguous column 'ID' (Line: 1, Col: 48)")
snowflake ERR OptimizeError("Ambiguous column 'FEB'")
snowflake ERR OptimizeError("Ambiguous column 'JAN' (Line: 1, Col: 83)")
[assistant] Now the CTE columns resolve, but the outer columns (`id`, `jan`, `feb`) end up unqualified. Let me see where they drop out.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.isolate_table_selects import isolate_table_selects\nfrom sqlglot.optimizer.norm
…[132 chars elided]…
b FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=sqlglot.parse_one(q)\ne=qualify_tables(e)\ne=qualify_columns(e, {}, infer_schema=True)\nprint(e.sql())\nfor s in traverse_scope(e): print(type(s.expression).__name__, {k:type(v).__name__ for k,v in s.sources.items()}, s.unqualified_columns)\n\" 2>&1 | tail -20", "description": "Step through qualify_columns to find unqualified id"}
[tool_result] WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT "".id AS id, "".m AS m, "".v AS v FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb))
Select {'t': 'Table'} []
Select {'c': 'Scope', '': 'Scope'} [Column(
  this=Identifier(this=id, quoted=False),
  table=Identifier(this='', quoted=True)), Column(
  this=Identifier(this=m, quoted=False),
  table=Identifier(this='', quoted=True)), Column(
  this=Identifier(this=v, quoted=False),
  table=Identifier(this='', quoted=True)), Column(
  this=Identifier(this=v, quoted=False)), Column(
  this=Identifier(this=m, quoted=False))]
[tool_use Bash] {"command": "sed -n 770,800p sqlglot/optimizer/scope.py; sed -n 830,850p sqlglot/optimizer/scope.py; sed -n 935,960p sqlglot/optimizer/scope.py", "description": "Read scope source-collection function around pivot handling"}
[tool_result]         expression.alias or isinstance(expression.this, exp.UNWRAPPED_QUERIES)
    )


def _is_from_or_join(expression: exp.Expr) -> bool:
    """
    Determine if `expression` is the FROM or JOIN clause of a SELECT statement.
    """
    parent = expression.parent

    # Subqueries can be arbitrarily nested
    while type(parent) is exp.Subquery:
        parent = parent.parent

    return type(parent) in (exp.From, exp.Join)


def _traverse_tables(scope: Scope) -> Iterator[Scope]:
    sources: 
…[1710 chars elided]…
stance(node, (exp.Subquery, exp.UDTF)):
                for key in ("joins", "laterals", "pivots"):
                    for arg in node.args.get(key) or []:
                        yield from walk_in_scope(arg)
            continue

        if prune and prune(node):
            continue

        for vs in reversed(node.args.values()):
            if isinstance(vs, list):
                for v in reversed(vs):
                    if isinstance(v, exp.Expr):
                        stack.append(v)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('SOURCES', {k_:(type(v).__name__, getattr(v,'expression',None) and type(v.expression).__name__) for k_,v in scope.sources.items()}, 'cols', resolver._get_all_sour
…[10 chars elided]…
())\n    return orig(scope,resolver,**k)\nqc._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: print(qualify(sqlglot.parse_one(q), dialect='').sql())\nexcept Exception as e: print(e)\n\" 2>&1 | tail -20", "description": "Debug full qualify sources and resolver columns per scope"}
[tool_result] SOURCES {'t': ('Table', None)} cols {'t': []}
SOURCES {'c': ('Scope', 'Select'), '': ('Scope', 'Select')} cols {'c': ['id', 'jan', 'feb']}
Ambiguous column 'id' (Line: 1, Col: 48)
[tool_use Bash] {"command": "grep -n \"_traverse_tables\\|scope.sources\\b\" sqlglot/optimizer/scope.py | head; grep -n \"def _get_all_source_columns\" -A20 sqlglot/optimizer/resolver.py | head -30", "description": "Find where scope sources are built and how resolver collects columns"}
[tool_result] 594:                if name in scope.sources:
595:                    scope_ref_count[id(scope.sources[name])] += 1
659:        yield from _traverse_tables(scope)
685:    yield from _traverse_tables(scope)
759:    scope.sources.update(sources)
787:def _traverse_tables(scope: Scope) -> Iterator[Scope]:
811:            if table_name in scope.sources and not expression.db:
817:                    sources[pivots[0].alias] = scope.sources[table_name]
819:                    sources[source_name] = sco
…[588 chars elided]…
elf, column_name: str, source_columns: dict[str, Sequence[str]] | None = None
218-    ) -> str | None:
219-        if not source_columns:
220-            # If not supplied, get all sources to calculate unambiguous columns
221-            if self._unambiguous_columns is None:
222-                self._unambiguous_columns = self._get_unambiguous_columns(
223-                    self._get_all_source_columns()
224-                )
225-
226-            unambiguous_columns = self._unambiguous_columns
[assistant] The stray `''` key comes from the pivot alias being empty at scope-build time; the CTE name `c` is already in `scope.sources`, so the two entries both expose the CTE's columns and collide. Keying the pivoted source by its alias, falling back to the table's own name, should avoid that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                    sources[pivots[0].alias] = scope.sources[table_name]", "new_string": "                    sources[pivots[0].alias or source_name] = scope.sources[table_name]"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM
…[6 chars elided]…
LECT * FROM c PIVOT(SUM(jan) FOR id IN (1, 2))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb','snowflake']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"", "description": "Re-verify qualify output after keying fix"}
[tool_result] bigquery ERR OptimizeError("Ambiguous column 'id'")
bigquery ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
bigquery ERR OptimizeError("Ambiguous column 'feb'")
bigquery ERR OptimizeError("Ambiguous column 'id'")
 ERR OptimizeError("Ambiguous column 'id'")
 ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
 ERR OptimizeError("Ambiguous column 'feb'")
 ERR OptimizeError("Ambiguous column 'id'")
duckdb ERR OptimizeError("Ambiguous column 'id'")
duckdb ERR OptimizeError("Ambiguous column 'id' (Line: 1, Col: 48)")
duckdb ERR OptimizeError("Ambiguous column 'feb'")
duckdb ERR OptimizeError("Ambiguous column 'id'")
snowflake ERR OptimizeError("Ambiguous column 'ID'")
snowflake ERR OptimizeError("Ambiguous column 'ID' (Line: 1, Col: 48)")
snowflake ERR OptimizeError("Ambiguous column 'FEB'")
snowflake ERR OptimizeError("Ambiguous column 'ID'")
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('SOURCES', {k_:(type(v).__name__, getattr(v,'expression',None) and type(v.expression).__name__) for k_,v in scope.sources.items()}, 'selected', list(scope.selecte
…[270 chars elided]…
nt(qualify(sqlglot.parse_one(q), dialect='').sql())\nexcept Exception as e: print(e)\n\" 2>&1 | tail -5; cd ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1 && sed -n 586,600p sqlglot/optimizer/scope.py; sed -n 745,760p sqlglot/optimizer/scope.py", "description": "Show scope sources, selected sources and resolver columns at qualify time"}
[tool_result] SOURCES {'t': ('Table', None)} selected ['t'] cols {'t': []}
SOURCES {'c': ('Scope', 'Select')} selected ['c'] cols {'c': ['id', 'jan', 'feb']}
Ambiguous column 'id' (Line: 1, Col: 48)

        for scope in self.traverse():
            for _, source in scope.selected_sources.values():
                scope_ref_count[id(source)] += 1

            for name in scope._semi_anti_join_tables:
                # semi/anti join sources are not actually selected but we still need to
                # incr
…[233 chars elided]…
.Expr) -> list[Scope]:
            scope.branch(
                cte.this,
                cte_sources=sources,
                outer_columns=cte.alias_column_names,
                scope_type=ScopeType.CTE,
            )
        ):
            yield child_scope

        # append the final child_scope yielded
        if child_scope:
            sources[cte_name] = child_scope
            scope.cte_scopes.append(child_scope)

    scope.sources.update(sources)
    scope.cte_sources.update(sources)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('GET id ->', repr(resolver.get_table('id')), 'unamb', resolver._get_unambiguous_columns(resolver._get_all_source_columns()))\n    print('scope cols', [(c.name, c.
…[115 chars elided]…
ope.columns])\n    return r\nqc._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: print(qualify(sqlglot.parse_one(q), dialect='').sql())\nexcept Exception as e: print(e)\n\" 2>&1 | tail -12", "description": "Check resolver.get_table result and columns before/after qualification"}
[tool_result] GET id -> Identifier(this=t, quoted=False) unamb <sqlglot.helper.SingleValuedMapping object at 0x1074b3aa0>
scope cols [('id', ''), ('jan', ''), ('feb', '')]
after [('id', 't'), ('jan', 't'), ('feb', 't')]
GET id -> Identifier(this=c, quoted=False) unamb <sqlglot.helper.SingleValuedMapping object at 0x1074b39b0>
scope cols [('id', ''), ('m', ''), ('v', ''), ('v', ''), ('m', ''), ('jan', ''), ('feb', '')]
after [('id', ''), ('m', ''), ('v', ''), ('v', ''), ('m', ''), ('jan', 'c'), ('feb', 'c')]
Ambiguous column 'id' (Line: 1, Col: 48)
[assistant] The pivot branch at `qualify_columns.py` (outer columns get the pivot alias as their table) runs before the pivot alias is filled in, so `id` is assigned `''`. Let me check when `qualify_tables` assigns pivot aliases and compare against the original code.
[tool_use Bash] {"command": "sed -n 120,180p sqlglot/optimizer/qualify_tables.py; rm -rf /tmp/orig_sg && mkdir -p /tmp/orig_sg && git archive HEAD sqlglot | tar -x -C /tmp/orig_sg && cd /tmp && PYTHONPATH=/tmp/orig_sg <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor q in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))']:\n  try: print(qualify(sqlglot.parse_one(q), dialect='').sql())\n  except Exception as e: print('ERR', e)\n\"", "description": "Read qualify_tables pivot aliasing and test original HEAD code"}
[tool_result ERROR] Exit code 1
            unnested = derived_table.unnest()
            if isinstance(unnested, exp.Table):
                joins = unnested.args.get("joins")
                unnested.set("joins", None)
                derived_table.this.replace(exp.select("*").from_(unnested.copy(), copy=False))
                derived_table.this.set("joins", joins)

            _set_alias(derived_table, canonical_aliases, scope=scope)
            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
  
…[1955 chars elided]…
cal_aliases, target_alias=target_alias, normalize=True)

                    # This case corresponds to a pivoted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('PIVOTS', [p.alias for p in scope.pivots], 'SRC', list(scope.sources))\n    return orig(scope,resolver,**k)\nqc._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: print(qualify(sqlglot.parse_one(q), dialect='').sql())\nexcept Exception as e: print(e)\n\" 2>&1 | tail -8; grep -n \"qualify_tables\\|qualify_columns(\" sqlglot/optimizer/qualify.py | head", "description": "Print pivot alias and sources at qualify_columns time"}
[tool_result] PIVOTS [] SRC ['t']
PIVOTS [''] SRC ['c']
Ambiguous column 'id' (Line: 1, Col: 48)
14:from sqlglot.optimizer.qualify_tables import qualify_tables
84:    expression = qualify_tables(
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=qualify_tables(sqlglot.parse_one(q))\nprint(e.sql()); p=e.find(sqlglot.exp.Pivot); print(repr(p.alias), p.parent.__class__.__name__, [ (type(x).__name__, x.alias) for x in [p.parent]])\n\"; sed -n 80,90p sqlglot/optimizer/qualify.py", "description": "Check whether qualify_tables assigns pivot alias for CTE source"}
[tool_result] WITH c AS (SELECT id, jan, feb FROM t AS t) SELECT id, m, v FROM c AS c UNPIVOT(v FOR m IN (jan, feb))
'' Table [('Table', 'c')]
        expression,
        dialect=dialect,
        store_original_column_identifiers=True,
    )
    expression = qualify_tables(
        expression,
        db=db,
        catalog=catalog,
        dialect=dialect,
        on_qualify=on_qualify,
        canonicalize_table_aliases=canonicalize_table_aliases,
[assistant] Found the real interaction: `qualify_tables` only aliases a pivoted source when it is a `Table` entry, and my scope change turned that entry into a `Scope`, so the pivot never got its alias. I'll revert the `scope.py` change and fix it in the resolver instead, where the pivoted CTE's columns are looked up.
[tool_use Bash] {"command": "git checkout -- sqlglot/optimizer/scope.py && git status --short && sed -n 133,205p sqlglot/optimizer/resolver.py && sed -n 1,20p sqlglot/optimizer/resolver.py | grep import", "description": "Revert scope change and read rest of get_source_columns"}
[tool_result]     def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._get_source_columns_cache:
            if name not in self.scope.sources:
                raise OptimizeError(f"Unknown table: {name}")

            source = self.scope.sources[name]

            if isinstance(source, exp.Table):
                columns = self.schema.
…[3304 chars elided]…
        ]

            self._get_source_columns_cache[cache_key] = columns

        return self._get_source_columns_cache[cache_key]

from __future__ import annotations
import itertools
import typing as t
from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.errors import OptimizeError
from sqlglot.helper import seq_get, SingleValuedMapping
from sqlglot.optimizer.scope import Scope
    from sqlglot.schema import Schema
    from collections.abc import Sequence, Mapping
[assistant] The harness says `scope.py` changed on disk since my last read. Let me check its current state before going further.
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff -- sqlglot/optimizer/scope.py | head -40; git log --oneline -1", "description": "Check git status and scope.py diff after revert"}
[tool_result] 34eb257be lithify: probe base
[assistant] The tree is clean and matches HEAD, so the `scope.py` change is gone as intended. Now the resolver fix: when a source is a pivoted `Table` that refers to a CTE, resolve its columns from the CTE scope.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            source = self.scope.sources[name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)", "new_string": "            source = self.scope.sources[name]\n\n            # A pivoted CTE reference is a Table whose columns are those of the CTE it refers to\n            if isinstance(source, exp.Table) and source.args.get(\"pivots\"):\n                source = self.scope.sources.get(source.name) or source\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM
…[20 chars elided]…
PIVOT(SUM(jan) FOR id IN (1, 2))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb','snowflake']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"", "description": "Verify qualify output with resolver fix across dialects"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`f
…[2431 chars elided]…
NPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT "_0"."FEB" AS "FEB", "_0"."1" AS "1", "_0"."2" AS "2" FROM "C" AS "C" PIVOT(SUM("C"."JAN") FOR "C"."ID" IN (1, 2)) AS "_0"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT "X"."ID" AS "ID", "X"."M" AS "M", "X"."V" AS "V" FROM "C" AS "X" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "X"
[assistant] Most of it now resolves. Remaining issue: in the default/BigQuery/Snowflake dialects the UNPIVOT's new names `v`/`m` still get the `c.` qualifier (DuckDB doesn't). Let me find which step sets that.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\nfrom sqlglot import exp\nprint([c.__name__ for c in exp.Column.__mro__][:4])\nbase=exp.Column.__mro__[1]\norig=base.set\ndef spy(self, k, v, *a, **kw):\n    if k=='table' and getattr(self,'name','') in ('v','m') and v is not None:\n        print('SET', self.name,
…[2 chars elided]…
->', v.name if hasattr(v,'name') else v); traceback.print_stack(limit=6)\n    return orig(self,k,v,*a,**kw)\nbase.set=spy\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(q), dialect='')\n\" 2>&1 | head -40", "description": "Trace which step assigns table to unpivot column v"}
[tool_result]   File "<string>", line 14, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 97, in qualify
    expression = qualify_columns_func(
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo
…[1975 chars elided]…
o-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 637, in _qualify_columns
    column.set("table", table)
  File "<string>", line 9, in spy
['Column', 'Expression', 'Condition', 'Expr']
SET m -> c
SET v -> c
SET v -> c
SET m -> c
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print('dialect', type(resolver.dialect).__name__, 'infer', resolver._infer_schema, 'srcs', resolver._get_all_source_columns(), 'selected', list(scope.selected_sources))
…[172 chars elided]…
._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\nfor d in ['', 'duckdb']:\n  print('==',d)\n  try: qualify(sqlglot.parse_one(q, read=d), dialect=d)\n  except Exception as e: print(e)\n\" 2>&1 | tail -20", "description": "Compare resolver state for default vs duckdb on pivot column"}
[tool_result] == 
dialect Dialect infer True srcs {'t': []} selected ['t']
get v t unamb {}
dialect Dialect infer True srcs {'c': []} selected ['c']
get v c unamb {}
== duckdb
dialect DuckDB infer True srcs {'t': []} selected ['t']
get v t unamb {}
dialect DuckDB infer True srcs {'c': []} selected ['c']
get v c unamb {}
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nimport sqlglot.optimizer.qualify_columns as qc\norig=qc._qualify_columns\ndef w(scope,resolver,**k):\n    print({k_:(type(v).__name__) for k_,v in scope.sources.items()}, {k_:type(v).__name__ for k_,v in scope.selected_sources.items()})\n    print([ (type(t).__name__, t.nam
…[84 chars elided]…
pe(t).__name__) for t in scope.derived_tables])\n    return orig(scope,resolver,**k)\nqc._qualify_columns=w\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(q, read=''), dialect='')\n\" 2>&1 | tail -6", "description": "Inspect scope source types for the pivoted CTE reference"}
[tool_result] {'t': 'Table'} {'t': 'tuple'}
[('Table', 't', None)] []
{'c': 'Table'} {'c': 'tuple'}
[('Table', 'c', 'c')] []
[assistant] The outer scope's `sources['c']` has been overwritten by the pivoted `Table`, so the CTE scope is only reachable via `cte_sources`. Let me confirm that and switch the lookup.
[tool_use Bash] {"command": "grep -n \"cte_sources\" sqlglot/optimizer/scope.py | head; sed -i 's/                source = self.scope.sources.get(source.name) or source/                source = self.scope.cte_sources.get(source.name) or source/' sqlglot/optimizer/resolver.py && git diff && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot
…[272 chars elided]…
 * FROM c PIVOT(SUM(jan) FOR id IN (1, 2))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"", "description": "Switch lookup to cte_sources and re-verify qualify output"}
[tool_result ERROR] Exit code 1
48:        cte_sources: Sources from CTES
92:        cte_sources: dict[str, exp.Table | Scope] | None = None,
98:        self.cte_sources = cte_sources or {}
100:        self.sources.update(self.cte_sources)
138:        cte_sources: dict[str, exp.Table | Scope] | None = None,
148:            cte_sources={**self.cte_sources, **(cte_sources or {})},
667:            yield from _traverse_scope(Scope(ddl_expression, cte_sources=scope.cte_sources))
674:                yield from _traverse_scope(Scope(query, cte_sources=scope.cte_sources))
747:                cte_sources=sources,
760:    scope.cte_sources.update(sources)
sed: 1: "sqlglot/optimizer/resol ...": unterminated substitute pattern
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "                source = self.scope.sources.get(source.name) or source", "new_string": "                source = self.scope.cte_sources.get(source.name) or source"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nqs=['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM
…[2 chars elided]…
) SELECT * FROM c PIVOT(SUM(jan) FOR id IN (1, 2))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))']\nfor d in ['bigquery','','duckdb']:\n  for q in qs:\n    try: print(d, qualify(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n    except Exception as e: print(d,'ERR',repr(e))\n\"", "description": "Re-verify qualify output using cte_sources lookup"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery WITH `c` AS (SELECT `t`.`id` AS `
…[1687 chars elided]…
M "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "_0"."feb" AS "feb", "_0"."1" AS "1", "_0"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "id" IN (1, 2)) AS "_0"
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "x"."id" AS "id", "x"."m" AS "m", "x"."v" AS "v" FROM "c" AS "x" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "x"
[assistant] The output is now right: the UNPIVOT's new names `v`/`m` stay unqualified, the `IN (...)` items resolve to the CTE, and `SELECT *` expands. Next, the full test suite, plus a HEAD comparison for the PIVOT case to make sure I haven't changed it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -30; cd /tmp && PYTHONPATH=/tmp/orig_sg <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nprint(sqlglot.__file__)\nprint(qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR id IN (1, 2))', read='duckdb'), dialect='duckdb').sql('duckdb'))\n\" 2>&1 | tail -3", "description": "Run full test suite and compare PIVOT output against HEAD"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
....................................................................................................................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
.........
…[672 chars elided]…
................                                                    [100%]
1092 passed, 17865 subtests passed in 57.29s
/tmp/orig_sg/sqlglot/__init__.py
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "_0"."feb" AS "feb", "_0"."1" AS "1", "_0"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "id" IN (1, 2)) AS "_0"
Shell cwd was reset to ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1
[assistant] The full suite still passes (1092). The one visible side effect is on PIVOT over a CTE: the source columns now get qualified (`SUM("c"."jan")`), where HEAD left them bare. That's valid SQL and matches the table-source behaviour, but I'll flag it. Now let me find the existing UNPIVOT tests to add a regression case next to them.
[tool_use Bash] {"command": "grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql tests/test_optimizer.py | head -30", "description": "Find existing UNPIVOT test cases"}
[tool_result] tests/fixtures/optimizer/optimizer.sql:696:# title: unpivoted table source with a single value column, unpivot columns can't be qualified
tests/fixtures/optimizer/optimizer.sql:699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
tests/fixtures/optimizer/optimizer.sql:706:UNPIVOT("SALES" FOR "MONTH" IN ("JAN", "FEB")) AS "M_SALES"
tests/fixtures/optimizer/optimizer.sql:710:# title: unpivoted table source, unpivot has column aliases
te
…[1053 chars elided]…
N (`produce`.`q1`, `produce`.`q2`, `produce`.`q3`, `produce`.`q4`)) AS `produce`;
tests/fixtures/optimizer/optimizer.sql:761:# title: unpivoted table source with multiple value columns
tests/fixtures/optimizer/optimizer.sql:764:SELECT * FROM produce AS produce(product, q1, q2, q3, q4) UNPIVOT((first_half_sales, second_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'));
tests/fixtures/optimizer/optimizer.sql:771:UNPIVOT((`first_half_sales`, `second_half_sales`) FOR
[tool_use Bash] {"command": "sed -n 690,800p tests/fixtures/optimizer/optimizer.sql; grep -n \"optimizer.sql\\|def test_qualify_columns\\|def test_qualify\" tests/test_optimizer.py | head", "description": "Read existing UNPIVOT fixture block and test runner hooks"}
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
…[3015 chars elided]…
tions
# execute: false
SELECT "foO".x FROM (SELECT 1 AS x) AS "foO";
WITH "foO" AS (
  SELECT
    1 AS "x"
)
SELECT
  "foO"."x" AS "x"
FROM "foO" AS "foO";

# title: lateral subquery
248:    def test_qualify_tables(self):
309:    def test_qualify_tables_copies_typed_alias_columns(self):
341:    def test_qualify_columns(self, logger):
693:    def test_qualify_columns__with_invisible(self):
703:    def test_qualify_columns__invalid(self):
2109:    def test_qualify_group_by_conflict_bigquery(self):
[assistant] I'll add a regression fixture next to the existing UNPIVOT cases, using the exact query from the report in BigQuery, and check the expected output by running it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "old_string": ") AS `produce`;\n\n# title: quoting is preserved", "new_string": ") AS `produce`;\n\n# title: unpivoted cte source, unpivot columns can't be qualified but the cte's columns can\n# execute: false\n# dialect: bigquery\nWITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));\nWITH `c` AS (\n  SELECT\n    `t`.`id` AS `id`,\n    `t`.`jan` AS `jan`,\n    `t`.`feb` AS `feb`\n  FROM `t` AS `t`\n)\nSELECT\n  `c`.`id` AS `id`,\n  `c`.`m` AS `m`,\n  `c`.`v` AS `v`\nFROM `c` AS `c`\nUNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`;\n\n# title: quoting is preserved"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py tests/dialects 2>&1 | tail -30", "description": "Run optimizer and dialect tests including new fixture"}
[tool_result]         for future in as_completed(results):
            sql, title, expected, dialect, execute = results[future]
    
            with self.subTest(title):
                optimized = future.result()
                actual = optimized.sql(pretty=pretty, dialect=dialect)
>               self.assertEqual(
                    expected,
                    actual,
                )
E               AssertionError: 'WITH `c` AS (\n  SELECT\n    `t`.`id` AS [210 chars] `c`' != 'SELECT\n  `c`.`id` AS `
…[339 chars elided]…
                `c`.`m` AS `m`,
E                   `c`.`v` AS `v`
E                 FROM `c` AS `c`
E                 UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[unpivoted cte source, unpivot columns can't be qualified but the cte's columns can] tests/test_optimizer.py::TestOptimizer::test_optimize
1 failed, 802 passed, 14703 subtests passed in 20.97s
[assistant] The fixture's expected text was a guess; the full optimizer also runs CTE elimination. Let me look at the real optimized output before deciding what to record.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nprint(optimize(sqlglot.parse_one(q, read='bigquery'), dialect='bigquery').sql('bigquery', pretty=True))\n\"; PYTHONPATH=/tmp/orig_sg <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nprint(optimize(sqlglot.parse_one(q, read='bigquery'), dialect='bigquery').sql('bigquery', pretty=True))\n\"", "description": "Compare full optimize output before and after the fix"}
[tool_result] SELECT
  `c`.`id` AS `id`,
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
SELECT
  `c`.`id` AS `id`,
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[assistant] The full optimizer output is identical before and after my change, and it has a dangling reference: `FROM c` with the CTE removed. That's a separate pre-existing bug in a later rule, so let me find which rule drops the CTE.
[tool_use Bash] {"command": "grep -n \"RULES = \\|^    [a-z_]*,$\" sqlglot/optimizer/optimizer.py | head -40; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=sqlglot.parse_one(q, read='bigquery')\nfor rule in RULES:\n    e=rule(e, dialect='bigquery') if rule.__name__!='qualify' else e\n    print(rule.__name__, '|', e.sql('bigquery').replace(chr(10),' ')[:230])\n\" 2>&1 | head -40", "description": "Step through optimizer rules to find where the CTE is dropped"}
[tool_result] 41:    qualify,
42:    pushdown_projections,
43:    normalize,
44:    unnest_subqueries,
45:    pushdown_predicates,
46:    optimize_joins,
47:    eliminate_subqueries,
48:    merge_subqueries,
49:    eliminate_joins,
50:    eliminate_ctes,
51:    quote_identifiers,
52:    annotate_types,
53:    canonicalize,
54:    simplify,
Traceback (most recent call last):
  File "<string>", line 8, in <module>
TypeError: normalize() got an unexpected keyword argument 'dialect'
qualify | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
pushdown_projections | WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot, inspect\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.qualify import qualify\nq='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=sqlglot.parse_one(q, read='bigquery')\nfor rule in RULES:\n    kw={'dialect':'bigquery'} if 'dialect' in inspect.signature(rule).parameters else {}\n    e=rule(e, **kw)\n    print(rule.__name__, '|', e.sql('bigquery').replace(chr(10),' ')[:260])\n\" 2>&1 | head -40", "description": "Run each optimizer rule and print intermediate SQL"}
[tool_result] qualify | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
pushdown_projections | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
normalize | WITH `c` AS (SE
…[1853 chars elided]…
v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
annotate_types | SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
canonicalize | SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
simplify | SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[assistant] The CTE is dropped by `eliminate_ctes`: the outer scope references it only through the pivoted `Table`, so the CTE's reference count is 0. Let me look at how reference counts are computed.
[tool_use Bash] {"command": "sed -n 572,600p sqlglot/optimizer/scope.py; grep -n \"ref_count\" sqlglot/optimizer/eliminate_ctes.py sqlglot/optimizer/*.py | head", "description": "Read scope reference counting and eliminate_ctes usage"}
[tool_result]                     scope.subquery_scopes,
                )
            )

        yield from reversed(result)

    def ref_count(self) -> dict[int, int]:
        """
        Count the number of times each scope in this tree is referenced.

        Returns:
            dict[int, int]: Mapping of Scope instance ID to reference count
        """
        scope_ref_count: dict[int, int] = defaultdict(int)

        for scope in self.traverse():
            for _, source in scope.selected_sources.val
…[918 chars elided]…
_ctes.py:51:                            ref_count[id(source)] -= 1
sqlglot/optimizer/pushdown_predicates.py:41:        scope_ref_count = root.ref_count()
sqlglot/optimizer/pushdown_predicates.py:66:                    pushdown(where.this, selected_sources, scope_ref_count, dialect, join_index)
sqlglot/optimizer/pushdown_predicates.py:76:                        scope_ref_count,
sqlglot/optimizer/pushdown_predicates.py:83:def pushdown(condition, sources, scope_ref_count, dialect, join_index=None):
[tool_use Bash] {"command": "sed -n 25,60p sqlglot/optimizer/eliminate_ctes.py", "description": "Read eliminate_ctes decrement logic"}
[tool_result]     Returns:
        sqlglot.Expr: optimized expression
    """
    root = build_scope(expression)

    if root:
        ref_count = root.ref_count()

        # Traverse the scope tree in reverse so we can remove chains of unused CTEs
        for scope in reversed(list(root.traverse())):
            if scope.is_cte:
                count = ref_count[id(scope)]
                if count <= 0:
                    cte_node = scope.expression.parent
                    if not cte_node:
              
…[72 chars elided]…
               cte_node.pop()

                    # Pop the entire WITH clause if this is the last CTE
                    if with_node and len(with_node.expressions) <= 0:
                        with_node.pop()

                    # Decrement the ref count for all sources this CTE selects from
                    for _, source in scope.selected_sources.values():
                        if isinstance(source, Scope):
                            ref_count[id(source)] -= 1

    return expression
[assistant] `ref_count` keys each selected source by the object it finds, and for a pivoted CTE that's the `Table`, not the CTE's scope. I'll map it back to the CTE scope, the same way the resolver does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "            for _, source in scope.selected_sources.values():\n                scope_ref_count[id(source)] += 1", "new_string": "            for _, source in scope.selected_sources.values():\n                # A pivoted CTE reference is a Table, but it still references the CTE's scope\n                if isinstance(source, exp.Table) and source.args.get(\"pivots\"):\n                    source = scope.cte_sources.get(source.name) or source\n                scope_ref_count[id(source)] += 1"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfor q in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT id, m, v FROM c UNPIVOT(v FOR m IN (jan, feb))']:\n  for d in ['bigquery','duckdb']:\n    print(optimize(sqlglot.parse_one(q, read=d), dialect=d).sql(d, pretty=True)); print('--')\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Verify full optimize output and run full test suite"}
[tool_result] WITH `c` AS (
  SELECT
    `t`.`id` AS `id`,
    `t`.`jan` AS `jan`,
    `t`.`feb` AS `feb`
  FROM `t` AS `t`
)
SELECT
  `c`.`id` AS `id`,
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
--
WITH "c" AS (
  SELECT
    "t"."id" AS "id",
    "t"."jan" AS "jan",
    "t"."feb" AS "feb"
  FROM "t" AS "t"
)
SELECT
  "c"."id" AS "id",
  "c"."m" AS "m",
  "c"."v" AS "v"
FROM "c" AS "c"
UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
--
WITH `c` AS (

…[1262 chars elided]…
 [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                   [100%]
1092 passed, 17866 subtests passed in 50.62s
[assistant] The full optimizer now keeps the CTE and qualifies correctly, and the suite passes (1092 tests, plus the new fixture subtest). Last, lint the changed files and spot-check a few more dialects and the PIVOT case through the full optimizer.
[tool_use Bash] {"command": "( <work>/env-sqlglot/bin/ruff --version && <work>/env-sqlglot/bin/ruff check sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py ) 2>&1 | tail -5; 
…[165 chars elided]…
('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','snowflake'),('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR id IN (1, 2))','duckdb')]:\n    print(optimize(sqlglot.parse_one(q, read=d), dialect=d).sql(d))\n\"; git status --short; git diff --stat", "description": "Lint changed files and spot-check other dialects through optimize"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT "C"."ID" AS "ID", "C"."M" AS "M", "C"."V" AS "V" FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "_0"."feb" AS "feb", "_0"."1" AS "1", "_0"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "id" IN (1, 2)) AS "_0"
 M sqlglot/optimizer/resolver.py
 M sqlglot/optimizer/scope.py
 M tests/fixtures/optimizer/optimizer.sql
 sqlglot/optimizer/resolver.py          |  4 ++++
 sqlglot/optimizer/scope.py             |  3 +++
 tests/fixtures/optimizer/optimizer.sql | 18 ++++++++++++++++++
 3 files changed, 25 insertions(+)
[tool_use Bash] {"command": "rm -rf /tmp/orig_sg && cd ~/.cache/lithify/work/repo-d5521a213087/20261028-171257-optimizer-select-from-cte-unpivo/base-1 && git diff", "description": "Remove temp copy and show final diff"}
[tool_result] diff --git a/sqlglot/optimizer/resolver.py b/sqlglot/optimizer/resolver.py
index 1868c662f..0d3544b88 100644
--- a/sqlglot/optimizer/resolver.py
+++ b/sqlglot/optimizer/resolver.py
@@ -139,6 +139,10 @@ class Resolver:
 
             source = self.scope.sources[name]
 
+            # A pivoted CTE reference is a Table whose columns are those of the CTE it refers to
+            if isinstance(source, exp.Table) and source.args.get("pivots"):
+                source = self.scope.cte_sources.get(sou
…[1277 chars elided]…
# execute: false
+# dialect: bigquery
+WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));
+WITH `c` AS (
+  SELECT
+    `t`.`id` AS `id`,
+    `t`.`jan` AS `jan`,
+    `t`.`feb` AS `feb`
+  FROM `t` AS `t`
+)
+SELECT
+  `c`.`id` AS `id`,
+  `c`.`m` AS `m`,
+  `c`.`v` AS `v`
+FROM `c` AS `c`
+UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`;
+
 # title: quoting is preserved
 # dialect: snowflake
 with cte1("id", foo) as (select 1, 2) select "id" from cte1;
[assistant] `SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))` now qualifies correctly over a CTE. The `v` and `m` names stay unqualified, the `IN (...)` items resolve to the CTE's columns, and the CTE is no longer dropped. The full suite passes (1092 tests, plus the new fixture subtest) and ruff is clean. I haven't committed anything.

There were three separate causes:

- **Resolver (`sqlglot/optimizer/resolver.py`)**: a pivoted CTE reference is a bare `Table`, so the resolver had no column list for it. It fell back to inference and assigned `v`/`m` to the CTE. It now looks up the CTE's columns through `ct
…[531 chars elided]…
h there is correct once the resolver knows the CTE's columns.

One side effect to review: PIVOT over a CTE now qualifies its source columns at the qualify stage (`SUM("c"."jan")` where HEAD left `SUM("jan")`). The full optimizer output for that case is unchanged and no test covers it, so I didn't add one. Table-sourced PIVOTs already behave this way.

Not covered: `eliminate_ctes` only decrements counts for `Scope` sources, so a CTE that is itself dropped and pivots another CTE leaves that inner CTE in place. The result is an unused CTE, not wrong SQL. I left it alone to keep the change small.
