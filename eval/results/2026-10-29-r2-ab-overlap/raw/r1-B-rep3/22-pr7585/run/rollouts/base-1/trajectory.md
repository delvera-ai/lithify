# trajectory base-1

final message:
`APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 tests) and ruff lint and format are clean. I did not commit.

The change is in three places:

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` also accepts a `PERCENTILE_DISC` `WITHIN GROUP` and builds an `exp.ApproxQuantile`. It only takes a single ORDER BY key in ascending order. Descending or multi-key forms still raise `ParseError`, since `ApproxQuantile` has no ordering concept and I didn't want to drop the direction silently.
- **Generator** (`sqlglot/generators/redshift.py`): a new `approxquantile_sql` emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is decorated with `unsupported_args("accuracy", "weight", "error_tolerance")`, since Redshift's form has no equivalents for those.
- **Tests** (`tests/dialects/test_redshift.py`): a `validate_all` case beside the existing `APPROXIMATE COUNT` test, covering the Redshift round-trip plus Snowflake and Spark read and write.

Transpiling from Redshift gives `APPROX_PERCENTILE(x, 0.5)` for Snowflake and Presto, and `PERCENTILE_APPROX(x, 0.5)` for Spark and Hive.

I didn't run mypy, which the pre-commit config includes.

## events
[tool_use Bash] {"command": "grep -rn -i \"approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn -i \"approximate\" tests/dialects/test_redshift.py | head", "description": "Search for APPROXIMATE handling in source and tests"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
[tool_use Bash] {"command": "grep -rn \"APPROXIMATE\" sqlglot/ | head -30; sed -n 50,75p tests/dialects/test_redshift.py; sed -n 355,370p tests/dialects/test_redshift.py; grep -n \"class Redshift\\|class Parser\\|class Generator\\|PERCENTILE\\|WITHIN\" sqlglot/dialects/redshift.py | head -40", "description": "Find APPROXIMATE handling and Redshift dialect structure"}
[tool_result] sqlglot/parsers/redshift.py:65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
sqlglot/parsers/exasol.py:43:        "APPROXIMATE_COUNT_DISTINCT": exp.ApproxDistinct.from_arg_list,
sqlglot/expressions/aggregate.py:22:    _sql_names = ["APPROXIMATE_SIMILARITY", "APPROXIMATE_JACCARD_INDEX"]
sqlglot/generators/redshift.py:75:        exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
sqlglot/generators/exasol.py:363:        exp.ApproxDistinc
…[1909 chars elided]…
date DATE, end_date DATE)")
        self.validate_identity("SELECT APPROXIMATE AS y")
        self.validate_identity("CREATE TABLE t (c BIGINT IDENTITY(0, 1))")
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS AVRO 'auto'"
        )
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS JSON 's3://jsonpaths_file'"
1 matches in 1 files:

11:0:
[tool_use Bash] {"command": "grep -n \"_parse_approximate_count\" -A25 sqlglot/parsers/redshift.py | head -60; grep -rn \"class PercentileDisc\\|class PercentileCont\\|class ApproxQuantile\\|class ApproxDistinct\" -A6 sqlglot/expressions/*.py; grep -rn \"PERCENTILE_DISC\\|ApproxQuantile\\|APPROX_PERCENTILE\" sqlglot/parsers/*.py sqlglot/generators/*.py | head -40", "description": "Inspect approximate count parser and percentile expressions"}
[tool_result] 65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
66-        "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp(sysdate=True)),
67-    }
68-
69-    SUPPORTS_IMPLICIT_UNNEST = True
70-
71-    def _parse_table(
72-        self,
73-        schema: bool = False,
74-        joins: bool = False,
75-        alias_tokens: Collection[TokenType] | None = None,
76-        parse_bracket: bool = False,
77-        is_db_reference: bool = False,
78-        parse_partition: bool 
…[5144 chars elided]…
: self.func(
sqlglot/generators/presto.py:262:            "APPROX_PERCENTILE",
sqlglot/generators/singlestore.py:186:        exp.ApproxQuantile: unsupported_args("accuracy", "weight")(
sqlglot/generators/singlestore.py:188:                "APPROX_PERCENTILE",
sqlglot/generators/snowflake.py:931:    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:
sqlglot/generators/snowflake.py:932:        return self.func("APPROX_PERCENTILE", expression.this, expression.args.get("quantile"))
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['redshift','postgres','snowflake']:\n    try:\n        e=sqlglot.parse_one('SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read=d)\n        print(d, repr(e.selects[0]))\n        print(d, e.sql(d))\n    except Exception as ex: print
…[126 chars elided]…
dshift')\nexcept Exception as ex: print('ERR',ex)\n\"; grep -n \"WITHIN\\|PERCENTILE\" sqlglot/parser.py sqlglot/parsers/base.py sqlglot/generator.py sqlglot/generators/base.py sqlglot/parsers/redshift.py sqlglot/generators/redshift.py 2>/dev/null | head -40; grep -n \"class Quantile\" -A5 sqlglot/expressions/aggregate.py", "description": "Probe current percentile parsing and generation behavior"}
[tool_result] redshift WithinGroup(
  this=PercentileDisc(
    this=Literal(this=0.5, is_string=False)),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=x, quoted=False),
          join_mark=False),
        nulls_first=False)]),
  join_mark=False)
redshift SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
postgres WithinGroup(
  this=PercentileDisc(
    this=Literal(this=0.5, is_string=False)),
  expression=Order(
    expressions=[
      Orde
…[923 chars elided]…
or WITHIN GROUPs
sqlglot/parser.py:7738:# Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_ex...
sqlglot/parser.py:7741:if not self._match_text_seq("WITHIN", "GROUP"):
sqlglot/parser.py:8127:# T-SQL allows the OVER (...) syntax after WITHIN GROUP.
sqlglot/parser.py:8129:if self._match_text_seq("WITHIN", "GROUP"):
230:class Quantile(Expression, AggFunc):
231-    arg_types = {"this": True, "quantile": True}
232-
233-
234-class ApproxQuantile(Quantile):
235-    arg_types = {
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/redshift.py; echo ----; sed -n 1,30p sqlglot/generators/redshift.py; echo ----; sed -n 60,110p sqlglot/generators/redshift.py; grep -n \"unsupported_args\" sqlglot/generators/redshift.py | head -3; grep -n \"def unsupported_args\" -A3 sqlglot/*.py | head", "description": "Read Redshift parser and generator headers"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.postgres import PostgresParser
from sqlglot.parser import build_convert_timezone
from sqlglot.tokens import TokenType
from sqlglot.dialects.dialect import map_date_part
from builtins import type as Type

if t.TYPE_CHECKING:
    from sqlglot._typing import E
    from collections.abc import Collection


def _build_date_delta(expr_type: Type[E]) -> t.Callable[[list
…[3181 chars elided]…
      exp.TsOrDsDiff: date_delta_sql("DATEDIFF"),
        exp.UnixToTime: lambda self, e: self._unix_to_time_sql(e),
        exp.SHA2Digest: lambda self, e: self.func(
            "SHA2", e.this, e.args.get("length") or exp.Literal.number(256)
        ),
0 matches for 'unsupported_args'
sqlglot/generator.py:30:def unsupported_args(
sqlglot/generator.py-31-    *args: str | tuple[str, str],
sqlglot/generator.py-32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
sqlglot/generator.py-33-    """
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[607 chars elided]…
rcentileDisc)\n            and len(func.expression.expressions) == 1\n            and not func.expression.expressions[0].args.get(\"desc\")\n        ):\n            return self.expression(\n                exp.ApproxQuantile(\n                    this=func.expression.expressions[0].this,\n                    quantile=func.this.this,\n                )\n            )\n        self._retreat(index)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def \\|^    [A-Z_]* = \\|^    TRANSFORMS\" sqlglot/generators/redshift.py | head -40", "description": "List methods in Redshift generator"}
[tool_result] 32 matches in 10 files:

273:0:exp.Unnest) -> str:
290:0:exp.Cast, safe_prefix: str | None = None) -> str:
297:0:exp.DataType) -> str:
313:0:exp.AlterSet) -> str:
323:0:exp.Array) -> str:
329:0:exp.IgnoreNulls) -> str:
332:0:exp.RespectNulls) -> str:
335:0:exp.Explode) -> str:
339:0:exp.UnixToTime) -> str:
sqlglot/generators/redshift.py:21:LOCKING_READS_SUPPORTED = False
sqlglot/generators/redshift.py:22:QUERY_HINTS = False
sqlglot/generators/redshift.py:23:VALUES_AS_TABLE = False
sqlglot/genera
…[728 chars elided]…
ORTS_DECODE_CASE = True
sqlglot/generators/redshift.py:38:SUPPORTS_BETWEEN_FLAGS = False
sqlglot/generators/redshift.py:39:LIMIT_FETCH = "LIMIT"
sqlglot/generators/redshift.py:40:STAR_EXCEPT = "EXCLUDE"
sqlglot/generators/redshift.py:41:STAR_EXCLUDE_REQUIRES_DERIVED_TABLE = False
sqlglot/generators/redshift.py:44:WITH_PROPERTIES_PREFIX = " "
sqlglot/generators/redshift.py:46:TYPE_MAPPING = {
sqlglot/generators/redshift.py:57:TRANSFORMS = {
sqlglot/generators/redshift.py:113:RESERVED_KEYWORDS = {
[tool_use Bash] {"command": "sed -n 268,345p sqlglot/generators/redshift.py", "description": "Read Redshift generator method section"}
[tool_result]         "where",
        "with",
        "without",
    }

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = expression.expressions
        num_args = len(args)

        if num_args != 1:
            self.unsupported(f"Unsupported number of arguments in UNNEST: {num_args}")
            return ""

        if isinstance(expression.find_ancestor(exp.From, exp.Join, exp.Select), exp.Select):
            self.unsupported("Unsupported UNNEST when not used in FROM/JOIN clauses")
 
…[2201 chars elided]…
str:
        return Generator.respectnulls_sql(self, expression)

    def explode_sql(self, expression: exp.Explode) -> str:
        self.unsupported("Unsupported EXPLODE() function")
        return ""

    def _unix_to_time_sql(self, expression: exp.UnixToTime) -> str:
        scale = expression.args.get("scale")
        this = self.sql(expression.this)

        if scale is not None and scale != exp.UnixToTime.SECONDS and scale.is_int:
            this = f"({this} / POWER(10, {scale.to_py()}))"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "        return f\"SET{exprs}{location}{file_format}\"\n\n    def array_sql", "new_string": "        return f\"SET{exprs}{location}{file_format}\"\n\n    @unsupported_args(\"accuracy\", \"weight\", \"error_tolerance\")\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        percentile = exp.PercentileDisc(this=expression.args[\"quantile\"])\n        order = exp.Order(expressions=[exp.Ordered(this=expression.this)])\n        return f\"APPROXIMATE {self.sql(exp.WithinGroup(this=percentile, expression=order))}\"\n\n    def array_sql"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/^from sqlglot.generator import Generator$/from sqlglot.generator import Generator, unsupported_args/' sqlglot/generators/redshift.py && grep -n \"^from sqlglot.generator\" sqlglot/generators/redshift.py && PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nq='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY 
…[294 chars elided]…
CT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x, y) FROM t']:\n    try: print(sqlglot.parse_one(s, read='redshift').sql('redshift'))\n    except Exception as ex: print('ERR', type(ex).__name__)\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t', read='snowflake', write='redshift'))\n\" 2>&1 | head -40", "description": "Apply import fix and probe new Redshift behavior"}
[tool_result] sed: 1: "sqlglot/generators/reds ...": unterminated substitute pattern
(eval):1: command not found: -c
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "from sqlglot.generator import Generator\n", "new_string": "from sqlglot.generator import Generator, unsupported_args\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t'\ne=sqlglot.parse_one(q, read='redshift'); print(repr(e.selects[0]))\nprint(e.sql('redshift'))\nfor d in ['postgres','snowflake','presto','spark','duckdb','hive']:\n    print(d, e.sql(d))\nfor s in ['SELECT APPROXI
…[177 chars elided]…
e(s, read='redshift').sql('redshift'))\n    except Exception as ex: print('ERR', type(ex).__name__)\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t', read='snowflake', write='redshift'))\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t', read='snowflake', write='redshift'))\n\" 2>&1 | head -60", "description": "Probe new Redshift approximate percentile behavior"}
[tool_result] ApproxQuantile(
  this=Column(
    this=Identifier(this=x, quoted=False),
    join_mark=False),
  quantile=Literal(this=0.5, is_string=False),
  join_mark=False)
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
postgres SELECT APPROX_QUANTILE(x, 0.5) FROM t
snowflake SELECT APPROX_PERCENTILE(x, 0.5) FROM t
presto SELECT APPROX_PERCENTILE(x, 0.5) FROM t
spark SELECT PERCENTILE_APPROX(x, 0.5) FROM t
duckdb SELECT APPROX_QUANTILE(x, 0.5) FROM t
hive SELECT PERCENTILE_APPROX(x, 0.5) FROM t
ERR ParseError
ERR ParseError
['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
[assistant] The parse, round-trip, and transpile paths all behave as intended. Now I'll add tests next to the existing `APPROXIMATE COUNT` coverage.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "                \"spark\": \"SELECT APPROX_COUNT_DISTINCT(y)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\",", "new_string": "                \"spark\": \"SELECT APPR
…[321 chars elided]…
(x, 0.5) FROM t\",\n            },\n            write={\n                \"redshift\": \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t\",\n                \"snowflake\": \"SELECT APPROX_PERCENTILE(x, 0.5) FROM t\",\n                \"spark\": \"SELECT PERCENTILE_APPROX(x, 0.5) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184057-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -3", "description": "Run full test suite plus ruff lint and format checks"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
........................................................................ [ 32%]
..................................................................... [ 38%]
......................................
…[307 chars elided]…
.................................................................................. [ 74%]
............................................. [ 78%]
................................................................................................................................................................................................... [ 95%]
..............................................            [100%]
1103 passed, 17894 subtests passed in 46.83s
All checks passed!
3 files already formatted
[assistant] `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 tests) and ruff lint and format are clean. I did not commit.

The change is in three places:

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` also accepts a `PERCENTILE_DISC` `WITHIN GROUP` and builds an `exp.ApproxQuantile`. It only takes a single ORDER BY key in ascending order. Descending or multi-key forms still raise `ParseError`, since `ApproxQuantile` has no ordering concept and I didn't want to drop the directio
…[78 chars elided]…
uantile_sql` emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is decorated with `unsupported_args("accuracy", "weight", "error_tolerance")`, since Redshift's form has no equivalents for those.
- **Tests** (`tests/dialects/test_redshift.py`): a `validate_all` case beside the existing `APPROXIMATE COUNT` test, covering the Redshift round-trip plus Snowflake and Spark read and write.

Transpiling from Redshift gives `APPROX_PERCENTILE(x, 0.5)` for Snowflake and Presto, and `PERCENTILE_APPROX(x, 0.5)` for Spark and Hive.

I didn't run mypy, which the pre-commit config includes.
