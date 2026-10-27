# trajectory base-1

final message:
Redshift now parses `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`, round-trips it, and transpiles it. The full suite passes (1103 tests), and ruff check and format are clean on the three changed files. I haven't committed anything.

**What changed**
- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts a `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` and builds an `exp.ApproxQuantile(this=x, quantile=p)`. Anything else still falls back to the old behavior, so `APPROXIMATE AS y` still works.
- **Generator** (`sqlglot/generators/redshift.py`): new `approxquantile_sql` writes `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is marked `@unsupported_args("accuracy", "weight", "error_tolerance")`, since Redshift can't express those options.
- **Tests** (`tests/dialects/test_redshift.py`): one `validate_all` covering Redshift round-trip plus DuckDB and Presto in both directions.

**Transpilation checked**
- Redshift → DuckDB and Postgres: `APPROX_QUANTILE(x, 0.5)`
- Redshift → Presto and Snowflake: `APPROX_PERCENTILE(x, 0.5)`
- Presto and DuckDB approximate percentiles → Redshift: the `APPROXIMATE PERCENTILE_DISC … WITHIN GROUP` form

**Decision for you:** `WITHIN GROUP (ORDER BY x DESC)` is still a `ParseError`. `ApproxQuantile` has no descending flag, so I didn't want to drop the direction silently. If you want that case supported, it needs a new representation, which I'd keep out of this change.

## events
[assistant] I'll start by finding how the Redshift dialect handles `APPROXIMATE` today.
[tool_use Bash] {"command": "grep -rn -i \"approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn -i \"approx\" tests/dialects/test_redshift.py | head", "description": "Search for APPROXIMATE handling in the codebase"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:63:                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:67:                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
[assistant] The grep missed `expressions.py`, so I'll check the repo layout and the Redshift parser directly.
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn -i \"approximate\" sqlglot/ | head -30", "description": "List package files and find APPROXIMATE references"}
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
sqlglot/parsers/redshift.py:65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
sqlglot/parsers/redshift.py:99:    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:
sqlglot/parsers/
…[980 chars elided]…
22:    _sql_names = ["APPROXIMATE_SIMILARITY", "APPROXIMATE_JACCARD_INDEX"]
sqlglot/generators/redshift.py:75:        exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
sqlglot/generators/exasol.py:362:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/approximate_count_distinct.htm
sqlglot/generators/exasol.py:363:        exp.ApproxDistinct: unsupported_args("accuracy")(rename_func("APPROXIMATE_COUNT_DISTINCT")),
[tool_use Bash] {"command": "sed -n 55,120p sqlglot/parsers/redshift.py; echo ----; sed -n 60,90p sqlglot/generators/redshift.py; echo ----; grep -n -i \"percentile_disc\\|PercentileDisc\\|WithinGroup\" sqlglot/expressions/*.py sqlglot/parsers/*.py sqlglot/generators/redshift.py sqlglot/generators/base.py | head -30", "description": "Read Redshift parser/generator APPROXIMATE code and percentile refs"}
[tool_result]         ),
        "SPLIT_TO_ARRAY": lambda args: exp.StringToArray(
            this=seq_get(args, 0), expression=seq_get(args, 1) or exp.Literal.string(",")
        ),
        "STRTOL": exp.FromBase.from_arg_list,
        "TEXTLEN": exp.Length.from_arg_list,
    }

    NO_PAREN_FUNCTION_PARSERS = {
        **PostgresParser.NO_PAREN_FUNCTION_PARSERS,
        "APPROXIMATE": lambda self: self._parse_approximate_count(),
        "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp(sysdate=
…[3469 chars elided]…
his"))),
        exp.RegexpExtract: rename_func("REGEXP_SUBSTR"),
        exp.Select: transforms.preprocess(
----
ugrep: warning: sqlglot/generators/base.py: No such file or directory
sqlglot/expressions/aggregate.py:218:class PercentileDisc(Expression, AggFunc):
sqlglot/expressions/aggregate.py:222:PERCENTILES = (PercentileCont, PercentileDisc)
sqlglot/expressions/core.py:1750:class WithinGroup(Expression):
sqlglot/parsers/duckdb.py:157:        "QUANTILE_DISC": exp.PercentileDisc.from_arg_list,
[assistant] Redshift's `APPROXIMATE` only handles `COUNT(DISTINCT)`. Next I'll reproduce the error and check whether an approximate-quantile expression already exists.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; $PY -c \"\nimport sqlglot\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t','SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try:\n        e=sqlglot.parse_one(s,read='redshift'); print(repr(e)); print(e.sql('redshift'))\n    except Exception as ex: print('ERR',type(ex).__name__, ex)\n\" 2>&1 | head -60; grep -rn -i \"ApproxQuantile\\|APPROX_QUANTILE\\|approx_percentile\" sqlglot/ | head -30", "description": "Reproduce the Redshift parse error and search approx-quantile refs"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
Select(
  expressions=[
    WithinGroup(
      this=Percenti
…[2890 chars elided]…
lglot/generators/duckdb.py:4411:            self.unsupported("APPROX_QUANTILES bucket count must be a positive integer")
sqlglot/generators/duckdb.py:4419:        return self.sql(exp.ApproxQuantile(this=this, quantile=exp.Array(expressions=quantiles)))
sqlglot/generators/singlestore.py:186:        exp.ApproxQuantile: unsupported_args("accuracy", "weight")(
sqlglot/generators/singlestore.py:188:                "APPROX_PERCENTILE",
sqlglot/generators/singlestore.py:405:        "approx_percentile",
[assistant] The parser fails because `APPROXIMATE` only accepts `COUNT(DISTINCT)`. Next I'll read the `ApproxQuantile`/`PercentileDisc` definitions and how the generators render them.
[tool_use Bash] {"command": "sed -n 195,245p sqlglot/expressions/aggregate.py; echo ----; grep -n \"def approxquantile\\|def quantile\\|def percentile\\|def withingroup\\|def withingroup_sql\\|approxquantile_sql\\|ApproxQuantile\\|PercentileDisc\\|WithinGroup\" sqlglot/generator.py sqlglot/generators/*.py | head -40; echo ----; grep -n \"ApproxQuantile\\|Quantile\" sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/parsers/redshift.py sqlglot/parsers/base.py 2>/dev/null | head; ls sqlglot/parsers | head -80", "description": "Inspect quantile expression classes and generator handlers"}
[tool_result]     pass


class Mode(Expression, AggFunc):
    arg_types = {"this": False, "deterministic": False}


class Ntile(Expression, AggFunc):
    arg_types = {"this": False}


class NthValue(Expression, AggFunc):
    arg_types = {"this": True, "offset": True, "from_first": False}


class ObjectAgg(Expression, AggFunc):
    arg_types = {"this": True, "expression": True}


class PercentileCont(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class PercentileDisc(Expression, Ag
…[2189 chars elided]…
supported_args("accuracy", "weight")(
sqlglot/generators/spark2.py:193:            exp.WithinGroup: transforms.preprocess(
----
__init__.py
__pycache__
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
[assistant] Snowflake and Presto already map `ApproxQuantile` to their approximate-percentile functions. Now I'll check where `WITHIN GROUP` is parsed and how Snowflake handles approximate percentiles, so the Redshift version follows the same pattern.
[tool_use Bash] {"command": "grep -n \"WITHIN\\|WithinGroup\" sqlglot/parser.py sqlglot/parsers/*.py | head -20; echo ----; sed -n 925,945p sqlglot/generators/snowflake.py; echo ----; sed -n 255,270p sqlglot/generators/presto.py; echo ----; grep -n \"def add_within_group_for_percentiles\" -A 12 sqlglot/transforms.py; echo ----; grep -n \"APPROX\\|Quantile\\|WITHIN\" tests/dialects/test_redshift.py tests/dialects/test_postgres.py | head -20", "description": "Locate WITHIN GROUP parsing and related tests"}
[tool_result] sqlglot/parser.py:7734:            # The order is parsed through `this` as a canonicalization for WITHIN GROUPs
sqlglot/parser.py:7738:        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
sqlglot/parser.py:7739:        # This is done "manually", instead of letting _parse_window parse it into an exp.WithinGroup node, so that
sqlglot/parser.py:7741:        if not self._match_text_seq("WITHIN", "GROUP"):
sqlglot/parser.py:8127:        # 
…[3387 chars elided]…

tests/dialects/test_postgres.py:601:                "presto": "SELECT APPROX_PERCENTILE(amount, 0.5)",
tests/dialects/test_postgres.py:602:                "spark": "SELECT PERCENTILE_APPROX(amount, 0.5)",
tests/dialects/test_postgres.py:603:                "trino": "SELECT APPROX_PERCENTILE(amount, 0.5)",
tests/dialects/test_postgres.py:944:            "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a) FILTER(WHERE CAST(b AS BOOLEAN)) AS mean_value FROM (VALUES (0, 't')) AS fake_data(a, b)"
[assistant] The parser does special-case `WITHIN GROUP` around line 7734. I'll read that section to see how the percentile arguments are laid out in the AST.
[tool_use Bash] {"command": "sed -n 7715,7760p sqlglot/parser.py; echo ----; grep -n \"def remove_within_group_for_percentiles\" -A 12 sqlglot/transforms.py", "description": "Read WITHIN GROUP parsing logic in parser"}
[tool_result]                 on_overflow: exp.Expr | None = exp.var("ERROR")
            else:
                self._match_text_seq("TRUNCATE")
                on_overflow = self.expression(
                    exp.OverflowTruncateBehavior(
                        this=self._parse_string(),
                        with_count=(
                            self._match_text_seq("WITH", "COUNT")
                            or not self._match_text_seq("WITHOUT", "COUNT")
                        ),
               
…[1920 chars elided]…
of their corresponding WITHIN GROUP clause."""
561-    if (
562-        isinstance(expression, exp.WithinGroup)
563-        and isinstance(expression.this, exp.PERCENTILES)
564-        and isinstance(expression.expression, exp.Order)
565-    ):
566-        quantile = expression.this.this
567-        input_value = t.cast(exp.Ordered, expression.find(exp.Ordered)).this
568-        return expression.replace(exp.ApproxQuantile(this=input_value, quantile=quantile))
569-
570-    return expression
571-
[assistant] The canonical AST for a percentile is `WithinGroup(this=PercentileDisc(quantile), expression=Order(...))`. `remove_within_group_for_percentiles` already turns that into `ApproxQuantile(this=column, quantile=p)`, so I can reuse that shape. Next I'll check the imports in the Redshift parser and generator.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/redshift.py; echo ----; sed -n 1,25p sqlglot/generators/redshift.py; echo ----; grep -n \"def approx\\|def withingroup_sql\" -A 8 sqlglot/generator.py | head -30; echo; grep -n \"def _parse_function\\b\" -A 3 sqlglot/parser.py | head; grep -n \"unsupported_args\" sqlglot/generators/redshift.py | head -3", "description": "Check imports and helper signatures for Redshift files"}
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
…[869 chars elided]…
_sql = self.sql(expression, "expression")[1:]  # order has a leading space
3286-        return f"{this} WITHIN GROUP ({expression_sql})"
3287-
3288-    def between_sql(self, expression: exp.Between) -> str:
3289-        this = self.sql(expression, "this")
3290-        low = self.sql(expression, "low")
3291-        high = self.sql(expression, "high")

6758:    def _parse_function(
6759-        self,
6760-        functions: dict[str, t.Callable] | None = None,
6761-        anonymous: bool = False,
[assistant] I have what I need. I'll make the parser change first: `APPROXIMATE` will accept `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` and build an `ApproxQuantile`, and it will still fall back for anything else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[707 chars elided]…
    and len(func.expression.expressions) == 1\n            and not func.expression.expressions[0].args.get(\"desc\")\n        ):\n            return self.expression(\n                exp.ApproxQuantile(\n                    this=func.expression.expressions[0].this,\n                    quantile=func.this.this,\n                )\n            )\n\n        self._retreat(index)\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[assistant] Next is the generator. The repo guidance says a single-entry-point handler should be an auto-discovered `<expr>_sql` method, so I'll add `approxquantile_sql` next to the existing Redshift methods.
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/generators/redshift.py | head -40; grep -rn \"def unsupported_args\" sqlglot/ | head -2", "description": "List Redshift generator methods and locate unsupported_args"}
[tool_result] 273:    def unnest_sql(self, expression: exp.Unnest) -> str:
290:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
297:    def datatype_sql(self, expression: exp.DataType) -> str:
313:    def alterset_sql(self, expression: exp.AlterSet) -> str:
323:    def array_sql(self, expression: exp.Array) -> str:
329:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
332:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
335:    def explode_sql(self, expression: exp.Explode) -> str:
339:    def _unix_to_time_sql(self, expression: exp.UnixToTime) -> str:
sqlglot/generator.py:30:def unsupported_args(
[tool_use Bash] {"command": "sed -n 320,340p sqlglot/generators/redshift.py", "description": "Read Redshift generator methods near the end"}
[tool_result]         return f"SET{exprs}{location}{file_format}"

    def array_sql(self, expression: exp.Array) -> str:
        if expression.args.get("bracket_notation"):
            return super().array_sql(expression)

        return rename_func("ARRAY")(self, expression)

    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
        return Generator.ignorenulls_sql(self, expression)

    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
        return Generator.respectnulls_sql(self, expression)

    def explode_sql(self, expression: exp.Explode) -> str:
        self.unsupported("Unsupported EXPLODE() function")
        return ""

    def _unix_to_time_sql(self, expression: exp.UnixToTime) -> str:
        scale = expression.args.get("scale")
[assistant] I'll add `approxquantile_sql` after `explode_sql`, using the same `unsupported_args` pattern as Snowflake for options Redshift cannot express.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "    def explode_sql(self, expression: exp.Explode) -> str:\n        self.unsupported(\"Unsupported EXPLODE() function\")\n        return \"\"\n", "new_string": "    def explode_sql(self, expression: exp.Exp
…[137 chars elided]…
"weight\", \"error_tolerance\")\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        order = exp.Order(expressions=[exp.Ordered(this=expression.this)])\n        percentile = exp.WithinGroup(\n            this=exp.PercentileDisc(this=expression.args.get(\"quantile\")),\n            expression=order,\n        )\n        return f\"APPROXIMATE {self.sql(percentile)}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "from sqlglot.generator import Generator\nfrom sqlglot.generators.postgres import PostgresGenerator", "new_string": "from sqlglot.generator import Generator, unsupported_args\nfrom sqlglot.generators.postgres import PostgresGenerator"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[assistant] Both halves are in. Before writing tests, I'll run a quick check of parsing, round-trip, and transpilation.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t'\nprint(repr(sqlglot.parse_one(s,read='redshift').selects[0]))\nfor d in ['redshift','duckdb','presto','snowflake','postgres']:\
…[19 chars elided]…
ot.transpile(s,read='redshift',write=d)[0])\ns2='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x DESC) FROM t'\nprint(sqlglot.transpile(s2,read='redshift',write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t',read='presto',write='redshift')[0])\n\" 2>&1 | tail -20", "description": "Check parse, round-trip and transpile of APPROXIMATE percentile"}
[tool_result]   File "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/parser.py", line 2154, in _parse
    return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/sqlglot/parser.py", line 2124, in _pa
…[365 chars elided]…
 PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x DESC) FROM t
ApproxQuantile(
  this=Column(
    this=Identifier(this=x, quoted=False),
    join_mark=False),
  quantile=Literal(this=0.5, is_string=False),
  join_mark=False)
redshift SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
duckdb SELECT APPROX_QUANTILE(x, 0.5) FROM t
presto SELECT APPROX_PERCENTILE(x, 0.5) FROM t
snowflake SELECT APPROX_PERCENTILE(x, 0.5) FROM t
postgres SELECT APPROX_QUANTILE(x, 0.5) FROM t
[assistant] Parsing, round-trip, and transpiling all work. The `DESC` case still raises a `ParseError`, which matches the old behavior. `ApproxQuantile` has no descending flag, so I'm leaving that unsupported rather than silently dropping the direction. The script stopped before the Presto-to-Redshift check, so I'll run that and look at the existing test block.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t',read='presto',write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_QUANTILE(x, 0.5) FROM t',read='duckdb',write='redshift')[0])\n\" 2>&1 | tail -3; sed -n 58,70p tests/dialects/test_redshift.py", "description": "Check Presto and DuckDB to Redshift output and view test block"}
[tool_result] SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
            },
        )
        self.validate_all(
            "SELECT APPROXIMATE COUNT(DISTINCT y)",
            read={
                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
            },
            write={
                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
            },
        )
        self.validate_all(
[assistant] Presto and DuckDB approximate percentiles now both come back as the Redshift form. I'll add a regression test next to the existing `APPROXIMATE AS y` identity test, which keeps `APPROXIMATE` usable as an alias.
[tool_use Bash] {"command": "sed -n 360,368p tests/dialects/test_redshift.py", "description": "View test lines around APPROXIMATE identity test"}
[tool_result]         self.validate_identity("CAST('foo' AS HLLSKETCH)")
        self.validate_identity("'abc' SIMILAR TO '(b|c)%'")
        self.validate_identity("'%' SIMILAR TO '^%' ESCAPE '^'")
        self.validate_identity("CREATE TABLE datetable (start_date DATE, end_date DATE)")
        self.validate_identity("SELECT APPROXIMATE AS y")
        self.validate_identity("CREATE TABLE t (c BIGINT IDENTITY(0, 1))")
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS AVRO 'auto'"
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "        self.validate_identity(\"SELECT APPROXIMATE AS y\")\n", "new_string": "        self.validate_identity(\"SELECT APPROXIMATE AS y\")\n        self.validate_all(\n            \"SELECT APPROXIMATE PERC
…[141 chars elided]…
\",\n                \"presto\": \"SELECT APPROX_PERCENTILE(x, 0.5) FROM t\",\n            },\n            write={\n                \"redshift\": \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t\",\n                \"duckdb\": \"SELECT APPROX_QUANTILE(x, 0.5) FROM t\",\n                \"presto\": \"SELECT APPROX_PERCENTILE(x, 0.5) FROM t\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144505-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[assistant] Now I'll run the project's test command, first the Redshift and Postgres dialect tests and then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_redshift.py tests/dialects/test_postgres.py 2>&1 | tail -15; echo ====; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run Redshift/Postgres tests then full pytest suite", "timeout": 900000}
[tool_result ERROR] Exit code 1
..........................................                                                  [100%]
42 passed, 557 subtests passed in 0.44s
(eval):1: === not found
[assistant] The targeted tests pass (42 passed). The `====` separator was parsed as a shell command, so I'll rerun the full suite on its own.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
........................................................................ [ 32%]
..................................................................... [ 38%]
......................................
…[262 chars elided]…
............................................................................................................................... [ 74%]
............................................. [ 78%]
................................................................................................................................................................................................... [ 95%]
..............................................            [100%]
1103 passed, 17894 subtests passed in 51.43s
[assistant] The full suite passes: 1103 tests. Last, I'll run the linter and formatter on the three changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files; show git status"}
[tool_result] All checks passed!
3 files already formatted
 M sqlglot/generators/redshift.py
 M sqlglot/parsers/redshift.py
 M tests/dialects/test_redshift.py
[assistant] Redshift now parses `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`, round-trips it, and transpiles it. The full suite passes (1103 tests), and ruff check and format are clean on the three changed files. I haven't committed anything.

**What changed**
- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts a `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` and builds an `exp.ApproxQuantile(this=x, quantile=p)`. Anything else still falls back to the old behavior, so `APPROXIMATE AS y` still works.
- **Generator** (`sqlglot/generators/redshift.py`): new
…[277 chars elided]…
overing Redshift round-trip plus DuckDB and Presto in both directions.

**Transpilation checked**
- Redshift → DuckDB and Postgres: `APPROX_QUANTILE(x, 0.5)`
- Redshift → Presto and Snowflake: `APPROX_PERCENTILE(x, 0.5)`
- Presto and DuckDB approximate percentiles → Redshift: the `APPROXIMATE PERCENTILE_DISC … WITHIN GROUP` form

**Decision for you:** `WITHIN GROUP (ORDER BY x DESC)` is still a `ParseError`. `ApproxQuantile` has no descending flag, so I didn't want to drop the direction silently. If you want that case supported, it needs a new representation, which I'd keep out of this change.
