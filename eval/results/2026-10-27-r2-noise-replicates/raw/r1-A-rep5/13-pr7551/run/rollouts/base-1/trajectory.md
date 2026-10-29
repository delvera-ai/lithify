# trajectory base-1

final message:
DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG`, and `list_distinct(col)` to `ARRAY_DISTINCT(ARRAY_COMPACT(col))`. The full suite passes (1092 tests) and ruff is clean. Nothing is committed.

**Changes**
- **`sqlglot/parsers/duckdb.py`**: `LIST_DISTINCT` now parses to `ArrayDistinct(ArrayCompact(x))`. That encodes "drop NULLs, then dedupe" directly, so Snowflake's NULL-keeping `ARRAY_DISTINCT` can't leak NULLs back in.
- **`sqlglot/generators/duckdb.py`**: `arraydistinct_sql` drops the redundant `ARRAY_COMPACT` wrapper when emitting DuckDB, so DuckDB→DuckDB stays `LIST_DISTINCT(x)`.
- **`sqlglot/generators/snowflake.py`**:
  - `list_sql` emits `ARRAY_AGG` for a single argument, so `DISTINCT` and `ORDER BY` inside `list(...)` carry through.
  - `filter_sql` is overridden because the generic `FILTER` → `IFF` rewrite crashed on `list(x) FILTER(WHERE ...)`. That crash was already there before my change.
- **`tests/dialects/test_duckdb.py`**: added cases for `list`, `list ... FILTER`, and `list_distinct`.

**Known issue: Materialize array literals**
`LIST[1]` in Materialize also parses to `exp.List`, so it now becomes `ARRAY_AGG(1)` on Snowflake. Before, it produced `LIST(1)`, which Snowflake rejects, so both outputs are wrong. The new one is silently wrong. A real fix needs `list()` from DuckDB and Materialize's `LIST[...]` to parse to different nodes, which touches the Materialize parser. I left that alone; say if you want it.

**Not verified**
I didn't run the generated SQL against real DuckDB or Snowflake. The CLAUDE.md rule about executing tests in the target databases still applies.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"list_distinct\\|ListDistinct\\|\\\"LIST\\\"\\|exp.ArrayAgg\\|ArrayUniqueAgg\\|ARRAY_DISTINCT\\|ArrayDistinct\\|ArrayUniq\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Check status and grep relevant functions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && git status --short | head && grep -rn -i \"list_distinct\\|ListDistinct\\|\\\"LIST\\\"\\|ArrayUniqueAgg\\|ArrayDistinct\\|ARRAY_UNIQUE_AGG\\|ArrayAgg\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py 2>/dev/null | head -80", "description": "List repo root and grep relevant functions"}
[tool_result] AGENTS.md
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
[tool_use Bash] {"command": "ls sqlglot | head -50; ls sqlglot/dialects | head -60; grep -rn -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayDistinct\\|ArrayAgg\\b\" sqlglot/ --include=*.py | head -60", "description": "Inspect sqlglot package layout and grep"}
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
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayDistinct\\|ArrayAgg\\b\\|\\\"LIST\\\"\" sqlglot/ | head -80", "description": "Grep for list and array distinct related names"}
[tool_result] sqlglot/tokens.py:450:        "LIST": TokenType.LIST,
sqlglot/generator.py:3583:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:3592:            "JSON_ARRAYAGG",
sqlglot/generator.py:5333:        array_agg_expr: exp.ArrayAgg,
sqlglot/generator.py:5341:            array_agg_expr: The ArrayAgg expression node
sqlglot/generator.py:5370:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
sqlglot/parser.py:323:        "ARRAYAGG": lambda args, dialect
…[5365 chars elided]…
f.func("LIST_DISTINCT", arr)
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/generators/presto.py:278:        exp.ArrayUniqueAgg: rename_func("SET_AGG"),
sqlglot/generators/mysql.py:140:        exp.ArrayAgg: rename_func("GROUP_CONCAT"),
sqlglot/generators/mysql.py:786:        return self._partition_by_sql(expression, "LIST")
sqlglot/generators/starrocks.py:91:        exp.ArrayAgg: rename_func("ARRAY_AGG"),
[tool_use Bash] {"command": "sed -n 3290,3325p sqlglot/generators/duckdb.py; echo ----; grep -n -i \"ArrayDistinct\\|ArrayCompact\\|ArrayUniqueAgg\\|ArrayAgg\\|\\\"LIST\\|LIST_DISTINCT\\|\\\"ARRAY_DISTINCT\\|ARRAY_COMPACT\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py; echo ----; sed -n 60,100p sqlglot/expressions/aggregate.py; sed -n 130,150p sqlglot/expressions/array.py", "description": "Read DuckDB/Snowflake relevant code sections"}
[tool_result]         expr = expression.this
        result = exp.replace_placeholders(self.MINHASH_COMBINE_TEMPLATE.copy(), expr=expr)
        return f"({self.sql(result)})"

    def approximatesimilarity_sql(self, expression: exp.ApproximateSimilarity) -> str:
        expr = expression.this
        result = exp.replace_placeholders(self.APPROXIMATE_SIMILARITY_TEMPLATE.copy(), expr=expr)
        return f"({self.sql(result)})"

    def arrayuniqueagg_sql(self, expression: exp.ArrayUniqueAgg) -> str:
        r
…[4364 chars elided]…
arg_types = {"this": False, "expressions": False, "big_int": False}
    is_var_len_args = True

class ArrayPosition(Expression, Binary, Func):
    arg_types = {"this": True, "expression": True, "zero_based": False}


# Array properties


class ArrayDistinct(Expression, Func):
    arg_types = {"this": True, "check_null": False}


class ArrayFirst(Expression, Func):
    arg_types = {"this": True, "expression": False}


class ArrayLast(Expression, Func):
    pass


class ArrayMax(Expression, Func):
[tool_use Bash] {"command": "sed -n 410,420p sqlglot/parsers/snowflake.py; grep -n \"list_distinct\\|LIST_DISTINCT\\|ArrayCompact\\|check_null\" sqlglot/parsers/*.py sqlglot/parser.py sqlglot/dialects/*.py sqlglot/generators/*.py | head -30; grep -n \"class ArrayCompact\" -A3 sqlglot/expressions/array.py; ls <work>/env-sqlglot/bin/python && PYTHONPATH=. ~/.
…[166 chars elided]…
nct(x) FROM t GROUP BY 1']:\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'))\nprint(repr(sqlglot.parse_one('SELECT list_distinct(x)', read='duckdb')))\nprint(repr(sqlglot.parse_one('SELECT list(x)', read='duckdb')))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x)', read='snowflake', write='duckdb'))\n\"", "description": "Inspect parser mappings and test current transpilation"}
[tool_result]             expression=seq_get(args, 0),
            ensure_variant=False,
            check_null=True,
        ),
        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
            this=seq_get(args, 0),
            check_null=True,
        ),
        "ARRAY_GENERATE_RANGE": lambda args: exp.GenerateSeries(
            # Snowflake has exclusive end semantics
            start=seq_get(args, 0),
sqlglot/parsers/clickhouse.py:256:        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
sqlglot/p
…[2068 chars elided]…
_DISTINCT(x) FROM t']
['SELECT LIST_DISTINCT(x) FROM t GROUP BY 1']
Select(
  expressions=[
    Anonymous(
      this=list_distinct,
      expressions=[
        Column(
          this=Identifier(this=x, quoted=False))])])
Select(
  expressions=[
    List(
      expressions=[
        Column(
          this=Identifier(this=x, quoted=False))])])
['SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END']
[tool_use Bash] {"command": "sed -n 2995,3015p sqlglot/generators/duckdb.py; grep -n \"class List\\b\" -A4 sqlglot/expressions/*.py; grep -rn \"LIST_DISTINCT\\|list_distinct\" tests/ | head -30; grep -rn \"\\\"LIST\\\"\\|'LIST'\\|list(\" tests/dialects/test_duckdb.py | head -20", "description": "Check DuckDB arrayagg, List class, and tests"}
[tool_result]     def withingroup_sql(self, expression: exp.WithinGroup) -> str:
        func = expression.this

        # For ARRAY_AGG, DuckDB requires ORDER BY inside the function, not in WITHIN GROUP
        # Transform: ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) -> ARRAY_AGG(x ORDER BY y)
        if isinstance(func, exp.ArrayAgg):
            if not isinstance(order := expression.expression, exp.Order):
                return self.sql(func)

            # Save the original column for FILTER clause (before wr
…[2601 chars elided]…
ts/test_snowflake.py:3121:                "duckdb": "SELECT CASE WHEN ARRAY_LENGTH([1, 2, 2, 3, 1]) <> LIST_COUNT([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
tests/dialects/test_dialect.py:1770:                "duckdb": "SELECT CASE WHEN [1, 2, 3] IS NULL OR [2] IS NULL THEN NULL ELSE LIST_FILTER(LIST_DISTINCT([1, 2, 3]), e -> LENGTH(LIST_FILTER([2], x -> x IS NOT DISTINCT FROM e)) = 0) END",
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT ARRAY_AGG(x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(DISTINCT x) FROM t']:\n    print(sqlglot.transpile(s, read='duckdb', write='duckdb'), sqlglot.transpile(s, read='duckdb', write='snowflake'))\nprint(sqlglot.
…[39 chars elided]…
 read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FROM t', read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FROM t', read='snowflake', write='duckdb'))\n\"; grep -rn \"LIST(\" tests/dialects/test_duckdb.py | head -30; grep -rn \"exp.List\\b\\|exp\\.List(\" sqlglot | head", "description": "Probe current DuckDB list aggregate behavior"}
[tool_result] ['SELECT ARRAY_AGG(x) FROM t'] ['SELECT ARRAY_AGG(x) FROM t']
['SELECT LIST(x ORDER BY y) FROM t'] ['SELECT LIST(x ORDER BY y) FROM t']
['SELECT LIST(DISTINCT x) FROM t'] ['SELECT LIST(DISTINCT x) FROM t']
['SELECT ARRAY_AGG(x) FILTER(WHERE x IS NOT NULL) FROM t']
['SELECT ARRAY_AGG(x) FILTER(WHERE x IS NOT NULL) FROM t']
['SELECT ARRAY_AGG(x) FILTER(WHERE x IS NOT NULL) FROM t']
tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/generators/materialize.py:47:    def list_sql(self, expression: exp.List) -> str:
[tool_use Bash] {"command": "sed -n 30,52p sqlglot/generators/materialize.py; sed -n 1030,1080p sqlglot/generators/snowflake.py; grep -n \"List\\b\" sqlglot/parsers/materialize.py sqlglot/dialects/materialize.py 2>/dev/null | head; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in ['SELECT LIST(x) FROM t','SELECT LIST(x ORDER BY y) FROM t','SELECT LIST(DISTINCT x) FILTER(WHERE x IS NOT NULL) FROM t','SELECT LIST(x) FILTER(WHERE x > 1) FROM t']:\n    e=sqlglot.parse_one(s,read='duckdb'); print(repr(e.selects[0]))\n\"", "description": "Inspect Materialize List use and Snowflake arrayagg"}
[tool_result]     }

    def propertyeq_sql(self, expression: exp.PropertyEQ) -> str:
        return self.binary(expression, "=>")

    def datatype_sql(self, expression: exp.DataType) -> str:
        if expression.is_type(exp.DType.LIST):
            if expression.expressions:
                return f"{self.expressions(expression, flat=True)} LIST"
            return "LIST"

        if expression.is_type(exp.DType.MAP) and len(expression.expressions) == 2:
            key, value = expression.expressions
    
…[2881 chars elided]…
       expressions=[
          Column(
            this=Identifier(this=x, quoted=False))])]),
  expression=Where(
    this=Not(
      this=Is(
        this=Column(
          this=Identifier(this=x, quoted=False)),
        expression=Null()))))
Filter(
  this=List(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False))]),
  expression=Where(
    this=GT(
      this=Column(
        this=Identifier(this=x, quoted=False)),
      expression=Literal(this=1, is_string=False))))
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor d,s in [('materialize','SELECT LIST[1]'),('materialize','SELECT LIST[1,2]'),('materialize','SELECT LIST(SELECT 1)'),('duckdb','SELECT LIST(x) FROM t')]:\n    e=sqlglot.parse_one(s,read=d); print(d, type(e.selects[0]).__name__, e.selects[0].sql(d))\n\"; grep -rn \"LIST\\[\" tests/dialects/test_materialize.py | head -5; grep -rn \"ArrayAgg\" sqlglot/generators/duckdb.py | head", "description": "Check Materialize LIST parse and DuckDB ArrayAgg refs"}
[tool_result] materialize List LIST[1]
materialize List LIST[1, 2]
materialize List LIST(SELECT 1)
duckdb List LIST(x)
tests/dialects/test_materialize.py:63:        self.validate_identity("SELECT LIST[]")
tests/dialects/test_materialize.py:64:        self.validate_identity("SELECT LIST[1, 2, 3]")
tests/dialects/test_materialize.py:65:        self.validate_identity("SELECT LIST[LIST[1], LIST[2], NULL]")
tests/dialects/test_materialize.py:66:        self.validate_identity("SELECT CAST(LIST[1, 2, 3] AS INT LIST)")
sqlglot/generators/duckdb.py:3001:        if isinstance(func, exp.ArrayAgg):
sqlglot/generators/duckdb.py:3009:            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/duckdb.py; grep -n \"def _build_array_prepend\" -A8 sqlglot/parsers/duckdb.py; sed -n 120,136p sqlglot/parsers/duckdb.py; sed -n 3311,3330p sqlglot/generators/duckdb.py; grep -n \"def function_fallback_sql\" sqlglot/generator.py; grep -n \"snowflake\\\": \\\"SELECT ARRAY_AGG\\|write={\\\"snowflake\\\"\" tests/dialects/test_duckdb.py | head -5; grep -n \"def test_duckdb\" tests/dialects/test_duckdb.py | head -3", "description": "Read parser builder and test conventions"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_default_decimal_type,
    build_formatted_time,
    build_regexp_extract,
    date_trunc_to_time,
    pivot_column_names,
)
from sqlglot.helper import seq_get
from sqlglot.parser import binary_range_parser
from sqlglot.tokens import TokenType
from collections.abc import Collection


25:def _build_array
…[1657 chars elided]…
T_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
            )
            return self.sql(
                exp.If(
                    this=exp.NEQ(
                        this=exp.ArraySize(this=arr), expression=exp.func("LIST_COUNT", arr)
                    ),
                    true=add_null_to_array,
                    false=func,
                )
            )

        return func

4312:    def function_fallback_sql(self, expression: exp.Func) -> str:
13:    def test_duckdb(self):
[assistant] Current behavior confirmed: DuckDB `list(x)` parses to the shared `exp.List` node, and `list_distinct(x)` stays an `Anonymous` call. I'll make the changes in three places: the DuckDB parser maps `list_distinct` to `ArrayDistinct(ArrayCompact(x))`, the DuckDB generator unwraps that compact for DuckDB output, and the Snowflake generator emits `ARRAY_AGG` for a single-argument `List`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_APPEND\": exp.ArrayAppend.from_arg_list,\n", "new_string": "        \"LIST_APPEND\": exp.ArrayAppend.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(\n            this=exp.ArrayCompact(this=seq_get(args, 0))\n        ),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py", "old_string": "    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        func = self.func(\"LIST_DISTINCT\", arr)\n\n        if expression.args.get(\"check_null\"):", "ne
…[26 chars elided]…
istinct_sql(self, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n        if isinstance(arr, exp.ArrayCompact) and not expression.args.get(\"check_null\"):\n            # LIST_DISTINCT already drops NULLs, so the ArrayCompact wrapper is redundant\n            arr = arr.this\n        func = self.func(\"LIST_DISTINCT\", arr)\n\n        if expression.args.get(\"check_null\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:", "new_string": "    def list_sql(self, expression: exp.List) -> str:\n        if len(expression.expressions) == 1:\n            return self.sql(exp.ArrayAgg(this=expression.expressions[0]))\n\n        return self.function_fallback_sql(expression)\n\n    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\ncases=['SELECT list(x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x) FILTER(WHERE x > 1) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct(list_filter(x, y -> y > 1)) FROM t','SELECT list(x) FROM t GROUP BY 1']\nfor s in cases:\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake')[0], '|', sqlglot.transpile(s, read='duckdb', write='duckdb')[0])\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x)', read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT LIST(x)', read='materialize', write='snowflake'))\n\"", "description": "Verify new transpilation outputs"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 5, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/__init__.py", line 211, in transpile
    write.generate(expression, copy=False, **opts) if expression else ""
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/dia
…[1878 chars elided]…
an/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", line 1827, in filter_sql
    agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
    ^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'replace'
SELECT ARRAY_AGG(x) FROM t | SELECT LIST(x) FROM t
SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t | SELECT LIST(x ORDER BY y) FROM t
SELECT ARRAY_AGG(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t
[tool_use Bash] {"command": "sed -n 1808,1835p sqlglot/generator.py", "description": "Read Snowflake filter_sql fallback logic"}
[tool_result]         return f"{self.seg('FETCH')}{direction}{count}{limit_options}"

    def limitoptions_sql(self, expression: exp.LimitOptions) -> str:
        percent = " PERCENT" if expression.args.get("percent") else ""
        rows = " ROWS" if expression.args.get("rows") else ""
        with_ties = " WITH TIES" if expression.args.get("with_ties") else ""
        if not with_ties and rows:
            with_ties = " ONLY"
        return f"{percent}{rows}{with_ties}"

    def filter_sql(self, expression:
…[176 chars elided]…
            return f"{this} FILTER({where})"

        agg = expression.this
        agg_arg = agg.this
        cond = expression.expression.this
        agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
        return self.sql(agg)

    def hint_sql(self, expression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"
[assistant] The `FILTER` case crashes on Snowflake: the generic filter rewrite expects an aggregate with `.this`, and `List` stores its args in `.expressions`. This path was already broken before my change for any `List` under `FILTER`, but `list(x) FILTER(...)` is a common DuckDB form, so I'll handle it in the Snowflake generator too.
[tool_use Bash] {"command": "grep -n \"def filter_sql\\|AGGREGATE_FILTER_SUPPORTED\" sqlglot/generators/snowflake.py sqlglot/generator.py | head", "description": "Check existing Snowflake filter handling"}
[tool_result] sqlglot/generators/snowflake.py:383:    AGGREGATE_FILTER_SUPPORTED = False
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1818:    def filter_sql(self, expression: exp.Filter) -> str:
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def list_sql(self, expression: exp.List) -> str:\n        if len(expression.expressions) == 1:\n            return self.sql(exp.ArrayAgg(this=expression.expressions[0]))\n\n        return self.function
…[165 chars elided]…
elf.sql(exp.ArrayAgg(this=expression.expressions[0]))\n\n        return self.function_fallback_sql(expression)\n\n    def filter_sql(self, expression: exp.Filter) -> str:\n        agg = expression.this\n        if isinstance(agg, exp.List) and len(agg.expressions) == 1:\n            expression.set(\"this\", exp.ArrayAgg(this=agg.expressions[0]))\n\n        return super().filter_sql(expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\ncases=['SELECT list(x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x) FILTER(WHERE x > 1) FROM t','SELECT list_distinct(x) FROM t','SELECT list_distinct(list_filter(x, y -> y > 1)) FROM t','SELECT list(x) FROM t GROUP BY 1']
…[58 chars elided]…
ckdb', write='snowflake')[0], '|', sqlglot.transpile(s, read='duckdb', write='duckdb')[0])\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(x)', read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT LIST(x)', read='materialize', write='snowflake'))\nprint(sqlglot.transpile('SELECT list_distinct(x)', read='duckdb', write='spark'))\n\"", "description": "Re-verify transpilation outputs"}
[tool_result] SELECT ARRAY_AGG(x) FROM t | SELECT LIST(x) FROM t
SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t | SELECT LIST(x ORDER BY y) FROM t
SELECT ARRAY_AGG(DISTINCT x) FROM t | SELECT LIST(DISTINCT x) FROM t
SELECT ARRAY_AGG(IFF(x > 1, x, NULL)) FROM t | SELECT LIST(x) FILTER(WHERE x > 1) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t | SELECT LIST_DISTINCT(x) FROM t
SELECT ARRAY_DISTINCT(ARRAY_COMPACT(FILTER(x, y -> y > 1))) FROM t | SELECT LIST_DISTINCT(LIST_FILTER(x, y -> y > 1)) FROM t
SELECT ARRAY_AGG(x) FROM t GROUP BY 1 | SELECT LIST(x) FROM t GROUP BY 1
['SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END']
['SELECT ARRAY_AGG(x)']
['SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))']
[assistant] Results look right for DuckDB sources. One caveat I need to report: Materialize's array literal `LIST[...]` also parses to `exp.List`, so it now gets the same `ARRAY_AGG` mapping when written to Snowflake. I'll confirm that below. Next I'll add tests and run the suite.
[tool_use Bash] {"command": "grep -n \"\\\"snowflake\\\": \\\"\" tests/dialects/test_duckdb.py | head -5; grep -n \"def test_\" tests/dialects/test_duckdb.py | head -40; sed -n 680,700p tests/dialects/test_duckdb.py; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot; print(sqlglot.transpile('SELECT LIST[1]', read='materialize', write='snowflake'))\"", "description": "Find test conventions and check Materialize caveat"}
[tool_result] 99:                "snowflake": "SELECT APPROX_TOP_K(category, 3) FROM t",
108:                "snowflake": """SELECT TRY_PARSE_JSON('{"x: 1}')""",
123:                "snowflake": "OBJECT_CONSTRUCT('a b', 1)",
139:                "snowflake": "ARRAY_TO_STRING(arr, delim)",
147:                "snowflake": "SELECT ARRAY_TO_STRING(arr, delim)",
13:    def test_duckdb(self):
1589:    def test_array_index(self):
1629:    def test_array_insert(self):
1670:    def test_array_remove(self):
1695:    de
…[2057 chars elided]…
sample_table",
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
['SELECT ARRAY_AGG(1)']
[assistant] The Materialize collision is confirmed (`LIST[1]` → `ARRAY_AGG(1)`), so I'll report it rather than hide it. Now I'll add DuckDB→Snowflake tests next to the existing `LIST` test.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "offset": 686, "limit": 8}
[tool_result] 686	        self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
687	        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
688	        self.validate_all("SELECT * FROM 'x.y'", write={"duckdb": 'SELECT * FROM "x.y"'})
689	        self.validate_all(
690	            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
691	            read={"spark": "SELECT COLLECT_SET(sample_col) FROM sample_table"},
692	        )
693	        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample_table\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x
…[443 chars elided]…
     )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x) FROM t\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-094147-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
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
…[329 chars elided]…
......................................................................................... [ 76%]
............................................. [ 80%]
................................ [ 83%]
................ [ 85%]
....................................... [ 88%]
..........................................................................................................................                                                        [100%]
1092 passed, 17861 subtests passed in 61.70s (0:01:01)
[assistant] All 1092 tests pass. I'll run the linter and formatter on the changed files too.
[tool_use Bash] {"command": "F=\"sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py\"; <work>/env-sqlglot/bin/python -m ruff check $F 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check $F 2>&1 | tail -5; git status --short; git diff --stat", "description": "Run ruff lint and format checks on changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
error: Failed to format sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
 M sqlglot/generators/duckdb.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generators/duckdb.py    |  3 +++
 sqlglot/generators/snowflake.py | 13 +++++++++++++
 sqlglot/parsers/duckdb.py       |  3 +++
 tests/dialects/test_duckdb.py   | 15 +++++++++++++++
 4 files changed, 34 insertions(+)
[assistant] The shell is zsh, so the unquoted variable didn't split. Rerunning with explicit paths.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Run ruff lint and format on changed files"}
[tool_result] All checks passed!
4 files already formatted
[assistant] DuckDB `list(col)` now transpiles to Snowflake `ARRAY_AGG`, and `list_distinct(col)` to `ARRAY_DISTINCT(ARRAY_COMPACT(col))`. The full suite passes (1092 tests) and ruff is clean. Nothing is committed.

**Changes**
- **`sqlglot/parsers/duckdb.py`**: `LIST_DISTINCT` now parses to `ArrayDistinct(ArrayCompact(x))`. That encodes "drop NULLs, then dedupe" directly, so Snowflake's NULL-keeping `ARRAY_DISTINCT` can't leak NULLs back in.
- **`sqlglot/generators/duckdb.py`**: `arraydistinct_sql` drops the redundant `ARRAY_COMPACT` wrapper when emitting DuckDB, so DuckDB→DuckDB stays `LIST_DISTINCT(x)`.
…[421 chars elided]…
nct`.

**Known issue: Materialize array literals**
`LIST[1]` in Materialize also parses to `exp.List`, so it now becomes `ARRAY_AGG(1)` on Snowflake. Before, it produced `LIST(1)`, which Snowflake rejects, so both outputs are wrong. The new one is silently wrong. A real fix needs `list()` from DuckDB and Materialize's `LIST[...]` to parse to different nodes, which touches the Materialize parser. I left that alone; say if you want it.

**Not verified**
I didn't run the generated SQL against real DuckDB or Snowflake. The CLAUDE.md rule about executing tests in the target databases still applies.
