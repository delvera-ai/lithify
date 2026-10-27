# trajectory base-1

final message:
The ClickHouse parser now accepts `groupConcat`'s parametric form, and `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and round-trips unchanged. The full suite passes (1081 tests) and ruff is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/clickhouse.py`**: in `_parse_function`, a `groupConcat` call followed by a second parenthesised group becomes `exp.GroupConcat`. The separator goes in `separator` and the column in `this`. Plain `groupConcat(x)` is untouched.
- **`sqlglot/generators/clickhouse.py`**: a new `groupconcat_sql` writes `groupConcat(<sep>)(<expr>)` when there is a separator and `groupConcat(<expr>)` otherwise.
- **`tests/dialects/test_clickhouse.py`**: identity tests for the Superset query and for the two-argument form, plus a ClickHouse ↔ MySQL cross-dialect check.

**Choices I made**

- I mapped the parametric form to `exp.GroupConcat` rather than the generic `ParameterizedAgg`. That lets it transpile to other dialects, e.g. `GROUP_CONCAT(part_name SEPARATOR ', ')` in MySQL.
- The `groupConcat(<sep>, <max_size>)(<expr>)` form has no slot for the max size on `GroupConcat`, so it falls back to the generic `ParameterizedAgg` and round-trips as before.
- Plain `groupConcat(x)` still parses as an anonymous function, so its existing behaviour is unchanged. Mapping it to `GroupConcat` too would be a separate change.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|GroupConcat\\|parametric\\|params\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/expressions.py | head -80", "description": "Search for groupConcat and parametric handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:1351:            exp.ExcludeColumnConstraint(this=self._parse_index_params())
sqlglot/parser.py:4434:    def _parse_index_params(self) -> exp.IndexParameters:
sqlglot/parser.py:4489:        params = self._parse_index_params()
sqlglot/parser.py:4493:                this=index, table=table, unique=unique, primary=primary, amp=amp, params=params
sqlglot/parser.py:7393:                include=self._parse_index_params
…[282 chars elided]…
m_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9281:        sep = TokenType.COMMA if self.dialect.COPY_PARAMS_ARE_CSV else None
sqlglot/parser.py:9370:        params = self._parse_wrapped(self._parse_copy_parameters, optional=True)
sqlglot/parser.py:9377:            exp.Copy(this=this, kind=kind, credentials=credentials, files=files, params=params)
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "sed -n 7640,7700p sqlglot/parser.py && echo ---- && sed -n 9815,9840p sqlglot/parser.py && echo ---- && grep -n \"class GroupConcat\" -A8 sqlglot/expressions/*.py && echo ---- && grep -n -i \"groupconcat\\|parametric\\|Param\" sqlglot/dialects/clickhouse.py | head -40", "description": "Inspect GroupConcat parsing and ClickHouse dialect"}
[tool_result]             safe=safe,
            action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
            default=default,
        )

    def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disj
…[3483 chars elided]…
xpression, AggFunc):
sqlglot/expressions/aggregate.py-134-    arg_types = {"this": True, "separator": False, "on_overflow": False}
sqlglot/expressions/aggregate.py-135-
sqlglot/expressions/aggregate.py-136-
sqlglot/expressions/aggregate.py-137-class Grouping(Expression, AggFunc):
sqlglot/expressions/aggregate.py-138-    arg_types = {"expressions": True}
sqlglot/expressions/aggregate.py-139-    is_var_len_args = True
sqlglot/expressions/aggregate.py-140-
sqlglot/expressions/aggregate.py-141-
----
[tool_use Bash] {"command": "ls sqlglot/dialects | grep -i click; grep -rn -i \"quantile\\|parametric\\|_parse_function_call\\|ParameterizedAgg\\|Quantile\" sqlglot/dialects/clickhouse.py sqlglot/expressions/*.py sqlglot/parser.py | head -60", "description": "Locate ClickHouse dialect and parametric aggregate handling"}
[tool_result] clickhouse.py
sqlglot/expressions/aggregate.py:37:class ApproxQuantiles(Expression, AggFunc):
sqlglot/expressions/aggregate.py:230:class Quantile(Expression, AggFunc):
sqlglot/expressions/aggregate.py:231:    arg_types = {"this": True, "quantile": True}
sqlglot/expressions/aggregate.py:234:class ApproxQuantile(Quantile):
sqlglot/expressions/aggregate.py:237:        "quantile": True,
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
sqlglot/parser.py:4095:        return self._parse_function_call()
sqlglot/parser.py:6739:        func = self._parse_function_call(
sqlglot/parser.py:6754:    def _parse_function_call(
[tool_use Bash] {"command": "sed -n 1930,1975p sqlglot/expressions/core.py; echo ----; grep -n -i \"ParameterizedAgg\\|parameterized\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/generator.py; echo ----; grep -n -i \"groupconcat\\|group_concat\" -r sqlglot/dialects/clickhouse.py tests/dialects/test_clickhouse.py | head", "description": "Inspect ParameterizedAgg and ClickHouse usages"}
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
…[365 chars elided]…
se}
    is_var_len_args = True


class Hll(Expression, AggFunc):
    arg_types = {"this": True, "expressions": False}
    is_var_len_args = True


class ApproxDistinct(Expression, AggFunc):
----
sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/generator.py:5720:        return self.parameterizedagg_sql(expression)
----
[tool_use Bash] {"command": "sed -n 5705,5722p sqlglot/generator.py; echo ----; grep -n \"ParameterizedAgg\\|params\" sqlglot/parser.py | head -30; echo ----; grep -rn \"ParameterizedAgg\" sqlglot/ tests/ | grep -v \"^sqlglot/generator.py\\|expressions/core.py\" | head -20; echo ----; grep -n -i \"quantile\" sqlglot/dialects/clickhouse.py tests/dialects/test_clickhouse.py | head -20", "description": "Trace ParameterizedAgg usage in parser and tests"}
[tool_result]         kind_sql = kind if kind == "CYCLE" else f"SEARCH {kind} FIRST BY"

        return f"{kind_sql} {this} SET {set}{using}"

    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
        params = self.expressions(expression, key="params", flat=True)
        return self.func(expression.name, *expression.expressions) + f"({params})"

    def anonymousaggfunc_sql(self, expression: exp.AnonymousAggFunc) -> str:
        return self.func(expression.name, *expression.expressi
…[3136 chars elided]…
lickhouse.py:576:            "SELECT quantiles(0.5)(a)",
tests/dialects/test_clickhouse.py:577:            read={"duckdb": "SELECT quantile(a, [0.5])"},
tests/dialects/test_clickhouse.py:578:            write={"clickhouse": "SELECT quantiles(0.5)(a)"},
tests/dialects/test_clickhouse.py:713:            "SELECT quantilesExactExclusive(0.25, 0.5, 0.75)(x) AS y FROM (SELECT number AS x FROM num)"
tests/dialects/test_clickhouse.py:1374:                a AggregateFunction(quantiles(0.5, 0.9), UInt64),
[tool_use Bash] {"command": "sed -n 660,720p sqlglot/parsers/clickhouse.py; echo ----; sed -n 1430,1495p tests/dialects/test_clickhouse.py; echo ----; grep -n -i \"group_concat\\|groupconcat\" sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py", "description": "Read ClickHouse parametric agg parser and tests"}
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
…[4125 chars elided]…
       0
        ].assert_is(exp.CombinedParameterizedAgg)

        # Collision-prone bases: "Map" is both a valid suffix and part of the function name.
        # These must parse as the base function (AnonymousAggFunc), not as sum/min/max + Map suffix.
        self.validate_identity("SELECT sumMap(k, v) FROM t").selects[0].assert_is(
            exp.AnonymousAggFunc
        )
        self.validate_identity("SELECT minMap(k, v) FROM t").selects[0].assert_is(
            exp.AnonymousAggFunc
----
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ')(part_name, x) FROM t\\\", \\\"SELECT groupConcat(1)(a) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(q, read='clickhouse'); print(repr(e.selects[0])[:300]); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', str(ex)[:200])\n\"; grep -n \"_resolve_clickhouse_agg\" -A30 sqlglot/parsers/clickhouse.py | head -60", "description": "Reproduce the groupConcat parse error"}
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
      Literal(this=', ', is_string=True)]),
  expressions=[
    Identifier(this=part_name, quoted=False),
    Identifier(this=x, quoted=False)
…[2954 chars elided]…
 base parser, fix its
710-                # type to be ClickHouse style CombinedAnonymousAggFunc / AnonymousAggFunc
711-                expr.set("this", func)
712-            elif params:
713-                # Params have blocked super()._parse_function() from parsing the following window
714-                # (if that exists) as they're standing between the function call and the window spec
715-                expr = self._parse_window(func)
716-            else:
717-                expr = func
[tool_use Bash] {"command": "grep -n \"def parameterizedagg_sql\\|def groupconcat_sql\\|GroupConcat\\|def combinedparameterizedagg\" -A6 sqlglot/generators/clickhouse.py | head -60; echo ----; grep -n \"def groupconcat_sql\" -A25 sqlglot/generator.py; echo ----; grep -rn -i \"groupconcat\" tests/ sqlglot/ | grep -v \"\\.pyc\" | head -30; echo ----; grep -n \"GroupConcat\\|AGG_FUNC_MAPPING = \\|\\\"Map\\\"\" sqlglot/parsers/clickhouse.py | head", "description": "Check ClickHouse generator and existing groupConcat references"}
[tool_result] ----
----
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
sqlglot/parsers/redshift.py:48:  
…[1513 chars elided]…

sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/presto.py:642:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/spark.py:12:    groupconcat_sql,
sqlglot/generators/spark.py:57:def _groupconcat_sql(self: SparkGenerator, expression: exp.GroupConcat) -> str:
sqlglot/generators/spark.py:65:    return groupconcat_sql(self, expression)
----
215:        "Map",
330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
[tool_use Bash] {"command": "ls sqlglot/generators | grep -i click; grep -n \"parameterizedagg\\|ParameterizedAgg\\|def quantile\\|params\" sqlglot/generators/clickhouse.py | head; echo ----; grep -n \"GroupConcat\" -B2 -A12 sqlglot/generators/base.py 2>/dev/null | head -5; grep -rn \"exp.GroupConcat\" sqlglot/generators/mysql.py sqlglot/generators/clickhouse.py sqlglot/generators/base.py sqlglot/generator.py | head; echo ----; sed -n 2397,2420p sqlglot/dialects/dialect.py; echo ----; sed -n 200,225p sqlglot/parsers/clickhouse.py", "description": "Check ClickHouse generator details and helpers"}
[tool_result] clickhouse.py
----
ugrep: warning: sqlglot/generators/base.py: No such file or directory
sqlglot/generators/mysql.py:159:        exp.GroupConcat: lambda self, e: (
----
def groupconcat_sql(
    self: Generator,
    expression: exp.GroupConcat,
    func_name: str = "LISTAGG",
    sep: str | None = ",",
    within_group: bool = True,
    on_overflow: bool = False,
) -> str:
    this = expression.this
    separator = self.sql(
        expression.args.get("separator") or (exp.Literal.string(sep) if 
…[467 chars elided]…
ialTimeDecayedAvg",
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
        "ForEach",
        "Distinct",
        "OrDefault",
        "OrNull",
        "Resample",
        "ArgMin",
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT quantile(0.5)(a)', read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n\"; grep -n \"_parse_func_params\" -A25 sqlglot/parsers/clickhouse.py | head -40; grep -n \"parameterized\\|ParameterizedAgg\\|def func\\b\" sqlglot/generators/clickhouse.py sqlglot/generator.py | head", "description": "Check quantile round-trip and params parser"}
[tool_result] Quantile(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  quantile=Literal(this=0.5, is_string=False))
SELECT quantile(0.5)(a)
694:            params = self._parse_func_params(anon_func)
695-
696-            if len(parts[1]) > 0:
697-                exp_class: Type[exp.Expr] = (
698-                    exp.CombinedParameterizedAgg if params else exp.CombinedAggFunc
699-                )
700-            else:
701-                exp_class = exp.ParameterizedAgg if params else exp.Ano
…[1265 chars elided]…
his)
728-            return params
729-
730-        return None
731-
732-    def _parse_quantile(self) -> exp.Quantile:
733-        this = self._parse_lambda()
sqlglot/generator.py:4319:    def func(
sqlglot/generator.py:5709:    def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5719:    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/generator.py:5720:        return self.parameterizedagg_sql(expression)
[tool_use Bash] {"command": "sed -n 732,750p sqlglot/parsers/clickhouse.py; grep -n \"_parse_quantile\\|\\\"QUANTILE\\\"\" sqlglot/parsers/clickhouse.py; grep -n \"quantile_sql\\|def quantile\" -A12 sqlglot/generators/clickhouse.py; sed -n 362,372p sqlglot/parsers/clickhouse.py", "description": "Read quantile parser and generator for pattern"}
[tool_result]     def _parse_quantile(self) -> exp.Quantile:
        this = self._parse_lambda()
        params = self._parse_func_params()
        if params:
            return self.expression(exp.Quantile(this=params[0], quantile=this))
        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))

    def _parse_wrapped_id_vars(self, optional: bool = False) -> list[exp.Expr]:
        return super()._parse_wrapped_id_vars(optional=True)

    def _parse_column_def(
        self, t
…[1693 chars elided]…
": lambda self: self.expression(exp.Explode(this=self._parse_expression())),
        "QUANTILE": lambda self: self._parse_quantile(),
        "MEDIAN": lambda self: self._parse_quantile(),
        "COLUMNS": lambda self: self._parse_columns(),
        "TUPLE": lambda self: exp.Struct.from_arg_list(self._parse_function_args(alias=True)),
        "AND": lambda self: exp.and_(*self._parse_function_args(alias=False)),
        "OR": lambda self: exp.or_(*self._parse_function_args(alias=False)),
    }
[tool_use Bash] {"command": "grep -n \"def _try_parse\" -A3 sqlglot/parser.py | head; grep -n \"FUNCTION_PARSERS.get\\|def _parse_function(\" sqlglot/parser.py | head -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT approx_top_sum(N)(column, weight) FROM t', read='clickhouse', write='clickhouse'))\"", "description": "Check try-parse helper and generic param agg output"}
[tool_result] 1979:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
1980-        index = self._index
1981-        error_level = self.error_level
1982-        this: T | None = None
6721:    def _parse_function(
6771:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6791:        parser = self.FUNCTION_PARSERS.get(upper)
['SELECT approx_top_sum(N)(column, weight) FROM t']
[assistant] The cause is clear: `groupConcat` isn't a known ClickHouse aggregate, so `(', ')` parses as a plain call and the following `(part_name)` is left unconsumed. I'll add a branch in the ClickHouse `_parse_function` that turns the parametric form into `exp.GroupConcat`, and a generator method that emits the parametric form back.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "            elif params:\n                # Params have blocked super()._parse_function() from parsing the following window\n                # (if that exists) as they're standing between the function call a
…[611 chars elided]…
he separator is the parameter, the column the argument\n            params = self._parse_func_params(func)\n            if params and len(params) == 1 and len(func.expressions) == 1:\n                func = self.expression(\n                    exp.GroupConcat(this=func.expressions[0], separator=params[0])\n                )\n                expr = self._parse_window(func)\n\n        return expr"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[assistant] The `params` branch silently drops parameters when the shape isn't a single separator plus single column, so I'll fall back to the generic parametric aggregate there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "            params = self._parse_func_params(func)\n            if params and len(params) == 1 and len(func.expressions) == 1:\n                func = self.expression(\n                    exp.GroupConcat(th
…[406 chars elided]…
            expr = self._parse_window(func)\n            elif params:\n                # e.g. groupConcat(<separator>, <max_size>)(<expr>)\n                func = self.expression(\n                    exp.ParameterizedAgg(\n                        this=func.this, expressions=func.expressions, params=params\n                    )\n                )\n                expr = self._parse_window(func)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[assistant] Now the generator, using the auto-discovered `groupconcat_sql` naming, placed near `_quantile_sql`'s neighbours in the class.
[tool_use Bash] {"command": "grep -n \"    def \\|^class \" sqlglot/generators/clickhouse.py | sed -n 1,60p", "description": "List ClickHouse generator methods for placement"}
[tool_result] 69:    def _delta_sql(self: generator.Generator, expression: DATETIME_DELTA) -> str:
166:class ClickHouseGenerator(generator.Generator):
419:    def offset_sql(self, expression: exp.Offset) -> str:
430:    def strtodate_sql(self, expression: exp.StrToDate) -> str:
440:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
448:    def trycast_sql(self, expression: exp.TryCast) -> str:
456:    def _jsonpathsubscript_sql(self, expression: exp.JSONPathSubscript) -> str:
…[1121 chars elided]…
tition) -> str:
612:    def projectiondef_sql(self, expression: exp.ProjectionDef) -> str:
615:    def nestedjsonselect_sql(self, expression: exp.NestedJSONSelect) -> str:
618:    def is_sql(self, expression: exp.Is) -> str:
627:    def in_sql(self, expression: exp.In) -> str:
635:    def not_sql(self, expression: exp.Not) -> str:
645:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
658:    def timestamptrunc_sql(self, expression: exp.TimestampTrunc) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/generators/clickhouse.py", "old_string": "    def prewhere_sql(self, expression: exp.PreWhere) -> str:", "new_string": "    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:\n        separator = expression.args.get(\"separator\")\n        if separator:\n            args = f\"({self.sql(expression, 'this')})\"\n            return self.func(\"groupConcat\", separator) + args\n\n        return self.func(\"groupConcat\", expression.this)\n\n    def prewhere_sql(self, expression: exp.PreWhere) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/generators/clickhouse.py has been updated successfully.
[assistant] Now I'll add tests next to the existing quantile tests, then run the ClickHouse suite and check the output directly.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor q in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ', 10)(x) FROM t\\\", \\\"SELECT groupConcat(
…[23 chars elided]…
N BY y) FROM t\\\"]:\n    e = sqlglot.parse_one(q, read='clickhouse'); print(e.sql('clickhouse')); \nprint(sqlglot.transpile(\\\"SELECT groupConcat(', ')(part_name) FROM t\\\", read='clickhouse', write='mysql'))\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(part_name SEPARATOR ', ') FROM t\\\", read='mysql', write='clickhouse'))\n\"", "description": "Verify round-trip and cross-dialect output"}
[tool_result] SELECT groupConcat(part_name)(', ') AS concatenated FROM system.parts
SELECT groupConcat(part_name) FROM t
SELECT groupConcat(', ', 10)(x) FROM t
SELECT groupConcat(x)(', ') OVER (PARTITION BY y) FROM t
["SELECT GROUP_CONCAT(', ' SEPARATOR part_name) FROM t"]
["SELECT groupConcat(', ')(part_name) FROM t"]
[assistant] The output is reversed: in this codebase's ClickHouse convention, the first parenthesised group lands in `expressions` and the second in `params` (the same as `quantile(0.5)(a)`). So the separator is `func.expressions[0]` and the column is `params[0]`. I'll fix the mapping.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "            params = self._parse_func_params(func)\n            if params and len(params) == 1 and len(func.expressions) == 1:\n                func = self.expression(\n                    exp.GroupConcat(this=func.expressions[0], separator=params[0])\n                )", "new_string": "            params = self._parse_func_params(func)\n            if params and len(params) == 1 and len(func.expressions) == 1:\n                func = self.expression(\n                    exp.GroupConcat(this=params[0], separator=func.expressions[0])\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor q in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ', 10)(x) FROM t\\\", \\\"SELECT groupConcat(
…[145 chars elided]…
rse_one(\\\"SELECT groupConcat(', ')(part_name) FROM t\\\", read='clickhouse').selects[0]))\nprint(sqlglot.transpile(\\\"SELECT groupConcat(', ')(part_name) FROM t\\\", read='clickhouse', write='mysql'))\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(part_name SEPARATOR ', ') FROM t\\\", read='mysql', write='clickhouse'))\n\"", "description": "Re-verify round-trip after fixing argument mapping"}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(part_name) FROM t
SELECT groupConcat(', ', 10)(x) FROM t
SELECT groupConcat(', ')(x) OVER (PARTITION BY y) FROM t
GroupConcat(
  this=Column(
    this=Identifier(this=part_name, quoted=False)),
  separator=Literal(this=', ', is_string=True))
["SELECT GROUP_CONCAT(part_name SEPARATOR ', ') FROM t"]
["SELECT groupConcat(', ')(part_name) FROM t"]
[assistant] The round-trip and cross-dialect output are correct now. Next, tests: I'll add identity tests beside the existing quantile identities and a cross-dialect check beside the quantile `validate_all`.
[tool_use Bash] {"command": "sed -n 96,106p tests/dialects/test_clickhouse.py; echo ----; sed -n 558,582p tests/dialects/test_clickhouse.py", "description": "View existing quantile test sections"}
[tool_result]         self.validate_identity("SELECT * FROM foo GLOBAL ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL LEFT ANY JOIN bla")
        self.validate_identity("SELECT quantile(0.5)(a)")
        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t
…[585 chars elided]…
 },
        )
        self.validate_all(
            "SELECT quantiles(0.5, 0.4)(a)",
            read={"duckdb": "SELECT quantile(a, [0.5, 0.4])"},
            write={"clickhouse": "SELECT quantiles(0.5, 0.4)(a)"},
        )
        self.validate_all(
            "SELECT quantiles(0.5)(a)",
            read={"duckdb": "SELECT quantile(a, [0.5])"},
            write={"clickhouse": "SELECT quantiles(0.5)(a)"},
        )

        self.validate_identity("SELECT isNaN(x)")
        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\n            \"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\"\n        )\n        self.validate_identity(\"SELECT groupConcat(', ', 10)(a) FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_all(\n            \"SELECT quantiles(0.5)(a)\",\n            read={\"duckdb\": \"SELECT quantile(a, [0.5])\"},\n            write={\"clickhouse\": \"SELECT quantiles(0.5)(a)\"},\n  
…[174 chars elided]…
rite={\"clickhouse\": \"SELECT quantiles(0.5)(a)\"},\n        )\n        self.validate_all(\n            \"SELECT groupConcat(', ')(a)\",\n            read={\"mysql\": \"SELECT GROUP_CONCAT(a SEPARATOR ', ')\"},\n            write={\n                \"clickhouse\": \"SELECT groupConcat(', ')(a)\",\n                \"mysql\": \"SELECT GROUP_CONCAT(a SEPARATOR ', ')\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Now the ClickHouse tests, then the full suite using the project's test command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -15", "description": "Run ClickHouse dialect tests"}
[tool_result] .............................                                                           [100%]
29 passed, 273 subtests passed in 0.24s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ----; (ruff --version && ruff check sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py && ruff format --check sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -8", "description": "Run full test suite and lint changed files"}
[tool_result] ..................... [ 22%]
....................... [ 24%]
................... [ 26%]
........................... [ 28%]
.............................................. [ 32%]
.......................................................................................................................................................................... [ 48%]
....................................................... [ 53%]
............................................ [ 57%]
...............................
…[95 chars elided]…
........ [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 96%]
.......................... [ 98%]
...............                 [100%]
1081 passed, 17839 subtests passed in 56.14s
----
ruff 0.15.6
All checks passed!
3 files already formatted
[assistant] The ClickHouse parser now accepts `groupConcat`'s parametric form, and `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and round-trips unchanged. The full suite passes (1081 tests) and ruff is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/clickhouse.py`**: in `_parse_function`, a `groupConcat` call followed by a second parenthesised group becomes `exp.GroupConcat`. The separator goes in `separator` and the column in `this`. Plain `groupConcat(x)` is untouched.
- **`sqlglot/generators/clickhouse.py`**: a new `groupconcat_sql` writes `groupConcat
…[194 chars elided]…
us a ClickHouse ↔ MySQL cross-dialect check.

**Choices I made**

- I mapped the parametric form to `exp.GroupConcat` rather than the generic `ParameterizedAgg`. That lets it transpile to other dialects, e.g. `GROUP_CONCAT(part_name SEPARATOR ', ')` in MySQL.
- The `groupConcat(<sep>, <max_size>)(<expr>)` form has no slot for the max size on `GroupConcat`, so it falls back to the generic `ParameterizedAgg` and round-trips as before.
- Plain `groupConcat(x)` still parses as an anonymous function, so its existing behaviour is unchanged. Mapping it to `GroupConcat` too would be a separate change.
