# trajectory base-1

final message:
`file(...)` now parses as a table function in ClickHouse and round-trips unchanged. Your example outputs the original SQL.

**Cause:** the tokenizer maps `FILE` to `TokenType.FILE`, which is in `ID_VAR_TOKENS` but not `FUNC_TOKENS`. So `file(` was read as a bare table name followed by an alias list, which produced `file AS _t0("base/dir/*.parquet", Parquet)`.

**Change:**
- `sqlglot/parser.py`: added `TokenType.FILE` to `FUNC_TOKENS`. This is in the base parser, so it applies to every dialect, not only ClickHouse.
- `tests/dialects/test_clickhouse.py`: added your statement to `test_functions` as a `validate_identity` case.

**Verification:**
- The full suite passes: 1114 passed, 18164 subtests.
- `ruff check` and `ruff format --check` pass on both changed files.
- `SELECT file FROM t` and `SELECT * FROM file AS f` still work, so using `file` as a plain identifier is unaffected.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n '\"FILE\"\\|FILE\\b\\|\"file\"\\|TABLE_FUNCTION\\|_parse_table_parts\\|def _parse_table' sqlglot/dialects/clickhouse.py sqlglot/parser.py | head -60", "description": "Search for file/table function handling in parsers"}
[tool_result] sqlglot/parser.py:701:        TokenType.FILE,
sqlglot/parser.py:1073:        exp.Table: lambda self: self._parse_table_parts(),
sqlglot/parser.py:2201:            this = self._parse_table_parts(schema=True)
sqlglot/parser.py:2218:        table = self._parse_table_parts(schema=True)
sqlglot/parser.py:2314:            this = self._parse_table_parts(schema=True, is_db_reference=kind == "SCHEMA")
sqlglot/parser.py:2493:            table = self._parse_table_parts()
sqlglot/parser.py:2494:            
…[1807 chars elided]…
his = self._parse_table_parts(schema=True)
sqlglot/parser.py:8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
sqlglot/parser.py:8962:            this = self._parse_table_parts()
sqlglot/parser.py:8978:            this = self._parse_table_parts()
sqlglot/parser.py:9689:        securable = self._try_parse(self._parse_table_parts)
sqlglot/parser.py:9770:                this=exp.var("FORMAT_NAME"), value=self._parse_string() or self._parse_table_parts()
[tool_use Bash] {"command": "sed -n 4705,4800p sqlglot/parser.py && grep -n 'FILE' sqlglot/tokens.py sqlglot/dialects/clickhouse.py | head; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')\nprint(repr(e))\n\"", "description": "Inspect table parsing and reproduce the bug"}
[tool_result]     def _parse_table_parts(
        self,
        schema: bool = False,
        is_db_reference: bool = False,
        wildcard: bool = False,
        fast: bool = False,
    ) -> exp.Table | exp.Dot | None:
        if fast:
            return self._parse_table_parts_fast()

        catalog: exp.Expr | str | None = None
        db: exp.Expr | str | None = None
        table: exp.Expr | str | None = self._parse_table_part(schema=schema)

        while self._match(TokenType.DOT):
            if ca
…[2706 chars elided]…
MIT
                if curr_tt in fast_terminators and next_tt != TokenType.MATCH_CONDITION:
                    return table

sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
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
[tool_use Bash] {"command": "sed -n 690,715p sqlglot/parser.py && grep -n 'FUNC_TOKENS = \\|ID_VAR_TOKENS\\|TABLE_FUNC\\|TokenType.FILE\\b' sqlglot/parser.py | head -20; grep -n 'FILE' sqlglot/dialects/clickhouse.py sqlglot/tokens.py; git log --oneline -3 -- sqlglot/tokens.py | cat", "description": "Check FILE token sets and history"}
[tool_result]         TokenType.DESC,
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
        TokenType.FILE,
        TokenType.FILTER,
        TokenType.FINAL,
        TokenType.FORMAT,
        TokenType.FULL,
        TokenType.GET,
        TokenType.IDENTIFIER,
        TokenType.INOUT,
        TokenT
…[813 chars elided]…
 not in self.ID_VAR_TOKENS:
8437:        # WINDOW is in ID_VAR_TOKENS, so it can be consumed as an implicit alias. Detect the
8480:            (any_token and self._advance_any()) or self._match_set(tokens or self.ID_VAR_TOKENS)
sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
cc448ac48 feat(postgres): add support for PostGIS 3D distance operator <<->> (#7655)
63f8dc6df perf(tokens): cache TokenizerCore per thread (#7547)
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
[tool_use Bash] {"command": "grep -n 'FUNC_TOKENS' sqlglot/parser.py sqlglot/dialects/*.py | head -20; grep -n 'TokenType.FILE\\|FILE' sqlglot/parser.py | head; grep -rn '\"FILE\"' sqlglot/dialects/ | head; grep -rn 'file(' tests/dialects/test_clickhouse.py | head", "description": "Locate FUNC_TOKENS and FILE references"}
[tool_result] sqlglot/parser.py:826:    FUNC_TOKENS: t.ClassVar = {
sqlglot/parser.py:6950:        elif token_type not in self.FUNC_TOKENS:
622:        TokenType.FILE_FORMAT,
701:        TokenType.FILE,
1700:        "FILE_FORMAT",
3641:                    files=self._match_text_seq("FROM", "FILES")
8850:        elif self._match_text_seq("FILESTREAM_ON", advance=False):
8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
8864:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
9533:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
9535:            elif prev == "FILE_FORMAT":
9767:        # for FILE_FORMAT = <format_name>
[tool_use Bash] {"command": "sed -n 820,850p sqlglot/parser.py; sed -n 6930,6960p sqlglot/parser.py; grep -n 'FUNC_TOKENS\\|FILE' sqlglot/dialects/clickhouse.py | head", "description": "Read FUNC_TOKENS definition and function lookup"}
[tool_result]             TokenType.PIVOT,
            TokenType.UNPIVOT,
            TokenType.TABLE_SAMPLE,
        }
    )

    FUNC_TOKENS: t.ClassVar = {
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
        Toke
…[830 chars elided]…
   return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())

            return None

        if any_token:
            if token_type in self.RESERVED_TOKENS:
                return None
        elif token_type not in self.FUNC_TOKENS:
            return None

        self._advance(2)

        parser = self.FUNCTION_PARSERS.get(upper)
        if parser and not anonymous:
            result = parser(self)
        else:
            subquery_predicate = self.SUBQUERY_PREDICATES.get(token_type)
[assistant] The `FILE` token is in `ID_VAR_TOKENS` but not `FUNC_TOKENS`, so `file(` is read as a bare table name followed by an alias list. I'll add it to `FUNC_TOKENS` and check the result.
[tool_use Bash] {"command": "sed -n 850,870p sqlglot/parser.py", "description": "View rest of FUNC_TOKENS set"}
[tool_result]         TokenType.NEXT,
        TokenType.OFFSET,
        TokenType.PRIMARY_KEY,
        TokenType.RANGE,
        TokenType.REPLACE,
        TokenType.RLIKE,
        TokenType.ROW,
        TokenType.SESSION_USER,
        TokenType.UNNEST,
        TokenType.VAR,
        TokenType.LEFT,
        TokenType.RIGHT,
        TokenType.SEQUENCE,
        TokenType.DATE,
        TokenType.DATETIME,
        TokenType.TABLE,
        TokenType.TIMESTAMP,
        TokenType.TIMESTAMPTZ,
        TokenType.TRUNCATE,
        TokenType.UTC_DATE,
        TokenType.UTC_TIME,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133807-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parser.py", "old_string": "        TokenType.FILTER,\n        TokenType.FIRST,\n        TokenType.FORMAT,\n        TokenType.GET,\n        TokenType.GLOB,", "new_string": "        TokenType.FILE,\n        TokenType.FILTER,\n        TokenType.FIRST,\n        TokenType.FORMAT,\n        TokenType.GET,\n        TokenType.GLOB,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133807-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in [\\\"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", \\\"SELECT * FROM file('a.csv', CSV, 'x String')\\\", \\\"SELECT file FROM t\\\", \\\"SELECT * FROM file AS f\\\"]:\n    e=sqlglot.parse_one(q, dialect='clickhouse')\n    print(e.sql(dialect='clickhouse'))\nprint(repr(sqlglot.parse_one(\\\"SELECT * FROM file('a.csv', CSV)\\\", dialect='clickhouse').args['from_'].this))\n\"", "description": "Verify round-trip after the parser change"}
[tool_result] CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
SELECT * FROM file('a.csv', CSV, 'x String')
SELECT file FROM t
SELECT * FROM file AS f
Table(
  this=Anonymous(
    this=file,
    expressions=[
      Literal(this='a.csv', is_string=True),
      Column(
        this=Identifier(this=CSV, quoted=False))]))
[assistant] The round-trip now works. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "grep -n 'def test_\\|FROM s3(\\|url(' tests/dialects/test_clickhouse.py | head -80", "description": "Find table-function tests in ClickHouse suite"}
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
…[160 chars elided]…
_datetime_funcs(self):
1584:    def test_convert(self):
1611:    def test_timestr_to_time(self):
1675:    def test_grant(self):
1679:    def test_revoke(self):
1683:    def test_array_join(self):
1710:    def test_traverse_scope(self):
1716:    def test_window_functions(self):
1724:    def test_groupconcat(self):
1765:    def test_functions(self):
1771:    def test_array_offset(self):
1794:    def test_to_start_of(self):
1830:    def test_string_split(self):
1858:    def test_sql_security(self):
[tool_use Bash] {"command": "sed -n 1765,1771p tests/dialects/test_clickhouse.py", "description": "View test_functions region for insertion point"}
[tool_result]     def test_functions(self):
        self.validate_identity("SELECT TRANSFORM(foo, [1, 2], ['first', 'second']) FROM table")
        self.validate_identity(
            "SELECT TRANSFORM(foo, [1, 2], ['first', 'second'], 'default') FROM table"
        )

    def test_array_offset(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133807-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "old_string": "            \"SELECT TRANSFORM(foo, [1, 2], ['first', 'second'], 'default') FROM table\"\n        )\n\n    def test_array_offset(self):", "new_string": "            \"SELECT TRANSFORM(foo, [1, 2], ['first', 'second'], 'default') FROM table\"\n        )\n        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n\n    def test_array_offset(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133807-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Now the project's check command, which the repo's harness specifies, on the full test suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 600000}
[tool_result] ........................................................................................... [  8%]
............. [  9%]
........................................................................ [ 15%]
.............. [ 17%]
............................................................. [ 22%]
........................................................................................... [ 30%]
..................................................................... [ 36%]
.................................
…[296 chars elided]…
....... [ 64%]
......................................................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 49.43s
[assistant] All 1114 tests pass. I'll also run the repo's linter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_clickhouse.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_clickhouse.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py                 | 1 +
 tests/dialects/test_clickhouse.py | 3 +++
 2 files changed, 4 insertions(+)
[assistant] `file(...)` now parses as a table function in ClickHouse and round-trips unchanged. Your example outputs the original SQL.

**Cause:** the tokenizer maps `FILE` to `TokenType.FILE`, which is in `ID_VAR_TOKENS` but not `FUNC_TOKENS`. So `file(` was read as a bare table name followed by an alias list, which produced `file AS _t0("base/dir/*.parquet", Parquet)`.

**Change:**
- `sqlglot/parser.py`: added `TokenType.FILE` to `FUNC_TOKENS`. This is in the base parser, so it applies to every dialect, not only ClickHouse.
- `tests/dialects/test_clickhouse.py`: added your statement to `test_functions` as a `validate_identity` case.

**Verification:**
- The full suite passes: 1114 passed, 18164 subtests.
- `ruff check` and `ruff format --check` pass on both changed files.
- `SELECT file FROM t` and `SELECT * FROM file AS f` still work, so using `file` as a plain identifier is unaffected.

I didn't commit anything.
