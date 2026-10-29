# trajectory base-1

final message:
Both UNPIVOT-over-CTE queries from the report now qualify correctly, and the full suite passes (1092 passed).

**Root cause:** the validation check in `_qualify_columns` took the pivoted source's columns from the resolver, which returns only the CTE's pre-pivot columns (`id, jan, feb`). The UNPIVOT's output names (`m`, `v`) were rejected as unknown. Bare `SELECT v` already worked because it's qualified straight to the pivot alias and never hits that check.

**Fix** (`sqlglot/optimizer/qualify_columns.py`): a new helper, `_unpivoted_source_columns`, applies the UNPIVOT transform to the source's columns in that check. It removes the IN-list columns and adds the output names. I put it in the check rather than in `Resolver.get_source_columns` because star expansion adds the pivot outputs on top of that method, and changing it would have duplicated them.

**Test** (`tests/test_optimizer.py`, in `test_qualify_columns`): regression assertions for `SELECT u.v ... AS u` and `SELECT c.v` against an unaliased pivot, with exact BigQuery output.

**Verified:**
- `u.v` (aliased) and `c.v` (unaliased) now qualify.
- Negative cases still error: `u.jan` (an IN-list column, consumed by the UNPIVOT) and `u.nope`.
- `SELECT *` with aliased and unaliased pivots expands to `id, m, v`.

**Not verified:**
- I did not reproduce a star-expansion failure. In this environment, `SELECT *` expands correctly for both the aliased and unaliased CTE shapes, so the "silently skips star expansion" part of the report may depend on something I didn't set up.
- I did not run against live BigQuery.
- I did not make a commit.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"pivot\\|Pivot\" sqlglot/optimizer/qualify_columns.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_tables.py | head -80", "description": "Check status and find pivot handling in optimizer"}
[tool_result] sqlglot/optimizer/qualify_tables.py:128:            if pivot := seq_get(derived_table.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py:129:                _set_alias(pivot, canonical_aliases)
sqlglot/optimizer/qualify_tables.py:135:                # When the name is empty, it means that we have a non-table source, e.g. a pivoted cte
sqlglot/optimizer/qualify_tables.py:138:                if pivot := seq_get(source.args.get("pivots") or [], 0):
sqlglot/optimizer/qualify_tables.py
…[4060 chars elided]…
/optimizer/scope.py:483:        return self._pivots
sqlglot/optimizer/scope.py:813:                # it is pivoted, because then we get back a new table and hence a new source.
sqlglot/optimizer/scope.py:814:                pivots = expression.args.get("pivots")
sqlglot/optimizer/scope.py:815:                if pivots:
sqlglot/optimizer/scope.py:816:                    sources[pivots[0].alias] = expression
sqlglot/optimizer/scope.py:947:                for key in ("joins", "laterals", "pivots"):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer.annotate_types import annotate_types\nqs = [\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, f
…[96 chars elided]…
b)) AS u',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n]\nfor q in qs:\n    try:\n        print(qualify(sqlglot.parse_one(q, read='bigquery'), dialect='bigquery', validate_qualify_columns=False).sql('bigquery'))\n    except Exception as e:\n        print('ERR', type(e).__name__, e)\n\"", "description": "Reproduce the two failing queries and variants"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
ERR OptimizeError Unknown column: v
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[assistant] Both queries qualify without error under `validate_qualify_columns=False`, but a third variant (unaliased, bare `v`) fails. Let me rerun with validation on and a schema, which is closer to how the failures are reported.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'id': 'INT64', 'jan': 'INT64', 'feb': 'INT64'}}\nqs = [\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (ja
…[202 chars elided]…
'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n]\nfor d in ['bigquery', None]:\n  for q in qs:\n    try:\n        print(d, '|', qualify(sqlglot.parse_one(q, read=d), dialect=d, schema=schema).sql(d))\n    except Exception as e:\n        print(d, '| ERR', type(e).__name__, e)\n\"", "description": "Run qualify with schema and validation on both dialects"}
[tool_result] bigquery | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
bigquery | ERR OptimizeError Unknown column: v
bigquery | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)
…[485 chars elided]…
| ERR OptimizeError Unknown column: v
None | WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "u"."id" AS "id", "u"."m" AS "m", "u"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("c"."jan", "c"."feb")) AS "u"
None | WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("c"."jan", "c"."feb")) AS "c"
None | ERR OptimizeError Unknown column: v
[assistant] The star-expansion cases already expand here, so the live failure is the unaliased pivot with a bare column `v` ("Unknown column: v"). Let me read the pivot-related code in `qualify_columns.py`.
[tool_use Bash] {"command": "sed -n 600,660p sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 770,900p sqlglot/optimizer/qualify_columns.py", "description": "Read pivot-related sections of qualify_columns.py"}
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
…[7103 chars elided]…
ons.append(
                        alias(exp.func("coalesce", *coalesce_args), alias=name, copy=False)
                    )
                else:
                    alias_ = renamed_columns.get(name, name)
                    selection_expr = replaced_columns.get(name) or exp.column(name, table=table)
                    new_selections.append(
                        alias(selection_expr, alias_, copy=False)
                        if alias_ != name
                        else selection_expr
[assistant] The bare `v` gets qualified to the pivot's source name `c`, then fails the "column in source_columns" check. So `get_source_columns("c")` returns the CTE's columns (`id, jan, feb`) instead of the pivot output. Let me check the resolver and the scope source registration.
[tool_use Bash] {"command": "sed -n 800,830p sqlglot/optimizer/scope.py && echo ---- && grep -n \"def get_source_columns\" -A40 sqlglot/optimizer/qualify_columns.py && echo ---- && sed -n 120,185p sqlglot/optimizer/qualify_tables.py", "description": "Read scope source registration, resolver, and qualify_tables pivot code"}
[tool_result ERROR] Exit code 1
        expressions.append(scope.expression)

    expressions.extend(scope.expression.args.get("laterals") or [])

    for expression in expressions:
        if isinstance(expression, exp.Final):
            expression = expression.this
        if isinstance(expression, exp.Table):
            table_name = expression.name
            source_name = expression.alias_or_name

            if table_name in scope.sources and not expression.db:
                # This is a reference to a par
…[344 chars elided]…
name] = scope.sources[table_name]
            elif source_name in sources:
                sources[find_new_name(sources, table_name)] = expression
            else:
                sources[source_name] = expression

            # Make sure to not include the joins twice
            if expression is not scope.expression:
                expressions.extend(join.this for join in expression.args.get("joins") or [])

            continue

        if not isinstance(expression, exp.DerivedTable):
----
[tool_use Bash] {"command": "grep -rn \"def get_source_columns\\|def _get_source_columns\\|pivot\" sqlglot/optimizer/resolver.py | head -30; echo ----; sed -n 120,185p sqlglot/optimizer/qualify_tables.py", "description": "Locate resolver and read qualify_tables pivot code"}
[tool_result] sqlglot/optimizer/resolver.py:95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py:133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
sqlglot/optimizer/resolver.py:142:            # A pivoted CTE reference is stored as an exp.Table in the scope sources (see
sqlglot/optimizer/resolver.py:144:            # column information we need to resolve pre-pivot columns.
sqlglot/optimizer/resolver.py:148
…[2798 chars elided]…
voted CTE, we don't want to qualify that
                    if isinstance(scope.sources.get(source.alias_or_name), Scope):
                        continue

                if is_real_table_source:
                    _qualify(source)

                    if on_qualify:
                        on_qualify(source)
            elif isinstance(source, Scope) and source.is_udtf:
                _set_alias(udtf := source.expression, canonical_aliases)

                table_alias = udtf.args["alias"]
[tool_use Bash] {"command": "sed -n 60,200p sqlglot/optimizer/resolver.py; git log --oneline -3 -- sqlglot/optimizer/resolver.py", "description": "Read resolver source column logic"}
[tool_result]                     pass

        if not table_name and self._infer_schema:
            sources_without_schema = tuple(
                source
                for source, columns in self._get_all_source_columns().items()
                if not columns or "*" in columns
            )
            if len(sources_without_schema) == 1:
                table_name = sources_without_schema[0]

        if table_name not in self.scope.selected_sources:
            return exp.to_identifier(table_name)

   
…[5966 chars elided]…
          else:
                    columns = selectable.named_selects

            node, _ = self.scope.selected_sources.get(name) or (None, None)
            if isinstance(node, Scope):
                column_aliases = node.expression.alias_column_names
            elif isinstance(node, exp.Expr):
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
5351ca128 fix(optimizer): EXPLODE qualify and annotate (#7549)
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
[assistant] The resolver special-cases pivoted CTEs (commit 8f572f865). Let me read the rest of `get_source_columns` and that commit's diff to see what it covers.
[tool_use Bash] {"command": "sed -n 200,225p sqlglot/optimizer/resolver.py; echo ----; git show 8f572f865 --stat; git show 8f572f865 -- sqlglot/ | head -150", "description": "Read rest of resolver and the prior UNPIVOT CTE fix diff"}
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
…[7493 chars elided]…
 
@@ -5142,6 +5151,12 @@ class Parser:
             )
         )
 
+        if unpivot:
+            pivot.set("expressions", [_unpivot_target(e) for e in pivot.expressions])
+            for pivot_field in pivot.fields:
+                if isinstance(pivot_field, exp.In):
+                    pivot_field.set("this", _unpivot_target(pivot_field.this))
+
         if not self._match_set((TokenType.PIVOT, TokenType.UNPIVOT), advance=False):
             pivot.set("alias", self._parse_table_alias())
[assistant] The prior fix only makes the resolver fall back to the CTE's columns; it never adds the UNPIVOT's output columns (`m`, `v`). I want to see exactly where each variant resolves, so I'll trace the scope sources and the resolver's answer for each case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.optimizer.scope import build_scope\nschema = {'t': {'id': 'INT64', 'jan': 'INT64', 'feb': 'INT64'}}\nqs = {\n'alias_u.v': 'WITH c AS (SELECT id, jan, feb FROM t) SELE
…[284 chars elided]…
alify_columns=False, quote_identifiers=False)\n    print(k, '->', e.sql('bigquery'))\n    s = build_scope(sqlglot.parse_one(q, read='bigquery'))\n    print('  sources', {n: type(v).__name__ for n,v in s.sources.items()}, 'pivots', [p.alias for p in s.pivots])\n    print('  cols', [c.sql() for c in s.columns])\n\" 2>&1 | head -40", "description": "Trace scope sources and columns for both variants"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 12, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify.py", line 97, in qualify
    expression = qualify_columns_func(
                 ^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", line 615, in _qualify_columns
    raise OptimizeError(f"Unknown column: {column_name}")
sqlglot.errors.OptimizeError: Unknown column: v
[assistant] The aliased `u.v` case raised here, though it passed in the earlier run. The only differences are `quote_identifiers=False` and the schema, so I'll run a small matrix to find which knob changes the result.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'id': 'INT64', 'jan': 'INT64', 'feb': 'INT64'}}\nqs = {\n'alias_u.v': 'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n'star_alias': 'WITH c AS (SELECT id, jan, feb FROM t) SELECT
…[419 chars elided]…
rse_one(q, read='bigquery'), dialect='bigquery', schema=sch, quote_identifiers=quote, validate_qualify_columns=val).sql('bigquery')\n          res = 'OK'\n        except Exception as e:\n          res = 'ERR ' + str(e)\n        print(f'{k:12} quote={quote!s:5} validate={val!s:5} schema={sch is not None!s:5} {res}')\n\" 2>&1", "description": "Matrix of qualify options across the four query shapes"}
[tool_result] alias_u.v    quote=True  validate=True  schema=True  ERR Unknown column: v
alias_u.v    quote=True  validate=True  schema=False ERR Unknown column: v
alias_u.v    quote=True  validate=False schema=True  ERR Unknown column: v
alias_u.v    quote=True  validate=False schema=False ERR Unknown column: v
alias_u.v    quote=False validate=True  schema=True  ERR Unknown column: v
alias_u.v    quote=False validate=True  schema=False ERR Unknown column: v
alias_u.v    quote=False validate=False schema=Tru
…[943 chars elided]…
r         quote=False validate=False schema=False OK
noalias_v    quote=True  validate=True  schema=True  OK
noalias_v    quote=True  validate=True  schema=False OK
noalias_v    quote=True  validate=False schema=True  OK
noalias_v    quote=True  validate=False schema=False OK
noalias_v    quote=False validate=True  schema=True  OK
noalias_v    quote=False validate=True  schema=False OK
noalias_v    quote=False validate=False schema=True  OK
noalias_v    quote=False validate=False schema=False OK
[assistant] The matrix settles it. Option-independent failures are the aliased `u.v` case and the explicit `c.v` case; the star cases and bare `SELECT v` already pass. The check is in `_qualify_columns`: `get_source_columns("u")` returns the CTE's columns (`id, jan, feb`), which lack the UNPIVOT output `v`. I'll confirm `c.v` and a real-table UNPIVOT too, then look at the existing test.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'id': 'INT64', 'jan': 'INT64', 'feb': 'INT64'}}\nqs = [\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'SELECT u.v FROM t UNPIVOT(v FOR m IN (jan, feb)) AS u',\n'SELECT u.id, u.m FR
…[79 chars elided]…
TH c AS (SELECT * FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n]\nfor q in qs:\n    try:\n        print(qualify(sqlglot.parse_one(q, read='bigquery'), dialect='bigquery', schema=schema).sql('bigquery'))\n    except Exception as e:\n        print('ERR', e)\n\"; grep -n \"UNPIVOT\" tests/test_optimizer.py | head", "description": "Check more UNPIVOT shapes and find existing test"}
[tool_result] ERR Unknown column: v
SELECT `u`.`v` AS `v` FROM `t` AS `t` UNPIVOT(`v` FOR `m` IN (`t`.`jan`, `t`.`feb`)) AS `u`
SELECT `u`.`id` AS `id`, `u`.`m` AS `m` FROM (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) AS `s` UNPIVOT(`v` FOR `m` IN (`s`.`jan`, `s`.`feb`)) AS `u`
ERR Unknown column: v
639:                    "SELECT * FROM produce UNPIVOT(sales FOR quarter IN (q1, q2))",
647:            "UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`",
[assistant] Real-table UNPIVOT passes, but the CTE shapes (aliased `u.v`, explicit `c.v`) and the derived-table form with an explicit `s`-prefixed join... the derived-table one works. So the defect is specific to pivoted CTE table sources. Let me look at the existing test and the `_qualify_columns` caller before editing.
[tool_use Bash] {"command": "sed -n 625,660p tests/test_optimizer.py; echo ----; sed -n 560,600p sqlglot/optimizer/qualify_columns.py", "description": "Read existing UNPIVOT test and qualify_columns caller"}
[tool_result]         self.assertEqual(
            optimizer.qualify.qualify(
                parse_one("SELECT * FROM t"),
                schema={"t": {"end": "text"}},
                quote_identifiers=False,
            ).sql(),
            "SELECT t.end AS end FROM t AS t",
        )

        self.assertEqual(
            optimizer.qualify.qualify(
                parse_one(
                    "WITH produce AS (SELECT 'Kale' AS product, 51 AS q1, 23 AS q2) "
                    "SELECT * FROM produce U
…[2003 chars elided]…
 rest of dot parts
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
[assistant] I have the root cause. In `_qualify_columns`, the validation check takes the pivoted source's columns from the resolver, which returns only the pre-pivot columns, so the UNPIVOT's output names (`m`, `v`) are rejected. I'll apply the UNPIVOT transform to those columns in that check, matching what star expansion already does. I'm leaving `get_source_columns` alone, because the star path adds pivot outputs on top of it and would double them.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "offset": 180, "limit": 20}
[tool_result] 180	    if has_pseudocolumns:
181	        scope.clear_cache()
182	
183	
184	def _unpivot_columns(unpivot: exp.Pivot) -> Iterator[exp.Identifier]:
185	    name_columns = [
186	        field.this
187	        for field in unpivot.fields
188	        if isinstance(field, exp.In) and isinstance(field.this, exp.Identifier)
189	    ]
190	    value_columns = (
191	        ident
192	        for e in unpivot.expressions
193	        for ident in (e.expressions if isinstance(e, exp.Tuple) else [e])
194	        if isinstance(ident, exp.Identifier)
195	    )
196	
197	    return itertools.chain(name_columns, value_columns)
198	
199	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    return itertools.chain(name_columns, value_columns)\n\n", "new_string": "    return itertools.chain(name_columns, value_columns)\n\n\ndef _unpivoted_source_columns(source: exp.Expr | Scope, column
…[277 chars elided]…
t) or not pivot.unpivot or pivot.alias_column_names or not columns:\n        return columns\n\n    exclude = {\n        c.output_name\n        for field in pivot.fields\n        if isinstance(field, exp.In)\n        for e in field.expressions\n        for c in e.find_all(exp.Column)\n    }\n    return [c for c in columns if c not in exclude] + [c.output_name for c in _unpivot_columns(pivot)]\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[assistant] Now I'll wire it into the check and confirm the imports I depend on are already present.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "            source_columns = resolver.get_source_columns(column_table)\n            if (\n                not allow_partial_qualification", "new_string": "            source_columns = _unpivoted_source_columns(\n                scope.sources[column_table], resolver.get_source_columns(column_table)\n            )\n            if (\n                not allow_partial_qualification"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/optimizer/qualify_columns.py | grep -n \"import\\|Sequence\\|Scope\\|seq_get\"", "description": "Check imports in qualify_columns.py"}
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
17:    from sqlglot._typing import E
18:    from collections.abc import Iterator, Iterable
[assistant] `Sequence` isn't imported in this module, so I'll add it to the existing `TYPE_CHECKING` block, then rerun the matrix.
[tool_use Bash] {"command": "sed -i 's/    from collections.abc import Iterator, Iterable$/    from collections.abc import Iterator, Iterable, Sequence/' sqlglot/optimizer/qualify_columns.py && sed -n 16,19p sqlglot/optimizer/qualify_columns.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'id': 'I
…[724 chars elided]…
H c AS (SELECT id, jan, feb FROM t) SELECT u.nope FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n]\nfor q in qs:\n    for d in ['bigquery', None]:\n        try:\n            print(d, '|', qualify(sqlglot.parse_one(q, read=d), dialect=d, schema=schema).sql(d))\n        except Exception as e:\n            print(d, '| ERR', e)\n\"", "description": "Add Sequence import and rerun the UNPIVOT CTE cases"}
[tool_result ERROR] Exit code 1
sed: 1: "sqlglot/optimizer/quali ...": unescaped newline inside substitute pattern
[assistant] The `sed` pattern didn't parse, so I'll make that edit with the Edit tool instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py", "old_string": "    from collections.abc import Iterator, Iterable\n", "new_string": "    from collections.abc import Iterator, Iterable, Sequence\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/sqlglot/optimizer/qualify_columns.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'id': 'INT64', 'jan': 'INT64', 'feb': 'INT64'}}\nqs = [\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (ja
…[505 chars elided]…
H c AS (SELECT id, jan, feb FROM t) SELECT u.nope FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n]\nfor q in qs:\n    for d in ['bigquery', None]:\n        try:\n            print(d, '|', qualify(sqlglot.parse_one(q, read=d), dialect=d, schema=schema).sql(d))\n        except Exception as e:\n            print(d, '| ERR', e)\n\"", "description": "Add Sequence import and rerun the UNPIVOT CTE cases"}
[tool_result] bigquery | WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
None | WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "c"."id" AS "id", "c"."m" AS "m", "c"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("c"."jan", "c"."feb")) AS "c"
bigquery | WITH `c` AS (SELECT `t`.`id` AS
…[1677 chars elided]…
M `t` AS `t`) SELECT `u`.`id` AS `id`, `u`.`m` AS `m`, `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
None | WITH "c" AS (SELECT "t"."id" AS "id", "t"."jan" AS "jan", "t"."feb" AS "feb" FROM "t" AS "t") SELECT "u"."id" AS "id", "u"."m" AS "m", "u"."v" AS "v" FROM "c" AS "c" UNPIVOT("v" FOR "m" IN ("c"."jan", "c"."feb")) AS "u"
bigquery | ERR Unknown column: jan
None | ERR Unknown column: jan
bigquery | ERR Unknown column: nope
None | ERR Unknown column: nope
[assistant] All the positive shapes now qualify, and the negative cases still error correctly: `u.jan` (an IN-list column, consumed by the UNPIVOT) and `u.nope` (unknown). Next I'll add a regression test next to the existing CTE UNPIVOT test, using the schema-less form that test uses. First, the exact expected output:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor q in [\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT * FROM c UNPIVOT(v FOR m IN (jan, feb))',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT u.v FROM c UNPIVOT(v FOR m IN (jan, feb)) AS u',\n'WITH c AS (SELECT id, jan, feb FROM t) SELECT c.v FROM c UNPIVOT(v FOR m IN (jan, feb))',\n]:\n    print(qualify(sqlglot.parse_one(q, read='bigquery'), dialect='bigquery').sql('bigquery'))\n\"", "description": "Generate expected BigQuery output without schema"}
[tool_result] WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`id` AS `id`, `c`.`m` AS `m`, `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `u`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `u`
WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) SELECT `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py", "old_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (`produce`.`q1`, `produce`.`q2`)) AS `produce`\",\n        )\n\n    def test_validate_columns(self):", "new_string": "            \"UNPIVOT(`sales` FOR `quarter` IN (
…[934 chars elided]…
   dialect=\"bigquery\",\n                ),\n                dialect=\"bigquery\",\n            ).sql(dialect=\"bigquery\"),\n            \"WITH `c` AS (SELECT `t`.`id` AS `id`, `t`.`jan` AS `jan`, `t`.`feb` AS `feb` FROM `t` AS `t`) \"\n            \"SELECT `c`.`v` AS `v` FROM `c` AS `c` UNPIVOT(`v` FOR `m` IN (`c`.`jan`, `c`.`feb`)) AS `c`\",\n        )\n\n    def test_validate_columns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-095429-optimizer-un-pivot-over-cte-sour/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now the project's test command from the harness, plus ruff on the two touched source files since I added long lines.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25; echo \"--- ruff\"; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py 2>&1 | tail -5", "description": "Run pytest suite and ruff format/lint checks"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
................................................................................................ [ 20%]
..................... [ 22%]
............................................................................................................... [ 32%]
.... [ 32%]
........................... [ 35%]
............................. [ 37%]
......................
…[467 chars elided]…
................................. [ 80%]
....................................................................................... [ 88%]
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 54.85s
--- ruff
Would reformat: sqlglot/optimizer/qualify_columns.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[assistant] The full suite passes (1092 passed). Ruff wants to reformat `qualify_columns.py`. I'll check that the reformat only touches my new lines before applying it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/optimizer/qualify_columns.py 2>&1 | head -40", "description": "Preview ruff format changes for qualify_columns.py"}
[tool_result] --- sqlglot/optimizer/qualify_columns.py
+++ sqlglot/optimizer/qualify_columns.py
@@ -200,7 +200,12 @@
 def _unpivoted_source_columns(source: exp.Expr | Scope, columns: Sequence[str]) -> Sequence[str]:
     """Replace the UNPIVOT's IN-list columns of a source with the UNPIVOT's output columns"""
     pivot = seq_get(source.args.get("pivots") or [], 0) if isinstance(source, exp.Table) else None
-    if not isinstance(pivot, exp.Pivot) or not pivot.unpivot or pivot.alias_column_names or not column
…[133 chars elided]…
 not columns
+    ):
         return columns
 
     exclude = {
@@ -210,7 +215,9 @@
         for e in field.expressions
         for c in e.find_all(exp.Column)
     }
-    return [c for c in columns if c not in exclude] + [c.output_name for c in _unpivot_columns(pivot)]
+    return [c for c in columns if c not in exclude] + [
+        c.output_name for c in _unpivot_columns(pivot)
+    ]
 
 
 def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:

1 file would be reformatted
[assistant] The reformat only touches my new function. I'll apply it, then rerun the optimizer tests and the full suite once more to confirm.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/optimizer/qualify_columns.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/qualify_columns.py tests/test_optimizer.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2 && git status --short && git diff --stat", "description": "Apply formatting, rerun full suite, and show diff stat"}
[tool_result] 1 file reformatted
2 files already formatted
.............................................................................................................................                                                     [100%]
1092 passed, 17864 subtests passed in 59.32s
 M sqlglot/optimizer/qualify_columns.py
 M tests/test_optimizer.py
 sqlglot/optimizer/qualify_columns.py | 29 +++++++++++++++++++++++++++--
 tests/test_optimizer.py              | 26 ++++++++++++++++++++++++++
 2 files changed, 53 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: sqlglot/optimizer/qualify_columns.py. Call Read before editing.]
[assistant] That notice is just my own `ruff format` run. I'll review the final source diff once.
[tool_use Bash] {"command": "git diff -- sqlglot/", "description": "Show the source diff for review"}
[tool_result] diff --git a/sqlglot/optimizer/qualify_columns.py b/sqlglot/optimizer/qualify_columns.py
index 28de2be45..442d0180a 100644
--- a/sqlglot/optimizer/qualify_columns.py
+++ b/sqlglot/optimizer/qualify_columns.py
@@ -15,7 +15,7 @@ from sqlglot.schema import Schema, ensure_schema
 
 if t.TYPE_CHECKING:
     from sqlglot._typing import E
-    from collections.abc import Iterator, Iterable
+    from collections.abc import Iterator, Iterable, Sequence
 
 
 def qualify_columns(
@@ -197,6 +197,29 @@ def _
…[1010 chars elided]…
move table column aliases.
@@ -605,7 +628,9 @@ def _qualify_columns(
         column_name = column.name
 
         if column_table and column_table in scope.sources:
-            source_columns = resolver.get_source_columns(column_table)
+            source_columns = _unpivoted_source_columns(
+                scope.sources[column_table], resolver.get_source_columns(column_table)
+            )
             if (
                 not allow_partial_qualification
                 and source_columns
[assistant] Both UNPIVOT-over-CTE queries from the report now qualify correctly, and the full suite passes (1092 passed).

**Root cause:** the validation check in `_qualify_columns` took the pivoted source's columns from the resolver, which returns only the CTE's pre-pivot columns (`id, jan, feb`). The UNPIVOT's output names (`m`, `v`) were rejected as unknown. Bare `SELECT v` already worked because it's qualified straight to the pivot alias and never hits that check.

**Fix** (`sqlglot/optimizer/qualify_columns.py`): a new helper, `_unpivoted_source_columns`, applies the UNPIVOT transform to the source's
…[412 chars elided]…
d pivot, with exact BigQuery output.

**Verified:**
- `u.v` (aliased) and `c.v` (unaliased) now qualify.
- Negative cases still error: `u.jan` (an IN-list column, consumed by the UNPIVOT) and `u.nope`.
- `SELECT *` with aliased and unaliased pivots expands to `id, m, v`.

**Not verified:**
- I did not reproduce a star-expansion failure. In this environment, `SELECT *` expands correctly for both the aliased and unaliased CTE shapes, so the "silently skips star expansion" part of the report may depend on something I didn't set up.
- I did not run against live BigQuery.
- I did not make a commit.
