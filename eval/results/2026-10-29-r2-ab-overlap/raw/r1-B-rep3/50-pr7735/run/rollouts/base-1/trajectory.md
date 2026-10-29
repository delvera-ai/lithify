# trajectory base-1

final message:
`UNDROP` now parses and generates for all twelve Snowflake object kinds, including the `IDENTIFIER('"<id>"')` form. The full suite passes (1121 tests, 18188 subtests), and ruff lint and format are clean. I haven't committed anything.

What changed:

- **Tokenizer:** a new `TokenType.UNDROP` in `sqlglot/tokenizer_core.py`, mapped from the `UNDROP` keyword in the Snowflake tokenizer. It is also added to the parser's `ID_VAR_TOKENS`, so `SELECT undrop FROM t` still parses as a column.
- **Expression:** `exp.Undrop(this, kind)` in `sqlglot/expressions/ddl.py`, next to `Drop`.
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py`, registered in Snowflake's `STATEMENT_PARSERS` the same way `GET`/`PUT` are. It matches the multi-word kinds (`DYNAMIC TABLE`, `EXTERNAL VOLUME`, `ICEBERG TABLE`) and reads the name with the same table-parts parsing `DROP` uses. An unrecognised kind falls back to `exp.Command`, as `DROP` does.
- **Generator:** `undrop_sql` in the base `sqlglot/generator.py`, placed beside `drop_sql`. I put it there rather than in the Snowflake generator because `Put`/`Get` do the same.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` round-trips each kind, both `IDENTIFIER` forms, and the `undrop` identifier case.

Not run: the mypyc build (`make testc`). Adding an enum member could matter there, so it's worth running before merging.

## events
[tool_use Bash] {"command": "git status --short && grep -rn -i \"undrop\\|UNDROP\" sqlglot/ tests/ | head -30; grep -n \"STATEMENT_PARSERS\\|def _parse_drop\\|\\\"DROP\\\"\\|TokenType.DROP\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -30", "description": "Check repo state and find UNDROP references"}
[tool_result] ok13 matches in 1 files:

sqlglot/parser.py:1082:STATEMENT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1094:TokenType.DROP: lambda self: self._parse_drop(),
sqlglot/parser.py:1442:"DROP": lambda self: self._parse_alter_table_drop(),
sqlglot/parser.py:1734:"DROP": lambda self: self._parse_analyze_histogram(),
sqlglot/parser.py:2278:if self._match_set(self.STATEMENT_PARSERS):
sqlglot/parser.py:2280:stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
sqlglot/parser.py:2298:def _parse_drop(self
…[62 chars elided]…
ser.py:3401:if self._match_set(self.STATEMENT_PARSERS, advance=False):
sqlglot/parser.py:8709:def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
sqlglot/parser.py:8710:drop = self._parse_drop() if self._match(TokenType.DROP) else None
sqlglot/parser.py:8719:def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartit...
sqlglot/parser.py:8772:if self._match_pair(TokenType.DROP, TokenType.DEFAULT):
sqlglot/parser.py:8778:if self._match_text_seq("DROP", "NOT", "NULL"):
[tool_use Bash] {"command": "sed -n 2298,2345p sqlglot/parser.py; sed -n 1082,1100p sqlglot/parser.py; grep -n \"UNDROP\\|Undrop\" -r sqlglot tests | head; grep -n \"STATEMENT_PARSERS\\|_parse_drop\\|class Parser\" sqlglot/dialects/snowflake.py | head", "description": "Read DROP parser and statement parsers"}
[tool_result]     def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
            return self._parse_as_command(start)

        concurrently = self._match_text_seq("
…[2110 chars elided]…
elf: self._parse_describe(),
        TokenType.DROP: lambda self: self._parse_drop(),
        TokenType.GRANT: lambda self: self._parse_grant(),
        TokenType.REVOKE: lambda self: self._parse_revoke(),
        TokenType.INSERT: lambda self: self._parse_insert(),
        TokenType.KILL: lambda self: self._parse_kill(),
        TokenType.LOAD: lambda self: self._parse_load(),
        TokenType.MERGE: lambda self: self._parse_merge(),
0 matches for 'STATEMENT_PARSERS\|_parse_drop\|class Parser'
[tool_use Bash] {"command": "grep -n \"class Parser\\|class Tokenizer\\|class Generator\\|STATEMENT_PARSERS\\|COMMAND\\|KEYWORDS = {\\|IDENTIFIER\\|\\\"SHOW\\\"\\|TokenType.SHOW\\|_parse_show\\|def _parse_drop\\|def _parse_create\\|CREATABLES\\|CREATABLE_KIND_MAPPING\" sqlglot/dialects/snowflake.py | head -60; grep -n \"CREATABLES\\|CREATABLE_KIND_MAPPING\" sqlglot/parser.py sqlglot/dialects/dialect.py | head; grep -n \"DYNAMIC\\|EXTERNAL VOLUME\\|ICEBERG\\|NOTEBOOK\\|STREAMLIT\\|SNAPSHOT\" sqlglot/dialects/snowflake.py sqlglot/tokens.py sqlglot/parser.py | head -30", "description": "Survey Snowflake dialect parser structure"}
[tool_result] rg: regex parse error:
    (?:class Parser|class Tokenizer|class Generator|STATEMENT_PARSERS|COMMAND|KEYWORDS = {|IDENTIFIER|"SHOW"|TokenType.SHOW|_parse_show|def _parse_drop|def _parse_create|CREATABLES|CREATABLE_KIND_MAPPING)
                                                                                          ^
error: repetition quantifier expects a valid decimal
0 matches for 'class Parser\|class Tokenizer\|class Generator\|STATEMENT_PARSERS\|COMMAND\|KEYWORDS = {\|IDENTIFIER\|"SHOW"\|To
…[1024 chars elided]…
n(exp.IcebergProperty()),
sqlglot/parser.py:2302:iceberg = self._match_text_seq("ICEBERG")
sqlglot/parser.py:4916:if self._match(TokenType.TIMESTAMP_SNAPSHOT):
sqlglot/parser.py:4918:elif self._match(TokenType.VERSION_SNAPSHOT):
sqlglot/parser.py:7575:if not self._match(TokenType.TIMESTAMP_SNAPSHOT):
sqlglot/parser.py:8898:iceberg = self._match_text_seq("ICEBERG")
sqlglot/tokens.py:529:"FOR VERSION": TokenType.VERSION_SNAPSHOT,
sqlglot/tokens.py:530:"FOR TIMESTAMP": TokenType.TIMESTAMP_SNAPSHOT,
[tool_use Bash] {"command": "rtk proxy grep -n \"class Parser\\|class Tokenizer\\|class Generator\\|STATEMENT_PARSERS\\|COMMAND\\|KEYWORDS = {\\|IDENTIFIER\\|SHOW\\|_parse_drop\\|_parse_create\\|DROP\" sqlglot/dialects/snowflake.py | head -80; rtk proxy grep -n \"UNDROP\\|class Drop\\|class Command\\|class Use(\" sqlglot/expressions.py sqlglot/tokens.py | head", "description": "Locate Snowflake parser sections"}
[tool_result] 133:    class Tokenizer(tokens.Tokenizer):
140:        KEYWORDS = {
155:            "REMOVE": TokenType.COMMAND,
156:            "RM": TokenType.COMMAND,
185:        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
grep: sqlglot/expressions.py: No such file or directory
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "offset": 125, "limit": 140}
[tool_result] 125	        )
126	
127	    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
128	        SINGLE_TOKENS = jsonpath.JSONPathTokenizer.SINGLE_TOKENS.copy()
129	        SINGLE_TOKENS.pop("$")
130	
131	    Parser = SnowflakeParser
132	
133	    class Tokenizer(tokens.Tokenizer):
134	        STRING_ESCAPES = ["\\", "'"]
135	        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
136	        RAW_STRINGS = ["$$"]
137	        COMMENTS = ["--", "//", ("/*", "*/")]
138	        NESTED_COMMENTS = False
139	
140	 
…[1533 chars elided]…

172	            # FLOAT is a synonym for DOUBLE in Snowflake
173	            "FLOAT": TokenType.DOUBLE,
174	        }
175	        KEYWORDS.pop("/*+")
176	
177	        SINGLE_TOKENS = {
178	            **tokens.Tokenizer.SINGLE_TOKENS,
179	            "$": TokenType.PARAMETER,
180	            "!": TokenType.EXCLAMATION,
181	        }
182	
183	        VAR_SINGLE_TOKENS = {"$"}
184	
185	        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
186	
187	    Generator = SnowflakeGenerator
188	
[tool_use Bash] {"command": "rtk proxy grep -n \"class Drop\\|class Command\\|class Undrop\\|class Use\\b\" sqlglot/expressions/*.py | head; rtk proxy grep -n \"\\\"UNDROP\\\"\\|\\\"UNDO\\\"\\|\\\"UNPIVOT\\\"\" sqlglot/tokens.py | head; rtk proxy grep -n \"class Drop\" -A 25 sqlglot/expressions/*.py | head -40", "description": "Read Snowflake tokenizer and find Drop expression"}
[tool_result] sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py:369:class DropPrimaryKey(Expression):
sqlglot/expressions/ddl.py:373:class Command(Expression):
sqlglot/expressions/ddl.py:418:class Use(Expression):
sqlglot/expressions/query.py:1949:class DropPartition(Expression):
401:        "UNPIVOT": TokenType.UNPIVOT,
sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py-346-    arg_types = {
sqlglot/expressions/ddl.py-347-        "this": False,
s
…[1455 chars elided]…
lot/expressions/ddl.py-375-
sqlglot/expressions/ddl.py-376-
sqlglot/expressions/ddl.py-377-class Transaction(Expression):
sqlglot/expressions/ddl.py-378-    arg_types = {"this": False, "modes": False, "mark": False}
sqlglot/expressions/ddl.py-379-
sqlglot/expressions/ddl.py-380-
sqlglot/expressions/ddl.py-381-class Commit(Expression):
sqlglot/expressions/ddl.py-382-    arg_types = {"chain": False, "this": False, "durability": False}
sqlglot/expressions/ddl.py-383-
sqlglot/expressions/ddl.py-384-
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP DYNAMIC TABLE db.s.t','UNDROP SCHEMA s', 'UNDROP DATABASE d']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, e)\n\"; rtk proxy grep -n \"COMMAND\" sqlglot/parser.py | head -20; rtk proxy grep -n \"def _parse_statement\" -A 25 sqlglot/parser.py | head -40", "description": "Reproduce current UNDROP behavior and inspect statement parsing"}
[tool_result] ERR UNDROP TABLE t Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR UNDROP DYNAMIC TABLE db.s.t Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP DYNAMIC [4mTABLE[0m db.s.t
ERR UNDROP SCHEMA s Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
ERR UNDROP DATABASE d Invalid expression / Unexpected token. Line 1, Col: 17.
  UNDROP DATABASE [4md[0m
681:        TokenType.COMMAND,
828:        TokenType.COMMAND,
1786
…[880 chars elided]…
on = self._parse_expression()
2291-        expression = self._parse_set_operations(expression) if expression else self._parse_select()
2292-
2293-        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
2294-            expression = self._parse_pipe_syntax_query(expression)
2295-
2296-        return self._parse_query_modifiers(expression)
2297-
2298-    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2299-        start = self._prev
[tool_use Bash] {"command": "rtk proxy grep -n \"TokenType.PUT\\|TokenType.GET\\|TokenType.STAGE\\|\\\"IDENTIFIER\\\"\\|IDENTIFIER\" sqlglot/parser.py sqlglot/dialects/snowflake.py sqlglot/tokens.py | head -30; rtk proxy grep -n \"def drop_sql\" -A 40 sqlglot/generator.py | head -60; rtk proxy grep -n \"class Drop\\|class Put\\|class Get\" sqlglot/expressions/*.py; rtk proxy grep -n \"\\bPUT\\b\\|\\bSTREAMLIT\\b\" sqlglot/tokens.py sqlglot/expressions/*.py | head", "description": "Inspect IDENTIFIER handling and Drop generation"}
[tool_result] sqlglot/parser.py:574:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:617:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:630:        TokenType.STAGE,
sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:707:        TokenType.IDENTIFIER,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:800:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
sqlglot/parser.py:839:        TokenType.GET,
sqlglot/parser.py:841:        TokenT
…[4010 chars elided]…
pressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py:369:class DropPrimaryKey(Expression):
sqlglot/expressions/functions.py:444:class GetIgnoreCase(Expression, Func):
sqlglot/expressions/math.py:271:class Getbit(Expression, Func):
sqlglot/expressions/query.py:935:class Put(Expression):
sqlglot/expressions/query.py:939:class Get(Expression):
sqlglot/expressions/query.py:1949:class DropPartition(Expression):
sqlglot/expressions/temporal.py:233:class GetExtract(Expression, Func):
[tool_use Bash] {"command": "rtk proxy grep -n \"TokenType.PUT\\b\\|TokenType.GET\\b\\|exp.Put\\|exp.Get\\b\\|_parse_put\\|_parse_get\" sqlglot/parser.py sqlglot/dialects/*.py sqlglot/generator.py | head; P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['DROP TABLE IDENTIFIER(\\'\\\"abc\\\"\\')','DROP TABLE IDENTIFIER(\\'db.s.t\\')', 'SELECT undrop FROM t', 'UNDROP TABLE IDENTIFIER(\\'\\\"x\\\"\\')']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', s, str(e)[:200])\n\"", "description": "Check PUT/GET handling and IDENTIFIER parsing"}
[tool_result] sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:839:        TokenType.GET,
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.py:154:            "PUT": TokenType.PUT,
sqlglot/generator.py:192:        exp.Get: lambda self, e: self.get_put_sql(e),
sqlglot/generator.py:239:        exp.Put: lambda self, e: self.get_put_sql(e),
sqlglot/generator.py:5994:    def get_put_sql(self, expression: exp.Put
…[543 chars elided]…
.t', is_string=True)])),
  kind=TABLE,
  temporary=False,
  materialized=False,
  cascade=False,
  restrict=False,
  constraints=False,
  purge=False,
  concurrently=False,
  sync=False,
  iceberg=False)
Select(
  expressions=[
    Column(
      this=Identifier(this=undrop, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))))
ERR UNDROP TABLE IDENTIFIER('"x"') Invalid expression / Unexpected token. Line 1, Col: 23.
  UNDROP TABLE [4mIDENTIFIER[0m('"x"')
[tool_use Bash] {"command": "rtk proxy grep -n \"class SnowflakeParser\" -A 6 sqlglot/dialects/snowflake.py; rtk proxy grep -n \"STATEMENT_PARSERS\\|_parse_statement\" sqlglot/dialects/*.py | head; rtk proxy grep -n \"^    [A-Z_]* *: t.ClassVar\\|^[A-Z_]* *: t.ClassVar\" sqlglot/parser.py | head -80; rtk proxy grep -n \"TokenType.STREAMLIT\\|TokenType.STAGE\\|TokenType.PUT\" sqlglot/tokens.py sqlglot/parser.py | head; rtk proxy grep -n \"STREAMLIT\\|    PUT\\|    GET\" sqlglot/tokens.py", "description": "Inspect SnowflakeParser and token set layout"}
[tool_result ERROR] Exit code 1
328:    FUNCTIONS: t.ClassVar[dict[str, t.Callable]] = {
432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
441:    STRUCT_TYPE_TOKENS: t.ClassVar = {
448:    NESTED_TYPE_TOKENS: t.ClassVar = {
458:    ENUM_TYPE_TOKENS: t.ClassVar = {
465:    AGGREGATE_TYPE_TOKENS: t.ClassVar = {
470:    TYPE_TOKENS: t.ClassVar = {
591:    SIGNED_TO_UNSIGNED_TYPE_TOKEN: t.ClassVar = {
601:    SUBQUERY_PREDICATES: t.ClassVar = {
608:    SUBQUERY_TOKENS: t.ClassVar = {
614:    RESERVED_TOKENS: t.ClassVar
…[3444 chars elided]…
AREN}
1569:    PRE_VOLATILE_TOKENS: t.ClassVar = {TokenType.CREATE, TokenType.REPLACE, TokenType.UNIQUE}
1571:    TRANSACTION_KIND: t.ClassVar = {"DEFERRED", "IMMEDIATE", "EXCLUSIVE"}
1572:    TRANSACTION_CHARACTERISTICS: t.ClassVar[OPTIONS_TYPE] = {
1582:    CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:630:        TokenType.STAGE,
sqlglot/parser.py:632:        TokenType.STREAMLIT,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:748:        TokenType.STREAMLIT,
[tool_use Bash] {"command": "rtk proxy grep -n \"Parser\\|STATEMENT\\|def \\|TokenType.STAGE\" sqlglot/dialects/snowflake.py | head -80; sed -n 660,700p sqlglot/parser.py", "description": "Locate Snowflake Parser class and ID_VAR_TOKENS"}
[tool_result] 10:    SnowflakeParser,
118:    def can_quote(self, identifier: exp.Identifier, identify: str | bool = "safe") -> bool:
131:    Parser = SnowflakeParser
163:            "STAGE": TokenType.STAGE,
        TokenType.TABLE,
        TokenType.VIEW,
        TokenType.SESSION,
    }

    # Tokens that can represent identifiers
    ID_VAR_TOKENS: t.ClassVar[set] = {
        TokenType.ALL,
        TokenType.ANALYZE,
        TokenType.ATTACH,
        TokenType.VAR,
        TokenType.ANTI,
        TokenTyp
…[244 chars elided]…
        TokenType.COMMENT,
        TokenType.COMMIT,
        TokenType.CONSTRAINT,
        TokenType.COPY,
        TokenType.CUBE,
        TokenType.CURRENT_SCHEMA,
        TokenType.DEFAULT,
        TokenType.DELETE,
        TokenType.DESC,
        TokenType.DESCRIBE,
        TokenType.DETACH,
        TokenType.DICTIONARY,
        TokenType.DIV,
        TokenType.END,
        TokenType.EXECUTE,
        TokenType.EXPORT,
        TokenType.ESCAPE,
        TokenType.FALSE,
        TokenType.FIRST,
[tool_use Bash] {"command": "rtk proxy grep -rn \"class SnowflakeParser\" sqlglot/ ; F=$(rtk proxy grep -rln \"class SnowflakeParser\" sqlglot/); echo $F; rtk proxy grep -n \"STATEMENT_PARSERS\\|def _parse_\\|TokenType.PUT\\|TokenType.GET\\|PUT\\|class SnowflakeParser\" $F | head -60", "description": "Find SnowflakeParser definition file"}
[tool_result] sqlglot/parsers/snowflake.py:329:class SnowflakeParser(parser.Parser):
sqlglot/parsers/snowflake.py
329:class SnowflakeParser(parser.Parser):
758:    STATEMENT_PARSERS = {
759:        **parser.Parser.STATEMENT_PARSERS,
760:        TokenType.GET: lambda self: self._parse_get(),
761:        TokenType.PUT: lambda self: self._parse_put(),
786:        "COMPUTE": lambda self: self.expression(exp.ComputeProperty()),
899:    def _parse_directory(self) -> exp.DirectoryStage:
904:    def _parse_describe(s
…[1138 chars elided]…
self) -> exp.FileFormatProperty:
1270:    def _parse_credentials_property(self) -> exp.CredentialsProperty:
1273:    def _parse_semantic_view(self) -> exp.SemanticView:
1290:    def _parse_set(self, unset: bool = False, tag: bool = False) -> exp.Set | exp.Command:
1299:    def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
1304:    def _parse_substring(self) -> exp.Substring:
1321:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 756,768p sqlglot/parsers/snowflake.py; sed -n 1184,1213p sqlglot/parsers/snowflake.py; sed -n 930,940p sqlglot/expressions/query.py; rtk proxy grep -n \"PUT\\|GET\\|STREAMLIT\\|UNDO\\|UNNEST\\|UNPIVOT\" sqlglot/tokens.py | head; rtk proxy grep -n \"PUT\\|GET\" sqlglot/parsers/snowflake.py | head -5; sed -n 1,20p sqlglot/parsers/snowflake.py", "description": "Read Snowflake PUT/GET parsing pattern"}
[tool_result]     }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.GET: lambda self: self._parse_get(),
        TokenType.PUT: lambda self: self._parse_put(),
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    PROPERTY_PARSERS = {
        **parser.Parser.PROPERTY_PARSERS,
        "CREDENTIALS": lambda self: self._parse_credentials_property(),
        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
    def _parse_put(self) -> exp.Put | e
…[1635 chars elided]…
__future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
    Dialect,
    build_default_decimal_type,
    build_formatted_time,
    build_like,
    build_replace_with_optional_replacement,
    build_timetostr_or_tochar,
    build_trunc,
    binary_from_function,
    date_trunc_to_time,
    map_date_part,
)
from sqlglot.helper import is_date_unit, is_int, seq_get
from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "rtk proxy grep -rn \"    UNPIVOT = \\|    UNNEST = \\|    UNION = \\|    TYPE\\b\\|    UNIQUE = \\|    TOP = \\|    TAG = \" sqlglot/tokens.py sqlglot/tokens*.py; rtk proxy grep -n \"ID_VAR_TOKENS\\|UNPIVOT\\|UNNEST\" sqlglot/parser.py | head -12; rtk proxy grep -n \"def drop_sql\" sqlglot/generator.py; rtk proxy grep -rn \"def _match_text_seq\" -A 12 sqlglot/parser.py | head -20", "description": "Find token enum and parser set locations"}
[tool_result] 279:    # UNPIVOT's pre-FOR values and FOR field are new output names, not column references.
421:        "UNNEST": lambda args: exp.Unnest(expressions=ensure_list(seq_get(args, 0))),
666:    ID_VAR_TOKENS: t.ClassVar[set] = {
754:        TokenType.UNNEST,
755:        TokenType.UNPIVOT,
772:    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
786:    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS
821:            TokenType.UNPIVOT,
858
…[489 chars elided]…
58-        for text in texts:
sqlglot/parser.py-1959-            if self._curr.token_type != string_type and self._curr.text.upper() == text:
sqlglot/parser.py-1960-                self._advance()
sqlglot/parser.py-1961-            else:
sqlglot/parser.py-1962-                self._retreat(index)
sqlglot/parser.py-1963-                return False
sqlglot/parser.py-1964-
sqlglot/parser.py-1965-        if not advance:
sqlglot/parser.py-1966-            self._retreat(index)
sqlglot/parser.py-1967-
[tool_use Bash] {"command": "rtk proxy grep -rln \"class TokenType\" sqlglot/; rtk proxy grep -rn \"^    PUT\\b\\|^    UNNEST\\b\\|^    UNPIVOT\\b\\|^    UNION\\b\\|^    UNIQUE\\b\\|^    TOP\\b\\|^    TSTZ\\|^    UNKNOWN\" sqlglot/*.py sqlglot/*/*.py | head; sed -n 728,734p sqlglot/parser.py", "description": "Locate TokenType enum definition"}
[tool_result] sqlglot/tokenizer_core.py
sqlglot/tokenizer_core.py:185:    TSTZRANGE = auto()
sqlglot/tokenizer_core.py:186:    TSTZMULTIRANGE = auto()
sqlglot/tokenizer_core.py:232:    UNKNOWN = auto()
sqlglot/tokenizer_core.py:386:    PUT = auto()
sqlglot/tokenizer_core.py:427:    TOP = auto()
sqlglot/tokenizer_core.py:434:    UNION = auto()
sqlglot/tokenizer_core.py:435:    UNNEST = auto()
sqlglot/tokenizer_core.py:436:    UNPIVOT = auto()
sqlglot/tokenizer_core.py:450:    UNIQUE = auto()
sqlglot/expressions/datatypes.py:145:    TSTZMULTIRANGE = auto()
        TokenType.PARTITION,
        TokenType.PERCENT,
        TokenType.PIVOT,
        TokenType.PRAGMA,
        TokenType.PUT,
        TokenType.RANGE,
        TokenType.RECURSIVE,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNION = auto()\n    UNNEST = auto()", "new_string": "    UNDROP = auto()\n    UNION = auto()\n    UNNEST = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "offset": 745, "limit": 30}
[tool_result] 745	        TokenType.SETTINGS,
746	        TokenType.SHOW,
747	        TokenType.STREAM,
748	        TokenType.STREAMLIT,
749	        TokenType.TEMPORARY,
750	        TokenType.TOP,
751	        TokenType.TRUE,
752	        TokenType.TRUNCATE,
753	        TokenType.UNIQUE,
754	        TokenType.UNNEST,
755	        TokenType.UNPIVOT,
756	        TokenType.UPDATE,
757	        TokenType.USE,
758	        TokenType.VOLATILE,
759	        TokenType.WINDOW,
760	        TokenType.CURRENT_CATALOG,
761	        TokenType.LOCALTIME,
762	        TokenType.LOCALTIMESTAMP,
763	        TokenType.SESSION_USER,
764	        TokenType.STRAIGHT_JOIN,
765	        *ALTERABLES,
766	        *CREATABLES,
767	        *SUBQUERY_PREDICATES,
768	        *TYPE_TOKENS,
769	        *NO_PAREN_FUNCTIONS,
770	    } - {TokenType.UNION}
771	
772	    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
773	        TokenType.ANTI,
774	        TokenType.ASOF,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.UNIQUE,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,\n        TokenType.UPDATE,\n        TokenType.USE,\n        TokenType.VOLATILE,", "new_string": "        TokenType.UNDROP,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,\n        TokenType.UPDATE,\n        TokenType.USE,\n        TokenType.VOLATILE,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 370,380p sqlglot/expressions/ddl.py; rtk proxy grep -n \"^from\\|^import\\|Drop\\b\" sqlglot/expressions/__init__.py | head -5", "description": "Check ddl expression layout and exports"}
[tool_result]     arg_types = {}


class Command(Expression):
    arg_types = {"this": True, "expression": False}


class Transaction(Expression):
    arg_types = {"this": False, "modes": False, "mark": False}


14:from sqlglot.expressions.core import *  # noqa: F401,F403
15:from sqlglot.expressions.datatypes import *  # noqa: F401,F403
16:from sqlglot.expressions.constraints import *  # noqa: F401,F403
17:from sqlglot.expressions.properties import *  # noqa: F401,F403
18:from sqlglot.expressions.query import *  # noqa: F401,F403
[assistant] Now the expression class, placed right after `Drop`, plus the generator and the parser pieces.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):\n    arg_types = {}\n", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):\n    arg_types = {}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generator.py", "offset": 1806, "limit": 4}
[tool_result] 1806	        return f"DROP{temporary}{materialized}{iceberg} {kind}{concurrently_sql}{exists_sql}{this}{on_cluster}{expressions}{cascade}{restrict}{constraints}{purge}{sync}"
1807	
1808	    def set_operation(self, expression: exp.SetOperation) -> str:
1809	        op_type = type(expression)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generator.py", "old_string": "        return f\"DROP{temporary}{materialized}{iceberg} {kind}{concurrently_sql}{exists_sql}{this}{on_cluster}{expressions}{cascade}{restrict}{constraints}{purge}{sync}\"\n\n    def set_operation(", "new_string": "        return f\"DROP{temporary}{materialized}{iceberg} {kind}{concurrently_sql}{exists_sql}{this}{on_cluster}{expressions}{cascade}{restrict}{constraints}{purge}{sync}\"\n\n    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n    def set_operation("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.PUT: lambda self: self._parse_put(),\n        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.PUT: lambda self: self._parse_put(),\n        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return self.expression(\n            exp.Get(this=self._parse_string(), target=target, properties=self._parse_properties())\n        )\n", "new_string": "        return self.expression(\n            e
…[704 chars elided]…
           )\n                if self._match_text_seq(*kind.split())\n            ),\n            None,\n        )\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Undrop(\n                this=self._parse_table_parts(schema=True, is_db_reference=kind == \"SCHEMA\"),\n                kind=kind,\n            )\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nstmts = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP DYNAMIC TABLE db.s.t','UNDROP ICEBERG TABLE t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT sn','UNDROP STREAMLIT st','UNDROP TAG tg','UNDROP TYPE ty','UNDROP EXTERNAL VOLUME ev',
…[93 chars elided]…
)','SELECT undrop FROM t', 'undrop table t', 'UNDROP FOO x']\nfor s in stmts:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex).splitlines()[0])\nprint(sqlglot.parse_one('UNDROP TABLE t', read='snowflake').sql('duckdb'))\n\"", "description": "Smoke-test UNDROP parsing and generation"}
[tool_result] 'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
Undrop | UNDROP TABLE t
Undrop | UNDROP TABLE db.s.t
Undrop | UNDROP DYNAMIC TABLE db.s.t
Undrop | UNDROP ICEBERG TABLE t
Undrop | UNDROP SCHEMA s
Undrop | UNDROP DATABASE d
Undrop | UNDROP ACCOUNT a
Undrop | UNDROP NOTEBOOK n
Undrop | UNDROP SNAPSHOT sn
Undrop | UNDROP STREAMLIT st
Undrop | UNDROP TAG tg
Undrop | UNDROP TYPE ty
Undrop | UNDROP EXTERNAL VOLUME ev
Undrop | UNDROP TABLE IDENTIFIER('"01b2c3-abc"')
Undrop | UNDROP SCHEMA IDENTIFIER('"x"')
Select | SELECT undrop FROM t
Undrop | UNDROP TABLE t
Command | UNDROP FOO x
UNDROP TABLE t
[assistant] Parsing and generation work for every kind, including the `IDENTIFIER(...)` form. Now the tests.
[tool_use Bash] {"command": "rtk proxy grep -n \"def test_\\|DROP\" tests/dialects/test_snowflake.py | head -80", "description": "Find test layout in Snowflake test file"}
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
4304:            "DROP FUNCTION my_udf (OBJECT(city VARCHAR, zipcode
…[2315 chars elided]…
by_min_by(self):
5937:    def test_create_view_copy_grants(self):
5959:    def test_create_view_row_access_policy(self):
5994:    def test_semantic_view(self):
6038:    def test_get_extract(self):
6065:    def test_create_sequence(self):
6078:    def test_bit_aggs(self):
6087:    def test_bitmap_or_agg(self):
6090:    def test_md5_functions(self):
6097:    def test_sha1(self):
6128:    def test_model_attribute(self):
6138:    def test_set_item_kind_attribute(self):
6149:    def test_round(self):
[tool_use Bash] {"command": "sed -n 5349,5358p tests/dialects/test_snowflake.py", "description": "Read existing drop test for style"}
[tool_result]         )

    def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n", "new_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n\n    def test_undrop(self):\n  
…[386 chars elided]…
E ty\",\n        ):\n            with self.subTest(kind):\n                self.validate_identity(f\"UNDROP {kind}\")\n\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('\\\"01b2c3d4-0000-0001-0000-000000000001\\\"')\")\n        self.validate_identity(\"UNDROP SCHEMA IDENTIFIER('\\\"01b2c3d4-0000-0001-0000-000000000002\\\"')\")\n        self.validate_identity(\"SELECT undrop FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-201845-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
...............................................................................
…[376 chars elided]…
.................. [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 52.31s
[assistant] All 1121 tests pass. Now the style check on the touched files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; F=\"sqlglot/tokenizer_core.py sqlglot/parser.py sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py\"; $P -m ruff check $F 2>&1 | tail -5; $P -m ruff format --check $F 2>&1 | tail -5; git status --short", "description": "Run ruff lint and format checks on changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/tokenizer_core.py sqlglot/parser.py sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py:1:1

Found 1 error.
error: Failed to format sqlglot/tokenizer_core.py sqlglot/parser.py sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py: No such file or directory (os error 2)
 M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff check sqlglot/tokenizer_core.py sqlglot/parser.py sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py; $P -m ruff format --check sqlglot/tokenizer_core.py sqlglot/parser.py sqlglot/expressions/ddl.py sqlglot/generator.py sqlglot/parsers/snowflake.py sqlglot/dialects/snowflake.py tests/dialects/test_snowflake.py", "description": "Run ruff lint and format checks on changed files"}
[tool_result ERROR] Exit code 1
All checks passed!
Would reformat: tests/dialects/test_snowflake.py
1 file would be reformatted, 6 files already formatted
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format --diff tests/dialects/test_snowflake.py 2>&1 | head -30", "description": "Show the formatting diff for the test file"}
[tool_result] --- tests/dialects/test_snowflake.py
+++ tests/dialects/test_snowflake.py
@@ -5374,8 +5374,12 @@
             with self.subTest(kind):
                 self.validate_identity(f"UNDROP {kind}")
 
-        self.validate_identity("UNDROP TABLE IDENTIFIER('\"01b2c3d4-0000-0001-0000-000000000001\"')")
-        self.validate_identity("UNDROP SCHEMA IDENTIFIER('\"01b2c3d4-0000-0001-0000-000000000002\"')")
+        self.validate_identity(
+            "UNDROP TABLE IDENTIFIER('\"01b2c3d4-0000-0001-0000-000000000001\"')"
+        )
+        self.validate_identity(
+            "UNDROP SCHEMA IDENTIFIER('\"01b2c3d4-0000-0001-0000-000000000002\"')"
+        )
         self.validate_identity("SELECT undrop FROM t")
 
     def test_show_primary_keys(self):

1 file would be reformatted
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format tests/dialects/test_snowflake.py && $P -m ruff format --check sqlglot tests/dialects/test_snowflake.py | tail -1 && $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -2; git diff --stat", "description": "Apply formatting and rerun Snowflake tests"}
[tool_result] 1 file reformatted
177 files already formatted
.................................................................                                                     [100%]
96 passed, 1580 subtests passed in 0.47s
sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generator.py             |  3 +++
 sqlglot/parser.py                |  1 +
 sqlglot/parsers/snowflake.py     | 34 ++++++++++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 26 ++++++++++++++++++++++++++
 7 files changed, 70 insertions(+)
[This command modified 1 file you've previously read: tests/dialects/test_snowflake.py. Call Read before editing.]
[assistant] `UNDROP` now parses and generates for all twelve Snowflake object kinds, including the `IDENTIFIER('"<id>"')` form. The full suite passes (1121 tests, 18188 subtests), and ruff lint and format are clean. I haven't committed anything.

What changed:

- **Tokenizer:** a new `TokenType.UNDROP` in `sqlglot/tokenizer_core.py`, mapped from the `UNDROP` keyword in the Snowflake tokenizer. It is also added to the parser's `ID_VAR_TOKENS`, so `SELECT undrop FROM t` still parses as a column.
- **Expression:** `exp.Undrop(this, kind)` in `sqlglot/expressions/ddl.py`, next to `Drop`.
- **Parser:** `_parse
…[185 chars elided]…
E`, `ICEBERG TABLE`) and reads the name with the same table-parts parsing `DROP` uses. An unrecognised kind falls back to `exp.Command`, as `DROP` does.
- **Generator:** `undrop_sql` in the base `sqlglot/generator.py`, placed beside `drop_sql`. I put it there rather than in the Snowflake generator because `Put`/`Get` do the same.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` round-trips each kind, both `IDENTIFIER` forms, and the `undrop` identifier case.

Not run: the mypyc build (`make testc`). Adding an enum member could matter there, so it's worth running before merging.
