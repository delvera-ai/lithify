# trajectory base-1

final message:
`UNDROP` now parses and generates as a structured Snowflake statement for all twelve object types, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests) and ruff is clean.

- **Parsing:** `UNDROP TABLE t`, `UNDROP DYNAMIC TABLE dt`, `UNDROP TABLE db.s.t`, and `UNDROP TABLE IDENTIFIER('"_abc123"')` all produce an `exp.Undrop` node with `this` and `kind`.
- **Generating:** round-trips cleanly through the Snowflake generator.
- **Tests:** added `test_undrop` to `tests/dialects/test_snowflake.py`, covering every kind plus the identifier forms.

Changes by file:
- `sqlglot/tokenizer_core.py`: new `UNDROP` token type.
- `sqlglot/dialects/snowflake.py`: maps the `UNDROP` keyword to that token.
- `sqlglot/expressions/ddl.py`: new `Undrop` expression.
- `sqlglot/parsers/snowflake.py`: statement parser plus the list of supported kinds.
- `sqlglot/generators/snowflake.py`: `undrop_sql`.

Things to be aware of:
- Because `UNDROP` is now a Snowflake keyword, `SELECT undrop FROM t` still works only because I added it to Snowflake's identifier tokens. Other dialects are unaffected since the keyword is Snowflake-only.
- Other dialects raise `ValueError: Unsupported expression type Undrop` when asked to generate it. That matches how other Snowflake-only statements behave; say if you want a fallback.
- Nothing is committed.

## events
[tool_use Bash] {"command": "rtk grep -rn -i \"undrop\\|UNDROP\" sqlglot tests | head -50; rtk grep -n \"ALTER\\|Command\\|STATEMENT_PARSERS\\|_parse_drop\\|def _parse_create\" sqlglot/dialects/snowflake.py | head -60", "description": "Search for UNDROP references and parser hooks"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn -i \"undrop\" sqlglot tests | head -50; echo ---; grep -n \"ALTER\\|STATEMENT_PARSERS\\|_parse_drop\\|UNDROP\\|Command\\|def _parse_create\\|def _parse_show\" sqlglot/dialects/snowflake.py | head -60", "description": "Search for UNDROP references and parser hooks"}
[tool_result] ---
27:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
[tool_use Bash] {"command": "grep -n \"STATEMENT_PARSERS\\|TokenType.DROP\\|_parse_drop\\|class Parser\\|class Generator\\|class Tokenizer\\|KEYWORDS\\|TokenType.COMMAND\\|STATEMENT\" sqlglot/dialects/snowflake.py | head -80; echo ---; grep -n \"STATEMENT_PARSERS\\|def _parse_drop\\|TokenType.DROP:\\|TokenType.DROP\\b\" sqlglot/parser.py | head; echo ---; grep -n \"class Drop\\|class Command\\|class AlterTable\\|class Undrop\" sqlglot/expressions.py; echo; grep -n \"Command\" sqlglot/generator.py | head", "description": "Inspect Snowflake parser and statement hooks"}
[tool_result] 133:    class Tokenizer(tokens.Tokenizer):
140:        KEYWORDS = {
141:            **tokens.Tokenizer.KEYWORDS,
155:            "REMOVE": TokenType.COMMAND,
156:            "RM": TokenType.COMMAND,
175:        KEYWORDS.pop("/*+")
---
1082:    STATEMENT_PARSERS: t.ClassVar = {
1094:        TokenType.DROP: lambda self: self._parse_drop(),
2278:        if self._match_set(self.STATEMENT_PARSERS):
2280:            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
2298:    def _parse_drop(se
…[96 chars elided]…
ENT_PARSERS, advance=False):
8709:    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
8710:        drop = self._parse_drop() if self._match(TokenType.DROP) else None
8719:    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
8772:        if self._match_pair(TokenType.DROP, TokenType.DEFAULT):
---
ugrep: warning: sqlglot/expressions.py: No such file or directory

783:        exp.Command,
4076:    def command_sql(self, expression: exp.Command) -> str:
[tool_use Bash] {"command": "sed -n 1075,1110p sqlglot/dialects/snowflake.py; echo ----; sed -n 2270,2400p sqlglot/parser.py; echo ----; ls sqlglot | head -50", "description": "Read Snowflake statement parsers and parser drop logic"}
[tool_result] ----
        return self.expression(
            exp.WhileBlock(this=self._parse_condition(), body=self._parse_block())
        )

    def _parse_statement(self) -> exp.Expr | None:
        if not self._curr:
            return None

        if self._match_set(self.STATEMENT_PARSERS):
            comments = self._prev_comments
            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
            stmt.add_comments(comments, prepend=True)
            return stmt

        if self._matc
…[4175 chars elided]…
 no_schema_binding = None
        begin = None
        clone = None

        def extend_props(temp_props: exp.Properties | None) -> None:
            nonlocal properties
            if properties and temp_props:
----
__init__.py
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
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP DYNAMIC TABLE t']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, type(e).__name__, str(e)[:200])\n\"; ls sqlglot/parsers sqlglot/generators | head -40; sed -n 1,60p sqlglot/dialects/snowflake.py | head -5; grep -n \"class Command\" -A8 sqlglot/expressions/*.py | head -20", "description": "Check current UNDROP parse behavior and layout"}
[tool_result] ERR UNDROP TABLE t ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR UNDROP SCHEMA s ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
ERR UNDROP DATABASE d ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
  UNDROP DATABASE [4md[0m
ERR UNDROP DYNAMIC TABLE t ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP DYNAMIC [4mTABLE[0m t
sqlglot/generators:
__init__.py

…[516 chars elided]…
ort (
    Dialect,
sqlglot/expressions/ddl.py:373:class Command(Expression):
sqlglot/expressions/ddl.py-374-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/ddl.py-375-
sqlglot/expressions/ddl.py-376-
sqlglot/expressions/ddl.py-377-class Transaction(Expression):
sqlglot/expressions/ddl.py-378-    arg_types = {"this": False, "modes": False, "mark": False}
sqlglot/expressions/ddl.py-379-
sqlglot/expressions/ddl.py-380-
sqlglot/expressions/ddl.py-381-class Commit(Expression):
[tool_use Bash] {"command": "grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/parsers/*.py | head -20; echo ---; grep -n \"def drop_sql\" -A12 sqlglot/generator.py sqlglot/generators/*.py | head -30; echo ---; grep -n \"class Drop\" -A4 sqlglot/expressions/ddl.py; echo ---; grep -n \"UNDROP\\|REMOVE\\|    SHOW\\|    DESCRIBE\\|    TYPE\\b\" sqlglot/tokens.py | head; echo ---; grep -n \"STATEMENT_PARSERS\" -A3 sqlglot/parser.py | head -20; grep -n \"\\\"REMOVE\\\"\\|\\\"RM\\\"\" -B3 -A3 sqlglot/dialects/snowflake.py", "description": "Inspect IDENTIFIER handling, drop generator, token enum"}
[tool_result] sqlglot/parser.py:574:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:617:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:707:        TokenType.IDENTIFIER,
sqlglot/parser.py:800:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
sqlglot/parser.py:841:        TokenType.IDENTIFIER,
sqlglot/parser.py:1479:        TokenType.IDENTIFIER,
sqlglot/parser.py:4651:        while self._match_set(self.IDENTIFIER_TOKENS):
sqlglot/parser.py:4662:            
…[3936 chars elided]…
(self.STATEMENT_PARSERS, advance=False):
3402-            this = self._parse_statement()
3403-        else:
3404-            this = self._parse_table(schema=True)
152-            "POLICY": TokenType.POLICY,
153-            "POOL": TokenType.POOL,
154-            "PUT": TokenType.PUT,
155:            "REMOVE": TokenType.COMMAND,
156:            "RM": TokenType.COMMAND,
157-            "ROLE": TokenType.ROLE,
158-            "RULE": TokenType.RULE,
159-            "SAMPLE": TokenType.TABLE_SAMPLE,
[tool_use Bash] {"command": "grep -n \"    UNCACHE\\|    UNIQUE\\|    UNNEST\\|    UNPIVOT\\|    UNKNOWN\" sqlglot/tokens.py; grep -n \"class Parser\" -A3 sqlglot/dialects/snowflake.py; grep -n \"ID_VAR_TOKENS\\|STATEMENT_PARSERS\\|FUNCTION_PARSERS\" sqlglot/dialects/snowflake.py; grep -n \"class Generator\" sqlglot/dialects/snowflake.py; grep -n \"def tablesample_sql\\|def .*_sql\" sqlglot/dialects/snowflake.py | tail -5; ls tests/dialects | grep snow; grep -n \"IDENTIFIER(\" tests/dialects/test_snowflake.py | head -5", "description": "Locate token enum, Snowflake class sections, and existing tests"}
[tool_result] test_snowflake.py
770:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
4268:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
4269:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
[tool_use Bash] {"command": "grep -rn \"UNCACHE\\b\" sqlglot --include=*.py | head -5; grep -rn \"class Parser\\|class Generator\\|class Tokenizer\" sqlglot/dialects/snowflake.py; grep -n \"^    [A-Za-z]*\\.*\\|^class\\|^    class\" sqlglot/dialects/snowflake.py | sed -n 1,20p; sed -n 4260,4275p tests/dialects/test_snowflake.py; grep -n \"IDENTIFIER\" sqlglot/parsers/*.py | head -3", "description": "Find TokenType enum definition and dialect class layout"}
[tool_result] (eval):1: no matches found: --include=*.py
sqlglot/dialects/snowflake.py:133:    class Tokenizer(tokens.Tokenizer):
5:    Dialect,
6:    NormalizationStrategy,
10:    SnowflakeParser,
16:class Snowflake(Dialect):
17:    # https://docs.snowflake.com/en/sql-reference/identifiers-syntax
18:    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
19:    NULL_ORDERING = "nulls_are_large"
20:    TIME_FORMAT = "'YYYY-MM-DD HH24:MI:SS'"
21:    SUPPORTS_USER_DEFINED_TYPES = False
22:    PREFER_CTE_AL
…[1469 chars elided]…
self.validate_identity("CREATE STREAMLIT x").this.assert_is(exp.Identifier)
        self.validate_identity(
            "CREATE TEMPORARY STAGE stage1 FILE_FORMAT=(TYPE=PARQUET)"
        ).this.assert_is(exp.Table)
sqlglot/parsers/clickhouse.py:554:            self._match_text_seq("IDENTIFIER") and "Identifier"
sqlglot/parsers/mysql.py:532:                if exp.SAFE_IDENTIFIER_RE.match(name := identifier.name)
sqlglot/parsers/snowflake.py:1129:        if self._match_text_seq("IDENTIFIER", "("):
[tool_use Bash] {"command": "grep -rln \"class TokenType\" sqlglot; grep -rn \"STATEMENT_PARSERS\\|ID_VAR_TOKENS\" sqlglot/parsers/snowflake.py | head; sed -n 1120,1145p sqlglot/parsers/snowflake.py; grep -n \"def _parse_drop\\|def _parse_show_snowflake\\|def _parse_alter\" sqlglot/parsers/*.py | head; ls sqlglot/expressions; grep -rn \"class Drop(\" sqlglot/expressions; grep -n \"_parse_table_parts\" sqlglot/parsers/snowflake.py | head -3", "description": "Locate TokenType, Snowflake parser hooks, and expression classes"}
[tool_result] sqlglot/tokenizer_core.py
sqlglot/parsers/snowflake.py:340:    ID_VAR_TOKENS = {
sqlglot/parsers/snowflake.py:341:        *parser.Parser.ID_VAR_TOKENS,
sqlglot/parsers/snowflake.py:379:    COLON_PLACEHOLDER_TOKENS = ID_VAR_TOKENS | {TokenType.NUMBER}
sqlglot/parsers/snowflake.py:758:    STATEMENT_PARSERS = {
sqlglot/parsers/snowflake.py:759:        **parser.Parser.STATEMENT_PARSERS,
            table = table_from_rows

        return table

    def _parse_id_var(
        self,
        any_token:
…[1493 chars elided]…
_snowflake(
sqlglot/parsers/tsql.py:473:    def _parse_alter_table_set(self) -> exp.AlterSet:
__init__.py
__pycache__
aggregate.py
array.py
builders.py
constraints.py
core.py
datatypes.py
ddl.py
dml.py
functions.py
json.py
math.py
properties.py
query.py
string.py
temporal.py
sqlglot/expressions/ddl.py:345:class Drop(Expression):
900:        table = self._parse_table_parts()
1054:    def _parse_table_parts(
1076:                    file_format = self._parse_string() or super()._parse_table_parts(
[tool_use Bash] {"command": "sed -n 750,800p sqlglot/parsers/snowflake.py; echo ----; sed -n 336,345p sqlglot/parsers/snowflake.py; echo ----; grep -n \"SHOW\\|\\\"PUT\\\"\\|\\\"REMOVE\\\"\" sqlglot/dialects/snowflake.py sqlglot/tokenizer_core.py sqlglot/tokens.py 2>/dev/null | head; grep -n \"    UNCACHE\\|    UNIQUE\\|    UNNEST\\|    UNPIVOT\\|    UNION\\b\" sqlglot/tokenizer_core.py; echo ----; grep -n \"STATEMENT_PARSERS\" -A2 sqlglot/parsers/snowflake.py | head; grep -n \"def _parse_drop\\|_parse_drop(\" sqlglot/parsers/snowflake.py | head -3", "description": "View Snowflake statement parsers and token sets"}
[tool_result]             exp.Set(
                tag=self._match_text_seq("TAG"),
                expressions=self._parse_csv(self._parse_id_var),
                unset=True,
            )
        ),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.GET: lambda self: self._parse_get(),
        TokenType.PUT: lambda self: self._parse_put(),
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    PROPERTY_PARSERS = {
        **parser.Parser.PROPERTY_PARS
…[2421 chars elided]…
e.PUT,
sqlglot/dialects/snowflake.py:155:            "REMOVE": TokenType.COMMAND,
sqlglot/dialects/snowflake.py:185:        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
433:    UNCACHE = auto()
434:    UNION = auto()
435:    UNNEST = auto()
436:    UNPIVOT = auto()
450:    UNIQUE = auto()
----
758:    STATEMENT_PARSERS = {
759:        **parser.Parser.STATEMENT_PARSERS,
760-        TokenType.GET: lambda self: self._parse_get(),
761-        TokenType.PUT: lambda self: self._parse_put(),
[tool_use Bash] {"command": "grep -n \"\\\"U\\|\\\"R\\|\\\"T\" sqlglot/dialects/snowflake.py | head; sed -n 133,140p sqlglot/dialects/snowflake.py; grep -n \"PUT\\b\" sqlglot/parsers/snowflake.py | head -3; sed -n 340,378p sqlglot/parsers/snowflake.py | grep -n \"PUT\\|GET\"; sed -n 405,412p sqlglot/tokenizer_core.py; sed -n 432,435p sqlglot/tokenizer_core.py; sed -n 343,345p sqlglot/expressions/ddl.py", "description": "Find keyword placement spots for the new token"}
[tool_result] 39:        "T": "T",  # in TIME_MAPPING we map '"T"' with the double quotes to 'T', and we want to prevent 'T' from being mapped back to '"T"' so that 'AUTO' doesn't become 'AU"T"O'
87:        "TZHTZM": "%z",
89:        "TZH:TZM": "%:z",  # internal representation for ±HH:MM
91:        "TZH": "%-z",  # internal representation ±HH
93:        '"T"': "T",  # remove the optional double quotes around the separator between the date and time
155:            "REMOVE": TokenType.COMMAND,
156:            
…[229 chars elided]…
X_STRINGS = [("x'", "'"), ("X'", "'")]
        RAW_STRINGS = ["$$"]
        COMMENTS = ["--", "//", ("/*", "*/")]
        NESTED_COMMENTS = False

        KEYWORDS = {
761:        TokenType.PUT: lambda self: self._parse_put(),
    RULE = auto()
    SELECT = auto()
    SEMI = auto()
    SEPARATOR = auto()
    SEQUENCE = auto()
    SERDE_PROPERTIES = auto()
    SET = auto()
    SETTINGS = auto()
    TYPE = auto()
    UNCACHE = auto()
    UNION = auto()
    UNNEST = auto()


class Drop(Expression):
[tool_use Bash] {"command": "sed -n 166,176p sqlglot/dialects/snowflake.py; grep -n \"class Generator\" -A3 sqlglot/generators/snowflake.py | head; grep -n \"    def drop_sql\\|    def describe_sql\\|    def put_sql\\|    def get_sql\\|    def show_sql\" sqlglot/generators/snowflake.py; grep -n \"^class Drop\" -B2 sqlglot/expressions/ddl.py; sed -n 369,372p sqlglot/expressions/ddl.py", "description": "Read keyword region and generator method layout"}
[tool_result]             "TAG": TokenType.TAG,
            "TIMESTAMP_TZ": TokenType.TIMESTAMPTZ,
            "TOP": TokenType.TOP,
            "VOLUME": TokenType.VOLUME,
            "WAREHOUSE": TokenType.WAREHOUSE,
            # https://docs.snowflake.com/en/sql-reference/data-types-numeric#float
            # FLOAT is a synonym for DOUBLE in Snowflake
            "FLOAT": TokenType.DOUBLE,
        }
        KEYWORDS.pop("/*+")

840:    def show_sql(self, expression: exp.Show) -> str:
875:    def describe_sql(self, expression: exp.Describe) -> str:
343-
344-
345:class Drop(Expression):
--
367-
368-
369:class DropPrimaryKey(Expression):
class DropPrimaryKey(Expression):
    arg_types = {}
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):\n    arg_types = {}", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):\n    arg_types = {}"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Now the parser: the statement hook, an ID-token guard so `undrop` stays usable as a column name, and the parse method.
[tool_use Bash] {"command": "sed -n 340,378p sqlglot/parsers/snowflake.py | tail -12; grep -n \"_parse_as_command\" sqlglot/parsers/snowflake.py | head -2; grep -n \"    def _parse_put\\|    def _parse_get\" -A3 sqlglot/parsers/snowflake.py | head -8", "description": "Inspect ID_VAR_TOKENS tail and put/get parsers"}
[tool_result]             TokenType.INTEGRATION,
            TokenType.PACKAGE,
            TokenType.POLICY,
            TokenType.POOL,
            TokenType.ROLE,
            TokenType.RULE,
            TokenType.SEMI,
            TokenType.VOLUME,
            TokenType.WINDOW,
        }
    ) - {TokenType.MATCH_CONDITION}

1186:            return self._parse_as_command(self._prev)
1208:            return self._parse_as_command(start)
1184:    def _parse_put(self) -> exp.Put | exp.Command:
1185-        if self._curr.token_type != TokenType.STRING:
1186-            return self._parse_as_command(self._prev)
1187-
--
1196:    def _parse_get(self) -> exp.Expr | None:
1197-        start = self._prev
1198-
[tool_use Bash] {"command": "sed -n 1196,1215p sqlglot/parsers/snowflake.py", "description": "Read the get parser for style reference"}
[tool_result]     def _parse_get(self) -> exp.Expr | None:
        start = self._prev

        # If we detect GET( then we need to parse a function, not a statement
        if self._match(TokenType.L_PAREN):
            self._retreat(self._index - 2)
            return self._parse_expression()

        target = self._parse_location_path()

        # Parse as command if unquoted file path
        if self._curr.token_type == TokenType.URI_START:
            return self._parse_as_command(start)

        return self.expression(
            exp.Get(this=self._parse_string(), target=target, properties=self._parse_properties())
        )

    def _parse_location_property(self) -> exp.LocationProperty:
        self._match(TokenType.EQ)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "            TokenType.SEMI,\n            TokenType.VOLUME,\n            TokenType.WINDOW,\n        }\n    ) - {TokenType.MATCH_CONDITION}", "new_string": "            TokenType.SEMI,\n            TokenType.UNDROP,\n            TokenType.VOLUME,\n            TokenType.WINDOW,\n        }\n    ) - {TokenType.MATCH_CONDITION}"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_location_property(self) -> exp.LocationProperty:", "new_string": "    def _parse_undrop(self) -> exp.Undrop | exp.Command:\n        start = self._prev\n        kind = next((k for k in self.UNDR
…[5 chars elided]…
NDS if self._match_text_seq(*k.split())), None)\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Undrop(\n                this=self._parse_table_parts(schema=True, is_db_reference=kind == \"DATABASE\"),\n                kind=kind,\n            )\n        )\n\n    def _parse_location_property(self) -> exp.LocationProperty:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,", "new_string": "    UNDROP_KINDS = (\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )\n\n    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "                this=self._parse_table_parts(schema=True, is_db_reference=kind == \"DATABASE\"),", "new_string": "                this=self._parse_table_parts(schema=True, is_db_reference=kind == \"SCHEMA\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    UNDROP_KINDS = (", "new_string": "    UNDROP_KINDS: t.ClassVar[tuple[str, ...]] = ("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "offset": 872, "limit": 12}
[tool_result] 872	        on = f" ON ({self.expressions(expression, flat=True)})" if expression.expressions else ""
873	        return f"WITH ROW ACCESS POLICY {self.sql(expression, 'this')}{on}"
874	
875	    def describe_sql(self, expression: exp.Describe) -> str:
876	        kind_value = expression.args.get("kind") or "TABLE"
877	
878	        properties = expression.args.get("properties")
879	        if properties:
880	            qualifier = self.expressions(properties, sep=" ")
881	            kind = f" {qualifier} {kind_value}"
882	        else:
883	            kind = f" {kind_value}"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "    def describe_sql(self, expression: exp.Describe) -> str:\n        kind_value = expression.args.get(\"kind\") or \"TABLE\"", "new_string": "    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n    def describe_sql(self, expression: exp.Describe) -> str:\n        kind_value = expression.args.get(\"kind\") or \"TABLE\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now a quick check of parsing, generation, and round-trips before writing tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA db.s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT st','UNDROP TAG tg','UNDROP TYPE ty','UNDROP DYNAMIC TABLE dt','UNDROP EXTERNAL VOLUME e
…[145 chars elided]…
in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake')\n        print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:150])\nprint(repr(sqlglot.parse_one('UNDROP TABLE t', read='snowflake')))\nprint(sqlglot.transpile('UNDROP TABLE t', read='snowflake', write='duckdb'))\n\"", "description": "Smoke-test UNDROP parsing and generation"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA db.s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT st','UNDROP TAG tg','UNDROP TYPE ty','UNDROP DYNAMIC TABLE dt','UNDROP EXTERNAL VOLUME ev','UNDROP ICEBERG TABLE it'
…[117 chars elided]…
in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake')\n        print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:150])\nprint(repr(sqlglot.parse_one('UNDROP TABLE t', read='snowflake')))\nprint(sqlglot.transpile('UNDROP TABLE t', read='snowflake', write='duckdb'))\n\"", "description": "Smoke-test UNDROP parsing and generation"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 10, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/__init__.py", line 195, in transpile
    write.generate(expression, copy=False, **opts) if expression else ""
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/di
…[839 chars elided]…
 UNDROP NOTEBOOK n
Undrop | UNDROP SNAPSHOT s
Undrop | UNDROP STREAMLIT st
Undrop | UNDROP TAG tg
Undrop | UNDROP TYPE ty
Undrop | UNDROP DYNAMIC TABLE dt
Undrop | UNDROP EXTERNAL VOLUME ev
Undrop | UNDROP ICEBERG TABLE it
Undrop | UNDROP TABLE IDENTIFIER('"_abc123"')
Undrop | UNDROP SCHEMA IDENTIFIER($foo)
ERR SELECT undrop FROM t Invalid expression / Unexpected token. Line 1, Col: 13.
  SELECT [4mundrop[0m FROM t
Undrop(
  this=Table(
    this=Identifier(this=t, quoted=False)),
  kind=TABLE)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT put FROM t','SELECT volume FROM t','SELECT undrop FROM t','SELECT a AS undrop FROM t','SELECT t.undrop FROM t']:\n    try: print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:80].replace(chr(10),' '))\n\"; grep -rn \"ID_VAR_TOKENS\" sqlglot/parsers/snowflake.py | head", "description": "Compare identifier handling for similar keywords"}
[tool_result] SELECT put FROM t
SELECT volume FROM t
ERR SELECT undrop FROM t Invalid expression / Unexpected token. Line 1, Col: 13.   SELECT [4mundrop[0m 
SELECT a AS undrop FROM t
SELECT t.undrop FROM t
sqlglot/parsers/snowflake.py:340:    ID_VAR_TOKENS = {
sqlglot/parsers/snowflake.py:341:        *parser.Parser.ID_VAR_TOKENS,
sqlglot/parsers/snowflake.py:380:    COLON_PLACEHOLDER_TOKENS = ID_VAR_TOKENS | {TokenType.NUMBER}
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.dialects.snowflake import Snowflake\nP = Snowflake.parser_class\nprint(sqlglot.parse_one('SELECT volume FROM t', read='snowflake').sql('snowflake'))\nfor s in ['SELECT undrop','SELECT undrop, 1','SELECT (undrop)','WITH c AS (SELECT 1 AS undrop) SELECT undrop FROM c']:\n    try: print(sqlglot.parse_one(s, read='snowflake').sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:60].replace(chr(10),' '))\nprint(any(TT for TT in P.ID_VAR_TOKENS if TT.name=='UNDROP'))\n\"; grep -rn \"RESERVED_TOKENS\\|_parse_primary(self\" sqlglot/parser.py sqlglot/parsers/snowflake.py | head -5", "description": "Narrow down where bare undrop identifier fails"}
[tool_result] SELECT volume FROM t
ERR SELECT undrop Invalid expression / Unexpected token. Line 1, Col: 13.   SE
ERR SELECT undrop, 1 Invalid expression / Unexpected token. Line 1, Col: 13.   SE
ERR SELECT (undrop) Required keyword: 'this' missing for <class 'sqlglot.express
ERR WITH c AS (SELECT 1 AS undrop) SELECT undrop FROM c Invalid expression / Unexpected token. Line 1, Col: 44.   WI
False
sqlglot/parser.py:614:    RESERVED_TOKENS: t.ClassVar = {
sqlglot/parser.py:6844:    def _parse_primary(self) -> exp.Expr | None:
sqlglot/parser.py:6952:            if token_type in self.RESERVED_TOKENS:
sqlglot/parser.py:8530:        if self._curr and (ignore_reserved or self._curr.token_type not in self.RESERVED_TOKENS):
sqlglot/parser.py:9495:        op = self._parse_var(any_token=True, tokens=self.RESERVED_TOKENS)
[tool_use Bash] {"command": "grep -n \"UNDROP\" sqlglot/parsers/snowflake.py; sed -n 376,384p sqlglot/parsers/snowflake.py; grep -n \"ID_VAR_TOKENS\" sqlglot/parser.py | head -3", "description": "Locate UNDROP entries in Snowflake parser"}
[tool_result] 374:            TokenType.UNDROP,
759:    UNDROP_KINDS: t.ClassVar[tuple[str, ...]] = (
779:        TokenType.UNDROP: lambda self: self._parse_undrop(),
1233:        kind = next((k for k in self.UNDROP_KINDS if self._match_text_seq(*k.split())), None)
            TokenType.WINDOW,
        }
    ) - {TokenType.MATCH_CONDITION}

    COLON_PLACEHOLDER_TOKENS = ID_VAR_TOKENS | {TokenType.NUMBER}

    NO_PAREN_FUNCTIONS = {
        **parser.Parser.NO_PAREN_FUNCTIONS,
        TokenType.LOCALTIME: exp.Localtime,
666:    ID_VAR_TOKENS: t.ClassVar[set] = {
772:    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.dialects.snowflake import Snowflake\nfrom sqlglot.tokens import TokenType\nfrom sqlglot.parsers.snowflake import SnowflakeParser\nprint(Snowflake.parser_class, SnowflakeParser.ID_VAR_TOKENS is not None, TokenType.UNDROP in SnowflakeParser.ID_VAR_TOKENS, TokenType.UNDROP in SnowflakeParser.RESERVED_TOKENS, TokenType.UNDROP in SnowflakeParser.TABLE_ALIAS_TOKENS)\nimport sqlglot.parser as p; print(p.Parser.ID_VAR_TOKENS is SnowflakeParser.ID_VAR_TOKENS)\nprint(TokenType.UNDROP in SnowflakeParser.STATEMENT_PARSERS)\n\"", "description": "Verify token membership in Snowflake parser sets"}
[tool_result] <class 'sqlglot.parsers.snowflake.SnowflakeParser'> True False False True
False
True
[tool_use Bash] {"command": "sed -n 338,378p sqlglot/parsers/snowflake.py", "description": "View full Snowflake ID_VAR_TOKENS definition"}
[tool_result]     NESTED_TYPE_TOKENS = {*parser.Parser.NESTED_TYPE_TOKENS, TokenType.FILE}

    ID_VAR_TOKENS = {
        *parser.Parser.ID_VAR_TOKENS,
        TokenType.EXCEPT,
        TokenType.INTEGRATION,
        TokenType.MATCH_CONDITION,
        TokenType.PACKAGE,
        TokenType.POLICY,
        TokenType.POOL,
        TokenType.ROLE,
        TokenType.RULE,
        TokenType.VOLUME,
    }

    ALIAS_TOKENS = parser.Parser.ALIAS_TOKENS | {
        TokenType.INTEGRATION,
        TokenType.PACKAGE,
    
…[78 chars elided]…
TokenType.RULE,
        TokenType.VOLUME,
    }

    TABLE_ALIAS_TOKENS = (
        parser.Parser.TABLE_ALIAS_TOKENS
        | {
            TokenType.ANTI,
            TokenType.INTEGRATION,
            TokenType.PACKAGE,
            TokenType.POLICY,
            TokenType.POOL,
            TokenType.ROLE,
            TokenType.RULE,
            TokenType.SEMI,
            TokenType.UNDROP,
            TokenType.VOLUME,
            TokenType.WINDOW,
        }
    ) - {TokenType.MATCH_CONDITION}
[assistant] My edit landed in `TABLE_ALIAS_TOKENS` rather than `ID_VAR_TOKENS`. Moving it to the ID set so `undrop` still works as a column name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "            TokenType.SEMI,\n            TokenType.UNDROP,\n            TokenType.VOLUME,\n            TokenType.WINDOW,\n        }\n    ) - {TokenType.MATCH_CONDITION}", "new_string": "            TokenType.SEMI,\n            TokenType.VOLUME,\n            TokenType.WINDOW,\n        }\n    ) - {TokenType.MATCH_CONDITION}"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.RULE,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS", "new_string": "        TokenType.RULE,\n        TokenType.UNDROP,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now the tests. I'll add a dedicated test method to the Snowflake test file.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_snowflake.py | sed -n 1,400p | grep -n \"ddl\\|show\\|put\\|describe\\|get\\|drop\" ", "description": "Find test method names for insertion point"}
[tool_result] 12:4238:    def test_ddl(self):
19:4703:    def test_describe(self):
25:5204:    def test_show_users(self):
26:5209:    def test_show_databases(self):
27:5219:    def test_show_file_formats(self):
28:5228:    def test_show_functions(self):
29:5236:    def test_show_procedures(self):
30:5245:    def test_show_stages(self):
31:5254:    def test_show_warehouses(self):
32:5261:    def test_show_schemas(self):
33:5271:    def test_show_objects(self):
34:5285:    def test_show_columns(self):
35:5296:    def test_show_tables(self):
37:5351:    def test_drop_iceberg_table(self):
38:5359:    def test_show_primary_keys(self):
39:5378:    def test_show_views(self):
40:5394:    def test_show_unique_keys(self):
41:5413:    def test_show_imported_keys(self):
42:5432:    def test_show_sequences(self):
49:5601:    def test_put_to_stage(self):
50:5641:    def test_get_from_stage(self):
66:6038:    def test_get_extract(self):
75:6246:    def test_get_bit(self):
[tool_use Bash] {"command": "sed -n 5349,5359p tests/dialects/test_snowflake.py", "description": "View iceberg drop test as insertion anchor"}
[tool_result]         )

    def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")

    def test_show_primary_keys(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n\n    def test_show_primary_keys(self):", "new_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRI
…[588 chars elided]…
ssertEqual(ast.args[\"kind\"], kind)\n\n        self.validate_identity(\"UNDROP TABLE db.s.t\")\n        self.validate_identity(\"UNDROP SCHEMA db.s\")\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('\\\"_abc123\\\"')\")\n        self.validate_identity(\"UNDROP SCHEMA IDENTIFIER($foo)\")\n        self.validate_identity(\"SELECT undrop FROM t\")\n\n    def test_show_primary_keys(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082049-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k undrop 2>&1 | tail -30; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run UNDROP test and full pytest suite"}
[tool_result] .                                                            [100%]
1 passed, 95 deselected, 12 subtests passed in 0.15s
............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
...................................................................................................................................
…[219 chars elided]…
.................. [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 55.88s
[assistant] Full suite passes (1121 tests). Running the linter on the changed files too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot tests/dialects/test_snowflake.py) 2>&1 | tail -8; git status --short; git diff --stat", "description": "Run ruff lint/format check and show diff stats"}
[tool_result] ruff 0.15.6
All checks passed!
177 files already formatted
 M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
 sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parsers/snowflake.py     | 30 ++++++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 26 ++++++++++++++++++++++++++
 6 files changed, 65 insertions(+)
[assistant] `UNDROP` now parses and generates as a structured Snowflake statement for all twelve object types, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests) and ruff is clean.

- **Parsing:** `UNDROP TABLE t`, `UNDROP DYNAMIC TABLE dt`, `UNDROP TABLE db.s.t`, and `UNDROP TABLE IDENTIFIER('"_abc123"')` all produce an `exp.Undrop` node with `this` and `kind`.
- **Generating:** round-trips cleanly through the Snowflake generator.
- **Tests:** added `test_undrop` to `tests/dialects/test_snowflake.py`, covering every kind plus the identifier forms.

Changes by file:
- `sqlglot/tokeni
…[146 chars elided]…
 new `Undrop` expression.
- `sqlglot/parsers/snowflake.py`: statement parser plus the list of supported kinds.
- `sqlglot/generators/snowflake.py`: `undrop_sql`.

Things to be aware of:
- Because `UNDROP` is now a Snowflake keyword, `SELECT undrop FROM t` still works only because I added it to Snowflake's identifier tokens. Other dialects are unaffected since the keyword is Snowflake-only.
- Other dialects raise `ValueError: Unsupported expression type Undrop` when asked to generate it. That matches how other Snowflake-only statements behave; say if you want a fallback.
- Nothing is committed.
