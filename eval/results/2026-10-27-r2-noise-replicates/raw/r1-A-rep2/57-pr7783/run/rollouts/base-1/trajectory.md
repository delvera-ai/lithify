# trajectory base-1

final message:
Fixed: `PATTERN` is now kept when there is no `FILE_FORMAT`, and each parameter is emitted independently.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')            # now preserved
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')   # unchanged
```

**Cause:** In `sqlglot/generator.py`, `table_sql` only wrote the parenthesized parameter list inside `if file_format:`, so a pattern-only table lost its `PATTERN` entirely.

**Change:** In `sqlglot/generator.py`, the block now collects `FILE_FORMAT => …` and `PATTERN => …` separately and emits the parenthesized list if either is present. The existing `FILE_FORMAT, PATTERN` ordering is preserved.

**Tests:** In `tests/dialects/test_snowflake.py`, I added two round-trip checks next to the existing staged-file tests: pattern-only and format-only. I did not change any existing test.

**Verification:**
- Snowflake and dialect test files: 194 passed.
- Full suite with the project's pytest command: 1126 passed, 18224 subtests passed.

I have not committed the change.

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
[tool_use Bash] {"command": "grep -rn -i \"PATTERN =>\\|FILE_FORMAT\" tests/dialects/test_snowflake.py | head -30", "description": "Find related Snowflake tests"}
[tool_result] tests/dialects/test_snowflake.py:3432:        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
tests/dialects/test_snowflake.py:3436:            "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
tests/dialects/test_snowflake.py:3439:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
tests/dialects/test_snowflake.py:3442:            "SELECT t.$1, t.$2 FROM @mysta
…[3816 chars elided]…
FORMAT_NAME=MY_DATABASE.MY_SCHEMA.MY_FILE_FORMAT)"""
tests/dialects/test_snowflake.py:5549:    FILE_FORMAT = (TYPE = CSV COMPRESSION = NONE NULL_IF = ('') FIELD_OPTIONALLY_ENCLOSED_BY = '"')
tests/dialects/test_snowflake.py:5558:  FILE_FORMAT = (TYPE=CSV COMPRESSION=NONE NULL_IF=(
tests/dialects/test_snowflake.py:5568:FILE_FORMAT = (TYPE=CSV COMPRESSION=NONE NULL_IF=(
tests/dialects/test_snowflake.py:5581:    FILE_FORMAT = (TYPE=CSV COMPRESSION=NONE NULL_IF=('') FIELD_OPTIONALLY_ENCLOSED_BY='"')
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "offset": 2400, "limit": 25}
[tool_result] 2400	            pre_alias = f"{pre_alias}{version}"
2401	        else:
2402	            post_alias = f"{post_alias}{version}"
2403	
2404	        hints = self.expressions(expression, key="hints", sep=" ")
2405	        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
2406	        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
2407	        joins = self.indent(
2408	            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
2409	      
…[141 chars elided]…
t")
2413	        if file_format:
2414	            pattern = self.sql(expression, "pattern")
2415	            pattern = f", PATTERN => {pattern}" if pattern else ""
2416	            file_format = f" (FILE_FORMAT => {file_format}{pattern})"
2417	
2418	        ordinality = expression.args.get("ordinality") or ""
2419	        if ordinality:
2420	            ordinality = f" WITH ORDINALITY{alias}"
2421	            alias = ""
2422	
2423	        when = self.sql(expression, "when")
2424	        if when:
[tool_use Bash] {"command": "grep -n \"format\\b\\|\\\"format\\\"\" sqlglot/parser.py | sed -n 1,60p; sed -n 3425,3462p tests/dialects/test_snowflake.py", "description": "Inspect parser format handling and existing tests"}
[tool_result] 1846:    # Whether INTERVAL spans with literal format '\d+ hh:[mm:[ss[.ff]]]'
2838:        input_format = self._parse_string() if self._match_text_seq("INPUTFORMAT") else None
2839:        output_format = self._parse_string() if self._match_text_seq("OUTPUTFORMAT") else None
2846:                            input_format=input_format, output_format=output_format
2849:                    if input_format or output_format
2852:                hive_format=True,
3408:        format = self._parse_prope
…[2356 chars elided]…
_identity(
            "SELECT * FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla",
            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla",
        )

        self.validate_identity(
            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
        )

    def test_sample(self):
[assistant] Let me find where the `format` and `pattern` args get set during parsing for staged files.
[tool_use Bash] {"command": "grep -rn \"FILE_FORMAT\\|\\\"pattern\\\"\\|pattern=\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head; sed -n 9540,9570p sqlglot/parser.py; grep -n \"def _parse_table_parts\\|_parse_table_part\\b\" sqlglot/parser.py | head -3", "description": "Find where staged file format/pattern is parsed"}
[tool_result] sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:622:        TokenType.FILE_FORMAT,
sqlglot/parser.py:1701:        "FILE_FORMAT",
sqlglot/parser.py:4360:                pattern=pattern,
sqlglot/parser.py:8879:        elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:9551:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9
…[1093 chars elided]…
per()}"))
                param.set("expression", self._parse_field())
            else:
                param.set("expression", self._parse_unquoted_field() or self._parse_bracket())

            options.append(param)

            if sep:
                self._match(sep)

3582:                into=self._match(TokenType.INTO) and self._parse_table_part(),
4647:    def _parse_table_part(self, schema: bool = False) -> exp.Expr | None:
4655:    def _parse_table_parts_fast(self) -> exp.Table | None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/sqlglot/parser.py", "offset": 4305, "limit": 70}
[tool_result] 4305	
4306	        if self._match_text_seq("AFTER", "MATCH", "SKIP"):
4307	            text = "AFTER MATCH SKIP"
4308	            if self._match_text_seq("PAST", "LAST", "ROW"):
4309	                text += " PAST LAST ROW"
4310	            elif self._match_text_seq("TO", "NEXT", "ROW"):
4311	                text += " TO NEXT ROW"
4312	            elif self._match_text_seq("TO", "FIRST"):
4313	                text += f" TO FIRST {self._advance_any().text}"  # type: ignore
4314	            elif s
…[1619 chars elided]…
             alias=self._parse_table_alias(),
4363	            )
4364	        )
4365	
4366	    def _parse_lateral(self) -> exp.Lateral | None:
4367	        cross_apply: bool | None = None
4368	        if self._match_pair(TokenType.CROSS, TokenType.APPLY):
4369	            cross_apply = True
4370	        elif self._match_pair(TokenType.OUTER, TokenType.APPLY):
4371	            cross_apply = False
4372	
4373	        if cross_apply is not None:
4374	            this = self._parse_select(table=True)
[tool_use Bash] {"command": "grep -rn \"\\\"format\\\"\\|format=\\|PATTERN\" sqlglot/parser.py sqlglot/dialects/snowflake.py | grep -v \"input_format\\|output_format\\|hive_format\\|row_format\\|date_format\\|time_format\\|fmt\" | head -30; grep -n \"class Table(\" -A 30 sqlglot/expressions/*.py | grep -n \"arg_types\" -A 25 | head -40", "description": "Locate table format/pattern handling"}
[tool_result] sqlglot/parser.py:1777:    TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:3425:                format=format,
sqlglot/parser.py:4320:        if self._match_text_seq("PATTERN"):
sqlglot/parser.py:7863:                        format=exp.Literal.string(
sqlglot/parser.py:8278:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
2:sqlglot/expressions/query.py-944-    arg_types = {
3-sqlglot/expressions/query.py-945-        "this": False,
4-sqlglot/e
…[937 chars elided]…
61-        "changes": False,
20-sqlglot/expressions/query.py-962-        "rows_from": False,
21-sqlglot/expressions/query.py-963-        "sample": False,
22-sqlglot/expressions/query.py-964-        "indexed": False,
23-sqlglot/expressions/query.py-965-    }
24-sqlglot/expressions/query.py-966-
25-sqlglot/expressions/query.py-967-    @property
26-sqlglot/expressions/query.py-968-    def name(self) -> str:
27-sqlglot/expressions/query.py-969-        if not self.this or isinstance(self.this, Func):
[tool_use Bash] {"command": "grep -rn \"\\\"pattern\\\"\\|\\\"format\\\"\\|'pattern'\\|'format'\" sqlglot/ | grep -v \"\\.pyc\" | head -30", "description": "Find where Table format and pattern args are set"}
[tool_result] sqlglot/parser.py:6480:        # SKIP col or SKIP REGEXP 'pattern'
sqlglot/generator.py:1502:        format = self.sql(expression, "format")
sqlglot/generator.py:2412:        file_format = self.sql(expression, "format")
sqlglot/generator.py:2414:            pattern = self.sql(expression, "pattern")
sqlglot/generator.py:3208:        pattern = self.sql(expression, "pattern")
sqlglot/generator.py:3774:        fmt = self.sql(expression, "format")
sqlglot/generator.py:4065:        format_sql = self.s
…[1595 chars elided]…
: True, "culture": False, "zone": False}
sqlglot/expressions/temporal.py:493:    arg_types = {"this": True, "format": False, "safe": False}
sqlglot/expressions/temporal.py:505:    arg_types = {"this": True, "format": False, "safe": False}
sqlglot/expressions/temporal.py:529:    arg_types = {"this": True, "format": False}
sqlglot/expressions/temporal.py:539:        "format": False,
sqlglot/expressions/functions.py:39:        "format": False,
sqlglot/expressions/ddl.py:129:        "format": False,
[tool_use Bash] {"command": "grep -rn \"FILE_FORMAT\\|PATTERN\\|pattern\\|\\bformat\\b\" sqlglot/parsers/snowflake.py | head -20; grep -rln \"FILE_FORMAT\" sqlglot/", "description": "Search Snowflake parser modules for file format"}
[tool_result] sqlglot/parsers/snowflake.py:56:        format=fmt,
sqlglot/parsers/snowflake.py:107:                    # format strings (e.g., TO_TIMESTAMP('20240115', 'YYYYMMDD')) should
sqlglot/parsers/snowflake.py:119:        # Handle DATE/TIME with format strings - allow int_value if a format string is provided
sqlglot/parsers/snowflake.py:652:            this=seq_get(args, 0), format=seq_get(args, 1), safe=True
sqlglot/parsers/snowflake.py:661:            this=seq_get(args, 0), format=seq_get(args, 1), s
…[235 chars elided]…
atch_text_seq("FILE_FORMAT", "=>"):
sqlglot/parsers/snowflake.py:1101:                elif self._match_text_seq("PATTERN", "=>"):
sqlglot/parsers/snowflake.py:1102:                    pattern = self._parse_string()
sqlglot/parsers/snowflake.py:1108:            table = self.expression(exp.Table(this=table, format=file_format, pattern=pattern))
sqlglot/tokenizer_core.py
sqlglot/parser.py
sqlglot/generator.py
sqlglot/parsers/snowflake.py
sqlglot/dialects/snowflake.py
sqlglot/generators/snowflake.py
[tool_use Bash] {"command": "sed -n 1080,1115p sqlglot/parsers/snowflake.py; grep -n \"FILE_FORMAT\\|pattern\\|PATTERN\" -B2 -A6 sqlglot/generators/snowflake.py | head -40", "description": "View Snowflake staged-file parse and generate code"}
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
…[1412 chars elided]…
y="file_format", flat=True, sep=" ")
944:        file_format = f" STAGE_FILE_FORMAT = ({file_format})" if file_format else ""
945-        copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
946-        copy_options = f" STAGE_COPY_OPTIONS = ({copy_options})" if copy_options else ""
947-        tag = self.expressions(expression, key="tag", flat=True)
948-        tag = f" TAG {tag}" if tag else ""
949-
950-        return f"SET{exprs}{file_format}{copy_options}{tag}"
[assistant] The cause is in the base generator's `table_sql`: the `PATTERN` is only emitted inside the `if file_format:` branch, so a pattern without a format is silently dropped. I'll restructure it so each parameter is emitted independently.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[86 chars elided]…
     file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        if file_format or pattern:\n            params = []\n            if file_format:\n                params.append(f\"FILE_FORMAT => {file_format}\")\n            if pattern:\n                params.append(f\"PATTERN => {pattern}\")\n            file_format = f\" ({', '.join(params)})\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add regression tests covering pattern-only, format-only, and both, next to the existing staged-file tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )\",\n            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE
…[116 chars elided]…
t.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )\",\n            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (FILE_FORMAT => 'myformat')\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104740-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py tests/dialects/test_dialect.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')\\\", \\\"SELECT * FROM @mystage (PATTERN => 'p', FILE_FORMAT => 'f')\\\"]:\n    print(sqlglot.parse_one(s, dialect='snowflake').sql(dialect='snowflake'))\n\"", "description": "Run Snowflake and dialect tests and check the three cases"}
[tool_result] ............................... [ 15%]
............................................................................ [ 55%]
.................................................... [ 81%]
...................................                 [100%]
194 passed, 4398 subtests passed in 1.09s
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')
[assistant] Targeted tests pass. Now the full project check suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run the full project test suite"}
[tool_result] .......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 51.82s
[assistant] Fixed: `PATTERN` is now kept when there is no `FILE_FORMAT`, and each parameter is emitted independently.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')            # now preserved
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')   # unchanged
```

**Cause:** In `sqlglot/generator.py`, `table_sql` only wrote the parenthesized parameter list inside `if file_format:`, so a pattern-only table lost its `PATTERN` entirely.

**Change:** In `sqlglot/generator.py`, the block now collects `FILE_FORMAT => …` and `PATTERN => …` separately and emits the parenthesized list if either is present. The existing `FILE_FORMAT, PATTERN` ordering is preserved.

**Tests:** In `tests/dialects/test_snowflake.py`, I added two round-trip checks next to the existing staged-file tests: pattern-only and format-only. I did not change any existing test.

**Verification:**
- Snowflake and dialect test files: 194 passed.
- Full suite with the project's pytest command: 1126 passed, 18224 subtests passed.

I have not committed the change.
