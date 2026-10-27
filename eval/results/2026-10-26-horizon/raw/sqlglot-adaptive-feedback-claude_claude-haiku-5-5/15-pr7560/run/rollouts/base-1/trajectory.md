# trajectory base-1

final message:
The aliased UNPIVOT over a CTE now qualifies correctly, with and without a schema. The full suite passes after the last edit: `SUMMARY: 1093 passed, 17866 subtests passed in 61.46s`, `EXIT: 0`. I haven't committed anything.

**What was broken:** `SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u` raised `Unknown column: v`. The check in `_qualify_columns` looks up `u`'s columns from the CTE (`id, jan, feb`) and never adds the pivot's output columns (`m`, `v`).

**The fix** (`sqlglot/optimizer/qualify_columns.py`): when an explicitly qualified source is a pivoted table, the check now adds the pivot's output columns to the CTE's columns. A new `_pivot_columns` helper computes those, reusing the same logic as star expansion.

**What I deliberately didn't change:**
- The resolver. My first attempt applied the pivot inside `Resolver.get_source_columns`. That broke the UNPIVOT's own IN list (`Ambiguous column 'jan'`), because the pivot's inputs need the pre-pivot columns. It also doubled pivot columns in star expansion.
- The star-expansion path, which already handles pivots.

**Tests:** I added `test_unpivot_cte_source_columns` to `tests/test_optimizer.py`. It covers `SELECT *`, `u.v`, and `u.*` for BigQuery, each with and without a schema. The test fails on unmodified `HEAD` (`Unknown column: v`) and passes with the fix.

**Discrepancies with your report:**
- I couldn't reproduce the `SELECT *` failure. On `HEAD`, the unaliased `SELECT * FROM c UNPIVOT(...)` already expands correctly to `id, m, v` in both schema modes, so the test covers it as a regression guard only.
- The aliased-pivot failure is the one that reproduced.

**Not fixed:** Without a schema, `SELECT u.v FROM t UNPIVOT(...) AS u` on a real table still produces `t.u.v`, which is wrong. It was wrong before this change too, and the fix doesn't touch it. The alias `u` isn't registered as a scope source for non-CTE tables, which is a separate bug in `scope.py`. Say if you want it handled here.

## events
[tool_use Bash] {"command": "cat .lithify/memory.md 2>/dev/null | head -20; git status --short | head; grep -n \"pivot\\|Pivot\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py | head -80", "description": "Check repo state and find pivot handling in optimizer"}
[tool_result] sqlglot/optimizer/qualify_tables.py:128:            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py:129:                _set_alias(pivot, canonical_aliases)
sqlglot/optimizer/qualify_tables.py:135:                # When the name is empty, it means that we have a non-table source, e.g. a pivoted cte
sqlglot/optimizer/qualify_tables.py:138:                if pivot := seq_get(source.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py
…[4060 chars elided]…
s]
sqlglot/optimizer/qualify_columns.py:870:                    pivot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns.py:872:                    pivot_columns = pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:874:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:876:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:877:                        for name in pivot_columns
[assistant] Let me reproduce both failing cases first to see the actual output.
[tool_use Bash] {"command": "cat > /tmp/repro_pivot.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfor sql in [\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n    \"WITH c AS (SELEC
…[261 chars elided]…
 print(d, \"|\", qualify(parse_one(sql, read=d), dialect=d).sql(d))\n        except Exception as e:\n            print(d, \"| ERR\", type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_pivot.py", "description": "Reproduce the pivot-over-CTE qualify failures"}
[tool_result] bigquery | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
duckdb | WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
bigquery | ERR OptimizeError Unknown column: v
duckdb | ERR OptimizeError Unknown column: v
bigquery | ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
duckdb | ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 75)
bigquery | ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 80)
duckdb | ERR OptimizeError Ambiguous column 'm' (Line: 1, Col: 80)
[assistant] Case 1 qualifies correctly in this run, so the failure is in case 2 (aliased UNPIVOT, `Unknown column: v`). My PIVOT cases were malformed (`m` isn't a column of `c`), so I'll fix those too. Next, the relevant code.
[tool_use Bash] {"command": "sed -n 600,660p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 775,890p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 120,180p sqlglot/optimizer/qualify_tables.py", "description": "Read pivot-related sections of qualify_columns and qualify_tables"}
[tool_result]     allow_partial_qualification: bool,
) -> None:
    """Disambiguate columns, ensuring each column specifies a source"""
    for column in scope.columns:
        column_table = column.table
        column_name = column.name

        if column_table and column_table in scope.sources:
            source_columns = resolver.get_source_columns(column_table)
            if (
                not allow_partial_qualification
                and source_columns
                and column_name not in sourc
…[9262 chars elided]…
:
                    target_alias = source.alias if pivot.unpivot else None
                    _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)

                    # This case corresponds to a pivoted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
[assistant] The error comes from the `column_table in scope.sources` check, so `u` is registered as a source whose columns don't include `v`. Let me see how scope registers pivot aliases and how the resolver gets source columns.
[tool_use Bash] {"command": "sed -n 800,830p sqlglot/optimizer/scope.py; echo ----; grep -n \"def get_source_columns\" -A40 sqlglot/optimizer/resolver.py | head -70", "description": "Read scope pivot source registration and resolver"}
[tool_result]         expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a parent source (
…[4041 chars elided]…
:
158-                columns = source_expr.named_selects
159-
160-                # in bigquery, unnest structs are automatically scoped as tables, so you can
161-                # directly select a struct field in a query.
162-                # this handles the case where the unnest is statically defined.
163-                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):
164-                    if not source_expr.type or source_expr.type.is_type(exp.DType.UNKNOWN):
[assistant] The resolver already special-cases pivoted CTEs, but it returns the CTE's pre-pivot columns (`id, jan, feb`), not the pivot's output (`id, m, v`). Before choosing a fix, I'll check whether a plain table with the same pivot has the same problem, and look at the existing test coverage.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.scope import traverse_scope\nS = {\"t\": {\"id\": \"int\", \"jan\": \"int\", \"feb\": \"int\"}}\ncases = [\n    (\"bigquery\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\")
…[1009 chars elided]…
ERR\", type(e).__name__, e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro2.py; grep -rn \"UNPIVOT\" tests/fixtures/optimizer/qualify_columns.sql | head; grep -rln \"pivot\" tests/fixtures/optimizer/ | head", "description": "Check pivot qualify behavior for CTEs and tables"}
[tool_result] False | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
False | ERR OptimizeError Unknown column: v
T
…[1865 chars elided]…
 `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
tests/fixtures/optimizer/optimizer.sql
tests/fixtures/optimizer/qualify_tables.sql
[assistant] Findings so far:

- Unaliased CTE UNPIVOT is already correct, including `SELECT *` (`id, m, v`).
- Aliased CTE UNPIVOT fails with and without a schema: `u` resolves to the CTE's pre-pivot columns, so `u.v` is unknown.
- The aliased-star case passes without a schema but fails with one, for the same reason.

So the fix belongs in column resolution: a pivoted source should expose the pivot's output columns, not the raw CTE columns. The star-expansion code already computes those. Let me look at that helper and the resolver's imports.
[tool_use Bash] {"command": "sed -n 180,200p sqlglot/optimizer/qualify_columns.py; echo ----; sed -n 1,30p sqlglot/optimizer/resolver.py; echo ----; sed -n 164,200p sqlglot/optimizer/resolver.py; echo ----; grep -n \"_unpivot_columns\\|from sqlglot.optimizer.resolver\\|import resolver\\|Resolver(\" sqlglot/optimizer/*.py", "description": "Read unpivot helper, resolver imports and tail of get_source_columns"}
[tool_result]     if has_pseudocolumns:
        scope.clear_cache()


def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
    name_columns = [
        field.this
        for field in unpivot.fields
        if isinstance(field, exp.In) and isinstance(field.this, exp.Identifier)
    ]
    value_columns = (
        ident
        for e in unpivot.expressions
        for ident in (e.expressions if isinstance(e, exp.Tuple) else [e])
        if isinstance(ident, exp.Identifier)
    )

    return it
…[3406 chars elided]…
 resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/qualify_columns.py:184:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
sqlglot/optimizer/qualify_columns.py:791:            pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/optimizer/pushdown_projections.py:162:        resolver = Resolver(scope, schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
[tool_use Bash] {"command": "sed -n 200,215p sqlglot/optimizer/resolver.py; echo ----; grep -n \"pivot\" -i tests/fixtures/optimizer/qualify_columns.sql | head -30; grep -n \"unpivot\\|UNPIVOT\" -i tests/test_optimizer.py | head", "description": "Read end of get_source_columns and existing pivot tests"}
[tool_result]             elif isinstance(node, exp.Expr):
                column_aliases = node.alias_column_names
            else:
                column_aliases = []

            if column_aliases:
                # If the source's columns are aliased, their aliases shadow the corresponding column names.
                # This can be expensive if there are lots of columns, so only do this if column_aliases exist.
                columns = [
                    alias or name
                    for (name, 
…[1705 chars elided]…
sterdam_count AS us_2010_amsterdam_count, _0.us_2010_seattle_total AS us_2010_seattle_total, _0.us_2010_seattle_count AS us_2010_seattle_count FROM cities AS cities PIVOT(SUM(population) AS total, COUNT(population) AS count FOR country IN ('nl', 'us') year IN (2000, 2010) name IN ('amsterdam', 'seattle')) AS _0;
639:                    "SELECT * FROM produce UNPIVOT(sales FOR quarter IN (q1, q2))",
647:            "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`",
[assistant] The fix is to have the resolver expose a pivoted source's output columns. Before writing it, I need to know where a PIVOT's generated column names come from (`pivot.args["columns"]`), since the resolver runs before star expansion.
[tool_use Bash] {"command": "grep -rn '\"columns\"' sqlglot/optimizer/*.py | head; grep -n \"class Pivot\" -A12 sqlglot/expressions/*.py | head -30", "description": "Locate where pivot output columns are populated"}
[tool_result] sqlglot/optimizer/qualify_tables.py:101:                "columns",
sqlglot/optimizer/qualify_tables.py:192:                    table_alias.set("columns", column_aliases)
sqlglot/optimizer/qualify_columns.py:211:            table_alias.set("columns", None)
sqlglot/optimizer/qualify_columns.py:802:            pivot_output_columns = [c.output_name for c in pivot.args.get("columns", [])]
sqlglot/expressions/core.py:1880:class PivotAlias(Alias):
sqlglot/expressions/core.py-1881-    pass
sqlglot/expre
…[1024 chars elided]…
sions": False,
sqlglot/expressions/query.py-1746-        "fields": False,
sqlglot/expressions/query.py-1747-        "unpivot": False,
sqlglot/expressions/query.py-1748-        "using": False,
sqlglot/expressions/query.py-1749-        "group": False,
sqlglot/expressions/query.py-1750-        "columns": False,
sqlglot/expressions/query.py-1751-        "include_nulls": False,
sqlglot/expressions/query.py-1752-        "default_on_null": False,
sqlglot/expressions/query.py-1753-        "into": False,
[assistant] Pivot output names come from the parser's `columns` arg, or fall back to the pivot's expressions. So the resolver can compute them without the optimizer state. I'll make the change in three parts:

1. Move `_unpivot_columns` into `resolver.py`, since `qualify_columns` imports from it, not the reverse.
2. Add a helper that maps a source's columns through a pivot.
3. Apply that helper to pivoted CTE sources in `get_source_columns`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/resolver.py", "old_string": "            # A pivoted CTE reference is stored as an exp.Table in the scope sources (see\n            # _traverse_tables in scope.py), but the underlying CTE Scope still holds the\n            # column info
…[567 chars elided]…
need to resolve pre-pivot columns.\n            pivot = None\n            if (\n                isinstance(source, exp.Table)\n                and not source.db\n                and source.args.get(\"pivots\")\n                and source.name in self.scope.cte_sources\n            ):\n                pivot = source.args[\"pivots\"][0]\n                source = self.scope.cte_sources[source.name]"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    columns = selectable.named_selects\n\n            node, _ = self.scope.selected_sources.get(name) or (None, None)", "new_string": "                    columns = selectable.named_selects\n\n            if pivot and not pivot.alias_column_names:\n                columns = pivot_columns(pivot, columns)\n\n            node, _ = self.scope.selected_sources.get(name) or (None, None)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Now the helpers. I'll put them at module level in `resolver.py`, moving `_unpivot_columns` there from `qualify_columns.py`.
[tool_use Bash] {"command": "tail -c 200 sqlglot/optimizer/resolver.py | cat -A | tail -3; grep -n \"itertools\\|^from\\|^import\\|Iterator\" sqlglot/optimizer/qualify_columns.py | head -30", "description": "Check file endings and qualify_columns imports"}
[tool_result] cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
1:from __future__ import annotations
3:import itertools
4:import typing as t
6:from sqlglot import alias, exp
7:from sqlglot.dialects.dialect import Dialect, DialectType
8:from sqlglot.errors import OptimizeError, highlight_sql
9:from sqlglot.helper import seq_get
10:from sqlglot.optimizer.annotate_types import TypeAnnotator
11:from sqlglot.optimizer.resolver import Resolver
12:from sqlglot.optimizer.scope import Scope, build_scope, trav
…[53 chars elided]…
implify import simplify_parens
14:from sqlglot.schema import Schema, ensure_schema
18:    from collections.abc import Iterator, Iterable
184:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
197:    return itertools.chain(name_columns, value_columns)
555:    for column in itertools.chain(scope.columns, scope.stars):
695:        root, *parts = [part.copy() for part in itertools.chain(dot_parts, [this])]
965:        itertools.zip_longest(expression.selects, scope.outer_columns)
[tool_use Bash] {"command": "tail -n 3 sqlglot/optimizer/resolver.py | od -c | tail -3", "description": "Inspect end of resolver.py"}
[tool_result] 0000040    y   p   e  \n  \n                                   r   e   t
0000060    u   r   n       N   o   n   e  \n                            
0000071
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/resolver.py", "offset": 215}
[tool_result] 215	                    for (name, alias) in itertools.zip_longest(columns, column_aliases)
216	                ]
217	
218	            self._get_source_columns_cache[cache_key] = columns
219	
220	        return self._get_source_columns_cache[cache_key]
221	
222	    def _get_all_source_columns(self) -> dict[str, Sequence[str]]:
223	        if self._source_columns is None:
224	            self._source_columns = {
225	                source_name: self.get_source_columns(source_name)
226	           
…[8191 chars elided]…
ol_type and not col_type.is_type(exp.DType.UNKNOWN):
410	                return col_type
411	        elif isinstance(source, Scope):
412	            # iterate over all sources in the scope
413	            for source_name, nested_source in source.sources.items():
414	                col_type = self._get_column_type_from_scope(nested_source, column)
415	                if col_type and not col_type.is_type(exp.DType.UNKNOWN):
416	                    return col_type
417	
418	        return None
419	
[assistant] I'll append the helpers to the end of `resolver.py`.
[tool_use Bash] {"command": "cat >> sqlglot/optimizer/resolver.py <<'EOF'\n\n\ndef _unpivot_columns(unpivot: exp.Pivot) -> t.Iterator[exp.Identifier]:\n    name_columns = [\n        field.this\n        for field in unpivot.fields\n        if isinstance(field, exp.In) and isinstance(field.this, exp.Identifier)\n    ]\n    value_columns = (\n        ident\n        for e in unpivot.expressions\n        for ident in 
…[678 chars elided]…
se:\n        excluded = {c.output_name for c in pivot.find_all(exp.Column)}\n        output = [c.output_name for c in pivot.args.get(\"columns\", [])] or [\n            c.alias_or_name for c in pivot.expressions\n        ]\n\n    return [c for c in columns if c not in excluded] + output\nEOF\ntail -n 3 sqlglot/optimizer/resolver.py", "description": "Append pivot column helpers to resolver module"}
[tool_result]         ]

    return [c for c in columns if c not in excluded] + output
[assistant] Now I'll remove the duplicate from `qualify_columns.py` and import it from the resolver.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:\n    name_columns = [\n        field.this\n        for field in unpivot.fields\n        if isinstance(field, exp.In) and isinstance(field.this, exp.Identifier)\n    ]\n    value_columns = (\n        ident\n        for e in unpivot.expressions\n        for ident in (e.expressions if isinstance(e, exp.Tuple) else [e])\n        if isinstance(ident, exp.Identifier)\n    )\n\n    return itertools.chain(name_columns, value_columns)\n\n\ndef _pop_table_column_aliases", "new_string": "def _pop_table_column_aliases"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "sed -i '' 's/^from sqlglot.optimizer.resolver import Resolver$/from sqlglot.optimizer.resolver import Resolver, _unpivot_columns/' sqlglot/optimizer/qualify_columns.py && grep -n \"Iterator\" sqlglot/optimizer/qualify_columns.py; grep -n \"resolver import\" sqlglot/optimizer/qualify_columns.py; <work>/env-sqlglot/bin/python -I /tmp/repro2.py", "description": "Fix import, check Iterator usage, rerun repro"}
[tool_result] 18:    from collections.abc import Iterator, Iterable
11:from sqlglot.optimizer.resolver import Resolver, _unpivot_columns
False | ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
True | ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
False | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`
…[2068 chars elided]…
 SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] My edit to `qualify_columns.py` is in place (the notice came from my own `sed -i`). The resolver change fixed `u.v`, but it introduced two regressions:

1. Aliased star now duplicates pivot columns (`u.m, u.v` twice), because the star path applies the pivot a second time on top of the resolver's output.
2. Unaliased UNPIVOT now reports `Ambiguous column 'jan'`.

I'll check how scope registers each case before deciding how to split the responsibility.
[tool_use Bash] {"command": "grep -n \"pivot_columns\\|_unpivot_columns\" sqlglot/optimizer/*.py; cat > /tmp/dbg.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.scope import traverse_scope\nfor sql in [\"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n            \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v F
…[101 chars elided]…
ry\"))[-1]\n    print({k: type(v).__name__ for k, v in root.sources.items()}, [p.alias for p in root.pivots])\n    print(\"cte_sources\", list(root.cte_sources))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/dbg.py", "description": "Inspect scope sources for the two pivot cases"}
[tool_result] sqlglot/optimizer/qualify_columns.py:11:from sqlglot.optimizer.resolver import Resolver, _unpivot_columns
sqlglot/optimizer/qualify_columns.py:775:            pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/optimizer/qualify_columns.py:853:                    pivot_columns = [c for c in columns if c not in pivot_exclude_columns]
sqlglot/optimizer/qualify_columns.py:854:                    pivot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns
…[242 chars elided]…
/optimizer/resolver.py:200:                columns = pivot_columns(pivot, columns)
sqlglot/optimizer/resolver.py:421:def _unpivot_columns(unpivot: exp.Pivot) -> t.Iterator[exp.Identifier]:
sqlglot/optimizer/resolver.py:437:def pivot_columns(pivot: exp.Pivot, columns: Sequence[str]) -> list[str]:
sqlglot/optimizer/resolver.py:447:        output = [c.output_name for c in _unpivot_columns(pivot)]
{'c': 'Scope', '': 'Table'} ['']
cte_sources ['c']
{'c': 'Scope', 'u': 'Table'} ['u']
cte_sources ['c']
[assistant] In the unaliased case the scope has a CTE source `c` plus an anonymous pivoted table `''`. The `Ambiguous column 'jan'` error sits in the UNPIVOT IN list, so I want the traceback to see which resolver call raises it.
[tool_use Bash] {"command": "cat > /tmp/dbg2.py <<'EOF'\nimport sys, traceback\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ntry:\n    qualify(parse_one(\"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\", read=\"bigquery\"), dialect=\"bigquery\")\nexcept Exception:\n    traceback.print_exc()\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/dbg2.py 2>&1 | grep -v \"^    \" | tail -20", "description": "Get traceback for the ambiguous column error"}
[tool_result] Traceback (most recent call last):
  File "/tmp/dbg2.py", line 6, in <module>
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify.py", line 110, in qualify
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 157, in validate_qualify_columns
sqlglot.errors.OptimizeError: Ambiguous column 'jan' (Line: 1, Col: 78)
[tool_use Bash] {"command": "sed -n 140,160p sqlglot/optimizer/qualify_columns.py; sed -n 60,75p sqlglot/optimizer/qualify_columns.py", "description": "Read validate_qualify_columns and qualify_columns entry"}
[tool_result]             all_unqualified_columns.extend(unqualified_columns)

    if all_unqualified_columns:
        first_column = all_unqualified_columns[0]
        line = first_column.this.meta.get("line")
        col = first_column.this.meta.get("col")
        start = first_column.this.meta.get("start")
        end = first_column.this.meta.get("end")

        error_msg = f"Ambiguous column '{first_column.name}'"
        if line and col:
            error_msg += f" (Line: {line}, Col: {col})"
        if 
…[297 chars elided]…
pe(expression):
        if dialect.PREFER_CTE_ALIAS_COLUMN:
            pushdown_cte_alias_columns(scope)

        scope_expression = scope.expression
        is_select = isinstance(scope_expression, exp.Select)

        _separate_pseudocolumns(scope, pseudocolumns)

        resolver = Resolver(scope, schema, infer_schema=infer_schema)
        _pop_table_column_aliases(scope.ctes)
        _pop_table_column_aliases(scope.derived_tables)
        using_column_tables = _expand_using(scope, resolver)
[assistant] The ambiguity is raised after qualification, meaning `jan` inside the pivot's IN list was never qualified. I'll print the resolver's view of each source to see why the pivot-block lookup doesn't resolve it.
[tool_use Bash] {"command": "cat > /tmp/dbg3.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.scope import traverse_scope\nfrom sqlglot.optimizer.resolver import Resolver\nfrom sqlglot.schema import ensure_schema\nsql = \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\"\nroot = traverse_scope(parse_one(sql, read=\"bigqu
…[68 chars elided]…
ry\"))\nfor n in root.selected_sources: print(repr(n), r.get_source_columns(n))\nprint(\"all\", r.all_columns if hasattr(r, \"all_columns\") else None)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/dbg3.py", "description": "Print resolver source columns for unaliased pivot case"}
[tool_result] 'c' ['id', 'jan', 'feb']
all {'feb', 'jan', 'id'}
[assistant] `selected_sources` only contains `c`, and that source is the CTE scope, so the pivot branch never runs here. Yet this case passed before my edits, so something else changed. I'll check the full diff rather than keep guessing.
[tool_use Bash] {"command": "git status --short && git diff", "description": "Show full working tree diff"}
[tool_result]  M sqlglot/optimizer/qualify_columns.py
 M sqlglot/optimizer/resolver.py
diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..9428ded31 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -8,7 +8,7 @@ from sqlglot.dialects.dialect import Dialect, DialectType
 from sqlglot.errors import OptimizeError, highlight_sql
 from sqlglot.helper import seq_get
 from sqlglot.optimizer.annotate_types import TypeA
…[3269 chars elided]…
ds
+            if isinstance(field, exp.In)
+            for e in field.expressions
+            for c in e.find_all(exp.Column)
+        }
+        output = [c.output_name for c in _unpivot_columns(pivot)]
+    else:
+        excluded = {c.output_name for c in pivot.find_all(exp.Column)}
+        output = [c.output_name for c in pivot.args.get("columns", [])] or [
+            c.alias_or_name for c in pivot.expressions
+        ]
+
+    return [c for c in columns if c not in excluded] + output
[assistant] The diff contains only my intended changes, so the regression comes from one of them. To confirm the baseline, I'll run the same repro against a clean `HEAD` export in a temp directory.
[tool_use Bash] {"command": "rm -rf /tmp/headcopy && mkdir /tmp/headcopy && git archive HEAD sqlglot | tar -x -C /tmp/headcopy && cd /tmp/headcopy && <work>/env-sqlglot/bin/python -I /tmp/repro2.py 2>&1 | head -4", "description": "Run repro against clean HEAD export for baseline"}
[tool_result] False | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
False | ERR OptimizeError Unknown column: v
True | ERR OptimizeError Unknown column: v
Shell cwd was reset to ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1
[assistant] Baseline behaves as I expected, so my change caused the regression. I'll check whether `get_source_columns('')` is called for the anonymous pivoted source, since that now returns different columns.
[tool_use Bash] {"command": "grep -n \"get_source_columns(\\|get_table(\\|\\.sources\\[\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/resolver.py | head -40", "description": "Find resolver call sites that could hit the anonymous pivot source"}
[tool_result] sqlglot/optimizer/resolver.py:34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
sqlglot/optimizer/resolver.py:133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
sqlglot/optimizer/resolver.py:140:            source = self.scope.sources[name]
sqlglot/optimizer/resolver.py:225:                source_name: self.get_source_columns(source_name)
sqlglot/optimizer/resolver.py:294:        available_sources = {from_name: self.get_sour
…[843 chars elided]…
er/qualify_columns.py:562:                column_table = resolver.get_table(root.name)
sqlglot/optimizer/qualify_columns.py:592:            source_columns = resolver.get_source_columns(column_table)
sqlglot/optimizer/qualify_columns.py:609:            table = resolver.get_table(column)
sqlglot/optimizer/qualify_columns.py:631:                table = resolver.get_table(column.name)
sqlglot/optimizer/qualify_columns.py:837:            columns = resolver.get_source_columns(table, only_visible=True)
[tool_use Bash] {"command": "sed -n 34,60p sqlglot/optimizer/resolver.py", "description": "Read Resolver.get_table"}
[tool_result]     def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
        """
        Get the table for a column name.

        Args:
            column: The column expression (or column name) to find the table for.
        Returns:
            The table name if it can be found/inferred.
        """
        column_name = column if isinstance(column, str) else column.name

        table_name = self._get_table_name_from_sources(column_name)

        if not table_name and isinstance(colum
…[455 chars elided]…
le to disambiguate the column
                # and we can use the source columns available at that join to get the table name
                # catch OptimizeError if column is still ambiguous and try to resolve with schema inference below
                try:
                    table_name = self._get_table_name_from_sources(
                        column_name, self._get_available_source_columns(join_context)
                    )
                except OptimizeError:
                    pass
[assistant] Nothing obvious from reading. I'll instrument `get_source_columns` from a script (no file edits) to log every call during the failing qualify.
[tool_use Bash] {"command": "cat > /tmp/dbg4.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.optimizer.resolver import Resolver\norig = Resolver.get_source_columns\ndef spy(self, name, only_visible=False):\n    r = orig(self, name, only_visible)\n    print(\"get_source_columns\", repr(name), list(r), \"| scope\", t
…[190 chars elided]…
 feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\", read=\"bigquery\"), dialect=\"bigquery\")\nexcept Exception as e: print(\"ERR\", e)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/dbg4.py", "description": "Trace resolver source-column lookups for the unaliased case"}
[tool_result] get_source_columns 't' [] | scope Select
get_source_columns 't' [] | scope Select
get_source_columns 'c' ['id', 'm', 'v'] | scope Select
get_source_columns 'c' ['id', 'm', 'v'] | scope Select
get_source_columns 'c' ['id', 'm', 'v'] | scope Select
ERR Ambiguous column 'jan' (Line: 1, Col: 78)
[assistant] Found it. After `qualify_tables`, the outer scope key `c` is the pivoted `Table`, so my resolver change applied the pivot to `c` for every lookup. That hid the pre-pivot `jan`/`feb` that the UNPIVOT's own IN list needs. Pivot-internal references need the CTE's input columns, while references from outside the pivot need the output columns.

So I'll revert the resolver change and handle this only where the explicit qualifier is checked (`u.v` / `c.v` against `source_columns`). That check is the sole place that rejects an output column, and it keeps the input-column resolution intact. The resolver is unchanged, so star expansion's existing pivot logic stays the only place that applies pivots to `*`, which avoids the duplicate columns.
[tool_use Bash] {"command": "git checkout -- sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py && git status --short && sed -n 586,600p sqlglot/optimizer/qualify_columns.py", "description": "Revert my edits and reread the explicit-qualifier check"}
[tool_result]                     # Remove the actual column parts from the rest of dot parts
                    new_column.meta["dot_parts"] = dot_parts[2 if was_qualified else 1 :]

                column.replace(exp.Dot.build([new_column, *parts]))

    if converted:
        # We want to re-aggregate the converted columns, otherwise they'd be skipped in
        # a `for column in scope.columns` iteration, even though they shouldn't be
        scope.clear_cache()


def _qualify_columns(
    scope: Scope,
    resolver: Resolver,
    allow_partial_qualification: bool,
[assistant] Now the targeted change in `_qualify_columns`. The check applies the pivot's output columns only when the source is a pivoted `Table`. I'll add a small helper beside `_unpivot_columns` that reuses the same column-name logic the star path uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)\n            if (", "new_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)\n            source = scope.sources[column_table]\n            if isinstance(source, exp.Table) and (\n                pivot := seq_get(source.args.get(\"pivots\") or [], 0)\n            ):\n                source_columns = _pivot_columns(pivot, source_columns)\n            if ("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[assistant] The tool reports the file changed on disk beyond my edit. I'll look at the full diff before going further, so I know what else is in there.
[tool_use Bash] {"command": "git status --short && git diff", "description": "Review current working tree diff after external change notice"}
[tool_result]  M sqlglot/optimizer/qualify_columns.py
diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..2fedab47c 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -606,6 +606,11 @@ def _qualify_columns(
 
         if column_table and column_table in scope.sources:
             source_columns = resolver.get_source_columns(column_table)
+            source = scope.sources[column_table]
+            if isinstance(source, exp.Table) and (
+                pivot := seq_get(source.args.get("pivots") or [], 0)
+            ):
+                source_columns = _pivot_columns(pivot, source_columns)
             if (
                 not allow_partial_qualification
                 and source_columns
[assistant] The diff holds only my change, so there's no conflicting edit. Now I'll add the `_pivot_columns` helper beside `_unpivot_columns`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pop_table_column_aliases", "new_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pivot_columns(pivot: exp.P
…[374 chars elided]…
}\n        output = [c.output_name for c in _unpivot_columns(pivot)]\n    else:\n        excluded = {c.output_name for c in pivot.find_all(exp.Column)}\n        output = [c.output_name for c in pivot.args.get(\"columns\", [])] or [\n            c.alias_or_name for c in pivot.expressions\n        ]\n\n    return [c for c in columns if c not in excluded] + output\n\n\ndef _pop_table_column_aliases"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] The helper uses `Sequence`, so I'll add it to the existing `TYPE_CHECKING` import, then rerun the repro.
[tool_use Bash] {"command": "sed -i '' 's/^    from collections.abc import Iterator, Iterable$/    from collections.abc import Iterator, Iterable, Sequence/' sqlglot/optimizer/qualify_columns.py && grep -n \"from collections.abc\" sqlglot/optimizer/qualify_columns.py && <work>/env-sqlglot/bin/python -I /tmp/repro2.py", "description": "Add Sequence type import and rerun pivot repro"}
[tool_result] 18:    from collections.abc import Iterator, Iterable, Sequence
False | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, 
…[2205 chars elided]…
 SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
True | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `p`.`id` AS `id`, `p`.`s_1` AS `s_1`, `p`.`s_2` AS `s_2` FROM `c` AS `c` PIVOT(SUM(`c`.`jan`) AS `s` FOR `c`.`feb` IN (1, 2)) AS `p`
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] Both target cases are now correct with and without a schema, and the PIVOT variants are unchanged. One new failure remains: the schema-less real-table case `SELECT u.v FROM t UNPIVOT(...) AS u`. It was already wrong before (it emitted `t.u.v`), but now it raises `Unknown column: u`. Without a schema, `source_columns` is empty, and my pivot step turns that empty list into `[v, m]`, which makes the existing "skip when unknown" check reject `u`. I'll only apply the pivot when the source's columns are known.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            source = scope.sources[column_table]\n            if isinstance(source, exp.Table) and (\n                pivot := seq_get(source.args.get(\"pivots\") or [], 0)\n            ):", "new_string": "            source = scope.sources[column_table]\n            if (\n                source_columns\n                and isinstance(source, exp.Table)\n                and (pivot := seq_get(source.args.get(\"pivots\") or [], 0))\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Next I'll add regression coverage. I'll look at how the existing UNPIVOT fixture is written so the new cases match its format.
[tool_use Bash] {"command": "grep -rn \"UNPIVOT\" tests/fixtures/optimizer/*.sql | head; sed -n 630,650p tests/test_optimizer.py; grep -n \"qualify_columns.sql\" tests/test_optimizer.py", "description": "Find existing UNPIVOT tests and fixture format"}
[tool_result] tests/fixtures/optimizer/optimizer.sql:699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
tests/fixtures/optimizer/optimizer.sql:706:UNPIVOT("SALES" FOR "MONTH" IN ("JAN", "FEB")) AS "M_SALES"
tests/fixtures/optimizer/optimizer.sql:712:SELECT * FROM (SELECT * FROM m_sales) AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) AS unpiv(a, b, c, d);
tests/fixtures/optimizer/optimizer.sql:726:UNPIVOT("sales" FOR "mon
…[1371 chars elided]…
ect="bigquery",
                ),
                dialect="bigquery",
            ).sql(dialect="bigquery"),
            "WITH `produce` AS (SELECT 'Kale' AS `product`, 51 AS `q1`, 23 AS `q2`) "
            "SELECT `produce`.`product` AS `product`, `produce`.`quarter` AS `quarter`, "
            "`produce`.`sales` AS `sales` FROM `produce` AS `produce` "
            "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`",
        )

    def test_validate_columns(self):
[assistant] The existing BigQuery UNPIVOT assertion lives in `tests/test_optimizer.py`. I'll add a sibling test next to it covering the two reported queries plus the aliased star, with and without a schema.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "old_string": "            \"`produce`.`sales` AS `sales` FROM `produce` AS `produce` \"\n            \"UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`\",\n        )\n\n    def test_validate_colum
…[2092 chars elided]…
             ).sql(dialect=\"bigquery\"),\n                    \"WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) \"\n                    \"SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` \"\n                    \"UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`\",\n                )\n\n    def test_validate_columns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the optimizer test file through the project's harness, then format and lint the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py tests/test_optimizer.py", "description": "Run optimizer test file via harness suite runner", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-00:38:42 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  77489       00:05 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/test_optimizer.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-2709aaeb7c.log
ELAPSED: 15s
SUMMARY: 78 passed, 3707 subtests passed in 14.81s
EXIT: 0
[assistant] The optimizer file passes (78 tests, `EXIT: 0`). Next, the project's formatter and linter on the two changed files, because my test lines are long.
[tool_use Bash] {"command": "V=<work>/env-sqlglot/bin; ($V/ruff --version || which ruff) 2>&1; $V/ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1; $V/ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1 | tail -5", "description": "Check formatting and lint on changed files"}
[tool_result] ruff 0.15.6
Would reformat: tests/test_optimizer.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "V=<work>/env-sqlglot/bin; git stash list >/dev/null; $V/ruff format tests/test_optimizer.py && git diff --stat && $V/ruff format --check tests/test_optimizer.py sqlglot/optimizer/qualify_columns.py && git diff -- tests/test_optimizer.py | head -20", "description": "Apply ruff formatting to the test file and verify diff size"}
[tool_result] 1 file reformatted
 sqlglot/optimizer/qualify_columns.py | 31 ++++++++++++++++++++++-
 tests/test_optimizer.py              | 48 ++++++++++++++++++++++++++++++++++++
 2 files changed, 78 insertions(+), 1 deletion(-)
2 files already formatted
diff --git a/tests/test_optimizer.py b/tests/test_optimizer.py
index ce908f20d..51272cc1d 100644
--- a/tests/test_optimizer.py
+++ b/tests/test_optimizer.py
@@ -647,6 +647,54 @@ class TestOptimizer(unittest.TestCase):
             "UNPIVOT(`sales` FOR `quart
…[223 chars elided]…
", "feb": "INT"}}
+
+        for schema_arg in (None, schema):
+            with self.subTest(schema=schema_arg):
+                self.assertEqual(
+                    optimizer.qualify.qualify(
+                        parse_one(
+                            f"{cte}SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))",
+                            dialect="bigquery",
+                        ),
[This command modified 1 file you've previously read: tests/test_optimizer.py. Call Read before editing.]
[assistant] Formatting is clean. Now the full suite, run once after the last edit, as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness runner", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-00:39:05 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  77489       00:28 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-2709aaeb7c.log
ELAPSED: 62s
SUMMARY: 1093 passed, 17866 subtests passed in 61.46s (0:01:01)
EXIT: 0
[assistant] The full suite passes after the last edit: `1093 passed`, `EXIT: 0`. Last, I'll confirm the new test actually fails on the unmodified code, so it's a real regression test.
[tool_use Bash] {"command": "cp tests/test_optimizer.py /tmp/headcopy/tests_new_test_optimizer.py 2>/dev/null; mkdir -p /tmp/headcopy/tests && git archive HEAD tests | tar -x -C /tmp/headcopy && cp tests/test_optimizer.py /tmp/headcopy/tests/test_optimizer.py && cd /tmp/headcopy && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unpivot_cte 2>&1 | grep -E \"passed|failed|Unknown column|FAILED\" | tail -5", "description": "Confirm new test fails against unmodified HEAD code"}
[tool_result] >                   raise OptimizeError(f"Unknown column: {column_name}")
E                   sqlglot.errors.OptimizeError: Unknown column: v
SUBFAILED(schema=None) tests/test_optimizer.py::TestOptimizer::test_unpivot_cte_source_columns
SUBFAILED(schema={'t': {'id': 'INT', 'jan': 'INT', 'feb': 'INT'}}) tests/test_optimizer.py::TestOptimizer::test_unpivot_cte_source_columns
2 failed, 1 passed, 77 deselected in 0.42s
Shell cwd was reset to ~/.cache/lithify/work/repo-55c905b0df68/20261026-200659-optimizer-un-pivot-over-cte-sour/base-1
[assistant] The new test fails on unmodified `HEAD` (`Unknown column: v`, both schema variants) and passes with the fix. I'll review the final source diff and clean up my scratch copy.
[tool_use Bash] {"command": "rm -rf /tmp/headcopy && git diff -- sqlglot/ && git status --short", "description": "Show final source diff and status"}
[tool_result] diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..805f635c7 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -15,7 +15,7 @@ from sqlglot.schema import Schema, ensure_schema
 
 if t.TYPE_CHECKING:
     from sqlglot._typing import E
-    from collections.abc import Iterator, Iterable
+    from collections.abc import Iterator, Iterable, Sequence
 
 
 def qualify_columns(
@@ -197,6 +197,28 @@ def _
…[1178 chars elided]…
s(column_table)
+            source = scope.sources[column_table]
+            if (
+                source_columns
+                and isinstance(source, exp.Table)
+                and (pivot := seq_get(source.args.get("pivots") or [], 0))
+            ):
+                source_columns = _pivot_columns(pivot, source_columns)
             if (
                 not allow_partial_qualification
                 and source_columns
 M sqlglot/optimizer/qualify_columns.py
 M tests/test_optimizer.py
[assistant] The aliased UNPIVOT over a CTE now qualifies correctly, with and without a schema. The full suite passes after the last edit: `SUMMARY: 1093 passed, 17866 subtests passed in 61.46s`, `EXIT: 0`. I haven't committed anything.

**What was broken:** `SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u` raised `Unknown column: v`. The check in `_qualify_columns` looks up `u`'s columns from the CTE (`id, jan, feb`) and never adds the pivot's output columns (`m`, `v`).

**The fix** (`sqlglot/optimizer/qualify_columns.py`): when an explicitly qualified source is a pivoted table, the check now adds t
…[786 chars elided]…
uldn't reproduce the `SELECT *` failure. On `HEAD`, the unaliased `SELECT * FROM c UNPIVOT(...)` already expands correctly to `id, m, v` in both schema modes, so the test covers it as a regression guard only.
- The aliased-pivot failure is the one that reproduced.

**Not fixed:** Without a schema, `SELECT u.v FROM t UNPIVOT(...) AS u` on a real table still produces `t.u.v`, which is wrong. It was wrong before this change too, and the fix doesn't touch it. The alias `u` isn't registered as a scope source for non-CTE tables, which is a separate bug in `scope.py`. Say if you want it handled here.
