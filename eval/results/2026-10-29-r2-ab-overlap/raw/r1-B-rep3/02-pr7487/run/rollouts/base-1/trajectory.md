# trajectory base-1

final message:
ClickHouse's `groupConcat` parametric form now parses and round-trips. The reported query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` produces the same SQL back.

**Cause:** `groupConcat` wasn't in the ClickHouse aggregate-function registry, so the parser treated `groupConcat(', ')` as a plain function call. It then choked on the second parenthesised group.

**Fix:** I added `"groupConcat"` to the aggregate set in `sqlglot/parsers/clickhouse.py`, next to `groupArray`. The existing parametric-aggregate machinery now handles it, the same way it does `quantile(0.5)(x)` and `groupUniqArray(2)(a)`. The combinators also work, e.g. `groupConcatIf(', ')(a, a > 1)`.

**Tests:** I added two round-trip identity checks to `tests/dialects/test_clickhouse.py`: the reported query and the `groupConcatIf` form. The full suite passes (1081 passed), `ruff format` and `ruff check` are clean on the changed files.

**Side effect:** A plain `groupConcat(col)` call is now parsed as an aggregate node rather than an anonymous function. Its generated SQL is unchanged.

**Naming note:** In sqlglot's AST, the first parenthesised group (`', '`) is stored as `expressions` and the second (`part_name`) as `params`. That's the existing convention for `quantile` and friends, so I left it alone.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|group_concat\\|PARAMETRIC\\|param\" sqlglot/dialects/clickhouse.py | head -60; grep -rn -i \"groupconcat\" sqlglot/ tests/dialects/test_clickhouse.py | head -20", "description": "Search ClickHouse dialect for parametric aggregate handling"}
[tool_result] sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.
…[621 chars elided]…
: lambda self, e: groupconcat_sql(self, e, on_overflow=True),
sqlglot/generators/bigquery.py:26:    groupconcat_sql,
sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/sqlite.py:266:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/doris.py:60:        exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/tsql.py:49:def _string_agg_sql(self: TSQLGenerator, expression: exp.GroupConcat) -> str:
[tool_use Bash] {"command": "ls sqlglot/dialects/ | head -50; grep -rn -i \"parametric\\|quantile\\|PARAM\" sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py | head -40; sed -n 125,145p sqlglot/expressions/aggregate.py", "description": "Locate ClickHouse parser/generator and GroupConcat class"}
[tool_result] __init__.py  3.6K
athena.py  4.3K
bigquery.py  7.1K
clickhouse.py  4.6K
databricks.py  1.1K
dialect.py  90.4K
doris.py  364B
dremio.py  1.6K
drill.py  1.4K
druid.py  224B
duckdb.py  4.1K
dune.py  329B
exasol.py  2.0K
fabric.py  1.8K
hive.py  3.6K
materialize.py  305B
mysql.py  5.7K
oracle.py  3.3K
postgres.py  4.4K
presto.py  2.1K
prql.py  782B
redshift.py  1.8K
risingwave.py  618B
singlestore.py  2.1K
snowflake.py  6.4K
solr.py  535B
spark.py  897B
spark2.py  977B
sqlite.py  1.1K
starrocks.py  
…[2811 chars elided]…
khouse.py:712:            elif params:
class First(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class FirstValue(Expression, AggFunc):
    pass


class GroupConcat(Expression, AggFunc):
    arg_types = {"this": True, "separator": False, "on_overflow": False}


class Grouping(Expression, AggFunc):
    arg_types = {"expressions": True}
    is_var_len_args = True


class GroupingId(Expression, AggFunc):
    arg_types = {"expressions": False}
    is_var_len_args = True
[tool_use Bash] {"command": "sed -n 140,155p sqlglot/parsers/clickhouse.py; sed -n 194,215p sqlglot/parsers/clickhouse.py; sed -n 670,730p sqlglot/parsers/clickhouse.py; grep -n \"ParameterizedAgg\\|class CombinedParameterizedAgg\" -A4 sqlglot/expressions/*.py | head -30", "description": "Read ClickHouse parametric aggregate parsing code"}
[tool_result]     "groupBitmapXor",
    "sumWithOverflow",
    "sumMap",
    "minMap",
    "maxMap",
    "skewSamp",
    "skewPop",
    "kurtSamp",
    "kurtPop",
    "uniq",
    "uniqExact",
    "uniqCombined",
    "uniqCombined64",
    "uniqHLL12",
    "uniqTheta",
    "quantile",
    "quantilesGK",
    "sparkBar",
    "sumCount",
    "largestTriangleThreeBuckets",
    "histogram",
    "sequenceMatch",
    "sequenceCount",
    "windowFunnel",
    "retention",
    "uniqUpTo",
    "sequenceNextNode",
    "exp
…[2768 chars elided]…
ue, "expressions": True, "params": True}
sqlglot/expressions/core.py-1941-
sqlglot/expressions/core.py-1942-
sqlglot/expressions/core.py-1943-class Anonymous(Expression, Func):
--
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
sqlglot/expressions/core.py-1962-    arg_types = {"this": True, "expressions": True, "params": True}
sqlglot/expressions/core.py-1963-
sqlglot/expressions/core.py-1964-
sqlglot/expressions/core.py-1965-class HashAgg(Expression, AggFunc):
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(1)(x) FROM t\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"_resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | sed -n 1,40p", "description": "Reproduce the ClickHouse groupConcat parse error"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m concatenated FROM system.parts
Anonymous(
  this=groupConcat,
  expressions=[
    Column(
      this=Identifier(this=part_name, quoted=False))])
SELECT groupConcat(part_name) FROM t
Aliases(
  this=Anonymous(
    this=groupConcat,
    expressions=[
      Literal(this=1, is_string=False)]),
  expressions=[
    Identifier(this=x, quoted=False)])
SELECT groupConcat(1) AS (x) FROM t
333:    d
…[1666 chars elided]…
xp.Anonymous) else None
691-
692-        if parts:
693-            anon_func: exp.Anonymous = t.cast(exp.Anonymous, func)
694-            params = self._parse_func_params(anon_func)
695-
696-            if len(parts[1]) > 0:
697-                exp_class: Type[exp.Expr] = (
698-                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
699-                )
700-            else:
701-                exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
702-
[tool_use Bash] {"command": "sed -n 60,80p sqlglot/parsers/clickhouse.py; grep -n \"groupArray\\|groupUniq\" sqlglot/parsers/clickhouse.py; grep -n \"quantile(0.5)\\|(0.5)(\\|ParameterizedAgg\\|groupArray(\" tests/dialects/test_clickhouse.py | head; grep -n \"ParameterizedAgg\" -A8 sqlglot/generators/clickhouse.py sqlglot/generator.py | head -30", "description": "Inspect AGG function registry and existing parametric tests"}
[tool_result]     sep = seq_get(args, 0)
    if isinstance(sep, exp.Literal):
        sep_value = sep.to_py()
        if isinstance(sep_value, str) and len(sep_value.encode("utf-8")) == 1:
            return _build_split(exp.Split)(args)

    return exp.Anonymous(this="splitByChar", expressions=args)


def _build_split(exp_class: Type[E]) -> t.Callable[[list], E]:
    return lambda args: exp_class(
        this=seq_get(args, 1), expression=seq_get(args, 0), limit=seq_get(args, 2)
    )


# Skip the 'week' uni
…[1645 chars elided]…
ot/generator.py-5720-        return self.parameterizedagg_sql(expression)
sqlglot/generator.py-5721-
sqlglot/generator.py-5722-    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generator.py-5723-        self.unsupported("Unsupported SHOW statement")
sqlglot/generator.py-5724-        return ""
sqlglot/generator.py-5725-
sqlglot/generator.py-5726-    def install_sql(self, expression: exp.Install) -> str:
sqlglot/generator.py-5727-        self.unsupported("Unsupported INSTALL statement")
[tool_use Bash] {"command": "sed -n 120,137p sqlglot/parsers/clickhouse.py", "description": "View the groupArray entries in the aggregate set"}
[tool_result]     "argMax",
    "avgWeighted",
    "topK",
    "approx_top_sum",
    "topKWeighted",
    "deltaSum",
    "deltaSumTimestamp",
    "groupArray",
    "groupArrayLast",
    "groupUniqArray",
    "groupArrayInsertAt",
    "groupArrayMovingAvg",
    "groupArrayMovingSum",
    "groupArraySample",
    "groupBitAnd",
    "groupBitOr",
    "groupBitXor",
    "groupBitmap",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172314-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupArraySample\",\n    \"groupBitAnd\",", "new_string": "    \"groupArraySample\",\n    \"groupConcat\",\n    \"groupBitAnd\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172314-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ')(a, b) FROM t\\\", \\\"SELECT groupConcatIf(', ')(a, x > 1) FROM t\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])[:200]); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Verify groupConcat parses and round-trips"}
[tool_result] Alias(
  this=ParameterizedAgg(
    this=groupConcat,
    expressions=[
      Literal(this=', ', is_string=True)],
    params=[
      Column(
        this=Identifier(this=part_name, quoted=False))]),

SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
AnonymousAggFunc(
  this=groupConcat,
  expressions=[
    Column(
      this=Identifier(this=part_name, quoted=False))])
SELECT groupConcat(part_name) FROM t
ParameterizedAgg(
  this=groupConcat,
  expressions=[
    Literal(this=', ', is_string=True)],
  params=[
    Column(
      this=Identifier(this=a, quoted=False)),
    Column(
      this=Identifier(th
SELECT groupConcat(', ')(a, b) FROM t
CombinedParameterizedAgg(
  this=groupConcatIf,
  expressions=[
    Literal(this=', ', is_string=True)],
  params=[
    Column(
      this=Identifier(this=a, quoted=False)),
    GT(
      this=Column(
SELECT groupConcatIf(', ')(a, x > 1) FROM t
[assistant] Parsing and round-trip now work. Next I'll add a regression test next to the existing parametric-aggregate tests and run the suite.
[tool_use Bash] {"command": "grep -n \"quantile\\|groupArray\" tests/dialects/test_clickhouse.py | head -20", "description": "Find existing aggregate tests in ClickHouse test file"}
[tool_result] 29 matches in 9 files:

1484:0:If + State with quantile parameter
520:0:"SELECT quantileIf(0.5)(a, TRUE)",
563:0:"SELECT quantile(a, 0.5)",
567:0:"SELECT quantile(0.5)(a)",
572:0:"SELECT quantile(a, [0.5, 0.4])"},
573:0:"SELECT quantiles(0.5, 0.4)(a)"},
577:0:"SELECT quantile(a, [0.5])"},
578:0:"SELECT quantiles(0.5)(a)"},
tests/dialects/test_clickhouse.py:98:self.validate_identity("SELECT quantile(0.5)(a)")
tests/dialects/test_clickhouse.py:99:self.validate_identity("SELECT quantiles(0.5)(a) AS
…[256 chars elided]…
e.py:103:self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
tests/dialects/test_clickhouse.py:104:self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
tests/dialects/test_clickhouse.py:151:"SELECT id, quantileGK(100, 0.95)(reading) OVER (PARTITION BY id ORDER BY id ...
tests/dialects/test_clickhouse.py:518:"SELECT quantileIf(0.5)(a, true)",
tests/dialects/test_clickhouse.py:561:"SELECT quantile(0.5)(a)",
tests/dialects/test_clickhouse.py:571:"SELECT quantiles(0.5, 0.4)(a)",
[tool_use Bash] {"command": "sed -n 96,106p tests/dialects/test_clickhouse.py", "description": "View parametric aggregate identity tests"}
[tool_result]         self.validate_identity("SELECT * FROM foo GLOBAL ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL LEFT ANY JOIN bla")
        self.validate_identity("SELECT quantile(0.5)(a)")
        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t")
        self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
        self.validate_identity("SELECT histogram(5)(a)")
        self.validate_identity("SELECT groupUniqArray(2)(a)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172314-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n        self.validate_identity(\"SELECT groupConcatIf(', ')(a, a > 1) AS x FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172314-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite"}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................. [ 38%]
.........................................
…[256 chars elided]…
................................................................................ [ 70%]
..................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 36.68s
[assistant] The full suite passes (1081 tests). I'll check the formatter on the new test line, since it may exceed the line limit.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ($R/ruff --version && $R/ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && $R/ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -8", "description": "Check formatting and lint on changed files"}
[tool_result] ruff 0.15.6
Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format --diff tests/dialects/test_clickhouse.py 2>&1 | head -30", "description": "Show the formatting diff for the test file"}
[tool_result] --- tests/dialects/test_clickhouse.py
+++ tests/dialects/test_clickhouse.py
@@ -104,7 +104,9 @@
         self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
         self.validate_identity("SELECT histogram(5)(a)")
         self.validate_identity("SELECT groupUniqArray(2)(a)")
-        self.validate_identity("SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts")
+        self.validate_identity(
+            "SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts"
+        )
         self.validate_identity("SELECT groupConcatIf(', ')(a, a > 1) AS x FROM t")
         self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
         self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")

1 file would be reformatted
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format tests/dialects/test_clickhouse.py && $R/ruff format --check sqlglot tests/dialects/test_clickhouse.py && $R/ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -2", "description": "Apply formatting, re-check, and rerun ClickHouse tests"}
[tool_result] 1 file reformatted
174 files already formatted
All checks passed!
sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 4 ++++
 2 files changed, 5 insertions(+)
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.13s
[This command modified 1 file you've previously read: tests/dialects/test_clickhouse.py. Call Read before editing.]
[assistant] ClickHouse's `groupConcat` parametric form now parses and round-trips. The reported query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` produces the same SQL back.

**Cause:** `groupConcat` wasn't in the ClickHouse aggregate-function registry, so the parser treated `groupConcat(', ')` as a plain function call. It then choked on the second parenthesised group.

**Fix:** I added `"groupConcat"` to the aggregate set in `sqlglot/parsers/clickhouse.py`, next to `groupArray`. The existing parametric-aggregate machinery now handles it, the same way it does `quantile(0.5)(x)`
…[139 chars elided]…
hecks to `tests/dialects/test_clickhouse.py`: the reported query and the `groupConcatIf` form. The full suite passes (1081 passed), `ruff format` and `ruff check` are clean on the changed files.

**Side effect:** A plain `groupConcat(col)` call is now parsed as an aggregate node rather than an anonymous function. Its generated SQL is unchanged.

**Naming note:** In sqlglot's AST, the first parenthesised group (`', '`) is stored as `expressions` and the second (`part_name`) as `params`. That's the existing convention for `quantile` and friends, so I left it alone.

I haven't committed anything.
