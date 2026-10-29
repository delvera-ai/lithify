# trajectory base-1

final message:
Fixed: `u.v` and other pivot-output references through a pivoted CTE now qualify, for both aliased and unaliased pivots. The full suite passes (1092 tests, plus 4 new fixtures), and ruff is clean. I haven't committed.

**What was actually broken:** the validation step in `_qualify_columns` checked `u.v` against the CTE's pre-pivot columns (`id, jan, feb`), so the pivot's output columns (`v`, `m`) were rejected as "Unknown column". Your first query (`SELECT * FROM c UNPIVOT(...)`) already qualified correctly in bigquery, duckdb, snowflake, and spark, with and without a schema. I couldn't reproduce the star-expansion failure you described, so if it shows up for you, I need the exact dialect or schema.

**Changes:**
- `sqlglot/optimizer/qualify_columns.py`:
  - Validation now adds the pivot's output columns to a pivoted source's columns. It skips this inside the pivot clause itself, where the pre-pivot names still apply.
  - I moved the pivot exclude/output computation into a shared `_pivot_columns` helper, so star expansion and validation use one definition.
- `tests/fixtures/optimizer/qualify_columns.sql`: four fixtures covering star and column references, aliased and unaliased, over a CTE UNPIVOT in bigquery.

**Behavior change to know about:** `SELECT c.jan FROM c UNPIVOT(v FOR m IN (jan, feb))` now raises "Unknown column: jan". `jan` is consumed by the UNPIVOT, so this is correct, but it used to pass silently.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"pivot\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify.py | head -80", "description": "Check git status and grep pivot handling in optimizer"}
[tool_result] sqlglot/optimizer/qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
sqlglot/optimizer/qualify_columns.py:124:            if scope.external_columns and not scope.is_correlated_subquery and not scope.pivots:
sqlglot/optimizer/qualify_columns.py:184:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
sqlglot/optimizer/qualify_columns.py:187:        for field in unpivot.fields
sqlglot/optimizer/qualify_columns.py:192:        for e in unpivot.
…[3250 chars elided]…
/optimizer/scope.py:483:        return self._pivots
sqlglot/optimizer/scope.py:813:                # it is pivoted, because then we get back a new table and hence a new source.
sqlglot/optimizer/scope.py:814:                pivots = expression.args.get("pivots")
sqlglot/optimizer/scope.py:815:                if pivots:
sqlglot/optimizer/scope.py:816:                    sources[pivots[0].alias] = expression
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "sed -n 600,660p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 770,900p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 470,490p sqlglot/optimizer/scope.py && echo ---- && sed -n 800,830p sqlglot/optimizer/scope.py", "description": "Read pivot-related sections of qualify_columns and scope"}
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
…[9084 chars elided]…
urce_name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
                sources[source_name] = expression

            # Make sure to not include the joins twice
            if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
[assistant] Let me reproduce both failing cases before changing anything.
[tool_use Bash] {"command": "cat > /tmp/repro_pivot.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n    \"WITH c AS (SELECT i
…[269 chars elided]…
try:\n            out = qualify(parse_one(sql, read=dialect), dialect=dialect).sql(dialect)\n        except Exception as e:\n            out = f\"ERROR {type(e).__name__}: {e}\"\n        print(f\"[{dialect}] {sql}\\n  -> {out}\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_pivot.py", "description": "Reproduce pivot-over-CTE qualification failures"}
[tool_result] [bigquery] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[bigquery] WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  -> ERROR OptimizeError: Unknown column: v
[bigquery] WITH c AS (SELECT i
…[1855 chars elided]…
wn column: V
[snowflake] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c PIVOT(SUM(jan) FOR m IN ('a','b'))
  -> ERROR OptimizeError: Ambiguous column 'M' (Line: 1, Col: 75)
[snowflake] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS x UNPIVOT(v FOR m IN (jan, feb))
  -> WITH "C" AS (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") SELECT "X"."ID" AS "ID", "X"."M" AS "M", "X"."V" AS "V" FROM "C" AS "X" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "X"
[assistant] The first case qualifies here, so the failure must depend on something else. My PIVOT case used a non-existent column `m`, so I'll fix that and add a schema to see the real behavior.
[tool_use Bash] {"command": "cat > /tmp/repro_pivot2.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\", \"m\": \"STRING\"}}\ncases = [\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n    \"WITH c AS (SELECT id, jan, fe
…[552 chars elided]…
ead=dialect), schema=sch, dialect=dialect).sql(dialect)\n            except Exception as e:\n                out = f\"ERROR {type(e).__name__}: {e}\"\n            print(f\"[{dialect} schema={sch is not None}] {sql}\\n  -> {out}\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_pivot2.py", "description": "Reproduce with valid pivot columns and schema"}
[tool_result] [bigquery schema=False] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[bigquery schema=True] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS 
…[4409 chars elided]…
jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "p"."id" AS "id", "p"."1" AS "1", "p"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "feb" IN (1, 2)) AS "p"
[duckdb schema=True] WITH c AS (SELECT id, jan, feb FROM t) SELECT p.* FROM c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS p
  -> WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "p"."id" AS "id", "p"."1" AS "1", "p"."2" AS "2" FROM "c" AS "c" PIVOT(SUM("jan") FOR "feb" IN (1, 2)) AS "p"
[assistant] Two things stand out: the aliased UNPIVOT (`u.v`) fails with "Unknown column", and the unaliased star case already qualifies here. Next I'll check how the resolver gets source columns for a pivoted source.
[tool_use Bash] {"command": "grep -n \"def get_source_columns\" -A40 sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -80; grep -n \"pivot\" sqlglot/optimizer/qualify_tables.py", "description": "Inspect resolver source column lookup and table qualification"}
[tool_result] 128:            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
129:                _set_alias(pivot, canonical_aliases)
135:                # When the name is empty, it means that we have a non-table source, e.g. a pivoted cte
138:                if pivot := seq_get(source.args.get("pivots") or [], 0):
169:                if pivot:
170:                    target_alias = source.alias if pivot.unpivot else None
171:                    _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)
173:                    # This case corresponds to a pivoted CTE, we don't want to qualify that
[tool_use Bash] {"command": "sed -n 120,185p sqlglot/optimizer/qualify_tables.py; echo ----; grep -rn \"def get_source_columns\" sqlglot/optimizer/ ; ", "description": "Read qualify_tables pivot handling and find resolver"}
[tool_result]             unnested = derived_table.unnest()
            if isinstance(unnested, exp.Table):
                joins = unnested.args.get("joins")
                unnested.set("joins", None)
                derived_table.this.replace(exp.select("*").from_(unnested.copy(), copy=False))
                derived_table.this.set("joins", joins)

            _set_alias(derived_table, canonical_aliases, scope=scope)
            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
              
…[2294 chars elided]…
              if on_qualify:
                        on_qualify(source)
            elif isinstance(source, Scope) and source.is_udtf:
                _set_alias(udtf := source.expression, canonical_aliases)

                table_alias = udtf.args["alias"]
----
sqlglot/optimizer/resolver.py:95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py:133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
[tool_use Bash] {"command": "sed -n 125,200p sqlglot/optimizer/resolver.py; echo ----; sed -n 180,200p sqlglot/optimizer/qualify_columns.py", "description": "Read resolver get_source_columns and unpivot column helper"}
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
…[3702 chars elided]…
fier]:
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

    return itertools.chain(name_columns, value_columns)


def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
[assistant] The resolver already maps a pivoted CTE reference back to the CTE scope, but it returns only the pre-pivot columns. It never adds the pivot's output columns (`v`, `m`). I'll look at the rest of that function and test a few more variants to pin the exact failure set.
[tool_use Bash] {"command": "sed -n 200,225p sqlglot/optimizer/resolver.py; cat > /tmp/repro_pivot3.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS u UNPIVOT(v FOR m IN (jan, feb))\",\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR 
…[553 chars elided]…
:\n            out = qualify(parse_one(sql, read=dialect), dialect=dialect).sql(dialect)\n        except Exception as e:\n            out = f\"ERROR {type(e).__name__}: {e}\"\n        print(f\"[{dialect}] {sql}\\n  -> {out}\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_pivot3.py", "description": "Test more pivot-over-CTE variants across dialects"}
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
…[7225 chars elided]…
[spark] WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v, u.m FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  -> ERROR OptimizeError: Unknown column: v
[spark] WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan AS 'a', feb AS 'b'))
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM (SELECT * FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`jan` AS a, `feb` AS b))) AS `c`
[assistant] The failure set is clearer now. Any reference to a pivot's output column through an explicit pivot alias (`u.v`, `u.m`) raises "Unknown column". Star expansion over an aliased pivot is correct only because `expand_stars` applies the pivot transform itself. The root cause is that the resolver reports only pre-pivot CTE columns for a pivoted source, so the output columns never reach validation or `get_table`.

Before I change anything, I'll check where the pivot helpers and related tests live.
[tool_use Bash] {"command": "grep -rn \"_unpivot_columns\\|alias_column_names\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -30; grep -n \"^from\\|^import\" sqlglot/optimizer/resolver.py sqlglot/optimizer/qualify_columns.py; grep -rn -i \"pivot\" tests/fixtures/optimizer/qualify_columns.sql tests/fixtures/optimizer/*.sql | wc -l; ls tests/fixtures/optimizer | head -50", "description": "Find pivot helper usages, imports, and related test fixtures"}
[tool_result] sqlglot/parser.py:5020:    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
sqlglot/parser.py:5047:        into = self._parse_unpivot_columns()
sqlglot/optimizer/qualify_columns.py:184:def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
sqlglot/optimizer/qualify_columns.py:789:    if isinstance(pivot, exp.Pivot) and not pivot.alias_column_names:
sqlglot/optimizer/qualify_columns.py:791:            pivot_output_columns = [c.output_name for c in _unpivot_columns(piv
…[3718 chars elided]…
ql
annotate_types.sql
canonicalize.sql
eliminate_ctes.sql
eliminate_joins.sql
eliminate_subqueries.sql
isolate_table_selects.sql
merge_subqueries.sql
normalize.sql
normalize_identifiers.sql
optimize_joins.sql
optimizer.sql
pushdown_cte_alias_columns.sql
pushdown_predicates.sql
pushdown_projections.sql
qualify_columns.sql
qualify_columns__invalid.sql
qualify_columns__with_invisible.sql
qualify_columns_ddl.sql
qualify_tables.sql
quote_identifiers.sql
simplify.sql
tpc-ds
tpc-h
unnest_subqueries.sql
[assistant] Before editing, I'll record the baseline test state so I can tell regressions apart from pre-existing failures.
[tool_use Bash] {"command": "time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite for baseline", "timeout": 900000}
[tool_result] ............................................................................................................... [ 32%]
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
................. [ 42%]
........................................................................................................... [ 52%]
......................................................... [ 57%]
........ [ 57%]
......................................
…[239 chars elided]…
................................................................................. [ 88%]
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 50.76s
<work>/env-sqlglot/bin/python -m   118.97s user 14.75s system 261% cpu 51.165 total
tail -15  0.00s user 0.00s system 0% cpu 51.165 total
[assistant] Baseline is clean: 1092 passed, 17864 subtests. Here's my plan.

The failing path is the validation in `_qualify_columns`. It checks `u.v` against the pre-pivot source columns. I'll apply the pivot's output transform there, for columns outside the pivot clause. I'll leave the resolver and star expansion alone, since star expansion already works and changing the resolver would double-apply the transform there. I'll factor the pivot exclude/output computation out of `expand_stars` so both paths share one definition.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    pivot_output_columns = None\n    pivot_exclude_columns: set[str] = set()\n\n    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n    if isinstance(pivot, exp.Pivot) and not pivot.a
…[641 chars elided]…
              pivot_output_columns = [c.alias_or_name for c in pivot.expressions]\n", "new_string": "    pivot_output_columns = None\n    pivot_exclude_columns: set[str] = set()\n\n    pivot = t.cast(t.Optional[exp.Pivot], seq_get(scope.pivots, 0))\n    if isinstance(pivot, exp.Pivot) and not pivot.alias_column_names:\n        pivot_exclude_columns, pivot_output_columns = _pivot_columns(pivot)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Now I'll add the shared helpers next to `_unpivot_columns` and use them in the validation loop.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pop_table_column_aliases(", "new_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _pivot_columns(pivot: exp.
…[305 chars elided]…
_name for e in field.expressions for c in e.find_all(exp.Column))\n\n        return exclude, [c.output_name for c in _unpivot_columns(pivot)]\n\n    exclude = set(c.output_name for c in pivot.find_all(exp.Column))\n    outputs = [c.output_name for c in pivot.args.get(\"columns\", [])]\n    return exclude, outputs or [c.alias_or_name for c in pivot.expressions]\n\n\ndef _pop_table_column_aliases("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "        if column_table and column_table in scope.sources:\n            source_columns = resolver.get_source_columns(column_table)\n            if (", "new_string": "        if column_table and column
…[177 chars elided]…
ide the pivot clause itself\n            pivot = next((p for p in scope.pivots if p.alias == column_table), None)\n            if pivot and source_columns and not pivot.alias_column_names and not column.find_ancestor(exp.Pivot):\n                exclude, outputs = _pivot_columns(pivot)\n                source_columns = [c for c in source_columns if c not in exclude] + outputs\n\n            if ("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Next I'll re-run the reproduction scripts against the change.
[tool_use Bash] {"command": "cat >> /tmp/repro_pivot3.py <<'EOF'\nprint(\"=== extra\")\nfor dialect in [\"bigquery\", \"duckdb\"]:\n    for sql in [\n        \"WITH c AS (SELECT id, jan, feb FROM t) SELECT c.v FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n        \"WITH c AS (SELECT id, jan, feb FROM t) SELECT c.jan FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n        \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.ja
…[356 chars elided]…
e}\"\n        print(f\"[{dialect}] {sql}\\n  -> {out}\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_pivot3.py 2>&1 | grep -A1 \"u.v\\|u.m\\|c.v\\|c.jan\\|u.jan\\|=== \\|p.id\\|u.\\*\\|\\[bigquery\\] WITH c AS (SELECT id, jan, feb FROM t) SELECT \\* FROM c UNPIVOT(v FOR m IN (jan AS\" | head -80", "description": "Re-run pivot repros after the fix"}
[tool_result] [bigquery] WITH c AS (SELECT id, jan, feb FROM t) SELECT u.* FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
--
[bigquery] WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v, u.m FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  -> WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `ja
…[3732 chars elided]…
 -> ERROR OptimizeError: Unknown column: jan
[duckdb] WITH c AS (SELECT id, jan, feb FROM t) SELECT u.jan FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
  -> ERROR OptimizeError: Unknown column: jan
[duckdb] WITH c AS (SELECT id, jan, feb FROM t) SELECT p.id, p.`1` FROM c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS p
  -> ERROR ParseError: Invalid expression / Unexpected token. Line 1, Col: 56.
  WITH c AS (SELECT id, jan, feb FROM t) SELECT p.id, p.`[4m1[0m` FROM c PIVOT(SUM(jan) FOR feb IN (1, 2)) AS p
[assistant] The reported cases now resolve. `u.v`, `u.m`, and `c.v` qualify correctly in both aliased and unaliased forms. `c.jan` now raises, which is correct because UNPIVOT consumes `jan`. The duckdb ParseError is a backtick typo in my own probe, not a code issue. Next, the full suite and the linter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; (ruff --version && ruff check sqlglot/optimizer/qualify_columns.py && ruff format --check sqlglot/optimizer/qualify_columns.py) 2>&1 | tail -10", "description": "Run full test suite and ruff checks", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
................................................................................................ [ 20%]
..................... [ 22%]
............................................................................................................... [ 32%]
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................
…[444 chars elided]…
... [ 76%]
............................................. [ 80%]
....................................................................................... [ 88%]
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 49.01s
ruff 0.15.6
All checks passed!
Would reformat: sqlglot/optimizer/qualify_columns.py
1 file would be reformatted
[assistant] All 1092 tests still pass. Ruff wants a reformat, so I'll apply it and confirm it only touches my lines.
[tool_use Bash] {"command": "ruff format sqlglot/optimizer/qualify_columns.py && ruff check sqlglot/optimizer/qualify_columns.py && git diff", "description": "Apply ruff format and show resulting diff"}
[tool_result] 1 file reformatted
All checks passed!
diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..8b3112efb 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -197,6 +197,23 @@ def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
     return itertools.chain(name_columns, value_columns)
 
 
+def _pivot_columns(pivot: exp.Pivot) -> tuple[set[str], list[str]]:
+    """Returns the source colum
…[2273 chars elided]…
lumns = [c.output_name for c in pivot.args.get("columns", [])]
-            if not pivot_output_columns:
-                pivot_output_columns = [c.alias_or_name for c in pivot.expressions]
+        pivot_exclude_columns, pivot_output_columns = _pivot_columns(pivot)
 
     if dialect.SUPPORTS_STRUCT_STAR_EXPANSION and any(
         isinstance(col, exp.Dot) for col in scope.stars
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] The diff is as intended. The "changed on disk" note is just the `ruff format` I ran. Next I'll add regression tests next to the existing pivot fixtures.
[tool_use Bash] {"command": "grep -n -i -B3 -A3 \"pivot\" tests/fixtures/optimizer/qualify_columns.sql | head -150", "description": "Show existing pivot fixtures in qualify_columns tests"}
[tool_result] 266-
267-# execute: false
268-# dialect: snowflake
269:SELECT * FROM quarterly_sales PIVOT(SUM(amount) FOR quarter IN (ANY ORDER BY quarter)) ORDER BY empid;
270:SELECT * FROM QUARTERLY_SALES AS QUARTERLY_SALES PIVOT(SUM(QUARTERLY_SALES.AMOUNT) FOR QUARTERLY_SALES.QUARTER IN (ANY ORDER BY QUARTER)) AS _0 ORDER BY _0.EMPID;
271-
272-# execute: false
273-SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x) AS x FROM t;
--
590-SELECT * FROM VALUES (1, 2, 3);
591-SELECT _0.c1 AS c1 FROM VALUES ((1)
…[1151 chars elided]…
_total, _0.us_2000_seattle_count AS us_2000_seattle_count, _0.us_2010_amsterdam_total AS us_2010_amsterdam_total, _0.us_2010_amsterdam_count AS us_2010_amsterdam_count, _0.us_2010_seattle_total AS us_2010_seattle_total, _0.us_2010_seattle_count AS us_2010_seattle_count FROM cities AS cities PIVOT(SUM(population) AS total, COUNT(population) AS count FOR country IN ('nl', 'us') year IN (2000, 2010) name IN ('amsterdam', 'seattle')) AS _0;
597-
598---------------------------------------
599--- CTEs
[tool_use Bash] {"command": "grep -n \"qualify_columns.sql\" -A25 tests/test_optimizer.py | head -60; sed -n 1,12p tests/fixtures/optimizer/qualify_columns.sql; sed -n 596,600p tests/fixtures/optimizer/qualify_columns.sql | cut -c1-120", "description": "Inspect how qualify_columns fixtures are executed and their format"}
[tool_result] --------------------------------------
-- Qualify columns
--------------------------------------
SELECT a FROM x;
SELECT x.a AS a FROM x AS x;

SELECT "a" FROM x;
SELECT x."a" AS a FROM x AS x;

# execute: false
SELECT a FROM zz GROUP BY a ORDER BY a;
SELECT zz.a AS a FROM zz AS zz GROUP BY zz.a ORDER BY a;
WITH cities AS (SELECT t.country AS country, t.name AS name, t.year AS year, t.population AS population FROM (VALUES ('n

--------------------------------------
-- CTEs
--------------------------------------
[tool_use Bash] {"command": "grep -rn \"qualify_columns\" tests/*.py | head; grep -n \"def check_file\" -A40 tests/helpers.py | head -70", "description": "Find the fixture runner for qualify_columns SQL files"}
[tool_result] tests/test_optimizer.py:30:def qualify_columns(expression, validate_qualify_columns=True, **kwargs):
tests/test_optimizer.py:34:        validate_qualify_columns=validate_qualify_columns,
tests/test_optimizer.py:43:    expression = optimizer.qualify_columns.qualify_columns(expression, infer_schema=True, **kwargs)
tests/test_optimizer.py:67:    optimizer.qualify_columns.pushdown_cte_alias_columns(build_scope(expression))
tests/test_optimizer.py:169:                validate_qualify_columns = meta.get("validate_qualify_columns")
tests/test_optimizer.py:177:                if validate_qualify_columns is not None:
tests/test_optimizer.py:178:                    func_kwargs["validate_qualify_columns"] = string_to_bool(
tests/test_optimizer.py:179:                        validate_qualify_columns
tests/test_optimizer.py:252:            qualify_columns=False,
tests/test_optimizer.py:341:    def test_qualify_columns(self, logger):
[assistant] The fixture runner calls `qualify_columns` with `infer_schema=True`. I'll generate the expected outputs with that same call, check them by hand, and then add the fixtures.
[tool_use Bash] {"command": "cat > /tmp/gen_fixtures.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import qualify_columns\ncases = [\n    (\"bigquery\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));\"),\n    (\"bigquery\", \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) A
…[185 chars elided]…
SELECT * FROM c AS u UNPIVOT(v FOR m IN (jan, feb));\"),\n]\nfor dialect, sql in cases:\n    e = qualify_columns.qualify_columns(parse_one(sql, read=dialect), infer_schema=True)\n    print(sql); print(e.sql(dialect)); print()\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/gen_fixtures.py", "description": "Generate expected qualify outputs for new fixtures"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/gen_fixtures.py", line 12, in <module>
    e = qualify_columns.qualify_columns(parse_one(sql, read=dialect), infer_schema=True)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: qualify_columns() missing 1 required positional argument: 'schema'
[tool_use Bash] {"command": "sed -i 's/qualify_columns.qualify_columns(parse_one(sql, read=dialect), infer_schema=True)/qualify_columns.qualify_columns(parse_one(sql, read=dialect), schema=None, infer_schema=True)/' /tmp/gen_fixtures.py && <work>/env-sqlglot/bin/python -I /tmp/gen_fixtures.py", "description": "Generate expected outputs with schema argument"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/gen_fixtures.py
": extra characters at the end of g command
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport pathlib\np = pathlib.Path('/tmp/gen_fixtures.py')\np.write_text(p.read_text().replace('parse_one(sql, read=dialect), infer_schema=True', 'parse_one(sql, read=dialect), schema=None, infer_schema=True'))\n\" && <work>/env-sqlglot/bin/python -I /tmp/gen_fixtures.py", "description": "Patch generator script and produce fixture outputs"}
[tool_result ERROR] Exit code 1
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb));
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t) SELECT ``.id AS id, ``.m AS m, ``.v AS v FROM c UNPIVOT(v FOR m IN (c.jan, c.feb))

WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u;
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t) SELECT u.v AS v FROM c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS u

Traceback (most recent call l
…[259 chars elided]…
^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 644, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: v
[assistant] Calling `qualify_columns` directly skips `qualify_tables`, which assigns the pivot alias, so this probe is not representative. I'll check what the test wrapper actually runs.
[tool_use Bash] {"command": "sed -n 28,50p tests/test_optimizer.py", "description": "Read the qualify_columns test wrapper"}
[tool_result] def qualify_columns(expression, validate_qualify_columns=True, **kwargs):
    expression = optimizer.qualify.qualify(
        expression,
        infer_schema=True,
        validate_qualify_columns=validate_qualify_columns,
        identify=False,
        **kwargs,
    )
    return expression


def pushdown_projections(expression, **kwargs):
    expression = optimizer.qualify_tables.qualify_tables(expression)
    expression = optimizer.qualify_columns.qualify_columns(expression, infer_schema=True, **kwargs)
    expression = optimizer.pushdown_projections.pushdown_projections(expression, **kwargs)
    return expression


def normalize(expression, **kwargs):
    schema = kwargs.get("schema")
[assistant] The wrapper runs the full `qualify` pipeline with `identify=False`. I'll regenerate the outputs that way.
[tool_use Bash] {"command": "cat > /tmp/gen_fixtures2.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))\",\n    \"WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n    \"WITH c AS (SELECT
…[342 chars elided]…
c UNPIVOT(v FOR m IN (jan, feb)) AS u\",\n]\nfor sql in cases:\n    e = qualify(parse_one(sql, read=\"bigquery\"), dialect=\"bigquery\", identify=False, infer_schema=True)\n    print(sql); print(e.sql(\"bigquery\")); print()\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/gen_fixtures2.py", "description": "Generate fixture outputs via full qualify pipeline"}
[tool_result ERROR] Exit code 1
WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT c.id AS id, c.m AS m, c.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c

WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u
WITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT u.v AS v FROM c AS c UNPIVOT(v FOR m IN (c.jan, c.feb)) AS u

WITH c AS
…[1265 chars elided]…

  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 644, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: jan
[assistant] The last probe raised the expected error. `u.jan` is consumed by the UNPIVOT, so it should not resolve, and I won't add it as a positive fixture. The other outputs are correct. I'll add those four as fixtures after the existing PIVOT block.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/tests/fixtures/optimizer/qualify_columns.sql", "old_string": "WITH cities AS (SELECT t.country AS country, t.name AS name, t.year AS year, t.population AS population FROM (VALUES ('nl', 'amsterdam', 2000, 1005)) AS t(country, name, year, population)) SEL
…[3242 chars elided]…
UNPIVOT(v FOR m IN (c.jan, c.feb)) AS c;\n\n# title: Star expansion over an aliased UNPIVOT of a CTE\n# execute: false\n# dialect: bigquery\nWITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c AS u UNPIVOT(v FOR m IN (jan, feb));\nWITH c AS (SELECT t.id AS id, t.jan AS jan, t.feb AS feb FROM t AS t) SELECT u.id AS id, u.m AS m, u.v AS v FROM c AS u UNPIVOT(v FOR m IN (u.jan, u.feb)) AS u;\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-172058-optimizer-un-pivot-over-cte-sour/base-1/tests/fixtures/optimizer/qualify_columns.sql has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -30", "description": "Run optimizer tests including new fixtures", "timeout": 600000}
[tool_result] ...... [  7%]
.......................................................................                               [100%]
77 passed, 3709 subtests passed in 15.61s
[assistant] The optimizer tests pass with the new fixtures. Last step is the full suite plus lint on the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; ruff check sqlglot/optimizer/qualify_columns.py && ruff format --check sqlglot/optimizer/qualify_columns.py; git status --short", "description": "Run full suite, lint, and show changed files", "timeout": 900000}
[tool_result] ............................................................................... [ 87%]
.....................................................................................................................................                                                 [100%]
1092 passed, 17868 subtests passed in 56.60s
All checks passed!
1 file already formatted
 M sqlglot/optimizer/qualify_columns.py
 M tests/fixtures/optimizer/qualify_columns.sql
[assistant] Fixed: `u.v` and other pivot-output references through a pivoted CTE now qualify, for both aliased and unaliased pivots. The full suite passes (1092 tests, plus 4 new fixtures), and ruff is clean. I haven't committed.

**What was actually broken:** the validation step in `_qualify_columns` checked `u.v` against the CTE's pre-pivot columns (`id, jan, feb`), so the pivot's output columns (`v`, `m`) were rejected as "Unknown column". Your first query (`SELECT * FROM c UNPIVOT(...)`) already qualified correctly in bigquery, duckdb, snowflake, and spark, with and without a schema. I couldn't reprod
…[235 chars elided]…
's columns. It skips this inside the pivot clause itself, where the pre-pivot names still apply.
  - I moved the pivot exclude/output computation into a shared `_pivot_columns` helper, so star expansion and validation use one definition.
- `tests/fixtures/optimizer/qualify_columns.sql`: four fixtures covering star and column references, aliased and unaliased, over a CTE UNPIVOT in bigquery.

**Behavior change to know about:** `SELECT c.jan FROM c UNPIVOT(v FOR m IN (jan, feb))` now raises "Unknown column: jan". `jan` is consumed by the UNPIVOT, so this is correct, but it used to pass silently.
