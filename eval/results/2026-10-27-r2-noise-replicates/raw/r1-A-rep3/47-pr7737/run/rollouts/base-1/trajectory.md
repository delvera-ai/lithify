# trajectory base-1

final message:
Qualifying a `LATERAL VIEW EXPLODE` over an unqualified column no longer recurses when the base table is missing from the schema. The full suite passes (1121 tests, 18166 subtests), and ruff and mypy are clean.

**Cause:** In `sqlglot/optimizer/resolver.py`, resolving a lateral explode's argument runs `_get_unnest_column_type`. That builds a new `Resolver` on the parent scope, which collects the columns of every source, including the lateral itself. Collecting the lateral's columns calls the same explode resolution again, so it loops until the stack overflows.

**Fix:** The resolver now tracks which lateral sources are being resolved. A lateral that is already in progress contributes no columns on re-entry, so the lookup terminates. The set is shared with the parent resolver. The non-cyclic path is unchanged.

**Behaviour now:**
- Spark/Hive `FROM missing LATERAL VIEW EXPLODE(arr) ...` with `arr` unqualified raises `OptimizeError: Column 'arr' could not be resolved`, a clean error rather than a crash.
- The same query with the column's table in the schema still qualifies correctly.

**Test:** I added `test_lateral_explode_unqualified_column_missing_table` to `tests/test_optimizer.py`. It fails on the original code with the recursion error and passes with the fix. No existing tests were changed.

**Scope notes:**
- I could only reproduce the recursion for `LATERAL VIEW EXPLODE` (Spark/Hive). The `LATERAL FLATTEN` and `UNNEST` variants I tried raise a clean `OptimizeError` both before and after the change, so I did not find a recursing case for them.
- I did not run the compiled `sqlglot[c]` build (`make testc`). The fix is plain Python in `resolver.py`, so I expect the compiled build to terminate as well, but that is unverified.
- I have not committed anything.

## events
[assistant] I'll start by reproducing the recursion so I can see the actual code path.
[tool_use Bash] {"command": "git status --short && ls <work>/env-sqlglot/bin/python && cat > /tmp/repro_lateral.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => col) AS f\"),\n    (\"snowflake\", \"SELECT f.value FROM missing_t, LATERAL FLATTEN(input => col) AS f\"
…[349 chars elided]…
ead=d), schema=schema, dialect=d).sql(d))\n    except RecursionError as e:\n        print(d, \"RecursionError:\", sql)\n    except Exception as e:\n        print(d, type(e).__name__, e, \"::\", sql)\nEOF\ntimeout 120 <work>/env-sqlglot/bin/python -I /tmp/repro_lateral.py 2>&1 | tail -20", "description": "Check worktree state and reproduce the recursion"}
[tool_result] <work>/env-sqlglot/bin/python
(eval):20: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sqlglot,sys; print(sqlglot.__file__, sys.version)\"; ls /tmp/repro_lateral.py", "description": "Confirm sqlglot import path in the project env"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sqlglot'
/tmp/repro_lateral.py
[assistant] The `-I` flag drops the worktree from the import path, so I'll add it explicitly in the script.
[tool_use Bash] {"command": "cd /tmp && sed -i '1i import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1\")' /tmp/repro_lateral.py && <work>/env-sqlglot/bin/python -I /tmp/repro_lateral.py 2>&1 | tail -20", "description": "Run the reproduction script against the worktree"}
[tool_result ERROR] Exit code 1
sed: -I or -i may not be used with stdin
[tool_use Bash] {"command": "cd /tmp && { echo 'import sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1\")'; cat /tmp/repro_lateral.py; } > /tmp/repro2.py && <work>/env-sqlglot/bin/python -I /tmp/repro2.py 2>&1 | tail -20", "description": "Run the reproduction script against the worktree"}
[tool_result] snowflake OK: SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."COL") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 59 :: SELECT f.value FROM missing_t, LATERAL FLATTEN(input => col) AS f
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 24 :: SELECT x FROM UNNEST(arr) AS x
bigquery OK: SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 35 :: SELECT x FROM missing_t, UNNEST(arr) AS x
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1
[assistant] None of these cases recurse, so the trigger is narrower than I assumed. I'll look at the column resolver's handling of lateral and unnest sources.
[tool_use Bash] {"command": "grep -n \"Lateral\\|Unnest\\|_get_unambiguous\\|def _\\|_expand_\\|def \" sqlglot/optimizer/qualify_columns.py | head -120", "description": "List functions and lateral/unnest handling in qualify_columns"}
[tool_result] 21:def qualify_columns(
74:        using_column_tables = _expand_using(scope, resolver)
77:            _expand_alias_refs(
92:            _expand_alias_refs(scope, resolver, dialect)
96:                _expand_stars(
105:        _expand_group_by(scope, dialect)
109:        _expand_order_by_and_distinct_on(scope, resolver)
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
162:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
184:def _pop_table
…[1221 chars elided]…
s_no_parens(expression)
817:                    struct_fields = _expand_struct_stars_with_parens(expression)
881:def _add_except_columns(expression: exp.Expr, tables, except_columns: dict[int, set[str]]) -> None:
893:def _add_rename_columns(
907:def _add_replace_columns(
921:def qualify_outputs(scope_or_expression: Scope | exp.Expr) -> None:
961:def quote_identifiers(expression: E, dialect: DialectType = None, identify: bool = True) -> E:
974:def pushdown_cte_alias_columns(scope: Scope) -> None:
[tool_use Bash] {"command": "sed -n 537,650p sqlglot/optimizer/qualify_columns.py && grep -n \"def \\(get_source_columns\\|get_table\\|_get_all_source_columns\\|get_source_columns_from_series\\|all_columns\\|_get_unambiguous\\|get_columns\\)\" sqlglot/optimizer/resolver.py", "description": "Read column conversion and qualify logic; locate resolver methods"}
[tool_result] def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
    """
    Converts `Column` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."field2"), but they need to be
    normalized to `Dot(Dot(...(<table>.<column>, field1), field2, ...))` to be qualified properly.
    """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot
…[4004 chars elided]…
 table)


def _expand_struct_stars_no_parens(
    expression: exp.Dot,
) -> list[exp.Alias]:
34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
87:    def all_columns(self) -> set[str]:
95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
217:    def _get_all_source_columns(self) -> dict[str, Sequence[str]]:
296:    def _get_unambiguous_columns(
[tool_use Bash] {"command": "sed -n 25,330p sqlglot/optimizer/resolver.py", "description": "Read the Resolver class in full"}
[tool_result]         self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | None = None
        self._infer_schema: bool = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}

    def get_table(self, column: str | exp.Column) -
…[13113 chars elided]…
dows a column name from another table.
        unnest_original_aliases: dict[str, str] = {}
        if self.dialect.UNNEST_COLUMN_ONLY:
            unnest_original_aliases = {
                alias_arg.columns[0].name: source_name
                for source_name, source in self.scope.sources.items()
                if (
                    isinstance(source.expression, exp.Unnest)
                    and (alias_arg := source.expression.args.get("alias"))
                    and alias_arg.columns
[assistant] The likely recursion point is `_get_unnest_column_type`, which runs for lateral explode and unnest sources. I'll read it.
[tool_use Bash] {"command": "grep -n \"_get_unnest_column_type\\|_struct_field_names\" sqlglot/optimizer/resolver.py && sed -n \"$(grep -n 'def _get_unnest_column_type' sqlglot/optimizer/resolver.py | cut -d: -f1),+45p\" sqlglot/optimizer/resolver.py", "description": "Read _get_unnest_column_type implementation"}
[tool_result] 167:                            col_type = self._get_unnest_column_type(unnest_expr, self.scope.parent)
175:                    columns.extend(self._struct_field_names(source_expr.type))
182:                        col_type = self._get_unnest_column_type(explode_col, source.parent)
183:                        columns.extend(self._struct_field_names(col_type))
353:    def _struct_field_names(self, col_type: exp.DataType | None) -> list[str]:
363:    def _get_unnest_column_type(self, column: exp.C
…[1557 chars elided]…
of the column, or None if not found.
        """
        if isinstance(source, exp.Table):
            # base table - get the column type from schema
            col_type: exp.DataType | None = self.schema.get_column_type(source, column)
            if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                return col_type
        elif isinstance(source, Scope):
            # iterate over all sources in the scope
            for source_name, nested_source in source.sources.items():
[tool_use Bash] {"command": "sed -n 353,362p sqlglot/optimizer/resolver.py && sed -n 408,440p sqlglot/optimizer/resolver.py", "description": "Read rest of type-tracing helpers"}
[tool_result]     def _struct_field_names(self, col_type: exp.DataType | None) -> list[str]:
        if col_type and col_type.is_type(exp.DType.ARRAY):
            col_type = seq_get(col_type.expressions, 0)

        return (
            [k.name for k in col_type.expressions]
            if col_type and col_type.is_type(exp.DType.STRUCT)
            else []
        )

            for source_name, nested_source in source.sources.items():
                col_type = self._get_column_type_from_scope(nested_source, column)
                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
                    return col_type

        return None
[assistant] I think I see the cycle: an unqualified column in a lateral explode calls `get_table`, which collects source columns, which re-enters the same lateral explode path. I'll test queries that use `Lateral(Explode)` and unnest, with the base table missing from the schema.
[tool_use Bash] {"command": "cat > /tmp/repro3.py <<'EOF'\nimport sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1\")\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"arr\": \"ARRAY<STRUCT<a INT>>\", \"id\": \"INT\"}}\ncases = [\n    (\"spark\", \"SELECT x FROM missing LATERAL VIEW EXPLODE(arr)
…[724 chars elided]…
(sql, read=d), schema=schema, dialect=d).sql(d))\n    except RecursionError:\n        print(d, \"RecursionError ::\", sql)\n    except Exception as e:\n        print(d, type(e).__name__, str(e)[:100], \"::\", sql)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro3.py 2>&1 | tail -20", "description": "Probe lateral/unnest cases with a missing base table"}
[tool_result] spark RecursionError :: SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x
spark OptimizeError Alias already used: t :: SELECT x FROM t LATERAL VIEW EXPLODE(arr) t AS x
hive RecursionError :: SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x
snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 57 :: SELECT f.value FROM missing, LATERAL FLATTEN(input => arr) AS f
snowflake OK: SELECT "F"."VALUE" AS "VALUE" FROM "MISSING" AS "M", LATERAL FLATTEN(input => "M"."ARR") AS
…[54 chars elided]…
igquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 35 :: SELECT x.a FROM missing, UNNEST(arr) AS x
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 45 :: SELECT x.a FROM missing CROSS JOIN UNNEST(arr) AS x
duckdb OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 33 :: SELECT x FROM missing, UNNEST(arr) AS u(x)
presto OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 43 :: SELECT x FROM missing CROSS JOIN UNNEST(arr) AS u(x)
[assistant] Spark and Hive `LATERAL VIEW EXPLODE` with a missing base table reproduce the `RecursionError`. Before fixing, I'll confirm the cycle from the traceback.
[tool_use Bash] {"command": "cat > /tmp/tb.py <<'EOF'\nimport sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1\")\nimport sqlglot, traceback\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"arr\": \"ARRAY<STRUCT<a INT>>\", \"id\": \"INT\"}}\ntry:\n    qualify(sqlglot.parse_one(\"SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x\", read=\"spark\"), schema=schema, dialect=\"spark\")\nexcept RecursionError:\n    tb = traceback.extract_tb(sys.exc_info()[2])\n    for f in tb[:40]:\n        print(f.name, f.lineno)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/tb.py 2>&1 | head -40", "description": "Capture a traceback of the spark recursion"}
[tool_result] <module> 6
qualify 98
qualify_columns 85
_qualify_columns 621
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
_get_table_name_from_sources 234
_get_all_source_columns 220
get_source_columns 182
_get_unnest_column_type 380
get_table 45
[assistant] The cycle is confirmed: `get_source_columns` (lateral explode) → `_get_unnest_column_type` → a new `Resolver` on the parent scope → `_get_all_source_columns` → `get_source_columns` on the same lateral again. The task also names `FLATTEN` and `UNNEST`, so I'll check whether those paths hit the same cycle when nested or using `UNNEST_COLUMN_ONLY`.
[tool_use Bash] {"command": "cat > /tmp/repro4.py <<'EOF'\nimport sys; sys.path.insert(0, \"~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1\")\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"arr\": \"ARRAY<STRUCT<a INT>>\", \"id\": \"INT\"}}\ncases = [\n    (\"bigquery\", \"SELECT * FROM (SELECT x.a FROM missing, UNNE
…[811 chars elided]…
).__name__, str(e)[:100], \"::\", sql)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro4.py 2>&1 | tail -20; cd ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1 && grep -rn \"Resolver(\" sqlglot | grep -v \"class Resolver\"", "description": "Probe nested and BigQuery/Snowflake unnest variants"}
[tool_result] bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 50 :: SELECT * FROM (SELECT x.a FROM missing, UNNEST(arr) AS x)
bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 60 :: SELECT * FROM (SELECT x.a FROM missing CROSS JOIN UNNEST(arr) AS x)
bigquery OK: SELECT `_1`.`a` AS `a` FROM (SELECT `x`.`a` AS `a` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`) AS `_1`
snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 72 :: SELECT * FR
…[204 chars elided]…
 f
spark RecursionError :: SELECT * FROM (SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x)
spark OK: SELECT `t2`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) t2 AS `x`
sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
[assistant] I have a reliable repro: Spark/Hive `LATERAL VIEW EXPLODE` with an unqualified column and a missing base table. The `FLATTEN` and `UNNEST` variants I tried raise a clean `OptimizeError` instead, so the cycle is specifically in the lateral-explode branch of `Resolver`. Next I'll read the constructor and the existing tests for this area before editing.
[tool_use Bash] {"command": "sed -n 1,24p sqlglot/optimizer/resolver.py && grep -rln \"LATERAL VIEW EXPLODE\\|lateral\" tests/ | head; grep -n \"LATERAL VIEW\" tests/test_optimizer.py | head -5", "description": "Read Resolver constructor and find related existing tests"}
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
…[638 chars elided]…
able`.`items`) ci AS `ci`",
738:                    "SELECT (SELECT SUM(ci.amount) FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci WHERE ci.type = 'promotion') AS total FROM my_table",
749:            "SELECT (SELECT SUM(`ci`.`amount`) AS `_col_0` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci` WHERE `ci`.`type` = 'promotion') AS `total` FROM `my_table` AS `my_table`",
1693:            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
[assistant] The cycle goes through a fresh `Resolver` on the parent scope, so a per-instance guard can't break it. I'll keep a set of lateral sources currently being resolved, share it with the parent resolver, and have a re-entered lateral contribute no columns. That lets the lookup finish and leaves the non-cyclic path unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n", "new_string": "        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        self._resolving_laterals: set[int] = set()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    explode_col = source_expr.this.this\n\n                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explo
…[591 chars elided]…
                   ):\n                        self._resolving_laterals.add(id(source))\n                        try:\n                            col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        finally:\n                            self._resolving_laterals.discard(id(source))\n                        columns.extend(self._struct_field_names(col_type))"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema)\n            table_identifier", "new_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema)\n            parent_resolver._resolving_laterals = self._resolving_laterals\n            table_identifier"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Now I'll rerun the repro scripts against the change.
[tool_use Bash] {"command": "cd /tmp && P=<work>/env-sqlglot/bin/python; $P -I /tmp/repro3.py; echo ---; $P -I /tmp/repro4.py", "description": "Rerun repro scripts after the fix"}
[tool_result] spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 46 :: SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x
spark OptimizeError Alias already used: t :: SELECT x FROM t LATERAL VIEW EXPLODE(arr) t AS x
hive OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 46 :: SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x
snowflake OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 57 :: SELECT f.value FROM missing, LATERAL FLATTEN(input => arr) AS f
s
…[1239 chars elided]…
ke OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51 :: SELECT * FROM missing, LATERAL FLATTEN(input => arr) AS f
spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 61 :: SELECT * FROM (SELECT x FROM missing LATERAL VIEW EXPLODE(arr) t AS x)
spark OK: SELECT `t2`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) t2 AS `x`
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1
[assistant] Every case now terminates. The Spark/Hive case raises a clean `OptimizeError` instead of recursing, and the in-schema cases still qualify. Next I'll run the full project test suite to check for regressions.
[tool_use Bash] {"command": "time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full project test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[436 chars elided]…
......................................................................................................................................................................................................... [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 53.63s
<work>/env-sqlglot/bin/python -m   123.90s user 16.81s system 261% cpu 53.903 total
tail -25  0.00s user 0.00s system 0% cpu 53.903 total
[assistant] The full suite passes: 1120 tests and 18166 subtests. Now I'll add a regression test next to the existing qualify-columns tests.
[tool_use Bash] {"command": "grep -n \"def test_qualify_columns\\|def test_.*lateral\\|OptimizeError\" tests/test_optimizer.py | head -30 && sed -n 1685,1700p tests/test_optimizer.py", "description": "Locate qualify-columns tests and error-case patterns"}
[tool_result] 11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
357:    def test_qualify_columns(self, logger):
697:            OptimizeError, "Column 'foo' could not be resolved. Line: 1, Col: 10"
705:        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
753:    def test_qualify_columns__with_invisible(self):
763:    def test_qualify_columns__invalid(self):
766:                with self.assertRaises((OptimizeError, SchemaError)):
790:        with self.
…[391 chars elided]…
.type.this)
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
[tool_use Bash] {"command": "sed -n 763,772p tests/test_optimizer.py", "description": "Read the qualify invalid-input test"}
[tool_result]     def test_qualify_columns__invalid(self):
        for sql in load_sql_fixtures("optimizer/qualify_columns__invalid.sql"):
            with self.subTest(sql):
                with self.assertRaises((OptimizeError, SchemaError)):
                    expression = optimizer.qualify_columns.qualify_columns(
                        parse_one(sql), schema=self.schema
                    )
                    optimizer.qualify_columns.validate_qualify_columns(expression)

        # this makes sure the fallback scenario in get_table in resolver is covered
[assistant] I'll add a focused regression test after `test_lateral_annotation`. It covers the missing-table case, which must end in a clean `OptimizeError`, and the in-schema case, which must still qualify.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\n\n    def test_derived_tables_column_annotation(self):", "new_string": "        self.assertEqual(expression.type.this, exp.DataType.Type.INT)\
…[443 chars elided]…
        optimizer.qualify.qualify(\n                parse_one(\"SELECT x FROM t LATERAL VIEW EXPLODE(arr) t2 AS x\", read=\"spark\"),\n                schema=schema,\n                dialect=\"spark\",\n            ).sql(\"spark\"),\n            \"SELECT `t2`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) t2 AS `x`\",\n        )\n\n    def test_derived_tables_column_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135253-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Next I'll confirm the new test fails on the original resolver and passes with the fix, then run the style checks. I'll back up my version first and restore it afterward.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python && cp sqlglot/optimizer/resolver.py /tmp/resolver_fixed.py && git show HEAD:sqlglot/optimizer/resolver.py > sqlglot/optimizer/resolver.py && $P -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral_explode_unqualified 2>&1 | tail -4; cp /tmp/resolver_fixed.py sqlglot/optimizer/resolver.py && $P -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral_explode_unqualified 2>&1 | tail -2; git diff --stat; grep -n \"^style\\|ruff\\|mypy\" Makefile | head", "description": "Verify the test fails without the fix and passes with it"}
[tool_result] !!! Recursion detected (same locals & position)
=========================== short test summary info ============================
FAILED tests/test_optimizer.py::TestOptimizer::test_lateral_explode_unqualified_column_missing_table
1 failed, 79 deselected in 0.29s
.                                                                        [100%]
1 passed, 79 deselected in 0.19s
 sqlglot/optimizer/resolver.py | 16 ++++++++++++++--
 tests/test_optimizer.py       | 16 ++++++++++++++++
 2 files changed, 30 insertions(+), 2 deletions(-)
41:# sqlglotc requires Python 3.10+ (sqlglot-mypy 1.20+ dropped 3.9). On 3.9
115:style:
[assistant] The test fails on the original code and passes with the fix. Next are the style and type checks, then the full suite again.
[tool_use Bash] {"command": "sed -n 115,122p Makefile; P=<work>/env-sqlglot/bin/python; $P -m ruff --version 2>&1; $P -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -3; $P -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -3; $P -m mypy --version 2>&1 | tail -1", "description": "Check the style target and run ruff and mypy"}
[tool_result] style:
	pre-commit run --all-files
	@if [ -f sqlglot-integration-tests/Makefile ]; then \
		MYPYPATH=$(abspath .) $(MAKE) -C sqlglot-integration-tests style && \
		$(MAKE) -C sqlglot-integration-tests check-submodule; \
	fi

check: style test testc
ruff 0.15.6
All checks passed!
2 files already formatted
mypy 2.3.0.post2 (compiled: yes)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m mypy sqlglot/optimizer/resolver.py 2>&1 | tail -3; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Run mypy on resolver and the full test suite again"}
[tool_result] Success: no issues found in 1 source file
................................................          [100%]
1121 passed, 18166 subtests passed in 49.09s
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
[assistant] Qualifying a `LATERAL VIEW EXPLODE` over an unqualified column no longer recurses when the base table is missing from the schema. The full suite passes (1121 tests, 18166 subtests), and ruff and mypy are clean.

**Cause:** In `sqlglot/optimizer/resolver.py`, resolving a lateral explode's argument runs `_get_unnest_column_type`. That builds a new `Resolver` on the parent scope, which collects the columns of every source, including the lateral itself. Collecting the lateral's columns calls the same explode resolution again, so it loops until the stack overflows.

**Fix:** The resolver now tracks
…[590 chars elided]…
ptimizer.py`. It fails on the original code with the recursion error and passes with the fix. No existing tests were changed.

**Scope notes:**
- I could only reproduce the recursion for `LATERAL VIEW EXPLODE` (Spark/Hive). The `LATERAL FLATTEN` and `UNNEST` variants I tried raise a clean `OptimizeError` both before and after the change, so I did not find a recursing case for them.
- I did not run the compiled `sqlglot[c]` build (`make testc`). The fix is plain Python in `resolver.py`, so I expect the compiled build to terminate as well, but that is unverified.
- I have not committed anything.
