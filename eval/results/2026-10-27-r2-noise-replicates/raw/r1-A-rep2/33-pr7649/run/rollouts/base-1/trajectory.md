# trajectory base-1

final message:
T-SQL now parses and round-trips `FOR JSON { AUTO | PATH } [, ROOT [('name')]] [, INCLUDE_NULL_VALUES] [, WITHOUT_ARRAY_WRAPPER]`. Other dialects drop the clause and emit the unsupported-option warning, the same as `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

The changes:

- **`sqlglot/parsers/tsql.py`**: added a `JSON_OPTIONS` table for `AUTO`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. `_parse_for` now returns the key along with the options. `FOR XML` still goes to `for_`, and `FOR JSON` goes to a new `for_json` key. `PATH` and `ROOT` reuse the existing XML key-value parser, so they accept the same forms as the XML options.
- **`sqlglot/generator.py`**: `for_modifiers` emits `FOR JSON` when `for_json` has output. Otherwise it emits `FOR XML` as before. Other dialects render each option as empty, so the clause disappears.
- **`tests/dialects/test_tsql.py`**: added `test_for_json`, which covers the option combinations and a pretty-printed case, plus a check that duckdb drops the clause.

Decision for you: I used a separate `for_json` key rather than one shared `for_` list. The shared list would need a marker to tell XML and JSON apart, since `AUTO` and `PATH` are valid in both. The separate key avoids that, but it means a Select can now carry two `FOR` clauses in the AST. Parsing a query with both a `FOR XML` and a `FOR JSON` clause is not rejected.

## events
[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\" sqlglot/ --include=*.py | head -60", "description": "Find FOR XML handling across sqlglot"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\" sqlglot/ tests/ | head -60", "description": "Find FOR XML handling across sqlglot and tests"}
[tool_result] sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
tests/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:697:        for xml_option in xml_possible_options:
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
[tool_use Bash] {"command": "sed -n 480,530p sqlglot/parsers/tsql.py && echo ---- && sed -n 3085,3120p sqlglot/generator.py && echo ---- && sed -n 635,720p tests/dialects/test_tsql.py && echo ---- && grep -n -i \"xml\" sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -30", "description": "Read FOR XML parser, generator, and tests"}
[tool_result]         if not self._match(TokenType.OPTION):
            return None

        def _parse_option() -> exp.Expr | None:
            option = self._parse_var_from_options(OPTIONS)
            if not option:
                return None

            self._match(TokenType.EQ)
            return self.expression(
                exp.QueryOption(this=option, expression=self._parse_primary_or_var())
            )

        return self._parse_wrapped_csv(_parse_option)

    def _parse_xml_key_value_option(
…[6975 chars elided]…
ons.py:431:# XML
sqlglot/expressions/functions.py:434:class XMLElement(Expression, Func):
sqlglot/expressions/functions.py:435:    _sql_names = ["XMLELEMENT"]
sqlglot/expressions/functions.py:443:class XMLGet(Expression, Func):
sqlglot/expressions/functions.py:444:    _sql_names = ["XMLGET"]
sqlglot/expressions/functions.py:448:class XMLTable(Expression, Func):
sqlglot/expressions/query.py:2073:class XMLNamespace(Expression):
sqlglot/expressions/query.py:2077:class XMLKeyValueOption(Expression):
[tool_use Bash] {"command": "grep -rn \"XML_OPTIONS\\|for_\\b\\|\\\"for_\\\"\\|QueryOption\\|\\\"options\\\"\" sqlglot/ | head -40; echo ----; grep -n \"class QueryOption\" -A4 sqlglot/expressions/query.py; grep -n \"class XMLKeyValueOption\" -A4 sqlglot/expressions/query.py; echo ----; ls <work>/env-sqlglot/bin/python && git status --short | head", "description": "Locate XML_OPTIONS and query option plumbing"}
[tool_result] sqlglot/parser.py:2531:                                if arg == "options":
sqlglot/parser.py:2538:                        sequence_props.set("options", options)
sqlglot/parser.py:2634:        seq.set("options", options if options else None)
sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
sqlglot/generator.py:1115:        options = expression.args.get("options")
sqlglot/generator.py:1250:        options = self.expressions(expression, key="options", flat=True, sep=" ")
sqlg
…[2877 chars elided]…
.py:159:    arg_types = {"this": True, "connection": False, "options": True}
sqlglot/expressions/dml.py:304:        "options": False,
----
914:class QueryOption(Expression):
915-    arg_types = {"this": True, "expression": False}
916-
917-
918-class WithTableHint(Expression):
2077:class XMLKeyValueOption(Expression):
2078-    arg_types = {"this": True, "expression": False}
2079-
2080-
2081-class Semicolon(Expression):
----
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "sed -n 85,120p sqlglot/parsers/tsql.py; echo ----; sed -n 300,330p sqlglot/parsers/tsql.py; echo ----; grep -n \"_parse_var_from_options\" -A25 sqlglot/parser.py | head -45; echo ----; grep -rn \"xmlkeyvalueoption\\|XMLKeyValueOption\\|for_modifiers\\|for_\" sqlglot/generators/tsql.py sqlglot/dialects/tsql.py 2>/dev/null | head; ls sqlglot/generators 2>/dev/null | head -50", "description": "Read XML options table and parser option helpers"}
[tool_result]     "OPTIMIZE": (("FOR", "UNKNOWN"),),
    "ORDER": ("GROUP",),
    "PARAMETERIZATION": ("FORCED", "SIMPLE"),
    "ROBUST": ("PLAN",),
    "USE": ("PLAN",),
}


XML_OPTIONS: parser.OPTIONS_TYPE = {
    **dict.fromkeys(
        (
            "AUTO",
            "EXPLICIT",
            "TYPE",
        ),
        tuple(),
    ),
    "ELEMENTS": (
        "XSINIL",
        "ABSENT",
    ),
    "BINARY": ("BASE64",),
}


OPTIONS_THAT_REQUIRE_EQUAL = ("MAX_GRANT_PERCENT", "MIN_GRANT_PERCENT", "LABEL")
…[3265 chars elided]…
         if not event_type:
2644-                self.raise_error("Expected trigger event (INSERT, UPDATE, DELETE, TRUNCATE)")
2645-
----
__init__.py
athena.py
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
python.py
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
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor d in ['duckdb','spark','tsql','postgres']:\n    try:\n        print(d, '=>', repr(sqlglot.transpile('SELECT * FROM t FOR XML PATH, ROOT(\\'r\\')', read='tsql', write=d, unsupported_level=ErrorLevel.WARN)[0]))\n    except Exception as e: pr
…[15 chars elided]…
)\ne = sqlglot.parse_one('SELECT * FROM t FOR XML PATH', read='tsql')\nprint(repr(e.args.get('for_')))\nprint(e.sql('tsql'))\nprint([k for k in sqlglot.exp.Select.arg_types if 'for' in k])\n\"; grep -n \"QUERY_MODIFIER_PARSERS\" -n sqlglot/parser.py | head; grep -n \"XML\" sqlglot/tokens.py sqlglot/tokens_core.py 2>/dev/null | head", "description": "Check current FOR XML behavior across dialects"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
duckdb => 'SELECT * FROM t'
spark => 'SELECT * FROM t'
tsql => "SELECT * FROM t FOR XML PATH, ROOT('r')"
postgres => 'SELECT * FROM t'
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH)))]
SELECT * FROM t FOR XML PATH
['format']
1521:    QUERY_MODIFIER_PARSERS: t.ClassVar = {
1549:    QUERY_MODIFIER_TOKENS: t.ClassVar = set(QUERY_MODIFIER_PARSERS)
4115:                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4117:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
[tool_use Bash] {"command": "grep -rn \"\\\"for_\\\"\\|for_modifiers\\|\\\"options\\\": False\" sqlglot/ | head -20; grep -n \"def queryoption_sql\\|def xmlkeyvaluoption_sql\\|def options_modifier\" -A8 sqlglot/generator.py sqlglot/generators/tsql.py | head -40; grep -n \"class Query\\b\\|class Query(\" -A12 sqlglot/expressions/query.py | head -30; grep -n \"XML\" sqlglot/tokens*.py sqlglot/*.py | grep -i \"token\" | head", "description": "Trace for_ arg declaration and generator hooks"}
[tool_result] sqlglot/generator.py:3102:            self.for_modifiers(expression),
sqlglot/generator.py:3110:    def for_modifiers(self, expression: exp.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("fo
…[3817 chars elided]…
class Query(Selectable):
113-    """Trait for any SELECT/UNION/etc. query expression."""
114-
115-    @property
116-    def ctes(self) -> list[CTE]:
117-        with_ = self.args.get("with_")
118-        return with_.expressions if with_ else []
119-
120-    def select(
121-        self: Q,
122-        *expressions: ExpOrStr | None,
123-        append: bool = True,
124-        dialect: DialectType = None,
sqlglot/tokenizer_core.py:208:    XML = auto()
sqlglot/parser.py:563:        TokenType.XML,
[tool_use Bash] {"command": "sed -n 4105,4135p sqlglot/parser.py; echo ----; sed -n 1868,1880p sqlglot/expressions/query.py; grep -n \"def xmlkeyvaluoption\\|def xmlkeyvalueoption\" -A6 sqlglot/generators/tsql.py sqlglot/generator.py; grep -n \"def _match_text_seq\" -A3 sqlglot/parser.py | head; grep -n \"^from\\|^import\" sqlglot/parsers/tsql.py", "description": "Inspect modifier loop and generator XML key-value helpers"}
[tool_result]     def _parse_query_modifiers(self, this: None) -> None: ...

    def _parse_query_modifiers(self, this):
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for lateral in iter(self._parse_lateral, None):
                this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._c
…[1618 chars elided]…
_match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1950-        index = self._index
1951-        string_type = TokenType.STRING
1952-        for text in texts:
1:from __future__ import annotations
3:import datetime
4:import re
5:import typing as t
7:from sqlglot import exp, parser
8:from sqlglot.dialects.dialect import (
13:from sqlglot.helper import seq_get
14:from sqlglot.parser import build_coalesce
15:from sqlglot.time import format_time
16:from sqlglot.tokens import TokenType
[assistant] The FOR XML path is parsed into a `for_` list and dropped by other dialects because `queryoption_sql` returns an empty string. I'll mirror that for JSON with a separate `for_json` key so the generator can tell the two clauses apart.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = {\n    \"AUTO\": tuple(),\n    \"INCLUDE_NULL_VALUES\": tuple(),\n    \"WITHOUT_ARRAY_WRAPPER\": tuple(),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[612 chars elided]…
n    def _parse_for(self) -> tuple[str, list[exp.Expr] | None]:\n        if self._match_pair(TokenType.FOR, TokenType.XML):\n            return \"for_\", self._parse_csv(lambda: self._parse_for_option(XML_OPTIONS))\n\n        if self._match_text_seq(\"FOR\", \"JSON\"):\n            return \"for_json\", self._parse_csv(lambda: self._parse_for_option(JSON_OPTIONS))\n\n        return \"for_\", None"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"", "new_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_xml = self.expressions(expression, key=\"for_\")\n        if for_xml:\n            return f\"{self.sep()}FOR XML{self.seg(for_xml)}\"\n\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a quick check of the round-trip and cross-dialect behavior before writing the tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor s in ['SELECT * FROM t FOR JSON AUTO','SELECT * FROM t FOR JSON PATH, ROOT(\\'r\\'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER','SELECT * FROM t FOR JSON PATH, ROOT, INCLUDE_NULL_VALUES','SELECT * FROM t FOR XML PATH']:\n    print(sqlglot
…[237 chars elided]…
T * FROM t FOR JSON PATH, ROOT(\\'r\\')', read='tsql', write='duckdb', unsupported_level=ErrorLevel.WARN)[0]))\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES', read='tsql', pretty=True)[0])\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES', read='tsql', pretty=True)[0])\n\" 2>&1", "description": "Smoke-test FOR JSON parsing and generation"}
[tool_result] Unsupported query option.
Unsupported query option.
SELECT * FROM t FOR JSON AUTO
SELECT * FROM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
SELECT * FROM t FOR JSON PATH, ROOT, INCLUDE_NULL_VALUES
SELECT * FROM t FOR XML PATH

'SELECT * FROM t'
SELECT
  *
FROM t
FOR JSON
  AUTO,
  INCLUDE_NULL_VALUES
SELECT
  *
FROM t
FOR JSON
  AUTO,
  INCLUDE_NULL_VALUES
[assistant] Round-trip and dropping for other dialects both work. Next, the tests. I'll check how existing tests assert unsupported output so the new test matches.
[tool_use Bash] {"command": "grep -n \"UnsupportedError\" tests/dialects/test_tsql.py | head -5; grep -n \"^from\\|^import\" tests/dialects/test_tsql.py; grep -n \"def validate_all\" -A12 tests/dialects/test_dialect.py | grep -n \"unsupported\" ", "description": "Check unsupported-error test conventions"}
[tool_result] 2:from sqlglot.errors import ParseError, UnsupportedError
636:                "databricks": UnsupportedError,
2316:                "tsql": UnsupportedError,
2326:                "tsql": UnsupportedError,
1:from sqlglot import exp, parse_one
2:from sqlglot.errors import ParseError, UnsupportedError
3:from sqlglot.optimizer.annotate_types import annotate_types
4:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "sed -n 620,640p tests/dialects/test_tsql.py", "description": "View nearby validate_all unsupported test example"}
[tool_result]         raising_queries = [
            # Missing parentheses
            "SELECT * FROM Table1 OPTION HASH GROUP",
            # Must be followed by 'PLAN"
            "SELECT * FROM Table1 OPTION(KEEPFIXED)",
            # Missing commas
            "SELECT * FROM Table1 OPTION(HASH GROUP HASH GROUP)",
        ]
        for query in raising_queries:
            with self.assertRaises(ParseError, msg=f"When running '{query}'"):
                self.parse_one(query)

        self.validate_all(
            "SELECT col FROM t OPTION(LABEL = 'foo')",
            write={
                "tsql": "SELECT col FROM t OPTION(LABEL = 'foo')",
                "databricks": UnsupportedError,
            },
        )

    def test_for_xml(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "            pretty=True,\n        )\n\n    def test_for_json(self):\n        json_possible_options = [\n            \"AUTO\",\n
…[907 chars elided]…
N\n  PATH,\n  ROOT('RootName'),\n  INCLUDE_NULL_VALUES\"\"\",\n            pretty=True,\n        )\n\n        self.validate_all(\n            \"SELECT * FROM t FOR JSON PATH, ROOT('RootName')\",\n            write={\n                \"tsql\": \"SELECT * FROM t FOR JSON PATH, ROOT('RootName')\",\n                \"duckdb\": UnsupportedError,\n            },\n        )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] The duckdb case should drop the clause with a warning, not raise. I'll correct the assertion and run the test to confirm the helper's behavior.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "                \"tsql\": \"SELECT * FROM t FOR JSON PATH, ROOT('RootName')\",\n                \"duckdb\": UnsupportedError,\n            },", "new_string": "                \"tsql\": \"SELECT * FROM t FOR JSON PATH, ROOT('RootName')\",\n                \"duckdb\": \"SELECT * FROM t\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092545-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -30", "description": "Run T-SQL dialect tests"}
[tool_result] ....................... [ 42%]
...............................                                                                     [100%]
54 passed, 670 subtests passed in 0.29s
[assistant] T-SQL tests pass. Now the full suite using the project's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -m ruff check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py 2>&1 | tail -3", "description": "Run full test suite and lint/format checks"}
[tool_result] ....................................................................................... [ 43%]
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
....................................................................................................................................................... [ 67%]
................................................ [ 71%]
............................................................ [ 76%]
............................................. [ 81%]
.................................................... [ 85%]
................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1108 passed, 18032 subtests passed in 52.58s
All checks passed!
3 files already formatted
[assistant] Full suite passes (1108 tests) and ruff is clean. I'll run a type check on the changed modules since the parser return type changed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 300 $PY -m mypy sqlglot/parsers/tsql.py sqlglot/generator.py 2>&1 | tail -5; git diff --stat", "description": "Type-check changed modules and show diff stat"}
[tool_result] (eval):1: command not found: timeout
 sqlglot/generator.py        |  8 ++++++--
 sqlglot/parsers/tsql.py     | 33 +++++++++++++++++++++------------
 tests/dialects/test_tsql.py | 40 ++++++++++++++++++++++++++++++++++++++++
 3 files changed, 67 insertions(+), 14 deletions(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parsers/tsql.py sqlglot/generator.py 2>&1 | tail -5", "description": "Run mypy on changed modules"}
[tool_result] Success: no issues found in 2 source files
[assistant] T-SQL now parses and round-trips `FOR JSON { AUTO | PATH } [, ROOT [('name')]] [, INCLUDE_NULL_VALUES] [, WITHOUT_ARRAY_WRAPPER]`. Other dialects drop the clause and emit the unsupported-option warning, the same as `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

The changes:

- **`sqlglot/parsers/tsql.py`**: added a `JSON_OPTIONS` table for `AUTO`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. `_parse_for` now returns the key along with the options. `FOR XML` still goes to `for_`, and `FOR JSON` goes to a new 
…[262 chars elided]…
dialects render each option as empty, so the clause disappears.
- **`tests/dialects/test_tsql.py`**: added `test_for_json`, which covers the option combinations and a pretty-printed case, plus a check that duckdb drops the clause.

Decision for you: I used a separate `for_json` key rather than one shared `for_` list. The shared list would need a marker to tell XML and JSON apart, since `AUTO` and `PATH` are valid in both. The separate key avoids that, but it means a Select can now carry two `FOR` clauses in the AST. Parsing a query with both a `FOR XML` and a `FOR JSON` clause is not rejected.
