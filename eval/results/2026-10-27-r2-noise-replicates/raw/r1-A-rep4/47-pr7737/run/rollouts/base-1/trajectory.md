# trajectory base-1

final message:
Qualifying a query that explodes an unqualified column through a missing table no longer recurses. The full suite passes (1120 tests), and the new regression test fails on unmodified HEAD with `RecursionError` and passes with the fix.

**What was happening:** The recursion was not in the `FLATTEN`/`UNNEST` paths I tried first. The cycle is `Resolver.get_source_columns` (for a lateral view) → `_get_unnest_column_type` → a fresh `Resolver` on the same scope → `get_table`, which needs the columns of every lateral in that scope, including the one being typed. I reproduced it with Spark/Hive `LATERAL VIEW EXPLODE(a)` where `a` is unqualified, the table is missing from the schema, and `infer_schema=False`.

**The fix** (`sqlglot/optimizer/resolver.py`): `_get_unnest_column_type` now tracks the ids of explode/unnest argument columns currently being typed. A re-entrant request for the same column returns `None`, and the set is passed to the nested resolver. The cycle always revisits the same argument node, so this breaks it without changing results for the non-cyclic cases.

**Tests** (`tests/test_optimizer.py`): added `test_qualify_columns__unnest_unqualified_column_missing_table`. It asserts the missing-table case raises `OptimizeError` (the ordinary "could not be resolved" error), and that the present-table case still qualifies.

**Things to know:**
- I did not reproduce recursion with the exact `LATERAL FLATTEN` (Snowflake) or `UNNEST` (BigQuery, DuckDB, Presto) shapes; those raise `OptimizeError` or qualify normally. The fix sits in the shared path both lateral explode and UNNEST go through, so it covers them too, but I did not verify those shapes beyond the fuzz I ran.
- I did not test the `sqlglot[c]` compiled build. The change is pure Python, so the mypyc build should be unaffected, but that is unverified.
- Lint is clean (ruff, and mypy on `resolver.py`). I did not commit anything.

## events
[assistant] I'll start by reproducing the recursion in the qualifier, then trace it through the column resolver.
[tool_use Bash] {"command": "git status --short && grep -n \"def \\|Unnest\\|Lateral\\|Flatten\\|_expand_stars\\|def _get_unambiguous\" sqlglot/optimizer/qualify_columns.py | head -120", "description": "Check git status and list qualify_columns functions"}
[tool_result] 21:def qualify_columns(
96:                _expand_stars(
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
162:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
184:def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
198:def _expand_using(scope: Scope, resolver: Resolver) -> dict[str, t.Any]:
201:    def _update_source_columns(source_name: str) -> None:
302:def _expand_alias_refs(
320:    def replace_columns(
422:def _
…[806 chars elided]…
s:
755:    for struct_field_def in t.cast(exp.DataType, starting_struct).expressions:
764:def _expand_stars(
881:def _add_except_columns(expression: exp.Expr, tables, except_columns: dict[int, set[str]]) -> None:
893:def _add_rename_columns(
907:def _add_replace_columns(
921:def qualify_outputs(scope_or_expression: Scope | exp.Expr) -> None:
961:def quote_identifiers(expression: E, dialect: DialectType = None, identify: bool = True) -> E:
974:def pushdown_cte_alias_columns(scope: Scope) -> None:
[tool_use Bash] {"command": "cat > /tmp/repro_qual.py <<'EOF'\nimport sys\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"db\": {\"t\": {\"a\": \"ARRAY<INT>\"}}}\nsqls = [\n  (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => a) f\"),\n  (\"snowflake\", \"SELECT f.value FROM missing, LATERAL FLATTEN(input => a) f\"),\n  (\"bigquery\", \"SELECT x FROM UNNES
…[197 chars elided]…
cept RecursionError as e:\n        print(\"RecursionError:\", s)\n    except Exception as e:\n        print(type(e).__name__, e, \"|\", s)\nEOF\ntimeout 60 <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_qual.py').read())\" 2>&1 | tail -20", "description": "Check worktree state and reproduce the recursion"}
[tool_result] (eval):20: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_qual.py').read())\" 2>&1 | tail -20", "description": "Run reproduction script against worktree sources"}
[tool_result] snowflake SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN(input => "T"."A") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
OptimizeError Column 'A' could not be resolved. Line: 1, Col: 55 | SELECT f.value FROM missing, LATERAL FLATTEN(input => a) f
OptimizeError Column 'a' could not be resolved. Line: 1, Col: 22 | SELECT x FROM UNNEST(a) AS x
OptimizeError Column 'a' could not be resolved. Line: 1, Col: 31 | SELECT x FROM missing, UNNEST(a) AS x
[assistant] The simple cases don't recurse, so the trigger is more specific. I'll look at how the resolver handles UNNEST and LATERAL sources.
[tool_use Bash] {"command": "grep -n \"Unnest\\|Lateral\\|Flatten\\|_get_source_columns\\|def get_source_columns\\|def _get_all_source_columns\\|def get_unambiguous\\|def all_columns\\|def get_table\\|def _get_table_name\" sqlglot/optimizer/resolver.py sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -80", "description": "Find UNNEST/LATERAL handling in resolver and scope"}
[tool_result] sqlglot/optimizer/resolver.py:32:        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}
sqlglot/optimizer/resolver.py:34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
sqlglot/optimizer/resolver.py:87:    def all_columns(self) -> set[str]:
sqlglot/optimizer/resolver.py:95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
sqlglot/optimizer/resolver.py:133:    def get_source_columns(self, name: str, only_visibl
…[1029 chars elided]…
xplode, exp.Unnest)
sqlglot/optimizer/qualify_columns.py:651:    """[BigQuery] Expand/Flatten foo.bar.* where bar is a struct column"""
sqlglot/optimizer/qualify_columns.py:703:    """[RisingWave] Expand/Flatten (<exp>.bar).*, where bar is a struct column"""
sqlglot/optimizer/scope.py:209:            elif type(node) is exp.Lateral or (
sqlglot/optimizer/scope.py:919:    if isinstance(scope.expression, exp.Unnest):
sqlglot/optimizer/scope.py:921:    elif isinstance(scope.expression, exp.Lateral):
[tool_use Bash] {"command": "sed -n 25,260p sqlglot/optimizer/resolver.py", "description": "Read resolver source-column and table-name logic"}
[tool_result]         self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | None = None
        self._infer_schema: bool = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}

    def get_table(self, column: str | exp.Column) -
…[10124 chars elided]…
on.args
        joins = args.get("joins")

        if not joins or args.get("laterals") or args.get("pivots"):
            # Feature gap: We currently don't try to disambiguate columns if other sources
            # (e.g laterals, pivots) exist alongside joins
            return None

        join_ancestor = column.find_ancestor(exp.Join, exp.Select)

        if (
            isinstance(join_ancestor, exp.Join)
            and join_ancestor.alias_or_name in self.scope.selected_sources
        ):
[assistant] The BigQuery branch calls `_get_unnest_column_type` against the parent scope, which could re-enter the resolver. I'll read that helper and the other UNNEST site.
[tool_use Bash] {"command": "sed -n 260,360p sqlglot/optimizer/resolver.py; grep -n \"_get_unnest_column_type\" -A25 sqlglot/optimizer/resolver.py | sed -n '/def _get_unnest/,$p' | head -40", "description": "Read unnest column-type helper and related resolver code"}
[tool_result]         ):
            # Ensure that the found ancestor is a join that contains an actual source,
            # e.g in Clickhouse `b` is an array expression in `a ARRAY JOIN b`
            return join_ancestor

        return None

    def _get_available_source_columns(self, join_ancestor: exp.Join) -> dict[str, Sequence[str]]:
        """
        Get the source columns that are available at the point where a column is referenced.

        For columns in JOIN conditions, this only includes table
…[4313 chars elided]…
esolver to disambiguate the column
379-            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
380-            table_identifier = parent_resolver.get_table(column)
381-            if not table_identifier:
382-                return None
383-            table_name = table_identifier.name
384-
385-        source = scope.sources.get(table_name)
386-        return self._get_column_type_from_scope(source, column) if source else None
387-
388-    def _get_column_type_from_scope(
[assistant] `_get_unnest_column_type` builds a new resolver on `scope.parent` and resolves the same unqualified column there, so re-entry looks plausible. I'll brute-force a set of variants (UNNEST/FLATTEN, qualified and unqualified, missing table, nested scopes) to find one that actually recurses.
[tool_use Bash] {"command": "cat > /tmp/fuzz_qual.py <<'EOF'\nimport sys\nsys.setrecursionlimit(400)\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {\"t\": {\"a\": \"ARRAY<INT64>\", \"s\": \"STRUCT<x INT64>\"}}\ncases = [\n (\"bigquery\", \"SELECT x FROM missing, UNNEST(a) AS x\"),\n (\"bigquery\", \"SELECT x FROM missing AS m, UNNEST(a) AS x\"),\n (\"bigquery\", \"SELECT 
…[1943 chars elided]…
or:\n        r = \"RECURSION\"\n    except Exception as e:\n        r = type(e).__name__\n    print(f\"infer={infer!s:5} {r:22} {d:10} {s}\")\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/fuzz_qual.py').read())\" 2>&1 | tail -70", "description": "Fuzz qualify across UNNEST/FLATTEN variants for recursion"}
[tool_result] infer=True  ok                     bigquery   SELECT x FROM missing, UNNEST(a) AS x
infer=True  ok                     bigquery   SELECT x FROM missing AS m, UNNEST(a) AS x
infer=True  ok                     bigquery   SELECT * FROM (SELECT x FROM missing, UNNEST(a) AS x)
infer=True  ok                     bigquery   WITH c AS (SELECT x FROM missing, UNNEST(a) AS x) SELECT * FROM c
infer=True  ok                     bigquery   SELECT (SELECT x FROM missing, UNNEST(a) AS x) FROM t
infer=True  ok 
…[3965 chars elided]…
put => a) f WHERE TRUE
infer=False OptimizeError          duckdb     SELECT x FROM missing, UNNEST(a) AS x
infer=False OptimizeError          duckdb     SELECT x FROM missing CROSS JOIN LATERAL UNNEST(a) AS x
infer=False OptimizeError          presto     SELECT x FROM missing CROSS JOIN UNNEST(a) AS x
infer=False RECURSION              spark      SELECT x FROM missing LATERAL VIEW EXPLODE(a) v AS x
infer=False RECURSION              hive       SELECT x FROM missing LATERAL VIEW EXPLODE(a) v AS x
[assistant] Found a real reproduction: Spark/Hive `LATERAL VIEW EXPLODE` with an unqualified column, a missing table, and `infer_schema=False` gives a `RecursionError`. I'll pull the traceback to see the cycle.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nschema = {'t': {'a': 'ARRAY<INT64>', 's': 'STRUCT<x INT64>'}}\nqualify(parse_one('SELECT x FROM missing LATERAL VIEW EXPLODE(a) v AS x', read='spark'), schema=schema, dialect='spark', infer_schema=False)\n\" 2>&1 | grep -o 'File \"[^\"]*\", line [0-9]*, in [a-z_A-Z]*' | uniq -c | head -40", "description": "Get the recursion cycle from traceback"}
[tool_result]    1 File "<string>", line 6, in 
   1 File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify.py", line 98, in qualify
   1 File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
   1 File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-
…[6264 chars elided]…
repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 182, in get_source_columns
   1 File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 380, in _get_unnest_column_type
   1 File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 45, in get_table
[assistant] The cycle is clear. `get_source_columns` for a lateral `v` (the `EXPLODE` branch) calls `_get_unnest_column_type(a, S)`. That builds a fresh `Resolver(S)`, whose `get_table` computes the columns of every lateral in `S`, including `v`, which brings us back to the start. The argument of a lateral should only be resolvable against sources that precede it, so I'll check how `lateral_sources` is built to see whether that ordering is available.
[tool_use Bash] {"command": "grep -n \"lateral_sources\\|selected_sources\" sqlglot/optimizer/scope.py | head -30; sed -n 195,235p sqlglot/optimizer/scope.py", "description": "Inspect how lateral_sources and selected_sources are built"}
[tool_result] 60:        lateral_sources: Sources from laterals
94:    _selected_sources: dict[str, tuple[exp.Selectable, exp.Table | Scope]] | None
108:        lateral_sources: dict[str, exp.Table | Scope] | None = None,
114:        self.lateral_sources = lateral_sources or {}
116:        self.sources.update(self.lateral_sources)
144:        self._selected_sources = None
157:        lateral_sources: dict[str, exp.Table | Scope] | None = None,
167:            lateral_sources=lateral_sources.copy() if lateral_
…[1806 chars elided]…
     node.args.get("except_") or not isinstance(node.parent, ROW_LEVEL_AGG_FUNCS)
            ):
                self._scans_all_subscope_columns = True

        self._collected = True

    def _ensure_collected(self) -> None:
        if not self._collected:
            self._collect()

    def walk(self, prune: t.Callable[[exp.Expr], bool] | None = None) -> Iterator[exp.Expr]:
        return walk_in_scope(self.expression, prune=prune)

    def find(self, *expression_types: Type[E]) -> E | None:
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | head; sed -n 14,24p sqlglot/optimizer/resolver.py; sed -n 860,875p sqlglot/optimizer/scope.py", "description": "Find Resolver constructor callers and lateral source construction"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
    from collections.abc import Sequence, Mapping


class Resolver:
    """
    Helper for resolving columns.

    This is a class so we can lazily load some things and easily share them a
…[244 chars elided]…
id DerivedTable/UDTF trait vtable dispatch
        node: exp.Expr = expression

        if isinstance(expression, exp.UDTF):
            lateral_sources = sources
            scope_type = ScopeType.UDTF
            scopes = scope.udtf_scopes
        elif _is_derived_table(expression):
            lateral_sources = None
            scope_type = ScopeType.DERIVED_TABLE
            scopes = scope.derived_table_scopes
            expressions.extend(join.this for join in node.args.get("joins") or [])
[assistant] The cycle always re-enters through `_get_unnest_column_type` with the same explode-argument `Column` node, so I can break it there. I'll guard that call by node identity and share the in-progress set with the nested resolver. Let me read the rest of the helper first.
[tool_use Bash] {"command": "sed -n 362,420p sqlglot/optimizer/resolver.py", "description": "Read unnest column type helper in full"}
[tool_result]     def _get_unnest_column_type(self, column: exp.Column, scope: Scope) -> exp.DataType | None:
        """
        Get the type of a column being unnested/exploded, tracing through CTEs/subqueries to find the base table.

        Args:
            column: The column expression being unnested/exploded.
            scope: The scope to resolve the column in.

        Returns:
            The DataType of the column, or None if not found.
        """
        # if column is qualified, use that table,
…[1225 chars elided]…
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
[assistant] Now I'll make the change: a shared in-progress set of explode-argument nodes, checked on entry to `_get_unnest_column_type`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "        # if column is qualified, use that table, otherwise disambiguate using the resolver\n        if column.table:\n            table_name = column.table\n        else:\n            # use the parent scope
…[1363 chars elided]…
entifier = parent_resolver.get_table(column)\n                if not table_identifier:\n                    return None\n                table_name = table_identifier.name\n\n            source = scope.sources.get(table_name)\n            return self._get_column_type_from_scope(source, column) if source else None\n        finally:\n            self._unnest_columns_in_progress.discard(id(column))"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.dia
…[871 chars elided]…
None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # ids of unnest/explode argument columns being typed up the stack, shared with nested resolvers\n        self._unnest_columns_in_progress: set[int] = (\n            set() if unnest_columns_in_progress is None else unnest_columns_in_progress\n        )"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:     def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:

        self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, str] | None = None
        self._all_columns: set[str] | None = None
        self._infer_schema: bool = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}</tool_use_error>
[assistant] The second edit's match failed, so I'll re-read the constructor to see the exact text.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "offset": 17, "limit": 22}
[tool_result] 17	class Resolver:
18	    """
19	    Helper for resolving columns.
20	
21	    This is a class so we can lazily load some things and easily share them across functions.
22	    """
23	
24	    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
25	        self.scope: Scope = scope
26	        self.schema: Schema = schema
27	        self.dialect: Dialect = schema.dialect or Dialect()
28	        self._source_columns: dict[str, Sequence[str]] | None = None
29	        self._unambiguous_columns: Mapping[str, str] | None = None
30	        self._all_columns: set[str] | None = None
31	        self._infer_schema: bool = infer_schema
32	        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}
33	
34	    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
35	        """
36	        Get the table for a column name.
37	
38	        Args:
[assistant] The blank line I assumed isn't there. Retrying with the exact text:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[867 chars elided]…
None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # ids of unnest/explode argument columns being typed up the stack, shared with nested resolvers\n        self._unnest_columns_in_progress: set[int] = (\n            set() if unnest_columns_in_progress is None else unnest_columns_in_progress\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[assistant] Now I'll re-run the fuzz, adding sibling and chained lateral shapes, and compare against the baseline.
[tool_use Bash] {"command": "cat >> /tmp/fuzz_qual.py <<'EOF'\nprint(\"--- extra\")\nextra = [\n (\"spark\", \"SELECT x, y FROM missing LATERAL VIEW EXPLODE(a) v AS x LATERAL VIEW EXPLODE(x) w AS y\"),\n (\"spark\", \"SELECT * FROM missing LATERAL VIEW EXPLODE(a) v AS x\"),\n (\"spark\", \"SELECT * FROM t LATERAL VIEW EXPLODE(a) v AS x\"),\n (\"spark\", \"SELECT x FROM missing LATERAL VIEW EXPLODE(missing.a) v AS
…[679 chars elided]…
pen('/tmp/fuzz_qual.py').read())\" 2>&1 | grep -v \"^infer=True  ok\\|^infer=False ok\" ; echo; echo \"--- infer=False rows with spark/hive:\"; <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/fuzz_qual.py').read())\" 2>&1 | grep \"spark\\|hive\" ", "description": "Re-run fuzz with extra lateral shapes after fix"}
[tool_result] infer=True  OptimizeError          duckdb     SELECT x FROM missing, UNNEST(a) AS x
infer=True  OptimizeError          duckdb     SELECT x FROM missing CROSS JOIN LATERAL UNNEST(a) AS x
infer=True  OptimizeError          presto     SELECT x FROM missing CROSS JOIN UNNEST(a) AS x
infer=False OptimizeError          bigquery   SELECT x FROM missing, UNNEST(a) AS x
infer=False OptimizeError          bigquery   SELECT x FROM missing AS m, UNNEST(a) AS x
infer=False OptimizeError          bigquery   S
…[4366 chars elided]…

infer=False spark  OptimizeError Column 'a' could not be resolved. Line: 1, Col: 44
infer=False spark  ok SELECT `t`.`a` AS `a`, `t`.`s` AS `s`, `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`a`) v AS `x`
infer=False spark  ok SELECT `v`.`x` AS `x` FROM `missing` AS `missing` LATERAL VIEW EXPLODE(`missing`.`a`) v AS `x`
infer=False spark  OptimizeError Column 'a' could not be resolved. Line: 1, Col: 59
infer=False hive   OptimizeError Column 'a' could not be resolved. Line: 1, Col: 44
[assistant] No recursion in any shape now. The Spark/Hive `infer_schema=False` case that used to recurse fails with the ordinary "Column could not be resolved" error, matching the other dialects. Next I'll run the project's test command in the background while I find where to add a regression test.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/ > /tmp/pytest_after.log 2>&1; echo \"exit=$?\" >> /tmp/pytest_after.log; tail -5 /tmp/pytest_after.log", "description": "Run full pytest suite with the fix applied", "run_in_background": true}
[tool_result] Command running in background with ID: bo2pe705q. Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-d5521a213087-20261029-081038-optimizer-sqlglot-optimizer-qual-base-1/4c04b06e-9590-49e8-9aaf-aae9cfe85b4e/tasks/bo2pe705q.output. You will be notified when it completes. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "grep -n \"def test_qualify_columns\\|def test_unnest\\|def test_lateral\\|def test_qualify\\b\\|def test_.*lateral\" tests/test_optimizer.py | head; grep -n \"LATERAL VIEW EXPLODE\" tests/fixtures/optimizer/qualify_columns.sql | head -5; grep -n \"unnest\\|UNNEST\" tests/fixtures/optimizer/qualify_columns.sql | head -3", "description": "Find qualify test locations and lateral fixtures"}
[tool_result] 357:    def test_qualify_columns(self, logger):
753:    def test_qualify_columns__with_invisible(self):
763:    def test_qualify_columns__invalid(self):
941:    def test_unnest_subqueries(self):
1691:    def test_lateral_annotation(self):
2006:    def test_unnest_annotation(self):
2048:    def test_unnest_struct_field_annotation(self):
806:SELECT c FROM x LATERAL VIEW EXPLODE (a) AS c;
807:SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
810:SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
811:SELECT _0.c AS c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
814:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
131:SELECT (SELECT MIN(a) FROM UNNEST([1, 2])) AS f FROM x GROUP BY 1;
132:SELECT (SELECT MIN(_0.a) AS _col_0 FROM UNNEST(ARRAY(1, 2)) AS _0) AS f FROM x AS x GROUP BY 1;
818:SELECT aa FROM x, UNNEST(a) AS t(aa);
[tool_use Bash] {"command": "sed -n 753,775p tests/test_optimizer.py", "description": "Read nearby qualify test for style"}
[tool_result]     def test_qualify_columns__with_invisible(self):
        schema = MappingSchema(self.schema, {"x": {"a"}, "y": {"b"}, "z": {"b"}})
        self.check_file("qualify_columns__with_invisible", qualify_columns, schema=schema)

    def test_pushdown_cte_alias_columns(self):
        self.check_file(
            "pushdown_cte_alias_columns",
            pushdown_ctes,
        )

    def test_qualify_columns__invalid(self):
        for sql in load_sql_fixtures("optimizer/qualify_columns__invalid.sql"
…[56 chars elided]…
ith self.assertRaises((OptimizeError, SchemaError)):
                    expression = optimizer.qualify_columns.qualify_columns(
                        parse_one(sql), schema=self.schema
                    )
                    optimizer.qualify_columns.validate_qualify_columns(expression)

        # this makes sure the fallback scenario in get_table in resolver is covered
        # and the error message is column cannot be resolved instead of unknown table
        sql = """
            SELECT
[assistant] I'll add a regression test next to the existing qualify column tests. It covers the missing-table case (which must raise the normal error, not recurse) and the present-table case (which must still qualify).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "    def test_qualify_columns__with_invisible(self):\n        schema = MappingSchema(self.schema, {\"x\": {\"a\"}, \"y\": {\"b\"}, \"z\": {\"b\"}})\n        self.check_file(\"qualify_columns__with_invisible\", qual
…[820 chars elided]…
    expression = optimizer.qualify_columns.qualify_columns(\n            parse_one(\"SELECT x FROM t LATERAL VIEW EXPLODE(a) v AS x\", read=\"spark\"),\n            schema=schema,\n            infer_schema=False,\n        )\n        self.assertEqual(\n            expression.sql(\"spark\"),\n            \"SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`a`) v AS `x`\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | tail -5", "description": "Run the new regression test"}
[tool_result] tests/test_optimizer.py:762: AssertionError
=========================== short test summary info ============================
FAILED tests/test_optimizer.py::TestOptimizer::test_qualify_columns__unnest_unqualified_column_missing_table
1 failed, 79 deselected in 0.23s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | grep -B3 \"AssertionError\" | head -30", "description": "Show the assertion failure detail"}
[tool_result] >       with self.assertRaises(OptimizeError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AssertionError: OptimizeError not raised

tests/test_optimizer.py:762: AssertionError
[assistant] The test expected an error but none was raised. My fuzz used `qualify(..., dialect="spark")` and this test calls `qualify_columns` with the default dialect, so I'll check what it actually produces.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import qualify_columns as qc\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'t': {'a': 'ARRAY<INT>'}})\nfor sql in ['SELECT x FROM missing LATERAL VIEW EXPLODE(a) v AS x']:\n    print(qc.qualify_col
…[223 chars elided]…
 sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'t': {'a': 'ARRAY<INT>'}})\nprint(qualify(parse_one('SELECT x FROM missing LATERAL VIEW EXPLODE(a) v AS x', read='spark'), schema=s, infer_schema=False).sql('spark'))\n\" 2>&1 | tail -3", "description": "Compare qualify_columns vs qualify outputs for the test SQL"}
[tool_result] SELECT v.x AS x FROM missing LATERAL VIEW EXPLODE(a) v AS x
  File "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", line 139, in validate_qualify_columns
    raise OptimizeError(error_msg)
sqlglot.errors.OptimizeError: Column 'a' could not be resolved. Line: 1, Col: 44
[assistant] The error comes from `validate_qualify_columns`, which `qualify()` runs but bare `qualify_columns` does not. The existing `test_qualify_columns__invalid` pattern calls both, so I'll match it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        with self.assertRaises(OptimizeError):\n            optimizer.qualify_columns.qualify_columns(\n                parse_one(sql, read=\"spark\"), schema=schema, infer_schema=False\n            )\n", "new_string": "        with self.assertRaises(OptimizeError):\n            expression = optimizer.qualify_columns.qualify_columns(\n                parse_one(sql, read=\"spark\"), schema=schema, infer_schema=False\n            )\n            optimizer.qualify_columns.validate_qualify_columns(expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | tail -2; cat /tmp/pytest_after.log 2>/dev/null | tail -3", "description": "Re-run regression test and check background suite status"}
[tool_result] FAILED tests/test_optimizer.py::TestOptimizer::test_qualify_columns__unnest_unqualified_column_missing_table
1 failed, 79 deselected in 0.23s
............................ [ 51%]
................................................................................................................................................... [ 64%]
........................................................
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | grep -E \"^E |Error|test_optimizer.py:[0-9]+\" | head -12", "description": "Show the new failure detail"}
[tool_result]         with self.assertRaises(OptimizeError):
E       AssertionError: 'SELECT v.x AS x FROM t LATERAL VIEW EXPLODE(t.a) v AS x' != 'SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`a`) v AS `x`'
E       - SELECT v.x AS x FROM t LATERAL VIEW EXPLODE(t.a) v AS x
E       + SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`a`) v AS `x`
E       ?        + + + +    + +      + ++++++++                      + + + +       + +
tests/test_optimizer.py:773: AssertionError
[assistant] The qualification is correct; only my expected string was wrong (`qualify_columns` alone doesn't quote identifiers). Correcting the expectation:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "            \"SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`a`) v AS `x`\",", "new_string": "            \"SELECT v.x AS x FROM t LATERAL VIEW EXPLODE(t.a) v AS x\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | tail -1; tail -3 /tmp/pytest_after.log", "description": "Confirm regression test passes; check full run"}
[tool_result] 1 passed, 79 deselected in 0.30s
............................ [ 51%]
................................................................................................................................................... [ 64%]
...........................................................................................................................................................................................................................................
[assistant] The regression test passes. To confirm it actually catches the bug, I'll run it against an untouched HEAD copy extracted to a scratch directory, leaving the worktree alone.
[tool_use Bash] {"command": "rm -rf /tmp/orig_head && mkdir /tmp/orig_head && git archive HEAD | tar -x -C /tmp/orig_head && cp tests/test_optimizer.py /tmp/orig_head/tests/test_optimizer.py && cd /tmp/orig_head && <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); import sqlglot; print(sqlglot.__file__)\" && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k unnest_unqualified_column_missing_table 2>&1 | grep -E \"RecursionError|passed|failed\" | tail -2", "description": "Confirm the new test fails on unmodified HEAD sources"}
[tool_result] /private/tmp/orig_head/sqlglot/__init__.py
E   RecursionError: maximum recursion depth exceeded
1 failed, 79 deselected in 0.31s
Shell cwd was reset to ~/.cache/lithify/work/repo-d5521a213087/20261029-081038-optimizer-sqlglot-optimizer-qual/base-1
[assistant] On unmodified HEAD the test fails with `RecursionError`, and it passes with the fix. Next I'll wait for the full suite and run the linter on the two changed files.
[tool_use Bash] {"command": "for i in $(seq 1 50); do grep -q \"^exit=\" /tmp/pytest_after.log && break; sleep 5; done; tail -4 /tmp/pytest_after.log; <work>/env-sqlglot/bin/python -m ruff --version 2>/dev/null && <work>/env-sqlglot/bin/python -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py", "description": "Wait for full test run and lint changed files"}
[tool_result] .............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 52.38s
exit=0
ruff 0.15.6
All checks passed!
2 files already formatted
[assistant] The full suite passed (1120 tests, exit 0), and ruff is clean. I'll run mypy on the changed module, since the project's pre-commit config uses it, and then review the diff.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/optimizer/resolver.py 2>&1 | tail -3; git diff --stat; rm -rf /tmp/orig_head", "description": "Run mypy on resolver and show diff stats"}
[tool_result] Success: no issues found in 1 source file
 sqlglot/optimizer/resolver.py | 52 +++++++++++++++++++++++++++++++------------
 tests/test_optimizer.py       | 21 +++++++++++++++++
 2 files changed, 59 insertions(+), 14 deletions(-)
[assistant] Qualifying a query that explodes an unqualified column through a missing table no longer recurses. The full suite passes (1120 tests), and the new regression test fails on unmodified HEAD with `RecursionError` and passes with the fix.

**What was happening:** The recursion was not in the `FLATTEN`/`UNNEST` paths I tried first. The cycle is `Resolver.get_source_columns` (for a lateral view) → `_get_unnest_column_type` → a fresh `Resolver` on the same scope → `get_table`, which needs the columns of every lateral in that scope, including the one being typed. I reproduced it with Spark/Hive `LATER
…[715 chars elided]…
nt-table case still qualifies.

**Things to know:**
- I did not reproduce recursion with the exact `LATERAL FLATTEN` (Snowflake) or `UNNEST` (BigQuery, DuckDB, Presto) shapes; those raise `OptimizeError` or qualify normally. The fix sits in the shared path both lateral explode and UNNEST go through, so it covers them too, but I did not verify those shapes beyond the fuzz I ran.
- I did not test the `sqlglot[c]` compiled build. The change is pure Python, so the mypyc build should be unaffected, but that is unverified.
- Lint is clean (ruff, and mypy on `resolver.py`). I did not commit anything.
