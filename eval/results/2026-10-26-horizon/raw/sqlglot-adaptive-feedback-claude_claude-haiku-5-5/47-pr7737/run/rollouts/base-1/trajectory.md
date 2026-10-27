# trajectory base-1

final message:
The optimizer no longer recurses when it types an unqualified `LATERAL VIEW EXPLODE` or `UNNEST` column. Qualifying those queries now terminates whether or not the owning table is in the schema. The full suite passes: `SUMMARY: 1121 passed, 18170 subtests passed`, `EXIT: 0`, run after the last edit.

**Root cause:** in `sqlglot/optimizer/resolver.py`, resolving a lateral or unnest source's struct fields calls `_get_unnest_column_type`. That builds a fresh `Resolver` and calls `get_table`, which re-reads the same source's columns, which calls `_get_unnest_column_type` again. Because each level makes a new `Resolver`, the per-instance cache never stops it.

**Fix:**
- `Resolver` takes an `unnest_in_progress` set of source ids (default empty).
- `_get_unnest_column_type` now takes the owning unnest/lateral expression and passes `{id(source)}` into the nested resolver.
- Both call sites skip struct-field inference when the source is already in progress. The source's own named columns are still returned, so the lookup terminates with the same result a non-cyclic lookup gives.

**Reproduction:** the trigger is a Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr` (also a chained second lateral). BigQuery `UNNEST(arr)` with an unqualified column does not recurse; it raises `OptimizeError`. I could not reproduce recursion with Snowflake `LATERAL FLATTEN(input => col)`. That query raises `OptimizeError` both before and after the change, so I did not claim it as covered.

**Behaviour for a missing table:** an unqualified `arr` whose table is not in the schema now raises `OptimizeError: Column 'arr' could not be resolved`. This matches what the optimizer already does for an unqualified column with no owning table (for example `SELECT arr FROM t1`), so it is a clean error, not a crash. When `t1` is in the schema, the query qualifies to ``SELECT `v`.`x` AS `x` FROM `t1` AS `t1` LATERAL VIEW EXPLODE(`t1`.`arr`) v AS `x` ``.

**Tests:** I added `test_qualify_columns__unnest_unqualified_column` in `tests/test_optimizer.py`. It checks the in-schema output above and that the missing-table cases (Spark, Hive, chained laterals, BigQuery UNNEST) raise `OptimizeError` rather than recursing. It fails on the original resolver (3 subtests) and passes with the fix. Ruff format and check are clean.

**Not verified:** I did not build or run the mypyc-compiled `sqlglot[c]` variant. The change removes the unbounded recursion, so it should cover that build too, but that is untested here.

## events
[assistant] I'll start by reading the qualify column resolver and reproducing the recursion before changing anything.
[tool_use Bash] {"command": "ls .lithify/harness/ && cat .lithify/harness/memory.md 2>/dev/null; git status --short | head; grep -n \"def _expand_\\|def _get_unambiguous\\|def _get_source\\|Unnest\\|Lateral\\|explode\\|def _qualify_columns\\|def _expand_alias\\|def _expand_stars\\|def _qualify_outputs\\|def qualify_columns\" sqlglot/optimizer/qualify_columns.py | head -80", "description": "Inspect harness files and qualify_columns structure"}
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/d
…[306 chars elided]…
e, resolver: Resolver) -> dict[str, t.Any]:
302:def _expand_alias_refs(
422:def _expand_group_by(scope: Scope, dialect: Dialect) -> None:
432:def _expand_order_by_and_distinct_on(scope: Scope, resolver: Resolver) -> None:
477:def _expand_positional_references(
518:                    or select_expr.find(exp.Explode, exp.Unnest)
587:def _qualify_columns(
648:def _expand_struct_stars_no_parens(
702:def _expand_struct_stars_with_parens(expression: exp.Dot) -> list[exp.Alias]:
764:def _expand_stars(
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python && cat > /tmp/probe_recur.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import qualify\nfrom sqlglot.optimizer.qualify import qualify as q\nschema = {\"t2\": {\"a\": \"int\"}}\ncases = {\n \"flatten_m
…[569 chars elided]…
sionError\")\n        except Exception as e:\n            print(name, dialect, type(e).__name__, str(e)[:200])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_recur.py 2>&1 | tail -20", "description": "Probe qualify on unqualified flatten/unnest with missing table"}
[tool_result] <work>/env-sqlglot/bin/python
flatten_missing snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 52
flatten_missing bigquery OptimizeError Column 'col' could not be resolved. Line: 1, Col: 52
unnest_missing snowflake OptimizeError Column 'X' could not be resolved. Line: 1, Col: 8
unnest_missing bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 38
flatten_bare_col_t1_in_schema snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 52
flatten_bare_col_t1_in_schema bigquery OptimizeError Column 'col' could not be resolved. Line: 1, Col: 52
[assistant] My probes raised `OptimizeError`, not recursion, so the trigger shape is different. I'll look at the resolver code paths directly.
[tool_use Bash] {"command": "grep -n \"class Resolver\" -A140 sqlglot/optimizer/resolver.py | head -220; grep -n \"Unnest\\|Lateral\\|Flatten\\|explode\" sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py | head -40", "description": "Read Resolver class and unnest/lateral references"}
[tool_result] 17:class Resolver:
18-    """
19-    Helper for resolving columns.
20-
21-    This is a class so we can lazily load some things and easily share them across functions.
22-    """
23-
24-    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
25-        self.scope: Scope = scope
26-        self.schema: Schema = schema
27-        self.dialect: Dialect = schema.dialect or Dialect()
28-        self._source_columns: dict[str, Sequence[str]] | None = None
29-        se
…[7407 chars elided]…
/optimizer/scope.py:919:    if isinstance(scope.expression, exp.Unnest):
sqlglot/optimizer/scope.py:921:    elif isinstance(scope.expression, exp.Lateral):
sqlglot/optimizer/qualify_columns.py:518:                    or select_expr.find(exp.Explode, exp.Unnest)
sqlglot/optimizer/qualify_columns.py:651:    """[BigQuery] Expand/Flatten foo.bar.* where bar is a struct column"""
sqlglot/optimizer/qualify_columns.py:703:    """[RisingWave] Expand/Flatten (<exp>.bar).*, where bar is a struct column"""
[tool_use Bash] {"command": "sed -i '' 's/^/ /;s/^ //' /dev/null; sed -n 156,200p sqlglot/optimizer/resolver.py; echo ----; sed -n 360,420p sqlglot/optimizer/resolver.py", "description": "Read unnest column type resolution code"}
[tool_result] sed: /dev/null: in-place editing only works for regular files
                source_expr := source.expression, (exp.Values, exp.Unnest, exp.Lateral)
            ):
                columns = source_expr.named_selects

                # in bigquery, unnest structs are automatically scoped as tables, so you can
                # directly select a struct field in a query.
                # this handles the case where the unnest is statically defined.
                if self.dialect.UNNEST_COLUMN_ON
…[4013 chars elided]…
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
[assistant] The recursion path is visible: `_get_unnest_column_type` calls `Resolver.get_table`, which calls `get_source_columns` on the same Unnest/Lateral source, which calls `_get_unnest_column_type` again. I'll find a query shape that actually hits it.
[tool_use Bash] {"command": "cat > /tmp/probe_recur2.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"other\": {\"a\": \"int\"}}\ncases = [\n (\"bigquery\", \"SELECT x FROM UNNEST(arr) AS x\"),\n (\"bigquery\", \"SELECT x FROM t1 CROSS JOIN UNNEST(arr) AS x\"),\n (\"bigquery\", \"SELECT x FROM t1, UNNEST(arr) AS x\"),\n (\"bigquery\", \"SELECT x FRO
…[805 chars elided]…
    print(\"REC\", dialect, sql)\n    except Exception as e:\n        print(\"ERR\", dialect, sql, type(e).__name__, str(e)[:120])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_recur2.py 2>&1 | tail -30", "description": "Probe unnest/lateral shapes for recursion"}
[tool_result] ERR bigquery SELECT x FROM UNNEST(arr) AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 24
ERR bigquery SELECT x FROM t1 CROSS JOIN UNNEST(arr) AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 38
ERR bigquery SELECT x FROM t1, UNNEST(arr) AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 28
OK  bigquery SELECT x FROM t1 AS t, UNNEST(t.arr) AS x -> SELECT `x` AS `x` FROM `t1` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
ERR bigquery SELECT 
…[212 chars elided]…
l: 31
ERR snowflake SELECT x.value FROM t1, LATERAL FLATTEN(input => col) AS x OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 52
REC hive SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x
REC spark SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x
REC spark SELECT x FROM other LATERAL VIEW EXPLODE(arr) v AS x
REC spark SELECT x FROM other LATERAL VIEW EXPLODE(arr) v AS x
ERR duckdb SELECT x FROM t1, UNNEST(arr) AS x OptimizeError Column 'x' could not be resolved. Line: 1, Col: 8
[assistant] Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified column reproduces the `RecursionError`. Next I'll pull the traceback to confirm the cycle.
[tool_use Bash] {"command": "cat > /tmp/tb.py <<'EOF'\nimport traceback, sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ntry:\n    qualify(parse_one(\"SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x\", read=\"spark\"), schema={\"other\": {\"a\": \"int\"}}, dialect=\"spark\")\nexcept RecursionError:\n    st = traceback.extract_tb(sys.exc_info()[2])\n    for f in st[:40]:\n        print(f.filename.split(\"/sqlglot/\")[-1], f.lineno, f.name)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/tb.py 2>&1 | head -60", "description": "Print first frames of the recursion traceback"}
[tool_result] /tmp/tb.py 5 <module>
optimizer/qualify.py 98 qualify
optimizer/qualify_columns.py 85 qualify_columns
optimizer/qualify_columns.py 621 _qualify_columns
optimizer/resolver.py 45 get_table
optimizer/resolver.py 234 _get_table_name_from_sources
optimizer/resolver.py 220 _get_all_source_columns
optimizer/resolver.py 182 get_source_columns
optimizer/resolver.py 380 _get_unnest_column_type
optimizer/resolver.py 45 get_table
optimizer/resolver.py 234 _get_table_name_from_sources
optimizer/resolver.py 2
…[831 chars elided]…
mizer/resolver.py 45 get_table
optimizer/resolver.py 234 _get_table_name_from_sources
optimizer/resolver.py 220 _get_all_source_columns
optimizer/resolver.py 182 get_source_columns
optimizer/resolver.py 380 _get_unnest_column_type
optimizer/resolver.py 45 get_table
optimizer/resolver.py 234 _get_table_name_from_sources
optimizer/resolver.py 220 _get_all_source_columns
optimizer/resolver.py 182 get_source_columns
optimizer/resolver.py 380 _get_unnest_column_type
optimizer/resolver.py 45 get_table
[assistant] The cycle is clear: `get_source_columns(lateral)` → `_get_unnest_column_type` → a fresh `Resolver.get_table` → `get_source_columns(same lateral)`. Each level builds a new `Resolver`, so a per-instance cache guard won't stop it. Before choosing a fix, I'll check the harness skill for optimizer passes and every `Resolver(` construction site.
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | head; sed -n 1,80p .lithify/harness/skills/sqlglot-optimizer-rewrites/SKILL.md", "description": "Find Resolver construction sites and read optimizer skill"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
---
name: sqlglot-optimizer-rewrites
description: Load when a task changes a sqlglot optimizer pass (sqlglot/optimizer/*.py — qualify_tables, qualify_columns, qualify, annotate_types, simp
…[5316 chars elided]…
d per pass — direct `assertEqual`
  calls, then `self.check_file("<pass>", ...)` over `tests/fixtures/optimizer/<pass>.sql`
  (input/expected pairs with `# title:` and optional `# dialect:` /
  `# canonicalize_table_aliases:` headers). Fixtures compare SQL text only, so a node-level fix
  needs a direct test that holds the original node and asserts type, children and
  independence from it afterwards.
- `tests/test_optimizer.py` passes, then one full-suite `run_suite.py` run ends with `EXIT: 0`.
[assistant] The fix needs to break the cycle across `Resolver` instances, so I'll thread an in-progress set of unnest/lateral source ids from parent to child resolver. Checking the remaining callers first:
[tool_use Bash] {"command": "grep -rn \"_get_unnest_column_type\\|_get_column_type_from_scope\" sqlglot/ tests/ | head; sed -n 1,16p sqlglot/optimizer/resolver.py", "description": "Find callers of unnest column type helpers"}
[tool_result] sqlglot/optimizer/resolver.py:167:                            col_type = self._get_unnest_column_type(unnest_expr, self.scope.parent)
sqlglot/optimizer/resolver.py:182:                        col_type = self._get_unnest_column_type(explode_col, source.parent)
sqlglot/optimizer/resolver.py:363:    def _get_unnest_column_type(self, column: exp.Column, scope: Scope) -> exp.DataType | None:
sqlglot/optimizer/resolver.py:386:        return self._get_column_type_from_scope(source, column) if source el
…[85 chars elided]…
t/optimizer/resolver.py:409:                col_type = self._get_column_type_from_scope(nested_source, column)
from __future__ import annotations

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
[assistant] The change is contained to `sqlglot/optimizer/resolver.py`. I'll add an in-progress set of unnest/lateral source ids, consult it before inferring a source's struct fields, and pass it into the nested resolver.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[777 chars elided]…
_columns: Mapping[str, str] | None = None\n        self._all_columns: set[str] | None = None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # ids of UNNEST / LATERAL sources whose column types are already being inferred up the stack\n        self._unnest_in_progress: frozenset[int] = unnest_in_progress"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):\n                    if not source_expr.type or source_expr.type.is_type(exp.DType.UNKNOWN):\n                     
…[488 chars elided]…
r) not in self._unnest_in_progress\n                    ):\n                        unnest_expr = seq_get(source_expr.expressions, 0)\n                        if isinstance(unnest_expr, exp.Column) and self.scope.parent:\n                            col_type = self._get_unnest_column_type(\n                                unnest_expr, self.scope.parent, source_expr\n                            )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explode_col, source.parent)", "new_string": "                    if (\n                        isinstance(explode_col, exp.Column)\n                        and source.parent\n                        and id(source_expr) not in self._unnest_in_progress\n                    ):\n                        col_type = self._get_unnest_column_type(\n                            explode_col, source.parent, source_expr\n                        )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def _get_unnest_column_type(self, column: exp.Column, scope: Scope) -> exp.DataType | None:\n        \"\"\"\n        Get the type of a column being unnested/exploded, tracing through CTEs/subqueries to f
…[1380 chars elided]…
 disambiguate using the resolver\n        if column.table:\n            table_name = column.table\n        else:\n            # use the parent scope's resolver to disambiguate the column\n            parent_resolver = Resolver(\n                scope,\n                self.schema,\n                self._infer_schema,\n                self._unnest_in_progress | {id(unnest_source)},\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Now I'll re-run the probes, covering the table-in-schema and table-missing variants plus a two-lateral chain.
[tool_use Bash] {"command": "cat > /tmp/probe_after.py <<'EOF'\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n (\"spark\", \"SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x\", {\"other\": {\"a\": \"int\"}}),\n (\"spark\", \"SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x\", {\"t1\": {\"arr\": \"array<int>\"}, \"other\": {\"a\": \"int\"}}),\n (\"spark\", \"SELECT x FR
…[1036 chars elided]…
    print(\"REC\", dialect, sql)\n    except Exception as e:\n        print(\"ERR\", dialect, sql, type(e).__name__, str(e)[:100])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_after.py 2>&1 | tail -20", "description": "Re-run qualify probes after resolver guard"}
[tool_result] ERR spark SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 41
OK  spark | SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x -> SELECT `v`.`x` AS `x` FROM `t1` AS `t1` LATERAL VIEW EXPLODE(`t1`.`arr`) v AS `x`
ERR spark SELECT x FROM other LATERAL VIEW EXPLODE(arr) v AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 44
ERR spark SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x LATERAL VIEW EXPLODE(x) w AS y Optim
…[330 chars elided]…
 45
ERR bigquery SELECT x FROM t1, UNNEST(arr) AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 28
OK  bigquery | SELECT x FROM t1 AS t, UNNEST(t.arr) AS x -> SELECT `x` AS `x` FROM `t1` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
ERR bigquery SELECT x FROM UNNEST(arr) AS x OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 24
ERR snowflake SELECT x.value FROM t1, LATERAL FLATTEN(input => col) AS x OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 52
[assistant] Every probe now terminates. Some still raise `OptimizeError` for an unresolvable unqualified `arr`. I need to confirm that matches how the optimizer already treats an unqualified column with no owning table, rather than being a new failure.
[tool_use Bash] {"command": "cat > /tmp/probe_base.py <<'EOF'\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfor dialect, sql in [(\"spark\", \"SELECT arr FROM t1\"), (\"spark\", \"SELECT x FROM t1 JOIN other ON TRUE, LATERAL VIEW\")]:\n    try:\n        print(qualify(parse_one(sql, read=dialect), schema={\"other\": {\"a\": \"int\"}}, dialect=dialect).sql(dialect))\n    except Exce
…[175 chars elided]…
1-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python /tmp/probe_base.py 2>&1 | tail -5; git stash list | head -2; grep -n \"LATERAL VIEW\\|lateral\" tests/fixtures/optimizer/qualify_columns.sql | head; grep -n \"def test_qualify_columns\\|def test_lateral\\|UNNEST\\|unnest\" tests/test_optimizer.py | head -20", "description": "Compare baseline unresolved-column behavior and find test locations"}
[tool_result] OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 10
ParseError Required keyword: 'this' missing for <class 'sqlglot.expressions.query.Lateral'>. Line 1, Col: 49.
 
806:SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
807:SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
810:SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
811:SELECT _0.c AS c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
814:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
815:SELECT t.c AS c FROM x
…[1599 chars elided]…
:    def test_lateral_annotation(self):
1983:            parse_one("SELECT unnest(t.x) FROM t AS t", dialect="postgres"),
2006:    def test_unnest_annotation(self):
2011:                SELECT a, a.b, a.b.c FROM x, UNNEST(x.a) AS a
2026:                        "SELECT x FROM UNNEST(GENERATE_DATE_ARRAY('2021-01-01', current_date(), interval 1 day)) AS x"
2039:                        "SELECT x FROM UNNEST(GENERATE_TIMESTAMP_ARRAY('2016-10-05 00:00:00', '2016-10-06 02:00:00', interval 1 day)) AS x"
[assistant] Baseline behaviour matches: an unqualified column with no owning table already raises a clean `OptimizeError`, so that outcome is consistent, not a regression. Next I'll add regression tests next to the existing qualify column tests.
[tool_use Bash] {"command": "sed -n 750,780p tests/test_optimizer.py; sed -n 1,30p tests/test_optimizer.py | grep -n import", "description": "Read existing qualify column tests for placement"}
[tool_result]         )
        self.assertEqual(expression.selects[0].type, exp.DataType.build("DOUBLE", dialect="spark"))

    def test_qualify_columns__with_invisible(self):
        schema = MappingSchema(self.schema, {"x": {"a"}, "y": {"b"}, "z": {"b"}})
        self.check_file("qualify_columns__with_invisible", qualify_columns, schema=schema)

    def test_pushdown_cte_alias_columns(self):
        self.check_file(
            "pushdown_cte_alias_columns",
            pushdown_ctes,
        )

    def tes
…[1068 chars elided]…
sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
12:from sqlglot.optimizer.annotate_types import annotate_types
13:from sqlglot.optimizer.canonicalize_internal_names import canonicalize_internal_names
14:from sqlglot.optimizer.normalize import normalization_distance
15:from sqlglot.optimizer.qualify import qualify
16:from sqlglot.optimizer.scope import build_scope, traverse_scope, walk_in_scope
17:from sqlglot.schema import MappingSchema
18:from tests.helpers import (
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "    def test_qualify_columns__with_invisible(self):\n        schema = MappingSchema(self.schema, {\"x\": {\"a\"}, \"y\": {\"b\"}, \"z\": {\"b\"}})\n        self.check_file(\"qualify_columns__with_invisible\", qual
…[1182 chars elided]…
 AS y\"),\n            (\"bigquery\", \"SELECT x FROM t1, UNNEST(arr) AS x\"),\n        ):\n            with self.subTest(sql):\n                with self.assertRaises(OptimizeError):\n                    qualify(\n                        parse_one(sql, read=dialect),\n                        schema={\"other\": {\"a\": \"int\"}},\n                        dialect=dialect,\n                    )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-105620-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Running the optimizer test module and checking the new test against the unmodified resolver:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"unnest_unqualified or qualify\" 2>&1 | tail -5; cp sqlglot/optimizer/resolver.py /tmp/fixed_resolver.py && git show HEAD:sqlglot/optimizer/resolver.py > sqlglot/optimizer/resolver.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified 2>&1 | tail -3; cp /tmp/fixed_resolver.py sqlglot/optimizer/resolver.py && git diff --stat", "description": "Run new test on fixed and original resolver"}
[tool_result] .......                          [100%]
7 passed, 73 deselected, 472 subtests passed in 2.47s
SUBFAILED[SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x] tests/test_optimizer.py::TestOptimizer::test_qualify_columns__unnest_unqualified_column
SUBFAILED[SELECT x FROM t1 LATERAL VIEW EXPLODE(arr) v AS x LATERAL VIEW EXPLODE(x) w AS y] tests/test_optimizer.py::TestOptimizer::test_qualify_columns__unnest_unqualified_column
3 failed, 1 passed, 79 deselected, 1 subtests passed in 0.30s
 sqlglot/optimizer/resolver.py | 41 ++++++++++++++++++++++++++++++++++-------
 tests/test_optimizer.py       | 27 +++++++++++++++++++++++++++
 2 files changed, 61 insertions(+), 7 deletions(-)
[assistant] The new test passes with the fix and fails on the original resolver, and the fixed file is restored. Next, lint and format on the two changed files, then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff format sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PY -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -8; git diff --stat", "description": "Run ruff format and check on changed files"}
[tool_result] ruff 0.15.6
1 file reformatted, 1 file left unchanged
All checks passed!
 sqlglot/optimizer/resolver.py | 41 ++++++++++++++++++++++++++++++++++-------
 tests/test_optimizer.py       | 32 ++++++++++++++++++++++++++++++++
 2 files changed, 66 insertions(+), 7 deletions(-)
[This command modified 1 file you've previously read: tests/test_optimizer.py. Call Read before editing.]
[assistant] Ruff reformatted the test file's long lines. Now the full suite, in the foreground as the harness requires:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:26:45 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-9e8afd647d.log
ELAPSED: 50s
SUMMARY: 1121 passed, 18170 subtests passed in 49.87s
EXIT: 0
[assistant] The full suite passed after the last edit. I'll check the final resolver diff once more before reporting.
[tool_use Bash] {"command": "git diff sqlglot/optimizer/resolver.py", "description": "Show final resolver diff"}
[tool_result] diff --git a/sqlglot/optimizer/resolver.py b/sqlglot/optimizer/resolver.py
index e840af2a1..9231fcb8f 100644
--- a/sqlglot/optimizer/resolver.py
+++ b/sqlglot/optimizer/resolver.py
@@ -21,7 +21,13 @@ class Resolver:
     This is a class so we can lazily load some things and easily share them across functions.
     """
 
-    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
+    def __init__(
+        self,
+        scope: Scope,
+        schema: Schema,
+     
…[3820 chars elided]…
:
             # use the parent scope's resolver to disambiguate the column
-            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
+            parent_resolver = Resolver(
+                scope,
+                self.schema,
+                self._infer_schema,
+                self._unnest_in_progress | {id(unnest_source)},
+            )
             table_identifier = parent_resolver.get_table(column)
             if not table_identifier:
                 return None
[assistant] The optimizer no longer recurses when it types an unqualified `LATERAL VIEW EXPLODE` or `UNNEST` column. Qualifying those queries now terminates whether or not the owning table is in the schema. The full suite passes: `SUMMARY: 1121 passed, 18170 subtests passed`, `EXIT: 0`, run after the last edit.

**Root cause:** in `sqlglot/optimizer/resolver.py`, resolving a lateral or unnest source's struct fields calls `_get_unnest_column_type`. That builds a fresh `Resolver` and calls `get_table`, which re-reads the same source's columns, which calls `_get_unnest_column_type` again. Because each level 
…[1314 chars elided]…
ERAL VIEW EXPLODE(`t1`.`arr`) v AS `x` ``.

**Tests:** I added `test_qualify_columns__unnest_unqualified_column` in `tests/test_optimizer.py`. It checks the in-schema output above and that the missing-table cases (Spark, Hive, chained laterals, BigQuery UNNEST) raise `OptimizeError` rather than recursing. It fails on the original resolver (3 subtests) and passes with the fix. Ruff format and check are clean.

**Not verified:** I did not build or run the mypyc-compiled `sqlglot[c]` variant. The change removes the unbounded recursion, so it should cover that build too, but that is untested here.
