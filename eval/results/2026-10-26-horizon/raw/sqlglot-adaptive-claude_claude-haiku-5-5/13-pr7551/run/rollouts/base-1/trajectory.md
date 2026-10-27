# trajectory base-1

final message:
DuckDB `list()` now transpiles to Snowflake `ARRAY_AGG`, and `list_distinct()` to `ARRAY_DISTINCT(ARRAY_COMPACT(x))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests) and ruff is clean. I haven't committed anything.

```
SELECT list(x)                 -> SELECT ARRAY_AGG(x)
SELECT list(DISTINCT x)        -> SELECT ARRAY_AGG(DISTINCT x)
SELECT list(x ORDER BY y)      -> SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y)
SELECT list_distinct(x)        -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))
```

**What changed**
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` now parses to `ArrayDistinct` with `check_null=False`, meaning NULLs are dropped. DuckDB output is unchanged, so `LIST_DISTINCT(x)` still round-trips.
- `sqlglot/generator.py`: the base `arraydistinct_sql` wraps the input in `ArrayCompact` when `check_null` is `False`. I put it in the base generator so Spark and Trino also get the NULL-dropping form rather than silently keeping NULLs. Nothing else sets `check_null=False`, so existing output is unaffected.
- `sqlglot/generators/snowflake.py`: `list_sql` emits `ARRAY_AGG` for a single-argument `List`. Multi-argument `LIST(a, b)` falls back to the old output.
- `tests/dialects/test_duckdb.py`: two `validate_all` cases covering the outputs above.

**Verification**
- I checked the NULL semantics against DuckDB 1.5.6: `LIST_DISTINCT([1, NULL, 1, NULL])` returns `[1]`, and `LIST` keeps NULLs.
- I couldn't run the generated SQL against a live Snowflake, so the Snowflake side rests on the documented behaviour of `ARRAY_AGG`, `ARRAY_COMPACT` and `ARRAY_DISTINCT`.

**Not fixed: `list(x) FILTER (WHERE ...)` to Snowflake**
This still crashes in the base `filter_sql` (`agg.this` is `None` because `LIST` keeps its argument in `expressions`). The crash predates this change. The obvious rewrite to `ARRAY_AGG(IFF(cond, x, NULL))` would leave NULL elements for non-matching rows, which is wrong. A correct fix needs a different construction, such as wrapping each value in an object and extracting it afterwards. I didn't want to ship that unverified, so it needs a decision from you.

## events
[assistant] I'll start by finding how the DuckDB dialect parses `list` and `list_distinct`, and how Snowflake generates array aggregates.
[tool_use Bash] {"command": "grep -n -i \"list_distinct\\|ListDistinct\\|\\\"LIST\\\"\\|ArrayAgg\\|ARRAY_AGG\\|ArrayUniqueAgg\\|ArrayDistinct\\|\\\"LIST\\\":\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Search DuckDB/Snowflake/expressions for list and array aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/snowflake.py:25:    ARRAY_AGG_INCLUDES_NULLS = None
[assistant] The grep missed `expressions.py`, which may be a package in this version. I'll search the whole package.
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayAgg\\b\\|class ArrayAgg\\|ARRAY_UNIQUE_AGG\\|\\\"LIST\\\"\\|ARRAY_DISTINCT\\|ArrayDistinct\" sqlglot/ | grep -v \"\\.pyc\" | head -80", "description": "Search sqlglot package for list and array aggregate expression handling"}
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
sqlglot/tokens.py:450:        "LIST": TokenType.LIST,
sqlglot/parser.py:323:        "ARRAYAGG": lambda args, dialect: exp.ArrayAgg(
sqlglot/parser.py:326:        "ARRAY_AGG": lambda args, dialect: exp.ArrayAgg(
sqlgl
…[5649 chars elided]…
me_func("COLLECT_SET"),
sqlglot/generators/hive.py:419:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
sqlglot/generators/doris.py:53:        exp.ArrayAgg: rename_func("COLLECT_LIST"),
sqlglot/generators/doris.py:55:        exp.ArrayUniqueAgg: rename_func("COLLECT_SET"),
sqlglot/generators/doris.py:334:        "list",
sqlglot/generators/presto.py:278:        exp.ArrayUniqueAgg: rename_func("SET_AGG"),
sqlglot/generators/starrocks.py:91:        exp.ArrayAgg: rename_func("ARRAY_AGG"),
[assistant] The DuckDB and Snowflake generators already have array-aggregate hooks. Next I'll check how DuckDB parses `LIST`/`LIST_DISTINCT` and how Snowflake emits `ArrayAgg`, `ArrayUniqueAgg` and `ArrayDistinct`.
[tool_use Bash] {"command": "grep -rn -i \"\\\"LIST\\|LIST_DISTINCT\\|\\\"ARRAY_UNIQUE\\|ArrayUniqueAgg\\|ArrayDistinct\\|ARRAY_DISTINCT\" sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/parsers/snowflake.py sqlglot/generators/duckdb.py; echo ---; sed -n 1030,1080p sqlglot/generators/snowflake.py; echo ---; sed -n 3295,3325p sqlglot/generators/duckdb.py; echo ---; sed -n 65,100p sqlglot/expressions/aggregate.py; sed -n 135,150p sqlglot/expressions/array.py", "description": "Inspect DuckDB/Snowflake list and array-agg code paths"}
[tool_result] sqlglot/parsers/duckdb.py:136:        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
sqlglot/parsers/duckdb.py:137:        "LIST_CONCAT": parser.build_array_concat,
sqlglot/parsers/duckdb.py:138:        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:139:        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
sqlglot/parsers/duckdb.py:140:        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
sqlglot/parsers/duckdb.py:141:        "LIST_FILTER": exp.Arr
…[8839 chars elided]…
   arg_types = {"this": True, "expression": True, "null_on_zero_variance": False}


class Count(Expression, AggFunc):
    arg_types = {"this": False, "expressions": False, "big_int": False}
    is_var_len_args = True
# Array properties


class ArrayDistinct(Expression, Func):
    arg_types = {"this": True, "check_null": False}


class ArrayFirst(Expression, Func):
    arg_types = {"this": True, "expression": False}


class ArrayLast(Expression, Func):
    pass


class ArrayMax(Expression, Func):
[assistant] Current generator code is in view. Next I'll run the actual transpilation to see what's emitted today, and check Snowflake's `ARRAY_DISTINCT` parser and generator, since the `check_null` flag is involved.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list_distinct(x) FROM t','SELECT list(x ORDER BY y) FROM t']:\n    e = sqlgl
…[316 chars elided]…
int(sqlglot.parse_one('SELECT ARRAY_COMPACT(x) FROM t', read='snowflake').sql('duckdb'))\n\"; sed -n 405,425p sqlglot/parsers/snowflake.py; grep -n \"arraydistinct\\|ArrayDistinct\\|ArrayCompact\\|arraycompact\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parsers/snowflake.py", "description": "Check current DuckDB to Snowflake output and Snowflake ARRAY_DISTINCT parsing"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
        "CURRENT_TIME": lambda args: exp.Localtime(this=seq_get(args, 0)),
        "APPROX_TOP_K": _build_approx_top_k,
        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
        "ARRAY_CONTAINS": lambda args: exp.ArrayContains(
            this=seq_get(args, 1),
            expression=seq_get(args, 0),
            ensure_variant=False,
            check_null
…[63 chars elided]…
rayDistinct(
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
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
[assistant] The `-I` flag also drops the working directory from `sys.path`, so `sqlglot` isn't importable. I'll rerun with `PYTHONPATH` pointing at the repo, since this is repo code rather than untrusted input.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x ORDER BY y) FROM t', 'SELECT list(x) FILTER (WHERE x > 1) F
…[469 chars elided]…
TINCT(x) FROM t', read='snowflake').sql('snowflake'))\nprint(sqlglot.parse_one('SELECT ARRAY_AGG(x) FROM t', read='duckdb').sql('snowflake'))\nprint(sqlglot.parse_one('SELECT ARRAY_AGG(x) FROM t', read='duckdb').sql('duckdb'))\n\"; grep -n \"ArrayDistinct\\|arraydistinct\" -r sqlglot/ tests/ | head -40", "description": "Run current DuckDB to Snowflake conversions and inspect ArrayDistinct usages"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/b
…[3484 chars elided]…
inct,
sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/expressions/array.py:138:class ArrayDistinct(Expression, Func):
sqlglot/generators/clickhouse.py:279:        exp.ArrayDistinct: rename_func("arrayDistinct"),
sqlglot/generators/duckdb.py:3311:    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
tests/dialects/test_clickhouse.py:724:        self.validate_identity("arrayDistinct([1, 2, 2, 3, 1])").assert_is(exp.ArrayDistinct)
[assistant] Two findings so far:
- DuckDB `list(x)` parses to `exp.List`, which Snowflake emits as `LIST(x)`.
- DuckDB `list_distinct(x)` parses to an `Anonymous` function, so nothing understands it.

Next I'll check the existing `exp.List` and `ARRAY_AGG_INCLUDES_NULLS` handling, and the `check_null` semantics that DuckDB's `ArrayDistinct` generator already relies on.
[tool_use Bash] {"command": "grep -rn \"class List(\\|exp.List\\b\\|def list_sql\\|ARRAY_AGG_INCLUDES_NULLS\\|class ArrayCompact\" sqlglot/ | head -30; echo ---; sed -n 640,665p sqlglot/dialects/dialect.py; echo ---; sed -n 20,30p sqlglot/dialects/snowflake.py; echo ---; sed -n 3311,3335p sqlglot/generators/duckdb.py; echo ---; grep -n \"check_null\" -r sqlglot/ | head -30", "description": "Inspect List node, NULL-inclusion flags and check_null usage"}
[tool_result] sqlglot/parser.py:324:            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/parser.py:327:            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/generator.py:5350:            self.dialect.ARRAY_AGG_INCLUDES_NULLS and array_agg_expr.args.get("nulls_excluded")
sqlglot/dialects/dialect.py:647:    ARRAY_AGG_INCLUDES_NULLS: bool | None = True
sqlglot
…[3916 chars elided]…
qlglot/generators/duckdb.py:559:    if expression.args.get("check_null"):
sqlglot/generators/duckdb.py:560:        check_null_in_array = exp.Nullif(
sqlglot/generators/duckdb.py:564:        return self.sql(exp.If(this=expr.is_(exp.Null()), true=check_null_in_array, false=func))
sqlglot/generators/duckdb.py:587:    check_nulls = exp.and_(
sqlglot/generators/duckdb.py:604:            exp.paren(check_nulls, copy=False),
sqlglot/generators/duckdb.py:3315:        if expression.args.get("check_null"):
[assistant] The key facts are settled:
- Snowflake's `ARRAY_AGG` keeps NULLs, which matches DuckDB's `list()`.
- Snowflake's parser already tags `ARRAY_DISTINCT` with `check_null=True` (NULLs kept). DuckDB's generator uses that flag to add NULLs back, so the flag's meaning is already established.

Before editing, I'll check the existing tests for these functions and whether the base generator has an `ArrayCompact` path I can reuse.
[tool_use Bash] {"command": "grep -rn -i \"list_distinct\\|LIST(\\|list(\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head -40; echo ---; grep -n \"ArrayCompact\\|arraycompact\\|def arrayagg\\|ArrayAgg\" sqlglot/generator.py sqlglot/generators/snowflake.py | head; echo ---; grep -n \"def array_sql\\|def arraydistinct\\|ArrayDistinct\" sqlglot/generators/*.py | head -30; git log --oneline -3 -- sqlglot/generators/duckdb.py | cat", "description": "Find existing tests and related generator hooks for list functions"}
[tool_result] tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNHEX('08000000000000000000' || h) END 
…[4828 chars elided]…
qlglot/generators/mysql.py:609:    def array_sql(self, expression: exp.Array) -> str:
sqlglot/generators/redshift.py:323:    def array_sql(self, expression: exp.Array) -> str:
sqlglot/generators/postgres.py:499:    def array_sql(self, expression: exp.Array) -> str:
b334dccb7 feat(duckdb)!: mark DECOMPRESS_BINARY as unsupported  (#7546)
8669e55f3 feat(duckdb)!: mark DECOMPRESS_STRING as unsupported [CLAUDE] (#7545)
ceb14fad0 feat(duckdb): Add transpilation unsupported for SOUNDEX function (#7517)
[assistant] Existing Snowflake→DuckDB tests already confirm the null-handling contract (`ARRAY_DISTINCT` keeps a NULL, DuckDB needs `LIST_APPEND`), so I'll follow that convention. My plan:

1. **DuckDB parser:** map `LIST_DISTINCT` to `ArrayDistinct` with `check_null=False`. That marks it as NULL-dropping, which DuckDB's generator already emits as plain `LIST_DISTINCT`, so DuckDB round-trips are unchanged.
2. **Base generator:** for `check_null=False`, wrap the input in `ArrayCompact` before the distinct function. The same logic then yields `ARRAY_DISTINCT(ARRAY_COMPACT(x))` for Snowflake. I'm putting it in the base generator so other targets don't silently keep NULLs either. Only the new `check_null=False` path is affected.
3. **Snowflake generator:** `list_sql` emits `ARRAY_AGG` for a single-argument `List`.

I'll check the imports I need first.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/duckdb.py | grep -n \"import\"; grep -n \"seq_get\" sqlglot/parsers/duckdb.py | head -3; sed -n 5365,5395p sqlglot/generator.py; grep -n \"def function_fallback_sql\\|def arrayagg_sql\\|def list_sql\" sqlglot/generator.py; <work>/env-sqlglot/bin/python -c \"import duckdb; print(duckdb.__version__)\"", "description": "Check parser imports, generator helpers, and duckdb availability"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
15:from sqlglot.helper import seq_get
22:    return exp.SortArray(this=seq_get(args, 0), asc=exp.false())
26:    return exp.ArrayPrepend(this=seq_get(args, 1), e
…[716 chars elided]…
   this = self.sql(expression, "this")
        expr = self.sql(expression, "expression")

        return f"{this} APPLY({expr})"

    def _grant_or_revoke_sql(
        self,
        expression: exp.Grant | exp.Revoke,
        keyword: str,
        preposition: str,
        grant_option_prefix: str = "",
        grant_option_suffix: str = "",
    ) -> str:
4312:    def function_fallback_sql(self, expression: exp.Func) -> str:
5370:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
1.5.6
[assistant] DuckDB 1.5.6 is installed in the project venv, so I can check the NULL semantics against the real engine. Making the parser edit first:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,", "new_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(this=seq_get(args, 0), check_null=False),\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", "old_string": "    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        array_agg = self.function_fallback_sql(expression)\n        return self._add_arrayagg_null_filter(array_agg, expression, expression.this)\n", "new
…[82 chars elided]…
rray_agg = self.function_fallback_sql(expression)\n        return self._add_arrayagg_null_filter(array_agg, expression, expression.this)\n\n    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        if expression.args.get(\"check_null\") is False:\n            arr = exp.ArrayCompact(this=arr)\n        return self.func(\"ARRAY_DISTINCT\", arr)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:\n        return self.func(\"ARRAY_TO_STRING\", expression.this, expression.expression)", "new_string": "    def list_sql(self, expression: exp.List) -> str:\n        if len(expression.expressions) != 1:\n            return self.function_fallback_sql(expression)\n        return self.sql(exp.ArrayAgg(this=expression.expressions[0]))\n\n    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:\n        return self.func(\"ARRAY_TO_STRING\", expression.this, expression.expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Edits are in. Now I'll check the transpilation outputs and confirm the NULL semantics against real DuckDB.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\ncases = ['SELECT list(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(x) FILTER(WHERE x > 1) FROM t','SELECT list_distinct(x) FROM t','SELECT list(
…[406 chars elided]…
[0])\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t', read='clickhouse', write='snowflake')[0])\n\"; PYTHONPATH=. $PY -c \"\nimport duckdb\nc = duckdb.connect()\nprint(c.sql('SELECT LIST_DISTINCT([1, NULL, 1, NULL]) AS r, LIST([1,NULL,1]) AS l, LIST(x ORDER BY y) FROM (SELECT 1 AS x, 2 AS y)').fetchall())\n\"", "description": "Verify new transpilation outputs and DuckDB NULL semantics"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/__init__.py", line 211, in transpile
    write.generate(expression, copy=False, **opts) if expression else ""
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/dialects/dialec
…[2207 chars elided]…
Y_AGG(x) FROM t 
   duckdb:    SELECT LIST(x) FROM t 
   spark:     SELECT LIST(x) FROM t
SELECT list(DISTINCT x) FROM t 
   snowflake: SELECT ARRAY_AGG(DISTINCT x) FROM t 
   duckdb:    SELECT LIST(DISTINCT x) FROM t 
   spark:     SELECT LIST(DISTINCT x) FROM t
SELECT list(x ORDER BY y) FROM t 
   snowflake: SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t 
   duckdb:    SELECT LIST(x ORDER BY y) FROM t 
   spark:     SELECT LIST(x ORDER BY y NULLS LAST) FROM t
[([1], [[1, None, 1]], [1])]
[assistant] The `list`, `list(DISTINCT)`, and `list(... ORDER BY)` cases now produce the right Snowflake SQL. The `FILTER (WHERE ...)` case still crashes in the base `filter_sql`, and the crash stopped the loop before the remaining cases ran. I'll look at `filter_sql`, since `list(x) FILTER (WHERE ...)` is a common DuckDB idiom.
[tool_use Bash] {"command": "sed -n 1795,1840p sqlglot/generator.py", "description": "Read filter_sql in base generator"}
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
…[1006 chars elided]…
    def hint_sql(self, expression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"

    def indexparameters_sql(self, expression: exp.IndexParameters) -> str:
        using = self.sql(expression, "using")
        using = f" USING {using}" if using else ""
        columns = self.expressions(expression, key="columns", flat=True)
[assistant] `filter_sql` assumes the aggregate's argument is `agg.this`. DuckDB's `LIST` stores its argument in `expressions`, so `agg.this` is `None`. This crash predates my change; the earlier run showed it too. Before choosing a fix, I need to see what the existing `ArrayAgg` FILTER path produces for Snowflake, since it's the template a `List` fix would follow.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['SELECT ARRAY_AGG(x) FILTER(WHERE c > 1) FROM t', 'SELECT COUNT(x) FILTER(WHERE c > 1) FROM t']:\n    print(s, '->', sqlglot.transpile(s, read='duckdb', write='snowflake')[0])\nfor 
…[431 chars elided]…
sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t', read='clickhouse', write='snowflake')[0])\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t', read='snowflake', write='duckdb')[0])\n\"; grep -n \"AGGREGATE_FILTER_SUPPORTED\" sqlglot/generators/snowflake.py sqlglot/generator.py | head -4", "description": "Compare FILTER handling for ArrayAgg versus List and check list_distinct outputs"}
[tool_result] SELECT ARRAY_AGG(x) FILTER(WHERE c > 1) FROM t -> SELECT ARRAY_AGG(IFF(c > 1, x, NULL)) FROM t
SELECT COUNT(x) FILTER(WHERE c > 1) FROM t -> SELECT COUNT(IFF(c > 1, x, NULL)) FROM t
SELECT list_distinct(x) FROM t 
   snowflake: SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t 
   duckdb:    SELECT LIST_DISTINCT(x) FROM t 
   spark:     SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t 
   trino:     SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
SELECT list(a, b) FROM t 
   snowflake: SELECT LIST(a, 
…[321 chars elided]…
AY_COMPACT(ARRAY(1, NULL, 1))) 
   trino:     SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY[1, NULL, 1]))
SELECT ARRAY_DISTINCT(x) FROM t
SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END FROM t
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
sqlglot/generators/snowflake.py:383:    AGGREGATE_FILTER_SUPPORTED = False
[assistant] Two things to record from this:
- **`list_distinct` is correct now.** Snowflake gets `ARRAY_DISTINCT(ARRAY_COMPACT(x))`, and the same logic gives the right result for Spark and Trino. DuckDB round-trips are unchanged.
- **`list(x) FILTER (WHERE ...)` is a separate, pre-existing problem.** Snowflake has no `FILTER` clause, so it rewrites the argument as `IFF(cond, x, NULL)`. `ARRAY_AGG` keeps NULLs, so non-matching rows would leak NULL elements. That's already the behaviour for `ARRAY_AGG(x) FILTER(...)`. A correct fix needs a different construction, which I can't verify without Snowflake access, so I'll leave it and report it instead of emitting wrong SQL.

Next I'll add the tests to the DuckDB dialect test file, near the existing `LIST(DISTINCT ...)` test.
[tool_use Bash] {"command": "sed -n 680,700p tests/dialects/test_duckdb.py", "description": "Read existing LIST test context in DuckDB tests"}
[tool_result]         self.validate_identity("DATESUB('YEAR', col, '2020-01-01')").assert_is(exp.Anonymous)
        self.validate_identity("SELECT SHA256('abc')")

        self.validate_all("0b1010", write={"": "0 AS b1010"})
        self.validate_all("0x1010", write={"": "0 AS x1010"})
        self.validate_identity("x ~ y", "REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
        self.validate_al
…[157 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table\",\n            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample
…[522 chars elided]…
 \"SELECT ARRAY_AGG(x), ARRAY_AGG(DISTINCT x), ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x) FROM t\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-182307-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll run the affected dialect test files, then the full suite with the project's configured command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_clickhouse.py 2>&1 | tail -15", "description": "Run DuckDB, Snowflake, and ClickHouse dialect tests"}
[tool_result] .........................................................................................................................................................................                                                            [100%]
169 passed, 2436 subtests passed in 1.66s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit: ${PIPESTATUS[0]}\"; git status --short; git diff --stat", "description": "Run the full test suite and show the working tree diff"}
[tool_result] ........................................................................................................................................... [ 24%]
....................................................................................................................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
........................... [ 43%]
................................................................................................. [ 51%]
...........
…[532 chars elided]…
......................................                                                        [100%]
1092 passed, 17861 subtests passed in 80.08s (0:01:20)
exit: 
 M sqlglot/generator.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generator.py            |  6 ++++++
 sqlglot/generators/snowflake.py |  5 +++++
 sqlglot/parsers/duckdb.py       |  1 +
 tests/dialects/test_duckdb.py   | 14 ++++++++++++++
 4 files changed, 26 insertions(+)
[assistant] The full suite passes: 1092 passed, no failures. Last, the style check. The repo uses ruff, and one of my test lines is long.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/generator.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/generator.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -20", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
[assistant] DuckDB `list()` now transpiles to Snowflake `ARRAY_AGG`, and `list_distinct()` to `ARRAY_DISTINCT(ARRAY_COMPACT(x))`, which drops NULLs the way DuckDB does. The full suite passes (1092 tests) and ruff is clean. I haven't committed anything.

```
SELECT list(x)                 -> SELECT ARRAY_AGG(x)
SELECT list(DISTINCT x)        -> SELECT ARRAY_AGG(DISTINCT x)
SELECT list(x ORDER BY y)      -> SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y)
SELECT list_distinct(x)        -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))
```

**What changed**
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` now parses to 
…[922 chars elided]…
 on the documented behaviour of `ARRAY_AGG`, `ARRAY_COMPACT` and `ARRAY_DISTINCT`.

**Not fixed: `list(x) FILTER (WHERE ...)` to Snowflake**
This still crashes in the base `filter_sql` (`agg.this` is `None` because `LIST` keeps its argument in `expressions`). The crash predates this change. The obvious rewrite to `ARRAY_AGG(IFF(cond, x, NULL))` would leave NULL elements for non-matching rows, which is wrong. A correct fix needs a different construction, such as wrapping each value in an object and extracting it afterwards. I didn't want to ship that unverified, so it needs a decision from you.
