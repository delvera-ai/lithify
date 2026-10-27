# trajectory base-2

final message:
The ClickHouse parametric form of `groupConcat` now parses and round-trips. The reported query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` comes back unchanged.

**Cause:** `groupConcat` wasn't in the ClickHouse `AGG_FUNCTIONS` list. Without that, the parser treated it as a plain function, so the second `(…)` group after the name was never read as parameters and the parse failed.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. This also makes the `-If`, `-Distinct`, `-Array` and other combinator suffixes work on it, e.g. `groupConcatIf(', ')(x, y > 1)`.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the Superset query, next to the existing `groupUniqArray(2)(a)` case.

**Verification:**
- `tests/dialects/test_clickhouse.py`: 29 passed.
- Full suite: 1081 passed.
- `ruff check` passes; I ran `ruff format` on the test file to fix one long line.

**Side effect:** a bare `groupConcat(x)` is now parsed as an aggregate rather than an anonymous function. It still generates the same SQL, but any caller inspecting the AST type would see a different node.

I haven't committed anything; the changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -n -i \"parametric\\|PARAMETRIC\\|groupconcat\\|group_concat\\|GroupConcat\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Search for parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9798:    def _parse_group_concat(self) -> exp.Expr | None:
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "grep -n -i \"parametric\\|quantile\\|PARAMETER\\|_parse_params\\|Anonymous\" sqlglot/dialects/clickhouse.py | head -60; echo ---; grep -n \"_parse_params\\|def _parse_function_call\\|params\" sqlglot/parser.py | head -40; echo ---; grep -n \"class Quantile\\|class GroupConcat\\|class ParameterizedAgg\\|ParameterizedAgg\" sqlglot/expressions/*.py sqlglot/*.py | head", "description": "Search clickhouse dialect and parser for param handling"}
[tool_result] ---
1351:            exp.ExcludeColumnConstraint(this=self._parse_index_params())
4434:    def _parse_index_params(self) -> exp.IndexParameters:
4489:        params = self._parse_index_params()
4493:                this=index, table=table, unique=unique, primary=primary, amp=amp, params=params
6754:    def _parse_function_call(
7393:                include=self._parse_index_params(),
9370:        params = self._parse_wrapped(self._parse_copy_parameters, optional=True)
9377:            exp.Copy(t
…[111 chars elided]…
133:class GroupConcat(Expression, AggFunc):
sqlglot/expressions/aggregate.py:230:class Quantile(Expression, AggFunc):
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
[tool_use Bash] {"command": "sed -n 1930,1975p sqlglot/expressions/core.py; echo ---; sed -n 5705,5730p sqlglot/generator.py; echo ---; grep -rn \"ParameterizedAgg\\|PARAMETERIZED_AGG\" sqlglot/ | grep -v \"^sqlglot/expressions/core.py:19\\|generator.py:57\" ; echo ---; grep -n \"groupconcat\\|GroupConcat\\|quantile\" -i sqlglot/dialects/clickhouse.py", "description": "Inspect ParameterizedAgg and its uses"}
[tool_result] class SafeFunc(Expression, Func):
    pass


class Typeof(Expression, Func):
    pass


class ParameterizedAgg(Expression, AggFunc):
    arg_types = {"this": True, "expressions": True, "params": True}


class Anonymous(Expression, Func):
    arg_types = {"this": True, "expressions": False}
    is_var_len_args = True

    @property
    def name(self) -> str:
        return self.this if isinstance(self.this, str) else self.this.name


class AnonymousAggFunc(Expression, AggFunc):
    arg_types = {"
…[1413 chars elided]…
orted("Unsupported SHOW statement")
        return ""

    def install_sql(self, expression: exp.Install) -> str:
        self.unsupported("Unsupported INSTALL statement")
        return ""

    def get_put_sql(self, expression: exp.Put | exp.Get) -> str:
---
sqlglot/parsers/clickhouse.py:698:                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
sqlglot/parsers/clickhouse.py:701:                exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
---
[tool_use Bash] {"command": "sed -n 660,730p sqlglot/parsers/clickhouse.py; echo ---; grep -n -i \"groupconcat\\|group_concat\" sqlglot/parsers/clickhouse.py sqlglot/parsers/*.py sqlglot/generators/clickhouse.py sqlglot/dialects/clickhouse.py 2>/dev/null | head; echo ---; grep -n -i \"groupconcat\\|group_concat\" tests/dialects/test_clickhouse.py | head", "description": "View ClickHouse parametric agg parsing code"}
[tool_result]         if join:
            method = join.args.get("method")
            join.set("method", None)
            join.set("global_", method)

            # tbl ARRAY JOIN arr <-- this should be a `Column` reference, not a `Table`
            # https://clickhouse.com/docs/en/sql-reference/statements/select/array-join
            if join.kind == "ARRAY":
                for table in join.find_all(exp.Table):
                    table.replace(table.to_column())

        return join

    def _parse_fu
…[2542 chars elided]…
py:122:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
sqlglot/parsers/exasol.py:123:        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
sqlglot/parsers/mysql.py:156:        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
---
[assistant] Let me reproduce the failure and check how the parser currently handles `groupConcat`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS c FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(1)(x) FROM t\\\", \\\"SELECT groupConcatDistinct(', ')(x) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])[:300]); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"_resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | head -60", "description": "Reproduce groupConcat parse failure"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m c FROM system.parts
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
Aliases(
  this=Anon
…[2663 chars elided]…
        # The window's func was parsed as Anonymous in base parser, fix its
710-                # type to be ClickHouse style CombinedAnonymousAggFunc / AnonymousAggFunc
711-                expr.set("this", func)
712-            elif params:
713-                # Params have blocked super()._parse_function() from parsing the following window
714-                # (if that exists) as they're standing between the function call and the window spec
715-                expr = self._parse_window(func)
[tool_use Bash] {"command": "grep -rn \"AGG_FUNC_MAPPING\\|AGG_FUNCTIONS\\b\" sqlglot/ | head; grep -rn -i \"groupconcat\\|group_concat\" sqlglot/ tests/dialects/test_clickhouse.py | grep -iv \"mysql\\|duckdb\\|exasol\\|redshift\\|spark\\|doris\\|GROUP_CONCAT\\\"\" | head -20", "description": "Locate AGG_FUNC_MAPPING and groupConcat references"}
[tool_result] sqlglot/parsers/clickhouse.py:90:AGG_FUNCTIONS = {
sqlglot/parsers/clickhouse.py:233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
sqlglot/parsers/clickhouse.py:234:    f"{f}{sfx}": (f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
sqlglot/parsers/clickhouse.py:235:} | {f: (f, None) for f in AGG_FUNCTIONS}
sqlglot/parsers/clickhouse.py:313:    AGG_FUNCTIONS = AGG_FUNCTIONS
sqlglot/parsers/clickhouse.py:330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
sqlglot/parsers/click
…[1381 chars elided]…
CAT({distinct_sql}{self.format_args(this, separator)})"
sqlglot/generators/tsql.py:49:def _string_agg_sql(self: TSQLGenerator, expression: exp.GroupConcat) -> str:
sqlglot/generators/tsql.py:53:        # exp.Distinct can appear below an exp.Order or an exp.GroupConcat expression
sqlglot/generators/tsql.py:204:        exp.GroupConcat: _string_agg_sql,
sqlglot/generators/postgres.py:18:    groupconcat_sql,
sqlglot/generators/postgres.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
[tool_use Bash] {"command": "sed -n 85,100p sqlglot/parsers/clickhouse.py; grep -n -i \"\\\"groupArray\\\"\\|\\\"groupUniqArray\\\"\\|\\\"quantile\\\"\\|\\\"uniq\\\"\\|\\\"topK\\\"\" sqlglot/parsers/clickhouse.py; sed -n 200,232p sqlglot/parsers/clickhouse.py; echo ---; grep -n -i \"parametric\\|quantile(0\\|topk(\" tests/dialects/test_clickhouse.py | head -20", "description": "View AGG_FUNCTIONS list and related tests"}
[tool_result]     "QUARTER",
    "YEAR",
}


AGG_FUNCTIONS = {
    "count",
    "min",
    "max",
    "sum",
    "avg",
    "any",
    "stddevPop",
    "stddevSamp",
    "varPop",
    "varSamp",
122:    "topK",
127:    "groupArray",
129:    "groupUniqArray",
149:    "uniq",
155:    "quantile",
297:        "UNIQ": exp.ApproxDistinct.from_arg_list,
365:        "QUANTILE": lambda self: self._parse_quantile(),
    "sequenceCount",
    "windowFunnel",
    "retention",
    "uniqUpTo",
    "sequenceNextNode",
    "e
…[303 chars elided]…
   "Map",
        "SimpleState",
        "State",
        "Merge",
        "MergeState",
        "ForEach",
        "Distinct",
        "OrDefault",
        "OrNull",
        "Resample",
        "ArgMin",
        "ArgMax",
    ],
    key=len,
    reverse=True,
)

# Memoized examples of all 0- and 1-suffix aggregate function names
---
98:        self.validate_identity("SELECT quantile(0.5)(a)")
561:            "SELECT quantile(0.5)(a)",
567:                "clickhouse": "SELECT quantile(0.5)(a)",
[tool_use Bash] {"command": "sed -n 100,160p sqlglot/parsers/clickhouse.py; sed -n 90,110p tests/dialects/test_clickhouse.py; sed -n 555,575p tests/dialects/test_clickhouse.py", "description": "View agg list and existing parametric tests"}
[tool_result]     "varSamp",
    "corr",
    "covarPop",
    "covarSamp",
    "entropy",
    "exponentialMovingAverage",
    "intervalLengthSum",
    "kolmogorovSmirnovTest",
    "mannWhitneyUTest",
    "median",
    "rankCorr",
    "sumKahan",
    "studentTTest",
    "welchTTest",
    "anyHeavy",
    "anyLast",
    "boundingRatio",
    "first_value",
    "last_value",
    "argMin",
    "argMax",
    "avgWeighted",
    "topK",
    "approx_top_sum",
    "topKWeighted",
    "deltaSum",
    "deltaSumTimestamp",

…[2430 chars elided]…
ECT quantile(0.5)(a)",
            read={
                "duckdb": "SELECT quantile(a, 0.5)",
                "clickhouse": "SELECT median(a)",
            },
            write={
                "clickhouse": "SELECT quantile(0.5)(a)",
            },
        )
        self.validate_all(
            "SELECT quantiles(0.5, 0.4)(a)",
            read={"duckdb": "SELECT quantile(a, [0.5, 0.4])"},
            write={"clickhouse": "SELECT quantiles(0.5, 0.4)(a)"},
        )
        self.validate_all(
[assistant] The cause is clear: `groupConcat` isn't in `AGG_FUNCTIONS`, so `_resolve_clickhouse_agg` returns `None` and the parametric path (`_parse_func_params`) never runs. Let me check for any existing expectations on `groupConcat` before changing the list.
[tool_use Bash] {"command": "grep -rn -i \"groupconcat\" tests/ | head", "description": "Check tests referencing groupConcat"}
[tool_result] (Bash completed with no output)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupArray\",\n    \"groupArrayLast\",", "new_string": "    \"groupArray\",\n    \"groupConcat\",\n    \"groupArrayLast\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py has been updated successfully.
[assistant] Now I'll add a regression test next to the existing parametric-aggregate identities, then verify the round-trip.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcatIf(', ')(x, y > 1) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='clickhouse'); print(e.sql('clickhouse'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5", "description": "Verify round-trip and run ClickHouse tests"}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(part_name) FROM t
SELECT groupConcatIf(', ')(x, y > 1) FROM t
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.26s
[assistant] The reported query now parses and round-trips. Running the full suite as the project's check command:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
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
1081 passed, 17836 subtests passed in 42.35s
[assistant] Full suite passes (1081 tests). I'll check formatting/lint on the touched files, since the new test line is long.
[tool_use Bash] {"command": "(ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py; ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -8", "description": "Run ruff format and lint checks"}
[tool_result] Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "ruff format tests/dialects/test_clickhouse.py && git diff --stat && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -1; git diff", "description": "Apply ruff formatting and show final diff"}
[tool_result] 1 file reformatted
 sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 3 +++
 2 files changed, 4 insertions(+)
29 passed, 270 subtests passed in 0.14s
diff --git a/sqlglot/parsers/clickhouse.py b/sqlglot/parsers/clickhouse.py
index 592ecc70c..0a880c597 100644
--- a/sqlglot/parsers/clickhouse.py
+++ b/sqlglot/parsers/clickhouse.py
@@ -125,6 +125,7 @@ AGG_FUNCTIONS = {
     "deltaSum",
     "deltaSumTimestamp",
     "groupArray",
+    "groupConcat",
     "groupArrayLast",
…[488 chars elided]…
2)(a)")
+        self.validate_identity(
+            "SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts"
+        )
         self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
         self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
         self.validate_identity("jaroWinklerSimilarity('hello', 'world')")
[This command modified 1 file you've previously read: tests/dialects/test_clickhouse.py. Call Read before editing.]
[assistant] The ClickHouse parametric form of `groupConcat` now parses and round-trips. The reported query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` comes back unchanged.

**Cause:** `groupConcat` wasn't in the ClickHouse `AGG_FUNCTIONS` list. Without that, the parser treated it as a plain function, so the second `(…)` group after the name was never read as parameters and the parse failed.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. This also makes the `-If`, `-Distinct`, `-Array` and other combinator suffixes work on it, e.g. `gr
…[28 chars elided]…
.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the Superset query, next to the existing `groupUniqArray(2)(a)` case.

**Verification:**
- `tests/dialects/test_clickhouse.py`: 29 passed.
- Full suite: 1081 passed.
- `ruff check` passes; I ran `ruff format` on the test file to fix one long line.

**Side effect:** a bare `groupConcat(x)` is now parsed as an aggregate rather than an anonymous function. It still generates the same SQL, but any caller inspecting the AST type would see a different node.

I haven't committed anything; the changes are in the working tree.
