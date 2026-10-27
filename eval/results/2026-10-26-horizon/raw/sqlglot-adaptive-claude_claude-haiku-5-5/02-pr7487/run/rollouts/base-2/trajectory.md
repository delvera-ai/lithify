# trajectory base-2

final message:
The ClickHouse parser now accepts `groupConcat`'s parametric form, so the Superset query parses and round-trips unchanged.

**Cause:** `groupConcat` was missing from the ClickHouse aggregate-function set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). Without it, `groupConcat(', ')` parsed as a plain function, and the trailing `(part_name)` was a syntax error.

**Fix:** I added `"groupConcat"` to `AGG_FUNCTIONS`. It now goes through the same `ParameterizedAgg` path as `groupArray(3)(x)` and `quantile(0.5)(a)`.

**Tests:** I added two identity round-trips to `tests/dialects/test_clickhouse.py`:
- `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts`
- `SELECT groupConcat(', ', 10)(part_name) AS x FROM t`

Results:
- Full suite: 1081 passed, 17836 subtests passed.
- `ruff check` passes. `ruff format` was applied to the test file.

**Side effect to be aware of:** plain `groupConcat(x)` used to parse as `Anonymous` and now parses as `AnonymousAggFunc`. It still generates the same SQL, and no existing test depended on the old node type.

I did not change transpilation to other dialects. `groupConcat` with a separator in ClickHouse has no direct equivalent elsewhere, so that's a separate question. I also didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|GroupConcat\\|PARAMETRIC\\|_parse_quantile\\|quantile\" sqlglot/dialects/clickhouse.py sqlglot/expressions.py | head -60", "description": "Search for groupConcat and parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "pwd; ls; git rev-parse --show-toplevel; grep -rn -i \"groupconcat\\|quantileif\\|PARAMETRIC\" sqlglot/dialects/clickhouse.py sqlglot/parser.py | head -60", "description": "Locate groupConcat and parametric handling in ClickHouse dialect"}
[tool_result] ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2
AGENTS.md
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
~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "grep -n \"PARAMETERIZED\\|Parameterized\\|parameters\\|def _parse_function_call\\|anonymous_func\\|_parse_lambda\" sqlglot/dialects/clickhouse.py | head -60; grep -n \"class ParameterizedAgg\\|parameters\" sqlglot/expressions.py | head; grep -n \"ParameterizedAgg\\|parameterized\" sqlglot/parser.py | head -30", "description": "Search ClickHouse parametric aggregate handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -80; grep -rn \"Parameterized\\|parameters\" sqlglot/dialects/clickhouse.py | head -40", "description": "List package files and grep ClickHouse parameters"}
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
[tool_use Bash] {"command": "ls sqlglot/dialects/ sqlglot/expressions; grep -rln -i \"parametric\\|parameterized\" sqlglot | head; grep -rn \"def _parse_function_call\\|PARAMETRIC\\|parameters\" sqlglot/parser.py sqlglot/parsers/ 2>/dev/null | head -30", "description": "List dialect and expression modules, find parametric handling"}
[tool_result] sqlglot/dialects/:
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

sqlglot/expressions:
__init__.py
aggregate.py
array.py
builders.py
constraints.py
core.py
datatypes.py
ddl.py
dml.py
…[721 chars elided]…
:        Create parameter mode constraint for function parameters.
sqlglot/parsers/snowflake.py:234:            parameters=seq_get(args, 4),
sqlglot/parsers/snowflake.py:259:    Build Round expression, unwrapping Snowflake's named parameters.
sqlglot/parsers/snowflake.py:297:    Build Generator expression, unwrapping Snowflake's named parameters.
sqlglot/parsers/singlestore.py:130:            parameters=seq_get(args, 2),
sqlglot/parsers/singlestore.py:137:            parameters=seq_get(args, 4),
[tool_use Bash] {"command": "grep -n -i \"parametric\\|parameterized\\|quantile\\|Anonymous\" sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py 2>/dev/null | head -60; ls sqlglot/generators sqlglot/parsers | head -80", "description": "Grep ClickHouse parser and generator for parametric handling"}
[tool_result] sqlglot/parsers/clickhouse.py:45:def _build_str_to_date(args: list) -> exp.Cast | exp.Anonymous:
sqlglot/parsers/clickhouse.py:47:        return exp.Anonymous(this="STR_TO_DATE", expressions=args)
sqlglot/parsers/clickhouse.py:59:def _build_split_by_char(args: list) -> exp.Split | exp.Anonymous:
sqlglot/parsers/clickhouse.py:66:    return exp.Anonymous(this="splitByChar", expressions=args)
sqlglot/parsers/clickhouse.py:155:    "quantile",
sqlglot/parsers/clickhouse.py:156:    "quantiles",
sqlglo
…[4224 chars elided]…
.py
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

sqlglot/parsers:
__init__.py
athena.py
base.py
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
[tool_use Bash] {"command": "sed -n 140,155p sqlglot/parsers/clickhouse.py; sed -n 196,260p sqlglot/parsers/clickhouse.py; sed -n 670,740p sqlglot/parsers/clickhouse.py", "description": "Read ClickHouse parametric aggregate parsing code"}
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

# Sorte
…[4099 chars elided]…
        return params

        return None

    def _parse_quantile(self) -> exp.Quantile:
        this = self._parse_lambda()
        params = self._parse_func_params()
        if params:
            return self.expression(exp.Quantile(this=params[0], quantile=this))
        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))

    def _parse_wrapped_id_vars(self, optional: bool = False) -> list[exp.Expr]:
        return super()._parse_wrapped_id_vars(optional=True)
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|group_concat\" sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT groupConcat(', ')(part_name) AS c FROM system.parts\\\", read='clickhouse')\nprint(repr(e))\n\" 2>&1 | tail -5", "description": "Check groupConcat references and reproduce parse error"}
[tool_result]     self.raise_error("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2/sqlglot/parser.py", line 1969, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m c FROM system.parts
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ', 10)(part_name) FROM t\\\", \\\"SELECT groupArray(3)(x) FROM t\\\", \\\"SELECT GROUP_CONCAT(x) FROM t\\\"]:\n    try:\n   
…[67 chars elided]…
s[0])); print(e.sql('clickhouse'))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"class ParameterizedAgg\\|class GroupConcat\\|class CombinedParameterizedAgg\" -A8 sqlglot/expressions/*.py | head -60; grep -n \"ParameterizedAgg\\|def groupconcat\\|groupconcat\" -i sqlglot/generators/clickhouse.py | head", "description": "Probe current groupConcat parse output and expression classes"}
[tool_result] Anonymous(
  this=groupConcat,
  expressions=[
    Column(
      this=Identifier(this=part_name, quoted=False))])
SELECT groupConcat(part_name) FROM t
Aliases(
  this=Anonymous(
    this=groupConcat,
    expressions=[
      Literal(this=', ', is_string=True),
      Literal(this=10, is_string=False)]),
  expressions=[
    Identifier(this=part_name, quoted=False)])
SELECT groupConcat(', ', 10) AS (part_name) FROM t
ParameterizedAgg(
  this=groupArray,
  expressions=[
    Literal(this=3, is_string=
…[1343 chars elided]…
lass CombinedParameterizedAgg(ParameterizedAgg):
sqlglot/expressions/core.py-1962-    arg_types = {"this": True, "expressions": True, "params": True}
sqlglot/expressions/core.py-1963-
sqlglot/expressions/core.py-1964-
sqlglot/expressions/core.py-1965-class HashAgg(Expression, AggFunc):
sqlglot/expressions/core.py-1966-    arg_types = {"this": True, "expressions": False}
sqlglot/expressions/core.py-1967-    is_var_len_args = True
sqlglot/expressions/core.py-1968-
sqlglot/expressions/core.py-1969-
[tool_use Bash] {"command": "grep -n \"AGG_FUNCTIONS: set\\|AGG_FUNCTIONS = \" -A12 sqlglot/parsers/clickhouse.py | head -30; grep -n \"def _resolve_clickhouse_agg\" -A25 sqlglot/parsers/clickhouse.py | head -40; grep -n \"ParameterizedAgg\" -A10 sqlglot/generators/clickhouse.py sqlglot/generator.py | head -30", "description": "Read aggregate function set and resolver code"}
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
313:    AGG_FUNCTIONS = AGG_FUNCTIONS
314-    AGG_FUNCTIONS_SUFFIXES = AGG_FUNCTIONS_SUFFIXES
315-
316-    FUNC_TOKENS = {
317-        *parser.Parser.FUNC_TOKENS,
318-        TokenType.AND,
319-        TokenType.OR,
320-        TokenType.SET,
321-    }
322-
323-    RESERVED_TO
…[2641 chars elided]…
n)
sqlglot/generator.py-5721-
sqlglot/generator.py-5722-    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generator.py-5723-        self.unsupported("Unsupported SHOW statement")
sqlglot/generator.py-5724-        return ""
sqlglot/generator.py-5725-
sqlglot/generator.py-5726-    def install_sql(self, expression: exp.Install) -> str:
sqlglot/generator.py-5727-        self.unsupported("Unsupported INSTALL statement")
sqlglot/generator.py-5728-        return ""
sqlglot/generator.py-5729-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py", "old_string": "    \"sumWithOverflow\",\n", "new_string": "    \"sumWithOverflow\",\n    \"groupConcat\",\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in [\\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\", \\\"SELECT groupConcat(part_name) FROM t\\\", \\\"SELECT groupConcat(', ', 10)(part_name) FROM t\\\", \\\"SELECT groupConcatIf(', ')(x, y > 1) FROM t\\\"]:\n    e=sqlglot.parse_one(s, read='clickhouse'); print(e.sql('clickhouse'))\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -3", "description": "Verify round-trip and run ClickHouse dialect tests"}
[tool_result] SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
SELECT groupConcat(part_name) FROM t
SELECT groupConcat(', ', 10)(part_name) FROM t
SELECT groupConcatIf(', ')(x, y > 1) FROM t
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.24s
[assistant] Round-trips work. Now I'll add a regression test next to the existing parametric-aggregate tests.
[tool_use Bash] {"command": "grep -n \"groupArray(\\|quantile(\" tests/dialects/test_clickhouse.py | head -8", "description": "Find existing parametric aggregate tests"}
[tool_result] 98:        self.validate_identity("SELECT quantile(0.5)(a)")
561:            "SELECT quantile(0.5)(a)",
563:                "duckdb": "SELECT quantile(a, 0.5)",
567:                "clickhouse": "SELECT quantile(0.5)(a)",
572:            read={"duckdb": "SELECT quantile(a, [0.5, 0.4])"},
577:            read={"duckdb": "SELECT quantile(a, [0.5])"},
[tool_use Bash] {"command": "sed -n 94,102p tests/dialects/test_clickhouse.py", "description": "Read context around existing identity tests"}
[tool_result]         self.validate_identity("SELECT * FROM foo ASOF JOIN bla")
        self.validate_identity("SELECT * FROM foo ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL LEFT ANY JOIN bla")
        self.validate_identity("SELECT quantile(0.5)(a)")
        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT quantileState(0.5)(a) AS x FROM t\")\n", "new_string": "        self.validate_identity(\"SELECT quantileState(0.5)(a) AS x FROM t\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n        self.validate_identity(\"SELECT groupConcat(', ', 10)(part_name) AS x FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-154113-clickhouse-dialect-the-parametri/base-2/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; ($P -m ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py; $P -m ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -5", "description": "Run full test suite and ruff checks"}
[tool_result] ........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1081 passed, 17836 subtests passed in 44.92s
Would reformat: tests/dialects/test_clickhouse.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format tests/dialects/test_clickhouse.py && git diff --stat && git diff tests/ | head -30", "description": "Apply ruff format and show diff stat"}
[tool_result] 1 file reformatted
 sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 4 ++++
 2 files changed, 5 insertions(+)
diff --git a/tests/dialects/test_clickhouse.py b/tests/dialects/test_clickhouse.py
index ea42a140b..31e1e4b9e 100644
--- a/tests/dialects/test_clickhouse.py
+++ b/tests/dialects/test_clickhouse.py
@@ -99,6 +99,10 @@ class TestClickhouse(Validator):
         self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
         self.validate_identity("SELECT q
…[162 chars elided]…
"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts"
+        )
+        self.validate_identity("SELECT groupConcat(', ', 10)(part_name) AS x FROM t")
         self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t")
         self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
         self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
[This command modified 1 file you've previously read: tests/dialects/test_clickhouse.py. Call Read before editing.]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -1", "description": "Re-run ClickHouse dialect tests after formatting"}
[tool_result] 29 passed, 270 subtests passed in 0.14s
[assistant] The ClickHouse parser now accepts `groupConcat`'s parametric form, so the Superset query parses and round-trips unchanged.

**Cause:** `groupConcat` was missing from the ClickHouse aggregate-function set (`AGG_FUNCTIONS` in `sqlglot/parsers/clickhouse.py`). Without it, `groupConcat(', ')` parsed as a plain function, and the trailing `(part_name)` was a syntax error.

**Fix:** I added `"groupConcat"` to `AGG_FUNCTIONS`. It now goes through the same `ParameterizedAgg` path as `groupArray(3)(x)` and `quantile(0.5)(a)`.

**Tests:** I added two identity round-trips to `tests/dialects/test_clickhous
…[65 chars elided]…
M system.parts`
- `SELECT groupConcat(', ', 10)(part_name) AS x FROM t`

Results:
- Full suite: 1081 passed, 17836 subtests passed.
- `ruff check` passes. `ruff format` was applied to the test file.

**Side effect to be aware of:** plain `groupConcat(x)` used to parse as `Anonymous` and now parses as `AnonymousAggFunc`. It still generates the same SQL, and no existing test depended on the old node type.

I did not change transpilation to other dialects. `groupConcat` with a separator in ClickHouse has no direct equivalent elsewhere, so that's a separate question. I also didn't commit anything.
