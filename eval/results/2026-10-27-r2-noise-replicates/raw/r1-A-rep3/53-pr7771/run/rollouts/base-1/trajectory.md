# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full suite passes: 1121 tests, 18178 subtests.

The fix is in `sqlglot/parsers/druid.py`. `DruidParser` was an empty subclass, so I registered `JSON_VALUE` in `FUNCTION_PARSERS` to call the shared `_parse_json_value` helper, the same way the MySQL, Trino and Exasol parsers do. I added a round-trip assertion to `tests/dialects/test_druid.py`.

The shared helper also accepts `ON EMPTY` / `ON ERROR` clauses after `RETURNING`. Druid's documented `JSON_VALUE` has only the `RETURNING` form, so those clauses are accepted here but aren't Druid syntax. I left that as is to match the other dialects; say if you want Druid restricted to `RETURNING` only.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"RETURNING\\|JSON_VALUE\\|JSONValue\\|JSON_VALUE\" sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/dialect.py | head -50; grep -n \"class JSONValue\\|class JSONExtract\\b\" -A12 sqlglot/expressions.py | head -60"}
[tool_result] sqlglot/dialects/dialect.py:374:    e.g JSON_VALUE vs JSON_EXTRACT_SCALAR in BigQuery
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls; grep -rln \"JSON_VALUE\\|JSONValue\" --include=*.py . | grep -v tests | head; grep -rn \"RETURNING\" --include=*.py sqlglot | head -30"}
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
(eval):1: no matches found: --include=*.py
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"RETURNING\" sqlglot/ | head -30; echo ---; grep -rn \"JSON_VALUE\\|JSONValue\\|JSON_EXISTS\" sqlglot/ | head -30; echo ---; cat sqlglot/dialects/druid.py | head -80"}
[tool_result] sqlglot/tokens.py:368:        "RETURNING": TokenType.RETURNING,
sqlglot/tokenizer_core.py:396:    RETURNING = auto()
sqlglot/parser.py:3497:        returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:        if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:            elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:        by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py
…[4730 chars elided]…
 expression: exp.JSONValueArray | exp.JSONExtractArray
sqlglot/generators/duckdb.py:1006:    data_type = "ARRAY<STRING>" if isinstance(expression, exp.JSONValueArray) else "ARRAY<JSON>"
sqlglot/generators/duckdb.py:1708:        exp.JSONBExists: rename_func("JSON_EXISTS"),
---
from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
[tool_use Bash] {"command": "cat sqlglot/parsers/druid.py; echo ---; sed -n 1,40p sqlglot/parsers/exasol.py | grep -n \"import\\|class\" ; sed -n 115,130p sqlglot/parsers/exasol.py; echo ---; sed -n 8025,8050p sqlglot/parser.py; sed -n 10028,10050p sqlglot/parser.py; echo ---; sed -n 5528,5542p sqlglot/generator.py; echo; grep -n \"JSON_VALUE\" tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_exasol.py tests/dialects/test_trino.py | head"}
[tool_result] from __future__ import annotations

from sqlglot.parser import Parser


class DruidParser(Parser):
    pass
---
1:from __future__ import annotations
4:from sqlglot import exp, parser
5:from sqlglot.dialects.dialect import (
12:from sqlglot.helper import seq_get
13:from sqlglot.tokens import TokenType
30:class ExasolParser(parser.Parser):
        TokenType.SYSTIMESTAMP: exp.Systimestamp,
        TokenType.CURRENT_SCHEMA: exp.CurrentSchema,
    }

    FUNCTION_PARSERS = {
        **parser.Parser.F
…[4241 chars elided]…
LL ON ERROR) AS x""",
tests/dialects/test_exasol.py:894:                "exasol": """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
tests/dialects/test_exasol.py:895:                "trino": """SELECT JSON_VALUE('{"d":"a"}', '$.d' NULL ON ERROR) AS x""",
tests/dialects/test_mysql.py:1559:        self.validate_identity(f"""SELECT JSON_VALUE({json_doc}, '$.price')""")
tests/dialects/test_mysql.py:1561:            f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
[tool_use Bash] {"command": "cat sqlglot/generators/druid.py; echo ---; cat tests/dialects/test_druid.py | head -60; echo ---; grep -n \"FUNCTION_PARSERS\" -A3 sqlglot/parsers/mysql.py | head; ls <work>/env-sqlglot/bin/python"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # https://druid.apache.org/docs/latest/querying/sql-data-types/
    TYPE_MAPPING = {
        **generator.Generator.TYPE
…[1250 chars elided]…
K)" for dialect in Dialects}
        self.validate_all(
            "FLOOR(__time TO WEEK)",
            write=write,
        )
---
154:    FUNCTION_PARSERS = {
155:        **parser.Parser.FUNCTION_PARSERS,
156-        "GROUP_CONCAT": lambda self: self._parse_group_concat(),
157-        # https://dev.mysql.com/doc/refman/5.7/en/miscellaneous-functions.html#function_values
158-        "VALUES": lambda self: self.expression(
<work>/env-sqlglot/bin/python
[assistant] Druid's parser is empty, so I'll wire `JSON_VALUE` to the shared `_parse_json_value` helper, the same way MySQL, Trino and Exasol do.
[tool_use Bash] {"command": "cat > sqlglot/parsers/druid.py <<'EOF'\nfrom __future__ import annotations\n\nfrom sqlglot import parser\n\n\nclass DruidParser(parser.Parser):\n    FUNCTION_PARSERS = {\n        **parser.Parser.FUNCTION_PARSERS,\n        # https://druid.apache.org/docs/latest/querying/sql-json-functions/\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }\nEOF\npython3 - <<'EOF'\ni
…[416 chars elided]…
thon -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", dialect='druid').sql('druid'))\"\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py 2>&1 | tail -5"}
[tool_result]  sqlglot/parsers/druid.py     | 10 +++++++---
 tests/dialects/test_druid.py |  1 +
 2 files changed, 8 insertions(+), 3 deletions(-)
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
.......................................................... [ 73%]
.... [ 78%]
.................                                            [100%]
79 passed, 1102 subtests passed in 0.39s
[assistant] The Druid tests and the MySQL/Trino/Exasol neighbours pass. Now the full project check suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short"}
[tool_result] ................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 53.29s
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged. The full suite passes: 1121 tests, 18178 subtests.

The fix is in `sqlglot/parsers/druid.py`. `DruidParser` was an empty subclass, so I registered `JSON_VALUE` in `FUNCTION_PARSERS` to call the shared `_parse_json_value` helper, the same way the MySQL, Trino and Exasol parsers do. I added a round-trip assertion to `tests/dialects/test_druid.py`.

The shared helper also accepts `ON EMPTY` / `ON ERROR` clauses after `RETURNING`. Druid's documented `JSON_VALUE` has only the `RETURNING` form, so those clauses are accepted here but aren't Druid syntax. I left that as is to match the other dialects; say if you want Druid restricted to `RETURNING` only.

I haven't committed anything.
