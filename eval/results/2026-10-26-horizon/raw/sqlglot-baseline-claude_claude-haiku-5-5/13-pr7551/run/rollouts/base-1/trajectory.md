# trajectory base-1

final message:
DuckDB `list()` and `list_distinct()` now transpile to Snowflake as `ARRAY_AGG` and `ARRAY_DISTINCT(ARRAY_COMPACT(...))`. The full suite passes (1092 tests) and ruff is clean. The changes are uncommitted in the worktree.

- **`list(x)` → `ARRAY_AGG(x)`, `list(DISTINCT x)` → `ARRAY_AGG(DISTINCT x)`.** DuckDB parses `LIST` as `exp.List`, so I added a `list_sql` method to the Snowflake generator that emits `ARRAY_AGG` (`sqlglot/generators/snowflake.py`). NULLs are kept, which matches Snowflake's `ARRAY_AGG`.
- **`list_distinct(x)` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`.** The DuckDB parser now builds `ArrayDistinct(ArrayCompact(x))`, which makes the NULL-dropping explicit in the AST (`sqlglot/parsers/duckdb.py`). I did not use the `check_null` flag for this: Spark's `array_distinct` has no flag and keeps NULLs, so treating the default as NULL-dropping would have broken Spark→Snowflake.
- **DuckDB round-trip preserved.** `arraydistinct_sql` drops the redundant compaction when generating DuckDB, since `LIST_DISTINCT` already drops NULLs. `LIST_DISTINCT(x)` still round-trips as `LIST_DISTINCT(x)`.
- **Tests** added to `tests/dialects/test_duckdb.py`. I did not run them against real Snowflake or DuckDB.

**Not fixed:** `list(DISTINCT x) FILTER (WHERE ...)` still crashes when transpiled to Snowflake. `filter_sql` expects the aggregate to have a `this` argument, and `exp.List` only has `expressions`. Separately, `ARRAY_AGG(DISTINCT x) FILTER (...)` already produces invalid `IFF(..., DISTINCT x, NULL)` output. Both are in the generic FILTER path, so I left them alone. This is the most common DuckDB form of `list`, so it is worth a follow-up.

Another side effect: any Snowflake input that calls a user-defined function named `LIST(...)` will now be emitted as `ARRAY_AGG`, because the base parser maps `LIST` to `exp.List`.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"ListDistinct\\|ArrayDistinct\\|ARRAY_DISTINCT\\|LIST_DISTINCT\\|\\\"LIST\\\"\\|ArrayAgg\\b\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -60", "description": "Search for list/array distinct and agg mappings"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"ListDistinct\\|ArrayDistinct\\|ArrayUniqueAgg\\|ARRAY_DISTINCT\\|LIST_DISTINCT\\|ArrayAgg\\|\\\"LIST\\\"\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions* | head -60", "description": "Locate list/array distinct and agg mappings"}
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
sqlglot/expressions/aggregate.py:71:class ArrayAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py:83:class ArrayUniqueAgg(Expression, AggFunc):
sqlglot/expressions/json.py:21:class JSONArrayAgg(Expression, AggFunc):
sqlglot/expressions/array.py:138:class ArrayDistinct(Expression, Func):
[tool_use Bash] {"command": "grep -rn \"ArrayUniqueAgg\\|ArrayDistinct\\|ArrayAgg\\|ListDistinct\\|\\\"LIST\\\"\\|list_distinct\\|LIST_DISTINCT\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/generators/*.py sqlglot/parsers/*.py sqlglot/expressions/*.py | head -60; ls sqlglot/dialects | head -80", "description": "Search dialect and generator files for list/array mappings"}
[tool_result] sqlglot/generators/clickhouse.py:279:        exp.ArrayDistinct: rename_func("arrayDistinct"),
sqlglot/generators/dremio.py:59:        exp.DType.ARRAY: "LIST",
sqlglot/generators/materialize.py:39:            return "LIST"
sqlglot/generators/materialize.py:49:            return self.func("LIST", seq_get(expression.expressions, 0))
sqlglot/generators/mysql.py:140:        exp.ArrayAgg: rename_func("GROUP_CONCAT"),
sqlglot/generators/mysql.py:786:        return self._partition_by_sql(expression, "LI
…[4126 chars elided]…
ions/aggregate.py:71:class ArrayAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py:83:class ArrayUniqueAgg(Expression, AggFunc):
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
[tool_use Bash] {"command": "sed -n 3295,3325p sqlglot/generators/duckdb.py; echo ----; sed -n 405,425p sqlglot/parsers/snowflake.py; echo ----; grep -n \"ArrayDistinct\\|ARRAY_DISTINCT\\|ArrayUniqueAgg\\|ArrayAgg\\|arrayagg\" sqlglot/generators/snowflake.py; echo ----; grep -n \"\\\"LIST\\\"\\|LIST_DISTINCT\\|\\\"LIST\\\":\\|ArrayUniqueAgg\\|ARRAY_UNIQUE_AGG\\|ArrayAgg\" sqlglot/parsers/duckdb.py; echo ---; sed -n 135,150p sqlglot/expressions/array.py; sed -n 68,95p sqlglot/expressions/aggregate.py", "description": "Inspect DuckDB/Snowflake array distinct and agg code"}
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
…[2699 chars elided]…
):
    pass


class ArrayUniqueAgg(Expression, AggFunc):
    pass


class Avg(Expression, AggFunc):
    pass


class Corr(Expression, AggFunc, Binary):
    # Correlation divides by variance(column). If a column has 0 variance, the denominator
    # is 0 - some dialects return NaN (DuckDB) while others return NULL (Snowflake).
    # `null_on_zero_variance` is set to True at parse time for dialects that return NULL.
    arg_types = {"this": True, "expression": True, "null_on_zero_variance": False}
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT array_distinct(x) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb')\n    print(repr(e.selects[0]))\n    print(e.sql('snowflake'))\n    print(e.sql('duckdb'))\n\" 2>&1 | head -60; grep -n \"\\\"LIST\\|LIST_\\|ArrayUniqueAgg\\|ArrayAgg\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head -30", "description": "Reproduce current DuckDB to Snowflake output"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parsers/duckdb.py:136:        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
sqlglot/parsers/duckdb.py:137:        "LIST_CONCAT": parser.build_array_concat,
sqlglot/parsers/duckdb.py:138:        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
sqlglot/parsers/duckdb.py:139:        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
sqlglot/parsers/duckdb.py:140: 
…[510 chars elided]…
LIST_PREPEND": _build_array_prepend,
sqlglot/parsers/duckdb.py:147:        "LIST_REVERSE_SORT": _build_sort_array_desc,
sqlglot/parsers/duckdb.py:148:        "LIST_SORT": exp.SortArray.from_arg_list,
sqlglot/parsers/duckdb.py:149:        "LIST_TRANSFORM": exp.Transform.from_arg_list,
sqlglot/parsers/duckdb.py:150:        "LIST_VALUE": lambda args: exp.Array(expressions=args),
sqlglot/parsers/duckdb.py:187:            ("GROUP_CONCAT", "LISTAGG", "STRINGAGG"), lambda self: self._parse_string_agg()
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/ | head; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT array_distinct(x) FROM t', 'SELECT list(x) FILTER (WHERE x IS NOT NULL) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb')\n    print(repr(e.selects[0]))\n    print(e.sql('snowflake'))\n    print(e.sql('duckdb'))\n\" 2>&1 | head -80", "description": "Reproduce DuckDB to Snowflake output using project venv"}
[tool_result] activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
dmypy
f2py
Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
…[2676 chars elided]…
      this=Identifier(this=x, quoted=False))])])
SELECT LIST(DISTINCT x) FROM t
SELECT LIST(DISTINCT x) FROM t
ArrayDistinct(
  this=Column(
    this=Identifier(this=x, quoted=False)))
SELECT ARRAY_DISTINCT(x) FROM t
SELECT LIST_DISTINCT(x) FROM t
Filter(
  this=List(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False))]),
  expression=Where(
    this=Not(
      this=Is(
        this=Column(
          this=Identifier(this=x, quoted=False)),
        expression=Null()))))
[tool_use Bash] {"command": "grep -rn \"class List\\b\\|class List(\\|exp\\.List\\b\" sqlglot | head; grep -rn \"check_null\" sqlglot | grep -v \"^sqlglot/expressions/core\" | head -30; echo ----; sed -n 2990,3030p sqlglot/generators/duckdb.py; echo ----; grep -n \"def arrayagg_sql\" -A25 sqlglot/generators/snowflake.py | head -40; echo; grep -n \"ArrayCompact\\|arraycompact\" sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/*.py | head", "description": "Inspect List class, check_null usage, ArrayCompact handling"}
[tool_result] sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/expressions/array.py:34:class List(Expression, Func):
sqlglot/generators/materialize.py:47:    def list_sql(self, expression: exp.List) -> str:
sqlglot/parsers/snowflake.py:412:            check_null=True,
sqlglot/parsers/snowflake.py:416:            check_null=True,
sqlglot/expressions/datatypes.py:375:    def is_type(self, *dtypes: DATA_TYPE, check_nullable: bool = False) -> bool:
sqlglot/expressions/datatypes.py:382:            check_nul
…[4170 chars elided]…
CONSTRUCT('alias_foo', foo))
1060-            if first_expr.text("kind").upper() == "STRUCT":

sqlglot/generators/duckdb.py:1503:        exp.ArrayCompact: array_compact_sql,
sqlglot/generators/duckdb.py:1505:            exp.ArrayCompact(this=exp.Array(expressions=e.expressions))
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/parsers/clickhouse.py:256:        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
[tool_use Bash] {"command": "grep -n \"arrayagg\\|ArrayAgg\" sqlglot/generators/duckdb.py sqlglot/generator.py | head -20; sed -n 30,40p sqlglot/expressions/array.py; echo ----; grep -rn \"LIST(\\|list(\\|LIST_DISTINCT\\|list_distinct\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_materialize.py | head -60", "description": "Check DuckDB ArrayAgg handling and related tests"}
[tool_result] sqlglot/generators/duckdb.py:3001:        if isinstance(func, exp.ArrayAgg):
sqlglot/generators/duckdb.py:3009:            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
sqlglot/generators/duckdb.py:3021:            return self._add_arrayagg_null_filter(array_agg_sql, func, original_this)
sqlglot/generator.py:3583:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:5330:    def _add_arrayagg_null_filter(
sqlglot/genera
…[4243 chars elided]…
T([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
tests/dialects/test_snowflake.py:4925:        self.assertEqual(list(search_ast.args), ["this", "expression"])
tests/dialects/test_snowflake.py:4945:        self.assertEqual(list(search_ast.args), ["this", "expression", "search_mode", "analyzer"])
tests/dialects/test_snowflake.py:5848:        self.assertEqual(len(list(ast.find_all(exp.Column))), 1)
[tool_use Bash] {"command": "sed -n 1805,1835p sqlglot/generator.py; echo ----; sed -n 5325,5375p sqlglot/generator.py; echo ----; grep -n \"def array_compact_sql\" -A12 sqlglot/generators/duckdb.py; echo ---; git log --oneline -3 -- sqlglot/generators/duckdb.py | cat", "description": "Read filter and arrayagg generator logic"}
[tool_result]         count = f" {count}" if count else ""
        limit_options = self.sql(expression, "limit_options")
        limit_options = f"{limit_options}" if limit_options else " ROWS ONLY"
        return f"{self.seg('FETCH')}{direction}{count}{limit_options}"

    def limitoptions_sql(self, expression: exp.LimitOptions) -> str:
        percent = " PERCENT" if expression.args.get("percent") else ""
        rows = " ROWS" if expression.args.get("rows") else ""
        with_ties = " WITH TIES" if expre
…[2642 chars elided]…
gg) -> str:
        array_agg = self.function_fallback_sql(expression)
        return self._add_arrayagg_null_filter(array_agg, expression, expression.this)

    def slice_sql(self, expression: exp.Slice) -> str:
        step = self.sql(expression, "step")
----
---
b334dccb7 feat(duckdb)!: mark DECOMPRESS_BINARY as unsupported  (#7546)
8669e55f3 feat(duckdb)!: mark DECOMPRESS_STRING as unsupported [CLAUDE] (#7545)
ceb14fad0 feat(duckdb): Add transpilation unsupported for SOUNDEX function (#7517)
[tool_use Bash] {"command": "sed -n 3311,3335p sqlglot/generators/duckdb.py; echo ----; grep -n \"seq_get\" sqlglot/parsers/duckdb.py | head -3; grep -n \"def list_sql\\|def arraycompact\" sqlglot/generator.py sqlglot/generators/*.py | head; echo ----; sed -n 680,700p tests/dialects/test_duckdb.py; echo ----; sed -n 1032,1036p sqlglot/generators/snowflake.py; sed -n 1,30p sqlglot/generators/snowflake.py | grep -n import", "description": "Read relevant code sections and test context"}
[tool_result]     def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
        arr = expression.this
        func = self.func("LIST_DISTINCT", arr)

        if expression.args.get("check_null"):
            add_null_to_array = exp.func(
                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
            )
            return self.sql(
                exp.If(
                    this=exp.NEQ(
                        this=exp.ArraySize(this=arr), expression=
…[1951 chars elided]…
ateable_sql(expression, locations)

    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
        this = expression.this
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
27:from sqlglot.generator import unsupported_args
28:from sqlglot.helper import find_new_name, flatten, seq_get
29:from sqlglot.optimizer.scope import build_scope, find_all_in_scope
30:from sqlglot.parsers.snowflake import (
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -5", "description": "Run baseline DuckDB and Snowflake dialect tests"}
[tool_result] ...........................................................................................................................................        [100%]
139 passed, 2158 subtests passed in 0.67s
[assistant] Baseline is green. Now the three edits: the DuckDB parser for `LIST_DISTINCT`, a DuckDB generator unwrap so identity round-trips, and a Snowflake `list_sql` that emits `ARRAY_AGG`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_CONTAINS\": exp.ArrayContains.from_arg_list,\n        \"LIST_COSINE_DISTANCE\": exp.CosineDistance.from_arg_list,\n        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,", "new_string": "        \"LIST_CONTAINS\": exp.ArrayContains.from_arg_list,\n        \"LIST_COSINE_DISTANCE\": exp.CosineDistance.from_arg_list,\n        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(\n            this=exp.ArrayCompact(this=seq_get(args, 0))\n        ),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py", "old_string": "    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        func = self.func(\"LIST_DISTINCT\", arr)", "new_string": "    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        if isinstance(arr, exp.ArrayCompact) and not expression.args.get(\"check_null\"):\n            # LIST_DISTINCT already drops NULLs, so the compaction is redundant\n            arr = arr.this\n        func = self.func(\"LIST_DISTINCT\", arr)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this\n\n        # If an ORDER BY clause is present", "new_string": "    def list_sql(self, expression: exp.List) -> str:\n        return self.sql(exp.ArrayAgg(this=seq_get(expression.expressions, 0)))\n\n    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:\n        this = expression.this\n\n        # If an ORDER BY clause is present"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT list(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(DISTINCT x) FILTER(WHERE NOT x IS NULL) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct(list(x)) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb')\n    print(e.sql('snowflake'), '|', e.sql('duckdb'), '|', e.sql('spark'))\n\" 2>&1 | tail -20", "description": "Check DuckDB to Snowflake output after changes"}
[tool_result]     return _sql_handler(expression)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", line 1011, in select_sql
    return super().select_sql(expression)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 3077, in select_sql
   
…[550 chars elided]…
^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1827, in filter_sql
    agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
    ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'replace'
SELECT ARRAY_AGG(x) FROM t | SELECT LIST(x) FROM t | SELECT LIST(x) FROM t
SELECT ARRAY_AGG(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT ARRAY_AGG(DISTINCT x) FILTER(WHERE NOT x IS NULL) FROM t','SELECT ARRAY_AGG(x) FILTER(WHERE y > 1) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb')\n    print(e.sql('snowflake'))\nprint(sqlglot.dialects.Dialect.get_or_raise('snowflake').generator_class.AGGREGATE_FILTER_SUPPORTED)\n\" 2>&1 | tail -5; grep -n \"AGGREGATE_FILTER_SUPPORTED\" sqlglot/generators/*.py sqlglot/generator.py | head", "description": "Check FILTER handling for ArrayAgg in Snowflake"}
[tool_result] SELECT ARRAY_AGG(IFF(NOT x IS NULL, DISTINCT x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(y > 1, x, NULL)) FROM t
False
sqlglot/generators/snowflake.py:383:    AGGREGATE_FILTER_SUPPORTED = False
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT list(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct(list(x)) FROM t','SELECT LIST_DISTINCT([1, NULL, 1]) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb')\n    print(e.sql('snowflake'), '|', e.sql('duckdb'), '|', e.sql('spark'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t', read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x) FROM t', read='spark', write='snowflake'))\n\" 2>&1 | tail -12", "description": "Verify transpilation outputs for list and list_distinct"}
[tool_result] SELECT ARRAY_AGG(x) FROM t | SELECT LIST(x) FROM t | SELECT LIST(x) FROM t
SELECT ARRAY_AGG(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t | SELECT LIST_DISTINCT(x) FROM t | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY_AGG(x))) FROM t | SELECT LIST_DISTINCT(LIST(x)) FROM t | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(LIST(x))) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT([1, NULL, 1])) FROM t | SELECT LIST_DISTINCT([1, NULL, 1]) FROM t | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY(1, NULL, 1))) FROM t
['SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END FROM t']
['SELECT ARRAY_DISTINCT(x) FROM t']
[assistant] Transpilation output is right. Now I'll add regression tests next to the existing `LIST(DISTINCT ...)` case in the DuckDB tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table\",\n            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample
…[329 chars elided]…
ST(DISTINCT x)\",\n            write={\n                \"snowflake\": \"SELECT ARRAY_AGG(x), ARRAY_AGG(DISTINCT x)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x)\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x)\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-140230-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $P -m ruff check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -3; $P -m ruff format --check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Run full test suite and lint checks"}
[tool_result] .... [ 32%]
........................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
................. [ 42%]
........................................................................................................... [ 52%]
................................................................................................................................................................... [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
................................ [ 83%]
....................................................... [ 88%]
.................................................................. [ 94%]
............................................ [ 98%]
...........                                                         [100%]
1092 passed, 17860 subtests passed in 53.32s
All checks passed!
175 files already formatted
[tool_use Bash] {"command": "git diff --stat", "description": "Show changed files summary"}
[tool_result]  sqlglot/generators/duckdb.py    |  3 +++
 sqlglot/generators/snowflake.py |  3 +++
 sqlglot/parsers/duckdb.py       |  3 +++
 tests/dialects/test_duckdb.py   | 13 +++++++++++++
 4 files changed, 22 insertions(+)
[assistant] DuckDB `list()` and `list_distinct()` now transpile to Snowflake as `ARRAY_AGG` and `ARRAY_DISTINCT(ARRAY_COMPACT(...))`. The full suite passes (1092 tests) and ruff is clean. The changes are uncommitted in the worktree.

- **`list(x)` → `ARRAY_AGG(x)`, `list(DISTINCT x)` → `ARRAY_AGG(DISTINCT x)`.** DuckDB parses `LIST` as `exp.List`, so I added a `list_sql` method to the Snowflake generator that emits `ARRAY_AGG` (`sqlglot/generators/snowflake.py`). NULLs are kept, which matches Snowflake's `ARRAY_AGG`.
- **`list_distinct(x)` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`.** The DuckDB parser now buil
…[639 chars elided]…
TINCT x) FILTER (WHERE ...)` still crashes when transpiled to Snowflake. `filter_sql` expects the aggregate to have a `this` argument, and `exp.List` only has `expressions`. Separately, `ARRAY_AGG(DISTINCT x) FILTER (...)` already produces invalid `IFF(..., DISTINCT x, NULL)` output. Both are in the generic FILTER path, so I left them alone. This is the most common DuckDB form of `list`, so it is worth a follow-up.

Another side effect: any Snowflake input that calls a user-defined function named `LIST(...)` will now be emitted as `ARRAY_AGG`, because the base parser maps `LIST` to `exp.List`.
