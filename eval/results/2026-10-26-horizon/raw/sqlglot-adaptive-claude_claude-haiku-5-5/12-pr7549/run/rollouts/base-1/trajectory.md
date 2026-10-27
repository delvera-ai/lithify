# trajectory base-1

final message:
The `EXPLODE` field-access case now optimizes correctly. The `ci.name` example from the report produces `SELECT ci.ci.name AS name … LATERAL VIEW EXPLODE(my_table.items) ci AS ci`, with the projection typed `STRING`.

**Root cause:** `ci` is a lateral source whose only column is the alias `ci`, and nothing knew that column is a struct when `qualify_columns` ran. So `ci.name` was treated as a column `name` on source `ci` and rejected as unknown. Struct field conversion (`_convert_columns_to_dots`) skips any prefix that is already a source, so it never applied here.

**Changes:**
- `sqlglot/optimizer/resolver.py`: new `Resolver.get_lateral_element_type`, which resolves the exploded array's element type through the lateral's scope.
- `sqlglot/optimizer/qualify_columns.py`: in `_convert_columns_to_dots`, when a column's table is a lateral alias and the element struct has that field, rewrite `ci.name` to `ci.ci.name`. Unknown fields still raise `Unknown column`.
- `sqlglot/optimizer/annotate_types.py`: for lateral explodes, the alias takes the array's element type instead of the array type, so `ci.ci.name` gets `STRING`. The `EXPLODE(a)` over an `INT` case keeps its existing `INT` type.
- `tests/test_optimizer.py`: added `test_lateral_struct_field_access` covering the SQL output and the projection type.

**Verification:** the full suite passes with the project's pytest command (1093 passed, including the new test). `ruff check`, `ruff format --check` and `mypy` on the touched modules are clean. I did not run the full `pre-commit` hook set.

**Not covered:** nested access such as `ci.name.first` still raises `Unknown column: name`. Handling it would need the same rewrite applied to the multi-part column path, which I left out to keep the change small. I can take that on if you want it in this change.

Nothing is committed.

## events
[assistant] I'll start by reproducing the failure in this worktree.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark')\nprint(e.sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The `-I` flag ignores the working directory, so `sqlglot` wasn't importable. Rerunning from the repo root.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nprint(sqlglot.__file__)\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark')\nprint(e.sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error from repo root"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[210 chars elided]…
timizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/__init__.py
[assistant] Reproduced: `Unknown column: name` from `qualify_columns`. Next I'll look at how the Spark/Hive `LATERAL VIEW` is parsed and how `qualify_columns` handles lateral table aliases.
[tool_use Bash] {"command": "grep -n -i \"lateral\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/parser.py | head -60; echo ---; grep -n -i \"lateral\\|explode\\|unnest\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py sqlglot/optimizer/scope.py | head -60", "description": "Find lateral view handling in parser and optimizer"}
[tool_result] sqlglot/parser.py:1046:        exp.Lateral: lambda self: self._parse_lateral(),
sqlglot/parser.py:4067:            for lateral in iter(self._parse_lateral, None):
sqlglot/parser.py:4068:                this.append("laterals", lateral)
sqlglot/parser.py:4266:    def _parse_lateral(self) -> exp.Lateral | None:
sqlglot/parser.py:4277:        elif self._match(TokenType.LATERAL):
sqlglot/parser.py:4306:            # We move the alias from the lateral's child node to the lateral itself
sqlglot/parser.
…[2383 chars elided]…
ot/optimizer/annotate_types.py:304:                        isinstance(expression, exp.Unnest)
sqlglot/optimizer/annotate_types.py:420:                    elif isinstance(source.expression, exp.Unnest):
sqlglot/optimizer/annotate_types.py:778:    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
sqlglot/optimizer/annotate_types.py:782:    def _annotate_unnest(self, expression: exp.Unnest) -> exp.Unnest:
sqlglot/optimizer/annotate_types.py:797:        query = expression.unnest()
[tool_use Bash] {"command": "sed -n 4266,4330p sqlglot/parser.py; echo ----ANN; sed -n 270,320p sqlglot/optimizer/annotate_types.py; echo ----ANN2; sed -n 405,440p sqlglot/optimizer/annotate_types.py; echo ---EXPL; sed -n 770,800p sqlglot/optimizer/annotate_types.py", "description": "Read lateral parsing and type annotation code"}
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
…[6781 chars elided]…

            expr_type = None

        self._set_type(expression, expr_type)
        return expression

    def _annotate_subquery(self, expression: exp.Subquery) -> exp.Subquery:
        # For scalar subqueries (subqueries with a single projection), infer the type
        # from that single projection. This allows type propagation in cases like:
        # SELECT (SELECT 1 AS c) AS c
        query = expression.unnest()

        if isinstance(query, exp.Query):
            selects = query.selects
[assistant] The parser sets the lateral's table alias `ci` with column `ci`, so `ci.name` becomes a column `name` on source `ci`. I need to see how `qualify_columns` resolves that and whether it has any struct-field handling.
[tool_use Bash] {"command": "sed -n 560,640p sqlglot/optimizer/qualify_columns.py; echo ---; grep -n \"def _get_source_columns\\|def _expand_struct\\|STRUCT\\|is_type\" sqlglot/optimizer/qualify_columns.py | head -40", "description": "Read unknown column resolution in qualify_columns"}
[tool_result]         column_table: str | exp.Identifier | None = column.table
        dot_parts = column.meta.pop("dot_parts", [])
        if (
            column_table
            and column_table not in scope.sources
            and (
                not scope.parent
                or column_table not in scope.parent.sources
                or not scope.is_correlated_subquery
            )
        ):
            root, *parts = column.parts

            if isinstance(root, exp.Identifier) and root.name in 
…[2929 chars elided]…
= part.name and field.kind.is_type(exp.DType.STRUCT):
708:def _expand_struct_stars_with_parens(expression: exp.Dot) -> list[exp.Alias]:
717:    if not isinstance(dot_column, exp.Column) or not dot_column.is_type(exp.DType.STRUCT):
808:    if dialect.SUPPORTS_STRUCT_STAR_EXPANSION and any(
834:                    dialect.SUPPORTS_STRUCT_STAR_EXPANSION
835:                    and not dialect.REQUIRES_PARENTHESIZED_STRUCT_ACCESS
841:                elif dialect.REQUIRES_PARENTHESIZED_STRUCT_ACCESS:
[tool_use Bash] {"command": "sed -n 540,560p sqlglot/optimizer/qualify_columns.py; echo ---; sed -n 60,100p sqlglot/optimizer/qualify_columns.py; echo ---; grep -n \"def get_source_columns\" -A25 sqlglot/optimizer/qualify_columns.py", "description": "Read struct-field conversion and source column lookup"}
[tool_result] def _select_by_pos(expression: exp.Selectable, node: exp.Literal) -> exp.Alias:
    try:
        return expression.selects[int(node.this) - 1].assert_is(exp.Alias)
    except IndexError:
        raise OptimizeError(f"Unknown output column: {node.name}")


def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
    """
    Converts `Column` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."fie
…[1169 chars elided]…
_to_dots(scope, resolver)
        _qualify_columns(
            scope,
            resolver,
            allow_partial_qualification=allow_partial_qualification,
        )

        if not schema.empty and expand_alias_refs:
            _expand_alias_refs(scope, resolver, dialect)

        if is_select:
            if expand_stars:
                _expand_stars(
                    scope,
                    resolver,
                    using_column_tables,
                    pseudocolumns,
---
[assistant] `_convert_columns_to_dots` only converts `a.b` into a struct field when `a` is not a source. Here `ci` *is* a source (the lateral alias), so the conversion is skipped and `_qualify_columns` then looks for a column `name` on that source. Next I'll check how the `Resolver` derives source columns for a lateral.
[tool_use Bash] {"command": "grep -n \"class Resolver\" -A75 sqlglot/optimizer/qualify_columns.py | head -120; echo; grep -n \"annotate_types\\|qualify_columns\\|RULES = \" sqlglot/optimizer/optimizer.py | head", "description": "Read Resolver class and optimizer rule order"}
[tool_result] 8:from sqlglot.optimizer.annotate_types import annotate_types
19:from sqlglot.optimizer.qualify_columns import quote_identifiers
52:    annotate_types,
[tool_use Bash] {"command": "grep -rn \"class Resolver\" sqlglot/optimizer/; sed -n 40,60p sqlglot/optimizer/optimizer.py", "description": "Locate Resolver class and rule order"}
[tool_result] sqlglot/optimizer/resolver.py:17:class Resolver:
RULES: tuple[OptimizerFn, ...] = (
    qualify,
    pushdown_projections,
    normalize,
    unnest_subqueries,
    pushdown_predicates,
    optimize_joins,
    eliminate_subqueries,
    merge_subqueries,
    eliminate_joins,
    eliminate_ctes,
    quote_identifiers,
    annotate_types,
    canonicalize,
    simplify,
)


def optimize(
    expression: str | exp.Expr,
    schema: dict[str, object] | Schema | None = None,
[tool_use Bash] {"command": "cat sqlglot/optimizer/resolver.py", "description": "Read the Resolver source"}
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
…[16052 chars elided]…
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
[assistant] The source for `ci` could be a `Scope` or a `Table`, and it matters which. I'll check what `get_source_columns("ci")` returns for this query.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.qualify_columns import *\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.schema import ensure_sch
…[232 chars elided]…
rgs.get('laterals')))\nfor s in traverse_scope(e):\n    print('scope', type(s.expression).__name__, {k:type(v).__name__ for k,v in s.sources.items()})\n    r = Resolver(s, schema)\n    for n in s.sources:\n        try: print(n, r.get_source_columns(n))\n        except Exception as ex: print(n, 'ERR', ex)\n\" 2>&1 | tail -30", "description": "Inspect scope sources and resolved columns for lateral"}
[tool_result] [Lateral(
  this=Explode(
    this=Column(
      this=Identifier(this=items, quoted=False))),
  view=True,
  outer=False,
  alias=TableAlias(
    this=Identifier(this=ci, quoted=False),
    columns=[
      Identifier(this=ci, quoted=False)]))]
scope Lateral {'my_table': 'Table'}
my_table ['items']
scope Select {'my_table': 'Table', 'ci': 'Scope'}
my_table ['items']
ci ['ci']
[assistant] `ci` resolves to just its alias column `['ci']`, and nothing knows that column is a struct at qualify time. Before choosing a fix, I'll check the existing tests for similar lateral/struct cases so the change follows the established pattern.
[tool_use Bash] {"command": "grep -rn -i \"lateral view\" tests/ --include=*.py --include=*.sql | grep -i \"optim\\|qualif\\|annot\" | head -30; echo ---; grep -rn -i \"lateral view explode\" tests/fixtures/optimizer/*.sql | head -30", "description": "Find existing lateral view optimizer tests"}
[tool_result] (eval):1: no matches found: --include=*.py
---
tests/fixtures/optimizer/optimizer.sql:3:SELECT a, m FROM z LATERAL VIEW EXPLODE([1, 2]) q AS m;
tests/fixtures/optimizer/qualify_columns.sql:794:SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:795:SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:798:SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:799:S
…[12 chars elided]…
S c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:802:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:803:SELECT t.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:839:SELECT c FROM (SELECT 1 a) AS x LATERAL VIEW EXPLODE(a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:840:SELECT _0.c AS c FROM (SELECT 1 AS a) AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
[tool_use Bash] {"command": "sed -n 785,845p tests/fixtures/optimizer/qualify_columns.sql; echo ---; grep -rn \"explode\\|EXPLODE\" tests/fixtures/optimizer/annotate_types.sql tests/test_optimizer.py | head -20; echo ---; grep -n \"qualify_columns.sql\\|def test_qualify_columns\" -A12 tests/test_optimizer.py | head -60", "description": "Read existing lateral explode qualify fixtures and test harness"}
[tool_result] --------------------------------------
# dialect: spark
SELECT /*+ BROADCAST(y) */ x.b FROM x JOIN y ON x.b = y.b;
SELECT /*+ BROADCAST(y) */ x.b AS b FROM x AS x JOIN y AS y ON x.b = y.b;

--------------------------------------
-- UDTF
--------------------------------------
# execute: false
SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;

# execute: false
SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
SELECT _0.c AS c FROM xx AS xx
…[3124 chars elided]…
, SchemaError)):
668-                    expression = optimizer.qualify_columns.qualify_columns(
669-                        parse_one(sql), schema=self.schema
670-                    )
671-                    optimizer.qualify_columns.validate_qualify_columns(expression)
672-
673-        # this makes sure the fallback scenario in get_table in resolver is covered
674-        # and the error message is column cannot be resolved instead of unknown table
675-        sql = """
676-            SELECT
[tool_use Bash] {"command": "sed -n 1330,1350p tests/test_optimizer.py; echo ---; sed -n 1488,1500p tests/test_optimizer.py; echo ---; grep -n \"lateral\\|LATERAL\" -i tests/dialects/test_spark.py tests/dialects/test_hive.py | head -30", "description": "Read related optimizer and dialect lateral tests"}
[tool_result]                 exp.DataType.Type.INT,
            ),
        ]:
            with self.subTest(sql):
                expression = annotate_types(parse_one(sql), schema=schema)
                self.assertEqual(expected_type, expression.expressions[0].type.this)
                self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.optimize(
            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expre
…[4982 chars elided]…
'tag': 'B', 'score': 99.5}}] AS info) SELECT h.id, amount, currency, type, val, leng FROM hourlycostagg AS h CROSS JOIN LATERAL (SELECT UNNEST(h.costs, max_depth => 2)) AS c CROSS JOIN LATERAL (SELECT UNNEST(h.adjustments, max_depth => 2)) AS _u_1(type, val, curr) CROSS JOIN LATERAL (SELECT UNNEST(h.info, max_depth => 2)) AS exploded(leng, det)",
tests/dialects/test_spark.py:467:            "SELECT id_column, name, age FROM test_table LATERAL VIEW INLINE(struc_column) explode_view AS name, age",
[assistant] The existing tests pin current lateral behaviour, including `EXPLODE(a)` over an `INT` giving `INT`, so I need to keep that working. Next I'll check whether `annotate_types` can run on a standalone `Lateral` node, which decides how qualify can learn the struct type.
[tool_use Bash] {"command": "sed -n 1,25p sqlglot/optimizer/qualify_columns.py | grep -n import; echo ---; grep -n \"^from\\|^import\" sqlglot/optimizer/annotate_types.py; echo ---; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_ty
…[396 chars elided]…
'|', a.this.this.type.sql('spark'))\n# what does a qualified select see\nq = sqlglot.optimizer.qualify.qualify(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark', validate_qualify_columns=False, identify=False) if False else None\n\" 2>&1 | tail -5", "description": "Check annotate_types on a standalone lateral node"}
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
13:from sqlglot.optimizer.simplif
…[19 chars elided]…
arens
14:from sqlglot.schema import Schema, ensure_schema
17:    from sqlglot._typing import E
18:    from collections.abc import Iterator, Iterable
---
1:from __future__ import annotations
3:import functools
4:import logging
5:import typing as t
7:from sqlglot import exp
8:from sqlglot.dialects.dialect import Dialect
9:from sqlglot.helper import (
16:from sqlglot.optimizer.scope import Scope, traverse_scope
17:from sqlglot.schema import MappingSchema, Schema, ensure_schema
---
UNKNOWN | UNKNOWN
[assistant] Annotating a bare `Lateral` gives `UNKNOWN`, but that copy was unqualified. I'll check whether the qualified form resolves the element type.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfr
…[211 chars elided]…
ems) ci AS ci', read='spark')\ne = qualify_tables(e, dialect='spark')\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nlat = e.args['laterals'][0].copy()\nprint(lat.sql('spark'))\na = annotate_types(lat, schema=schema, dialect='spark')\nprint(a.this.type.sql('spark'), '|', a.this.this.type.sql('spark'))\n\" 2>&1 | tail -8", "description": "Test annotation on qualified lateral node"}
[tool_result] LATERAL VIEW EXPLODE(items) ci AS ci
UNKNOWN | UNKNOWN
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfr
…[298 chars elided]…
alify_columns(e, schema, dialect='spark', allow_partial_qualification=True)\nexcept Exception as ex: print('qc err', ex)\nlat = e.args['laterals'][0].copy()\nprint(lat.sql('spark'))\na = annotate_types(lat, schema=schema, dialect='spark')\nprint(a.this.type.sql('spark'), '|', a.this.this.type.sql('spark'))\n\" 2>&1 | tail -8", "description": "Test annotation after column qualification of lateral"}
[tool_result] LATERAL VIEW EXPLODE(my_table.items) ci AS ci
UNKNOWN | UNKNOWN
[assistant] Annotating a standalone lateral still yields `UNKNOWN` because its source table isn't in scope. The existing `Resolver._get_column_type_from_scope` already resolves a column's type through a scope's sources, so I'll reuse it for the explode argument. Checking the imports and the `Dot` handling before I edit.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/optimizer/qualify_columns.py; echo ---; sed -n 745,778p sqlglot/optimizer/annotate_types.py", "description": "Read qualify_columns imports and Dot annotation"}
[tool_result] from __future__ import annotations

import itertools
import typing as t

from sqlglot import alias, exp
from sqlglot.dialects.dialect import Dialect, DialectType
from sqlglot.errors import OptimizeError, highlight_sql
from sqlglot.helper import seq_get
from sqlglot.optimizer.annotate_types import TypeAnnotator
from sqlglot.optimizer.resolver import Resolver
from sqlglot.optimizer.scope import Scope, build_scope, traverse_scope, walk_in_scope
from sqlglot.optimizer.simplify import simplify_parens
…[1326 chars elided]…
exp.Anonymous):
            self._set_type(expression, expression.expression.type)
            return expression

        this_type = expression.this.type

        if this_type and this_type.is_type(exp.DType.STRUCT):
            for e in this_type.expressions:
                if e.name == expression.expression.name:
                    self._set_type(expression, e.kind)
                    break

        return expression

    def _annotate_explode(self, expression: exp.Explode) -> exp.Explode:
[assistant] I'll add the element-type lookup to `Resolver`, next to the existing `_get_unnest_column_type`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/resolver.py", "old_string": "        source = scope.sources.get(table_name)\n        return self._get_column_type_from_scope(source, column) if source else None\n\n    def _get_column_type_from_scope(", "new_string": "        source = sc
…[684 chars elided]…
p.Column) or not column.table:\n            return None\n\n        source = lateral_scope.sources.get(column.table)\n        col_type = self._get_column_type_from_scope(source, column) if source else None\n\n        if col_type and col_type.is_type(exp.DType.ARRAY) and col_type.expressions:\n            return col_type.expressions[0]\n\n        return None\n\n    def _get_column_type_from_scope("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/resolver.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll make `_convert_columns_to_dots` turn `ci.name` into `ci.ci.name` when `ci` is a lateral alias whose element struct has that field.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        column_table = column.table\n        dot_parts = column.meta.pop(\"dot_parts\", [])\n        if (\n            column_table\n            and column_table not in scope.sources", "new_string": " 
…[679 chars elided]…
              and any(field.name == column.name for field in struct_type.expressions)\n                ):\n                    new_column = exp.column(source_columns[0], table=column_table)\n                    column.replace(exp.Dot.build([new_column, column.this]))\n                    converted = True\n\n        if (\n            column_table\n            and column_table not in scope.sources"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:         column_table = column.table
        dot_parts = column.meta.pop("dot_parts", [])
        if (
            column_table
            and column_table not in scope.sources</tool_use_error>
[assistant] The variable is annotated (`column_table: str | exp.Identifier | None`), so the match failed. Retrying with the exact line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        column_table: str | exp.Identifier | None = column.table\n        dot_parts = column.meta.pop(\"dot_parts\", [])\n        if (\n            column_table\n            and column_table not in sco
…[737 chars elided]…
              and any(field.name == column.name for field in struct_type.expressions)\n                ):\n                    new_column = exp.column(source_columns[0], table=column_table)\n                    column.replace(exp.Dot.build([new_column, column.this]))\n                    converted = True\n\n        if (\n            column_table\n            and column_table not in scope.sources"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Rerunning the reproduction and the lateral-related optimizer tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nfor sql in ['SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci',\n            'SELEC
…[174 chars elided]…
      e = optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark')\n        print(e.sql('spark'))\n    except Exception as ex: print(type(ex).__name__, ex)\n\" 2>&1 | tail -8; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"lateral or qualify or annotat or unnest\" 2>&1 | tail -15", "description": "Verify fix on repro and related optimizer tests"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
OptimizeError Unknown column: nope
OptimizeError Unknown column: name
...... [ 13%]
......................................                                      [100%]
44 passed, 33 deselected, 2655 subtests passed in 5.15s
[assistant] The basic case now resolves to `ci.ci.name`, and the existing lateral/qualify/annotate tests pass. The nested form `ci.name.first` still fails; I'll decide on that after checking the rest. Next I'll run the full suite using the project's test command.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
...........................................................................................................................
…[334 chars elided]…
........................................................................ [ 77%]
............................................. [ 81%]
.... [ 81%]
...................................................................... [ 88%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 130.08s (0:02:10)
[assistant] The full suite passes (1092 tests, 17857 subtests). Before adding a regression test, I'll check the type that annotation assigns to the projection, since the issue asks for type-annotated field access.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nprint(e.sql('spark'))\nprint(e.expressions[0].type.sql('spark'))\nprint(e.expressions[0].this.this.type.sql('spark') if e.expressions[0].this.this.type else None)\n\" 2>&1 | tail -5", "description": "Check annotated type of optimized projection"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
UNKNOWN
ARRAY<STRUCT<name: STRING>>
[assistant] The optimized query now runs, but the projection's type is `UNKNOWN`, and `ci.ci` is typed `ARRAY<STRUCT<…>>` instead of the struct. `_get_scope_selects` takes the exploded array's type for the alias, and this has to be the element type. I'll unwrap the array for lateral explodes only, so the existing `EXPLODE(a)` over an `INT` case keeps its current `INT` type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py", "old_string": "                    else:\n                        selects[name] = {\n                            alias: column.type for alias, column in zip(alias_column_names, values)\n                        }", "ne
…[172 chars elided]…
ons[0]\n                                if isinstance(expression, exp.Lateral)\n                                and column.is_type(exp.DType.ARRAY)\n                                and column.type.expressions\n                                else column.type\n                            )\n                            for alias, column in zip(alias_column_names, values)\n                        }"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/annotate_types.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\ne = optimize(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark'), schema=schema, dialect='spark')\nprint(e.sql('spark'))\nprint(e.expressions[0].type.sql('spark'))\n\" 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Recheck type and run full test suite", "timeout": 900000}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
STRING
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 108.12s (0:01:48)
[assistant] Full suite still passes, and the projection is now typed `STRING`. Next I'll add a regression test next to `test_lateral_annotation`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n
…[332 chars elided]…
lect=\"spark\",\n        )\n        self.assertEqual(\n            expression.sql(\"spark\"),\n            \"SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` \"\n            \"LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`\",\n        )\n        self.assertTrue(expression.expressions[0].is_type(*exp.DataType.TEXT_TYPES))\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Running the new test, then the linter and type checker on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral 2>&1 | tail -3; ($PY -m ruff check sqlglot/optimizer/ tests/test_optimizer.py && $PY -m ruff format --check sqlglot/optimizer/ tests/test_optimizer.py) 2>&1 | tail -5; grep -n \"^style:\" -A6 Makefile", "description": "Run new test, lint, and format check"}
[tool_result] ..                                                                       [100%]
2 passed, 76 deselected in 0.33s
All checks passed!
22 files already formatted
83:style:
84-	pre-commit run --all-files
85-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
86-
87-check: style test testc
88-
89-docs:
[assistant] Ruff passes. The pre-commit config also runs mypy, so I'll run that on the touched modules.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py 2>&1 | tail -5; git status --short; git diff --stat", "description": "Run mypy on changed modules and show diff stat"}
[tool_result] sqlglot/optimizer/qualify_columns.py:564: error: Argument 1 to "get" of "dict" has incompatible type "str | Identifier | None"; expected "str"  [arg-type]
sqlglot/optimizer/qualify_columns.py:567: error: Argument 1 to "get_source_columns" of "Resolver" has incompatible type "str | Identifier | None"; expected "str"  [arg-type]
Found 2 errors in 1 file (checked 3 source files)
 M sqlglot/optimizer/annotate_types.py
 M sqlglot/optimizer/qualify_columns.py
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
 sqlglot/optimizer/annotate_types.py  |  9 ++++++++-
 sqlglot/optimizer/qualify_columns.py | 16 ++++++++++++++++
 sqlglot/optimizer/resolver.py        | 23 +++++++++++++++++++++++
 tests/test_optimizer.py              | 15 +++++++++++++++
 4 files changed, 62 insertions(+), 1 deletion(-)
[assistant] mypy flags `column_table`, which is typed `str | Identifier | None`. `column.table` is a `str`, so I'll use that directly in the new block.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        lateral = scope.sources.get(column_table)\n        if isinstance(lateral, Scope) and isinstance(lateral.expression, exp.Lateral):\n            # e.g. `ci.name` in `LATERAL VIEW EXPLODE(items) c
…[967 chars elided]…
_columns:\n                struct_type = resolver.get_lateral_element_type(lateral)\n                if (\n                    struct_type\n                    and struct_type.is_type(exp.DType.STRUCT)\n                    and any(field.name == column.name for field in struct_type.expressions)\n                ):\n                    new_column = exp.column(source_columns[0], table=column.table)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-181248-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/annotate_types.py 2>&1 | tail -3; $PY -m ruff check sqlglot tests/test_optimizer.py | tail -1; $PY -m ruff format --check sqlglot tests/test_optimizer.py | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Recheck mypy, ruff, and full test suite", "timeout": 900000}
[tool_result] Success: no issues found in 3 source files
All checks passed!
175 files already formatted
.........                                                           [100%]
1093 passed, 17857 subtests passed in 73.65s (0:01:13)
[assistant] The `EXPLODE` field-access case now optimizes correctly. The `ci.name` example from the report produces `SELECT ci.ci.name AS name … LATERAL VIEW EXPLODE(my_table.items) ci AS ci`, with the projection typed `STRING`.

**Root cause:** `ci` is a lateral source whose only column is the alias `ci`, and nothing knew that column is a struct when `qualify_columns` ran. So `ci.name` was treated as a column `name` on source `ci` and rejected as unknown. Struct field conversion (`_convert_columns_to_dots`) skips any prefix that is already a source, so it never applied here.

**Changes:**
- `sqlglot/opti
…[648 chars elided]…
l_struct_field_access` covering the SQL output and the projection type.

**Verification:** the full suite passes with the project's pytest command (1093 passed, including the new test). `ruff check`, `ruff format --check` and `mypy` on the touched modules are clean. I did not run the full `pre-commit` hook set.

**Not covered:** nested access such as `ci.name.first` still raises `Unknown column: name`. Handling it would need the same rewrite applied to the multi-part column path, which I left out to keep the change small. I can take that on if you want it in this change.

Nothing is committed.
