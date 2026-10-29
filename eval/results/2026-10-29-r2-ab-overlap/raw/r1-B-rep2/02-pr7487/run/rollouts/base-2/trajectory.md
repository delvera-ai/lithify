# trajectory base-2

final message:
The ClickHouse parser now accepts `groupConcat`'s parametric form, and the statement round-trips unchanged.

`SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and regenerates identically. The full suite passes (1081 tests, 17836 subtests), and the ClickHouse test file passes after formatting.

**Cause:** the ClickHouse parser only treats a call as a parametric aggregate when the function name is in its `AGG_FUNCTIONS` list. `groupConcat` wasn't in the list, so the first call was parsed as a plain function and the second `(part_name)` was misread, which produced the `Invalid expression` error.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. Combinators such as `groupConcatIf` now work through the existing suffix handling.
- `tests/dialects/test_clickhouse.py`: added round-trip checks for `groupConcat(', ')(part_name)` and `groupConcatIf(', ')(part_name, x > 1)`.

Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"groupconcat\\|group_concat\\|PARAMETRIC\\|quantile\\|Parameterized\\|params\" sqlglot/dialects/clickhouse.py | head -80; grep -n -i \"class GroupConcat\\|class Quantile\\|parameters\" sqlglot/expressions.py | head -30"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -n -i \"groupconcat\\|parametric\\|quantile\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/dialects/dialect.py | head -60; grep -n \"class GroupConcat\\|class Quantile\\|class ParameterizedAgg\" -A6 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -60"}
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
sqlglot/dialects/dialect.py:2397:def groupconcat_sql(
sqlglot/dialects/dialect.py:2399:    expression: exp.GroupConcat,
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=se
…[1140 chars elided]…
/aggregate.py-236-        "this": True,
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py-1940-    arg_types = {"this": True, "expressions": True, "params": True}
sqlglot/expressions/core.py-1941-
sqlglot/expressions/core.py-1942-
sqlglot/expressions/core.py-1943-class Anonymous(Expression, Func):
sqlglot/expressions/core.py-1944-    arg_types = {"this": True, "expressions": False}
sqlglot/expressions/core.py-1945-    is_var_len_args = True
[tool_use Bash] {"command": "grep -n \"ParameterizedAgg\\|PARAMETERIZED_AGG\\|_parse_quantile\\|QUANTILE\" -n sqlglot/parser.py sqlglot/dialects/clickhouse.py sqlglot/generator.py | head -40"}
[tool_result] sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
[tool_use Bash] {"command": "grep -n \"ParameterizedAgg\\|PARAMETRIC\\|parametric\\|ParamAgg\\|_parse_params\\|params\" sqlglot/parser.py sqlglot/dialects/clickhouse.py | head -40; sed -n 5700,5730p sqlglot/generator.py"}
[tool_result] sqlglot/parser.py:1351:            exp.ExcludeColumnConstraint(this=self._parse_index_params())
sqlglot/parser.py:4434:    def _parse_index_params(self) -> exp.IndexParameters:
sqlglot/parser.py:4489:        params = self._parse_index_params()
sqlglot/parser.py:4493:                this=index, table=table, unique=unique, primary=primary, amp=amp, params=params
sqlglot/parser.py:7393:                include=self._parse_index_params(),
sqlglot/parser.py:9370:        params = self._parse_wrapped(se
…[961 chars elided]…
saggfunc_sql(expression)

    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
        return self.parameterizedagg_sql(expression)

    def show_sql(self, expression: exp.Show) -> str:
        self.unsupported("Unsupported SHOW statement")
        return ""

    def install_sql(self, expression: exp.Install) -> str:
        self.unsupported("Unsupported INSTALL statement")
        return ""

    def get_put_sql(self, expression: exp.Put | exp.Get) -> str:
[tool_use Bash] {"command": "grep -rn \"ParameterizedAgg\\|CombinedParameterizedAgg\" sqlglot | grep -v \"^sqlglot/generator.py:57\" | head -30; grep -n \"groupConcat\\|groupconcat\\|GROUPCONCAT\\|GroupConcat\" -i sqlglot/dialects/clickhouse.py tests/dialects/test_clickhouse.py | head"}
[tool_result] sqlglot/parsers/clickhouse.py:698:                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
sqlglot/parsers/clickhouse.py:701:                exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
[tool_use Bash] {"command": "sed -n 640,730p sqlglot/parsers/clickhouse.py; grep -n -i \"groupconcat\\|group_concat\" sqlglot/parsers/clickhouse.py sqlglot/dialects/clickhouse.py sqlglot/generators/clickhouse.py 2>/dev/null"}
[tool_result]                 exp.CTE(this=self._parse_assignment(), alias=self._parse_table_alias(), scalar=True)
            )

        return cte

    def _parse_join_parts(
        self,
    ) -> tuple[Token | None, Token | None, Token | None]:
        is_global = self._prev if self._match(TokenType.GLOBAL) else None

        kind_pre = self._prev if self._match_set(self.JOIN_KINDS) else None
        side = self._prev if self._match_set(self.JOIN_SIDES) else None
        kind = self._prev if self._match_s
…[2576 chars elided]…
    expr = self._parse_window(func)
            else:
                expr = func

        return expr

    def _parse_func_params(self, this: exp.Func | None = None) -> list[exp.Expr] | None:
        if self._match_pair(TokenType.R_PAREN, TokenType.L_PAREN):
            return self._parse_csv(self._parse_lambda)

        if self._match(TokenType.L_PAREN):
            params = self._parse_csv(self._parse_lambda)
            self._match_r_paren(this)
            return params

        return None
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS c FROM system.parts\\\", \\\"SELECT groupConcat(part_name) AS c FROM t\\\", \\\"SELECT groupConcat(3)(part_name) FROM t\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\" ; grep -n \"_resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | head -60"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m c FROM system.parts
Alias(
  this=Anonymous(
    this=groupConcat,
    expressions=[
      Column(
        this=Identifier(this=part_name, quoted=False))]),
  alias=Identifier(this=c, quoted=False))
SELECT groupConcat(part_name) AS c FROM t
Aliases(
  this=Anonymous(
    this=groupConcat,
    expressions=[
      Literal(this=3, is_string=False)]),
  expressions=[
    Identifier(this=part_
…[2528 chars elided]…
        # The window's func was parsed as Anonymous in base parser, fix its
710-                # type to be ClickHouse style CombinedAnonymousAggFunc / AnonymousAggFunc
711-                expr.set("this", func)
712-            elif params:
713-                # Params have blocked super()._parse_function() from parsing the following window
714-                # (if that exists) as they're standing between the function call and the window spec
715-                expr = self._parse_window(func)
[tool_use Bash] {"command": "grep -rn \"AGG_FUNC_MAPPING\\b\" sqlglot | head; grep -rn \"groupconcat\\|groupConcat\" -i sqlglot | head; grep -rn -i \"groupconcat\" tests | head"}
[tool_result] sqlglot/parsers/clickhouse.py:233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
sqlglot/parsers/clickhouse.py:330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
sqlglot/parsers/clickhouse.py:342:        # as AGG_FUNC_MAPPING memoizes all 0- and 1-suffix
sqlglot/parsers/clickhouse.py:344:        while (parts := AGG_FUNC_MAPPING.get(name)) is None:
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.Gr
…[144 chars elided]…
y:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/typing/bigquery.py:171:            exp.GroupConcat,
sqlglot/typing/__init__.py:222:            exp.GroupConcat,
sqlglot/dialects/dialect.py:2397:def groupconcat_sql(
[tool_use Bash] {"command": "sed -n 200,300p sqlglot/parsers/clickhouse.py; sed -n 360,380p sqlglot/parsers/clickhouse.py"}
[tool_result]     "sequenceCount",
    "windowFunnel",
    "retention",
    "uniqUpTo",
    "sequenceNextNode",
    "exponentialTimeDecayedAvg",
}

# Sorted longest-first so that compound suffixes (e.g. "SimpleState") are matched
# before their sub-suffixes (e.g. "State") when resolving multi-combinator functions.
AGG_FUNCTIONS_SUFFIXES: list[str] = sorted(
    [
        "If",
        "Array",
        "ArrayIf",
        "Map",
        "SimpleState",
        "State",
        "Merge",
        "MergeState",
    
…[4420 chars elided]…
ion_args(alias=False)),
        "OR": lambda self: exp.or_(*self._parse_function_args(alias=False)),
    }

    PROPERTY_PARSERS = {
        **{k: v for k, v in parser.Parser.PROPERTY_PARSERS.items() if k != "DYNAMIC"},
        "ENGINE": lambda self: self._parse_engine_property(),
        "UUID": lambda self: self.expression(exp.UuidProperty(this=self._parse_string())),
    }

    NO_PAREN_FUNCTION_PARSERS = {
        k: v for k, v in parser.Parser.NO_PAREN_FUNCTION_PARSERS.items() if k != "ANY"
[tool_use Bash] {"command": "sed -n 120,200p sqlglot/parsers/clickhouse.py | grep -n \"groupArray\\|AGG_FUNCTIONS\\|\\\"group\\|quantile\" ; grep -n \"groupArray\\|groupUniq\" tests/dialects/test_clickhouse.py | head -20; grep -n \"class GroupConcat\\|ParameterizedAgg\\|group_concat\" -i sqlglot/generators/clickhouse.py 2>/dev/null | head; ls sqlglot/generators | head -50"}
[tool_result] 8:    "groupArray",
9:    "groupArrayLast",
10:    "groupUniqArray",
11:    "groupArrayInsertAt",
12:    "groupArrayMovingAvg",
13:    "groupArrayMovingSum",
14:    "groupArraySample",
15:    "groupBitAnd",
16:    "groupBitOr",
17:    "groupBitXor",
18:    "groupBitmap",
19:    "groupBitmapAnd",
20:    "groupBitmapOr",
21:    "groupBitmapXor",
36:    "quantile",
37:    "quantiles",
38:    "quantileExact",
39:    "quantilesExact",
40:    "quantilesExactExclusive",
41:    "quantileExactLow",
42:  
…[765 chars elided]…
73:            "SELECT * FROM ABC WHERE hasAny(COLUMNS('.*field') APPLY(toUInt64) APPLY(to), (SELECT groupUniqArray(toUInt64(field))))"
__init__.py
__pycache__
athena.py
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
[tool_use Bash] {"command": "sed -n 120,135p sqlglot/parsers/clickhouse.py; sed -n 95,115p tests/dialects/test_clickhouse.py; grep -n \"groupArray\" sqlglot/parsers/clickhouse.py | head -3; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nprint(repr(sqlglot.parse_one(\\\"SELECT groupArray(', ')(x) FROM t\\\", read='clickhouse').selects[0]))\""}
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
        self.validate_identity("SELECT * FROM foo ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL ANY JOIN bla")
        self.validate_identity("
…[1119 chars elided]…
("POSITION(haystack, needle)")
        self.validate_identity("POSITION(haystack, needle, position)")
        self.validate_identity("CAST(x AS DATETIME)", "CAST(x AS DateTime)")
        self.validate_identity("CAST(x AS TIMESTAMPTZ)", "CAST(x AS DateTime)")
127:    "groupArray",
128:    "groupArrayLast",
130:    "groupArrayInsertAt",
ParameterizedAgg(
  this=groupArray,
  expressions=[
    Literal(this=', ', is_string=True)],
  params=[
    Column(
      this=Identifier(this=x, quoted=False))])
[assistant] The root cause is visible: `groupConcat` isn't in the ClickHouse `AGG_FUNCTIONS` list, so the call parses as a plain `Anonymous` and the trailing `(part_name)` is misread. Let me check the list's layout before adding it.
[tool_use Bash] {"command": "grep -n \"^AGG_FUNCTIONS\" -A3 sqlglot/parsers/clickhouse.py; sed -n 126,140p sqlglot/parsers/clickhouse.py"}
[tool_result] 90:AGG_FUNCTIONS = {
91-    "count",
92-    "min",
93-    "max",
--
210:AGG_FUNCTIONS_SUFFIXES: list[str] = sorted(
211-    [
212-        "If",
213-        "Array",
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
    "groupBitmapAnd",
    "groupBitmapOr",
    "groupBitmapXor",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupArraySample\",\n    \"groupBitAnd\",", "new_string": "    \"groupArraySample\",\n    \"groupConcat\",\n    \"groupBitAnd\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py has been updated successfully.
[assistant] Now I'll add a test next to the existing parametric-aggregate identities, then check the behavior.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n        self.validate_identity(\"SELECT groupConcatIf(', ')(part_name, x > 1) FROM system.parts\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcatIf(', ')(part_name, x > 1) FROM t\\\"]:\n    e=sqlglot.parse_one(s, read='clickhouse'); print(e.sql('clickhouse'))\n\"; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(part_name) FROM t
SELECT groupConcatIf(', ')(part_name, x > 1) FROM t
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.31s
..................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 49.34s
[assistant] Targeted and full suites pass. The new test line may exceed the line-length limit, so I'll run the formatter check.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; ($R/ruff --version && $R/ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py; $R/ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -8"}
[tool_result] ruff 0.15.6
Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format tests/dialects/test_clickhouse.py && git diff && $R/python -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -2"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parsers/clickhouse.py b/sqlglot/parsers/clickhouse.py
index 592ecc70c..dda19b6d6 100644
--- a/sqlglot/parsers/clickhouse.py
+++ b/sqlglot/parsers/clickhouse.py
@@ -131,6 +131,7 @@ AGG_FUNCTIONS = {
     "groupArrayMovingAvg",
     "groupArrayMovingSum",
     "groupArraySample",
+    "groupConcat",
     "groupBitAnd",
     "groupBitOr",
     "groupBitXor",
diff --git a/tests/dialects/test_clickhouse.py b/tests/dialects/test_clickhouse.py
index ea42a140b..39
…[572 chars elided]…
        self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
         self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
         self.validate_identity("jaroWinklerSimilarity('hello', 'world')")
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.24s
[This command modified 1 file you've previously read: tests/dialects/test_clickhouse.py. Call Read before editing.]
[assistant] The ClickHouse parser now accepts `groupConcat`'s parametric form, and the statement round-trips unchanged.

`SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and regenerates identically. The full suite passes (1081 tests, 17836 subtests), and the ClickHouse test file passes after formatting.

**Cause:** the ClickHouse parser only treats a call as a parametric aggregate when the function name is in its `AGG_FUNCTIONS` list. `groupConcat` wasn't in the list, so the first call was parsed as a plain function and the second `(part_name)` was misread, which produced the `Invalid expression` error.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. Combinators such as `groupConcatIf` now work through the existing suffix handling.
- `tests/dialects/test_clickhouse.py`: added round-trip checks for `groupConcat(', ')(part_name)` and `groupConcatIf(', ')(part_name, x > 1)`.

Nothing is committed.
