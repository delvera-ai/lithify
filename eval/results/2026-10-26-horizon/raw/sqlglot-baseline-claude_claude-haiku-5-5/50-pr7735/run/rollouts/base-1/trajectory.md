# trajectory base-1

final message:
UNDROP now parses and generates for all twelve Snowflake object types you listed, including the `IDENTIFIER('…')` form. The full test suite passes (1121 passed) and ruff format and lint are clean on the changed files. I did not commit.

Changes:

- **`sqlglot/expressions/ddl.py`**: new `Undrop` expression with an optional `this` (the object name) and a required `kind`.
- **`sqlglot/parsers/snowflake.py`**: `_parse_statement` recognises a leading `UNDROP`. `_parse_undrop` matches the kind against a `UNDROP_KINDS` tuple, including multi-word kinds like `DYNAMIC TABLE`, `ICEBERG TABLE` and `EXTERNAL VOLUME`. An unrecognised kind falls back to `exp.Command`, as `DROP` does.
- **`sqlglot/generators/snowflake.py`**: `undrop_sql` writes `UNDROP <kind> [<name>]`.
- **`tests/dialects/test_snowflake.py`**: new `test_undrop` round-trips every kind, a schema-qualified table name, `UNDROP ACCOUNT` with no name, and `UNDROP TABLE IDENTIFIER('12345')`.

Decisions you may want to redirect:

- The object name is optional so that a bare `UNDROP ACCOUNT` parses. I'm not certain Snowflake documents a nameless account form, so I kept it lenient.
- The generator lives in the Snowflake dialect rather than the base generator, since the syntax is Snowflake-specific.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"undrop\\|UNDROP\" sqlglot/ tests/ | head -30 && grep -n \"\\\"ALTER\\\"\\|TokenType.ALTER\\|def _parse_create\\|_parse_drop\\|def _parse_show_snowflake\\|Snowflake.*Parser\" sqlglot/dialects/snowflake.py | head -40", "description": "Check repo state and search for existing UNDROP handling"}
[tool_result] 10:    SnowflakeParser,
131:    Parser = SnowflakeParser
[tool_use Bash] {"command": "git status --short; grep -rn -i \"undrop\" sqlglot/ tests/ ; echo \"---\"; grep -n \"Drop\\|DROP\\|ALTER\\|Command\\|STATEMENT_PARSERS\\|def _parse_drop\" sqlglot/dialects/snowflake.py | head -60; echo ---; grep -n \"def _parse_drop\\|def _parse_create\\|def _parse_alter\\|TokenType.DROP\" sqlglot/parser.py | head", "description": "Search for UNDROP and DROP/ALTER handling in Snowflake"}
[tool_result] ---
27:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
---
1094:        TokenType.DROP: lambda self: self._parse_drop(),
2298:    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2351:    def _parse_create(self) -> exp.Create | exp.Command:
3334:    def _parse_create_like(self) -> exp.LikeProperty | None:
8709:    def _parse_drop_column(self) -> exp.Drop | exp.Command | None:
8710:        drop = self._parse_drop() if self._match(TokenType.DROP) else None
8715:    def _parse_alter_drop_action(self) -> exp.Expr | None:
8719:    def _parse_drop_partition(self, exists: bool | None = None) -> exp.DropPartition:
8724:    def _parse_alter_table_add(self) -> list[exp.Expr]:
8763:    def _parse_alter_table_alter(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 2298,2350p sqlglot/parser.py; echo ----; sed -n 1080,1110p sqlglot/dialects/snowflake.py; echo ---; grep -n \"class Drop\\|class Undrop\\|class Restore\" sqlglot/expressions.py; grep -n \"def drop_sql\\|def undrop\" sqlglot/generator.py; grep -n \"UNDROP\\|undrop\" sqlglot/tokens.py sqlglot/dialects/*.py | head", "description": "Read drop parser and related expression classes"}
[tool_result]     def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
            return self._parse_as_command(start)

        concurrently = self._match_text_seq("
…[1199 chars elided]…
ncurrently=concurrently,
                sync=self._match_text_seq("SYNC"),
                iceberg=iceberg,
            )
        )

    def _parse_exists(self, not_: bool = False) -> bool | None:
        return (
            self._match_text_seq("IF")
            and (not not_ or self._match(TokenType.NOT))
            and self._match(TokenType.EXISTS)
        )

----
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
1784:    def drop_sql(self, expression: exp.Drop) -> str:
[tool_use Bash] {"command": "ls sqlglot/ sqlglot/expressions* 2>/dev/null | head -80; grep -rn \"^class Drop\\|^class Command\\|^class Use\\b\" sqlglot/ ; sed -n 1085,1100p sqlglot/dialects/snowflake.py; grep -n \"STATEMENT_PARSERS\" sqlglot/parser.py | head -3; grep -n \"TokenType.ALTER\\|TokenType.DROP\\|UNDROP\" sqlglot/parser.py sqlglot/tokens.py | head; grep -rn \"^class Drop(\" -A 30 sqlglot/ | head -45", "description": "Locate expression definitions and statement parser table"}
[tool_result] sqlglot/:
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
sqlglot/expres
…[2145 chars elided]…
args.get("kind")
sqlglot/expressions/ddl.py-366-        return kind and kind.upper()
sqlglot/expressions/ddl.py-367-
sqlglot/expressions/ddl.py-368-
sqlglot/expressions/ddl.py-369-class DropPrimaryKey(Expression):
sqlglot/expressions/ddl.py-370-    arg_types = {}
sqlglot/expressions/ddl.py-371-
sqlglot/expressions/ddl.py-372-
sqlglot/expressions/ddl.py-373-class Command(Expression):
sqlglot/expressions/ddl.py-374-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/ddl.py-375-
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && $PY -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP DYNAMIC TABLE t','UNDROP ICEBERG TABLE t','UNDROP EXTERNAL VOLUME v','UNDROP TABLE IDENTIFIER(\\'12345\\')','UNDROP TAG t']:\n    try:\n        e=sqlglot.parse_one(s, read='snowflake'); print(repr(e)[:200])\n    except Exception as ex: print(s, '->', type(ex).__name__, str(ex)[:150])\n\"; grep -n \"ParseError\\|_parse_as_command\" sqlglot/parser.py | head -5; grep -rn \"DROP\" tests/dialects/test_snowflake.py | head -20", "description": "Reproduce UNDROP parse errors and check existing tests"}
[tool_result] <work>/env-sqlglot/bin/python
UNDROP TABLE t -> ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
UNDROP SCHEMA s -> ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
UNDROP DATABASE d -> ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
  UNDROP DATABASE [4md[0m
UNDROP DYN
…[990 chars elided]…
"
tests/dialects/test_snowflake.py:4394:        for action in ("SET", "DROP"):
tests/dialects/test_snowflake.py:5352:        ast = self.validate_identity("DROP ICEBERG TABLE t")
tests/dialects/test_snowflake.py:5354:        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
tests/dialects/test_snowflake.py:5355:        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
tests/dialects/test_snowflake.py:5357:        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")
[tool_use Bash] {"command": "sed -n 2262,2297p sqlglot/parser.py; echo ----; grep -rn \"def _parse_statement\" sqlglot/ ; grep -rn \"_match_text_seq(\\\"[A-Z]*\\\")\" sqlglot/dialects/snowflake.py | head -3; grep -n \"IDENTIFIER\" sqlglot/dialects/snowflake.py | head; grep -n \"class Parser\\|STATEMENT_PARSERS\\|FUNCTIONS = \\|class Generator\" sqlglot/dialects/snowflake.py", "description": "Inspect statement dispatch and Snowflake IDENTIFIER handling"}
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
…[522 chars elided]…
f expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

----
sqlglot/parser.py:2274:    def _parse_statement(self) -> exp.Expr | None:
sqlglot/parsers/exasol.py:130:    def _parse_statement(self) -> exp.Expr | None:
sqlglot/parsers/prql.py:78:    def _parse_statement(self) -> exp.Expr | None:
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators; sed -n 125,145p sqlglot/parsers/exasol.py; echo ----; grep -n \"STATEMENT_PARSERS\\|def _parse_statement\\|IDENTIFIER\\|class \\|def _parse_drop\\|_parse_drop\" sqlglot/parsers/snowflake.py | head -40; echo ---; grep -n \"class \\|def drop_sql\" sqlglot/generators/snowflake.py | head; grep -n \"def drop_sql\" -A 3 sqlglot/generator.py", "description": "Inspect Snowflake parser and generator module layout"}
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
…[1295 chars elided]…
9:        **parser.Parser.STATEMENT_PARSERS,
1129:        if self._match_text_seq("IDENTIFIER", "("):
1134:            return self.expression(exp.Anonymous(this="IDENTIFIER", expressions=[identifier]))
---
375:class SnowflakeGenerator(generator.Generator):
1784:    def drop_sql(self, expression: exp.Drop) -> str:
1785-        this = self.sql(expression, "this")
1786-        expressions = self.expressions(expression, flat=True)
1787-        expressions = f" ({expressions})" if expressions else ""
[tool_use Bash] {"command": "sed -n 1120,1140p sqlglot/parsers/snowflake.py; echo ----; sed -n 750,775p sqlglot/parsers/snowflake.py; echo ---; grep -n \"_parse_drop\\|def _parse_table_parts\" sqlglot/parsers/*.py | head; echo ---; sed -n 1784,1800p sqlglot/generator.py; echo; grep -n \"def drop_sql\\|def undrop\" sqlglot/generators/*.py | head; sed -n 340,368p sqlglot/expressions/ddl.py", "description": "Read Snowflake IDENTIFIER parsing and drop generation"}
[tool_result]             table = table_from_rows

        return table

    def _parse_id_var(
        self,
        any_token: bool = True,
        tokens: Collection[TokenType] | None = None,
    ) -> exp.Expr | None:
        if self._match_text_seq("IDENTIFIER", "("):
            identifier = (
                super()._parse_id_var(any_token=any_token, tokens=tokens) or self._parse_string()
            )
            self._match_r_paren()
            return self.expression(exp.Anonymous(this="IDENTIFIER", 
…[2582 chars elided]…
       "this": False,
        "kind": False,
        "expressions": False,
        "exists": False,
        "temporary": False,
        "materialized": False,
        "cascade": False,
        "restrict": False,
        "constraints": False,
        "purge": False,
        "cluster": False,
        "concurrently": False,
        "sync": False,
        "iceberg": False,
    }

    @property
    def kind(self) -> str | None:
        kind = self.args.get("kind")
        return kind and kind.upper()
[tool_use Bash] {"command": "grep -n \"def _parse_as_command\" -A 8 sqlglot/parser.py; grep -n \"def _match_text_seq\" -A 22 sqlglot/parser.py | head -30; grep -n \"class ShowSnowflake\\|class Show(\" sqlglot/expressions/*.py; grep -n \"SHOW_PARSERS\\|_parse_show_snowflake\" sqlglot/parsers/snowflake.py | head -3; grep -n \"def show_sql\\|def command_sql\" -A4 sqlglot/generators/snowflake.py sqlglot/generator.py | head -20", "description": "Check helper signatures for command fallback and text matching"}
[tool_result] 9278:    def _parse_as_command(self, start: Token) -> exp.Command:
9279-        while self._curr:
9280-            self._advance()
9281-        text = self._find_sql(start, self._prev)
9282-        size = len(start.text)
9283-        self._warn_unsupported()
9284-        return exp.Command(this=text[:size], expression=text[size:])
9285-
9286-    def _parse_dict_property(self, this: str) -> exp.DictProperty:
1955:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1956-     
…[1641 chars elided]…
sqlglot/generator.py-4078-
sqlglot/generator.py-4079-    def comment_sql(self, expression: exp.Comment) -> str:
sqlglot/generator.py-4080-        this = self.sql(expression, "this")
--
sqlglot/generator.py:5986:    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generator.py-5987-        self.unsupported("Unsupported SHOW statement")
sqlglot/generator.py-5988-        return ""
sqlglot/generator.py-5989-
sqlglot/generator.py-5990-    def install_sql(self, expression: exp.Install) -> str:
[assistant] Snowflake has no UNDROP handling today, and `IDENTIFIER(...)` already parses as a name. I'll add an `Undrop` expression, a Snowflake statement parser, and a generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "        return kind and kind.upper()\n\n\nclass DropPrimaryKey(Expression):", "new_string": "        return kind and kind.upper()\n\n\nclass Undrop(Expression):\n    arg_types = {\"this\": False, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_show_snowflake(\n        self, this: str, terse: bool = False, iceberg: bool = False\n    ) -> exp.Show:", "new_string": "    def _parse_statement(self) -> exp.Expr | None:\n        # https://d
…[403 chars elided]…
atch_text_seq(*kind.split(\" \"))\n            ),\n            None,\n        )\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Undrop(this=self._parse_table_parts(schema=True), kind=kind)\n        )\n\n    def _parse_show_snowflake(\n        self, this: str, terse: bool = False, iceberg: bool = False\n    ) -> exp.Show:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,\n        TokenType.GET: lambda self: self._parse_get(),\n        TokenType.PUT: lambda self: self._parse_put(),\n        TokenType.SHOW: l
…[214 chars elided]…
elf: self._parse_put(),\n        TokenType.SHOW: lambda self: self._parse_show(),\n    }\n\n    UNDROP_KINDS = (\n        \"DYNAMIC TABLE\",\n        \"ICEBERG TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"TABLE\",\n        \"SCHEMA\",\n        \"DATABASE\",\n        \"ACCOUNT\",\n        \"NOTEBOOK\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TAG\",\n        \"TYPE\",\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now the generator, placed next to the Snowflake-specific statement generators.
[tool_use Bash] {"command": "sed -n 836,840p sqlglot/generators/snowflake.py && grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py | head; grep -n \"ddl\" sqlglot/expressions/__init__.py | head -3", "description": "Locate generator insertion point and expression exports"}
[tool_result]         )

        return f"{value}{explode}{alias}"

    def show_sql(self, expression: exp.Show) -> str:
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
27:from sqlglot.generator import unsupported_args
28:from sqlglot.helper import find_new_name, flatten, seq_get
29:from sqlglot.optimizer.scope import build_scope, find_all_in_scope
30:from sqlglot.parsers.snowflake import (
36:from sqlglot.tokens import TokenType
37:from collections import defaultdict
19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "        return f\"{value}{explode}{alias}\"\n\n    def show_sql(self, expression: exp.Show) -> str:", "new_string": "        return f\"{value}{explode}{alias}\"\n\n    def undrop_sql(self, expression: exp.Undrop) -> str:\n        this = self.sql(expression, \"this\")\n        this = f\" {this}\" if this else \"\"\n        return f\"UNDROP {expression.name.upper()}{this}\"\n\n    def show_sql(self, expression: exp.Show) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] I used `expression.name`, which reads `this`, not `kind`. Fixing that to read the kind argument directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "        this = f\" {this}\" if this else \"\"\n        return f\"UNDROP {expression.name.upper()}{this}\"", "new_string": "        this = f\" {this}\" if this else \"\"\n        return f\"UNDROP {expression.args['kind']}{this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases=['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP DYNAMIC TABLE t','UNDROP ICEBERG TABLE t','UNDROP EXTERNAL VOLUME v','UNDROP TABLE IDENTIFIER(\\'12345\\')','UND
…[48 chars elided]…
UNDROP SNAPSHOT s','UNDROP STREAMLIT s','UNDROP ACCOUNT','UNDROP ACCOUNT a','UNDROP FOO x']\nfor s in cases:\n    try:\n        e=sqlglot.parse_one(s, read='snowflake'); print(s,'=>',type(e).__name__, e.sql('snowflake'))\n    except Exception as ex: print(s, '->', type(ex).__name__, str(ex)[:120].replace(chr(10),' '))\n\"", "description": "Verify UNDROP parsing and generation across object kinds"}
[tool_result] 'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
UNDROP TABLE t => Undrop UNDROP TABLE t
UNDROP TABLE db.s.t => Undrop UNDROP TABLE db.s.t
UNDROP SCHEMA s => Undrop UNDROP SCHEMA s
UNDROP DATABASE d => Undrop UNDROP DATABASE d
UNDROP DYNAMIC TABLE t => Undrop UNDROP DYNAMIC TABLE t
UNDROP ICEBERG TABLE t => Undrop UNDROP ICEBERG TABLE t
UNDROP EXTERNAL VOLUME v => Undrop UNDROP EXTERNAL VOLUME v
UNDROP TABLE IDENTIFIER('12345') => Undrop UNDROP TABLE IDENTIFIER('12345')
UNDROP TAG t => Undrop UNDROP TAG t
UNDROP TYPE t => Undrop UNDROP TYPE t
UNDROP NOTEBOOK n => Undrop UNDROP NOTEBOOK n
UNDROP SNAPSHOT s => Undrop UNDROP SNAPSHOT s
UNDROP STREAMLIT s => Undrop UNDROP STREAMLIT s
UNDROP ACCOUNT -> ParseError Expected table name but got <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, co
UNDROP ACCOUNT a => Undrop UNDROP ACCOUNT a
UNDROP FOO x => Command UNDROP FOO x
[assistant] Bare `UNDROP ACCOUNT` (no name) fails because the table-name parse runs unconditionally. Making the name optional.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return self.expression(\n            exp.Undrop(this=self._parse_table_parts(schema=True), kind=kind)\n        )", "new_string": "        this = self._parse_table_parts(schema=True) if self._curr else None\n        return self.expression(exp.Undrop(this=this, kind=kind))"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now adding tests to the Snowflake dialect test file, next to the existing ICEBERG DROP tests.
[tool_use Bash] {"command": "sed -n 5345,5362p tests/dialects/test_snowflake.py; grep -n \"    def test_\" tests/dialects/test_snowflake.py | awk -F: '$1>5340' | head -3", "description": "View test context around existing DROP ICEBERG tests"}
[tool_result]             write={
                "snowflake": "ALTER ICEBERG TABLE t RENAME TO x",
                "duckdb": "ALTER TABLE t RENAME TO x",
            },
        )

    def test_drop_iceberg_table(self):
        ast = self.validate_identity("DROP ICEBERG TABLE t")
        self.assertTrue(ast.args["iceberg"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
        self.assertTrue(ast.args["restrict"])
        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")

    def test_show_primary_keys(self):
        self.validate_identity("SHOW PRIMARY KEYS")
        self.validate_identity("SHOW PRIMARY KEYS IN ACCOUNT")
        self.validate_identity("SHOW PRIMARY KEYS IN DATABASE")
5351:    def test_drop_iceberg_table(self):
5359:    def test_show_primary_keys(self):
5378:    def test_show_views(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n\n    def test_show_primary_keys(self):", "new_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRI
…[326 chars elided]…
       \"EXTERNAL VOLUME\",\n            \"ICEBERG TABLE\",\n        ):\n            with self.subTest(kind):\n                self.validate_identity(f\"UNDROP {kind} t\")\n\n        self.validate_identity(\"UNDROP TABLE db.schema.t\")\n        self.validate_identity(\"UNDROP ACCOUNT\")\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('12345')\")\n\n    def test_show_primary_keys(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-183620-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"undrop or iceberg\" 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run new Snowflake tests and then the full test suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bidrpeyg9). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-183620-snowflake-dialect-snowflake-s-ti-base-1/f026656b-58b5-41c6-8301-562d00c93083/tasks/bidrpeyg9.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "sleep 5; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-b63a38b63828-20261026-183620-snowflake-dialect-snowflake-s-ti-base-1/f026656b-58b5-41c6-8301-562d00c93083/tasks/bidrpeyg9.output | tail -15", "description": "Check output of the background full test run"}
[tool_result] ...                                                        [100%]
3 passed, 93 deselected, 14 subtests passed in 0.13s
[assistant] The new tests pass (3 passed, 14 subtests). The full suite is still running in the background, so I'll wait for it to finish.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 900 $PY -m pytest -q -p no:cacheprovider --color=no -x 2>&1 | tail -15", "description": "Run full test suite with extended timeout", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] ............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
....................................................................................................................................................................................................................................................... [ 63
…[108 chars elided]…
........ [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 71.84s (0:01:11)
[assistant] The full suite passes (1121 passed). Next I'll run the linter and formatter on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff --version || $PY/python -m ruff --version) 2>&1; F=\"sqlglot/expressions/ddl.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py\"; $PY/python -m ruff format --check $F 2>&1 | tail -3; $PY/python -m ruff check $F 2>&1 | tail -3; git status --short", "description": "Run ruff format and lint checks on changed files"}
[tool_result] ruff 0.15.6
error: Failed to format sqlglot/expressions/ddl.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py: No such file or directory (os error 2)
--> sqlglot/expressions/ddl.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py:1:1

Found 1 error.
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[assistant] The shell is zsh, so the unquoted file list didn't split. Re-running with explicit paths.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/ruff; $R format --check sqlglot/expressions/ddl.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py; $R check sqlglot/expressions/ddl.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py tests/dialects/test_snowflake.py", "description": "Check formatting and lint on changed files"}
[tool_result] Would reformat: sqlglot/parsers/snowflake.py
1 file would be reformatted, 3 files already formatted
All checks passed!
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/ruff; $R format sqlglot/parsers/snowflake.py && git diff sqlglot/parsers/snowflake.py && $R format --check sqlglot/parsers/snowflake.py && PY=<work>/env-sqlglot/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -2", "description": "Apply ruff formatting and rerun Snowflake tests", "timeout": 300000}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parsers/snowflake.py b/sqlglot/parsers/snowflake.py
index 8c3fed5c3..d00be3b64 100644
--- a/sqlglot/parsers/snowflake.py
+++ b/sqlglot/parsers/snowflake.py
@@ -762,6 +762,21 @@ class SnowflakeParser(parser.Parser):
         TokenType.SHOW: lambda self: self._parse_show(),
     }
 
+    UNDROP_KINDS = (
+        "DYNAMIC TABLE",
+        "ICEBERG TABLE",
+        "EXTERNAL VOLUME",
+        "TABLE",
+        "SCHEMA",
+        "DATABASE",
+        "ACCOUNT"
…[904 chars elided]…
     return self._parse_as_command(start)
+
+        this = self._parse_table_parts(schema=True) if self._curr else None
+        return self.expression(exp.Undrop(this=this, kind=kind))
+
     def _parse_show_snowflake(
         self, this: str, terse: bool = False, iceberg: bool = False
     ) -> exp.Show:
1 file already formatted
.................................................................                                                     [100%]
96 passed, 1580 subtests passed in 0.60s
[assistant] UNDROP now parses and generates for all twelve Snowflake object types you listed, including the `IDENTIFIER('…')` form. The full test suite passes (1121 passed) and ruff format and lint are clean on the changed files. I did not commit.

Changes:

- **`sqlglot/expressions/ddl.py`**: new `Undrop` expression with an optional `this` (the object name) and a required `kind`.
- **`sqlglot/parsers/snowflake.py`**: `_parse_statement` recognises a leading `UNDROP`. `_parse_undrop` matches the kind against a `UNDROP_KINDS` tuple, including multi-word kinds like `DYNAMIC TABLE`, `ICEBERG TABLE` and `EXTER
…[61 chars elided]…
, as `DROP` does.
- **`sqlglot/generators/snowflake.py`**: `undrop_sql` writes `UNDROP <kind> [<name>]`.
- **`tests/dialects/test_snowflake.py`**: new `test_undrop` round-trips every kind, a schema-qualified table name, `UNDROP ACCOUNT` with no name, and `UNDROP TABLE IDENTIFIER('12345')`.

Decisions you may want to redirect:

- The object name is optional so that a bare `UNDROP ACCOUNT` parses. I'm not certain Snowflake documents a nameless account form, so I kept it lenient.
- The generator lives in the Snowflake dialect rather than the base generator, since the syntax is Snowflake-specific.
