# trajectory base-1

final message:
`PATTERN` is now kept when `FILE_FORMAT` is absent, and both options are preserved on their own and together. The full suite passes: 1126 tests, 18224 subtests.

**Cause:** the parser already stored `pattern` on the table correctly. The bug was in `table_sql` in `sqlglot/generator.py`, which only looked for `pattern` inside the `if file_format:` branch.

**Fix:** the generator now collects `FILE_FORMAT => ...` and `PATTERN => ...` into one list and emits the parenthesized group only when that list is non-empty.

**Tests:** I added one round-trip check in `tests/dialects/test_snowflake.py` for `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The existing tests already cover `FILE_FORMAT` alone and both together.

One side effect to be aware of: the generator is shared, so a `Table` with a `pattern` arg now emits `(PATTERN => ...)` in other dialects too. Previously that arg was dropped whenever no format was set. I didn't add cross-dialect tests for that.

I haven't committed. The changes are in the worktree as two modified files.

## events
[tool_use Bash] {"command": "grep -n -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/dialects/snowflake.py sqlglot/generator.py sqlglot/parser.py | head -80", "description": "Search for PATTERN and FILE_FORMAT handling"}
[tool_result] sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/generator.py:548:    # Whether the text pattern/fill (3rd) parameter of RPAD()/LPAD() is optional (defaults to space)
sqlglot/generator.py:549:    PAD_FILL_PATTERN_IS_REQUIRED = False
sqlglot/generator.py:1640:            escape_pattern = re.compile(rf"{escape.name}(\d+)")
sqlglot/generator.py:1643:            escape_pattern = ESCAPED_UNICODE_RE
sqlglot/generator.py:1647:            this = escape_pattern.
…[2184 chars elided]…
ERN_FIRST
sqlglot/parser.py:8878:            alter_set.set("file_format", [self._parse_field()])
sqlglot/parser.py:8879:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:8880:            alter_set.set("file_format", self._parse_wrapped_options())
sqlglot/parser.py:9551:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9553:            elif prev == "FILE_FORMAT":
sqlglot/parser.py:9788:        # for FILE_FORMAT = <format_name>
[tool_use Bash] {"command": "sed -n 2405,2420p sqlglot/generator.py && echo ---- && grep -n \"FILE_FORMAT\\|PATTERN\\|file_format\\|\\\"format\\\"\" sqlglot/parser.py | sed -n 1,40p && echo ---- && sed -n 9540,9570p sqlglot/parser.py && echo ---- && grep -n \"def _parse_table_parts\\|def _parse_table(\" sqlglot/parser.py && grep -rn \"PATTERN\" tests/dialects/test_snowflake.py | head", "description": "Inspect generator, parser, and existing tests"}
[tool_result]         hints = f" {hints}" if hints and self.TABLE_HINTS else ""
        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        joins = self.indent(
            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
        )
        laterals = self.expressions(expression, key="laterals", sep="")

        file_format = self.sql(expression, "format")
        if file_format:
            pattern = self.sql(expression, "pattern")
            pattern = 
…[3079 chars elided]…
 SEARCH(line, 'king', ANALYZER => 'PATTERN_ANALYZER', SEARCH_MODE => 'AND')",
tests/dialects/test_snowflake.py:5197:  PATTERN (^ S1 S2*? ( {{- S3 -}} S4 )+ | PERMUTE(S1, S2){{1,2}} $)
tests/dialects/test_snowflake.py:5536:            """COPY INTO mytable (col1, col2) FROM 's3://mybucket/data/files' STORAGE_INTEGRATION = "storage" ENCRYPTION = (TYPE='NONE' MASTER_KEY='key') FILES = ('file1', 'file2') PATTERN = 'pattern' FILE_FORMAT = (FORMAT_NAME=my_csv_format NULL_IF=('')) PARSE_HEADER = TRUE"""
[tool_use Bash] {"command": "sed -n 4300,4370p sqlglot/parser.py && echo ---- && sed -n 3430,3460p tests/dialects/test_snowflake.py && echo ---- && .. 2>/dev/null; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')\\\"]:\n    e = sqlglot.parse_one(s, dialect='snowflake'); print(repr(e.find(sqlglot.exp.Table).args.get('format')), e.sql('snowflake'))\n\"", "description": "Read pattern parsing and reproduce the bug"}
[tool_result]             elif self._match_text_seq("WITH", "UNMATCHED", "ROWS"):
                text += " WITH UNMATCHED ROWS"
            rows = exp.var(text)
        else:
            rows = None

        if self._match_text_seq("AFTER", "MATCH", "SKIP"):
            text = "AFTER MATCH SKIP"
            if self._match_text_seq("PAST", "LAST", "ROW"):
                text += " PAST LAST ROW"
            elif self._match_text_seq("TO", "NEXT", "ROW"):
                text += " TO NEXT ROW"
            elif
…[3256 chars elided]…
sandbox.test.my_csv_format, PATTERN => 'test') AS bla",
        )

        self.validate_identity(
            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
        )
----
None SELECT * FROM @mystage
Literal(this='f', is_string=True) SELECT * FROM @mystage (FILE_FORMAT => 'f')
Literal(this='f', is_string=True) SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')
[tool_use Bash] {"command": "grep -rn \"\\\"pattern\\\"\\|\\\"format\\\"\\|PATTERN\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/expressions.py | grep -v \"MatchRecognize\\|TRIM\" | head -20", "description": "Find where table pattern/format args are parsed"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:4320:        if self._match_text_seq("PATTERN"):
[tool_use Bash] {"command": "grep -rn \"pattern\\b\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/expressions/*.py 2>/dev/null | grep -i \"arg\\|set(\\|\\\"pattern\\|'pattern\" | head -20; grep -rn \"FILE_FORMAT\\|\\\"format\\\"\" sqlglot/parser.py sqlglot/dialects/snowflake.py | head", "description": "Locate pattern arg handling in parser and expressions"}
[tool_result] sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:6480:        # SKIP col or SKIP REGEXP 'pattern'
sqlglot/expressions/string.py:106:    arg_types = {"this": True, "expression": True, "fill_pattern": False, "is_left": True}
sqlglot/expressions/query.py:831:        "pattern": False,
sqlglot/expressions/query.py:956:        "pattern": False,
sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/parser.py:622:        TokenType.FILE_FORMAT,
sqlglot/parser.py:1701:        "FILE_FORMAT",
sqlglot/parser.py:8879:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:9551:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9553:            elif prev == "FILE_FORMAT":
sqlglot/parser.py:9788:        # for FILE_FORMAT = <format_name>
[tool_use Bash] {"command": "sed -n 820,840p sqlglot/expressions/query.py; sed -n 945,960p sqlglot/expressions/query.py; sed -n 1695,1710p sqlglot/parser.py; grep -n \"def _parse_table_parts\\b\" -A40 sqlglot/parser.py | grep -n \"format\\|L_PAREN\\|paren\" ; grep -n \"_parse_ordered_wrapped\\|\\\"format\\\"\\|format=\" sqlglot/parser.py | head", "description": "Inspect Table arg_types and format parsing"}
[tool_result]         "window_frame": False,
    }


class MatchRecognize(Expression):
    arg_types = {
        "partition_by": False,
        "order": False,
        "measures": False,
        "rows": False,
        "after": False,
        "pattern": False,
        "define": False,
        "alias": False,
    }


class Final(Expression):
    pass


        "this": False,
        "alias": False,
        "db": False,
        "catalog": False,
        "laterals": False,
        "joins": False,
        "pivots"
…[642 chars elided]…
T"}

    ODBC_DATETIME_LITERALS: t.ClassVar[dict[str, type[exp.Expr]]] = {}

2846:                            input_format=input_format, output_format=output_format
2852:                hive_format=True,
3425:                format=format,
3483:                    row_format=self._parse_row_format(match_row=True),
3657:                    input_format=self._match_text_seq("INPUTFORMAT") and self._parse_string(),
7863:                        format=exp.Literal.string(
7888:            format=fmt,
[tool_use Bash] {"command": "grep -n \"\\\"format\\\"\\|\\\"pattern\\\"\\|\\.set(\\\"format\\|set(\\\"pattern\" sqlglot/parser.py sqlglot/dialects/*.py | head; grep -n \"FILE_FORMAT\\|PATTERN\" -i sqlglot/dialects/snowflake.py | head", "description": "Find parser sets of table format and pattern"}
[tool_result] sqlglot/dialects/dialect.py:2240:        expression.args.get("format"),
144:            "FILE FORMAT": TokenType.FILE_FORMAT,
[tool_use Bash] {"command": "grep -n \"format\\b\" sqlglot/parser.py | sed -n 1,60p | grep -i \"table\\|stage\\|file\" ; grep -n \"_parse_table_parts(\" sqlglot/parser.py | head -3; grep -n \"def _parse_table_parts\" -A60 sqlglot/parser.py | grep -n \"format\\|pattern\\|stage\" ", "description": "Search table-part parser for format/pattern"}
[tool_result] 8878:            alter_set.set("file_format", [self._parse_field()])
8880:            alter_set.set("file_format", self._parse_wrapped_options())
9554:                # T-SQL's external file format case
1073:        exp.Table: lambda self: self._parse_table_parts(),
2210:            this = self._parse_table_parts(schema=True)
2227:        table = self._parse_table_parts(schema=True)
[tool_use Bash] {"command": "grep -n \"_parse_table\\|FILE\\|stage\" sqlglot/dialects/snowflake.py | head -30", "description": "Look for Snowflake table/stage parsing overrides"}
[tool_result] 143:            "FILE://": TokenType.URI_START,
144:            "FILE FORMAT": TokenType.FILE_FORMAT,
[tool_use Bash] {"command": "grep -n \"_parse_table_parts\\|def _parse_table\\b\" -A3 sqlglot/parser.py | sed -n 1,20p; sed -n 4718,4800p sqlglot/parser.py | grep -n \"L_PAREN\\|paren\\|wrapped\\|FORMAT\\|=>\" ", "description": "Read table-parts parser around stage handling"}
[tool_result] 1073:        exp.Table: lambda self: self._parse_table_parts(),
1074-        exp.TableAlias: lambda self: self._parse_table_alias(),
1075-        exp.Tuple: lambda self: self._parse_value(values=False),
1076-        exp.Whens: lambda self: self._parse_when_matched(),
--
2210:            this = self._parse_table_parts(schema=True)
2211-
2212-        self._match(TokenType.IS)
2213-
--
2227:        table = self._parse_table_parts(schema=True)
2228-        return self.expression(exp.ToTableProperty(this=table))
2229-
2230-    # https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/mergetree#mergetree-table-ttl
--
2323:            this = self._parse_table_parts(schema=True, is_db_reference=kind == "SCHEMA")
2324-
2325-        cluster = self._parse_on_property() if self._match(TokenType.ON) else None
2326-
--
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*x.*')\\\", dialect='snowflake').find(sqlglot.exp.Table)))\nprint(repr(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*x.*', FILE_FORMAT => 'f')\\\", dialect='snowflake').find(sqlglot.exp.Table)))\n\"; grep -rn \"\\\"format\\\"\" sqlglot/*.py sqlglot/dialects/*.py | head", "description": "Inspect parsed Table AST for pattern and format"}
[tool_result] Table(
  this=Var(this=@mystage),
  pattern=Literal(this='.*x.*', is_string=True))
Table(
  this=Var(this=@mystage),
  format=Literal(this='f', is_string=True),
  pattern=Literal(this='.*x.*', is_string=True))
sqlglot/generator.py:1502:        format = self.sql(expression, "format")
sqlglot/generator.py:2412:        file_format = self.sql(expression, "format")
sqlglot/generator.py:3774:        fmt = self.sql(expression, "format")
sqlglot/generator.py:4065:        format_sql = self.sql(expression, "format")
sqlglot/generator.py:4077:        return self.func("STR_TO_TIME", expression.this, expression.args.get("format"))
sqlglot/generator.py:4083:            expression.args.get("format"),
sqlglot/generator.py:4624:            self.sql(expression, "format"),
sqlglot/generator.py:4793:    @unsupported_args("format")
sqlglot/generator.py:4803:        fmt = expression.args.get("format")
sqlglot/generator.py:5083:                    exp.StrToTime(this=this, format=expression.args["format"]),
[assistant] The parser already stores `pattern` correctly. The bug is in `table_sql` in the generator: `PATTERN` is only emitted inside the `if file_format:` branch. I'll emit each option independently.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132335-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[90 chars elided]…
   file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        staged_options = []\n        if file_format:\n            staged_options.append(f\"FILE_FORMAT => {file_format}\")\n        if pattern:\n            staged_options.append(f\"PATTERN => {pattern}\")\n        file_format = f\" ({', '.join(staged_options)})\" if staged_options else \"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132335-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add regression tests for the pattern-only case next to the existing FILE_FORMAT/PATTERN tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132335-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla\",\n            \"SELECT * FROM @foo/bar (FILE_FORMAT => ds_s
…[73 chars elided]…
ew_string": "        self.validate_identity(\n            \"SELECT * FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla\",\n            \"SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132335-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Running the project's test command now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
[tool_result] .............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
...................................................... [ 40%]
.............................................................................................................................................................................................................................. [ 59%]
.........................
…[72 chars elided]…
............................. [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 64.51s (0:01:04)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')\\\", 'SELECT * FROM @mystage']:\n    print(sqlglot.parse_one(s, dialect='snowflake').sql(dialect='snowflake'))\n\" && git status --short && git diff --stat", "description": "Verify outputs and show changed files"}
[tool_result] SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @mystage (FILE_FORMAT => 'f')
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')
SELECT * FROM @mystage
 M sqlglot/generator.py
 M tests/dialects/test_snowflake.py
 sqlglot/generator.py             | 9 ++++++---
 tests/dialects/test_snowflake.py | 3 +++
 2 files changed, 9 insertions(+), 3 deletions(-)
[assistant] `PATTERN` is now kept when `FILE_FORMAT` is absent, and both options are preserved on their own and together. The full suite passes: 1126 tests, 18224 subtests.

**Cause:** the parser already stored `pattern` on the table correctly. The bug was in `table_sql` in `sqlglot/generator.py`, which only looked for `pattern` inside the `if file_format:` branch.

**Fix:** the generator now collects `FILE_FORMAT => ...` and `PATTERN => ...` into one list and emits the parenthesized group only when that list is non-empty.

**Tests:** I added one round-trip check in `tests/dialects/test_snowflake.py` for `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The existing tests already cover `FILE_FORMAT` alone and both together.

One side effect to be aware of: the generator is shared, so a `Table` with a `pattern` arg now emits `(PATTERN => ...)` in other dialects too. Previously that arg was dropped whenever no format was set. I didn't add cross-dialect tests for that.

I haven't committed. The changes are in the worktree as two modified files.
