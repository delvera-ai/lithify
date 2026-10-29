# trajectory base-1

final message:
Snowflake `UNDROP` now parses and generates for all twelve object types, including the `IDENTIFIER(<id>)` form. The full suite passes (1121 tests, 18188 subtests), and ruff format and lint are clean. The changes are uncommitted in the worktree.

Parsing an `UNDROP` in Snowflake gives a new `exp.Undrop` node. Generating it writes back the same SQL.

- **Tokenizer:** `UNDROP` is a new keyword in the Snowflake tokenizer. It's also in Snowflake's `ID_VAR_TOKENS` and `ALIAS_TOKENS`, so `SELECT undrop FROM undrop` still parses as identifiers.
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowflake.py` matches the kind from a fixed list (`UNDROP_KINDS`, multi-word kinds included) and parses the name with the same table-parts logic that `DROP` uses. An unrecognised kind falls back to `exp.Command`, so it round-trips as raw text instead of raising.
- **Expression and generator:** `exp.Undrop(this, kind)` lives in `sqlglot/expressions/ddl.py`. `undrop_sql` is in the Snowflake generator.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` covers every kind, qualified names, and the `IDENTIFIER('12345')` form for TABLE, SCHEMA and DATABASE.

I couldn't run these statements against a live Snowflake account, so the tests check parse and generate round-trips only. The `IDENTIFIER(...)` form is validated by the round-trip, not by Snowflake accepting it.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"undrop\\|UNDROP\" -r sqlglot tests | head -30; grep -n \"STATEMENT_PARSERS\\|def _parse_drop\\|_parse_drop\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -30", "description": "Check repo state and search for UNDROP references"}
[tool_result] sqlglot/parser.py:1082:    STATEMENT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1094:        TokenType.DROP: lambda self: self._parse_drop(),
sqlglot/parser.py:2278:        if self._match_set(self.STATEMENT_PARSERS):
sqlglot/parser.py:2280:            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
sqlglot/parser.py:2298:    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
sqlglot/parser.py:3401:        if self._match_set(self.STATEMENT_PARSERS, advance=False):
sqlglot/parser.py:8709:    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
sqlglot/parser.py:8710:        drop = self._parse_drop() if self._match(TokenType.DROP) else None
sqlglot/parser.py:8716:        return self._parse_drop_column()
sqlglot/parser.py:8719:    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
sqlglot/parser.py:8825:            return self._parse_csv(lambda: self._parse_drop_partition(exists=partition_exists))
[tool_use Bash] {"command": "git status --short | head; sed -n 2298,2380p sqlglot/parser.py; grep -n \"UNDROP\\|Undrop\" sqlglot/expressions.py | head; grep -n \"STATEMENT_PARSERS\\|_parse_drop\\|ALTER\\|def _parse_alter\" sqlglot/dialects/snowflake.py | head -30", "description": "Inspect base drop parsing and snowflake statements"}
[tool_result]     def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
            return self._parse_as_command(start)

        concurrently = self._match_text_seq("
…[2252 chars elided]…
STORE"
        ):
            clustered = False
        else:
            clustered = None

        if self._match_pair(TokenType.TABLE, TokenType.FUNCTION, advance=False):
            self._advance()

        properties = None
        create_token = self._match_set(self.CREATABLES) and self._prev

        if not create_token:
            # exp.Properties.Location.POST_CREATE
ugrep: warning: sqlglot/expressions.py: No such file or directory
27:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP SCHEMA s','UNDROP TABLE IDENTIFIER(\\'123\\')']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake')))\n    except Exception as e: print('ERR', e)\n\"; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.__file__)\"; grep -n \"UNDROP\\|Undrop\" sqlglot/tokens.py sqlglot/dialects/snowflake.py sqlglot/parser.py | head; grep -n \"class Drop\\b\\|class Drop(\" -A 25 sqlglot/expressions/*.py | head -40", "description": "Reproduce UNDROP ParseError and locate Drop expression"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
ERR Invalid expression / Unexpected token. Line 1, Col: 23.
  UNDROP TABLE [4mIDENTIFIER[0m('123')
~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/__init__.py
sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py-346-    arg_types
…[805 chars elided]…
False,
sqlglot/expressions/ddl.py-361-    }
sqlglot/expressions/ddl.py-362-
sqlglot/expressions/ddl.py-363-    @property
sqlglot/expressions/ddl.py-364-    def kind(self) -> str | None:
sqlglot/expressions/ddl.py-365-        kind = self.args.get("kind")
sqlglot/expressions/ddl.py-366-        return kind and kind.upper()
sqlglot/expressions/ddl.py-367-
sqlglot/expressions/ddl.py-368-
sqlglot/expressions/ddl.py-369-class DropPrimaryKey(Expression):
sqlglot/expressions/ddl.py-370-    arg_types = {}
[tool_use Bash] {"command": "grep -rn \"STATEMENT_PARSERS\" sqlglot/dialects | head; grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -20; sed -n 1082,1100p sqlglot/parser.py; grep -n \"class Snowflake\" -A3 sqlglot/dialects/snowflake.py | head; grep -n \"class Parser\" sqlglot/dialects/snowflake.py", "description": "Find statement parser extension patterns and IDENTIFIER handling"}
[tool_result] sqlglot/parser.py:574:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:617:    } - {TokenType.IDENTIFIER}
sqlglot/parser.py:707:        TokenType.IDENTIFIER,
sqlglot/parser.py:800:    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
sqlglot/parser.py:841:        TokenType.IDENTIFIER,
sqlglot/parser.py:1479:        TokenType.IDENTIFIER,
sqlglot/parser.py:4651:        while self._match_set(self.IDENTIFIER_TOKENS):
sqlglot/parser.py:4662:            
…[1953 chars elided]…
        TokenType.REVOKE: lambda self: self._parse_revoke(),
        TokenType.INSERT: lambda self: self._parse_insert(),
        TokenType.KILL: lambda self: self._parse_kill(),
        TokenType.LOAD: lambda self: self._parse_load(),
        TokenType.MERGE: lambda self: self._parse_merge(),
16:class Snowflake(Dialect):
17-    # https://docs.snowflake.com/en/sql-reference/identifiers-syntax
18-    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
19-    NULL_ORDERING = "nulls_are_large"
[tool_use Bash] {"command": "sed -n 1100,1115p sqlglot/parser.py; grep -n \"UNDROP\\|\\\"UNDROP\\|\\\"UNDO\\|UNDO\" sqlglot/tokens.py sqlglot/parser.py | head; grep -n \"class Parser\\|class Tokenizer\\|class Generator\\|STATEMENT_PARSERS\\|SHOW_PARSERS\\|def _parse_show\\|def _parse_describe\\|class Show\" sqlglot/dialects/snowflake.py | head -20; grep -n \"IDENTIFIER(\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py | head", "description": "Inspect remaining statement parsers and Snowflake IDENTIFIER usage"}
[tool_result]         TokenType.MERGE: lambda self: self._parse_merge(),
        TokenType.PIVOT: lambda self: self._parse_simplified_pivot(),
        TokenType.PRAGMA: lambda self: self.expression(exp.Pragma(this=self._parse_expression())),
        TokenType.REFRESH: lambda self: self._parse_refresh(),
        TokenType.ROLLBACK: lambda self: self._parse_commit_or_rollback(),
        TokenType.SET: lambda self: self._parse_set(),
        TokenType.TRUNCATE: lambda self: self._parse_truncate_table(),
        TokenType.UNCACHE: lambda self: self._parse_uncache(),
        TokenType.UNPIVOT: lambda self: self._parse_simplified_pivot(is_unpivot=True),
        TokenType.UPDATE: lambda self: self._parse_update(),
        TokenType.USE: lambda self: self._parse_use(),
        TokenType.SEMICOLON: lambda self: exp.Semicolon(),
    }

    UNARY_PARSERS: t.ClassVar = {
        TokenType.PLUS: lambda self: self._parse_unary(),  # Unary + is handled as a no-op
133:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "grep -n \"^    class \\|    STATEMENT\\|IDENTIFIER\\|def _parse_\\|def .*_sql\" sqlglot/dialects/snowflake.py | head -120; grep -n \"class Undrop\\|class Drop\\|^class Use\\b\" sqlglot/expressions/*.py", "description": "List Snowflake parser and generator methods"}
[tool_result] 127:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
133:    class Tokenizer(tokens.Tokenizer):
sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py:369:class DropPrimaryKey(Expression):
sqlglot/expressions/ddl.py:418:class Use(Expression):
sqlglot/expressions/query.py:1949:class DropPartition(Expression):
[tool_use Bash] {"command": "wc -l sqlglot/dialects/snowflake.py && sed -n 1,20p sqlglot/dialects/snowflake.py && grep -n \"^class \\|^    class \" sqlglot/dialects/snowflake.py; grep -n \"snowflake\" sqlglot/dialects/__init__.py | head -3; ls sqlglot/dialects | head -50", "description": "Locate Snowflake dialect parser definitions"}
[tool_result]      187 sqlglot/dialects/snowflake.py
from __future__ import annotations

from sqlglot import exp, jsonpath, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.snowflake import SnowflakeGenerator
from sqlglot.parsers.snowflake import (
    SnowflakeParser,
)
from sqlglot.tokens import TokenType
from sqlglot.typing.snowflake import EXPRESSION_METADATA


class Snowflake(Dialect):
    # https://docs.snowflake.com/en/sql-reference/identif
…[163 chars elided]…
 Snowflake(Dialect):
127:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
133:    class Tokenizer(tokens.Tokenizer):
__init__.py
__pycache__
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators; wc -l sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py; grep -n \"STATEMENT_PARSERS\\|IDENTIFIER\\|def _parse_drop\\|UNDROP\\|Undrop\\|SHOW\\|def _parse_show\" sqlglot/parsers/snowflake.py | head -40; grep -n \"def drop_sql\" -A40 sqlglot/generators/*.py | head -60", "description": "Inspect Snowflake parser and generator modules"}
[tool_result] sqlglot/generators:
__init__.py
__pycache__
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

sqlglot/parsers:
__init__.py
__pycache__
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris
…[3542 chars elided]…
nerators/tsql.py-623-
sqlglot/generators/tsql.py-624-    def ifblock_sql(self, expression: exp.IfBlock) -> str:
sqlglot/generators/tsql.py-625-        this = self.sql(expression, "this")
sqlglot/generators/tsql.py-626-        true = self.sql(expression, "true")
sqlglot/generators/tsql.py-627-        true = f" {true}" if true else " "
sqlglot/generators/tsql.py-628-        false = self.sql(expression, "false")
sqlglot/generators/tsql.py-629-        false = f"; ELSE BEGIN {false}" if false else ""
[tool_use Bash] {"command": "sed -n 750,800p sqlglot/parsers/snowflake.py; sed -n 1115,1140p sqlglot/parsers/snowflake.py; grep -n \"IDENTIFIER\\|UNDROP\\|def use_sql\\|def drop_sql\" sqlglot/generators/snowflake.py | head; grep -n \"UNDROP\\|\\\"UNDO\\|undrop\" -ri sqlglot/ tests/ | head; grep -n \"class Use\" -A12 sqlglot/expressions/ddl.py; grep -n \"def _parse_use\" -A20 sqlglot/parsers/base.py | head -30", "description": "View Snowflake statement parser and identifier helper"}
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
…[3056 chars elided]…
verload(Expression):
234-    arg_types = {"this": True, "expressions": False, "is_table": False}
235-
236-
237-class CharacterSet(Expression):
--
418:class Use(Expression):
419-    arg_types = {"this": False, "expressions": False, "kind": False}
420-
421-
422-class NextValueFor(Expression, Func):
423-    arg_types = {"this": True, "order": False}
424-
425-
426-class Execute(Expression):
427-    arg_types = {"this": True, "expressions": False}
428-
429-    @property
430-    def name(self) -> str:
[tool_use Bash] {"command": "grep -rn \"GET\\b\\|\\bPUT\\b\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/base.py sqlglot/parsers/snowflake.py sqlglot/dialects/dialect.py | head -20; grep -n \"def _parse_get\" -A12 sqlglot/parsers/snowflake.py; grep -n \"KEYWORDS = {\" -A3 sqlglot/parsers/snowflake.py sqlglot/tokens*.py | head; grep -n \"class Tokenizer\" -A10 sqlglot/dialects/snowflake.py | head -40", "description": "Check how GET/PUT statement tokens are defined"}
[tool_result] sqlglot/parsers/snowflake.py:524:        "GET": exp.GetExtract.from_arg_list,
sqlglot/parsers/snowflake.py:760:        TokenType.GET: lambda self: self._parse_get(),
sqlglot/parsers/snowflake.py:761:        TokenType.PUT: lambda self: self._parse_put(),
sqlglot/parsers/snowflake.py:1199:        # If we detect GET( then we need to parse a function, not a statement
sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:839:        TokenType.GET,
…[548 chars elided]…
e == TokenType.URI_START:
1208-            return self._parse_as_command(start)
133:    class Tokenizer(tokens.Tokenizer):
134-        STRING_ESCAPES = ["\\", "'"]
135-        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
136-        RAW_STRINGS = ["$$"]
137-        COMMENTS = ["--", "//", ("/*", "*/")]
138-        NESTED_COMMENTS = False
139-
140-        KEYWORDS = {
141-            **tokens.Tokenizer.KEYWORDS,
142-            "BYTEINT": TokenType.INT,
143-            "FILE://": TokenType.URI_START,
[tool_use Bash] {"command": "grep -rn \"\\bGET = \\|\\bPUT = \\|\\\"GET\\\"\\|\\\"PUT\\\"\\|\\\"USE\\\"\\|\\bUSE = \" sqlglot/*.py sqlglot/**/*.py | head; sed -n 700,712p sqlglot/parser.py; sed -n 728,736p sqlglot/parser.py; sed -n 836,842p sqlglot/parser.py", "description": "Find where GET/PUT token types are defined"}
[tool_result] sqlglot/tokens.py:403:        "USE": TokenType.USE,
sqlglot/tokenizer_core.py:306:    GET = auto()
sqlglot/tokenizer_core.py:386:    PUT = auto()
sqlglot/tokenizer_core.py:438:    USE = auto()
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.py:154:            "PUT": TokenType.PUT,
sqlglot/generators/snowflake.py:497:        exp.GetExtract: rename_func("GET"),
sqlglot/parsers/tsql.py:89:    "USE": ("PLAN",),
sqlglot/tokenizer_core.py:306:    GET = au
…[299 chars elided]…
S,
        TokenType.ISNULL,
        TokenType.INTERVAL,
        TokenType.KEEP,
        TokenType.PARTITION,
        TokenType.PERCENT,
        TokenType.PIVOT,
        TokenType.PRAGMA,
        TokenType.PUT,
        TokenType.RANGE,
        TokenType.RECURSIVE,
        TokenType.REFERENCES,
        TokenType.REFRESH,
        TokenType.FILTER,
        TokenType.FIRST,
        TokenType.FORMAT,
        TokenType.GET,
        TokenType.GLOB,
        TokenType.IDENTIFIER,
        TokenType.INDEX,
[tool_use Bash] {"command": "sed -n 2262,2297p sqlglot/parser.py; sed -n 300,310p sqlglot/tokenizer_core.py; sed -n 380,390p sqlglot/tokenizer_core.py; ls sqlglot/tokens*.py; grep -n \"TokenType.USE\\b\" sqlglot/parser.py | head -3; git log --oneline -3 -- sqlglot/tokenizer_core.py", "description": "Inspect statement dispatch and token enum layout"}
[tool_result]             exp.Block(
                expressions=self._parse_batch_statements(
                    parse_method=lambda self: self._parse_statement()
                )
            )
        )

    def _parse_whileblock(self) -> exp.WhileBlock:
        return self.expression(
            exp.WhileBlock(this=self._parse_condition(), body=self._parse_block())
        )

    def _parse_statement(self) -> exp.Expr | None:
        if not self._curr:
            return None

        if self._match_set
…[1171 chars elided]…
= auto()
    QUOTE = auto()
    QDCOLON = auto()
    RANGE = auto()
sqlglot/tokens.py
757:        TokenType.USE,
1110:        TokenType.USE: lambda self: self._parse_use(),
1672:    TABLE_INDEX_HINT_TOKENS: t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
cc448ac48 feat(postgres): add support for PostGIS 3D distance operator <<->> (#7655)
87cc1069e fix(redshift)!: roundtrip support for CURRENT_USER_ID and USER (#7633)
ae58fd10c feat(postgres)!: parse CREATE TYPE statements (#7616)
[tool_use Bash] {"command": "grep -n \"def _match_text_seq\" -A22 sqlglot/parser.py | head -30; grep -n \"def _parse_table_part\\b\" -A12 sqlglot/parser.py | head -20; grep -n \"class Use\\|class Drop\" -B2 sqlglot/expressions/ddl.py | head; sed -n 1,30p sqlglot/typing/snowflake.py | head -30; grep -n \"EXPRESSION_METADATA\" -r sqlglot tests | head -5", "description": "Check text-match helpers and typing metadata"}
[tool_result] 1955:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1956-        index = self._index
1957-        string_type = TokenType.STRING
1958-        for text in texts:
1959-            if self._curr.token_type != string_type and self._curr.text.upper() == text:
1960-                self._advance()
1961-            else:
1962-                self._retreat(index)
1963-                return False
1964-
1965-        if not advance:
1966-            self._retreat(index)
1967-
196
…[1709 chars elided]…
self: TypeAnnotator, expression: exp.TimestampFromParts
) -> exp.TimestampFromParts:
sqlglot/optimizer/annotate_types.py:207:        self.expression_metadata = expression_metadata or dialect.EXPRESSION_METADATA
sqlglot/typing/clickhouse.py:4:from sqlglot.typing import EXPRESSION_METADATA
sqlglot/typing/clickhouse.py:6:EXPRESSION_METADATA = {
sqlglot/typing/clickhouse.py:7:    **EXPRESSION_METADATA,
sqlglot/typing/bigquery.py:6:from sqlglot.typing import EXPRESSION_METADATA, TIMESTAMP_EXPRESSIONS
[tool_use Bash] {"command": "grep -n \"UNCACHE\\|UNION = \\|UNNEST = \\|UNIQUE = \" sqlglot/tokenizer_core.py; grep -n \"TokenType.UNCACHE\\|TokenType.UNION,\" sqlglot/parser.py | head; sed -n 140,160p sqlglot/dialects/snowflake.py; grep -n \"def undrop\\|GET\\b\" sqlglot/generators/snowflake.py | head -3; grep -n \"    def describe_sql\\|    def use_sql\\|    def show_sql\" sqlglot/generators/snowflake.py", "description": "Locate insertion points for token and parser entries"}
[tool_result] 433:    UNCACHE = auto()
434:    UNION = auto()
435:    UNNEST = auto()
450:    UNIQUE = auto()
445:        TokenType.UNION,
940:        TokenType.UNION,
1107:        TokenType.UNCACHE: lambda self: self._parse_uncache(),
        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "BYTEINT": TokenType.INT,
            "FILE://": TokenType.URI_START,
            "FILE FORMAT": TokenType.FILE_FORMAT,
            "GET": TokenType.GET,
            "INTEGRATION": TokenType.INTEGRATION,

…[274 chars elided]…
pe.POLICY,
            "POOL": TokenType.POOL,
            "PUT": TokenType.PUT,
            "REMOVE": TokenType.COMMAND,
            "RM": TokenType.COMMAND,
            "ROLE": TokenType.ROLE,
            "RULE": TokenType.RULE,
            "SAMPLE": TokenType.TABLE_SAMPLE,
            "SEMANTIC VIEW": TokenType.SEMANTIC_VIEW,
497:        exp.GetExtract: rename_func("GET"),
840:    def show_sql(self, expression: exp.Show) -> str:
875:    def describe_sql(self, expression: exp.Describe) -> str:
[tool_use Bash] {"command": "sed -n 160,172p sqlglot/dialects/snowflake.py; sed -n 1,12p sqlglot/parsers/snowflake.py; sed -n 700,706p sqlglot/parser.py; sed -n 1,5p sqlglot/generators/snowflake.py; sed -n 870,880p sqlglot/generators/snowflake.py; grep -n \"^class Drop\" -A23 sqlglot/expressions/ddl.py | tail -4", "description": "Review Snowflake keyword block and generator layout"}
[tool_result]             "SEMANTIC VIEW": TokenType.SEMANTIC_VIEW,
            "SQL_DOUBLE": TokenType.DOUBLE,
            "SQL_VARCHAR": TokenType.VARCHAR,
            "STAGE": TokenType.STAGE,
            "STORAGE INTEGRATION": TokenType.STORAGE_INTEGRATION,
            "STREAMLIT": TokenType.STREAMLIT,
            "TAG": TokenType.TAG,
            "TIMESTAMP_TZ": TokenType.TIMESTAMPTZ,
            "TOP": TokenType.TOP,
            "VOLUME": TokenType.VOLUME,
            "WAREHOUSE": TokenType.WAREHOUSE,
 
…[812 chars elided]…
pression, flat=True)})" if expression.expressions else ""
        return f"WITH ROW ACCESS POLICY {self.sql(expression, 'this')}{on}"

    def describe_sql(self, expression: exp.Describe) -> str:
        kind_value = expression.args.get("kind") or "TABLE"

        properties = expression.args.get("properties")
        if properties:
            qualifier = self.expressions(properties, sep=" ")
389-class Alter(Expression):
390-    arg_types = {
391-        "this": False,
392-        "kind": True,
[assistant] Plan: add an `UNDROP` token (Snowflake keyword), an `exp.Undrop` expression, a Snowflake statement parser, and a generator method. Starting with the token and expression.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.FULL,\n        TokenType.GET,\n        TokenType.IDENTIFIER,\n        TokenType.INOUT,", "new_string": "        TokenType.FULL,\n        TokenType.GET,\n        TokenType.IDENTIFIER,\n        TokenType.INOUT,"}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] The last edit was a no-op. Checking which token set `GET`/`PUT` live in so `undrop` still works as an identifier.
[tool_use Bash] {"command": "awk 'NR<=740 && /^    [A-Z_]+ *[:=]/ {l=$0; n=NR} NR==706 {print n\": \"l}' sqlglot/parser.py; grep -n \"ID_VAR_TOKENS\\|TABLE_ALIAS_TOKENS\" sqlglot/parsers/snowflake.py | head -5", "description": "Identify which parser token set contains GET/PUT"}
[tool_result] 666:     ID_VAR_TOKENS: t.ClassVar[set] = {
340:    ID_VAR_TOKENS = {
341:        *parser.Parser.ID_VAR_TOKENS,
363:    TABLE_ALIAS_TOKENS = (
364:        parser.Parser.TABLE_ALIAS_TOKENS
379:    COLON_PLACEHOLDER_TOKENS = ID_VAR_TOKENS | {TokenType.NUMBER}
[tool_use Bash] {"command": "sed -n 340,362p sqlglot/parsers/snowflake.py", "description": "View Snowflake ID_VAR_TOKENS block"}
[tool_result]     ID_VAR_TOKENS = {
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
        TokenType.POLICY,
        TokenType.POOL,
        TokenType.ROLE,
        TokenType.RULE,
        TokenType.VOLUME,
    }
[assistant] Adding `UNDROP` to Snowflake's `ID_VAR_TOKENS` and `ALIAS_TOKENS`, then the statement parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.RULE,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS = parser.Parser.ALIAS_TOKENS | {\n        TokenType.INTEGRATION,\n        TokenType.PACKAGE,\n        TokenType.POLICY,\n        T
…[78 chars elided]…
nType.VOLUME,\n    }", "new_string": "        TokenType.RULE,\n        TokenType.UNDROP,\n        TokenType.VOLUME,\n    }\n\n    ALIAS_TOKENS = parser.Parser.ALIAS_TOKENS | {\n        TokenType.INTEGRATION,\n        TokenType.PACKAGE,\n        TokenType.POLICY,\n        TokenType.POOL,\n        TokenType.ROLE,\n        TokenType.RULE,\n        TokenType.UNDROP,\n        TokenType.VOLUME,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_get(self) -> exp.Expr | None:", "new_string": "    def _parse_undrop(self) -> exp.Undrop | exp.Command:\n        start = self._prev\n        kind = next(\n            (\n                k\n    
…[21 chars elided]…
self.UNDROP_KINDS\n                if self._match_text_seq(*k.split(\" \"))\n            ),\n            None,\n        )\n        if not kind:\n            return self._parse_as_command(start)\n\n        this = self._parse_table_parts(schema=True, is_db_reference=kind == \"SCHEMA\")\n        return self.expression(exp.Undrop(this=this, kind=kind))\n\n    def _parse_get(self) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] The parser references `UNDROP_KINDS`, which doesn't exist yet. Adding it next to `STATEMENT_PARSERS`, and tidying the `next(...)` call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }", "new_string": "        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }\n\n    UNDROP_KINDS = (\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        kind = next(\n            (\n                k\n                for k in self.UNDROP_KINDS\n                if self._match_text_seq(*k.split(\" \"))\n            ),\n            None,\n        )", "new_string": "        kind = next((k for k in self.UNDROP_KINDS if self._match_text_seq(*k.split())), None)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "    def describe_sql(self, expression: exp.Describe) -> str:", "new_string": "    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n    def describe_sql(self, expression: exp.Describe) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = ['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP SCHEMA db.s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT x','UNDROP STREAMLIT st','UNDROP TAG tg','UNDROP TYPE ty','UNDROP DYNAMIC TABLE dt','UNDROP EXTERNAL VOLUME ev','UNDROP ICEBERG TABLE it','UNDROP TABLE IDENTIFIER(\\'12345\\')','UNDROP SCHEMA IDENTIFIER(\\'12345\\')','undrop table t', 'SELECT undrop FROM undrop']\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print('ERR', s, str(ex)[:200])\n\"", "description": "Exercise UNDROP parsing across all object kinds"}
[tool_result] Undrop | UNDROP TABLE t
Undrop | UNDROP TABLE db.s.t
Undrop | UNDROP SCHEMA s
Undrop | UNDROP SCHEMA db.s
Undrop | UNDROP DATABASE d
Undrop | UNDROP ACCOUNT a
Undrop | UNDROP NOTEBOOK n
Undrop | UNDROP SNAPSHOT x
Undrop | UNDROP STREAMLIT st
Undrop | UNDROP TAG tg
Undrop | UNDROP TYPE ty
Undrop | UNDROP DYNAMIC TABLE dt
Undrop | UNDROP EXTERNAL VOLUME ev
Undrop | UNDROP ICEBERG TABLE it
Undrop | UNDROP TABLE IDENTIFIER('12345')
Undrop | UNDROP SCHEMA IDENTIFIER('12345')
Undrop | UNDROP TABLE t
Select | SELECT undrop FROM undrop
[assistant] All 12 kinds plus the `IDENTIFIER(...)` form parse and round-trip, and `undrop` still works as an identifier. Now adding tests to the Snowflake dialect test file.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_snowflake.py | sed -n 1,400p | grep -i \"ddl\\|drop\\|alter\\|show\\|describe\" ; grep -n \"def test_ddl\" -A4 tests/dialects/test_snowflake.py | head", "description": "Find existing DDL test methods in Snowflake tests"}
[tool_result] 4238:    def test_ddl(self):
4703:    def test_describe(self):
5204:    def test_show_users(self):
5209:    def test_show_databases(self):
5219:    def test_show_file_formats(self):
5228:    def test_show_functions(self):
5236:    def test_show_procedures(self):
5245:    def test_show_stages(self):
5254:    def test_show_warehouses(self):
5261:    def test_show_schemas(self):
5271:    def test_show_objects(self):
5285:    def test_show_columns(self):
5296:    def test_show_tables(self):
5335:   
…[164 chars elided]…
:    def test_show_unique_keys(self):
5413:    def test_show_imported_keys(self):
5432:    def test_show_sequences(self):
5750:    def test_alter_set_unset(self):
5767:    def test_alter_session(self):
4238:    def test_ddl(self):
4239-        for constraint_prefix in ("WITH ", ""):
4240-            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4241-                self.validate_identity(
4242-                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
[tool_use Bash] {"command": "sed -n 5351,5358p tests/dialects/test_snowflake.py", "description": "View existing drop-iceberg test for style"}
[tool_result]     def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_drop_iceberg_table(self):", "new_string": "    def test_undrop(self):\n        for kind in (\n            \"ACCOUNT a\",\n            \"DATABASE d\",\n            \"DYNAMIC TABLE dt\",\n     
…[331 chars elided]…
    self.validate_identity(f\"UNDROP {kind}\")\n\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('12345')\")\n        self.validate_identity(\"UNDROP SCHEMA IDENTIFIER('12345')\")\n        self.validate_identity(\"UNDROP DATABASE IDENTIFIER('12345')\")\n        self.assertIsInstance(parse_one(\"UNDROP TABLE t\", read=\"snowflake\"), exp.Undrop)\n\n    def test_drop_iceberg_table(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-140418-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_snowflake.py | grep import; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"undrop or drop\" 2>&1 | tail -15", "description": "Run targeted Snowflake drop/undrop tests"}
[tool_result] from unittest import mock
from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.parser import logger as parser_logger
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify_columns import quote_identifiers
from tests.dialects.test_dialect import Validator
..                                                           [100%]
2 passed, 94 deselected, 12 subtests passed in 0.14s
[assistant] Targeted tests pass. Running the full suite with the project's check command, plus the linter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff format --check sqlglot tests 2>&1 || <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py 2>&1) | tail -5; (<work>/env-sqlglot/bin/python -m ruff check sqlglot tests 2>&1 | tail -3)", "description": "Run full test suite and lint/format checks"}
[tool_result] ............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
....................................................................................................................................................................................................................................................... [ 63
…[145 chars elided]…
...................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 51.30s
237 files already formatted
All checks passed!
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Show changed files summary"}
[tool_result]  M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
 sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parsers/snowflake.py     | 27 +++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 23 +++++++++++++++++++++++
 6 files changed, 59 insertions(+)
[assistant] Snowflake `UNDROP` now parses and generates for all twelve object types, including the `IDENTIFIER(<id>)` form. The full suite passes (1121 tests, 18188 subtests), and ruff format and lint are clean. The changes are uncommitted in the worktree.

Parsing an `UNDROP` in Snowflake gives a new `exp.Undrop` node. Generating it writes back the same SQL.

- **Tokenizer:** `UNDROP` is a new keyword in the Snowflake tokenizer. It's also in Snowflake's `ID_VAR_TOKENS` and `ALIAS_TOKENS`, so `SELECT undrop FROM undrop` still parses as identifiers.
- **Parser:** `_parse_undrop` in `sqlglot/parsers/snowfla
…[176 chars elided]…
 falls back to `exp.Command`, so it round-trips as raw text instead of raising.
- **Expression and generator:** `exp.Undrop(this, kind)` lives in `sqlglot/expressions/ddl.py`. `undrop_sql` is in the Snowflake generator.
- **Tests:** `test_undrop` in `tests/dialects/test_snowflake.py` covers every kind, qualified names, and the `IDENTIFIER('12345')` form for TABLE, SCHEMA and DATABASE.

I couldn't run these statements against a live Snowflake account, so the tests check parse and generate round-trips only. The `IDENTIFIER(...)` form is validated by the round-trip, not by Snowflake accepting it.
