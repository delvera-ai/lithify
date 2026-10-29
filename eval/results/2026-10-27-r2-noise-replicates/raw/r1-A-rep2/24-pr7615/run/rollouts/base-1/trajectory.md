# trajectory base-1

final message:
`MappingSchema.find` now caches its results per table and `ensure_data_types` setting. The full suite passes (1105 tests, including a new one), but I did not benchmark the speedup on a wide query.

**What changed** (`sqlglot/schema.py`):
- `find` checks a `_find_cache` keyed by `(table, ensure_data_types)` before doing the lookup. It stores only found results. A missing table is never cached, so `raise_on_missing` behaves as before.
- `add_table` clears the cache after updating the mapping. That covers both new tables and changed column sets for existing tables.
- The cache is created before the base-class constructor runs, so `_normalize` can't hit an uninitialised attribute.

**Test** (`tests/test_schema.py`): a new `test_find_cache_invalidated_on_add_table` checks that repeated calls return the same object, and that results after `add_table` reflect the new tables and columns. I did not edit any existing test.

**Caveat:** the cache is only invalidated through `add_table`. If code writes directly into `schema.mapping`, cached results can go stale. Nothing in the repo does that, but it is the one way the cache could return wrong results.

## events
[tool_use Bash] {"command": "grep -n \"\" sqlglot/schema.py | sed -n '1,40p;230,420p'", "description": "Read MappingSchema source region"}
[tool_result] 1:from __future__ import annotations
2:
3:import abc
4:import typing as t
5:
6:from sqlglot import expressions as exp
7:from sqlglot.dialects.dialect import Dialect
8:from sqlglot.errors import SchemaError
9:from sqlglot.helper import dict_depth, first
10:from sqlglot.trie import TrieResult, in_trie, new_trie
11:
12:from sqlglot.helper import trait
13:
14:
15:if t.TYPE_CHECKING:
16:    from sqlglot._typing import SchemaArgs
17:    from sqlglot.dialects.dialect import DialectType
18:    from coll
…[8412 chars elided]…
rsed(parts)), normalized_column_mapping)
409:        new_trie([parts], self.mapping_trie)
410:
411:    def column_names(
412:        self,
413:        table: exp.Table | str,
414:        only_visible: bool = False,
415:        dialect: DialectType = None,
416:        normalize: bool | None = None,
417:    ) -> list[str]:
418:        normalized_table = self._normalize_table(table, dialect=dialect, normalize=normalize)
419:
420:        schema: dict[str, object] | None = self.find(normalized_table)
[tool_use Bash] {"command": "grep -n \"cache\\|mapping_trie\\|self.mapping\\b\\|_depth\\|def \\|nested_set\" sqlglot/schema.py | sed -n '1,400p'; git status --short; git log --oneline -1", "description": "Find caches, mutations and methods in schema.py"}
[tool_result] 9:from sqlglot.helper import dict_depth, first
29:    def dialect(self) -> Dialect | None:
37:    def add_table(
43:        match_depth: bool = True,
54:            match_depth: whether to enforce that the table must match the schema's depth or not.
58:    def column_names(
79:    def get_column_type(
99:    def has_column(
121:    def get_udf_type(
142:    def supported_table_args(self) -> tuple[str, ...]:
148:    def empty(self) -> bool:
154:    def __init__(
159:        self.mapping: dict[str
…[3538 chars elided]…
_schema(
711:def ensure_column_mapping(mapping: ColumnMapping | None) -> dict[str, t.Any]:
728:def flatten_schema(
733:    depth = dict_depth(schema) - 1 if depth is None else depth
744:def nested_get(
771:def nested_set(d: dict[str, t.Any], keys: Sequence[str], value: t.Any) -> dict[str, t.Any]:
776:        >>> nested_set({}, ["top_key", "second_key"], "value")
779:        >>> nested_set({"top_key": {"third_key": "third_value"}}, ["top_key", "second_key"], "value")
28947a65d lithify: probe base
[tool_use Bash] {"command": "sed -n 430,470p sqlglot/schema.py; sed -n 596,626p sqlglot/schema.py; grep -rn \"\\.find(\\|nested_set(\" sqlglot | grep -v \"\\.find_\\|expression.find\\|tree.find\" | head -30; grep -n \"def __hash__\" -A4 sqlglot/expressions.py | head -20", "description": "Inspect lookup callers, table normalization, and hashing"}
[tool_result]     def get_column_type(
        self,
        table: exp.Table | str,
        column: exp.Column | str,
        dialect: DialectType = None,
        normalize: bool | None = None,
    ) -> exp.DataType:
        normalized_table = self._normalize_table(table, dialect=dialect, normalize=normalize)

        normalized_column_name = self._normalize_name(
            column if isinstance(column, str) else column.this, dialect=dialect, normalize=normalize
        )

        table_schema: dict[str, ob
…[4603 chars elided]…
er/merge_subqueries.py:210:        and not any(e.find(exp.AggFunc, exp.Select, exp.Explode) for e in inner_select.expressions)
sqlglot/optimizer/pushdown_predicates.py:216:                select for select in node.selects if select.find(exp.Window)
sqlglot/optimizer/pushdown_projections.py:158:        if not is_agg and selection.find(exp.AggFunc):
sqlglot/optimizer/unnest_subqueries.py:97:    if select.find(exp.Limit, exp.Offset):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[exp.Table, bool], dict[str, object]] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        schema: dict[str, object] | None = super().find(\n            table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\
…[552 chars elided]…
nd isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        # Only found tables are cached, so a result never depends on raise_on_missing\n        if schema is not None:\n            self._find_cache[cache_key] = schema\n\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[assistant] Cache is in place. Running the project's test command now, plus a quick check that the cache is invalidated on `add_table`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.schema import MappingSchema\nfrom sqlglot import exp\ns = MappingSchema({'t': {'a': 'INT'}})\nt = exp.to_table('t')\nprint(s.find(t, ensure_data_types=True), s.find(t, ensure_data_types=True) is s.find(t, ensure_data_types=True))\ns.add_table('t', {'a': 'TEXT', 'b': 'INT'})\nprint(s.find(t, ensure_data_types=True))\nprint(s.find(exp.to_table('missing'), raise_on_missing=False))\n\" 2>&1", "description": "Run test suite and a cache invalidation sanity check"}
[tool_result] ..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 54%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
....................................... [ 65%]
......................................... [ 69%]
.... [ 69%]
.........
…[83 chars elided]…
........... [ 78%]
................................................................................................................................................. [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1104 passed, 17948 subtests passed in 52.38s
{'a': DataType(this=DType.INT, nested=False)} True
{'a': DataType(this=DType.TEXT, nested=False), 'b': DataType(this=DType.INT, nested=False)}
None
[assistant] All 1104 tests pass. I'll add a regression test for the cache behaviour, since the existing suite doesn't exercise it.
[tool_use Bash] {"command": "grep -n \"^class \\|def test_.*find\\|def test_add_table\\|^import\\|^from\" tests/test_schema.py | head -40", "description": "Locate schema test conventions"}
[tool_result] 1:import unittest
3:from sqlglot import exp, parse_one, to_table
4:from sqlglot.errors import SchemaError
5:from sqlglot.schema import MappingSchema, ensure_schema
8:class TestSchema(unittest.TestCase):
337:    def test_find(self):
[tool_use Bash] {"command": "sed -n 337,375p tests/test_schema.py", "description": "Read existing find test for style"}
[tool_result]     def test_find(self):
        schema = MappingSchema({"x": {"c": "int"}})
        found = schema.find(exp.to_table("x"))
        self.assertEqual(found, {"c": "int"})
        found = schema.find(exp.to_table("x"), ensure_data_types=True)
        self.assertEqual(found, {"c": exp.DataType.build("int")})
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"int\")})", "new_string": "        found = schema.find(exp.to_table(\"x\"), ensure
…[453 chars elided]…
missing=False))\n\n        schema.add_table(\"x\", {\"c\": \"text\", \"d\": \"int\"})\n        schema.add_table(\"y\", {\"e\": \"int\"})\n\n        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"text\"), \"d\": exp.DataType.build(\"int\")})\n        self.assertEqual(schema.find(exp.to_table(\"y\")), {\"e\": \"int\"})"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085458-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff --stat", "description": "Run schema tests and full suite, show diff stat"}
[tool_result] ..........                                [100%]
10 passed, 31 subtests passed in 0.04s
1105 passed, 17948 subtests passed in 51.94s
 sqlglot/schema.py    | 10 ++++++++++
 tests/test_schema.py | 15 +++++++++++++++
 2 files changed, 25 insertions(+)
[assistant] `MappingSchema.find` now caches its results per table and `ensure_data_types` setting. The full suite passes (1105 tests, including a new one), but I did not benchmark the speedup on a wide query.

**What changed** (`sqlglot/schema.py`):
- `find` checks a `_find_cache` keyed by `(table, ensure_data_types)` before doing the lookup. It stores only found results. A missing table is never cached, so `raise_on_missing` behaves as before.
- `add_table` clears the cache after updating the mapping. That covers both new tables and changed column sets for existing tables.
- The cache is created before the base-class constructor runs, so `_normalize` can't hit an uninitialised attribute.

**Test** (`tests/test_schema.py`): a new `test_find_cache_invalidated_on_add_table` checks that repeated calls return the same object, and that results after `add_table` reflect the new tables and columns. I did not edit any existing test.

**Caveat:** the cache is only invalidated through `add_table`. If code writes directly into `schema.mapping`, cached results can go stale. Nothing in the repo does that, but it is the one way the cache could return wrong results.
