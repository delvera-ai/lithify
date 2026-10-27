# trajectory base-1

final message:
Snowflake `UNDROP` now parses into a real AST node and generates back out for all twelve object types, including the `IDENTIFIER(<id>)` form. The full suite passed after my last edit: `SUMMARY: 1121 passed, 18188 subtests passed`, `EXIT: 0`.

**What changed**
- **Token:** `UNDROP` is a new `TokenType` (`tokenizer_core.py`). Snowflake maps the keyword to it (`dialects/snowflake.py`). It is also added to `ID_VAR_TOKENS` in `parser.py`, so `undrop` still works as a column or table name (`SELECT undrop FROM undrop` round-trips).
- **Node:** `exp.Undrop(this=<Table>, kind=<str>)` in `expressions/ddl.py`. `kind` is the uppercase object type, e.g. `DYNAMIC TABLE`.
- **Parser:** `SnowflakeParser` registers `TokenType.UNDROP` in `STATEMENT_PARSERS`. `_parse_undrop` matches the kind from a `UNDROP_KINDS` tuple, then parses the name with `_parse_table_parts`. As with `DROP SCHEMA`, a schema name goes in the `db` slot. An unknown kind falls back to `exp.Command`, with the usual warning.
- **Generator:** `undrop_sql` in the base `generator.py`, auto-discovered by name, next to `drop_sql`.
- **Test:** `test_undrop` in `tests/dialects/test_snowflake.py`. It checks the node class and `kind` for every object type, plus the multi-part name, `IDENTIFIER(...)` and fallback cases.

**Checks**
- `ast_check.py` on `UNDROP TABLE IDENTIFIER('"01a2b3"')`: the node is `Undrop(this=Table(this=Anonymous(IDENTIFIER, ...)), kind=TABLE)`, and the round-trip has no `[DIFFERS]`.
- Ruff and mypy pass on the changed modules.

**Decision for you**
- Transpiling `UNDROP` to DuckDB or Postgres prints `UNDROP TABLE ...` unchanged. Neither engine has `UNDROP`, so there is no valid equivalent to emit. I followed the existing Snowflake `GET`/`PUT` precedent, which also passes through verbatim. If you would rather those targets get a warning or an error, that is a small change in the generator.

## events
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-ddl-statements/SKILL.md; echo ----; grep -rn -i \"undrop\" sqlglot/ tests/ | head -50; echo ----; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Read DDL skill and grep UNDROP references"}
[tool_result] ---
name: sqlglot-ddl-statements
description: Load when a task adds or changes parsing/generation of a DDL statement in sqlglot (CREATE / ALTER / DROP of a TABLE, VIEW, TYPE, SEQUENCE, FUNCTION, MACRO, INDEX, TRIGGER, …, including statements with several repeated clauses such as overloaded DuckDB macros), or when a statement "contains unsupported syntax. Falling back to parsing as a Command" and must become a real AST node (exp.Create, exp.Alter, …) in any dialect.
---

# DDL statements (exp.Cre
…[7014 chars elided]…
on -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md | head -80; echo ----; grep -n \"_parse_drop\\|def _parse_create\\|DROP\" sqlglot/parser.py | head -40; echo ----; ls sqlglot/parsers/ | head -50; grep -n \"DROP\\|Drop\\|_parse_create\\|STATEMENT_PARSERS\" sqlglot/parsers/snowflake.py | head -40", "description": "Read dialect skill and locate DROP parsing code"}
[tool_result] ---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — any change to a
…[6930 chars elided]…
use.py
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
758:    STATEMENT_PARSERS = {
759:        **parser.Parser.STATEMENT_PARSERS,
1008:    def _parse_create(self) -> exp.Create | exp.Command:
1009:        expression = super()._parse_create()
[tool_use Bash] {"command": "sed -n 2298,2350p sqlglot/parser.py; echo ----; sed -n 1000,1030p sqlglot/parsers/snowflake.py; echo ----; grep -n \"class Drop\\b\" -A 25 sqlglot/expressions/ddl.py; echo ----; grep -n \"def drop_sql\" -A 40 sqlglot/generator.py | head -60; echo ----; sed -n 750,800p sqlglot/parsers/snowflake.py", "description": "Read DROP parser, Snowflake create override, Drop node, drop generator"}
[tool_result]     def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
            return self._parse_as_command(start)

        concurrently = self._match_text_seq("
…[7831 chars elided]…
y()),
        "HYBRID": lambda self: self.expression(exp.HybridProperty()),
        "ICEBERG": lambda self: self.expression(exp.IcebergProperty()),
        "MASKING": lambda self: self.expression(exp.MaskingProperty()),
        "MATERIALIZED": lambda self: self.expression(exp.MaterializedProperty()),
        "NETWORK": lambda self: self.expression(exp.NetworkProperty()),
        "ROW": lambda self: (
            self.expression(exp.RowAccessProperty()) if self._match_text_seq("ACCESS") else None
[tool_use Bash] {"command": "grep -n \"GET\\b\\|PUT\\b\\|\\\"SHOW\\\"\" sqlglot/dialects/snowflake.py sqlglot/tokens.py sqlglot/tokens_*.py 2>/dev/null | head; echo ----; grep -rn \"class Restore\\|Flashback\\|class Undo\\|UNDELETE\\|class Get(\\|class Put(\" sqlglot/expressions/*.py | head; echo ----; grep -n \"IDENTIFIER\" sqlglot/parsers/snowflake.py sqlglot/parser.py sqlglot/dialects/snowflake.py | head; echo ----; grep -n \"def _parse_get\\|def _parse_put\\|def _parse_table_parts\\|def _parse_table_part\\b\" -A 12 sqlglot/parsers/snowflake.py sqlglot/parser.py | head -90; echo ----; grep -n \"class Get\\|class Put\" -A 12 sqlglot/expressions/*.py | head -40", "description": "Look up Snowflake statement tokenization and related nodes"}
[tool_result] (eval):1: no matches found: sqlglot/tokens_*.py
----
sqlglot/expressions/query.py:935:class Put(Expression):
sqlglot/expressions/query.py:939:class Get(Expression):
----
sqlglot/parsers/snowflake.py:1129:        if self._match_text_seq("IDENTIFIER", "("):
sqlglot/parsers/snowflake.py:1134:            return self.expression(exp.Anonymous(this="IDENTIFIER", expressions=[identifier]))
sqlglot/parser.py:574:        TokenType.OBJECT_IDENTIFIER,
sqlglot/parser.py:617:    } - {TokenType.IDENTIFIER}
sql
…[6954 chars elided]…
sions/query.py-936-    arg_types = {"this": True, "target": True, "properties": False}
sqlglot/expressions/query.py-937-
sqlglot/expressions/query.py-938-
sqlglot/expressions/query.py:939:class Get(Expression):
sqlglot/expressions/query.py-940-    arg_types = {"this": True, "target": True, "properties": False}
sqlglot/expressions/query.py-941-
sqlglot/expressions/query.py-942-
sqlglot/expressions/query.py-943-class Table(Expression, Selectable):
sqlglot/expressions/query.py-944-    arg_types = {
[tool_use Bash] {"command": "grep -rn '\"GET\"\\|\"SHOW\"\\|\"PUT\"\\|\"UNDROP\"\\|\"REFRESH\"' sqlglot/tokens.py sqlglot/dialects/snowflake.py sqlglot/tokenizer_core.py 2>/dev/null; grep -n \"GET = \\|PUT = \\|SHOW = \\|REFRESH\" sqlglot/tokens.py | head; echo ----; sed -n 1120,1140p sqlglot/parsers/snowflake.py; echo ----; grep -n \"UNDROP\\|undrop\" -ri tests/ | head; echo ----; grep -n \"class Snowflake\\|class Generator\\|class Parser\\|class Tokenizer\" sqlglot/dialects/snowflake.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py", "description": "Check Snowflake keyword tokenization for GET/PUT/SHOW"}
[tool_result] sqlglot/tokens.py:383:        "SHOW": TokenType.SHOW,
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.py:154:            "PUT": TokenType.PUT,
----
            table = table_from_rows

        return table

    def _parse_id_var(
        self,
        any_token: bool = True,
        tokens: Collection[TokenType] | None = None,
    ) -> exp.Expr | None:
        if self._match_text_seq("IDENTIFIER", "("):
            identifier = (
                sup
…[210 chars elided]…
entifier]))

        return super()._parse_id_var(any_token=any_token, tokens=tokens)

    def _parse_show_snowflake(
        self, this: str, terse: bool = False, iceberg: bool = False
    ) -> exp.Show:
----
----
sqlglot/dialects/snowflake.py:16:class Snowflake(Dialect):
sqlglot/dialects/snowflake.py:133:    class Tokenizer(tokens.Tokenizer):
sqlglot/parsers/snowflake.py:329:class SnowflakeParser(parser.Parser):
sqlglot/generators/snowflake.py:375:class SnowflakeGenerator(generator.Generator):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_undrop.py <<'EOF'\nimport sqlglot\nfor sql in [\"UNDROP TABLE t\", \"UNDROP DYNAMIC TABLE db.s.t\", \"UNDROP TABLE IDENTIFIER('\\\"01a2b3\\\"')\", \"UNDROP SCHEMA s\"]:\n    try:\n        print(repr(sqlglot.parse_o
…[314 chars elided]…
qlglot/tokens.py; echo ----; grep -n \"def _match_text_seq\" -A 12 sqlglot/parser.py | head -30; echo ----; sed -n 130,160p sqlglot/dialects/snowflake.py; echo ----; grep -n \"class Drop\" -B2 sqlglot/expressions/ddl.py | head -3; cat .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py | head -30", "description": "Probe current UNDROP behavior and inspect token and helper code"}
[tool_result] ERR UNDROP TABLE t ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
ERR UNDROP DYNAMIC TABLE db.s.t ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP DYNAMIC [4mTABLE[0m db.s.t
ERR UNDROP TABLE IDENTIFIER('"01a2b3"') ParseError Invalid expression / Unexpected token. Line 1, Col: 23.
  UNDROP TABLE [4mIDENTIFIER[0m('"01a2b3"')
ERR UNDROP SCHEMA s ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCH
…[2677 chars elided]…
s spelling was rewritten into another
                     function; that is a failed round-trip, not a normalisation.
Exit codes: 0 = parsed, no FUNCTION CHANGED; 1 = parse error (message printed);
2 = bad arguments or sqlglot not importable from the current directory;
4 = parsed, but at least one statement has FUNCTION CHANGED.
"""
import argparse
import os
import re
import sys
from collections import Counter

_CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _norm(sql: str) -> str:
[tool_use Bash] {"command": "grep -rn \"\\bGET\\b\" sqlglot/*.py | grep -v \"^sqlglot/dialects\" | head -5; grep -rln \"class TokenType\" sqlglot/; echo ----; grep -n \"    SHOW\\b\\|    PUT\\b\\|    COMMAND\\b\" sqlglot/tokens_core.py sqlglot/tokens.py 2>/dev/null | head", "description": "Find TokenType enum definition location"}
[tool_result] sqlglot/generator.py:5995:        # Snowflake GET/PUT statements:
sqlglot/generator.py:5997:        #   GET <internalStage> <file> <properties>
sqlglot/generator.py:6006:            return f"GET {target} {this}{props_sql}"
sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:839:        TokenType.GET,
sqlglot/tokenizer_core.py
----
[tool_use Bash] {"command": "grep -n \"class TokenType\" -A 5 sqlglot/tokenizer_core.py; grep -n \"    GET\\b\\|    PUT\\b\\|    SHOW\\b\\|    DROP\\b\\|    TAG\\b\\|    COMMAND\\b\" sqlglot/tokenizer_core.py; echo ----; sed -n 700,712p sqlglot/parser.py; sed -n 835,845p sqlglot/parser.py", "description": "Inspect TokenType enum members and parser token sets"}
[tool_result] 13:class TokenType(IntEnum):
14-    L_PAREN = auto()
15-    R_PAREN = auto()
16-    L_BRACKET = auto()
17-    R_BRACKET = auto()
18-    L_BRACE = auto()
257:    COMMAND = auto()
285:    DROP = auto()
306:    GET = auto()
386:    PUT = auto()
413:    SHOW = auto()
425:    TAG = auto()
----
        TokenType.FIRST,
        TokenType.FILE,
        TokenType.FILTER,
        TokenType.FINAL,
        TokenType.FORMAT,
        TokenType.FULL,
        TokenType.GET,
        TokenType.IDENTIFIER,
        TokenType.INOUT,
        TokenType.IS,
        TokenType.ISNULL,
        TokenType.INTERVAL,
        TokenType.KEEP,
        TokenType.CURRENT_CATALOG,
        TokenType.FILTER,
        TokenType.FIRST,
        TokenType.FORMAT,
        TokenType.GET,
        TokenType.GLOB,
        TokenType.IDENTIFIER,
        TokenType.INDEX,
        TokenType.ISNULL,
        TokenType.ILIKE,
        TokenType.INSERT,
[tool_use Bash] {"command": "grep -n \"UNIQUE = auto\\|UNNEST = auto\\|UNPIVOT = auto\\|UNCACHE = auto\\|UNION = auto\\|    TYPE = auto\\|    UPDATE = auto\" sqlglot/tokenizer_core.py; grep -n \"TokenType.PUT,\\|TokenType.GET,\\|TokenType.TAG,\" sqlglot/parser.py; sed -n 1085,1096p sqlglot/parser.py; grep -n \"def undrop\\|def drop_sql\" sqlglot/generator.py", "description": "Locate TokenType placement and parser token sets"}
[tool_result] 432:    TYPE = auto()
433:    UNCACHE = auto()
434:    UNION = auto()
435:    UNNEST = auto()
436:    UNPIVOT = auto()
437:    UPDATE = auto()
450:    UNIQUE = auto()
634:        TokenType.TAG,
706:        TokenType.GET,
732:        TokenType.PUT,
839:        TokenType.GET,
        TokenType.BEGIN: lambda self: self._parse_transaction(),
        TokenType.CACHE: lambda self: self._parse_cache(),
        TokenType.COMMENT: lambda self: self._parse_comment(),
        TokenType.COMMIT: lambda self:
…[74 chars elided]…
lf._parse_copy(),
        TokenType.CREATE: lambda self: self._parse_create(),
        TokenType.DELETE: lambda self: self._parse_delete(),
        TokenType.DESC: lambda self: self._parse_describe(),
        TokenType.DESCRIBE: lambda self: self._parse_describe(),
        TokenType.DROP: lambda self: self._parse_drop(),
        TokenType.GRANT: lambda self: self._parse_grant(),
        TokenType.REVOKE: lambda self: self._parse_revoke(),
1784:    def drop_sql(self, expression: exp.Drop) -> str:
[tool_use Bash] {"command": "grep -n \"_TOKENS.*= \\|_TOKENS: t.ClassVar\" sqlglot/parser.py | head -30; sed -n 160,175p sqlglot/dialects/snowflake.py; sed -n 1196,1225p sqlglot/parsers/snowflake.py", "description": "Locate token sets and Snowflake keyword and parse helpers"}
[tool_result] 441:    STRUCT_TYPE_TOKENS: t.ClassVar = {
448:    NESTED_TYPE_TOKENS: t.ClassVar = {
458:    ENUM_TYPE_TOKENS: t.ClassVar = {
465:    AGGREGATE_TYPE_TOKENS: t.ClassVar = {
470:    TYPE_TOKENS: t.ClassVar = {
608:    SUBQUERY_TOKENS: t.ClassVar = {
614:    RESERVED_TOKENS: t.ClassVar = {
666:    ID_VAR_TOKENS: t.ClassVar[set] = {
772:    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
786:    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_T
…[2828 chars elided]…
    )

    def _parse_location_property(self) -> exp.LocationProperty:
        self._match(TokenType.EQ)
        return self.expression(exp.LocationProperty(this=self._parse_location_path()))

    def _parse_file_location(self) -> exp.Expr | None:
        # Parse either a subquery or a staged file
        return (
            self._parse_select(table=True, parse_subquery_alias=False)
            if self._match(TokenType.L_PAREN, advance=False)
            else self._parse_table_parts()
        )
[tool_use Bash] {"command": "grep -n \"TokenType.UN\\|TokenType.UP\\|TokenType.TOP,\\|TokenType.TYPE,\\|TokenType.TAG,\" sqlglot/parser.py | head -20; sed -n 666,668p sqlglot/parser.py; sed -n 772,776p sqlglot/parser.py", "description": "Find UNION/UNNEST placement in parser token sets"}
[tool_result] 445:        TokenType.UNION,
580:        TokenType.UNKNOWN,
634:        TokenType.TAG,
647:        TokenType.TYPE,
653:        TokenType.UPDATE,
750:        TokenType.TOP,
753:        TokenType.UNIQUE,
754:        TokenType.UNNEST,
755:        TokenType.UNPIVOT,
756:        TokenType.UPDATE,
770:    } - {TokenType.UNION}
821:            TokenType.UNPIVOT,
858:        TokenType.UNNEST,
940:        TokenType.UNION,
1107:        TokenType.UNCACHE: lambda self: self._parse_uncache(),
1108:        To
…[113 chars elided]…
a self: self._parse_update(),
1136:        TokenType.UNICODE_STRING: lambda self, token: self.expression(
1385:                self._match(TokenType.UPDATE)
1569:    PRE_VOLATILE_TOKENS: t.ClassVar = {TokenType.CREATE, TokenType.REPLACE, TokenType.UNIQUE}
    ID_VAR_TOKENS: t.ClassVar[set] = {
        TokenType.ALL,
        TokenType.ANALYZE,
    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
        TokenType.ANTI,
        TokenType.ASOF,
        TokenType.FULL,
        TokenType.LEFT,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.UNIQUE,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,\n        TokenType.UPDATE,\n    }", "new_string": "        TokenType.UNDROP,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,\n        TokenType.UPDATE,\n    }"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:         TokenType.UNIQUE,
        TokenType.UNNEST,
        TokenType.UNPIVOT,
        TokenType.UPDATE,
    }</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "    @property\n    def kind(self) -> str | None:\n        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass DropPrimaryKey(Expression):", "new_string": "    @property\n    def kind(self) -> str | None:\n        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generator.py", "old_string": "        return f\"DROP{temporary}{materialized}{iceberg} {kind}{concurrently_sql}{exists_sql}{this}{on_cluster}{expressions}{cascade}{restrict}{constraints}{purge}{sync}\"\n", "new_string": "        return f\"DROP{temporary}{materialized}{iceberg} {kind}{concurrently_sql}{exists_sql}{this}{on_cluster}{expressions}{cascade}{restrict}{constraints}{purge}{sync}\"\n\n    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_location_property(self) -> exp.LocationProperty:", "new_string": "    def _parse_undrop(self) -> exp.Undrop | exp.Command:\n        start = self._prev\n        kind = next(\n            (kind f
…[37 chars elided]…
_match_text_seq(*kind.split())),\n            None,\n        )\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Undrop(\n                this=self._parse_table_parts(is_db_reference=kind == \"SCHEMA\"),\n                kind=kind,\n            )\n        )\n\n    def _parse_location_property(self) -> exp.LocationProperty:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 748,760p sqlglot/parser.py | cat -A | cut -c1-60; grep -n \"DESCRIBE_QUALIFIER_PARSERS: t.ClassVar\" sqlglot/parsers/snowflake.py", "description": "View parser token set lines near UNIQUE"}
[tool_result] cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
783:    DESCRIBE_QUALIFIER_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
[tool_use Bash] {"command": "sed -n 748,760p sqlglot/parser.py", "description": "View parser token set lines near UNIQUE"}
[tool_result]         TokenType.STREAMLIT,
        TokenType.TEMPORARY,
        TokenType.TOP,
        TokenType.TRUE,
        TokenType.TRUNCATE,
        TokenType.UNIQUE,
        TokenType.UNNEST,
        TokenType.UNPIVOT,
        TokenType.UPDATE,
        TokenType.USE,
        TokenType.VOLATILE,
        TokenType.WINDOW,
        TokenType.CURRENT_CATALOG,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.TRUNCATE,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,", "new_string": "        TokenType.TRUNCATE,\n        TokenType.UNDROP,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 780,783p sqlglot/parsers/snowflake.py", "description": "View lines before DESCRIBE_QUALIFIER_PARSERS"}
[tool_result]         ),
    }

    DESCRIBE_QUALIFIER_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        ),\n    }\n\n    DESCRIBE_QUALIFIER_PARSERS: t.ClassVar[dict[str, t.Callable]] = {", "new_string": "        ),\n    }\n\n    UNDROP_KINDS: t.ClassVar[tuple[str, ...]] = (\n        \"TABLE\",\n        \"SCHEMA\",\n        \"DATABASE\",\n        \"ACCOUNT\",\n        \"NOTEBOOK\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TAG\",\n        \"TYPE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n    )\n\n    DESCRIBE_QUALIFIER_PARSERS: t.ClassVar[dict[str, t.Callable]] = {"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_undrop.py <<'EOF'\nimport sqlglot\nfor sql in [\"UNDROP TABLE t\", \"UNDROP DYNAMIC TABLE db.s.t\", \"UNDROP TABLE IDENTIFIER('\\\"01a2b3\\\"')\", \"UNDROP SCHEMA s\", \"UNDROP ICEBERG TABLE x\", \"UNDROP EXTERNAL 
…[195 chars elided]…
undrop FROM undrop\"]:\n    try:\n        e = sqlglot.parse_one(sql, read=\"snowflake\")\n        print(sql, \"=>\", repr(e)[:200].replace(\"\\n\",\" \"), \"|\", e.sql(\"snowflake\"), \"|\", e.sql(\"duckdb\"))\n    except Exception as ex:\n        print(\"ERR\", sql, type(ex).__name__, str(ex)[:150])\nEOF\nPYTHONPATH=. $PY /tmp/probe_undrop.py", "description": "Probe UNDROP forms after the edits"}
[tool_result] 'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
UNDROP TABLE t => Undrop(   this=Table(     this=Identifier(this=t, quoted=False)),   kind=TABLE) | UNDROP TABLE t | UNDROP TABLE t
UNDROP DYNAMIC TABLE db.s.t => Undrop(   this=Table(     this=Identifier(this=t, quoted=False),     db=Identifier(this=s, quoted=False),     catalog=Identifier(this=db, quoted=False)),   kind=DYNAMIC TABLE) | UNDROP DYNAMIC TABLE db.s.t | UNDROP DYNAMIC TABLE db.s.t
UNDROP TABLE IDEN
…[1547 chars elided]…
ROP STREAMLIT st
UNDROP DATABASE d => Undrop(   this=Table(     this=Identifier(this=d, quoted=False)),   kind=DATABASE) | UNDROP DATABASE d | UNDROP DATABASE d
UNDROP FOO x => Command(this=UNDROP, expression=FOO x) | UNDROP FOO x | UNDROP FOO x
SELECT undrop FROM undrop => Select(   expressions=[     Column(       this=Identifier(this=undrop, quoted=False))],   from_=From(     this=Table(       this=Identifier(this=undrop, quoted=False)))) | SELECT undrop FROM undrop | SELECT undrop FROM undrop
[tool_use Bash] {"command": "grep -n \"def test_ddl\\|def test_get\\|def test_put\\|def test_show\" tests/dialects/test_snowflake.py; grep -n \"def test_ddl\" -A 6 tests/dialects/test_snowflake.py | head -12", "description": "Locate Snowflake DDL test method"}
[tool_result] 4238:    def test_ddl(self):
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
5359:    def test_show_primary_keys(self):
…[205 chars elided]…
:    def test_get_from_stage(self):
6038:    def test_get_extract(self):
6246:    def test_get_bit(self):
4238:    def test_ddl(self):
4239-        for constraint_prefix in ("WITH ", ""):
4240-            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4241-                self.validate_identity(
4242-                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
4243-                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
4244-                )
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_snowflake.py; sed -n 5200,5204p tests/dialects/test_snowflake.py", "description": "Check test imports and insertion point"}
[tool_result] from unittest import mock

from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.parser import logger as parser_logger
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify_columns import quote_identifiers
from tests.dialects.test_dialect import Validator


class TestSnowflake(Validator):
    maxDiff = None
)""",
                            pretty=True,
                        )

    def test_show_users(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_show_users(self):", "new_string": "    def test_undrop(self):\n        for kind in (\n            \"TABLE\",\n            \"SCHEMA\",\n            \"DATABASE\",\n            \"ACCOUNT\",\n   
…[481 chars elided]…
  self.validate_identity(\"UNDROP TABLE db.s.t\")\n        self.validate_identity(\"UNDROP SCHEMA db.s\")\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('\\\"01a2b3\\\"')\")\n        self.validate_identity(\"UNDROP DYNAMIC TABLE IDENTIFIER('\\\"01a2b3\\\"')\")\n        self.assertIsInstance(parse_one(\"UNDROP FOO x\", read=\"snowflake\"), exp.Command)\n\n    def test_show_users(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-111204-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"undrop\" 2>&1 | tail -15; echo ----; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -3", "description": "Run new UNDROP test and full Snowflake test file"}
[tool_result] .                                                            [100%]
1 passed, 95 deselected, 12 subtests passed in 0.12s
----
............................... [ 32%]
.................................................................                                                     [100%]
96 passed, 1580 subtests passed in 0.47s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read snowflake --write duckdb,postgres --repr \"UNDROP TABLE IDENTIFIER('\\\"01a2b3\\\"')\"; echo \"exit $?\"; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read snowflake --write duckdb \"UNDROP DYNAMIC TABLE db.s.t\"; echo \"exit $?\"; (ruff --version && ruff check sqlglot tests/dialects/test_snowflake.py && ruff format --check sqlglot tests/dialects/test_snowflake.py) 2>&1 | tail -8", "description": "Run AST check on examples and lint changed files"}
[tool_result] == UNDROP TABLE IDENTIFIER('"01a2b3"')
  node: Undrop
  Undrop(
    this=Table(
      this=Anonymous(
        this=IDENTIFIER,
        expressions=[
          Literal(this='"01a2b3"', is_string=True)])),
    kind=TABLE)
  snowflake (round-trip): UNDROP TABLE IDENTIFIER('"01a2b3"')
  duckdb: UNDROP TABLE IDENTIFIER('"01a2b3"')
  postgres: UNDROP TABLE IDENTIFIER('"01a2b3"')
exit 0
== UNDROP DYNAMIC TABLE db.s.t
  node: Undrop
  snowflake (round-trip): UNDROP DYNAMIC TABLE db.s.t
  duckdb: UNDROP DYNAMIC TABLE db.s.t
exit 0
ruff 0.15.6
All checks passed!
177 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:42:44 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-b902e88061.log
ELAPSED: 52s
SUMMARY: 1121 passed, 18188 subtests passed in 51.54s
EXIT: 0
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parsers/snowflake.py sqlglot/expressions/ddl.py sqlglot/generator.py 2>&1 | tail -5; git status --short", "description": "Run mypy on changed modules and show git status", "timeout": 300000}
[tool_result] Success: no issues found in 3 source files
 M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
[assistant] Snowflake `UNDROP` now parses into a real AST node and generates back out for all twelve object types, including the `IDENTIFIER(<id>)` form. The full suite passed after my last edit: `SUMMARY: 1121 passed, 18188 subtests passed`, `EXIT: 0`.

**What changed**
- **Token:** `UNDROP` is a new `TokenType` (`tokenizer_core.py`). Snowflake maps the keyword to it (`dialects/snowflake.py`). It is also added to `ID_VAR_TOKENS` in `parser.py`, so `undrop` still works as a column or table name (`SELECT undrop FROM undrop` round-trips).
- **Node:** `exp.Undrop(this=<Table>, kind=<str>)` in `expressions/dd
…[683 chars elided]…
*Checks**
- `ast_check.py` on `UNDROP TABLE IDENTIFIER('"01a2b3"')`: the node is `Undrop(this=Table(this=Anonymous(IDENTIFIER, ...)), kind=TABLE)`, and the round-trip has no `[DIFFERS]`.
- Ruff and mypy pass on the changed modules.

**Decision for you**
- Transpiling `UNDROP` to DuckDB or Postgres prints `UNDROP TABLE ...` unchanged. Neither engine has `UNDROP`, so there is no valid equivalent to emit. I followed the existing Snowflake `GET`/`PUT` precedent, which also passes through verbatim. If you would rather those targets get a warning or an error, that is a small change in the generator.
