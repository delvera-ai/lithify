# trajectory base-1

final message:
ClickHouse `groupConcat` now parses its parametric form, so `groupConcat(', ')(part_name)` round-trips unchanged. The full suite passes: 1081 tests, including the ClickHouse file.

The cause was that `groupConcat` was missing from the ClickHouse aggregate-name list in `sqlglot/parsers/clickhouse.py`. Without it, the call parsed as a plain anonymous function, so the `(...)` after it was an error. I added it next to `groupArray`. That also makes the `-If`/`-Merge`-style combinators work on it, for example `groupConcatIf(', ')(part_name, x > 1)`.

I added two identity round-trip assertions to `tests/dialects/test_clickhouse.py`: the parametric form from the Superset report, and the plain `groupConcat(part_name)` form.

Changes are uncommitted in the worktree. I did not commit, since you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|GROUP_CONCAT\\|parametric\\|PARAMETRIC\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/expressions.py sqlglot/generator.py | head -60; grep -n \"quantile\\|Quantile\" sqlglot/dialects/clickhouse.py | head -30", "description": "Search for existing parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9798:    def _parse_group_concat(self) -> exp.Expr | None:
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "grep -n -i \"param\\|quantile\\|FUNCTION_PARAMS\\|_parse_function\" sqlglot/dialects/clickhouse.py | head -60; grep -rn -i \"param\" sqlglot/dialects/clickhouse.py | wc -l; grep -n \"class Quantile\\|class GroupConcat\\|class ParameterizedAgg\" -A6 sqlglot/expressions/*.py | head -60", "description": "Look at ClickHouse parametric handling and expression classes"}
[tool_result]        0
sqlglot/expressions/aggregate.py:133:class GroupConcat(Expression, AggFunc):
sqlglot/expressions/aggregate.py-134-    arg_types = {"this": True, "separator": False, "on_overflow": False}
sqlglot/expressions/aggregate.py-135-
sqlglot/expressions/aggregate.py-136-
sqlglot/expressions/aggregate.py-137-class Grouping(Expression, AggFunc):
sqlglot/expressions/aggregate.py-138-    arg_types = {"expressions": True}
sqlglot/expressions/aggregate.py-139-    is_var_len_args = True
--
sqlglot/expr
…[367 chars elided]…
/aggregate.py-236-        "this": True,
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py-1940-    arg_types = {"this": True, "expressions": True, "params": True}
sqlglot/expressions/core.py-1941-
sqlglot/expressions/core.py-1942-
sqlglot/expressions/core.py-1943-class Anonymous(Expression, Func):
sqlglot/expressions/core.py-1944-    arg_types = {"this": True, "expressions": False}
sqlglot/expressions/core.py-1945-    is_var_len_args = True
[tool_use Bash] {"command": "grep -rn \"ParameterizedAgg\" sqlglot/ | head; grep -n \"PARAMETERIZED\\|ParameterizedAgg\" -B3 -A25 sqlglot/parser.py | sed -n 1,80p", "description": "Find how ParameterizedAgg is parsed and generated"}
[tool_result] sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/parsers/clickhouse.py:698:                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
sqlglot/parsers/clickhouse.py:701:                exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
[tool_use Bash] {"command": "sed -n 650,730p sqlglot/parsers/clickhouse.py; sed -n 5700,5730p sqlglot/generator.py; grep -n \"groupconcat\\|GroupConcat\\|group_concat\" -i sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py sqlglot/dialects/clickhouse.py 2>/dev/null", "description": "Read ClickHouse parametric aggregate parse and generate code"}
[tool_result]         kind_pre = self._prev if self._match_set(self.JOIN_KINDS) else None
        side = self._prev if self._match_set(self.JOIN_SIDES) else None
        kind = self._prev if self._match_set(self.JOIN_KINDS) else None

        return is_global, side or kind, kind_pre or kind

    def _parse_join(
        self, skip_join_token: bool = False, parse_bracket: bool = False
    ) -> exp.Join | None:
        join = super()._parse_join(skip_join_token=skip_join_token, parse_bracket=True)
        if jo
…[3567 chars elided]…
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
[assistant] Parametric aggregates already exist for ClickHouse. Let me reproduce the failure and see why `groupConcat` isn't taking that path.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT quantile(0.5)(x) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])[:300]); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"_resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | head -50; grep -rn -i \"groupconcat\\|group_concat\" sqlglot/ | head", "description": "Reproduce groupConcat parse failure"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m concatenated FROM system.parts
Anonymous(
  this=groupConcat,
  expressions=[
    Column(
      this=Identifier(this=part_name, quoted=False))])
SELECT groupConcat(part_name) FROM t
Quantile(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  quantile=Literal(this=0.5, is_string=False))
SELECT quantile(0.5)(x) FROM t
333:    def _resolve_clickhouse_agg(cls, name: str) -> tuple[s
…[3136 chars elided]…
Concat(this=this, separator=separator))
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/doris.py:38:        k: v for k, v in MySQLParser.FUNCTION_PARSERS.items() if k != "GROUP_CONCAT"
sqlglot/parsers/exasol.py:122:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
sqlglot/parsers/exasol.py:123:        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
[assistant] The reproduction confirms it: `groupConcat` falls through to `Anonymous` because `_resolve_clickhouse_agg` doesn't recognize it. Let me check how `AGG_FUNC_MAPPING` is built.
[tool_use Bash] {"command": "grep -n \"AGG_FUNC_MAPPING\\|AGG_FUNCTIONS\\b\\|AGG_FUNCTIONS =\" -A12 sqlglot/parsers/clickhouse.py | sed -n 1,80p; grep -n \"groupArray\\|grouparray\\|GROUPARRAY\" -i sqlglot/parsers/clickhouse.py sqlglot/dialects/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py | head", "description": "Inspect AGG_FUNC_MAPPING construction"}
[tool_result] 90:AGG_FUNCTIONS = {
91-    "count",
92-    "min",
93-    "max",
94-    "sum",
95-    "avg",
96-    "any",
97-    "stddevPop",
98-    "stddevSamp",
99-    "varPop",
100-    "varSamp",
101-    "corr",
102-    "covarPop",
--
233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
234:    f"{f}{sfx}": (f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
235:} | {f: (f, None) for f in AGG_FUNCTIONS}
236-
237-
238-class ClickHouseParser(parser.Parser):
239-    # Tested in ClickHou
…[2152 chars elided]…
agg_func_name, inner_suffix = parts
355-        if inner_suffix:
356-            # this is a 1-suffix aggregate (either naturally or via repeated suffix
sqlglot/parsers/clickhouse.py:127:    "groupArray",
sqlglot/parsers/clickhouse.py:128:    "groupArrayLast",
sqlglot/parsers/clickhouse.py:130:    "groupArrayInsertAt",
sqlglot/parsers/clickhouse.py:131:    "groupArrayMovingAvg",
sqlglot/parsers/clickhouse.py:132:    "groupArrayMovingSum",
sqlglot/parsers/clickhouse.py:133:    "groupArraySample",
[tool_use Bash] {"command": "sed -n 120,150p sqlglot/parsers/clickhouse.py; grep -n \"groupConcat\\|groupArray(\" -i tests/dialects/test_clickhouse.py | head; grep -n \"class CombinedParameterizedAgg\\|AggFunc)\" sqlglot/expressions/core.py | head -3", "description": "Read the ClickHouse aggregate name list around groupArray"}
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
    "groupBitmapAnd",
    "groupBitmapOr",
    "groupBitmapXor",
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
1939:class ParameterizedAgg(Expression, AggFunc):
1952:class AnonymousAggFunc(Expression, AggFunc):
1957:class CombinedAggFunc(AnonymousAggFunc):
[assistant] `groupConcat` is simply missing from the ClickHouse `AGG_FUNCTIONS` list, so it never reaches the parametric branch. Adding it there should route `groupConcat(', ')(x)` through `ParameterizedAgg`, as `quantile` already does. Let me check existing test conventions before editing.
[tool_use Bash] {"command": "grep -n \"(0.5)(\\|quantileTDigest\\|topK(\" tests/dialects/test_clickhouse.py | head -8; grep -n \"def test_\" tests/dialects/test_clickhouse.py | head -3", "description": "Find existing parametric aggregate tests"}
[tool_result] 98:        self.validate_identity("SELECT quantile(0.5)(a)")
99:        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
100:        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
101:        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
104:        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
518:            "SELECT quantileIf(0.5)(a, true)",
520:                "clickhouse": "SELECT quantileIf(0.5)(a, TRUE)",
561:            "SELECT quantile(0.5)(a)",
15:    def test_clickhouse(self):
737:    def test_clickhouse_values(self):
776:    def test_cte(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163206-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupArray\",\n    \"groupArrayLast\",", "new_string": "    \"groupArray\",\n    \"groupConcat\",\n    \"groupArrayLast\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163206-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-163206-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT quantileState(0.5)(a) AS x FROM t\")", "new_string": "        self.validate_identity(\"SELECT quantileState(0.5)(a) AS x FROM t\")\n        self.validate_identity(\n            \"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\"\n        )\n        self.validate_identity(\"SELECT groupConcat(part_name) FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-163206-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT groupConcat(', ')(part_name) AS c FROM system.parts\\\", read='clickhouse', write='clickhouse'))\nprint(sqlglot.transpile(\\\"SELECT groupConcatIf(', ')(part_name, x > 1) FROM t\\\", read='clickhouse', write='clickhouse'))\"", "description": "Run ClickHouse tests and spot-check round-trips"}
[tool_result] .............................                                                              [100%]
29 passed, 270 subtests passed in 0.24s
["SELECT groupConcat(', ')(part_name) AS c FROM system.parts"]
["SELECT groupConcatIf(', ')(part_name, x > 1) FROM t"]
[assistant] Targeted tests pass. Now the full project check suite, since adding a name to the shared aggregate list could affect other dialects.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
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
1081 passed, 17836 subtests passed in 43.65s
[assistant] ClickHouse `groupConcat` now parses its parametric form, so `groupConcat(', ')(part_name)` round-trips unchanged. The full suite passes: 1081 tests, including the ClickHouse file.

The cause was that `groupConcat` was missing from the ClickHouse aggregate-name list in `sqlglot/parsers/clickhouse.py`. Without it, the call parsed as a plain anonymous function, so the `(...)` after it was an error. I added it next to `groupArray`. That also makes the `-If`/`-Merge`-style combinators work on it, for example `groupConcatIf(', ')(part_name, x > 1)`.

I added two identity round-trip assertions to `tests/dialects/test_clickhouse.py`: the parametric form from the Superset report, and the plain `groupConcat(part_name)` form.

Changes are uncommitted in the worktree. I did not commit, since you didn't ask for one.
