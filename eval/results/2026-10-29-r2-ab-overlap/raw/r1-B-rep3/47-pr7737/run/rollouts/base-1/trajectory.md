# trajectory base-1

final message:
Fixed: qualifying an unqualified `LATERAL VIEW EXPLODE(...)` no longer recurses, whether or not the table is in the schema. The full suite passes (1121 tests, 18168 subtests), and ruff lint and format are clean on the changed files.

**Cause:** Resolving a lateral's explode argument built a new `Resolver` over the parent scope. That resolver's source lookup included the same lateral, which asked for its columns again, and each `Resolver` has its own cache, so nothing stopped the loop. I reproduced it with Spark, where the recursion appeared for both a missing table and a table without the column. Snowflake `FLATTEN`, BigQuery and DuckDB `UNNEST` fail with an ordinary `OptimizeError` rather than recursing, so only the Spark `LATERAL VIEW EXPLODE` path was affected.

**Fix** (`sqlglot/optimizer/resolver.py`): a set of in-progress lateral ids is shared with the child resolver. A lateral that is already being resolved contributes no struct fields on re-entry, which breaks the cycle. Qualified arguments and non-recursive cases take the same path as before.

**Test** (`tests/test_optimizer.py`, `test_lateral_explode_unqualified_column_terminates`): for schemas that lack the table or the column, qualification raises `OptimizeError` instead of recursing. With `arr` present in `t`, it produces the expected SQL. Chained laterals (`EXPLODE(x)` where `x` comes from an earlier lateral) also still qualify.

**Not verified:**
- I did not build or test the `sqlglot[c]` mypyc build, so the crash on that build is fixed by inference from the pure-Python recursion, not observed directly.
- I did not run mypy.

The changes are uncommitted in the worktree.

## events
[assistant] I'll start by reading the column resolver and reproducing the recursion before changing anything.
[tool_use Bash] {"command": "git status --short | head && grep -n \"unnest\\|Unnest\\|_expand_\\|lateral\\|Lateral\\|def _\" sqlglot/optimizer/qualify_columns.py | head -80", "description": "Check git status and find resolver code"}
[tool_result] ok29 matches in 11 files:

162:0:Scope, pseudocolumns: set[str]) -> None:
184:0:Iterable[exp.Expr]) -> None:
198:0:Scope, resolver: Resolver) -> dict[str, t.Any]:
201:0:str) -> None:
422:0:Scope, dialect: Dialect) -> None:
432:0:Scope, resolver: Resolver) -> None:
530:0:exp.Selectable, node: exp.Literal) -> exp.Alias:
537:0:Scope, resolver: Resolver) -> None:
702:0:exp.Dot) -> list[exp.Alias]:
881:0:exp.Expr, tables, except_columns: dict[int, set[str]]) -> None:
sqlglot/optimizer/qualify_columns
…[991 chars elided]…
ry unnest has no table alias
sqlglot/optimizer/qualify_columns.py:648:def _expand_struct_stars_no_parens(
sqlglot/optimizer/qualify_columns.py:764:def _expand_stars(
sqlglot/optimizer/qualify_columns.py:812:struct_fields = _expand_struct_stars_no_parens(expression)
sqlglot/optimizer/qualify_columns.py:817:struct_fields = _expand_struct_stars_with_parens(expression)
sqlglot/optimizer/qualify_columns.py:893:def _add_rename_columns(
sqlglot/optimizer/qualify_columns.py:907:def _add_replace_columns(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", "offset": 580, "limit": 70}
[tool_result] 580	
581	    if converted:
582	        # We want to re-aggregate the converted columns, otherwise they'd be skipped in
583	        # a `for column in scope.columns` iteration, even though they shouldn't be
584	        scope.clear_cache()
585	
586	
587	def _qualify_columns(
588	    scope: Scope,
589	    resolver: Resolver,
590	    allow_partial_qualification: bool,
591	) -> None:
592	    """Disambiguate columns, ensuring each column specifies a source"""
593	    for column in scope.columns:
594	 
…[2083 chars elided]…
treating them as structs/records
638	                scope.replace(column, exp.TableColumn(this=column.this))
639	
640	    for pivot in scope.pivots:
641	        for column in pivot.find_all(exp.Column):
642	            if not column.table and column.name in resolver.all_columns:
643	                table = resolver.get_table(column.name)
644	                if table:
645	                    column.set("table", table)
646	
647	
648	def _expand_struct_stars_no_parens(
649	    expression: exp.Dot,
[tool_use Bash] {"command": "grep -n \"class Resolver\" -A 120 sqlglot/optimizer/scope.py | head -170", "description": "Read column resolver and Resolver class"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"class Resolver\" sqlglot/ ; grep -n \"def get_table\\|def _get_all_source_columns\\|def get_source_columns\\|def all_columns\\|def _get_unambiguous\\|def _get_source_columns\" sqlglot/optimizer/*.py", "description": "Locate Resolver class and its methods"}
[tool_result] sqlglot/optimizer/resolver.py:17:class Resolver:
6 matches in 1 files:

sqlglot/optimizer/resolver.py:34:def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
sqlglot/optimizer/resolver.py:87:def all_columns(self) -> set[str]:
sqlglot/optimizer/resolver.py:95:def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py:133:def get_source_columns(self, name: str, only_visible: bool = False) -> Sequen...
sqlglot/optimizer/resolver.py:217:def _get_all_source_columns(self) -> dict[str, Sequence[str]]:
sqlglot/optimizer/resolver.py:296:def _get_unambiguous_columns(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py"}
[tool_result] 1	from __future__ import annotations
2	
3	import itertools
4	import typing as t
5	
6	from sqlglot import exp
7	from sqlglot.dialects.dialect import Dialect
8	from sqlglot.errors import OptimizeError
9	from sqlglot.helper import seq_get, SingleValuedMapping
10	from sqlglot.optimizer.scope import Scope
11	
12	if t.TYPE_CHECKING:
13	    from sqlglot.schema import Schema
14	    from collections.abc import Sequence, Mapping
15	
16	
17	class Resolver:
18	    """
19	    Helper for resolving columns.
20
…[18633 chars elided]…
ol_type and not col_type.is_type(exp.DType.UNKNOWN):
405	                return col_type
406	        elif isinstance(source, Scope):
407	            # iterate over all sources in the scope
408	            for source_name, nested_source in source.sources.items():
409	                col_type = self._get_column_type_from_scope(nested_source, column)
410	                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
411	                    return col_type
412	
413	        return None
414	
[assistant] The recursion path looks like `get_source_columns` → `_get_unnest_column_type` → a new `Resolver.get_table` → `get_source_columns` again. I'll reproduce it before going further.
[tool_use Bash] {"command": "cat > /tmp/repro_qual.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f\", {\"other\": {\"x\": \"int\"}}),\n    (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f\", {\"t\": {\"id\": \"int\"}}),\n    (\"snowflake\
…[700 chars elided]…
lect=dialect)\n        print(\"OK \", dialect, out.sql(dialect))\n    except RecursionError:\n        print(\"RECURSION\", dialect, sql)\n    except Exception as e:\n        print(\"ERR\", type(e).__name__, dialect, sql, str(e)[:150])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_qual.py", "description": "Reproduce qualify recursion across dialects"}
[tool_result] ERR OptimizeError snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f Column 'ARR' could not be resolved. Line: 1, Col: 51
ERR OptimizeError snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f Column 'ARR' could not be resolved. Line: 1, Col: 51
OK  snowflake SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
ERR OptimizeError bigquery SELECT x FROM t, UNNEST(arr) AS x Column 'arr' could not be resolved. Line: 1, Col: 27
ERR OptimizeError bigquery SELECT x FROM t, UNNEST(arr) AS x Column 'arr' could not be resolved. Line: 1, Col: 27
ERR OptimizeError bigquery SELECT x FROM t CROSS JOIN UNNEST(arr) AS x Column 'arr' could not be resolved. Line: 1, Col: 37
ERR OptimizeError duckdb SELECT x FROM t, UNNEST(arr) AS u(x) Column 'arr' could not be resolved. Line: 1, Col: 27
RECURSION spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x
[assistant] Spark `LATERAL VIEW EXPLODE` on an unqualified column recurses; the other dialects fail with an ordinary `OptimizeError`, not a recursion. Next I'll check which schema variants trigger it and confirm the cycle in the traceback.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sys, traceback\nsys.path.insert(0, \".\")\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsql = \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x\"\nfor schema in [{\"other\": {\"x\": \"int\"}}, {\"t\": {\"id\": \"int\"}}, {\"t\": {\"arr\": \"array<int>\"}}, {\"t\": {\"id\": \"int\"}, \"other\": {\"x\": \"int\"}}]:\n    try:\n     
…[524 chars elided]…
"{f.filename.split('/')[-1]}:{f.lineno} {f.name}\")\n    print(\"\\n\".join(seen[-25:]))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro2.py 2>&1 | tail -45; <work>/env-sqlglot/bin/python -I -c \"import sqlglot,sys;print(sqlglot.__file__)\"", "description": "Check schema variants and inspect recursion cycle"}
[tool_result ERROR] Exit code 1
RECURSION {'other': {'x': 'int'}}
RECURSION {'t': {'id': 'int'}}
OK SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
RECURSION {'t': {'id': 'int'}, 'other': {'x': 'int'}}
resolver.py:234 _get_table_name_from_sources
resolver.py:220 _get_all_source_columns
resolver.py:182 get_source_columns
resolver.py:380 _get_unnest_column_type
resolver.py:45 get_table
resolver.py:234 _get_table_name_from_sources
resolver.py:220 _get_all_source_columns
resolver.py:182 g
…[258 chars elided]…
get_table
resolver.py:234 _get_table_name_from_sources
resolver.py:220 _get_all_source_columns
resolver.py:182 get_source_columns
resolver.py:380 _get_unnest_column_type
resolver.py:45 get_table
resolver.py:234 _get_table_name_from_sources
resolver.py:220 _get_all_source_columns
resolver.py:182 get_source_columns
resolver.py:380 _get_unnest_column_type
resolver.py:45 get_table
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The cycle is confirmed: `get_source_columns` (lateral explode) → `_get_unnest_column_type` → a fresh `Resolver` on the parent scope → `_get_all_source_columns` → `get_source_columns` on the same lateral again. Each `Resolver` has its own cache, so nothing stops it. Before choosing a fix, I'll check where `Resolver` is constructed and whether the lateral branch has tests.
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | grep -v \"class Resolver\"; grep -rln \"LATERAL VIEW\\|lateral_view\\|LATERAL FLATTEN\" tests/ | head; grep -n \"lateral_sources\" sqlglot/optimizer/scope.py | head -5", "description": "Find Resolver constructions and related tests"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
tests/test_parser.py
tests/test_optimizer.py
tests/test_build.py
tests/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_spark.py
tests/dialects/test_presto.py
tests/dialects/test_dialect.py
tests/dialects/test_starrocks.py
tests/dialects/test_hive.py
9 matches in 4 files:

108:0:dict[str, exp.Table | Scope] | None = None,
157:0:dict[str, exp.Table | Scope] | None = None,
60:0:Sources from laterals
[assistant] I'll use an in-progress guard that is shared with the child resolver. While a lateral's own explode argument is being typed, a re-entrant request for that same lateral returns no struct fields, which cuts the cycle. It doesn't change the lookup otherwise, so qualified and already-resolved cases stay the same.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[894 chars elided]…
l = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # ids of lateral sources whose explode argument is currently being resolved, shared with\n        # child resolvers so that a lateral referencing itself through its parent scope terminates\n        self._pending_laterals: set[int] = set() if pending_laterals is None else pending_laterals"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        columns.ext
…[254 chars elided]…
s\n                    ):\n                        self._pending_laterals.add(id(source))\n                        try:\n                            col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        finally:\n                            self._pending_laterals.discard(id(source))\n                        columns.extend(self._struct_field_names(col_type))"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema)", "new_string": "            parent_resolver = Resolver(\n                scope, self.schema, self._infer_schema, self._pending_laterals\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_qual.py; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nsql='SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x'\nfor s in [{'other':{'x':'int'}},{'t':{'id':'int'}},
…[326 chars elided]…
={'t':{'arr':'array<struct<a:int>>'}},dialect='spark').sql('spark'))\nsql3='SELECT y FROM t LATERAL VIEW EXPLODE(arr) v1 AS x LATERAL VIEW EXPLODE(x) v2 AS y'\ntry: print(qualify(sqlglot.parse_one(sql3,read='spark'),schema={'t':{'arr':'array<int>'}},dialect='spark').sql('spark'))\nexcept Exception as e: print(type(e).__name__, str(e)[:120])\n\"", "description": "Apply guard and rerun repro cases"}
[tool_result] ERR OptimizeError snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f Column 'ARR' could not be resolved. Line: 1, Col: 51
ERR OptimizeError snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f Column 'ARR' could not be resolved. Line: 1, Col: 51
OK  snowflake SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
ERR OptimizeError bigquery SELECT x FROM t, UNNEST(arr) AS x Column 'arr' co
…[422 chars elided]…
x FROM t LATERAL VIEW EXPLODE(arr) v AS x Column 'arr' could not be resolved. Line: 1, Col: 40
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
SELECT `v`.`x`.`a` AS `a` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
SELECT `v2`.`y` AS `y` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v1 AS `x` LATERAL VIEW EXPLODE(`v1`.`x`) v2 AS `y`
[assistant] The recursion is gone and the chained-lateral case still resolves. The remaining errors are `OptimizeError: Column 'arr' could not be resolved`, which is the expected result when `arr` exists in no schema table. I'll confirm that matches how an ordinary unknown unqualified column already behaves, then look for the right test home.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ntry: print(qualify(sqlglot.parse_one('SELECT arr FROM t',read='spark'),schema={'other':{'x':'int'}},dialect='spark').sql('spark'))\nexcept Exception as e: print(type(e).__name__, str(e)[:100])\n\"; grep -n \"def test_qualify_columns__\\|def test_lateral\\|LATERAL VIEW\" tests/test_optimizer.py | head -30; grep -n \"LATERAL VIEW\" tests/fixtures/optimizer/qualify_columns.sql | head", "description": "Compare unknown-column behavior and find test locations"}
[tool_result] OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 10
8 matches in 4 files:

1691:0:
753:0:
763:0:
tests/test_optimizer.py:718:"SELECT ci.name, ci.age FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci",
tests/test_optimizer.py:729:"SELECT `ci`.`name` AS `name`, `ci`.`age` AS `age` FROM `my_table` AS `my_tab...
tests/test_optimizer.py:738:"SELECT (SELECT SUM(ci.amount) FROM my_table LATERAL VIEW EXPLODE(items) ci A...
tests/test_optimizer.py:749:"SELECT (SELECT SUM(`ci`.`amount`) AS
…[539 chars elided]…
S c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:814:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:815:SELECT t.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:851:SELECT c FROM (SELECT 1 a) AS x LATERAL VIEW EXPLODE(a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:852:SELECT _0.c AS c FROM (SELECT 1 AS a) AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
[assistant] An unknown unqualified column already raises `OptimizeError` on the same path, so the new behavior is consistent. Next I'll look at the existing lateral-view test near line 1691 to match its style.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "offset": 1680, "limit": 30}
[tool_result] 1680	            ),
1681	            (
1682	                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
1683	                exp.DataType.Type.INT,
1684	            ),
1685	        ]:
1686	            with self.subTest(sql):
1687	                expression = annotate_types(parse_one(sql), schema=schema)
1688	                self.assertEqual(expected_type, expression.expressions[0].type.this)
1689	                self.assertEqual(sql, expression.sql())
1690	
1691	    def test_
…[291 chars elided]…
t_derived_tables_column_annotation(self):
1698	        schema = {"x": {"cola": "INT"}, "y": {"cola": "FLOAT"}}
1699	        sql = """
1700	            SELECT a.cola AS cola
1701	            FROM (
1702	                SELECT x.cola + y.cola AS cola
1703	                FROM (
1704	                    SELECT x.cola AS cola
1705	                    FROM x AS x
1706	                ) AS x
1707	                JOIN (
1708	                    SELECT y.cola AS cola
1709	                    FROM y AS y
[assistant] I'll add a regression test next to `test_lateral_annotation`. First I need to confirm what the file already imports.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|OptimizeError\\|qualify\" tests/test_optimizer.py | head -40", "description": "Check test file imports"}
[tool_result] 149 matches in 21 files:

1321:0:table.replace(exp.to_table("bar")),
183:0:
2314:0:
2421:0:
254:0:
259:0:tables.add(t.name),
2721:0:{"col": "TEXT"}})
315:0:
32:0:
357:0:
36:0:
697:0:1, Col: 10"
705:0:
753:0:
763:0:
764:0:
766:0:
790:0:
804:0:
814:0:
tests/test_optimizer.py:1:import unittest
tests/test_optimizer.py:2:from concurrent.futures import ProcessPoolExecutor, as_completed
tests/test_optimizer.py:3:from functools import partial
tests/test_optimizer.py:4:from unittest.mock import patch
tes
…[585 chars elided]…
 import normalization_distance
tests/test_optimizer.py:15:from sqlglot.optimizer.qualify import qualify
tests/test_optimizer.py:16:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
tests/test_optimizer.py:17:from sqlglot.schema import MappingSchema
tests/test_optimizer.py:18:from tests.helpers import (
tests/test_optimizer.py:33:return canonicalize_internal_names(qualify(expression, **qualify_kwargs))
tests/test_optimizer.py:37:expression = optimizer.qualify.qualify(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\
…[401 chars elided]…
ialect=\"spark\")\n\n        expression = qualify(\n            parse_one(sql, read=\"spark\"), schema={\"t\": {\"arr\": \"array<int>\"}}, dialect=\"spark\"\n        )\n        self.assertEqual(\n            expression.sql(\"spark\"),\n            \"SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`\",\n        )\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-200916-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "git stash list >/dev/null; <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"lateral\" 2>&1 | tail -5", "description": "Run new and existing lateral optimizer tests"}
[tool_result] ..                                                                     [100%]
2 passed, 78 deselected, 2 subtests passed in 0.21s
[assistant] The two lateral tests pass. Now the project's full check command from CLAUDE.md, run against the whole suite:
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[252 chars elided]…
........................... [ 64%]
........................................................................................................................................................................................................................................................................................................................................... [ 94%]
...................................................................        [100%]
1121 passed, 18168 subtests passed in 46.03s
[assistant] The full suite passes: 1121 tests, 18168 subtests. I'll also run the repo's style checks on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -I -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && <work>/env-sqlglot/bin/python -I -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -5; git status --short; git diff --stat", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.pysqlglot/optimizer/resolver.py | 27 +++++++++++++++++++++++----
 tests/test_optimizer.py       | 15 +++++++++++++++
 2 files changed, 38 insertions(+), 4 deletions(-)
[assistant] Fixed: qualifying an unqualified `LATERAL VIEW EXPLODE(...)` no longer recurses, whether or not the table is in the schema. The full suite passes (1121 tests, 18168 subtests), and ruff lint and format are clean on the changed files.

**Cause:** Resolving a lateral's explode argument built a new `Resolver` over the parent scope. That resolver's source lookup included the same lateral, which asked for its columns again, and each `Resolver` has its own cache, so nothing stopped the loop. I reproduced it with Spark, where the recursion appeared for both a missing table and a table without the colu
…[462 chars elided]…
fore.

**Test** (`tests/test_optimizer.py`, `test_lateral_explode_unqualified_column_terminates`): for schemas that lack the table or the column, qualification raises `OptimizeError` instead of recursing. With `arr` present in `t`, it produces the expected SQL. Chained laterals (`EXPLODE(x)` where `x` comes from an earlier lateral) also still qualify.

**Not verified:**
- I did not build or test the `sqlglot[c]` mypyc build, so the crash on that build is fixed by inference from the pure-Python recursion, not observed directly.
- I did not run mypy.

The changes are uncommitted in the worktree.
