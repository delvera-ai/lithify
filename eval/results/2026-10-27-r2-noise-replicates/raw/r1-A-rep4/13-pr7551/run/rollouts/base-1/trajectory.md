# trajectory base-1

final message:
DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG`, and DuckDB `list_distinct(col)` to `ARRAY_DISTINCT(ARRAY_COMPACT(col))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests), and ruff check and format are clean. I have not committed anything.

```
SELECT LIST(x) FROM t                  -> SELECT ARRAY_AGG(x) FROM t
SELECT LIST_DISTINCT(x) FROM t         -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
SELECT LIST(DISTINCT x) FROM t         -> SELECT ARRAY_AGG(DISTINCT x) FROM t
SELECT LIST(x ORDER BY y) FROM t       -> SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t
SELECT LIST(x) FILTER(WHERE c) FROM t  -> SELECT ARRAY_AGG(IFF(c, x, NULL)) FROM t
```

**Changes**
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` now parses to `exp.ArrayDistinct`. Before, it was an unrecognised function and passed through unchanged. DuckDB-to-DuckDB output is unchanged.
- `sqlglot/generators/snowflake.py`: added `list_sql` (emits `ARRAY_AGG`) and `arraydistinct_sql`. The latter wraps the input in `ARRAY_COMPACT` unless `check_null` is set, which matches how the DuckDB generator already reads that flag.
- `sqlglot/generator.py`: in the base `filter_sql`, the aggregate argument now falls back to `expressions[0]` when `this` is empty. Before, `list(x) FILTER (...)` crashed with an `AttributeError` for any target that doesn't support aggregate FILTER natively.
- `tests/dialects/test_duckdb.py`: four new assertions covering the cases above, added next to the existing `LIST` test. No existing tests were changed.

**Decisions**
- I did not change DuckDB's parse of `list` to `ArrayAgg`. That would have changed DuckDB's own output and broken the existing identity test for `LIST(DISTINCT …) FILTER(…)`. The conversion happens at Snowflake generation instead.

**Things to check**
- **Behaviour change for other sources:** `ArrayDistinct` without `check_null` now drops NULLs when generating Snowflake. The only other source that produces it is ClickHouse's `arrayDistinct`. I haven't verified whether ClickHouse keeps NULLs, so ClickHouse-to-Snowflake output may now differ.
- **Pre-existing, not fixed:** `COUNT(DISTINCT x) FILTER (WHERE …)` already generates invalid Snowflake (`IFF(cond, DISTINCT x, NULL)`) on the unmodified code. `list(DISTINCT x) FILTER (…)` now hits the same path, so it produces that invalid shape instead of crashing.
- **Not run against a live Snowflake:** the expected strings are from sqlglot's output, not from executing them in Snowflake, which isn't available here.

## events
[tool_use Bash] {"command": "grep -n -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|\\\"LIST\\\"\\|ArrayAgg\\|ARRAY_DISTINCT\\|ArrayDistinct\\|list_agg\\|ListAgg\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Search duckdb/snowflake dialects for list-related expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "pwd && git status --short | head && ls && grep -rn -i \"list_distinct\\|ArrayUniqueAgg\\|ARRAY_UNIQUE_AGG\\|\\\"LIST\\\"\\|ArrayAgg\\|ARRAY_DISTINCT\\|ArrayDistinct\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py 2>&1 | head -80", "description": "Check repo location and search for list expressions"}
[tool_result] ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1
AGENTS.md
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
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rln \"ArrayUniqueAgg\\|ARRAY_UNIQUE_AGG\" sqlglot | head; grep -n -i \"list_distinct\\|ArrayUniqueAgg\\|ARRAY_UNIQUE_AGG\\|\\\"LIST\\\"\\|ArrayAgg\\|ARRAY_DISTINCT\\|ArrayDistinct\\|ARRAY_AGG\\|\\\"LIST\\\"\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py", "description": "Inspect sqlglot package and grep dialects for list functions"}
[tool_result] __init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
sqlglot/parsers/doris.py
sqlglot/parsers/hive.py
sqlglot/parsers/presto.py
sqlglot/typing/snowflake.py
sqlglot/expressions/aggregate.py
sqlglot/generators/trino.py
sqlglot/generators/doris.py
sqlglot/generators/duckdb.py
sqlglot/generators/hive.py
sqlglot/generators/presto.py
sqlglot/dialects/snowflake.py:25:    ARRAY_AGG_INCLUDES_NULLS = None
[tool_use Bash] {"command": "grep -n -i \"ArrayUniqueAgg\\|ArrayDistinct\\|ARRAY_UNIQUE_AGG\\|ARRAY_DISTINCT\\|ListDistinct\\|list_distinct\\|ArrayAgg\\b\" sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py sqlglot/expressions/*.py sqlglot/typing/snowflake.py sqlglot/parsers/*.py 2>/dev/null | head -80; ls sqlglot/generators sqlglot/parsers | head -100", "description": "Grep duckdb/snowflake generators, parsers and expressions"}
[tool_result] sqlglot/generators/snowflake.py:189:                    exp.select(exp.ArrayAgg(this=exp.Star())).from_(unnest).subquery()
sqlglot/generators/snowflake.py:611:        exp.ArrayConcatAgg: lambda self, e: self.func("ARRAY_FLATTEN", exp.ArrayAgg(this=e.this)),
sqlglot/generators/snowflake.py:673:    RESPECT_IGNORE_NULLS_UNSUPPORTED_EXPRESSIONS = (exp.ArrayAgg,)
sqlglot/generators/snowflake.py:1035:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
sqlglot/generators/snowflake.py:1069:    
…[3167 chars elided]…
.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py

sqlglot/parsers:
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
[assistant] Let me look at the DuckDB parser/generator handling of `LIST` and `LIST_DISTINCT`, and the Snowflake side.
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/expressions/aggregate.py; sed -n 130,160p sqlglot/expressions/array.py; sed -n 3295,3325p sqlglot/generators/duckdb.py; grep -n \"\\\"LIST\\\"\\|LIST_DISTINCT\\|\\\"ARRAY_AGG\\|ArrayAgg\\|ARRAY_UNIQUE\\|ArrayUniqueAgg\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/generators/duckdb.py | head -30; sed -n 405,425p sqlglot/parsers/snowflake.py", "description": "Read relevant expression, DuckDB and Snowflake parser code"}
[tool_result] class ArgMax(Expression, AggFunc):
    arg_types = {"this": True, "expression": True, "count": False}
    _sql_names = ["ARG_MAX", "ARGMAX", "MAX_BY"]


class ArgMin(Expression, AggFunc):
    arg_types = {"this": True, "expression": True, "count": False}
    _sql_names = ["ARG_MIN", "ARGMIN", "MIN_BY"]


class ArrayAgg(Expression, AggFunc):
    arg_types = {"this": True, "nulls_excluded": False}


class ArrayConcatAgg(Expression, AggFunc):
    pass


class ArrayUnionAgg(Expression, AggFunc):
   
…[3964 chars elided]…
alse,
            check_null=True,
        ),
        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
            this=seq_get(args, 0),
            check_null=True,
        ),
        "ARRAY_GENERATE_RANGE": lambda args: exp.GenerateSeries(
            # Snowflake has exclusive end semantics
            start=seq_get(args, 0),
            end=seq_get(args, 1),
            step=seq_get(args, 2),
            is_end_exclusive=True,
        ),
        "ARRAY_EXCEPT": lambda args: exp.ArrayExcept(
[assistant] Now let me check what the current transpilation actually produces, and how DuckDB parses these.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SELECT list(x) FROM t', 'SELECT list_distinct(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT list(x ORDER BY y) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:300])\n    print(e.sql('snowflake'))\n\" 2>&1 | head -60; grep -n \"\\\"LIST\\\"\\|LIST_DISTINCT\\|ArrayUniqueAgg\\|\\\"LIST_\\|ListDistinct\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head", "description": "Test current DuckDB to Snowflake transpilation of list functions"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parsers/duckdb.py:136:        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
sqlglot/parsers/duckdb.py:137:        "LIST_CONCAT": parser.build_array_concat,
sqlglot/parsers/duckdb.py:138:        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:139:        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
sqlglot/parsers/duckdb.py:140:        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
sqlglot/parsers/duckdb.py:141:        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
sqlglot/parsers/duckdb.py:142:        "LIST_HAS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:143:        "LIST_HAS_ANY": exp.ArrayOverlaps.from_arg_list,
sqlglot/parsers/duckdb.py:144:        "LIST_MAX": exp.ArrayMax.from_arg_list,
sqlglot/parsers/duckdb.py:145:        "LIST_MIN": exp.ArrayMin.from_arg_list,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT list(x) FROM t', 'SELECT list_distinct(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT list(x ORDER BY y) FROM t', 'SELECT list(x) FILTER (WHERE x IS NOT NULL) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:400])\n    print('  ->', e.sql('snowflake'))\n\" 2>&1 | head -80; sed -n 120,135p sqlglot/parsers/duckdb.py; grep -n \"list_distinct\\|LIST_DISTINCT\" -r sqlglot/parsers sqlglot/dialects sqlglot/generators | head", "description": "Run transpilation test using repo sources"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/b
…[4209 chars elided]…
b.py:1968:            FROM (SELECT LIST_SORT(LIST_DISTINCT(LIST(:arg) FILTER(NOT :arg IS NULL))) AS l)
sqlglot/generators/duckdb.py:2083:    # Set semantics for ARRAY_EXCEPT. Deduplicates arr1 via LIST_DISTINCT, then
sqlglot/generators/duckdb.py:2092:                LIST_DISTINCT(:arr1),
sqlglot/generators/duckdb.py:3313:        func = self.func("LIST_DISTINCT", arr)
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
[assistant] Key findings so far: DuckDB's `list(x)` parses to `exp.List`, which passes through to Snowflake unchanged, and `list_distinct` parses to an `Anonymous` call. Let me look at the `exp.List` definition, the DuckDB ArrayDistinct generator in full, and Snowflake's handling of ArrayDistinct/ArrayAgg/ArrayCompact.
[tool_use Bash] {"command": "grep -rn \"class List(\\|class ArrayCompact\\|class ArrayAgg\\|ARRAY_AGG_INCLUDES_NULLS\\|ArrayDistinct\" sqlglot --include=*.py | grep -v \"^sqlglot/generators/duckdb.py:31\" ; sed -n 3325,3335p sqlglot/generators/duckdb.py; sed -n 1030,1075p sqlglot/generators/snowflake.py; grep -n \"ARRAY_AGG_INCLUDES_NULLS\" -B3 -A3 sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py | head -30", "description": "Locate List, ArrayCompact, ArrayDistinct, ArrayAgg definitions and handlers"}
[tool_result] (eval):1: no matches found: --include=*.py
                    false=func,
                )
            )

        return func

    def arrayintersect_sql(self, expression: exp.ArrayIntersect) -> str:
        if expression.args.get("is_multiset") and len(expression.expressions) == 2:
            return self._array_bag_sql(
                self.ARRAY_INTERSECTION_CONDITION,
                expression.expressions[0],

            return f"{this_name}{self.sep()}{copy_grants}{this_schema}"

      
…[1855 chars elided]…
alect.py-644-    ON_CONDITION_EMPTY_BEFORE_ERROR = True
sqlglot/dialects/dialect.py-645-    """Whether "X ON EMPTY" should come before "X ON ERROR" (for dialects like T-SQL, MySQL, Oracle)."""
sqlglot/dialects/dialect.py-646-
sqlglot/dialects/dialect.py:647:    ARRAY_AGG_INCLUDES_NULLS: bool | None = True
sqlglot/dialects/dialect.py-648-    """Whether ArrayAgg needs to filter NULL values."""
sqlglot/dialects/dialect.py-649-
sqlglot/dialects/dialect.py-650-    ARRAY_FUNCS_PROPAGATES_NULLS = False
[tool_use Bash] {"command": "grep -rn \"class List(\\|class ArrayCompact\\|class ArrayDistinct\\|ArrayDistinct\\b\" sqlglot | head -20; sed -n 3290,3330p sqlglot/generators/duckdb.py | head -5; grep -n \"ARRAY_DISTINCT\\|ArrayDistinct\\|arraydistinct\\|ArrayCompact\\|arraycompact\" sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py; grep -n \"ARRAY_AGG_INCLUDES_NULLS\" -r sqlglot | head", "description": "Find List, ArrayCompact, ArrayDistinct definitions and snowflake handlers"}
[tool_result] sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
sqlglot/typing/hive.py:53:            exp.ArrayDistinct,
sqlglot/expressions/array.py:34:class List(Expression, Func):
sqlglot/expressions/array.py:50:class ArrayCompact(Expression, Func):
sqlglot/expressions/array.py:138:class ArrayDistinct(Expression, Func):
sqlglot/generators/clickhouse.py:279:        exp.ArrayDi
…[890 chars elided]…
ct.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/parser.py:327:            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/generator.py:5350:            self.dialect.ARRAY_AGG_INCLUDES_NULLS and array_agg_expr.args.get("nulls_excluded")
sqlglot/dialects/dialect.py:647:    ARRAY_AGG_INCLUDES_NULLS: bool | None = True
sqlglot/dialects/hive.py:24:    ARRAY_AGG_INCLUDES_NULLS = None
sqlglot/dialects/snowflake.py:25:    ARRAY_AGG_INCLUDES_NULLS = None
[tool_use Bash] {"command": "sed -n 30,60p sqlglot/expressions/array.py; sed -n 136,142p sqlglot/expressions/array.py; sed -n 1495,1510p sqlglot/generators/duckdb.py; grep -n \"\\\"LIST\\\"\\|exp.List\\b\\|List:\" sqlglot/parsers/*.py sqlglot/generators/*.py sqlglot/dialects/*.py | head -20; grep -n \"ArrayAgg\\|ArrayCompact\\|ArrayUniqueAgg\" sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/typing/snowflake.py | head; sed -n 5340,5360p sqlglot/generator.py", "description": "Read List, ArrayCompact, ArrayDistinct classes and related handlers"}
[tool_result]     arg_types = {"expressions": False}
    is_var_len_args = True


class List(Expression, Func):
    arg_types = {"expressions": False}
    is_var_len_args = True


class ToArray(Expression, Func):
    pass


# Array manipulation


class ArrayAppend(Expression, Func):
    arg_types = {"this": True, "expression": True, "null_propagation": False}


class ArrayCompact(Expression, Func):
    pass


class ArrayConcat(Expression, Func):
    _sql_names = ["ARRAY_CONCAT", "ARRAY_CAT"]
    arg_types = {
…[2932 chars elided]…
")
        ):
            return array_agg_sql

        parent = array_agg_expr.parent
        if isinstance(parent, exp.Filter):
            parent_cond = parent.expression.this
            parent_cond.replace(parent_cond.and_(column_expr.is_(exp.null()).not_()))
        elif column_expr.find(exp.Column):
            # Do not add the filter if the input is not a column (e.g. literal, struct etc)
            # DISTINCT is already present in the agg function, do not propagate it to FILTER as well
[assistant] The mapping picture is clear now. Before choosing where to hook the change, I'll check existing test expectations for these functions and how DuckDB's `ArrayCompact` and `ArrayAgg` generate.
[tool_use Bash] {"command": "grep -rn -i \"list_distinct\\|ARRAY_DISTINCT\\|arrayDistinct\\|ArrayDistinct\" tests | head -40; echo ---; grep -rn -i \"LIST(\\|list(\" tests/dialects/test_duckdb.py | head -30; echo ---; grep -n \"def array_compact_sql\" -A12 sqlglot/generators/duckdb.py; sed -n 2998,3030p sqlglot/generators/duckdb.py", "description": "Check tests and DuckDB ArrayCompact/ArrayAgg generation"}
[tool_result] tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNHEX('08000000000000000000' || h) END FROM (SELECT l, COALESCE(LIST_REDUCE(LIST_TRANSFORM(l, __x -> PRINTF('%02X%02X', CAST(__x AS INT) & 255, (CAST(__x AS INT) >> 8) & 255)),
…[4159 chars elided]…
   return self._add_arrayagg_null_filter(array_agg_sql, func, original_this)

        # For other functions (like PERCENTILES), use existing logic
        expression_sql = self.sql(expression, "expression")

        if isinstance(func, exp.PERCENTILES):
            # Make the order key the first arg and slide the fraction to the right
            # https://duckdb.org/docs/sql/aggregates#ordered-set-aggregate-functions
            order_col = expression.find(exp.Ordered)
            if order_col:
[assistant] Two things stand out. The existing DuckDB test at `tests/dialects/test_duckdb.py:690` requires `LIST(...)` to round-trip in DuckDB, so the DuckDB-side parse can't simply become `ArrayAgg`. Also, `list(x) FILTER (WHERE ...)` crashes the Snowflake generator today because `exp.List` has no `this` arg. Let me read `filter_sql` and the DuckDB ArrayAgg/Filter path to decide where the mapping belongs.
[tool_use Bash] {"command": "sed -n 1795,1835p sqlglot/generator.py; sed -n 300,330p tests/dialects/test_dialect.py; sed -n 3100,3125p tests/dialects/test_snowflake.py", "description": "Read filter_sql and related existing test expectations"}
[tool_result]                 sqls.append(self.sql(node))

        this = self.sep().join(sqls)
        this = self.query_modifiers(expression, this)
        return self.prepend_ctes(expression, this)

    def fetch_sql(self, expression: exp.Fetch) -> str:
        direction = expression.args.get("direction")
        direction = f" {direction}" if direction else ""
        count = self.sql(expression, "count")
        count = f" {count}" if count else ""
        limit_options = self.sql(expression, "limit_opti
…[3317 chars elided]…
NULL]) END",
            },
        )

        self.validate_all(
            "SELECT ARRAY_DISTINCT([1, 2, 2, 3, 1])",
            write={
                "snowflake": "SELECT ARRAY_DISTINCT([1, 2, 2, 3, 1])",
                "duckdb": "SELECT CASE WHEN ARRAY_LENGTH([1, 2, 2, 3, 1]) <> LIST_COUNT([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
            },
        )

        self.validate_all(
[assistant] I have enough context to settle the design. Here's the plan, following the existing conventions in the codebase:

- **`list(x)`**: DuckDB parses it to `exp.List` with `expressions` (no `this`). I'll generate `ARRAY_AGG` from it in the Snowflake generator. Changing the DuckDB parse to `ArrayAgg` would break the DuckDB identity test at `test_duckdb.py:690`.
- **`list_distinct(x)`**: DuckDB parses it as `Anonymous` today. I'll map it to `exp.ArrayDistinct` in the DuckDB parser. The DuckDB generator already treats `check_null=False` as NULL-dropping (`LIST_DISTINCT`), so DuckDB round-trips stay intact.
- **Snowflake generator**: for `ArrayDistinct` without `check_null`, wrap the input in `ARRAY_COMPACT` so NULLs are dropped, matching the existing DuckDB-side convention.

Let me confirm the imports and the surrounding Snowflake code before editing.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/generators/snowflake.py | grep -n \"import\"; grep -n \"seq_get\" sqlglot/generators/snowflake.py | head -3; grep -n \"def list_sql\\|def arraydistinct\\|def arrayagg_sql\" sqlglot/generators/*.py | head; sed -n 136,142p sqlglot/parsers/duckdb.py; grep -n '\"LIST_DISTANCE\"' sqlglot/parsers/duckdb.py", "description": "Check imports and existing method names in Snowflake generator"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
28:from sqlglot.helper import find_new_name, flatten, seq_get
45:        this=seq_get(args, 2),
46:        expression=seq_get(args, 1),
sqlglot/generators/materialize.py:47:    def list_sql(self, expression: exp.List) -> str:
sqlglot/generators/duckdb.py:3311:    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
sqlglot/generators/sn
…[131 chars elided]…
lf, expression: exp.ArrayAgg) -> str:
        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
        "LIST_CONCAT": parser.build_array_concat,
        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
        "LIST_HAS": exp.ArrayContains.from_arg_list,
140:        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
[assistant] Now the edits. First the DuckDB parser mapping for `LIST_DISTINCT`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,", "new_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": exp.ArrayDistinct.from_arg_list,\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this", "new_string": "    def list_sql(self, expression: exp.List) -> str:\n        return self.sql(exp.ArrayAgg(this=seq_get(expression.expressions, 0)))\n\n    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        if not expression.args.get(\"check_null\"):\n            arr = exp.ArrayCompact(this=arr)\n        return self.func(\"ARRAY_DISTINCT\", arr)\n\n    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nqs = ['SELECT list(x) FROM t', 'SELECT list_distinct(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT list(x ORDER BY y) FROM t', 'SELECT list(x) FILTER (WHERE x IS NOT NULL) FROM t', 'SELECT list_distinct(list(x)) FROM t']\nfor q in qs:\n  
…[135 chars elided]…
ame__, ex)\nprint(sqlglot.transpile('SELECT LIST_DISTINCT(x), LIST(DISTINCT x) FILTER(WHERE NOT x IS NULL)', read='duckdb', write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x)', read='snowflake', write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x)', read='snowflake', write='duckdb'))\n\" 2>&1", "description": "Verify new DuckDB to Snowflake transpilation output"}
[tool_result] SELECT ARRAY_AGG(x) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
SELECT ARRAY_AGG(DISTINCT x) FROM t
SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t
ERR AttributeError 'NoneType' object has no attribute 'replace'
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY_AGG(x))) FROM t
['SELECT LIST_DISTINCT(x), LIST(DISTINCT x) FILTER(WHERE NOT x IS NULL)']
['SELECT ARRAY_DISTINCT(x)']
['SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END']
[assistant] The core mapping works. `list(x) FILTER (WHERE ...)` still crashes, and that's a pre-existing crash in the base `filter_sql` path: it reads `agg.this`, which `exp.List` doesn't have. Since FILTER on `list` is a common form (the existing DuckDB test at line 690 uses it), I'll fix it at the base level, limited to the crash path.
[tool_use Bash] {"command": "grep -n \"seq_get\" sqlglot/generator.py | head -3", "description": "Check seq_get import in base generator"}
[tool_result] 12:from sqlglot.helper import csv, name_sequence, seq_get
3453:            "CONCAT_WS", seq_get(expression.expressions, 0), *self.convert_concat_args(expression)
4952:        if not seq_get(to.expressions, 0) and to.this in self.PARAMETERIZABLE_TEXT_TYPES:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", "old_string": "        agg = expression.this\n        agg_arg = agg.this\n        cond = expression.expression.this", "new_string": "        agg = expression.this\n        agg_arg = agg.this or seq_get(agg.expressions, 0)\n        cond = expression.expression.this"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['SELECT list(x) FILTER (WHERE x IS NOT NULL) FROM t', 'SELECT list(DISTINCT x) FILTER (WHERE x > 1) FROM t']:\n    print(sqlglot.transpile(q, read='duckdb', write='snowflake')[0])\n\" 2>&1; echo ---; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Verify FILTER output and run full test suite"}
[tool_result] SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(x > 1, DISTINCT x, NULL)) FROM t
---
................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
................................................................................ [ 31%]
............
…[434 chars elided]…
................................................................................... [ 77%]
............................................. [ 81%]
.... [ 81%]
...................................................................... [ 88%]
............. [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1092 passed, 17857 subtests passed in 50.80s
[assistant] The FILTER case now generates SQL without crashing. The `DISTINCT` inside `IFF(...)` is wrong, though: Snowflake won't accept it. I need to check whether the existing `ArrayAgg` path already does this, which would make it pre-existing rather than something I introduced.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nprint(sqlglot.transpile('SELECT ARRAY_AGG(DISTINCT x) FILTER (WHERE x > 1) FROM t', read='duckdb', write='snowflake')[0])\nprint(sqlglot.transpile('SELECT COUNT(DISTINCT x) FILTER (WHERE x > 1) FROM t', read='duckdb', write='snowflake')[0])\n\" 2>&1; git stash list | head -2 >/dev/null; git diff --stat", "description": "Check pre-existing DISTINCT-inside-FILTER behavior for ArrayAgg"}
[tool_result] SELECT ARRAY_AGG(IFF(x > 1, DISTINCT x, NULL)) FROM t
SELECT COUNT(IFF(x > 1, DISTINCT x, NULL)) FROM t
 sqlglot/generator.py            | 2 +-
 sqlglot/generators/snowflake.py | 9 +++++++++
 sqlglot/parsers/duckdb.py       | 1 +
 3 files changed, 11 insertions(+), 1 deletion(-)
[assistant] That's pre-existing: `COUNT(DISTINCT x) FILTER (WHERE ...)` already produces the same `IFF(..., DISTINCT x, NULL)` shape on the current code. The FILTER fix only moves `list(...)` onto that existing path instead of crashing. I'll leave the shared `DISTINCT`-inside-`IFF` issue alone and report it.

Now I'll add tests next to the existing DuckDB `LIST` test, without modifying existing ones.
[tool_use Bash] {"command": "sed -n 682,700p tests/dialects/test_duckdb.py", "description": "View existing DuckDB LIST test context"}
[tool_result]         self.validate_all("0b1010", write={"": "0 AS b1010"})
        self.validate_all("0x1010", write={"": "0 AS x1010"})
        self.validate_identity("x ~ y", "REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
        self.validate_all("SELECT * FROM 'x.y'", write={"duckdb": 'SELECT * FROM "x.y"'})
        self.validate_all(
            "SELECT LIST(DISTINCT sample_col) FILTER(WHER
…[7 chars elided]…
ample_col IS NULL) FROM sample_table",
            read={"spark": "SELECT COLLECT_SET(sample_col) FROM sample_table"},
        )
        self.validate_all(
            "SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))",
            write={
                "duckdb": "SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))",
                "spark": "SELECT TRANSFORM(SPLIT('abc , dfg ', ','), x -> TRIM(x))",
            },
        )
        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table\",\n            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample
…[405 chars elided]…
          write={\"snowflake\": \"SELECT ARRAY_AGG(x) FROM t\"},\n        )\n        self.validate_all(\n            \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t\",\n            read={\"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\"},\n            write={\"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t\"},\n        )\n        self.validate_identity(\"SELECT LIST_DISTINCT(x)\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I got the `validate_all` direction wrong in that edit: `read=` parses the other dialect into DuckDB, while I need DuckDB input written to Snowflake. Fixing that now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT ARRAY_AGG(x) FROM t\",\n            read={\"duckdb\": \"SELECT LIST(x) FROM t\"},\n            write={\"snowflake\": \"SELECT ARRAY_AGG(x) FROM t\"},\n       
…[526 chars elided]…
  \"SELECT LIST(x) FILTER(WHERE x IS NOT NULL) FROM t\",\n            write={\"snowflake\": \"SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x) FROM t\",\n            write={\"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t\"},\n        )\n        self.validate_identity(\"SELECT LIST_DISTINCT(x)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-170821-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Running the full suite again, plus a lint pass on the touched files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; ($PY -m ruff check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py sqlglot/generator.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot tests/dialects/test_duckdb.py) 2>&1 | tail -5; git diff", "description": "Run full test suite, lint, and review the diff"}
[tool_result] .................................................................. [ 94%]
............................................ [ 98%]
...........                                                         [100%]
1092 passed, 17860 subtests passed in 51.32s
All checks passed!
175 files already formatted
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 26d481a50..9fc671c0c 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -1822,7 +1822,7 @@ class Generator:
             return f"{
…[2359 chars elided]…
TER(WHERE x IS NOT NULL) FROM t",
+            write={"snowflake": "SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t"},
+        )
+        self.validate_all(
+            "SELECT LIST_DISTINCT(x) FROM t",
+            write={"snowflake": "SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t"},
+        )
+        self.validate_identity("SELECT LIST_DISTINCT(x)")
         self.validate_all(
             "SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))",
             write={
[assistant] DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG`, and DuckDB `list_distinct(col)` to `ARRAY_DISTINCT(ARRAY_COMPACT(col))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests), and ruff check and format are clean. I have not committed anything.

```
SELECT LIST(x) FROM t                  -> SELECT ARRAY_AGG(x) FROM t
SELECT LIST_DISTINCT(x) FROM t         -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
SELECT LIST(DISTINCT x) FROM t         -> SELECT ARRAY_AGG(DISTINCT x) FROM t
SELECT LIST(x ORDER BY y) FROM t       -> SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER B
…[1335 chars elided]…
ake. The only other source that produces it is ClickHouse's `arrayDistinct`. I haven't verified whether ClickHouse keeps NULLs, so ClickHouse-to-Snowflake output may now differ.
- **Pre-existing, not fixed:** `COUNT(DISTINCT x) FILTER (WHERE …)` already generates invalid Snowflake (`IFF(cond, DISTINCT x, NULL)`) on the unmodified code. `list(DISTINCT x) FILTER (…)` now hits the same path, so it produces that invalid shape instead of crashing.
- **Not run against a live Snowflake:** the expected strings are from sqlglot's output, not from executing them in Snowflake, which isn't available here.
