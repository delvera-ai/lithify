# trajectory base-1

final message:
`FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the same "Unsupported query option." warning that `FOR XML` gets. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I didn't commit.

Changes:

- **Parser (`sqlglot/parsers/tsql.py`)**: `_parse_for` now recognises `FOR JSON` alongside `FOR XML`. Options are `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`, plus `ROOT` with or without a `('name')`. Parsing reuses the existing XML key/value path for `ROOT`.
- **Generator (`sqlglot/generator.py`)**: `for_modifiers` emits `FOR JSON` when the new `for_json` arg is set. The `FOR XML` output is unchanged.
- **Tests (`tests/dialects/test_tsql.py`)**: new `test_for_json` covers the option combinations as identity round-trips, a pretty-printed case, and a DuckDB check that the clause is dropped.

Decisions to review:

- **Separate `for_json` arg, not `for_`**: I kept the `for_` key for `FOR XML` so its AST doesn't change, and stored `FOR JSON` items under `for_json`. The alternative was a shared key with a marker, which would have changed the XML shape.
- **Option order isn't enforced**: like the XML parser, it accepts the options in any order and doesn't require `AUTO` or `PATH` first.
- **Both clauses in one query aren't rejected**: a query with both `FOR XML` and `FOR JSON` parses without error, since they use different keys. T-SQL doesn't allow that, but I didn't add a check.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|for xml\" sqlglot/ | head -60", "description": "Locate existing FOR XML support"}
[tool_result] sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
[tool_use Bash] {"command": "sed -n 480,530p sqlglot/parsers/tsql.py && echo ---- && sed -n 3060,3120p sqlglot/generator.py && echo ---- && grep -rn \"for_xml\\|FOR XML\\|ForXml\" tests/ sqlglot/ | grep -v \"^sqlglot/parsers/tsql.py:5[01]\" | head -40", "description": "Read FOR XML parser and generator code"}
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
…[4023 chars elided]…
ef test_for_xml(self):
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
[tool_use Bash] {"command": "grep -n \"XML_OPTIONS\\|XML_KEY\\|XMLKeyValueOption\\|xmlkeyvalueoption\" -r sqlglot/ | head; grep -n \"XML_OPTIONS\" -A25 sqlglot/parsers/tsql.py | head -50; sed -n 636,720p tests/dialects/test_tsql.py; grep -n \"class XMLKeyValueOption\" -A5 sqlglot/expressions/*.py sqlglot/*.py", "description": "Inspect XML option definitions and tests"}
[tool_result] sqlglot/generator.py:5674:    def xmlkeyvalueoption_sql(self, expression: exp.XMLKeyValueOption) -> str:
sqlglot/parsers/tsql.py:93:XML_OPTIONS: parser.OPTIONS_TYPE = {
sqlglot/parsers/tsql.py:495:    def _parse_xml_key_value_option(self) -> exp.XMLKeyValueOption:
sqlglot/parsers/tsql.py:502:        return exp.XMLKeyValueOption(this=this, expression=expression)
sqlglot/parsers/tsql.py:511:                    this=self._parse_var_from_options(XML_OPTIONS, raise_unmatched=False)
sqlglot/expression
…[5337 chars elided]…

        self.validate_identity("CAST(x AS IMAGE)")
        self.validate_identity("CAST(x AS SQL_VARIANT)")
        self.validate_identity("CAST(x AS BIT)")
sqlglot/expressions/query.py:2077:class XMLKeyValueOption(Expression):
sqlglot/expressions/query.py-2078-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/query.py-2079-
sqlglot/expressions/query.py-2080-
sqlglot/expressions/query.py-2081-class Semicolon(Expression):
sqlglot/expressions/query.py-2082-    arg_types = {}
[tool_use Bash] {"command": "grep -rn '\"for_\"\\|for_modifiers\\|_parse_for\\b\\|self._parse_for()\\|\"for_\"' sqlglot/ | head -30; grep -n \"def _parse_var_from_options\" -A40 sqlglot/parser.py | head -60; grep -n \"class QueryOption\" -B2 -A5 sqlglot/expressions/query.py; grep -n \"XML\\|JSON\" sqlglot/tokens.py sqlglot/tokenizer_core.py 2>/dev/null | head -20", "description": "Trace for_ arg through parser and generator"}
[tool_result] sqlglot/generator.py:3102:            self.for_modifiers(expression),
sqlglot/generator.py:3110:    def for_modifiers(self, expression: exp.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("fo
…[1751 chars elided]…
arg_types = {"this": True, "expression": False}
916-
917-
918-class WithTableHint(Expression):
919-    arg_types = {"expressions": True}
sqlglot/tokens.py:462:        "JSON": TokenType.JSON,
sqlglot/tokens.py:463:        "JSONB": TokenType.JSONB,
sqlglot/tokens.py:545:    # In tokenizers like JSONPath, dots are always key separators, never decimal points
sqlglot/tokenizer_core.py:158:    JSON = auto()
sqlglot/tokenizer_core.py:159:    JSONB = auto()
sqlglot/tokenizer_core.py:208:    XML = auto()
[tool_use Bash] {"command": "sed -n 300,330p sqlglot/parsers/tsql.py; grep -n \"for_\" sqlglot/expressions/query.py | head; sed -n 5535,5560p sqlglot/generator.py; grep -n \"FOR\\b\" sqlglot/parser.py | head; grep -n \"XML_OPTIONS\\|OPTIONS_TYPE\" sqlglot/parsers/*.py sqlglot/*.py | head; grep -rn \"QueryOption\\|queryoption\" sqlglot/ --include=*.py | grep -v \"^sqlglot/parsers/tsql.py\" | head; grep -n \"def unsupported\\b\" -A12 sqlglot/generator.py | head -20", "description": "Check FOR keyword dispatch and option handling"}
[tool_result]     if this and this.is_string:
        this = exp.cast(this, exp.DType.DATETIME2)

    return exp.TimestampTrunc(this=this, unit=unit)


class TSQLParser(parser.Parser):
    SET_REQUIRES_ASSIGNMENT_DELIMITER = False
    LOG_DEFAULTS_TO_LN = True
    STRING_ALIASES = True
    NO_PAREN_IF_COMMANDS = False

    NO_PAREN_FUNCTIONS = {
        **parser.Parser.NO_PAREN_FUNCTIONS,
        TokenType.SESSION_USER: exp.SessionUser,
    }

    QUERY_MODIFIER_PARSERS = {
        **parser.Parser.QUERY_MODIF
…[3254 chars elided]…
 self.unsupported_level == ErrorLevel.IMMEDIATE:
973-            raise UnsupportedError(message)
974-        self.unsupported_messages.append(message)
975-
976-    def sep(self, sep: str = " ") -> str:
977-        return f"{sep.strip()}\n" if self.pretty else sep
978-
979-    def seg(self, sql: str, sep: str = " ") -> str:
980-        return f"{self.sep(sep)}{sql}"
981-
982-    def sanitize_comment(self, comment: str) -> str:
983-        comment = " " + comment if comment[0].strip() else comment
[tool_use Bash] {"command": "grep -rn \"for_\" sqlglot/expressions/ | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM t FOR XML PATH, ROOT(\\'r\\')', read='tsql')\nprint(repr(e.args.get('for_')))\nprint(e.sql('tsql'))\nprint(e.sql('duckdb'))\nprint(sqlglot.parse_one('SELECT * FROM t FOR XML PATH, ROOT', read='tsql').sql('tsql'))\n\"", "description": "Probe current FOR XML parse and generation"}
[tool_result] sqlglot/expressions/properties.py:266:        "for_or_in": False,
sqlglot/expressions/ddl.py:87:        "for_each": False,
sqlglot/expressions/ddl.py:215:        "for_table": False,
sqlglot/expressions/ddl.py:216:        "for_group": False,
sqlglot/expressions/ddl.py:217:        "for_user": False,
sqlglot/expressions/ddl.py:218:        "for_role": False,
sqlglot/expressions/query.py:1106:    https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#for_system_time_as_of
sqlglot/
…[5 chars elided]…
ssions/core.py:1903:        "returns_list_for_maps": False,
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
Unsupported query option.
Unsupported query option.
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH))), QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=ROOT),
    expression=Literal(this='r', is_string=True)))]
SELECT * FROM t FOR XML PATH, ROOT('r')
SELECT * FROM t
SELECT * FROM t FOR XML PATH, ROOT
[tool_use Bash] {"command": "grep -n \"QUERY_MODIFIER_PARSERS\" -A3 sqlglot/parser.py | head -30; grep -n \"def _parse_query_modifiers\" -A40 sqlglot/parser.py | grep -n \"parser\\|key\\|value\" ; sed -n 5670,5680p sqlglot/generator.py; grep -n \"def expressions\" -A30 sqlglot/generator.py | grep -n \"if\\|sql\" | head; grep -n \"XML_OPTIONS\\|for_\" tests/*.py | head", "description": "Inspect query modifier dispatch and helpers"}
[tool_result] 1521:    QUERY_MODIFIER_PARSERS: t.ClassVar = {
1522-        TokenType.MATCH_RECOGNIZE: lambda self: ("match", self._parse_match_recognize()),
1523-        TokenType.PREWHERE: lambda self: ("prewhere", self._parse_prewhere()),
1524-        TokenType.WHERE: lambda self: ("where", self._parse_where()),
--
1549:    QUERY_MODIFIER_TOKENS: t.ClassVar = set(QUERY_MODIFIER_PARSERS)
1550-
1551-    SET_PARSERS: t.ClassVar = {
1552-        "GLOBAL": lambda self: self._parse_set_item_assignment("GLOBAL"),

…[1261 chars elided]…
470-        expressions = expression.args.get(key or "expressions") if expression else sqls
17:4472-        if not expressions:
20:4475-        if flat:
21:4476-            return sep.join(sql for sql in (self.sql(e) for e in expressions) if sql)
23:4478-        num_sqls = len(expressions)
24:4479-        result_sqls = []
27:4482-            sql = self.sql(e, comment=False)
28:4483-            if not sql:
31:4486-            comments = self.maybe_comment("", e) if isinstance(e, exp.Expr) else ""
[tool_use Bash] {"command": "sed -n 4112,4140p sqlglot/parser.py; grep -rn \"Unsupported query option\\|unsupported_level=ErrorLevel.WARN\" tests/ | head -5; grep -n \"^from\\|^import\" sqlglot/parsers/tsql.py | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT * FROM t FOR XML PATH', read='tsql')\nprint(e.args.get('for_'))\" ", "description": "Check modifier loop and imports"}
[tool_result]                 this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
                    key, expression = parser(self)

                    if expression:
                        if this.args.get(key):
                            self.raise_error(
                                f"
…[705 chars elided]…
     offset.set("expressions", limit_by_expressions)
                        continue
                break
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
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH)))]
[assistant] Parser and generator both hard-code the FOR XML path, so I'll add a parallel `for_json` arg, reusing the same `QueryOption` items that XML already uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182723-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[900 chars elided]…
          return \"for_\", None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return self.expression(\n                exp.QueryOption(\n                    this=self._parse_var_from_options(XML_OPTIONS, raise_unmatched=False)\n                    or self._parse_xml_key_value_option()\n                )\n            )\n\n        return \"for_\", self._parse_csv(_parse_for_xml)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182723-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/tsql.py'\ns=open(p).read()\ns=s.replace('''        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),''','''        TokenType.FOR: lambda self: self._parse_for(),''',1)\ns=s.replace('''OPTIONS_THAT_REQUIRE_EQUAL = (''','''JSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(\n    (\"AUTO\", \"PATH\", \"INCLUDE_NULL_VALUES\", \"WITH
…[493 chars elided]…
key=\"for_\")\n        if for_xml:\n            return f\"{self.sep()}FOR XML{self.seg(for_xml)}\"\n\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\"\n'''\nassert old in s\ns=s.replace(old,new,1)\nopen(p,'w').write(s)\nEOF\ngit diff --stat", "description": "Wire JSON options and generator branch"}
[tool_result]  sqlglot/generator.py    |  8 ++++++--
 sqlglot/parsers/tsql.py | 26 ++++++++++++++++++++++----
 2 files changed, 28 insertions(+), 6 deletions(-)
[tool_use Bash] {"command": "git diff sqlglot/parsers/tsql.py", "description": "Review parser diff"}
[tool_result] diff --git a/sqlglot/parsers/tsql.py b/sqlglot/parsers/tsql.py
index 1fb6146a1..4f7311eea 100644
--- a/sqlglot/parsers/tsql.py
+++ b/sqlglot/parsers/tsql.py
@@ -107,6 +107,12 @@ XML_OPTIONS: parser.OPTIONS_TYPE = {
 }
 
 
+JSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(
+    ("AUTO", "PATH", "INCLUDE_NULL_VALUES", "WITHOUT_ARRAY_WRAPPER"),
+    tuple(),
+)
+
+
 OPTIONS_THAT_REQUIRE_EQUAL = ("MAX_GRANT_PERCENT", "MIN_GRANT_PERCENT", "LABEL")
 
 
@@ -318,7 +324,7 @@ class TSQLParser(parser.Pars
…[1017 chars elided]…
urn "for_json", self._parse_csv(_parse_for_json)
+
         if not self._match_pair(TokenType.FOR, TokenType.XML):
-            return None
+            return "for_", None
 
         def _parse_for_xml() -> exp.Expr | None:
             return self.expression(
@@ -513,7 +531,7 @@ class TSQLParser(parser.Parser):
                 )
             )
 
-        return self._parse_csv(_parse_for_xml)
+        return "for_", self._parse_csv(_parse_for_xml)
 
     def _parse_projections(
         self,
[assistant] Diff looks right. Now a probe across T-SQL and another dialect before adding tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nqs=['SELECT * FROM t FOR JSON AUTO','SELECT * FROM t FOR JSON PATH','SELECT * FROM t FOR JSON AUTO, ROOT',\\\"SELECT * FROM t FOR JSON PATH, ROOT('r')\\\",'SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES','SELECT * FROM t FOR JSON PATH, WIT
…[235 chars elided]…
sql('tsql'))\nprint(sqlglot.parse_one(qs[3],read='tsql').sql('tsql',pretty=True))\nprint(repr(sqlglot.transpile(qs[3],read='tsql',write='duckdb',unsupported_level=ErrorLevel.WARN)))\nimport logging\nprint(sqlglot.transpile(qs[6],read='tsql',write='duckdb'))\nprint(sqlglot.parse_one('SELECT * FROM t FOR XML PATH', read='tsql').sql('tsql'))\n\"", "description": "Probe FOR JSON parse and round-trip"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
SELECT * FROM t FOR JSON AUTO
SELECT * FROM t FOR JSON PATH
SELECT * FROM t FOR JSON AUTO, ROOT
SELECT * FROM t FOR JSON PATH, ROOT('r')
SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES
SELECT * FROM t FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
SELECT * FROM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
SELECT a AS x FROM t WHERE a > 1 ORDER BY a FOR JSON AUTO
SELECT
  *
FROM t
FOR JSON
  PATH,
  ROOT('r')
['SELECT * FROM t']
['SELECT * FROM t']
SELECT * FROM t FOR XML PATH
[assistant] Round-trips work and other dialects drop the clause with the existing warning. Adding tests next to `test_for_xml`.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_tsql.py'\ns=open(p).read()\nanchor='''    def test_types(self):\n        self.validate_identity(\"CAST(x AS XML)\")'''\nnew='''    def test_for_json(self):\n        json_possible_options = [\n            \"AUTO\",\n            \"AUTO, INCLUDE_NULL_VALUES\",\n            \"AUTO, WITHOUT_ARRAY_WRAPPER\",\n            \"AUTO, ROOT\",\n           
…[1025 chars elided]…
tName')\",\n            write={\"duckdb\": \"SELECT * FROM t\"},\n        )\n\n'''\nassert s.count(anchor)==1\ns=s.replace(anchor,new+anchor,1)\nopen(p,'w').write(s)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -15", "description": "Add FOR JSON tests and run T-SQL tests"}
[tool_result] ....................... [ 42%]
...............................                                                                     [100%]
54 passed, 670 subtests passed in 0.28s
[assistant] T-SQL tests pass. Running the full suite and the linter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; (ruff --version && ruff check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py && ruff format --check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py) 2>&1 | tail -5", "description": "Run full test suite and lint checks"}
[tool_result] ................................................ [ 71%]
............................................................ [ 76%]
............................................. [ 81%]
.................................................... [ 85%]
................................................................................................................. [ 95%]
.......................... [ 98%]
...................             [100%]
1108 passed, 18032 subtests passed in 49.35s
ruff 0.15.6
All checks passed!
3 files already formatted
[assistant] Full suite passes (1108 tests) and ruff is clean. Checking types since `_parse_for`'s return type changed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parsers/tsql.py sqlglot/generator.py 2>&1 | tail -5; git status --short", "description": "Type-check changed modules"}
[tool_result] Success: no issues found in 2 source files
 M sqlglot/generator.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.py
[assistant] `FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the same "Unsupported query option." warning that `FOR XML` gets. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I didn't commit.

Changes:

- **Parser (`sqlglot/parsers/tsql.py`)**: `_parse_for` now recognises `FOR JSON` alongside `FOR XML`. Options are `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`, plus `ROOT` with or without a `('name')`. Parsing reuses the existing XML key/value path for `ROOT`.
- **Generator (`sqlglot/generator.py`)**: `for_modifiers` 
…[274 chars elided]…
ped.

Decisions to review:

- **Separate `for_json` arg, not `for_`**: I kept the `for_` key for `FOR XML` so its AST doesn't change, and stored `FOR JSON` items under `for_json`. The alternative was a shared key with a marker, which would have changed the XML shape.
- **Option order isn't enforced**: like the XML parser, it accepts the options in any order and doesn't require `AUTO` or `PATH` first.
- **Both clauses in one query aren't rejected**: a query with both `FOR XML` and `FOR JSON` parses without error, since they use different keys. T-SQL doesn't allow that, but I didn't add a check.
