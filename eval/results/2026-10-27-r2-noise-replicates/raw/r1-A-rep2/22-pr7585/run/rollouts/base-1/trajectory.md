# trajectory base-1

final message:
`APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips as Redshift SQL, and transpiles to other dialects. The full test suite passes (1103 passed), and ruff lint and format are clean on the changed files. I did not commit.

Changes:

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts a `WithinGroup` over `PercentileDisc` and builds an `exp.ApproxQuantile` (order key as `this`, percentile as `quantile`). It reuses the existing `APPROXIMATE` hook and retreats otherwise, as the `COUNT(DISTINCT)` path already does.
- **Generator** (`sqlglot/generators/redshift.py`): a new `approxquantile_sql` method emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`.
- **Tests** (`tests/dialects/test_redshift.py`): a `validate_all` case covering Redshift round-trip, Snowflake `APPROX_PERCENTILE` both ways, and Spark `PERCENTILE_APPROX`.

Choices I made that you may want to change:

- I only handle a single ascending order key. `ORDER BY x DESC` still raises `ParseError`, because the quantile would need flipping and I didn't want to guess the semantics.
- `APPROXIMATE PERCENTILE_CONT(...)` still raises `ParseError`. Redshift's documentation I'm working from covers only the `PERCENTILE_DISC` form, and I didn't add `PERCENTILE_CONT` without a clear mapping.
- For Postgres, the output is `APPROX_QUANTILE(...)`, which is the generic default rather than something Postgres actually supports. That matches how `ApproxQuantile` already renders for other dialects.

## events
[tool_use Bash] {"command": "grep -rn -i \"approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn -i \"approximate\" tests/dialects/test_redshift.py | head; grep -rn \"PERCENTILE_DISC\\|APPROX_PERCENTILE\\|ApproxQuantile\" sqlglot/*.py sqlglot/dialects/*.py | head -40", "description": "Search for approximate and percentile handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
sqlglot/transforms.py:568:        return expression.replace(exp.ApproxQuantile(this=input_value, quantile=quantile))
[tool_use Bash] {"command": "ls; grep -rn -i \"APPROXIMATE\" sqlglot/ | head -30; grep -rn \"class ApproxQuantile\\|class PercentileDisc\\|class PercentileCont\" sqlglot/ ; grep -n \"WITHIN GROUP\\|within_group\\|WithinGroup\" sqlglot/parser.py sqlglot/generator.py | head -30", "description": "Locate APPROXIMATE handling and percentile classes"}
[tool_result] AGENTS.md
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
sqlglot/parsers/redshift.py:65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
sqlglot/parsers/redshift.py:99:    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:
sqlglot/parsers/exasol.py:43:        "APPROXIMATE_COUNT_DISTINCT": exp.ApproxDistinct.from_arg_
…[1966 chars elided]…
nonicalization for WITHIN GROUPs
sqlglot/parser.py:7738:        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
sqlglot/parser.py:7739:        # This is done "manually", instead of letting _parse_window parse it into an exp.WithinGroup node, so that
sqlglot/parser.py:8127:        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
sqlglot/parser.py:8131:            this = self.expression(exp.WithinGroup(this=this, expression=order))
[tool_use Bash] {"command": "cat sqlglot/parsers/redshift.py | sed -n 55,120p; echo ----; sed -n 60,90p sqlglot/generators/redshift.py; echo ----; sed -n 205,245p sqlglot/expressions/aggregate.py; echo ----; grep -n \"class Quantile\" -A8 sqlglot/expressions/*.py; echo ----; sed -n 55,75p tests/dialects/test_redshift.py; sed -n 355,370p tests/dialects/test_redshift.py", "description": "Read Redshift parser/generator and related expression code"}
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
…[6235 chars elided]…
REATE TABLE datetable (start_date DATE, end_date DATE)")
        self.validate_identity("SELECT APPROXIMATE AS y")
        self.validate_identity("CREATE TABLE t (c BIGINT IDENTITY(0, 1))")
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS AVRO 'auto'"
        )
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS JSON 's3://jsonpaths_file'"
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one('SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read='redshift')\nprint(repr(e.selects[0]))\nfor d in ['snowflake','duckdb','spark','postgres']:\n    try: print(d, sqlglot.transpile('SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read='redshift', write=d))\n    except Exception as ex: print(d, ex)\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t', read='snowflake', write='redshift'))\n\" 2>&1 | head -30; grep -rn \"ApproxQuantile\" sqlglot/generators sqlglot/parsers sqlglot/dialects | head -30", "description": "Inspect current parse of percentile_disc and related generation"}
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
snowflake ['SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
duckdb ['SELECT QUANTILE_DISC(x, 0.5 ORDER BY x) FROM t']
spark ['SELECT PERCENTILE_APPROX(x, 0.5) FROM t']
postgres ['SELECT PERCENTILE_DISC(0
…[1079 chars elided]…
_PERCENTILE": lambda self: self._parse_quantile_function(exp.ApproxQuantile),
sqlglot/parsers/hive.py:66:        "PERCENTILE_APPROX": lambda self: self._parse_quantile_function(exp.ApproxQuantile),
sqlglot/parsers/snowflake.py:404:        "APPROX_PERCENTILE": exp.ApproxQuantile.from_arg_list,
sqlglot/parsers/presto.py:18:        return exp.ApproxQuantile(
sqlglot/parsers/presto.py:25:        return exp.ApproxQuantile(
sqlglot/parsers/presto.py:28:    return exp.ApproxQuantile.from_arg_list(args)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\np=sqlglot.parser  if False else None\nfrom sqlglot.dialects.redshift import Redshift\nparser=Redshift().parser()\ntoks=Redshift().tokenize('PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x)')\nparser.reset(); parser.sql=''; \nprint(repr(parser._parse_function()))\n\" 2>&1 | tail -15; grep -n \"def _parse_window\\|self._parse_window(\" sqlglot/parser.py | head; grep -n \"def _parse_function(\" -A12 sqlglot/parser.py | head -30", "description": "Check whether _parse_function includes WITHIN GROUP"}
[tool_result] None
6715:            return self._parse_window(this)
6811:            return self._parse_window(parser(self))
6900:        return self._parse_window(result)
8099:    def _parse_window_clause(self) -> list[exp.Expr] | None:
8103:        return self._parse_window(self._parse_id_var(), alias=True)
8123:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
8232:            return self._parse_window(window, alias=alias)
8241:    def _parse_window_spec(self) -> d
…[118 chars elided]…
Callable] | None = None,
6761-        anonymous: bool = False,
6762-        optional_parens: bool = True,
6763-        any_token: bool = False,
6764-    ) -> exp.Expr | None:
6765-        # This allows us to also parse {fn <function>} syntax (Snowflake, MySQL support this)
6766-        # See: https://community.snowflake.com/s/article/SQL-Escape-Sequences
6767-        fn_syntax = False
6768-        if (
6769-            self._match(TokenType.L_BRACE, advance=False)
6770-            and self._next
[assistant] `_parse_function` already wraps the call in `_parse_window`, so the `WITHIN GROUP` node should come back as a `WithinGroup`. I'll add the parse branch and the generator method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[663 chars elided]…
n, exp.Order)\n            and len(func.expression.expressions) == 1\n            and not func.expression.expressions[0].args.get(\"desc\")\n        ):\n            return self.expression(\n                exp.ApproxQuantile(\n                    this=func.expression.expressions[0].this,\n                    quantile=func.this.this,\n                )\n            )\n        self._retreat(index)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"def .*_sql(self\" sqlglot/generators/redshift.py | head -40; grep -n \"class RedshiftGenerator\" sqlglot/generators/redshift.py", "description": "List Redshift generator methods"}
[tool_result] 273:    def unnest_sql(self, expression: exp.Unnest) -> str:
290:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
297:    def datatype_sql(self, expression: exp.DataType) -> str:
313:    def alterset_sql(self, expression: exp.AlterSet) -> str:
323:    def array_sql(self, expression: exp.Array) -> str:
329:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
332:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
335:    def explode_sql(self, expression: exp.Explode) -> str:
339:    def _unix_to_time_sql(self, expression: exp.UnixToTime) -> str:
20:class RedshiftGenerator(PostgresGenerator):
[tool_use Bash] {"command": "sed -n 318,340p sqlglot/generators/redshift.py", "description": "Read generator methods around the insertion point"}
[tool_result]         file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
        file_format = f" FILE FORMAT {file_format}" if file_format else ""

        return f"SET{exprs}{location}{file_format}"

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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "    def explode_sql(self, expression: exp.Explode) -> str:\n        self.unsupported(\"Unsupported EXPLODE() function\")\n        return \"\"\n", "new_string": "    def explode_sql(self, expression: exp.Explode) -> str:\n        self.unsupported(\"Unsupported EXPLODE() function\")\n        return \"\"\n\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        percentile = self.func(\"PERCENTILE_DISC\", expression.args[\"quantile\"])\n        return f\"APPROXIMATE {percentile} WITHIN GROUP (ORDER BY {self.sql(expression, 'this')})\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[assistant] Now I'll check the round-trip and cross-dialect output before adding tests.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nq='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t'\nprint(sqlglot.transpile(q, read='redshift', write='redshift'))\nfor d in ['snowflake','duckdb','spark','postgres','hive','presto']:\n    print(d, sqlglot.transpile(q, read='redshift', write=d))\nprint(sqlgl
…[226 chars elided]…
 in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x DESC) FROM t','SELECT APPROXIMATE PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try: print(sqlglot.transpile(bad, read='redshift', write='redshift'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:120])\n\"", "description": "Verify round-trip and transpilation of approximate percentile_disc"}
[tool_result] ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
snowflake ['SELECT APPROX_PERCENTILE(x, 0.5) FROM t']
duckdb ['SELECT APPROX_QUANTILE(x, 0.5) FROM t']
spark ['SELECT PERCENTILE_APPROX(x, 0.5) FROM t']
postgres ['SELECT APPROX_QUANTILE(x, 0.5) FROM t']
hive ['SELECT PERCENTILE_APPROX(x, 0.5) FROM t']
presto ['SELECT APPROX_PERCENTILE(x, 0.5) FROM t']
['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
['SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_CONT[4m([0m0.5) WITHIN GROUP (
[assistant] Round-trip and cross-dialect output look right. I'll add tests next to the existing `APPROXIMATE COUNT` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "                \"spark\": \"SELECT APPROX_COUNT_DISTINCT(y)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\",", "new_string": "                \"spark\": \"SELECT APPR
…[213 chars elided]…
: \"SELECT APPROX_PERCENTILE(y, 0.5)\",\n            },\n            write={\n                \"redshift\": \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"SELECT APPROX_PERCENTILE(y, 0.5)\",\n                \"spark\": \"SELECT PERCENTILE_APPROX(y, 0.5)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-084803-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_redshift.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run Redshift tests and full project test suite"}
[tool_result] .................                      [100%]
17 passed, 178 subtests passed in 0.37s
............................................. [ 78%]
................................................................................................................................................................................................... [ 95%]
.......................... [ 98%]
...................             [100%]
1103 passed, 17893 subtests passed in 57.09s
[assistant] Both the Redshift tests and the full suite pass. I'll run the linter on the changed files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
3 files already formatted
 M sqlglot/generators/redshift.py
 M sqlglot/parsers/redshift.py
 M tests/dialects/test_redshift.py
[assistant] `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips as Redshift SQL, and transpiles to other dialects. The full test suite passes (1103 passed), and ruff lint and format are clean on the changed files. I did not commit.

Changes:

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts a `WithinGroup` over `PercentileDisc` and builds an `exp.ApproxQuantile` (order key as `this`, percentile as `quantile`). It reuses the existing `APPROXIMATE` hook and retreats otherwise, as the `COUNT(DISTINCT)` path alread
…[361 chars elided]…
 want to change:

- I only handle a single ascending order key. `ORDER BY x DESC` still raises `ParseError`, because the quantile would need flipping and I didn't want to guess the semantics.
- `APPROXIMATE PERCENTILE_CONT(...)` still raises `ParseError`. Redshift's documentation I'm working from covers only the `PERCENTILE_DISC` form, and I didn't add `PERCENTILE_CONT` without a clear mapping.
- For Postgres, the output is `APPROX_QUANTILE(...)`, which is the generic default rather than something Postgres actually supports. That matches how `ApproxQuantile` already renders for other dialects.
