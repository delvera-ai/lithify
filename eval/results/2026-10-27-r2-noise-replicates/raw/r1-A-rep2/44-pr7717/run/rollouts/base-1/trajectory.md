# trajectory base-1

final message:
`file(...)` now parses as a table function in ClickHouse and round-trips unchanged. Your example outputs `CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)`.

**Cause:** `FILE` is a base-tokenizer keyword, but `_parse_function` only accepts tokens in `FUNC_TOKENS`, and `FILE` wasn't in that set. So `file` was parsed as a plain table name, and the parenthesized arguments were taken as column aliases.

**Change:**
- `sqlglot/parser.py`: added `TokenType.FILE` to `FUNC_TOKENS`. This is in the base parser, so it applies to every dialect, not just ClickHouse. I did not add a ClickHouse-only override because ClickHouse has no parser class.
- `tests/dialects/test_clickhouse.py`: added `test_file_table_function` with your example and an aliased `file('a.csv', CSV) AS f` case.

**Verification:** the full suite passes with the test runner you gave (1114 passed, 18164 subtests). `file` as a column name still round-trips. I did not run `make check` or the linter.

## events
[tool_use Bash] {"command": "rtk grep -rn -i '\"file\"\\|FILE\\b' sqlglot/dialects/clickhouse.py sqlglot/parser.py | head -40; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT c1 FROM file('base/dir/*.parquet', Parquet)\\\", dialect='clickhouse')\nprint(repr(e))\n\"", "description": "Search FILE handling and reproduce parse tree"}
[tool_result] (eval):1: command not found: rtk
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
[tool_use Bash] {"command": "grep -rn -i 'file' sqlglot/dialects/clickhouse.py | head -30; grep -n 'FILE\\|\"FILE\"' sqlglot/tokens.py sqlglot/parser.py | head; grep -rn -i \"file(\" tests/dialects/test_clickhouse.py | head", "description": "Search for file-related handling in ClickHouse code and tests"}
[tool_result] sqlglot/tokens.py:297:        "FILE": TokenType.FILE,
sqlglot/parser.py:622:        TokenType.FILE_FORMAT,
sqlglot/parser.py:701:        TokenType.FILE,
sqlglot/parser.py:1700:        "FILE_FORMAT",
sqlglot/parser.py:3641:                    files=self._match_text_seq("FROM", "FILES")
sqlglot/parser.py:8850:        elif self._match_text_seq("FILESTREAM_ON", advance=False):
sqlglot/parser.py:8862:        elif self._match_text_seq("FILE", "FORMAT") or self._match_text_seq("FILEFORMAT"):
sqlglot/parser.py:8864:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:9533:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9535:            elif prev == "FILE_FORMAT":
tests/dialects/test_clickhouse.py:1364:            "CREATE DICTIONARY dict1 (key UInt64) PRIMARY KEY (key) SOURCE(FILE(PATH '/tmp/test.csv' FORMAT CSVWithNames)) LIFETIME(MIN 0 MAX 1) LAYOUT(FLAT())"
[tool_use Bash] {"command": "sed -n 690,710p sqlglot/parser.py; grep -n 'FUNC_TOKENS = \\|TokenType.FILE\\b' sqlglot/parser.py sqlglot/dialects/*.py | head; grep -n 'def _parse_table_part\\b' -A25 sqlglot/parser.py | head -50", "description": "Inspect token sets and table part parsing"}
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
…[685 chars elided]…
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
[tool_use Bash] {"command": "grep -n 'FUNC_TOKENS' sqlglot/parser.py | head -5; grep -n 'FUNC_TOKENS' -A3 sqlglot/dialects/clickhouse.py | head -30; grep -n 'class Parser' -A3 sqlglot/dialects/clickhouse.py", "description": "Locate FUNC_TOKENS definitions"}
[tool_result] 826:    FUNC_TOKENS: t.ClassVar = {
6950:        elif token_type not in self.FUNC_TOKENS:
[tool_use Bash] {"command": "sed -n 826,835p sqlglot/parser.py; sed -n 826,870p sqlglot/parser.py | grep -n 'TokenType.F' ; grep -n 'class Parser' -A40 sqlglot/dialects/clickhouse.py | grep -n 'TokenType\\|_TOKENS' | head -20", "description": "Inspect FUNC_TOKENS set and ClickHouse parser overrides"}
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
11:        TokenType.FILTER,
12:        TokenType.FIRST,
13:        TokenType.FORMAT,
[tool_use Bash] {"command": "grep -n 'class Parser' sqlglot/dialects/clickhouse.py; awk '/class Parser\\(parser.Parser\\)/{f=1} f&&/_TOKENS|FUNCTIONS = /{print NR\": \"$0} /class Tokenizer/{f=0}' sqlglot/dialects/clickhouse.py | head -20", "description": "Find ClickHouse Parser class token overrides"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n 'class \\|_TOKENS' sqlglot/dialects/clickhouse.py | head -40", "description": "List classes and token sets in ClickHouse dialect"}
[tool_result] 15:class ClickHouse(Dialect):
71:    class Tokenizer(tokens.Tokenizer):
124:        SINGLE_TOKENS = {
125:            **tokens.Tokenizer.SINGLE_TOKENS,
[tool_use Bash] {"command": "sed -n 15,20p sqlglot/dialects/clickhouse.py; grep -n '^    class \\|^        [A-Z_]* = \\|^        [A-Z_]*: ' sqlglot/dialects/clickhouse.py | sed -n 1,60p", "description": "Show ClickHouse dialect class structure"}
[tool_result] class ClickHouse(Dialect):
    INDEX_OFFSET = 1
    NORMALIZE_FUNCTIONS: bool | str = False
    NULL_ORDERING = "nulls_are_last"
    SUPPORTS_USER_DEFINED_TYPES = False
    SAFE_DIVISION = True
71:    class Tokenizer(tokens.Tokenizer):
72:        COMMENTS = ["--", "#", "#!", ("/*", "*/")]
73:        IDENTIFIERS = ['"', "`"]
74:        IDENTIFIER_ESCAPES = ["\\"]
75:        STRING_ESCAPES = ["'", "\\"]
76:        BIT_STRINGS = [("0b", "")]
77:        HEX_STRINGS = [("0x", ""), ("0X", "")]
78:        HEREDOC_STRINGS = ["$"]
80:        KEYWORDS = {
124:        SINGLE_TOKENS = {
[assistant] The ClickHouse dialect has no parser override, so `FILE` is a base-tokenizer keyword that `_parse_function` never accepts (it isn't in `FUNC_TOKENS`). It falls through to `_parse_id_var`, and the parenthesized args become column aliases. The fix is to add it to `FUNC_TOKENS`.
[tool_use Bash] {"command": "sed -n 836,900p sqlglot/parser.py | grep -n 'TokenType\\.\\(E\\|F\\|G\\)' ", "description": "Find alphabetical insert point in FUNC_TOKENS"}
[tool_result] 1:        TokenType.FILTER,
2:        TokenType.FIRST,
3:        TokenType.FORMAT,
4:        TokenType.GET,
5:        TokenType.GLOB,
56:        TokenType.EQ: exp.EQ,
62:        TokenType.GT: exp.GT,
63:        TokenType.GTE: exp.GTE,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100502-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parser.py", "old_string": "        TokenType.FILTER,\n        TokenType.FIRST,\n        TokenType.FORMAT,\n        TokenType.GET,\n        TokenType.GLOB,", "new_string": "        TokenType.FILE,\n        TokenType.FILTER,\n        TokenType.FIRST,\n        TokenType.FORMAT,\n        TokenType.GET,\n        TokenType.GLOB,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100502-clickhouse-dialect-the-file-tabl/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one('CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file(\\'base/dir/*.parquet\\', Parquet)', dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one('SELECT * FROM file(\\'a.csv\\')', dialect='clickhouse').sql(dialect='clickhouse')
…[17 chars elided]…
parse_one('SELECT file FROM t', dialect='clickhouse').sql(dialect='clickhouse'))\nprint(sqlglot.parse_one('SELECT * FROM file(\\'a.csv\\', CSV) AS f', dialect='clickhouse').sql(dialect='clickhouse'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify round-trip and run full test suite"}
[tool_result] CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)
SELECT * FROM file('a.csv')
SELECT file FROM t
SELECT * FROM file('a.csv', CSV) AS f
............. [  9%]
........................................................................ [ 15%]
.............. [ 17%]
............................................................. [ 22%]
........................................................................................... [ 30%]
.....................
…[385 chars elided]…
....... [ 64%]
......................................................................................................................................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1114 passed, 18164 subtests passed in 52.10s
[assistant] The fix works and the full suite passes. I'll add a regression test next to the existing ClickHouse table-function tests.
[tool_use Bash] {"command": "grep -n 'FROM remote\\|FROM url\\|FROM numbers\\|def test_' tests/dialects/test_clickhouse.py | head -30", "description": "Find a good spot for the regression test"}
[tool_result] 15:    def test_clickhouse(self):
148:            "SELECT number, COUNT() OVER (PARTITION BY number % 3) AS partition_count FROM numbers(10) WINDOW window_name AS (PARTITION BY number) QUALIFY partition_count = 4 ORDER BY number"
163:            "SELECT n, source FROM (SELECT toFloat32(number % 10) AS n, 'original' AS source FROM numbers(10) WHERE number % 3 = 1) ORDER BY n WITH FILL"
166:            "SELECT n, source FROM (SELECT toFloat32(number % 10) AS n, 'original' AS source FROM numbers(10
…[998 chars elided]…
est_agg_functions_multiple_suffixes(self):
1526:                "FROM (SELECT sumState(toFloat64(number)) AS agg FROM numbers(10)))"
1533:    def test_detach(self):
1546:    def test_drop_on_cluster(self):
1552:    def test_datetime_funcs(self):
1584:    def test_convert(self):
1611:    def test_timestr_to_time(self):
1675:    def test_grant(self):
1679:    def test_revoke(self):
1683:    def test_array_join(self):
1710:    def test_traverse_scope(self):
1716:    def test_window_functions(self):
[tool_use Bash] {"command": "sed -n 1,14p tests/dialects/test_clickhouse.py | grep -n import; sed -n 1533,1546p tests/dialects/test_clickhouse.py", "description": "Check test imports and surrounding test code"}
[tool_result] 1:from datetime import date, datetime, timezone
2:from sqlglot import exp, parse_one
3:from sqlglot.dialects import ClickHouse
4:from sqlglot.expressions import convert
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer import traverse_scope
7:from sqlglot.optimizer.qualify_columns import quote_identifiers
8:from tests.dialects.test_dialect import Validator
9:from sqlglot.errors import ErrorLevel
    def test_detach(self):
        for kind in ("TABLE", "VIEW", "DICTION
…[161 chars elided]…
idate_identity(f"DETACH {kind} IF EXISTS t")
                self.validate_identity(f"DETACH {kind} IF EXISTS db.t")
                self.validate_identity(f"DETACH {kind} t ON CLUSTER c")
                self.validate_identity(f"DETACH {kind} t PERMANENTLY")
                self.validate_identity(f"DETACH {kind} t SYNC")
                self.validate_identity(
                    f"DETACH {kind} IF EXISTS db.t ON CLUSTER c PERMANENTLY SYNC"
                )

    def test_drop_on_cluster(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100502-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py", "old_string": "    def test_drop_on_cluster(self):", "new_string": "    def test_file_table_function(self):\n        self.validate_identity(\n            \"CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)\"\n        )\n        self.validate_identity(\"SELECT * FROM file('a.csv', CSV) AS f\")\n\n    def test_drop_on_cluster(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100502-clickhouse-dialect-the-file-tabl/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py -k file_table 2>&1 | tail -3; git stash list >/dev/null; git diff --stat", "description": "Run new test and show diff stat"}
[tool_result] .                                                                        [100%]
1 passed, 30 deselected in 0.05s
 sqlglot/parser.py                 | 1 +
 tests/dialects/test_clickhouse.py | 6 ++++++
 2 files changed, 7 insertions(+)
[assistant] `file(...)` now parses as a table function in ClickHouse and round-trips unchanged. Your example outputs `CREATE VIEW myschema.myview (c1 String NOT NULL) AS SELECT c1 FROM file('base/dir/*.parquet', Parquet)`.

**Cause:** `FILE` is a base-tokenizer keyword, but `_parse_function` only accepts tokens in `FUNC_TOKENS`, and `FILE` wasn't in that set. So `file` was parsed as a plain table name, and the parenthesized arguments were taken as column aliases.

**Change:**
- `sqlglot/parser.py`: added `TokenType.FILE` to `FUNC_TOKENS`. This is in the base parser, so it applies to every dialect, not just ClickHouse. I did not add a ClickHouse-only override because ClickHouse has no parser class.
- `tests/dialects/test_clickhouse.py`: added `test_file_table_function` with your example and an aliased `file('a.csv', CSV) AS f` case.

**Verification:** the full suite passes with the test runner you gave (1114 passed, 18164 subtests). `file` as a column name still round-trips. I did not run `make check` or the linter.
