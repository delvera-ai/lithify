# trajectory base-1

final message:
`FOR JSON` now parses and round-trips in T-SQL. Other dialects warn and drop the clause. The full suite passes (1108 tests, 18033 subtests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**What changed**

- **`sqlglot/parsers/tsql.py`**: added `JSON_OPTIONS` (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `_parse_for` now returns a `(key, value)` pair, so `FOR JSON` is stored under its own `for_json` key rather than `for_`. `ROOT` and `ROOT('name')` go through the existing `XMLKeyValueOption` path.
- **`sqlglot/generator.py`**: the base generator's `for_json_modifiers` calls `unsupported("FOR JSON is not supported.")` and returns nothing, so the clause is dropped with a warning.
- **`sqlglot/generators/tsql.py`**: overrides `for_json_modifiers` to emit `FOR JSON` with its options.
- **`tests/dialects/test_tsql.py`**: added `test_for_json` covering the option combinations as identity round-trips, a pretty-printed case, and the cross-dialect warning and drop for duckdb, mysql, and oracle.

**Things to know**

- The option parsing is as lenient as the existing `FOR XML` parsing, so `FOR JSON` followed by an arbitrary word may parse without error. I kept it consistent with `FOR XML` rather than tightening it.
- Oracle is a pre-existing exception. Its `queryoption_sql` override doesn't drop anything, so `FOR XML PATH` still comes out unchanged in Oracle. My change doesn't alter that, and `FOR JSON` is dropped there correctly. Fixing Oracle's `FOR XML` would be a separate change.

## events
[assistant] I'll start by finding how `FOR XML` is handled across the T-SQL and other dialects.
[tool_use Bash] {"command": "git status --short | head && grep -rn \"FOR XML\\|ForXml\\|for_xml\\|FOR_XML\\|ForJson\\|FOR JSON\" --include=*.py sqlglot tests | head -80", "description": "Locate FOR XML handling in sources and tests"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short | head; grep -rn \"ForXml\\|FOR XML\\|for_xml\\|FOR_XML\\|ForJson\\|FOR JSON\" sqlglot tests | head -80", "description": "Locate FOR XML handling in sources and tests"}
[tool_result] sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
tests/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
[tool_use Bash] {"command": "sed -n 480,530p sqlglot/parsers/tsql.py; echo ----; sed -n 3085,3115p sqlglot/generator.py; echo ----; sed -n 636,720p tests/dialects/test_tsql.py; echo ----; grep -n \"for_xml\\|ForXml\\|class Query\\|\\\"options\\\"\\|unsupported_args\" sqlglot/expressions.py | head -30; grep -rn \"for_xml\\|FOR XML\" sqlglot/ | head", "description": "Read FOR XML parser, generator, and tests"}
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
…[6432 chars elided]…
NEY)")
        self.validate_identity("CAST(x AS IMAGE)")
        self.validate_identity("CAST(x AS SQL_VARIANT)")
        self.validate_identity("CAST(x AS BIT)")
----
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
[assistant] The `FOR XML` path is a `for_` list of `QueryOption` nodes, rendered by `for_modifiers`. Next I'll read the option sets, the `queryoption_sql` generator, and how `for_` is declared on `Query`.
[tool_use Bash] {"command": "grep -rn \"XML_OPTIONS\\|\\\"for_\\\"\\|for_modifiers\\|QueryOption\\|XMLKeyValueOption\\|\\\"options\\\"\" sqlglot | grep -v \"^Binary\"; echo ----; sed -n 3112,3135p sqlglot/generator.py; echo ----; grep -n \"XML_OPTIONS\" -A 40 sqlglot/parsers/tsql.py | head -60", "description": "Find option sets, QueryOption and for_ usage"}
[tool_result] sqlglot/parser.py:2531:                                if arg == "options":
sqlglot/parser.py:2538:                        sequence_props.set("options", options)
sqlglot/parser.py:2634:        seq.set("options", options if options else None)
sqlglot/generator.py:1115:        options = expression.args.get("options")
sqlglot/generator.py:1250:        options = self.expressions(expression, key="options", flat=True, sep=" ")
sqlglot/generator.py:1262:        options = self.expressions(expression, ke
…[7619 chars elided]…
519-        self,
520-    ) -> tuple[list[exp.Expr], list[exp.Expr] | None]:
521-        """
522-        T-SQL supports the syntax alias = expression in the SELECT's projection list,
523-        so we transform all parsed Selects to convert their EQ projections into Aliases.
524-
525-        See: https://learn.microsoft.com/en-us/sql/t-sql/queries/select-clause-transact-sql?view=sql-server-ver16#syntax
526-        """
527-        projections, _ = super()._parse_projections()
528-        return [
[assistant] Now the T-SQL generator's `queryoption_sql`, the `XMLKeyValueOption` generator, and the `QueryOption`/`XMLKeyValueOption` node definitions.
[tool_use Bash] {"command": "sed -n 280,300p sqlglot/generators/tsql.py; echo ----; sed -n 5670,5685p sqlglot/generator.py; echo ----; sed -n 905,925p sqlglot/expressions/query.py; echo ----; sed -n 2070,2090p sqlglot/expressions/query.py; echo ----; grep -n '\"for_\"' sqlglot/expressions/*.py; echo ----; sed -n 120,135p sqlglot/generators/oracle.py; echo ----; sed -n 160,175p sqlglot/parsers/oracle.py; echo ---; grep -n \"unsupported\\b\" sqlglot/generators/tsql.py | head -3; grep -n \"def unsupported\" -A8 sqlglot/generator.py", "description": "Read generator/node definitions for query options"}
[tool_result]                 limit.replace(exp.Fetch(direction="FIRST", count=limit.expression))

        return super().select_sql(expression)

    def convert_sql(self, expression: exp.Convert) -> str:
        name = "TRY_CONVERT" if expression.args.get("safe") else "CONVERT"
        return self.func(name, expression.this, expression.expression, expression.args.get("style"))

    def queryoption_sql(self, expression: exp.QueryOption) -> str:
        option = self.sql(expression, "this")
        value = sel
…[3877 chars elided]…
 diagnostic_msg).
36-    """
37-    diagnostic_by_arg: dict[str, str | None] = {}
38-    for arg in args:
--
971:    def unsupported(self, message: str) -> None:
972-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
973-            raise UnsupportedError(message)
974-        self.unsupported_messages.append(message)
975-
976-    def sep(self, sep: str = " ") -> str:
977-        return f"{sep.strip()}\n" if self.pretty else sep
978-
979-    def seg(self, sql: str, sep: str = " ") -> str:
[assistant] The base generator's `queryoption_sql` warns and returns `""`, but `for_modifiers` hardcodes the `FOR XML` prefix. I need to see what other dialects actually emit for `FOR XML` today before deciding how to handle `FOR JSON`.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SELECT * FROM t FOR XML PATH', 'SELECT * FROM t FOR XML AUTO, ROOT(\\'r\\')']:\n    e = sqlglot.parse_one(q, read='tsql')\n    print(repr(e.args.get('for_')))\n    for d in ['duckdb','oracle','mysql']:\n        try:\n            print(d, repr(e.sql(d, unsupported_level=sqlglot.ErrorLevel.WARN)))\n        except Exception as ex: print(d, 'ERR', ex)\n\" 2>&1 | head -40; grep -n '\"for_\"\\|for_' sqlglot/expressions/query.py | head; grep -n \"for_\" sqlglot/parser.py | head", "description": "Check current FOR XML behavior in other dialects"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH)))]
duckdb 'SELECT * FROM t'
oracle 'SELECT * FROM t FOR XML PATH'
mysql 'SELECT * FROM t'
[QueryOption(
  this=Var(this=AUTO)), QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=ROOT),
    expression=Literal(this='r', is_string=True)))]
duckdb 'SELECT * FROM t'
oracle "SEL
…[255 chars elided]…
    for_each = self._parse_trigger_for_each()
2482:                    for_each=for_each,
2707:    def _parse_trigger_for_each(self) -> str | None:
3158:            for_or_in = "FOR"
3160:            for_or_in = "IN"
3162:            for_or_in = None
3183:                this=this, kind=kind, for_or_in=for_or_in, lock_type=lock_type, override=override
7465:    def _parse_period_for_system_time(self) -> exp.PeriodForSystemTimeConstraint | None:
9656:                for_=_parse_overlay_arg("FOR"),
[assistant] Current behavior: `queryoption_sql` returns `""` in the base generator, so `for_modifiers` produces nothing and the whole `FOR XML` clause is dropped with a warning. Oracle overrides `queryoption_sql` without that drop, which is a pre-existing wart. Next I'll check how the modifier parsers dispatch and whether `JSON` tokenizes as its own token.
[tool_use Bash] {"command": "grep -n \"QUERY_MODIFIER_PARSERS\" -A3 sqlglot/parser.py | head -20; grep -n \"def _parse_query_modifiers\" -A45 sqlglot/parser.py | grep -n \"parser\\|key\\|set(\" ; grep -n \"TokenType.JSON\\b\\|\\\"JSON\\\"\" sqlglot/tokens.py sqlglot/parsers/tsql.py | head -5; grep -n \"XML\\b\" sqlglot/tokens.py | head; sed -n 300,330p sqlglot/parsers/tsql.py; grep -n \"def _parse_var_from_options\" -A30 sqlglot/parser.py | head -45", "description": "Inspect modifier dispatch and option parsing helpers"}
[tool_result] 1521:    QUERY_MODIFIER_PARSERS: t.ClassVar = {
1522-        TokenType.MATCH_RECOGNIZE: lambda self: ("match", self._parse_match_recognize()),
1523-        TokenType.PREWHERE: lambda self: ("prewhere", self._parse_prewhere()),
1524-        TokenType.WHERE: lambda self: ("where", self._parse_where()),
--
1549:    QUERY_MODIFIER_TOKENS: t.ClassVar = set(QUERY_MODIFIER_PARSERS)
1550-
1551-    SET_PARSERS: t.ClassVar = {
1552-        "GLOBAL": lambda self: self._parse_set_item_assignment("GLOBAL"),

…[2842 chars elided]…
               option = f"{option} {' '.join(keywords)}"
9158-                break
9159-        else:
9160-            if continuations or continuations is None:
9161-                if raise_unmatched:
9162-                    self.raise_error(f"Unknown option {option}")
9163-
9164-                self._retreat(index)
9165-                return None
9166-
9167-        return exp.var(option)
9168-
9169-    def _parse_as_command(self, start: Token) -> exp.Command:
9170-        while self._curr:
[assistant] Dispatch is keyed by token: every `FOR` maps to the `for_` key, so a `FOR JSON` clause can't use a different key without changing that lambda. Before designing the change, I'll check the test helpers' handling of unsupported warnings and get a baseline for the T-SQL tests.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -3; grep -n \"def validate_all\" -A12 tests/dialects/test_dialect.py | head -30; grep -rn \"unsupported_level=ErrorLevel.RAISE\\|assertRaises(UnsupportedError)\" tests/dialects/test_tsql.py | head -3; grep -n \"def _match_pair\" -A8 sqlglot/parser.py; grep -n \"def query_modifiers\" sqlglot/generator.py", "description": "Baseline T-SQL tests and check helper signatures"}
[tool_result] ........ [ 60%]
.....................            [100%]
53 passed, 656 subtests passed in 0.28s
68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
72-        2. `sql` transpiles to everything in `write`
73-
74-        Args:
75-            sql (str): Main SQL expression
76-            read (dict): Mapping of dialect -> SQL
77-            write (dict): Mapping of di
…[97 chars elided]…
bool): quote identifiers in both read and write
80-        """
1933:    def _match_pair(
1934-        self, token_type_a: TokenType, token_type_b: TokenType, advance: bool = True
1935-    ) -> bool:
1936-        if self._curr.token_type == token_type_a and self._next.token_type == token_type_b:
1937-            if advance:
1938-                self._advance(2)
1939-            return True
1940-        return False
1941-
3079:    def query_modifiers(self, expression: exp.Expr, *sqls: str) -> str:
[assistant] Baseline is green (53 tests, 656 subtests). The design:

- **Parse:** `FOR JSON` lands under its own `for_json` key, not `for_`, so the generator can tell the two clauses apart. The `FOR` dispatcher returns `(key, value)` itself. Options reuse the existing `QueryOption` / `XMLKeyValueOption` nodes, so `ROOT('name')` works unchanged.
- **Generate:** the base generator warns and drops `for_json` (same user-visible result as `FOR XML` today). T-SQL overrides it to emit `FOR JSON`.

Making the edits now, starting with the parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = {\n    **dict.fromkeys(\n        (\n            \"AUTO\",\n            \"PATH\",\n            \"INCLUDE_NULL_VALUES\",\n            \"WITHOUT_ARRAY_WRAPPER\",\n        ),\n        tuple(),\n    ),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[620 chars elided]…
arse_csv(lambda: self._parse_for_option(XML_OPTIONS))\n\n        return \"for_\", None\n\n    def _parse_for_option(self, options: parser.OPTIONS_TYPE) -> exp.QueryOption:\n        return self.expression(\n            exp.QueryOption(\n                this=self._parse_var_from_options(options, raise_unmatched=False)\n                or self._parse_xml_key_value_option()\n            )\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "            self.for_modifiers(expression),\n            sep=\"\",", "new_string": "            self.for_modifiers(expression),\n            self.for_json_modifiers(expression),\n            sep=\"\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"\n", "new_string": "        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"\n\n    def for_json_modifiers(self, expression: exp.Expr) -> str:\n        if expression.args.get(\"for_json\"):\n            self.unsupported(\"FOR JSON is not supported.\")\n        return \"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py", "old_string": "    def queryoption_sql(self, expression: exp.QueryOption) -> str:\n        option = self.sql(expression, \"this\")", "new_string": "    def for_json_modifiers(self, expression: exp.Expr) -> str:\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\"\n\n    def queryoption_sql(self, expression: exp.QueryOption) -> str:\n        option = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py has been updated successfully.
[assistant] Edits are in. Next I'll check how existing tests assert unsupported-option warnings so the new test follows the same pattern.
[tool_use Bash] {"command": "grep -rn \"unsupported_level\\|UnsupportedError\" tests/dialects/test_dialect.py | head -8; grep -rn \"unsupported_level=ErrorLevel\" tests/dialects/*.py | head -3", "description": "Check how tests assert unsupported warnings"}
[tool_result] tests/dialects/test_dialect.py:11:    UnsupportedError,
tests/dialects/test_dialect.py:88:                        unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:97:                if write_sql is UnsupportedError:
tests/dialects/test_dialect.py:98:                    with self.assertRaises(UnsupportedError):
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:104:          
…[31 chars elided]…
evel=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:1163:                "mysql": UnsupportedError,
tests/dialects/test_dialect.py:1202:                "mysql": UnsupportedError,
tests/dialects/test_dialect.py:88:                        unsupported_level=ErrorLevel.IGNORE,
tests/dialects/test_dialect.py:99:                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
tests/dialects/test_dialect.py:104:                            unsupported_level=ErrorLevel.IGNORE,
[assistant] `validate_all` with `UnsupportedError` checks the warning under `ErrorLevel.RAISE`. I'll use that for the warning and a separate assertion for the dropped SQL text. Checking the test file imports first.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_tsql.py", "description": "Read test file imports"}
[tool_result] from sqlglot import exp, parse_one
from sqlglot.errors import ParseError, UnsupportedError
from sqlglot.optimizer.annotate_types import annotate_types
from tests.dialects.test_dialect import Validator


class TestTSQL(Validator):
    dialect = "tsql"

    def test_tsql(self):
        self.validate_all(
            "WITH x AS (SELECT 1 AS [1]) SELECT TOP 0 * FROM (SELECT * FROM x UNION SELECT * FROM x) AS _l_0 ORDER BY 1",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_for_json(self):\n      
…[1116 chars elided]…
 t FOR JSON AUTO\",\n            write={\n                \"duckdb\": UnsupportedError,\n                \"mysql\": UnsupportedError,\n                \"oracle\": UnsupportedError,\n            },\n        )\n        self.assertEqual(\n            parse_one(\"SELECT * FROM t FOR JSON AUTO\", read=\"tsql\").sql(\"duckdb\"),\n            \"SELECT * FROM t\",\n        )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125817-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] Running the T-SQL tests and the full suite now that the change is in.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -30", "description": "Run T-SQL dialect tests"}
[tool_result] ......................................................                                                                    [100%]
54 passed, 671 subtests passed in 0.28s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; $P -c \"\nimport sqlglot\nfrom sqlglot import ErrorLevel\nfor q in ['SELECT * FROM t FOR JSON PATH, ROOT(\\'r\\'), INCLUDE_NULL_VALUES', 'SELECT * FROM t FOR XML PATH']:\n    e = sqlglot.parse_one(q, read='tsql')\n    print(e.sql('tsql'))\n    print(repr(sqlglot.transpile(q, read='tsql', write='duckdb', unsupported_level=ErrorLevel.IGNORE)[0]))\n    print(repr(sqlglot.transpile(q, read='tsql', write='oracle', unsupported_level=ErrorLevel.IGNORE)[0]))\n\" ; git diff --stat", "description": "Run full test suite and spot-check outputs"}
[tool_result] ........................... [ 53%]
.................................................................................................................... [ 64%]
.................................. [ 67%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................................
…[114 chars elided]…
assed, 18033 subtests passed in 56.21s
SELECT * FROM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES
'SELECT * FROM t'
'SELECT * FROM t'
SELECT * FROM t FOR XML PATH
'SELECT * FROM t'
'SELECT * FROM t FOR XML PATH'
 sqlglot/generator.py        |  6 ++++++
 sqlglot/generators/tsql.py  |  4 ++++
 sqlglot/parsers/tsql.py     | 39 +++++++++++++++++++++++++++------------
 tests/dialects/test_tsql.py | 45 +++++++++++++++++++++++++++++++++++++++++++++
 4 files changed, 82 insertions(+), 12 deletions(-)
[assistant] The full suite passes: 1108 tests, 18033 subtests. Last, lint and type-check the changed files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; F=\"sqlglot/generator.py sqlglot/generators/tsql.py sqlglot/parsers/tsql.py tests/dialects/test_tsql.py\"; $P -m ruff format --check $F 2>&1 | tail -3; $P -m ruff check $F 2>&1 | tail -3; $P -m mypy sqlglot/parsers/tsql.py sqlglot/generator.py sqlglot/generators/tsql.py 2>&1 | tail -3", "description": "Run ruff format, ruff check, and mypy on changed files"}
[tool_result] error: Failed to format sqlglot/generator.py sqlglot/generators/tsql.py sqlglot/parsers/tsql.py tests/dialects/test_tsql.py: No such file or directory (os error 2)
--> sqlglot/generator.py sqlglot/generators/tsql.py sqlglot/parsers/tsql.py tests/dialects/test_tsql.py:1:1

Found 1 error.
Success: no issues found in 3 source files
[assistant] Ruff reports "No such file" on paths that exist, so I'll check the files individually.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls sqlglot/generators/tsql.py; $P -m ruff --version; $P -m ruff format --check sqlglot/generator.py sqlglot/parsers/tsql.py 2>&1 | tail -3;  $P -m ruff format --check sqlglot/generators/tsql.py tests/dialects/test_tsql.py 2>&1 | tail -3; $P -m ruff check sqlglot/parsers/tsql.py sqlglot/generator.py sqlglot/generators/tsql.py tests/dialects/test_tsql.py 2>&1 | tail -5", "description": "Run ruff per-file to isolate the path error"}
[tool_result] sqlglot/generators/tsql.py
ruff 0.15.6
2 files already formatted
2 files already formatted
All checks passed!
[assistant] `FOR JSON` now parses and round-trips in T-SQL. Other dialects warn and drop the clause. The full suite passes (1108 tests, 18033 subtests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**What changed**

- **`sqlglot/parsers/tsql.py`**: added `JSON_OPTIONS` (`AUTO`, `PATH`, `INCLUDE_NULL_VALUES`, `WITHOUT_ARRAY_WRAPPER`). `_parse_for` now returns a `(key, value)` pair, so `FOR JSON` is stored under its own `for_json` key rather than `for_`. `ROOT` and `ROOT('name')` go through the existing `XMLKeyValueOption` path.
- **`sqlglot/generator.py`**: the base gene
…[351 chars elided]…
und-trips, a pretty-printed case, and the cross-dialect warning and drop for duckdb, mysql, and oracle.

**Things to know**

- The option parsing is as lenient as the existing `FOR XML` parsing, so `FOR JSON` followed by an arbitrary word may parse without error. I kept it consistent with `FOR XML` rather than tightening it.
- Oracle is a pre-existing exception. Its `queryoption_sql` override doesn't drop anything, so `FOR XML PATH` still comes out unchanged in Oracle. My change doesn't alter that, and `FOR JSON` is dropped there correctly. Fixing Oracle's `FOR XML` would be a separate change.
