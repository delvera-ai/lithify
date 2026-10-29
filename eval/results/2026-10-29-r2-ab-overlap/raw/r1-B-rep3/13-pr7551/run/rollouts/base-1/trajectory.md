# trajectory base-1

final message:
DuckDB → Snowflake now translates `list(col)` and `list_distinct(col)`. The full suite passes (1092 tests) and ruff is clean. I haven't committed.

**Mappings**
- `list(col)` → `ARRAY_AGG(col)`. `ORDER BY` inside `list()` becomes `WITHIN GROUP (ORDER BY ...)`, and `DISTINCT` carries through.
- `list_distinct(x)` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`. This keeps DuckDB's NULL-dropping, since Snowflake's `ARRAY_DISTINCT` keeps NULLs.

**Changes**
- `sqlglot/expressions/array.py`: `ArrayDistinct` gets a `nulls_excluded` flag.
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` parses to `ArrayDistinct(nulls_excluded=True)`.
- `sqlglot/generators/snowflake.py`: `list_sql`, `arraydistinct_sql`, and a `filter_sql` override for `LIST(...) FILTER(...)`.
- `tests/dialects/test_duckdb.py`: three `validate_all` cases covering the mappings above.

**Decisions**
- **New flag instead of `check_null`.** `check_null=True` already means "source keeps NULLs" (Snowflake parsing sets it). Other parsers build `ArrayDistinct` without any flag and do keep NULLs, such as Spark's `ARRAY_DISTINCT` and ClickHouse's `arrayDistinct`. Reusing `check_null` would have made Spark→Snowflake and ClickHouse→Snowflake start dropping NULLs.
- **`list` mapped in the Snowflake generator, not the DuckDB parser.** DuckDB's `list` parses to the base `exp.List`. Switching it to `ArrayAgg` in the DuckDB parser would change DuckDB→DuckDB output for an existing test (`LIST(DISTINCT ...) FILTER(...)`), so I left that alone.

**Known gap: FILTER**
`list(x) FILTER(WHERE c)` used to crash the Snowflake generator, because `List` isn't an aggregate. It now emits `ARRAY_AGG(IFF(c, x, NULL))`, which keeps NULL placeholders from filtered-out rows, unlike DuckDB. I couldn't find a Snowflake form that is exact here, so the generator emits an `unsupported` warning. Plain `ARRAY_AGG` FILTER translation already has this same problem.

**Side effect to be aware of**
DuckDB `list_distinct` → other dialects (for example Spark) now emits `ARRAY_DISTINCT(x)` with no NULL compaction. Previously it emitted `LIST_DISTINCT(x)`, which those engines don't support anyway, so the output is still wrong for NULL-containing arrays, just differently.

I haven't run these against a live Snowflake; the NULL semantics come from the behaviour you described.

## events
[tool_use Bash] {"command": "grep -n -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayAgg\\|\\\"LIST\\\"\\|\\\"LIST_DISTINCT\\\"\\|ARRAY_DISTINCT\\|ArrayDistinct\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Search for list/array distinct handling in dialects"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -n -i \"\\\"list\\\"\\|ARRAY_AGG\\|array_agg\\|\\\"LIST\\\"\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py | head -60; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT ARRAY_AGG(x) FROM t','SELECT ARRAY_DISTINCT(x) FROM t']:\n    e=sqlglot.parse_one(q,read='duckdb')\n    print(repr(e.selects[0]))\n    print(e.sql('snowflake'))\n\"", "description": "Inspect DuckDB/Snowflake array function mappings"}
[tool_result] sqlglot/dialects/snowflake.py:25:    ARRAY_AGG_INCLUDES_NULLS = None
List(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))])
SELECT LIST(x) FROM t
Anonymous(
  this=list_distinct,
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))])
SELECT LIST_DISTINCT(x) FROM t
ArrayAgg(
  this=Column(
    this=Identifier(this=x, quoted=False)))
SELECT ARRAY_AGG(x) FROM t
ArrayDistinct(
  this=Column(
    this=Identifier(this=x, quoted=False)))
SELECT ARRAY_DISTINCT(x) FROM t
[tool_use Bash] {"command": "grep -n \"class List(\\|class ArrayAgg\\|class ArrayDistinct\\|class ArrayCompact\\|class ArrayUniqueAgg\\|class ArrayFilter\\|class ArrayCompact\" -A6 sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null | head -80; echo ---; grep -n \"ARRAY_AGG_INCLUDES_NULLS\\|ArrayAgg\\|ArrayDistinct\\|ArrayCompact\\|ArrayUniqueAgg\\|exp.List\\b\\|\\\"LIST\\\"\\|ListDistinct\\|list_distinct\" sqlglot/dialects/*.py | head -80", "description": "Locate array expression classes and dialect handling"}
[tool_result] sqlglot/expressions/aggregate.py:71:class ArrayAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py-72-    arg_types = {"this": True, "nulls_excluded": False}
sqlglot/expressions/aggregate.py-73-
sqlglot/expressions/aggregate.py-74-
sqlglot/expressions/aggregate.py-75-class ArrayConcatAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py-76-    pass
sqlglot/expressions/aggregate.py-77-
--
sqlglot/expressions/aggregate.py:83:class ArrayUniqueAgg(Expression, AggFunc):
sqlglot/expression
…[1880 chars elided]…
types = {"this": True, "expression": False}
sqlglot/expressions/array.py-144-
---
5 matches in 3 files:

sqlglot/dialects/dialect.py:647:ARRAY_AGG_INCLUDES_NULLS: bool | None = True
sqlglot/dialects/dialect.py:648:"""Whether ArrayAgg needs to filter NULL values."""
sqlglot/dialects/dialect.py:2176:def array_compact_sql(self: Generator, expression: exp.ArrayCompact) -> str:
sqlglot/dialects/hive.py:24:ARRAY_AGG_INCLUDES_NULLS = None
sqlglot/dialects/snowflake.py:25:ARRAY_AGG_INCLUDES_NULLS = None
[tool_use Bash] {"command": "grep -n \"ArrayDistinct\\|ArrayCompact\\|ArrayAgg\\|exp.List\\|\\\"LIST\\|List\\b\\|check_null\\|ARRAY_AGG\\|array_agg\\|ARRAY_COMPACT\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py; echo ---; sed -n 2170,2190p sqlglot/dialects/dialect.py; echo ---; grep -n \"def arrayagg_sql\\|def _array_agg\\|ARRAY_AGG_INCLUDES_NULLS\" -A12 sqlglot/dialects/dialect.py | head -40; echo ---; grep -n \"tests.*list_distinct\\|list_distinct\\|LIST_DISTINCT\" -r tests | head", "description": "Inspect duckdb/snowflake array handling and tests"}
[tool_result] 1 matches in 1 files:

sqlglot/dialects/snowflake.py:25:ARRAY_AGG_INCLUDES_NULLS = None
---

    unnest = exp.Unnest(expressions=[expression.this])
    filtered = exp.select(alias).from_(exp.alias_(unnest, None, table=[alias])).where(cond)
    return self.sql(exp.Array(expressions=[filtered]))


def array_compact_sql(self: Generator, expression: exp.ArrayCompact) -> str:
    lambda_id = exp.to_identifier("_u")
    cond = exp.Is(this=lambda_id, expression=exp.null()).not_()
    return self.sql(
 
…[2868 chars elided]…
ts/test_snowflake.py:3121:                "duckdb": "SELECT CASE WHEN ARRAY_LENGTH([1, 2, 2, 3, 1]) <> LIST_COUNT([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
tests/dialects/test_dialect.py:1770:                "duckdb": "SELECT CASE WHEN [1, 2, 3] IS NULL OR [2] IS NULL THEN NULL ELSE LIST_FILTER(LIST_DISTINCT([1, 2, 3]), e -> LENGTH(LIST_FILTER([2], x -> x IS NOT DISTINCT FROM e)) = 0) END",
[tool_use Bash] {"command": "grep -n -i \"distinct\\|arraycompact\\|array_compact\\|ArrayAgg\\|arrayagg\\|def list\\|List\\b\" sqlglot/dialects/snowflake.py | head -40; echo ---; grep -n -i \"arraydistinct\\|array_distinct\\|ArrayAgg\\|arrayagg\\|def list\\|exp.List\\|ListDistinct\\|nulls_excluded\\|check_null\" sqlglot/dialects/duckdb.py | head -40; echo ---; PY=<work>
…[502 chars elided]…
Y_DISTINCT(x)',read='snowflake',write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FROM t',read='snowflake',write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_COMPACT(x) FROM t',read='snowflake',write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_COMPACT(x) FROM t',read='duckdb',write='snowflake'))\n\"", "description": "Probe current transpile behavior and generator handlers"}
[tool_result ERROR] Exit code 1
105:        # EPOCH_SECOND as a distinct value for two reasons:
---
---
Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cac
…[1818 chars elided]…
lake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1083, in sql
    sql = handler(self, expression)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1827, in filter_sql
    agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
    ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'replace'
SELECT list(x) FROM t => SELECT LIST(x) FROM t
[tool_use Bash] {"command": "grep -rn \"exp\\.List\\b\\|\\\"LIST\\\"\\|LIST_DISTINCT\\|list_distinct\" sqlglot | head -30; echo ---; grep -n \"ArrayDistinct\\|ArrayAgg\\|ArrayCompact\\|ArrayUniqueAgg\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py sqlglot/parsers/snowflake.py 2>/dev/null; ls sqlglot/generators sqlglot/parsers 2>/dev/null | head -50", "description": "Find List and list_distinct references across sqlglot"}
[tool_result] sqlglot/parsers/mysql.py:559:        elif self._match_text_seq("LIST"):
sqlglot/tokens.py:450:        "LIST": TokenType.LIST,
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parser.py:1720:        "LIST": lambda self: self._parse_analyze_list(),
sqlglot/generators/dremio.py:59:        exp.DType.ARRAY: "LIST",
Binary file sqlglot/generators/__pycache__/duckdb.cpython-312.pyc matches
sqlglot/generators/materialize.py:39:            return "LIST"
sqlglot/generators/materialize.py:47:    def
…[2656 chars elided]…
y  3.9K
redshift.py  10.1K
risingwave.py  1.1K
singlestore.py  42.1K
snowflake.py  46.3K
solr.py  192B
spark.py  7.7K
spark2.py  9.6K
sqlite.py  11.9K
starrocks.py  9.9K
tableau.py  1.6K
teradata.py  7.0K
trino.py  2.3K
tsql.py  25.2K
__init__.py  1B
athena.py  2.3K
base.py  582B
bigquery.py  28.3K
clickhouse.py  32.6K
databricks.py  1.8K
doris.py  5.0K
dremio.py  3.8K
drill.py  671B
druid.py  108B
duckdb.py  15.2K
dune.py  124B
exasol.py  6.5K
fabric.py  1.3K
hive.py  10.3K
materialize.py  1.3K
[tool_use Bash] {"command": "sed -n 3295,3325p sqlglot/generators/duckdb.py; echo ----SF-GEN; sed -n 1030,1050p sqlglot/generators/snowflake.py; grep -n \"ArrayDistinct\\|arraydistinct\\|ARRAY_DISTINCT\\|ArrayCompact\\|array_compact\" sqlglot/generators/snowflake.py; echo ----SF-PARSE; sed -n 405,425p sqlglot/parsers/snowflake.py; echo ----DUCK-PARSE; grep -n \"\\\"LIST\\|LIST_DISTINCT\\|ArrayDistinct\\|ArrayAgg\\|\\\"LIST_\\|ListDistinct\" sqlglot/parsers/duckdb.py | head -30", "description": "Read relevant generator and parser snippets"}
[tool_result]         expr = expression.this
        result = exp.replace_placeholders(self.APPROXIMATE_SIMILARITY_TEMPLATE.copy(), expr=expr)
        return f"({self.sql(result)})"

    def arrayuniqueagg_sql(self, expression: exp.ArrayUniqueAgg) -> str:
        return self.sql(
            exp.Filter(
                this=exp.func("LIST", exp.Distinct(expressions=[expression.this])),
                expression=exp.Where(this=expression.this.copy().is_(exp.null()).not_()),
            )
        )

    def ar
…[2585 chars elided]…
rrayContains.from_arg_list,
139:0:exp.CosineDistance.from_arg_list,
140:0:exp.EuclideanDistance.from_arg_list,
141:0:exp.ArrayFilter.from_arg_list,
142:0:exp.ArrayContains.from_arg_list,
143:0:exp.ArrayOverlaps.from_arg_list,
144:0:exp.ArrayMax.from_arg_list,
145:0:exp.ArrayMin.from_arg_list,
146:0:_build_array_prepend,
147:0:_build_sort_array_desc,
148:0:exp.SortArray.from_arg_list,
149:0:exp.Transform.from_arg_list,
150:0:lambda args: exp.Array(expressions=args),
187:0:self._parse_string_agg()
[tool_use Bash] {"command": "grep -rn -i \"list(\" tests/dialects/test_duckdb.py | head -40; echo ---; grep -rn -i \"list_distinct\\|array_distinct\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | cut -c1-250 | head -20; echo ---; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT ARRAY_AGG(x) FROM t',read
…[142 chars elided]…
ARRAY_DISTINCT(x) FROM t',read='snowflake',write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t',read='duckdb',write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_COMPACT(x) FROM t',read='duckdb',write='snowflake'))\nprint(sqlglot.transpile('SELECT list(x) FROM t',read='duckdb',write='snowflake'))\n\"", "description": "Grep duckdb tests and probe array transpilations"}
[tool_result] tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
---
tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04
tests/dialects/test_snowflake.py:471:                "duckdb": "SELECT CASE WHEN CAST(m1 AS MAP(TEXT, INT)) 
…[1286 chars elided]…
 LIST_COUNT([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINC
---
ArrayAgg(
  this=Column(
    this=Identifier(this=x, quoted=False)))
['SELECT ARRAY_AGG(x) FROM t']
['SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
['SELECT ARRAY_COMPACT(x) FROM t']
['SELECT LIST(x) FROM t']
[tool_use Bash] {"command": "sed -n 1805,1835p sqlglot/generator.py; echo ---; grep -n \"def filter_sql\" -A3 sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py; echo ---; grep -rn \"FILTER(WHERE\\|FILTER (WHERE\" tests/dialects/test_snowflake.py | cut -c1-200 | head; echo ---; grep -n \"class Filter\" -A3 sqlglot/expressions/*.py", "description": "Read Filter generation logic and related tests"}
[tool_result]         count = f" {count}" if count else ""
        limit_options = self.sql(expression, "limit_options")
        limit_options = f"{limit_options}" if limit_options else " ROWS ONLY"
        return f"{self.seg('FETCH')}{direction}{count}{limit_options}"

    def limitoptions_sql(self, expression: exp.LimitOptions) -> str:
        percent = " PERCENT" if expression.args.get("percent") else ""
        rows = " ROWS" if expression.args.get("rows") else ""
        with_ties = " WITH TIES" if expre
…[2279 chars elided]…

tests/dialects/test_snowflake.py:6590:                "duckdb": "SELECT CASE WHEN ISNAN(CORR(a, b) FILTER(WHERE c > 0)) THEN NULL ELSE CORR(a, b) FILTER(WHERE c > 0) END",
tests/dialects/test_snowflake.py:6594:            "SELECT CORR(a, b) FILTER(WHERE c > 0) OVER (PARTITION BY d)",
---
sqlglot/expressions/core.py:2041:class Filter(Expression):
sqlglot/expressions/core.py-2042-    arg_types = {"this": True, "expression": True}
sqlglot/expressions/core.py-2043-
sqlglot/expressions/core.py-2044-
[tool_use Bash] {"command": "grep -rn \"AGGREGATE_FILTER_SUPPORTED\\|ARRAY_AGG_INCLUDES_NULLS\" sqlglot | grep -v pyc; echo ---; grep -n \"def arrayagg_sql\" -A25 sqlglot/generator.py | head -40; echo ---; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in ['SELECT list(x) FROM t','SELECT list(DISTINCT x) FILTER(WHERE x IS NOT NULL) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(x) OVER (PARTITION BY g) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct(x) FILTER(WHERE x > 1) FROM t']:\n    try:\n        print(q, '=>', sqlglot.transpile(q,read='duckdb',write='snowflake'))\n    except Exception as ex: print(q,'ERR',type(ex).__name__, ex)\n\"", "description": "Check filter flags and probe several DuckDB list queries"}
[tool_result] sqlglot/parser.py:324:            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/parser.py:327:            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
sqlglot/generator.py:5350:            self.dialect.ARRAY_AGG_INCLUDES_NULLS and array_agg_expr.args.get("nulls_excluded")
sql
…[1358 chars elided]…
OM t => ['SELECT LIST(x) FROM t']
SELECT list(DISTINCT x) FILTER(WHERE x IS NOT NULL) FROM t ERR AttributeError 'NoneType' object has no attribute 'replace'
SELECT list(x ORDER BY y) FROM t => ['SELECT LIST(x ORDER BY y) FROM t']
SELECT list(x) OVER (PARTITION BY g) FROM t => ['SELECT LIST(x) OVER (PARTITION BY g) FROM t']
SELECT list_distinct(x) FROM t => ['SELECT LIST_DISTINCT(x) FROM t']
SELECT list_distinct(x) FILTER(WHERE x > 1) FROM t ERR AttributeError 'str' object has no attribute 'copy'
[tool_use Bash] {"command": "sed -n 5336,5369p sqlglot/generator.py; echo ---; sed -n 1,80p sqlglot/parsers/duckdb.py | grep -n \"FUNCTIONS\\|def \\|class \" ; grep -n \"FUNCTIONS = {\" -A3 sqlglot/parsers/duckdb.py | head; grep -n \"\\\"LIST\\|\\\"ARRAY_AGG\\|\\\"LIST_\\|\\\"ARRAY_UNIQUE\\|\\\"LIST_UNIQUE\" sqlglot/parsers/duckdb.py sqlglot/parsers/snowflake.py sqlglot/parser.py | head", "description": "Read array-agg null-filter helper and parser keys"}
[tool_result]         """
        Add NULL filter to ARRAY_AGG if dialect requires it.

        Args:
            array_agg_sql: The generated ARRAY_AGG SQL string
            array_agg_expr: The ArrayAgg expression node
            column_expr: The column/expression to filter (before ORDER BY wrapping)

        Returns:
            SQL string with FILTER clause added if needed
        """
        # Add a NULL FILTER on the column to mimic the results going from a dialect that excludes nulls
        # on ARRA
…[2149 chars elided]…
ser.py:775:"LIST": exp.List,
sqlglot/parser.py:1720:"LIST": lambda self: self._parse_analyze_list(),
sqlglot/parsers/duckdb.py:136:"LIST_APPEND": exp.ArrayAppend.from_arg_list,
sqlglot/parsers/duckdb.py:137:"LIST_CONCAT": parser.build_array_concat,
sqlglot/parsers/duckdb.py:138:"LIST_CONTAINS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:139:"LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
sqlglot/parsers/duckdb.py:140:"LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
[tool_use Bash] {"command": "grep -rn \"ArrayDistinct\\|check_null\" sqlglot --include=*.py | grep -v \"^sqlglot/expressions/array.py:13[89]\" | cut -c1-220; echo ---; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FILTER(WHERE c > 1) FROM t',read='duckdb',write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t',read='spark',write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t',read='duckdb',write='spark'))\n\"", "description": "Find all ArrayDistinct usages and probe Filter fallback"}
[tool_result] (eval):1: no matches found: --include=*.py
---
['SELECT ARRAY_AGG(IFF(c > 1, x, NULL)) FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
[tool_use Bash] {"command": "grep -rn \"ArrayDistinct\\|check_null\" sqlglot | grep -v \"\\.pyc\" | cut -c1-220", "description": "Find all ArrayDistinct and check_null usages"}
[tool_result] sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/parsers/snowflake.py:412:            check_null=True,
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
sqlglot/parsers/snowflake.py:416:            check_null=True,
sqlglot/typing/hive.py:53:            exp.ArrayDistinct,
sqlglot/expressions/datatypes.py:375:    def is_type(self, *dtypes: DATA_TYPE, check_nullable: bool = False) -> bool:
sqlglot/expression
…[1075 chars elided]…
0:        check_null_in_array = exp.Nullif(
sqlglot/generators/duckdb.py:564:        return self.sql(exp.If(this=expr.is_(exp.Null()), true=check_null_in_array, false=func))
sqlglot/generators/duckdb.py:587:    check_nulls = exp.and_(
sqlglot/generators/duckdb.py:604:            exp.paren(check_nulls, copy=False),
sqlglot/generators/duckdb.py:3311:    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
sqlglot/generators/duckdb.py:3315:        if expression.args.get("check_null"):
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|seq_get\" sqlglot/parsers/duckdb.py | head -20; echo ---; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py; echo ---; grep -n \"def list_sql\\|def filter_sql\\|def arraydistinct_sql\" sqlglot/generator.py sqlglot/generators/*.py | head; echo ---; sed -n 130,146p sqlglot/parsers/duckdb.py; echo ---; sed -n 136,140p sqlglot/expressions/array.py; echo; sed -n 1,30p tests/dialects/test_duckdb.py | grep -n \"class\\|def \" ", "description": "Check imports and surrounding code for edits"}
[tool_result] 29 matches in 3 files:

125:0:lambda args: exp.UnixToTime(this=seq_get(args, 0), scale=exp.UnixToTime.MILLIS),
167:0:lambda args: exp.SHA2(this=seq_get(args, 0), length=exp.Literal.number(256)),
sqlglot/parsers/duckdb.py:1:from __future__ import annotations
sqlglot/parsers/duckdb.py:3:import typing as t
sqlglot/parsers/duckdb.py:5:from sqlglot import exp, parser
sqlglot/parsers/duckdb.py:6:from sqlglot.trie import new_trie
sqlglot/parsers/duckdb.py:7:from sqlglot.dialects.dialect import (
sqlglo
…[2646 chars elided]…
.EuclideanDistance.from_arg_list,
        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
        "LIST_HAS": exp.ArrayContains.from_arg_list,
        "LIST_HAS_ANY": exp.ArrayOverlaps.from_arg_list,
        "LIST_MAX": exp.ArrayMax.from_arg_list,
        "LIST_MIN": exp.ArrayMin.from_arg_list,
        "LIST_PREPEND": _build_array_prepend,
---


class ArrayDistinct(Expression, Func):
    arg_types = {"this": True, "check_null": False}


10:class TestDuckDB(Validator):
13:    def test_duckdb(self):
[assistant] Current behavior: DuckDB `list()` parses to the base `exp.List` (a plain `Func`, not an aggregate), and `list_distinct` falls through as an `Anonymous`. Snowflake's `ARRAY_DISTINCT` already maps to `ArrayDistinct` with `check_null=True` (NULLs kept). I'll make the DuckDB-side NULL-dropping explicit on `ArrayDistinct` rather than reusing `check_null`, since other parsers (ClickHouse, Spark via the base parser) build `ArrayDistinct` without that flag and do keep NULLs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/array.py", "old_string": "class ArrayDistinct(Expression, Func):\n    arg_types = {\"this\": True, \"check_null\": False}", "new_string": "class ArrayDistinct(Expression, Func):\n    arg_types = {\"this\": True, \"check_null\": False, \"nulls_excluded\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/array.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,", "new_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(this=seq_get(args, 0), nulls_excluded=True),\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now the Snowflake generator: `List` → `ARRAY_AGG` (with the FILTER path routed through the same aggregate, since `List` isn't an `AggFunc` and currently crashes there), and `ArrayDistinct` with `nulls_excluded` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this\n\n        # If an ORDER BY clause is present", "new_string": "    def list_sql(self, expression: exp.List) -> s
…[395 chars elided]…
)\n\n    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        if expression.args.get(\"nulls_excluded\"):\n            arr = exp.ArrayCompact(this=arr)\n        return self.func(\"ARRAY_DISTINCT\", arr)\n\n    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this\n\n        # If an ORDER BY clause is present"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nqs=['SELECT list(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(x) FILTER(WHERE x IS NOT NULL) FROM t','SELECT list(x) OVER (PARTITION BY g) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct([1, NULL, 1]) AS a FROM t','SELEC
…[266 chars elided]…
 FROM t',read='snowflake',write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t',read='spark',write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAYDISTINCT(x) FROM t',read='clickhouse',write='snowflake'))\nprint(sqlglot.transpile('SELECT list_distinct(x) FROM t',read='duckdb',write='spark'))\n\"", "description": "Probe new DuckDB\u2192Snowflake and regression outputs"}
[tool_result] SELECT list(x) FROM t => SF: SELECT ARRAY_AGG(x) FROM t | DDB: SELECT LIST(x) FROM t
SELECT list(DISTINCT x) FROM t => SF: SELECT ARRAY_AGG(DISTINCT x) FROM t | DDB: SELECT LIST(DISTINCT x) FROM t
SELECT list(x ORDER BY y) FROM t => SF: SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t | DDB: SELECT LIST(x ORDER BY y) FROM t
SELECT list(x) FILTER(WHERE x IS NOT NULL) FROM t => SF: SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t | DDB: SELECT LIST(x) FILTER(WHERE NOT x IS NULL) FROM t
SEL
…[289 chars elided]…
ct([1, NULL, 1]) AS a FROM t => SF: SELECT ARRAY_DISTINCT(ARRAY_COMPACT([1, NULL, 1])) AS a FROM t | DDB: SELECT LIST_DISTINCT([1, NULL, 1]) AS a FROM t
SELECT ARRAY_DISTINCT(x) FROM t => SF: SELECT ARRAY_DISTINCT(x) FROM t | DDB: SELECT LIST_DISTINCT(x) FROM t
SELECT ARRAY_AGG(x) FROM t => SF: SELECT ARRAY_AGG(x) FROM t | DDB: SELECT ARRAY_AGG(x) FROM t
['SELECT ARRAY_DISTINCT(x) FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
[assistant] The core mappings work, but the FILTER output is semantically lossy: `ARRAY_AGG(IFF(c, x, NULL))` keeps NULL placeholders from filtered-out rows, which DuckDB's `list(x) FILTER(...)` does not. I can't verify a Snowflake-exact FILTER form here, so I'll keep the translation but flag it with `unsupported()` instead of silently emitting it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "        if isinstance(expression.this, exp.List):\n            agg = exp.ArrayAgg(this=expression.this.expressions[0])", "new_string": "        if isinstance(expression.this, exp.List):\n            self.unsupported(\"LIST ... FILTER is not exact: filtered-out rows contribute NULLs\")\n            agg = exp.ArrayAgg(this=expression.this.expressions[0])"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now tests. I'll add them to the DuckDB dialect test file, next to the existing `LIST(DISTINCT ...) FILTER` case.
[tool_use Bash] {"command": "sed -n 680,700p tests/dialects/test_duckdb.py", "description": "View existing LIST FILTER test context"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table\",\n            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample
…[483 chars elided]…
ORDER BY sort_col)\",\n            read={\"snowflake\": \"SELECT LIST(col ORDER BY sort_col)\"},\n        )\n        self.validate_all(\n            \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            read={\"duckdb\": \"SELECT LIST_DISTINCT(x)\"},\n        )\n        self.validate_all(\n            \"SELECT ARRAY_AGG(col)\",\n            read={\"duckdb\": \"SELECT LIST(col)\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I wrote those four cases with `read=`, which is backwards for DuckDB-source → Snowflake-target. Fixing them to use `write=`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT ARRAY_AGG(col)\",\n            read={\"snowflake\": \"SELECT LIST(col)\"},\n        )\n        self.validate_all(\n            \"SELECT ARRAY_AGG(col) WITHIN 
…[601 chars elided]…
"SELECT LIST(col ORDER BY sort_col)\",\n            write={\"snowflake\": \"SELECT ARRAY_AGG(col) WITHIN GROUP (ORDER BY sort_col)\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x)\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x)\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-180052-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the full test suite using the project's configured command, plus a lint check.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
....................................................................................................................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
.........
…[319 chars elided]…
................................................................................................... [ 76%]
............................................. [ 80%]
................................ [ 83%]
................ [ 85%]
....................................... [ 88%]
..........................................................................................................................                                                        [100%]
1092 passed, 17861 subtests passed in 45.35s
[assistant] All 1092 tests pass. Running the linter/formatter on the changed files:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff --version && $PY/ruff check sqlglot/expressions/array.py sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && $PY/ruff format --check sqlglot/expressions/array.py sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py) 2>&1 | tail -15; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
sqlglot/expressions/array.py    |  2 +-
 sqlglot/generators/snowflake.py | 16 ++++++++++++++++
 sqlglot/parsers/duckdb.py       |  1 +
 tests/dialects/test_duckdb.py   | 15 +++++++++++++++
 4 files changed, 33 insertions(+), 1 deletion(-)
[assistant] DuckDB → Snowflake now translates `list(col)` and `list_distinct(col)`. The full suite passes (1092 tests) and ruff is clean. I haven't committed.

**Mappings**
- `list(col)` → `ARRAY_AGG(col)`. `ORDER BY` inside `list()` becomes `WITHIN GROUP (ORDER BY ...)`, and `DISTINCT` carries through.
- `list_distinct(x)` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`. This keeps DuckDB's NULL-dropping, since Snowflake's `ARRAY_DISTINCT` keeps NULLs.

**Changes**
- `sqlglot/expressions/array.py`: `ArrayDistinct` gets a `nulls_excluded` flag.
- `sqlglot/parsers/duckdb.py`: `LIST_DISTINCT` parses to `ArrayDistinct(
…[1111 chars elided]…
ows, unlike DuckDB. I couldn't find a Snowflake form that is exact here, so the generator emits an `unsupported` warning. Plain `ARRAY_AGG` FILTER translation already has this same problem.

**Side effect to be aware of**
DuckDB `list_distinct` → other dialects (for example Spark) now emits `ARRAY_DISTINCT(x)` with no NULL compaction. Previously it emitted `LIST_DISTINCT(x)`, which those engines don't support anyway, so the output is still wrong for NULL-containing arrays, just differently.

I haven't run these against a live Snowflake; the NULL semantics come from the behaviour you described.
