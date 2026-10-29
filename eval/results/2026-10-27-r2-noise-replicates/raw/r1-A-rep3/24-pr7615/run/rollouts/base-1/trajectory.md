# trajectory base-1

final message:
`MappingSchema.find` now caches its results per instance, and repeated lookups for the same table skip the trie walk and the type conversion. The full suite passes (1104 tests), and ruff lint and format are clean on both changed files. I haven't committed anything.

**What changed**

- **`sqlglot/schema.py`**:
  - `find` caches results in a new `_find_cache`, keyed on the table's resolved name parts, `raise_on_missing`, and `ensure_data_types`. `raise_on_missing` is in the key because a cached `None` must not answer a call that should raise.
  - Calls that raise are not cached.
  - `add_table` clears the cache after it mutates the mapping. That is the only place the mapping changes inside the library, so this covers table additions and column updates.
- **`tests/test_schema.py`**: a new `test_find_cache_invalidated_on_add_table` covers a cached miss that becomes a hit after `add_table`, a changed column set after an update, and both `ensure_data_types` settings.

**Things to know**

- With `ensure_data_types=True`, every call now returns the same converted dict object instead of a fresh one. Values are identical, but a caller that mutated the returned dict would change later results. Nothing in the repo does this.
- If something outside `add_table` mutates `schema.mapping` directly, the cache will not notice. The library does not do that.
- I did not benchmark the speedup. The change is aimed at the many `get_column_type`/`has_column` calls per table during `annotate_types`, but the size of the gain on your wide queries is unmeasured.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"class MappingSchema\" -A 200 sqlglot/schema.py | head -300", "description": "Check git status and view MappingSchema class"}
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
[tool_use Bash] {"command": "grep -n \"_type_mapping_cache\\|_normalized_table_cache\\|_normalized_name_cache\\|def find\\|def _to_data_type\\|mapping_trie\\|_depth\\|def depth\\|def empty\\|def _normalize\\b\" sqlglot/schema.py && sed -n 1,120p sqlglot/schema.py | grep -n \"class\\|def \" ", "description": "Locate caches and find methods in schema.py"}
[tool_result] 9:from sqlglot.helper import dict_depth, first
43:        match_depth: bool = True,
54:            match_depth: whether to enforce that the table must match the schema's depth or not.
148:    def empty(self) -> bool:
160:        self.mapping_trie: dict[str, object] = new_trie(
165:            tuple(reversed(t)) for t in flatten_schema(self.udf_mapping, depth=self.udf_depth())
171:    def empty(self) -> bool:
174:    def depth(self) -> int:
175:        return dict_depth(self.mapping)
177:    def 
…[1830 chars elided]…
ache[schema_type]
733:    depth = dict_depth(schema) - 1 if depth is None else depth
25:class Schema(abc.ABC):
26:    """Abstract base class for database schemas"""
29:    def dialect(self) -> Dialect | None:
31:        Returns None by default. Subclasses that require dialect-specific
37:    def add_table(
46:        Register or update a table. Some implementing classes may require column information to also be provided.
58:    def column_names(
79:    def get_column_type(
99:    def has_column(
[tool_use Bash] {"command": "sed -n 140,260p sqlglot/schema.py && sed -n 480,560p sqlglot/schema.py && sed -n 600,690p sqlglot/schema.py", "description": "Read AbstractMappingSchema find and mutation logic"}
[tool_result]     @property
    @abc.abstractmethod
    def supported_table_args(self) -> tuple[str, ...]:
        """
        Table arguments this schema support, e.g. `("this", "db", "catalog")`
        """

    @property
    def empty(self) -> bool:
        """Returns whether the schema is empty."""
        return True


class AbstractMappingSchema:
    def __init__(
        self,
        mapping: dict[str, object] | None = None,
        udf_mapping: dict[str, object] | None = None,
    ) -> None:
        
…[9435 chars elided]…
False)
                self._type_mapping_cache[schema_type] = expression
            except AttributeError:
                in_dialect = f" in dialect {dialect}" if dialect else ""
                raise SchemaError(f"Failed to build type '{schema_type}'{in_dialect}.")

        return self._type_mapping_cache[schema_type]


def normalize_name(
    identifier: str | exp.Identifier,
    dialect: DialectType = None,
    is_table: bool = False,
    normalize: bool | None = True,
) -> exp.Identifier:
[tool_use Bash] {"command": "grep -rn \"\\.mapping\\b\\s*=\\|\\.mapping\\[\\|mapping_trie\\s*=\\|\\.find(\" sqlglot/ | grep -v \"^sqlglot/schema.py:2[0-9][0-9]:.*def \" ; grep -rn \"_cache\" sqlglot/schema.py tests/test_schema.py | head -30; ls <work>/env-sqlglot/bin/python && git log --oneline -1", "description": "Find mutation sites and existing cache tests"}
[tool_result] sqlglot/planner.py:151:            if e.find(exp.AggFunc):
sqlglot/tokenizer_core.py:1134:        # use str.find() when the string is simple... no \ or other escapes
sqlglot/tokenizer_core.py:1137:            end = sql.find(delimiter, pos)
sqlglot/tokenizer_core.py:1145:                and (not (unescaped_sequences or "\\" in escapes) or sql.find("\\", pos, end) == -1)
sqlglot/transforms.py:431:                explode = select.find(exp.Explode)
sqlglot/transforms.py:446:                        e
…[7593 chars elided]…
hema.py:640:        if cached := self._normalized_name_cache.get(cache_key):
sqlglot/schema.py:650:        self._normalized_name_cache[cache_key] = result
sqlglot/schema.py:670:        if schema_type not in self._type_mapping_cache:
sqlglot/schema.py:677:                self._type_mapping_cache[schema_type] = expression
sqlglot/schema.py:682:        return self._type_mapping_cache[schema_type]
<work>/env-sqlglot/bin/python
306aad63b lithify: probe base
[assistant] The only mutation path for the mapping is `add_table`, so I'll key a per-instance cache on the resolved table parts and the two flags, and clear it there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._depth: int = 0", "new_string": "        self._normalized_name_cache: dict[tuple[str, DialectType, bool, bool], str] = {}\n        self._find_cache: dict[tuple[tuple[str, ...], bool, bool], t.Any] = {}\n        self._depth: int = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "    def find(\n        self, table: exp.Table, raise_on_missing: bool = True, ensure_data_types: bool = False\n    ) -> t.Any | None:\n        schema: dict[str, object] | None = super().find(\n            table, raise_o
…[798 chars elided]…
           table, raise_on_missing=raise_on_missing, ensure_data_types=ensure_data_types\n        )\n        if ensure_data_types and isinstance(schema, dict):\n            schema = {\n                col: self._to_data_type(dtype) if isinstance(dtype, str) else dtype\n                for col, dtype in schema.items()\n            }\n\n        self._find_cache[key] = schema\n        return schema"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py", "old_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)", "new_string": "        nested_set(self.mapping, tuple(reversed(parts)), normalized_column_mapping)\n        new_trie([parts], self.mapping_trie)\n        self._find_cache.clear()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/sqlglot/schema.py has been updated successfully.
[assistant] Now the project's test command, plus a quick check that the cache is hit and invalidated.
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nfrom sqlglot import exp, parse_one\nfrom sqlglot.schema import MappingSchema\ns = MappingSchema({'db': {'t': {'a': 'int', 'b': 'text'}}}, dialect='duckdb')\ntbl = exp.to_table('db.t')\nprint('first', s.find(tbl, ensure_data_types=True))\nprint('second same', s.find(
…[26 chars elided]…
e) is s.find(tbl, ensure_data_types=True))\nprint('miss', s.find(exp.to_table('db.x'), raise_on_missing=False))\ns.add_table('db.x', {'c': 'int'})\nprint('after add', s.find(exp.to_table('db.x'), raise_on_missing=False))\ns.add_table('db.t', {'a': 'int', 'z': 'text'})\nprint('updated', s.find(tbl, raise_on_missing=False))\n\"", "description": "Sanity-check cache hit and invalidation on add_table"}
[tool_result] first {'a': DataType(this=DType.INT, nested=False), 'b': DataType(this=DType.TEXT)}
second same True
miss None
after add {'c': 'int'}
updated {'a': 'int', 'z': 'text'}
[assistant] The cache hits and invalidates correctly. The test run failed only because `timeout` isn't installed here, so I'm rerunning it without that wrapper.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite", "timeout": 600000}
[tool_result] ..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 54%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
....................................... [ 65%]
......................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
................................................................................................................................................. [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1104 passed, 17948 subtests passed in 50.41s
[assistant] All 1104 tests pass. The repo guidance asks for a test on non-trivial changes, so I'll add one for cache invalidation and lint the file.
[tool_use Bash] {"command": "grep -n \"^class \\|    def test_\" tests/test_schema.py | head -40; sed -n 1,20p tests/test_schema.py | grep import", "description": "Inspect test_schema.py structure"}
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
import unittest
from sqlglot import exp, parse_one, to_table
from sqlglot.errors import SchemaError
from sqlglot.schema import MappingSchema, ensure_schema
[tool_use Bash] {"command": "sed -n 337,400p tests/test_schema.py", "description": "View existing find test"}
[tool_result]     def test_find(self):
        schema = MappingSchema({"x": {"c": "int"}})
        found = schema.find(exp.to_table("x"))
        self.assertEqual(found, {"c": "int"})
        found = schema.find(exp.to_table("x"), ensure_data_types=True)
        self.assertEqual(found, {"c": exp.DataType.build("int")})
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/tests/test_schema.py", "old_string": "        found = schema.find(exp.to_table(\"x\"), ensure_data_types=True)\n        self.assertEqual(found, {\"c\": exp.DataType.build(\"int\")})", "new_string": "        found = schema.find(exp.to_table(\"x\"), ensure
…[505 chars elided]…
\"})\n        self.assertEqual(\n            schema.find(exp.to_table(\"y\"), ensure_data_types=True),\n            {\"d\": exp.DataType.build(\"text\")},\n        )\n\n        schema.add_table(\"x\", {\"c\": \"int\", \"e\": \"int\"})\n        self.assertEqual(schema.find(exp.to_table(\"x\")), {\"c\": \"int\", \"e\": \"int\"})\n        self.assertEqual(schema.column_names(\"x\"), [\"c\", \"e\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122624-schema-performance-mappingschema/base-1/tests/test_schema.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/python -m pytest -q -p no:cacheprovider --color=no tests/test_schema.py 2>&1 | tail -3; ($P/ruff check sqlglot/schema.py tests/test_schema.py && $P/ruff format --check sqlglot/schema.py tests/test_schema.py) 2>&1 | tail -5", "description": "Run schema tests and ruff lint/format check"}
[tool_result] ..........                                [100%]
10 passed, 31 subtests passed in 0.04s
All checks passed!
2 files already formatted
[assistant] `MappingSchema.find` now caches its results per instance, and repeated lookups for the same table skip the trie walk and the type conversion. The full suite passes (1104 tests), and ruff lint and format are clean on both changed files. I haven't committed anything.

**What changed**

- **`sqlglot/schema.py`**:
  - `find` caches results in a new `_find_cache`, keyed on the table's resolved name parts, `raise_on_missing`, and `ensure_data_types`. `raise_on_missing` is in the key because a cached `None` must not answer a call that should raise.
  - Calls that raise are not cached.
  - `add_table`
…[360 chars elided]…
types` settings.

**Things to know**

- With `ensure_data_types=True`, every call now returns the same converted dict object instead of a fresh one. Values are identical, but a caller that mutated the returned dict would change later results. Nothing in the repo does this.
- If something outside `add_table` mutates `schema.mapping` directly, the cache will not notice. The library does not do that.
- I did not benchmark the speedup. The change is aimed at the many `get_column_type`/`has_column` calls per table during `annotate_types`, but the size of the gain on your wide queries is unmeasured.
