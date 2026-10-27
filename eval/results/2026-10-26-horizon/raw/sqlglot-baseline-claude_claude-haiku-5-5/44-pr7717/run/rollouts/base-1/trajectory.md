# trajectory base-1

final message:
ClickHouse's `file(...)` now parses as a table function and round-trips unchanged. The reported statement gives back exactly the input.

**Cause:** `FILE` is a keyword token that isn't in the parser's `FUNC_TOKENS`, so `file` was read as a table name and the parenthesised arguments became the table alias's column list. The ClickHouse parser (`sqlglot/parsers/clickhouse.py`) already extends `FUNC_TOKENS` for its own keywords.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS` set. The change is scoped to ClickHouse, so other dialects keep their current behaviour.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the `CREATE VIEW ... AS SELECT c1 FROM file(...)` statement from the report.

**Verification:** the full suite passes (1114 tests, 18164 subtests), and `ruff format --check` and `ruff check` are clean on both files. I did not run `make check` or the C-extension (`testc`) variant.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"file\\|File\" sqlglot/dialects/clickhouse.py | head -60; grep -rn \"\\\"FILE\\\"\\|FILE\\b\" sqlglot/parser.py sqlglot/dialects/clickhouse.py | head; sqlglot_py=1; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')\nprint(repr(e.args['from']))\n\"", "description": "Search for file handling in ClickHouse dialect and reproduce"}
[tool_result ERROR] Exit code 1
sqlglot/parser.py:701:        TokenType.FILE,
sqlglot/parser.py:8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'from'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')\nprint(repr(e))\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='duckdb')\nprint(repr(e))\n\"; grep -n \"TokenType.FILE\\|\\\"FILE\\\"\" sqlglot/tokens.py sqlglot/dialects/*.py | head; sed -n 690,710p sqlglot/parser.py", "description": "Inspect AST for file() in ClickHouse and DuckDB"}
[tool_result] Select(
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
Select(
  expressions=[
    Column(
      this=Identifier(this=c1, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=file, quoted=False),
      alias=TableA
…[311 chars elided]…
okenType.DESCRIBE,
        TokenType.DETACH,
        TokenType.DICTIONARY,
        TokenType.DIV,
        TokenType.END,
        TokenType.EXECUTE,
        TokenType.EXPORT,
        TokenType.ESCAPE,
        TokenType.FALSE,
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
[tool_use Bash] {"command": "grep -n \"FUNC_TOKENS = \\|TokenType.FILE\\b\" sqlglot/parser.py; grep -n \"FUNC_TOKENS\" sqlglot/parser.py | head -3; sed -n '/^    FUNC_TOKENS = {/,/^    }/p' sqlglot/parser.py | head -80 | tail -30; git log --oneline -3 -- sqlglot/parser.py | cat", "description": "Check FUNC_TOKENS for FILE token"}
[tool_result] 701:        TokenType.FILE,
826:    FUNC_TOKENS: t.ClassVar = {
6950:        elif token_type not in self.FUNC_TOKENS:
e23a9eece feat(duckdb): Add transpilation support for BOOLEAN and TEXT cases of TRY_CAST function (#7681)
98b2b923a fix(bigquery): avoid self join auto unnest (#7697)
603433d27 fix(duckdb)!: fix for Snowflake transpilation issue related to PIVOT and string literal column names (#7660)
[tool_use Bash] {"command": "sed -n 826,870p sqlglot/parser.py; grep -n \"def _parse_table_part\\b\" -A25 sqlglot/parser.py | head -40", "description": "Read FUNC_TOKENS and table part parsing"}
[tool_result]     FUNC_TOKENS: t.ClassVar = {
        TokenType.COLLATE,
        TokenType.COMMAND,
        TokenType.CURRENT_DATE,
        TokenType.CURRENT_DATETIME,
        TokenType.CURRENT_SCHEMA,
        TokenType.CURRENT_TIMESTAMP,
        TokenType.CURRENT_TIME,
        TokenType.CURRENT_USER,
        TokenType.CURRENT_CATALOG,
        TokenType.FILTER,
        TokenType.FIRST,
        TokenType.FORMAT,
        TokenType.GET,
        TokenType.GLOB,
        TokenType.IDENTIFIER,
        TokenType.INDE
…[1357 chars elided]…
.IDENTIFIER_TOKENS):
4648-            token = self._prev
4649-            comments = self._prev_comments
4650-
4651-            has_dot = self._match(TokenType.DOT)
4652-            curr_tt = self._curr.token_type
4653-
4654-            if not has_dot:
4655-                if curr_tt in self.TABLE_POSTFIX_TOKENS:
4656-                    self._retreat(index)
4657-                    return None
4658-            elif curr_tt not in self.IDENTIFIER_TOKENS:
4659-                self._retreat(index)
[tool_use Bash] {"command": "grep -n \"class Parser\" -A12 sqlglot/dialects/clickhouse.py | head -30; grep -n \"FUNC_TOKENS\" sqlglot/dialects/*.py | head", "description": "Check how dialects override FUNC_TOKENS"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"class Parser\\|FUNCTIONS = \\|TABLE_POSTFIX\\|ID_VAR_TOKENS\\|^    class\\|^class\" sqlglot/dialects/clickhouse.py | head -30", "description": "Find Parser class structure in ClickHouse dialect"}
[tool_result] 15:class ClickHouse(Dialect):
71:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "sed -n 60,140p sqlglot/dialects/clickhouse.py", "description": "Read ClickHouse dialect class body"}
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
…[1635 chars elided]…
       "MULTIPOLYGON": TokenType.MULTIPOLYGON,
            "AGGREGATEFUNCTION": TokenType.AGGREGATEFUNCTION,
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
[tool_use Bash] {"command": "grep -n \"class ClickHouseParser\" -A40 sqlglot/dialects/clickhouse.py | grep -n \"FUNC\\|_TOKENS\\|=\" | head -30", "description": "Inspect ClickHouseParser class attributes"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"class ClickHouseParser\" sqlglot/ ; f=$(grep -rln \"class ClickHouseParser\" sqlglot/); grep -n \"FUNC_TOKENS\\|ID_VAR_TOKENS\\|TABLE_ALIAS\\|^    [A-Z_]* = \\|^    [A-Z_]*: \" $f | head -30", "description": "Locate ClickHouseParser definition"}
[tool_result] sqlglot/parsers/clickhouse.py:239:class ClickHouseParser(parser.Parser):
243:    MODIFIERS_ATTACHED_TO_SET_OP = False
244:    INTERVAL_SPANS = False
245:    OPTIONAL_ALIAS_TOKEN_CTE = False
246:    JOINS_HAVE_EQUAL_PRECEDENCE = True
248:    FUNCTIONS = {
313:    AGG_FUNCTIONS = AGG_FUNCTIONS
314:    AGG_FUNCTIONS_SUFFIXES = AGG_FUNCTIONS_SUFFIXES
316:    FUNC_TOKENS = {
317:        *parser.Parser.FUNC_TOKENS,
323:    RESERVED_TOKENS = parser.Parser.RESERVED_TOKENS - {TokenType.SELECT}
325:    ID
…[153 chars elided]…
RS = {
381:    NO_PAREN_FUNCTION_PARSERS = {
385:    NO_PAREN_FUNCTIONS = {
391:    RANGE_PARSERS = {
396:    COLUMN_OPERATORS = {
403:    JOIN_KINDS = {
411:    TABLE_ALIAS_TOKENS = parser.Parser.TABLE_ALIAS_TOKENS - {
421:    ALIAS_TOKENS = parser.Parser.ALIAS_TOKENS - {
425:    LOG_DEFAULTS_TO_LN = True
427:    QUERY_MODIFIER_PARSERS = {
436:    CONSTRAINT_PARSERS = {
443:    ALTER_PARSERS = {
449:    SCHEMA_UNNAMED_CONSTRAINTS = {
454:    PLACEHOLDER_PARSERS = {
459:    STATEMENT_PARSERS = {
[assistant] The ClickHouse parser lives in `sqlglot/parsers/clickhouse.py`, and it already extends `FUNC_TOKENS`. Let me look at that block.
[tool_use Bash] {"command": "sed -n 314,332p sqlglot/parsers/clickhouse.py; grep -n \"file(\" tests/dialects/test_clickhouse.py | head", "description": "Read ClickHouse FUNC_TOKENS override"}
[tool_result]     AGG_FUNCTIONS_SUFFIXES = AGG_FUNCTIONS_SUFFIXES

    FUNC_TOKENS = {
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
[assistant] The fix is a one-token addition to ClickHouse's `FUNC_TOKENS`, so `file` followed by `(` parses as a function call. Applying it and checking the round-trip:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160728-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.SET,\n    }", "new_string": "        TokenType.AND,\n        TokenType.FILE,\n        TokenType.OR,\n        TokenType.SET,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160728-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse_one('CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file(\\'base/dir/*.parquet\\', Parquet)', dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.transpile(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", read='clickhouse', write='clickhouse'))\n\"", "description": "Verify the reported case and a plain file() query round-trip"}
[tool_result] CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
["SELECT c1 FROM file('base/dir/*.parquet', Parquet)"]
[assistant] Both cases round-trip now. Next I'll add a regression test to the ClickHouse dialect tests.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_clickhouse.py | head -20; grep -n \"FROM [a-z_]*(\" tests/dialects/test_clickhouse.py | head -5", "description": "Find test layout in ClickHouse test file"}
[tool_result] 15:    def test_clickhouse(self):
739:    def test_clickhouse_values(self):
778:    def test_cte(self):
798:    def test_ternary(self):
836:    def test_parameterization(self):
849:    def test_signed_and_unsigned_types(self):
870:    def test_geom_types(self):
876:    def test_nothing_type(self):
882:    def test_json_type(self):
917:    def test_aggregate_function_column_with_any_keyword(self):
944:    def test_create_table_as_alias(self):
955:    def test_ddl(self):
1430:    def test_agg_func
…[500 chars elided]…
NT() OVER (PARTITION BY number % 3) AS partition_count FROM numbers(10) WINDOW window_name AS (PARTITION BY number) QUALIFY partition_count = 4 ORDER BY number"
163:            "SELECT n, source FROM (SELECT toFloat32(number % 10) AS n, 'original' AS source FROM numbers(10) WHERE number % 3 = 1) ORDER BY n WITH FILL"
166:            "SELECT n, source FROM (SELECT toFloat32(number % 10) AS n, 'original' AS source FROM numbers(10) WHERE number % 3 = 1) ORDER BY n WITH FILL FROM 0 TO 5.51 STEP 0.5"
[tool_use Bash] {"command": "sed -n 66,72p tests/dialects/test_clickhouse.py", "description": "View context around an existing identity test"}
[tool_result]         self.validate_identity("countIf(x, y)")
        self.validate_identity("x = y")
        self.validate_identity("x <> y")
        self.validate_identity("SELECT * FROM (SELECT a FROM b SAMPLE 0.01)")
        self.validate_identity("SELECT * FROM (SELECT a FROM b SAMPLE 1 / 10 OFFSET 1 / 2)")
        self.validate_identity("SELECT sum(foo * bar) FROM bla SAMPLE 10000000")
        self.validate_identity("CAST(x AS Nested(ID UInt32, Serial UInt32, EventTime DateTime))")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-160728-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT sum(foo * bar) FROM bla SAMPLE 10000000\")\n", "new_string": "        self.validate_identity(\"SELECT sum(foo * bar) FROM bla SAMPLE 10000000\")\n        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-160728-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Now the full test suite, using the project's configured test command:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
[tool_result] ............. [  9%]
........................................................................ [ 15%]
.............. [ 17%]
............................................................. [ 22%]
........................................................................................... [ 30%]
..................................................................... [ 36%]
............................................................................................................. [ 46%]
...............
…[197 chars elided]…
....... [ 64%]
......................................................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 54.30s
[assistant] All 1114 tests pass. I'll run the formatter/linter on the two changed files too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py 2>&1 | tail -3; $PY -m ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py 2>&1 | tail -3; git status --short", "description": "Run ruff format and lint on changed files"}
[tool_result] 2 files already formatted
All checks passed!
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[assistant] ClickHouse's `file(...)` now parses as a table function and round-trips unchanged. The reported statement gives back exactly the input.

**Cause:** `FILE` is a keyword token that isn't in the parser's `FUNC_TOKENS`, so `file` was read as a table name and the parenthesised arguments became the table alias's column list. The ClickHouse parser (`sqlglot/parsers/clickhouse.py`) already extends `FUNC_TOKENS` for its own keywords.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS` set. The change is scoped to ClickHouse, so other dialects keep their current behaviour.
- `tests/dialects/test_clickhouse.py`: added a `validate_identity` case for the `CREATE VIEW ... AS SELECT c1 FROM file(...)` statement from the report.

**Verification:** the full suite passes (1114 tests, 18164 subtests), and `ruff format --check` and `ruff check` are clean on both files. I did not run `make check` or the C-extension (`testc`) variant.

I did not commit anything.
