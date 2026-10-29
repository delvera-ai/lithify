# trajectory base-1

final message:
`qualify` now resolves `SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))` over a CTE, and the full optimizer keeps the CTE. The full suite passes (1092 tests, plus the new fixture), and ruff and mypy are clean on the changed modules. Nothing is committed.

There were two bugs on the same path:

- **Qualification (`resolver.py`):** A pivoted CTE reference stays a bare `Table` source, so the resolver had no columns for `c` and `jan` was reported as ambiguous. The resolver now reads the columns from the CTE's scope in that case.
- **Dropped CTE (`scope.py`, `eliminate_ctes.py`):** Even with qualification fixed, `optimize` deleted the CTE, leaving `FROM c` dangling. Reference counting only counted CTE scopes, not the pivoted `Table` that points at them. I added `Scope.pivoted_cte_scope()` and used it in `ref_count` and in the matching decrement in `eliminate_ctes`.

The BigQuery output for your example is now:

```sql
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`)
SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v`
FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
```

I added this as a BigQuery case in `tests/fixtures/optimizer/optimizer.sql`. Existing UNPIVOT-over-table fixtures also table-qualify the IN-list items, so the IN-list qualification matches the existing convention.

Things I chose or noticed:
- I tried pointing the pivoted reference at the CTE scope directly. That broke existing PIVOT and `qualify_tables` tests, so I dropped it.
- `WITH c AS (...) SELECT * FROM c PIVOT(SUM(x) FOR m IN ('a'))` with `m` as the pivot column still reports `m` as ambiguous. I did not dig into that; it may share the root cause but is outside this request.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"unpivot\\|pivot\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/annotate_types.py | head -60 && grep -n \"class Pivot\" -A 30 sqlglot/expressions.py | head -50", "description": "Check repo state and find pivot handling"}
[tool_result] sqlglot/optimizer/scope.py:81:    _pivots: list[exp.Pivot] | None
sqlglot/optimizer/scope.py:130:        self._pivots = None
sqlglot/optimizer/scope.py:411:                            expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:477:    def pivots(self) -> list[exp.Pivot]:
sqlglot/optimizer/scope.py:478:        if self._pivots is None:
sqlglot/optimizer/scope.py:479:            self._pivots = [
sqlglot/optimizer/scope.py:480:                pivo
…[4012 chars elided]…
vot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns.py:874:                    pivot_columns = pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:876:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:878:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:879:                        for name in pivot_columns
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot import exp\nfor d in ['bigquery','duckdb','snowflake']:\n    e = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read=d)\n    print(d, qualify(e, dialect=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}).sql(d))\n    print(repr(e.args['from'].this.args.get('pivots')) if False else '')\ne = sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery')\nprint(repr(e))\n\" 2>&1 | head -60; grep -n \"pivot\" sqlglot/optimizer/*.py | head -40", "description": "Reproduce UNPIVOT qualify issue"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
    validate_qualify_columns_func(expression, sql=sql)
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 164, in validate_qualify_columns
    rais
…[3881 chars elided]…
optimizer/qualify_columns.py:804:            pivot_output_columns = [c.output_name for c in pivot.args.get("columns", [])]
sqlglot/optimizer/qualify_columns.py:805:            if not pivot_output_columns:
sqlglot/optimizer/qualify_columns.py:806:                pivot_output_columns = [c.alias_or_name for c in pivot.expressions]
sqlglot/optimizer/qualify_columns.py:869:            if pivot:
sqlglot/optimizer/qualify_columns.py:870:                if pivot_output_columns and pivot_exclude_columns:
[tool_use Bash] {"command": "sed -n 110,205p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 600,660p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 780,815p sqlglot/optimizer/qualify_columns.py", "description": "Read UNPIVOT handling in qualify_columns"}
[tool_result]         if dialect.ANNOTATE_ALL_SCOPES:
            annotator.annotate_scope(scope)

    return expression


def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
    """Raise an `OptimizeError` if any columns aren't qualified"""
    all_unqualified_columns = []
    for scope in traverse_scope(expression):
        if isinstance(scope.expression, exp.Select):
            unqualified_columns = scope.unqualified_columns

            if scope.external_columns and not scope.is_cor
…[6489 chars elided]…
find_all(exp.Column))

            pivot_output_columns = [c.output_name for c in pivot.args.get("columns", [])]
            if not pivot_output_columns:
                pivot_output_columns = [c.alias_or_name for c in pivot.expressions]

    if dialect.SUPPORTS_STRUCT_STAR_EXPANSION and any(
        isinstance(col, exp.Dot) for col in scope.stars
    ):
        # Found struct expansion, annotate scope ahead of time
        annotator.annotate_scope(scope)

    scope_expression = scope.expression
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot import exp\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne = sqlglot.parse_one(sql, read='bigquery')\nprint(repr(e.args['from']))\nfor d in ['bigquery','duckdb','snowflake']:\n  try:
…[60 chars elided]…
ct=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}).sql(d))\n  except Exception as ex: print(d, 'ERR', ex)\n  try:\n    print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=False).sql(d))\n  except Exception as ex: print(d, 'ERR', ex)\n\" 2>&1 | head -60", "description": "Inspect pivot AST and qualify results"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
KeyError: 'from'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot import exp\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne = sqlglot.parse_one(sql, read='bigquery')\nprint(repr(e.args['from'] if 'from' in e.args else e.find(exp.From)))\nfor d in ['bigquery','duckdb','snowflake']:\n  for v in [True, False]:\n    try:\n      print(d, v, qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=v).sql(d))\n    except Exception as ex: print(d, v, 'ERR', ex)\n\" 2>&1 | head -60", "description": "Inspect pivot AST and qualify results"}
[tool_result] From(
  this=Table(
    this=Identifier(this=c, quoted=False),
    pivots=[
      Pivot(
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
        unpivot=Tru
…[254 chars elided]…
(`jan`, `feb`)) AS `c`
duckdb True ERR Ambiguous column 'jan' (Line: 1, Col: 78)
duckdb False WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake True ERR Ambiguous column 'JAN' (Line: 1, Col: 78)
snowflake False WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
[tool_use Bash] {"command": "grep -n \"^def \\|_qualify_columns(\\|_expand_\\|_qualify_outputs(\\|_disambiguate\" sqlglot/optimizer/qualify_columns.py | head -80 && grep -n \"def get_table\\|def all_columns\\|def get_source_columns\\|def _get_all_source_columns\\|def unambiguous\" -A 25 sqlglot/optimizer/resolver.py | sed -n 1,140p", "description": "Map qualify_columns functions and resolver"}
[tool_result] 21:def qualify_columns(
74:        using_column_tables = _expand_using(scope, resolver)
77:            _expand_alias_refs(
85:        _qualify_columns(
92:            _expand_alias_refs(scope, resolver, dialect)
96:                _expand_stars(
105:        _expand_group_by(scope, dialect)
109:        _expand_order_by_and_distinct_on(scope, resolver)
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
169:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]
…[7124 chars elided]…
ied, get all sources to calculate unambiguous columns
221-            if self._unambiguous_columns is None:
222-                self._unambiguous_columns = self._get_unambiguous_columns(
223-                    self._get_all_source_columns()
224-                )
225-
226-            unambiguous_columns = self._unambiguous_columns
227-        else:
228-            unambiguous_columns = self._get_unambiguous_columns(source_columns)
229-
230-        return unambiguous_columns.get(column_name)
231-
[tool_use Bash] {"command": "sed -n 21,110p sqlglot/optimizer/qualify_columns.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\norig = qc._qualify_columns\ndef spy(scope, resolver, allow):\n    print('scope', type(scope.expression).__name__, 'sources', list(scope
…[163 chars elided]…
able('jan'))\n    return orig(scope, resolver, allow)\nqc._qualify_columns = spy\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=False)\n\" 2>&1 | tail -30", "description": "Trace qualify_columns scope state"}
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
…[2782 chars elided]…
hify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 97, in qualify
    expression = qualify_columns_func(
                 ^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
TypeError: spy() got an unexpected keyword argument 'allow_partial_qualification'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\norig = qc._qualify_columns\ndef spy(scope, resolver, allow_partial_qualification):\n    print('scope', type(scope.expression).__name__, 'sources', list(scope.sources), 'pivots', len(scope.pi
…[152 chars elided]…
rn orig(scope, resolver, allow_partial_qualification)\nqc._qualify_columns = spy\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=False)\n\" 2>&1 | tail -30", "description": "Trace qualify_columns scope state"}
[tool_result] scope Select sources ['t'] pivots 0 cols ['id', 'jan', 'feb']
  all_columns {'jan', 'feb', 'id'} get_table(jan) t
scope Select sources ['c'] pivots 1 cols ['v', 'm', 'jan', 'feb']
  all_columns set() get_table(jan) None
[tool_use Bash] {"command": "sed -n 158,205p sqlglot/optimizer/resolver.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ns=build_scope(sqlglot.parse_one(sql, read='bigquery'))\nprint(s.sources)\nprint(s.selected_sources)\n\" 2>&1 | tail", "description": "Read source column resolution and scope sources"}
[tool_result]                                 element_types = col_type.expressions
                                if element_types:
                                    source_expr.type = element_types[0].copy()
                            elif col_type:
                                source_expr.type = col_type.copy()

                    columns.extend(self._struct_field_names(source_expr.type))
                elif isinstance(source_expr, exp.Lateral) and isinstance(
                    source_expr.this, 
…[1784 chars elided]…
ses)
                ]

            self._get_source_columns_cache[cache_key] = columns

        return self._get_source_columns_cache[cache_key]

        In(
          this=Column(
            this=Identifier(this=m, quoted=False)),
          expressions=[
            Column(
              this=Identifier(this=jan, quoted=False)),
            Column(
              this=Identifier(this=feb, quoted=False))])],
      unpivot=True,
      default_on_null=False)]), Scope<SELECT id, jan, feb FROM t>)}
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.schema import ensure_schema\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ne=sqlglot.parse_one(sql, read='bigquery')\nfrom sqlglot.o
…[32 chars elided]…
nfrom sqlglot.optimizer.qualify_tables import qualify_tables\ns=build_scope(e)\nprint('sources', {k:type(v).__name__ for k,v in s.sources.items()})\nprint('selected', list(s.selected_sources.keys()))\nprint('lateral', list(s.lateral_sources.keys()))\n\" 2>&1 | tail -8; grep -n \"def selected_sources\" -A 40 sqlglot/optimizer/scope.py | head -60", "description": "Check scope selected sources keys"}
[tool_result] sources {'c': 'Scope', '': 'Table'}
selected ['c']
lateral []
370:    def selected_sources(self) -> dict[str, tuple[exp.Selectable, exp.Table | Scope]]:
371-        """
372-        Mapping of nodes and sources that are actually selected from in this scope.
373-
374-        That is, all tables in a schema are selectable at any point. But a
375-        table only becomes a selected source if it's included in a FROM or JOIN clause.
376-
377-        Returns:
378-            dict[str, (exp.Table|exp.
…[976 chars elided]…
2-            for table in self.tables:
403-                self._references.append((table.alias_or_name, table))
404-            for _expr in itertools.chain(self.derived_tables, self.udtfs):
405-                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
406-                expression: exp.Expr = _expr
407-                self._references.append(
408-                    (
409-                        _get_source_alias(expression),
410-                        (
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\norig = qc._qualify_columns\ndef spy(scope, resolver, allow_partial_qualification):\n    if scope.pivots:\n        print('sources', {k:type(v).__name__ for k,v in scope.sources.items()}, 'sel
…[233 chars elided]…
scope, resolver, allow_partial_qualification)\nqc._qualify_columns = spy\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nqualify(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, validate_qualify_columns=False)\n\" 2>&1 | tail -30", "description": "Inspect CTE source columns during qualify"}
[tool_result] sources {'c': 'Table'} selected {'c': 'Table'}
get_source_columns []
src expr None
[tool_use Bash] {"command": "sed -n 780,830p sqlglot/optimizer/scope.py && grep -n \"def _traverse_tables\" -A 60 sqlglot/optimizer/scope.py | grep -n \"cte\\|sources\\[\" ", "description": "Read scope table source handling for pivots"}
[tool_result]     # Subqueries can be arbitrarily nested
    while type(parent) is exp.Subquery:
        parent = parent.parent

    return type(parent) in (exp.From, exp.Join)


def _traverse_tables(scope: Scope) -> Iterator[Scope]:
    sources: dict[str, exp.Table | Scope] = {}

    # Traverse FROMs, JOINs, and LATERALs in the order they are defined
    expressions: list[exp.Expr] = []
    from_ = scope.expression.args.get("from_")
    if from_:
        expressions.append(from_.this)

    for join in scope.
…[1228 chars elided]…
           if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
30:816-                    sources[pivots[0].alias] = expression
32:818-                    sources[source_name] = scope.sources[table_name]
34:820-                sources[find_new_name(sources, table_name)] = expression
36:822-                sources[source_name] = expression
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def ctes\\|self.sources\\b\" sqlglot/optimizer/scope.py | head -30; grep -rn \"UNPIVOT\\|PIVOT\" tests/test_optimizer.py tests/fixtures/optimizer/qualify_columns.sql | head -40; git log --oneline -3 -- sqlglot/optimizer/qualify_columns.py", "description": "Check scope CTE handling and existing pivot tests"}
[tool_result] 48:        cte_sources: Sources from CTES
92:        cte_sources: dict[str, exp.Table | Scope] | None = None,
96:        self.sources = sources or {}
98:        self.cte_sources = cte_sources or {}
99:        self.sources.update(self.lateral_sources)
100:        self.sources.update(self.cte_sources)
138:        cte_sources: dict[str, exp.Table | Scope] | None = None,
148:            cte_sources={**self.cte_sources, **(cte_sources or {})},
242:    def ctes(self) -> list[exp.CTE]:
391:            
…[3185 chars elided]…
al AS us_2010_seattle_total, _0.us_2010_seattle_count AS us_2010_seattle_count FROM cities AS cities PIVOT(SUM(population) AS total, COUNT(population) AS count FOR country IN ('nl', 'us') year IN (2000, 2010) name IN ('amsterdam', 'seattle')) AS _0;
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
c31e2e3a6 Refactor(Optimizer): improve typing coverage of optimizer modules (#7446)
f7bb6bea8 chore: use collections.abc and built-in types for typing to avoid deprecation (#7329)
[assistant] The root cause is in `scope.py`: a pivoted CTE reference is kept as a bare `Table` source, so the resolver has no columns for it and `jan` can't be qualified. The resolver already has the CTE's scope in `cte_sources`, so I'll resolve the pivoted source's columns from it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            source = self.scope.sources[name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)", "new_string": "            source = 
…[138 chars elided]…
")\n                and not source.db\n                and source.name in self.scope.cte_sources\n            ):\n                # A pivoted CTE reference stays a Table source, so resolve its columns from the CTE\n                source = self.scope.cte_sources[source.name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nfor d in ['bigquery','duckdb','snowflake','spark']:\n    print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}).sql(d))\nprint(qualify(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT v, m FROM c UNPIVOT(v FOR m IN (jan AS a, feb))', read='duckdb'), dialect='duckdb', schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}).sql('duckdb'))\n\" 2>&1 | tail -20", "description": "Verify fix on CTE UNPIVOT across dialects"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T".
…[104 chars elided]…
"V" FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
spark WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM (SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))) AS `c`
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."v" AS "v", "c"."m" AS "m" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan" AS "a", "feb")) AS "c"
[assistant] The outer `SELECT` now qualifies. The BigQuery output qualifies the IN-list items as `c.jan`, so I'll check how existing UNPIVOT-over-table fixtures are qualified to see whether that's consistent.
[tool_use Bash] {"command": "grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql tests/test_optimizer.py | head -20", "description": "Find existing UNPIVOT optimizer fixtures"}
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
[assistant] Existing fixtures also qualify IN-list items with the table prefix, so the BigQuery output is consistent. Now the full suite to check for regressions.
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
1092 passed, 17865 subtests passed in 53.27s
[assistant] All 1092 tests pass. Next I'll add a regression fixture next to the existing UNPIVOT cases.
[tool_use Bash] {"command": "sed -n 745,762p tests/fixtures/optimizer/optimizer.sql; grep -n \"^# title\" tests/fixtures/optimizer/optimizer.sql | awk -F: '$1>745 && $1<800' | head -3; grep -n \"pivot\\|PIVOT\" tests/fixtures/optimizer/optimizer.sql | head -5", "description": "View existing unpivot fixture format"}
[tool_result] UNPIVOT("SALES" FOR "MONTH" IN ("JAN", "FEB")) AS "_0"
ORDER BY
  "_0"."EMPID";

# title: unpivoted table source with a single value column, unpivot columns can be qualified
# execute: false
# dialect: bigquery
# note: the named columns aren not supported by BQ but we add them here to avoid defining a schema
SELECT * FROM produce AS produce(product, q1, q2, q3, q4) UNPIVOT(sales FOR quarter IN (q1, q2, q3, q4));
SELECT
  `produce`.`product` AS `product`,
  `produce`.`quarter` AS `quarter`,
  `pr
…[376 chars elided]…
e with multiple value columns
778:# title: quoting is preserved
544:# title: pivoted source with explicit selections
546:SELECT * FROM (SELECT a, b, c FROM sc.tb) PIVOT (SUM(c) FOR b IN ('x','y','z'));
559:PIVOT(SUM("_0"."c") FOR "_0"."b" IN ('x', 'y', 'z')) AS "_1";
561:# title: pivoted source with explicit selections where one of them is excluded & selected at the same time
562:# note: we need to respect the exclude when selecting * from pivoted source and not include the computed column twice
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "old_string": "# title: unpivoted table source with multiple value columns\n# execute: false", "new_string": "# title: unpivoted CTE source, unpivot columns can be qualified\n# execute: false\n# dialect: bigquery\
…[28 chars elided]…
feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));\nWITH `c` AS (\n  SELECT\n    `t`.`id` AS `id`,\n    `t`.`jan` AS `jan`,\n    `t`.`feb` AS `feb`\n  FROM `t` AS `t`\n)\nSELECT\n  `c`.`id` AS `id`,\n  `c`.`m` AS `m`,\n  `c`.`v` AS `v`\nFROM `c` AS `c`\nUNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`;\n\n# title: unpivoted table source with multiple value columns\n# execute: false"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -40", "description": "Run optimizer tests with new fixture", "timeout": 600000}
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
…[669 chars elided]…
        `c`.`id` AS `id`,
E                   `c`.`m` AS `m`,
E                   `c`.`v` AS `v`
E                 FROM `c` AS `c`
E                 UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`

tests/test_optimizer.py:203: AssertionError
=========================== short test summary info ============================
SUBFAILED[unpivoted CTE source, unpivot columns can be qualified] tests/test_optimizer.py::TestOptimizer::test_optimize
1 failed, 77 passed, 3705 subtests passed in 14.23s
[assistant] The full optimizer output drops the CTE definition, which would leave `FROM c` dangling. I need to see the actual output to judge whether that's my change or an existing rule.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nprint(optimize(sqlglot.parse_one(sql, read='bigquery'), schema={'t':{'id':'INT','jan':'INT','feb':'INT'}}, dialect='bigquery').sql('bigquery', pretty=True))\n\" 2>&1 | tail -30; git stash list | head -2; git -C ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1 status --short", "description": "Show full optimizer output for CTE UNPIVOT"}
[tool_result] SELECT
  `c`.`id` AS `id`,
  `c`.`m` AS `m`,
  `c`.`v` AS `v`
FROM `c` AS `c`
UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
 M sqlglot/optimizer/resolver.py
 M tests/fixtures/optimizer/optimizer.sql
[assistant] The full optimizer drops the CTE. I'll step through the rule sequence to find which rule does it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import ensure_schema\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\nschema={'t':{'id':'INT','jan':'INT','feb':'INT'}}\ne=sqlglot.
…[191 chars elided]…
_schema(schema, dialect=d)\n    if 'dialect' in params: kw['dialect']=d\n    if 'quote_identifiers' in params: pass\n    try:\n        e=rule(e, **kw)\n    except Exception as ex:\n        print('ERR', rule.__name__, ex); break\n    print(rule.__name__, 'WITH' in e.sql(d)[:5], e.sql(d)[:140].replace(chr(10),' '))\n\" 2>&1 | tail -40", "description": "Step through optimizer rules to find CTE drop"}
[tool_result] qualify True WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`
pushdown_projections True WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`
normalize True WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`
unnest_subqueries True 
…[1189 chars elided]…
OM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
annotate_types False SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
canonicalize False SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
simplify False SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[assistant] `eliminate_ctes` is removing the CTE even though the outer query still references it. Let me look at how it counts references.
[tool_use Bash] {"command": "cat sqlglot/optimizer/eliminate_ctes.py | sed -n 1,60p; grep -n \"def cte_sources\\|def tables\\|def _collect\" -A 12 sqlglot/optimizer/scope.py | sed -n 1,50p", "description": "Read eliminate_ctes implementation"}
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
     
…[1384 chars elided]…
mns = []
163-        self._stars = []
164-        self._join_hints = []
165-        self._semi_anti_join_tables = set()
166-        self._column_index = set()
167-
--
231:    def tables(self) -> list[exp.Table]:
232-        """
233-        List of tables in this scope.
234-
235-        Returns:
236-            list[exp.Table]: tables
237-        """
238-        self._ensure_collected()
239-        return self._tables
240-
241-    @property
242-    def ctes(self) -> list[exp.CTE]:
243-        """
[tool_use Bash] {"command": "grep -n \"def ref_count\" -A 25 sqlglot/optimizer/scope.py; grep -n \"def _traverse_scope\" -A 5 sqlglot/optimizer/scope.py | head; grep -n \"def _traverse_ctes\" -A 30 sqlglot/optimizer/scope.py | head -45", "description": "Read ref_count and CTE traversal"}
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
…[1468 chars elided]…
        for child_scope in _traverse_scope(
745-            scope.branch(
746-                cte.this,
747-                cte_sources=sources,
748-                outer_columns=cte.alias_column_names,
749-                scope_type=ScopeType.CTE,
750-            )
751-        ):
752-            yield child_scope
753-
754-        # append the final child_scope yielded
755-        if child_scope:
756-            sources[cte_name] = child_scope
757-            scope.cte_scopes.append(child_scope)
[assistant] The root cause of the dropped CTE is in `scope.py`: `ref_count` only counts `selected_sources` that are CTE `Scope`s, and the pivoted reference is a bare `Table`. The pivoted source should point at the CTE scope, as derived-table pivots already do. I'll try that and drop my resolver-only change if it holds up.
[tool_use Bash] {"command": "git checkout sqlglot/optimizer/resolver.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR m IN (\\'x\\'))'\nprint(optimize(sqlglot.parse_one(sql, read='bigquery'), schema={'t':{'id':'INT','jan':'INT','feb':'INT','m':'STRING'}}, dialect='bigquery').sql('bigquery', pretty=True))\n\" 2>&1 | tail -12", "description": "Revert resolver change; check PIVOT CTE baseline"}
[tool_result] Updated 1 path from the index
Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
    validate_qualify_columns_func(expression, sql=sql)
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 164, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Ambiguous column 'm' (Line: 1, Col: 75)
[assistant] The `git checkout` I ran reverted my resolver edit, as intended. I'll confirm the tree state before editing `scope.py`.
[tool_use Bash] {"command": "git status --short && sed -n 808,820p sqlglot/optimizer/scope.py", "description": "Confirm tree state and scope source code"}
[tool_result]  M tests/fixtures/optimizer/optimizer.sql
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                # This is a reference to a parent source (e.g. a CTE), not an actual table, unless\n                # it is pivoted, because then we get back a new table and hence a new source.\n               
…[268 chars elided]…
eference to a parent source (e.g. a CTE), not an actual table. If it is\n                # pivoted, the pivot's alias names the source, but it still resolves to the parent source\n                # so that its columns and references are known.\n                pivots = expression.args.get(\"pivots\")\n                sources[pivots[0].alias if pivots else source_name] = scope.sources[table_name]"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ns={'t':{'id':'INT','jan':'INT','feb':'INT'}}\nprint(optimize(sqlglot.parse_one(sql, read='bigquery'), schema=s
…[102 chars elided]…
CT id, jan, feb FROM t) SELECT id, v FROM c UNPIVOT(v FOR m IN (jan, feb)) WHERE v > 1', read='duckdb'), schema=s, dialect='duckdb').sql('duckdb', pretty=True))\n\" 2>&1 | tail -30 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Verify scope change and run full test suite", "timeout": 900000}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in
…[1757 chars elided]…
s from a pivoted CTE source, using alias for the aggregation and generating bigquery] tests/test_optimizer.py::TestOptimizer::test_optimize
SUBFAILED[unpivoted CTE source, unpivot columns can be qualified] tests/test_optimizer.py::TestOptimizer::test_optimize
SUBFAILED[Expand PIVOT column combinations] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
FAILED tests/test_optimizer.py::TestOptimizer::test_qualify_tables - Assertio...
4 failed, 1091 passed, 17795 subtests passed in 48.14s
[assistant] Moving the pivoted reference to the CTE scope breaks the existing PIVOT tests and `qualify_tables`, so I'm reverting that. The dropped-CTE bug needs its own fix. Let me see who consumes `selected_sources` before choosing where to fix it.
[tool_use Bash] {"command": "git checkout sqlglot/optimizer/scope.py && git status --short && grep -rn \"selected_sources\" sqlglot/ | grep -v \"def \\|_selected_sources\" | head -30", "description": "Revert scope change; find selected_sources users"}
[tool_result] Updated 1 path from the index
 M tests/fixtures/optimizer/optimizer.sql
sqlglot/lineage.py:325:                selected_node, _ = scope.selected_sources.get(table, (None, None))
sqlglot/optimizer/eliminate_ctes.py:49:                    for _, source in scope.selected_sources.values():
sqlglot/optimizer/isolate_table_selects.py:24:        if len(scope.selected_sources) == 1:
sqlglot/optimizer/isolate_table_selects.py:27:        for _, source in scope.selected_sources.values():
sqlglot/optimizer/
…[2234 chars elided]…
[conflict]
sqlglot/optimizer/merge_subqueries.py:417:        or len(outer_scope.selected_sources) != 1
sqlglot/optimizer/scope.py:588:            for _, source in scope.selected_sources.values():
sqlglot/optimizer/pushdown_projections.py:113:            for name, (node, source) in scope.selected_sources.items():
sqlglot/generators/exasol.py:184:    if not scope or not scope.selected_sources:
sqlglot/generators/exasol.py:189:    for source_name, (source_expr, _) in scope.selected_sources.items():
[assistant] Only the intended files are modified now; the `scope.py` and `resolver.py` notices were from my own checkouts. Before choosing the `eliminate_ctes` fix, I want to know whether the existing PIVOT-over-CTE case also loses its CTE under the full optimizer.
[tool_use Bash] {"command": "git status --short && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\ns={'t':{'id':'INT','jan':'INT','feb':'INT','v':'STRING','c':'INT'}}\nprint(optimize(sqlglot.parse_one(\\\"WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y'))\\\", read='bigquery'), schema=s, dialect='bigquery').sql('bigquery'))\n\" 2>&1 | tail -5; sed -n 262,290p tests/test_optimizer.py", "description": "Check PIVOT-over-CTE under full optimizer"}
[tool_result]  M tests/fixtures/optimizer/optimizer.sql
WITH `cte` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb`, `t`.`v` AS `v`, `t`.`c` AS `c` FROM `t` AS `t`) SELECT `_0`.`id` AS `id`, `_0`.`jan` AS `jan`, `_0`.`feb` AS `feb`, `_0`.`x` AS `x`, `_0`.`y` AS `y` FROM `cte` AS `cte` PIVOT(SUM(`cte`.`c`) FOR `cte`.`v` IN ('x', 'y')) AS `_0`
                dialect="bigquery",
                quote_identifiers=False,
            ).sql("bigquery"),
            "WITH test AS (SELECT * FROM ca
…[502 chars elided]…
 )

        self.assertEqual(
            optimizer.qualify_tables.qualify_tables(
                parse_one(
                    "WITH cte AS (SELECT * FROM t) SELECT * FROM cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias"
                ),
                db="db",
                catalog="catalog",
            ).sql(),
            "WITH cte AS (SELECT * FROM catalog.db.t AS t) SELECT * FROM cte AS cte PIVOT(SUM(c) FOR v IN ('x', 'y')) AS pivot_alias",
        )

        self.assertEqual(
[assistant] PIVOT over a CTE keeps its CTE under the full optimizer, so the drop is specific to my UNPIVOT case. I'll check the ref counts at `eliminate_ctes` for both to find the difference.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.schema import ensure_schema\nimport inspect\ns={'t':{'id':'INT','jan':'INT','feb':'INT','v':'STRING','c':'INT','m':'STRING'}}\nfor sql in ['WITH c AS (SELECT id, jan, feb FROM t) SE
…[510 chars elided]…
      print(rule.__name__, e.sql(d)[:60].replace(chr(10),' '), [ (type(sc.expression).__name__) for sc in root.traverse()][:4] if root else None)\n      if root:\n        rc=root.ref_count()\n        for sc in root.traverse():\n          if sc.is_cte: print('  cte', sc.expression.alias, rc[id(sc)])\n  print('----')\n\" 2>&1 | tail -30", "description": "Compare CTE ref counts for PIVOT vs UNPIVOT"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 15, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
    validate_qualify_columns_func(expression, sql=sql)
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 164, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Ambiguous column 'jan' (Line: 1, Col: 78)
[assistant] The resolver fix was reverted by my earlier checkout, so I'll re-apply it before continuing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            source = self.scope.sources[name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)", "new_string": "            source = 
…[138 chars elided]…
")\n                and not source.db\n                and source.name in self.scope.cte_sources\n            ):\n                # A pivoted CTE reference stays a Table source, so resolve its columns from the CTE\n                source = self.scope.cte_sources[source.name]\n\n            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import RULES\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.schema import ensure_schema\nimport inspect\ns={'t':{'id':'INT','jan':'INT','feb':'INT','v':'STRING','c':'INT','m':'STRING'}}\nfor sql in ['WITH c AS (SELECT id, jan, feb FROM t) SE
…[427 chars elided]…
_name__=='eliminate_ctes' or rule.__name__=='qualify':\n      root=build_scope(e)\n      print(rule.__name__, e.sql(d)[:60].replace(chr(10),' '))\n      if root:\n        rc=root.ref_count()\n        for sc in root.traverse():\n          if sc.is_cte: print('  cte', sc.expression.alias, rc[id(sc)])\n  print('----')\n\" 2>&1 | tail -30", "description": "Compare CTE ref counts for PIVOT vs UNPIVOT"}
[tool_result] qualify WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t
  cte  0
eliminate_ctes SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM
----
qualify WITH `cte` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, 
  cte  1
eliminate_ctes WITH `cte` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, 
  cte  1
----
[assistant] For PIVOT the CTE ref count is 1, for UNPIVOT it is 0. I'll compare the outer scope's sources for the two cases after `qualify`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\ns={'t':{'id':'INT','jan':'INT','feb':'INT','v':'STRING','c':'INT','m':'STRING'}}\nfor sql in ['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', \\\"WITH ct
…[101 chars elided]…
.parse_one(sql, read='bigquery'), schema=s, dialect='bigquery')\n  root=build_scope(e)\n  outer=[sc for sc in root.traverse() if not sc.is_cte][-1]\n  print({k:(type(n).__name__, type(src).__name__) for k,(n,src) in outer.selected_sources.items()})\n  print({k:type(v).__name__ for k,v in outer.sources.items()})\n\" 2>&1 | tail -8", "description": "Compare outer scope sources for PIVOT vs UNPIVOT"}
[tool_result] {'c': ('Table', 'Table')}
{'c': 'Table'}
{'cte': ('Table', 'Scope')}
{'cte': 'Scope', '_0': 'Table'}
[assistant] The difference is in how `qualify_tables` aliases the pivot: for UNPIVOT the table alias equals the pivot alias, so `_traverse_tables` registers the CTE reference as a bare `Table` and `ref_count` never counts it. Changing what the source maps to broke other tests, so I'll keep the source as-is and teach reference counting to resolve a pivoted CTE reference to its CTE scope.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "        scope_ref_count: dict[int, int] = defaultdict(int)\n\n        for scope in self.traverse():\n            for _, source in scope.selected_sources.values():\n                scope_ref_count[id(source)] += 1\n", "new_string": "        scope_ref_count: dict[int, int] = defaultdict(int)\n\n        for scope in self.traverse():\n            for node, source in scope.selected_sources.values():\n                scope_ref_count[id(source)] += 1\n                if pivoted_cte := scope.pivoted_cte_scope(node):\n                    scope_ref_count[id(pivoted_cte)] += 1\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "offset": 560, "limit": 30}
[tool_result] 560	            Scope: scope instances in depth-first-search post-order
561	        """
562	        stack: list[Scope] = [self]
563	        result: list[Scope] = []
564	        while stack:
565	            scope = stack.pop()
566	            result.append(scope)
567	            stack.extend(
568	                itertools.chain(
569	                    scope.cte_scopes,
570	                    scope.union_scopes,
571	                    scope.table_scopes,
572	                    scope.subquery_s
…[90 chars elided]…
)
577	
578	    def ref_count(self) -> dict[int, int]:
579	        """
580	        Count the number of times each scope in this tree is referenced.
581	
582	        Returns:
583	            dict[int, int]: Mapping of Scope instance ID to reference count
584	        """
585	        scope_ref_count: dict[int, int] = defaultdict(int)
586	
587	        for scope in self.traverse():
588	            for node, source in scope.selected_sources.values():
589	                scope_ref_count[id(source)] += 1
[assistant] Now I'll add the `pivoted_cte_scope` helper next to `ref_count`, and use it in `eliminate_ctes` so the decrement stays symmetric.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "    def ref_count(self) -> dict[int, int]:\n        \"\"\"", "new_string": "    def pivoted_cte_scope(self, node: exp.Expr) -> Scope | None:\n        \"\"\"\n        The CTE scope behind a pivoted CTE reference
…[140 chars elided]…
  Scope | None: the CTE scope if `node` is a pivoted reference to a CTE.\n        \"\"\"\n        if isinstance(node, exp.Table) and node.args.get(\"pivots\") and not node.db:\n            cte_source = self.cte_sources.get(node.name)\n            if isinstance(cte_source, Scope):\n                return cte_source\n        return None\n\n    def ref_count(self) -> dict[int, int]:\n        \"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/eliminate_ctes.py", "old_string": "                    for _, source in scope.selected_sources.values():\n                        if isinstance(source, Scope):\n                            ref_count[id(source)] -= 1", "new_string": "                    for node, source in scope.selected_sources.values():\n                        if isinstance(source, Scope):\n                            ref_count[id(source)] -= 1\n                        elif pivoted_cte := scope.pivoted_cte_scope(node):\n                            ref_count[id(pivoted_cte)] -= 1"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094621-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/eliminate_ctes.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\ns={'t':{'id':'INT','jan':'INT','feb':'INT'}}\nprint(optimize(sqlglot.parse_one('WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='bigquery'), schema=s, dialect='bigquery').sql('bigquery', pretty=True))\npri
…[276 chars elided]…
, feb FROM t), b AS (SELECT * FROM a UNPIVOT(v FOR m IN (jan, feb))) SELECT id FROM b', read='duckdb'), schema=s, dialect='duckdb').sql('duckdb', pretty=True))\n\" 2>&1 | tail -40 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Verify optimize keeps CTE and run full tests", "timeout": 900000}
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
WITH "a" AS (
  SELECT
    "t"."id" AS "id",
    "t"."jan" AS "jan",
    "t"."feb" AS "feb"
  FROM "t" AS "t"
)
SELECT
  "a"."id" AS "id"
FROM "a" AS "a"
UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "a"
WITH "a" AS (
  SELECT
    "t"."id" AS "id",
    "t"."ja
…[934 chars elided]…
 [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
............................ [ 83%]
.........................................................................................................................................................................................                                                   [100%]
1092 passed, 17866 subtests passed in 48.58s
[assistant] All 1092 tests pass, including the new fixture, and the chained case (CTE `b` over pivoted `a`) keeps the right CTEs. Last, the project's lint/format checks on the changed files.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/ | grep -i \"ruff\\|mypy\" ; <work>/env-sqlglot/bin/ruff check sqlglot/optimizer/scope.py sqlglot/optimizer/eliminate_ctes.py sqlglot/optimizer/resolver.py 2>&1 | tail -3; <work>/env-sqlglot/bin/ruff format --check sqlglot/optimizer/scope.py sqlglot/optimizer/eliminate_ctes.py sqlglot/optimizer/resolver.py 2>&1 | tail -3; git diff --stat", "description": "Run ruff lint and format checks on changed files"}
[tool_result] dmypy
mypy
mypyc
ruff
All checks passed!
3 files already formatted
 sqlglot/optimizer/eliminate_ctes.py    |  4 +++-
 sqlglot/optimizer/resolver.py          |  9 +++++++++
 sqlglot/optimizer/scope.py             | 19 ++++++++++++++++++-
 tests/fixtures/optimizer/optimizer.sql | 18 ++++++++++++++++++
 4 files changed, 48 insertions(+), 2 deletions(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/mypy sqlglot/optimizer/scope.py sqlglot/optimizer/eliminate_ctes.py sqlglot/optimizer/resolver.py 2>&1 | tail -5", "description": "Type-check changed optimizer modules", "timeout": 600000}
[tool_result] Success: no issues found in 3 source files
[assistant] `qualify` now resolves `SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))` over a CTE, and the full optimizer keeps the CTE. The full suite passes (1092 tests, plus the new fixture), and ruff and mypy are clean on the changed modules. Nothing is committed.

There were two bugs on the same path:

- **Qualification (`resolver.py`):** A pivoted CTE reference stays a bare `Table` source, so the resolver had no columns for `c` and `jan` was reported as ambiguous. The resolver now reads the columns from the CTE's scope in that case.
- **Dropped CTE (`scope.py`, `eliminate_ctes.py`):** Even with qualifi
…[539 chars elided]…
AS `c`
```

I added this as a BigQuery case in `tests/fixtures/optimizer/optimizer.sql`. Existing UNPIVOT-over-table fixtures also table-qualify the IN-list items, so the IN-list qualification matches the existing convention.

Things I chose or noticed:
- I tried pointing the pivoted reference at the CTE scope directly. That broke existing PIVOT and `qualify_tables` tests, so I dropped it.
- `WITH c AS (...) SELECT * FROM c PIVOT(SUM(x) FOR m IN ('a'))` with `m` as the pivot column still reports `m` as ambiguous. I did not dig into that; it may share the root cause but is outside this request.
