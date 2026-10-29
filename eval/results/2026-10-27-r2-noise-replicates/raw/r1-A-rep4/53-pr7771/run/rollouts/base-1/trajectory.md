# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full suite passes (1121 tests), and ruff check and format are clean.

The fix is in `sqlglot/parsers/druid.py`. `DruidParser` had no `JSON_VALUE` entry in `FUNCTION_PARSERS`, so it fell back to generic function parsing, which doesn't understand `RETURNING`. I registered it to the shared `_parse_json_value`, the same way Trino and MySQL do. The generator already emits `RETURNING` and the `ON EMPTY` / `ON ERROR` clauses, so no generator change was needed.

I added two identity round-trip assertions to `tests/dialects/test_druid.py`: the `RETURNING BIGINT` case from the report, and a variant with `NULL ON EMPTY NULL ON ERROR`. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"RETURNING\\|JSON_VALUE\\|JSONValue\\|JSON_VALUE\" sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find JSON_VALUE and RETURNING handling across dialects"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:377:    # Whether to generate INSERT INTO ... RETURNING or INSERT INTO RETURNING ...
sqlglot/generator.py:378:    RETURNING_END = True
sqlglot/generator.py:1786:        if self.RETURNING_END:
sqlglot/generator.py:2279:        if self.RETURNING_END:
sqlglot/generator.py:2335:        return f"{self.seg('RETURNING')} {self.expressions(expression, flat=True)}"
sqlglot/generator.py:2654:        if self.RETURNING_EN
…[1059 chars elided]…
NING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8034:        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the opposite (e.g. JSON_EXISTS)
sqlglot/parser.py:8088:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10031:    def _parse_json_value(self) -> exp.JSONValue:
sqlglot/parser.py:10036:        returning = self._match(TokenType.RETURNING) and self._parse_type()
sqlglot/parser.py:10039:            exp.JSONValue(
[tool_use Bash] {"command": "cat sqlglot/dialects/druid.py && grep -rn \"druid\" tests/dialects/test_druid.py | head -5 && grep -n \"RETURNING\" tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py | head", "description": "Read Druid dialect and find existing RETURNING tests"}
[tool_result] from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
tests/dialects/test_druid.py:6:    dialect = "druid"
tests/dialects/test_druid.py:8:    def test_druid(self):
tests/dialects/test_trino.py:151:            "JSON_VALUE(jl.extra_attributes, 'lax $.amount_source' RETURNING VARCHAR)"
tests/dialects/test_trino.py:157:            f
…[41 chars elided]…
rice' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_trino.py:162:                f"""SELECT JSON_VALUE({json_doc}, 'lax $.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
tests/dialects/test_mysql.py:1561:            f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_mysql.py:1566:                f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
[tool_use Bash] {"command": "cat sqlglot/parsers/druid.py; echo ----; cat sqlglot/generators/druid.py; echo ----; sed -n 10025,10050p sqlglot/parser.py; echo ----; grep -rn \"JSON_VALUE\\|JSONValue\\|_parse_json_value\" sqlglot/parsers/*.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/generators/mysql.py | head -30; echo ----; grep -n \"JSON_VALUE\\|JSONValue\" -i tests/dialects/test_druid.py; cat tests/dialects/test_druid.py | head -30", "description": "Read Druid parser/generator and JSON_VALUE parse code"}
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
…[2660 chars elided]…
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
[tool_use Bash] {"command": "sed -n 15,30p sqlglot/parsers/trino.py; echo ----; sed -n 1555,1575p tests/dialects/test_mysql.py; echo ----; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a') FROM t\\\", dialect='druid').sql('druid')))\n\"", "description": "Check Trino parser pattern and current Druid JSON_VALUE behavior"}
[tool_result]     FUNCTIONS = {
        **PrestoParser.FUNCTIONS,
        "VERSION": exp.CurrentVersion.from_arg_list,
    }

    FUNCTION_PARSERS = {
        **PrestoParser.FUNCTION_PARSERS,
        "TRIM": lambda self: self._parse_trim(),
        "JSON_QUERY": lambda self: self._parse_json_query(),
        "JSON_VALUE": lambda self: self._parse_json_value(),
        "LISTAGG": lambda self: self._parse_string_agg(),
    }

    JSON_QUERY_OPTIONS: parser.OPTIONS_TYPE = {
        **dict.fromkeys(
            (
…[527 chars elided]…
son_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
            )

    def test_grant(self):
        grant_cmds = [
            "GRANT 'role1', 'role2' TO 'user1'@'localhost', 'user2'@'localhost'",
            "GRANT SELECT ON world.* TO 'role3'",
            "GRANT SELECT ON db2.invoice TO 'jeffrey'@'localhost'",
            "GRANT INSERT ON `d%`.* TO u",
            "GRANT ALL ON test.* TO ''@'localhost'",
----
"SELECT JSON_VALUE(x, '$.a') FROM t"
[assistant] The Druid parser has no `FUNCTION_PARSERS` entry for `JSON_VALUE`, so it falls back to generic function parsing. I'll wire it to the shared `_parse_json_value` the way Trino and MySQL do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083027-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083027-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", \\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT NULL ON EMPTY NULL ON ERROR) FROM t\\\", \\\"SELECT JSON_VALUE(x, '\\$.a') FROM t\\\"]:\n    print(repr(sqlglot.parse_one(s, dialect='druid').sql('druid')))\n\"", "description": "Check Druid JSON_VALUE RETURNING round-trips"}
[tool_result] "SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t"
"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT NULL ON EMPTY NULL ON ERROR) FROM t"
"SELECT JSON_VALUE(x, '$.a') FROM t"
[assistant] Round-trips work. Now I'll add a regression test next to the existing Druid tests and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083027-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n        self.validate_identity(\n            \"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT NULL ON EMPTY NULL ON ERROR) FROM t\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083027-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite"}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[29 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 49.43s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/druid.py tests/dialects/test_druid.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/druid.py tests/dialects/test_druid.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full suite passes (1121 tests), and ruff check and format are clean.

The fix is in `sqlglot/parsers/druid.py`. `DruidParser` had no `JSON_VALUE` entry in `FUNCTION_PARSERS`, so it fell back to generic function parsing, which doesn't understand `RETURNING`. I registered it to the shared `_parse_json_value`, the same way Trino and MySQL do. The generator already emits `RETURNING` and the `ON EMPTY` / `ON ERROR` clauses, so no generator change was needed.

I added two identity round-trip assertions to `tests/dialects/test_druid.py`: the `RETURNING BIGINT` case from the report, and a variant with `NULL ON EMPTY NULL ON ERROR`. Nothing is committed.
