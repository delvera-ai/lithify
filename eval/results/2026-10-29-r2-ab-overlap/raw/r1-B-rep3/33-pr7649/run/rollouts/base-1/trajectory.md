# trajectory base-1

final message:
T-SQL now parses and round-trips `FOR JSON`, and other dialects drop it with the same "Unsupported query option." warning that `FOR XML` already gets. The full suite passes (1108 tests) and ruff is clean on the changed files. I did not commit.

Changes:

- **`sqlglot/parsers/tsql.py`**: added `JSON_OPTIONS` (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `_parse_for` now dispatches on `FOR JSON` or `FOR XML`, and both share the existing option parsing. `ROOT` and `ROOT('name')` go through the same key-value path `FOR XML` uses.
- **`sqlglot/generator.py`**: `for_modifiers` emits `FOR JSON` for the new `for_json` arg. `FOR XML` output is unchanged.
- **`tests/dialects/test_tsql.py`**: added `test_for_json`, covering option combinations as identity round-trips, a pretty-printed case, and a tsql → duckdb case that drops the clause.

Decisions to check:

- JSON options go in a separate `for_json` key rather than `for_`. This keeps the `FOR XML` AST shape unchanged, at the cost of a second key the generator has to check.
- Option order and mode are not enforced, matching how `FOR XML` is parsed today. Input such as `FOR JSON` with no `AUTO`/`PATH` parses without error.

## events
[assistant] I'll start by finding how `FOR XML` is handled today, since the new clause should follow the same path.
[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\" sqlglot/ --include=*.py | head -60; echo ---; grep -rn -i \"for json\\|ForJson\\|JSON_OPTIONS\\|for_json\" sqlglot/ tests/ --include=*.py | head -40", "description": "Search for FOR XML and FOR JSON references"}
[tool_result] (eval):1: no matches found: --include=*.py
---
(eval):1: no matches found: --include=*.py
[assistant] The shell glob failed on `--include=*.py`. I'll use the search tool instead.
[tool_use Grep] {"pattern": "(?i)for_xml|ForXml|for xml|for_json|ForJson|for json", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "grep -rn -i -E \"for_?xml|for json|for_?json\" sqlglot tests --include='*.py'", "description": "Search repo for FOR XML and FOR JSON references"}
[tool_result] sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
tests/dialects/test_tsql.py:545:            for json_clause in ("", " NULL ON NULL", " ABSENT ON NULL"):
tests/dialects/test_tsql.py:640:    def test_for_xml(self):
[tool_use Bash] {"command": "sed -n 480,540p sqlglot/parsers/tsql.py; echo ----; sed -n 630,700p tests/dialects/test_tsql.py; echo ----; grep -rn -i -E \"ForXml|QueryOption|FOR_XML|\\bXML\\b\" sqlglot --include='*.py' | grep -v \"^sqlglot/dialects/.*XML\" | head -40", "description": "Read FOR XML parser and its tests"}
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
…[6022 chars elided]…
ption) -> str:
sqlglot/expressions/functions.py:431:# XML
sqlglot/expressions/query.py:914:class QueryOption(Expression):
sqlglot/expressions/datatypes.py:158:    XML = auto()
sqlglot/generators/fabric.py:70:        exp.DType.XML: "VARCHAR",
sqlglot/generators/singlestore.py:337:        exp.DType.XML,
sqlglot/generators/tsql.py:288:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
sqlglot/generators/oracle.py:126:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
[assistant] The `FOR XML` path is a `QueryOption` on the select's `for` modifiers. I need the generator side, the option tables, and how other dialects drop it.
[tool_use Bash] {"command": "sed -n 3085,3125p sqlglot/generator.py; echo ----TSQLGEN; sed -n 270,310p sqlglot/generators/tsql.py; echo ----ORACLE; sed -n 120,140p sqlglot/generators/oracle.py; echo ----EXPR; sed -n 900,935p sqlglot/expressions/query.py; echo ----XMLOPTS; grep -rn -E \"XML_OPTIONS|XMLKeyValueOption|for_xml|ELEMENTS|XSINIL\" sqlglot --include='*.py' | head -30", "description": "Read generator FOR XML and QueryOption code"}
[tool_result]             limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))

        return csv(
            *sqls,
            *[self.sql(join) for join in expression.args.get("joins") or []],
            self.sql(expression, "match"),
            *[self.sql(lateral) for lateral in expression.args.get("laterals") or []],
            self.sql(expression, "prewhere"),
            self.sql(expression, "where"),
            self.sql(expression, "connect"),
            self.sql(expressi
…[5695 chars elided]…
ONS, raise_unmatched=False)
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
sqlglot/generator.py:5674:    def xmlkeyvalueoption_sql(self, expression: exp.XMLKeyValueOption) -> str:
sqlglot/expressions/query.py:2077:class XMLKeyValueOption(Expression):
sqlglot/generators/postgres.py:446:                    self.unsupported("Unsupported JSON_ARRAY_ELEMENTS with offset")
sqlglot/generators/postgres.py:448:                return f"JSON_ARRAY_ELEMENTS({arg_as_json}){alias}"
[assistant] The base generator hardcodes `FOR XML` in `for_modifiers`, so FOR JSON needs its own emission path. Next I'll read the XML option tables and check what other dialects currently do with `FOR XML`.
[tool_use Bash] {"command": "sed -n 60,125p sqlglot/parsers/tsql.py; echo ----; sed -n 2070,2085p sqlglot/expressions/query.py; echo ----; sed -n 5670,5680p sqlglot/generator.py; echo ----; grep -n -E \"for_|\\\"for\\\"\" sqlglot/parser.py sqlglot/parsers/tsql.py sqlglot/expressions/query.py | head; echo ----; grep -rn -B3 -A12 \"FOR XML\" tests --include='*.py' | grep -v \"test_tsql.py\" | head -60", "description": "Read XML options, for_ arg, and FOR XML tests in other dialects"}
[tool_result]     **dict.fromkeys(
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
            "QUERYTRACEON",
            "RECOMPILE",
        ),
        tuple(),
    ),
    "CONCAT": ("UNION",),
    "DISABLE": ("EXTERNALPUSHDOWN", "SCALEOUTEXECUTION"),
    "
…[2311 chars elided]…
gger_for_each(self) -> str | None:
sqlglot/parser.py:3158:            for_or_in = "FOR"
sqlglot/parser.py:3160:            for_or_in = "IN"
sqlglot/parser.py:3162:            for_or_in = None
sqlglot/parser.py:3183:                this=this, kind=kind, for_or_in=for_or_in, lock_type=lock_type, override=override
sqlglot/parser.py:7465:    def _parse_period_for_system_time(self) -> exp.PeriodForSystemTimeConstraint | None:
sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
----
[tool_use Bash] {"command": "grep -rn -E \"_parse_for\\(|\\\"for_\\\"|for_=|key=\\\"for_\\\"|\\bfor_\\b\" sqlglot --include='*.py' | grep -v \"for_or_in\\|for_each\\|for_system\" | head -20; echo ----; grep -rn -E \"for_\\b\" sqlglot/expressions/query.py | head; echo ----; grep -rln \"FOR XML\\|for_xml\\|test_for_xml\" tests | head; echo; ls tests | head -50; echo ----; grep -rn -i \"unsupported\" tests/dialects/test_tsql.py | head -5; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1 && git log --oneline -3 -- sqlglot/parsers/tsql.py", "description": "Locate for_ arg usage and related tests"}
[tool_result] sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/parsers/tsql.py:504:    def _parse_for(self) -> list[exp.Expr] | None:
sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_":
…[692 chars elided]…
t_tsql.py:2:from sqlglot.errors import ParseError, UnsupportedError
tests/dialects/test_tsql.py:636:                "databricks": UnsupportedError,
tests/dialects/test_tsql.py:2316:                "tsql": UnsupportedError,
tests/dialects/test_tsql.py:2326:                "tsql": UnsupportedError,
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
f7bb6bea8 chore: use collections.abc and built-in types for typing to avoid deprecation (#7329)
ea76ca554 Chore: unpin ruff (#7287)
[assistant] I have the parse and generate paths. Next I'll check the current behavior of `FOR XML` and `FOR JSON` with the project's Python environment.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in ['SELECT * FROM t FOR XML AUTO', 'SELECT * FROM t FOR XML PATH(\\'a\\'), ROOT(\\'r\\')', 'SELECT * FROM t FOR JSON AUTO']:\n    try:\n        e = sqlglot.parse_one(q, read='tsql')\n        print(repr(e.args.get('for_')))\n        print('tsql:', e.sql('tsql'))\n    except Exception as ex: print('ERR', type(ex), ex)\n    try:\n        print('duckdb:', sqlglot.transpile(q, read='tsql', write='duckdb', unsupported_level=sqlglot.ErrorLevel.WARN))\n    except Exception as ex: print('ERR2', type(ex), ex)\n\" 2>&1 | head -40; git status --short | head", "description": "Check current FOR XML/FOR JSON behavior"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
[QueryOption(
  this=Var(this=AUTO))]
tsql: SELECT * FROM t FOR XML AUTO
duckdb: ['SELECT * FROM t']
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH),
    expression=Literal(this='a', is_string=True))), QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=ROOT),
    expression=Literal(this='r', is_string=True)))]
tsql: SELECT * FROM t FOR XML PATH('a'), ROOT('r')
duckdb: ['SELECT * FROM t']
ERR <class 'sqlglot.errors.ParseError'> Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT * FROM t [4mFOR[0m JSON AUTO
ERR2 <class 'sqlglot.errors.ParseError'> Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT * FROM t [4mFOR[0m JSON AUTO
ok
[assistant] Current behavior confirms the split: `FOR XML` parses to `for_` and generates back, and other dialects drop it with an "Unsupported query option." warning. `FOR JSON` fails to parse at all. Next I'll read the option-parsing helper, the query-modifier dispatch, and the test helpers that drive unsupported-level checks.
[tool_use Bash] {"command": "grep -n \"def _parse_var_from_options\" -A40 sqlglot/parser.py | head -60; echo ----QM; grep -n \"QUERY_MODIFIER_PARSERS\\|_parse_query_modifiers\" sqlglot/parser.py | head; echo ----; sed -n 310,330p sqlglot/parsers/tsql.py; echo ----SEL; grep -rn \"QUERY_MODIFIERS\\b\" sqlglot --include='*.py' | head -5; grep -n \"class Select(\" -A8 sqlglot/expressions/query.py; echo ----HELP; grep -n \"def validate_all\" -A30 tests/dialects/test_dialect.py | head -50", "description": "Read option parser, modifier dispatch, and test helpers"}
[tool_result] 9140:    def _parse_var_from_options(
9141-        self, options: OPTIONS_TYPE, raise_unmatched: bool = True
9142-    ) -> exp.Var | None:
9143-        start = self._curr
9144-        if not start:
9145-            return None
9146-
9147-        option = start.text.upper()
9148-        continuations = options.get(option)
9149-
9150-        index = self._index
9151-        self._advance()
9152-        for keywords in continuations or []:
9153-            if isinstance(keywords, str):
9154-       
…[3570 chars elided]…
         self.dialect,
88-                        unsupported_level=ErrorLevel.IGNORE,
89-                        pretty=pretty,
90-                        identify=identify,
91-                    ),
92-                    sql,
93-                )
94-
95-        for write_dialect, write_sql in (write or {}).items():
96-            with self.subTest(f"{sql} -> {write_dialect}"):
97-                if write_sql is UnsupportedError:
98-                    with self.assertRaises(UnsupportedError):
[tool_use Bash] {"command": "sed -n 2408,2425p sqlglot/expressions/core.py; sed -n 1123,1150p sqlglot/expressions/query.py | grep -n \"for_\\|QUERY\\|}\" ; sed -n 1020,1030p sqlglot/expressions/query.py; grep -n \"def _parse_for_xml\\|self.expression(\" sqlglot/parsers/tsql.py | head -3; grep -n \"def test_for_xml\" -A3 tests/dialects/test_tsql.py | head; sed -n 655,672p tests/dialects/test_tsql.py | head -3; grep -n \"options\\b\" sqlglot/expressions/core.py | head -3", "description": "Inspect query modifier arg definitions"}
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
12:        **QUERY_MODIFIERS,
13:    }
        "expression": True,
        "distinct": False,
        "by_name": False,
…[120 chars elided]…
      self: S,
rg: regex parse error:
    (?:def _parse_for_xml|self.expression()
    ^
error: unclosed group
0 matches for 'def _parse_for_xml\|self.expression('
640:    def test_for_xml(self):
641-        xml_possible_options = [
642-            "RAW('ElementName')",
643-            "RAW('ElementName'), BINARY BASE64",
            "RAW('ElementName'), XMLSCHEMA('TargetNameSpaceURI'), ELEMENTS XSINIL",
            "AUTO",
            "AUTO, BINARY BASE64",
12 matches in 12 files:

1562:0:False,
[tool_use Bash] {"command": "sed -n 2425,2445p sqlglot/expressions/core.py; grep -n \"for_\" sqlglot/expressions/core.py", "description": "Read rest of QUERY_MODIFIERS dict"}
[tool_result]     "offset": False,
    "locks": False,
    "sample": False,
    "settings": False,
    "format": False,
    "options": False,
}


TIMESTAMP_PARTS = {
    "year": False,
    "month": False,
    "day": False,
    "hour": False,
    "min": False,
    "sec": False,
    "nano": False,
}


@t.overload
1 matches in 1 files:

1903:0:False,
[tool_use Bash] {"command": "sed -n 1123,1160p sqlglot/expressions/query.py", "description": "Read Select arg_types"}
[tool_result] class Select(Expression, Query):
    arg_types = {
        "with_": False,
        "kind": False,
        "expressions": False,
        "hint": False,
        "distinct": False,
        "into": False,
        "from_": False,
        "operation_modifiers": False,
        "exclude": False,
        **QUERY_MODIFIERS,
    }

    def from_(
        self,
        expression: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
    ) -> 
…[157 chars elided]…
'

        Args:
            expression : the SQL code strings to parse.
                If a `From` instance is passed, this is used as-is.
                If another `Expr` instance is passed, it will be wrapped in a `From`.
            dialect: the dialect used to parse the input expression.
            copy: if `False`, modify this expression instance in-place.
            opts: other options to use to parse the input expressions.

        Returns:
            The modified Select expression.
[assistant] `for_` is not declared in `Select.arg_types`, so the new key can follow the same pattern without touching the schema. Before editing I need three more facts: whether `TokenType.JSON` exists, how existing tests assert unsupported-option warnings, and whether any generator overrides `for_modifiers`.
[tool_use Bash] {"command": "sed -n 95,112p tests/dialects/test_dialect.py; echo ----; grep -rn \"assertLogs\\|unsupported_level=\" tests/dialects/test_tsql.py | head -5; echo ----; grep -n \"    JSON = \\|    JSON\\b\" sqlglot/tokenizer_core.py | head -3; echo ----; grep -rn \"for_modifiers\\|def expressions\" sqlglot --include='*.py' | head; echo ----; grep -n \"_match_pair\\|def _match_text_seq\" sqlglot/parser.py | head -3", "description": "Check test helpers, warnings conventions, and token types"}
[tool_result]         for write_dialect, write_sql in (write or {}).items():
            with self.subTest(f"{sql} -> {write_dialect}"):
                if write_sql is UnsupportedError:
                    with self.assertRaises(UnsupportedError):
                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
                else:
                    self.assertEqual(
                        expression.sql(
                            write_dialect,
                            unsu
…[447 chars elided]…
pression: exp.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generator.py:4456:    def expressions(
sqlglot/expressions/core.py:142:    def expressions(self) -> list[t.Any]:
sqlglot/expressions/core.py:894:    def expressions(self) -> list[t.Any]:
----
35 matches in 22 files:

1949:0:str, advance: bool = True) -> bool:
[assistant] I have what I need. The plan:

1. **Parser** (`sqlglot/parsers/tsql.py`): add a `JSON_OPTIONS` table and let `_parse_for` dispatch on `FOR JSON` vs `FOR XML`. JSON options go into a separate `for_json` key so the existing `FOR XML` AST shape stays unchanged.
2. **Generator** (`sqlglot/generator.py`): `for_modifiers` emits `FOR JSON` for the new key. Other dialects inherit the existing `queryoption_sql` warning and drop the empty clause.
3. **Tests** (`tests/dialects/test_tsql.py`): round-trip cases plus a cross-dialect drop check.

I'll start with the parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(\n    (\"AUTO\", \"INCLUDE_NULL_VALUES\", \"PATH\", \"WITHOUT_ARRAY_WRAPPER\"), tuple()\n)\n\n\nOPTIONS_THAT_REQUIRE_EQUAL"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[607 chars elided]…
n            return \"for_\", None\n\n        def _parse_for_option() -> exp.Expr | None:\n            return self.expression(\n                exp.QueryOption(\n                    this=self._parse_var_from_options(options, raise_unmatched=False)\n                    or self._parse_xml_key_value_option()\n                )\n            )\n\n        return key, self._parse_csv(_parse_for_option)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"", "new_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_xml = self.expressions(expression, key=\"for_\")\n        if for_xml:\n            return f\"{self.sep()}FOR XML{self.seg(for_xml)}\"\n\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests. I'll add a `test_for_json` next to `test_for_xml`, after reading the end of that method.
[tool_use Bash] {"command": "grep -n \"FOR XML {xml_option}\" -A4 tests/dialects/test_tsql.py", "description": "Locate end of test_for_xml"}
[tool_result] 699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
700-
701-        self.validate_identity(
702-            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
703-            """SELECT
[tool_use Bash] {"command": "sed -n 700,725p tests/dialects/test_tsql.py", "description": "Read rest of test_for_xml"}
[tool_result]         self.validate_identity(
            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
            """SELECT
  *
FROM t
FOR XML
  PATH,
  BINARY BASE64,
  ELEMENTS XSINIL""",
            pretty=True,
        )

    def test_types(self):
        self.validate_identity("CAST(x AS XML)")
        self.validate_identity("CAST(x AS UNIQUEIDENTIFIER)")
        self.validate_identity("CAST(x AS MONEY)")
        self.validate_identity("CAST(x AS SMALLMONEY)")
        self.validate_identity("CAST(x AS IMAGE)")
        self.validate_identity("CAST(x AS SQL_VARIANT)")
        self.validate_identity("CAST(x AS BIT)")

        self.validate_all(
            "CAST(x AS DATETIME2(6))",
            write={
                "hive": "CAST(x AS TIMESTAMP)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "  PATH,\n  BINARY BASE64,\n  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "  PATH,\n  BINARY BASE64,\n  ELEMENTS XSINIL\"\"\",\n            pretty=Tr
…[951 chars elided]…
PATH,\n  ROOT('RootName'),\n  WITHOUT_ARRAY_WRAPPER\"\"\",\n            pretty=True,\n        )\n\n        self.validate_all(\n            \"SELECT * FROM t FOR JSON AUTO, ROOT('RootName')\",\n            write={\n                \"duckdb\": \"SELECT * FROM t\",\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO, ROOT('RootName')\",\n            },\n        )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191932-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] Now I'll run the T-SQL test module and the new test, using the project's test interpreter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py -k \"for_json or for_xml\" 2>&1 | tail -30", "description": "Run new FOR JSON and FOR XML tests"}
[tool_result] ..      [100%]
2 passed, 52 deselected, 65 subtests passed in 0.14s
[assistant] Both pass. Next I'll confirm the unsupported-option warning fires in another dialect and that the full suite still passes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\ne = sqlglot.parse_one(\\\"SELECT * FROM t FOR JSON PATH, ROOT('r')\\\", read='tsql')\nprint(repr(e.sql('duckdb', unsupported_level=ErrorLevel.WARN)))\nprint(e.sql('tsql'))\nprint(sqlglot.transpile(\\\"SELECT * FROM t FOR JSON AUTO\\\", read='tsql', write='tsql', pretty=True)[0])\ntry:\n    e.sql('duckdb', unsupported_level=ErrorLevel.RAISE)\nexcept Exception as ex: print('RAISE:', type(ex).__name__, ex)\n\"; echo ---FULL; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify warnings and run the full test suite"}
[tool_result] Unsupported query option.
Unsupported query option.
'SELECT * FROM t'
SELECT * FROM t FOR JSON PATH, ROOT('r')
SELECT
  *
FROM t
FOR JSON
  AUTO
RAISE: UnsupportedError Unsupported query option.

Unsupported query option.
---FULL
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
...........................................................................................................................
…[21 chars elided]…
......... [ 67%]
............................................................................................................ [ 77%]
............................................. [ 81%]
....................... [ 83%]
............. [ 84%]
................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1108 passed, 18030 subtests passed in 46.13s
[assistant] The full suite passes (1108 tests), and the other-dialect path warns and drops the clause as required. Last, a lint and format check on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py && $PY -m ruff format --check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py) 2>&1 | tail -8; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generator.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.py
[assistant] T-SQL now parses and round-trips `FOR JSON`, and other dialects drop it with the same "Unsupported query option." warning that `FOR XML` already gets. The full suite passes (1108 tests) and ruff is clean on the changed files. I did not commit.

Changes:

- **`sqlglot/parsers/tsql.py`**: added `JSON_OPTIONS` (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `_parse_for` now dispatches on `FOR JSON` or `FOR XML`, and both share the existing option parsing. `ROOT` and `ROOT('name')` go through the same key-value path `FOR XML` uses.
- **`sqlglot/generator.py`**: `for_modifiers` emits `FOR JSON` for the new `for_json` arg. `FOR XML` output is unchanged.
- **`tests/dialects/test_tsql.py`**: added `test_for_json`, covering option combinations as identity round-trips, a pretty-printed case, and a tsql → duckdb case that drops the clause.

Decisions to check:

- JSON options go in a separate `for_json` key rather than `for_`. This keeps the `FOR XML` AST shape unchanged, at the cost of a second key the generator has to check.
- Option order and mode are not enforced, matching how `FOR XML` is parsed today. Input such as `FOR JSON` with no `AUTO`/`PATH` parses without error.
