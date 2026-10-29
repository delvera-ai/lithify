# trajectory base-1

final message:
T-SQL now parses and round-trips `FOR JSON`, and other dialects drop the clause with an unsupported warning. The full suite passes (1108 tests), and ruff and mypy are clean on the changed modules.

**What changed**
- **Parser (`sqlglot/parsers/tsql.py`):** `_parse_for` now recognises `FOR JSON` alongside `FOR XML`. Options are parsed by the same helpers XML uses, so `ROOT` works with or without `('name')`. A new `JSON_OPTIONS` table covers `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`.
- **AST:** `FOR JSON` is stored under a separate `for_json` key on `Select`, not in `for_`. That keeps the `FOR XML` prefix from being printed for JSON clauses.
- **Generator (`sqlglot/generator.py`):** the base generator warns "Unsupported FOR JSON clause." and emits nothing for `for_json`.
- **T-SQL generator (`sqlglot/generators/tsql.py`):** emits `FOR JSON` plus its options.
- **Tests (`tests/dialects/test_tsql.py`):** added `test_for_json`, which covers identity round-trips, pretty-printing, and an `UnsupportedError` check for DuckDB. I did not modify any existing test.

**Choices to confirm**
- I kept the warning as the base generator's `unsupported` call, so it respects `unsupported_level`. In `validate_all` it raises, as the existing `OPTION(LABEL…)` test does.
- The base generator emits one warning per `FOR JSON` clause, not one per option. `FOR XML` in other dialects warns once per option, so the two now differ slightly.

## events
[tool_use Bash] {"command": "rtk grep -rn \"FOR XML\\|for_xml\\|ForXml\\|FOR JSON\\|ForJson\\|for_json\\|JSON_OPTIONS\\|WITHOUT_ARRAY\" sqlglot/ tests/ | head -80", "description": "Search for FOR XML and FOR JSON references"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"FOR XML\\|ForXml\\|FOR JSON\\|ForJson\\|for_xml\\|XML_OPTIONS\\|WITHOUT_ARRAY\\|OPTIONS.*XML\" sqlglot/ tests/ | head -80", "description": "Search for FOR XML and FOR JSON references"}
[tool_result] sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:93:XML_OPTIONS: parser.OPTIONS_TYPE = {
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:511:                    this=self._parse_var_from_options(XML_OPTIONS, raise_unmatched=False)
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
tests/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
[tool_use Bash] {"command": "sed -n 80,120p sqlglot/parsers/tsql.py && echo ---- && sed -n 495,520p sqlglot/parsers/tsql.py && echo ---- && sed -n 3085,3115p sqlglot/generator.py && echo ---- && sed -n 635,720p tests/dialects/test_tsql.py && echo ---- && grep -n \"for_xml\\|ForXml\" -r sqlglot/ | head; grep -n \"class Query\\|class Select\" -A3 sqlglot/expressions/*.py | head -20", "description": "Read FOR XML parsing, generation, and tests"}
[tool_result]     "HASH": ("GROUP", "JOIN", "UNION"),
    "KEEP": ("PLAN",),
    "KEEPFIXED": ("PLAN",),
    "LOOP": ("JOIN",),
    "MERGE": ("JOIN", "UNION"),
    "OPTIMIZE": (("FOR", "UNKNOWN"),),
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
        
…[7365 chars elided]…
:112:class Query(Selectable):
sqlglot/expressions/query.py-113-    """Trait for any SELECT/UNION/etc. query expression."""
sqlglot/expressions/query.py-114-
sqlglot/expressions/query.py-115-    @property
--
sqlglot/expressions/query.py:438:class QueryBand(Expression):
sqlglot/expressions/query.py-439-    arg_types = {"this": True, "scope": False, "update": False}
sqlglot/expressions/query.py-440-
sqlglot/expressions/query.py-441-
--
sqlglot/expressions/query.py:914:class QueryOption(Expression):
[tool_use Bash] {"command": "grep -rn \"_parse_for\\b\\|\\\"for_\\\"\\|for_=\\|\\bfor_\\b\" sqlglot/ | head -30; echo ----; sed -n 3115,3125p sqlglot/generator.py; echo ----; grep -n \"XMLKeyValueOption\" -A12 sqlglot/expressions/*.py | head -30; grep -n \"def _parse_var_from_options\" -A30 sqlglot/parser.py | head -45; grep -rn \"XML_OPTIONS\\|OPTIONS_TYPE\" sqlglot/ | head; grep -n \"class Select(\" -A40 sqlglot/expressions/query.py | grep -n \"for_\\|options\"", "description": "Inspect FOR parsing hooks and option helpers"}
[tool_result] sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/parsers/tsql.py:504:    def _parse_for(self) -> list[exp.Expr] | None:
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_":
…[2634 chars elided]…
ENCE: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1621:    ISOLATED_LOADING_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {"FOR": ("ALL", "INSERT", "NONE")}
sqlglot/parser.py:1623:    USABLES: t.ClassVar[OPTIONS_TYPE] = dict.fromkeys(
sqlglot/parser.py:1627:    CAST_ACTIONS: t.ClassVar[OPTIONS_TYPE] = dict.fromkeys(("RENAME", "ADD"), ("FIELDS",))
sqlglot/parser.py:1629:    SCHEMA_BINDING_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
35:1157-            opts: other options to use to parse the input expressions.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('SELECT * FROM t FOR XML PATH', read='tsql')))\nfor d in ['duckdb','mysql','spark']:\n    print(d, sqlglot.transpile('SELECT * FROM t FOR XML PATH', read='tsql', write=d))\nprint(sqlglot.transpile('SELECT * FROM t FOR XML PATH', read='tsql', write='duckdb', unsupported_level=sqlglot.ErrorLevel.RAISE) if False else '')\n\" ; grep -rn \"for_\" tests/ | head; git log --oneline -3 -- sqlglot/parsers/tsql.py", "description": "Check current FOR XML behavior across dialects"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
Select(
  expressions=[
    Star()],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  for_=[
    QueryOption(
      this=XMLKeyValueOption(
        this=Var(this=PATH)))])
duckdb ['SELECT * FROM t']
mysql ['SELECT * FROM t']
spark ['SELECT * FROM t']

tests/dialects/test_bigquery.py:2251:            for_in_stmts = parse(
tests/dialects/test_bigquery.py:2256:                [s.sql(dialect="
…[447 chars elided]…
_wide_part = 0, min_bytes_for_wide_part = 0;
tests/dialects/test_clickhouse.py:1218:                "clickhouse": """CREATE TABLE table_for_recompression (
tests/dialects/test_clickhouse.py:1230:  min_rows_for_wide_part = 0,
tests/dialects/test_clickhouse.py:1231:  min_bytes_for_wide_part = 0""",
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
f7bb6bea8 chore: use collections.abc and built-in types for typing to avoid deprecation (#7329)
ea76ca554 Chore: unpin ruff (#7287)
[tool_use Bash] {"command": "sed -n 310,330p sqlglot/parsers/tsql.py; echo ----; grep -n \"QUERY_MODIFIER_PARSERS\" -A3 sqlglot/parser.py | head -30; grep -n \"def _parse_query_modifiers\" -A45 sqlglot/parser.py | grep -n \"parser\\|key\\|expression\" ; echo ----; grep -n \"def queryoption_sql\\|def xmlkeyvalueoption_sql\\|def xmlkeyvalue\" -A6 sqlglot/generator.py; echo ----; grep -n \"class Select(\" -A30 sqlglot/expressions/query.py | grep -n \"for_\\|arg_types\" ; grep -n \"for_modifiers\\|options_modifier\" -r sqlglot/ | head; grep -n \"def _match_text_seq\" -A3 sqlglot/parser.py", "description": "Inspect query modifier dispatch and generator hooks"}
[tool_result]     STRING_ALIASES = True
    NO_PAREN_IF_COMMANDS = False

    NO_PAREN_FUNCTIONS = {
        **parser.Parser.NO_PAREN_FUNCTIONS,
        TokenType.SESSION_USER: exp.SessionUser,
    }

    QUERY_MODIFIER_PARSERS = {
        **parser.Parser.QUERY_MODIFIER_PARSERS,
        TokenType.OPTION: lambda self: ("options", self._parse_options()),
        TokenType.FOR: lambda self: ("for_", self._parse_for()),
    }

    # T-SQL does not allow BEGIN to be used as an identifier
    ID_VAR_TOKENS = parser
…[3021 chars elided]…
p.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generators/tsql.py:574:    def options_modifier(self, expression: exp.Expr) -> str:
1949:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1950-        index = self._index
1951-        string_type = TokenType.STRING
1952-        for text in texts:
[tool_use Bash] {"command": "grep -n \"queryoption\\|QueryOption\\|xmlkeyvalue\" sqlglot/generators/tsql.py; sed -n 570,585p sqlglot/generators/tsql.py; echo ----; sed -n 1120,1130p sqlglot/expressions/query.py; grep -n \"for_\\\"\" -B2 -A2 sqlglot/expressions/query.py; grep -n \"\\\"for_\\\"\\|for_:\" sqlglot/expressions/*.py; sed -n 4119,4150p sqlglot/parser.py", "description": "Check tsql generator overrides and Select args"}
[tool_result] 288:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
        if expression.args["kind"] == "VIEW":
            expression.this.set("catalog", None)
        return super().drop_sql(expression)

    def options_modifier(self, expression: exp.Expr) -> str:
        options = self.expressions(expression, key="options")
        return f" OPTION{self.wrap(options)}" if options else ""

    def dpipe_sql(self, expression: exp.DPipe) -> str:
        return self.sql(reduce(lambda x, y: e
…[1568 chars elided]…
                       expression.set("expressions", None)
                                offset.set("expressions", limit_by_expressions)
                        continue
                break

        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
            this = self._implicit_unnests_to_explicit(this)

        return this

    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
        start = self._curr
        while self._curr:
            self._advance()
[tool_use Bash] {"command": "sed -n 284,296p sqlglot/generators/tsql.py; grep -n \"def select_sql\" sqlglot/generator.py; grep -n \"for_modifiers\\|for_json\" sqlglot/generators/*.py", "description": "View tsql queryoption_sql override"}
[tool_result]     def convert_sql(self, expression: exp.Convert) -> str:
        name = "TRY_CONVERT" if expression.args.get("safe") else "CONVERT"
        return self.func(name, expression.this, expression.expression, expression.args.get("style"))

    def queryoption_sql(self, expression: exp.QueryOption) -> str:
        option = self.sql(expression, "this")
        value = self.sql(expression, "expression")
        if value:
            optional_equal_sign = "= " if option in OPTIONS_THAT_REQUIRE_EQUAL else ""
            return f"{option} {optional_equal_sign}{value}"
        return option

    def lateral_op(self, expression: exp.Lateral) -> str:
3131:    def select_sql(self, expression: exp.Select) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "OPTIONS_THAT_REQUIRE_EQUAL = (\"MAX_GRANT_PERCENT\", \"MIN_GRANT_PERCENT\", \"LABEL\")", "new_string": "JSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(\n    (\n        \"AUTO\",\n        \"INCLUDE_NULL_VALUES\",\n        \"PATH\",\n        \"WITHOUT_ARRAY_WRAPPER\",\n    ),\n    tuple(),\n)\n\n\nOPTIONS_THAT_REQUIRE_EQUAL = (\"MAX_GRANT_PERCENT\", \"MIN_GRANT_PERCENT\", \"LABEL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[599 chars elided]…
n            return \"for_\", None\n\n        def _parse_for_option() -> exp.Expr | None:\n            return self.expression(\n                exp.QueryOption(\n                    this=self._parse_var_from_options(options, raise_unmatched=False)\n                    or self._parse_xml_key_value_option()\n                )\n            )\n\n        return key, self._parse_csv(_parse_for_option)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "            self.for_modifiers(expression),\n            sep=\"\",\n        )", "new_string": "            self.for_modifiers(expression),\n            self.for_json_modifiers(expression),\n            sep=\"\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"\n", "new_string": "        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"\n\n    def for_json_modifiers(self, expression: exp.Expr) -> str:\n        if expression.args.get(\"for_json\"):\n            self.unsupported(\"Unsupported FOR JSON clause.\")\n        return \"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py", "old_string": "    def options_modifier(self, expression: exp.Expr) -> str:\n        options = self.expressions(expression, key=\"options\")\n        return f\" OPTION{self.wrap(options)}\" if options else \"\"\n", "new_strin
…[23 chars elided]…
difier(self, expression: exp.Expr) -> str:\n        options = self.expressions(expression, key=\"options\")\n        return f\" OPTION{self.wrap(options)}\" if options else \"\"\n\n    def for_json_modifiers(self, expression: exp.Select) -> str:\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py", "old_string": "    def for_json_modifiers(self, expression: exp.Select) -> str:", "new_string": "    def for_json_modifiers(self, expression: exp.Expr) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py has been updated successfully.
[assistant] Now the tests. I'll add a FOR JSON test next to the FOR XML one, then run the T-SQL suite to see where it stands.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_for_json(self):\n      
…[853 chars elided]…
H,\n  ROOT('RootName'),\n  WITHOUT_ARRAY_WRAPPER\"\"\",\n            pretty=True,\n        )\n\n        self.validate_all(\n            \"SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES\",\n            write={\n                \"tsql\": \"SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES\",\n                \"duckdb\": UnsupportedError,\n            },\n        )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105940-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py -k \"for_\" 2>&1 | tail -30; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON PATH, ROOT(\\'r\\')', read='tsql', write='duckdb'))\nprint(sqlglo
…[36 chars elided]…
N AUTO', read='tsql', write='mysql'))\nprint(sqlglot.transpile('SELECT a FROM t FOR JSON PATH, INCLUDE_NULL_VALUES', read='tsql', write='tsql'))\nprint(sqlglot.transpile('SELECT a FROM t FOR XML PATH', read='tsql', write='tsql'))\nprint(sqlglot.transpile('SELECT a FROM t FOR JSON PATH', read='tsql', write='tsql', pretty=True))\n\"", "description": "Run FOR JSON tests and spot-check transpilation"}
[tool_result] ..       [100%]
2 passed, 52 deselected, 64 subtests passed in 0.24s
Unsupported FOR JSON clause.
Unsupported FOR JSON clause.
['SELECT * FROM t']
['SELECT * FROM t']
['SELECT a FROM t FOR JSON PATH, INCLUDE_NULL_VALUES']
['SELECT a FROM t FOR XML PATH']
['SELECT\n  a\nFROM t\nFOR JSON\n  PATH']
[assistant] Parsing, round-trip, and cross-dialect dropping all behave as specified. Now the full suite and lint.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (<work>/env-sqlglot/bin/ruff check sqlglot tests/dialects/test_tsql.py && <work>/env-sqlglot/bin/ruff format --check sqlglot tests/dialects/test_tsql.py) 2>&1 | tail -5", "description": "Run full test suite and ruff checks"}
[tool_result] ....................................................................................... [ 43%]
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
.......................................................................................................................................................... [ 67%]
............................................... [ 71%]
.......................................................................................................... [ 81%]
....................... [ 83%]
............. [ 84%]
................................................................................................................................. [ 96%]
.......................... [ 98%]
................                [100%]
1108 passed, 18029 subtests passed in 59.99s
All checks passed!
176 files already formatted
[tool_use Bash] {"command": "timeout 300 <work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/tsql.py sqlglot/generators/tsql.py sqlglot/generator.py 2>&1 | tail -5; git status --short", "description": "Type-check changed modules and show status"}
[tool_result] (eval):1: command not found: timeout
 M sqlglot/generator.py
 M sqlglot/generators/tsql.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.py
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/tsql.py sqlglot/generators/tsql.py sqlglot/generator.py 2>&1 | tail -5", "description": "Type-check changed modules"}
[tool_result] Success: no issues found in 3 source files
[assistant] T-SQL now parses and round-trips `FOR JSON`, and other dialects drop the clause with an unsupported warning. The full suite passes (1108 tests), and ruff and mypy are clean on the changed modules.

**What changed**
- **Parser (`sqlglot/parsers/tsql.py`):** `_parse_for` now recognises `FOR JSON` alongside `FOR XML`. Options are parsed by the same helpers XML uses, so `ROOT` works with or without `('name')`. A new `JSON_OPTIONS` table covers `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`.
- **AST:** `FOR JSON` is stored under a separate `for_json` key on `Select`, not in `for_
…[255 chars elided]…
** emits `FOR JSON` plus its options.
- **Tests (`tests/dialects/test_tsql.py`):** added `test_for_json`, which covers identity round-trips, pretty-printing, and an `UnsupportedError` check for DuckDB. I did not modify any existing test.

**Choices to confirm**
- I kept the warning as the base generator's `unsupported` call, so it respects `unsupported_level`. In `validate_all` it raises, as the existing `OPTION(LABEL…)` test does.
- The base generator emits one warning per `FOR JSON` clause, not one per option. `FOR XML` in other dialects warns once per option, so the two now differ slightly.
