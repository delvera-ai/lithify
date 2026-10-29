# trajectory base-1

final message:
The ClickHouse `groupConcat(', ')(part_name)` form now parses and round-trips unchanged. The full suite passes (1081 tests), and ruff format is clean on both edited files.

**Cause:** `groupConcat` wasn't in the ClickHouse aggregate-name set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). So `groupConcat(', ')` was parsed as an ordinary anonymous function, and the trailing `(part_name)` was never read as parameters, which caused the `Invalid expression` error.

**Fix:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. It now goes through the same `ParameterizedAgg` path that already handles `groupUniqArray(2)(a)` and `quantile(0.5)(a)`. The separator is the parameter and the column is the argument.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the Superset query next to the other parametric-aggregate cases.

The plain form `groupConcat(a, ',')` and the windowed form `groupConcat(', ')(a) OVER (...)` also still round-trip.

I did not add cross-dialect transpilation for this form. Converting it to another dialect's `GROUP_CONCAT`/`LISTAGG` would be a separate change, since the separator-as-parameter semantics would need mapping.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|parametric\\|quantile\\|PARAMETER\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/generator.py | head -80; grep -rn -i \"groupconcat\\|group_concat\" sqlglot/expressions.py | head; grep -n -i \"groupconcat\\|parametric\" tests/dialects/test_clickhouse.py | head -30", "description": "Search for parametric aggregate handling"}
[tool_result] sqlglot/generator.py:183:        exp.ParameterStyleProperty: lambda self, e: f"PARAMETER STYLE {self.sql(e, 'this')}",
sqlglot/generator.py:347:    # Separator for IN/OUT parameter mode (Oracle uses " " for "IN OUT", PostgreSQL uses "" for "INOUT")
sqlglot/generator.py:499:    # Whether parameters from COPY statement are wrapped in parentheses
sqlglot/generator.py:529:    # Whether the text pattern/fill (3rd) parameter of RPAD()/LPAD() is optional (defaults to space)
sqlglot/generator.py:642:   
…[3158 chars elided]…
parser.py:9360:            # Backtrack one token since we've consumed the lhs of a parameter assignment here.
sqlglot/parser.py:9361:            # This can happen for Snowflake dialect. Instead, we'd like to parse the parameter
sqlglot/parser.py:9370:        params = self._parse_wrapped(self._parse_copy_parameters, optional=True)
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 7640,7700p sqlglot/parser.py; sed -n 9820,9840p sqlglot/parser.py; grep -n \"class GroupConcat\\|class ParameterizedAgg\\|class CombinedParameterizedAgg\" -A8 sqlglot/expressions/*.py; sed -n 5705,5722p sqlglot/generator.py; grep -n \"ParameterizedAgg\\|PARAMETERIZED\" sqlglot/dialects/clickhouse.py sqlglot/parser.py | head -30", "description": "Inspect group concat parsing and param agg classes"}
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
…[5221 chars elided]…
ressions) + f"({params})"

    def anonymousaggfunc_sql(self, expression: exp.AnonymousAggFunc) -> str:
        return self.func(expression.name, *expression.expressions)

    def combinedaggfunc_sql(self, expression: exp.CombinedAggFunc) -> str:
        return self.anonymousaggfunc_sql(expression)

    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
        return self.parameterizedagg_sql(expression)

    def show_sql(self, expression: exp.Show) -> str:
[tool_use Bash] {"command": "grep -rn \"ParameterizedAgg\\|parameterized\" sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/expressions/*.py | head -30; grep -n \"groupconcat\\|GROUP_CONCAT\\|GroupConcat\" sqlglot/dialects/clickhouse.py sqlglot/dialects/mysql.py | head; grep -n \"PARAM\" tests/dialects/test_clickhouse.py | head", "description": "Find ParameterizedAgg usages across code"}
[tool_result] sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
[tool_use Bash] {"command": "grep -n -i \"quantile\\|(0\\.\\|)(\" tests/dialects/test_clickhouse.py | head -30; grep -n \"def _parse_function\\b\\|def _parse_function_call\\|FUNCTION_PARSERS\\|ParameterizedAgg\\|_parse_lambda\" sqlglot/parser.py | head; grep -n \"class Parser\" -A3 sqlglot/dialects/clickhouse.py; grep -n \"FUNCTIONS\\|def _parse_\" sqlglot/dialects/clickhouse.py | head -60", "description": "Check existing ClickHouse parametric tests and parser hooks"}
[tool_result] 98:        self.validate_identity("SELECT quantile(0.5)(a)")
99:        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
100:        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
101:        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
103:        self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
104:        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
105:        self.validate_identity("SELECT histogram
…[2024 chars elided]…
allable]] = {
5278:        self.NO_PAREN_FUNCTION_PARSERS["PRIOR"] = lambda self: self.expression(
5282:        self.NO_PAREN_FUNCTION_PARSERS.pop("PRIOR")
6428:            if parts is None and token.text.upper() in self.NO_PAREN_FUNCTION_PARSERS:
6721:    def _parse_function(
6752:        return self._parse_csv(lambda: self._parse_lambda(alias=alias))
6754:    def _parse_function_call(
6771:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
17:    NORMALIZE_FUNCTIONS: bool | str = False
[tool_use Bash] {"command": "grep -n \"param\\|Param\" sqlglot/dialects/clickhouse.py | head -60; sed -n 6721,6760p sqlglot/parser.py", "description": "Locate parametric aggregate handling in ClickHouse dialect"}
[tool_result]     def _parse_function(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
        # This allows us to also parse {fn <function>} syntax (Snowflake, MySQL support this)
        # See: https://community.snowflake.com/s/article/SQL-Escape-Sequences
        fn_syntax = False
        if (
            self._match(TokenType.L_BRACE, advance=False)
      
…[300 chars elided]…
    any_token=any_token,
        )

        if fn_syntax:
            self._match(TokenType.R_BRACE)

        return func

    def _parse_function_args(self, alias: bool = False) -> list[exp.Expr]:
        return self._parse_csv(lambda: self._parse_lambda(alias=alias))

    def _parse_function_call(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 6760,6830p sqlglot/parser.py; grep -n \"def _parse_function_call\" -B2 sqlglot/dialects/clickhouse.py; grep -n \"class Parser\" sqlglot/dialects/clickhouse.py", "description": "Read function call parsing logic"}
[tool_result]     ) -> exp.Expr | None:
        if not self._curr:
            return None

        comments = self._curr.comments
        prev = self._prev
        token = self._curr
        token_type = self._curr.token_type
        this: str | exp.Expr = self._curr.text
        upper = self._curr.text.upper()

        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
        if optional_parens and parser and token_type not in self.INVALID_FUNC_NAME_TOKENS:
            self._advance()
            return se
…[1795 chars elided]…
urr else None
            if known_function and post_func_comments:
                # If the user-inputted comment "/* sqlglot.anonymous */" is following the function
                # call we'll construct it as exp.Anonymous, even if it's "known"
                if any(
                    comment.lstrip().startswith(exp.SQLGLOT_ANONYMOUS)
                    for comment in post_func_comments
                ):
                    known_function = False

            if alias and known_function:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT quantile(0.5)(a)','SELECT groupConcat(\\', \\')(part_name) AS c FROM system.parts','SELECT groupUniqArray(2)(a)']:\n    try:\n        e=sqlglot.parse_one(s,read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR',ex)\n\"; grep -rn \"ClickHouse\\|clickhouse\" sqlglot/parser.py | head; grep -n \"ParameterizedAgg\\|parameterized\" sqlglot/*.py sqlglot/dialects/*.py | head", "description": "Test current ClickHouse parse behavior for parametric aggregates"}
[tool_result] Quantile(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  quantile=Literal(this=0.5, is_string=False))
SELECT quantile(0.5)(a)
ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m c FROM system.parts
ParameterizedAgg(
  this=groupUniqArray,
  expressions=[
    Literal(this=2, is_string=False)],
  params=[
    Column(
      this=Identifier(this=a, quoted=False))])
SELECT groupUniqArray(2)(a)
sqlglot/parser.py:2188:    # https://
…[653 chars elided]…
gg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
sqlglot/generator.py:5720:        return self.parameterizedagg_sql(expression)
sqlglot/transforms.py:257:def remove_precision_parameterized_types(expression: exp.Expr) -> exp.Expr:
sqlglot/transforms.py:259:    Some dialects only allow the precision for parameterized types to be defined in the DDL and not in
sqlglot/transforms.py:260:    other expressions. This transforms removes the precision from parameterized types in expressions.
[tool_use Bash] {"command": "grep -rn \"ParameterizedAgg\\|Quantile\\b\" sqlglot/ | grep -v \"\\.pyc\" | head -20; grep -n \"class Quantile\" -A4 sqlglot/expressions/*.py", "description": "Find all references to parameterized aggregate classes"}
[tool_result] sqlglot/transforms.py:568:        return expression.replace(exp.ApproxQuantile(this=input_value, quantile=quantile))
sqlglot/parsers/singlestore.py:120:        "APPROX_PERCENTILE": lambda args, dialect: exp.ApproxQuantile(
sqlglot/parsers/hive.py:55:        "PERCENTILE": lambda self: self._parse_quantile_function(exp.Quantile),
sqlglot/parsers/hive.py:56:        "PERCENTILE_APPROX": lambda self: self._parse_quantile_function(exp.ApproxQuantile),
sqlglot/generator.py:5709:    def parameterizedagg
…[1310 chars elided]…
ntile: {"annotator": lambda self, e: self._annotate_by_args(e, "quantile")},
sqlglot/typing/__init__.py:96:            exp.ApproxQuantile,
sqlglot/typing/__init__.py:111:            exp.Quantile,
sqlglot/expressions/aggregate.py:230:class Quantile(Expression, AggFunc):
sqlglot/expressions/aggregate.py-231-    arg_types = {"this": True, "quantile": True}
sqlglot/expressions/aggregate.py-232-
sqlglot/expressions/aggregate.py-233-
sqlglot/expressions/aggregate.py-234-class ApproxQuantile(Quantile):
[tool_use Bash] {"command": "sed -n 660,745p sqlglot/parsers/clickhouse.py; grep -n \"GROUPCONCAT\\|groupconcat\\|GroupConcat\\|\\\"GROUP\" sqlglot/parsers/clickhouse.py sqlglot/parsers/mysql.py | head", "description": "Read ClickHouse parametric aggregate parsing code"}
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
…[2610 chars elided]…
e_wrapped_id_vars(self, optional: bool = False) -> list[exp.Expr]:
        return super()._parse_wrapped_id_vars(optional=True)

    def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        if self._match(TokenType.DOT):
sqlglot/parsers/mysql.py:156:        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
sqlglot/parsers/mysql.py:429:        for_group = self._parse_string() if self._match_text_seq("FOR", "GROUP") else None
[tool_use Bash] {"command": "grep -n \"_resolve_clickhouse_agg\" -A30 sqlglot/parsers/clickhouse.py | head -60; grep -n \"AGG_FUNCS\\|AGG_SUFFIX\" sqlglot/parsers/clickhouse.py sqlglot/dialects/clickhouse.py | head", "description": "Read clickhouse aggregate name resolution"}
[tool_result] 333:    def _resolve_clickhouse_agg(cls, name: str) -> tuple[str, Sequence[str]] | None:
334-        # ClickHouse allows chaining multiple combinators on aggregate functions.
335-        # See https://clickhouse.com/docs/sql-reference/aggregate-functions/combinators
336-        # N.B. this resolution allows any suffix stack, including ones that ClickHouse rejects
337-        # syntactically such as sumMergeMerge (due to repeated adjacent suffixes)
338-
339-        # Until we are able to identify
…[2201 chars elided]…
 base parser, fix its
710-                # type to be ClickHouse style CombinedAnonymousAggFunc / AnonymousAggFunc
711-                expr.set("this", func)
712-            elif params:
713-                # Params have blocked super()._parse_function() from parsing the following window
714-                # (if that exists) as they're standing between the function call and the window spec
715-                expr = self._parse_window(func)
716-            else:
717-                expr = func
[tool_use Bash] {"command": "grep -n \"AGG_FUNC_MAPPING\\|AGG_FUNCTIONS\\b\\|AGG_FUNCTIONS =\" sqlglot/parsers/clickhouse.py | head; grep -n \"^AGG_FUNCTIONS\\|^AGG_FUNC_MAPPING\" -A6 sqlglot/parsers/clickhouse.py | head -40; grep -rn \"groupconcat\" -i sqlglot/ tests/ | head", "description": "Check aggregate function list and groupconcat mentions"}
[tool_result] 90:AGG_FUNCTIONS = {
233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
234:    f"{f}{sfx}": (f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
235:} | {f: (f, None) for f in AGG_FUNCTIONS}
313:    AGG_FUNCTIONS = AGG_FUNCTIONS
330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
342:        # as AGG_FUNC_MAPPING memoizes all 0- and 1-suffix
344:        while (parts := AGG_FUNC_MAPPING.get(name)) is None:
90:AGG_FUNCTIONS = {
91-    "count",
92-    "min",
93-    "max",
94-    "
…[847 chars elided]…
args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/typing/__init__.py:222:            exp.GroupConcat,
sqlglot/typing/bigquery.py:171:            exp.GroupConcat,
sqlglot/dialects/dialect.py:2397:def groupconcat_sql(
[tool_use Bash] {"command": "sed -n 88,210p sqlglot/parsers/clickhouse.py | tr -s ' \\n' ' ' | head -c 4000; echo; sed -n 2390,2420p sqlglot/dialects/dialect.py; grep -n \"groupConcat\\|groupconcat\\|GROUP_CONCAT\" -i tests/dialects/test_clickhouse.py | head", "description": "Read the ClickHouse aggregate function list"}
[tool_result]  AGG_FUNCTIONS = { "count", "min", "max", "sum", "avg", "any", "stddevPop", "stddevSamp", "varPop", "varSamp", "corr", "covarPop", "covarSamp", "entropy", "exponentialMovingAverage", "intervalLengthSum", "kolmogorovSmirnovTest", "mannWhitneyUTest", "median", "rankCorr", "sumKahan", "studentTTest", "welchTTest", "anyHeavy", "anyLast", "boundingRatio", "first_value", "last_value", "argMin", "argMax", "avgWeighted", "topK", "approx_top_sum", "topKWeighted", "deltaSum", "deltaSumTimestamp", "groupAr
…[2110 chars elided]…
: bool = False,
) -> str:
    this = expression.this
    separator = self.sql(
        expression.args.get("separator") or (exp.Literal.string(sep) if sep else None)
    )

    on_overflow_sql = self.sql(expression, "on_overflow")
    on_overflow_sql = f" ON OVERFLOW {on_overflow_sql}" if (on_overflow and on_overflow_sql) else ""

    if isinstance(this, exp.Limit) and this.this:
        limit = this
        this = limit.this.pop()
    else:
        limit = None

    order = this.find(exp.Order)
[assistant] The cause is clear: `groupConcat` isn't in the ClickHouse `AGG_FUNCTIONS` set, so `groupConcat(', ')` is parsed as a plain anonymous function and the trailing `(part_name)` is never treated as parameters. Adding it to that set should route it through the existing `ParameterizedAgg` path, the same one `groupUniqArray(2)(a)` uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupBitmapXor\",\n", "new_string": "    \"groupBitmapXor\",\n    \"groupConcat\",\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "offset": 104, "limit": 6}
[tool_result] 104	        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
105	        self.validate_identity("SELECT histogram(5)(a)")
106	        self.validate_identity("SELECT groupUniqArray(2)(a)")
107	        self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
108	        self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
109	        self.validate_identity("jaroWinklerSimilarity('hello', 'world')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", 'SELECT groupConcat(a, \\',\\') FROM t', 'SELECT groupConcat(\\', \\')(a) OVER (PARTITION BY b) FROM t']:\n    e=sqlglot.parse_one(s,read='clickhouse'); print(e.sql('clickhouse'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5", "description": "Verify parse round-trip and run ClickHouse dialect tests"}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(a, ',') FROM t
SELECT groupConcat(', ')(a) OVER (PARTITION BY b) FROM t
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.34s
[assistant] Targeted tests pass. Now the full project check suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ..................................... [ 47%]
....................................................................... [ 54%]
.................................................................................................................................................................................... [ 70%]
..................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 50.09s
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[tool_use Bash] {"command": "grep -n \"line-length\" pyproject.toml setup.cfg ruff.toml 2>/dev/null; awk 'length > 100 {print FILENAME\": \"FNR\": \"length}' tests/dialects/test_clickhouse.py | head -3; (<work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py 2>&1 || true) | tail -2", "description": "Check line length and formatting of edited files"}
[tool_result] pyproject.toml:47:line-length = 100
tests/dialects/test_clickhouse.py: 107: 103
tests/dialects/test_clickhouse.py: 143: 128
tests/dialects/test_clickhouse.py: 146: 261
Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --diff tests/dialects/test_clickhouse.py 2>&1 | head -20", "description": "Show the formatting diff for the test file"}
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
         self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
         self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
         self.validate_identity("jaroWinklerSimilarity('hello', 'world')")

1 file would be reformatted
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n", "new_string": "        self.validate_identity(\n            \"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-111747-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -1", "description": "Recheck formatting and ClickHouse tests"}
[tool_result] 2 files already formatted
29 passed, 270 subtests passed in 0.18s
[assistant] The ClickHouse `groupConcat(', ')(part_name)` form now parses and round-trips unchanged. The full suite passes (1081 tests), and ruff format is clean on both edited files.

**Cause:** `groupConcat` wasn't in the ClickHouse aggregate-name set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). So `groupConcat(', ')` was parsed as an ordinary anonymous function, and the trailing `(part_name)` was never read as parameters, which caused the `Invalid expression` error.

**Fix:**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to `AGG_FUNCTIONS`. It now goes through the same `Parameterize
…[8 chars elided]…
th that already handles `groupUniqArray(2)(a)` and `quantile(0.5)(a)`. The separator is the parameter and the column is the argument.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the Superset query next to the other parametric-aggregate cases.

The plain form `groupConcat(a, ',')` and the windowed form `groupConcat(', ')(a) OVER (...)` also still round-trip.

I did not add cross-dialect transpilation for this form. Converting it to another dialect's `GROUP_CONCAT`/`LISTAGG` would be a separate change, since the separator-as-parameter semantics would need mapping.
