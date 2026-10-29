# trajectory base-1

final message:
Exasol `LISTAGG` now parses `x` as the value and `','` as the separator, the same as Oracle, Snowflake and Trino, and it round-trips.

The cause was in `sqlglot/parsers/exasol.py`: `LISTAGG` was mapped to the `GROUP_CONCAT` parser, which folds extra arguments into a `CONCAT`. I moved `LISTAGG` onto the shared `_parse_string_agg` parser that Oracle and Snowflake use. `GROUP_CONCAT` keeps its own parser, so its `SEPARATOR` syntax is unchanged.

Checks:
- `SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t` now gives `separator=','` and round-trips in Exasol.
- Transpiled to Oracle, Snowflake and Trino it gives the same SQL back. DuckDB gets its own `LISTAGG(x, ',' ORDER BY y)` form, as before.
- I added a round-trip case and Oracle/Snowflake/Trino read cases to `tests/dialects/test_exasol.py`. No existing test was changed.
- Full suite: 1126 passed. `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything; the changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -n -i \"listagg\\|GroupConcat\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/parser.py sqlglot/generator.py | head -80; grep -n -i \"listagg\" tests/dialects/test_exasol.py | head"}
[tool_result] sqlglot/dialects/dialect.py:2423:def groupconcat_sql(
sqlglot/dialects/dialect.py:2425:    expression: exp.GroupConcat,
sqlglot/dialects/dialect.py:2426:    func_name: str = "LISTAGG",
sqlglot/dialects/dialect.py:2454:    listagg: exp.Expr = exp.Anonymous(this=func_name, expressions=[args])
sqlglot/dialects/dialect.py:2460:            listagg = exp.WithinGroup(this=listagg, expression=order)
sqlglot/dialects/dialect.py:2465:        listagg.set("expressions", [f"{args}{modifiers}"])
sqlglot/diale
…[548 chars elided]…
urn self.expression(exp.GroupConcat(this=this, separator=separator))
326:            "SELECT id, department, hire_date, LISTAGG(id, ',') WITHIN GROUP (ORDER BY hire_date) OVER (PARTITION BY department rows BETWEEN 1 preceding AND 1 following) AS GROUP_CONCAT_RESULT FROM employee_table ORDER BY department, hire_date",
331:                "exasol": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
334:                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
[tool_use Bash] {"command": "sed -n 7890,7950p sqlglot/parser.py; echo ----; sed -n 2420,2470p sqlglot/dialects/dialect.py; echo ----; grep -n \"GROUP_CONCAT\\|GroupConcat\\|LISTAGG\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/parser.py | head -60"}
[tool_result]             action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
            default=default,
        )

    def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disjunction))
        else:
…[3833 chars elided]…
Concat:
sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7928:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7935:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7941:            exp.GroupConcat(
sqlglot/parser.py:10094:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; echo ----; grep -rn \"LISTAGG\\|ListAgg\" sqlglot/ | grep -v \"^sqlglot/dialects/dialect.py\" | head -30"}
[tool_result] from __future__ import annotations


from sqlglot import tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.exasol import ExasolGenerator
from sqlglot.parsers.exasol import DATE_UNITS as DATE_UNITS, ExasolParser
from sqlglot.tokens import TokenType


class Exasol(Dialect):
    # https://docs.exasol.com/db/latest/sql_references/basiclanguageelements.htm#SQLidentifier
    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
    # htt
…[2070 chars elided]…
e.py:738:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/duckdb.py:195:            ("GROUP_CONCAT", "LISTAGG", "STRINGAGG"), lambda self: self._parse_string_agg()
sqlglot/generators/redshift.py:89:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/exasol.py:352:            self, e, func_name="LISTAGG", within_group=True
sqlglot/generators/duckdb.py:2105:        SELECT LISTAGG(
[tool_use Bash] {"command": "grep -n \"_parse_group_concat\" -A30 sqlglot/parsers/exasol.py | head -60; echo ----; sed -n 340,360p sqlglot/generators/exasol.py; echo ----; sed -n 10070,10096p sqlglot/parser.py; echo; grep -n \"def _parse_group_concat\" -A5 sqlglot/parser.py"}
[tool_result] 123:        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
124-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
125-        "JSON_VALUE": lambda self: self._parse_json_value(),
126-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_extract.htm
127-        "JSON_EXTRACT": lambda self: self._parse_json_extract(),
128-    }
129-
130-    def _parse_sta
…[3097 chars elided]…
ATOR) else None

        return self.expression(exp.GroupConcat(this=this, separator=separator))

    def _parse_initcap(self) -> exp.Initcap:

10057:    def _parse_group_concat(self) -> exp.Expr | None:
10058-        def concat_exprs(node: exp.Expr | None, exprs: list[exp.Expr]) -> exp.Expr:
10059-            if isinstance(node, exp.Distinct) and len(node.expressions) > 1:
10060-                concat_exprs = [
10061-                    self.expression(
10062-                        exp.Concat(
[tool_use Bash] {"command": "sed -n 315,345p tests/dialects/test_exasol.py; grep -n \"GROUP_CONCAT\\|SEPARATOR\" tests/dialects/test_exasol.py | head -30"}
[tool_result]         self.validate_identity("SELECT TO_CHAR(12345.6789) AS TO_CHAR")
        self.validate_identity("SELECT TO_CHAR(-12345.67890, '000G000G000D000000MI') AS TO_CHAR")
        self.validate_all(
            "SELECT TO_CHAR(CAST('2009-10-04 22:23:00' AS TIMESTAMP), 'DAY MONTH YYYY')",
            read={
                "mysql": "SELECT DATE_FORMAT('2009-10-04 22:23:00', '%W %M %Y')",
            },
        )

        self.validate_identity(
            "SELECT id, department, hire_date, GROUP_C
…[1470 chars elided]…
n 1 preceding and 1 following) GROUP_CONCAT_RESULT from employee_table ORDER BY department, hire_date",
326:            "SELECT id, department, hire_date, LISTAGG(id, ',') WITHIN GROUP (ORDER BY hire_date) OVER (PARTITION BY department rows BETWEEN 1 preceding AND 1 following) AS GROUP_CONCAT_RESULT FROM employee_table ORDER BY department, hire_date",
329:            "GROUP_CONCAT(DISTINCT x ORDER BY y DESC)",
332:                "mysql": "GROUP_CONCAT(DISTINCT x ORDER BY y DESC SEPARATOR ',')",
[assistant] The Exasol parser maps `LISTAGG` to `_parse_group_concat`, which is the `GROUP_CONCAT` path (it reads the separator via `SEPARATOR` and folds the extra args into a `CONCAT`). Oracle, Snowflake and Trino use `_parse_string_agg`, which handles `LISTAGG(x, sep) WITHIN GROUP`. I'll move `LISTAGG` onto that parser and leave `GROUP_CONCAT` alone.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/exasol.py && sed -n 118,124p sqlglot/parsers/exasol.py"}
[tool_result] from __future__ import annotations


from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_date_delta,
    build_formatted_time,
    build_timetostr_or_tochar,
    build_trunc,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType

DATE_UNITS = {"DAY", "WEEK", "MONTH", "YEAR", "HOUR", "MINUTE", "SECOND"}


# https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/zeroifnull.htm
def _build_zeroif
…[83 chars elided]…
.Null())

    FUNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105008-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105008-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[assistant] Now I'll check the behaviour against the reported case and the other dialects.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.__file__)\nsql='SELECT LISTAGG(x, \\',\\') WITHIN GROUP (ORDER BY y) FROM t'\ne=sqlglot.parse_one(sql, read='exasol')\nprint(repr(e.find(sqlglot.exp.GroupConcat)))\nprint(e.sql('exasol'))\nfor d in ['oracle','snowflake','trino','duckdb']:\n    print(d, sqlglot.transpile(sql, read='exasol', write=d))\nprint(sqlglot.transpile('SELECT LISTAGG(DISTINCT x, \\',\\') WITHIN GROUP (ORDER BY y DESC) FROM t', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t', read='exasol', write='exasol'))\nprint(sqlglot.transpile('SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR \\',\\') FROM t', read='exasol', write='exasol'))\n\""}
[tool_result] ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105008-exasol-dialect-the-second-argume/base-1/sqlglot/__init__.py
GroupConcat(
  this=Order(
    this=Column(
      this=Identifier(this=x, quoted=False)),
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=y, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this=',', is_string=True))
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
oracle ["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
snowflake ["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
trino ["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
duckdb ["SELECT LISTAGG(x, ',' ORDER BY y) FROM t"]
["SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t"]
["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
[assistant] The separator is now parsed correctly and round-trips. I'll add a regression test next to the existing `GROUP_CONCAT` test, then run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-105008-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"EDIT_DISTANCE(col1, col2)\",", "new_string": "        self.validate_identity(\n            \"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\",\n            
…[110 chars elided]…
   \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            read={\n                \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"trino\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"EDIT_DISTANCE(col1, col2)\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-105008-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] ....................                                               [100%]
20 passed, 582 subtests passed in 0.22s
.......................................... [ 78%]
......................................................................................................................................................................................................... [ 96%]
.......................... [ 98%]
................                [100%]
1126 passed, 18227 subtests passed in 62.04s (0:01:02)
[assistant] Full suite passes. I'll run the linter on the changed files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git diff --stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parsers/exasol.py     |  3 ++-
 tests/dialects/test_exasol.py | 12 ++++++++++++
 2 files changed, 14 insertions(+), 1 deletion(-)
[assistant] Exasol `LISTAGG` now parses `x` as the value and `','` as the separator, the same as Oracle, Snowflake and Trino, and it round-trips.

The cause was in `sqlglot/parsers/exasol.py`: `LISTAGG` was mapped to the `GROUP_CONCAT` parser, which folds extra arguments into a `CONCAT`. I moved `LISTAGG` onto the shared `_parse_string_agg` parser that Oracle and Snowflake use. `GROUP_CONCAT` keeps its own parser, so its `SEPARATOR` syntax is unchanged.

Checks:
- `SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t` now gives `separator=','` and round-trips in Exasol.
- Transpiled to Oracle, Snowflake and Trino it gives the same SQL back. DuckDB gets its own `LISTAGG(x, ',' ORDER BY y)` form, as before.
- I added a round-trip case and Oracle/Snowflake/Trino read cases to `tests/dialects/test_exasol.py`. No existing test was changed.
- Full suite: 1126 passed. `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything; the changes are in the working tree.
