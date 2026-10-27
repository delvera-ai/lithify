# trajectory base-1

final message:
`FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the same "Unsupported query option." warning they use for `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

The changes:

- **Parser** (`sqlglot/parsers/tsql.py`): `FOR JSON` is parsed into a new `for_json` arg, separate from `for_`, using a `JSON_OPTIONS` set (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `ROOT('name')` goes through the same key-value path `FOR XML` uses for `ROOT`.
- **Generator** (`sqlglot/generator.py`): `for_modifiers` emits `FOR XML` and `FOR JSON` from their own args. Other dialects reach the existing `queryoption_sql` warning and drop the clause, so no per-dialect change was needed.
- **Tests** (`tests/dialects/test_tsql.py`): a new `test_for_json` covers the option combinations as identity round-trips, a pretty-printed case, and an `UnsupportedError` check for DuckDB.

Because `ROOT` reuses the loose XML parsing, `ROOT` accepts any trailing token rather than only the documented forms. That matches how `FOR XML` already behaves.

## events
[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\\|for_json\\|ForJson\\|OPTIONS_TYPE\\|INCLUDE_NULL\\|WITHOUT_ARRAY\" sqlglot/ tests/dialects/test_tsql.py | head -60", "description": "Find existing FOR XML and JSON references"}
[tool_result] sqlglot/parser.py:39:OPTIONS_TYPE = dict[str, Sequence[t.Union[Sequence[str], str]]]
sqlglot/parser.py:1571:    TRANSACTION_CHARACTERISTICS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1581:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1586:    TRIGGER_TIMING: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1592:    TRIGGER_DEFERRABLE: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1597:    CREATE_SEQUENCE: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:1621:    ISOLATED
…[2165 chars elided]…
ts/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:697:        for xml_option in xml_possible_options:
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
[tool_use Bash] {"command": "sed -n 55,110p sqlglot/parsers/tsql.py && echo ---- && sed -n 480,530p sqlglot/parsers/tsql.py && echo ---- && sed -n 3080,3115p sqlglot/generator.py && echo ---- && grep -n \"for_xml\\|QUERY_MODIFIER\\|ForXml\\|\\\"for\\\"\" sqlglot/expressions/query.py sqlglot/parser.py sqlglot/generator.py | head -30", "description": "Read T-SQL FOR XML parser and generator code"}
[tool_result] # Unsupported options:
# - OPTIMIZE FOR ( @variable_name { UNKNOWN | = <literal_constant> } [ , ...n ] )
# - TABLE HINT
OPTIONS: parser.OPTIONS_TYPE = {
    **dict.fromkeys(
        (
            "DISABLE_OPTIMIZED_PLAN_FORCING",
            "FAST",
            "IGNORE_NONCLUSTERED_COLUMNSTORE_INDEX",
            "LABEL",
            "MAXDOP",
            "MAXRECURSION",
            "MAX_GRANT_PERCENT",
            "MIN_GRANT_PERCENT",
            "NO_PERFORMANCE_SPOOL",
            "QUERYTRACEO
…[4730 chars elided]…
uery.py:1668:        **QUERY_MODIFIERS,
sqlglot/parser.py:1521:    QUERY_MODIFIER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1549:    QUERY_MODIFIER_TOKENS: t.ClassVar = set(QUERY_MODIFIER_PARSERS)
sqlglot/parser.py:4115:                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
sqlglot/parser.py:4117:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
sqlglot/parser.py:5277:        if self._match_set(self.QUERY_MODIFIER_TOKENS, advance=False):
[tool_use Bash] {"command": "grep -rn \"for_modifiers\\|\\\"for_\\\"\\|for_=\\|XMLKeyValueOption\\|xmlkeyvalue\\|queryoption\" sqlglot/ | grep -v \"\\.pyc\" ; echo ----; grep -n \"def queryoption_sql\" -A8 sqlglot/generator.py; echo ----; grep -n \"class QueryOption\\|class XMLKeyValueOption\" -A6 sqlglot/expressions/*.py; echo ----; sed -n 636,720p tests/dialects/test_tsql.py; echo ----; sed -n 1740,1760p sqlglot/expressions/query.py; grep -n \"QUERY_MODIFIERS\" -A3 sqlglot/expressions/query.py | head; grep -rn \"\\\"for_\\\"\\|for_\\b\" sqlglot/expressions/query.py | head", "description": "Trace for_ modifier and XML option handling"}
[tool_result] sqlglot/generator.py:3102:            self.for_modifiers(expression),
sqlglot/generator.py:3110:    def for_modifiers(self, expression: exp.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generator.py:3114:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
sqlglot/generator.py:5546:        for_sql = self
…[5922 chars elided]…
se,
        "fields": False,
        "unpivot": False,
        "using": False,
        "group": False,
        "columns": False,
        "include_nulls": False,
        "default_on_null": False,
        "into": False,
        "with_": False,
    }

    @property
    def unpivot(self) -> bool:
        return bool(self.args.get("unpivot"))
27:    QUERY_MODIFIERS,
28-    maybe_parse,
29-    maybe_copy,
30-    to_identifier,
--
1026:        **QUERY_MODIFIERS,
1027-    }
1028-
1029-    def select(
--
[tool_use Bash] {"command": "sed -n 280,300p sqlglot/generators/tsql.py; echo ----; sed -n 5670,5685p sqlglot/generator.py; echo ----; grep -n \"xmlkeyvalue\\|XMLKeyValue\" -r sqlglot/generators/ sqlglot/dialects/ ; echo ----; git log --oneline -3 -- sqlglot/parsers/tsql.py | cat; echo ----; $(ls /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratc
…[16 chars elided]…
qlglot/bin/python 2>/dev/null || echo python3) -c \"\nimport sqlglot\nfor d in ['duckdb','mysql','postgres']:\n    print(d, sqlglot.transpile('SELECT * FROM t FOR XML PATH, ROOT(\\'r\\')', read='tsql', write=d))\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON AUTO', read='tsql', write='tsql'))\n\" 2>&1 | tail -20", "description": "Inspect T-SQL generator and check other-dialect FOR XML output"}
[tool_result]                 limit.replace(exp.Fetch(direction="FIRST", count=limit.expression))

        return super().select_sql(expression)

    def convert_sql(self, expression: exp.Convert) -> str:
        name = "TRY_CONVERT" if expression.args.get("safe") else "CONVERT"
        return self.func(name, expression.this, expression.expression, expression.args.get("style"))

    def queryoption_sql(self, expression: exp.QueryOption) -> str:
        option = self.sql(expression, "this")
        value = sel
…[2569 chars elided]…
glot/parser.py", line 2125, in _parse_batch_statements
    self.raise_error("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parser.py", line 1992, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT * FROM t [4mFOR[0m JSON AUTO
duckdb ['SELECT * FROM t']
mysql ['SELECT * FROM t']
postgres ['SELECT * FROM t']
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python; python3 -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\ne = sqlglot.parse_one('SELECT * FROM t FOR XML PATH, ROOT(\\'r\\')', read='tsql')\nprint(repr(e))\nprint(e.sql('duckdb', unsupported_level=ErrorLevel.WARN))\n\" 2>&1 | tail -30; grep -rn \"for_\" sqlglot/generators/*.py sqlglot/generator.py | head", "description": "Inspect parsed FOR XML AST and other-dialect output"}
[tool_result] <work>/env-sqlglot/bin/python
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
        this=Var(this=PATH))),
    QueryOption(
      this=XMLKeyValueOption(
        this=Var(this=ROOT),
        expression=
…[562 chars elided]…
expression.args.get("returns_list_for_maps"):
sqlglot/generators/presto.py:379:        exp.WithinGroup: transforms.preprocess([transforms.remove_within_group_for_percentiles]),
sqlglot/generators/mysql.py:737:        for_table = self._prefixed_sql("FOR TABLE", expression, "for_table")
sqlglot/generators/mysql.py:738:        for_group = self._prefixed_sql("FOR GROUP", expression, "for_group")
sqlglot/generators/mysql.py:739:        for_user = self._prefixed_sql("FOR USER", expression, "for_user")
[tool_use Bash] {"command": "grep -rn \"QUERY_MODIFIERS\\b\" sqlglot/expressions/*.py | head -5; grep -n \"^QUERY_MODIFIERS\" -A30 sqlglot/expressions/*.py | grep -n \"for_\\|QUERY_MODIFIERS\" ; echo ----; sed -n 4108,4130p sqlglot/parser.py; echo ----; grep -n \"_parse_for\\b\\|_parse_for(\" sqlglot/parser*.py sqlglot/parsers/*.py; echo ----; grep -n \"TokenType.FOR\\b\" sqlglot/parser.py sqlglot/parsers/tsql.py | head; echo ----; grep -n \"\\bJSON\\b\" sqlglot/tokens.py sqlglot/dialects/tsql.py | head -5; grep -n \"\\\"for_\\\"\\|for_\" sqlglot/expressions/query.py | head", "description": "Locate QUERY_MODIFIERS, modifier parse loop and JSON token"}
[tool_result] sqlglot/expressions/core.py:2408:QUERY_MODIFIERS = {
sqlglot/expressions/query.py:27:    QUERY_MODIFIERS,
sqlglot/expressions/query.py:1026:        **QUERY_MODIFIERS,
sqlglot/expressions/query.py:1134:        **QUERY_MODIFIERS,
sqlglot/expressions/query.py:1668:        **QUERY_MODIFIERS,
1:sqlglot/expressions/core.py:2408:QUERY_MODIFIERS = {
----
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for 
…[1556 chars elided]…
     if self._match(TokenType.FOR):
sqlglot/parser.py:5165:        if not self._match(TokenType.FOR):
sqlglot/parser.py:7997:            ordinality = self._match_pair(TokenType.FOR, TokenType.ORDINALITY)
sqlglot/parser.py:8131:            elif self._match(TokenType.FOR):
sqlglot/parser.py:8915:        elif self._match(TokenType.FOR):
----
sqlglot/tokens.py:462:        "JSON": TokenType.JSON,
1106:    https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#for_system_time_as_of
[tool_use Bash] {"command": "sed -n 2408,2432p sqlglot/expressions/core.py; echo ----; sed -n 312,325p sqlglot/parsers/tsql.py; echo ----; grep -rn \"for_\" sqlglot/optimizer sqlglot/transforms.py sqlglot/generators sqlglot/dialects 2>/dev/null | grep -v \"for_sql\\|for_table\\|check_for\\|returns_list\" | head; echo ----; git grep -n \"FOR JSON\\|for_json\" -- tests sqlglot | head", "description": "Read QUERY_MODIFIERS and tsql FOR parser mapping"}
[tool_result] QUERY_MODIFIERS = {
    "match": False,
    "laterals": False,
    "joins": False,
    "connect": False,
    "pivots": False,
    "prewhere": False,
    "where": False,
    "group": False,
    "having": False,
    "qualify": False,
    "windows": False,
    "distribute": False,
    "sort": False,
    "cluster": False,
    "order": False,
    "limit": False,
    "offset": False,
    "locks": False,
    "sample": False,
    "settings": False,
    "format": False,
    "options": False,
}

----

   
…[1025 chars elided]…
/singlestore.py:446:        "_background_threads_for_cleanup",
sqlglot/generators/singlestore.py:480:        "call_for_pipeline",
sqlglot/generators/spark2.py:194:                [transforms.remove_within_group_for_percentiles]
sqlglot/generators/snowflake.py:539:        exp.PercentileCont: transforms.preprocess([transforms.add_within_group_for_percentiles]),
sqlglot/generators/snowflake.py:540:        exp.PercentileDisc: transforms.preprocess([transforms.add_within_group_for_percentiles]),
----
[tool_use Bash] {"command": "grep -rn '\"for_\"' sqlglot/ ; sed -n 1020,1028p sqlglot/expressions/query.py; sed -n 1128,1136p sqlglot/expressions/query.py", "description": "Find where for_ arg is declared on Select"}
[tool_result] sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
        "expression": True,
        "distinct": False,
        "by_name": False,
        "side": False,
        "kind": False,
        "on": False,
        **QUERY_MODIFIERS,
    }

        "hint": False,
        "distinct": False,
        "into": False,
        "from_": False,
        "operation_modifiers": False,
        "exclude": False,
        **QUERY_MODIFIERS,
    }
[tool_use Bash] {"command": "grep -rn \"Unsupported query option\\|unsupported_level=ErrorLevel.WARN\\|assertLogs\" tests/dialects/*.py | head -5; echo ----; grep -n \"def validate_all\" -A30 tests/dialects/test_dialect.py | grep -n \"unsupported\\|def \" | head; echo ----; grep -n \"def expressions\" -A25 sqlglot/generator.py | grep -n \"if \\|filter\\|sql\" | head -12", "description": "Check unsupported-warning test patterns and expressions filter"}
[tool_result] tests/dialects/test_bigquery.py:2134:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2143:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2151:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2171:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2192:        with self.assertLogs(helper_logger):
----
1:68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
21:88-                        unsupported_level=ErrorLevel.IGNORE,
----
5:4460-        sqls: t.Collection[str | exp.Expr] | None = None,
15:4470-        expressions = expression.args.get(key or "expressions") if expression else sqls
17:4472-        if not expressions:
20:4475-        if flat:
21:4476-            return sep.join(sql for sql in (self.sql(e) for e in expressions) if sql)
23:4478-        num_sqls = len(expressions)
24:4479-        result_sqls = []
[assistant] Plan: parse `FOR JSON` in the T-SQL parser into its own `for_json` arg (so the generator can print `FOR JSON` separately from `FOR XML`), and have the base generator print it with the same drop-and-warn path that `FOR XML` uses in other dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(\n    (\n        \"AUTO\",\n        \"INCLUDE_NULL_VALUES\",\n        \"PATH\",\n        \"WITHOUT_ARRAY_WRAPPER\",\n    ),\n    tuple(),\n)\n\n\nOPTIONS_THAT_REQUIRE_EQUAL"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[607 chars elided]…
n            return \"for_\", None\n\n        def _parse_for_option() -> exp.Expr | None:\n            return self.expression(\n                exp.QueryOption(\n                    this=self._parse_var_from_options(options, raise_unmatched=False)\n                    or self._parse_xml_key_value_option()\n                )\n            )\n\n        return key, self._parse_csv(_parse_for_option)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"
…[21 chars elided]…
   def for_modifiers(self, expression: exp.Expr) -> str:\n        for_xml = self.expressions(expression, key=\"for_\")\n        for_json = self.expressions(expression, key=\"for_json\")\n        xml_sql = f\"{self.sep()}FOR XML{self.seg(for_xml)}\" if for_xml else \"\"\n        json_sql = f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\"\n        return f\"{xml_sql}{json_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/sqlglot/expressions/core.py", "old_string": "    \"locks\": False,\n    \"sample\": False,", "new_string": "    \"locks\": False,\n    \"sample\": False,"}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] Now a test for the round-trip and the other-dialect drop, placed after `test_for_xml`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "            \"\"\"SELECT\n  *\nFROM t\nFOR XML\n  PATH,\n  BINARY BASE64,\n  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "            \"\"\"SELECT\n
…[803 chars elided]…
ULL_VALUES\",\n            \"\"\"SELECT\n  *\nFROM t\nFOR JSON\n  PATH,\n  ROOT('RootName'),\n  INCLUDE_NULL_VALUES\"\"\",\n            pretty=True,\n        )\n\n        with self.assertRaises(UnsupportedError):\n            parse_one(\"SELECT * FROM t FOR JSON AUTO\", read=\"tsql\").sql(\n                \"duckdb\", unsupported_level=ErrorLevel.RAISE\n            )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_tsql.py | grep import; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -30", "description": "Run T-SQL dialect tests"}
[tool_result] from sqlglot import exp, parse_one
from sqlglot.errors import ParseError, UnsupportedError
from sqlglot.optimizer.annotate_types import annotate_types
from tests.dialects.test_dialect import Validator
    
            for json_option in json_possible_options:
                with self.subTest(f"Testing FOR JSON option: {json_option}"):
                    self.validate_identity(f"SELECT * FROM t FOR JSON {json_option}")
    
            self.validate_identity(
                "SELECT * FROM t FO
…[402 chars elided]…
l=ErrorLevel.RAISE
                                                ^^^^^^^^^^
                )
E               NameError: name 'ErrorLevel' is not defined

tests/dialects/test_tsql.py:742: NameError
----------------------------- Captured stdout call -----------------------------
uuuuuuu
=========================== short test summary info ============================
FAILED tests/dialects/test_tsql.py::TestTSQL::test_for_json - NameError: name...
1 failed, 53 passed, 663 subtests passed in 0.37s
[assistant] The round-trip tests pass; the failure is a missing `ErrorLevel` import in my test. Fixing that and running the full suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "from sqlglot.errors import ParseError, UnsupportedError", "new_string": "from sqlglot.errors import ErrorLevel, ParseError, UnsupportedError"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152156-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON PATH, ROOT(\\'r\\')', read='tsql', write='duckdb'))\nprint(sqlglot.transpile('SELECT * FROM t FOR XML PATH', read='tsql', write='tsql'))\nprint(sqlglot.transpile('SELECT * FROM t FOR JSON AUTO', read='tsql', write='tsql'))\n\"; git status --short", "description": "Run full test suite and spot-check transpilation"}
[tool_result] ....................................................................................... [ 43%]
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
.............................................................................................................................................................. [ 67%]
............................................... [ 72%]
.....................................
…[104 chars elided]…
..................... [ 86%]
............... [ 87%]
............................................................................... [ 94%]
....................... [ 96%]
......................................                    [100%]
1108 passed, 18025 subtests passed in 55.41s
Unsupported query option.
Unsupported query option.
['SELECT * FROM t']
['SELECT * FROM t FOR XML PATH']
['SELECT * FROM t FOR JSON AUTO']
 M sqlglot/generator.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.py
[assistant] All 1108 tests pass. Running the linter and type checker on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/generator.py sqlglot/parsers/tsql.py tests/dialects/test_tsql.py && $PY -m ruff format --check sqlglot/generator.py sqlglot/parsers/tsql.py tests/dialects/test_tsql.py) 2>&1 | tail -5; $PY -m mypy sqlglot/parsers/tsql.py sqlglot/generator.py 2>&1 | tail -3", "description": "Run ruff lint, format check, and mypy on changed files"}
[tool_result] All checks passed!
3 files already formatted
Success: no issues found in 2 source files
[assistant] `FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the same "Unsupported query option." warning they use for `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

The changes:

- **Parser** (`sqlglot/parsers/tsql.py`): `FOR JSON` is parsed into a new `for_json` arg, separate from `for_`, using a `JSON_OPTIONS` set (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `ROOT('name')` goes through the same key-value path `FOR XML` uses for `ROOT`.
- **Generator** (`sqlglot/generator.py`): `for_modifiers` emits `FOR XML` and `FOR JSON` from their own args. Other dialects reach the existing `queryoption_sql` warning and drop the clause, so no per-dialect change was needed.
- **Tests** (`tests/dialects/test_tsql.py`): a new `test_for_json` covers the option combinations as identity round-trips, a pretty-printed case, and an `UnsupportedError` check for DuckDB.

Because `ROOT` reuses the loose XML parsing, `ROOT` accepts any trailing token rather than only the documented forms. That matches how `FOR XML` already behaves.
