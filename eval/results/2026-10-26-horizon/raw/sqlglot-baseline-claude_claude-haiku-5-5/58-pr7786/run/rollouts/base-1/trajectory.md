# trajectory base-1

final message:
`LISTAGG` in the Exasol dialect now treats the second argument as the separator, and `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` round-trips in Exasol. The full suite passes (1126 tests) and ruff lint and format are clean.

**What was wrong:** `LISTAGG` shared the generic `_parse_group_concat` with `GROUP_CONCAT`. That path folds all positional arguments into a `CONCAT`, so `x` and `','` became one value with no separator.

**Changes:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now has its own `_parse_listagg`. It parses an optional `DISTINCT` on the value, then the value, then an optional comma and separator. `GROUP_CONCAT` keeps the existing shared parser, so its `SEPARATOR` syntax and tests are untouched.
- `tests/dialects/test_exasol.py`: added round-trip checks for `LISTAGG(x, ',')` and `LISTAGG(DISTINCT x, ',')`, plus Oracle and Trino reads and Oracle, Snowflake and Trino writes. No existing assertions were changed.

**Results:**
- `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` now parses with `x` as the value and `','` as the separator, and generates the same SQL in Exasol, Oracle, Snowflake and Trino.
- The `DISTINCT` case first produced a duplicated separator because `DISTINCT` swallowed the whole argument list. Parsing `DISTINCT` explicitly fixed that.

I haven't committed the change.

## events
[tool_use Bash] {"command": "grep -n -i \"listagg\\|GroupConcat\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find LISTAGG handling across dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/dialect.py:2423:def groupconcat_sql(
sqlglot/dialects/dialect.py:2425:    expression: exp.GroupConcat,
sqlglot/dialects/dialect.py:2426:    func_name: str = "LISTAGG",
sqlglot/dialects/dialect.py:2454:    listagg: exp.Expr = exp.Anonymous(this=func_name, expressions=[args])
sqlglot/dialects/dialect.py:2460:            listagg = exp.WithinGroup(this=listagg, expression=order)
sqlglot/dialects/dialect.py:2465:      
…[182 chars elided]…
Concat:
sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7928:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7935:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7941:            exp.GroupConcat(
sqlglot/parser.py:10094:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "sed -n 7885,7960p sqlglot/parser.py; echo ----; sed -n 2415,2470p sqlglot/dialects/dialect.py; echo ----; grep -n -i \"listagg\\|group_concat\\|GroupConcat\" sqlglot/dialects/*.py | head -60", "description": "Read LISTAGG parser and generator code"}
[tool_result]             strict=strict,
            this=this,
            to=to,
            format=fmt,
            safe=safe,
            action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
            default=default,
        )

    def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            
…[4537 chars elided]…
_sql(
sqlglot/dialects/dialect.py:2425:    expression: exp.GroupConcat,
sqlglot/dialects/dialect.py:2426:    func_name: str = "LISTAGG",
sqlglot/dialects/dialect.py:2454:    listagg: exp.Expr = exp.Anonymous(this=func_name, expressions=[args])
sqlglot/dialects/dialect.py:2460:            listagg = exp.WithinGroup(this=listagg, expression=order)
sqlglot/dialects/dialect.py:2465:        listagg.set("expressions", [f"{args}{modifiers}"])
sqlglot/dialects/dialect.py:2467:    return self.sql(listagg)
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py; echo ----; grep -n -i \"groupconcat\\|listagg\\|GROUP_CONCAT\\|STRING_AGG\" sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py; echo ----; grep -rn -i \"listagg\" tests/dialects/*.py | head -40", "description": "Read Exasol dialect and related LISTAGG usages"}
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
…[6578 chars elided]…
(ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5888:                    "trino": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|') WITHIN GROUP (ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5889:                    "duckdb": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|' ORDER BY col2) FROM t",
tests/dialects/test_redshift.py:45:            "LISTAGG(sellerid, ', ')",
tests/dialects/test_redshift.py:51:                # GROUP_CONCAT, LISTAGG and STRING_AGG are aliases in DuckDB
[tool_use Bash] {"command": "grep -n -i \"listagg\\|groupconcat\\|GROUP_CONCAT\\|string_agg\" sqlglot/parsers/exasol.py sqlglot/generators/exasol.py sqlglot/parsers/oracle.py sqlglot/generators/oracle.py; echo ----; sed -n 300,345p tests/dialects/test_exasol.py; echo ----; sed -n 895,915p tests/dialects/test_oracle.py", "description": "Inspect Exasol parser/generator and related tests"}
[tool_result] sqlglot/generators/oracle.py:6:    groupconcat_sql,
sqlglot/generators/oracle.py:67:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, on_overflow=True),
sqlglot/parsers/exasol.py:121:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
sqlglot/parsers/exasol.py:122:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
sqlglot/parsers/exasol.py:123:        **dict.fromkey
…[3601 chars elided]…
SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) "
            "WITHIN GROUP (ORDER BY hire_date) FROM employees"
        )

    def test_merge(self):
        self.validate_all(
            "MERGE INTO target tgt USING (SELECT id, col1 FROM source_tbl) src ON tgt.id = src.id "
            "WHEN MATCHED THEN UPDATE SET tgt.col1 = src.col1 WHERE tgt.some_column IS NULL "
            "WHEN NOT MATCHED THEN INSERT (id, col1) VALUES (src.id, src.col1) WHERE NOT src.col1 IS NULL",
            write={
[tool_use Bash] {"command": "grep -n \"_parse_group_concat\" -A40 sqlglot/parsers/exasol.py | head -80; echo ----; grep -n \"def _parse_group_concat\" -A40 sqlglot/parser.py sqlglot/parsers/*.py | head -60; echo ----; grep -n \"class GroupConcat\" -A12 sqlglot/expressions/*.py | head -30; echo; ls sqlglot/parsers sqlglot/generators | head -100", "description": "Locate Exasol group concat parser and GroupConcat class"}
[tool_result] 123:        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
124-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
125-        "JSON_VALUE": lambda self: self._parse_json_value(),
126-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_extract.htm
127-        "JSON_EXTRACT": lambda self: self._parse_json_extract(),
128-    }
129-
130-    def _parse_sta
…[6393 chars elided]…
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
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN
…[68 chars elided]…
WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR ';') FROM t\\\", \\\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='exasol')\n    print(repr(e.find(sqlglot.exp.GroupConcat)))\n    print(e.sql('exasol'))\n    print(e.sql('oracle'))\n\" 2>&1 | head -60", "description": "Reproduce current Exasol LISTAGG parse results"}
[tool_result] <work>/env-sqlglot/bin/python
GroupConcat(
  this=Concat(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False)),
      Literal(this=',', is_string=True)],
    safe=True,
    coalesce=True))
SELECT LISTAGG(CONCAT(x, ','), ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(CONCAT(COALESCE(x, ''), ','), ',') WITHIN GROUP (ORDER BY y) FROM t
GroupConcat
…[470 chars elided]…
this=x, quoted=False)),
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=y, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this=';', is_string=True))
SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
GroupConcat(
  this=Column(
    this=Identifier(this=x, quoted=False)))
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
[assistant] Reproduced: `LISTAGG` goes through the shared `_parse_group_concat`, which folds every positional argument into a `CONCAT`. Let me check the imports in the Exasol parser before adding a dedicated LISTAGG parser.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/exasol.py; sed -n 112,124p sqlglot/parsers/exasol.py", "description": "Read Exasol parser imports and function table"}
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
…[264 chars elided]…
a,
    }

    FUNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
[assistant] I'll give `LISTAGG` its own parser, where the second positional argument is the separator. `GROUP_CONCAT` keeps the shared path, since its MySQL-style `SEPARATOR` and multi-argument concat behaviour are already covered by tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[73 chars elided]…
 self: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_listagg(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "    def _parse_json_extract(self) -> exp.JSONExtract:", "new_string": "    def _parse_listagg(self) -> exp.GroupConcat:\n        # LISTAGG([DISTINCT] value [, separator]) [WITHIN GROUP (ORDER BY ...)]\n        args = self._parse_csv(self._parse_lambda)\n        return self.expression(\n            exp.GroupConcat(this=seq_get(args, 0), separator=seq_get(args, 1))\n        )\n\n    def _parse_json_extract(self) -> exp.JSONExtract:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\", \\\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FR
…[114 chars elided]…
sol')\n    print(e.sql('exasol'))\n    print(e.sql('oracle'), '|', e.sql('snowflake'), '|', e.sql('trino'))\n\" 2>&1; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_oracle.py tests/dialects/test_snowflake.py tests/dialects/test_trino.py tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Verify LISTAGG round-trip and run dialect tests"}
[tool_result] SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(DISTINCT x, ',', ',') WITHIN GROUP (ORDER BY y DESC) FROM t
SELECT LISTAGG(DISTINCT x, ',', ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FROM t | SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FROM t | SELECT LISTAGG(DISTINCT CA
…[384 chars elided]…
Y y) FROM t
SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
................................................................. [ 32%]
.............................................. [ 55%]
.................................................... [ 81%]
....................................                                             [100%]
199 passed, 2853 subtests passed in 2.89s
[assistant] The non-distinct cases now round-trip, but `LISTAGG(DISTINCT x, ',')` comes out with a duplicated separator. I'll check how `DISTINCT` is parsed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one(\\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read='exasol')\nprint(repr(e.find(sqlglot.exp.GroupConcat)))\n\"; grep -n \"def _parse_lambda\" -A30 sqlglot/parser.py | grep -n -i distinct", "description": "Inspect DISTINCT parse tree for LISTAGG"}
[tool_result] GroupConcat(
  this=Distinct(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False)),
      Literal(this=',', is_string=True)]))
[assistant] `DISTINCT` is parsed as a list that swallows the separator. I'll parse `DISTINCT` explicitly and wrap only the value, as `_parse_string_agg` does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        args = self._parse_csv(self._parse_lambda)\n        return self.expression(\n            exp.GroupConcat(this=seq_get(args, 0), separator=seq_get(args, 1))\n        )", "new_string": "        distinct = self._match(TokenType.DISTINCT)\n        this: exp.Expr = self._parse_lambda()\n        if distinct:\n            this = self.expression(exp.Distinct(expressions=[this]))\n        separator = self._parse_lambda() if self._match(TokenType.COMMA) else None\n        return self.expression(exp.GroupConcat(this=this, separator=separator))"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\", \\\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FR
…[67 chars elided]…
e.sql('exasol'))\n    print(e.sql('oracle'), '|', e.sql('snowflake'), '|', e.sql('trino'), '|', e.sql('duckdb'))\n\" 2>&1; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_oracle.py tests/dialects/test_snowflake.py tests/dialects/test_trino.py tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Re-verify LISTAGG outputs and dialect tests"}
[tool_result] SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',' ORDER BY y) FROM t
SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t
SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FROM t | SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FR
…[89 chars elided]…
TAGG(DISTINCT x, ',' ORDER BY y DESC) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',' ORDER BY y) FROM t
.................................................... [ 81%]
....................................                                             [100%]
199 passed, 2853 subtests passed in 1.57s
[assistant] Both cases now round-trip and cross-dialect output matches. I'll add a regression test next to the existing `GROUP_CONCAT` assertions in `test_exasol.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "                \"databricks\": \"LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)\",\n            },\n        )\n        self.validate_all(\n            \"EDIT_DISTANCE(col1, col2)\",", "new_string":
…[520 chars elided]…
,') WITHIN GROUP (ORDER BY y)\",\n            },\n            write={\n                \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"trino\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"EDIT_DISTANCE(col1, col2)\","}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195258-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Now the full test suite and the repo's linter, using the project's test command from CLAUDE.md.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; ($PY -m ruff check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py && $PY -m ruff format --check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; echo ---; git status --short", "description": "Run full test suite, ruff lint and format check"}
[tool_result] .............................. [ 35%]
................................. [ 38%]
.................... [ 39%]
................... [ 41%]
............................................................... [ 47%]
............................... [ 49%]
.................................................................................................................................. [ 61%]
........ [ 62%]
............................................................................................... [ 70%]
…[55 chars elided]…
......................................... [ 78%]
......................................................................................................................................................................................................... [ 96%]
.......................... [ 98%]
..................              [100%]
1126 passed, 18229 subtests passed in 70.49s (0:01:10)
---
All checks passed!
2 files already formatted
---
 M sqlglot/parsers/exasol.py
 M tests/dialects/test_exasol.py
[assistant] `LISTAGG` in the Exasol dialect now treats the second argument as the separator, and `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` round-trips in Exasol. The full suite passes (1126 tests) and ruff lint and format are clean.

**What was wrong:** `LISTAGG` shared the generic `_parse_group_concat` with `GROUP_CONCAT`. That path folds all positional arguments into a `CONCAT`, so `x` and `','` became one value with no separator.

**Changes:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now has its own `_parse_listagg`. It parses an optional `DISTINCT` on the value, then the value, then an optional comm
…[111 chars elided]…
ched.
- `tests/dialects/test_exasol.py`: added round-trip checks for `LISTAGG(x, ',')` and `LISTAGG(DISTINCT x, ',')`, plus Oracle and Trino reads and Oracle, Snowflake and Trino writes. No existing assertions were changed.

**Results:**
- `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` now parses with `x` as the value and `','` as the separator, and generates the same SQL in Exasol, Oracle, Snowflake and Trino.
- The `DISTINCT` case first produced a duplicated separator because `DISTINCT` swallowed the whole argument list. Parsing `DISTINCT` explicitly fixed that.

I haven't committed the change.
