# trajectory base-1

final message:
`file(...)` now parses as a table function in the ClickHouse dialect and round-trips unchanged. Your example outputs `... FROM file('base/dir/*.parquet', Parquet)`.

**Cause:** `file` tokenizes as `TokenType.FILE`, which isn't in the ClickHouse parser's `FUNC_TOKENS`. So `file(` was never parsed as a function call and fell through to a table named `file` with the arguments as an alias list.

**Fix:** I added `TokenType.FILE` to `FUNC_TOKENS` in `sqlglot/parsers/clickhouse.py`. I scoped it to ClickHouse rather than the base parser, since the reported bug is ClickHouse-only.

**Test:** I added `test_file_table_function` to `tests/dialects/test_clickhouse.py`. It covers your exact statement, a `file('a.csv', CSV)` table function, and a bare `file` column to confirm it still works as an identifier.

**Verification:** The full suite passes with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/`: 1115 passed, 18164 subtests passed.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n '\"FILE\"\\|FILE\\b\\|TokenType.FILE\\|\"file\"' sqlglot/dialects/clickhouse.py sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py | head -40; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')\nprint(repr(e))\nprint(e.sql(dialect='clickhouse'))\n\"", "description": "Search file handling in ClickHouse dialect and reproduce"}
[tool_result] sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
sqlglot/parser.py:622:        TokenType.FILE_FORMAT,
sqlglot/parser.py:701:        TokenType.FILE,
sqlglot/parser.py:8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
Select(
  expressions=[
    Column(
      this=Identifier(this=c1, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=file, quoted=False),
      alias=TableAlias(
        columns=[
          Identifier(this='base/dir/*.parquet', quoted=True),
          Identifier(this=Parquet, quoted=False)]))))
SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet)
[tool_use Bash] {"command": "sed -n 600,630p sqlglot/parser.py; sed -n 690,710p sqlglot/parser.py; grep -n \"FILE\\b\" sqlglot/tokens.py sqlglot/dialects/*.py | head -30; grep -n \"TokenType.FILE\\b\" sqlglot/parser.py", "description": "Inspect parser token sets referencing FILE"}
[tool_result]     SUBQUERY_PREDICATES: t.ClassVar = {
        TokenType.ANY: exp.Any,
        TokenType.ALL: exp.All,
        TokenType.EXISTS: exp.Exists,
        TokenType.SOME: exp.Any,
    }

    SUBQUERY_TOKENS: t.ClassVar = {
        TokenType.SELECT,
        TokenType.WITH,
        TokenType.FROM,
    }

    RESERVED_TOKENS: t.ClassVar = {
        *Tokenizer.SINGLE_TOKENS.values(),
        TokenType.SELECT,
    } - {TokenType.IDENTIFIER}

    DB_CREATABLES: t.ClassVar = {
        TokenType.DATABASE,
  
…[624 chars elided]…
e.FINAL,
        TokenType.FORMAT,
        TokenType.FULL,
        TokenType.GET,
        TokenType.IDENTIFIER,
        TokenType.INOUT,
        TokenType.IS,
        TokenType.ISNULL,
sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
sqlglot/dialects/hive.py:103:            "ADD FILE": TokenType.COMMAND,
sqlglot/dialects/snowflake.py:143:            "FILE://": TokenType.URI_START,
sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
701:        TokenType.FILE,
[tool_use Bash] {"command": "grep -n \"FUNC_TOKENS: t.ClassVar\" -A3 sqlglot/parser.py; grep -n \"def _parse_table_part\\b\" -A25 sqlglot/parser.py | head -40; grep -n \"TokenType.FILE\\b\\|FILE_FORMAT\" sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/clickhouse.py; git log --oneline -3 -- sqlglot/parser.py | cat", "description": "Check FUNC_TOKENS and table part parsing"}
[tool_result] 826:    FUNC_TOKENS: t.ClassVar = {
827-        TokenType.COLLATE,
828-        TokenType.COMMAND,
829-        TokenType.CURRENT_DATE,
4634:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
4635-        return (
4636-            (not schema and self._parse_function(optional_parens=False))
4637-            or self._parse_id_var(any_token=False)
4638-            or self._parse_string_as_identifier()
4639-            or self._parse_placeholder()
4640-        )
4641-
4642-    
…[1033 chars elided]…
py:9533:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9535:            elif prev == "FILE_FORMAT":
sqlglot/parser.py:9767:        # for FILE_FORMAT = <format_name>
e23a9eece feat(duckdb): Add transpilation support for BOOLEAN and TEXT cases of TRY_CAST function (#7681)
98b2b923a fix(bigquery): avoid self join auto unnest (#7697)
603433d27 fix(duckdb)!: fix for Snowflake transpilation issue related to PIVOT and string literal column names (#7660)
[tool_use Bash] {"command": "grep -n \"class Parser\" -A30 sqlglot/dialects/clickhouse.py | head -60; grep -n \"FUNC_TOKENS\" sqlglot/dialects/*.py | head", "description": "Inspect ClickHouse parser class configuration"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"class Parser\\|FUNC_TOKENS\\|FUNCTION_PARSERS\\|^    class \" sqlglot/dialects/clickhouse.py | head -30", "description": "Locate parser class in ClickHouse dialect"}
[tool_result] 71:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "sed -n 60,140p sqlglot/dialects/clickhouse.py; grep -n \"Parser\" sqlglot/dialects/clickhouse.py | head", "description": "Read ClickHouse dialect tokenizer and surrounding classes"}
[tool_result]             column_aliases = [
                exp.to_identifier(coldef.split(" ")[0]) for coldef in structure_coldefs
            ]
        else:
            # Default column aliases in CH are "c1", "c2", etc.
            column_aliases = [
                exp.to_identifier(f"c{i + 1}") for i in range(len(values[0].expressions))
            ]

        return column_aliases

    class Tokenizer(tokens.Tokenizer):
        COMMENTS = ["--", "#", "#!", ("/*", "*/")]
        IDENTIFIERS = ['"', "`"]
…[1728 chars elided]…
REGATEFUNCTION,
            "SIMPLEAGGREGATEFUNCTION": TokenType.SIMPLEAGGREGATEFUNCTION,
            "SYSTEM": TokenType.COMMAND,
            "PREWHERE": TokenType.PREWHERE,
        }

        KEYWORDS.pop("/*+")

        SINGLE_TOKENS = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.HEREDOC_STRING,
        }

    Parser = ClickHouseParser

    Generator = ClickHouseGenerator
10:from sqlglot.parsers.clickhouse import ClickHouseParser
129:    Parser = ClickHouseParser
[tool_use Bash] {"command": "grep -n \"FUNC_TOKENS\\|class ClickHouseParser\\|FUNCTION_PARSERS\\|^from\\|^import\" sqlglot/parsers/clickhouse.py | head -30; grep -n \"FUNC_TOKENS\" -A3 sqlglot/parsers/clickhouse.py | head; ls sqlglot/parsers | head -50", "description": "Inspect ClickHouse parser module"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from collections import deque
7:from sqlglot import exp, parser
8:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import Token, TokenType
16:from builtins import type as Type
239:class ClickHouseParser(parser.Parser):
316:    FUNC_TOKENS = {
317:        *parser.Parser.FUNC_TOKENS,
362:    FUNCTION_PARSERS = {
363:        **{k: v for k, v in parser.Parser.FUNCTION_PARSERS.items() if k !
…[157 chars elided]…
ENS = {
317:        *parser.Parser.FUNC_TOKENS,
318-        TokenType.AND,
319-        TokenType.OR,
320-        TokenType.SET,
__init__.py
__pycache__
athena.py
base.py
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
[tool_use Bash] {"command": "sed -n 316,362p sqlglot/parsers/clickhouse.py", "description": "Read ClickHouse FUNC_TOKENS block"}
[tool_result]     FUNC_TOKENS = {
        *parser.Parser.FUNC_TOKENS,
        TokenType.AND,
        TokenType.OR,
        TokenType.SET,
    }

    RESERVED_TOKENS = parser.Parser.RESERVED_TOKENS - {TokenType.SELECT}

    ID_VAR_TOKENS = {
        *parser.Parser.ID_VAR_TOKENS,
        TokenType.LIKE,
    }

    AGG_FUNC_MAPPING = AGG_FUNC_MAPPING

    @classmethod
    def _resolve_clickhouse_agg(cls, name: str) -> tuple[str, Sequence[str]] | None:
        # ClickHouse allows chaining multiple combinators on 
…[920 chars elided]…
    name = name[: -len(suffix)]
                    break
            else:
                return None

        # We now have a 0- or 1-suffix aggregate
        agg_func_name, inner_suffix = parts
        if inner_suffix:
            # this is a 1-suffix aggregate (either naturally or via repeated suffix
            # stripping). prepend the innermost suffix.
            accumulated_suffixes.appendleft(inner_suffix)

        return (agg_func_name, accumulated_suffixes)

    FUNCTION_PARSERS = {
[assistant] The ClickHouse parser's `FUNC_TOKENS` doesn't include `FILE`, so `file(` is never treated as a function call. I'll add it there, scoped to the ClickHouse dialect.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123328-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.SET,\n    }\n\n    RESERVED_TOKENS", "new_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.FILE,\n        TokenType.SET,\n    }\n\n    RESERVED_TOKENS"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-123328-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq='CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file(\\'base/dir/*.parquet\\', Parquet)'\nprint(sqlglot.parse_one(q, dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM file('a.csv', CSV)\\\", dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT file FROM t\\\", dialect='clickhouse').sql(dialect='clickhouse'))\n\"; grep -n \"def test_\" tests/dialects/test_clickhouse.py | tail -3; grep -n \"validate_identity\" tests/dialects/test_clickhouse.py | head -3", "description": "Verify the fix round-trips and check test file layout"}
[tool_result] CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
SELECT * FROM file('a.csv', CSV)
SELECT file FROM t
1794:    def test_to_start_of(self):
1830:    def test_string_split(self):
1858:    def test_sql_security(self):
16:        self.validate_identity(
20:        self.validate_identity(
29:            self.validate_identity(f"CAST(x AS {string_type_enum.value})", "CAST(x AS String)")
[assistant] The fix round-trips for all three cases. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "sed -n 1858,1875p tests/dialects/test_clickhouse.py", "description": "Read end of ClickHouse test file"}
[tool_result]     def test_sql_security(self):
        stmts = [
            "CREATE VIEW v DEFINER='alice' SQL SECURITY DEFINER AS SELECT 1",
            "CREATE VIEW v SQL SECURITY DEFINER DEFINER='alice' AS SELECT 1",
            "CREATE VIEW v SQL SECURITY DEFINER DEFINER=CURRENT_USER AS SELECT 1",
            "CREATE VIEW v SQL SECURITY INVOKER AS SELECT 1",
            "CREATE VIEW v SQL SECURITY NONE AS SELECT 1",
            "CREATE MATERIALIZED VIEW v TO t SQL SECURITY DEFINER DEFINER='alice' AS SELECT 1",
            "CREATE MATERIALIZED VIEW v TO t SQL SECURITY INVOKER AS SELECT 1",
            "CREATE MATERIALIZED VIEW v TO t SQL SECURITY NONE AS SELECT 1",
            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER='alice'",
            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER=CURRENT_USER",
        ]
        for stmt in stmts:
            with self.subTest(stmt):
                self.validate_identity(stmt)
[tool_use Bash] {"command": "cat >> tests/dialects/test_clickhouse.py <<'EOF'\n\n    def test_file_table_function(self):\n        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n        self.validate_identity(\"SELECT * FROM file('a.csv', CSV)\")\n        self.validate_identity(\"SELECT file FROM t\")\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Add regression test and run full test suite"}
[tool_result] ................................................................................................................................................................................................................................................................................... [ 24%]
........................... [ 27%]
........................................ [ 30%]
........................................................................................ [ 38%]
......................................
…[280 chars elided]…
............................................................................................................................................................................................................................................. [ 86%]
........................................................................................... [ 94%]
....................... [ 96%]
.......... [ 97%]
................ [ 98%]
..............                  [100%]
1115 passed, 18164 subtests passed in 54.31s
[assistant] `file(...)` now parses as a table function in the ClickHouse dialect and round-trips unchanged. Your example outputs `... FROM file('base/dir/*.parquet', Parquet)`.

**Cause:** `file` tokenizes as `TokenType.FILE`, which isn't in the ClickHouse parser's `FUNC_TOKENS`. So `file(` was never parsed as a function call and fell through to a table named `file` with the arguments as an alias list.

**Fix:** I added `TokenType.FILE` to `FUNC_TOKENS` in `sqlglot/parsers/clickhouse.py`. I scoped it to ClickHouse rather than the base parser, since the reported bug is ClickHouse-only.

**Test:** I added `test_file_table_function` to `tests/dialects/test_clickhouse.py`. It covers your exact statement, a `file('a.csv', CSV)` table function, and a bare `file` column to confirm it still works as an identifier.

**Verification:** The full suite passes with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/`: 1115 passed, 18164 subtests passed.

The changes are uncommitted in the worktree.
