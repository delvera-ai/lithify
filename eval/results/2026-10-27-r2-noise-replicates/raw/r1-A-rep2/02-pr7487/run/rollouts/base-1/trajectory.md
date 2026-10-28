# trajectory base-1

final message:
`groupConcat` now accepts its parametric form in the ClickHouse dialect. `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and round-trips unchanged.

The cause was that `groupConcat` was missing from the ClickHouse aggregate-name registry. Without it, the parser treated `groupConcat(', ')` as a plain function call and then choked on the `(part_name)` that followed.

**Changes**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to the `AGG_FUNCTIONS` list. The existing parametric-aggregate machinery then handles it, and combinators like `groupConcatIf(...)(...)` work too.
- `tests/dialects/test_clickhouse.py`: in `test_agg_functions`, added a round-trip check for the parametric form and a check that the plain `groupConcat(part_name)` still parses as an anonymous aggregate.

**Verification**
- Full test suite: 1081 passed.
- `ruff format --check` and `ruff check` pass on both changed files.

**Choices and limits**
- I did not map ClickHouse's `groupConcat` to the shared `exp.GroupConcat` class. ClickHouse's plain `groupConcat(x)` uses a default separator, and the ClickHouse generator has no handler for `GroupConcat`, so that mapping would break the plain form's round-trip. Keeping it as a generic aggregate is the smaller, safer change.
- Transpiling to other dialects emits `GROUPCONCAT(', ')(part_name)`, which is not valid in those dialects. That is the same behaviour as other ClickHouse-only aggregates, so I left it alone.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|parametric\\|quantile\\|PARAMETRIC\" sqlglot/dialects/clickhouse.py | head -60; grep -rn -i \"groupconcat\\|GroupConcat\" sqlglot/expressions.py sqlglot/dialects/clickhouse.py tests/dialects/test_clickhouse.py | head -30", "description": "Search ClickHouse dialect for parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot/ | head -50; grep -rn -i \"groupconcat\\|group_concat\" sqlglot/ tests/dialects/test_clickhouse.py | head -30; grep -n -i \"parametric\\|PARAMETER\" sqlglot/dialects/clickhouse.py | head -40", "description": "Locate groupConcat and parametric handling in source"}
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
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686: 
…[1907 chars elided]…
       exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/doris.py:61:            "GROUP_CONCAT", e.this, e.args.get("separator") or exp.Literal.string(",")
sqlglot/generators/duckdb.py:25:    groupconcat_sql,
sqlglot/generators/duckdb.py:1598:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, within_group=False),
sqlglot/generators/mysql.py:140:        exp.ArrayAgg: rename_func("GROUP_CONCAT"),
sqlglot/generators/mysql.py:159:        exp.GroupConcat: lambda self, e: (
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators | grep -i click; grep -rn -i \"param\" sqlglot/parsers/clickhouse.py | head -40; grep -n -i \"quantile\\|PARAMETRIC\\|parameters\" sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py sqlglot/expressions/*.py | head -40", "description": "Find ClickHouse parser/generator and parametric handling"}
[tool_result] clickhouse.py
clickhouse.py
sqlglot/parsers/clickhouse.py:454:        TokenType.L_BRACE: lambda self: self._parse_query_parameter(),
sqlglot/parsers/clickhouse.py:534:    def _parse_query_parameter(self) -> exp.Expr | None:
sqlglot/parsers/clickhouse.py:537:        https://clickhouse.com/docs/en/sql-reference/syntax#defining-and-using-query-parameters
sqlglot/parsers/clickhouse.py:694:            params = self._parse_func_params(anon_func)
sqlglot/parsers/clickhouse.py:698:                    ex
…[3279 chars elided]…
     "MEDIAN": lambda self: self._parse_quantile(),
sqlglot/parsers/clickhouse.py:537:        https://clickhouse.com/docs/en/sql-reference/syntax#defining-and-using-query-parameters
sqlglot/parsers/clickhouse.py:732:    def _parse_quantile(self) -> exp.Quantile:
sqlglot/parsers/clickhouse.py:736:            return self.expression(exp.Quantile(this=params[0], quantile=this))
sqlglot/parsers/clickhouse.py:737:        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))
[tool_use Bash] {"command": "sed -n 140,200p sqlglot/parsers/clickhouse.py; sed -n 660,740p sqlglot/parsers/clickhouse.py; grep -n \"ParameterizedAgg\\|CombinedParameterizedAgg\" -A6 sqlglot/expressions/aggregate.py sqlglot/expressions/*.py | head -40; grep -n \"parameterizedagg\\|ParameterizedAgg\\|params\" sqlglot/generators/clickhouse.py", "description": "Read ClickHouse aggregate parsing and related expression classes"}
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
    "quantiles",
    "quantileExact",
    "quantilesExact",
    "quantilesExactExclusive",
    "quantileExactLow",
    "quantilesExactLow",
    "quantileExactHigh",
    "quantilesExactHigh",
    "quantileExactWeighted",
    "quant
…[4600 chars elided]…
945-    is_var_len_args = True
--
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
sqlglot/expressions/core.py-1962-    arg_types = {"this": True, "expressions": True, "params": True}
sqlglot/expressions/core.py-1963-
sqlglot/expressions/core.py-1964-
sqlglot/expressions/core.py-1965-class HashAgg(Expression, AggFunc):
sqlglot/expressions/core.py-1966-    arg_types = {"this": True, "expressions": False}
sqlglot/expressions/core.py-1967-    is_var_len_args = True
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(1)(x) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])[:400]); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"groupArray\\|_resolve_clickhouse_agg\" -A3 sqlglot/parsers/clickhouse.py | head -60; grep -rn -i \"groupconcat\" tests/dialects/test_clickhouse.py | head", "description": "Reproduce the ClickHouse groupConcat parse error"}
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
127:    "
…[327 chars elided]…
nce[str]] | None:
334-        # ClickHouse allows chaining multiple combinators on aggregate functions.
335-        # See https://clickhouse.com/docs/sql-reference/aggregate-functions/combinators
336-        # N.B. this resolution allows any suffix stack, including ones that ClickHouse rejects
--
690:        parts = self._resolve_clickhouse_agg(func.this) if isinstance(func, exp.Anonymous) else None
691-
692-        if parts:
693-            anon_func: exp.Anonymous = t.cast(exp.Anonymous, func)
[tool_use Bash] {"command": "sed -n 110,126p sqlglot/parsers/clickhouse.py; sed -n 326,362p sqlglot/parsers/clickhouse.py; grep -n -i \"groupArray\\|ParameterizedAgg\\|quantile(\" tests/dialects/test_clickhouse.py | head -20", "description": "Read aggregate name registry and existing ClickHouse tests"}
[tool_result]     "rankCorr",
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
        *parser.Parser.ID_VAR_TOKENS,
        TokenType.LIKE,
    }

    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING

    @classmethod
    def _resolve_clickhouse_agg(cls, name: str) -> tuple[str, Sequence[s
…[1580 chars elided]…
quantile(0.5)(a)",
563:                "duckdb": "SELECT quantile(a, 0.5)",
567:                "clickhouse": "SELECT quantile(0.5)(a)",
572:            read={"duckdb": "SELECT quantile(a, [0.5, 0.4])"},
577:            read={"duckdb": "SELECT quantile(a, [0.5])"},
1440:            exp.ParameterizedAgg,
1450:            exp.CombinedParameterizedAgg,
1460:        ].assert_is(exp.ParameterizedAgg)
1463:        ].assert_is(exp.ParameterizedAgg)
1487:        ].assert_is(exp.CombinedParameterizedAgg)
[tool_use Bash] {"command": "grep -n \"AGG_FUNCTIONS\\b\\|AGG_FUNC_MAPPING\\s*=\\|AGG_FUNCTIONS = \\|^AGG\" sqlglot/parsers/clickhouse.py | head; sed -n 1425,1470p tests/dialects/test_clickhouse.py; grep -n \"groupArray\" tests/dialects/test_clickhouse.py | head -5", "description": "Check AGG function list definition and existing agg tests"}
[tool_result] 90:AGG_FUNCTIONS = {
210:AGG_FUNCTIONS_SUFFIXES: list[str] = sorted(
233:AGG_FUNC_MAPPING: Mapping[str, tuple[str, str | None]] = {
234:    f"{f}{sfx}": (f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
235:} | {f: (f, None) for f in AGG_FUNCTIONS}
313:    AGG_FUNCTIONS = AGG_FUNCTIONS
330:    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
        self.validate_identity("DROP TABLE t SYNC")
        self.validate_identity("DROP DATABASE IF EXISTS d SYNC")

    def test_agg_functions(self):
 
…[1110 chars elided]…
ity("SELECT approx_top_sum(N)(column, weight) FROM t").selects[
            0
        ].assert_is(exp.ParameterizedAgg)
        self.validate_identity("SELECT approx_top_sum(N, reserved)(column, weight) FROM t").selects[
            0
        ].assert_is(exp.ParameterizedAgg)

    def test_agg_functions_multiple_suffixes(self):
        # Regression test: single-suffix
        self.validate_identity("SELECT uniqExactIf(x, y) FROM t").selects[0].assert_is(
            exp.CombinedAggFunc
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155227-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupArray\",\n    \"groupArrayLast\",", "new_string": "    \"groupConcat\",\n    \"groupArray\",\n    \"groupArrayLast\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155227-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ')(part_name) OVER (PARTITION BY id) FROM t\\\", \\\"SELECT groupConcatIf(', ')(part_name, x > 1) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='clickhouse'); print(type(e.selects[0]).__name__, '|', e.sql('clickhouse'))\n    print(e.sql('duckdb'))\n\"", "description": "Verify groupConcat parametric parse and round-trip"}
[tool_result] Alias | SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT GROUPCONCAT(', ')(part_name) AS concatenated FROM system.parts
AnonymousAggFunc | SELECT groupConcat(part_name) FROM t
SELECT GROUPCONCAT(part_name) FROM t
Window | SELECT groupConcat(', ')(part_name) OVER (PARTITION BY id) FROM t
SELECT GROUPCONCAT(', ')(part_name) OVER (PARTITION BY id) FROM t
CombinedParameterizedAgg | SELECT groupConcatIf(', ')(part_name, x > 1) FROM t
SELECT GROUPCONCATIF(', ')(part_name, x > 1) FROM t
[assistant] The parse and round-trip now work. I'll add regression tests next to the existing parametric-agg identity checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155227-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT approx_top_sum(N, reserved)(column, weight) FROM t\").selects[\n            0\n        ].assert_is(exp.ParameterizedAgg)\n", "new_string": "        self.validate_i
…[61 chars elided]…
FROM t\").selects[\n            0\n        ].assert_is(exp.ParameterizedAgg)\n        self.validate_identity(\n            \"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\"\n        ).selects[0].this.assert_is(exp.ParameterizedAgg)\n        self.validate_identity(\"SELECT groupConcat(part_name) FROM t\").selects[0].assert_is(\n            exp.AnonymousAggFunc\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155227-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run ClickHouse tests then the full test suite"}
[tool_result] .............................                                                              [100%]
29 passed, 270 subtests passed in 0.40s
..................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 46.42s
[assistant] Full suite passes. Running the formatter and linter on the two changed files:
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -5; git diff --stat", "description": "Run ruff format and lint checks on changed files"}
[tool_result] 2 files already formatted
All checks passed!
 sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 6 ++++++
 2 files changed, 7 insertions(+)
[assistant] `groupConcat` now accepts its parametric form in the ClickHouse dialect. `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` parses and round-trips unchanged.

The cause was that `groupConcat` was missing from the ClickHouse aggregate-name registry. Without it, the parser treated `groupConcat(', ')` as a plain function call and then choked on the `(part_name)` that followed.

**Changes**
- `sqlglot/parsers/clickhouse.py`: added `"groupConcat"` to the `AGG_FUNCTIONS` list. The existing parametric-aggregate machinery then handles it, and combinators like `groupConcatIf(...)(.
…[282 chars elided]…
at --check` and `ruff check` pass on both changed files.

**Choices and limits**
- I did not map ClickHouse's `groupConcat` to the shared `exp.GroupConcat` class. ClickHouse's plain `groupConcat(x)` uses a default separator, and the ClickHouse generator has no handler for `GroupConcat`, so that mapping would break the plain form's round-trip. Keeping it as a generic aggregate is the smaller, safer change.
- Transpiling to other dialects emits `GROUPCONCAT(', ')(part_name)`, which is not valid in those dialects. That is the same behaviour as other ClickHouse-only aggregates, so I left it alone.
