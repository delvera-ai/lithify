# trajectory base-1

final message:
The Spark `LATERAL VIEW EXPLODE` case from the report now optimizes instead of raising. The fix is in `sqlglot/optimizer/qualify_columns.py`, with a regression test in `tests/test_optimizer.py`. The full suite passed (1093 tests) before a final comment-only edit. I then re-ran the optimizer and dialect tests and ruff check and format, and all passed. I did not commit.

```
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci
→ SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Cause:** the optimizer's `isolate_table_selects` step wraps `my_table` in a subquery, and that subquery is never typed. So the lateral's exploded struct stayed UNKNOWN, and `ci.name` was rejected as an unknown column of `ci`. Separately, `ci` is already a source, so the existing struct-to-dot conversion skipped it.

**Changes:**
- **Typing:** when qualification reaches a lateral scope, it now annotates that scope's source subqueries and then the lateral itself, so the exploded element type is known.
- **Field access:** a `table.field` reference whose table is a lateral alias over a struct becomes a struct field access, but only if the struct actually has that field. `ci.foo` still raises `Unknown column: foo`.

**Choices I made:**
- I restricted the field-access rewrite to exploded struct aliases rather than treating every unknown `x.y` as a struct access. That keeps validation intact for non-struct and missing-field cases.
- I did not change how the lateral alias column is typed. It still takes the array's type rather than the element type. This doesn't affect the reported case, but it is a related inaccuracy you may want fixed separately.

## events
[assistant] I'll reproduce the failure first, then trace it through the optimizer.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nprint(optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[82 chars elided]…
^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
[assistant] Reproduced: `Unknown column: name`, raised from `qualify_columns`. Next I'll look at how lateral view aliases are handled there.
[tool_use Bash] {"command": "grep -n \"Lateral\\|explode\\|Explode\\|_expand_alias_refs\\|def \\|is_type\\|annotate\" sqlglot/optimizer/qualify_columns.py | head -120; echo ---; sed -n 580,630p sqlglot/optimizer/qualify_columns.py", "description": "Inspect qualify_columns lateral and unknown-column logic"}
[tool_result] 10:from sqlglot.optimizer.annotate_types import TypeAnnotator
21:def qualify_columns(
77:            _expand_alias_refs(
92:            _expand_alias_refs(scope, resolver, dialect)
112:            annotator.annotate_scope(scope)
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
169:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
191:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Column]:
202:def _pop_table_column_aliases(derived_t
…[3236 chars elided]…
  if scope.pivots and not column.find_ancestor(exp.Pivot):
                # If the column is under the Pivot expression, we need to qualify it
                # using the name of the pivoted source instead of the pivot's alias
                column.set("table", exp.to_identifier(scope.pivots[0].alias))
                continue

            # column_table can be a '' because bigquery unnest has no table alias
            table = resolver.get_table(column)

            if (
                table
[tool_use Bash] {"command": "grep -n \"Lateral\\|explode\\|Explode\\|unnest\\|Unnest\" sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py sqlglot/optimizer/annotate_types.py sqlglot/optimizer/qualify.py | head -60; echo ---; grep -n \"LATERAL VIEW\\|LateralView\\|lateral_view\\|EXPLODE\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/parser.py | head -40", "description": "Find lateral view handling across optimizer and parser"}
[tool_result] sqlglot/optimizer/qualify_tables.py:120:            unnested = derived_table.unnest()
sqlglot/optimizer/qualify_tables.py:121:            if isinstance(unnested, exp.Table):
sqlglot/optimizer/qualify_tables.py:122:                joins = unnested.args.get("joins")
sqlglot/optimizer/qualify_tables.py:123:                unnested.set("joins", None)
sqlglot/optimizer/qualify_tables.py:124:                derived_table.this.replace(exp.select("*").from_(unnested.copy(), copy=False))
sqlglot/optimize
…[748 chars elided]…
ptimizer/annotate_types.py:304:                        isinstance(expression, exp.Unnest)
sqlglot/optimizer/annotate_types.py:420:                    elif isinstance(source.expression, exp.Unnest):
sqlglot/optimizer/annotate_types.py:778:    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
sqlglot/optimizer/annotate_types.py:782:    def _annotate_unnest(self, expression: exp.Unnest) -> exp.Unnest:
sqlglot/optimizer/annotate_types.py:797:        query = expression.unnest()
---
[tool_use Bash] {"command": "sed -n 270,330p sqlglot/optimizer/annotate_types.py; echo ---; sed -n 405,435p sqlglot/optimizer/annotate_types.py; echo ---; sed -n 775,790p sqlglot/optimizer/annotate_types.py; echo ---; sed -n 180,200p sqlglot/optimizer/scope.py; echo ---; sed -n 880,900p sqlglot/optimizer/scope.py; echo ---; sed -n 135,150p sqlglot/optimizer/scope.py", "description": "Read annotate_types lateral/explode and scope lateral code"}
[tool_result]         # Replace NULL type with the default type of the targeted dialect, since the former is not an actual type;
        # it is mostly used to aid type coercion, e.g. in query set operations.
        # TODO (mypyc): uses list() + _set_type instead of direct expr.type = ... because
        # mypyc's property setter bypass rejects DType, and _set_type modifies the dict.
        for expr in list(self._null_expressions.values()):
            self._set_type(expr, self.dialect.DEFAULT_NULL_TYPE)

 
…[6716 chars elided]…
olumns: list[str] | None = None,
    ) -> Scope:
        """Branch from the current scope to a new, inner scope"""
        return Scope(
            expression=expression.unnest(),
            sources=sources.copy() if sources else None,
            parent=self,
            scope_type=scope_type,
            cte_sources={**self.cte_sources, **(cte_sources or {})},
            lateral_sources=lateral_sources.copy() if lateral_sources else None,
            can_be_correlated=self.can_be_correlated
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark')\nprint(repr(e))\n\"", "description": "Print parsed AST for the lateral view query"}
[tool_result] Select(
  expressions=[
    Column(
      this=Identifier(this=name, quoted=False),
      table=Identifier(this=ci, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=my_table, quoted=False))),
  laterals=[
    Lateral(
      this=Explode(
        this=Column(
          this=Identifier(this=items, quoted=False))),
      view=True,
      outer=False,
      alias=TableAlias(
        this=Identifier(this=ci, quoted=False),
        columns=[
          Identifier(this=ci, quoted=False)]))])
[assistant] The AST shows the lateral alias is both table and column `ci`, and `ci.name` is a struct field access on that column. Next I'll check how `_convert_columns_to_dots` handles struct access, since that is the path that should catch it.
[tool_use Bash] {"command": "sed -n 21,116p sqlglot/optimizer/qualify_columns.py; echo ---; sed -n 549,580p sqlglot/optimizer/qualify_columns.py", "description": "Read qualify_columns entry and dot conversion"}
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
…[3602 chars elided]…
ot in scope.parent.sources
                or not scope.is_correlated_subquery
            )
        ):
            root, *parts = column.parts

            if isinstance(root, exp.Identifier) and root.name in scope.sources:
                # The struct is already qualified, but we still need to change the AST
                column_table = root
                root, *parts = parts
                was_qualified = True
            else:
                column_table = resolver.get_table(root.name)
[assistant] `_convert_columns_to_dots` skips `ci.name` because `ci` is already a source, and `_qualify_columns` then rejects `name` because the lateral's only column is `ci`. Before choosing a fix, I'll check which nearby variants already work, so I know the intended behavior.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor sql in [\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS item',\n 'SELECT item.name FR
…[313 chars elided]…
_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n  except Exception as e:\n    print('ERR', sql, '->', type(e).__name__, e)\n\" 2>&1 | tail -20; git log --oneline -3 -- sqlglot/optimizer/qualify_columns.py; grep -rn \"LATERAL VIEW\" tests/*.py tests/dialects/*.py | grep -i \"optimiz\\|qualif\" | head", "description": "Test nearby lateral view variants for expected behavior"}
[tool_result] ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS item -> OptimizeError Unknown column: name
OK  SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci -> OptimizeError Unknown column: name
OK  SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci -> OptimizeError Unknown column: name
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
c31e2e3a6 Refactor(Optimizer): improve typing coverage of optimizer modules (#7446)
f7bb6bea8 chore: use collections.abc and built-in types for typing to avoid deprecation (#7329)
tests/test_optimizer.py:1340:            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
[assistant] Both `AS ci` and `AS item` fail in different ways, and only the `ci.item` version qualifies. The issue wants `ci.name` to resolve as a struct field on the exploded `ci` column. I'll look at the `Resolver` and how it exposes source column types before choosing where the fix goes.
[tool_use Bash] {"command": "grep -n \"class Resolver\" -A 12 sqlglot/optimizer/resolver.py | head -30; grep -n \"def \\|_get_scope_selects\\|get_source_columns\" sqlglot/optimizer/resolver.py | head -60", "description": "Inspect Resolver source column lookup"}
[tool_result] 17:class Resolver:
18-    """
19-    Helper for resolving columns.
20-
21-    This is a class so we can lazily load some things and easily share them across functions.
22-    """
23-
24-    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True):
25-        self.scope = scope
26-        self.schema = schema
27-        self.dialect = schema.dialect or Dialect()
28-        self._source_columns: dict[str, Sequence[str]] | None = None
29-        self._unambiguous_columns: Mapping
…[1206 chars elided]…
context(self, column: exp.Column) -> exp.Join | None:
255:    def _get_available_source_columns(self, join_ancestor: exp.Join) -> dict[str, Sequence[str]]:
277:        available_sources = {from_name: self.get_source_columns(from_name)}
280:            available_sources[join.alias_or_name] = self.get_source_columns(join.alias_or_name)
284:    def _get_unambiguous_columns(
341:    def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:
368:    def _get_column_type_from_scope(
[tool_use Bash] {"command": "sed -n 133,203p sqlglot/optimizer/resolver.py; echo ---; sed -n 341,400p sqlglot/optimizer/resolver.py", "description": "Read Resolver source-column and type lookup"}
[tool_result]     def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._get_source_columns_cache:
            if name not in self.scope.sources:
                raise OptimizeError(f"Unknown table: {name}")

            source = self.scope.sources[name]

            if isinstance(source, exp.Table):
                columns = self.schema.
…[5058 chars elided]…
umn_type(source, column)
            if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                return col_type
        elif isinstance(source, Scope):
            # iterate over all sources in the scope
            for source_name, nested_source in source.sources.items():
                col_type = self._get_column_type_from_scope(nested_source, column)
                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                    return col_type

        return None
[assistant] The Resolver only knows column names for a lateral alias, not types, and `_get_scope_selects` uses the array column's type rather than the exploded element type. I'll check what the annotator produces for the Explode and the alias before deciding the fix.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglo
…[126 chars elided]…
i.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark')\ne = annotate_types(e, schema=schema, dialect='spark')\nex = e.find(exp.Explode)\nprint('explode type', ex.type.sql('spark'), '| items type', ex.this.type.sql('spark'))\nfor s in traverse_scope(e):\n    print(s.expression.key, list(s.sources))\n\" 2>&1 | tail -20", "description": "Check annotated types for the explode node"}
[tool_result] explode type UNKNOWN | items type UNKNOWN
lateral ['my_table']
select ['my_table', 'ci']
[assistant] The schema-only annotation leaves `items` as UNKNOWN because the column isn't qualified yet, so the type has to be filled in during qualification. I'll check how the annotator is driven per scope and what `ANNOTATE_ALL_SCOPES` controls.
[tool_use Bash] {"command": "grep -rn \"ANNOTATE_ALL_SCOPES\" sqlglot | head; echo ---; grep -n \"def annotate_scope\" -A 40 sqlglot/optimizer/annotate_types.py | head -60", "description": "Check ANNOTATE_ALL_SCOPES and annotate_scope"}
[tool_result] sqlglot/optimizer/qualify_columns.py:111:        if dialect.ANNOTATE_ALL_SCOPES:
sqlglot/dialects/dialect.py:495:    ANNOTATE_ALL_SCOPES = False
sqlglot/dialects/bigquery.py:35:    ANNOTATE_ALL_SCOPES = True
---
328:    def annotate_scope(self, scope: Scope) -> None:
329-        if isinstance(self.schema, MappingSchema):
330-            for table_column in scope.table_columns:
331-                source = scope.sources.get(table_column.name)
332-
333-                if isinstance(source, exp.Tab
…[1296 chars elided]…
te_expression(scope.expression, scope)
360-        self._fixup_order_by_aliases(scope)
361-
362-        if self.dialect.QUERY_RESULTS_ARE_STRUCTS and isinstance(scope.expression, exp.Query):
363-            struct_type = exp.DataType(
364-                this=exp.DType.STRUCT,
365-                expressions=[
366-                    exp.ColumnDef(
367-                        this=exp.to_identifier(select.output_name),
368-                        kind=select.type.copy() if select.type else None,
[assistant] The annotator only runs per scope at the end of `qualify_columns` (and only for BigQuery), so the Explode's type is never known while the select scope is qualified. My plan:

1. In `qualify_columns`, annotate a lateral scope right after its columns are qualified, so the Explode gets the element type.
2. In `_convert_columns_to_dots`, rewrite `ci.name` as a struct field access when `ci` is a lateral alias whose exploded element is a struct and has no `name` column of its own.

I'll make the edits and then test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        _qualify_columns(\n            scope,\n            resolver,\n            allow_partial_qualification=allow_partial_qualification,\n        )\n\n        if not schema.empty and expand_alias_ref
…[26 chars elided]…
  _qualify_columns(\n            scope,\n            resolver,\n            allow_partial_qualification=allow_partial_qualification,\n        )\n\n        if isinstance(scope_expression, exp.Lateral):\n            # Annotate the exploded expression so its struct type is known to the enclosing scope\n            annotator.annotate_scope(scope)\n\n        if not schema.empty and expand_alias_refs:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            if column_table:\n                converted = True\n                new_column = exp.column(root, table=column_table)\n\n                if dot_parts:\n                    # Remove the actu
…[782 chars elided]…
lver.get_source_columns(column_table)\n            and _is_exploded_struct_alias(scope.sources[column_table], column_table)\n        ):\n            # e.g. `LATERAL VIEW EXPLODE(structs) t AS t`, where `t.field` is a struct field lookup\n            converted = True\n            column.replace(exp.Dot.build([exp.column(column_table, table=column_table), column.this.copy()]))\n\n    if converted:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] The new `elif` sits at the same level as the outer `if`, so it only runs for qualified columns whose table is already a source. Next I'll add the helper it calls.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:", "new_string": "def _is_exploded_struct_alias(source: exp.Table | Scope, name: str) -> bool:\n    expression = source.expression if isinstance(source, Scope) else None\n    return (\n        isinstance(expression, exp.Lateral)\n        and isinstance(expression.this, exp.Explode)\n        and expression.this.is_type(exp.DType.STRUCT)\n        and name in expression.alias_column_names\n    )\n\n\ndef _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor sql in [\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n 'SELECT ci.name FROM m
…[71 chars elided]…
OM my_table LATERAL VIEW EXPLODE(items) ci AS item',\n 'SELECT ci FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n]:\n  try:\n    print('OK ', optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n  except Exception as e:\n    print('ERR', sql, '->', type(e).__name__, e)\n\" 2>&1 | tail -20", "description": "Re-run lateral view variants after the fix"}
[tool_result] ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci -> OptimizeError Unknown column: name
ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS item -> OptimizeError Unknown column: name
OK  SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
OK  SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
[assistant] The target case still fails, so one of my assumptions is wrong. I'll check whether the Explode is typed when the select scope is converted.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nimport sqlglot.optimizer.qualify_columns as qc\norig = qc._convert_columns_to_dots\ndef dbg(scope, resolver):\n    print('scope', scope.expression.key, list(scope.sources), [ (c.sql(), c.
…[354 chars elided]…
t_columns_to_dots = dbg\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ntry:\n  optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nexcept Exception as e: print(e)\n\" 2>&1 | tail -20", "description": "Debug the explode type during column conversion"}
[tool_result] scope select ['my_table'] []
scope lateral ['my_table'] [('items', '')]
scope select ['my_table', 'ci'] [('ci.name', 'ci'), ('my_table.items', 'my_table'), ('my_table.items', 'my_table')]
 lateral explode type: UNKNOWN alias cols ['ci'] this type UNKNOWN
Unknown column: name
[assistant] The lateral scope runs first and `items` gets qualified, but the Explode is still UNKNOWN. I'll check directly whether annotating that scope types the Explode.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_types import TypeAnnotator\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.schema import ensure_schema\nfrom sqlglot.optimizer.qualify im
…[362 chars elided]…
e', lat.this.this.this.type if lat.this.this else None)\nann = TypeAnnotator(schema)\nfor s in traverse_scope(e):\n    if isinstance(s.expression, exp.Lateral):\n        ann.annotate_scope(s)\n        print('explode after', lat.this.type, '| items', lat.this.this.type, '| col', lat.this.this.table)\n\" 2>&1 | tail -20", "description": "Check whether annotating the lateral scope types the Explode"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
items type before UNKNOWN
explode after STRUCT<name TEXT> | items ARRAY<STRUCT<name TEXT>> | col my_table
[assistant] Annotating the lateral scope after qualification does type the Explode as a struct, so the problem is in the sequence inside `qualify_columns`. I'll print the Explode type right after my new annotate call.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nimport sqlglot.optimizer.annotate_types as at\norig = at.TypeAnnotator.annotate_scope\ndef dbg(self, scope):\n    r = orig(self, scope)\n    if isinstance(scope.expression, exp.Lateral):\
…[229 chars elided]…
rom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ntry:\n  print(optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark').sql('spark'))\nexcept Exception as e: print(e)\n\" 2>&1 | tail -20", "description": "Trace annotation of the lateral scope during optimize"}
[tool_result] annotated lateral; explode type UNKNOWN items type UNKNOWN items table my_table
Unknown column: name
[assistant] The lateral scope is annotated, and `items` now has the right table, but its type is still UNKNOWN. I'll look at how the annotator types a column to see why.
[tool_use Bash] {"command": "sed -n 380,405p sqlglot/optimizer/annotate_types.py; grep -n \"def _set_type\\|def _maybe_annotate\\|def _annotate_expression\" -A 12 sqlglot/optimizer/annotate_types.py | head -80", "description": "Read column annotation and set-type helpers"}
[tool_result]                 # annotations, i.e., it shouldn't be interpreted as a STRUCT value.
                scope.expression.meta["query_type"] = struct_type

    def _annotate_expression(
        self,
        expression: exp.Expr,
        scope: Scope | None = None,
    ) -> None:
        stack = [(expression, False)]

        while stack:
            expr, children_annotated = stack.pop()

            if id(expr) in self._visited or (
                not self._overwrite_types and expr.type and not ex
…[1071 chars elided]…
)
248-        self._visited.add(expression_id)
249-
--
383:    def _annotate_expression(
384-        self,
385-        expression: exp.Expr,
386-        scope: Scope | None = None,
387-    ) -> None:
388-        stack = [(expression, False)]
389-
390-        while stack:
391-            expr, children_annotated = stack.pop()
392-
393-            if id(expr) in self._visited or (
394-                not self._overwrite_types and expr.type and not expr.is_type(exp.DType.UNKNOWN)
395-            ):
[assistant] `_annotate_expression` skips nodes already in `self._visited`, and the annotator is shared across the whole `qualify_columns` call. I'll check whether `items` was already visited with UNKNOWN before my call.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nimport sqlglot.optimizer.annotate_types as at\norig = at.TypeAnnotator.annotate_scope\ndef dbg(self, scope):\n    if isinstance(scope.expression, exp.Lateral):\n        col = scope.expres
…[245 chars elided]…
nnotate_scope = dbg\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ntry:\n  optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nexcept Exception as e: print(e)\n\" 2>&1 | tail -20", "description": "Check visited state before annotating lateral scope"}
[tool_result] before: visited False overwrite True type None sources {'my_table': 'Scope'}
Unknown column: name
[assistant] The lateral scope's `my_table` source is a `Scope`, not a `Table`, so the annotator takes the scope-selects branch and never finds `items`. I'll check what that scope wraps during `optimize`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nimport sqlglot.optimizer.annotate_types as at\norig = at.TypeAnnotator.annotate_scope\ndef dbg(self, scope):\n    if isinstance(scope.expression, exp.Lateral):\n        s = scope.sources[
…[276 chars elided]…
mport optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ntry:\n  optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nexcept Exception as e: print(e)\n\" 2>&1 | tail -20; sed -n 402,412p sqlglot/optimizer/scope.py", "description": "Inspect the scope wrapping my_table in lateral scope"}
[tool_result] source expr Select SELECT my_table.items AS items FROM my_table AS my_table selects [Alias(
  this=Column(
    this=Identifier(this=items, quoted=False),
    table=Identifier(this=my_table, quoted=False)),
  alias=Identifier(this=items, quoted=False))]
Unknown column: name
            for table in self.tables:
                self._references.append((table.alias_or_name, table))
            for _expr in itertools.chain(self.derived_tables, self.udtfs):
                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
                expression: exp.Expr = _expr
                self._references.append(
                    (
                        _get_source_alias(expression),
                        (
                            expression if expression.args.get("pivots") else expression.unnest()
                        ).assert_is(exp.Selectable),
[assistant] The `isolate_table_selects` step wraps `my_table` in a `SELECT my_table.items AS items FROM my_table` subquery, and that subquery is never annotated. So the lateral's annotation finds no type for `items`. I'll annotate the lateral's source scopes first, then the lateral scope itself.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if isinstance(scope_expression, exp.Lateral):\n            # Annotate the exploded expression so its struct type is known to the enclosing scope\n            annotator.annotate_scope(scope)", "new_string": "        if isinstance(scope_expression, exp.Lateral):\n            # Annotate the exploded expression (and its sources) so its struct type is known to the enclosing scope\n            for source in scope.sources.values():\n                if isinstance(source, Scope):\n                    annotator.annotate_scope(source)\n            annotator.annotate_scope(scope)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor sql in [\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n 'SELECT ci.name FROM m
…[151 chars elided]…
LATERAL VIEW EXPLODE(items) ci AS ci',\n 'SELECT ci.foo FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n]:\n  try:\n    print('OK ', optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n  except Exception as e:\n    print('ERR', sql, '->', type(e).__name__, e)\n\" 2>&1 | tail -20", "description": "Re-test lateral view variants with source annotation"}
[tool_result] OK  SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS item -> OptimizeError Unknown column: name
OK  SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
OK  SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
OK  SELECT `ci`.`ci`.`foo` AS `foo` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
[assistant] The target query now works, but the check is too loose: `ci.foo`, a field the struct doesn't have, now passes instead of raising. I'll tighten the helper to require the struct to actually contain the accessed field.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "def _is_exploded_struct_alias(source: exp.Table | Scope, name: str) -> bool:\n    expression = source.expression if isinstance(source, Scope) else None\n    return (\n        isinstance(expression, exp
…[263 chars elided]…
field: str) -> bool:\n    expression = source.expression if isinstance(source, Scope) else None\n    return (\n        isinstance(expression, exp.Lateral)\n        and isinstance(expression.this, exp.Explode)\n        and alias in expression.alias_column_names\n        and expression.this.is_type(exp.DType.STRUCT)\n        and any(f.name == field for f in expression.this.type.expressions)\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            and _is_exploded_struct_alias(scope.sources[column_table], column_table)", "new_string": "            and _is_exploded_struct_field(scope.sources[column_table], column_table, column.name)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Now I'll re-run the variants, including the invalid-field case, which should raise again.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor sql in [\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n 'SELECT ci.name FROM m
…[3 chars elided]…
able LATERAL VIEW EXPLODE(items) ci AS item',\n 'SELECT ci.foo FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n]:\n  try:\n    print('OK ', optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n  except Exception as e:\n    print('ERR', sql, '->', type(e).__name__, e)\n\" 2>&1 | tail -20", "description": "Verify target and invalid-field lateral cases"}
[tool_result] OK  SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
ERR SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS item -> OptimizeError Unknown column: name
ERR SELECT ci.foo FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci -> OptimizeError Unknown column: foo
[assistant] Both the target case and the invalid-field case behave correctly now. Next I'll add a regression test next to the existing lateral-explode optimizer test.
[tool_use Bash] {"command": "sed -n 1325,1350p tests/test_optimizer.py; grep -n \"def test_\" tests/test_optimizer.py | awk -F: '$1>1200 && $1<1400'", "description": "Read the existing lateral explode optimizer test"}
[tool_result]                 "SELECT DATE_TRUNC('DAY', '2023-01-01') FROM x AS x",
                exp.DataType.Type.DATE,
            ),
            (
                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
                exp.DataType.Type.INT,
            ),
        ]:
            with self.subTest(sql):
                expression = annotate_types(parse_one(sql), schema=schema)
                self.assertEqual(expected_type, expression.expressions[0].type.this)
                self
…[388 chars elided]…
T"}, "y": {"cola": "FLOAT"}}
        sql = """
            SELECT a.cola AS cola
            FROM (
                SELECT x.cola + y.cola AS cola
                FROM (
1204:    def test_binary_annotation(self):
1219:    def test_typeddiv_annotation(self):
1235:    def test_bracket_annotation(self):
1276:    def test_interval_math_annotation(self):
1338:    def test_lateral_annotation(self):
1344:    def test_derived_tables_column_annotation(self):
1376:    def test_cte_column_annotation(self):
[assistant] I'll add a regression test that exercises the exact reported query, placed beside the existing lateral test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n
…[254 chars elided]…
W EXPLODE(items) ci AS ci\", read=\"spark\"\n            ),\n            schema=schema,\n            dialect=\"spark\",\n        )\n        self.assertEqual(\n            expression.sql(\"spark\"),\n            \"SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`\",\n        )\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run the full project test suite"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
...........................................................................................................................
…[331 chars elided]…
........................................................................... [ 77%]
............................................. [ 81%]
.... [ 81%]
............................ [ 84%]
.......................................... [ 87%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
.........                                                           [100%]
1093 passed, 17857 subtests passed in 58.59s
[assistant] All 1093 tests pass. Next I'll run the project's formatter and linter on the two changed files, since one of my lines is over the length limit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff --version && $PY -m ruff format sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && $PY -m ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py; git diff --stat", "description": "Format and lint the changed files"}
[tool_result] ruff 0.15.6
1 file reformatted, 1 file left unchanged
All checks passed!
 sqlglot/optimizer/qualify_columns.py | 29 +++++++++++++++++++++++++++++
 tests/test_optimizer.py              | 14 ++++++++++++++
 2 files changed, 43 insertions(+)
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] Ruff reformatted `qualify_columns.py`. I'll review the final diff to confirm the change is what I intended.
[tool_use Bash] {"command": "git diff -- sqlglot/optimizer/qualify_columns.py", "description": "Show the final diff for the optimizer change"}
[tool_result] diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index ea09866bc..e386a7e7c 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -88,6 +88,13 @@ def qualify_columns(
             allow_partial_qualification=allow_partial_qualification,
         )
 
+        if isinstance(scope_expression, exp.Lateral):
+            # Annotate the exploded expression (and its sources) so its struct type is known to the enclosing sc
…[1556 chars elided]…
able)
+            and _is_exploded_struct_field(scope.sources[column_table], column_table, column.name)
+        ):
+            # e.g. `LATERAL VIEW EXPLODE(structs) t AS t`, where `t.field` is a struct field lookup
+            converted = True
+            column.replace(
+                exp.Dot.build([exp.column(column_table, table=column_table), column.this.copy()])
+            )
 
     if converted:
         # We want to re-aggregate the converted columns, otherwise they'd be skipped in
[assistant] The logic is right. The comment line is long, so I'll shorten it to match the file's style, then re-run the optimizer and qualify tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            # Annotate the exploded expression (and its sources) so its struct type is known to the enclosing scope", "new_string": "            # Type the exploded expression so its struct fields are visible to the enclosing scope"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-135653-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && $PY -m ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py tests/test_transpile.py tests/dialects 2>&1 | tail -3", "description": "Recheck formatting, lint, and optimizer tests"}
[tool_result] 2 files already formatted
All checks passed!
......................................................... [ 97%]
....................             [100%]
831 passed, 15717 subtests passed in 21.43s
[assistant] The Spark `LATERAL VIEW EXPLODE` case from the report now optimizes instead of raising. The fix is in `sqlglot/optimizer/qualify_columns.py`, with a regression test in `tests/test_optimizer.py`. The full suite passed (1093 tests) before a final comment-only edit. I then re-ran the optimizer and dialect tests and ruff check and format, and all passed. I did not commit.

```
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci
→ SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Cause:** the optimizer's `isolate
…[525 chars elided]…
able is a lateral alias over a struct becomes a struct field access, but only if the struct actually has that field. `ci.foo` still raises `Unknown column: foo`.

**Choices I made:**
- I restricted the field-access rewrite to exploded struct aliases rather than treating every unknown `x.y` as a struct access. That keeps validation intact for non-struct and missing-field cases.
- I did not change how the lateral alias column is typed. It still takes the array's type rather than the element type. This doesn't affect the reported case, but it is a related inaccuracy you may want fixed separately.
