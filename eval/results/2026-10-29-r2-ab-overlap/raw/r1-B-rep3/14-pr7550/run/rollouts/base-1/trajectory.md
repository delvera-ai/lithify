# trajectory base-1

final message:
The `UNPIVOT` over a CTE now qualifies correctly, and the full suite passes (1092 tests). I haven't committed.

**Root cause:** A pivoted CTE reference (`FROM c UNPIVOT(...)`) becomes a new `Table` source in scope, not the CTE's `Scope`. The resolver then asked the schema for `c`'s columns, got none, and so could not resolve the `IN (...)` items. The schema-less path only worked because it fell back to attaching everything to the pivot alias.

**Fix:** In `sqlglot/optimizer/resolver.py` (`get_source_columns`), a pivoted reference whose name is a CTE in `scope.cte_sources` now takes its columns from that CTE. Output is now:

```sql
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`)
SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v`
FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
```

The `v` and `m` names stay unqualified inside the `UNPIVOT` clause, and only the `IN` items reference source columns. Before the fix, the same query with a schema raised `OptimizeError: Ambiguous column 'jan'`. `SELECT *` now expands to `id, m, v` as it already does for plain tables, instead of staying `*`.

**Test:** I added an assertion for this query to `test_qualify_columns` in `tests/test_optimizer.py`. I did not weaken any existing test.

**Not covered:** If the CTE has a column with the same name as an unpivot output (for example `v`), the existing pivot loop in `qualify_columns.py` may still qualify that output name. The plain-table path has the same behavior, so I left it alone.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor d in ['bigquery','duckdb','snowflake']:\n    sql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\n    try:\n        print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d).sql(d))\n    except Exception as e: print(d, 'ERR', type(e).__name__, e)\n\"; grep -n \"Pivot\\|unpivot\" sqlglot/optimizer/*.py | head -60"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("
…[1005 chars elided]…
glot/optimizer/qualify_columns.py:791:if isinstance(pivot, exp.Pivot) and not pivot.alias_column_names:
sqlglot/optimizer/qualify_columns.py:792:if pivot.unpivot:
sqlglot/optimizer/qualify_columns.py:793:pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/optimizer/qualify_tables.py:170:target_alias = source.alias if pivot.unpivot else None
sqlglot/optimizer/scope.py:81:_pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:477:def pivots(self) -> list[exp.Pivot]:
[tool_use Bash] {"command": "sed -n 125,200p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 600,640p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 780,800p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 160,180p sqlglot/optimizer/qualify_tables.py"}
[tool_result]                 column = scope.external_columns[0]
                for_table = f" for table: '{column.table}'" if column.table else ""
                line = column.this.meta.get("line")
                col = column.this.meta.get("col")
                start = column.this.meta.get("start")
                end = column.this.meta.get("end")

                error_msg = f"Column '{column.name}' could not be resolved{for_table}."
                if line and col:
                    error_msg += f" L
…[5335 chars elided]…
:
                    target_alias = source.alias if pivot.unpivot else None
                    _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)

                    # This case corresponds to a pivoted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases=[('bigquery','SELECT * FROM t UNPIVOT(v FOR m IN (jan, feb))'),\n('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'),\n('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT id, v FROM
…[152 chars elided]…
TH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan AS x, feb))'),\n]\nfor d,sql in cases:\n    try:\n        print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d).sql(d))\n    except Exception as e: print(d, 'ERR', type(e).__name__, e)\n\"; ls tests/fixtures/optimizer/ | grep -i qualif; grep -n -i \"unpivot\" tests/fixtures/optimizer/qualify_columns.sql | head -30"}
[tool_result] bigquery SELECT * FROM `t` AS `t` UNPIVOT(`t`.`v` FOR `t`.`m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) 
…[17 chars elided]…
H "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan" AS "x", "feb")) AS "c"
qualify_columns.sql  49.8K
qualify_columns__invalid.sql  751B
qualify_columns__with_invisible.sql  1.1K
qualify_columns_ddl.sql  2.3K
qualify_tables.sql  12.4K
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.optimizer import optimize\nfor d,sql in [('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'),('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT id, v FROM c UNPIVO
…[140 chars elided]…
validate_qualify_columns=True), lambda e: optimize(e, dialect=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}})]:\n    try: print(f(sqlglot.parse_one(sql,read=d)).sql(d))\n    except Exception as e: print('ERR', type(e).__name__, e)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -3"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 82)
SELECT `t`.`id` AS `id`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`t`.`v` FOR `t`.`m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT `t`.`id` AS `id`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
.................................................................... [ 96%]
...                                   [100%]
77 passed, 3705 subtests passed in 12.57s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(sql,read='bigquery'), dialect='bigquery', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}})\n\" 2>&1 | tail -25"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
    validate_qualify_columns_func(expression, sql=sql)
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 164, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Ambiguous column 'jan' (Line: 1, Col: 78)
[tool_use Bash] {"command": "sed -n 60,124p sqlglot/optimizer/qualify_columns.py; sed -n 800,850p sqlglot/optimizer/qualify_columns.py"}
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
…[3490 chars elided]…
                  if struct_fields:
                        new_selections.extend(struct_fields)
                        continue
                elif dialect.REQUIRES_PARENTHESIZED_STRUCT_ACCESS:
                    struct_fields = _expand_struct_stars_with_parens(expression)
                    if struct_fields:
                        new_selections.extend(struct_fields)
                        continue

        if not tables:
            new_selections.append(expression)
            continue
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor sql in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT id, v FROM c UNPIVOT(v FOR m IN (jan, feb))','SELECT * FROM t UNPIVOT(v FOR m IN (jan, feb))']:\n  e=qualify(sqlglot.parse_one(sql,read='bigquery'), dialect='bigquery', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=False)\n  print(e.sql('bigquery'))\n\""}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`)) AS `c`
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
[tool_use Bash] {"command": "grep -n \"def get_table\\|def _get_table_name_from_sources\\|def get_source_columns\\|def _get_all_source_columns\\|def _get_unambiguous\\|def all_columns\" sqlglot/optimizer/qualify_columns.py; sed -n 640,660p sqlglot/optimizer/qualify_columns.py"}
[tool_result] 0 matches for 'def get_table\|def _get_table_name_from_sources\|def get_source_columns\|def _get_all_source_columns\|def _get_unambiguous\|def all_columns'
                and len(column.parts) == 1
                and column_name in scope.selected_sources
            ):
                # BigQuery and Postgres allow tables to be referenced as columns, treating them as structs/records
                scope.replace(column, exp.TableColumn(this=column.this))

    for pivot in scope.pivots:
        
…[40 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"all_columns\\|def get_table\" sqlglot/optimizer/resolver.py | head; grep -n \"def all_columns\" -A 25 sqlglot/optimizer/resolver.py"}
[tool_result] 9 matches in 5 files:

30:0:set[str] | None = None
34:0:str | exp.Column) -> exp.Identifier | None:
87:0:
89:0:
sqlglot/optimizer/resolver.py:90:self._all_columns = {
sqlglot/optimizer/resolver.py:93:return self._all_columns
sqlglot/optimizer/resolver.py:324:all_columns = set(unambiguous_columns)
sqlglot/optimizer/resolver.py:328:ambiguous = all_columns.intersection(unique)
87:    def all_columns(self) -> set[str]:
88-        """All available columns of all sources in this scope"""
89-        if
…[766 chars elided]…
          raise OptimizeError(f"Unknown set operation: {expression}")
103-
104-        set_op = expression
105-
106-        # BigQuery specific set operations modifiers, e.g INNER UNION ALL BY NAME
107-        on_column_list = set_op.args.get("on")
108-
109-        if on_column_list:
110-            # The resulting columns are the columns in the ON clause:
111-            # {INNER | LEFT | FULL} UNION ALL BY NAME ON (col1, col2, ...)
112-            columns = [col.name for col in on_column_list]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.optimizer.normalize_identifiers import normalize_identifiers\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify import qualify\nfrom s
…[193 chars elided]…
mport Dialect\ns=ensure_schema({'t':{'id':'INT','jan':'INT','feb':'INT'}}, dialect='bigquery')\ne=qualify_tables(e, db=None, catalog=None, dialect='bigquery')\nfor sc in traverse_scope(e):\n  r=Resolver(sc, s, infer_schema=True)\n  print(type(sc.expression).__name__, sc.sources.keys(), r.all_columns, r._get_all_source_columns())\n  print(' get_table jan:', r.get_table('jan'))\n\" 2>&1 | tail -12"}
[tool_result] Select dict_keys(['t']) {'jan', 'feb', 'id'} {'t': ['id', 'jan', 'feb']}
 get_table jan: t
Select dict_keys(['c']) set() {'c': []}
 get_table jan: c
[tool_use Bash] {"command": "grep -n \"pivot\" -i sqlglot/optimizer/resolver.py; grep -n \"def get_source_columns\" -A 40 sqlglot/optimizer/resolver.py | head -60"}
[tool_result] 239:        if not joins or args.get("laterals") or args.get("pivots"):
241:            # (e.g laterals, pivots) exist alongside joins
95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
96-        if isinstance(expression, exp.Select):
97-            return expression.named_selects
98-        if isinstance(expression, exp.Subquery) and isinstance(expression.this, exp.SetOperation):
99-            # Different types of SET modifiers can be chained together if they'
…[2348 chars elided]…
     # in bigquery, unnest structs are automatically scoped as tables, so you can
150-                # directly select a struct field in a query.
151-                # this handles the case where the unnest is statically defined.
152-                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):
153-                    if not source_expr.type or source_expr.type.is_type(exp.DType.UNKNOWN):
154-                        unnest_expr = seq_get(source_expr.expressions, 0)
[tool_use Bash] {"command": "sed -n 155,185p sqlglot/optimizer/resolver.py"}
[tool_result]                         if isinstance(unnest_expr, exp.Column) and self.scope.parent:
                            col_type = self._get_unnest_column_type(unnest_expr, self.scope.parent)
                            if col_type and col_type.is_type(exp.DType.ARRAY):
                                element_types = col_type.expressions
                                if element_types:
                                    source_expr.type = element_types[0].copy()
                            elif col_
…[811 chars elided]…
lectable = source.expression.assert_is(exp.Selectable)
                select = seq_get(selectable.selects, 0)

                if isinstance(select, exp.QueryTransform):
                    # https://spark.apache.org/docs/3.5.1/sql-ref-syntax-qry-select-transform.html
                    schema = select.args.get("schema")
                    columns = [c.name for c in schema.expressions] if schema else ["key", "value"]
                else:
                    columns = selectable.named_selects
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\ne=sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',read='bigquery')\ne=qualify_tables(e, dialect='bigquery')\nfor sc in traverse_scope(e):\n  print({k:type(v).__name__ for k,v in sc.sources.items()})\n\"; grep -n \"def _traverse_tables\" -A 60 sqlglot/optimizer/scope.py | grep -n \"pivot\\|cte\\|sources\\[\" "}
[tool_result] {'t': 'Table'}
{'c': 'Table'}
27:813-                # it is pivoted, because then we get back a new table and hence a new source.
28:814-                pivots = expression.args.get("pivots")
29:815-                if pivots:
30:816-                    sources[pivots[0].alias] = expression
32:818-                    sources[source_name] = scope.sources[table_name]
34:820-                sources[find_new_name(sources, table_name)] = expression
36:822-                sources[source_name] = expression
[tool_use Bash] {"command": "sed -n 790,830p sqlglot/optimizer/scope.py; git log --oneline -3 -L 805,822:sqlglot/optimizer/scope.py | head -5"}
[tool_result]     # Traverse FROMs, JOINs, and LATERALs in the order they are defined
    expressions: list[exp.Expr] = []
    from_ = scope.expression.args.get("from_")
    if from_:
        expressions.append(from_.this)

    for join in scope.expression.args.get("joins") or []:
        expressions.append(join.this)

    if isinstance(scope.expression, exp.Table):
        expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressi
…[889 chars elided]…
 = expression

            # Make sure to not include the joins twice
            if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
10b233e1e Fix(clickhouse): traverse_scope with FINAL modifier (#4263)

diff --git a/sqlglot/optimizer/scope.py b/sqlglot/optimizer/scope.py
index 0bd7ab26f..6612f6102 100644
--- a/sqlglot/optimizer/scope.py
[tool_use Bash] {"command": "grep -n \"cte_sources\" sqlglot/optimizer/*.py | head -20; grep -n \"def column_names\" -A 12 sqlglot/schema.py | head -30"}
[tool_result] 10 matches in 1 files:

sqlglot/optimizer/scope.py:48:cte_sources: Sources from CTES
sqlglot/optimizer/scope.py:92:cte_sources: dict[str, exp.Table | Scope] | None = None,
sqlglot/optimizer/scope.py:98:self.cte_sources = cte_sources or {}
sqlglot/optimizer/scope.py:100:self.sources.update(self.cte_sources)
sqlglot/optimizer/scope.py:138:cte_sources: dict[str, exp.Table | Scope] | None = None,
sqlglot/optimizer/scope.py:148:cte_sources={**self.cte_sources, **(cte_sources or {})},
sqlglot/optimize
…[688 chars elided]…
    only_visible: whether to include invisible columns.
--
411:    def column_names(
412-        self,
413-        table: exp.Table | str,
414-        only_visible: bool = False,
415-        dialect: DialectType = None,
416-        normalize: bool | None = None,
417-    ) -> list[str]:
418-        normalized_table = self._normalize_table(table, dialect=dialect, normalize=normalize)
419-
420-        schema = self.find(normalized_table)
421-        if schema is None:
422-            return []
423-
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/optimizer/resolver.py | grep -n \"import\"; grep -n \"def named_selects\" -A 3 sqlglot/expressions.py | head -20"}
[tool_result] 1:from __future__ import annotations
3:import itertools
4:import typing as t
6:from sqlglot import exp
7:from sqlglot.dialects.dialect import Dialect
8:from sqlglot.errors import OptimizeError
9:from sqlglot.helper import seq_get, SingleValuedMapping
10:from sqlglot.optimizer.scope import Scope
13:    from sqlglot.schema import Schema
14:    from collections.abc import Sequence, Mapping
grep: sqlglot/expressions.py: No such file or directory
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)\n            elif", "new_string": "            if isinstance(source, exp.Table):\n     
…[52 chars elided]…
ame)\n                if source.args.get(\"pivots\") and isinstance(cte, Scope) and not source.db:\n                    # A pivoted CTE reference is a new source, but its columns come from the CTE\n                    columns = self.get_source_columns_from_set_op(cte.expression)\n                else:\n                    columns = self.schema.column_names(source, only_visible)\n            elif"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.optimize_joins import *\ns={'t':{'id':'INT','jan':'INT','feb':'INT'}}\nfor d,sql in [('bigquery','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'),('bigquery','WITH c AS (SELECT id,
…[219 chars elided]…
 feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))')]:\n  for sch in [s, None]:\n    try: print(qualify(sqlglot.parse_one(sql,read=d), dialect=d, schema=sch).sql(d))\n    except Exception as e: print('ERR', type(e).__name__, e)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -3"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t
…[888 chars elided]…
c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
.................................................................... [ 96%]
...                                   [100%]
77 passed, 3705 subtests passed in 12.10s
[tool_use Bash] {"command": "grep -n -i -B2 -A3 \"unpivot\" tests/fixtures/optimizer/qualify_columns.sql | head -80; grep -n -i \"unpivot\" tests/test_optimizer.py | head"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln -i \"unpivot\" tests/ | head; grep -rn -i \"unpivot\" tests/dialects/test_bigquery.py | head -5"}
[tool_result] tests/dialects/test_snowflake.py
tests/dialects/test_databricks.py
tests/dialects/test_bigquery.py
tests/dialects/test_redshift.py
tests/dialects/test_oracle.py
tests/dialects/test_duckdb.py
tests/dialects/test_pipe_syntax.py
tests/test_transpile.py
tests/fixtures/identity.sql
tests/fixtures/optimizer/optimizer.sql
tests/dialects/test_bigquery.py:198:        self.validate_identity("SELECT * FROM q UNPIVOT(values FOR quarter IN (b, c))")
tests/dialects/test_bigquery.py:264:            "SELECT * F
…[160 chars elided]…
es, second_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'))",
tests/dialects/test_bigquery.py:653:                "spark": "SELECT * FROM Produce UNPIVOT((first_half_sales, second_half_sales) FOR semesters IN ((Q1, Q2) AS semester_1, (Q3, Q4) AS semester_2))",
tests/dialects/test_bigquery.py:656:                "bigquery": "SELECT * FROM Produce UNPIVOT((first_half_sales, second_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'))",
[tool_use Bash] {"command": "grep -n -i -B3 -A3 \"unpivot\" tests/fixtures/optimizer/optimizer.sql | head -60; grep -n \"def test_qualify_columns\\b\" -A 12 tests/test_optimizer.py | head -30"}
[tool_result] 693-FROM "SOURCE" AS "SOURCE"
694-PIVOT(MAX("SOURCE"."VALUE") FOR "SOURCE"."KEY" IN ('a', 'b', 'c')) AS "FINAL"("ID", "TIMESTAMP_1", "TIMESTAMP_2", "COL_1", "COL_2", "COL_3");
695-
696:# title: unpivoted table source with a single value column, unpivot columns can't be qualified
697-# execute: false
698-# dialect: snowflake
699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
700-SELECT
701-  "M_SALES"."EMPID" AS "EMPID",
702-  "M_SAL
…[2205 chars elided]…
s(self, logger):
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
352-                    read="bigquery",
353-                ),
[tool_use Bash] {"command": "sed -n 353,380p tests/test_optimizer.py; grep -n \"    def test_\" tests/test_optimizer.py | awk -F: '$1>340 && $1<460'"}
[tool_result]                 ),
                schema={
                    "raw": {
                        "TeamMemberships": {
                            "Id": "INTEGER",
                            "UserId": "INTEGER",
                            "TeamId": "INTEGER",
                        },
                        "Teams": {
                            "Id": "INTEGER",
                            "Name": "STRING",
                        },
                    }
                },
                di
…[201 chars elided]…
s` ON `teams`.`id` = `teammemberships`.`teamid` GROUP BY `teams`.`name`",
        )
        self.assertEqual(
            optimizer.qualify.qualify(
                parse_one(
                    "SELECT `my_db.my_table`.`my_column` FROM `my_db.my_table`",
                    read="bigquery",
                ),
                dialect="bigquery",
            ).sql(dialect="bigquery"),
            "SELECT `my_table`.`my_column` AS `my_column` FROM `my_db.my_table` AS `my_table`",
        )
341:0:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/tests/test_optimizer.py", "old_string": "            \"SELECT `my_table`.`my_column` AS `my_column` FROM `my_db.my_table` AS `my_table`\",\n        )\n", "new_string": "            \"SELECT `my_table`.`my_column` AS `my_column` FROM `my_db.my_table` AS `
…[324 chars elided]…
\"id\": \"INTEGER\", \"jan\": \"INTEGER\", \"feb\": \"INTEGER\"}},\n                dialect=\"bigquery\",\n            ).sql(dialect=\"bigquery\"),\n            \"WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180536-optimizer-select-from-cte-unpivo/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now the full test suite, plus lint on the touched files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -2"}
[tool_result] ............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                    [100%]
1092 passed, 17865 subtests passed in 45.39s
All checks passed!
2 files already formatted
[assistant] The `UNPIVOT` over a CTE now qualifies correctly, and the full suite passes (1092 tests). I haven't committed.

**Root cause:** A pivoted CTE reference (`FROM c UNPIVOT(...)`) becomes a new `Table` source in scope, not the CTE's `Scope`. The resolver then asked the schema for `c`'s columns, got none, and so could not resolve the `IN (...)` items. The schema-less path only worked because it fell back to attaching everything to the pivot alias.

**Fix:** In `sqlglot/optimizer/resolver.py` (`get_source_columns`), a pivoted reference whose name is a CTE in `scope.cte_sources` now takes its columns
…[360 chars elided]…
rence source columns. Before the fix, the same query with a schema raised `OptimizeError: Ambiguous column 'jan'`. `SELECT *` now expands to `id, m, v` as it already does for plain tables, instead of staying `*`.

**Test:** I added an assertion for this query to `test_qualify_columns` in `tests/test_optimizer.py`. I did not weaken any existing test.

**Not covered:** If the CTE has a column with the same name as an unpivot output (for example `v`), the existing pivot loop in `qualify_columns.py` may still qualify that output name. The plain-table path has the same behavior, so I left it alone.
