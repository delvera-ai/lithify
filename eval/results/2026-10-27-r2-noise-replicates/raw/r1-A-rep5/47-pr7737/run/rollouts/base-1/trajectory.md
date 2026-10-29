# trajectory base-1

final message:
Qualifying a lateral column that is unqualified no longer recurses. The pure-Python `RecursionError` is gone, and the full suite passes (1120 tests, plus the new regression test).

**Cause:** `Resolver.get_source_columns` handles a `LATERAL VIEW EXPLODE(col)` source by calling `_get_unnest_column_type`. For an unqualified `col`, that builds a new `Resolver` on the parent scope to find which table `col` belongs to. That resolver calls `_get_all_source_columns`, which includes the same lateral, so the cycle repeats. Each new resolver has its own cache, so nothing stopped it.

**Fix** (`sqlglot/optimizer/resolver.py`): a re-entrancy guard. A set of in-progress column nodes is shared with the child resolvers. If the same unqualified column comes back around, `_get_unnest_column_type` returns `None`, which is the existing "type not found" path. The lateral then gets no inferred struct fields, and the query fails with the normal `OptimizeError` if the column can't be resolved.

**Test** (`tests/test_optimizer.py`, in `test_validate_columns`): covers the missing-table case (expects `OptimizeError`) and the case where the table is in the schema (expects the correct qualified SQL). The test raises `RecursionError` on the original code and passes with the fix.

**Notes:**
- I reproduced the crash with `LATERAL VIEW EXPLODE(v)` (Spark/Hive syntax), not with `LATERAL FLATTEN` or `UNNEST`. Those shapes raise `OptimizeError` in my tests, not `RecursionError`, so the guard doesn't change their behavior. If your report comes from a `FLATTEN` query, send me the exact SQL and schema and I'll check it.
- The compiled `sqlglot[c]` build wasn't exercised. This checkout has no `.so` files, so I couldn't build the mypyc variant. The change is plain Python and should compile under mypyc, but that's unverified.
- Ruff check and format pass on both files.

## events
[assistant] I'll start by reproducing the recursion on the pure-Python build before reading the resolver.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"FLATTEN\\|UNNEST\\|Lateral\\|Unnest\" sqlglot/optimizer/qualify_columns.py | head -60", "description": "Check repo state and find lateral/unnest handling in qualify_columns"}
[tool_result] 69f3ae69e lithify: probe base
518:                    or select_expr.find(exp.Explode, exp.Unnest)
[tool_use Bash] {"command": "cat > /tmp/repro_flatten.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import optimize\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n    (\"SELECT f.value FROM missing_tbl AS t, LATERAL FLATTEN(input => v) AS f\", {\"other\": {\"x\": \"INT\"}}),\n    (\"SELECT x FROM missing_tbl, UNNEST(arr) AS x\", {\"other\": {\
…[273 chars elided]…
=schema, dialect=d)\n            print(\"OK\", d, sql)\n        except RecursionError:\n            print(\"RecursionError\", d, sql)\n        except Exception as e:\n            print(type(e).__name__, d, str(e)[:120])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_flatten.py", "description": "Grep resolver for lateral handling and run repro script"}
[tool_result] OptimizeError snowflake Column 'V' could not be resolved. Line: 1, Col: 64
OptimizeError bigquery Column 'v' could not be resolved. Line: 1, Col: 64
OptimizeError snowflake Column 'X' could not be resolved. Line: 1, Col: 8
OptimizeError bigquery Column 'arr' could not be resolved. Line: 1, Col: 37
OK snowflake SELECT x FROM missing_tbl CROSS JOIN UNNEST(arr) AS u(x)
ParseError bigquery Unexpected extra column alias in unnest.. Line 1, Col: 56.
  SELECT x FROM missing_tbl CROSS JOIN UNNEST(arr) AS u(x[4m
[assistant] No recursion yet with these shapes. I'll read the column resolver to find the path that loops.
[tool_use Bash] {"command": "grep -n \"def \\|class \" sqlglot/optimizer/qualify_columns.py && grep -n \"def \\|class \" sqlglot/optimizer/scope.py | head -80", "description": "List functions in qualify_columns and scope modules"}
[tool_result] 21:def qualify_columns(
117:def validate_qualify_columns(expression: E, sql: str | None = None) -> E:
162:def _separate_pseudocolumns(scope: Scope, pseudocolumns: set[str]) -> None:
184:def _pop_table_column_aliases(derived_tables: Iterable[exp.Expr]) -> None:
198:def _expand_using(scope: Scope, resolver: Resolver) -> dict[str, t.Any]:
201:    def _update_source_columns(source_name: str) -> None:
302:def _expand_alias_refs(
320:    def replace_columns(
422:def _expand_group_by(scope: Scope, dial
…[3486 chars elided]…
> Iterator[Scope]:
758:def _traverse_ctes(scope: Scope) -> Iterator[Scope]:
794:def _is_derived_table(expression: exp.Expr) -> bool:
805:def _is_from_or_join(expression: exp.Expr) -> bool:
818:def _traverse_tables(scope: Scope) -> Iterator[Scope]:
908:def _traverse_subqueries(scope: Scope) -> Iterator[Scope]:
918:def _traverse_udtfs(scope: Scope) -> Iterator[Scope]:
947:def walk_in_scope(
1001:def find_all_in_scope(
1023:def find_in_scope(
1043:def _get_source_alias(expression: exp.Expr) -> str:
[tool_use Bash] {"command": "grep -n \"def \\|class \" sqlglot/optimizer/resolver.py && sed -n 1,60p sqlglot/optimizer/resolver.py | head -5 && grep -n \"_get_all_source_columns\\|get_source_columns\\|def get_source_columns\\|_get_unambiguous\\|is_udtf\\|udtf\" sqlglot/optimizer/resolver.py", "description": "Locate resolver functions handling source columns and UDTFs"}
[tool_result] 17:class Resolver:
21:    This is a class so we can lazily load some things and easily share them across functions.
24:    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
34:    def get_table(self, column: str | exp.Column) -> exp.Identifier | None:
87:    def all_columns(self) -> set[str]:
95:    def get_source_columns_from_set_op(self, expression: exp.Expr) -> list[str]:
133:    def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence
…[1664 chars elided]…
               source_name: self.get_source_columns(source_name)
233:                self._unambiguous_columns = self._get_unambiguous_columns(
234:                    self._get_all_source_columns()
239:            unambiguous_columns = self._get_unambiguous_columns(source_columns)
289:        available_sources = {from_name: self.get_source_columns(from_name)}
292:            available_sources[join.alias_or_name] = self.get_source_columns(join.alias_or_name)
296:    def _get_unambiguous_columns(
[tool_use Bash] {"command": "sed -n 133,226p sqlglot/optimizer/resolver.py && sed -n 363,420p sqlglot/optimizer/resolver.py", "description": "Read resolver source column and unnest type code"}
[tool_result]     def get_source_columns(self, name: str, only_visible: bool = False) -> Sequence[str]:
        """Resolve the source columns for a given source `name`."""
        cache_key = (name, only_visible)
        if cache_key not in self._get_source_columns_cache:
            if name not in self.scope.sources:
                raise OptimizeError(f"Unknown table: {name}")

            source = self.scope.sources[name]

            # A pivoted CTE reference is stored as an exp.Table in the scope sources
…[6124 chars elided]…
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
[assistant] The likely cycle is `get_source_columns` → `_get_unnest_column_type` → a new `Resolver` on the parent scope → `get_source_columns` again. My repro didn't hit it, so I'll try more query shapes, including a Lateral/Explode with an unqualified column.
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sys\nsys.path.insert(0, \".\")\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nsqls = [\n \"SELECT f.value FROM missing_tbl, LATERAL FLATTEN(input => v) AS f\",\n \"SELECT f.value FROM missing_tbl AS m, LATERAL FLATTEN(input => v) AS f\",\n \"SELECT * FROM missing_tbl, LATERAL FLATTEN(input => v)\",\n \"SELECT f.value
…[675 chars elided]…
       except RecursionError:\n            r=\"RecursionError\"\n        except Exception as e:\n            r=type(e).__name__+\": \"+str(e)[:70].replace(\"\\n\",\" \")\n        print(d, len(s), r, \"|\", sql)\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro2.py 2>&1 | tail -70", "description": "Try more lateral/unnest shapes to trigger the recursion"}
[tool_result] snowflake 1 OptimizeError: Column 'V' could not be resolved. Line: 1, Col: 59 | SELECT f.value FROM missing_tbl, LATERAL FLATTEN(input => v) AS f
snowflake 2 OptimizeError: Column 'V' could not be resolved. Line: 1, Col: 59 | SELECT f.value FROM missing_tbl, LATERAL FLATTEN(input => v) AS f
bigquery 1 OptimizeError: Column 'v' could not be resolved. Line: 1, Col: 59 | SELECT f.value FROM missing_tbl, LATERAL FLATTEN(input => v) AS f
bigquery 2 OptimizeError: Column 'v' could not be resolved. Lin
…[7409 chars elided]…
OM missing_tbl, UNNEST(v) AS x
spark 1 OptimizeError: Column 'x' could not be resolved. Line: 1, Col: 8 | SELECT x FROM missing_tbl, UNNEST(v) AS x
spark 2 OptimizeError: Column 'x' could not be resolved. Line: 1, Col: 8 | SELECT x FROM missing_tbl, UNNEST(v) AS x
presto 1 OptimizeError: Column 'x' could not be resolved. Line: 1, Col: 8 | SELECT x FROM missing_tbl, UNNEST(v) AS x
presto 2 OptimizeError: Column 'x' could not be resolved. Line: 1, Col: 8 | SELECT x FROM missing_tbl, UNNEST(v) AS x
[assistant] `LATERAL VIEW EXPLODE(v)` with an unqualified `v` and a missing base table reproduces the `RecursionError` on every dialect. I'll pull the traceback to confirm the cycle.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nqualify(parse_one('SELECT x FROM missing_tbl LATERAL VIEW EXPLODE(v) t AS x', read='spark'), schema={'other': {'x': 'INT'}}, dialect='spark')\n\" 2>&1 | grep -A1 \"File\" | head -40; echo ---; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nprint(repr(parse_one('SELECT x FROM missing_tbl LATERAL VIEW EXPLODE(v) t AS x', read='spark')))\" | head -5", "description": "Get traceback for the Lateral Explode recursion"}
[tool_result]   File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify.py", line 98, in qualify
    expression = qualify_columns_func(
--
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/qualify_columns.py", line 85, in qualify_columns
    _qualify_columns(
  File "~/.cache/lithify/work/re
…[2439 chars elided]…
er-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 380, in _get_unnest_column_type
    table_identifier = parent_resolver.get_table(column)
--
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", line 45, in get_table
    table_name = self._get_table_name_from_sources(column_name)
--
---
Select(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))],
  from_=From(
[assistant] The traceback confirms the cycle. `get_source_columns` on a Lateral calls `_get_unnest_column_type`, which builds a fresh `Resolver` for the parent scope to resolve the unqualified `v`. That resolver calls `_get_all_source_columns`, which includes the same Lateral, so the loop repeats. Each new resolver has its own cache, so nothing stops it. I'll look at the constructor and the other call sites before choosing a guard.
[tool_use Bash] {"command": "sed -n 17,33p sqlglot/optimizer/resolver.py && grep -rn \"Resolver(\" sqlglot/ | grep -v \"class \"", "description": "Read Resolver constructor and its call sites"}
[tool_result] class Resolver:
    """
    Helper for resolving columns.

    This is a class so we can lazily load some things and easily share them across functions.
    """

    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
        self.scope: Scope = scope
        self.schema: Schema = schema
        self.dialect: Dialect = schema.dialect or Dialect()
        self._source_columns: dict[str, Sequence[str]] | None = None
        self._unambiguous_columns: Mapping[str, s
…[11 chars elided]…
= None
        self._all_columns: set[str] | None = None
        self._infer_schema: bool = infer_schema
        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}

sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
[assistant] The fix is a re-entrancy guard shared across the child resolvers. Child resolvers are created only in `_get_unnest_column_type`, so I'll pass one in-progress set down through them. If the same column node is re-entered, it returns `None` (no type known), which matches the existing "couldn't find it" path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[949 chars elided]…
olumns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # Shared with the parent resolvers created in `_get_unnest_column_type`, so that a\n        # lateral source whose unnested column is itself unqualified can't recurse forever\n        self._unnest_columns_in_progress: set[int] = (\n            set() if _unnest_columns_in_progress is None else _unnest_columns_in_progress\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "        # if column is qualified, use that table, otherwise disambiguate using the resolver\n        if column.table:\n            table_name = column.table\n        else:\n            # use the parent scope
…[1193 chars elided]…
  table_identifier = parent_resolver.get_table(column)\n            finally:\n                self._unnest_columns_in_progress.discard(id(column))\n\n            if not table_identifier:\n                return None\n            table_name = table_identifier.name\n\n        source = scope.sources.get(table_name)\n        return self._get_column_type_from_scope(source, column) if source else None"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro2.py 2>&1 | grep -c RecursionError; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.qualify import qualify\nfor s in [{'other': {'x': 'INT'}}, {'other': {'x': 'INT'}, 'missing_tbl': {'v': 'ARRAY<INT>'}}]:\n  try: print(qualify(parse_one('SELECT x FROM missing_tbl LATERAL VIEW EXPLODE(v) t AS x', read='spark'), schema=s, dialect='spark').sql('spark'))\n  except Exception as e: print(type(e).__name__, str(e)[:100])\n\"", "description": "Apply guard, rerun repro matrix, and check schema-present variant"}
[tool_result] 0
OptimizeError Column 'v' could not be resolved. Line: 1, Col: 48
SELECT `t`.`x` AS `x` FROM `missing_tbl` AS `missing_tbl` LATERAL VIEW EXPLODE(`missing_tbl`.`v`) t AS `x`
[assistant] The matrix now has zero `RecursionError`s, and the schema-present variant qualifies correctly. Next I'll check whether a compiled `.so` is present and run the project's test command.
[tool_use Bash] {"command": "ls sqlglot/*.so sqlglot/optimizer/*.so 2>/dev/null; ls sqlglotc 2>/dev/null | head; <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check for compiled extension and run full test suite"}
[tool_result] (eval):1: no matches found: sqlglot/*.so
MANIFEST.in
pyproject.toml
setup.py
........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
.................................................
…[341 chars elided]…
............... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 71.33s (0:01:11)
[assistant] The full suite passes (1120 tests). There's no compiled extension in this checkout, so the `[c]` build can't be exercised here. The change is plain Python using a `set` and type annotations, so it should compile under mypyc. Next, I'll add a regression test next to the existing lateral-explode qualify tests.
[tool_use Bash] {"command": "grep -rn \"LATERAL VIEW EXPLODE\\|lateral.*explode\" tests/test_optimizer.py tests/fixtures/optimizer/qualify_columns.sql | head; grep -n \"def test_qualify_columns\\b\\|def test_qualify_columns_\\|def check_file\" tests/test_optimizer.py | head", "description": "Find existing lateral explode qualify tests"}
[tool_result] tests/test_optimizer.py:718:                    "SELECT ci.name, ci.age FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci",
tests/test_optimizer.py:729:            "SELECT `ci`.`name` AS `name`, `ci`.`age` AS `age` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`",
tests/test_optimizer.py:738:                    "SELECT (SELECT SUM(ci.amount) FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci WHERE ci.type = 'promotion') AS total FROM my_table",
tests/test_optim
…[569 chars elided]…
sts/fixtures/optimizer/qualify_columns.sql:807:SELECT _0.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:810:SELECT c FROM xx LATERAL VIEW EXPLODE (a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:811:SELECT _0.c AS c FROM xx AS xx LATERAL VIEW EXPLODE(xx.a) _0 AS c;
154:    def check_file(
357:    def test_qualify_columns(self, logger):
753:    def test_qualify_columns__with_invisible(self):
763:    def test_qualify_columns__invalid(self):
[tool_use Bash] {"command": "sed -n 710,765p tests/test_optimizer.py", "description": "Read nearby lateral explode test to match style"}
[tool_result]                 expression, schema={"x": {"a": "int", "b": "int", "c": "str"}}
            )
            optimizer.qualify_columns.validate_qualify_columns(qualified)

        schema = {"my_table": {"items": "ARRAY<STRUCT<name STRING, age INT>>"}}
        expression = annotate_types(
            optimizer.qualify.qualify(
                parse_one(
                    "SELECT ci.name, ci.age FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci",
                    read="spark",
                ),
…[1551 chars elided]…
isible(self):
        schema = MappingSchema(self.schema, {"x": {"a"}, "y": {"b"}, "z": {"b"}})
        self.check_file("qualify_columns__with_invisible", qualify_columns, schema=schema)

    def test_pushdown_cte_alias_columns(self):
        self.check_file(
            "pushdown_cte_alias_columns",
            pushdown_ctes,
        )

    def test_qualify_columns__invalid(self):
        for sql in load_sql_fixtures("optimizer/qualify_columns__invalid.sql"):
            with self.subTest(sql):
[assistant] I'll add a regression test after the existing lateral-explode test. It covers the missing-table case (must raise the normal `OptimizeError`, not recurse) and the case where the table is in the schema (must qualify).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.selects[0].type, exp.DataType.build(\"DOUBLE\", dialect=\"spark\"))\n\n    def test_qualify_columns__with_invisible(self):", "new_string": "        self.assertEqual(expression.s
…[581 chars elided]…
={\"missing_table\": {\"items\": \"ARRAY<INT>\"}, \"other\": {\"x\": \"INT\"}},\n            dialect=\"spark\",\n        )\n        self.assertEqual(\n            expression.sql(dialect=\"spark\"),\n            \"SELECT `t`.`x` AS `x` FROM `missing_table` AS `missing_table` LATERAL VIEW EXPLODE(`missing_table`.`items`) t AS `x`\",\n        )\n\n    def test_qualify_columns__with_invisible(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-124909-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"OptimizeError\" tests/test_optimizer.py | head -3; <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral 2>&1 | tail -15", "description": "Check OptimizeError import and run new test"}
[tool_result] 11:from sqlglot.errors import ANSI_RESET, ANSI_UNDERLINE, OptimizeError, SchemaError
697:            OptimizeError, "Column 'foo' could not be resolved. Line: 1, Col: 10"
705:        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
.                                                                        [100%]
1 passed, 78 deselected in 0.28s
[assistant] The new test passes. To confirm it actually catches the bug, I'll run it against the original `resolver.py` and then restore my version.
[tool_use Bash] {"command": "cp sqlglot/optimizer/resolver.py /tmp/resolver_fixed.py && git show HEAD:sqlglot/optimizer/resolver.py > sqlglot/optimizer/resolver.py && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k lateral 2>&1 | grep -E \"RecursionError|passed|failed\" | tail -3; cp /tmp/resolver_fixed.py sqlglot/optimizer/resolver.py && git status --short && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Confirm test fails on original code, restore fix, rerun full suite"}
[tool_result] 1 passed, 78 deselected in 0.19s
 M sqlglot/optimizer/resolver.py
 M tests/test_optimizer.py
...............................................           [100%]
1120 passed, 18166 subtests passed in 58.20s
[assistant] That result is suspicious: the test passed on the original code. The `-k lateral` filter may not have selected the method I edited. I'll check which method contains the new code.
[tool_use Bash] {"command": "awk 'NR<=735 && /    def test_/{name=$0} END{}; NR==735{print name}' tests/test_optimizer.py", "description": "Identify the test method containing the new assertions"}
[tool_result]     def test_validate_columns(self):
[tool_use Bash] {"command": "L=$(grep -n \"missing_table LATERAL\" tests/test_optimizer.py | cut -d: -f1); awk -v L=$L 'NR<=L && /    def test_/{name=$0} NR==L{print L\": \"name}' tests/test_optimizer.py", "description": "Find enclosing test method for the new test lines"}
[tool_result] 754:     def test_validate_columns(self):
[assistant] The new assertions live in `test_validate_columns`, which the `-k lateral` filter missed. I'll rerun that test against both versions.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; echo \"== fixed\"; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k test_validate_columns 2>&1 | tail -1; git show HEAD:sqlglot/optimizer/resolver.py > sqlglot/optimizer/resolver.py; echo \"== original\"; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k test_validate_columns 2>&1 | grep -E \"^E  .*Error|passed|failed\" | tail -3; cp /tmp/resolver_fixed.py sqlglot/optimizer/resolver.py; git diff --stat", "description": "Run regression test on fixed and original resolver"}
[tool_result] == fixed
1 passed, 78 deselected in 0.18s
== original
E   RecursionError: maximum recursion depth exceeded
1 failed, 78 deselected in 0.23s
 sqlglot/optimizer/resolver.py | 29 ++++++++++++++++++++++++++---
 tests/test_optimizer.py       | 17 +++++++++++++++++
 2 files changed, 43 insertions(+), 3 deletions(-)
[assistant] The test fails with `RecursionError` on the original code and passes with the fix. Last, a lint/format check on the two changed files.
[tool_use Bash] {"command": "PYDIR=<work>/env-sqlglot/bin; ($PYDIR/ruff --version && $PYDIR/ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PYDIR/ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -6", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
[assistant] Qualifying a lateral column that is unqualified no longer recurses. The pure-Python `RecursionError` is gone, and the full suite passes (1120 tests, plus the new regression test).

**Cause:** `Resolver.get_source_columns` handles a `LATERAL VIEW EXPLODE(col)` source by calling `_get_unnest_column_type`. For an unqualified `col`, that builds a new `Resolver` on the parent scope to find which table `col` belongs to. That resolver calls `_get_all_source_columns`, which includes the same lateral, so the cycle repeats. Each new resolver has its own cache, so nothing stopped it.

**Fix** (`sqlglot/o
…[661 chars elided]…
 the fix.

**Notes:**
- I reproduced the crash with `LATERAL VIEW EXPLODE(v)` (Spark/Hive syntax), not with `LATERAL FLATTEN` or `UNNEST`. Those shapes raise `OptimizeError` in my tests, not `RecursionError`, so the guard doesn't change their behavior. If your report comes from a `FLATTEN` query, send me the exact SQL and schema and I'll check it.
- The compiled `sqlglot[c]` build wasn't exercised. This checkout has no `.so` files, so I couldn't build the mypyc variant. The change is plain Python and should compile under mypyc, but that's unverified.
- Ruff check and format pass on both files.
