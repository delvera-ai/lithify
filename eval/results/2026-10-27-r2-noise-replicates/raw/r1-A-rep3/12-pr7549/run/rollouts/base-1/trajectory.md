# trajectory base-1

final message:
The reported query now optimizes instead of raising `OptimizeError`. The full suite passes (1093 tests) and ruff is clean. I haven't committed.

```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Cause:** `ci.name` was read as column `name` of table `ci`. The lateral only exposes `ci`, so qualification failed with "Unknown column: name". Nothing looked through the exploded struct.

**Fix:** In `sqlglot/optimizer/qualify_columns.py`, a new `_convert_lateral_struct_columns` pass runs before column qualification. When a column's table is a `LATERAL VIEW EXPLODE` alias that shares its name with the exploded column, and the array's element struct has a field with that name, it rewrites `ci.name` to `ci.ci.name`. The array's type comes from the existing resolver helper `_get_column_type_from_scope`. Unknown fields still raise.

**Tests:** I added `test_qualify_columns_lateral_view_explode_struct` to `tests/test_optimizer.py`. It checks the exact output for the reported query and that `ci.missing` still raises `OptimizeError`. I put it there rather than in the qualify fixtures, because those share a schema without `items`.

**Choices I made:**
- I resolved `ci.name` as a struct field of the exploded column, which is how Spark resolves it. The alternative was to treat it as an error and tell the user to write `ci.ci.name`.
- The rewrite handles one level of field access only. I haven't tested deeper paths such as `ci.name.first`.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nsql = 'SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci'\nschema = {'my_table': {'items': 'ARRAY<STRUCT<name:STRING>>'}}\nprint(optimize(sqlglot.parse_one(sql, read='spark'), schema=schema, dialect='spark').sql('spark'))\n\" 2>&1 | tail -30", "description": "Reproduce the optimizer error"}
[tool_use Bash] {"command": "grep -rn -i \"explode\\|lateral\" sqlglot/optimizer/*.py | head -60", "description": "Search optimizer for explode and lateral handling"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/optimizer.py", line 112, in optimize
    optimized = rule(optimized, **rule_kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify.py", line 97, in qu
…[82 chars elided]…
^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", line 617, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: name
[tool_result] sqlglot/optimizer/merge_subqueries.py:210:        and not any(e.find(exp.AggFunc, exp.Select, exp.Explode) for e in inner_select.expressions)
sqlglot/optimizer/resolver.py:210:                    self.scope.selected_sources.items(), self.scope.lateral_sources.items()
sqlglot/optimizer/resolver.py:238:        if not joins or args.get("laterals") or args.get("pivots"):
sqlglot/optimizer/resolver.py:240:            # (e.g laterals, pivots) exist alongside joins
sqlglot/optimizer/annotate_types.py:2
…[1531 chars elided]…
 are defined
sqlglot/optimizer/scope.py:802:    expressions.extend(scope.expression.args.get("laterals") or [])
sqlglot/optimizer/scope.py:837:            lateral_sources = sources
sqlglot/optimizer/scope.py:841:            lateral_sources = None
sqlglot/optimizer/scope.py:856:                lateral_sources=lateral_sources,
sqlglot/optimizer/scope.py:890:    elif isinstance(scope.expression, exp.Lateral):
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "sed -n 270,320p sqlglot/optimizer/annotate_types.py && echo ---- && sed -n 770,800p sqlglot/optimizer/annotate_types.py && echo ---- && grep -n \"def _qualify_columns\\|def _expand_alias_refs\\|def qualify_columns\\|Lateral\\|table_alias\\|column_alias\" sqlglot/optimizer/qualify_columns.py | head -60", "description": "Read lateral and explode type annotation code"}
[tool_result]         # Replace NULL type with the default type of the targeted dialect, since the former is not an actual type;
        # it is mostly used to aid type coercion, e.g. in query set operations.
        # TODO (mypyc): uses list() + _set_type instead of direct expr.type = ... because
        # mypyc's property setter bypass rejects DType, and _set_type modifies the dict.
        for expr in list(self._null_expressions.values()):
            self._set_type(expr, self.dialect.DEFAULT_NULL_TYPE)

 
…[3112 chars elided]…
pression.unnest()

        if isinstance(query, exp.Query):
            selects = query.selects
----
21:def qualify_columns(
72:        _pop_table_column_aliases(scope.ctes)
73:        _pop_table_column_aliases(scope.derived_tables)
202:def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
211:        table_alias = derived_table.args.get("alias")
212:        if table_alias:
213:            table_alias.set("columns", None)
314:def _expand_alias_refs(
599:def _qualify_columns(
[tool_use Bash] {"command": "cat > /tmp/repro_lv.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nschema = {\"my_table\": {\"items\": \"ARRAY<STRUCT<name:STRING>>\"}}\nfor sql in [\n    \"SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\",\n    \"SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) t AS ci\",\n    \"SELECT t.ci.name FROM my_table LATERAL VIEW EXPLODE(items)
…[445 chars elided]…
-I /tmp/repro_lv.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot; print(repr(sqlglot.parse_one('SELECT ci.name FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci', read='spark').args.get('laterals')))\"; grep -rn \"LATERAL VIEW\" tests/fixtures/optimizer/*.sql | head -20", "description": "Try lateral view variants and check existing fixtures"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_lv.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
tests/fixtures/optimizer/optimizer.sql:3:SELECT a, m FROM z LATERAL VIEW EXPLODE([1, 2]) q AS m;
tests/fixtures/optimizer/optimizer.sql:8:LATERAL VIEW
tests/fixtures/optimizer/qualify_columns.sql:794:SELECT c FROM x LATERAL VIEW EX
…[288 chars elided]…
S c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:802:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:803:SELECT t.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:839:SELECT c FROM (SELECT 1 a) AS x LATERAL VIEW EXPLODE(a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:840:SELECT _0.c AS c FROM (SELECT 1 AS a) AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/repro_lv.py", "description": "Run lateral view repro variants with repo on path"}
[tool_result] ERR OptimizeError Unknown column: name
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
ERR OptimizeError Unknown column: name
SELECT `ci`.`x`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `x`
[tool_use Bash] {"command": "sed -n 599,700p sqlglot/optimizer/qualify_columns.py", "description": "Read _qualify_columns main loop"}
[tool_result] def _qualify_columns(
    scope: Scope,
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
               
…[2968 chars elided]…
ataType, starting_struct.kind).expressions:
        name = field.name

        # Ambiguous or anonymous fields can't be expanded
        if name in taken_names or not isinstance(field.this, exp.Identifier):
            return []

        taken_names.add(name)

        this = field.this.copy()
        root, *parts = [part.copy() for part in itertools.chain(dot_parts, [this])]
        new_column = exp.column(
            t.cast(exp.Identifier, root),
            table=dot_column.args.get("table"),
[tool_use Bash] {"command": "grep -n \"Dot\\|def \\|source_columns\\|get_source_columns\" sqlglot/optimizer/qualify_columns.py | head -90; echo ----; grep -n \"def get_source_columns\" -A25 sqlglot/optimizer/resolver.py", "description": "Map qualify_columns functions and resolver source columns"}
[tool_result] 21:def qualify_columns(
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
169:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
191:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Column]:
202:def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
216:def _expand_using(scope: Scope, resolver: Resolver) -> dict[str, t.Any]:
219:    def _update_source_columns(source_name: str) -> None:
220:        for column_name in
…[4738 chars elided]…
efined.
152-                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source.expression, exp.Unnest):
153-                    unnest = source.expression
154-
155-                    # if type is not annotated yet, try to get it from the schema
156-                    if not unnest.type or unnest.type.is_type(exp.DType.UNKNOWN):
157-                        unnest_expr = seq_get(unnest.expressions, 0)
158-                        if isinstance(unnest_expr, exp.Column) and self.scope.parent:
[tool_use Bash] {"command": "sed -n 549,598p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 158,185p sqlglot/optimizer/resolver.py; echo ----; sed -n 60,100p sqlglot/optimizer/qualify_columns.py", "description": "Read struct dot conversion and resolver lateral handling"}
[tool_result] def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
    """
    Converts `Column` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."field2"), but they need to be
    normalized to `Dot(Dot(...(<table>.<column>, field1), field2, ...))` to be qualified properly.
    """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot
…[4076 chars elided]…
umns_to_dots(scope, resolver)
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
[tool_use Bash] {"command": "grep -n \"_get_unnest_column_type\" -A22 sqlglot/optimizer/resolver.py | sed -n 1,60p; echo ----; grep -n \"def get_table\\b\" -A30 sqlglot/optimizer/resolver.py | head -50", "description": "Read resolver unnest type helper and get_table"}
[tool_result] 159:                            col_type = self._get_unnest_column_type(unnest_expr)
160-                            # extract element type if it's an ARRAY
161-                            if col_type and col_type.is_type(exp.DType.ARRAY):
162-                                element_types = col_type.expressions
163-                                if element_types:
164-                                    unnest.type = element_types[0].copy()
165-                            else:
166-             
…[3249 chars elided]…
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
[tool_use Bash] {"command": "sed -n 363,400p sqlglot/optimizer/resolver.py; echo ----; grep -n \"def get_column_type\" -A12 sqlglot/schema.py | head -40", "description": "Read rest of unnest type helper and schema type lookup"}
[tool_result]             table_name = table_identifier.name

        source = scope.sources.get(table_name)
        return self._get_column_type_from_scope(source, column) if source else None

    def _get_column_type_from_scope(
        self, source: Scope | exp.Table, column: exp.Column
    ) -> exp.DataType | None:
        """
        Get a column's type by tracing through scopes/tables to find the base table.

        Args:
            source: The source to search - can be a Scope (to iterate its sources
…[1266 chars elided]…
olumn_type(
431-        self,
432-        table: exp.Table | str,
433-        column: exp.Column | str,
434-        dialect: DialectType = None,
435-        normalize: bool | None = None,
436-    ) -> exp.DataType:
437-        normalized_table = self._normalize_table(table, dialect=dialect, normalize=normalize)
438-
439-        normalized_column_name = self._normalize_name(
440-            column if isinstance(column, str) else column.this, dialect=dialect, normalize=normalize
441-        )
442-
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/optimizer/qualify_columns.py; grep -n \"alias_column_names\" -A8 sqlglot/expressions/*.py | head -20", "description": "Check imports and alias_column_names definition"}
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
…[732 chars elided]…
r]:
sqlglot/expressions/core.py-679-        table_alias = self.args.get("alias")
sqlglot/expressions/core.py-680-        if not table_alias:
sqlglot/expressions/core.py-681-            return []
sqlglot/expressions/core.py-682-        return [c.name for c in table_alias.args.get("columns") or []]
sqlglot/expressions/core.py-683-
sqlglot/expressions/core.py-684-    @property
sqlglot/expressions/core.py-685-    def name(self) -> str:
sqlglot/expressions/core.py-686-        return self.text("this")
[assistant] Now I'll add a pass that rewrites `alias.field` into `alias.alias.field` when the struct field is only reachable through the exploded column.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    if converted:\n        # We want to re-aggregate the converted columns, otherwise they'd be skipped in\n        # a `for column in scope.columns` iteration, even though they shouldn't be\n        s
…[1787 chars elided]…
ct_type.is_type(exp.DType.STRUCT) or column.name not in {\n            field.name for field in struct_type.expressions\n        }:\n            continue\n\n        converted = True\n        column.replace(\n            exp.Dot.build(\n                [exp.column(column.table, table=column.table), column.this.copy()],\n            )\n        )\n\n    if converted:\n        scope.clear_cache()\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        _convert_columns_to_dots(scope, resolver)\n        _qualify_columns(", "new_string": "        _convert_columns_to_dots(scope, resolver)\n        _convert_lateral_struct_columns(scope, resolver)\n        _qualify_columns("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/repro_lv.py", "description": "Rerun lateral view repro variants"}
[tool_result] SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
SELECT `t`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) t AS `ci`
ERR OptimizeError Unknown column: name
SELECT `ci`.`x`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `x`
[assistant] The reported case now optimizes to `ci.ci.name`. The fourth variant still raises, which is correct since `x` is not a field of `ci`. Next I'll add a fixture next to the existing LATERAL VIEW cases and run the suite.
[tool_use Bash] {"command": "sed -n 790,806p tests/fixtures/optimizer/qualify_columns.sql; grep -n \"dialect\\|spark\" tests/fixtures/optimizer/qualify_columns.sql | head -5; grep -n \"qualify_columns.sql\" -B3 -A10 tests/test_optimizer.py | head -40", "description": "View existing lateral fixtures and how fixtures are loaded"}
[tool_result] --------------------------------------
-- UDTF
--------------------------------------
# execute: false
SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;

# execute: false
SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
SELECT _0.c AS c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;

# execute: false
SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
SELECT t.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) t AS c;

# execute: false
SELECT aa FROM x, UNNEST(a) AS t(aa);
106:# dialect: oracle
111:# dialect: oracle
134:# dialect: bigquery
167:# dialect: starrocks
172:# dialect: bigquery
[tool_use Bash] {"command": "grep -n \"schema\\|# dialect\" tests/fixtures/optimizer/qualify_columns.sql | sed -n 1,12p; grep -n \"def test_qualify_columns\\b\" -A25 tests/test_optimizer.py | head -40; grep -n \"^# dialect: spark\\|^# dialect: hive\" -A3 tests/fixtures/optimizer/*.sql | head", "description": "Find how qualify_columns fixture uses schema and dialect"}
[tool_result] 106:# dialect: oracle
111:# dialect: oracle
134:# dialect: bigquery
167:# dialect: starrocks
172:# dialect: bigquery
204:# dialect: clickhouse
209:# dialect: snowflake
233:# dialect: oracle
258:# dialect: postgres
263:# dialect: clickhouse
268:# dialect: snowflake
277:# dialect: bigquery
341:    def test_qualify_columns(self, logger):
342-        self.assertEqual(
343-            optimizer.qualify.qualify(
344-                parse_one(
345-                    """
346-                    SELECT 
…[1008 chars elided]…
sts/fixtures/optimizer/annotate_types.sql-49-
tests/fixtures/optimizer/annotate_functions.sql:194:# dialect: spark2, spark, databricks
tests/fixtures/optimizer/annotate_functions.sql-195-SUBSTRING(tbl.str_col, 0, 0);
tests/fixtures/optimizer/annotate_functions.sql-196-STRING;
tests/fixtures/optimizer/annotate_functions.sql-197-
tests/fixtures/optimizer/annotate_functions.sql:198:# dialect: spark2, spark, databricks
tests/fixtures/optimizer/annotate_functions.sql-199-SUBSTRING(tbl.bin_col, 0, 0);
[assistant] The qualify fixtures use a shared schema that has no `items` column, so I'll add a focused test in `tests/test_optimizer.py` instead. Let me find a spot near `test_qualify_columns`.
[tool_use Bash] {"command": "sed -n 366,380p tests/test_optimizer.py", "description": "View end of test_qualify_columns method"}
[tool_result]                 },
                dialect="bigquery",
            ).sql(dialect="bigquery"),
            "SELECT `teams`.`name` AS `name`, count(*) AS `_col_1` FROM `raw`.`TeamMemberships` AS `teammemberships` JOIN `raw`.`Teams` AS `teams` ON `teams`.`id` = `teammemberships`.`teamid` GROUP BY `teams`.`name`",
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
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/test_optimizer.py | awk -F: '$1>341' | head -2", "description": "Find method following test_qualify_columns"}
[tool_result] 635:    def test_validate_columns(self):
654:    def test_qualify_columns__with_invisible(self):
[tool_use Bash] {"command": "sed -n 628,634p tests/test_optimizer.py", "description": "View lines before test_validate_columns"}
[tool_result]                 parse_one("SELECT * FROM t"),
                schema={"t": {"end": "text"}},
                quote_identifiers=False,
            ).sql(),
            "SELECT t.end AS end FROM t AS t",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py", "old_string": "            \"SELECT t.end AS end FROM t AS t\",\n        )\n\n    def test_validate_columns(self):", "new_string": "            \"SELECT t.end AS end FROM t AS t\",\n        )\n\n    def test_qualify_columns_later
…[582 chars elided]…
\",\n        )\n        with self.assertRaises(OptimizeError):\n            optimizer.optimize(\n                parse_one(\n                    \"SELECT ci.missing FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci\",\n                    read=\"spark\",\n                ),\n                schema=schema,\n                dialect=\"spark\",\n            )\n\n    def test_validate_columns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-113645-optimizer-spark-hive-optimizing/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"OptimizeError\\|^from\\|^import\" tests/test_optimizer.py | head -20; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral 2>&1 | tail -15", "description": "Check imports and run new optimizer test"}
[tool_result] 1:import unittest
2:from concurrent.futures import ProcessPoolExecutor, as_completed
3:from functools import partial
4:from unittest.mock import patch
6:import duckdb
7:from pandas.testing import assert_frame_equal
9:import sqlglot
10:from sqlglot import exp, optimizer, parse_one
11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
12:from sqlglot.optimizer.annotate_types import annotate_types
13:from sqlglot.optimizer.normalize import normalization_distance
14:fr
…[171 chars elided]…
lf.assertRaises(OptimizeError):
660:            OptimizeError, "Column 'foo' could not be resolved. Line: 1, Col: 10"
668:        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
690:                with self.assertRaises((OptimizeError, SchemaError)):
714:        with self.assertRaises(OptimizeError) as ctx:
728:        with self.assertRaises(OptimizeError) as ctx:
..                                                                       [100%]
2 passed, 76 deselected in 0.38s
[assistant] Both new assertions pass. Now the full project check suite, as specified in the project harness.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
.........................................................................................................................................................................................................................................................................
…[191 chars elided]…
......................................................................... [ 77%]
............................................. [ 81%]
.... [ 81%]
...................................................................... [ 87%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
.........                                                           [100%]
1093 passed, 17857 subtests passed in 63.37s (0:01:03)
[assistant] All 1093 tests pass. I'll run the linter on the changed files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py) 2>&1 | tail -10; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/optimizer/qualify_columns.py
 M tests/test_optimizer.py
[assistant] The reported query now optimizes instead of raising `OptimizeError`. The full suite passes (1093 tests) and ruff is clean. I haven't committed.

```
SELECT `ci`.`ci`.`name` AS `name` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`
```

**Cause:** `ci.name` was read as column `name` of table `ci`. The lateral only exposes `ci`, so qualification failed with "Unknown column: name". Nothing looked through the exploded struct.

**Fix:** In `sqlglot/optimizer/qualify_columns.py`, a new `_convert_lateral_struct_columns` pass runs before column qualification. When a c
…[321 chars elided]…
I added `test_qualify_columns_lateral_view_explode_struct` to `tests/test_optimizer.py`. It checks the exact output for the reported query and that `ci.missing` still raises `OptimizeError`. I put it there rather than in the qualify fixtures, because those share a schema without `items`.

**Choices I made:**
- I resolved `ci.name` as a struct field of the exploded column, which is how Spark resolves it. The alternative was to treat it as an error and tell the user to write `ci.ci.name`.
- The rewrite handles one level of field access only. I haven't tested deeper paths such as `ci.name.first`.
