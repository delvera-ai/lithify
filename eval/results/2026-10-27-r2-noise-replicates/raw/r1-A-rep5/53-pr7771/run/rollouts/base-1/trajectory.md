# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full test suite passes (1121 passed) and ruff is clean.

The cause was that Druid's parser had no `JSON_VALUE` hook, so the call fell through to the generic function parser, which doesn't understand `RETURNING`. MySQL, Trino and Exasol route `JSON_VALUE` through the shared `_parse_json_value()`, which already handles `RETURNING`.

Changes:
- `sqlglot/parsers/druid.py`: `DruidParser` gets a `FUNCTION_PARSERS` entry for `JSON_VALUE` that calls `_parse_json_value()`, matching the other dialects.
- `tests/dialects/test_druid.py`: added a `validate_identity` round-trip for `SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t`.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask for one; the repo's CONTRIBUTING rules also ask for a conventional-commit title with the model name appended.

## events
[tool_use Bash] {"command": "grep -rn \"RETURNING\" sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py sqlglot/parser.py | head -50; grep -rn \"JSON_VALUE\\|JSONValue\\|JSONValue\" sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/parser.py | head -40", "description": "Find RETURNING and JSON_VALUE handling across dialects"}
[tool_result] sqlglot/parser.py:3497:        returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:        if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:            elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:        by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8088:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10036:        returning = self._match(TokenType.RETURNING) and self._parse_type()
sqlglot/parser.py:8034:        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the opposite (e.g. JSON_EXISTS)
sqlglot/parser.py:10031:    def _parse_json_value(self) -> exp.JSONValue:
sqlglot/parser.py:10039:            exp.JSONValue(
[tool_use Bash] {"command": "sed -n 8020,8100p sqlglot/parser.py; echo ----; sed -n 10025,10050p sqlglot/parser.py; echo ----; grep -n \"JSON_VALUE\\|JSONValue\\|_parse_json_value\\|JSON_VALUE\" sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py sqlglot/dialects/dialect.py sqlglot/generator.py sqlglot/expressions.py | head -30", "description": "Inspect JSON value parsing and related dialect code"}
[tool_result]         self._match_text_seq("VALUE")
        value = self._parse_bitwise()

        if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
…[3367 chars elided]…
st[exp.Expr]) -> exp.Expr:
            if isinstance(node, exp.Distinct) and len(node.expressions) > 1:
                concat_exprs = [
----
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/dialect.py:374:    e.g JSON_VALUE vs JSON_EXTRACT_SCALAR in BigQuery
sqlglot/generator.py:5531:    def jsonvalue_sql(self, expression: exp.JSONValue) -> str:
sqlglot/generator.py:5539:        return self.func("JSON_VALUE", expression.this, f"{path}{returning}{on_condition}")
[tool_use Bash] {"command": "grep -rn \"JSON_VALUE\\|json_value\\|JSONValue\" sqlglot/ --include=*.py | grep -v \"^sqlglot/optimizer\" | head -40; echo ----; cat sqlglot/dialects/druid.py | head -80; echo ----; grep -n \"JSON_VALUE\\|RETURNING\" tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py | head -30", "description": "Locate JSON_VALUE wiring and druid dialect code"}
[tool_result] (eval):1: no matches found: --include=*.py
----
from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
----
tests/dialects/test_trino.py:151:            "JSON_VALUE(jl.extra_attributes, 'lax $.amount_source' RETURNING VARCHAR)"
tests/dialects/test_trino.py:155:        self.validate_identity(f"""SELECT JSON_VALUE({json_doc}, 'stri
…[704 chars elided]…
py:895:                "trino": """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
tests/dialects/test_mysql.py:1559:        self.validate_identity(f"""SELECT JSON_VALUE({json_doc}, '$.price')""")
tests/dialects/test_mysql.py:1561:            f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_mysql.py:1566:                f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
[tool_use Bash] {"command": "cat sqlglot/parsers/druid.py; echo ----; cat sqlglot/generators/druid.py; echo ----; ls sqlglot/parsers | head -80; echo ----; grep -rn \"JSON_VALUE\\|JSONValue\\|json_value\" sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generators/*.py | head -30", "description": "Read druid parser and generator modules"}
[tool_result] from __future__ import annotations

from sqlglot.parser import Parser


class DruidParser(Parser):
    pass
----
from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # http
…[2902 chars elided]…
t/generators/snowflake.py:511:        exp.JSONValueArray: _json_extract_value_array_sql,
sqlglot/generators/singlestore.py:1440:    def jsonvalue_sql(self, expression: exp.JSONValue) -> str:
sqlglot/generators/singlestore.py:1442:            self.unsupported("JSON_VALUE does not support on_condition")
sqlglot/generators/tsql.py:104:    json_value = self.func("JSON_VALUE", expression.this, expression.expression)
sqlglot/generators/tsql.py:105:    return self.func("ISNULL", json_query, json_value)
[tool_use Bash] {"command": "sed -n 150,170p sqlglot/parsers/mysql.py; echo ----; sed -n 1,35p sqlglot/parsers/trino.py; echo ----; sed -n 5525,5545p sqlglot/generator.py; echo ----; ls tests/dialects | grep -i druid; grep -n \"def test\\|validate\" tests/dialects/test_druid.py | head -20", "description": "Check mysql/trino parser wiring and druid tests"}
[tool_result]         "WEEKOFYEAR": lambda args: exp.WeekOfYear(this=exp.TsOrDsToDate(this=seq_get(args, 0))),
        "YEAR": lambda args: exp.Year(this=exp.TsOrDsToDate(this=seq_get(args, 0))),
    }

    FUNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
        # https://dev.mysql.com/doc/refman/5.7/en/miscellaneous-functions.html#function_values
        "VALUES": lambda self: self.expression(
            exp.Anonymous(this="VALU
…[2487 chars elided]…
M t")
12:        self.validate_identity("SELECT CEIL(price, 2) AS rounded_price FROM t")
13:        self.validate_identity("SELECT FLOOR(__time TO WEEK) FROM t")
14:        self.validate_identity("SELECT FLOOR(col) FROM t")
15:        self.validate_identity("SELECT FLOOR(price, 2) AS rounded_price FROM t")
16:        self.validate_identity("SELECT CURRENT_TIMESTAMP")
17:        self.validate_identity("SELECT ARRAY[1, 2, 3]")
19:        # validate across all dialects
21:        self.validate_all(
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", dialect='druid').sql('druid'))\" 2>&1 | tail -3; cat tests/dialects/test_druid.py", "description": "Reproduce the Druid parse error and read druid tests"}
[tool_result]     raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT) FROM t
from sqlglot.dialects.dialect import Dialects
from tests.dialects.test_dialect import Validator


class TestDruid(Validator):
    dialect = "druid"

    def test_druid(self):
        self.validate_identity("SELECT MOD(1000, 60)")
        self.validate_identity("SELECT CEIL(__time TO WEEK) FROM t")
        self.validate_identity("SELECT CEIL(col) FROM t")
        
…[116 chars elided]…
(__time TO WEEK) FROM t")
        self.validate_identity("SELECT FLOOR(col) FROM t")
        self.validate_identity("SELECT FLOOR(price, 2) AS rounded_price FROM t")
        self.validate_identity("SELECT CURRENT_TIMESTAMP")
        self.validate_identity("SELECT ARRAY[1, 2, 3]")

        # validate across all dialects
        write = {dialect.value: "FLOOR(__time TO WEEK)" for dialect in Dialects}
        self.validate_all(
            "FLOOR(__time TO WEEK)",
            write=write,
        )
[assistant] Reproduced. Druid's parser has no `JSON_VALUE` hook, so it falls through to the generic function parser. MySQL, Trino and Exasol route `JSON_VALUE` through `_parse_json_value`, which already handles `RETURNING`. I'll do the same for Druid.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131052-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131052-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131052-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131052-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py 2>&1 | tail -3; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='druid'))\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='mysql'))\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run druid tests and full suite"}
[tool_result] .                                        [100%]
1 passed, 32 subtests passed in 0.19s
["SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t"]
["SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`) FROM t"]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 50.82s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/druid.py tests/dialects/test_druid.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/druid.py tests/dialects/test_druid.py) 2>&1 | tail -3; git status --short", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full test suite passes (1121 passed) and ruff is clean.

The cause was that Druid's parser had no `JSON_VALUE` hook, so the call fell through to the generic function parser, which doesn't understand `RETURNING`. MySQL, Trino and Exasol route `JSON_VALUE` through the shared `_parse_json_value()`, which already handles `RETURNING`.

Changes:
- `sqlglot/parsers/druid.py`: `DruidParser` gets a `FUNCTION_PARSERS` entry for `JSON_VALUE` that calls `_parse_json_value()`, matching the other dialects.
- `tests/dialects/test_druid.py`: added a `validate_identity` round-trip for `SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t`.

The change is uncommitted in the worktree. I didn't commit it because you didn't ask for one; the repo's CONTRIBUTING rules also ask for a conventional-commit title with the model name appended.
