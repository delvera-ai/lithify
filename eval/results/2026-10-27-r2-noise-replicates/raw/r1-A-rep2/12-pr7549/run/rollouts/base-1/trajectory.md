# trajectory base-1

final message:
The Spark `LATERAL VIEW EXPLODE` case now optimizes without error, and the exploded struct field gets its type. The full suite passes (1093 passed) and ruff check and format are clean. The changes are uncommitted in the worktree.

**Cause:** When the table alias equals the exploded column name (`ci ... AS ci`), the qualifier treated `ci` only as a table, so `ci.name` was never rewritten into a field access on the struct column. Separately, the exploded alias was typed as the whole array (`ARRAY<STRUCT<...>>`) rather than its element.

**Changes:**
- `sqlglot/optimizer/qualify_columns.py`: in `_convert_columns_to_dots`, a field reference on a lateral source whose only column shares its name is rewritten to `ci.ci.name`. This is restricted to `Lateral` sources, so other tables and BigQuery unnest are unaffected.
- `sqlglot/optimizer/annotate_types.py`: the lateral alias now takes the element type of the explode. `_annotate_explode` still passes a non-array input through unchanged, because the existing `test_lateral_annotation` pins `EXPLODE(int) AS c` to `INT`. I didn't edit that test.
- `tests/test_optimizer.py`: added `test_lateral_explode_struct_field_access`, which checks that `ci.name` is `STRING` and that `EXPLODE(nums) AS c` is `INT`.

Your repro now returns `SELECT ci.ci.name AS name ... LATERAL VIEW EXPLODE(items) ci AS ci`. The output type of `ci.name` is `STRING`, not `UNKNOWN`. One note: `SELECT ci.name ... EXPLODE(items) ci AS c` still raises `Unknown column`, which is correct because the struct's `name` column isn't visible under that alias.

## events
[assistant] I'll reproduce the failure first, then trace where the exploded alias loses its type.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nprint(optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[82 chars elided]…
^
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
[assistant] The error reproduces. Next I'll look at how `qualify_columns` handles lateral aliases and how the Spark parser builds `LATERAL VIEW`.
[tool_use Bash] {"command": "grep -n -i \"lateral\\|explode\\|unnest\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py sqlglot/optimizer/scope.py | head -60; echo ---; grep -n -i \"lateral\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/parser.py | head -40", "description": "Find lateral/explode handling in optimizer and parsers"}
[tool_result] sqlglot/optimizer/qualify_columns.py:530:                    or select_expr.find(exp.Explode, exp.Unnest)
sqlglot/optimizer/qualify_columns.py:626:            # column_table can be a '' because bigquery unnest has no table alias
sqlglot/optimizer/annotate_types.py:290:                    if isinstance(expression, exp.Lateral):
sqlglot/optimizer/annotate_types.py:291:                        if isinstance(expression.this, exp.Explode):
sqlglot/optimizer/annotate_types.py:293:                    el
…[2383 chars elided]…
eral, None):
sqlglot/parser.py:4068:                this.append("laterals", lateral)
sqlglot/parser.py:4266:    def _parse_lateral(self) -> exp.Lateral | None:
sqlglot/parser.py:4277:        elif self._match(TokenType.LATERAL):
sqlglot/parser.py:4306:            # We move the alias from the lateral's child node to the lateral itself
sqlglot/parser.py:4313:            exp.Lateral(
sqlglot/parser.py:4725:        if lateral := self._parse_lateral():
sqlglot/parser.py:4726:            return lateral
[tool_use Bash] {"command": "sed -n 4266,4330p sqlglot/parser.py; echo ----; sed -n 270,320p sqlglot/optimizer/annotate_types.py; echo ----; sed -n 410,435p sqlglot/optimizer/annotate_types.py; echo ----; sed -n 775,790p sqlglot/optimizer/annotate_types.py", "description": "Read lateral parsing and annotate_types lateral code"}
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
…[5721 chars elided]…
def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
        self._set_type(expression, seq_get(expression.this.type.expressions, 0))
        return expression

    def _annotate_unnest(self, expression: exp.Unnest) -> exp.Unnest:
        child = seq_get(expression.expressions, 0)

        if child and child.is_type(exp.DType.ARRAY):
            expr_type = seq_get(child.type.expressions, 0)
        else:
            expr_type = None

        self._set_type(expression, expr_type)
[assistant] The `_get_scope_selects` path for `Lateral` only exposes the alias column (`ci`) with the struct type, so `ci.name` has no matching column. Let me check the column-resolution code and existing tests for this pattern.
[tool_use Bash] {"command": "sed -n 520,640p sqlglot/optimizer/qualify_columns.py; echo ----; grep -rn \"LATERAL VIEW\" tests/fixtures/optimizer/*.sql tests/test_optimizer.py tests/dialects/test_hive.py tests/dialects/test_spark.py | head -30", "description": "Read column qualification logic and related tests"}
[tool_result]                     ambiguous = any(
                        column.parts[0].name in ambiguous_projections
                        for column in select_expr.find_all(exp.Column)
                    )
                else:
                    ambiguous = False

                if (
                    isinstance(select_expr, exp.CONSTANTS)
                    or select_expr.is_number
                    or select_expr.find(exp.Explode, exp.Unnest)
                    or ambiguous
                
…[6898 chars elided]…
ELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
tests/dialects/test_spark.py:415:            "SELECT h.id, amount FROM hourlycostagg h LATERAL VIEW inline(h.costs) c",
tests/dialects/test_spark.py:421:            "SELECT h.id, amount FROM hourlycostagg h LATERAL VIEW inline(h.adjustments) as type, val, curr",
tests/dialects/test_spark.py:458:            LATERAL VIEW inline(h.costs) c
tests/dialects/test_spark.py:459:            LATERAL VIEW inline(h.adjustments) as type, val, curr
[assistant] The qualifier only treats `ci` as a source, so `ci.name` never gets rewritten into struct-field access on the exploded column. Before choosing a fix, I'll compare against a few nearby variants to see which forms already work.
[tool_use Bash] {"command": "cat > /tmp/probe_explode.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ncases = [\n  \"SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\",\n  \"SELECT ci.ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\",\n  \"SELECT t.ci.name 
…[371 chars elided]…
hema, dialect='spark').sql('spark')\n    except Exception as e:\n        out = f\"ERR {type(e).__name__}: {e}\"\n    print(sql, \"\\n   ->\", out)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_explode.py').read())\" 2>&1 | tail -30", "description": "Probe variants of the LATERAL VIEW struct access"}
[tool_result] SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> ERR OptimizeError: Unknown column: name
SELECT ci.ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> ERR OptimizeError: Unknown column: name
SELECT t.ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci 
   -> SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci 
   -> SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT ci FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS c 
   -> ERR OptimizeError: Unknown column: name
[assistant] Two findings from the probe:

- With a different table alias (`t AS ci`), `ci.name` works, because `ci` resolves to a column and the struct field is handled by dot conversion.
- Only the case where the table alias equals the exploded column name fails. The qualifier sees `ci` as a source, so `.name` is never turned into a field access on the struct column.

Next I'll check how the resolver reports a lateral source's columns and how annotation handles `Dot` on a struct, so I can pick the narrowest fix.
[tool_use Bash] {"command": "grep -n \"def get_source_columns\" -A 25 sqlglot/optimizer/qualify_columns.py; grep -n \"def _annotate_dot\\|exp.Dot\\b\" sqlglot/optimizer/annotate_types.py | head; grep -n \"class Resolver\" -A 3 sqlglot/optimizer/qualify_columns.py", "description": "Inspect Resolver source columns and Dot annotation"}
[tool_result] 431:                    while isinstance(parent, exp.Dot):
760:    def _annotate_dot(self, expression: exp.Dot) -> exp.Dot:
[tool_use Bash] {"command": "grep -rn \"def get_source_columns\" -A 22 sqlglot/optimizer/ | head -60; sed -n 760,778p sqlglot/optimizer/annotate_types.py; grep -n \"_convert_columns_to_dots\" sqlglot/optimizer/*.py", "description": "Locate Resolver.get_source_columns and Dot annotation"}
[tool_result] sqlglot/optimizer/resolver.py:95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py-96-        if isinstance(expression, exp.Select):
sqlglot/optimizer/resolver.py-97-            return expression.named_selects
sqlglot/optimizer/resolver.py-98-        if isinstance(expression, exp.Subquery) and isinstance(expression.this, exp.SetOperation):
sqlglot/optimizer/resolver.py-99-            # Different types of SET modifiers can be chained to
…[3830 chars elided]…
DType.STRUCT):
            for e in this_type.expressions:
                if e.name == expression.expression.name:
                    self._set_type(expression, e.kind)
                    break

        return expression

    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
sqlglot/optimizer/qualify_columns.py:84:        _convert_columns_to_dots(scope, resolver)
sqlglot/optimizer/qualify_columns.py:549:def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
[tool_use Bash] {"command": "sed -n 155,185p sqlglot/optimizer/resolver.py; sed -n 75,90p sqlglot/optimizer/qualify_columns.py", "description": "Read rest of get_source_columns and qualify_columns entry"}
[tool_result]                     # if type is not annotated yet, try to get it from the schema
                    if not unnest.type or unnest.type.is_type(exp.DType.UNKNOWN):
                        unnest_expr = seq_get(unnest.expressions, 0)
                        if isinstance(unnest_expr, exp.Column) and self.scope.parent:
                            col_type = self._get_unnest_column_type(unnest_expr)
                            # extract element type if it's an ARRAY
                            if c
…[1428 chars elided]…
) or (None, None)

        if (schema.empty or dialect.FORCE_EARLY_ALIAS_REF_EXPANSION) and expand_alias_refs:
            _expand_alias_refs(
                scope,
                resolver,
                dialect,
                expand_only_groupby=dialect.EXPAND_ONLY_GROUP_ALIAS_REF,
            )

        _convert_columns_to_dots(scope, resolver)
        _qualify_columns(
            scope,
            resolver,
            allow_partial_qualification=allow_partial_qualification,
        )
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import ensure_schema\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nsql='SELECT ci.name FROM my_table LATER
…[122 chars elided]…
park')\ne = qualify_tables(sqlglot.parse_one(sql, read='spark'), dialect='spark')\ns = build_scope(e)\nprint(s.sources)\nsrc = s.sources['ci']\nprint(type(src), getattr(src,'expression',None).__class__)\nr = Resolver(s, schema, infer_schema=True)\nprint(r.get_source_columns('ci'))\nprint(s.columns)\n\" 2>&1 | tail -20", "description": "Inspect scope sources and resolver columns for lateral alias"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.schema import ensure_schema\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nsql='SELECT ci.name FROM my_table LATERAL VIEW EXP
…[111 chars elided]…
park')\ne = qualify_tables(sqlglot.parse_one(sql, read='spark'), dialect='spark')\ns = build_scope(e)\nprint(s.sources)\nsrc = s.sources['ci']\nprint(type(src), getattr(src,'expression',None).__class__)\nr = Resolver(s, schema, infer_schema=True)\nprint(r.get_source_columns('ci'))\nprint(s.columns)\n\" 2>&1 | tail -20", "description": "Inspect scope sources and resolver columns for lateral alias"}
[tool_result] {'my_table': Table(
  this=Identifier(this=my_table, quoted=False),
  alias=TableAlias(
    this=Identifier(this=my_table, quoted=False))), 'ci': Scope<LATERAL VIEW EXPLODE(items) ci AS ci>}
<class 'sqlglot.optimizer.scope.Scope'> <class 'sqlglot.expressions.query.Lateral'>
['ci']
[Column(
  this=Identifier(this=name, quoted=False),
  table=Identifier(this=ci, quoted=False)), Column(
  this=Identifier(this=items, quoted=False)), Column(
  this=Identifier(this=items, quoted=False))]
[assistant] The scope confirms the cause: `ci` is a `Scope` over a `Lateral`, and its only exposed column is `ci`. My plan is to add a narrow rule to `_convert_columns_to_dots`. If a column's qualifier is a lateral source that exposes a column with the same name, and the field isn't a column of that source, rewrite it as a field access on that column (`ci.name` → `ci.ci.name`). Then I'll check whether types propagate.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        column_table: str | exp.Identifier | None = column.table\n        dot_parts = column.meta.pop(\"dot_parts\", [])\n        if (\n            column_table\n            and column_table not in sco
…[434 chars elided]…
d column_table in resolver.get_source_columns(column_table)\n            and column.name not in resolver.get_source_columns(column_table)\n        ):\n            converted = True\n            column.replace(exp.Dot.build([exp.column(column_table, table=column_table), column.this]))\n            continue\n\n        if (\n            column_table\n            and column_table not in scope.sources"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] The `.expression` access is unsafe because `scope.sources` also holds plain `exp.Table` values. I'll guard it with a `Scope` check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            and column_table in scope.sources\n            and isinstance(scope.sources[column_table].expression, exp.Lateral)", "new_string": "            and column_table in scope.sources\n            and isinstance(source := scope.sources[column_table], Scope)\n            and isinstance(source.expression, exp.Lateral)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" sqlglot/optimizer/qualify_columns.py | head; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nexec(open('/tmp/probe_explode.py').read())\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.optimizer import optimize as o\nex = o(sqlglot.parse_one('SELECT ci.name AS n FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nprint(ex.selects[0].type, ex.sql('spark'))\n\" 2>&1 | tail -20", "description": "Re-run probe cases and check output type"}
[tool_result] 1:from __future__ import annotations
3:import itertools
4:import typing as t
6:from sqlglot import alias, exp
7:from sqlglot.dialects.dialect import Dialect, DialectType
8:from sqlglot.errors import OptimizeError, highlight_sql
9:from sqlglot.helper import seq_get
10:from sqlglot.optimizer.annotate_types import TypeAnnotator
11:from sqlglot.optimizer.resolver import Resolver
12:from sqlglot.optimizer.scope import Scope, build_scope, traverse_scope, walk_in_scope
SELECT ci.name FROM my_table LATE
…[629 chars elided]…
` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT ci FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS c 
   -> ERR OptimizeError: Unknown column: name
UNKNOWN SELECT `ci`.`ci`.`name` AS `n` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
[assistant] The rewrite works for all the variants, and the optimizer no longer raises. The output type is still `UNKNOWN`, though: `_get_scope_selects` reads the exploded array's own type rather than the element type, so the struct never reaches the `ci` column. I'll check how `EXPLODE` and lateral columns are typed today before changing that.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>', 'nums':'ARRAY<INT>'}}\nfor sql in ['SELECT c FROM my_table LATERAL VIEW EXPLODE(nums) t AS c',\n            'SELECT ci.name AS n FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci']:\n    ex = optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark')\n    print(ex.selects[0].type.sql('spark'), '|', ex.sql('spark'))\n\" 2>&1 | tail -8; git stash list >/dev/null; git diff --stat", "description": "Check current types of exploded columns"}
[tool_result] ARRAY<INT> | SELECT `t`.`c` AS `c` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`nums`) t AS `c`
UNKNOWN | SELECT `ci`.`ci`.`name` AS `n` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
 sqlglot/optimizer/qualify_columns.py | 14 ++++++++++++++
 1 file changed, 14 insertions(+)
[assistant] This confirms the type side of the bug. `EXPLODE(nums) AS c` is typed `ARRAY<INT>` when it should be `INT`, which is the same root cause. I'll make the lateral explode expose the `Explode` node, whose element type `_annotate_explode` already computes, and check that it is annotated by then.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "                        if isinstance(expression.this, exp.Explode):\n                            values = [expression.this.this]", "new_string": "                        if isinstance(expression.this, exp.Explode):\n                            values = [expression.this]"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>', 'nums':'ARRAY<INT>'}}\nfor sql in ['SELECT c FROM my_table LATERAL VIEW EXPLODE(nums) t AS c',\n            'SELECT ci.name AS n FROM my_ta
…[154 chars elided]…
arse_one(sql, read='spark'), schema=schema, dialect='spark')\n    print(ex.selects[0].type.sql('spark'), '|', ex.sql('spark'))\n\" 2>&1 | tail -8; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_explode.py').read())\" 2>&1 | tail -14", "description": "Verify exploded column types after annotation change"}
[tool_result] INT | SELECT `t`.`c` AS `c` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`nums`) t AS `c`
STRING | SELECT `ci`.`ci`.`name` AS `n` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
STRING | SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL V
…[395 chars elided]…
y_table`.`items`) t AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci 
   -> SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT ci FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci 
   -> SELECT `ci`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS c 
   -> ERR OptimizeError: Unknown column: name
[assistant] Types now propagate (`INT` for `nums`, `STRING` for `ci.name`), and the one remaining error is correct, since `ci` has no `name` column when aliased as `c`. Next I'll run the project's test suite to catch regressions.
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite", "timeout": 600000}
[tool_result] ........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
.........................................................................................................................................................................................................................................................................
…[987 chars elided]…
CT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expressions[0]
>       self.assertEqual(expression.type.this, exp.DataType.Type.INT)
E       AssertionError: <DType.UNKNOWN: 'UNKNOWN'> != <DType.INT: 'INT'>

tests/test_optimizer.py:1342: AssertionError
=========================== short test summary info ============================
FAILED tests/test_optimizer.py::TestOptimizer::test_lateral_annotation - Asse...
1 failed, 1091 passed, 17857 subtests passed in 60.25s (0:01:00)
[assistant] One existing test fails: `EXPLODE(a)` over an `INT` column is pinned to `INT`, and the old code passed the raw column type through. I can't edit that test, so I'll keep that pass-through for non-array inputs while typing arrays by their element type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:\n        self._set_type(expression, seq_get(expression.this.type.expressions, 0))\n        return expression", "new_string": "    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:\n        child_type = expression.this.type\n        self._set_type(\n            expression,\n            seq_get(child_type.expressions, 0) if child_type.expressions else child_type,\n        )\n        return expression"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[assistant] Next I'll run the full suite again and look at the existing lateral test, so I can add a regression test next to it.
[tool_use Bash] {"command": "sed -n 1334,1350p tests/test_optimizer.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Show existing lateral test and rerun full suite", "timeout": 600000}
[tool_result]                 expression = annotate_types(parse_one(sql), schema=schema)
                self.assertEqual(expected_type, expression.expressions[0].type.this)
                self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.optimize(
            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expressions[0]
        self.assertEqual(expression.type.this, exp.DataType.Type.INT)

    def test_derived_tables_column_annotation(self):
        schema = {"x": {"cola": "INT"}, "y": {"cola": "FLOAT"}}
        sql = """
            SELECT a.cola AS cola
            FROM (
                SELECT x.cola + y.cola AS cola
                FROM (
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 60.41s (0:01:00)
[assistant] The full suite passes (1092 passed). Now I'll add regression tests next to the existing lateral test: one for the reported field access, and one checking that the exploded element type is the struct and array element rather than the array.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n
…[305 chars elided]…
LODE(items) ci AS ci LATERAL VIEW EXPLODE(nums) t AS c\",\n                read=\"spark\",\n            ),\n            schema=schema,\n            dialect=\"spark\",\n        )\n        self.assertEqual(expression.selects[0].type.this, exp.DataType.Type.TEXT)\n        self.assertEqual(expression.selects[1].type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162234-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral 2>&1 | tail -4; <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py tests/test_optimizer.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py tests/test_optimizer.py 2>&1 | tail -3", "description": "Run lateral tests and lint/format checks"}
[tool_result] ..                                                                       [100%]
2 passed, 76 deselected in 0.25s
All checks passed!
Would reformat: sqlglot/optimizer/qualify_columns.py
1 file would be reformatted, 2 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/optimizer/qualify_columns.py 2>&1 | head -20; <work>/env-sqlglot/bin/python -m ruff format sqlglot/optimizer/qualify_columns.py && git diff --stat", "description": "Show and apply ruff formatting fix"}
[tool_result] --- sqlglot/optimizer/qualify_columns.py
+++ sqlglot/optimizer/qualify_columns.py
@@ -571,7 +571,9 @@
             and column.name not in resolver.get_source_columns(column_table)
         ):
             converted = True
-            column.replace(exp.Dot.build([exp.column(column_table, table=column_table), column.this]))
+            column.replace(
+                exp.Dot.build([exp.column(column_table, table=column_table), column.this])
+            )
             continue
 
         if (

1 file would be reformatted
1 file reformatted
 sqlglot/optimizer/annotate_types.py  |  8 ++++++--
 sqlglot/optimizer/qualify_columns.py | 16 ++++++++++++++++
 tests/test_optimizer.py              | 14 ++++++++++++++
 3 files changed, 36 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] The formatter only re-wrapped my new line. I'll run the full suite, lint, and the original repro once more on the final state.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $PY -m ruff check sqlglot tests/test_optimizer.py | tail -1; $PY -m ruff format --check sqlglot/optimizer tests/test_optimizer.py | tail -1; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nprint(optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\"; git diff sqlglot/", "description": "Run final tests, lint, repro, and review diff", "timeout": 600000}
[tool_result] .........                                                           [100%]
1093 passed, 17857 subtests passed in 50.21s
All checks passed!
22 files already formatted
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
diff --git a/sqlglot/optimizer/annotate_types.py b/sqlglot/optimizer/annotate_types.py
index 5d6b2b47a..fab521acb 100644
--- a/sqlglot/optimizer/annotate_types.py
+++ b/sqlglot/optimizer/annotate_types.py
@@ -289,7 +28
…[1674 chars elided]…
        and isinstance(source.expression, exp.Lateral)
+            and column_table in resolver.get_source_columns(column_table)
+            and column.name not in resolver.get_source_columns(column_table)
+        ):
+            converted = True
+            column.replace(
+                exp.Dot.build([exp.column(column_table, table=column_table), column.this])
+            )
+            continue
+
         if (
             column_table
             and column_table not in scope.sources
[assistant] The Spark `LATERAL VIEW EXPLODE` case now optimizes without error, and the exploded struct field gets its type. The full suite passes (1093 passed) and ruff check and format are clean. The changes are uncommitted in the worktree.

**Cause:** When the table alias equals the exploded column name (`ci ... AS ci`), the qualifier treated `ci` only as a table, so `ci.name` was never rewritten into a field access on the struct column. Separately, the exploded alias was typed as the whole array (`ARRAY<STRUCT<...>>`) rather than its element.

**Changes:**
- `sqlglot/optimizer/qualify_columns.py`: in `
…[379 chars elided]…
ugh unchanged, because the existing `test_lateral_annotation` pins `EXPLODE(int) AS c` to `INT`. I didn't edit that test.
- `tests/test_optimizer.py`: added `test_lateral_explode_struct_field_access`, which checks that `ci.name` is `STRING` and that `EXPLODE(nums) AS c` is `INT`.

Your repro now returns `SELECT ci.ci.name AS name ... LATERAL VIEW EXPLODE(items) ci AS ci`. The output type of `ci.name` is `STRING`, not `UNKNOWN`. One note: `SELECT ci.name ... EXPLODE(items) ci AS c` still raises `Unknown column`, which is correct because the struct's `name` column isn't visible under that alias.
