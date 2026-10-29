# trajectory base-1

final message:
`MappingSchema.find` now caches its results per instance, and the cache is cleared whenever `add_table` changes the schema. The full test suite passes (1105 tests), and ruff lint and format are clean.

**Change (`sqlglot/schema.py`)**
- `find` keys the cache on `(table parts, raise_on_missing, ensure_data_types)`. A repeat lookup returns the stored result, including the converted-type dict on the `ensure_data_types=True` path that `annotate_scope` hits per column.
- `add_table` clears the cache right after it writes the mapping and trie, so tables added later, and columns changed on existing tables, are seen by the next `find`.
- Cached `None` results for missing tables are cleared the same way, so a table added later is found.

**Tests**
- Added `test_find_cache_invalidated_by_add_table` in `tests/test_schema.py`. It covers a miss followed by `add_table`, a column update on an existing table, and both `ensure_data_types` modes. No existing tests were touched.

**Performance**
- Synthetic benchmark (3,000 column refs across 3 tables, `annotate_types`): 0.126s → 0.114s, about 10%. The `find` share of the profile was small to begin with, so this is a modest gain, not a large one.

**Things to know**
- With `ensure_data_types=False`, `find` still returns the live mapping dict, as before. With `ensure_data_types=True`, repeat calls now return the same dict object instead of a fresh copy. Equal content, but callers that mutate the returned dict would affect later lookups. Nothing in the repo does that.
- The cache is only cleared through `add_table`. Code that writes into `schema.mapping` directly would bypass it. I found no such writes on a `MappingSchema` instance in the repo; the executor only mutates dicts it builds itself.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n \"class MappingSchema\" -A 200 sqlglot/schema.py | head -320", "description": "Read MappingSchema class source"}
[tool_result] 287:class MappingSchema(AbstractMappingSchema, Schema):
288-    """
289-    Schema based on a nested mapping.
290-
291-    Args:
292-        schema: Mapping in one of the following forms:
293-            1. {table: {col: type}}
294-            2. {db: {table: {col: type}}}
295-            3. {catalog: {db: {table: {col: type}}}}
296-            4. None - Tables will be added later
297-        visible: Optional mapping of which columns in the schema are visible. If not provided, all columns
298- 
…[7767 chars elided]…
alse)
473-
474-        if resolved_parts is None:
475-            return exp.DType.UNKNOWN.into_expr()
476-
477-        udf_type = nested_get(
478-            self.udf_mapping,
479-            *zip(resolved_parts, reversed(resolved_parts)),
480-            raise_on_missing=False,
481-        )
482-
483-        if isinstance(udf_type, exp.DataType):
484-            return udf_type
485-        elif isinstance(udf_type, str):
486-            return self._to_data_type(udf_type, dialect=dialect)
487-
[tool_use Bash] {"command": "grep -n \"def find\" -A 60 sqlglot/schema.py | sed -n '1,140p'; grep -n \"_type_mapping_cache\\|_normalized_table_cache\\|_normalized_name_cache\\|_to_data_type\\|def add_table\\|def _normalize_table\\|_depth\\|def depth\" sqlglot/schema.py", "description": "Read find and cache references in schema.py"}
[tool_result] 229:    def find(
230-        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False
231-    ) -> t.Any | None:
232-        """
233-        Returns the schema of a given table.
234-
235-        Args:
236-            table: the target table.
237-            raise_on_missing: whether to raise in case the schema is not found.
238-            ensure_data_types: whether to convert `str` types to their `DataType` equivalents.
239-
240-        Returns:
241-            Th
…[7282 chars elided]…
pth(self) -> int:
654:        if not self.empty and not self._depth:
656:            self._depth = super().depth() - 1
657:        return self._depth
659:    def _to_data_type(self, schema_type: str, dialect: DialectType = None) -> exp.DataType:
670:        if schema_type not in self._type_mapping_cache:
677:                self._type_mapping_cache[schema_type] = expression
682:        return self._type_mapping_cache[schema_type]
733:    depth = dict_depth(schema) - 1 if depth is None else depth
[tool_use Bash] {"command": "sed -n 596,690p sqlglot/schema.py; grep -rn \"nested_set\\|\\.mapping\\[\\|mapping_trie\\|_find_in_trie\" sqlglot/ | grep -v \"^sqlglot/schema.py:6[0-9][0-9]\" ; ls tests | grep -i schema; git log --oneline -1", "description": "Read normalize helpers and find mutation points"}
[tool_result]         return parts

    def _normalize_table(
        self,
        table: exp.Table | str,
        dialect: DialectType = None,
        normalize: bool | None = None,
    ) -> exp.Table:
        dialect = dialect or self.dialect
        normalize = self.normalize if normalize is None else normalize

        # Cache normalized tables by object id for exp.Table inputs
        # This is effective when the same Table object is looked up multiple times
        if isinstance(table, exp.Table) and (
…[3785 chars elided]…
, value: t.Any) -> dict[str, t.Any]:
sqlglot/schema.py:776:        >>> nested_set({}, ["top_key", "second_key"], "value")
sqlglot/schema.py:779:        >>> nested_set({"top_key": {"third_key": "third_value"}}, ["top_key", "second_key"], "value")
sqlglot/executor/__init__.py:21:from sqlglot.schema import ensure_schema, flatten_schema, nested_get, nested_set
sqlglot/executor/__init__.py:68:                nested_set(schema, [*keys, column], column_type)
test_schema.py
d02a58290 lithify: probe base
[tool_use Bash] {"command": "grep -n \"def table_parts\" -A 12 sqlglot/schema.py; sed -n 55,70p sqlglot/executor/__init__.py; grep -rn \"\\.mapping\\b\" sqlglot/ | grep -v \"udf_mapping\\|self.mapping\\b\" | head -20; grep -rn \"find(\" sqlglot/optimizer/*.py | head", "description": "Inspect table_parts and mapping mutation sites"}
[tool_result] 194:    def table_parts(self, table: exp.Table) -> list[str]:
195-        return [p.name for p in reversed(table.parts)]
196-
197-    def udf_parts(self, udf: exp.Anonymous) -> list[str]:
198-        # a.b.c(...) is represented as Dot(Dot(a, b), Anonymous(c, ...))
199-        parent = udf.parent
200-        parts = [p.name for p in parent.flatten()] if isinstance(parent, exp.Dot) else [udf.name]
201-        return list(reversed(parts))[0 : self.udf_depth()]
202-
203-    def _find_in_trie(
204-  
…[1623 chars elided]…
hdown_predicates.py:216:                select for select in node.selects if select.find(exp.Window)
sqlglot/optimizer/optimize_joins.py:123:        >>> _is_reorderable(ast.find(exp.Select).args.get("joins", []))
sqlglot/optimizer/optimize_joins.py:126:        >>> _is_reorderable(ast.find(exp.Select).args.get("joins", []))
sqlglot/optimizer/scope.py:211:    def find(self, *expression_types: Type[E]) -> E | None:
sqlglot/optimizer/unnest_subqueries.py:97:    if select.find(exp.Limit, exp.Offset):
[tool_use Bash] {"command": "sed -n 336,362p sqlglot/optimizer/annotate_types.py; grep -n \"def get_column_type\\|def column_names\" -B2 -A3 sqlglot/schema.py | head -30; grep -rn \"ensure_data_types=True\" sqlglot | head", "description": "View annotate_types schema lookup"}
[tool_result]                     selects[pivot.alias] = col_types

            self._scope_selects[scope] = selects

        return self._scope_selects[scope]

    def annotate_scope(self, scope: Scope) -> None:
        if isinstance(self.schema, MappingSchema):
            for table_column in scope.table_columns:
                source = scope.sources.get(table_column.name)

                if isinstance(source, exp.Table):
                    schema = self.schema.find(
                        source, raise
…[858 chars elided]…
.Column | str,
--
409-        new_trie([parts], self.mapping_trie)
410-
411:    def column_names(
412-        self,
413-        table: exp.Table | str,
414-        only_visible: bool = False,
--
428-        return [col for col in schema if col in visible]
429-
430:    def get_column_type(
431-        self,
432-        table: exp.Table | str,
433-        column: exp.Column | str,
sqlglot/optimizer/annotate_types.py:349:                        source, raise_on_missing=False, ensure_data_types=True
[assistant] Current state: `find` runs a trie walk, `nested_get`, and (with `ensure_data_types`) a fresh dict conversion on every call. `annotate_scope` calls it per column reference with `ensure_data_types=True`, so that's the hot path. Let me get a baseline before editing.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py tests/test_optimizer.py 2>&1 | tail -3; cat > /tmp/bench_find.py <<'EOF'\nimport time\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.schema import MappingSchema\ncols = {f\"c{i}\": 
…[144 chars elided]…
.join(f\"t{(i%3)+1}.c{i%200}\" for i in range(3000)) + \" FROM t1 JOIN t2 ON t1.c0 = t2.c0 JOIN t3 ON t1.c0 = t3.c0\"\nexpr = parse_one(sql, dialect=\"duckdb\")\nt = time.perf_counter()\nfor _ in range(3):\n    annotate_types(expr.copy(), schema=schema, dialect=\"duckdb\")\nprint(f\"{time.perf_counter()-t:.3f}s\")\nEOF\n$PY -I /tmp/bench_find.py", "description": "Run baseline tests and benchmark"}
[tool_result ERROR] Exit code 1
............... [ 86%]
............                                                                   [100%]
87 passed, 3807 subtests passed in 15.83s
Traceback (most recent call last):
  File "/tmp/bench_find.py", line 2, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/bench_find.py; PYTHONPATH=. $PY -m cProfile -s cumtime /tmp/bench_find.py 2>&1 | grep -E \"schema.py|annotate_types.py\" | head -8", "description": "Benchmark baseline and profile find calls"}
[tool_result] 0.126s
        3    0.001    0.000    0.383    0.128 annotate_types.py:45(annotate_types)
        3    0.000    0.000    0.382    0.127 annotate_types.py:261(annotate)
        3    0.000    0.000    0.315    0.105 annotate_types.py:342(annotate_scope)
        6    0.046    0.008    0.315    0.053 annotate_types.py:397(_annotate_expression)
     9012    0.010    0.000    0.094    0.000 schema.py:430(get_column_type)
    27072    0.024    0.000    0.058    0.000 annotate_types.py:238(_set_type)
     9012    0.002    0.000    0.041    0.000 schema.py:344(find)
     9012    0.006    0.000    0.038    0.000 schema.py:229(find)
[assistant] Baseline: 9,012 `find` calls, about 0.04s of 0.38s profiled. Now the change: a per-instance cache in `MappingSchema.find`, cleared in `add_table`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[tuple[str, ...], bool, bool], t.Any] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "    def find(\n        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False\n    ) -> t.Any | None:\n        schema: dict[str, object] | None = super().find(\n            table, raise_o
…[735 chars elided]…
     table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        self._find_cache[cache_key] = schema\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        parts = self.table_parts(normalized_table)\n\n        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        parts = self.table_parts(normalized_table)\n\n        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[assistant] Now I'll check the benchmark, the existing tests, and the invalidation cases directly: a miss followed by `add_table`, an update to an existing table, and the `ensure_data_types` path.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/bench_find.py; cat > /tmp/check_find.py <<'EOF'\nfrom sqlglot import exp, parse_one\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({\"t1\": {\"a\": \"INT\"}}, dialect=\"duckdb\")\ntbl = exp.to_table(\"t2\")\nassert s.find(tbl, raise_on_missing=False) is None\nassert s.find
…[749 chars elided]…
() == \"BIGINT\"\nassert s.find(exp.to_table(\"t1\"), ensure_data_types=True)[\"a\"].sql() == \"BIGINT\"\nprint(\"invalidation ok\")\nEOF\nPYTHONPATH=. $PY /tmp/check_find.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py tests/test_optimizer.py tests/test_executor.py tests/test_lineage.py 2>&1 | tail -3", "description": "Benchmark, invalidation checks, and related tests"}
[tool_result] 0.114s
invalidation ok
..................................................................... [ 98%]
..                                                                       [100%]
146 passed, 4032 subtests passed in 38.88s
[assistant] Invalidation checks pass and the related suites are green. The benchmark gain is modest (0.126s → 0.114s, about 10%). I'll add a regression test for the invalidation behavior, then run the full suite.
[tool_use Bash] {"command": "grep -n \"^class \\|def test_\" tests/test_schema.py | head -30; grep -n \"def test_schema_add_table\" -A 12 tests/test_schema.py | head -30", "description": "Look at existing schema test layout"}
[tool_result] 8:class TestSchema(unittest.TestCase):
25:    def test_schema(self):
53:    def test_schema_db(self):
92:    def test_schema_catalog(self):
154:    def test_schema_add_table_with_and_without_mapping(self):
165:    def test_schema_get_column_type(self):
199:    def test_schema_normalization(self):
274:    def test_same_number_of_qualifiers(self):
332:    def test_has_column(self):
337:    def test_find(self):
154:    def test_schema_add_table_with_and_without_mapping(self):
155-        schema = M
…[87 chars elided]…
.column_names("test"), [])
158-        schema.add_table("test", {"x": "string"})
159-        self.assertEqual(schema.column_names("test"), ["x"])
160-        schema.add_table("test", {"x": "string", "y": "int"})
161-        self.assertEqual(schema.column_names("test"), ["x", "y"])
162-        schema.add_table("test")
163-        self.assertEqual(schema.column_names("test"), ["x", "y"])
164-
165-    def test_schema_get_column_type(self):
166-        schema = MappingSchema({"A": {"b": "varchar"}})
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        schema.add_table(\"test\")\n        self.assertEqual(schema.column_names(\"test\"), [\"x\", \"y\"])\n\n    def test_schema_get_column_type(self):", "new_string": "        schema.add_table(\"test\")\n        s
…[570 chars elided]…
schema.find(table, raise_on_missing=False, ensure_data_types=True),\n            {\"b\": exp.DataType.build(\"TEXT\")},\n        )\n\n        schema.add_table(\"t2\", {\"b\": \"TEXT\", \"c\": \"INT\"})\n        self.assertEqual(schema.column_names(\"t2\"), [\"b\", \"c\"])\n        self.assertEqual(schema.get_column_type(\"t2\", \"c\").sql(), \"INT\")\n\n    def test_schema_get_column_type(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102433-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; head -8 tests/test_schema.py | grep import; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py -k find_cache 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Run new test and full project test suite"}
[tool_result] import unittest
from sqlglot import exp, parse_one, to_table
from sqlglot.errors import SchemaError
from sqlglot.schema import MappingSchema, ensure_schema
.                                                                        [100%]
1 passed, 9 deselected in 0.03s
............................................. [ 78%]
................................................................................................................................................. [ 91%]
.............................................................................................                            [100%]
1105 passed, 17948 subtests passed in 56.58s
[assistant] Full suite passes (1105 tests). Last, the lint and format checks on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/schema.py tests/test_schema.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/schema.py tests/test_schema.py 2>&1 | tail -2; git status --short; git diff --stat", "description": "Run ruff lint and format checks"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/schema.py
 M tests/test_schema.py
 sqlglot/schema.py    |  7 +++++++
 tests/test_schema.py | 17 +++++++++++++++++
 2 files changed, 24 insertions(+)
[assistant] `MappingSchema.find` now caches its results per instance, and the cache is cleared whenever `add_table` changes the schema. The full test suite passes (1105 tests), and ruff lint and format are clean.

**Change (`sqlglot/schema.py`)**
- `find` keys the cache on `(table parts, raise_on_missing, ensure_data_types)`. A repeat lookup returns the stored result, including the converted-type dict on the `ensure_data_types=True` path that `annotate_scope` hits per column.
- `add_table` clears the cache right after it writes the mapping and trie, so tables added later, and columns changed on existing t
…[579 chars elided]…
 not a large one.

**Things to know**
- With `ensure_data_types=False`, `find` still returns the live mapping dict, as before. With `ensure_data_types=True`, repeat calls now return the same dict object instead of a fresh copy. Equal content, but callers that mutate the returned dict would affect later lookups. Nothing in the repo does that.
- The cache is only cleared through `add_table`. Code that writes into `schema.mapping` directly would bypass it. I found no such writes on a `MappingSchema` instance in the repo; the executor only mutates dicts it builds itself.

I didn't commit anything.
