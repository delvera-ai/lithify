# trajectory base-1

final message:
The `find` lookups are now cached in `MappingSchema`, and the full test suite passes (1105 passed). The changes are uncommitted in the worktree.

**What changed**

- **`sqlglot/schema.py`**: `MappingSchema.find` caches its result in `self._find_cache`, keyed by `(table, raise_on_missing, ensure_data_types)`. `raise_on_missing` is in the key because it changes results for ambiguous tables (`None` vs. raising). `add_table` clears the cache after it mutates the mapping, so tables added or updated later are visible immediately.
- **`tests/test_schema.py`**: new `test_find_cache_invalidated_on_add_table`. It checks that a cached miss is replaced after `add_table` and that an updated table's columns show up on both the plain and `ensure_data_types=True` paths.

**Measurements**

- 20k `find` calls on a 300-column table: `ensure_data_types=True` went from 0.385s to 0.005s. The default path went from 0.025s to 0.004s.
- The `annotate_types` benchmark on a 900-column, 3-table join showed no measurable difference (about 0.007s before and 0.006s after). Its 904 `find` calls are cheap on small dicts, so the wall-clock win there is negligible. The gain is in the per-call cost.
- Output is identical before and after under a fixed `PYTHONHASHSEED`.

**Things to know**

- Mutating `schema.mapping` directly, outside `add_table`, is not detected, so the cache would go stale. `add_table` is the only in-library mutation path I found.
- With `ensure_data_types=True`, callers now get the same dict object on repeat calls instead of a fresh one. The library doesn't mutate these results, but external code that does would now see the change on later calls.
- I did not commit. The project's CLAUDE.md asks for model attribution in commit messages and PR titles, so I can add that when you commit or open the PR.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"class \\|def \\|_normalize\\|ensure_data_types\\|_depth\\|self\\._\" sqlglot/schema.py | head -200", "description": "Inspect schema.py structure and MappingSchema methods"}
[tool_result] 9:from sqlglot.helper import dict_depth, first
25:class Schema(abc.ABC):
26:    """Abstract base class for database schemas"""
29:    def dialect(self) -> Dialect | None:
37:    def add_table(
43:        match_depth: bool = True,
54:            match_depth: whether to enforce that the table must match the schema's depth or not.
58:    def column_names(
79:    def get_column_type(
99:    def has_column(
121:    def get_udf_type(
142:    def supported_table_args(self) -> tuple[str, ...]:
148:    d
…[5165 chars elided]…
ype not in self._type_mapping_cache:
677:                self._type_mapping_cache[schema_type] = expression
682:        return self._type_mapping_cache[schema_type]
685:def normalize_name(
702:def ensure_schema(
711:def ensure_column_mapping(mapping: ColumnMapping | None) -> dict[str, t.Any]:
728:def flatten_schema(
733:    depth = dict_depth(schema) - 1 if depth is None else depth
744:def nested_get(
771:def nested_set(d: dict[str, t.Any], keys: Sequence[str], value: t.Any) -> dict[str, t.Any]:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py", "offset": 150, "limit": 420}
[tool_result] 150	        return True
151	
152	
153	class AbstractMappingSchema:
154	    def __init__(
155	        self,
156	        mapping: dict[str, object] | None = None,
157	        udf_mapping: dict[str, object] | None = None,
158	    ) -> None:
159	        self.mapping: dict[str, object] = mapping or {}
160	        self.mapping_trie: dict[str, object] = new_trie(
161	            tuple(reversed(t)) for t in flatten_schema(self.mapping, depth=self.depth())
162	        )
163	        self.udf_mapping: dict
…[16100 chars elided]…
t_depth(udfs)):
557	            udf_type = nested_get(udfs, *zip(keys, keys))
558	            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
559	            nested_set(normalized_mapping, normalized_keys, udf_type)
560	
561	        return normalized_mapping
562	
563	    def _normalize_udf(
564	        self,
565	        udf: exp.Anonymous | str,
566	        dialect: DialectType = None,
567	        normalize: bool | None = None,
568	    ) -> list[str]:
569	        """
[tool_use Bash] {"command": "grep -n \"def __hash__\\|def __eq__\" -A8 sqlglot/expressions.py | head -60; grep -rn \"\\.mapping\\b\\|mapping_trie\\|_normalized_table_cache\" sqlglot/ --include=*.py | grep -v \"udf_mapping\" | head -40; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Check expression hashing and mapping mutation sites"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
(eval):1: no matches found: --include=*.py
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "rg -n \"def __hash__|def __eq__\" -A6 sqlglot/ | head -60; rg -n \"\\.mapping\\b|mapping_trie|_normalized_table_cache\" sqlglot/ | grep -v udf_mapping", "description": "Find hash/eq definitions and mapping mutation sites"}
[tool_result] sqlglot/expressions/core.py:831:    def __eq__(self, other: object) -> bool:
sqlglot/expressions/core.py-832-        return self is other or (type(self) is type(other) and hash(self) == hash(other))
sqlglot/expressions/core.py-833-
sqlglot/expressions/core.py-834-    def __ne__(self, other: object) -> bool:
sqlglot/expressions/core.py-835-        return not self.__eq__(other)
sqlglot/expressions/core.py-836-
sqlglot/expressions/core.py:837:    def __hash__(self) -> int:
sqlglot/expressions/core.
…[3411 chars elided]…
.py:409:        new_trie([parts], self.mapping_trie)
sqlglot/schema.py:611:            cached := self._normalized_table_cache.get((table, dialect, normalize))
sqlglot/schema.py:624:        self._normalized_table_cache[(normalized_table, dialect, normalize)] = normalized_table
sqlglot/executor/__init__.py:57:        flattened_tables = flatten_schema(tables_.mapping, depth=dict_depth(tables_.mapping))
sqlglot/executor/__init__.py:60:            table = nested_get(tables_.mapping, *zip(keys, keys))
[tool_use Bash] {"command": "rg -n \"ensure_data_types|\\.find\\(\" sqlglot/ | head -30; rg -n \"_hash = None|_hash=None\" sqlglot/expressions/core.py | head; git log --oneline -1", "description": "Check ensure_data_types and find usages"}
[tool_result] sqlglot/schema.py:230:        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False
sqlglot/schema.py:238:            ensure_data_types: whether to convert `str` types to their `DataType` equivalents.
sqlglot/schema.py:345:        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False
sqlglot/schema.py:347:        schema: dict[str, object] | None = super().find(
sqlglot/schema.py:348:            table, raise_on_missing=raise_on_mis
…[2010 chars elided]…
edProperty)
sqlglot/generators/snowflake.py:1017:        copy_grants_property = expression.find(exp.CopyGrantsProperty)
sqlglot/generators/tsql.py:51:    distinct = expression.find(exp.Distinct)
sqlglot/generators/tsql.py:400:        like_property = expression.find(exp.LikeProperty)
sqlglot/generators/tsql.py:415:        table = expression.find(exp.Table)
sqlglot/generators/tsql.py:461:            table = expression.find(exp.Table)
1060:            node._hash = None
311efdf74 lithify: probe base
[assistant] Baseline first: a wide-query benchmark outside the repo, so I can measure the change.
[tool_use Bash] {"command": "mkdir -p /tmp/schema_bench && cat > /tmp/schema_bench/bench.py <<'EOF'\nimport time\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.schema import MappingSchema\n\nN_COLS = 300\nTABLES = [\"t1\", \"t2\", \"t3\"]\nschema = {t: {f\"c{i}\": \"INT\" for i in range(N_COLS)} for t in TABLES}\nprojs = \", \".join(f\"{t}.c{i}\
…[590 chars elided]…
\"sample types:\", types[:3])\nEOF\ncd ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1 && PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/schema_bench/bench.py", "description": "Run baseline annotate_types benchmark"}
[tool_result] annotate_types best of 3: 0.008s, column types digest=-4903255481370635194
sample types: ['INT', 'INT', 'INT']
[assistant] The timing is suspiciously low, so I'll count how many `find` calls actually happen before trusting it.
[tool_use Bash] {"command": "cd /tmp/schema_bench && cat > count.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.schema import MappingSchema\nimport sqlglot.schema as S\nexec(open(\"/tmp/schema_bench/bench.py\").read().split(\"best = None\")[0])\ncalls = {\"n\": 0}\norig = MappingSchema.find\ndef counting(self, *a, **k):\n    calls[\"n\"] += 1\n    return orig
…[250 chars elided]…
ype) for c in out.selects}))\nEOF\ncd ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1 && PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/schema_bench/count.py", "description": "Count find calls during annotate_types"}
[tool_result] find calls: 904 | types: ['INT']
[assistant] Lookups are real (904 `find` calls for this query), so the cache has something to hit. Now the change: a cache in `MappingSchema.find`, keyed by table, `raise_on_missing`, and `ensure_data_types`, cleared whenever `add_table` mutates the mapping.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[exp.Table, bool, bool], t.Any] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "    ) -> t.Any | None:\n        schema: dict[str, object] | None = super().find(\n            table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and is
…[464 chars elided]…
           table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        self._find_cache[key] = schema\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[assistant] Now a microbenchmark on `find` itself, plus a check that the cache is invalidated correctly on `add_table`.
[tool_use Bash] {"command": "cat > /tmp/schema_bench/micro.py <<'EOF'\nimport time\nfrom sqlglot import exp, parse_one\nfrom sqlglot.schema import MappingSchema\nschema = {f\"t{j}\": {f\"c{i}\": \"INT\" for i in range(300)} for j in range(3)}\ns = MappingSchema(schema, dialect=\"duckdb\")\ntbl = parse_one(\"t1\", into=exp.Table, dialect=\"duckdb\")\nfor kw in ({}, {\"ensure_data_types\": True}):\n    start = time
…[574 chars elided]…
&& git archive HEAD sqlglot | tar -x -C /tmp/schema_bench/orig\necho \"--- before:\"; PYTHONPATH=/tmp/schema_bench/orig $P /tmp/schema_bench/micro.py\necho \"--- annotate bench after:\"; PYTHONPATH=. $P /tmp/schema_bench/bench.py\necho \"--- annotate bench before:\"; PYTHONPATH=/tmp/schema_bench/orig $P /tmp/schema_bench/bench.py", "description": "Benchmark find before and after the cache change"}
[tool_result] --- after:
default 0.004s for 20k finds
{'ensure_data_types': True} 0.005s for 20k finds
--- before:
default 0.025s for 20k finds
{'ensure_data_types': True} 0.385s for 20k finds
--- annotate bench after:
annotate_types best of 3: 0.006s, column types digest=-8443644152441153960
sample types: ['INT', 'INT', 'INT']
--- annotate bench before:
annotate_types best of 3: 0.007s, column types digest=6436106121682746095
sample types: ['INT', 'INT', 'INT']
[assistant] The `ensure_data_types=True` path went from 0.385s to 0.005s per 20k lookups; the default path was already cheap. The annotate digests differ only because Python's string hash is randomized per process, so I'll check result equality with a deterministic comparison. Next, adding a regression test for cache invalidation, following the existing test style.
[tool_use Bash] {"command": "rg -n \"def test_|^class \" tests/test_schema.py | head -60; rg -n \"def test_add_table|def test_find\" -A22 tests/test_schema.py | head -60", "description": "Look at existing schema test style"}
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
337:    def test_find(self):
338-        schema = MappingSchema({"x": {"c": "int"}})
339-        found = schema.find(exp.to_table("x"))
340-        self.assertEqual(found, {"c": "int"})
341-        found = schema.find(exp.to_table("x"), ensure_data_types=True)
342-        self.assertEqual(found, {"c": exp.DataType.build("int")})
[tool_use Bash] {"command": "sed -n 332,360p tests/test_schema.py", "description": "Read end of find test"}
[tool_result]     def test_has_column(self):
        schema = MappingSchema({"x": {"c": "int"}})
        self.assertTrue(schema.has_column("x", exp.column("c")))
        self.assertFalse(schema.has_column("x", exp.column("k")))

    def test_find(self):
        schema = MappingSchema({"x": {"c": "int"}})
        found = schema.find(exp.to_table("x"))
        self.assertEqual(found, {"c": "int"})
        found = schema.find(exp.to_table("x"), ensure_data_types=True)
        self.assertEqual(found, {"c": exp.DataType.build("int")})
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"int\")})", "new_string": "        found = schema.find(exp.to_table(\"x\"), ensure
…[637 chars elided]…
Type.build(\"text\")},\n        )\n\n        schema.add_table(\"x\", {\"c\": \"int\", \"e\": \"float\"})\n        self.assertEqual(schema.find(exp.to_table(\"x\")), {\"c\": \"int\", \"e\": \"float\"})\n        self.assertEqual(\n            schema.find(exp.to_table(\"x\"), ensure_data_types=True),\n            {\"c\": exp.DataType.build(\"int\"), \"e\": exp.DataType.build(\"float\")},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-145124-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[assistant] Running the project's check command (full suite) now.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
........................................................................ [ 31%]
..................................................................... [ 38%]
......................................
…[312 chars elided]…
%]
......................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
................................................................................................................................................. [ 91%]
.............................................................................................                            [100%]
1105 passed, 17948 subtests passed in 59.44s
[assistant] All 1105 tests pass. Last, an output-equality check: the same annotate run before and after with a fixed hash seed.
[tool_use Bash] {"command": "cd /tmp/schema_bench && cat > equal.py <<'EOF'\nimport sqlglot\nfrom sqlglot.optimizer.annotate_types import annotate_types\nfrom sqlglot.schema import MappingSchema\nschema = {\"t1\": {\"a\": \"INT\", \"b\": \"TEXT\"}, \"db.t2\": {\"a\": \"DOUBLE\", \"c\": \"DATE\"}}\nsql = \"SELECT t1.a, t1.b, t2.a AS x, t2.c, t1.a + t2.a AS s FROM t1 JOIN db.t2 AS t2 ON t1.a = t2.a\"\ns = MappingSc
…[423 chars elided]…
6-145124-schema-performance-mappingschema/base-1\nA=$(PYTHONHASHSEED=0 PYTHONPATH=/tmp/schema_bench/orig $P /tmp/schema_bench/equal.py); B=$(PYTHONHASHSEED=0 PYTHONPATH=. $P /tmp/schema_bench/equal.py)\n[ \"$A\" = \"$B\" ] && echo \"IDENTICAL\" || { echo DIFF; echo \"$A\"; echo \"$B\"; }; echo \"$B\"\ngit status --short", "description": "Verify annotate_types output is identical before and after"}
[tool_result] IDENTICAL
[('a', 'INT'), ('b', 'TEXT'), ('x', 'UNKNOWN'), ('c', 'UNKNOWN'), ('s', 'UNKNOWN')]
SELECT t1.a, t1.b, t2.a AS x, t2.c, t1.a + t2.a AS s FROM t1 JOIN db.t2 AS t2 ON t1.a = t2.a
 M sqlglot/schema.py
 M tests/test_schema.py
[assistant] The `find` lookups are now cached in `MappingSchema`, and the full test suite passes (1105 passed). The changes are uncommitted in the worktree.

**What changed**

- **`sqlglot/schema.py`**: `MappingSchema.find` caches its result in `self._find_cache`, keyed by `(table, raise_on_missing, ensure_data_types)`. `raise_on_missing` is in the key because it changes results for ambiguous tables (`None` vs. raising). `add_table` clears the cache after it mutates the mapping, so tables added or updated later are visible immediately.
- **`tests/test_schema.py`**: new `test_find_cache_invalidated_on_add_
…[613 chars elided]…
nd after under a fixed `PYTHONHASHSEED`.

**Things to know**

- Mutating `schema.mapping` directly, outside `add_table`, is not detected, so the cache would go stale. `add_table` is the only in-library mutation path I found.
- With `ensure_data_types=True`, callers now get the same dict object on repeat calls instead of a fresh one. The library doesn't mutate these results, but external code that does would now see the change on later calls.
- I did not commit. The project's CLAUDE.md asks for model attribution in commit messages and PR titles, so I can add that when you commit or open the PR.
