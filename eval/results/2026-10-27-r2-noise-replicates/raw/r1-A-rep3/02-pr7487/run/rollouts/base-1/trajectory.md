# trajectory base-1

final message:
`groupConcat(', ')(part_name)` now parses and round-trips in the ClickHouse dialect. The full suite passes: 1081 tests, 17,836 subtests.

**Cause:** `groupConcat` was not in ClickHouse's aggregate-name set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). So the call parsed as a plain `Anonymous` function, and the parser never looked for the second parenthesized list.

**Fix:** I added `"groupConcat"` to `AGG_FUNCTIONS`. The existing parametric-aggregate path then handles it, the same way it handles `quantile`, `uniqCombined` and others. The change also makes combinators like `groupConcatIf(...)(...)` work.

**Behaviour:**
- `groupConcat(', ')(part_name)` → `ParameterizedAgg`, output unchanged.
- `groupConcat(x)` → still prints as `groupConcat(x)`. Its class changes from `Anonymous` to `AnonymousAggFunc`.

**Test:** I added two assertions to `test_agg_functions` in `tests/dialects/test_clickhouse.py`, covering the Superset query with an alias and the bare form.

I haven't committed anything. The change is two lines in the parser plus the test.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|group_concat\\|parametric\\|PARAMETRIC\\|quantile\" sqlglot/dialects/clickhouse.py | head -50; grep -n -i \"groupconcat\\|GroupConcat\" sqlglot/expressions.py sqlglot/dialects/dialect.py | head", "description": "Search ClickHouse dialect for parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
2397:def groupconcat_sql(
2399:    expression: exp.GroupConcat,
[tool_use Bash] {"command": "sed -n 2390,2410p sqlglot/dialects/clickhouse.py; grep -rn \"class GroupConcat\" -A6 sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null; grep -n \"Parametric\\|parameters\\|params\" sqlglot/dialects/clickhouse.py | head -40; grep -n \"def _parse_function_call\\|PARAMETRIZED\\|parameters\" sqlglot/parser.py | head -30", "description": "Inspect groupconcat_sql and parametric parsing hooks"}
[tool_result] sqlglot/expressions/aggregate.py:133:class GroupConcat(Expression, AggFunc):
sqlglot/expressions/aggregate.py-134-    arg_types = {"this": True, "separator": False, "on_overflow": False}
sqlglot/expressions/aggregate.py-135-
sqlglot/expressions/aggregate.py-136-
sqlglot/expressions/aggregate.py-137-class Grouping(Expression, AggFunc):
sqlglot/expressions/aggregate.py-138-    arg_types = {"expressions": True}
sqlglot/expressions/aggregate.py-139-    is_var_len_args = True
6754:    def _parse_function_call(
9280:    def _parse_copy_parameters(self) -> list[exp.CopyParameter]:
9370:        params = self._parse_wrapped(self._parse_copy_parameters, optional=True)
[tool_use Bash] {"command": "grep -n \"groupconcat_sql\" -A12 sqlglot/dialects/clickhouse.py; grep -n \"_parse_function_call\\|def _parse_function\\b\\|def _parse_lambda\\|ClickHouse.*param\\|anonymous_params\\|PARAM\" sqlglot/dialects/clickhouse.py | head -30; sed -n 6754,6850p sqlglot/parser.py", "description": "Show groupconcat_sql and ClickHouse function parsing hooks"}
[tool_result]     def _parse_function_call(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
        if not self._curr:
            return None

        comments = self._curr.comments
        prev = self._prev
        token = self._curr
        token_type = self._curr.token_type
        this: str | exp.Expr = self._curr.text
        upper = self._curr.text.uppe
…[2814 chars elided]…
                func = func_builder(args)
                except TypeError:
                    func = func_builder(args, dialect=self.dialect)

                func = self.validate_expression(func, args)
                if self.dialect.PRESERVE_ORIGINAL_NAMES:
                    func.meta["name"] = this

                result = func
            else:
                if token_type == TokenType.IDENTIFIER:
                    this = exp.Identifier(this=this, quoted=True).update_positions(token)
[tool_use Bash] {"command": "git status --short | head; wc -l sqlglot/dialects/clickhouse.py; grep -n -i \"quantile\\|ParamAgg\\|Parameterized\\|GroupConcat\\|group_concat\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/generator.py | head -40", "description": "Check file size and search for parametric aggregate support"}
[tool_result]      131 sqlglot/dialects/clickhouse.py
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9798:    def _parse_group_concat(self) -> exp.Expr | None:
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/generator.py:5720:        return self.parameterizedagg_sql(expression)
[tool_use Bash] {"command": "grep -rn \"ParameterizedAgg\\|CombinedParameterizedAgg\" sqlglot/ | head -30; sed -n 5705,5725p sqlglot/generator.py", "description": "Locate ParameterizedAgg definitions and generator"}
[tool_result] sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/parsers/clickhouse.py:698:                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
sqlglot/parsers/clickhouse.py:701:                exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
sqlglot/expressions/core.py:1939:class Pa
…[527 chars elided]…
 exp.AnonymousAggFunc) -> str:
        return self.func(expression.name, *expression.expressions)

    def combinedaggfunc_sql(self, expression: exp.CombinedAggFunc) -> str:
        return self.anonymousaggfunc_sql(expression)

    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
        return self.parameterizedagg_sql(expression)

    def show_sql(self, expression: exp.Show) -> str:
        self.unsupported("Unsupported SHOW statement")
        return ""
[tool_use Bash] {"command": "sed -n 660,720p sqlglot/parsers/clickhouse.py; grep -n \"groupConcat\\|groupconcat\\|GROUP_CONCAT\\|\\\"GROUPCONCAT\\\"\" sqlglot/parsers/clickhouse.py sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/dialects/dialect.py; sed -n 1935,1965p sqlglot/expressions/core.py", "description": "Read ClickHouse parametric aggregate parsing and expression class"}
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
…[2207 chars elided]…
ue

    @property
    def name(self) -> str:
        return self.this if isinstance(self.this, str) else self.this.name


class AnonymousAggFunc(Expression, AggFunc):
    arg_types = {"this": True, "expressions": False}
    is_var_len_args = True


class CombinedAggFunc(AnonymousAggFunc):
    arg_types = {"this": True, "expressions": False}


class CombinedParameterizedAgg(ParameterizedAgg):
    arg_types = {"this": True, "expressions": True, "params": True}


class HashAgg(Expression, AggFunc):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS c FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT quantile(0.5)(x) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"def _resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py; grep -n \"def _parse_func_params\" -A25 sqlglot/parsers/clickhouse.py", "description": "Reproduce parse failure for groupConcat parametric form"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m c FROM system.parts
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
333:    def _resolve_clickhouse_agg(cls, name: str) -> tuple[str, Sequenc
…[2206 chars elided]…
37-        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))
738-
739-    def _parse_wrapped_id_vars(self, optional: bool = False) -> list[exp.Expr]:
740-        return super()._parse_wrapped_id_vars(optional=True)
741-
742-    def _parse_column_def(
743-        self, this: exp.Expr | None, computed_column: bool = True
744-    ) -> exp.Expr | None:
745-        if self._match(TokenType.DOT):
746-            return exp.Dot(this=this, expression=self._parse_id_var())
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT sumIf(1)(x) FROM t', 'SELECT uniqCombined(12)(x) FROM t', 'SELECT topKWeighted(10)(x, w) FROM t', 'SELECT foo(1)(x) FROM t']:\n    e = sqlglot.parse_one(s, read='clickhouse'); print(type(e.selects[0]).__name__, e.sql('clickhouse'))\n\"; grep -rn \"groupConcat\\|groupconcat\" tests/ | head; grep -n \"AGG_FUNC_MAPPING\\b\" -m3 sqlglot/parsers/clickhouse.py", "description": "Check existing parametric aggregate round-trips"}
[tool_result] CombinedParameterizedAgg SELECT sumIf(1)(x) FROM t
ParameterizedAgg SELECT uniqCombined(12)(x) FROM t
ParameterizedAgg SELECT topKWeighted(10)(x, w) FROM t
Aliases SELECT foo(1) AS (x) FROM t
233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
342:        # as AGG_FUNC_MAPPING memoizes all 0- and 1-suffix
[tool_use Bash] {"command": "sed -n 200,262p sqlglot/parsers/clickhouse.py; grep -n \"AGG_FUNC_MAPPING\\[\" -B3 -A10 sqlglot/parsers/clickhouse.py | head -40", "description": "Read ClickHouse aggregate function mapping"}
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
    
…[1067 chars elided]…
for unit in TIMESTAMP_TRUNC_UNITS},
        "ANY": exp.AnyValue.from_arg_list,
        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
        "ARRAYCONCAT": exp.ArrayConcat.from_arg_list,
        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
        "ARRAYEXCEPT": exp.ArrayExcept.from_arg_list,
        "ARRAYSUM": exp.ArraySum.from_arg_list,
        "ARRAYMAX": exp.ArrayMax.from_arg_list,
        "ARRAYMIN": exp.ArrayMin.from_arg_list,
        "ARRAYREVERSE": exp.ArrayReverse.from_arg_list,
[tool_use Bash] {"command": "sed -n 150,200p sqlglot/parsers/clickhouse.py; grep -n '\"GROUPCONCAT\\|\"GROUP_CONCAT\\|\"STRING_AGG\\|GroupConcat' sqlglot/parsers/*.py sqlglot/dialects/*.py | head -20", "description": "Read ClickHouse aggregate names list and GroupConcat usages"}
[tool_result]     "uniqExact",
    "uniqCombined",
    "uniqCombined64",
    "uniqHLL12",
    "uniqTheta",
    "quantile",
    "quantiles",
    "quantileExact",
    "quantilesExact",
    "quantilesExactExclusive",
    "quantileExactLow",
    "quantilesExactLow",
    "quantileExactHigh",
    "quantilesExactHigh",
    "quantileExactWeighted",
    "quantilesExactWeighted",
    "quantileTiming",
    "quantilesTiming",
    "quantileTimingWeighted",
    "quantilesTimingWeighted",
    "quantileDeterministic",
    "q
…[949 chars elided]…
CAT", "LISTAGG"), lambda self: self._parse_group_concat()),
sqlglot/parsers/duckdb.py:186:            ("GROUP_CONCAT", "LISTAGG", "STRINGAGG"), lambda self: self._parse_string_agg()
sqlglot/parsers/mysql.py:156:        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/dialects/dialect.py:2399:    expression: exp.GroupConcat,
[tool_use Bash] {"command": "grep -n \"AGG_FUNCTIONS: set\\|AGG_FUNCTIONS = \" -A8 sqlglot/parsers/clickhouse.py | head -20; grep -n \"uniqCombined(\\|sumIf\\|topKWeighted\" tests/dialects/test_clickhouse.py | head -5", "description": "Locate AGG_FUNCTIONS definition and existing ClickHouse tests"}
[tool_result] 90:AGG_FUNCTIONS = {
91-    "count",
92-    "min",
93-    "max",
94-    "sum",
95-    "avg",
96-    "any",
97-    "stddevPop",
98-    "stddevSamp",
--
313:    AGG_FUNCTIONS = AGG_FUNCTIONS
314-    AGG_FUNCTIONS_SUFFIXES = AGG_FUNCTIONS_SUFFIXES
315-
316-    FUNC_TOKENS = {
317-        *parser.Parser.FUNC_TOKENS,
318-        TokenType.AND,
319-        TokenType.OR,
320-        TokenType.SET,
321-    }
[assistant] Adding `groupConcat` to the ClickHouse aggregate set is the minimal fix: the existing parametric path already handles `f(params)(args)` for every name in that set. Let me make the change and check the round-trips.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110559-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"any\",\n    \"stddevPop\",", "new_string": "    \"any\",\n    \"groupConcat\",\n    \"stddevPop\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110559-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", 'SELECT groupConcat(x) FROM t', 'SELECT groupConcatIf(\\', \\')(x, c) FROM t']:\n    e = sqlglot.parse_one(s, read='clickhouse'); print(type(e.selects[0]).__name__, e.sql('clickhouse'))\n\"", "description": "Verify groupConcat parametric form parses and round-trips"}
[tool_result] Alias SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
AnonymousAggFunc SELECT groupConcat(x) FROM t
CombinedParameterizedAgg SELECT groupConcatIf(', ')(x, c) FROM t
[assistant] The reported query now parses and round-trips. Next I'll add a regression test next to the existing parametric-aggregate tests and run the suite.
[tool_use Bash] {"command": "grep -n \")(x\" tests/dialects/test_clickhouse.py | head -5; grep -n \"def test_clickhouse\\|def test_\" tests/dialects/test_clickhouse.py | head -60 | tail -30", "description": "Find parametric aggregate tests in ClickHouse test file"}
[tool_result] 713:            "SELECT quantilesExactExclusive(0.25, 0.5, 0.75)(x) AS y FROM (SELECT number AS x FROM num)"
15:    def test_clickhouse(self):
737:    def test_clickhouse_values(self):
776:    def test_cte(self):
796:    def test_ternary(self):
834:    def test_parameterization(self):
847:    def test_signed_and_unsigned_types(self):
868:    def test_geom_types(self):
874:    def test_nothing_type(self):
880:    def test_json_type(self):
915:    def test_aggregate_function_column_with_any_keywor
…[232 chars elided]…
p_on_cluster(self):
1550:    def test_datetime_funcs(self):
1582:    def test_convert(self):
1609:    def test_timestr_to_time(self):
1673:    def test_grant(self):
1677:    def test_revoke(self):
1681:    def test_array_join(self):
1708:    def test_traverse_scope(self):
1714:    def test_window_functions(self):
1722:    def test_functions(self):
1728:    def test_array_offset(self):
1751:    def test_to_start_of(self):
1779:    def test_string_split(self):
1807:    def test_sql_security(self):
[tool_use Bash] {"command": "sed -n 1428,1466p tests/dialects/test_clickhouse.py", "description": "Read existing agg functions test for placement"}
[tool_result]     def test_agg_functions(self):
        def extract_agg_func(query):
            return parse_one(query, read="clickhouse").selects[0].this

        self.assertIsInstance(
            extract_agg_func("select quantileGK(100, 0.95) OVER (PARTITION BY id) FROM table"),
            exp.AnonymousAggFunc,
        )
        self.assertIsInstance(
            extract_agg_func(
                "select quantileGK(100, 0.95)(reading) OVER (PARTITION BY id) FROM table"
            ),
            exp.Para
…[515 chars elided]…
prox_top_sum(column, weight) FROM t").selects[0].assert_is(
            exp.AnonymousAggFunc
        )
        self.validate_identity("SELECT approx_top_sum(N)(column, weight) FROM t").selects[
            0
        ].assert_is(exp.ParameterizedAgg)
        self.validate_identity("SELECT approx_top_sum(N, reserved)(column, weight) FROM t").selects[
            0
        ].assert_is(exp.ParameterizedAgg)

    def test_agg_functions_multiple_suffixes(self):
        # Regression test: single-suffix
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110559-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT approx_top_sum(N, reserved)(column, weight) FROM t\").selects[\n            0\n        ].assert_is(exp.ParameterizedAgg)\n\n    def test_agg_functions_multiple_suf
…[170 chars elided]…
xp.ParameterizedAgg)\n\n        self.validate_identity(\n            \"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\"\n        ).selects[0].assert_is(exp.Alias)\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) FROM system.parts\").selects[\n            0\n        ].assert_is(exp.ParameterizedAgg)\n\n    def test_agg_functions_multiple_suffixes(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110559-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -15", "description": "Run ClickHouse dialect tests"}
[tool_result] .............................                                                              [100%]
29 passed, 270 subtests passed in 0.31s
[assistant] ClickHouse tests pass. Running the full project check suite now.
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
1081 passed, 17836 subtests passed in 44.66s
[assistant] `groupConcat(', ')(part_name)` now parses and round-trips in the ClickHouse dialect. The full suite passes: 1081 tests, 17,836 subtests.

**Cause:** `groupConcat` was not in ClickHouse's aggregate-name set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). So the call parsed as a plain `Anonymous` function, and the parser never looked for the second parenthesized list.

**Fix:** I added `"groupConcat"` to `AGG_FUNCTIONS`. The existing parametric-aggregate path then handles it, the same way it handles `quantile`, `uniqCombined` and others. The change also makes combinators like `groupConcatIf(...)(...)` work.

**Behaviour:**
- `groupConcat(', ')(part_name)` → `ParameterizedAgg`, output unchanged.
- `groupConcat(x)` → still prints as `groupConcat(x)`. Its class changes from `Anonymous` to `AnonymousAggFunc`.

**Test:** I added two assertions to `test_agg_functions` in `tests/dialects/test_clickhouse.py`, covering the Superset query with an alias and the bare form.

I haven't committed anything. The change is two lines in the parser plus the test.
