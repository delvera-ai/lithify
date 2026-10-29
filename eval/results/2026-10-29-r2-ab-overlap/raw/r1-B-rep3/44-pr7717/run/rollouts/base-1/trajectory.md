# trajectory base-1

final message:
`file(...)` now parses as a table function in the ClickHouse dialect, and your example round-trips unchanged. The full test suite passes (1115 tests) and ruff is clean. I haven't committed anything.

**Cause:** `file` is tokenized as `TokenType.FILE`, which isn't in the ClickHouse parser's `FUNC_TOKENS`. So `_parse_table_part` never treated `file(` as a function call. It read `file` as a bare table name and then took the parenthesised arguments as column aliases, which is where the `AS _t0("base/dir/*.parquet", Parquet)` output came from.

**Fix:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS`, next to the existing `AND`/`OR`/`SET` entries. I scoped it to ClickHouse rather than the base parser, since the report is ClickHouse-specific and the base change would affect every dialect.
- `tests/dialects/test_clickhouse.py`: added `test_file_table_function` with the reported `CREATE VIEW` statement and a `SELECT * FROM file('data.csv', 'CSV') AS t` case.

A bare column named `file` (e.g. `SELECT file FROM t`) still parses and round-trips as before.

## events
[tool_use Bash] {"command": "grep -n '\"FILE\"\\|FILE\\b\\|\"file\"' sqlglot/dialects/clickhouse.py sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/dialect.py | head -50; grep -rn \"file(\" tests/dialects/test_clickhouse.py | head", "description": "Search for file function handling in ClickHouse dialect"}
[tool_result] 3 matches in 2 files:

sqlglot/parser.py:701:TokenType.FILE,
sqlglot/parser.py:8862:elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORM...
sqlglot/tokens.py:297:"FILE": TokenType.FILE,
[tool_use Bash] {"command": "sed -n 8850,8875p sqlglot/parser.py; sed -n 690,710p sqlglot/parser.py; grep -n \"FILE\" sqlglot/dialects/clickhouse.py sqlglot/dialects/*.py | head; grep -n \"TokenType.FILE\\|FILE_FORMAT\\|\\\"FILE\\\"\" sqlglot/*.py | head -20", "description": "Inspect parser FILE handling and related tokens"}
[tool_result]         elif self._match_text_seq("FILESTREAM_ON", advance=False):
            alter_set.set("expressions", [self._parse_assignment()])
        elif self._match_texts(("LOGGED", "UNLOGGED")):
            alter_set.set("option", exp.var(self._prev.text.upper()))
        elif self._match_text_seq("WITHOUT") and self._match_texts(("CLUSTER", "OIDS")):
            alter_set.set("option", exp.var(f"WITHOUT {self._prev.text.upper()}"))
        elif self._match_text_seq("LOCATION"):
            alter_s
…[2305 chars elided]…
glot/parser.py:1700:"FILE_FORMAT",
sqlglot/parser.py:8862:elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORM...
sqlglot/parser.py:8864:elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:9533:# Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9535:elif prev == "FILE_FORMAT":
sqlglot/parser.py:9767:# for FILE_FORMAT = <format_name>
sqlglot/tokenizer_core.py:295:FILE_FORMAT = auto()
sqlglot/tokens.py:297:"FILE": TokenType.FILE,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", \\\"SELECT c1 FROM file('a', 'Parquet')\\\", \\\"SELECT * FROM s3('a', 'Parquet')\\\"]:\n    e=sqlglot.parse_one(s, dialect='clickhouse'); print(repr(e.args['from'].this)); print(e.sql(dialect='clickhouse'))\n\"; grep -n \"TokenType.FILE\\b\" sqlglot/parser.py; grep -n \"def _parse_table_parts\\|def _parse_table(\" sqlglot/parser.py; grep -n \"FUNC_TOKENS = \" -A3 sqlglot/parser.py", "description": "Reproduce file() parse and round-trip behavior"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'from'
1 matches in 1 files:

sqlglot/parser.py:701:TokenType.FILE,
rg: regex parse error:
    (?:def _parse_table_parts|def _parse_table()
    ^
error: unclosed group
0 matches for 'def _parse_table_parts\|def _parse_table('
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in [\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", \\\"SELECT c1 FROM file('a', 'Parquet')\\\", \\\"SELECT * FROM s3('a', 'Parquet')\\\"]:\n    e=sqlglot.parse_one(s, dialect='clickhouse'); print(repr(e.find(exp.From).this)); print(e.sql(dialect='clickhouse'))\nprint(repr(sqlglot.parse_one(\\\"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')))\n\"", "description": "Reproduce file() parse and round-trip behavior"}
[tool_result] Table(
  this=Identifier(this=file, quoted=False),
  alias=TableAlias(
    columns=[
      Identifier(this='base/dir/*.parquet', quoted=True),
      Identifier(this=Parquet, quoted=False)]))
SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet)
Table(
  this=Identifier(this=file, quoted=False),
  alias=TableAlias(
    columns=[
      Identifier(this='a', quoted=True),
      Identifier(this='Parquet', quoted=True)]))
SELECT c1 FROM file AS _t0("a", "Parquet")
Table(
  this=Anonymous(
    this
…[492 chars elided]…
         kind=NotNullColumnConstraint())])]),
  kind=VIEW,
  replace=False,
  refresh=False,
  unique=False,
  expression=Select(
    expressions=[
      Column(
        this=Identifier(this=c1, quoted=False))],
    from_=From(
      this=Table(
        this=Identifier(this=file, quoted=False),
        alias=TableAlias(
          columns=[
            Identifier(this='base/dir/*.parquet', quoted=True),
            Identifier(this=Parquet, quoted=False)])))),
  exists=False,
  concurrently=False)
[tool_use Bash] {"command": "grep -n \"def _parse_table_part\\b\" -A25 sqlglot/parser.py; grep -n \"^    FUNC_TOKENS\" -A3 sqlglot/parser.py; grep -n \"ID_VAR_TOKENS\\|TABLE_ALIAS_TOKENS\" sqlglot/parser.py | head -5; git log --oneline -3 -- sqlglot/parser.py | cat", "description": "Inspect table part parsing and FUNC_TOKENS"}
[tool_result] 4634:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
4635-        return (
4636-            (not schema and self._parse_function(optional_parens=False))
4637-            or self._parse_id_var(any_token=False)
4638-            or self._parse_string_as_identifier()
4639-            or self._parse_placeholder()
4640-        )
4641-
4642-    def _parse_table_parts_fast(self) -> exp.Table | None:
4643-        index = self._index
4644-        parts: list[exp.Identifier] | Non
…[763 chars elided]…


1676:0:t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1682:0:t.ClassVar = ID_VAR_TOKENS - {TokenType.ROW, TokenType.ROWS, TokenType.PERCENT}
1695:0:t.ClassVar = TABLE_ALIAS_TOKENS - SET_OPERATIONS
e23a9eece feat(duckdb): Add transpilation support for BOOLEAN and TEXT cases of TRY_CAST function (#7681)
98b2b923a fix(bigquery): avoid self join auto unnest (#7697)
603433d27 fix(duckdb)!: fix for Snowflake transpilation issue related to PIVOT and string literal column names (#7660)
[tool_use Bash] {"command": "sed -n 826,900p sqlglot/parser.py | grep -n \"FILE\\|}\" | head -3; grep -n \"def _parse_table_parts\" -A40 sqlglot/parser.py | sed -n 1,60p; grep -n \"FILE\" sqlglot/dialects/clickhouse.py", "description": "Check FUNC_TOKENS membership and table parts parsing"}
[tool_result ERROR] Exit code 1
51:    }
55:    }
59:    }
4642:    def _parse_table_parts_fast(self) -> exp.Table | None:
4643-        index = self._index
4644-        parts: list[exp.Identifier] | None = None
4645-        all_comments: list[str] | None = None
4646-
4647-        while self._match_set(self.IDENTIFIER_TOKENS):
4648-            token = self._prev
4649-            comments = self._prev_comments
4650-
4651-            has_dot = self._match(TokenType.DOT)
4652-            curr_tt = self._curr.token_type
…[1255 chars elided]…
    if fast:
4713-            return self._parse_table_parts_fast()
4714-
4715-        catalog: exp.Expr | str | None = None
4716-        db: exp.Expr | str | None = None
4717-        table: exp.Expr | str | None = self._parse_table_part(schema=schema)
4718-
4719-        while self._match(TokenType.DOT):
4720-            if catalog:
4721-                # This allows nesting the table in arbitrarily many dot expressions if needed
4722-                table = self.expression(
0 matches for 'FILE'
[tool_use Bash] {"command": "grep -n \"class Parser\" -A30 sqlglot/dialects/clickhouse.py | head -60; grep -n \"FUNC_TOKENS\" sqlglot/dialects/*.py | head; grep -n \"FUNC_TOKENS\" sqlglot/parser.py | head", "description": "Inspect ClickHouse parser class and FUNC_TOKENS usage"}
[tool_result] 0 matches for 'FUNC_TOKENS'
2 matches in 2 files:

6950:0:
826:0:t.ClassVar = {
[tool_use Bash] {"command": "grep -n \"class Parser\\|FUNCTION_PARSERS\\|FUNCTIONS = \\|TABLE_FUNCTION\\|def _parse_table\" sqlglot/dialects/clickhouse.py | head -30; sed -n 6945,6960p sqlglot/parser.py; grep -n \"def _parse_function_call\" -A30 sqlglot/parser.py | grep -n \"FUNC_TOKENS\\|token_type\" ", "description": "Locate ClickHouse parser and function-call token checks"}
[tool_result] 0 matches for 'class Parser\|FUNCTION_PARSERS\|FUNCTIONS = \|TABLE_FUNCTION\|def _parse_table'
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

14:6925-        token_type = self._curr.token_type
18:6929-        after_dot = prev.token_type == TokenType.DOT
23:6934-            and token_type not in self.INVALID_FUNC_NAME_TOKENS
29:6940-        if self._next.token_type != TokenType.L_PAREN:
30:6941-            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS and not after_dot:
[tool_use Bash] {"command": "grep -n \"^class \\|^    class \\|FUNC\\|Parser\" sqlglot/dialects/clickhouse.py | head -60; sed -n 6925,6945p sqlglot/parser.py", "description": "Outline ClickHouse dialect classes and function-call check"}
[tool_result] 7 matches in 6 files:

116:0:TokenType.AGGREGATEFUNCTION,
117:0:TokenType.SIMPLEAGGREGATEFUNCTION,
15:0:
17:0:bool | str = False
71:0:
sqlglot/dialects/clickhouse.py:10:from sqlglot.parsers.clickhouse import ClickHouseParser
sqlglot/dialects/clickhouse.py:129:Parser = ClickHouseParser
        token_type = self._curr.token_type
        this: str | exp.Expr = self._curr.text
        upper = self._curr.text.upper()

        after_dot = prev.token_type == TokenType.DOT
        parser = self.NO_PAREN
…[60 chars elided]…
al_parens
            and parser
            and token_type not in self.INVALID_FUNC_NAME_TOKENS
            and not after_dot
        ):
            self._advance()
            return self._parse_window(parser(self))

        if self._next.token_type != TokenType.L_PAREN:
            if optional_parens and token_type in self.NO_PAREN_FUNCTIONS and not after_dot:
                self._advance()
                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())

            return None
[assistant] The ClickHouse parser lives in `sqlglot/parsers/clickhouse.py`. Let me look at it.
[tool_use Bash] {"command": "wc -l sqlglot/parsers/clickhouse.py && grep -n \"FUNC_TOKENS\\|_parse_table_part\\|TABLE_FUNC\\|class \\|    def \" sqlglot/parsers/clickhouse.py | head -80", "description": "Outline ClickHouse parser methods and token sets"}
[tool_result] 930
45 matches in 34 files:

239:0:
26:0:list, dialect: t.Any) -> E:
333:0:str) -> tuple[str, Sequence[str]] | None:
464:0:
469:0:
474:0:
479:0:
486:0:
512:0:
529:0:
543:0:
567:0:exp.Expr | None = None) -> exp.Expr | None:
600:0:exp.Expr | None) -> exp.Not | exp.In:
638:0:bool = False) -> exp.StrPosition:
642:0:
735:0:exp.Func | None = None) -> list[exp.Expr] | None:
746:0:
762:0:
769:0:bool = False) -> list[exp.Expr]:
792:0:
802:0:str | None = None) -> exp.IndexColumnConstraint:
817:0:
832:0:
8
…[436 chars elided]…
qlglot/parsers/clickhouse.py:665:def _parse_join(
sqlglot/parsers/clickhouse.py:687:def _parse_function(
sqlglot/parsers/clickhouse.py:715:exp_class = exp.ParameterizedAgg if params else exp.AnonymousAggFunc
sqlglot/parsers/clickhouse.py:772:def _parse_column_def(
sqlglot/parsers/clickhouse.py:780:def _parse_primary_key(
sqlglot/parsers/clickhouse.py:839:exp.ReplacePartition(expression=partition, source=self._parse_table_parts())
sqlglot/parsers/clickhouse.py:919:this = self._parse_table_parts()
[tool_use Bash] {"command": "sed -n 310,335p sqlglot/parsers/clickhouse.py; sed -n 600,655p sqlglot/parsers/clickhouse.py", "description": "Read ClickHouse FUNC_TOKENS and _parse_table"}
[tool_result]         "UTCTIMESTAMP": exp.UtcTimestamp.from_arg_list,
    }

    AGG_FUNCTIONS = AGG_FUNCTIONS
    AGG_FUNCTIONS_SUFFIXES = AGG_FUNCTIONS_SUFFIXES

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

    @classmet
…[1755 chars elided]…
khouse.com/docs/en/sql-reference/statements/select/with/
    def _parse_cte(self) -> exp.CTE | None:
        # WITH <identifier> AS <subquery expression>
        cte: exp.CTE | None = self._try_parse(super()._parse_cte)

        if not cte:
            # WITH <expression> AS <identifier>
            cte = self.expression(
                exp.CTE(this=self._parse_assignment(), alias=self._parse_table_alias(), scalar=True)
            )

        return cte

    def _parse_join_parts(
        self,
[assistant] The ClickHouse parser's `FUNC_TOKENS` doesn't include `FILE`, so `file(` falls through to table-alias parsing. Adding it there, scoped to ClickHouse, matches how `AND`/`OR`/`SET` are already handled.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195517-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.SET,\n    }\n\n    RESERVED_TOKENS", "new_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.SET,\n        TokenType.FILE,\n    }\n\n    RESERVED_TOKENS"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195517-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\ns=\\\"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\"\nprint(sqlglot.parse_one(s, dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM file('a', 'Parquet') AS t\\\", dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT file FROM t\\\", dialect='clickhouse').sql(dialect='clickhouse'))\n\"", "description": "Verify the reported round-trip now works"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns=\\\"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\"\nprint(sqlglot.parse_one(s, dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM file('a', 'Parquet') AS t\\\", dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one(\\\"SELECT file FROM t\\\", dialect='clickhouse').sql(dialect='clickhouse'))\n\"", "description": "Verify the reported round-trip now works"}
[tool_result] CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
SELECT * FROM file('a', 'Parquet') AS t
SELECT file FROM t
[assistant] The reported case round-trips now. Next I'll add a regression test to the ClickHouse dialect tests.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_clickhouse.py | head -5; grep -n \"validate_identity(\\\"SELECT \\* FROM s3\\|FROM s3\\|table function\" tests/dialects/test_clickhouse.py | head", "description": "Find a spot in ClickHouse tests for a new case"}
[tool_result] 30 matches in 30 files:

1430:0:
1467:0:
15:0:
rg: regex parse error:
    (?:validate_identity("SELECT \* FROM s3|FROM s3|table function)
    ^
error: unclosed group
0 matches for 'validate_identity("SELECT \* FROM s3\|FROM s3\|table function'
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_clickhouse.py | head -8; grep -n \"def test_ddl\" -A4 tests/dialects/test_clickhouse.py | head", "description": "List ClickHouse test method names"}
[tool_result] 30 matches in 30 files:

1430:0:
1467:0:
15:0:
1533:0:
1546:0:
1552:0:
955:    def test_ddl(self):
956-        db_table_expr = exp.Table(this=None, db=exp.to_identifier("foo"), catalog=None)
957-        create_with_cluster = exp.Create(
958-            this=db_table_expr,
959-            kind="DATABASE",
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_clickhouse.py | sed -n 1,6p; grep -n \"CREATE VIEW\" tests/dialects/test_clickhouse.py | head -3", "description": "Find test methods and existing CREATE VIEW cases"}
[tool_result] 30 matches in 30 files:

1430:0:
1467:0:
15:0:
1533:0:
5 matches in 1 files:

tests/dialects/test_clickhouse.py:1860:"CREATE VIEW v DEFINER='alice' SQL SECURITY DEFINER AS SELECT 1",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195517-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "offset": 1850, "limit": 30}
[tool_result] 1850	            write={
1851	                "clickhouse": r"splitByRegexp('\\d+', x)",
1852	                "duckdb": r"STR_SPLIT_REGEX(x, '\d+')",
1853	                "hive": r"SPLIT(x, '\\d+')",
1854	            },
1855	        )
1856	        self.validate_identity("splitByChar('', x)")
1857	
1858	    def test_sql_security(self):
1859	        stmts = [
1860	            "CREATE VIEW v DEFINER='alice' SQL SECURITY DEFINER AS SELECT 1",
1861	            "CREATE VIEW v SQL SECURITY DEFINER DEFI
…[318 chars elided]…
FINER='alice' AS SELECT 1",
1866	            "CREATE MATERIALIZED VIEW v TO t SQL SECURITY INVOKER AS SELECT 1",
1867	            "CREATE MATERIALIZED VIEW v TO t SQL SECURITY NONE AS SELECT 1",
1868	            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER='alice'",
1869	            "ALTER TABLE v MODIFY SQL SECURITY DEFINER DEFINER=CURRENT_USER",
1870	        ]
1871	        for stmt in stmts:
1872	            with self.subTest(stmt):
1873	                self.validate_identity(stmt)
1874	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195517-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"splitByChar('', x)\")\n\n    def test_sql_security(self):", "new_string": "        self.validate_identity(\"splitByChar('', x)\")\n\n    def test_file_table_function(self):\n        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n        self.validate_identity(\"SELECT * FROM file('data.csv', 'CSV') AS t\")\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195517-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Now I'll run the project's test command and the style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 900000}
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
1115 passed, 18164 subtests passed in 46.43s
[assistant] All 1115 tests pass. I'll check the style on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -8; git status --short", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[assistant] `file(...)` now parses as a table function in the ClickHouse dialect, and your example round-trips unchanged. The full test suite passes (1115 tests) and ruff is clean. I haven't committed anything.

**Cause:** `file` is tokenized as `TokenType.FILE`, which isn't in the ClickHouse parser's `FUNC_TOKENS`. So `_parse_table_part` never treated `file(` as a function call. It read `file` as a bare table name and then took the parenthesised arguments as column aliases, which is where the `AS _t0("base/dir/*.parquet", Parquet)` output came from.

**Fix:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS`, next to the existing `AND`/`OR`/`SET` entries. I scoped it to ClickHouse rather than the base parser, since the report is ClickHouse-specific and the base change would affect every dialect.
- `tests/dialects/test_clickhouse.py`: added `test_file_table_function` with the reported `CREATE VIEW` statement and a `SELECT * FROM file('data.csv', 'CSV') AS t` case.

A bare column named `file` (e.g. `SELECT file FROM t`) still parses and round-trips as before.
