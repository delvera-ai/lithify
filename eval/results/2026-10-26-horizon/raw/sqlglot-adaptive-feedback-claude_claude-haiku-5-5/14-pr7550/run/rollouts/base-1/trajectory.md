# trajectory base-1

final message:
`SELECT * FROM cte UNPIVOT(...)` now qualifies in BigQuery, DuckDB, Snowflake and Spark. The full suite passes after my last edit: `SUMMARY: 1092 passed, 17866 subtests passed in 59.31s`, `EXIT: 0`. I haven't committed anything.

**Root cause:** `sqlglot/optimizer/scope.py` registered a pivoted CTE reference as the raw `Table` node. The outer query then had no CTE columns to resolve against, so `jan` and `feb` in the `IN (...)` list came out as "Ambiguous column". Derived-table pivots already work because they register the subquery's `Scope`.

**Changes:**
- `sqlglot/optimizer/scope.py`: a pivoted CTE source now maps to the CTE's `Scope`, matching the derived-table path.
- `sqlglot/optimizer/qualify_tables.py`: the scope change skipped the pivot aliasing that used to happen in the `Table` branch. Unaliased pivots (`FROM c UNPIVOT(...)`) ended up with an empty alias. The loop over `scope.tables` now aliases a pivoted CTE's pivot, taking the table's alias for UNPIVOT as the old code did.
- `tests/fixtures/optimizer/optimizer.sql`: one new fixture for `WITH c AS (...) SELECT * FROM c UNPIVOT(sales FOR month IN (jan, feb))`. I added it and did not edit existing fixtures.

**Verification:**
- The repro, which failed before the change, now qualifies in all four dialects.
- The aliased form `UNPIVOT(...) AS p` works too.
- A PIVOT over a CTE, which the scope change also touches, expands `SELECT *` to `_0.id, _0.a, _0.b`, which is correct.
- The new fixture passes in `tests/test_optimizer.py`.
- Ruff check and format pass on the changed files.

Output for the example, with the value and name columns left unqualified and the `IN` items qualified to `c`:
```sql
WITH "c" AS (SELECT "m_sales"."empid" ... FROM "m_sales" AS "m_sales")
SELECT "c"."empid" AS "empid", "c"."month" AS "month", "c"."sales" AS "sales"
FROM "c" AS "c" UNPIVOT("sales" FOR "month" IN ("c"."jan", "c"."feb")) AS "c"
```

I did not add a dialect-specific test. The fixture uses the default dialect, and the four-dialect check was done by hand.

## events
[tool_use Bash] {"command": "git status --short | head && ls .lithify/harness 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -30; grep -rn -i \"unpivot\" sqlglot/optimizer/*.py sqlglot/expressions/*.py | head -50", "description": "Check repo state and find UNPIVOT references"}
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
sqlglot/optimizer/qualify_tables.py:170:                    target_alias = source.alias if pivot.unpivot else None
sqlglot/optimizer/qualify_columns.py:54:        - Currently only handles a single PIVOT or UNPIVOT operator
sqlglot/optimizer/qualify_columns.py:141:            if unqualified_columns and scope.pivots and scope.pivots[0].unpivot:
sqlglot/optimizer/qualify_columns.py:142:                # New columns produced by the UN
…[715 chars elided]…
ns for c in e.find_all(exp.Column))
sqlglot/optimizer/qualify_columns.py:792:        if pivot.unpivot:
sqlglot/optimizer/qualify_columns.py:793:            pivot_output_columns = [c.output_name for c in _unpivot_columns(pivot)]
sqlglot/expressions/query.py:1747:        "unpivot": False,
sqlglot/expressions/query.py:1758:    def unpivot(self) -> bool:
sqlglot/expressions/query.py:1759:        return bool(self.args.get("unpivot"))
sqlglot/expressions/query.py:1766:class UnpivotColumns(Expression):
[tool_use Bash] {"command": "cat .lithify/memory.md; sed -n 100,210p sqlglot/optimizer/qualify_columns.py; sed -n 760,830p sqlglot/optimizer/qualify_columns.py", "description": "Read memory notes and relevant qualify_columns code"}
[tool_result] cat: .lithify/memory.md: No such file or directory
                    pseudocolumns,
                    annotator,
                )
            qualify_outputs(scope)

        _expand_group_by(scope, dialect)

        # DISTINCT ON and ORDER BY follow the same rules (tested in DuckDB, Postgres, ClickHouse)
        # https://www.postgresql.org/docs/current/sql-select.html#SQL-DISTINCT
        _expand_order_by_and_distinct_on(scope, resolver)

        if dialect.ANNOTATE_ALL_SCOPES:
           
…[6126 chars elided]…
urces)
            _add_except_columns(expression, tables, except_columns)
            _add_replace_columns(expression, tables, replace_columns)
            _add_rename_columns(expression, tables, rename_columns)
        elif expression.is_star:
            if isinstance(expression, exp.Column):
                tables.append(expression.table)
                _add_except_columns(expression.this, tables, except_columns)
                _add_replace_columns(expression.this, tables, replace_columns)
[assistant] Let me reproduce the bug first, with the dialect's test file as a baseline.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && cat > /tmp/repro_unpivot.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_columns import validate_qualify_columns\nfrom sqlglot.schema import MappingSchema\nschema 
…[266 chars elided]…
 FROM (SELECT id, jan, feb FROM t) UNPIVOT(v FOR m IN (jan, feb))\",\n    ]:\n        try:\n            out = qualify(sqlglot.parse_one(sql, read=d), schema=schema, dialect=d)\n            print(d, \"OK \", out.sql(d))\n        except Exception as e:\n            print(d, \"ERR\", type(e).__name__, e)\nEOF\n$PY -I /tmp/repro_unpivot.py", "description": "Reproduce UNPIVOT over CTE qualify failure"}
[tool_result ERROR] Exit code 1
<work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "/tmp/repro_unpivot.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_unpivot.py", "description": "Run repro with repo on PYTHONPATH"}
[tool_result] bigquery ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
bigquery OK  SELECT `_1`.`id` AS `id`, `_1`.`m` AS `m`, `_1`.`v` AS `v` FROM (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) AS `_0` UNPIVOT(`v` FOR `m` IN (`_0`.`jan`, `_0`.`feb`)) AS `_1`
duckdb ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
duckdb OK  SELECT "_1"."id" AS "id", "_1"."m" AS "m", "_1"."v" AS "v" FROM (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" 
…[149 chars elided]…
ke OK  SELECT "_1"."ID" AS "ID", "_1"."M" AS "M", "_1"."V" AS "V" FROM (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") AS "_0" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "_1"
spark ERR OptimizeError Ambiguous column 'jan' (Line: 1, Col: 78)
spark OK  SELECT `_1`.`id` AS `id`, `_1`.`m` AS `m`, `_1`.`v` AS `v` FROM (SELECT * FROM (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) AS `_0` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))) AS `_1`
[tool_use Bash] {"command": "sed -n 140,200p sqlglot/optimizer/qualify_tables.py; grep -n \"pivot\" sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -60", "description": "Inspect qualify_tables pivot handling and scope pivots"}
[tool_result]                 table_this = source.this
                table_alias = source.args.get("alias")
                function_columns: Sequence[str | exp.Identifier | exp.ColumnDef] | None = None
                if isinstance(table_this, exp.Func):
                    if not table_alias:
                        function_columns = ensure_list(
                            dialect.DEFAULT_FUNCTIONS_COLUMN_NAMES.get(type(table_this))
                        )
                    elif columns := table_ali
…[6171 chars elided]…
s]
sqlglot/optimizer/qualify_columns.py:872:                    pivot_columns.extend(pivot_output_columns)
sqlglot/optimizer/qualify_columns.py:874:                    pivot_columns = pivot.alias_column_names
sqlglot/optimizer/qualify_columns.py:876:                if pivot_columns:
sqlglot/optimizer/qualify_columns.py:878:                        alias(exp.column(name, table=pivot.alias), name, copy=False)
sqlglot/optimizer/qualify_columns.py:879:                        for name in pivot_columns
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/dbg.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.qualify_columns import qualify_columns\nfrom sqlglot.opti
…[325 chars elided]…
e = qualify_tables(e, dialect=\"duckdb\")\nfor s in traverse_scope(e):\n    print(type(s.expression).__name__, list(s.sources), [type(x).__name__ for x in s.sources.values()], \"pivots\", len(s.pivots), \"unq\", [c.sql() for c in s.unqualified_columns], \"ext\", [c.sql() for c in s.external_columns])\nEOF\nPYTHONPATH=$PWD $PY /tmp/dbg.py", "description": "Debug scope sources for CTE unpivot case"}
[tool_result] Select ['t'] ['Table'] pivots 0 unq ['id', 'jan', 'feb'] ext ['id', 'jan', 'feb']
Select ['c'] ['Table'] pivots 1 unq ['v', 'm', 'jan', 'feb'] ext ['v', 'm', 'jan', 'feb']
[tool_use Bash] {"command": "sed -n 395,420p sqlglot/optimizer/scope.py; echo ----; sed -n 795,830p sqlglot/optimizer/scope.py", "description": "Read scope.py source registration for pivoted tables"}
[tool_result]         return self._selected_sources

    @property
    def references(self) -> list[tuple[str, exp.Selectable]]:
        if self._references is None:
            self._references = []

            for table in self.tables:
                self._references.append((table.alias_or_name, table))
            for _expr in itertools.chain(self.derived_tables, self.udtfs):
                # TODO (mypyc): rebind to exp.Expr to avoid DerivedTable trait vtable dispatch
                expression: exp.Exp
…[1434 chars elided]…
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
[tool_use Bash] {"command": "sed -n 420,450p sqlglot/optimizer/scope.py; echo ----; sed -n 830,850p sqlglot/optimizer/scope.py; echo ----; grep -n \"def _get_source_alias\" -A12 sqlglot/optimizer/scope.py", "description": "Read scope source registration for derived tables"}
[tool_result]         """
        Columns that appear to reference sources in outer scopes.

        Returns:
            list[exp.Column]: Column instances that don't reference sources in the current scope.
        """
        if self._external_columns is None:
            if isinstance(self.expression, exp.SetOperation):
                left, right = self.union_scopes
                self._external_columns = left.external_columns + right.external_columns
            else:
                local_source_names 
…[1415 chars elided]…
onstructs
            expressions.append(node.this)
            expressions.extend(join.this for join in node.args.get("joins") or [])
            continue

----
1006:def _get_source_alias(expression: exp.Expr) -> str:
1007-    alias_arg = expression.args.get("alias")
1008-    alias_name = expression.alias
1009-
1010-    if not alias_name and isinstance(alias_arg, exp.TableAlias) and len(alias_arg.columns) == 1:
1011-        alias_name = alias_arg.columns[0].name
1012-
1013-    return alias_name
[assistant] The root cause is in `scope.py`: a pivoted CTE reference is registered as the raw `Table` node, not the CTE's `Scope`, so the outer query can't see `c`'s columns. Let me test pointing it at the CTE scope.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py", "old_string": "                if pivots:\n                    sources[pivots[0].alias] = expression", "new_string": "                if pivots:\n                    sources[pivots[0].alias] = scope.sources[table_name]"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/scope.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/repro_unpivot.py", "description": "Re-run repro after scope change"}
[tool_result] bigquery ERR OptimizeError Ambiguous column 'id'
bigquery OK  SELECT `_1`.`id` AS `id`, `_1`.`m` AS `m`, `_1`.`v` AS `v` FROM (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) AS `_0` UNPIVOT(`v` FOR `m` IN (`_0`.`jan`, `_0`.`feb`)) AS `_1`
duckdb ERR OptimizeError Ambiguous column 'id'
duckdb OK  SELECT "_1"."id" AS "id", "_1"."m" AS "m", "_1"."v" AS "v" FROM (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") AS "_0" UNPIVOT("v" FOR
…[69 chars elided]…
 column 'ID'
snowflake OK  SELECT "_1"."ID" AS "ID", "_1"."M" AS "M", "_1"."V" AS "V" FROM (SELECT "T"."ID" AS "ID", "T"."JAN" AS "JAN", "T"."FEB" AS "FEB" FROM "T" AS "T") AS "_0" UNPIVOT("V" FOR "M" IN ("JAN", "FEB")) AS "_1"
spark ERR OptimizeError Ambiguous column 'id'
spark OK  SELECT `_1`.`id` AS `id`, `_1`.`m` AS `m`, `_1`.`v` AS `v` FROM (SELECT * FROM (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) AS `_0` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))) AS `_1`
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/dbg2.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.scope import traverse_scope\nsql = \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, 
…[58 chars elided]…
\", \"feb\": \"INT\"}}\ne = sqlglot.parse_one(sql, read=\"duckdb\")\ntry:\n    qualify(e, schema=schema, dialect=\"duckdb\", validate_qualify_columns=False)\nexcept Exception as x:\n    print(\"ERR\", x)\nprint(e.sql(\"duckdb\"))\nEOF\nPYTHONPATH=$PWD $PY /tmp/dbg2.py; sed -n 1,30p sqlglot/optimizer/qualify_columns.py | grep -n import", "description": "Inspect qualified output without validation"}
[tool_result] WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT ""."id" AS "id", ""."m" AS "m", ""."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb"))
1:from __future__ import annotations
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
17:    from sqlglot._typing import E
18:    from collections.abc import Iterator, Iterable
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/dbg3.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify_tables import qualify_tables\nfrom sqlglot.optimizer.scope import traverse_scope\nsql = \"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v F
…[118 chars elided]…
rgs[\"expression\"].args.get(\"from\") or e.find(sqlglot.exp.From)))\np = e.find(sqlglot.exp.Pivot)\nprint(\"pivot alias:\", repr(p.alias), p.args.get(\"alias\"))\nfor s in traverse_scope(e):\n    print(list(s.sources), {k: type(v).__name__ for k, v in s.sources.items()}, [r[0] for r in s.references])\nEOF\nPYTHONPATH=$PWD $PY /tmp/dbg3.py", "description": "Check pivot alias after qualify_tables"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/dbg3.py", line 6, in <module>
    print(repr(e.args["expression"].args.get("from") or e.find(sqlglot.exp.From)))
               ~~~~~~^^^^^^^^^^^^^^
KeyError: 'expression'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; sed -i '' '/^print(repr(e.args/d' /tmp/dbg3.py; PYTHONPATH=$PWD $PY /tmp/dbg3.py", "description": "Re-run pivot alias debug script"}
[tool_result] pivot alias: '' None
['t'] {'t': 'Table'} ['t']
['c', ''] {'c': 'Scope', '': 'Scope'} ['c']
[tool_use Bash] {"command": "sed -n 95,140p sqlglot/optimizer/qualify_tables.py; grep -n \"def _set_alias\" -A30 sqlglot/optimizer/qualify_tables.py | head -45", "description": "Read qualify_tables source loop and _set_alias"}
[tool_result]             return

        alias.set("this", exp.to_identifier(new_alias_name))

        if columns:
            alias.set(
                "columns",
                [exp.to_identifier(c) if isinstance(c, str) else c.copy() for c in columns],
            )

        expression.set("alias", alias)

        if scope:
            scope.rename_source(None, new_alias_name)

    for scope in traverse_scope(expression):
        local_columns = scope.local_columns
        canonical_aliases: dict[str, s
…[1862 chars elided]…
lize and target_alias:
93-                new_alias_name = normalize_identifiers(new_alias_name, dialect=dialect).name
94-        else:
95-            return
96-
97-        alias.set("this", exp.to_identifier(new_alias_name))
98-
99-        if columns:
100-            alias.set(
101-                "columns",
102-                [exp.to_identifier(c) if isinstance(c, str) else c.copy() for c in columns],
103-            )
104-
105-        expression.set("alias", alias)
106-
107-        if scope:
[assistant] The scope change alone isn't enough: `qualify_tables` relies on the pivoted CTE being a `Table` under key `""` to assign the pivot its alias, so it now gets skipped. Let me check whether the scope logic is right when the pivot is explicitly aliased, to separate the two problems.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/dbg4.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"id\": \"INT\", \"jan\": \"INT\", \"feb\": \"INT\"}}\nfor sql in [\"WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM 
…[87 chars elided]…
FROM t) SELECT * FROM c AS c UNPIVOT(v FOR m IN (jan, feb))\"]:\n    try:\n        print(qualify(sqlglot.parse_one(sql, read=\"duckdb\"), schema=schema, dialect=\"duckdb\").sql(\"duckdb\"))\n    except Exception as x:\n        print(\"ERR\", x)\nEOF\nPYTHONPATH=$PWD $PY /tmp/dbg4.py; git stash list | head -2; git diff --stat", "description": "Test explicitly aliased pivoted CTE with scope change"}
[tool_result] WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "p"."id" AS "id", "p"."m" AS "m", "p"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "p"
ERR Ambiguous column 'id'
 sqlglot/optimizer/scope.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
[assistant] The explicitly aliased form works with the scope change; only the unaliased `FROM c AS c UNPIVOT(...)` form breaks, because the pivot's alias is still `""` when qualify_tables runs. Before I restructure, let me check how the Resolver gets columns for a `Table` source, since that determines the least invasive fix.
[tool_use Bash] {"command": "grep -n \"def get_source_columns\\|def _get_source_columns\\|isinstance(source, exp.Table)\\|isinstance(source, Scope)\\|Table\" sqlglot/optimizer/resolver.py | head -30; grep -n \"def selected_sources\" -A25 sqlglot/optimizer/scope.py | head -40", "description": "Inspect resolver source handling and selected_sources"}
[tool_result] 95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
142:            if isinstance(source, exp.Table):
144:            elif isinstance(source, Scope) and isinstance(
173:            elif isinstance(source, Scope) and isinstance(source.expression, exp.SetOperation):
378:        self, source: Scope | exp.Table, column: exp.Column
384:            source: The source to search 
…[882 chars elided]…
_join_tables:
385-                    # The RHS table of SEMI/ANTI joins shouldn't be collected as a
386-                    # selected source
387-                    continue
388-
389-                if name in result:
390-                    raise OptimizeError(f"Alias already used: {name}")
391-                if name in self.sources:
392-                    result[name] = (node, self.sources[name])
393-
394-            self._selected_sources = result
395-        return self._selected_sources
[assistant] The Resolver needs the CTE `Scope` to see `c`'s columns, so the scope-side change is the right one. The remaining gap is that `qualify_tables` only assigns the pivot alias inside its `Table` branch, which no longer sees pivoted CTEs. Let me look at the tail of that loop before restructuring it.
[tool_use Bash] {"command": "sed -n 196,225p sqlglot/optimizer/qualify_tables.py", "description": "Read tail of qualify_tables scope loop"}
[tool_result]                 _set_alias(table, canonical_aliases, target_alias=table.name)

        for column in local_columns:
            column_table = column.table

            if column.db:
                table_alias = table_aliases.get(".".join(p.name for p in column.parts[0:-1]))

                if table_alias:
                    for p in exp.COLUMN_PARTS[1:]:
                        column.set(p, None)

                    column.set("table", table_alias.copy())
            elif (
                canonical_aliases
                and column_table
                and (canonical_table := canonical_aliases.get(column_table, "")) != column_table
            ):
                # Amend existing aliases, e.g. t.c -> _0.c if t is aliased to _0
                column.set("table", exp.to_identifier(canonical_table))

    return expression
[assistant] I'll make the minimal change: name a pivoted CTE's pivot in the existing per-table loop, which is where the `Table` branch used to handle it. Real-table pivots keep their current path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "        for table in scope.tables:\n            if not table.alias and isinstance(table.parent, (exp.From, exp.Join)):\n                _set_alias(table, canonical_aliases, target_alias=table.name)\n",
…[196 chars elided]…
alias=table.name)\n\n            # A pivoted CTE is a Scope source keyed by its pivot's alias, so its pivot is aliased here\n            if (pivot := seq_get(table.args.get(\"pivots\") or [], 0)) and table.name in scope.sources:\n                target_alias = table.alias if pivot.unpivot else None\n                _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; grep -n \"seq_get\" sqlglot/optimizer/qualify_tables.py | head -3; PYTHONPATH=$PWD $PY /tmp/repro_unpivot.py; PYTHONPATH=$PWD $PY /tmp/dbg4.py", "description": "Re-run repro cases after qualify_tables change"}
[tool_result] 7:from sqlglot.helper import name_sequence, seq_get, ensure_list
128:            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
138:                if pivot := seq_get(source.args.get("pivots") or [], 0):
bigquery OK  WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery OK  SELECT `_1`.`id` AS `id`, `_1`.`
…[1443 chars elided]…
eb` FROM `t` AS `t`) AS `_0` UNPIVOT(`v` FOR `m` IN (`jan`, `feb`))) AS `_1`
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "p"."id" AS "id", "p"."m" AS "m", "p"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "p"
WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("jan", "feb")) AS "c"
[assistant] All CTE forms now qualify, and the subquery forms are unchanged. Next I'll look for existing UNPIVOT/pivot tests so I can add regression coverage alongside them.
[tool_use Bash] {"command": "grep -rn -i \"unpivot\" tests/fixtures/optimizer/*.sql tests/test_optimizer.py | head -30; grep -rln -i \"unpivot\" tests | head", "description": "Find existing UNPIVOT optimizer test fixtures"}
[tool_result] tests/fixtures/optimizer/optimizer.sql:696:# title: unpivoted table source with a single value column, unpivot columns can't be qualified
tests/fixtures/optimizer/optimizer.sql:699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
tests/fixtures/optimizer/optimizer.sql:706:UNPIVOT("SALES" FOR "MONTH" IN ("JAN", "FEB")) AS "M_SALES"
tests/fixtures/optimizer/optimizer.sql:710:# title: unpivoted table source, unpivot has column aliases
te
…[1371 chars elided]…
d_half_sales) FOR semesters IN ((Q1, Q2) AS 'semester_1', (Q3, Q4) AS 'semester_2'));
tests/fixtures/optimizer/optimizer.sql:771:UNPIVOT((`first_half_sales`, `second_half_sales`) FOR 
tests/test_transpile.py
tests/dialects/test_databricks.py
tests/dialects/test_bigquery.py
tests/dialects/test_oracle.py
tests/dialects/test_snowflake.py
tests/dialects/test_redshift.py
tests/dialects/test_duckdb.py
tests/dialects/test_pipe_syntax.py
tests/fixtures/identity.sql
tests/fixtures/optimizer/optimizer.sql
[tool_use Bash] {"command": "sed -n 690,800p tests/fixtures/optimizer/optimizer.sql", "description": "Read existing UNPIVOT optimizer fixtures"}
[tool_result] SELECT
  "FINAL"."ID" AS "ID",
  "FINAL"."TIMESTAMP_1" AS "TIMESTAMP_1"
FROM "SOURCE" AS "SOURCE"
PIVOT(MAX("SOURCE"."VALUE") FOR "SOURCE"."KEY" IN ('a', 'b', 'c')) AS "FINAL"("ID", "TIMESTAMP_1", "TIMESTAMP_2", "COL_1", "COL_2", "COL_3");

# title: unpivoted table source with a single value column, unpivot columns can't be qualified
# execute: false
# dialect: snowflake
SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
SELECT
  "M_SAL
…[2697 chars elided]…
`produce`.`q4`) AS 'semester_2'
  )
) AS `produce`;

# title: quoting is preserved
# dialect: snowflake
with cte1("id", foo) as (select 1, 2) select "id" from cte1;
WITH "CTE1" AS (
  SELECT
    1 AS "id"
)
SELECT
  "CTE1"."id" AS "id"
FROM "CTE1" AS "CTE1";

# title: ensures proper quoting happens after all optimizations
# execute: false
SELECT "foO".x FROM (SELECT 1 AS x) AS "foO";
WITH "foO" AS (
  SELECT
    1 AS "x"
)
SELECT
  "foO"."x" AS "x"
FROM "foO" AS "foO";

# title: lateral subquery
[assistant] I'll add a fixture alongside the existing UNPIVOT cases. First I'll check the schema the fixture runner uses so the expected output is meaningful.
[tool_use Bash] {"command": "grep -n \"m_sales\\|produce\" tests/test_optimizer.py tests/helpers.py tests/fixtures/optimizer/*.sql | grep -v \"optimizer.sql:7[0-9][0-9]\" | head; grep -n \"def check_file\" -A6 tests/test_optimizer.py | head -20", "description": "Check fixture schema for m_sales and check_file signature"}
[tool_result] tests/test_optimizer.py:996:        # In T-SQL and Redshift, SELECT a + b can produce a NULL, so we can't transpile it
tests/fixtures/optimizer/optimizer.sql:699:SELECT * FROM m_sales AS m_sales(empid, dept, jan, feb) UNPIVOT(sales FOR month IN (jan, feb)) ORDER BY empid;
148:    def check_file(
149-        self,
150-        file,
151-        func,
152-        pretty=False,
153-        execute=False,
154-        only=None,
[assistant] The fixtures run without a schema, so I'll write the CTE case with explicit columns and let the runner check it, then verify the generated SQL by reading it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql", "old_string": "# title: unpivoted table source with a single value column, unpivot columns can be qualified\n# execute: false\n# dialect: bigquery", "new_string": "# title: unpivoted CTE source, the unpivot's valu
…[285 chars elided]…
".\"feb\" AS \"feb\"\n  FROM \"m_sales\" AS \"m_sales\"\n)\nSELECT\n  \"c\".\"empid\" AS \"empid\",\n  \"c\".\"month\" AS \"month\",\n  \"c\".\"sales\" AS \"sales\"\nFROM \"c\" AS \"c\"\nUNPIVOT(\"sales\" FOR \"month\" IN (\"c\".\"jan\", \"c\".\"feb\")) AS \"c\";\n\n# title: unpivoted table source with a single value column, unpivot columns can be qualified\n# execute: false\n# dialect: bigquery"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/tests/fixtures/optimizer/optimizer.sql has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat .lithify/harness/memory.md 2>/dev/null | head -5; $PY .lithify/harness/scripts/run_suite.py tests/test_optimizer.py 2>&1 | tail -40", "description": "Run optimizer test file to check the new fixture", "timeout": 600000}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[360 chars elided]…
1/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/test_optimizer.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fe4a6e2d56.log
ELAPSED: 14s
SUMMARY: 77 passed, 3706 subtests passed in 13.41s
EXIT: 0
[assistant] The new fixture passes, and the runner matched the expected output I wrote from the qualified AST. Now the full suite, once, after the last edit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -40", "description": "Run full test suite once after edits", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-00:30:04 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  65324       00:07 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fe4a6e2d56.log
ELAPSED: 56s
SUMMARY: 1092 passed, 17866 subtests passed in 55.95s
EXIT: 0
[assistant] Full suite: `SUMMARY: 1092 passed ... EXIT: 0`. The scope change also affects non-UNPIVOT pivots on CTEs, so I'll spot-check a PIVOT over a CTE and run the linter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/pivot_cte.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"id\": \"INT\", \"k\": \"TEXT\", \"v\": \"INT\"}}\nfor sql in [\"WITH c AS (SELECT id, k, v FROM t) SELECT * FROM c 
…[308 chars elided]…
as x:\n        print(\"ERR\", type(x).__name__, x)\nEOF\nPYTHONPATH=$PWD $PY /tmp/pivot_cte.py; git stash list >/dev/null; $PY -m ruff check sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py 2>&1 | tail -3", "description": "Spot-check PIVOT over CTE and run ruff on changed files"}
[tool_result] WITH "c" AS (SELECT "t"."id" AS "id", "t"."k" AS "k", "t"."v" AS "v" FROM "t" AS "t") SELECT "_0"."id" AS "id", "_0"."a" AS "a", "_0"."b" AS "b" FROM "c" AS "c" PIVOT(SUM("v") FOR "k" IN ('a', 'b')) AS "_0"
WITH "c" AS (SELECT "t"."id" AS "id", "t"."k" AS "k", "t"."v" AS "v" FROM "t" AS "t") SELECT "p"."id" AS "id", "p"."a" AS "a" FROM "c" AS "c" PIVOT(SUM("v") FOR "k" IN ('a', 'b')) AS "p"("id", "a", "b")
All checks passed!
Would reformat: sqlglot/optimizer/qualify_tables.py
1 file would be reformatted, 1 file already formatted
[assistant] PIVOT over a CTE now expands correctly (`_0.id, _0.a, _0.b`). Ruff flags a formatting issue in `qualify_tables.py`; let me see whether it's my line.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff sqlglot/optimizer/qualify_tables.py 2>&1 | head -20", "description": "Show ruff format diff for qualify_tables"}
[tool_result] --- sqlglot/optimizer/qualify_tables.py
+++ sqlglot/optimizer/qualify_tables.py
@@ -196,7 +196,9 @@
                 _set_alias(table, canonical_aliases, target_alias=table.name)
 
             # A pivoted CTE is a Scope source keyed by its pivot's alias, so its pivot is aliased here
-            if (pivot := seq_get(table.args.get("pivots") or [], 0)) and table.name in scope.sources:
+            if (
+                pivot := seq_get(table.args.get("pivots") or [], 0)
+            ) and table.name in scope.sources:
                 target_alias = table.alias if pivot.unpivot else None
                 _set_alias(pivot, canonical_aliases, target_alias=target_alias, normalize=True)
 

1 file would be reformatted
[assistant] That's my line. I'll restructure it to a plain assignment, which reads better anyway, then re-run lint and the full suite since the file changed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_tables.py", "old_string": "            # A pivoted CTE is a Scope source keyed by its pivot's alias, so its pivot is aliased here\n            if (pivot := seq_get(table.args.get(\"pivots\") or [], 0)) and table.name in scope.sources:\n                target_alias", "new_string": "            # A pivoted CTE is a Scope source keyed by its pivot's alias, so its pivot is aliased here\n            pivot = seq_get(table.args.get(\"pivots\") or [], 0)\n            if pivot and table.name in scope.sources:\n                target_alias"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195836-optimizer-select-from-cte-unpivo/base-1/sqlglot/optimizer/qualify_tables.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py && $PY -m ruff check sqlglot/optimizer/ tests/test_optimizer.py | tail -1; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -4", "description": "Lint, format-check, and run full suite after final edit", "timeout": 600000}
[tool_result] 2 files already formatted
All checks passed!
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fe4a6e2d56.log
ELAPSED: 186s
SUMMARY: 1092 passed, 17866 subtests passed in 59.31s
EXIT: 0
[assistant] `SELECT * FROM cte UNPIVOT(...)` now qualifies in BigQuery, DuckDB, Snowflake and Spark. The full suite passes after my last edit: `SUMMARY: 1092 passed, 17866 subtests passed in 59.31s`, `EXIT: 0`. I haven't committed anything.

**Root cause:** `sqlglot/optimizer/scope.py` registered a pivoted CTE reference as the raw `Table` node. The outer query then had no CTE columns to resolve against, so `jan` and `feb` in the `IN (...)` list came out as "Ambiguous column". Derived-table pivots already work because they register the subquery's `Scope`.

**Changes:**
- `sqlglot/optimizer/scope.py`: a piv
…[833 chars elided]…
.b`, which is correct.
- The new fixture passes in `tests/test_optimizer.py`.
- Ruff check and format pass on the changed files.

Output for the example, with the value and name columns left unqualified and the `IN` items qualified to `c`:
```sql
WITH "c" AS (SELECT "m_sales"."empid" ... FROM "m_sales" AS "m_sales")
SELECT "c"."empid" AS "empid", "c"."month" AS "month", "c"."sales" AS "sales"
FROM "c" AS "c" UNPIVOT("sales" FOR "month" IN ("c"."jan", "c"."feb")) AS "c"
```

I did not add a dialect-specific test. The fixture uses the default dialect, and the four-dialect check was done by hand.
