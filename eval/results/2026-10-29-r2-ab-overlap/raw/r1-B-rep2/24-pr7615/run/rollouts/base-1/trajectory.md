# trajectory base-1

final message:
`MappingSchema.find` now caches its results per table, and the cache is cleared whenever `add_table` changes the schema. The full suite passes (1105 tests), but the speedup on my benchmark was negligible, so this doesn't yet justify a performance claim.

**What changed**
- **`sqlglot/schema.py`**: `find` keys a per-instance `_find_cache` on the table's name parts plus `raise_on_missing` and `ensure_data_types`. The key includes both flags because they change the result: `raise_on_missing` changes whether a miss raises or returns `None`, and `ensure_data_types` changes the returned types. Exceptions are never cached. `add_table` clears the cache after it mutates the mapping and trie.
- **`tests/test_schema.py`**: added `test_find_cache_invalidated_by_add_table`. It covers a cached miss that becomes a hit after `add_table`, an update to an existing table, and the `ensure_data_types=True` path.

**Results**
- `tests/test_schema.py` and `tests/test_optimizer.py`: 87 passed, and the new test passes.
- Full suite: 1105 passed.
- Benchmark: a synthetic query with 4,000 column references across three tables went from 0.028s to 0.026s. `find` was called 4,004 times and took about 9ms cumulative under cProfile, so the cache removes a small share of the time for this workload. Wider or deeper queries may benefit more, but I did not measure one.

**Things to know**
- Invalidation covers `add_table` only. Code that writes to `schema.mapping` directly already bypasses the trie, so it was never a supported mutation path, but it will now also leave the cache stale.
- With `ensure_data_types=True`, callers now receive the same dict object on repeated calls rather than a fresh one. `annotate_types` only reads it, but a caller that mutated it would corrupt later lookups.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo's CLAUDE.md asks for.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"class MappingSchema\" -A 5 sqlglot/schema.py && grep -n \"def find\\|def _depth\\|def _normalize\\|def add_table\\|def _to_data_type\\|def _ensure\\|def __init__\\|ensure_data_types\\|_schema_cache\\|self.mapping_trie\\|def _normalize_name\\|def column_names\\|def get_column_type\\|def _find_table\\|def _get_table\" sqlglot/schema.py", "description": "Check repo state and locate MappingSchema methods"}
[tool_result] ok287:class MappingSchema(AbstractMappingSchema, Schema):
288-    """
289-    Schema based on a nested mapping.
290-
291-    Args:
292-        schema: Mapping in one of the following forms:
25 matches in 10 files:

160:0:dict[str, object] = new_trie(
230:0:exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False
238:0:whether to convert `str` types to their `DataType` equivalents.
251:0:exp.Anonymous, raise_on_missing: bool = False) -> t.Any | None:
345:0:exp.Table, raise_on_mis
…[471 chars elided]…
_trie, raise_on_missing)
sqlglot/schema.py:306:def __init__(
sqlglot/schema.py:344:def find(
sqlglot/schema.py:348:table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types
sqlglot/schema.py:370:def add_table(
sqlglot/schema.py:409:new_trie([parts], self.mapping_trie)
sqlglot/schema.py:411:def column_names(
sqlglot/schema.py:430:def get_column_type(
sqlglot/schema.py:563:def _normalize_udf(
sqlglot/schema.py:599:def _normalize_table(
sqlglot/schema.py:627:def _normalize_name(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py", "offset": 140, "limit": 420}
[tool_result] 140	    @property
141	    @abc.abstractmethod
142	    def supported_table_args(self) -> tuple[str, ...]:
143	        """
144	        Table arguments this schema support, e.g. `("this", "db", "catalog")`
145	        """
146	
147	    @property
148	    def empty(self) -> bool:
149	        """Returns whether the schema is empty."""
150	        return True
151	
152	
153	class AbstractMappingSchema:
154	    def __init__(
155	        self,
156	        mapping: dict[str, object] | None = None,
157	     
…[16174 chars elided]…
gs:
549	            udfs: the UDF mapping to normalize.
550	
551	        Returns:
552	            The normalized UDF mapping.
553	        """
554	        normalized_mapping: dict[str, object] = {}
555	
556	        for keys in flatten_schema(udfs, depth=dict_depth(udfs)):
557	            udf_type = nested_get(udfs, *zip(keys, keys))
558	            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
559	            nested_set(normalized_mapping, normalized_keys, udf_type)
[tool_use Bash] {"command": "grep -rn \"\\.find(\\|\\.mapping\\[\\|\\.mapping\\.\\(update\\|pop\\|clear\\|setdefault\\)\\|mapping_trie\\|_type_mapping_cache\\|_normalized_table_cache\" --include=*.py sqlglot tests | grep -v \"str.find\\|\\.find(exp\\.\\|expression.find\\|\\.find(\\\"\" | head -60", "description": "Find schema find() callers and direct mapping mutations"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -e \"schema\\.find(\" -e \"\\.find(table\" -e \"\\.mapping\\[\" -e \"\\.mapping\\.\\(update\\|pop\\|clear\\|setdefault\\)\" -e \"mapping_trie\" -e \"_type_mapping_cache\" -e \"_normalized_table_cache\" sqlglot tests | head -60", "description": "Search for schema find callers and direct mapping mutations"}
[tool_result] sqlglot/optimizer/annotate_types.py:348:                    schema = self.schema.find(
sqlglot/generators/starrocks.py:280:            primary_key = schema.find(exp.PrimaryKey)
sqlglot/schema.py:160:        self.mapping_trie: dict[str, object] = new_trie(
sqlglot/schema.py:244:        resolved_parts = self._find_in_trie(parts, self.mapping_trie, raise_on_missing)
sqlglot/schema.py:317:        self._type_mapping_cache: dict[str, exp.DataType] = {}
sqlglot/schema.py:318:        self._normalized_ta
…[269 chars elided]…
   self._normalized_table_cache[(normalized_table, dialect, normalize)] = normalized_table
sqlglot/schema.py:670:        if schema_type not in self._type_mapping_cache:
sqlglot/schema.py:677:                self._type_mapping_cache[schema_type] = expression
sqlglot/schema.py:682:        return self._type_mapping_cache[schema_type]
tests/test_schema.py:339:        found = schema.find(exp.to_table("x"))
tests/test_schema.py:341:        found = schema.find(exp.to_table("x"), ensure_data_types=True)
[tool_use Bash] {"command": "sed -n 325,375p sqlglot/optimizer/annotate_types.py && sed -n 325,350p tests/test_schema.py && sed -n 596,630p sqlglot/schema.py", "description": "Read annotate_types find call and schema cache code"}
[tool_result]                             alias: column.type for alias, column in zip(alias_column_names, values)
                        }
                elif isinstance(expression, exp.SetOperation) and len(
                    expression.left.selects
                ) == len(expression.right.selects):
                    selects[name] = self._get_setop_column_types(expression)
                elif isinstance(expression, exp.Selectable):
                    selects[name] = {s.alias_or_name: s.type for s in
…[3302 chars elided]…
ze:
            for part in normalized_table.parts:
                if isinstance(part, exp.Identifier):
                    part.replace(
                        normalize_name(part, dialect=dialect, is_table=True, normalize=normalize)
                    )

        self._normalized_table_cache[(normalized_table, dialect, normalize)] = normalized_table
        return normalized_table

    def _normalize_name(
        self,
        name: str | exp.Identifier,
        dialect: DialectType = None,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py tests/test_optimizer.py 2>&1 | tail -5", "description": "Run baseline schema and optimizer tests"}
[tool_result] <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
............................................................ [ 68%]
............... [ 86%]
............                                                                   [100%]
87 passed, 3807 subtests passed in 16.32s
[assistant] Baseline passes. Now the change: a per-schema cache keyed by table parts and the two flags, cleared whenever `add_table` mutates the mapping.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[tuple[str, ...], bool, bool], t.Any] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "    def find(\n        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False\n    ) -> t.Any | None:\n        schema: dict[str, object] | None = super().find(\n            table, raise_o
…[711 chars elided]…
           table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        self._find_cache[key] = schema\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[assistant] Now a test covering the cache-invalidation cases: a miss that becomes a hit after `add_table`, an update to an existing table, and the `ensure_data_types` variant.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"int\")})\n", "new_string": "        found = schema.find(exp.to_table(\"x\"), ensu
…[422 chars elided]…
"})\n        self.assertEqual(schema.find(exp.to_table(\"y\")), {\"d\": \"text\"})\n        self.assertEqual(\n            schema.find(exp.to_table(\"y\"), ensure_data_types=True),\n            {\"d\": exp.DataType.build(\"text\")},\n        )\n\n        schema.add_table(\"x\", {\"e\": \"bigint\"})\n        self.assertEqual(schema.find(exp.to_table(\"x\")), {\"c\": \"int\", \"e\": \"bigint\"})\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py tests/test_optimizer.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py -k find_cache 2>&1 | tail -2; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py 2>&1 | tail -2", "description": "Run schema, optimizer and new cache tests"}
[tool_result] =========================== short test summary info ============================
FAILED tests/test_schema.py::TestSchema::test_find_cache_invalidated_by_add_table
1 failed, 87 passed, 3807 subtests passed in 16.36s
FAILED tests/test_schema.py::TestSchema::test_find_cache_invalidated_by_add_table
1 failed, 9 deselected in 0.03s
.......                                            [100%]
58 passed, 1051 subtests passed in 0.37s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py -k find_cache 2>&1 | grep -B5 \"Error\" | head -40", "description": "Show failure detail for new test"}
[tool_result]             {"d": exp.DataType.build("text")},
        )
    
        schema.add_table("x", {"e": "bigint"})
>       self.assertEqual(schema.find(exp.to_table("x")), {"c": "int", "e": "bigint"})
E       AssertionError: {'e': 'bigint'} != {'c': 'int', 'e': 'bigint'}
E       - {'e': 'bigint'}
E       + {'c': 'int', 'e': 'bigint'}

tests/test_schema.py:357: AssertionError
[assistant] The failure is in my test's expectation, not the cache: `add_table` replaces a table's column mapping rather than merging into it. I'll confirm that against the uncached path before fixing the assertion.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'x': {'c': 'int'}})\ns.add_table('x', {'e': 'bigint'})\nprint(s.find(exp.to_table('x')), s.mapping)\ns2 = MappingSchema({'x': {'c': 'int'}})\ns2.mapping['x'] = {'e': 'bigint'}\nprint(s2.find(exp.to_table('x')))\n\"", "description": "Confirm add_table replaces column mapping"}
[tool_result] {'e': 'bigint'} {'x': {'e': 'bigint'}}
{'e': 'bigint'}
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        self.assertEqual(schema.find(exp.to_table(\"x\")), {\"c\": \"int\", \"e\": \"bigint\"})", "new_string": "        self.assertEqual(schema.find(exp.to_table(\"x\")), {\"e\": \"bigint\"})"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[assistant] Now the full suite as the final gate, plus a quick timing check on a wide query to confirm the cache actually helps.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4", "description": "Run full test suite", "timeout": 600000}
[tool_use Bash] {"command": "cat > /tmp/bench_find.py <<'EOF'\nimport time\nfrom sqlglot import parse_one\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.schema import MappingSchema\ncols = {f\"c{i}\": \"int\" for i in range(40)}\nschema = MappingSchema({\"t1\": cols, \"t2\": cols, \"t3\": cols})\nsql = \"SELECT \" + \", \".join(f\"t{i%3+1}.c{i%40}\" for i in range(4000)) + \" FROM t1 J
…[277 chars elided]…
\"; PYTHONPATH=. $PY -I /tmp/bench_find.py; git stash list >/dev/null; git show HEAD:sqlglot/schema.py > /tmp/orig_schema.py; mkdir -p /tmp/orig_pkg && rm -rf /tmp/orig_pkg/sqlglot && git archive HEAD sqlglot | tar -x -C /tmp/orig_pkg && echo \"before:\" && PYTHONPATH=/tmp/orig_pkg $PY -I /tmp/bench_find.py", "description": "Benchmark annotate_types before and after the change", "timeout": 600000}
[tool_result] ............................................. [ 78%]
................................................................................................................................................. [ 91%]
.............................................................................................                            [100%]
1105 passed, 17948 subtests passed in 52.25s
[tool_result ERROR] Exit code 1
after:
Traceback (most recent call last):
  File "/tmp/bench_find.py", line 2, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
before:
Traceback (most recent call last):
  File "/tmp/bench_find.py", line 2, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The suite passes (1105 tests). The benchmark failed only because `-I` ignores `PYTHONPATH`; rerunning without it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; echo \"after:\"; PYTHONPATH=$PWD $PY /tmp/bench_find.py; echo \"before:\"; PYTHONPATH=/tmp/orig_pkg $PY /tmp/bench_find.py; rm -rf /tmp/orig_pkg /tmp/orig_schema.py", "description": "Run benchmark before and after the change", "timeout": 600000}
[tool_result] after:
0.026s
before:
0.028s
[assistant] The timing gain is small on this workload (26ms vs 28ms). Before reporting, I'll check whether `find` is actually a meaningful share of the time here.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport cProfile, pstats, io\nexec(open('/tmp/bench_find.py').read().replace('t = time.perf_counter()','pr = cProfile.Profile(); pr.enable(); t = time.perf_counter()').replace('print(f\\\"{time.perf_counter() - t:.3f}s\\\")','pr.disable(); s=io.StringIO(); pstats.Stats(pr,stream=s).sort_stats(\\\"cumtime\\\").print_stats(\\\"find\\\"); print(s.getvalue()[:1500])'))\n\" 2>&1 | grep -E \"find|ncalls\" | head -8", "description": "Profile find() call count and time"}
[tool_result]    List reduced from 153 to 3 due to restriction <'find'>
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     4004    0.001    0.000    0.009    0.000 ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py:345(find)
        3    0.000    0.000    0.000    0.000 ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py:229(find)
        3    0.000    0.000    0.000    0.000 ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150836-schema-performance-mappingschema/base-1/sqlglot/schema.py:203(_find_in_trie)
[tool_use Bash] {"command": "rm -f /tmp/bench_find.py && git status --short && git diff", "description": "Review final diff and clean up temp file"}
[tool_result]  M sqlglot/schema.py
 M tests/test_schema.pysqlglot/schema.py    |  7 +++++++
 tests/test_schema.py | 15 +++++++++++++++
 2 files changed, 22 insertions(+)

--- Changes ---

sqlglot/schema.py
  @@ -317,6 +317,7 @@ class MappingSchema(AbstractMappingSchema, Schema):
  +        self._find_cache: dict[tuple[tuple[str, ...], bool, bool], t.Any] = {}
           self._depth: int = 0
           schema = {} if schema is None else schema
           udf_mapping = {} if udf_mapping is None else udf_mapping
…[1030 chars elided]…
        self.assertEqual(schema.find(exp.to_table("x")), {"c": "int"})
  +
  +        schema.add_table("y", {"d": "text"})
  +        self.assertEqual(schema.find(exp.to_table("y")), {"d": "text"})
  +        self.assertEqual(
  +            schema.find(exp.to_table("y"), ensure_data_types=True),
  +            {"d": exp.DataType.build("text")},
  +        )
  +
  +        schema.add_table("x", {"e": "bigint"})
  +        self.assertEqual(schema.find(exp.to_table("x")), {"e": "bigint"})
  +15 -0
[assistant] `MappingSchema.find` now caches its results per table, and the cache is cleared whenever `add_table` changes the schema. The full suite passes (1105 tests), but the speedup on my benchmark was negligible, so this doesn't yet justify a performance claim.

**What changed**
- **`sqlglot/schema.py`**: `find` keys a per-instance `_find_cache` on the table's name parts plus `raise_on_missing` and `ensure_data_types`. The key includes both flags because they change the result: `raise_on_missing` changes whether a miss raises or returns `None`, and `ensure_data_types` changes the returned types. Excep
…[705 chars elided]…
eries may benefit more, but I did not measure one.

**Things to know**
- Invalidation covers `add_table` only. Code that writes to `schema.mapping` directly already bypasses the trie, so it was never a supported mutation path, but it will now also leave the cache stale.
- With `ensure_data_types=True`, callers now receive the same dict object on repeated calls rather than a fresh one. `annotate_types` only reads it, but a caller that mutated it would corrupt later lookups.

I haven't committed anything. Say if you want a commit, and I'll add the model attribution the repo's CLAUDE.md asks for.
