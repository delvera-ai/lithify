# trajectory base-1

final message:
`MappingSchema.find` now caches its results, keyed by table parts, `raise_on_missing`, and `ensure_data_types`. The cache is cleared whenever `add_table` runs. The full suite passes (1106 tests, up from 1104 with two new ones), and ruff and mypy are clean. The changes are uncommitted in the worktree.

**What changed**
- `sqlglot/schema.py`: a new `_find_cache` dict is initialised in `MappingSchema.__init__`. `find` checks it first and stores its result after the lookup. `add_table` clears it after mutating the mapping.
- `tests/test_schema.py`: `test_find_cache` covers repeated lookups, the `ensure_data_types` variants, and invalidation after adding or replacing a table. `test_find_cache_raise_on_missing` checks that a `raise_on_missing=False` result doesn't leak into a `raise_on_missing=True` call.

**Choices to be aware of**
- Results that raise are not cached. Missing-table `None` results are cached, and `add_table` clears them.
- With `ensure_data_types=True`, callers now get the same converted dict on repeat calls. Nothing in the repo mutates that result (the only caller, `annotate_types`, only reads it).
- The cache only tracks changes made through `add_table`. Editing `schema.mapping` directly would leave cached results stale. Nothing in the repo does that after construction.

**Performance:** the gain is small. On a synthetic query with 3000 column references across 3 tables, `annotate_types` took about 0.027s with the cache and 0.030s with it cleared on every call, roughly 10%. The lookups were already cheap. The bulk of the time is elsewhere in annotation.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"class MappingSchema\" -A 200 sqlglot/schema.py | head -320", "description": "Show MappingSchema class source"}
[tool_result] ok287:class MappingSchema(AbstractMappingSchema, Schema):
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
298
…[7769 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"def find\\|def _normalize_table\\|_normalized_table_cache\\|_type_mapping_cache\\|def _to_data_type\\|def add_table\\|mapping_trie\\|def empty\\|def depth\" sqlglot/schema.py && sed -n 1,80p sqlglot/schema.py | grep -n \"import\\|class\" ; grep -n \"class AbstractMappingSchema\" -A 120 sqlglot/schema.py | grep -n \"def find\" -A 40", "description": "Locate cache and find-related code in schema.py"}
[tool_result] 21 matches in 12 files:

148:0:
160:0:dict[str, object] = new_trie(
171:0:
174:0:
251:0:exp.Anonymous, raise_on_missing: bool = False) -> t.Any | None:
317:0:dict[str, exp.DataType] = {}
318:0:dict[tuple[exp.Table, DialectType, bool], exp.Table] = {}
611:0:= self._normalized_table_cache.get((table, dialect, normalize))
653:0:
659:0:str, dialect: DialectType = None) -> exp.DataType:
670:0:
sqlglot/schema.py:37:def add_table(
sqlglot/schema.py:229:def find(
sqlglot/schema.py:244:resolved_parts = s
…[2647 chars elided]…
e UDF, or None if not found.
109-261-        """
110-262-        parts = self.udf_parts(udf)
111-263-        resolved_parts = self._find_in_trie(parts, self.udf_trie, raise_on_missing)
112-264-
113-265-        if resolved_parts is None:
114-266-            return None
115-267-
116-268-        return nested_get(
117-269-            self.udf_mapping,
118-270-            *zip(resolved_parts, reversed(resolved_parts)),
119-271-            raise_on_missing=raise_on_missing,
120-272-        )
121-273-
[tool_use Bash] {"command": "sed -n 595,690p sqlglot/schema.py && grep -rn \"\\.mapping\\b\\|mapping_trie\\|nested_set\" sqlglot/schema.py | head -40 && grep -rn \"schema\\b\" setup.py pyproject.toml 2>/dev/null | grep -i mypyc | head; grep -rln \"\\.mapping\\[\\|\\.mapping =\\|mapping_trie\" sqlglot | head", "description": "Read normalization and type caching code"}
[tool_result]             parts = [self._normalize_name(part, dialect=dialect, is_table=True) for part in parts]

        return parts

    def _normalize_table(
        self,
        table: exp.Table | str,
        dialect: DialectType = None,
        normalize: bool | None = None,
    ) -> exp.Table:
        dialect = dialect or self.dialect
        normalize = self.normalize if normalize is None else normalize

        # Cache normalized tables by object id for exp.Table inputs
        # This is effective 
…[4010 chars elided]…
elf.mapping_trie)
sqlglot/schema.py:536:                nested_set(
sqlglot/schema.py:559:            nested_set(normalized_mapping, normalized_keys, udf_type)
sqlglot/schema.py:771:def nested_set(d: dict[str, t.Any], keys: Sequence[str], value: t.Any) -> dict[str, t.Any]:
sqlglot/schema.py:776:        >>> nested_set({}, ["top_key", "second_key"], "value")
sqlglot/schema.py:779:        >>> nested_set({"top_key": {"third_key": "third_value"}}, ["top_key", "second_key"], "value")
sqlglot/schema.py
[tool_use Bash] {"command": "grep -n \"def table_parts\" -A 12 sqlglot/schema.py && grep -rn \"ensure_data_types=True\\|\\.find(\" sqlglot | grep -v \"\\.find_all\\|str.find\" | head -30 && grep -n \"def _find_in_trie\" -A 25 sqlglot/schema.py && grep -n \"def nested_get\" -A 25 sqlglot/schema.py | head -40", "description": "Inspect table_parts, find callers, trie lookup"}
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
…[4988 chars elided]…
chema:
299-            1. {table: set(*cols)}}
--
744:def nested_get(
745-    d: dict[str, object], *path: tuple[str, str], raise_on_missing: bool = True
746-) -> t.Any | None:
747-    """
748-    Get a value for a nested dictionary.
749-
750-    Args:
751-        d: the dictionary to search.
752-        *path: tuples of (name, key), where:
753-            `key` is the key in the dictionary to get.
754-            `name` is a string to use in the error if `key` isn't found.
755-
756-    Returns:
[tool_use Bash] {"command": "sed -n 335,370p sqlglot/optimizer/annotate_types.py && grep -rn \"ensure_data_types\" sqlglot tests | head && ls tests | grep -i schema; ls <work>/env-sqlglot/bin/python && git log --oneline -1", "description": "Check annotate_types usage and test environment"}
[tool_result]                 if pivot.unpivot and (col_types := self._get_unpivot_column_types(pivot, selects)):
                    selects[pivot.alias] = col_types

            self._scope_selects[scope] = selects

        return self._scope_selects[scope]

    def annotate_scope(self, scope: Scope) -> None:
        if isinstance(self.schema, MappingSchema):
            for table_column in scope.table_columns:
                source = scope.sources.get(table_column.name)

                if isinstance(sour
…[1564 chars elided]…
/schema.py:348:            table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types
sqlglot/schema.py:350:        if ensure_data_types and isinstance(schema, dict):
tests/test_schema.py:341:        found = schema.find(exp.to_table("x"), ensure_data_types=True)
test_schema.py  12.0K
<work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
6ee42d28b lithify: probe base
[tool_use Bash] {"command": "sed -n 325,350p tests/test_schema.py && grep -n \"^class \\|def test_\" tests/test_schema.py | head -60 && sed -n 1,20p tests/test_schema.py", "description": "Read existing schema tests for style"}
[tool_result]                 },
            )
        self.assertEqual(
            str(ctx.exception),
            "Table catalog.db.tbl must match the schema's nesting level: 1.",
        )

    def test_has_column(self):
        schema = MappingSchema({"x": {"c": "int"}})
        self.assertTrue(schema.has_column("x", exp.column("c")))
        self.assertFalse(schema.has_column("x", exp.column("k")))

    def test_find(self):
        schema = MappingSchema({"x": {"c": "int"}})
        found = schema.find(
…[520 chars elided]…
, schema, *table_results):
        for table, result in table_results:
            with self.subTest(f"{table} -> {result}"):
                self.assertEqual(schema.column_names(to_table(table)), result)

    def assert_column_names_raises(self, schema, *tables):
        for table in tables:
            with self.subTest(table):
                with self.assertRaises(SchemaError):
                    schema.column_names(to_table(table))

    def assert_column_names_empty(self, schema, *tables):
[tool_use Bash] {"command": "time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run baseline test suite before changes", "timeout": 900000}
[tool_result] ............................................. [ 78%]
................................................................................................................................................. [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1104 passed, 17948 subtests passed in 49.17s
<work>/env-sqlglot/bin/python -m   118.47s user 13.69s system 266% cpu 49.562 total
tail -5  0.00s user 0.00s system 0% cpu 49.561 total
[assistant] Baseline is green (1104 passed). Now the change: cache `find` results on `MappingSchema`, keyed by table parts, `raise_on_missing`, and `ensure_data_types`, and clear the cache in `add_table`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[tuple[str, ...], bool, bool], t.Any] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "    ) -> t.Any | None:\n        schema: dict[str, object] | None = super().find(\n            table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and is
…[513 chars elided]…
     table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        self._find_cache[cache_key] = schema\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"int\")})\n", "new_string": "        found = schema.find(exp.to_table(\"x\"), ensu
…[1041 chars elided]…
=True),\n            {\"c\": exp.DataType.build(\"bigint\"), \"d\": exp.DataType.build(\"text\")},\n        )\n\n    def test_find_cache_raise_on_missing(self):\n        schema = MappingSchema({\"x\": {\"c\": \"int\"}})\n        self.assertIsNone(schema.find(exp.to_table(\"y\"), raise_on_missing=False))\n        with self.assertRaises(SchemaError):\n            schema.find(exp.to_table(\"y\"))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[assistant] Checking the test I just wrote: a fully missing table returns `None` without raising, so the raise case needs an ambiguous path. Fixing that test to use one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        schema = MappingSchema({\"x\": {\"c\": \"int\"}})\n        self.assertIsNone(schema.find(exp.to_table(\"y\"), raise_on_missing=False))\n        with self.assertRaises(SchemaError):\n            schema.find(exp.to_table(\"y\"))", "new_string": "        schema = MappingSchema({\"db1\": {\"x\": {\"c\": \"int\"}}, \"db2\": {\"x\": {\"c\": \"int\"}}})\n        self.assertIsNone(schema.find(exp.to_table(\"x\"), raise_on_missing=False))\n        with self.assertRaises(SchemaError):\n            schema.find(exp.to_table(\"x\"))"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184648-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py 2>&1 | tail -15", "description": "Run schema tests with new cache tests", "timeout": 300000}
[tool_result] ...........                               [100%]
11 passed, 31 subtests passed in 0.06s
[assistant] Schema tests pass. Next, a quick timing check on a wide query to confirm the cache helps, comparing against the uncached path via a monkeypatch.
[tool_use Bash] {"command": "mkdir -p /tmp/bench-sqlglot-find && cat > /tmp/bench-sqlglot-find/bench.py <<'EOF'\nimport time\nfrom sqlglot import exp, parse_one\nfrom sqlglot.optimizer import annotate_types\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\nimport sqlglot.schema as S\n\ncols = {f\"c{i}\": \"int\" for i in range(200)}\nschema = MappingSchema({\"t1\": cols, \"
…[584 chars elided]…
on_missing, ensure_data_types)\nMappingSchema.find = uncached\nprint(\"uncached:\", round(min(run() for _ in range(3)), 3))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/bench-sqlglot-find/bench.py').read())\"", "description": "Time annotate_types on wide query with and without cache", "timeout": 600000}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "<string>", line 19, in <module>
  File "<string>", line 19, in <genexpr>
  File "<string>", line 16, in run
TypeError: 'module' object is not callable
[tool_use Bash] {"command": "sed -i 's/^from sqlglot.optimizer.qualify import qualify$/from sqlglot.optimizer.qualify import qualify as _q/; s/e = qualify(parse_one(sql), schema=schema)/e = _q.qualify(parse_one(sql), schema=schema) if hasattr(_q, \"qualify\") else _q(parse_one(sql), schema=schema)/' /tmp/bench-sqlglot-find/bench.py && <work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot.optimizer.qualify as q; print(type(q.qualify), hasattr(q,'qualify'))\" && <work>/env-sqlglot/bin/python -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/bench-sqlglot-find/bench.py').read())\"", "description": "Fix qualify import in benchmark and run it", "timeout": 600000}
[tool_result ERROR] Exit code 1
sed: 2: "/tmp/bench-sqlglot-find ...": undefined label 'ench-sqlglot-find/bench.py'
[assistant] Rewriting the benchmark file directly, since the sed edit was fragile.
[tool_use Write] {"file_path": "/tmp/bench-sqlglot-find/bench.py", "content": "import sys\nimport time\n\nsys.path.insert(0, \".\")\n\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer import annotate_types\nfrom sqlglot.optimizer.qualify import qualify\nfrom sqlglot.schema import MappingSchema\n\ncols = {f\"c{i}\": \"int\" for i in range(200)}\nschema = MappingSchema({\"t1\": cols, \"t2\": cols, \"t3\": cols}
…[304 chars elided]…
turn time.perf_counter() - t0\n\n\nprint(\"cached  :\", round(min(run() for _ in range(3)), 3))\norig = MappingSchema.find\n\n\ndef uncached(self, table, raise_on_missing=True, ensure_data_types=False):\n    self._find_cache.clear()\n    return orig(self, table, raise_on_missing, ensure_data_types)\n\n\nMappingSchema.find = uncached\nprint(\"uncached:\", round(min(run() for _ in range(3)), 3))\n"}
[tool_result] The file /tmp/bench-sqlglot-find/bench.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python /tmp/bench-sqlglot-find/bench.py 2>&1 | tail -5", "description": "Run find-cache timing benchmark", "timeout": 600000}
[tool_result]     print("cached  :", round(min(run() for _ in range(3)), 3))
                                 ^^^^^
  File "/tmp/bench-sqlglot-find/bench.py", line 20, in run
    annotate_types(e, schema=schema)
TypeError: 'module' object is not callable
[tool_use Bash] {"command": "grep -n \"^def annotate_types\\|^def qualify\\b\" sqlglot/optimizer/annotate_types.py sqlglot/optimizer/qualify.py", "description": "Find annotate_types and qualify function definitions"}
[tool_result] 2 matches in 2 files:

sqlglot/optimizer/annotate_types.py:45:def annotate_types(
sqlglot/optimizer/qualify.py:19:def qualify(
[tool_use Bash] {"command": "sed -i.bak -e 's/^from sqlglot.optimizer import annotate_types$/from sqlglot.optimizer.annotate_types import annotate_types/' -e 's/^from sqlglot.optimizer.qualify import qualify$/from sqlglot.optimizer.qualify import qualify/' /tmp/bench-sqlglot-find/bench.py && rm -f /tmp/bench-sqlglot-find/bench.py.bak && <work>/env-sqlglot/bin/python /tmp/bench-sqlglot-find/bench.py 2>&1 | tail -5", "description": "Rerun benchmark with direct module imports", "timeout": 600000}
[tool_result] cached  : 0.027
uncached: 0.03
[This command modified 1 file you've previously read: ../../../../../../../../tmp/bench-sqlglot-find/bench.py. Call Read before editing.]
[assistant] The timing is modest: about 0.027s cached vs 0.030s uncached on this 3000-column query, roughly 10%. Now the full suite and lint on the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; (<work>/env-sqlglot/bin/python -m ruff --version && <work>/env-sqlglot/bin/python -m ruff check sqlglot/schema.py tests/test_schema.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/schema.py tests/test_schema.py) 2>&1 | tail -5; git diff --stat", "description": "Run full test suite, ruff, and show diff stat", "timeout": 900000}
[tool_result] .................................................................................. [ 98%]
............                           [100%]
1106 passed, 17948 subtests passed in 49.79s
ruff 0.15.6
All checks passed!
2 files already formatted
sqlglot/schema.py    |  7 +++++++
 tests/test_schema.py | 29 +++++++++++++++++++++++++++++
 2 files changed, 36 insertions(+)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/schema.py 2>&1 | tail -3; rm -rf /tmp/bench-sqlglot-find", "description": "Run mypy on schema module and clean scratch files", "timeout": 600000}
[tool_result] Success: no issues found in 1 source file
[assistant] `MappingSchema.find` now caches its results, keyed by table parts, `raise_on_missing`, and `ensure_data_types`. The cache is cleared whenever `add_table` runs. The full suite passes (1106 tests, up from 1104 with two new ones), and ruff and mypy are clean. The changes are uncommitted in the worktree.

**What changed**
- `sqlglot/schema.py`: a new `_find_cache` dict is initialised in `MappingSchema.__init__`. `find` checks it first and stores its result after the lookup. `add_table` clears it after mutating the mapping.
- `tests/test_schema.py`: `test_find_cache` covers repeated lookups, the `e
…[392 chars elided]…
et the same converted dict on repeat calls. Nothing in the repo mutates that result (the only caller, `annotate_types`, only reads it).
- The cache only tracks changes made through `add_table`. Editing `schema.mapping` directly would leave cached results stale. Nothing in the repo does that after construction.

**Performance:** the gain is small. On a synthetic query with 3000 column references across 3 tables, `annotate_types` took about 0.027s with the cache and 0.030s with it cleared on every call, roughly 10%. The lookups were already cheap. The bulk of the time is elsewhere in annotation.
