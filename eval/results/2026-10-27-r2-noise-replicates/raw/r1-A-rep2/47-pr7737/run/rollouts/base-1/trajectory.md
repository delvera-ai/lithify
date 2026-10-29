# trajectory base-1

final message:
Fixed: qualifying a Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr` no longer recurses, whether or not the table is in the schema. The full suite passes (1121 tests), and ruff and mypy are clean on the changed files. I haven't committed.

**Cause:** In `sqlglot/optimizer/resolver.py`, resolving the lateral's input column `arr` builds a resolver over the parent scope. That resolver needs every source's columns, including the lateral `e` itself, whose columns call back into the same lookup. Nothing breaks the cycle.

**Fix:** Each resolver now takes an `excluded_sources` set. When a lateral or unnest source disambiguates its own input column, it adds its own name to that set. A lateral can't supply its own input, so this is semantically safe. The set grows with each level, so recursion is bounded by the number of sources.

**Test:** `test_lateral_explode_unqualified_column_recursion` in `tests/test_optimizer.py` covers both cases. With the table missing from the schema it expects a normal `OptimizeError`. With the table present it checks the expected output. No existing tests were changed.

Things I checked that you should know:
- **Snowflake `LATERAL FLATTEN`** never recursed. Its argument parses as a `Kwarg`, not a column, so it fails with a normal `OptimizeError`.
- **BigQuery `UNNEST`** didn't recurse on any shape I tried, before or after the fix. I changed its branch to use the same exclusion because it shares the helper, but I didn't reproduce a recursion there. If you have a specific UNNEST query that crashed, send it and I'll check it against this fix.
- **`sqlglot[c]`** (mypyc-compiled) isn't built or tested here. The change is plain Python, but the compiled build is unverified.

## events
[assistant] I'll start by reproducing the recursion with a minimal query, then look at the column resolver.
[tool_use Bash] {"command": "cat > /tmp/repro_flatten.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1\")\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f\", {\"other\"
…[448 chars elided]…
\n        print(\"OK\", dialect, sql, schema)\n    except RecursionError as e:\n        print(\"RecursionError\", dialect, sql, schema)\n    except Exception as e:\n        print(type(e).__name__, e, dialect, sql, schema)\nEOF\nls; <work>/env-sqlglot/bin/python -I /tmp/repro_flatten.py", "description": "Reproduce the qualify recursion on FLATTEN/UNNEST"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51 snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f {'other': {'x': 'int'}}
OK snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f {'t': {'arr': 'array'}}
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27 bigquery SELECT x FROM t, UNNEST(arr) AS x {'other': {'x': 'int'}}
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27 bigquery SELECT x FROM t, UNNEST(arr) AS x {'t': {'y': 'int'}}
[assistant] No recursion on these inputs, so the trigger must be narrower. I'll look at the column resolver's handling of unnest/lateral sources.
[tool_use Bash] {"command": "grep -n \"def \\|Unnest\\|Lateral\\|_get_source_columns\\|unnest\\|Explode\" sqlglot/optimizer/qualify_columns.py | head -150", "description": "List functions and unnest handling in qualify_columns"}
[tool_result] 21:def qualify_columns(
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
162:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
184:def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
198:def _expand_using(scope: Scope, resolver: Resolver) -> dict[str, t.Any]:
201:    def _update_source_columns(source_name: str) -> None:
302:def _expand_alias_refs(
320:    def replace_columns(
422:def _expand_group_by(scope: Scope, dial
…[693 chars elided]…
s:
755:    for struct_field_def in t.cast(exp.DataType, starting_struct).expressions:
764:def _expand_stars(
881:def _add_except_columns(expression: exp.Expr, tables, except_columns: dict[int, set[str]]) -> None:
893:def _add_rename_columns(
907:def _add_replace_columns(
921:def qualify_outputs(scope_or_expression: Scope | exp.Expr) -> None:
961:def quote_identifiers(expression: E, dialect: DialectType = None, identify: bool = True) -> E:
974:def pushdown_cte_alias_columns(scope: Scope) -> None:
[tool_use Bash] {"command": "grep -n \"def \\|Unnest\\|Lateral\\|Flatten\\|Explode\" sqlglot/optimizer/scope.py sqlglot/optimizer/resolver.py 2>/dev/null | head -150; ls sqlglot/optimizer/", "description": "Find resolver and unnest/lateral handling in optimizer"}
[tool_result] sqlglot/optimizer/resolver.py:24:    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
sqlglot/optimizer/resolver.py:34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
sqlglot/optimizer/resolver.py:87:    def all_columns(self) -> set[str]:
sqlglot/optimizer/resolver.py:95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py:133:    def get_source_columns(self, name: str, only_
…[5949 chars elided]…
pe(
sqlglot/optimizer/scope.py:1043:def _get_source_alias(expression: exp.Expr) -> str:
__init__.py
__pycache__
annotate_types.py
canonicalize.py
canonicalize_internal_names.py
eliminate_ctes.py
eliminate_joins.py
eliminate_subqueries.py
isolate_table_selects.py
merge_subqueries.py
normalize.py
normalize_identifiers.py
optimize_joins.py
optimizer.py
pushdown_predicates.py
pushdown_projections.py
qualify.py
qualify_columns.py
qualify_tables.py
resolver.py
scope.py
simplify.py
unnest_subqueries.py
[tool_use Bash] {"command": "sed -n 130,216p sqlglot/optimizer/resolver.py; echo ----; sed -n 296,420p sqlglot/optimizer/resolver.py", "description": "Read resolver source column logic"}
[tool_result]         return columns

    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._get_source_columns_cache:
            if name not in self.scope.sources:
                raise OptimizeError(f"Unknown table: {name}")

            source = self.scope.sources[name]

            # A pivoted CTE reference is stored as an exp.Ta
…[8261 chars elided]…
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
[assistant] The likely cycle is in `_get_unnest_column_type`: it builds a parent resolver and calls `get_table`, which can ask for the lateral's own source columns, which call back into `_get_unnest_column_type`. Checking `get_table` to see when that path is reached.
[tool_use Bash] {"command": "sed -n 20,95p sqlglot/optimizer/resolver.py; echo ----; sed -n 217,240p sqlglot/optimizer/resolver.py", "description": "Read Resolver.get_table and source column helpers"}
[tool_result]     This is a class so we can lazily load some things and easily share them across functions.
    """

    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
        self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | Non
…[3412 chars elided]…
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
[assistant] The cycle looks structurally real: a fresh `Resolver` per call means nothing short-circuits it. My earlier inputs didn't hit it, so I'll check how FLATTEN and UNNEST parse and try the Spark `LATERAL VIEW EXPLODE` form, which goes through the `Explode` branch.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1\")\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"spark\", \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x\", {\"other\": {\"x\": \"int\"}}),\n    (\"spark\", \"SELECT x FROM t 
…[943 chars elided]…
thify-dev/r2-noise-scratch/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1')\nimport sqlglot; print(repr(sqlglot.parse_one('SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f', read='snowflake'))[:600])\"", "description": "Test Spark explode and FLATTEN/UNNEST variants"}
[tool_result] RecursionError spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x {'other': {'x': 'int'}}
RecursionError spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x {'t': {'y': 'int'}}
OK spark SELECT x FROM t LATERAL VIEW EXPLODE(t.arr) e AS x {'other': {'x': 'int'}}
OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51 | snowflake SELECT f.value FROM t, LATERAL FLATTEN(input => arr) f {'other': {'x': 'int'}}
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27 | bigqu
…[211 chars elided]…
ntifier(this=f, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  joins=[
    Join(
      this=Lateral(
        this=Explode(
          this=Kwarg(
            this=Var(this=input),
            expression=Column(
              this=Identifier(this=arr, quoted=False)))),
        view=False,
        outer=False,
        alias=TableAlias(
          this=Identifier(this=f, quoted=False),
          columns=[
            Identifier(this=SEQ, quoted=False),
[assistant] Reproduced: Spark `LATERAL VIEW EXPLODE(arr)` with unqualified `arr` recurses under both schema cases. The Snowflake `FLATTEN` case fails earlier with a normal `OptimizeError` because its argument is a `Kwarg`, so it isn't on the cycle.

The cycle: resolving `arr` in the parent scope calls `get_table`, which needs every source's columns, including the lateral `e` itself, whose columns call `_get_unnest_column_type` again. A lateral can't supply its own input column, so the fix is to exclude the lateral's own source (and any already-in-progress ones) from the disambiguation resolver. I'll check the `Resolver` call sites before changing it.
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | grep -v \"class Resolver\"; grep -n \"lateral_sources\" sqlglot/optimizer/*.py | head; git status --short", "description": "Find Resolver call sites and lateral_sources usage"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
sqlglot/optimizer/scope.py:60:        lateral_sources: Sources from laterals
sqlglot/optimizer/scope.py:108:        lateral_sources: dict[str, exp.Table | Scope] | None = None,
sqlglot/opt
…[206 chars elided]…
es: dict[str, exp.Table | Scope] | None = None,
sqlglot/optimizer/scope.py:167:            lateral_sources=lateral_sources.copy() if lateral_sources else None,
sqlglot/optimizer/scope.py:868:            lateral_sources = sources
sqlglot/optimizer/scope.py:872:            lateral_sources = None
sqlglot/optimizer/scope.py:887:                lateral_sources=lateral_sources,
sqlglot/optimizer/resolver.py:222:                    self.scope.selected_sources.items(), self.scope.lateral_sources.items()
[assistant] Only `_get_unnest_column_type` builds a nested resolver, so the change stays local to `resolver.py`. I'll thread an excluded-sources set through the resolver: the lateral's own name is added when it disambiguates its input column, and the set grows along the chain, so recursion is bounded by the number of sources.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[669 chars elided]…
Dialect()\n        self._source_columns: dict[str, Sequence[str]] | None = None\n        self._unambiguous_columns: Mapping[str, str] | None = None\n        self._all_columns: set[str] | None = None\n        self._infer_schema: bool = infer_schema\n        self._excluded_sources: frozenset[str] = excluded_sources\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    columns.extend(self._struct_field_names(source_expr.type))\n                elif isinstance(source_expr, exp.Lateral) and isinstance(\n                    source_expr.this, exp.Explode\n 
…[329 chars elided]…
rce_expr.type))\n                elif isinstance(source_expr, exp.Lateral) and isinstance(\n                    source_expr.this, exp.Explode\n                ):\n                    explode_col = source_expr.this.this\n\n                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explode_col, source.parent, name)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "        if self._source_columns is None:\n            self._source_columns = {\n                source_name: self.get_source_columns(source_name)\n                for source_name, source in itertools.chain(\
…[141 chars elided]…
: "        if self._source_columns is None:\n            self._source_columns = {\n                source_name: self.get_source_columns(source_name)\n                for source_name, source in itertools.chain(\n                    self.scope.selected_sources.items(), self.scope.lateral_sources.items()\n                )\n                if source_name not in self._excluded_sources\n            }"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def _get_unnest_column_type(self, column: exp.Column, scope: Scope) -> exp.DataType | None:\n        \"\"\"\n        Get the type of a column being unnested/exploded, tracing through CTEs/subqueries to f
…[1368 chars elided]…
uate using the resolver\n        if column.table:\n            table_name = column.table\n        else:\n            # use the parent scope's resolver to disambiguate the column\n            parent_resolver = Resolver(\n                scope,\n                self.schema,\n                self._infer_schema,\n                excluded_sources=self._excluded_sources | {source_name},\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] The Unnest branch also calls `_get_unnest_column_type`, so it needs the new argument too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                            col_type = self._get_unnest_column_type(unnest_expr, self.scope.parent)", "new_string": "                            col_type = self._get_unnest_column_type(\n                                unnest_expr, self.scope.parent, name\n                            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro2.py && <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot.optimizer import optimize\nfor sql, d, s in [\n ('SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x', 'spark', {'t': {'arr': 'array<int>'}}),\n 
…[244 chars elided]…
TERAL VIEW EXPLODE(x) e2 AS y', 'spark', {'other': {'a': 'int'}}),\n ('SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x', 'spark', {'t': {'arr': 'array<struct<x:int>>'}}),\n]:\n  try: print(optimize(sqlglot.parse_one(sql, read=d), schema=s, dialect=d).sql(d))\n  except Exception as ex: print(type(ex).__name__, str(ex)[:100])\n\"", "description": "Rerun repro cases and a few Spark optimize checks"}
[tool_result] OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40 | spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x {'other': {'x': 'int'}}
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40 | spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x {'t': {'y': 'int'}}
OK spark SELECT x FROM t LATERAL VIEW EXPLODE(t.arr) e AS x {'other': {'x': 'int'}}
OptimizeError Column 'ARR' could not be resolved. Line: 1, Col: 51 | snowflake SELECT f.value FROM t, LATERAL FLATTEN(input 
…[89 chars elided]…
 1, Col: 27 | bigquery SELECT x FROM t, UNNEST(arr) AS x {'other': {'x': 'int'}}
OK bigquery SELECT x FROM t, UNNEST(arr) AS x {}
SELECT `e`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) e AS `x`
SELECT `e`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) e AS `x`
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
SELECT `e`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) e AS `x`
[assistant] The recursion is gone for the Spark form, and the remaining errors are clean `OptimizeError`s, which terminate. Next I'll sweep more shapes (nested unnest, BigQuery UNNEST in subqueries, lateral chains) to check that no other path still recurses.
[tool_use Bash] {"command": "cat > /tmp/sweep.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nimport sqlglot\nfrom sqlglot.optimizer import optimize\ncases = [\n (\"bigquery\", \"SELECT x FROM t, UNNEST(arr) AS x\", [{\"other\": {\"x\": \"int\"}}, {\"t\": {\"y\": \"int\"}}, {}]),\n (\"bigquery\", \"SELECT (SELECT x FROM UNNEST(arr) AS x) FROM t\", [{\"other\": {\"x\": \"int\"}}, {\"t\": {\"y\": \"int\"}}]),\n 
…[1271 chars elided]…
ct), schema=s, dialect=dialect)\n            r = \"OK\"\n        except RecursionError:\n            r = \"RECURSION\"\n        except Exception as ex:\n            r = type(ex).__name__\n        print(f\"{r:18} {dialect:9} {s} {sql[:70]}\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/sweep.py", "description": "Sweep unnest/lateral shapes for recursion"}
[tool_result] OptimizeError      bigquery  {'other': {'x': 'int'}} SELECT x FROM t, UNNEST(arr) AS x
OptimizeError      bigquery  {'t': {'y': 'int'}} SELECT x FROM t, UNNEST(arr) AS x
OK                 bigquery  {} SELECT x FROM t, UNNEST(arr) AS x
OptimizeError      bigquery  {'other': {'x': 'int'}} SELECT (SELECT x FROM UNNEST(arr) AS x) FROM t
OptimizeError      bigquery  {'t': {'y': 'int'}} SELECT (SELECT x FROM UNNEST(arr) AS x) FROM t
OptimizeError      bigquery  {'other': {'x': 'int'}} WITH c AS (SELE
…[703 chars elided]…
nt'}} SELECT x FROM (SELECT arr FROM t) s LATERAL VIEW EXPLODE(arr) e AS x
OK                 spark     {'t': {'arr': 'array<int>'}} SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x WHERE x > 1
OK                 spark     {'t': {'arr': 'array<int>'}} SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x
OptimizeError      presto    {'other': {'x': 'int'}} SELECT x FROM t CROSS JOIN UNNEST(arr) AS u(x)
OptimizeError      trino     {'other': {'x': 'int'}} SELECT x FROM t CROSS JOIN UNNEST(arr) AS u(x)
[assistant] Every shape now terminates. The task also names UNNEST, and my BigQuery cases never recursed even before the fix, so I want to confirm the original code actually recursed on some UNNEST shape. I'll run the sweep against a copy of the package at HEAD.
[tool_use Bash] {"command": "rm -rf /tmp/orig && mkdir -p /tmp/orig && cp -r sqlglot /tmp/orig/ && git show HEAD:sqlglot/optimizer/resolver.py > /tmp/orig/sqlglot/optimizer/resolver.py && cd /tmp/orig && sed 's#sys.path.insert(0, \".\")#sys.path.insert(0, \"/tmp/orig\")#' /tmp/sweep.py > /tmp/sweep_orig.py && <work>/env-sqlglot/bin/python -I /tmp/sweep_orig.py", "description": "Run the sweep against the original resolver at HEAD"}
[tool_result] OptimizeError      bigquery  {'other': {'x': 'int'}} SELECT x FROM t, UNNEST(arr) AS x
OptimizeError      bigquery  {'t': {'y': 'int'}} SELECT x FROM t, UNNEST(arr) AS x
OK                 bigquery  {} SELECT x FROM t, UNNEST(arr) AS x
OptimizeError      bigquery  {'other': {'x': 'int'}} SELECT (SELECT x FROM UNNEST(arr) AS x) FROM t
OptimizeError      bigquery  {'t': {'y': 'int'}} SELECT (SELECT x FROM UNNEST(arr) AS x) FROM t
OptimizeError      bigquery  {'other': {'x': 'int'}} WITH c AS (SELE
…[835 chars elided]…
 SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x WHERE x > 1
OK                 spark     {'t': {'arr': 'array<int>'}} SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x
OptimizeError      presto    {'other': {'x': 'int'}} SELECT x FROM t CROSS JOIN UNNEST(arr) AS u(x)
OptimizeError      trino     {'other': {'x': 'int'}} SELECT x FROM t CROSS JOIN UNNEST(arr) AS u(x)
Shell cwd was reset to ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1
[assistant] The original recurses on the Spark `EXPLODE` shapes, which the fix covers. None of my BigQuery UNNEST shapes recursed, but the report names UNNEST, so I'll try a few more nested and self-referencing BigQuery forms against both versions.
[tool_use Bash] {"command": "cat > /tmp/sweep_bq.py <<'EOF'\nimport sys\nsys.path.insert(0, ROOT)\nimport sqlglot\nfrom sqlglot.optimizer import optimize\ncases = [\n \"SELECT x FROM t, UNNEST(x) AS x\",\n \"SELECT x FROM t, UNNEST(t.arr) AS x\",\n \"SELECT x FROM (SELECT 1 AS a) s, UNNEST(arr) AS x\",\n \"SELECT * FROM (SELECT y FROM t, UNNEST(arr) AS x) q\",\n \"SELECT x FROM t, UNNEST(arr) AS x, UNNEST(x) AS z
…[659 chars elided]…
")\nEOF\necho \"== fixed\"; <work>/env-sqlglot/bin/python -I -c \"ROOT='.'; exec(open('/tmp/sweep_bq.py').read())\"; echo \"== original\"; <work>/env-sqlglot/bin/python -I -c \"ROOT='/tmp/orig'; exec(open('/tmp/sweep_bq.py').read())\"", "description": "Compare BigQuery UNNEST shapes on fixed and original code"}
[tool_result] == fixed
OptimizeError {'other': {'x': 'int'}} SELECT x FROM t, UNNEST(x) AS x
OptimizeError {'t': {'y': 'int'}} SELECT x FROM t, UNNEST(x) AS x
OptimizeError {'t': {'arr': 'array<int>'}} SELECT x FROM t, UNNEST(x) AS x
OK           {'other': {'x': 'int'}} SELECT x FROM t, UNNEST(t.arr) AS x
OptimizeError {'t': {'y': 'int'}} SELECT x FROM t, UNNEST(t.arr) AS x
OK           {'t': {'arr': 'array<int>'}} SELECT x FROM t, UNNEST(t.arr) AS x
OptimizeError {'other': {'x': 'int'}} SELECT x FROM (SELECT
…[3790 chars elided]…
OptimizeError {'t': {'y': 'int'}} SELECT x FROM t WHERE EXISTS (SELECT 1 FROM UNNEST(arr) AS x)
OptimizeError {'t': {'arr': 'array<int>'}} SELECT x FROM t WHERE EXISTS (SELECT 1 FROM UNNEST(arr) AS x)
OptimizeError {'other': {'x': 'int'}} WITH c AS (SELECT * FROM t) SELECT x FROM c, UNNEST(arr) AS x
OptimizeError {'t': {'y': 'int'}} WITH c AS (SELECT * FROM t) SELECT x FROM c, UNNEST(arr) AS x
OK           {'t': {'arr': 'array<int>'}} WITH c AS (SELECT * FROM t) SELECT x FROM c, UNNEST(arr) AS x
[assistant] BigQuery UNNEST doesn't recurse on any shape I tried, before or after the fix, so the reproducible recursion is the Spark/Hive `LATERAL VIEW EXPLODE` path. The UNNEST branch uses the same helper and now also excludes its own source, so it's covered by the same guard, but I didn't find a UNNEST input that recursed. Next I'll add regression tests, checking the existing fixtures first so I follow their format.
[tool_use Bash] {"command": "grep -rn -i \"explode\" tests/fixtures/optimizer/qualify_columns.sql | head; grep -n \"def test_.*\\(qualify\\|lateral\\|explode\\|unnest\\)\" tests/test_optimizer.py | head -30; grep -n \"def test_\" tests/test_optimizer.py | head -5", "description": "Locate existing qualify and explode tests"}
[tool_result] tests/fixtures/optimizer/qualify_columns.sql:806:SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:807:SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:810:SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:811:SELECT _0.c AS c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:814:SELECT c FROM x LATERAL VIEW 
…[654 chars elided]…
queries(self):
1691:    def test_lateral_annotation(self):
2006:    def test_unnest_annotation(self):
2048:    def test_unnest_struct_field_annotation(self):
2421:    def test_qualify_group_by_conflict_bigquery(self):
2451:    def test_bigquery_unnest_alias_shadowing(self):
228:    def test_optimize(self, logger):
247:    def test_isolate_table_selects(self):
254:    def test_qualify_tables(self):
315:    def test_qualify_tables_copies_typed_alias_columns(self):
328:    def test_normalize(self):
[assistant] The fixtures are the natural place for the regression case. I'll look at the test near line 2451 for the style used for schema-based cases.
[tool_use Bash] {"command": "sed -n 2451,2480p tests/test_optimizer.py; sed -n 800,812p tests/fixtures/optimizer/qualify_columns.sql; sed -n 357,375p tests/test_optimizer.py", "description": "Read existing test style for qualify with schema"}
[tool_result]     def test_bigquery_unnest_alias_shadowing(self):
        """Test that BigQuery UNNEST table alias shadows column names from other tables."""
        sql = """
            SELECT timeline_date
            FROM UNNEST(GENERATE_DATE_ARRAY('2020-01-01', '2020-01-03')) AS timeline_date
            LEFT JOIN production_tier ON production_tier.timeline_date = timeline_date
        """
        schema = {"production_tier": {"timeline_date": "DATE", "id": "INT"}}

        result = optimizer.qualify.qua
…[1547 chars elided]…
       FROM raw.TeamMemberships as TeamMemberships
                    join raw.Teams
                        on Teams.Id = TeamMemberships.TeamId
                    GROUP BY 1
                    """,
                    read="bigquery",
                ),
                schema={
                    "raw": {
                        "TeamMemberships": {
                            "Id": "INTEGER",
                            "UserId": "INTEGER",
                            "TeamId": "INTEGER",
[assistant] I'll add a regression test next to the BigQuery alias-shadowing test. It covers the Spark EXPLODE case with the table missing (must raise a normal `OptimizeError`, not recurse) and with the table present (must qualify correctly). I'll check the test file's imports first.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|OptimizeError\" tests/test_optimizer.py | head -30", "description": "Check test file imports for OptimizeError"}
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
13:from sqlglot.optimizer.canonicalize_internal_names import canonicali
…[203 chars elided]…
lk_in_scope
17:from sqlglot.schema import MappingSchema
18:from tests.helpers import (
697:            OptimizeError, "Column 'foo' could not be resolved. Line: 1, Col: 10"
705:        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
766:                with self.assertRaises((OptimizeError, SchemaError)):
790:        with self.assertRaises(OptimizeError) as ctx:
804:        with self.assertRaises(OptimizeError) as ctx:
814:        with self.assertRaises(OptimizeError) as ctx:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "    def test_struct_field_case_sensitivity_annotation(self):", "new_string": "    def test_lateral_explode_unqualified_column_recursion(self):\n        sql = \"SELECT x FROM t LATERAL VIEW EXPLODE(arr) e AS x\"\n\
…[492 chars elided]…
r.optimize(\n            parse_one(sql, read=\"spark\"),\n            schema={\"t\": {\"arr\": \"array<int>\"}},\n            dialect=\"spark\",\n        )\n        self.assertEqual(\n            result.sql(dialect=\"spark\"),\n            \"SELECT `e`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) e AS `x`\",\n        )\n\n    def test_struct_field_case_sensitivity_annotation(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101448-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now the project's check command, which is the full pytest suite with the given interpreter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run the project test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[278 chars elided]…
. [ 64%]
................................................................................................................................................................................................................................................ [ 85%]
........................................................... [ 91%]
.................................. [ 94%]
................. [ 95%]
................................................          [100%]
1121 passed, 18166 subtests passed in 56.18s
[assistant] All 1121 tests pass, including the new one. The repo also runs a style check, so I'll run ruff and mypy on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py 2>&1 | tail -3; $PY -m mypy sqlglot/optimizer/resolver.py 2>&1 | tail -3; git status --short", "description": "Run ruff and mypy on changed files"}
[tool_result] All checks passed!
2 files already formatted
Success: no issues found in 1 source file
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
[assistant] Fixed: qualifying a Spark/Hive `LATERAL VIEW EXPLODE(arr)` with an unqualified `arr` no longer recurses, whether or not the table is in the schema. The full suite passes (1121 tests), and ruff and mypy are clean on the changed files. I haven't committed.

**Cause:** In `sqlglot/optimizer/resolver.py`, resolving the lateral's input column `arr` builds a resolver over the parent scope. That resolver needs every source's columns, including the lateral `e` itself, whose columns call back into the same lookup. Nothing breaks the cycle.

**Fix:** Each resolver now takes an `excluded_sources` set. Wh
…[531 chars elided]…
 checked that you should know:
- **Snowflake `LATERAL FLATTEN`** never recursed. Its argument parses as a `Kwarg`, not a column, so it fails with a normal `OptimizeError`.
- **BigQuery `UNNEST`** didn't recurse on any shape I tried, before or after the fix. I changed its branch to use the same exclusion because it shares the helper, but I didn't reproduce a recursion there. If you have a specific UNNEST query that crashed, send it and I'll check it against this fix.
- **`sqlglot[c]`** (mypyc-compiled) isn't built or tested here. The change is plain Python, but the compiled build is unverified.
