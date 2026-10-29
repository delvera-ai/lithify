# trajectory base-1

final message:
`JSON_VALUE(x, '$.a' RETURNING BIGINT)` now parses and round-trips unchanged in the Druid dialect. The full test suite passes (1121 passed) and ruff check and format are clean. I haven't committed.

The cause was that Druid's parser inherited the base parser, which has no `JSON_VALUE` handler, so the call fell back to a generic function and the `RETURNING` clause was a syntax error.

Changes:
- **`sqlglot/parsers/druid.py`**: `DruidParser` now registers `JSON_VALUE` to use the shared `_parse_json_value()` helper, as MySQL, Trino and Exasol already do.
- **`tests/dialects/test_druid.py`**: added round-trip identity tests for `JSON_VALUE(x, '$.a')` and the `RETURNING BIGINT` form.

Side effect: a plain `JSON_VALUE(x, '$.a')` in Druid now parses to the `JSONValue` expression instead of a generic function. It still generates the same SQL, so no output changes for that form.

## events
[tool_use Bash] {"command": "grep -rn \"RETURNING\\|JSON_VALUE\\|JSONValue\\|JSONExtractScalar\" sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/dialect.py | head -60; grep -n \"class JSONValue\\|class JSONExtractScalar\" -A 12 sqlglot/expressions.py", "description": "Find JSON_VALUE handling across dialects"}
[tool_result ERROR] Exit code 2
sqlglot/dialects/dialect.py:45:    exp.JSONExtract, exp.JSONExtractScalar, exp.JSONBExtract, exp.JSONBExtractScalar
sqlglot/dialects/dialect.py:374:    e.g JSON_VALUE vs JSON_EXTRACT_SCALAR in BigQuery
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"RETURNING\" sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/dialect.py sqlglot/parser.py | head -40", "description": "List package and search RETURNING handling"}
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
sqlglot/parser.py:3497:        returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:        if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:            elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:        by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8088:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10036:        returning = self._match(TokenType.RETURNING) and self._parse_type()
[tool_use Bash] {"command": "sed -n 10020,10060p sqlglot/parser.py; grep -rn \"JSONValue\\b\" sqlglot --include=*.py | head -30; echo ---; cat sqlglot/dialects/druid.py | head -80", "description": "Inspect JSON_VALUE parsing and Druid dialect"}
[tool_result]         return self.expression(exp.Declare(expressions=expressions, replace=replace))

    def build_cast(self, strict: bool, **kwargs) -> exp.Expr:
        exp_class = exp.Cast if strict else exp.TryCast

        if exp_class == exp.TryCast:
            kwargs["requires_string"] = self.dialect.TRY_CAST_REQUIRES_STRING

        return self.expression(exp_class(**kwargs))

    def _parse_json_value(self) -> exp.JSONValue:
        this = self._parse_bitwise()
        self._match(TokenType.COMMA)
 
…[776 chars elided]…
    safe=True,
                            coalesce=self.dialect.CONCAT_COALESCE,
                        )
                    )
                ]
                node.set("expressions", concat_exprs)
                return node
(eval):1: no matches found: --include=*.py
---
from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
[tool_use Bash] {"command": "cat sqlglot/parsers/druid.py; echo ---GEN; cat sqlglot/generators/druid.py; echo ---; grep -rn \"_parse_json_value\\|JSON_VALUE\" sqlglot/parsers sqlglot/parser.py sqlglot/generators sqlglot/dialects | head -40", "description": "Read Druid parser and generator"}
[tool_result] from __future__ import annotations

from sqlglot.parser import Parser


class DruidParser(Parser):
    pass
---GEN
from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # ht
…[1475 chars elided]…
ore.py:1442:            self.unsupported("JSON_VALUE does not support on_condition")
sqlglot/generators/bigquery.py:36:DQUOTES_ESCAPING_JSON_FUNCTIONS = ("JSON_QUERY", "JSON_VALUE", "JSON_QUERY_ARRAY")
sqlglot/generators/bigquery.py:333:        exp.JSONValueArray: rename_func("JSON_VALUE_ARRAY"),
sqlglot/generators/duckdb.py:4634:                this=rename_func("JSON_VALUE")(self, expression), expression="'$'"
sqlglot/dialects/dialect.py:374:    e.g JSON_VALUE vs JSON_EXTRACT_SCALAR in BigQuery
[tool_use Bash] {"command": "grep -rn \"def jsonvalue_sql\\|def jsonvalue\\|JSONValue\" sqlglot/generator.py sqlglot/generators/*.py | head; grep -n \"def jsonvalue_sql\" -A 25 sqlglot/generator.py; sed -n 155,165p sqlglot/parsers/mysql.py; sed -n 20,28p sqlglot/parsers/trino.py; sed -n 120,128p sqlglot/parsers/exasol.py; grep -n \"class JSONValue\" -A 12 sqlglot/expressions/*.py; grep -n \"JSON_VALUE\\|RETURNING\" tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py | head -20", "description": "Inspect JSONValue generator and existing tests"}
[tool_result] sqlglot/generator.py:5531:    def jsonvalue_sql(self, expression: exp.JSONValue) -> str:
sqlglot/generators/duckdb.py:1003:    self: DuckDBGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
sqlglot/generators/duckdb.py:1006:    data_type = "ARRAY<STRING>" if isinstance(expression, exp.JSONValueArray) else "ARRAY<JSON>"
sqlglot/generators/duckdb.py:1712:        exp.JSONValueArray: _json_extract_value_array_sql,
sqlglot/generators/bigquery.py:333:        exp.JSONValueArray: rename_fu
…[5591 chars elided]…
R) AS price"""
tests/dialects/test_exasol.py:890:        self.validate_identity("""SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""")
tests/dialects/test_exasol.py:892:            """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
tests/dialects/test_exasol.py:894:                "exasol": """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
tests/dialects/test_exasol.py:895:                "trino": """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in [\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", \\\"SELECT JSON_VALUE(x, '\\$.a') FROM t\\\"]:\n    try: print(sqlglot.transpile(q, read='druid', write='druid'))\n    except Exception as e: print('ERR', e)\nprint(repr(sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a') FROM t\\\", read='druid')))\n\"; cat tests/dialects/test_druid.py | head -60; grep -n \"FUNCTION_PARSERS\" sqlglot/parsers/*.py | head -5", "description": "Reproduce and inspect current Druid JSON_VALUE behavior"}
[tool_result] ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT) FROM t
["SELECT JSON_VALUE(x, '$.a') FROM t"]
Select(
  expressions=[
    Anonymous(
      this=JSON_VALUE,
      expressions=[
        Column(
          this=Identifier(this=x, quoted=False)),
        Literal(this='$.a', is_string=True)])],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))))
from sqlglot.dialects.dialect import Dialects
from tests.dialects.test_dialect import Valida
…[823 chars elided]…
       "FLOOR(__time TO WEEK)",
            write=write,
        )
sqlglot/parsers/clickhouse.py:363:    FUNCTION_PARSERS = {
sqlglot/parsers/clickhouse.py:364:        **{k: v for k, v in parser.Parser.FUNCTION_PARSERS.items() if k != "MATCH"},
sqlglot/parsers/clickhouse.py:382:    NO_PAREN_FUNCTION_PARSERS = {
sqlglot/parsers/clickhouse.py:383:        k: v for k, v in parser.Parser.NO_PAREN_FUNCTION_PARSERS.items() if k != "ANY"
sqlglot/parsers/databricks.py:29:    NO_PAREN_FUNCTION_PARSERS = {
[tool_use Bash] {"command": "grep -n \"FUNCTION_PARSERS = {\" -A 3 sqlglot/parsers/exasol.py | head; sed -n 1,12p sqlglot/parsers/exasol.py", "description": "Check parser class conventions for FUNCTION_PARSERS"}
[tool_result] 119:    FUNCTION_PARSERS = {
120-        **parser.Parser.FUNCTION_PARSERS,
121-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
122-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm
from __future__ import annotations


from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_date_delta,
    build_formatted_time,
    build_timetostr_or_tochar,
    build_trunc,
)
from sqlglot.helper import seq_get
[assistant] Druid's parser inherits from the base `Parser` with no overrides, so the fix is to register `JSON_VALUE` with the shared `_parse_json_value` helper, the same way MySQL, Trino and Exasol do.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103449-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103449-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103449-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a')\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103449-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py 2>&1 | tail -15; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='druid'))\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='mysql'))\"", "description": "Run Druid tests and verify round-trip"}
[tool_result] .                                        [100%]
1 passed, 32 subtests passed in 0.19s
["SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t"]
["SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`) FROM t"]
[assistant] The Druid test passes and the round-trip is correct. Now the full project check suite, to make sure the parser change doesn't affect other dialects.
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
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
1121 passed, 18178 subtests passed in 54.17s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/druid.py tests/dialects/test_druid.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/druid.py tests/dialects/test_druid.py) 2>&1 | tail -5; git status --short; git diff", "description": "Lint, format-check and show the diff"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
diff --git a/sqlglot/parsers/druid.py b/sqlglot/parsers/druid.py
index 20f2cef3a..ecdb528a1 100644
--- a/sqlglot/parsers/druid.py
+++ b/sqlglot/parsers/druid.py
@@ -4,4 +4,7 @@ from sqlglot.parser import Parser
 
 
 class DruidParser(Parser):
-    pass
+    FUNCTION_PARSERS = {
+        **Parser.FUNCTION_PARSERS,
+        "JSON_VALUE": lambda self: self._parse_json_value(),
+    }
diff --git 
…[184 chars elided]…
class TestDruid(Validator):
         self.validate_identity("SELECT FLOOR(price, 2) AS rounded_price FROM t")
         self.validate_identity("SELECT CURRENT_TIMESTAMP")
         self.validate_identity("SELECT ARRAY[1, 2, 3]")
+        self.validate_identity("SELECT JSON_VALUE(x, '$.a')")
+        self.validate_identity("SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t")
 
         # validate across all dialects
         write = {dialect.value: "FLOOR(__time TO WEEK)" for dialect in Dialects}
[assistant] `JSON_VALUE(x, '$.a' RETURNING BIGINT)` now parses and round-trips unchanged in the Druid dialect. The full test suite passes (1121 passed) and ruff check and format are clean. I haven't committed.

The cause was that Druid's parser inherited the base parser, which has no `JSON_VALUE` handler, so the call fell back to a generic function and the `RETURNING` clause was a syntax error.

Changes:
- **`sqlglot/parsers/druid.py`**: `DruidParser` now registers `JSON_VALUE` to use the shared `_parse_json_value()` helper, as MySQL, Trino and Exasol already do.
- **`tests/dialects/test_druid.py`**: added round-trip identity tests for `JSON_VALUE(x, '$.a')` and the `RETURNING BIGINT` form.

Side effect: a plain `JSON_VALUE(x, '$.a')` in Druid now parses to the `JSONValue` expression instead of a generic function. It still generates the same SQL, so no output changes for that form.
