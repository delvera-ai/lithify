# trajectory base-1

final message:
The `LATERAL VIEW EXPLODE` query now optimizes correctly. `ci.name` resolves to the struct field, and the projected column is typed as TEXT. The full suite passes (1093 tests, including a new regression test).

Your repro produced `Unknown column: name` for two reasons:

- **Qualify (`sqlglot/optimizer/qualify_columns.py`)**: when the table alias `ci` is also the exploded column name, `ci.name` was treated as a reference to a column `name` on table `ci`. Spark resolves this as the exploded column `ci` followed by the field `name`. I added a narrow fallback in `_convert_columns_to_dots` for Lateral sources that rewrites it to `ci.ci.name`. It only applies when the column name is missing from the alias's columns and the alias is one of them.
- **Annotation (`sqlglot/optimizer/annotate_types.py`)**: the exploded alias was typed as the array argument (`ARRAY<STRUCT<...>>`) rather than its element type. It now takes the Explode node's type. `_annotate_explode` falls back to the argument's own type when there is no element type. The existing `test_lateral_annotation` depends on that fallback, since it explodes a plain `INT`.

I added `test_lateral_explode_struct_field_access` in `tests/test_optimizer.py`. It covers both the shadowing case from the report and the case where the table alias is different (`t AS ci`). No existing tests were changed.

Output for your example:
```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

I ran pytest with the project's configured interpreter and `ruff format`/`ruff check`, which both pass. I did not run `make check` (mypy isn't included). I also haven't committed anything.

## events
[assistant] I'll reproduce the failure first, then trace it through the optimizer.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark')\nprint(e.sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[82 chars elided]…
^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
[assistant] Reproduced: `Unknown column: name`. Next I'll look at how the qualifier handles the LATERAL VIEW alias and how types flow through Explode.
[tool_use Bash] {"command": "grep -n -i \"lateral\\|explode\\|unnest\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/annotate_types.py sqlglot/dialects/hive.py sqlglot/dialects/spark*.py | head -80; echo ---; grep -n \"class Explode\\|class Lateral\\|class Unnest\\|class Posexplode\" sqlglot/expressions.py", "description": "Find lateral/explode handling in optimizer"}
[tool_result ERROR] Exit code 2
sqlglot/optimizer/qualify_columns.py:530:                    or select_expr.find(exp.Explode, exp.Unnest)
sqlglot/optimizer/qualify_columns.py:626:            # column_table can be a '' because bigquery unnest has no table alias
sqlglot/optimizer/annotate_types.py:290:                    if isinstance(expression, exp.Lateral):
sqlglot/optimizer/annotate_types.py:291:                        if isinstance(expression.this, exp.Explode):
sqlglot/optimizer/annotate_types.py:293:          
…[1810 chars elided]…
     lateral_sources = sources
sqlglot/optimizer/scope.py:841:            lateral_sources = None
sqlglot/optimizer/scope.py:856:                lateral_sources=lateral_sources,
sqlglot/optimizer/scope.py:888:    if isinstance(scope.expression, exp.Unnest):
sqlglot/optimizer/scope.py:890:    elif isinstance(scope.expression, exp.Lateral):
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 270,320p sqlglot/optimizer/annotate_types.py; echo ---; sed -n 770,800p sqlglot/optimizer/annotate_types.py; echo ---; sed -n 515,560p sqlglot/optimizer/qualify_columns.py; echo ---; grep -n \"class Explode\\b\\|class Explode(\" sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null", "description": "Read relevant optimizer sections"}
[tool_result]         # Replace NULL type with the default type of the targeted dialect, since the former is not an actual type;
        # it is mostly used to aid type coercion, e.g. in query set operations.
        # TODO (mypyc): uses list() + _set_type instead of direct expr.type = ... because
        # mypyc's property setter bypass rejects DType, and _set_type modifies the dict.
        for expr in list(self._null_expressions.values()):
            self._set_type(expr, self.dialect.DEFAULT_NULL_TYPE)

 
…[4465 chars elided]…
` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."field2"), but they need to be
    normalized to `Dot(Dot(...(<table>.<column>, field1), field2, ...))` to be qualified properly.
    """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot):
            continue

---
sqlglot/expressions/array.py:225:class Explode(Expression, Func, UDTF):
[assistant] The likely culprit is `_get_scope_selects`: it maps the exploded column alias to the type of the *array* argument rather than its element type. I'll confirm that by checking the parsed AST and the qualified output.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot import exp\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = sqlglot.parse_
…[307 chars elided]…
Exception as ex: print('ERR', ex)\nprint('---- explicit struct access with different alias')\nsql3 = 'SELECT t.ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci'\ntry:\n  print(qualify(sqlglot.parse_one(sql3, read='spark'), schema=schema, dialect='spark').sql('spark'))\nexcept Exception as ex: print('ERR', ex)\n\" 2>&1 | tail -30", "description": "Inspect lateral AST and qualify variants"}
[tool_result] Lateral(
  this=Explode(
    this=Column(
      this=Identifier(this=items, quoted=False))),
  view=True,
  outer=False,
  alias=TableAlias(
    this=Identifier(this=ci, quoted=False),
    columns=[
      Identifier(this=ci, quoted=False)]))
---- qualify w/o struct field (alias ci.x works?)
SELECT `t`.`ci` AS `ci` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
---- explicit struct access with different alias
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
[assistant] Explicit `t.ci.name` works, so the failure is specific to `ci.name`, where `ci` is both the table alias and the column alias. Let me check a few variants to confirm which part matters.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ncases = [\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci',\n 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items)
…[191 chars elided]…
ify','optimize'):\n    try:\n      r = qualify(sqlglot.parse_one(s, read='spark'), schema=schema, dialect='spark') if fn=='qualify' else optimize(sqlglot.parse_one(s, read='spark'), schema=schema, dialect='spark')\n      print(fn, 'OK ', r.sql('spark'))\n    except Exception as ex: print(fn, 'ERR', type(ex).__name__, ex)\n\" 2>&1 | tail -30", "description": "Test variants of lateral alias naming"}
[tool_result] qualify OK  SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
optimize OK  SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
qualify ERR OptimizeError Unknown column: name
optimize ERR OptimizeError Unknown column: name
qualify ERR OptimizeError Unknown column: name
optimize ERR OptimizeError Unknown column: name
qualify ERR OptimizeError Unknown column: name
optimize ERR OptimizeError Unknown column: name
[assistant] Now the picture is clear. The failing cases are the ones where `ci` is both the table alias and the column alias. Spark resolves `ci.name` by falling back to column `ci` plus field `name` in that case. Let me read the column-to-dot conversion and the resolver logic.
[tool_use Bash] {"command": "sed -n 555,650p sqlglot/optimizer/qualify_columns.py", "description": "Read _convert_columns_to_dots and column resolution"}
[tool_result]     """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot):
            continue

        column_table: str | exp.Identifier | None = column.table
        dot_parts = column.meta.pop("dot_parts", [])
        if (
            column_table
            and column_table not in scope.sources
            and (
                not scope.parent
                or column_table not in scope.parent.sources
                or not scope
…[2712 chars elided]…
 1
                and column_name in scope.selected_sources
            ):
                # BigQuery and Postgres allow tables to be referenced as columns, treating them as structs/records
                scope.replace(column, exp.TableColumn(this=column.this))

    for pivot in scope.pivots:
        for column in pivot.find_all(exp.Column):
            if not column.table and column.name in resolver.all_columns:
                table = resolver.get_table(column.name)
                if table:
[assistant] The check at `_qualify_columns` fires because `ci` is a real source name, so `_convert_columns_to_dots` (which only handles columns whose table is *not* a source) never gets a chance. Before choosing a fix, I need to see how the Resolver gets source columns for a UDTF.
[tool_use Bash] {"command": "grep -n \"def get_source_columns\\|def _get_all_source_columns\\|def get_table\\|def all_columns\\|def _get_source_columns\" sqlglot/optimizer/qualify_columns.py; sed -n \"$(grep -n 'def get_source_columns' sqlglot/optimizer/qualify_columns.py | cut -d: -f1),+40p\" sqlglot/optimizer/qualify_columns.py; echo ---; grep -n \"def _get_source_columns\\|def get_source_columns\" -A3 sqlglot/optimizer/scope.py | head; grep -n \"def _get_source_columns\\|_get_source_columns\" -n sqlglot/optimizer/*.py | head", "description": "Read Resolver.get_source_columns"}
[tool_result] sed: 1: ",+40p
": invalid command code ,
---
sqlglot/optimizer/resolver.py:32:        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}
sqlglot/optimizer/resolver.py:136:        if cache_key not in self._get_source_columns_cache:
sqlglot/optimizer/resolver.py:201:            self._get_source_columns_cache[cache_key] = columns
sqlglot/optimizer/resolver.py:203:        return self._get_source_columns_cache[cache_key]
[tool_use Bash] {"command": "sed -n 125,205p sqlglot/optimizer/resolver.py", "description": "Read Resolver source column logic"}
[tool_result]                 columns = list(dict.fromkeys(left + right))
            elif kind == "INNER":
                columns = list(dict.fromkeys(left).keys() & dict.fromkeys(right).keys())
        else:
            columns = set_op.named_selects

        return columns

    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._ge
…[3192 chars elided]…
he corresponding column names.
                # This can be expensive if there are lots of columns, so only do this if column_aliases exist.
                columns = [
                    alias or name
                    for (name, alias) in itertools.zip_longest(columns, column_aliases)
                ]

            self._get_source_columns_cache[cache_key] = columns

        return self._get_source_columns_cache[cache_key]

    def _get_all_source_columns(self) -> dict[str, Sequence[str]]:
[assistant] The Lateral source goes through a generic branch here, so I need to see what `get_source_columns('ci')` actually returns for this query.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.optimizer.qualify_columns import _get_unambiguous_columns\nsql = 'SELEC
…[340 chars elided]…
ema, dialect='spark')\nprint(repr(e2.args['laterals'][0].this.type))\ns = build_scope(sqlglot.parse_one(sql, read='spark'))\nprint({k:type(v).__name__ for k,v in s.sources.items()})\nprint(s.sources['ci'].expression.__class__)\nr = Resolver(s, schema, infer_schema=True)\nprint('cols ci:', r.get_source_columns('ci'))\n\" 2>&1 | tail -30", "description": "Inspect scope sources and resolver columns"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
ImportError: cannot import name '_get_unambiguous_columns' from 'sqlglot.optimizer.qualify_columns' (~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.scope import build_scope\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.resolver import Resolver\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = 
…[192 chars elided]…
][0].this.type))\ns = build_scope(sqlglot.parse_one(sql, read='spark'))\nprint({k:type(v).__name__ for k,v in s.sources.items()})\nprint(type(s.sources['ci'].expression).__name__)\nr = Resolver(s, sqlglot.schema.MappingSchema(schema, dialect='spark'), infer_schema=True)\nprint('cols ci:', r.get_source_columns('ci'))\n\" 2>&1 | tail -30", "description": "Inspect scope sources and resolver columns"}
[tool_result] explode type: DataType(this=DType.UNKNOWN)
{'my_table': 'Table', 'ci': 'Scope'}
Lateral
cols ci: ['ci']
[assistant] Two findings. First, after `annotate_types` the Explode type is `UNKNOWN`, which I suspect comes from running annotation before the `items` column is qualified. Second, the resolver reports the source's columns as `['ci']`, so `name` is rejected. Next I'll check the qualify pipeline order and whether annotation after qualify gives the right element type.
[tool_use Bash] {"command": "sed -n 1,95p sqlglot/optimizer/qualify_columns.py | grep -n \"def \\|_convert_columns_to_dots\\|_qualify_columns\\|_expand\\|for scope\" ; grep -n \"_convert_columns_to_dots\\|_qualify_columns(\\|def qualify_columns\\|_expand_alias_refs\\|_expand_stars\\|_qualify_outputs\" sqlglot/optimizer/qualify_columns.py", "description": "Check qualify_columns pass ordering"}
[tool_result] 21:def qualify_columns(
62:    for scope in traverse_scope(expression):
74:        using_column_tables = _expand_using(scope, resolver)
77:            _expand_alias_refs(
84:        _convert_columns_to_dots(scope, resolver)
85:        _qualify_columns(
92:            _expand_alias_refs(scope, resolver, dialect)
21:def qualify_columns(
77:            _expand_alias_refs(
84:        _convert_columns_to_dots(scope, resolver)
85:        _qualify_columns(
92:            _expand_alias_refs(scope, resolver, dialect)
96:                _expand_stars(
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
314:def _expand_alias_refs(
549:def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
599:def _qualify_columns(
770:def _expand_stars(
[assistant] The pipeline runs `_convert_columns_to_dots` immediately before `_qualify_columns`, and the Resolver has no type info at that point. So the fix in qualify has to be structural: a Lateral alias that shadows a column name should fall back to field access, matching Spark's resolution order. I'll apply that, then check whether annotation then gives the field the right type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    converted = False\n    for column in itertools.chain(scope.columns, scope.stars):\n        if isinstance(column, exp.Dot):\n            continue\n\n        column_table: str | exp.Identifier | None
…[781 chars elided]…
  and column.name not in (source_columns := resolver.get_source_columns(column_table.name))\n                and column_table.name in source_columns\n            ):\n                column.replace(\n                    exp.Dot.build([exp.column(column_table.name, table=column_table.name), column.this])\n                )\n                converted = True\n                continue\n\n        if ("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] I used `.name` on `column_table`, but `Column.table` is a string here. I'll simplify the block and fix that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        # e.g. `LATERAL VIEW EXPLODE(items) ci AS ci`: `ci.name` is the exploded column `ci` followed by\n        # the struct field `name`, since `ci` is the table alias but the table itself has no `n
…[933 chars elided]…
)\n            and isinstance(source.expression, exp.Lateral)\n            and column.name not in resolver.get_source_columns(column_table)\n            and column_table in resolver.get_source_columns(column_table)\n        ):\n            column.replace(exp.Dot.build([exp.column(column_table, table=column_table), column.this]))\n            converted = True\n            continue\n\n        if ("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" sqlglot/optimizer/qualify_columns.py | head -20; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor s in ['SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci','SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci']:\n  o = optimize(sqlglot.parse_one(s, read='spark'), schema=schema, dialect='spark')\n  print(o.sql('spark'))\n  print(repr(o.selects[0].type))\n\" 2>&1 | tail -20", "description": "Re-run repro after the qualify change"}
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
13:from sqlglot.optimizer.simplify import simplify_parens
14:from sqlglot.schema import Schema, ensure_schema
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
DataType(this=DType.UNKNOWN)
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
DataType(this=DType.UNKNOWN)
[assistant] The query no longer errors, but the projected `name` is `UNKNOWN`. That's the annotation half of the hint. The `_get_scope_selects` branch maps the exploded alias to the array argument's type (`ARRAY<STRUCT>`) instead of the element type. I'll switch it to the Explode node so the alias gets the element type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "                        if isinstance(expression.this, exp.Explode):\n                            values = [expression.this.this]", "new_string": "                        if isinstance(expression.this, exp.Explode):\n                            values = [expression.this]"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor s in ['SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci','SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci','SELECT t.ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci']:\n  o = optimize(sqlglot.parse_one(s, read='spark'), schema=schema, dialect='spark')\n  print(o.sql('spark'))\n  print(repr(o.selects[0].type))\n\" 2>&1 | tail -20", "description": "Check output SQL and types after annotation fix"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
DataType(this=DType.TEXT, nested=False)
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
DataType(this=DType.TEXT, nested=False)
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
DataType(this=DType.TEXT, nested=False)
[assistant] Both the error and the type are fixed: `name` is now TEXT. Next I'll run the full test suite with the project's configured command to check for regressions.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
...........................................................................................................................
…[1119 chars elided]…
_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expressions[0]
>       self.assertEqual(expression.type.this, exp.DataType.Type.INT)
E       AssertionError: <DType.UNKNOWN: 'UNKNOWN'> != <DType.INT: 'INT'>

tests/test_optimizer.py:1342: AssertionError
=========================== short test summary info ============================
FAILED tests/test_optimizer.py::TestOptimizer::test_lateral_annotation - Asse...
1 failed, 1091 passed, 17857 subtests passed in 52.31s
[assistant] One existing test regresses: `test_lateral_annotation` uses `EXPLODE(a)` where `a` is a plain `INT`, and it expects the alias to be `INT`. My change makes the alias take the Explode's type, which is `UNKNOWN` for a non-array argument. I can't weaken that test, so `_annotate_explode` needs to fall back to the argument's type when the argument has no element type. I'll keep the element-type path as the primary behaviour.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:\n        self._set_type(expression, seq_get(expression.this.type.expressions, 0))\n        return expression", "new_string": "    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:\n        this_type = expression.this.type\n        element_type = seq_get(this_type.expressions, 0)\n        self._set_type(expression, element_type if element_type else this_type)\n        return expression"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[assistant] `if element_type` depends on how `DataType` defines truthiness, so I'll make the check explicit with `is not None`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "        self._set_type(expression, element_type if element_type else this_type)", "new_string": "        self._set_type(expression, this_type if element_type is None else element_type)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\no = optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nprint(o.sql('spark'), repr(o.selects[0].type.this))\n\"", "description": "Rerun full suite and repro", "timeout": 900000}
[tool_result] ............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 51.59s
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci` <DType.TEXT: 'TEXT'>
[assistant] All 1092 tests pass, and the repro now produces TEXT. Next I'll add regression tests next to the existing lateral-annotation test.
[tool_use Bash] {"command": "sed -n 1325,1350p tests/test_optimizer.py; grep -n \"^from\\|^import\" tests/test_optimizer.py", "description": "View existing lateral tests and imports"}
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
…[709 chars elided]…
6:import duckdb
7:from pandas.testing import assert_frame_equal
9:import sqlglot
10:from sqlglot import exp, optimizer, parse_one
11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
12:from sqlglot.optimizer.annotate_types import annotate_types
13:from sqlglot.optimizer.normalize import normalization_distance
14:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
15:from sqlglot.schema import MappingSchema
16:from tests.helpers import (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n
…[661 chars elided]…
\",\n            ),\n        ):\n            with self.subTest(sql):\n                optimized = optimizer.optimize(parse_one(sql, read=\"spark\"), schema=schema, dialect=\"spark\")\n                self.assertEqual(optimized.sql(\"spark\"), expected)\n                self.assertEqual(optimized.selects[0].type.this, exp.DataType.Type.TEXT)\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-093454-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] I'll run the new test, the full suite, and the linter on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"lateral\" 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; ($PY -m ruff --version && $PY -m ruff format --check sqlglot/optimizer tests/test_optimizer.py; $PY -m ruff check sqlglot/optimizer tests/test_optimizer.py) 2>&1 | tail -15", "description": "Run lateral tests, full suite, and ruff", "timeout": 900000}
[tool_result] ..                                                                     [100%]
2 passed, 76 deselected, 2 subtests passed in 0.37s
...........                                                         [100%]
1093 passed, 17859 subtests passed in 56.35s
ruff 0.15.6
Would reformat: sqlglot/optimizer/qualify_columns.py
Would reformat: tests/test_optimizer.py
2 files would be reformatted, 20 files already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && git diff --stat && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1 && git diff sqlglot/", "description": "Apply ruff formatting and show final diff", "timeout": 900000}
[tool_result] 2 files reformatted
 sqlglot/optimizer/annotate_types.py  |  6 ++++--
 sqlglot/optimizer/qualify_columns.py | 16 ++++++++++++++++
 tests/test_optimizer.py              | 20 ++++++++++++++++++++
 3 files changed, 40 insertions(+), 2 deletions(-)
1093 passed, 17859 subtests passed in 56.06s
diff --git a/sqlglot/optimizer/annotate_types.py b/sqlglot/optimizer/annotate_types.py
index 5d6b2b47a..d936d6cee 100644
--- a/sqlglot/optimizer/annotate_types.py
+++ b/sqlglot/optimizer/annotate_types.py
@@ -2
…[1878 chars elided]…
 and column_table in resolver.get_source_columns(column_table)
+        ):
+            column.replace(
+                exp.Dot.build([exp.column(column_table, table=column_table), column.this])
+            )
+            converted = True
+            continue
+
         if (
             column_table
             and column_table not in scope.sources
[This command modified 2 files you've previously read: tests/test_optimizer.py, sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] The `LATERAL VIEW EXPLODE` query now optimizes correctly. `ci.name` resolves to the struct field, and the projected column is typed as TEXT. The full suite passes (1093 tests, including a new regression test).

Your repro produced `Unknown column: name` for two reasons:

- **Qualify (`sqlglot/optimizer/qualify_columns.py`)**: when the table alias `ci` is also the exploded column name, `ci.name` was treated as a reference to a column `name` on table `ci`. Spark resolves this as the exploded column `ci` followed by the field `name`. I added a narrow fallback in `_convert_columns_to_dots` for Lat
…[501 chars elided]…
k, since it explodes a plain `INT`.

I added `test_lateral_explode_struct_field_access` in `tests/test_optimizer.py`. It covers both the shadowing case from the report and the case where the table alias is different (`t AS ci`). No existing tests were changed.

Output for your example:
```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

I ran pytest with the project's configured interpreter and `ruff format`/`ruff check`, which both pass. I did not run `make check` (mypy isn't included). I also haven't committed anything.
