# trajectory base-1

final message:
`qualify` now handles `UNPIVOT` over a CTE. The example from the issue comes out correctly in BigQuery, DuckDB and Snowflake, and the full suite passes (1092 tests).

**Before:** the new names were qualified with the CTE alias:
```sql
... FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`))
```
**After:**
```sql
... FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
```

There were two causes:

1. **`sqlglot/optimizer/qualify_columns.py`:** the `v` and `m` columns were unqualified, so the resolver assigned them to the only source. They are now left alone, matched by node identity so a same-named column elsewhere in the query is still qualified. The IN-list items still get qualified.
2. **`sqlglot/optimizer/resolver.py`:** with a schema, the UNPIVOTed CTE's columns came back empty, so `jan` was reported as ambiguous. This failed on unmodified HEAD too. The resolver now uses the CTE's projections for an UNPIVOTed CTE. Pivoted CTEs that are not UNPIVOTs are unchanged.

**Tests:** I added two cases to `tests/fixtures/optimizer/qualify_columns.sql`: the bare `SELECT *` from the issue, and selecting `v, m` explicitly. Both fail on the original source and pass now. I did not edit any existing test.

Not done: I haven't run this against real BigQuery, DuckDB or Snowflake, only through sqlglot's own generation. I also haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"unpivot\" sqlglot/optimizer/ sqlglot/expressions.py | head -50", "description": "Check status and find UNPIVOT references"}
[tool_result] okgrep: sqlglot/expressions.py: No such file or directory
sqlglot/optimizer/qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
sqlglot/optimizer/qualify_columns.py:141:            if unqualified_columns and scope.pivots and scope.pivots[0].unpivot:
sqlglot/optimizer/qualify_columns.py:142:                # New columns produced by the UNPIVOT can't be qualified, but there may be columns
sqlglot/optimizer/qualify_columns.py:143:                # under the UNP
…[434 chars elided]…
ptimizer/qualify_columns.py:194:        for field in unpivot.fields
sqlglot/optimizer/qualify_columns.py:197:    value_columns = (c for e in unpivot.expressions for c in e.find_all(exp.Column))
sqlglot/optimizer/qualify_columns.py:792:        if pivot.unpivot:
sqlglot/optimizer/qualify_columns.py:793:            pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/optimizer/qualify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor d in ['bigquery','duckdb','snowflake','sqlglot']:\n    sql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\n    try:\n        print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d).sql(d))\n    except Exception as e: print(d, 'ERR', repr(e))\n\"", "description": "Reproduce UNPIVOT qualify issue across dialects"}
[tool_result] bigquery WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
snowflake WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
sqlglot ERR ValueError("Unknown dialect 'sqlglot'. Did you mean sqlite?")
[assistant] The bug reproduces: the new `v` and `m` names come out as `c.v` and `c.m`. Let me look at the relevant code.
[tool_use Bash] {"command": "sed -n 120,205p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 770,815p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 150,185p sqlglot/optimizer/qualify_tables.py", "description": "Read unpivot-related qualify code"}
[tool_result]     for scope in traverse_scope(expression):
        if isinstance(scope.expression, exp.Select):
            unqualified_columns = scope.unqualified_columns

            if scope.external_columns and not scope.is_correlated_subquery and not scope.pivots:
                column = scope.external_columns[0]
                for_table = f" for table: '{column.table}'" if column.table else ""
                line = column.this.meta.get("line")
                col = column.this.meta.get("col")
       
…[5651 chars elided]…
voted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
                        on_qualify(source)
            elif isinstance(source, Scope) and source.is_udtf:
                _set_alias(udtf := source.expression, canonical_aliases)

                table_alias = udtf.args["alias"]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\nprint(repr(e.args['from'].this.args.get('pivots') or e.find(sqlglot.exp.Pivot)))\n\" ; grep -n \"pivot\" sqlglot/optimizer/scope.py | head -30; grep -n \"pivot\" sqlglot/optimizer/qualify_columns.py | head -40", "description": "Inspect UNPIVOT AST and scope pivot handling"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'from'
13 matches in 6 files:

477:0:
478:0:
81:0:list[exp.Pivot] | None
815:0:
947:0:
sqlglot/optimizer/scope.py:130:self._pivots = None
sqlglot/optimizer/scope.py:411:expression if expression.args.get("pivots") else expression.unnest()
sqlglot/optimizer/scope.py:479:self._pivots = [
sqlglot/optimizer/scope.py:480:pivot for _, node in self.references for pivot in node.args.get("pivots") or []
sqlglot/optimizer/s
…[1732 chars elided]…
olumns = [c.alias_or_name for c in pivot.expressions]
sqlglot/optimizer/qualify_columns.py:871:pivot_columns = [c for c in columns if c not in pivot_exclude_columns]
sqlglot/optimizer/qualify_columns.py:872:pivot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns.py:874:pivot_columns = pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:878:alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:879:for name in pivot_columns
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))', read='duckdb')\np=e.find(sqlglot.exp.Pivot)\nprint(repr(p))\n\" ; sed -n 600,660p sqlglot/optimizer/qualify_columns.py", "description": "Show parsed UNPIVOT node and column qualification code"}
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
    scope: Scope,
    resolver: Resolver,
    allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring ea
…[1799 chars elided]…
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
[assistant] The pivot columns `v` and `m` are the new output names, but they get a table qualifier. Let me check whether this also happens for a real table, to narrow down which code path adds it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'t':{'id':'int','jan':'int','feb':'int'}}, dialect='bigquery
…[138 chars elided]…
N (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT v, m FROM c UNPIVOT(v FOR m IN (jan, feb))']:\n    print(qualify(sqlglot.parse_one(sql, read='bigquery'), schema=s, dialect='bigquery').sql('bigquery'))\n    print(qualify(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery').sql('bigquery'))\n\" 2>&1 | tail -20", "description": "Compare UNPIVOT qualify with table vs CTE source"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 9, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
    validate_qualify_columns_func(expression, sql=sql)
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", line 164, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Ambiguous column 'jan' (Line: 1, Col: 78)
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT * FROM `t` AS `t` UNPIVOT(`t`.`v` FOR `t`.`m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
[assistant] Root cause is in `_qualify_columns`: the new UNPIVOT names (`v` in the value list, `m` as the `FOR` column) are unqualified columns in the scope, and the resolver assigns them to the single source. Let me read that function's start and the resolver's `get_table` to confirm.
[tool_use Bash] {"command": "sed -n 585,600p sqlglot/optimizer/qualify_columns.py && grep -n \"def get_table\" -A 30 sqlglot/optimizer/qualify_columns.py | head -50", "description": "Read _qualify_columns header and resolver.get_table"}
[tool_result]                 new_column = exp.column(root, table=column_table)

                if dot_parts:
                    # Remove the actual column parts from the rest of dot parts
                    new_column.meta["dot_parts"] = dot_parts[2 if was_qualified else 1 :]

                column.replace(exp.Dot.build([new_column, *parts]))

    if converted:
        # We want to re-aggregate the converted columns, otherwise they'd be skipped in
        # a `for column in scope.columns` iteration, even though they shouldn't be
        scope.clear_cache()


def _qualify_columns(
    scope: Scope,
[tool_use Bash] {"command": "grep -n \"def get_table\" -A 25 sqlglot/optimizer/resolver.py", "description": "Read Resolver.get_table implementation"}
[tool_result] 34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
35-        """
36-        Get the table for a column name.
37-
38-        Args:
39-            column: The column expression (or column name) to find the table for.
40-        Returns:
41-            The table name if it can be found/inferred.
42-        """
43-        column_name = column if isinstance(column, str) else column.name
44-
45-        table_name = self._get_table_name_from_sources(column_name)
46-
47-    
…[508 chars elided]…
e able to disambiguate the column
53-                # and we can use the source columns available at that join to get the table name
54-                # catch OptimizeError if column is still ambiguous and try to resolve with schema inference below
55-                try:
56-                    table_name = self._get_table_name_from_sources(
57-                        column_name, self._get_available_source_columns(join_context)
58-                    )
59-                except OptimizeError:
[assistant] Confirmed: for an unqualified column the resolver falls back to the single source, so `v` and `m` get the CTE alias. The UNPIVOT output names are the `expressions` columns and the `FOR` column (`In.this`), which `_unpivot_columns` already identifies. The fix is to leave those unqualified in `_qualify_columns`, matching by node identity so that a same-named column elsewhere in the query is still qualified.
[tool_use Bash] {"command": "sed -n 600,612p sqlglot/optimizer/qualify_columns.py", "description": "Show exact lines to edit in _qualify_columns"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    \"\"\"Disambiguate columns, ensuring each column specifies a source\"\"\"\n    for column in scope.columns:\n        column_table = column.table\n        column_name = column.name\n\n        if co
…[205 chars elided]…
not references to source columns\n    unpivot_output_ids = {\n        id(c) for pivot in scope.pivots if pivot.unpivot for c in _unpivot_columns(pivot)\n    }\n\n    for column in scope.columns:\n        column_table = column.table\n        column_name = column.name\n\n        if id(column) in unpivot_output_ids:\n            continue\n\n        if column_table and column_table in scope.sources:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    for pivot in scope.pivots:\n        for column in pivot.find_all(exp.Column):\n            if not column.table and column.name in resolver.all_columns:", "new_string": "    for pivot in scope.pivots:\n        for column in pivot.find_all(exp.Column):\n            if not column.table and column.name in resolver.all_columns and id(column) not in unpivot_output_ids:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'t':{'id':'int','jan':'int','feb':'int'}}, dialect='bigquery')\ncases=['SELECT * FROM t UNPIVOT(v FOR m IN (jan, feb))','WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(
…[203 chars elided]…
)']\nfor sql in cases:\n  for sch in [None, s]:\n    try: print(qualify(sqlglot.parse_one(sql, read='bigquery'), schema=sch, dialect='bigquery').sql('bigquery'))\n    except Exception as e: print('ERR', e)\n  print()\nfor d in ['bigquery','duckdb','snowflake']:\n    print(qualify(sqlglot.parse_one(cases[1], read=d), dialect=d).sql(d))\n\"", "description": "Verify qualify output for UNPIVOT cases"}
[tool_result] SELECT * FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`

WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR Ambiguous column 'jan' (Line: 1, Col: 78)

WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`v` AS `v`, `t`.`jan` AS `jan`, 
…[422 chars elided]…
TH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT * FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT * FROM "C" AS "C" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "C"
[assistant] The reported case is fixed in all three dialects. Two schema-backed cases still raise "Ambiguous column 'jan'". I need to know whether that predates my change, so I'll run the same inputs against the unmodified HEAD source.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-orig && mkdir -p /tmp/sqlglot-orig && git archive HEAD sqlglot | tar -x -C /tmp/sqlglot-orig && cat > /tmp/unpivot_check.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'t': {'id': 'int', 'jan': 'int', 'feb': 'int'}}, dialect='bigquery')\ncases = ['WITH c AS (SELECT id, jan, feb
…[319 chars elided]…
print('ERR', e)\nEOF\necho ORIG; /usr/bin/env -i PYTHONPATH=/tmp/sqlglot-orig <work>/env-sqlglot/bin/python -I /tmp/unpivot_check.py; echo NEW; /usr/bin/env -i PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I /tmp/unpivot_check.py", "description": "Compare schema-backed UNPIVOT results before and after change"}
[tool_result ERROR] Exit code 1
ORIG
Traceback (most recent call last):
  File "/tmp/unpivot_check.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
NEW
Traceback (most recent call last):
  File "/tmp/unpivot_check.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "echo ORIG; PYTHONPATH=/tmp/sqlglot-orig <work>/env-sqlglot/bin/python /tmp/unpivot_check.py; echo NEW; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_check.py", "description": "Compare schema-backed UNPIVOT results before and after change"}
[tool_result] ORIG
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
ERR Ambiguous column 'jan' (Line: 1, Col: 81)
NEW
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
ERR Ambiguous column 'jan' (Line: 1, Col: 81)
[assistant] Both schema-backed failures also occur on unmodified HEAD, so they're pre-existing. The issue is about this same shape over a CTE, though, so I'll check why the IN-list `jan` stays unqualified when a schema is present.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'t':{'id':'int','jan':'int','feb':'int'}}, dialect='bigquery')\norig=qc._qualify_columns\ndef dbg(scope, resolver, 
…[233 chars elided]…
xception as e: print('exc', e)\n    return orig(scope, resolver, allow)\nqc._qualify_columns=dbg\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: qualify(sqlglot.parse_one(sql, read='bigquery'), schema=s, dialect='bigquery')\nexcept Exception as e: print('ERR', e)\n\" 2>&1 | head -30", "description": "Trace resolver for IN-list column with schema"}
[tool_result] ERR dbg() got an unexpected keyword argument 'allow_partial_qualification'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'t':{'id':'int','jan':'int','feb':'int'}}, dialect='bigquery')\norig=qc._qualify_columns\ndef dbg(scope, resolver, 
…[238 chars elided]…
on as e: print('exc', e)\n    return orig(scope, resolver, **kw)\nqc._qualify_columns=dbg\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: qualify(sqlglot.parse_one(sql, read='bigquery'), schema=s, dialect='bigquery')\nexcept Exception as e: print('ERR', e)\n\" 2>&1 | head -30", "description": "Retry resolver trace with keyword-compatible wrapper"}
[tool_result] sources ['t'] [('id', ''), ('jan', ''), ('feb', '')]
get_table t
sources ['c'] [('v', ''), ('m', ''), ('jan', ''), ('feb', '')]
get_table None
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'t':{'id':'int','jan':'int','feb':'int'}}, dialect='bigquery')\norig=qc._qualify_columns\ndef dbg(scope, resolver, 
…[212 chars elided]…
bg\nsql='WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))'\ntry: qualify(sqlglot.parse_one(sql, read='bigquery'), schema=s, dialect='bigquery')\nexcept Exception as e: print('ERR', e)\n\" 2>&1 | head; grep -n \"def _get_table_name_from_sources\" -A 25 sqlglot/optimizer/resolver.py | head -40", "description": "Inspect source columns resolved for the CTE source"}
[tool_result] src cols c []
all set()
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
216:    def _get_table_name_from_sources(
217-        self, column_name: str, source_columns: dict[str, Sequence[str]] | None = None
218-    ) -> str | None:
219-        if not source_columns:
220-            # If not supplied, get all sources to calculate unambiguous columns
221-            if self._unambiguous_columns is None:
222-                self._unambiguous_columns = self._get_unambiguous_columns(
223-                
…[325 chars elided]…
ntext(self, column: exp.Column) -> exp.Join | None:
233-        """
234-        Check if a column participating in a join can be qualified based on the source order.
235-        """
236-        args = self.scope.expression.args
237-        joins = args.get("joins")
238-
239-        if not joins or args.get("laterals") or args.get("pivots"):
240-            # Feature gap: We currently don't try to disambiguate columns if other sources
241-            # (e.g laterals, pivots) exist alongside joins
[tool_use Bash] {"command": "grep -n \"def get_source_columns\\|def _get_source_columns\\|def _get_all_source_columns\" -A 30 sqlglot/optimizer/resolver.py | sed -n 1,120p", "description": "Read resolver source-column lookup for scope sources"}
[tool_result] 95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
96-        if isinstance(expression, exp.Select):
97-            return expression.named_selects
98-        if isinstance(expression, exp.Subquery) and isinstance(expression.this, exp.SetOperation):
99-            # Different types of SET modifiers can be chained together if they're explicitly grouped by nesting
100-            return self.get_source_columns_from_set_op(expression.this)
101-        if not isinsta
…[4051 chars elided]…
   )
225-
226-            unambiguous_columns = self._unambiguous_columns
227-        else:
228-            unambiguous_columns = self._get_unambiguous_columns(source_columns)
229-
230-        return unambiguous_columns.get(column_name)
231-
232-    def _get_column_join_context(self, column: exp.Column) -> exp.Join | None:
233-        """
234-        Check if a column participating in a join can be qualified based on the source order.
235-        """
236-        args = self.scope.expression.args
[tool_use Bash] {"command": "sed -n 163,205p sqlglot/optimizer/resolver.py", "description": "Read remaining get_source_columns logic"}
[tool_result]                     columns.extend(self._struct_field_names(source_expr.type))
                elif isinstance(source_expr, exp.Lateral) and isinstance(
                    source_expr.this, exp.Explode
                ):
                    explode_col = source_expr.this.this

                    if isinstance(explode_col, exp.Column) and source.parent:
                        col_type = self._get_unnest_column_type(explode_col, source.parent)
                        columns.extend(self._struct
…[1120 chars elided]…
       # If the source's columns are aliased, their aliases shadow the corresponding column names.
                # This can be expensive if there are lots of columns, so only do this if column_aliases exist.
                columns = [
                    alias or name
                    for (name, alias) in itertools.zip_longest(columns, column_aliases)
                ]

            self._get_source_columns_cache[cache_key] = columns

        return self._get_source_columns_cache[cache_key]
[assistant] The CTE source's columns come back empty here. I think the pivot replaces the CTE's scope in `scope.sources`, so the resolver never sees the CTE's projections. Let me check that in scope.py.
[tool_use Bash] {"command": "sed -n 800,830p sqlglot/optimizer/scope.py && sed -n 60,94p sqlglot/optimizer/resolver.py", "description": "Read scope pivot source handling and resolver fallback"}
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
…[1543 chars elided]…
    node_alias = node.args.get("alias")
        if node_alias:
            return exp.to_identifier(node_alias.this)

        return exp.to_identifier(table_name)

    @property
    def all_columns(self) -> set[str]:
        """All available columns of all sources in this scope"""
        if self._all_columns is None:
            self._all_columns = {
                column for columns in self._get_all_source_columns().values() for column in columns
            }
        return self._all_columns
[assistant] The pivot case in `scope.py` stores the bare `exp.Table` in `scope.sources` instead of the CTE's `Scope`. The resolver then asks the schema for `c`'s columns and gets none. Let me check whether the CTE's scope is reachable from the resolver's scope.
[tool_use Bash] {"command": "grep -n \"cte_sources\\|def selected_sources\" sqlglot/optimizer/scope.py | head -20; grep -n \"def selected_sources\" -A 12 sqlglot/optimizer/scope.py", "description": "Locate CTE source tracking in Scope"}
[tool_result] 11 matches in 5 files:

138:0:dict[str, exp.Table | Scope] | None = None,
370:0:
48:0:Sources from CTES
92:0:dict[str, exp.Table | Scope] | None = None,
sqlglot/optimizer/scope.py:98:self.cte_sources = cte_sources or {}
sqlglot/optimizer/scope.py:100:self.sources.update(self.cte_sources)
sqlglot/optimizer/scope.py:148:cte_sources={**self.cte_sources, **(cte_sources or {})},
sqlglot/optimizer/scope.py:667:yield from _traverse_scope(Scope(ddl_expression, cte_sources=scope.cte_sources))
sqlglot/opt
…[349 chars elided]…
sources that are actually selected from in this scope.
373-
374-        That is, all tables in a schema are selectable at any point. But a
375-        table only becomes a selected source if it's included in a FROM or JOIN clause.
376-
377-        Returns:
378-            dict[str, (exp.Table|exp.Select, exp.Table|Scope)]: selected sources and nodes
379-        """
380-        if self._selected_sources is None:
381-            result: dict[str, tuple[exp.Selectable, exp.Table | Scope]] = {}
382-
[assistant] The resolver's scope has `cte_sources`, so it can reach the CTE's projections. I'll have the resolver use those projections, with the UNPIVOT applied (IN-list columns removed, new names added), for an unpivoted CTE. First, the resolver's imports:
[tool_use Bash] {"command": "sed -n 1,33p sqlglot/optimizer/resolver.py && grep -n \"^def \\|^class \" sqlglot/optimizer/resolver.py", "description": "Read resolver module header and top-level defs"}
[tool_result] from __future__ import annotations

import itertools
import typing as t

from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.errors import OptimizeError
from sqlglot.helper import seq_get, SingleValuedMapping
from sqlglot.optimizer.scope import Scope

if t.TYPE_CHECKING:
    from sqlglot.schema import Schema
    from collections.abc import Sequence, Mapping


class Resolver:
    """
    Helper for resolving columns.

    This is a class so we can lazily load some th
…[82 chars elided]…
: Scope, schema: Schema, infer_schema: bool = True):
        self.scope = scope
        self.schema = schema
        self.dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | None = None
        self._infer_schema = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}

1 matches in 1 files:

17:0:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "            if isinstance(source, exp.Table):\n                columns = self.schema.column_names(source, only_visible)\n            elif", "new_string": "            if isinstance(source, exp.Table):\n     
…[95 chars elided]…
IVOTed CTE is kept as a Table, so its columns come from the CTE's projections\n                cte = self.scope.cte_sources.get(source.name)\n                unpivot = seq_get(source.args.get(\"pivots\") or [], 0)\n                if cte and isinstance(unpivot, exp.Pivot) and unpivot.unpivot:\n                    columns = _unpivot_columns(cte.expression.named_selects, unpivot)\n            elif"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "if t.TYPE_CHECKING:\n    from sqlglot.schema import Schema\n    from collections.abc import Sequence, Mapping\n\n\nclass Resolver:", "new_string": "if t.TYPE_CHECKING:\n    from sqlglot.schema import Schema\
…[284 chars elided]…
eld in unpivot.fields\n        if isinstance(field, exp.In)\n        for e in field.expressions\n        for c in e.find_all(exp.Column)\n    }\n    new_columns = [c.output_name for c in unpivot.expressions] + [\n        field.this.output_name for field in unpivot.fields if isinstance(field, exp.In)\n    ]\n    return [c for c in columns if c not in in_columns] + new_columns\n\n\nclass Resolver:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/unpivot_check.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'t': {'id': 'int', 'jan': 'int', 'feb': 'int'}}, dialect='bigquery')\ncases = ['WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n         'WITH c AS (SELECT id, jan, feb FROM t) SELECT v
…[390 chars elided]…
\n        except Exception as e: print('ERR', e)\n    print()\nEOF\necho ORIG; PYTHONPATH=/tmp/sqlglot-orig <work>/env-sqlglot/bin/python /tmp/unpivot_check.py; echo NEW; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_check.py", "description": "Compare UNPIVOT qualify output before and after fixes"}
[tool_result] ORIG
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT * FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR Ambiguous column 'jan' (Line: 1, Col: 78)

WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`v` AS `v`, `c`.`m` AS `m` FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR Ambiguous column 'jan' (Line: 1, Col: 81)

WITH `c` A
…[472 chars elided]…
b`)) AS `t`

NEW
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
ERR Ambiguous column 'jan' (Line: 1, Col: 78)

ERR Ambiguous column 'jan' (Line: 1, Col: 81)
ERR Ambiguous column 'jan' (Line: 1, Col: 81)

ERR Ambiguous column 'jan' (Line: 1, Col: 82)
ERR Ambiguous column 'jan' (Line: 1, Col: 82)

SELECT * FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
[assistant] That fixed the schema case but broke the no-schema one. Removing the IN-list columns from the CTE's column set means the IN-list items (`jan`, `feb`) no longer resolve to the CTE, because they are inputs to the UNPIVOT, not outputs. The resolver should keep the CTE's columns and add the new names. I'll change the helper to do that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "def _unpivot_columns(columns: Sequence[str], unpivot: exp.Pivot) -> list[str]:\n    \"\"\"The columns produced by an UNPIVOT over a source with the given `columns`\"\"\"\n    in_columns = {\n        c.output
…[538 chars elided]…
 to an UNPIVOT's source: its own `columns`, which include the IN list\n    columns that are referenced by the UNPIVOT, plus the new names that the UNPIVOT produces.\n    \"\"\"\n    new_columns = [c.output_name for c in unpivot.expressions] + [\n        field.this.output_name for field in unpivot.fields if isinstance(field, exp.In)\n    ]\n    return list(dict.fromkeys([*columns, *new_columns]))"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    columns = _unpivot_columns(cte.expression.named_selects, unpivot)", "new_string": "                    columns = _unpivot_source_columns(cte.expression.named_selects, unpivot)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_check.py", "description": "Re-run UNPIVOT qualify cases with updated resolver"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v`, `c`.`m` AS `m`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v`, `c`.`m` AS `m`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS 
…[567 chars elided]…
(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c` WHERE `c`.`m` = 'jan'
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c` WHERE `c`.`m` = 'jan'

SELECT * FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
[assistant] Schema and no-schema now agree, but star expansion duplicates `v` and `m`: the expansion appends the UNPIVOT names to columns that already contain them. The expansion expects the pre-UNPIVOT column list, so the helper isn't needed. The resolver should return the CTE's own projections, and the rest of the existing logic handles the new names.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "def _unpivot_source_columns(columns: Sequence[str], unpivot: exp.Pivot) -> list[str]:\n    \"\"\"\n    The columns visible to an UNPIVOT's source: its own `columns`, which include the IN list\n    columns that are referenced by the UNPIVOT, plus the new names that the UNPIVOT produces.\n    \"\"\"\n    new_columns = [c.output_name for c in unpivot.expressions] + [\n        field.this.output_name for field in unpivot.fields if isinstance(field, exp.In)\n    ]\n    return list(dict.fromkeys([*columns, *new_columns]))\n\n\nclass Resolver:", "new_string": "class Resolver:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py", "old_string": "                # An UNPIVOTed CTE is kept as a Table, so its columns come from the CTE's projections\n                cte = self.scope.cte_sources.get(source.name)\n                unpivot = seq_get(source.
…[195 chars elided]…
 unpivot)", "new_string": "                # An UNPIVOTed CTE is kept as a Table, so its columns come from the CTE's projections\n                cte = self.scope.cte_sources.get(source.name)\n                pivot = seq_get(source.args.get(\"pivots\") or [], 0)\n                if cte and isinstance(pivot, exp.Pivot) and pivot.unpivot:\n                    columns = cte.expression.named_selects"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/unpivot_check.py", "description": "Re-run UNPIVOT qualify cases after simplifying resolver"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`

WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `
…[503 chars elided]…
(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c` WHERE `c`.`m` = 'jan'
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c` WHERE `c`.`m` = 'jan'

SELECT * FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
SELECT `t`.`id` AS `id`, `t`.`m` AS `m`, `t`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `t`
[assistant] All four cases now qualify correctly with and without a schema, and the star expansion matches the existing table behavior. Next I'll run the project's test command to see whether anything else moved.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with project's pytest command", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with project's pytest command", "timeout": 900000}
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
1092 passed, 17865 subtests passed in 49.63s
[assistant] The full suite passes (1092 tests). Now I'll add regression tests next to the existing UNPIVOT qualify fixtures.
[tool_use Bash] {"command": "grep -rn -i \"unpivot\" tests/fixtures/optimizer/qualify_columns.sql tests/test_optimizer.py | head -30", "description": "Find existing UNPIVOT qualify test fixtures"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln -i \"unpivot\" tests/ | head; grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql | head -20", "description": "Search tests for UNPIVOT references"}
[tool_result] tests/__pycache__/test_transpile.cpython-312-pytest-9.1.1.pyc
tests/dialects/test_snowflake.py
tests/dialects/test_databricks.py
tests/dialects/test_bigquery.py
tests/dialects/test_redshift.py
tests/dialects/test_oracle.py
tests/dialects/test_duckdb.py
tests/dialects/__pycache__/test_pipe_syntax.cpython-312-pytest-9.1.1.pyc
tests/dialects/__pycache__/test_databricks.cpython-312-pytest-9.1.1.pyc
tests/dialects/__pycache__/test_bigquery.cpython-312-pytest-9.1.1.pyc
tests/fixtures/optimizer/optimiz
…[1521 chars elided]…
N (`produce`.`q1`, `produce`.`q2`, `produce`.`q3`, `produce`.`q4`)) AS `produce`;
tests/fixtures/optimizer/optimizer.sql:761:# title: unpivoted table source with multiple value columns
tests/fixtures/optimizer/optimizer.sql:764:SELECT * FROM produce AS produce(product, q1, q2, q3, q4) UNPIVOT((first_half_sales, second_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'));
tests/fixtures/optimizer/optimizer.sql:771:UNPIVOT((`first_half_sales`, `second_half_sales`) FOR
[tool_use Bash] {"command": "sed -n 690,800p tests/fixtures/optimizer/optimizer.sql", "description": "Read existing UNPIVOT optimizer fixtures for format"}
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
…[2697 chars elided]…
`produce`.`q4`) AS 'semester_2'
  )
) AS `produce`;

# title: quoting is preserved
# dialect: snowflake
with cte1("id", foo) as (select 1, 2) select "id" from cte1;
WITH "CTE1" AS (
  SELECT
    1 AS "id"
)
SELECT
  "CTE1"."id" AS "id"
FROM "CTE1" AS "CTE1";

# title: ensures proper quoting happens after all optimizations
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
[assistant] The optimizer fixtures are full-pipeline outputs. The issue is about `qualify` specifically, so I'll check `qualify_columns.sql` and its test harness.
[tool_use Bash] {"command": "grep -n \"unpivot\\|pivot\" -i tests/fixtures/optimizer/qualify_columns.sql | head; tail -15 tests/fixtures/optimizer/qualify_columns.sql; grep -n \"qualify_columns.sql\" -B3 -A12 tests/test_optimizer.py | head -40", "description": "Inspect qualify_columns fixture format and harness"}
[tool_result] 269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 ORDER BY _0.EMPID;
593:# title: Expand PIVOT column combinations
595:WITH cities AS (SELECT * FROM (VALUES ('nl', 'amsterdam', 2000, 1005)) AS t(country, name, year, population)) SELECT * FROM cities PIVOT(SUM(population) AS total, COUNT(populat
…[1620 chars elided]…
 y ON x.b = y.b;

# title: SEMI + normal joins reinclude the table on scope
SELECT * FROM x SEMI JOIN y USING (b) JOIN y USING (b);
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x SEMI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;

# title: ANTI + normal joins reinclude the table on scope
SELECT * FROM x ANTI JOIN y USING (b) JOIN y USING (b);
SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;
[tool_use Bash] {"command": "grep -n \"def test_qualify_columns\\b\" -A 25 tests/test_optimizer.py", "description": "Read qualify_columns test harness to see schema usage"}
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
…[46 chars elided]…
      schema={
355-                    "raw": {
356-                        "TeamMemberships": {
357-                            "Id": "INTEGER",
358-                            "UserId": "INTEGER",
359-                            "TeamId": "INTEGER",
360-                        },
361-                        "Teams": {
362-                            "Id": "INTEGER",
363-                            "Name": "STRING",
364-                        },
365-                    }
366-                },
[tool_use Bash] {"command": "grep -n \"qualify_columns.sql\" -B2 -A10 tests/test_optimizer.py | head -30; grep -n \"def check_file\" -A 12 tests/test_optimizer.py | head -30", "description": "Find how qualify_columns fixture file is run"}
[tool_result] 148:    def check_file(
149-        self,
150-        file,
151-        func,
152-        pretty=False,
153-        execute=False,
154-        only=None,
155-        **kwargs,
156-    ):
157-        with ProcessPoolExecutor() as pool:
158-            results = {}
159-
160-            for i, (meta, sql, expected) in enumerate(
[tool_use Bash] {"command": "grep -n \"check_file(\" -B3 -A8 tests/test_optimizer.py | sed -n 1,80p | grep -n \"qualify_columns\\|schema\\|check_file\" ", "description": "Find check_file usages for qualify fixtures"}
[tool_result] 4:148:    def check_file(
17:232:        self.check_file(
20:235-            infer_schema=True,
23:238-            schema=schema,
27:242:        self.check_file(
30:245-            schema=self.schema,
40:302:        self.check_file(
53:338:        self.check_file("normalize", normalize, schema=self.schema)
56:341-    def test_qualify_columns(self, logger):
66:584:        self.check_file(
67:585-            "qualify_columns",
68:586-            qualify_columns,
70:588-            schema=self.schema,
72:590:        self.check_file("qualify_columns_ddl", qualify_columns, schema=self.schema)
[tool_use Bash] {"command": "grep -n \"self.schema = \" -A 12 tests/test_optimizer.py | head -20", "description": "Read the test schema used by qualify fixtures"}
[tool_result] 117:        self.schema = {
118-            "x": {
119-                "a": "INT",
120-                "b": "INT",
121-            },
122-            "y": {
123-                "b": "INT",
124-                "c": "INT",
125-            },
126-            "z": {
127-                "b": "INT",
128-                "c": "INT",
129-            },
[assistant] The fixture harness uses a shared schema where `x` has columns `a` and `b`. I'll add two fixtures in that file, one for the bare CTE case and one for selecting the new names, then check the generated output by hand.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.schema import MappingSchema\ns=MappingSchema({'x':{'a':'INT','b':'INT'}})\nfor sql in ['WITH c AS (SELECT a, b FROM x) SELECT * FROM c UNPIVOT(v FOR m IN (a, b))', 'WITH c AS (SELECT a, b FROM x) SELECT v, m FROM c UNPIVOT(v FOR m IN (a, b))']:\n    e=qualify_tables(sqlglot.parse_one(sql))\n    print(qualify_columns(e, s).sql(pretty=True))\n\"", "description": "Generate expected output for new fixture cases"}
[tool_result] WITH c AS (
  SELECT
    x.a AS a,
    x.b AS b
  FROM x AS x
)
SELECT
  c.m AS m,
  c.v AS v
FROM c AS c
UNPIVOT(v FOR m IN (c.a, c.b)) AS c
WITH c AS (
  SELECT
    x.a AS a,
    x.b AS b
  FROM x AS x
)
SELECT
  c.v AS v,
  c.m AS m
FROM c AS c
UNPIVOT(v FOR m IN (c.a, c.b)) AS c
[assistant] The output is consistent with the existing table-source fixture, which also orders the `FOR` column before the value column. Adding the fixtures:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/qualify_columns.sql", "old_string": "SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.c AS c FROM x AS x ANTI JOIN y AS y ON x.b = y.b JOIN y AS y_2 ON x.b = y_2.b;", "new_string": "SELECT x.a AS a, COALESCE(x.b, y_2.b) AS b, y_2.
…[280 chars elided]…
b AS b FROM x AS x) SELECT c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.a, c.b)) AS c;\n\n# title: UNPIVOT over a CTE, selecting the new columns qualifies them with the unpivoted source\nWITH c AS (SELECT a, b FROM x) SELECT v, m FROM c UNPIVOT(v FOR m IN (a, b));\nWITH c AS (SELECT x.a AS a, x.b AS b FROM x AS x) SELECT c.v AS v, c.m AS m FROM c AS c UNPIVOT(v FOR m IN (c.a, c.b)) AS c;"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/qualify_columns.sql has been updated successfully.
[assistant] Now I'll run the optimizer tests with the new fixtures, then run the new cases against the original source to confirm they catch the bug.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -30", "description": "Run optimizer tests including new fixtures", "timeout": 600000}
[tool_result] ...... [  7%]
.......................................................................                               [100%]
77 passed, 3709 subtests passed in 15.75s
[tool_use Bash] {"command": "cd /tmp/sqlglot-orig && cp -r ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1/tests /tmp/sqlglot-orig/ && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k qualify_columns 2>&1 | tail -4", "description": "Confirm new fixtures fail against original source", "timeout": 600000}
[tool_result] =========================== short test summary info ============================
SUBFAILED[UNPIVOT over a CTE, selecting the new columns qualifies them with the unpivoted source] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
SUBFAILED[UNPIVOT over a CTE, the new columns are not qualified and the IN list columns are] tests/test_optimizer.py::TestOptimizer::test_qualify_columns
2 failed, 3 passed, 74 deselected, 399 subtests passed in 2.48s
Shell cwd was reset to ~/.cache/lithify/work/repo-3abf279ffb90/20261029-141405-optimizer-select-from-cte-unpivo/base-1
[assistant] Against the original source, both new fixtures fail, and both pass with the fix. Now the full suite again, plus lint on the changed files.
[tool_use Bash] {"command": "rm -rf /tmp/sqlglot-orig /tmp/unpivot_check.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; (<work>/env-sqlglot/bin/ruff --version && <work>/env-sqlglot/bin/ruff check sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/resolver.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/resolver.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks on changed files", "timeout": 900000}
[tool_result] .............................................................................. [ 94%]
........................................................                                                [100%]
1092 passed, 17869 subtests passed in 54.47s
ruff 0.15.6
All checks passed!
Would reformat: sqlglot/optimizer/qualify_columns.py
1 file would be reformatted, 1 file already formatted
[assistant] All 1092 tests pass. Ruff wants to reformat `qualify_columns.py`; I'll look at the diff before applying it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --diff sqlglot/optimizer/qualify_columns.py 2>&1 | head -30", "description": "Preview ruff formatting diff for changed file"}
[tool_result] --- sqlglot/optimizer/qualify_columns.py
+++ sqlglot/optimizer/qualify_columns.py
@@ -653,7 +653,11 @@
 
     for pivot in scope.pivots:
         for column in pivot.find_all(exp.Column):
-            if not column.table and column.name in resolver.all_columns and id(column) not in unpivot_output_ids:
+            if (
+                not column.table
+                and column.name in resolver.all_columns
+                and id(column) not in unpivot_output_ids
+            ):
                 table = resolver.get_table(column.name)
                 if table:
                     column.set("table", table)

1 file would be reformatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format sqlglot/optimizer/qualify_columns.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/optimizer/ && <work>/env-sqlglot/bin/ruff check sqlglot/optimizer/ && git diff --stat && git diff sqlglot/", "description": "Apply formatting and show final source diff"}
[tool_result] 1 file reformatted
21 files already formatted
All checks passed!
sqlglot/optimizer/qualify_columns.py         | 14 +++++++++++++-
 sqlglot/optimizer/resolver.py                |  6 ++++++
 tests/fixtures/optimizer/qualify_columns.sql |  8 ++++++++
 3 files changed, 27 insertions(+), 1 deletion(-)
sqlglot/optimizer/qualify_columns.py | 14 +++++++++++++-
 sqlglot/optimizer/resolver.py        |  6 ++++++
 2 files changed, 19 insertions(+), 1 deletion(-)

--- Changes ---

sqlglot/optimizer/qualify_c
…[1352 chars elided]…
           pivot = seq_get(source.args.get("pivots") or [], 0)
  +                if cte and isinstance(pivot, exp.Pivot) and pivot.unpivot:
  +                    columns = cte.expression.named_selects
               elif isinstance(source, Scope) and isinstance(
                   source_expr := source.expression, (exp.Values, exp.Unnest, exp.Lateral)
               ):
  +6 -0
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] The file change the harness mentioned is just my own `ruff format` run. I'll re-run the suite once more after formatting.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Re-run full test suite after formatting", "timeout": 900000}
[tool_result] ........................................................                                                [100%]
1092 passed, 17869 subtests passed in 55.44s
[assistant] `qualify` now handles `UNPIVOT` over a CTE. The example from the issue comes out correctly in BigQuery, DuckDB and Snowflake, and the full suite passes (1092 tests).

**Before:** the new names were qualified with the CTE alias:
```sql
... FROM `c` AS `c` UNPIVOT(`c`.`v` FOR `c`.`m` IN (`c`.`jan`, `c`.`feb`))
```
**After:**
```sql
... FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
```

There were two causes:

1. **`sqlglot/optimizer/qualify_columns.py`:** the `v` and `m` columns were unqualified, so the resolver assigned them to the only source. They are now left alone, m
…[195 chars elided]…
ed CTE's columns came back empty, so `jan` was reported as ambiguous. This failed on unmodified HEAD too. The resolver now uses the CTE's projections for an UNPIVOTed CTE. Pivoted CTEs that are not UNPIVOTs are unchanged.

**Tests:** I added two cases to `tests/fixtures/optimizer/qualify_columns.sql`: the bare `SELECT *` from the issue, and selecting `v, m` explicitly. Both fail on the original source and pass now. I did not edit any existing test.

Not done: I haven't run this against real BigQuery, DuckDB or Snowflake, only through sqlglot's own generation. I also haven't committed anything.
