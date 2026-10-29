# trajectory base-1

final message:
Fixed: a `PATTERN` on a staged-file table is now kept when `FILE_FORMAT` is absent.

Your example now round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The parser already stored `format` and `pattern` as separate args; the bug was in `sqlglot/generator.py`, where `PATTERN` was only emitted inside the `FILE_FORMAT` branch. The generator now emits each option independently, joined by `, ` when both are present. I checked all three cases: pattern only, both, and format only. The both-present case still renders `(FILE_FORMAT => 'f', PATTERN => 'p')`, as before.

I added one `validate_identity` case for the pattern-only query to `tests/dialects/test_snowflake.py`; no existing assertions were changed. The full suite passes (1126 tests) with the project's pytest command, and `ruff format --check` is clean on both files.

Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Search for PATTERN and FILE_FORMAT handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/generator.py:548:    # Whether the text pattern/fill (3rd) parameter of RPAD()/LPAD() is optional (defaults to space)
sqlglot/generator.py:549:    PAD_FILL_PATTERN_IS_REQUIRED = False
sqlglot/generator.py:1640:            escape_pattern = re.compile(rf"{escape.name}(\d+)")
sqlglot/generator.py:1643:            escape_pattern = ESCAPED_UNICO
…[2250 chars elided]…
ERN_FIRST
sqlglot/parser.py:8878:            alter_set.set("file_format", [self._parse_field()])
sqlglot/parser.py:8879:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:8880:            alter_set.set("file_format", self._parse_wrapped_options())
sqlglot/parser.py:9551:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9553:            elif prev == "FILE_FORMAT":
sqlglot/parser.py:9788:        # for FILE_FORMAT = <format_name>
[tool_use Bash] {"command": "sed -n 2400,2445p sqlglot/generator.py && echo ---- && sed -n 4300,4370p sqlglot/parser.py && echo ---- && grep -n \"class FileFormat\\|class Table(\\|class TableFromRows\" -A12 sqlglot/expressions.py | head -60", "description": "Show generator, parser, and expression code"}
[tool_result]             pre_alias = f"{pre_alias}{version}"
        else:
            post_alias = f"{post_alias}{version}"

        hints = self.expressions(expression, key="hints", sep=" ")
        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        joins = self.indent(
            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
        )
        laterals = self.expressions(expression
…[3290 chars elided]…
 rows=rows,
                after=after,
                pattern=pattern,
                define=define,
                alias=self._parse_table_alias(),
            )
        )

    def _parse_lateral(self) -> exp.Lateral | None:
        cross_apply: bool | None = None
        if self._match_pair(TokenType.CROSS, TokenType.APPLY):
            cross_apply = True
        elif self._match_pair(TokenType.OUTER, TokenType.APPLY):
----
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"\\\"PATTERN\\\"\\|\\\"format\\\"\\|pattern=\" sqlglot/parser.py sqlglot/dialects/snowflake.py sqlglot/expressions/*.py 2>/dev/null | head -30; ls sqlglot | head -50; grep -rn \"FILE_FORMAT\\|PATTERN =>\" tests/dialects/test_snowflake.py | head -20", "description": "Locate table format/pattern parsing and tests"}
[tool_result] sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:4320:        if self._match_text_seq("PATTERN"):
sqlglot/parser.py:4360:                pattern=pattern,
sqlglot/expressions/dml.py:172:        "format": False,
sqlglot/expressions/ddl.py:129:        "format": False,
sqlglot/expressions/core.py:2280:    arg_types = {"this": True, "format": True}
sqlglot/expressions/core.py:2467:    "format": False,
sqlglot/expressions/temporal.py:445:    arg_types = {"this": True, "fo
…[4693 chars elided]…
ER='|' NULL_IF=('str1', 'str2') FIELD_OPTIONALLY_ENCLOSED_BY='"' TIMESTAMP_FORMAT='TZHTZM YYYY-MM-DD HH24:MI:SS.FF9' DATE_FORMAT='TZHTZM YYYY-MM-DD HH24:MI:SS.FF9' BINARY_FORMAT=BASE64) VALIDATION_MODE = 'RETURN_3_ROWS'"""
tests/dialects/test_snowflake.py:5533:            """COPY INTO mytable FROM 'azure://myaccount.blob.core.windows.net/mycontainer/data/files' CREDENTIALS = (AZURE_SAS_TOKEN='token') ENCRYPTION = (TYPE='AZURE_CSE' MASTER_KEY='kPx...') FILE_FORMAT = (FORMAT_NAME=my_csv_format)"""
[tool_use Bash] {"command": "grep -n \"FILE_FORMAT\\|\\\"PATTERN\\\"\\|\\\"format\\\"\" sqlglot/dialects/snowflake.py sqlglot/parsers/*.py | head; sed -n 9775,9800p sqlglot/parser.py; grep -n \"class Table(\" -A30 sqlglot/expressions/query.py | grep -n \"format\\|pattern\"", "description": "Find staged-file table parsing code"}
[tool_result] sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/parsers/clickhouse.py:435:        TokenType.FORMAT: lambda self: ("format", self._advance() or self._parse_id_var()),
sqlglot/parsers/snowflake.py:770:        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
sqlglot/parsers/snowflake.py:1097:                if self._match_text_seq("FILE_FORMAT", "=>"):
sqlglot/parsers/snowflake.py:1101:                elif self._match_text_seq("PATTERN", "=
…[525 chars elided]…
       exp.Property(
                this=exp.var("FORMAT_NAME"), value=self._parse_string() or self._parse_table_parts()
            )
        )

    def _parse_max_min_by(self, expr_type: type[exp.AggFunc]) -> exp.AggFunc:
        args: list[exp.Expr] = []

        if self._match(TokenType.DISTINCT):
            args.append(self.expression(exp.Distinct(expressions=[self._parse_lambda()])))
            self._match(TokenType.COMMA)
13:955-        "format": False,
14:956-        "pattern": False,
[tool_use Bash] {"command": "sed -n 1080,1125p sqlglot/parsers/snowflake.py", "description": "Show Snowflake staged-file parsing code"}
[tool_result]         wildcard: bool = False,
        fast: bool = False,
    ) -> exp.Table | exp.Dot | None:
        # https://docs.snowflake.com/en/user-guide/querying-stage
        if self._match(TokenType.STRING, advance=False):
            table = self._parse_string()
        elif self._match_text_seq("@", advance=False):
            table = self._parse_location_path()
        else:
            table = None

        if table:
            file_format = None
            pattern = None

            wrapped
…[617 chars elided]…
format, pattern=pattern))
        else:
            table = super()._parse_table_parts(
                schema=schema,
                is_db_reference=is_db_reference,
                fast=fast,
            )

        return table

    def _parse_table(
        self,
        schema: bool = False,
        joins: bool = False,
        alias_tokens: Collection[TokenType] | None = None,
        parse_bracket: bool = False,
        is_db_reference: bool = False,
        parse_partition: bool = False,
[assistant] The parser keeps `format` and `pattern` as separate args, but the generator only emits `PATTERN` inside the `FILE_FORMAT` branch. Let me look at the existing tests before editing.
[tool_use Bash] {"command": "sed -n 3428,3462p tests/dialects/test_snowflake.py", "description": "Show existing staged-file tests"}
[tool_result]         self.validate_identity("SELECT * FROM @mystage")
        self.validate_identity("SELECT * FROM '@mystage'")
        self.validate_identity("SELECT * FROM @namespace.mystage/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM @namespace.%table_name/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
        self.validate_identity("PUT file:///dir/tmp.csv @%table", check_command_warning=True)
        se
…[853 chars elided]…
_identity(
            "SELECT * FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla",
            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla",
        )

        self.validate_identity(
            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
        )

    def test_sample(self):
[assistant] Now the fix: emit `FILE_FORMAT` and `PATTERN` independently, joined by `, ` when both are present.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-084344-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[83 chars elided]…
        file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        if file_format or pattern:\n            options = [\n                f\"{name} => {value}\"\n                for name, value in ((\"FILE_FORMAT\", file_format), (\"PATTERN\", pattern))\n                if value\n            ]\n            file_format = f\" ({', '.join(options)})\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-084344-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Next, a regression test for the pattern-only case, added alongside the existing staged-file assertions.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-084344-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )\",\n            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE
…[3 chars elided]…
RMAT => 'fmt')\",\n        )\n", "new_string": "        self.validate_identity(\n            \"SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )\",\n            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-084344-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f')\\\", \\\"SELECT * FROM @mystage\\\"]:\n    print(sqlglot.parse_one(s, dialect='snowflake').sql(dialect='snowflake'))\n\"", "description": "Run Snowflake tests and check the three PATTERN/FILE_FORMAT cases"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.71s
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')
SELECT * FROM @mystage (FILE_FORMAT => 'f')
SELECT * FROM @mystage
[assistant] The Snowflake tests pass and all four cases render correctly. Now the project's full check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git diff --stat", "description": "Run full test suite and show diff stats"}
[tool_result] .......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 53.77s
 sqlglot/generator.py             | 12 ++++++++----
 tests/dialects/test_snowflake.py |  3 +++
 2 files changed, 11 insertions(+), 4 deletions(-)
[assistant] All 1126 tests pass. I'll run the formatter check on the two changed files, since my test edit may not match the project's formatting.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/dialects/test_snowflake.py 2>&1 || true) | tail -5", "description": "Check formatting of changed files with ruff"}
[tool_result] 2 files already formatted
[assistant] Fixed: a `PATTERN` on a staged-file table is now kept when `FILE_FORMAT` is absent.

Your example now round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The parser already stored `format` and `pattern` as separate args; the bug was in `sqlglot/generator.py`, where `PATTERN` was only emitted inside the `FILE_FORMAT` branch. The generator now emits each option independently, joined by `, ` when both are present. I checked all three cases: pattern only, both, and format only. The both-present case still renders `(FILE_FORMAT => 'f', PATTERN => 'p')`, as before.

I added one `validate_identity` case for the pattern-only query to `tests/dialects/test_snowflake.py`; no existing assertions were changed. The full suite passes (1126 tests) with the project's pytest command, and `ruff format --check` is clean on both files.

Changes are uncommitted in the worktree.
