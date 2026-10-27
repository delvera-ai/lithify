# trajectory base-1

final message:
Fixed: qualifying a Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr`, a non-empty schema, and the base table missing from that schema now terminates instead of recursing. The full suite passes (1121 tests), including a new regression test.

**Root cause:** In `sqlglot/optimizer/resolver.py`, `get_source_columns` for a `Lateral(Explode)` source calls `_get_unnest_column_type`. That builds a new `Resolver` on the parent scope and calls `get_table`, which calls `get_source_columns` on the same lateral again. The per-instance cache is only written after the call returns, and each hop uses a fresh resolver, so nothing stopped the loop.

**Fix:**
- `Resolver` takes an optional `_exploding` set of lateral source ids, shared with the parent resolvers it creates.
- A lateral whose explode column is already being resolved skips the type lookup and falls back to its plain named columns. That is what it returns when no type is found anyway.
- Changes are in `sqlglot/optimizer/resolver.py`. The regression test is `test_lateral_explode_unqualified_column_missing_table` in `tests/test_optimizer.py`.

**Behaviour now:**
- Non-empty schema, base table missing, unqualified column: `OptimizeError: Column 'arr' could not be resolved`. This matches what `SELECT arr FROM t` already does against that schema.
- Empty schema, or the table present: qualifies to `t.arr` as before.
- A two-lateral cycle (`EXPLODE(c) … EXPLODE(a)`) also terminates.

**Checks:**
- Pytest: 1121 passed.
- `ruff check`, `ruff format --check`, and `mypy` on the changed files are clean.
- I did not run the compiled `sqlglot[c]` build (`make testc`). The fix removes the unbounded recursion, so the process crash should go with it, but I haven't confirmed that on the compiled build.

**Not changed:** Snowflake `LATERAL FLATTEN(input => arr)` with the table missing does not recurse. Its argument is a `Kwarg`, not a `Column`, so it never reaches the type lookup, and it ends in the same `OptimizeError`. I left it alone since it already terminates.

I haven't committed anything. The changes are in the working tree of this worktree.

## events
[assistant] I'll start by reproducing the recursion with a minimal query, then trace it in the column resolver.
[tool_use Bash] {"command": "git status --short | head && ls <work>/env-sqlglot/bin/python 2>&1; cat > /tmp/repro_flatten.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"other\": {\"id\": 
…[482 chars elided]…
nError\")\n    except Exception as e:\n        print(name, type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_flatten.py').read())\" 2>&1 | tail -20", "description": "Check env and reproduce the recursion"}
[tool_result] <work>/env-sqlglot/bin/python
snowflake_flatten OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
bq_unnest OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
presto_unnest OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
[assistant] The repro raised `OptimizeError`, not `RecursionError`, so my inputs don't hit the bug yet. I'll read the column resolver to find the path that recurses.
[tool_use Bash] {"command": "grep -n \"def \\|Unnest\\|Lateral\\|Explode\\|_get_source\\|expand_\" sqlglot/optimizer/qualify_columns.py | head -150", "description": "List functions in qualify_columns"}
[tool_result] 21:def qualify_columns(
24:    expand_alias_refs: bool = True,
25:    expand_stars: bool = True,
43:        expand_alias_refs: Whether to expand references to aliases.
44:        expand_stars: Whether to expand star queries. This is a necessary step
74:        using_column_tables = _expand_using(scope, resolver)
76:        if (schema.empty or dialect.FORCE_EARLY_ALIAS_REF_EXPANSION) and expand_alias_refs:
77:            _expand_alias_refs(
81:                expand_only_groupby=dialect.EXPAND_ON
…[1954 chars elided]…
s_no_parens(expression)
817:                    struct_fields = _expand_struct_stars_with_parens(expression)
881:def _add_except_columns(expression: exp.Expr, tables, except_columns: dict[int, set[str]]) -> None:
893:def _add_rename_columns(
907:def _add_replace_columns(
921:def qualify_outputs(scope_or_expression: Scope | exp.Expr) -> None:
961:def quote_identifiers(expression: E, dialect: DialectType = None, identify: bool = True) -> E:
974:def pushdown_cte_alias_columns(scope: Scope) -> None:
[tool_use Bash] {"command": "sed -n 537,650p sqlglot/optimizer/qualify_columns.py; grep -n \"def get_source_columns\\|def get_table\\|def get_source_columns\\|def _get_unnest\\|def unnest\\|Unnest\\|Lateral\\|Explode\\|Flatten\" sqlglot/optimizer/resolver.py", "description": "Read column qualification and resolver hits"}
[tool_result] def _convert_columns_to_dots(scope: Scope, resolver: Resolver) -> None:
    """
    Converts `Column` instances that represent STRUCT or JSON field lookup into chained `Dots`.

    These lookups may be parsed as columns (e.g. "col"."field"."field2"), but they need to be
    normalized to `Dot(Dot(...(<table>.<column>, field1), field2, ...))` to be qualified properly.
    """
    converted = False
    for column in itertools.chain(scope.columns, scope.stars):
        if isinstance(column, exp.Dot
…[4339 chars elided]…
Sequence[str]:
156:                source_expr := source.expression, (exp.Values, exp.Unnest, exp.Lateral)
163:                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):
176:                elif isinstance(source_expr, exp.Lateral) and isinstance(
177:                    source_expr.this, exp.Explode
328:                    isinstance(source.expression, exp.Unnest)
363:    def _get_unnest_column_type(self, column: exp.Column, scope: Scope) -> exp.DataType | None:
[tool_use Bash] {"command": "sed -n 25,240p sqlglot/optimizer/resolver.py", "description": "Read resolver get_table and get_source_columns"}
[tool_result]         self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | None = None
        self._infer_schema: bool = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}

    def get_table(self, column: str | exp.Column) -
…[9338 chars elided]…
str]] | None = None
    ) -> str | None:
        if not source_columns:
            # If not supplied, get all sources to calculate unambiguous columns
            if self._unambiguous_columns is None:
                self._unambiguous_columns = self._get_unambiguous_columns(
                    self._get_all_source_columns()
                )

            unambiguous_columns = self._unambiguous_columns
        else:
            unambiguous_columns = self._get_unambiguous_columns(source_columns)
[assistant] The recursion probably runs through `_get_unnest_column_type`, which resolves the column in the parent scope. Reading that next.
[tool_use Bash] {"command": "sed -n 240,420p sqlglot/optimizer/resolver.py", "description": "Read rest of resolver helpers"}
[tool_result]         return unambiguous_columns.get(column_name)

    def _get_column_join_context(self, column: exp.Column) -> exp.Join | None:
        """
        Check if a column participating in a join can be qualified based on the source order.
        """
        args = self.scope.expression.args
        joins = args.get("joins")

        if not joins or args.get("laterals") or args.get("pivots"):
            # Feature gap: We currently don't try to disambiguate columns if other sources
            # 
…[6101 chars elided]…
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
[assistant] The likely loop: `get_source_columns` on a `Lateral(Explode)` or `Unnest` source calls `_get_unnest_column_type`, which builds a resolver for the same scope and calls `get_table`, which calls `get_source_columns` on that same source again. The cache is only written after the call returns, so nothing stops it. I'll test a few shapes to trigger it.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"other\": {\"id\": \"INT\"}}\ncases = [\n (\"spark\", \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x\"),\n (\"hive\", \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x\"),\n (\"bigquery\", \"SELECT x FROM t, UNNEST(arr) AS x\"),\n (\"bigquery\", \"SEL
…[577 chars elided]…
e:\n        print(d, \"|\", sql, \"->\", type(e).__name__, str(e)[:100])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro2.py').read())\" 2>&1 | tail -20", "description": "Try more UNNEST/LATERAL shapes to trigger recursion"}
[tool_result] spark | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> RecursionError
hive | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> RecursionError
bigquery | SELECT x FROM t, UNNEST(arr) AS x -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery | SELECT x FROM UNNEST(arr) AS x -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 24
snowflake | SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f -> OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51
snowflake | SELECT value FROM LATERAL FLATTEN(input => arr) -> OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 46
snowflake | SELECT f.value FROM t, LATERAL FLATTEN(input => t.arr) f -> SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
presto | SELECT x FROM t CROSS JOIN UNNEST(arr) AS u(x) -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
[assistant] Spark and Hive `LATERAL VIEW EXPLODE` reproduce the `RecursionError`. Before settling on a fix, I'll confirm the recursion cycle from the traceback and check how Snowflake's `FLATTEN` parses.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys,traceback; sys.path.insert(0,'.')\nfrom sqlglot import parse_one, exp\nfrom sqlglot.optimizer.qualify import qualify\nschema={'other':{'id':'INT'}}\ntry:\n    qualify(parse_one('SELECT x FROM t LATERAL VIEW
…[6 chars elided]…
DE(arr) u AS x', read='spark'), schema=schema, dialect='spark')\nexcept RecursionError:\n    tb=traceback.format_exc().splitlines()\n    print('\\n'.join(tb[:12])); print('...'); print('\\n'.join(tb[-30:]))\nprint(repr(parse_one('SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f', read='snowflake').args['joins'][0]))\n\" 2>&1 | cut -c1-220", "description": "Show recursion cycle in traceback"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify.py", line 98, in qualify
    expression = qualify_columns_func(
                 ^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_colu
…[3574 chars elided]…
=input),
        expression=Column(
          this=Identifier(this=arr, quoted=False)))),
    view=False,
    outer=False,
    alias=TableAlias(
      this=Identifier(this=f, quoted=False),
      columns=[
        Identifier(this=SEQ, quoted=False),
        Identifier(this=KEY, quoted=False),
        Identifier(this=PATH, quoted=False),
        Identifier(this=INDEX, quoted=False),
        Identifier(this=VALUE, quoted=False),
        Identifier(this=THIS, quoted=False)]),
    ordinality=False))
[assistant] The cycle is confirmed: `get_source_columns` (Lateral/Explode branch) → `_get_unnest_column_type` → a new `Resolver` on the parent scope → `get_table` → `_get_all_source_columns` → `get_source_columns` on the same lateral again. Each hop creates a fresh `Resolver`, so the per-instance cache never sees the cycle. I'll check how the Snowflake form and a few neighbouring cases behave, then decide where to put the guard.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ndef run(d, sql, schema):\n    try: print(d,'|',sql,'->',qualify(parse_one(sql,read=d),schema=schema,dia
…[535 chars elided]…
run('snowflake','SELECT value FROM t, LATERAL FLATTEN(input => arr)',S)\nrun('snowflake','SELECT value FROM t, LATERAL FLATTEN(input => t.arr)',S)\nrun('snowflake','SELECT value FROM t, LATERAL FLATTEN(input => arr)',{'t':{'arr':'ARRAY'}})\nrun('bigquery','SELECT x FROM (SELECT * FROM t, UNNEST(arr) AS x)',S)\n\" 2>&1 | cut -c1-260", "description": "Probe neighbouring cases for expected behavior"}
[tool_result] spark | SELECT arr FROM t -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 10
spark | SELECT x FROM t LATERAL VIEW EXPLODE(t.arr) u AS x -> SELECT `u`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) u AS `x`
spark | SELECT x FROM (SELECT * FROM t LATERAL VIEW EXPLODE(arr) u AS x) -> RecursionError
spark | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> SELECT `u`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) u AS `x`
spark | SELECT x FROM t LATERAL V
…[315 chars elided]…
_FLATTENED"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "_FLATTENED"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
snowflake | SELECT value FROM t, LATERAL FLATTEN(input => arr) -> SELECT "_FLATTENED"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."ARR") AS "_FLATTENED"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
bigquery | SELECT x FROM (SELECT * FROM t, UNNEST(arr) AS x) -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 42
[assistant] Findings so far:
- Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr`, a schema present, and the base table missing → `RecursionError`. This is the reported bug. It also appears when the query sits in a subquery.
- Qualified (`t.arr`), empty-schema, and table-present variants already work.
- Snowflake `FLATTEN(input => arr)` doesn't recurse. Its explode argument is a `Kwarg`, not a `Column`, so it never reaches the type lookup. It fails with a normal `OptimizeError` instead.

Now I'll read the resolver's constructor and its callers so I can break the cycle.
[tool_use Bash] {"command": "sed -n 1,24p sqlglot/optimizer/resolver.py; grep -rn \"Resolver(\" sqlglot | head; grep -rn \"lateral.*explode\\|LATERAL VIEW EXPLODE\\|explode\" tests/test_optimizer.py tests/fixtures/optimizer/qualify_columns.sql | head -20", "description": "Read Resolver init and callers, related tests"}
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
…[1794 chars elided]…
OM my_table",
tests/test_optimizer.py:749:            "SELECT (SELECT SUM(`ci`.`amount`) AS `_col_0` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci` WHERE `ci`.`type` = 'promotion') AS `total` FROM `my_table` AS `my_table`",
tests/test_optimizer.py:1693:            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
tests/test_optimizer.py:1847:        annotate_types(parse_one("select x from y lateral view explode(y) as x")).expressions[0]
[assistant] The cycle always re-enters through the same lateral `Scope` object, but each hop builds a new `Resolver`, so the guard has to be shared across instances. I'll pass an in-progress set of lateral source ids through the constructor and into the parent resolver. When a lateral is re-entered during its own explode-type lookup, it falls back to its plain named columns. That matches what it returns when no type is found.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[850 chars elided]…
 None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # Ids of LATERAL EXPLODE sources whose exploded column is being resolved. Shared with\n        # the parent resolvers so that a source doesn't recursively resolve itself\n        self._exploding: set[int] = set() if _exploding is None else _exploding"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    explode_col = source_expr.this.this\n\n                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explo
…[351 chars elided]…
self._exploding\n                    ):\n                        self._exploding.add(id(source))\n                        try:\n                            col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        finally:\n                            self._exploding.discard(id(source))\n                        columns.extend(self._struct_field_names(col_type))"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema)", "new_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema, self._exploding)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Now I'll re-run the repro cases against the patched resolver.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ndef run(d, sql, schema):\n    try: print(d,'|',sql,'->',qualify(parse_one(sql,read=d),schema=schema,dia
…[420 chars elided]…
y AS c',S)\nrun('spark','SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x',{'t':{'arr':'ARRAY<STRUCT<x:INT>>'}})\nrun('spark','SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x',{})\nrun('snowflake','SELECT value FROM t, LATERAL FLATTEN(input => arr)',S)\nrun('bigquery','SELECT x FROM (SELECT * FROM t, UNNEST(arr) AS x)',S)\n\" 2>&1 | cut -c1-260", "description": "Re-run repro cases after the fix"}
[tool_result] spark | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
spark | SELECT x FROM (SELECT * FROM t LATERAL VIEW EXPLODE(arr) u AS x) -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 55
hive | SELECT x FROM t LATERAL VIEW EXPLODE(c) x AS a LATERAL VIEW EXPLODE(a) y AS c -> OptimizeError Column 'x' could not be resolved. Line: 1, Col: 8
spark | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> SELECT `u`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) u AS `x`
spark | SELECT x FROM t LATERAL VIEW EXPLODE(arr) u AS x -> SELECT `u`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) u AS `x`
snowflake | SELECT value FROM t, LATERAL FLATTEN(input => arr) -> OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 49
bigquery | SELECT x FROM (SELECT * FROM t, UNNEST(arr) AS x) -> OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 42
[assistant] The recursion is gone for every shape I tried, and the nested-lateral variant also terminates. With a schema present but without `t`, the unqualified `arr` now raises the standard `OptimizeError: could not be resolved`. That's the same result as plain `SELECT arr FROM t` against that schema, so it's consistent with existing behaviour. Next I'll add a regression test next to the existing LATERAL test in `tests/test_optimizer.py`.
[tool_use Bash] {"command": "sed -n 1680,1700p tests/test_optimizer.py; grep -n \"^from\\|^import\\|OptimizeError\" tests/test_optimizer.py | head -30", "description": "View existing lateral test and imports"}
[tool_result]             ),
            (
                "SELECT DATEDIFF('2023-01-01', '2023-01-02', DAY) FROM x AS x",
                exp.DataType.Type.INT,
            ),
        ]:
            with self.subTest(sql):
                expression = annotate_types(parse_one(sql), schema=schema)
                self.assertEqual(expected_type, expression.expressions[0].type.this)
                self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.opt
…[1062 chars elided]…
lk_in_scope
17:from sqlglot.schema import MappingSchema
18:from tests.helpers import (
697:            OptimizeError, "Column 'foo' could not be resolved. Line: 1, Col: 10"
705:        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
766:                with self.assertRaises((OptimizeError, SchemaError)):
790:        with self.assertRaises(OptimizeError) as ctx:
804:        with self.assertRaises(OptimizeError) as ctx:
814:        with self.assertRaises(OptimizeError) as ctx:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "    def test_derived_tables_column_annotation(self):\n        schema = {\"x\": {\"cola\": \"INT\"}, \"y\": {\"cola\": \"FLOAT\"}}", "new_string": "    def test_lateral_explode_unqualified_column_missing_table(self
…[712 chars elided]…
 x FROM t LATERAL VIEW EXPLODE(arr) u AS x\", read=\"spark\"),\n                schema={},\n                dialect=\"spark\",\n            ).sql(\"spark\"),\n            \"SELECT `u`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) u AS `x`\",\n        )\n\n    def test_derived_tables_column_annotation(self):\n        schema = {\"x\": {\"cola\": \"INT\"}, \"y\": {\"cola\": \"FLOAT\"}}"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-095917-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the new test, then the full suite with the project's pytest command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"lateral\" 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run lateral tests then full pytest suite"}
[tool_result] ..                                                                     [100%]
2 passed, 78 deselected, 2 subtests passed in 0.26s
........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 3
…[382 chars elided]…
........................... [ 64%]
........................................................................................................................................................................................................................................................................................................................................... [ 94%]
...................................................................        [100%]
1121 passed, 18168 subtests passed in 58.84s
[assistant] All 1121 tests pass, including the new regression test. The compiled build also needs a lint/format check on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PY -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -5; $PY -m mypy sqlglot/optimizer/resolver.py 2>&1 | tail -3; git status --short", "description": "Lint, format-check and type-check changed files"}
[tool_result] All checks passed!
2 files already formatted
Success: no issues found in 1 source file
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
[assistant] Fixed: qualifying a Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr`, a non-empty schema, and the base table missing from that schema now terminates instead of recursing. The full suite passes (1121 tests), including a new regression test.

**Root cause:** In `sqlglot/optimizer/resolver.py`, `get_source_columns` for a `Lateral(Explode)` source calls `_get_unnest_column_type`. That builds a new `Resolver` on the parent scope and calls `get_table`, which calls `get_source_columns` on the same lateral again. The per-instance cache is only written after the call returns, and each h
…[926 chars elided]…
-check`, and `mypy` on the changed files are clean.
- I did not run the compiled `sqlglot[c]` build (`make testc`). The fix removes the unbounded recursion, so the process crash should go with it, but I haven't confirmed that on the compiled build.

**Not changed:** Snowflake `LATERAL FLATTEN(input => arr)` with the table missing does not recurse. Its argument is a `Kwarg`, not a `Column`, so it never reaches the type lookup, and it ends in the same `OptimizeError`. I left it alone since it already terminates.

I haven't committed anything. The changes are in the working tree of this worktree.
