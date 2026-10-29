# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged.

The cause was that `DruidParser` didn't register `JSON_VALUE` at all. MySQL, Trino and Exasol each map it to `_parse_json_value()` in their parser's `FUNCTION_PARSERS`, and the generic generator already emits `RETURNING`. So the fix was adding the same entry to Druid:

- `sqlglot/parsers/druid.py`: `DruidParser` now has `FUNCTION_PARSERS` that extends the base set with `"JSON_VALUE": lambda self: self._parse_json_value()`.
- `tests/dialects/test_druid.py`: added `validate_identity("SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t")`.

Results: the Druid, MySQL, Trino and Exasol test files pass (79 tests), and the full suite passes (1121 tests, 18178 subtests). I did not run `ruff` or the `make check` style step, so formatting is unverified beyond matching the surrounding code.

## events
[tool_use Bash] {"command": "grep -rn \"RETURNING\" sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py sqlglot/parser.py | head -50; grep -n \"JSON_VALUE\\|JSONValue\\|JSONExtractScalar\" sqlglot/parser.py sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py | head -40", "description": "Search RETURNING and JSON_VALUE handling across dialects"}
[tool_result] sqlglot/parser.py:3497:        returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:        if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:            elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:        by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8088:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10036:  
…[115 chars elided]…
114:if expr_type is exp.JSONExtractScalar:
sqlglot/parser.py:382:"JSON_EXTRACT_SCALAR": build_extract_json_with_path(exp.JSONExtractScalar),
sqlglot/parser.py:383:"JSON_EXTRACT_PATH_TEXT": build_extract_json_with_path(exp.JSONExtractScalar),
sqlglot/parser.py:1023:exp.JSONExtractScalar(
sqlglot/parser.py:8034:# MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the ...
sqlglot/parser.py:10031:def _parse_json_value(self) -> exp.JSONValue:
sqlglot/parser.py:10039:exp.JSONValue(
[tool_use Bash] {"command": "sed -n 8025,8050p sqlglot/parser.py; sed -n 10025,10050p sqlglot/parser.py; grep -n \"JSON_VALUE\\|JSONValue\\|_parse_json_value\\|JSON_VALUE\" sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py sqlglot/dialects/dialect.py sqlglot/generator.py | head -30; grep -n \"JSON_VALUE\" tests/dialects/*.py | head -30", "description": "Inspect JSON value parser and related dialect code"}
[tool_result]         return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the opposite (e.g. JSON_EXISTS)
        if self.diale
…[4594 chars elided]…
$[0].attr[0].name')) FROM vartab""",
tests/dialects/test_snowflake.py:1365:...SON_QUERY(v, '$.attr[0].name'), JSON_VALUE(v, '$.attr[0].name')) FROM vartab""",
tests/dialects/test_snowflake.py:1378:..."fruit":"banana"}', '$.fruit'), JSON_VALUE('{"fruit":"banana"}', '$.fruit'))""",
tests/dialects/test_trino.py:151:"JSON_VALUE(jl.extra_attributes, 'lax $.amount_source' RETURNING VARCHAR)"
tests/dialects/test_trino.py:155:self.validate_identity(f"""SELECT JSON_VALUE({json_doc}, 'strict $.price')""")
[assistant] The generic `_parse_json_value` already handles `RETURNING`, so the Druid failure is likely a Druid-specific override. Checking the Druid dialect and how MySQL/Trino wire this up.
[tool_use Bash] {"command": "cat sqlglot/dialects/druid.py; grep -n \"JSON_VALUE\\|JSONValue\\|json_value\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py; grep -n \"class Druid\\|JSON_VALUE\" tests/dialects/test_druid.py | head", "description": "Read Druid dialect and find JSON_VALUE parser wiring"}
[tool_result] from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
3 matches in 1 files:

sqlglot/parser.py:8034:# MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the ...
sqlglot/parser.py:10031:def _parse_json_value(self) -> exp.JSONValue:
sqlglot/parser.py:10039:exp.JSONValue(
0 matches for 'class Druid\|JSON_VALUE'
[tool_use Bash] {"command": "ls sqlglot/parsers/ | head -80; cat sqlglot/parsers/druid.py; grep -rn \"JSON_VALUE\\|JSONValue\\|_parse_json_value\" sqlglot/parsers/ sqlglot/generators/ | head -30; ls tests | grep -i druid", "description": "Inspect parsers package and Druid parser/generator"}
[tool_result] __init__.py  1B
athena.py  2.3K
base.py  582B
bigquery.py  29.8K
clickhouse.py  32.9K
databricks.py  1.9K
doris.py  5.0K
dremio.py  3.8K
drill.py  662B
druid.py  108B
duckdb.py  15.5K
dune.py  124B
exasol.py  6.5K
fabric.py  1.3K
hive.py  11.0K
materialize.py  1.3K
mysql.py  24.1K
oracle.py  9.4K
postgres.py  13.0K
presto.py  5.3K
prql.py  6.9K
redshift.py  5.8K
risingwave.py  2.2K
singlestore.py  10.4K
snowflake.py  54.2K
solr.py  353B
spark.py  5.2K
spark2.py  4.2K
sqlite.py  3.5K
starrocks.py
…[1719 chars elided]…
ONValueArray: _json_extract_value_array_sql,
sqlglot/generators/duckdb.py:1003:    self: DuckDBGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
sqlglot/generators/duckdb.py:1006:    data_type = "ARRAY<STRING>" if isinstance(expression, exp.JSONValueArray) else "ARRAY<JSON>"
sqlglot/generators/duckdb.py:1712:        exp.JSONValueArray: _json_extract_value_array_sql,
sqlglot/generators/duckdb.py:4634:                this=rename_func("JSON_VALUE")(self, expression), expression="'$'"
[assistant] MySQL, Trino and Exasol each register `JSON_VALUE` in their parser's `FUNCTION_PARSERS`; `DruidParser` is empty. Let me look at one of those and the generic generator before changing anything.
[tool_use Bash] {"command": "sed -n 1,40p sqlglot/parsers/trino.py; sed -n 115,130p sqlglot/parsers/exasol.py; sed -n 5528,5545p sqlglot/generator.py; cat sqlglot/generators/druid.py | head -60; ls tests/dialects | grep -i druid; grep -rln \"druid\" tests | head", "description": "Read Trino/Exasol parser, generic JSON generator, Druid generator"}
[tool_result] from __future__ import annotations


from sqlglot import exp, parser
from sqlglot.parsers.presto import PrestoParser
from sqlglot.tokens import TokenType


class TrinoParser(PrestoParser):
    NO_PAREN_FUNCTIONS = {
        **PrestoParser.NO_PAREN_FUNCTIONS,
        TokenType.CURRENT_CATALOG: exp.CurrentCatalog,
    }

    FUNCTIONS = {
        **PrestoParser.FUNCTIONS,
        "VERSION": exp.CurrentVersion.from_arg_list,
    }

    FUNCTION_PARSERS = {
        **PrestoParser.FUNCTION_PARSERS,
 
…[2777 chars elided]…
pes/
    TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.NCHAR: "STRING",
        exp.DType.NVARCHAR: "STRING",
        exp.DType.TEXT: "STRING",
        exp.DType.UUID: "STRING",
    }

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.CurrentTimestamp: lambda *_: "CURRENT_TIMESTAMP",
        exp.Mod: rename_func("MOD"),
        exp.Array: lambda self, e: f"ARRAY[{self.expressions(e)}]",
    }
test_druid.py  982B
tests/dialects/test_druid.py
[assistant] The generic `jsonvalue_sql` already emits `RETURNING`, and the base parser has no `JSON_VALUE` entry. So the fix is to register the same `FUNCTION_PARSERS` entry that MySQL/Trino/Exasol use, in `DruidParser`. Checking the existing Druid test first.
[tool_use Bash] {"command": "cat tests/dialects/test_druid.py; sed -n 1,30p sqlglot/parsers/mysql.py | grep -n \"import\\|class\\|FUNCTION_PARSERS\"", "description": "Read Druid test file and MySQL parser imports"}
[tool_result] from sqlglot.dialects.dialect import Dialects
from tests.dialects.test_dialect import Validator


class TestDruid(Validator):
    dialect = "druid"

    def test_druid(self):
        self.validate_identity("SELECT MOD(1000, 60)")
        self.validate_identity("SELECT CEIL(__time TO WEEK) FROM t")
        self.validate_identity("SELECT CEIL(col) FROM t")
        self.validate_identity("SELECT CEIL(price, 2) AS rounded_price FROM t")
        self.validate_identity("SELECT FLOOR(__time TO WEEK) FR
…[228 chars elided]…
identity("SELECT ARRAY[1, 2, 3]")

        # validate across all dialects
        write = {dialect.value: "FLOOR(__time TO WEEK)" for dialect in Dialects}
        self.validate_all(
            "FLOOR(__time TO WEEK)",
            write=write,
        )
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
[assistant] Now the change: register `JSON_VALUE` in `DruidParser`, using the same lambda the other dialects use.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202737-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202737-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202737-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202737-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", dialect='druid').sql('druid'))\"", "description": "Run Druid and related dialect tests, check round-trip"}
[tool_result] .......................................................... [ 73%]
.... [ 78%]
.................                                            [100%]
79 passed, 1102 subtests passed in 0.46s
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
[assistant] Targeted tests pass and the round-trip works. Now the project's full check suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show git status"}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[89 chars elided]…
........................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 46.06s
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged.

The cause was that `DruidParser` didn't register `JSON_VALUE` at all. MySQL, Trino and Exasol each map it to `_parse_json_value()` in their parser's `FUNCTION_PARSERS`, and the generic generator already emits `RETURNING`. So the fix was adding the same entry to Druid:

- `sqlglot/parsers/druid.py`: `DruidParser` now has `FUNCTION_PARSERS` that extends the base set with `"JSON_VALUE": lambda self: self._parse_json_value()`.
- `tests/dialects/test_druid.py`: added `validate_identity("SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t")`.

Results: the Druid, MySQL, Trino and Exasol test files pass (79 tests), and the full suite passes (1121 tests, 18178 subtests). I did not run `ruff` or the `make check` style step, so formatting is unverified beyond matching the surrounding code.
