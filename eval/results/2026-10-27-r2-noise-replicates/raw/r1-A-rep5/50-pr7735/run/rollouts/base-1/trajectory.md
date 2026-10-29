# trajectory base-1

final message:
`UNDROP` now parses and generates for all twelve Snowflake object types, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests), and ruff and mypy are clean. I haven't committed anything.

What changed:
- **Token:** `UNDROP` is a new `TokenType` (`sqlglot/tokenizer_core.py`), mapped in the Snowflake tokenizer, the same way `GET` and `PUT` are.
- **Expression:** a new `exp.Undrop(this, kind)` in `sqlglot/expressions/ddl.py`, where `kind` is the object-type string such as `"DYNAMIC TABLE"`.
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py` matches one of the twelve kinds listed in `UNDROP_KINDS`, then parses the name with the existing table-parts logic. The `IDENTIFIER(...)` form works through the existing Snowflake handling. An unrecognised kind falls back to `exp.Command`, as other statements do.
- **Generator:** `undrop_sql` in `sqlglot/generators/snowflake.py` emits `UNDROP <kind> <name>`.
- **Tests:** a `test_undrop` case in `tests/dialects/test_snowflake.py` covers every kind, the `IDENTIFIER` form, and the `kind` argument.

Two things to know:
- Making `UNDROP` a keyword would have broken `undrop` as an identifier, so I added it to the Snowflake `ID_VAR_TOKENS`. `SELECT undrop FROM undrop` still round-trips.
- Generating `Undrop` for other dialects, e.g. `.sql("duckdb")`, raises `ValueError: Unsupported expression type Undrop`. That follows from the statement being Snowflake-only.

The project guidance asks that dialect tests also run against a real Snowflake or DuckDB instance. I couldn't do that here, so this is verified only by the pure-Python suite.

## events
[tool_use Bash] {"command": "rtk grep -n -i \"undrop\\|UNDROP\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py tests/dialects/test_snowflake.py | head -50; echo ---; rtk grep -n \"UNDROP\\|Undrop\" -r sqlglot tests | head", "description": "Search existing UNDROP references in repo"}
[tool_result] (eval):1: command not found: rtk
---
(eval):1: command not found: rtk
[tool_use Bash] {"command": "rtk grep -n \"def _parse_drop\\|def _parse_create\\|STATEMENT_PARSERS\\|TokenType.DROP\" sqlglot/parser.py sqlglot/dialects/snowflake.py | head -30; rtk grep -n \"class Drop\\|class Create(\" sqlglot/expressions.py", "description": "Locate drop/create parser code and Drop expression"}
[tool_result ERROR] Exit code 127
(eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n -i \"undrop\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py tests/dialects/test_snowflake.py; echo ---; grep -n \"def _parse_drop\\|STATEMENT_PARSERS\\|TokenType.DROP\" sqlglot/parser.py sqlglot/dialects/snowflake.py; grep -n \"class Drop\\|class Create(\" sqlglot/expressions.py; grep -n \"UNDROP\\|Undrop\\|undrop\" sqlglot/*.py sqlglot/dialects/*.py | head", "description": "Search for UNDROP and drop-related parser code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
---
sqlglot/parser.py:1082:    STATEMENT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1094:        TokenType.DROP: lambda self: self._parse_drop(),
sqlglot/parser.py:2278:        if self._match_set(self.STATEMENT_PARSERS):
sqlglot/parser.py:2280:            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
sqlglot/parser.py:2298:    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
sqlglot/parser.py:3401
…[17 chars elided]…
_match_set(self.STATEMENT_PARSERS, advance=False):
sqlglot/parser.py:8709:    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
sqlglot/parser.py:8710:        drop = self._parse_drop() if self._match(TokenType.DROP) else None
sqlglot/parser.py:8719:    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
sqlglot/parser.py:8772:        if self._match_pair(TokenType.DROP, TokenType.DEFAULT):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 1082,1100p sqlglot/parser.py; echo ----; sed -n 2265,2345p sqlglot/parser.py; echo ----; ls sqlglot/expressions* -d; grep -rn \"class Drop(\" sqlglot/expressions/ | head", "description": "Read statement parser and drop parser code"}
[tool_result]     STATEMENT_PARSERS: t.ClassVar = {
        TokenType.ALTER: lambda self: self._parse_alter(),
        TokenType.ANALYZE: lambda self: self._parse_analyze(),
        TokenType.BEGIN: lambda self: self._parse_transaction(),
        TokenType.CACHE: lambda self: self._parse_cache(),
        TokenType.COMMENT: lambda self: self._parse_comment(),
        TokenType.COMMIT: lambda self: self._parse_commit_or_rollback(),
        TokenType.COPY: lambda self: self._parse_copy(),
        TokenType.CREAT
…[3473 chars elided]…
oncurrently=concurrently,
                sync=self._match_text_seq("SYNC"),
                iceberg=iceberg,
            )
        )

    def _parse_exists(self, not_: bool = False) -> bool | None:
        return (
----
ls: -d: No such file or directory
sqlglot/expressions:
__init__.py
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
[tool_use Bash] {"command": "grep -n \"STATEMENT_PARSERS\\|STATEMENT\\|class Parser\\|class Generator\\|class Tokenizer\\|KEYWORDS = \\|COMMANDS\\|CREATABLES\\|IDENTIFIER\\|SHOW\\b\" sqlglot/dialects/snowflake.py | head -60; echo ----; grep -n \"CREATABLES\\|CREATABLE_KIND_MAPPING\" -A12 sqlglot/parser.py sqlglot/dialects/dialect.py | head -60; echo; sed -n 345,375p sqlglot/expressions/ddl.py; grep -n \"def drop_sql\" -A40 sqlglot/generator.py | head -60", "description": "Inspect Snowflake parser hooks and Drop generation"}
[tool_result] 133:    class Tokenizer(tokens.Tokenizer):
140:        KEYWORDS = {
185:        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
----
sqlglot/dialects/dialect.py:247:        klass.INVERSE_CREATABLE_KIND_MAPPING = {
sqlglot/dialects/dialect.py:248:            v: k for k, v in klass.CREATABLE_KIND_MAPPING.items()
sqlglot/dialects/dialect.py-249-        }
sqlglot/dialects/dialect.py-250-
sqlglot/dialects/dialect.py-251-        base = seq_get(bases, 0)
sqlglot/dialects/dialect.py-252-        
…[5837 chars elided]…
ssion.args.get("distinct")
1813-        if (
1814-            distinct is False
1815-            and op_type in (exp.Except, exp.Intersect)
1816-            and not self.EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE
1817-        ):
1818-            self.unsupported(f"{op_name} ALL is not supported")
1819-
1820-        default_distinct = self.dialect.SET_OP_DISTINCT_BY_DEFAULT[op_type]
1821-
1822-        if distinct is None:
1823-            distinct = default_distinct
1824-            if distinct is None:
[tool_use Bash] {"command": "grep -n \"class \\|def _parse_\\|STATEMENT\" sqlglot/dialects/snowflake.py | head -120; echo; grep -rn \"STATEMENT_PARSERS\\[\" sqlglot/dialects | head; grep -rn \"STATEMENT_PARSERS = \" -A3 sqlglot/dialects | head -20", "description": "List Snowflake parser/generator structure and statement overrides"}
[tool_result] 16:class Snowflake(Dialect):
127:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
133:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "ls sqlglot/dialects/snowflake* ; wc -l sqlglot/dialects/snowflake.py; ls sqlglot/dialects/snowflake/ 2>/dev/null; grep -rln \"UNDROP\\|class Snowflake\" sqlglot/ | head", "description": "Locate Snowflake dialect package files"}
[tool_result] sqlglot/dialects/snowflake.py
     187 sqlglot/dialects/snowflake.py
sqlglot/parsers/snowflake.py
sqlglot/dialects/snowflake.py
sqlglot/generators/snowflake.py
[tool_use Bash] {"command": "wc -l sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py; grep -n \"class \\|STATEMENT\\|def _parse_\\|def .*_sql\" sqlglot/parsers/snowflake.py | head -150", "description": "List Snowflake parser and generator methods"}
[tool_result]     1365 sqlglot/parsers/snowflake.py
    1163 sqlglot/generators/snowflake.py
    2528 total
329:class SnowflakeParser(parser.Parser):
758:    STATEMENT_PARSERS = {
759:        **parser.Parser.STATEMENT_PARSERS,
899:    def _parse_directory(self) -> exp.DirectoryStage:
904:    def _parse_describe(self) -> exp.Describe:
930:    def _parse_use(self) -> exp.Use:
954:    def _parse_tag(self) -> exp.Tags:
957:    def _parse_with_constraint(self) -> exp.Expr | None:
982:    def _parse_with_property(s
…[938 chars elided]…
self) -> exp.FileFormatProperty:
1270:    def _parse_credentials_property(self) -> exp.CredentialsProperty:
1273:    def _parse_semantic_view(self) -> exp.SemanticView:
1290:    def _parse_set(self, unset: bool = False, tag: bool = False) -> exp.Set | exp.Command:
1299:    def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
1304:    def _parse_substring(self) -> exp.Substring:
1321:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 758,800p sqlglot/parsers/snowflake.py; echo ...; sed -n 1184,1214p sqlglot/parsers/snowflake.py; echo ...; sed -n 1273,1300p sqlglot/parsers/snowflake.py; echo ...; grep -n \"class Put\\|class Get\\|class Describe\\|class Use\\b\\|class Use(\" -A12 sqlglot/expressions/*.py | head -70", "description": "Read Snowflake statement parsers and related expression defs"}
[tool_result]     STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.GET: lambda self: self._parse_get(),
        TokenType.PUT: lambda self: self._parse_put(),
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    PROPERTY_PARSERS = {
        **parser.Parser.PROPERTY_PARSERS,
        "CREDENTIALS": lambda self: self._parse_credentials_property(),
        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
        "LOCATION": lambda self: self._parse_l
…[7426 chars elided]…
s_msb": False}
sqlglot/expressions/temporal.py:233:class GetExtract(Expression, Func):
sqlglot/expressions/temporal.py-234-    arg_types = {"this": True, "expression": True}
sqlglot/expressions/temporal.py-235-
sqlglot/expressions/temporal.py-236-
sqlglot/expressions/temporal.py-237-class Hour(Expression, Func):
sqlglot/expressions/temporal.py-238-    pass
sqlglot/expressions/temporal.py-239-
sqlglot/expressions/temporal.py-240-
sqlglot/expressions/temporal.py-241-class Minute(Expression, Func):
[tool_use Bash] {"command": "sed -n 133,187p sqlglot/parsers/snowflake.py >/dev/null; grep -n \"class Tokenizer\" -A50 sqlglot/tokenizer*.py sqlglot/tokens*.py 2>/dev/null | grep -n \"COMMANDS\" ; grep -rn \"COMMANDS = \" -A12 sqlglot/tokens*.py sqlglot/*/tokens*.py 2>/dev/null | head -30; grep -rn \"\\\"PUT\\\"\\|\\\"SHOW\\\"\\|\\\"GET\\\"\" sqlglot/dialects/snowflake.py sqlglot/tokens*.py sqlglot/tokenizer*.py 2>/dev/null | head; ls sqlglot | head -80", "description": "Find tokenizer COMMANDS and keyword definitions"}
[tool_result] (eval):1: no matches found: sqlglot/*/tokens*.py
sqlglot/tokens.py:383:        "SHOW": TokenType.SHOW,
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.py:154:            "PUT": TokenType.PUT,
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
[tool_use Bash] {"command": "sed -n 133,190p sqlglot/dialects/snowflake.py; grep -n \"COMMANDS\" -A12 sqlglot/tokens.py | head -30; grep -n \"    SHOW\\|    GET\\|    PUT\\|    COMMAND\" sqlglot/tokens.py", "description": "Read Snowflake tokenizer keywords and token enums"}
[tool_result]     class Tokenizer(tokens.Tokenizer):
        STRING_ESCAPES = ["\\", "'"]
        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
        RAW_STRINGS = ["$$"]
        COMMENTS = ["--", "//", ("/*", "*/")]
        NESTED_COMMENTS = False

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "BYTEINT": TokenType.INT,
            "FILE://": TokenType.URI_START,
            "FILE FORMAT": TokenType.FILE_FORMAT,
            "GET": TokenType.GET,
            "INTEGRATION": TokenType.IN
…[2446 chars elided]…
41-    COMMAND_PREFIX_TOKENS = {TokenType.SEMICOLON, TokenType.BEGIN}
542-
543-    # Handle numeric literals like in hive (3L = BIGINT)
544-    NUMERIC_LITERALS: t.ClassVar[dict[str, str]] = {}
545-
--
576:            commands=self.COMMANDS,
577-            command_prefix_tokens=self.COMMAND_PREFIX_TOKENS,
74:    COMMANDS: t.ClassVar[set[TokenType]]
75:    COMMAND_PREFIX_TOKENS: t.ClassVar[set[TokenType]]
533:    COMMANDS = {
541:    COMMAND_PREFIX_TOKENS = {TokenType.SEMICOLON, TokenType.BEGIN}
[tool_use Bash] {"command": "grep -n \"    GET = \\|    PUT = \\|    SHOW = \\|    UNIQUE\\|    UNNEST = \\|    UPDATE = \\|    UNPIVOT\" sqlglot/tokens.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP TABLE IDENTIFIER(\\'\\\\\\\"_abc\\\\\\\"\\')','UNDROP DYNAMIC TABLE db.s.t']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:150])\n\"", "description": "Check enum definitions and current UNDROP behavior"}
[tool_result] ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 23.
  UNDROP TABLE [4mIDENTIFIER[0m('"_abc"')
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP DYNAMIC [4mTABLE[0m db.s.t
[tool_use Bash] {"command": "grep -n \"\\bGET\\b\\|\\bPUT\\b\\|\\bSHOW\\b\" sqlglot/tokens.py | head; grep -n \"class TokenType\" sqlglot/*.py; grep -n \"def _parse_table_parts\" -A40 sqlglot/parsers/snowflake.py | head -50; grep -n \"IDENTIFIER\" sqlglot/parsers/snowflake.py | head", "description": "Find TokenType enum and IDENTIFIER handling"}
[tool_result] 383:        "SHOW": TokenType.SHOW,
537:        TokenType.SHOW,
sqlglot/tokenizer_core.py:13:class TokenType(IntEnum):
1054:    def _parse_table_parts(
1055-        self,
1056-        schema: bool = False,
1057-        is_db_reference: bool = False,
1058-        wildcard: bool = False,
1059-        fast: bool = False,
1060-    ) -> exp.Table | exp.Dot | None:
1061-        # https://docs.snowflake.com/en/user-guide/querying-stage
1062-        if self._match(TokenType.STRING, advance=False):
1063-
…[939 chars elided]…
86-            table = self.expression(exp.Table(this=table, format=file_format, pattern=pattern))
1087-        else:
1088-            table = super()._parse_table_parts(
1089-                schema=schema,
1090-                is_db_reference=is_db_reference,
1091-                fast=fast,
1092-            )
1093-
1094-        return table
1129:        if self._match_text_seq("IDENTIFIER", "("):
1134:            return self.expression(exp.Anonymous(this="IDENTIFIER", expressions=[identifier]))
[tool_use Bash] {"command": "sed -n 1096,1140p sqlglot/parsers/snowflake.py; grep -n \"    GET\\b\\|    PUT\\b\\|    SHOW\\b\\|    STREAMLIT\\|    TAG\\b\\|    DYNAMIC\\|    ICEBERG\\|    NOTEBOOK\\|    SNAPSHOT\\|    ACCOUNT\\|    VOLUME\\|    TYPE\\b\" sqlglot/tokenizer_core.py", "description": "Read Snowflake table/IDENTIFIER parse logic and token enum entries"}
[tool_result]     def _parse_table(
        self,
        schema: bool = False,
        joins: bool = False,
        alias_tokens: Collection[TokenType] | None = None,
        parse_bracket: bool = False,
        is_db_reference: bool = False,
        parse_partition: bool = False,
        consume_pipe: bool = False,
    ) -> exp.Expr | None:
        table = super()._parse_table(
            schema=schema,
            joins=joins,
            alias_tokens=alias_tokens,
            parse_bracket=parse_bracket,
…[784 chars elided]…
        self._match_r_paren()
            return self.expression(exp.Anonymous(this="IDENTIFIER", expressions=[identifier]))

        return super()._parse_id_var(any_token=any_token, tokens=tokens)

    def _parse_show_snowflake(
        self, this: str, terse: bool = False, iceberg: bool = False
    ) -> exp.Show:
104:    STREAMLIT = auto()
234:    DYNAMIC = auto()
306:    GET = auto()
386:    PUT = auto()
413:    SHOW = auto()
425:    TAG = auto()
432:    TYPE = auto()
445:    VOLUME = auto()
[tool_use Bash] {"command": "grep -n \"    UNNEST\\|    UNPIVOT\\|    UNIQUE\\|    UNKNOWN\\|    UPDATE\\|    UNION\\|    UNCACHE\\|    UNCOMMITTED\" sqlglot/tokenizer_core.py; grep -n \"def _match_text_seq\" -A22 sqlglot/parser.py | head -30; grep -n \"class Drop\" -B3 sqlglot/expressions/ddl.py | head; grep -n \"def drop_sql\\|def get_sql\\|def put_sql\" sqlglot/generator.py sqlglot/generators/snowflake.py", "description": "Check token enum placement and text matching helper"}
[tool_result] 232:    UNKNOWN = auto()
433:    UNCACHE = auto()
434:    UNION = auto()
435:    UNNEST = auto()
436:    UNPIVOT = auto()
437:    UPDATE = auto()
450:    UNIQUE = auto()
1955:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1956-        index = self._index
1957-        string_type = TokenType.STRING
1958-        for text in texts:
1959-            if self._curr.token_type != string_type and self._curr.text.upper() == text:
1960-                self._advance()
1961-      
…[222 chars elided]…
ed(self) -> bool:
1971-        prev = self._prev
1972-        curr = self._curr
1973-        return bool(prev and curr and prev.end + 1 == curr.start)
1974-
1975-    def _find_sql(self, start: Token, end: Token) -> str:
1976-        return self.sql[start.start : end.end + 1]
1977-
342-    }
343-
344-
345:class Drop(Expression):
--
366-        return kind and kind.upper()
367-
368-
369:class DropPrimaryKey(Expression):
sqlglot/generator.py:1784:    def drop_sql(self, expression: exp.Drop) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[assistant] Now the expression class, the parser hook, and the generator method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):\n    arg_types = {}", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):\n    arg_types = {}"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 329, "limit": 30}
[tool_result] 329	class SnowflakeParser(parser.Parser):
330	    IDENTIFY_PIVOT_STRINGS = True
331	    TYPED_LAMBDA_ARGS = True
332	    DEFAULT_SAMPLING_METHOD = "BERNOULLI"
333	    COLON_IS_VARIANT_EXTRACT = True
334	    JSON_EXTRACT_REQUIRES_JSON_EXPRESSION = True
335	
336	    TYPE_TOKENS = {*parser.Parser.TYPE_TOKENS, TokenType.FILE}
337	    STRUCT_TYPE_TOKENS = {*parser.Parser.STRUCT_TYPE_TOKENS, TokenType.FILE}
338	    NESTED_TYPE_TOKENS = {*parser.Parser.NESTED_TYPE_TOKENS, TokenType.FILE}
339	
340	    I
…[58 chars elided]…

342	        TokenType.EXCEPT,
343	        TokenType.INTEGRATION,
344	        TokenType.MATCH_CONDITION,
345	        TokenType.PACKAGE,
346	        TokenType.POLICY,
347	        TokenType.POOL,
348	        TokenType.ROLE,
349	        TokenType.RULE,
350	        TokenType.VOLUME,
351	    }
352	
353	    ALIAS_TOKENS = parser.Parser.ALIAS_TOKENS | {
354	        TokenType.INTEGRATION,
355	        TokenType.PACKAGE,
356	        TokenType.POLICY,
357	        TokenType.POOL,
358	        TokenType.ROLE,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_location_property(self) -> exp.LocationProperty:", "new_string": "    def _parse_undrop(self) -> exp.Undrop | exp.Command:\n        start = self._prev\n\n        kind = next((k for k in self.UNDROP_KINDS if self._match_text_seq(*k.split())), None)\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Undrop(this=self._parse_table_parts(schema=True), kind=kind))\n\n    def _parse_location_property(self) -> exp.LocationProperty:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,", "new_string": "    UNDROP_KINDS = (\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )\n\n    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/generators/snowflake.py | head -80", "description": "List Snowflake generator methods"}
[tool_result] 53:    def _builder(args: list) -> E:
102:    def _flatten_structured_type(expression: exp.Expr) -> exp.Expr:
619:    def sortarray_sql(self, expression: exp.SortArray) -> str:
626:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
677:    def with_properties(self, properties: exp.Properties) -> str:
680:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
686:    def datatype_sql(self, expression: exp.DataType) -> str:
717:    def tonumber_sql(self, e
…[1749 chars elided]…
l(self, expression: exp.Array) -> str:
1082:    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
1093:    def dot_sql(self, expression: exp.Dot) -> str:
1107:    def modelattribute_sql(self, expression: exp.ModelAttribute) -> str:
1110:    def format_sql(self, expression: exp.Format) -> str:
1116:    def splitpart_sql(self, expression: exp.SplitPart) -> str:
1126:    def uniform_sql(self, expression: exp.Uniform) -> str:
1140:    def window_sql(self, expression: exp.Window) -> str:
[tool_use Bash] {"command": "sed -n 875,890p sqlglot/generators/snowflake.py", "description": "View describe_sql for style reference"}
[tool_result]     def describe_sql(self, expression: exp.Describe) -> str:
        kind_value = expression.args.get("kind") or "TABLE"

        properties = expression.args.get("properties")
        if properties:
            qualifier = self.expressions(properties, sep=" ")
            kind = f" {qualifier} {kind_value}"
        else:
            kind = f" {kind_value}"

        this = f" {self.sql(expression, 'this')}"
        expressions = self.expressions(expression, flat=True)
        expressions = f" {expressions}" if expressions else ""
        return f"DESCRIBE{kind}{this}{expressions}"

    def generatedasidentitycolumnconstraint_sql(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "        return f\"DESCRIBE{kind}{this}{expressions}\"\n\n", "new_string": "        return f\"DESCRIBE{kind}{this}{expressions}\"\n\n    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now let me try the parser against the full list of object types, the `IDENTIFIER(...)` form, and a non-UNDROP identifier.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n 'UNDROP TABLE t', 'UNDROP TABLE db.s.t', 'UNDROP SCHEMA s', 'UNDROP DATABASE d', 'UNDROP ACCOUNT a',\n 'UNDROP NOTEBOOK n', 'UNDROP SNAPSHOT sn', 'UNDROP STREAMLIT st', 'UNDROP TAG tg', 'UNDROP TYPE ty',\n 'UNDROP DYNAMIC TABLE dt', 'UNDROP EXTERNAL VOLUME ev', 'UNDROP ICEBERG 
…[6 chars elided]…
it',\n \\\"UNDROP TABLE IDENTIFIER('\\\\\\\"_abc\\\\\\\"')\\\", \\\"UNDROP DATABASE IDENTIFIER('\\\\\\\"_abc\\\\\\\"')\\\",\n 'SELECT undrop FROM t',\n]\nfor s in cases:\n    e = sqlglot.parse_one(s, read='snowflake')\n    out = e.sql('snowflake')\n    print(type(e).__name__, '|', out, '| roundtrip' if out == s else '| DIFF')\n\"", "description": "Round-trip UNDROP statements across object types"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 11, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/dialect.py", line 1124, in parse
    
…[1332 chars elided]…
ATABASE d | roundtrip
Undrop | UNDROP ACCOUNT a | roundtrip
Undrop | UNDROP NOTEBOOK n | roundtrip
Undrop | UNDROP SNAPSHOT sn | roundtrip
Undrop | UNDROP STREAMLIT st | roundtrip
Undrop | UNDROP TAG tg | roundtrip
Undrop | UNDROP TYPE ty | roundtrip
Undrop | UNDROP DYNAMIC TABLE dt | roundtrip
Undrop | UNDROP EXTERNAL VOLUME ev | roundtrip
Undrop | UNDROP ICEBERG TABLE it | roundtrip
Undrop | UNDROP TABLE IDENTIFIER('"_abc"') | roundtrip
Undrop | UNDROP DATABASE IDENTIFIER('"_abc"') | roundtrip
[assistant] The keyword change makes `undrop` unusable as an identifier, so I'll register it as an ID-var token the same way the Snowflake parser does for `VOLUME`/`POOL`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.RULE,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS", "new_string": "        TokenType.RULE,\n        TokenType.UNDROP,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT undrop FROM undrop AS undrop', 'SELECT t.undrop FROM t', 'UNDROP TABLE t']:\n    e = sqlglot.parse_one(s, read='snowflake'); print(e.sql('snowflake'))\nprint(sqlglot.parse_one('SELECT undrop FROM t', read='snowflake').sql('duckdb'))\nprint(sqlglot.parse_one('UNDROP TABLE t', read='snowflake').sql('duckdb'))\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py tests/test_tokens.py tests/test_parser.py tests/test_transpile.py 2>&1 | tail -5", "description": "Verify identifier use of undrop and run related tests"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 6, in <module>
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/core.py", line 1250, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/b
…[601 chars elided]…
(f"Unsupported expression type {expression.__class__.__name__}")
ValueError: Unsupported expression type Undrop
SELECT undrop FROM undrop AS undrop
SELECT t.undrop FROM t
UNDROP TABLE t
SELECT undrop FROM t
............................... [ 15%]
.............................................................. [ 46%]
.......................................................................... [ 83%]
................................                     [100%]
199 passed, 2661 subtests passed in 10.47s
[assistant] Parsing, generation and identifier use all work, and the existing Snowflake/parser/tokenizer/transpile tests pass (199). Now I'll add a dialect test next to the existing Snowflake statement tests.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_snowflake.py | head -40; grep -n \"def test_describe\\|def test_show\\|def test_put\\|def test_ddl\" -A4 tests/dialects/test_snowflake.py | head -30", "description": "Find a suitable test location in Snowflake tests"}
[tool_result] 15:    def test_snowflake(self):
3373:    def test_null_treatment(self):
3414:    def test_staged_files(self):
3462:    def test_sample(self):
3557:    def test_timestamps(self):
3897:    def test_to_date(self):
3989:    def test_trunc(self):
4064:    def test_semi_structured_types(self):
4106:    def test_next_day(self):
4147:    def test_previous_day(self):
4180:    def test_historical_data(self):
4238:    def test_ddl(self):
4408:    def test_user_defined_functions(self):
4433:    def test_st
…[1984 chars elided]…
1-        self.validate_identity(
5212-            "SHOW TERSE DATABASES HISTORY LIKE 'foo' STARTS WITH 'bla' LIMIT 5 FROM 'bob' WITH PRIVILEGES USAGE, MODIFY"
5213-        )
--
5219:    def test_show_file_formats(self):
5220-        self.validate_identity("SHOW FILE FORMATS")
5221-        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN DATABASE db1")
5222-        self.validate_identity("SHOW FILE FORMATS LIKE 'foo' IN SCHEMA db1.schema1")
5223-
--
5228:    def test_show_functions(self):
[tool_use Bash] {"command": "sed -n 5349,5359p tests/dialects/test_snowflake.py", "description": "View drop iceberg test for placement context"}
[tool_result]         )

    def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")

    def test_show_primary_keys(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n\n    def test_show_primary_keys(self):", "new_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRI
…[673 chars elided]…
n        ast = self.validate_identity(\"UNDROP DYNAMIC TABLE dt\")\n        self.assertIsInstance(ast, exp.Undrop)\n        self.assertEqual(ast.args[\"kind\"], \"DYNAMIC TABLE\")\n\n        self.assertEqual(\n            parse_one(\"SELECT undrop FROM undrop\", read=\"snowflake\").sql(\"snowflake\"),\n            \"SELECT undrop FROM undrop\",\n        )\n\n    def test_show_primary_keys(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130149-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_snowflake.py | grep import; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k undrop 2>&1 | tail -15", "description": "Run the new UNDROP test"}
[tool_result] from unittest import mock
from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.parser import logger as parser_logger
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify_columns import quote_identifiers
from tests.dialects.test_dialect import Validator
.                                                         [100%]
1 passed, 95 deselected, 15 subtests passed in 0.12s
[assistant] Test passes. Now the project's full check command from the harness, plus a style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; (ruff --version >/dev/null 2>&1 && ruff check sqlglot tests/dialects/test_snowflake.py && ruff format --check sqlglot tests/dialects/test_snowflake.py) 2>&1 | tail -5", "description": "Run full test suite and lint checks"}
[tool_result] ....................................................................................................... [ 80%]
................ [ 82%]
.................................................................... [ 88%]
.......... [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
...........                                                         [100%]
1121 passed, 18191 subtests passed in 51.40s
All checks passed!
177 files already formatted
[assistant] Full suite passes (1121) and ruff is clean. Checking mypy too, since pre-commit runs it.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/expressions/ddl.py 2>&1 | tail -5) ; git status --short; git diff --stat", "description": "Run mypy on touched modules and show diff stat"}
[tool_result] Success: no issues found in 3 source files
 M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
 sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parsers/snowflake.py     | 26 ++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 30 ++++++++++++++++++++++++++++++
 6 files changed, 65 insertions(+)
[assistant] `UNDROP` now parses and generates for all twelve Snowflake object types, including the `IDENTIFIER(...)` form. The full suite passes (1121 tests), and ruff and mypy are clean. I haven't committed anything.

What changed:
- **Token:** `UNDROP` is a new `TokenType` (`sqlglot/tokenizer_core.py`), mapped in the Snowflake tokenizer, the same way `GET` and `PUT` are.
- **Expression:** a new `exp.Undrop(this, kind)` in `sqlglot/expressions/ddl.py`, where `kind` is the object-type string such as `"DYNAMIC TABLE"`.
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py` matches one of the twelv
…[416 chars elided]…
every kind, the `IDENTIFIER` form, and the `kind` argument.

Two things to know:
- Making `UNDROP` a keyword would have broken `undrop` as an identifier, so I added it to the Snowflake `ID_VAR_TOKENS`. `SELECT undrop FROM undrop` still round-trips.
- Generating `Undrop` for other dialects, e.g. `.sql("duckdb")`, raises `ValueError: Unsupported expression type Undrop`. That follows from the statement being Snowflake-only.

The project guidance asks that dialect tests also run against a real Snowflake or DuckDB instance. I couldn't do that here, so this is verified only by the pure-Python suite.
