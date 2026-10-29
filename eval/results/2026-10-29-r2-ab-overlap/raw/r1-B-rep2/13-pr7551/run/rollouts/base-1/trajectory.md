# trajectory base-1

final message:
DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG(col)`, and `list_distinct(col)` becomes `ARRAY_DISTINCT(ARRAY_COMPACT(col))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests), and ruff is clean.

**Changes (4 files):**
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` now parses to `ArrayDistinct(ArrayCompact(x))`. `ArrayDistinct` already carries Snowflake's NULL-keeping semantics, and the `ArrayCompact` supplies DuckDB's NULL-dropping.
- `sqlglot/generators/snowflake.py`: `exp.List` (what DuckDB's `list()` parses to) renders as `ARRAY_AGG`. Both engines keep NULLs in `list`/`ARRAY_AGG`, so no NULL filter is added.
- `sqlglot/generators/duckdb.py`: `arraydistinct_sql` drops a redundant `ArrayCompact` before emitting `LIST_DISTINCT`, so DuckDB→DuckDB output is unchanged (`list_distinct(c)` still round-trips).
- `tests/dialects/test_duckdb.py`: one `validate_all` covering both the DuckDB identity and the Snowflake output.

**Verified outputs:**
- `list(c)` → `ARRAY_AGG(c)`; `list(DISTINCT c)` → `ARRAY_AGG(DISTINCT c)`
- `list_distinct(c)` → `ARRAY_DISTINCT(ARRAY_COMPACT(c))`

**Not covered:**
- `list(c) FILTER(WHERE ...)` → Snowflake still crashes in `filter_sql`. Snowflake doesn't support aggregate `FILTER`, and the generic rewrite reads the aggregate's `this` argument, which `List` doesn't use. This predates my change, and I left it alone since it's a separate fix to the generic path.
- I haven't run the new Snowflake expectation against a live Snowflake, so semantics rest on the documented behavior of `ARRAY_AGG`, `ARRAY_DISTINCT`, and `ARRAY_COMPACT`.

I didn't commit anything.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"list_distinct\\|ListDistinct\\|\\\"LIST\\\"\\|ArrayAgg\\|ARRAY_AGG\\|ArrayDistinct\\|ARRAY_COMPACT\\|ArrayCompact\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -60", "description": "Check status and find list/array references"}
[tool_result] ok1 matches in 1 files:

sqlglot/dialects/snowflake.py:25:ARRAY_AGG_INCLUDES_NULLS = None
[tool_use Bash] {"command": "git status --short; /usr/bin/grep -n -i \"list_distinct\\|ListDistinct\\|ArrayAgg\\|ArrayDistinct\\|ArrayCompact\\|\\\"LIST\\\"\\|array_compact\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Search DuckDB, Snowflake and expressions for list/array classes"}
[tool_result] okgrep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls; ls sqlglot | head -50", "description": "List repo root and package contents"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  2.6K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  794B
sqlglot.png  7.2K
dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__.py  6.4K
__main__.py  2.1K
_typing.py  1.5K
_version.py  91B
diff.py  16.3K
errors.py  4.7K
generator.py  245.2K
helper.py  11.7K
jsonpath.py  7.8K
lineage.py  16.7K
parser.py  366.4K
planner.py  14.2K
py.typed  0B
schema.py  27.4K
serde.py  3.0K
time.py  18.0K
tokenizer_core.py  34.4K
tokens.py  22.8K
transforms.py  41.0K
trie.py  2.2K
[tool_use Bash] {"command": "/usr/bin/grep -rn -i \"list_distinct\\|ListDistinct\\|ArrayAgg\\|ArrayDistinct\\|ArrayCompact\\|array_compact\\|\\\"LIST\\\"\" sqlglot/ | head -80; echo ---; /usr/bin/grep -rn -i \"list_distinct\\|ARRAY_AGG\\|ArrayAgg\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head -40", "description": "Search sqlglot and tests for list/array aggregate refs"}
[tool_result] sqlglot/parsers/clickhouse.py:256:        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/parsers/singlestore.py:148:        "JSON_AGG": lambda self: exp.JSONArrayAgg(
sqlglot/parsers/sqlite.py:33:        "JSON_GROUP_ARRAY": exp.JSONArrayAgg.from_arg_list,
sqlglot/parsers/hive.py:62:        "COLLECT_LIST": lambda args: exp.ArrayAgg(this=seq_get(args, 0), nulls_excluded=True),
sqlglot/parsers/tsql.
…[8895 chars elided]…
WHEN ARRAY_LENGTH(['A', NULL, 'B', NULL]) <> LIST_COUNT(['A', NULL, 'B', NULL]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(['A', NULL, 'B', NULL], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(['A', NULL, 'B', NULL]) END",
tests/dialects/test_snowflake.py:3121:                "duckdb": "SELECT CASE WHEN ARRAY_LENGTH([1, 2, 2, 3, 1]) <> LIST_COUNT([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
[assistant] Let me check how the current code handles these DuckDB inputs.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor q in ['SELECT list(c) FROM t', 'SELECT list(DISTINCT c) FROM t', 'SELECT list_distinct(c) FROM t', 'SELECT list_distinct(c) FILTER(WHERE c IS NOT NULL) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:300])\n    print(' ->', e.sql('snowflake'))\n\" 2>&1 | head -40", "description": "Probe current DuckDB to Snowflake output for list functions"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT list(c) FROM t', 'SELECT list(DISTINCT c) FROM t', 'SELECT list_distinct(c) FROM t', 'SELECT list_distinct(c) FILTER(WHERE c IS NOT NULL) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:300])\n    print(' ->', e.sql('snowflake'))\n\" 2>&1 | head -40", "description": "Probe current DuckDB to Snowflake output for list functions"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/b
…[1851 chars elided]…
^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1827, in filter_sql
    agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
                                                  ^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'copy'
List(
  expressions=[
    Column(
      this=Identifier(this=c, quoted=False))])
 -> SELECT LIST(c) FROM t
List(
  expressions=[
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT list(c) FROM t', 'SELECT list(DISTINCT c) FROM t', 'SELECT list_distinct(c) FROM t', 'SELECT list_distinct(c) FILTER(WHERE c IS NOT NULL) FROM t', 'SELECT array_agg(c) FROM t', 'SELECT array_distinct(c) FROM t']:\n    e = sqlglot.pa
…[20 chars elided]…
kdb')\n    print(q, '| tree:', type(e.selects[0]).__name__, '|', e.selects[0].key)\n    try: print(' ->', e.sql('snowflake'))\n    except Exception as ex: print(' -> ERR', type(ex).__name__, ex)\n\" 2>&1 | head -40; /usr/bin/grep -n \"list_distinct\\|LIST_DISTINCT\\|\\\"LIST\\\"\" sqlglot/parsers/duckdb.py | head", "description": "Probe each DuckDB list function's parse tree and Snowflake output"}
[tool_result] SELECT list(c) FROM t | tree: List | list
 -> SELECT LIST(c) FROM t
SELECT list(DISTINCT c) FROM t | tree: List | list
 -> SELECT LIST(DISTINCT c) FROM t
SELECT list_distinct(c) FROM t | tree: Anonymous | anonymous
 -> SELECT LIST_DISTINCT(c) FROM t
SELECT list_distinct(c) FILTER(WHERE c IS NOT NULL) FROM t | tree: Filter | filter
 -> ERR AttributeError 'str' object has no attribute 'copy'
SELECT array_agg(c) FROM t | tree: ArrayAgg | arrayagg
 -> SELECT ARRAY_AGG(c) FROM t
SELECT array_distinct(c) FROM t | tree: ArrayDistinct | arraydistinct
 -> SELECT ARRAY_DISTINCT(c) FROM t
[assistant] The DuckDB `list()` parses to a generic `exp.List`, and `list_distinct()` stays `Anonymous`. Before choosing a mapping, I need to see the ArrayAgg null-filter logic and the DuckDB/Snowflake array generators.
[tool_use Bash] {"command": "sed -n 640,660p sqlglot/dialects/dialect.py; echo ----; sed -n 2990,3025p sqlglot/generators/duckdb.py; echo ----; sed -n 3295,3325p sqlglot/generators/duckdb.py; echo ----; /usr/bin/grep -n \"ARRAY_AGG_INCLUDES_NULLS\\|ARRAY_COMPACT\\|ArrayCompact\\|ArrayDistinct\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/parsers/duckdb.py sqlglot/dialects/snowflake.py sqlglot/dialects/duckdb.py; echo ----; /usr/bin/grep -n \"FUNCTIONS\\b\" sqlglot/parsers/duckdb.py | head -3; /usr/bin/grep -n \"\\\"LIST\\|\\\"ARRAY_AGG\\|ArrayCompact\" sqlglot/parser.py sqlglot/parsers/*.py | head", "description": "Inspect null-filter logic and array generators in duckdb/snowflake"}
[tool_result]     JSON_PATH_SINGLE_DOT_IS_WILDCARD = False
    """Whether a single DOT in a JSON path (e.g. $.) is treated as a valid wildcard key."""

    ON_CONDITION_EMPTY_BEFORE_ERROR = True
    """Whether "X ON EMPTY" should come before "X ON ERROR" (for dialects like T-SQL, MySQL, Oracle)."""

    ARRAY_AGG_INCLUDES_NULLS: bool | None = True
    """Whether ArrayAgg needs to filter NULL values."""

    ARRAY_FUNCS_PROPAGATES_NULLS = False
    """Whether Array update functions return NULL when the input a
…[3790 chars elided]…
py:136:        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
sqlglot/parsers/duckdb.py:137:        "LIST_CONCAT": parser.build_array_concat,
sqlglot/parsers/duckdb.py:138:        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:139:        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
sqlglot/parsers/duckdb.py:140:        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
sqlglot/parsers/duckdb.py:141:        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
[tool_use Bash] {"command": "sed -n 5330,5372p sqlglot/generators/duckdb.py sqlglot/generator.py | head -5; sed -n 5330,5375p sqlglot/generator.py; echo ----; sed -n 405,420p sqlglot/parsers/snowflake.py; echo ----; sed -n 100,110p sqlglot/parsers/duckdb.py; /usr/bin/grep -n \"ARRAY_AGG_INCLUDES_NULLS\" -r sqlglot | head; echo ----; sed -n 3,12p sqlglot/parser.py >/dev/null; sed -n 320,330p sqlglot/parser.py", "description": "Read arrayagg null-filter logic and snowflake array_distinct parser"}
[tool_result]     def generate(self, expression: exp.Expr, copy: bool = True) -> str:
        """
        Generates the SQL string corresponding to the given syntax tree.

    def _add_arrayagg_null_filter(
        self,
        array_agg_sql: str,
        array_agg_expr: exp.ArrayAgg,
        column_expr: exp.Expr,
    ) -> str:
        """
        Add NULL filter to ARRAY_AGG if dialect requires it.

        Args:
            array_agg_sql: The generated ARRAY_AGG SQL string
            array_agg_expr: The 
…[3824 chars elided]…
ild_coalesce),
        "ARRAY": lambda args, dialect: exp.Array(expressions=args),
        "ARRAYAGG": lambda args, dialect: exp.ArrayAgg(
            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
        ),
        "ARRAY_AGG": lambda args, dialect: exp.ArrayAgg(
            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
        ),
        "ARRAY_APPEND": build_array_append,
        "ARRAY_CAT": build_array_concat,
[assistant] The key constraints so far: DuckDB `list()` should emit `ARRAY_AGG` on Snowflake without a NULL filter (both keep NULLs), and `list_distinct` needs a `NULL`-dropping step. Let me check the `List` node definition, the array-compact helper, and the Snowflake array generation paths.
[tool_use Bash] {"command": "/usr/bin/grep -rn -A6 \"^class List(\" sqlglot/expressions/ ; /usr/bin/grep -n -A10 \"^class ArrayDistinct\\|^class ArrayCompact\" sqlglot/expressions/array.py; echo ----; sed -n 2176,2190p sqlglot/dialects/dialect.py; echo ----; sed -n 1498,1510p sqlglot/generators/duckdb.py; echo ----; /usr/bin/grep -n \"ArrayDistinct\\|ArrayCompact\\|ARRAY_DISTINCT\\|ARRAY_COMPACT\\|\\bexp.List\\b\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/typing/snowflake.py; echo ----; /usr/bin/grep -rn \"exp.List\\b\\|LIST(\" tests/dialects/test_duckdb.py | head -20", "description": "Read List/ArrayDistinct/ArrayCompact definitions and related generator refs"}
[tool_result] sqlglot/expressions/array.py:34:class List(Expression, Func):
sqlglot/expressions/array.py-35-    arg_types = {"expressions": False}
sqlglot/expressions/array.py-36-    is_var_len_args = True
sqlglot/expressions/array.py-37-
sqlglot/expressions/array.py-38-
sqlglot/expressions/array.py-39-class ToArray(Expression, Func):
sqlglot/expressions/array.py-40-    pass
50:class ArrayCompact(Expression, Func):
51-    pass
52-
53-
54-class ArrayConcat(Expression, Func):
55-    _sql_names = ["ARRAY_CONCAT"
…[1327 chars elided]…
(
            exp.ArrayCompact(this=exp.Array(expressions=e.expressions))
        ),
        exp.ArrayConcat: array_concat_sql("LIST_CONCAT"),
        exp.ArrayContains: _array_contains_sql,
        exp.ArrayOverlaps: _array_overlaps_sql,
        exp.ArrayFilter: rename_func("LIST_FILTER"),
----
sqlglot/typing/snowflake.py:266:            exp.ArrayCompact,
----
tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
[assistant] I have what I need. Plan:

- **`list(c)`**: DuckDB parses it to the generic `exp.List`, and both DuckDB and Snowflake `ARRAY_AGG` keep NULLs. So I'll map `List` to `ARRAY_AGG` in the Snowflake generator with no NULL filter.
- **`list_distinct(c)`**: parse it as `ArrayDistinct(ArrayCompact(c))`, since ArrayDistinct already uses Snowflake's NULL-keeping semantics. The `ArrayCompact` drops the NULLs. In the DuckDB generator, I'll unwrap that case back to `LIST_DISTINCT(c)` so DuckDB→DuckDB output stays the same.

Let me look at the exact spots to edit.
[tool_use Bash] {"command": "sed -n 600,615p sqlglot/generators/snowflake.py; echo ----; sed -n 3311,3335p sqlglot/generators/duckdb.py; echo ----; sed -n 102,106p sqlglot/parsers/duckdb.py; /usr/bin/grep -n \"\\\"LIST_\" sqlglot/parsers/duckdb.py | head -3", "description": "Read the Snowflake TRANSFORMS block and DuckDB arraydistinct generator"}
[tool_result]         exp.UnixToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, e.args.get("scale")),
        exp.Uuid: rename_func("UUID_STRING"),
        exp.VarMap: lambda self, e: var_map_sql(self, e, "OBJECT_CONSTRUCT"),
        exp.Booland: rename_func("BOOLAND"),
        exp.Boolor: rename_func("BOOLOR"),
        exp.WeekOfYear: rename_func("WEEKISO"),
        exp.YearOfWeek: rename_func("YEAROFWEEK"),
        exp.YearOfWeekIso: rename_func("YEAROFWEEKISO"),
        exp.Xor: rename_func("BOOLXO
…[1318 chars elided]…
n.expressions[0],
----
    FUNCTIONS = {
        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
        "ARRAY_PREPEND": _build_array_prepend,
        "ARRAY_REVERSE_SORT": _build_sort_array_desc,
136:        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
137:        "LIST_CONCAT": parser.build_array_concat,
138:        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
[assistant] Making the three edits now: the Snowflake `List` transform, the DuckDB `LIST_DISTINCT` parser mapping, and the DuckDB generator unwrap that keeps DuckDB→DuckDB output unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.ArrayConcatAgg:", "new_string": "        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.List: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayConcatAgg:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,", "new_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(\n            this=exp.ArrayCompact(this=seq_get(args, 0)),\n        ),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py", "old_string": "    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        func = self.func(\"LIST_DISTINCT\", arr)\n\n        if expression.args.get(\"check_null\"):", "ne
…[19 chars elided]…
 arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        # LIST_DISTINCT already drops NULLs, so ARRAY_COMPACT(x) is redundant here\n        if isinstance(arr, exp.ArrayCompact) and not expression.args.get(\"check_null\"):\n            arr = arr.this\n        func = self.func(\"LIST_DISTINCT\", arr)\n\n        if expression.args.get(\"check_null\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\ncases = [\n ('SELECT list(c) FROM t', 'duckdb'),\n ('SELECT list(DISTINCT c) FROM t', 'duckdb'),\n ('SELECT list(c) FILTER(WHERE c > 1) FROM t', 'duckdb'),\n ('SELECT list_distinct(c) FROM t', 'duckdb'),\n ('SELECT list_distinct(LIST(c)) FROM t', 'du
…[26 chars elided]…
stinct([1, NULL, 1]) AS x', 'duckdb'),\n ('SELECT ARRAY_DISTINCT(ARRAY_COMPACT(c)) FROM t', 'snowflake'),\n ('SELECT ARRAY_DISTINCT(c) FROM t', 'snowflake'),\n]\nfor q, r in cases:\n    e = sqlglot.parse_one(q, read=r)\n    print(q, '\\n   snowflake:', e.sql('snowflake'), '\\n   duckdb:   ', e.sql('duckdb'))\n\" 2>&1 | head -60", "description": "Verify new DuckDB to Snowflake and identity output"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 16, in <module>
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/
…[1917 chars elided]…
k/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1827, in filter_sql
    agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
    ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'replace'
SELECT list(c) FROM t 
   snowflake: SELECT ARRAY_AGG(c) FROM t 
   duckdb:    SELECT LIST(c) FROM t
SELECT list(DISTINCT c) FROM t 
   snowflake: SELECT ARRAY_AGG(DISTINCT c) FROM t 
   duckdb:    SELECT LIST(DISTINCT c) FROM t
[assistant] The `FILTER(WHERE ...)` case crashes in `filter_sql`, which is because `List` stores its argument in `expressions`, not `this`. Let me look at that code.
[tool_use Bash] {"command": "sed -n 1800,1840p sqlglot/generator.py", "description": "Read filter_sql aggregate handling"}
[tool_result]     def fetch_sql(self, expression: exp.Fetch) -> str:
        direction = expression.args.get("direction")
        direction = f" {direction}" if direction else ""
        count = self.sql(expression, "count")
        count = f" {count}" if count else ""
        limit_options = self.sql(expression, "limit_options")
        limit_options = f"{limit_options}" if limit_options else " ROWS ONLY"
        return f"{self.seg('FETCH')}{direction}{count}{limit_options}"

    def limitoptions_sql(self, e
…[818 chars elided]…
    def hint_sql(self, expression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"

    def indexparameters_sql(self, expression: exp.IndexParameters) -> str:
        using = self.sql(expression, "using")
        using = f" USING {using}" if using else ""
        columns = self.expressions(expression, key="columns", flat=True)
[assistant] The generic `filter_sql` assumes the aggregate's argument is in `this`, and `List` doesn't use that slot. This crash predates my change: the same `list(c) FILTER(...)` input already failed on Snowflake before. Let me check whether Snowflake overrides `filter_sql` and what the existing DuckDB test at line 690 pins down, before I decide how far to go.
[tool_use Bash] {"command": "/usr/bin/grep -n \"def filter_sql\\|AGGREGATE_FILTER_SUPPORTED\" sqlglot/generators/snowflake.py sqlglot/generator.py | head; sed -n 684,694p tests/dialects/test_duckdb.py", "description": "Check snowflake filter override and duckdb LIST test"}
[tool_result] sqlglot/generators/snowflake.py:383:    AGGREGATE_FILTER_SUPPORTED = False
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1818:    def filter_sql(self, expression: exp.Filter) -> str:
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
        self.validate_all("0x1010", write={"": "0 AS x1010"})
        self.validate_identity("x ~ y", "REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
        self.validate_all("SELECT * FROM 'x.y'", write={"duckdb": 'SELECT * FROM "x.y"'})
        self.validate_all(
            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
            read={"spark": "SELECT COLLECT_SET(sample_col) FROM sample_table"},
        )
        self.validate_all(
            "SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))",
[assistant] Snowflake disables aggregate `FILTER` and falls back to the generic rewrite, which assumes `this`. Fixing that generic path is outside this request, and the crash predates my change, so I'll leave it and flag it. Let me verify the remaining cases and run the test suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\ncases = [\n ('SELECT list(c) FROM t', 'duckdb'),\n ('SELECT list(DISTINCT c) FROM t', 'duckdb'),\n ('SELECT list_distinct(c) FROM t', 'duckdb'),\n ('SELECT list_distinct(list(c)) FROM t', 'duckdb'),\n ('SELECT list_distinct([1, NULL, 1]) AS x', 'duck
…[123 chars elided]…
,\n]\nfor q, r in cases:\n    e = sqlglot.parse_one(q, read=r)\n    print(q, '\\n   snowflake:', e.sql('snowflake'), '\\n   duckdb:   ', e.sql('duckdb'))\n\"; echo ---- ; timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -30", "description": "Verify outputs and run full test suite", "timeout": 900000}
[tool_result] SELECT list(c) FROM t 
   snowflake: SELECT ARRAY_AGG(c) FROM t 
   duckdb:    SELECT LIST(c) FROM t
SELECT list(DISTINCT c) FROM t 
   snowflake: SELECT ARRAY_AGG(DISTINCT c) FROM t 
   duckdb:    SELECT LIST(DISTINCT c) FROM t
SELECT list_distinct(c) FROM t 
   snowflake: SELECT ARRAY_DISTINCT(ARRAY_COMPACT(c)) FROM t 
   duckdb:    SELECT LIST_DISTINCT(c) FROM t
SELECT list_distinct(list(c)) FROM t 
   snowflake: SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY_AGG(c))) FROM t 
   duckdb:    SELECT 
…[414 chars elided]…
c, _u -> NOT _u IS NULL)) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(LIST_FILTER(c, _u -> NOT _u IS NULL), _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(LIST_FILTER(c, _u -> NOT _u IS NULL)) END FROM t
SELECT ARRAY_DISTINCT(c) FROM t 
   snowflake: SELECT ARRAY_DISTINCT(c) FROM t 
   duckdb:    SELECT CASE WHEN ARRAY_LENGTH(c) <> LIST_COUNT(c) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(c, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(c) END FROM t
----
(eval):16: command not found: timeout
[assistant] Outputs look right. The `ARRAY_DISTINCT(ARRAY_COMPACT(c))` → DuckDB result is the pre-existing nested form (the unwrap is skipped when `check_null` is set), so that path is unchanged. Running the project's test command now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run project test suite with pytest", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
...........................................................................................................................
…[323 chars elided]…
................................................................................... [ 77%]
............................................. [ 81%]
.... [ 81%]
...................................................................... [ 88%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 48.63s
[assistant] All 1092 tests pass. Next I'll add regression tests in the DuckDB dialect test file, next to the existing `LIST(...)` case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample_table\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM(", "new_string": "            read={\"spark\": 
…[39 chars elided]…
ample_table\"},\n        )\n        self.validate_all(\n            \"SELECT LIST(c), LIST_DISTINCT(c) FROM t\",\n            write={\n                \"duckdb\": \"SELECT LIST(c), LIST_DISTINCT(c) FROM t\",\n                \"snowflake\": \"SELECT ARRAY_AGG(c), ARRAY_DISTINCT(ARRAY_COMPACT(c)) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-140940-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -1; git status --short", "description": "Run dialect tests and full suite, check changed files", "timeout": 900000}
[tool_result] ............................................................................ [ 54%]
...............................................................      [100%]
139 passed, 2160 subtests passed in 0.57s
1092 passed, 17859 subtests passed in 51.73s
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] Tests pass. Let me run the linter on the changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Lint and format-check changed files with ruff"}
[tool_result] All checks passed!
4 files already formatted
[assistant] DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG(col)`, and `list_distinct(col)` becomes `ARRAY_DISTINCT(ARRAY_COMPACT(col))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests), and ruff is clean.

**Changes (4 files):**
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` now parses to `ArrayDistinct(ArrayCompact(x))`. `ArrayDistinct` already carries Snowflake's NULL-keeping semantics, and the `ArrayCompact` supplies DuckDB's NULL-dropping.
- `sqlglot/generators/snowflake.py`: `exp.List` (what DuckDB's `list()` parses to) renders as `ARRAY_AGG`. Both engines keep NU
…[438 chars elided]…
→ `ARRAY_AGG(DISTINCT c)`
- `list_distinct(c)` → `ARRAY_DISTINCT(ARRAY_COMPACT(c))`

**Not covered:**
- `list(c) FILTER(WHERE ...)` → Snowflake still crashes in `filter_sql`. Snowflake doesn't support aggregate `FILTER`, and the generic rewrite reads the aggregate's `this` argument, which `List` doesn't use. This predates my change, and I left it alone since it's a separate fix to the generic path.
- I haven't run the new Snowflake expectation against a live Snowflake, so semantics rest on the documented behavior of `ARRAY_AGG`, `ARRAY_DISTINCT`, and `ARRAY_COMPACT`.

I didn't commit anything.
