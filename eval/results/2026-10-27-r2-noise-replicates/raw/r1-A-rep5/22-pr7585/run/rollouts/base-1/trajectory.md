# trajectory base-1

final message:
Redshift now parses `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` as an approximate quantile, round-trips it in Redshift, and transpiles it. The full suite passes (1103 tests) and ruff check and format are clean. I did not commit.

**Changes**
- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` and builds `exp.ApproxQuantile(this=x, quantile=p)`. It falls back to the existing retreat path for anything else, so `APPROXIMATE AS y` still works.
- **Generator** (`sqlglot/generators/redshift.py`): new `approxquantile_sql` emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`.
- **Tests** (`tests/dialects/test_redshift.py`): one `validate_all` next to the existing `APPROXIMATE COUNT(DISTINCT)` case, covering the Redshift round-trip plus reads from Snowflake and Spark and writes to Snowflake and Spark.

**Choices to review**
- I only accept ascending order. `ORDER BY x DESC` still raises `ParseError`. Silently treating it as ascending would return the wrong quantile.
- Only the single-quantile form is handled. Other dialects' array-quantile forms are not mapped to Redshift.

## events
[tool_use Bash] {"command": "grep -rn \"APPROXIMATE\\|approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/dialect.py | head -50; grep -rn \"APPROXIMATE\" tests/dialects/test_redshift.py | head", "description": "Find APPROXIMATE handling in dialect and parser code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
[tool_use Bash] {"command": "grep -n \"APPROXIMATE\\|PERCENTILE_DISC\\|PercentileDisc\\|WITHIN GROUP\\|WithinGroup\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py sqlglot/dialects/*.py | head -60", "description": "Search percentile and approximate token references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3283:    def withingroup_sql(self, expression: exp.WithinGroup) -> str:
sqlglot/generator.py:3286:        return f"{this} WITHIN GROUP ({expression_sql})"
sqlglot/parser.py:7734:            # The order is parsed through `this` as a canonicalization for WITHIN GROUPs
sqlglot/parser.py:7738:        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
sqlglot/parser.py:7739:        # This is done "manually", instead of letting _parse_window parse it into an exp.WithinGroup node, so that
sqlglot/parser.py:8127:        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
sqlglot/parser.py:8131:            this = self.expression(exp.WithinGroup(this=this, expression=order))
sqlglot/dialects/dialect.py:2445:            listagg = exp.WithinGroup(this=listagg, expression=order)
[tool_use Bash] {"command": "grep -rn \"APPROXIMATE\\|ApproxDistinct\\|PERCENTILE_DISC\\|PercentileDisc\\|ApproxQuantile\" sqlglot/ | grep -v \"\\.pyc\" | head -60; echo ---; sed -n 50,80p tests/dialects/test_redshift.py; echo ---; sed -n 355,370p tests/dialects/test_redshift.py", "description": "Search approximate and percentile references across sqlglot"}
[tool_result] sqlglot/transforms.py:568:        return expression.replace(exp.ApproxQuantile(this=input_value, quantile=quantile))
sqlglot/parsers/redshift.py:65:        "APPROXIMATE": lambda self: self._parse_approximate_count(),
sqlglot/parsers/redshift.py:99:    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:
sqlglot/parsers/redshift.py:104:            return self.expression(exp.ApproxDistinct(this=seq_get(func.this.expressions, 0)))
sqlglot/parsers/spark2.py:82:        "APPROX_PERCENTILE"
…[6596 chars elided]…
REATE TABLE datetable (start_date DATE, end_date DATE)")
        self.validate_identity("SELECT APPROXIMATE AS y")
        self.validate_identity("CREATE TABLE t (c BIGINT IDENTITY(0, 1))")
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS AVRO 'auto'"
        )
        self.validate_identity(
            "COPY test_staging_tbl FROM 's3://your/bucket/prefix/here' IAM_ROLE default FORMAT AS JSON 's3://jsonpaths_file'"
[tool_use Bash] {"command": "sed -n 55,115p sqlglot/parsers/redshift.py; echo ---; sed -n 60,85p sqlglot/generators/redshift.py; echo ---; sed -n 210,245p sqlglot/expressions/aggregate.py; echo ---; sed -n 1,40p sqlglot/parsers/redshift.py | grep -n import; echo ---; grep -n \"PERCENTILE\\|Percentile\" sqlglot/parsers/*.py sqlglot/generators/redshift.py sqlglot/generators/postgres.py | head -30; sed -n 1,30p sqlglot/transforms.py | head -0; grep -n \"def add_within_group_for_percentiles\" -A15 sqlglot/transforms.py", "description": "Inspect redshift parser/generator and percentile classes"}
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
…[5724 chars elided]…
ERCENTILES)
548-        and not isinstance(expression.parent, exp.WithinGroup)
549-        and expression.expression
550-    ):
551-        column = expression.this.pop()
552-        expression.set("this", expression.expression.pop())
553-        order = exp.Order(expressions=[exp.Ordered(this=column)])
554-        expression = exp.WithinGroup(this=expression, expression=order)
555-
556-    return expression
557-
558-
559-def remove_within_group_for_percentiles(expression: exp.Expr) -> exp.Expr:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', 'SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='redshift'); print(repr(e.selects[0]))\n    except Except
…[227 chars elided]…
int(d, e.sql(d))\n    except Exception as ex: print(d,'ERR',ex)\nprint(repr(exp.ApproxQuantile(this=exp.column('x'), quantile=exp.Literal.number(0.5)).sql('redshift')))\n\"; grep -n \"ApproxQuantile\" -A8 sqlglot/generators/snowflake.py | sed -n 1,20p; grep -n \"approxquantile_sql\" -A8 sqlglot/generators/snowflake.py", "description": "Probe current Redshift parse behavior and generator fallback"}
[tool_result] ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
WithinGroup(
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
snowflake SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) 
…[972 chars elided]…
ion.this, expression.args.get("quantile"))
933-
934-    def alterset_sql(self, expression: exp.AlterSet) -> str:
935-        exprs = self.expressions(expression, flat=True)
936-        exprs = f" {exprs}" if exprs else ""
937-        file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
938-        file_format = f" STAGE_FILE_FORMAT = ({file_format})" if file_format else ""
939-        copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[781 chars elided]…
    and len(func.expression.expressions) == 1\n            and not func.expression.expressions[0].args.get(\"desc\")\n        ):\n            return self.expression(\n                exp.ApproxQuantile(\n                    this=func.expression.expressions[0].this,\n                    quantile=func.this.this,\n                )\n            )\n\n        self._retreat(index)\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def \\|^class \\|^from\\|^import\" sqlglot/generators/redshift.py", "description": "List methods and imports in Redshift generator"}
[tool_result] 1:from __future__ import annotations
4:from sqlglot import exp, transforms
5:from sqlglot.dialects.dialect import (
15:from sqlglot.generator import Generator
16:from sqlglot.generators.postgres import PostgresGenerator
17:from sqlglot.helper import seq_get
20:class RedshiftGenerator(PostgresGenerator):
273:    def unnest_sql(self, expression: exp.Unnest) -> str:
290:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
297:    def datatype_sql(self, expression: exp.DataType) -> str:
313:    def alterset_sql(self, expression: exp.AlterSet) -> str:
323:    def array_sql(self, expression: exp.Array) -> str:
329:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
332:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
335:    def explode_sql(self, expression: exp.Explode) -> str:
339:    def _unix_to_time_sql(self, expression: exp.UnixToTime) -> str:
[tool_use Bash] {"command": "sed -n 320,340p sqlglot/generators/redshift.py", "description": "View generator methods near array and explode"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "    def explode_sql(self, expression: exp.Explode) -> str:\n        self.unsupported(\"Unsupported EXPLODE() function\")\n        return \"\"\n", "new_string": "    def explode_sql(self, expression: exp.Exp
…[39 chars elided]…
(\"Unsupported EXPLODE() function\")\n        return \"\"\n\n    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:\n        percentile = exp.PercentileDisc(this=expression.args[\"quantile\"].copy())\n        order = exp.Order(expressions=[exp.Ordered(this=expression.this.copy())])\n        return f\"APPROXIMATE {self.sql(exp.WithinGroup(this=percentile, expression=order))}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[assistant] Now the tests, placed beside the existing `APPROXIMATE COUNT(DISTINCT)` case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "                \"spark\": \"SELECT APPROX_COUNT_DISTINCT(y)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\",", "new_string": "                \"spark\": \"SELECT APPR
…[279 chars elided]…
: \"SELECT PERCENTILE_APPROX(x, 0.5)\",\n            },\n            write={\n                \"redshift\": \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x)\",\n                \"snowflake\": \"SELECT APPROX_PERCENTILE(x, 0.5)\",\n                \"spark\": \"SELECT PERCENTILE_APPROX(x, 0.5)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101849-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ns='SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t'\ne=sqlglot.parse_one(s, read='redshift'); print(repr(e.selects[0].__class__))\nprint(e.sql('redshift'))\nprint(sqlglot.transpile(s, read='redshift', write='snowflake'))\nprint(sqlg
…[90 chars elided]…
ROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x DESC) FROM t','SELECT APPROXIMATE AS y']:\n    try: print(sqlglot.transpile(bad, read='redshift', write='redshift'))\n    except Exception as ex: print('ERR', type(ex).__name__)\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_redshift.py 2>&1 | tail -5", "description": "Verify parse, transpile, and run Redshift tests"}
[tool_result] <class 'sqlglot.expressions.aggregate.ApproxQuantile'>
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
['SELECT APPROX_PERCENTILE(x, 0.5) FROM t']
['SELECT\n  APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY\n    x)\nFROM t']
ERR ParseError
['SELECT APPROXIMATE AS y']
.................                     [100%]
17 passed, 179 subtests passed in 0.32s
[assistant] Redshift tests pass and the DESC form still fails loudly rather than silently changing meaning. Running the full suite and the linter now.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; ($PY -m ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py && $PY -m ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py) 2>&1 | tail -4", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ............................................. [ 78%]
................................................................................................................................................................................................... [ 95%]
..............................................            [100%]
1103 passed, 17894 subtests passed in 55.06s
All checks passed!
3 files already formatted
[assistant] Redshift now parses `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` as an approximate quantile, round-trips it in Redshift, and transpiles it. The full suite passes (1103 tests) and ruff check and format are clean. I did not commit.

**Changes**
- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` now also accepts `PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` and builds `exp.ApproxQuantile(this=x, quantile=p)`. It falls back to the existing retreat path for anything else, so `APPROXIMATE AS y` still works.
- **Generator** (`sqlglot/generators/redshift.py`): new `approxquantile_sql` emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`.
- **Tests** (`tests/dialects/test_redshift.py`): one `validate_all` next to the existing `APPROXIMATE COUNT(DISTINCT)` case, covering the Redshift round-trip plus reads from Snowflake and Spark and writes to Snowflake and Spark.

**Choices to review**
- I only accept ascending order. `ORDER BY x DESC` still raises `ParseError`. Silently treating it as ascending would return the wrong quantile.
- Only the single-quantile form is handled. Other dialects' array-quantile forms are not mapped to Redshift.
