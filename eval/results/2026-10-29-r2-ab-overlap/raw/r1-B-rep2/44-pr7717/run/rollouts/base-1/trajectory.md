# trajectory base-1

final message:
Fixed: ClickHouse `file(...)` now parses as a table function and round-trips unchanged.

**Cause:** `FILE` is a keyword token. In table position, `_parse_table_part` only parses a function when the token is in `FUNC_TOKENS`, and `FILE` wasn't in that set for ClickHouse. So `file` was read as a bare table name, and `('base/dir/*.parquet', Parquet)` was taken as a column alias list.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS`, alongside its existing `AND`/`OR`/`SET` additions. Other dialects are unaffected.
- `tests/dialects/test_clickhouse.py`: added four `validate_identity` cases to `test_clickhouse`: the reported CREATE VIEW, a plain FROM select, an aliased select, and a JOIN.

**Probe results:** before the fix, the reported statement and the FROM, CTE, subquery, and IN variants all produced the broken `file AS _t0(...)` output, and the aliased and JOIN forms raised ParseError. After the fix, every variant reads OK. `url(...)` and `remote(...)` were already fine and still are.

**Tests:**
- `tests/dialects/test_clickhouse.py`: 30 passed.
- Full suite: 1114 passed, 0 failures. I didn't capture the exit code, but the output reports no failures.

**Setup note:** the project interpreter doesn't have sqlglot installed, and `probe_parse.py` run with `-I` can't import the repo. I ran the probe with `PYTHONPATH` set to the worktree, without `-I`.

No ERR lines were left outside the reported construct.

## events
[tool_use Skill] {"skill": "parse-failure-triage", "args": "ClickHouse dialect: `file('base/dir/*.parquet', Parquet)` in FROM parses as a table alias and does not round-trip: outputs `FROM file AS _t0(\"base/dir/*.parquet\", Parquet)`. Should parse as a table function and round-trip unchanged."}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/.claude/skills/parse-failure-triage

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: inpu
…[757 chars elided]…
tatement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.


ARGUMENTS: ClickHouse dialect: `file('base/dir/*.parquet', Parquet)` in FROM parses as a table alias and does not round-trip: outputs `FROM file AS _t0("base/dir/*.parquet", Parquet)`. Should parse as a table function and round-trip unchanged.
[tool_use Write] {"file_path": "/tmp/ch-file-probe/stmts.sql", "content": "CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\nSELECT c1 FROM file('base/dir/*.parquet', Parquet)\nSELECT c1 FROM file('base/dir/*.parquet', Parquet, 'c1 String')\nSELECT c1 FROM file('base/dir/*.parquet')\nSELECT c1 FROM file('base/dir/*.parquet') AS f\nSELECT f.c1 FROM file('base/di
…[40 chars elided]…
 FROM t JOIN file('base/dir/*.parquet', Parquet) AS f ON t.c1 = f.c1\nWITH x AS (SELECT c1 FROM file('base/dir/*.parquet', Parquet)) SELECT c1 FROM x\nSELECT c1 FROM (SELECT c1 FROM file('base/dir/*.parquet', Parquet))\nSELECT c1 FROM t WHERE c1 IN (SELECT c1 FROM file('base/dir/*.parquet', Parquet))\nSELECT c1 FROM url('http://x/y.csv', CSV, 'c1 String')\nSELECT c1 FROM remote('host', db.tbl)\n"}
[tool_result] File created successfully at: /tmp/ch-file-probe/stmts.sql (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read clickhouse < /tmp/ch-file-probe/stmts.sql", "description": "Probe ClickHouse file() table function variants"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"import sys; print(sys.path)\"; <work>/env-sqlglot/bin/python -m pip list 2>/dev/null | grep -i sqlglot", "description": "Check the project env for sqlglot install"}
[tool_result] ['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
[assistant] The project env doesn't have sqlglot installed, and `-I` also drops `PYTHONPATH`. The repo is trusted code, so I'll run the probe without `-I` and point `PYTHONPATH` at the worktree.
[tool_use Bash] {"command": "PYTHONPATH=\"$PWD\" <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read clickhouse < /tmp/ch-file-probe/stmts.sql", "description": "Probe ClickHouse file() variants with worktree on path"}
[tool_result ERROR] Exit code 1
OK        CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
          CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet)
OK        SELECT c1 FROM file('base/dir/*.parquet', Parquet)
          SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet)
OK        SELECT c1 FROM file('base/dir/*.parquet', Parquet, 'c1 String')
          SELECT c1 FROM file AS _t0("base/dir/*.par
…[855 chars elided]…
         SELECT c1 FROM (SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet))
OK        SELECT c1 FROM t WHERE c1 IN (SELECT c1 FROM file('base/dir/*.parquet', Parquet))
          SELECT c1 FROM t WHERE c1 IN (SELECT c1 FROM file AS _t0("base/dir/*.parquet", Parquet))
OK        SELECT c1 FROM url('http://x/y.csv', CSV, 'c1 String')
          SELECT c1 FROM url('http://x/y.csv', CSV, 'c1 String')
OK        SELECT c1 FROM remote('host', db.tbl)
          SELECT c1 FROM remote('host', db.tbl)
[assistant] Reproduced: the `file(...)` form in FROM, CTE, subquery, and IN turns into a table alias, while `url(...)` and `remote(...)` are fine. Next I'll find where `file` is special-cased.
[tool_use Bash] {"command": "grep -rn -i \"\\\"FILE\\\"\\|'FILE'\\|\\bFILE\\b\" sqlglot/dialects/clickhouse.py sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/dialect.py | head -40; echo ---; grep -rn -i \"table_function\\|TABLE_FUNCTION\\|_parse_table_parts\\|def _parse_table(\" sqlglot/parser.py | head -30", "description": "Locate file keyword handling in tokenizer and parser"}
[tool_result] sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
sqlglot/parser.py:701:        TokenType.FILE,
sqlglot/parser.py:8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
sqlglot/parser.py:9536:                # T-SQL's external file format case
---
sqlglot/parser.py:1073:        exp.Table: lambda self: self._parse_table_parts(),
sqlglot/parser.py:2201:            this = self._parse_table_parts(schema=True)
sqlglot/parser.py:2218:        table = self._p
…[1599 chars elided]…
sqlglot/parser.py:4881:            this.set("indexed", self._parse_table_parts())
sqlglot/parser.py:7083:        this = self._parse_table_parts(schema=True)
sqlglot/parser.py:8962:            this = self._parse_table_parts()
sqlglot/parser.py:8978:            this = self._parse_table_parts()
sqlglot/parser.py:9689:        securable = self._try_parse(self._parse_table_parts)
sqlglot/parser.py:9770:                this=exp.var("FORMAT_NAME"), value=self._parse_string() or self._parse_table_parts()
[tool_use Bash] {"command": "sed -n 690,720p sqlglot/parser.py; echo ---; sed -n 4776,4800p sqlglot/parser.py; echo ---; grep -n \"TokenType.FILE\\|FILE:\" sqlglot/parser.py sqlglot/dialects/clickhouse.py sqlglot/tokens.py; echo ---; sed -n 290,300p sqlglot/tokens.py", "description": "Inspect FILE token usages and table parsing entry"}
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
…[1336 chars elided]…
2:TokenType.FILE_FORMAT,
sqlglot/parser.py:701:TokenType.FILE,
sqlglot/tokens.py:297:"FILE": TokenType.FILE,
---
        "ESCAPE": TokenType.ESCAPE,
        "EXCEPT": TokenType.EXCEPT,
        "EXECUTE": TokenType.EXECUTE,
        "EXISTS": TokenType.EXISTS,
        "FALSE": TokenType.FALSE,
        "FETCH": TokenType.FETCH,
        "FILTER": TokenType.FILTER,
        "FILE": TokenType.FILE,
        "FIRST": TokenType.FIRST,
        "FULL": TokenType.FULL,
        "FUNCTION": TokenType.FUNCTION,
[tool_use Bash] {"command": "grep -n \"FUNC_TOKENS = \\|FILE_FORMAT,\\|TokenType.FILE_FORMAT\" sqlglot/parser.py | head; sed -n 615,626p sqlglot/parser.py; echo ---; grep -n \"def _parse_table_part\\b\\|def _parse_table_part(\" sqlglot/parser.py; sed -n \"$(grep -n 'def _parse_table_part(' sqlglot/parser.py | cut -d: -f1),+25p\" sqlglot/parser.py", "description": "Check FUNC_TOKENS and table part parsing"}
[tool_result] 1 matches in 1 files:

sqlglot/parser.py:622:TokenType.FILE_FORMAT,
        *Tokenizer.SINGLE_TOKENS.values(),
        TokenType.SELECT,
    } - {TokenType.IDENTIFIER}

    DB_CREATABLES: t.ClassVar = {
        TokenType.DATABASE,
        TokenType.DICTIONARY,
        TokenType.FILE_FORMAT,
        TokenType.MODEL,
        TokenType.NAMESPACE,
        TokenType.SCHEMA,
        TokenType.SEMANTIC_VIEW,
---
rg: regex parse error:
    (?:def _parse_table_part\b|def _parse_table_part()
    ^
error: 
…[554 chars elided]…
 list[str] | None = None

        while self._match_set(self.IDENTIFIER_TOKENS):
            token = self._prev
            comments = self._prev_comments

            has_dot = self._match(TokenType.DOT)
            curr_tt = self._curr.token_type

            if not has_dot:
                if curr_tt in self.TABLE_POSTFIX_TOKENS:
                    self._retreat(index)
                    return None
            elif curr_tt not in self.IDENTIFIER_TOKENS:
                self._retreat(index)
[tool_use Bash] {"command": "grep -n \"^    [A-Z_]*: t.ClassVar = {\" sqlglot/parser.py | awk -F: '$1>560 && $1<760'; echo ---; grep -n \"FUNC_TOKENS\" sqlglot/parser.py sqlglot/dialects/clickhouse.py | head; echo ---; grep -n \"FILE\\b\" sqlglot/dialects/clickhouse.py | head", "description": "Identify which token set contains FILE"}
[tool_result] rg: regex parse error:
    (?:^    [A-Z_]*: t.ClassVar = {)
                                   ^
error: repetition quantifier expects a valid decimal
---
2 matches in 1 files:

sqlglot/parser.py:826:FUNC_TOKENS: t.ClassVar = {
sqlglot/parser.py:6950:elif token_type not in self.FUNC_TOKENS:
---
0 matches for 'FILE\b'
[tool_use Bash] {"command": "sed -n 826,835p sqlglot/parser.py; echo ...; sed -n 826,900p sqlglot/parser.py | grep -n \"FILE\\|ID_VAR\\|}\" | head; echo ---; sed -n 6935,6960p sqlglot/parser.py", "description": "Check FUNC_TOKENS composition and function gating"}
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
...
51:    }
55:    }
59:    }
63:    }
69:    }
---
            and not after_dot
        ):
            self._advance()
            return self._parse_window(parser(self))

 
…[191 chars elided]…
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
[assistant] `FILE` is a keyword token, and `_parse_table_part` only parses a function when the token is in `FUNC_TOKENS`, which doesn't include `FILE`. Before deciding where to add it, I'll check how other dialects extend `FUNC_TOKENS`.
[tool_use Bash] {"command": "grep -rn \"FUNC_TOKENS\" sqlglot/dialects/ | head -20; echo ---; sed -n 1,40p sqlglot/dialects/clickhouse.py | grep -n \"import\" ; grep -n \"class Parser\" sqlglot/dialects/clickhouse.py; grep -n \"TABLE_FUNCTION\\|\\\"URL\\\"\\|\\\"REMOTE\\\"\\|\\\"S3\\\"\" sqlglot/dialects/clickhouse.py | head", "description": "See dialect FUNC_TOKENS overrides and ClickHouse table function handling"}
[tool_result] ---
1:from __future__ import annotations
4:from sqlglot import exp, tokens
5:from sqlglot.dialects.dialect import (
9:from sqlglot.generators.clickhouse import ClickHouseGenerator
10:from sqlglot.parsers.clickhouse import ClickHouseParser
11:from sqlglot.tokens import TokenType
12:from sqlglot.typing.clickhouse import EXPRESSION_METADATA
0 matches for 'class Parser'
0 matches for 'TABLE_FUNCTION\|"URL"\|"REMOTE"\|"S3"'
[tool_use Bash] {"command": "wc -l sqlglot/parsers/clickhouse.py; grep -n \"FUNC\\|_TOKENS\\|def _parse_table\\|def _parse_table_part\\|TokenType.FILE\\|_parse_function\" sqlglot/parsers/clickhouse.py | head -60; echo ---; ls sqlglot/parsers | head -50", "description": "Survey ClickHouse parser for function and table token overrides"}
[tool_result] 930
36 matches in 13 files:

211:0:list[str] = sorted(
234:0:Mapping[str, tuple[str, str | None]] = {
235:0:(f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
236:0:(f, None) for f in AGG_FUNCTIONS}
344:0:= AGG_FUNC_MAPPING.get(name)) is None:
345:0:
363:0:v for k, v in parser.Parser.FUNCTION_PARSERS.items() if k != "MATCH"},
369:0:lambda self: exp.Struct.from_arg_list(self._parse_function_args(alias=True)),
370:0:lambda self: exp.and_(*self._parse_function_args(alias=False)),
371
…[2051 chars elided]…
ouse.py  32.9K
databricks.py  1.7K
doris.py  5.0K
dremio.py  3.8K
drill.py  662B
druid.py  108B
duckdb.py  15.5K
dune.py  124B
exasol.py  6.5K
fabric.py  1.3K
hive.py  11.0K
materialize.py  1.3K
mysql.py  24.1K
oracle.py  9.4K
postgres.py  12.9K
presto.py  5.3K
prql.py  6.9K
redshift.py  5.8K
risingwave.py  2.2K
singlestore.py  10.4K
snowflake.py  53.1K
solr.py  353B
spark.py  5.2K
spark2.py  4.2K
sqlite.py  3.5K
starrocks.py  6.4K
tableau.py  507B
teradata.py  7.4K
trino.py  2.0K
tsql.py  26.4K
[tool_use Bash] {"command": "sed -n 314,330p sqlglot/parsers/clickhouse.py; echo ---; sed -n 608,640p sqlglot/parsers/clickhouse.py; echo ---; sed -n 687,700p sqlglot/parsers/clickhouse.py", "description": "Read ClickHouse FUNC_TOKENS and table parse override"}
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
---
    def _parse_table(
        self,
        schema: bool = False,
        joins: bool = False,
        alia
…[910 chars elided]…
exp.StrPosition:
        return super()._parse_position(haystack_first=True)

---
    def _parse_function(
        self,
        functions: dict[str, t.Callable] | None = None,
        anonymous: bool = False,
        optional_parens: bool = True,
        any_token: bool = False,
    ) -> exp.Expr | None:
        expr = super()._parse_function(
            functions=functions,
            anonymous=anonymous,
            optional_parens=optional_parens,
            any_token=any_token,
        )
[assistant] ClickHouse already extends `FUNC_TOKENS` with its own keyword tokens (`AND`, `OR`, `SET`), so adding `FILE` there follows the existing pattern and leaves other dialects alone. Applying that one-line change:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        TokenType.AND,\n        TokenType.OR,\n        TokenType.SET,\n    }", "new_string": "        TokenType.AND,\n        TokenType.FILE,\n        TokenType.OR,\n        TokenType.SET,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=\"$PWD\" <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read clickhouse < /tmp/ch-file-probe/stmts.sql", "description": "Re-run probe after adding FILE to ClickHouse FUNC_TOKENS"}
[tool_result] OK        CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
          CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
OK        SELECT c1 FROM file('base/dir/*.parquet', Parquet)
          SELECT c1 FROM file('base/dir/*.parquet', Parquet)
OK        SELECT c1 FROM file('base/dir/*.parquet', Parquet, 'c1 String')
          SELECT c1 FROM file('base/dir/*.parquet', Parquet, 'c1 String')
OK  
…[775 chars elided]…
', Parquet))
          SELECT c1 FROM (SELECT c1 FROM file('base/dir/*.parquet', Parquet))
OK        SELECT c1 FROM t WHERE c1 IN (SELECT c1 FROM file('base/dir/*.parquet', Parquet))
          SELECT c1 FROM t WHERE c1 IN (SELECT c1 FROM file('base/dir/*.parquet', Parquet))
OK        SELECT c1 FROM url('http://x/y.csv', CSV, 'c1 String')
          SELECT c1 FROM url('http://x/y.csv', CSV, 'c1 String')
OK        SELECT c1 FROM remote('host', db.tbl)
          SELECT c1 FROM remote('host', db.tbl)
[assistant] Every variant now round-trips. Next I'll add regression cases to the existing ClickHouse test function, next to the existing table-function tests.
[tool_use Bash] {"command": "grep -n \"def test_\\|remote(\\|url(\" tests/dialects/test_clickhouse.py | head -80", "description": "Locate ClickHouse test functions and table function cases"}
[tool_result] rg: regex parse error:
    (?:def test_|remote(|url()
                       ^
error: unclosed group
0 matches for 'def test_\|remote(\|url('
[tool_use Bash] {"command": "grep -n -F -e \"def test_\" -e \"remote(\" -e \"url(\" tests/dialects/test_clickhouse.py | head -80", "description": "Locate ClickHouse test functions and table function cases"}
[tool_result] 15:    def test_clickhouse(self):
600:            "INSERT INTO FUNCTION remote('localhost', default.simple_table) VALUES (100, 'inserted via remote()')",
601:            "INSERT INTO FUNCTION remote('localhost', default.simple_table) VALUES ((100), ('inserted via remote()'))",
739:    def test_clickhouse_values(self):
778:    def test_cte(self):
798:    def test_ternary(self):
836:    def test_parameterization(self):
849:    def test_signed_and_unsigned_types(self):
870:    def test_geom_types(s
…[404 chars elided]…
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
[tool_use Bash] {"command": "sed -n 596,606p tests/dialects/test_clickhouse.py", "description": "View context around existing table function tests"}
[tool_result]         self.validate_identity(
            "INSERT INTO FUNCTION s3('url', 'CSV', 'name String, value UInt32', 'gzip') SELECT name, value FROM existing_table"
        )
        self.validate_identity(
            "INSERT INTO FUNCTION remote('localhost', default.simple_table) VALUES (100, 'inserted via remote()')",
            "INSERT INTO FUNCTION remote('localhost', default.simple_table) VALUES ((100), ('inserted via remote()'))",
        )
        self.validate_identity(
            """INSERT INTO TABLE FUNCTION hdfs('hdfs://hdfs1:9000/test', 'TSV', 'name String, column2 UInt32, column3 UInt32') VALUES ('test', 1, 2)""",
            """INSERT INTO FUNCTION hdfs('hdfs://hdfs1:9000/test', 'TSV', 'name String, column2 UInt32, column3 UInt32') VALUES (('test'), (1), (2))""",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "old_string": "            \"\"\"INSERT INTO FUNCTION hdfs('hdfs://hdfs1:9000/test', 'TSV', 'name String, column2 UInt32, column3 UInt32') VALUES (('test'), (1), (2))\"\"\",\n        )", "new_string": "            \"\"
…[243 chars elided]…
        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n        self.validate_identity(\"SELECT f.c1 FROM file('base/dir/*.parquet', Parquet) AS f\")\n        self.validate_identity(\n            \"SELECT t.c1 FROM t JOIN file('base/dir/*.parquet', Parquet) AS f ON t.c1 = f.c1\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-162323-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Now the dialect test file, then the full suite as the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -15", "description": "Run ClickHouse dialect test file"}
[tool_result] ........... [ 36%]
...................                                                        [100%]
30 passed, 275 subtests passed in 0.22s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"EXIT=${PIPESTATUS[0]}\"", "description": "Run full test suite as final gate", "timeout": 300000}
[tool_result] ............. [  9%]
........................................................................ [ 15%]
.............. [ 17%]
............................................................. [ 22%]
........................................................................................... [ 30%]
..................................................................... [ 36%]
............................................................................................................. [ 46%]
...............
…[203 chars elided]…
. [ 64%]
......................................................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 50.16s
EXIT=
[tool_use Bash] {"command": "git diff --stat; git status --short", "description": "Show changed files in worktree"}
[tool_result] sqlglot/parsers/clickhouse.py     | 1 +
 tests/dialects/test_clickhouse.py | 8 ++++++++
 2 files changed, 9 insertions(+)
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[assistant] Fixed: ClickHouse `file(...)` now parses as a table function and round-trips unchanged.

**Cause:** `FILE` is a keyword token. In table position, `_parse_table_part` only parses a function when the token is in `FUNC_TOKENS`, and `FILE` wasn't in that set for ClickHouse. So `file` was read as a bare table name, and `('base/dir/*.parquet', Parquet)` was taken as a column alias list.

**Change:**
- `sqlglot/parsers/clickhouse.py`: added `TokenType.FILE` to the ClickHouse `FUNC_TOKENS`, alongside its existing `AND`/`OR`/`SET` additions. Other dialects are unaffected.
- `tests/dialects/test_clickho
…[276 chars elided]…
ile AS _t0(...)` output, and the aliased and JOIN forms raised ParseError. After the fix, every variant reads OK. `url(...)` and `remote(...)` were already fine and still are.

**Tests:**
- `tests/dialects/test_clickhouse.py`: 30 passed.
- Full suite: 1114 passed, 0 failures. I didn't capture the exit code, but the output reports no failures.

**Setup note:** the project interpreter doesn't have sqlglot installed, and `probe_parse.py` run with `-I` can't import the repo. I ran the probe with `PYTHONPATH` set to the worktree, without `-I`.

No ERR lines were left outside the reported construct.
