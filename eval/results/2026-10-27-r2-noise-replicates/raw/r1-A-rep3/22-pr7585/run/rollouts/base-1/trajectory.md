# trajectory base-1

final message:
`APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 passed) and ruff check and format are clean. I haven't committed anything.

How it's mapped:
- **Parser** (`sqlglot/parsers/redshift.py`): the `APPROXIMATE` handler, renamed from `_parse_approximate_count` to `_parse_approximate`, now also accepts `PERCENTILE_DISC ... WITHIN GROUP` and builds an `exp.ApproxQuantile(this=x, quantile=p)`. It only accepts a single ordering key without `DESC`. `DESC` would change the meaning and `ApproxQuantile` can't represent it, so that form still raises a `ParseError`.
- **Generator** (`sqlglot/generators/redshift.py`): `approxquantile_sql` emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is decorated with `unsupported_args("accuracy", "weight", "error_tolerance")`, so those arguments raise instead of being dropped silently.
- **Tests** (`tests/dialects/test_redshift.py`): added a `validate_all` case covering Redshift round-trip and Snowflake `APPROX_PERCENTILE(y, 0.5)` in both directions, and a `validate_identity` case. I didn't change any existing test.

Verified: `ApproxQuantile` generates `APPROX_QUANTILE` for DuckDB and `APPROX_PERCENTILE` for Snowflake, and the existing `APPROXIMATE COUNT(DISTINCT ...)` behavior is unchanged.

## events
[tool_use Bash] {"command": "grep -n -i \"approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -n -i \"approx\" tests/dialects/test_redshift.py | head -20", "description": "Find APPROXIMATE handling in redshift and core code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
63:                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
67:                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
364:        self.validate_identity("SELECT APPROXIMATE AS y")
[tool_use Bash] {"command": "grep -rn -i \"approximate\" sqlglot/ | grep -v \"^Binary\" | head -40; echo ---; sed -n 50,75p tests/dialects/test_redshift.py; echo ---; sed -n 355,370p tests/dialects/test_redshift.py", "description": "Search for APPROXIMATE across sqlglot and tests"}
[tool_result] sqlglot/parsers/redshift.py:65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
sqlglot/parsers/redshift.py:99:    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:
sqlglot/parsers/exasol.py:43:        "APPROXIMATE_COUNT_DISTINCT": exp.ApproxDistinct.from_arg_list,
sqlglot/typing/snowflake.py:363:            exp.ApproximateSimilarity,
sqlglot/expressions/aggregate.py:21:class ApproximateSimilarity(Expression, AggFunc):
sqlglot/expressions/aggregate.py:22:    _s
…[2688 chars elided]…
REATE TABLE datetable (start_date DATE, end_date DATE)")
        self.validate_identity("SELECT APPROXIMATE AS y")
        self.validate_identity("CREATE TABLE t (c BIGINT IDENTITY(0, 1))")
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS AVRO 'auto'"
        )
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS JSON 's3://jsonpaths_file'"
[tool_use Bash] {"command": "sed -n 1,130p sqlglot/parsers/redshift.py; echo ---; grep -n \"PERCENTILE\\|class Percentile\\|class Quantile\\|ApproxQuantile\" sqlglot/expressions/*.py | head -30", "description": "Read Redshift parser and percentile expressions"}
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
…[4082 chars elided]…
  return projections, exclude
---
sqlglot/expressions/aggregate.py:37:class ApproxQuantiles(Expression, AggFunc):
sqlglot/expressions/aggregate.py:214:class PercentileCont(Expression, AggFunc):
sqlglot/expressions/aggregate.py:218:class PercentileDisc(Expression, AggFunc):
sqlglot/expressions/aggregate.py:222:PERCENTILES = (PercentileCont, PercentileDisc)
sqlglot/expressions/aggregate.py:230:class Quantile(Expression, AggFunc):
sqlglot/expressions/aggregate.py:234:class ApproxQuantile(Quantile):
[tool_use Bash] {"command": "sed -n 30,45p sqlglot/expressions/aggregate.py; sed -n 210,245p sqlglot/expressions/aggregate.py; echo ---; grep -rn \"ApproxQuantile\\b\\|ApproxQuantile(\" sqlglot/ | head -40; echo ---; grep -rn \"PercentileDisc\" sqlglot/ | head -30; echo ---; grep -n -i \"approx\\|percentile\" sqlglot/generators/redshift.py sqlglot/parsers/postgres.py sqlglot/parser.py | head -30", "description": "Inspect quantile expressions and their usages"}
[tool_result]     pass


class ApproxPercentileEstimate(Expression, Func):
    arg_types = {"this": True, "percentile": True}


class ApproxQuantiles(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class ApproxTopK(Expression, AggFunc):
    arg_types = {"this": True, "expression": False, "counters": False}


class ApproxTopKAccumulate(Expression, AggFunc):
class ObjectAgg(Expression, AggFunc):
    arg_types = {"this": True, "expression": True}


class PercentileCont(Expression, Agg
…[3096 chars elided]…
,
sqlglot/generators/postgres.py:340:        exp.PercentileDisc: transforms.preprocess([transforms.add_within_group_for_percentiles]),
sqlglot/generators/duckdb.py:1634:        exp.PercentileDisc: rename_func("QUANTILE_DISC"),
---
sqlglot/generators/redshift.py:75:        exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
sqlglot/parser.py:8128:        # https://learn.microsoft.com/en-us/sql/t-sql/functions/percentile-disc-transact-sql?view=sql-server-ver16
[tool_use Bash] {"command": "grep -n \"WITHIN\\|PERCENTILES\\|def _parse_quantile\" sqlglot/parser.py | head; echo ---; sed -n 8115,8150p sqlglot/parser.py; echo ---; grep -n -A22 \"def add_within_group_for_percentiles\" sqlglot/transforms.py; echo ---; sed -n 925,945p sqlglot/generators/snowflake.py; echo ---; sed -n 4370,4390p sqlglot/generators/duckdb.py; echo; grep -n \"def approxquantile\\|ApproxQuantile\" sqlglot/generator.py", "description": "Inspect WITHIN GROUP parsing and percentile transforms"}
[tool_result] 7734:            # The order is parsed through `this` as a canonicalization for WITHIN GROUPs
7738:        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
7741:        if not self._match_text_seq("WITHIN", "GROUP"):
8127:        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
8129:        if self._match_text_seq("WITHIN", "GROUP"):
---
            self._match_texts(("MAX", "MIN"))
            max = self._prev.text.upper() != "MI
…[3982 chars elided]…
quantile"))

        # DuckDB returns integers for APPROX_QUANTILE, cast to DOUBLE if the expected type is a real type
        if expression.is_type(*exp.DataType.REAL_TYPES):
            result = f"CAST({result} AS DOUBLE)"

        return result

    def approxquantiles_sql(self, expression: exp.ApproxQuantiles) -> str:
        """
        BigQuery's APPROX_QUANTILES(expr, n) returns an array of n+1 approximate quantile values
        dividing the input distribution into n equal-sized buckets.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t','SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try:\n        e=sqlglot.parse_one(s,read='redshift'); print(repr(e.selects[0])); print(e.sql('redshift'))\n    except Exception as ex: print('ERR',type(ex).__name__, ex)\n\" ; $PY -c \"import sqlglot;print(sqlglot.__file__)\"", "description": "Reproduce current parsing behavior for Redshift"}
[tool_result] WithinGroup(
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
SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/generators/redshift.py; echo ...; grep -n \"unsupported_args\\|    def \\|TRANSFORMS\" sqlglot/generators/redshift.py | head -60; echo ---; grep -n \"class Ordered\" -A8 sqlglot/expressions/*.py | head -12", "description": "Read Redshift generator structure and Ordered definition"}
[tool_result] from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    array_concat_sql,
    concat_to_dpipe_sql,
    concat_ws_to_dpipe_sql,
    date_delta_sql,
    generatedasidentitycolumnconstraint_sql,
    json_extract_segments,
    no_tablesample_sql,
    rename_func,
)
from sqlglot.generator import Generator
from sqlglot.generators.postgres import PostgresGenerator
from sqlglot.helper import seq_get


class RedshiftGenerator(PostgresGenerator):
…[728 chars elided]…
ions/core.py:2049:class Ordered(Expression):
sqlglot/expressions/core.py-2050-    arg_types = {"this": True, "desc": False, "nulls_first": True, "with_fill": False}
sqlglot/expressions/core.py-2051-
sqlglot/expressions/core.py-2052-    @property
sqlglot/expressions/core.py-2053-    def name(self) -> str:
sqlglot/expressions/core.py-2054-        return self.this.name
sqlglot/expressions/core.py-2055-
sqlglot/expressions/core.py-2056-
sqlglot/expressions/core.py-2057-class Add(Expression, Binary):
[tool_use Bash] {"command": "grep -rn \"def unsupported_args\" sqlglot/ ; grep -rn \"import.*unsupported_args\" sqlglot/generators/*.py | head -3; sed -n 268,275p sqlglot/generators/redshift.py", "description": "Locate unsupported_args helper and generator insertion point"}
[tool_result] sqlglot/generator.py:30:def unsupported_args(
sqlglot/generators/clickhouse.py:25:from sqlglot.generator import unsupported_args
sqlglot/generators/drill.py:14:from sqlglot.generator import unsupported_args
sqlglot/generators/exasol.py:16:from sqlglot.generator import unsupported_args
        "where",
        "with",
        "without",
    }

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = expression.expressions
        num_args = len(args)
[assistant] Now the parser change: extend the existing `APPROXIMATE` handler to accept `PERCENTILE_DISC ... WITHIN GROUP`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[643 chars elided]…
      and len(func.expression.expressions) == 1\n            and not func.expression.expressions[0].args.get(\"desc\")\n        ):\n            return self.expression(\n                exp.ApproxQuantile(\n                    this=func.expression.expressions[0].this,\n                    quantile=func.this.this,\n                )\n            )\n        self._retreat(index)\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "        \"APPROXIMATE\": lambda self: self._parse_approximate_count(),", "new_string": "        \"APPROXIMATE\": lambda self: self._parse_approximate(),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[assistant] Now the generator, plus the import for `unsupported_args`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "from sqlglot.generator import Generator\nfrom sqlglot.generators.postgres import PostgresGenerator", "new_string": "from sqlglot.generator import Generator, unsupported_args\nfrom sqlglot.generators.postgres import PostgresGenerator"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "    def unnest_sql(self, expression: exp.Unnest) -> str:\n        args = expression.expressions", "new_string": "    @unsupported_args(\"accuracy\", \"weight\", \"error_tolerance\")\n    def approxquantile_
…[50 chars elided]…
n        order = exp.Order(expressions=[exp.Ordered(this=expression.this.copy())])\n        percentile = exp.PercentileDisc(this=expression.args[\"quantile\"].copy())\n        within_group = exp.WithinGroup(this=percentile, expression=order)\n        return f\"APPROXIMATE {self.sql(within_group)}\"\n\n    def unnest_sql(self, expression: exp.Unnest) -> str:\n        args = expression.expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[assistant] Now I'll add tests next to the existing `APPROXIMATE COUNT` cases, then run them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "        self.validate_all(\n            \"x ~* 'pat'\",", "new_string": "        self.validate_all(\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y)\",\n            read={\n
…[333 chars elided]…
ity(\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y) FROM t\"\n        )\n        self.validate_identity(\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y DESC) FROM t\",\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y DESC) FROM t\",\n        )\n        self.validate_all(\n            \"x ~* 'pat'\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[assistant] I wrote a DESC identity test by mistake: my parser deliberately rejects `DESC` (ApproxQuantile can't represent it), so that line would fail. Removing it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "        self.validate_identity(\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y DESC) FROM t\",\n            \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y DESC) FROM t\",\n        )\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122033-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s,d in [('SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y) FROM t','redshift'),('SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y DESC) FROM t','redshift'),('SELECT APPROX_PERCENTILE(y, 0.5)','snowflake')]:\n    try:\n        e=sqlglot.parse_one(s,read=d); print(repr(e.selects[0])[:200]); print('->', e.sql('redshift'), '|', e.sql('snowflake'), '|', e.sql('duckdb'))\n    except Exception as ex: print('ERR',type(ex).__name__, str(ex)[:120])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_redshift.py 2>&1 | tail -15", "description": "Check parse/generate behavior and run Redshift tests"}
[tool_result] ApproxQuantile(
  this=Column(
    this=Identifier(this=y, quoted=False),
    join_mark=False),
  quantile=Literal(this=0.5, is_string=False),
  join_mark=False)
-> SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y) FROM t | SELECT APPROX_PERCENTILE(y, 0.5) FROM t | SELECT APPROX_QUANTILE(y, 0.5) FROM t
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (
ApproxQuantile(
  this=Column(
    this=Identifier(this=y, quoted=False)),
  quantile=Literal(this=0.5, is_string=False))
-> SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y) | SELECT APPROX_PERCENTILE(y, 0.5) | SELECT APPROX_QUANTILE(y, 0.5)
.................                       [100%]
17 passed, 177 subtests passed in 0.30s
[assistant] Parsing, round-trip, and transpilation work, and `DESC` is rejected rather than silently dropped. Now the full suite using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] ............................................................ [ 25%]
........................................................................ [ 32%]
..................................................................... [ 38%]
................................................ [ 42%]
........................................................ [ 47%]
...................................... [ 51%]
.................................................. [ 55%]
...................................................
…[51 chars elided]…
......................................................... [ 69%]
...................................................... [ 74%]
............................................. [ 78%]
................................................................................................................................................................................................... [ 96%]
.......................... [ 98%]
..................              [100%]
1103 passed, 17892 subtests passed in 48.24s
[tool_use Bash] {"command": "(ruff --version && ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py && ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py) 2>&1 | tail -8; git status --short; git diff --stat", "description": "Lint, format-check, and show changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generators/redshift.py
 M sqlglot/parsers/redshift.py
 M tests/dialects/test_redshift.py
 sqlglot/generators/redshift.py  |  9 ++++++++-
 sqlglot/parsers/redshift.py     | 17 +++++++++++++++--
 tests/dialects/test_redshift.py | 13 +++++++++++++
 3 files changed, 36 insertions(+), 3 deletions(-)
[assistant] `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 passed) and ruff check and format are clean. I haven't committed anything.

How it's mapped:
- **Parser** (`sqlglot/parsers/redshift.py`): the `APPROXIMATE` handler, renamed from `_parse_approximate_count` to `_parse_approximate`, now also accepts `PERCENTILE_DISC ... WITHIN GROUP` and builds an `exp.ApproxQuantile(this=x, quantile=p)`. It only accepts a single ordering key without `DESC`. `DESC` would change the meaning and `ApproxQuantile` ca
…[155 chars elided]…
CENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is decorated with `unsupported_args("accuracy", "weight", "error_tolerance")`, so those arguments raise instead of being dropped silently.
- **Tests** (`tests/dialects/test_redshift.py`): added a `validate_all` case covering Redshift round-trip and Snowflake `APPROX_PERCENTILE(y, 0.5)` in both directions, and a `validate_identity` case. I didn't change any existing test.

Verified: `ApproxQuantile` generates `APPROX_QUANTILE` for DuckDB and `APPROX_PERCENTILE` for Snowflake, and the existing `APPROXIMATE COUNT(DISTINCT ...)` behavior is unchanged.
