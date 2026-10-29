# trajectory base-1

final message:
`optimize()` no longer raises for the `LATERAL VIEW EXPLODE` case in the report. The full suite passes (1093 tests, 17857 subtests), and ruff and mypy are clean on the changed files.

**Root cause:** when the table alias and the column alias are both `ci`, `ci.name` is treated as a column of the `ci` source. The qualifier-to-struct rewrite skips any qualifier that is already a source, and the exploded alias was typed as the raw `ARRAY<STRUCT<...>>` rather than the struct element. So `name` was never found and qualification raised.

**Changes:**
- **`sqlglot/optimizer/resolver.py`:** new `is_lateral_struct_field()`. It returns true when `ci.<field>` refers to a field of the struct that an explode alias produces under a same-named column, by reading the exploded array's type from the schema.
- **`sqlglot/optimizer/qualify_columns.py`:** `_convert_columns_to_dots` rewrites such a column to `ci.ci.name`, which is how Spark resolves it.
- **`sqlglot/optimizer/annotate_types.py`:** an exploded `ARRAY` alias now gets its element type instead of the array type. The output for the example is typed `TEXT`, not `UNKNOWN`. Non-array explodes keep their existing type, so `test_lateral_annotation` is unaffected.
- **`tests/test_optimizer.py`:** added `test_lateral_explode_struct_field_access`, which checks the rewritten SQL and the `TEXT` type. No existing tests were edited.

**Output for the example:**
```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Intentional behavior:** `LATERAL VIEW EXPLODE(items) ci AS item` with `SELECT ci.name` still raises. Spark would also reject it, since `ci` has no `name` column. The working path there is `item.name`, which I confirmed still qualifies.

I have not committed anything.

## events
[assistant] I'll reproduce the failure first, then trace it through the Spark/Hive lateral view and optimizer code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nprint(optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[82 chars elided]…
^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
[assistant] Reproduced: `OptimizeError: Unknown column: name`. Next I'll look at how the parser represents this `LATERAL VIEW` and how column qualification treats it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark')\nprint(repr(e))\nprint(e.sql('spark'))\n\" 2>&1; grep -rn \"Lateral\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/parser.py | head -40; grep -rn \"lateral\" sqlglot/optimizer/*.py | head -40", "description": "Inspect parsed LATERAL VIEW tree and related code"}
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
          Identifier(this=ci, quote
…[1153 chars elided]…
r/scope.py:149:            lateral_sources=lateral_sources.copy() if lateral_sources else None,
sqlglot/optimizer/scope.py:802:    expressions.extend(scope.expression.args.get("laterals") or [])
sqlglot/optimizer/scope.py:837:            lateral_sources = sources
sqlglot/optimizer/scope.py:841:            lateral_sources = None
sqlglot/optimizer/scope.py:856:                lateral_sources=lateral_sources,
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "sed -n 4266,4325p sqlglot/parser.py; echo ----; sed -n 790,830p sqlglot/optimizer/scope.py; echo ----; grep -n \"Lateral\\|lateral\\|explode\\|Explode\\|UNNEST\\|Unnest\" sqlglot/optimizer/annotate_types.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/qualify_tables.py | head -40", "description": "Read lateral parser and scope code"}
[tool_result]     def _parse_lateral(self) -> exp.Lateral | None:
        cross_apply: bool | None = None
        if self._match_pair(TokenType.CROSS, TokenType.APPLY):
            cross_apply = True
        elif self._match_pair(TokenType.OUTER, TokenType.APPLY):
            cross_apply = False

        if cross_apply is not None:
            this = self._parse_select(table=True)
            view = None
            outer = None
        elif self._match(TokenType.LATERAL):
            this = self._parse_selec
…[3594 chars elided]…
 isinstance(expression, exp.Unnest):
sqlglot/optimizer/annotate_types.py:304:isinstance(expression, exp.Unnest)
sqlglot/optimizer/annotate_types.py:420:elif isinstance(source.expression, exp.Unnest):
sqlglot/optimizer/annotate_types.py:778:def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
sqlglot/optimizer/annotate_types.py:782:def _annotate_unnest(self, expression: exp.Unnest) -> exp.Unnest:
sqlglot/optimizer/qualify_columns.py:530:or select_expr.find(exp.Explode, exp.Unnest)
[tool_use Bash] {"command": "sed -n 270,320p sqlglot/optimizer/annotate_types.py; echo ----; sed -n 405,440p sqlglot/optimizer/annotate_types.py; echo ----; sed -n 770,790p sqlglot/optimizer/annotate_types.py; echo ----; sed -n 520,540p sqlglot/optimizer/qualify_columns.py; echo ----; grep -n \"lateral\\|Lateral\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py | head -30", "description": "Read annotate_types lateral handling"}
[tool_result]         # Replace NULL type with the default type of the targeted dialect, since the former is not an actual type;
        # it is mostly used to aid type coercion, e.g. in query set operations.
        # TODO (mypyc): uses list() + _set_type instead of direct expr.type = ... because
        # mypyc's property setter bypass rejects DType, and _set_type modifies the dict.
        for expr in list(self._null_expressions.values()):
            self._set_type(expr, self.dialect.DEFAULT_NULL_TYPE)

 
…[6000 chars elided]…
lse None,
sqlglot/optimizer/scope.py:189:elif type(node) is exp.Lateral or (
sqlglot/optimizer/scope.py:802:expressions.extend(scope.expression.args.get("laterals") or [])
sqlglot/optimizer/scope.py:837:lateral_sources = sources
sqlglot/optimizer/scope.py:841:lateral_sources = None
sqlglot/optimizer/scope.py:856:lateral_sources=lateral_sources,
sqlglot/optimizer/scope.py:890:elif isinstance(scope.expression, exp.Lateral):
sqlglot/optimizer/scope.py:947:for key in ("joins", "laterals", "pivots"):
[assistant] The key spot is `_get_scope_selects`: for `Lateral(Explode)` it records the column type as the raw `items` column type (`ARRAY<STRUCT<...>>`) rather than the exploded element type. I'll check how the same struct-field access behaves with an `UNNEST`, a plain struct table column, and the explode variant, to see what the existing working paths do.
[tool_use Bash] {"command": "cat > /tmp/probe_lv.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.annotate_types import annotate_types\ncases = [\n (\"explode alias same name\", \"SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\", {\"my_table\": {\"items\": \"ARRAY<STRUCT<name:STRING>>\"}}, \"spark\"),\n (\"explode alias diff name\", \"SELECT ci.name FRO
…[615 chars elided]…
out = optimize(sqlglot.parse_one(sql, read=d), schema=schema, dialect=d)\n        print(\"OK  \", label, \"->\", out.sql(d))\n    except Exception as e:\n        print(\"FAIL\", label, \"->\", type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe_lv.py 2>&1 | tail -20", "description": "Probe related LATERAL VIEW and struct access cases"}
[tool_result] Traceback (most recent call last):
  File "/tmp/probe_lv.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores `PYTHONPATH`, so the import failed. I'll keep `-I` and add the repo path via `sys.path` in the probe script instead.
[tool_use Bash] {"command": "sed -i '1i import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1\")' /tmp/probe_lv.py && <work>/env-sqlglot/bin/python -I /tmp/probe_lv.py 2>&1 | tail -20", "description": "Run probe cases against the repo source"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/probe_lv.py
": extra characters at the end of p command
[tool_use Bash] {"command": "R=$(pwd) && { echo \"import sys; sys.path.insert(0, '$R')\"; cat /tmp/probe_lv.py; } > /tmp/probe_lv2.py && mv /tmp/probe_lv2.py /tmp/probe_lv.py && <work>/env-sqlglot/bin/python -I /tmp/probe_lv.py 2>&1 | tail -20", "description": "Run probe cases against the repo source"}
[tool_result] FAIL explode alias same name -> OptimizeError Unknown column: name
FAIL explode alias diff name -> OptimizeError Unknown column: name
OK   explode, select item.name -> SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
OK   plain struct column -> SELECT `t`.`s`.`name` AS `name` FROM `my_table` AS `t`
OK   unnest struct -> SELECT `ci`.`name` AS `name` FROM EXPLODE(ARRAY(CAST(NULL AS STRUCT<`name`: STRING>))) AS `ci`
[assistant] Three of the five cases behave: the `item.name` variant qualifies to `ci.item.name`, and `UNNEST` works. The "diff name" failure is arguably correct, because `ci` has no `name` column. The real bug is the same-name case, where `ci` is both the table alias and the struct column. I'll find where qualification resolves `col.field` for struct columns, since the working `item.name` path must go through it.
[tool_use Bash] {"command": "grep -n \"def \\|dot_parts\\|Dot\\|struct\\|STRUCT\" sqlglot/optimizer/qualify_columns.py | head -120", "description": "List functions and struct handling in qualify_columns"}
[tool_result] 73 matches in 35 files:

117:0:E, sql: str | None = None) -> E:
169:0:Scope, pseudocolumns: set[str]) -> None:
191:0:exp.Pivot) -> Iterator[exp.Column]:
202:0:Iterable[exp.Expr]) -> None:
216:0:Scope, resolver: Resolver) -> dict[str, t.Any]:
219:0:str) -> None:
434:0:Scope, dialect: Dialect) -> None:
444:0:Scope, resolver: Resolver) -> None:
542:0:exp.Selectable, node: exp.Literal) -> exp.Alias:
549:0:Scope, resolver: Resolver) -> None:
558:0:
587:0:
589:0:]
655:0:exp.Dot,
660:0:
668:0:-1]
671:0
…[2216 chars elided]…
arts, [this])]
sqlglot/optimizer/qualify_columns.py:709:"""[RisingWave] Expand/Flatten (<exp>.bar).*, where bar is a struct column"""
sqlglot/optimizer/qualify_columns.py:721:starting_struct = dot_column.type
sqlglot/optimizer/qualify_columns.py:723:# walk up AST and down into struct definition in sync
sqlglot/optimizer/qualify_columns.py:742:# Check if current rhs identifier is in struct
sqlglot/optimizer/qualify_columns.py:747:starting_struct = struct_field_def.kind  # update struct
[+14 more]
[tool_use Bash] {"command": "sed -n 548,660p sqlglot/optimizer/qualify_columns.py", "description": "Read struct/dot column qualification and _qualify_columns"}
[tool_result] def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
    """
    Converts `Column` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."field2"), but they need to be
    normalized to `Dot(Dot(...(<table>.<column>, field1), field2, ...))` to be qualified properly.
    """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot
…[3426 chars elided]…
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
[assistant] The mechanism is clear now. `_convert_columns_to_dots` skips any column whose qualifier is already a source (`ci` is one), so `ci.name` is never rewritten to `ci.ci.name`. Then `_qualify_columns` checks `name` against the `ci` source's columns, which only contain `ci` typed as `ARRAY<STRUCT>`, and raises. I'll check the resolver's column lookup and the existing lateral-explode type tests before choosing the fix.
[tool_use Bash] {"command": "grep -n \"def get_source_columns\" -A 25 sqlglot/optimizer/resolver.py; echo ----; grep -rn \"EXPLODE\\|explode\" tests/test_optimizer.py tests/fixtures/optimizer/*.sql tests/fixtures/optimizer/qualify_columns.sql tests/dialects/test_hive.py tests/dialects/test_spark.py 2>/dev/null | grep -i \"lateral\\|explode\" | head -30", "description": "Read resolver source columns and lateral explode tests"}
[tool_result] 95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
96-        if isinstance(expression, exp.Select):
97-            return expression.named_selects
98-        if isinstance(expression, exp.Subquery) and isinstance(expression.this, exp.SetOperation):
99-            # Different types of SET modifiers can be chained together if they're explicitly grouped by nesting
100-            return self.get_source_columns_from_set_op(expression.this)
101-        if not isinsta
…[5143 chars elided]…
sts/dialects/test_hive.py:273:            "SELECT a, b FROM x LATERAL VIEW EXPLODE(y) t AS a LATERAL VIEW EXPLODE(z) u AS b",
tests/dialects/test_hive.py:277:                "hive": "SELECT a, b FROM x LATERAL VIEW EXPLODE(y) t AS a LATERAL VIEW EXPLODE(z) u AS b",
tests/dialects/test_hive.py:278:                "spark": "SELECT a, b FROM x LATERAL VIEW EXPLODE(y) t AS a LATERAL VIEW EXPLODE(z) u AS b",
tests/dialects/test_hive.py:282:            "SELECT a FROM x LATERAL VIEW EXPLODE(y) t AS a",
[assistant] Existing fixtures pin `SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c` → `_0.c`, so I need to leave those alone. I'll check the rest of `get_source_columns` to see where a lateral source's column names come from.
[tool_use Bash] {"command": "sed -n 158,200p sqlglot/optimizer/resolver.py; echo ----; grep -n \"get_table\\b\" -A 30 sqlglot/optimizer/resolver.py | sed -n 1,60p | grep -n \"def get_table\" -A 30", "description": "Read rest of get_source_columns and get_table"}
[tool_result]                         if isinstance(unnest_expr, exp.Column) and self.scope.parent:
                            col_type = self._get_unnest_column_type(unnest_expr)
                            # extract element type if it's an ARRAY
                            if col_type and col_type.is_type(exp.DType.ARRAY):
                                element_types = col_type.expressions
                                if element_types:
                                    unnest.type = element_types[0].
…[3152 chars elided]…
still ambiguous and try to resolve with schema inference below
22-55-                try:
23-56-                    table_name = self._get_table_name_from_sources(
24-57-                        column_name, self._get_available_source_columns(join_context)
25-58-                    )
26-59-                except OptimizeError:
27-60-                    pass
28-61-
29-62-        if not table_name and self._infer_schema:
30-63-            sources_without_schema = tuple(
31-64-                source
[assistant] Lateral sources don't carry struct field names the way `UNNEST` sources do. The `UNNEST` path in the resolver computes the element type on demand through `_get_unnest_column_type`, and that is the pattern to mirror. I'll read that helper and the optimizer's rule ordering to see whether types are annotated before `qualify_columns` runs.
[tool_use Bash] {"command": "grep -n \"_get_unnest_column_type\" -A 25 sqlglot/optimizer/resolver.py | sed -n 1,40p; echo ----; grep -n \"RULES\" -A 25 sqlglot/optimizer/optimizer.py | head -40; echo ----; sed -n 80,110p sqlglot/optimizer/qualify.py", "description": "Read unnest type helper and optimizer rule order"}
[tool_result] 159:                            col_type = self._get_unnest_column_type(unnest_expr)
160-                            # extract element type if it's an ARRAY
161-                            if col_type and col_type.is_type(exp.DType.ARRAY):
162-                                element_types = col_type.expressions
163-                                if element_types:
164-                                    unnest.type = element_types[0].copy()
165-                            else:
166-             
…[3376 chars elided]…
    expression = qualify_columns_func(
            expression,
            schema,
            expand_alias_refs=expand_alias_refs,
            expand_stars=expand_stars,
            infer_schema=infer_schema,
            allow_partial_qualification=allow_partial_qualification,
        )

    if quote_identifiers:
        expression = quote_identifiers_func(expression, dialect=dialect, identify=identify)

    if validate_qualify_columns:
        validate_qualify_columns_func(expression, sql=sql)
[assistant] `qualify` runs before `annotate_types`, so the struct type of the exploded column isn't available during qualification unless I compute it there. I'll read the rest of `_get_unnest_column_type` to see whether it can be reused for the `EXPLODE` argument.
[tool_use Bash] {"command": "sed -n 341,380p sqlglot/optimizer/resolver.py; echo ----; sed -n 180,200p sqlglot/optimizer/scope.py; sed -n 885,900p sqlglot/optimizer/scope.py", "description": "Read full unnest column type helper and scope lateral handling"}
[tool_result]     def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:
        """
        Get the type of a column being unnested, tracing through CTEs/subqueries to find the base table.

        Args:
            column: The column expression being unnested.

        Returns:
            The DataType of the column, or None if not found.
        """
        scope = self.scope.parent
        assert scope

        # if column is qualified, use that table, otherwise disambiguate using t
…[2219 chars elided]…

    if isinstance(scope.expression, exp.Unnest):
        udtf_expressions = scope.expression.expressions
    elif isinstance(scope.expression, exp.Lateral):
        udtf_expressions = [scope.expression.this]
    else:
        udtf_expressions = []

    sources: dict[str, exp.Table | Scope] = {}
    for expression in udtf_expressions:
        if isinstance(expression, exp.Subquery):
            top: Scope | None = None
            for child_scope in _traverse_scope(
                scope.branch(
[assistant] The `_get_unnest_column_type` helper walks from `self.scope.parent`, which is the wrong scope for a `LATERAL VIEW` in the same `SELECT`. I'll read `_get_column_type_from_scope` and `Dot.build`, then confirm the approach against the existing fixtures.
[tool_use Bash] {"command": "sed -n 380,410p sqlglot/optimizer/resolver.py; echo ----; grep -n \"def build\" -A 12 sqlglot/expressions.py | grep -A12 \"class Dot\\|Dot\" | head -5; grep -n \"class Dot\" -A 40 sqlglot/expressions.py | grep -n \"def build\" -A 15", "description": "Read column type helper and Dot.build"}
[tool_result]         """
        if isinstance(source, exp.Table):
            # base table - get the column type from schema
            col_type: exp.DataType | None = self.schema.get_column_type(source, column)
            if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                return col_type
        elif isinstance(source, Scope):
            # iterate over all sources in the scope
            for source_name, nested_source in source.sources.items():
                col_type = self._get_column_type_from_scope(nested_source, column)
                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                    return col_type

        return None
----
grep: sqlglot/expressions.py: No such file or directory
grep: sqlglot/expressions.py: No such file or directory
[assistant] `_get_column_type_from_scope` handles `Table` sources, so I can get the exploded array's type directly from the schema. My plan:

1. **Resolver:** add a helper that answers whether `ci.<field>` refers to a field of the struct that a `LATERAL VIEW EXPLODE` alias produces under a same-named column.
2. **`_convert_columns_to_dots`:** rewrite such a column to `ci.ci.<field>`, which is how Spark resolves it, instead of leaving it for `_qualify_columns` to reject.

Starting with the resolver helper, placed next to `_get_unnest_column_type`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:", "new_string": "    def is_lateral_struct_field(self, source_name: str, field_name: str) -> bool:\n        \"\"\"\n        Wh
…[1010 chars elided]…
p.DType.ARRAY) or not array_type.expressions:\n            return False\n\n        struct_type = array_type.expressions[0]\n        return isinstance(struct_type, exp.DataType) and struct_type.is_type(\n            exp.DType.STRUCT\n        ) and any(field.name == field_name for field in struct_type.expressions)\n\n    def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Next, the rewrite in `_convert_columns_to_dots`. The existing loop already tracks `converted` and clears the scope cache, so the new branch only needs to replace the column and set the flag.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        column_table: str | exp.Identifier | None = column.table\n        dot_parts = column.meta.pop(\"dot_parts\", [])\n        if (", "new_string": "        column_table: str | exp.Identifier | None
…[102 chars elided]…
esolver.is_lateral_struct_field(column_table.name, column.name):\n            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`\n            converted = True\n            column.replace(\n                exp.Dot.build(\n                    [exp.column(column_table.name, table=column_table.name), column.this.copy()]\n                )\n            )\n        elif ("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] I used `.name` on `column_table`, but `Column.table` returns a plain string, so that would fail. Fixing it to use the string directly:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and resolver.is_lateral_struct_field(column_table.name, column.name):\n            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`\n           
…[186 chars elided]…
        )\n            )", "new_string": "        if column_table and resolver.is_lateral_struct_field(column_table, column.name):\n            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`\n            converted = True\n            column.replace(\n                exp.Dot.build([exp.column(column_table, table=column_table), column.this.copy()])\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/probe_lv.py 2>&1 | tail -20; cat > /tmp/probe_types.py <<'EOF'\nimport sys; sys.path.insert(0, '~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1')\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nout = optimize(sqlglot.parse_one(\"SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\", read=\"spark\"), schema={\"my_table\": {\"items\": \"ARRAY<STRUCT<name:STRING>>\"}}, dialect=\"spark\")\nprint(out.sql(\"spark\"))\nprint(out.selects[0].type)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe_types.py", "description": "Rerun probes and check output SQL and type"}
[tool_result] OK   explode alias same name -> SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
FAIL explode alias diff name -> OptimizeError Unknown column: name
OK   explode, select item.name -> SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
OK   plain struct column -> SELECT `t`.`s`.`name` AS `name` FROM `my_table` AS `t`
OK   unnest struct -> SELECT `ci`.`name` AS `name` FROM EXPLODE(ARRAY(CAST(NULL AS STRUCT<`name`: STRING>))) AS `ci`
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
UNKNOWN
[assistant] The main case now produces `ci.ci.name` and the diff-name case still errors, which matches Spark because `ci` has no `name` column. The output type is still `UNKNOWN`, though. `_get_scope_selects` records the array column's type (`ARRAY<STRUCT>`) for the lateral alias rather than the exploded element type. I'll try recording the element type there, and check the existing type tests afterwards.
[tool_use Bash] {"command": "grep -n \"lateral\\|Lateral\" tests/test_optimizer.py tests/test_expressions.py tests/test_schema.py 2>/dev/null | head; grep -rln \"LATERAL VIEW\\|lateral view\" tests | head", "description": "Find existing tests covering lateral view typing"}
[tool_result] 5 matches in 1 files:

tests/test_optimizer.py:494:# Detection of correlation where columns are referenced in derived tables nes...
tests/test_optimizer.py:855:# check order of lateral expansion with no schema
tests/test_optimizer.py:1079:self.assertEqual(set(scopes[1].sources), {"", "foo"})  # foo is a lateral source
tests/test_optimizer.py:1338:def test_lateral_annotation(self):
tests/test_optimizer.py:1494:annotate_types(parse_one("select x from y lateral view explode(y) as x")).exp...
tests/test_parser.py
tests/test_optimizer.py
tests/test_build.py
tests/dialects/test_bigquery.py
tests/dialects/test_spark.py
tests/dialects/test_presto.py
tests/dialects/test_dialect.py
tests/dialects/test_starrocks.py
tests/dialects/test_hive.py
tests/fixtures/identity.sql
[tool_use Bash] {"command": "sed -n 1336,1350p tests/test_optimizer.py; sed -n 1490,1500p tests/test_optimizer.py", "description": "Read existing lateral annotation tests"}
[tool_result]                 self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.optimize(
            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expressions[0]
        self.assertEqual(expression.type.this, exp.DataType.Type.INT)

    def test_derived_tables_column_annotation(self):
        schema = {"x": {"cola": "INT"}, "y": {"cola": "FLOAT"}}
        sql = """
            SELECT a.cola AS cola
           
…[72 chars elided]…
ROM (
            concat_expr.right.expressions[0].type.this, exp.DataType.Type.VARCHAR
        )  # x.cola (arg)

        # Ensures we don't raise if there are unqualified columns
        annotate_types(parse_one("select x from y lateral view explode(y) as x")).expressions[0]

        # NULL <op> UNKNOWN should yield UNKNOWN
        self.assertEqual(
            annotate_types(parse_one("SELECT NULL + ANONYMOUS_FUNC()")).expressions[0].type.this,
            exp.DataType.Type.UNKNOWN,
        )
[assistant] The existing `test_lateral_annotation` expects `EXPLODE(a)` over a non-array `INT` to stay `INT`, so the element-type change should only apply when the exploded column is an `ARRAY`. I'll make that change in `_get_scope_selects` and keep the non-array behavior.
[tool_use Bash] {"command": "grep -n \"values = \\[expression.this.this\\]\" -B3 -A3 sqlglot/optimizer/annotate_types.py; grep -n \"alias: column.type for alias, column in zip\" -B2 -A2 sqlglot/optimizer/annotate_types.py", "description": "Locate lateral explode type code in annotate_types"}
[tool_result] 289-
290-                    if isinstance(expression, exp.Lateral):
291-                        if isinstance(expression.this, exp.Explode):
292:                            values = [expression.this.this]
293-                    elif isinstance(expression, exp.Unnest):
294-                        values = [expression]
295-                    elif not isinstance(expression, exp.TableFromRows):
313-                    else:
314-                        selects[name] = {
315:                            alias: column.type for alias, column in zip(alias_column_names, values)
316-                        }
317-                elif isinstance(expression, exp.SetOperation) and len(
[assistant] I'll apply the element-type rule only to `ARRAY`-typed explode columns, mirroring `_annotate_explode`, which already takes `expressions[0]` of the array type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "                        selects[name] = {\n                            alias: column.type for alias, column in zip(alias_column_names, values)\n                        }", "new_string": "               
…[118 chars elided]…
ons[0]\n                                if isinstance(expression, exp.Lateral)\n                                and column.is_type(exp.DType.ARRAY)\n                                and column.type.expressions\n                                else column.type\n                            )\n                            for alias, column in zip(alias_column_names, values)\n                        }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/probe_types.py && <work>/env-sqlglot/bin/python -I /tmp/probe_lv.py 2>&1 | head -3", "description": "Check output type and rerun main probe"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
TEXT
OK   explode alias same name -> SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
FAIL explode alias diff name -> OptimizeError Unknown column: name
OK   explode, select item.name -> SELECT `ci`.`item`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `item`
[assistant] The output is now `ci.ci.name` with a `TEXT` type. Next I'll run the project's check command in full to catch regressions before adding tests.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
...........................................................................................................................
…[323 chars elided]…
................................................................................... [ 77%]
............................................. [ 81%]
.... [ 81%]
...................................................................... [ 88%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 49.81s
[assistant] All 1092 tests pass (17857 subtests). Next I'll add a regression test next to `test_lateral_annotation`, asserting both the rewritten SQL and the element-typed output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n
…[344 chars elided]…
ema,\n            dialect=\"spark\",\n        )\n        self.assertEqual(\n            expression.sql(\"spark\"),\n            \"SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`\",\n        )\n        self.assertEqual(expression.selects[0].type.this, exp.DataType.Type.TEXT)\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Running the linter and formatter on the changed files, since the long SQL string may exceed the line-length limit:
[tool_use Bash] {"command": "grep -n \"^style\" -A 6 Makefile; R=<work>/env-sqlglot/bin; ls $R | grep -i \"ruff\\|mypy\"; $R/ruff check sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py tests/test_optimizer.py 2>&1 | tail -15; $R/ruff format --check sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py tests/test_optimizer.py 2>&1 | tail -5", "description": "Run ruff lint and format checks on changed files"}
[tool_result] 83:style:
84-	pre-commit run --all-files
85-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
86-
87-check: style test testc
88-
89-docs:
dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
All checks passed!
Would reformat: sqlglot/optimizer/resolver.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format --diff sqlglot/optimizer/resolver.py 2>&1 | head -30; $R/ruff format sqlglot/optimizer/resolver.py && $R/mypy sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py 2>&1 | tail -5", "description": "Format resolver and run mypy on changed modules"}
[tool_result] --- sqlglot/optimizer/resolver.py
+++ sqlglot/optimizer/resolver.py
@@ -364,9 +364,11 @@
             return False
 
         struct_type = array_type.expressions[0]
-        return isinstance(struct_type, exp.DataType) and struct_type.is_type(
-            exp.DType.STRUCT
-        ) and any(field.name == field_name for field in struct_type.expressions)
+        return (
+            isinstance(struct_type, exp.DataType)
+            and struct_type.is_type(exp.DType.STRUCT)
+            and an
…[54 chars elided]…
pressions)
+        )
 
     def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:
         """

1 file would be reformatted
1 file reformatted
sqlglot/optimizer/qualify_columns.py:563: error: Argument 1 to "is_lateral_struct_field" of "Resolver" has incompatible type "str | Identifier"; expected "str"  [arg-type]
Found 1 error in 1 file (checked 3 source files)
[This command modified 1 file you've previously read: sqlglot/optimizer/resolver.py. Call Read before editing.]
[assistant] The formatter reflowed the resolver expression as expected. mypy flags the call site because `column_table` is annotated `str | Identifier`. I'll look at the current block and pass the string directly.
[tool_use Bash] {"command": "sed -n 556,572p sqlglot/optimizer/qualify_columns.py", "description": "View the edited conversion block"}
[tool_result]     converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot):
            continue

        column_table: str | exp.Identifier | None = column.table
        dot_parts = column.meta.pop("dot_parts", [])
        if column_table and resolver.is_lateral_struct_field(column_table, column.name):
            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`
            converted = True
            column.replace(
                exp.Dot.build([exp.column(column_table, table=column_table), column.this.copy()])
            )
        elif (
            column_table
            and column_table not in scope.sources
            and (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and resolver.is_lateral_struct_field(column_table, column.name):\n            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`\n            conv
…[171 chars elided]…
 "        if column.table and resolver.is_lateral_struct_field(column.table, column.name):\n            # e.g. `ci.name` where `ci` is an exploded struct column: rewrite to `ci.ci.name`\n            converted = True\n            column.replace(\n                exp.Dot.build(\n                    [exp.column(column.table, table=column.table), column.this.copy()]\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140326-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py >/dev/null; $R/ruff check sqlglot/optimizer tests/test_optimizer.py | tail -3; $R/ruff format --check sqlglot tests | tail -2; $R/mypy sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py 2>&1 | tail -3; $R/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"lateral\" 2>&1 | tail -3; git diff --stat", "description": "Format, lint, type-check, and run lateral tests"}
[tool_result] All checks passed!
234 files already formatted
Success: no issues found in 3 source files
..                                                                       [100%]
2 passed, 76 deselected in 0.25s
sqlglot/optimizer/annotate_types.py  |  9 ++++++++-
 sqlglot/optimizer/qualify_columns.py |  8 +++++++-
 sqlglot/optimizer/resolver.py        | 32 ++++++++++++++++++++++++++++++++
 tests/test_optimizer.py              | 15 +++++++++++++++
 4 files changed, 62 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] Lint, format, and mypy are clean, and the two lateral tests pass. The "changed on disk" notices come from my own formatter run. Now the full suite again with the project's check command, then a review of the diff.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff -- sqlglot", "description": "Run full suite and show source diff", "timeout": 900000}
[tool_result] ............................................ [ 99%]
.........                                                           [100%]
1093 passed, 17857 subtests passed in 52.12s
sqlglot/optimizer/annotate_types.py  |  9 ++++++++-
 sqlglot/optimizer/qualify_columns.py |  8 +++++++-
 sqlglot/optimizer/resolver.py        | 32 ++++++++++++++++++++++++++++++++
 3 files changed, 47 insertions(+), 2 deletions(-)

--- Changes ---

sqlglot/optimizer/annotate_types.py
  @@ -312,7 +312,14 @@ class TypeAnnotator:
…[2696 chars elided]…
  +        struct_type = array_type.expressions[0]
  +        return (
  +            isinstance(struct_type, exp.DataType)
  +            and struct_type.is_type(exp.DType.STRUCT)
  +            and any(field.name == field_name for field in struct_type.expressions)
  +        )
  +
       def _get_unnest_column_type(self, column: exp.Column) -> exp.DataType | None:
           """
           Get the type of a column being unnested, tracing through CTEs/subqueries to find the base table.
  +32 -0
[assistant] `optimize()` no longer raises for the `LATERAL VIEW EXPLODE` case in the report. The full suite passes (1093 tests, 17857 subtests), and ruff and mypy are clean on the changed files.

**Root cause:** when the table alias and the column alias are both `ci`, `ci.name` is treated as a column of the `ci` source. The qualifier-to-struct rewrite skips any qualifier that is already a source, and the exploded alias was typed as the raw `ARRAY<STRUCT<...>>` rather than the struct element. So `name` was never found and qualification raised.

**Changes:**
- **`sqlglot/optimizer/resolver.py`:** new `is_la
…[607 chars elided]…
naffected.
- **`tests/test_optimizer.py`:** added `test_lateral_explode_struct_field_access`, which checks the rewritten SQL and the `TEXT` type. No existing tests were edited.

**Output for the example:**
```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Intentional behavior:** `LATERAL VIEW EXPLODE(items) ci AS item` with `SELECT ci.name` still raises. Spark would also reject it, since `ci` has no `name` column. The working path there is `item.name`, which I confirmed still qualifies.

I have not committed anything.
