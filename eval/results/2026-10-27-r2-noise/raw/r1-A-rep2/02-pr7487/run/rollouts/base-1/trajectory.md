# trajectory base-1

final message:
The reported query now parses and round-trips in the ClickHouse dialect: `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` comes back unchanged.

The fix is one line in `sqlglot/parsers/clickhouse.py`: `groupConcat` is now in the `AGG_FUNCTIONS` set, so the parser treats it as a parametric aggregate like `quantile(0.5)(x)`. The `groupConcatIf(', ')(a, a > 1)` combinator form also works, and plain `groupConcat(x)` still round-trips. I added two identity tests in `tests/dialects/test_clickhouse.py`.

The ClickHouse test file passes (29 tests). Ruff is clean. The full suite has one failure, `test_lazy_load`, which also fails on the untouched tree because it calls a `python` binary that isn't on PATH.

I kept this to the parse/round-trip fix. The parametric form is stored as a generic `ParameterizedAgg` rather than `exp.GroupConcat` with a separator, so it won't transpile to other dialects' `GROUP_CONCAT ... SEPARATOR` syntax. Making that mapping would be a separate change if you want it.

## events
[assistant] I'll look at how the ClickHouse dialect currently handles parametric aggregates like `quantile(0.5)(x)`.
[tool_use Bash] {"command": "grep -n -i \"param\\|quantile\\|groupconcat\\|GroupConcat\\|ParameterizedAgg\" sqlglot/dialects/clickhouse.py | head -80; echo ---; grep -n -i \"class GroupConcat\\|class Quantile\\|ParameterizedAgg\" sqlglot/expressions.py"}
[tool_result ERROR] Exit code 2
---
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls && grep -rn -i \"param_agg\\|parameterized\\|quantile\\|groupconcat\\|GroupConcat\" sqlglot/dialects/clickhouse.py sqlglot/expressions.py | head -80"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.7M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  2.5K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  794B
sqlglot.png  7.2K
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; ls sqlglot/dialects | grep -i click; grep -n -i \"param\\|quantile\\|groupconcat\" sqlglot/dialects/clickhouse.py | head -80"}
[tool_result] dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__.py  6.4K
__main__.py  2.1K
_typing.py  1.5K
_version.py  91B
diff.py  16.3K
errors.py  4.7K
generator.py  244.6K
helper.py  11.7K
jsonpath.py  7.8K
lineage.py  16.7K
parser.py  365.3K
planner.py  14.2K
py.typed  0B
schema.py  27.4K
serde.py  3.0K
time.py  18.0K
tokenizer_core.py  34.4K
tokens.py  22.4K
transforms.py  41.0K
trie.py  2.2K
clickhouse.py  4.6K
[tool_use Bash] {"command": "cat sqlglot/dialects/clickhouse.py; echo ---; grep -rn -i \"parameterized\\|ParamAgg\\|quantile\\|groupconcat\\|group_concat\" sqlglot/parsers/ sqlglot/generators/ sqlglot/expressions/ sqlglot/dialects/clickhouse.py | head -60"}
[tool_result] from __future__ import annotations


from sqlglot import exp, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.clickhouse import ClickHouseGenerator
from sqlglot.parsers.clickhouse import ClickHouseParser
from sqlglot.tokens import TokenType
from sqlglot.typing.clickhouse import EXPRESSION_METADATA


class ClickHouse(Dialect):
    INDEX_OFFSET = 1
    NORMALIZE_FUNCTIONS: bool | str = False
    NULL_ORDERING = "nulls_are_last"
    SU
…[8476 chars elided]…
g_list,
sqlglot/parsers/duckdb.py:186:            ("GROUP_CONCAT", "LISTAGG", "STRINGAGG"), lambda self: self._parse_string_agg()
sqlglot/parsers/mysql.py:156:        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
sqlglot/generators/redshift.py:87:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/clickhouse.py:56:def _quantile_sql(self: ClickHouseGenerator, expression: exp.Quantile) -> str:
sqlglot/generators/clickhouse.py:57:    quantile = expression.args["quantile"]
[tool_use Bash] {"command": "sed -n 140,160p sqlglot/parsers/clickhouse.py; echo ...; sed -n 180,200p sqlglot/parsers/clickhouse.py; echo ...; sed -n 660,745p sqlglot/parsers/clickhouse.py; echo ---; grep -n -i \"groupconcat\\|parameterizedagg\" sqlglot/generators/clickhouse.py sqlglot/expressions/*.py | head; echo ---; grep -n -i \"groupconcat\\|group_concat\" tests/dialects/test_clickhouse.py | head"}
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
...
    "simpleLinearRegression",
    "stochasticLinearRegression",
    "stochasticLogisticRegression",
    "catego
…[3558 chars elided]…
: bool = False) -> list[exp.Expr]:
        return super()._parse_wrapped_id_vars(optional=True)

    def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        if self._match(TokenType.DOT):
---
sqlglot/expressions/aggregate.py:133:class GroupConcat(Expression, AggFunc):
sqlglot/expressions/core.py:1939:class ParameterizedAgg(Expression, AggFunc):
sqlglot/expressions/core.py:1961:class CombinedParameterizedAgg(ParameterizedAgg):
---
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT quantile(0.5)(x) FROM t\\\", \\\"SELECT groupConcat(x) FROM t\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='clickhouse'); print(repr(e.selects[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; sed -n 1930,1975p sqlglot/expressions/core.py; sed -n 125,150p sqlglot/expressions/aggregate.py; grep -n \"_resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | head -50"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m concatenated FROM system.parts
Quantile(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  quantile=Literal(this=0.5, is_string=False))
SELECT quantile(0.5)(x) FROM t
Anonymous(
  this=groupConcat,
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))])
SELECT groupConcat(x) FROM t

class SafeFunc(Expression, Func):
    pass


class Typeof(Expression, Func):

…[3693 chars elided]…
exp_class(this=anon_func.this, expressions=anon_func.expressions)
704-            if params:
705-                instance.set("params", params)
706-            func = self.expression(instance)
707-
708-            if isinstance(expr, exp.Window):
709-                # The window's func was parsed as Anonymous in base parser, fix its
710-                # type to be ClickHouse style CombinedAnonymousAggFunc / AnonymousAggFunc
711-                expr.set("this", func)
712-            elif params:
[tool_use Bash] {"command": "grep -n \"AGG_FUNC_MAPPING\\|AGG_FUNCTIONS\\b\\|^AGG_FUNCTIONS\\|^[A-Z_]* = \" sqlglot/parsers/clickhouse.py | head -30; sed -n 1,30p sqlglot/parsers/clickhouse.py | grep -n \"AGG\\|import\"; grep -n \"ParameterizedAgg\" -A12 sqlglot/generators/clickhouse.py | head -30; grep -rn \"groupconcat\\|groupConcat\" tests/ | head"}
[tool_result] 10 matches in 6 files:

210:0:list[str] = sorted(
233:0:Mapping[str, tuple[str, str | None]] = {
234:0:(f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
235:0:(f, None) for f in AGG_FUNCTIONS}
344:0:= AGG_FUNC_MAPPING.get(name)) is None:
sqlglot/parsers/clickhouse.py:77:TIMESTAMP_TRUNC_UNITS = {
sqlglot/parsers/clickhouse.py:90:AGG_FUNCTIONS = {
sqlglot/parsers/clickhouse.py:313:AGG_FUNCTIONS = AGG_FUNCTIONS
sqlglot/parsers/clickhouse.py:330:AGG_FUNC_MAPPING = AGG_FUNC_MAPPING
sqlglot/parsers/clickhouse.py:342:# as AGG_FUNC_MAPPING memoizes all 0- and 1-suffix
1:from __future__ import annotations
3:import typing as t
5:from collections import deque
7:from sqlglot import exp, parser
8:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import Token, TokenType
16:from builtins import type as Type
19:    from sqlglot._typing import E
20:    from collections.abc import Mapping, Sequence, Collection
[tool_use Bash] {"command": "sed -n 88,96p sqlglot/parsers/clickhouse.py; sed -n 196,215p sqlglot/parsers/clickhouse.py; sed -n 240,250p sqlglot/parsers/clickhouse.py; grep -n \"AGG_FUNCTIONS\\|ParameterizedAgg\\|AnonymousAggFunc\" sqlglot/generators/clickhouse.py sqlglot/generator.py | head"}
[tool_result] AGG_FUNCTIONS = {
    "count",
    "min",
    "max",
    "sum",
    "avg",
    "any",
    "sumCount",
    "largestTriangleThreeBuckets",
    "histogram",
    "sequenceMatch",
    "sequenceCount",
    "windowFunnel",
    "retention",
    "uniqUpTo",
    "sequenceNextNode",
    "exponentialTimeDecayedAvg",
}

# Sorted longest-first so that compound suffixes (e.g. "SimpleState") are matched
# before their sub-suffixes (e.g. "State") when resolving multi-combinator functions.
AGG_FUNCTIONS_SUFFIXES:
…[291 chars elided]…
IONAL_ALIAS_TOKEN_CTE = False
    JOINS_HAVE_EQUAL_PRECEDENCE = True

    FUNCTIONS = {
        **{
            k: v
            for k, v in parser.Parser.FUNCTIONS.items()
3 matches in 1 files:

sqlglot/generator.py:5709:def parameterizedagg_sql(self, expression: exp.ParameterizedAgg) -> str:
sqlglot/generator.py:5713:def anonymousaggfunc_sql(self, expression: exp.AnonymousAggFunc) -> str:
sqlglot/generator.py:5719:def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedA...
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1; grep -n \"def _parse_group_concat\" -A22 sqlglot/parsers/base.py sqlglot/parser.py 2>/dev/null | head -40; grep -n \"function = self.FUNCTION_PARSERS\\|FUNCTION_PARSERS.get\" -B3 -A8 sqlglot/parser.py sqlglot/parsers/base.py 2>/dev/null | head -40; grep -rn \"GroupConcat\" sqlglot/generators/*.py sqlglot/generator.py | head"}
[tool_result] sqlglot/parser.py:9798:    def _parse_group_concat(self) -> exp.Expr | None:
sqlglot/parser.py-9799-        def concat_exprs(node: exp.Expr | None, exprs: list[exp.Expr]) -> exp.Expr:
sqlglot/parser.py-9800-            if isinstance(node, exp.Distinct) and len(node.expressions) > 1:
sqlglot/parser.py-9801-                concat_exprs = [
sqlglot/parser.py-9802-                    self.expression(
sqlglot/parser.py-9803-                        exp.Concat(
sqlglot/parser.py-9804-                  
…[2851 chars elided]…
ncat: lambda self, e: groupconcat_sql(
sqlglot/generators/mysql.py:159:        exp.GroupConcat: lambda self, e: (
sqlglot/generators/postgres.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/presto.py:642:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/redshift.py:87:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/snowflake.py:498:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=""),
[assistant] The parser has no entry for `groupConcat`, so it falls through to `Anonymous` and the `(sep)` call is unparseable. ClickHouse parametric aggregates are driven by the `AGG_FUNCTIONS` set, so the minimal fix is to register `groupConcat` there. I'll confirm the existing quantile test pattern first.
[tool_use Bash] {"command": "grep -n \"quantile(\" tests/dialects/test_clickhouse.py | head -5; grep -n \"def test_clickhouse\\|def test_\" tests/dialects/test_clickhouse.py | head -5; grep -n \"\\\"groupBitmapXor\\\"\\|\\\"uniqUpTo\\\"\" sqlglot/parsers/clickhouse.py"}
[tool_result] rg: regex parse error:
    (?:quantile()
    ^
error: unclosed group
0 matches for 'quantile('
29 matches in 29 files:

1428:0:
1465:0:
15:0:
2 matches in 1 files:

sqlglot/parsers/clickhouse.py:140:"groupBitmapXor",
sqlglot/parsers/clickhouse.py:203:"uniqUpTo",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "offset": 134, "limit": 10}
[tool_result] 134	    "groupBitAnd",
135	    "groupBitOr",
136	    "groupBitXor",
137	    "groupBitmap",
138	    "groupBitmapAnd",
139	    "groupBitmapOr",
140	    "groupBitmapXor",
141	    "sumWithOverflow",
142	    "sumMap",
143	    "minMap",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "    \"groupBitmapXor\",\n    \"sumWithOverflow\",", "new_string": "    \"groupBitmapXor\",\n    \"groupConcat\",\n    \"sumWithOverflow\","}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now I'll check the round-trip for the reported query and a few neighboring forms (no-separator, combinator suffix).
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(x) FROM t\\\", \\\"SELECT groupConcatIf(', ')(x, y > 1) FROM t\\\", \\\"SELECT groupConcat(', ')(x) OVER (PARTITION BY y) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='clickhouse'); print(e.sql('clickhouse'))\n\""}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(x) FROM t
SELECT groupConcatIf(', ')(x, y > 1) FROM t
SELECT groupConcat(', ')(x) OVER (PARTITION BY y) FROM t
[assistant] All four forms round-trip. Next I'll add a regression test next to the existing ClickHouse aggregate tests, then run the project checks.
[tool_use Bash] {"command": "grep -n \"AggFunc\\|parametric\\|Parametric\\|quantile\" tests/dialects/test_clickhouse.py | head -20"}
[tool_result] 46 matches in 9 files:

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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "offset": 98, "limit": 8}
[tool_result] 98	        self.validate_identity("SELECT quantile(0.5)(a)")
99	        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
100	        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
101	        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
102	        self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t")
103	        self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
104	        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
105	        self.validate_identity("SELECT histogram(5)(a)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT histogram(5)(a)\")", "new_string": "        self.validate_identity(\"SELECT histogram(5)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n        self.validate_identity(\"SELECT groupConcatIf(', ')(a, a > 1) AS x FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -3"}
[tool_result] .............................                                                              [100%]
29 passed, 270 subtests passed in 0.31s
=========================== short test summary info ============================
FAILED tests/dialects/test_dialect.py::TestDialect::test_lazy_load - FileNotF...
1 failed, 1080 passed, 17836 subtests passed in 42.79s
[assistant] The ClickHouse tests pass. One unrelated failure, `test_lazy_load`, needs checking against the unmodified tree.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py::TestDialect::test_lazy_load 2>&1 | grep -i \"FileNotFound\\|No such\" | head -3; git -C ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1 stash -q && ~/.cache/lithif
…[30 chars elided]…
glot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py::TestDialect::test_lazy_load 2>&1 | tail -1; git -C ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1 stash pop -q && git -C ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-130227-clickhouse-dialect-the-parametri/base-1 status --short"}
[tool_result] E                   FileNotFoundError: [Errno 2] No such file or directory: 'python'
~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/subprocess.py:1955: FileNotFoundError
1 failed in 0.09s
ok stash pop
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[assistant] `test_lazy_load` fails identically on the untouched tree (it shells out to a `python` binary that isn't on PATH), so it's environmental. Last, a lint pass on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -4"}
[tool_result] All checks passed!
Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format tests/dialects/test_clickhouse.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -1"}
[tool_result] 1 file reformatted
sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 4 ++++
 2 files changed, 5 insertions(+)
29 passed, 270 subtests passed in 0.14s
[This command modified 1 file you've previously read: tests/dialects/test_clickhouse.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff"}
[tool_result] sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 4 ++++
 2 files changed, 5 insertions(+)

--- Changes ---

sqlglot/parsers/clickhouse.py
  @@ -138,6 +138,7 @@ AGG_FUNCTIONS = {
  +    "groupConcat",
       "sumWithOverflow",
       "sumMap",
       "minMap",
  +1 -0

tests/dialects/test_clickhouse.py
  @@ -103,6 +103,10 @@ class TestClickhouse(Validator):
  +        self.validate_identity(
  +            "SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts"
  +        )
  +        self.validate_identity("SELECT groupConcatIf(', ')(a, a > 1) AS x FROM t")
           self.validate_identity("SELECT groupUniqArray(2)(a)")
           self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
           self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
  +4 -0
[assistant] The reported query now parses and round-trips in the ClickHouse dialect: `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` comes back unchanged.

The fix is one line in `sqlglot/parsers/clickhouse.py`: `groupConcat` is now in the `AGG_FUNCTIONS` set, so the parser treats it as a parametric aggregate like `quantile(0.5)(x)`. The `groupConcatIf(', ')(a, a > 1)` combinator form also works, and plain `groupConcat(x)` still round-trips. I added two identity tests in `tests/dialects/test_clickhouse.py`.

The ClickHouse test file passes (29 tests). Ruff is clean. The full suite has one failure, `test_lazy_load`, which also fails on the untouched tree because it calls a `python` binary that isn't on PATH.

I kept this to the parse/round-trip fix. The parametric form is stored as a generic `ParameterizedAgg` rather than `exp.GroupConcat` with a separator, so it won't transpile to other dialects' `GROUP_CONCAT ... SEPARATOR` syntax. Making that mapping would be a separate change if you want it.
